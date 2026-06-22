from __future__ import annotations

from scribe.adapters.gitlab import GitLabAdapter, build_mr_body, mr_commands


def test_build_mr_body_contains_summary_and_files():
    body = build_mr_body("3 new modules", {"AGENTS.md": "x", ".scribe/m.json": "y"})
    assert "3 new modules" in body
    assert "`AGENTS.md`" in body
    assert "never merges" in body


def test_mr_commands_shape():
    cmds = mr_commands(
        "scribe/x", "title", "body", ["scribe"], ["AGENTS.md"], "main"
    )
    assert cmds[0] == ["git", "checkout", "-b", "scribe/x"]
    glab = cmds[-1]
    assert glab[:3] == ["glab", "mr", "create"]
    assert "--target-branch" in glab
    assert "main" in glab


def test_dry_run_returns_plan():
    adapter = GitLabAdapter(dry_run=True)
    plan = adapter.open_mr(
        "/repo", "scribe/x", {"AGENTS.md": "data"}, "t", "b", ["scribe"]
    )
    assert plan["branch"] == "scribe/x"
    assert plan["files"] == {"AGENTS.md": "data"}


def test_open_mr_invokes_runner():
    captured = {}

    def runner(repo, plan):
        captured.update(plan)
        return "https://gitlab.com/mr/1"

    adapter = GitLabAdapter(runner=runner)
    url = adapter.open_mr(
        "/repo", "scribe/x", {"AGENTS.md": "data"}, "t", "b", ["scribe"], "main"
    )
    assert url == "https://gitlab.com/mr/1"
    assert captured["title"] == "t"
    assert captured["target_branch"] == "main"
