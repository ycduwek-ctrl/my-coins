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

# עיצוב CSS - קרוסלה, חצים וכרטיס הוספה בסוף
st.markdown("""
<style>
    .carousel-wrapper {
        position: relative;
        width: 100%;
        aspect-ratio: 1 / 1;
        overflow: hidden;
        border-radius: 12px;
        background-color: #f8f9fa;
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
        top: 0; bottom: 0; width: 40px;
        background: rgba(0, 0, 0, 0.1);
        color: white; border: none;
        display: flex; align-items: center; justify-content: center;
        font-size: 30px; cursor: pointer; z-index: 5;
    }
    .nav-arrow:hover { background: rgba(0, 0, 0, 0.4); }
    .prev-arrow { left: 0; }
    .next-arrow { right: 0; }

    /* עיצוב כרטיס הוספה (פלוס) */
    .stPopover { width: 100%; }
    .stPopover > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        border-radius: 12px !important;
        border: 2px dashed #ddd !important;
        background-color: #fafafa !important;
        font-size: 50px !important;
        color: #bbb !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: 0.3s;
    }
    
    .price-tag {
        color: #2e7d32;
        font-weight: bold;
        font-size: 1.1em;
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

DB_FILE = 'final_coins_db.csv'
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE, dtype=str)
            return df
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
    st.sidebar.download_button("📥 הורד גיבוי (CSV)", csv_data, "coins_backup.csv", "text/csv", use_container_width=True)

tab1, tab2 = st.tabs(["💎 הגלריה שלי", "➕ ניהול כללי"])

with tab1:
    if view_mode == "גלריה":
        cols = st.columns(grid_size)
        
        # 1. המטבעות הקיימים
        for index, row in df.iterrows():
            col_idx = index % grid_size
            coin_id = str(row['id'])
            with cols[col_idx]:
                img_list = [img for img in str(row["images"]).split("|") if img.strip()]
                images_html = "".join([f'<div class="scroll-item"><img src="{url}"></div>' for url in img_list])
                
                carousel_html = f"""
                <div class="carousel-wrapper">
                    <button class="nav-arrow prev-arrow" onclick="this.nextElementSibling.scrollBy({{left: -this.nextElementSibling.offsetWidth, behavior: 'smooth'}})">‹</button>
                    <div class="scroll-container">{images_html}</div>
                    <button class="nav-arrow next-arrow" onclick="this.previousElementSibling.scrollBy({{left: this.previousElementSibling.offsetWidth, behavior: 'smooth'}})">›</button>
                </div>
                """
                st.markdown(carousel_html, unsafe_allow_html=True)
                
                # שם ומחיר באותה שורה
                st.markdown(f"**{row['name']}** | <span class='price-tag'>{row['price']} ₪</span>", unsafe_allow_html=True)

                with st.expander("🔍 ניהול"):
                    e_name = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                    e_price = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                    e_comm = st.text_area("תגובה:", value=str(row["comments"]) if pd.notna(row["comments"]) else "", key=f"ec_{coin_id}")
                    
                    if st.button("💾 שמור שינויים", key=f"sv_{coin_id}"):
                        full_df = load_data()
                        idx_match = full_df[full_df['id'] == coin_id].index
                        if not idx_match.empty:
                            full_df.at[idx_match[0], 'name'] = e_name
                            full_df.at[idx_match[0], 'price'] = e_price
                            full_df.at[idx_match[0], 'comments'] = e_comm
                            save_data(full_df)
                            st.rerun()
                    
                    st.divider()
                    st.write("🖼️ **ניהול תמונות:**")
                    # תצוגת תמונות קיימות למחיקה בודדת
                    temp_img_list = img_list.copy()
                    was_deleted = False
                    for i, img_url in enumerate(temp_img_list):
                        c_img, c_del = st.columns([4, 1])
                        c_img.image(img_url, width=60)
                        if c_del.button("🗑️", key=f"delimg_{coin_id}_{i}"):
                            temp_img_list.pop(i)
                            was_deleted = True
                    
                    if was_deleted:
                        full_df = load_data()
                        idx_match = full_df[full_df['id'] == coin_id].index
                        if not idx_match.empty:
                            full_df.at[idx_match[0], 'images'] = "|".join(temp_img_list)
                            save_data(full_df)
                            st.rerun()

                    st.write("➕ הוספת תמונות:")
                    add_f = st.file_uploader("בחר תמונות:", accept_multiple_files=True, key=f"af_{coin_id}")
                    if st.button("✅ הוסף", key=f"ab_{coin_id}"):
                        if add_f:
                            with st.spinner('מעלה...'):
                                new_urls = [upload_to_cloud(nf) for nf in add_f]
                                full_df = load_data()
                                idx_match = full_df[full_df['id'] == coin_id].index
                                if not idx_match.empty:
                                    old_imgs = full_df.at[idx_match[0], 'images']
                                    full_df.at[idx_match[0], 'images'] = f"{old_imgs}|{'|'.join(new_urls)}"
                                    save_data(full_df)
                                    st.rerun()

                    if st.button("🗑️ מחק את כל הפריט", key=f"del_{coin_id}", use_container_width=True):
                        full_df = load_data()
                        full_df = full_df[full_df['id'] != coin_id]
                        save_data(full_df)
                        st.rerun()

        # 2. כרטיס ה-"➕" בסוף
        last_col_idx = len(df) % grid_size
        with cols[last_col_idx]:
            with st.popover("➕"):
                st.subheader("הוספת מטבע חדש")
                q_name = st.text_input("שם המטבע:", key="q_n")
                q_price = st.text_input("מחיר:", key="q_p")
                q_files = st.file_uploader("בחר תמונות:", accept_multiple_files=True, key="q_f")
                if st.button("🚀 שמור לקטלוג", key="q_s", use_container_width=True):
                    if q_name and q_files:
                        with st.spinner('מעלה...'):
                            urls = [upload_to_cloud(f) for f in q_files]
                            new_id = str(int(time.time()))
                            new_row = pd.DataFrame([{"id": new_id, "name": q_name, "price": q_price, "images": "|".join(urls), "comments": ""}])
                            save_data(pd.concat([df, new_row], ignore_index=True))
                            st.rerun()
            st.write("**הוסף חדש**")

    else: # רשימה מפורטת
        total_sum = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
        st.subheader(f"💰 שווי כולל: {total_sum:,.0f} ₪")
        for index, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                img_url = str(row["images"]).split("|")[0]
                c1.image(img_url, use_container_width=True)
                c2.write(f"### {row['name']} | {row['price']} ₪")

# טאב ניהול כללי
with tab2:
    st.header("הוספה דרך ממשק מלא")
    with st.form("main_add", clear_on_submit=True):
        n_n = st.text_input("שם:")
        n_p = st.text_input("מחיר:")
        n_f = st.file_uploader("תמונות:", accept_multiple_files=True)
        if st.form_submit_button("🚀 שמור"):
            if n_n and n_f:
                urls = [upload_to_cloud(f) for f in n_f]
                new_row = pd.DataFrame([{"id": str(int(time.time())), "name": n_n, "price": n_p, "images": "|".join(urls), "comments": ""}])
                save_data(pd.concat([df, new_row], ignore_index=True))
                st.rerun()
