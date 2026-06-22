"""Drift classification and human-readable change summaries (pure).

Two jobs, kept separate from config policy on purpose:
  - classify() decides how *much* changed (none/minor/material) from fingerprints.
  - opens_mr() applies the repo's configured floor to decide whether that warrants
    an MR. Keeping the measurement free of policy lets us unit-test boundaries
    without threading config through, and lets a team retune chattiness via config
    alone.
"""

from __future__ import annotations

from .models import RepoStructure

NONE = "none"
MINOR = "minor"
MATERIAL = "material"
_ORDER = {NONE: 0, MINOR: 1, MATERIAL: 2}


def classify(
    old_fp: str | None,
    new_fp: str,
    section_fps_old: dict[str, str],
    section_fps_new: dict[str, str],
    threshold: float = 0.5,
) -> str:
    """Grade the gap between two runs as none | minor | material.

    `threshold` is the fraction of sections that must change for the drift to be
    "material" -- at or above it is material, below it is minor. Equal top-level
    fingerprints short-circuit to none (the common, cheap no-op case).
    """
    if old_fp == new_fp:
        return NONE
    keys = set(section_fps_old) | set(section_fps_new)
    if not keys:
        return MATERIAL
    changed = sum(
        1 for k in keys if section_fps_old.get(k) != section_fps_new.get(k)
    )
    if changed == 0:
        return MINOR
    ratio = changed / len(keys)
    return MATERIAL if ratio >= threshold else MINOR


def opens_mr(drift_class: str, config_threshold: str) -> bool:
    """Policy gate: does this drift class clear the repo's configured floor?"""
    floor = MINOR if config_threshold == "minor" else MATERIAL
    return drift_class != NONE and _ORDER[drift_class] >= _ORDER[floor]


def summarize(old: RepoStructure | None, new: RepoStructure) -> str:
    """One-line, human-readable account of what moved -- becomes the MR body.

    Reviewers should grasp the change without reading the diff: new/removed
    modules and the single largest fan-in swing. First runs have no `old` to
    compare against, so they get a plain count instead.
    """
    if old is None:
        return (
            f"Initial AGENTS.md: {len(new.modules)} modules, "
            f"{len(new.definitions)} definitions."
        )

    old_modules = {m.path for m in old.modules}
    new_modules = {m.path for m in new.modules}
    added = sorted(new_modules - old_modules)
    removed = sorted(old_modules - new_modules)

    old_fan = {d.name: d.fan_in for d in old.definitions}
    deltas: list[tuple[int, str, int]] = []
    for d in new.definitions:
        prev = old_fan.get(d.name)
        if prev is not None and d.fan_in != prev:
            deltas.append((abs(d.fan_in - prev), d.name, d.fan_in - prev))
    deltas.sort(reverse=True)

    parts: list[str] = []
    if added:
        parts.append(
            f"{len(added)} new module(s): " + ", ".join(f"`{m}`" for m in added)
        )
    if removed:
        parts.append(
            f"{len(removed)} removed module(s): "
            + ", ".join(f"`{m}`" for m in removed)
        )
    if deltas:
        _, name, delta = deltas[0]
        sign = "+" if delta > 0 else ""
        parts.append(f"`{name}` fan-in {sign}{delta}")
    return "; ".join(parts) if parts else "Structural change detected."
