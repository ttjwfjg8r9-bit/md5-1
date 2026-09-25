from typing import Optional, Dict, Any, List


def analyze(history: List[dict]) -> Optional[Dict[str, Any]]:
    if len(history) < 8:
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
        return {"pred": "XIU" if last == "TAI" else "TAI", "score": 3.4, "reason": f"SoiCau: Be {streak}"}
    if streak == 5:
        return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.7, "reason": "SoiCau: Be 5"}
    if streak == 2:
        return {"pred": last, "score": 1.9, "reason": "SoiCau: Follow 2"}

    last6 = outs[-6:]
    if all(last6[i] != last6[i - 1] for i in range(1, len(last6))):
        return {"pred": "XIU" if last == "TAI" else "TAI", "score": 2.5, "reason": "SoiCau: 1-1"}
    return None
