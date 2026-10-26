from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import HTMLResponse, Response

app = FastAPI()

screenshots = {}      
client_commands = {}  

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Multi-PC Secure Operations Center</title>
        <style>
            body { background-color: #121212; color: #ffffff; font-family: sans-serif; text-align: center; padding: 20px; }
            h2 { color: #00ffcc; }
            .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; margin-top: 20px; }
            .card { background: #1e1e1e; border: 2px solid #444; border-radius: 8px; padding: 10px; width: 420px; cursor: pointer; transition: 0.2s; }
            .card:hover { border-color: #00ffcc; }
            .card.live { border-color: #ff4444; box-shadow: 0 0 10px rgba(255, 68, 68, 0.5); }
            .card h3 { margin: 5px 0; color: #fff; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .badge-normal { background: #444; color: #ccc; }
            .badge-live { background: #ff4444; color: #fff; }
            img { width: 100%; border-radius: 4px; margin-top: 10px; border: 1px solid #333; }
        </style>
    </head>
    <body>
        <h2>MULTI-PC LIVE MONITORING CENTER</h2>
        <p>💡 <b>화면을 클릭하면</b> 해당 PC만 골라서 <b>[일반(3초) ⇄ 집중확인(0.5초)]</b> 모드로 전환됩니다.</p>
        <div id="container" class="grid">접속 중인 PC를 검색 중입니다...</div>

        <script>
            let knownClients = new Set();

            async function updateDashboard() {
                try {
                    const res = await fetch('/api/clients');
                    const data = await res.json();
                    const container = document.getElementById('container');
                    
                    if (data.clients.length === 0) {
                        container.innerHTML = '<p style="color: #888;">접속 중인 클라이언트 PC가 없습니다.</p>';
                        knownClients.clear();
                        return;
                    }

                    const currentClientNames = new Set(data.clients.map(c => c.name));
                    let needFullRender = clientListChanged(knownClients, currentClientNames);
                    
                    if (needFullRender) {
                        knownClients = currentClientNames;
                        let html = '';
                        for (let c of data.clients) {
                            const isLive = c.command === 'live';
                            const cardClass = isLive ? 'card live' : 'card';
                            const badgeClass = isLive ? 'badge badge-live' : 'badge badge-normal';
                            const badgeText = isLive ? '🔥 집중확인 모드 (0.5초)' : '일반 모드 (3초)';

                            html += `
                                <div id="card-${c.name}" class="${cardClass}" onclick="toggleMode('${c.name}', '${c.command}')">
                                    <h3>🖥️ ${c.name}</h3>
                                    <span id="badge-${c.name}" class="${badgeClass}">${badgeText}</span>
                                    <div>
                                        <img id="img-${c.name}" src="/get_screen/${c.name}?t=${new Date().getTime()}" alt="${c.name} screen" />
                                    </div>
                                </div>
                            `;
                        }
                        container.innerHTML = html;
                    }

                    for (let c of data.clients) {
                        const img = document.getElementById(`img-${c.name}`);
                        if (img) {
                            const currentSrc = img.src.split('?')[0];
                            img.src = `${currentSrc}?t=${new Date().getTime()}`;
                        }

                        const card = document.getElementById(`card-${c.name}`);
                        const badge = document.getElementById(`badge-${c.name}`);
                        if (card && badge) {
                            const isLive = c.command === 'live';
                            card.className = isLive ? 'card live' : 'card';
                            badge.className = isLive ? 'badge badge-live' : 'badge badge-normal';
                            badge.innerText = isLive ? '🔥 집중확인 모드 (0.5초)' : '일반 모드 (3초)';
                            card.setAttribute("onclick", `toggleMode('${c.name}', '${c.command}')`);
                        }
                    }

                } catch (e) {
                    console.error(e);
                }
            }

            function clientListChanged(setA, setB) {
                if (setA.size !== setB.size) return true;
                for (let item of setA) {
                    if (!setB.has(item)) return true;
                }
                return false;
            }

            async function toggleMode(clientName, currentCommand) {
                const newMode = currentCommand === 'live' ? 'normal' : 'live';
                await fetch('/set_mode', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ client_name: clientName, mode: newMode })
                });
                updateDashboard();
            }

            setInterval(updateDashboard, 500);
            updateDashboard();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content, media_type="text/html")

@app.get("/api/clients")
async def get_clients():
    clients_list = []
    for name in screenshots.keys():
        clients_list.append({
            "name": name,
            "command": client_commands.get(name, "normal")
        })
    return {"clients": clients_list}

@app.post("/upload_screen")
async def upload_screen(file: UploadFile = File(...), client_name: str = Form("target_pc")):
    screenshots[client_name] = await file.read()
    current_cmd = client_commands.get(client_name, "normal")
    return {"status": "success", "command": current_cmd}

@app.get("/get_screen/{client_name}")
async def get_screen(client_name: str):
    if client_name in screenshots:
        return Response(content=screenshots[client_name], media_type="image/jpeg")
    return Response(status_code=404)

@app.post("/set_mode")
async def set_mode(payload: dict = Body(...)):
    client_name = payload.get("client_name")
    mode = payload.get("mode", "normal")
    if client_name:
        client_commands[client_name] = mode
    return {"result": "ok", "client_name": client_name, "set_mode": mode}