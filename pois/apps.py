"""
POI app configuration.
"""
from django.apps import AppConfig


class PoisConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pois'
    verbose_name = 'Points of Interest' 