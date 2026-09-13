#!/usr/bin/env bash
# Scaffold the agentcitadel repository tree.
# Usage: ./scaffold_agentcitadel.sh [target-dir]   (default: ./agentcitadel)
# Idempotent: safe to re-run; existing files are left untouched.

set -euo pipefail

ROOT="${1:-agentcitadel}"
PKG="$ROOT/src/agentcitadel"

mkdir -p "$ROOT"

# ---------------------------------------------------------------- directories
mkdir -p \
  "$PKG" \
  "$PKG/llm" \
  "$PKG/tools/builtin" \
  "$PKG/guard/detectors" \
  "$PKG/guard/policy" \
  "$PKG/memory" \
  "$PKG/observe/exporters" \
  "$PKG/storage" \
  "$PKG/cli/commands" \
  "$ROOT/tests/guard" \
  "$ROOT/tests/memory" \
  "$ROOT/tests/observe" \
  "$ROOT/tests/attacks" \
  "$ROOT/examples" \
  "$ROOT/docs"

# ------------------------------------------------------------- package inits
for d in \
  "$PKG" \
  "$PKG/llm" \
  "$PKG/tools" \
  "$PKG/tools/builtin" \
  "$PKG/guard" \
  "$PKG/guard/detectors" \
  "$PKG/guard/policy" \
  "$PKG/memory" \
  "$PKG/observe" \
  "$PKG/observe/exporters" \
  "$PKG/storage" \
  "$PKG/cli" \
  "$PKG/cli/commands"
do
  touch "$d/__init__.py"
done

# -------------------------------------------------------------- module files
touch \
  "$PKG/py.typed" \
  "$PKG/types.py" \
  "$PKG/protocols.py" \
  "$PKG/exceptions.py" \
  "$PKG/config.py" \
  "$PKG/agent.py" \
  "$PKG/llm/base.py" \
  "$PKG/llm/anthropic.py" \
  "$PKG/llm/openai.py" \
  "$PKG/llm/litellm.py" \
  "$PKG/tools/base.py" \
  "$PKG/tools/registry.py" \
  "$PKG/tools/builtin/fs.py" \
  "$PKG/tools/builtin/http.py" \
  "$PKG/tools/builtin/shell.py" \
  "$PKG/guard/pipeline.py" \
  "$PKG/guard/input_guard.py" \
  "$PKG/guard/output_guard.py" \
  "$PKG/guard/approval.py" \
  "$PKG/guard/detectors/regex.py" \
  "$PKG/guard/detectors/vektor.py" \
  "$PKG/guard/detectors/presidio.py" \
  "$PKG/guard/policy/schema.py" \
  "$PKG/guard/policy/engine.py" \
  "$PKG/memory/base.py" \
  "$PKG/memory/episodic.py" \
  "$PKG/memory/semantic.py" \
  "$PKG/memory/procedural.py" \
  "$PKG/memory/audit.py" \
  "$PKG/observe/recorder.py" \
  "$PKG/observe/metrics.py" \
  "$PKG/observe/replay.py" \
  "$PKG/observe/exporters/jsonl.py" \
  "$PKG/observe/exporters/otel.py" \
  "$PKG/observe/exporters/html.py" \
  "$PKG/storage/base.py" \
  "$PKG/storage/filesystem.py" \
  "$PKG/storage/sqlite.py" \
  "$PKG/storage/postgres.py" \
  "$PKG/cli/main.py" \
  "$PKG/cli/commands/run.py" \
  "$PKG/cli/commands/trace.py" \
  "$PKG/cli/commands/guard.py" \
  "$PKG/cli/commands/replay.py" \
  "$PKG/cli/commands/export.py"

# ---------------------------------------------------------------------- tests
touch \
  "$ROOT/tests/conftest.py" \
  "$ROOT/tests/test_agent.py"

for d in guard memory observe attacks; do
  touch "$ROOT/tests/$d/.gitkeep"
done

# ------------------------------------------------------------------- examples
touch \
  "$ROOT/examples/minimal_agent.py" \
  "$ROOT/examples/guarded_agent.py" \
  "$ROOT/examples/tool_policies.yaml"

# ----------------------------------------------------------------------- docs
touch \
  "$ROOT/docs/getting-started.md" \
  "$ROOT/docs/architecture.md" \
  "$ROOT/docs/guard-layer.md" \
  "$ROOT/docs/memory-layer.md" \
  "$ROOT/docs/observe-layer.md"

# -------------------------------------------------------------- repo top level
touch \
  "$ROOT/pyproject.toml" \
  "$ROOT/README.md" \
  "$ROOT/CHANGELOG.md" \
  "$ROOT/CONTRIBUTING.md" \
  "$ROOT/SECURITY.md" \
  "$ROOT/LICENSE" \
  "$ROOT/.gitignore" \
  "$ROOT/.env.example"

echo "Scaffolded $ROOT"
command -v tree >/dev/null 2>&1 && tree -a -I '.git' "$ROOT" || find "$ROOT" -type f | sort
