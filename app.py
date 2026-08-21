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

# ----------------- GOOGLE SHEETS સેટઅપ -----------------
SHEET_NAME = "Hari_Om_Insurance_DB"
DEFAULT_PIN = "7698"

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
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            return gspread.authorize(credentials)
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
        except Exception:
            pass
            
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
            
    row_dict = dict(zip(COLUMNS, new_row))
    new_df = pd.concat([df, pd.DataFrame([row_dict])], ignore_index=True)
    new_df.to_csv("insurance_data.csv", index=False)
    return success

def renew_one_year(p_id, current_expiry_str):
    try:
        curr_dt = datetime.strptime(str(current_expiry_str), "%Y-%m-%d").date()
    except Exception:
        curr_dt = date.today()
    new_dt = str(curr_dt + timedelta(days=365))
    
    sheet = get_sheet()
    if sheet:
        try:
            cell = sheet.find(str(p_id))
            if cell:
                row_num = cell.row
                sheet.update_cell(row_num, 9, new_dt)
                sheet.update_cell(row_num, 11, str(date.today()))
        except Exception:
            pass

# ----------------- MODERN CUSTOM CSS -----------------
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
    [data-testid="stSidebar"] .stButton > button[kind="primary"] { background-color: #1E3A8A !important; color: #ffffff !important; border-color: #1E3A8A !important; }
</style>
""", unsafe_allow_html=True)

# ----------------- LOGIN SCREEN -----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

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
                if pin_input == DEFAULT_PIN:
                    st.session_state.authenticated = True
                    st.success("✅ લોગિન સફળ!")
                    st.rerun()
                else:
                    st.error("❌ ખોટો પિન!")
    st.stop()

# ----------------- MAIN APP -----------------
df = get_data()

if 'current_page' not in st.session_state:
    st.session_state.current_page = "📊 ડેશબોર્ડ"

with st.sidebar:
    logo_c1, logo_c2, logo_c3 = st.columns([1, 2.5, 1])
    with logo_c2:
        if os.path.exists("HARI OM IL.jpg"):
            st.image("HARI OM IL.jpg", use_container_width=True)
        elif os.path.exists("logo.jpg"):
            st.image("logo.jpg", use_container_width=True)

    st.markdown("<p style='font-size:11px; color:#64748b; font-weight:700; text-transform:uppercase; margin: 12px 0 6px 0;'>મેનૂ વિકલ્પો</p>", unsafe_allow_html=True)
    menu_items = ["📊 ડેશબોર્ડ", "🔔 રીમાઇન્ડર ડેસ્ક", "➕ નવી પોલિસી એન્ટ્રી", "📁 તમામ ગ્રાહકોની યાદી"]
    
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
    search_term = st.text_input("વાહન નંબર, મોબાઈલ નંબર કે પોલિસી નંબર નાખો:", placeholder="વાહન નંબર / મોબાઈલ / પોલિસી નં.")
    
    if search_term.strip():
        clean_query = search_term.strip().lower()
        search_results = df[
            df["vehicle_no"].astype(str).str.lower().str.replace("-", "").str.replace(" ", "").str.contains(clean_query.replace("-", "").replace(" ", "")) |
            df["mobile"].astype(str).str.contains(clean_query) |
            df["policy_no"].astype(str).str.lower().str.contains(clean_query)
        ]
        
        if not search_results.empty:
            st.markdown("<div class='customer-found-card'><b>✅ જૂનો ગ્રાહક છે (પોલિસી સિસ્ટમમાં ઉપલબ્ધ છે)</b></div>", unsafe_allow_html=True)
            for _, r in search_results.iterrows():
                col_det1, col_det2 = st.columns([3, 1])
                with col_det1:
                    st.markdown(f"👤 **{r['name']}** | 🚗 વાહન: `{r['vehicle_no']}` ({r['vehicle_type']})")
                    st.markdown(f"🏢 **કંપની:** {r['policy_company']} | 📋 **પોલિસી નં:** `{r['policy_no']}` | 💰 **પ્રીમિયમ:** ₹{r['premium_amount']} | 📅 **એક્સપાયરી:** `{r['expiry_date']}`")
                with col_det2:
                    msg_text = f"નમસ્તે {r['name']}જી, આપના વાહન *{r['vehicle_no']}* ની પોલિસી એક્સપાયરી તારીખ *{r['expiry_date']}* છે. રિન્યુઅલ માટે સંપર્ક કરો: હરિ ઓમ ઇન્સ્યોરન્સ (Mo: 7698564672)."
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
        df_dash["expiry_dt"] = pd.to_datetime(df_dash["expiry_date"], errors="coerce").dt.date
        df_dash["premium_clean"] = pd.to_numeric(df_dash["premium_amount"], errors="coerce").fillna(0)
        today = date.today()
        valid = df_dash.dropna(subset=["expiry_dt"])
        days = valid["expiry_dt"].apply(lambda x: (x - today).days)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 કુલ પોલિસી", len(df))
        c2.metric("⚠️ ૧૫ દિવસમાં બાકી", len(valid[(days <= 15) & (days >= 0)]))
        c3.metric("✅ એક્ટિવ પોલિસી", len(valid[days > 15]))
        c4.metric("💰 કુલ પ્રીમિયમ", f"₹{df_dash['premium_clean'].sum():,.0f}")
    else:
        st.info("ડેટાબેઝ ખાલી છે.")

# ----------------- 2. રીમાઇન્ડર ડેસ્ક -----------------
elif st.session_state.current_page == "🔔 રીમાઇન્ડર ડેસ્ક":
    st.markdown("<h2 style='color:#0f172a;'>🔔 પોલિસી રિન્યુઅલ રીમાઇન્ડર (૧૫ દિવસ)</h2>", unsafe_allow_html=True)
    if not df.empty:
        df_rem = df.copy()
        df_rem["expiry_dt"] = pd.to_datetime(df_rem["expiry_date"], errors="coerce").dt.date
        today = date.today()
        df_rem = df_rem.dropna(subset=["expiry_dt"])
        df_rem["days_left"] = df_rem["expiry_dt"].apply(lambda x: (x - today).days)
        reminders = df_rem[(df_rem["days_left"] <= 15) & (df_rem["days_left"] >= 0)].sort_values(by="days_left")
        
        if not reminders.empty:
            for _, row in reminders.iterrows():
                badge = f"<span class='badge-urgent'>🚨 {row['days_left']} દિવસ બાકી</span>" if row['days_left'] <= 3 else f"<span class='badge-warning'>⏳ {row['days_left']} દિવસ બાકી</span>"
                msg = f"નમસ્તે {row['name']}જી,\n\nહરિ ઓમ ઇન્સ્યોરન્સ તરફથી યાદી કે આપના વાહન નંબર *{row['vehicle_no']}* ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['expiry_date']}* ના રોજ પૂર્ણ થઈ રહી છે ({row['days_left']} દિવસ બાકી).\n\n📄 પોલિસી નં: {row['policy_no']}\n🏢 કંપની: {row['policy_company']}\n\nસમયસર રિન્યુ કરાવવા વિનંતી.\n📞 7698564672 / 9714776364"
                clean_mobile = "".join(filter(str.isdigit, str(row['mobile'])))[-10:]
                wa_url = f"https://wa.me/91{clean_mobile}?text={urllib.parse.quote(msg)}"
                
                st.markdown(f"""
                <div class="reminder-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0;">{row['name']} ({row['vehicle_no']})</h4>
                        {badge}
                    </div>
                    <p style="margin:8px 0 0 0; font-size:13px; color:#475569;">
                        <b>કંપની:</b> {row['policy_company']} | <b>પોલિસી નં:</b> {row['policy_no']} | <b>એક્સપાયરી:</b> {row['expiry_date']}
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

# ----------------- 3. નવી પોલિસી એન્ટ્રી -----------------
elif st.session_state.current_page == "➕ નવી પોલિસી એન્ટ્રી":
    st.markdown("<h2 style='color:#0f172a;'>➕ નવી પોલિસી ઉમેરો</h2>", unsafe_allow_html=True)
    with st.form("new_entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("ગ્રાહકનું પૂરું નામ *")
        mobile = c2.text_input("મોબાઇલ નંબર *")
        vehicle_no = c1.text_input("વાહન નંબર (GJ-xx-xxxx) *")
        vehicle_type = c2.selectbox("વાહનનો પ્રકાર", ["2 Wheeler", "4 Wheeler (Car)", "Commercial Goods", "Passenger Taxi", "Tractor", "અન્ય"])
        company = c1.selectbox("ઇન્સ્યોરન્સ કંપની", ["ICICI Lombard", "Bajaj Allianz", "Tata AIG", "New India", "HDFC ERGO", "Go Digit", "National", "Star Health", "અન્ય"])
        policy_no = c2.text_input("પોલિસી નંબર")
        premium = c1.number_input("પ્રીમિયમ રકમ (₹)", min_value=0, step=500)
        expiry = c2.date_input("પોલિસી એક્સપાયરી તારીખ *")
        remarks = st.text_input("નોંધ / રિમાર્ક્સ")
        
        if st.form_submit_button("💾 પોલિસી સેવ કરો"):
            if name.strip() and mobile.strip() and vehicle_no.strip():
                is_saved = insert_policy(name.strip(), mobile.strip(), vehicle_no.upper().strip(), vehicle_type, company, policy_no.strip(), premium, str(expiry), remarks.strip())
                if is_saved:
                    st.success("✅ નવો ગ્રાહક સફળતાપૂર્વક Google Sheets માં ઉમેરાઈ ગયો!")
                else:
                    st.warning("⚠️ Google Sheets માં સેવ ન થયો (ડેટા લોકલ સેવ થયો છે).")
                st.rerun()
            else:
                st.error("નામ, મોબાઇલ અને વાહન નંબર જરૂરી છે.")

# ----------------- 4. તમામ ગ્રાહકોની યાદી -----------------
elif st.session_state.current_page == "📁 તમામ ગ્રાહકોની યાદી":
    st.markdown("<h2 style='color:#0f172a;'>📁 તમામ ગ્રાહકોની યાદી (Google Sheets Live)</h2>", unsafe_allow_html=True)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        csv_exp = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Excel / CSV માં ડાઉનલોડ કરો", data=csv_exp, file_name="HariOm_Clients.csv", mime="text/csv")
    else:
        st.info("શીટમાં કોઈ ડેટા નથી.")
