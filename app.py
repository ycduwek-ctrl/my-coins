import streamlit as st
import pandas as pd
import os
from PIL import Image

# הגדרות דף
st.set_page_config(page_title="קטלוג מטבעות", layout="wide")

# יצירת תיקיית תמונות אם לא קיימת
if not os.path.exists("coin_images"):
    os.makedirs("coin_images")

# פונקציה לטעינת נתונים
DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "my_price", "images", "offers"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# כותרת האתר
st.markdown("<h1 style='text-align: center;'>🪙 קטלוג המטבעות שלי</h1>", unsafe_allow_html=True)
st.divider()

# תפריט עליון
tab1, tab2 = st.tabs(["💎 הגלריה", "➕ הוספת מטבע (ניהול)"])

# --- טאב ניהול: הוספת מטבעות ---
with tab2:
    st.header("הוספת מטבע חדש לקטלוג")
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("שם המטבע / תיאור:")
        price = st.text_input("מחיר מבוקש (שח):")
        uploaded_files = st.file_uploader("בחר תמונות (ניתן לבחור כמה ביחד):", accept_multiple_files=True, type=['jpg','png','jpeg'])
        submit = st.form_submit_state = st.form_submit_button("פרסם בקטלוג")
        
        if submit and name and uploaded_files:
            image_paths = []
            for f in uploaded_files:
                path = os.path.join("coin_images", f.name)
                with open(path, "wb") as file:
                    file.write(f.getvalue())
                image_paths.append(path)
            
            df = load_data()
            new_id = len(df) + 1
            new_row = {
                "id": new_id,
                "name": name,
                "my_price": price,
                "images": "|".join(image_paths),
                "offers": ""
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success(f"המטבע '{name}' נוסף בהצלחה!")

# --- טאב גלריה: הצגת המטבעות ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג כרגע ריק. הוסף מטבעות בטאב הניהול.")
    else:
        # יצירת גריד של 3 עמודות
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                # הצגת התמונה הראשונה כראשי
                img_list = str(row["images"]).split("|")
                st.image(img_list[0], use_container_width=True)
                st.subheader(row["name"])
                
                if row["my_price"]:
                    st.write(f"**מחיר מבוקש:** {row['my_price']} ש''ח")
                else:
                    st.write("**מחיר:** לא צוין")

                # כפתור פרטים נוספים
                with st.expander("🔍 לצפייה בכל התמונות והצעת מחיר"):
                    # הצגת כל התמונות של המטבע
                    for img_path in img_list:
                        st.image(img_path, use_container_width=True)
                    
                    st.divider()
                    # מערכת הצעות מחיר
                    st.write("💬 הצעת מחיר משלך:")
                    new_offer = st.text_input("הכנס סכום:", key=f"in_{idx}")
                    if st.button("שלח הצעה", key=f"btn_{idx}"):
                        if new_offer:
                            current_offers = str(row["offers"])
                            updated_offers = current_offers + f" | {new_offer}" if current_offers else new_offer
                            df.at[idx, "offers"] = updated_offers
                            save_data(df)
                            st.success("ההצעה נשלחה!")
                
                # אפשרות מחיקה למנהל (מוצג לכולם כרגע כי אין סיסמה)
                if st.button(f"🗑️ מחק מטבע", key=f"del_{idx}"):
                    df = df.drop(idx)
                    save_data(df)
                    st.rerun()

# הצגת הצעות למנהל בתחתית הדף בצורה שקטה
if not df.empty:
    st.divider()
    with st.expander("📩 צפייה בהצעות מחיר שנשלחו (למנהל בלבד)"):
        for idx, row in df.iterrows():
            if row["offers"]:
                st.write(f"**{row['name']}:** {row['offers']}")
