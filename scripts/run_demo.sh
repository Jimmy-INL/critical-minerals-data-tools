#!/usr/bin/env bash
set -euo pipefail

# Ports (override via env)
BGS_PORT="${BGS_PORT:-8000}"
USGS_PORT="${USGS_PORT:-8011}"
DOCS_PORT="${DOCS_PORT:-8085}"

# Kill existing processes on ports
for PORT in "${BGS_PORT}" "${USGS_PORT}" "${DOCS_PORT}"; do
  PIDS="$(lsof -ti :"${PORT}" || true)"
  if [[ -n "${PIDS}" ]]; then
    echo "Killing processes on port ${PORT}: ${PIDS}"
    kill -9 ${PIDS}
  fi
done

# Start services
echo "Starting BGS API on ${BGS_PORT}..."
BGS_PORT="${BGS_PORT}" ./scripts/run_bgs_api.sh &
PID_BGS=$!

echo "Starting USGS API on ${USGS_PORT}..."
USGS_PORT="${USGS_PORT}" ./scripts/run_usgs_api.sh &
PID_USGS=$!

echo "Starting docs server on ${DOCS_PORT}..."
DOCS_PORT="${DOCS_PORT}" ./scripts/run_docs_server.sh &
PID_DOCS=$!

echo ""
echo "Demo running:"
echo "  BGS API  -> http://localhost:${BGS_PORT}"
echo "  USGS API -> http://localhost:${USGS_PORT}"
echo "  Globe    -> http://localhost:${DOCS_PORT}/bgs_globe.html"
echo ""
if command -v open >/dev/null 2>&1; then
  open "http://localhost:${DOCS_PORT}/bgs_globe.html?source=usgs&commodity=copper"
fi
echo "Press Ctrl+C to stop all."

cleanup() {
  echo "Stopping services..."
  kill -9 ${PID_BGS} ${PID_USGS} ${PID_DOCS} 2>/dev/null || true
}
trap cleanup INT TERM EXIT

wait
