"""Structural hashing for drift detection (pure).

The fingerprint is the heart of the self-healing loop. It must be sensitive to
real structural change (a renamed definition, a new module, a new reference that
shifts fan-in) yet blind to cosmetic edits (whitespace, comments). We get that
for free by hashing only the normalized structure -- never source text -- over a
sorted, set-like canonical form so element order cannot affect the digest.
"""

from __future__ import annotations

import hashlib
import json

from .models import RepoStructure, Section


def _canonical(struct: RepoStructure) -> dict:
    """Flatten the structure to sorted string sets the hash can depend on.

    References are folded in via each definition's fan-in: add or remove a
    cross-file reference and the affected entry changes, so the digest changes.
    """
    return {
        "modules": sorted(m.path for m in struct.modules),
        "definitions": sorted(
            f"{d.path}::{d.name}::{d.kind}" for d in struct.definitions
        ),
        "references": sorted(
            f"{d.path}::{d.name}#{d.fan_in}" for d in struct.definitions
        ),
    }


def fingerprint(struct: RepoStructure) -> str:
    blob = json.dumps(_canonical(struct), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def section_fingerprint(section: Section) -> str:
    return hashlib.sha256(section.markdown.encode("utf-8")).hexdigest()


def section_fingerprints(sections: list[Section]) -> dict[str, str]:
    return {s.key: section_fingerprint(s) for s in sections}
