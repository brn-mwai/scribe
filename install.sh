#!/usr/bin/env bash
# Scribe end-user installer. Sets up a virtualenv and installs the CLI.
set -euo pipefail

PYTHON="${PYTHON:-python3}"

if ! "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "scribe: Python 3.11+ is required (found $($PYTHON --version 2>&1))." >&2
  exit 1
fi

"$PYTHON" -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
pip install --upgrade pip >/dev/null
pip install .

echo "scribe: installed. Try: scribe --help"
