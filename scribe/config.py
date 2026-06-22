"""Single-file runtime config (`.scribe.yml`), with sane defaults.

Every key is optional. We deep-merge the user's file over `DEFAULTS` so a repo
can override one nested setting (say, `mr.target_branch`) without restating the
rest -- convention over configuration.
"""

from __future__ import annotations

import os

try:
    import yaml
except ImportError:  # pragma: no cover - yaml is a declared dependency
    yaml = None

DEFAULTS = {
    "source": "local",
    "core_count": 8,
    "drift_threshold": "minor",
    "sections": ["overview", "architecture", "layout"],
    "paths": {"include": ["**/*"], "exclude": []},
    "mr": {"target_branch": "main", "labels": ["scribe", "documentation"]},
}


def _merge(base: dict, override: dict | None) -> dict:
    out = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


def load_config(repo: str) -> dict:
    path = os.path.join(repo, ".scribe.yml")
    data: dict = {}
    if os.path.exists(path) and yaml is not None:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    return _merge(DEFAULTS, data)
