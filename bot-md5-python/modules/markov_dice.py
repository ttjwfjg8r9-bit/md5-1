from typing import Optional, Dict, Any, List
from collections import defaultdict


class MarkovDice:
    def __init__(self):
        self.order1 = {}
        self.order2 = {}
        self.ALPHA = 1

    def learn(self, history: List[dict]):
        outs = [h["outcome"] for h in history if h.get("outcome")]
        window = min(len(outs), 250)
        recent = outs[-window:]
        self.order1 = defaultdict(lambda: {"TAI": 0, "XIU": 0})
        self.order2 = defaultdict(lambda: {"TAI": 0, "XIU": 0})
        for i in range(1, len(recent)):
            self.order1[recent[i - 1]][recent[i]] += 1
        for i in range(2, len(recent)):
            key = f"{recent[i - 2]}|{recent[i - 1]}"
            self.order2[key][recent[i]] += 1

    def _prob(self, counts):
        t = counts.get("TAI", 0) + self.ALPHA
        x = counts.get("XIU", 0) + self.ALPHA
        total = t + x
        return {"TAI": t / total, "XIU": x / total}

    def analyze(self, history: List[dict]) -> Optional[Dict[str, Any]]:
        if len(history) < 15:
            return None
        self.learn(history)
        outs = [h["outcome"] for h in history if h.get("outcome")]
        last = outs[-1]
        last2 = outs[-2] if len(outs) >= 2 else None

        if last2:
            key = f"{last2}|{last}"
            c = self.order2.get(key)
            if c and sum(c.values()) >= 5:
                p = self._prob(c)
                pred = "TAI" if p["TAI"] >= p["XIU"] else "XIU"
                conf = max(p.values())
                if conf >= 0.57:
                    return {"pred": pred, "score": 2.3 + (conf - 0.5) * 3, "reason": f"Markov-2 -> {pred} ({conf:.0%})"}

        c1 = self.order1.get(last)
        if c1 and sum(c1.values()) >= 8:
            p = self._prob(c1)
            pred = "TAI" if p["TAI"] >= p["XIU"] else "XIU"
            conf = max(p.values())
            if conf >= 0.55:
                return {"pred": pred, "score": 1.7 + (conf - 0.5) * 2, "reason": f"Markov-1 -> {pred} ({conf:.0%})"}
        return None


markov = MarkovDice()


def analyze(history):
    return markov.analyze(history)
