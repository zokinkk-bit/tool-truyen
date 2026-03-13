import streamlit as st
import easyocr
import PIL.Image
from deep_translator import GoogleTranslator
import google.generativeai as genai
import os

# --- CẤU HÌNH BẢO MẬT ---
try:
    GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    # Sửa tên model thành đường dẫn đầy đủ để tránh lỗi NotFound
    ai_model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

st.set_page_config(page_title="Việt Comic Reader - Sidebar Edition", layout="wide")

@st.cache_resource
def load_ocr():
    # Load nhận diện tiếng Trung và tiếng Anh
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

# --- SIDEBAR: QUẢN LÝ DANH SÁCH ---
with st.sidebar:
    st.header("📂 Quản lý Chapter")
    uploaded_files = st.file_uploader("Tải ảnh lên đây:", 
                                      type=['jpg', 'jpeg', 'png', 'webp'], 
                                      accept_multiple_files=True)
    
    if uploaded_files:
        # Sắp xếp ảnh theo tên file để đúng thứ tự trang
        uploaded_files = sorted(uploaded_files, key=lambda x: x.name)
        st.subheader("Trình tự quét:")
        for idx, f in enumerate(uploaded_files):
            st.write(f"{idx+1}. {f.name}")
        
        st.info("💡 Mẹo: Đặt tên file 01, 02... để máy tự ghép đúng thứ tự.")

# --- MÀN HÌNH CHÍNH ---
st.title("📖 AI Comic Reader - Chế độ Ghép Ảnh & Sidebar")

if not uploaded_files:
    st.warning("👈 Hãy tải các trang truyện ở thanh bên trái để bắt đầu!")
else:
    if st.button("Bắt đầu quét & Review Chapter 🚀"):
        full_text = ""
        st.subheader("🖼️ Nội dung Chapter (Đã ghép nối tiếp)")
        
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                img = PIL.Image.open(file)
                if img.mode != 'RGB': img = img.convert('RGB')
                
                # Hiển thị ảnh tràn màn hình như web truyện
                st.image(img, use_container_width=True)
                
                # OCR xử lý ngầm
                temp_name = f"temp_{i}.jpg"
                img.save(temp_name)
                results = reader.readtext(temp_name, detail=0)
                full_text += " ".join(results) + " "
                
                # Xóa file tạm ngay sau khi quét trang đó
                if os.path.exists(temp_name):
                    os.remove(temp_name)
                
            except Exception as e:
                st.error(f"Lỗi trang {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        # --- AI REVIEW ---
        if full_text.strip():
            st.divider()
            with st.spinner("AI đang phân tích nội dung truyện..."):
                try:
                    # Dịch nội dung (Giới hạn 3500 ký tự để không lỗi API)
                    dich = GoogleTranslator(source='auto', target='vi').translate(full_text[:3500])
                    
                    prompt = f"""
                    Dưới đây là nội dung dịch thô từ các trang truyện: {dich}
                    
                    Yêu cầu:
                    1. Nhận diện nhân vật (Nếu tên là Pinyin như Lin Fan, Xiao Yan... hãy đổi sang Hán Việt như Lâm Phàm, Tiêu Viêm).
                    2. Tóm tắt cốt truyện kịch tính của chapter này.
                    3. Viết bài review ngắn gọn, phân tích tình huống hay nhất.
                    4. Chấm điểm chapter trên thang điểm 10.
                    
                    Trình bày đẹp mắt bằng Markdown với các icon phù hợp.
                    """
                    
                    response = ai_model.generate_content(prompt)
                    
                    st.subheader("🤖 Phân tích chuyên sâu từ AI")
                    st.success("Đã hoàn thành bài review!")
                    st.markdown(response.text)
                    
                except Exception as ai_err:
                    st.error(f"Lỗi khi gọi AI Gemini: {ai_err}")
                    st.info("Nội dung dịch thô để bạn đọc tạm:")
                    st.write(dich)
        else:
            st.warning("Không tìm thấy nội dung chữ để AI phân tích.")

# Dọn dẹp footer
st.sidebar.markdown("---")
st.sidebar.caption("Phiên bản Pro của Việt - ITC Student")