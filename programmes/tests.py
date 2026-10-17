from datetime import timedelta
from decimal import Decimal
from smtplib import SMTPException
from tempfile import TemporaryDirectory
from unittest.mock import patch

from accounts.models import User
from common.models import District
from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from institutions.models import Institution
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from .models import PreliminaryReview, Program, ProgramAccreditation, ProgrammeAssessment, ProgrammeAssessmentInvoice, ProgrammeInvoice, DeskReviewInvoiceLine, DeskReviewPaymentVerification
from .views import ProgrammeAccreditationViewset, ProgrammeReviewersViewset, ProgramAccessorViewset


class SubmittedApplicationSearchTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user('search-owner', 'search-owner@example.test', is_active=True)
        district = District.objects.create(name='Search District')
        self.institution = Institution.objects.create(user=self.owner, name='Search University', district=district)
        self.computing = ProgramAccreditation.objects.create(
            institution=self.institution, programme_name='Computer Science', program_level='bachelor', duration=6, programme_category='stem',
        )
        self.arts = ProgramAccreditation.objects.create(
            institution=self.institution, programme_name='Fine Art', program_level='diploma', duration=4, programme_category='humanities',
        )
        ProgramAccreditation.objects.create(
            institution=self.institution, programme_name='Computer Science Reviewed', program_level='bachelor',
            duration=6, status='under_review',
        )

    def search(self, term='', **filters):
        request = APIRequestFactory().get('/submitted-applications/', {'search': term, **filters})
        force_authenticate(request, self.owner)
        return ProgrammeAccreditationViewset.as_view({'get': 'submitted_applications'})(request)

    def test_searches_programme_institution_application_number_and_level(self):
        for term, expected in [
            ('computer', {self.computing.pk}), ('Search University', {self.computing.pk, self.arts.pk}),
            (self.computing.application_number, {self.computing.pk}), ('diploma', {self.arts.pk}),
        ]:
            with self.subTest(term=term):
                response = self.search(term)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual({row['id'] for row in response.data['results']}, expected)

    def test_no_matches_returns_empty_paginated_results(self):
        response = self.search('unmatched programme')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

    def test_combines_institution_category_and_search_filters(self):
        response = self.search('computer', institution=self.institution.pk, programme_category='stem')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual([row['id'] for row in response.data['results']], [self.computing.pk])
        self.assertEqual(self.search('computer', institution=self.institution.pk, programme_category='humanities').data['results'], [])
        self.assertEqual([row['id'] for row in self.search(programme_category='humanities').data['results']], [self.arts.pk])

    def test_filter_options_include_distinct_scoped_institutions_and_model_categories(self):
        other_owner = User.objects.create_user('filter-owner', 'filter-owner@example.test', is_active=True)
        other = Institution.objects.create(user=other_owner, name='Hidden Institution', district=self.institution.district)
        ProgramAccreditation.objects.create(institution=other, programme_name='Hidden Programme', program_level='bachelor', duration=6)
        request = APIRequestFactory().get('/submitted-application-filter-options/')
        force_authenticate(request, self.owner)
        response = ProgrammeAccreditationViewset.as_view({'get': 'submitted_application_filter_options'})(request)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['institutions'], [{'id': self.institution.pk, 'name': self.institution.name}])
        self.assertEqual(response.data['programme_categories'], [{'value': value, 'label': label} for value, label in ProgramAccreditation.CATEGORY])
        self.assertEqual(self.search(institution=other.pk).data['results'], [])

    def test_invalid_filters_return_validation_errors(self):
        for filters in [{'institution': 'invalid'}, {'programme_category': 'invalid'}]:
            response = self.search(**filters)
            self.assertEqual(response.status_code, 400, response.data)

    def test_search_preserves_institution_scope(self):
        other_owner = User.objects.create_user('other-search-owner', 'other-search@example.test', is_active=True)
        other = Institution.objects.create(user=other_owner, name='Other University', district=self.institution.district)
        ProgramAccreditation.objects.create(institution=other, programme_name='Hidden Programme', program_level='bachelor', duration=6)
        self.assertEqual(self.search('Hidden Programme').data['results'], [])


class ProgrammeReviewerWorkloadTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user('workload-owner', 'workload-owner@example.test', is_active=True)
        district = District.objects.create(name='Workload District')
        self.institution = Institution.objects.create(user=self.owner, name='Workload University', district=district)
        reviewers = Group.objects.create(name='Programme Reviewers')
        self.busy = User.objects.create_user('busy-reviewer', 'busy@example.test', is_active=True)
        self.idle = User.objects.create_user('idle-reviewer', 'idle@example.test', is_active=True)
        self.busy.groups.add(reviewers)
        self.idle.groups.add(reviewers)
        other = User.objects.create_user('non-reviewer', 'non-reviewer@example.test', is_active=True)
        for index, (reviewer, status) in enumerate([
            (self.busy, 'under_review'), (self.busy, 'approved'), (other, 'under_review'), (None, 'submitted'),
        ]):
            application = ProgramAccreditation.objects.create(
                institution=self.institution, programme_name=f'Programme {index}', program_level='bachelor',
                duration=6, status=status, preliminary_reviewer=reviewer,
            )
            if index == 0:
                self.pending_application = application
                # Another reviewer's record must not remove this assignment from the count.
                PreliminaryReview.objects.create(application=application, reviewer=other, expert_progression='yes')
            elif index == 1:
                PreliminaryReview.objects.create(application=application, reviewer=self.busy, expert_progression='yes')

    def test_counts_only_assignments_without_a_review_by_the_assigned_reviewer(self):
        request = APIRequestFactory().get('/programme-reviewers/')
        force_authenticate(request, self.owner)
        response = ProgrammeReviewersViewset.as_view({'get': 'list'})(request)
        self.assertEqual(response.status_code, 200, response.data)
        rows = {row['id']: row for row in response.data}
        self.assertEqual(set(rows), {self.busy.pk, self.idle.pk})
        self.assertEqual(rows[self.busy.pk]['assigned_application_count'], 1)
        self.assertEqual(rows[self.idle.pk]['assigned_application_count'], 0)
        self.assertEqual(rows[self.busy.pk]['name'], 'busy-reviewer')

    def test_count_drops_when_assigned_reviewer_records_a_review(self):
        PreliminaryReview.objects.create(application=self.pending_application, reviewer=self.busy, expert_progression='yes')
        request = APIRequestFactory().get('/programme-reviewers/')
        force_authenticate(request, self.owner)
        response = ProgrammeReviewersViewset.as_view({'get': 'list'})(request)
        self.assertEqual(response.status_code, 200, response.data)
        rows = {row['id']: row for row in response.data}
        self.assertEqual(rows[self.busy.pk]['assigned_application_count'], 0)

    def test_requires_authentication(self):
        request = APIRequestFactory().get('/programme-reviewers/')
        response = ProgrammeReviewersViewset.as_view({'get': 'list'})(request)
        self.assertIn(response.status_code, [401, 403])

    def retrieve_application(self, user):
        request = APIRequestFactory().get(f'/programme-accreditation/{self.pending_application.pk}/')
        force_authenticate(request, user)
        return ProgrammeAccreditationViewset.as_view({'get': 'retrieve'})(request, pk=self.pending_application.pk)

    def test_assigned_preliminary_reviewer_can_retrieve_application(self):
        self.assertEqual(self.retrieve_application(self.busy).status_code, 200)
        self.assertEqual(self.retrieve_application(self.idle).status_code, 404)

    def test_assigned_assessor_can_retrieve_application(self):
        self.idle.groups.add(Group.objects.create(name='Programme Assessors'))
        self.pending_application.assessor = self.idle
        self.pending_application.save(update_fields=['assessor'])
        self.assertEqual(self.retrieve_application(self.idle).status_code, 200)
        self.pending_application.assessor = None
        self.pending_application.save(update_fields=['assessor'])
        self.assertEqual(self.retrieve_application(self.idle).status_code, 404)

    def test_detail_access_does_not_allow_reviewer_to_edit_application(self):
        request = APIRequestFactory().patch(f'/programme-accreditation/{self.pending_application.pk}/', {'programme_name': 'Changed'})
        force_authenticate(request, self.busy)
        response = ProgrammeAccreditationViewset.as_view({'patch': 'partial_update'})(request, pk=self.pending_application.pk)
        self.assertEqual(response.status_code, 404)


@override_settings(
    ROOT_URLCONF='programmes.test_urls',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class ProgrammeRenewalWorkflowTests(APITestCase):
    def setUp(self):
        district = District.objects.create(name='Renewal District')
        self.owner = User.objects.create_user('renewal-owner', 'renewal-owner@example.test', is_active=True)
        self.other = User.objects.create_user('renewal-other', 'renewal-other@example.test', is_active=True)
        self.manager = User.objects.create_user('renewal-manager', 'renewal-manager@example.test', is_active=True)
        self.manager.user_permissions.add(Permission.objects.get(codename='can_approve_programme_at_management_level'))
        self.institution = Institution.objects.create(user=self.owner, name='Renewal Institution', district=district)
        self.other_institution = Institution.objects.create(user=self.other, name='Other Renewal Institution', district=district)
        today = timezone.localdate()
        self.programme = Program.objects.create(
            institution=self.institution, programme_name='Computing', program_level='bachelor',
            accreditation_date=today - timedelta(days=365), expiry_date=today + timedelta(days=365), status='active',
        )
        self.url = '/programme-accreditation/'

    def payload(self, **overrides):
        return {
            'application_type': 're-accredit', 'program_to_renew': self.programme.pk,
            'programme_name': 'Computing', 'program_level': 'bachelor',
            'duration': 6, 'duration_type': 'semester',
            'campus': 'Main', 'programme_category': 'stem', **overrides,
        }

    def submit(self):
        self.client.force_authenticate(self.owner)
        with patch('programmes.views.render_to_string', return_value='Submitted'):
            return self.client.post(self.url, self.payload())

    def test_renewal_submission_and_early_approval_preserve_history(self):
        response = self.submit()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['programme_name'], 'Computing')
        self.assertNotIn('program_name', response.data)
        application = ProgramAccreditation.objects.get(pk=response.data['id'])
        old_expiry = self.programme.expiry_date
        self.assertEqual(application.previous_expiry_date, old_expiry)
        self.assertEqual(application.program_to_renew_id, self.programme.pk)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.post(f'{self.url}{application.pk}/management-decision/', {'decision': 'approved'}).status_code, 400)
        application.status = 'progressed_to_management'
        application.save(update_fields=['status'])
        response = self.client.post(f'{self.url}{application.pk}/management-decision/', {'decision': 'approved'})
        self.assertEqual(response.status_code, 200, response.data)
        self.programme.refresh_from_db()
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        self.assertEqual(application.previous_expiry_date, old_expiry)
        self.assertEqual(self.programme.expiry_date.year, old_expiry.year + 5)
        self.assertEqual(application.approved_expiry_date, self.programme.expiry_date)
        self.assertEqual(self.programme.applications.filter(pk=application.pk).count(), 1)
        self.assertEqual(self.client.post(f'{self.url}{application.pk}/management-decision/', {'decision': 'approved'}).status_code, 400)

    def test_rejects_foreign_unaccredited_duplicate_and_modified_programmes(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 400)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(self.url, self.payload(programme_name='Different')).status_code, 400)
        self.assertEqual(self.client.post(self.url, self.payload(application_type='accredit')).status_code, 400)
        self.programme.expiry_date = None
        self.programme.save(update_fields=['expiry_date'])
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 400)
        self.programme.expiry_date = timezone.localdate() + timedelta(days=365)
        self.programme.save(update_fields=['expiry_date'])
        self.assertEqual(self.submit().status_code, 201)
        self.assertEqual(self.client.post(self.url, self.payload()).status_code, 400)

    def test_cannot_patch_status_or_approve_without_permission(self):
        response = self.submit()
        application_id = response.data['id']
        self.assertEqual(self.client.get(f'{self.url}{application_id}/').status_code, 200)
        self.assertEqual(self.client.patch(f'{self.url}{application_id}/', {'status': 'approved'}).status_code, 400)
        self.assertEqual(self.client.post(f'{self.url}{application_id}/management-decision/', {'decision': 'approved'}).status_code, 403)
        self.assertEqual(self.client.post(f'/institution-programmes/{self.programme.pk}/', {'status': 'active'}).status_code, 405)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'{self.url}{application_id}/').status_code, 404)
        self.client.force_authenticate(self.manager)
        self.assertEqual(self.client.get(f'{self.url}{application_id}/').status_code, 200)
        self.assertEqual(self.client.get(f'{self.url}999999999/').status_code, 404)

    def test_renewal_options_are_scoped_to_institution(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get('/institution-programmes/renewal-options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [self.programme.pk])
        self.assertEqual(response.data[0]['programme_name'], 'Computing')
        self.assertNotIn('program_name', response.data[0])
        self.submit()
        self.assertEqual(self.client.get('/institution-programmes/renewal-options/').data, [])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/institution-programmes/renewal-options/').data, [])

    def test_new_application_approval_creates_programme(self):
        self.client.force_authenticate(self.owner)
        payload = self.payload(application_type='accredit', programme_name='Engineering')
        payload.pop('program_to_renew')
        with patch('programmes.views.render_to_string', return_value='Submitted'):
            response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 201, response.data)
        application = ProgramAccreditation.objects.get(pk=response.data['id'])
        application.status = 'progressed_to_management'
        application.save(update_fields=['status'])
        self.client.force_authenticate(self.manager)
        response = self.client.post(f'{self.url}{application.pk}/management-decision/', {'decision': 'approved'})
        self.assertEqual(response.status_code, 200, response.data)
        programme = Program.objects.get(institution=self.institution, programme_name='Engineering')
        self.assertEqual(programme.applications.filter(pk=application.pk).count(), 1)
        self.assertEqual(application.pk, response.data['id'])

    def test_rejection_does_not_change_programme_dates(self):
        response = self.submit()
        application = ProgramAccreditation.objects.get(pk=response.data['id'])
        application.status = 'progressed_to_management'
        application.save(update_fields=['status'])
        old_expiry = self.programme.expiry_date
        self.client.force_authenticate(self.manager)
        with patch.object(ProgrammeAccreditationViewset, '_send_rejection_email'):
            response = self.client.post(f'{self.url}{application.pk}/management-decision/', {'decision': 'rejected', 'reason': 'Insufficient evidence'})
        self.assertEqual(response.status_code, 200, response.data)
        self.programme.refresh_from_db()
        self.assertEqual(self.programme.expiry_date, old_expiry)
        application.refresh_from_db()
        self.assertEqual(application.rejection_reason, 'Insufficient evidence')


@override_settings(
    ROOT_URLCONF='programmes.test_urls',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class ReviewInvoiceWorkflowTests(APITestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        media = override_settings(MEDIA_ROOT=directory.name)
        media.enable()
        self.addCleanup(media.disable)
        self.accounts = User.objects.create_user('accounts', 'accounts@example.test', is_active=True)
        self.accounts.groups.add(Group.objects.create(name='Finance Officer'))
        self.head = User.objects.create_user('head', 'head@example.test', is_active=True)
        self.head.groups.add(Group.objects.create(name='Head Programme Accreditation'))
        self.owner = User.objects.create_user('owner', 'owner@example.test', is_active=True)
        self.other = User.objects.create_user('other', 'other@example.test', is_active=True)
        district = District.objects.create(name='Test District')
        self.institution = Institution.objects.create(user=self.owner, name='Institution A', district=district)
        Institution.objects.create(user=self.other, name='Institution B', district=district)
        self.application = ProgramAccreditation.objects.create(
            institution=self.institution, programme_name='Computing', program_level='degree', duration=6, status='reviewed',
        )
        self.invoice = ProgrammeAssessmentInvoice.objects.create(institution=self.institution, desk_review_fee=Decimal('100.00'))
        DeskReviewInvoiceLine.objects.create(invoice=self.invoice, application=self.application,
            application_number=self.application.application_number, programme_name=self.application.programme_name,
            desk_review_fee=Decimal('100.00'))
        self.application.status = 'invoiced'
        self.application.save(update_fields=['status'])
        self.url = f'/invoices/{self.invoice.pk}/'

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def invoice_data(self, fee='100.00'):
        return {'institution_id': self.institution.pk, 'lines': [{'application': self.application.pk, 'desk_review_fee': fee}]}

    def acknowledge(self):
        amount = ProgrammeAssessmentInvoice.objects.get(pk=self.invoice.pk).grand_total
        return self.client.post(self.url + 'reconcile-invoice/', {'verified_amount': str(amount)}, format='json')

    def payment(self, **overrides):
        return {
            'payment_reference': ' BANK-123 ',
            'payment_date': str(timezone.localdate()),
            'payment_receipt': SimpleUploadedFile('receipt.pdf', b'%PDF-1.4\nTest receipt', content_type='application/pdf'),
            **overrides,
        }

    def issue(self):
        self.authenticate(self.head)
        response = self.client.post(self.url + 'send-invoice/')
        self.assertEqual(response.status_code, 200, response.data)

    def test_full_workflow_recalculates_notifies_and_acknowledges(self):
        self.authenticate(self.head)
        response = self.client.patch(self.url, {'lines': self.invoice_data('250.00')['lines']}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['administrative_fee'], '25.00')
        self.assertEqual(response.data['grand_total'], '275.00')
        self.issue()
        self.assertEqual(mail.outbox[-1].to, ['owner@example.test'])
        self.assertEqual(mail.outbox[-1].attachments[0][2], 'application/pdf')
        self.authenticate(self.owner)
        self.assertEqual(self.client.get('/invoices/').data['count'], 1)
        response = self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['status'], 'Paid')
        self.assertFalse(response.data['cleared'])
        self.assertEqual(response.data['payment_reference'], 'BANK-123')
        self.assertIn('accounts@example.test', mail.outbox[-1].to)
        self.assertNotIn('head@example.test', mail.outbox[-1].to)
        self.authenticate(self.accounts)
        response = self.acknowledge()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['cleared'])
        self.assertEqual(response.data['status'], 'Reconciled')
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'invoice_reconciled')
        self.assertTrue(self.application.is_paid)
        self.assertEqual(mail.outbox[-1].to, ['owner@example.test'])

    def test_cleared_desk_review_becomes_assignable_without_expert_recommendation(self):
        ready_url = '/programme-accreditation/ready-for-assessment/'
        self.authenticate(self.head)
        self.assertEqual(self.client.get(ready_url).data['count'], 0)
        self.issue()
        self.authenticate(self.owner)
        self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart')
        self.authenticate(self.head)
        self.assertEqual(self.client.get(ready_url).data['count'], 0)
        self.head.user_permissions.add(Permission.objects.get(codename='can_assign_assessors'))
        self.head = User.objects.get(pk=self.head.pk)
        self.authenticate(self.head)
        assessor = User.objects.create_user('assessor', 'assessor@example.test', is_active=True)
        assessor.groups.add(Group.objects.create(name='Programme Assessors'))
        self.assertEqual(self.client.post('/programme-accreditation/assign-assessor/', {
            'userId': assessor.pk, 'applications': [self.application.pk],
        }, format='json').status_code, 400)
        self.authenticate(self.accounts)
        self.assertEqual(self.acknowledge().status_code, 200)
        self.authenticate(self.head)
        response = self.client.get(ready_url)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.application.pk)
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_paid)
        response = self.client.post('/programme-accreditation/assign-assessor/', {
            'userId': assessor.pk, 'applications': [self.application.pk],
        }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.application.refresh_from_db()
        self.assertEqual(self.application.assessor_id, assessor.pk)
        self.assertEqual(self.application.status, 'under_assessment')
        self.assertEqual(self.client.get(ready_url).data['count'], 0)

    def test_cleared_visit_invoice_does_not_unlock_desk_review_assessment(self):
        invoice = ProgrammeInvoice.objects.create(
            application=self.application, status='paid', cleared=False,
            grand_total=Decimal('100.00'), payment_reference='BANK-456',
            payment_receipt=SimpleUploadedFile('receipt.pdf', b'%PDF-1.4\nTest receipt', content_type='application/pdf'),
        )
        self.application.status = 'invoiced'
        self.application.save(update_fields=['status'])
        self.authenticate(self.head)
        ready_url = '/programme-accreditation/ready-for-assessment/'
        self.assertEqual(self.client.get(ready_url).data['count'], 0)
        self.authenticate(self.owner)
        self.assertEqual(self.client.post(f'/programme-invoices/{invoice.pk}/reconcile-invoice/').status_code, 403)
        self.authenticate(self.accounts)
        self.assertEqual(self.client.post(f'/programme-invoices/{invoice.pk}/reconcile-invoice/').status_code, 200)
        self.authenticate(self.head)
        response = self.client.get(ready_url)
        self.assertEqual(response.data['count'], 0)
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_paid)

    def test_drafts_hidden_and_other_institutions_cannot_access_or_pay(self):
        self.authenticate(self.owner)
        self.assertEqual(self.client.get('/invoices/').data['count'], 0)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.issue()
        self.authenticate(self.other)
        self.assertEqual(self.client.get('/invoices/').data['count'], 0)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 404)

    def test_institution_cannot_edit_issue_acknowledge_or_delete(self):
        self.issue()
        self.authenticate(self.owner)
        self.assertEqual(self.client.patch(self.url, {'desk_review_fee': '1.00'}).status_code, 403)
        self.assertEqual(self.client.post(self.url + 'send-invoice/').status_code, 403)
        self.assertEqual(self.acknowledge().status_code, 403)
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        self.assertEqual(self.client.post('/invoices/', {'application': self.application.pk, 'desk_review_fee': '1.00'}).status_code, 403)

    def test_anonymous_cannot_access(self):
        self.assertEqual(self.client.get('/invoices/').status_code, 401)
        self.assertEqual(self.client.post(self.url + 'send-invoice/').status_code, 401)

    def test_head_can_create_edit_and_send_but_cannot_approve_payment(self):
        self.invoice.delete()
        self.application.status = 'reviewed'
        self.application.save(update_fields=['status'])
        self.authenticate(self.head)
        response = self.client.post('/invoices/', self.invoice_data(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'Draft')
        self.assertFalse(response.data['can_manage'])
        self.assertTrue(response.data['can_send'])
        url = f'/invoices/{response.data["id"]}/'
        self.assertEqual(self.client.patch(url, {'lines': self.invoice_data('200.00')['lines']}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url + 'send-invoice/').status_code, 200)
        self.authenticate(self.owner)
        self.assertEqual(self.client.post(url + 'add-payment-details/', self.payment(), format='multipart').status_code, 200)
        self.authenticate(self.head)
        self.assertEqual(self.client.post(url + 'reconcile-invoice/').status_code, 403)
        self.assertEqual(self.client.post('/invoices/', self.invoice_data(), format='json').status_code, 400)

    def test_accounts_can_only_approve_payments_even_with_invoice_permissions(self):
        self.accounts.user_permissions.add(*Permission.objects.filter(codename__in=[
            'can_manage_invoices', 'add_programmeassessmentinvoice', 'change_programmeassessmentinvoice',
        ]))
        self.authenticate(self.accounts)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data['can_manage'])
        self.assertFalse(response.data['can_send'])
        self.assertEqual(self.client.patch(self.url, {'desk_review_fee': '200.00'}).status_code, 403)
        self.assertEqual(self.client.post(self.url + 'send-invoice/').status_code, 403)
        self.assertEqual(self.client.post('/invoices/', {'application': self.application.pk, 'desk_review_fee': '100.00'}).status_code, 403)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'draft')
        self.assertEqual(len(mail.outbox), 0)

    def test_cannot_bypass_actions_or_change_application(self):
        self.authenticate(self.head)
        for data in [{'status': 'reconciled'}, {'cleared': True}, {'grand_total': '1.00'}, {'application': self.application.pk}, {'payment_reference': 'fake'}]:
            with self.subTest(data=data):
                self.assertEqual(self.client.patch(self.url, data).status_code, 400)

    def test_invalid_fees_rejected(self):
        self.authenticate(self.head)
        for fee in ['0', '-1', 'NaN', '90909090.91', '12.345']:
            with self.subTest(fee=fee):
                self.assertEqual(self.client.patch(self.url, {'lines': self.invoice_data(fee)['lines']}, format='json').status_code, 400)

    def test_issued_invoice_locked_and_transitions_cannot_repeat(self):
        self.issue()
        self.assertEqual(self.client.patch(self.url, {'desk_review_fee': '200.00'}).status_code, 400)
        self.assertEqual(self.client.post(self.url + 'send-invoice/').status_code, 400)
        self.authenticate(self.accounts)
        self.assertEqual(self.acknowledge().status_code, 400)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 403)
        self.authenticate(self.owner)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 200)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 400)
        self.authenticate(self.accounts)
        self.assertEqual(self.acknowledge().status_code, 200)
        self.assertEqual(self.acknowledge().status_code, 400)

    def test_payment_validation(self):
        self.issue()
        self.authenticate(self.owner)
        invalid = [
            {'payment_reference': '   '},
            {'payment_date': str(timezone.localdate() + timedelta(days=1))},
            {'payment_receipt': SimpleUploadedFile('receipt.pdf', b'not a pdf')},
            {'payment_receipt': SimpleUploadedFile('receipt.html', b'<html>')},
            {'payment_receipt': SimpleUploadedFile('receipt.pdf', b'%PDF-' + b'x' * (2 * 1024 * 1024))},
        ]
        for overrides in invalid:
            with self.subTest(fields=list(overrides)):
                self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(**overrides), format='multipart').status_code, 400)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', {'payment_reference': 'ref'}, format='multipart').status_code, 400)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'issued')

    def test_email_failure_does_not_advance_invoice(self):
        self.authenticate(self.head)
        with patch('programmes.review_invoice_views.EmailMessage.send', side_effect=SMTPException('offline')):
            self.assertEqual(self.client.post(self.url + 'send-invoice/').status_code, 503)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'draft')
        self.issue()
        self.authenticate(self.owner)
        with patch('programmes.review_invoice_views.EmailMessage.send', side_effect=SMTPException('offline')):
            self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 503)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'issued')
        self.assertFalse(self.invoice.payment_receipt)

    def create_grouped_invoice(self):
        self.invoice.delete()
        self.application.status = 'reviewed'
        self.application.save(update_fields=['status'])
        second = ProgramAccreditation.objects.create(institution=self.institution, programme_name='Business',
            program_level='degree', duration=6, status='reviewed')
        self.authenticate(self.head)
        response = self.client.post('/invoices/', {'institution_id': self.institution.pk, 'lines': [
            {'application': self.application.pk, 'desk_review_fee': '100.00'},
            {'application': second.pk, 'desk_review_fee': '200.00'},
        ]}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['grand_total'], '330.00')
        self.assertEqual(response.data['programme_count'], 2)
        self.invoice = ProgrammeAssessmentInvoice.objects.get(pk=response.data['id'])
        self.url = f'/invoices/{self.invoice.pk}/'
        return second

    def test_grouped_invoice_partial_payment_blocks_every_programme_until_fully_verified(self):
        second = self.create_grouped_invoice()
        self.issue()
        self.authenticate(self.owner)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 200)
        self.authenticate(self.accounts)
        response = self.client.post(self.url + 'reconcile-invoice/', {'verified_amount': '100.00'}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(response.data['cleared'])
        self.assertEqual(response.data['outstanding_balance'], '230.00')
        self.assertEqual(response.data['verifications'][0]['verified_by'], 'accounts')
        self.assertFalse(ProgramAccreditation.objects.filter(pk__in=[self.application.pk, second.pk], is_paid=True).exists())
        self.authenticate(self.head)
        self.head.user_permissions.add(Permission.objects.get(codename='can_assign_assessors'))
        self.head = User.objects.get(pk=self.head.pk)
        self.authenticate(self.head)
        assessor = User.objects.create_user('batch-assessor', 'batch@example.test', is_active=True)
        assessor.groups.add(Group.objects.create(name='Programme Assessors'))
        payload = {'userId': assessor.pk, 'applications': [self.application.pk, second.pk]}
        self.assertEqual(self.client.get('/programme-accreditation/ready-for-assessment/').data['count'], 0)
        response = self.client.post('/programme-accreditation/assign-assessor/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.data['blocked_programmes']), 2)
        self.authenticate(self.accounts)
        self.assertEqual(self.acknowledge().status_code, 200)
        self.assertEqual(DeskReviewPaymentVerification.objects.filter(invoice=self.invoice).count(), 2)
        self.authenticate(self.head)
        self.assertEqual(self.client.get('/programme-accreditation/ready-for-assessment/').data['count'], 2)
        self.assertEqual(self.client.post('/programme-accreditation/assign-assessor/', payload, format='json').status_code, 200)
        self.assertEqual(ProgramAccreditation.objects.filter(pk__in=payload['applications'], assessor=assessor, status='under_assessment').count(), 2)

    def test_grouped_invoice_rejects_foreign_duplicate_unready_and_already_invoiced_programmes(self):
        second = self.create_grouped_invoice()
        foreign = ProgramAccreditation.objects.create(institution=self.other.institution, programme_name='Foreign', program_level='degree', duration=6, status='reviewed')
        for lines in [
            [{'application': foreign.pk, 'desk_review_fee': '100.00'}],
            self.invoice_data()['lines'] * 2,
            [{'application': second.pk, 'desk_review_fee': '100.00'}],
            [],
        ]:
            with self.subTest(lines=lines):
                self.assertEqual(self.client.post('/invoices/', {'institution_id': self.institution.pk, 'lines': lines}, format='json').status_code, 400)
        foreign.institution = self.institution
        foreign.status = 'submitted'
        foreign.save()
        self.assertEqual(self.client.post('/invoices/', {'institution_id': self.institution.pk,
            'lines': [{'application': foreign.pk, 'desk_review_fee': '100.00'}]}, format='json').status_code, 400)

    def test_draft_lines_edit_totals_and_issued_lines_are_locked(self):
        second = self.create_grouped_invoice()
        response = self.client.patch(self.url, {'lines': [{'application': second.pk, 'desk_review_fee': '50.05'}]}, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['grand_total'], '55.05')
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, 'reviewed')
        self.issue()
        self.assertEqual(self.client.patch(self.url, {'lines': self.invoice_data()['lines']}, format='json').status_code, 400)
        self.assertEqual(self.invoice.lines.get().application_id, second.pk)

    def test_verification_requires_valid_cumulative_amount_and_rolls_back_on_email_failure(self):
        self.issue()
        self.authenticate(self.owner)
        self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart')
        self.authenticate(self.accounts)
        for payload in [{}, {'verified_amount': '111'}, {'verified_amount': 'NaN'}, {'verified_amount': '0'}, {'verified_amount': '-1'}, {'verified_amount': '2.345'}]:
            self.assertEqual(self.client.post(self.url + 'reconcile-invoice/', payload, format='json').status_code, 400)
        with patch('programmes.review_invoice_views.EmailMessage.send', side_effect=SMTPException('offline')):
            self.assertEqual(self.acknowledge().status_code, 503)
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.verified_amount, 0)
        self.assertFalse(self.invoice.verifications.exists())
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/', {'verified_amount': '50.00'}, format='json').status_code, 200)
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/', {'verified_amount': '50.00'}, format='json').status_code, 400)

    def test_institution_options_and_pdf_access_follow_permissions(self):
        self.authenticate(self.accounts)
        self.assertFalse(self.client.get('/invoices/creation-options/').data['can_create'])
        self.assertEqual(self.client.get('/invoices/available-programmes/', {'institution_id': self.institution.pk}).status_code, 403)
        self.authenticate(self.head)
        self.assertTrue(self.client.get('/invoices/creation-options/').data['can_create'])
        self.assertEqual(self.client.get('/invoices/available-programmes/', {'institution_id': self.institution.pk}).data, [])
        self.authenticate(self.owner)
        self.assertEqual(self.client.get(self.url + 'pdf/').status_code, 404)
        self.issue()
        self.authenticate(self.owner)
        response = self.client.get(self.url + 'pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF-'))
        self.authenticate(self.other)
        self.assertEqual(self.client.get(self.url + 'pdf/').status_code, 404)

    def test_institution_dropdown_contains_only_institutions_with_available_reviewed_programmes(self):
        reviewed = ProgramAccreditation.objects.create(institution=self.other.institution,
            programme_name='Reviewed Business', program_level='degree', duration=6, status='reviewed')
        another = ProgramAccreditation.objects.create(institution=self.other.institution,
            programme_name='Reviewed Computing', program_level='degree', duration=6, status='reviewed')
        ProgramAccreditation.objects.create(institution=self.other.institution,
            programme_name='Unreviewed Programme', program_level='degree', duration=6, status='submitted')
        accounting = ProgramAccreditation.objects.create(institution=self.institution,
            programme_name='Accounting Stage', program_level='degree', duration=6, status='progressed_to_accounting')
        empty_owner = User.objects.create_user('no-programmes', 'empty@example.test', is_active=True)
        Institution.objects.create(user=empty_owner, name='No Programmes', district=self.institution.district)
        self.authenticate(self.head)
        response = self.client.get('/invoices/creation-options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['institutions'], [{'id': self.other.institution.pk, 'name': self.other.institution.name}])
        available = self.client.get('/invoices/available-programmes/', {'institution_id': self.other.institution.pk})
        self.assertEqual({item['id'] for item in available.data}, {reviewed.pk, another.pk})
        self.assertEqual(self.client.post('/invoices/', {'institution_id': self.institution.pk,
            'lines': [{'application': accounting.pk, 'desk_review_fee': '100.00'}]}, format='json').status_code, 400)
        response = self.client.post('/invoices/', {'institution_id': self.other.institution.pk,
            'lines': [{'application': app.pk, 'desk_review_fee': '100.00'} for app in [reviewed, another]]}, format='json')
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(self.client.get('/invoices/creation-options/').data['institutions'], [])

    def test_mixed_paid_and_unpaid_selection_does_not_assign_any_programme(self):
        second = self.create_grouped_invoice()
        self.issue()
        self.authenticate(self.owner)
        self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart')
        self.authenticate(self.accounts)
        self.assertEqual(self.acknowledge().status_code, 200)
        unpaid = ProgramAccreditation.objects.create(institution=self.institution, programme_name='Unpaid Education',
            program_level='degree', duration=6, status='invoice_reconciled', is_paid=True)
        self.head.user_permissions.add(Permission.objects.get(codename='can_assign_assessors'))
        self.head = User.objects.get(pk=self.head.pk)
        self.authenticate(self.head)
        assessor = User.objects.create_user('mixed-assessor', 'mixed@example.test', is_active=True)
        assessor.groups.add(Group.objects.create(name='Programme Assessors'))
        response = self.client.post('/programme-accreditation/assign-assessor/', {
            'userId': assessor.pk, 'applications': [self.application.pk, second.pk, unpaid.pk],
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(response.data['blocked_programmes']), 1)
        self.assertFalse(ProgramAccreditation.objects.filter(assessor=assessor).exists())

    def test_partial_payment_follow_up_preserves_verified_receipt_history(self):
        self.issue()
        self.authenticate(self.owner)
        self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart')
        self.authenticate(self.accounts)
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/', {'verified_amount': '50.00'}, format='json').status_code, 200)
        previous_receipt = self.invoice.verifications.get().payment_receipt.name
        self.authenticate(self.owner)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(payment_reference='TOPUP-456'), format='multipart').status_code, 200)
        self.authenticate(self.accounts)
        self.assertEqual(self.acknowledge().status_code, 200)
        history = list(self.invoice.verifications.all())
        self.assertEqual(history[0].payment_receipt.name, previous_receipt)
        self.assertEqual(history[0].payment_reference, 'BANK-123')
        self.assertEqual(history[1].payment_reference, 'TOPUP-456')
        self.assertNotEqual(history[1].payment_receipt.name, previous_receipt)


@override_settings(ROOT_URLCONF='programmes.test_urls')
class AssessorAssignmentFilterTests(APITestCase):
    def setUp(self):
        self.head = User.objects.create_user('filter-head', 'filter-head@example.test', is_active=True)
        self.head.groups.add(Group.objects.create(name='Head Programme Accreditation'))
        self.reviewer = User.objects.create_user('filter-reviewer', 'filter-reviewer@example.test', is_active=True)
        self.reviewer.groups.add(Group.objects.create(name='Programme Reviewers'))
        district = District.objects.create(name='Assessor Filter District')
        self.owner = User.objects.create_user('filter-institution-owner', 'filter-owner@example.test', is_active=True)
        self.institution = Institution.objects.create(user=self.owner, name='Filter University', district=district)
        other_owner = User.objects.create_user('other-filter-owner', 'other-filter@example.test', is_active=True)
        self.other_institution = Institution.objects.create(user=other_owner, name='Other Filter University', district=district)
        self.computing = self.programme('Computing', self.institution, 'stem', 'computing')
        self.business = self.programme('Business', self.other_institution, 'humanities', 'business')
        self.computing.preliminary_reviewer = self.reviewer
        self.computing.save(update_fields=['preliminary_reviewer'])
        self.client.force_authenticate(self.head)

    def programme(self, name, institution, category, tier, cleared=True):
        app = ProgramAccreditation.objects.create(institution=institution, programme_name=name,
            program_level='bachelor', duration=6, programme_category=category, status='invoice_reconciled', is_paid=True)
        invoice = ProgrammeAssessmentInvoice.objects.create(institution=institution, desk_review_fee=Decimal('100.00'),
            status='reconciled' if cleared else 'paid', cleared=cleared, verified_amount=Decimal('110.00') if cleared else 0)
        DeskReviewInvoiceLine.objects.create(invoice=invoice, application=app, programme_name=name,
            application_number=app.application_number, desk_review_fee=Decimal('100.00'))
        PreliminaryReview.objects.create(application=app, reviewer=self.reviewer, tier_displine=tier)
        return app

    def test_combines_search_institution_category_and_tier_before_pagination(self):
        response = self.client.get('/programme-accreditation/ready-for-assessment/', {
            'search': 'Computing', 'institution': self.institution.pk, 'programme_category': 'stem', 'tier_displine': 'computing',
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.computing.pk)
        self.assertEqual(response.data['results'][0]['tier_displine'], 'computing')
        self.assertEqual(response.data['results'][0]['tier_displine_display'], 'Computing')
        self.assertEqual(self.client.get('/programme-accreditation/ready-for-assessment/', {
            'institution': self.institution.pk, 'tier_displine': 'business',
        }).data['count'], 0)
        self.assertEqual(self.client.get('/programme-accreditation/ready-for-assessment/', {'search': 'unmatched'}).data['count'], 0)

    def test_tier_uses_latest_preliminary_review_without_duplicate_results(self):
        latest = PreliminaryReview.objects.create(application=self.computing, reviewer=self.reviewer, tier_displine='business')
        # Equal timestamps still resolve deterministically to the most recent ID.
        PreliminaryReview.objects.filter(application=self.computing).update(reviewed_at=latest.reviewed_at)
        response = self.client.get('/programme-accreditation/ready-for-assessment/', {'tier_displine': 'business'})
        self.assertEqual(response.data['count'], 2)
        self.assertEqual({row['id'] for row in response.data['results']}, {self.computing.pk, self.business.pk})
        self.assertEqual(self.client.get('/programme-accreditation/ready-for-assessment/', {'tier_displine': 'computing'}).data['count'], 0)

    def test_filter_options_are_scoped_and_filters_do_not_unlock_unpaid_programmes(self):
        self.programme('Unpaid Computing', self.institution, 'stem', 'computing', cleared=False)
        response = self.client.get('/programme-accreditation/ready-for-assessment/', {'tier_displine': 'computing'})
        self.assertEqual(response.data['count'], 1)
        self.client.force_authenticate(self.reviewer)
        response = self.client.get('/programme-accreditation/assessment-application-filter-options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['institutions'], [{'id': self.institution.pk, 'name': self.institution.name}])
        self.assertEqual(response.data['tier_disciplines'], [{'value': value, 'label': label} for value, label in PreliminaryReview.DISPLINE_CHOICE])
        self.assertEqual(self.client.get('/programme-accreditation/ready-for-assessment/', {'institution': self.other_institution.pk}).data['count'], 0)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get('/programme-accreditation/assessment-application-filter-options/').data['institutions'], [])

    def test_invalid_filters_return_errors_and_unclassified_programmes_remain_visible(self):
        for filters in [{'institution': 'invalid'}, {'programme_category': 'invalid'}, {'tier_displine': 'invalid'}]:
            self.assertEqual(self.client.get('/programme-accreditation/ready-for-assessment/', filters).status_code, 400)
        PreliminaryReview.objects.filter(application=self.computing).delete()
        response = self.client.get('/programme-accreditation/ready-for-assessment/')
        row = next(row for row in response.data['results'] if row['id'] == self.computing.pk)
        self.assertIsNone(row['tier_displine'])
        self.assertIsNone(row['tier_displine_display'])


class ProgrammeAssessorWorkloadTests(APITestCase):
    def setUp(self):
        self.busy = User.objects.create_user('busy-assessor', 'busy-assessor@example.test', is_active=True)
        self.idle = User.objects.create_user('idle-assessor', 'idle-assessor@example.test', is_active=True)
        group = Group.objects.create(name='Programme Assessors')
        self.busy.groups.add(group)
        self.idle.groups.add(group)
        owner = User.objects.create_user('workload-assessor-owner', 'assessor-owner@example.test', is_active=True)
        district = District.objects.create(name='Assessor Workload District')
        institution = Institution.objects.create(user=owner, name='Assessor Workload University', district=district)
        self.pending = ProgramAccreditation.objects.create(institution=institution, programme_name='Pending', program_level='bachelor', duration=6, assessor=self.busy)
        completed = ProgramAccreditation.objects.create(institution=institution, programme_name='Completed', program_level='bachelor', duration=6, assessor=self.busy)
        # An assessment by a different assessor must not clear the current workload.
        ProgrammeAssessment.objects.create(application=self.pending, assessor=self.idle)
        ProgrammeAssessment.objects.create(application=completed, assessor=self.busy)

    def workloads(self, user):
        request = APIRequestFactory().get('/programme-assessors/')
        if user:
            force_authenticate(request, user)
        return ProgramAccessorViewset.as_view({'get': 'list'})(request)

    def test_workload_counts_only_applications_without_assigned_assessors_assessment(self):
        response = self.workloads(self.busy)
        self.assertEqual(response.status_code, 200, response.data)
        counts = {item['id']: item['assigned_application_count'] for item in response.data}
        self.assertEqual(counts, {self.busy.pk: 1, self.idle.pk: 0})
        ProgrammeAssessment.objects.create(application=self.pending, assessor=self.busy)
        counts = {item['id']: item['assigned_application_count'] for item in self.workloads(self.busy).data}
        self.assertEqual(counts[self.busy.pk], 0)

    def test_workloads_require_authentication(self):
        self.assertEqual(self.workloads(None).status_code, 401)


@override_settings(ROOT_URLCONF='programmes.test_urls')
class ProgrammeHeadDashboardTests(APITestCase):
    def setUp(self):
        self.head = User.objects.create_user('dashboard-head', 'dashboard-head@example.test', is_active=True)
        self.head.groups.add(Group.objects.create(name='Head Programme Accreditation'))
        self.owner = User.objects.create_user('dashboard-owner', 'dashboard-owner@example.test', is_active=True)
        self.other_owner = User.objects.create_user('dashboard-other', 'dashboard-other@example.test', is_active=True)
        district = District.objects.create(name='Dashboard District')
        self.institution = Institution.objects.create(user=self.owner, name='Alpha University', district=district)
        self.other_institution = Institution.objects.create(user=self.other_owner, name='Beta University', district=district)
        self.computing = ProgramAccreditation.objects.create(institution=self.institution, programme_name='Computing',
            program_level='bachelor', duration=6, programme_category='stem', status='reviewed')
        self.business = ProgramAccreditation.objects.create(institution=self.other_institution, programme_name='Business',
            program_level='bachelor', duration=6, programme_category='humanities', status='invoice_reconciled')
        self.unknown = ProgramAccreditation.objects.create(institution=self.institution, programme_name='Unclassified',
            program_level='diploma', duration=4, programme_category=None, status='submitted')
        for application in [self.computing, self.computing, self.business]:
            PreliminaryReview.objects.create(application=application, reviewer=self.head, tier_displine='computing')
        self.invoice = ProgrammeAssessmentInvoice.objects.create(institution=self.other_institution, desk_review_fee=Decimal('100.00'),
            status='reconciled', cleared=True, verified_amount=Decimal('110.00'))
        DeskReviewInvoiceLine.objects.create(invoice=self.invoice, application=self.business,
            programme_name=self.business.programme_name, application_number=self.business.application_number, desk_review_fee=Decimal('100.00'))
        self.client.force_authenticate(self.head)

    def test_summary_uses_live_counts_without_duplicate_review_records(self):
        response = self.client.get('/head-dashboard/summary/')
        self.assertEqual(response.status_code, 200, response.data)
        totals = response.data['totals']
        for key, value in {'applications': 3, 'institutions': 2, 'reviewed': 2,
                'stem': 1, 'humanities': 1, 'unspecified': 1, 'ready_for_assessment': 1, 'payment_verification': 0}.items():
            self.assertEqual(totals[key], value, key)
        self.assertEqual(response.data['top_institutions'][0], {'id': self.institution.pk,
            'name': 'Alpha University', 'applications': 2, 'reviewed': 1})
        self.assertEqual(next(stage['count'] for stage in response.data['stages'] if stage['value']=='submitted'), 1)

    def test_register_filters_search_sort_and_pagination(self):
        response = self.client.get('/head-dashboard/', {'search': 'Computing', 'institution': self.institution.pk,
            'programme_category': 'stem', 'status': 'reviewed'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.computing.pk)
        response = self.client.get('/head-dashboard/', {'programme_category': 'unspecified'})
        self.assertEqual([row['id'] for row in response.data['results']], [self.unknown.pk])
        response = self.client.get('/head-dashboard/', {'ordering': 'programme_name', 'page_size': 1})
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(response.data['results'][0]['id'], self.business.pk)
        self.assertIsNotNone(response.data['next'])
        response = self.client.get('/head-dashboard/', {'ordering': 'programme_name', 'page_size': 1, 'page': 2})
        self.assertEqual(response.data['results'][0]['id'], self.computing.pk)

    def test_payment_labels_use_verified_invoice_amounts(self):
        rows = {row['id']: row for row in self.client.get('/head-dashboard/').data['results']}
        self.assertEqual(rows[self.business.pk]['payment_status'], 'Fully verified')
        self.assertEqual(rows[self.computing.pk]['payment_status'], 'Not invoiced')
        partial = ProgrammeAssessmentInvoice.objects.create(institution=self.institution, desk_review_fee=Decimal('100.00'),
            status='paid', cleared=False, verified_amount=Decimal('50.00'))
        DeskReviewInvoiceLine.objects.create(invoice=partial, application=self.computing,
            programme_name=self.computing.programme_name, application_number=self.computing.application_number, desk_review_fee=Decimal('100.00'))
        rows = {row['id']: row for row in self.client.get('/head-dashboard/').data['results']}
        self.assertEqual(rows[self.computing.pk]['payment_status'], 'Partially verified')
        totals = self.client.get('/head-dashboard/summary/').data['totals']
        self.assertEqual(totals['payment_verification'], 1)
        self.assertEqual(totals['ready_for_assessment'], 1)
        partial.status = 'cancelled'
        partial.save()
        rows = {row['id']: row for row in self.client.get('/head-dashboard/').data['results']}
        self.assertEqual(rows[self.computing.pk]['payment_status'], 'Not invoiced')

    def test_dashboard_is_read_only_and_restricted_to_programme_heads(self):
        self.assertEqual(self.client.post('/head-dashboard/', {}).status_code, 405)
        finance = User.objects.create_user('dashboard-finance', 'dashboard-finance@example.test', is_active=True)
        finance.groups.add(Group.objects.create(name='Finance Officer'))
        for user in [self.owner, finance, None]:
            client = self.client_class()
            if user:
                client.force_authenticate(user)
            for path in ['/head-dashboard/', '/head-dashboard/summary/', '/head-dashboard/filter-options/']:
                self.assertEqual(client.get(path).status_code, 403 if user else 401)

    def test_filter_options_and_invalid_values(self):
        response = self.client.get('/head-dashboard/filter-options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['name'] for item in response.data['institutions']], ['Alpha University', 'Beta University'])
        self.assertEqual(len(response.data['statuses']), len(ProgramAccreditation.STATUS))
        for query in [{'institution': 'invalid'}, {'institution': '-1'}, {'programme_category': 'invalid'}, {'status': 'invalid'}]:
            self.assertEqual(self.client.get('/head-dashboard/', query).status_code, 400)

    def test_empty_dashboard_returns_zero_counts(self):
        ProgrammeAssessmentInvoice.objects.all().delete()
        ProgramAccreditation.objects.all().delete()
        response = self.client.get('/head-dashboard/summary/')
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['totals']['applications'], 0)
        self.assertEqual(response.data['totals']['institutions'], 0)
        self.assertIsNone(response.data['totals']['latest_submission'])
        self.assertEqual(response.data['top_institutions'], [])
