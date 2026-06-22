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
        border-radius: 5px;
        margin-bottom: 0px;
    }
    /* צמצום מרווחים בין אלמנטים */
    .stExpander {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }
    /* הסתרת מסגרות מיותרות */
    [data-testid="stVerticalBlock"] > div:contains("🔍") {
        padding-top: 0px;
    }
</style>
""", unsafe_allow_html=True)

# יצירת תיקייה
if not os.path.exists("coin_images"):
    os.makedirs("coin_images")

DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "price", "images"])

def save_data(df): df.to_csv(DB_FILE, index=False)

# --- תפריט צד (Sidebar) ---
st.sidebar.title("⚙️ הגדרות תצוגה")
grid_size = st.sidebar.slider("כמה מטבעות בשורה?", 1, 4, 3)

# --- טאבים ---
tab1, tab2 = st.tabs(["🖼️ גלריה", "📸 הוספה"])

# --- טאב הוספה ---
with tab2:
    st.header("העלאה לקטלוג")
    with st.container(border=True):
        name = st.text_input("שם", placeholder="שם המטבע")
        price = st.text_input("מחיר", placeholder="₪")
        
        up_files = st.file_uploader("בחר תמונות מהגלריה", accept_multiple_files=True)
        cam_file = st.camera_input("או צלם תמונה")
        
        if st.button("💾 שמור"):
            all_paths = []
            if up_files:
                for f in up_files:
                    p = os.path.join("coin_images", f.name)
                    with open(p, "wb") as file: file.write(f.getvalue())
                    all_paths.append(p)
            if cam_file:
                p = os.path.join("coin_images", f"cam_{cam_file.name}.jpg")
                with open(p, "wb") as file: file.write(cam_file.getvalue())
                all_paths.append(p)
            
            if name and all_paths:
                df = load_data()
                new_row = {"id": len(df)+1, "name": name, "price": price, "images": "|".join(all_paths)}
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success("נוסף!")
                st.rerun()

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        # יצירת גריד דינמי לפי בחירת המשתמש
        cols = st.columns(grid_size)
        for idx, row in df.iterrows():
            with cols[idx % grid_size]:
                img_list = str(row["images"]).split("|")
                # תצוגה ראשית (רק התמונה)
                st.image(img_list[0], use_container_width=True)
                
                # פרטים נוספים (מוסתרים)
                with st.expander(f"🔍 {row['name']}"):
                    st.write(f"💰 מחיר: {row['price']} ₪")
                    
                    # קרוסלה פנימית של שאר התמונות
                    if len(img_list) > 1:
                        st.write("תמונות נוספות:")
                        for extra_img in img_list:
                            st.image(extra_img, use_container_width=True)
                    
                    st.divider()
                    
                    # מצב עריכה
                    edit_col, del_col = st.columns(2)
                    show_edit = edit_col.toggle("✏️", key=f"ed_{idx}")
                    
                    if show_edit:
                        new_n = st.text_input("שם", value=row["name"], key=f"n_{idx}")
                        new_p = st.text_input("מחיר", value=row["price"], key=f"p_{idx}")
                        
                        # ניהול תמונות קיימות
                        keep = []
                        for i, p in enumerate(img_list):
                            c1, c2 = st.columns([4,1])
                            c1.image(p, width=50)
                            if not c2.button("🗑️", key=f"di_{idx}_{i}"):
                                keep.append(p)
                        
                        if st.button("💾", key=f"sv_{idx}"):
                            df.at[idx, "name"] = new_n
                            df.at[idx, "price"] = new_p
                            df.at[idx, "images"] = "|".join(keep)
                            save_data(df)
                            st.rerun()
                        
                        if st.button("🗑️ מחק הכל", key=f"fdel_{idx}"):
                            df.drop(idx).to_csv(DB_FILE, index=False)
                            st.rerun()
