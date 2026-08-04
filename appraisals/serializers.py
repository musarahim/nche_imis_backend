from rest_framework import serializers

from .models import (AdditionalQualification, AppraisalComment,
                     AppraisalOutput, CompetencyRating, ImprovementArea,
                     InitialQualification, NextYearPerformancePlan,
                     PerformanceAppraisal, Training)


class AppraisalOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppraisalOutput
        fields = '__all__'


class CompetencyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetencyRating
        fields = '__all__'


class ImprovementAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImprovementArea
        fields = '__all__'


class NextYearPerformancePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextYearPerformancePlan
        fields = '__all__'


class InitialQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InitialQualification
        fields = '__all__'


class AdditionalQualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalQualification
        fields = '__all__'


class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = '__all__'


class AppraisalCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppraisalComment
        fields = '__all__'


class PerformanceAppraisalSerializer(serializers.ModelSerializer):
    appraisee_name = serializers.SerializerMethodField()
    appraiser_name = serializers.SerializerMethodField()

    class Meta:
        model = PerformanceAppraisal
        fields = '__all__'

    def get_appraisee_name(self, obj):
        return obj.appraisee.full_name if obj.appraisee else None

    def get_appraiser_name(self, obj):
        return obj.appraiser.full_name if obj.appraiser else None


class PerformanceAppraisalDetailSerializer(PerformanceAppraisalSerializer):
    """Full detail serializer with all nested objects."""
    outputs = AppraisalOutputSerializer(many=True, read_only=True)
    competencies = CompetencyRatingSerializer(many=True, read_only=True)
    improvement_areas = ImprovementAreaSerializer(many=True, read_only=True)
    next_year_plans = NextYearPerformancePlanSerializer(many=True, read_only=True)
    initial_qualifications = InitialQualificationSerializer(many=True, read_only=True)
    additional_qualifications = AdditionalQualificationSerializer(many=True, read_only=True)
    trainings = TrainingSerializer(many=True, read_only=True)
    comments = AppraisalCommentSerializer(many=True, read_only=True)

    class Meta(PerformanceAppraisalSerializer.Meta):
        pass