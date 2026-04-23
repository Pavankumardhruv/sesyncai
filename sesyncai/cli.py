"""CLI entry point — sesyncai commands."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from . import __version__
from .model import ProjectContext
from .scanner import scan_project
from .exporters import export_context, EXPORTERS
from .gist import push, pull
from .instructions import InstructionStore, CATEGORIES
from .extractor import scan_all, merge_into_store

app = typer.Typer(
    name="sesyncai",
    help="Capture, sync, and share your AI project context.",
    invoke_without_command=True,
)
console = Console()

CTX_DIR = ".sesyncai"
CTX_FILE = "context.yaml"
INST_FILE = "instructions.yaml"


def _version_callback(value: bool):
    if value:
        console.print(f"sesyncai {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", callback=_version_callback, is_eager=True, help="Show version"),
):
    """Capture, sync, and share your AI project context."""
    if ctx.invoked_subcommand is None:
        _interactive_flow()


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
    """Push context and instructions to a GitHub Gist."""
    root = Path(path).resolve() if path else Path.cwd()
    _require_init(root)

    ctx = ProjectContext.load(_ctx_path(root))
    store = InstructionStore.load(_inst_path(root))

    with console.status("Syncing to GitHub Gist…"):
        gist_id = push(ctx, store)
        ctx.save(_ctx_path(root))

    parts = [f"[bold green]Synced[/bold green]\n"]
    parts.append(f"  Gist ID:  {gist_id}")
    parts.append(f"  URL:      https://gist.github.com/{gist_id}")
    parts.append(f"  Context:  {ctx.name} ({ctx.language or 'unknown'})")
    if store.instructions:
        parts.append(f"  Rules:    {len(store.instructions)} instructions")

    console.print(Panel("\n".join(parts), title="sesyncai sync", border_style="cyan"))


@app.command()
def load(
    gist_id: str = typer.Argument(..., help="Gist ID to pull context from"),
    path: Optional[str] = typer.Option(None, "--path", "-p", help="Project root to save into"),
):
    """Pull context and instructions from a GitHub Gist."""
    root = Path(path).resolve() if path else Path.cwd()

    with console.status("Pulling from GitHub Gist…"):
        ctx, store = pull(gist_id)

    ctx.save(_ctx_path(root))
    if store.instructions:
        store.save(_inst_path(root))

    parts = [f"[bold green]Loaded[/bold green] → .sesyncai/\n"]
    parts.append(f"  Name:      {ctx.name}")
    parts.append(f"  Language:   {ctx.language or '—'}")
    parts.append(f"  Framework:  {ctx.framework or '—'}")
    if store.instructions:
        parts.append(f"  Rules:     {len(store.instructions)} instructions")

    console.print(Panel("\n".join(parts), title="sesyncai load", border_style="cyan"))


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


# ── Interactive flow ─────────────────────────────────────────────────


def _prompt_choice(prompt: str, options: list[str]) -> int:
    for i, opt in enumerate(options, 1):
        console.print(f"  [cyan]{i}[/cyan]  {opt}")
    console.print()

    while True:
        try:
            raw = console.input(f"[bold]{prompt}[/bold] ")
            choice = int(raw.strip())
            if 1 <= choice <= len(options):
                return choice - 1
        except (ValueError, EOFError):
            pass
        console.print(f"[dim]Enter a number 1–{len(options)}[/dim]")


def _interactive_flow() -> None:
    root = Path.cwd()

    console.print(Panel(
        "[bold]sesyncai[/bold] — AI context capture & sync\n\n"
        f"Project directory: [cyan]{root}[/cyan]",
        border_style="cyan",
    ))

    ctx_path = _ctx_path(root)
    inst_path = _inst_path(root)
    has_context = ctx_path.exists()

    if has_context:
        ctx = ProjectContext.load(ctx_path)
        store = InstructionStore.load(inst_path)
        console.print(f"[green]Context loaded[/green] — {ctx.name} ({ctx.language or 'unknown'}, {len(ctx.dependencies)} deps, {len(store.instructions)} instructions)\n")
    else:
        console.print("[yellow]No context yet.[/yellow] Let's set it up.\n")

    while True:
        if not has_context:
            options = [
                "Scan this project",
                "Exit",
            ]
        else:
            options = [
                "Re-scan project (refresh context)",
                "Scan for instructions in AI context files",
                "Add an instruction manually",
                "View captured instructions",
                "Save as local markdown file",
                "Export for Claude Code (CLAUDE.md)",
                "Export for Cursor (.cursorrules)",
                "Copy system prompt to paste anywhere",
                "Sync to GitHub Gist",
                "Exit",
            ]

        choice = _prompt_choice("What would you like to do?", options)

        if not has_context:
            if choice == 0:
                with console.status("Scanning project…"):
                    ctx = scan_project(root)
                ctx.save(ctx_path)
                store = InstructionStore.load(inst_path)
                has_context = True
                console.print(Panel(
                    f"[bold green]Context captured[/bold green]\n\n"
                    f"  Name:      {ctx.name}\n"
                    f"  Language:   {ctx.language or '—'}\n"
                    f"  Framework:  {ctx.framework or '—'}\n"
                    f"  Deps:       {len(ctx.dependencies)}",
                    border_style="cyan",
                ))
                continue
            else:
                break
        else:
            if choice == 0:
                with console.status("Scanning project…"):
                    ctx = scan_project(root)
                ctx.save(ctx_path)
                console.print("[green]Context refreshed.[/green]\n")
                continue

            elif choice == 1:
                with console.status("Scanning AI context files…"):
                    found = scan_all(root)
                if not found:
                    console.print("[yellow]No instructions found in AI context files.[/yellow]\n")
                else:
                    added, skipped = merge_into_store(store, found)
                    store.save(inst_path)
                    console.print(f"[green]Extracted {added} instructions[/green]"
                                  + (f" [dim]({skipped} duplicates skipped)[/dim]" if skipped else "") + "\n")
                continue

            elif choice == 2:
                try:
                    text = console.input("[bold]Instruction:[/bold] ")
                except EOFError:
                    continue
                if not text.strip():
                    console.print("[dim]Skipped — empty input[/dim]\n")
                    continue

                cat_options = list(CATEGORIES)
                console.print()
                cat_idx = _prompt_choice("Category?", cat_options)
                try:
                    inst = store.add(text.strip(), category=cat_options[cat_idx])
                    store.save(inst_path)
                    console.print(f"[green]Captured[/green] [{inst.category}] {inst.text}\n")
                except ValueError as e:
                    console.print(f"[red]{e}[/red]\n")
                continue

            elif choice == 3:
                if not store.instructions:
                    console.print("[dim]No instructions captured yet.[/dim]\n")
                else:
                    _render_instructions_table(store)
                    console.print()
                continue

            elif choice == 4:
                _save_local_markdown(root, ctx, store)
                continue

            elif choice == 5:
                result = export_context(ctx, "claude", root, store)
                console.print(f"[green]Saved[/green] → {result}\n")
                continue

            elif choice == 6:
                result = export_context(ctx, "cursor", root, store)
                console.print(f"[green]Saved[/green] → {result}\n")
                continue

            elif choice == 7:
                result = export_context(ctx, "prompt", root, store)
                console.print(Panel(result.strip(), title="System Prompt — copy this", border_style="green"))
                console.print()
                continue

            elif choice == 8:
                try:
                    with console.status("Syncing to GitHub Gist…"):
                        gist_id = push(ctx, store)
                        ctx.save(ctx_path)
                    n = len(store.instructions)
                    console.print(f"[green]Synced[/green] → https://gist.github.com/{gist_id}"
                                  + (f" ({n} instructions included)" if n else "") + "\n")
                except Exception as e:
                    console.print(f"[red]Sync failed:[/red] {e}\n")
                continue

            else:
                break

    console.print("[dim]Done.[/dim]")


def _save_local_markdown(root: Path, ctx: ProjectContext, store: InstructionStore) -> None:
    from .exporters import to_claude_md

    default_name = f"{ctx.name}-context.md"
    try:
        raw = console.input(f"[bold]Filename[/bold] [dim]({default_name})[/dim]: ")
    except EOFError:
        raw = ""

    filename = raw.strip() or default_name
    if not filename.endswith(".md"):
        filename += ".md"

    content = to_claude_md(ctx, store)
    out_path = root / filename
    out_path.write_text(content, encoding="utf-8")

    console.print(f"[green]Saved[/green] → {out_path}\n")
    console.print(f"[dim]Open this file and paste it into any AI chat.[/dim]\n")
