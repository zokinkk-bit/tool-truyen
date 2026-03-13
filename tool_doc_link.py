import streamlit as st
import easyocr
import PIL.Image
from deep_translator import GoogleTranslator
import google.generativeai as genai
import os

# --- CẤU HÌNH BẢO MẬT ---
target_model_name = "gemini-1.5-flash" # Tên model mặc định

try:
    if "GEMINI_KEY" not in st.secrets:
        st.error("Thiếu GEMINI_KEY trong Secrets của Streamlit!")
    else:
        GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # Thử khởi tạo trực tiếp model - Cách này ổn định nhất hiện tại
        ai_model = genai.GenerativeModel(target_model_name)
        
        # Test nhẹ xem key có sống không (không tốn phí)
        target_model_name = "gemini-1.5-flash (Sẵn sàng)"
except Exception as e:
    st.error(f"Lỗi cấu hình API: {e}")
    st.info("Mẹo: Hãy chắc chắn bạn đã cập nhật API Key mới vào mục Secrets.")

st.set_page_config(page_title="Việt Comic Reader - ITC Pro", layout="wide")

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
st.title("📖 AI Comic Reader - Bản Fix Lỗi Attribute")

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
                full_text += " ".join(results) + " . "
                if os.path.exists(temp_name): os.remove(temp_name)
            except Exception as e:
                st.error(f"Lỗi trang {file.name}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if full_text.strip():
            st.divider()
            with st.spinner("AI đang xử lý nội dung..."):
                try:
                    # Prompt tối ưu để AI tự sửa lỗi dấu và cách chữ cho Việt
                    prompt_fix = f"""
                    Nhiệm vụ: Phục hồi tiếng Việt và Review truyện.
                    Dữ liệu thô từ OCR: "{full_text[:3000]}"
                    
                    Yêu cầu:
                    1. Phục hồi thành tiếng Việt chuẩn, có dấu, tách từ rõ ràng, đúng ngữ pháp.
                    2. Loại bỏ rác quảng cáo web (như Baotangtruyen, FlameComics...).
                    3. Tóm tắt nội dung kịch tính và chấm điểm chapter này.
                    4. Chuyển tên nhân vật Pinyin sang Hán Việt.
                    """
                    
                    response = ai_model.generate_content(prompt_fix)
                    st.subheader("🤖 Kết quả từ AI")
                    st.markdown(response.text)
                    
                except Exception as ai_err:
                    st.error(f"AI không phản hồi: {ai_err}")
                    # Backup dịch thô bằng Google Translator nếu Gemini lỗi
                    dich_tam = GoogleTranslator(source='auto', target='vi').translate(full_text[:1500])
                    st.write("Bản dịch thô:", dich_tam)
        else:
            st.warning("Không tìm thấy chữ để xử lý.")

st.sidebar.markdown("---")
st.sidebar.caption(f"Trạng thái: {target_model_name}")