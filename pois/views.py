"""
Views for Point of Interest API with optimized spatial queries.
"""
import logging

from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PointOfInterest
from .serializers import PointOfInterestCreateSerializer, PointOfInterestSerializer, RadiusQuerySerializer

logger = logging.getLogger(__name__)


class PointOfInterestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Points of Interest: CRUD plus index-backed radius search (ST_DWithin on a geography column).
    """

    serializer_class = PointOfInterestSerializer

    def get_serializer_class(self):
        """Use different serializers for different actions."""
        if self.action == "create":
            return PointOfInterestCreateSerializer
        return PointOfInterestSerializer

    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        return PointOfInterest.objects.select_related().prefetch_related()

    @method_decorator(cache_page(300))  # Cache for 5 minutes
    @action(detail=False, methods=["get"], url_path="pois")
    def radius_search(self, request):
        """
        Search POIs within a radius, nearest first (max 100).

        Query Parameters:
        - lat, lng: center point
        - radius_km: search radius in kilometers
        - category: filter by POI category (optional)
        - min_rating: minimum rating (optional)

        Responses are cached for 5 minutes per URL.
        """

        # Validate query parameters
        serializer = RadiusQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Extract parameters
        lat = data["lat"]
        lng = data["lng"]
        radius_km = data["radius_km"]
        category = data.get("category")
        min_rating = data.get("min_rating")

        # Create center point
        center_point = Point(lng, lat, srid=4326)

        # The index-backed radius filter narrows the rows before distances are computed and sorted.
        queryset = PointOfInterest.objects.filter(location__dwithin=(center_point, D(km=radius_km))).annotate(
            distance=Distance("location", center_point)
        )

        # Apply additional filters
        if category:
            queryset = queryset.filter(category=category)

        if min_rating is not None:
            queryset = queryset.filter(rating__gte=min_rating)

        # Order by distance for most relevant results first
        queryset = queryset.order_by("distance")

        # Limit results for performance (max 100 POIs)
        queryset = queryset[:100]

        # Serialize results
        serializer = self.get_serializer(queryset, many=True)

        # Add metadata
        response_data = {
            "count": len(serializer.data),
            "query": {
                "center": {"lat": lat, "lng": lng},
                "radius_km": radius_km,
                "category": category,
                "min_rating": min_rating,
            },
            "results": serializer.data,
        }

        return Response(response_data)

    @action(detail=False, methods=["get"])
    def categories(self, request):
        """Get list of available POI categories."""
        categories = [{"value": choice[0], "label": choice[1]} for choice in PointOfInterest.CATEGORY_CHOICES]
        return Response({"categories": categories})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get basic statistics about POIs."""
        from django.db.models import Avg, Count

        stats = PointOfInterest.objects.aggregate(
            total_count=Count("id"), avg_rating=Avg("rating"), category_count=Count("category", distinct=True)
        )

        category_stats = PointOfInterest.objects.values("category").annotate(count=Count("id")).order_by("-count")

        return Response(
            {
                "total_pois": stats["total_count"],
                "average_rating": round(stats["avg_rating"], 2) if stats["avg_rating"] else None,
                "categories": list(category_stats),
            }
        )

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
