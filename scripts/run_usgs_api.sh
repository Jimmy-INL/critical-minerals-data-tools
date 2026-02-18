#!/usr/bin/env bash
set -euo pipefail

PORT="${USGS_PORT:-8011}"

if [[ -z "${OPENAI_API_KEY:-}" && -z "${OPENAI_API_KEY_OSS:-}" ]]; then
  for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.profile"; do
    if [[ -f "${rc}" ]]; then
      # shellcheck source=/dev/null
      source "${rc}"
    fi
  done
fi

if [[ -z "${OPENAI_API_KEY:-}" && -z "${OPENAI_API_KEY_OSS:-}" ]]; then
  echo "WARNING: OPENAI_API_KEY or OPENAI_API_KEY_OSS is not set in the environment."
fi

# Prefer model/base_url from repo .env (non-secret), avoid stale shell exports.
unset OPENAI_MODEL OPENAI_BASE_URL
ENV_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/.env"
if [[ -f "${ENV_FILE}" ]]; then
  export OPENAI_MODEL="$(grep -E '^OPENAI_MODEL=' "${ENV_FILE}" | tail -n1 | cut -d= -f2- | tr -d '\"')"
  export OPENAI_BASE_URL="$(grep -E '^OPENAI_BASE_URL=' "${ENV_FILE}" | tail -n1 | cut -d= -f2- | tr -d '\"')"
fi

echo "DEBUG: OPENAI_MODEL=${OPENAI_MODEL:-<empty>}"
echo "DEBUG: OPENAI_BASE_URL=${OPENAI_BASE_URL:-<empty>}"
if [[ -n "${OPENAI_API_KEY_OSS:-}" ]]; then
  echo "DEBUG: OPENAI_API_KEY_OSS set? yes"
else
  echo "DEBUG: OPENAI_API_KEY_OSS set? no"
fi
if [[ -n "${OPENAI_API_KEY:-}" ]]; then
  echo "DEBUG: OPENAI_API_KEY set? yes"
else
  echo "DEBUG: OPENAI_API_KEY set? no"
fi

PIDS="$(lsof -ti :"${PORT}" || true)"
if [[ -n "${PIDS}" ]]; then
  echo "Killing processes on port ${PORT}: ${PIDS}"
  kill -9 ${PIDS}
fi

cd "$(dirname "${BASH_SOURCE[0]}")/../USGS_MCP"
uv run usgs-api
