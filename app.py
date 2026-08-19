import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import urllib.parse
import base64

# પેજ સેટઅપ
st.set_page_config(
    page_title="Hari Om Insurance & Loan Advisor",
    page_icon="☂️",
    layout="wide"
)

DB_FILE = "insurance_data.csv"
LOGO_FILE = "HARI OM IL.jpg"

# ડેટાબેઝ લોડ કરવાનું ફંક્શન (વધારાના ફીલ્ડ્સ સાથે)
def load_data():
    columns = ["ID", "Name", "Mobile", "Vehicle_No", "Vehicle_Type", "Company", "Policy_No", "Expiry_Date", "Premium", "Notes"]
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)
        # જૂના ડેટા સાથે સુસંગતતા જાળવવા નવા કોલમ્સ ઉમેરો
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        if "ID" not in df.columns or df["ID"].isnull().all():
            df["ID"] = [str(i+1) for i in range(len(df))]
        return df[columns]
    return pd.DataFrame(columns=columns)

# ડેટાબેઝ સેવ કરવાનું ફંક્શન
def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

# ----------------- હેડર અને લોગો બ્રાન્ડિંગ -----------------
col_logo, col_header = st.columns([1, 3])

with col_logo:
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; font-size: 70px; margin:0;'>☂️</h1>", unsafe_allow_html=True)

with col_header:
    st.markdown("""
        <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 18px 25px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
            <h1 style="margin: 0; color: #FBBF24; font-size: 32px; font-weight: bold;">HARI OM INSURANCE & LOAN ADVISOR</h1>
            <p style="font-size: 15px; margin: 6px 0; color: #E0E7FF;">📍 F-46, VATSALY STATUS, NR.DHAVAL PLAZA, KADI-384440.</p>
            <p style="font-size: 18px; font-weight: bold; margin: 0; color: #6EE7B7;">📞 MO: 7698564672 / 9714776364</p>
        </div>
    """, unsafe_allow_html=True)

st.write("")

# ----------------- ટેબ્સ -----------------
tab_dash, tab_reminders, tab_details, tab_manage = st.tabs([
    "📊 ડેશબોર્ડ (Dashboard)", 
    "🔔 ૧૫ દિવસના રીમાઇન્ડર્સ", 
    "📁 કસ્ટમર ડિટેલ્સ (Customer Directory)",
    "⚙️ એન્ટ્રી ઉમેરો / એડિટ / ડિલીટ"
])

# ----------------- ૧. ડેશબોર્ડ ટેબ -----------------
with tab_dash:
    st.subheader("📌 બિઝનેસ ડેશબોર્ડ")
    
    if not df.empty:
        temp_df = df.copy()
        temp_df["Expiry_Date_dt"] = pd.to_datetime(temp_df["Expiry_Date"], errors='coerce').dt.date
        today = date.today()
        temp_df["Days_Left"] = temp_df["Expiry_Date_dt"].apply(lambda x: (x - today).days if pd.notnull(x) else 999)
        
        total_policies = len(temp_df)
        expiring_15 = len(temp_df[(temp_df["Days_Left"] <= 15) & (temp_df["Days_Left"] >= 0)])
        expired = len(temp_df[temp_df["Days_Left"] < 0])
        active = len(temp_df[temp_df["Days_Left"] > 15])
        
        # સ્ટેટિસ્ટિક્સ કાર્ડ્સ
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("કુલ પોલિસીઓ", total_policies)
        col2.metric("૧૫ દિવસમાં એક્સપાયર થતી", expiring_15, delta_color="inverse")
        col3.metric("એક્સપાયર્ડ થઈ ગયેલી", expired, delta_color="inverse")
        col4.metric("એક્ટિવ પોલિસીઓ (>15 દિવસ)", active)
        
        st.divider()
        
        # શોધો અને ફિલ્ટર કરો
        search_term = st.text_input("🔍 ગ્રાહકના નામ, વાહન નંબર, પોલિસી નંબર અથવા કંપનીથી શોધો:")
        
        display_cols = ["Name", "Mobile", "Vehicle_No", "Vehicle_Type", "Company", "Policy_No", "Expiry_Date", "Days_Left", "Premium"]
        
        if search_term:
            filtered_df = temp_df[
                temp_df["Name"].str.contains(search_term, case=False, na=False) |
                temp_df["Vehicle_No"].str.contains(search_term, case=False, na=False) |
                temp_df["Policy_No"].str.contains(search_term, case=False, na=False) |
                temp_df["Company"].str.contains(search_term, case=False, na=False) |
                temp_df["Mobile"].str.contains(search_term, case=False, na=False)
            ]
            st.dataframe(filtered_df[display_cols], use_container_width=True)
        else:
            st.write("### 📋 તાજેતરની પોલિસી વિગતો")
            st.dataframe(temp_df[display_cols], use_container_width=True)
    else:
        st.info("ડેશબોર્ડ જોવા માટે પ્રથમ પોલિસી એન્ટ્રી ઉમેરો.")

# ----------------- ૨. ૧૫ દિવસના રીમાઇન્ડર્સ ટેબ -----------------
with tab_reminders:
    st.subheader("📲 WhatsApp રીમાઇન્ડર લિસ્ટ (૧૫ દિવસ બાકી)")
    
    if not df.empty:
        temp_df = df.copy()
        temp_df["Expiry_Date_dt"] = pd.to_datetime(temp_df["Expiry_Date"], errors='coerce').dt.date
        today = date.today()
        temp_df["Days_Left"] = temp_df["Expiry_Date_dt"].apply(lambda x: (x - today).days if pd.notnull(x) else 999)
        
        reminders = temp_df[(temp_df["Days_Left"] <= 15) & (temp_df["Days_Left"] >= 0)].sort_values(by="Days_Left")
        
        if not reminders.empty:
            st.warning(f"⚠️ કુલ {len(reminders)} પોલિસી રિન્યુઅલ માટે બાકી છે.")
            
            for _, row in reminders.iterrows():
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    
                    comp_text = f"કંપની: {row['Company']}\n" if row.get('Company') else ""
                    type_text = f"વાહન પ્રકાર: {row['Vehicle_Type']}\n" if row.get('Vehicle_Type') else ""
                    prem_text = f"પ્રીમિયમ: ₹{row['Premium']}\n" if row.get('Premium') else ""
                    
                    # વ્હોટ્સએપ મેસેજ ફોર્મેટ (હરિ ઓમ ઇન્સ્યોરન્સ & લોન એડવાઇઝર)
                    msg_text = (
                        f"*હરિ ઓમ ઇન્સ્યોરન્સ & લોન એડવાઇઝર*\n"
                        f"F-46, વાત્સલ્ય સ્ટેટસ, ધવલ પ્લાઝા પાસે, કડી-૩૮૪૪૪૦.\n"
                        f"મો: 7698564672 / 9714776364\n\n"
                        f"નમસ્તે *{row['Name']}*જી,\n\n"
                        f"આપના વાહન નંબર: *{row['Vehicle_No']}*\n"
                        f"{type_text}"
                        f"{comp_text}"
                        f"પોલિસી નંબર: *{row['Policy_No']}*\n"
                        f"{prem_text}"
                        f"ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['Expiry_Date']}* ના રોજ પૂર્ણ થાય છે (માત્ર *{row['Days_Left']}* દિવસ બાકી).\n\n"
                        f"પોલિસી લેપ્સ ન થાય અને ક્લેમ સુવિધા જળવાઈ રહે તે માટે સમયસર રિન્યુ કરાવવા વિનંતી.\n"
                        f"બેસ્ટ ડિસ્કાઉન્ટ અને ત્વરિત રિન્યુઅલ માટે સંપર્ક કરો."
                    )
                    
                    encoded_msg = urllib.parse.quote(msg_text)
                    clean_mobile = str(row['Mobile'])[-10:]
                    wa_url = f"https://wa.me/91{clean_mobile}?text={encoded_msg}"
                    
                    with c1:
                        st.markdown(f"👤 **{row['Name']}** ({row['Mobile']}) | 🚘 વાહન: `{row['Vehicle_No']}` | 🏢 કંપની: **{row.get('Company', 'N/A')}**")
                        st.markdown(f"📄 પોલિસી: `{row['Policy_No']}` | 📅 એક્સપાયરી: **{row['Expiry_Date']}** (બાકી દિવસ: **{row['Days_Left']}**)")
                        if row.get('Premium'):
                            st.caption(f"💰 પ્રીમિયમ રકમ: ₹{row['Premium']} | 📝 નોંધ: {row.get('Notes', 'કોઈ નથી')}")
                    
                    with c2:
                        st.link_button("📲 WhatsApp મોકલો", wa_url, use_container_width=True)
                    st.divider()
        else:
            st.success("🎉 હાલમાં આગામી ૧૫ દિવસમાં એક્સપાયર થતી કોઈ પોલિસી નથી!")
    else:
        st.info("કોઈ ડેટા ઉપલબ્ધ નથી.")

# ----------------- ૩. કસ્ટમર ડિટેલ્સ ટેબ -----------------
with tab_details:
    st.subheader("📁 ગ્રાહકોની તમામ વિગતો (Customer Profiles)")
    if not df.empty:
        # CSV Export બટન
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 તમામ ગ્રાહક ડેટા CSV તરીકે ડાઉનલોડ કરો",
            data=csv_data,
            file_name=f"HariOm_Insurance_Data_{date.today()}.csv",
            mime="text/csv"
        )
        st.write("")
        
        # ગ્રાહક પસંદ કરો
        selected_cust = st.selectbox("ગ્રાહક પ્રોફાઇલ કાર્ડ જોવા માટે પસંદ કરો:", options=df["ID"].tolist(), format_func=lambda x: f"{df[df['ID']==x]['Name'].values[0]} - {df[df['ID']==x]['Vehicle_No'].values[0]} ({df[df['ID']==x]['Policy_No'].values[0]})")
        
        if selected_cust:
            cust_row = df[df["ID"] == selected_cust].iloc[0]
            
            st.markdown(f"""
            <div style="background-color: #F0F9FF; border: 2px solid #0284C7; border-radius: 12px; padding: 20px; margin-top: 10px;">
                <h3 style="color: #0369A1; margin-top:0;">👤 {cust_row['Name']}</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 16px;">
                    <p><b>📞 મોબાઇલ નંબર:</b> {cust_row['Mobile']}</p>
                    <p><b>🚘 વાહન નંબર:</b> {cust_row['Vehicle_No']}</p>
                    <p><b>🛵 વાહનનો પ્રકાર:</b> {cust_row.get('Vehicle_Type', 'N/A')}</p>
                    <p><b>🏢 ઇન્સ્યોરન્સ કંપની:</b> {cust_row.get('Company', 'N/A')}</p>
                    <p><b>📄 પોલિસી નંબર:</b> {cust_row['Policy_No']}</p>
                    <p><b>📅 એક્સપાયરી તારીખ:</b> {cust_row['Expiry_Date']}</p>
                    <p><b>💰 પ્રીમિયમ રકમ:</b> ₹{cust_row.get('Premium', 'N/A')}</p>
                    <p><b>📝 નોંધ / રિમાર્ક્સ:</b> {cust_row.get('Notes', 'N/A')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        st.write("### 📊 તમામ ગ્રાહકોનું કોષ્ટક")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("હાલમાં કોઈ ગ્રાહક ડેટા ઉપલબ્ધ નથી.")

# ----------------- ૪. એન્ટ્રી ઉમેરો / એડિટ / ડિલીટ ટેબ -----------------
with tab_manage:
    manage_action = st.radio("એક્શન પસંદ કરો:", ["➕ નવી એન્ટ્રી ઉમેરો", "✏️ એડિટ કરો (Edit)", "❌ ડિલીટ કરો (Delete)"], horizontal=True)
    st.divider()
    
    # --- નવી એન્ટ્રી ---
    if manage_action == "➕ નવી એન્ટ્રી ઉમેરો":
        st.subheader("નવી પોલિસી વિગત ઉમેરો")
        with st.form("add_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            name = col_a.text_input("ગ્રાહકનું નામ *")
            mobile = col_b.text_input("મોબાઇલ નંબર (10 અંક) *")
            
            vehicle = col_a.text_input("વાહન નંબર (દા.ત. GJ-02-AB-1234) *")
            vehicle_type = col_b.selectbox("વાહનનો પ્રકાર", ["2 Wheeler (ટૂ વ્હીલર)", "4 Wheeler (કાર/જીપ)", "Commercial Vehicle", "Tractor", "Auto / Three Wheeler", "Bus / Truck", "અન્ય"])
            
            company = col_a.text_input("ઇન્સ્યોરન્સ કંપની (દા.ત. ICICI Lombard, Bajaj, TATA AIG)")
            policy_no = col_b.text_input("પોલિસી નંબર (Policy No.) *")
            
            expiry = col_a.date_input("પોલિસી એક્સપાયરી તારીખ *", min_value=date.today())
            premium = col_b.text_input("પ્રીમિયમ રકમ (₹)")
            
            notes = st.text_area("નોંધ / વધારાની વિગત (Notes)")
            
            submit_btn = st.form_submit_button("💾 સેવ કરો")
            if submit_btn:
                if name and mobile and vehicle and policy_no:
                    new_id = str(len(df) + 1)
                    new_row = pd.DataFrame([{
                        "ID": new_id,
                        "Name": name.strip(),
                        "Mobile": str(mobile).strip(),
                        "Vehicle_No": vehicle.upper().strip(),
                        "Vehicle_Type": vehicle_type,
                        "Company": company.strip(),
                        "Policy_No": policy_no.strip(),
                        "Expiry_Date": str(expiry),
                        "Premium": premium.strip(),
                        "Notes": notes.strip()
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("✅ નવી પોલિસી સફળતાપૂર્વક ઉમેરાઈ ગઈ!")
                    st.rerun()
                else:
                    st.error("કૃપા કરીને તારાંકિત (*) તમામ જરૂરી વિગતો ભરો.")

    # --- એડિટ કરો ---
    elif manage_action == "✏️ એડિટ કરો (Edit)":
        st.subheader("હાલની પોલિસીમાં સુધારો કરો")
        if not df.empty:
            record_options = {f"{row['Vehicle_No']} - {row['Name']} ({row['Policy_No']})": row['ID'] for _, row in df.iterrows()}
            selected_label = st.selectbox("સુધારવા માટે વાહન / ગ્રાહક પસંદ કરો:", list(record_options.keys()))
            
            selected_id = record_options[selected_label]
            row_to_edit = df[df["ID"] == selected_id].iloc[0]
            
            with st.form("edit_form"):
                col_a, col_b = st.columns(2)
                edit_name = col_a.text_input("ગ્રાહકનું નામ", value=row_to_edit["Name"])
                edit_mobile = col_b.text_input("મોબાઇલ નંબર", value=row_to_edit["Mobile"])
                
                edit_vehicle = col_a.text_input("વાહન નંબર", value=row_to_edit["Vehicle_No"])
                
                v_type_val = row_to_edit.get("Vehicle_Type", "2 Wheeler (ટૂ વ્હીલર)")
                v_options = ["2 Wheeler (ટૂ વ્હીલર)", "4 Wheeler (કાર/જીપ)", "Commercial Vehicle", "Tractor", "Auto / Three Wheeler", "Bus / Truck", "અન્ય"]
                v_idx = v_options.index(v_type_val) if v_type_val in v_options else 0
                edit_vehicle_type = col_b.selectbox("વાહનનો પ્રકાર", v_options, index=v_idx)
                
                edit_company = col_a.text_input("ઇન્સ્યોરન્સ કંપની", value=row_to_edit.get("Company", ""))
                edit_policy = col_b.text_input("પોલિસી નંબર", value=row_to_edit["Policy_No"])
                
                curr_date = datetime.strptime(row_to_edit["Expiry_Date"], "%Y-%m-%d").date() if pd.notnull(row_to_edit["Expiry_Date"]) and row_to_edit["Expiry_Date"] != "" else date.today()
                edit_expiry = col_a.date_input("પોલિસી એક્સપાયરી તારીખ", value=curr_date)
                
                edit_premium = col_b.text_input("પ્રીમિયમ રકમ (₹)", value=row_to_edit.get("Premium", ""))
                edit_notes = st.text_area("નોંધ / વધારાની વિગત", value=row_to_edit.get("Notes", ""))
                
                update_btn = st.form_submit_button("🔄 અપડેટ કરો")
                if update_btn:
                    df.loc[df["ID"] == selected_id, ["Name", "Mobile", "Vehicle_No", "Vehicle_Type", "Company", "Policy_No", "Expiry_Date", "Premium", "Notes"]] = [
                        edit_name.strip(), str(edit_mobile).strip(), edit_vehicle.upper().strip(), edit_vehicle_type, edit_company.strip(), edit_policy.strip(), str(edit_expiry), edit_premium.strip(), edit_notes.strip()
                    ]
                    save_data(df)
                    st.success("✅ વિગતો સફળતાપૂર્વક અપડેટ થઈ ગઈ!")
                    st.rerun()
        else:
            st.info("કોઈ ડેટા ઉપલબ્ધ નથી.")

    # --- ડિલીટ કરો ---
    elif manage_action == "❌ ડિલીટ કરો (Delete)":
        st.subheader("પોલિસી રદ / ડિલીટ કરો")
        if not df.empty:
            record_options = {f"{row['Vehicle_No']} - {row['Name']} ({row['Policy_No']})": row['ID'] for _, row in df.iterrows()}
            selected_label = st.selectbox("ડિલીટ કરવા માટે વાહન પસંદ કરો:", list(record_options.keys()))
            
            selected_id = record_options[selected_label]
            
            st.warning("⚠️ શું તમે ખરેખર આ એન્ટ્રી ડિલીટ કરવા માંગો છો?")
            if st.button("❌ હા, ડિલીટ કરો"):
                df = df[df["ID"] != selected_id]
                save_data(df)
                st.success("🗑️ એન્ટ્રી સફળતાપૂર્વક ડિલીટ થઈ ગઈ!")
                st.rerun()
        else:
            st.info("કોઈ ડેટા ઉપલબ્ધ નથી.")
```

તમે GitHub માં `app.py` અપડેટ કરશો એટલે Streamlit પર લોગો અને તમામ નવા ફીચર્સ સાથે એપ અપડેટ થઈ જશે!
