#!/usr/bin/env bash
set -euo pipefail

PY=.venv-core/bin/python
UV_PROJECT_ENVIRONMENT=.venv-core uv sync --no-dev --no-editable --quiet

"$PY" -c "
import sys, agentcitadel
heavy = {'torch','transformers','presidio_analyzer','spacy','opentelemetry','litellm'}
leaked = heavy & {m.split('.')[0] for m in sys.modules}
assert not leaked, f'core import pulled: {leaked}'
print('core clean')
"

uv pip list --python "$PY" --format json \
  | "$PY" -c 'import json,sys; print(len(json.load(sys.stdin)) - 1, "runtime dependencies")'