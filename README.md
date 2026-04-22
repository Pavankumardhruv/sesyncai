# sesyncai

Capture, sync, and share your AI project context across tools and machines.

Stop re-explaining your project every time you switch between Claude, Cursor, ChatGPT, or move to a new machine. `sesyncai` scans your codebase once and generates a portable context snapshot you can export, sync, and reload anywhere.

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
└── .sesyncai/
    └── context.yaml        ← generates this

sesyncai export claude  →  CLAUDE.md
sesyncai export cursor  →  .cursorrules
sesyncai sync           →  GitHub Gist (private)
```

## License

MIT
