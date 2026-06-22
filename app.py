import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import base64
import io

# --- הגדרות עיצוב לקרוסלה וגלילה ---
st.set_page_config(page_title="Coin Catalog Swipe", layout="wide")

def get_image_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

st.markdown("""
<style>
    /* עיצוב הקרוסלה - מאפשר גלילה באצבע (Swipe) */
    .scroll-container {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        gap: 5px;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none; /* מסתיר סרגל גלילה */
    }
    .scroll-container::-webkit-scrollbar { display: none; }
    
    .scroll-item {
        flex: 0 0 100%; /* כל תמונה תופסת 100% מהרוחב */
        scroll-snap-align: center;
        aspect-ratio: 1 / 1;
    }
    .scroll-item img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# פונקציות בסיס
IMG_DIR = "coin_images"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)
DB_FILE = 'catalog_data.csv'

def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "price", "images"])

def save_data(df): df.to_csv(DB_FILE, index=False)

def process_image(uploaded_file):
    img = Image.open(uploaded_file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    l, t = (w-s)/2, (h-s)/2
    return img.crop((l, t, l+s, t+s))

# --- תפריט צד ---
st.sidebar.title("🖼️ תצוגה")
view_mode = st.sidebar.radio("סגנון:", ["גלריה", "רשימה"])
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הקטלוג", "➕ הוספה"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת מטבע")
    c_name = st.text_input("שם:", key="add_n")
    c_price = st.text_input("מחיר:", key="add_p")
    up_files = st.file_uploader("בחר תמונות:", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    
    if st.button("💾 שמור", use_container_width=True):
        if c_name and up_files:
            paths = []
            for f in up_files:
                sq = process_image(f)
                p = os.path.join(IMG_DIR, f"coin_{int(time.time()*1000)}_{f.name}")
                sq.save(p)
                paths.append(p)
            df = load_data()
            new = {"id": len(df)+1, "name": c_name, "price": c_price, "images": "|".join(paths)}
            save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
            st.success("נוסף!")
            st.rerun()

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        if view_mode == "גלריה":
            cols = st.columns(grid_size)
            for idx, row in df.iterrows():
                with cols[idx % grid_size]:
                    img_list = str(row["images"]).split("|")
                    
                    # --- יצירת הקרוסלה ב-HTML כדי לאפשר Swipe ---
                    carousel_html = '<div class="scroll-container">'
                    for img_p in img_list:
                        if os.path.exists(img_p):
                            base64_img = get_image_base64(img_p)
                            carousel_html += f'<div class="scroll-item"><img src="data:image/jpeg;base64,{base64_img}"></div>'
                    carousel_html += '</div>'
                    st.markdown(carousel_html, unsafe_allow_html=True)
                    
                    # חלונית ניהול
                    with st.expander("🔍 פרטים וניהול"):
                        en = st.text_input("שם:", value=str(row["name"]), key=f"en_{idx}")
                        ep = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{idx}")
                        if st.button("💾 שמור שינויים", key=f"sv_{idx}"):
                            df.at[idx, "name"], df.at[idx, "price"] = en, ep
                            save_data(df)
                            st.rerun()
                        
                        st.divider()
                        st.write("מחיקת תמונות:")
                        keep = []
                        for i, p in enumerate(img_list):
                            if os.path.exists(p):
                                c1, c2 = st.columns([4, 1])
                                c1.image(p, width=60)
                                if not c2.button("🗑️", key=f"di_{idx}_{i}"): keep.append(p)
                        
                        if len(keep) != len(img_list):
                            df.at[idx, "images"] = "|".join(keep)
                            save_data(df)
                            st.rerun()

                        if st.button("❌ מחק הכל", key=f"del_{idx}", use_container_width=True):
                            df.drop(idx).to_csv(DB_FILE, index=False)
                            st.rerun()
        else:
            for idx, row in df.iterrows():
                st.write(f"**{row['name']}** | {row['price']} ₪")
