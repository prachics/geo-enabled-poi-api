# Geo-Enabled Points-of-Interest API

A REST API and map UI for finding points of interest within a radius, built with Django 5, Django REST Framework, GeoDjango, and PostgreSQL 15 + PostGIS 3.

<p align="center">
  <img src="UI.png" alt="Map UI for radius search" width="900"/>
</p>

Radius search runs as an index-backed `ST_DWithin` query on a PostGIS **geography** column, so distances are in meters and the GIST spatial index is used. Results include the distance from the query point and can be filtered by category and minimum rating.

---

## Quickstart

Requires Docker.

```bash
git clone https://github.com/prachics/geo-enabled-poi-api.git
cd geo-enabled-poi-api
docker compose up -d                                        # Postgres + PostGIS, Django on :8000
docker compose exec web python manage.py load_sample_data   # 50 random POIs around NYC

curl "http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=5"
```

Map UI: `http://localhost:8000/` · Interactive API docs: `http://localhost:8000/api/docs/`

`env.sample` lists the settings to change for a production deployment (secret key, `DEBUG`, allowed hosts).

---

## Results

Measured with `scripts/bench.sh` (wrk, 4 threads, 10 connections, 30 s per case) on an Apple M4 Pro (24 GB) in Docker
Desktop, Django development server with `DJANGO_DEBUG=False`, against 100,000 POIs generated within 50 km of Times
Square (about 10,000 of them within 5 km of the query center).

| Query | Requests/sec | Median latency | p90 | p99 |
|---|---:|---:|---:|---:|
| 5 km radius, uncached | 60 | 138 ms | 176 ms | 283 ms |
| 40 km radius, uncached | 14 | 671 ms | 715 ms | 852 ms |
| 5 km radius, cached | 1,485 | 4.6 ms | 8.1 ms | 160 ms |
| 40 km radius, cached | 1,417 | 4.7 ms | 9.4 ms | 1.26 s |

*Uncached*: every request uses a different random center within ~2 km of Times Square, so it misses the 5-minute
response cache and runs the spatial query. *Cached*: the same URL repeatedly; after the first request it is served from
Django's response cache.

Reproduce:

```bash
DJANGO_DEBUG=False docker compose up -d   # DEBUG=True logs every SQL query, which skews latency
docker compose exec web python manage.py generate_random_pois --count 100000 --radius-km 50
./scripts/bench.sh                         # BASE=http://localhost:8000 by default
```

---

## Design notes

- **Geography, not geometry.** Coordinates are stored as a PostGIS `geography(Point, 4326)`, so `ST_DWithin` takes a radius in meters directly. Storing them as a 4326 *geometry* would make distances degrees, which is the most common radius-search bug.
- **Index-backed filtering.** GeoDjango creates a GIST index on the location column; the radius filter runs before distance sorting so the index does the narrowing.
- **Composite indexes** on `(category, created_at)` and `(rating, category)` support the optional filters.
- **Where the time goes.** `EXPLAIN ANALYZE` on the 5 km query: the GIST index scan takes ~3 ms; computing exact
  geodesic distances for the ~10,000 matching rows to return the nearest 100 takes most of the ~100 ms. Ordering by the
  KNN operator (`<->`) didn't help here, because the planner still sorts the filtered rows.

---

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/pois/pois/` | GET | Radius search (`lat`, `lng`, `radius_km`; optional `category`, `min_rating`) |
| `/api/pois/` | GET / POST | List or create POIs |
| `/api/pois/categories/` | GET | Available categories |
| `/api/pois/stats/` | GET | Dataset statistics |
| `/health/`, `/health/ready/` | GET | Liveness and readiness checks |
| `/api/docs/` | GET | OpenAPI documentation |

Example:

```bash
curl "http://localhost:8000/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=10&category=landmark&min_rating=4.5"
```

---

## Testing

```bash
docker compose exec web python -m pytest -q
```

19 tests: models and spatial operations, API endpoints and serializers, radius search with filters (including a
regression test that a point 50 km away is not returned by a 5 km search), invalid coordinates and radius, and health
checks.

---

## Stack

| Layer | Choice |
|---|---|
| API | Django 5, Django REST Framework |
| Spatial | GeoDjango, PostgreSQL 15 + PostGIS 3 |
| Runtime | Python 3.12, Docker Compose |
| CI | GitHub Actions |
| Load testing | wrk |

## License

MIT
