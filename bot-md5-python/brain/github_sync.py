import os
import subprocess


class GitHubSync:

    def __init__(self):
        self.enabled = os.getenv(
            "AUTO_GIT_PUSH",
            "false"
        ).lower() == "true"
        self.remote = os.getenv("GIT_REMOTE", "origin")
        self.branch = os.getenv("GIT_BRANCH") or "HEAD"
        self.author_name = os.getenv("GIT_AUTHOR_NAME", "Brain Auto Evolution")
        self.author_email = os.getenv("GIT_AUTHOR_EMAIL", "brain@localhost")

    def run(self, command):
        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            cwd=os.getcwd(),
        )

        if result.returncode != 0:
            raise RuntimeError(
                (result.stderr or result.stdout or "git command failed").strip()
            )

        return result.stdout

    def sync(self, message):
        if not self.enabled:
            return {
                "status": "disabled"
            }

        try:
            self.run("git rev-parse --is-inside-work-tree")
        except Exception:
            return {
                "status": "not_git_repo"
            }

        self.run(
            f"git config user.name '{self.author_name}'"
        )

        self.run(
            f"git config user.email '{self.author_email}'"
        )

        self.run(
            "git add generated/ memory/ brain/"
        )

        status = self.run(
            "git status --porcelain"
        )

        if not status.strip():
            return {
                "status": "nothing_to_commit"
            }

        self.run(
            f"git commit -m \"{message}\""
        )

        push_target = self.branch if self.branch and self.branch != "HEAD" else "HEAD"
        self.run(
            f"git push {self.remote} {push_target}"
        )

        return {
            "status": "pushed"
        }
