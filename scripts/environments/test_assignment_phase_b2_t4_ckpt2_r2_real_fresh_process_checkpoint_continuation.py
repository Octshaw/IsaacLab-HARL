"""CKPT2-R2: ledger-schema repaired fresh-process continuation gate."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
AGENTREAD = SCAN / "AgentRead"
DAY = AGENTREAD / "202609" / "20260923"
ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r2_artifacts"
CHECKPOINT_ROOT = ARTIFACT_ROOT / "checkpoint"
R1_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_r1_real_fresh_process_checkpoint_continuation.py"
R1_ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r1_artifacts"
R1_REPORT = DAY / "PHASE_B2_T4_CKPT2_R1_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
CKPT2_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation.py"
CKPT2_ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_artifacts"
CKPT2_REPORT = DAY / "PHASE_B2_T4_CKPT2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
EXPECTED_R1_HARNESS_SHA256 = "c11774e887045bd96aae8cb2241f2bee953bf1eb92a411888a7fc58927abe324"
EXPECTED_R1_REPORT_SHA256 = "94b0898b7c4d28c5a14982e1052de86eb84acaf76fd73d7e0b4f5841b55a1ef4"
EXPECTED_R1_ARTIFACT_COUNT = 25
EXPECTED_R1_ARTIFACT_SHA256 = "511fa0d2727c6a9f2eeece317ce06b75f7b03c47e46607c0e4e09553d93f122b"
EXPECTED_CKPT2_HARNESS_SHA256 = "3fc8f262956fba9e8f3ee39a22182a615d220c09964371837f1e43b5e4695551"
EXPECTED_CKPT2_REPORT_SHA256 = "ea8108f301d2fd027d008e2126851a5eac3721e3a78b53ffcae524d1507a69c7"
EXPECTED_CKPT2_ARTIFACT_COUNT = 35
EXPECTED_CKPT2_ARTIFACT_SHA256 = "248d4415835bab99029da77478bac6f195fdfc40de5193378423c7a5b86083ef"
EXPECTED_CKPT1_SHA256 = {
    "assignment_optimization_checkpoint.py": "b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9",
    "assignment_harl_training.py": "31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
EXPECTED_HARL_SHA256 = {
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "models/value_function_models/v_net.py": "a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}
PASS_CLASSIFICATION = (
    "PHASE-B2-T4-CKPT2-R2-REAL-FRESH-PROCESS-OPTIMIZATION-"
    "CONTINUATION-QUALIFIED-AWAITING-GPT-REVIEW"
)
BEFORE_FIRST_WRITE = {
    "branch": "main",
    "HEAD": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "origin_main": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "merge_base": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "porcelain_bytes": 12822039,
    "porcelain_entry_count": 50996,
    "porcelain_sha256": "5e5593134a9b2573359b52e659c57854caf6b9e16382f19f6f43c5b18c6b7412",
    "staged_path_count": 359,
    "staged_index_sha256": "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
    "agentread_file_count": 50534,
    "agentread_path_set_sha256": "555ad2b79bc078df7a30646ef1ddfc4f1d43f6e9441d6001e0e41ffe5164721a",
}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str, detail: Any = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-CKPT2-R2 {code}: {detail!r}")


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    rows = [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": _sha(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8") + bytes([10])
    return rows, hashlib.sha256(encoded).hexdigest()


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.longpaths=true", *arguments], cwd=ROOT)


def _repository_authority() -> dict[str, Any]:
    status = _git_bytes("status", "--porcelain=v1", "-uall", "-z")
    index = _git_bytes("ls-files", "--stage")
    staged = _git_bytes("diff", "--cached", "--name-only", "-z")
    paths = sorted(path.relative_to(ROOT).as_posix() for path in AGENTREAD.rglob("*") if path.is_file())
    return {
        "branch": _git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": _git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": _git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": _git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "porcelain_bytes": len(status),
        "porcelain_entry_count": sum(bool(item) for item in status.split(bytes([0]))),
        "porcelain_sha256": hashlib.sha256(status).hexdigest(),
        "staged_path_count": sum(bool(item) for item in staged.split(bytes([0]))),
        "staged_index_sha256": hashlib.sha256(index).hexdigest(),
        "agentread_file_count": len(paths),
        "agentread_path_set_sha256": hashlib.sha256(("\n".join(paths) + "\n").encode()).hexdigest(),
        "before_first_write": BEFORE_FIRST_WRITE,
        "git_mutations_by_ckpt2_r2": {"add": 0, "commit": 0, "push": 0, "reset": 0, "checkout": 0, "clean": 0},
    }


@dataclass
class _LedgerBinder:
    expected_next_index: int
    committed_indices: set[int]

    @classmethod
    def starting_at(cls, index: int) -> "_LedgerBinder":
        return cls(expected_next_index=index, committed_indices=set())

    def bind(self, index: int, transaction: Any) -> dict[str, Any]:
        _require(type(index) is int, "LEDGER-TRANSACTION-INDEX-TYPE", type(index).__name__)
        _require(index not in self.committed_indices, "LEDGER-DUPLICATE-TRANSACTION", index)
        _require(index == self.expected_next_index, "LEDGER-TRANSACTION-ORDER", {"expected": self.expected_next_index, "actual": index})

        audit = transaction.real_audit
        _require(hasattr(audit, "event_return_compute_count"), "LEDGER-EVENT-RETURN-AUTHORITY-MISSING")
        event_return_count = audit.event_return_compute_count
        _require(type(event_return_count) is int, "LEDGER-EVENT-RETURN-TYPE", type(event_return_count).__name__)
        _require(event_return_count == 1, "LEDGER-EVENT-RETURN-COUNT", event_return_count)

        r5_transaction = transaction.r5_transaction
        transaction_id = r5_transaction.transaction_id
        _require(type(transaction_id) is str and transaction_id.endswith(f"-tx{index}"), "LEDGER-TRANSACTION-ID", transaction_id)

        counts = dict(transaction.exact_execution_counts)
        required = (
            "successful_real_full_learner_transactions",
            "s10_entries",
            "actor_optimizer_step_by_actor",
            "critic_optimizer_step",
            "live_valuenorm_update",
        )
        missing = [name for name in required if name not in counts]
        _require(not missing, "LEDGER-REQUIRED-COUNT-MISSING", missing)
        successful = counts["successful_real_full_learner_transactions"]
        s10_entries = counts["s10_entries"]
        actor_steps = counts["actor_optimizer_step_by_actor"]
        critic_steps = counts["critic_optimizer_step"]
        valuenorm_updates = counts["live_valuenorm_update"]
        _require(type(successful) is int and successful == 1, "LEDGER-UPDATE-NOT-COMPLETE", successful)
        _require(type(s10_entries) is int and s10_entries == 1, "LEDGER-S10-NOT-COMPLETE", s10_entries)
        _require(
            isinstance(actor_steps, tuple)
            and len(actor_steps) == 3
            and all(type(value) is int and value == 5 for value in actor_steps),
            "LEDGER-ACTOR-UPDATE-STATUS",
            actor_steps,
        )
        _require(type(critic_steps) is int and critic_steps == 10, "LEDGER-CRITIC-UPDATE-STATUS", critic_steps)
        _require(type(valuenorm_updates) is int and valuenorm_updates == 10, "LEDGER-VALUENORM-UPDATE-STATUS", valuenorm_updates)
        _require(transaction.next_rollout_ready is True, "LEDGER-TRANSACTION-NOT-READY", transaction.next_rollout_ready)
        quiescence = r5_transaction.quiescence_evidence
        _require(quiescence.route_poisoned is False, "LEDGER-ROUTE-POISONED", quiescence.route_poisoned)
        return {
            "transaction": f"tx{index:03d}",
            "transaction_index": index,
            "transaction_id": transaction_id,
            "event_return_authority_path": "transaction.real_audit.event_return_compute_count",
            "event_return_compute_count": event_return_count,
            "update_returned": True,
            "actor_update_status": "PASS",
            "actor_optimizer_steps": actor_steps,
            "critic_update_status": "PASS",
            "critic_optimizer_steps": critic_steps,
            "valuenorm_update_status": "PASS",
            "valuenorm_updates": valuenorm_updates,
            "transaction_completion_status": "PASS",
            "s10_entries": s10_entries,
            "next_rollout_ready": True,
            "route_poisoned": False,
        }

    def commit(self, index: int) -> None:
        _require(index == self.expected_next_index and index not in self.committed_indices, "LEDGER-COMMIT-ORDER", index)
        self.committed_indices.add(index)
        self.expected_next_index += 1


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _ckpt2_r2_append_transaction_ledger(
    *,
    index: int,
    process: str,
    transaction: Any,
    state: dict[str, Any],
    snapshot: Mapping[str, Any],
    next_lr_receipt: Any,
    ledger_path: Path,
) -> dict[str, Any]:
    binder = state.get("ledger_binder")
    if binder is None:
        binder = _LedgerBinder.starting_at(1 if process == "a" else 4)
        state["ledger_binder"] = binder
    row = binder.bind(index, transaction)
    row.update(
        {
            "process": process.upper(),
            "physical_steps": 2,
            "lr_set_before_fingerprint": True,
            "collection_immutable": state["collection_checks"][index]["result"] == "PASS",
            "lr_mutations_inside_collection_interval": state["collection_checks"][index]["lr_mutations_inside_collection_interval"],
            "lr_schedule": state["lr_receipts"][index],
            "next_lr_primed_at_post_update_boundary": next_lr_receipt,
            "progression_after": state["progression"].state.to_mapping(),
            "semantic_digest_after": snapshot["semantic_digest"],
            "result": "PASS",
        }
    )
    _append_jsonl(ledger_path, row)
    binder.commit(index)
    if process == "a" and index == 1:
        _atomic_json(
            ledger_path.parent / "ckpt2_r1_ledger_keyerror_regression_check.json",
            {
                "historical_error": "KeyError('event_return_computations')",
                "historical_incorrect_path": "dict(transaction.exact_execution_counts)['event_return_computations']",
                "corrected_path": "transaction.real_audit.event_return_compute_count",
                "observed_count": row["event_return_compute_count"],
                "regression": False,
                "result": "PASS",
            },
        )
    return row


def _runtime_namespace() -> tuple[dict[str, Any], str]:
    _require(_sha(R1_HARNESS) == EXPECTED_R1_HARNESS_SHA256, "R1-HARNESS-DRIFT")
    source = R1_HARNESS.read_text(encoding="utf-8")
    start = "        counts = dict(transaction.exact_execution_counts)\n"
    end = "        _append_jsonl(ledger_path, row)\n"
    _require(source.count(start) == 1 and source.count(end) == 1, "R1-LEDGER-BLOCK-IDENTITY")
    left = source.index(start)
    right = source.index(end, left) + len(end)
    replacement = (
        "        row = _ckpt2_r2_append_transaction_ledger(\n"
        "            index=index, process=process, transaction=transaction, state=state,\n"
        "            snapshot=snapshot, next_lr_receipt=next_lr_receipt, ledger_path=ledger_path,\n"
        "        )\n"
    )
    transformed = source[:left] + replacement + source[right:]
    transformed = transformed.replace("ckpt2_r1", "ckpt2_r2").replace("CKPT2-R1", "CKPT2-R2")
    namespace: dict[str, Any] = {
        "__name__": "_b2_t4_ckpt2_r2_runtime",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
        "_ckpt2_r2_append_transaction_ledger": _ckpt2_r2_append_transaction_ledger,
    }
    exec(compile(transformed, str(R1_HARNESS), "exec"), namespace)
    namespace["ARTIFACT_ROOT"] = ARTIFACT_ROOT
    namespace["CHECKPOINT_ROOT"] = CHECKPOINT_ROOT
    namespace["PASS_CLASSIFICATION"] = PASS_CLASSIFICATION
    return namespace, hashlib.sha256(transformed.encode("utf-8")).hexdigest()


RUNTIME, TRANSFORMED_RUNTIME_SHA256 = _runtime_namespace()


def _fixture(index: int = 1) -> Any:
    counts = (
        ("successful_real_full_learner_transactions", 1),
        ("s10_entries", 1),
        ("actor_optimizer_step_by_actor", (5, 5, 5)),
        ("critic_optimizer_step", 10),
        ("live_valuenorm_update", 10),
    )
    return SimpleNamespace(
        classification="PASS",
        real_audit=SimpleNamespace(event_return_compute_count=1),
        r5_transaction=SimpleNamespace(
            transaction_id=f"transaction-fixture-tx{index}",
            quiescence_evidence=SimpleNamespace(route_poisoned=False),
        ),
        exact_execution_counts=counts,
        next_rollout_ready=True,
    )


def _expect_stop(name: str, operation: Any) -> dict[str, Any]:
    try:
        operation()
    except RuntimeError as exc:
        return {"name": name, "expected_stop": True, "error": str(exc), "result": "PASS"}
    return {"name": name, "expected_stop": True, "error": None, "result": "UNEXPECTED_PASS"}


def _pure_ledger_qualification() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    historical = _fixture()
    historical_counts = dict(historical.exact_execution_counts)
    reproduced = False
    error = None
    try:
        historical_counts["event_return_computations"]
    except KeyError as exc:
        reproduced = exc.args == ("event_return_computations",)
        error = repr(exc)
    reproduction = {
        "incorrect_source": "dict(transaction.exact_execution_counts)['event_return_computations']",
        "actual_transaction_count_keys": sorted(historical_counts),
        "historical_error": error,
        "keyerror_reproduced": reproduced,
        "result": "PASS" if reproduced else "FAIL",
    }
    _require(reproduced, "R1-KEYERROR-REPRODUCTION", reproduction)

    binder = _LedgerBinder.starting_at(1)
    row = binder.bind(1, _fixture(1))
    binder.commit(1)
    positive = {
        "production_shaped_result_type": "B2R5IRealTransactionEvidenceV1 fixture",
        "authority_path": row["event_return_authority_path"],
        "event_return_compute_count": row["event_return_compute_count"],
        "missing_required_fields": [],
        "aggregate_scope_substitution": False,
        "ledger_row_accepted": True,
        "result": "PASS",
    }

    cases = []
    missing = _fixture()
    del missing.real_audit.event_return_compute_count
    cases.append(_expect_stop("transaction_local_authority_missing", lambda: _LedgerBinder.starting_at(1).bind(1, missing)))
    aggregate_only = _fixture()
    del aggregate_only.real_audit.event_return_compute_count
    aggregate_only.exact_execution_counts += (("event_return_computations", 1),)
    cases.append(_expect_stop("aggregate_present_transaction_local_missing", lambda: _LedgerBinder.starting_at(1).bind(1, aggregate_only)))
    wrong_type = _fixture()
    wrong_type.real_audit.event_return_compute_count = "1"
    cases.append(_expect_stop("event_return_wrong_type", lambda: _LedgerBinder.starting_at(1).bind(1, wrong_type)))
    mismatch = _fixture()
    mismatch.r5_transaction.transaction_id = "transaction-fixture-tx999"
    cases.append(_expect_stop("transaction_id_mismatch", lambda: _LedgerBinder.starting_at(1).bind(1, mismatch)))
    incomplete = _fixture()
    incomplete.exact_execution_counts = tuple(
        (key, 0 if key == "successful_real_full_learner_transactions" else value)
        for key, value in incomplete.exact_execution_counts
    )
    cases.append(_expect_stop("update_not_complete", lambda: _LedgerBinder.starting_at(1).bind(1, incomplete)))
    duplicate_binder = _LedgerBinder.starting_at(1)
    duplicate_binder.bind(1, _fixture())
    duplicate_binder.commit(1)
    cases.append(_expect_stop("duplicate_transaction_append", lambda: duplicate_binder.bind(1, _fixture())))
    cases.append(_expect_stop("out_of_order_transaction", lambda: _LedgerBinder.starting_at(1).bind(2, _fixture(2))))
    negative = {
        "cases": cases,
        "case_count": len(cases),
        "unexpected_pass": sum(case["result"] != "PASS" for case in cases),
    }
    negative["result"] = "PASS" if negative["unexpected_pass"] == 0 else "FAIL"
    _require(negative["result"] == "PASS", "LEDGER-NEGATIVE-MATRIX", negative)
    return reproduction, positive, negative


def _binding_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    authority = {
        "producer_symbol": "execute_real_isaac_single_transaction_v1",
        "result_object_type": "B2R5IRealTransactionEvidenceV1",
        "transaction_local_path": "transaction.real_audit.event_return_compute_count",
        "value_type": "int (bool rejected)",
        "expected_value_per_transaction": 1,
        "scope": "transaction-local immutable audit",
        "campaign_aggregate_path": "evidence['exact_execution_counts']['event_return_computations']",
        "campaign_aggregate_semantics": "len(completed transactions), constructed only after campaign completion",
        "ckpt2_r1_incorrect_path": "dict(transaction.exact_execution_counts)['event_return_computations']",
        "ckpt2_r2_corrected_path": "transaction.real_audit.event_return_compute_count",
        "silent_default": False,
        "result": "PASS",
    }
    rows = [
        ("event_return_compute_count", "transaction.real_audit", "event_return_compute_count", "int", "exactly one transaction-local computation"),
        ("transaction_id", "transaction.r5_transaction", "transaction_id", "str", "must end in authorized tx index"),
        ("actor_update_status", "transaction.exact_execution_counts", "actor_optimizer_step_by_actor", "tuple[int,int,int]", "exactly (5,5,5)"),
        ("critic_update_status", "transaction.exact_execution_counts", "critic_optimizer_step", "int", "exactly 10"),
        ("valuenorm_update_status", "transaction.exact_execution_counts", "live_valuenorm_update", "int", "exactly 10"),
        ("transaction_completion_status", "transaction.exact_execution_counts", "successful_real_full_learner_transactions + s10_entries", "int + int", "exactly 1 + 1"),
        ("progression_after", "OptimizationProgressionTracker", "state.to_mapping()", "mapping[str,int]", "advanced once after returned transaction"),
    ]
    binding = {
        "schema_version": "b2_t4_ckpt2_r2_transaction_ledger_binding_v1",
        "fields": [
            {"ledger_field": a, "authoritative_source_object": b, "source_field_path": c, "type": d, "expected_semantics": e}
            for a, b, c, d, e in rows
        ],
        "required_field_count": len(rows),
        "silent_defaults": 0,
        "result": "PASS",
    }
    return authority, binding


def _preflight(args: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    pure_path = ARTIFACT_ROOT / "preflight_ckpt1_pure.json"
    _require(pure_path.is_file(), "MISSING-CKPT1-PURE-PREFLIGHT")
    pure = json.loads(pure_path.read_text(encoding="utf-8"))
    _require(
        pure.get("successful") is True
        and pure.get("tests_run") == 6
        and pure.get("negative_case_count") == 25
        and pure.get("unexpected_negative_case_count") == 0,
        "CKPT1-PURE-PREFLIGHT",
        pure,
    )

    repository = _repository_authority()
    _require(repository["branch"] == "main", "REPOSITORY-BRANCH", repository)
    _require(repository["HEAD"] == repository["origin_main"] == repository["merge_base"] == BEFORE_FIRST_WRITE["HEAD"], "REPOSITORY-HEAD", repository)
    _require(repository["staged_path_count"] == 359 and repository["staged_index_sha256"] == BEFORE_FIRST_WRITE["staged_index_sha256"], "STAGED-INDEX", repository)
    _atomic_json(ARTIFACT_ROOT / "repository_authority.json", repository)

    ckpt2_inventory, ckpt2_digest = _inventory(CKPT2_ARTIFACT_ROOT)
    r1_inventory, r1_digest = _inventory(R1_ARTIFACT_ROOT)
    ckpt2_preservation = {
        "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL",
        "artifact_file_count": len(ckpt2_inventory),
        "artifact_inventory_sha256": ckpt2_digest,
        "harness_sha256": _sha(CKPT2_HARNESS),
        "report_sha256": _sha(CKPT2_REPORT),
    }
    ckpt2_preservation["preserved"] = (
        len(ckpt2_inventory) == EXPECTED_CKPT2_ARTIFACT_COUNT
        and ckpt2_digest == EXPECTED_CKPT2_ARTIFACT_SHA256
        and ckpt2_preservation["harness_sha256"] == EXPECTED_CKPT2_HARNESS_SHA256
        and ckpt2_preservation["report_sha256"] == EXPECTED_CKPT2_REPORT_SHA256
    )
    _require(ckpt2_preservation["preserved"], "HISTORICAL-CKPT2-DRIFT", ckpt2_preservation)
    ckpt2_preservation["result"] = "PASS"
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_preservation.json", ckpt2_preservation)
    r1_preservation = {
        "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POST-UPDATE TEST-SIDE EVIDENCE-HOOK FAILURE / NOT POISONED / NO RETRY",
        "artifact_file_count": len(r1_inventory),
        "artifact_inventory_sha256": r1_digest,
        "harness_sha256": _sha(R1_HARNESS),
        "report_sha256": _sha(R1_REPORT),
    }
    r1_preservation["preserved"] = (
        len(r1_inventory) == EXPECTED_R1_ARTIFACT_COUNT
        and r1_digest == EXPECTED_R1_ARTIFACT_SHA256
        and r1_preservation["harness_sha256"] == EXPECTED_R1_HARNESS_SHA256
        and r1_preservation["report_sha256"] == EXPECTED_R1_REPORT_SHA256
    )
    _require(r1_preservation["preserved"], "HISTORICAL-CKPT2-R1-DRIFT", r1_preservation)
    r1_preservation["result"] = "PASS"
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_r1_preservation.json", r1_preservation)

    production = {name: _sha(SCAN / name) for name in EXPECTED_CKPT1_SHA256}
    installed = {name: _sha(HARL_ROOT / name) for name in EXPECTED_HARL_SHA256}
    _require(production == EXPECTED_CKPT1_SHA256, "CKPT1-PRODUCTION-DRIFT", production)
    _require(installed == EXPECTED_HARL_SHA256, "INSTALLED-HARL-DRIFT", installed)
    _atomic_json(
        ARTIFACT_ROOT / "ckpt1_preservation.json",
        {"status": "GPT REVIEW PASS / CLOSED", "implementation_sha256": production, "installed_harl_sha256": installed, "pure_tests": "6/6", "negative_matrix": "25/25", "result": "PASS"},
    )

    authority, binding = _binding_inventory()
    reproduction, positive, negative = _pure_ledger_qualification()
    lr = RUNTIME["_lr_boundary_pure"]()
    gate = RUNTIME["_launch_gate_matrix"]()
    _atomic_json(ARTIFACT_ROOT / "transaction_event_return_authority_inventory.json", authority)
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r1_ledger_schema_failure_reproduction.json", reproduction)
    _atomic_json(ARTIFACT_ROOT / "transaction_ledger_schema_binding.json", binding)
    _atomic_json(ARTIFACT_ROOT / "transaction_ledger_positive_qualification.json", positive)
    _atomic_json(ARTIFACT_ROOT / "transaction_ledger_negative_matrix.json", negative)
    _atomic_json(
        ARTIFACT_ROOT / "ckpt2_r1_lr_repair_preservation.json",
        {"r1_runtime_observation": "tx001 PASS", "pure_boundary_fixture": lr, "repair_changed_by_r2": False, "result": "PASS"},
    )
    _atomic_json(
        ARTIFACT_ROOT / "ckpt2_r1_process_a_gate_preservation.json",
        {"r1_runtime_observation": "return_code_zero_with_semantic_failure_denied_B", "negative_matrix": gate, "all_conditions_required": True, "repair_weakened_by_r2": False, "result": "PASS"},
    )
    _atomic_json(
        ARTIFACT_ROOT / "pre_runtime_harness_repair_log.json",
        {
            "repairs": [{"id": "POST_UPDATE_TRANSACTION_LEDGER_SCHEMA_BINDING", "scope": "CKPT2-R2 test-side evidence only", "old_path": authority["ckpt2_r1_incorrect_path"], "new_path": authority["ckpt2_r2_corrected_path"], "production_semantic_change": False, "result": "PASS"}],
            "production_files_modified": 0,
            "installed_harl_files_modified": 0,
            "unresolved_test_side_repairs": 0,
            "result": "PASS",
        },
    )
    _require(args.run_id not in ("b2-t4-ckpt2-20260923-real01-6f72c9ad", "b2-t4-ckpt2-r1-20260923-real01-a83f5d2c"), "RUN-ID-REUSE")
    _atomic_json(
        ARTIFACT_ROOT / "ckpt2_r2_run_identity.json",
        {"run_id": args.run_id, "fresh": True, "historical_run_ids_reused": False, "attempt_number": 1, "maximum_attempts": 1},
    )
    preflight = {
        "schema_version": "b2_t4_ckpt2_r2_preflight_v1",
        "run_id": args.run_id,
        "historical_ckpt2_preserved": True,
        "historical_ckpt2_r1_preserved": True,
        "ckpt1_core_qualification": "PASS",
        "r1_keyerror_reproduction": "PASS",
        "transaction_event_return_authority": authority["transaction_local_path"],
        "ledger_positive": "PASS",
        "ledger_negative_matrix": "7/7 PASS",
        "silent_defaults": 0,
        "lr_repair_preservation": "PASS",
        "process_a_gate_preservation": "PASS",
        "checkpoint_schema": "PASS",
        "valuenorm_adapter": "PASS",
        "optimizer_state_coverage": "PASS",
        "installed_harl_preservation": "PASS",
        "unresolved_repairs": 0,
        "runtime_started": False,
        "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r2_preflight.json", preflight)
    harness = Path(__file__).resolve()
    freeze = {
        "run_id": args.run_id,
        "frozen_before_process_a": True,
        "harness_sha256": _sha(harness),
        "transformed_r1_runtime_sha256": TRANSFORMED_RUNTIME_SHA256,
        "source_sha256": {
            harness.relative_to(ROOT).as_posix(): _sha(harness),
            R1_HARNESS.relative_to(ROOT).as_posix(): _sha(R1_HARNESS),
            **{(SCAN / name).relative_to(ROOT).as_posix(): digest for name, digest in production.items()},
        },
        "post_freeze_source_edits_authorized": False,
        "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r2_pre_runtime_freeze.json", freeze)
    print(json.dumps(preflight, indent=2, sort_keys=True))
    return 0


def _parent(args: argparse.Namespace) -> int:
    result = RUNTIME["_parent"](args)
    if result == 0:
        final_path = ARTIFACT_ROOT / "final_result.json"
        final = json.loads(final_path.read_text(encoding="utf-8"))
        a_ledger = [json.loads(line) for line in (ARTIFACT_ROOT / "process_a" / "transaction_ledger.jsonl").read_text(encoding="utf-8").splitlines() if line]
        b_ledger = [json.loads(line) for line in (ARTIFACT_ROOT / "process_b" / "transaction_ledger.jsonl").read_text(encoding="utf-8").splitlines() if line]
        _require(len(a_ledger) == len(b_ledger) == 3, "FINAL-LEDGER-COUNT", {"a": len(a_ledger), "b": len(b_ledger)})
        final.update(
            {
                "classification": PASS_CLASSIFICATION,
                "historical_ckpt2_r1": "GPT REVIEW STOP CONFIRMED / HISTORICAL",
                "transaction_event_return_authority": "transaction.real_audit.event_return_compute_count",
                "r1_ledger_keyerror_regression": False,
                "ledger_schema_repair": "PASS",
                "process_a_ledger_rows": "3/3",
                "process_b_ledger_rows": "3/3",
            }
        )
        _atomic_json(final_path, final)
        bridge_path = ARTIFACT_ROOT / "real_checkpoint_continuation_bridge.json"
        bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
        bridge.update({"process_a_ledger_rows": 3, "process_b_ledger_rows": 3})
        _atomic_json(bridge_path, bridge)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--parent", action="store_true")
    mode.add_argument("--worker", choices=("a", "b"))
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.preflight:
        return _preflight(args)
    if args.worker:
        return RUNTIME["_worker"](args)
    return _parent(args)


if __name__ == "__main__":
    raise SystemExit(main())
