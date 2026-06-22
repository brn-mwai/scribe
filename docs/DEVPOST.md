# Scribe - Devpost submission

Fill the `<...>` placeholders before submitting. Submit to **both tracks** (Showcase + Contribute) with buffer before the deadline.

**Links to attach:** repo `<repo-url>` · AI Catalog flow `<catalog-url>` · video `<video-url>`

---

## Tagline

Scribe keeps your repo's `AGENTS.md` true as the code changes - automatically, from the real code graph, and without ever touching the parts you wrote.

---

## Inspiration

Every AI coding agent - Duo, Claude, Cursor, Copilot - reads a file called `AGENTS.md` to understand a project before it touches the code. A good one makes the agent noticeably better.

The first time I refactored a repo that had one, I watched it happen: I moved a module, and the file didn't move with it. From that moment, the context file was quietly *lying* to every agent that read it - and a wrong context file is worse than none, because it misleads with confidence. Nobody re-writes it by hand. I called this **context rot**, and I wanted it gone.

## What it does

Scribe reads the real structure of a codebase from the GitLab Orbit knowledge graph - modules, files, definitions, and what references what - and writes a structured `AGENTS.md`: an overview, an architecture map, the load-bearing "core" files ranked by inbound references, and where tests and config live. It opens a merge request with it. Then it keeps watching: when the structure drifts away from the committed file, it opens a **corrective** merge request. You review and merge. Scribe never merges anything itself, and it never touches a word you wrote by hand.

## Why this isn't "just ask an LLM to write it"

You can ask an LLM to generate an `AGENTS.md` once - and that's a commoditized generator. The hard problem was never *writing* the file; it's **keeping it true without a human babysitting it.**

- An LLM **guesses** structure from the files it can fit in a context window; Scribe **derives** it from the real graph - actual reference counts, real fan-in. On a big repo the model approximates and sometimes confabulates; the graph knows.
- "Which files are load-bearing" is a graph query, not a vibe - and it's the most valuable part of the file, and the part the model is weakest at.
- The one-shot file goes stale the next refactor and nobody re-runs the prompt. Scribe's **drift detection and corrective MR are the product**; generation is just the on-ramp.
- Re-prompting overwrites your hand-written conventions. Scribe only ever rewrites its own marked blocks.

> An LLM can write `AGENTS.md` once, from a guess. Scribe keeps it true, from the graph - automatically, deterministically, and without ever touching the parts you wrote.

## How I built it

A small Python tool with a deliberate shape: a **pure core** (rank, synthesize, render, fingerprint, drift) that does no network or file I/O, and thin **adapters** that isolate everything that touches the outside world - the Orbit graph and GitLab. That split is what makes it deterministic (same input, byte-identical output) and testable - **54 tests**, running in under a second.

Drift detection works by fingerprinting the *structure*, not the text - so renames and new modules register as change, while reformatting and comments don't. The renderer only edits content between its own `<!-- scribe:begin --> / <!-- scribe:end -->` markers, which is what makes it safe to run automatically forever. It's shipped as a CLI (`run` / `check` / `--dry-run`) and as a flow published to the GitLab AI Catalog.

## Challenges

Keeping the core honest: it was tempting to let an LLM "polish" the structure, but the moment facts come from a model instead of the graph, you reintroduce the exact problem you're solving. So structure and facts come only from the graph; the model never invents conventions.

## Accomplishments I'm proud of

A genuinely deterministic, fully-tested core, and a tool that's safe to leave running because it physically can't clobber human-authored content.

## What I learned

The reframe: the valuable problem in AI-native codebases isn't generating context, it's *maintaining* it against constant drift - grounded in real structure, not a guess.

## What's next

Ownership/contributor enrichment from Orbit Remote, optional LLM prose-polish inside managed blocks only, and multi-repo orchestration.

---

## Contribute Track

Ran Scribe against the GitLab Orbit repos; the generated `AGENTS.md`/docs improvements were opened as merge requests labeled `orbit::hackathon`. MR links: `<...>`
