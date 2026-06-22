from __future__ import annotations

from scribe.models import Section
from scribe.renderer import render

HUMAN_DOC = """# AGENTS.md

<!-- scribe:begin overview -->
old overview
<!-- scribe:end overview -->

## Conventions (human-owned)

- Business logic never lives in controllers.
- Module `legacy/` is frozen.
"""


def test_managed_block_updates():
    out = render(HUMAN_DOC, [Section("overview", "new overview")])
    assert "new overview" in out
    assert "old overview" not in out


def test_human_block_survives():
    out = render(HUMAN_DOC, [Section("overview", "new overview")])
    assert "Business logic never lives in controllers." in out
    assert "Module `legacy/` is frozen." in out


def test_missing_block_appended():
    out = render(HUMAN_DOC, [Section("layout", "where things live")])
    assert "<!-- scribe:begin layout -->" in out
    assert "<!-- scribe:end layout -->" in out
    assert "where things live" in out


def test_idempotent_rerender():
    once = render(HUMAN_DOC, [Section("overview", "fresh")])
    twice = render(once, [Section("overview", "fresh")])
    assert once == twice


def test_render_into_empty_doc():
    out = render("", [Section("overview", "body")])
    assert out == "<!-- scribe:begin overview -->\nbody\n<!-- scribe:end overview -->\n"


def test_multiple_sections_render():
    out = render(
        "",
        [Section("overview", "o"), Section("architecture", "a")],
    )
    assert "<!-- scribe:begin overview -->" in out
    assert "<!-- scribe:begin architecture -->" in out


def test_block_content_only_replaced_once():
    doc = render("", [Section("overview", "v1")])
    doc2 = render(doc, [Section("overview", "v2")])
    assert doc2.count("<!-- scribe:begin overview -->") == 1
    assert "v2" in doc2 and "v1" not in doc2
