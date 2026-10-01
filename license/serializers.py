import json

from payments.models import ApplicationPRNS
from rest_framework import serializers

from .models import (CertificationAndClassification, CharterApplication,
                     InterimDiscussion, InterimPromoters, IntrimAuthority,
                     IntrimAuthorityObjective, OTIProvisional,
                     OTIProvisionalAward, UniversityProvisionalLicense)


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
    class Meta:
        model = InterimPromoters
        fields = "__all__"
        read_only_fields = []


class IntrimAuthorityObjectiveSerializer(serializers.ModelSerializer):
    """Serializer for single interim authority objective rows."""

    class Meta:
        model = IntrimAuthorityObjective
        fields = ["id", "objective", "order"]
        read_only_fields = ["id"]

class IntrimAuthoritySerializer(serializers.ModelSerializer):
    '''Serializer for IntrimAuthority model.'''
    promoters_details = InterimPromotersSerializer(source='interimpromoters_set', many=True, read_only=True)
    objective_items = IntrimAuthorityObjectiveSerializer(many=True, read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._provided_objectives = False
        self._normalized_objectives = []

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

    def create(self, validated_data):
        instance = super().create(validated_data)
        if getattr(self, '_provided_objectives', False):
            self._sync_objectives(instance, self._normalized_objectives)
        return instance

    def update(self, instance, validated_data):
        updated_instance = super().update(instance, validated_data)
        if getattr(self, '_provided_objectives', False):
            self._sync_objectives(updated_instance, self._normalized_objectives)
        return updated_instance


    def to_representation(self, instance):
        response = super().to_representation(instance)
        objective_rows = list(
            instance.objective_items.order_by('order').values_list('objective', flat=True)
        )
        if objective_rows:
            response['objectives'] = "\n".join(objective_rows)

        response['institution'] = instance.institution.name
        response['status'] = instance.get_status_display()
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

class UniversityProvisionalLicenseSerializer(serializers.ModelSerializer):
    '''Serializer for UniversityProvisionalLicense model.'''

    class Meta:
        '''Meta class for UniversityProvisionalLicense Serializer'''
        model = UniversityProvisionalLicense
        fields = "__all__"
        read_only_fields = ['id', 'application_code']


    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['institution'] = instance.institution.name
        response['status'] = instance.get_status_display()
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