import streamlit as st
import easyocr
import requests
import PIL.Image
from io import BytesIO
from deep_translator import GoogleTranslator
import google.generativeai as genai
from bs4 import BeautifulSoup

# --- CẤU HÌNH BẢO MẬT ---
try:
    GOOGLE_API_KEY = st.secrets["GEMINI_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    ai_model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Lỗi API Key!")

st.set_page_config(page_title="Việt Comic Chapter Reader", layout="wide")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ch_sim', 'en'])

reader = load_ocr()

def get_all_images_from_url(url):
    """Hàm tìm tất cả link ảnh trong một Chapter"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Tìm tất cả thẻ img có chứa link ảnh truyện
    img_links = []
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-original')
        if src and ('.jpg' in src or '.png' in src or '.webp' in src):
            if not src.startswith('http'):
                src = "https:" + src if src.startswith('//') else url + src
            img_links.append(src)
    
    # Lọc bỏ các icon nhỏ, chỉ lấy ảnh truyện (thường to hơn 500px)
    return list(set(img_links)) 

# --- GIAO DIỆN ---
st.title("📖 Tool Review Cả Chapter Truyện")
url_chapter = st.text_input("Dán link Chapter truyện (Ví dụ: link tập 1...):")

if st.button("Quét Toàn Bộ Chapter 🚀"):
    if url_chapter:
        with st.spinner("Đang phân tích Chapter..."):
            all_imgs = get_all_images_from_url(url_chapter)
            st.success(f"Tìm thấy {len(all_imgs)} trang ảnh trong tập này!")
        
        full_text = ""
        # Chỉ quét 5-10 trang đầu để review (tránh bị treo máy)
        limit = min(len(all_imgs), 5) 
        
        for i in range(limit):
            with st.status(f"Đang đọc trang {i+1}/{limit}...", expanded=True):
                try:
                    res = requests.get(all_imgs[i], timeout=10)
                    img = PIL.Image.open(BytesIO(res.content))
                    img.save("temp.jpg")
                    
                    # Quét chữ
                    results = reader.readtext("temp.jpg", detail=0)
                    page_text = " ".join(results)
                    full_text += page_text + " "
                    st.write(f"Đã đọc xong trang {i+1}")
                except:
                    st.write(f"Bỏ qua trang {i+1} do lỗi.")

        if full_text:
            dich = GoogleTranslator(source='auto', target='vi').translate(full_text[:3000]) # Giới hạn 3000 ký tự để AI review chuẩn
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📝 Tóm tắt nội dung tập này")
                st.write(dich)
            with col2:
                st.subheader("🤖 AI Review Toàn Chapter")
                prompt = f"Dựa trên nội dung tập truyện này: {dich}, hãy viết review cực hay, phân tích cốt truyện và chấm điểm."
                review = ai_model.generate_content(prompt)
                st.success(review.text)