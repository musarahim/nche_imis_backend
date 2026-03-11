from accounts.models import User
from accounts.serializers import UserReviewerSerializer
from django.shortcuts import get_object_or_404, render
from institutions.models import Institution
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (PreliminaryReview, Program, ProgramAccessor,
                     ProgramAccreditation)
from .serializers import (PreliminaryReviewSerializer,
                          ProgramAccessorSerializer,
                          ProgrammeAccreditationSerializer, ProgramSerializer)


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
        serializer = self.serializer_class(application)
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
    

    def create(self, request):
        '''Set institution to the logged in user's institution'''
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            user = self.request.user
            institution = Institution.objects.get(user=user)
            serializer.save(institution=institution)
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
    queryset = ProgramAccessor.objects.order_by('-assigned_at').all()
    serializer_class = ProgramAccessorSerializer
    permissions_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['user__username','program_accreditation__application_number','group_leader']
    parsers_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser] 


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
            application_id = serializer.validated_data['application'].id
            
            # Check if a review already exists for this reviewer and application
            review, created = PreliminaryReview.objects.update_or_create(
                reviewer=reviewer,
                application_id=application_id,
                defaults={
                    'type_of_entry_summary': serializer.validated_data['type_of_entry_summary'],
                    'type_of_entry_comments': serializer.validated_data.get('type_of_entry_comments', '')
                }
            )
            
            return Response(self.serializer_class(review).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





