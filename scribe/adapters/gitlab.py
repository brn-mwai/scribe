"""The only code that opens merge requests.

Scribe's action is a reviewable MR, never an auto-merge -- that human gate is the
trust contract. The shell commands are produced by a pure `mr_commands()` so the
exact `git`/`glab` invocation can be asserted in a test without a real GitLab,
and `dry_run` returns the would-be plan instead of touching anything.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable


def build_mr_body(drift_summary: str, files: dict[str, str]) -> str:
    """Render the MR description: the drift summary plus the files touched."""
    lines = [
        "## Scribe -- context update",
        "",
        drift_summary,
        "",
        "### Files touched",
        "",
    ]
    lines += [f"- `{name}`" for name in sorted(files)]
    lines += [
        "",
        "_Opened by Scribe. Review and merge. Scribe never merges on its own._",
    ]
    return "\n".join(lines)


def mr_commands(
    branch: str,
    title: str,
    body: str,
    labels: list[str],
    paths: list[str],
    target_branch: str = "main",
) -> list[list[str]]:
    """The ordered git + glab commands that stage, push, and open the MR.

    Pure and side-effect-free so it can be asserted directly; the adapter's
    runner is what actually executes the list.
    """
    return [
        ["git", "checkout", "-b", branch],
        ["git", "add", *paths],
        ["git", "commit", "-m", title],
        ["git", "push", "-u", "origin", branch],
        [
            "glab",
            "mr",
            "create",
            "--title",
            title,
            "--description",
            body,
            "--label",
            ",".join(labels),
            "--source-branch",
            branch,
            "--target-branch",
            target_branch,
            "--yes",
        ],
    ]


class GitLabAdapter:
    def __init__(
        self,
        runner: Callable[[str, dict], str] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.dry_run = dry_run
        self._runner = runner or self._default_runner

    def open_mr(
        self,
        repo: str,
        branch: str,
        files: dict[str, str],
        title: str,
        body: str,
        labels: list[str],
        target_branch: str = "main",
    ) -> object:
        """Open an MR for `files`, or return the plan unchanged when dry_run."""
        plan = {
            "repo": repo,
            "branch": branch,
            "title": title,
            "body": body,
            "labels": list(labels),
            "target_branch": target_branch,
            "files": dict(files),
        }
        if self.dry_run:
            return plan
        return self._runner(repo, plan)

    @staticmethod
    def _default_runner(repo: str, plan: dict) -> str:
        written: list[str] = []
        for rel_path, content in plan["files"].items():
            abs_path = os.path.join(repo, rel_path)
            os.makedirs(os.path.dirname(abs_path) or repo, exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            written.append(rel_path)

        commands = mr_commands(
            branch=plan["branch"],
            title=plan["title"],
            body=plan["body"],
            labels=plan["labels"],
            paths=written,
            target_branch=plan["target_branch"],
        )
        last = ""
        for command in commands:
            proc = subprocess.run(
                command, cwd=repo, capture_output=True, text=True, check=True
            )
            last = proc.stdout.strip()
        return last
