#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
uv run pytest packages/*/tests/ tests/ -v --tb=short "$@"
