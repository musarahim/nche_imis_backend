from django.contrib.auth.models import Group, Permission
from django.urls import resolve
from common.pagination import StandardResultsSetPagination
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from accounts.models import User
from common.models import District
from institutions.models import Institution

from .models import CertificationAndClassification, CharterApplication, IntrimAuthority, OTIProvisional, UniversityProvisionalLicense
from .views import (
    CertificationAndClassificationViewset, CharterApplicationViewset, DeskReviewersViewset,
    IntrimAuthorityODIViewset, IntrimAuthorityViewset, ODAIProvisionalLicenseViewset,
    ODICharterApplicationViewset, OTIProvisionalViewset, UniversityProvisionalLicenseViewset,
)


class LicensingReviewerAssignmentTests(APITestCase):
    def setUp(self):
        self.actor = User.objects.create_user('assigner', 'assigner@example.test', is_active=True)
        self.actor.user_permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_assign_reviewers'))
        self.reviewer = User.objects.create_user('reviewer', 'reviewer@example.test', is_active=True)
        self.reviewer2 = User.objects.create_user('reviewer2', 'reviewer2@example.test', is_active=True)
        group = Group.objects.create(name='ILA Desk Review Officer')
        self.reviewer.groups.add(group)
        self.reviewer2.groups.add(group)
        self.owner = User.objects.create_user('applicant', 'applicant@example.test', is_active=True)
        district = District.objects.create(name='Assignment District')
        self.institution = Institution.objects.create(user=self.owner, district=district, name='Assignment Institution')
        provisional = {'amount_of_land': 25, 'land_in_use': 20, 'year_obtained': '2026'}
        charter = {'has_provisional_license': True, 'amount_of_land_owned': 25, 'land_in_use': 20, 'year_obtained': '2026'}
        configurations = [
            (IntrimAuthority, IntrimAuthorityViewset, {'is_odai': False, 'has_title_deed': False}),
            (IntrimAuthority, IntrimAuthorityODIViewset, {'is_odai': True, 'has_title_deed': False}),
            (UniversityProvisionalLicense, UniversityProvisionalLicenseViewset, {**provisional, 'is_odai': False}),
            (UniversityProvisionalLicense, ODAIProvisionalLicenseViewset, {**provisional, 'is_odai': True}),
            (CharterApplication, CharterApplicationViewset, {**charter, 'is_odai': False}),
            (CharterApplication, ODICharterApplicationViewset, {**charter, 'is_odai': True}),
            (OTIProvisional, OTIProvisionalViewset, {}),
            (CertificationAndClassification, CertificationAndClassificationViewset, {'amount_of_land': 25, 'land_in_use': 20, 'year_obtained': 2026}),
        ]
        self.cases = []
        for model, view, defaults in configurations:
            parent = {view.institution_field: self.institution}
            app = model.objects.create(**parent, **defaults, status='submitted')
            self.cases.append((app, view, {**parent, **defaults}))

    def call(self, view, action, user, data=None, method='post', params=None, pk=None):
        factory = APIRequestFactory()
        request = factory.get('/licensing/', params or {}) if method == 'get' else factory.post('/licensing/', data or {}, format='json')
        if user:
            force_authenticate(request, user)
        return view.as_view({method: action})(request, **({'pk': pk} if pk is not None else {}))

    def assign(self, app, view, reviewer=None, ids=None, user=None):
        return self.call(view, 'assign_reviewer', user or self.actor, {
            'userId': (reviewer or self.reviewer).pk,
            'applications': ids if ids is not None else [app.pk],
        })

    def test_assign_and_reassign_all_eight_types_and_queue_visibility(self):
        for app, view, _ in self.cases:
            with self.subTest(view=view.__name__):
                with self.captureOnCommitCallbacks(execute=False) as notifications:
                    response = self.assign(app, view)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(len(notifications), 1)
                app.refresh_from_db()
                self.assertEqual(app.desk_reviewer, self.reviewer)
                self.assertEqual(app.status, 'prelim_review')
                self.assertEqual(self.call(view, 'submitted_applications', self.actor, method='get').data['count'], 0)
                queue = self.call(view, 'under_review', self.reviewer, method='get')
                self.assertEqual(queue.data['results'][0]['id'], app.pk)
                self.assertFalse(queue.data['can_assign'])
                response = self.assign(app, view, self.reviewer2)
                self.assertEqual(response.status_code, 200, response.data)
                app.refresh_from_db()
                self.assertEqual(app.desk_reviewer, self.reviewer2)
                self.assertEqual(self.call(view, 'under_review', self.reviewer, method='get').data['count'], 0)

    def test_repeat_assignment_is_idempotent_and_does_not_notify_twice(self):
        for app, view, _ in self.cases:
            self.assign(app, view)
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                response = self.assign(app, view)
            self.assertEqual(response.data['changed_count'], 0)
            self.assertEqual(len(callbacks), 0)

    def test_bulk_assignment_validates_whole_batch_before_writing(self):
        for app, view, defaults in self.cases:
            draft = type(app).objects.create(**defaults, status='draft')
            response = self.assign(app, view, ids=[app.pk, draft.pk])
            self.assertEqual(response.status_code, 400, response.data)
            app.refresh_from_db()
            self.assertIsNone(app.desk_reviewer)
            self.assertEqual(app.status, 'submitted')
            response = self.assign(app, view, ids=[app.pk, 999999])
            self.assertEqual(response.status_code, 400, response.data)

    def test_bulk_assignment_of_multiple_applications(self):
        for app, view, defaults in self.cases:
            second = type(app).objects.create(**defaults, status='submitted')
            response = self.assign(app, view, ids=[app.pk, second.pk])
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data['assigned_count'], 2)
            second.refresh_from_db()
            self.assertEqual(second.desk_reviewer, self.reviewer)

    def test_university_and_odai_ids_cannot_be_mixed(self):
        for index in [0, 2, 4]:
            university, view, _ = self.cases[index]
            odai, odai_view, _ = self.cases[index + 1]
            self.assertEqual(self.assign(university, view, ids=[university.pk, odai.pk]).status_code, 400)
            self.assertEqual(self.assign(odai, odai_view, ids=[university.pk, odai.pk]).status_code, 400)
            university.refresh_from_db()
            odai.refresh_from_db()
            self.assertIsNone(university.desk_reviewer)
            self.assertIsNone(odai.desk_reviewer)

    def test_applicants_and_reviewers_cannot_assign_or_open_candidates(self):
        for app, view, _ in self.cases:
            for user in [self.owner, self.reviewer]:
                self.assertEqual(self.assign(app, view, user=user).status_code, 403)
                self.assertEqual(self.call(view, 'assignment_candidates', user, method='get').status_code, 403)
            anonymous = self.call(view, 'assign_reviewer', None, {'userId': self.reviewer.pk, 'applications': [app.pk]})
            self.assertIn(anonymous.status_code, [401, 403])

    def test_ineligible_or_inactive_reviewers_and_malformed_payloads(self):
        inactive = User.objects.create_user('inactive', 'inactive@example.test', is_active=False)
        inactive.groups.add(Group.objects.get(name='ILA Desk Review Officer'))
        for app, view, _ in self.cases:
            for user in [inactive, self.owner]:
                self.assertEqual(self.assign(app, view, reviewer=user).status_code, 400)
            for payload in [{}, {'userId': self.reviewer.pk, 'applications': []},
                            {'userId': self.reviewer.pk, 'applications': [app.pk, app.pk]},
                            {'userId': 'bad', 'applications': [app.pk]},
                            {'userId': self.reviewer.pk, 'applications': '1,2'}]:
                self.assertEqual(self.call(view, 'assign_reviewer', self.actor, payload).status_code, 400)

    def test_module_specific_permissions_do_not_grant_other_assignment_types(self):
        actor = User.objects.create_user('interim-assigner', 'interim@example.test', is_active=True)
        actor.user_permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_assign_interim_authority_reviewer'))
        for index, (app, view, _) in enumerate(self.cases):
            response = self.assign(app, view, user=actor)
            self.assertEqual(response.status_code, 200 if index < 2 else 403, response.data)

    def test_existing_ila_department_role_can_assign(self):
        actor = User.objects.create_user('ila-head', 'ila-head@example.test', is_active=True)
        actor.groups.add(Group.objects.create(name='Head of Department(ILA)'))
        for app, view, _ in self.cases:
            self.assertEqual(self.assign(app, view, user=actor).status_code, 200)

    def test_reviewer_dropdown_requires_group_membership_even_with_review_permissions(self):
        charter_reviewer = User.objects.create_user('charter-only', 'charter@example.test', is_active=True)
        charter_reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_review_charter_application'))
        response = self.call(DeskReviewersViewset, 'list', self.actor, method='get', params={'review_permission': 'can_review_application'})
        self.assertNotIn(charter_reviewer.pk, [row['id'] for row in response.data])
        response = self.call(DeskReviewersViewset, 'list', self.actor, method='get', params={'review_permission': 'can_review_charter_application'})
        self.assertNotIn(charter_reviewer.pk, [row['id'] for row in response.data])
        self.assertEqual({row['id'] for row in response.data}, {self.reviewer.pk, self.reviewer2.pk})

    def test_nonmember_administrators_and_permission_holders_cannot_be_assigned_any_licensing_type(self):
        administrator = User.objects.create_user('admin-reviewer', 'admin@example.test', is_active=True, is_staff=True, is_superuser=True)
        administrator.groups.add(Group.objects.create(name='System Administrator'))
        permission_holder = User.objects.create_user('permission-reviewer', 'permission@example.test', is_active=True)
        permission_holder.user_permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_review_institutional_licensing'))
        permission_group = Group.objects.create(name='Other Reviewers')
        permission_group.permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_review_charter_application'))
        permission_holder.groups.add(permission_group)
        for params in [{}, {'review_permission': 'can_review_institutional_licensing'}]:
            response = self.call(DeskReviewersViewset, 'list', self.actor, method='get', params=params)
            self.assertEqual({row['id'] for row in response.data}, {self.reviewer.pk, self.reviewer2.pk})
        for app, view, _ in self.cases:
            for nominee in [administrator, permission_holder]:
                response = self.assign(app, view, reviewer=nominee)
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn('ILA Desk Review Officer', str(response.data))
            app.refresh_from_db()
            self.assertIsNone(app.desk_reviewer)
            self.assertEqual(app.status, 'submitted')

    def test_membership_changes_take_effect_without_relying_on_a_cached_reviewer_list(self):
        self.reviewer.groups.remove(Group.objects.get(name='ILA Desk Review Officer'))
        for app, view, _ in self.cases:
            self.assertEqual(self.assign(app, view).status_code, 400)
        response = self.call(DeskReviewersViewset, 'list', self.actor, method='get')
        self.assertNotIn(self.reviewer.pk, [row['id'] for row in response.data])
        self.reviewer.groups.add(Group.objects.get(name='ILA Desk Review Officer'))
        for app, view, _ in self.cases:
            self.assertEqual(self.assign(app, view).status_code, 200)

    def test_candidate_search_and_reviewers_cannot_read_unassigned_records(self):
        for app, view, _ in self.cases:
            response = self.call(view, 'assignment_candidates', self.actor, method='get', params={'search': 'not-a-match'})
            self.assertEqual(response.data['count'], 0)
            self.assertEqual(self.call(view, 'retrieve', self.reviewer, method='get', pk=app.pk).status_code, 404)
            self.assign(app, view)
            response = self.call(view, 'retrieve', self.reviewer, method='get', pk=app.pk)
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data['desk_reviewer'], self.reviewer.pk)

    def test_all_eight_endpoint_routers_expose_the_assignment_and_queue_actions(self):
        endpoints = ['interim-authority', 'interim-authority-odai', 'university-provisional-license',
                     'provisional-license-odai', 'charter-application', 'charter-application-odai',
                     'oti-provisional', 'certification-and-classification']
        for endpoint in endpoints:
            for suffix, verb, action in [('assign-desk-reviewer', 'post', 'assign_reviewer'),
                                         ('assignment-candidates', 'get', 'assignment_candidates'),
                                         ('assignment-filter-options', 'get', 'assignment_filter_options'),
                                         ('under-review', 'get', 'under_review'),
                                         ('submitted-applications', 'get', 'submitted_applications')]:
                match = resolve(f'/{endpoint}/{suffix}/', urlconf='license.urls')
                self.assertEqual(match.func.actions[verb], action)

    def test_candidate_queue_paginates_without_losing_permissions_or_reviewer_labels(self):
        app, view, defaults = self.cases[0]
        for _ in range(2):
            type(app).objects.create(**defaults, status='submitted')
        paginated = type('PaginatedLicensingView', (view,), {'pagination_class': StandardResultsSetPagination})
        first = self.call(paginated, 'assignment_candidates', self.actor, method='get', params={'page_size': 2})
        self.assertEqual(first.data['count'], 3)
        self.assertEqual(len(first.data['results']), 2)
        self.assertTrue(first.data['can_assign'])
        self.assertIsNotNone(first.data['next'])
        second = self.call(paginated, 'assignment_candidates', self.actor, method='get', params={'page_size': 2, 'page': 2})
        first_ids = {row['id'] for row in first.data['results']}
        self.assertTrue(first_ids.isdisjoint({row['id'] for row in second.data['results']}))

    def test_workload_totals_cover_all_licensing_types_without_counting_shared_tables_twice(self):
        for app, view, _ in self.cases:
            self.assign(app, view)
        self.reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='license', codename='can_review_institutional_licensing'))
        response = self.call(DeskReviewersViewset, 'list', self.actor, method='get')
        counts = {row['id']: row['assigned_application_count'] for row in response.data}
        self.assertEqual(counts[self.reviewer.pk], 8)
        self.assertEqual(counts[self.reviewer2.pk], 0)
        app, view, _ = self.cases[0]
        self.assign(app, view, reviewer=self.reviewer2)
        response = self.call(DeskReviewersViewset, 'list', self.actor, method='get')
        counts = {row['id']: row['assigned_application_count'] for row in response.data}
        self.assertEqual(counts[self.reviewer.pk], 7)
        self.assertEqual(counts[self.reviewer2.pk], 1)
        app.status = 'submitted'
        app.save(update_fields=['status'])
        response = self.call(DeskReviewersViewset, 'list', self.actor, method='get')
        self.assertEqual(next(row['assigned_application_count'] for row in response.data if row['id'] == self.reviewer2.pk), 0)

    def test_assignment_filters_are_scoped_to_each_application_type_and_apply_before_pagination(self):
        other_user = User.objects.create_user('filter-owner', 'filter@example.test', is_active=True)
        other_institution = Institution.objects.create(user=other_user, district=self.institution.district, name='Second Institution')
        for app, view, defaults in self.cases:
            other_defaults = {**defaults, view.institution_field: other_institution}
            other_app = type(app).objects.create(**other_defaults, status='prelim_review', desk_reviewer=self.reviewer)
            response = self.call(view, 'assignment_filter_options', self.actor, method='get')
            self.assertEqual({row['id'] for row in response.data['institutions']}, {self.institution.pk, other_institution.pk})
            response = self.call(view, 'assignment_candidates', self.actor, method='get', params={
                'institution': str(other_institution.pk), 'status': 'prelim_review',
            })
            self.assertEqual([row['id'] for row in response.data['results']], [other_app.pk])
            self.assertEqual(self.call(view, 'assignment_filter_options', self.owner, method='get').status_code, 403)
            self.assertEqual(self.call(view, 'assignment_candidates', self.actor, method='get', params={'institution': 'invalid'}).status_code, 400)
            self.assertEqual(self.call(view, 'assignment_candidates', self.actor, method='get', params={'status': 'draft'}).status_code, 400)
