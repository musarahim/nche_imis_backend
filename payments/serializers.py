from decimal import Decimal

from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import ApplicationPRNS


class PRNGenerationRequestSerializer(serializers.Serializer):
    """Serializer for PRN generation requests from external systems."""
    
    # Required fields
    amount = serializers.IntegerField(help_text="Amount to be paid")
    referenceNo = serializers.CharField(max_length=100, help_text="External system reference number")
    taxHead = serializers.CharField(max_length=100)
    taxSubHead = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Taxpayer information
    tin = serializers.CharField(max_length=100, required=False, allow_blank=True,
                                validators=[RegexValidator(r'^\d{10}$', 'TIN must be 10 digits')])
    taxPayerName = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    contactNo = serializers.CharField(max_length=20, required=False, allow_blank=True)
    mobileNo = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    # Address fields
    plot = serializers.CharField(max_length=100, required=False, allow_blank=True)
    buildingName = serializers.CharField(max_length=100, required=False, allow_blank=True)
    street = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tradeCentre = serializers.CharField(max_length=100, required=False, allow_blank=True)
    district = serializers.CharField(max_length=100, required=False, allow_blank=True)
    county = serializers.CharField(max_length=100, required=False, allow_blank=True)
    subCounty = serializers.CharField(max_length=100, required=False, allow_blank=True)
    parish = serializers.CharField(max_length=100, required=False, allow_blank=True)
    village = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # System fields
    paymentType = serializers.CharField(max_length=100, default="DT")
    srcSystem = serializers.CharField(max_length=100, default="EXTERNAL_API")
    expiryDays = serializers.CharField(max_length=100, default="30")
    
    def validate_referenceNo(self, value):
        """Ensure reference number is unique."""
        if ApplicationPRNS.objects.filter(referenceNo=value).exists():
            raise serializers.ValidationError("Reference number already exists.")
        return value


class PRNGenerationResponseSerializer(serializers.ModelSerializer):
    """Serializer for PRN generation response to external systems."""
    
    class Meta:
        model = ApplicationPRNS
        fields = [
            'id', 'referenceNo', 'prn', 'amount', 'taxPayerName', 'email',
            'statusCode', 'statusDesc', 'expiryDate', 'searchCode'
        ]
        read_only_fields = fields


class PRNStatusRequestSerializer(serializers.Serializer):
    """Serializer for PRN status check requests from external systems."""
    prn = serializers.CharField(max_length=100, help_text="Payment Reference Number to check")
    
    def validate_prn(self, value):
        """Ensure PRN exists in our system."""
        if not ApplicationPRNS.objects.filter(prn=value).exists():
            raise serializers.ValidationError("PRN not found in system.")
        return value


class PRNStatusResponseSerializer(serializers.Serializer):
    """Serializer for PRN status response to external systems."""
    prn = serializers.CharField()
    referenceNo = serializers.CharField()
    amount = serializers.IntegerField()
    taxPayerName = serializers.CharField()
    statusCode = serializers.CharField()
    statusDesc = serializers.CharField()
    expiryDate = serializers.DateField()
    prn_reconciled = serializers.BooleanField()
    ura_status = serializers.DictField(required=False, help_text="Live status from URA API")


class ApplicationPRNSSerializer(serializers.ModelSerializer):
    '''Serializer for ApplicationPRNS model.'''
    class Meta:
        '''Default serializer for ApplicationPRNS model.'''
        model = ApplicationPRNS
        fields = "__all__"
        read_only_fields = ['id', 'referenceNo', 'prn', 'statusCode', 'statusDesc', 'searchCode']

    def to_representation(self, instance):
        '''Custom representation to include institution name'''
        response = super().to_representation(instance)
        response['prn_reconciled'] = 'Yes' if instance.prn_reconciled else 'No'
        return response