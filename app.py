import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import os
from PIL import Image
import io
import time

# --- הגדרות דף ---
st.set_page_config(page_title="Coin Index Pro", layout="wide")

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

# עיצוב CSS למראה אינסטגרם נקי עם חצים ו-Swipe
st.markdown("""
<style>
    .carousel-wrapper { position: relative; width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 12px; background: #f8f9fa; }
    .scroll-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scroll-behavior: smooth; gap: 0px; scrollbar-width: none; width: 100%; height: 100%; }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-item { flex: 0 0 100%; scroll-snap-align: center; aspect-ratio: 1/1; }
    .scroll-item img { width: 100%; height: 100%; object-fit: cover; }
    .nav-arrow { position: absolute; top: 0; bottom: 0; width: 40px; background: rgba(0,0,0,0.1); color: white; border: none; font-size: 30px; cursor: pointer; z-index: 5; }
    .nav-arrow:hover { background: rgba(0,0,0,0.4); }
    .prev-arrow { left: 0; } .next-arrow { right: 0; }
    
    .filter-tag { background: #f1f3f4; color: #5f6368; padding: 3px 10px; border-radius: 12px; font-size: 0.8em; margin: 2px; display: inline-block; border: 1px solid #ddd; }
    .price-label { color: #2e7d32; font-weight: bold; font-size: 1.1em; }
    
    .stPopover > button { width: 100% !important; aspect-ratio: 1/1 !important; border-radius: 12px !important; border: 2px dashed #ccc !important; font-size: 40px !important; color: #bbb !important; }
    .main { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# רשימת מדינות היסטורית ומודרנית
COUNTRIES = [
    "ישראל", "המנדט הבריטי", "האימפריה העות'מאנית", "ארה\"ב", "בריטניה", "רוסיה", 
    "ברית המועצות", "גרמניה", "צרפת", "קנדה", "איטליה", "ספרד", "מצרים", 
    "ירדן", "לבנון", "סוריה", "יוון", "טורקיה", "סין", "יפן", "אחר"
]

MATERIALS = ["נחושת", "כסף", "זהב", "ניקל", "ברונזה", "אלומיניום", "פלדה", "מתכת מעורבת"]

def upload_to_cloud(file):
    img = Image.open(file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    res = cloudinary.uploader.upload(buf.getvalue())
    return res['secure_url']

DB_FILE = 'coins_final_data.csv'
COLUMNS = ["id", "name", "price", "country", "material", "year", "images", "comments"]

def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE, dtype=str)
        except: pass
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary ב-Secrets.")
    st.stop()

df = load_data()

# --- סינון מהיר בסידבר ---
st.sidebar.title("🔍 סינון מהיר")
f_country = st.sidebar.multiselect("מדינה / ישות:", COUNTRIES)
f_material = st.sidebar.multiselect("חומר:", MATERIALS)
f_year = st.sidebar.text_input("חיפוש לפי שנה:")

st.sidebar.divider()
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

# לוגיקת סינון
filtered_df = df.copy()
if f_country: filtered_df = filtered_df[filtered_df['country'].isin(f_country)]
if f_material: filtered_df = filtered_df[filtered_df['material'].isin(f_material)]
if f_year: filtered_df = filtered_df[filtered_df['year'].str.contains(f_year, na=False)]

# --- ממשק ראשי ---
tab1, tab2 = st.tabs(["💎 הגלריה", "📜 רשימה וסיכום"])

with tab1:
    cols = st.columns(grid_size)
    
    # הצגת המטבעות
    for index, row in filtered_df.iterrows():
        col_idx = index % grid_size
        coin_id = str(row['id'])
        with cols[col_idx]:
            img_list = str(row["images"]).split("|")
            images_html = "".join([f'<div class="scroll-item"><img src="{url}"></div>' for url in img_list])
            
            st.markdown(f"""
            <div class="carousel-wrapper">
                <button class="nav-arrow prev-arrow" onclick="this.nextElementSibling.scrollBy({{left: -this.nextElementSibling.offsetWidth, behavior: 'smooth'}})">‹</button>
                <div class="scroll-container">{images_html}</div>
                <button class="nav-arrow next-arrow" onclick="this.previousElementSibling.scrollBy({{left: this.previousElementSibling.offsetWidth, behavior: 'smooth'}})">›</button>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**{row['name']}** | <span class='price-label'>{row['price']} ₪</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='filter-tag'>{row['country']}</span><span class='filter-tag'>{row['year']}</span>", unsafe_allow_html=True)

            with st.expander("🔍 ניהול ופרטים"):
                e_name = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                e_price = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                e_country = st.selectbox("מדינה:", COUNTRIES, index=COUNTRIES.index(row['country']) if row['country'] in COUNTRIES else 0, key=f"ec_{coin_id}")
                e_mat = st.selectbox("חומר:", MATERIALS, index=MATERIALS.index(row['material']) if row['material'] in MATERIALS else 0, key=f"em_{coin_id}")
                e_year = st.text_input("שנה:", value=str(row["year"]), key=f"ey_{coin_id}")
                e_comm = st.text_area("תגובה:", value=str(row["comments"]), key=f"ect_{coin_id}")
                
                if st.button("💾 שמור שינויים", key=f"sv_{coin_id}"):
                    full_df = load_data()
                    idx = full_df[full_df['id'] == coin_id].index[0]
                    full_df.at[idx, 'name'], full_df.at[idx, 'price'] = e_name, e_price
                    full_df.at[idx, 'country'], full_df.at[idx, 'material'] = e_country, e_mat
                    full_df.at[idx, 'year'], full_df.at[idx, 'comments'] = e_year, e_comm
                    save_data(full_df); st.rerun()

                st.divider()
                if st.button("🗑️ מחק פריט", key=f"del_{coin_id}", use_container_width=True):
                    full_df = load_data()
                    full_df = full_df[full_df['id'] != coin_id]
                    save_data(full_df); st.rerun()

    # כפתור "+" בסוף
    last_col = len(filtered_df) % grid_size
    with cols[last_col]:
        with st.popover("➕"):
            st.subheader("הוספת מטבע")
            q_name = st.text_input("שם המטבע:", key="q_n")
            q_price = st.text_input("מחיר:", key="q_p")
            q_country = st.selectbox("מדינה:", COUNTRIES, key="q_c")
            q_mat = st.selectbox("חומר:", MATERIALS, key="q_m")
            q_year = st.text_input("שנה:", key="q_y")
            q_files = st.file_uploader("תמונות:", accept_multiple_files=True, key="q_f")
            if st.button("🚀 שמור", key="q_s"):
                if q_name and q_files:
                    urls = [upload_to_cloud(f) for f in q_files]
                    new_id = str(int(time.time()))
                    new_row = pd.DataFrame([{"id": new_id, "name": q_name, "price": q_price, "country": q_country, "material": q_mat, "year": q_year, "images": "|".join(urls), "comments": ""}])
                    save_data(pd.concat([df, new_row], ignore_index=True)); st.rerun()
        st.write("**הוסף חדש**")

with tab2:
    total_val = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
    st.subheader(f"💰 שווי כולל של כל האוסף: {total_val:,.0f} ₪")
    st.dataframe(df[["name", "price", "country", "year", "material", "comments"]], use_container_width=True)
