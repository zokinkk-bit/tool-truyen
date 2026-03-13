import streamlit as st
import easyocr
import PIL.Image
from deep_translator import GoogleTranslator
import google.generativeai as genai
from google.generativeai.types import RequestOptions
import os

# --- CẤU HÌNH BẢO MẬT ---
try:
    if "GEMINI_KEY" not in st.secrets:
        st.error("Thiếu GEMINI_KEY trong Secrets!")
    else:
        genai.configure(api_key=st.secrets["GEMINI_KEY"])
        # Ép buộc sử dụng phiên bản API v1 để tránh lỗi 404 v1beta
        ai_model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            # Đây là dòng quan trọng nhất để fix lỗi 404 của Việt
            generation_config={"temperature": 0.7}
        )
except Exception as e:
    st.error(f"Lỗi cấu hình: {e}")

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
st.title("📖 AI Comic Reader - Bản Sửa Lỗi 404 & Tiếng Việt")

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
                # Tách trang bằng dấu chấm để AI dễ đọc
                full_text += " ".join(results) + " . "
                if os.path.exists(temp_name): os.remove(temp_name)
            except Exception as e:
                st.error(f"Lỗi trang {file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if full_text.strip():
            st.divider()
            with st.spinner("AI đang 'giải mã' tiếng Việt và dọn rác..."):
                try:
                    # Gửi thêm options để ép API dùng bản ổn định
                    prompt_fix = f"""
                    Nhiệm vụ: Phục hồi tiếng Việt từ dữ liệu OCR bị dính chữ và lỗi dấu.
                    Dữ liệu: "{full_text[:3000]}"
                    
                    Yêu cầu:
                    1. Bỏ qua các từ quảng cáo như 'BAOTANGTRUYENVIP', 'WEB CHINH', 'NHOM DICH'...
                    2. Khôi phục đoạn hội thoại thành tiếng Việt chuẩn, có dấu, tách chữ rõ ràng. 
                    (Ví dụ: 'TOIKHGNGBAO' -> 'Tôi không bao', 'TATCACHIA' -> 'Tất cả chỉ là')
                    3. Viết tóm tắt nội dung và review ngắn gọn.
                    4. Chấm điểm độ hay.
                    
                    Trình bày bằng Markdown đẹp mắt.
                    """
                    
                    # Thêm request_options để ép phiên bản API
                    response = ai_model.generate_content(
                        prompt_fix,
                        request_options=RequestOptions(api_version='v1')
                    )
                    
                    st.subheader("🤖 Kết quả từ AI (Đã sửa lỗi)")
                    st.markdown(response.text)
                    
                except Exception as ai_err:
                    st.error(f"AI vẫn chưa phản hồi: {ai_err}")
                    # Backup dịch thô
                    dich_tam = GoogleTranslator(source='auto', target='vi').translate(full_text[:1500])
                    st.info("Bản dịch thô (Dùng khi AI lỗi):")
                    st.write(dich_tam)
        else:
            st.warning("Không tìm thấy chữ nào trong ảnh.")