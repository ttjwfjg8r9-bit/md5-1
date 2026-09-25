from typing import Optional, Dict, Any, List


def analyze(history: List[dict]) -> Optional[Dict[str, Any]]:
    if len(history) < 18:
        return None
    outs = [h["outcome"] for h in history if h.get("outcome")]
    if len(outs) < 15:
        return None
    t10 = outs[-10:].count("TAI")
    t15 = outs[-15:].count("TAI")

    if t10 >= 8:
        return {"pred": "XIU", "score": 3.2, "reason": "DeepSeek: đảo cực 10"}
    if t10 <= 2:
        return {"pred": "TAI", "score": 3.2, "reason": "DeepSeek: đảo cực 10"}
    if t10 >= 7:
        return {"pred": "XIU", "score": 2.6, "reason": "DeepSeek: đảo mạnh"}
    if t10 <= 3:
        return {"pred": "TAI", "score": 2.6, "reason": "DeepSeek: đảo mạnh"}
    if t15 >= 11:
        return {"pred": "XIU", "score": 2.1, "reason": "DeepSeek: đảo 15"}
    if t15 <= 4:
        return {"pred": "TAI", "score": 2.1, "reason": "DeepSeek: đảo 15"}
    return None
