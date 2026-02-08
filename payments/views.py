from django.shortcuts import get_object_or_404, render
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ApplicationPRNS
from .serializers import ApplicationPRNSSerializer
from .ura_payment import UraMdaPaymentService

service = UraMdaPaymentService()
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