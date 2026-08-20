import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
import urllib.parse
from streamlit_gsheets import GSheetsConnection

# પેજ કન્ફિગરેશન
st.set_page_config(
    page_title="Hari Om Insurance Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# કસ્ટમ CSS સ્ટાઇલિંગ
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #1E3A8A;
    }
    .reminder-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .badge-urgent {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
    .badge-warning {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

COLUMNS = [
    "Name", "Mobile", "Vehicle_No", "Vehicle_Type", 
    "Policy_Company", "Policy_No", "Premium_Amount", 
    "Expiry_Date", "Remarks", "Last_Renewed"
]

# ડેટાબેઝ હેન્ડલર (Google Sheets જો કનેક્ટ હોય તો એમાંથી, નહીંતર Local CSV)
def get_connection():
    try:
        return st.connection("gsheets", type=GSheetsConnection)
    except Exception:
        return None

conn = get_connection()
DB_FILE = "insurance_data.csv"

def load_data():
    if conn:
        try:
            df = conn.read(ttl=0)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNS].dropna(how="all")
        except Exception:
            pass
    
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[COLUMNS]
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    if conn:
        try:
            conn.update(data=df)
        except Exception:
            pass
    df.to_csv(DB_FILE, index=False)

df = load_data()

# ----------------- SIDEBAR NAVIGATION MENU -----------------
with st.sidebar:
    if os.path.exists("HARI OM IL.jpg"):
        st.image("HARI OM IL.jpg", use_container_width=True)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.markdown("## 🛡️ હરિ ઓમ ઇન્સ્યોરન્સ")

    st.markdown("### 📌 નેવિગેશન મેનૂ")
    menu_choice = st.radio(
        "મેનૂ પસંદ કરો:",
        [
            "📊 ડેશબોર્ડ", 
            "🔔 રીમાઇન્ડર ડેસ્ક", 
            "➕ નવી પોલિસી એન્ટ્રી", 
            "📁 તમામ ગ્રાહકોની યાદી", 
            "⚙️ એડિટ / ડિલીટ",
            "💾 ડેટા બેકઅપ & સેટિંગ્સ"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    **સંપર્ક સહાય:**  
    📍 કડી - 384440  
    📞 7698564672  
    📞 9714776364  
    """)

# ----------------- 1. ડેશબોર્ડ -----------------
if menu_choice == "📊 ડેશબોર્ડ":
    st.title("📊 બિઝનેસ ડેશબોર્ડ")
    if not df.empty:
        df_dash = df.copy()
        df_dash["Expiry_Date_dt"] = pd.to_datetime(df_dash["Expiry_Date"], errors="coerce").dt.date
        df_dash["Premium_Clean"] = pd.to_numeric(df_dash["Premium_Amount"], errors="coerce").fillna(0)
        today = date.today()
        
        valid = df_dash.dropna(subset=["Expiry_Date_dt"])
        days = valid["Expiry_Date_dt"].apply(lambda x: (x - today).days)
        
        due_15 = valid[(days <= 15) & (days >= 0)]
        expired = valid[days < 0]
        active = valid[days > 15]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 કુલ ગ્રાહકો", len(df))
        c2.metric("⚠️ ૧૫ દિવસમાં એક્સપાયર", len(due_15))
        c3.metric("✅ એક્ટિવ પોલિસી", len(active))
        c4.metric("💰 કુલ પ્રીમિયમ રકમ", f"₹{df_dash['Premium_Clean'].sum():,.0f}")
    else:
        st.info("ડેશબોર્ડ પર ડેટા જોવા માટે નવી પોલિસી ઉમેરો.")

# ----------------- 2. રીમાઇન્ડર ડેસ્ક -----------------
elif menu_choice == "🔔 રીમાઇન્ડર ડેસ્ક":
    st.title("🔔 પોલિસી રિન્યુઅલ રીમાઇન્ડર સેન્ટર")
    
    filter_col, template_col = st.columns(2)
    with filter_col:
        filter_mode = st.selectbox("સમયગાળો પસંદ કરો:", ["આગામી ૧૫ દિવસ", "આગામી ૭ દિવસ", "આગામી ૩ દિવસ", "આજે એક્સપાયર થતી"])
    with template_col:
        msg_style = st.selectbox("WhatsApp મેસેજ પ્રકાર:", ["સ્ટાન્ડર્ડ વિગતવાર મેસેજ", "અર્જન્ટ / લાસ્ટ રીમાઇન્ડર", "ટૂંકો મેસેજ"])

    days_limit = 15
    if "૭" in filter_mode: days_limit = 7
    elif "૩" in filter_mode: days_limit = 3
    elif "આજે" in filter_mode: days_limit = 0

    if not df.empty:
        df_rem = df.copy()
        df_rem["Expiry_Date_dt"] = pd.to_datetime(df_rem["Expiry_Date"], errors="coerce").dt.date
        today = date.today()
        df_rem = df_rem.dropna(subset=["Expiry_Date_dt"])
        df_rem["Days_Left"] = df_rem["Expiry_Date_dt"].apply(lambda x: (x - today).days)
        
        reminders = df_rem[(df_rem["Days_Left"] <= days_limit) & (df_rem["Days_Left"] >= 0)].sort_values(by="Days_Left")
        
        if not reminders.empty:
            for idx, row in reminders.iterrows():
                badge = f"<span class='badge-urgent'>🚨 {row['Days_Left']} દિવસ બાકી</span>" if row['Days_Left'] <= 3 else f"<span class='badge-warning'>⏳ {row['Days_Left']} દિવસ બાકી</span>"
                
                if msg_style == "અર્જન્ટ / લાસ્ટ રીમાઇન્ડર":
                    msg = (
                        f"🚨 *અર્જન્ટ રિન્યુઅલ એલર્ટ* 🚨\n\n"
                        f"નમસ્તે {row['Name']}જી,\n"
                        f"આપના વાહન *{row['Vehicle_No']}* ના ઇન્સ્યોરન્સની મુદત *{row['Expiry_Date']}* ના રોજ પૂર્ણ થાય છે ({row['Days_Left']} દિવસ બાકી).\n"
                        f"પોલિસી લેપ્સ થયા વગર તાત્કાલિક રિન્યુ કરાવવા વિનંતી.\n\n"
                        f"📞 *હરિ ઓમ ઇન્સ્યોરન્સ, કડી:* 7698564672 / 9714776364"
                    )
                elif msg_style == "ટૂંકો મેસેજ":
                    msg = f"નમસ્તે {row['Name']}જી, વાહન *{row['Vehicle_No']}* ની પોલિસી તારીખ {row['Expiry_Date']} એ પૂર્ણ થાય છે. રિન્યુઅલ માટે સંપર્ક કરો: હરિ ઓમ ઇન્સ્યોરન્સ (Mo: 7698564672)."
                else:
                    msg = (
                        f"નમસ્તે {row['Name']}જી,\n\n"
                        f"હરિ ઓમ ઇન્સ્યોરન્સ તરફથી યાદી કે આપના વાહન નંબર *{row['Vehicle_No']}* ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['Expiry_Date']}* ના રોજ પૂર્ણ થઈ રહી છે ({row['Days_Left']} દિવસ બાકી).\n\n"
                        f"📄 *પોલિસી નંબર:* {row['Policy_No']}\n"
                        f"🏢 *કંપની:* {row['Policy_Company']}\n\n"
                        f"સમયસર રિન્યુ કરાવવા વિનંતી.\n"
                        f"📞 7698564672 / 9714776364\n"
                        f"*હરિ ઓમ ઇન્સ્યોરન્સ & લોન એડવાઈઝર, કડી*"
                    )

                encoded_msg = urllib.parse.quote(msg)
                clean_mobile = "".join(filter(str.isdigit, str(row['Mobile'])))[-10:]
                wa_url = f"https://wa.me/91{clean_mobile}?text={encoded_msg}"

                st.markdown(f"""
                <div class="reminder-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; color:#0f172a;">{row['Name']} ({row['Vehicle_No']})</h4>
                        {badge}
                    </div>
                    <p style="margin:6px 0 0 0; font-size:13px; color:#475569;">
                        <b>પ્રકાર:</b> {row['Vehicle_Type']} | <b>કંપની:</b> {row['Policy_Company']} | <b>પોલિસી નં:</b> {row['Policy_No']} | <b>એક્સપાયરી:</b> {row['Expiry_Date']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2 = st.columns([1, 4])
                with b1:
                    st.link_button("📲 WhatsApp મોકલો", wa_url)
                with b2:
                    if st.button(f"⚡ ૧-ક્લિક રિન્યુ (૧ વર્ષ ઉમેરો)", key=f"ren_{idx}"):
                        curr_exp = pd.to_datetime(row['Expiry_Date']).date()
                        new_exp = curr_exp + timedelta(days=365)
                        df.at[idx, "Expiry_Date"] = str(new_exp)
                        df.at[idx, "Last_Renewed"] = str(date.today())
                        save_data(df)
                        st.success(f"પોલિસી તારીખ {new_exp} સુધી રિન્યુ થઈ ગઈ!")
                        st.rerun()
                st.divider()
        else:
            st.success("આ સમયગાળામાં કોઈ પોલિસી એક્સપાયર થતી નથી.")
    else:
        st.info("કોઈ ડેટા ઉપલબ્ધ નથી.")

# ----------------- 3. નવી એન્ટ્રી -----------------
elif menu_choice == "➕ નવી પોલિસી એન્ટ્રી":
    st.title("➕ નવો ગ્રાહક અને પોલિસી ઉમેરો")
    with st.form("new_entry_form", clear_on_submit=True):
        c_a, c_b = st.columns(2)
        name = c_a.text_input("ગ્રાહકનું પૂરું નામ *")
        mobile = c_b.text_input("મોબાઇલ નંબર *")
        vehicle_no = c_a.text_input("વાહન નંબર (GJ-xx-xxxx) *")
        vehicle_type = c_b.selectbox("વાહનનો પ્રકાર", ["2 Wheeler", "4 Wheeler (Car)", "Commercial Goods", "Passenger Taxi", "Tractor", "અન્ય"])
        company = c_a.selectbox("ઇન્સ્યોરન્સ કંપની", ["ICICI Lombard", "Bajaj Allianz", "Tata AIG", "New India", "HDFC ERGO", "Go Digit", "National", "Star Health", "અન્ય"])
        policy_no = c_b.text_input("પોલિસી નંબર")
        premium = c_a.number_input("પ્રીમિયમ રકમ (₹)", min_value=0, step=500)
        expiry = c_b.date_input("પોલિસી એક્સપાયરી તારીખ *")
        remarks = st.text_input("નોંધ / રિમાર્ક્સ")
        
        if st.form_submit_button("💾 પોલિસી સેવ કરો"):
            if name.strip() and mobile.strip() and vehicle_no.strip():
                new_row = {
                    "Name": name.strip(),
                    "Mobile": mobile.strip(),
                    "Vehicle_No": vehicle_no.upper().strip(),
                    "Vehicle_Type": vehicle_type,
                    "Policy_Company": company,
                    "Policy_No": policy_no.strip(),
                    "Premium_Amount": premium,
                    "Expiry_Date": str(expiry),
                    "Remarks": remarks.strip(),
                    "Last_Renewed": str(date.today())
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("✅ ગ્રાહક સફળતાપૂર્વક ઉમેરાઈ ગયો અને ડેટા ઓટો-સેવ થઈ ગયો!")
                st.rerun()
            else:
                st.error("કૃપા કરીને નામ, મોબાઇલ અને વાહન નંબર ભરો.")

# ----------------- 4. તમામ ગ્રાહકોની યાદી -----------------
elif menu_choice == "📁 તમામ ગ્રાહકોની યાદી":
    st.title("📁 ગ્રાહક ડિરેક્ટરી")
    if not df.empty:
        sq = st.text_input("🔍 સર્ચ કરો (નામ, વાહન નંબર કે મોબાઇલ):")
        vdf = df.copy()
        if sq:
            q = sq.lower()
            vdf = vdf[
                vdf["Name"].astype(str).str.lower().str.contains(q) |
                vdf["Vehicle_No"].astype(str).str.lower().str.contains(q) |
                vdf["Mobile"].astype(str).contains(q)
            ]
        st.dataframe(vdf, use_container_width=True)
        csv_exp = vdf.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Excel / CSV માં ડાઉનલોડ કરો", data=csv_exp, file_name="HariOm_Clients.csv", mime="text/csv")
    else:
        st.info("કોઈ ગ્રાહકનો ડેટા નથી.")

# ----------------- 5. એડિટ / ડિલીટ -----------------
elif menu_choice == "⚙️ એડિટ / ડિલીટ":
    st.title("⚙️ ગ્રાહક ડેટા સુધારો અથવા રદ કરો")
    if not df.empty:
        opts = [f"{i}: {r['Name']} - {r['Vehicle_No']}" for i, r in df.iterrows()]
        sel = st.selectbox("ગ્રાહક પસંદ કરો:", opts)
        if sel:
            s_idx = int(sel.split(":")[0])
            s_row = df.loc[s_idx]
            
            with st.form("edit_form"):
                e1, e2 = st.columns(2)
                en = e1.text_input("નામ", value=str(s_row['Name']))
                em = e2.text_input("મોબાઇલ", value=str(s_row['Mobile']))
                ev = e1.text_input("વાહન નંબર", value=str(s_row['Vehicle_No']))
                et = e2.text_input("વાહનનો પ્રકાર", value=str(s_row['Vehicle_Type']))
                ec = e1.text_input("કંપની", value=str(s_row['Policy_Company']))
                ep = e2.text_input("પોલિસી નં", value=str(s_row['Policy_No']))
                
                try: prem_val = int(float(s_row['Premium_Amount']))
                except: prem_val = 0
                eprem = e1.number_input("પ્રીમિયમ (₹)", value=prem_val, step=500)
                
                try: exp_val = datetime.strptime(str(s_row['Expiry_Date']), "%Y-%m-%d").date()
                except: exp_val = date.today()
                eexp = e2.date_input("એક્સપાયરી તારીખ", value=exp_val)
                erem = st.text_input("નોંધ", value=str(s_row['Remarks']))
                
                ub1, ub2 = st.columns(2)
                if ub1.form_submit_button("🔄 અપડેટ કરો"):
                    df.at[s_idx, "Name"] = en.strip()
                    df.at[s_idx, "Mobile"] = em.strip()
                    df.at[s_idx, "Vehicle_No"] = ev.upper().strip()
                    df.at[s_idx, "Vehicle_Type"] = et
                    df.at[s_idx, "Policy_Company"] = ec.strip()
                    df.at[s_idx, "Policy_No"] = ep.strip()
                    df.at[s_idx, "Premium_Amount"] = eprem
                    df.at[s_idx, "Expiry_Date"] = str(eexp)
                    df.at[s_idx, "Remarks"] = erem.strip()
                    save_data(df)
                    st.success("વિગતો અપડેટ થઈ ગઈ!")
                    st.rerun()
                if ub2.form_submit_button("🗑️ એન્ટ્રી ડિલીટ કરો"):
                    df = df.drop(s_idx).reset_index(drop=True)
                    save_data(df)
                    st.warning("એન્ટ્રી ડિલીટ થઈ ગઈ!")
                    st.rerun()
    else:
        st.info("ડેટાબેઝ ખાલી છે.")

# ----------------- 6. બેકઅપ અને સેટિંગ્સ -----------------
elif menu_choice == "💾 ડેટા બેકઅપ & સેટિંગ્સ":
    st.title("💾 ડેટા ઓટોમેશન & બેકઅપ")
    st.markdown("""
    💡 **લાઈવ ગૂગલ શીટ કનેક્શન:**  
    જો તમે Google Sheets કનેક્ટ કરશો, તો તમારે ક્યારેય મેન્યુઅલ બેકઅપ લેવું નહીં પડે કે ફાઈલ અપલોડ કરવી નહીં પડે. બધી એન્ટ્રી સીધી Google Sheets માં ક્લાઉડ પર સુરક્ષિત રહેશે.
    """)
    bk1, bk2 = st.columns(2)
    with bk1:
        st.markdown("### 📥 ડાઉનલોડ ઑફલાઇન બેકઅપ")
        if not df.empty:
            bk_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ સંપૂર્ણ ડેટાબેઝ ડાઉનલોડ (CSV)", data=bk_csv, file_name=f"hari_om_backup_{date.today()}.csv", mime="text/csv")
    with bk2:
        st.markdown("### 📤 CSV ફાઇલ રિસ્ટોર કરો")
        up_file = st.file_uploader("CSV બેકઅપ અપલોડ કરો", type=["csv"])
        if up_file and st.button("🚀 ડેટા રિસ્ટોર કરો"):
            try:
                new_df = pd.read_csv(up_file)
                save_data(new_df)
                st.success("ડેટા સફળતાપૂર્વક રિસ્ટોર થઈ ગયો!")
                st.rerun()
            except Exception as err:
                st.error(f"એરર: {err}")
