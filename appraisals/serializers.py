from rest_framework import serializers
from datetime import timedelta

from .models import (AdditionalQualification, AppraisalComment,
                     AppraisalOutput, CompetencyRating, ImprovementArea,
                     InitialQualification, NextYearPerformancePlan,
                     PerformanceAppraisal, Training)


class AppraisalOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppraisalOutput
        fields = '__all__'

    def validate(self, attrs):
        appraisal = attrs.get('appraisal') or getattr(self.instance, 'appraisal', None)
        if appraisal and not self.instance and appraisal.outputs.count() >= 10:
            raise serializers.ValidationError('An appraisal can have at most 10 outputs.')
        return attrs


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
    appraisee_birth_date = serializers.DateField(source='appraisee.date_of_birth', read_only=True)
    appraisee_designation = serializers.CharField(source='appraisee.designation.name', read_only=True)
    appraisee_directorate = serializers.CharField(source='appraisee.directorate.name', read_only=True)
    appraisee_department = serializers.CharField(source='appraisee.department.name', read_only=True)
    appraiser_designation = serializers.CharField(source='appraiser.designation.name', read_only=True)
    employment_terms = serializers.CharField(source='appraisee.employment_terms', read_only=True)
    present_appointment_date = serializers.DateField(source='appraisee.present_appointment_date', read_only=True)
    appraisee_salary_scale = serializers.CharField(source='appraisee.grade_scale.code', read_only=True)
    appraiser_salary_scale = serializers.CharField(source='appraiser.grade_scale.code', read_only=True)

    class Meta:
        model = PerformanceAppraisal
        fields = '__all__'
        read_only_fields = ('appraisee', 'appraiser', 'status', 'date_submitted',
                            'reviewer', 'director', 'executive_director',
                            'output_total_score', 'output_average', 'output_weighted_score',
                            'competency_total_score', 'competency_average',
                            'competency_weighted_score', 'overall_score', 'overall_level')

    def validate(self, attrs):
        start = attrs.get('start_date', getattr(self.instance, 'start_date', None))
        end = attrs.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end:
            if end < start:
                raise serializers.ValidationError({'end_date': 'End date must be after start date.'})
            # The form provides a three month probation or twelve month annual period.
            if end - start > timedelta(days=366):
                raise serializers.ValidationError({'end_date': 'Assessment period cannot exceed one year.'})
            request = self.context.get('request')
            employee = getattr(self.instance, 'appraisee', None) or getattr(getattr(request, 'user', None), 'employee', None)
            terms = getattr(employee, 'employment_terms', '')
            if terms == 'probation' and end - start > timedelta(days=92):
                raise serializers.ValidationError({'end_date': 'A probation appraisal cannot exceed three months.'})
        return attrs

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
