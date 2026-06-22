# Installing Scribe

Two audiences are covered: **end users** who want to run Scribe on a repo, and **AI coding agents** setting up the development environment autonomously. Agents: follow the *Autonomous setup* section, run every verification check, and stop on the first failure.

---

## Prerequisites

| Tool | Version | Why | Check |
|------|---------|-----|-------|
| Python | 3.11+ | Engine runtime | `python --version` |
| git | any recent | Repo operations | `git --version` |
| glab (GitLab CLI) | 1.94+ | Orbit queries + opening MRs | `glab --version` |
| Orbit Local | latest | Code structure graph (primary data source) | `orbit --version` |
| Orbit Remote | optional | Ownership/contributor enrichment | enabled per top-level group |

Authentication: `glab auth login` (OAuth, or a PAT with `read_api` and permission to open MRs).

---

## Quick install (end user)

```shell
# option A: from source
git clone <scribe-repo-url> && cd scribe
pipx install .            # or: pip install .

# option B: installer script (once published)
curl -fsSL <scribe-install-url>/install.sh | bash

# verify
scribe --help
```

Then, in any repo:

```shell
scribe run --repo . --dry-run   # preview the proposed AGENTS.md
scribe run --repo .             # open the merge request
```

---

## Autonomous setup (for AI coding agents)

Run these in order. Each step has a verification check; **stop and report** if a check fails rather than guessing.

### 1. Verify / install tooling
```shell
python --version            # expect 3.11+
git --version
glab --version              # expect 1.94+
orbit --version || curl -fsSL "https://gitlab.com/gitlab-org/orbit/knowledge-graph/-/raw/main/install.sh" | bash
```
Verification: all four commands print a version. Ensure `$HOME/.local/bin` is on `$PATH`.

### 2. Authenticate GitLab
```shell
glab auth status || glab auth login
glab skills install --global orbit
```
Verification: `glab auth status` reports a logged-in user.

### 3. Provide a graph to query (Orbit Local)
```shell
orbit index .
orbit sql 'SELECT count(*) AS n FROM gl_definition'
glab orbit local schema
```
Verification: the count query returns a number > 0, and `schema` lists entity types. If 0, the repo isn't indexed or isn't a supported language — report this.

### 4. Set up the Python environment
```shell
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"     # after pyproject.toml exists (T0)
pytest -q
```
Verification: `pytest` runs and stays green (54 tests today).

### 5. Smoke test the engine (offline, no Orbit required)
```shell
SCRIBE_GRAPH=tests/fixtures/graph_small.json scribe run --repo . --dry-run
```
Verification: prints a proposed `AGENTS.md` diff without opening an MR and exits 0. Drop `SCRIBE_GRAPH` once Orbit Local is indexing the repo.

### 6. End-to-end (optional, opens a real MR)
```shell
scribe run --repo .
```
Verification: a merge request URL is printed; the branch contains only `AGENTS.md` (+ `.scribe/scribe-manifest.json`).

---

## Configuration — `.scribe.yml`

Place at the target repo root. All keys optional; sensible defaults apply.

```yaml
source: local            # local | remote
core_count: 8            # how many "core" files to surface
drift_threshold: minor   # minimum drift class that opens an MR: minor | material
sections:                # which managed blocks to generate
  - overview
  - architecture
  - layout
paths:
  include: ["**/*"]
  exclude: ["vendor/**", "node_modules/**", "**/*.min.*"]
mr:
  target_branch: main
  labels: ["scribe", "documentation"]
```

---

## Health check

```shell
scribe check --repo .    # exit 0 = AGENTS.md is current, exit 1 = drift detected
```

---

## Troubleshooting

- **`orbit`/`scribe` not found** → add `$HOME/.local/bin` to `$PATH`, reopen the shell.
- **`glab auth status` fails** → re-run `glab auth login`; confirm the token has `read_api` and MR-create scope.
- **`gl_definition` count is 0** → run `orbit index .` from the repo root; confirm the language is supported.
- **MCP `query_graph` consuming credits unexpectedly** → prefer Orbit Local (`source: local`) and `get_graph_schema` (free) for development.
- **MR not opening** → check the token can push and open MRs on the target project; try `--dry-run` first to isolate generation from the action.
