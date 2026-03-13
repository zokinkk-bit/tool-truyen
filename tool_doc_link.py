import streamlit as st
import easyocr
import requests
import PIL.Image
from io import BytesIO
from deep_translator import GoogleTranslator
import google.generativeai as genai
import time

# --- CẤU HÌNH AI ---
GOOGLE_API_KEY = "NHAP_API_KEY_CUA_VIET_TAI_DAY"
genai.configure(api_key=GOOGLE_API_KEY)
ai_model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Việt Comic Link Reader", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

def viet_review(noidung):
    prompt = f"Bạn là một chuyên gia review truyện. Hãy tóm tắt và review cực hay nội dung sau: {noidung}"
    response = ai_model.generate_content(prompt)
    return response.text

# --- GIAO DIỆN ---
st.title("🌐 Tool Đọc & Review Truyện Qua Link")
st.info("Nhập link ảnh trực tiếp từ các trang web truyện Trung Quốc.")

url = st.text_input("Dán link ảnh truyện (.jpg, .png...):")

if st.button("Bắt đầu đọc 🚀"):
    if url:
        try:
            with st.spinner("Đang tải ảnh từ link..."):
                # Tải ảnh từ URL
                header = {'User-Agent': 'Mozilla/5.0'} # Giả lập trình duyệt để tránh bị chặn
                response = requests.get(url, headers=header)
                img = PIL.Image.open(BytesIO(response.content))
                st.image(img, caption="Ảnh đã tải thành công", width=400)
                
                # Lưu tạm để OCR đọc
                img.save("temp.jpg")
                
            with st.spinner("AI đang quét chữ và phân tích..."):
                results = reader.readtext("temp.jpg", detail=0)
                text_trung = " ".join(results)
                
                if text_trung:
                    # Dịch
                    dich = GoogleTranslator(source='auto', target='vi').translate(text_trung)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Nội dung dịch thô")
                        st.write(dich)
                    
                    with col2:
                        st.subheader("AI Reviewer nhận xét")
                        st.markdown(viet_review(dich))
                else:
                    st.warning("Không tìm thấy chữ trong ảnh này. Hãy thử link khác!")
        except Exception as e:
            st.error(f"Lỗi: Không thể truy cập link này. Chi tiết: {e}")