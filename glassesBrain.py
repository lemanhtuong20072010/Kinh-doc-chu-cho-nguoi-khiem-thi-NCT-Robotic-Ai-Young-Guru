import google.generativeai as genai
import cv2
import requests
import numpy as np
import edge_tts
import asyncio
import os
import PIL.Image
import time

# 1. Cấu hình AI (Nhớ bảo mật Key của bạn nhé!)
genai.configure(api_key="AIzaSyDll4_oq20Ps3BIrC6FL_IqToiNWDI2xHk")
model = genai.GenerativeModel('models/gemini-1.5-flash') # Dùng bản ổn định hơn

# 2. Cấu hình IP của ESP32 
ESP32_IP = "192.168.1.15" 
URL_CAPTURE = f"http://{ESP32_IP}/capture"
URL_BUTTON  = f"http://{ESP32_IP}/button"
URL_VOICE   = f"http://{ESP32_IP}/play_voice"

# 3. Hàm xử lý âm thanh và gửi cho ESP32
async def process_and_send_audio(text):
    print(f"AI phản hồi: {text}")
    output_file = "speech.mp3"
    
    # Tạo file âm thanh bằng Edge-TTS
    communicate = edge_tts.Communicate(text, "vi-VN-HoaiMyNeural", rate="+10%")
    await communicate.save(output_file)
    
    # Gửi file MP3 qua ESP32 bằng phương thức POST
    try:
        print("Đang truyền âm thanh đến kính...")
        with open(output_file, 'rb') as f:
            headers = {'Content-Type': 'audio/mpeg'}
            response = requests.post(URL_VOICE, data=f, headers=headers, timeout=10)
            if response.status_code == 200:
                print("Đã gửi âm thanh thành công.")
    except Exception as e:
        print(f"Lỗi khi gửi âm thanh: {e}")
    
    # Xóa file tạm sau khi gửi
    if os.path.exists(output_file):
        os.remove(output_file)

# 4. Hàm xử lý AI chính
def ai_xu_ly(frame):
    # Chuyển OpenCV sang PIL Image để Gemini đọc được
    cv2_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_img = PIL.Image.fromarray(cv2_img)
    
    try:
        # Gửi ảnh cho Gemini
        response = model.generate_content([
            "Bạn là một trợ lý thông minh hỗ trợ người khiếm thị đọc sách. Hãy nhìn vào ảnh làm đọc lại văn bản của cuốn sách", 
            pil_img
        ])
        
        # Chạy tiến trình gửi âm thanh
        asyncio.run(process_and_send_audio(response.text))
        
    except Exception as e:
        print(f"Lỗi AI: {e}")

# 5. Vòng lặp chính (Main Loop)
print("Hệ thống khởi động...")
print(f"Đang kết nối tới ESP32 tại: {ESP32_IP}")

while True:
    try:
        # Lấy luồng ảnh từ ESP32 để hiển thị lên máy tính (để mình biết kính đang nhìn gì)
        img_resp = requests.get(URL_CAPTURE, timeout=2)
        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)
        
        if frame is not None:
            cv2.imshow("Giao dien Kinh AI", frame)

        # KIỂM TRA NÚT BẤM VẬT LÝ TRÊN ESP32
        # Gửi request nhẹ đến endpoint /button
        try:
            btn_resp = requests.get(URL_BUTTON, timeout=0.1)
            if btn_resp.text == "1":
                print("--- Nút bấm đã được nhấn! ---")
                ai_xu_ly(frame)
                # Tạm dừng để tránh nhận diện liên tục khi nhấn giữ nút
                time.sleep(2) 
        except:
            pass # Bỏ qua nếu việc kiểm tra nút gặp lỗi mạng tạm thời

    except Exception as e:
        print("Đang đợi kết nối từ kính...")
        time.sleep(1)
        continue

cv2.destroyAllWindows()
