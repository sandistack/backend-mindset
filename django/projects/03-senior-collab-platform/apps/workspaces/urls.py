"""
URL routing for workspace endpoints.
"""

from django.urls import path
from . import views

app_name = 'workspaces'

urlpatterns = [
    # Placeholder - will be implemented in next steps
    path('', views.placeholder, name='list'),
]
