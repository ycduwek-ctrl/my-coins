import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import cloudinary
import cloudinary.uploader
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
    CLOUDINARY_READY = True
except:
    CLOUDINARY_READY = False

# הגדרת Google Sheets
def get_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # קריאה עם ttl=0 כדי למנוע זיכרון ישן
        return conn.read(worksheet="coins", ttl=0).astype(str)
    except Exception as e:
        return None

def save_data(df):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        conn.update(worksheet="coins", data=df)
        return True
    except:
        return False

# עיצוב CSS - מראה אינסטגרם + גלילה חלקה
st.markdown("""
<style>
    .gallery-container { width: 100%; aspect-ratio: 1/1; overflow-x: auto; display: flex; scroll-snap-type: x mandatory; border-radius: 12px; background-color: #f8f9fa; }
    .gallery-container::-webkit-scrollbar { height: 4px; }
    .gallery-item { flex: 0 0 100%; scroll-snap-align: start; display: flex; align-items: center; justify-content: center; }
    .gallery-item img { width: 100%; height: 100%; object-fit: cover; border-radius: 12px; }
    .tag-container { display: flex; align-items: center; gap: 5px; margin-top: 8px; direction: rtl; }
    .price-green { color: #2e7d32; font-weight: bold; margin-left: 10px; }
    .chip { padding: 4px 10px; border-radius: 15px; font-size: 0.75em; border: 1px solid rgba(0,0,0,0.05); }
    .chip-country { background-color: #e8f5e9; color: #2e7d32; } 
    .chip-material { background-color: #fff9c4; color: #856404; } 
    .chip-year { background-color: #fce4ec; color: #880e4f; }
    div[data-testid="stPopover"] > button { width: 100% !important; aspect-ratio: 1 / 1 !important; border: 2px solid #2e7d32 !important; background-color: #f1fdf4 !important; color: #2e7d32 !important; font-size: 60px !important; border-radius: 15px !important; }
    .add-label { text-align: center; color: #2e7d32; font-weight: bold; margin-top: -5px; }
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

# --- טעינת נתונים ---
if not CLOUDINARY_READY:
    st.error("❌ שגיאה: פרטי Cloudinary לא הוגדרו ב-Secrets")
    st.stop()

df = get_data()

if df is None:
    st.warning("⚠️ לא מצליח להתחבר לגוגל שיטס. וודא שהקובץ משותף כ-'Anyone with link' וששם הלשונית הוא 'coins'.")
    st.stop()

# --- תפריט צד ---
st.sidebar.title("🔍 סינון")
COUNTRIES = ["ישראל", "המנדט הבריטי", "האימפריה העות'מאנית", "ארה\"ב", "בריטניה", "רוסיה", "ברית המועצות", "אחר"]
MATERIALS = ["כסף", "זהב", "נחושת", "ניקל", "ברונזה", "אלומיניום", "מתכת מעורבת"]

f_country = st.sidebar.multiselect("מדינה:", COUNTRIES)
f_material = st.sidebar.multiselect("חומר:", MATERIALS)
f_year = st.sidebar.text_input("חיפוש לפי שנה:")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

if not df.empty:
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button("📥 הורד גיבוי (CSV)", csv, "coins_backup.csv", use_container_width=True)

# לוגיקת סינון
filtered_df = df.copy()
if f_country: filtered_df = filtered_df[filtered_df['country'].isin(f_country)]
if f_material: filtered_df = filtered_df[filtered_df['material'].isin(f_material)]
if f_year: filtered_df = filtered_df[filtered_df['year'].str.contains(f_year, na=False)]

tab1, tab2 = st.tabs(["🪙 הגלריה", "📜 רשימה וסיכום"])

with tab1:
    if filtered_df.empty or (len(filtered_df) == 1 and filtered_df.iloc[0].isnull().all()):
        st.info("הקטלוג ריק. השתמש בכפתור ה-"+" למטה כדי להוסיף מטבע.")
    else:
        cols = st.columns(grid_size)
        for index, row in filtered_df.iterrows():
            with cols[index % grid_size]:
                img_list = str(row["images"]).split("|")
                items_html = "".join([f'<div class="gallery-item"><img src="{url}"></div>' for url in img_list])
                st.markdown(f'<div class="gallery-container">{items_html}</div>', unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="tag-container">
                    <span style="font-weight:bold;">{row['name']}</span>
                    <span class="price-green">{row['price']} ₪</span>
                    <span class="chip chip-country">{row['country']}</span>
                    <span class="chip chip-material">{row['material']}</span>
                    <span class="chip chip-year">{row['year']}</span>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("🔍 ניהול"):
                    coin_id = str(row['id'])
                    e_n = st.text_input("שם:", value=str(row["name"]), key=f"n_{coin_id}")
                    e_p = st.text_input("מחיר:", value=str(row["price"]), key=f"p_{coin_id}")
                    
                    if st.button("💾 שמור שינויים", key=f"s_{coin_id}"):
                        current_df = get_data()
                        idx = current_df[current_df['id'] == coin_id].index[0]
                        current_df.at[idx, 'name'], current_df.at[idx, 'price'] = e_n, e_p
                        if save_data(current_df): st.rerun()

                    if st.button("🗑️ מחק", key=f"d_{coin_id}"):
                        current_df = get_data()
                        current_df = current_df[current_df['id'] != coin_id]
                        if save_data(current_df): st.rerun()

    # כפתור הוספה בסוף הגלריה
    last_col = len(filtered_df) % grid_size
    with st.columns(grid_size)[last_col]:
        with st.popover("＋"):
            with st.form("add_new", clear_on_submit=True):
                st.subheader("הוספה מהירה")
                qn, qp = st.text_input("שם:"), st.text_input("מחיר:")
                qc = st.selectbox("מדינה:", COUNTRIES)
                qm = st.selectbox("חומר:", MATERIALS)
                qy = st.text_input("שנה:")
                qf = st.file_uploader("תמונות:", accept_multiple_files=True)
                if st.form_submit_button("🚀 שמור לענן"):
                    if qn and qf:
                        with st.spinner('מעלה לענן...'):
                            urls = [upload_to_cloud(f) for f in qf]
                            new_row = pd.DataFrame([{"id": str(int(time.time())), "name": qn, "price": qp, "country": qc, "material": qm, "year": qy, "images": "|".join(urls), "comments": ""}])
                            if save_data(pd.concat([df, new_row], ignore_index=True)): st.rerun()
        st.write("<p class='add-label'>הוסף חדש</p>", unsafe_allow_html=True)

with tab2:
    total_val = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
    st.subheader(f"💰 שווי כולל: {total_val:,.0f} ₪")
    st.dataframe(df[["name", "price", "country", "year"]], use_container_width=True)
