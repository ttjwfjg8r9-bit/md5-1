from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from brain import Brain
from config import PORT

app = FastAPI(title="MD5 UI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

brain = Brain()


def _normalize_history(history):
    if not isinstance(history, list):
        return []

    cleaned = []
    for item in history:
        if isinstance(item, str):
            cleaned.append(item.upper())
        elif isinstance(item, dict):
            value = item.get("outcome") or item.get("result") or item.get("prediction")
            if isinstance(value, str):
                cleaned.append(value.upper())
        elif item is not None:
            cleaned.append(str(item).upper())
    return cleaned


async def _read_json_body(request: Request):
    try:
        return await request.json()
    except Exception:
        return {}


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
def root():
    return """
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MD5 UI</title>
  <style>
    :root {
      --bg: #071018;
      --panel: rgba(15, 23, 42, 0.96);
      --panel-2: rgba(9, 14, 22, 0.98);
      --line: rgba(148, 163, 184, 0.18);
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
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, sans-serif;
      display: grid;
      place-items: center;
      padding: 24px;
    }
    .wrap {
      width: min(420px, 100%);
      background: linear-gradient(180deg, var(--panel), var(--panel-2));
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 20px;
      box-shadow: 0 25px 60px rgba(0, 0, 0, 0.38);
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 18px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 800;
      letter-spacing: 1.5px;
      color: var(--cyan);
    }
    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--cyan);
      box-shadow: 0 0 14px var(--cyan);
    }
    .stats {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .stat-box {
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px 12px;
      text-align: center;
    }
    .label {
      color: var(--muted);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 1.3px;
    }
    .value {
      margin-top: 8px;
      font-size: 26px;
      font-weight: 800;
      color: var(--cyan);
    }
    .card {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: rgba(15, 23, 42, 0.9);
      margin-bottom: 16px;
    }
    .title {
      color: var(--cyan);
      font-weight: 700;
      letter-spacing: 1px;
      margin-bottom: 8px;
    }
    .prediction {
      text-align: center;
      font-size: 42px;
      font-weight: 800;
      letter-spacing: 1px;
      margin: 10px 0 12px;
      color: var(--gold);
    }
    .prediction.tai { color: var(--green); }
    .prediction.xiu { color: var(--red); }
    .meta {
      color: var(--muted);
      display: flex;
      justify-content: space-between;
      gap: 10px;
      margin-top: 8px;
      font-size: 12px;
    }
    .meta strong {
      color: var(--text);
    }
    .dice-row {
      display: flex;
      justify-content: center;
      gap: 10px;
      margin: 12px 0 4px;
    }
    .dice {
      width: 52px;
      height: 52px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: rgba(15, 23, 42, 0.8);
      font-weight: 800;
      font-size: 22px;
      color: var(--text);
    }
    .dice.tai { color: var(--green); border-color: rgba(74, 222, 128, 0.35); }
    .dice.xiu { color: var(--red); border-color: rgba(248, 113, 113, 0.35); }
    .status {
      text-align: center;
      margin-top: 10px;
      color: var(--gold);
      font-size: 12px;
    }
    .list {
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.8;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div class="brand"><span class="dot"></span>MD5 UI</div>
    </div>

    <div class="stats">
      <div class="stat-box">
        <div class="label">Total</div>
        <div id="totalValue" class="value">--</div>
      </div>
      <div class="stat-box">
        <div class="label">Win</div>
        <div id="winValue" class="value">--</div>
      </div>
    </div>

    <div class="card">
      <div class="title">Prediction</div>
      <div id="predictionValue" class="prediction tai">--</div>
      <div class="meta"><span>Confidence</span><strong id="confidenceValue">--</strong></div>
      <div class="meta"><span>Method</span><strong id="methodValue">--</strong></div>
      <div class="dice-row">
        <div class="dice tai">--</div>
        <div class="dice xiu">--</div>
        <div class="dice tai">--</div>
      </div>
      <div id="statusValue" class="status">Loading...</div>
    </div>

    <div class="card">
      <div class="title">Summary</div>
      <ul class="list">
        <li>Bot đang lấy dữ liệu từ backend</li>
        <li>Đồng bộ hóa tự động với engine</li>
        <li>Không cần token để xem dự đoán</li>
      </ul>
    </div>
  </div>

  <script>
    async function loadBotData() {
      try {
        const [predictRes, statusRes] = await Promise.all([
          fetch('/api/bot/predict'),
          fetch('/api/bot/status')
        ]);

        const predictData = await predictRes.json();
        const statusData = await statusRes.json();

        const prediction = predictData.prediction && predictData.prediction.pred ? predictData.prediction.pred : 'Chưa đủ dữ liệu';
        const confidence = predictData.prediction && predictData.prediction.confidence ? predictData.prediction.confidence : 0;
        const method = predictData.prediction && predictData.prediction.reason ? predictData.prediction.reason : 'insufficient_data';

        const predictionEl = document.getElementById('predictionValue');
        predictionEl.textContent = prediction;
        predictionEl.classList.remove('tai', 'xiu');
        if (prediction === 'TAI') predictionEl.classList.add('tai');
        else if (prediction === 'XIU') predictionEl.classList.add('xiu');

        document.getElementById('confidenceValue').textContent = predictData.canPredict ? `${confidence}%` : '--';
        document.getElementById('methodValue').textContent = predictData.canPredict ? method : 'insufficient_data';

        const total = statusData.stats && statusData.stats.total ? statusData.stats.total : 0;
        const win = statusData.stats && statusData.stats.correct ? statusData.stats.correct : 0;
        document.getElementById('totalValue').textContent = total;
        document.getElementById('winValue').textContent = win;

        const statusEl = document.getElementById('statusValue');
        statusEl.textContent = predictData.canPredict ? 'Live brain prediction' : 'Chưa đủ dữ liệu để dự đoán';
      } catch (error) {
        document.getElementById('predictionValue').textContent = 'Chưa đủ dữ liệu';
        document.getElementById('statusValue').textContent = 'Bot unavailable';
      }
    }

    document.addEventListener('DOMContentLoaded', loadBotData);
  </script>
</body>
</html>
    """


@app.get("/api/bot/status")
def status():
    memory = getattr(brain.evolution, "memory", {})
    history = memory.get("history", []) or []
    algorithms = brain.evolution.algorithms.get("algorithms", []) or []
    can_predict = len(history) >= 3 and bool(algorithms)
    return {
        "status": "online",
        "lastSession": history[-1] if history else None,
        "historyCount": len(history),
        "stats": {
            "total": len(algorithms),
            "correct": sum(1 for item in algorithms if item.get("status") == "active"),
            "wrong": sum(1 for item in algorithms if item.get("status") in {"weak", "disabled"}),
        },
        "prediction": {"pred": None, "confidence": 0, "reason": "insufficient_data" if not can_predict else "brain ready"},
        "canPredict": can_predict,
    }


@app.post("/api/bot/learn")
async def learn_bot(request: Request):
    payload = await _read_json_body(request)
    history = _normalize_history(payload.get("history", []))
    actual = str(payload.get("actual", "")).upper()

    if actual in {"TAI", "XIU"}:
        brain.learn(history, actual)
        return {"status": "ok", "updated": True, "historyCount": len(history)}

    return {"status": "ok", "updated": False, "historyCount": len(history)}


@app.post("/api/bot/predict")
async def predict_bot(request: Request):
    payload = await _read_json_body(request)
    history = _normalize_history(payload.get("history", []))
    result = brain.think(history)

    if not result:
        return {
            "status": "ok",
            "canPredict": False,
            "historyCount": len(history),
            "prediction": {"pred": None, "confidence": 0, "reason": "insufficient_data"},
        }

    accuracy = result.get("accuracy", 0.0)
    prediction = result.get("prediction")
    return {
        "status": "ok",
        "canPredict": True,
        "historyCount": len(history),
        "prediction": {
            "pred": prediction,
            "confidence": round(float(accuracy) * 100, 1),
            "reason": result.get("algorithm", "brain"),
            "algorithm": result.get("algorithm", "fallback"),
        },
    }


@app.get("/api/bot/predict")
def predict():
    history = []
    result = brain.think(history)
    if not result:
        return {
            "status": "ok",
            "lastSession": None,
            "historyCount": 0,
            "canPredict": False,
            "prediction": {"pred": None, "confidence": 0, "reason": "insufficient_data"},
        }

    return {
        "status": "ok",
        "lastSession": None,
        "historyCount": 0,
        "canPredict": True,
        "prediction": {"pred": result.get("prediction"), "confidence": 0, "reason": result.get("algorithm", "brain")},
    }


@app.get("/api/bot/history")
def history_api():
    memory = getattr(brain.evolution, "memory", {})
    system_history = memory.get("history", []) or []
    return {
        "status": "ok",
        "historyCount": len(system_history),
        "lastSession": system_history[-1] if system_history else None,
        "history": system_history,
        "system_history": system_history,
    }


@app.get("/api/bot/learning-history")
def learning_history_api():
    memory = getattr(brain.evolution, "memory", {})
    patterns = memory.get("patterns", {}) or {}
    real_history = []

    for pattern, stats in patterns.items():
        samples = stats.get("samples", 0)
        if samples <= 0:
            continue
        real_history.append({
            "pattern": pattern,
            "samples": samples,
            "TAI": stats.get("TAI", 0),
            "XIU": stats.get("XIU", 0),
        })

    system_history = memory.get("history", []) or []
    return {
        "status": "ok",
        "historyCount": len(real_history),
        "real_history": real_history,
        "system_history": system_history,
    }


@app.post("/api/bot/sync")
async def sync_bot(request: Request):
    payload = await _read_json_body(request)
    message = str(payload.get("message") or "brain:auto-sync")
    result = brain.sync_git(message)
    return {"status": "ok", "sync": result}


@app.get("/api/bot/sync-status")
def sync_status():
    return {
        "status": "ok",
        "enabled": brain.sync.enabled,
        "remote": brain.sync.remote,
        "branch": brain.sync.branch,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
