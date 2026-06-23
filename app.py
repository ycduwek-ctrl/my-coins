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

# ניהול נתונים
DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # וודא שה-ID תמיד מסוג מספר
        df['id'] = df['id'].astype(int)
        return df
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ממשק משתמש ---
if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary ב-Secrets.")
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
        new_files = st.file_uploader("בחר תמונות (אחת או יותר):", accept_multiple_files=True)
        submit_button = st.form_submit_button("🚀 שמור לקטלוג")

        if submit_button:
            if new_name and new_files:
                with st.spinner('מעלה לענן...'):
                    urls = [upload_to_cloud(f) for f in new_files]
                    df = load_data()
                    new_row = pd.DataFrame([{
                        "id": int(time.time()), 
                        "name": new_name, 
                        "price": new_price, 
                        "images": "|".join(urls), 
                        "comments": ""
                    }])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.success("נוסף בהצלחה!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("חובה להזין שם ולבחור תמונה אחת לפחות.")

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        # יצירת עותק לעבודה כדי למנוע בעיות אינדקס בלופ
        current_catalog = df.copy()
        
        for index, row in current_catalog.iterrows():
            with cols[index % grid_size]:
                img_list = str(row["images"]).split("|")
                coin_id = int(row["id"])
                
                # קרוסלת Swipe
                carousel_html = '<div class="scroll-container">'
                for url in img_list:
                    carousel_html += f'<div class="scroll-item"><img src="{url}"></div>'
                carousel_html += '</div>'
                st.markdown(carousel_html, unsafe_allow_html=True)
                
                st.write(f"**{row['name']}**")

                with st.expander("🔍 ניהול ופרטים"):
                    # עריכה
                    edit_name = st.text_input("שנה שם:", value=str(row["name"]), key=f"en_{coin_id}")
                    edit_price = st.text_input("שנה מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                    edit_comm = st.text_area("תגובה/הערה:", value=str(row["comments"]) if pd.notna(row["comments"]) else "", key=f"ec_{coin_id}")
                    
                    if st.button("💾 שמור שינויים", key=f"sv_{coin_id}"):
                        # עדכון לפי ID כדי למנוע TypeError
                        df.loc[df['id'] == coin_id, ["name", "price", "comments"]] = [edit_name, edit_price, edit_comm]
                        save_data(df)
                        st.success("עודכן!")
                        st.rerun()
                    
                    st.divider()
                    st.write("➕ הוספת תמונות:")
                    add_more_files = st.file_uploader("בחר תמונות נוספות:", accept_multiple_files=True, key=f"am_{coin_id}")
                    if st.button("✅ הוסף", key=f"amb_{coin_id}"):
                        if add_more_files:
                            with st.spinner('מעלה...'):
                                new_urls = [upload_to_cloud(nf) for nf in add_more_files]
                                current_images = df.loc[df['id'] == coin_id, "images"].values[0]
                                df.loc[df['id'] == coin_id, "images"] = current_images + "|" + "|".join(new_urls)
                                save_data(df)
                                st.rerun()

                    st.divider()
                    # ניהול מחיקת תמונות קיימות
                    st.write("מחיקת תמונות בודדות:")
                    keep_imgs = []
                    images_changed = False
                    for i, url in enumerate(img_list):
                        c1, c2 = st.columns([4, 1])
                        c1.image(url, width=60)
                        if c2.button("🗑️", key=f"delimg_{coin_id}_{i}"):
                            images_changed = True
                        else:
                            keep_imgs.append(url)
                    
                    if images_changed:
                        if len(keep_imgs) > 0:
                            df.loc[df['id'] == coin_id, "images"] = "|".join(keep_imgs)
                            save_data(df)
                            st.rerun()
                        else:
                            st.error("לא ניתן למחוק את כל התמונות. מחק את כל הפריט במקום.")

                    if st.button("❌ מחק את כל המטבע", key=f"del_all_{coin_id}", use_container_width=True):
                        df = df[df['id'] != coin_id]
                        save_data(df)
                        st.rerun()
