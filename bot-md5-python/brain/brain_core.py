from .evolution import SelfEvolution
from .github_sync import GitHubSync


class Brain:

    def __init__(self):
        self.evolution = SelfEvolution()
        self.sync = GitHubSync()

    def sync_git(self, message):
        try:
            return self.sync.sync(message)
        except Exception as exc:  # pragma: no cover - keeps bot alive even when git is unavailable
            return {"status": "error", "message": str(exc)}

    def learn(self, history, actual):
        self.evolution.observe(
            history,
            actual
        )

        if actual in {"TAI", "XIU"}:
            self.sync_git("brain:learn")

    def think(self, history):

        if not history or len(history) < 3:
            return None

        result = self.evolution.predict(
            history
        )

        if result:
            return result

        return None
