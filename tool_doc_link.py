import streamlit as st
import easyocr
import requests
import PIL.Image
from io import BytesIO
from deep_translator import GoogleTranslator
import google.generativeai as genai
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os

# --- CẤU HÌNH BẢO MẬT ---
try:
    GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Lỗi API Key trong Secrets!")

st.set_page_config(page_title="Việt Comic Chapter Reader Pro", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

def get_all_images_from_url(url):
    """Hàm tìm tất cả link ảnh trong một Chapter (Hỗ trợ Lazy Load & Data-Attributes)"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': url
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_links = []
        for img in soup.find_all('img'):
            src = (img.get('data-src') or img.get('data-original') or 
                   img.get('src') or img.get('data-cdn') or img.get('srcset'))
            if src:
                src = src.strip().split(' ')[0]
                full_src = urljoin(url, src)
                if any(ext in full_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    if not any(bad in full_src.lower() for bad in ['logo', 'icon', 'avatar', 'button']):
                        img_links.append(full_src)
        return list(dict.fromkeys(img_links))
    except Exception as e:
        st.error(f"Lỗi kết nối web: {e}")
        return []

# --- GIAO DIỆN ---
st.title("📖 AI Comic Reviewer - Chuyên Gia Phân Tích Chapter")
url_chapter = st.text_input("Dán link Chapter truyện cần review:")

if st.button("Bắt đầu quét & Việt hóa nhân vật 🚀"):
    if url_chapter:
        with st.spinner("Đang tìm kiếm trang ảnh..."):
            all_imgs = get_all_images_from_url(url_chapter)
            
        if all_imgs:
            st.success(f"Tìm thấy {len(all_imgs)} trang ảnh!")
            full_text = ""
            limit = min(len(all_imgs), 7) 
            progress_bar = st.progress(0)
            
            for i in range(limit):
                with st.status(f"Đang đọc trang {i+1}/{limit}...", expanded=False):
                    try:
                        headers = {'User-Agent': 'Mozilla/5.0', 'Referer': url_chapter}
                        res = requests.get(all_imgs[i], headers=headers, timeout=10)
                        img = PIL.Image.open(BytesIO(res.content))
                        if img.mode != 'RGB': img = img.convert('RGB')
                        img.save("temp.jpg")
                        results = reader.readtext("temp.jpg", detail=0)
                        full_text += " ".join(results) + " "
                    except:
                        st.write(f"❌ Lỗi trang {i+1}")
                progress_bar.progress((i + 1) / limit)

            if full_text.strip():
                with st.spinner("AI đang dịch thuật & Chuyển đổi tên nhân vật..."):
                    # Dịch thô
                    dich_tho = GoogleTranslator(source='auto', target='vi').translate(full_text[:3500])
                    
                    # Bước nâng cao: AI nhận diện nhân vật và viết review
                    prompt = f"""
                    Dựa trên nội dung dịch thô sau: {dich_tho}
                    1. Hãy nhận diện các nhân vật chính và phụ (Nếu tên là tiếng Trung/Pinyin, hãy chuyển sang Hán Việt chuẩn).
                    2. Tóm tắt cốt truyện tập này một cách lôi cuốn.
                    3. Viết bài review phân tích diễn biến và cảm xúc nhân vật.
                    4. Chấm điểm tập truyện.
                    Ghi chú: Trình bày đẹp mắt bằng Markdown.
                    """
                    review = ai_model.generate_content(prompt)
                
                st.divider()
                st.subheader("🤖 Kết quả phân tích từ AI")
                st.markdown(review.text)
            else:
                st.warning("Không quét được nội dung chữ.")
        else:
            st.error("Không tìm thấy ảnh. Hãy kiểm tra lại link!")

if os.path.exists("temp.jpg"): os.remove("temp.jpg")