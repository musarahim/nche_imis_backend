from rest_framework import serializers

from .models import ApplicationPRNS


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