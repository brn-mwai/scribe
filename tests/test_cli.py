from __future__ import annotations

import json
import os

import pytest
from typer.testing import CliRunner

from scribe.cli import app

runner = CliRunner()


def _seed_graph(tmp_path) -> str:
    graph = {
        "files": [
            {"path": "core/engine.py", "language": "Python"},
            {"path": "core/util.py", "language": "Python"},
            {"path": "tests/test_engine.py", "language": "Python"},
        ],
        "definitions": [
            {"name": "Engine", "kind": "class", "path": "core/engine.py"},
            {"name": "helper", "kind": "function", "path": "core/util.py"},
        ],
        "references": [
            {"from": "core/util.py", "to_def": "Engine"},
            {"from": "tests/test_engine.py", "to_def": "Engine"},
        ],
    }
    graph_path = os.path.join(str(tmp_path), "graph.json")
    with open(graph_path, "w", encoding="utf-8") as fh:
        json.dump(graph, fh)
    return graph_path


def test_dry_run_prints_diff_and_exits_zero(tmp_path, monkeypatch):
    graph_path = _seed_graph(tmp_path)
    monkeypatch.setenv("SCRIBE_GRAPH", graph_path)
    result = runner.invoke(app, ["run", "--repo", str(tmp_path), "--dry-run"])
    assert result.exit_code == 0
    assert "scribe:begin overview" in result.stdout
    assert "drift: material" in result.stdout
    assert not os.path.exists(os.path.join(str(tmp_path), "AGENTS.md"))


def test_check_reports_drift_when_no_manifest(tmp_path, monkeypatch):
    graph_path = _seed_graph(tmp_path)
    monkeypatch.setenv("SCRIBE_GRAPH", graph_path)
    result = runner.invoke(app, ["check", "--repo", str(tmp_path)])
    assert result.exit_code == 1
    assert "drift=material" in result.stdout


def test_run_writes_files_and_check_is_clean(tmp_path, monkeypatch):
    graph_path = _seed_graph(tmp_path)
    monkeypatch.setenv("SCRIBE_GRAPH", graph_path)

    captured = {}

    def fake_runner(repo, plan):
        captured.update(plan)
        return "https://gitlab.com/mr/42"

    import scribe.cli as cli_mod

    monkeypatch.setattr(
        cli_mod.GitLabAdapter, "_default_runner", staticmethod(fake_runner)
    )

    result = runner.invoke(app, ["run", "--repo", str(tmp_path)])
    assert result.exit_code == 0
    assert "opened MR" in result.stdout
    assert os.path.exists(os.path.join(str(tmp_path), "AGENTS.md"))
    assert os.path.exists(
        os.path.join(str(tmp_path), ".scribe", "scribe-manifest.json")
    )

    check = runner.invoke(app, ["check", "--repo", str(tmp_path)])
    assert check.exit_code == 0
    assert "current" in check.stdout
