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

# הגדרת Cloudinary מה-Secrets
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

# פונקציה להעלאת תמונה
def upload_to_cloud(file):
    img = Image.open(file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    res = cloudinary.uploader.upload(buf.getvalue())
    return res['secure_url']

# ניהול נתונים - טעינה ושמירה חסינה
DB_FILE = 'catalog_data.csv'

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['id'] = df['id'].astype(str) # תמיד לעבוד עם טקסט ב-ID
            return df
        except:
            pass
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ממשק משתמש ---
if not READY:
    st.error("⚠️ הגדרות Cloudinary חסרות ב-Secrets.")
    st.stop()

st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

tab1, tab2 = st.tabs(["💎 הגלריה שלי", "➕ הוספת מטבע"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת מטבע חדש")
    with st.form("add_form", clear_on_submit=True):
        n_name = st.text_input("שם המטבע:")
        n_price = st.text_input("מחיר (₪):")
        n_files = st.file_uploader("בחר תמונות:", accept_multiple_files=True)
        if st.form_submit_button("🚀 שמור לקטלוג"):
            if n_name and n_files:
                with st.spinner('מעלה...'):
                    urls = [upload_to_cloud(f) for f in n_files]
                    df = load_data()
                    new_id = str(int(time.time()))
                    new_row = pd.DataFrame([{"id": new_id, "name": n_name, "price": n_price, "images": "|".join(urls), "comments": ""}])
                    save_data(pd.concat([df, new_row], ignore_index=True))
                    st.success("נוסף!")
                    time.sleep(1)
                    st.rerun()

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for index, row in df.iterrows():
            coin_id = str(row['id'])
            with cols[index % grid_size]:
                img_list = str(row["images"]).split("|")
                
                # קרוסלת Swipe
                carousel_html = '<div class="scroll-container">'
                for url in img_list:
                    carousel_html += f'<div class="scroll-item"><img src="{url}"></div>'
                carousel_html += '</div>'
                st.markdown(carousel_html, unsafe_allow_html=True)
                
                st.write(f"**{row['name']}**")

                with st.expander("🔍 ניהול ופרטים"):
                    # שדות עריכה
                    e_name = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                    e_price = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                    e_comm = st.text_area("תגובה:", value=str(row["comments"]) if pd.notna(row["comments"]) else "", key=f"ec_{coin_id}")
                    
                    if st.button("💾 שמור שינויים", key=f"sv_{coin_id}"):
                        # עדכון חסין: טוענים את כל הקובץ, מעדכנים ושומרים
                        fresh_df = load_data()
                        fresh_df.loc[fresh_df['id'
