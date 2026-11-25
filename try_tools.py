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

# --- Part 4: the agent's view (DECLARATIONS + run_tool), still without Gemini
from tools import DECLARATIONS, run_tool

print()
print("tools Gemini will see:", [d["name"] for d in DECLARATIONS])


def say_no(question):          # stands in for the user; no tool asks yet
    return False


# 1. A call like Gemini would send: plain JSON, dates as text
result = run_tool("find_trips", {
    "origin": "lisbon", "destination": None, "start_date": "2027-06-10", "end_date": "2027-06-15",
    "people": 3, "budget_per_person_eur": 500, "max_travel_hours": None,
    "interests": ["food"], "climate_wanted": None, "cheaper_than": "barcelona",
}, say_no)
print("1.", result["found"], [t["city_name"] for t in result["trips"]])

# 2. A tool that doesn't exist
print("2.", run_tool("book_flight", {}, say_no))

# 3. Arguments missing
print("3.", run_tool("find_trips", {"people": 3}, say_no))

# --- Any starting city (travel.py)
print()
from_madrid = request.model_copy(update={"origin": "madrid", "cheaper_than": None})
result = find_trips(from_madrid)
print("4. from Madrid:", result["found"], [t["city_name"] for t in result.get("trips", [])])


from_ibiza = request.model_copy(update={"origin": "ibiza", "cheaper_than": None})
print("5. from Ibiza:", find_trips(from_ibiza))

from_paris = request.model_copy(update={"origin": "paris", "cheaper_than": None})
result = find_trips(from_paris)
print("6. from Paris:", result["found"], [t["city_name"] for t in result.get("trips", [])][:5])

# --- Part 3: tools for the logged-in user's past trips
print()
import db
alex = db.login("alex", "demo123")       # the demo user from seed.py; gives back his user id
print("alex's user id:", alex)
print("7. list alex's trips:", run_tool("list_my_trips", {}, say_no, user_id=alex))
print("8. nobody logged in:", run_tool("list_my_trips", {}, say_no))