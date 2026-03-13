import streamlit as st
import easyocr
import PIL.Image
from deep_translator import GoogleTranslator
import google.generativeai as genai
import os
import re

# --- CẤU HÌNH BẢO MẬT ---
try:
    if "GEMINI_KEY" not in st.secrets:
        st.error("Thiếu GEMINI_KEY trong Secrets!")
    else:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Sử dụng model gemini-1.5-flash trực tiếp, không dùng RequestOptions lỗi thời
        ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Lỗi khởi tạo AI: {e}")

st.set_page_config(page_title="Việt Comic Reader - Final Fix", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

# --- HÀM LỌC RÁC (DỌN DẸP CHỮ DÍNH) ---
def clean_comic_text(text):
    # Loại bỏ tên các web truyện rác
    trash_words = ['BAOTANGTRUYENVIP', 'FLAMECOMICS', 'WEBCHINH', 'NHOMDICH', 'COMIC', 'NETTRUYEN']
    for word in trash_words:
        text = re.sub(word, '', text, flags=re.IGNORECASE)
    # Loại bỏ các ký tự đặc biệt thừa thãi
    text = re.sub(r'[@#$*%^&()_+={}\[\]|\\:;"\'<>,?/]', ' ', text)
    return " ".join(text.split())

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Quản lý Chapter")
    uploaded_files = st.file_uploader("Tải ảnh truyện:", 
                                      type=['jpg', 'jpeg', 'png', 'webp'], 
                                      accept_multiple_files=True)
    if uploaded_files:
        uploaded_files = sorted(uploaded_files, key=lambda x: x.name)
        st.success(f"Đã nhận {len(uploaded_files)} trang.")

# --- MÀN HÌNH CHÍNH ---
st.title("📖 AI Comic Reader - Bản Fix Lỗi 'RequestOptions'")

if not uploaded_files:
    st.warning("👈 Hãy tải ảnh ở thanh bên trái để bắt đầu!")
else:
    if st.button("Bắt đầu quét & Review 🚀"):
        full_text = ""
        st.subheader("🖼️ Nội dung Chapter")
        
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                img = PIL.Image.open(file)
                if img.mode != 'RGB': img = img.convert('RGB')
                st.image(img, use_container_width=True)
                
                temp_name = f"temp_{i}.jpg"
                img.save(temp_name)
                results = reader.readtext(temp_name, detail=0)
                full_text += " ".join(results) + " . "
                if os.path.exists(temp_name): os.remove(temp_name)
            except Exception as e:
                st.error(f"Lỗi trang {file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if full_text.strip():
            # Dọn dẹp văn bản thô trước khi gửi AI
            cleaned_text = clean_comic_text(full_text)
            
            st.divider()
            with st.spinner("AI đang phục hồi nội dung truyện..."):
                try:
                    # Prompt cực mạnh để AI tự sửa dấu
                    prompt = f"""
                    Dữ liệu thô từ truyện tranh: "{cleaned_text[:3500]}"
                    
                    Yêu cầu:
                    1. Phục hồi đoạn văn trên thành tiếng Việt chuẩn (có dấu, đúng chính tả, tách chữ).
                    2. Chuyển tên nhân vật sang Hán Việt.
                    3. Tóm tắt nội dung và Review ngắn gọn.
                    4. Chấm điểm Chapter.
                    
                    Ghi chú: Nếu chữ quá nát, hãy dựa vào ngữ cảnh (ví dụ: cha nói chuyện với con, hầm ngục) để đoán nội dung.
                    """
                    
                    response = ai_model.generate_content(prompt)
                    st.subheader("🤖 Kết quả từ AI")
                    st.markdown(response.text)
                    
                except Exception as ai_err:
                    st.error(f"Lỗi AI: {ai_err}")
                    dich_tam = GoogleTranslator(source='auto', target='vi').translate(cleaned_text[:1500])
                    st.info("Bản dịch tạm thời:")
                    st.write(dich_tam)
        else:
            st.warning("Không tìm thấy chữ để xử lý.")

st.sidebar.markdown("---")
st.sidebar.caption("Sửa lỗi RequestOptions cho Việt ITC")