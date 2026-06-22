<div align="center">

<img src="docs/assets/scribe-logo.png" alt="Scribe" width="420">

**Keeps your repo's `AGENTS.md` file accurate - automatically.**

When your code changes, Scribe notices the docs are now wrong and opens a merge request to fix them.

[What it does](#what-it-does) · [Why it matters](#why-it-matters) · [How it works](#how-it-works) · [Quickstart](#quickstart) · [Commands](#commands) · [Status](#project-status)

MIT licensed · Python 3.11+ · Built for the GitLab Transcend Hackathon

</div>

---

## The 30-second version

AI coding assistants (GitLab Duo, Claude, Cursor, Copilot) read a file called **`AGENTS.md`** to understand your project before they touch it. A good one makes them much smarter. The problem: it's written by hand, and the moment you refactor, it's out of date - and now it's actively *lying* to every AI that reads it.

**Scribe fixes that.** It looks at the real structure of your code, writes an accurate `AGENTS.md`, and opens a merge request. Then it keeps watching - when your code drifts away from the docs, it opens another MR to correct them. You just review and click merge.

---

## What it does

| | |
|---|---|
| **Reads your codebase** | Pulls the real structure - modules, files, functions, and what calls what - from the GitLab Orbit code graph. |
| **Writes the docs** | Generates a clean `AGENTS.md`: project overview, architecture map, the most important files, and where tests and config live. |
| **Never touches your words** | It only edits the sections it owns. Anything you wrote by hand is left exactly as it is. |
| **Notices when docs go stale** | It remembers what the code looked like. Next run, if the structure moved, it flags the drift. |
| **Opens a merge request** | You always review and merge. Scribe never merges anything itself. |

---

## Why it matters

Generating a docs file once is easy - lots of tools do it. **Keeping it accurate forever is the hard part, and that's the whole point of Scribe.**

| Without Scribe | With Scribe |
|---|---|
| `AGENTS.md` written by hand | Generated from the real code |
| Goes stale the next time you refactor | Stays in sync automatically |
| Quietly misleads every AI that reads it | Corrected by a small, reviewable MR |
| Nobody owns keeping it up to date | Scribe owns it; you just approve |

---

## How it works

```
  your code
      │
      ▼
 ┌──────────┐   reads structure
 │  Orbit   │   (modules, files, functions, references)
 │  graph   │
 └────┬─────┘
      ▼
 ┌──────────────────────────────────────────────┐
 │  Scribe engine                               │
 │                                              │
 │  build AGENTS.md ──► compare to last time    │
 │                          │                   │
 │              same? ──────┴────── changed?    │
 │                │                    │        │
 │              do nothing       open a merge   │
 │                                  request     │
 └──────────────────────────────────────────────┘
```

Want the deeper picture and the reasoning behind each decision? See **[`docs/scribe-system-design.md`](docs/scribe-system-design.md)**.

---

## Quickstart

```bash
git clone https://github.com/<you>/scribe.git
cd scribe
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
scribe --help
```

**Try it right now, with no setup** - Scribe ships with a sample codebase graph so you can see the output before connecting anything:

```bash
SCRIBE_GRAPH=tests/fixtures/graph_small.json scribe run --repo . --dry-run
```

That prints the `AGENTS.md` it *would* write, without changing any files or opening anything.

---

## Commands

| Command | What it does |
|---|---|
| `scribe run --repo .` | Build/update `AGENTS.md` and open a merge request if needed. |
| `scribe run --repo . --dry-run` | Show the proposed changes. Touch nothing, open nothing. |
| `scribe check --repo .` | Is the docs file current? Exit `0` = yes, `1` = it has drifted. Good for CI. |

### Configure it (optional) - `.scribe.yml`

| Setting | Means | Default |
|---|---|---|
| `core_count` | How many "most important" files to highlight | `8` |
| `drift_threshold` | How much change before Scribe opens an MR (`minor` / `material`) | `minor` |
| `sections` | Which sections to generate | overview, architecture, layout |
| `mr.target_branch` | Branch to open the MR against | `main` |

---

## Project status

| Part | State |
|---|---|
| Core engine (read → write → detect drift) | ✅ Done |
| Protects hand-written content | ✅ Done |
| `run` / `check` / `--dry-run` commands | ✅ Done |
| Opens merge requests (never auto-merges) | ✅ Done |
| Test suite | ✅ 54 tests passing |
| Live GitLab Orbit connection | ⏳ Needs Orbit installed on your machine |
| Publish to GitLab AI Catalog | ⏳ Needs a GitLab account with Duo enabled |

---

## How it's built (for the curious)

The decision-making logic is **pure** - it does no network, file, or system calls - so it's fast, predictable, and easy to test. Anything that touches the outside world (the code graph, Git, GitLab) is isolated in small "adapter" files. Same input always produces the exact same output.

```
scribe/
  extractor / synthesizer / renderer / fingerprint / drift   ← pure logic, fully tested
  adapters/orbit.py     ← the only code that talks to the code graph
  adapters/gitlab.py    ← the only code that opens a merge request
  cli.py                ← ties it together (run / check)
docs/                   ← system design + build plan
tests/                  ← 54 tests
```

---

## License

[MIT](LICENSE). Use it, fork it, ship it.
