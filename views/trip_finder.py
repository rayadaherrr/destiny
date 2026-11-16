import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import config
import db
from extraction import extract_request
from geo import COORDS
from schemas import TripRequest
from tools import find_trips, load_cities

st.title("Trip finder")

cities = load_cities()
by_id = {c.id: c for c in cities}
my_id = st.session_state.user_id


def my_rating(city_id):
    """Average of the ratings the logged-in user gave this city, or None."""
    ratings = [t["rating"] for t in db.user_trips(my_id) if t["city_id"] == city_id]
    return sum(ratings) / len(ratings) if ratings else None


def show_card(t, budget):
    city = by_id[t["city_id"]]
    with st.container(border=True):
        st.subheader(t["city_name"])
        st.caption(city.description)
        word = "person" if t["people"] == 1 else "people"
        st.write(f"{t['nights']} nights · {t['people']} {word} · {t['season']} season · "
                 f"{t['travel_hours']:g} h by {t['travel_mode']} · tags: {', '.join(t['tags'])}")
        mine = my_rating(t["city_id"])
        if mine:
            st.caption(f"⭐ You rated {t['city_name']} {mine:.0f}/5 on a past trip")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Travel", f"€{t['travel_eur']:.0f}")
        c2.metric("Stay", f"€{t['stay_eur']:.0f}")
        c3.metric("Food", f"€{t['food_eur']:.0f}")
        c4.metric("Activities", f"€{t['activities_eur']:.0f}")

        total = t["total_eur"]
        if budget is None:
            st.info(f"Total about €{total:.0f} per person")
        elif total <= budget:
            st.success(f"Total about €{total:.0f} per person: fits your budget")
        else:
            st.warning(f"Total about €{total:.0f} per person: €{total - budget:.0f} over budget")


def show_trips(request):
    """Search with the same tool the agent will use, then draw one card per result."""
    result = find_trips(request)
    if not result["found"]:
        for problem in result.get("problems", []):
            st.warning(problem)
        if not result.get("problems"):
            st.info("No city matches every limit. Try relaxing one.")
        return
    for trip in result["trips"]:
        show_card(trip, request.budget_per_person_eur)


def show_understood(r):
    parts = [f"{r.people} {'person' if r.people == 1 else 'people'}"]
    if r.destination:
        parts.append(f"to {r.destination.title()}")
    if r.start_date and r.end_date:
        parts.append(f"{r.start_date:%d %b} – {r.end_date:%d %b %Y}")
    else:
        parts.append("no dates (rough 5-night estimate)")
    if r.budget_per_person_eur:
        parts.append(f"€{r.budget_per_person_eur:.0f} each")
    if r.interests:
        parts.append(", ".join(r.interests))
    if r.max_travel_hours:
        parts.append(f"max {r.max_travel_hours:g} h away")
    if r.cheaper_than:
        parts.append(f"cheaper than {r.cheaper_than.title()}")
    st.markdown("**I understood:** " + " · ".join(parts))


tab_prompt, tab_map = st.tabs(["✍️ Describe your trip", "🗺️ Pick on the map"])

# ------------------------------------------------------------ option 1: describe it
with tab_prompt:
    if not config.API_KEY:
        st.error("No API key found. Fill in the GOOGLE_API_KEY line of your .env file.")
    else:
        with st.form("prompt_form"):
            text = st.text_area(
                "What kind of trip do you want?",
                placeholder="Me and 2 friends, 10 to 15 June, 500 euros each, "
                            "great food, cheaper than Barcelona",
            )
            submitted = st.form_submit_button("Find trips")
        if submitted and text.strip():
            try:
                with st.spinner("Reading your request..."):
                    st.session_state.prompt_request = extract_request(text)
            except Exception as e:
                st.error(f"Gemini call failed: {type(e).__name__}")
                st.caption(str(e)[:300])
        request = st.session_state.get("prompt_request")
        if request:
            show_understood(request)
            show_trips(request)

# ------------------------------------------------------------ option 2: pick on the map
with tab_map:
    df = pd.DataFrame([
        {"id": c.id, "city": c.name, "lat": COORDS[c.id][0], "lon": COORDS[c.id][1]}
        for c in cities if c.id in COORDS
    ])
    fig = px.scatter_geo(df, lat="lat", lon="lon", hover_name="city", scope="europe")
    fig.update_traces(marker={"size": 14, "color": "#e4572e"})
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, height=420)

    event = st.plotly_chart(fig, on_select="rerun", selection_mode="points", key="europe_map")
    points = event.selection.points
    map_pick = df.iloc[points[0]["point_index"]]["id"] if points else None

    list_pick = st.selectbox("…or choose from the list", [None] + list(df["id"]),
                             format_func=lambda cid: "—" if cid is None else by_id[cid].name)
    city_id = map_pick or list_pick

    if city_id is None:
        st.info("Click a city on the map to start.")
    else:
        city = by_id[city_id]
        st.subheader(f"{city.name}, {city.country}")
        st.caption(city.description)

        today = datetime.date.today()
        with st.form("map_form"):
            c1, c2 = st.columns(2)
            start = c1.date_input("Start date", value=today + datetime.timedelta(days=30))
            end = c2.date_input("End date", value=today + datetime.timedelta(days=35))
            c3, c4 = st.columns(2)
            people = c3.number_input("People", min_value=1, max_value=20, value=1)
            budget = c4.number_input("Budget per person (€)", min_value=0.0, step=50.0,
                                     value=None, placeholder="no budget")
            go = st.form_submit_button(f"Price a trip to {city.name}")
        if go:
            st.session_state.map_request = TripRequest(
                origin="lisbon", destination=city_id,
                start_date=start, end_date=end, people=int(people),
                budget_per_person_eur=budget or None,
                max_travel_hours=None, interests=[], climate_wanted=None, cheaper_than=None,
            )
        request = st.session_state.get("map_request")
        if request and request.destination == city_id:
            show_trips(request)