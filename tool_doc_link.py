import streamlit as st
import easyocr
import requests
import PIL.Image
from io import BytesIO
from deep_translator import GoogleTranslator
import google.generativeai as genai
import time

# --- CẤU HÌNH AI (ĐÃ SỬA ĐỂ BẢO MẬT) ---
# Lấy Key từ mục Secrets trên Streamlit Cloud thay vì dán trực tiếp
try:
    GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Chưa cấu hình API Key trong mục Secrets hoặc lỗi kết nối AI.")

st.set_page_config(page_title="Việt Comic Link Reader", layout="wide")

@st.cache_resource
def load_ocr():
    # Load nhận diện tiếng Trung giản thể và tiếng Anh
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

def viet_review(noidung):
    try:
        prompt = f"Bạn là một chuyên gia review truyện tranh. Hãy tóm tắt ngắn gọn và viết một bài review hấp dẫn, phân tích tình tiết cho nội dung sau: {noidung}"
        response = ai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI không thể viết review lúc này: {e}"

# --- GIAO DIỆN ---
st.title("🌐 Tool Đọc & Review Truyện Qua Link")
st.info("Nhập link ảnh trực tiếp từ các trang web truyện Trung Quốc.")

url = st.text_input("Dán link ảnh truyện (.jpg, .png...):")

if st.button("Bắt đầu đọc 🚀"):
    if url:
        try:
            with st.spinner("Đang tải ảnh từ link..."):
                header = {'User-Agent': 'Mozilla/5.0'} 
                response = requests.get(url, headers=header, timeout=10)
                img = PIL.Image.open(BytesIO(response.content))
                st.image(img, caption="Ảnh đã tải thành công", width=400)
                
                # Lưu tạm để OCR đọc
                img.save("temp.jpg")
                
            with st.spinner("AI đang quét chữ từ ảnh... (Lần đầu có thể mất 1-2 phút)"):
                results = reader.readtext("temp.jpg", detail=0)
                text_trung = " ".join(results)
                
                if text_trung:
                    # Dịch sang tiếng Việt
                    with st.spinner("Đang dịch sang tiếng Việt..."):
                        dich = GoogleTranslator(source='auto', target='vi').translate(text_trung)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("📝 Nội dung dịch thô")
                        st.info(dich)
                    
                    with col2:
                        st.subheader("🤖 AI Reviewer nhận xét")
                        st.success(viet_review(dich))
                else:
                    st.warning("Không tìm thấy chữ trong ảnh này. Hãy thử link khác!")
        except Exception as e:
            st.error(f"Lỗi: Không thể xử lý link này. Chi tiết: {e}")