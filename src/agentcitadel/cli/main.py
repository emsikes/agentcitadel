"""citadel command line."""

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from agentcitadel.agent import CitadelAgent
from agentcitadel.guard.approval import CLIApprover
from agentcitadel.guard.detectors.regex import RegexDetector
from agentcitadel.guard.pipeline import GuardPipeline
from agentcitadel.guard.policy.schema import Policy
from agentcitadel.llm.anthropic import AnthropicProvider
from agentcitadel.observe.recorder import Recorder
from agentcitadel.storage.filesystem import FilesystemStorage
from agentcitadel.tools.registry import ToolRegistry

app = typer.Typer(help="AgentCitadel — guarded agent runs and trace inspection.")
console = Console()


@app.callback()
def main() -> None:
    """AgentCitadel - guarded agent runs and trace inspection."""


@app.command()
def trace(
    run_id: str,
    trace_dir: Annotated[
        Path, typer.Option(help="Directory holding trace files.")
    ] = Path("traces"),
) -> None:
    """Show the recorded spans for a run."""
    path = trace_dir / f"{run_id}.jsonl"
    if not path.exists():
        console.print(f"[red]No trace found at {path}[/red]")
        raise typer.Exit(1)

    table = Table("kind", "name", "detail")
    for line in path.read_text().splitlines():
        span = json.loads(line)
        table.add_row(span["kind"], span["name"], json.dumps(span["output"])[:80])

    console.print(table)


@app.command()
def run(
    prompt: str,
    policy: Annotated[Path, typer.Option(help="Tool policy file.")] = Path(
        "tool_policies.yaml"
    ),
    trace_dir: Annotated[Path, typer.Option(help="Where to write traces.")] = Path(
        "traces"
    ),
) -> None:
    """Run the guard agent against a prompt."""
    agent = CitadelAgent(
        provider=AnthropicProvider(),
        tools=ToolRegistry([]),
        recorder=Recorder(FilesystemStorage(trace_dir)),
        policy=Policy.from_yaml(policy) if policy.exists() else Policy(),
        approver=CLIApprover(),
        input_guard=GuardPipeline(
            [
                RegexDetector(
                    {"instruction_override": r"ignore (all )?previous instructions"}
                )
            ]
        ),
        output_guard=GuardPipeline([]),
    )
    reply = asyncio.run(agent.run(prompt))
    console.print(reply.content)
