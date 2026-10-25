from datetime import date

from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase

from . import test_reviewer_assignment as assignments
from .models import LicensingPreliminaryReview, LicensingProcessing, LicensingProcessingEvent
from .processing import PERMISSIONS, actions, add_days, add_months


class LicensingProcessingTests(APITestCase):
    setUp = assignments.LicensingReviewerAssignmentTests.setUp
    call = assignments.LicensingReviewerAssignmentTests.call

    def prepare(self, index):
        app, view, _ = self.cases[index]
        app.status = 'prelim_feedback'
        app.save(update_fields=['status'])
        self.actor.user_permissions.add(*Permission.objects.filter(content_type__app_label='license', codename__in=PERMISSIONS))
        LicensingPreliminaryReview.objects.create(application_type=view.review_portal_path.removeprefix('/license/'), application_id=app.pk,
            reviewer=self.reviewer, application_snapshot=[], snapshot_hash='a' * 64, summary='Checked', outcome='no_concerns', submitted_at='2026-01-01T00:00:00Z')
        return app, view

    def move(self, app, view, action, day='2026-10-01', evidence=None):
        state = self.call(view, 'processing', self.actor, method='get', pk=app.pk)
        self.assertEqual(state.status_code, 200, state.data)
        spec = next((a for a in state.data['actions'] if a['action'] == action), None)
        supplied = {f['name']: 'Evidence reference' for f in spec['fields']} if spec else {}
        if action == 'acknowledge':
            supplied['received_on'] = day
        supplied.update(evidence or {})
        return self.call(view, 'processing', self.actor, pk=app.pk, data={'action': action, 'revision': state.data['revision'],
            'occurred_on': day, 'notes': 'Recorded findings and decision reasons', 'evidence': supplied, 'confirmed': True})

    def team(self):
        return [{'name': role, 'role': role, 'experience': 12, 'conflict_declared': True, 'has_conflict': False}
                for role in ['leader', 'finance', 'law', 'education_management', 'engineer']]

    def verification(self, app, view, kind):
        self.assertEqual(self.move(app, view, 'acknowledge').status_code, 200)
        dates = {'interim_issued_on': '2025-01-01'} if kind == 'provisional' else {'provisional_published_on': '2020-01-01'}
        for action, extra in [('appoint_vetting', dates), ('submit_vetting', {'completed_on': '2026-10-01'}),
                              ('refer_council', {}), ('approve_verification', {}), ('invoice_verification', {}),
                              ('appoint_verification', {'team': self.team()}), ('submit_verification', {'completed_on': '2026-10-01'}), ('forward_verification', {})]:
            result = self.move(app, view, action, evidence=extra)
            self.assertEqual(result.status_code, 200, result.data)

    def test_interim_for_university_and_odai_and_no_duplicate_transition(self):
        for index in [0, 1]:
            app, view = self.prepare(index)
            self.assertEqual(self.move(app, view, 'refer_council').status_code, 200)
            result = self.move(app, view, 'issue_interim')
            self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(str(result.data['validity']['valid_until']), '2029-10-01')
            self.assertEqual(self.move(app, view, 'issue_interim').status_code, 400)

    def test_provisional_not_effective_until_publication(self):
        for index in [2, 3]:
            app, view = self.prepare(index)
            self.verification(app, view, 'provisional')
            result = self.move(app, view, 'issue_provisional')
            self.assertEqual(result.status_code, 200, result.data)
            self.assertIsNone(result.data['validity'])
            app.refresh_from_db()
            self.assertNotEqual(app.status, 'completed')
            result = self.move(app, view, 'publish_provisional', evidence={'gazette_on': '2026-10-01'})
            self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(result.data['stage'], 'issued')

    def test_charter_external_authorities_cannot_be_skipped(self):
        for index in [4, 5]:
            app, view = self.prepare(index)
            self.verification(app, view, 'charter')
            self.assertEqual(self.move(app, view, 'record_president').status_code, 400)
            for action in ['recommend_charter', 'record_ag_clearance', 'record_minister', 'record_president', 'publish_charter']:
                result = self.move(app, view, action)
                self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(result.data['stage'], 'issued')

    def test_conflicts_membership_and_prerequisites(self):
        app, view = self.prepare(2)
        self.assertEqual(self.move(app, view, 'acknowledge').status_code, 200)
        self.assertEqual(self.move(app, view, 'appoint_vetting', evidence={'interim_issued_on': '2020-01-01'}).status_code, 400)
        for action, extra in [('appoint_vetting', {'interim_issued_on': '2025-01-01'}), ('submit_vetting', {'completed_on': '2026-10-01'}), ('refer_council', {}), ('approve_verification', {}), ('invoice_verification', {})]:
            self.assertEqual(self.move(app, view, action, evidence=extra).status_code, 200)
        members = self.team()
        members[0]['has_conflict'] = True
        self.assertEqual(self.move(app, view, 'appoint_verification', evidence={'team': members}).status_code, 400)
        self.assertEqual(self.move(app, view, 'appoint_verification', evidence={'team': self.team()[:4]}).status_code, 400)
        charter, charter_view = self.prepare(4)
        self.assertEqual(self.move(charter, charter_view, 'appoint_vetting', evidence={'provisional_published_on': '2025-01-01'}).status_code, 400)

    def test_hearing_period_and_refusal_reasons(self):
        app, view = self.prepare(2)
        self.verification(app, view, 'provisional')
        self.assertEqual(self.move(app, view, 'refuse').status_code, 400)
        self.assertEqual(self.move(app, view, 'invite_hearing').status_code, 200)
        self.assertEqual(self.move(app, view, 'close_hearing', day='2026-10-14').status_code, 400)
        self.assertEqual(self.move(app, view, 'close_hearing', day='2026-10-16').status_code, 200)
        self.assertEqual(self.move(app, view, 'refuse', day='2026-10-16').status_code, 200)

    def test_permissions_scope_stale_revisions_and_oti_exclusion(self):
        app, view = self.prepare(0)
        for user in [self.owner, self.reviewer, self.reviewer2]:
            self.assertEqual(self.call(view, 'processing', user, method='get', pk=app.pk).status_code, 403)
        odai_view = self.cases[1][1]
        self.assertEqual(self.call(odai_view, 'processing', self.actor, method='get', pk=app.pk).status_code, 404)
        self.move(app, view, 'refer_council')
        response = self.call(view, 'processing', self.actor, pk=app.pk, data={'revision': 0, 'action': 'issue_interim', 'occurred_on': '2026-10-01', 'notes': 'Stale', 'confirmed': True})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(LicensingProcessingEvent.objects.count(), 1)
        self.assertEqual(self.call(self.cases[6][1], 'processing_queue', self.actor, method='get').status_code, 400)

    def test_acknowledgment_before_preliminary_review_and_locked_application_updates(self):
        app, view, _ = self.cases[0]
        self.actor.user_permissions.add(*Permission.objects.filter(content_type__app_label='license', codename__in=PERMISSIONS))
        result = self.move(app, view, 'acknowledge')
        self.assertEqual(result.status_code, 200, result.data)
        app.refresh_from_db()
        self.assertEqual(app.status, 'submitted')
        response = self.call(view, 'partial_update', self.owner, pk=app.pk, data={'status': 'completed'})
        self.assertEqual(response.status_code, 403)

    def test_calendar_boundaries(self):
        self.assertEqual(add_days(date(2026, 10, 2), 3, True), date(2026, 10, 7))
        self.assertEqual(add_months(date(2026, 1, 31), 3), date(2026, 4, 30))

    def test_processing_queues_filter_before_pagination_and_validate_sorting(self):
        app, view = self.prepare(0)
        result = self.call(view, 'processing_queue', self.actor, method='get', params={'queue': 'preliminary'})
        self.assertEqual(result.status_code, 200, result.data)
        self.assertEqual(result.data['results'][0]['id'], app.pk)
        self.assertIn('application_date', result.data['results'][0])
        self.assertEqual(self.move(app, view, 'refer_council').status_code, 200)
        for queue, count in [('council', 1), ('preliminary', 0), ('completed', 0)]:
            result = self.call(view, 'processing_queue', self.actor, method='get', params={'queue': queue, 'ordering': 'application_code'})
            self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(result.data['count'], count)
        for params in [{'queue': 'unknown'}, {'ordering': 'desk_reviewer__password'}]:
            self.assertEqual(self.call(view, 'processing_queue', self.actor, method='get', params=params).status_code, 400)

    def test_clarification_requires_response_and_processor_cannot_record_council_decision(self):
        app, view = self.prepare(0)
        review = LicensingPreliminaryReview.objects.get(application_id=app.pk)
        review.outcome = 'clarification_required'
        review.save()
        self.assertEqual(self.move(app, view, 'refer_council').status_code, 400)
        for action in ['request_clarification', 'record_response', 'refer_council']:
            result = self.move(app, view, action)
            self.assertEqual(result.status_code, 200, result.data)
        self.reviewer2.user_permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_process_licensing'))
        state = self.call(view, 'processing', self.reviewer2, method='get', pk=app.pk)
        self.assertEqual(state.status_code, 200)
        self.assertNotIn('issue_interim', [action['action'] for action in state.data['actions']])
        response = self.call(view, 'processing', self.reviewer2, pk=app.pk, data={'revision': state.data['revision'], 'action': 'issue_interim', 'occurred_on': '2026-10-01', 'notes': 'Forbidden', 'confirmed': True})
        self.assertEqual(response.status_code, 403)
