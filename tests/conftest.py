from __future__ import annotations

import json
import os

import pytest

from scribe.adapters.orbit import normalize
from scribe.models import Definition, Module, RepoStructure

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture
def raw_graph() -> dict:
    with open(os.path.join(FIXTURES, "graph_small.json"), encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def small_struct(raw_graph) -> RepoStructure:
    return normalize(raw_graph)


def make_struct(
    modules=(("a/", 1),),
    definitions=(("A", "class", "a/x.py", 0),),
    test_paths=(),
    config_paths=(),
    languages=("Python",),
    owners=(),
) -> RepoStructure:
    return RepoStructure(
        languages=tuple(languages),
        modules=tuple(Module(path=p, file_count=c) for p, c in modules),
        definitions=tuple(
            Definition(name=n, kind=k, path=p, fan_in=f)
            for n, k, p, f in definitions
        ),
        test_paths=tuple(test_paths),
        config_paths=tuple(config_paths),
        owners=tuple(owners),
    )
