from typing import List, Dict, Any
from modules.deepseek import analyze as deepseek_analyze
from modules.hybrid import analyze as hybrid_analyze
from modules.markov_dice import analyze as markov_analyze
from modules.soi_cau_pro import analyze as soi_cau_analyze
from modules.brain_tu_phan_tich import analyze as brain_analyze

WEIGHTS = {
    "deepseek": 1.70,
    "hybrid": 1.55,
    "markov": 1.50,
    "soiCau": 1.55,
    "brain": 2.00,
}

MODULES = [
    ("deepseek", deepseek_analyze),
    ("hybrid", hybrid_analyze),
    ("markov", markov_analyze),
    ("soiCau", soi_cau_analyze),
    ("brain", brain_analyze),
]


def ensemble_predict(history: List[dict]) -> Dict[str, Any]:
    if len(history) < 10:
        return {"pred": None, "confidence": 0, "reason": "Dang warmup", "active": 0}

    scores = {"TAI": 0.0, "XIU": 0.0}
    reasons = []
    active = 0

    for name, fn in MODULES:
        try:
            res = fn(history)
            if not res or not res.get("pred"):
                continue
            w = WEIGHTS.get(name, 1.0)
            s = float(res.get("score", 1.0)) * w
            scores[res["pred"]] += s
            reasons.append(res.get("reason", name))
            active += 1
        except Exception as e:
            print(f"Module {name} loi:", e)

    if scores["TAI"] == 0 and scores["XIU"] == 0:
        recent = [h["outcome"] for h in history[-6:] if h.get("outcome")]
        tai = recent.count("TAI")
        pred = "XIU" if tai >= 4 else "TAI" if tai <= 2 else ("XIU" if recent[-1] == "TAI" else "TAI")
        return {"pred": pred, "confidence": 52, "reason": "Fallback", "active": 0}

    pred = "TAI" if scores["TAI"] > scores["XIU"] else "XIU"
    diff = abs(scores["TAI"] - scores["XIU"])
    conf = min(50 + diff * 7 + active * 2, 88)

    return {
        "pred": pred,
        "confidence": round(conf),
        "reason": " | ".join(reasons[:3]) + f" | {active} modules",
        "active": active,
        "scores": scores,
    }
