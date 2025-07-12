"""
URL configuration for POI API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'pois', views.PointOfInterestViewSet, basename='pointofinterest')

urlpatterns = [
    path('', include(router.urls)),
] 