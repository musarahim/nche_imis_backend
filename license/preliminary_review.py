"""Generate reviewable fields from licensing records and persist field observations."""
import hashlib
import html
import json
import re
from datetime import date, datetime
from decimal import Decimal

from django.db import models, transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import LicensingPreliminaryReview

EXCLUDED = {'id', 'created', 'modified', 'deleted_at', 'application_code', 'code', 'application_date',
            'institution', 'institute', 'status', 'desk_reviewer', 'is_odai'}
LABELS = {'acroynm': 'Acronym', 'ISP_provider': 'Internet service provider', 'stractegic_plan': 'Strategic plan',
          'student_Welfare_offices': 'Student welfare offices', 'tin': 'Tax identification number'}
INSTITUTION_FIELDS = ['name', 'acroynm', 'institution_type', 'category', 'postal_address', 'website', 'landline',
                      'alternative_email', 'tin', 'region', 'district', 'county', 'sub_county', 'parish', 'village',
                      'location', 'contact_person', 'contact_person_phone', 'alternative_contact_person',
                      'alternative_contact_person_phone', 'logo']
SECTIONS = [
    ('Location and land', ['geographical', 'location', 'land', 'year_obtained', 'leased', 'lease', 'title_deed', 'has_title_deed']),
    ('Infrastructure and transport', ['classroom', 'libraries', 'science_lab', 'computer_lab', 'staff_house', 'administrative_staff_area',
        'area_for_staff', 'administrative_block_area', 'welfare_office', 'sick_bay', 'hostel', 'meeting_hall', 'master_plan',
        'playground', 'empty_space', 'roads', 'water_source', 'power_source', 'cultivable', 'vehicle', 'infrastructure']),
    ('Educational facilities', ['library', 'text_book', 'publication', 'computer', 'internet', 'isp_', 'students_have_access',
        'seats', 'student_facilities', 'facilities', 'physical_education']),
    ('Staff and governance', ['staff', 'qualification', 'phd', 'master', 'bachelor', 'diploma', 'council', 'senate', 'chancellor',
        'secretary', 'registrar', 'dean', 'heads_of', 'governing', 'principal', 'governance', 'human_resources']),
    ('Ownership and promoters', ['ownership', 'promoter']),
    ('Financial management', ['finance', 'financial', 'budget', 'fee', 'income', 'bank', 'assets', 'accounts', 'salary', 'salaries']),
    ('Vision, mission and programmes', ['vision', 'mission', 'objective', 'philosophy', 'strategic', 'stractegic', 'programme', 'competence', 'action_plan']),
    ('Student population', ['student', 'percentage', 'region', 'east_african']),
    ('Supporting documents', ['signature', 'member_cv', 'document', 'proposal']),
]


def label_for(name):
    return LABELS.get(name, name.replace('_', ' ').strip().capitalize())


def section_for(name, file_field=False):
    for section, prefixes in SECTIONS:
        if any(part in name.lower() for part in prefixes):
            return section
    return 'Supporting documents' if file_field else 'Other application details'


def display_field(instance, field, key, section, request):
    value = getattr(instance, field.name)
    kind = 'text'
    if isinstance(field, models.FileField):
        kind = 'file'
        value = request.build_absolute_uri(value.url) if value else None
    elif field.choices:
        value = getattr(instance, 'get_' + field.name + '_display')()
    elif field.is_relation:
        value = getattr(value, 'name', None) or getattr(value, 'code', None) or (str(value.pk) if value else None)
    elif isinstance(value, bool):
        kind = 'boolean'
    elif isinstance(value, (int, float, Decimal)):
        kind = 'number'
        value = str(value) if isinstance(value, Decimal) else value
    elif isinstance(value, (date, datetime)):
        value = value.isoformat()
    elif isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    elif value is not None:
        value = str(value)
        # Render submitted rich text as text, never execute applicant HTML in the review UI.
        if '<' in value:
            value = html.unescape(re.sub('<[^>]*>', ' ', value))
    return {'key': key, 'label': label_for(field.name), 'section': section, 'kind': kind, 'value': value}


def application_fields(view, application, request):
    rows = []
    institution = getattr(application, view.institution_field)
    if institution:
        for name in INSTITUTION_FIELDS:
            rows.append(display_field(institution, institution._meta.get_field(name), 'institution.' + name, 'Institution details', request))
        for name in ['email', 'phone']:
            value = getattr(institution.user, name, None)
            rows.append({'key': 'institution.' + name, 'label': label_for(name), 'section': 'Institution details',
                         'kind': 'text', 'value': str(value) if value else None})
    for field in application._meta.concrete_fields:
        if field.name in EXCLUDED:
            continue
        rows.append(display_field(application, field, 'application.' + field.name,
                                  section_for(field.name, isinstance(field, models.FileField)), request))
    # Each submitted repeatable item has stable, individually commentable fields.
    collections = [('interimpromoters_set', 'Ownership and promoters'), ('objective_items', 'Vision, mission and programmes'),
                   ('university_provisional_objective_items', 'Vision, mission and programmes'),
                   ('vehicles', 'Infrastructure and transport'), ('documents', 'Supporting documents')]
    for relation, section in collections:
        manager = getattr(application, relation, None)
        if not hasattr(manager, 'all'):
            continue
        for index, item in enumerate(manager.all().order_by('id'), start=1):
            for field in item._meta.concrete_fields:
                if field.name in {'id', 'created', 'modified', 'deleted_at', 'order'} or (field.is_relation and field.name != 'nationality'):
                    continue
                row = display_field(item, field, f'{relation}.{item.pk}.{field.name}', section, request)
                collection_label = {'interimpromoters_set': 'Promoter', 'objective_items': 'Objective',
                                    'university_provisional_objective_items': 'Objective', 'vehicles': 'Vehicle',
                                    'documents': 'Supporting document'}[relation]
                row['label'] = f'{collection_label} {index}: {row["label"]}'
                rows.append(row)
    return rows


def fields_hash(fields):
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def review_type(view):
    # Includes university/ODAI type so IDs from shared models never cross application types.
    return view.review_portal_path.removeprefix('/license/')


def serialize_review(review):
    if review is None:
        return None
    return {'id': review.pk, 'reviewer_id': review.reviewer_id, 'reviewer_name': review.reviewer.username,
            'observations': review.observations, 'summary': review.summary, 'outcome': review.outcome,
            'revision': review.revision, 'updated_at': review.updated_at, 'submitted_at': review.submitted_at,
            'snapshot_hash': review.snapshot_hash}


class ObservationSerializer(serializers.Serializer):
    finding = serializers.ChoiceField(choices=['note', 'clarification'])
    comment = serializers.CharField(max_length=10000, trim_whitespace=True)


class ReviewInputSerializer(serializers.Serializer):
    revision = serializers.IntegerField(min_value=0)
    snapshot_hash = serializers.CharField(max_length=64)
    observations = serializers.DictField(child=ObservationSerializer(), required=False, default=dict)
    summary = serializers.CharField(required=False, allow_blank=True, max_length=20000, default='')
    outcome = serializers.ChoiceField(choices=['', 'no_concerns', 'clarification_required'], default='')
    submit = serializers.BooleanField(default=False)
    confirmed = serializers.BooleanField(default=False)


def preliminary_review(view, request, pk):
    from .reviewer_assignment import eligible_reviewers

    with transaction.atomic():
        # Lock the application to serialize draft creation, submission and reassignment.
        application = get_object_or_404(view.get_queryset().select_for_update(), pk=pk) if request.method == 'POST' else view.get_object()
        reviewer = application.desk_reviewer
        can_edit = bool(reviewer and reviewer.pk == request.user.pk and application.status == 'prelim_review'
                        and eligible_reviewers().filter(pk=request.user.pk).exists())
        if not (can_edit or view.can_assign_reviews() or (reviewer and reviewer.pk == request.user.pk and eligible_reviewers().filter(pk=request.user.pk).exists())):
            raise PermissionDenied('Only the assigned ILA reviewer and licensing supervisors can access preliminary reviews.')
        reviews = LicensingPreliminaryReview.objects.filter(application_type=review_type(view), application_id=application.pk)
        current = reviews.filter(reviewer=reviewer).first() if reviewer else None
        if current and current.submitted_at and application.status == 'prelim_review':
            # A later review round must not overwrite a submitted record.
            current = None
        fields = application_fields(view, application, request)
        current_hash = fields_hash(fields)
        if request.method == 'POST':
            if not can_edit:
                raise PermissionDenied('Only the assigned active ILA Desk Review Officer can save this review.')
            payload = ReviewInputSerializer(data=request.data)
            payload.is_valid(raise_exception=True)
            data = payload.validated_data
            if data['revision'] != (current.revision if current else 0):
                return Response({'detail': 'This draft changed in another session. Reload before saving.'}, status=409)
            if data['snapshot_hash'] != current_hash:
                return Response({'detail': 'The application changed. Reload and check your observations against the latest fields.'}, status=409)
            keys = {row['key'] for row in fields}
            if set(data['observations']) - keys:
                raise ValidationError({'observations': 'Comments must reference fields in this application.'})
            if data['submit']:
                if not data['confirmed'] or not data['summary'].strip() or not data['outcome']:
                    raise ValidationError({'detail': 'Confirm the review, provide an overall summary and select a conclusion.'})
                if data['outcome'] == 'no_concerns' and any(row['finding'] == 'clarification' for row in data['observations'].values()):
                    raise ValidationError({'outcome': 'Choose clarification required when any field needs clarification.'})
            current = current or LicensingPreliminaryReview(application_type=review_type(view), application_id=application.pk, reviewer=reviewer, revision=0)
            current.application_snapshot = fields
            current.snapshot_hash = current_hash
            current.observations = data['observations']
            current.summary = data['summary']
            current.outcome = data['outcome']
            current.revision += 1
            if data['submit']:
                current.submitted_at = timezone.now()
                application.status = 'prelim_feedback'
                application.save(update_fields=['status'])
                can_edit = False
            current.save()
        shown_fields = current.application_snapshot if current and current.submitted_at else fields
        return Response({
            'application_code': getattr(application, view.code_field), 'institution': institution_name(view, application),
            'status': application.get_status_display(), 'can_edit': can_edit and not bool(current and current.submitted_at),
            'fields': shown_fields, 'snapshot_hash': current_hash,
            'review': serialize_review(current),
            'history': [dict(serialize_review(row), fields=row.application_snapshot) for row in reviews.filter(submitted_at__isnull=False).select_related('reviewer')],
        })


def institution_name(view, application):
    institution = getattr(application, view.institution_field)
    return institution.name if institution else ''
