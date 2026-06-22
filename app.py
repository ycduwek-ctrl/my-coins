import streamlit as st
import pandas as pd
import os
from PIL import Image

# --- הגדרות עיצוב אינסטגרם ---
st.set_page_config(page_title="Coin Gallery", layout="wide")

st.markdown("""
<style>
    /* ריבוע 1:1 נקי */
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 8px;
    }
    /* הסתרת כותרות מיותרות ב-Expander */
    .stExpander {
        border: none !important;
        background-color: transparent !important;
    }
    /* כפתור העלאה גדול ונוח */
    .stFileUploader {
        padding-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# יצירת תיקייה
if not os.path.exists("coin_images"):
    os.makedirs("coin_images")

DB_FILE = 'catalog_data.csv'

def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        # תיקון שגיאת שמות העמודות (אם השם ישן, נהפוך לחדש)
        if 'my_price' in df.columns:
            df.rename(columns={'my_price': 'price'}, inplace=True)
        return df
    return pd.DataFrame(columns=["id", "name", "price", "images"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- תפריט צד ---
st.sidebar.title("⚙️ תצוגה")
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["🖼️ גלריה", "📸 הוספת מטבע"])

# --- טאב הוספה (מצלמה מקורית של הפלאפון) ---
with tab2:
    st.header("העלאה לקטלוג")
    with st.container(border=True):
        name = st.text_input("שם / תיאור")
        price = st.text_input("מחיר (₪)")
        
        # שימוש ב-file_uploader. בנייד זה יפתח את המצלמה המקורית
        up_files = st.file_uploader("📸 לחץ כאן לצילום או בחירה מהגלריה", accept_multiple_files=True)
        
        if st.button("💾 שמור לקטלוג"):
            if name and up_files:
                all_paths = []
                for f in up_files:
                    p = os.path.join("coin_images", f"{name}_{f.name}")
                    with open(p, "wb") as file:
                        file.write(f.getvalue())
                    all_paths.append(p)
                
                df = load_data()
                new_row = {"id": len(df)+1, "name": name, "price": price, "images": "|".join(all_paths)}
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("המטבע נוסף בהצלחה!")
                st.rerun()
            else:
                st.error("נא להזין שם ולהעלות לפחות תמונה אחת")

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                # וודא שיש תמונות
                img_list = str(row["images"]).split("|")
                if img_list and os.path.exists(img_list[0]):
                    st.image(img_list[0], use_container_width=True)
                
                # פרטים מוסתרים
                with st.expander(f"🔍 {row['name']}"):
                    st.write(f"**מחיר:** {row['price']} ₪")
                    
                    # הצגת כל שאר התמונות
                    if len(img_list) > 1:
                        st.write("תמונות נוספות:")
                        for p in img_list:
                            if os.path.exists(p):
                                st.image(p, use_container_width=True)
                    
                    st.divider()
                    # עריכה ומחיקה
                    col_e, col_d = st.columns(2)
                    show_edit = col_e.toggle("✏️", key=f"e_{idx}")
                    
                    if show_edit:
                        en = st.text_input("שם", value=row["name"], key=f"en_{idx}")
                        ep = st.text_input("מחיר", value=row["price"], key=f"ep_{idx}")
                        
                        # ניהול תמונות ספציפיות
                        keep = []
                        for i, p in enumerate(img_list):
                            c1, c2 = st.columns([4,1])
                            if os.path.exists(p):
                                c1.image(p, width=60)
                                if not c2.button("🗑️", key=f"di_{idx}_{i}"):
                                    keep.append(p)
                        
                        if st.button("💾 שמור שינויים", key=f"s_{idx}"):
                            df.at[idx, "name"] = en
                            df.at[idx, "price"] = ep
                            df.at[idx, "images"] = "|".join(keep)
                            save_data(df)
                            st.rerun()

                    if st.button("🗑️ מחק מטבע", key=f"del_{idx}"):
                        df.drop(idx).to_csv(DB_FILE, index=False)
                        st.rerun()
