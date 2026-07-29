from django.shortcuts import render
from rest_framework import viewsets

from .models import (AppraisalComment, AppraisalOutput, CompetencyRating,
                     ImprovementArea, PerformanceAppraisal)
from .serializers import (AppraisalCommentSerializer,
                          AppraisalOutputSerializer,
                          CompetencyRatingSerializer,
                          ImprovementAreaSerializer,
                          PerformanceAppraisalSerializer)

# Create your views here.

class PerformanceAppraisalViewSet(viewsets.ModelViewSet):
    """ViewSet for PerformanceAppraisal model"""
    queryset = PerformanceAppraisal.objects.all()
    serializer_class = PerformanceAppraisalSerializer


class AppraisalOutputViewSet(viewsets.ModelViewSet):
    """ViewSet for AppraisalOutput model"""
    queryset = AppraisalOutput.objects.all()
    serializer_class = AppraisalOutputSerializer


class CompetencyRatingViewSet(viewsets.ModelViewSet):
    """ViewSet for CompetencyRating model"""
    queryset = CompetencyRating.objects.all()
    serializer_class = CompetencyRatingSerializer

class ImprovementAreaViewSet(viewsets.ModelViewSet):
    """ViewSet for ImprovementArea model"""
    queryset = ImprovementArea.objects.all()
    serializer_class = ImprovementAreaSerializer

class AppraisalCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for AppraisalComment model"""
    queryset = AppraisalComment.objects.all()
    serializer_class = AppraisalCommentSerializer



