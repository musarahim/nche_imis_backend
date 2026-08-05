from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = 'procurement'
# Create a router and register our viewset with it.
router = DefaultRouter()
router.register(r'procurement-items', views.ProcurementItemViewSet, basename='procurement-item')
router.register(r'procurement-budgets', views.ProcurementBudgetViewSet, basename='procurement-budget')
router.register(r'procurement-expenditures', views.ProcurementExpenditureViewSet, basename='procurement-expenditure')

urlpatterns = [
    path('', include(router.urls)),
]