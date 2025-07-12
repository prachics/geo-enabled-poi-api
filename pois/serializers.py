"""
Serializers for Point of Interest API.
"""
from rest_framework import serializers
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from .models import PointOfInterest


class PointOfInterestSerializer(serializers.ModelSerializer):
    """
    Serializer for Point of Interest with distance calculation.
    
    Features:
    - Distance calculation from query point
    - Optimized field selection for performance
    - Coordinate formatting for API responses
    """
    
    distance_km = serializers.SerializerMethodField()
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = PointOfInterest
        fields = [
            'id', 'name', 'category', 'description', 'address',
            'phone', 'website', 'rating', 'coordinates', 'distance_km',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_distance_km(self, obj):
        """Calculate distance in kilometers from query point."""
        if hasattr(obj, 'distance') and obj.distance is not None:
            # Convert meters to kilometers
            return round(obj.distance.km, 2)
        return None
    
    def get_coordinates(self, obj):
        """Format coordinates as [longitude, latitude]."""
        if obj.location:
            return [obj.location.x, obj.location.y]
        return None


class PointOfInterestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Point of Interest with coordinate validation.
    """
    
    coordinates = serializers.ListField(
        child=serializers.FloatField(),
        min_length=2,
        max_length=2,
        help_text="Coordinates as [longitude, latitude]"
    )
    
    class Meta:
        model = PointOfInterest
        fields = [
            'name', 'category', 'description', 'address',
            'phone', 'website', 'rating', 'coordinates'
        ]
    
    def validate_coordinates(self, value):
        """Validate coordinate format and range."""
        longitude, latitude = value
        
        if not (-180 <= longitude <= 180):
            raise serializers.ValidationError(
                "Longitude must be between -180 and 180 degrees"
            )
        
        if not (-90 <= latitude <= 90):
            raise serializers.ValidationError(
                "Latitude must be between -90 and 90 degrees"
            )
        
        return value
    
    def create(self, validated_data):
        """Create POI with proper Point object."""
        coordinates = validated_data.pop('coordinates')
        longitude, latitude = coordinates
        
        # Create Point object with WGS84 SRID
        location = Point(longitude, latitude, srid=4326)
        
        return PointOfInterest.objects.create(
            location=location,
            **validated_data
        )


class RadiusQuerySerializer(serializers.Serializer):
    """
    Serializer for radius query parameters with validation.
    """
    
    lat = serializers.FloatField(
        min_value=-90,
        max_value=90,
        help_text="Latitude of the center point"
    )
    lng = serializers.FloatField(
        min_value=-180,
        max_value=180,
        help_text="Longitude of the center point"
    )
    radius_km = serializers.FloatField(
        min_value=0.1,
        max_value=1000,
        default=10.0,
        help_text="Search radius in kilometers"
    )
    category = serializers.ChoiceField(
        choices=PointOfInterest.CATEGORY_CHOICES,
        required=False,
        help_text="Filter by POI category"
    )
    min_rating = serializers.FloatField(
        min_value=0,
        max_value=5,
        required=False,
        help_text="Minimum rating filter"
    )
    
    def validate(self, data):
        """Additional validation for query parameters."""
        # Ensure radius is reasonable for performance
        if data.get('radius_km', 10) > 100:
            raise serializers.ValidationError(
                "Radius cannot exceed 100 km for performance reasons"
            )
        return data 