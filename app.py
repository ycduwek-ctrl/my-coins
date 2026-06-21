import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import os

st.set_page_config(page_title="ניהול אוסף מטבעות", layout="wide")

st.sidebar.title("🔑 גישה למערכת")
# ניקוי רווחים קיצוני
raw_key = st.sidebar.text_input("הכנס Google API Key", type="password")
api_key_input = raw_key.strip() if raw_key else ""
password_input = st.sidebar.text_input("סיסמת גישה", type="password").strip()

if password_input != "1234":
    st.warning("אנא הכנס סיסמה נכונה.")
    st.stop()

# ניהול מסד נתונים
DB_FILE = 'catalog.csv'
def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE)
        except: return pd.DataFrame(columns=["מזהה", "מידע", "מחיר"])
    return pd.DataFrame(columns=["מזהה", "מידע", "מחיר"])

st.title("💰 קטלוג המטבעות הפרטי שלי")
tab1, tab2 = st.tabs(["🆕 הוספת מטבע", "📜 ניהול האוסף"])

with tab1:
    col1, col2 = st.columns(2)
    with col1: img_front = st.file_uploader("צד קדמי", type=["jpg", "png", "jpeg"])
    with col2: img_back = st.file_uploader("צד אחורי", type=["jpg", "png", "jpeg"])

    if img_front and img_back and api_key_input:
        if st.button("🔍 זהה מטבע"):
            try:
                # אתחול ה-AI בכל לחיצה עם המפתח שסופק
                genai.configure(api_key=api_key_input)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                with st.spinner('מנתח...'):
                    p1 = Image.open(img_front)
                    p2 = Image.open(img_back)
                    # ניסיון זיהוי
                    response = model.generate_content(["Identify this coin. Country, Year, Value. Hebrew.", p1, p2])
                    st.session_state['ai_res'] = response.text
            except Exception as e:
                st.error(f"שגיאה: {str(e)}")
                st.info("אם המפתח מתחיל ב-AQ, וודא שהעתקת אותו במלואו ללא רווחים.")

        if 'ai_res' in st.session_state:
            info = st.text_area("פרטי המטבע:", value=st.session_state['ai_res'], height=150)
            price = st.text_input("מחיר:")
            if st.button("💾 שמור"):
                df = load_data()
                new_row = {"מזהה": len(df)+1, "מידע": info, "מחיר": price}
                pd.concat([df, pd.DataFrame([new_row])]).to_csv(DB_FILE, index=False)
                st.success("נשמר!")
                del st.session_state['ai_res']
