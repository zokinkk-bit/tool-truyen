import streamlit as st
import easyocr
import PIL.Image
from deep_translator import GoogleTranslator
import google.generativeai as genai
import os

# --- CẤU HÌNH BẢO MẬT & FIX LỖI 404 ---
try:
    GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    
    # Hàm tìm model khả dụng để không bao giờ bị lỗi 404 nữa
    def get_working_model():
        for m in genai.list_models():
            if 'generateContent' in m.supported_methods:
                if 'gemini-1.5-flash' in m.name:
                    return m.name
        return 'gemini-pro' # Phương án dự phòng cuối cùng

    target_model_name = get_working_model()
    ai_model = genai.GenerativeModel(target_model_name)
except Exception as e:
    st.error(f"Lỗi cấu hình API: {e}")

st.set_page_config(page_title="Việt Comic Reader - Ultimate Fix", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

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
st.title("📖 AI Comic Reader - Bản Sửa Lỗi Tiếng Việt")

if not uploaded_files:
    st.warning("👈 Hãy tải ảnh ở thanh bên trái!")
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
                # Thêm dấu chấm để tách câu rõ ràng cho AI
                full_text += " ".join(results) + " . "
                if os.path.exists(temp_name): os.remove(temp_name)
            except Exception as e:
                st.error(f"Lỗi trang {file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if full_text.strip():
            st.divider()
            with st.spinner("AI đang phục hồi tiếng Việt và viết review..."):
                try:
                    # Dùng AI để "giải mã" đống chữ dính nhau
                    prompt_fix = f"""
                    Nhiệm vụ: Phục hồi và Review truyện tranh.
                    Dữ liệu thô (bị dính chữ, thiếu dấu, rác từ web): "{full_text[:3500]}"
                    
                    Yêu cầu:
                    1. Phục hồi đoạn văn trên thành tiếng Việt có dấu, đúng ngữ pháp, tách từ rõ ràng.
                    2. Loại bỏ các từ rác của web như 'BAOTANGTRUYENVIP', 'FLAMECOMICS', 'DONG CON'...
                    3. Tóm tắt nội dung: Đây là cảnh đối thoại giữa một người cha cực đoan và đứa con trai trong hầm ngục?
                    4. Viết bài review ngắn và chấm điểm.
                    
                    Trình bày bằng Markdown chuyên nghiệp.
                    """
                    
                    response = ai_model.generate_content(prompt_fix)
                    
                    st.subheader("🤖 Kết quả phân tích (Đã Fix lỗi tiếng Việt)")
                    st.markdown(response.text)
                    
                except Exception as ai_err:
                    st.error(f"Lỗi AI: {ai_err}")
                    # Nếu AI lỗi, dùng bộ dịch tạm thời
                    dich_tam = GoogleTranslator(source='auto', target='vi').translate(full_text[:2000])
                    st.write("Bản dịch tạm:", dich_tam)
        else:
            st.warning("Không tìm thấy chữ để xử lý.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Model: {target_model_name}")