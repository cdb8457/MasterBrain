"""Safe attributed-note writer for the agent API (Phase 3a). Stdlib only.

The ONLY automated path that writes Markdown into the vault, and it can only
land in ``inbox/<token-agent>/`` (PROCESS.md rule 11: automated write paths
never touch canonical pages). Filenames are server-generated from a slugified
title — client-supplied paths are never used; traversal characters are
rejected; existing files are never overwritten.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .slugs import slugify
from .store import VALID_AGENTS

MAX_TITLE_CHARS = 200
MAX_BODY_CHARS = 64_000
MAX_LIST_ITEMS = 50

_FORBIDDEN = re.compile(r"[\\/\x00-\x1f]")


def _clean_list(values, label: str) -> list[str]:
    if not values:
        return []
    if len(values) > MAX_LIST_ITEMS:
        raise ValueError(f"{label}: at most {MAX_LIST_ITEMS} items")
    out = []
    for v in values:
        s = str(v).strip()
        if s and not _FORBIDDEN.search(s.replace("/", "")):  # refs may contain /
            out.append(s)
    return out


def write_agent_note(
    data_dir: Path,
    agent: str,
    title: str,
    body: str,
    source_refs: list[str] | None = None,
    links: list[str] | None = None,
    tags: list[str] | None = None,
) -> str:
    """Write one attributed draft note into inbox/<agent>/. Returns the
    vault-relative path. Raises ValueError on any invalid input."""
    if agent not in VALID_AGENTS:
        raise ValueError(f"'{agent}' is not a registered agent")
    title = (title or "").strip()
    if not title:
        raise ValueError("title is required")
    if len(title) > MAX_TITLE_CHARS:
        raise ValueError(f"title exceeds {MAX_TITLE_CHARS} characters")
    if _FORBIDDEN.search(title) or ".." in title:
        raise ValueError("title may not contain path separators, '..', or "
                         "control characters")
    body = body or ""
    if len(body) > MAX_BODY_CHARS:
        raise ValueError(f"body exceeds {MAX_BODY_CHARS} characters")

    refs = _clean_list(source_refs, "source_refs")
    lks = _clean_list(links, "links")
    tgs = [slugify(t) for t in _clean_list(tags, "tags") if slugify(t)]

    slug = slugify(title) or "note"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    folder = Path(data_dir) / "inbox" / agent
    folder.mkdir(parents=True, exist_ok=True)

    name = f"{today}-{slug}.md"
    path = folder / name
    n = 2
    while path.exists():
        if n > 99:
            raise ValueError("too many notes with this title today")
        path = folder / f"{today}-{slug}-{n}.md"
        n += 1

    fm = [
        "---",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        "type: agent-note",
        "node_type: agent_note",
        "canonical: false",
        f"agent: {agent}",
        "status: draft",
        "source_type: api-note",
        "source_refs: [" + ", ".join(json.dumps(r, ensure_ascii=False) for r in refs) + "]",
        f"created: {today}",
        f"updated: {today}",
        "tags: [" + ", ".join(tgs) + "]",
        "links: [" + ", ".join(json.dumps(l, ensure_ascii=False) for l in lks) + "]",
        "---",
        "",
        f"# {title}",
        "",
        f"*Attributed note by **{agent}**, written via the authenticated API. "
        "One perspective, not shared truth. Status `draft` - only Clint "
        "approves.*",
        "",
        body,
        "",
    ]
    path.write_text("\n".join(fm), encoding="utf-8")
    return path.relative_to(Path(data_dir)).as_posix()
