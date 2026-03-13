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
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Lỗi API Key! Hãy kiểm tra mục Secrets.")

st.set_page_config(page_title="Việt Comic Reader - Auto Merge", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

# --- GIAO DIỆN ---
st.title("📚 AI Comic Reader - Tự Ghép Thứ Tự Trang")
st.markdown("---")

# Tải nhiều ảnh
uploaded_files = st.file_uploader("Chọn tất cả các trang ảnh của Chapter:", 
                                  type=['jpg', 'jpeg', 'png', 'webp'], 
                                  accept_multiple_files=True)

if uploaded_files:
    # --- TỰ ĐỘNG GHÉP THỨ TỰ THEO TÊN FILE ---
    # Sắp xếp lại danh sách file để trang 1 luôn đi trước trang 2
    uploaded_files = sorted(uploaded_files, key=lambda x: x.name)
    
    st.success(f"Đã nhận {len(uploaded_files)} trang. Thứ tự: " + " ➔ ".join([f.name for f in uploaded_files[:3]]) + "...")

    if st.button("Bắt đầu quét & Review toàn bộ Chapter 🚀"):
        full_text = ""
        
        # Hiển thị khu vực đọc truyện ghép
        st.subheader("🖼️ Chapter xem trước (Đã ghép)")
        
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            with st.status(f"Đang xử lý: {file.name}", expanded=False):
                try:
                    img = PIL.Image.open(file)
                    if img.mode != 'RGB': img = img.convert('RGB')
                    
                    # Hiển thị ảnh ghép nối tiếp nhau
                    st.image(img, caption=f"Trang {i+1} ({file.name})", use_column_width=True)
                    
                    # Quét chữ
                    temp_name = f"temp_{i}.jpg"
                    img.save(temp_name)
                    results = reader.readtext(temp_name, detail=0)
                    full_text += " ".join(results) + " "
                    os.remove(temp_name)
                except Exception as e:
                    st.error(f"Lỗi tại file {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        # --- AI REVIEW ---
        if full_text.strip():
            st.divider()
            with st.spinner("AI đang 'đọc' và viết bài review..."):
                # Dịch nội dung
                dich = GoogleTranslator(source='auto', target='vi').translate(full_text[:3500])
                
                prompt = f"""
                Nội dung truyện: {dich}
                Hãy làm một bài review chuyên nghiệp:
                1. Tóm tắt diễn biến theo thứ tự các trang ảnh.
                2. Phân tích nhân vật (Dùng tên Hán Việt nếu là truyện Trung).
                3. Đánh giá độ hấp dẫn và chấm điểm.
                Trình bày đẹp bằng Markdown.
                """
                review = ai_model.generate_content(prompt)
                
            st.subheader("🤖 Phân tích từ AI Reviewer")
            st.markdown(review.text)
        else:
            st.warning("Không tìm thấy thoại trong các trang ảnh này.")

# Dọn dẹp
st.markdown("---")
st.caption("Dự án được phát triển bởi Việt - ITC Student")