# Scribe — Implementation plan

> This turns `scribe-system-design.md` into ordered, testable tasks. Build **top to
> bottom**. After each task, run its acceptance check and the full suite
> (`pytest -q`); commit only when green. Do not start the next task until the current
> one passes.

## Ground rules

- Pure core = no I/O. `extractor`, `synthesizer`, `renderer`, `fingerprint`, `drift` must not touch the network, filesystem, or subprocesses. Side effects live in `adapters/`.
- Determinism: same input ⇒ byte-identical output. Sort everything with explicit keys.
- Test alongside code. Target 30+ meaningful tests by T8.
- Scribe edits only its own managed blocks. Never clobber human content.

## Data contracts (define first, in `scribe/models.py`)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Definition:
    name: str
    kind: str          # "method" | "class" | "function" | ...
    path: str
    fan_in: int        # number of inbound references

@dataclass(frozen=True)
class Module:
    path: str          # e.g. "payments/"
    file_count: int
    summary: str = ""  # short, may be empty

@dataclass(frozen=True)
class RepoStructure:
    languages: list[str]
    modules: list[Module]
    definitions: list[Definition]
    test_paths: list[str]
    config_paths: list[str]
    owners: list[str] = ()   # optional (Orbit Remote)

@dataclass(frozen=True)
class Section:
    key: str           # "overview" | "architecture" | "layout"
    markdown: str      # body that goes between the managed markers

# manifest = {schema_version, generated_at, orbit_source, fingerprint,
#             section_fingerprints, scribe_version}
```

> Implementation note: the shipped `models.py` uses immutable `tuple` fields instead
> of `list` so frozen structures stay hashable and can never be sorted in place —
> determinism over convenience.

---

## Tasks

### T0 — Scaffold
- Create `pyproject.toml` (package `scribe`, `console_scripts: scribe = scribe.cli:main`, deps: `typer`, `pyyaml`; dev: `pytest`).
- Create package skeleton (`scribe/`, `scribe/adapters/`, `tests/`, `tests/fixtures/`).
- Add MIT `LICENSE`, a `.gitlab-ci.yml` running `pytest`, and a stub `scribe/cli.py` with `--help`.
- **Acceptance:** `pip install -e ".[dev]"` succeeds; `scribe --help` runs; `pytest -q` collects cleanly.

### T1 — Orbit Adapter (`scribe/adapters/orbit.py`)
- `class OrbitAdapter` with `def structure(repo: str) -> RepoStructure`.
- Local path: shell out to `glab orbit local query` (JSON DSL) and/or `orbit sql` to pull files, definitions, and reference edges; compute `fan_in` from inbound references. Call `get_graph_schema` first to confirm entity names.
- Keep the raw-query layer (`runner`) separate from the normalization layer (`normalize`) so a recorded fixture can drive tests.
- **Acceptance:** unit test feeds `tests/fixtures/graph_small.json` → returns a `RepoStructure` with expected modules/definitions; an injected runner exercises the real `structure()` path.

### T2 — Extractor (`scribe/extractor.py`)
- `def rank_core(struct, n) -> list[Definition]` (top by `fan_in`, deterministic tie-break by `path,name`).
- `def module_tree(struct) -> list[Module]` (sorted, with file counts).
- **Acceptance:** on a fixture with known fan-in, the right N core definitions are selected in a stable order.

### T3 — Synthesizer (`scribe/synthesizer.py`, pure)
- `def synthesize(struct, sections) -> list[Section]`.
- Owns editorial rules: overview (languages, counts, owners), architecture (module tree + core files), layout (where tests/config live). Facts come only from `struct`; no invention.
- **Acceptance:** byte-stable output for a fixed input across repeated calls; section contents match expectations.

### T4 — Renderer / managed-block merger (`scribe/renderer.py`)
- `def render(existing_md, sections) -> str`: replace only content between `<!-- scribe:begin KEY -->` and `<!-- scribe:end KEY -->`; insert missing blocks at the end; leave all human content untouched.
- Idempotent: rendering the same sections twice yields identical output.
- **Acceptance:** human "Conventions" block survives verbatim; managed block updates; second render is byte-identical.

### T5 — Fingerprinter (`scribe/fingerprint.py`, pure)
- `def fingerprint(struct) -> str`: stable hash over sorted module paths + definitions + reference relationships (fan-in). Whitespace/comment-only changes must not alter it.
- **Acceptance:** identical structure ⇒ identical hash; a renamed/added module or new reference ⇒ different hash; cosmetic change ⇒ same hash.

### T6 — Drift gate (`scribe/drift.py`, pure)
- `def classify(old_fp, new_fp, section_fps_old, section_fps_new, threshold) -> none|minor|material`.
- **Acceptance:** boundary tests at the threshold; `none` when fingerprints match.

### T7 — GitLab Adapter (`scribe/adapters/gitlab.py`)
- `def open_mr(repo, branch, files, title, body, labels) -> str` via `glab` (branch, commit, `glab mr create`). Never merges.
- Build the MR body from the drift summary ("3 new modules, `AuthService` fan-in +12").
- **Acceptance:** dry-run returns the would-be plan without calling `glab`; a mocked-runner test asserts the correct invocation.

### T8 — CLI orchestration (`scribe/cli.py`)
- `scribe run --repo PATH [--dry-run]`: structure → synthesize → render → fingerprint → (first run or drift) open MR / (dry-run) print diff.
- `scribe check --repo PATH`: exit 0 if current, 1 if drift.
- Load `.scribe.yml`; write `.scribe/scribe-manifest.json` on a real run.
- **Acceptance:** end-to-end with `--dry-run` prints a diff and exits 0; suite has 30+ tests, all green.

### T9 — AI Catalog flow (`flow/scribe.yml`)
- Model on the foundational Developer Flow Orbit config: a triggered flow that runs the engine and opens the MR.
- Publish to the AI Catalog as **Public**; descriptive name + clear description with an example.
- **Acceptance:** the flow appears in the AI Catalog and triggers a run that opens an MR.

### T10 — Product polish
- `README.md` with a GIF of the MR, quickstart, and the before/after framing.
- Confirm MIT license is detectable at the repo top.
- Run Scribe against the GitLab Orbit repo → submit the generated `AGENTS.md`/docs as `orbit::hackathon` Contribute MRs.
- **Acceptance:** README renders; `scribe run --dry-run` produces a clean `AGENTS.md` on a real repo; at least one Contribute MR opened.

---

## Definition of done

- `pytest -q` green with 30+ tests; pure core has no I/O.
- `scribe run --repo <real repo> --dry-run` produces a faithful `AGENTS.md` diff; a real run opens an MR touching only `AGENTS.md` (+ manifest) and never merges.
- Drift loop: re-running after a structural change opens a corrective MR; re-running with no change is a silent no-op.
- Flow published to the AI Catalog; repo is MIT.

## Status

T0–T8 implemented and green (**54 tests**). T9 flow config committed at `flow/scribe.yml` (publish step pending a Duo-enabled group). T10 README/LICENSE/INSTALL committed; Contribute MRs pending live Orbit indexing.

## Demo cut (the 3-minute video)

1. `scribe run --dry-run` → the proposed `AGENTS.md`.
2. An agent answering a repo question poorly **without** it, well **with** it.
3. Refactor → `scribe run` opens the self-healing corrective MR.
4. Same flow opening a Contribute MR on the Orbit repo. Show the passing test count on screen.
