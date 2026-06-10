"""Command-line interface for the MasterBrain memory store (canonical schema).

Durable data is append-only JSONL under the mounted vault. Stdlib only.

Examples (inside the container, or locally with MASTERBRAIN_DATA_DIR set):

    python -m masterbrain init

    # Add an attributed claim about a canonical subject
    python -m masterbrain add-claim \
        --canonical-subject "Team Forge" \
        --claim "The onboarding UI uses a multi-step wizard flow" \
        --source-agent claude \
        --source-type ui-review \
        --source-ref "inbox/claude/2026-05-29-team-forge-ui-review.md" \
        --project "team-forge" \
        --confidence 0.8 \
        --evidence-level explicit \
        --approval-status draft

    python -m masterbrain list-claims --canonical-subject "Team Forge"
    python -m masterbrain get-claim --claim-id clm_xxx

    # Move a claim through the approval lifecycle (append-only review event)
    python -m masterbrain review --claim-id clm_xxx --approval-status reviewed --by clint
    python -m masterbrain review --claim-id clm_xxx --approval-status approved --by clint

    # Relationships (append-only; original record is never overwritten)
    python -m masterbrain link --claim-id clm_xxx --field supports --value clm_yyy --by-agent codex
    python -m masterbrain supersede --old-claim-id clm_old --new-claim-id clm_new --by-agent hermes

    # Edges and sources
    python -m masterbrain add-edge --from-id clm_xxx --to-id clm_yyy \
        --edge-type evidence_for --created-by-agent codex --confidence 0.6
    python -m masterbrain add-source --path "inbox/claude/2026-05-29-team-forge-ui-review.md" \
        --source-type ui-review --source-agent claude --project team-forge

    python -m masterbrain stats
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .store import (APPROVAL_STATUSES, CLAIM_REL_FIELDS, EDGE_TYPES,
                    EVIDENCE_LEVELS, GuardError, Store)


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="masterbrain",
        description="Shared External Agent Brain — provenance-aware memory CLI.",
    )
    p.add_argument(
        "--data-dir",
        default=None,
        help="Override vault data dir (else $MASTERBRAIN_DATA_DIR or /data).",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create graph-memory/ and empty JSONL files.")

    ac = sub.add_parser("add-claim", help="Append an attributed claim.")
    ac.add_argument("--canonical-subject", required=True,
                    help="Canonical node the claim is about (e.g. 'Team Forge').")
    ac.add_argument("--claim", required=True, help="The claim statement itself.")
    ac.add_argument("--source-agent", required=True,
                    help="Contributing agent (claude, codex, hermes, gpt, gemini, ...).")
    ac.add_argument("--source-type", default=None,
                    help="Kind of source (e.g. ui-review, build-notes, chat, doc).")
    ac.add_argument("--source-ref", action="append", default=[], dest="source_refs",
                    help="Source reference (path/URL/id). Repeatable.")
    ac.add_argument("--project", default=None, help="Owning project, if any.")
    ac.add_argument("--confidence", type=float, default=None, help="0.0-1.0.")
    ac.add_argument("--evidence-level", default="explicit", choices=EVIDENCE_LEVELS)
    ac.add_argument("--approval-status", default="draft", choices=APPROVAL_STATUSES)
    ac.add_argument("--force-new-subject", action="store_true",
                    help="Insist the subject is genuinely new when it looks "
                         "like a near-miss of an existing canonical page.")
    for f in CLAIM_REL_FIELDS:
        ac.add_argument(f"--{f.replace('_', '-')}", action="append", default=[], dest=f,
                        help=f"Initial {f} target (claim id or subject). Repeatable.")

    lc = sub.add_parser("list-claims", help="List current-state claims.")
    lc.add_argument("--canonical-subject", default=None)
    lc.add_argument("--approval-status", default=None, choices=APPROVAL_STATUSES)
    lc.add_argument("--project", default=None)

    gc = sub.add_parser("get-claim", help="Show one claim with folded state + history.")
    gc.add_argument("--claim-id", required=True)

    rv = sub.add_parser("review", help="Append a review that changes approval_status.")
    rv.add_argument("--claim-id", required=True)
    rv.add_argument("--approval-status", required=True, choices=APPROVAL_STATUSES)
    rv.add_argument("--by", required=True, help="Reviewer (e.g. clint).")
    rv.add_argument("--note", default=None)

    ln = sub.add_parser("link", help="Append a relationship to a claim (no overwrite).")
    ln.add_argument("--claim-id", required=True)
    ln.add_argument("--field", required=True, choices=CLAIM_REL_FIELDS)
    ln.add_argument("--value", required=True, help="Target claim id or subject.")
    ln.add_argument("--by-agent", required=True)

    sp = sub.add_parser("supersede", help="Record that one claim supersedes another.")
    sp.add_argument("--old-claim-id", required=True)
    sp.add_argument("--new-claim-id", required=True)
    sp.add_argument("--by-agent", required=True)
    sp.add_argument("--no-deprecate", action="store_true",
                    help="Do not auto-set the old claim to 'deprecated'.")

    ae = sub.add_parser("add-edge", help="Append a typed graph edge between two nodes.")
    ae.add_argument("--from-id", required=True)
    ae.add_argument("--to-id", required=True)
    ae.add_argument("--edge-type", required=True, choices=EDGE_TYPES)
    ae.add_argument("--created-by-agent", required=True)
    ae.add_argument("--confidence", type=float, default=None, help="0.0-1.0.")
    ae.add_argument("--evidence-level", default=None, choices=EVIDENCE_LEVELS)
    ae.add_argument("--source-ref", action="append", default=[], dest="source_refs",
                    help="Source reference. Repeatable.")

    asr = sub.add_parser("add-source", help="Register a raw source reference.")
    asr.add_argument("--path", required=True, help="Path/URL/id of the source.")
    asr.add_argument("--source-type", default=None)
    asr.add_argument("--source-agent", default=None)
    asr.add_argument("--title", default=None)
    asr.add_argument("--project", default=None)
    asr.add_argument("--checksum", dest="checksum_or_stable_id", default=None,
                     help="Checksum or other stable identifier.")

    sub.add_parser("stats", help="Summary counts by status, agent, evidence level.")

    lt = sub.add_parser("lint", help="Read-only reconciler: report Markdown/JSONL "
                                     "drift and convention violations. Never modifies anything.")
    lt.add_argument("--json", action="store_true", dest="as_json",
                    help="Emit the report as JSON.")

    sj = sub.add_parser("subjects", help="List the derived canonical slug "
                                         "registry (read-only).")
    sj.add_argument("--json", action="store_true", dest="as_json",
                    help="Emit the registry as JSON.")

    rs = sub.add_parser("resolve", help="Show what a subject would resolve to "
                                        "(read-only; nothing is written).")
    rs.add_argument("--subject", required=True)
    rs.add_argument("--force-new-subject", action="store_true")

    rq = sub.add_parser("review-queue",
                        help="Everything waiting on Clint's review (read-only "
                             "by default; --write emits queries/review-queue.md).")
    rq.add_argument("--json", action="store_true", dest="as_json",
                    help="Emit the queue as JSON.")
    rq.add_argument("--group-by", default="status",
                    choices=("status", "agent", "project", "canonical-id"),
                    help="Grouping for pending claims (default: status).")
    rq.add_argument("--write", action="store_true",
                    help="Create/overwrite the generated Markdown report at "
                         "queries/review-queue.md (gitignored). Nothing else "
                         "is touched.")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = Store() if args.data_dir is None else Store(data_dir=Path(args.data_dir))

    if args.cmd == "lint":
        from .lint import exit_code, lint, render_text

        report = lint(store.data_dir)
        if args.as_json:
            _print(report)
        else:
            print(render_text(report))
        return exit_code(report)

    if args.cmd == "subjects":
        from dataclasses import asdict

        from .slugs import build_registry

        registry = build_registry(store.data_dir)
        pages = [asdict(p) for p in registry.values()]
        if args.as_json:
            _print({"data_dir": str(store.data_dir), "subjects": pages})
        else:
            if not pages:
                print("No canonical pages found.")
            for p in pages:
                aliases = f" aliases={p['aliases']}" if p["aliases"] else ""
                print(f"{p['canonical_id']}  (slug: {p['canonical_slug']}; "
                      f"title: {p['title']}){aliases}")
        return 0

    if args.cmd == "resolve":
        from .slugs import resolve_subject

        try:
            _print(resolve_subject(store.data_dir, args.subject,
                                   force_new=args.force_new_subject))
            return 0
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if args.cmd == "review-queue":
        from .review_queue import build_queue, render_text, write_report

        queue = build_queue(store.data_dir)
        if args.as_json:
            _print(queue)
        else:
            print(render_text(queue, group_by=args.group_by))
        if args.write:
            path = write_report(store.data_dir, queue, group_by=args.group_by)
            print(f"\nwrote {path}", file=sys.stderr)
        return 0

    try:
        return _dispatch(args, store)
    except GuardError as exc:
        print(f"GUARD REJECTED: {exc}", file=sys.stderr)
        return 3
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _dispatch(args, store: Store) -> int:
    if args.cmd == "init":
        created = store.init()
        _print({"data_dir": str(store.data_dir), "created": [str(p) for p in created]})
    elif args.cmd == "add-claim":
        _print(store.add_claim(
            canonical_subject=args.canonical_subject,
            claim=args.claim,
            source_agent=args.source_agent,
            source_type=args.source_type,
            source_refs=args.source_refs,
            project=args.project,
            confidence=args.confidence,
            evidence_level=args.evidence_level,
            approval_status=args.approval_status,
            related_to=args.related_to,
            supports=args.supports,
            contradicts=args.contradicts,
            supersedes=args.supersedes,
            superseded_by=args.superseded_by,
            force_new_subject=args.force_new_subject,
        ))
    elif args.cmd == "list-claims":
        _print(store.claims(subject=args.canonical_subject,
                            status=args.approval_status, project=args.project))
    elif args.cmd == "get-claim":
        claim = store.get_claim(args.claim_id)
        if claim is None:
            print(f"No claim found with id {args.claim_id}", file=sys.stderr)
            return 1
        _print(claim)
    elif args.cmd == "review":
        _print(store.review_claim(args.claim_id, args.approval_status,
                                 by=args.by, note=args.note))
    elif args.cmd == "link":
        _print(store.link_claim(args.claim_id, args.field, args.value, by_agent=args.by_agent))
    elif args.cmd == "supersede":
        _print(store.supersede_claim(args.old_claim_id, args.new_claim_id,
                                    by_agent=args.by_agent, deprecate=not args.no_deprecate))
    elif args.cmd == "add-edge":
        _print(store.add_edge(args.from_id, args.to_id, args.edge_type,
                             created_by_agent=args.created_by_agent,
                             confidence=args.confidence,
                             evidence_level=args.evidence_level,
                             source_refs=args.source_refs))
    elif args.cmd == "add-source":
        _print(store.add_source(args.path, source_type=args.source_type,
                               source_agent=args.source_agent, title=args.title,
                               project=args.project,
                               checksum_or_stable_id=args.checksum_or_stable_id))
    elif args.cmd == "stats":
        _print(store.stats())
    else:  # pragma: no cover
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
