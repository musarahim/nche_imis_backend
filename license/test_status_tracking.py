from django.contrib.auth.models import Permission
from rest_framework.test import APITestCase

from . import test_reviewer_assignment as assignments
from .models import LicensingProcessing, LicensingProcessingEvent, LicensingStatusHistory
from .status_tracking import application_type, current_status


class LicensingStatusTrackingTests(APITestCase):
    setUp = assignments.LicensingReviewerAssignmentTests.setUp
    call = assignments.LicensingReviewerAssignmentTests.call
    assign = assignments.LicensingReviewerAssignmentTests.assign

    def status(self, app, view, user=None):
        return self.call(view, 'application_status', user or self.owner, method='get', pk=app.pk)

    def test_all_eight_application_types_have_owner_visible_status_and_history(self):
        for app, view, _ in self.cases:
            with self.subTest(view=view.__name__):
                response = self.status(app, view)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data['status_code'], 'submitted')
                self.assertEqual(response.data['application_type'], application_type(app))
                self.assertEqual(len(response.data['history']), 1)
                self.assertIsNotNone(response.data['updated_at'])
                self.assertEqual(self.assign(app, view).status_code, 200)
                response = self.status(app, view)
                self.assertEqual(response.data['status_code'], 'prelim_review')
                self.assertEqual([r['status_code'] for r in response.data['history']], ['submitted', 'prelim_review'])
                app.save(update_fields=['vision'])
                self.assertEqual(len(self.status(app, view).data['history']), 2)

    def test_other_institutions_and_route_types_cannot_read_status(self):
        from accounts.models import User
        from institutions.models import Institution
        outsider = User.objects.create_user('other-institution', 'other@example.test')
        Institution.objects.create(user=outsider, district=self.institution.district, name='Other Institution')
        for app, view, _ in self.cases:
            self.assertEqual(self.status(app, view, outsider).status_code, 404)
        app, _, _ = self.cases[0]
        self.assertEqual(self.status(app, self.cases[1][1]).status_code, 404)

    def test_exact_processing_stages_are_public_without_internal_evidence(self):
        app, view, _ = self.cases[2]
        state = LicensingProcessing.objects.create(application_type=application_type(app), application_id=app.pk, stage='verification', revision=1)
        LicensingProcessingEvent.objects.create(processing=state, revision=1, action='appoint_verification', from_stage='verification_appointment',
            to_stage='verification', actor=self.actor, occurred_on='2026-10-01', notes='Confidential council concerns', evidence={'report_reference': 'Internal-only'})
        app.status = 'under_council_review'
        app.save(update_fields=['status'])
        response = self.status(app, view)
        self.assertEqual(response.data['status_code'], 'verification')
        self.assertEqual(response.data['status'], 'Verification / Inspection in Progress')
        self.assertNotIn('Confidential', str(response.data))
        self.assertNotIn('Internal-only', str(response.data))
        self.assertNotIn('actor', str(response.data))
        result = self.call(view, 'retrieve', self.owner, method='get', pk=app.pk)
        self.assertEqual(result.data['tracking_status_code'], 'verification')
        self.assertEqual(result.data['tracking_status'], response.data['status'])
        state.stage = 'publication_pending'
        state.save()
        app.save(update_fields=['status'])
        response = self.status(app, view)
        self.assertEqual(response.data['status_code'], 'publication_pending')
        self.assertNotIn('Effective', response.data['status'])

    def test_old_records_do_not_invent_status_dates_and_legacy_events_are_sanitised(self):
        app, view, _ = self.cases[0]
        LicensingStatusHistory.objects.filter(application_type=application_type(app), application_id=app.pk).delete()
        response = self.status(app, view)
        self.assertIsNone(response.data['updated_at'])
        self.assertIsNone(response.data['history'][0]['recorded_at'])
        state = LicensingProcessing.objects.create(application_type=application_type(app), application_id=app.pk, stage='council_decision', revision=1)
        LicensingProcessingEvent.objects.create(processing=state, revision=1, action='refer_council', from_stage='preliminary_feedback',
            to_stage='council_decision', actor=self.actor, occurred_on='2026-10-01', notes='Private', evidence={})
        type(app).objects.filter(pk=app.pk).update(status='under_council_review')
        app.refresh_from_db()
        response = self.status(app, view)
        self.assertEqual(response.data['status_code'], 'council_decision')
        self.assertIsNotNone(response.data['history'][0]['recorded_at'])
        self.assertNotIn('Private', str(response.data))

    def test_processing_staff_can_track_and_status_endpoint_is_read_only(self):
        from django.urls import resolve
        from rest_framework.test import APIRequestFactory, force_authenticate
        app, view, _ = self.cases[0]
        self.reviewer2.user_permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_process_licensing'))
        self.assertEqual(self.status(app, view, self.reviewer2).status_code, 200)
        match = resolve(f'/interim-authority/{app.pk}/application-status/', urlconf='license.urls')
        request = APIRequestFactory().post('/status/', {'status': 'issued'}, format='json')
        force_authenticate(request, self.owner)
        self.assertEqual(match.func(request, **match.kwargs).status_code, 405)

    def test_preliminary_completion_takes_precedence_over_waiting_processing_state(self):
        app, _, _ = self.cases[0]
        LicensingProcessing.objects.create(application_type=application_type(app), application_id=app.pk, stage='awaiting_preliminary')
        app.status = 'prelim_feedback'
        self.assertEqual(current_status(app), 'prelim_feedback')
