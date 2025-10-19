import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Swing Screener", layout="wide")
st.title("📊 Swing Screener App")

allowed_users = st.secrets["auth"]["emails"]
user_email = st.text_input("Enter your Google email to access:")
if user_email not in allowed_users:
    st.error("❌ Access denied. Authorized users only.")
    st.stop()

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)
sheet = client.open("SwingData").sheet1

st.success("✅ Connected to Sheet successfully!")
data = sheet.get_all_records()
st.dataframe(data)
