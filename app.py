import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account

st.title("Swing Screener")

# Load credentials safely from Streamlit secrets
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)

client = gspread.authorize(creds)

# Open your sheet
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1eyLEPy91_bS4d5wD5DF7IJvZIqhtv55i7ijqncWTNL0/edit?usp=sharing").sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)
st.dataframe(df)
