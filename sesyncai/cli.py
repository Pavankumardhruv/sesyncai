"""CLI entry point — sesyncai commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .model import ProjectContext
from .scanner import scan_project
from .exporters import export_context, EXPORTERS
from .gist import push, pull

app = typer.Typer(
    name="sesyncai",
    help="Capture, sync, and share your AI project context.",
    no_args_is_help=True,
)
console = Console()

CTX_DIR = ".sesyncai"
CTX_FILE = "context.yaml"


def _ctx_path(root: Path) -> Path:
    return root / CTX_DIR / CTX_FILE


@app.command()
def init(
    path: Optional[str] = typer.Argument(None, help="Project root (defaults to cwd)"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing context"),
):
    """Scan a project and generate context."""
    root = Path(path).resolve() if path else Path.cwd()

    if not root.is_dir():
        console.print(f"[red]Not a directory:[/red] {root}")
        raise typer.Exit(1)

    ctx_path = _ctx_path(root)
    if ctx_path.exists() and not force:
        console.print(f"[yellow]Context already exists.[/yellow] Use --force to overwrite.")
        raise typer.Exit(1)

    with console.status("Scanning project…"):
        ctx = scan_project(root)

    ctx.save(ctx_path)

    console.print(Panel(
        f"[bold green]Context captured[/bold green] → {ctx_path.relative_to(root)}\n\n"
        f"  Name:      {ctx.name}\n"
        f"  Language:   {ctx.language or '—'}\n"
        f"  Framework:  {ctx.framework or '—'}\n"
        f"  Deps:       {len(ctx.dependencies)}",
        title="sesyncai init",
        border_style="cyan",
    ))


@app.command()
def show(
    path: Optional[str] = typer.Argument(None, help="Project root"),
):
    """Display the captured context."""
    root = Path(path).resolve() if path else Path.cwd()
    ctx_path = _ctx_path(root)

    if not ctx_path.exists():
        console.print("[red]No context found.[/red] Run `sesyncai init` first.")
        raise typer.Exit(1)

    content = ctx_path.read_text()
    console.print(Syntax(content, "yaml", theme="monokai", line_numbers=False))


@app.command()
def export(
    fmt: str = typer.Argument(..., help="Format: claude, cursor, or prompt"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root"),
):
    """Export context to an AI tool format."""
    root = Path(path).resolve() if path else Path.cwd()
    ctx_path = _ctx_path(root)

    if not ctx_path.exists():
        console.print("[red]No context found.[/red] Run `sesyncai init` first.")
        raise typer.Exit(1)

    ctx = ProjectContext.load(ctx_path)

    if fmt not in EXPORTERS:
        console.print(f"[red]Unknown format:[/red] {fmt}")
        console.print(f"Available: {', '.join(EXPORTERS)}")
        raise typer.Exit(1)

    result = export_context(ctx, fmt, root)

    if fmt == "prompt":
        console.print(Panel(result.strip(), title="System Prompt", border_style="cyan"))
    else:
        console.print(f"[green]Exported[/green] → {result}")


@app.command()
def sync(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root"),
):
    """Push context to a GitHub Gist."""
    root = Path(path).resolve() if path else Path.cwd()
    ctx_path = _ctx_path(root)

    if not ctx_path.exists():
        console.print("[red]No context found.[/red] Run `sesyncai init` first.")
        raise typer.Exit(1)

    ctx = ProjectContext.load(ctx_path)

    with console.status("Syncing to GitHub Gist…"):
        gist_id = push(ctx)
        ctx.save(ctx_path)

    console.print(Panel(
        f"[bold green]Synced[/bold green]\n\n"
        f"  Gist ID:  {gist_id}\n"
        f"  URL:      https://gist.github.com/{gist_id}",
        title="sesyncai sync",
        border_style="cyan",
    ))


@app.command()
def load(
    gist_id: str = typer.Argument(..., help="Gist ID to pull context from"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root to save into"),
):
    """Pull context from a GitHub Gist."""
    root = Path(path).resolve() if path else Path.cwd()

    with console.status("Pulling from GitHub Gist…"):
        ctx = pull(gist_id)

    ctx_path = _ctx_path(root)
    ctx.save(ctx_path)

    console.print(Panel(
        f"[bold green]Loaded[/bold green] → {ctx_path.relative_to(root)}\n\n"
        f"  Name:      {ctx.name}\n"
        f"  Language:   {ctx.language or '—'}\n"
        f"  Framework:  {ctx.framework or '—'}",
        title="sesyncai load",
        border_style="cyan",
    ))


@app.command()
def diff(
    path: Optional[str] = typer.Argument(None, help="Project root"),
):
    """Compare saved context with current project state."""
    root = Path(path).resolve() if path else Path.cwd()
    ctx_path = _ctx_path(root)

    if not ctx_path.exists():
        console.print("[red]No context found.[/red] Run `sesyncai init` first.")
        raise typer.Exit(1)

    saved = ProjectContext.load(ctx_path)

    with console.status("Rescanning…"):
        current = scan_project(root)

    saved_yaml = saved.to_yaml()
    current_yaml = current.to_yaml()

    if saved_yaml == current_yaml:
        console.print("[green]Context is up to date.[/green]")
        return

    console.print("[yellow]Context has drifted:[/yellow]\n")

    saved_lines = saved_yaml.splitlines()
    current_lines = current_yaml.splitlines()

    for line in current_lines:
        if line not in saved_lines:
            console.print(f"  [green]+ {line}[/green]")
    for line in saved_lines:
        if line not in current_lines:
            console.print(f"  [red]- {line}[/red]")

    console.print(f"\nRun [cyan]sesyncai init --force[/cyan] to update.")
