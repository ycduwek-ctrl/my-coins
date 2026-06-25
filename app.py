import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import os
from PIL import Image
import io
import time

# --- הגדרות דף ---
st.set_page_config(page_title="Israel Coin Index", layout="wide")

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

# עיצוב CSS מתקדם
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
    
    /* תגיות סינון מהיר */
    .filter-tag { background: #e1f5fe; color: #01579b; padding: 4px 12px; border-radius: 15px; font-size: 0.85em; margin: 2px; display: inline-block; }
    .price-bold { color: #2e7d32; font-weight: bold; }
    
    .stPopover > button { width: 100% !important; aspect-ratio: 1/1 !important; border-radius: 12px !important; border: 2px dashed #ddd !important; font-size: 40px !important; color: #bbb !important; }
</style>
""", unsafe_allow_html=True)

# פונקציות בסיס
def upload_to_cloud(file):
    img = Image.open(file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    img = img.crop(((w-s)/2, (h-s)/2, (w+s)/2, (h+s)/2))
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    res = cloudinary.uploader.upload(buf.getvalue())
    return res['secure_url']

# שימוש בקובץ חדש לתמיכה בסינונים
DB_FILE = 'coins_v4_filtered.csv'
COLUMNS = ["id", "name", "price", "country", "year", "type", "material", "condition", "period", "images", "comments"]

def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE, dtype=str)
        except: pass
    return pd.DataFrame(columns=COLUMNS)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

if not READY:
    st.error("⚠️ חסרים פרטי Cloudinary.")
    st.stop()

# טעינת נתונים
df = load_data()

# --- תפריט צד: מערכת סינונים (UX המלצות) ---
st.sidebar.title("🔍 חיפוש וסינון")

# קבוצה 1: סינון מהיר
with st.sidebar.expander("⚡ סינון מהיר", expanded=True):
    f_country = st.multiselect("מדינה / אזור:", ["ישראל", "ארה\"ב", "בריטניה", "אירופה", "אסיה", "עתיק"], key="f_country")
    f_condition = st.multiselect("מצב המטבע:", ["חדש (UNC)", "כמעט חדש", "משומש", "שחוק"], key="f_cond")
    f_max_price = st.number_input("מחיר מקסימלי (₪):", value=0, step=50)

# קבוצה 2: סינון מתקדם
with st.sidebar.expander("🛠️ סינון מתקדם"):
    f_year = st.text_input("שנה ספציפית:", key="f_year")
    f_material = st.multiselect("חומר:", ["נחושת", "כסף", "זהב", "ניקל", "ברונזה", "אלומיניום"], key="f_mat")

# קבוצה 3: סינון עניין ותקופה
with st.sidebar.expander("⏳ תקופה וסוג"):
    f_period = st.multiselect("תקופה:", ["עות'מאני", "מנדט בריטי", "קום המדינה", "מודרני"], key="f_per")
    f_type = st.multiselect("סוג:", ["רגיל", "זיכרון", "אסימון", "שטר"], key="f_type")

st.sidebar.divider()
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 2)

# --- לוגיקת סינון ---
filtered_df = df.copy()
if f_country: filtered_df = filtered_df[filtered_df['country'].isin(f_country)]
if f_condition: filtered_df = filtered_df[filtered_df['condition'].isin(f_condition)]
if f_type: filtered_df = filtered_df[filtered_df['type'].isin(f_type)]
if f_material: filtered_df = filtered_df[filtered_df['material'].isin(f_material)]
if f_period: filtered_df = filtered_df[filtered_df['period'].isin(f_period)]
if f_year: filtered_df = filtered_df[filtered_df['year'] == f_year]
if f_max_price > 0:
    filtered_df['price_num'] = pd.to_numeric(filtered_df['price'], errors='coerce').fillna(0)
    filtered_df = filtered_df[filtered_df['price_num'] <= f_max_price]

# --- ממשק ראשי ---
tab1, tab2 = st.tabs(["💎 הגלריה", "➕ ניהול מלא"])

with tab1:
    # תגיות סינון מהיר (UI)
    st.write("🔥 **גישה מהירה:**")
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🇮🇱 מטבעות ישראל"): f_country = ["ישראל"]; st.rerun()
    if c2.button("🥈 מטבעות כסף"): f_material = ["כסף"]; st.rerun()
    if c3.button("💰 עד 100 ₪"): f_max_price = 100; st.rerun()
    if c4.button("🧹 נקה הכל"): st.rerun()

    st.divider()
    
    # חישוב שווי מסונן
    total_val = pd.to_numeric(filtered_df['price'], errors='coerce').sum()
    st.write(f"נמצאו **{len(filtered_df)}** מטבעות | שווי תצוגה: **{total_val:,.0f} ₪**")

    cols = st.columns(grid_size)
    
    # הצגת המטבעות המסוננים
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
            
            st.markdown(f"**{row['name']}** | <span class='price-bold'>{row['price']} ₪</span>", unsafe_allow_html=True)
            st.markdown(f"<span class='filter-tag'>{row['country']}</span><span class='filter-tag'>{row['material']}</span>", unsafe_allow_html=True)

            with st.expander("🔍 פרטים וניהול"):
                # עריכה מורחבת
                e_name = st.text_input("שם:", value=str(row["name"]), key=f"en_{coin_id}")
                e_price = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{coin_id}")
                e_country = st.selectbox("מדינה:", ["ישראל", "ארה\"ב", "בריטניה", "אירופה", "אסיה", "עתיק"], index=0, key=f"ec_{coin_id}")
                e_mat = st.selectbox("חומר:", ["נחושת", "כסף", "זהב", "ניקל", "ברונזה", "אלומיניום"], key=f"em_{coin_id}")
                e_comm = st.text_area("תגובה:", value=str(row["comments"]), key=f"ect_{coin_id}")
                
                if st.button("💾 שמור שינויים", key=f"sv_{coin_id}"):
                    df.loc[df['id'] == coin_id, ["name", "price", "country", "material", "comments"]] = [e_name, e_price, e_country, e_mat, e_comm]
                    save_data(df); st.rerun()

                if st.button("🗑️ מחק", key=f"del_{coin_id}"):
                    df = df[df['id'] != coin_id]; save_data(df); st.rerun()

    # כפתור הוספה בסוף (גם הוא עם השדות החדשים)
    last_col = len(filtered_df) % grid_size
    with cols[last_col]:
        with st.popover("➕"):
            st.subheader("הוספה מהירה")
            q_name = st.text_input("שם המטבע:")
            q_price = st.text_input("מחיר:")
            q_country = st.selectbox("מדינה:", ["ישראל", "ארה\"ב", "בריטניה", "אירופה", "אסיה", "עתיק"])
            q_mat = st.selectbox("חומר:", ["נחושת", "כסף", "זהב", "ניקל", "ברונזה", "אלומיניום"])
            q_files = st.file_uploader("תמונות:", accept_multiple_files=True)
            if st.button("🚀 שמור"):
                if q_name and q_files:
                    urls = [upload_to_cloud(f) for f in q_files]
                    new_row = pd.DataFrame([{"id": str(int(time.time())), "name": q_name, "price": q_price, "country": q_country, "material": q_mat, "images": "|".join(urls)}])
                    save_data(pd.concat([df, new_row], ignore_index=True)); st.rerun()
        st.write("**הוסף מטבע**")

with tab2:
    st.header("ממשק ניהול מלא")
    st.write("כאן תוכל לראות את כל הטבלה ולבצע פעולות גורפות.")
    st.dataframe(df)
