import streamlit as st
import pandas as pd
import os
from PIL import Image
import io

# --- הגדרות עיצוב ---
st.set_page_config(page_title="Coin Catalog", layout="wide")

st.markdown("""
<style>
    /* פורמט 1:1 לכל התמונות */
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 15px;
    }
    /* ביטול מרווחים מיותרים */
    .block-container { padding-top: 2rem; }
    /* כפתורי איקונים גדולים */
    .stButton button {
        border-radius: 50px;
        padding: 5px 15px;
    }
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
if "temp_photos" not in st.session_state: st.session_state.temp_photos = []

# --- ממשק משתמש ---
st.title("🪙 קטלוג מטבעות")

tab1, tab2 = st.tabs(["💎 גלריה", "➕ הוספה"])

# --- טאב הוספה (צילום רציף) ---
with tab2:
    col_a, col_b = st.columns([2, 1])
    with col_a:
        name = st.text_input("שם הפריט", placeholder="למשל: שקל עתיק 1980")
        price = st.text_input("מחיר", placeholder="מחיר בשח")
    
    # מצלמה
    cam_photo = st.camera_input("📷 צלם תמונה")
    if cam_photo:
        # הוספה לרשימה זמנית רק אם היא לא שם
        img_bytes = cam_photo.getvalue()
        if img_bytes not in [p['bytes'] for p in st.session_state.temp_photos]:
            st.session_state.temp_photos.append({'bytes': img_bytes, 'name': f"cam_{len(st.session_state.temp_photos)}.jpg"})
            st.success(f"תמונה {len(st.session_state.temp_photos)} נוספה לרשימה")

    # הצגת התמונות שצולמו לפני שמירה
    if st.session_state.temp_photos:
        st.write("תמונות שצולמו:")
        cols = st.columns(4)
        for i, p in enumerate(st.session_state.temp_photos):
            with cols[i % 4]:
                st.image(p['bytes'], width=80)
        
        if st.button("💾 שמור הכל לקטלוג"):
            saved_paths = []
            for p in st.session_state.temp_photos:
                path = os.path.join("coin_images", f"{name}_{p['name']}")
                with open(path, "wb") as f: f.write(p['bytes'])
                saved_paths.append(path)
            
            df = load_data()
            new_row = {"id": len(df)+1, "name": name, "my_price": price, "images": "|".join(saved_paths)}
            save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.session_state.temp_photos = [] # איפוס
            st.success("נשמר!")
            st.rerun()

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

                # --- תצוגת קרוסלה עם חצים על התמונה (באמצעות Columns) ---
                c_prev, c_img, c_next = st.columns([1, 6, 1])
                
                with c_prev:
                    st.write(" ") # מרווח
                    st.write(" ")
                    if st.button("⬅️", key=f"p_{idx}"):
                        st.session_state.img_indices[coin_id] = (curr - 1) % len(img_list)
                        st.rerun()
                
                with c_img:
                    st.image(img_list[curr], use_container_width=True)
                
                with c_next:
                    st.write(" ")
                    st.write(" ")
                    if st.button("➡️", key=f"n_{idx}"):
                        st.session_state.img_indices[coin_id] = (curr + 1) % len(img_list)
                        st.rerun()

                # פרטים ואיקוני ניהול
                col_info, col_actions = st.columns([4, 1])
                with col_info:
                    st.write(f"**{row['name']}** | 💰 {row['my_price']} ₪")
                
                with col_actions:
                    edit_mode = st.toggle("✏️", key=f"edit_tgl_{idx}")

                if edit_mode:
                    new_n = st.text_input("שם", value=row["name"], key=f"name_{idx}")
                    new_p = st.text_input("מחיר", value=row["my_price"], key=f"price_{idx}")
                    
                    # מחיקת תמונות ספציפיות
                    keep_imgs = []
                    for i, img_p in enumerate(img_list):
                        col_i, col_d = st.columns([4, 1])
                        col_i.image(img_p, width=50)
                        if not col_d.button("🗑️", key=f"del_img_{idx}_{i}"):
                            keep_imgs.append(img_p)
                    
                    if st.button("💾", key=f"save_btn_{idx}"):
                        df.at[idx, "name"] = new_n
                        df.at[idx, "my_price"] = new_p
                        df.at[idx, "images"] = "|".join(keep_imgs)
                        save_data(df)
                        st.rerun()
                    
                    if st.button("🗑️ מחק מטבע", key=f"full_del_{idx}"):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
