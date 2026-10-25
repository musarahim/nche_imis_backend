from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from . import test_reviewer_assignment as assignment_tests
from .models import LicensingPreliminaryReview


class DynamicPreliminaryReviewTests(APITestCase):
    setUp = assignment_tests.LicensingReviewerAssignmentTests.setUp
    call = assignment_tests.LicensingReviewerAssignmentTests.call
    assign = assignment_tests.LicensingReviewerAssignmentTests.assign

    def get_review(self, app, view, user=None):
        return self.call(view, 'preliminary_review', user or self.reviewer, method='get', pk=app.pk)

    def save_review(self, app, view, state, **changes):
        payload = {'snapshot_hash': state['snapshot_hash'], 'revision': (state.get('review') or {}).get('revision', 0),
                   'observations': {}, 'summary': '', 'outcome': '', 'submit': False, **changes}
        return self.call(view, 'preliminary_review', self.reviewer, data=payload, pk=app.pk)

    def test_generates_fields_and_saves_drafts_for_all_eight_application_types(self):
        for app, view, _ in self.cases:
            self.assign(app, view)
            response = self.get_review(app, view)
            self.assertEqual(response.status_code, 200, response.data)
            keys = {field['key'] for field in response.data['fields']}
            self.assertIn('institution.district', keys)
            self.assertIn('institution.county', keys)
            self.assertIn('institution.phone', keys)
            self.assertIn('application.vision', keys)
            self.assertNotIn('application.desk_reviewer', keys)
            self.assertNotIn('institution.user', keys)
            self.assertTrue(response.data['can_edit'])
            result = self.save_review(app, view, response.data, observations={
                'application.vision': {'finding': 'clarification', 'comment': 'Please clarify this statement.'},
            })
            self.assertEqual(result.status_code, 200, result.data)
            self.assertEqual(result.data['review']['revision'], 1)
            self.assertEqual(self.get_review(app, view).data['review']['observations']['application.vision']['finding'], 'clarification')
            app.refresh_from_db()
            self.assertEqual(app.status, 'prelim_review')

    def test_only_assigned_active_group_member_can_edit_and_supervisors_are_read_only(self):
        for app, view, _ in self.cases:
            self.assign(app, view)
            state = self.get_review(app, view).data
            for user in [self.actor, self.owner, self.reviewer2]:
                response = self.call(view, 'preliminary_review', user, method='get', pk=app.pk)
                self.assertIn(response.status_code, [200, 403, 404])
                if response.status_code == 200:
                    self.assertFalse(response.data['can_edit'])
                response = self.call(view, 'preliminary_review', user, data={'snapshot_hash': state['snapshot_hash'], 'revision': 0}, pk=app.pk)
                self.assertIn(response.status_code, [403, 404])
            self.reviewer.groups.clear()
            self.assertIn(self.get_review(app, view).status_code, [403, 404])
            self.reviewer.groups.add(self.reviewer2.groups.first())

    def test_rejects_unknown_fields_blank_clarifications_and_missing_submission_summary(self):
        app, view, _ = self.cases[0]
        self.assign(app, view)
        state = self.get_review(app, view).data
        for changes in [
            {'observations': {'application.not_a_field': {'finding': 'note', 'comment': 'Unknown'}}},
            {'observations': {'application.vision': {'finding': 'clarification', 'comment': ''}}},
            {'submit': True},
            {'submit': True, 'confirmed': True, 'summary': 'Checked', 'outcome': 'no_concerns',
             'observations': {'application.vision': {'finding': 'clarification', 'comment': 'Explain this.'}}},
        ]:
            self.assertEqual(self.save_review(app, view, state, **changes).status_code, 400)
        self.assertEqual(LicensingPreliminaryReview.objects.count(), 0)

    def test_revision_and_application_change_conflicts_do_not_overwrite_comments(self):
        app, view, _ = self.cases[0]
        self.assign(app, view)
        state = self.get_review(app, view).data
        saved = self.save_review(app, view, state, summary='First saved summary')
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(self.save_review(app, view, state, summary='Stale tab').status_code, 409)
        app.vision = 'A changed application value'
        app.save(update_fields=['vision'])
        self.assertEqual(self.save_review(app, view, saved.data, summary='Old snapshot').status_code, 409)
        self.assertEqual(LicensingPreliminaryReview.objects.get().summary, 'First saved summary')

    def test_submission_freezes_snapshot_and_records_feedback_for_all_eight_types(self):
        for app, view, _ in self.cases:
            self.assign(app, view)
            state = self.get_review(app, view).data
            response = self.save_review(app, view, state, submit=True, confirmed=True, summary='All submitted information was reviewed.', outcome='no_concerns')
            self.assertEqual(response.status_code, 200, response.data)
            self.assertFalse(response.data['can_edit'])
            self.assertIsNotNone(response.data['review']['submitted_at'])
            app.refresh_from_db()
            self.assertEqual(app.status, 'prelim_feedback')
            app.vision = 'Later changed vision'
            app.save(update_fields=['vision'])
            reviewed = self.get_review(app, view)
            old_vision = next(field['value'] for field in state['fields'] if field['key'] == 'application.vision')
            self.assertEqual(next(field['value'] for field in reviewed.data['fields'] if field['key'] == 'application.vision'), old_vision)
            self.assertEqual(len(reviewed.data['history']), 1)
            self.assertEqual(self.save_review(app, view, response.data, summary='Attempt to edit submitted review').status_code, 403)
            pending = self.call(view, 'under_review', self.reviewer, method='get')
            self.assertEqual(pending.data['count'], 0)
            completed = self.call(view, 'under_review', self.reviewer, method='get', params={'review_status': 'completed'})
            self.assertEqual(completed.data['results'][0]['id'], app.pk)

    def test_reassignment_and_later_rounds_preserve_earlier_submitted_reviews(self):
        app, view, _ = self.cases[0]
        self.assign(app, view)
        state = self.get_review(app, view).data
        first = self.save_review(app, view, state, submit=True, confirmed=True, summary='Clarify the vision.', outcome='clarification_required', observations={
            'application.vision': {'finding': 'clarification', 'comment': 'Please clarify.'},
        })
        self.assertEqual(first.status_code, 200)
        app.status = 'submitted'
        app.save(update_fields=['status'])
        self.assign(app, view)
        new = self.get_review(app, view)
        self.assertIsNone(new.data['review'])
        self.assertEqual(len(new.data['history']), 1)
        second = self.save_review(app, view, new.data, summary='New review round')
        self.assertNotEqual(second.data['review']['id'], first.data['review']['id'])
        self.assertEqual(LicensingPreliminaryReview.objects.count(), 2)
        self.assign(app, view, reviewer=self.reviewer2)
        self.assertEqual(self.get_review(app, view).status_code, 404)

    def test_attachments_and_repeatable_items_are_individually_reviewable(self):
        app, view, _ = self.cases[2]
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        with override_settings(MEDIA_ROOT=directory.name):
            app.documents.create(title='Supporting evidence', document=SimpleUploadedFile('evidence.pdf', b'%PDF-1.4'))
            vehicle = app.vehicles.create(make='Toyota', registration_number='UBA 123A')
            app.university_provisional_objective_items.create(objective='A clear objective', order=1)
            self.assign(app, view)
            state = self.get_review(app, view)
            self.assertEqual(state.status_code, 200)
            keys = {field['key'] for field in state.data['fields']}
            self.assertIn(f'vehicles.{vehicle.pk}.registration_number', keys)
            files = [field for field in state.data['fields'] if field['kind'] == 'file' and field['value']]
            self.assertTrue(any('evidence.pdf' in field['value'] for field in files))
            self.assertTrue(any(field['value'] == 'A clear objective' for field in state.data['fields']))
