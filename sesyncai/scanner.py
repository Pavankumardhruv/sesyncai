"""Auto-detect project context from code, config files, and git history."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Optional

from .model import ProjectContext, Dependency


def scan_project(root: Path) -> ProjectContext:
    ctx = ProjectContext()
    ctx.name = root.name

    _scan_git(root, ctx)
    _scan_python(root, ctx)
    _scan_node(root, ctx)
    _scan_flutter(root, ctx)
    _scan_rust(root, ctx)
    _scan_go(root, ctx)
    _scan_structure(root, ctx)
    _scan_existing_context(root, ctx)

    return ctx


def _run(cmd: list[str], cwd: Path) -> Optional[str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _scan_git(root: Path, ctx: ProjectContext) -> None:
    remote = _run(["git", "remote", "get-url", "origin"], root)
    if remote:
        ctx.git_remote = remote

    branch = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root)
    if branch:
        ctx.default_branch = branch


def _scan_python(root: Path, ctx: ProjectContext) -> None:
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"
    requirements = root / "requirements.txt"

    if pyproject.exists():
        _parse_pyproject(pyproject, ctx)
    elif setup_py.exists():
        ctx.language = ctx.language or "Python"
        ctx.entry_point = ctx.entry_point or "setup.py"

    if requirements.exists() and not ctx.dependencies:
        for line in requirements.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split(">=")[0].split("==")[0].split("~=")[0]
                ctx.dependencies.append(Dependency(name=parts.strip()))

    version = _run(["python3", "--version"], root)
    if version and ctx.language == "Python":
        ctx.python_version = version.replace("Python ", "")


def _parse_pyproject(path: Path, ctx: ProjectContext) -> None:
    text = path.read_text()
    data = None

    try:
        import tomllib
        data = tomllib.loads(text)
    except ImportError:
        try:
            import tomli as tomllib
            data = tomllib.loads(text)
        except ImportError:
            pass

    if data is None:
        _parse_pyproject_regex(text, ctx)
        return

    project = data.get("project", {})
    ctx.language = "Python"
    ctx.name = project.get("name", ctx.name)
    ctx.description = project.get("description", ctx.description)

    for dep_str in project.get("dependencies", []):
        name = dep_str.split(">=")[0].split("==")[0].split("~=")[0].split("[")[0].strip()
        ctx.dependencies.append(Dependency(name=name))

    scripts = project.get("scripts", {})
    if scripts:
        ctx.entry_point = list(scripts.values())[0]

    build_backend = data.get("build-system", {}).get("build-backend", "")
    if "hatchling" in build_backend:
        ctx.build_command = "hatch build"
    elif "setuptools" in build_backend:
        ctx.build_command = "python -m build"

    if "pytest" in text:
        ctx.test_command = "pytest"

    _detect_python_framework(ctx)


def _parse_pyproject_regex(text: str, ctx: ProjectContext) -> None:
    """Fallback parser for Python < 3.11 without tomllib/tomli."""
    import re

    ctx.language = "Python"

    m = re.search(r'^name\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if m:
        ctx.name = m.group(1)

    m = re.search(r'^description\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if m:
        ctx.description = m.group(1)

    deps_match = re.search(r'dependencies\s*=\s*\[(.*?)\]', text, re.DOTALL)
    if deps_match:
        for dep in re.findall(r'"([^"]+)"', deps_match.group(1)):
            name = dep.split(">=")[0].split("==")[0].split("~=")[0].split("[")[0].strip()
            ctx.dependencies.append(Dependency(name=name))

    scripts_match = re.search(r'\[project\.scripts\](.*?)(?:\n\[|\Z)', text, re.DOTALL)
    if scripts_match:
        entry = re.search(r'=\s*"([^"]+)"', scripts_match.group(1))
        if entry:
            ctx.entry_point = entry.group(1)

    if "hatchling" in text:
        ctx.build_command = "hatch build"
    elif "setuptools" in text:
        ctx.build_command = "python -m build"

    if "pytest" in text:
        ctx.test_command = "pytest"

    _detect_python_framework(ctx)


def _detect_python_framework(ctx: ProjectContext) -> None:
    dep_names = [d.name.lower() for d in ctx.dependencies]
    if "fastapi" in dep_names:
        ctx.framework = "FastAPI"
    elif "flask" in dep_names:
        ctx.framework = "Flask"
    elif "django" in dep_names:
        ctx.framework = "Django"
    elif "typer" in dep_names:
        ctx.framework = "Typer CLI"


def _scan_node(root: Path, ctx: ProjectContext) -> None:
    pkg = root / "package.json"
    if not pkg.exists():
        return

    try:
        data = json.loads(pkg.read_text())
    except (json.JSONDecodeError, OSError):
        return

    ctx.language = ctx.language or "JavaScript"
    ctx.name = data.get("name", ctx.name)
    ctx.description = data.get("description", ctx.description)

    if "typescript" in str(data.get("devDependencies", {})):
        ctx.language = "TypeScript"

    for name in data.get("dependencies", {}):
        ctx.dependencies.append(Dependency(name=name))

    scripts = data.get("scripts", {})
    if "build" in scripts:
        ctx.build_command = f"npm run build"
    if "test" in scripts:
        ctx.test_command = f"npm test"
    if "main" in data:
        ctx.entry_point = data["main"]

    dep_names = [d.name for d in ctx.dependencies]
    if "next" in dep_names:
        ctx.framework = "Next.js"
    elif "react" in dep_names:
        ctx.framework = "React"
    elif "vue" in dep_names:
        ctx.framework = "Vue"
    elif "express" in dep_names:
        ctx.framework = "Express"

    version = _run(["node", "--version"], root)
    if version:
        ctx.node_version = version.lstrip("v")


def _scan_flutter(root: Path, ctx: ProjectContext) -> None:
    pubspec = root / "pubspec.yaml"
    if not pubspec.exists():
        return

    import yaml
    try:
        data = yaml.safe_load(pubspec.read_text())
    except Exception:
        return

    ctx.language = "Dart"
    ctx.framework = "Flutter"
    ctx.name = data.get("name", ctx.name)
    ctx.description = data.get("description", ctx.description)
    ctx.build_command = "flutter build"
    ctx.test_command = "flutter test"

    for name in data.get("dependencies", {}):
        if name != "flutter":
            ctx.dependencies.append(Dependency(name=name))


def _scan_rust(root: Path, ctx: ProjectContext) -> None:
    cargo = root / "Cargo.toml"
    if not cargo.exists():
        return

    ctx.language = "Rust"
    ctx.build_command = "cargo build"
    ctx.test_command = "cargo test"

    for line in cargo.read_text().splitlines():
        if line.strip().startswith("name") and not ctx.name:
            ctx.name = line.split("=")[-1].strip().strip('"')
        if line.strip().startswith("description"):
            ctx.description = line.split("=", 1)[-1].strip().strip('"')


def _scan_go(root: Path, ctx: ProjectContext) -> None:
    gomod = root / "go.mod"
    if not gomod.exists():
        return

    ctx.language = "Go"
    ctx.build_command = "go build ./..."
    ctx.test_command = "go test ./..."

    for line in gomod.read_text().splitlines():
        if line.startswith("module "):
            ctx.name = line.split()[-1].split("/")[-1]
            break


def _scan_structure(root: Path, ctx: ProjectContext) -> None:
    ignore = {".git", "__pycache__", "node_modules", ".venv", "venv",
              "build", "dist", ".eggs", ".tox", ".mypy_cache", ".pytest_cache",
              ".sesyncai", "target", ".next", ".nuxt"}

    dirs = []
    files = []
    for item in sorted(root.iterdir()):
        if item.name.startswith(".") and item.name not in (".github",):
            continue
        if item.name in ignore:
            continue
        if item.is_dir():
            dirs.append(f"{item.name}/")
        else:
            files.append(item.name)

    ctx.structure = dirs + files


def _scan_existing_context(root: Path, ctx: ProjectContext) -> None:
    claude_md = root / "CLAUDE.md"
    if claude_md.exists():
        ctx.notes.append("Has CLAUDE.md — existing Claude Code context file")
        ctx.files_of_interest.append("CLAUDE.md")

    cursorrules = root / ".cursorrules"
    if cursorrules.exists():
        ctx.notes.append("Has .cursorrules — existing Cursor context file")
        ctx.files_of_interest.append(".cursorrules")

    makefile = root / "Makefile"
    if makefile.exists():
        ctx.files_of_interest.append("Makefile")

    dockerfile = root / "Dockerfile"
    if dockerfile.exists():
        ctx.files_of_interest.append("Dockerfile")
        ctx.notes.append("Dockerized project")

    ci_dir = root / ".github" / "workflows"
    if ci_dir.exists():
        ctx.notes.append("Has GitHub Actions CI/CD")
        ctx.files_of_interest.append(".github/workflows/")
