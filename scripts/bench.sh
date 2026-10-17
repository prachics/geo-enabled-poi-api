#!/usr/bin/env bash
# Reproduce the README benchmark. Requires wrk (brew install wrk / apt install wrk).
#
#   DJANGO_DEBUG=False docker compose up -d     # DEBUG=True logs every SQL query, which skews latency
#   docker compose exec web python manage.py generate_random_pois --count 100000 --radius-km 50
#   ./scripts/bench.sh
#
# Two cases per radius:
#   uncached  every request uses a different random center within ~2 km of Times Square, so each one misses the
#             5-minute response cache and runs the spatial query (ST_DWithin + distance sort)
#   cached    the same URL every time, so after the first request it is served from the response cache
set -euo pipefail
BASE=${BASE:-http://localhost:8000}
DURATION=${DURATION:-30s}
HERE=$(cd "$(dirname "$0")" && pwd)

for R in 5 40; do
  echo "== radius_km=$R, uncached =="
  RADIUS_KM=$R wrk -t4 -c10 -d"$DURATION" --latency -s "$HERE/random_center.lua" "$BASE"
  echo "== radius_km=$R, cached =="
  wrk -t4 -c10 -d"$DURATION" --latency "$BASE/api/pois/pois/?lat=40.7580&lng=-74.0060&radius_km=$R"
done
