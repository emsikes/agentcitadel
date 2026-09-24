# AgentCitadel

**Fortified agents. Full visibility.**

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?logo=pydantic&logoColor=white)
![uv](https://img.shields.io/badge/uv-managed-DE5FE9?logo=uv&logoColor=white)
![Ruff](https://img.shields.io/badge/Ruff-linted-D7FF64?logo=ruff&logoColor=black)
![mypy](https://img.shields.io/badge/mypy-strict-2A6DB2)
![pytest](https://img.shields.io/badge/pytest-passing-0A9EDC?logo=pytest&logoColor=white)
![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-export-425CC7?logo=opentelemetry&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-storage-003B57?logo=sqlite&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-provider-D97757?logo=anthropic&logoColor=white)
[![CI](https://github.com/emsikes/agentcitadel/actions/workflows/ci.yml/badge.svg)](https://github.com/emsikes/agentcitadel/actions/workflows/ci.yml)

An agent framework where guardrails, authorization, and audit trails are primitives rather than
add-ons. Every agent run is guarded on the way in, authorized at every tool call, guarded on the
way out, and recorded in full.

---

## Why

Most agent frameworks treat security as middleware you bolt on afterwards. That ordering produces
systems where a prompt injection reaches the model unexamined, a tool executes because nobody wrote
a rule preventing it, and the only evidence of what happened is whatever got logged by accident.

AgentCitadel inverts the default. Tools are denied unless a policy permits them. Guards fail closed.
Every decision — including the ones that allowed something — is written to an append-only trace
before the run continues.

---

## How it works

A single agent run, step by step.

1. **A user sends a prompt.** Someone hands the agent a question or instruction.

2. **The input guard inspects it.** Every configured detector runs concurrently, each looking for
   something different — injection attempts, personal data, whatever you set up. All of them finish
   before anything else happens.

3. **Their answers collapse into one verdict.** If any detector says block, the request is blocked.
   If none block but one is suspicious, it is flagged and allowed through. Otherwise it is clean.

4. **A blocked run stops here.** The caller receives a plain sentence naming the check that caught
   it. The decision is written to the trace first, so a blocked run leaves exactly as much evidence
   as a successful one.

5. **An allowed prompt goes to the model,** along with your system instructions and the list of
   tools the agent may use.

6. **The model replies one of two ways.** Either it answers in text, meaning it is finished, or it
   asks to use a tool.

7. **A requested tool is checked against the policy file first.** Your rules say whether that tool
   is allowed, denied, or requires a person to approve it. Anything without a matching rule is
   denied by default.

8. **A rule of `ask` prompts a human.** On a terminal, that is a yes/no question showing exactly
   what the tool would do. Running unattended, it is refused rather than hanging.

9. **Denied tools do not run.** The model is told it was refused and why, as text, so it can try a
   different approach instead of the run failing.

10. **Allowed tools run and their output returns to the model.** If a tool raises, the error message
    is what goes back — the model reads it like any other result.

11. **Steps 5 through 10 repeat** until the model answers in text or the turn limit is reached.

12. **The final answer passes the output guard** — the same mechanism as step 2, pointed at what is
    leaving rather than what arrived, catching leaked personal data or exfiltration attempts.

13. **The caller receives the answer, or a block notice.**

Underneath all of it, every step appends a line to a file named after that run: guard decisions,
model calls, policy rulings, tool executions. That file is what `citadel trace` reads back, and it
is why "why did this happen" is answerable after the fact rather than a guess.

---

## Install

```bash
pip install agentcitadel
```

Optional extras, none of which the core requires:

```bash
pip install agentcitadel[pii]          # Presidio-backed PII detection
pip install agentcitadel[guard-local]  # local transformer classifier
pip install agentcitadel[otel]         # OpenTelemetry export
pip install agentcitadel[postgres]     # PostgreSQL storage backend
```

Set your provider key:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

---

## Usage

```python
import asyncio
from pathlib import Path

from agentcitadel.agent import CitadelAgent
from agentcitadel.guard.approval import CLIApprover
from agentcitadel.guard.detectors.regex import RegexDetector
from agentcitadel.guard.pipeline import GuardPipeline
from agentcitadel.guard.policy.schema import Policy
from agentcitadel.llm.anthropic import AnthropicProvider
from agentcitadel.observe.recorder import Recorder
from agentcitadel.storage.filesystem import FilesystemStorage
from agentcitadel.tools.base import Tool
from agentcitadel.tools.registry import ToolRegistry


async def read_file(path: str) -> str:
    return Path(path).read_text()


agent = CitadelAgent(
    provider=AnthropicProvider(model="claude-sonnet-4-5"),
    tools=ToolRegistry(
        [
            Tool(
                name="fs.read",
                description="Read a file from disk",
                parameters={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                fn=read_file,
            )
        ]
    ),
    recorder=Recorder(FilesystemStorage(Path("traces"))),
    policy=Policy.from_yaml(Path("tool_policies.yaml")),
    approver=CLIApprover(),
    input_guard=GuardPipeline(
        [
            RegexDetector(
                {"instruction_override": r"ignore (all )?previous instructions"}
            )
        ]
    ),
    output_guard=GuardPipeline([]),
    system="You are a careful research assistant.",
)

reply = asyncio.run(agent.run("Summarise the contents of ./notes.md"))
print(reply.content)
```

### Policy file

```yaml
default: deny

rules:
  - tool: fs.read
    action: allow

  - tool: fs.*
    action: ask
    reason: filesystem write outside the read allowlist

  - tool: shell.*
    action: deny
    reason: shell execution is not permitted
```

Rules are evaluated in order and the first match wins, so specific rules go above broad ones.
Patterns are globs, not regular expressions: `fs.read` matches only `fs.read`, never `fsXread`.
Matching is case-sensitive, and `default: deny` means a tool you forget to write a rule for
does not run.

---

## Concepts

### Guard

Two chokepoints — one on input, one on output — each running a pipeline of detectors concurrently.
Verdicts combine fail-closed: `BLOCK` beats `FLAG` beats `ALLOW`, regardless of which detector
produced them or in what order. Adding a detector can never make a system more permissive.

Between them sits tool authorization: a declarative YAML policy resolving each call to allow, deny,
or ask, with human approval pluggable per deployment (terminal prompt, webhook, or automatic
refusal when unattended).

### Observe

Every step emits a `Span` — the run it belongs to, its kind (`llm`, `tool`, `guard`, `policy`), and
its full input and output. Spans append to a JSONL file per run. Nothing is overwritten and nothing
is deleted, which is what makes a trace usable as evidence rather than as a log.

### Memory

Episodic, semantic, and procedural stores behind a single audited interface, where every read and
write is recorded. Planned; see Status.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Ecosystem standard, native async, modern typing |
| Validation | Pydantic v2 | Runtime validation at every boundary |
| HTTP | httpx | Async client for providers and approval webhooks |
| CLI | Typer + Rich | Terminal output that a human can act on |
| Config | pydantic-settings | Environment and `.env` with validation |
| Vector store | sqlite-vec | Single auditable file, no server |
| Storage | JSONL / SQLite / PostgreSQL | Append-only by default, scaling when needed |
| Tracing | Native spans, OTEL export | Replay needs verbatim records that OTEL discards |
| Tooling | uv, ruff, mypy (strict), pytest | Fast, reproducible, strictly typed |

### Dependency budget

A security tool that installs half of PyPI is asking you to trust a supply chain nobody has read.
The core is 22 runtime dependencies and imports no machine-learning stack. Transformers, Presidio,
OpenTelemetry, and database drivers live behind extras and are verified absent from a bare install
by a dedicated CI job.

### Provider neutrality

Vendors disagree about message shape — where tool calls live, whether tool results are their own
role, whether system prompts are a message or a parameter. AgentCitadel defines one neutral
`Message` type and translates at each adapter's edge, so the agent loop never contains a vendor
conditional.

---

## Status

Pre-release and under active development. The API is not yet stable.

| Component | State |
|---|---|
| Core types and protocols | Complete |
| Guard pipeline, verdict resolution | Complete |
| Tool policy: schema, matcher, evaluation, lint | Complete |
| Approvers: auto-deny, CLI, webhook | Complete |
| Regex detector | Complete |
| Span, recorder, filesystem storage | Complete |
| Tool registry and execution | Complete |
| Anthropic provider adapter | Complete |
| Agent loop | Complete |
| Configuration via environment or `.env` | Complete |
| CLI (`citadel run`, `citadel trace`) | Complete |
| Tool loading for the CLI | In progress |
| Memory: episodic, semantic, audit trail | Planned |
| SQLite and PostgreSQL storage backends | Planned |
| Replay, cost metrics, HTML trace viewer | Planned |
| OpenTelemetry export | Planned |
| Vektor-Guard detector | Planned |

---

## Development

```bash
git clone https://github.com/emsikes/agentcitadel.git
cd agentcitadel
uv sync --all-extras
uv run pre-commit install
```

Checks:

```bash
uv run pytest            # test suite
uv run ruff check .      # lint
uv run mypy src tests    # strict type checking
./check-core.sh          # verify the core install stays thin
```

`check-core.sh` builds a separate environment with no extras, imports the package, and asserts that
no heavy dependency was pulled in transitively. A module-scope `import torch` anywhere in the
package fails it.

---

## Security

Report vulnerabilities per [SECURITY.md](SECURITY.md). Please do not open a public issue for a
security report.

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

[theinferenceloop.com](https://theinferenceloop.com) · AI Security · Agentic AI

Related work: [Vektor-Guard](https://github.com/emsikes/Vektor-Guard), a ModernBERT prompt-injection
classifier, and the [agent evaluation harness](https://github.com/emsikes/agent-evaluation-harness).