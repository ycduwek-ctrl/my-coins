import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import cloudinary
import cloudinary.uploader
from PIL import Image
import io
import time
import json
import re
import base64
import requests

st.set_page_config(page_title="Coin Index Pro", layout="wide")

try:
    cloudinary.config(
        cloud_name=st.secrets["CLOUDINARY_CLOUD_NAME"],
        api_key=st.secrets["CLOUDINARY_API_KEY"],
        api_secret=st.secrets["CLOUDINARY_API_SECRET"]
    )
    CLOUDINARY_READY = True
except:
    CLOUDINARY_READY = False

OPENROUTER_KEY = st.secrets.get("GEMINI_API_KEY", "")
AI_READY = bool(OPENROUTER_KEY)

SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
SHEET_URL = "https://docs.google.com/spreadsheets/d/1F8wYC4Q9r_kIgkFZMzrOWueVLYVaky60Vf7cfsjbs1M"

COUNTRIES = ["ישראל", "המנדט הבריטי", "האימפריה העות'מאנית", 'ארה"ב', "בריטניה", "רוסיה", "ברית המועצות", "אחר"]
MATERIALS = ["כסף", "זהב", "נחושת", "ניקל", "ברונזה", "אלומיניום", "מתכת מעורבת"]

def get_client():
    info = {
        "type": "service_account",
        "project_id": "voltaic-tooling-500108-b5",
        "private_key_id": st.secrets["connections"]["gsheets"]["private_key_id"],
        "private_key": st.secrets["connections"]["gsheets"]["private_key"],
        "client_email": st.secrets["connections"]["gsheets"]["client_email"],
        "client_id": st.secrets["connections"]["gsheets"]["client_id"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": st.secrets["connections"]["gsheets"]["token_uri"],
    }
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)

def get_data():
    try:
        client = get_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("coins")
        data = ws.get_all_records()
        if not data:
            return pd.DataFrame(columns=["id","name","price","country","material","year","images","comments"])
        return pd.DataFrame(data).astype(str)
    except Exception as e:
        st.error(f"שגיאה: {e}")
        return None

def save_data(df):
    try:
        client = get_client()
        sh = client.open_by_url(SHEET_URL)
        ws = sh.worksheet("coins")
        ws.clear()
        ws.update([df.columns.tolist()] + df.fillna("").values.tolist())
        return True
    except Exception as e:
        st.error(f"שגיאת שמירה: {e}")
        return False

def compress_image(file):
    file.seek(0)
    img = Image.open(file).convert('RGB')
    img.thumbnail((600, 600), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=75)
    buf.seek(0)
    return buf

def upload_to_cloud(file):
    try:
        buf = compress_image(file)
        res = cloudinary.uploader.upload(buf.getvalue())
        return res['secure_url']
    except Exception as e:
        st.error(f"שגיאת העלאה: {e}")
        return None

def identify_coin(front_file, back_file=None):
    try:
        def file_to_b64(f):
            buf = compress_image(f)
            return base64.b64encode(buf.getvalue()).decode('utf-8')

        content = [
            {
                "type": "text",
                "text": """אתה מומחה למטבעות עתיקים. זהה את המטבע ותחזיר JSON בלבד ללא שום טקסט נוסף:
{"name":"שם המטבע בעברית","country":"אחת מ: ישראל / המנדט הבריטי / האימפריה העות'מאנית / ארה\"ב / בריטניה / רוסיה / ברית המועצות / אחר","year":"שנה","material":"אחד מ: כסף / זהב / נחושת / ניקל / ברונזה / אלומיניום / מתכת מעורבת","price":"מחיר משוער בשקלים"}"""
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{file_to_b64(front_file)}"}
            }
        ]

        if back_file:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{file_to_b64(back_file)}"}
            })

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemma-4-31b-it:free",
                "messages": [{"role": "user", "content": content}]
            },
            timeout=30
        )

        result = response.json()
        text = result['choices'][0]['message']['content'].strip()
        text = re.sub(r'```json|```', '', text).strip()
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except Exception as e:
        result_raw = response.json()
        st.error(f"תשובת API: {result_raw}")
        return None

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700&display=swap');
    * { font-family: 'Heebo', sans-serif; }
    .gallery-container { width: 100%; aspect-ratio: 1/1; overflow-x: auto; display: flex; scroll-snap-type: x mandatory; border-radius: 16px 16px 0 0; background-color: #f0f0f0; }
    .gallery-container::-webkit-scrollbar { display: none; }
    .gallery-item { flex: 0 0 100%; scroll-snap-align: start; display: flex; align-items: center; justify-content: center; }
    .gallery-item img { width: 100%; height: 100%; object-fit: cover; }
    .coin-info { padding: 10px 12px 6px 12px; direction: rtl; }
    .tags-row { display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; direction: rtl; }
    .chip { padding: 3px 10px; border-radius: 20px; font-size: 0.72em; font-weight: 600; }
    .chip-country { background-color: #e8f5e9; color: #2e7d32; }
    .chip-material { background-color: #fff8e1; color: #f57f17; }
    .chip-year { background-color: #fce4ec; color: #c62828; }
    div[data-testid="stPopover"] > button {
        width: 100% !important; aspect-ratio: 1/1 !important;
        border: 2.5px dashed #81c784 !important;
        background: linear-gradient(135deg, #f1fdf4, #e8f5e9) !important;
        color: #4caf50 !important; font-size: 3em !important;
        border-radius: 16px !important; box-shadow: none !important;
    }
    .ai-box { background: linear-gradient(135deg, #e8f4fd, #f3e5f5); border-radius: 12px; padding: 12px; margin: 8px 0; border: 1px solid #ce93d8; direction: rtl; }
</style>
""", unsafe_allow_html=True)

if not CLOUDINARY_READY:
    st.error("❌ שגיאה: פרטי Cloudinary לא הוגדרו")
    st.stop()

df = get_data()
if df is None:
    st.stop()

with st.sidebar:
    st.markdown("### 🔍 סינון")
    f_country = st.multiselect("מדינה:", COUNTRIES)
    f_material = st.multiselect("חומר:", MATERIALS)
    f_year = st.text_input("שנה:")
    st.divider()
    grid_size = st.slider("מטבעות בשורה", 1, 4, 2)
    st.divider()
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 גיבוי CSV", csv, "coins_backup.csv", use_container_width=True)

filtered_df = df.copy()
if f_country: filtered_df = filtered_df[filtered_df['country'].isin(f_country)]
if f_material: filtered_df = filtered_df[filtered_df['material'].isin(f_material)]
if f_year: filtered_df = filtered_df[filtered_df['year'].str.contains(f_year, na=False)]

tab1, tab2 = st.tabs(["🪙 הגלריה", "📜 רשימה וסיכום"])

with tab1:
    all_items = list(filtered_df.iterrows()) if not filtered_df.empty else []
    total_items = len(all_items) + 1
    rows = (total_items + grid_size - 1) // grid_size

    item_index = 0
    for row in range(rows):
        cols = st.columns(grid_size)
        for col_i in range(grid_size):
            if item_index < len(all_items):
                index, coin = all_items[item_index]
                with cols[col_i]:
                    img_list = [u for u in str(coin["images"]).split("|") if u.startswith("http")]
                    if img_list:
                        items_html = "".join([f'<div class="gallery-item"><img src="{url}" loading="lazy"></div>' for url in img_list])
                        st.markdown(f'<div class="gallery-container">{items_html}</div>', unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="coin-info">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:700; color:#1a1a1a;">{coin['name']}</span>
                            <span style="color:#2e7d32; font-weight:700;">{coin['price']} ₪</span>
                        </div>
                        <div class="tags-row">
                            <span class="chip chip-country">🌍 {coin['country']}</span>
                            <span class="chip chip-material">⚗️ {coin['material']}</span>
                            <span class="chip chip-year">📅 {coin['year']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    with st.expander("✏️ עריכה"):
                        coin_id = str(coin['id'])
                        e_n = st.text_input("שם:", value=str(coin["name"]), key=f"n_{coin_id}")
                        e_p = st.text_input("מחיר (₪):", value=str(coin["price"]), key=f"p_{coin_id}")
                        cur_country = coin['country'] if coin['country'] in COUNTRIES else COUNTRIES[0]
                        e_c = st.selectbox("מדינה:", COUNTRIES, index=COUNTRIES.index(cur_country), key=f"c_{coin_id}")
                        cur_material = coin['material'] if coin['material'] in MATERIALS else MATERIALS[0]
                        e_m = st.selectbox("חומר:", MATERIALS, index=MATERIALS.index(cur_material), key=f"m_{coin_id}")
                        e_y = st.text_input("שנה:", value=str(coin["year"]), key=f"y_{coin_id}")

                        cur_imgs = [u for u in str(coin["images"]).split("|") if u.startswith("http")]
                        if cur_imgs:
                            st.markdown("**תמונות קיימות:**")
                        imgs_to_keep = []
                        for i, url in enumerate(cur_imgs):
                            col_img, col_del = st.columns([3, 1])
                            with col_img:
                                st.image(url, width=80)
                            with col_del:
                                if not st.checkbox("מחק", key=f"del_img_{coin_id}_{i}"):
                                    imgs_to_keep.append(url)

                        new_imgs = st.file_uploader("הוסף תמונות:", accept_multiple_files=True, key=f"imgs_{coin_id}", type=["jpg","jpeg","png","webp"])

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("💾 שמור", key=f"s_{coin_id}", use_container_width=True):
                                with st.spinner("שומר..."):
                                    new_urls = []
                                    for f in (new_imgs or []):
                                        url = upload_to_cloud(f)
                                        if url:
                                            new_urls.append(url)
                                    all_imgs = imgs_to_keep + new_urls
                                    current_df = get_data()
                                    idx = current_df[current_df['id'] == coin_id].index[0]
                                    current_df.at[idx, 'name'] = e_n
                                    current_df.at[idx, 'price'] = e_p
                                    current_df.at[idx, 'country'] = e_c
                                    current_df.at[idx, 'material'] = e_m
                                    current_df.at[idx, 'year'] = e_y
                                    current_df.at[idx, 'images'] = "|".join(all_imgs)
                                    if save_data(current_df):
                                        st.success("✅ נשמר!")
                                        time.sleep(0.5)
                                        st.rerun()
                        with col2:
                            if st.button("🗑️ מחק", key=f"d_{coin_id}", use_container_width=True):
                                current_df = get_data()
                                current_df = current_df[current_df['id'] != coin_id]
                                if save_data(current_df):
                                    st.rerun()

                item_index += 1

            elif item_index == len(all_items):
                with cols[col_i]:
                    with st.popover("＋", use_container_width=True):
                        st.markdown("### ➕ הוספת מטבע חדש")

                        if AI_READY:
                            st.markdown("#### 🤖 זיהוי אוטומטי עם AI")
                            col_f, col_b = st.columns(2)
                            with col_f:
                                st.markdown("**פנים:**")
                                front_img = st.file_uploader("", type=["jpg","jpeg","png","webp"], key="ai_front")
                                if front_img:
                                    front_img.seek(0)
                                    st.image(Image.open(front_img), use_container_width=True)
                            with col_b:
                                st.markdown("**גב (אופציונלי):**")
                                back_img = st.file_uploader("", type=["jpg","jpeg","png","webp"], key="ai_back")
                                if back_img:
                                    back_img.seek(0)
                                    st.image(Image.open(back_img), use_container_width=True)

                            if front_img:
                                if st.button("✨ זהה מטבע", use_container_width=True):
                                    with st.spinner("🔍 מזהה..."):
                                        front_img.seek(0)
                                        if back_img:
                                            back_img.seek(0)
                                        result = identify_coin(front_img, back_img if back_img else None)
                                        if result:
                                            st.session_state['ai_result'] = result
                                            st.session_state['ai_front'] = front_img
                                            st.session_state['ai_back'] = back_img
                                            st.success("✅ זוהה!")

                            if 'ai_result' in st.session_state:
                                r = st.session_state['ai_result']
                                st.markdown(f"""
                                <div class="ai-box">
                                    <b>🤖 {r.get('name','')}</b><br>
                                    🌍 {r.get('country','')} | ⚗️ {r.get('material','')} | 📅 {r.get('year','')} | 💰 ~{r.get('price','')} ₪
                                </div>
                                """, unsafe_allow_html=True)
                            st.divider()

                        with st.form("add_new", clear_on_submit=True):
                            ai = st.session_state.get('ai_result', {})
                            qn = st.text_input("שם המטבע:", value=ai.get('name', ''))
                            qp = st.text_input("מחיר (₪):", value=str(ai.get('price', '')))
                            default_country = ai.get('country', COUNTRIES[0])
                            if default_country not in COUNTRIES:
                                default_country = COUNTRIES[0]
                            qc = st.selectbox("מדינה:", COUNTRIES, index=COUNTRIES.index(default_country))
                            default_material = ai.get('material', MATERIALS[0])
                            if default_material not in MATERIALS:
                                default_material = MATERIALS[0]
                            qm = st.selectbox("חומר:", MATERIALS, index=MATERIALS.index(default_material))
                            qy = st.text_input("שנה:", value=str(ai.get('year', '')))
                            qf = st.file_uploader("תמונות נוספות:", accept_multiple_files=True, type=["jpg","jpeg","png","webp"])

                            if st.form_submit_button("🚀 הוסף מטבע", use_container_width=True):
                                if qn:
                                    with st.spinner('מעלה...'):
                                        urls = []
                                        for key in ['ai_front', 'ai_back']:
                                            f = st.session_state.get(key)
                                            if f:
                                                f.seek(0)
                                                url = upload_to_cloud(f)
                                                if url:
                                                    urls.append(url)
                                        for f in (qf or []):
                                            url = upload_to_cloud(f)
                                            if url:
                                                urls.append(url)
                                        new_row = pd.DataFrame([{
                                            "id": str(int(time.time())),
                                            "name": qn, "price": qp,
                                            "country": qc, "material": qm,
                                            "year": qy,
                                            "images": "|".join(urls) if urls else "",
                                            "comments": ""
                                        }])
                                        if save_data(pd.concat([df, new_row], ignore_index=True)):
                                            for key in ['ai_result','ai_front','ai_back']:
                                                st.session_state.pop(key, None)
                                            st.rerun()
                                else:
                                    st.warning("נא להזין שם")

                    st.markdown("<p style='text-align:center; color:#4caf50; font-size:0.8em; font-weight:600; margin-top:4px;'>הוסף חדש</p>", unsafe_allow_html=True)
                item_index += 1

with tab2:
    total_val = pd.to_numeric(df['price'].str.replace(r'[^\d.]', '', regex=True), errors='coerce').sum()
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 שווי כולל", f"{total_val:,.0f} ₪")
    col2.metric("🪙 סה״כ מטבעות", len(df))
    col3.metric("🔍 מסוננים", len(filtered_df))
    st.divider()
    st.dataframe(df[["name", "price", "country", "material", "year"]], use_container_width=True, hide_index=True)
