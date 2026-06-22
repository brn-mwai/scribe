from __future__ import annotations

from scribe.fingerprint import fingerprint, section_fingerprints
from scribe.models import Section

from .conftest import make_struct


def test_identical_structure_same_hash():
    a = make_struct()
    b = make_struct()
    assert fingerprint(a) == fingerprint(b)


def test_new_module_changes_hash():
    base = make_struct(modules=(("a/", 1),))
    changed = make_struct(modules=(("a/", 1), ("b/", 1)))
    assert fingerprint(base) != fingerprint(changed)


def test_rename_changes_hash():
    base = make_struct(definitions=(("A", "class", "a/x.py", 0),))
    renamed = make_struct(definitions=(("B", "class", "a/x.py", 0),))
    assert fingerprint(base) != fingerprint(renamed)


def test_new_reference_changes_hash():
    base = make_struct(definitions=(("A", "class", "a/x.py", 1),))
    more_refs = make_struct(definitions=(("A", "class", "a/x.py", 4),))
    assert fingerprint(base) != fingerprint(more_refs)


def test_module_order_invariant():
    a = make_struct(modules=(("a/", 1), ("b/", 1)))
    b = make_struct(modules=(("b/", 1), ("a/", 1)))
    assert fingerprint(a) == fingerprint(b)


def test_summary_change_does_not_affect_hash():
    a = make_struct(modules=(("a/", 1),))
    from scribe.models import Module, RepoStructure

    b = RepoStructure(
        languages=a.languages,
        modules=(Module(path="a/", file_count=1, summary="cosmetic"),),
        definitions=a.definitions,
        test_paths=a.test_paths,
        config_paths=a.config_paths,
        owners=a.owners,
    )
    assert fingerprint(a) == fingerprint(b)


def test_section_fingerprints_keyed_by_section():
    fps = section_fingerprints([Section("overview", "x"), Section("layout", "y")])
    assert set(fps) == {"overview", "layout"}
    assert fps["overview"] != fps["layout"]
