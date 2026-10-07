from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .models import District, Region
from .views import DistrictViewSet


class DistrictRegionFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.central = Region.objects.create(name='Central', code='CENTRAL')
        cls.eastern = Region.objects.create(name='Eastern', code='EASTERN')
        cls.kampala = District.objects.create(name='Kampala', region=cls.central)
        District.objects.create(name='Jinja', region=cls.eastern)
        District.objects.create(name='Unassigned', region=None)

    def get_districts(self, params=None):
        request = APIRequestFactory().get('/districts/', params or {})
        return DistrictViewSet.as_view({'get': 'list'})(request)

    def test_only_districts_in_selected_region_are_returned(self):
        response = self.get_districts({'region_id': self.central.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data], [self.kampala.pk])

    def test_without_region_returns_all_districts_for_initial_value_lookup(self):
        response = self.get_districts()
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['name'] for item in response.data], ['Jinja', 'Kampala', 'Unassigned'])

    def test_invalid_region_returns_bad_request(self):
        for region_id in ['', 'invalid', '0', '-1']:
            with self.subTest(region_id=region_id):
                self.assertEqual(self.get_districts({'region_id': region_id}).status_code, 400)
