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

# עיצוב CSS מלא - גלריה, צבעים וכפתור הוספה ירוק
st.markdown("""
<style>
    /* קרוסלה וחצים */
    .carousel-wrapper { position: relative; width: 100%; aspect-ratio: 1/1; overflow: hidden; border-radius: 12px; background: #f8f9fa; }
    .scroll-container { display: flex; overflow-x: auto; scroll-snap-type: x mandatory; scroll-behavior: smooth; gap: 0px; scrollbar-width: none; width: 100%; height: 100%; }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-item { flex: 0 0 100%; scroll-snap-align: center; aspect-ratio: 1 / 1; }
    .scroll-item img { width: 100%; height: 100%; object-fit: cover; }
    .nav-arrow { position: absolute; top: 0; bottom: 0; width: 40px; background: rgba(0,0,0,0.05); color: white; border: none; font-size: 30px; cursor: pointer; z-index: 5; }
    .nav-arrow:hover { background: rgba(0,0,0,0.4); }
    .prev-arrow { left: 0; } .next-arrow { right: 0; }

    /* תגיות (Chips) מעוצבות */
    .tag-container { display: flex; align-items: center; gap: 5px; margin-top: 8px; direction: rtl; flex-wrap: nowrap; overflow-x: auto; }
    .coin-name { font-weight: bold; border-left: 2px solid #ddd; padding-left: 8px; margin-left: 5px; white-space: nowrap; }
    .price-green { color: #2e7d32; font-weight: bold; margin-left: 10px; white-space: nowrap; }
    
    .chip { padding: 4px 10px; border-radius: 15px; font-size: 0.75em; white-space: nowrap; border: 1px solid rgba(0,0,0,0.05); }
    .chip-country { background-color: #e8f5e9; color: #2e7d32; } /* ירוק */
    .chip-material { background-color: #fff9c4; color: #856404; } /* צהוב */
    .chip-year { background-color: #fce4ec; color: #880e4f; } /* ורוד */

    /* עיצוב כפתור ההוספה - ריבוע ירוק בהיר 1:1 */
    div[data-testid="stPopover"] { width: 100%; display: flex; justify-content: center; }
    div[data-testid="stPopover"] > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        height: auto !important;
        border-radius: 15px !important;
        border: 2px solid #2e7d32 !important; /* מסגרת ירוקה כהה */
        background-color: #f1fdf4 !important; /* ירוק בהיר מאוד */
        color: #2e7d32 !important; /* פלוס ירוק */
        font-size: 60px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: 0.3s !important;
        padding: 0 !important;
    }
    div[data-testid="stPopover"] > button:hover {
        background-color: #e3f9e9 !important;
        transform: scale(1.02);
    }
    div[data-testid="stPopover"] svg { display: none !important; } /* הסתרת החץ של המערכת */

    .add-label { text-align: center; color: #2e7d32; font-weight: bold; margin-top: -5px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# פונקציות טעינה ושמירה
def upload_to_cloud(file):
    img = Image.open(file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    res = cloudinary.uploader.upload(buf.getvalue())
    return res['secure_url']

DB_FILE = 'final_coins_db_v11.csv'
COLUMNS = ["id", "name", "price", "country", "material", "year", "images", "comments"]

def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE, dtype=str)
        except: pass
    return pd.DataFrame(columns=COLUMNS)

def save_data(df): df.to_csv(DB_FILE, index=False)

if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary.")
    st.stop()

df = load_data()

# --- תפריט צד (Sidebar) ---
st.sidebar.title("🔍 סינון וחיפוש")
COUNTRIES = ["ישראל", "המנדט הבריטי", "האימפריה העות'מאנית", "ארה\"ב", "בריטניה", "רוסיה", "ברית המועצות", "אחר"]
MATERIALS = ["כסף", "זהב", "נחושת", "ניקל", "ברונזה", "אלומיניום", "מתכת מעורבת"]

f_country = st.sidebar.multiselect("מדינה:", COUNTRIES)
f_material = st.sidebar.multiselect("חומר:", MATERIALS)
f_year = st.sidebar.text_input("חיפוש לפי שנה:") # החזרתי את חיפוש השנה

st.sidebar.divider()
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

# כפתור גיבוי (החזרתי)
st.sidebar.divider()
if not df.empty:
    csv_data = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 הורד גיבוי (CSV)", csv_data, "coins_backup.csv", "text/csv", use_container_width=True)

# לוגיקת סינון
filtered_df = df.copy()
if f_country: filtered_df = filtered_df[filtered_df['country'].isin(f_country)]
if f_material: filtered_df = filtered_df[filtered_df['material'].isin(f_material)]
if f_year: filtered_df = filtered_df[filtered_df['year'].str.contains(f_year, na=False)]

# --- ממשק ראשי ---
tab1, tab2 = st.tabs(["🪙 הגלריה", "📜 רשימה וסיכום"])

with tab1:
    cols = st.columns(grid_size)
    
    # 1. הצגת המטבעות
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
                    full_df.at[idx, 'country'], full_df.at[idx, 'material'] = e_country, em
                    full_df.at[idx, 'year'] = e_year
                    save_data(full_df); st.rerun()

                if st.button("🗑️ מחק", key=f"del_{coin_id}", use_container_width=True):
                    df = df[df['id'] != coin_id]; save_data(df); st.rerun()

    # 2. ריבוע ה-"➕" הירוק בסוף
    last_col_idx = len(filtered_df) % grid_size
    with cols[last_col_idx]:
        with st.popover("＋"):
            st.subheader("הוספת מטבע חדש")
            q_n = st.text_input("שם המטבע:", key="q_n")
            q_p = st.text_input("מחיר:", key="q_p")
            q_c = st.selectbox("מדינה:", COUNTRIES, key="q_c")
            q_m = st.selectbox("חומר:", MATERIALS, key="q_m")
            q_y = st.text_input("שנה:", key="q_y")
            q_f = st.file_uploader("תמונות:", accept_multiple_files=True, key="q_f")
            if st.button("🚀 שמור לקטלוג", key="q_s", use_container_width=True):
                if q_n and q_f:
                    with st.spinner('מעלה...'):
                        urls = [upload_to_cloud(f) for f in q_f]
                        new_id = str(int(time.time()))
                        new_row = pd.DataFrame([{"id": new_id, "name": q_n, "price": q_p, "country": q_c, "material": q_m, "year": q_y, "images": "|".join(urls), "comments": ""}])
                        save_data(pd.concat([df, new_row], ignore_index=True)); st.rerun()
        st.markdown("<p class='add-label'>הוספה חדש</p>", unsafe_allow_html=True)

with tab2:
    total_val = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
    st.subheader(f"💰 שווי כולל של האוסף: {total_val:,.0f} ₪")
    st.dataframe(df[["name", "price", "country", "year", "material"]], use_container_width=True)
