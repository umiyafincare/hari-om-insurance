import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import urllib.parse

st.set_page_config(page_title="Vehicle Insurance Reminders", layout="wide")

DB_FILE = "insurance_data.csv"

# ડેટાબેઝ લોડ કે ક્રીએટ કરવાનું ફંક્શન
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Name", "Mobile", "Vehicle_No", "Policy_Company", "Expiry_Date"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

df = load_data()

st.title("🚗 વ્હીકલ ઇન્સ્યોરન્સ રીમાઇન્ડર સિસ્ટમ")

# ટેબ્સ - ડેશબોર્ડ અને નવી એન્ટ્રી
tab1, tab2 = st.tabs(["🔔 આગામી રીમાઇન્ડર્સ (૧૫ દિવસ)", "➕ નવી પોલિસી ઉમેરો"])

with tab2:
    st.subheader("ગ્રાહકની વિગત ઉમેરો")
    with st.form("new_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        name = col1.text_input("ગ્રાહકનું નામ")
        mobile = col2.text_input("મોબાઇલ નંબર (દા.ત. 9876543210)")
        vehicle = col1.text_input("વાહન નંબર (દા.ત. GJ-02-AB-1234)")
        company = col2.text_input("ઇન્સ્યોરન્સ કંપની")
        expiry = st.date_input("પોલિસી એક્સપાયરી તારીખ", min_value=date.today())
        
        submitted = st.form_submit_button("ડેટા સેવ કરો")
        if submitted:
            if name and mobile and vehicle:
                new_row = pd.DataFrame([{
                    "Name": name,
                    "Mobile": str(mobile).strip(),
                    "Vehicle_No": vehicle.upper().strip(),
                    "Policy_Company": company,
                    "Expiry_Date": str(expiry)
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("✅ ડેટા સફળતાપૂર્વક ઉમેરાઈ ગયો!")
                st.rerun()
            else:
                st.error("કૃપા કરીને બધી જરૂરી વિગતો ભરો.")

with tab1:
    st.subheader("📋 એક્સપાયર થતી પોલિસીઓ")
    
    if not df.empty:
        df["Expiry_Date_dt"] = pd.to_datetime(df["Expiry_Date"]).dt.date
        today = date.today()
        
        # બાકી દિવસોની ગણતરી
        df["Days_Left"] = (df["Expiry_Date_dt"] - today).apply(lambda x: x.days)
        
        # ૧૫ દિવસ કે તેથી ઓછા દિવસ બાકી હોય તેનું લિસ્ટ (અને એક્સપાયર ના થઈ હોય)
        reminders = df[(df["Days_Left"] <= 15) & (df["Days_Left"] >= 0)].sort_values(by="Days_Left")
        
        if not reminders.empty:
            st.warning(f"કુલ {len(reminders)} પોલિસી રિન્યુઅલ માટે બાકી છે.")
            
            for _, row in reminders.iterrows():
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    
                    # WhatsApp મેસેજ ટેમ્પલેટ
                    msg_text = (
                        f"નમસ્તે {row['Name']}જી,\n\n"
                        f"આપના વાહન નંબર *{row['Vehicle_No']}* ના ઇન્સ્યોરન્સની મુદત તારીખ *{row['Expiry_Date']}* ના રોજ પૂર્ણ થઈ રહી છે ({row['Days_Left']} દિવસ બાકી).\n\n"
                        f"કંપની: {row['Policy_Company']}\n\n"
                        f"પોલિસી લેપ્સ ન થાય તે માટે સમયસર રિન્યુ કરાવવા વિનંતી.\n"
                        f"રિન્યુઅલ અને બેસ્ટ પ્રીમિયમ માટે આ નંબર પર સંપર્ક કરો."
                    )
                    
                    encoded_msg = urllib.parse.quote(msg_text)
                    clean_mobile = str(row['Mobile'])[-10:]
                    wa_url = f"https://wa.me/91{clean_mobile}?text={encoded_msg}"
                    
                    with col_a:
                        st.markdown(f"**{row['Name']}** | વાહન: `{row['Vehicle_No']}` | બાકી દિવસ: **{row['Days_Left']}** (તારીખ: {row['Expiry_Date']})")
                    
                    with col_b:
                        st.link_button("📲 WhatsApp મોકલો", wa_url)
                    st.divider()
        else:
            st.info("હાલમાં આગામી ૧૫ દિવસમાં કોઈ પોલિસી એક્સપાયર થતી નથી.")
            
        # તમામ ડેટા ટેબલ
        with st.expander("બધો ડેટા જુઓ"):
            st.dataframe(df[["Name", "Mobile", "Vehicle_No", "Policy_Company", "Expiry_Date"]])
    else:
        st.info("કોઈ ડેટા ઉપલબ્ધ નથી. નવી એન્ટ્રી ઉમેરો.")
