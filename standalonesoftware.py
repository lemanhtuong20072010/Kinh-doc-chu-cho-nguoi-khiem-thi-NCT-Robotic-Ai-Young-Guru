import cv2
import google.generativeai as genai
import edge_tts
import asyncio
import pygame
import os
import PIL.Image

# --- CẤU HÌNH AI ---
genai.configure(api_key="AIzaSyCAR9w9zDIQL4DJnGeWifja87oqsqc0SO0")
model = genai.GenerativeModel('models/gemini-3-flash-preview')
async def speak(text):
    """Sử dụng thư viện Edge-TTS để đọc giọng Hoài My"""
    communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural")
    await communicate.save("voice.mp3")
    
    pygame.mixer.init()
    pygame.mixer.music.load("voice.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy(): 
        await asyncio.sleep(0.1)
    pygame.mixer.quit()
    # Xóa file sau khi đọc xong để sạch bộ nhớ
    if os.path.exists("voice.mp3"):
        os.remove("voice.mp3")

# --- KHỞI TẠO WEBCAM ---
# '0' là camera mặc định của laptop MSI
cap = cv2.VideoCapture(0)

print("--- HỆ THỐNG KÍNH AI ĐÃ SẴN SÀNG ---")
print("Nhấn 'S' để Chụp ảnh và Đọc chữ")
print("Nhấn 'ESC' để Thoát")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Không thể kết nối Webcam!")
        break
    
    # Hiển thị khung hình lên màn hình máy tính
    cv2.imshow("Kinh cho người khiếm thị - NCT Robotics", frame)
    
    key = cv2.waitKey(1)
    
    # Nhấn 'S' (Scan) để bắt đầu nhận diện
    if key & 0xFF == ord('s') or key & 0xFF == ord('S'):
        print("Đang quét nội dung...")
        
        # Chuyển đổi định dạng ảnh cho Gemini
        cv2_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_img = PIL.Image.fromarray(cv2_img)
        
        try:
            # Gửi ảnh cho Gemini xử lý
            prompt = "Đây là gì? Nếu là văn bản, hãy đọc chính xác nội dung. Nếu là vật thể, hãy mô tả ngắn gọn trong 1 câu."
            response = model.generate_content([prompt, pil_img])
            
            result_text = response.text
            print("Kết quả AI:", result_text)
            
            # Phát âm thanh giọng Hoài My
            asyncio.run(speak(result_text))
            
        except Exception as e:
            print("Lỗi hệ thống:", e)
            
    # Nhấn ESC để thoát
    if key & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
