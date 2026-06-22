from __future__ import annotations

from scribe.drift import classify, opens_mr, summarize

from .conftest import make_struct


def test_none_when_fingerprints_match():
    assert classify("abc", "abc", {}, {}, 0.5) == "none"


def test_minor_when_few_sections_change():
    old = {"overview": "1", "architecture": "1", "layout": "1"}
    new = {"overview": "2", "architecture": "1", "layout": "1"}
    assert classify("a", "b", old, new, 0.5) == "minor"


def test_material_when_many_sections_change():
    old = {"overview": "1", "architecture": "1", "layout": "1"}
    new = {"overview": "2", "architecture": "2", "layout": "1"}
    assert classify("a", "b", old, new, 0.5) == "material"


def test_threshold_boundary_is_material():
    old = {"a": "1", "b": "1"}
    new = {"a": "2", "b": "1"}
    assert classify("x", "y", old, new, 0.5) == "material"


def test_threshold_just_below_is_minor():
    old = {"a": "1", "b": "1", "c": "1"}
    new = {"a": "2", "b": "1", "c": "1"}
    assert classify("x", "y", old, new, 0.5) == "minor"


def test_opens_mr_respects_config_floor():
    assert opens_mr("minor", "minor") is True
    assert opens_mr("minor", "material") is False
    assert opens_mr("material", "material") is True
    assert opens_mr("none", "minor") is False


def test_summarize_initial():
    new = make_struct(modules=(("a/", 1), ("b/", 1)))
    assert "Initial AGENTS.md" in summarize(None, new)


def test_summarize_added_module():
    old = make_struct(modules=(("a/", 1),))
    new = make_struct(modules=(("a/", 1), ("b/", 1)))
    text = summarize(old, new)
    assert "1 new module(s)" in text
    assert "`b/`" in text


def test_summarize_fan_in_delta():
    old = make_struct(definitions=(("A", "class", "a/x.py", 2),))
    new = make_struct(definitions=(("A", "class", "a/x.py", 5),))
    assert "`A` fan-in +3" in summarize(old, new)
