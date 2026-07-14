import streamlit as st
from main import handle_query, format_response
import pandas as pd

st.set_page_config(page_title="Tennis Statistics Assistant", page_icon="🎾")
st.title("🎾 Tennis Statistics Assistant")
st.caption("Ask me tennis questions e.g. • head to head records • surface performance • player statistics • on-form players • tournament favourites")
st.caption("Examples: How does Alcaraz perform on clay? • Who wins Djokovic vs Federer? • Who are the Wimbledon favourites?")


df = pd.read_csv("data/atp_tennis.csv")

if "messages" not in st.session_state:
    st.session_state.messages = []

# display session message history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])



query = st.chat_input("Ask me anything about ATP tennis")
if query:

    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        with st.spinner("Generating"):
            query, result = handle_query(df, query, st.session_state.messages)
        response = st.write_stream(format_response(query, result, st.session_state.messages))

    
    st.session_state.messages.append({"role": "user", "content": query})
    st.session_state.messages.append({"role": "assistant", "content": response})



if st.button("Clear chat"):
    st.session_state.messages = []
    st.rerun()
