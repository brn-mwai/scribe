# Scribe - 3-minute demo script

The video is where the prize is won. This is a shot-by-shot script so the three minutes don't fumble. Total target: **2:45-3:00**.

## Before you hit record (hard prerequisites)

A **real merge request must already exist** before you film - the before/after on a real repo is the whole demo. So do these first:

1. `orbit index .` on a repo you actually know.
2. `scribe run --dry-run` and **read the output critically** - are the names right, are the "core" files genuinely the load-bearing ones?
3. `scribe run` for real, on a glab-authenticated group, so a genuine MR exists to show.

**Pick a repo big enough that the graph visibly knows things a model would miss.** The argument becomes undeniable on a large codebase; it narrows on a toy repo that fits in a context window. Don't demo on something tiny.

Public on YouTube/Vimeo. No copyrighted music.

---

## The script

### 0:00-0:15 - The pain (lead with it)
> "Every AI coding agent reads a file called `AGENTS.md` to understand your project. Here's the problem."

Show a real `AGENTS.md`. Then show a recent refactor in the same repo (a renamed module, a moved file).

> "The code moved. The file didn't. It's now lying to every AI that reads it - and nobody noticed. This is context rot."

### 0:15-0:45 - Prove the cost (the without/with)
Open an AI assistant **without** a good `AGENTS.md`. Ask a real architecture question ("where does auth live?", "what's the entry point?"). Let it answer vaguely or wrong.

> "Without accurate context, it guesses."

Now show the same question answered well **with** Scribe's `AGENTS.md` in place.

> "With it, it's right the first time. So the file matters - which is exactly why it rotting is dangerous."

### 0:45-1:00 - Defuse the obvious objection (say this, it's the whole moat)
> "You're thinking: just ask an LLM to write the file. You can - once, from a guess. But it goes stale the next refactor, and nobody re-runs the prompt. Scribe keeps it true, from the real code graph, automatically - and never touches the parts you wrote."

### 1:00-1:45 - The generate path
Terminal, clean:

```bash
scribe run --repo . --dry-run
```

Point at the screen:
> "Scribe reads the real structure from GitLab Orbit's code graph - not a guess. The architecture map, and these core files, are ranked by actual inbound references. That ranking is a graph query the model can't do - it has no global view of the codebase."

```bash
scribe run --repo .
```

> "And the action isn't a chat reply - it's a merge request. A human reviews it. Scribe never merges."

Show the real MR in the browser. Scroll the diff.

### 1:45-2:30 - The self-healing loop (the product)
> "Generation was the easy part. This is the part nobody else does."

Make a structural change live - rename a module or move a file. Then:

```bash
scribe run --repo .
```

Show the **second, corrective** MR open by itself. Open its body - point at the plain-language summary ("2 new modules, AuthService fan-in +9").

> "The code drifted, Scribe noticed, and it opened a corrective MR on its own. That's the whole point - it keeps the context honest without anyone babysitting it."

Then show a no-op:
```bash
scribe check --repo .
```
> "And when nothing changed, it does nothing. No noise."

### 2:30-2:45 - Credibility + close
Put the test count on screen:
```bash
pytest -q     # 54 passed
```

> "The core logic is pure and deterministic - 54 tests, same input, same output, every time."

Close on the reframe:
> "Writing the context file was always the easy part. Keeping it true, from the graph, without a human in the loop - that's Scribe."

---

## On-screen checklist
- [ ] A real MR is visible (not a dry-run).
- [ ] The corrective/self-healing MR opens on camera.
- [ ] `54 passed` is shown.
- [ ] Demo repo is large enough to make the graph's advantage obvious.
- [ ] The one-liner is spoken almost verbatim.
