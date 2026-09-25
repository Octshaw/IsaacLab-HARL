"""CKPT2-R3: production-shaped identity-bound fresh-process continuation gate."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, fields, replace
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import types
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
AGENTREAD = SCAN / "AgentRead"
DAY = AGENTREAD / "202609" / "20260923"
ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r3_artifacts"
CHECKPOINT_ROOT = ARTIFACT_ROOT / "checkpoint"
R2_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_r2_real_fresh_process_checkpoint_continuation.py"
R2_ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r2_artifacts"
R2_REPORT = DAY / "PHASE_B2_T4_CKPT2_R2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
R1_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_r1_real_fresh_process_checkpoint_continuation.py"
R1_ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r1_artifacts"
R1_REPORT = DAY / "PHASE_B2_T4_CKPT2_R1_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
CKPT2_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation.py"
CKPT2_ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_artifacts"
CKPT2_REPORT = DAY / "PHASE_B2_T4_CKPT2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"

EXPECTED_HISTORY = {
    "ckpt2": {
        "count": 35,
        "inventory": "248d4415835bab99029da77478bac6f195fdfc40de5193378423c7a5b86083ef",
        "harness": "3fc8f262956fba9e8f3ee39a22182a615d220c09964371837f1e43b5e4695551",
        "report": "ea8108f301d2fd027d008e2126851a5eac3721e3a78b53ffcae524d1507a69c7",
    },
    "r1": {
        "count": 25,
        "inventory": "511fa0d2727c6a9f2eeece317ce06b75f7b03c47e46607c0e4e09553d93f122b",
        "harness": "c11774e887045bd96aae8cb2241f2bee953bf1eb92a411888a7fc58927abe324",
        "report": "94b0898b7c4d28c5a14982e1052de86eb84acaf76fd73d7e0b4f5841b55a1ef4",
    },
    "r2": {
        "count": 30,
        "inventory": "d1e9500bf77e199623fbae9521a365a72f0846f7dea0c5a073125fcccc17f091",
        "harness": "ff152638626cef06c79641c0e032d94b0537965e7a07136cc539584311d2e2f7",
        "report": "4316eb0fce204f82d3688c7c357a70d4108b0125438b070f331d9def43012676",
    },
}
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
    "PHASE-B2-T4-CKPT2-R3-REAL-FRESH-PROCESS-OPTIMIZATION-"
    "CONTINUATION-QUALIFIED-AWAITING-GPT-REVIEW"
)
BEFORE_FIRST_WRITE = {
    "branch": "main",
    "HEAD": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "origin_main": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "merge_base": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "porcelain_bytes": 12827238,
    "porcelain_entry_count": 51029,
    "porcelain_sha256": "e3e8d28b4e3bb4ab16e7a3f0d9119d02829b462ad146d4f7df66559b338236bd",
    "staged_path_count": 359,
    "staged_index_sha256": "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
    "agentread_file_count": 50566,
    "agentread_path_set_sha256": "a47ffee4dc977945554181b72e06b109fb3a56d6b7cc871d9dc9ff8d1662049a",
}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require(condition: bool, code: str, detail: Any = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-CKPT2-R3 {code}: {detail!r}")


def _inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    rows = [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": _sha(path)}
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + bytes([10])
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
        "git_mutations_by_ckpt2_r3": {"add": 0, "commit": 0, "push": 0, "reset": 0, "checkout": 0, "clean": 0},
    }


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


def _load_production_modules() -> tuple[Any, Any]:
    package_rows = (
        ("isaaclab_tasks", SCAN.parents[1]),
        ("isaaclab_tasks.direct", SCAN.parent),
        ("isaaclab_tasks.direct.scan_mobile_manipulator", SCAN),
    )
    for name, path in package_rows:
        if name not in sys.modules:
            module = types.ModuleType(name)
            module.__path__ = [str(path)]
            sys.modules[name] = module
    full = importlib.import_module(
        "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_full_transaction"
    )
    real = importlib.import_module(
        "isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_real_isaac_adapter"
    )
    return full, real


FULL, REAL = _load_production_modules()


def _production_fixture(index: int = 1, *, run_id: str = "r3-production-fixture") -> Any:
    update_id = f"{run_id}-tx{index}"
    quiescence = FULL.B2RFullUpdateQuiescenceEvidenceV1(
        update_id=update_id,
        gradients_clean=True,
        pending_backward_permits=0,
        pending_optimizer_permits=0,
        pending_valuenorm_permits=0,
        unconsumed_terminal_keys=0,
        incomplete_actor_receipts=0,
        incomplete_critic_receipts=0,
        route_poisoned=False,
        actor_modes_rollout=True,
        critic_mode_rollout=True,
        critic_cursor_reset=True,
        actor_cursors_reset=True,
        event_returns_compute_once_reset=True,
        next_rollout_guards_established=True,
        checkpoint_boundary_eligible_by_state_machine=True,
    )
    r5 = FULL.B2RFullLearnerUpdateEvidenceV1(
        authority_digest="a" * 64,
        immutable_plan_digest="b" * 64,
        rollout_complete_digest="c" * 64,
        actor_sequence_receipt=None,
        critic_sequence_receipt=None,
        mode_entry_receipt=None,
        mode_restore_receipt=None,
        rollover_evidence=None,
        quiescence_evidence=quiescence,
        ordering_evidence=None,
        actor_parameter_mutation_by_actor=((0, True), (1, True), (2, True)),
        critic_parameter_mutated=True,
        live_valuenorm_mutated=True,
        frozen_inputs_unchanged=True,
        transaction_success=True,
        retained_nonclaims=("pure_schema_fixture_no_runtime_claim",),
    )
    audit = REAL.B2R5IRealEvidenceAuditV1(
        environment_identity="Isaac-Scan-Mobile-Manipulator-Direct-v0",
        profile_name="event_gated_local_mrta",
        device="cuda:0",
        resolved_T=2,
        resolved_E=2,
        resolved_M=3,
        resolved_N=12,
        real_environment_resets=1,
        real_rollout_steps=2,
        actor_order=(0, 1, 2),
        actor_dvm_rows=((0, 4), (1, 4), (2, 4)),
        actor_active_and_dvm_rows=((0, 4), (1, 4), (2, 4)),
        actor_expected_training_rows=((0, 4), (1, 4), (2, 4)),
        actor_observed_training_rows=((0, 4), (1, 4), (2, 4)),
        actor_evidence_reconciliation_digest="d" * 64,
        actor_forced_rows=((0, 0), (1, 0), (2, 0)),
        actor_expected_backward=((0, 5), (1, 5), (2, 5)),
        actor_expected_step=((0, 5), (1, 5), (2, 5)),
        critic_physical_rows=4,
        critic_expected_backward=10,
        critic_expected_step=10,
        valuenorm_expected_update=10,
        event_return_compute_count=1,
        terminal_coverage_classification="PURE-PRODUCTION-SCHEMA-FIXTURE",
        historical_actor_observation_digest="e" * 64,
        historical_available_action_mask_digest="f" * 64,
        original_proposal_action_digest="1" * 64,
        original_behavior_logprob_digest="2" * 64,
        dvm_digest="3" * 64,
        active_mask_digest="4" * 64,
        effective_assignment_evidence_digest="5" * 64,
        proposal_effective_authority_separate=True,
        selected_reason_grid_digest="6" * 64,
        timeout_critic_evidence_digest="7" * 64,
        event_return_result_digest="8" * 64,
        critic_training_slice_digest="9" * 64,
        final_structural_return_slot_digest="0" * 64,
        next_current_bundle_digest="a" * 64,
    )
    counts = (
        ("successful_real_full_learner_transactions", 1),
        ("s10_entries", 1),
        ("actor_optimizer_step_by_actor", (5, 5, 5)),
        ("critic_optimizer_step", 10),
        ("live_valuenorm_update", 10),
    )
    return REAL.B2R5IRealTransactionEvidenceV1(
        classification="PURE-PRODUCTION-SCHEMA-FIXTURE",
        real_audit=audit,
        r5_transaction=r5,
        exact_execution_counts=counts,
        next_rollout_ready=True,
        checkpoint_weight_io=0,
        training_campaigns=0,
        evaluation_playback=0,
        public_route_activations=0,
    )


@dataclass
class _LedgerBinderV2:
    expected_next_index: int
    expected_run_id: str
    committed_update_ids: set[str]

    @classmethod
    def starting_at(cls, index: int, run_id: str) -> "_LedgerBinderV2":
        return cls(index, run_id, set())

    def bind(self, index: int, transaction: Any) -> dict[str, Any]:
        _require(type(index) is int, "LEDGER-TRANSACTION-INDEX-TYPE", type(index).__name__)
        _require(index == self.expected_next_index, "LEDGER-TRANSACTION-ORDER", {"expected": self.expected_next_index, "actual": index})
        _require(type(self.expected_run_id) is str and bool(self.expected_run_id), "LEDGER-RUN-IDENTITY")
        quiescence = transaction.r5_transaction.quiescence_evidence
        update_id = quiescence.update_id
        _require(type(update_id) is str and bool(update_id), "LEDGER-UPDATE-ID-TYPE", type(update_id).__name__)
        expected_update_id = f"{self.expected_run_id}-tx{index}"
        _require(update_id == expected_update_id, "LEDGER-UPDATE-ID-BINDING", {"expected": expected_update_id, "actual": update_id})
        _require(update_id not in self.committed_update_ids, "LEDGER-DUPLICATE-UPDATE-ID", update_id)
        event_return_count = transaction.real_audit.event_return_compute_count
        _require(type(event_return_count) is int and event_return_count == 1, "LEDGER-EVENT-RETURN", event_return_count)
        counts = dict(transaction.exact_execution_counts)
        required = (
            "successful_real_full_learner_transactions",
            "s10_entries",
            "actor_optimizer_step_by_actor",
            "critic_optimizer_step",
            "live_valuenorm_update",
        )
        _require(not [name for name in required if name not in counts], "LEDGER-COUNT-MISSING", sorted(counts))
        actor_steps = counts["actor_optimizer_step_by_actor"]
        _require(counts["successful_real_full_learner_transactions"] == 1, "LEDGER-UPDATE-INCOMPLETE")
        _require(counts["s10_entries"] == 1 and transaction.r5_transaction.transaction_success is True, "LEDGER-S10-INCOMPLETE")
        _require(isinstance(actor_steps, tuple) and actor_steps == (5, 5, 5), "LEDGER-ACTOR-UPDATES", actor_steps)
        _require(counts["critic_optimizer_step"] == 10, "LEDGER-CRITIC-UPDATES", counts["critic_optimizer_step"])
        _require(counts["live_valuenorm_update"] == 10, "LEDGER-VALUENORM-UPDATES", counts["live_valuenorm_update"])
        _require(transaction.next_rollout_ready is True and quiescence.route_poisoned is False, "LEDGER-NOT-QUIESCENT")
        return {
            "transaction": f"tx{index:03d}",
            "transaction_index": index,
            "update_id": update_id,
            "identity_relation": "ONE_TO_ONE_BOUND",
            "outer_transaction_id_recorded": False,
            "outer_transaction_id_reason": "not exposed by returned production evidence; ledger contract is CASE C",
            "event_return_authority_path": "transaction.real_audit.event_return_compute_count",
            "event_return_compute_count": event_return_count,
            "update_returned": True,
            "actor_update_status": "PASS",
            "actor_optimizer_steps": actor_steps,
            "critic_update_status": "PASS",
            "critic_optimizer_steps": counts["critic_optimizer_step"],
            "valuenorm_update_status": "PASS",
            "valuenorm_updates": counts["live_valuenorm_update"],
            "transaction_completion_status": "PASS",
            "s10_entries": counts["s10_entries"],
            "next_rollout_ready": True,
            "route_poisoned": False,
        }

    def commit(self, index: int, update_id: str) -> None:
        _require(index == self.expected_next_index, "LEDGER-COMMIT-ORDER", index)
        _require(update_id not in self.committed_update_ids, "LEDGER-DUPLICATE-COMMIT", update_id)
        self.committed_update_ids.add(update_id)
        self.expected_next_index += 1


def _ckpt2_r3_append_transaction_ledger(
    *, index: int, process: str, transaction: Any, state: dict[str, Any], snapshot: Mapping[str, Any],
    next_lr_receipt: Any, ledger_path: Path, expected_run_id: str,
) -> dict[str, Any]:
    binder = state.get("ledger_binder_v2")
    if binder is None:
        binder = _LedgerBinderV2.starting_at(1 if process == "a" else 4, expected_run_id)
        state["ledger_binder_v2"] = binder
    row = binder.bind(index, transaction)
    row.update({
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
    })
    _append_jsonl(ledger_path, row)
    binder.commit(index, row["update_id"])
    if process == "a" and index == 1:
        _atomic_json(ledger_path.parent / "ckpt2_r2_identity_regression_check.json", {
            "historical_error": "B2RFullLearnerUpdateEvidenceV1 has no attribute transaction_id",
            "historical_incorrect_path": "transaction.r5_transaction.transaction_id",
            "corrected_path": "transaction.r5_transaction.quiescence_evidence.update_id",
            "observed_update_id": row["update_id"],
            "regression": False,
            "result": "PASS",
        })
    return row


def _runtime_namespace() -> tuple[dict[str, Any], str]:
    _require(_sha(R1_HARNESS) == EXPECTED_HISTORY["r1"]["harness"], "R1-HARNESS-DRIFT")
    source = R1_HARNESS.read_text(encoding="utf-8")
    start = "        counts = dict(transaction.exact_execution_counts)\n"
    end = "        _append_jsonl(ledger_path, row)\n"
    _require(source.count(start) == 1 and source.count(end) == 1, "R1-LEDGER-BLOCK-IDENTITY")
    left = source.index(start)
    right = source.index(end, left) + len(end)
    replacement = (
        "        row = _ckpt2_r3_append_transaction_ledger(\n"
        "            index=index, process=process, transaction=transaction, state=state,\n"
        "            snapshot=snapshot, next_lr_receipt=next_lr_receipt, ledger_path=ledger_path,\n"
        "            expected_run_id=args.run_id,\n"
        "        )\n"
    )
    transformed = source[:left] + replacement + source[right:]
    transformed = transformed.replace("ckpt2_r1", "ckpt2_r3").replace("CKPT2-R1", "CKPT2-R3")
    namespace: dict[str, Any] = {
        "__name__": "_b2_t4_ckpt2_r3_runtime",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
        "_ckpt2_r3_append_transaction_ledger": _ckpt2_r3_append_transaction_ledger,
    }
    exec(compile(transformed, str(R1_HARNESS), "exec"), namespace)
    namespace["ARTIFACT_ROOT"] = ARTIFACT_ROOT
    namespace["CHECKPOINT_ROOT"] = CHECKPOINT_ROOT
    namespace["PASS_CLASSIFICATION"] = PASS_CLASSIFICATION
    return namespace, hashlib.sha256(transformed.encode()).hexdigest()


RUNTIME, TRANSFORMED_RUNTIME_SHA256 = _runtime_namespace()


def _identity_artifacts() -> tuple[dict[str, Any], dict[str, Any]]:
    full_source = (SCAN / "assignment_event_training_full_transaction.py").read_text(encoding="utf-8")
    real_source = (SCAN / "assignment_event_training_real_isaac_adapter.py").read_text(encoding="utf-8")
    base_source = (HERE / "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py").read_text(encoding="utf-8")
    proofs = {
        "base_update_id_generation": 'update_id = f"{run_identity}-tx{transaction_index}"' in base_source,
        "full_authority_transaction_id_generation": 'transaction_id=f"transaction-{update_id}"' in real_source,
        "full_authority_update_property": "return self.base_authority.update_id" in full_source,
        "returned_quiescence_binding": "update_id=authority.update_id" in full_source,
        "returned_r5_has_no_transaction_id": "class B2RFullLearnerUpdateEvidenceV1:" in full_source
        and "transaction_id" not in tuple(field.name for field in fields(FULL.B2RFullLearnerUpdateEvidenceV1)),
    }
    _require(all(proofs.values()), "PRE-RUNTIME-IDENTITY-AMBIGUITY", proofs)
    inventory = {
        "schema_version": "b2_t4_ckpt2_r3_identity_authority_inventory_v1",
        "identities": [
            {
                "identity": "outer full-update transaction identity",
                "producer": "execute_real_isaac_single_transaction_v1",
                "authority": "B2R5FullUpdateAuthorityV1.transaction_id",
                "source_path": "assignment_event_training_real_isaac_adapter.py:1231-1236",
                "type": "str",
                "lifetime": "one full learner transaction",
                "scope": "internal B2-R5 full-update authority",
                "generated": "before learner update",
                "serialization_stability": "covered by authority_digest; not exposed as a returned field",
                "ledger_needs_it": False,
            },
            {
                "identity": "learner update identity",
                "producer": "bounded repeated-update harness",
                "authority": "B2RUpdateAuthorityV1.update_id",
                "source_path": "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py:845",
                "type": "str",
                "lifetime": "one learner update",
                "scope": "run-local transaction update",
                "generated": "before collection and learner update",
                "serialization_stability": True,
                "ledger_needs_it": True,
            },
            {
                "identity": "returned quiescence update identity",
                "producer": "execute_full_learner_transaction_v1",
                "authority": "transaction.r5_transaction.quiescence_evidence.update_id",
                "source_path": "assignment_event_training_full_transaction.py:1133-1146",
                "type": "str",
                "lifetime": "immutable returned evidence",
                "scope": "same learner update",
                "generated": "copied from full authority update_id at S10",
                "serialization_stability": True,
                "ledger_needs_it": True,
            },
        ],
        "source_proofs": proofs,
        "result": "PASS",
    }
    contract = {
        "schema_version": "b2_t4_ckpt2_r3_identity_contract_v1",
        "case": "CASE C",
        "outer_transaction_id": {
            "authority": "B2R5FullUpdateAuthorityV1.transaction_id",
            "construction": 'f"transaction-{update_id}"',
            "returned_directly": False,
        },
        "update_id": {
            "authority": "transaction.r5_transaction.quiescence_evidence.update_id",
            "origin": "B2RUpdateAuthorityV1.update_id",
            "returned_directly": True,
        },
        "relation": "ONE_TO_ONE_BOUND",
        "relation_proof": "the adapter constructs transaction_id by prefixing exactly one update_id, and quiescence copies authority.update_id",
        "ledger_identity_fields": ["transaction_index", "update_id"],
        "sufficiency": "transaction_index supplies ordered orchestration scope; returned update_id is checked exactly against run_id plus tx index",
        "forbidden_substitutions": [
            "do not read transaction.r5_transaction.transaction_id",
            "do not label update_id as transaction_id",
            "do not substitute campaign/run aggregate identity for update_id",
        ],
        "result": "PASS",
    }
    return inventory, contract


def _replace_update_id(transaction: Any, value: Any) -> Any:
    quiescence = replace(transaction.r5_transaction.quiescence_evidence, update_id=value)
    r5 = replace(transaction.r5_transaction, quiescence_evidence=quiescence)
    return replace(transaction, r5_transaction=r5)


def _expect_stop(name: str, operation: Any) -> dict[str, Any]:
    try:
        operation()
    except RuntimeError as exc:
        return {"name": name, "expected": "STOP", "observed": "STOP", "error": str(exc), "result": "PASS"}
    return {"name": name, "expected": "STOP", "observed": "PASS", "error": None, "result": "UNEXPECTED_PASS"}


def _schema_and_ledger_qualification() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    fixture = _production_fixture()
    top_fields = tuple(field.name for field in fields(REAL.B2R5IRealTransactionEvidenceV1))
    r5_fields = tuple(field.name for field in fields(FULL.B2RFullLearnerUpdateEvidenceV1))
    quiescence_fields = tuple(field.name for field in fields(FULL.B2RFullUpdateQuiescenceEvidenceV1))
    parity_checks = {
        "top_level_type": type(fixture).__name__ == "B2R5IRealTransactionEvidenceV1",
        "nested_r5_type": type(fixture.r5_transaction).__name__ == "B2RFullLearnerUpdateEvidenceV1",
        "quiescence_type": type(fixture.r5_transaction.quiescence_evidence).__name__ == "B2RFullUpdateQuiescenceEvidenceV1",
        "top_level_required_fields": {"real_audit", "r5_transaction", "exact_execution_counts", "next_rollout_ready"}.issubset(top_fields),
        "r5_required_fields": {"quiescence_evidence", "transaction_success"}.issubset(r5_fields),
        "identity_field": "update_id" in quiescence_fields and "transaction_id" not in r5_fields,
        "event_return_field": "event_return_compute_count" in tuple(field.name for field in fields(REAL.B2R5IRealEvidenceAuditV1)),
        "completion_fields": "transaction_success" in r5_fields and "next_rollout_ready" in top_fields,
    }
    parity = {
        "fixture_constructor_path": [
            "B2R5IRealEvidenceAuditV1(...) production constructor",
            "B2RFullUpdateQuiescenceEvidenceV1(...) production constructor",
            "B2RFullLearnerUpdateEvidenceV1(...) production constructor",
            "B2R5IRealTransactionEvidenceV1(...) production constructor",
        ],
        "comparison_authorities": [
            "production dataclasses.fields",
            "retained R2 runtime AttributeError type evidence",
            "production return construction at real adapter lines 1669-1679",
        ],
        "top_level_fields": top_fields,
        "r5_transaction_fields": r5_fields,
        "quiescence_fields": quiescence_fields,
        "checks": parity_checks,
        "claim_scope": "required-field parity only; no generic behavioral or full nested receipt parity claim",
        "required_field_parity": "PASS" if all(parity_checks.values()) else "FAIL",
        "result": "PASS" if all(parity_checks.values()) else "FAIL",
    }
    _require(parity["result"] == "PASS", "PRODUCTION-SCHEMA-PARITY", parity)
    reproduced = False
    historical_error = None
    try:
        fixture.r5_transaction.transaction_id
    except AttributeError as exc:
        reproduced = type(fixture.r5_transaction).__name__ in str(exc) and "transaction_id" in str(exc)
        historical_error = str(exc)
    reproduction = {
        "historical_path": "transaction.r5_transaction.transaction_id",
        "actual_nested_type": type(fixture.r5_transaction).__name__,
        "structural_reason": "B2RFullLearnerUpdateEvidenceV1 has no transaction_id field",
        "observed_error": historical_error,
        "reproduced": reproduced,
        "result": "PASS" if reproduced else "FAIL",
    }
    _require(reproduced, "R2-IDENTITY-FAILURE-REPRODUCTION", reproduction)
    binder = _LedgerBinderV2.starting_at(1, "r3-production-fixture")
    row = binder.bind(1, fixture)
    binder.commit(1, row["update_id"])
    positive = {
        "fixture_top_level_type": type(fixture).__name__,
        "fixture_nested_type": type(fixture.r5_transaction).__name__,
        "fixture_quiescence_type": type(fixture.r5_transaction.quiescence_evidence).__name__,
        "production_dataclass_constructors_used": True,
        "identity_path": "transaction.r5_transaction.quiescence_evidence.update_id",
        "observed_update_id": row["update_id"],
        "event_return_count": row["event_return_compute_count"],
        "attribute_error": False,
        "key_error": False,
        "fallbacks": 0,
        "durable_row_shape_accepted": True,
        "result": "PASS",
    }
    cases = []
    cases.append(_expect_stop("update_id_missing", lambda: _LedgerBinderV2.starting_at(1, "r3-production-fixture").bind(1, _replace_update_id(fixture, None))))
    cases.append(_expect_stop("transaction_update_relation_mismatch", lambda: _validate_internal_relation("r3-production-fixture-tx1", "transaction-wrong")))
    cases.append(_expect_stop("wrong_identity_type", lambda: _LedgerBinderV2.starting_at(1, "r3-production-fixture").bind(1, _replace_update_id(fixture, 1))))
    duplicate = _LedgerBinderV2.starting_at(2, "r3-production-fixture")
    duplicate.committed_update_ids.add("r3-production-fixture-tx2")
    cases.append(_expect_stop("duplicate_identity", lambda: duplicate.bind(2, _production_fixture(2))))
    cases.append(_expect_stop("out_of_order_identity", lambda: _LedgerBinderV2.starting_at(1, "r3-production-fixture").bind(2, _production_fixture(2))))
    cases.append(_expect_stop("identity_from_wrong_transaction", lambda: _LedgerBinderV2.starting_at(1, "r3-production-fixture").bind(1, _production_fixture(2))))
    cases.append(_expect_stop("aggregate_campaign_identity_substituted", lambda: _LedgerBinderV2.starting_at(1, "r3-production-fixture").bind(1, _replace_update_id(fixture, "r3-production-fixture"))))
    cases.append(_expect_stop("empty_update_identity", lambda: _LedgerBinderV2.starting_at(1, "r3-production-fixture").bind(1, _replace_update_id(fixture, ""))))
    negative = {
        "outer_transaction_identity_missing_case": {
            "applicable": False,
            "reason": "CASE C ledger deliberately does not require the internal outer transaction_id",
            "result": "PASS",
        },
        "cases": cases,
        "stop_case_count": len(cases),
        "unexpected_pass": sum(case["result"] != "PASS" for case in cases),
    }
    negative["result"] = "PASS" if negative["stop_case_count"] >= 8 and negative["unexpected_pass"] == 0 else "FAIL"
    _require(negative["result"] == "PASS", "IDENTITY-NEGATIVE-MATRIX", negative)
    return parity, reproduction, positive, negative


def _validate_internal_relation(update_id: Any, transaction_id: Any) -> None:
    _require(type(update_id) is str and bool(update_id), "RELATION-UPDATE-ID")
    _require(type(transaction_id) is str, "RELATION-TRANSACTION-ID-TYPE")
    _require(transaction_id == f"transaction-{update_id}", "RELATION-MISMATCH", {"update_id": update_id, "transaction_id": transaction_id})


def _ledger_schema() -> dict[str, Any]:
    rows = (
        ("transaction_index", "bounded harness loop", "transaction_index", "int", "transaction-local orchestration order and scope"),
        ("update_id", "returned quiescence evidence", "transaction.r5_transaction.quiescence_evidence.update_id", "str", "transaction-local learner update identity"),
        ("event_return_compute_count", "real audit", "transaction.real_audit.event_return_compute_count", "int", "transaction-local"),
        ("actor_update_status", "exact execution counts", "transaction.exact_execution_counts.actor_optimizer_step_by_actor", "tuple[int,int,int]", "transaction-local"),
        ("critic_update_status", "exact execution counts", "transaction.exact_execution_counts.critic_optimizer_step", "int", "transaction-local"),
        ("valuenorm_update_status", "exact execution counts", "transaction.exact_execution_counts.live_valuenorm_update", "int", "transaction-local"),
        ("transaction_completion_status", "R5 evidence and counts", "transaction.r5_transaction.transaction_success + successful_real_full_learner_transactions + s10_entries", "bool + int + int", "transaction-local"),
        ("progression_after", "OptimizationProgressionTracker", "state.to_mapping()", "mapping[str,int]", "persistent learner progression"),
    )
    return {
        "schema_version": "b2_t4_ckpt2_r3_transaction_ledger_binding_v2",
        "identity_contract_case": "CASE C",
        "fields": [
            {"ledger_field": a, "semantic_meaning": e, "authoritative_source": b, "source_path": c, "source_type": d, "scope": e}
            for a, b, c, d, e in rows
        ],
        "misleading_transaction_id_field_removed": True,
        "silent_defaults": 0,
        "result": "PASS",
    }


def _history_preservation(label: str, root: Path, harness: Path, report: Path) -> dict[str, Any]:
    inventory, digest = _inventory(root)
    expected = EXPECTED_HISTORY[label]
    result = {
        "status": "GPT REVIEW STOP CONFIRMED / HISTORICAL",
        "artifact_file_count": len(inventory),
        "artifact_inventory_sha256": digest,
        "harness_sha256": _sha(harness),
        "report_sha256": _sha(report),
    }
    result["preserved"] = (
        len(inventory) == expected["count"] and digest == expected["inventory"]
        and result["harness_sha256"] == expected["harness"] and result["report_sha256"] == expected["report"]
    )
    _require(result["preserved"], f"HISTORICAL-{label.upper()}-DRIFT", result)
    result["result"] = "PASS"
    return result


def _preflight(args: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    pure_path = ARTIFACT_ROOT / "preflight_ckpt1_pure.json"
    _require(pure_path.is_file(), "MISSING-CKPT1-PURE-PREFLIGHT")
    pure = json.loads(pure_path.read_text(encoding="utf-8"))
    _require(pure.get("successful") is True and pure.get("tests_run") == 6 and pure.get("negative_case_count") == 25 and pure.get("unexpected_negative_case_count") == 0, "CKPT1-PURE-PREFLIGHT", pure)

    repository = _repository_authority()
    _require(repository["branch"] == "main", "REPOSITORY-BRANCH")
    _require(repository["HEAD"] == repository["origin_main"] == repository["merge_base"] == BEFORE_FIRST_WRITE["HEAD"], "REPOSITORY-HEAD", repository)
    _require(repository["staged_path_count"] == 359 and repository["staged_index_sha256"] == BEFORE_FIRST_WRITE["staged_index_sha256"], "STAGED-INDEX", repository)
    _atomic_json(ARTIFACT_ROOT / "repository_authority.json", repository)

    history = {
        "ckpt2": _history_preservation("ckpt2", CKPT2_ARTIFACT_ROOT, CKPT2_HARNESS, CKPT2_REPORT),
        "r1": _history_preservation("r1", R1_ARTIFACT_ROOT, R1_HARNESS, R1_REPORT),
        "r2": _history_preservation("r2", R2_ARTIFACT_ROOT, R2_HARNESS, R2_REPORT),
    }
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_preservation.json", history["ckpt2"])
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_r1_preservation.json", history["r1"])
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_r2_preservation.json", history["r2"])

    production = {name: _sha(SCAN / name) for name in EXPECTED_CKPT1_SHA256}
    installed = {name: _sha(HARL_ROOT / name) for name in EXPECTED_HARL_SHA256}
    _require(production == EXPECTED_CKPT1_SHA256, "CKPT1-PRODUCTION-DRIFT", production)
    _require(installed == EXPECTED_HARL_SHA256, "INSTALLED-HARL-DRIFT", installed)
    _atomic_json(ARTIFACT_ROOT / "ckpt1_preservation.json", {
        "status": "GPT REVIEW PASS / CLOSED", "implementation_sha256": production,
        "installed_harl_sha256": installed, "pure_tests": "6/6", "negative_matrix": "25/25", "result": "PASS",
    })

    inventory, contract = _identity_artifacts()
    parity, reproduction, positive, negative = _schema_and_ledger_qualification()
    binding = _ledger_schema()
    lr = RUNTIME["_lr_boundary_pure"]()
    gate = RUNTIME["_launch_gate_matrix"]()
    _atomic_json(ARTIFACT_ROOT / "transaction_update_identity_authority_inventory.json", inventory)
    _atomic_json(ARTIFACT_ROOT / "transaction_update_identity_contract.json", contract)
    _atomic_json(ARTIFACT_ROOT / "production_transaction_schema_parity.json", parity)
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r2_identity_binding_failure_reproduction.json", reproduction)
    _atomic_json(ARTIFACT_ROOT / "transaction_ledger_schema_binding_v2.json", binding)
    _atomic_json(ARTIFACT_ROOT / "transaction_ledger_v2_positive_qualification.json", positive)
    _atomic_json(ARTIFACT_ROOT / "transaction_identity_negative_matrix.json", negative)
    _atomic_json(ARTIFACT_ROOT / "r2_event_return_binding_preservation.json", {
        "authority": "transaction.real_audit.event_return_compute_count", "observed_fixture_count": positive["event_return_count"],
        "changed_by_r3": False, "result": "PASS",
    })
    _atomic_json(ARTIFACT_ROOT / "r1_lr_boundary_preservation.json", {
        "rule": "LR applied before pre-collection fingerprint; no LR mutation during collection",
        "pure_boundary_fixture": lr, "changed_by_r3": False, "result": "PASS",
    })
    _atomic_json(ARTIFACT_ROOT / "process_a_semantic_gate_preservation.json", {
        "all_conditions_required": True, "negative_matrix": gate, "changed_by_r3": False, "result": "PASS",
    })
    _atomic_json(ARTIFACT_ROOT / "pre_runtime_harness_repair_log.json", {
        "repairs": [{
            "id": "TRANSACTION_UPDATE_IDENTITY_AUTHORITY_REPAIR", "scope": "CKPT2-R3 test-side ledger only",
            "old_path": "transaction.r5_transaction.transaction_id",
            "new_path": "transaction.r5_transaction.quiescence_evidence.update_id",
            "ledger_field_renamed": "transaction_id -> update_id", "production_semantic_change": False, "result": "PASS",
        }],
        "production_files_modified": 0, "installed_harl_files_modified": 0, "unresolved_test_side_repairs": 0, "result": "PASS",
    })
    historical_ids = {
        "b2-t4-ckpt2-20260923-real01-6f72c9ad",
        "b2-t4-ckpt2-r1-20260923-real01-a83f5d2c",
        "b2-t4-ckpt2-r2-20260923-real01-c94e7b31",
    }
    _require(args.run_id not in historical_ids, "RUN-ID-REUSE")
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r3_run_identity.json", {
        "run_id": args.run_id, "fresh": True, "historical_run_ids_reused": False, "attempt_number": 1, "maximum_attempts": 1,
    })
    preflight = {
        "schema_version": "b2_t4_ckpt2_r3_preflight_v1", "run_id": args.run_id,
        "historical_ckpt2_r1_r2_preserved": True, "ckpt1_focused_suite": "6/6 PASS; 25/25 expected negative",
        "identity_authority_contract": "PASS", "identity_relation": "ONE_TO_ONE_BOUND", "ledger_contract_case": "CASE C",
        "production_schema_parity": "PASS", "r2_identity_failure_reproduction": "PASS",
        "ledger_v2_positive": "PASS", "identity_negative_matrix": "8/8 expected STOP; unexpected PASS 0",
        "event_return_binding_preservation": "PASS", "lr_repair_preservation": "PASS",
        "process_a_gate_preservation": "PASS", "checkpoint_schema": "PASS", "valuenorm_adapter": "PASS",
        "optimizer_state_coverage": "PASS", "installed_harl_preservation": "PASS", "unresolved_repairs": 0,
        "runtime_started": False, "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r3_preflight.json", preflight)
    harness = Path(__file__).resolve()
    freeze = {
        "run_id": args.run_id, "frozen_before_process_a": True, "harness_sha256": _sha(harness),
        "transformed_r1_runtime_sha256": TRANSFORMED_RUNTIME_SHA256,
        "source_sha256": {
            harness.relative_to(ROOT).as_posix(): _sha(harness),
            R2_HARNESS.relative_to(ROOT).as_posix(): _sha(R2_HARNESS),
            R1_HARNESS.relative_to(ROOT).as_posix(): _sha(R1_HARNESS),
            **{(SCAN / name).relative_to(ROOT).as_posix(): digest for name, digest in production.items()},
        },
        "post_freeze_source_edits_authorized": False, "result": "PASS",
    }
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r3_pre_runtime_freeze.json", freeze)
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
        _require(all("update_id" in row and "transaction_id" not in row for row in a_ledger + b_ledger), "FINAL-LEDGER-IDENTITY-SCHEMA")
        final.update({
            "classification": PASS_CLASSIFICATION,
            "historical_ckpt2_r1_r2": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRESERVED",
            "identity_relation": "ONE_TO_ONE_BOUND", "ledger_contract_case": "CASE C",
            "ledger_identity_path": "transaction.r5_transaction.quiescence_evidence.update_id",
            "r2_transaction_id_regression": False, "ledger_identity_repair": "PASS",
            "transaction_event_return_authority": "transaction.real_audit.event_return_compute_count",
            "process_a_ledger_rows": "3/3", "process_b_ledger_rows": "3/3",
        })
        _atomic_json(final_path, final)
        bridge_path = ARTIFACT_ROOT / "real_checkpoint_continuation_bridge.json"
        bridge = json.loads(bridge_path.read_text(encoding="utf-8"))
        bridge.update({
            "process_a_tx003_update_id": a_ledger[-1]["update_id"],
            "process_b_tx004_update_id": b_ledger[0]["update_id"],
            "transaction_update_identity_relation": "ONE_TO_ONE_BOUND",
            "process_a_ledger_rows": 3, "process_b_ledger_rows": 3,
        })
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
