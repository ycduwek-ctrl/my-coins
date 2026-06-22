import streamlit as st
import pandas as pd
import os

# --- הגדרות דף ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

# --- מערכת אבטחה (מיילים מאושרים) ---
# ב-Secrets תגדיר רשימה: APPROVED_EMAILS = ["admin@me.com", "client@test.com"]
APPROVED_EMAILS = ["admin@gmail.com", "user1@gmail.com"] # לדוגמה

if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None

def login_screen():
    st.title("🔒 כניסה למערכת המאובטחת")
    email = st.text_input("הכנס כתובת מייל:")
    if st.button("כניסה"):
        if email in APPROVED_EMAILS:
            st.session_state["logged_in_user"] = email
            st.rerun()
        else:
            st.error("מייל לא מאושר. פנה למנהל המערכת.")
    st.stop()

if not st.session_state["logged_in_user"]:
    login_screen()

# --- זיהוי אם המשתמש הוא מנהל (אתה) ---
IS_ADMIN = st.session_state["logged_in_user"] == "admin@gmail.com"

# --- ניהול נתונים (שימוש ב-CSV כרגע, מומלץ לעבור לגוגל שיטס) ---
DB_FILE = 'coin_catalog.csv'
def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["מזהה", "שם", "מחיר_מנהל", "תמונות", "הצעות_לקוחות"])

# --- תפריט ראשי ---
st.sidebar.write(f"שלום, {st.session_state['logged_in_user']}")
if st.sidebar.button("התנתק"):
    st.session_state["logged_in_user"] = None
    st.rerun()

st.title("🪙 קטלוג המטבעות היוקרתי")

tab1, tab2 = st.tabs(["🖼️ גלריית מטבעות", "⚙️ ניהול קטלוג (מנהל בלבד)"])

with tab1:
    df = load_data()
    if df.empty:
        st.write("אין עדיין מטבעות בקטלוג.")
    else:
        # הצגת המטבעות בגלריה (3 בעמודה)
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                st.subheader(row["שם"])
                # מציג רק תמונה ראשונה
                img_list = str(row["תמונות"]).split(",")
                st.image(img_list[0], use_container_width=True)
                
                with st.expander("לפרטים נוספים ותמונות"):
                    # הצגת כל שאר התמונות
                    for extra_img in img_list:
                        st.image(extra_img)
                    
                    st.write(f"**מחיר מבוקש:** {row['מחיר_מנהל']} ש''ח")
                    
                    # הצעת מחיר לקוח
                    st.divider()
                    st.write("💬 הצע מחיר או השאר הודעה:")
                    offer = st.text_input(f"הצעה עבור {row['שם']}", key=f"offer_{idx}")
                    if st.button("שלח הצעה", key=f"btn_{idx}"):
                        # כאן נוסיף קוד שמעדכן את השורה בטבלה בלי לדרוס
                        st.success("ההצעה נשלחה למנהל!")

with tab2:
    if not IS_ADMIN:
        st.error("אין לך הרשאה לנהל את הקטלוג.")
    else:
        st.header("העלאת מטבע חדש")
        coin_name = st.text_input("שם המטבע:")
        coin_price = st.text_input("מחיר מבוקש (שח):")
        # העלאת מספר תמונות יחד
        uploaded_files = st.file_uploader("בחר תמונות למטבע (ניתן לבחור כמה):", accept_multiple_files=True, type=['jpg','png','jpeg'])
        
        if st.button("פרסם מטבע"):
            if uploaded_files and coin_name:
                # כאן צריך להעלות את התמונות לענן ולקבל לינקים
                # לצורך הדוגמה נשמור רק את השמות שלהם
                links = [f.name for f in uploaded_files] 
                links_str = ",".join(links)
                
                df = load_data()
                new_coin = {"מזהה": len(df)+1, "שם": coin_name, "מחיר_מנהל": coin_price, "תמונות": links_str, "הצעות_לקוחות": ""}
                pd.concat([df, pd.DataFrame([new_coin])]).to_csv(DB_FILE, index=False)
                st.success("המטבע הועלה בהצלחה!")
