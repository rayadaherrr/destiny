import json
from pathlib import Path

import streamlit as st

import config
from extraction import extract_request
from pricing import estimate_cost
from schemas import City, Tag, Turn, Weather

st.set_page_config(page_title="Destiny", page_icon="✈️", layout="centered")
st.title("Destiny")
st.caption("Tell me who is going, when, your budget and what you like.")

# --- Load the cities ---
# app.py is in the main folder, so only ONE .parent (the page file needed two)
CITIES_FILE = Path(__file__).parent / "data" / "cities.json"


def load_cities():
    with open(CITIES_FILE, encoding="utf-8") as f:
        return [City.model_validate(c) for c in json.load(f)]


cities = load_cities()
cities_by_id = {city.id: city for city in cities}

# --- Key check ---
if not config.API_KEY:
    st.error("No API key found.")
    st.markdown(
        "Create a `.env` file from `.env.example` and fill in the "
        "`GOOGLE_API_KEY` line with your key from "
        "[aistudio.google.com/apikey](https://aistudio.google.com/apikey)."
    )
    st.stop()


# --- Show what Gemini understood, in one line ---
def show_request(request):
    # "1 person" but "3 people"
    if request.people == 1:                                   # ← NEW
        word = "person"                                       # ← NEW
    else:                                                     # ← NEW
        word = "people"                                       # ← NEW
    parts = [f"{request.people} {word}"]                      # ← CHANGED

    # Only mention the starting city if it's not the normal one (Lisbon)
    if request.origin != "lisbon":                            # ← NEW
        parts.append(f"from {request.origin.title()}")        # ← NEW
    if request.destination:
        parts.append(f"to {request.destination.title()}")

    if request.start_date and request.end_date:
        parts.append(f"{request.start_date:%d %b} – {request.end_date:%d %b %Y}")
    else:
        parts.append("no dates (rough 5-night estimate)")
    if request.budget_per_person_eur:
        parts.append(f"€{request.budget_per_person_eur:.0f} each")
    if request.interests:
        parts.append(", ".join(request.interests))
    if request.cheaper_than:
        parts.append(f"cheaper than {request.cheaper_than.title()}")

    if request.max_travel_hours:                              # ← NEW
        parts.append(f"max {request.max_travel_hours:g} h away")  # ← NEW
    if request.climate_wanted:                                # ← NEW
        parts.append(f"{request.climate_wanted} weather")    # ← NEW

    st.markdown("**I understood:** " + " · ".join(parts))

# --- Editable "I understood" boxes (only for the latest message) ---
def edit_request(turn, i):
    r = turn.request
    city_ids = list(cities_by_id)

    st.markdown("**I understood** — check it and change anything that's wrong:")
    with st.form(f"edit_{i}"):
        c1, c2 = st.columns(2)
        people = c1.number_input("People", min_value=1, max_value=20,
                                 value=r.people, key=f"people_{i}")
        budget = c2.number_input("Budget per person (€)", min_value=0.0, step=50.0,
                                 value=r.budget_per_person_eur, placeholder="no budget",
                                 key=f"budget_{i}")

        c3, c4 = st.columns(2)
        start = c3.date_input("Start date", value=r.start_date, key=f"start_{i}")
        end = c4.date_input("End date", value=r.end_date, key=f"end_{i}")

        interests = st.multiselect("Interests", options=list(Tag.__args__),
                                   default=r.interests, key=f"interests_{i}")

        c5, c6 = st.columns(2)
        max_hours = c5.number_input("Max travel hours (one way)", min_value=0.5, step=0.5,
                                    value=r.max_travel_hours, placeholder="no limit",
                                    key=f"hours_{i}")
        climate_options = [None] + list(Weather.__args__)
        climate = c6.selectbox("Weather", climate_options,
                               index=climate_options.index(r.climate_wanted),
                               format_func=lambda x: "any" if x is None else x,
                               key=f"climate_{i}")

        c7, c8 = st.columns(2)
        origin_options = ["lisbon"] + city_ids
        if r.origin not in origin_options:
            origin_options.append(r.origin)
        origin = c7.selectbox("Starting from", origin_options,
                              index=origin_options.index(r.origin),
                              format_func=str.title, key=f"origin_{i}")
        cheaper_options = [None] + city_ids
        if r.cheaper_than not in cheaper_options:
            cheaper_options.append(r.cheaper_than)
        cheaper = c8.selectbox("Cheaper than", cheaper_options,
                               index=cheaper_options.index(r.cheaper_than),
                               format_func=lambda x: "—" if x is None else x.title(),
                               key=f"cheaper_{i}")

        submitted = st.form_submit_button("Update results")

    if submitted:
        if (start is None) != (end is None):
            st.warning("Pick both dates, or leave both empty.")
            return
        if start and end and end <= start:
            st.warning("The end date must be after the start date.")
            return
        turn.request = r.model_copy(update={
            "people": int(people),
            "budget_per_person_eur": budget,
            "start_date": start,
            "end_date": end,
            "interests": interests,
            "max_travel_hours": max_hours,
            "climate_wanted": climate,
            "origin": origin,
            "cheaper_than": cheaper,
        })
        st.rerun()


# --- One card per city (same as pages/1_Trip_results.py) ---
# --- One card per city (same as pages/1_Trip_results.py) ---
def show_card(e, budget):
    city = cities_by_id[e.city_id]
    with st.container(border=True):
        st.subheader(e.city_name)
        st.caption(city.description)
        if e.people == 1:
            word = "person"
        else:
            word = "people"
        st.write(f"{e.nights} nights · {e.people} {word} · {e.season} season · tags: {', '.join(city.tags)}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Travel", f"€{e.travel_eur:.0f}")
        c2.metric("Stay", f"€{e.stay_eur:.0f}")
        c3.metric("Food", f"€{e.food_eur:.0f}")
        c4.metric("Activities", f"€{e.activities_eur:.0f}")

        if budget is None:
            st.info(f"Total about €{e.total_eur:.0f} per person")
        elif e.total_eur <= budget:
            st.success(f"Total about €{e.total_eur:.0f} per person: fits your budget")
        else:
            st.warning(f"Total about €{e.total_eur:.0f} per person: €{e.total_eur - budget:.0f} over budget")


# --- Price every city (pricing.py does the maths, not Gemini) ---
def show_results(request):
    estimates = [estimate_cost(city, request) for city in cities]
    estimates = sorted([e for e in estimates if e is not None], key=lambda e: e.total_eur)
    if not estimates:
        st.info("No cities found from that starting point yet.")
    for e in estimates:
        show_card(e, request.budget_per_person_eur)


# --- Chat history: kept between interactions ---
if "history" not in st.session_state:
    st.session_state.history = []

history = st.session_state.history
for i, turn in enumerate(history):
    with st.chat_message("user"):
        st.markdown(turn.message)
    with st.chat_message("assistant"):
        if i == len(history) - 1:
            edit_request(turn, i)              # latest message: editable boxes
        else:
            show_request(turn.request)         # older messages: read-only line
        show_results(turn.request)
        

# --- New message: user -> Gemini -> saved -> page redraws ---
message = st.chat_input("Where do you want to go?")

if message:
    with st.chat_message("user"):
        st.markdown(message)
    try:
        with st.spinner("Reading your request..."):
            request = extract_request(message)
    except Exception as e:
        st.error(f"Gemini call failed: {type(e).__name__}")
        st.caption(str(e)[:300])
        st.stop()
    st.session_state.history.append(Turn(message=message, request=request))
    st.rerun()

# --- Sidebar ---
with st.sidebar:
    st.caption(f"Model: `{config.MODEL}`")
    if st.button("Clear conversation"):
        st.session_state.history = []
        st.rerun()