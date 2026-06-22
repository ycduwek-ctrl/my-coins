import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import io

# --- הגדרות עיצוב מתקדמות להשגת המראה ששלחת ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

st.markdown("""
<style>
    /* הגדרות מצלמה ותמונות */
    [data-testid="stCameraInput"] video { aspect-ratio: 1 / 1; object-fit: cover; border-radius: 15px; }
    .stImage > img { aspect-ratio: 1 / 1; object-fit: cover; border-radius: 10px; }
    
    /* עיצוב שורת הניהול כמו בתמונה */
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
        gap: 5px;
    }
    
    /* שדה שם - רקע אפור */
    div[data-testid="stTextInput"]:has(input[aria-label="name_field"]) input {
        background-color: #f1f3f4;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
    }
    
    /* שדה מחיר - רקע ירוק בהיר */
    div[data-testid="stTextInput"]:has(input[aria-label="price_field"]) input {
        background-color: #e8f5e9;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        color: #2e7d32;
    }
    
    /* עיצוב ה-Expander (ניהול ותמונות) */
    .stExpander {
        border: 1px solid #ddd !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# פונקציית חיתוך לריבוע
def crop_to_square(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    s = min(w, h)
    l, t = (w-s)/2, (h-s)/2
    return img.crop((l, t, l+s, t+s))

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
            p = f"temp_{int(time.time()*1000)}.jpg"
            sq_img.save(p)
            st.session_state.temp_list.append(p)
            st.toast("נוסף!")
    if st.session_state.temp_list:
        cols = st.columns(5)
        for i, p in enumerate(st.session_state.temp_list):
            cols[i % 5].image(p, width=70)
        if st.button("💾 שמור הכל", use_container_width=True):
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
                if os.path.exists(img_list[0]):
                    st.image(img_list[0], use_container_width=True)
                
                # --- שורת הניהול המעוצבת לפי התמונה שלך ---
                # חלוקת השורה לעמודות צפופות
                c1, c2, c3, c4 = st.columns([1.8, 0.6, 1.2, 1.4])
                
                with c4: # שם המטבע (ימין)
                    new_n = st.text_input("שם:", value=row["name"], key=f"n_{idx}", label_visibility="visible", aria_label="name_field")
                
                with c3: # מחיר (מרכז-ימין)
                    new_p = st.text_input("₪", value=row["price"], key=f"p_{idx}", label_visibility="visible", aria_label="price_field")
                
                with c2: # כפתור שמירה (מרכז-שמאל)
                    st.write("") # מרווח גובה
                    st.write("")
                    if st.button("💾", key=f"sv_{idx}"):
                        df.at[idx, "name"], df.at[idx, "price"] = new_n, new_p
                        save_data(df)
                        st.toast("עודכן!")

                with c1: # כפתור ניהול (שמאל)
                    with st.expander("🔍 תמונות וניהול"):
                        st.write("תמונות נוספות:")
                        keep_imgs = []
                        for i, p in enumerate(img_list):
                            if os.path.exists(p):
                                im_c, del_c = st.columns([4, 1])
                                im_c.image(p, use_container_width=True)
                                if not del_c.button("🗑️", key=f"dim_{idx}_{i}"):
                                    keep_imgs.append(p)
                        
                        # הוספת תמונה חדשה למטבע קיים
                        new_shot = st.camera_input("הוסף תמונה:", key=f"cam_add_{idx}")
                        if new_shot:
                            if st.button("➕ הוסף", key=f"btn_add_{idx}"):
                                sq = crop_to_square(new_shot.getvalue())
                                n_p = os.path.join(IMG_DIR, f"extra_{int(time.time())}.jpg")
                                sq.save(n_p)
                                keep_imgs.append(n_p)
                                df.at[idx, "images"] = "|".join(keep_imgs)
                                save_data(df)
                                st.rerun()

                        if len(keep_imgs) != len(img_list):
                            df.at[idx, "images"] = "|".join(keep_imgs)
                            save_data(df)
                            st.rerun()

                        if st.button("❌ מחק הכל", key=f"full_del_{idx}", use_container_width=True):
                            df.drop(idx).to_csv(DB_FILE, index=False)
                            st.rerun()
