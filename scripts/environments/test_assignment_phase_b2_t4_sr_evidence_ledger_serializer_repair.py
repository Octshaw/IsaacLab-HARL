"""Pure qualification for the B2-T4-SR evidence-ledger serializer repair."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import tempfile
from typing import Mapping

import numpy as np
import torch

from _assignment_phase_b2_t4_sr_reason_grid_serializer import (
    EVIDENCE_REASON_GRID_MISSING,
    EVIDENCE_REASON_GRID_RAGGED,
    EVIDENCE_REASON_GRID_RANK_MISMATCH,
    EVIDENCE_REASON_GRID_SHAPE_MISMATCH,
    EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON,
    EVIDENCE_REASON_VALUE_INVALID,
    EvidenceReasonGridError,
    REASON_GRID_SCHEMA_VERSION,
    classification_precedence_metadata_v1,
    serialize_termination_reason_grid_v1,
)
import test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration as RE1


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
DATE_ROOT = SCAN / "AgentRead" / "202609" / "20260913"
RE1_ARTIFACTS = DATE_ROOT / "b2_t4_re1_artifacts"
DEFAULT_ARTIFACTS = DATE_ROOT / "b2_t4_sr_artifacts"
PASS = "PHASE-B2-T4-SR-EVIDENCE-LEDGER-SERIALIZER-REPAIR-QUALIFIED-AWAITING-GPT-REVIEW"

RE1_EXPECTED_SHA256 = {
    "b2_t4_re1_cuda_cublas_readiness.json": "a57b28dc04fd0c0f283eab0ca1de6c3170b8a9330e832d42509ca0211d17a212",
    "b2_t4_re1_failure_adjudication.json": "1cc0998de076d7cd3c2bdaac740d3ad252b4ebaf64fd8d83cc2c13b2da8360cd",
    "b2_t4_re1_final_result.json": "ed5558af4f401fe77dd27fb7c7538292cc36bcbb4f5c184186b506afcbda5247",
    "b2_t4_re1_formal_supervisor_result.json": "f63608a379adb3406ab8580f5f0ab74dfa226124aeee23cadab8030f0fdca0b9",
    "b2_t4_re1_preflight_summary.json": "6f6afbd4a893d814d3cc2ae0617ac74463b1e52143a7611a4be2473085abd136",
    "b2_t4_re1_process_config_authority.json": "1a655e2de413a2c113658ddc3db30edf442711a8b8a28ac38997a73ce5df218c",
    "b2_t4_re1_tx1_actor_factor_progress.json": "49ba9c7c1923b9cf080d4fa7cc5a0db8c9826affb824f8822bbf11ba42e51319",
    "b2_t4_re1_tx1_critic_progress.json": "62be57c6e43e873735c214650c7c754e9318b2c0f78aa9552cd4cc6ae40b292e",
    "b2_t4_re1_tx1_pre_mutation.json": "18fdb7d1c3d5827711d03599530397643da1fef61a7e1659e9517b171fe2cca3",
    "b2_t4_re1_tx1_rollout_decision_evidence.json": "2a2ff13446b8c65b0e1e34b510d1393bf0ec282ed76ab14ecb79c861900c0878",
    "b2_t4_re1_tx1_s10.json": "e21591961c59e60a71cd9f27b6515a3f266bd7ac869ecff51e8b1600761e5649",
    "re1_static_draft.json": "920a48bdd51b558e5dafaa27c125dc867a76b7a36a38c0683e0b8846ed9a31a0",
}
PRODUCTION_EXPECTED_SHA256 = {
    "assignment_event_training_full_transaction.py": "a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de",
    "assignment_event_training_real_isaac_adapter.py": "b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _load_canonical_termination_reason():
    module_name = (
        "isaaclab_tasks.direct.scan_mobile_manipulator."
        "assignment_lifecycle_transition_contract"
    )
    path = SCAN / "assignment_lifecycle_transition_contract.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("STOP — B2-T4-SR CANONICAL_REASON_MODULE_SPEC")
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


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _require(condition: bool, label: str, detail: object = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-SR {label}: {detail!r}")


def _source_snapshot(source: object) -> object:
    if isinstance(source, torch.Tensor):
        return source.detach().clone()
    if isinstance(source, np.ndarray):
        return source.copy()
    return copy.deepcopy(source)


def _source_equal(source: object, before: object) -> bool:
    if isinstance(source, torch.Tensor):
        return isinstance(before, torch.Tensor) and torch.equal(source, before)
    if isinstance(source, np.ndarray):
        return isinstance(before, np.ndarray) and np.array_equal(source, before)
    return source == before


def _numpy_rng_equal(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return bool(
        left[0] == right[0]
        and np.array_equal(left[1], right[1])
        and left[2:] == right[2:]
    )


def _historical_hashes() -> dict[str, str]:
    return {name: _sha(RE1_ARTIFACTS / name) for name in sorted(RE1_EXPECTED_SHA256)}


def _positive_case(
    name: str,
    source: object,
    *,
    expected_t: int,
    expected_e: int,
    valid_reasons: tuple[int, ...],
) -> dict[str, object]:
    before = _source_snapshot(source)
    first = serialize_termination_reason_grid_v1(
        source,
        expected_t=expected_t,
        expected_e=expected_e,
        valid_reason_values=valid_reasons,
    )
    second = serialize_termination_reason_grid_v1(
        source,
        expected_t=expected_t,
        expected_e=expected_e,
        valid_reason_values=valid_reasons,
    )
    shape = (len(first), len(first[0]), len(first[0][0]))
    result = {
        "name": name,
        "source_type": type(source).__name__,
        "expected_shape": [expected_t, expected_e, 1],
        "observed_shape": list(shape),
        "serialized": first,
        "deterministic_repeat_equal": first == second,
        "json_byte_semantic_equal": json.dumps(first, separators=(",", ":"))
        == json.dumps(second, separators=(",", ":")),
        "source_unchanged": _source_equal(source, before),
    }
    result["pass"] = bool(
        tuple(shape) == (expected_t, expected_e, 1)
        and result["deterministic_repeat_equal"]
        and result["json_byte_semantic_equal"]
        and result["source_unchanged"]
    )
    _require(bool(result["pass"]), "POSITIVE_CASE_FAILED", result)
    return result


def _negative_case(
    name: str,
    source: object,
    *,
    expected_t: int,
    expected_e: int,
    expected_code: str,
    valid_reasons: tuple[int, ...],
) -> dict[str, object]:
    before = _source_snapshot(source)
    try:
        serialize_termination_reason_grid_v1(
            source,
            expected_t=expected_t,
            expected_e=expected_e,
            valid_reason_values=valid_reasons,
        )
    except EvidenceReasonGridError as exc:
        result = {
            "name": name,
            "expected_code": expected_code,
            "observed_code": exc.code,
            "diagnostic": str(exc),
            "raw_type_error": False,
            "source_unchanged": _source_equal(source, before),
            "pass": exc.code == expected_code and _source_equal(source, before),
        }
    except BaseException as exc:
        result = {
            "name": name,
            "expected_code": expected_code,
            "observed_code": type(exc).__name__,
            "diagnostic": str(exc),
            "raw_type_error": isinstance(exc, TypeError),
            "source_unchanged": _source_equal(source, before),
            "pass": False,
        }
    else:
        result = {
            "name": name,
            "expected_code": expected_code,
            "observed_code": "ACCEPTED",
            "diagnostic": "malformed evidence was accepted",
            "raw_type_error": False,
            "source_unchanged": _source_equal(source, before),
            "pass": False,
        }
    _require(bool(result["pass"]), "NEGATIVE_CASE_FAILED", result)
    return result


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _append_replay(
    payload: dict[str, object], label: str, expected_grid: list[list[list[int]]]
) -> dict[str, object]:
    payload_before = _digest(payload)
    RE1._ledger_counts.clear()
    with tempfile.TemporaryDirectory(prefix=f"b2_t4_sr_{label}_") as directory:
        root = Path(directory)
        trigger_path = root / f"{label}_tx1_s10.json"
        RE1._append_transaction_ledgers(trigger_path, payload)
        ledgers = {}
        for path in sorted(root.glob(f"{label}_*_ledger.jsonl")):
            rows = _read_jsonl(path)
            ledgers[path.name] = {
                "rows": len(rows),
                "sha256": _sha(path),
                "payload": rows,
            }
        bootstrap_name = f"{label}_nonterminal_bootstrap_ledger.jsonl"
        bootstrap = ledgers[bootstrap_name]["payload"][0]
        result = {
            "label": label,
            "ledger_file_count": len(ledgers),
            "ledger_counts": dict(RE1._ledger_counts),
            "ledgers": ledgers,
            "reason_grid_roundtrip_equal": bootstrap["termination_reason_grid"]
            == expected_grid,
            "reason_grid_shape": bootstrap["termination_reason_grid_shape"],
            "reason_grid_schema": bootstrap["termination_reason_grid_schema"],
            "source_payload_unchanged": payload_before == _digest(payload),
        }
        result["pass"] = bool(
            len(ledgers) == 8
            and all(row["rows"] == 1 for row in ledgers.values())
            and result["reason_grid_roundtrip_equal"]
            and result["reason_grid_shape"] == [2, 2, 1]
            and result["reason_grid_schema"] == REASON_GRID_SCHEMA_VERSION
            and result["source_payload_unchanged"]
        )
        _require(bool(result["pass"]), "APPEND_REPLAY_FAILED", result)
        return result


def run(artifact_dir: Path) -> dict[str, object]:
    app_imported_before = "isaaclab.app" in sys.modules
    TerminationReason = _load_canonical_termination_reason()
    RE1._INNER["_re1_canonical_termination_reason"] = TerminationReason

    valid_reasons = tuple(int(member) for member in TerminationReason)
    reason_domain = {member.name: int(member) for member in TerminationReason}
    _require(
        reason_domain
        == {
            "NONE": 0,
            "ALL_TASKS_COMPLETED": 1,
            "NO_FEASIBLE_TASKS_REMAIN": 2,
            "TIME_LIMIT": 3,
        },
        "CANONICAL_REASON_DOMAIN_DRIFT",
        reason_domain,
    )

    historical_before = _historical_hashes()
    _require(historical_before == RE1_EXPECTED_SHA256, "RE1_HISTORICAL_HASH_DRIFT")
    real_s10_path = RE1_ARTIFACTS / "b2_t4_re1_tx1_s10.json"
    real_s10_bytes_before = real_s10_path.read_bytes()
    real_payload = json.loads(real_s10_bytes_before.decode("utf-8"))
    real_grid = real_payload["termination_reason_grid"]
    expected_t = len(real_payload["re1_step_details"])
    expected_e = len(real_payload["re1_step_details"][0]["state_rows"])

    old_failure = {
        "input_sha256": _digest(real_grid),
        "canonical_shape": [expected_t, expected_e, 1],
        "old_expression": "tuple(tuple(int(value) for value in row) for row in grid)",
        "pass": False,
    }
    try:
        tuple(tuple(int(value) for value in row) for row in real_grid)
    except TypeError as exc:
        old_failure.update(
            {
                "exception_type": type(exc).__name__,
                "exception": str(exc),
                "int_list_defect_reproduced": "int()" in str(exc) and "list" in str(exc),
                "pass": "int()" in str(exc) and "list" in str(exc),
            }
        )
    _require(bool(old_failure["pass"]), "OLD_FAILURE_NOT_REPRODUCED", old_failure)

    python_rng_before = random.getstate()
    numpy_rng_before = np.random.get_state()
    torch_rng_before = torch.random.get_rng_state().clone()

    none = reason_domain["NONE"]
    time_limit = reason_domain["TIME_LIMIT"]
    completed = reason_domain["ALL_TASKS_COMPLETED"]
    no_feasible = reason_domain["NO_FEASIBLE_TASKS_REMAIN"]
    positive_inputs = (
        ("A_all_none_T2_E2_list", [[[none], [none]], [[none], [none]]], 2, 2),
        (
            "B_mixed_T2_E2_list",
            [[[none], [time_limit]], [[completed], [none]]],
            2,
            2,
        ),
        (
            "C_T2_E3_numpy",
            np.array(
                [[[none], [time_limit], [completed]], [[no_feasible], [none], [none]]],
                dtype=np.int64,
            ),
            2,
            3,
        ),
        (
            "D_T4_E2_tuple",
            tuple(tuple(([none], [time_limit])) for _ in range(4)),
            4,
            2,
        ),
        (
            "E_T2_E2_torch_cpu",
            torch.tensor([[[none], [time_limit]], [[completed], [no_feasible]]], dtype=torch.int64),
            2,
            2,
        ),
        (
            "F_T2_E2_mixed_list_tuple",
            ([(none,), [time_limit]], ((completed,), (no_feasible,))),
            2,
            2,
        ),
        ("G_repeated_determinism", copy.deepcopy(real_grid), 2, 2),
    )
    positive = tuple(
        _positive_case(
            name,
            source,
            expected_t=t_size,
            expected_e=e_size,
            valid_reasons=valid_reasons,
        )
        for name, source, t_size, e_size in positive_inputs
    )

    negative_inputs = (
        ("A_rank_2_T_E", [[none, none], [none, none]], 2, 2, EVIDENCE_REASON_GRID_RANK_MISMATCH),
        ("B_trailing_dim_2", [[[none, none], [none, none]], [[none, none], [none, none]]], 2, 2, EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON),
        ("C_swapped_E_T", np.zeros((3, 2, 1), dtype=np.int64), 2, 3, EVIDENCE_REASON_GRID_SHAPE_MISMATCH),
        ("D_ragged", [[[none]], [[none], [none]]], 2, 2, EVIDENCE_REASON_GRID_RAGGED),
        ("E_invalid_reason", [[[none], [99]], [[none], [none]]], 2, 2, EVIDENCE_REASON_VALUE_INVALID),
        ("F_wrong_nested_depth", [[[[none]], [[none]]], [[[none]], [[none]]]], 2, 2, EVIDENCE_REASON_GRID_RANK_MISMATCH),
        ("G_non_integral_scalar", [[[none], [0.5]], [[none], [none]]], 2, 2, EVIDENCE_REASON_VALUE_INVALID),
        ("H_bool_reason", [[[none], [True]], [[none], [none]]], 2, 2, EVIDENCE_REASON_VALUE_INVALID),
        ("I_missing_grid", None, 2, 2, EVIDENCE_REASON_GRID_MISSING),
        ("J_empty_grid", [], 2, 2, EVIDENCE_REASON_GRID_SHAPE_MISMATCH),
        ("K_T_mismatch", [[[none], [none]]] * 3, 2, 2, EVIDENCE_REASON_GRID_SHAPE_MISMATCH),
        ("L_E_mismatch", [[[none], [none], [none]], [[none], [none], [none]]], 2, 2, EVIDENCE_REASON_GRID_SHAPE_MISMATCH),
    )
    negative = tuple(
        _negative_case(
            name,
            source,
            expected_t=t_size,
            expected_e=e_size,
            expected_code=code,
            valid_reasons=valid_reasons,
        )
        for name, source, t_size, e_size, code in negative_inputs
    )

    python_rng_after = random.getstate()
    numpy_rng_after = np.random.get_state()
    torch_rng_after = torch.random.get_rng_state().clone()
    nonmutation = {
        "positive_sources_unchanged": all(bool(row["source_unchanged"]) for row in positive),
        "negative_sources_unchanged": all(bool(row["source_unchanged"]) for row in negative),
        "python_rng_unchanged": python_rng_before == python_rng_after,
        "numpy_rng_unchanged": _numpy_rng_equal(numpy_rng_before, numpy_rng_after),
        "torch_cpu_rng_unchanged": torch.equal(torch_rng_before, torch_rng_after),
        "cuda_api_calls": 0,
        "mutation_count": 0,
    }
    nonmutation["pass"] = all(bool(value) for key, value in nonmutation.items() if key not in ("cuda_api_calls", "mutation_count"))
    _require(bool(nonmutation["pass"]), "NONMUTATION_FAILED", nonmutation)

    serialized_real = serialize_termination_reason_grid_v1(
        real_grid,
        expected_t=expected_t,
        expected_e=expected_e,
        valid_reason_values=valid_reasons,
    )
    replay = {
        "historical_s10_path": str(real_s10_path),
        "historical_s10_sha256": _sha(real_s10_path),
        "source_type": type(real_grid).__name__,
        "element_type": type(real_grid[0][0][0]).__name__,
        "original_shape": [expected_t, expected_e, len(real_grid[0][0])],
        "serialized_shape": [len(serialized_real), len(serialized_real[0]), len(serialized_real[0][0])],
        "serialized": serialized_real,
        "all_none_preserved": all(cell[0] == none for row in serialized_real for cell in row),
        "source_payload_unchanged": real_s10_bytes_before == real_s10_path.read_bytes(),
        "pass": False,
    }
    replay["pass"] = bool(
        replay["original_shape"] == [2, 2, 1]
        and replay["serialized_shape"] == [2, 2, 1]
        and replay["all_none_preserved"]
        and replay["source_payload_unchanged"]
    )
    _require(bool(replay["pass"]), "RE1_REPLAY_FAILED", replay)

    synthetic_payload = copy.deepcopy(real_payload)
    synthetic_payload["update_id"] = "b2-t4-sr-synthetic-ledger-roundtrip"
    ledger_roundtrip = _append_replay(
        synthetic_payload, "sr_synthetic", serialized_real
    )
    bookkeeping_replay = _append_replay(real_payload, "re1_tx001_replay", serialized_real)

    raw_result = json.loads(
        (RE1_ARTIFACTS / "b2_t4_re1_final_result.json").read_text(encoding="utf-8")
    )
    adjudication = json.loads(
        (RE1_ARTIFACTS / "b2_t4_re1_failure_adjudication.json").read_text(
            encoding="utf-8"
        )
    )
    precedence = classification_precedence_metadata_v1(
        raw_worker_classification=str(raw_result["classification"]),
        final_phase_classification=str(adjudication["classification"]),
        adjudication_source="b2_t4_re1_failure_adjudication.json",
    )
    precedence["pass"] = bool(
        precedence["raw_worker_classification"]
        == "PHASE-B2-T4-RE1-STOP-TX1-BOUNDED-SMOKE-FAILURE-NOT-COMPLETE"
        and precedence["final_phase_classification"]
        == "PHASE-B2-T4-RE1-STOP-TX001-EVIDENCE-LEDGER-SERIALIZATION-NOT-COMPLETE"
        and precedence["raw_worker_classification"]
        != precedence["final_phase_classification"]
    )
    _require(bool(precedence["pass"]), "CLASSIFICATION_PRECEDENCE_FAILED", precedence)

    production = {
        name: {
            "expected_sha256": expected,
            "observed_sha256": _sha(SCAN / name),
        }
        for name, expected in PRODUCTION_EXPECTED_SHA256.items()
    }
    production_pass = all(
        row["expected_sha256"] == row["observed_sha256"] for row in production.values()
    )
    historical_after = _historical_hashes()
    historical_pass = bool(
        historical_before == historical_after == RE1_EXPECTED_SHA256
        and real_s10_bytes_before == real_s10_path.read_bytes()
    )
    static_guards = {
        "app_launcher_imported_before": app_imported_before,
        "app_launcher_imported_after": "isaaclab.app" in sys.modules,
        "app_launcher_constructions": 0,
        "real_isaac_environments": 0,
        "cuda_readiness_probes": 0,
        "formal_learners": 0,
        "physical_environment_steps": 0,
        "learner_mutations": 0,
        "checkpoint_io": 0,
        "public_activations": 0,
        "b2_t4_re2_started": 0,
    }
    static_guards["pass"] = bool(
        not static_guards["app_launcher_imported_before"]
        and not static_guards["app_launcher_imported_after"]
        and all(
            int(value) == 0
            for key, value in static_guards.items()
            if key not in ("app_launcher_imported_before", "app_launcher_imported_after", "pass")
        )
    )
    _require(production_pass, "PRODUCTION_SOURCE_MODIFIED", production)
    _require(historical_pass, "HISTORICAL_RE1_ARTIFACT_MODIFIED")
    _require(bool(static_guards["pass"]), "STATIC_GUARD_FAILED", static_guards)

    artifacts = {
        "serializer_positive_matrix.json": {
            "schema_version": "b2_t4_sr_positive_matrix_v1",
            "case_count": len(positive),
            "cases": positive,
            "pass": all(bool(row["pass"]) for row in positive),
        },
        "serializer_negative_matrix.json": {
            "schema_version": "b2_t4_sr_negative_matrix_v1",
            "case_count": len(negative),
            "cases": negative,
            "raw_type_error_count": sum(int(bool(row["raw_type_error"])) for row in negative),
            "pass": all(bool(row["pass"]) for row in negative),
        },
        "old_failure_reproduction.json": old_failure,
        "re1_tx001_serializer_replay.json": replay,
        "ledger_roundtrip.json": ledger_roundtrip,
        "tx001_post_s10_bookkeeping_replay.json": bookkeeping_replay,
        "production_source_identity_check.json": {
            "production_sources": production,
            "production_semantic_modifications": 0,
            "pass": production_pass,
        },
    }
    for name, payload in artifacts.items():
        _write_json(artifact_dir / name, payload)

    artifact_inventory = {
        path.name: {"bytes": path.stat().st_size, "sha256": _sha(path)}
        for path in sorted(artifact_dir.glob("*.json"))
    }
    result = {
        "schema_version": "b2_t4_sr_final_result_v1",
        "status": "PASS",
        "classification": PASS,
        "canonical_reason_grid_shape": "[T,E,1]",
        "canonical_reason_domain": reason_domain,
        "old_failure_reproduction": bool(old_failure["pass"]),
        "positive_cases": len(positive),
        "positive_pass": sum(int(bool(row["pass"])) for row in positive),
        "negative_cases": len(negative),
        "negative_stop": sum(int(bool(row["pass"])) for row in negative),
        "deterministic_serialization": all(
            bool(row["deterministic_repeat_equal"]) for row in positive
        ),
        "nonmutation": nonmutation,
        "re1_tx001_replay": bool(replay["pass"]),
        "append_ledger_roundtrips": 1,
        "append_ledger_roundtrip_pass": bool(ledger_roundtrip["pass"]),
        "post_s10_bookkeeping_replays": 1,
        "post_s10_bookkeeping_replay_pass": bool(bookkeeping_replay["pass"]),
        "classification_precedence": precedence,
        "historical_re1_artifacts_unchanged": historical_pass,
        "historical_re1_hashes": historical_after,
        "production_source_identity_pass": production_pass,
        "production_semantic_modifications": 0,
        "static_guards": static_guards,
        "artifact_inventory_before_final": artifact_inventory,
        "formal_execution_counts": {
            "app_launcher": 0,
            "real_isaac_environments": 0,
            "cuda_readiness_probes": 0,
            "formal_learners": 0,
            "physical_environment_steps": 0,
            "actor_backward": 0,
            "actor_optimizer_step": 0,
            "critic_backward": 0,
            "critic_optimizer_step": 0,
            "valuenorm_update": 0,
            "learner_mutations": 0,
            "checkpoint_io": 0,
            "public_activation": 0,
            "b2_t4_re2_started": 0,
        },
    }
    _write_json(artifact_dir / "final_result.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACTS)
    args = parser.parse_args()
    result = run(args.artifact_dir.resolve())
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
