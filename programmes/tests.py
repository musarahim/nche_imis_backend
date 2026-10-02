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
from rest_framework.test import APITestCase

from .models import Program, ProgramAccreditation, ProgrammeAssessmentInvoice, ProgrammeInvoice
from .views import ProgrammeAccreditationViewset


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
            institution=self.institution, program_name='Computing', program_level='bachelor',
            accreditation_date=today - timedelta(days=365), expiry_date=today + timedelta(days=365), status='active',
        )
        self.url = '/programme-accreditation/'

    def payload(self, **overrides):
        return {
            'application_type': 'renewal', 'program_to_renew': self.programme.pk,
            'program_name': 'Computing', 'program_level': 'bachelor',
            'duration': 6, 'duration_type': 'semester', 'number_of_years': 3,
            'campus': 'Main', 'programme_category': 'stem', **overrides,
        }

    def submit(self):
        self.client.force_authenticate(self.owner)
        with patch('programmes.views.render_to_string', return_value='Submitted'):
            return self.client.post(self.url, self.payload())

    def test_renewal_submission_and_early_approval_preserve_history(self):
        response = self.submit()
        self.assertEqual(response.status_code, 201, response.data)
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
        self.assertEqual(self.client.post(self.url, self.payload(program_name='Different')).status_code, 400)
        self.assertEqual(self.client.post(self.url, self.payload(application_type='new')).status_code, 400)
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
        self.assertEqual(self.client.patch(f'{self.url}{application_id}/', {'status': 'approved'}).status_code, 400)
        self.assertEqual(self.client.post(f'{self.url}{application_id}/management-decision/', {'decision': 'approved'}).status_code, 403)
        self.assertEqual(self.client.post(f'/institution-programmes/{self.programme.pk}/', {'status': 'active'}).status_code, 405)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f'{self.url}{application_id}/').status_code, 404)

    def test_renewal_options_are_scoped_to_institution(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get('/institution-programmes/renewal-options/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [self.programme.pk])
        self.submit()
        self.assertEqual(self.client.get('/institution-programmes/renewal-options/').data, [])
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get('/institution-programmes/renewal-options/').data, [])

    def test_new_application_approval_creates_programme(self):
        self.client.force_authenticate(self.owner)
        payload = self.payload(application_type='new', program_name='Engineering')
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
        programme = Program.objects.get(institution=self.institution, program_name='Engineering')
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
            institution=self.institution, program_name='Computing', program_level='degree', duration=6, status='reviewed',
        )
        self.invoice = ProgrammeAssessmentInvoice.objects.create(application=self.application, desk_review_fee=Decimal('100.00'))
        self.url = f'/invoices/{self.invoice.pk}/'

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def payment(self, **overrides):
        return {
            'payment_reference': ' BANK-123 ',
            'payment_date': str(timezone.localdate()),
            'payment_receipt': SimpleUploadedFile('receipt.pdf', b'%PDF-1.4\nTest receipt', content_type='application/pdf'),
            **overrides,
        }

    def issue(self):
        self.authenticate(self.accounts)
        response = self.client.post(self.url + 'send-invoice/')
        self.assertEqual(response.status_code, 200, response.data)

    def test_full_workflow_recalculates_notifies_and_acknowledges(self):
        self.authenticate(self.accounts)
        response = self.client.patch(self.url, {'desk_review_fee': '250.00'})
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
        response = self.client.post(self.url + 'reconcile-invoice/')
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
        assessor = User.objects.create_user('assessor', 'assessor@example.test', is_active=True)
        assessor.groups.add(Group.objects.create(name='Programme Assessors'))
        self.assertEqual(self.client.post('/programme-accreditation/assign-assessor/', {
            'userId': assessor.pk, 'applications': [self.application.pk],
        }, format='json').status_code, 400)
        self.authenticate(self.accounts)
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/').status_code, 200)
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

    def test_cleared_programme_invoice_becomes_ready_for_assessment(self):
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
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.application.pk)
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
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/').status_code, 403)
        self.assertEqual(self.client.delete(self.url).status_code, 405)
        self.assertEqual(self.client.post('/invoices/', {'application': self.application.pk, 'desk_review_fee': '1.00'}).status_code, 403)

    def test_anonymous_cannot_access(self):
        self.assertEqual(self.client.get('/invoices/').status_code, 401)
        self.assertEqual(self.client.post(self.url + 'send-invoice/').status_code, 401)

    def test_head_can_create_but_cannot_issue_or_edit(self):
        self.invoice.delete()
        self.authenticate(self.head)
        response = self.client.post('/invoices/', {'application': self.application.pk, 'desk_review_fee': '100.00'})
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data['status'], 'Draft')
        self.assertFalse(response.data['can_manage'])
        url = f'/invoices/{response.data["id"]}/'
        self.assertEqual(self.client.post(url + 'send-invoice/').status_code, 403)
        self.assertEqual(self.client.patch(url, {'desk_review_fee': '200.00'}).status_code, 403)
        self.assertEqual(self.client.post('/invoices/', {'application': self.application.pk, 'desk_review_fee': '100.00'}).status_code, 400)

    def test_accounts_permission_also_allows_management(self):
        self.head.user_permissions.add(Permission.objects.get(codename='can_manage_invoices'))
        self.authenticate(self.head)
        response = self.client.patch(self.url, {'desk_review_fee': '200.00'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['can_manage'])

    def test_cannot_bypass_actions_or_change_application(self):
        self.authenticate(self.accounts)
        for data in [{'status': 'reconciled'}, {'cleared': True}, {'grand_total': '1.00'}, {'application': self.application.pk}, {'payment_reference': 'fake'}]:
            with self.subTest(data=data):
                self.assertEqual(self.client.patch(self.url, data).status_code, 400)

    def test_invalid_fees_rejected(self):
        self.authenticate(self.accounts)
        for fee in ['0', '-1', 'NaN', '90909090.91', '12.345']:
            with self.subTest(fee=fee):
                self.assertEqual(self.client.patch(self.url, {'desk_review_fee': fee}).status_code, 400)

    def test_issued_invoice_locked_and_transitions_cannot_repeat(self):
        self.issue()
        self.assertEqual(self.client.patch(self.url, {'desk_review_fee': '200.00'}).status_code, 400)
        self.assertEqual(self.client.post(self.url + 'send-invoice/').status_code, 400)
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/').status_code, 400)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 403)
        self.authenticate(self.owner)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 200)
        self.assertEqual(self.client.post(self.url + 'add-payment-details/', self.payment(), format='multipart').status_code, 400)
        self.authenticate(self.accounts)
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/').status_code, 200)
        self.assertEqual(self.client.post(self.url + 'reconcile-invoice/').status_code, 400)

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
        self.authenticate(self.accounts)
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
