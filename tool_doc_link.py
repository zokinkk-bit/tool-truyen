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
    # Sửa lại tên model chuẩn nhất để fix lỗi 404
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

st.set_page_config(page_title="Việt Comic Reader - Fix Lỗi 404 & Dịch", layout="wide")

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
        uploaded_files = sorted(uploaded_files, key=lambda x: x.name)
        st.subheader("Trình tự quét:")
        for idx, f in enumerate(uploaded_files):
            st.write(f"{idx+1}. {f.name}")
        
        st.info("💡 Mẹo: Đặt tên file 01, 02... để máy tự ghép đúng thứ tự.")

# --- MÀN HÌNH CHÍNH ---
st.title("📖 AI Comic Reader - Bản Fix Lỗi Dịch")

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
                
                # Hiển thị ảnh
                st.image(img, use_container_width=True)
                
                # OCR xử lý
                temp_name = f"temp_{i}.jpg"
                img.save(temp_name)
                results = reader.readtext(temp_name, detail=0)
                # Thêm dấu cách sau mỗi trang để tránh dính chữ
                full_text += " ".join(results) + " . "
                
                if os.path.exists(temp_name):
                    os.remove(temp_name)
                
            except Exception as e:
                st.error(f"Lỗi trang {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        # --- AI REVIEW & FIX DỊCH ---
        if full_text.strip():
            st.divider()
            with st.spinner("AI đang sửa lỗi chính tả và viết review..."):
                try:
                    # Dịch thô từ Google (thường bị lỗi dấu)
                    dich_tho = GoogleTranslator(source='auto', target='vi').translate(full_text[:3000])
                    
                    # Dùng AI làm nhiệm vụ sửa dấu, cách chữ và review
                    prompt = f"""
                    Nội dung sau đây được dịch từ truyện tranh nhưng bị lỗi mất dấu, dính chữ và thiếu dấu câu:
                    "{dich_tho}"
                    
                    Yêu cầu Việt hóa:
                    1. Hãy sửa lại đoạn văn trên thành tiếng Việt chuẩn (đầy đủ dấu, cách chữ, dấu câu).
                    2. Chuyển tên nhân vật sang Hán Việt (Ví dụ: Lin Fan -> Lâm Phàm).
                    3. Tóm tắt nội dung và viết bài review cực hay kèm chấm điểm.
                    
                    Trình bày Markdown đẹp mắt.
                    """
                    
                    response = ai_model.generate_content(prompt)
                    
                    st.subheader("🤖 Kết quả phân tích (Đã sửa lỗi dấu & cách chữ)")
                    st.success("Đã hoàn thành!")
                    st.markdown(response.text)
                    
                except Exception as ai_err:
                    st.error(f"Lỗi khi gọi AI Gemini: {ai_err}")
                    st.info("Nội dung dịch thô để bạn xem tạm:")
                    st.write(dich_tho)
        else:
            st.warning("Không tìm thấy chữ để xử lý.")

st.sidebar.markdown("---")
st.sidebar.caption("Sửa lỗi bởi Việt - ITC Student")