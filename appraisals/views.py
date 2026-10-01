from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from hr.models import Employee
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import (AdditionalQualification, AppraisalComment,
                     AppraisalOutput, CompetencyRating, ImprovementArea,
                     InitialQualification, NextYearPerformancePlan,
                     PerformanceAppraisal, Training)
from .serializers import (AdditionalQualificationSerializer,
                          AppraisalCommentSerializer,
                          AppraisalOutputSerializer,
                          CompetencyRatingSerializer,
                          ImprovementAreaSerializer,
                          InitialQualificationSerializer,
                          NextYearPerformancePlanSerializer,
                          PerformanceAppraisalDetailSerializer,
                          PerformanceAppraisalSerializer, TrainingSerializer)


class PerformanceAppraisalViewSet(viewsets.ModelViewSet):
    queryset = PerformanceAppraisal.objects.all()
    serializer_class = PerformanceAppraisalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PerformanceAppraisalDetailSerializer
        return PerformanceAppraisalSerializer

    def _get_employee(self, request):
        """Return the Employee linked to the current user, or None."""
        return getattr(request.user, 'employee', None)

    def get_queryset(self):
        qs = PerformanceAppraisal.objects.all().select_related(
            'appraisee', 'appraiser', 'reviewer', 'director', 'executive_director'
        )
        if self.request.user.is_staff or self.request.user.has_perm('appraisals.can_approve_staff_appraisal'):
            return qs
        employee = self._get_employee(self.request)
        if not employee:
            return qs.none()
        return qs.filter(Q(appraisee=employee) | Q(appraiser=employee) | Q(reviewer=employee) |
                         Q(director=employee) | Q(executive_director=employee)).distinct()

    def _require_stage(self, request, appraisal, role, stage):
        employee = self._get_employee(request)
        if not employee or getattr(appraisal, role + '_id') != employee.pk:
            raise PermissionDenied('You are not assigned to this appraisal stage.')
        if appraisal.status != stage:
            raise ValidationError({'status': f'Expected {stage}; current status is {appraisal.status}.'})
        return employee

    def perform_update(self, serializer):
        appraisal = self.get_object()
        self._require_stage(self.request, appraisal, 'appraisee', 'draft')
        serializer.save()

    def perform_destroy(self, instance):
        self._require_stage(self.request, instance, 'appraisee', 'draft')
        instance.delete()

    # ── Appraisee: my appraisals ──────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='my-appraisals')
    def my_appraisals(self, request):
        employee = self._get_employee(request)
        if not employee:
            return Response([], status=status.HTTP_200_OK)
        qs = PerformanceAppraisal.objects.filter(appraisee=employee)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Appraiser: pending reviews ────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='appraiser-reviews')
    def appraiser_reviews(self, request):
        employee = self._get_employee(request)
        if not employee:
            return Response([], status=status.HTTP_200_OK)
        qs = PerformanceAppraisal.objects.filter(
            appraiser=employee,
            status='self_assessment'
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Reviewer: pending reviews ─────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='reviewer-reviews')
    def reviewer_reviews(self, request):
        employee = self._get_employee(request)
        if not employee:
            return Response([], status=status.HTTP_200_OK)
        qs = PerformanceAppraisal.objects.filter(
            reviewer=employee,
            status='appraiser_review'
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Director: pending reviews ─────────────────────────────────────────────
    @action(detail=False, methods=['get'], url_path='director-reviews')
    def director_reviews(self, request):
        employee = self._get_employee(request)
        if not employee:
            return Response([], status=status.HTTP_200_OK)
        qs = PerformanceAppraisal.objects.filter(
            director=employee,
            status='reviewer_review'
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Executive Director: pending reviews ──────────────────────────────────
    @action(detail=False, methods=['get'], url_path='executive-reviews')
    def executive_reviews(self, request):
        employee = self._get_employee(request)
        if not employee:
            return Response([], status=status.HTTP_200_OK)
        qs = PerformanceAppraisal.objects.filter(
            executive_director=employee,
            status='director_review'
        )
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    # ── Status transitions ─────────────────────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='submit-self-assessment')
    def submit_self_assessment(self, request, pk=None):
        appraisal = self.get_object()
        employee = self._require_stage(request, appraisal, 'appraisee', 'draft')
        outputs = list(appraisal.outputs.all())
        if not outputs or any(o.self_score is None for o in outputs):
            raise ValidationError({'outputs': 'Add at least one complete output and rate every output.'})
        if not appraisal.appraiser_id:
            raise ValidationError({'appraiser': 'A supervisor must be assigned before submission.'})
        if not appraisal.appraisee.employment_terms:
            raise ValidationError({'employment_terms': 'Complete the terms of employment in employee biodata.'})
        appraisal.status = 'self_assessment'
        appraisal.date_submitted = timezone.now()
        appraisal.save()
        # Save appraisee comment (Section F) if provided
        comment_text = request.data.get('comment', '')
        if comment_text and employee:
            AppraisalComment.objects.create(
                appraisal=appraisal,
                commenter=employee,
                commenter_role='appraisee',
                comment=comment_text,
            )
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    @action(detail=True, methods=['post'], url_path='submit-appraiser-review')
    def submit_appraiser_review(self, request, pk=None):
        appraisal = self.get_object()
        employee = self._require_stage(request, appraisal, 'appraiser', 'self_assessment')
        outputs = list(appraisal.outputs.all())
        competencies = list(appraisal.competencies.all())
        if not outputs or any(o.appraiser_score is None or o.agreed_score is None for o in outputs):
            raise ValidationError({'outputs': 'Rate and agree a score for every output.'})
        if {c.competency_number for c in competencies} != set(range(1, 11)):
            raise ValidationError({'competencies': 'Rate all 10 competencies.'})
        if not appraisal.reviewer_id:
            raise ValidationError({'reviewer': 'A reviewing officer must be assigned before submission.'})
        # Save supervisor remarks if provided
        supervisor_remarks = request.data.get('supervisor_remarks', '')
        if supervisor_remarks:
            appraisal.supervisor_remarks = supervisor_remarks

        # Recalculate scores
        agreed_scores = [o.agreed_score for o in outputs if o.agreed_score is not None]
        if agreed_scores:
            total = sum(agreed_scores)
            max_score = len(agreed_scores) * 5
            appraisal.output_total_score = total
            appraisal.output_average = total / len(agreed_scores)
            appraisal.output_weighted_score = round((total / max_score) * 70, 2)

        comp_scores = [c.score for c in competencies]
        if comp_scores:
            total_c = sum(comp_scores)
            max_c = len(comp_scores) * 5
            appraisal.competency_total_score = total_c
            appraisal.competency_average = total_c / len(comp_scores)
            appraisal.competency_weighted_score = round((total_c / max_c) * 30, 2)

        overall = float(appraisal.output_weighted_score) + float(appraisal.competency_weighted_score)
        appraisal.overall_score = round((overall / 100) * 5, 2)

        score = appraisal.overall_score
        if score < 2:
            appraisal.overall_level = 'Poor'
        elif score < 3:
            appraisal.overall_level = 'Fair'
        elif score < 4:
            appraisal.overall_level = 'Good'
        elif score < 5:
            appraisal.overall_level = 'Very Good'
        else:
            appraisal.overall_level = 'Excellent'

        appraisal.status = 'appraiser_review'
        appraisal.save()
        # Also save appraiser comment record (Section F)
        appraiser_comment = request.data.get('appraiser_comment', supervisor_remarks)
        if appraiser_comment and employee:
            AppraisalComment.objects.update_or_create(
                appraisal=appraisal,
                commenter=employee,
                commenter_role='appraiser',
                defaults={'comment': appraiser_comment},
            )
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    @action(detail=True, methods=['post'], url_path='submit-reviewer-comment')
    def submit_reviewer_comment(self, request, pk=None):
        appraisal = self.get_object()
        employee = self._require_stage(request, appraisal, 'reviewer', 'appraiser_review')
        if not appraisal.director_id:
            raise ValidationError({'director': 'A director must be assigned before submission.'})
        comment_text = request.data.get('comment', '')
        if comment_text and employee:
            AppraisalComment.objects.create(
                appraisal=appraisal,
                commenter=employee,
                commenter_role='reviewer',
                comment=comment_text,
            )
        appraisal.status = 'reviewer_review'
        appraisal.save()
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    @action(detail=True, methods=['post'], url_path='submit-director-comment')
    def submit_director_comment(self, request, pk=None):
        appraisal = self.get_object()
        employee = self._require_stage(request, appraisal, 'director', 'reviewer_review')
        if not appraisal.executive_director_id:
            raise ValidationError({'executive_director': 'An executive director must be assigned before submission.'})
        comment_text = request.data.get('comment', '')
        if comment_text and employee:
            AppraisalComment.objects.create(
                appraisal=appraisal,
                commenter=employee,
                commenter_role='director',
                comment=comment_text,
            )
        appraisal.status = 'director_review'
        appraisal.save()
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    @action(detail=True, methods=['post'], url_path='submit-executive-comment')
    def submit_executive_comment(self, request, pk=None):
        appraisal = self.get_object()
        employee = self._require_stage(request, appraisal, 'executive_director', 'director_review')
        comment_text = request.data.get('comment', '')
        if comment_text and employee:
            AppraisalComment.objects.create(
                appraisal=appraisal,
                commenter=employee,
                commenter_role='executive',
                comment=comment_text,
            )
        appraisal.status = 'completed'
        appraisal.save()
        return Response(PerformanceAppraisalSerializer(appraisal).data)

    def perform_create(self, serializer):
        employee = self._get_employee(self.request)
        if not employee:
            raise PermissionDenied('An employee profile is required to create an appraisal.')
        serializer.save(appraisee=employee, appraiser=employee.supervisor)


class StageProtectedViewSet(viewsets.ModelViewSet):
    """Child records may only be changed by the participant at the current stage."""
    stage_role = 'appraisee'
    stage_status = 'draft'

    def _check(self, appraisal):
        employee = getattr(self.request.user, 'employee', None)
        if not employee or getattr(appraisal, self.stage_role + '_id') != employee.pk:
            raise PermissionDenied('You are not assigned to edit this appraisal.')
        if appraisal.status != self.stage_status:
            raise ValidationError({'status': 'This appraisal is no longer editable at this stage.'})

    def perform_create(self, serializer):
        self._check(serializer.validated_data['appraisal'])
        serializer.save()

    def perform_update(self, serializer):
        self._check(serializer.instance.appraisal)
        if 'appraisal' in serializer.validated_data and serializer.validated_data['appraisal'] != serializer.instance.appraisal:
            raise ValidationError({'appraisal': 'Cannot move a record to another appraisal.'})
        serializer.save()

    def perform_destroy(self, instance):
        self._check(instance.appraisal)
        instance.delete()


class AppraisalOutputViewSet(StageProtectedViewSet):
    queryset = AppraisalOutput.objects.all()
    serializer_class = AppraisalOutputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        appraisal = serializer.instance.appraisal
        if 'appraisal' in serializer.validated_data and serializer.validated_data['appraisal'] != appraisal:
            raise ValidationError({'appraisal': 'Cannot move an output to another appraisal.'})
        employee = getattr(self.request.user, 'employee', None)
        fields = set(serializer.validated_data) - {'appraisal'}
        if employee and employee.pk == appraisal.appraisee_id and appraisal.status == 'draft':
            if fields & {'appraiser_score', 'agreed_score'}:
                raise PermissionDenied('The appraisee cannot set review scores.')
        elif employee and employee.pk == appraisal.appraiser_id and appraisal.status == 'self_assessment':
            if fields - {'appraiser_score', 'agreed_score', 'comments'}:
                raise PermissionDenied('The appraiser can only set review scores and comments.')
        else:
            raise PermissionDenied('You cannot edit this output at this stage.')
        serializer.save()


class CompetencyRatingViewSet(StageProtectedViewSet):
    queryset = CompetencyRating.objects.all()
    serializer_class = CompetencyRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    stage_role = 'appraiser'
    stage_status = 'self_assessment'


class ImprovementAreaViewSet(StageProtectedViewSet):
    queryset = ImprovementArea.objects.all()
    serializer_class = ImprovementAreaSerializer
    permission_classes = [permissions.IsAuthenticated]
    stage_role = 'appraiser'
    stage_status = 'self_assessment'


class NextYearPerformancePlanViewSet(StageProtectedViewSet):
    queryset = NextYearPerformancePlan.objects.all()
    serializer_class = NextYearPerformancePlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    stage_role = 'appraiser'
    stage_status = 'self_assessment'


class InitialQualificationViewSet(StageProtectedViewSet):
    queryset = InitialQualification.objects.all()
    serializer_class = InitialQualificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class AdditionalQualificationViewSet(StageProtectedViewSet):
    queryset = AdditionalQualification.objects.all()
    serializer_class = AdditionalQualificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingViewSet(StageProtectedViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [permissions.IsAuthenticated]


class AppraisalCommentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AppraisalComment.objects.all()
    serializer_class = AppraisalCommentSerializer
    permission_classes = [permissions.IsAuthenticated]



