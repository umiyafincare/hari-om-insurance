import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import urllib.parse

# પેજ સેટઅપ
st.set_page_config(
    page_title="Hari Om Insurance - Vehicle Reminder App",
    page_icon="🚗",
    layout="wide"
)

DB_FILE = "insurance_data.csv"

# ડેટાબેઝ લોડ કરવાનું ફંક્શન
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE, dtype=str)
        if "ID" not in df.columns:
            df["ID"] = [str(i+1) for i in range(len(df))]
            df.to_csv(DB_FILE, index=False)
        return df
    return pd.DataFrame(columns=["ID", "Name", "Mobile", "Vehicle_No", "Policy_No", "Expiry_Date"])

# ડેટાબેઝ સેવ કરવાનું ફંક્શન
def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

# ----------------- હેડર અને બ્રાન્ડિંગ -----------------
st.markdown("""
    <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); padding: 25px; border-radius: 15px; color: white; text-align: center; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
        <h1 style="margin: 0; color: #FBBF24; font-size: 38px; font-weight: bold;">HARI OM INSURANCE</h1>
        <p style="font-size: 16px; margin: 8px 0 4px 0; color: #E0E7FF;">📍 F-46, VATSALY STATUS, NR.DHAVAL PLAZA, KADI-384440.</p>
        <p style="font-size: 20px; font-weight: bold; margin: 0; color: #6EE7B7;">📞 MO: 7698564672 / 9714776364</p>
    </div>
""", unsafe_allow_html=True)

# ----------------- ટેબ્સ -----------------
tab_dash, tab_reminders, tab_manage = st.tabs([
    "📊 ડેશબોર્ડ (Dashboard)", 
    "🔔 ૧૫ દિવસના રીમાઇન્ડર્સ", 
    "⚙️ એન્ટ્રી ઉમેરો / એડિટ / ડિલીટ"
])

# ----------------- ૧. ડેશબોર્ડ ટેબ -----------------
with tab_dash:
    st.subheader("📌 બિઝનેસ ડેશબોર્ડ")
    
    if not df.empty:
        # ડેટા પ્રોસેસિંગ
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
        col1.metric("કુલ પોલિસીઓ", total_policies, delta=None)
        col2.metric("૧૫ દિવસમાં એક્સપાયર થતી", expiring_15, delta_color="inverse")
        col3.metric("એક્સપાયર્ડ થઈ ગયેલી", expired, delta_color="inverse")
        col4.metric("એક્ટિવ પોલિસીઓ (>15 દિવસ)", active)
        
        st.divider()
        
        # શોધો અને ફિલ્ટર કરો
        search_term = st.text_input("🔍 ગ્રાહકના નામ, વાહન નંબર અથવા પોલિસી નંબરથી શોધો:")
        if search_term:
            filtered_df = temp_df[
                temp_df["Name"].str.contains(search_term, case=False, na=False) |
                temp_df["Vehicle_No"].str.contains(search_term, case=False, na=False) |
                temp_df["Policy_No"].str.contains(search_term, case=False, na=False)
            ]
            st.dataframe(filtered_df[["Name", "Mobile", "Vehicle_No", "Policy_No", "Expiry_Date", "Days_Left"]], use_container_width=True)
        else:
            st.write("### 📋 તાજેતરની પોલિસી વિગતો")
            st.dataframe(temp_df[["Name", "Mobile", "Vehicle_No", "Policy_No", "Expiry_Date", "Days_Left"]], use_container_width=True)
            
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
                with st.card() if hasattr(st, "card") else st.container():
                    c1, c2 = st.columns([3, 1])
                    
                    # વ્હોટ્સએપ મેસેજ ફોર્મેટ (હરિ ઓમ ઇન્સ્યોરન્સ)
                    msg_text = (
                        f"*હરિ ઓમ ઇન્સ્યોરન્સ*\n"
                        f"F-46, વાત્સલ્ય સ્ટેટસ, ધવલ પ્લાઝા પાસે, કડી-૩૮૪૪૪૦.\n"
                        f"મો: 7698564672 / 9714776364\n\n"
                        f"નમસ્તે *{row['Name']}*જી,\n\n"
                        f"આપના વાહન નંબર: *{row['Vehicle_No']}*\n"
                        f"પોલિસી નંબર: *{row['Policy_No']}*\n"
                        f"ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['Expiry_Date']}* ના રોજ પૂર્ણ થાય છે (માત્ર *{row['Days_Left']}* દિવસ બાકી).\n\n"
                        f"પોલિસી લેપ્સ ન થાય અને ક્લેમ સુવિધા જળવાઈ રહે તે માટે સમયસર રિન્યુ કરાવવા વિનંતી.\n"
                        f"બેસ્ટ ડિસ્કાઉન્ટ અને ત્વરિત રિન્યુઅલ માટે આ નંબર પર સંપર્ક કરો."
                    )
                    
                    encoded_msg = urllib.parse.quote(msg_text)
                    clean_mobile = str(row['Mobile'])[-10:]
                    wa_url = f"https://wa.me/91{clean_mobile}?text={encoded_msg}"
                    
                    with c1:
                        st.markdown(f"👤 **{row['Name']}** | 🚘 વાહન: `{row['Vehicle_No']}` | 📄 પોલિસી: `{row['Policy_No']}`")
                        st.markdown(f"📅 એક્સપાયરી તારીખ: **{row['Expiry_Date']}** (બાકી દિવસ: **{row['Days_Left']}**)")
                    
                    with c2:
                        st.link_button("📲 WhatsApp મોકલો", wa_url, use_container_width=True)
                    st.divider()
        else:
            st.success("🎉 હાલમાં આગામી ૧૫ દિવસમાં એક્સપાયર થતી કોઈ પોલિસી નથી!")
    else:
        st.info("કોઈ ડેટા ઉપલબ્ધ નથી.")

# ----------------- ૩. એન્ટ્રી ઉમેરો / એડિટ / ડિલીટ ટેબ -----------------
with tab_manage:
    manage_action = st.radio("એક્શન પસંદ કરો:", ["➕ નવી એન્ટ્રી ઉમેરો", "✏️ એડિટ કરો (Edit)", "❌ ડિલીટ કરો (Delete)"], horizontal=True)
    st.divider()
    
    # --- નવી એન્ટ્રી ---
    if manage_action == "➕ નવી એન્ટ્રી ઉમેરો":
        st.subheader("નવી પોલિસી વિગત ઉમેરો")
        with st.form("add_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            name = col_a.text_input("ગ્રાહકનું નામ")
            mobile = col_b.text_input("મોબાઇલ નંબર (10 અંક)")
            vehicle = col_a.text_input("વાહન નંબર (દા.ત. GJ-02-AB-1234)")
            policy_no = col_b.text_input("પોલિસી નંબર (Policy No.)")
            expiry = st.date_input("પોલિસી એક્સપાયરી તારીખ", min_value=date.today())
            
            submit_btn = st.form_submit_button("💾 સેવ કરો")
            if submit_btn:
                if name and mobile and vehicle and policy_no:
                    new_id = str(len(df) + 1)
                    new_row = pd.DataFrame([{
                        "ID": new_id,
                        "Name": name.strip(),
                        "Mobile": str(mobile).strip(),
                        "Vehicle_No": vehicle.upper().strip(),
                        "Policy_No": policy_no.strip(),
                        "Expiry_Date": str(expiry)
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("✅ નવી પોલિસી સફળતાપૂર્વક ઉમેરાઈ ગઈ!")
                    st.rerun()
                else:
                    st.error("કૃપા કરીને બધી વિગતો ભરો.")

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
                edit_policy = col_b.text_input("પોલિસી નંબર", value=row_to_edit["Policy_No"])
                
                # તારીખ સેટ કરવી
                curr_date = datetime.strptime(row_to_edit["Expiry_Date"], "%Y-%m-%d").date() if pd.notnull(row_to_edit["Expiry_Date"]) else date.today()
                edit_expiry = st.date_input("પોલિસી એક્સપાયરી તારીખ", value=curr_date)
                
                update_btn = st.form_submit_button("🔄 અપડેટ કરો")
                if update_btn:
                    df.loc[df["ID"] == selected_id, ["Name", "Mobile", "Vehicle_No", "Policy_No", "Expiry_Date"]] = [
                        edit_name.strip(), str(edit_mobile).strip(), edit_vehicle.upper().strip(), edit_policy.strip(), str(edit_expiry)
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
