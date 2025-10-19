import streamlit as st

st.title("Secrets Test Farooq Bhai")

st.write("Keys found in st.secrets:", list(st.secrets.keys()))
st.write("Full secrets dictionary:")
st.json(st.secrets)
