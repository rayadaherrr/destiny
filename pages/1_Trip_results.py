import datetime
import json
from pathlib import Path

import streamlit as st

from pricing import estimate_cost
from schemas import City, Tag, TripRequest

st.title("Find a trip")
CITIES_FILE = Path(__file__).parent.parent / "data" / "cities.json"


def load_cities():
    with open(CITIES_FILE, encoding="utf-8") as f:
        return [City.model_validate(c) for c in json.load(f)]


cities = load_cities()

# --- The user's choices (later, the chatbot fills these in instead) ---
today = datetime.date.today()
col1, col2 = st.columns(2)
start = col1.date_input("Start date", value=today + datetime.timedelta(days=30))
end = col2.date_input("End date", value=start + datetime.timedelta(days=5))
people = st.number_input("How many people?", min_value=1, max_value=10, value=3)
budget = st.number_input("Budget per person (€)", min_value=0, max_value=5000, value=500, step=50)
interests = st.multiselect("Interests", options=list(Tag.__args__))

if end <= start:
    st.error("The end date must be after the start date.")
    st.stop()

request = TripRequest(
    origin="lisbon",
    destination=None,
    start_date=start,
    end_date=end,
    people=int(people),
    budget_per_person_eur=float(budget),
    max_travel_hours=None,
    interests=interests,
    climate_wanted=None,
    cheaper_than=None,
)

# --- Price every city, cheapest first ---
estimates = [estimate_cost(city, request) for city in cities]
estimates = sorted([e for e in estimates if e is not None], key=lambda e: e.total_eur)

# --- One card per city ---
for e in estimates:
    city = next(c for c in cities if c.id == e.city_id)
    with st.container(border=True):
        st.subheader(e.city_name)
        st.caption(city.description)
        st.write(f"{e.nights} nights · {e.people} people · {e.season} season · tags: {', '.join(city.tags)}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Travel", f"€{e.travel_eur:.0f}")
        c2.metric("Stay", f"€{e.stay_eur:.0f}")
        c3.metric("Food", f"€{e.food_eur:.0f}")
        c4.metric("Activities", f"€{e.activities_eur:.0f}")

        if e.total_eur <= budget:
            st.success(f"Total about €{e.total_eur:.0f} per person: fits your budget")
        else:
            st.warning(f"Total about €{e.total_eur:.0f} per person: €{e.total_eur - budget:.0f} over budget")