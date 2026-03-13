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
    # headers giả lập cực chi tiết để tránh bị web chặn
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Referer': 'https://google.com',
        'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    try:
        session = requests.Session() # Dùng session để giữ cookie
        response = session.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            st.error(f"Web chặn truy cập (Lỗi {response.status_code})")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        img_links = []
        
        # Tìm tất cả thẻ img
        for img in soup.find_all('img'):
            # Kiểm tra mọi thuộc tính có thể chứa link ảnh truyện
            src = (img.get('data-src') or 
                   img.get('data-original') or 
                   img.get('src') or 
                   img.get('data-cdn') or 
                   img.get('srcset'))
            
            if src:
                src = src.strip().split(' ')[0]
                full_src = urljoin(url, src)
                
                # Lọc lấy ảnh thực sự (bỏ qua icon, logo nhỏ)
                if any(ext in full_src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    if not any(bad in full_src.lower() for bad in ['logo', 'icon', 'avatar', 'button', 'loading']):
                        img_links.append(full_src)
        
        # Loại bỏ trùng lặp mà vẫn giữ đúng thứ tự
        return list(dict.fromkeys(img_links))
    except Exception as e:
        st.error(f"Lỗi kết nối web: {e}")
        return []

# --- GIAO DIỆN ---
st.title("📖 AI Comic Reviewer - Chuyên Gia Phân Tích Chapter")
url_chapter = st.text_input("Dán link Chapter truyện cần review:")

if st.button("Bắt đầu quét & Việt hóa nhân vật 🚀"):
    if url_chapter:
        with st.spinner("Đang tìm kiếm trang ảnh... (Có thể mất 10-20 giây)"):
            all_imgs = get_all_images_from_url(url_chapter)
            
        if all_imgs:
            st.success(f"Tìm thấy {len(all_imgs)} trang ảnh!")
            full_text = ""
            # Giới hạn số trang để review (tăng lên 7 trang để nội dung sâu hơn)
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
                        
                        # Sử dụng EasyOCR để lấy text
                        results = reader.readtext("temp.jpg", detail=0)
                        full_text += " ".join(results) + " "
                    except:
                        st.write(f"❌ Lỗi khi tải hoặc đọc trang {i+1}")
                progress_bar.progress((i + 1) / limit)

            if full_text.strip():
                with st.spinner("AI đang dịch thuật & Chuyển đổi tên nhân vật..."):
                    # Dịch sang tiếng Việt (giới hạn ký tự để tránh quá tải)
                    dich_tho = GoogleTranslator(source='auto', target='vi').translate(full_text[:3500])
                    
                    # Yêu cầu AI phân tích sâu
                    prompt = f"""
                    Dựa trên nội dung dịch thô từ truyện tranh sau: {dich_tho}
                    Yêu cầu:
                    1. Nhận diện các nhân vật chính/phụ. Nếu tên là tiếng Anh hoặc Pinyin (ví dụ: Lin Fan, Xiao Yan), hãy chuyển sang tên Hán Việt chuẩn (ví dụ: Lâm Phàm, Tiêu Viêm).
                    2. Tóm tắt diễn biến cốt truyện của tập này một cách kịch tính.
                    3. Viết bài review ngắn phân tích tâm lý nhân vật hoặc tình huống nổi bật.
                    4. Chấm điểm tập truyện trên thang điểm 10.
                    
                    Trình bày bằng Markdown thật đẹp mắt với các icon phù hợp.
                    """
                    review = ai_model.generate_content(prompt)
                
                st.divider()
                st.subheader("🤖 Kết quả phân tích từ AI")
                st.markdown(review.text)
            else:
                st.warning("Tìm thấy ảnh nhưng AI không thể quét được chữ. Có thể chữ quá nhỏ hoặc ảnh không có thoại.")
        else:
            st.error("Không tìm thấy ảnh. Có thể trang web này chặn bot hoặc link không đúng.")

# Dọn dẹp file tạm
if os.path.exists("temp.jpg"): 
    try: os.remove("temp.jpg")
    except: pass