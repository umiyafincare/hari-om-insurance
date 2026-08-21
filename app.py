import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import urllib.parse
import os
import gspread
from google.oauth2.service_account import Credentials

# ----------------- પેજ કન્ફિગરેશન -----------------
st.set_page_config(
    page_title="Hari Om Insurance & Loan Advisor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- GOOGLE SHEETS API સેટઅપ -----------------
# તમારી Google Sheet નું જે સાચું નામ હોય તે અહીં લખો:
SHEET_NAME = "Hari_Om_Insurance_DB"

COLUMNS = [
    "id", "name", "mobile", "vehicle_no", "vehicle_type", 
    "policy_company", "policy_no", "premium_amount", 
    "expiry_date", "remarks", "last_renewed"
]

@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        # Secrets માંથી Credentials લેવા
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            # Private key formatting fix
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            client = gspread.authorize(credentials)
            return client
        else:
            st.error("❌ Streamlit Secrets માં 'gcp_service_account' મળ્યું નથી!")
            return None
    except Exception as e:
        st.error(f"❌ Google Auth Error: {e}")
        return None

def get_sheet():
    client = get_gspread_client()
    if client:
        try:
            # શીટના નામથી ઓપન કરવાનો પ્રયત્ન
            return client.open(SHEET_NAME).sheet1
        except Exception as e:
            st.error(f"❌ Sheet Open Error ('{SHEET_NAME}' નામની શીટ મળી નથી અથવા Service Account સાથે શેર નથી): {e}")
            return None
    return None

def get_data():
    sheet = get_sheet()
    if sheet:
        try:
            records = sheet.get_all_records()
            df = pd.DataFrame(records)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS]
        except Exception as e:
            st.error(f"❌ Data Read Error: {e}")
    
    # ફોલબેક લોકલ CSV
    if os.path.exists("insurance_data.csv"):
        return pd.read_csv("insurance_data.csv")
    return pd.DataFrame(columns=COLUMNS)

def insert_policy(name, mobile, vehicle_no, v_type, company, policy_no, premium, expiry, remarks):
    sheet = get_sheet()
    df = get_data()
    
    new_id = len(df) + 1
    new_row = [
        new_id,
        name,
        str(mobile),
        vehicle_no,
        v_type,
        company,
        str(policy_no),
        premium,
        str(expiry),
        remarks,
        str(date.today())
    ]
    
    success = False
    if sheet:
        try:
            sheet.append_row(new_row)
            success = True
        except Exception as e:
            st.error(f"❌ Sheet Append Error: {e}")
            
    # સુરક્ષા માટે લોકલ સેવ
    row_dict = dict(zip(COLUMNS, new_row))
    new_df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    new_df.to_csv("insurance_data.csv", index=False)
    return success

# ----------------- MODERN CUSTOM CSS -----------------
st.markdown("""
<style>
    .main { background-color: #f1f5f9; }
    [data-testid="stMetric"] { background: #ffffff; padding: 18px 20px; border-radius: 14px; border-top: 4px solid #1E3A8A; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] { background-color: #ffffff; }
    [data-testid="stSidebar"] .stButton > button { width: 100% !important; text-align: left !important; padding: 10px 16px !important; border-radius: 10px !important; margin-bottom: 6px !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- સાઇડબાર નેવિગેશન -----------------
if 'current_page' not in st.session_state:
    st.session_state.current_page = "➕ નવી પોલિસી એન્ટ્રી"

df = get_data()

with st.sidebar:
    st.markdown("### 🛡️ હરિ ઓમ ઇન્સ્યોરન્સ")
    menu_items = ["📊 ડેશબોર્ડ", "➕ નવી પોલિસી એન્ટ્રી", "📁 તમામ ગ્રાહકોની યાદી"]
    for item in menu_items:
        if st.button(item, key=f"nav_{item}", type="primary" if st.session_state.current_page == item else "secondary"):
            st.session_state.current_page = item
            st.rerun()

# ----------------- 1. નવી પોલિસી એન્ટ્રી (મુખ્ય ટેસ્ટિંગ પેજ) -----------------
if st.session_state.current_page == "➕ નવી પોલિસી એન્ટ્રી":
    st.title("➕ નવી પોલિસી ઉમેરો (Live Google Sheets Test)")
    
    with st.form("new_entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("ગ્રાહકનું નામ *")
        mobile = c2.text_input("મોબાઇલ નંબર *")
        vehicle_no = c1.text_input("વાહન નંબર (GJ-xx-xxxx) *")
        vehicle_type = c2.selectbox("વાહનનો પ્રકાર", ["2 Wheeler", "4 Wheeler (Car)", "Commercial", "Tractor", "અન્ય"])
        company = c1.selectbox("ઇન્સ્યોરન્સ કંપની", ["ICICI Lombard", "Bajaj Allianz", "Tata AIG", "HDFC ERGO", "અન્ય"])
        policy_no = c2.text_input("પોલિસી નંબર")
        premium = c1.number_input("પ્રીમિયમ રકમ (₹)", min_value=0, step=500)
        expiry = c2.date_input("પોલિસી એક્સપાયરી તારીખ *")
        remarks = st.text_input("નોંધ / રિમાર્ક્સ")
        
        if st.form_submit_button("💾 પોલિસી સેવ કરો"):
            if name.strip() and mobile.strip() and vehicle_no.strip():
                is_saved = insert_policy(name.strip(), mobile.strip(), vehicle_no.upper().strip(), vehicle_type, company, policy_no.strip(), premium, str(expiry), remarks.strip())
                if is_saved:
                    st.success("✅ Google Sheets માં ડેટા સફળતાપૂર્વક ઉમેરાઈ ગયો!")
                else:
                    st.warning("⚠️ Google Sheets માં ડેટા સેવ ન થયો (ઉપરની લાલ એરર વાંચો). ડેટા લોકલ સેવ થઈ ગયો છે.")
                st.rerun()
            else:
                st.error("નામ, મોબાઇલ અને વાહન નંબર જરૂરી છે.")

# ----------------- 2. તમામ ગ્રાહકોની યાદી -----------------
elif st.session_state.current_page == "📁 તમામ ગ્રાહકોની યાદી":
    st.title("📁 તમામ ગ્રાહકોની યાદી (Google Sheets)")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("શીટમાં કોઈ ડેટા નથી.")

# ----------------- 3. ડેશબોર્ડ -----------------
elif st.session_state.current_page == "📊 ડેશબોર્ડ":
    st.title("📊 બિઝનેસ ડેશબોર્ડ")
    st.metric("કુલ પોલિસી", len(df))
