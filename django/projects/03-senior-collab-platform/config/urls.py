"""
Main URL configuration for Senior Collaboration Platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Senior Collaboration Platform API",
#         default_version='v1',
#         description="Advanced collaboration platform with real-time features",
#         terms_of_service="https://www.example.com/terms/",
#         contact=openapi.Contact(email="contact@example.com"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation (drf-yasg disabled for now)
    # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API v1
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/workspaces/', include('apps.workspaces.urls')),
    path('api/v1/documents/', include('apps.documents.urls')),
    path('api/v1/channels/', include('apps.channels.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/files/', include('apps.files.urls')),
    path('api/v1/search/', include('apps.search.urls')),
    path('api/v1/activity/', include('apps.activity.urls')),
    
    # Health check
    path('health/', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
