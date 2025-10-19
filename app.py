import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="📊 Swing Screener", layout="wide")

# ---- LOGIN SYSTEM ----
st.title("📊 Swing Screener App")

st.write("### 🔐 Secure Login")

# Allowed users (email + password) from secrets.toml
allowed_users = st.secrets["auth"].get("users", {})

email_input = st.text_input("📧 Enter your Email:")
password_input = st.text_input("🔑 Enter your Password:", type="password")

if st.button("Login"):
    if email_input.lower().strip() in allowed_users and password_input == allowed_users[email_input.lower().strip()]:
        st.success(f"✅ Access granted! Welcome, {email_input} 👋")

        # ---- CONNECT TO GOOGLE SHEET ----
        try:
            creds = Credentials.from_service_account_info(
                st.secrets["gcp_service_account"],
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            client = gspread.authorize(creds)
            sheet = client.open("streamlit-service").sheet1  # 👈 your sheet name here
            data = sheet.get_all_records()
            df = pd.DataFrame(data)

            st.success("✅ Connected to Google Sheet successfully!")

            # ---- SEARCH FEATURE ----
            st.write("### 🔍 Search your data below")
            search_query = st.text_input("Type to search (e.g., stock name, pattern, sector):")

            if search_query:
                filtered_df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
                if not filtered_df.empty:
                    st.success(f"Found {len(filtered_df)} matching records:")
                    st.dataframe(filtered_df)
                else:
                    st.warning("No matching results found.")
            else:
                st.dataframe(df)

        except Exception as e:
            st.error(f"❌ Error connecting to Google Sheet: {e}")

    else:
        st.error("❌ Invalid email or password. Please try again.")
