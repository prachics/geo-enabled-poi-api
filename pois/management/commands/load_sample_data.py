"""
Django management command to load sample POI data.
"""
import csv
import random
import os
from django.core.management.base import BaseCommand
from django.contrib.gis.geos import Point
from django.utils import timezone
from pois.models import PointOfInterest


class Command(BaseCommand):
    help = 'Load sample POI data from CSV file or generate random NYC landmarks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            help='Path to CSV file with POI data'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=50,
            help='Number of random POIs to generate if no CSV file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing POI data before loading'
        )
    
    def handle(self, *args, **options):
        csv_file = options.get('csv_file')
        count = options.get('count')
        clear = options.get('clear')
        
        if clear:
            self.stdout.write('Clearing existing POI data...')
            PointOfInterest.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared'))
        
        if csv_file and os.path.exists(csv_file):
            self.load_from_csv(csv_file)
        else:
            self.generate_random_pois(count)
    
    def load_from_csv(self, csv_file):
        """Load POI data from CSV file."""
        self.stdout.write(f'Loading POI data from {csv_file}...')
        
        created_count = 0
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Parse coordinates
                    lng = float(row.get('longitude', 0))
                    lat = float(row.get('latitude', 0))
                    
                    # Create Point object
                    location = Point(lng, lat, srid=4326)
                    
                    # Create POI
                    poi, created = PointOfInterest.objects.get_or_create(
                        name=row.get('name', 'Unknown'),
                        location=location,
                        defaults={
                            'category': row.get('category', 'landmark'),
                            'description': row.get('description', ''),
                            'address': row.get('address', ''),
                            'phone': row.get('phone', ''),
                            'website': row.get('website', ''),
                            'rating': float(row.get('rating', 0)) if row.get('rating') else None,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'Error loading row: {row} - {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully loaded {created_count} POIs from CSV')
        )
    
    def generate_random_pois(self, count):
        """Generate random NYC landmarks."""
        self.stdout.write(f'Generating {count} random NYC landmarks...')
        
        # NYC landmarks with real coordinates
        nyc_landmarks = [
            {
                'name': 'Times Square',
                'category': 'landmark',
                'description': 'Famous commercial intersection and tourist destination',
                'address': 'Manhattan, NY 10036',
                'coordinates': (-74.0060, 40.7580),
                'rating': 4.2
            },
            {
                'name': 'Central Park',
                'category': 'park',
                'description': 'Urban oasis with walking trails and recreational facilities',
                'address': 'Manhattan, NY 10024',
                'coordinates': (-73.9654, 40.7829),
                'rating': 4.8
            },
            {
                'name': 'Statue of Liberty',
                'category': 'landmark',
                'description': 'Iconic symbol of freedom and democracy',
                'address': 'Liberty Island, NY 10004',
                'coordinates': (-74.0445, 40.6892),
                'rating': 4.6
            },
            {
                'name': 'Empire State Building',
                'category': 'landmark',
                'description': 'Art Deco skyscraper and observation deck',
                'address': '350 5th Ave, NY 10118',
                'coordinates': (-73.9857, 40.7484),
                'rating': 4.4
            },
            {
                'name': 'Brooklyn Bridge',
                'category': 'landmark',
                'description': 'Historic suspension bridge connecting Manhattan and Brooklyn',
                'address': 'Brooklyn Bridge, NY 10038',
                'coordinates': (-73.9969, 40.7061),
                'rating': 4.5
            },
            {
                'name': 'Metropolitan Museum of Art',
                'category': 'museum',
                'description': 'World-renowned art museum with extensive collections',
                'address': '1000 5th Ave, NY 10028',
                'coordinates': (-73.9632, 40.7794),
                'rating': 4.7
            },
            {
                'name': 'Broadway',
                'category': 'entertainment',
                'description': 'Famous theater district and entertainment hub',
                'address': 'Manhattan, NY 10036',
                'coordinates': (-73.9857, 40.7589),
                'rating': 4.3
            },
            {
                'name': 'High Line',
                'category': 'park',
                'description': 'Elevated park built on former railway tracks',
                'address': 'Manhattan, NY 10011',
                'coordinates': (-74.0060, 40.7484),
                'rating': 4.6
            },
            {
                'name': 'Wall Street',
                'category': 'landmark',
                'description': 'Financial district and historic trading center',
                'address': 'Manhattan, NY 10005',
                'coordinates': (-74.0109, 40.7064),
                'rating': 4.1
            },
            {
                'name': 'Rockefeller Center',
                'category': 'entertainment',
                'description': 'Complex of commercial buildings and entertainment venues',
                'address': '45 Rockefeller Plaza, NY 10111',
                'coordinates': (-73.9787, 40.7587),
                'rating': 4.4
            }
        ]
        
        # Categories for random generation
        categories = [choice[0] for choice in PointOfInterest.CATEGORY_CHOICES]
        
        # NYC bounding box (approximate)
        nyc_bounds = {
            'min_lat': 40.4774,
            'max_lat': 40.9176,
            'min_lng': -74.2591,
            'max_lng': -73.7004
        }
        
        created_count = 0
        
        # First, create the predefined landmarks
        for landmark in nyc_landmarks:
            lng, lat = landmark['coordinates']
            location = Point(lng, lat, srid=4326)
            
            poi, created = PointOfInterest.objects.get_or_create(
                name=landmark['name'],
                location=location,
                defaults={
                    'category': landmark['category'],
                    'description': landmark['description'],
                    'address': landmark['address'],
                    'rating': landmark['rating'],
                }
            )
            
            if created:
                created_count += 1
        
        # Generate additional random POIs
        remaining_count = count - len(nyc_landmarks)
        if remaining_count > 0:
            for i in range(remaining_count):
                # Generate random coordinates within NYC bounds
                lat = random.uniform(nyc_bounds['min_lat'], nyc_bounds['max_lat'])
                lng = random.uniform(nyc_bounds['min_lng'], nyc_bounds['max_lng'])
                
                location = Point(lng, lat, srid=4326)
                
                # Generate random POI data
                category = random.choice(categories)
                name = f"Random {category.title()} {i+1}"
                description = f"A randomly generated {category} in NYC"
                rating = round(random.uniform(3.0, 5.0), 1)
                
                poi = PointOfInterest.objects.create(
                    name=name,
                    category=category,
                    description=description,
                    location=location,
                    rating=rating,
                    address=f"Random Address {i+1}, NYC"
                )
                
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} POIs')
        ) 