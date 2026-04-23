# sesyncai

[![PyPI](https://img.shields.io/pypi/v/sesyncai.svg)](https://pypi.org/project/sesyncai/)
[![tests](https://github.com/Pavankumardhruv/sesyncai/actions/workflows/test.yml/badge.svg)](https://github.com/Pavankumardhruv/sesyncai/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Your AI context, captured once, usable everywhere.**

Every time you switch between Claude, Cursor, ChatGPT, Windsurf, or move to a new machine — you lose context. You re-explain your project, re-state your preferences, re-teach the same rules. sesyncai fixes that.

It scans your codebase once, captures the developer instructions you've built up over time, and generates a portable context snapshot you can export to any AI tool or sync across machines.

---

## The Problem

You've spent hours training your AI coding assistant — "use functional components", "never mock the database", "we picked Riverpod over Bloc because...". Then you:

- Switch from Claude to Cursor → **context lost**
- Open the project on your laptop → **context lost**
- Start a new AI session → **context lost**
- Onboard a teammate → **they start from zero**

sesyncai captures all of this once and makes it portable.

---

## Install

```bash
pip install sesyncai
```

Requires Python 3.10 or higher.

---

## Quick Start

Just run `sesyncai` in your project directory — no commands to memorize:

```bash
cd your-project
sesyncai
```

You'll see an interactive menu:

```
┌──────────────────────────────────────────────────┐
│ sesyncai — AI context capture & sync             │
│                                                  │
│ Project directory: /your-project                 │
└──────────────────────────────────────────────────┘

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

Pick a number. That's it.

---

## What It Does

### 1. Scans your project

sesyncai reads your project files and auto-detects everything an AI assistant needs to know:

| What it captures | Where it looks |
|---|---|
| Language & framework | `pyproject.toml`, `package.json`, `pubspec.yaml`, `Cargo.toml`, `go.mod` |
| Dependencies | Lock files, manifest files |
| Build & test commands | Package manager configs, Makefiles |
| Project structure | Directory tree (filtered, ignoring noise) |
| Git remote & branch | `.git/config` |
| Runtime versions | Python version, Node version |
| Existing AI context | `CLAUDE.md`, `.cursorrules`, `.windsurfrules` |

### 2. Captures your instructions

The rules and preferences you build up while prompting AI get automatically extracted from your existing AI context files:

**Files it reads from:**

| File | Tool |
|---|---|
| `CLAUDE.md` | Claude Code |
| `.cursorrules` | Cursor |
| `.windsurfrules` | Windsurf |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `.claude/rules/*.md` | Scoped Claude rules (with path metadata) |

**What it extracts:**

sesyncai uses pattern matching to find imperative developer instructions — statements starting with words like *Always*, *Never*, *Don't*, *Must*, *Prefer*, *Avoid*, *Use*, *Keep*, *Ensure*, *Run*. It's smart about it:

- Skips code blocks (won't extract from fenced ` ``` ` sections)
- Joins multi-line bullet points into complete instructions
- Understands negation sections — rules under a `### Never` heading get automatically prefixed with "Never"
- Filters out noise (bare URLs, short fragments, code-only lines)
- Auto-categorizes each instruction into one of 7 categories

**The 7 categories:**

| Category | Examples |
|---|---|
| `constraint` | "Always validate user input", "Never store secrets in code" |
| `architecture` | "Keep business logic in the service layer" |
| `convention` | "All API routes use snake_case" |
| `style` | "Use camelCase for JavaScript variables" |
| `preference` | "Prefer composition over inheritance" |
| `decision` | "We chose Riverpod over Bloc because of testability" |
| `workflow` | "Run `pytest -v` before pushing" |

You can also add instructions manually, and sesyncai will auto-suggest the right category:

```bash
sesyncai capture "All API responses must include request_id"
# → auto-categorized as: constraint
```

### 3. Exports to any AI tool

One snapshot, multiple formats:

| Format | Command | Output file |
|---|---|---|
| Claude Code | `sesyncai export claude` | `CLAUDE.md` |
| Cursor | `sesyncai export cursor` | `.cursorrules` |
| Windsurf | `sesyncai export windsurf` | `.windsurfrules` |
| System prompt | `sesyncai export prompt` | Copied to clipboard + stdout |
| Local markdown | Interactive menu → option 7 | `yourproject-context.md` |

Each export format is optimized for its target tool — structured markdown for Claude, flat bullet points for Cursor/Windsurf, a dense paragraph for system prompts.

### 4. Syncs across machines

Push your context to a private GitHub Gist and pull it on any machine:

```bash
# Push (creates or updates a private gist)
sesyncai sync

# Pull on another machine
sesyncai load <gist-id>
```

Both your project context **and** all captured instructions are synced together. Requires the [GitHub CLI](https://cli.github.com/) authenticated: `gh auth login`.

---

## Usage

### Interactive mode (recommended)

```bash
sesyncai
```

This is the easiest way to use sesyncai. It walks you through everything with a numbered menu — scan, capture, export, sync. No commands to memorize.

### Direct commands

For scripting, CI, or power users:

```bash
# Scan & init
sesyncai init                      # scan project, save context to .sesyncai/
sesyncai init --force              # re-scan and overwrite existing context

# View context
sesyncai show                      # display captured context (YAML)
sesyncai status                    # quick summary (language, deps, instruction count)
sesyncai diff                      # check if project has changed since last scan

# Capture instructions
sesyncai capture --scan            # auto-extract from AI context files
sesyncai capture "your rule"       # add a single instruction (auto-categorized)
sesyncai capture "rule" -c style   # add with explicit category
sesyncai import notes.md           # extract instructions from any markdown file

# View & manage instructions
sesyncai instructions              # list all captured instructions in a table
sesyncai instructions --remove 3   # remove instruction #3
sesyncai instructions --clear      # clear all instructions

# Export
sesyncai export claude             # → CLAUDE.md
sesyncai export cursor             # → .cursorrules
sesyncai export windsurf           # → .windsurfrules
sesyncai export prompt             # → clipboard + stdout

# Cloud sync
sesyncai sync                      # push context + instructions to GitHub Gist
sesyncai load <gist-id>            # pull context from a gist

# Info
sesyncai --version                 # show version
```

---

## Supported Languages

| Language | Config file | Frameworks detected |
|---|---|---|
| Python | `pyproject.toml`, `setup.py`, `requirements.txt` | FastAPI, Flask, Django, Typer |
| JavaScript / TypeScript | `package.json` | Next.js, React, Vue, Express |
| Flutter / Dart | `pubspec.yaml` | Flutter |
| Rust | `Cargo.toml` | — |
| Go | `go.mod` | — |

sesyncai detects the language, framework, dependencies, build commands, and test commands from these files.

---

## How It Works

```
your-project/
├── pyproject.toml            ← sesyncai reads these
├── package.json              ←   for project context
├── .git/                     ← git remote & branch
│
├── CLAUDE.md                 ← sesyncai extracts instructions
├── .cursorrules              ←   from these AI context files
├── .windsurfrules            ←
├── .claude/rules/*.md        ←
│
└── .sesyncai/                ← sesyncai stores everything here
    ├── context.yaml          ←   project snapshot
    └── instructions.yaml     ←   captured rules & preferences
```

**Scan** → reads your project files and AI context files  
**Store** → saves to `.sesyncai/` (YAML, human-readable, git-ignorable)  
**Export** → generates the right format for each AI tool  
**Sync** → pushes to a private GitHub Gist for cross-machine use  

---

## Example Workflow

```bash
# 1. Set up context in your project
cd my-app
sesyncai

# 2. Pick "Scan this project" → captures language, deps, structure
# 3. Pick "Scan for instructions" → extracts rules from CLAUDE.md, .cursorrules
# 4. Pick "Add an instruction" → "Never use innerHTML with user content"
# 5. Pick "Export for Claude Code" → writes CLAUDE.md with everything
# 6. Pick "Sync to GitHub Gist" → saved to cloud

# Later, on your laptop:
sesyncai load abc123def456

# Or export for a different tool:
sesyncai export cursor
```

---

## Storage

Everything is stored in `.sesyncai/` inside your project:

- **`context.yaml`** — project metadata (language, framework, dependencies, structure)
- **`instructions.yaml`** — captured rules and preferences with categories

Both files are human-readable YAML. You can edit them directly, version them, or add `.sesyncai/` to your `.gitignore` to keep context local.

---

## Requirements

- Python 3.10+
- [GitHub CLI](https://cli.github.com/) (only needed for `sync` and `load` commands)

---

## License

MIT
