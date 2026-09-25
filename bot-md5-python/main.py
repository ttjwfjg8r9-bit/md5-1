import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/")
def root():
    return {"status": "running", "history": len(history), "stats": stats}


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
