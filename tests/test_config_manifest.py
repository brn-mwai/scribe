from __future__ import annotations

import os

from scribe.config import load_config
from scribe.manifest import build_manifest, dumps, loads


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
        "fp123", {"overview": "h1"}, "local", "2026-01-01T00:00:00Z", "0.1.0"
    )
    assert manifest["fingerprint"] == "fp123"
    assert manifest["schema_version"] == 1
    restored = loads(dumps(manifest))
    assert restored == manifest


def test_manifest_dumps_is_stable():
    manifest = build_manifest(
        "fp", {"b": "2", "a": "1"}, "local", "2026-01-01T00:00:00Z", "0.1.0"
    )
    assert dumps(manifest) == dumps(manifest)
