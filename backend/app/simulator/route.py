"""Dallas → Chicago GPS waypoints along I-35 / I-44 / I-55 corridor."""

import numpy as np
from app.models import LatLng

# Key cities along the route with approximate lat/lng
_CONTROL_POINTS = [
    (32.7767, -96.7970),   # Dallas, TX
    (33.2148, -97.1331),   # Denton, TX
    (33.9137, -97.1430),   # Gainesville, TX
    (34.1748, -97.1436),   # Ardmore, OK
    (34.6009, -97.0956),   # Pauls Valley, OK
    (35.0078, -97.0929),   # Norman, OK
    (35.4676, -97.5164),   # Oklahoma City, OK
    (35.7476, -97.6324),   # Edmond, OK
    (36.1199, -97.0584),   # Stillwater, OK (I-35 area)
    (36.4072, -97.8784),   # Enid area, OK
    (36.7281, -97.0851),   # Ponca City, OK
    (37.0842, -97.0390),   # Near KS border
    (37.6872, -97.3301),   # Wichita, KS
    (38.0608, -97.9298),   # Hutchinson, KS
    (38.3614, -97.6645),   # McPherson, KS
    (38.7509, -97.2281),   # Salina area, KS
    (38.8814, -96.6005),   # Emporia, KS
    (39.0997, -94.5786),   # Kansas City, MO
    (39.2507, -93.8488),   # Lexington, MO area
    (39.5168, -92.8399),   # Moberly, MO area
    (39.7817, -91.9493),   # Hannibal, MO area
    (39.7990, -89.6440),   # Springfield, IL
    (40.1164, -89.1285),   # Bloomington, IL area
    (40.6936, -89.5890),   # Peoria, IL area
    (41.0534, -88.8148),   # Pontiac, IL area
    (41.5250, -88.0817),   # Joliet, IL
    (41.8781, -87.6298),   # Chicago, IL
]


def _interpolate_points(points: list[tuple[float, float]], n: int) -> list[LatLng]:
    """Interpolate between control points to create smooth route."""
    lats = [p[0] for p in points]
    lngs = [p[1] for p in points]

    # Parameter t from 0..1 for each control point
    dists = [0.0]
    for i in range(1, len(points)):
        d = ((lats[i] - lats[i - 1]) ** 2 + (lngs[i] - lngs[i - 1]) ** 2) ** 0.5
        dists.append(dists[-1] + d)
    total = dists[-1]
    t_control = [d / total for d in dists]

    t_interp = np.linspace(0, 1, n)
    interp_lats = np.interp(t_interp, t_control, lats)
    interp_lngs = np.interp(t_interp, t_control, lngs)

    return [LatLng(lat=float(la), lng=float(ln)) for la, ln in zip(interp_lats, interp_lngs)]


# ~200 waypoints along the route
ROUTE_WAYPOINTS: list[LatLng] = _interpolate_points(_CONTROL_POINTS, 200)

TOTAL_WAYPOINTS = len(ROUTE_WAYPOINTS)

# Approximate total distance in miles (Dallas to Chicago ~ 920 miles)
TOTAL_DISTANCE_MILES = 920.0


def get_waypoint(index: int) -> LatLng:
    """Get waypoint at index, clamped to valid range."""
    idx = max(0, min(index, TOTAL_WAYPOINTS - 1))
    return ROUTE_WAYPOINTS[idx]


def get_route_as_latlng_list() -> list[dict]:
    """Return route as list of {lat, lng} dicts for frontend."""
    return [{"lat": wp.lat, "lng": wp.lng} for wp in ROUTE_WAYPOINTS]
