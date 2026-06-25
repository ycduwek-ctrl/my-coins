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

# עיצוב CSS להשגת המראה המדויק מהתמונה
st.markdown("""
<style>
    /* הגדרות קרוסלה */
    .carousel-wrapper { position: relative; width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 12px; background: #f8f9fa; }
    .scroll-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scroll-behavior: smooth; gap: 0px; scrollbar-width: none; width: 100%; height: 100%; }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-item { flex: 0 0 100%; scroll-snap-align: center; aspect-ratio: 1/1; }
    .scroll-item img { width: 100%; height: 100%; object-fit: cover; }
    .nav-arrow { position: absolute; top: 0; bottom: 0; width: 35px; background: rgba(0,0,0,0.05); color: white; border: none; font-size: 25px; cursor: pointer; z-index: 5; }
    .nav-arrow:hover { background: rgba(0,0,0,0.2); }
    .prev-arrow { left: 0; } .next-arrow { right: 0; }

    /* עיצוב תגיות (Chips) כמו בתמונה */
    .tag-container { display: flex; align-items: center; gap: 5px; flex-wrap: nowrap; margin-top: 8px; direction: rtl; }
    .coin-name { font-weight: bold; border-left: 2px solid #ddd; padding-left: 8px; margin-left: 5px; }
    .price-green { color: #2e7d32; font-weight: bold; margin-left: 10px; }
    
    .chip { padding: 4px 12px; border-radius: 15px; font-size: 0.8em; border: 1px solid rgba(0,0,0,0.05); }
    .chip-country { background-color: #e8f5e9; color: #2e7d32; } /* ירוק בהיר */
    .chip-material { background-color: #fff9c4; color: #856404; } /* צהוב/קרם */
    .chip-year { background-color: #fce4ec; color: #880e4f; } /* ורוד בהיר */

    /* עיצוב כפתור הפלוס - תמונת המטבע */
    .stPopover { width: 100%; }
    .stPopover > button { 
        width: 100% !important; aspect-ratio: 1/1 !important; border-radius: 12px !important; 
        border: 2px solid #2e7d32 !important; padding: 0 !important; overflow: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

# רשימות לקטלוג
COUNTRIES = ["ישראל", "המנדט הבריטי", "האימפריה העות'מאנית", "ארה\"ב", "בריטניה", "רוסיה", "ברית המועצות", "אחר"]
MATERIALS = ["כסף", "זהב", "נחושת", "ניקל", "ברונזה", "אלומיניום", "מתכת מעורבת"]

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
        try: return pd.read_csv(DB_FILE, dtype=str)
        except: pass
    return pd.DataFrame(columns=["id", "name", "price", "country", "material", "year", "images", "comments"])

def save_data(df): df.to_csv(DB_FILE, index=False)

if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary.")
    st.stop()

df = load_data()

# --- סינון מהיר בסידבר ---
st.sidebar.title("🔍 סינון")
f_country = st.sidebar.multiselect("מדינה:", COUNTRIES)
f_material = st.sidebar.multiselect("חומר:", MATERIALS)
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

filtered_df = df.copy()
if f_country: filtered_df = filtered_df[filtered_df['country'].isin(f_country)]
if f_material: filtered_df = filtered_df[filtered_df['material'].isin(f_material)]

# --- ממשק ראשי ---
tab1, tab2 = st.tabs(["🪙 הגלריה", "📜 רשימה וסיכום"])

with tab1:
    cols = st.columns(grid_size)
    
    # 1. הצגת המטבעות הקיימים
    for index, row in filtered_df.iterrows():
        col_idx = index % grid_size
        coin_id = str(row['id'])
        with cols[col_idx]:
            img_list = str(row["images"]).split("|")
            images_html = "".join([f'<div class="scroll-item"><img src="{url}"></div>' for url in img_list])
            
            # קרוסלה
            st.markdown(f"""
            <div class="carousel-wrapper">
                <button class="nav-arrow prev-arrow" onclick="this.nextElementSibling.scrollBy({{left: -this.nextElementSibling.offsetWidth, behavior: 'smooth'}})">‹</button>
                <div class="scroll-container">{images_html}</div>
                <button class="nav-arrow next-arrow" onclick="this.previousElementSibling.scrollBy({{left: this.previousElementSibling.offsetWidth, behavior: 'smooth'}})">›</button>
            </div>
            """, unsafe_allow_html=True)
            
            # שורת מידע מעוצבת בדיוק לפי התמונה
            st.markdown(f"""
            <div class="tag-container">
                <span class="coin-name">{row['name']}</span>
                <span class="price-green">{row['price']} ₪</span>
                <span class="chip chip-country">{row['country']}</span>
                <span class="chip chip-material">{row['material']}</span>
                <span class="chip chip-year">{row['year']}</span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ניהול ופרטים"):
                e_name = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                e_price = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                e_country = st.selectbox("מדינה:", COUNTRIES, index=COUNTRIES.index(row['country']) if row['country'] in COUNTRIES else 0, key=f"ec_{coin_id}")
                e_mat = st.selectbox("חומר:", MATERIALS, index=MATERIALS.index(row['material']) if row['material'] in MATERIALS else 0, key=f"em_{coin_id}")
                e_year = st.text_input("שנה:", value=str(row["year"]), key=f"ey_{coin_id}")
                
                if st.button("💾 שמור", key=f"sv_{coin_id}"):
                    full_df = load_data()
                    idx = full_df[full_df['id'] == coin_id].index[0]
                    full_df.at[idx, 'name'], full_df.at[idx, 'price'] = e_name, e_price
                    full_df.at[idx, 'country'], full_df.at[idx, 'material'] = e_country, e_mat
                    full_df.at[idx, 'year'] = e_year
                    save_data(full_df); st.rerun()

                if st.button("🗑️ מחק", key=f"del_{coin_id}"):
                    full_df = load_data(); full_df = full_df[full_df['id'] != coin_id]
                    save_data(full_df); st.rerun()

    # 2. כפתור "+" בסוף הרשימה עם התמונה מהענן שלך
    last_col_idx = len(filtered_df) % grid_size
    with cols[last_col_idx]:
        plus_img_url = "https://res.cloudinary.com/dvxamxm9x/image/upload/v1782371799/coin_Plus_txh2vk.jpg"
        with st.popover("➕", help="הוסף מטבע חדש"):
            # שימוש בתמונה בתוך הפופאובר כדי שייראה כמו בתמונה ששלחת
            st.image(plus_img_url, use_container_width=True)
            st.subheader("הוספת מטבע חדש")
            q_name = st.text_input("שם המטבע:", key="q_n")
            q_price = st.text_input("מחיר:", key="q_p")
            q_country = st.selectbox("מדינה:", COUNTRIES, key="q_c")
            q_mat = st.selectbox("חומר:", MATERIALS, key="q_m")
            q_year = st.text_input("שנה:", key="q_y")
            q_files = st.file_uploader("תמונות:", accept_multiple_files=True, key="q_f")
            if st.button("🚀 שמור לקטלוג", key="q_s"):
                if q_name and q_files:
                    urls = [upload_to_cloud(f) for f in q_files]
                    new_row = pd.DataFrame([{"id": str(int(time.time())), "name": q_name, "price": q_price, "country": q_country, "material": q_mat, "year": q_year, "images": "|".join(urls), "comments": ""}])
                    save_data(pd.concat([df, new_row], ignore_index=True)); st.rerun()
        st.write("<p style='text-align:center; color:#2e7d32; font-weight:bold;'>הוסף חדש</p>", unsafe_allow_html=True)

with tab2:
    total_val = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
    st.subheader(f"💰 שווי כולל: {total_val:,.0f} ₪")
    st.dataframe(df[["name", "price", "country", "year", "material"]], use_container_width=True)
