from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .ura_payment import UraMdaPaymentService


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