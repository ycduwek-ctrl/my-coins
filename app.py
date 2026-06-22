import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import io

# --- הגדרות עיצוב ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

st.markdown("""
<style>
    [data-testid="stCameraInput"] video {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 15px;
    }
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 10px;
    }
    /* צמצום מרווחים לעריכה מהירה */
    .stTextInput { margin-top: -15px; }
    div[data-testid="stExpander"] { border: 1px solid #eee !important; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# פונקציית חיתוך לריבוע
def crop_to_square(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    new_size = min(width, height)
    left, top = (width - new_size) / 2, (height - new_size) / 2
    right, bottom = (width + new_size) / 2, (height + new_size) / 2
    return img.crop((left, top, right, bottom))

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

if 'temp_list' not in st.session_state: st.session_state.temp_list = []
if 'img_indices' not in st.session_state: st.session_state.img_indices = {}

st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הגלריה", "📸 הוספת מטבע"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת פריט")
    coin_name = st.text_input("שם המטבע")
    coin_price = st.text_input("מחיר (₪)")
    cam_shot = st.camera_input("צלם צד של המטבע")
    
    if cam_shot:
        if st.button("➕ הוסף תמונה זו"):
            sq_img = crop_to_square(cam_shot.getvalue())
            path = f"temp_{int(time.time()*1000)}.jpg"
            sq_img.save(path)
            st.session_state.temp_list.append(path)
            st.toast("נוסף!")

    if st.session_state.temp_list:
        cols = st.columns(5)
        for i, p in enumerate(st.session_state.temp_list):
            cols[i % 5].image(p, width=70)
        if st.button("💾 שמור הכל לקטלוג", use_container_width=True):
            if coin_name:
                final_paths = []
                for p in st.session_state.temp_list:
                    f_p = os.path.join(IMG_DIR, p.replace("temp_", f"{coin_name}_"))
                    os.rename(p, f_p)
                    final_paths.append(f_p)
                df = load_data()
                new_row = {"id": len(df)+1, "name": coin_name, "price": coin_price, "images": "|".join(final_paths)}
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.session_state.temp_list = []
                st.success("נשמר!")
                st.rerun()

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
                coin_id = str(row["id"])
                
                # תצוגה ראשית
                if os.path.exists(img_list[0]):
                    st.image(img_list[0], use_container_width=True)
                
                # --- עריכה מהירה (שם ומחיר מחוץ לחלונית) ---
                new_n = st.text_input("שם", value=row["name"], key=f"n_{idx}", label_visibility="collapsed")
                c_pr, c_sv = st.columns([3, 1])
                new_p = c_pr.text_input("מחיר", value=row["price"], key=f"p_{idx}", label_visibility="collapsed")
                if c_sv.button("💾", key=f"sv_{idx}"):
                    df.at[idx, "name"], df.at[idx, "price"] = new_n, new_p
                    save_data(df)
                    st.toast("הפרטים עודכנו!")

                # --- חלונית פרטים נוספים וניהול תמונות ---
                with st.expander("🔍 תמונות וניהול"):
                    st.write("תמונות נוספות:")
                    keep_imgs = []
                    for i, p in enumerate(img_list):
                        if os.path.exists(p):
                            im_c, del_c = st.columns([4, 1])
                            im_c.image(p, use_container_width=True)
                            if not del_c.button("🗑️", key=f"dim_{idx}_{i}"):
                                keep_imgs.append(p)
                    
                    # אפשרות הוספת תמונות חדשות למטבע קיים
                    new_shots = st.camera_input("הוסף תמונה חדשה:", key=f"cam_add_{idx}")
                    if new_shots:
                        if st.button("➕ הוסף", key=f"btn_add_{idx}"):
                            sq = crop_to_square(new_shots.getvalue())
                            new_p = os.path.join(IMG_DIR, f"extra_{int(time.time())}.jpg")
                            sq.save(new_p)
                            keep_imgs.append(new_p)
                            df.at[idx, "images"] = "|".join(keep_imgs)
                            save_data(df)
                            st.rerun()

                    if len(keep_imgs) != len(img_list): # אם נמחקה תמונה
                        df.at[idx, "images"] = "|".join(keep_imgs)
                        save_data(df)
                        st.rerun()

                    st.divider()
                    if st.button("❌ מחק הכל", key=f"full_del_{idx}", use_container_width=True):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
