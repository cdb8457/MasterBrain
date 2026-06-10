"""Read-only reconciler/linter for the Shared External Agent Brain (Phase 1.7).

Reports drift between the Markdown vault and the structured JSONL memory, and
violations of CONVENTIONS.md / PROCESS.md. **Never modifies anything** — no
auto-fixing, no JSONL rewriting, no Markdown mutation.

Usage:
    python -m masterbrain lint [--json]

Exit codes: 0 = clean, 1 = warnings/info only, 2 = errors found.
Stdlib only.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .slugs import (
    CANONICAL_NAMESPACES,
    build_key_index,
    build_registry,
    norm_key,
    parse_frontmatter,
    quiet_resolve,
)
from .store import (
    AGENT_ALIASES,
    APPROVAL_STATUSES,
    APPROVER,
    CLINT_ONLY_STATUSES,
    EDGE_TYPES,
    EVIDENCE_LEVELS,
    INTAKE_ONLY_AGENTS,
    VALID_AGENTS,
    Store,
)

# Directories never scanned (code, caches, generated output, VCS).
SKIP_DIRS = {".git", "app", "node_modules", "__pycache__", ".obsidian",
             "graphify-out", "templates"}

# Frontmatter `type:` values for governance/infrastructure pages that use
# `status: active` and are exempt from canonical/agent-note checks (avoids
# false positives on README-adjacent docs — spec risk R4).
GOVERNANCE_TYPES = {"governance", "schema", "handoff", "log", "index",
                    "reference", "policy", "allowlist",
                    "generated-view"}  # generated reports (e.g. review queue)

# Statuses allowed in note frontmatter (CONVENTIONS) + `active` for governance.
NOTE_STATUSES = set(APPROVAL_STATUSES) | {"active"}

# Folders whose direct content must be canonical pages (from slugs.py).
CANONICAL_DIRS = CANONICAL_NAMESPACES

# Folders holding attributed agent notes.
ATTRIBUTED_DIRS = ("inbox", "agents")

# Mojibake/encoding artifacts (D4 addition, Clint 2026-06-09): UTF-8 text that
# was decoded as cp1252/latin-1 somewhere produces these literal sequences,
# e.g. â€” (em dash), â†’ (arrow), â€œ/â€\x9d (curly quotes). Report only.
ENCODING_ARTIFACTS = ("â€", "â†", "â‚", "Ã¢", "Ã©", "Ã¨", "Ã±", "Ã¼", "Ã¶",
                      "Â·", "�")

WIKILINK_RE = re.compile(r"\[\[([^\]\[|#]+)(?:[|#][^\]]*)?\]\]")


@dataclass
class Finding:
    severity: str  # "error" | "warn" | "info"
    check: str
    location: str
    message: str


def _is_skipped(rel_parts: tuple[str, ...]) -> bool:
    return any(part in SKIP_DIRS for part in rel_parts)


# Frontmatter parsing lives in slugs.py (imported above) so the registry and
# the linter share one parser without an import cycle.


def _norm_agent_key(value: str | None) -> str | None:
    key = (value or "").lower().strip()
    return AGENT_ALIASES.get(key, key) or None


class Linter:
    """Read-only checks over the vault + JSONL memory."""

    def __init__(self, data_dir: Path):
        self.root = Path(data_dir)
        self.store = Store(data_dir=self.root)
        self.findings: list[Finding] = []
        self._canonical_titles: set[str] = set()

    # -- helpers ------------------------------------------------------------
    def add(self, severity: str, check: str, location: str, message: str) -> None:
        self.findings.append(Finding(severity, check, location, message))

    def _md_files(self) -> list[Path]:
        out = []
        for p in sorted(self.root.rglob("*.md")):
            rel = p.relative_to(self.root)
            if _is_skipped(rel.parts):
                continue
            out.append(p)
        return out

    # -- Markdown checks ------------------------------------------------------
    def collect_titles(self, files: list[Path]) -> None:
        """Resolvable wikilink targets: file stems + frontmatter titles."""
        for p in files:
            self._canonical_titles.add(p.stem.lower())
            try:
                fm, _ = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
            if fm and isinstance(fm.get("title"), str):
                self._canonical_titles.add(fm["title"].lower())

    def check_markdown(self) -> None:
        files = self._md_files()
        self.collect_titles(files)
        for p in files:
            rel = p.relative_to(self.root)
            loc = str(rel).replace("\\", "/")
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                self.add("warn", "unreadable-file", loc, f"could not read: {exc}")
                continue

            # Encoding artifacts (report-only; never auto-fix).
            for artifact in ENCODING_ARTIFACTS:
                if artifact in text:
                    n = text.count(artifact)
                    # Escape the sequence so the finding text itself never
                    # contains literal mojibake (it gets embedded in the
                    # generated review-queue report).
                    shown = artifact.encode("unicode_escape").decode("ascii")
                    self.add("warn", "encoding-artifact", loc,
                             f"contains {n}x mojibake sequence '{shown}' "
                             "(broken em-dash/arrow/quote). Report-only; "
                             "fix manually if the file is yours to edit.")

            fm, parse_ok = parse_frontmatter(text)
            in_content_dir = rel.parts and rel.parts[0] in (
                CANONICAL_DIRS + ATTRIBUTED_DIRS + ("comparisons", "queries"))

            if fm is None:
                if in_content_dir and p.name.lower() != "readme.md":
                    self.add("warn", "missing-frontmatter", loc,
                             "content note has no YAML frontmatter (CONVENTIONS).")
                continue
            if not parse_ok:
                self.add("warn", "frontmatter-unparseable", loc,
                         "frontmatter could not be fully parsed (unclosed block "
                         "or non-simple YAML); checks may be incomplete.")

            ftype = str(fm.get("type") or "").lower()
            is_governance = ftype in GOVERNANCE_TYPES
            canonical = fm.get("canonical") is True
            agent_raw = fm.get("agent")

            # Rule: canonical pages are not owned (CONVENTIONS rule 1).
            if canonical and agent_raw:
                self.add("error", "canonical-with-agent", loc,
                         f"canonical page carries agent: {agent_raw!r}; canonical "
                         "pages must have no agent field (CONVENTIONS rule 1).")

            # Rule: attributed notes require a registered agent.
            in_attributed = rel.parts and rel.parts[0] in ATTRIBUTED_DIRS
            if (ftype == "agent-note" or (in_attributed and not is_governance)) \
                    and p.name.lower() != "readme.md":
                key = _norm_agent_key(str(agent_raw) if agent_raw else None)
                if not agent_raw:
                    self.add("error", "agent-note-missing-agent", loc,
                             "attributed note has no agent: field (CONVENTIONS rule 2).")
                elif key not in VALID_AGENTS and key not in INTAKE_ONLY_AGENTS:
                    self.add("error", "agent-not-registered", loc,
                             f"agent: {agent_raw!r} is not in agents/agent-registry.md.")
                # Folder vs agent mismatch for inbox/<agent>/ and agents/<agent>/.
                if len(rel.parts) >= 2 and rel.parts[1] not in ("README.md",):
                    folder_key = _norm_agent_key(rel.parts[1])
                    if key and folder_key and folder_key != key and \
                            folder_key in (VALID_AGENTS + INTAKE_ONLY_AGENTS):
                        self.add("error", "inbox-folder-mismatch", loc,
                                 f"note sits in {rel.parts[0]}/{rel.parts[1]}/ but "
                                 f"claims agent: '{key}'.")

            # Rule: status vocabulary.
            status = fm.get("status")
            if isinstance(status, str) and status.lower() not in NOTE_STATUSES:
                self.add("warn", "status-unknown", loc,
                         f"status: {status!r} not in {sorted(NOTE_STATUSES)}.")
            if isinstance(status, str) and status.lower() == "active" and not is_governance:
                self.add("warn", "status-active-nongovernance", loc,
                         "status 'active' is reserved for governance pages.")

            # Rule: files directly under canonical dirs should be canonical.
            if rel.parts and rel.parts[0] in CANONICAL_DIRS and not is_governance \
                    and p.name.lower() != "readme.md" and not canonical:
                self.add("warn", "canonical-flag-missing", loc,
                         f"file lives under {rel.parts[0]}/ but is not "
                         "canonical: true.")

            # Wikilinks that resolve nowhere (warn — CONVENTIONS allows them as
            # "a node worth creating", so this is a report, not a violation).
            for m in WIKILINK_RE.finditer(text):
                target = m.group(1).strip().lower()
                if target and target not in self._canonical_titles:
                    self.add("warn", "wikilink-unresolved", loc,
                             f"[[{m.group(1).strip()}]] has no page yet "
                             "(allowed by CONVENTIONS; listed for visibility).")

    # -- JSONL checks ---------------------------------------------------------
    def check_jsonl(self) -> None:
        claims = self.store.claims()
        by_id = {c.get("claim_id"): c for c in claims}
        for c in claims:
            cid = c.get("claim_id") or "?"
            loc = f"graph-memory/claims.jsonl#{cid}"
            key = _norm_agent_key(c.get("source_agent"))
            if key in INTAKE_ONLY_AGENTS:
                self.add("error", "phone-authored-claim", loc,
                         "claim authored by intake-only identity 'phone' (D2).")
            elif key not in VALID_AGENTS:
                self.add("error", "claim-agent-unregistered", loc,
                         f"source_agent {c.get('source_agent')!r} not registered.")
            if c.get("approval_status") not in APPROVAL_STATUSES:
                self.add("warn", "claim-status-invalid", loc,
                         f"approval_status {c.get('approval_status')!r} not in vocab.")
            ev = c.get("evidence_level")
            if ev is not None and ev not in EVIDENCE_LEVELS:
                self.add("warn", "claim-evidence-invalid", loc,
                         f"evidence_level {ev!r} not in vocab.")
            # Elevated status must trace to a clint review event.
            if c.get("approval_status") in CLINT_ONLY_STATUSES:
                elevating = [r for r in c.get("reviews", [])
                             if r.get("approval_status") == c.get("approval_status")]
                last_by = (elevating[-1].get("by") if elevating else None)
                if _norm_agent_key(last_by) != APPROVER:
                    self.add("error", "elevated-status-not-clint", loc,
                             f"status '{c.get('approval_status')}' but the "
                             f"elevating review is by {last_by!r}, not "
                             f"'{APPROVER}' (PROCESS.md rule 10).")
            # Dangling local source_refs.
            for ref in c.get("source_refs") or []:
                if not isinstance(ref, str) or "://" in ref or ref.startswith(("http", "mailto:")):
                    continue
                if not (self.root / ref).exists():
                    self.add("warn", "dangling-source-ref", loc,
                             f"source_ref '{ref}' does not exist in the vault.")
            # Broken supersede pairs (only checkable for clm_ ids).
            for other in c.get("supersedes") or []:
                if isinstance(other, str) and other.startswith("clm_"):
                    target = by_id.get(other)
                    if target is None:
                        self.add("warn", "supersedes-missing-claim", loc,
                                 f"supersedes '{other}' but no such claim exists.")
                    elif cid not in (target.get("superseded_by") or []):
                        self.add("warn", "supersede-pair-broken", loc,
                                 f"supersedes '{other}' but the reverse "
                                 "superseded_by link is missing.")

        for e in self.store.edges():
            loc = f"graph-memory/edges.jsonl#{e.get('edge_id') or '?'}"
            key = _norm_agent_key(e.get("created_by_agent"))
            if key not in VALID_AGENTS and key != APPROVER:
                self.add("error", "edge-agent-unregistered", loc,
                         f"created_by_agent {e.get('created_by_agent')!r} not registered.")
            if e.get("edge_type") not in EDGE_TYPES:
                self.add("warn", "edge-type-invalid", loc,
                         f"edge_type {e.get('edge_type')!r} not in vocab.")

        for s in self.store.sources():
            loc = f"graph-memory/sources.jsonl#{s.get('source_id') or '?'}"
            key = _norm_agent_key(s.get("source_agent"))
            if key and key not in VALID_AGENTS and key not in INTAKE_ONLY_AGENTS \
                    and key != APPROVER:
                self.add("error", "source-agent-unregistered", loc,
                         f"source_agent {s.get('source_agent')!r} not registered.")

    # -- Subject identity checks (Phase 1.8) ----------------------------------
    def check_subjects(self) -> None:
        registry = build_registry(self.root)
        idx = build_key_index(registry)

        # Vault-level: an alias/title key shared by multiple pages is latent
        # ambiguity. Same-basename pages in different namespaces are allowed
        # (D4) — reported only as the keys that will force qualified ids.
        for key, cids in sorted(idx.items()):
            if len(cids) > 1:
                pages = sorted(cids)
                explicit_alias = any(
                    key in {norm_key(a) for a in registry[c].aliases}
                    for c in cids
                )
                sev = "warn" if explicit_alias else "info"
                self.add(sev, "shared-subject-key",
                         ", ".join(pages),
                         f"unqualified '{key}' matches multiple canonical "
                         f"pages; unqualified use is an ambiguity error at "
                         "write time — use qualified canonical_ids."
                         + (" An explicit alias is shared — likely a mistake."
                            if explicit_alias else ""))

        # Claim-level: how does each claim's stored/derived identity stand now?
        for c in self.store.claims():
            cid = c.get("claim_id") or "?"
            loc = f"graph-memory/claims.jsonl#{cid}"
            can_id = c.get("canonical_id")
            subject = c.get("canonical_subject")
            if can_id and "/" in can_id:
                if can_id not in registry:
                    self.add("warn", "orphaned-canonical-id", loc,
                             f"canonical_id '{can_id}' no longer matches any "
                             "canonical page (renamed? add the old name to "
                             "the page's aliases).")
                continue
            # Provisional (namespace-less) or unresolved identity.
            _qcid, _slug, kind = quiet_resolve(registry, idx, subject)
            if kind == "ambiguous":
                self.add("error", "ambiguous-subject", loc,
                         f"subject {subject!r} now resolves to multiple "
                         "canonical pages; re-point this claim at a qualified "
                         "canonical_id.")
            elif kind == "resolved":
                self.add("warn", "unregistered-subject", loc,
                         f"claim carries provisional id '{can_id}' but "
                         f"subject {subject!r} now resolves to "
                         f"'{_qcid}' — consider re-pointing.")
            elif can_id:
                self.add("warn", "unregistered-subject", loc,
                         f"subject {subject!r} has no canonical page yet "
                         f"(provisional id '{can_id}') — page-creation queue.")

    # -- Registry drift (D2: registry file is the human source of truth) ------
    def check_registry_drift(self) -> None:
        reg_path = self.root / "agents" / "agent-registry.md"
        loc = "agents/agent-registry.md"
        if not reg_path.exists():
            self.add("error", "registry-missing", loc,
                     "agent registry file not found; VALID_AGENTS in code has "
                     "no human source of truth to mirror.")
            return
        text = reg_path.read_text(encoding="utf-8", errors="replace")
        keys = set(re.findall(r"^\s*-\s*key:\s*([a-z0-9-]+)\s*$", text, re.M))
        if not keys:
            self.add("warn", "registry-unparseable", loc,
                     "could not parse '- key: <agent>' entries from the "
                     "structured YAML block; drift check skipped.")
            return
        code = set(VALID_AGENTS)
        missing_in_code = sorted(keys - code)
        missing_in_registry = sorted(code - keys)
        if missing_in_code:
            self.add("error", "registry-drift", loc,
                     f"registry keys missing from VALID_AGENTS in store.py: "
                     f"{missing_in_code} (D2: update the code mirror).")
        if missing_in_registry:
            self.add("error", "registry-drift", loc,
                     f"VALID_AGENTS keys missing from the registry: "
                     f"{missing_in_registry} (D2: registry is source of truth).")

    # -- run -------------------------------------------------------------------
    def run(self) -> dict[str, Any]:
        self.check_markdown()
        self.check_jsonl()
        self.check_subjects()
        self.check_registry_drift()
        counts = {"error": 0, "warn": 0, "info": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return {
            "data_dir": str(self.root),
            "findings": [asdict(f) for f in self.findings],
            "counts": counts,
            "ok": not self.findings,
        }


def lint(data_dir: Path) -> dict[str, Any]:
    return Linter(data_dir).run()


def exit_code(report: dict[str, Any]) -> int:
    if report["counts"].get("error"):
        return 2
    if report["counts"].get("warn") or report["counts"].get("info"):
        return 1
    return 0


def render_text(report: dict[str, Any]) -> str:
    lines = [f"masterbrain lint — {report['data_dir']} (read-only)"]
    if not report["findings"]:
        lines.append("OK: no findings.")
        return "\n".join(lines)
    for f in report["findings"]:
        lines.append(f"[{f['severity'].upper():5}] {f['check']}: {f['location']} — {f['message']}")
    c = report["counts"]
    lines.append(f"{c.get('error', 0)} error(s), {c.get('warn', 0)} warning(s), "
                 f"{c.get('info', 0)} info. Nothing was modified.")
    return "\n".join(lines)
