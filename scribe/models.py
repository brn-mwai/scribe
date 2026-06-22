"""Core data contracts shared across the pipeline.

These are frozen and tuple-backed on purpose: the whole engine promises
byte-identical output for identical input (NFR-1), so every value that flows
through it must be immutable and order-stable. Mutable lists would invite an
accidental in-place sort somewhere downstream and break determinism.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Definition:
    name: str
    kind: str
    path: str
    fan_in: int = 0


@dataclass(frozen=True)
class Module:
    path: str
    file_count: int
    summary: str = ""


@dataclass(frozen=True)
class RepoStructure:
    languages: tuple[str, ...]
    modules: tuple[Module, ...]
    definitions: tuple[Definition, ...]
    test_paths: tuple[str, ...]
    config_paths: tuple[str, ...]
    owners: tuple[str, ...] = ()


@dataclass(frozen=True)
class Section:
    key: str
    markdown: str
