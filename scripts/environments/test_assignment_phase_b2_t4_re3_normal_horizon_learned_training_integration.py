"""Fresh B2-T4-RE3 normal-horizon learned-training integration qualification."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Mapping

import test_assignment_phase_b2_t4_re2_normal_horizon_learned_training_integration as RE2


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
DATE_ROOT = SCAN / "AgentRead" / "202609" / "20260915"
RE2_WRAPPER = HERE / "test_assignment_phase_b2_t4_re2_normal_horizon_learned_training_integration.py"
SR_SERIALIZER = HERE / "_assignment_phase_b2_t4_sr_reason_grid_serializer.py"
ZD_SUITE = HERE / "test_assignment_phase_b2_t4_zd_continuation_only_zero_dvm_contract.py"
RE1_S10 = (
    SCAN
    / "AgentRead"
    / "202609"
    / "20260913"
    / "b2_t4_re1_artifacts"
    / "b2_t4_re1_tx1_s10.json"
)
RE2_TX2 = (
    SCAN
    / "AgentRead"
    / "202609"
    / "20260914"
    / "b2_t4_re2_artifacts"
    / "b2_t4_re2_normal_horizon_20260914_formal01_tx2_rollout_decision_evidence.json"
)

QUALIFIED_RE2_WRAPPER_SHA256 = "263d48ca5988ab809ff63c5e11b4c8364d04159bd0cd96f4e0675d2465f8b40b"
QUALIFIED_SR_SERIALIZER_SHA256 = "dcf780a37387e24b4cc3c1f5ee39d006029b04875bc6422c96896cddd8cb5358"
QUALIFIED_ZD_SUITE_SHA256 = "a7293d97569ff70d9c487d8a3f67467205ceb0affa8cb270b78f637a172b2438"
QUALIFIED_RE1_S10_SHA256 = "e21591961c59e60a71cd9f27b6515a3f266bd7ac869ecff51e8b1600761e5649"
QUALIFIED_RE2_TX2_SHA256 = "93b4624167ce8b8dd052e4d3ab4c3cf105b34cd1a140ee840313edc2f8935fda"
OLD_FULL_SHA256 = "a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de"
OLD_ADAPTER_SHA256 = "b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014"
ZD_FULL_SHA256 = "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7"
ZD_ADAPTER_SHA256 = "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac"
SENTINELS = frozenset((1, 2, 3, 10, 25, 50, 75, 100, 125, 150, 160))
PASS = (
    "PHASE-B2-T4-RE3-NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-"
    "QUALIFIED-AWAITING-GPT-REVIEW"
)
STOP_READINESS = "PHASE-B2-T4-RE3-STOP-RUNNER-READINESS-NOT-QUALIFIED"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _replace_exact(source: str, old: str, new: str, *, count: int | None = None) -> str:
    observed = source.count(old)
    expected = observed if count is None else count
    if observed == 0 or observed != expected:
        raise RuntimeError(
            "STOP — B2-T4-RE3 QUALIFIED-TEST-SOURCE-DRIFT: "
            f"expected {expected} occurrences, observed {observed}: {old!r}"
        )
    return source.replace(old, new)


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8", newline="\n")
    temporary.replace(path)


def _qualified_re3_source() -> tuple[str, dict[str, object]]:
    identities = {
        "re2_wrapper": _sha(RE2_WRAPPER),
        "sr_serializer": _sha(SR_SERIALIZER),
        "zd_suite": _sha(ZD_SUITE),
        "re1_s10": _sha(RE1_S10),
        "re2_tx2": _sha(RE2_TX2),
    }
    expected = {
        "re2_wrapper": QUALIFIED_RE2_WRAPPER_SHA256,
        "sr_serializer": QUALIFIED_SR_SERIALIZER_SHA256,
        "zd_suite": QUALIFIED_ZD_SUITE_SHA256,
        "re1_s10": QUALIFIED_RE1_S10_SHA256,
        "re2_tx2": QUALIFIED_RE2_TX2_SHA256,
    }
    if identities != expected:
        raise RuntimeError(
            f"STOP — B2-T4-RE3 QUALIFIED-TEST-SOURCE-DRIFT: {identities!r} != {expected!r}"
        )
    source = RE2._SOURCE
    transform_counts = {
        "uppercase_re2": source.count("RE2"),
        "lowercase_re2": source.count("re2"),
        "date_20260914": source.count("20260914"),
        "old_full_hash": source.count(OLD_FULL_SHA256),
        "old_adapter_hash": source.count(OLD_ADAPTER_SHA256),
    }
    if not all(value > 0 for value in transform_counts.values()):
        raise RuntimeError(
            f"STOP — B2-T4-RE3 QUALIFIED-TEST-SOURCE-DRIFT: {transform_counts!r}"
        )
    transformed = source.replace("RE2", "RE3").replace("re2", "re3")
    transformed = transformed.replace("20260914", "20260915")
    transformed = _replace_exact(transformed, OLD_FULL_SHA256, ZD_FULL_SHA256, count=1)
    transformed = _replace_exact(transformed, OLD_ADAPTER_SHA256, ZD_ADAPTER_SHA256, count=1)
    transformed = _replace_exact(
        transformed,
        "SENTINEL_TRANSACTIONS = frozenset((1, 10, 25, 50, 75, 100, 125, 150, 160))",
        "SENTINEL_TRANSACTIONS = frozenset((1, 2, 3, 10, 25, 50, 75, 100, 125, 150, 160))",
        count=1,
    )
    receipt = {
        "schema_version": "b2_t4_re3_runner_derivation_v1",
        "source_wrapper": str(RE2_WRAPPER),
        "source_wrapper_sha256": identities["re2_wrapper"],
        "source_generated_re2_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "transform_counts": transform_counts,
        "transformed_source_sha256": hashlib.sha256(transformed.encode("utf-8")).hexdigest(),
        "qualified_dependencies": identities,
        "zd_production_sha256": {
            "assignment_event_training_full_transaction.py": ZD_FULL_SHA256,
            "assignment_event_training_real_isaac_adapter.py": ZD_ADAPTER_SHA256,
        },
        "sentinel_transactions": tuple(sorted(SENTINELS)),
        "production_semantic_modifications": 0,
    }
    return transformed, receipt


_SOURCE, RUNNER_DERIVATION = _qualified_re3_source()
_RE3: dict[str, object] = {
    "__name__": "_phase_b2_t4_re3_qualified_runner",
    "__file__": str(Path(__file__).resolve()),
    "__package__": None,
}
exec(compile(_SOURCE, str(Path(__file__).resolve()), "exec"), _RE3)

_BASE_RUN_STATIC = _RE3["run_static"]
_BASE_APPEND_TRANSACTION_LEDGERS = _RE3["_append_transaction_ledgers"]
_BASE_FIND_WITNESSES = _RE3["_find_witnesses"]
_BASE_POSTPROCESS_SUCCESS = _RE3["_postprocess_success"]


def _load_canonical_termination_reason():
    module_name = (
        "isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_lifecycle_transition_contract"
    )
    path = SCAN / "assignment_lifecycle_transition_contract.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("STOP — B2-T4-RE3 CANONICAL-REASON-MODULE-SPEC")
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


def run_static() -> dict[str, object]:
    result = dict(_BASE_RUN_STATIC())
    current = {
        "assignment_event_training_full_transaction.py": _sha(
            SCAN / "assignment_event_training_full_transaction.py"
        ),
        "assignment_event_training_real_isaac_adapter.py": _sha(
            SCAN / "assignment_event_training_real_isaac_adapter.py"
        ),
    }
    expected = {
        "assignment_event_training_full_transaction.py": ZD_FULL_SHA256,
        "assignment_event_training_real_isaac_adapter.py": ZD_ADAPTER_SHA256,
    }
    result.update(
        {
            "runner_derivation": RUNNER_DERIVATION,
            "re3_wrapper_sha256": _sha(Path(__file__).resolve()),
            "zd_production_identity": current,
            "zd_production_identity_pass": current == expected,
            "actor_evidence_receipt_fields": (
                "actor_expected_training_rows",
                "actor_observed_training_rows",
                "actor_evidence_reconciliation_digest",
            ),
        }
    )
    result["pass"] = bool(result.get("pass") and current == expected)
    return result


_RE3["run_static"] = run_static
_RE3["_INNER"]["run_static"] = run_static


def _actor_evidence_row(payload: Mapping[str, object]) -> dict[str, object]:
    normalized = _RE3["V2"].normalize(payload)
    audit = normalized["transaction"]["real_audit"]
    expected = tuple(tuple(int(value) for value in row) for row in audit["actor_expected_training_rows"])
    observed = tuple(tuple(int(value) for value in row) for row in audit["actor_observed_training_rows"])
    digest = str(audit["actor_evidence_reconciliation_digest"])
    exact = bool(expected == observed and len(expected) == 3 and len(digest) == 64)
    if not exact:
        raise RuntimeError(
            "STOP — B2-T4-RE3 ACTOR-EVIDENCE-CONTRADICTION: "
            f"expected={expected!r}, observed={observed!r}, digest={digest!r}"
        )
    return {
        "schema_version": "b2_t4_re3_actor_evidence_ledger_v1",
        "transaction_index": int(normalized["transaction_index"]),
        "update_id": str(normalized["update_id"]),
        "expected_training_rows_by_actor": expected,
        "observed_training_rows_by_actor": observed,
        "reconciliation_digest": digest,
        "exact_match": True,
        "faults": 0,
    }


def _append_transaction_ledgers(path: Path, payload: Mapping[str, object]) -> None:
    actor_row = _actor_evidence_row(payload)
    _BASE_APPEND_TRANSACTION_LEDGERS(path, payload)
    tx = int(actor_row["transaction_index"])
    prefix = _RE3["_prefix"](path, f"_tx{tx}_s10.json")
    ledger = prefix.parent / f"{prefix.name}_actor_evidence_reconciliation_ledger.jsonl"
    _RE3["_append_jsonl"](ledger, actor_row)
    _RE3["_ledger_counts"]["actor_evidence_reconciliation"] += 1
    readback = _RE3["_read_jsonl"](ledger)
    if len(readback) != tx or readback[-1] != _RE3["V2"].normalize(actor_row):
        raise RuntimeError("STOP — B2-T4-RE3 ACTOR-EVIDENCE-LEDGER-READBACK")


_RE3["_append_transaction_ledgers"] = _append_transaction_ledgers


def _find_witnesses(prefix: Path) -> dict[str, object]:
    result = dict(_BASE_FIND_WITNESSES(prefix))
    ledger = prefix.parent / f"{prefix.name}_actor_evidence_reconciliation_ledger.jsonl"
    rows = _RE3["_read_jsonl"](ledger)
    actor_pass = bool(
        len(rows) == 160
        and all(bool(row["exact_match"]) and int(row["faults"]) == 0 for row in rows)
    )
    result["ACTOR_EVIDENCE_RECONCILIATION"] = {
        "pass": actor_pass,
        "rows": len(rows),
        "required": 160,
        "faults": sum(int(row["faults"]) for row in rows),
    }
    result["pass"] = bool(result.get("pass") and actor_pass)
    return result


_RE3["_find_witnesses"] = _find_witnesses


def _postprocess_success(prefix: Path, result_path: Path) -> dict[str, object]:
    final = dict(_BASE_POSTPROCESS_SUCCESS(prefix, result_path))
    witnesses = final["primary_witnesses"]
    witness_names = {
        "W1_cross_update_ownership.json": "W1_CROSS_UPDATE_OWNERSHIP",
        "W2_multi_update_task_completion.json": "W2_MULTI_UPDATE_COMPLETION",
        "W3_real_zero_dvm_actor.json": "W3_ZERO_DVM_ACTOR",
        "W4_real_nonterminal_bootstrap.json": "W4_NONTERMINAL_BOOTSTRAP",
        "W5_normal_horizon_terminal_autoreset.json": "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
        "W6_post_autoreset_training.json": "W6_POST_AUTORESET_TRAINING",
        "W7_learner_runtime_p2_immutability.json": "W7_RUNTIME_P2_IMMUTABILITY",
    }
    for filename, key in witness_names.items():
        _atomic_json(prefix.parent / filename, witnesses[key])
    actor_ledger = prefix.parent / f"{prefix.name}_actor_evidence_reconciliation_ledger.jsonl"
    actor_inventory = {
        "path": str(actor_ledger),
        "rows": len(_RE3["_read_jsonl"](actor_ledger)),
        "bytes": actor_ledger.stat().st_size,
        "sha256": _sha(actor_ledger),
    }
    final_path = prefix.parent / f"{prefix.name}_final_result.json"
    final = json.loads(final_path.read_text(encoding="utf-8"))
    final.update(
        {
            "classification": PASS,
            "actor_evidence_reconciliation_ledger": actor_inventory,
            "actor_evidence_reconciliation_faults": 0,
            "sentinel_transactions": tuple(sorted(SENTINELS)),
            "production_semantic_modifications": 0,
            "transaction_161_started": False,
        }
    )
    _RE3["_base_atomic_json"](final_path, final)
    worker = json.loads(result_path.read_text(encoding="utf-8"))
    worker.update(
        {
            "classification": PASS,
            "actor_evidence_reconciliation_ledger": actor_inventory,
            "actor_evidence_reconciliation_faults": 0,
        }
    )
    _RE3["_base_atomic_json"](result_path, worker)
    return final


_RE3["_postprocess_success"] = _postprocess_success


def run_runner_readiness_replay(output_path: Path) -> dict[str, object]:
    # ZD's pure-test dependency chain installs synthetic isaaclab_tasks package
    # placeholders.  Keep that import inside the pure readiness path so a formal
    # worker reaches AppLauncher with the canonical task package still importable.
    import test_assignment_phase_b2_t4_zd_continuation_only_zero_dvm_contract as ZD

    static = run_static()
    if not static["pass"]:
        raise RuntimeError(f"STOP — {STOP_READINESS}: static authority failed")
    TerminationReason = _load_canonical_termination_reason()
    # The qualified RE2-to-RE3 source transform also advances this private
    # runtime binding name from ``_re2_*`` to ``_re3_*``.
    _RE3["_INNER"]["_re3_canonical_termination_reason"] = TerminationReason
    historical_payload = json.loads(RE1_S10.read_text(encoding="utf-8"))
    historical_before = _sha(RE1_S10)
    _RE3["_ledger_counts"].clear()
    with tempfile.TemporaryDirectory(prefix="b2_t4_re3_readiness_") as directory:
        prefix = Path(directory) / "b2_t4_re3_re1_bookkeeping"
        trigger = prefix.parent / f"{prefix.name}_tx1_s10.json"
        _BASE_APPEND_TRANSACTION_LEDGERS(trigger, historical_payload)
        ledger_names = (
            "transaction",
            "episode_update_timeline",
            "lifecycle_task_progress",
            "terminal_reconciliation",
            "nonterminal_bootstrap",
            "learner_runtime_immutability",
            "training_metric",
            "rolling_health",
        )
        re1_ledgers = {
            name: len(
                _RE3["_read_jsonl"](
                    prefix.parent / f"{prefix.name}_{name}_ledger.jsonl"
                )
            )
            for name in ledger_names
        }
    actor_rich, re2_replay = ZD.positive_re2_sequence()
    zero = re2_replay["source_faithful_replay"]
    result = {
        "schema_version": "b2_t4_re3_runner_readiness_replay_v1",
        "status": "PASS",
        "classification": "PHASE-B2-T4-RE3-RUNNER-READINESS-QUALIFIED",
        "static_authority": static,
        "runner_derivation": RUNNER_DERIVATION,
        "re1_sr_bookkeeping_replay": {
            "historical_input_sha256": historical_before,
            "historical_input_unchanged": _sha(RE1_S10) == historical_before,
            "ledger_rows": re1_ledgers,
            "all_ledgers_pass": all(count == 1 for count in re1_ledgers.values()),
        },
        "re2_zd_replay": {
            "historical_input_sha256": _sha(RE2_TX2),
            "historical_input_unchanged": _sha(RE2_TX2) == QUALIFIED_RE2_TX2_SHA256,
            "actor_rich_setup_pass": actor_rich["status"] == "PASS",
            "expected_actor_populations": zero["expected_actor_population"],
            "observed_actor_populations": zero["observed_actor_population"],
            "actor_backward": zero["actor_backward"],
            "actor_optimizer_step": zero["actor_optimizer_step"],
            "actor_adam_delta": zero["actor_adam_delta"],
            "factor": zero["factor"],
            "critic_backward": zero["critic_backward"],
            "critic_optimizer_step": zero["critic_optimizer_step"],
            "valuenorm_update": zero["valuenorm_update"],
            "event_returns": zero["event_returns"],
            "s7_s8_s9_s10": zero["s7_s8_s9_s10"],
            "pass": bool(
                zero["expected_actor_population"] == ((0, 0), (1, 0), (2, 0))
                and zero["observed_actor_population"] == ((0, 0), (1, 0), (2, 0))
                and zero["actor_backward"] == (0, 0, 0)
                and zero["actor_optimizer_step"] == (0, 0, 0)
                and zero["factor"] == "IDENTITY"
                and zero["critic_backward"] > 0
                and zero["critic_optimizer_step"] > 0
                and zero["valuenorm_update"] > 0
                and zero["s7_s8_s9_s10"] == [True, True, True, True]
            ),
        },
        "synthetic_cpu_full_transactions": 2,
        "historical_runtime_learner_mutations": 0,
        "AppLauncher": 0,
        "real_isaac_environments": 0,
        "cuda_cublas_probes": 0,
    }
    result["pass"] = bool(
        result["re1_sr_bookkeeping_replay"]["all_ledgers_pass"]
        and result["re1_sr_bookkeeping_replay"]["historical_input_unchanged"]
        and result["re2_zd_replay"]["pass"]
        and result["re2_zd_replay"]["historical_input_unchanged"]
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
    return int(_RE3["main"]())


if __name__ == "__main__":
    raise SystemExit(main())
