"""Selection logic over an already-normalized structure (pure).

The Extractor answers one question for the Synthesizer: which definitions are
"load-bearing" enough to name in AGENTS.md? Fan-in (inbound reference count) is
the proxy. Ranking and sorting live here so the Synthesizer stays purely about
editorial layout.
"""

from __future__ import annotations

from .models import Definition, Module, RepoStructure

# Definition kinds that are structural noise, not "components" a reader orients
# around: struct/dataclass fields, module markers, imports, bare constants. A
# heavily-referenced field (e.g. `id`) is real but not illuminating.
NOISE_KINDS = frozenset(
    {
        "field",
        "module",
        "moduleexport",
        "import",
        "variable",
        "constant",
        "property",
        "parameter",
        "lambda",
    }
)


def rank_core(struct: RepoStructure, n: int) -> list[Definition]:
    """Return the n most-referenced production definitions, highest fan-in first.

    Two exclusions keep the list illuminating: definitions in test files (a
    heavily-called test helper is not a "core component"), and structural-noise
    kinds (fields, module markers). Ties break on (path, name) so the order is
    stable regardless of the order Orbit returned rows in -- a hard requirement
    for a byte-stable AGENTS.md.
    """
    test_files = set(struct.test_paths)
    production = [
        d
        for d in struct.definitions
        if d.path not in test_files and d.kind.lower() not in NOISE_KINDS
    ]
    ranked = sorted(production, key=lambda d: (-d.fan_in, d.path, d.name))
    return ranked[: max(n, 0)]


def module_tree(struct: RepoStructure) -> list[Module]:
    """Modules sorted by path, ready to render as an architecture map."""
    return sorted(struct.modules, key=lambda m: m.path)
