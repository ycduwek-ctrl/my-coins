import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import io

# --- הגדרות עיצוב ---
st.set_page_config(page_title="Coin Catalog", layout="wide")

st.markdown("""
<style>
    /* תמונות ריבועיות 1:1 */
    [data-testid="stCameraInput"] video { aspect-ratio: 1 / 1; object-fit: cover; border-radius: 15px; }
    .stImage > img { aspect-ratio: 1 / 1; object-fit: cover; border-radius: 10px; }
    
    /* עיצוב כותרות מעל התמונה */
    .coin-label {
        font-size: 14px;
        font-weight: bold;
        margin-bottom: -10px;
        color: #555;
    }
    
    /* עיצוב שדות הטקסט של השם והמחיר */
    div[data-testid="stTextInput"] input {
        border-radius: 8px !important;
        margin-bottom: 5px;
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
    st.header("הוספת פריט חדש")
    coin_name = st.text_input("שם המטבע:", key="main_input_name")
    coin_price = st.text_input("מחיר (₪):", key="main_input_price")
    cam_shot = st.camera_input("צלם צד של המטבע")
    
    if cam_shot:
        if st.button("➕ הוסף תמונה זו"):
            sq_img = crop_to_square(cam_shot.getvalue())
            p = f"temp_{int(time.time()*1000)}.jpg"
            sq_img.save(p)
            st.session_state.temp_list.append(p)
            st.toast("תמונה נוספה לרשימה")

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
                st.success("נשמר בהצלחה!")
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
                # --- מידע מעל התמונה ---
                st.markdown(f'<p class="coin-label">שם:</p>', unsafe_allow_html=True)
                new_n = st.text_input("", value=str(row["name"]), key=f"n_{idx}")
                
                st.markdown(f'<p class="coin-label">מחיר:</p>', unsafe_allow_html=True)
                c_price, c_save = st.columns([3, 1])
                new_p = c_price.text_input("", value=str(row["price"]), key=f"p_{idx}")
                if c_save.button("💾", key=f"sv_{idx}"):
                    df.at[idx, "name"], df.at[idx, "price"] = new_n, new_p
                    save_data(df)
                    st.toast("הפרטים עודכנו!")

                # --- התמונה ---
                img_list = str(row["images"]).split("|")
                if os.path.exists(img_list[0]):
                    st.image(img_list[0], use_container_width=True)
                
                # --- כפתור נפתח מתחת לתמונה ---
                with st.expander("🔍 תמונות נוספות וניהול"):
                    st.write("גלריית תמונות:")
                    keep_imgs = []
                    for i, p in enumerate(img_list):
                        if os.path.exists(p):
                            im_c, del_c = st.columns([4, 1])
                            im_c.image(p, use_container_width=True)
                            if del_c.button("🗑️", key=f"dim_{idx}_{i}"):
                                pass # לא מוסיפים ל-keep_imgs
                            else:
                                keep_imgs.append(p)
                    
                    if len(keep_imgs) != len(img_list):
                        df.at[idx, "images"] = "|".join(keep_imgs)
                        save_data(df)
                        st.rerun()

                    st.divider()
                    add_shot = st.camera_input("הוסף תמונה חדשה:", key=f"cam_add_{idx}")
                    if add_shot:
                        if st.button("✅ הוסף תמונה", key=f"btn_add_{idx}"):
                            sq = crop_to_square(add_shot.getvalue())
                            n_p = os.path.join(IMG_DIR, f"extra_{int(time.time())}.jpg")
                            sq.save(n_p)
                            keep_imgs.append(n_p)
                            df.at[idx, "images"] = "|".join(keep_imgs)
                            save_data(df)
                            st.rerun()

                    st.divider()
                    if st.button("❌ מחק את כל הפריט", key=f"full_del_{idx}", use_container_width=True):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
