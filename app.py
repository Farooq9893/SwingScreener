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
        raise FileNotFoundError(f"Credentials file not found: {cred_path}")
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

    allowed_users = {"farooq9893@gmail.com": "12345"}  # Default user

    email = st.text_input("📧 Email", placeholder="your.email@gmail.com")
    password = st.text_input("🔑 Password", type="password")

    col1, col2 = st.columns([1, 1])
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
        if st.button("Cancel"):
            st.info("Login cancelled.")

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
if st.sidebar.button("🔄 Reload Sheet Data"):
    st.session_state.df = None
    st.rerun()

# Hard-coded sheet name
SHEET_NAME = "streamlit_service"

# Load sheet once into session_state
if st.session_state.df is None:
    with st.spinner("Connecting to Google Sheet..."):
        try:
            df = load_sheet_as_df(streamlit_service)
            st.session_state.df = df
            st.success("✅ Connected to Google Sheet successfully!")
        except Exception as e:
            st.error("❌ Error connecting to Google Sheet.")
            st.exception(e)
            st.stop()

df = st.session_state.df.copy()

# ----------------------------
# Search feature
# ----------------------------
st.write("### 🔍 Search the Sheet")

col_search, col_button = st.columns([4, 1])
with col_search:
    search_term = st.text_input("Enter keyword to search across all columns:")
with col_button:
    do_search = st.button("Search")

if do_search:
    if not search_term:
        st.warning("Please type a keyword before pressing Search.")
    else:
        term = search_term.strip().lower()
        mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(term).any(), axis=1)
        filtered_df = df[mask]

        if filtered_df.empty:
            st.warning("No matching records found.")
        else:
            st.success(f"✅ Found {len(filtered_df)} matching rows.")
            st.dataframe(filtered_df, use_container_width=True)

            # CSV Download
            csv_bytes = df_to_csv_bytes(filtered_df)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv_bytes,
                file_name=f"search_results_{term}.csv",
                mime="text/csv",
            )
else:
    st.dataframe(df, use_container_width=True)

