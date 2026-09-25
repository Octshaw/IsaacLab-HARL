"""Fresh B2-T4-RE2 normal-horizon learned-training integration qualification."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

from _assignment_phase_b2_t4_sr_reason_grid_serializer import (
    CLASSIFICATION_PRECEDENCE_SCHEMA_VERSION,
    REASON_GRID_SCHEMA_VERSION,
)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = (
    ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
DATE_ROOT = SCAN / "AgentRead" / "202609" / "20260914"
RE1_CANDIDATE = (
    HERE
    / "test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py"
)
SR_SERIALIZER = HERE / "_assignment_phase_b2_t4_sr_reason_grid_serializer.py"
RE1_S10 = (
    SCAN
    / "AgentRead"
    / "202609"
    / "20260913"
    / "b2_t4_re1_artifacts"
    / "b2_t4_re1_tx1_s10.json"
)
RE1_RAW_RESULT = RE1_S10.parent / "b2_t4_re1_final_result.json"
RE1_ADJUDICATION = RE1_S10.parent / "b2_t4_re1_failure_adjudication.json"

QUALIFIED_RE1_CANDIDATE_SHA256 = (
    "44ef0a289225a34c21bb31451465422e33fa20a713eb9a3ed4a715e97a0ff5d6"
)
QUALIFIED_SR_SERIALIZER_SHA256 = (
    "dcf780a37387e24b4cc3c1f5ee39d006029b04875bc6422c96896cddd8cb5358"
)
QUALIFIED_RE1_S10_SHA256 = (
    "e21591961c59e60a71cd9f27b6515a3f266bd7ac869ecff51e8b1600761e5649"
)
LIVE_REASON_GRID_SCHEMA = "b2_t4_sr_termination_reason_grid_v1"
LIVE_CLASSIFICATION_SCHEMA = "b2_t4_sr_classification_precedence_v1"
PASS = (
    "PHASE-B2-T4-RE2-NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-"
    "QUALIFIED-AWAITING-GPT-REVIEW"
)
STOP_READINESS = (
    "PHASE-B2-T4-RE2-STOP-RUNNER-BOOKKEEPING-READINESS-NOT-QUALIFIED"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _qualified_re2_source() -> tuple[str, dict[str, object]]:
    candidate_sha = _sha(RE1_CANDIDATE)
    serializer_sha = _sha(SR_SERIALIZER)
    if candidate_sha != QUALIFIED_RE1_CANDIDATE_SHA256:
        raise RuntimeError(
            "STOP — B2-T4-RE2 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"RE1 candidate {candidate_sha} != {QUALIFIED_RE1_CANDIDATE_SHA256}"
        )
    if serializer_sha != QUALIFIED_SR_SERIALIZER_SHA256:
        raise RuntimeError(
            "STOP — B2-T4-RE2 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"SR serializer {serializer_sha} != {QUALIFIED_SR_SERIALIZER_SHA256}"
        )
    source = RE1_CANDIDATE.read_text(encoding="utf-8")
    counts = {
        "uppercase_re1": source.count("RE1"),
        "lowercase_re1": source.count("re1"),
        "date_20260913": source.count("20260913"),
    }
    if counts["uppercase_re1"] == 0 or counts["lowercase_re1"] == 0:
        raise RuntimeError(
            f"STOP — B2-T4-RE2 QUALIFIED-TEST-SOURCE-DRIFT: transform counts {counts}"
        )
    transformed = source.replace("RE1", "RE2").replace("re1", "re2")
    transformed = transformed.replace("20260913", "20260914")
    # Preserve the already-qualified S10 payload field name.  It is evidence
    # schema, not a phase/run identity, and the readiness replay consumes the
    # immutable RE1 payload without rewriting it.
    transformed = transformed.replace("re2_step_details", "re1_step_details")
    receipt = {
        "schema_version": "b2_t4_re2_runner_derivation_v1",
        "re1_candidate_path": str(RE1_CANDIDATE),
        "re1_candidate_sha256": candidate_sha,
        "sr_serializer_path": str(SR_SERIALIZER),
        "sr_serializer_sha256": serializer_sha,
        "transform_counts": counts,
        "transformed_source_sha256": hashlib.sha256(
            transformed.encode("utf-8")
        ).hexdigest(),
        "production_semantic_modifications": 0,
    }
    return transformed, receipt


_SOURCE, RUNNER_DERIVATION = _qualified_re2_source()
_RE2: dict[str, object] = {
    "__name__": "_phase_b2_t4_re2_qualified_runner",
    "__file__": str(Path(__file__).resolve()),
    "__package__": None,
}
exec(compile(_SOURCE, str(Path(__file__).resolve()), "exec"), _RE2)


def _load_canonical_termination_reason():
    module_name = (
        "isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_lifecycle_transition_contract"
    )
    path = SCAN / "assignment_lifecycle_transition_contract.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("STOP — B2-T4-RE2 CANONICAL-REASON-MODULE-SPEC")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            del sys.modules[module_name]
        else:
            sys.modules[module_name] = previous
    return module.TerminationReason


_BASE_RUN_STATIC = _RE2["run_static"]


def run_static() -> dict[str, object]:
    result = dict(_BASE_RUN_STATIC())
    source_identity = dict(result["qualified_source_identity"])
    test_side = dict(source_identity["test_side"])
    test_side.update(
        {
            "re1_sr_qualified_candidate": _sha(RE1_CANDIDATE),
            "re2_harness": _sha(Path(__file__).resolve()),
            "sr_reason_grid_serializer": _sha(SR_SERIALIZER),
            "re1_tx001_s10": _sha(RE1_S10),
            "re2_transformed_source": RUNNER_DERIVATION["transformed_source_sha256"],
        }
    )
    source_identity["test_side"] = test_side
    result.update(
        {
            "qualified_source_identity": source_identity,
            "runner_derivation": RUNNER_DERIVATION,
            "live_reason_grid_schema": LIVE_REASON_GRID_SCHEMA,
            "live_classification_precedence_schema": LIVE_CLASSIFICATION_SCHEMA,
            "schema_documentation_discrepancy": {
                "historical_report_prose": "b2_t4_sr_termination_reason_grid_T_E_1_v1",
                "implementation_and_machine_authority": LIVE_REASON_GRID_SCHEMA,
                "semantic_change_made": False,
            },
        }
    )
    result["pass"] = bool(
        result.get("pass")
        and test_side["re1_sr_qualified_candidate"]
        == QUALIFIED_RE1_CANDIDATE_SHA256
        and test_side["sr_reason_grid_serializer"]
        == QUALIFIED_SR_SERIALIZER_SHA256
        and test_side["re1_tx001_s10"] == QUALIFIED_RE1_S10_SHA256
        and REASON_GRID_SCHEMA_VERSION == LIVE_REASON_GRID_SCHEMA
        and CLASSIFICATION_PRECEDENCE_SCHEMA_VERSION == LIVE_CLASSIFICATION_SCHEMA
    )
    return result


_RE2["run_static"] = run_static
_RE2["_INNER"]["run_static"] = run_static


def run_runner_readiness_replay(output_path: Path) -> dict[str, object]:
    payload_bytes = RE1_S10.read_bytes()
    if hashlib.sha256(payload_bytes).hexdigest() != QUALIFIED_RE1_S10_SHA256:
        raise RuntimeError(f"STOP — {STOP_READINESS}: RE1 S10 identity drift")
    payload = json.loads(payload_bytes.decode("utf-8"))
    payload_digest_before = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    TerminationReason = _load_canonical_termination_reason()
    _RE2["_INNER"]["_re2_canonical_termination_reason"] = TerminationReason
    _RE2["_ledger_counts"].clear()
    _RE2["_last_bridge_count"] = 0
    expected_ledgers = (
        "transaction",
        "episode_update_timeline",
        "lifecycle_task_progress",
        "terminal_reconciliation",
        "nonterminal_bootstrap",
        "learner_runtime_immutability",
        "training_metric",
        "rolling_health",
    )
    with tempfile.TemporaryDirectory(prefix="b2_t4_re2_readiness_") as directory:
        prefix = Path(directory) / "b2_t4_re2_runner_readiness"
        trigger = prefix.parent / f"{prefix.name}_tx1_s10.json"
        _RE2["_append_transaction_ledgers"](trigger, payload)
        ledgers: dict[str, object] = {}
        for name in expected_ledgers:
            path = prefix.parent / f"{prefix.name}_{name}_ledger.jsonl"
            rows = _RE2["_read_jsonl"](path)
            ledgers[name] = {
                "rows": len(rows),
                "sha256": _sha(path),
                "payload": rows,
            }
        bootstrap = ledgers["nonterminal_bootstrap"]["payload"][0]
        transaction = ledgers["transaction"]["payload"][0]
    raw = json.loads(RE1_RAW_RESULT.read_text(encoding="utf-8"))
    adjudication = json.loads(RE1_ADJUDICATION.read_text(encoding="utf-8"))
    precedence = _RE2["classification_precedence_metadata_v1"](
        raw_worker_classification=str(raw["classification"]),
        final_phase_classification=str(adjudication["classification"]),
        adjudication_source=RE1_ADJUDICATION.name,
    )
    payload_digest_after = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    result = {
        "schema_version": "b2_t4_re2_runner_readiness_replay_v1",
        "status": "PASS",
        "classification": "PHASE-B2-T4-RE2-RUNNER-BOOKKEEPING-READINESS-QUALIFIED",
        "runner_path": str(Path(__file__).resolve()),
        "runner_sha256": _sha(Path(__file__).resolve()),
        "runner_derivation": RUNNER_DERIVATION,
        "historical_input_path": str(RE1_S10),
        "historical_input_sha256": _sha(RE1_S10),
        "canonical_shape": bootstrap["termination_reason_grid_shape"],
        "reason_grid_schema": bootstrap["termination_reason_grid_schema"],
        "serialization_pass": bootstrap["termination_reason_grid"]
        == payload["termination_reason_grid"],
        "transaction_ledger_pass": bool(
            transaction["transaction_index"] == 1
            and transaction["s7_s8_s9_s10"] == [True, True, True, True]
        ),
        "bookkeeping_ledgers": ledgers,
        "all_expected_bookkeeping_ledgers_pass": all(
            row["rows"] == 1 for row in ledgers.values()
        ),
        "classification_metadata": precedence,
        "classification_metadata_pass": precedence[
            "classification_precedence_schema"
        ]
        == LIVE_CLASSIFICATION_SCHEMA,
        "source_payload_mutations": int(payload_digest_before != payload_digest_after),
        "learner_mutations": 0,
        "AppLauncher": 0,
        "real_isaac_environments": 0,
        "cuda_cublas_probes": 0,
    }
    result["pass"] = bool(
        result["canonical_shape"] == [2, 2, 1]
        and result["reason_grid_schema"] == LIVE_REASON_GRID_SCHEMA
        and result["serialization_pass"]
        and result["transaction_ledger_pass"]
        and result["all_expected_bookkeeping_ledgers_pass"]
        and result["classification_metadata_pass"]
        and result["source_payload_mutations"] == 0
        and result["learner_mutations"] == 0
    )
    if not result["pass"]:
        result["status"] = "STOP"
        result["classification"] = STOP_READINESS
    _atomic_json(output_path, result)
    return result


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--runner-readiness-replay":
        result = run_runner_readiness_replay(Path(sys.argv[2]).resolve())
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0 if result["pass"] else 2
    return int(_RE2["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
