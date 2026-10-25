"""Evidence-backed application processing based on the 18 February 2026 draft.

External decisions are recorded here; this service does not make those decisions.
"""
from datetime import date, timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import LicensingProcessing, LicensingProcessingEvent, LicensingPreliminaryReview
from .preliminary_review import review_type

PERMISSIONS = ('can_process_licensing', 'can_forward_licensing', 'can_decide_licensing', 'can_record_charter_authorities')


def can_process(user, permission=None):
    return bool(user.is_authenticated and user.is_active and (
        user.is_superuser or any(user.has_perm('license.' + p) for p in ([permission] if permission else PERMISSIONS))))


def family(view):
    path = view.review_portal_path
    if '/oti/' in path:
        raise ValidationError('This draft applies to private universities and ODAIs, not OTI applications.')
    return 'interim' if 'interim-authority' in path else 'charter' if 'charter' in path else 'provisional'


def field(name, label, kind='text'):
    return {'name': name, 'label': label, 'kind': kind}


def actions(kind):
    """action: (source stages, destination, permission, required evidence)."""
    process, forward, decide, external = PERMISSIONS
    result = {
        'request_clarification': (['preliminary_feedback'], 'clarification', process, [field('letter_reference', 'Clarification letter / document reference')]),
        'record_response': (['clarification'], 'preliminary_feedback', process, [field('response_reference', 'Applicant response document reference')]),
        'refer_council': (['preliminary_feedback'], 'council_decision', forward, [field('report_reference', 'Assessment report reference')]),
        'refuse': (['council_decision'], 'refused', decide, [field('decision_reference', 'Council decision / minutes reference')]),
        'issue_interim': (['council_decision'], 'issued', decide, [field('decision_reference', 'Council decision reference'), field('letter_reference', 'Signed interim authority letter reference')]),
    }
    if kind == 'interim':
        result['refer_council'][3].append(field('promoter_screening_reference', 'Promoter integrity checks and national-interest assessment reference'))
        return result
    result.pop('issue_interim')
    result['refer_council'] = (['vetting_report'], 'council_decision', forward, [field('forwarding_reference', 'Executive Director forwarding reference')])
    result.update({
        'appoint_vetting': (['preliminary_feedback'], 'vetting', process, [field('appointment_reference', 'Vetting team appointment reference'), field('members', 'Vetting team members')]),
        'submit_vetting': (['vetting'], 'vetting_report', process, [field('completed_on', 'Vetting completion date', 'date'), field('report_reference', 'Vetting report to Executive Director')]),
        'defer': (['council_decision'], 'deferred', decide, [field('decision_reference', 'Council decision reference')]),
        'reopen': (['deferred'], 'preliminary_feedback', process, [field('response_reference', 'Evidence addressing the shortfalls')]),
        'approve_verification': (['council_decision'], 'verification_invoice', decide, [field('decision_reference', 'Council decision authorising verification')]),
        'invoice_verification': (['verification_invoice'], 'verification_appointment', process, [field('invoice_reference', 'Verification invoice reference')]),
        'appoint_verification': (['verification_appointment'], 'verification', process, [field('appointment_reference', 'Committee appointment reference'), field('team', 'Verification / inspection committee', 'team'), field('briefing_reference', 'Briefing and duties reference')]),
        'submit_verification': (['verification'], 'verification_report', process, [field('completed_on', 'Physical verification / inspection completion date', 'date'), field('report_reference', 'Signed committee report reference'), field('signed_annexes_reference', 'Signed individual findings and minority reports reference')]),
        'forward_verification': (['verification_report'], 'final_council', forward, [field('forwarding_reference', 'Executive Director forwarding reference')]),
    })
    if kind == 'provisional':
        result['appoint_vetting'][3].extend([field('interim_letter_reference', 'Valid interim authority letter reference'), field('interim_issued_on', 'Interim authority issue date', 'date')])
        result.pop('refuse')
        result.update({
            'invite_hearing': (['council_decision', 'final_council'], 'hearing', decide, [field('notice_reference', 'Written show-cause invitation reference')]),
            'record_hearing_response': (['hearing'], 'hearing_decision', process, [field('response_reference', 'Applicant written response reference')]),
            'close_hearing': (['hearing'], 'hearing_decision', process, [field('service_reference', 'Proof of service and absence of response')]),
            'refuse': (['hearing_decision'], 'refused', decide, [field('decision_reference', 'Council decision reference')]),
            'issue_provisional': (['final_council', 'hearing_decision'], 'publication_pending', decide, [field('decision_reference', 'Council decision reference'), field('licence_reference', 'Signed provisional licence reference')]),
            'publish_provisional': (['publication_pending'], 'issued', process, [field('gazette_reference', 'Gazette publication reference'), field('gazette_on', 'Gazette publication date', 'date'), field('press_reference', 'Nationwide newspaper publication reference')]),
        })
    else:
        result['appoint_vetting'][3].extend([field('provisional_reference', 'Provisional licence and Gazette reference'), field('provisional_published_on', 'Provisional Gazette publication date', 'date')])
        result['submit_verification'][3].append(field('charter_review_reference', 'Draft charter review before inspection reference'))
        result['refuse'] = (['final_council'], 'refused', decide, [field('decision_reference', 'Council decision reference'), field('applicant_notice_reference', 'Reasoned notice to applicant'), field('minister_notice_reference', 'Reasoned notice to Minister')])
        result.update({
            'recommend_charter': (['final_council'], 'attorney_general', decide, [field('decision_reference', 'Council recommendation reference'), field('legal_request_reference', 'Request for Attorney General legal guidance')]),
            'record_ag_clearance': (['attorney_general'], 'minister', external, [field('clearance_reference', 'Attorney General charter clearance'), field('submission_reference', 'Submission of cleared charter to Minister')]),
            'record_minister': (['minister'], 'president', external, [field('accreditation_reference', 'Minister accreditation reference'), field('recommendation_reference', 'Minister recommendation to President')]),
            'record_president': (['president'], 'publication_pending', external, [field('grant_reference', 'Presidential charter grant reference')]),
            'publish_charter': (['publication_pending'], 'issued', external, [field('gazette_reference', 'Minister legal notice / Gazette reference'), field('press_reference', 'Public print media reference')]),
        })
    return result


class MemberSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    role = serializers.ChoiceField(choices=['leader', 'finance', 'law', 'education_management', 'engineer', 'other'])
    experience = serializers.IntegerField(min_value=0, max_value=80)
    conflict_declared = serializers.BooleanField()
    has_conflict = serializers.BooleanField()


def validate_evidence(required, evidence, occurred_on):
    result = {}
    for spec in required:
        name = spec['name']
        value = evidence.get(name)
        if spec['kind'] == 'team':
            team = MemberSerializer(data=value, many=True)
            team.is_valid(raise_exception=True)
            members = team.validated_data
            if not 5 <= len(members) <= 9 or len({m['name'].strip().casefold() for m in members}) != len(members):
                raise ValidationError({'team': 'Provide 5–9 distinct committee members.'})
            leaders = [m for m in members if m['role'] == 'leader']
            if len(leaders) != 1 or leaders[0]['experience'] < 10:
                raise ValidationError({'team': 'One leader with at least ten years of higher education management experience is required.'})
            if not {'finance', 'law', 'education_management', 'engineer'} <= {m['role'] for m in members}:
                raise ValidationError({'team': 'Include finance, law, education management and engineering experts.'})
            if any(not m['conflict_declared'] or m['has_conflict'] or (m['role'] != 'leader' and m['experience'] < 7) for m in members):
                raise ValidationError({'team': 'Record declarations, replace conflicted members and ensure other members have seven years of experience.'})
            result[name] = members
        elif spec['kind'] == 'date':
            parsed = serializers.DateField().run_validation(value)
            if parsed > occurred_on:
                raise ValidationError({name: 'This date cannot follow the recorded action date.'})
            result[name] = parsed.isoformat()
        else:
            result[name] = serializers.CharField(max_length=10000).run_validation(value)
    return result


def add_days(day, count, working=False):
    while count:
        day += timedelta(days=1)
        if not working or day.weekday() < 5:
            count -= 1
    return day


def add_years(day, years):
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def add_months(day, months):
    import calendar
    month = day.month - 1 + months
    year = day.year + month // 12
    month = month % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


def deadlines(kind, application, events):
    rows = []
    if kind != 'interim':
        # The legacy date field uses auto_now, so use creation time as the best available receipt baseline.
        acknowledgment = next((e for e in reversed(events) if e.action == 'acknowledge'), None)
        received = date.fromisoformat(acknowledgment.evidence['received_on']) if acknowledgment else getattr(application, 'created', None)
        received = received.date() if hasattr(received, 'date') else received or application.application_date
        if received:
            rows.append({'task': 'Acknowledge receipt and explain the process (confirm actual receipt date)', 'due_on': add_days(received, 7)})
    for event in events:
        day, action = event.occurred_on, event.action
        tasks = []
        if action == 'submit_vetting': tasks = [('Submit vetting report to Executive Director', add_days(date.fromisoformat(event.evidence['completed_on']), 14))]
        if action == 'refer_council' and kind != 'interim': tasks = [('Council review of vetting report', add_days(day, 90))]
        if action in ['defer', 'approve_verification']: tasks = [('Communicate Council decision', add_days(day, 7, True))]
        if action == 'approve_verification' and kind == 'provisional': tasks += [('Constitute verification team', add_days(day, 14))]
        if action == 'submit_verification': tasks = [('Prepare verification / inspection report', add_days(date.fromisoformat(event.evidence['completed_on']), 7 if kind == 'charter' else 3, True))]
        if action == 'invite_hearing': tasks = [('Applicant written show-cause response', add_days(day, 14))]
        if action == 'refuse' and kind == 'provisional': tasks = [('Communicate refusal', add_days(day, 14))]
        if action == 'record_ag_clearance': tasks = [('Minister accreditation and recommendation (confirm receipt baseline)', add_days(day, 90))]
        if action == 'issue_provisional': tasks = [('Publish in Gazette and nationwide newspaper', add_months(day, 3))]
        if action == 'appoint_verification' and kind == 'charter': tasks = [('Submit inspection report to National Council', add_months(day, 6))]
        for task, due in tasks:
            rows.append({'task': task, 'due_on': due, 'event_id': event.pk})
    return rows


def serialize_event(event):
    return {'id': event.pk, 'revision': event.revision, 'action': event.action, 'from_stage': event.from_stage,
            'to_stage': event.to_stage, 'actor': event.actor.username, 'occurred_on': event.occurred_on,
            'notes': event.notes, 'evidence': event.evidence, 'created_at': event.created_at}


class TransitionSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=0)
    action = serializers.CharField(max_length=50)
    occurred_on = serializers.DateField()
    notes = serializers.CharField(max_length=20000)
    evidence = serializers.DictField(default=dict)
    confirmed = serializers.BooleanField()


def processing(view, request, pk):
    kind = family(view)
    if not (can_process(request.user) or view.can_assign_reviews()):
        raise PermissionDenied('Licensing processing access is required.')
    with transaction.atomic():
        app = get_object_or_404(view.get_queryset().select_for_update(), pk=pk)
        state = LicensingProcessing.objects.filter(application_type=review_type(view), application_id=app.pk).first()
        stage = state.stage if state else ('preliminary_feedback' if app.status == 'prelim_feedback' else 'awaiting_preliminary')
        if stage == 'awaiting_preliminary' and app.status == 'prelim_feedback':
            stage = 'preliminary_feedback'
        if not state and app.status not in ['submitted', 'prelim_review', 'prelim_feedback']:
            raise ValidationError('Only submitted applications can enter backoffice processing.')
        configured = actions(kind)
        configured['record_communication'] = ([stage], stage, PERMISSIONS[0], [field('recipient', 'Recipient'), field('letter_reference', 'Sent letter / service evidence reference')])
        configured['acknowledge'] = ([stage], stage, PERMISSIONS[0], [field('received_on', 'Actual application receipt date', 'date'), field('letter_reference', 'Acknowledgment and process explanation letter reference')])
        if request.method == 'POST':
            payload = TransitionSerializer(data=request.data)
            payload.is_valid(raise_exception=True)
            data = payload.validated_data
            if data['revision'] != (state.revision if state else 0):
                return Response({'detail': 'Processing changed. Reload before recording an action.'}, status=409)
            config = configured.get(data['action'])
            if not config or stage not in config[0]:
                raise ValidationError('This action is not available at the current stage.')
            if not can_process(request.user, config[2]):
                raise PermissionDenied('You cannot record this authority’s action.')
            if not data['confirmed'] or data['occurred_on'] > timezone.localdate():
                raise ValidationError('Confirm the record and use an action date no later than today.')
            previous = state.events.order_by('-revision').first() if state else None
            if previous and data['occurred_on'] < previous.occurred_on:
                raise ValidationError('The action date cannot precede the previous action.')
            evidence = validate_evidence(config[3], data['evidence'], data['occurred_on'])
            if data['action'] == 'appoint_vetting':
                if not state or not state.events.filter(action='acknowledge').exists():
                    raise ValidationError('Record acknowledgment and the process explanation before appointing the vetting team.')
                acknowledgment = state.events.filter(action='acknowledge').last()
                received_on = date.fromisoformat(acknowledgment.evidence['received_on'])
                prerequisite_on = date.fromisoformat(evidence['interim_issued_on'] if kind == 'provisional' else evidence['provisional_published_on'])
                if prerequisite_on > received_on:
                    raise ValidationError('The prerequisite licence cannot postdate application receipt.')
                if kind == 'provisional' and add_years(prerequisite_on, 3) <= received_on:
                    raise ValidationError('The interim authority letter must be valid at application receipt.')
                if kind == 'charter' and add_years(prerequisite_on, 3) > received_on:
                    raise ValidationError('The institution must hold a provisional licence for at least three years.')
            if data['action'] in ['submit_vetting', 'submit_verification']:
                appointment_action = 'appoint_vetting' if data['action'] == 'submit_vetting' else 'appoint_verification'
                appointed = state.events.filter(action=appointment_action).last()
                if date.fromisoformat(evidence['completed_on']) < appointed.occurred_on:
                    raise ValidationError('Completion cannot precede the team appointment date.')
            if data['action'] == 'publish_provisional':
                issued = state.events.filter(action='issue_provisional').last()
                if date.fromisoformat(evidence['gazette_on']) < issued.occurred_on:
                    raise ValidationError('Gazette publication cannot precede issuance.')
            if data['action'] in ['refer_council', 'appoint_vetting'] and stage == 'preliminary_feedback':
                review = LicensingPreliminaryReview.objects.filter(application_type=review_type(view), application_id=app.pk, submitted_at__isnull=False).first()
                responded = state and state.events.filter(action='record_response').exists()
                if not review or (review.outcome == 'clarification_required' and not responded):
                    raise ValidationError('Resolve the submitted preliminary review clarifications first.')
            if data['action'] == 'close_hearing':
                notice = state.events.filter(action='invite_hearing').last()
                if data['occurred_on'] <= add_days(notice.occurred_on, 14):
                    raise ValidationError('Allow the full fourteen-day response period before closing the hearing.')
            state = state or LicensingProcessing(application_type=review_type(view), application_id=app.pk)
            state.stage = config[1]
            state.revision += 1
            state.save()
            LicensingProcessingEvent.objects.create(processing=state, revision=state.revision, action=data['action'], from_stage=stage,
                to_stage=state.stage, actor=request.user, occurred_on=data['occurred_on'], notes=data['notes'], evidence=evidence)
            # Existing application statuses remain compatible with applicant-facing screens.
            if state.stage != 'awaiting_preliminary':
                app.status = 'completed' if state.stage == 'issued' else 'rejected' if state.stage == 'refused' else 'deferred' if state.stage == 'deferred' else 'under_council_review'
                app.save(update_fields=['status'])
            stage = state.stage
        events = list(state.events.select_related('actor')) if state else []
        # Rebuild self transitions using the stage after the recorded action.
        configured = actions(kind)
        configured['record_communication'] = ([stage], stage, PERMISSIONS[0], [field('recipient', 'Recipient'), field('letter_reference', 'Sent letter / service evidence reference')])
        configured['acknowledge'] = ([stage], stage, PERMISSIONS[0], [field('received_on', 'Actual application receipt date', 'date'), field('letter_reference', 'Acknowledgment and process explanation letter reference')])
        available = [{'action': name, 'label': name.replace('_', ' ').capitalize(), 'fields': config[3]}
                     for name, config in configured.items() if stage in config[0] and can_process(request.user, config[2])]
        validity = None
        for event in events:
            if event.action == 'issue_interim': validity = {'effective_on': event.occurred_on, 'valid_until': add_years(event.occurred_on, 3)}
            if event.action == 'publish_provisional':
                effective = date.fromisoformat(event.evidence['gazette_on'])
                validity = {'effective_on': effective, 'minimum_valid_until': add_years(effective, 3)}
        review = LicensingPreliminaryReview.objects.filter(application_type=review_type(view), application_id=app.pk, submitted_at__isnull=False).first()
        return Response({'application_code': getattr(app, view.code_field), 'institution': getattr(app, view.institution_field).name,
                         'family': kind, 'stage': stage, 'revision': state.revision if state else 0,
                         'actions': available, 'history': [serialize_event(e) for e in events],
                         'deadlines': deadlines(kind, app, events), 'validity': validity,
                         'preliminary_review': {'summary': review.summary, 'outcome': review.outcome,
                             'fields': review.application_snapshot, 'observations': review.observations} if review else None})
