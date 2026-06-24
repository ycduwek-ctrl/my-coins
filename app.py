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

# עיצוב הקרוסלה עם חצים פעילים בשיטה החדשה
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

    /* חצים על התמונה */
    .nav-arrow {
        position: absolute;
        top: 0;
        bottom: 0;
        width: 45px;
        background: rgba(0, 0, 0, 0.1);
        color: white;
        border: none;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 35px;
        cursor: pointer;
        z-index: 5;
        transition: background 0.3s;
    }
    
    .nav-arrow:hover { background: rgba(0, 0, 0, 0.4); }
    .prev-arrow { left: 0; }
    .next-arrow { right: 0; }

    .stExpander { border: 1px solid #eee !important; border-radius: 10px !important; margin-top: 5px; }
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
    st.sidebar.download_button("📥 הורד גיבוי (CSV)", csv_data, f"coins_backup.csv", "text/csv")

tab1, tab2 = st.tabs(["💎 הגלריה", "➕ הוספה"])

with tab2:
    st.header("הוספת מטבע חדש")
    with st.form("add_form", clear_on_submit=True):
        n_name = st.text_input("שם:")
        n_price = st.text_input("מחיר:")
        n_files = st.file_uploader("בחר תמונות:", accept_multiple_files=True)
        if st.form_submit_button("🚀 שמור"):
            if n_name and n_files:
                with st.spinner('מעלה...'):
                    urls = [upload_to_cloud(f) for f in n_files]
                    new_id = str(int(time.time()))
                    new_row = pd.DataFrame([{"id": new_id, "name": str(n_name), "price": str(n_price), "images": "|".join(urls), "comments": ""}])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_data(df)
                    st.rerun()

with tab1:
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        if view_mode == "גלריה":
            cols = st.columns(grid_size)
            for index, row in df.iterrows():
                coin_id = str(row['id'])
                with cols[index % grid_size]:
                    img_list = str(row["images"]).split("|")
                    
                    images_html = "".join([f'<div class="scroll-item"><img src="{url}"></div>' for url in img_list])
                    
                    # פתרון החצים החדש - פקודת JavaScript פשוטה שתמיד עובדת
                    carousel_html = f"""
                    <div class="carousel-wrapper">
                        <button class="nav-arrow prev-arrow" onclick="this.nextElementSibling.scrollBy({{left: -this.nextElementSibling.offsetWidth, behavior: 'smooth'}})">‹</button>
                        <div class="scroll-container">
                            {images_html}
                        </div>
                        <button class="nav-arrow next-arrow" onclick="this.previousElementSibling.scrollBy({{left: this.previousElementSibling.offsetWidth, behavior: 'smooth'}})">›</button>
                    </div>
                    """
                    st.markdown(carousel_html, unsafe_allow_html=True)
                    
                    st.write(f"**{row['name']}**")

                    with st.expander("🔍 ניהול"):
                        e_name = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                        e_price = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                        e_comm = st.text_area("תגובה:", value=str(row["comments"]) if pd.notna(row["comments"]) else "", key=f"ec_{coin_id}")
                        
                        if st.button("💾 שמור שינויים", key=f"sv_{coin_id}"):
                            full_df = load_data()
                            idx = full_df[full_df['id'] == coin_id].index[0]
                            full_df.at[idx, 'name'], full_df.at[idx, 'price'], full_df.at[idx, 'comments'] = str(e_name), str(e_price), str(e_comm)
                            save_data(full_df)
                            st.rerun()
                        
                        st.divider()
                        add_f = st.file_uploader("➕ הוסף תמונות:", accept_multiple_files=True, key=f"af_{coin_id}")
                        if st.button("✅ הוסף", key=f"ab_{coin_id}"):
                            if add_f:
                                with st.spinner('מעלה...'):
                                    new_urls = [upload_to_cloud(nf) for nf in add_f]
                                    full_df = load_data()
                                    idx = full_df[full_df['id'] == coin_id].index[0]
                                    full_df.at[idx, 'images'] = f"{full_df.at[idx, 'images']}|{'|'.join(new_urls)}"
                                    save_data(full_df)
                                    st.rerun()

                        if st.button("🗑️ מחק פריט", key=f"del_{coin_id}", use_container_width=True):
                            full_df = load_data()
                            full_df = full_df[full_df['id'] != coin_id]
                            save_data(full_df)
                            st.rerun()
        
        else: # תצוגת רשימה
            total_sum = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
            st.subheader(f"💰 שווי כולל: {total_sum:,.0f} ₪")
            for index, row in df.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    img_url = str(row["images"]).split("|")[0]
                    c1.image(img_url, use_container_width=True)
                    c2.write(f"### {row['name']}\n**מחיר:** {row['price']} ₪")
