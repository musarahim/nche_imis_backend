"""Shared, type-scoped reviewer assignment for institution licensing."""
import logging

from accounts.models import User
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

logger = logging.getLogger(__name__)

REVIEW_PERMISSIONS = (
    'can_review_institutional_licensing', 'can_review_application',
    'can_review_provisional_license_application', 'can_review_charter_application',
    'can_review_oti_provisional_application', 'can_review_classification_application',
)
ASSIGNER_GROUPS = ('System Administrator', 'Head of Department(ILA)', 'Director QA')


def eligible_reviewers(review_permission=None):
    """Reviewer eligibility requires active ILA membership, regardless of permissions."""
    return User.objects.filter(
        is_active=True, groups__name='ILA Desk Review Officer',
    ).distinct().order_by('username')


def reviewers_with_workload(review_permission=None):
    from .models import CertificationAndClassification, CharterApplication, IntrimAuthority, OTIProvisional, UniversityProvisionalLicense

    total = Value(0, output_field=IntegerField())
    # University and ODAI share tables: count each application once.
    for model in [IntrimAuthority, UniversityProvisionalLicense, CharterApplication, OTIProvisional, CertificationAndClassification]:
        pending = model.objects.filter(desk_reviewer_id=OuterRef('pk'), status='prelim_review').values('desk_reviewer_id').annotate(
            total=Count('pk'),
        ).values('total')
        total = total + Coalesce(Subquery(pending, output_field=IntegerField()), Value(0))
    return eligible_reviewers(review_permission).annotate(assigned_application_count=total)


class AssignmentInputSerializer(serializers.Serializer):
    userId = serializers.IntegerField(min_value=1)
    applications = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

    def validate_applications(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError('An application cannot be selected twice.')
        return value


class LicensingReviewMixin:
    assignment_permission = ''
    review_permission = ''
    institution_field = 'institution'
    code_field = 'application_code'
    review_portal_path = ''

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.action in ['update', 'partial_update', 'destroy'] or (self.action == 'promoters' and request.method == 'POST'):
            application = self.get_object()
            institution = getattr(application, self.institution_field)
            if not institution or institution.user_id != request.user.pk:
                raise PermissionDenied('Only the applicant can edit application information.')
            if application.status != 'draft':
                raise PermissionDenied('Submitted application information is locked; record processing evidence through the workflow.')
            if request.data.get('status', 'draft') not in ['draft', 'submitted']:
                raise ValidationError({'status': 'Use the backoffice workflow to change processing status.'})

    def can_assign_reviews(self):
        user = self.request.user
        return user.is_authenticated and user.is_active and (
            user.is_superuser or user.groups.filter(name__in=ASSIGNER_GROUPS).exists() or
            user.has_perm('license.can_assign_reviewers') or
            user.has_perm('license.' + self.assignment_permission)
        )

    def review_queryset(self):
        queryset = self.queryset.all()
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none()
        from .processing import can_process
        if self.action in ['processing', 'processing_queue', 'application_status'] and can_process(user):
            return queryset
        if self.can_assign_reviews():
            return queryset
        scope = Q(pk__in=[])
        if hasattr(user, 'institution'):
            scope |= Q(**{self.institution_field: user.institution})
        if eligible_reviewers(self.review_permission).filter(pk=user.pk).exists():
            scope |= Q(desk_reviewer=user)
        return queryset.filter(scope)

    def _review_queue(self, queryset):
        from .status_tracking import status_summary
        can_review = eligible_reviewers().filter(pk=self.request.user.pk).exists()
        institution = self.request.query_params.get('institution')
        if institution:
            institution_id = serializers.IntegerField(min_value=1).run_validation(institution)
            queryset = queryset.filter(**{self.institution_field + '_id': institution_id})
        application_status = self.request.query_params.get('status')
        if application_status:
            if application_status not in ['submitted', 'prelim_review']:
                raise ValidationError({'status': 'Select a valid assignment status.'})
            queryset = queryset.filter(status=application_status)
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(**{self.code_field + '__icontains': search}) |
                Q(**{self.institution_field + '__name__icontains': search}) |
                Q(desk_reviewer__username__icontains=search)
            )
        queryset = queryset.select_related(self.institution_field, 'desk_reviewer').order_by('-id')
        page = self.paginate_queryset(queryset)
        applications = page if page is not None else queryset
        rows = []
        for application in applications:
            institution = getattr(application, self.institution_field)
            reviewer = application.desk_reviewer
            rows.append({
                'id': application.pk,
                'application_code': getattr(application, self.code_field),
                'institution': institution.name if institution else '',
                'institution_id': institution.pk if institution else None,
                'application_date': application.application_date,
                'status': status_summary(application)['status'],
                'status_code': application.status,
                'desk_reviewer': reviewer.pk if reviewer else None,
                'desk_reviewer_name': self._reviewer_name(reviewer) if reviewer else None,
                'can_open_review': bool(self.can_assign_reviews() or (can_review and reviewer and reviewer.pk == self.request.user.pk)),
            })
        if page is not None:
            response = self.get_paginated_response(rows)
            response.data['can_assign'] = bool(self.can_assign_reviews())
            return response
        return Response({'count': len(rows), 'next': None, 'previous': None,
                         'results': rows, 'can_assign': bool(self.can_assign_reviews())})

    @action(detail=False, methods=['get'], url_path='submitted-applications')
    def submitted_applications(self, request):
        return self._review_queue(self.get_queryset().filter(status='submitted'))

    @action(detail=False, methods=['get'], url_path='under-review')
    def under_review(self, request):
        status = 'prelim_feedback' if request.query_params.get('review_status') == 'completed' else 'prelim_review'
        return self._review_queue(self.get_queryset().filter(status=status))

    @action(detail=True, methods=['get', 'post'], url_path='preliminary-review')
    def preliminary_review(self, request, pk=None):
        from .preliminary_review import preliminary_review
        return preliminary_review(self, request, pk)

    @action(detail=True, methods=['get'], url_path='application-status')
    def application_status(self, request, pk=None):
        from .status_tracking import tracking_response
        return Response(tracking_response(self.get_object()))

    @action(detail=True, methods=['get', 'post'], url_path='processing')
    def processing(self, request, pk=None):
        from .processing import processing
        return processing(self, request, pk)

    @action(detail=False, methods=['get'], url_path='processing-queue')
    def processing_queue(self, request):
        from .processing import can_process, family
        from .models import LicensingProcessing
        from .preliminary_review import review_type
        family(self)
        if not (can_process(request.user) or self.can_assign_reviews()):
            raise PermissionDenied('Licensing processing access is required.')
        states = {row.application_id: row for row in LicensingProcessing.objects.filter(application_type=review_type(self))}
        queryset = self.get_queryset().filter(Q(status__in=['submitted', 'prelim_review', 'prelim_feedback']) | Q(pk__in=states))
        queues = {
            'all': [],
            'preliminary': ['awaiting_preliminary', 'preliminary_feedback', 'clarification'],
            'vetting': ['vetting', 'vetting_report'],
            'council': ['council_decision', 'final_council', 'hearing', 'hearing_decision'],
            'verification': ['verification_invoice', 'verification_appointment', 'verification', 'verification_report'],
            'external': ['attorney_general', 'minister', 'president'],
            'publication': ['publication_pending'],
            'completed': ['issued', 'refused', 'deferred'],
        }
        queue = request.query_params.get('queue', 'all')
        if queue not in queues:
            raise ValidationError({'queue': 'Select a valid processing queue.'})
        if queue != 'all':
            selected = Q(pk__in=[pk for pk, state in states.items() if state.stage in queues[queue]])
            if queue == 'preliminary':
                selected |= Q(status__in=['submitted', 'prelim_review', 'prelim_feedback'])
            queryset = queryset.filter(selected)
        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(Q(**{self.code_field + '__icontains': search}) | Q(**{self.institution_field + '__name__icontains': search}))
        ordering = request.query_params.get('ordering', '-id')
        order_fields = {'id': 'id', 'institution': self.institution_field + '__name',
                        'application_code': self.code_field, 'application_date': 'application_date'}
        if ordering.lstrip('-') not in order_fields:
            raise ValidationError({'ordering': 'Select a valid processing sort column.'})
        order_field = ('-' if ordering.startswith('-') else '') + order_fields[ordering.lstrip('-')]
        queryset = queryset.select_related(self.institution_field).order_by(order_field, '-pk')
        page = self.paginate_queryset(queryset)
        rows = [{'id': app.pk, 'application_code': getattr(app, self.code_field),
                 'institution': getattr(app, self.institution_field).name,
                 'application_date': app.application_date,
                 'stage': ('preliminary_feedback' if app.status == 'prelim_feedback' else states[app.pk].stage if app.pk in states else 'awaiting_preliminary')} for app in (page if page is not None else queryset)]
        return self.get_paginated_response(rows) if page is not None else Response({'results': rows, 'count': len(rows), 'next': None, 'previous': None})

    @action(detail=False, methods=['get'], url_path='assignment-candidates')
    def assignment_candidates(self, request):
        if not self.can_assign_reviews():
            raise PermissionDenied('You do not have permission to assign licensing reviewers.')
        return self._review_queue(self.get_queryset().filter(status__in=['submitted', 'prelim_review']))

    @action(detail=False, methods=['get'], url_path='assignment-filter-options')
    def assignment_filter_options(self, request):
        if not self.can_assign_reviews():
            raise PermissionDenied('You do not have permission to assign licensing reviewers.')
        field = self.institution_field
        institutions = self.get_queryset().filter(
            status__in=['submitted', 'prelim_review'], **{field + '__isnull': False},
        ).values(field + '__id', field + '__name').order_by(field + '__name', field + '__id').distinct()
        return Response({
            'institutions': [{'id': row[field + '__id'], 'name': row[field + '__name']} for row in institutions],
            'statuses': [{'value': 'submitted', 'label': 'Submitted'},
                         {'value': 'prelim_review', 'label': 'Under Preliminary Review'}],
        })

    @action(detail=False, methods=['post'], url_path='assign-desk-reviewer')
    def assign_reviewer(self, request):
        if not self.can_assign_reviews():
            raise PermissionDenied('You do not have permission to assign licensing reviewers.')
        payload = AssignmentInputSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        ids = payload.validated_data['applications']
        reviewer = eligible_reviewers(self.review_permission).filter(pk=payload.validated_data['userId']).first()
        if reviewer is None:
            raise ValidationError({'userId': 'Select an active member of the ILA Desk Review Officer group.'})
        with transaction.atomic():
            applications = list(self.get_queryset().select_for_update().filter(pk__in=ids))
            if len(applications) != len(ids):
                raise ValidationError({'applications': 'Some applications do not belong to this licensing type or are unavailable.'})
            if any(application.status not in ['submitted', 'prelim_review'] for application in applications):
                raise ValidationError({'applications': 'Only submitted applications or applications under preliminary review can be assigned.'})
            changed = []
            for application in applications:
                if application.desk_reviewer_id == reviewer.pk and application.status == 'prelim_review':
                    continue
                application.desk_reviewer = reviewer
                application.status = 'prelim_review'
                application.save(update_fields=['desk_reviewer', 'status'])
                changed.append(getattr(application, self.code_field))
            if changed:
                transaction.on_commit(lambda: self._notify_reviewer(reviewer, changed))
        return Response({'message': f'{len(applications)} application(s) assigned to {self._reviewer_name(reviewer)}.',
                         'assigned_count': len(applications), 'changed_count': len(changed)})

    @staticmethod
    def _reviewer_name(user):
        return ' '.join(part for part in [user.first_name, user.last_name] if part) or user.username

    def _notify_reviewer(self, reviewer, codes):
        portal = getattr(settings, 'STAFF_PORTAL_URL', 'https://portal.unche.or.ug').rstrip('/')
        try:
            EmailMessage(
                subject='Institution Licensing — Reviewer Assignment',
                body='You have been assigned the following licensing applications:\n' +
                     '\n'.join(codes) + '\n\nOpen your review queue: ' + portal + self.review_portal_path + '/under-review',
                to=[reviewer.email],
            ).send(fail_silently=False)
        except Exception:
            # A notification failure must not invalidate an already committed assignment.
            logger.exception('Could not notify licensing reviewer %s', reviewer.pk)
