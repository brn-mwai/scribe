from __future__ import annotations

from scribe.adapters.orbit import OrbitAdapter, normalize


def test_normalize_modules(small_struct):
    paths = [m.path for m in small_struct.modules]
    assert paths == ["(root)", "api/", "payments/", "tests/"]
    counts = {m.path: m.file_count for m in small_struct.modules}
    assert counts["payments/"] == 2
    assert counts["api/"] == 2
    assert counts["(root)"] == 2


def test_normalize_fan_in(small_struct):
    fan = {d.name: d.fan_in for d in small_struct.definitions}
    assert fan["PaymentService"] == 3
    assert fan["AuthService"] == 2
    assert fan["charge"] == 0


def test_normalize_definitions_sorted(small_struct):
    keys = [(d.path, d.name) for d in small_struct.definitions]
    assert keys == sorted(keys)


def test_normalize_languages(small_struct):
    assert small_struct.languages == ("Markdown", "Python")


def test_normalize_test_and_config_paths(small_struct):
    assert small_struct.test_paths == ("tests/test_payments.py",)
    assert small_struct.config_paths == ("pyproject.toml",)


def test_normalize_owners(small_struct):
    assert small_struct.owners == ("alice", "bob")


def test_adapter_with_injected_runner(raw_graph):
    import json

    adapter = OrbitAdapter(runner=lambda repo, source: json.dumps(raw_graph))
    struct = adapter.structure("/whatever")
    assert any(d.name == "PaymentService" for d in struct.definitions)


def test_adapter_accepts_dict_runner(raw_graph):
    adapter = OrbitAdapter(runner=lambda repo, source: raw_graph)
    struct = adapter.structure("/whatever")
    assert len(struct.modules) == 4


def test_normalize_empty():
    struct = normalize({})
    assert struct.modules == ()
    assert struct.definitions == ()
    assert struct.languages == ()
