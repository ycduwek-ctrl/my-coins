import streamlit as st
import pandas as pd
import os
from PIL import Image

# --- הגדרות דף ---
st.set_page_config(page_title="Coin Gallery 1:1", layout="wide")

# עיצוב CSS לקרוסלה ופורמט 1:1
st.markdown("""
<style>
    .carousel-container {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        gap: 10px;
        padding-bottom: 10px;
        scrollbar-width: thin;
    }
    .carousel-item {
        flex: 0 0 100%;
        scroll-snap-align: start;
        aspect-ratio: 1 / 1;
        overflow: hidden;
        border-radius: 10px;
    }
    .carousel-item img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        cursor: zoom-in;
    }
    /* עיצוב חצים למחשב */
    .carousel-container::-webkit-scrollbar {
        height: 6px;
    }
    .carousel-container::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# יצירת תיקיית תמונות
if not os.path.exists("coin_images"):
    os.makedirs("coin_images")

DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "my_price", "images", "offers"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ממשק משתמש ---
st.title("🪙 קטלוג המטבעות שלי")

tab1, tab2 = st.tabs(["💎 גלריית המטבעות", "➕ הוספת מטבע חדש"])

# --- טאב 2: הוספה ---
with tab2:
    st.header("ניהול קטלוג")
    with st.form("upload_form", clear_on_submit=True):
        name = st.text_input("שם המטבע:")
        price = st.text_input("מחיר מבוקש (ש''ח):")
        files = st.file_uploader("העלה את כל תמונות המטבע:", accept_multiple_files=True, type=['jpg','png','jpeg'])
        submit = st.form_submit_button("הוסף לקטלוג")
        
        if submit and name and files:
            paths = []
            for f in files:
                f_path = os.path.join("coin_images", f"{name}_{f.name}")
                with open(f_path, "wb") as file:
                    file.write(f.getvalue())
                paths.append(f_path)
            
            df = load_data()
            new_row = {"id": len(df)+1, "name": name, "my_price": price, "images": "|".join(paths), "offers": ""}
            pd.concat([df, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
            st.success("המטבע נוסף!")

# --- טאב 1: גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.write("אין מטבעות בקטלוג.")
    else:
        # הצגת המטבעות בגריד
        grid_cols = st.columns(2 if st.sidebar.checkbox("תצוגה צפופה (2 בטור)", False) else 3)
        
        for idx, row in df.iterrows():
            with grid_cols[idx % len(grid_cols)]:
                img_list = str(row["images"]).split("|")
                
                # כרטיס המטבע
                with st.container(border=True):
                    # הצגת התמונה הראשית (1:1)
                    st.image(img_list[0], use_container_width=True)
                    st.subheader(row["name"])
                    st.write(f"**מחיר:** {row['my_price']} ש''ח")
                    
                    # אזור הקרוסלה והפרטים
                    with st.expander("🔍 צפה בכל התמונות והצע מחיר"):
                        # קרוסלה ב-HTML/CSS
                        carousel_html = '<div class="carousel-container">'
                        for img_p in img_list:
                            # שימוש בנתיב התמונה
                            carousel_html += f'<div class="carousel-item"><img src="file/{img_p}" onclick="window.open(this.src)"></div>'
                        carousel_html += '</div>'
                        
                        # הערה: Streamlit Cloud לא תמיד מאפשר גישה ישירה ל-file/. 
                        # לכן נשתמש בפתרון המובנה של Streamlit לקרוסלה פשוטה:
                        
                        st.write("דפדף בין התמונות:")
                        current_img_idx = st.slider(f"תמונה", 1, len(img_list), 1, key=f"sld_{idx}") - 1
                        st.image(img_list[current_img_idx], use_container_width=True, caption=f"תמונה {current_img_idx+1} מתוך {len(img_list)}")
                        
                        st.divider()
                        # הצעת מחיר
                        offer = st.text_input("הצעה שלך (ש''ח):", key=f"off_{idx}")
                        if st.button("שלח הצעה", key=f"btn_{idx}"):
                            st.toast("ההצעה נשלחה בהצלחה!")

                # כפתור מחיקה (למטה)
                if st.checkbox(f"אפשרות מחיקה #{row['id']}", key=f"chk_{idx}"):
                    if st.button(f"אישור מחיקה {row['id']}", key=f"del_{idx}"):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
