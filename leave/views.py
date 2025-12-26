from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from hr.models import Employee
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import LeaveApplication, LeaveEvent, LeaveType
from .serializers import (LeaveApplicationSerializer, LeaveScheduleSerializer,
                          LeaveTypeSerializer)

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

    def get_queryset(self):
        """
        Override to filter leave applications by the logged-in employee.
        """
        employee = Employee.objects.get(system_account=self.request.user)
        return LeaveApplication.objects.filter(employee=employee)
    
    def retrieve(self, request,pk=None):
        """
        GET /leave-applications/{id}/
        Retrieve a specific leave application by ID.
        """
        leave_application = LeaveApplication.objects.get(pk=pk)
        serializer = self.get_serializer(leave_application)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='schedules')
    def schedules(self, request, pk=None):
        """
        GET /leave-applications/{id}/schedules/
        Retrieve planned (scheduled) leaves for a specific employee.
        """
        employee = Employee.objects.get(system_account=request.user)
        leave_application = LeaveApplication.objects.filter(employee=employee, status='planned').all()
        serializer = self.get_serializer(leave_application, many=True)
        self.pagination_class = None
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='schedule')
    def schedule(self, request, *args, **kwargs):
        """
        POST /leave-applications/schedule/
        Creates a PLANNED (scheduled) leave, not yet submitted.
        """
        serializer = LeaveScheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        #getting employee from request user
        employee = Employee.objects.get(system_account=request.user)
        # For planned leave
        instance = serializer.save(status='planned', employee=employee)
        # If you want a different response structure, you can customize here
        return Response(
            self.get_serializer(instance).data,
            status=status.HTTP_201_CREATED
        )
    
    def partial_update(self, request, pk, format=None):
        """
        PUT /leave-applications/{id}/
        Update a leave application.
        """
        leave_application = self.get_object()
        serializer = LeaveApplicationSerializer(leave_application, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            status = serializer.data.get('status')
            # Additional logic based on status can be added here
            if status == 'submitted':
                print('send email notification')
                # send the applicant an email notification
                html_message = render_to_string('emails/leave_application.html', {
                    'leave_application': leave_application,
                    'protocol': 'https',
                    'domain': 'imis.unche.or.ug',
                    'site_name': 'UNCHE IMIS',
                })
                email = EmailMessage(
                    subject='Leave Application Submission',
                    body=html_message,
                    to=[leave_application.employee.system_account.email],
                )
                email.content_subtype = 'html'  # Main content is now text/html
                email.send(fail_silently=True)

                html_message2 = render_to_string('emails/delegation_notification.html', {
                    'leave_application': leave_application,
                    'protocol': 'https',
                    'domain': 'imis.unche.or.ug',
                    'site_name': 'UNCHE IMIS',
                })
                email2 = EmailMessage(
                    subject=f'Action Required: Leave Approval Request from {leave_application.employee.full_name}',
                    body=html_message2,
                    to=[leave_application.delegated_to.system_account.email],
                )
                email2.content_subtype='html'
                email2.send()

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='delegations')
    def delegations(self, request):
        """
        GET /leave-applications/delegations/
        Retrieve leave delegations for a specific employee.
        """
        employee = Employee.objects.get(system_account=request.user)
        queryset = LeaveApplication.objects.filter(delegated_to=employee, status='submitted')
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback if no pagination is configured
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='approve_delegation')
    def acceptDelegation(self, request, pk=None):
        """
        POST /leave-applications/{id}/approve_delegation/
        Approve a leave application delegation.
        """
        leave_application = LeaveApplication.objects.get(pk=pk)
        serializer = LeaveApplicationSerializer(leave_application, data=request.data, partial=True)
        if serializer.is_valid():
            accepted = serializer.validated_data.get('delegation_accepted')
            leave_status = 'delegation_accepted' if accepted else 'delegation_rejected'
            serializer.save(status=leave_status, delegation_acceptance_date= timezone.now())
            # Send email notification to the applicant about approval
            html_message = render_to_string('emails/leave_approval_notification.html', {
                'leave_application': leave_application,
                'protocol': 'https',
                'domain': 'imis.unche.or.ug',
                'site_name': 'UNCHE IMIS',
            })
            email = EmailMessage(
                subject='Leave Delegation Acceptance Notification',
                body=html_message,
                to=[leave_application.employee.system_account.email],
            )
            email.content_subtype = 'html'  # Main content is now text/html
            email.send(fail_silently=True)
            # notify supervisor incase the delegation is accepted
            if accepted:
                html_message = render_to_string('emails/leave_approval_request.html', {
                'leave_application': leave_application,
                'protocol': 'https',
                'domain': 'imis.unche.or.ug',
                'site_name': 'UNCHE IMIS',
                })
                email = EmailMessage(
                subject='Leave  Approval Request',
                body=html_message,
                to=[leave_application.employee.system_account.email],
                )
                email.content_subtype = 'html'  # Main content is now text/html
                email.send(fail_silently=True)

            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='supervisor-approvals')
    def supervisor_approvals(self, request):
        """
        GET /leave-applications/supervisor-approvals/
        Retrieve leave applications pending supervisor approval.
        """
        employee = Employee.objects.get(system_account=request.user)
        queryset = LeaveApplication.objects.filter(supervisor=employee, delegation_accepted=True, status='delegation_accepted')
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback if no pagination is configured
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='approve_supervisor')
    def approve_supervisor(self, request, pk=None):
        """
        POST /leave-applications/{id}/approve_supervisor/
        Approve a leave application by supervisor.
        """
        leave_application = LeaveApplication.objects.get(pk=pk)
        serializer = LeaveApplicationSerializer(leave_application, data=request.data, partial=True)
        if serializer.is_valid():
            approved = serializer.validated_data.get('supervisor_approved')
            leave_status = 'supervisor_approved' if approved else 'supervisor_rejected'
            serializer.save(status=leave_status, approval_date= timezone.now())
            # Send email notification to the applicant about approval
            html_message = render_to_string('emails/leave_supervisor_approval_notification.html', {
                'leave_application': leave_application,
                'protocol': 'https',
                'domain': 'imis.unche.or.ug',
                'site_name': 'UNCHE IMIS',
            })
            email = EmailMessage(
                subject='Leave Supervisor Approval Notification',
                body=html_message,
                to=[leave_application.employee.system_account.email],
            )
            email.content_subtype = 'html'  # Main content is now text/html
            email.send(fail_silently=True)

            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='director-approvals')
    def director_approvals(self, request):
        """
        GET /leave-applications/director-approvals/
        Retrieve leave applications pending director approval.
        """
        director = Employee.objects.get(system_account=request.user)
        queryset = LeaveApplication.objects.filter(employee__directorate=director.directorate, supervisor_approved=True, status='supervisor_approved')
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback if no pagination is configured
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='approve_director')
    def approve_director(self, request, pk=None):
        """
        POST /leave-applications/{id}/approve_director/
        Approve a leave application by director.
        """
        leave_application = LeaveApplication.objects.get(pk=pk)
        serializer = LeaveApplicationSerializer(leave_application, data=request.data, partial=True)
        director = Employee.objects.get(system_account=request.user)
        if serializer.is_valid():
            approved = serializer.validated_data.get('director_approved')
            leave_status = 'director_approved' if approved else 'director_rejected'
            serializer.save(status=leave_status, director_approval_date= timezone.now(), director=director)
            # Send email notification to the applicant about approval
            html_message = render_to_string('emails/director_leave_approval_notification.html', {
                'leave_application': leave_application,
                'protocol': 'https',
                'domain': 'imis.unche.or.ug',
                'site_name': 'UNCHE IMIS',
            })
            email = EmailMessage(
                subject='Director Leave Approval Notification',
                body=html_message,
                to=[leave_application.employee.system_account.email],
            )
            email.content_subtype = 'html'  # Main content is now text/html
            email.send(fail_silently=True)

            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        