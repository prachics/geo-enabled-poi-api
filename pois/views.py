"""
Views for Point of Interest API with optimized spatial queries.
"""
from django.contrib.gis.db.models.functions import Distance, Transform
from django.contrib.gis.geos import Point
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
import logging

from .models import PointOfInterest
from .serializers import (
    PointOfInterestSerializer,
    PointOfInterestCreateSerializer,
    RadiusQuerySerializer
)

logger = logging.getLogger(__name__)


class PointOfInterestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Point of Interest with optimized spatial queries.
    
    Features:
    - ST_DWithin for efficient radius queries
    - ST_Transform for coordinate system optimization
    - GIST and SP-GIST spatial indexing
    - Caching for frequently accessed queries
    - Distance calculation in responses
    """
    
    serializer_class = PointOfInterestSerializer
    
    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == 'create':
            return PointOfInterestCreateSerializer
        return PointOfInterestSerializer
    
    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        return PointOfInterest.objects.select_related().prefetch_related()
    
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    @action(detail=False, methods=['get'], url_path='pois')
    def radius_search(self, request):
        """
        Search POIs within a radius using optimized spatial queries.
        
        Query Parameters:
        - lat: Latitude of center point
        - lng: Longitude of center point  
        - radius_km: Search radius in kilometers
        - category: Filter by POI category (optional)
        - min_rating: Minimum rating filter (optional)
        
        Performance optimizations:
        - ST_DWithin for efficient spatial filtering
        - ST_Transform (EPSG 4326→3857) for better performance
        - GIST spatial index utilization
        - Distance calculation in meters then converted to km
        """
        
        # Validate query parameters
        serializer = RadiusQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Extract parameters
        lat = data['lat']
        lng = data['lng']
        radius_km = data['radius_km']
        category = data.get('category')
        min_rating = data.get('min_rating')
        
        # Create center point
        center_point = Point(lng, lat, srid=4326)
        
        # Build base queryset with spatial filtering
        queryset = PointOfInterest.objects.annotate(
            distance=Distance('location', center_point)
        ).filter(
            location__dwithin=(center_point, radius_km * 1000)  # Convert km to meters
        )
        
        # Apply additional filters
        if category:
            queryset = queryset.filter(category=category)
        
        if min_rating is not None:
            queryset = queryset.filter(rating__gte=min_rating)
        
        # Optimize query with spatial indexing
        # Use ST_Transform for better performance on large datasets
        queryset = queryset.extra(
            select={
                'distance_meters': """
                    ST_Distance(
                        ST_Transform(location, 3857),
                        ST_Transform(ST_GeomFromText(%s, 4326), 3857)
                    )
                """
            },
            select_params=[center_point.wkt]
        )
        
        # Order by distance for most relevant results first
        queryset = queryset.order_by('distance')
        
        # Limit results for performance (max 100 POIs)
        queryset = queryset[:100]
        
        # Serialize results
        serializer = self.get_serializer(queryset, many=True)
        
        # Add metadata
        response_data = {
            'count': len(serializer.data),
            'query': {
                'center': {'lat': lat, 'lng': lng},
                'radius_km': radius_km,
                'category': category,
                'min_rating': min_rating
            },
            'results': serializer.data
        }
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get list of available POI categories."""
        categories = [{'value': choice[0], 'label': choice[1]} 
                     for choice in PointOfInterest.CATEGORY_CHOICES]
        return Response({'categories': categories})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get basic statistics about POIs."""
        from django.db.models import Count, Avg
        
        stats = PointOfInterest.objects.aggregate(
            total_count=Count('id'),
            avg_rating=Avg('rating'),
            category_count=Count('category', distinct=True)
        )
        
        category_stats = PointOfInterest.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_pois': stats['total_count'],
            'average_rating': round(stats['avg_rating'], 2) if stats['avg_rating'] else None,
            'categories': list(category_stats)
        })
    
    def list(self, request, *args, **kwargs):
        """Override list to add performance optimizations."""
        # Add caching for list view
        cache_key = f"poi_list_{request.query_params}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return Response(cached_result)
        
        response = super().list(request, *args, **kwargs)
        
        # Cache for 2 minutes
        cache.set(cache_key, response.data, 120)
        
        return response 