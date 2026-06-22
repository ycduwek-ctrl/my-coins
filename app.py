import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import io

# --- הגדרות עיצוב להשגת המראה המדויק מהתמונה ---
st.set_page_config(page_title="Coin Catalog", layout="wide")

st.markdown("""
<style>
    /* הגדרת כיוון כללית לימין */
    .main { direction: rtl; }
    
    /* עיצוב תיבות הטקסט (שם ומחיר) */
    div[data-testid="stTextInput"] input {
        background-color: #f1f3f4 !important;
        border-radius: 10px !important;
        border: none !important;
        text-align: right !important;
        padding: 10px !important;
        font-size: 16px !important;
    }
    
    /* עיצוב התגיות (Labels) של התיבות */
    div[data-testid="stTextInput"] label {
        direction: rtl;
        text-align: right;
        width: 100%;
        margin-bottom: 2px;
        color: #333;
    }

    /* עיצוב התמונה - ריבוע מושלם 1:1 */
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 10px;
        margin-top: 5px;
    }

    /* עיצוב כפתור השמירה (💾) */
    div.stButton > button {
        border-radius: 8px !important;
        border: 1px solid #ddd !important;
        background-color: white !important;
        float: right;
    }

    /* עיצוב הכפתור הנפתח (Expander) */
    .stExpander {
        border-radius: 10px !important;
        border: 1px solid #ddd !important;
        background-color: white !important;
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
        return df
    return pd.DataFrame(columns=["id", "name", "price", "images"])

def save_data(df): df.to_csv(DB_FILE, index=False)

if 'temp_list' not in st.session_state: st.session_state.temp_list = []

tab1, tab2 = st.tabs(["💎 הגלריה", "📸 הוספת מטבע"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת מטבע חדש")
    c_name = st.text_input("שם המטבע:", key="add_n")
    c_price = st.text_input("מחיר (₪):", key="add_p")
    cam = st.camera_input("צלם תמונה")
    if cam:
        if st.button("➕ הוסף תמונה"):
            sq = crop_to_square(cam.getvalue())
            p = f"temp_{int(time.time()*1000)}.jpg"
            sq.save(p)
            st.session_state.temp_list.append(p)
    
    if st.session_state.temp_list:
        cols = st.columns(5)
        for i, p in enumerate(st.session_state.temp_list):
            cols[i%5].image(p, width=70)
        if st.button("💾 שמור הכל", use_container_width=True):
            final_p = []
            for p in st.session_state.temp_list:
                f_p = os.path.join(IMG_DIR, p.replace("temp_", "coin_"))
                os.rename(p, f_p)
                final_p.append(f_p)
            df = load_data()
            new = {"id": len(df)+1, "name": c_name, "price": c_price, "images": "|".join(final_p)}
            save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
            st.session_state.temp_list = []
            st.rerun()

# --- טאב גלריה (העיצוב מהתמונה) ---
with tab1:
    df = load_data()
    # בורר תצוגה צדדי
    grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)
    
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                # 1. שדה שם
                new_n = st.text_input("שם:", value=str(row["name"]), key=f"n_{idx}")
                
                # 2. שדה מחיר
                new_p = st.text_input("מחיר:", value=str(row["price"]), key=f"p_{idx}")
                
                # 3. כפתור שמירה (מיושר לימין)
                c_empty, c_save = st.columns([4, 1])
                if c_save.button("💾", key=f"sv_{idx}"):
                    df.at[idx, "name"], df.at[idx, "price"] = new_n, new_p
                    save_data(df)
                    st.toast("נשמר!")

                # 4. התמונה הריבועית
                img_list = str(row["images"]).split("|")
                if os.path.exists(img_list[0]):
                    st.image(img_list[0], use_container_width=True)
                
                # 5. הכפתור הנפתח
                with st.expander("🔍 תמונות נוספות וניהול"):
                    for p in img_list:
                        if os.path.exists(p):
                            im_c, del_c = st.columns([4, 1])
                            im_c.image(p, use_container_width=True)
                            if del_c.button("🗑️", key=f"di_{idx}_{p}"):
                                # הסרת תמונה מהרשימה
                                new_list = [img for img in img_list if img != p]
                                df.at[idx, "images"] = "|".join(new_list)
                                save_data(df)
                                st.rerun()
                    
                    st.divider()
                    if st.button("❌ מחק פריט", key=f"del_{idx}", use_container_width=True):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
