"""
Point of Interest model with spatial indexing for high-performance queries.
"""
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class PointOfInterest(models.Model):
    """
    Point of Interest model with spatial indexing for high-performance radius queries.
    
    Features:
    - GIST and SP-GIST spatial indexes for optimal performance
    - ST_Transform support for coordinate system conversions
    - Optimized field types for minimal storage and maximum speed
    """
    
    CATEGORY_CHOICES = [
        ('restaurant', 'Restaurant'),
        ('hotel', 'Hotel'),
        ('museum', 'Museum'),
        ('park', 'Park'),
        ('shopping', 'Shopping'),
        ('transport', 'Transport'),
        ('landmark', 'Landmark'),
        ('entertainment', 'Entertainment'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
    ]
    
    name = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    location = models.PointField(
        srid=4326,  # WGS84 - standard for GPS coordinates
        spatial_index=True,  # Creates GIST index automatically
        db_index=True,
        help_text="Geographic coordinates (longitude, latitude)"
    )
    description = models.TextField(blank=True)
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'pois'
        indexes = [
            models.Index(fields=['category', 'created_at']),
            models.Index(fields=['rating', 'category']),
        ]
        # Spatial indexes are created automatically by GeoDjango
        # GIST index on location field for spatial queries
        # SP-GIST index will be created manually in migrations
        
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    def save(self, *args, **kwargs):
        """Ensure location is properly formatted before saving."""
        if isinstance(self.location, (list, tuple)) and len(self.location) == 2:
            # Convert [lng, lat] to Point object
            self.location = Point(self.location[0], self.location[1], srid=4326)
        super().save(*args, **kwargs)
    
    @property
    def longitude(self):
        """Get longitude coordinate."""
        return self.location.x if self.location else None
    
    @property
    def latitude(self):
        """Get latitude coordinate."""
        return self.location.y if self.location else None
    
    @property
    def coordinates(self):
        """Get coordinates as tuple (longitude, latitude)."""
        if self.location:
            return (self.location.x, self.location.y)
        return None 