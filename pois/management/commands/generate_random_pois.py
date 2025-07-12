"""
Management command to generate random Points of Interest.
"""
import random
import math
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.contrib.gis.geos import Point
from django.utils import timezone
from pois.models import PointOfInterest


class Command(BaseCommand):
    help = 'Generate random Points of Interest around a specified location'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of POIs to generate (default: 100)'
        )
        parser.add_argument(
            '--center-lat',
            type=float,
            default=40.7580,
            help='Center latitude (default: 40.7580 - NYC)'
        )
        parser.add_argument(
            '--center-lng',
            type=float,
            default=-74.0060,
            help='Center longitude (default: -74.0060 - NYC)'
        )
        parser.add_argument(
            '--radius-km',
            type=float,
            default=10.0,
            help='Radius in kilometers to generate POIs within (default: 10.0)'
        )

    def handle(self, *args, **options):
        count = options['count']
        center_lat = options['center_lat']
        center_lng = options['center_lng']
        radius_km = options['radius_km']

        # Florida-specific POI categories and names
        florida_categories = [
            ('restaurant', [
                'Tropical Breeze Cafe', 'Orange Grove Diner', 'Palm Tree Grill',
                'Sunset Seafood', 'Florida Fresh Eats', 'Citrus Delight',
                'Beachside Bistro', 'Gator Grill', 'Sunshine Cafe',
                'Orlando Oasis', 'Central Florida Kitchen', 'Oviedo Eats'
            ]),
            ('hotel', [
                'Palm Resort', 'Sunshine Inn', 'Florida Comfort Suites',
                'Tropical Paradise Hotel', 'Central Florida Lodge',
                'Oviedo Plaza Hotel', 'Orlando Gateway Inn',
                'Florida Breeze Resort', 'Sunset Lodge'
            ]),
            ('park', [
                'Central Park', 'Oviedo Community Park', 'Florida Nature Preserve',
                'Sunshine State Park', 'Orange Grove Park', 'Palm Tree Park',
                'Citrus Memorial Park', 'Florida Wildlife Refuge'
            ]),
            ('shopping', [
                'Oviedo Mall', 'Florida Shopping Center', 'Central Market',
                'Sunshine Plaza', 'Orange Grove Shopping', 'Palm Tree Mall',
                'Florida Retail Center', 'Oviedo Marketplace'
            ]),
            ('landmark', [
                'Oviedo City Hall', 'Florida Historical Museum', 'Central Florida Monument',
                'Sunshine Memorial', 'Orange Grove Fountain', 'Palm Tree Plaza',
                'Florida Heritage Site', 'Oviedo Welcome Center'
            ]),
            ('entertainment', [
                'Florida Fun Center', 'Oviedo Entertainment', 'Sunshine Theater',
                'Central Florida Cinema', 'Orange Grove Arcade', 'Palm Tree Bowling',
                'Florida Family Fun', 'Oviedo Recreation Center'
            ]),
            ('transport', [
                'Oviedo Transit Center', 'Florida Bus Station', 'Central Florida Airport',
                'Sunshine Railway', 'Orange Grove Metro', 'Palm Tree Transport',
                'Florida Commuter Hub', 'Oviedo Station'
            ]),
            ('museum', [
                'Florida History Museum', 'Oviedo Cultural Center', 'Central Florida Gallery',
                'Sunshine Art Museum', 'Orange Grove Heritage', 'Palm Tree Exhibit',
                'Florida Science Center', 'Oviedo Museum'
            ])
        ]

        self.stdout.write(
            self.style.SUCCESS(
                f'Generating {count} POIs around ({center_lat}, {center_lng}) '
                f'within {radius_km}km radius...'
            )
        )

        created_count = 0
        for i in range(count):
            # Generate random point within radius
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, radius_km)
            
            # Convert km to degrees (approximate)
            lat_offset = distance / 111.0 * math.cos(angle)
            lng_offset = distance / (111.0 * math.cos(math.radians(center_lat))) * math.sin(angle)
            
            lat = center_lat + lat_offset
            lng = center_lng + lng_offset
            
            # Select random category and name
            category, names = random.choice(florida_categories)
            name = random.choice(names)
            
            # Add some variety to names
            if random.random() < 0.3:
                name += f" #{random.randint(1, 5)}"
            
            # Generate realistic data
            rating = round(random.uniform(3.0, 5.0), 1)
            description = f"A popular {category} in the {random.choice(['Oviedo', 'Central Florida', 'Orlando'])} area."
            
            # Generate address
            street_numbers = ['123', '456', '789', '321', '654', '987']
            street_names = ['Main St', 'Oak Ave', 'Pine Rd', 'Cedar Ln', 'Maple Dr', 'Elm St']
            street_number = random.choice(street_numbers)
            street_name = random.choice(street_names)
            address = f"{street_number} {street_name}, Oviedo, FL 32765"
            
            # Generate phone number
            area_code = random.choice(['407', '321', '689'])
            phone = f"({area_code}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
            
            # Generate website
            website = f"https://www.{name.lower().replace(' ', '')}.com"
            
            # Create POI
            poi = PointOfInterest.objects.create(
                name=name,
                category=category,
                description=description,
                location=Point(lng, lat, srid=4326),
                address=address,
                phone=phone,
                website=website,
                rating=rating
            )
            
            created_count += 1
            
            if created_count % 20 == 0:
                self.stdout.write(f'Created {created_count} POIs...')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} POIs around Oviedo, Florida!'
            )
        ) 