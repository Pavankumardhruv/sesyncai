"""Tests for the project scanner."""

from pathlib import Path
from sesyncai.scanner import scan_project


def test_scan_python_project(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "testapp"
description = "A test project"
dependencies = ["fastapi>=0.100", "pydantic"]

[project.scripts]
testapp = "testapp.cli:main"

[build-system]
build-backend = "hatchling.build"
""")

    (tmp_path / "testapp").mkdir()
    (tmp_path / "testapp" / "__init__.py").touch()

    ctx = scan_project(tmp_path)

    assert ctx.name == "testapp"
    assert ctx.language == "Python"
    assert ctx.framework == "FastAPI"
    assert ctx.description == "A test project"
    assert len(ctx.dependencies) == 2
    assert ctx.entry_point == "testapp.cli:main"
    assert ctx.build_command == "hatch build"


def test_scan_node_project(tmp_path: Path):
    pkg = tmp_path / "package.json"
    pkg.write_text("""{
  "name": "my-app",
  "description": "A React app",
  "main": "index.js",
  "dependencies": {"react": "^18.0", "next": "^14.0"},
  "devDependencies": {"typescript": "^5.0"},
  "scripts": {"build": "next build", "test": "jest"}
}""")

    ctx = scan_project(tmp_path)

    assert ctx.name == "my-app"
    assert ctx.language == "TypeScript"
    assert ctx.framework == "Next.js"
    assert ctx.build_command == "npm run build"
    assert ctx.test_command == "npm test"


def test_scan_flutter_project(tmp_path: Path):
    pubspec = tmp_path / "pubspec.yaml"
    pubspec.write_text("""
name: my_app
description: A Flutter app

dependencies:
  flutter:
    sdk: flutter
  riverpod: ^2.0
""")

    ctx = scan_project(tmp_path)

    assert ctx.name == "my_app"
    assert ctx.language == "Dart"
    assert ctx.framework == "Flutter"
    assert any(d.name == "riverpod" for d in ctx.dependencies)


def test_scan_empty_dir(tmp_path: Path):
    ctx = scan_project(tmp_path)
    assert ctx.name == tmp_path.name
    assert ctx.language == ""


def test_detects_existing_ai_context(tmp_path: Path):
    (tmp_path / "CLAUDE.md").write_text("# Rules")
    (tmp_path / ".cursorrules").write_text("Be helpful")

    ctx = scan_project(tmp_path)

    assert any("CLAUDE.md" in n for n in ctx.notes)
    assert any(".cursorrules" in n for n in ctx.notes)
