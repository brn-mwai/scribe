"""The only code that talks to GitLab Orbit.

Orbit is beta, so its DSL and entity names may shift. We contain that risk two
ways: every query lives behind this one adapter, and `normalize()` (pure) is
split from the subprocess `runner` so tests drive a recorded fixture instead of
a live `orbit` binary. Swap Orbit Local for Remote, or a schema change, and only
this file moves.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections.abc import Callable

from ..models import Definition, Module, RepoStructure

TEST_MARKERS = ("test_", "_test", "tests/", "/test/", "spec_", "_spec", ".spec.")
CONFIG_NAMES = frozenset(
    {
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "package.json",
        "tsconfig.json",
        "requirements.txt",
        ".scribe.yml",
        "dockerfile",
        "makefile",
        "go.mod",
        "cargo.toml",
        "pom.xml",
        "build.gradle",
    }
)


def _top_module(path: str) -> str:
    parts = path.split("/")
    if len(parts) == 1:
        return "(root)"
    return parts[0] + "/"


def _is_test(path: str) -> bool:
    low = path.lower()
    return any(marker in low for marker in TEST_MARKERS)


def _is_config(path: str) -> bool:
    return path.split("/")[-1].lower() in CONFIG_NAMES


def normalize(raw: dict) -> RepoStructure:
    """Turn raw Orbit rows into a sorted, immutable RepoStructure.

    Fan-in is computed here by counting inbound references per definition name,
    because the downstream "core" ranking depends on it and we want a single
    place that defines what fan-in means.
    """
    files = raw.get("files", [])
    raw_defs = raw.get("definitions", [])
    refs = raw.get("references", [])

    fan_in: dict[str, int] = {}
    for ref in refs:
        target = ref.get("to_def")
        if target is not None:
            fan_in[target] = fan_in.get(target, 0) + 1

    definitions = []
    for d in raw_defs:
        explicit = d.get("fan_in")
        count = explicit if explicit is not None else fan_in.get(d["name"], 0)
        definitions.append(
            Definition(
                name=d["name"],
                kind=d.get("kind", "definition"),
                path=d["path"],
                fan_in=int(count),
            )
        )
    definitions.sort(key=lambda d: (d.path, d.name, d.kind))

    file_counts: dict[str, int] = {}
    languages: set[str] = set()
    for f in files:
        module = _top_module(f["path"])
        file_counts[module] = file_counts.get(module, 0) + 1
        language = f.get("language")
        if language and language.lower() != "unknown":
            languages.add(language)

    modules = [Module(path=p, file_count=c) for p, c in file_counts.items()]
    modules.sort(key=lambda m: m.path)

    test_paths = tuple(sorted({f["path"] for f in files if _is_test(f["path"])}))
    config_paths = tuple(sorted({f["path"] for f in files if _is_config(f["path"])}))
    owners = tuple(sorted(raw.get("owners", [])))

    return RepoStructure(
        languages=tuple(sorted(languages)),
        modules=tuple(modules),
        definitions=tuple(definitions),
        test_paths=test_paths,
        config_paths=config_paths,
        owners=owners,
    )


class OrbitAdapter:
    def __init__(
        self,
        source: str = "local",
        runner: Callable[[str, str], object] | None = None,
    ) -> None:
        self.source = source
        self._runner = runner or self._default_runner

    def structure(self, repo: str) -> RepoStructure:
        """Fetch and normalize the structure of `repo`.

        The injected `runner` may hand back a dict (tests) or a JSON string
        (the real CLI, reading whatever `orbit`/`glab` printed); both are
        accepted so the calling code never cares which path produced the data.
        """
        raw = self._runner(repo, self.source)
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode()
        if isinstance(raw, str):
            raw = json.loads(raw)
        return normalize(raw)

    @staticmethod
    def _orbit_bin() -> str:
        override = os.environ.get("SCRIBE_ORBIT_BIN")
        if override:
            return override
        found = shutil.which("orbit")
        if found:
            return found
        home = os.path.expanduser("~")
        candidates = []
        local = os.environ.get("LOCALAPPDATA")
        if local:
            candidates.append(os.path.join(local, "glab-cli", "bin", "orbit.exe"))
        candidates += [
            os.path.join(home, ".local", "share", "glab-cli", "bin", "orbit"),
            os.path.join(home, ".config", "glab-cli", "bin", "orbit"),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        raise RuntimeError(
            "orbit binary not found. Install Orbit Local, set SCRIBE_ORBIT_BIN, "
            "or set SCRIBE_GRAPH to a recorded graph."
        )

    @staticmethod
    def _default_runner(repo: str, source: str) -> dict:
        orbit = OrbitAdapter._orbit_bin()

        def run(args: list[str]) -> str:
            proc = subprocess.run(
                [orbit, *args], cwd=repo, capture_output=True, text=True, check=True
            )
            return proc.stdout

        def sql(query: str) -> list[dict]:
            out = run(["sql", "--format", "json", query]).strip()
            return json.loads(out) if out else []

        # Re-index so the freshest manifest row is this repo, then scope every
        # query to that commit -- the local DuckDB graph may hold several repos.
        run(["index", "."])
        manifest = sql(
            "SELECT commit_sha FROM _orbit_manifest WHERE status = 'indexed' "
            "ORDER BY last_indexed_at DESC LIMIT 1"
        )
        if not manifest:
            return {"files": [], "definitions": [], "references": []}
        sha = manifest[0]["commit_sha"]

        files = sql(
            f"SELECT path, language FROM gl_file WHERE commit_sha = '{sha}'"
        )
        # Fan-in = inbound CALLS edges to a definition (gl_edge), computed in SQL
        # by definition id so name collisions do not distort the count.
        definitions = sql(
            "SELECT d.name AS name, d.definition_type AS kind, "
            "d.file_path AS path, COUNT(e.source_id) AS fan_in "
            "FROM gl_definition d "
            "LEFT JOIN gl_edge e ON e.target_id = d.id "
            "AND e.target_kind = 'Definition' AND e.relationship_kind = 'CALLS' "
            f"WHERE d.commit_sha = '{sha}' "
            "GROUP BY d.id, d.name, d.definition_type, d.file_path"
        )
        return {"files": files, "definitions": definitions, "references": []}
