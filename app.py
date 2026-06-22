import streamlit as st
import pandas as pd
import os
from PIL import Image
import time

# --- עיצוב אינסטגרם ---
st.set_page_config(page_title="Coin Collection", layout="wide")

st.markdown("""
<style>
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 10px;
    }
    .main { background-color: #fafafa; }
    div[data-testid="stExpander"] { border: none !important; }
</style>
""", unsafe_allow_html=True)

# יצירת תיקייה
IMG_DIR = "coin_images"
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

DB_FILE = 'catalog_data.csv'

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if 'my_price' in df.columns:
            df.rename(columns={'my_price': 'price'}, inplace=True)
        return df
    return pd.DataFrame(columns=["id", "name", "price", "images"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- תפריט צד ---
st.sidebar.title("🖼️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הגלריה", "📸 הוספת מטבע"])

# --- טאב הוספה ---
with tab2:
    st.header("צילום והעלאה")
    
    # משתנה זמני לשמירת שמות הקבצים
    if 'temp_images' not in st.session_state:
        st.session_state.temp_images = []

    name = st.text_input("שם המטבע")
    price = st.text_input("מחיר (₪)")
    
    # מעלה קבצים - בנייד יפתח מצלמה
    uploaded_files = st.file_uploader("📸 צלם תמונה או בחר מהגלריה", accept_multiple_files=True)
    
    if uploaded_files:
        st.write("✅ התמונות נקלטו! תצוגה מקדימה:")
        cols = st.columns(4)
        for i, f in enumerate(uploaded_files):
            cols[i % 4].image(f, width=100)

    if st.button("💾 שמור הכל לקטלוג", use_container_width=True):
        if name and uploaded_files:
            new_paths = []
            for f in uploaded_files:
                # יצירת שם קובץ ייחודי כדי למנוע דריסה
                timestamp = int(time.time())
                file_path = os.path.join(IMG_DIR, f"{timestamp}_{f.name}")
                
                # שמירה באמצעות PIL כדי לוודא שהקובץ תקין
                img = Image.open(f)
                img.save(file_path)
                new_paths.append(file_path)
            
            df = load_data()
            new_entry = {
                "id": len(df) + 1,
                "name": name,
                "price": price,
                "images": "|".join(new_paths)
            }
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df)
            st.success("🎉 נשמר בהצלחה!")
            time.sleep(1)
            st.rerun()
        else:
            st.error("חובה להזין שם ולצלם לפחות תמונה אחת")

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
                
                # הצגת תמונה ראשית
                if os.path.exists(img_list[0]):
                    st.image(img_list[0], use_container_width=True)
                
                # פרטים נוספים בתוך Expander קטן
                with st.expander(f"🔍 {row['name']}"):
                    st.write(f"**מחיר:** {row['price']} ₪")
                    
                    # תמונות נוספות
                    if len(img_list) > 1:
                        for p in img_list:
                            if os.path.exists(p):
                                st.image(p, use_container_width=True)
                    
                    st.divider()
                    # עריכה
                    if st.toggle("✏️ ערוך", key=f"tgl_{idx}"):
                        new_n = st.text_input("שם", value=row["name"], key=f"n_{idx}")
                        new_p = st.text_input("מחיר", value=row["price"], key=f"p_{idx}")
                        
                        # מחיקת תמונות
                        keep = []
                        for i, p in enumerate(img_list):
                            c1, c2 = st.columns([4,1])
                            if os.path.exists(p):
                                c1.image(p, width=60)
                                if not c2.button("🗑️", key=f"delimg_{idx}_{i}"):
                                    keep.append(p)
                        
                        if st.button("💾 שמור שינויים", key=f"save_{idx}"):
                            df.at[idx, "name"] = new_n
                            df.at[idx, "price"] = new_p
                            df.at[idx, "images"] = "|".join(keep)
                            save_data(df)
                            st.rerun()

                    if st.button("🗑️ מחק מטבע", key=f"del_{idx}"):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
