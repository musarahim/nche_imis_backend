from accounts.models import User
from accounts.serializers import UserReviewerSerializer
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.utils import timezone
from institutions.models import Institution
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (PreliminaryReview, Program, ProgramAccreditation,
                     ProgrammeAssessment)
from .serializers import (PreliminaryReviewSerializer,
                          ProgrammeAccreditationSerializer,
                          ProgrammeAssessmentSerializer, ProgramSerializer,
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

    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        if (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name='System Administrator').exists()
            or self.request.user.groups.filter(name='Head Programme Accreditation').exists()
        ):
            return queryset.select_related('institution').order_by('institution__name', '-date_submitted')

        if hasattr(self.request.user, 'institution'):
            return queryset.filter(institution=self.request.user.institution)

        return queryset.none()

    def retrieve(self, request,pk=None):
        '''retrieve a programme accreditation application'''
        queryset = ProgramAccreditation.objects.all()
        application = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(application)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
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

    @action(detail=False, methods=['post'], url_path='assign-reviewer')
    def assign_reviewer(self, request, pk=None):
        '''assign multiple applications to a reviewer
            applications come as a list of application ids and reviewer is the user id of the reviewer'''
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
        application_ids = request.data.get('applications', [])
        assessor_id = request.data.get('userId')
        
        if not application_ids or not assessor_id:
            return Response({'error': 'applications and userId are required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assessor = User.objects.get(id=assessor_id)
        except User.DoesNotExist:
            return Response({'error': 'Assessor not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        applications = ProgramAccreditation.objects.filter(id__in=application_ids)
        
        for application in applications:
            application.assessor=assessor
            if application.status != 'under_assessment':
                application.status = 'under_assessment'
                application.save()
        #TODO: send emails to assessors
        
        return Response({'message': f'{len(applications)} applications assigned to assessor {assessor.username}.'}, status=status.HTTP_200_OK)
    
    
    @action(detail=False, methods=['get'], url_path='ready-for-assessment')
    def ready_for_assessment(self, request, pk=None):
        """
        applications ready for assessment.
        """
        queryset = ProgramAccreditation.objects.filter(status='progressed_to_experts', preliminary_reviewers__expert_progression='yes')

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
        application.save()
        # TODO: send email notification to management and department head about the director's comment and application status

        return Response({'message': 'Director comment added successfully.'}, status=status.HTTP_200_OK)
    
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
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = self.request.user
            institution = Institution.objects.get(user=user)
            serializer.save(institution=institution)
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


class ProgramViewset(viewsets.ModelViewSet):
    '''University programs'''
    queryset = Program.objects.all()
    serializer_class = ProgramSerializer
    permissions_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['program_name','program_level','accreditation_date','expiry_date']
    parsers_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser] 

    def get_queryset(self):
        '''return documents for the logged in institution'''
        queryset = self.queryset
        if self.request.user.is_superuser or self.request.user.groups.filter(name='System Administrator').exists() or self.request.user.groups.filter(name='Head Programme Accreditation').exists():
            data = queryset
        else:
            if hasattr(self.request.user, 'institution'):
                data = queryset.filter(program_accreditation__institution=self.request.user.institution)
            else:
                data = None
        return data

    
    
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
    search_fields = ['application__application_number','reviewer__username','comments']

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
                    recommendation = serializer.validated_data['expert_progression']
                    if recommendation == 'yes':
                        application.status = 'progressed_to_experts'
                    elif recommendation == 'no':
                        application.status = 'returned_for_review'
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