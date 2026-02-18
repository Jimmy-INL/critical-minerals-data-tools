#!/usr/bin/env bash
set -euo pipefail

PORT="${DOCS_PORT:-8085}"

PIDS="$(lsof -ti :"${PORT}" || true)"
if [[ -n "${PIDS}" ]]; then
  echo "Killing processes on port ${PORT}: ${PIDS}"
  kill -9 ${PIDS}
fi

cd "$(dirname "${BASH_SOURCE[0]}")/../docs/examples"
python -m http.server "${PORT}"
