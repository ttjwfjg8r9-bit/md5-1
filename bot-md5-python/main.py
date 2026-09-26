from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import uvicorn

from config import PORT

app = FastAPI(title="MD5 UI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


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
        <div class="value">120</div>
      </div>
      <div class="stat-box">
        <div class="label">Win</div>
        <div class="value">76</div>
      </div>
    </div>

    <div class="card">
      <div class="title">Prediction</div>
      <div class="prediction tai">TAI</div>
      <div class="meta"><span>Confidence</span><strong>82%</strong></div>
      <div class="meta"><span>Method</span><strong>UI</strong></div>
      <div class="dice-row">
        <div class="dice tai">4</div>
        <div class="dice xiu">2</div>
        <div class="dice tai">6</div>
      </div>
      <div class="status">UI-only mode</div>
    </div>

    <div class="card">
      <div class="title">Summary</div>
      <ul class="list">
        <li>Giao diện chỉ hiển thị</li>
        <li>Không fetch API bên ngoài</li>
        <li>Không cần token</li>
      </ul>
    </div>
  </div>
</body>
</html>
    """


@app.get("/api/bot/status")
def status():
    return {
        "status": "ui_only",
        "lastSession": None,
        "historyCount": 0,
        "stats": {"total": 0, "correct": 0, "wrong": 0},
        "prediction": {"pred": None, "confidence": 0, "reason": "ui only"},
        "canPredict": False,
    }


@app.get("/api/bot/predict")
def predict():
    return {
        "status": "ui_only",
        "lastSession": None,
        "historyCount": 0,
        "canPredict": False,
        "prediction": {"pred": None, "confidence": 0, "reason": "ui only"},
    }


@app.get("/api/bot/history")
def history_api():
    return {
        "status": "ui_only",
        "historyCount": 0,
        "lastSession": None,
        "history": [],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT)
