"""Managed-block merge into an existing AGENTS.md (pure).

The safety contract that makes Scribe trustworthy lives here: it only ever
touches text *between* its own `scribe:begin/end` markers. Everything a human
wrote outside those markers is returned verbatim. Re-rendering the same sections
must be idempotent, so the loop never produces a noisy "nothing really changed"
MR.
"""

from __future__ import annotations

import re

from .models import Section

_BEGIN = "<!-- scribe:begin {key} -->"
_END = "<!-- scribe:end {key} -->"


def _block(section: Section) -> str:
    begin = _BEGIN.format(key=section.key)
    end = _END.format(key=section.key)
    return f"{begin}\n{section.markdown}\n{end}"


def render(existing_md: str | None, sections: list[Section]) -> str:
    """Replace each section's managed block in place, append the ones missing.

    `pattern.sub` is fed a function returning the block (not a string template)
    so regex backreference syntax inside generated markdown can never corrupt
    the output.
    """
    md = existing_md or ""
    for section in sections:
        begin = re.escape(_BEGIN.format(key=section.key))
        end = re.escape(_END.format(key=section.key))
        pattern = re.compile(begin + r".*?" + end, re.DOTALL)
        block = _block(section)
        if pattern.search(md):
            md = pattern.sub(lambda _match: block, md, count=1)
        else:
            md = _append_block(md, block)
    return md


def _append_block(md: str, block: str) -> str:
    if md == "":
        return block + "\n"
    if not md.endswith("\n"):
        md += "\n"
    if not md.endswith("\n\n"):
        md += "\n"
    return md + block + "\n"
