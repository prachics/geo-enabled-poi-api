"""
Test suite for Point of Interest API.
"""
import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.gis.geos import Point
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from pois.models import PointOfInterest


class PointOfInterestModelTest(TestCase):
    """Test PointOfInterest model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.poi = PointOfInterest.objects.create(
            name="Test POI",
            category="landmark",
            description="Test description",
            location=Point(-73.9857, 40.7484, srid=4326),  # Empire State Building
            address="Test Address",
            rating=4.5
        )
    
    def test_poi_creation(self):
        """Test POI creation with coordinates."""
        self.assertEqual(self.poi.name, "Test POI")
        self.assertEqual(self.poi.category, "landmark")
        self.assertEqual(self.poi.longitude, -73.9857)
        self.assertEqual(self.poi.latitude, 40.7484)
        self.assertEqual(self.poi.rating, Decimal('4.5'))
    
    def test_coordinates_property(self):
        """Test coordinates property returns correct format."""
        coords = self.poi.coordinates
        self.assertEqual(coords, (-73.9857, 40.7484))
    
    def test_string_representation(self):
        """Test string representation of POI."""
        self.assertEqual(str(self.poi), "Test POI (landmark)")


class PointOfInterestAPITest(APITestCase):
    """Test POI API endpoints."""
    
    def setUp(self):
        """Set up test POIs with known coordinates."""
        # Create test POIs around NYC
        self.pois = [
            PointOfInterest.objects.create(
                name="Times Square",
                category="landmark",
                location=Point(-74.0060, 40.7580, srid=4326),
                rating=4.2
            ),
            PointOfInterest.objects.create(
                name="Central Park",
                category="park",
                location=Point(-73.9654, 40.7829, srid=4326),
                rating=4.8
            ),
            PointOfInterest.objects.create(
                name="Empire State Building",
                category="landmark",
                location=Point(-73.9857, 40.7484, srid=4326),
                rating=4.4
            ),
            PointOfInterest.objects.create(
                name="Brooklyn Bridge",
                category="landmark",
                location=Point(-73.9969, 40.7061, srid=4326),
                rating=4.5
            ),
            PointOfInterest.objects.create(
                name="Metropolitan Museum",
                category="museum",
                location=Point(-73.9632, 40.7794, srid=4326),
                rating=4.7
            )
        ]
    
    def test_list_pois(self):
        """Test listing all POIs."""
        url = reverse('pointofinterest-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)
    
    def test_radius_search_basic(self):
        """Test basic radius search functionality."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,  # Times Square latitude
            'lng': -74.0060,  # Times Square longitude
            'radius_km': 5.0
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertIn('query', response.data)
        
        # Should find Times Square and nearby POIs
        self.assertGreater(len(response.data['results']), 0)
    
    def test_radius_search_with_category_filter(self):
        """Test radius search with category filtering."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,
            'lng': -74.0060,
            'radius_km': 10.0,
            'category': 'landmark'
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # All results should be landmarks
        for poi in response.data['results']:
            self.assertEqual(poi['category'], 'landmark')
    
    def test_radius_search_with_rating_filter(self):
        """Test radius search with minimum rating filter."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,
            'lng': -74.0060,
            'radius_km': 10.0,
            'min_rating': 4.5
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # All results should have rating >= 4.5
        for poi in response.data['results']:
            if poi['rating'] is not None:
                self.assertGreaterEqual(poi['rating'], 4.5)
    
    def test_radius_search_edge_case_40km(self):
        """Test radius search with 40km edge case."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,
            'lng': -74.0060,
            'radius_km': 40.0
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find all POIs within 40km
        self.assertEqual(len(response.data['results']), 5)
    
    def test_radius_search_invalid_coordinates(self):
        """Test radius search with invalid coordinates."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 100.0,  # Invalid latitude
            'lng': -74.0060,
            'radius_km': 5.0
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_radius_search_invalid_radius(self):
        """Test radius search with invalid radius."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,
            'lng': -74.0060,
            'radius_km': 1001.0  # Too large
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_create_poi(self):
        """Test creating a new POI."""
        url = reverse('pointofinterest-list')
        data = {
            'name': 'New Test POI',
            'category': 'restaurant',
            'description': 'A test restaurant',
            'coordinates': [-73.9857, 40.7484],
            'rating': 4.0
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PointOfInterest.objects.count(), 6)
        
        # Verify the POI was created correctly
        poi = PointOfInterest.objects.get(name='New Test POI')
        self.assertEqual(poi.category, 'restaurant')
        self.assertEqual(poi.coordinates, (-73.9857, 40.7484))
    
    def test_categories_endpoint(self):
        """Test categories endpoint."""
        url = reverse('pointofinterest-categories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('categories', response.data)
        
        # Should return all category choices
        categories = response.data['categories']
        self.assertGreater(len(categories), 0)
        
        # Check that each category has value and label
        for category in categories:
            self.assertIn('value', category)
            self.assertIn('label', category)
    
    def test_stats_endpoint(self):
        """Test stats endpoint."""
        url = reverse('pointofinterest-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_pois', response.data)
        self.assertIn('average_rating', response.data)
        self.assertIn('categories', response.data)
        
        self.assertEqual(response.data['total_pois'], 5)
    
    def test_distance_calculation(self):
        """Test that distance is calculated correctly in responses."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,
            'lng': -74.0060,
            'radius_km': 5.0
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that distance_km is present in results
        for poi in response.data['results']:
            self.assertIn('distance_km', poi)
            if poi['distance_km'] is not None:
                self.assertIsInstance(poi['distance_km'], (int, float))
                self.assertGreaterEqual(poi['distance_km'], 0)


class PointOfInterestPerformanceTest(APITestCase):
    """Test POI API performance characteristics."""
    
    def setUp(self):
        """Set up many POIs for performance testing."""
        # Create 100 random POIs for performance testing
        import random
        
        for i in range(100):
            lat = random.uniform(40.4774, 40.9176)  # NYC bounds
            lng = random.uniform(-74.2591, -73.7004)
            
            PointOfInterest.objects.create(
                name=f"Performance Test POI {i}",
                category=random.choice(['landmark', 'park', 'museum', 'restaurant']),
                location=Point(lng, lat, srid=4326),
                rating=random.uniform(3.0, 5.0)
            )
    
    def test_radius_search_performance(self):
        """Test that radius search completes within reasonable time."""
        import time
        
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,
            'lng': -74.0060,
            'radius_km': 10.0
        }
        
        start_time = time.time()
        response = self.client.get(url, params)
        end_time = time.time()
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should complete within 1 second (generous for test environment)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)
        
        print(f"Radius search completed in {execution_time:.3f} seconds")
    
    def test_large_radius_search(self):
        """Test search with large radius (40km edge case)."""
        url = reverse('pointofinterest-radius-search')
        params = {
            'lat': 40.7580,
            'lng': -74.0060,
            'radius_km': 40.0
        }
        
        response = self.client.get(url, params)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find many POIs within 40km
        self.assertGreater(len(response.data['results']), 0) 