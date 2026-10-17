-- wrk script: a random center near Times Square per request, so no two requests share a cached URL.
local radius = os.getenv("RADIUS_KM") or "5"
local counter = 0

function setup(thread)
  counter = counter + 1
  thread:set("seed", counter)
end

function init(args)
  math.randomseed(os.time() + seed)
end

function request()
  local lat = 40.7580 + (math.random() - 0.5) * 0.04
  local lng = -74.0060 + (math.random() - 0.5) * 0.05
  return wrk.format("GET", string.format("/api/pois/pois/?lat=%.6f&lng=%.6f&radius_km=%s", lat, lng, radius))
end
