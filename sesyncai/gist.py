"""GitHub Gist sync — push and pull context + instructions via gists."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from typing import Optional

import httpx

from .model import ProjectContext
from .instructions import InstructionStore

CONTEXT_FILENAME = "sesyncai-context.yaml"
INSTRUCTIONS_FILENAME = "sesyncai-instructions.yaml"


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


def push(ctx: ProjectContext, store: Optional[InstructionStore] = None, description: str = "") -> str:
    token = _gh_token()
    if not token:
        raise RuntimeError(
            "GitHub CLI not authenticated. Run: gh auth login"
        )

    ctx.last_synced = datetime.now(timezone.utc).isoformat()
    desc = description or f"sesyncai context — {ctx.name}"

    files = {CONTEXT_FILENAME: {"content": ctx.to_yaml()}}
    if store and store.instructions:
        import yaml
        data = [{"text": i.text, "category": i.category, "source": i.source, "added": i.added}
                for i in store.instructions]
        files[INSTRUCTIONS_FILENAME] = {
            "content": yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
        }

    if ctx.gist_id:
        return _update_gist(token, ctx.gist_id, files, desc)
    else:
        gist_id = _create_gist(token, files, desc)
        ctx.gist_id = gist_id
        return gist_id


def _api_request(method: str, url: str, token: str, **kwargs) -> httpx.Response:
    try:
        resp = httpx.request(method, url, headers=_headers(token), timeout=30, **kwargs)
        resp.raise_for_status()
        return resp
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        if code == 401:
            raise RuntimeError("GitHub token expired or invalid. Run: gh auth login")
        elif code == 404:
            raise RuntimeError(f"Gist not found. Check the ID and permissions.")
        elif code == 422:
            raise RuntimeError(f"GitHub rejected the request: {e.response.text[:200]}")
        raise RuntimeError(f"GitHub API error ({code})")
    except httpx.ConnectError:
        raise RuntimeError("Cannot reach GitHub. Check your internet connection.")
    except httpx.TimeoutException:
        raise RuntimeError("GitHub request timed out. Try again.")
    except httpx.RequestError as e:
        raise RuntimeError(f"Network error: {e}")


def _create_gist(token: str, files: dict, description: str) -> str:
    resp = _api_request("POST", "https://api.github.com/gists", token, json={
        "description": description,
        "public": False,
        "files": files,
    })
    return resp.json()["id"]


def _update_gist(token: str, gist_id: str, files: dict, description: str) -> str:
    _api_request("PATCH", f"https://api.github.com/gists/{gist_id}", token, json={
        "description": description,
        "files": files,
    })
    return gist_id


def pull(gist_id: str) -> tuple[ProjectContext, InstructionStore]:
    token = _gh_token()
    if not token:
        raise RuntimeError(
            "GitHub CLI not authenticated. Run: gh auth login"
        )

    resp = _api_request("GET", f"https://api.github.com/gists/{gist_id}", token)

    data = resp.json()
    files = data.get("files", {})

    if CONTEXT_FILENAME not in files:
        raise ValueError(f"Gist {gist_id} doesn't contain {CONTEXT_FILENAME}")

    ctx = ProjectContext.from_yaml(files[CONTEXT_FILENAME]["content"])
    ctx.gist_id = gist_id

    store = InstructionStore()
    if INSTRUCTIONS_FILENAME in files:
        import yaml
        raw = yaml.safe_load(files[INSTRUCTIONS_FILENAME]["content"])
        if raw and isinstance(raw, list):
            from .instructions import Instruction
            store.instructions = [Instruction(**item) for item in raw]

    return ctx, store
