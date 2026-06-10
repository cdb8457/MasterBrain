"""Canonical slug registry (Phase 1.8) — derived, never committed.

The registry is built by scanning canonical pages (frontmatter
``canonical: true``) under the four canonical namespaces. The durable identity
of a subject is its **canonical_id**: the page's relative path without
``.md`` (e.g. ``concepts/team-forge``, ``projects/arcane``). A short
``canonical_slug`` (the slugified basename) is stored for display; the
canonical_id is primary (Clint's D1 correction, 2026-06-09).

Resolution rules (D2–D4, approved 2026-06-09):

- Qualified subjects (containing ``/``) resolve directly by canonical_id.
- Unqualified subjects match the normalized basename slug, ``title:``, or any
  Obsidian-style ``aliases:`` entry. Exactly one match resolves; multiple
  matches raise :class:`AmbiguousSubjectError` (e.g. ``Arcane`` when both
  ``projects/arcane`` and ``entities/arcane`` exist) — pages in different
  namespaces may share a basename; only *unqualified use* is the error.
- Normalized-identical forms (case/space/hyphen/underscore-insensitive,
  ``TeamForge`` ≡ ``Team Forge``) auto-resolve.
- Fuzzy near-misses (difflib ratio ≥ 0.85) raise :class:`NearMissError` with
  suggestions; ``force_new=True`` (CLI ``--force-new-subject``) overrides.
- Unknown subjects are accepted with a provisional, namespace-less
  canonical_id (the bare slug) and reported by the linter (accept+warn; must
  be revisited before MCP/agent-facing writes open).

This module never modifies the vault. Stdlib only.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# The four canonical namespaces (CONVENTIONS node-type → folder map).
CANONICAL_NAMESPACES = ("concepts", "entities", "components", "projects")

FUZZY_THRESHOLD = 0.85


class AmbiguousSubjectError(ValueError):
    """An unqualified subject resolves to multiple canonical pages; a
    qualified canonical_id (e.g. 'projects/arcane') is required."""


class NearMissError(ValueError):
    """The subject looks like a typo of an existing canonical page; pass
    force_new=True / --force-new-subject if it is genuinely new."""


def slugify(text: str) -> str:
    """Lowercase alphanumerics + hyphens (D4): 'Team Forge' -> 'team-forge'."""
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")


def norm_key(text: str) -> str:
    """Match key: case/space/hyphen/underscore/punctuation-insensitive,
    so 'TeamForge' ≡ 'Team Forge' ≡ 'team_forge' ≡ 'team-forge'."""
    return re.sub(r"[^a-z0-9]+", "", (text or "").lower())


# --- Minimal frontmatter parsing (simple YAML subset per CONVENTIONS) --------
# Canonical home of the parser used by both this module and lint.py.

def _split_inline_list(inner: str) -> list[str]:
    """Split 'a, "b, c", d' respecting quotes."""
    out, buf, quote = [], "", None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            out.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        out.append(buf)
    return out


def parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, bool]:
    """Parse the simple YAML subset CONVENTIONS defines (flat keys, inline
    lists, block lists). Returns (frontmatter | None, parse_ok). Read-only and
    deliberately forgiving: unparseable lines are skipped, not fatal."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, True
    fm: dict[str, Any] = {}
    ok = True
    key_for_block: str | None = None
    for line in lines[1:]:
        if line.strip() == "---":
            return fm, ok
        if not line.strip() or line.strip().startswith("#"):
            continue
        block_item = re.match(r"^\s+-\s*(.+)$", line)
        if block_item and key_for_block:
            fm.setdefault(key_for_block, [])
            if isinstance(fm[key_for_block], list):
                fm[key_for_block].append(block_item.group(1).strip().strip('"\''))
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not m:
            if not line.startswith(" "):
                ok = False
            continue
        key, raw = m.group(1), m.group(2).strip()
        key_for_block = key if raw == "" else None
        if raw == "":
            fm.setdefault(key, [])  # may become a block list
            continue
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            fm[key] = [v.strip().strip('"\'') for v in _split_inline_list(inner)] if inner else []
        elif raw.lower() in ("true", "false"):
            fm[key] = raw.lower() == "true"
        else:
            fm[key] = raw.strip('"\'')
    return fm, False  # no closing ---


# --- Registry ------------------------------------------------------------------

@dataclass
class CanonicalPage:
    canonical_id: str          # relative path without .md (durable identity)
    canonical_slug: str        # slugified basename (display)
    title: str | None
    aliases: list[str]
    path: str                  # relative path with .md


def build_registry(root: Path) -> dict[str, CanonicalPage]:
    """Scan canonical namespaces for pages with ``canonical: true``.
    Read-only. Returns {canonical_id: CanonicalPage}."""
    root = Path(root)
    registry: dict[str, CanonicalPage] = {}
    for ns in CANONICAL_NAMESPACES:
        base = root / ns
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            try:
                fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if not fm or fm.get("canonical") is not True:
                continue
            rel = p.relative_to(root).as_posix()
            cid = rel[:-3]  # strip .md
            aliases = fm.get("aliases")
            aliases = [str(a) for a in aliases] if isinstance(aliases, list) else []
            registry[cid] = CanonicalPage(
                canonical_id=cid,
                canonical_slug=slugify(p.stem),
                title=fm.get("title") if isinstance(fm.get("title"), str) else None,
                aliases=aliases,
                path=rel,
            )
    return registry


def build_key_index(registry: dict[str, CanonicalPage]) -> dict[str, set[str]]:
    """norm_key -> {canonical_id, ...} for basename slug, title, and aliases."""
    idx: dict[str, set[str]] = {}
    for cid, page in registry.items():
        keys = {norm_key(page.canonical_slug)}
        if page.title:
            keys.add(norm_key(page.title))
        for a in page.aliases:
            keys.add(norm_key(a))
        keys.discard("")
        for k in keys:
            idx.setdefault(k, set()).add(cid)
    return idx


# --- Resolution -----------------------------------------------------------------

def quiet_resolve(
    registry: dict[str, CanonicalPage],
    idx: dict[str, set[str]],
    subject: str | None,
) -> tuple[str | None, str | None, str]:
    """Read-time resolution: never raises, no fuzzy matching.
    Returns (canonical_id, canonical_slug, kind) where kind ∈
    resolved | provisional | ambiguous | empty."""
    s = (subject or "").strip()
    if not s:
        return None, None, "empty"
    if "/" in s:
        cid = s[:-3] if s.lower().endswith(".md") else s
        cid = cid.replace("\\", "/").strip("/")
        if cid in registry:
            return cid, registry[cid].canonical_slug, "resolved"
        return cid, slugify(cid.rsplit("/", 1)[-1]), "provisional"
    matches = idx.get(norm_key(s), set())
    if len(matches) == 1:
        cid = next(iter(matches))
        return cid, registry[cid].canonical_slug, "resolved"
    if len(matches) > 1:
        return None, slugify(s), "ambiguous"
    return slugify(s), slugify(s), "provisional"


def resolve_subject(
    root: Path,
    subject: str,
    force_new: bool = False,
    registry: dict[str, CanonicalPage] | None = None,
) -> dict[str, Any]:
    """Write-time resolution (D2/D3). Raises AmbiguousSubjectError or
    NearMissError; returns {canonical_id, canonical_slug, kind, matches}."""
    if registry is None:
        registry = build_registry(Path(root))
    idx = build_key_index(registry)
    s = (subject or "").strip()
    if not s:
        raise ValueError("canonical_subject must not be empty")

    if "/" in s:
        cid, slug, kind = quiet_resolve(registry, idx, s)
        return {"canonical_id": cid, "canonical_slug": slug,
                "kind": "exact-id" if kind == "resolved" else "new-qualified",
                "matches": [cid] if kind == "resolved" else []}

    matches = sorted(idx.get(norm_key(s), set()))
    if len(matches) == 1:
        cid = matches[0]
        return {"canonical_id": cid,
                "canonical_slug": registry[cid].canonical_slug,
                "kind": "resolved", "matches": matches}
    if len(matches) > 1:
        raise AmbiguousSubjectError(
            f"subject {subject!r} is ambiguous — it resolves to multiple "
            f"canonical pages: {', '.join(matches)}. Use a qualified "
            "canonical_id (e.g. 'projects/arcane' vs 'entities/arcane')."
        )

    # Fuzzy near-miss against all known keys (D3 tier b).
    close = difflib.get_close_matches(norm_key(s), list(idx.keys()), n=3,
                                      cutoff=FUZZY_THRESHOLD)
    if close and not force_new:
        suggestions = sorted({cid for k in close for cid in idx[k]})
        raise NearMissError(
            f"subject {subject!r} looks like a near-miss of existing canonical "
            f"page(s): {', '.join(suggestions)}. Use one of those, or pass "
            "--force-new-subject if this is genuinely a new subject."
        )

    # Genuinely new (or forced): provisional namespace-less id (D2 accept+warn;
    # the linter reports these as the page-creation queue).
    slug = slugify(s)
    return {"canonical_id": slug, "canonical_slug": slug,
            "kind": "new-forced" if (close and force_new) else "new",
            "matches": []}
