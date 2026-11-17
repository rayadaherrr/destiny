import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import config
import db
from extraction import extract_request
from geo import COORDS
from pricing import estimate_cost
from schemas import TripRequest
from tools import find_trips, load_cities

st.title("Trip finder")

cities = load_cities()
by_id = {c.id: c for c in cities}
my_id = st.session_state.user_id

# A typical trip, used only to colour the map: 1 person, no dates (5 nights, normal season)
BASELINE = TripRequest(
    origin="lisbon", start_date=None, end_date=None, people=1,
    budget_per_person_eur=None, max_travel_hours=None, destination=None,
    interests=[], climate_wanted=None, cheaper_than=None,
)

# colour mode -> (which number to use, is lower better?, colour-bar title)
COLOR_MODES = {
    "Average Price (Low to High)": ("price", True, "Price (green = cheaper)"),
    "Your Past Ratings": ("rating", False, "Your rating (green = higher)"),
    "Travel Time from Origin": ("hours", True, "Travel time (green = faster)"),
}


# ------------------------------------------------------------ helpers
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


def map_rows(cities_to_show, color_mode):
    """One row per city for the map, using real data from cities.json and your ratings."""
    my_trips = db.user_trips(my_id)          # one database query, not one per city
    metrics = {}
    for c in cities_to_show:
        mine = [t["rating"] for t in my_trips if t["city_id"] == c.id]
        estimate = estimate_cost(c, BASELINE)
        travel = c.travel_from.get(BASELINE.origin)
        metrics[c.id] = {
            "price": estimate.total_eur if estimate else None,
            "rating": sum(mine) / len(mine) if mine else None,
            "hours": travel.hours if travel else None,
        }

    key, lower_is_better, scale_label = COLOR_MODES[color_mode]
    known = [m[key] for m in metrics.values() if m[key] is not None]
    if key == "rating":
        low, high = 1, 5                     # ratings always use the full 1-5 scale
    else:
        low, high = (min(known), max(known)) if known else (0, 1)
    span = (high - low) or 1.0

    rows = []
    for c in cities_to_show:
        m = metrics[c.id]
        if m[key] is None:
            score = 0.5                      # no data: neutral middle colour
        else:
            score = (m[key] - low) / span
            if lower_is_better:
                score = 1 - score
        details = " · ".join([
            f"€{m['price']:.0f} for a typical 5-night trip" if m["price"] is not None else "no price data",
            f"{m['hours']:g} h from {BASELINE.origin.title()}" if m["hours"] is not None else "no travel data",
            f"you: {m['rating']:.1f} ★" if m["rating"] is not None else "you: not rated yet",
        ])
        rows.append({
            "id": c.id, "city": c.name, "country": c.country,
            "lat": COORDS[c.id][0], "lon": COORDS[c.id][1],
            "metric_val": score, "details": details, "scale_label": scale_label,
        })
    return rows


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
    st.subheader("Explore Destinations")

    with st.expander("Filter and color options", expanded=True):
        col_f1, col_f2 = st.columns(2)
        all_tags = sorted({tag for c in cities for tag in c.tags})
        selected_tags = col_f1.multiselect("Filter by tags/interests", all_tags)
        color_mode = col_f2.selectbox("Color map by", list(COLOR_MODES), index=0)

    filtered_cities = [
        c for c in cities
        if c.id in COORDS and (not selected_tags or any(tag in selected_tags for tag in c.tags))
    ]
    df = pd.DataFrame(map_rows(filtered_cities, color_mode))

    if df.empty:
        st.warning("No cities match the selected filters.")
    else:
        fig = px.scatter_geo(
            df, lat="lat", lon="lon",
            color="metric_val", color_continuous_scale="RdYlGn", range_color=[0.0, 1.0],
            hover_name="city",
            hover_data={"country": True, "details": True,
                        "metric_val": False, "lat": False, "lon": False},
            scope="europe",
        )
        fig.update_traces(
            marker={"size": 16, "line": {"width": 1, "color": "white"}},
            hovertemplate="<b>%{hovertext}</b><br>%{customdata[0]}<br>%{customdata[1]}<extra></extra>",
        )
        fig.update_layout(
            geo={
                "bgcolor": "rgba(0,0,0,0)",
                "showland": True,
                "landcolor": "#f4f4f6",
                "subunitcolor": "#ffffff",
                "countrycolor": "#dcdde1",
                "center": {"lat": 50, "lon": 10},
                "projection": {"scale": 3.2},
            },
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
            height=420,
            coloraxis_colorbar={
                "title": df["scale_label"].iloc[0],
                "thickness": 12,
                "len": 0.6,
                "y": 0.5,
                "tickvals": [0, 0.5, 1],
                "ticktext": ["Low / Worst", "Medium", "High / Best"],
            },
        )

        # The key changes with the filters, so an old click can't point at the wrong city
        map_key = f"europe_map_{color_mode}_{'-'.join(selected_tags)}"
        event = st.plotly_chart(fig, on_select="rerun", selection_mode="points", key=map_key)
        points = event.selection.points
        index = points[0]["point_index"] if points else None
        map_pick = df.iloc[index]["id"] if index is not None and index < len(df) else None

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