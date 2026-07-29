from rest_framework import serializers

from .models import (AppraisalComment, AppraisalOutput, CompetencyRating,
                     ImprovementArea, PerformanceAppraisal)


class PerformanceAppraisalSerializer(serializers.ModelSerializer):
    """Serializer for PerformanceAppraisal model"""
    class Meta:
        model = PerformanceAppraisal
        fields = '__all__'

class AppraisalOutputSerializer(serializers.ModelSerializer):
    """Serializer for AppraisalOutput model"""
    class Meta:
        model = AppraisalOutput
        fields = '__all__'

class CompetencyRatingSerializer(serializers.ModelSerializer):
    """Serializer for CompetencyRating model"""
    class Meta:
        model = CompetencyRating
        fields = '__all__'

class ImprovementAreaSerializer(serializers.ModelSerializer):
    """Serializer for ImprovementArea model"""
    class Meta:
        model = ImprovementArea
        fields = '__all__'

class AppraisalCommentSerializer(serializers.ModelSerializer):
    """Serializer for AppraisalComment model"""
    class Meta:
        model = AppraisalComment
        fields = '__all__'