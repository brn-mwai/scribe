from __future__ import annotations

from ..models import RepoStructure


def owners_for(struct: RepoStructure) -> list[str]:
    return sorted(struct.owners)


def has_ownership(struct: RepoStructure) -> bool:
    return bool(struct.owners)
