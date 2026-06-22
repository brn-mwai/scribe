# AGENTS.md — Scribe

> This file is the context layer for AI agents working on this repository.
> It is also a live example of what Scribe produces: the blocks between
> `<!-- scribe:begin ... -->` and `<!-- scribe:end ... -->` are machine-maintained;
> everything outside them is human-owned and never touched by Scribe.

## For AI coding agents — start here

You can set up and build this project autonomously. Before writing any code, engage the `coding-standards` skill and apply *Standards and process* below.

1. Read `docs/scribe-system-design.md` (the authoritative spec) and `docs/IMPLEMENTATION.md` (the ordered build plan).
2. Run the **Autonomous setup** steps in `INSTALL.md`. Stop and report if any verification check fails.
3. Implement `docs/IMPLEMENTATION.md` tasks **in order (T0 → T10)**. After each task, run its acceptance check and the test suite. Do not start the next task until the current one is green.
4. Keep the pure core (extractor, synthesizer, renderer, fingerprinter, drift gate) free of I/O so it stays unit-testable. All Orbit and GitLab access lives behind adapters.
5. Never edit content outside Scribe markers in any `AGENTS.md` (including this one's human blocks). Determinism is a hard requirement: same input ⇒ byte-identical output.

## Standards and process (mandatory)

Built under the team coding standards loaded in Claude Code. Apply them on every task — do not hand-roll a different process.

- **Process:** follow the 7-phase coding system — reason → requirements → design → implement → test → review → deploy → monitor. The Phase 0 reasoning gate precedes any code.
- **Design framework:** `docs/scribe-system-design.md` follows the 7-step framework (clarify → estimate → architect → detail → design → scale → verify). Scribe is a batch CLI/flow, not a high-QPS service, so *estimate* and *scale* are intentionally light — runs per repo, on a schedule, no QPS surface. *Verify* maps every NFR back to a design decision.
- **Quality metrics (hard gates):**

  | Metric | Target |
  |--------|--------|
  | Function length | 5–20 lines (max 40) |
  | Cyclomatic complexity | < 10 |
  | File length | < 300 lines |
  | Nesting depth | ≤ 3 |
  | Coverage (critical paths) | > 80% |
  | Build/test time | < 5 min |

- **Security CI:** attach via the `security-ci` skill, but this repo lives on **GitLab**, so use GitLab-native CI templates, not GitHub Actions. Map the layers: Secret Detection (blocks) · SAST — Semgrep-based, since CodeQL is GitHub-only · Dependency Scanning / SCA (blocks HIGH/CRITICAL). **DAST is N/A** — Scribe has no runtime web surface to spin up.
- **Pre-PR checklist (every MR):** works? · readable? · safe? · tested (happy + edge + failure)? · documents *why*? · backwards compatible?
- **Fundamentals:** KISS · YAGNI · DRY (rule of three) · separation of concerns · fail fast · program to interfaces. These are already the spine of the design (pure core + adapters) — keep it that way.

<!-- scribe:begin overview -->
## Project overview

- **Languages:** bash, javascript, python
- **Modules:** 6
- **Definitions:** 130
<!-- scribe:end overview -->

## Conventions (human-owned)

- Determinism over cleverness. No nondeterministic ordering anywhere in the core.
- The pure core has **no** network, filesystem, or subprocess calls. Side effects live in adapters.
- Tests are written alongside each component, not after. Target 30+ meaningful tests.
- Scribe only ever rewrites its own managed blocks. Human blocks are sacred.
- Docs and commit messages in sentence case. MIT headers on original source files.

<!-- scribe:begin architecture -->
## Architecture map

### Modules

- `(root)` (9 files)
- `.github/` (1 file)
- `docs/` (3 files)
- `flow/` (1 file)
- `scribe/` (13 files)
- `tests/` (12 files)

### Core components

- `Section` (DecoratedClass) in `scribe/models.py` -- fan-in 19
- `RepoStructure` (DecoratedClass) in `scribe/models.py` -- fan-in 16
- `fingerprint` (Function) in `scribe/fingerprint.py` -- fan-in 14
- `render` (Function) in `scribe/renderer.py` -- fan-in 10
- `synthesize` (Function) in `scribe/synthesizer.py` -- fan-in 8
- `classify` (Function) in `scribe/drift.py` -- fan-in 7
- `rank_core` (Function) in `scribe/extractor.py` -- fan-in 7
- `OrbitAdapter` (Class) in `scribe/adapters/orbit.py` -- fan-in 5
<!-- scribe:end architecture -->

<!-- scribe:begin layout -->
## Where things live

- **Tests:**
  - `tests/__init__.py`
  - `tests/conftest.py`
  - `tests/fixtures/graph_small.json`
  - `tests/test_cli.py`
  - `tests/test_config_manifest.py`
  - `tests/test_drift.py`
  - `tests/test_extractor.py`
  - `tests/test_fingerprint.py`
  - `tests/test_gitlab.py`
  - `tests/test_orbit.py`
  - `tests/test_renderer.py`
  - `tests/test_synthesizer.py`
- **Config:**
  - `.scribe.yml`
  - `pyproject.toml`
<!-- scribe:end layout -->

## Build, test, run

```shell
# setup
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"

# test (must stay green)
pytest -q

# run against a repo (no MR — prints the proposed diff)
scribe run --repo /path/to/repo --dry-run

# real run (opens an MR)
scribe run --repo /path/to/repo

# drift check only (exit 0 = no drift, exit 1 = drift)
scribe check --repo /path/to/repo
```

## Key references

- `docs/scribe-system-design.md` — full spec (requirements, non-goals, components, testing).
- `docs/IMPLEMENTATION.md` — ordered, testable build tasks (T0–T10).
- `INSTALL.md` — prerequisites and autonomous setup.
- Orbit schema + cookbook: https://docs.gitlab.com/orbit/remote/schema/ , https://docs.gitlab.com/orbit/remote/cookbook/
