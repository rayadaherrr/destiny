import streamlit as st

import db

st.set_page_config(page_title="Destiny", page_icon="✈️", layout="centered")
db.init_db()   # creates destiny.db and the tables the first time


def login_screen():
    st.title("Destiny ✈️")
    st.caption("Log the trips you took, rate them, and find your next one.")
    tab_in, tab_up = st.tabs(["Log in", "Create account"])

    with tab_in:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")
        if submitted:
            user_id = db.login(username, password)
            if user_id:
                st.session_state.user_id = user_id
                st.rerun()
            else:
                st.error("Wrong username or password.")

    with tab_up:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username")
            new_password = st.text_input("Choose a password (6+ characters)", type="password")
            created = st.form_submit_button("Create account")
        if created:
            user_id, error = db.create_user(new_username, new_password)
            if error:
                st.error(error)
            else:
                st.session_state.user_id = user_id
                st.rerun()


# --- Gate: nobody gets past this point without logging in ---
if "user_id" not in st.session_state:
    login_screen()
    st.stop()

user = db.get_user(st.session_state.user_id)

with st.sidebar:
    st.write(f"Logged in as **@{user['username']}**")
    if st.button("Log out"):
        st.session_state.clear()
        st.rerun()

# --- The two options ---
navigation = st.navigation([
    st.Page("views/profile.py", title="My profile", icon="👤"),
    st.Page("views/trip_finder.py", title="Trip finder", icon="🧭"),
])
navigation.run()