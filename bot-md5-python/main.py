import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn
from datetime import datetime, timezone

from config import PORT, FETCH_INTERVAL, WARMUP_ROUNDS, MAX_HISTORY
from core.fetch import fetch_data
from core.state import load_state, save_state
from core.ensemble import ensemble_predict

state = load_state()
history = state.get("history", [])
stats = state.get("stats", {"total": 0, "correct": 0, "wrong": 0})
last_session = state.get("last_session")
websocket_clients: set[WebSocket] = set()


async def broadcast_update():
    if not websocket_clients:
        return

    payload = {
        "status": "running",
        "lastSession": last_session,
        "historyCount": len(history),
        "stats": stats,
        "prediction": ensemble_predict(history),
        "canPredict": len(history) >= WARMUP_ROUNDS,
    }
    disconnected = set()
    for client in websocket_clients:
        try:
            await client.send_json(payload)
        except Exception:
            disconnected.add(client)
    websocket_clients.difference_update(disconnected)


async def background_loop():
    global history, stats, last_session
    while True:
        try:
            data = await fetch_data()
            if not data:
                await asyncio.sleep(FETCH_INTERVAL)
                continue

            data.sort(key=lambda x: x.get("GameSessionID", 0))
            new_items = [x for x in data if x.get("GameSessionID", 0) > (last_session or 0)]

            for item in new_items:
                sid = item["GameSessionID"]
                d1, d2, d3 = int(item["Dice1"]), int(item["Dice2"]), int(item["Dice3"])
                total = d1 + d2 + d3
                outcome = "TAI" if total > 10 else "XIU"

                pred_result = ensemble_predict(history)

                if history and history[-1].get("pred"):
                    stats["total"] += 1
                    if history[-1]["pred"] == outcome:
                        stats["correct"] += 1
                    else:
                        stats["wrong"] += 1

                history.append({
                    "sessionId": sid,
                    "dice": [d1, d2, d3],
                    "sum": total,
                    "outcome": outcome,
                    "pred": pred_result.get("pred"),
                    "confidence": pred_result.get("confidence", 0),
                    "reason": pred_result.get("reason", ""),
                    "receivedAt": datetime.now(timezone.utc).isoformat(),
                })

                if len(history) > MAX_HISTORY:
                    history = history[-1800:]

                last_session = sid
                print(f"Van {sid}: {d1}-{d2}-{d3} = {total} ({outcome})")
                if pred_result.get("pred"):
                    print(f"Du doan: {pred_result['pred']} ({pred_result.get('confidence')}%) | {pred_result.get('reason')}")

            if new_items:
                save_state({"history": history, "stats": stats, "last_session": last_session})
                await broadcast_update()

        except Exception as e:
            print("Loop error:", e)
        await asyncio.sleep(FETCH_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(background_loop())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        websocket_clients.clear()


app = FastAPI(title="Bot MD5 Python", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <!DOCTYPE html>
    <html lang="vi">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>MD5 Dashboard</title>
      <style>
        :root {
          --bg: #070b14;
          --panel: #101827;
          --panel-2: #0f172a;
          --line: #1e293b;
          --text: #e2e8f0;
          --muted: #94a3b8;
          --cyan: #22d3ee;
          --green: #4ade80;
          --red: #f87171;
          --gold: #fbbf24;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          font-family: Arial, sans-serif;
          background: var(--bg);
          color: var(--text);
          padding: 20px;
        }
        .wrap {
          max-width: 760px;
          margin: 0 auto;
        }
        .card {
          background: linear-gradient(180deg, var(--panel), var(--panel-2));
          border: 1px solid var(--line);
          border-radius: 16px;
          padding: 18px;
          margin-bottom: 16px;
          box-shadow: 0 10px 30px rgba(0,0,0,.2);
        }
        .top {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }
        .stat {
          background: #0b1220;
          border: 1px solid var(--line);
          border-radius: 12px;
          padding: 12px;
          text-align: center;
        }
        .label {
          color: var(--muted);
          font-size: 11px;
          letter-spacing: 1.3px;
          text-transform: uppercase;
        }
        .value {
          margin-top: 8px;
          font-size: 28px;
          font-weight: 800;
          color: var(--cyan);
        }
        .title {
          color: var(--cyan);
          font-weight: 700;
          letter-spacing: 1px;
          margin-bottom: 10px;
        }
        .row {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          margin: 8px 0;
          color: var(--muted);
        }
        .badge {
          font-weight: 700;
          color: var(--text);
        }
        .prediction {
          font-size: 42px;
          font-weight: 800;
          text-align: center;
          padding: 12px 0;
        }
        .TAI { color: var(--green); }
        .XIU { color: var(--red); }
        .WAIT { color: var(--gold); font-size: 28px; }
        .history {
          max-height: 260px;
          overflow: auto;
          font-family: monospace;
          font-size: 12px;
          color: var(--muted);
          background: #050b14;
          border: 1px solid var(--line);
          border-radius: 10px;
          padding: 10px;
        }
        .history-item {
          padding: 4px 0;
          border-bottom: 1px solid rgba(148,163,184,.15);
        }
        .history-item:last-child { border-bottom: none; }
        .status {
          color: var(--gold);
          font-size: 13px;
          margin-top: 10px;
        }
        @media (max-width: 600px) {
          body { padding: 12px; }
          .top { grid-template-columns: 1fr; }
        }
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="top">
          <div class="stat">
            <div class="label">History</div>
            <div class="value" id="historyCount">0</div>
          </div>
          <div class="stat">
            <div class="label">Win rate</div>
            <div class="value" id="winRate">0%</div>
          </div>
        </div>

        <div class="card">
          <div class="title">MD5 LIVE PREDICTION</div>
          <div class="row"><span>Last session</span><span class="badge" id="lastSession">-</span></div>
          <div class="row"><span>Can predict</span><span class="badge" id="canPredict">-</span></div>
          <div class="prediction WAIT" id="prediction">WAITING</div>
          <div class="row"><span>Confidence</span><span class="badge" id="confidence">-</span></div>
          <div class="row"><span>Reason</span><span class="badge" id="reason">-</span></div>
          <div class="status" id="statusText">Loading...</div>
        </div>

        <div class="card">
          <div class="title">HISTORY</div>
          <div class="history" id="historyBox">Loading history...</div>
        </div>
      </div>

      <script>
        async function fetchJson(url) {
          const res = await fetch(url, { cache: 'no-store' });
          if (!res.ok) throw new Error('Request failed: ' + res.status);
          return await res.json();
        }

        function setPrediction(data) {
          const pred = data.prediction || {};
          const predText = pred.pred || 'WAITING';
          const el = document.getElementById('prediction');
          el.textContent = predText === 'WAITING' ? 'WAITING' : (predText === 'TAI' ? 'TAI' : 'XIU');
          el.className = 'prediction ' + (predText === 'WAITING' ? 'WAIT' : predText);
          document.getElementById('confidence').textContent = pred.confidence ? pred.confidence + '%' : '-';
          document.getElementById('reason').textContent = pred.reason || '-';
          document.getElementById('canPredict').textContent = data.canPredict ? 'YES' : 'NO';
          document.getElementById('lastSession').textContent = data.lastSession ?? '-';
          document.getElementById('statusText').textContent = data.status || 'Running';
        }

        function setHistory(data) {
          const items = data.history || [];
          document.getElementById('historyCount').textContent = items.length;
          const correct = items.filter(item => item.pred && item.outcome && item.pred === item.outcome).length;
          const winRate = items.length ? Math.round((correct / items.length) * 100) : 0;
          document.getElementById('winRate').textContent = winRate + '%';

          const html = items.slice(-20).reverse().map(item => {
            const outcome = item.outcome || '-';
            const pred = item.pred || '-';
            return '<div class="history-item">#' + (item.sessionId ?? '-') + ' · ' + item.dice + ' · pred=' + pred + ' · result=' + outcome + '</div>';
          }).join('') || '<div class="history-item">No history yet</div>';

          document.getElementById('historyBox').innerHTML = html;
        }

        async function refresh() {
          try {
            const pred = await fetchJson('/api/bot/predict');
            setPrediction(pred);
            const hist = await fetchJson('/api/bot/history');
            setHistory(hist);
          } catch (err) {
            document.getElementById('statusText').textContent = 'Error: ' + err.message;
          }
        }

        refresh();
        setInterval(refresh, 3000);
      </script>
    </body>
    </html>
    """


@app.get("/api/bot/status")
def status():
    pred = ensemble_predict(history)
    return {
        "status": "running",
        "lastSession": last_session,
        "historyCount": len(history),
        "stats": stats,
        "prediction": pred,
        "canPredict": len(history) >= WARMUP_ROUNDS,
    }


@app.get("/api/bot/predict")
def predict():
    pred = ensemble_predict(history)
    return {
        "status": "running",
        "lastSession": last_session,
        "historyCount": len(history),
        "canPredict": len(history) >= WARMUP_ROUNDS,
        "prediction": pred,
    }


@app.get("/api/bot/history")
def history_api():
    return {
        "status": "running",
        "historyCount": len(history),
        "lastSession": last_session,
        "history": history[-50:],
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_clients.add(websocket)
    try:
        await websocket.send_json(status())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        websocket_clients.discard(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
