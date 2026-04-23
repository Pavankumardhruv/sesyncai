"""Extract developer instructions from existing AI context files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .instructions import Instruction, InstructionStore

INSTRUCTION_PATTERNS = [
    re.compile(r"^\s*[-*]\s+(Always\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Never\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Don'?t\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Do not\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Must\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Must not\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Prefer\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Avoid\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Use\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Keep\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Ensure\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Run\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(All\b.+\b(?:must|should|shall)\b.+)", re.IGNORECASE),
    re.compile(r"^\s*[-*]\s+(Every\b.+\b(?:must|should|shall)\b.+)", re.IGNORECASE),
]

NOISE_PATTERNS = [
    re.compile(r"^\s*[-*]\s*$"),
    re.compile(r"^\s*[-*]\s*https?://"),
    re.compile(r"^\s*[-*]\s*\[.*\]\(.*\)\s*$"),
    re.compile(r"^\s*[-*]\s*`[^`]+`\s*$"),
    re.compile(r"^\s*[-*]\s*.{0,8}$"),
]

CATEGORY_HINTS = {
    "architecture": ["layer", "module", "service", "component", "pattern", "separate", "decouple", "dependency"],
    "style": ["naming", "name", "case", "snake_case", "camelCase", "format", "indent", "spacing", "lint"],
    "constraint": ["always", "never", "must", "must not", "don't", "do not", "shall", "forbidden", "required"],
    "preference": ["prefer", "favor", "instead of", "over", "rather than", "opt for"],
    "decision": ["chose", "decided", "because", "reason", "rationale", "trade-off", "we went with"],
    "workflow": ["run", "deploy", "test", "build", "commit", "branch", "merge", "ci", "cd", "pipeline"],
    "convention": ["convention", "standard", "rule", "guideline", "practice"],
}


def scan_all(root: Path) -> list[Instruction]:
    found: list[Instruction] = []
    seen_texts: set[str] = set()

    sources = [
        (root / "CLAUDE.md", "CLAUDE.md", _extract_markdown),
        (root / ".cursorrules", ".cursorrules", _extract_cursorrules),
        (root / ".github" / "copilot-instructions.md", "copilot-instructions.md", _extract_markdown),
        (root / ".windsurfrules", ".windsurfrules", _extract_cursorrules),
    ]

    for path, source_name, extractor in sources:
        if path.exists():
            for inst in extractor(path, source_name):
                if inst.text not in seen_texts:
                    seen_texts.add(inst.text)
                    found.append(inst)

    rules_dir = root / ".claude" / "rules"
    if rules_dir.is_dir():
        for rule_file in sorted(rules_dir.glob("*.md")):
            source_name = f".claude/rules/{rule_file.name}"
            for inst in _extract_rule_file(rule_file, source_name):
                if inst.text not in seen_texts:
                    seen_texts.add(inst.text)
                    found.append(inst)

    return found


def _is_noise(line: str) -> bool:
    return any(p.match(line) for p in NOISE_PATTERNS)


def _classify(text: str) -> str:
    lower = text.lower()
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_HINTS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return "convention"

    return max(scores, key=scores.get)


def _extract_instruction(line: str) -> Optional[str]:
    if _is_noise(line):
        return None

    for pattern in INSTRUCTION_PATTERNS:
        m = pattern.match(line)
        if m:
            text = m.group(1).strip()
            text = re.sub(r"\s*[.;,]\s*$", "", text)
            if len(text) > 10:
                return text

    return None


def _join_continuation_lines(raw_lines: list[str]) -> list[str]:
    """Merge bullet-point continuation lines into single logical lines.

    A continuation is any indented non-blank line that doesn't start a new
    bullet or heading, following a bullet line.
    """
    merged: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped:
            merged.append(line)
            continue
        is_bullet = bool(re.match(r"^\s*[-*]\s+", line))
        is_heading = stripped.startswith("#")
        is_fence = stripped.startswith("```")

        if is_bullet or is_heading or is_fence or not merged:
            merged.append(line)
        else:
            prev = merged[-1].strip()
            if prev and re.match(r"^\s*[-*]\s+", merged[-1]):
                merged[-1] = merged[-1].rstrip() + " " + stripped
            else:
                merged.append(line)
    return merged


def _extract_markdown(path: Path, source: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    in_code_block = False
    section_context = ""

    lines = _join_continuation_lines(path.read_text(encoding="utf-8").splitlines())

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        if stripped.startswith("#"):
            section_context = stripped.lstrip("#").strip().lower()
            continue

        text = _extract_instruction(line)
        if text:
            category = _classify(text + " " + section_context)
            instructions.append(Instruction(
                text=text,
                category=category,
                source=source,
            ))

    return instructions


def _extract_cursorrules(path: Path, source: str) -> list[Instruction]:
    instructions: list[Instruction] = []
    in_code_block = False

    for line in _join_continuation_lines(path.read_text(encoding="utf-8").splitlines()):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        text = _extract_instruction(line)
        if text:
            instructions.append(Instruction(
                text=text,
                category=_classify(text),
                source=source,
            ))
            continue

        if stripped.startswith("- ") and len(stripped) > 15:
            content = stripped[2:].strip()
            if any(kw in content.lower() for kw in
                   ("always", "never", "use", "prefer", "avoid", "must", "should", "don't", "keep")):
                instructions.append(Instruction(
                    text=content,
                    category=_classify(content),
                    source=source,
                ))

    return instructions


def _extract_rule_file(path: Path, source: str) -> list[Instruction]:
    text = path.read_text(encoding="utf-8")

    body = text
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            body = text[end + 3:]

    scope = ""
    if text.startswith("---"):
        header = text[3:text.find("---", 3)]
        import yaml
        try:
            meta = yaml.safe_load(header)
            if isinstance(meta, dict) and "paths" in meta:
                scope = f" (scope: {', '.join(meta['paths'][:3])})"
        except Exception:
            pass

    instructions: list[Instruction] = []
    in_code_block = False

    for line in _join_continuation_lines(body.splitlines()):
        stripped = line.strip()

        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        extracted = _extract_instruction(line)
        if extracted:
            if scope:
                extracted = extracted + scope
            instructions.append(Instruction(
                text=extracted,
                category=_classify(extracted),
                source=source,
            ))

    return instructions


def merge_into_store(store: InstructionStore, found: list[Instruction]) -> tuple[int, int]:
    added = 0
    skipped = 0
    existing_texts = {i.text for i in store.instructions}

    for inst in found:
        if inst.text in existing_texts:
            skipped += 1
            continue
        store.instructions.append(inst)
        existing_texts.add(inst.text)
        added += 1

    return added, skipped
