import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import io

# --- הגדרות עיצוב אינסטגרם ---
st.set_page_config(page_title="Coin Gallery", layout="wide")

st.markdown("""
<style>
    /* הפיכת תצוגת המצלמה לריבועית */
    [data-testid="stCameraInput"] video {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 15px;
    }
    /* תמונות הגלריה בריבוע */
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    div[data-testid="stExpander"] { border: none !important; }
</style>
""", unsafe_allow_html=True)

# פונקציה לחיתוך תמונה לריבוע מושלם 1:1
def crop_to_square(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    new_size = min(width, height)
    left = (width - new_size) / 2
    top = (height - new_size) / 2
    right = (width + new_size) / 2
    bottom = (height + new_size) / 2
    img = img.crop((left, top, right, bottom))
    return img

IMG_DIR = "coin_images"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if 'my_price' in df.columns: df.rename(columns={'my_price': 'price'}, inplace=True)
        return df
    return pd.DataFrame(columns=["id", "name", "price", "images"])

def save_data(df): df.to_csv(DB_FILE, index=False)

# ניהול רשימת תמונות זמנית לצילום רציף
if 'temp_list' not in st.session_state: st.session_state.temp_list = []

st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הגלריה", "📸 הוספת מטבע"])

# --- טאב הוספה (מצלמה ריבועית) ---
with tab2:
    st.header("צילום פריט חדש")
    
    coin_name = st.text_input("שם המטבע")
    coin_price = st.text_input("מחיר (₪)")
    
    # מצלמת הממשק - נסה לבקש מצלמה אחורית
    cam_shot = st.camera_input("צלם צד של המטבע", label_visibility="visible")
    
    if cam_shot:
        if st.button("➕ הוסף תמונה זו לרשימה"):
            squared_img = crop_to_square(cam_shot.getvalue())
            timestamp = int(time.time() * 1000)
            temp_path = f"temp_{timestamp}.jpg"
            squared_img.save(temp_path)
            st.session_state.temp_list.append(temp_path)
            st.toast("התמונה נוספה!")

    if st.session_state.temp_list:
        st.write("תמונות שצולמו:")
        t_cols = st.columns(5)
        for i, p in enumerate(st.session_state.temp_list):
            t_cols[i % 5].image(p, width=70)
        
        if st.button("💾 שמור הכל לקטלוג", use_container_width=True):
            if coin_name:
                final_paths = []
                for p in st.session_state.temp_list:
                    final_p = os.path.join(IMG_DIR, p.replace("temp_", f"{coin_name}_"))
                    os.rename(p, final_p)
                    final_paths.append(final_p)
                
                df = load_data()
                new_entry = {"id": len(df)+1, "name": coin_name, "price": coin_price, "images": "|".join(final_paths)}
                save_data(pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True))
                st.session_state.temp_list = [] # איפוס
                st.success("נשמר!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("נא להזין שם למטבע")

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                img_list = str(row["images"]).split("|")
                if os.path.exists(img_list[0]):
                    st.image(img_list[0], use_container_width=True)
                
                with st.expander(f"🔍 {row['name']}"):
                    st.write(f"**מחיר:** {row['price']} ₪")
                    for p in img_list:
                        if os.path.exists(p): st.image(p, use_container_width=True)
                    
                    st.divider()
                    if st.toggle("✏️", key=f"tgl_{idx}"):
                        new_n = st.text_input("שם", value=row["name"], key=f"n_{idx}")
                        new_p = st.text_input("מחיר", value=row["price"], key=f"p_{idx}")
                        if st.button("💾", key=f"sv_{idx}"):
                            df.at[idx, "name"], df.at[idx, "price"] = new_n, new_p
                            save_data(df)
                            st.rerun()
                        if st.button("🗑️", key=f"del_{idx}"):
                            df.drop(idx).to_csv(DB_FILE, index=False)
                            st.rerun()
