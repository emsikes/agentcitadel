"""citadel command line."""

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="AgentCitadel — guarded agent runs and trace inspection.")
console = Console()


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
