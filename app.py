import streamlit as st
import google.generativeai as genai
from PIL import Image
import pandas as pd
import os

st.set_page_config(page_title="קטלוג המטבעות שלי", layout="wide")

# ניסיון למשוך את המפתח מהסודות של המערכת
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("חסר מפתח API בהגדרות המערכת (Secrets)")
    st.stop()

# פונקציית זיהוי
def identify_coin(img1, img2):
    # ניסיון להשתמש בכמה שמות מודלים למקרה שאחד לא עובד
    for model_name in ['gemini-1.5-flash', 'models/gemini-1.5-flash', 'gemini-pro-vision']:
        try:
            model = genai.GenerativeModel(model_name)
            prompt = "זהה את המטבע בתמונות. פרט: מדינה, שנה, חומר והערכת מחיר בשקלים. ענה בעברית."
            response = model.generate_content([prompt, img1, img2])
            return response.text
        except:
            continue
    return "שגיאה: לא הצלחתי להתחבר למודל הזיהוי. וודא שהמפתח תקין."

# מסד נתונים פשוט
DB_FILE = 'catalog.csv'
def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["מזהה", "מידע", "מחיר"])

st.title("💰 קטלוג המטבעות החכם")

# האתר פתוח ישר (בלי סיסמה בצד, הסיסמה תהיה רק הלינק ששלחת לחברים)
tab1, tab2 = st.tabs(["🆕 הוספת מטבע", "📜 האוסף שלי"])

with tab1:
    col1, col2 = st.columns(2)
    with col1: img_f = st.file_uploader("צד קדמי", type=["jpg","png","jpeg"])
    with col2: img_b = st.file_uploader("צד אחורי", type=["jpg","png","jpeg"])

    if img_f and img_b:
        if st.button("🔍 זהה מטבע עכשיו"):
            with st.spinner('מנתח...'):
                res = identify_coin(Image.open(img_f), Image.open(img_b))
                st.session_state['info'] = res
        
        if 'info' in st.session_state:
            final_info = st.text_area("מידע מה-AI:", value=st.session_state['info'], height=150)
            price = st.text_input("כמה זה עולה?")
            if st.button("✅ שמור לאוסף"):
                df = load_data()
                new_row = {"מזהה": len(df)+1, "מידע": final_info, "מחיר": price}
                pd.concat([df, pd.DataFrame([new_row])]).to_csv(DB_FILE, index=False)
                st.success("נשמר!")
                del st.session_state['info']

with tab2:
    df = load_data()
    if df.empty: st.write("אין פריטים.")
    else:
        for i, r in df.iterrows():
            with st.expander(f"מטבע #{r['מזהה']} - {r['מחיר']} ש''ח"):
                st.write(r['מידע'])
                if st.button(f"מחק פריט {r['מזהה']}", key=f"d_{i}"):
                    df.drop(i).to_csv(DB_FILE, index=False)
                    st.rerun()
