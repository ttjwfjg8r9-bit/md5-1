import json
import math
import os
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MEMORY_FILE = ROOT / "memory" / "brain_memory.json"
ALGORITHM_FILE = ROOT / "generated" / "algorithms.json"
BACKUP_DIR = ROOT / "generated" / "backups"

MIN_SAMPLES = 30
PROMOTE_ACCURACY = 0.60
DISABLE_ACCURACY = 0.48


class SelfEvolution:

    def __init__(self):
        MEMORY_FILE.parent.mkdir(exist_ok=True)
        ALGORITHM_FILE.parent.mkdir(exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

        self.memory = self._load(
            MEMORY_FILE,
            {
                "patterns": {},
                "algorithms": {},
                "history": []
            }
        )

        self.algorithms = self._load(
            ALGORITHM_FILE,
            {
                "version": 1,
                "algorithms": []
            }
        )

    def _load(self, path, default):
        try:
            if not path.exists():
                return default

            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception:
            return default

    def _save(self, path, data):
        tmp = str(path) + ".tmp"

        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

        os.replace(tmp, path)

    def _backup(self):
        if not ALGORITHM_FILE.exists():
            return

        name = time.strftime(
            "algorithms_%Y%m%d_%H%M%S.json"
        )

        shutil.copy2(
            ALGORITHM_FILE,
            BACKUP_DIR / name
        )

    def pattern_key(self, history):
        return "|".join(history)

    def observe(self, history, actual):

        if len(history) < 3:
            return

        key = self.pattern_key(history[-7:])

        patterns = self.memory["patterns"]

        if key not in patterns:
            patterns[key] = {
                "TAI": 0,
                "XIU": 0,
                "samples": 0
            }

        p = patterns[key]

        if actual not in ("TAI", "XIU"):
            return

        p[actual] += 1
        p["samples"] += 1

        self._save(MEMORY_FILE, self.memory)

        self._discover(key, p)

    def _discover(self, key, stats):

        samples = stats["samples"]

        if samples < MIN_SAMPLES:
            return

        tai = stats["TAI"]
        xiu = stats["XIU"]

        prediction = "TAI" if tai >= xiu else "XIU"

        hits = max(tai, xiu)
        accuracy = hits / samples

        z = 1.96
        phat = accuracy

        denominator = 1 + z * z / samples

        centre = (
            phat +
            z * z / (2 * samples)
        )

        spread = z * math.sqrt(
            (
                phat * (1 - phat)
                + z * z / (4 * samples)
            ) / samples
        )

        lower_bound = (
            centre - spread
        ) / denominator

        self._update_algorithm(
            key,
            prediction,
            samples,
            accuracy,
            lower_bound
        )

    def _update_algorithm(
        self,
        key,
        prediction,
        samples,
        accuracy,
        lower_bound
    ):

        algorithms = self.algorithms["algorithms"]

        found = None

        for algorithm in algorithms:
            if algorithm["pattern"] == key:
                found = algorithm
                break

        if found is None:

            if (
                samples >= MIN_SAMPLES
                and lower_bound >= 0.52
            ):
                self._backup()

                found = {
                    "id": f"auto_{len(algorithms)+1:05d}",
                    "pattern": key,
                    "prediction": prediction,
                    "samples": samples,
                    "accuracy": accuracy,
                    "lower_bound": lower_bound,
                    "weight": 1.0,
                    "status": "active",
                    "created_at": time.time()
                }

                algorithms.append(found)

                self.memory["history"].append({
                    "event": "NEW_ALGORITHM",
                    "pattern": key,
                    "prediction": prediction,
                    "samples": samples,
                    "accuracy": accuracy,
                    "time": time.time()
                })

        else:

            found["prediction"] = prediction
            found["samples"] = samples
            found["accuracy"] = accuracy
            found["lower_bound"] = lower_bound

            if accuracy >= 0.65:
                found["weight"] = min(
                    3.0,
                    found["weight"] + 0.05
                )

            elif accuracy < 0.55:
                found["weight"] = max(
                    0.25,
                    found["weight"] - 0.05
                )

            if (
                samples >= MIN_SAMPLES
                and lower_bound < 0.50
            ):
                found["status"] = "disabled"

            elif accuracy >= PROMOTE_ACCURACY:
                found["status"] = "active"

            elif accuracy <= DISABLE_ACCURACY:
                found["status"] = "weak"

        self.algorithms["version"] += 1

        self._save(
            ALGORITHM_FILE,
            self.algorithms
        )

        self._save(
            MEMORY_FILE,
            self.memory
        )

    def predict(self, history):

        if len(history) < 3:
            return None

        best = None

        for algorithm in self.algorithms["algorithms"]:

            if algorithm["status"] != "active":
                continue

            pattern = algorithm["pattern"]
            current = self.pattern_key(history[-7:])

            if pattern != current:
                continue

            if best is None:
                best = algorithm
                continue

            score_a = (
                algorithm["accuracy"]
                * algorithm["weight"]
            )

            score_b = (
                best["accuracy"]
                * best["weight"]
            )

            if score_a > score_b:
                best = algorithm

        if best:
            return {
                "prediction": best["prediction"],
                "algorithm": best["id"],
                "accuracy": best["accuracy"],
                "weight": best["weight"]
            }

        return None
