"""
Your first AI web application.

Run with:  uv run streamlit run app.py

You do not need to write anything for this to work. It is already built.
This is where the course starts. Every week from here builds on it.
"""
import streamlit as st
from google import genai
from google.genai import types

import config

st.set_page_config(page_title="Capstone Project", page_icon="✈️", layout="centered")

st.title("My first AI app")

# --- Key check ---
if not config.API_KEY:
    st.error("No API key found.")
    st.markdown(
        "Create a `.env` file from `.env.example` and fill in the "
        "`GOOGLE_API_KEY` line with your key from "
        "[aistudio.google.com/apikey](https://aistudio.google.com/apikey)."
    )
    st.stop()

# --- Chat session: kept between interactions ---
if "chat" not in st.session_state:
    # The client must be stored in session state. As a plain local variable,
    # Python closes its connection at the end of the script run and the
    # conversation stops working.
    st.session_state.client = genai.Client(api_key=config.API_KEY)
    st.session_state.chat = st.session_state.client.chats.create(
        model=config.MODEL,
        config=types.GenerateContentConfig(temperature=config.TEMPERATURE),
    )
    st.session_state.messages = []

# --- History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- User input ---
if prompt := st.chat_input("Type something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = st.session_state.chat.send_message(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"The API call failed: {type(e).__name__}")
            st.caption(str(e)[:300])

with st.sidebar:
    st.subheader("What is happening")
    st.markdown(
        "Every message you send goes to the API, and the reply comes back here.\n\n"
        "`st.session_state` keeps the conversation between interactions. "
        "Without it, the model would forget everything after each message."
    )
    st.divider()
    st.caption(f"Model: `{config.MODEL}`")
    st.caption(f"Messages this session: {len(st.session_state.messages)}")
    if st.button("Clear conversation"):
        del st.session_state.chat
        st.rerun()
