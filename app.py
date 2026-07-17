"""
app.py

Streamlit web interface for the ATP Tennis Statistics Assistant.
Handles user input, displays chat history and streams LLM responses.
"""

import streamlit as st
from main import handle_query
from llm import format_response
from name_matching import get_unique_players, get_unique_tournaments
import pandas as pd

import kagglehub
import shutil
import os

if not os.path.exists("data/atp_tennis.csv"):
    try:
        path = kagglehub.dataset_download("dissfya/atp-tennis-2000-2023daily-pull")
        os.makedirs("data", exist_ok=True)
        for file in os.listdir(path):
            if file.endswith(".csv"):
                shutil.copy(os.path.join(path, file), "data/atp_tennis.csv")
    except Exception as e:
        st.error(f"Failed to download data: {e}")
        st.stop()

try:
    df = pd.read_csv("data/atp_tennis.csv")
except FileNotFoundError:
    st.error("Data file not found.")
    st.stop()

# precompute at startup to avoid recalculating on every query
unique_players = get_unique_players(df)
unique_tournaments = get_unique_tournaments(df)

st.set_page_config(page_title="Tennis Statistics Assistant", page_icon="🎾")
st.title("🎾 Tennis Statistics Assistant")
st.caption("Ask me tennis questions about the ATP tour from the 2000s-present day")
st.caption("""e.g. • head-to-head records • surface performance of a player 
           • player statistics • on-form players • tournament favourites • player performance at a specific tournament""")
st.caption("Examples: How does Alcaraz perform on clay? • Who wins Djokovic vs Federer? • Who are the Wimbledon favourites?")

# initialise session state on first load
if "messages" not in st.session_state:
    st.session_state.messages = []

if "cache" not in st.session_state:
        st.session_state.cache = {}

# display session message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

query = st.chat_input("Ask me anything about ATP tennis")
if query:
    with st.chat_message("user"):
        st.write(query)
    # upon asking the LLM a question
    with st.chat_message("assistant"):
        with st.spinner("Generating"):
            query, result = handle_query(df, query, unique_players, unique_tournaments, st.session_state.messages, st.session_state.cache)
        response = st.write_stream(format_response(query, result, st.session_state.messages))
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.messages.append({"role": "assistant", "content": response})

if st.button("Clear chat"):
    st.session_state.messages = []
    st.session_state.cache = {}
    st.rerun()
