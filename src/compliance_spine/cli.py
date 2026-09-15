"""Command-line interface for the compliance spine."""

from __future__ import annotations

import argparse

import yaml

from compliance_spine.config import paths
from compliance_spine.intent import IntentRegistry, validate_traceability


def _cmd_intent(_args: argparse.Namespace) -> int:
    registry = IntentRegistry.load()
    for r in registry.rules:
        owner = r.owner or "(unassigned)"
        enforced = ", ".join(r.enforced_by) or "—"
        print(f"[{r.rank}] {r.slug}: {r.title}")
        print(f"      owner={owner}  enforced_by={enforced}")
    return 0


def _cmd_doctor(_args: argparse.Namespace) -> int:
    registry = IntentRegistry.load()
    gate_config = yaml.safe_load(paths().gate_config.read_text(encoding="utf-8")) or {}
    findings = validate_traceability(registry, gate_config)
    if not findings:
        print("doctor: intent <-> gate traceability OK.")
        return 0
    errors = 0
    for f in findings:
        print(f"{f.level.upper()}: [{f.code}] {f.message}")
        errors += f.level == "error"
    print(f"\ndoctor: {len(findings)} finding(s), {errors} error(s).")
    return 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compliance-spine",
        description="ISEE compliance spine — GDPR + EU AI Act controls for agentic delivery.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("intent", help="list the never-delegate rules (Intent)").set_defaults(
        func=_cmd_intent
    )
    sub.add_parser("doctor", help="validate intent <-> gate traceability").set_defaults(
        func=_cmd_doctor
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
