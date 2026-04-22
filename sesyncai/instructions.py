"""Instruction store — persistent, categorized developer instructions."""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


CATEGORIES = (
    "architecture",
    "convention",
    "constraint",
    "decision",
    "preference",
    "style",
    "workflow",
)


@dataclass
class Instruction:
    text: str
    category: str = "convention"
    source: str = "manual"
    added: str = ""

    def __post_init__(self):
        if not self.added:
            self.added = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self.category not in CATEGORIES:
            self.category = "convention"


@dataclass
class InstructionStore:
    instructions: list[Instruction] = field(default_factory=list)

    def add(self, text: str, category: str = "convention", source: str = "manual") -> Instruction:
        text = text.strip()
        if not text:
            raise ValueError("Instruction text cannot be empty")

        if any(i.text == text for i in self.instructions):
            raise ValueError("Duplicate instruction")

        inst = Instruction(text=text, category=category, source=source)
        self.instructions.append(inst)
        return inst

    def remove(self, index: int) -> Instruction:
        if index < 0 or index >= len(self.instructions):
            raise IndexError(f"No instruction at index {index}")
        return self.instructions.pop(index)

    def clear(self) -> int:
        count = len(self.instructions)
        self.instructions.clear()
        return count

    def by_category(self) -> dict[str, list[Instruction]]:
        grouped: dict[str, list[Instruction]] = {}
        for inst in self.instructions:
            grouped.setdefault(inst.category, []).append(inst)
        return grouped

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(i) for i in self.instructions]
        path.write_text(
            yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path) -> InstructionStore:
        if not path.exists():
            return cls()
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not raw or not isinstance(raw, list):
            return cls()
        instructions = [Instruction(**item) for item in raw]
        return cls(instructions=instructions)
