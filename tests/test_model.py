"""Tests for the context data model."""

from pathlib import Path
from sesyncai.model import ProjectContext, Dependency


def test_roundtrip_yaml():
    ctx = ProjectContext(
        name="myproject",
        language="Python",
        framework="FastAPI",
        dependencies=[Dependency("fastapi"), Dependency("uvicorn", "0.29")],
    )
    yaml_str = ctx.to_yaml()
    restored = ProjectContext.from_yaml(yaml_str)

    assert restored.name == "myproject"
    assert restored.language == "Python"
    assert restored.framework == "FastAPI"
    assert len(restored.dependencies) == 2
    assert restored.dependencies[0].name == "fastapi"


def test_empty_fields_omitted():
    ctx = ProjectContext(name="minimal")
    d = ctx.to_dict()
    assert "framework" not in d
    assert "dependencies" not in d
    assert d["name"] == "minimal"


def test_save_and_load(tmp_path: Path):
    ctx = ProjectContext(name="saved", language="Rust", build_command="cargo build")
    path = tmp_path / "ctx.yaml"
    ctx.save(path)

    loaded = ProjectContext.load(path)
    assert loaded.name == "saved"
    assert loaded.language == "Rust"
    assert loaded.build_command == "cargo build"


def test_load_missing_file(tmp_path: Path):
    ctx = ProjectContext.load(tmp_path / "nonexistent.yaml")
    assert ctx.name == ""
