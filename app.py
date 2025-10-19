import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import io

st.set_page_config(page_title="📊 Swing Screener", layout="wide")

# ---------- Helper functions ----------

def clean_private_key(key_raw: str) -> str:
    """Fixes escaped \\n inside private_key text."""
    if not key_raw:
        return key_raw
    if "\\n" in key_raw:
        return key_raw.replace("\\n", "\n").strip()
    return key_raw.strip()

def get_gspread_client():
    gcp = st.secrets.get("gcp_service_account")
    if not gcp:
        raise RuntimeError("gcp_service_account not found in secrets")

    creds_dict = dict(gcp)
    creds_dict["private_key"] = clean_private_key(creds_dict.get("private_key", ""))

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def load_sheet_as_df(sheet_name: str) -> pd.DataFrame:
    client = get_gspread_client()
    sh = client.open(sheet_name)
    data = sh.sheet1.get_all_records()
    return pd.DataFrame(data)

def to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()

# ---------- Session defaults ----------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.df = None

st.title("📊 Swing Screener — Secure Dashboard")

# ---------- Login screen ----------
if not st.session_state.logged_in:
    st.subheader("🔐 Login (Email + Password)")

    email = st.text_input("📧 Email")
    password = st.text_input("🔑 Password", type="password")
    if st.button("Login"):
        auth = st.secrets.get("auth", {})
        allowed = auth.get("users", {})

        user = email.lower().strip()
        if user in allowed and password == allowed[user]:
            st.session_state.logged_in = True
            st.session_state.username = user
            st.success(f"✅ Access granted! Welcome, {email}")
            st.rerun()
        else:
            st.error("❌ Invalid email or password.")

    st.info("Enter credentials defined under [auth] in Streamlit Secrets.")
    st.stop()

# ---------- Logged-in area ----------
st.sidebar.write(f"👤 Signed in as **{st.session_state.username}**")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.df = None
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Reload sheet data"):
    st.session_state.df = None

sheet_name = "streamlit-service"

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
query = st.text_input("Search any keyword:")

if query:
    mask = df.apply(lambda r: r.astype(str).str.contains(query, case=False, na=False).any(), axis=1)
    filtered = df[mask].reset_index(drop=True)
    if filtered.empty:
        st.warning("No matching results found.")
    else:
        st.success(f"Found {len(filtered)} matching rows.")
        st.dataframe(filtered, use_container_width=True)
        st.download_button("⬇️ Download filtered CSV", to_csv_bytes(filtered),
                           file_name="filtered_results.csv", mime="text/csv")
else:
    st.dataframe(df, use_container_width=True)
    st.download_button("⬇️ Download full CSV", to_csv_bytes(df),
                       file_name="full_sheet.csv", mime="text/csv")

st.write("---")
st.caption("Ensure the service-account email has Editor access to the Google Sheet.")
