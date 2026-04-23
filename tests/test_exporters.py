"""Tests for context exporters."""

from pathlib import Path
from sesyncai.model import ProjectContext, Dependency
from sesyncai.instructions import InstructionStore
from sesyncai.exporters import to_claude_md, to_cursorrules, to_system_prompt, export_context


def _sample_ctx() -> ProjectContext:
    return ProjectContext(
        name="testapp",
        description="A test application",
        language="Python",
        framework="FastAPI",
        entry_point="testapp.main:app",
        build_command="hatch build",
        test_command="pytest",
        dependencies=[Dependency("fastapi"), Dependency("pydantic")],
        structure=["testapp/", "tests/", "pyproject.toml"],
        notes=["Has GitHub Actions CI/CD"],
    )


def _sample_store() -> InstructionStore:
    store = InstructionStore()
    store.add("Always use type hints", category="constraint")
    store.add("Prefer composition over inheritance", category="preference")
    store.add("Use snake_case for all endpoints", category="style")
    return store


def test_claude_md_structure():
    ctx = _sample_ctx()
    output = to_claude_md(ctx)

    assert output.startswith("# testapp\n")
    assert "A test application" in output
    assert "- Language: Python" in output
    assert "- Framework: FastAPI" in output
    assert "- fastapi" in output
    assert "- Build: `hatch build`" in output
    assert "testapp/" in output


def test_claude_md_with_instructions():
    ctx = _sample_ctx()
    store = _sample_store()
    output = to_claude_md(ctx, store)

    assert "## Instructions" in output
    assert "### Constraints" in output
    assert "Always use type hints" in output
    assert "### Preferences" in output
    assert "Prefer composition over inheritance" in output
    assert "### Code Style" in output


def test_claude_md_without_instructions():
    ctx = _sample_ctx()
    output = to_claude_md(ctx)
    assert "## Instructions" not in output


def test_cursorrules_structure():
    ctx = _sample_ctx()
    output = to_cursorrules(ctx)

    assert "Python" in output
    assert "FastAPI" in output
    assert "Entry point: testapp.main:app" in output
    assert "fastapi, pydantic" in output


def test_cursorrules_with_instructions():
    ctx = _sample_ctx()
    store = _sample_store()
    output = to_cursorrules(ctx, store)

    assert "Always use type hints" in output
    assert "Prefer composition over inheritance" in output


def test_system_prompt_structure():
    ctx = _sample_ctx()
    output = to_system_prompt(ctx)

    assert output.startswith("You are working on testapp.")
    assert "Python, FastAPI" in output
    assert "fastapi, pydantic" in output
    assert "hatch build" in output
    assert "pytest" in output


def test_system_prompt_with_instructions():
    ctx = _sample_ctx()
    store = _sample_store()
    output = to_system_prompt(ctx, store)

    assert "Key rules:" in output
    assert "Always use type hints" in output
    assert "Guidelines:" in output


def test_export_writes_file(tmp_path: Path):
    ctx = _sample_ctx()
    result = export_context(ctx, "claude", tmp_path)

    assert result == str(tmp_path / "CLAUDE.md")
    assert (tmp_path / "CLAUDE.md").exists()
    content = (tmp_path / "CLAUDE.md").read_text()
    assert "# testapp" in content


def test_export_cursor_writes_file(tmp_path: Path):
    ctx = _sample_ctx()
    result = export_context(ctx, "cursor", tmp_path)

    assert result == str(tmp_path / ".cursorrules")
    assert (tmp_path / ".cursorrules").exists()


def test_export_prompt_returns_string(tmp_path: Path):
    ctx = _sample_ctx()
    result = export_context(ctx, "prompt", tmp_path)

    assert "You are working on testapp" in result
    assert not (tmp_path / "prompt").exists()
