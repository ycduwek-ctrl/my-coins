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

# עיצוב CSS - גלריה נקייה ותגיות צבעוניות
st.markdown("""
<style>
    /* עיצוב המכולה של התמונה */
    .img-container {
        width: 100%;
        aspect-ratio: 1 / 1;
        overflow: hidden;
        border-radius: 12px;
        cursor: pointer;
        background-color: #f8f9fa;
        position: relative;
    }
    .img-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: opacity 0.2s;
    }
    .img-container:active img { opacity: 0.7; }

    /* שורת תגיות (Chips) */
    .tag-container { display: flex; align-items: center; gap: 5px; margin-top: 8px; direction: rtl; flex-wrap: nowrap; overflow-x: auto; }
    .coin-name { font-weight: bold; border-left: 2px solid #ddd; padding-left: 8px; margin-left: 5px; white-space: nowrap; }
    .price-green { color: #2e7d32; font-weight: bold; margin-left: 10px; white-space: nowrap; }
    
    .chip { padding: 4px 10px; border-radius: 15px; font-size: 0.75em; white-space: nowrap; border: 1px solid rgba(0,0,0,0.05); }
    .chip-country { background-color: #e8f5e9; color: #2e7d32; } 
    .chip-material { background-color: #fff9c4; color: #856404; } 
    .chip-year { background-color: #fce4ec; color: #880e4f; }

    /* עיצוב כפתור ההוספה הירוק */
    div[data-testid="stPopover"] { width: 100%; display: flex; justify-content: center; }
    div[data-testid="stPopover"] > button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        height: auto !important;
        border-radius: 15px !important;
        border: 2px solid #2e7d32 !important;
        background-color: #f1fdf4 !important;
        color: #2e7d32 !important;
        font-size: 60px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0 !important;
    }
    div[data-testid="stPopover"] svg { display: none !important; }
    .add-label { text-align: center; color: #2e7d32; font-weight: bold; margin-top: -5px; width: 100%; }
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

DB_FILE = 'final_coins_db_v14.csv'
COLUMNS = ["id", "name", "price", "country", "material", "year", "images", "comments"]

def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE, dtype=str)
        except: pass
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary.")
    st.stop()

df = load_data()

# --- סינון מהיר בסידבר ---
st.sidebar.title("🔍 סינון")
COUNTRIES = ["ישראל", "המנדט הבריטי", "האימפריה העות'מאנית", "ארה\"ב", "בריטניה", "רוסיה", "ברית המועצות", "אחר"]
MATERIALS = ["כסף", "זהב", "נחושת", "ניקל", "ברונזה", "אלומיניום", "מתכת מעורבת"]

f_country = st.sidebar.multiselect("מדינה:", COUNTRIES)
f_material = st.sidebar.multiselect("חומר:", MATERIALS)
f_year = st.sidebar.text_input("חיפוש לפי שנה:")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

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
    
    # הצגת המטבעות
    for index, row in filtered_df.iterrows():
        col_idx = index % grid_size
        coin_id = str(row['id'])
        with cols[col_idx]:
            img_list = str(row["images"]).split("|")
            
            # ג'אווה סקריפט להחלפת תמונה בלחיצה בלולאה
            js_urls = str(img_list).replace("'", '"') # הכנה ל-JS
            
            click_html = f"""
            <div class="img-container" onclick='
                const urls = {js_urls};
                const img = this.querySelector("img");
                let currentSrc = img.src;
                let idx = urls.indexOf(currentSrc);
                if (idx === -1) idx = 0;
                img.src = urls[(idx + 1) % urls.length];
            '>
                <img src="{img_list[0]}">
            </div>
            """
            st.markdown(click_html, unsafe_allow_html=True)
            
            # שורת מידע
            st.markdown(f"""
            <div class="tag-container">
                <span class="coin-name">{row['name']}</span>
                <span class="price-green">{row['price']} ₪</span>
                <span class="chip chip-country">{row['country']}</span>
                <span class="chip chip-material">{row['material']}</span>
                <span class="chip chip-year">{row['year']}</span>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 ניהול"):
                en = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                ep = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                ec = st.selectbox("מדינה:", COUNTRIES, index=COUNTRIES.index(row['country']) if row['country'] in COUNTRIES else 0, key=f"ec_{coin_id}")
                em = st.selectbox("חומר:", MATERIALS, index=MATERIALS.index(row['material']) if row['material'] in MATERIALS else 0, key=f"em_{coin_id}")
                ey = st.text_input("שנה:", value=str(row["year"]), key=f"ey_{coin_id}")
                
                if st.button("💾 שמור", key=f"sv_{coin_id}"):
                    full_df = load_data()
                    idx_match = full_df[full_df['id'] == coin_id].index[0]
                    full_df.at[idx_match, 'name'], full_df.at[idx_match, 'price'] = en, ep
                    full_df.at[idx_match, 'country'], full_df.at[idx_match, 'material'] = ec, em
                    full_df.at[idx_match, 'year'] = ey
                    save_data(full_df); st.rerun()

                st.divider()
                if st.button("🗑️ מחק פריט", key=f"del_{coin_id}", use_container_width=True):
                    df = df[df['id'] != coin_id]; save_data(df); st.rerun()

    # כפתור הוספה מהירה בסוף
    last_col_idx = len(filtered_df) % grid_size
    with cols[last_col_idx]:
        with st.popover("＋"):
            with st.form("q_add", clear_on_submit=True):
                st.subheader("הוספה מהירה")
                qn = st.text_input("שם המטבע:")
                qp = st.text_input("מחיר:")
                qc = st.selectbox("מדינה:", COUNTRIES)
                qm = st.selectbox("חומר:", MATERIALS)
                qy = st.text_input("שנה:")
                qf = st.file_uploader("תמונות:", accept_multiple_files=True)
                if st.form_submit_button("🚀 שמור"):
                    if qn and qf:
                        urls = [upload_to_cloud(f) for f in qf]
                        new_row = pd.DataFrame([{"id": str(int(time.time())), "name": qn, "price": qp, "country": qc, "material": qm, "year": qy, "images": "|".join(urls)}])
                        save_data(pd.concat([df, new_row], ignore_index=True)); st.rerun()
        st.markdown("<p class='add-label'>הוספה חדש</p>", unsafe_allow_html=True)

with tab2:
    total_val = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
    st.subheader(f"💰 שווי כולל: {total_val:,.0f} ₪")
    st.dataframe(df[["name", "price", "country", "year", "material"]], use_container_width=True)
