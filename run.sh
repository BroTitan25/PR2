#!/usr/bin/env sh
for candidate in python3 python py; do
  if "$candidate" -c "" >/dev/null 2>&1; then
    PYTHON=$candidate
    break
  fi
done
ROOT=$(dirname "$0")
PYTHONPATH="$ROOT/src" exec "$PYTHON" -m depviz "$@"
