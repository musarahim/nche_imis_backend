import logging

from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_api_key.permissions import HasAPIKey

from .models import ApplicationPRNS
from .serializers import (ApplicationPRNSSerializer,
                          PRNGenerationRequestSerializer,
                          PRNGenerationResponseSerializer,
                          PRNStatusRequestSerializer,
                          PRNStatusResponseSerializer)
from .ura_payment import UraMdaPaymentService

logger = logging.getLogger(__name__)
service = UraMdaPaymentService()

# External API Views for third-party integration
class ExternalPRNGenerationAPIView(APIView):
    """
    API endpoint for external systems to generate PRNs.
    Requires API key authentication.
    
    POST /api/external/generate-prn/
    """
    permission_classes = [HasAPIKey]
    
    def post(self, request):
        """Generate a new PRN for external system."""
        serializer = PRNGenerationRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Invalid PRN generation request: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Prepare PRN request data for URA API
            prn_request_data = serializer.validated_data.copy()
            prn_request_data['assessmentDate'] = timezone.now().isoformat()
            
            # Generate and save PRN using the service
            svc = UraMdaPaymentService()
            application_prn = svc.generate_and_save_prn(prn_request_data)
            
            # Serialize response
            response_serializer = PRNGenerationResponseSerializer(application_prn)
            
            logger.info(f"PRN generated successfully for reference: {application_prn.referenceNo}")
            return Response({
                'success': True,
                'message': 'PRN generated successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as ex:
            logger.error(f"PRN generation failed: {str(ex)}")
            return Response({
                'success': False,
                'message': 'PRN generation failed',
                'error': str(ex)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExternalPRNStatusAPIView(APIView):
    """
    API endpoint for external systems to check PRN status.
    Requires API key authentication.
    
    POST /api/external/check-prn-status/
    """
    permission_classes = [HasAPIKey]
    
    def post(self, request):
        """Check status of a PRN."""
        serializer = PRNStatusRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"Invalid PRN status request: {serializer.errors}")
            return Response({
                'success': False,
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            prn = serializer.validated_data['prn']
            
            # Get PRN record from local database
            application_prn = ApplicationPRNS.objects.get(prn=prn)
            
            # Get live status from URA API
            svc = UraMdaPaymentService()
            ura_status = svc.check_prn_status(prn)
            
            # Update local reconciliation status if needed
            if ura_status.get("statusCode") == "T" and not application_prn.prn_reconciled:
                application_prn.prn_reconciled = True
                application_prn.save()
                logger.info(f"PRN {prn} marked as reconciled")
            
            # Prepare response data
            response_data = {
                'prn': application_prn.prn,
                'referenceNo': application_prn.referenceNo,
                'amount': application_prn.amount,
                'taxPayerName': application_prn.taxPayerName,
                'statusCode': application_prn.statusCode,
                'statusDesc': application_prn.statusDesc,
                'expiryDate': application_prn.expiryDate,
                'prn_reconciled': application_prn.prn_reconciled,
                'ura_status': ura_status
            }
            
            response_serializer = PRNStatusResponseSerializer(response_data)
            
            logger.info(f"PRN status checked successfully for PRN: {prn}")
            return Response({
                'success': True,
                'message': 'PRN status retrieved successfully',
                'data': response_serializer.data
            }, status=status.HTTP_200_OK)
            
        except ApplicationPRNS.DoesNotExist:
            logger.warning(f"PRN not found: {serializer.validated_data.get('prn')}")
            return Response({
                'success': False,
                'message': 'PRN not found in system'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as ex:
            logger.error(f"PRN status check failed: {str(ex)}")
            return Response({
                'success': False,
                'message': 'PRN status check failed',
                'error': str(ex)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Create your views here.
# sample prn call
class CreatePRNView(APIView):
    def post(self, request):
        svc = UraMdaPaymentService()
        prn_request = {
            "clientType": "MDA",
            "mdaCode": request.data.get("mdaCode"),
            "amount": request.data.get("amount"),
            "taxPayerType": request.data.get("taxPayerType"),
            "narration": request.data.get("narration"),
            "externalReferenceNumber": request.data.get("externalReferenceNumber"),
        }  # validate in a serializer!
        try:
            data = svc.get_prn(prn_request)
            return Response(data, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        

class ApplicationPRNSViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ApplicationPRNS.objects.all()
    serializer_class = ApplicationPRNSSerializer

    def get_queryset(self):
        application_code = self.request.query_params.get('application_code')
        if application_code:
            prn_objects = ApplicationPRNS.objects.filter(referenceNo=application_code).order_by("-assessmentDate")
            # check if prns where reconciled and update the prn_reconciled field accordingly
            for prn in prn_objects:
                if prn.prn and not prn.prn_reconciled:
                    # Here you would typically call a method to check the PRN status with URA
                    # For example: is_reconciled = check_prn_status_with_ura(prn.prn)
                    # For demonstration, let's assume all PRNs are reconciled
                   checked_status = service.check_prn_status(prn.prn)  # This method should call URA to get the current status of the PRN
                   if checked_status.get("statusCode") == "T":
                       prn.prn_reconciled = True
                       prn.save()
                   else:
                       print(f"PRN {prn.prn} is not yet reconciled. Current status: {checked_status.get('statusCode')}")


            return prn_objects
        return super().get_queryset().order_by("-assessmentDate")