"""
Health check views for monitoring and readiness checks.
"""
from django.http import JsonResponse
from django.db import connection
import psutil
import os


def health_check(request):
    """
    Basic health check endpoint.
    
    Returns:
        - 200: Service is healthy
        - 500: Service is unhealthy
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check PostGIS functionality
        with connection.cursor() as cursor:
            cursor.execute("SELECT PostGIS_Version()")
        
        # Check system resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_data = {
            'status': 'healthy',
            'database': 'connected',
            'postgis': 'available',
            'system': {
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'cpu_percent': psutil.cpu_percent(interval=1)
            }
        }
        
        return JsonResponse(health_data, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)


def ready_check(request):
    """
    Readiness check for Kubernetes/container orchestration.
    
    Checks:
        - Database connectivity
        - PostGIS availability
        - Basic application functionality
    """
    try:
        # Check database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check PostGIS functionality
        with connection.cursor() as cursor:
            cursor.execute("SELECT PostGIS_Version()")
        
        # Check if POI model is accessible
        from .models import PointOfInterest
        try:
            poi_count = PointOfInterest.objects.count()
        except Exception as model_exc:
            poi_count = None
            # Optionally, you could log model_exc here
        
        ready_data = {
            'status': 'ready',
            'database': 'connected',
            'postgis': 'available',
            'models': 'accessible' if poi_count is not None else 'unavailable',
            'poi_count': poi_count
        }
        
        return JsonResponse(ready_data, status=200)
        
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e)
        }, status=503) 