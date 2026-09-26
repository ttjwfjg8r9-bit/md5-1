from .evolution import SelfEvolution


class Brain:

    def __init__(self):
        self.evolution = SelfEvolution()

    def learn(self, history, actual):
        self.evolution.observe(
            history,
            actual
        )

    def think(self, history):

        result = self.evolution.predict(
            history
        )

        if result:
            return result

        if not history:
            return {
                "prediction": "TAI",
                "algorithm": "fallback"
            }

        return {
            "prediction": (
                "XIU"
                if history[-1] == "TAI"
                else "TAI"
            ),
            "algorithm": "fallback"
        }
