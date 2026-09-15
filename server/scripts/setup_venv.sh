#!/usr/bin/env bash
set -euo pipefail

python_bin=""
for candidate in "${PYTHON_BIN:-}" python3 python3.14 python3.13 python3.12 python3.11 python3.10; do
  if [[ -n "$candidate" ]] && command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; raise SystemExit(sys.version_info < (3, 10))'; then
    python_bin="$candidate"
    break
  fi
done

if [[ -z "$python_bin" ]]; then
  echo "Python 3.10 or newer is required. Set PYTHON_BIN to a compatible interpreter." >&2
  exit 1
fi

echo "Creating server/venv with $($python_bin --version 2>&1)"
rm -rf venv
"$python_bin" -m venv venv
venv/bin/python3 -m pip install --upgrade pip
PIP_INDEX_URL=https://pypi.org/simple venv/bin/python3 -m pip install -r requirements.txt
