# sesyncai

[![tests](https://github.com/Pavankumardhruv/sesyncai/actions/workflows/test.yml/badge.svg)](https://github.com/Pavankumardhruv/sesyncai/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Capture, sync, and share your AI project context across tools and machines.

Stop re-explaining your project every time you switch between Claude, Cursor, ChatGPT, or move to a new machine. `sesyncai` scans your codebase once, captures your developer instructions, and generates a portable context snapshot you can export, sync, and reload anywhere.

## Install

```bash
pip install sesyncai
```

## Quick start

Just run `sesyncai` in your project directory — it walks you through everything:

```bash
cd your-project
sesyncai
```

```text
┌──────────────────────────────────────────────┐
│ sesyncai — AI context capture & sync         │
│ Project directory: /your-project             │
└──────────────────────────────────────────────┘

 1  Re-scan project (refresh context)
 2  Scan for instructions in AI context files
 3  Import instructions from a markdown file
 4  Add an instruction manually
 5  View captured instructions
 6  Remove an instruction
 7  Save as local markdown file
 8  Export for Claude Code (CLAUDE.md)
 9  Export for Cursor (.cursorrules)
10  Export for Windsurf (.windsurfrules)
11  Copy system prompt to paste anywhere
12  Sync to GitHub Gist
13  Exit

What would you like to do?
```

Pick a number. No commands to memorize.

### Direct commands

Power users can also use individual commands:

```bash
sesyncai init                    # scan project
sesyncai capture --scan          # extract rules from AI context files
sesyncai capture "your rule"     # add a rule (category auto-detected)
sesyncai import notes.md         # import rules from any markdown file
sesyncai instructions            # view captured rules
sesyncai export claude           # → CLAUDE.md
sesyncai export cursor           # → .cursorrules
sesyncai export windsurf         # → .windsurfrules
sesyncai export prompt           # paste-ready system prompt (copied to clipboard)
sesyncai sync                    # push to GitHub Gist
sesyncai load <gist-id>          # pull on another machine
sesyncai status                  # quick summary
sesyncai diff                    # check for context drift
```

## What it captures

`sesyncai init` auto-detects from your project files:

| Signal | Source |
|---|---|
| Language & framework | `pyproject.toml`, `package.json`, `pubspec.yaml`, `Cargo.toml`, `go.mod` |
| Dependencies | Lock files, manifest files |
| Build & test commands | Package manager configs, Makefiles |
| Project structure | Directory tree (filtered) |
| Git remote & branch | `.git/config` |
| Existing AI context | `CLAUDE.md`, `.cursorrules` |

Everything is stored in `.sesyncai/context.yaml` — a single YAML file you can version, edit, or ignore.

## Instruction capture

The rules and preferences you build up while prompting AI — "use functional components", "never mock the database", "we chose Riverpod over Bloc because..." — normally get lost when you start a new session.

sesyncai captures them:

```bash
# manually, as you make decisions
sesyncai capture "Prefer composition over inheritance" -c architecture
sesyncai capture "All API responses must include request_id" -c constraint

# or auto-extract from existing AI context files
sesyncai capture --scan
```

Auto-scan reads from:

- `CLAUDE.md` — Claude Code project context
- `.cursorrules` — Cursor editor rules
- `.claude/rules/*.md` — scoped Claude rules with path metadata
- `.github/copilot-instructions.md` — GitHub Copilot config
- `.windsurfrules` — Windsurf editor rules

Instructions are categorized automatically (constraint, architecture, style, preference, convention, decision, workflow) and included in every export.

```bash
# review what's captured
sesyncai instructions

# remove one by number
sesyncai instructions --remove 3

# clear all
sesyncai instructions --clear
```

## Export formats

| Format | Command | Output |
|---|---|---|
| Claude Code | `sesyncai export claude` | `CLAUDE.md` |
| Cursor | `sesyncai export cursor` | `.cursorrules` |
| Windsurf | `sesyncai export windsurf` | `.windsurfrules` |
| System prompt | `sesyncai export prompt` | Copied to clipboard + stdout |

## Cloud sync

Push your context to a private GitHub Gist and pull it on any machine:

```bash
# push (creates or updates a gist)
sesyncai sync

# pull (downloads and saves locally)
sesyncai load abc123def456
```

Requires [GitHub CLI](https://cli.github.com/) authenticated: `gh auth login`

## Supported languages

- Python (pyproject.toml, setup.py, requirements.txt)
- JavaScript / TypeScript (package.json)
- Flutter / Dart (pubspec.yaml)
- Rust (Cargo.toml)
- Go (go.mod)

## How it works

```
your-project/
├── pyproject.toml          ← sesyncai reads these for context
├── package.json            ←   (also Cargo.toml, pubspec.yaml, go.mod)
├── .git/                   ← git remote & branch
├── CLAUDE.md               ← extracts instructions from these
├── .cursorrules            ←   (also .claude/rules/, .windsurfrules,
├── .claude/rules/          ←    copilot-instructions.md)
└── .sesyncai/
    ├── context.yaml        ← project snapshot
    └── instructions.yaml   ← captured rules & preferences

sesyncai export claude    →  CLAUDE.md (with instructions)
sesyncai export cursor    →  .cursorrules (with instructions)
sesyncai export windsurf  →  .windsurfrules (with instructions)
sesyncai export prompt    →  clipboard + stdout
sesyncai sync             →  GitHub Gist (private)
```

## License

MIT
