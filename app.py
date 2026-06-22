import streamlit as st
import pandas as pd
import os
from PIL import Image
import io

# --- הגדרות עיצוב מתקדמות ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

st.markdown("""
<style>
    /* הפיכת תמונות לריבוע 1:1 עם איכות גבוהה */
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 12px;
    }
    /* מירכוז אנכי של חצים בצידי התמונה */
    [data-testid="column"] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    /* עיצוב כפתורי איקונים */
    .stButton button {
        background-color: transparent !important;
        border: none !important;
        font-size: 25px !important;
    }
    /* ביטול מרווח עליון */
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# יצירת תיקייה
if not os.path.exists("coin_images"):
    os.makedirs("coin_images")

DB_FILE = 'catalog_data.csv'

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "my_price", "images"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# אתחול Session State
if "img_indices" not in st.session_state: st.session_state.img_indices = {}

# --- ממשק משתמש ---
st.title("🪙 קטלוג מטבעות")

tab1, tab2 = st.tabs(["💎 גלריה", "➕ הוספה"])

# --- טאב הוספה (איכות גבוהה) ---
with tab2:
    st.header("הוספת פריט")
    name = st.text_input("שם המטבע", placeholder="תיאור קצר...")
    price = st.text_input("מחיר", placeholder="מחיר בשח")
    
    # שימוש ב-file_uploader עבור איכות מצלמה מקסימלית במובייל
    up_files = st.file_uploader("📸 צלם או בחר תמונות (איכות גבוהה)", 
                                accept_multiple_files=True, 
                                type=['jpg','png','jpeg'])
    
    if st.button("💾 שמור הכל", use_container_width=True):
        if name and up_files:
            saved_paths = []
            for f in up_files:
                path = os.path.join("coin_images", f"{name}_{f.name}")
                with open(path, "wb") as file:
                    file.write(f.getvalue())
                saved_paths.append(path)
            
            df = load_data()
            new_row = {"id": len(df)+1, "name": name, "my_price": price, "images": "|".join(saved_paths)}
            save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("המטבע נוסף בהצלחה!")
            st.rerun()
        else:
            st.error("חובה להזין שם ולהעלות לפחות תמונה אחת.")

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        for idx, row in df.iterrows():
            with st.container(border=True):
                img_list = str(row["images"]).split("|")
                coin_id = str(row["id"])
                
                if coin_id not in st.session_state.img_indices:
                    st.session_state.img_indices[coin_id] = 0
                
                curr = st.session_state.img_indices[coin_id]

                # --- קרוסלה עם חצים במרכז הגובה ---
                col_left, col_mid, col_right = st.columns([1, 6, 1])
                
                with col_left:
                    if st.button("⬅️", key=f"p_{idx}"):
                        st.session_state.img_indices[coin_id] = (curr - 1) % len(img_list)
                        st.rerun()
                
                with col_mid:
                    st.image(img_list[curr], use_container_width=True)
                
                with col_right:
                    if st.button("➡️", key=f"n_{idx}"):
                        st.session_state.img_indices[coin_id] = (curr + 1) % len(img_list)
                        st.rerun()

                # שורת מידע ואיקונים
                info_c, edit_c = st.columns([4, 1])
                info_c.subheader(f"{row['name']} | 💰 {row['my_price']} ₪")
                
                edit_mode = edit_c.toggle("✏️", key=f"ed_tgl_{idx}")

                if edit_mode:
                    new_n = st.text_input("שם פריט", value=row["name"], key=f"nm_{idx}")
                    new_p = st.text_input("מחיר פריט", value=row["my_price"], key=f"pr_{idx}")
                    
                    st.write("ניהול תמונות:")
                    keep_imgs = []
                    for i, img_p in enumerate(img_list):
                        img_col, del_col = st.columns([4, 1])
                        img_col.image(img_p, width=80)
                        if not del_col.button("🗑️", key=f"di_{idx}_{i}"):
                            keep_imgs.append(img_p)
                    
                    # הוספת תמונות נוספות למטבע קיים
                    more_files = st.file_uploader("➕ הוסף תמונות", accept_multiple_files=True, key=f"af_{idx}")
                    
                    if st.button("💾 שמור שינויים", key=f"sv_{idx}"):
                        if more_files:
                            for f in more_files:
                                p = os.path.join("coin_images", f.name)
                                with open(p, "wb") as file: file.write(f.getvalue())
                                keep_imgs.append(p)
                        
                        df.at[idx, "name"] = new_n
                        df.at[idx, "my_price"] = new_p
                        df.at[idx, "images"] = "|".join(keep_imgs)
                        save_data(df)
                        st.rerun()
                    
                    if st.button("🗑️ מחק הכל", key=f"full_d_{idx}"):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
