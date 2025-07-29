from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrganizationViewSet, SubsidiaryViewSet, DepartmentViewSet

app_name = 'producers'

# Create router
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'subsidiaries', SubsidiaryViewSet, basename='subsidiary')
router.register(r'departments', DepartmentViewSet, basename='department')

urlpatterns = [
    path('', include(router.urls)),
] 