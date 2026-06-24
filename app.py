import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import os
from PIL import Image
import io
import time

# --- הגדרות דף ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

# הגדרת Cloudinary
try:
    cloudinary.config(
        cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key = st.secrets["CLOUDINARY_API_KEY"],
        api_secret = st.secrets["CLOUDINARY_API_SECRET"]
    )
    READY = True
except:
    READY = False

# עיצוב CSS כולל כרטיס הפלוס החדש
st.markdown("""
<style>
    .carousel-wrapper {
        position: relative;
        width: 100%;
        aspect-ratio: 1 / 1;
        overflow: hidden;
        border-radius: 12px;
    }
    .scroll-container {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        scroll-behavior: smooth;
        gap: 0px;
        scrollbar-width: none;
        width: 100%;
        height: 100%;
    }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-item {
        flex: 0 0 100%;
        scroll-snap-align: center;
        aspect-ratio: 1 / 1;
    }
    .scroll-item img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .nav-arrow {
        position: absolute;
        top: 0; bottom: 0; width: 45px;
        background: rgba(0, 0, 0, 0.1);
        color: white; border: none;
        display: flex; align-items: center; justify-content: center;
        font-size: 35px; cursor: pointer; z-index: 5;
    }
    .nav-arrow:hover { background: rgba(0, 0, 0, 0.4); }
    .prev-arrow { left: 0; }
    .next-arrow { right: 0; }

    /* עיצוב כפתור הפלוס שייראה כמו כרטיס מטבע */
    .stPopover { width: 100%; }
    .stPopover > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        border-radius: 12px !important;
        border: 2px dashed #ccc !important;
        background-color: #fafafa !important;
        color: #999 !important;
        font-size: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s !important;
    }
    .stPopover > button:hover {
        border-color: #4CAF50 !important;
        color: #4CAF50 !important;
        background-color: #f0fdf0 !important;
    }
</style>
""", unsafe_allow_html=True)

def upload_to_cloud(file):
    img = Image.open(file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    res = cloudinary.uploader.upload(buf.getvalue())
    return res['secure_url']

DB_FILE = 'final_coins_db.csv'
def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE, dtype=str)
        except: pass
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ממשק משתמש ---
if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary.")
    st.stop()

df = load_data()

st.sidebar.title("🖼️ תצוגה")
view_mode = st.sidebar.radio("סגנון:", ["גלריה", "רשימה מפורטת"])
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

st.sidebar.divider()
if not df.empty:
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 הורד גיבוי (CSV)", csv_data, f"coins_backup.csv"
