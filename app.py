import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import os

# הגדרות דף
st.set_page_config(page_title="ניהול אוסף מטבעות", layout="wide")

# תפריט צד
st.sidebar.title("🔑 גישה למערכת")
api_key_input = st.sidebar.text_input("הכנס Google API Key", type="password")
password_input = st.sidebar.text_input("סיסמת גישה", type="password")

if password_input != "1234":
    st.warning("אנא הכנס סיסמה בתפריט הצד.")
    st.stop()

# ניהול מסד נתונים
DB_FILE = 'catalog.csv'
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["מזהה", "מידע", "מחיר"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# ממשק משתמש
st.title("💰 קטלוג המטבעות הפרטי שלי")
tab1, tab2 = st.tabs(["🆕 הוספת מטבע חדש", "📜 ניהול האוסף"])

with tab1:
    st.header("צילום המטבע")
    col1, col2 = st.columns(2)
    with col1:
        img_front = st.file_uploader("צד קדמי", type=["jpg", "jpeg", "png"])
    with col2:
        img_back = st.file_uploader("צד אחורי", type=["jpg", "jpeg", "png"])

    if img_front and img_back and api_key_input:
        if st.button("🔍 זהה מטבע"):
            try:
                with st.spinner('מנתח...'):
                    # הגדרת ה-API בתוך הפונקציה למניעת שגיאות גרסה
                    genai.configure(api_key=api_key_input)
                    
                    # שינוי חשוב: שימוש בשם המודל המלא והעדכני
                    model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
                    
                    p1 = Image.open(img_front)
                    p2 = Image.open(img_back)
                    
                    prompt = "Identify this coin based on these images. Tell me the country, year, and estimated value in ILS. Hebrew only."
                    
                    # שליחה לזיהוי
                    response = model.generate_content([prompt, p1, p2])
                    st.session_state['temp_info'] = response.text
            except Exception as e:
                st.error(f"שגיאה מהשרת של גוגל: {str(e)}")
                st.info("טיפ: וודא שה-API Key תקין ושיש לך חיבור אינטרנט יציב.")

        if 'temp_info' in st.session_state:
            final_info = st.text_area("ערוך מידע:", value=st.session_state['temp_info'], height=150)
            final_price = st.text_input("מחיר מבוקש:")
            if st.button("💾 שמור לאוסף"):
                df = load_data()
                new_row = {"מזהה": len(df)+1, "מידע": final_info, "מחיר": final_price}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df)
                st.success("נשמר!")
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
