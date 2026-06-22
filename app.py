import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import io

# --- הגדרות עיצוב למראה נקי ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

st.markdown("""
<style>
    /* ריבוע 1:1 נקי לגלריה */
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 8px;
        margin-bottom: 0px;
    }
    /* עיצוב החלונית הנפתחת (Expander) */
    .stExpander {
        border: none !important;
        background-color: #f9f9f9 !important;
        border-radius: 10px !important;
        margin-top: 5px;
    }
    /* ביטול רווחים מיותרים בטאבים */
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
</style>
""", unsafe_allow_html=True)

# פונקציה לחיתוך לריבוע (עבור תמונות שמועלות מהגלריה)
def process_image(uploaded_file):
    img = Image.open(uploaded_file)
    # המרת תמונה ל-RGB (למקרה שהיא בפורמט אחר)
    img = img.convert('RGB')
    w, h = img.size
    s = min(w, h)
    l, t = (w-s)/2, (h-s)/2
    return img.crop((l, t, l+s, t+s))

IMG_DIR = "coin_images"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)

DB_FILE = 'catalog_data.csv'
def load_data():
    if os.path.exists(DB_FILE): return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "price", "images"])

def save_data(df): df.to_csv(DB_FILE, index=False)

# --- תפריט צד (Sidebar) ---
st.sidebar.title("🖼️ הגדרות תצוגה")
view_mode = st.sidebar.radio("סגנון תצוגה:", ["גלריה (אינסטגרם)", "רשימה מפורטת"])
grid_size = st.sidebar.slider("מטבעות בשורה (בגלריה)", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הקטלוג שלי", "➕ הוספת מטבע"])

# --- טאב הוספה (העלאה מרובה מהגלריה) ---
with tab2:
    st.header("הוספת מטבע חדש")
    with st.container(border=True):
        c_name = st.text_input("שם המטבע:", key="add_n")
        c_price = st.text_input("מחיר (₪):", key="add_p")
        
        # בחירת כמה תמונות שרוצים מהגלריה/קבצים בבת אחת
        up_files = st.file_uploader("📸 בחר את כל תמונות המטבע:", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])
        
        if st.button("💾 שמור לקטלוג", use_container_width=True):
            if c_name and up_files:
                final_paths = []
                for f in up_files:
                    # עיבוד התמונה לריבוע ושמירה
                    sq_img = process_image(f)
                    timestamp = int(time.time() * 1000)
                    f_path = os.path.join(IMG_DIR, f"coin_{timestamp}_{f.name}")
                    sq_img.save(f_path)
                    final_paths.append(f_path)
                
                df = load_data()
                new_row = {"id": len(df)+1, "name": c_name, "price": c_price, "images": "|".join(final_paths)}
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success(f"המטבע '{c_name}' נוסף בהצלחה!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("חובה להזין שם ולהעלות לפחות תמונה אחת.")

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        if view_mode == "גלריה (אינסטגרם)":
            cols = st.columns(grid_size)
            for idx, row in df.iterrows():
                with cols[idx % grid_size]:
                    img_list = str(row["images"]).split("|")
                    # מציג רק תמונה ראשית
                    if os.path.exists(img_list[0]):
                        st.image(img_list[0], use_container_width=True)
                    
                    # חלונית ניהול (מוסתרת)
                    with st.expander(f"🔍 ניהול ופרטים"):
                        # עריכה בראש החלונית
                        edit_n = st.text_input("שם:", value=str(row["name"]), key=f"en_{idx}")
                        edit_p = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{idx}")
                        if st.button("💾 שמור שינויים", key=f"sv_{idx}"):
                            df.at[idx, "name"], df.at[idx, "price"] = edit_n, edit_p
                            save_data(df)
                            st.rerun()
                        
                        st.divider()
                        st.write("כל תמונות המטבע:")
                        keep_imgs = []
                        for i, p in enumerate(img_list):
                            if os.path.exists(p):
                                im_c, del_c = st.columns([4, 1])
                                im_c.image(p, use_container_width=True)
                                if not del_c.button("🗑️", key=f"di_{idx}_{i}"):
                                    keep_imgs.append(p)
                        
                        # הוספת עוד תמונות למטבע קיים מהגלריה
                        more_files = st.file_uploader("➕ הוסף עוד תמונות:", accept_multiple_files=True, key=f"add_more_{idx}")
                        if st.button("✅ הוסף תמונות", key=f"btn_more_{idx}"):
                            if more_files:
                                for mf in more_files:
                                    sq = process_image(mf)
                                    p_path = os.path.join(IMG_DIR, f"extra_{int(time.time())}_{mf.name}")
                                    sq.save(p_path)
                                    keep_imgs.append(p_path)
                                df.at[idx, "images"] = "|".join(keep_imgs)
                                save_data(df)
                                st.rerun()

                        if len(keep_imgs) != len(img_list):
                            df.at[idx, "images"] = "|".join(keep_imgs)
                            save_data(df)
                            st.rerun()

                        st.divider()
                        if st.button("❌ מחק את כל הפריט", key=f"full_del_{idx}", use_container_width=True):
                            df.drop(idx).to_csv(DB_FILE, index=False)
                            st.rerun()

        else: # תצוגת רשימה
            for idx, row in df.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    img_list = str(row["images"]).split("|")
                    c1.image(img_list[0], width=80)
                    c2.write(f"**{row['name']}** | {row['price']} ₪")
