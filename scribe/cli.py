"""CLI orchestration -- the thin wrapper that wires the pure core to the world.

`run` walks the pipeline (structure -> synthesize -> render -> fingerprint ->
drift gate) and, on a first run or material drift, opens an MR. `check` is the
CI-friendly read-only sibling: exit 0 when AGENTS.md is current, 1 when it has
drifted. All I/O (Orbit, git, the clock, the filesystem) is confined to this
file and the adapters so the engine underneath stays deterministic and testable.
"""

from __future__ import annotations

import datetime as _dt
import difflib
import os
import sys

import typer

from . import __version__
from .adapters.gitlab import GitLabAdapter, build_mr_body
from .adapters.orbit import OrbitAdapter
from .config import load_config
from .drift import classify, opens_mr, summarize
from .fingerprint import fingerprint, section_fingerprints
from .manifest import build_manifest, dumps, loads
from .renderer import render
from .synthesizer import synthesize

app = typer.Typer(add_completion=False, help="Scribe -- self-healing AGENTS.md.")

AGENTS_FILE = "AGENTS.md"
MANIFEST_FILE = "scribe-manifest.json"
MANIFEST_DIR = ".scribe"
BRANCH = "scribe/update-agents-md"


def _manifest_rel() -> str:
    return f"{MANIFEST_DIR}/{MANIFEST_FILE}"


def _read(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _make_adapter(source: str) -> OrbitAdapter:
    # SCRIBE_GRAPH points the adapter at a recorded graph JSON instead of a live
    # `orbit` binary -- the offline path used for demos, CI, and the e2e test.
    graph = os.environ.get("SCRIBE_GRAPH")
    if graph:
        def runner(repo: str, src: str, _graph: str = graph) -> str:
            return _read(_graph)

        return OrbitAdapter(source=source, runner=runner)
    return OrbitAdapter(source=source)


def _engine(repo: str, cfg: dict):
    adapter = _make_adapter(cfg["source"])
    struct = adapter.structure(repo)
    sections = synthesize(struct, cfg["sections"], cfg["core_count"])
    return struct, sections


def _diff(old: str, new: str) -> str:
    lines = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile="AGENTS.md (current)",
        tofile="AGENTS.md (scribe)",
    )
    text = "".join(lines)
    return text or "(no change)"


@app.command()
def run(
    repo: str = typer.Option(".", "--repo", help="Target repository path."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print diff, open no MR."),
) -> None:
    """Generate or heal AGENTS.md; open a corrective MR on first run or drift."""
    cfg = load_config(repo)
    struct, sections = _engine(repo, cfg)

    agents_path = os.path.join(repo, AGENTS_FILE)
    manifest_path = os.path.join(repo, MANIFEST_DIR, MANIFEST_FILE)
    existing = _read(agents_path)
    new_md = render(existing, sections)

    new_fp = fingerprint(struct)
    new_sfps = section_fingerprints(sections)

    first_run = not os.path.exists(manifest_path)
    if first_run:
        drift_class = "material"
        old_sfps: dict[str, str] = {}
        old_fp = None
    else:
        old_manifest = loads(_read(manifest_path))
        old_fp = old_manifest.get("fingerprint")
        old_sfps = old_manifest.get("section_fingerprints", {})
        drift_class = classify(old_fp, new_fp, old_sfps, new_sfps)

    if dry_run:
        typer.echo(_diff(existing, new_md))
        typer.echo(f"\n# drift: {drift_class}")
        raise typer.Exit(0)

    if not first_run and not opens_mr(drift_class, cfg["drift_threshold"]):
        typer.echo(f"scribe: drift={drift_class}; below threshold, nothing to do.")
        raise typer.Exit(0)

    os.makedirs(os.path.join(repo, MANIFEST_DIR), exist_ok=True)
    with open(agents_path, "w", encoding="utf-8") as fh:
        fh.write(new_md)
    manifest = build_manifest(
        new_fp, new_sfps, cfg["source"], _now(), __version__
    )
    manifest_text = dumps(manifest)
    with open(manifest_path, "w", encoding="utf-8") as fh:
        fh.write(manifest_text)

    summary = summarize(None, struct) if first_run else "Structure drift detected."
    files = {AGENTS_FILE: new_md, _manifest_rel(): manifest_text}
    body = build_mr_body(summary, files)
    gitlab = GitLabAdapter()
    result = gitlab.open_mr(
        repo,
        BRANCH,
        files,
        "docs: update AGENTS.md (scribe)",
        body,
        cfg["mr"]["labels"],
        cfg["mr"]["target_branch"],
    )
    typer.echo(f"scribe: opened MR -> {result}")


@app.command()
def check(
    repo: str = typer.Option(".", "--repo", help="Target repository path."),
) -> None:
    """Read-only drift check for CI: exit 0 if current, 1 if drifted."""
    cfg = load_config(repo)
    struct, sections = _engine(repo, cfg)
    new_fp = fingerprint(struct)
    new_sfps = section_fingerprints(sections)

    manifest_path = os.path.join(repo, MANIFEST_DIR, MANIFEST_FILE)
    if not os.path.exists(manifest_path):
        typer.echo("scribe: no manifest; drift=material")
        raise typer.Exit(1)

    manifest = loads(_read(manifest_path))
    drift_class = classify(
        manifest.get("fingerprint"),
        new_fp,
        manifest.get("section_fingerprints", {}),
        new_sfps,
    )
    if drift_class == "none":
        typer.echo("scribe: AGENTS.md is current.")
        raise typer.Exit(0)
    typer.echo(f"scribe: drift={drift_class}")
    raise typer.Exit(1)


def main() -> None:
    # AGENTS.md is UTF-8 and routinely contains arrows and box glyphs. Default
    # Windows consoles are cp1252 and would crash printing them, so force UTF-8
    # on our streams before Typer writes anything.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    app()


if __name__ == "__main__":
    main()
