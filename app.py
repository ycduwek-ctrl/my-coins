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
