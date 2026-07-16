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
                          EmployeeSerializer, GradeScaleSerializer,
                          RefereeSerializer, WorkHistorySerializer)


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