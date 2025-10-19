import base64

# ---- CONNECT TO GOOGLE SHEET ----
try:
    key = st.secrets["gcp_service_account"]["private_key"]
    # agar key me \n replace nahi hua ho to manually clean kar do
    if "\\n" in key:
        key = key.replace("\\n", "\n")

    # manually validate base64 part to avoid padding error
    try:
        base64.b64decode("".join(key.splitlines()[1:-1] + ["=="]))
    except Exception:
        pass  # ignore; just ensures padding safe

    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = key

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)
    sheet = client.open("streamlit-service").sheet1
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    st.success("✅ Connected to Google Sheet successfully!")

except Exception as e:
    st.error(f"❌ Error connecting to Google Sheet: {e}")
