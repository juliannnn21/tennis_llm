import streamlit as st
from main import handle_query
import pandas as pd

st.set_page_config(page_title="Tennis Statistics Assistant", page_icon="🎾")
st.title("🎾 Tennis Statistics Assistant")
st.caption("Ask me tennis questions e.g. • head to head records • surface performance • player statistics • on-form players • tournament favourites")



df = pd.read_csv("data/atp_tennis.csv")

query = st.text_input("Ask me anything about ATP tennis")
st.caption("Examples: How does Alcaraz perform on clay? • Who wins Djokovic vs Federer? • Who are the Wimbledon favourites?")

if st.button("Ask"):
    if query:
        with st.spinner("Generating..."):
            response = handle_query(df, query)
        st.write(response)