# Scribe - System Design

This explains **what Scribe is, how it's built, and why we made the choices we did.** It's meant to be readable in one sitting.

---

## 1. The problem

AI coding assistants read a file called `AGENTS.md` to learn a project before they edit it. A good one makes them noticeably better. But:

1. **It's written by hand** - tedious and easy to skip.
2. **It rots silently** - the first refactor makes it wrong, and from then on it *misleads* every AI that reads it. Nobody notices until an assistant confidently makes a wrong change.

We call this **context rot**. Scribe's job is to kill it.

---

## 2. What we're building

A small tool that:

- reads the **real** structure of a codebase from the GitLab Orbit code graph,
- writes an accurate `AGENTS.md`,
- opens a merge request with it,
- and re-checks on a schedule, opening a corrective MR whenever the code and the docs drift apart.

**The insight that shaped everything:** generating a docs file once is easy and unremarkable. The valuable, defensible part is **keeping it correct over time**. So the maintenance loop - not the generator - is the product.

---

## 3. Requirements

**Functional - what it must do**

| # | Requirement |
|---|---|
| F1 | Read code structure: modules, files, definitions, and cross-file references. |
| F2 | Identify the most important ("load-bearing") files by how often they're referenced. |
| F3 | Write a structured `AGENTS.md`: overview, architecture map, key files, where tests/config live. |
| F4 | Never overwrite human-written content - only its own marked sections. |
| F5 | Detect when the docs have drifted from the code. |
| F6 | Open a merge request for review. Never auto-merge. |

**Non-functional - how it must behave**

| # | Requirement | Why it matters |
|---|---|---|
| N1 | **Deterministic** - same input gives byte-for-byte the same output. | No noisy "nothing really changed" MRs. |
| N2 | **Testable** - the core logic is pure (no network/files). | We can trust it and prove it works. |
| N3 | **Safe** - code data is treated as text, never instructions; nothing auto-merges. | A docs tool must never become a security hole. |
| N4 | **Cheap** - prefer free, local data sources. | Runs often without burning credits. |

---

## 4. Key decisions (and why)

| Decision | Why we did it |
|---|---|
| **Maintenance loop is the product, not generation** | Anyone can generate a file once. Keeping it honest forever is the hard, valuable part - so we lead with it. |
| **Local-first data source** | Scribe only needs *code structure*, which Orbit Local gives for free with zero setup. This keeps the demo working on any repo in minutes, with no account or billing in the critical path. |
| **Pure core, side effects at the edges** | All decision logic (rank, write, fingerprint, drift) is pure functions. Orbit, Git, and the clock are isolated in "adapters". This is what makes it deterministic and easy to test. |
| **Only edit our own marked blocks** | Scribe writes between `<!-- scribe:begin -->` / `<!-- scribe:end -->` markers and never outside them. Your conventions and notes are untouchable. This is the trust contract. |
| **A "fingerprint" to detect drift** | We hash the *structure* (not the text), so renames and new modules register as change, while reformatting and comments don't. That's how we avoid false alarms. |
| **Always a merge request, never auto-merge** | A human reviews every change. Safety and trust gate. |
| **One adapter for Orbit** | Orbit is in beta and may change. Keeping all of it behind one file means a future change is a one-file fix, not a rewrite. |

---

## 5. How a run flows

```
 Trigger (you, or a schedule)
        |
        v
 Orbit adapter ----> read structure (modules, files, references)
        |
        v
 Extractor ----> rank the most-referenced files
        |
        v
 Synthesizer ----> turn structure into AGENTS.md sections
        |
        v
 Fingerprint + Drift gate ----> did the structure actually change?
        |                                 |
     no change                        changed / first run
        |                                 |
       stop                              v
   (silent no-op)                  Renderer ----> merge new sections into
                                          |        the file, keeping human
                                          |        content intact
                                          v
                                   GitLab adapter ----> open a merge request
```

---

## 6. The pieces

| Component | Job | Pure? |
|---|---|---|
| `adapters/orbit.py` | The only code that talks to the code graph. Returns a clean internal model. | No (I/O) |
| `extractor.py` | Rank files by importance; build the module tree. | Yes |
| `synthesizer.py` | Turn structure into markdown sections. Owns the editorial rules. | Yes |
| `renderer.py` | Merge sections into the file, protecting human content. Idempotent. | Yes |
| `fingerprint.py` | Stable hash of the structure for drift detection. | Yes |
| `drift.py` | Grade the change: none / minor / material. | Yes |
| `adapters/gitlab.py` | The only code that opens a merge request. Never merges. | No (I/O) |
| `cli.py` | Wires it together: `run`, `check`, `--dry-run`. | No (I/O) |

The split is deliberate: **everything that makes a decision is pure and tested; everything that touches the outside world is small and isolated.**

---

## 7. What it deliberately does *not* do

Saying no kept the scope sane and the tool sharp.

| Not doing | Why |
|---|---|
| Code review / bug finding | A crowded space; not our lane. Scribe is about context, not change risk. |
| A chat interface | Assistants already chat. Scribe's output is a merge request, not a conversation. |
| Inventing conventions | Scribe only writes facts it can see in the code. Humans own intent and conventions. |
| Auto-merging | A human reviews everything. Always. |
| Multi-repo orchestration | v1 is one repo. That's enough to prove the idea. |

---

## 8. Does the design meet its requirements?

| Requirement | How the design delivers it |
|---|---|
| Deterministic (N1) | Pure core + sorting everything + structure-only fingerprint. |
| Testable (N2) | No I/O in the core; 54 tests run in well under a second. |
| Safe (N3) | Marked-block-only edits, no auto-merge, code treated as data. |
| Cheap (N4) | Local-first; free data path; no work when nothing changed. |
| Keeps docs honest (the goal) | Fingerprint + drift gate + corrective MR - the maintenance loop. |

---

## 9. A note on scale

Scribe runs **once per repo, on a trigger or schedule** - there's no live traffic, no users hitting an API, nothing to load-balance. So this design intentionally skips the usual "scale to millions of requests" machinery: it would be answering a question nobody asked. The engineering effort went where the real risk is - **correctness, determinism, and never clobbering human work.**
