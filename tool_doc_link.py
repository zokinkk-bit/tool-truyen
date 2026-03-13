import streamlit as st
import easyocr
import PIL.Image
from deep_translator import GoogleTranslator
import google.generativeai as genai
import os
import re

# --- CẤU HÌNH BẢO MẬT & AUTO-DETECT MODEL ---
ai_model = None
target_model_name = "Đang kiểm tra..."

try:
    if "GEMINI_KEY" not in st.secrets:
        st.error("Thiếu GEMINI_KEY trong Secrets của Streamlit!")
    else:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        
        # Tự động quét danh sách model để tránh lỗi 404 dứt điểm
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên các dòng Flash, nếu không có thì lấy bất cứ cái gì dùng được
        selected = next((m for m in available_models if "1.5-flash" in m), None)
        if not selected:
            selected = available_models[0] if available_models else None
            
        if selected:
            target_model_name = selected
            ai_model = genai.GenerativeModel(target_model_name)
        else:
            st.error("Không tìm thấy model nào khả dụng!")
except Exception as e:
    st.error(f"Lỗi khởi tạo hệ thống: {e}")

st.set_page_config(page_title="Việt Comic Reader - Ultra Stable", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

# --- HÀM LÀM SẠCH VĂN BẢN ---
def clean_text(text):
    # Xóa rác web và các ký tự gây nhiễu
    junk = ['BAOTANGTRUYENVIP', 'FLAMECOMICS', 'WEBCHINH', 'NHOMDICH', 'COMIC', 'DANGTAIWEB']
    for w in junk:
        text = re.sub(w, '', text, flags=re.IGNORECASE)
    text = re.sub(r'[^\w\s.!?]', ' ', text) # Chỉ giữ lại chữ, số và dấu câu cơ bản
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
    st.divider()
    st.caption(f"Model active: {target_model_name}")

# --- MÀN HÌNH CHÍNH ---
st.title("📖 AI Comic Reader - Bản Phục Hồi Nội Dung")

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
            # Dọn dẹp văn bản thô
            cleaned = clean_text(full_text)
            
            st.divider()
            with st.spinner("AI đang phục hồi nội dung và viết Review..."):
                try:
                    # Prompt "cứu vớt" nội dung nát
                    prompt = f"""
                    Dữ liệu truyện tranh (OCR thô): "{cleaned[:3500]}"
                    
                    Yêu cầu:
                    1. Đây là truyện về một người bị giam cầm trong hầm ngục. Hãy phục hồi các câu thoại thành tiếng Việt có dấu chuẩn.
                    2. Chuyển tên nhân vật sang Hán Việt (ví dụ: mẹ chết, người cha độc tài...).
                    3. Tóm tắt diễn biến kịch tính: Người con muốn thoát khỏi hầm, người cha ngăn cản bằng lời lẽ cực đoan?
                    4. Viết bài review ngắn gọn, đánh giá tình huống và chấm điểm.
                    
                    Trình bày Markdown đẹp mắt.
                    """
                    
                    response = ai_model.generate_content(prompt)
                    st.subheader("🤖 Kết quả từ AI")
                    st.markdown(response.text)
                    
                except Exception as ai_err:
                    st.error(f"AI lỗi phản hồi: {ai_err}")
                    # Backup dịch thô
                    dich = GoogleTranslator(source='auto', target='vi').translate(cleaned[:1500])
                    st.info("Nội dung dịch thô (AI không phản hồi):")
                    st.write(dich)
        else:
            st.warning("Không tìm thấy chữ để xử lý.")

st.sidebar.markdown("---")
st.sidebar.caption("ITC Student Project - Việt")