"""Shared, institution-safe status tracking for all eight licensing types."""
from django.db.models.signals import post_save

from .models import (
    CertificationAndClassification, CharterApplication, IntrimAuthority,
    LicensingProcessing, LicensingProcessingEvent, LicensingStatusHistory, OTIProvisional, UniversityProvisionalLicense,
)

# Labels and next steps are deliberately public; internal notes never enter this feed.
STATUSES = {
    'draft': ('Draft', 'Complete your application and submit it with the required payment.'),
    'submitted': ('Submitted', 'Your application has been received. Await preliminary review.'),
    'completed': ('Application Processing Completed', 'Refer to your formal NCHE instrument for its effective date and terms.'),
    'prelim_review': ('Under Preliminary Review', 'NCHE is reviewing your application. No action is required unless NCHE contacts you.'),
    'prelim_feedback': ('Preliminary Review Completed', 'NCHE has completed the preliminary review. Check your correspondence for feedback or clarification requests.'),
    'clarification': ('Awaiting Your Clarification', 'Respond to the clarification request sent by NCHE through the indicated channel.'),
    'vetting': ('Vetting in Progress', 'Your application is being vetted. NCHE will contact you if a meeting or further information is needed.'),
    'vetting_report': ('Vetting Completed', 'The vetting report is awaiting forwarding for Council consideration.'),
    'council_decision': ('Under Council Review', 'Await the Council decision on your application.'),
    'verification_invoice': ('Approved for Verification / Inspection', 'Await the verification or inspection invoice and instructions from NCHE.'),
    'verification_appointment': ('Verification / Inspection Being Arranged', 'Follow the invoice instructions and await confirmation of the verification or inspection arrangements.'),
    'verification': ('Verification / Inspection in Progress', 'Cooperate with the appointed committee and provide any information requested during the visit.'),
    'verification_report': ('Verification / Inspection Completed', 'The committee report is being forwarded for a final Council decision.'),
    'final_council': ('Awaiting Final Council Decision', 'Await the final Council decision following verification or inspection.'),
    'hearing': ('Awaiting Your Show-Cause Response', 'Respond in writing to the NCHE show-cause notice within the period stated in the notice.'),
    'hearing_decision': ('Response Period Concluded - Council Reconsideration', 'The response period has concluded. Await Council reconsideration.'),
    'deferred': ('Deferred - Further Requirements', 'Address the shortfalls communicated by NCHE and submit the required evidence.'),
    'attorney_general': ('Charter Awaiting Legal Clearance', 'The charter recommendation is awaiting Attorney General legal clearance.'),
    'minister': ('Charter with the Minister', 'The cleared charter has been submitted to the Minister for consideration.'),
    'president': ('Charter Awaiting Presidential Grant', 'The Minister recommendation is awaiting Presidential consideration.'),
    'publication_pending': ('Issued / Granted - Awaiting Publication', 'Publication is being completed. A provisional licence takes effect only after Gazette publication.'),
    'issued': ('Issued', 'Processing is complete. Follow NCHE instructions to obtain the signed instrument.'),
    'refused': ('Application Refused', 'Refer to the formal NCHE decision letter for the reasons and any further instructions.'),
}
ALIASES = {'awaiting_preliminary': None, 'preliminary_feedback': 'prelim_feedback', 'rejected': 'refused'}


def application_type(application):
    model = type(application)
    prefix = 'odai' if getattr(application, 'is_odai', False) else 'university'
    names = {
        IntrimAuthority: prefix + '/interim-authority',
        UniversityProvisionalLicense: prefix + '/provisional-license',
        CharterApplication: prefix + '/charter',
        OTIProvisional: 'oti/provisional-license',
        CertificationAndClassification: 'oti/classification-registration',
    }
    return names[model]


def current_status(application, processing=None):
    status = application.status
    # Assignment and preliminary review remain authoritative while processing is waiting.
    if status not in ['draft', 'submitted', 'prelim_review', 'prelim_feedback']:
        if processing is None:
            processing = LicensingProcessing.objects.filter(application_type=application_type(application), application_id=application.pk).first()
        if processing and processing.stage != 'awaiting_preliminary':
            status = processing.stage
    return ALIASES.get(status, status) or application.status


def describe(status, application=None):
    choices = dict(application._meta.get_field('status').choices or []) if application else {}
    fallback = choices.get(status, status.replace('_', ' ').capitalize())
    label, next_step = STATUSES.get(status, (fallback, 'Your application is being processed. Follow any instructions sent by NCHE.'))
    if status == 'issued' and isinstance(application, IntrimAuthority):
        label = 'Interim Authority Issued'
        next_step = 'Your interim authority has been issued. It permits institutional development, not academic operations.'
    elif status == 'issued' and isinstance(application, CharterApplication):
        label = 'Charter Granted and Published'
    elif status == 'issued' and isinstance(application, UniversityProvisionalLicense):
        label = 'Provisional Licence Published / Effective'
    elif status == 'publication_pending' and isinstance(application, CharterApplication):
        label = 'Charter Granted - Awaiting Publication'
        next_step = 'The charter grant is awaiting publication by the Minister.'
    return {'status_code': status, 'status': label, 'next_step': next_step,
            'action_required': status in ['draft', 'clarification', 'hearing', 'deferred']}


def status_summary(application):
    return describe(current_status(application), application)


def record_status(sender, instance, raw=False, update_fields=None, **kwargs):
    if raw or (update_fields is not None and 'status' not in update_fields):
        return
    kind = application_type(instance)
    status = current_status(instance)
    previous = LicensingStatusHistory.objects.filter(application_type=kind, application_id=instance.pk).order_by('-id').first()
    if previous is None or previous.status != status:
        LicensingStatusHistory.objects.create(application_type=kind, application_id=instance.pk, status=status)


def tracking_response(application):
    kind = application_type(application)
    summary = status_summary(application)
    changes = list(LicensingStatusHistory.objects.filter(application_type=kind, application_id=application.pk))
    history = []
    legacy = LicensingProcessingEvent.objects.filter(processing__application_type=kind, processing__application_id=application.pk)
    if changes:
        legacy = legacy.filter(created_at__lt=changes[0].recorded_at)
    for event in legacy.order_by('created_at', 'id'):
        if event.from_stage != event.to_stage:
            status = ALIASES.get(event.to_stage, event.to_stage)
            if status:
                history.append({'id': None, **describe(status, application), 'recorded_at': event.created_at})
    for row in changes:
        if history and history[-1]['status_code'] == row.status:
            continue
        history.append({'id': row.pk, **describe(row.status, application), 'recorded_at': row.recorded_at})
    # Legacy records may have no tracked history yet. Never invent transition dates.
    if not history or history[-1]['status_code'] != summary['status_code']:
        history.append({'id': None, **summary, 'recorded_at': None})
    return {
        'application_code': getattr(application, 'application_code', None) or getattr(application, 'code', ''),
        'application_type': kind,
        'institution': getattr(getattr(application, 'institution', None) or getattr(application, 'institute', None), 'name', ''),
        **summary,
        'updated_at': history[-1]['recorded_at'],
        'history': history,
    }


for model in [IntrimAuthority, UniversityProvisionalLicense, CharterApplication, OTIProvisional, CertificationAndClassification]:
    post_save.connect(record_status, sender=model, dispatch_uid='license.status.' + model._meta.model_name)
