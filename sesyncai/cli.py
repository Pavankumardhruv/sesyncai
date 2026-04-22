"""CLI entry point — sesyncai commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .model import ProjectContext
from .scanner import scan_project
from .exporters import export_context, EXPORTERS
from .gist import push, pull
from .instructions import InstructionStore, CATEGORIES
from .extractor import scan_all, merge_into_store

app = typer.Typer(
    name="sesyncai",
    help="Capture, sync, and share your AI project context.",
    no_args_is_help=True,
)
console = Console()

CTX_DIR = ".sesyncai"
CTX_FILE = "context.yaml"
INST_FILE = "instructions.yaml"


def _ctx_path(root: Path) -> Path:
    return root / CTX_DIR / CTX_FILE


def _inst_path(root: Path) -> Path:
    return root / CTX_DIR / INST_FILE


def _require_init(root: Path) -> Path:
    ctx_path = _ctx_path(root)
    if not ctx_path.exists():
        console.print("[red]No context found.[/red] Run `sesyncai init` first.")
        raise typer.Exit(1)
    return ctx_path


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
    _require_init(root)

    content = _ctx_path(root).read_text()
    console.print(Syntax(content, "yaml", theme="monokai", line_numbers=False))

    store = InstructionStore.load(_inst_path(root))
    if store.instructions:
        console.print(f"\n[dim]{len(store.instructions)} instructions captured[/dim] — run `sesyncai instructions` to view")


@app.command()
def export(
    fmt: str = typer.Argument(..., help="Format: claude, cursor, or prompt"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root"),
):
    """Export context to an AI tool format."""
    root = Path(path).resolve() if path else Path.cwd()
    _require_init(root)

    ctx = ProjectContext.load(_ctx_path(root))
    store = InstructionStore.load(_inst_path(root))

    if fmt not in EXPORTERS:
        console.print(f"[red]Unknown format:[/red] {fmt}")
        console.print(f"Available: {', '.join(EXPORTERS)}")
        raise typer.Exit(1)

    result = export_context(ctx, fmt, root, store)

    if fmt == "prompt":
        console.print(Panel(result.strip(), title="System Prompt", border_style="cyan"))
    else:
        console.print(f"[green]Exported[/green] → {result}")
        if store.instructions:
            console.print(f"[dim]Included {len(store.instructions)} instructions[/dim]")


@app.command()
def sync(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root"),
):
    """Push context to a GitHub Gist."""
    root = Path(path).resolve() if path else Path.cwd()
    _require_init(root)

    ctx = ProjectContext.load(_ctx_path(root))

    with console.status("Syncing to GitHub Gist…"):
        gist_id = push(ctx)
        ctx.save(_ctx_path(root))

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
    _require_init(root)

    saved = ProjectContext.load(_ctx_path(root))

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


# ── Instruction capture ──────────────────────────────────────────────


@app.command()
def capture(
    text: Optional[str] = typer.Argument(None, help="Instruction text to capture"),
    category: str = typer.Option("convention", "--category", "-c", help=f"Category: {', '.join(CATEGORIES)}"),
    scan: bool = typer.Option(False, "--scan", "-s", help="Auto-extract from AI context files"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root"),
):
    """Capture a developer instruction, or scan existing AI context files."""
    root = Path(path).resolve() if path else Path.cwd()
    inst_path = _inst_path(root)
    store = InstructionStore.load(inst_path)

    if scan:
        with console.status("Scanning AI context files…"):
            found = scan_all(root)

        if not found:
            console.print("[yellow]No instructions found[/yellow] in CLAUDE.md, .cursorrules, or .claude/rules/")
            return

        added, skipped = merge_into_store(store, found)
        store.save(inst_path)

        console.print(Panel(
            f"[bold green]Extracted {added} instructions[/bold green]"
            + (f" [dim]({skipped} duplicates skipped)[/dim]" if skipped else "")
            + f"\n\nRun [cyan]sesyncai instructions[/cyan] to review",
            title="sesyncai capture --scan",
            border_style="cyan",
        ))

        _show_extraction_summary(found)
        return

    if not text:
        console.print("[red]Provide instruction text or use --scan[/red]")
        console.print("  sesyncai capture \"Always use snake_case for API routes\"")
        console.print("  sesyncai capture --scan")
        raise typer.Exit(1)

    try:
        inst = store.add(text, category=category)
        store.save(inst_path)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    console.print(
        f"[green]Captured[/green] [{inst.category}] {inst.text}"
    )


@app.command()
def instructions(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root"),
    remove: Optional[int] = typer.Option(None, "--remove", "-r", help="Remove instruction by number"),
    clear: bool = typer.Option(False, "--clear", help="Remove all instructions"),
):
    """List, remove, or clear captured instructions."""
    root = Path(path).resolve() if path else Path.cwd()
    inst_path = _inst_path(root)
    store = InstructionStore.load(inst_path)

    if clear:
        count = store.clear()
        store.save(inst_path)
        console.print(f"[yellow]Cleared {count} instructions[/yellow]")
        return

    if remove is not None:
        try:
            removed = store.remove(remove)
            store.save(inst_path)
            console.print(f"[yellow]Removed[/yellow] [{removed.category}] {removed.text}")
        except IndexError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
        return

    if not store.instructions:
        console.print("[dim]No instructions captured yet.[/dim]")
        console.print("  sesyncai capture \"your instruction here\"")
        console.print("  sesyncai capture --scan")
        return

    _render_instructions_table(store)


def _render_instructions_table(store: InstructionStore) -> None:
    table = Table(
        title="Captured Instructions",
        border_style="cyan",
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Category", style="yellow", width=14)
    table.add_column("Instruction", ratio=1)
    table.add_column("Source", style="dim", width=20)

    for i, inst in enumerate(store.instructions):
        table.add_row(str(i), inst.category, inst.text, inst.source)

    console.print(table)
    console.print(f"\n[dim]{len(store.instructions)} total[/dim]")


def _show_extraction_summary(found: list) -> None:
    from collections import Counter

    sources = Counter(i.source for i in found)
    categories = Counter(i.category for i in found)

    console.print()

    if sources:
        console.print("[bold]Sources:[/bold]")
        for source, count in sources.most_common():
            console.print(f"  {source}: {count}")

    if categories:
        console.print("[bold]Categories:[/bold]")
        for cat, count in categories.most_common():
            console.print(f"  {cat}: {count}")
