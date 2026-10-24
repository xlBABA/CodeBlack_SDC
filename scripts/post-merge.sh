#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

# Use the same Python environment as the existing backend workflow.
# Nix's Python is immutable; install into Replit's writable package directory.
python_version="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
python -m pip install --disable-pip-version-check --no-input \
  --target "$PWD/.pythonlibs/lib/python${python_version}/site-packages" \
  --upgrade -r backend/requirements.txt

# The backend serves the built frontend, so rebuild after merged UI changes.
(
  cd frontend
  npm ci --no-audit --no-fund
  npm run build
)
