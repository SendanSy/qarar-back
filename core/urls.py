"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Standard Swagger/OpenAPI configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Qarar API",
        default_version='v1',
        description="API for Qarar news platform",
        terms_of_service="https://www.qarar.com/terms/",
        contact=openapi.Contact(email="contact@qarar.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# API URL patterns
urlpatterns = [
    # Language switching
    path('i18n/', include('django.conf.urls.i18n')),
    
    # API endpoints
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/content/', include('apps.content.urls')),
    
    # Swagger documentation - standard implementation
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Admin URLs with i18n support
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    prefix_default_language=False,
)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
