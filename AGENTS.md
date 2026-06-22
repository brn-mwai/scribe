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

Scribe keeps a repository's `AGENTS.md` accurate as the code changes. It queries the
GitLab Orbit knowledge graph for the real structure of a codebase, synthesizes a
structured `AGENTS.md`, opens a merge request with it, and then detects drift on a
schedule and opens corrective MRs. Generation is the on-ramp; the self-healing
maintenance loop is the product.

- **Language:** Python 3.11+
- **CLI:** `scribe` (commands: `run`, `check`) — Typer
- **Graph access:** GitLab Orbit Local (primary), Orbit Remote (optional enrichment), behind one adapter
- **Action:** opens a GitLab merge request via `glab`; never auto-merges
- **Catalog artifact:** a Duo flow (`flow/scribe.yml`) published to the AI Catalog
- **License:** MIT
<!-- scribe:end overview -->

## Conventions (human-owned)

- Determinism over cleverness. No nondeterministic ordering anywhere in the core.
- The pure core has **no** network, filesystem, or subprocess calls. Side effects live in adapters.
- Tests are written alongside each component, not after. Target 30+ meaningful tests.
- Scribe only ever rewrites its own managed blocks. Human blocks are sacred.
- Docs and commit messages in sentence case. MIT headers on original source files.

<!-- scribe:begin architecture -->
## Architecture map

Data flow: **Trigger → Orbit Adapter → Extractor → Synthesizer → Renderer → MR Action**,
with **Fingerprinter → Drift gate** deciding whether a run produces an MR at all.

- `scribe/adapters/orbit.py` — only code that talks to Orbit (`get_graph_schema`, then `query_graph` / `glab orbit local query`). Returns a normalized `RepoStructure`.
- `scribe/extractor.py` — `RepoStructure` → ranked modules, core files (fan-in), test/config locations.
- `scribe/synthesizer.py` — pure: structure → `Sections`. Owns editorial rules. No I/O.
- `scribe/renderer.py` — merges generated sections into existing `AGENTS.md`, preserving human blocks. Idempotent.
- `scribe/fingerprint.py` — stable structural hash; formatting-insensitive, structure-sensitive.
- `scribe/drift.py` — classifies `none | minor | material` against the configured threshold.
- `scribe/adapters/gitlab.py` — branch, commit, open MR via `glab`. No merge rights.
- `scribe/cli.py` — orchestration (`run`, `check`, `--dry-run`).
- `flow/scribe.yml` — Duo flow config for the AI Catalog.
<!-- scribe:end architecture -->

<!-- scribe:begin layout -->
## Where things live

```
scribe/            engine package (pure core + adapters + cli)
  adapters/        orbit.py, gitlab.py  (all side effects)
  *.py             extractor, synthesizer, renderer, fingerprint, drift, cli
flow/scribe.yml    AI Catalog flow config
tests/             pytest suite
  fixtures/        recorded graph responses + sample repos
docs/              scribe-system-design.md, IMPLEMENTATION.md
.scribe.yml        runtime config (sections, drift threshold, mr settings)
install.sh         end-user installer
pyproject.toml     packaging + console_scripts: scribe
```
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
