from __future__ import annotations

import os

from scribe.config import load_config
from scribe.drift import summarize
from scribe.manifest import build_manifest, dumps, loads, restore, snapshot
from scribe.models import Definition, Module, RepoStructure


def _struct(modules, definitions):
    return RepoStructure(
        languages=(),
        modules=tuple(Module(path=p, file_count=0) for p in modules),
        definitions=tuple(
            Definition(name=n, kind="", path="", fan_in=f) for n, f in definitions
        ),
        test_paths=(),
        config_paths=(),
        owners=(),
    )


def test_config_defaults_when_no_file(tmp_path):
    cfg = load_config(str(tmp_path))
    assert cfg["source"] == "local"
    assert cfg["core_count"] == 8
    assert cfg["drift_threshold"] == "minor"


def test_config_merges_override(tmp_path):
    path = os.path.join(str(tmp_path), ".scribe.yml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("core_count: 3\nmr:\n  target_branch: develop\n")
    cfg = load_config(str(tmp_path))
    assert cfg["core_count"] == 3
    assert cfg["mr"]["target_branch"] == "develop"
    assert cfg["mr"]["labels"] == ["scribe", "documentation"]


def test_manifest_build_and_roundtrip():
    manifest = build_manifest(
        "fp123",
        {"overview": "h1"},
        "local",
        "2026-01-01T00:00:00Z",
        "0.1.0",
        {"modules": ["a/"], "definitions": [["x", 1]]},
    )
    assert manifest["fingerprint"] == "fp123"
    assert manifest["schema_version"] == 2
    assert manifest["structure"]["modules"] == ["a/"]
    restored = loads(dumps(manifest))
    assert restored == manifest


def test_snapshot_is_sorted_and_deterministic():
    struct = _struct(["z/", "a/"], [("Zeta", 1), ("Alpha", 2)])
    snap = snapshot(struct)
    assert snap["modules"] == ["a/", "z/"]
    assert snap["definitions"] == [["Alpha", 2], ["Zeta", 1]]
    assert snapshot(struct) == snap


def test_restore_empty_is_none():
    assert restore({}) is None
    assert restore(None) is None


def test_snapshot_restore_feeds_summarize_specific_line():
    old = _struct(["api/"], [("AuthService", 3)])
    new = _struct(["api/", "billing/"], [("AuthService", 7)])
    previous = restore(loads(dumps(snapshot(old))))
    text = summarize(previous, new)
    assert "1 new module(s): `billing/`" in text
    assert "`AuthService` fan-in +4" in text


def test_manifest_dumps_is_stable():
    manifest = build_manifest(
        "fp", {"b": "2", "a": "1"}, "local", "2026-01-01T00:00:00Z", "0.1.0"
    )
    assert dumps(manifest) == dumps(manifest)
