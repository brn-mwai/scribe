from __future__ import annotations

from scribe.synthesizer import synthesize


def test_synthesize_returns_requested_sections(small_struct):
    sections = synthesize(small_struct, ["overview", "architecture", "layout"])
    assert [s.key for s in sections] == ["overview", "architecture", "layout"]


def test_synthesize_is_deterministic(small_struct):
    a = synthesize(small_struct, ["overview", "architecture", "layout"])
    b = synthesize(small_struct, ["overview", "architecture", "layout"])
    assert [s.markdown for s in a] == [s.markdown for s in b]


def test_overview_lists_languages_and_owners(small_struct):
    overview = synthesize(small_struct, ["overview"])[0].markdown
    assert "Python" in overview
    assert "alice, bob" in overview


def test_architecture_lists_core_components(small_struct):
    arch = synthesize(small_struct, ["architecture"], core_count=2)[0].markdown
    assert "PaymentService" in arch
    assert "payments/" in arch
    assert "fan-in 3" in arch


def test_layout_lists_tests_and_config(small_struct):
    layout = synthesize(small_struct, ["layout"])[0].markdown
    assert "tests/test_payments.py" in layout
    assert "pyproject.toml" in layout


def test_unknown_section_skipped(small_struct):
    sections = synthesize(small_struct, ["overview", "bogus"])
    assert [s.key for s in sections] == ["overview"]
