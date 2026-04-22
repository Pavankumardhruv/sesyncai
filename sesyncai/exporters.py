"""Export project context to different AI tool formats."""

from __future__ import annotations

from pathlib import Path

from .model import ProjectContext


def to_claude_md(ctx: ProjectContext) -> str:
    lines = [f"# {ctx.name}", ""]

    if ctx.description:
        lines.append(ctx.description)
        lines.append("")

    lines.append("## Project")
    if ctx.language:
        lines.append(f"- Language: {ctx.language}")
    if ctx.framework:
        lines.append(f"- Framework: {ctx.framework}")
    if ctx.entry_point:
        lines.append(f"- Entry point: `{ctx.entry_point}`")
    lines.append("")

    if ctx.dependencies:
        lines.append("## Dependencies")
        for dep in ctx.dependencies:
            lines.append(f"- {dep.name}")
        lines.append("")

    if ctx.build_command or ctx.test_command:
        lines.append("## Commands")
        if ctx.build_command:
            lines.append(f"- Build: `{ctx.build_command}`")
        if ctx.test_command:
            lines.append(f"- Test: `{ctx.test_command}`")
        lines.append("")

    if ctx.structure:
        lines.append("## Structure")
        lines.append("```")
        for item in ctx.structure:
            lines.append(item)
        lines.append("```")
        lines.append("")

    if ctx.conventions:
        lines.append("## Conventions")
        for c in ctx.conventions:
            lines.append(f"- {c}")
        lines.append("")

    if ctx.notes:
        lines.append("## Notes")
        for n in ctx.notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def to_cursorrules(ctx: ProjectContext) -> str:
    lines = []

    if ctx.description:
        lines.append(ctx.description)
        lines.append("")

    lines.append(f"This is a {ctx.language or 'software'} project{f' using {ctx.framework}' if ctx.framework else ''}.")
    lines.append("")

    if ctx.entry_point:
        lines.append(f"Entry point: {ctx.entry_point}")
    if ctx.build_command:
        lines.append(f"Build: {ctx.build_command}")
    if ctx.test_command:
        lines.append(f"Test: {ctx.test_command}")

    if ctx.entry_point or ctx.build_command or ctx.test_command:
        lines.append("")

    if ctx.dependencies:
        lines.append("Key dependencies: " + ", ".join(d.name for d in ctx.dependencies[:15]))
        lines.append("")

    if ctx.conventions:
        lines.append("Conventions:")
        for c in ctx.conventions:
            lines.append(f"- {c}")
        lines.append("")

    if ctx.notes:
        for n in ctx.notes:
            lines.append(f"- {n}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def to_system_prompt(ctx: ProjectContext) -> str:
    parts = [f"You are working on {ctx.name}."]

    if ctx.description:
        parts.append(ctx.description)

    tech = []
    if ctx.language:
        tech.append(ctx.language)
    if ctx.framework:
        tech.append(ctx.framework)
    if tech:
        parts.append(f"Tech stack: {', '.join(tech)}.")

    if ctx.entry_point:
        parts.append(f"Entry point: {ctx.entry_point}.")

    if ctx.dependencies:
        top = [d.name for d in ctx.dependencies[:10]]
        parts.append(f"Dependencies: {', '.join(top)}.")

    if ctx.build_command:
        parts.append(f"Build with: {ctx.build_command}.")
    if ctx.test_command:
        parts.append(f"Test with: {ctx.test_command}.")

    if ctx.conventions:
        parts.append("Conventions: " + "; ".join(ctx.conventions) + ".")

    if ctx.notes:
        parts.append("Notes: " + "; ".join(ctx.notes) + ".")

    return " ".join(parts) + "\n"


EXPORTERS = {
    "claude": ("CLAUDE.md", to_claude_md),
    "cursor": (".cursorrules", to_cursorrules),
    "prompt": (None, to_system_prompt),
}


def export_context(ctx: ProjectContext, fmt: str, root: Path) -> str:
    if fmt not in EXPORTERS:
        raise ValueError(f"Unknown format: {fmt}. Choose from: {', '.join(EXPORTERS)}")

    filename, formatter = EXPORTERS[fmt]
    content = formatter(ctx)

    if filename:
        out = root / filename
        out.write_text(content, encoding="utf-8")
        return str(out)

    return content
