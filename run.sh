#!/usr/bin/env sh
PYTHON=$(command -v python3 || command -v python)
ROOT=$(dirname "$0")
PYTHONPATH="$ROOT/src" exec "$PYTHON" -m depviz "$@"
