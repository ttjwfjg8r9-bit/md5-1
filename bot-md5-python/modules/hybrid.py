from typing import Optional, Dict, Any, List


def analyze(history: List[dict]) -> Optional[Dict[str, Any]]:
    if len(history) < 12:
        return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 8:
        return None
    last = outs[-1]
    streak = 1
    for i in range(len(outs) - 2, -1, -1):
        if outs[i] == last:
            streak += 1
        else:
            break

    if streak >= 6:
        return {"pred": "XIU" if last == "TAI" else "TAI", "score": 3.0, "reason": f"Hybrid: break {streak}"}
    if streak == 5:
        return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.6, "reason": "Hybrid: break 5"}
    if streak == 4:
        return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.0, "reason": "Hybrid: break 4"}
    if streak == 2:
        return {"pred": last, "score": 1.9, "reason": "Hybrid: follow 2"}
    if streak == 3:
        return {"pred": last, "score": 1.6, "reason": "Hybrid: follow 3"}
    return None
