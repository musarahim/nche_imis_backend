import json

from accounts.models import User
from accounts.serializers import EmployeeUserSerializer
from django.shortcuts import render
from rest_framework import filters, parsers, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (Department, Dependent, Designation, Directorate,
                     EducationHistory, Employee, GradeScale, Referee,
                     WorkHistory)
from .serializers import (DepartmentSerializer, DependentSerializer,
                          DesignationSerializer, DirectorateSerializer,
                          EducationHistorySerializer, EmpDrodpdownSerializer,
                          EmployeeSerializer, EmployeeUpdateSerializer,
                          GradeScaleSerializer, RefereeSerializer,
                          WorkHistorySerializer)


# Create your views here.
class DirectorateViewSet(viewsets.ModelViewSet):
    '''Directorate viewset'''
    queryset = Directorate.objects.all()
    serializer_class = DirectorateSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'short_code']
    ordering_fields = ['name', 'created']
    ordering = ['name']
    pagination_class = None

class DepartmentViewSet(viewsets.ModelViewSet):
    '''Department viewset'''
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'short_code']
    ordering_fields = ['name', 'created']
    ordering = ['name']
    pagination_class = None

    def get_queryset(self):
        '''Return departments, optionally filtered by directorate'''
        queryset = self.queryset
        directorate_id = self.request.query_params.get('directorate_id', None)
        if directorate_id is not None:
            queryset = queryset.filter(directorate__id=directorate_id)
        return queryset


class DesignationViewSet(viewsets.ModelViewSet):
    '''Designation viewset'''
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created']
    ordering = ['name']
    pagination_class = None


class GradeScaleViewSet(viewsets.ModelViewSet):
    '''GradeScale viewset'''
    queryset = GradeScale.objects.all()
    serializer_class = GradeScaleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

class DependentViewSet(viewsets.ModelViewSet):
    '''Dependent viewset'''
    queryset = Dependent.objects.all()
    serializer_class = DependentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        '''Return dependents for a specific employee if employee_id is provided'''
        queryset = self.queryset
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id is not None:
            queryset = queryset.filter(employee__id=employee_id)
        return queryset

class EducationHistoryViewSet(viewsets.ModelViewSet):
    '''EducationHistory viewset'''
    queryset = EducationHistory.objects.all()
    serializer_class = EducationHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        '''Return education histories for a specific employee if employee_id is provided'''
        queryset = self.queryset
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id is not None:
            queryset =queryset.filter(employee__id=employee_id)
        return queryset

class WorkHistoryViewSet(viewsets.ModelViewSet):
    '''WorkHistory viewset'''
    queryset = WorkHistory.objects.all()
    serializer_class = WorkHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        '''Return work histories for a specific employee if employee_id is provided'''
        queryset = self.queryset
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id is not None:
            queryset =queryset.filter(employee__id=employee_id)
        return queryset
    
class RefereeViewSet(viewsets.ModelViewSet):
    '''Referee viewset'''
    queryset = Referee.objects.all()
    serializer_class = RefereeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        '''Return referees for a specific employee if employee_id is provided'''
        queryset = self.queryset
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id is not None:
            queryset =queryset.filter(employee__id=employee_id)
        return queryset
    
    
class EmployeeViewSet(viewsets.ModelViewSet):
    '''Employee viewset'''
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['system_account__first_name', 'system_account__last_name', 'employee_number']
    ordering_fields = ['employee_number', 'created']
    ordering = ['employee_number']

    def get_queryset(self):
        '''Return employees, optionally filtered by department or designation'''
        if self.request.user.is_superuser or  self.request.user.groups.filter(name='Human Resource').exists():
            # If the user is not a superuser, filter by the user's employee record
            try:
                queryset = self.queryset.all()
            except Employee.DoesNotExist:
                queryset = self.queryset.none()  # No employee record found for the user
        else:
            # If the user is a superuser, return all employees
            queryset = self.queryset.filter(system_account=self.request.user)
        return queryset
    
    @action(detail=False, methods=['get'], url_path='employee-dropdown')
    def employee_dropdown(self, request, pk=None):
        """
        GET /employees/employee-dropdown/
        Retrieve employees in the same department as the requesting user for dropdowns.
        """
        employee = Employee.objects.get(system_account=request.user)
        employees = Employee.objects.filter(department=employee.department, is_active=True).exclude(id=employee.id)
        serializer = EmpDrodpdownSerializer(employees, many=True)
        self.pagination_class = None
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='employee-details')
    def employee_details(self, request, pk=None):
        """
        GET /employees/{id}/employee-details/
        Retrieve detailed information for a specific employee.
        """
        employee = self.get_object()
        serializer = EmployeeUpdateSerializer(employee)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """Override update to handle dependants JSON submitted via FormData."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        dependents_json = request.data.get('dependents', None)
        if dependents_json is not None:
            try:
                dependents_data = json.loads(dependents_json)
                instance.dependent_set.all().delete()
                for dep in dependents_data:
                    dep.pop('id', None)
                    dep.pop('employee', None)
                    relationship_id = dep.pop('relationship', None)
                    if relationship_id:
                        Dependent.objects.create(
                            employee=instance,
                            relationship_id=relationship_id,
                            **dep
                        )
            except (json.JSONDecodeError, Exception):
                pass

        education_histories_json = request.data.get('education_histories', None)
        if education_histories_json is not None:
            try:
                edu_data_list = json.loads(education_histories_json)
                submitted_ids = {int(e['id']) for e in edu_data_list if e.get('id')}
                instance.educationhistory_set.exclude(id__in=submitted_ids).delete()
                for idx, edu in enumerate(edu_data_list):
                    edu_id = edu.pop('id', None)
                    edu.pop('employee', None)
                    edu.pop('certificate_document', None)
                    cert_file = request.FILES.get(f'edu_cert_{idx}', None)
                    if edu_id:
                        try:
                            edu_obj = EducationHistory.objects.get(id=edu_id, employee=instance)
                            for k, v in edu.items():
                                setattr(edu_obj, k, v)
                            if cert_file:
                                edu_obj.certificate_document = cert_file
                            edu_obj.save()
                        except EducationHistory.DoesNotExist:
                            edu_obj = EducationHistory.objects.create(employee=instance, **edu)
                            if cert_file:
                                edu_obj.certificate_document = cert_file
                                edu_obj.save()
                    else:
                        edu_obj = EducationHistory.objects.create(employee=instance, **edu)
                        if cert_file:
                            edu_obj.certificate_document = cert_file
                            edu_obj.save()
            except (json.JSONDecodeError, Exception):
                pass

        work_histories_json = request.data.get('work_histories', None)
        if work_histories_json is not None:
            try:
                work_data_list = json.loads(work_histories_json)
                submitted_ids = {int(w['id']) for w in work_data_list if w.get('id')}
                instance.workhistory_set.exclude(id__in=submitted_ids).delete()
                for work in work_data_list:
                    work_id = work.pop('id', None)
                    work.pop('employee', None)
                    if work_id:
                        try:
                            work_obj = WorkHistory.objects.get(id=work_id, employee=instance)
                            for k, v in work.items():
                                setattr(work_obj, k, v)
                            work_obj.save()
                        except WorkHistory.DoesNotExist:
                            WorkHistory.objects.create(employee=instance, **work)
                    else:
                        WorkHistory.objects.create(employee=instance, **work)
            except (json.JSONDecodeError, Exception):
                pass

        referees_json = request.data.get('referees', None)
        if referees_json is not None:
            try:
                referee_data_list = json.loads(referees_json)
                submitted_ids = {int(r['id']) for r in referee_data_list if r.get('id')}
                instance.referee_set.exclude(id__in=submitted_ids).delete()
                for ref in referee_data_list:
                    ref_id = ref.pop('id', None)
                    ref.pop('employee', None)
                    if ref_id:
                        try:
                            ref_obj = Referee.objects.get(id=ref_id, employee=instance)
                            for k, v in ref.items():
                                setattr(ref_obj, k, v)
                            ref_obj.save()
                        except Referee.DoesNotExist:
                            Referee.objects.create(employee=instance, **ref)
                    else:
                        Referee.objects.create(employee=instance, **ref)
            except (json.JSONDecodeError, Exception):
                pass

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(self.get_serializer(instance).data)
    

class UserDropdownViewSet(viewsets.ModelViewSet):
    '''User dropdown viewset'''
    queryset = User.objects.all()
    serializer_class = EmployeeUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


# employee dropdown viewset
class EmployeeDropdownViewSet(viewsets.ModelViewSet):
    '''Employee dropdown viewset'''
    queryset = Employee.objects.all()
    serializer_class = EmpDrodpdownSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

