from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import math

VN_TZ = timezone(timedelta(hours=7))
MEMORY_FILE = Path("brain_auto_patterns.json")


def get_hour(ts=None) -> int:
    if ts is None:
        return datetime.now(VN_TZ).hour
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(VN_TZ).hour
        except Exception:
            pass
    return datetime.now(VN_TZ).hour


def get_frame(hour: int) -> str:
    if 5 <= hour < 11:
        return "sang"
    if 11 <= hour < 14:
        return "trua"
    if 14 <= hour < 18:
        return "chieu"
    if 18 <= hour < 23:
        return "toi"
    return "dem"


class AutoBrain:
    def __init__(self):
        self.patterns = {}
        self.last_size = 0
        self.load()

    def load(self):
        if MEMORY_FILE.exists():
            try:
                data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                self.patterns = data.get("patterns", {})
                print(f"Nao load {len(self.patterns)} mau")
            except Exception:
                pass

    def save(self):
        MEMORY_FILE.write_text(json.dumps({"patterns": self.patterns}, ensure_ascii=False), encoding="utf-8")

    def learn(self, history: List[dict]):
        if len(history) < 8 or len(history) == self.last_size:
            return
        outs = [h.get("outcome") for h in history if h.get("outcome")]
        for length in range(2, 7):
            for i in range(length, len(outs)):
                key = "|".join(outs[i - length:i])
                nxt = outs[i]
                if key not in self.patterns:
                    self.patterns[key] = {"next": {"TAI": 0, "XIU": 0}, "total": 0, "score": 0}
                p = self.patterns[key]
                p["next"][nxt] += 1
                p["total"] += 1
                conf = max(p["next"].values()) / p["total"]
                p["score"] = conf * (1 + math.log1p(p["total"]) * 0.35)
        if len(self.patterns) > 1200:
            top = sorted(self.patterns.items(), key=lambda x: x[1]["score"], reverse=True)[:900]
            self.patterns = dict(top)
        self.last_size = len(history)
        self.save()

    def think(self, history: List[dict]) -> Optional[Dict[str, Any]]:
        if len(history) < 10:
            return None
        self.learn(history)
        outs = [h.get("outcome") for h in history if h.get("outcome")]
        if len(outs) < 5:
            return None
        hour = get_hour(history[-1].get("receivedAt"))
        frame = get_frame(hour)
        best = None
        best_score = 0
        for length in range(6, 1, -1):
            if len(outs) < length:
                continue
            key = "|".join(outs[-length:])
            info = self.patterns.get(key)
            if not info or info["total"] < 3 or info["score"] < 0.55:
                continue
            tai = info["next"].get("TAI", 0)
            xiu = info["next"].get("XIU", 0)
            total = tai + xiu
            if total == 0:
                continue
            conf = max(tai, xiu) / total
            pred = "TAI" if tai >= xiu else "XIU"
            score = info["score"] * 0.7 + conf * 0.3
            if score > best_score:
                best_score = score
                best = {
                    "pred": pred,
                    "score": round(1.9 + score * 2.1, 2),
                    "reason": f"Nao[{frame}]: {key[-16:]} -> {pred} ({conf:.0%} n={info['total']})",
                    "frame": frame,
                }
        return best


auto_brain = AutoBrain()


def analyze(history):
    return auto_brain.think(history)
