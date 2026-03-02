from accounts.models import User
from common.models import District, Region
from django.db import transaction
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from .models import Institution, LicenseType, OtherDocuments


class InstitutionSerializer(serializers.ModelSerializer):
    '''Serializer for Institution model.'''
    logo = Base64ImageField(
        max_length=None, use_url=True, required=True, allow_null=True
    )
    class Meta:
        '''Meta class for Institution Serializer'''
        model = Institution
        fields = [
            'id', 'user', 'name','acroynm','region', 'district', 'institution_type',"alternative_email",
            'landline','website','postal_address', 'contact_person', 'contact_person_phone',
            'alternative_contact_person', 'alternative_contact_person_phone','location',
            'logo','tin','is_closed',
        ]
        read_only_fields = ['id', 'user']

    def to_representation(self, instance):
        '''Override to_representation method for proper representation of data'''
        representation = super().to_representation(instance)
        representation['district'] = instance.district.name
        representation['region'] = instance.region.name if instance.region else None
        representation['institution_type'] = instance.get_institution_type_display()
        representation['phone'] = instance.user.phone.raw_input if instance.user else ''
        representation['email'] = instance.user.email if instance.user else ''
        return representation
    



class OtherDocumentsSerializer(serializers.ModelSerializer):
    '''Serializer for OtherDocuments model.'''
    class Meta:
        '''Meta class for OtherDocuments Serializer'''
        model = OtherDocuments
        fields = ['id', 'document_name', 'document']
        read_only_fields = ['id']


class LicenseTypeSerializer(serializers.ModelSerializer):
    '''Serializer for LicenseType model.'''
    class Meta:
        '''Meta class for LicenseType Serializer'''
        model = LicenseType
        fields = ['id','code', 'name']
        read_only_fields = ['id']


# serializer for larger payloads
class InstitutionCreateSerializer(serializers.Serializer):
    # ---------------- USER FIELDS ----------------
    username = serializers.CharField(max_length=50)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    alternative_phone_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    other_names = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    # ---------------- INSTITUTION FIELDS ----------------
    name = serializers.CharField(max_length=255)
    acroynm = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    alternative_email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    tin = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    region = serializers.IntegerField(required=False, allow_null=True)
    district = serializers.IntegerField()

    institution_type = serializers.ChoiceField(
        choices=Institution.INSTITUTION_TYPE_CHOICES,
        default="public"
    )

    landline = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    contact_person = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    contact_person_phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    alternative_contact_person = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    alternative_contact_person_phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    website = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    location = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    address = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    license = serializers.IntegerField(required=False, allow_null=True)
    is_closed = serializers.BooleanField(required=False, allow_null=True)

    # ---------------- CREATE LOGIC ----------------
    @transaction.atomic
    def create(self, validated_data):

        # ---- Extract user data ----
        username = validated_data.pop("username")
        email = validated_data.pop("email")
        password = validated_data.pop("password")

        phone = validated_data.pop("phone", None)
        alternative_phone_number = validated_data.pop("alternative_phone_number", None)
        first_name = validated_data.pop("first_name", None)
        last_name = validated_data.pop("last_name", None)
        other_names = validated_data.pop("other_names", None)

        # ---- Create user ----
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        user.phone = phone
        user.alternative_phone_number = alternative_phone_number
        user.first_name = first_name
        user.last_name = last_name
        user.other_names = other_names
        user.is_active = True   # remove if approval workflow needed
        user.save()

        # ---- Map address -> postal_address ----
        postal_address = validated_data.pop("address", None)

        # ---- Convert district ID to instance and get its region ----
        district_id = validated_data.pop("district")
        validated_data.pop("region", None)  # Remove region from validated_data if provided
        
        district = District.objects.get(id=district_id)
        region = district.region  # Get region from the district

        # ---- Convert license ID to instance ----
        license_id = validated_data.pop("license", None)
        license_instance = None
        if license_id and license_id != 0:  # Handle cases where license is None, 0, or empty
            license_instance = LicenseType.objects.get(id=license_id)

        # ---- Create institution ----
        institution = Institution.objects.create(
            user=user,
            postal_address=postal_address,
            district=district,
            region=region,
            license=license_instance,
            **validated_data
        )

        return institution

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "user_id": instance.user.id,
            "username": instance.user.username,
            "email": instance.user.email,
            "name": instance.name,
            "district": instance.district_id,
            "region": instance.region_id,
            "institution_type": instance.institution_type,
            "is_closed": instance.is_closed,
        }