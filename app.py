import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import urllib.parse

st.set_page_config(page_title="Hari Om Insurance", layout="wide", page_icon="🚗")

DB_FILE = "insurance_data.csv"

# ડેટાબેઝ લોડ કરવાનું ફંક્શન
def load_data():
    columns = [
        "Name", "Mobile", "Vehicle_No", "Vehicle_Type", 
        "Policy_Company", "Policy_No", "Premium_Amount", 
        "Expiry_Date", "Remarks"
    ]
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns]
    return pd.DataFrame(columns=columns)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

# હેડર અને બ્રાન્ડિંગ
header_col1, header_col2 = st.columns([1, 4])

with header_col1:
    if os.path.exists("HARI OM IL.jpg"):
        st.image("HARI OM IL.jpg", use_container_width=True)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.markdown("### 🏢")

with header_col2:
    st.markdown("""
    ## **હરિ ઓમ ઇન્સ્યોરન્સ & લેન્ડ એડવાઈઝર**
    📍 **સરનામું:** F-46, વાત્સલ્ય સ્ટેટસ, ધવલ પ્લાઝા પાસે, કડી - 384440.  
    📞 **સંપર્ક:** 7698564672 / 9714776364
    """)

st.markdown("---")

# મુખ્ય ટેબ્સ
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 ડેશબોર્ડ", 
    "🔔 આગામી રીમાઇન્ડર્સ (૧૫ દિવસ)", 
    "➕ નવી પોલિસી ઉમેરો", 
    "📁 કસ્ટમર ડિટેલ્સ", 
    "⚙️ એડિટ / ડિલીટ"
])

# ----------------- TAB 1: ડેશબોર્ડ -----------------
with tab1:
    st.subheader("📈 બિઝનેસ અને પોલિસી ઓવરવ્યૂ")
    if not df.empty:
        df_temp = df.copy()
        df_temp["Expiry_Date_dt"] = pd.to_datetime(df_temp["Expiry_Date"], errors="coerce").dt.date
        today = date.today()
        
        valid_dates = df_temp.dropna(subset=["Expiry_Date_dt"])
        days_diff = valid_dates["Expiry_Date_dt"].apply(lambda x: (x - today).days)
        
        due_15 = valid_dates[(days_diff <= 15) & (days_diff >= 0)]
        expired = valid_dates[days_diff < 0]
        active = valid_dates[days_diff > 15]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("કુલ ગ્રાહકો / પોલિસી", len(df))
        m2.metric("૧૫ દિવસમાં એક્સપાયર", len(due_15))
        m3.metric("એક્ટિવ પોલિસી", len(active))
        m4.metric("એક્સપાયર થઈ ગયેલી", len(expired))
    else:
        st.info("હાલમાં કોઈ ડેટા ઉપલબ્ધ નથી.")

# ----------------- TAB 2: રીમાઇન્ડર્સ -----------------
with tab2:
    st.subheader("🔔 આગામી ૧૫ દિવસમાં રિન્યુ કરવાની પોલિસીઓ")
    if not df.empty:
        df_rem = df.copy()
        df_rem["Expiry_Date_dt"] = pd.to_datetime(df_rem["Expiry_Date"], errors="coerce").dt.date
        today = date.today()
        df_rem = df_rem.dropna(subset=["Expiry_Date_dt"])
        df_rem["Days_Left"] = df_rem["Expiry_Date_dt"].apply(lambda x: (x - today).days)
        
        reminders = df_rem[(df_rem["Days_Left"] <= 15) & (df_rem["Days_Left"] >= 0)].sort_values(by="Days_Left")
        
        if not reminders.empty:
            st.warning(f"કુલ {len(reminders)} ગ્રાહકોની પોલિસી રિન્યુઅલ માટે બાકી છે.")
            for _, row in reminders.iterrows():
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    
                    msg_text = (
                        f"નમસ્તે {row['Name']}જી,\n\n"
                        f"હરિ ઓમ ઇન્સ્યોરન્સ તરફથી યાદી કે આપના વાહન નંબર *{row['Vehicle_No']}* ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['Expiry_Date']}* ના રોજ પૂર્ણ થઈ રહી છે ({row['Days_Left']} દિવસ બાકી).\n\n"
                        f"📄 *પોલિસી નંબર:* {row['Policy_No']}\n"
                        f"🏢 *કંપની:* {row['Policy_Company']}\n\n"
                        f"પોલિસી લેપ્સ ન થાય અને અવિરત કવરેજ જળવાઈ રહે તે માટે સમયસર રિન્યુ કરાવવા વિનંતી.\n\n"
                        f"સંપર્ક: 7698564672 / 9714776364\n"
                        f"*હરિ ઓમ ઇન્સ્યોરન્સ & લેન્ડ એડવાઈઝર, કડી*"
                    )
                    
                    encoded_msg = urllib.parse.quote(msg_text)
                    clean_mobile = "".join(filter(str.isdigit, str(row['Mobile'])))[-10:]
                    wa_url = f"[https://wa.me/91](https://wa.me/91){clean_mobile}?text={encoded_msg}"
                    
                    with c1:
                        st.markdown(f"👤 **{row['Name']}** | 🚗 વાહન: `{row['Vehicle_No']}` ({row['Vehicle_Type']})")
                        st.markdown(f"📋 પોલિસી નં: `{row['Policy_No']}` | કંપની: **{row['Policy_Company']}** | બાકી દિવસ: **{row['Days_Left']}** (તારીખ: {row['Expiry_Date']})")
                    
                    with c2:
                        st.link_button("📲 WhatsApp મોકલો", wa_url)
                    st.divider()
        else:
            st.success("આગામી ૧૫ દિવસમાં કોઈ પોલિસી એક્સપાયર થતી નથી.")
    else:
        st.info("કોઈ ડેટા ઉપલબ્ધ નથી.")

# ----------------- TAB 3: નવી પોલિસી ઉમેરો -----------------
with tab3:
    st.subheader("➕ નવા ગ્રાહકની વિગત ઉમેરો")
    with st.form("add_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        
        name = f_col1.text_input("ગ્રાહકનું પૂરું નામ *")
        mobile = f_col2.text_input("મોબાઇલ નંબર *")
        vehicle_no = f_col1.text_input("વાહન નંબર (દા.ત. GJ-02-AB-1234) *")
        vehicle_type = f_col2.selectbox("વાહનનો પ્રકાર", ["2 Wheeler (બાઇક/સ્કૂટર)", "4 Wheeler (કાર)", "Commercial Vehicle", "Tractor", "અન્ય"])
        company = f_col1.text_input("ઇન્સ્યોરન્સ કંપનીનું નામ")
        policy_no = f_col2.text_input("પોલિસી નંબર")
        premium = f_col1.number_input("પ્રીમિયમ રકમ (₹)", min_value=0, step=100)
        expiry = f_col2.date_input("પોલિસી એક્સપાયરી તારીખ *")
        remarks = st.text_input("નોંધ / રિમાર્ક્સ (ઓપ્શનલ)")
        
        submitted = st.form_submit_button("💾 ડેટા સેવ કરો")
        if submitted:
            if name.strip() and mobile.strip() and vehicle_no.strip():
                new_data = {
                    "Name": name.strip(),
                    "Mobile": mobile.strip(),
                    "Vehicle_No": vehicle_no.upper().strip(),
                    "Vehicle_Type": vehicle_type,
                    "Policy_Company": company.strip(),
                    "Policy_No": policy_no.strip(),
                    "Premium_Amount": premium,
                    "Expiry_Date": str(expiry),
                    "Remarks": remarks.strip()
                }
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                save_data(df)
                st.success("✅ નવો ગ્રાહક સફળતાપૂર્વક ઉમેરાઈ ગયો!")
                st.rerun()
            else:
                st.error("કૃપા કરીને નામ, મોબાઈલ અને વાહન નંબર જરૂર ભરો.")

# ----------------- TAB 4: કસ્ટમર ડિટેલ્સ -----------------
with tab4:
    st.subheader("📁 તમામ ગ્રાહકોની ડિટેલ્સ")
    if not df.empty:
        search_query = st.text_input("🔍 નામ, વાહન નંબર કે મોબાઈલ નંબરથી સર્ચ કરો:")
        view_df = df.copy()
        if search_query:
            q = search_query.lower()
            view_df = view_df[
                view_df["Name"].astype(str).str.lower().str.contains(q) |
                view_df["Vehicle_No"].astype(str).str.lower().str.contains(q) |
                view_df["Mobile"].astype(str).str.contains(q)
            ]
        st.dataframe(view_df, use_container_width=True)
        
        csv_data = view_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 ડેટા Excel/CSV ડાઉનલોડ કરો", data=csv_data, file_name="insurance_customers.csv", mime="text/csv")
    else:
        st.info("કોઈ ગ્રાહકનો ડેટા મળ્યો નથી.")

# ----------------- TAB 5: એડિટ / ડિલીટ -----------------
with tab5:
    st.subheader("⚙️ એન્ટ્રી સુધારો (Edit) અથવા રદ કરો (Delete)")
    if not df.empty:
        options = [f"{i}: {row['Name']} ({row['Vehicle_No']})" for i, row in df.iterrows()]
        selected_option = st.selectbox("ગ્રાહક પસંદ કરો:", options)
        
        if selected_option:
            selected_idx = int(selected_option.split(":")[0])
            selected_row = df.loc[selected_idx]
            
            with st.form("edit_form"):
                e_col1, e_col2 = st.columns(2)
                e_name = e_col1.text_input("ગ્રાહકનું નામ", value=str(selected_row['Name']))
                e_mobile = e_col2.text_input("મોબાઇલ નંબર", value=str(selected_row['Mobile']))
                e_vehicle = e_col1.text_input("વાહન નંબર", value=str(selected_row['Vehicle_No']))
                
                v_types = ["2 Wheeler (બાઇક/સ્કૂટર)", "4 Wheeler (કાર)", "Commercial Vehicle", "Tractor", "અન્ય"]
                curr_type_idx = v_types.index(selected_row['Vehicle_Type']) if selected_row['Vehicle_Type'] in v_types else 0
                e_type = e_col2.selectbox("વાહનનો પ્રકાર", v_types, index=curr_type_idx)
                
                e_company = e_col1.text_input("ઇન્સ્યોરન્સ કંપની", value=str(selected_row['Policy_Company']))
                e_policy_no = e_col2.text_input("પોલિસી નંબર", value=str(selected_row['Policy_No']))
                
                try:
                    curr_prem = int(float(selected_row['Premium_Amount']))
                except:
                    curr_prem = 0
                e_premium = e_col1.number_input("પ્રીમિયમ રકમ (₹)", min_value=0, step=100, value=curr_prem)
                
                try:
                    curr_exp = datetime.strptime(str(selected_row['Expiry_Date']), "%Y-%m-%d").date()
                except:
                    curr_exp = date.today()
                e_expiry = e_col2.date_input("એક્સપાયરી તારીખ", value=curr_exp)
                
                e_remarks = st.text_input("નોંધ / રિમાર્ક્સ", value=str(selected_row['Remarks']))
                
                btn_col1, btn_col2 = st.columns(2)
                update_btn = btn_col1.form_submit_button("🔄 ફેરફાર સેવ કરો (Update)")
                delete_btn = btn_col2.form_submit_button("🗑️ ડિલીટ કરો (Delete)")
                
                if update_btn:
                    df.at[selected_idx, "Name"] = e_name.strip()
                    df.at[selected_idx, "Mobile"] = e_mobile.strip()
                    df.at[selected_idx, "Vehicle_No"] = e_vehicle.upper().strip()
                    df.at[selected_idx, "Vehicle_Type"] = e_type
                    df.at[selected_idx, "Policy_Company"] = e_company.strip()
                    df.at[selected_idx, "Policy_No"] = e_policy_no.strip()
                    df.at[selected_idx, "Premium_Amount"] = e_premium
                    df.at[selected_idx, "Expiry_Date"] = str(e_expiry)
                    df.at[selected_idx, "Remarks"] = e_remarks.strip()
                    save_data(df)
                    st.success("✅ વિગતો અપડેટ થઈ ગઈ!")
                    st.rerun()
                
                if delete_btn:
                    df = df.drop(selected_idx).reset_index(drop=True)
                    save_data(df)
                    st.warning("🗑️ ગ્રાહકની એન્ટ્રી ડિલીટ થઈ ગઈ!")
                    st.rerun()
    else:
        st.info("ડેટાબેઝ ખાલી છે.")
