from __future__ import annotations

from scribe.extractor import module_tree, rank_core

from .conftest import make_struct


def test_rank_core_by_fan_in(small_struct):
    core = rank_core(small_struct, 2)
    names = [d.name for d in core]
    assert names == ["PaymentService", "AuthService"]


def test_rank_core_limit(small_struct):
    assert len(rank_core(small_struct, 1)) == 1
    assert len(rank_core(small_struct, 99)) == len(small_struct.definitions)


def test_rank_core_tie_break():
    struct = make_struct(
        definitions=(
            ("Zeta", "function", "z/mod.py", 5),
            ("Alpha", "function", "a/mod.py", 5),
            ("Beta", "function", "a/mod.py", 5),
        )
    )
    core = rank_core(struct, 3)
    assert [d.name for d in core] == ["Alpha", "Beta", "Zeta"]


def test_module_tree_sorted():
    struct = make_struct(modules=(("z/", 1), ("a/", 2), ("m/", 3)))
    paths = [m.path for m in module_tree(struct)]
    assert paths == ["a/", "m/", "z/"]


def test_rank_core_zero():
    struct = make_struct()
    assert rank_core(struct, 0) == []
