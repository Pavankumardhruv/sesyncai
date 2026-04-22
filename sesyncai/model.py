"""Context data model — the core schema that sesyncai captures and exports."""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Dependency:
    name: str
    version: str = ""


@dataclass
class ProjectContext:
    name: str = ""
    description: str = ""
    language: str = ""
    framework: str = ""
    python_version: str = ""
    node_version: str = ""
    entry_point: str = ""
    build_command: str = ""
    test_command: str = ""
    dependencies: list[Dependency] = field(default_factory=list)
    dev_dependencies: list[Dependency] = field(default_factory=list)
    structure: list[str] = field(default_factory=list)
    conventions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    files_of_interest: list[str] = field(default_factory=list)
    git_remote: str = ""
    default_branch: str = ""
    last_synced: str = ""
    gist_id: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d = {k: v for k, v in d.items() if v}
        if "dependencies" in d:
            d["dependencies"] = [
                dep if dep.get("version") else dep["name"]
                for dep in d["dependencies"]
            ]
        if "dev_dependencies" in d:
            d["dev_dependencies"] = [
                dep if dep.get("version") else dep["name"]
                for dep in d["dev_dependencies"]
            ]
        return d

    def to_yaml(self) -> str:
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

    @classmethod
    def from_dict(cls, data: dict) -> ProjectContext:
        deps = []
        for d in data.get("dependencies", []):
            if isinstance(d, str):
                deps.append(Dependency(name=d))
            elif isinstance(d, dict):
                deps.append(Dependency(**d))

        dev_deps = []
        for d in data.get("dev_dependencies", []):
            if isinstance(d, str):
                dev_deps.append(Dependency(name=d))
            elif isinstance(d, dict):
                dev_deps.append(Dependency(**d))

        simple_fields = {
            k: v for k, v in data.items()
            if k not in ("dependencies", "dev_dependencies") and isinstance(v, (str, list))
        }
        return cls(dependencies=deps, dev_dependencies=dev_deps, **simple_fields)

    @classmethod
    def from_yaml(cls, text: str) -> ProjectContext:
        data = yaml.safe_load(text) or {}
        return cls.from_dict(data)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_yaml(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> ProjectContext:
        if not path.exists():
            return cls()
        return cls.from_yaml(path.read_text(encoding="utf-8"))
