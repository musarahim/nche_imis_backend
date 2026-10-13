import json
from django.db import transaction

from payments.models import ApplicationPRNS
from rest_framework import serializers

from .models import (CertificationAndClassification, CharterApplication,
                     InterimDiscussion, InterimPromoters, IntrimAuthority,
                     IntrimAuthorityObjective, IntrimAuthorityDocument, OTIProvisional,
                     OTIProvisionalAward, UniversityProvisionalLicense, UniversityProvisionalLicenseDocument,
                     UniversityProvisionalObjective, UniversityProvisionalLicenseVehicle)


class CertificationAndClassificationSerializer(serializers.ModelSerializer):
    '''Serializer for CertificationAndClassification model.'''
    class Meta:
        '''Meta class for CertificationAndClassification Serializer'''
        model = CertificationAndClassification
        fields = "__all__"
        read_only_fields = ['id']

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        response['provisional_license_value'] = instance.provisional_license.code if instance.provisional_license else None
        response['prn'] = ApplicationPRNS.objects.filter(referenceNo=instance.application_code).last().prn if ApplicationPRNS.objects.filter(referenceNo=instance.application_code).exists() else None
        response['status'] = instance.get_status_display()
        return response


class InterimPromotersSerializer(serializers.ModelSerializer):
    " serializer for Interim Authority Promoters" 
    nationality_name = serializers.CharField(source='nationality.name', read_only=True, default=None)

    def validate_id_passport_document(self, value):
        if not value:
            return value
        from pathlib import Path
        if Path(value.name).suffix.lower() not in {'.pdf', '.jpg', '.jpeg', '.png'}:
            raise serializers.ValidationError('Upload a PDF, JPG or PNG document.')
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('The document must be no larger than 2 MB.')
        return value

    class Meta:
        model = InterimPromoters
        fields = "__all__"
        read_only_fields = ['id', 'application', 'created', 'modified', 'deleted_at']


class IntrimAuthorityObjectiveSerializer(serializers.ModelSerializer):
    """Serializer for single interim authority objective rows."""

    class Meta:
        model = IntrimAuthorityObjective
        fields = ["id", "objective", "order"]
        read_only_fields = ["id"]

class InterimSupportingDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntrimAuthorityDocument
        fields = ['id', 'title', 'document']
        read_only_fields = ['id']

    def validate_document(self, value):
        from pathlib import Path
        if Path(value.name).suffix.lower() != '.pdf':
            raise serializers.ValidationError('Upload a PDF document.')
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('The document must be no larger than 2 MB.')
        return value


class SupportingDocumentMixin:
    def _prepare_supporting_documents(self, data):
        self._supporting_documents = None
        if 'supporting_documents' in data:
            rows = data.get('supporting_documents')
            if isinstance(rows, str):
                try:
                    rows = json.loads(rows)
                except (ValueError, TypeError):
                    raise serializers.ValidationError({'supporting_documents': 'Provide a valid document list.'})
            if not isinstance(rows, list) or len(rows) > 5:
                raise serializers.ValidationError({'supporting_documents': 'You can upload at most 5 supporting documents.'})
            existing = {str(row.pk): row for row in self.instance.documents.all()} if self.instance else {}
            prepared = []
            seen = set()
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    raise serializers.ValidationError({'supporting_documents': 'Each document must include a title and file.'})
                row_id = row.get('id')
                previous = existing.get(str(row_id)) if row_id is not None else None
                if row_id is not None and (previous is None or previous.pk in seen):
                    raise serializers.ValidationError({'supporting_documents': 'An existing document is invalid or repeated.'})
                if previous:
                    seen.add(previous.pk)
                upload = data.get(f'supporting_document_{index}')
                if not upload and not (previous and previous.document):
                    raise serializers.ValidationError({'supporting_documents': f'Upload a file for document {index + 1}.'})
                fields = {'title': row.get('title', '')}
                if upload:
                    fields['document'] = upload
                document_serializer = self.fields['supporting_documents'].child.__class__(instance=previous, data=fields, partial=bool(previous))
                if not document_serializer.is_valid():
                    raise serializers.ValidationError({'supporting_documents': {str(index): document_serializer.errors}})
                prepared.append((previous, document_serializer.validated_data))
            self._supporting_documents = prepared

    def _sync_supporting_documents(self, instance):
        if self._supporting_documents is None:
            return
        retained_ids = []
        for previous, fields in self._supporting_documents:
            if previous:
                for field, value in fields.items():
                    setattr(previous, field, value)
                previous.save()
                retained_ids.append(previous.pk)
            else:
                retained_ids.append(instance.documents.create(**fields).pk)
        instance.documents.exclude(pk__in=retained_ids).delete()


class IntrimAuthoritySerializer(SupportingDocumentMixin, serializers.ModelSerializer):
    '''Serializer for IntrimAuthority model.'''
    promoters_details = InterimPromotersSerializer(source='interimpromoters_set', many=True, read_only=True)
    objective_items = IntrimAuthorityObjectiveSerializer(many=True, read_only=True)
    supporting_documents = InterimSupportingDocumentSerializer(source='documents', many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._provided_objectives = False
        self._normalized_objectives = []
        self._supporting_documents = None

    class Meta:
        '''Meta class for IntrimAuthority Serializer'''
        model = IntrimAuthority
        fields = "__all__"
        read_only_fields = ['id']

    def _normalize_objectives(self, raw_value):
        """Accept objectives as text/list input and return a cleaned objective list."""
        if raw_value is None:
            return []

        if isinstance(raw_value, str):
            stripped = raw_value.strip()
            if stripped == "":
                return []

            parsed = None
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError:
                parsed = None

            if isinstance(parsed, list):
                raw_items = parsed
            else:
                raw_items = stripped.splitlines()
        elif isinstance(raw_value, (list, tuple)):
            raw_items = raw_value
        else:
            raise serializers.ValidationError({"objectives": "Objectives must be a text value or a list."})

        cleaned = [str(item).strip() for item in raw_items if str(item).strip()]

        if len(cleaned) == 0:
            raise serializers.ValidationError({"objectives": "Please add at least one objective."})

        if len(cleaned) > 5:
            raise serializers.ValidationError({"objectives": "You can add up to 5 objectives only."})

        return cleaned

    def _sync_objectives(self, instance, objectives):
        """Replace existing objective rows for the application."""
        instance.objective_items.all().delete()

        objective_rows = [
            IntrimAuthorityObjective(application=instance, objective=text, order=index)
            for index, text in enumerate(objectives, start=1)
        ]
        IntrimAuthorityObjective.objects.bulk_create(objective_rows)

    def to_internal_value(self, data):
        normalized_data = data.copy()
        self._prepare_supporting_documents(data)
        has_objectives = False
        objectives_value = None
        self._provided_objectives = False
        self._normalized_objectives = []

        if hasattr(data, 'getlist'):
            objectives_list = data.getlist('objectives')
            if len(objectives_list) > 1:
                has_objectives = True
                objectives_value = objectives_list
            elif 'objectives' in data:
                has_objectives = True
                objectives_value = data.get('objectives')
        elif isinstance(data, dict) and 'objectives' in data:
            has_objectives = True
            objectives_value = data.get('objectives')

        if has_objectives:
            normalized_objectives = self._normalize_objectives(objectives_value)
            self._provided_objectives = True
            self._normalized_objectives = normalized_objectives
            normalized_data['objectives'] = "\n".join(normalized_objectives)

        return super().to_internal_value(normalized_data)

    @transaction.atomic
    def create(self, validated_data):
        instance = super().create(validated_data)
        if getattr(self, '_provided_objectives', False):
            self._sync_objectives(instance, self._normalized_objectives)
        self._sync_supporting_documents(instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        updated_instance = super().update(instance, validated_data)
        if getattr(self, '_provided_objectives', False):
            self._sync_objectives(updated_instance, self._normalized_objectives)
        self._sync_supporting_documents(updated_instance)
        return updated_instance


    def to_representation(self, instance):
        response = super().to_representation(instance)
        request = self.context.get('request')

        def file_url(file_field):
            if not file_field:
                return None
            return request.build_absolute_uri(file_field.url) if request else file_field.url

        objective_rows = list(
            instance.objective_items.order_by('order').values_list('objective', flat=True)
        )
        if objective_rows:
            response['objectives'] = "\n".join(objective_rows)

        response['institution'] = instance.institution.name
        response['status'] = instance.get_status_display()
        response['governance_structure'] = file_url(instance.governance_structure)
        response['human_resources'] = file_url(instance.human_resources)
        response['prn'] = ApplicationPRNS.objects.filter(referenceNo=instance.application_code).last().prn if ApplicationPRNS.objects.filter(referenceNo=instance.application_code).exists() else None
        return response
    
class InterimDiscussionSerializer(serializers.ModelSerializer):
    '''Serializer for InterimDiscussion model.'''
    class Meta:
        '''Meta class for InterimDiscussion Serializer'''
        model = InterimDiscussion
        fields = "__all__"
        read_only_fields = ['id', 'created_at', 'updated_at']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['applicant_name'] = instance.application.institution.name
        response['reviewer_name'] = instance.reviewer.get_full_name() if instance.reviewer else None

        return response

class ProvisionalSupportingDocumentSerializer(InterimSupportingDocumentSerializer):
    class Meta(InterimSupportingDocumentSerializer.Meta):
        model = UniversityProvisionalLicenseDocument


class UniversityProvisionalLicenseVehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniversityProvisionalLicenseVehicle
        fields = ['id', 'make', 'registration_number']
        read_only_fields = ['id']

    def validate_registration_number(self, value):
        return value.upper()


class UniversityProvisionalLicenseSerializer(SupportingDocumentMixin, serializers.ModelSerializer):
    '''Serializer for UniversityProvisionalLicense model.'''
    supporting_documents = ProvisionalSupportingDocumentSerializer(source='documents', many=True, read_only=True)
    specific_objectives = serializers.CharField(required=False, write_only=True)
    vehicles = UniversityProvisionalLicenseVehicleSerializer(many=True, read_only=True)

    def to_internal_value(self, data):
        self._prepare_supporting_documents(data)
        self._prepared_vehicles = None
        if 'vehicles' in data:
            rows = data.get('vehicles')
            if isinstance(rows, str):
                try:
                    rows = json.loads(rows)
                except (ValueError, TypeError):
                    raise serializers.ValidationError({'vehicles': 'Provide a valid vehicle list.'})
            if not isinstance(rows, list):
                raise serializers.ValidationError({'vehicles': 'Provide a vehicle list.'})
            existing = {str(row.pk): row for row in self.instance.vehicles.all()} if self.instance else {}
            prepared, seen_ids, registrations = [], set(), set()
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    raise serializers.ValidationError({'vehicles': 'Each vehicle must include a make and registration number.'})
                row_id = row.get('id')
                previous = existing.get(str(row_id)) if row_id is not None else None
                if row_id is not None and (previous is None or previous.pk in seen_ids):
                    raise serializers.ValidationError({'vehicles': 'An existing vehicle is invalid or repeated.'})
                if previous:
                    seen_ids.add(previous.pk)
                serializer = UniversityProvisionalLicenseVehicleSerializer(data={
                    'make': row.get('make', ''), 'registration_number': row.get('registration_number', ''),
                })
                if not serializer.is_valid():
                    raise serializers.ValidationError({'vehicles': {str(index): serializer.errors}})
                fields = serializer.validated_data
                registration = ''.join(fields['registration_number'].split())
                if registration in registrations:
                    raise serializers.ValidationError({'vehicles': {str(index): {'registration_number': 'This registration number is repeated.'}}})
                registrations.add(registration)
                prepared.append((previous, fields))
            self._prepared_vehicles = prepared
        return super().to_internal_value(data)

    def _sync_vehicles(self, instance):
        if self._prepared_vehicles is None and not instance.vehicles.exists():
            return
        retained_ids = []
        for previous, fields in self._prepared_vehicles or []:
            if previous:
                for field, value in fields.items():
                    setattr(previous, field, value)
                previous.save()
                retained_ids.append(previous.pk)
            else:
                retained_ids.append(instance.vehicles.create(**fields).pk)
        if self._prepared_vehicles is not None:
            instance.vehicles.exclude(pk__in=retained_ids).delete()
        instance.number_of_vehicles = instance.vehicles.count()
        instance.vehicle_registration = '\n'.join(
            f'{row.make} - {row.registration_number}' for row in instance.vehicles.order_by('id')
        )
        instance.save(update_fields=['number_of_vehicles', 'vehicle_registration'])

    @transaction.atomic
    def create(self, validated_data):
        objectives = validated_data.pop('specific_objectives', None)
        instance = super().create(validated_data)
        self._sync_provisional_objectives(instance, objectives)
        self._sync_supporting_documents(instance)
        self._sync_vehicles(instance)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        objectives = validated_data.pop('specific_objectives', None)
        instance = super().update(instance, validated_data)
        self._sync_provisional_objectives(instance, objectives)
        self._sync_supporting_documents(instance)
        self._sync_vehicles(instance)
        return instance

    def _sync_provisional_objectives(self, instance, objectives):
        if objectives is None:
            return
        instance.university_provisional_objective_items.all().delete()
        UniversityProvisionalObjective.objects.bulk_create([
            UniversityProvisionalObjective(application=instance, objective=text, order=index)
            for index, text in enumerate(json.loads(objectives), start=1)
        ])

    def validate_specific_objectives(self, value):
        if value is None:
            raise serializers.ValidationError('Please add at least one objective.')
        try:
            parsed = json.loads(value)
        except (ValueError, TypeError):
            parsed = [line for line in value.splitlines() if line.strip()]
        if not isinstance(parsed, list) or any(not isinstance(item, str) or not item.strip() for item in parsed):
            raise serializers.ValidationError('Each objective must contain text.')
        if not 1 <= len(parsed) <= 5:
            raise serializers.ValidationError('Please provide between 1 and 5 objectives.')
        return json.dumps([item.strip() for item in parsed], ensure_ascii=False)

    class Meta:
        '''Meta class for UniversityProvisionalLicense Serializer'''
        model = UniversityProvisionalLicense
        fields = "__all__"
        read_only_fields = ['id', 'application_code']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['specific_objectives'] = json.dumps(list(
            instance.university_provisional_objective_items.order_by('order', 'id').values_list('objective', flat=True)
        ), ensure_ascii=False)
        if response['vehicles']:
            response['number_of_vehicles'] = len(response['vehicles'])
            response['vehicle_registration'] = '\n'.join(
                f"{row['make']} - {row['registration_number']}" for row in response['vehicles']
            )
        response['institution'] = instance.institution.name
        response['status'] = instance.get_status_display()
        response['geographical_location'] = instance.get_geographical_location_display()
        response['prn'] = ApplicationPRNS.objects.filter(referenceNo=instance.application_code).last().prn if ApplicationPRNS.objects.filter(referenceNo=instance.application_code).exists() else None
        return response
    

class CharterApplicationSerializer(serializers.ModelSerializer):
    '''Serializer for CharterApplication model.'''

    class Meta:
        '''Meta class for CharterApplication Serializer'''
        model = CharterApplication
        fields = "__all__"
        read_only_fields = ['id', 'application_code']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        response['status'] = instance.get_status_display()
        response['prn'] = ApplicationPRNS.objects.filter(referenceNo=instance.application_code).last().prn if ApplicationPRNS.objects.filter(referenceNo=instance.application_code).exists() else None
        return response
    

    
class OTIProvisionalSerializer(serializers.ModelSerializer):
    '''Serializer for OTIProvisional model.'''

    class Meta:
        '''Meta class for OTIProvisional Serializer'''
        model = OTIProvisional
        fields = "__all__"
        read_only_fields = ['id', 'application_code']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institute'] = instance.institute.name
        response['status'] = instance.get_status_display()
        response['prn'] = ApplicationPRNS.objects.filter(referenceNo=instance.code).last().prn if ApplicationPRNS.objects.filter(referenceNo=instance.code).exists() else None
        return response
    
class OTIProvisionalAwardSerializer(serializers.ModelSerializer):
    '''Serializer for OTIProvisionalAward model.'''

    class Meta:
        '''Meta class for OTIProvisionalAward Serializer'''
        model = OTIProvisionalAward
        fields = "__all__"
        read_only_fields = ['id']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        return response
