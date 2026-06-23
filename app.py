import streamlit as st
import pandas as pd
try:
    from streamlit_gsheets import GSheetsConnection
    HAS_GSHEETS = True
except ImportError:
    HAS_GSHEETS = False

import os
from PIL import Image
import time
import base64
import io

# --- הגדרות דף ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

# עיצוב גלילה (Swipe)
st.markdown("""
<style>
    .scroll-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 5px; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-item { flex: 0 0 100%; scroll-snap-align: center; aspect-ratio: 1 / 1; }
    .scroll-item img { width: 100%; height: 100%; object-fit: cover; border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# פונקציות טעינה ושמירה
DB_FILE = 'catalog_data.csv'

def load_data():
    if HAS_GSHEETS:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            # אם שם הגיליון בגוגל הוא לא 'coins', שנה כאן ל-'Sheet1'
            return conn.read(worksheet="coins", ttl="0s")
        except:
            pass
    
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)
    if HAS_GSHEETS:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(worksheet="coins", data=df)
            st.toast("המידע נשמר גם בגוגל שיטס!")
        except:
            st.warning("המידע נשמר מקומית בלבד (בעיה בחיבור לגוגל)")

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

IMG_DIR = "coin_images"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

# --- ממשק משתמש ---
st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הקטלוג", "➕ הוספה"])

with tab2:
    st.header("הוספת מטבע")
    c_name = st.text_input("שם המטבע:")
    c_price = st.text_input("מחיר:")
    up_files = st.file_uploader("בחר תמונות מהגלריה:", accept_multiple_files=True)
    
    if st.button("💾 שמור הכל"):
        if c_name and up_files:
            paths = []
            for f in up_files:
                img = Image.open(f).convert('RGB')
                # חיתוך לריבוע
                w, h = img.size
                s = min(w, h)
                img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
                p = os.path.join(IMG_DIR, f"c_{int(time.time()*1000)}_{f.name}")
                img.save(p)
                paths.append(p)
            
            df = load_data()
            new_row = pd.DataFrame([{"id": len(df)+1, "name": c_name, "price": c_price, "images": "|".join(paths), "comments": ""}])
            df = pd.concat([df, new_row], ignore_index=True)
            save_data(df)
            st.success("נשמר!")
            st.rerun()

with tab1:
    df = load_data()
    if df is None or df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                img_list = str(row["images"]).split("|")
                
                # קרוסלת Swipe
                carousel_html = '<div class="scroll-container">'
                for img_p in img_list:
                    b64 = get_image_base64(img_p)
                    if b64:
                        carousel_html += f'<div class="scroll-item"><img src="data:image/jpeg;base64,{b64}"></div>'
                carousel_html += '</div>'
                st.markdown(carousel_html, unsafe_allow_html=True)
                
                st.write(f"**{row['name']}**")

                with st.expander("🔍 פרטים וניהול"):
                    en = st.text_input("שם:", value=str(row["name"]), key=f"n_{idx}")
                    ep = st.text_input("מחיר:", value=str(row["price"]), key=f"p_{idx}")
                    ec = st.text_area("תגובה:", value=str(row["comments"]) if pd.notna(row["comments"]) else "", key=f"c_{idx}")
                    
                    if st.button("💾 שמור שינויים", key=f"s_{idx}"):
                        df.at[idx, "name"] = en
                        df.at[idx, "price"] = ep
                        df.at[idx, "comments"] = ec
                        save_data(df)
                        st.rerun()
                    
                    if st.button("🗑️ מחק פריט", key=f"d_{idx}"):
                        df = df.drop(idx)
                        save_data(df)
                        st.rerun()

# כפתור גיבוי ידני
st.sidebar.divider()
if st.sidebar.button("📥 הורד גיבוי (CSV)"):
    df = load_data()
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("לחץ להורדה", csv, "coins_backup.csv", "text/csv")
