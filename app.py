import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sqlite3
import urllib.parse
import os

# પેજ કન્ફિગરેશન
st.set_page_config(
    page_title="Hari Om Insurance Portal",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS સ્ટાઇલિંગ
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

# ----------------- SQLite ડેટાબેઝ સેટઅપ -----------------
DB_FILE = "insurance_master.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            mobile TEXT,
            vehicle_no TEXT,
            vehicle_type TEXT,
            policy_company TEXT,
            policy_no TEXT,
            premium_amount REAL,
            expiry_date TEXT,
            remarks TEXT,
            last_renewed TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_data():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM policies", conn)
    conn.close()
    return df

def insert_policy(name, mobile, vehicle_no, v_type, company, policy_no, premium, expiry, remarks):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO policies (name, mobile, vehicle_no, vehicle_type, policy_company, policy_no, premium_amount, expiry_date, remarks, last_renewed)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, mobile, vehicle_no, v_type, company, policy_no, premium, expiry, remarks, str(date.today())))
    conn.commit()
    conn.close()

def update_policy(p_id, name, mobile, vehicle_no, v_type, company, policy_no, premium, expiry, remarks):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        UPDATE policies 
        SET name=?, mobile=?, vehicle_no=?, vehicle_type=?, policy_company=?, policy_no=?, premium_amount=?, expiry_date=?, remarks=?
        WHERE id=?
    ''', (name, mobile, vehicle_no, v_type, company, policy_no, premium, expiry, remarks, p_id))
    conn.commit()
    conn.close()

def delete_policy(p_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('DELETE FROM policies WHERE id=?', (p_id,))
    conn.commit()
    conn.close()

def renew_one_year(p_id, current_expiry_str):
    try:
        curr_dt = datetime.strptime(str(current_expiry_str), "%Y-%m-%d").date()
    except Exception:
        curr_dt = date.today()
    new_dt = str(curr_dt + timedelta(days=365))
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE policies SET expiry_date=?, last_renewed=? WHERE id=?', (new_dt, str(date.today()), p_id))
    conn.commit()
    conn.close()

df = get_data()

# ----------------- સાઇડબાર નેવિગેશન -----------------
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
            "💾 ડેટા બેકઅપ & રિસ્ટોર"
        ],
        index=0
    )
    
    st.markdown("---")
    st.markdown("""
    **સંપર્ક:**  
    📍 F-46, વાત્સલ્ય સ્ટેટસ, ધવલ પ્લાઝા પાસે, કડી - 384440  
    📞 7698564672  
    📞 9714776364  
    """)

# ----------------- 1. ડેશબોર્ડ -----------------
if menu_choice == "📊 ડેશબોર્ડ":
    st.title("📊 બિઝનેસ ડેશબોર્ડ")
    if not df.empty:
        df_dash = df.copy()
        df_dash["expiry_dt"] = pd.to_datetime(df_dash["expiry_date"], errors="coerce").dt.date
        df_dash["premium_clean"] = pd.to_numeric(df_dash["premium_amount"], errors="coerce").fillna(0)
        today = date.today()
        
        valid = df_dash.dropna(subset=["expiry_dt"])
        days = valid["expiry_dt"].apply(lambda x: (x - today).days)
        
        due_15 = valid[(days <= 15) & (days >= 0)]
        expired = valid[days < 0]
        active = valid[days > 15]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 કુલ ગ્રાહકો", len(df))
        c2.metric("⚠️ ૧૫ દિવસમાં એક્સપાયર", len(due_15))
        c3.metric("✅ એક્ટિવ પોલિસી", len(active))
        c4.metric("💰 કુલ પ્રીમિયમ રકમ", f"₹{df_dash['premium_clean'].sum():,.0f}")
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
        df_rem["expiry_dt"] = pd.to_datetime(df_rem["expiry_date"], errors="coerce").dt.date
        today = date.today()
        df_rem = df_rem.dropna(subset=["expiry_dt"])
        df_rem["days_left"] = df_rem["expiry_dt"].apply(lambda x: (x - today).days)
        
        reminders = df_rem[(df_rem["days_left"] <= days_limit) & (df_rem["days_left"] >= 0)].sort_values(by="days_left")
        
        if not reminders.empty:
            for _, row in reminders.iterrows():
                badge = f"<span class='badge-urgent'>🚨 {row['days_left']} દિવસ બાકી</span>" if row['days_left'] <= 3 else f"<span class='badge-warning'>⏳ {row['days_left']} દિવસ બાકી</span>"
                
                if msg_style == "અર્જન્ટ / લાસ્ટ રીમાઇન્ડર":
                    msg = (
                        f"🚨 *અર્જન્ટ રિન્યુઅલ એલર્ટ* 🚨\n\n"
                        f"નમસ્તે {row['name']}જી,\n"
                        f"આપના વાહન *{row['vehicle_no']}* ના ઇન્સ્યોરન્સની મુદત *{row['expiry_date']}* ના રોજ પૂર્ણ થાય છે ({row['days_left']} દિવસ બાકી).\n"
                        f"પોલિસી લેપ્સ થયા વગર તાત્કાલિક રિન્યુ કરાવવા વિનંતી.\n\n"
                        f"📞 *હરિ ઓમ ઇન્સ્યોરન્સ, કડી:* 7698564672 / 9714776364"
                    )
                elif msg_style == "ટૂંકો મેસેજ":
                    msg = f"નમસ્તે {row['name']}જી, વાહન *{row['vehicle_no']}* ની પોલિસી તારીખ {row['expiry_date']} એ પૂર્ણ થાય છે. રિન્યુઅલ માટે સંપર્ક કરો: હરિ ઓમ ઇન્સ્યોરન્સ (Mo: 7698564672)."
                else:
                    msg = (
                        f"નમસ્તે {row['name']}જી,\n\n"
                        f"હરિ ઓમ ઇન્સ્યોરન્સ તરફથી યાદી કે આપના વાહન નંબર *{row['vehicle_no']}* ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['expiry_date']}* ના રોજ પૂર્ણ થઈ રહી છે ({row['days_left']} દિવસ બાકી).\n\n"
                        f"📄 *પોલિસી નંબર:* {row['policy_no']}\n"
                        f"🏢 *કંપની:* {row['policy_company']}\n\n"
                        f"સમયસર રિન્યુ કરાવવા વિનંતી.\n"
                        f"📞 7698564672 / 9714776364\n"
                        f"*હરિ ઓમ ઇન્સ્યોરન્સ & લોન એડવાઈઝર, કડી*"
                    )

                encoded_msg = urllib.parse.quote(msg)
                clean_mobile = "".join(filter(str.isdigit, str(row['mobile'])))[-10:]
                wa_url = f"https://wa.me/91{clean_mobile}?text={encoded_msg}"

                st.markdown(f"""
                <div class="reminder-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; color:#0f172a;">{row['name']} ({row['vehicle_no']})</h4>
                        {badge}
                    </div>
                    <p style="margin:6px 0 0 0; font-size:13px; color:#475569;">
                        <b>પ્રકાર:</b> {row['vehicle_type']} | <b>કંપની:</b> {row['policy_company']} | <b>પોલિસી નં:</b> {row['policy_no']} | <b>એક્સપાયરી:</b> {row['expiry_date']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                b1, b2 = st.columns([1, 4])
                with b1:
                    st.link_button("📲 WhatsApp મોકલો", wa_url)
                with b2:
                    if st.button(f"⚡ ૧-ક્લિક રિન્યુ (૧ વર્ષ ઉમેરો)", key=f"ren_{row['id']}"):
                        renew_one_year(row['id'], row['expiry_date'])
                        st.success("પોલિસી ૧ વર્ષ માટે રિન્યુ થઈ ગઈ!")
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
                insert_policy(
                    name.strip(),
                    mobile.strip(),
                    vehicle_no.upper().strip(),
                    vehicle_type,
                    company,
                    policy_no.strip(),
                    premium,
                    str(expiry),
                    remarks.strip()
                )
                st.success("✅ ગ્રાહક સફળતાપૂર્વક ઉમેરાઈ ગયો અને ડેટાબેઝમાં સેવ થઈ ગયો!")
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
                vdf["name"].astype(str).str.lower().str.contains(q) |
                vdf["vehicle_no"].astype(str).str.lower().str.contains(q) |
                vdf["mobile"].astype(str).contains(q)
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
        opts = {f"{r['id']}: {r['name']} - {r['vehicle_no']}": r['id'] for _, r in df.iterrows()}
        sel_label = st.selectbox("ગ્રાહક પસંદ કરો:", list(opts.keys()))
        
        if sel_label:
            p_id = opts[sel_label]
            s_row = df[df['id'] == p_id].iloc[0]
            
            with st.form("edit_form"):
                e1, e2 = st.columns(2)
                en = e1.text_input("નામ", value=str(s_row['name']))
                em = e2.text_input("મોબાઇલ", value=str(s_row['mobile']))
                ev = e1.text_input("વાહન નંબર", value=str(s_row['vehicle_no']))
                et = e2.text_input("વાહનનો પ્રકાર", value=str(s_row['vehicle_type']))
                ec = e1.text_input("કંપની", value=str(s_row['policy_company']))
                ep = e2.text_input("પોલિસી નં", value=str(s_row['policy_no']))
                
                try: 
                    prem_val = int(float(s_row['premium_amount']))
                except Exception: 
                    prem_val = 0
                eprem = e1.number_input("પ્રીમિયમ (₹)", value=prem_val, step=500)
                
                try: 
                    exp_val = datetime.strptime(str(s_row['expiry_date']), "%Y-%m-%d").date()
                except Exception: 
                    exp_val = date.today()
                eexp = e2.date_input("એક્સપાયરી તારીખ", value=exp_val)
                erem = st.text_input("નોંધ", value=str(s_row['remarks']))
                
                ub1, ub2 = st.columns(2)
                if ub1.form_submit_button("🔄 અપડેટ કરો"):
                    update_policy(p_id, en.strip(), em.strip(), ev.upper().strip(), et, ec.strip(), ep.strip(), eprem, str(eexp), erem.strip())
                    st.success("વિગતો અપડેટ થઈ ગઈ!")
                    st.rerun()
                if ub2.form_submit_button("🗑️ એન્ટ્રી ડિલીટ કરો"):
                    delete_policy(p_id)
                    st.warning("એન્ટ્રી ડિલીટ થઈ ગઈ!")
                    st.rerun()
    else:
        st.info("ડેટાબેઝ ખાલી છે.")

# ----------------- 6. બેકઅપ અને રિસ્ટોર -----------------
elif menu_choice == "💾 ડેટા બેકઅપ & રિસ્ટોર":
    st.title("💾 ડેટા બેકઅપ અને રિસ્ટોર સેન્ટર")
    bk1, bk2 = st.columns(2)
    with bk1:
        st.markdown("### 📥 ડાઉનલોડ બેકઅપ")
        st.write("હાલના તમામ ગ્રાહકોની CSV બેકઅપ ફાઈલ ડાઉનલોડ કરો.")
        if not df.empty:
            bk_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ સંપૂર્ણ ડેટાબેઝ ડાઉનલોડ (CSV)", data=bk_csv, file_name=f"hari_om_backup_{date.today()}.csv", mime="text/csv")
        else:
            st.info("બેકઅપ લેવા માટે ડેટાબેઝમાં કોઈ એન્ટ્રી નથી.")
    with bk2:
        st.markdown("### 📤 રિસ્ટોર ડેટા")
        st.write("અગાઉ લીધેલ બેકઅપ CSV ફાઇલ અપલોડ કરીને ડેટા પાછો લાવો.")
        up_file = st.file_uploader("CSV ફાઇલ અપલોડ કરો", type=["csv"])
        if up_file and st.button("🚀 ડેટા રિસ્ટોર કરો"):
            try:
                new_df = pd.read_csv(up_file)
                for _, r in new_df.iterrows():
                    insert_policy(
                        str(r.get('name', '')),
                        str(r.get('mobile', '')),
                        str(r.get('vehicle_no', '')),
                        str(r.get('vehicle_type', '')),
                        str(r.get('policy_company', '')),
                        str(r.get('policy_no', '')),
                        float(r.get('premium_amount', 0)),
                        str(r.get('expiry_date', '')),
                        str(r.get('remarks', ''))
                    )
                st.success("ડેટા સફળતાપૂર્વક રિસ્ટોર થઈ ગયો!")
                st.rerun()
            except Exception as err:
                st.error(f"એરર આવી: {err}")
