"""
Health check URL configuration.
"""
from django.urls import path
from . import health_views

urlpatterns = [
    path('', health_views.health_check, name='health_check'),
    path('ready/', health_views.ready_check, name='ready_check'),
] 