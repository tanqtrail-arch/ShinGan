#!/bin/bash
set -euo pipefail

# Only run in remote (Claude Code on the web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Install project + dev dependencies
pip install -e ".[dev]" --quiet

# Export PYTHONPATH for module resolution
echo 'export PYTHONPATH="."' >> "$CLAUDE_ENV_FILE"
