import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import os
from PIL import Image
import io
import time
import base64

# --- הגדרות דף ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

# ניסיון להגדיר Cloudinary בצורה בטוחה
try:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"]
    )
    READY = True
except:
    READY = False

# עיצוב Swipe 1:1
st.markdown("""
<style>
    .scroll-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 5px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-item { flex: 0 0 100%; scroll-snap-align: center; aspect-ratio: 1 / 1; }
    .scroll-item img { width: 100%; height: 100%; object-fit: cover; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# פונקציה להעלאת תמונה לענן
def upload_to_cloud(file):
    img = Image.open(file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    res = cloudinary.uploader.upload(buf.getvalue())
    return res['secure_url']

# טעינה ושמירה (שימוש ב-CSV מקומי כגיבוי אם אין גוגל שיטס)
DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ממשק משתמש ---
if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary ב-Secrets. אנא הגדר אותם כדי להעלות תמונות.")
    st.stop()

st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הקטלוג שלי", "➕ הוספה"])

with tab2:
    st.header("הוספת מטבע חדש")
    name = st.text_input("שם המטבע:")
    price = st.text_input("מחיר:")
    files = st.file_uploader("בחר תמונות מהגלריה:", accept_multiple_files=True)
    
    if st.button("💾 שמור לענן"):
        if name and files:
            with st.spinner('מעלה תמונות לענן...'):
                urls = [upload_to_cloud(f) for f in files]
                df = load_data()
                new_row = {"id": len(df)+1, "name": name, "price": price, "images": "|".join(urls), "comments": ""}
                pd.concat([df, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
                st.success("נשמר בהצלחה!")
                st.rerun()

with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                img_list = str(row["images"]).split("|")
                
                # תצוגת Swipe (אינסטגרם)
                carousel_html = '<div class="scroll-container">'
                for url in img_list:
                    carousel_html += f'<div class="scroll-item"><img src="{url}"></div>'
                carousel_html += '</div>'
                st.markdown(carousel_html, unsafe_allow_html=True)
                
                st.write(f"**{row['name']}**")

                with st.expander("🔍 ניהול ופרטים"):
                    st.write(f"מחיר: {row['price']} ₪")
                    st.write(f"הערות: {row['comments']}")
                    if st.button("🗑️ מחק", key=f"del_{idx}"):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
