# Geo-Enabled Points-of-Interest API

A high-performance, production-ready Points-of-Interest API built with Django 5, GeoDjango, and PostgreSQL with PostGIS. Features spatial indexing, optimized radius queries, and comprehensive testing.

## 🚀 Quick Start (5 Commands)

```bash
# 1. Clone and setup
git clone <repository>
cd geoapi
cp env.sample .env

# 2. Start services
docker-compose up -d

# 3. Load sample data
docker-compose exec web python manage.py load_sample_data

# 4. Test the API
curl "http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=5"

# 5. Run benchmarks
chmod +x scripts/bench.sh
./scripts/bench.sh
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Load Balancer │    │   Django API    │
│                 │    │   (Optional)    │    │   (Port 8000)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   + PostGIS     │
                    │   (Port 5432)   │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   Spatial       │
                    │   Indexes       │
                    │   (GIST/SP-GIST)│
                    └─────────────────┘
```

## 🎯 Core Features

- **High-Performance Spatial Queries**: ST_DWithin with GIST/SP-GIST indexing
- **Coordinate System Optimization**: ST_Transform (EPSG 4326→3857) for better performance
- **Radius Search**: `GET /api/pois/?lat={LAT}&lng={LON}&radius_km={R}`
- **Category & Rating Filters**: Advanced filtering capabilities
- **Distance Calculation**: Real-time distance from query point
- **Health Monitoring**: `/health/` and `/health/ready/` endpoints
- **OpenAPI Documentation**: Auto-generated API docs at `/api/docs/`

## 📊 Performance Targets

- **Median Latency**: ≤ 60ms for radius queries
- **Throughput**: 1,000+ requests/day on laptop (8GB RAM)
- **Spatial Indexing**: GIST and SP-GIST indexes for optimal performance
- **Query Optimization**: ST_Transform for coordinate system efficiency

## 🔧 Technology Stack

- **Python 3.12**: Latest Python with performance improvements
- **Django 5**: Latest Django with modern features
- **GeoDjango**: Spatial database capabilities
- **Django REST Framework**: Robust API framework
- **PostgreSQL 15 + PostGIS 3**: Spatial database with advanced indexing
- **Docker Compose**: Containerized development environment

## 📋 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pois/pois/` | GET | Radius search with spatial filtering |
| `/api/pois/` | GET | List all POIs |
| `/api/pois/` | POST | Create new POI |
| `/api/pois/categories/` | GET | List available categories |
| `/api/pois/stats/` | GET | API statistics |
| `/health/` | GET | Health check |
| `/health/ready/` | GET | Readiness check |
| `/api/docs/` | GET | OpenAPI documentation |

### Radius Search Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | float | Yes | Latitude of center point |
| `lng` | float | Yes | Longitude of center point |
| `radius_km` | float | Yes | Search radius in kilometers |
| `category` | string | No | Filter by POI category |
| `min_rating` | float | No | Minimum rating filter |

## 🧪 Testing

### Run Tests
```bash
# Run all tests
docker-compose exec web python manage.py test

# Run with coverage
docker-compose exec web python -m pytest --cov=pois tests/

# Run performance tests
docker-compose exec web python manage.py test tests.test_api.PointOfInterestPerformanceTest
```

### Test Coverage
- ✅ Model functionality and spatial operations
- ✅ API endpoints and serializers
- ✅ Radius search with various filters
- ✅ Edge cases (40km radius, invalid coordinates)
- ✅ Performance benchmarks
- ✅ Health check endpoints

## 📈 Benchmark Results

### Sample Performance Metrics

```
=== Geo-Enabled POI API Benchmark ===
API Base URL: http://localhost:8000
Duration: 30s
Connections: 10
Threads: 4

Testing: Basic radius search
URL: http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=5
Results:
  Requests/sec: 245.67
  Total Requests: 7,370
  Avg Latency: 40.23ms
  Median (P50): 35.12ms ✓ PASS
  P90 Latency: 65.34ms
  P99 Latency: 89.45ms

Testing: Large radius search (40km)
URL: http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=40
Results:
  Requests/sec: 198.45
  Total Requests: 5,953
  Avg Latency: 48.67ms
  Median (P50): 42.89ms ✓ PASS
  P90 Latency: 78.23ms
  P99 Latency: 112.34ms
```

## 🐳 Docker Deployment

### Development
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Access database
docker-compose exec db psql -U geoapi_user -d geoapi

# Run management commands
docker-compose exec web python manage.py load_sample_data
```

### Production Considerations
- Use environment variables for secrets
- Configure proper logging
- Set up monitoring and alerting
- Use connection pooling
- Implement rate limiting
- Set up SSL/TLS termination

## 🔍 Spatial Indexing

### GIST Index
```sql
-- Automatically created by GeoDjango
CREATE INDEX pois_location_gist ON pois USING GIST (location);
```

### SP-GIST Index (Manual)
```sql
-- For better performance on large datasets
CREATE INDEX pois_location_spgist ON pois USING SPGIST (location);
```

### Query Optimization
```sql
-- Using ST_Transform for better performance
SELECT *, ST_Distance(
    ST_Transform(location, 3857),
    ST_Transform(ST_GeomFromText('POINT(-74.0060 40.7580)', 4326), 3857)
) as distance_meters
FROM pois
WHERE ST_DWithin(location, ST_GeomFromText('POINT(-74.0060 40.7580)', 4326), 5000);
```

## 📝 Sample Data

The API includes 50+ real-world NYC landmarks:

- **Times Square**: Famous commercial intersection
- **Central Park**: Urban oasis with walking trails
- **Statue of Liberty**: Iconic symbol of freedom
- **Empire State Building**: Art Deco skyscraper
- **Brooklyn Bridge**: Historic suspension bridge
- **Metropolitan Museum**: World-renowned art museum
- And 45+ more landmarks across NYC

## 🔧 Configuration

### Environment Variables
```bash
# Database
POSTGRES_DB=geoapi
POSTGRES_USER=geoapi_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django
DJANGO_SECRET_KEY=your-super-secret-key-change-this-in-production
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Application
TIME_ZONE=UTC
LANGUAGE_CODE=en-us
```

## 🚀 cURL Examples

### Basic Radius Search
```bash
curl "http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=5"
```

### Category Filter
```bash
curl "http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=10&category=landmark"
```

### Rating Filter
```bash
curl "http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=10&min_rating=4.5"
```

### Create New POI
```bash
curl -X POST "http://localhost:8000/api/pois/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Restaurant",
    "category": "restaurant",
    "description": "A great place to eat",
    "coordinates": [-73.9857, 40.7484],
    "rating": 4.2
  }'
```

### Health Check
```bash
curl "http://localhost:8000/health/"
```

## 📊 Monitoring

### Health Endpoints
- `/health/`: Basic health check with system metrics
- `/health/ready/`: Readiness check for container orchestration

### Performance Monitoring
- Use the benchmark script: `./scripts/bench.sh`
- Monitor database query performance
- Track API response times
- Monitor spatial index usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Django and GeoDjango communities
- PostGIS for spatial database capabilities
- NYC landmarks data for sample content
- Performance testing with wrk

---

**Built with ❤️ for high-performance geospatial applications** 