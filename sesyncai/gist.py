"""GitHub Gist sync — push and pull context via gists."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import httpx

from .model import ProjectContext

GIST_FILENAME = "sesyncai-context.yaml"


def _gh_token() -> Optional[str]:
    try:
        r = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def push(ctx: ProjectContext, description: str = "") -> str:
    token = _gh_token()
    if not token:
        raise RuntimeError(
            "GitHub CLI not authenticated. Run: gh auth login"
        )

    ctx.last_synced = datetime.now(timezone.utc).isoformat()
    content = ctx.to_yaml()
    desc = description or f"sesyncai context — {ctx.name}"

    if ctx.gist_id:
        return _update_gist(token, ctx.gist_id, content, desc)
    else:
        gist_id = _create_gist(token, content, desc)
        ctx.gist_id = gist_id
        return gist_id


def _create_gist(token: str, content: str, description: str) -> str:
    resp = httpx.post(
        "https://api.github.com/gists",
        headers=_headers(token),
        json={
            "description": description,
            "public": False,
            "files": {GIST_FILENAME: {"content": content}},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def _update_gist(token: str, gist_id: str, content: str, description: str) -> str:
    resp = httpx.patch(
        f"https://api.github.com/gists/{gist_id}",
        headers=_headers(token),
        json={
            "description": description,
            "files": {GIST_FILENAME: {"content": content}},
        },
        timeout=30,
    )
    resp.raise_for_status()
    return gist_id


def pull(gist_id: str) -> ProjectContext:
    token = _gh_token()
    if not token:
        raise RuntimeError(
            "GitHub CLI not authenticated. Run: gh auth login"
        )

    resp = httpx.get(
        f"https://api.github.com/gists/{gist_id}",
        headers=_headers(token),
        timeout=30,
    )
    resp.raise_for_status()

    data = resp.json()
    files = data.get("files", {})

    if GIST_FILENAME not in files:
        raise ValueError(f"Gist {gist_id} doesn't contain {GIST_FILENAME}")

    content = files[GIST_FILENAME]["content"]
    ctx = ProjectContext.from_yaml(content)
    ctx.gist_id = gist_id
    return ctx
