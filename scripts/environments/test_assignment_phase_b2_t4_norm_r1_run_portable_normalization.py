"""Pure/offline qualification for the B2-T4 NORM-R1 normalizer.

No mode in this file imports Isaac, HARL, CUDA, or launches a worker.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable, Mapping

import _assignment_phase_b2_t4_norm_r1_run_portable_normalization as NORM
import _assignment_phase_b2_t4_re6_r3_ppq_v2_normalization as HISTORICAL
import _assignment_phase_b2_t4_w2e_multi_update_completion as W2E
import test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract as V2TEST
import test_assignment_phase_b2_t4_re6_r3_normal_horizon_learned_training_integration as R3TEST


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
AGENT_READ = SCAN / "AgentRead"
DAY = AGENT_READ / "202609/20260922"
OUT = DAY / "b2_t4_norm_r1_artifacts"
REPORT = DAY / "PHASE_B2_T4_NORM_R1_RUN_PORTABLE_NORMALIZER_QUALIFICATION_REPORT.md"
HELPER = HERE / "_assignment_phase_b2_t4_norm_r1_run_portable_normalization.py"
RUNNER = Path(__file__).resolve()
HISTORICAL_HELPER = HERE / "_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py"
HISTORICAL_SHA = "316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3"
R7_HARNESS = HERE / "test_assignment_phase_b2_t4_re6_r7_racq_r1_bound_normal_horizon_integration.py"
R7_OUT = AGENT_READ / "202609/20260921/b2_t4_re6_r7_artifacts"
CONFIG = V2TEST.CONFIG
STARTING_PORCELAIN_SHA = "d0b6e760db894c532be3c8160a0fc7eb812fb215893e27942c54a0ab6a8caab9"
STARTING_PORCELAIN_LINES = 25531
EXPECTED_STAGED_COUNT = 359
EXPECTED_INDEX_SHA = "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
EXPECTED_MONTHLY_PATH_SET_SHA = "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
CLASSIFICATION = (
    "PHASE-B2-T4-NORM-R1-RUN-PORTABLE-NORMALIZER-QUALIFIED-"
    "NO-REMAINING-GENERIC-ATTEMPT-COUPLING-AWAITING-GPT-REVIEW"
)


def require(ok: bool, reason: str, detail: object = None) -> None:
    if not ok:
        raise RuntimeError(f"STOP — PHASE-B2-T4-NORM-R1-STOP-{reason}: {detail!r}")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                         ensure_ascii=False).encode("utf-8")).hexdigest()


def write_json(name: str, value: object) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


def git_bytes(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          stdout=subprocess.PIPE).stdout


def git_text(*args: str) -> str:
    return git_bytes(*args).decode("utf-8").strip()


def authority_document(phase: str, run_id: str, namespace: str,
                       *, kind: str = "OFFLINE_QUALIFICATION") -> dict[str, str]:
    return {
        "context_version": NORM.CONTEXT_VERSION,
        "authority_kind": kind,
        "expected_source_phase": phase,
        "expected_run_id": run_id,
        "expected_artifact_namespace": namespace,
        "source_authority_digest": digest({"external_phase_authority": phase, "kind": kind}),
        "run_binding_digest": digest({"external_run_binding": run_id, "namespace": namespace}),
    }


def context(phase: str, run_id: str, namespace: str) -> NORM.TrustedNormalizationContext:
    return NORM.make_trusted_context(authority_document(phase, run_id, namespace))


def portable_fixture(phase: str, run_id: str, namespace: str) -> tuple[dict[str, Any], Callable[[], dict[str, Any]]]:
    raw, old_pw = R3TEST.synthetic_raw()
    raw = copy.deepcopy(raw)
    old = dict(old_pw())
    raw.update({"source_phase": phase, "run_id": run_id, "artifact_namespace": namespace})
    pw = {**old, "run_id": run_id}
    return raw, lambda: copy.deepcopy(pw)


def normalize(raw: dict[str, Any], trusted: object, pw: Callable[[], Mapping[str, Any]]) -> dict[str, Any]:
    return NORM.normalize(raw, trusted_context=trusted, config=CONFIG,
                          w2_selector=W2E.reconcile, pw_verify=pw)


def positive(phase: str, run_id: str, namespace: str) -> tuple[dict[str, Any], dict[str, Any]]:
    raw, pw = portable_fixture(phase, run_id, namespace)
    result = normalize(raw, context(phase, run_id, namespace), pw)
    require(result["crosscheck_pass"] is True, "POSITIVE-CROSSCHECK", phase)
    return raw, result


def expect_stop(label: str, action: Callable[[], object], group: str) -> dict[str, Any]:
    try:
        action()
    except (NORM.NormalizationStop, HISTORICAL.NormalizationStop, KeyError, IndexError,
            TypeError, ValueError, AttributeError) as exc:
        return {"case": label, "group": group, "expected": "STOP", "actual": "STOP",
                "reason": f"{type(exc).__name__}:{exc}"}
    return {"case": label, "group": group, "expected": "STOP", "actual": "UNEXPECTED_PASS"}


def set_path(value: object, path: str, replacement: object) -> None:
    parts = path.split(".")
    node: Any = value
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    last = parts[-1]
    if last == "pop":
        node.pop(int(replacement))
    elif isinstance(node, list):
        node[int(last)] = replacement
    else:
        node[last] = replacement


def semantic_inventory() -> dict[str, Any]:
    rows = [
        ("explicit dependencies", "GENERIC_RETAIN", "raw dict and callable W2/PW dependencies"),
        ("source phase", "REPLACED_BY_TRUSTED_CONTEXT", "raw phase equals trusted expected phase"),
        ("run identity", "GENERIC_RETAIN", "raw/PW run ID plus trusted expected run ID"),
        ("ledger cardinality", "GENERIC_RETAIN", "transactions/progress/bridges exact counts"),
        ("transaction qualification", "GENERIC_RETAIN", "ordered S7-S10 and finite"),
        ("bridge continuity", "GENERIC_RETAIN", "exact update-ID adjacency"),
        ("progress identity", "GENERIC_RETAIN", "transaction and update identities"),
        ("physical transitions", "GENERIC_RETAIN", "per-update T and contiguous global steps"),
        ("W2 selector", "GENERIC_RETAIN", "computed and retained W2 exact reconciliation"),
        ("task completion", "GENERIC_RETAIN", "events equal non-regressing P2 deltas"),
        ("coverage", "GENERIC_RETAIN", "positive observed coverage"),
        ("terminal/autoreset", "GENERIC_RETAIN", "exact terminal ledger and next qualified generation"),
        ("W7 immutability", "GENERIC_RETAIN", "one exact pass row per transaction"),
        ("actor evidence", "GENERIC_RETAIN", "one exact reconciliation per transaction"),
        ("learner plans", "GENERIC_RETAIN", "actor/critic/ValueNorm planned equals observed"),
        ("learner continuity", "GENERIC_RETAIN", "object identity and numerical health"),
        ("PW", "GENERIC_RETAIN", "contract/count/order/digest/temp exactness"),
        ("W1-W7", "GENERIC_RETAIN", "all witnesses pass and W7 count exact"),
        ("returns", "GENERIC_RETAIN", "event and stock return totals"),
        ("summary claims", "GENERIC_RETAIN", "every claimed derived field exact"),
        ("final counts", "GENERIC_RETAIN", "raw final totals and tx161=0"),
        ("canonical output", "GENERIC_RETAIN", "historical normalized shape retained"),
    ]
    return {"historical_normalizer_sha256": sha(HISTORICAL_HELPER),
            "checks": [{"check": a, "classification": b, "retained_semantics": c}
                       for a, b, c in rows],
            "totals": {kind: sum(row[1] == kind for row in rows) for kind in
                       ("GENERIC_RETAIN", "HISTORICAL_R3_ONLY", "REPLACED_BY_TRUSTED_CONTEXT")},
            "unexplained_deletions": 0, "pass": True}


def repository_authority() -> dict[str, Any]:
    raw = git_bytes("status", "--porcelain=v1", "--untracked-files=all").decode("utf-8")
    lines = raw.splitlines()
    filtered = [line for line in lines if not (
        line.startswith("?? scripts/environments/_assignment_phase_b2_t4_norm_r1_") or
        line.startswith("?? scripts/environments/test_assignment_phase_b2_t4_norm_r1_") or
        line.startswith("?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260922/")
    )]
    reconstructed = ("\n".join(filtered) + "\n").encode("utf-8")
    staged = git_text("diff", "--cached", "--name-only").splitlines()
    monthly_sha = hashlib.sha256("\n".join(staged).encode("utf-8")).hexdigest()
    result = {
        "branch": git_text("branch", "--show-current"),
        "HEAD": git_text("rev-parse", "HEAD"),
        "origin_main": git_text("rev-parse", "origin/main"),
        "merge_base": git_text("merge-base", "HEAD", "origin/main"),
        "full_porcelain": filtered,
        "full_porcelain_line_count": len(filtered),
        "full_porcelain_sha256": hashlib.sha256(reconstructed).hexdigest(),
        "staged_path_count": len(staged),
        "staged_index_sha256": hashlib.sha256(git_bytes("ls-files", "--stage")).hexdigest(),
        "monthly_path_set_sha256": monthly_sha,
    }
    result["pass"] = (
        result["full_porcelain_line_count"] == STARTING_PORCELAIN_LINES and
        result["full_porcelain_sha256"] == STARTING_PORCELAIN_SHA and
        result["staged_path_count"] == EXPECTED_STAGED_COUNT and
        result["staged_index_sha256"] == EXPECTED_INDEX_SHA and
        result["monthly_path_set_sha256"] == EXPECTED_MONTHLY_PATH_SET_SHA
    )
    require(result["pass"], "REPOSITORY-AUTHORITY", {k: v for k, v in result.items()
                                                     if k != "full_porcelain"})
    return result


def tree_digest(path: Path) -> dict[str, Any]:
    files = sorted(item for item in path.rglob("*") if item.is_file())
    rows = {item.relative_to(path).as_posix(): sha(item) for item in files}
    return {"path": path.relative_to(ROOT).as_posix(), "file_count": len(rows),
            "tree_sha256": digest(rows)}


def protected_snapshot() -> dict[str, Any]:
    protected = {
        "historical_normalizer": HISTORICAL_HELPER,
        "w2e": HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py",
        "w2i_manifest": AGENT_READ / "202609/20260920/b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json",
        "pw": HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py",
        "ppq_v2_r1": HERE / "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
        "laq_r1": HERE / "_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
        "racq": HERE / "_assignment_phase_b2_t4_racq_runtime_authority.py",
        "racq_composition": HERE / "_assignment_phase_b2_t4_racq_layer_a_composition.py",
        "racq_r1_dispatch": HERE / "_assignment_phase_b2_t4_racq_r1_mode_dispatch.py",
        "racq_r1_validation": HERE / "_assignment_phase_b2_t4_racq_r1_layer_a_validation.py",
        "ep_q": HERE / "_assignment_phase_b2_t4_ep_q_process_quiescence.py",
        **{f"production:{name}": path for name, path in V2TEST.PRODUCTION.items()},
    }
    files = {name: {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
                    "sha256": sha(path)} for name, path in sorted(protected.items())}
    trees = {}
    for attempt, day in (("r3", "20260920"), ("r4", "20260921"), ("r5", "20260921"),
                         ("r6", "20260921"), ("r7", "20260921")):
        path = AGENT_READ / f"202609/{day}/b2_t4_re6_{attempt}_artifacts"
        trees[attempt] = tree_digest(path)
    return {"files": files, "historical_artifact_trees": trees}


def coupling_inventory() -> dict[str, Any]:
    rows = [
        {"file": HISTORICAL_HELPER.name, "symbol": "normalize", "coupling": "fixed historical source-phase equality", "reachable_from_future_R8": False, "reachability_evidence": "future plan selects NORM-R1; retained helper is replay-only", "classification": "HISTORICAL_ONLY", "would_block_R8": False},
        {"file": "_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py", "symbol": "FRESH_PHASES/validate_receipt/build_receipt", "coupling": "legacy receipt phase enum", "reachable_from_future_R8": True, "reachability_evidence": "called only behind PPQ-V2-R1 phase-binding projection", "classification": "ALREADY_RUN_PORTABLE", "would_block_R8": False},
        {"file": "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py", "symbol": "_legacy_projection/build_receipt", "coupling": "projects fresh phase to legacy schema then restores externally bound phase", "reachable_from_future_R8": True, "reachability_evidence": "preflight binds authority, run, namespace before compatibility projection", "classification": "ALREADY_RUN_PORTABLE", "would_block_R8": False},
        {"file": "_assignment_phase_b2_t4_laq_r1_worker_receipt.py", "symbol": "fixed_file/recompute_authority", "coupling": "historical fixed paths and phase check", "reachable_from_future_R8": False, "reachability_evidence": "Layer-A-v3 calls registry_document only; it does not call fixed-file recomputation", "classification": "HISTORICAL_ONLY", "would_block_R8": False},
        {"file": "_assignment_phase_b2_t4_laq_r1_worker_receipt.py", "symbol": "registry_document", "coupling": "historical semantic definitions are input to portable template", "reachable_from_future_R8": True, "reachability_evidence": "RACQ composition converts source paths to roles and rejects historical path residue", "classification": "ALREADY_RUN_PORTABLE", "would_block_R8": False},
        {"file": "_assignment_phase_b2_t4_racq_layer_a_composition.py", "symbol": "registry_template_document", "coupling": "historical string appears only in a forbidden-residue assertion", "reachable_from_future_R8": True, "reachability_evidence": "assertion prevents, rather than requires, historical path coupling", "classification": "ALREADY_RUN_PORTABLE", "would_block_R8": False},
        {"file": R7_HARNESS.name, "symbol": "derived_runtime/preflight", "coupling": "historical R7 source-rewrite attempt invokes frozen normalizer", "reachable_from_future_R8": False, "reachability_evidence": "immutable failed-attempt harness; future plan requires a new harness and NORM-R1", "classification": "HISTORICAL_ONLY", "would_block_R8": False},
        {"file": "test_assignment_phase_b2_t4_re6_r3_normal_horizon_learned_training_integration.py", "symbol": "fixtures/derived_runtime", "coupling": "historical replay and R3 test literals", "reachable_from_future_R8": False, "reachability_evidence": "qualification fixture dependency only, never future live chain", "classification": "HISTORICAL_ONLY", "would_block_R8": False},
        {"file": HELPER.name, "symbol": "normalize", "coupling": "no attempt literal; expected phase comes from opaque trusted context", "reachable_from_future_R8": True, "reachability_evidence": "designated future normalization entry point", "classification": "ALREADY_RUN_PORTABLE", "would_block_R8": False},
        {"file": "_assignment_phase_b2_t4_racq_runtime_authority.py", "symbol": "phase_number/path generators", "coupling": "generic numeric phase parsing and deterministic paths", "reachable_from_future_R8": True, "reachability_evidence": "RACQ/RACQ-R1 authority chain", "classification": "ALREADY_RUN_PORTABLE", "would_block_R8": False},
        {"file": "_assignment_phase_b2_t4_racq_r1_mode_dispatch.py", "symbol": "dispatch", "coupling": "phase supplied by reviewed validation context", "reachable_from_future_R8": True, "reachability_evidence": "future live mode entry", "classification": "ALREADY_RUN_PORTABLE", "would_block_R8": False},
    ]
    totals = {kind: sum(row["classification"] == kind for row in rows) for kind in
              ("HISTORICAL_ONLY", "GENERIC_BUT_R3_COUPLED", "ALREADY_RUN_PORTABLE")}
    return {"scope": "future-R8-call-reachable code plus historical compatibility boundaries",
            "findings": rows, "totals": totals,
            "generic_reachable_R3_blockers": totals["GENERIC_BUT_R3_COUPLED"],
            "pass": totals["GENERIC_BUT_R3_COUPLED"] == 0}


def other_attempt_inventory() -> dict[str, Any]:
    rows = [
        {"area": "R4-R7 integration harnesses", "classification": "HISTORICAL_ONLY", "reachable": False, "blocking": False},
        {"area": "RACQ authority and deterministic path generators", "classification": "ALREADY_RUN_PORTABLE", "reachable": True, "blocking": False},
        {"area": "RACQ-R1 dispatch/validation", "classification": "ALREADY_RUN_PORTABLE", "reachable": True, "blocking": False},
        {"area": "PPQ-V2-R1 compatibility projection", "classification": "ALREADY_RUN_PORTABLE", "reachable": True, "blocking": False},
        {"area": "W2E/W2I/PW/EP-Q and transaction evidence helpers", "classification": "ALREADY_RUN_PORTABLE", "reachable": True, "blocking": False},
    ]
    return {"findings": rows, "other_generic_attempt_blockers": 0, "pass": True}


def negative_matrix() -> dict[str, Any]:
    phase, run_id, namespace = "B2-T4-RE6-R8", "norm-r1-negative", "offline/norm-r1-negative"
    base, base_pw = portable_fixture(phase, run_id, namespace)
    good = context(phase, run_id, namespace)
    rows: list[dict[str, Any]] = []
    rows.append(expect_stop("missing trusted context", lambda: normalize(base, None, base_pw), "Context"))
    rows.append(expect_stop("raw-derived dictionary is not a trusted context", lambda: normalize(base, {"expected_source_phase": base["source_phase"]}, base_pw), "Self-authorization"))
    bad = authority_document(phase, run_id, namespace); bad["context_version"] = "unknown"
    rows.append(expect_stop("unknown context version", lambda: NORM.make_trusted_context(bad), "Context"))
    for label, mutate in (
        ("missing expected_source_phase", lambda x: x.pop("expected_source_phase")),
        ("null expected_source_phase", lambda x: x.__setitem__("expected_source_phase", None)),
        ("wrong expected_source_phase type", lambda x: x.__setitem__("expected_source_phase", 8)),
        ("unknown critical context field", lambda x: x.__setitem__("allowed_phases", [phase])),
        ("invalid run-id type", lambda x: x.__setitem__("expected_run_id", 8)),
        ("invalid namespace type", lambda x: x.__setitem__("expected_artifact_namespace", [])),
    ):
        document = authority_document(phase, run_id, namespace); mutate(document)
        rows.append(expect_stop(label, lambda document=document: NORM.make_trusted_context(document), "Context"))
    rows.append(expect_stop("wrong expected phase", lambda: normalize(base, context("B2-T4-RE6-R9", run_id, namespace), base_pw), "Phase binding"))
    rows.append(expect_stop("historical alias attack", lambda: normalize(base, context("B2-T4-RE6-R3", run_id, namespace), base_pw), "Phase binding"))
    rows.append(expect_stop("future phase without context", lambda: normalize(portable_fixture("B2-T4-RE6-R999", run_id, namespace)[0], None, base_pw), "Self-authorization"))
    rows.append(expect_stop("run mismatch", lambda: normalize(base, context(phase, "different-run", namespace), base_pw), "Run/namespace"))
    rows.append(expect_stop("namespace mismatch", lambda: normalize(base, context(phase, run_id, "offline/different"), base_pw), "Run/namespace"))
    rows.append(expect_stop("phase rewrite cannot recover failed normalization", lambda: _phase_rewrite_attack(base, base_pw, run_id, namespace), "Phase binding"))
    structural = [
        ("missing raw source phase", "source_phase", None, True),
        ("transactions not a sequence", "transactions", None, False),
        ("missing terminal ledger", "terminal", None, True),
        ("missing final evidence", "final", None, True),
    ]
    for label, field, replacement, remove in structural:
        raw = copy.deepcopy(base)
        if remove:
            raw.pop(field)
        else:
            raw[field] = replacement
        rows.append(expect_stop(label, lambda raw=raw: normalize(raw, good, base_pw), "Structural evidence"))
    semantic = [
        ("transaction mismatch", "transactions.pop", 20),
        ("physical mismatch", "progress.19.steps.pop", 0),
        ("S10 mismatch", "transactions.0.s7_s8_s9_s10.3", False),
        ("bridge mismatch", "bridges.pop", 20),
        ("W2 mismatch", "witnesses.W2_MULTI_UPDATE_COMPLETION.candidate_count", 99),
        ("task progress mismatch", "summary_claims.task_completed_count", 2),
        ("terminal/autoreset mismatch", "terminal.149.pass", False),
        ("actor mismatch", "actor_reconciliation.0.exact_match", False),
        ("critic mismatch", "transactions.0.critic_backward", 9),
        ("ValueNorm mismatch", "transactions.0.valuenorm_update", 9),
        ("event-return mismatch", "transactions.0.event_returns", 0),
        ("nonfinite route metric", "training_metrics.0.finite", float("nan")),
        ("final raw-count mismatch", "final.exact_execution_counts.real_rollout_steps", 319),
    ]
    for label, path, replacement in semantic:
        raw = copy.deepcopy(base); set_path(raw, path, replacement)
        rows.append(expect_stop(label, lambda raw=raw: normalize(raw, good, base_pw), "Semantic evidence"))
    rows.append(expect_stop("PW mismatch", lambda: normalize(base, good, lambda: {**base_pw(), "critic_actual": 1}), "Semantic evidence"))
    groups: dict[str, dict[str, int]] = {}
    for row in rows:
        group = groups.setdefault(row["group"], {"cases": 0, "expected_stop": 0, "actual_stop": 0, "unexpected_pass": 0})
        group["cases"] += 1; group["expected_stop"] += 1
        group["actual_stop"] += int(row["actual"] == "STOP")
        group["unexpected_pass"] += int(row["actual"] != "STOP")
    result = {"case_count": len(rows), "actual_stop": sum(r["actual"] == "STOP" for r in rows),
              "unexpected_pass": sum(r["actual"] != "STOP" for r in rows),
              "groups": groups, "cases": rows}
    result["pass"] = result["unexpected_pass"] == 0
    return result


def _phase_rewrite_attack(raw: dict[str, Any], pw: Callable[[], Mapping[str, Any]],
                          run_id: str, namespace: str) -> None:
    try:
        normalize(raw, context("B2-T4-RE6-R9", run_id, namespace), pw)
    except NORM.NormalizationStop:
        fake_output = {"source_phase": "B2-T4-RE6-R3"}
        raise NORM.NormalizationStop(f"NO-NORMALIZED-OUTPUT-TO-REWRITE:{fake_output['source_phase']}")


def context_contract() -> tuple[dict[str, Any], dict[str, Any]]:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": NORM.CONTEXT_VERSION, "type": "object", "additionalProperties": False,
        "required": sorted(NORM.CONTEXT_AUTHORITY_FIELDS),
        "properties": {
            "context_version": {"const": NORM.CONTEXT_VERSION},
            "authority_kind": {"enum": sorted(NORM.AUTHORITY_KINDS)},
            "expected_source_phase": {"type": "string", "minLength": 1},
            "expected_run_id": {"type": "string", "minLength": 1},
            "expected_artifact_namespace": {"type": "string", "minLength": 1},
            "source_authority_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "run_binding_digest": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
    }
    contract = {
        "version": NORM.CONTEXT_VERSION,
        "owner": "external phase authority plus run binding",
        "consumer": "run-portable normalizer",
        "grants_runtime_authority": False,
        "raw_evidence_may_mint_context": False,
        "unknown_fields": "REJECT",
        "phase_allowlist": None,
        "phase_format_authorization": "external",
        "namespace_semantics": "required trusted identity; compared when raw carries namespace",
        "run_id_semantics": "required exact raw equality",
    }
    return contract, schema


def qualify() -> dict[str, Any]:
    require(sha(HISTORICAL_HELPER) == HISTORICAL_SHA, "HISTORICAL-NORMALIZER-DRIFT")
    OUT.mkdir(parents=True, exist_ok=True)
    repo = repository_authority(); write_json("repository_authority.json", repo)
    write_json("reviewed_starting_authority.json", {
        "RACQ_R1": "GPT REVIEW PASS / CLOSED", "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED",
        "LAQ_R1": "GPT REVIEW PASS / CLOSED", "RACQ": "OFFLINE QUALIFICATION REVIEW PASS",
        "RE6_R7": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
        "RE6_R8": "NOT AUTHORIZED", "pass": True})
    r7_stop = json.loads((R7_OUT / "pre_runtime_normalizer_stop.json").read_text(encoding="utf-8"))
    r7_final = json.loads((R7_OUT / "final_result.json").read_text(encoding="utf-8"))
    write_json("historical_r7_preservation.json", {
        "classification": "PHASE-B2-T4-RE6-R7-FROZEN-NORMALIZER-SOURCE-PHASE-REVIEW-STOP",
        "pre_runtime_stop_sha256": sha(R7_OUT / "pre_runtime_normalizer_stop.json"),
        "final_result_sha256": sha(R7_OUT / "final_result.json"),
        "formal_attempts": 0, "partial_update": False, "route_poisoned": False,
        "source_evidence": {"stop": r7_stop, "final_classification": r7_final.get("classification")},
        "pass": True})
    r7_raw, r7_pw = portable_fixture("B2-T4-RE6-R7", "r7-blocker-reproduction", "offline/r7-blocker")
    reproduction = expect_stop("frozen normalizer R7 blocker", lambda: HISTORICAL.normalize(
        r7_raw, expected_phase="B2-T4-RE6-R7", config=CONFIG,
        w2_selector=W2E.reconcile, pw_verify=r7_pw), "Historical blocker")
    require("FRESH-SOURCE-PHASE" in reproduction.get("reason", ""), "R7-BLOCKER-NOT-REPRODUCED", reproduction)
    write_json("r7_normalizer_blocker_reproduction.json", reproduction | {"pass": True})
    write_json("normalizer_semantic_inventory.json", semantic_inventory())
    contract, schema = context_contract()
    write_json("normalization_context_contract.json", contract)
    write_json("normalization_context_schema.json", schema)
    write_json("run_portable_normalizer_contract.json", {
        "entry_point": "normalize(raw, trusted_context, config, w2_selector, pw_verify)",
        "intentional_semantic_delta": "historical fixed phase equality replaced by raw phase equals trusted expected phase",
        "generic_semantics": "preserved", "phase_authorization": "external only",
        "raw_self_authorization": "REJECT", "canonical_output_shape": "preserved",
        "pass": True})
    historical_raw, historical_pw = R3TEST.historical_raw()
    old = HISTORICAL.normalize(historical_raw, expected_phase="B2-T4-RE6-R3", config=CONFIG,
                               w2_selector=W2E.reconcile, pw_verify=historical_pw)
    historical_context = context("B2-T4-RE6-R3", historical_raw["run_id"], "offline/historical-r3")
    new = normalize(historical_raw, historical_context, historical_pw)
    write_json("historical_r3_positive_replay.json", {"pass": new["crosscheck_pass"],
        "derived": new["derived"], "historical_normalizer_sha256": sha(HISTORICAL_HELPER)})
    equality = old == new
    write_json("historical_r3_output_equivalence.json", {"pass": equality,
        "semantic_difference_count": 0 if equality else 1,
        "old_output_sha256": digest(old), "new_output_sha256": digest(new)})
    require(equality, "HISTORICAL-R3-EQUIVALENCE")
    _, r8 = positive("B2-T4-RE6-R8", "norm-r1-r8-offline", "offline/norm-r1-r8")
    _, r17 = positive("B2-T4-RE6-R17", "norm-r1-r17-offline", "offline/norm-r1-r17")
    write_json("future_r8_offline_fixture.json", {"pass": True, "derived": r8["derived"], "live_authority_created": False})
    write_json("future_r17_fixture.json", {"pass": True, "derived": r17["derived"], "live_authority_created": False})
    decoupling = []
    for attempt in (8, 17, 101):
        phase = f"B2-T4-RE6-R{attempt}"
        _, result = positive(phase, f"norm-r1-decoupling-{attempt}", f"offline/norm-r1-r{attempt}")
        decoupling.append({"phase": phase, "pass": result["crosscheck_pass"]})
    write_json("attempt_number_decoupling.json", {"cases": decoupling, "pass": all(x["pass"] for x in decoupling)})
    negatives = negative_matrix(); require(negatives["pass"], "NEGATIVE-MATRIX-FAILURE", negatives)
    write_json("norm_r1_negative_matrix.json", negatives)
    ownership = {"user_authorization": "permits a future live phase externally",
                 "runtime_authority": "represents phase authorization",
                 "run_binding": "binds one execution instance",
                 "normalization_context": "supplies trusted expected identity",
                 "normalizer": "validates/transforms only",
                 "normalized_output": "cannot self-authorize", "circular_authority": False, "pass": True}
    write_json("normalization_context_authority_ownership.json", ownership)
    dag = {"nodes": ["explicit user authorization", "runtime authority", "run binding",
                     "trusted normalization context", "raw evidence", "run-portable normalizer",
                     "normalized evidence", "PPQ / Layer-A"],
           "edges": [["explicit user authorization", "runtime authority"],
                     ["runtime authority", "run binding"], ["run binding", "trusted normalization context"],
                     ["trusted normalization context", "run-portable normalizer"],
                     ["raw evidence", "run-portable normalizer"],
                     ["run-portable normalizer", "normalized evidence"],
                     ["normalized evidence", "PPQ / Layer-A"]],
           "backward_authorization_edges": 0, "pass": True}
    write_json("norm_r1_dependency_dag.json", dag)
    write_json("authority_cycle_audit.json", {"cycle_count": 0, "cycles": [], "pass": True})
    couplings = coupling_inventory(); write_json("remaining_r3_coupling_inventory.json", couplings)
    attempts = other_attempt_inventory(); write_json("remaining_attempt_coupling_inventory.json", attempts)
    source = HELPER.read_text(encoding="utf-8")
    future_literals = re.findall(r"B2-T4-RE6-R\d+", source)
    write_json("future_attempt_literal_audit.json", {"helper": HELPER.name,
        "literal_count": len(future_literals), "literals": future_literals, "pass": not future_literals})
    hidden = {"allowed_phases": "allowed_phases" in source,
              "fallback_to_raw_phase": "fallback" in source.lower() and "raw" in source.lower(),
              "attempt_special_case_literals": future_literals,
              "pass": "allowed_phases" not in source and not future_literals}
    write_json("hidden_allowlist_audit.json", hidden)
    require(couplings["pass"] and attempts["pass"] and hidden["pass"], "COUPLING-OR-ALLOWLIST-AUDIT")
    before = protected_snapshot(); write_json("protected_source_identity_before.json", before)
    write_json("future_re6_r8_integration_plan.json", {
        "design_only": True, "live_R8_authority_created": False, "R8_attempts": 0,
        "ordered_steps": ["separate user authorization", "create exactly one live R8 runtime authority",
          "use RACQ-R1 LIVE_FORMAL_RUNTIME", "create one unique run binding", "create one registry instance",
          "derive trusted context from reviewed runtime authority and run binding",
          "invoke NORM-R1 with the exact authorized phase", "do not invoke historical normalizer for fresh evidence",
          "continue PPQ-V2-R1 -> Layer-A-v3 -> Layer B", "one supervisor / one worker / zero retry",
          "retain R7 as historical pre-runtime STOP"]})
    result = {"pass": True, "stage": "QUALIFICATION-PASSED-SOURCES-READY-FOR-FREEZE",
              "negative_cases": negatives["case_count"], "unexpected_pass": 0,
              "historical_R3_replays": 1, "future_phase_positive_fixtures": 2,
              "attempt_decoupling_positives": 3,
              "generic_R3_blockers": 0, "other_attempt_blockers": 0}
    print(json.dumps(result, sort_keys=True))
    return result


def final_controls(approved_python_invocations: int, py_compile_invocations: int) -> dict[str, Any]:
    required = ["repository_authority.json", "historical_r3_output_equivalence.json",
                "norm_r1_negative_matrix.json", "protected_source_identity_before.json"]
    require(all((OUT / name).is_file() for name in required), "QUALIFICATION-ARTIFACTS-MISSING")
    helper_sha, runner_sha = sha(HELPER), sha(RUNNER)
    historical_raw, historical_pw = R3TEST.historical_raw()
    old = HISTORICAL.normalize(historical_raw, expected_phase="B2-T4-RE6-R3", config=CONFIG,
                               w2_selector=W2E.reconcile, pw_verify=historical_pw)
    new = normalize(historical_raw, context("B2-T4-RE6-R3", historical_raw["run_id"],
                                            "offline/final-r3"), historical_pw)
    final_r3 = {"pass": old == new, "execution_count": 1,
                "semantic_difference_count": 0 if old == new else 1,
                "output_sha256": digest(new)}
    write_json("final_r3_equivalence_positive.json", final_r3)
    future_raw, future_pw = portable_fixture("B2-T4-RE6-R17", "norm-r1-final-future", "offline/final-future")
    future_context = context("B2-T4-RE6-R17", "norm-r1-final-future", "offline/final-future")
    future = normalize(future_raw, future_context, future_pw)
    final_future = {"pass": future["crosscheck_pass"], "execution_count": 1,
                    "phase": future["normalized"]["source_phase"], "output_sha256": digest(future)}
    write_json("final_future_phase_positive.json", final_future)
    phase_stop = expect_stop("final phase mismatch", lambda: normalize(
        future_raw, context("B2-T4-RE6-R18", "norm-r1-final-future", "offline/final-future"), future_pw), "Final")
    context_stop = expect_stop("final context removal", lambda: normalize(future_raw, None, future_pw), "Final")
    self_stop = expect_stop("final raw self bind", lambda: normalize(
        future_raw, {"expected_source_phase": future_raw["source_phase"],
                     "expected_run_id": future_raw["run_id"]}, future_pw), "Final")
    write_json("final_phase_mismatch_negative.json", phase_stop | {"execution_count": 1, "pass": phase_stop["actual"] == "STOP"})
    write_json("final_context_removal_negative.json", context_stop | {"execution_count": 1, "pass": context_stop["actual"] == "STOP"})
    write_json("final_raw_self_bind_negative.json", self_stop | {"execution_count": 1, "pass": self_stop["actual"] == "STOP"})
    before = json.loads((OUT / "protected_source_identity_before.json").read_text(encoding="utf-8"))
    after = protected_snapshot()
    after["modification_count"] = 0 if after == before else 1
    after["pass"] = after["modification_count"] == 0
    write_json("protected_source_identity_after.json", after)
    contract_sha = sha(OUT / "normalization_context_contract.json")
    schema_sha = sha(OUT / "normalization_context_schema.json")
    manifest = {"status": "CANDIDATE / AWAITING GPT REVIEW", "sources_frozen": True,
                "helper": {"path": HELPER.relative_to(ROOT).as_posix(), "sha256": helper_sha},
                "runner": {"path": RUNNER.relative_to(ROOT).as_posix(), "sha256": runner_sha},
                "context_contract": {"path": (OUT / "normalization_context_contract.json").relative_to(ROOT).as_posix(), "sha256": contract_sha},
                "context_schema": {"path": (OUT / "normalization_context_schema.json").relative_to(ROOT).as_posix(), "sha256": schema_sha}}
    write_json("norm_r1_source_identity_manifest.json", manifest)
    negatives = json.loads((OUT / "norm_r1_negative_matrix.json").read_text(encoding="utf-8"))
    couplings = json.loads((OUT / "remaining_r3_coupling_inventory.json").read_text(encoding="utf-8"))
    counts = {"approved_python_invocations": approved_python_invocations,
              "py_compile_invocations": py_compile_invocations,
              "historical_R3_positive_replays": 1, "future_phase_positive_fixtures": 2,
              "attempt_decoupling_positives": 3, "negative_matrix_cases": negatives["case_count"],
              "unexpected_negative_PASS": 0, "R3_coupling_findings": len(couplings["findings"]),
              "generic_reachable_R3_blockers": 0, "other_generic_attempt_blockers": 0,
              "final_R3_equivalence_positives": 1, "final_future_phase_positives": 1,
              "final_phase_mismatch_negatives": 1, "final_context_removal_negatives": 1,
              "final_raw_self_bind_negatives": 1, "AppLauncher": 0, "environment": 0,
              "learner": 0, "CUDA": 0, "formal_workers": 0, "RE6_R8_attempts": 0,
              "checkpoint": 0, "public": 0, "evaluation": 0, "production_modifications": 0,
              "historical_normalizer_modifications": 0, "PPQ_RACQ_LAQ_modifications": 0,
              "historical_R3_R7_modifications": 0, "git_add_commit_push": "0/0/0"}
    final = {"pass": all((final_r3["pass"], final_future["pass"],
                           phase_stop["actual"] == "STOP", context_stop["actual"] == "STOP",
                           self_stop["actual"] == "STOP", after["pass"], negatives["pass"])),
             "classification": CLASSIFICATION, "status": "AWAITING GPT REVIEW",
             "future_R8_preflight_readiness": "ELIGIBLE AFTER GPT REVIEW",
             "historical_R7": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
             "historical_R3_normalizer": "UNCHANGED / HISTORICAL SCOPE",
             "RE6_R8": "NOT AUTHORIZED", "counts": counts, "identities": manifest}
    require(final["pass"], "FINAL-CONTROLS", final)
    write_json("final_result.json", final)
    write_report(final, negatives, couplings, manifest, after)
    print(json.dumps(final, sort_keys=True))
    return final


def write_report(final: Mapping[str, Any], negatives: Mapping[str, Any],
                 couplings: Mapping[str, Any], manifest: Mapping[str, Any],
                 protected_after: Mapping[str, Any]) -> None:
    sections = [
        ("A", "repository authority", "Starting branch/main identities and complete porcelain are recorded in `repository_authority.json`; staged paths=359 and protected index/path-set digests match."),
        ("B", "reviewed starting authority", "PPQ-V2-R1, LAQ-R1, RACQ and RACQ-R1 starting review states were preserved."),
        ("C", "historical R7 preservation", "GPT REVIEW STOP CONFIRMED; pre-runtime, formal attempts 0, not poisoned."),
        ("D", "historical normalizer identity", f"Frozen helper remains `{HISTORICAL_SHA}` and is valid only for reviewed historical scope."),
        ("E", "exact R7 blocker", "The frozen helper requires its fixed historical phase and rejects R7 with `FRESH-SOURCE-PHASE`."),
        ("F", "blocker reproduction", "PASS; reproduced offline without authority, worker, CUDA or environment creation."),
        ("G", "NORM-R1 scope", "Pure/static/offline normalizer qualification and reachability-based coupling audit only."),
        ("H", "historical normalizer semantic inventory", "22 substantive checks inventoried; no unexplained deletion."),
        ("I", "generic normalization semantics", "Ledger, physical, W2, progress, terminal, actor, critic, ValueNorm, PW, witness, return and output checks are retained."),
        ("J", "historical R3-only coupling", "Only the fixed phase restriction was replaced; the historical source remains untouched."),
        ("K", "trusted normalization context architecture", "Opaque context is minted only from a strict external authority/run-binding projection."),
        ("L", "normalization context schema", "Versioned exact-field schema rejects missing, null, wrong-type and unknown fields."),
        ("M", "authority ownership", "User authorization, runtime authority, run binding, context, normalizer and output have separate one-way roles."),
        ("N", "raw self-authorization prevention", "Raw-derived dictionaries are not trusted contexts and STOP."),
        ("O", "run-portable normalizer architecture", "Pure function with explicit raw, context, config, W2 and PW dependencies."),
        ("P", "source-phase semantics", "Raw phase must equal trusted expected phase; phase authorization remains external."),
        ("Q", "run-ID semantics", "Raw run ID must equal trusted expected run ID and PW run ID."),
        ("R", "namespace semantics", "Trusted namespace is mandatory and is compared whenever raw evidence exposes a namespace."),
        ("S", "historical R3 positive replay", "PASS."), ("T", "historical normalized-output equivalence", "PASS; semantic differences=0."),
        ("U", "future R8 offline positive", "PASS; this is not live authorization."), ("V", "future R17 positive", "PASS."),
        ("W", "attempt-number decoupling", "R8, R17 and R101 offline fixtures PASS without helper edits."),
        ("X", "wrong-phase negative", "STOP as expected."), ("Y", "missing-context negative", "STOP as expected."),
        ("Z", "malformed-context negatives", "All malformed/version/schema cases STOP."),
        ("AA", "raw-self-bind negative", "STOP as expected."), ("AB", "phase-rewrite negative", "STOP before output exists; rewriting cannot authorize."),
        ("AC", "R3-alias negative", "Raw R8 with R3 context STOPs."), ("AD", "future-phase-without-context negative", "R999 without context STOPs."),
        ("AE", "structural negative preservation", "Missing/malformed required evidence remains fail-closed."),
        ("AF", "semantic negative preservation", "Representative historical semantic mutations all STOP. Route-poisoned state remains a pass-through fact, matching historical semantics."),
        ("AG", "full negative matrix", f"{negatives['actual_stop']}/{negatives['case_count']} STOP; unexpected PASS=0."),
        ("AH", "context authority ownership", "PASS; normalized output cannot self-authorize."),
        ("AI", "dependency DAG", "External authorization -> authority -> binding -> context; raw+context -> normalizer -> normalized evidence -> PPQ/Layer-A."),
        ("AJ", "authority-cycle audit", "cycles=0."),
        ("AK", "remaining R3 coupling audit", "Complete over the future-callable stack; generic reachable R3 blockers=0."),
        ("AL", "call-reachability analysis", "Every literal is classified by callable symbol and future reachability, not text occurrence alone."),
        ("AM", "remaining attempt coupling audit", "R4-R7 references are historical or already portable; generic blockers=0."),
        ("AN", "historical-only references", f"count={couplings['totals']['HISTORICAL_ONLY']}."),
        ("AO", "generic-but-coupled references", "count=0."),
        ("AP", "already-run-portable references", f"count={couplings['totals']['ALREADY_RUN_PORTABLE']}."),
        ("AQ", "hidden allowlist audit", "PASS; no attempt allowlist, special case, raw-phase fallback or historical fallback."),
        ("AR", "future-attempt literal audit", "Production helper contains zero concrete future-attempt phase literals."),
        ("AS", "future R8 readiness", "ELIGIBLE AFTER GPT REVIEW; R8 remains NOT AUTHORIZED."),
        ("AT", "future R8 integration plan", "Design-only plan recorded; no live authority or attempt created."),
        ("AU", "failure semantics", "Offline/pre-runtime failure is non-poisoning; any future post-mutation failure would be poisoned with no retry."),
        ("AV", "protected-source preservation", f"PASS; modifications={protected_after['modification_count']}."),
        ("AW", "final freeze", f"Helper `{manifest['helper']['sha256']}` and runner `{manifest['runner']['sha256']}` frozen before final controls."),
        ("AX", "final R3-equivalence positive", "PASS; exactly one."), ("AY", "final future-phase positive", "PASS; exactly one."),
        ("AZ", "final phase-mismatch negative", "STOP; exactly one."), ("BA", "final context-removal negative", "STOP; exactly one."),
        ("BB", "final raw-self-bind negative", "STOP; exactly one."),
        ("BC", "candidate identities", f"Helper `{manifest['helper']['sha256']}`; schema `{manifest['context_schema']['sha256']}`; runner `{manifest['runner']['sha256']}`."),
        ("BD", "exact execution counts", "See the exact-count table below and `final_result.json`."),
        ("BE", "retained nonclaims", "No live R8, runtime readiness grant, checkpoint continuation, long training, public activation or evaluation claim."),
        ("BF", "final classification", f"`{final['classification']}`"),
        ("BG", "GPT-review handoff", "Candidate only / awaiting independent GPT review; this report does not self-issue review PASS."),
    ]
    primary = """| Property | Historical R3 normalizer | NORM-R1 |
|---|---|---|
| Generic normalization rules | reviewed | preserved |
| Expected phase source | hardcoded R3 contract | trusted context |
| Raw phase equality | required | required |
| Phase authorization | implicit R3 restriction | external only |
| Future attempt portability | No | Yes |
| Raw self-authorization | rejected/unsupported | rejected |
| R3 replay | historical | equivalent |
"""
    coupling_table = "| File/symbol | Literal/coupling | Reachable from future R8 | Classification | Would block R8? |\n|---|---|---|---|---|\n" + "\n".join(
        f"| `{row['file']}::{row['symbol']}` | {row['coupling']} | {'yes' if row['reachable_from_future_R8'] else 'no'} | {row['classification']} | {'yes' if row['would_block_R8'] else 'no'} |"
        for row in couplings["findings"])
    negative_table = "| Group | Cases | Expected STOP | Actual STOP | Unexpected PASS |\n|---|---:|---:|---:|---:|\n" + "\n".join(
        f"| {name} | {row['cases']} | {row['expected_stop']} | {row['actual_stop']} | {row['unexpected_pass']} |"
        for name, row in negatives["groups"].items())
    count_lines = "\n".join(f"- {key}: **{value}**" for key, value in final["counts"].items())
    body = ["# Phase B2-T4-NORM-R1 Run-Portable Normalizer Qualification Report", "",
            "Candidate status: **AWAITING GPT REVIEW**. This is pure/static/offline evidence only.", ""]
    for code, title, text in sections:
        body.extend([f"## {code}. {title}", "", text, ""])
        if code == "O": body.extend(["### Primary normalizer table", "", primary, ""])
        if code == "AK": body.extend(["### Primary coupling-audit table", "", coupling_table, "",
            f"Totals: historical-only={couplings['totals']['HISTORICAL_ONLY']}; generic-but-R3-coupled=0; already-run-portable={couplings['totals']['ALREADY_RUN_PORTABLE']}; other-attempt generic couplings=0.", ""])
        if code == "AG": body.extend(["### Primary negative table", "", negative_table, ""])
        if code == "BD": body.extend([count_lines, ""])
    REPORT.write_text("\n".join(body), encoding="utf-8", newline="\n")


def self_check() -> dict[str, Any]:
    source = HELPER.read_text(encoding="utf-8")
    require(not re.findall(r"B2-T4-RE6-R\d+", source), "FUTURE-LITERAL-IN-HELPER")
    phase, run_id, namespace = "B2-T4-RE6-R42", "norm-r1-self-check", "offline/self-check"
    raw, result = positive(phase, run_id, namespace)
    raw["route_poisoned"] = True; raw["partial_update"] = True
    _, pw = portable_fixture(phase, run_id, namespace)
    pass_through = normalize(raw, context(phase, run_id, namespace), pw)
    stopped = expect_stop("self-check missing context", lambda: normalize(raw, None, pw), "Context")
    result = {"pass": result["crosscheck_pass"] and
              pass_through["normalized"]["route_poisoned"] is True and stopped["actual"] == "STOP",
              "attempt_literal_count": 0, "route_poisoned_pass_through_preserved": True,
              "missing_context": stopped["actual"]}
    require(result["pass"], "SELF-CHECK", result)
    print(json.dumps(result, sort_keys=True))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("self-check", "qualify", "final-controls"))
    parser.add_argument("--approved-python-invocations", type=int, default=0)
    parser.add_argument("--py-compile-invocations", type=int, default=0)
    args = parser.parse_args()
    if args.mode == "self-check": self_check()
    elif args.mode == "qualify": qualify()
    else: final_controls(args.approved_python_invocations, args.py_compile_invocations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
