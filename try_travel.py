"""Check travel.py by hand: travel between a few cities, without Gemini or the app."""
from tools import load_cities
from travel import distance_km, travel_between

cities = {city.id: city for city in load_cities()}

for start, end in [("lisbon", "porto"), ("lisbon", "rome"), ("madrid", "rome"),
                   ("valencia", "barcelona"), ("rome", "lisbon")]:
    a, b = cities[start], cities[end]
    km = distance_km(a, b)
    print(f"{a.name} -> {b.name}: {km:.0f} km, {travel_between(a, b)}")