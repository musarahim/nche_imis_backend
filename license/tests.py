import json
from tempfile import TemporaryDirectory

from accounts.models import User
from common.models import District, Nationality
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from institutions.models import Institution
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from .models import InterimPromoters, IntrimAuthority, IntrimAuthorityDocument, UniversityProvisionalLicense, UniversityProvisionalLicenseDocument, UniversityProvisionalLicenseVehicle
from .views import IntrimAuthorityViewset, UniversityProvisionalLicenseViewset
from .serializers import UniversityProvisionalLicenseSerializer


class ProvisionalObjectiveTests(SimpleTestCase):
    def test_accepts_five_objectives_and_preserves_multiline_entries(self):
        rows = ['First line\nSecond line', 'Two', 'Three', 'Four', ' Five ']
        serializer = UniversityProvisionalLicenseSerializer(data={'specific_objectives': json.dumps(rows)}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(json.loads(serializer.validated_data['specific_objectives']), [item.strip() for item in rows])

    def test_accepts_legacy_text_and_partial_updates_without_objectives(self):
        serializer = UniversityProvisionalLicenseSerializer(data={'specific_objectives': ' First \n\n Second '}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(json.loads(serializer.validated_data['specific_objectives']), ['First', 'Second'])
        serializer = UniversityProvisionalLicenseSerializer(data={'vision': 'Updated vision'}, partial=True)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn('specific_objectives', serializer.validated_data)

    def test_rejects_more_than_five_empty_or_invalid_objectives(self):
        for value in [json.dumps(['Objective'] * 6), 'One\nTwo\nThree\nFour\nFive\nSix', '[]', '[" "]', '[123]', '{}', '', None]:
            with self.subTest(value=value):
                serializer = UniversityProvisionalLicenseSerializer(data={'specific_objectives': value}, partial=True)
                self.assertFalse(serializer.is_valid())
                self.assertIn('specific_objectives', serializer.errors)


class ProvisionalVehicleValidationTests(SimpleTestCase):
    def test_accepts_json_and_multipart_vehicle_lists(self):
        rows = [{'make': ' Toyota ', 'registration_number': ' uba 123a '}]
        for payload in [rows, json.dumps(rows)]:
            serializer = UniversityProvisionalLicenseSerializer(data={'vehicles': payload}, partial=True)
            self.assertTrue(serializer.is_valid(), serializer.errors)
            self.assertEqual(serializer._prepared_vehicles[0][1], {'make': 'Toyota', 'registration_number': 'UBA 123A'})

    def test_rejects_invalid_and_duplicate_registrations(self):
        for payload in ['invalid json', '{}', None, [None], [{'make': '', 'registration_number': ''}],
                        [{'make': 'Toyota', 'registration_number': 'UBA 123A'}, {'make': 'Isuzu', 'registration_number': 'uba123a'}]]:
            with self.subTest(payload=payload):
                serializer = UniversityProvisionalLicenseSerializer(data={'vehicles': payload}, partial=True)
                self.assertFalse(serializer.is_valid())
                self.assertIn('vehicles', serializer.errors)


class InterimPromoterUploadTests(APITestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        media = override_settings(MEDIA_ROOT=directory.name, MEDIA_URL='/media/')
        media.enable()
        self.addCleanup(media.disable)
        self.user = User.objects.create_user('promoter-owner', 'owner@example.test', is_active=True)
        district = District.objects.create(name='Promoter District')
        institution = Institution.objects.create(user=self.user, name='Promoter University', district=district)
        self.application = IntrimAuthority.objects.create(institution=institution, has_title_deed=False)
        self.nationality = Nationality.objects.create(name='Ugandan')

    def post_promoters(self, promoters, upload=None, multipart=True):
        data = {'promoters': json.dumps(promoters) if multipart else promoters}
        if upload is not None:
            data['promoter_document_0'] = upload
        request = APIRequestFactory().post('/promoters/', data, format='multipart' if multipart else 'json')
        force_authenticate(request, self.user)
        return IntrimAuthorityViewset.as_view({'post': 'promoters'})(request, pk=self.application.pk)

    def promoter(self, **overrides):
        return {'name': 'Jane', 'phone': '+256772123456', 'email': '', 'nationality': self.nationality.pk, **overrides}

    def document(self, name='passport.pdf', content=b'%PDF-1.4\nPassport'):
        return SimpleUploadedFile(name, content, content_type='application/pdf')

    def test_uploads_nationality_and_document(self):
        response = self.post_promoters([self.promoter()], self.document())
        self.assertEqual(response.status_code, 200, response.data)
        saved = InterimPromoters.objects.get(application=self.application)
        self.assertEqual(saved.nationality, self.nationality)
        with saved.id_passport_document.open('rb') as uploaded:
            self.assertEqual(uploaded.read(), b'%PDF-1.4\nPassport')
        self.assertEqual(response.data[0]['nationality_name'], 'Ugandan')
        self.assertTrue(response.data[0]['id_passport_document'].startswith('http://testserver/media/'))

    def test_edit_preserves_document_and_id_without_reupload(self):
        created = self.post_promoters([self.promoter()], self.document())
        promoter_id = created.data[0]['id']
        previous_document = InterimPromoters.objects.get(pk=promoter_id).id_passport_document.name
        response = self.post_promoters([self.promoter(id=promoter_id, name='Updated Jane')])
        self.assertEqual(response.status_code, 200, response.data)
        saved = InterimPromoters.objects.get(pk=promoter_id)
        self.assertEqual(saved.name, 'Updated Jane')
        self.assertEqual(saved.id_passport_document.name, previous_document)

    def test_invalid_upload_or_nationality_does_not_replace_saved_promoters(self):
        saved = InterimPromoters.objects.create(application=self.application, name='Original', phone='+256772123456')
        for upload in [self.document('passport.exe'), self.document(content=b'x' * (2 * 1024 * 1024 + 1))]:
            response = self.post_promoters([self.promoter()], upload)
            self.assertEqual(response.status_code, 400, response.data)
            self.assertTrue(InterimPromoters.objects.filter(pk=saved.pk, name='Original').exists())
        response = self.post_promoters([self.promoter(nationality=999999)])
        self.assertEqual(response.status_code, 400)
        self.assertTrue(InterimPromoters.objects.filter(pk=saved.pk).exists())

    def test_document_retention_cannot_use_promoter_from_another_application(self):
        other_application = IntrimAuthority.objects.create(institution=self.application.institution, has_title_deed=False)
        other = InterimPromoters.objects.create(application=other_application, name='Other', phone='+256772123456')
        response = self.post_promoters([self.promoter(id=other.pk)])
        self.assertEqual(response.status_code, 400)
        self.assertFalse(InterimPromoters.objects.filter(application=self.application).exists())

    def test_existing_json_clients_can_still_save_promoters(self):
        response = self.post_promoters([{'name': 'Legacy', 'phone': '+256772123456'}], multipart=False)
        self.assertEqual(response.status_code, 200, response.data)


class InterimSupportingDocumentTests(APITestCase):
    application_model = IntrimAuthority
    document_model = IntrimAuthorityDocument
    viewset = IntrimAuthorityViewset
    application_defaults = {'has_title_deed': False}
    document_parent_field = 'intrim_authority'

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        media = override_settings(MEDIA_ROOT=directory.name, MEDIA_URL='/media/')
        media.enable()
        self.addCleanup(media.disable)
        self.user = User.objects.create_user('document-owner', 'documents@example.test', is_active=True)
        district = District.objects.create(name='Document District')
        institution = Institution.objects.create(user=self.user, name='Document University', district=district)
        self.application = self.application_model.objects.create(institution=institution, **self.application_defaults)

    def patch_documents(self, rows=None, uploads=None, extra=None):
        data = dict(extra or {})
        if rows is not None:
            data['supporting_documents'] = json.dumps(rows)
        data.update(uploads or {})
        request = APIRequestFactory().patch('/interim-authority/', data, format='multipart')
        force_authenticate(request, self.user)
        return self.viewset.as_view({'patch': 'partial_update'})(request, pk=self.application.pk)

    def upload(self, name='support.pdf', content=b'%PDF-1.4\nSupport'):
        return SimpleUploadedFile(name, content, content_type='application/pdf')

    def test_uploads_up_to_five_documents_and_returns_links(self):
        rows = [{'title': f'Document {i}'} for i in range(5)]
        uploads = {f'supporting_document_{i}': self.upload(name=f'support-{i}.pdf') for i in range(5)}
        response = self.patch_documents(rows, uploads)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(self.application.documents.count(), 5)
        self.assertEqual(len(response.data['supporting_documents']), 5)
        self.assertTrue(response.data['supporting_documents'][0]['document'].startswith('http://testserver/media/'))

    def test_retain_rename_remove_and_replace_existing_documents(self):
        response = self.patch_documents([{'title': 'First'}, {'title': 'Second'}], {
            'supporting_document_0': self.upload('first.pdf'), 'supporting_document_1': self.upload('second.pdf'),
        })
        first, second = response.data['supporting_documents']
        response = self.patch_documents([{'id': second['id'], 'title': 'Renamed'}])
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(self.application.documents.filter(pk=first['id']).exists())
        self.assertEqual(response.data['supporting_documents'][0]['document'], second['document'])
        response = self.patch_documents([{'id': second['id'], 'title': 'Replaced'}], {
            'supporting_document_0': self.upload('replacement.pdf', b'%PDF-1.4\nReplacement'),
        })
        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn('replacement', response.data['supporting_documents'][0]['document'])

    def test_omitting_documents_retains_them_and_empty_list_removes_them(self):
        self.patch_documents([{'title': 'Saved'}], {'supporting_document_0': self.upload()})
        self.assertEqual(self.patch_documents(extra={'vision': 'New vision'}).status_code, 200)
        self.assertEqual(self.application.documents.count(), 1)
        self.assertEqual(self.patch_documents([]).status_code, 200)
        self.assertEqual(self.application.documents.count(), 0)

    def test_limit_and_invalid_uploads_do_not_change_application(self):
        original = self.patch_documents([{'title': 'Saved'}], {'supporting_document_0': self.upload()})
        for rows, uploads in [
            ([{'title': 'Extra'}] * 6, {}),
            ([{'title': 'Missing upload'}], {}),
            ([{'title': 'Wrong type'}], {'supporting_document_0': self.upload('support.exe')}),
            ([{'title': 'Too large'}], {'supporting_document_0': self.upload(content=b'x' * (2 * 1024 * 1024 + 1))}),
        ]:
            response = self.patch_documents(rows, uploads, {'vision': 'Must not be saved'})
            self.assertEqual(response.status_code, 400, response.data)
            self.application.refresh_from_db()
            self.assertNotEqual(self.application.vision, 'Must not be saved')
            self.assertTrue(self.application.documents.filter(pk=original.data['supporting_documents'][0]['id']).exists())

    def test_cannot_retain_another_applications_document(self):
        other = self.application_model.objects.create(institution=self.application.institution, **self.application_defaults)
        document = self.document_model.objects.create(**{self.document_parent_field: other}, title='Other', document=self.upload())
        response = self.patch_documents([{'id': document.pk, 'title': 'Other'}])
        self.assertEqual(response.status_code, 400, response.data)
        self.assertEqual(self.application.documents.count(), 0)


class ProvisionalSupportingDocumentTests(InterimSupportingDocumentTests):
    application_model = UniversityProvisionalLicense
    document_model = UniversityProvisionalLicenseDocument
    viewset = UniversityProvisionalLicenseViewset
    application_defaults = {'amount_of_land': 20, 'land_in_use': 10, 'year_obtained': '2026'}
    document_parent_field = 'university_provisional_license'

    def test_objectives_persist_and_survive_document_updates(self):
        objectives = ['First objective\nWith details', 'Second objective']
        response = self.patch_documents(extra={'specific_objectives': json.dumps(objectives)})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(json.loads(response.data['specific_objectives']), objectives)
        self.assertEqual(list(self.application.university_provisional_objective_items.values_list('objective', flat=True)), objectives)
        response = self.patch_documents([{'title': 'Support'}], {'supporting_document_0': self.upload()})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(json.loads(response.data['specific_objectives']), objectives)


class ProvisionalVehicleTests(APITestCase):
    application_model = UniversityProvisionalLicense
    application_defaults = ProvisionalSupportingDocumentTests.application_defaults
    viewset = UniversityProvisionalLicenseViewset
    setUp = InterimSupportingDocumentTests.setUp
    patch_application = InterimSupportingDocumentTests.patch_documents

    def patch_vehicles(self, rows, **extra):
        return self.patch_application(extra={'vehicles': json.dumps(rows), **extra})

    def test_add_edit_remove_and_derived_count(self):
        response = self.patch_vehicles([
            {'make': 'Toyota', 'registration_number': 'uba 123a'},
            {'make': 'Isuzu', 'registration_number': 'UBB 456B'},
        ], number_of_vehicles=99)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['number_of_vehicles'], 2)
        self.application.refresh_from_db()
        self.assertEqual(self.application.number_of_vehicles, 2)
        first, second = response.data['vehicles']
        response = self.patch_vehicles([{**second, 'make': 'Updated Isuzu'}])
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(self.application.vehicles.filter(pk=first['id']).exists())
        self.assertEqual(response.data['vehicles'][0]['id'], second['id'])
        self.assertEqual(response.data['number_of_vehicles'], 1)
        self.assertEqual(response.data['vehicle_registration'], 'Updated Isuzu - UBB 456B')
        self.assertEqual(self.patch_vehicles([]).data['number_of_vehicles'], 0)
        self.application.refresh_from_db()
        self.assertEqual(self.application.vehicles.count(), 0)
        self.assertEqual(self.application.vehicle_registration, '')

    def test_omitted_vehicles_preserve_records_and_legacy_details(self):
        self.application.number_of_vehicles = 3
        self.application.vehicle_registration = 'Legacy details'
        self.application.save()
        response = self.patch_application(extra={'vision': 'Updated vision'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['number_of_vehicles'], 3)
        self.assertEqual(response.data['vehicle_registration'], 'Legacy details')
        self.patch_vehicles([{'make': 'Toyota', 'registration_number': 'UBA 123A'}])
        response = self.patch_application(extra={'number_of_vehicles': 99, 'vehicle_registration': 'Wrong summary'})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['number_of_vehicles'], 1)
        self.application.refresh_from_db()
        self.assertEqual(self.application.number_of_vehicles, 1)
        self.assertEqual(self.application.vehicles.count(), 1)

    def test_invalid_or_foreign_vehicle_ids_leave_application_unchanged(self):
        self.patch_vehicles([{'make': 'Toyota', 'registration_number': 'UBA 123A'}])
        other = UniversityProvisionalLicense.objects.create(institution=self.application.institution, **self.application_defaults)
        foreign = UniversityProvisionalLicenseVehicle.objects.create(university_provisional_license=other, make='Isuzu', registration_number='UBB 456B')
        for rows in [[{'id': foreign.pk, 'make': 'Isuzu', 'registration_number': 'UBB 456B'}],
                     [{'make': 'Toyota', 'registration_number': 'UBA 123A'}, {'make': 'Isuzu', 'registration_number': 'uba123a'}]]:
            response = self.patch_vehicles(rows, vision='Must not save')
            self.assertEqual(response.status_code, 400, response.data)
            self.application.refresh_from_db()
            self.assertNotEqual(self.application.vision, 'Must not save')
            self.assertEqual(self.application.vehicles.count(), 1)
