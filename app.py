# app.py - Option A: hard-coded sheet name  
import streamlit as st  
import pandas as pd  
import gspread  
from google.oauth2.service_account import Credentials  
import io  
import os  

st.set_page_config(page_title="📊 Swing Screener", layout="wide")  

# ----------------------------  
# Google Sheets helper  
# ----------------------------  
def get_gspread_client_from_file():  
    cred_path = os.path.join(os.path.dirname(__file__), "secrets", "credentials.json")  
    if not os.path.exists(cred_path):  
        raise FileNotFoundError(f"Credentials file not found: {cred_path}\nPut your service account JSON at this path.")  
    creds = Credentials.from_service_account_file(  
        cred_path,  
        scopes=[  
            "https://www.googleapis.com/auth/spreadsheets",  
            "https://www.googleapis.com/auth/drive",  
        ],  
    )  
    return gspread.authorize(creds)  

def load_sheet_as_df(sheet_name: str) -> pd.DataFrame:  
    client = get_gspread_client_from_file()  
    sh = client.open(sheet_name)  
    data = sh.sheet1.get_all_records()  
    return pd.DataFrame(data)  

def df_to_csv_bytes(df: pd.DataFrame) -> bytes:  
    buf = io.BytesIO()  
    df.to_csv(buf, index=False)  
    return buf.getvalue()  

# ----------------------------  
# Session defaults  
# ----------------------------  
if "logged_in" not in st.session_state:  
    st.session_state.logged_in = False  
    st.session_state.user_email = ""  
    st.session_state.df = None  

st.title("📊 Swing Screener — Login + Search")  

# ----------------------------  
# Login screen  
# ----------------------------  
if not st.session_state.logged_in:  
    st.subheader("🔐 Login (Email + Password)")  

    secrets_auth = st.secrets.get("auth", {}) if hasattr(st, "secrets") else {}  
    allowed_users = secrets_auth.get("users", {}) or {  
        "farooq9893@gmail.com": "12345"  
    }  

    email = st.text_input("📧 Email", placeholder="your.email@gmail.com")  
    password = st.text_input("🔑 Password", type="password")  

    col1, col2 = st.columns([1,1])  
    with col1:  
        if st.button("Login"):  
            key = email.lower().strip()  
            if key in allowed_users and password == allowed_users[key]:  
                st.session_state.logged_in = True  
                st.session_state.user_email = key  
                st.success(f"✅ Access granted — {email}")  
                st.rerun()  
            else:  
                st.error("❌ Invalid email or password.")  
    with col2:  
        st.write(" ")  
        if st.button("Cancel"):  
            st.info("Login cancelled.")  

    st.info("Tip: put your user list in Streamlit Secrets under [auth].")  
    st.stop()  

# ----------------------------  
# Logged-in area  
# ----------------------------  
st.sidebar.write(f"👤 Signed in as **{st.session_state.user_email}**")  
if st.sidebar.button("Logout"):  
    st.session_state.logged_in = False  
    st.session_state.user_email = ""  
    st.session_state.df = None  
    st.rerun()  

st.sidebar.markdown("---")  
if st.sidebar.button("Reload sheet data"):  
    st.session_state.df = None  

# Hard-coded sheet name  
SHEET_NAME = "streamlit-service"  

# Load sheet once into session_state  
if st.session_state.df is None:  
    with st.spinner("Connecting to Google Sheet..."):  
        try:  
            df = load_sheet_as_df(SHEET_NAME)  
            st.session_state.df = df  
            st.success("✅ Connected to Google Sheet successfully!")  
        except Exception as e:  
            st.error("❌ Error connecting to Google Sheet.")  
            st.exception(e)  
            st.stop()  

# Work with a copy  
df = st.session_state.df.copy()  

st.write("### 🔍 Search the sheet")  
col_search, col_button = st.columns([4,1])  
with col_search:  
    search_term = st.text_input("Enter keyword to search across all columns:")  
with col_button:  
    do_search = st.button("Search")  

if do_search:  
    if not search_term:  
        st.warning("Please type a keyword then press Search.")  
    else:
