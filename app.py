import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
import os
from PIL import Image
import io

# --- הגדרות דף ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

# הגדרת Cloudinary מה-Secrets
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"]
)

# חיבור לגוגל שיטס
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        return conn.read(worksheet="coins", ttl="0s")
    except:
        return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    conn.update(worksheet="coins", data=df)

# פונקציה להעלאת תמונה לענן
def upload_image_to_cloud(uploaded_file):
    # חיתוך לריבוע לפני העלאה
    img = Image.open(uploaded_file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    
    # שמירה זמנית בזיכרון לשליחה
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    byte_im = buf.getvalue()
    
    # העלאה ל-Cloudinary
    result = cloudinary.uploader.upload(byte_im)
    return result['secure_url'] # מחזיר קישור אינטרנט קבוע

# --- ממשק משתמש ---
tab1, tab2 = st.tabs(["💎 הקטלוג הקבוע", "➕ הוספה"])

with tab2:
    st.header("הוספת מטבע (גיבוי ענן מלא)")
    name = st.text_input("שם המטבע:")
    price = st.text_input("מחיר:")
    files = st.file_uploader("צלם או בחר תמונות:", accept_multiple_files=True)
    
    if st.button("💾 שמור לענן ולגוגל"):
        if name and files:
            with st.spinner('מעלה תמונות לענן...'):
                urls = []
                for f in files:
                    url = upload_image_to_cloud(f)
                    urls.append(url)
                
                df = load_data()
                new_row = pd.DataFrame([{"id": len(df)+1, "name": name, "price": price, "images": "|".join(urls), "comments": ""}])
                df = pd.concat([df, new_row], ignore_index=True)
                save_data(df)
                st.success("הכל נשמר לנצח!")
                st.rerun()

with tab1:
    df = load_data()
    grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)
    
    if df is None or df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                img_list = str(row["images"]).split("|")
                # מציג את התמונה ישירות מהקישור בענן
                st.image(img_list[0], use_container_width=True)
                st.write(f"**{row['name']}**")

                with st.expander("🔍 ניהול"):
                    st.write(f"מחיר: {row['price']}")
                    st.write(f"הערות: {row['comments']}")
                    
                    if st.button("🗑️ מחק", key=f"del_{idx}"):
                        df = df.drop(idx)
                        save_data(df)
                        st.rerun()
