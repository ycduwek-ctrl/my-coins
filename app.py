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

# עיצוב Swipe 1:1 נקי
st.markdown("""
<style>
    .scroll-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 5px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-item { flex: 0 0 100%; scroll-snap-align: center; aspect-ratio: 1 / 1; }
    .scroll-item img { width: 100%; height: 100%; object-fit: cover; border-radius: 12px; }
    .stExpander { border: 1px solid #eee !important; border-radius: 10px !important; margin-top: 5px; }
</style>
""", unsafe_allow_html=True)

def upload_to_cloud(file):
    img = Image.open(file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    res = cloudinary.uploader.upload(buf.getvalue())
    return res['secure_url']

DB_FILE = 'catalog_data.csv'

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['id'] = df['id'].astype(str)
            return df
        except:
            pass
    return p
