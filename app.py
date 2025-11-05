import streamlit as st
from google.oauth2 import service_account
import gspread
import pandas as pd

# Load credentials from Streamlit Secrets
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
)
client = gspread.authorize(creds)
sheet = client.open("streamlit_service").sheet1
data = sheet.get_all_records()
df = pd.DataFrame(data)
st.dataframe(df)
