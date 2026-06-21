import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import os

# --- הגדרות בסיסיות ---
st.set_page_config(page_title="קטלוג מטבעות חכם", layout="wide")

# הגדרת ה-API של גוגל (כאן תכניס את המפתח שלך או נשתמש ב-Secrets של Streamlit)
API_KEY = st.sidebar.text_input("הכנס Google API Key", type="password")
PASSWORD = "1234"  # שנה את זה לסיסמה שאתה רוצה לחברים

if API_KEY:
    genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(model_name="gemini-1.5-flash")

# פונקציה לניהול מסד הנתונים (שמירה לקובץ CSV פשוט)
def save_to_catalog(data):
    df = pd.DataFrame([data])
    if not os.path.isfile('catalog.csv'):
        df.to_csv('catalog.csv', index=False)
    else:
        df.to_csv('catalog.csv', mode='a', header=False, index=False)

# --- ממשק המשתמש ---
st.title("💰 מערכת זיהוי וניהול מטבעות לאספנים")

# בדיקת סיסמה
user_pass = st.sidebar.text_input("סיסמת גישה למערכת", type="password")

if user_pass != PASSWORD:
    st.warning("אנא הכנס סיסמה נכונה בתפריט הצד כדי להתחיל.")
    st.stop()

# יצירת טאבים: העלאה חדשה ותצוגת האוסף
tab1, tab2 = st.tabs(["🆕 העלאת מטבע חדש", "📜 האוסף שלי"])

with tab1:
    st.header("העלה תמונה לזיהוי")
    uploaded_file = st.file_uploader("בחר תמונה מהגלריה...", type=["jpg", "jpeg", "png"])

    if uploaded_file and API_KEY:
        image = Image.open(uploaded_file)
        st.image(image, caption='המטבע שצולם', width=300)
        
        if st.button("🔍 זהה מטבע בעזרת AI"):
            with st.spinner('המערכת מנתחת את המטבע...'):
                prompt = """זהה את המטבע שבתמונה. החזר תשובה בפורמט הבא בלבד בעברית:
                שם המטבע: [שם]
                שנה: [שנה]
                מדינה: [מדינה]
                חומר: [זהב/כסף/נחושת וכו']
                הערכת מחיר לאספנים: [טווח מחיר בשקלים]
                תיאור קצר: [תיאור]"""
                
                response = model.generate_content([prompt, p1, p2])
                ai_result = response.text
                st.session_state['ai_info'] = ai_result

        # טופס עריכה ידנית
        if 'ai_info' in st.session_state:
            st.subheader("ערוך ואשר את הפרטים:")
            edited_info = st.text_area("מידע על המטבע:", value=st.session_state['ai_info'], height=200)
            price = st.text_input("מחיר סופי שאתה קובע (שח):")
            
            if st.button("✅ שמור לאוסף הפרטי"):
                save_to_catalog({"מידע": edited_info, "מחיר": price})
                st.success("המטבע נשמר בהצלחה!")
                del st.session_state['ai_info']

with tab2:
    st.header("הקטלוג שלך")
    if os.path.isfile('catalog.csv'):
        catalog_df = pd.read_csv('catalog.csv')
        st.dataframe(catalog_df, use_container_width=True)
    else:
        st.info("האוסף עדיין ריק.")
