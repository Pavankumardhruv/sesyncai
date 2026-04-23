"""Tests for the instruction extractor."""

from pathlib import Path
from sesyncai.extractor import scan_all, _extract_instruction, _negate_if_needed
from sesyncai.instructions import InstructionStore


def test_extract_always_rule():
    assert _extract_instruction("- Always validate user input") == "Always validate user input"


def test_extract_never_rule():
    assert _extract_instruction("- Never use eval()") == "Never use eval()"


def test_extract_use_rule():
    assert _extract_instruction("- Use type hints on all functions") == "Use type hints on all functions"


def test_skip_short_text():
    assert _extract_instruction("- Use X") is None


def test_skip_noise_url():
    assert _extract_instruction("- https://example.com") is None


def test_skip_bare_code():
    assert _extract_instruction("- `some_func`") is None


def test_negate_under_never_section():
    result = _negate_if_needed("Use innerHTML with user content", "never")
    assert result == "Never use innerHTML with user content"


def test_no_double_negate():
    result = _negate_if_needed("Never use eval()", "never")
    assert result == "Never use eval()"


def test_no_negate_normal_section():
    result = _negate_if_needed("Use type hints everywhere", "code style")
    assert result == "Use type hints everywhere"


def test_scan_markdown_file(tmp_path: Path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("""# My Project

## Rules

- Always use type hints
- Prefer functional components over class components

## Never

- Use eval() or exec()
- Avoid importing from internal modules directly
""")

    found = scan_all(tmp_path)
    texts = [i.text for i in found]

    assert any("type hints" in t for t in texts)
    assert any("functional components" in t for t in texts)
    assert any("Never use eval()" in t for t in texts)
    assert any("importing from internal" in t for t in texts)


def test_scan_with_code_blocks_skipped(tmp_path: Path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text("""## Rules

- Always validate input

```python
# Use this pattern always
def validate(x):
    pass
```

- Never skip tests
""")

    found = scan_all(tmp_path)
    texts = [i.text for i in found]

    assert any("validate input" in t for t in texts)
    assert any("skip tests" in t for t in texts)
    assert not any("pattern always" in t for t in texts)


def test_merge_deduplicates():
    from sesyncai.extractor import merge_into_store

    store = InstructionStore()
    store.add("Always validate input")

    from sesyncai.instructions import Instruction
    found = [
        Instruction(text="Always validate input", category="constraint"),
        Instruction(text="Never use eval()", category="constraint"),
    ]

    added, skipped = merge_into_store(store, found)
    assert added == 1
    assert skipped == 1
    assert len(store.instructions) == 2
