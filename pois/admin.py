"""
Admin configuration for Point of Interest model.
"""
from django.contrib import admin
from .models import PointOfInterest


@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    """
    Admin interface for Point of Interest with map display.
    """
    list_display = ('name', 'category', 'rating', 'created_at', 'coordinates_display')
    list_filter = ('category', 'rating', 'created_at')
    search_fields = ('name', 'description', 'address')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description')
        }),
        ('Location', {
            'fields': ('location',)
        }),
        ('Contact Information', {
            'fields': ('address', 'phone', 'website')
        }),
        ('Rating', {
            'fields': ('rating',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def coordinates_display(self, obj):
        """Display coordinates in a readable format."""
        if obj.coordinates:
            lng, lat = obj.coordinates
            return f"{lat:.6f}, {lng:.6f}"
        return "No coordinates"
    coordinates_display.short_description = "Coordinates" 