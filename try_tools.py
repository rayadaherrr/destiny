"""
Quick check of the tools, without Gemini or the agent.

Run with:  uv run python try_tools.py
"""
import datetime

from schemas import TripRequest
from tools import find_trips

# A request written by hand: what Gemini would fill in for
# "Me, Alex and Raya, 10 to 15 June, 500 euros each, great food, cheaper than Barcelona"
request = TripRequest(
    origin="lisbon",
    destination=None,
    start_date=datetime.date(2027, 6, 10),
    end_date=datetime.date(2027, 6, 15),
    people=3,
    budget_per_person_eur=500,
    max_travel_hours=None,
    interests=["food"],
    climate_wanted=None,
    cheaper_than="barcelona",
)

result = find_trips(request)

print("found:", result["found"])
for trip in result.get("trips", []):
    print(f"{trip['city_name']:10} €{trip['total_eur']:.0f}  fits budget: {trip['fits_budget']}")