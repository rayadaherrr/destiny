import datetime

import streamlit as st

import db
from tools import load_cities

st.title("Profile")

cities = load_cities()
city_names = {c.id: c.name for c in cities}
my_id = st.session_state.user_id


def stars(n):
    return "★" * n + "☆" * (5 - n)


def show_profile(user_id, own):
    user = db.get_user(user_id)
    stats = db.user_stats(user_id)

    st.subheader(f"@{user['username']}")
    if user["bio"]:
        st.write(user["bio"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Trips logged", stats["trips"])
    c2.metric("Cities", stats["cities"])
    average = "–" if stats["avg_rating"] is None else f"{stats['avg_rating']:.1f} ★"
    c3.metric("Average rating", average)

    trips = db.user_trips(user_id)
    if not trips:
        st.info("No trips logged yet.")
    for trip in trips:
        with st.container(border=True):
            name = city_names.get(trip["city_id"], trip["city_id"].title())
            st.markdown(f"**{name}**  {stars(trip['rating'])}")
            details = []
            if trip["start_date"] and trip["end_date"]:
                details.append(f"{trip['start_date']} → {trip['end_date']}")
            if trip["budget_eur"] is not None:
                details.append(f"€{trip['budget_eur']:.0f} per person")
            if details:
                st.caption(" · ".join(details))
            if trip["review"]:
                st.write(trip["review"])
            if own and st.button("Delete", key=f"delete_{trip['id']}"):
                db.delete_trip(my_id, trip["id"])
                st.rerun()


tab_mine, tab_explore = st.tabs(["My trips", "Explore travellers"])

with tab_mine:
    me = db.get_user(my_id)

    with st.expander("➕ Log a trip you took"):
        with st.form("log_trip_form", clear_on_submit=True):
            city_id = st.selectbox("Where did you go?", list(city_names),
                                   format_func=lambda cid: city_names[cid])
            rating = st.slider("Your rating", 1, 5, 4)
            review = st.text_area("Short review (optional)", max_chars=500)
            c1, c2 = st.columns(2)
            start = c1.date_input("Start date (optional)", value=None,
                                  max_value=datetime.date.today())
            end = c2.date_input("End date (optional)", value=None,
                                max_value=datetime.date.today())
            budget = st.number_input("Spent per person, in € (optional)",
                                     min_value=0.0, step=50.0, value=None)
            saved = st.form_submit_button("Save trip")
        if saved:
            if (start is None) != (end is None):
                st.warning("Give both dates, or neither.")
            elif start and end and end < start:
                st.warning("The end date is before the start date.")
            else:
                db.add_trip(
                    my_id, city_id, rating, review.strip(),
                    start.isoformat() if start else None,
                    end.isoformat() if end else None,
                    budget,
                )
                st.success("Trip saved!")

    with st.expander("✏️ Edit your bio"):
        with st.form("bio_form"):
            bio = st.text_area("About you", value=me["bio"], max_chars=200)
            if st.form_submit_button("Save bio"):
                db.update_bio(my_id, bio.strip())
                st.rerun()

    show_profile(my_id, own=True)

with tab_explore:
    others = [u for u in db.list_users() if u["id"] != my_id]
    if not others:
        st.info("No other travellers yet. Ask a friend to create an account!")
    else:
        usernames = {u["id"]: u["username"] for u in others}
        pick = st.selectbox("Choose a traveller", list(usernames),
                            format_func=lambda uid: "@" + usernames[uid])
        show_profile(pick, own=False)