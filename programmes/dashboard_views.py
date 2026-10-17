"""Read-only programme accreditation dashboard for the programme head."""
from django.db.models import Count, Exists, Max, OuterRef, Q, Subquery
from django.utils import timezone
from rest_framework import filters, mixins, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from common.pagination import StandardResultsSetPagination
from .models import DeskReviewInvoiceLine, PreliminaryReview, ProgramAccreditation, ProgrammeAssessment, ProgrammeAssessmentInvoice


class CanViewProgrammeHeadDashboard(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (
            user.is_superuser or user.groups.filter(name__in=[
                'Head Programme Accreditation', 'System Administrator',
            ]).exists()
        ))


class DashboardPagination(StandardResultsSetPagination):
    page_size = 25
    max_page_size = 250


class DashboardOrderingFilter(filters.OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)
        # Keep pagination and multi-page exports stable when sort values repeat.
        return ordering if any(field.lstrip('-') == 'pk' for field in ordering) else [*ordering, 'pk']


class DashboardApplicationSerializer(serializers.ModelSerializer):
    institution = serializers.CharField(source='institution.name', read_only=True)
    programme_category_label = serializers.CharField(source='get_programme_category_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    program_level = serializers.CharField(source='get_program_level_display', read_only=True)
    invoice_number = serializers.CharField(read_only=True, allow_null=True)
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = ProgramAccreditation
        fields = ('id', 'application_number', 'programme_name', 'institution', 'institution_id',
            'date_submitted', 'programme_category', 'programme_category_label', 'program_level',
            'status', 'status_label', 'invoice_number', 'payment_status')

    def get_payment_status(self, instance):
        if not instance.invoice_status:
            return 'Not invoiced'
        if instance.invoice_status == 'draft':
            return 'Draft invoice'
        if instance.invoice_status == 'issued':
            return 'Awaiting payment'
        if (instance.invoice_status == 'reconciled' and instance.invoice_cleared
                and instance.invoice_verified >= instance.invoice_total):
            return 'Fully verified'
        if instance.invoice_verified and instance.invoice_verified > 0:
            return 'Partially verified'
        return 'Awaiting verification'


class ProgrammeHeadDashboardViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, CanViewProgrammeHeadDashboard]
    serializer_class = DashboardApplicationSerializer
    pagination_class = DashboardPagination
    filter_backends = [filters.SearchFilter, DashboardOrderingFilter]
    search_fields = ['application_number', 'programme_name', 'institution__name']
    ordering_fields = ['programme_name', 'institution__name', 'date_submitted', 'programme_category', 'status']
    ordering = ['-date_submitted', '-pk']

    def get_queryset(self):
        queryset = ProgramAccreditation.objects.select_related('institution')
        institution = self.request.query_params.get('institution')
        category = self.request.query_params.get('programme_category')
        stage = self.request.query_params.get('status')
        if institution:
            try:
                institution_id = int(institution)
                if institution_id <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                raise ValidationError({'institution': 'Select a valid institution.'})
            queryset = queryset.filter(institution_id=institution_id)
        if category:
            if category == 'unspecified':
                queryset = queryset.filter(Q(programme_category__isnull=True) | Q(programme_category=''))
            elif category in dict(ProgramAccreditation.CATEGORY):
                queryset = queryset.filter(programme_category=category)
            else:
                raise ValidationError({'programme_category': 'Select a valid programme category.'})
        if stage:
            if stage not in dict(ProgramAccreditation.STATUS):
                raise ValidationError({'status': 'Select a valid workflow stage.'})
            queryset = queryset.filter(status=stage)
        latest_invoice = DeskReviewInvoiceLine.objects.filter(application_id=OuterRef('pk')).exclude(
            invoice__status='cancelled',
        ).order_by('-invoice_id')
        return queryset.annotate(**{
            name: Subquery(latest_invoice.values(field)[:1]) for name, field in {
                'invoice_number': 'invoice__invoice_number', 'invoice_status': 'invoice__status',
                'invoice_cleared': 'invoice__cleared', 'invoice_verified': 'invoice__verified_amount',
                'invoice_total': 'invoice__grand_total',
            }.items()
        })

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        reviewed = PreliminaryReview.objects.filter(application_id=OuterRef('pk'))
        queryset = ProgramAccreditation.objects.annotate(has_review=Exists(reviewed))
        totals = queryset.aggregate(
            applications=Count('pk'), institutions=Count('institution_id', distinct=True),
            reviewed=Count('pk', filter=Q(has_review=True)),
            stem=Count('pk', filter=Q(programme_category='stem')),
            humanities=Count('pk', filter=Q(programme_category='humanities')),
            latest_submission=Max('date_submitted'),
        )
        totals['unspecified'] = totals['applications'] - totals['stem'] - totals['humanities']
        # Reuse the assignment gate so dashboard readiness cannot disagree with assignment.
        from .views import ProgrammeAccreditationViewset
        totals['ready_for_assessment'] = ProgrammeAccreditationViewset._ready_for_assessment_queryset().count()
        totals['payment_verification'] = ProgrammeAssessmentInvoice.objects.filter(status='paid', cleared=False).count()
        stages = dict(ProgramAccreditation.objects.order_by().values('status').annotate(count=Count('pk')).values_list('status', 'count'))
        top = queryset.values('institution_id', 'institution__name').annotate(
            applications=Count('pk'), reviewed=Count('pk', filter=Q(has_review=True)),
        ).order_by('-applications', 'institution__name', 'institution_id')[:10]
        return Response({
            'totals': totals,
            'stages': [{'value': value, 'label': label, 'count': stages.get(value, 0)} for value, label in ProgramAccreditation.STATUS],
            'top_institutions': [{'id': row['institution_id'], 'name': row['institution__name'],
                'applications': row['applications'], 'reviewed': row['reviewed']} for row in top],
            'generated_at': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        institutions = ProgramAccreditation.objects.order_by('institution__name', 'institution_id').values(
            'institution_id', 'institution__name',
        ).distinct()
        return Response({
            'institutions': [{'id': row['institution_id'], 'name': row['institution__name']} for row in institutions],
            'programme_categories': [{'value': value, 'label': label} for value, label in ProgramAccreditation.CATEGORY]
                + [{'value': 'unspecified', 'label': 'Not specified'}],
            'statuses': [{'value': value, 'label': label} for value, label in ProgramAccreditation.STATUS],
        })


class CanViewReviewerDashboard(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Programme Reviewers').exists()


class ReviewerDashboardApplicationSerializer(serializers.ModelSerializer):
    institution = serializers.CharField(source='institution.name', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    has_review = serializers.BooleanField(read_only=True)
    review_pending = serializers.BooleanField(read_only=True)
    reviewed_at = serializers.DateTimeField(read_only=True, allow_null=True)

    class Meta:
        model = ProgramAccreditation
        fields = ('id', 'application_number', 'programme_name', 'institution', 'date_submitted',
                  'status', 'status_label', 'has_review', 'review_pending', 'reviewed_at')


class PreliminaryReviewerDashboardViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, CanViewReviewerDashboard]
    serializer_class = ReviewerDashboardApplicationSerializer
    pagination_class = DashboardPagination
    filter_backends = [filters.SearchFilter, DashboardOrderingFilter]
    search_fields = ['application_number', 'programme_name', 'institution__name']
    ordering_fields = ['date_submitted', 'programme_name']
    ordering = ['date_submitted', 'pk']

    def assigned_applications(self):
        from django.db.models import BooleanField, Case, Value, When
        reviews = PreliminaryReview.objects.filter(application_id=OuterRef('pk'), reviewer=self.request.user)
        return ProgramAccreditation.objects.filter(preliminary_reviewer=self.request.user).select_related(
            'institution',
        ).annotate(
            has_review=Exists(reviews),
            reviewed_at=Subquery(reviews.order_by('-reviewed_at', '-pk').values('reviewed_at')[:1]),
        ).annotate(review_pending=Case(
            When(Q(has_review=False) | Q(status__in=['under_review', 'returned_for_review']), then=Value(True)),
            default=Value(False), output_field=BooleanField(),
        ))

    def get_queryset(self):
        queryset = self.assigned_applications()
        queue = self.request.query_params.get('queue', 'all')
        if queue not in ['all', 'pending', 'completed']:
            raise ValidationError({'queue': 'Select all, pending or completed.'})
        if queue != 'all':
            queryset = queryset.filter(review_pending=queue == 'pending')
        return queryset

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        queryset = self.assigned_applications()
        totals = queryset.aggregate(
            assigned=Count('pk'), pending=Count('pk', filter=Q(review_pending=True)),
            completed=Count('pk', filter=Q(review_pending=False)),
            institutions=Count('institution_id', distinct=True),
        )
        stages = queryset.order_by().values('status').annotate(count=Count('pk'))
        labels = dict(ProgramAccreditation.STATUS)
        return Response({'totals': totals, 'stages': [
            {'value': row['status'], 'label': labels.get(row['status'], row['status']), 'count': row['count']}
            for row in stages
        ]})


class CanViewAssessorDashboard(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Programme Assessors').exists()


class AssessorDashboardApplicationSerializer(serializers.ModelSerializer):
    institution = serializers.CharField(source='institution.name', read_only=True)
    has_assessment = serializers.BooleanField(read_only=True)
    assessment_pending = serializers.BooleanField(read_only=True)
    assessment_date = serializers.DateField(read_only=True, allow_null=True)

    class Meta:
        model = ProgramAccreditation
        fields = ('id', 'application_number', 'programme_name', 'institution', 'date_submitted',
                  'has_assessment', 'assessment_pending', 'assessment_date')


class ProgrammeAssessorDashboardViewset(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated, CanViewAssessorDashboard]
    serializer_class = AssessorDashboardApplicationSerializer
    pagination_class = DashboardPagination
    filter_backends = [filters.SearchFilter, DashboardOrderingFilter]
    search_fields = ['application_number', 'programme_name', 'institution__name']
    ordering_fields = ['date_submitted', 'programme_name']
    ordering = ['date_submitted', 'pk']

    def assigned_applications(self):
        from django.db.models import BooleanField, Case, Value, When
        assessments = ProgrammeAssessment.objects.filter(application_id=OuterRef('pk'), assessor=self.request.user)
        return ProgramAccreditation.objects.filter(assessor=self.request.user).select_related(
            'institution',
        ).annotate(
            has_assessment=Exists(assessments),
            assessment_date=Subquery(assessments.order_by('-assessment_date', '-pk').values('assessment_date')[:1]),
        ).annotate(assessment_pending=Case(
            When(Q(has_assessment=False) | Q(status__in=['under_assessment', 'return_to_assessor']), then=Value(True)),
            default=Value(False), output_field=BooleanField(),
        ))

    def get_queryset(self):
        queryset = self.assigned_applications()
        queue = self.request.query_params.get('queue', 'all')
        if queue not in ['all', 'pending', 'completed']:
            raise ValidationError({'queue': 'Select all, pending or completed.'})
        if queue != 'all':
            queryset = queryset.filter(assessment_pending=queue == 'pending')
        return queryset

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        queryset = self.assigned_applications()
        totals = queryset.aggregate(
            assigned=Count('pk'), pending=Count('pk', filter=Q(assessment_pending=True)),
            completed=Count('pk', filter=Q(assessment_pending=False)),
            institutions=Count('institution_id', distinct=True),
        )
        return Response({'totals': totals})
