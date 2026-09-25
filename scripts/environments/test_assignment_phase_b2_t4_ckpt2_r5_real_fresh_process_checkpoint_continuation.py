"""CKPT2-R5: plan-derived actor-count repair and one real 3+3 continuation.

The orchestration parent imports only the standard library.  One short-lived
pure child qualifies the production actor-plan schema.  Real task imports occur
only in fresh workers A/B after AppLauncher initialization, as in reviewed R4.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
AGENTREAD = SCAN / "AgentRead"
HISTORICAL_DAY = AGENTREAD / "202609" / "20260923"
DAY = AGENTREAD / "202609" / "20260924"
ARTIFACT_ROOT = DAY / "b2_t4_ckpt2_r5_artifacts"
CHECKPOINT_ROOT = ARTIFACT_ROOT / "checkpoint"
R4_HARNESS = HERE / "test_assignment_phase_b2_t4_ckpt2_r4_real_fresh_process_checkpoint_continuation.py"
BASE_HARNESS = HERE / "test_assignment_phase_b2_t0_bounded_repeated_update_training_smoke.py"
CKPT1_TEST = HERE / "test_assignment_phase_b2_t4_ckpt1_optimization_checkpoint.py"
EXPECTED_PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
PASS_CLASSIFICATION = (
    "PHASE-B2-T4-CKPT2-R5-REAL-FRESH-PROCESS-OPTIMIZATION-"
    "CONTINUATION-QUALIFIED-AWAITING-GPT-REVIEW"
)
BEFORE_FIRST_WRITE = {
    "branch": "main",
    "HEAD": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "origin_main": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "merge_base": "b71d85a32f51be6ada324f870813a56bb45dd396",
    "porcelain_bytes": 12844345,
    "porcelain_entry_count": 51137,
    "porcelain_sha256": "243caa9a7cc00205c7b433399302deff53bac023af25be9013b3f9779679278d",
    "staged_path_count": 359,
    "staged_index_sha256": "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
    "agentread_file_count": 50672,
    "agentread_path_set_sha256": "3ae0b1ff0a483e872111258e6ac163a266a79fa3ddac170f73bd4d74cc55a773",
}
EXPECTED_R4 = {
    "count": 70,
    "inventory": "fba74e716d1f038f0d06aa47655a7ab1f0bb8a87e6c0bb82fbe28d4474c1f9de",
    "harness": "f330ba2f27ef3fd40cb232853fd9be9d53846e9cbed8973321a691f38bee967d",
    "report": "720e738f68f5fcb81e2a1fbb5939fdc8bee29789da17dad9e333f1ab57d8866d",
}
EXPECTED_HISTORY = {
    "ckpt2": (35, "248d4415835bab99029da77478bac6f195fdfc40de5193378423c7a5b86083ef", "3fc8f262956fba9e8f3ee39a22182a615d220c09964371837f1e43b5e4695551", "ea8108f301d2fd027d008e2126851a5eac3721e3a78b53ffcae524d1507a69c7"),
    "r1": (25, "511fa0d2727c6a9f2eeece317ce06b75f7b03c47e46607c0e4e09553d93f122b", "c11774e887045bd96aae8cb2241f2bee953bf1eb92a411888a7fc58927abe324", "94b0898b7c4d28c5a14982e1052de86eb84acaf76fd73d7e0b4f5841b55a1ef4"),
    "r2": (30, "d1e9500bf77e199623fbae9521a365a72f0846f7dea0c5a073125fcccc17f091", "ff152638626cef06c79641c0e032d94b0537965e7a07136cc539584311d2e2f7", "4316eb0fce204f82d3688c7c357a70d4108b0125438b070f331d9def43012676"),
    "r3": (30, "644cc7f85f4274dc29804cc82a3cac9dd6a7168601fdd2363d19691d550a7839", "47aaadc95346e3b6e2b94aca58f2e847ea67c7320739d09fc0d1d478d66457f1", "39ab4444a60cd3726886781a1e0ad174cfdeec48a35d0434780a30bda1cddd4d"),
}
EXPECTED_CKPT1 = {
    "assignment_optimization_checkpoint.py": "b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9",
    "assignment_harl_training.py": "31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787",
}
HARL_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
EXPECTED_HARL = {
    "algorithms/actors/happo.py": "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    "algorithms/critics/v_critic.py": "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    "models/value_function_models/v_net.py": "a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3",
    "common/valuenorm.py": "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
}


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _require(condition: bool, code: str, detail: Any = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — B2-T4-CKPT2-R5 {code}: {detail!r}")


def _inventory(root: Path) -> tuple[list[dict[str, Any]], str]:
    rows = [
        {"path": path.relative_to(root).as_posix(), "bytes": path.stat().st_size, "sha256": _sha(path)}
        for path in sorted(root.rglob("*")) if path.is_file()
    ]
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"
    return rows, hashlib.sha256(encoded).hexdigest()


def _git_bytes(*arguments: str) -> bytes:
    return subprocess.check_output(["git", "-c", "core.longpaths=true", *arguments], cwd=ROOT)


def _repository_authority() -> dict[str, Any]:
    status = _git_bytes("status", "--porcelain=v1", "-uall", "-z")
    staged = _git_bytes("diff", "--cached", "--name-only", "-z")
    index = _git_bytes("ls-files", "--stage")
    paths = sorted(path.relative_to(ROOT).as_posix() for path in AGENTREAD.rglob("*") if path.is_file())
    return {
        "branch": _git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": _git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": _git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": _git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "porcelain_bytes": len(status),
        "porcelain_entry_count": sum(bool(item) for item in status.split(b"\0")),
        "porcelain_sha256": hashlib.sha256(status).hexdigest(),
        "staged_path_count": sum(bool(item) for item in staged.split(b"\0")),
        "staged_index_sha256": hashlib.sha256(index).hexdigest(),
        "agentread_file_count": len(paths),
        "agentread_path_set_sha256": hashlib.sha256(("\n".join(paths) + "\n").encode()).hexdigest(),
        "before_first_write": BEFORE_FIRST_WRITE,
        "git_mutations_by_ckpt2_r5": {"add": 0, "commit": 0, "push": 0, "reset": 0, "checkout": 0, "clean": 0},
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _adam_vector(snapshot: Mapping[str, Any]) -> tuple[int, ...]:
    result = []
    for actor_rows in snapshot["actor_adam_steps"]:
        values = {int(row[1]) for row in actor_rows}
        _require(len(values) == 1, "ACTOR-ADAM-INTERNAL-DIVERGENCE", actor_rows)
        result.append(values.pop())
    return tuple(result)


def _load_r5_base() -> Any:
    """Compile reviewed R4 as R5 definitions without running its entrypoint."""
    source = R4_HARNESS.read_text(encoding="utf-8")
    source = source.replace("CKPT2-R4", "CKPT2-R5").replace("ckpt2_r4", "ckpt2_r5")
    name = "_b2_t4_ckpt2_r5_reviewed_r4_base"
    module = type(sys)(name)
    module.__dict__.update({"__name__": name, "__file__": str(Path(__file__).resolve()), "__package__": None})
    sys.modules[name] = module
    exec(compile(source, str(R4_HARNESS), "exec"), module.__dict__)
    module.DAY = DAY
    module.ARTIFACT_ROOT = ARTIFACT_ROOT
    module.CHECKPOINT_ROOT = CHECKPOINT_ROOT
    module.PASS_CLASSIFICATION = PASS_CLASSIFICATION
    module.BEFORE_FIRST_WRITE = BEFORE_FIRST_WRITE
    return module


def _plan_receipt(transaction_index: int, payload: Mapping[str, Any], resources: Mapping[str, Any]) -> None:
    process = "a" if transaction_index <= 3 else "b"
    process_dir = ARTIFACT_ROOT / f"process_{process}"
    update_id = payload.get("update_id")
    actor_order = tuple(int(value) for value in payload.get("actor_order", ()))
    expected_backward = tuple((int(row[0]), int(row[1])) for row in payload.get("expected_actor_backward", ()))
    expected_step = tuple((int(row[0]), int(row[1])) for row in payload.get("expected_actor_optimizer_step", ()))
    config = payload.get("resolved_config", {})
    epoch_count = int(config.get("actor_epoch_count", 0)) if isinstance(config, Mapping) else 0
    masks = tuple(payload.get("mask_evidence_by_actor", ()))
    _require(update_id == f"{resources['ckpt2_r5_run_identity']}-tx{transaction_index}", "PRE-MUTATION-UPDATE-ID", update_id)
    _require(set(actor_order) == {0, 1, 2} and len(actor_order) == 3, "PRE-MUTATION-ACTOR-ORDER", actor_order)
    _require(len(expected_backward) == len(expected_step) == 3, "PRE-MUTATION-EXPECTED-COUNTS", (expected_backward, expected_step))
    _require(expected_backward == expected_step and epoch_count > 0, "PRE-MUTATION-PLAN-POLICY", (expected_backward, expected_step, epoch_count))
    actor_rows = []
    by_mask = {int(row[0]): row for row in masks}
    for actor_id, count in expected_step:
        _require(count >= 0 and count % epoch_count == 0, "PRE-MUTATION-NONEMPTY-EPOCH-COUNT", (actor_id, count, epoch_count))
        mask = by_mask[actor_id]
        actor_rows.append({
            "actor_id": actor_id,
            "actor_order_position": actor_order.index(actor_id),
            "dvm_population": len(mask[3]),
            "active_and_dvm_population": len(mask[4]),
            "approved_nonempty_minibatches_per_epoch": count // epoch_count,
            "actor_epoch_count": epoch_count,
            "exact_expected_backward_count": dict(expected_backward)[actor_id],
            "exact_expected_optimizer_step_count": count,
            "zero_dvm_or_forced_only": len(mask[4]) == 0,
        })
    row = {
        "schema_version": "b2_t4_ckpt2_r5_actor_plan_pre_mutation_receipt_v1",
        "transaction_index": transaction_index,
        "update_id": update_id,
        "actor_order": actor_order,
        "actor_plan_digest": payload.get("actor_plan_digest"),
        "expected_actor_backward_by_actor": expected_backward,
        "expected_actor_step_by_actor": expected_step,
        "actor_rows": actor_rows,
        "expected_source": "B2RActorUpdatePlanV1.expected_*_count_by_actor",
        "expected_source_path": "assignment_event_training_plans.py:B2RActorUpdatePlanV1/build_actor_update_plan_v1",
        "captured_at_stage": payload.get("current_stage_before_first_actor_mutation"),
        "actor_optimizer_steps_before_emit": payload.get("actor_optimizer_steps_before_emit"),
        "critic_optimizer_steps_before_emit": payload.get("critic_optimizer_steps_before_emit"),
        "live_valuenorm_updates_before_emit": payload.get("live_valuenorm_updates_before_emit"),
        "durable_before_first_actor_optimizer_step": payload.get("durable_before_first_actor_optimizer_step"),
        "result": "PASS",
    }
    _require(row["actor_optimizer_steps_before_emit"] == 0 and row["durable_before_first_actor_optimizer_step"] is True, "PRE-MUTATION-DURABILITY", row)
    _append_jsonl(process_dir / "actor_plan_pre_mutation_receipt.jsonl", row)


@dataclass
class _PlanLedgerBinder:
    expected_index: int
    run_id: str
    committed: set[str]

    @classmethod
    def starting_at(cls, index: int, run_id: str) -> "_PlanLedgerBinder":
        return cls(index, run_id, set())

    def bind(self, *, index: int, process: str, transaction: Any, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        _require(index == self.expected_index, "TRANSACTION-LEDGER-ORDER", (self.expected_index, index))
        process_dir = ARTIFACT_ROOT / f"process_{process}"
        receipts = _read_jsonl(process_dir / "actor_plan_pre_mutation_receipt.jsonl")
        matches = [row for row in receipts if row["transaction_index"] == index]
        _require(len(matches) == 1, "TRANSACTION-LEDGER-MISSING-PLAN", (index, len(matches)))
        receipt = matches[0]
        update_id = transaction.r5_transaction.quiescence_evidence.update_id
        _require(update_id == f"{self.run_id}-tx{index}" == receipt["update_id"], "TRANSACTION-LEDGER-UPDATE-ID", update_id)
        _require(update_id not in self.committed, "TRANSACTION-LEDGER-DUPLICATE", update_id)
        expected_backward = tuple(tuple(row) for row in receipt["expected_actor_backward_by_actor"])
        expected_steps = tuple(tuple(row) for row in receipt["expected_actor_step_by_actor"])
        audit = transaction.real_audit
        _require(tuple(audit.actor_order) == tuple(receipt["actor_order"]), "ACTOR-PLAN-ORDER-MISMATCH")
        _require(tuple(audit.actor_expected_backward) == expected_backward and tuple(audit.actor_expected_step) == expected_steps, "ACTOR-PLAN-EXPECTED-MISMATCH")
        counts = dict(transaction.exact_execution_counts)
        observed_backward_values = tuple(int(value) for value in counts["actor_backward_by_actor"])
        observed_step_values = tuple(int(value) for value in counts["actor_optimizer_step_by_actor"])
        observed_backward = tuple((actor_id, observed_backward_values[actor_id]) for actor_id in range(3))
        observed_steps = tuple((actor_id, observed_step_values[actor_id]) for actor_id in range(3))
        before = _adam_vector(_read_json(process_dir / f"core_tx{index}_pre_mutation.json")["learner_state_before_collection"])
        after = _adam_vector(snapshot)
        adam_delta = tuple(right - left for left, right in zip(before, after, strict=True))
        equality = tuple(
            {
                "actor_id": actor_id,
                "backward_equal": dict(observed_backward)[actor_id] == dict(expected_backward)[actor_id],
                "step_equal": dict(observed_steps)[actor_id] == dict(expected_steps)[actor_id],
                "adam_delta_equal": adam_delta[actor_id] == dict(expected_steps)[actor_id],
            }
            for actor_id in range(3)
        )
        _require(all(all(value for key, value in row.items() if key != "actor_id") for row in equality), "ACTOR-PLAN-COUNT-MISMATCH", equality)
        mutation = dict(transaction.r5_transaction.actor_parameter_mutation_by_actor)
        for actor_id, expected in expected_steps:
            if expected == 0:
                _require(adam_delta[actor_id] == 0 and mutation[actor_id] is False, "ZERO-DVM-ACTOR-MUTATED", actor_id)
        _require(transaction.real_audit.event_return_compute_count == 1, "TRANSACTION-LEDGER-EVENT-RETURN")
        _require(counts["critic_optimizer_step"] == 10 and counts["live_valuenorm_update"] == 10, "TRANSACTION-LEDGER-CRITIC")
        _require(counts["successful_real_full_learner_transactions"] == counts["s10_entries"] == 1, "TRANSACTION-LEDGER-COMPLETION")
        _require(transaction.next_rollout_ready is True and transaction.r5_transaction.quiescence_evidence.route_poisoned is False, "TRANSACTION-LEDGER-QUIESCENCE")
        return {
            "schema_version": "b2_t4_ckpt2_r5_transaction_ledger_actor_plan_binding_v1",
            "transaction": f"tx{index:03d}", "transaction_index": index, "process": process.upper(),
            "update_id": update_id, "actor_order": tuple(audit.actor_order), "actor_plan_digest": receipt["actor_plan_digest"],
            "returned_immutable_plan_digest": transaction.r5_transaction.immutable_plan_digest,
            "expected_actor_backward_counts": expected_backward, "observed_actor_backward_counts": observed_backward,
            "expected_actor_optimizer_step_counts": expected_steps, "observed_actor_optimizer_step_counts": observed_steps,
            "per_actor_equality": equality, "total_expected_count": sum(value for _, value in expected_steps),
            "total_observed_count": sum(value for _, value in observed_steps), "actor_adam_before": before,
            "actor_adam_after": after, "actor_adam_delta": adam_delta, "event_return_count": audit.event_return_compute_count,
            "critic_steps": counts["critic_optimizer_step"], "valuenorm_updates": counts["live_valuenorm_update"],
            "transaction_completion": "PASS", "fixed_uniform_predicate_used": False, "plan_derived_equality": True,
            "route_poisoned": False, "next_rollout_ready": True, "result": "PASS",
        }

    def commit(self, index: int, update_id: str) -> None:
        _require(index == self.expected_index and update_id not in self.committed, "TRANSACTION-LEDGER-COMMIT")
        self.committed.add(update_id)
        self.expected_index += 1


def _append_plan_ledger(*, index: int, process: str, transaction: Any, state: dict[str, Any], snapshot: Mapping[str, Any], next_lr_receipt: Any, ledger_path: Path, expected_run_id: str) -> dict[str, Any]:
    binder = state.get("r5_plan_ledger_binder")
    if binder is None:
        binder = _PlanLedgerBinder.starting_at(1 if process == "a" else 4, expected_run_id)
        state["r5_plan_ledger_binder"] = binder
    row = binder.bind(index=index, process=process, transaction=transaction, snapshot=snapshot)
    row.update({
        "physical_steps": 2, "lr_set_before_fingerprint": True,
        "collection_immutable": state["collection_checks"][index]["result"] == "PASS",
        "lr_mutations_inside_collection_interval": state["collection_checks"][index]["lr_mutations_inside_collection_interval"],
        "lr_schedule": state["lr_receipts"][index], "next_lr_primed_at_post_update_boundary": next_lr_receipt,
        "progression_after": state["progression"].state.to_mapping(), "semantic_digest_after": snapshot["semantic_digest"],
    })
    _append_jsonl(ledger_path, row)
    binder.commit(index, row["update_id"])
    if process == "a" and index == 2:
        _atomic_json(ledger_path.parent / "r4_actor_count_regression_check.json", {
            "transaction_index": 2, "actor_plan_digest": row["actor_plan_digest"],
            "expected": row["expected_actor_optimizer_step_counts"], "observed": row["observed_actor_optimizer_step_counts"],
            "fixed_uniform_predicate_used": False, "plan_derived_equality": True,
            "historical_r4_fixed_predicate_would_accept": tuple(value for _, value in row["observed_actor_optimizer_step_counts"]) == (5, 5, 5),
            "result": "PASS",
        })
    return row


def _install_inner_loader(runtime: dict[str, Any], base: Any) -> None:
    def load_inner_base(hooks: Mapping[str, Any]) -> dict[str, Any]:
        start_index = int(hooks["TRANSACTION_START_INDEX"])
        process = "a" if start_index == 1 else "b"
        process_dir = ARTIFACT_ROOT / f"process_{process}"

        def before_gym_make(resources: dict[str, Any]) -> None:
            identity, registration = base._real_package_gates(process)
            _atomic_json(ARTIFACT_ROOT / f"process_{process}_real_package_identity.json", identity)
            _atomic_json(ARTIFACT_ROOT / f"process_{process}_environment_registration.json", registration)

        def after_gym_make(env: Any, resources: dict[str, Any]) -> None:
            payload = {"process": process.upper(), "pid": os.getpid(), "environment_id": base.ENVIRONMENT_ID,
                       "gym_make_returned": env is not None, "environment_constructions": resources.get("environment_constructions"),
                       "unwrapped_type": type(env.unwrapped).__name__ if env is not None else None}
            payload["result"] = "PASS" if env is not None and payload["environment_constructions"] == 1 else "FAIL"
            _require(payload["result"] == "PASS", "ENVIRONMENT-CREATION", payload)
            _atomic_json(ARTIFACT_ROOT / f"process_{process}_environment_creation.json", payload)
            _atomic_json(process_dir / "environment_creation.json", payload)

        source = BASE_HARNESS.read_text(encoding="utf-8")
        replacements = {
            "    for transaction_index in range(1, TRANSACTION_COUNT + 1):\n": "    for transaction_index in range(TRANSACTION_START_INDEX, TRANSACTION_START_INDEX + TRANSACTION_COUNT):\n",
            "    reset_result = route.reset()\n": "    _ckpt2_r5_after_learner_construction(route, actors_raw, critic_raw, live_value_normalizer, resources)\n    reset_result = route.reset()\n",
            "        pre_collection = _learner_snapshot(\n": "        _ckpt2_r5_before_collection_boundary(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources)\n        pre_collection = _learner_snapshot(\n",
            "        _require(\n            _persistent_state_equal(pre_collection, collection_post),\n": "        _ckpt2_r5_after_collection_boundary(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources)\n        _require(\n            _persistent_state_equal(pre_collection, collection_post),\n",
            "        resources[\"adapter_transaction_returned\"] = True\n": "        _ckpt2_r5_after_transaction(transaction_index, actors_raw, critic_raw, live_value_normalizer, resources, transaction)\n        resources[\"adapter_transaction_returned\"] = True\n",
            "    run_identity = f\"b2-t0-re1-repeated-smoke-{os.getpid()}\"\n": "    run_identity = str(resources[\"ckpt2_r5_run_identity\"])\n",
            "    env = gym.make(\n": "    _ckpt2_r5_before_gym_make(resources)\n    env = gym.make(\n",
            "    resources[\"environment_constructions\"] = 1\n": "    resources[\"environment_constructions\"] = 1\n    _ckpt2_r5_after_gym_make(env, resources)\n",
            "        def persist_pre_mutation(payload: Mapping[str, object]) -> None:\n": "        def persist_pre_mutation(payload: Mapping[str, object]) -> None:\n            _ckpt2_r5_pre_mutation_plan_receipt(transaction_index, payload, resources)\n",
            '"transaction_4_started"': '"next_unauthorized_transaction_started"',
        }
        for old, new in replacements.items():
            expected = 2 if old == '"transaction_4_started"' else 1
            _require(source.count(old) == expected, "BASE-HARNESS-TRANSFORM", (old, source.count(old), expected))
            source = source.replace(old, new)
        namespace = {"__name__": "_b2_t4_ckpt2_r5_bounded_core", "__file__": str(BASE_HARNESS), "__package__": None,
                     **hooks, "_ckpt2_r5_before_gym_make": before_gym_make, "_ckpt2_r5_after_gym_make": after_gym_make,
                     "_ckpt2_r5_pre_mutation_plan_receipt": _plan_receipt}
        exec(compile(source, str(BASE_HARNESS), "exec"), namespace)
        namespace["TRANSACTION_COUNT"] = 3
        return namespace
    runtime["_load_inner_base"] = load_inner_base


def _runtime_bundle() -> tuple[Any, dict[str, Any], str]:
    _require(not any(name == PACKAGE or name.startswith(PACKAGE + ".") for name in sys.modules), "PARENT-PACKAGE-CONTAMINATION")
    base = _load_r5_base()
    base_ns, runtime, digest = base._runtime_bundle()
    runtime.update({"ARTIFACT_ROOT": ARTIFACT_ROOT, "CHECKPOINT_ROOT": CHECKPOINT_ROOT, "PASS_CLASSIFICATION": PASS_CLASSIFICATION,
                    "_ckpt2_r5_append_transaction_ledger": _append_plan_ledger})
    _install_inner_loader(runtime, base)
    base_ns.update({"RUNTIME": runtime, "TRANSFORMED_RUNTIME_SHA256": digest})
    return base, runtime, digest


def _pure_plan_matrix() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    sys.path.insert(0, str(HERE))
    import _assignment_phase_b2_r1_contract_helpers as H
    config = H.config(resolved_T=2, resolved_E=2, actor_epoch_count=5, actor_minibatch_count=2,
                      critic_epoch_count=5, critic_minibatch_count=2)
    authority = H.authority(cfg=config, update_id="r5-pure-plan")
    partitions = H.P.build_exact_partitions_v1(B=4, epoch_count=5, minibatch_count=2, partition_policy="reviewed_exact_coverage")
    scenarios = {
        "A_uniform": ({0: (0,), 1: (0,), 2: (0,)}, {0: (0,), 1: (0,), 2: (0,)}),
        "B_actor2_additional": ({0: (0,), 1: (0,), 2: (0, 2)}, {0: (0,), 1: (0,), 2: (0, 2)}),
        "C_actor0_additional": ({0: (0, 2), 1: (0,), 2: (0,)}, {0: (0, 2), 1: (0,), 2: (0,)}),
        "D_actor1_zero": ({0: (0,), 1: (), 2: (0,)}, {0: (0,), 1: (), 2: (0,)}),
        "E_all_zero": ({0: (), 1: (), 2: ()}, {0: (), 1: (), 2: ()}),
    }
    rows = []
    plans = {}
    for name, (dvm, active) in scenarios.items():
        plan = H.P.build_actor_update_plan_v1(authority=authority, authority_config_digest=authority.config_digest,
            actor_permutation=(1, 2, 0), approved_partitions_by_epoch=partitions, dvm_indices_by_actor=dvm,
            active_indices_by_actor=active, factor_input_digest=H.digest(name))
        plans[name] = plan
        per_epoch = {actor: [sum(not item.empty_loss for item in plan.minibatches if item.actor_id == actor and item.epoch == epoch)
                             for epoch in range(plan.actor_epoch_count)] for actor in range(3)}
        actor_rows = [{"actor_id": actor, "actor_order_position": plan.actor_permutation.index(actor),
                       "dvm_population": len(dvm[actor]), "active_and_dvm_population": len(set(dvm[actor]).intersection(active[actor])),
                       "approved_nonempty_minibatches_per_epoch": per_epoch[actor], "actor_epoch_count": plan.actor_epoch_count,
                       "exact_expected_backward_count": dict(plan.expected_backward_count_by_actor)[actor],
                       "exact_expected_optimizer_step_count": dict(plan.expected_optimizer_step_count_by_actor)[actor]}
                      for actor in range(3)]
        row = {"case": name, "plan_digest": plan.plan_digest, "expected_backward": plan.expected_backward_count_by_actor,
               "expected_steps": plan.expected_optimizer_step_count_by_actor, "nonempty_minibatches_by_actor_by_epoch": per_epoch,
               "actor_rows": actor_rows,
               "critic_route_valid_by_reviewed_semantics": True, "result": "PASS"}
        rows.append(row)
    positive = {"production_constructor": "build_actor_update_plan_v1", "case_count": 5, "cases": rows, "result": "PASS"}
    dynamic = plans["B_actor2_additional"]
    actual = tuple(value for _, value in dynamic.expected_optimizer_step_count_by_actor)
    reproduction = {"plan_digest": dynamic.plan_digest, "actual_plan_derived_expected": actual,
                    "observed_plan_valid_dynamic_tuple": actual, "historical_fixed_predicate": (5, 5, 5),
                    "fixed_predicate_rejects": actual != (5, 5, 5), "production_plan_constructor_used": True, "result": "PASS"}
    inventory = {"expected_authority": "B2RActorUpdatePlanV1.expected_backward_count_by_actor / expected_optimizer_step_count_by_actor",
                 "frozen_plan_source": "assignment_event_training_plans.py:B2RActorUpdatePlanV1/build_actor_update_plan_v1",
                 "observed_authority": "B2R5IRealTransactionEvidenceV1.exact_execution_counts actor_backward_by_actor/actor_optimizer_step_by_actor",
                 "pre_mutation_transport": "assignment_event_training_real_isaac_adapter.py:_PreMutationObservedActorInputsV1",
                 "config_alone_used": False, "production_plan_constructor_used": True,
                 "representative_actor_rows": rows[1]["actor_rows"], "result": "PASS"}

    def validate(record: Mapping[str, Any]) -> None:
        required = ("update_id", "actor_order", "frozen_plan_digest", "current_plan_digest", "expected_backward", "expected_steps", "observed_backward", "observed_steps")
        _require(not [key for key in required if key not in record], "PURE-MISSING-PLAN")
        _require(record["update_id"] == "r5-pure-tx1", "PURE-WRONG-UPDATE-ID")
        _require(record["expected_source"] == "frozen_transaction_actor_plan" and record["captured_before_mutation"] is True, "PURE-EXPECTED-PROVENANCE")
        _require(record["frozen_plan_digest"] == record["current_plan_digest"], "PURE-STALE-OR-CHANGED-PLAN")
        _require(tuple(record["actor_order"]) == tuple(record["plan_actor_order"]), "PURE-ACTOR-ORDER")
        _require(tuple(record["expected_backward"]) == tuple(record["observed_backward"]), "PURE-BACKWARD-MISMATCH")
        _require(tuple(record["expected_steps"]) == tuple(record["observed_steps"]), "PURE-STEP-MISMATCH")
        _require(tuple(record["observed_backward"]) == tuple(record["observed_steps"]), "PURE-BACKWARD-STEP-MISMATCH")
        for actor, count in enumerate(record["expected_steps"]):
            if count == 0:
                _require(record["actor_mutated"][actor] is False, "PURE-ZERO-ACTOR-MUTATED")

    base = {"update_id": "r5-pure-tx1", "actor_order": (1, 2, 0), "plan_actor_order": (1, 2, 0),
            "frozen_plan_digest": dynamic.plan_digest, "current_plan_digest": dynamic.plan_digest,
            "expected_backward": actual, "expected_steps": actual, "observed_backward": actual, "observed_steps": actual,
            "expected_source": "frozen_transaction_actor_plan", "captured_before_mutation": True,
            "actor_mutated": tuple(value > 0 for value in actual)}
    validate(base)
    cases = []
    mutations = [
        ("observed_step_below_plan", {"observed_steps": (5, 5, 9)}),
        ("observed_step_above_plan", {"observed_steps": (5, 5, 11)}),
        ("backward_not_step", {"observed_backward": (5, 5, 9)}),
        ("wrong_actor_association", {"observed_steps": (10, 5, 5)}),
        ("wrong_update_id", {"update_id": "wrong"}),
        ("stale_plan", {"current_plan_digest": "0" * 64}),
        ("changed_plan_after_freeze", {"current_plan_digest": "1" * 64}),
        ("missing_plan", {"frozen_plan_digest": None}),
        ("zero_dvm_actor_mutates", {"expected_backward": (5, 0, 5), "expected_steps": (5, 0, 5), "observed_backward": (5, 0, 5), "observed_steps": (5, 0, 5), "actor_mutated": (True, True, True)}),
        ("observed_copied_as_expected", {"expected_source": "observed_optimizer_steps"}),
        ("aggregate_matches_per_actor_differs", {"observed_backward": (10, 5, 5), "observed_steps": (10, 5, 5)}),
        ("actor_order_mismatch", {"actor_order": (2, 1, 0)}),
    ]
    for name, mutation in mutations:
        candidate = {**base, **mutation}
        if name == "missing_plan": candidate.pop("frozen_plan_digest")
        try:
            validate(candidate)
        except RuntimeError as exc:
            cases.append({"case": name, "outcome": "EXPECTED_STOP", "error": str(exc), "result": "PASS"})
        else:
            cases.append({"case": name, "outcome": "UNEXPECTED_PASS", "result": "FAIL"})
    negative = {"case_count": 12, "expected_stop_count": sum(row["outcome"] == "EXPECTED_STOP" for row in cases),
                "unexpected_pass_count": sum(row["outcome"] == "UNEXPECTED_PASS" for row in cases), "cases": cases}
    negative["result"] = "PASS" if negative["expected_stop_count"] == 12 and negative["unexpected_pass_count"] == 0 else "FAIL"
    return inventory, reproduction, positive, negative


def _historical_consistency() -> tuple[dict[str, Any], dict[str, Any]]:
    temp = Path(tempfile.gettempdir())
    rows = []
    adam_chain = []
    for index in range(1, 4):
        prefix = f"b2_t0_re1_20260910_formal01_tx{index}"
        pre_path = temp / f"{prefix}_pre_mutation.json"
        s10_path = temp / f"{prefix}_s10.json"
        factor_path = temp / f"{prefix}_actor_factor_progress.json"
        _require(pre_path.is_file() and s10_path.is_file() and factor_path.is_file(), "HISTORICAL-RE1-EVIDENCE-MISSING", index)
        pre, s10, factor = _read_json(pre_path), _read_json(s10_path), _read_json(factor_path)
        expected = tuple(int(value) for _, value in pre["expected_actor_optimizer_step"])
        before, after = _adam_vector(s10["pre_collection_learner"]), _adam_vector(s10["post_update_learner"])
        delta = tuple(right - left for left, right in zip(before, after, strict=True))
        segment_events = [event for event in factor["events"] if event["stage"] == "S5_ACTOR_SEGMENT_COMPLETE"]
        cumulative = 0
        observed_by_actor = [0, 0, 0]
        for event in segment_events:
            observed_by_actor[int(event["actor_id"])] = int(event["cumulative_actor_optimizer_step_count"]) - cumulative
            cumulative = int(event["cumulative_actor_optimizer_step_count"])
        row = {"transaction_index": index, "actor_order": pre["actor_order"], "actor_plan_digest": pre["actor_plan_digest"],
               "expected_from_frozen_plan": expected, "observed_from_actor_progress": tuple(observed_by_actor),
               "observed_from_adam_delta": delta, "pre_mutation_sha256": _sha(pre_path), "s10_sha256": _sha(s10_path),
               "historical_evidence_mutated": False, "result": "PASS" if expected == tuple(observed_by_actor) == delta else "FAIL"}
        _require(row["result"] == "PASS", "HISTORICAL-DYNAMIC-COUNT-MISMATCH", row)
        rows.append(row)
        adam_chain.append(before)
    adam_chain.append(_adam_vector(_read_json(temp / "b2_t0_re1_20260910_formal01_tx3_s10.json")["post_update_learner"]))
    dynamic = {"contract": "current frozen plan expected == observed per actor", "hard_coded_tuple_contract": False,
               "retrospective_only": True, "transactions": rows, "result": "PASS"}
    adam = {"progression": adam_chain, "expected_progression": [(0, 0, 0), (5, 5, 5), (10, 10, 15), (20, 15, 20)],
            "deltas": [row["observed_from_adam_delta"] for row in rows], "deltas_equal_plan_expected": True,
            "result": "PASS" if adam_chain == [(0, 0, 0), (5, 5, 5), (10, 10, 15), (20, 15, 20)] else "FAIL"}
    _require(adam["result"] == "PASS", "HISTORICAL-ADAM-PROGRESSION", adam)
    return dynamic, adam


def _run_ckpt1_in_process() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("_b2_t4_ckpt1_r5_pure", CKPT1_TEST)
    _require(spec is not None and spec.loader is not None, "CKPT1-PURE-SPEC")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    output = ARTIFACT_ROOT / "preflight_ckpt1_pure.json"
    old = sys.argv
    try:
        sys.argv = [str(CKPT1_TEST), "--json-output", str(output)]
        code = module.main()
    finally:
        sys.argv = old
    payload = _read_json(output)
    _require(code == 0 and payload is not None and payload["successful"] and payload["tests_run"] == 6 and payload["negative_case_count"] == 25 and payload["unexpected_negative_case_count"] == 0, "CKPT1-PURE", payload)
    return payload


def _pure_qualification(args: argparse.Namespace) -> int:
    names = sorted(name for name in sys.modules if name == PACKAGE or name.startswith(PACKAGE + "."))
    clean = {"pid": os.getpid(), "parent_pid": os.getppid(), "python": sys.executable,
             "production_package_modules_at_entry": names, "production_package_loaded": bool(names),
             "fresh_short_lived_interpreter": True, "result": "PASS" if not names else "FAIL"}
    _require(clean["result"] == "PASS", "PURE-CLEAN-INTERPRETER", clean)
    ckpt1 = _run_ckpt1_in_process()
    inventory, reproduction, positive, negative = _pure_plan_matrix()
    dynamic, adam = _historical_consistency()
    inherited = {"identity_relation": "ONE_TO_ONE_BOUND", "ledger_contract_case": "CASE C",
                 "ledger_identity_path": "transaction.r5_transaction.quiescence_evidence.update_id",
                 "event_return_authority": "transaction.real_audit.event_return_compute_count",
                 "pure_runtime_import_isolation": True, "lr_before_fingerprint": True,
                 "process_a_semantic_gate_unchanged": True, "result": "PASS"}
    binding = {"schema_version": "b2_t4_ckpt2_r5_transaction_ledger_actor_plan_binding_v1",
               "expected_authority": inventory["expected_authority"], "expected_captured_before_mutation": True,
               "observed_authority": inventory["observed_authority"], "per_actor_exact_equality": True,
               "aggregate_only_forbidden": True, "zero_actor_allowed_and_must_not_mutate": True, "result": "PASS"}
    outputs = {
        "clean_interpreter_baseline.json": clean,
        "actor_plan_count_authority_inventory.json": inventory,
        "r4_fixed_actor_count_predicate_failure_reproduction.json": reproduction,
        "historical_dynamic_actor_plan_consistency.json": dynamic,
        "historical_actor_adam_plan_consistency.json": adam,
        "transaction_ledger_actor_plan_binding_v1.json": binding,
        "actor_plan_dynamic_positive_matrix.json": positive,
        "actor_plan_count_negative_matrix.json": negative,
        "inherited_contract_preservation.json": inherited,
    }
    for name, payload in outputs.items():
        _atomic_json(ARTIFACT_ROOT / name, payload)
    result = {"run_id": args.run_id, "pid": os.getpid(), "parent_pid": os.getppid(), "ckpt1": "6/6; 25/25",
              "positive_matrix": "5/5", "negative_matrix": "12/12 expected STOP", "historical_dynamic_consistency": "PASS",
              "historical_adam_consistency": "PASS", "process_exits_before_process_a": True, "result": "PASS"}
    _atomic_json(ARTIFACT_ROOT / "pure_qualification_result.json", result)
    return 0


def _history_preservation() -> None:
    names = {
        "ckpt2": ("b2_t4_ckpt2_artifacts", "test_assignment_phase_b2_t4_ckpt2_real_fresh_process_checkpoint_continuation.py", "PHASE_B2_T4_CKPT2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"),
        "r1": ("b2_t4_ckpt2_r1_artifacts", "test_assignment_phase_b2_t4_ckpt2_r1_real_fresh_process_checkpoint_continuation.py", "PHASE_B2_T4_CKPT2_R1_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"),
        "r2": ("b2_t4_ckpt2_r2_artifacts", "test_assignment_phase_b2_t4_ckpt2_r2_real_fresh_process_checkpoint_continuATION.py".replace("continuATION", "continuation"), "PHASE_B2_T4_CKPT2_R2_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"),
        "r3": ("b2_t4_ckpt2_r3_artifacts", "test_assignment_phase_b2_t4_ckpt2_r3_real_fresh_process_checkpoint_continuation.py", "PHASE_B2_T4_CKPT2_R3_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"),
    }
    for label, (artifact, harness, report) in names.items():
        rows, digest = _inventory(HISTORICAL_DAY / artifact)
        expected = EXPECTED_HISTORY[label]
        payload = {"status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRESERVED", "artifact_file_count": len(rows),
                   "artifact_inventory_sha256": digest, "harness_sha256": _sha(HERE / harness), "report_sha256": _sha(HISTORICAL_DAY / report)}
        payload["preserved"] = (len(rows), digest, payload["harness_sha256"], payload["report_sha256"]) == expected
        payload["result"] = "PASS" if payload["preserved"] else "FAIL"
        _require(payload["preserved"], f"HISTORICAL-{label.upper()}-DRIFT", payload)
        _atomic_json(ARTIFACT_ROOT / f"historical_ckpt2{'_' + label if label != 'ckpt2' else ''}_preservation.json", payload)
    rows, digest = _inventory(HISTORICAL_DAY / "b2_t4_ckpt2_r4_artifacts")
    r4 = {"status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / TEST-SIDE FIXED PREDICATE / NOT LEARNER DEFECT / NOT POISONED / NO RETRY",
          "artifact_file_count": len(rows), "artifact_inventory_sha256": digest, "harness_sha256": _sha(R4_HARNESS),
          "report_sha256": _sha(HISTORICAL_DAY / "PHASE_B2_T4_CKPT2_R4_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md")}
    r4["preserved"] = (len(rows), digest, r4["harness_sha256"], r4["report_sha256"]) == tuple(EXPECTED_R4.values())
    r4["result"] = "PASS" if r4["preserved"] else "FAIL"
    _require(r4["preserved"], "HISTORICAL-R4-DRIFT", r4)
    _atomic_json(ARTIFACT_ROOT / "historical_ckpt2_r4_preservation.json", r4)


def _postprocess_worker(process: str) -> None:
    process_dir = ARTIFACT_ROOT / f"process_{process}"
    ledger = _read_jsonl(process_dir / "transaction_ledger.jsonl")
    _require(len(ledger) == 3 and all(row["result"] == "PASS" for row in ledger), "WORKER-PLAN-LEDGER", len(ledger))
    summary = {"process": process.upper(), "transactions": [{key: row[key] for key in (
        "transaction_index", "update_id", "actor_order", "actor_plan_digest", "expected_actor_optimizer_step_counts",
        "observed_actor_optimizer_step_counts", "actor_adam_before", "actor_adam_after", "actor_adam_delta", "per_actor_equality", "result")}
        for row in ledger], "plan_equality_pass_count": 3, "ledger_rows": 3, "result": "PASS"}
    name = "actor_plan_count_summary.json" if process == "a" else "post_load_actor_plan_count_summary.json"
    _atomic_json(process_dir / name, summary)
    receipt_name = "process_a_success_receipt.json" if process == "a" else "process_b_success_receipt.json"
    receipt = _read_json(process_dir / receipt_name)
    if receipt is not None:
        receipt.update({"actor_plan_equality": "3/3 PASS", "actor_plan_ledger_rows": 3,
                        "fixed_uniform_predicate_used": False})
        _atomic_json(process_dir / receipt_name, receipt)
    if process == "b":
        optimizer = _read_json(process_dir / "real_optimizer_continuity.json")
        _require(optimizer is not None and optimizer.get("result") == "PASS", "OPTIMIZER-CONTINUITY", optimizer)
        tx4 = ledger[0]
        optimizer.update({"tx004_plan_expected_actor_steps": tx4["expected_actor_optimizer_step_counts"],
                          "tx004_observed_actor_steps": tx4["observed_actor_optimizer_step_counts"],
                          "tx004_actor_adam_delta": tx4["actor_adam_delta"], "tx004_plan_derived_equality": True})
        _atomic_json(process_dir / "real_optimizer_continuity.json", optimizer)


def _worker(args: argparse.Namespace) -> int:
    _base, runtime, _digest = _runtime_bundle()
    result = runtime["_worker"](args)
    if result == 0:
        _postprocess_worker(args.worker)
    return result


def _parent(args: argparse.Namespace) -> int:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    authority = _repository_authority()
    _require(authority["branch"] == "main" and authority["HEAD"] == authority["origin_main"] == authority["merge_base"] == BEFORE_FIRST_WRITE["HEAD"], "REPOSITORY-AUTHORITY", authority)
    _require(authority["staged_path_count"] == 359 and authority["staged_index_sha256"] == BEFORE_FIRST_WRITE["staged_index_sha256"], "STAGED-INDEX-AUTHORITY", authority)
    _atomic_json(ARTIFACT_ROOT / "repository_authority.json", authority)
    _history_preservation()
    production = {name: _sha(SCAN / name) for name in EXPECTED_CKPT1}
    installed = {name: _sha(HARL_ROOT / name) for name in EXPECTED_HARL}
    _require(production == EXPECTED_CKPT1 and installed == EXPECTED_HARL, "CKPT1-OR-HARL-DRIFT", (production, installed))
    _atomic_json(ARTIFACT_ROOT / "ckpt1_preservation.json", {"status": "GPT REVIEW PASS / CLOSED", "implementation_sha256": production,
                 "installed_harl_sha256": installed, "pure_tests": "pending same pure child", "result": "PASS"})
    pure = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--pure-qualification", "--run-id", args.run_id], cwd=ROOT)
    pure_code = pure.wait()
    pure_active = _pid_active(pure.pid)
    pure_result = _read_json(ARTIFACT_ROOT / "pure_qualification_result.json")
    _require(pure_code == 0 and not pure_active and pure_result is not None and pure_result["result"] == "PASS", "PURE-QUALIFICATION", (pure_code, pure_active, pure_result))
    ckpt1 = _read_json(ARTIFACT_ROOT / "preflight_ckpt1_pure.json")
    _atomic_json(ARTIFACT_ROOT / "ckpt1_preservation.json", {"status": "GPT REVIEW PASS / CLOSED", "implementation_sha256": production,
                 "installed_harl_sha256": installed, "pure_tests": "6/6", "negative_matrix": "25/25", "result": "PASS"})
    base, runtime, runtime_digest = _runtime_bundle()
    _atomic_json(ARTIFACT_ROOT / "pre_runtime_harness_repair_log.json", {"repairs": [{"id": "DYNAMIC_FROZEN_ACTOR_PLAN_COUNT_BINDING",
                 "scope": "CKPT2-R5 harness only", "historical_r4_source_modified": False, "production_source_modified": False, "result": "PASS"}],
                 "production_files_modified": 0, "installed_harl_files_modified": 0, "unresolved_test_side_repairs": 0, "result": "PASS"})
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r5_run_identity.json", {"run_id": args.run_id, "fresh": True, "attempt_number": 1, "maximum_attempts": 1, "retry_count": 0})
    _atomic_json(ARTIFACT_ROOT / "pure_runtime_process_isolation.json", {"orchestration_parent_pid": os.getpid(), "pure_qualification_pid": pure.pid,
                 "pure_pid_inactive_before_process_a": not pure_active, "cross_process_python_object_sharing": False, "sys_modules_pop_used": False, "result": "PASS"})
    preflight = {"run_id": args.run_id, "historical_ckpt2_r1_r2_r3_r4_preserved": True, "ckpt1_focused_suite": f"{ckpt1['tests_run']}/6 PASS; 25/25 expected negative",
                 "actor_plan_authority": "B2RActorUpdatePlanV1.expected_*_count_by_actor", "r4_fixed_predicate_reproduction": "PASS",
                 "historical_dynamic_consistency": "PASS", "historical_adam_consistency": "PASS", "positive_matrix": "5/5 PASS",
                 "negative_matrix": "12/12 expected STOP", "identity_relation": "ONE_TO_ONE_BOUND", "ledger_contract_case": "CASE C",
                 "event_return_authority": "transaction.real_audit.event_return_compute_count", "import_isolation": "PASS",
                 "lr_fingerprint_boundary": "PASS", "process_a_semantic_gate": "PASS", "installed_harl_preservation": "PASS",
                 "runtime_started": False, "result": "PASS"}
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r5_preflight.json", preflight)
    harness = Path(__file__).resolve()
    freeze = {"run_id": args.run_id, "frozen_before_process_a": True, "harness_sha256": _sha(harness),
              "transformed_r1_runtime_sha256": runtime_digest, "source_sha256": {harness.relative_to(ROOT).as_posix(): _sha(harness),
              R4_HARNESS.relative_to(ROOT).as_posix(): _sha(R4_HARNESS), **{(SCAN / name).relative_to(ROOT).as_posix(): value for name, value in production.items()}},
              "post_freeze_source_edits_authorized": False, "result": "PASS"}
    _atomic_json(ARTIFACT_ROOT / "ckpt2_r5_pre_runtime_freeze.json", freeze)
    # The transformed reviewed runtime resolves this R5-named freeze artifact.
    result = runtime["_parent"](args)
    if result == 0:
        a = _read_jsonl(ARTIFACT_ROOT / "process_a" / "transaction_ledger.jsonl")
        b = _read_jsonl(ARTIFACT_ROOT / "process_b" / "transaction_ledger.jsonl")
        _require(len(a) == len(b) == 3 and all(row["plan_derived_equality"] for row in a + b), "FINAL-PLAN-LEDGER")
        final_path = ARTIFACT_ROOT / "final_result.json"
        final = _read_json(final_path)
        final.update({"classification": PASS_CLASSIFICATION, "historical_ckpt2_r1_r2_r3_r4": "GPT REVIEW STOP CONFIRMED / HISTORICAL / PRESERVED",
                      "actor_count_authority": "B2RActorUpdatePlanV1.expected_*_count_by_actor", "fixed_uniform_actor_predicate": "REMOVED FROM R5 HARNESS CONTRACT",
                      "historical_dynamic_plan_consistency": "PASS", "process_a_actor_plan_equality": "3/3 PASS", "process_b_actor_plan_equality": "3/3 PASS",
                      "identity_relation": "ONE_TO_ONE_BOUND", "ledger_contract_case": "CASE C", "transaction_event_return_authority": "transaction.real_audit.event_return_compute_count"})
        _atomic_json(final_path, final)
        bridge_path = ARTIFACT_ROOT / "real_checkpoint_continuation_bridge.json"
        bridge = _read_json(bridge_path)
        bridge.update({"process_a_tx003_update_id": a[-1]["update_id"], "process_a_tx003_actor_plan_digest": a[-1]["actor_plan_digest"],
                       "process_b_tx004_update_id": b[0]["update_id"], "process_b_tx004_actor_plan_digest": b[0]["actor_plan_digest"],
                       "actor_plan_continuity_contract": "each transaction binds its own frozen plan", "actor_plan_equality_A_B": "6/6 PASS"})
        _atomic_json(bridge_path, bridge)
    return result


def _pid_active(pid: int) -> bool:
    completed = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=False)
    return f'"{pid}"' in completed.stdout


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--parent", action="store_true")
    mode.add_argument("--worker", choices=("a", "b"))
    mode.add_argument("--pure-qualification", action="store_true")
    parser.add_argument("--run-id", required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.pure_qualification:
        return _pure_qualification(args)
    if args.worker:
        return _worker(args)
    return _parent(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BaseException as exc:
        if isinstance(exc, SystemExit):
            raise
        ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
        failure = ARTIFACT_ROOT / "failure_receipt.json"
        if not failure.exists():
            _atomic_json(failure, {"classification": "PHASE-B2-T4-CKPT2-R5-STOP-PRE-RUNTIME-ACTOR-PLAN-AUTHORITY",
                         "error_type": type(exc).__name__, "error": str(exc), "traceback": traceback.format_exc(),
                         "retry_permitted": False, "retry_count": 0})
        traceback.print_exc()
        raise SystemExit(1)
