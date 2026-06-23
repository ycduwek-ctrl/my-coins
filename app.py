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
    if "CLOUDINARY_CLOUD_NAME" in st.secrets:
        cloudinary.config(
            cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
            api_key = st.secrets["CLOUDINARY_API_KEY"],
            api_secret = st.secrets["CLOUDINARY_API_SECRET"]
        )
        READY = True
    else:
        READY = False
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

# ניהול נתונים - CSV
DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE)
        except:
            return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ממשק משתמש ---
if not READY:
    st.error("⚠️ הגדרות Cloudinary חסרות ב-Secrets של Streamlit.")
    st.stop()

st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

tab1, tab2 = st.tabs(["💎 הגלריה שלי", "➕ הוספת מטבע"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת מטבע חדש")
    with st.form("add_coin_form", clear_on_submit=True):
        new_name = st.text_input("שם המטבע:")
        new_price = st.text_input("מחיר (₪):")
        new_files = st.file_uploader("בחר תמונות מהגלריה:", accept_multiple_files=True)
        submit_button = st.form_submit_button("🚀 שמור לקטלוג")

        if submit_button:
            if new_name and new_files:
                with st.spinner('מעלה תמונות...'):
                    urls = [upload_to_cloud(f) for f in new_files]
                    df = load_data()
                    # יצירת ID ייחודי כמספר
                    new_id = int(time.time())
                    new_row = {"id": new_id, "name": new_name, "price": new_price, "images": "|".join(urls), "comments": ""}
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                    save_data(df)
                    st.success("נוסף בהצלחה!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("נא להזין שם ולבחור תמונה.")

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        # לופ על הטבלה
        for index, row in df.iterrows():
            with cols[index % grid_size]:
                img_list = str(row["images"]).split("|")
                coin_id = row["id"]
                
                # קרוסלה
                carousel_html = '<div class="scroll-container">'
                for url in img_list:
                    carousel_html += f'<div class="scroll-item"><img src="{url}"></div>'
                carousel_html += '</div>'
                st.markdown(carousel_html, unsafe_allow_html=True)
                
                st.write(f"**{row['name']}**")

                with st.expander("🔍 ניהול ופרטים"):
                    # עריכה - משתמשים ב-Session State כדי למנוע ריענון לא רצוי
                    edit_name = st.text_input("שם:", value=str(row["name"]), key=f"n_{index}")
                    edit_price = st.text_input("מחיר:", value=str(row["price"]), key=f"p_{index}")
                    edit_comm = st.text_area("תגובה:", value=str(row["comments"]) if pd.notna(row["comments"]) else "", key=f"c_{index}")
                    
                    if st.button("💾 שמור שינויים", key=f"save_{index}"):
                        # תיקון השגיאה: עדכון ישיר לפי האינדקס של השורה
                        df.at[index, "name"] = edit_name
                        df.at[index, "price"] = edit_price
                        df.at[index, "comments"] = edit_comm
                        save_data(df)
                        st.success("עודכן!")
                        st.rerun()
                    
                    st.divider()
                    st.write("➕ הוספת תמונות:")
                    add_files = st.file_uploader("בחר תמונות נוספות:", accept_multiple_files=True, key=f"up_{index}")
                    if st.button("✅ הוסף תמונות", key=f"btn_up_{index}"):
                        if add_files:
                            with st.spinner('מעלה...'):
                                new_urls = [upload_to_cloud(nf) for nf in add_files]
                                df.at[index, "images"] = str(row["images"]) + "|" + "|".join(new_urls)
                                save_data(df)
                                st.rerun()

                    st.divider()
                    st.write("מחיקת תמונות:")
                    current_images = str(row["images"]).split("|")
                    keep_list = []
                    was_deleted = False
                    
                    for i, url in enumerate(current_images):
                        c1, c2 = st.columns([4, 1])
                        c1.image(url, width=60)
                        if c2.button("🗑️", key=f"delimg_{index}_{i}"):
                            was_deleted = True
                        else:
                            keep_list.append(url)
                    
                    if was_deleted:
                        if len(keep_list) > 0:
                            df.at[index, "images"] = "|".join(keep_list)
                            save_data(df)
                            st.rerun()
                        else:
                            st.error("חייבת להישאר לפחות תמונה אחת.")

                    if st.button("❌ מחק את כל המטבע", key=f"full_{index}", use_container_width=True):
                        df = df.drop(index)
                        save_data(df)
                        st.rerun()
