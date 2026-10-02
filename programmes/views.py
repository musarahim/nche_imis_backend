from io import BytesIO

from accounts.models import User
from accounts.serializers import UserReviewerSerializer
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import (InvoiceItemType, PreliminaryReview, Program,
                     ProgramAccreditation, ProgrammeAssessment,
                     ProgrammeAssessmentInvoice, ProgrammeInvoice)
from .invoice_permissions import can_manage_review_invoices
from .review_invoice_views import ProgrammeAssessmentInvoiceViewset
from .serializers import (InvoiceItemSerializer, InvoiceItemTypeSerializer,
                          PreliminaryReviewSerializer,
                          ProgrammeAccreditationSerializer,
                          ProgrammeAssessmentInvoiceSerializer,
                          ProgrammeAssessmentSerializer,
                          ProgrammeInvoiceSerializer, ProgramSerializer,
                          ProgressedToDirectorateSerializer)


# Create your views here.
class ProgrammeAccreditationViewset(viewsets.ModelViewSet):
    '''Programme Accreditation Applications'''
    queryset = ProgramAccreditation.objects.all()
    serializer_class = ProgrammeAccreditationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application_number','programme_name','programme_level','status','institution__name']
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    @staticmethod
    def _ready_for_assessment_queryset():
        """Applications whose programme or desk-review payment was cleared by accounts."""
        return ProgramAccreditation.objects.filter(status='invoice_reconciled').filter(
            Q(programme_invoices__status='reconciled', programme_invoices__cleared=True)
            | Q(assessment_invoices__status='reconciled', assessment_invoices__cleared=True)
        ).distinct()

    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
            or self.request.user.has_perm('programmes.can_approve_programme_at_management_level')
        ):
            return queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        if hasattr(self.request.user, 'institution'):
            return queryset.filter(institution=self.request.user.institution)

        return queryset.none()

    def retrieve(self, request,pk=None):
        '''retrieve a programme accreditation application'''
        application = self.get_object()
        serializer = self.get_serializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def _send_rejection_email(self, application, reason):
        '''Send rejection notification email to the applicant institution.'''
        if not application or not application.institution:
            return

        institution_user = getattr(application.institution, 'user', None)
        recipient = getattr(institution_user, 'email', None)

        if not recipient:
            return

        html_message = render_to_string('email/programme_rejection.html', {
            'application': application,
            'institution': application.institution,
            'reason': reason,
        })

        email = EmailMessage(
            subject='NCHE Programme Application Rejected',
            body=html_message,
            to=[recipient],
        )
        email.content_subtype = 'html'
        email.send(fail_silently=True)

    def partial_update(self, request, *args, **kwargs):
        '''Allow institutions to amend their own submitted application documents.'''
        application = self.get_object()
        if getattr(request.user, 'institution', None) != application.institution:
            raise PermissionDenied('Only the applicant institution can amend this application.')
        if application.status not in ('submitted', 'returned_for_review'):
            raise ValidationError('This application can no longer be amended.')
        forbidden = set(request.data) & {
            'status', 'institution', 'application_number', 'application_type', 'program_to_renew',
            'preliminary_reviewer', 'assessor', 'pod_comment', 'director_comment', 'is_paid',
            'rejection_reason',
        }
        if forbidden:
            raise ValidationError({field: 'This field cannot be changed here.' for field in forbidden})
        return super().partial_update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if not kwargs.get('partial', False):
            return Response({'detail': 'Use PATCH to amend an application.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return Response({'detail': 'Submitted applications cannot be deleted.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    @action(detail=True, methods=['post'], url_path='management-decision')
    def management_decision(self, request, pk=None):
        if not request.user.has_perm('programmes.can_approve_programme_at_management_level'):
            raise PermissionDenied('Management approval permission is required.')
        decision = request.data.get('decision')
        if decision not in ('approved', 'rejected'):
            raise ValidationError({'decision': 'Choose approved or rejected.'})
        reason = str(request.data.get('reason') or '').strip()
        if decision == 'rejected' and not reason:
            raise ValidationError({'reason': 'A rejection reason is required.'})

        with transaction.atomic():
            application = (
                ProgramAccreditation.objects.select_for_update(of=('self',))
                .select_related('institution')
                .get(pk=self.get_object().pk)
            )
            if application.status != 'progressed_to_management':
                raise ValidationError('Only applications progressed to management can be decided.')
            if decision == 'approved':
                today = timezone.localdate()
                if application.application_type == 'renewal':
                    if not application.program_to_renew_id:
                        raise ValidationError('This renewal has no linked programme.')
                    programme = Program.objects.select_for_update().get(pk=application.program_to_renew_id)
                    if programme.institution_id != application.institution_id:
                        raise ValidationError('The linked programme belongs to another institution.')
                    if programme.program_name != application.program_name or programme.program_level != application.program_level:
                        raise ValidationError('The linked programme name or level has changed since submission.')
                    start = max(today, programme.expiry_date) if programme.expiry_date else today
                elif application.application_type == 'new':
                    if Program.objects.filter(institution=application.institution, program_name=application.program_name).exists():
                        raise ValidationError('This programme already exists. Submit a renewal instead.')
                    programme = Program(institution=application.institution, program_name=application.program_name,
                                        program_level=application.program_level)
                    start = today
                else:
                    raise ValidationError('This decision action supports new and renewal applications only.')
                try:
                    expiry = start.replace(year=start.year + 5)
                except ValueError:
                    expiry = start.replace(month=2, day=28, year=start.year + 5)
                programme.accreditation_date = today
                programme.expiry_date = expiry
                programme.status = 'active'
                programme.save()
                programme.applications.add(application)
                application.approved_expiry_date = expiry
            else:
                application.rejection_reason = reason
            application.status = decision
            application.decision_date = timezone.localdate()
            application.save(update_fields=['status', 'decision_date', 'rejection_reason'] if decision == 'rejected' else ['status', 'decision_date', 'approved_expiry_date'])

        if decision == 'rejected':
            self._send_rejection_email(application, reason)
        return Response(self.get_serializer(application).data)
    
    @action(detail=False, methods=['get'], url_path='submitted-applications')
    def submitted_applications(self, request, pk=None):
        """
        GET applications submitted by the logged in user's institution.
        """
        queryset = self.get_queryset().filter(status='submitted')
        if queryset is None or not queryset.exists():
            return Response([], status=status.HTTP_200_OK)
        
        # Apply pagination manually for custom actions
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        # Fallback if pagination is not configured
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='under-review')
    def under_review(self, request, pk=None):
        """
        GET applications under review.
        """
        queryset = ProgramAccreditation.objects.filter(status='under_review')

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
        ):
            queryset = queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        elif self.request.user.groups.filter(name='Programme Reviewers').exists():
            queryset = queryset.filter(
                preliminary_reviewer=self.request.user
            ).select_related('institution').order_by('institution__name', '-date_submitted')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='reviewed-applications')
    def reviewed_applications(self, request, pk=None):
        """
        GET applications that have been reviewed.
        """
        queryset = ProgramAccreditation.objects.filter(status='reviewed')

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='assign-reviewer')
    def assign_reviewer(self, request, pk=None):
        '''assign multiple applications to a reviewer
            applications come as a list of application ids and reviewer is the user id of the reviewer'''
        if not request.user.has_perm('programmes.can_assign_reviewers'):
            raise PermissionDenied('Reviewer assignment permission is required.')
        application_ids = request.data.get('applications', [])
        reviewer_id = request.data.get('userId')
        
        if not application_ids or not reviewer_id:
            return Response({'error': 'applications and userId are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            reviewer = User.objects.get(id=reviewer_id)
        except User.DoesNotExist:
            return Response({'error': 'Reviewer not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        applications = ProgramAccreditation.objects.filter(id__in=application_ids)
        
        for application in applications:
            application.preliminary_reviewer=reviewer
            if application.status != 'under_review':
                application.status = 'under_review'
                application.save()
            #TODO: send emails to reviewers
        
        return Response({'message': f'{len(applications)} applications assigned to reviewer {reviewer.username}.'}, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='assign-assessor')
    def assign_assessor(self, request, pk=None):
        '''assign multiple applications to an assessor
            applications come as a list of application ids and assessor is the user id of the assessor'''
        if not request.user.has_perm('programmes.can_assign_assessors'):
            raise PermissionDenied('Assessor assignment permission is required.')
        application_ids = request.data.get('applications', [])
        assessor_id = request.data.get('userId')
        
        if not isinstance(application_ids, list) or not application_ids or not assessor_id:
            return Response({'error': 'applications and userId are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            requested_ids = {int(application_id) for application_id in application_ids}
        except (TypeError, ValueError):
            raise ValidationError({'applications': 'Provide valid application IDs.'})
        if any(application_id <= 0 for application_id in requested_ids):
            raise ValidationError({'applications': 'Provide valid application IDs.'})
        
        try:
            assessor = User.objects.get(id=assessor_id)
        except User.DoesNotExist:
            return Response({'error': 'Assessor not found.'}, status=status.HTTP_404_NOT_FOUND)
        if not assessor.groups.filter(name='Programme Assessors').exists():
            raise ValidationError({'userId': 'Select a programme assessor.'})

        with transaction.atomic():
            applications = list(ProgramAccreditation.objects.select_for_update().filter(pk__in=requested_ids))
            ready_ids = set(self._ready_for_assessment_queryset().filter(pk__in=requested_ids).values_list('pk', flat=True))
            if ready_ids != requested_ids:
                raise ValidationError({'applications': 'Only paid and reconciled applications can be assigned.'})
            for application in applications:
                application.assessor = assessor
                application.status = 'under_assessment'
                application.save(update_fields=['assessor', 'status'])
        #TODO: send emails to assessors
        
        return Response({'message': f'{len(applications)} applications assigned to assessor {assessor.username}.'}, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=['get'], url_path='ready-for-assessment')
    def ready_for_assessment(self, request, pk=None):
        """
        applications ready for assessment.
        """
        queryset = self._ready_for_assessment_queryset()

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
            or self.request.user.has_perm('programmes.can_assign_assessors')
        ):
            queryset = queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        elif self.request.user.groups.filter(name='Programme Reviewers').exists():
            queryset = queryset.filter(
                preliminary_reviewer=self.request.user
            ).select_related('institution').order_by('institution__name', '-date_submitted')
        else:
            queryset = queryset.none()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    # progressed tp accounting stage
    @action(detail=False, methods=['get'], url_path='ready-for-invoicing')
    def ready_for_invoicing(self, request, pk=None):
        """
        applications ready for invoicing.
        """
        queryset = ProgramAccreditation.objects.filter(status='progressed_to_accounting')

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
        ):
            queryset = queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        elif self.request.user.groups.filter(name='Programme Reviewers').exists():
            queryset = queryset.filter(
                preliminary_reviewer=self.request.user
            ).select_related('institution').order_by('institution__name', '-date_submitted')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['get'], url_path='under-assessment')
    def under_assessment(self, request, pk=None):
        """
        GET applications under assessment.
        """
        queryset = ProgramAccreditation.objects.filter(status='under_assessment')

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
        ):
            queryset = queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        elif self.request.user.groups.filter(name='Programme Assessors').exists():
            queryset = queryset.filter(
                assessor=self.request.user
            ).select_related('institution').order_by('institution__name', '-date_submitted')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='progressed-to-directorate')
    def directorate_stage(self, request, pk=None):
        """
        GET applications progressed to directorate stage.
        """
        queryset = ProgramAccreditation.objects.filter(status='progressed_to_director')

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
        ):
            queryset = queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        elif self.request.user.groups.filter(name='Programme Assessors').exists():
            queryset = queryset.filter(
                assessor=self.request.user
            ).select_related('institution').order_by('institution__name', '-date_submitted')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='progressed-to-directorate-details')
    def directorate_stage_details(self, request, pk=None):
        """
        GET applications progressed to directorate stage.
        """
        application = get_object_or_404(ProgramAccreditation, pk=pk, status='progressed_to_director')
        serializer = ProgressedToDirectorateSerializer(application, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='progressed-to-management-details')
    def management_stage_details(self, request, pk=None):
        """
        GET applications progressed to management stage.
        """
        application = get_object_or_404(ProgramAccreditation, pk=pk, status='progressed_to_management')
        serializer = ProgressedToDirectorateSerializer(application, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # Director's comment 
    @action(detail=True, methods=['post'], url_path='add-director-comment')
    def add_director_comment(self, request, pk=None):
        """
        POST director's comment on an application.
        """
        if not request.user.has_perm('programmes.can_make_directorate_decision'):
            raise PermissionDenied('Directorate decision permission is required.')
        application = get_object_or_404(ProgramAccreditation, pk=pk, status='progressed_to_director')
        comment = request.data.get('comment')
        app_status = request.data.get('status')  # expected values: 'progressed_to_management' or 'rejected'
        
        if not comment:
            return Response({'error': 'Comment is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        application.director_comment = comment
        application.director_comment_date = timezone.now()
        if app_status == 'progressed_to_management':
            application.status = 'progressed_to_management'
        elif app_status == 'rejected':
            application.status = 'rejected'
            application.rejection_reason = comment
        application.save()

        if app_status == 'rejected':
            self._send_rejection_email(application, comment)
        # TODO: send email notification to management and department head about the director's comment and application status

        return Response({'message': 'Director comment added successfully.'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='post_invoice')
    def invoice(self, request, pk=None):
        """
        Add an invoice to an applications.
        """
        application = get_object_or_404(ProgramAccreditation, pk=pk, status='progressed_to_accounting')
        serializer = ProgrammeInvoiceSerializer(application, data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            serializer.save(status='invoiced', invoice_status='pending', invoice_cleared=False, invoice_date=timezone.now())
            # send email notification to the institution about the invoice details
            html_message = render_to_string('email/invoice_details.html', {
                'application': application,
                'institution': application.institution,
                'invoice_amount': serializer.validated_data.get('invoice_amount'),
                'invoice_number': serializer.validated_data.get('invoice_number'),
                'invoice_date': serializer.validated_data.get('invoice_date'),
            })
            email = EmailMessage(
                subject='NCHE Programme Application Invoice Details',
                body=html_message,
                to=[application.institution.user.email],
                )
            email.content_subtype = 'html'  # Main content is now text/html
            email.send(fail_silently=False)
            return Response({'message': 'Invoice details added successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    # invoice applications 
    @action(detail=False, methods=['get'], url_path='invoiced-applications')
    def invoiced_applications(self, request, pk=None):
        """
        GET applications that have been invoiced.
        """
        queryset = ProgramAccreditation.objects.filter(invoice_number__isnull=False, invoice_amount__isnull=False)

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
        ):
            queryset = queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

   
    # progressed to management stage
    @action(detail=False, methods=['get'], url_path='progressed-to-management')
    def progressed_to_management(self, request, pk=None):
        """
        GET applications progressed to management stage.
        """
        queryset = ProgramAccreditation.objects.filter(status='progressed_to_management')

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
        ):
            queryset = queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        '''Set institution to the logged in user's institution'''
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = self.request.user
            institution = getattr(user, 'institution', None)
            if institution is None:
                raise PermissionDenied('Only an institution can submit an application.')
            with transaction.atomic():
                programme = serializer.validated_data.get('program_to_renew')
                if programme:
                    Program.objects.select_for_update().get(pk=programme.pk)
                    if ProgramAccreditation.objects.filter(program_to_renew=programme).exclude(status__in=['approved', 'rejected']).exists():
                        raise ValidationError({'program_to_renew': 'This programme already has an open renewal application.'})
                serializer.save(
                    institution=institution,
                    previous_accreditation_date=programme.accreditation_date if programme else None,
                    previous_expiry_date=programme.expiry_date if programme else None,
                )
            # Send email notification to the institution about successful submission of the application
            html_message = render_to_string('email/programme_submission.html', {
                'application': serializer.instance,
                'institution': institution,
                })
            email = EmailMessage(
                subject='NCHE Programme Application Received',
                body=html_message,
                to=[user.email],
                )
            email.content_subtype = 'html'  # Main content is now text/html
            email.send(fail_silently=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProgramViewset(viewsets.ReadOnlyModelViewSet):
    '''University programs'''
    queryset = Program.objects.prefetch_related('renewals')
    serializer_class = ProgramSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['program_name','program_level','accreditation_date','expiry_date']
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists() or self.request.user.groups.filter(name='Head Programme Accreditation').exists():
            data = queryset
        else:
            if hasattr(self.request.user, 'institution'):
                data = queryset.filter(institution=self.request.user.institution)
            else:
                data = queryset.none()
        return data

    @action(detail=False, methods=['get'], url_path='renewal-options')
    def renewal_options(self, request):
        institution = getattr(request.user, 'institution', None)
        if institution is None:
            raise PermissionDenied('Only an institution can submit a renewal.')
        programmes = self.get_queryset().filter(institution=institution,
            accreditation_date__isnull=False, expiry_date__isnull=False).exclude(
            renewals__status__in=[value for value, _ in ProgramAccreditation.STATUS if value not in ('approved', 'rejected')]
        ).distinct().order_by('program_name')
        return Response([{
            'id': programme.pk,
            'program_name': programme.program_name,
            'program_level': programme.program_level,
            'accreditation_date': programme.accreditation_date.isoformat(),
            'expiry_date': programme.expiry_date.isoformat(),
        } for programme in programmes])

    
    
    # def create(self, request):
    #     '''Set institution to the logged in user's institution'''
    #     serializer = self.serializer_class(data=request.data)
        
    #     if serializer.is_valid():
    #         user = self.request.user
    #         institution = Institution.objects.get(user=user)
    #         serializer.save(institution=institution)
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProgramAccessorViewset(viewsets.ModelViewSet):
    '''Program Accessor Viewset'''
    queryset = User.objects.filter(groups__name='Programme Assessors').order_by('username')
    serializer_class = UserReviewerSerializer
    pagination_class = None
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username','email','first_name','last_name','other_names']


class ProgrammeReviewersViewset(viewsets.ReadOnlyModelViewSet):
    '''Programme Accreditation Reviewers'''
    queryset = User.objects.filter(groups__name='Programme Reviewers').order_by('username')
    serializer_class = UserReviewerSerializer
    pagination_class = None
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username','email','first_name','last_name','other_names']


class PreminaryReviewViewset(viewsets.ModelViewSet):
    '''Preliminary Review Viewset'''
    queryset = PreliminaryReview.objects.all()
    serializer_class = PreliminaryReviewSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application__application_number','reviewer__username','comments','application__status']

    def get_queryset(self):
        '''return preliminary reviews for the logged in reviewer'''
        queryset = self.queryset
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists() or self.request.user.groups.filter(name='Head Programme Accreditation').exists():
            data = queryset
        else:
            data = queryset.filter(reviewer=self.request.user)
        return data

    def create(self, request):
        '''Create or update preliminary review for an application by a reviewer'''
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            reviewer = self.request.user  
            application = serializer.validated_data['application']          
            # update application status based on review comments
            if application.status == 'under_review':
                if 'expert_progression' in serializer.validated_data:
                    application.status = 'reviewed'
                    application.save()
            serializer.save(reviewer=reviewer)
            # TODO: send email notifications to applicants and reviewers based on the review outcome
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProgrammeAssessmentViewset(viewsets.ModelViewSet):
    '''Programme Assessment Viewset'''
    queryset = ProgrammeAssessment.objects.all()
    serializer_class = ProgrammeAssessmentSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application__application_number','assessor__username','comments']

    def get_queryset(self):
        '''return assessments for the logged in assessor'''
        queryset = self.queryset
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists() or self.request.user.groups.filter(name='Head Programme Accreditation').exists():
            data = queryset
        else:
            data = queryset.filter(assessor=self.request.user)
        return data
    
    def create(self, request):
        '''Create or update preliminary review for an application by a reviewer'''
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            assessor = self.request.user  
            application = serializer.validated_data['application']          
            # update application status based on review comments
            if application.status == 'under_assessment':
                if 'recommendation' in serializer.validated_data:
                    recommendation = serializer.validated_data['recommendation']
                    if recommendation == 'accredit' or recommendation=='minor' or recommendation=='major':
                        application.status = 'progressed_to_director'
                    elif recommendation == 'reject':
                        application.status = 'returned_for_review'
                    application.save()
            serializer.save(assessor = assessor)
            # TODO: send email notifications to applicants and reviewers based on the review outcome
            return Response(serializer.data, status=status.HTTP_200_OK)
        

class ProgrammeInvoiceViewset(viewsets.ModelViewSet):
    '''Programme Invoice Viewset'''
    queryset = ProgrammeInvoice.objects.all()
    serializer_class = ProgrammeInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['application__application_number','invoice_number','application__institution__name','status','payment_reference']

    def get_queryset(self):
        """Limit invoice visibility to owner institution for non-privileged users."""
        queryset = self.queryset.select_related('application', 'application__institution')

        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
            or can_manage_review_invoices(self.request.user)
        ):
            return queryset.order_by('-invoice_date')

        if hasattr(self.request.user, 'institution'):
            return queryset.filter(
                application__institution=self.request.user.institution
            ).order_by('-invoice_date')

        return queryset.none()
    
    

    def _generate_invoice_pdf(self, invoice):
        """Generate a simple invoice PDF and return its bytes."""
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 50
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "NCHE Programme Invoice")

        y -= 30
        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Invoice Number: {invoice.invoice_number or '-'}")
        y -= 16
        pdf.drawString(50, y, f"Invoice Date: {invoice.invoice_date or '-'}")
        y -= 16
        pdf.drawString(50, y, f"Application Number: {invoice.application.application_number if invoice.application else '-'}")
        y -= 16
        pdf.drawString(50, y, f"Institution: {invoice.application.institution.name if invoice.application and invoice.application.institution else '-'}")
        y -= 24

        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, y, "Invoice Items")
        y -= 18

        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, "Item")
        pdf.drawString(280, y, "Persons")
        pdf.drawString(360, y, "Days")
        pdf.drawString(430, y, "Total (UGX)")
        y -= 12
        pdf.line(50, y, width - 50, y)
        y -= 14

        pdf.setFont("Helvetica", 10)
        items = invoice.items.select_related("item_type").all()
        for item in items:
            if y < 70:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 10)

            pdf.drawString(50, y, str(item.item_type.name if item.item_type else "-"))
            pdf.drawString(280, y, str(item.persons_number))
            pdf.drawString(360, y, str(item.number_of_days))
            pdf.drawRightString(width - 50, y, f"{item.total:,.2f}")
            y -= 16

        y -= 6
        pdf.line(50, y, width - 50, y)
        y -= 20
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(50, y, "Grand Total (UGX):")
        pdf.drawRightString(width - 50, y, f"{invoice.grand_total:,.2f}")

        pdf.showPage()
        pdf.save()
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _notify_head_programme_accreditation(self, invoice, subject, intro_message):
        """Send invoice workflow notification to Head Programme Accreditation users."""
        recipients = list(
            User.objects.filter(groups__name='Head Programme Accreditation')
            .exclude(email__isnull=True)
            .exclude(email__exact='')
            .values_list('email', flat=True)
            .distinct()
        )

        if not recipients:
            return

        application = invoice.application
        institution = application.institution if application else None

        html_message = """
                            <div style=\"font-family: Arial, sans-serif; line-height: 1.6;\">
                                <p>{intro_message}</p>
                                <ul>
                                    <li><strong>Invoice Number:</strong> {invoice_number}</li>
                                    <li><strong>Application Number:</strong> {application_number}</li>
                                    <li><strong>Institution:</strong> {institution_name}</li>
                                    <li><strong>Programme:</strong> {programme_name}</li>
                                    <li><strong>Status:</strong> {status}</li>
                                    <li><strong>Payment Reference:</strong> {payment_reference}</li>
                                    <li><strong>Grand Total (UGX):</strong> {grand_total}</li>
                                </ul>
                            </div>
            """.format(
            intro_message=intro_message,
            invoice_number=invoice.invoice_number or '-',
            application_number=application.application_number if application else '-',
            institution_name=institution.name if institution else '-',
            programme_name=application.program_name if application else '-',
            status=invoice.status,
            payment_reference=invoice.payment_reference or '-',
            grand_total=f"{invoice.grand_total:,.2f}",
        )

        email = EmailMessage(
            subject=subject,
            body=html_message,
            to=recipients,
        )
        email.content_subtype = 'html'
        email.send(fail_silently=True)

    def create(self, request):
        """Create invoice, notify institution, and attach generated invoice PDF."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            invoice = serializer.save(status='issued', cleared=False)
            application = invoice.application
            if application.status != 'invoiced':
                application.status = 'invoiced'
                application.save(update_fields=['status'])

            institution = application.institution if application else None
            recipient = (
                institution.user.email
                if institution and hasattr(institution, 'user') and institution.user
                else None
            )

            if recipient:
                html_message = render_to_string('email/invoice_details.html', {
                    'application': application,
                    'institution': institution,
                    'invoice_amount': f"{invoice.grand_total:,.2f}",
                    'invoice_number': invoice.invoice_number,
                    'invoice_date': invoice.invoice_date,
                })

                email = EmailMessage(
                    subject='NCHE Programme Accreditation Invoice Details',
                    body=html_message,
                    to=[recipient],
                )
                email.content_subtype = 'html'

                pdf_bytes = self._generate_invoice_pdf(invoice)
                filename = f"{(invoice.invoice_number or 'invoice').replace('/', '-')}.pdf"
                email.attach(filename, pdf_bytes, 'application/pdf')
                email.send(fail_silently=False)

        response_serializer = self.get_serializer(invoice)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


    # Reconcile invoice
    @action(detail=True, methods=['post'], url_path='reconcile-invoice')
    @transaction.atomic
    def reconcile_invoice(self, request, pk=None):
        """
        POST reconcile an invoice for an application.
        """
        if not can_manage_review_invoices(request.user):
            raise PermissionDenied('Only accounts staff can reconcile programme invoices.')
        invoice = get_object_or_404(
            ProgrammeInvoice.objects.select_for_update(), pk=pk, status='paid', cleared=False,
        )
        if not invoice.payment_reference or not invoice.payment_receipt:
            raise ValidationError('A payment reference and receipt are required before reconciliation.')
        invoice.cleared = True
        invoice.status = 'reconciled'
        invoice.save()
        invoice_application = invoice.application
        invoice_application.status = 'invoice_reconciled'
        invoice_application.is_paid = True
        invoice_application.save(update_fields=['status', 'is_paid'])
        self._notify_head_programme_accreditation(
            invoice,
            subject='NCHE Programme Invoice Reconciled',
            intro_message='An invoice has been reconciled and the related application is ready for the next stage.',
        )
        return Response({'message': 'Invoice reconciled successfully.'}, status=status.HTTP_200_OK)
        
    # add payment receipt and payment reference and send email to notify head of programmes accreditation
    @action(detail=True, methods=['post'], url_path='add-payment-details')
    def add_payment_details(self, request, pk=None):
        """
        POST add payment details to an invoice.
        """
        invoice = get_object_or_404(ProgrammeInvoice, pk=pk, status='issued', cleared=False)
        if getattr(request.user, 'institution', None) != invoice.application.institution:
            raise PermissionDenied('Only the applicant institution can submit payment details.')
        payment_reference = request.data.get('payment_reference')
        payment_receipt = request.data.get('payment_receipt')

        if not payment_reference or not payment_receipt:
            return Response({'error': 'Payment reference and receipt are required.'}, status=status.HTTP_400_BAD_REQUEST)

        invoice.payment_reference = payment_reference
        invoice.payment_receipt = payment_receipt
        invoice.status = 'paid'
        invoice.save()
        self._notify_head_programme_accreditation(
            invoice,
            subject='NCHE Programme Invoice Payment Submitted',
            intro_message='Payment details have been added to an invoice and are ready for reconciliation review.',
        )
        
        return Response({'message': 'Payment details added successfully.'}, status=status.HTTP_200_OK)


class InvoiceTypeViewset(viewsets.ModelViewSet):
    '''Invoice Item Type Viewset'''
    queryset = InvoiceItemType.objects.filter(is_active=True).order_by('name')
    serializer_class = InvoiceItemTypeSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name','default_rate']
    pagination_class = None
