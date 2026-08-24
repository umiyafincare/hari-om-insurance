import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import urllib.parse
import os
import re
import gspread
from google.oauth2.service_account import Credentials
import pypdf

# ----------------- પેજ કન્ફિગરેશન -----------------
st.set_page_config(
    page_title="Hari Om Insurance & Loan Advisor",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- GOOGLE SHEETS સેટઅપ -----------------
SHEET_NAME = "Hari_Om_Insurance_DB"
LOCAL_CSV = "insurance_data.csv"
DEFAULT_PIN = "7698"

COLUMNS = [
    "id", "name", "mobile", "vehicle_no", "vehicle_type", 
    "policy_company", "policy_no", "premium_amount", 
    "expiry_date", "remarks", "last_renewed"
]

# તમામ ૨૪ ઇન્સ્યોરન્સ કંપનીઓનું લિસ્ટ
COMPANIES_LIST = [
    "ACKO General Insurance",
    "Bajaj Allianz General Insurance",
    "Cholamandalam MS General Insurance",
    "Future Generali India Insurance",
    "Go Digit General Insurance",
    "HDFC ERGO General Insurance",
    "ICICI Lombard General Insurance",
    "IFFCO TOKIO General Insurance",
    "Kotak Mahindra General Insurance (Zurich Kotak)",
    "Liberty General Insurance",
    "Magma HDI General Insurance",
    "National Insurance Company",
    "Navi General Insurance",
    "Raheja QBE General Insurance",
    "Reliance General Insurance",
    "Royal Sundaram General Insurance",
    "SBI General Insurance",
    "Shriram General Insurance",
    "Tata AIG General Insurance",
    "The New India Assurance Company",
    "The Oriental Insurance Company",
    "United India Insurance Company",
    "Universal Sompo General Insurance",
    "Zuno General Insurance",
    "Star Health and Allied Insurance",
    "અન્ય"
]

# ----------------- DATE FORMATTING UTILITIES -----------------
def parse_to_date_obj(date_val):
    if pd.isna(date_val) or not str(date_val).strip():
        return None
    s = str(date_val).strip().split(" ")[0]
    formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    return None

def format_to_dd_mm_yyyy(date_val):
    d_obj = parse_to_date_obj(date_val)
    if d_obj:
        return d_obj.strftime("%d/%m/%Y")
    return str(date_val)

@st.cache_resource
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(credentials)
        return None
    except Exception:
        return None

def get_sheet():
    client = get_gspread_client()
    if client:
        try:
            return client.open(SHEET_NAME).sheet1
        except Exception:
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
            df_clean = df[COLUMNS].dropna(how="all")
            if not df_clean.empty:
                df_clean["expiry_date"] = df_clean["expiry_date"].apply(format_to_dd_mm_yyyy)
                df_clean["last_renewed"] = df_clean["last_renewed"].apply(format_to_dd_mm_yyyy)
                df_clean.to_csv(LOCAL_CSV, index=False)
                return df_clean
        except Exception:
            pass
            
    if os.path.exists(LOCAL_CSV):
        df_local = pd.read_csv(LOCAL_CSV)
        for col in COLUMNS:
            if col not in df_local.columns:
                df_local[col] = ""
        df_local["expiry_date"] = df_local["expiry_date"].apply(format_to_dd_mm_yyyy)
        df_local["last_renewed"] = df_local["last_renewed"].apply(format_to_dd_mm_yyyy)
        return df_local[COLUMNS]
    return pd.DataFrame(columns=COLUMNS)

def save_all_to_sheet(df):
    sheet = get_sheet()
    df["expiry_date"] = df["expiry_date"].apply(format_to_dd_mm_yyyy)
    df["last_renewed"] = df["last_renewed"].apply(format_to_dd_mm_yyyy)
    df.to_csv(LOCAL_CSV, index=False)
    if sheet:
        try:
            sheet.clear()
            sheet.append_row(COLUMNS)
            if not df.empty:
                sheet.append_rows(df.values.tolist())
            return True
        except Exception:
            return False
    return False

def insert_policy(name, mobile, vehicle_no, v_type, company, policy_no, premium, expiry, remarks):
    df = get_data()
    if not df.empty and "id" in df.columns:
        try:
            valid_ids = pd.to_numeric(df["id"], errors="coerce").dropna()
            new_id = int(valid_ids.max() + 1) if not valid_ids.empty else 1
        except Exception:
            new_id = len(df) + 1
    else:
        new_id = 1

    formatted_exp = format_to_dd_mm_yyyy(expiry)
    today_str = date.today().strftime("%d/%m/%Y")

    new_row = [
        new_id,
        name,
        str(mobile),
        vehicle_no,
        v_type,
        company,
        str(policy_no),
        premium,
        formatted_exp,
        remarks,
        today_str
    ]
    
    sheet = get_sheet()
    if sheet:
        try:
            sheet.append_row(new_row)
        except Exception:
            pass
            
    row_dict = dict(zip(COLUMNS, new_row))
    new_df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    new_df.to_csv(LOCAL_CSV, index=False)

def update_policy(p_id, name, mobile, vehicle_no, v_type, company, policy_no, premium, expiry, remarks):
    df = get_data()
    idx = df[df["id"].astype(str) == str(p_id)].index
    if not idx.empty:
        i = idx[0]
        df.at[i, "name"] = name
        df.at[i, "mobile"] = str(mobile)
        df.at[i, "vehicle_no"] = vehicle_no
        df.at[i, "vehicle_type"] = v_type
        df.at[i, "policy_company"] = company
        df.at[i, "policy_no"] = str(policy_no)
        df.at[i, "premium_amount"] = premium
        df.at[i, "expiry_date"] = format_to_dd_mm_yyyy(expiry)
        df.at[i, "remarks"] = remarks
        save_all_to_sheet(df)

def delete_policy(p_id):
    df = get_data()
    df = df[df["id"].astype(str) != str(p_id)].reset_index(drop=True)
    save_all_to_sheet(df)

def renew_one_year(p_id, current_expiry_str):
    curr_dt = parse_to_date_obj(current_expiry_str)
    if not curr_dt:
        curr_dt = date.today()
    new_dt = (curr_dt + timedelta(days=365)).strftime("%d/%m/%Y")
    today_str = date.today().strftime("%d/%m/%Y")
    
    df = get_data()
    idx = df[df["id"].astype(str) == str(p_id)].index
    if not idx.empty:
        i = idx[0]
        df.at[i, "expiry_date"] = new_dt
        df.at[i, "last_renewed"] = today_str
        save_all_to_sheet(df)

# ----------------- OCR / PDF AUTO-PARSER -----------------
def extract_info_from_pdf(uploaded_file):
    extracted = {
        "name": "",
        "mobile": "",
        "vehicle_no": "",
        "policy_no": "",
        "premium": 0,
        "expiry_date": None,
        "company": "ICICI Lombard General Insurance",
        "vehicle_type": "2 Wheeler"
    }
    
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        
        # ૧. વાહન નંબર (GJ-xx-xxxx)
        veh_match = re.search(r'\b(GJ[\s\-]?[0-9]{1,2}[\s\-]?[A-Z]{1,3}[\s\-]?[0-9]{4})\b', text, re.IGNORECASE)
        if veh_match:
            raw_v = veh_match.group(1).upper().replace(" ", "").replace("-", "")
            if len(raw_v) >= 9:
                extracted["vehicle_no"] = f"{raw_v[:2]}-{raw_v[2:4]}-{raw_v[4:-4]}-{raw_v[-4:]}"

        # ૨. મોબાઈલ નંબર
        mob_match = re.search(r'\b([6-9][0-9]{9})\b', text)
        if mob_match:
            extracted["mobile"] = mob_match.group(1)

        # ૩. પોલિસી નંબર
        pol_match = re.search(r'(?:Policy\s*(?:No|Number|#)?[:\s\-]+)([A-Z0-9\/\-]{8,25})', text, re.IGNORECASE)
        if pol_match:
            extracted["policy_no"] = pol_match.group(1).strip()

        # ૪. પ્રીમિયમ રકમ
        prem_match = re.search(r'(?:Total\s*Premium|Net\s*Premium|Gross\s*Premium|Amount)[:\s₹Rs\.]*([0-9,]+(?:\.[0-9]{2})?)', text, re.IGNORECASE)
        if prem_match:
            clean_p = prem_match.group(1).replace(",", "")
            try:
                extracted["premium"] = int(float(clean_p))
            except Exception:
                pass

        # ૫. એક્સપાયરી તારીખ
        date_match = re.search(r'(?:Expiry\s*Date|Valid\s*Upto|Period\s*of\s*Insurance\s*To|To\s*Midnight\s*of)[:\s]+([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{4})', text, re.IGNORECASE)
        if date_match:
            parsed = parse_to_date_obj(date_match.group(1))
            if parsed:
                extracted["expiry_date"] = parsed

        # ૬. કંપની શોધવી
        for comp in COMPANIES_LIST:
            short_name = comp.split(" ")[0].lower()
            if short_name in text.lower():
                extracted["company"] = comp
                break
                
        # ૭. વાહનનો પ્રકાર
        if any(w in text.lower() for w in ["motorcycle", "scooter", "activa", "two wheeler", "2-wheeler"]):
            extracted["vehicle_type"] = "2 Wheeler"
        elif any(w in text.lower() for w in ["car", "motor car", "private car", "4-wheeler"]):
            extracted["vehicle_type"] = "4 Wheeler (Car)"
        elif any(w in text.lower() for w in ["goods", "carrier", "truck", "commercial"]):
            extracted["vehicle_type"] = "Commercial Goods"
        elif any(w in text.lower() for w in ["tractor"]):
            extracted["vehicle_type"] = "Tractor"
            
    except Exception as e:
        st.warning(f"⚠️ PDF વાંચવામાં તકલીફ: {e}")
        
    return extracted

# ----------------- MODERN CSS -----------------
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
    html, body, [class*="css"], .stMarkdown, .stText { font-family: 'Inter', sans-serif; }
    h1, h2, h3, h4, h5, h6, .stMetric label { font-family: 'Poppins', sans-serif !important; font-weight: 600 !important; }
    .main { background-color: #f1f5f9; }
    .login-badge { background: #eff6ff; color: #1e3a8a; padding: 6px 14px; border-radius: 9999px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 12px; border: 1px solid #bfdbfe; }
    [data-testid="stMetric"] { background: #ffffff; padding: 18px 20px; border-radius: 14px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05); border: 1px solid #e2e8f0; border-top: 4px solid #1E3A8A; }
    .reminder-card { background: #ffffff; border-radius: 14px; padding: 18px; margin-bottom: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); }
    .customer-found-card { background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 14px; padding: 18px; margin-top: 15px; margin-bottom: 15px; }
    .customer-not-found-card { background: #fef2f2; border: 1.5px solid #fca5a5; border-radius: 14px; padding: 18px; margin-top: 15px; margin-bottom: 15px; }
    .badge-urgent { background: #fee2e2; color: #b91c1c; padding: 5px 12px; border-radius: 9999px; font-weight: 600; font-size: 12px; border: 1px solid #fca5a5; }
    .badge-warning { background: #fef3c7; color: #b45309; padding: 5px 12px; border-radius: 9999px; font-weight: 600; font-size: 12px; border: 1px solid #fde68a; }
    .badge-success { background: #dcfce7; color: #166534; padding: 5px 12px; border-radius: 9999px; font-weight: 600; font-size: 12px; border: 1px solid #bbf7d0; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] .stButton > button { width: 100% !important; text-align: left !important; justify-content: flex-start !important; padding: 10px 16px !important; border-radius: 10px !important; margin-bottom: 6px !important; font-family: 'Poppins', sans-serif !important; font-size: 14px !important; font-weight: 500 !important; border: 1px solid #e2e8f0 !important; background-color: #f8fafc !important; color: #334155 !important; }
    [data-testid="stSidebar"] .stButton > button:hover { background-color: #1E3A8A !important; color: #ffffff !important; border-color: #1E3A8A !important; }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] { background-color: #1E3A8A !important; color: #ffffff !important; border-color: #1E3A8A !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- LOGIN SCREEN -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "app_pin" not in st.session_state:
    st.session_state.app_pin = DEFAULT_PIN

if not st.session_state.authenticated:
    _, col_mid, _ = st.columns([1, 1.4, 1])
    with col_mid:
        st.markdown("<br>", unsafe_allow_html=True)
        logo_c1, logo_c2, logo_c3 = st.columns([1, 2, 1])
        with logo_c2:
            if os.path.exists("HARI OM IL.jpg"):
                st.image("HARI OM IL.jpg", use_container_width=True)
            elif os.path.exists("logo.jpg"):
                st.image("logo.jpg", use_container_width=True)
            else:
                st.markdown("<h1 style='text-align:center; font-size:48px;'>🛡️</h1>", unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align:center; margin-bottom: 15px;'>
            <span class="login-badge">🔐 સુરક્ષિત પોર્ટલ</span>
            <h3 style='margin:0; color:#0f172a;'>હરિ ઓમ ઇન્સ્યોરન્સ</h3>
            <p style='color:#64748b; font-size:13px; margin-top:4px;'>પોર્ટલ અનલોક કરવા ૪-અંકનો સિક્યોરિટી પિન દાખલ કરો</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("pin_form"):
            pin_input = st.text_input("સિક્યોરિટી પિન", type="password", placeholder="••••", label_visibility="collapsed")
            if st.form_submit_button("🔓 પોર્ટલ ખોલો (Login)", use_container_width=True):
                if pin_input == st.session_state.app_pin:
                    st.session_state.authenticated = True
                    st.success("✅ લોગિન સફળ!")
                    st.rerun()
                else:
                    st.error("❌ ખોટો પિન! ફરીથી પ્રયાસ કરો.")
    st.stop()

# ----------------- MAIN APP INITIALIZATION -----------------
df = get_data()

if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 ડેશબોર્ડ"

# ----------------- સાઇડબાર નેવિગેશન -----------------
with st.sidebar:
    logo_c1, logo_c2, logo_c3 = st.columns([1, 2.5, 1])
    with logo_c2:
        if os.path.exists("HARI OM IL.jpg"):
            st.image("HARI OM IL.jpg", use_container_width=True)
        elif os.path.exists("logo.jpg"):
            st.image("logo.jpg", use_container_width=True)
        else:
            st.markdown("<h3 style='text-align:center; color:#1e3a8a;'>🛡️ HARI OM</h3>", unsafe_allow_html=True)

    st.markdown("<p style='font-size:11px; color:#64748b; font-weight:700; text-transform:uppercase; margin: 12px 0 6px 0;'>મેનૂ વિકલ્પો</p>", unsafe_allow_html=True)
    menu_items = [
        "📊 ડેશબોર્ડ", 
        "🔔 રીમાઇન્ડર ડેસ્ક", 
        "➕ નવી પોલિસી એન્ટ્રી", 
        "📁 તમામ ગ્રાહકોની યાદી", 
        "⚙️ એડિટ / ડિલીટ",
        "💾 બેકઅપ & રિસ્ટોર",
        "🔐 પિન બદલો"
    ]
    
    for item in menu_items:
        is_active = (st.session_state.current_page == item)
        if st.button(item, key=f"nav_{item}", type="primary" if is_active else "secondary"):
            st.session_state.current_page = item
            st.rerun()
            
    st.markdown("---")
    if st.button("🔒 લોગઆઉટ (Logout)"):
        st.session_state.authenticated = False
        st.rerun()
        
    st.markdown("""
    <div style='background:#f8fafc; padding:10px 12px; border-radius:10px; border:1px solid #e2e8f0; font-size:11.5px; color:#475569; margin-top:10px;'>
        <b>📍 સરનામું:</b> F-46, વાત્સલ્ય સ્ટેટસ, ધવલ પ્લાઝા પાસે, કડી - 384440<br>
        <b>📞 સંપર્ક:</b> 7698564672 / 9714776364
    </div>
    """, unsafe_allow_html=True)

# ----------------- 1. ડેશબોર્ડ -----------------
if st.session_state.current_page == "📊 ડેશબોર્ડ":
    st.markdown("<h2 style='color:#0f172a;'>📊 બિઝનેસ ડેશબોર્ડ</h2>", unsafe_allow_html=True)
    
    # ક્વિક સર્ચ
    st.markdown("### 🔍 ક્વિક સર્ચ & ગ્રાહક સ્ટેટસ (નવો કે જૂનો ગ્રાહક)")
    search_term = st.text_input("વાહન નંબર, મોબાઈલ નંબર કે પોલિસી નંબર નાખો:", placeholder="GJ-xx-xxxx / મોબાઈલ / પોલિસી નં.")
    
    if search_term.strip():
        clean_query = search_term.strip().lower()
        search_results = df[
            df["vehicle_no"].astype(str).str.lower().str.replace("-", "").str.replace(" ", "").str.contains(clean_query.replace("-", "").replace(" ", "")) |
            df["mobile"].astype(str).str.contains(clean_query) |
            df["policy_no"].astype(str).str.lower().str.contains(clean_query)
        ]
        
        if not search_results.empty:
            st.markdown(f"""
            <div class="customer-found-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="margin:0; color:#166534;">✅ પોલિસી મળી ગઈ (જૂનો ગ્રાહક છે)</h4>
                    <span class="badge-success">કુલ રેકોર્ડ: {len(search_results)}</span>
                </div>
                <p style="margin:5px 0 0 0; color:#15803d; font-size:13px;">આ ગ્રાહકનો ડેટા પહેલેથી જ આપણી સિસ્ટમમાં ઉપલબ્ધ છે.</p>
            </div>
            """, unsafe_allow_html=True)
            
            for _, r in search_results.iterrows():
                col_det1, col_det2 = st.columns([3, 1])
                with col_det1:
                    st.markdown(f"👤 **{r['name']}** | 🚗 વાહન: `{r['vehicle_no']}` ({r['vehicle_type']})")
                    st.markdown(f"🏢 **કંપની:** {r['policy_company']} | 📋 **પોલિસી નં:** `{r['policy_no']}` | 💰 **પ્રીમિયમ:** ₹{r['premium_amount']} | 📅 **એક્સપાયરી:** `{r['expiry_date']}`")
                with col_det2:
                    msg_text = f"નમસ્તે {r['name']}જી, આપના વાહન *{r['vehicle_no']}* ની પોલિસી એક્સપાયરી તારીખ *{r['expiry_date']}* છે. રિન્યુઅલ માટે સંપર્ક કરો: હરિ ઓમ ઇન્સ્યોરન્સ, કડી (Mo: 7698564672)."
                    wa_url = f"https://wa.me/91{''.join(filter(str.isdigit, str(r['mobile'])))[-10:]}?text={urllib.parse.quote(msg_text)}"
                    st.link_button("📲 WhatsApp", wa_url)
                st.divider()
        else:
            st.markdown("<div class='customer-not-found-card'><b>❌ નવો ગ્રાહક છે (રેકોર્ડ મળ્યો નથી)</b></div>", unsafe_allow_html=True)
            if st.button("➕ આ નવા ગ્રાહકની પોલિસી ઉમેરો"):
                st.session_state.current_page = "➕ નવી પોલિસી એન્ટ્રી"
                st.rerun()
    st.markdown("---")

    if not df.empty:
        df_dash = df.copy()
        df_dash["expiry_dt"] = df_dash["expiry_date"].apply(parse_to_date_obj)
        df_dash["premium_clean"] = pd.to_numeric(df_dash["premium_amount"], errors="coerce").fillna(0)
        today = date.today()
        valid = df_dash.dropna(subset=["expiry_dt"])
        days = valid["expiry_dt"].apply(lambda x: (x - today).days)
        
        due_15 = valid[(days <= 15) & (days >= 0)]
        expired = valid[days < 0]
        active = valid[days > 15]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 કુલ પોલિસી", len(df))
        c2.metric("⚠️ ૧૫ દિવસમાં બાકી", len(due_15))
        c3.metric("✅ એક્ટિવ પોલિસી", len(active))
        c4.metric("💰 કુલ પ્રીમિયમ", f"₹{df_dash['premium_clean'].sum():,.0f}")
    else:
        st.info("ડેટાબેઝ ખાલી છે.")

# ----------------- 2. રીમાઇન્ડર ડેસ્ક -----------------
elif st.session_state.current_page == "🔔 રીમાઇન્ડર ડેસ્ક":
    st.markdown("<h2 style='color:#0f172a;'>🔔 પોલિસી રિન્યુઅલ રીમાઇન્ડર (૧૫ દિવસ)</h2>", unsafe_allow_html=True)
    if not df.empty:
        df_rem = df.copy()
        df_rem["expiry_dt"] = df_rem["expiry_date"].apply(parse_to_date_obj)
        today = date.today()
        df_rem = df_rem.dropna(subset=["expiry_dt"])
        df_rem["days_left"] = df_rem["expiry_dt"].apply(lambda x: (x - today).days)
        reminders = df_rem[(df_rem["days_left"] <= 15) & (df_rem["days_left"] >= 0)].sort_values(by="days_left")
        
        if not reminders.empty:
            for _, row in reminders.iterrows():
                badge = f"<span class='badge-urgent'>🚨 {row['days_left']} દિવસ બાકી</span>" if row['days_left'] <= 3 else f"<span class='badge-warning'>⏳ {row['days_left']} દિવસ બાકી</span>"
                msg = (
                    f"નમસ્તે {row['name']}જી,\n\n"
                    f"હરિ ઓમ ઇન્સ્યોરન્સ તરફથી યાદી કે આપના વાહન નંબર *{row['vehicle_no']}* ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['expiry_date']}* ના રોજ પૂર્ણ થઈ રહી છે ({row['days_left']} દિવસ બાકી).\n\n"
                    f"📄 પોલિસી નં: {row['policy_no']}\n"
                    f"🏢 કંપની: {row['policy_company']}\n\n"
                    f"સમયસર રિન્યુ કરાવવા વિનંતી.\n"
                    f"📞 7698564672 / 9714776364\n"
                    f"*હરિ ઓમ ઇન્સ્યોરન્સ & લોન એડવાઈઝર, કડી*"
                )
                clean_mobile = "".join(filter(str.isdigit, str(row['mobile'])))[-10:]
                wa_url = f"https://wa.me/91{clean_mobile}?text={urllib.parse.quote(msg)}"
                
                st.markdown(f"""
                <div class="reminder-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;">{row['name']} ({row['vehicle_no']})</h4>
                        {badge}
                    </div>
                    <p style="margin:8px 0 0 0; font-size:13px; color:#475569;">
                        <b>કંપની:</b> {row['policy_company']} | <b>પોલિસી નં:</b> {row['policy_no']} | <b>એક્સપાયરી (DD/MM/YYYY):</b> {row['expiry_date']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2 = st.columns([1, 4])
                with b1:
                    st.link_button("📲 WhatsApp મોકલો", wa_url)
                with b2:
                    if st.button(f"⚡ ૧-ક્લિક રિન્યુ (૧ વર્ષ)", key=f"ren_{row['id']}"):
                        renew_one_year(row['id'], row['expiry_date'])
                        st.success("પોલિસી ૧ વર્ષ માટે રિન્યુ થઈ ગઈ!")
                        st.rerun()
                st.divider()
        else:
            st.success("આગામી ૧૫ દિવસમાં કોઈ પોલિસી એક્સપાયર થતી નથી.")

# ----------------- 3. નવી પોલિસી એન્ટ્રી (WITH PDF AUTO-FETCH & 24 COMPANIES) -----------------
elif st.session_state.current_page == "➕ નવી પોલિસી એન્ટ્રી":
    st.markdown("<h2 style='color:#0f172a;'>➕ નવી પોલિસી ઉમેરો</h2>", unsafe_allow_html=True)
    
    st.markdown("### 📄 પોલિસી PDF અપલોડ કરો (Auto-Fetch Data)")
    uploaded_pdf = st.file_uploader("જૂની અથવા નવી પોલિસીની PDF ફાઇલ અપલોડ કરો:", type=["pdf"])
    
    auto_data = {
        "name": "", "mobile": "", "vehicle_no": "", 
        "policy_no": "", "premium": 0, "expiry_date": date.today(), 
        "company": "ICICI Lombard General Insurance", "vehicle_type": "2 Wheeler"
    }
    
    if uploaded_pdf:
        with st.spinner("🔍 PDF માંથી વિગતો વાંચી રહ્યા છીએ..."):
            extracted = extract_info_from_pdf(uploaded_pdf)
            auto_data.update(extracted)
            if not auto_data["expiry_date"]:
                auto_data["expiry_date"] = date.today()
            st.success("✅ PDF માંથી વિગતો સફળતાપૂર્વક મેળવી લીધી છે! નીચે ચેક કરીને સેવ કરો.")

    with st.form("new_entry_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        name = c1.text_input("ગ્રાહકનું પૂરું નામ *", value=auto_data["name"])
        mobile = c2.text_input("મોબાઇલ નંબર *", value=auto_data["mobile"])
        vehicle_no = c1.text_input("વાહન નંબર (GJ-xx-xxxx) *", value=auto_data["vehicle_no"])
        
        v_types = ["2 Wheeler", "4 Wheeler (Car)", "Commercial Goods", "Passenger Taxi", "Tractor", "અન્ય"]
        v_idx = v_types.index(auto_data["vehicle_type"]) if auto_data["vehicle_type"] in v_types else 0
        vehicle_type = c2.selectbox("વાહનનો પ્રકાર", v_types, index=v_idx)
        
        c_idx = COMPANIES_LIST.index(auto_data["company"]) if auto_data["company"] in COMPANIES_LIST else 0
        company = c1.selectbox("ઇન્સ્યોરન્સ કંપની", COMPANIES_LIST, index=c_idx)
        
        policy_no = c2.text_input("પોલિસી નંબર", value=auto_data["policy_no"])
        premium = c1.number_input("પ્રીમિયમ રકમ (₹)", min_value=0, step=500, value=auto_data["premium"])
        expiry = c2.date_input("પોલિસી એક્સપાયરી તારીખ (DD/MM/YYYY) *", value=auto_data["expiry_date"], format="DD/MM/YYYY")
        remarks = st.text_input("નોંધ / રિમાર્ક્સ")
        
        if st.form_submit_button("💾 પોલિસી સેવ કરો"):
            if name.strip() and mobile.strip() and vehicle_no.strip():
                insert_policy(name.strip(), mobile.strip(), vehicle_no.upper().strip(), vehicle_type, company, policy_no.strip(), premium, expiry, remarks.strip())
                st.success("✅ નવો ગ્રાહક સફળતાપૂર્વક ઉમેરાઈ ગયો (DD/MM/YYYY ફોર્મેટમાં સેવ થયો)!")
                st.rerun()
            else:
                st.error("નામ, મોબાઇલ અને વાહન નંબર જરૂરી છે.")

# ----------------- 4. તમામ ગ્રાહકોની યાદી -----------------
elif st.session_state.current_page == "📁 તમામ ગ્રાહકોની યાદી":
    st.markdown("<h2 style='color:#0f172a;'>📁 તમામ ગ્રાહકોની યાદી (DD/MM/YYYY Live)</h2>", unsafe_allow_html=True)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv_exp = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Excel / CSV માં ડાઉનલોડ કરો", data=csv_exp, file_name="HariOm_Clients.csv", mime="text/csv")
    else:
        st.info("કોઈ ગ્રાહકનો ડેટા નથી.")

# ----------------- 5. એડિટ / ડિલીટ -----------------
elif st.session_state.current_page == "⚙️ એડિટ / ડિલીટ":
    st.markdown("<h2 style='color:#0f172a;'>⚙️ ગ્રાહક ડેટા સુધારો અથવા રદ કરો</h2>", unsafe_allow_html=True)
    if not df.empty:
        opts = {f"{r['id']}: {r['name']} - {r['vehicle_no']}": r['id'] for _, r in df.iterrows()}
        sel_label = st.selectbox("ગ્રાહક પસંદ કરો:", list(opts.keys()))
        
        if sel_label:
            p_id = opts[sel_label]
            s_row = df[df['id'].astype(str) == str(p_id)].iloc[0]
            
            with st.form("edit_form"):
                e1, e2 = st.columns(2)
                en = e1.text_input("નામ", value=str(s_row['name']))
                em = e2.text_input("મોબાઇલ", value=str(s_row['mobile']))
                ev = e1.text_input("વાહન નંબર", value=str(s_row['vehicle_no']))
                
                v_types = ["2 Wheeler", "4 Wheeler (Car)", "Commercial Goods", "Passenger Taxi", "Tractor", "અન્ય"]
                v_curr = str(s_row['vehicle_type'])
                v_edit_idx = v_types.index(v_curr) if v_curr in v_types else 0
                et = e2.selectbox("વાહનનો પ્રકાર", v_types, index=v_edit_idx)
                
                c_curr = str(s_row['policy_company'])
                c_edit_idx = COMPANIES_LIST.index(c_curr) if c_curr in COMPANIES_LIST else 0
                ec = e1.selectbox("ઇન્સ્યોરન્સ કંપની", COMPANIES_LIST, index=c_edit_idx)
                
                ep = e2.text_input("પોલિસી નં", value=str(s_row['policy_no']))
                
                try: prem_val = int(float(s_row['premium_amount']))
                except Exception: prem_val = 0
                eprem = e1.number_input("પ્રીમિયમ (₹)", value=prem_val, step=500)
                
                exp_date_obj = parse_to_date_obj(s_row['expiry_date']) or date.today()
                eexp = e2.date_input("એક્સપાયરી તારીખ", value=exp_date_obj, format="DD/MM/YYYY")
                erem = st.text_input("નોંધ", value=str(s_row['remarks']))
                
                ub1, ub2 = st.columns(2)
                if ub1.form_submit_button("🔄 વિગતો અપડેટ કરો"):
                    update_policy(p_id, en.strip(), em.strip(), ev.upper().strip(), et, ec, ep.strip(), eprem, eexp, erem.strip())
                    st.success("વિગતો અપડેટ થઈ ગઈ!")
                    st.rerun()
                if ub2.form_submit_button("🗑️ એન્ટ્રી ડિલીટ કરો"):
                    delete_policy(p_id)
                    st.warning("એન્ટ્રી ડિલીટ થઈ ગઈ!")
                    st.rerun()
    else:
        st.info("ડેટાબેઝ ખાલી છે.")

# ----------------- 6. બેકઅપ અને રિસ્ટોર -----------------
elif st.session_state.current_page == "💾 બેકઅપ & રિસ્ટોર":
    st.markdown("<h2 style='color:#0f172a;'>💾 ડેટા બેકઅપ અને રિસ્ટોર</h2>", unsafe_allow_html=True)
    bk1, bk2 = st.columns(2)
    with bk1:
        st.markdown("### 📥 ડાઉનલોડ બેકઅપ")
        if not df.empty:
            bk_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ ડેટાબેઝ ડાઉનલોડ (CSV)", data=bk_csv, file_name=f"hari_om_backup_{date.today().strftime('%d_%m_%Y')}.csv", mime="text/csv")
    with bk2:
        st.markdown("### 📤 રિસ્ટોર ડેટા")
        up_file = st.file_uploader("CSV ફાઇલ અપલોડ કરો", type=["csv"])
        if up_file and st.button("🚀 ડેટા રિસ્ટોર કરો"):
            try:
                new_df = pd.read_csv(up_file)
                for col in COLUMNS:
                    if col not in new_df.columns:
                        new_df[col] = ""
                new_df = new_df[COLUMNS]
                save_all_to_sheet(new_df)
                st.success("ડેટા સફળતાપૂર્વક રિસ્ટોર થઈ ગયો!")
                st.rerun()
            except Exception as err:
                st.error(f"એરર આવી: {err}")

# ----------------- 7. પિન બદલો -----------------
elif st.session_state.current_page == "🔐 પિન બદલો":
    st.markdown("<h2 style='color:#0f172a;'>🔐 સિક્યોરિટી પિન બદલો</h2>", unsafe_allow_html=True)
    col_p1, _ = st.columns([1.5, 1])
    with col_p1:
        with st.form("change_pin_form"):
            old_pin = st.text_input("જૂનો પિન", type="password")
            new_pin = st.text_input("નવો પિન", type="password")
            confirm_pin = st.text_input("નવો પિન કન્ફર્મ કરો", type="password")
            
            if st.form_submit_button("💾 નવો પિન સેવ કરો"):
                if old_pin != st.session_state.app_pin:
                    st.error("❌ જૂનો પિન ખોટો છે.")
                elif len(new_pin.strip()) < 4:
                    st.warning("⚠️ નવો પિન ઓછામાં ઓછો ૪ અંકનો હોવો જોઈએ.")
                elif new_pin != confirm_pin:
                    st.error("❌ નવો પિન મેચ થતો નથી.")
                else:
                    st.session_state.app_pin = new_pin.strip()
                    st.success("✅ સિક્યોરિટી પિન બદલાઈ ગયો છે!")
