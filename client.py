import time
import requests
import pyautogui

SERVER_URL = "https://monitoring-server-ftu4.onrender.com/upload_screen"
CLIENT_NAME = "Store-PC-01"

print("=== 모니터링 클라이언트 디버깅 시작 ===")

def main():
    while True:
        start_time = time.time()
        sleep_time = 3.0  
        
        try:
            # 1. 화면 캡처
            screenshot = pyautogui.screenshot()
            screenshot.save("screen.jpg", "JPEG")
            
            # 2. 서버로 전송 시도
            with open("screen.jpg", "rb") as f:
                files = {"file": ("screen.jpg", f, "image/jpeg")}
                data = {"client_name": CLIENT_NAME}
                
                print(f"서버로 전송 시도 중... ({SERVER_URL})")
                res = requests.post(SERVER_URL, data=data, files=files, timeout=5)
                
                # 서버가 뭐라고 응답하는지 출력
                print(f"서버 응답 결과 코드: {res.status_code}")
                print(f"서버 응답 내용: {res.text}")
                
                if res.status_code == 200:
                    res_data = res.json()
                    command = res_data.get("command", "normal")
                    if command == "live":
                        sleep_time = 0.5  
                    else:
                        sleep_time = 3.0  
                else:
                    print(f"⚠️ 서버 거부 또는 에러 발생 (코드: {res.status_code})")
                            
        except Exception as e:
            # 통신 실패 시 정확히 어떤 에러인지 콘솔에 출력
            print(f"❌ 통신 중 예외(에러) 발생: {e}")
            sleep_time = 3.0
            
        elapsed = time.time() - start_time
        actual_sleep = max(0.1, sleep_time - elapsed)
        time.sleep(actual_sleep)

if __name__ == "__main__":
    main()