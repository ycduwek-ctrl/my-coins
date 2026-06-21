import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import os

st.set_page_config(page_title="ניהול אוסף מטבעות", layout="wide")

# תפריט צד
st.sidebar.title("🔑 גישה למערכת")
# שימוש ב-strip() כדי למחוק רווחים מיותרים בטעות
api_key_input = st.sidebar.text_input("הכנס Google API Key", type="password").strip()
password_input = st.sidebar.text_input("סיסמת גישה", type="password").strip()

if password_input != "1234":
    st.warning("אנא הכנס סיסמה נכונה (1234).")
    st.stop()

if not api_key_input:
    st.info("אנא הכנס את ה-API Key שמתחיל ב-AIza...")
    st.stop()

# ניהול מסד נתונים
DB_FILE = 'catalog.csv'
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["מזהה", "מידע", "מחיר"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

st.title("💰 קטלוג המטבעות הפרטי שלי")
tab1, tab2 = st.tabs(["🆕 הוספת מטבע חדש", "📜 ניהול האוסף"])

with tab1:
    st.header("צילום המטבע")
    col1, col2 = st.columns(2)
    with col1:
        img_front = st.file_uploader("צד קדמי", type=["jpg", "jpeg", "png"])
    with col2:
        img_back = st.file_uploader("צד אחורי", type=["jpg", "jpeg", "png"])

    if img_front and img_back:
        if st.button("🔍 זהה מטבע"):
            try:
                with st.spinner('מתחבר ל-AI של גוגל...'):
                    # הגדרה מחדש בכל לחיצה כדי לוודא שהמפתח נקלט
                    genai.configure(api_key=api_key_input)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    p1 = Image.open(img_front)
                    p2 = Image.open(img_back)
                    
                    prompt = "Identify this coin. Country, Year, and Value in ILS. Hebrew only."
                    response = model.generate_content([prompt, p1, p2])
                    
                    if response.text:
                        st.session_state['temp_info'] = response.text
                    else:
                        st.error("ה-AI לא החזיר תשובה. נסה תמונה ברורה יותר.")
            except Exception as e:
                error_msg = str(e)
                if "API_KEY_INVALID" in error_msg:
                    st.error("המפתח שהכנסת לא תקין. וודא שהוא מתחיל ב-AIza.")
                else:
                    st.error(f"שגיאה: {error_msg}")

        if 'temp_info' in st.session_state:
            final_info = st.text_area("ערוך מידע:", value=st.session_state['temp_info'], height=150)
            final_price = st.text_input("מחיר מבוקש:")
            if st.button("💾 שמור לאוסף"):
                df = load_data()
                new_row = {"מזהה": len(df)+1, "מידע": final_info, "מחיר": final_price}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("נשמר בהצלחה!")
                del st.session_state['temp_info']

with tab2:
    df = load_data()
    if df.empty:
        st.write("האוסף ריק.")
    else:
        for index, row in df.iterrows():
            with st.expander(f"מטבע #{row['מזהה']} - {row['מחיר']} ש''ח"):
                st.write(row['מידע'])
                if st.button(f"🗑️ מחק #{row['מזהה']}", key=f"del_{index}"):
                    df = df.drop(index)
                    save_data(df)
                    st.rerun()
