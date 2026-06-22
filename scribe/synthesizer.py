"""Structure -> markdown sections (pure, the editorial core).

This module owns *what an AGENTS.md says*: which facts go in which section and
in what order. It depends only on the normalized structure -- no Orbit, no files,
no LLM -- which is what keeps the most opinion-heavy part of Scribe fully
unit-testable and deterministic. Every fact rendered here traces back to the
graph; the module never invents conventions (NG-10).
"""

from __future__ import annotations

from .extractor import module_tree, rank_core
from .models import RepoStructure, Section

DEFAULT_CORE = 8
KNOWN_SECTIONS = ("overview", "architecture", "layout")


def _overview(struct: RepoStructure, core_count: int) -> str:
    languages = ", ".join(struct.languages) if struct.languages else "unknown"
    lines = [
        "## Project overview",
        "",
        f"- **Languages:** {languages}",
        f"- **Modules:** {len(struct.modules)}",
        f"- **Definitions:** {len(struct.definitions)}",
    ]
    if struct.owners:
        lines.append(f"- **Owners:** {', '.join(struct.owners)}")
    return "\n".join(lines)


def _architecture(struct: RepoStructure, core_count: int) -> str:
    lines = ["## Architecture map", "", "### Modules", ""]
    for module in module_tree(struct):
        plural = "" if module.file_count == 1 else "s"
        lines.append(f"- `{module.path}` ({module.file_count} file{plural})")
    lines += ["", "### Core components", ""]
    for definition in rank_core(struct, core_count):
        lines.append(
            f"- `{definition.name}` ({definition.kind}) in "
            f"`{definition.path}` -- fan-in {definition.fan_in}"
        )
    return "\n".join(lines)


def _layout(struct: RepoStructure, core_count: int) -> str:
    lines = ["## Where things live", "", "- **Tests:**"]
    if struct.test_paths:
        lines += [f"  - `{p}`" for p in struct.test_paths]
    else:
        lines.append("  - none detected")
    lines.append("- **Config:**")
    if struct.config_paths:
        lines += [f"  - `{p}`" for p in struct.config_paths]
    else:
        lines.append("  - none detected")
    return "\n".join(lines)


_BUILDERS = {
    "overview": _overview,
    "architecture": _architecture,
    "layout": _layout,
}


def synthesize(
    struct: RepoStructure,
    sections: list[str],
    core_count: int = DEFAULT_CORE,
) -> list[Section]:
    """Build the requested sections, in request order, skipping unknown keys.

    All builders share the `(struct, core_count)` signature so the dispatch table
    stays uniform; sections that do not need the count simply ignore it.
    """
    out: list[Section] = []
    for key in sections:
        builder = _BUILDERS.get(key)
        if builder is None:
            continue
        out.append(Section(key=key, markdown=builder(struct, core_count)))
    return out
