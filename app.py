import streamlit as st
import pandas as pd
import os
from PIL import Image
import time
import base64
import io

# --- הגדרות עיצוב למראה אינסטגרם נקי ---
st.set_page_config(page_title="Coin Catalog Pro", layout="wide")

def get_image_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

st.markdown("""
<style>
    /* קרוסלת Swipe */
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
    }
    /* עיצוב החלונית */
    .stExpander {
        border: none !important;
        background-color: #f9f9f9 !important;
        border-radius: 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# פונקציות בסיס
IMG_DIR = "coin_images"
if not os.path.exists(IMG_DIR): os.makedirs(IMG_DIR)
DB_FILE = 'catalog_data_v3.csv'

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "price", "images", "comments"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def process_image(uploaded_file):
    img = Image.open(uploaded_file).convert('RGB')
    w, h = img.size
    s = min(w, h)
    l, t = (w-s)/2, (h-s)/2
    return img.crop((l, t, l+s, t+s))

# --- תפריט צד ---
st.sidebar.title("🖼️ הגדרות תצוגה")
view_mode = st.sidebar.radio("סגנון:", ["גלריה", "רשימה"])
grid_size = st.sidebar.slider("מטבעות בשורה", 1, 4, 3)

tab1, tab2 = st.tabs(["💎 הקטלוג", "➕ הוספה"])

# --- טאב הוספה ---
with tab2:
    st.header("הוספת מטבע חדש")
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
            new = {"id": len(df)+1, "name": c_name, "price": c_price, "images": "|".join(paths), "comments": ""}
            save_data(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
            st.success("נוסף בהצלחה!")
            st.rerun()

# --- טאב גלריה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        if view_mode == "גלריה":
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
                    
                    st.write(f"**{row['name']}**")

                    # --- חלונית ניהול ופרטים ---
                    with st.expander("🔍 פרטים וניהול"):
                        # עריכת פרטים
                        en = st.text_input("שם:", value=str(row["name"]), key=f"en_{idx}")
                        ep = st.text_input("מחיר:", value=str(row["price"]), key=f"ep_{idx}")
                        
                        # תגובות/הערות
                        comment = st.text_area("תגובה/הערה על המטבע:", value=str(row["comments"]), key=f"com_{idx}")
                        
                        if st.button("💾 שמור שינויים", key=f"sv_{idx}"):
                            df.at[idx, "name"], df.at[idx, "price"], df.at[idx, "comments"] = en, ep, comment
                            save_data(df)
                            st.rerun()

                        st.divider()
                        st.write("ניהול תמונות:")
                        keep = []
                        for i, p in enumerate(img_list):
                            if os.path.exists(p):
                                c1, c2 = st.columns([4, 1])
                                c1.image(p, use_container_width=True)
                                if not c2.button("🗑️", key=f"di_{idx}_{i}"):
                                    keep.append(p)
                        
                        # הוספת תמונות למטבע קיים
                        more_f = st.file_uploader("➕ הוסף תמונות:", accept_multiple_files=True, key=f"mf_{idx}")
                        if st.button("✅ הוסף", key=f"am_{idx}"):
                            if more_f:
                                new_paths = keep
                                for f in more_f:
                                    sq = process_image(f)
                                    np = os.path.join(IMG_DIR, f"ex_{int(time.time())}_{f.name}")
                                    sq.save(np)
                                    new_paths.append(np)
                                df.at[idx, "images"] = "|".join(new_paths)
                                save_data(df)
                                st.rerun()

                        if len(keep) != len(img_list):
                            df.at[idx, "images"] = "|".join(keep)
                            save_data(df)
                            st.rerun()

                        st.divider()
                        if st.button("❌ מחק את כל הפריט", key=f"del_{idx}", use_container_width=True):
                            df.drop(idx).to_csv(DB_FILE, index=False)
                            st.rerun()
        else:
            # תצוגת רשימה פשוטה
            for idx, row in df.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([1, 4])
                    img_list = str(row["images"]).split("|")
                    c1.image(img_list[0], width=80)
                    c2.write(f"**{row['name']}** | {row['price']} ₪")
                    c2.write(f"_{row['comments']}_" if pd.notna(row['comments']) else "")
