import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import base64
import io

# --- הגדרות עיצוב מתקדמות ---
st.set_page_config(page_title="Coin Collection Pro", layout="wide")

def get_image_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

st.markdown("""
<style>
    .scroll-container {
        display: flex;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        gap: 5px;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
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
        border-radius: 12px;
        cursor: pointer;
    }
    /* עיצוב כפתור הלייק */
    .like-btn { font-size: 24px; cursor: pointer; }
</style>
""", unsafe_allow_html=True)

# פונקציות עיבוד
IMG_DIR = "coin_images"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)
DB_FILE = 'catalog_data_v2.csv'

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments", "likes"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def process_image(uploaded_file):
    img = Image.open(uploaded_file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    l, t = (w-s)/2, (h-s)/2
    return img.crop((l, t, l+s, t+s))

# --- תפריט צד ---
st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הקטלוג", "➕ הוספה"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת מטבע")
    c_name = st.text_input("שם המטבע:", key="add_n")
    c_price = st.text_input("מחיר (₪):", key="add_p")
    up_files = st.file_uploader("בחר תמונות מהגלריה:", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
    
    if st.button("💾 שמור הכל", use_container_width=True):
        if c_name and up_files:
            paths = []
            for f in up_files:
                sq = process_image(f)
                p = os.path.join(IMG_DIR, f"coin_{int(time.time()*1000)}_{f.name}")
                sq.save(p)
                paths.append(p)
            df = load_data()
            new = {"id": len(df)+1, "name": c_name, "price": c_price, "images": "|".join(paths), "comments": "", "likes": 0}
            save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
            st.success("נוסף בהצלחה!")
            st.rerun()

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                img_list = str(row["images"]).split("|")
                
                # --- קרוסלת Swipe ---
                carousel_html = '<div class="scroll-container">'
                for img_p in img_list:
                    if os.path.exists(img_p):
                        base64_img = get_image_base64(img_p)
                        carousel_html += f'<div class="scroll-item"><img src="data:image/jpeg;base64,{base64_img}"></div>'
                carousel_html += '</div>'
                st.markdown(carousel_html, unsafe_allow_html=True)
                
                # שורת לייק ושם מהירה
                l_col, n_col = st.columns([1, 4])
                if l_col.button(f"{'🟡' if row['likes'] > 0 else '🪙'}", key=f"like_{idx}"):
                    df.at[idx, 'likes'] = 1 - row['likes']
                    save_data(df)
                    st.rerun()
                n_col.write(f"**{row['name']}**")

                # --- חלונית ניהול ופרטים ---
                with st.expander("🔍 פרטים, תגובות וזום"):
                    # עריכה בסיסית
                    en = st.text_input("שם:", value=str(row["name"]), key=f"en_{idx}")
                    ep = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{idx}")
                    
                    # תגובות
                    comment = st.text_area("הערות / תגובות:", value=str(row["comments"]), key=f"com_{idx}")
                    
                    if st.button("💾 שמור שינויים ותגובה", key=f"sv_{idx}"):
                        df.at[idx, "name"], df.at[idx, "price"], df.at[idx, "comments"] = en, ep, comment
                        save_data(df)
                        st.toast("עודכן!")

                    st.divider()
                    st.write("🖼️ צפייה בזום (לחץ להגדלה):")
                    # כאן המשתמש יכול ללחוץ על תמונה ו-Streamlit יפתח אותה למסך מלא עם זום
                    for p in img_list:
                        if os.path.exists(p):
                            st.image(p, use_container_width=True)

                    st.divider()
                    # הוספת תמונות חדשות למטבע קיים
                    more_f = st.file_uploader("➕ הוסף תמונות למטבע זה:", accept_multiple_files=True, key=f"mf_{idx}")
                    if st.button("✅ הוסף תמונות", key=f"am_{idx}"):
                        if more_f:
                            new_paths = img_list
                            for f in more_f:
                                sq = process_image(f)
                                np = os.path.join(IMG_DIR, f"ex_{int(time.time())}_{f.name}")
                                sq.save(np)
                                new_paths.append(np)
                            df.at[idx, "images"] = "|".join(new_paths)
                            save_data(df)
                            st.rerun()

                    if st.button("❌ מחק הכל", key=f"del_{idx}", use_container_width=True):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
