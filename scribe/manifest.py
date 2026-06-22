"""The committed drift manifest -- Scribe's memory between runs.

Stored next to AGENTS.md, it records the fingerprint of the structure the file
was generated from. The next run compares against it to decide whether anything
drifted. `schema_version` is here so a future format change is detectable rather
than silently misread.
"""

from __future__ import annotations

import json

SCHEMA_VERSION = 1


def build_manifest(
    fingerprint: str,
    section_fps: dict[str, str],
    orbit_source: str,
    generated_at: str,
    scribe_version: str,
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "orbit_source": orbit_source,
        "fingerprint": fingerprint,
        "section_fingerprints": dict(sorted(section_fps.items())),
        "scribe_version": scribe_version,
    }


def dumps(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def loads(text: str) -> dict:
    return json.loads(text)
