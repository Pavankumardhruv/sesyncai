# sesyncai

Capture, sync, and share your AI project context across tools and machines.

Stop re-explaining your project every time you switch between Claude, Cursor, ChatGPT, or move to a new machine. `sesyncai` scans your codebase once, captures your developer instructions, and generates a portable context snapshot you can export, sync, and reload anywhere.

## Install

```bash
pip install sesyncai
```

## Quick start

```bash
# scan your project
sesyncai init

# see what was captured
sesyncai show

# export for Claude Code
sesyncai export claude    # → CLAUDE.md

# export for Cursor
sesyncai export cursor    # → .cursorrules

# export as a system prompt (paste into any AI)
sesyncai export prompt

# sync to GitHub Gist (requires gh auth)
sesyncai sync

# load on another machine
sesyncai load <gist-id>

# capture instructions as you work
sesyncai capture "Always use snake_case for API routes" -c style
sesyncai capture "Never mock the database in tests" -c constraint

# auto-extract rules from existing AI context files
sesyncai capture --scan

# view captured instructions
sesyncai instructions

# check if context drifted
sesyncai diff
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
| System prompt | `sesyncai export prompt` | Printed to stdout |

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
├── pyproject.toml          ← sesyncai reads this
├── package.json            ← and this
├── .git/                   ← and this
├── CLAUDE.md               ← extracts instructions from this
├── .cursorrules            ← and this
└── .sesyncai/
    ├── context.yaml        ← project snapshot
    └── instructions.yaml   ← captured rules & preferences

sesyncai export claude  →  CLAUDE.md (with instructions)
sesyncai export cursor  →  .cursorrules (with instructions)
sesyncai sync           →  GitHub Gist (private)
```

## License

MIT
