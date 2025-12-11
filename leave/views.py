from django.shortcuts import render
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import LeaveApplication, LeaveEvent, LeaveType
from .serializers import LeaveApplicationSerializer, LeaveTypeSerializer

# Create your views here.

class LeaveTypeViewset(viewsets.ModelViewSet):
    '''Leave Type viewset'''
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    pagination_class = None



class LeaveApplicationViewSet(viewsets.ModelViewSet):
    queryset = LeaveApplication.objects.all()
    serializer_class = LeaveApplicationSerializer

    def perform_create(self, serializer):
        """
        Default create -> normal leave application (submitted).
        This is called by POST /leave-applications/
        """
        # You can also infer employee from request.user here if needed
        serializer.save(status='submitted')

    @action(detail=False, methods=['post'], url_path='schedule')
    def schedule(self, request, *args, **kwargs):
        """
        POST /leave-applications/schedule/
        Creates a PLANNED (scheduled) leave, not yet submitted.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # For planned leave
        instance = serializer.save(status='planned')

        # If you want a different response structure, you can customize here
        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_201_CREATED
        )
