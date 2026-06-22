"""The committed drift manifest -- Scribe's memory between runs.

Stored next to AGENTS.md, it records the fingerprint of the structure the file
was generated from. The next run compares against it to decide whether anything
drifted. `schema_version` is here so a future format change is detectable rather
than silently misread.
"""

from __future__ import annotations

import json

from .models import Definition, Module, RepoStructure

SCHEMA_VERSION = 2


def snapshot(struct: RepoStructure) -> dict:
    """Compact, sorted structure record stored in the manifest.

    Holds just what summarize() needs to describe drift in words next run --
    module paths and per-definition fan-in -- not the whole graph. Sorted so
    the manifest stays byte-stable.
    """
    return {
        "modules": sorted(m.path for m in struct.modules),
        "definitions": sorted([d.name, d.fan_in] for d in struct.definitions),
    }


def restore(snap: dict | None) -> RepoStructure | None:
    """Rebuild a minimal RepoStructure from a snapshot for summarize().

    Only the fields summarize() reads (module paths, definition name + fan-in)
    are populated; the rest are empty. Returns None when there is no snapshot.
    """
    if not snap:
        return None
    modules = tuple(Module(path=p, file_count=0) for p in snap.get("modules", []))
    definitions = tuple(
        Definition(name=name, kind="", path="", fan_in=int(fan))
        for name, fan in snap.get("definitions", [])
    )
    return RepoStructure(
        languages=(),
        modules=modules,
        definitions=definitions,
        test_paths=(),
        config_paths=(),
        owners=(),
    )


def build_manifest(
    fingerprint: str,
    section_fps: dict[str, str],
    orbit_source: str,
    generated_at: str,
    scribe_version: str,
    structure: dict | None = None,
) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "orbit_source": orbit_source,
        "fingerprint": fingerprint,
        "section_fingerprints": dict(sorted(section_fps.items())),
        "structure": structure or {},
        "scribe_version": scribe_version,
    }


def dumps(manifest: dict) -> str:
    return json.dumps(manifest, indent=2, sort_keys=True) + "\n"


def loads(text: str) -> dict:
    return json.loads(text)
