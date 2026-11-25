"""
travel.py – how to get from one city to another.

Travel is estimated from the straight-line distance between the two cities
(their lat/lon in cities.json), with one simple rule for every route.
The rule was fitted to the Lisbon routes we had before (see docs/data_model.md).
"""
from math import asin, cos, radians, sin, sqrt

from schemas import City, Travel

EARTH_RADIUS_KM = 6371

GROUND_MAX_KM = 400        # below this distance: train; from this distance: flight
GROUND_SPEED_KMH = 90
GROUND_EUR_PER_KM = 0.12

FLIGHT_FIXED_HOURS = 0.75  # take-off, landing, taxiing
FLIGHT_SPEED_KMH = 800
FLIGHT_BASE_EUR = 50
FLIGHT_EUR_PER_KM = 0.027

def distance_km(a: City, b: City) -> float:
    """Straight-line distance between two cities in km (haversine formula)."""
    lat1, lon1 = radians(a.lat), radians(a.lon)
    lat2, lon2 = radians(b.lat), radians(b.lon)
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(h))

def travel_between(origin: City, destination: City) -> Travel:
    """How to get from origin to destination: mode, hours and price (one way)."""
    km = distance_km(origin, destination)
    if km < GROUND_MAX_KM:
        mode = "train"
        hours = km / GROUND_SPEED_KMH
        cost = km * GROUND_EUR_PER_KM
    else:
        mode = "flight"
        hours = FLIGHT_FIXED_HOURS + km / FLIGHT_SPEED_KMH
        cost = FLIGHT_BASE_EUR + km * FLIGHT_EUR_PER_KM
    return Travel(hours=round(hours, 1), cost_eur=round(cost, 2), mode=mode)