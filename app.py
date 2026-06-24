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

# עיצוב Swipe + תמיכה במחשב (לחיצה וחצים ב-Hover)
st.markdown("""
<style>
    /* מיכל הקרוסלה */
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
        gap: 0px;
        scrollbar-width: none;
        -ms-overflow-style: none;
        cursor: pointer;
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

    /* חצים עדינים שמופיעים רק במחשב (Hover) */
    .carousel-wrapper::after, .carousel-wrapper::before {
        content: '›';
        position: absolute;
        top: 50%;
        transform: translateY(-50%);
        font-size: 40px;
        color: white;
        background: rgba(0,0,0,0.2);
        width: 35px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 5px;
        opacity: 0;
        transition: opacity 0.3s;
        pointer-events: none;
    }
    .carousel-wrapper::before { content: '‹'; left: 10px; }
    .carousel-wrapper::after { content: '›'; right: 10px; }
    
    .carousel-wrapper:hover::after, .carousel-wrapper:hover::before {
        opacity: 1;
    }

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

# ניהול נתונים
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
    st.error("⚠️ הגדרות Cloudinary חסרות.")
    st.stop()

df = load_data()

# --- תפריט צד ---
st.sidebar.title("🖼️ תצוגה")
view_mode = st.sidebar.radio("סגנון:", ["גלריה", "רשימה מפורטת"])
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

st.sidebar.divider()
if not df.empty:
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 הורד גיבוי (CSV)", csv_data, f"coins_{int(time.time())}.csv", "text/csv")

tab1, tab2 = st.tabs(["💎 הגלריה", "➕ הוספה"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת מטבע")
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
                    st.success("נוסף!")
                    time.sleep(0.5)
                    st.rerun()

# --- טאב גלריה ---
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
                    
                    # קרוסלה עם JavaScript פשוט למעבר בלחיצה (ימין=הבא, שמאל=הקודם)
                    carousel_html = f"""
                    <div class="carousel-wrapper">
                        <div class="scroll-container" onclick="
                            const rect = this.getBoundingClientRect();
                            const x = event.clientX - rect.left;
                            if (x > rect.width / 2) {{
                                this.scrollBy({{left: rect.width, behavior: 'smooth'}});
                            }} else {{
                                this.scrollBy({{left: -rect.width, behavior: 'smooth'}});
                            }}">
                            {''.join([f'<div class="scroll-item"><img src="{url}"></div>' for url in img_list])}
                        </div>
                    </div>
                    """
                    st.markdown(carousel_html, unsafe_allow_html=True)
                    
                    st.write(f"**{row['name']}**")

                    with st.expander("🔍 ניהול"):
                        e_name = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                        e_price = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                        e_comm = st.text_area("תגובה:", value=str(row["comments"]) if pd.notna(row["comments"]) else "", key=f"ec_{coin_id}")
                        
                        if st.button("💾 שמור שינויים", key=f"sv_{coin_id}"):
                            idx = df[df['id'] == coin_id].index[0]
                            df.at[idx, 'name'], df.at[idx, 'price'], df.at[idx, 'comments'] = str(e_name), str(e_price), str(e_comm)
                            save_data(df)
                            st.rerun()
                        
                        st.divider()
                        add_f = st.file_uploader("➕ הוסף תמונות:", accept_multiple_files=True, key=f"af_{coin_id}")
                        if st.button("✅ הוסף", key=f"ab_{coin_id}"):
                            if add_f:
                                with st.spinner('מעלה...'):
                                    new_urls = [upload_to_cloud(nf) for nf in add_f]
                                    idx = df[df['id'] == coin_id].index[0]
                                    df.at[idx, 'images'] = f"{df.at[idx, 'images']}|{'|'.join(new_urls)}"
                                    save_data(df)
                                    st.rerun()

                        if st.button("🗑️ מחק פריט", key=f"del_{coin_id}", use_container_width=True):
                            df = df[df['id'] != coin_id]
                            save_data(df)
                            st.rerun()
        
        else: # תצוגת רשימה
            total_sum = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
            st.subheader(f"💰 שווי כולל: {total_sum:,.0f} ₪")
            for index, row in df.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    c1.image(str(row["images"]).split("|")[0], use_container_width=True)
                    c2.write(f"### {row['name']}\n**מחיר:** {row['price']} ₪")
