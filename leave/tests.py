from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import override_settings
from hr.models import Employee
from rest_framework.test import APITestCase

from .models import LeaveApplication, LeaveType


@override_settings(
    ROOT_URLCONF='leave.urls',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class LeaveScheduleTests(APITestCase):
    schedule_url = '/leave-applications/schedule/'
    schedules_url = '/leave-applications/schedules/'

    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            'leave-owner', 'owner@example.test', is_active=True,
            first_name='Leave', last_name='Owner',
        )
        cls.other_user = user_model.objects.create_user(
            'leave-other', 'other@example.test', is_active=True,
        )
        cls.employee = Employee.objects.create(system_account=cls.user)
        cls.other_employee = Employee.objects.create(system_account=cls.other_user)
        cls.leave_type = LeaveType.objects.create(code='ANNUAL', name='Annual', max_days=30)

    def setUp(self):
        self.client.force_authenticate(self.user)

    def payload(self, **overrides):
        return {
            'leave_type': self.leave_type.pk, 'leave_days': 2,
            'start_date': '2026-09-29', 'end_date': '2026-09-30', **overrides,
        }

    def make_schedule(self, **overrides):
        fields = self.payload()
        fields.update(leave_type=self.leave_type, employee=self.employee, status='planned')
        fields.update(overrides)
        return LeaveApplication.objects.create(**fields)

    def test_created_schedule_is_available_to_calendar(self):
        response = self.client.post(self.schedule_url, self.payload(), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        schedule = LeaveApplication.objects.get(pk=response.data['id'])
        self.assertEqual(schedule.employee, self.employee)
        self.assertEqual(schedule.status, 'planned')
        response = self.client.get(self.schedules_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)
        event = response.data[0]
        for key, value in {
            'id': schedule.pk, 'leave_type': 'Annual', 'leave_days': 2,
            'start_date': '2026-09-29', 'end_date': '2026-09-30',
        }.items():
            self.assertEqual(event[key], value)

    def test_creation_uses_authenticated_employee_and_forces_planned_status(self):
        response = self.client.post(self.schedule_url, self.payload(
            employee=self.other_employee.pk, status='hr_approved',
        ), format='json')
        self.assertEqual(response.status_code, 201, response.data)
        schedule = LeaveApplication.objects.get(pk=response.data['id'])
        self.assertEqual(schedule.employee, self.employee)
        self.assertEqual(schedule.status, 'planned')

    def test_calendar_only_lists_current_employees_planned_leaves(self):
        own = self.make_schedule()
        self.make_schedule(employee=self.other_employee)
        for leave_status, _label in LeaveApplication.STATUS_CHOICES:
            if leave_status != 'planned':
                self.make_schedule(status=leave_status)
        response = self.client.get(self.schedules_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [own.pk])

    def test_calendar_returns_empty_array_when_no_schedules_exist(self):
        response = self.client.get(self.schedules_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_calendar_returns_all_schedules_without_pagination(self):
        ids = {self.make_schedule().pk for _ in range(12)}
        response = self.client.get(self.schedules_url)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual({item['id'] for item in response.data}, ids)

    def test_invalid_schedule_is_rejected_without_creating_a_record(self):
        for invalid in (
            {'leave_type': 999999}, {'start_date': 'invalid-date'},
            {'end_date': None}, {'leave_days': -1},
        ):
            with self.subTest(invalid=invalid):
                response = self.client.post(self.schedule_url, self.payload(**invalid), format='json')
                self.assertEqual(response.status_code, 400, response.data)
                self.assertIn(next(iter(invalid)), response.data)
                self.assertEqual(LeaveApplication.objects.count(), 0)

    def test_missing_required_field_is_rejected(self):
        payload = self.payload()
        del payload['leave_type']
        response = self.client.post(self.schedule_url, payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('leave_type', response.data)
        self.assertEqual(LeaveApplication.objects.count(), 0)

    def test_scheduling_and_listing_require_authentication(self):
        self.client.force_authenticate(user=None)
        for method, url, data in (
            ('get', self.schedules_url, None),
            ('post', self.schedule_url, self.payload()),
        ):
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, data, format='json')
                self.assertIn(response.status_code, (401, 403))
        self.assertEqual(LeaveApplication.objects.count(), 0)

    def test_submitting_schedule_removes_it_from_calendar(self):
        schedule = self.make_schedule()
        # Isolate template rendering; retain the real in-memory email backend.
        with patch('leave.views.render_to_string', return_value='Leave notification'):
            response = self.client.patch(f'/leave-applications/{schedule.pk}/', {
                'status': 'submitted', 'delegated_to': self.other_employee.pk,
                'reason': 'Annual leave', 'return_date': '2026-10-01',
            }, format='json')
        self.assertEqual(response.status_code, 200, response.data)
        schedule.refresh_from_db()
        self.assertEqual(schedule.status, 'submitted')
        self.assertEqual(schedule.delegated_to, self.other_employee)
        response = self.client.get(self.schedules_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        self.assertTrue(LeaveApplication.objects.filter(pk=schedule.pk).exists())

    def test_cannot_update_another_employees_schedule(self):
        schedule = self.make_schedule(employee=self.other_employee)
        response = self.client.patch(f'/leave-applications/{schedule.pk}/', {
            'start_date': '2026-10-01',
        }, format='json')
        self.assertEqual(response.status_code, 404)
        schedule.refresh_from_db()
        self.assertEqual(schedule.start_date.isoformat(), '2026-09-29')
