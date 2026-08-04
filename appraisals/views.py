from django.shortcuts import render
from django.utils import timezone
from hr.models import Employee
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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
        return PerformanceAppraisal.objects.all().select_related(
            'appraisee', 'appraiser', 'reviewer', 'director', 'executive_director'
        )

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
        appraisal.status = 'self_assessment'
        appraisal.date_submitted = timezone.now()
        appraisal.save()
        # Save appraisee comment (Section F) if provided
        comment_text = request.data.get('comment', '')
        employee = self._get_employee(request)
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
        # Save supervisor remarks if provided
        supervisor_remarks = request.data.get('supervisor_remarks', '')
        if supervisor_remarks:
            appraisal.supervisor_remarks = supervisor_remarks

        # Recalculate scores
        outputs = appraisal.outputs.all()
        agreed_scores = [o.agreed_score for o in outputs if o.agreed_score is not None]
        if agreed_scores:
            total = sum(agreed_scores)
            max_score = len(agreed_scores) * 5
            appraisal.output_total_score = total
            appraisal.output_average = total / len(agreed_scores)
            appraisal.output_weighted_score = round((total / max_score) * 70, 2)

        competencies = appraisal.competencies.all()
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
        comment_text = request.data.get('comment', '')
        employee = self._get_employee(request)
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
        comment_text = request.data.get('comment', '')
        employee = self._get_employee(request)
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
        comment_text = request.data.get('comment', '')
        employee = self._get_employee(request)
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
        print(f"Creating appraisal for employee: {employee}")
        if employee:
            
            serializer.save(appraisee=employee, appraiser=employee.supervisor)
        else:
            serializer.save()


class AppraisalOutputViewSet(viewsets.ModelViewSet):
    queryset = AppraisalOutput.objects.all()
    serializer_class = AppraisalOutputSerializer
    permission_classes = [permissions.IsAuthenticated]


class CompetencyRatingViewSet(viewsets.ModelViewSet):
    queryset = CompetencyRating.objects.all()
    serializer_class = CompetencyRatingSerializer
    permission_classes = [permissions.IsAuthenticated]


class ImprovementAreaViewSet(viewsets.ModelViewSet):
    queryset = ImprovementArea.objects.all()
    serializer_class = ImprovementAreaSerializer
    permission_classes = [permissions.IsAuthenticated]


class NextYearPerformancePlanViewSet(viewsets.ModelViewSet):
    queryset = NextYearPerformancePlan.objects.all()
    serializer_class = NextYearPerformancePlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class InitialQualificationViewSet(viewsets.ModelViewSet):
    queryset = InitialQualification.objects.all()
    serializer_class = InitialQualificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class AdditionalQualificationViewSet(viewsets.ModelViewSet):
    queryset = AdditionalQualification.objects.all()
    serializer_class = AdditionalQualificationSerializer
    permission_classes = [permissions.IsAuthenticated]


class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [permissions.IsAuthenticated]


class AppraisalCommentViewSet(viewsets.ModelViewSet):
    queryset = AppraisalComment.objects.all()
    serializer_class = AppraisalCommentSerializer
    permission_classes = [permissions.IsAuthenticated]



