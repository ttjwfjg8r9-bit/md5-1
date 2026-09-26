"""Helper discovery layer for the self-evolution brain."""

from .evolution import SelfEvolution


class PatternDiscovery:
    def __init__(self):
        self.engine = SelfEvolution()

    def update(self, history, actual):
        self.engine.observe(history, actual)

    def recommend(self, history):
        return self.engine.predict(history)
