"""Command-line interface for the compliance spine.

Subcommands map onto the ISEE loop:
  intent    — list the never-delegate rules (Intent)
  doctor    — check every gate traces to a principle (Structure serves Intent)
  check     — run the fail-closed gates over a change and emit Evidence (Structure + Execution)
  override  — a human silences a blocking gate for a bounded window (human-in-the-loop)
  evidence  — show recent Evidence records
  verify    — verify the Evidence hash-chain (tamper detection)
  ghosts    — find consequential decisions with no named human owner
  eval      — run the ZAVA suite proving the gates work
"""

from __future__ import annotations

import argparse

import yaml

from compliance_spine.agents import (
    AiActBaselineAgent,
    CodingAdvisorAgent,
    QualityReviewerAgent,
    TestAuthorAgent,
)
from compliance_spine.change import Change
from compliance_spine.config import paths
from compliance_spine.diagnostics import diagnose
from compliance_spine.evidence.detector import scan
from compliance_spine.evidence.ledger import Ledger
from compliance_spine.gates.runner import enforce
from compliance_spine.governance import export_change, governance_report
from compliance_spine.intent import IntentRegistry, validate_traceability
from compliance_spine.overrides import OverrideStore
from compliance_spine.zava import run as zava_run


def _cmd_intent(_a: argparse.Namespace) -> int:
    for r in IntentRegistry.load().rules:
        print(f"[{r.rank}] {r.slug}: {r.title}")
        enforced = ", ".join(r.enforced_by) or "—"
        print(f"      owner={r.owner or '(unassigned)'}  enforced_by={enforced}")
    return 0


def _cmd_doctor(_a: argparse.Namespace) -> int:
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


def _cmd_check(a: argparse.Namespace) -> int:
    change = Change.from_json_file(a.change)
    result = enforce(change, phase=a.phase, overrides=OverrideStore())
    print(result.summary())
    return 0 if result.allowed else 1


def _cmd_propose(a: argparse.Namespace) -> int:
    from compliance_spine.proposals import propose

    change = Change.from_json_file(a.change)
    preview = propose(change, model_ref=a.model)
    print(f"advisory LLM proposal recorded: {preview.proposal_id} (model={a.model}) — NON-BINDING")
    if preview.proposed_metadata:
        import json

        print(f"proposed metadata: {json.dumps(preview.proposed_metadata)}")
    else:
        print("proposed metadata: (none — put the LLM's draft in the change's "
              "'proposed_metadata' block)")
    print("\nPREVIEW — what the gates would say if a human confirms this metadata:")
    print(preview.result.summary())
    print("\nThis is advisory only. To make it binding, a human moves proposed_metadata -> "
          "metadata and runs 'check'.")
    return 0


def _cmd_override(a: argparse.Namespace) -> int:
    from compliance_spine import human

    change = Change.from_json_file(a.change)
    signers = dict(s.split(":", 1) for s in a.signer)
    try:
        record = human.request_override(
            change,
            a.gate,
            reason=a.reason,
            signers=signers,
            signature=a.signature,
            days=a.days,
            compensating_control=a.compensating_control,
        )
    except (human.PolicyError, KeyError) as exc:
        print(f"override rejected: {exc}")
        return 1
    print(f"override recorded: {record['id']} (gate '{a.gate}', "
          f"expires {record['override']['expires']})")
    return 0


def _cmd_evidence(a: argparse.Namespace) -> int:
    records = Ledger().read_all()
    if not records:
        print("evidence: ledger is empty.")
        return 0
    for rec in records[-a.limit :]:
        actor = rec.get("actor", {})
        owner = (rec.get("owner") or {}).get("human_id", "")
        subject = rec.get("subject", {})
        print(
            f"{rec['id']}  {rec['ts']}  {rec['action']:9} {rec['severity']:8} "
            f"{actor.get('type')}:{actor.get('id')}  {rec['rule_id']}  "
            f"change={subject.get('change')}"
            + (f"  owner={owner}" if owner else "")
        )
    return 0


def _cmd_verify(_a: argparse.Namespace) -> int:
    result = Ledger().verify()
    if result.ok:
        print(f"verify: OK — {result.count} record(s), chain intact.")
        return 0
    print(f"verify: FAILED — {result.count} record(s), {len(result.errors)} error(s):")
    for e in result.errors:
        print(f"  - {e}")
    return 1


def _cmd_ghosts(_a: argparse.Namespace) -> int:
    findings = scan(Ledger())
    if not findings:
        print("ghosts: none — every consequential decision has a named human owner.")
        return 0
    print(f"ghosts: {len(findings)} decision(s) without a named human owner:")
    for g in findings:
        print(f"  - {g.render()}")
    return 1


def _cmd_eval(a: argparse.Namespace) -> int:
    thresholds = {}
    if a.recall_min is not None:
        thresholds["recall_min"] = a.recall_min
    if a.fpr_max is not None:
        thresholds["fpr_max"] = a.fpr_max
    report = zava_run(thresholds=thresholds or None)
    print(report.summary())
    return 0 if report.passed else 1


def _cmd_advise(a: argparse.Namespace) -> int:
    result = CodingAdvisorAgent().run(Change.from_json_file(a.change))
    print(result.render())
    return 0


def _cmd_tests(a: argparse.Namespace) -> int:
    result = TestAuthorAgent().run(Change.from_json_file(a.change))
    print(result.render())
    if a.emit_stubs:
        for code in result.detail["stubs"].values():
            print("\n" + code)
    return 0


def _cmd_review(a: argparse.Namespace) -> int:
    result = QualityReviewerAgent().run(Change.from_json_file(a.change), ledger=Ledger())
    print(result.render())
    return 0 if result.ok else 1


def _cmd_ai_act(a: argparse.Namespace) -> int:
    result = AiActBaselineAgent().run(Change.from_json_file(a.change), ledger=Ledger())
    print(result.render())
    return 0 if result.ok else 1


def _cmd_scan_diff(a: argparse.Namespace) -> int:
    from compliance_spine.gates.registry import code_scanning_gate_names
    from compliance_spine.gitdiff import collect_change

    if a.base:
        change = collect_change(staged=False, base=a.base, head=a.head)
    else:
        change = collect_change(staged=True)
    if not change.files:
        print("scan-diff: no changed text files to scan.")
        return 0
    result = enforce(change, emit_evidence=False, only=code_scanning_gate_names())
    print(result.summary())
    return 0 if result.allowed else 1


def _cmd_llm_review(a: argparse.Namespace) -> int:
    from compliance_spine.evidence.ledger import Ledger
    from compliance_spine.llm import LayeredReviewer

    if a.base is not None or a.staged:
        from compliance_spine.gitdiff import collect_change

        change = collect_change(staged=a.staged, base=a.base, head=a.head)
        if not change.files:
            print("llm-review: no changed text files to review.")
            return 0
    elif a.change:
        change = Change.from_json_file(a.change)
    else:
        print("llm-review: provide a change JSON path, or --base <ref> / --staged for a git diff.")
        return 2
    result = LayeredReviewer().review(change, ledger=Ledger())
    print(result.summary())
    return 0 if result.allowed else 1


def _cmd_scorecard(_a: argparse.Namespace) -> int:
    from compliance_spine.llm.scorecard import score

    report = score()
    print(report.render())
    # The augmentation must lift recall without raising false positives.
    ok = report.augmented.false_positive_rate <= report.baseline.false_positive_rate
    return 0 if ok else 1


def _cmd_assess_eval(a: argparse.Namespace) -> int:
    from compliance_spine.llm.assessor_eval import evaluate

    thresholds = {}
    if a.recall_min is not None:
        thresholds["recall_min"] = a.recall_min
    if a.fpr_max is not None:
        thresholds["fpr_max"] = a.fpr_max
    report = evaluate(thresholds=thresholds or None)
    print(report.render())
    return 0 if report.passed else 1


def _cmd_adjudicate(a: argparse.Namespace) -> int:
    from compliance_spine.learning import adjudicate

    try:
        record = adjudicate(
            a.finding_id, a.outcome, human_id=a.human, signature=a.signature, reason=a.reason
        )
    except (KeyError, ValueError) as exc:
        print(f"adjudicate: {exc}")
        return 1
    print(f"adjudication recorded: {record['id']} — {a.outcome} by {a.human}")
    return 0


def _cmd_learn(_a: argparse.Namespace) -> int:
    from compliance_spine.learning import learning_report

    print(learning_report().render())
    return 0


def _cmd_diagnose(a: argparse.Namespace) -> int:
    diag = diagnose(run_evals=not a.no_evals)
    print(diag.render())
    return 0 if diag.healthy else 1


def _cmd_matrix(a: argparse.Namespace) -> int:
    from compliance_spine.matrix import build_matrix

    matrix = build_matrix(framework=a.framework)
    print(matrix.to_json() if a.json else matrix.render_markdown())
    return 0


def _cmd_frameworks(_a: argparse.Namespace) -> int:
    from compliance_spine.frameworks import render

    print(render())
    return 0


def _cmd_init(a: argparse.Namespace) -> int:
    from compliance_spine.scaffold import next_steps, scaffold_spine

    root = a.path
    written = scaffold_spine(root, force=a.force)
    if not written:
        print(
            f"init: a spine already exists under {root} (nothing written). "
            "Re-run with --force to overwrite the starter templates."
        )
        return 0
    for rel in written:
        print(f"  + {rel}")
    print()
    print(next_steps(root))
    return 0


def _cmd_governance(_a: argparse.Namespace) -> int:
    report = governance_report()
    print("Governance report")
    print(f"  intent owners unassigned: {report['intent_owners_unassigned'] or 'none'}")
    print(f"  active overrides: {len(report['active_overrides'])}")
    for ov in report["active_overrides"]:
        print(f"      - {ov['gate']} until {ov['expires']} ({', '.join(ov['signed_by'])})")
    if report["expiring_overrides"]:
        print(f"  expiring soon: {', '.join(report['expiring_overrides'])}")
    status = "OK" if report["ledger_ok"] else "BROKEN"
    print(f"  ledger: {status} ({report['ledger_count']} records)")
    print(f"  ghost decisions: {report['ghosts'] or 'none'}")
    return 0 if (report["ledger_ok"] and not report["ghosts"]) else 1


def _cmd_export(a: argparse.Namespace) -> int:
    bundle = export_change(a.change_id, out=a.out)
    print(f"exported {bundle['count']} record(s) for change '{a.change_id}'"
          + (f" -> {a.out}" if a.out else ""))
    if not a.out:
        import json

        print(json.dumps(bundle, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compliance-spine",
        description="ISEE compliance spine — GDPR + EU AI Act controls for agentic delivery.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init", help="scaffold a starter spine/ policy folder into a repo (run this first)"
    )
    p_init.add_argument("path", nargs="?", default=".", help="target repo root (default: cwd)")
    p_init.add_argument(
        "--force", action="store_true", help="overwrite existing starter templates"
    )
    p_init.set_defaults(func=_cmd_init)

    sub.add_parser("intent", help="list the never-delegate rules").set_defaults(func=_cmd_intent)
    sub.add_parser("doctor", help="validate intent <-> gate traceability").set_defaults(
        func=_cmd_doctor
    )

    p_check = sub.add_parser("check", help="run gates over a change (JSON) and emit evidence")
    p_check.add_argument("change", help="path to a change JSON file")
    p_check.add_argument("--phase", choices=["build", "run"], default="build")
    p_check.set_defaults(func=_cmd_check)

    p_prop = sub.add_parser(
        "propose", help="record an advisory LLM metadata proposal + non-binding preview"
    )
    p_prop.add_argument("change", help="change JSON with a 'proposed_metadata' block")
    p_prop.add_argument("--model", default="copilot", help="model/prompt reference for the record")
    p_prop.set_defaults(func=_cmd_propose)

    p_ov = sub.add_parser("override", help="silence a blocking gate for a bounded window")
    p_ov.add_argument("change", help="path to a change JSON file")
    p_ov.add_argument("gate", help="gate name to silence")
    p_ov.add_argument("--reason", required=True)
    p_ov.add_argument("--signer", action="append", default=[], metavar="ROLE:PERSON", required=True)
    p_ov.add_argument("--signature", required=True)
    p_ov.add_argument("--days", type=int, default=None)
    p_ov.add_argument("--compensating-control", dest="compensating_control", default=None)
    p_ov.set_defaults(func=_cmd_override)

    p_ev = sub.add_parser("evidence", help="show recent evidence records")
    p_ev.add_argument("--limit", type=int, default=20)
    p_ev.set_defaults(func=_cmd_evidence)

    sub.add_parser("verify", help="verify the evidence hash-chain").set_defaults(func=_cmd_verify)
    sub.add_parser("ghosts", help="find decisions with no named human owner").set_defaults(
        func=_cmd_ghosts
    )

    p_eval = sub.add_parser("eval", help="run the ZAVA compliance eval suite")
    p_eval.add_argument("--recall-min", dest="recall_min", type=float, default=None)
    p_eval.add_argument("--fpr-max", dest="fpr_max", type=float, default=None)
    p_eval.set_defaults(func=_cmd_eval)

    p_advise = sub.add_parser("advise", help="coding-advisor: GDPR/AI-Act remediation guidance")
    p_advise.add_argument("change")
    p_advise.set_defaults(func=_cmd_advise)

    p_tests = sub.add_parser("tests", help="test-author: recommend compliance tests")
    p_tests.add_argument("change")
    p_tests.add_argument("--emit-stubs", action="store_true", help="print generated test stubs")
    p_tests.set_defaults(func=_cmd_tests)

    p_review = sub.add_parser("review", help="quality-reviewer: verdict + evidence")
    p_review.add_argument("change")
    p_review.set_defaults(func=_cmd_review)

    p_aiact = sub.add_parser("ai-act", help="ai-act-baseline: risk tier + obligations checklist")
    p_aiact.add_argument("change")
    p_aiact.set_defaults(func=_cmd_ai_act)

    p_diag = sub.add_parser("diagnose", help="ISEE coverage & maturity diagnostic")
    p_diag.add_argument("--no-evals", action="store_true", help="skip running ZAVA")
    p_diag.set_defaults(func=_cmd_diagnose)

    p_mx = sub.add_parser("matrix", help="compliance matrix: article -> gate -> coverage status")
    p_mx.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    p_mx.add_argument("--framework", help="filter to one framework pack (e.g. gdpr, eu-ai-act)")
    p_mx.set_defaults(func=_cmd_matrix)

    sub.add_parser(
        "frameworks", help="list regulatory framework packs and their gate coverage"
    ).set_defaults(func=_cmd_frameworks)

    p_sd = sub.add_parser(
        "scan-diff", help="run the code-scanning gates over the git diff (pre-commit / CI)"
    )
    p_sd.add_argument("--staged", action="store_true", help="scan the staged diff (default)")
    p_sd.add_argument("--base", default=None, help="scan base..head instead of the staged diff")
    p_sd.add_argument("--head", default="HEAD")
    p_sd.set_defaults(func=_cmd_scan_diff)

    p_lr = sub.add_parser(
        "llm-review",
        help="layered review: deterministic gates (floor) + assessor (ceiling), on a change "
        "JSON or a git diff",
    )
    p_lr.add_argument("change", nargs="?", help="path to a change JSON file")
    p_lr.add_argument("--staged", action="store_true", help="review the staged git diff")
    p_lr.add_argument("--base", default=None, help="review base..head instead of a change JSON")
    p_lr.add_argument("--head", default="HEAD")
    p_lr.set_defaults(func=_cmd_llm_review)

    p_sc = sub.add_parser(
        "scorecard", help="measure recall lift: gates only vs. gates + assessor"
    )
    p_sc.set_defaults(func=_cmd_scorecard)

    p_ae = sub.add_parser("assess-eval", help="ZAVA on the assessor: its own recall / precision")
    p_ae.add_argument("--recall-min", dest="recall_min", type=float, default=None)
    p_ae.add_argument("--fpr-max", dest="fpr_max", type=float, default=None)
    p_ae.set_defaults(func=_cmd_assess_eval)

    p_adj = sub.add_parser("adjudicate", help="record a human decision on an assessor finding")
    p_adj.add_argument("finding_id", metavar="FINDING_ID")
    p_adj.add_argument("--outcome", choices=["confirmed", "dismissed"], required=True)
    p_adj.add_argument("--human", required=True, help="the deciding human's id")
    p_adj.add_argument("--signature", required=True)
    p_adj.add_argument("--reason", default=None)
    p_adj.set_defaults(func=_cmd_adjudicate)

    p_learn = sub.add_parser(
        "learn", help="findings by adjudication: confirmed / dismissed / pending"
    )
    p_learn.set_defaults(func=_cmd_learn)

    p_gov = sub.add_parser("governance", help="governance gaps: owners, overrides, ledger, ghosts")
    p_gov.set_defaults(func=_cmd_governance)

    p_exp = sub.add_parser("export", help="export an audit/DSAR evidence bundle for a change")
    p_exp.add_argument("change_id", metavar="CHANGE_ID")
    p_exp.add_argument("--out", default=None, help="write the bundle to this path")
    p_exp.set_defaults(func=_cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
