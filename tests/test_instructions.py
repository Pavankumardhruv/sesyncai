"""Tests for the instruction store."""

import pytest
from pathlib import Path
from sesyncai.instructions import InstructionStore, Instruction


def test_add_and_list():
    store = InstructionStore()
    store.add("Use snake_case", category="style")
    store.add("Never mock the DB", category="constraint")

    assert len(store.instructions) == 2
    assert store.instructions[0].text == "Use snake_case"
    assert store.instructions[1].category == "constraint"


def test_duplicate_rejected():
    store = InstructionStore()
    store.add("Always validate input")

    with pytest.raises(ValueError, match="Duplicate"):
        store.add("Always validate input")


def test_empty_rejected():
    store = InstructionStore()
    with pytest.raises(ValueError, match="empty"):
        store.add("")


def test_remove():
    store = InstructionStore()
    store.add("First rule")
    store.add("Second rule")

    removed = store.remove(0)
    assert removed.text == "First rule"
    assert len(store.instructions) == 1


def test_clear():
    store = InstructionStore()
    store.add("A")
    store.add("B")

    count = store.clear()
    assert count == 2
    assert len(store.instructions) == 0


def test_by_category():
    store = InstructionStore()
    store.add("Rule A", category="style")
    store.add("Rule B", category="constraint")
    store.add("Rule C", category="style")

    grouped = store.by_category()
    assert len(grouped["style"]) == 2
    assert len(grouped["constraint"]) == 1


def test_save_and_load(tmp_path: Path):
    store = InstructionStore()
    store.add("Prefer composition over inheritance", category="architecture")
    store.add("Always run tests first", category="workflow")

    path = tmp_path / "instructions.yaml"
    store.save(path)

    loaded = InstructionStore.load(path)
    assert len(loaded.instructions) == 2
    assert loaded.instructions[0].text == "Prefer composition over inheritance"
    assert loaded.instructions[1].source == "manual"
