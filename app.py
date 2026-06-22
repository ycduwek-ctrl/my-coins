import streamlit as st
import pandas as pd
import os
from PIL import Image

# --- הגדרות דף ועיצוב ---
st.set_page_config(page_title="Coin Manager Pro", layout="wide")

st.markdown("""
<style>
    /* עיצוב תמונה לריבוע 1:1 */
    .stImage > img {
        aspect-ratio: 1 / 1;
        object-fit: cover;
        border-radius: 12px;
        border: 1px solid #ddd;
    }
    /* עיצוב כפתורי דפדוף מעל התמונה */
    .nav-button {
        background-color: rgba(255, 255, 255, 0.7);
        border: none;
        border-radius: 50%;
        padding: 5px 10px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# יצירת תיקיית תמונות
if not os.path.exists("coin_images"):
    os.makedirs("coin_images")

DB_FILE = 'catalog_data.csv'

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["id", "name", "my_price", "images"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# אתחול מצב דפדוף במידה ולא קיים
if "img_indices" not in st.session_state:
    st.session_state.img_indices = {}

# --- ממשק משתמש ---
st.title("🪙 קטלוג מטבעות חכם")

tab1, tab2 = st.tabs(["💎 הגלריה שלי", "➕ הוספת מטבע"])

# --- טאב 2: הוספת מטבע (כולל מצלמה) ---
with tab2:
    st.header("הוספת פריט חדש")
    with st.container(border=True):
        new_name = st.text_input("שם המטבע:", key="new_name")
        new_price = st.text_input("מחיר מבוקש:", key="new_price")
        
        col_files, col_cam = st.columns(2)
        with col_files:
            up_files = st.file_uploader("העלה תמונות מהגלריה:", accept_multiple_files=True, type=['jpg','png','jpeg'])
        with col_cam:
            cam_file = st.camera_input("או צלם עכשיו:")

        if st.button("🚀 פרסם לקטלוג"):
            all_images = []
            # שמירת קבצים מהגלריה
            if up_files:
                for f in up_files:
                    path = os.path.join("coin_images", f.name)
                    with open(path, "wb") as file: file.write(f.getvalue())
                    all_images.append(path)
            # שמירת תמונה מהמצלמה
            if cam_file:
                path = os.path.join("coin_images", f"cam_{cam_file.name}.jpg")
                with open(path, "wb") as file: file.write(cam_file.getvalue())
                all_images.append(path)

            if new_name and all_images:
                df = load_data()
                new_row = {"id": len(df)+1, "name": new_name, "my_price": new_price, "images": "|".join(all_images)}
                pd.concat([df, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
                st.success("המטבע נוסף!")
                st.rerun()

# --- טאב 1: גלריה ועריכה ---
with tab1:
    df = load_data()
    if df.empty:
        st.info("הקטלוג ריק.")
    else:
        for idx, row in df.iterrows():
            with st.container(border=True):
                col_display, col_info = st.columns([1, 1.5])
                
                img_list = str(row["images"]).split("|")
                coin_id = str(row["id"])
                
                # ניהול אינדקס תמונה נוכחית
                if coin_id not in st.session_state.img_indices:
                    st.session_state.img_indices[coin_id] = 0
                
                current_idx = st.session_state.img_indices[coin_id]

                with col_display:
                    # תצוגת התמונה בפורמט 1:1
                    st.image(img_list[current_idx], use_container_width=True)
                    
                    # חצי דפדוף מתחת לתמונה (עובד מעולה במובייל)
                    b_col1, b_col2, b_col3 = st.columns([1, 2, 1])
                    if b_col1.button("⬅️", key=f"prev_{idx}"):
                        st.session_state.img_indices[coin_id] = (current_idx - 1) % len(img_list)
                        st.rerun()
                    b_col2.write(f"תמונה {current_idx+1} / {len(img_list)}")
                    if b_col3.button("➡️", key=f"next_{idx}"):
                        st.session_state.img_indices[coin_id] = (current_idx + 1) % len(img_list)
                        st.rerun()

                with col_info:
                    st.subheader(row["name"])
                    st.write(f"💰 מחיר: **{row['my_price']} ש''ח**")
                    
                    # --- מנגנון עריכה ---
                    with st.expander("✏️ ערוך פרטים ותמונות"):
                        edit_name = st.text_input("שנה שם:", value=row["name"], key=f"en_{idx}")
                        edit_price = st.text_input("שנה מחיר:", value=row["my_price"], key=f"ep_{idx}")
                        
                        st.write("ניהול תמונות:")
                        images_to_keep = []
                        for i, img_p in enumerate(img_list):
                            c1, c2 = st.columns([3, 1])
                            c1.image(img_p, width=100)
                            if not c2.checkbox("מחק", key=f"del_img_{idx}_{i}"):
                                images_to_keep.append(img_p)
                        
                        new_imgs = st.file_uploader("הוסף עוד תמונות:", accept_multiple_files=True, key=f"au_{idx}")
                        
                        if st.button("שמור שינויים", key=f"save_{idx}"):
                            # הוספת התמונות החדשות
                            if new_imgs:
                                for nf in new_imgs:
                                    n_path = os.path.join("coin_images", nf.name)
                                    with open(n_path, "wb") as f: f.write(nf.getvalue())
                                    images_to_keep.append(n_path)
                            
                            df.at[idx, "name"] = edit_name
                            df.at[idx, "my_price"] = edit_price
                            df.at[idx, "images"] = "|".join(images_to_keep)
                            save_data(df)
                            st.success("עודכן!")
                            st.rerun()
                    
                    if st.button("🗑️ מחק מטבע מהקטלוג", key=f"full_del_{idx}"):
                        df = df.drop(idx)
                        save_data(df)
                        st.rerun()
