# app.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import io

st.set_page_config(page_title="📊 Swing Screener", layout="wide")

# -------------------------
# Helper functions
# -------------------------
def clean_private_key(key_raw: str) -> str:
    """
    Accepts private_key as stored in st.secrets and returns clean multiline private key.
    Handles both triple-quoted multi-line and escaped \\n sequences.
    """
    if not key_raw:
        return key_raw
    # If key already contains real newlines, just strip surrounding spaces
    if "\n" in key_raw and "\\n" not in key_raw:
        return key_raw.strip()
    # If key contains escaped newline characters (literal backslash + n), convert them
    cleaned = key_raw.replace("\\n", "\n")
    # Remove leading/trailing quotes if present accidentally
    cleaned = cleaned.strip().strip('"').strip("'")
    return cleaned

def get_gspread_client():
    """
    Builds a gspread client using st.secrets["gcp_service_account"], with robust key handling.
    Returns authorized gspread client.
    """
    gcp = st.secrets.get("gcp_service_account")
    if not gcp:
        raise RuntimeError("gcp_service_account not found in st.secrets")

    creds_dict = dict(gcp)  # copy
    # Clean private_key
    raw_pk = creds_dict.get("private_key", "")
    creds_dict["private_key"] = clean_private_key(raw_pk)

    # Build Credentials object
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

def load_sheet_as_df(sheet_name: str) -> pd.DataFrame:
    client = get_gspread_client()
    sh = client.open(sheet_name)
    worksheet = sh.sheet1
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def csv_download_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue()

# -------------------------
# Authentication / Session
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.df = None

st.title("📊 Swing Screener — Secure Dashboard")

if not st.session_state.logged_in:
    st.subheader("🔐 Login (Email + Password)")
    col1, col2 = st.columns([2, 1])
    with col1:
        email_input = st.text_input("📧 Email", placeholder="yourname@gmail.com")
        password_input = st.text_input("🔑 Password", type="password")
    with col2:
        show_pass = st.checkbox("Show password")
        if show_pass and password_input:
            st.info(f"Password: `{password_input}`")

    if st.button("Login"):
        # load allowed users from secrets
        auth = st.secrets.get("auth")
        if not auth:
            st.error("Authentication info not found in st.secrets (add [auth] in Secrets).")
        else:
            allowed_users = auth.get("users", {})
            # case-insensitive email matching
            user_key = email_input.lower().strip()
            if user_key in allowed_users and password_input == allowed_users[user_key]:
                st.session_state.logged_in = True
                st.session_state.username = user_key
                st.success(f"✅ Access granted! Welcome, {email_input}")
                st.experimental_rerun()
            else:
                st.error("❌ Invalid email or password. Please try again.")
    st.write("---")
    st.info("Note: Make sure your credentials are set in Streamlit Secrets (`auth.users` and `gcp_service_account`).")
else:
    # -------------------------
    # Logged in UI
    # -------------------------
    st.sidebar.write(f"Signed in as: **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.df = None
        st.experimental_rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Actions**")
    if st.sidebar.button("Reload sheet data"):
        st.session_state.df = None  # force reload

    # Try load sheet once
    sheet_name = "streamlit-service"  # <-- change if your sheet name differs
    if st.session_state.df is None:
        with st.spinner("Connecting to Google Sheet..."):
            try:
                df = load_sheet_as_df(sheet_name)
                st.session_state.df = df
                st.success("✅ Connected to Google Sheet successfully!")
            except Exception as e:
                st.error("❌ Error connecting to Google Sheet.")
                st.exception(e)
                st.stop()

    df = st.session_state.df.copy()
    st.write("### 🔍 Search & Filter")
    search_col1, search_col2 = st.columns([3,1])
    with search_col1:
        query = st.text_input("Type any keyword to search across all columns (case-insensitive):")
    with search_col2:
        if st.button("Clear"):
            st.experimental_rerun()

    if query:
        mask = df.apply(lambda row: row.astype(str).str.contains(query, case=False, na=False).any(), axis=1)
        filtered = df[mask].reset_index(drop=True)
        if filtered.empty:
            st.warning("No matching results found.")
        else:
            st.success(f"Found {len(filtered)} matching rows")
            st.dataframe(filtered)
            csv_bytes = csv_download_bytes(filtered)
            st.download_button("⬇️ Download filtered CSV", csv_bytes, file_name="filtered_results.csv", mime="text/csv")
    else:
        st.dataframe(df)
        csv_bytes = csv_download_bytes(df)
        st.download_button("⬇️ Download full CSV", csv_bytes, file_name="full_sheet.csv", mime="text/csv")

    st.write("---")
    st.write("If you face issues with Google authentication, check:")
    st.write("- Service account email is shared with the Google Sheet (Editor permission).")
    st.write("- `gcp_service_account` is correctly present in Streamlit Secrets.")
    st.write("- If private_key contained `\\n` escapes, the app automatically cleans them.")
