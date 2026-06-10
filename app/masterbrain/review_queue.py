"""Review queue (Phase 1.9) — everything waiting on Clint, in one view.

Aggregation only: reuses ``Store.claims()`` and the existing ``Linter``. No new
state, no schema changes, no review actions (approval still happens via
``python -m masterbrain review --by clint``).

Surfaces (approved D1–D5, 2026-06-09):
- CLI: ``python -m masterbrain review-queue`` (read-only; ``--json``;
  ``--group-by status|agent|project|canonical-id``).
- ``--write`` (and only ``--write``) creates/overwrites the single generated
  report ``queries/review-queue.md`` — plain Markdown, no plugins, clearly
  banner-marked, gitignored (claim text is private, PROCESS.md rule 14).

Sections: draft/proposed claims, contested claims, unregistered subjects
(page-creation queue), orphan notes (unlinked; linked-but-claimless is
informational), and actionable lint findings. Stdlib only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .lint import Linter
from .slugs import parse_frontmatter
from .store import Store

REPORT_RELPATH = "queries/review-queue.md"

PENDING_STATUSES = ("draft", "proposed")

# D5: lint findings that count as "needs review": every error, plus these
# actionable warning checks. wikilink-unresolved is excluded as
# CONVENTIONS-sanctioned documentation noise.
ACTIONABLE_WARN_CHECKS = {
    "unregistered-subject",
    "orphaned-canonical-id",
    "dangling-source-ref",
    "shared-subject-key",   # included when warn (= explicit alias shared)
    "encoding-artifact",
}
EXCLUDED_CHECKS = {"wikilink-unresolved"}

GROUP_KEYS = {
    "status": lambda c: c.get("approval_status") or "unknown",
    "agent": lambda c: c.get("source_agent") or "unknown",
    "project": lambda c: c.get("project") or "(no project)",
    "canonical-id": lambda c: c.get("canonical_id") or "(unresolved)",
}

ATTRIBUTED_DIRS = ("inbox", "agents")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _age_days(created_at: str | None) -> int | None:
    if not created_at:
        return None
    try:
        dt = datetime.strptime(created_at[:19], "%Y-%m-%dT%H:%M:%S")
        return max(0, (datetime.now(timezone.utc).replace(tzinfo=None) - dt).days)
    except ValueError:
        return None


def _slim(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_id": c.get("claim_id"),
        "canonical_subject": c.get("canonical_subject"),
        "canonical_id": c.get("canonical_id"),
        "project": c.get("project"),
        "source_agent": c.get("source_agent"),
        "approval_status": c.get("approval_status"),
        "evidence_level": c.get("evidence_level"),
        "claim": c.get("claim"),
        "source_refs": c.get("source_refs") or [],
        "created_at": c.get("created_at"),
        "age_days": _age_days(c.get("created_at")),
    }


def _scan_notes(root: Path) -> list[dict[str, Any]]:
    """Attributed notes under inbox/<agent>/ and agents/<agent>/ (read-only)."""
    notes = []
    for top in ATTRIBUTED_DIRS:
        base = root / top
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name.lower() == "readme.md":
                continue
            rel = p.relative_to(root).as_posix()
            # Attributed notes live in inbox/<agent>/ and agents/<agent>/ —
            # files directly under the top dir (e.g. agents/agent-registry.md)
            # are registry/governance, not notes.
            if len(rel.split("/")) < 3:
                continue
            try:
                fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            fm = fm or {}
            links = []
            for key in ("links", "canonical_links"):
                v = fm.get(key)
                if isinstance(v, list):
                    links.extend(str(x) for x in v)
            notes.append({
                "path": rel,
                "title": fm.get("title") if isinstance(fm.get("title"), str) else p.stem,
                "agent": fm.get("agent"),
                "status": fm.get("status"),
                "links": links,
            })
    return notes


def build_queue(data_dir: Path) -> dict[str, Any]:
    """Build the queue model. Read-only."""
    root = Path(data_dir)
    store = Store(data_dir=root)
    claims = store.claims()

    pending = [_slim(c) for c in claims
               if c.get("approval_status") in PENDING_STATUSES]
    contested = [_slim(c) for c in claims
                 if c.get("approval_status") == "contested"]

    # Unregistered subjects: provisional (namespace-less) canonical_id.
    unregistered: dict[str, dict[str, Any]] = {}
    for c in claims:
        cid = c.get("canonical_id")
        if cid and "/" not in cid:
            u = unregistered.setdefault(cid, {"provisional_id": cid,
                                              "subjects": set(), "claims": 0})
            u["claims"] += 1
            if c.get("canonical_subject"):
                u["subjects"].add(c["canonical_subject"])
    unregistered_list = [
        {**u, "subjects": sorted(u["subjects"])}
        for u in (unregistered[k] for k in sorted(unregistered))
    ]

    # Orphan notes (D2): unlinked vs linked-but-claimless (informational).
    all_refs: set[str] = set()
    for c in claims:
        for r in c.get("source_refs") or []:
            if isinstance(r, str):
                all_refs.add(r.replace("\\", "/").lstrip("./"))
    notes = _scan_notes(root)
    unlinked = [n for n in notes if not n["links"]]
    claimless = [n for n in notes if n["links"] and n["path"] not in all_refs]

    # Lint findings per D5 (reuse the Linter — no reimplementation).
    lint_report = Linter(root).run()
    findings = [
        f for f in lint_report["findings"]
        if f["check"] not in EXCLUDED_CHECKS
        and (f["severity"] == "error" or f["check"] in ACTIONABLE_WARN_CHECKS)
    ]

    return {
        "data_dir": str(root),
        "generated_at": _now_iso(),
        "summary": {
            "pending_claims": len(pending),
            "contested_claims": len(contested),
            "unregistered_subjects": len(unregistered_list),
            "unlinked_notes": len(unlinked),
            "claimless_notes": len(claimless),
            "lint_findings": len(findings),
        },
        "pending_claims": pending,
        "contested_claims": contested,
        "unregistered_subjects": unregistered_list,
        "orphan_notes": {"unlinked": unlinked, "claimless": claimless},
        "lint_findings": findings,
    }


def group_claims(claims: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    fn = GROUP_KEYS[key]
    out: dict[str, list[dict[str, Any]]] = {}
    for c in claims:
        out.setdefault(fn(c), []).append(c)
    return {k: out[k] for k in sorted(out)}


# --- Rendering -----------------------------------------------------------------

def _claim_table(claims: list[dict[str, Any]]) -> list[str]:
    lines = ["| claim_id | canonical_id | subject | agent | project | status | age (d) | claim |",
             "|---|---|---|---|---|---|---|---|"]
    for c in claims:
        text = (c.get("claim") or "").replace("|", "\\|").replace("\n", " ")
        if len(text) > 100:
            text = text[:97] + "..."
        lines.append(
            f"| `{c['claim_id']}` | `{c.get('canonical_id') or '—'}` "
            f"| {c.get('canonical_subject') or ''} | {c.get('source_agent') or ''} "
            f"| {c.get('project') or ''} | {c.get('approval_status')} "
            f"| {c.get('age_days') if c.get('age_days') is not None else ''} | {text} |")
    return lines


def render_text(queue: dict[str, Any], group_by: str = "status") -> str:
    s = queue["summary"]
    lines = [f"review-queue — {queue['data_dir']} (read-only view, "
             f"generated {queue['generated_at']})",
             f"pending: {s['pending_claims']}  contested: {s['contested_claims']}  "
             f"unregistered subjects: {s['unregistered_subjects']}  "
             f"unlinked notes: {s['unlinked_notes']}  "
             f"claimless notes (info): {s['claimless_notes']}  "
             f"lint findings: {s['lint_findings']}", ""]
    if queue["pending_claims"]:
        lines.append(f"# Claims awaiting review, by {group_by}")
        for grp, items in group_claims(queue["pending_claims"], group_by).items():
            lines.append(f"## {grp} ({len(items)})")
            for c in items:
                lines.append(f"  {c['claim_id']}  [{c.get('source_agent')}] "
                             f"{c.get('canonical_id') or c.get('canonical_subject')}: "
                             f"{(c.get('claim') or '')[:80]}")
    if queue["contested_claims"]:
        lines.append("# Contested")
        for c in queue["contested_claims"]:
            lines.append(f"  {c['claim_id']}  [{c.get('source_agent')}] "
                         f"{(c.get('claim') or '')[:80]}")
    if queue["unregistered_subjects"]:
        lines.append("# Unregistered subjects (page-creation queue)")
        for u in queue["unregistered_subjects"]:
            lines.append(f"  {u['provisional_id']}  claims={u['claims']}  "
                         f"subjects={', '.join(u['subjects'])}")
    on = queue["orphan_notes"]
    if on["unlinked"]:
        lines.append("# Orphan notes — unlinked")
        for n in on["unlinked"]:
            lines.append(f"  {n['path']}  [{n.get('agent')}]")
    if on["claimless"]:
        lines.append("# Orphan notes — linked but claimless (informational)")
        for n in on["claimless"]:
            lines.append(f"  {n['path']}  [{n.get('agent')}]")
    if queue["lint_findings"]:
        lines.append("# Lint findings needing review")
        for f in queue["lint_findings"]:
            lines.append(f"  [{f['severity'].upper()}] {f['check']}: "
                         f"{f['location']} — {f['message']}")
    if not any((queue["pending_claims"], queue["contested_claims"],
                queue["unregistered_subjects"], on["unlinked"], on["claimless"],
                queue["lint_findings"])):
        lines.append("Queue is empty — nothing is waiting on review.")
    return "\n".join(lines)


def render_markdown(queue: dict[str, Any], group_by: str = "status") -> str:
    """The generated report. Plain Markdown, standard relative links only (no
    wikilinks, so the report itself never creates lint findings)."""
    s = queue["summary"]
    out = [
        "---",
        'title: "Review Queue (generated)"',
        "type: generated-view",
        "canonical: false",
        "status: active",
        f"generated_at: {queue['generated_at']}",
        'generated_by: "python -m masterbrain review-queue --write"',
        "---",
        "",
        "# Review Queue",
        "",
        "> **GENERATED — do not edit by hand.** This file is overwritten on",
        "> every run. Regenerate with `python -m masterbrain review-queue",
        f"> --write`. Generated **{queue['generated_at']}**.",
        "",
        "## Summary",
        "",
        "| Pending claims | Contested | Unregistered subjects | Unlinked notes | Claimless notes (info) | Lint findings |",
        "|---|---|---|---|---|---|",
        f"| {s['pending_claims']} | {s['contested_claims']} | "
        f"{s['unregistered_subjects']} | {s['unlinked_notes']} | "
        f"{s['claimless_notes']} | {s['lint_findings']} |",
        "",
    ]
    out.append(f"## Claims awaiting review (draft/proposed), by {group_by}")
    out.append("")
    if queue["pending_claims"]:
        for grp, items in group_claims(queue["pending_claims"], group_by).items():
            out.append(f"### {grp} ({len(items)})")
            out.append("")
            out.extend(_claim_table(items))
            out.append("")
        out.append("Approve/contest via: "
                   "`python -m masterbrain review --claim-id <id> "
                   "--approval-status <status> --by clint`")
    else:
        out.append("*None.*")
    out.append("")
    out.append("## Contested claims")
    out.append("")
    if queue["contested_claims"]:
        out.extend(_claim_table(queue["contested_claims"]))
    else:
        out.append("*None.*")
    out.append("")
    out.append("## Unregistered subjects (page-creation queue)")
    out.append("")
    if queue["unregistered_subjects"]:
        out.append("| provisional id | claims | subject spellings |")
        out.append("|---|---|---|")
        for u in queue["unregistered_subjects"]:
            out.append(f"| `{u['provisional_id']}` | {u['claims']} | "
                       f"{', '.join(u['subjects'])} |")
        out.append("")
        out.append("Create the canonical page under `concepts/`, `entities/`, "
                   "`components/`, or `projects/` to register the subject.")
    else:
        out.append("*None.*")
    out.append("")
    out.append("## Orphan notes")
    out.append("")
    on = queue["orphan_notes"]
    out.append("### Unlinked (no canonical links)")
    out.append("")
    if on["unlinked"]:
        for n in on["unlinked"]:
            out.append(f"- [{n['title']}]({n['path']}) — agent: "
                       f"`{n.get('agent') or '?'}`, status: {n.get('status')}")
    else:
        out.append("*None.*")
    out.append("")
    out.append("### Linked but claimless (informational pre-Phase-2)")
    out.append("")
    if on["claimless"]:
        for n in on["claimless"]:
            out.append(f"- [{n['title']}]({n['path']}) — agent: "
                       f"`{n.get('agent') or '?'}`, status: {n.get('status')}")
    else:
        out.append("*None.*")
    out.append("")
    out.append("## Lint findings needing review")
    out.append("")
    if queue["lint_findings"]:
        out.append("| severity | check | location | message |")
        out.append("|---|---|---|---|")
        for f in queue["lint_findings"]:
            msg = f["message"].replace("|", "\\|")
            out.append(f"| {f['severity']} | `{f['check']}` | "
                       f"`{f['location']}` | {msg} |")
    else:
        out.append("*None.*")
    out.append("")
    return "\n".join(out)


def write_report(data_dir: Path, queue: dict[str, Any],
                 group_by: str = "status") -> Path:
    """Create/overwrite the single generated report (D3). Touches nothing else."""
    path = Path(data_dir) / REPORT_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(queue, group_by), encoding="utf-8")
    return path
