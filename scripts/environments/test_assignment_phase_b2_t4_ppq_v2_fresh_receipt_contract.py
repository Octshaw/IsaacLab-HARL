"""Pure/offline PPQ-V2 qualification. check writes nothing; final runs once."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as V2
import _assignment_phase_b2_t4_w2e_multi_update_completion as W2E
import test_assignment_phase_b2_t4_w2e_claim_evidence_contract as W2TEST
import test_assignment_phase_b2_t4_ppq_postprocess as V1TEST
import _assignment_phase_b2_t4_windows_evidence_persistence as PW


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DATE = SCAN / "AgentRead/202609/20260920"
OUT = DATE / "b2_t4_ppq_v2_artifacts"
SELF = Path(__file__).resolve()
HELPER = HERE / "_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py"
PW_HELPER = HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py"
W2I = DATE / "b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json"
V1_HELPER = HERE / "_assignment_phase_b2_t4_ppq_postprocess.py"
V1_SCHEMA = DATE / "b2_t4_ppq_artifacts/success_receipt_schema.json"
HISTORICAL = DATE / "b2_t4_re6_r1_artifacts"
HISTORICAL_MANIFEST = DATE / "b2_t4_ppq_artifacts/re6_r1_artifact_identity.json"
R2 = DATE / "b2_t4_re6_r2_artifacts"
PRODUCTION = {
    "full_transaction": SCAN / "assignment_event_training_full_transaction.py",
    "real_isaac_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
    "environment": SCAN / "scan_mobile_manipulator_env.py",
}
CONFIG = {"expected_transaction_count": 160, "expected_T": 2,
          "critic_records_per_tx": 41, "actor_factor_records_per_tx": 4}
REVIEWED = {
    "full_transaction": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "real_isaac_adapter": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
    "environment": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
    "w2e_selector": V2.W2E_SHA, "w2i_manifest": V2.W2I_SHA,
    "pw_helper": V2.PW_SHA,
    "ppq_v1_helper": "1bc419e96fe095ef15b70483abbbacca57580345d803d6ce83b211e68054352d",
    "ppq_v1_schema": "9423742d525acb154c789c4b99922cc366bc596decef1be783c0ac1ffc98e5f6",
    "re6_r1_harness": "858656975abef50adf6a143fe7f6bc68731756d2ad6378430acc6b9e3f3d049c",
}
R2_REVIEWED = {
    "final_result.json": "1caee8e6cde98f497831bdf50fd4aa113d8596e16b43dde9db5408ffd5bfa580",
    "ppq_fresh_success_receipt_contract_gap.json": "5a30b20a02a99e36e78b2eeee8b8a16b78a6451fe17d86797769e5617cf71089",
    "ppq_identity_gate.json": "101bd6ba80175492a2cde4fb14f41c633c0e154b7aa58bdeb31ab22f4d1121e5",
    "re6_r1_re6_r2_gate_equivalence.json": "799557ad677ad7e8e2fad4f0028845d128a73afaba839469777d77d76e6e2fd3",
    "repository_authority.json": "2f4a13e07ee1bbf379610a1609832b6b2ff6477e1ef1343c14888be1a6f97a99",
    "static_authority.json": "bf25e75b174bbe513419c6c6770445ba94697892c63fe161332daae065c22602",
    "success_postprocess_dependency_inventory.json": "e0c531406156d38757262a29c7299ebb09b6cce103d743ab407a5b975976f162",
    "w2e_w2i_identity_gate.json": "859513956cef110c73a7cb49009bfa7cbc35bdaddc8d91b1d33ee9baa419a047",
}


def require(value: bool, reason: str) -> None:
    if not value:
        raise AssertionError(reason)


def artifact(name: str, value: Mapping[str, Any]) -> None:
    V2.atomic_persist(OUT / name, value)


def source_identity() -> dict[str, Any]:
    paths = {**PRODUCTION, "w2e_selector": HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py",
             "w2i_manifest": W2I, "pw_helper": PW_HELPER,
             "ppq_v1_helper": V1_HELPER, "ppq_v1_schema": V1_SCHEMA,
             "re6_r1_harness": HERE / "test_assignment_phase_b2_t4_re6_r1_normal_horizon_learned_training_integration.py"}
    observed = {name: {"path": str(path.relative_to(ROOT)).replace("\\", "/"),
                       "bytes": path.stat().st_size, "sha256": V2.sha_file(path)}
                for name, path in paths.items()}
    require(all(observed[k]["sha256"] == v for k, v in REVIEWED.items()), "PROTECTED-SOURCE-DRIFT")
    return observed


def historical_identity() -> dict[str, Any]:
    manifest = json.loads(HISTORICAL_MANIFEST.read_text(encoding="utf-8"))
    expected = manifest["files"]
    paths = {p.relative_to(HISTORICAL).as_posix(): p for p in HISTORICAL.rglob("*") if p.is_file()}
    require(set(paths) == set(expected), "HISTORICAL-PATH-DRIFT")
    bad = [name for name, path in paths.items()
           if path.stat().st_size != expected[name]["bytes"] or
           V2.sha_file(path) != expected[name]["sha256"]]
    require(not bad, "HISTORICAL-BYTES-DRIFT")
    r2 = {p.name: V2.sha_file(p) for p in R2.iterdir() if p.is_file()}
    require(r2 == R2_REVIEWED, "RE6-R2-DIAGNOSTIC-DRIFT")
    v1_root = DATE / "b2_t4_ppq_artifacts"
    v1_artifacts = {p.relative_to(v1_root).as_posix(): V2.sha_file(p)
                    for p in v1_root.rglob("*") if p.is_file()}
    return {"re6_r1_files": len(paths), "re6_r1_bytes": manifest["total_bytes"],
            "re6_r1_manifest_sha256": V2.sha_file(HISTORICAL_MANIFEST),
            "re6_r1_mismatches": 0, "re6_r2_files": len(r2), "re6_r2_sha256": r2,
            "re6_r2_mismatches": 0, "ppq_v1_artifact_count": len(v1_artifacts),
            "ppq_v1_artifact_sha256": v1_artifacts}


def identity(schema_sha: str) -> dict[str, str]:
    return {"ppq_v2_helper_sha256": V2.sha_file(HELPER),
            "ppq_v2_schema_sha256": schema_sha,
            "production_identity_digest": V2.digest({k: V2.sha_file(p) for k, p in sorted(PRODUCTION.items())}),
            "config_identity_digest": V2.digest(CONFIG)}


def generic_pw(evidence: Mapping[str, Any]) -> dict[str, Any]:
    return dict(evidence["pw_result"])


def historical_fixture() -> dict[str, Any]:
    source = V1TEST.load_evidence()
    # Reverify immutable historical PW records; its RE6-R1 schema is consumed
    # only as provenance, never imposed on the new success receipt.
    checked = V1TEST.verify_pw(PW, source)
    require(checked["pass"] is True, "HISTORICAL-PW-REPLAY")
    c = source["final"]["exact_execution_counts"]
    tx = source["transactions"]
    witnesses = copy.deepcopy(source["witnesses"])
    witnesses["W7"]["qualified_count"] = witnesses["W7"]["equal"]
    selected = source["retained_selected"]
    require(selected["layers"]["C_completion_authority"], "HISTORICAL-COMPLETION")
    run_id = "ppq-v2-synthetic-historical-evidence-compatibility"
    return {
        "source_phase": "B2-T4-PPQ-V2-HISTORICAL-FIXTURE", "run_id": run_id,
        "worker_pid": os.getpid(), "transactions": tx, "bridges": source["bridges"],
        "physical_transitions": c["real_rollout_steps"], "production_s10": c["s10_pass"],
        "transaction_ledger_count": len(tx), "bridge_count": len(source["bridges"]),
        "tx161_started": bool(c["transaction_161_started"]),
        "w2e_input": source["w2e_input"],
        "retained_w2e_inventory": source["retained_w2e_inventory"],
        "witnesses": witnesses,
        "task_completed_count": source["final"]["primary_witnesses"]["task_progress_gate"]["task_completed_events"],
        "completion_delta": 1,
        "coverage_max": source["final"]["primary_witnesses"]["task_progress_gate"]["coverage_max"],
        "terminal_autoreset_count": c["terminal_autoreset_events"],
        "terminal_reason_priority_pass": witnesses["W5"]["pass"] and
                                         sum(value for key, value in witnesses["W5"]["reason_counts"].items()
                                             if key != "NONE") ==
                                         c["terminal_autoreset_events"],
        "post_autoreset_learned_transaction": witnesses["W6"]["fresh_rollout_and_update"],
        "pw_result": {"contract_version": V2.PW_VERSION, "run_id": run_id,
                      "transaction_count": checked["transactions"],
                      "critic_actual": checked["critic_records"],
                      "actor_factor_actual": checked["actor_factor_records"],
                      "missing_count": checked["missing"], "duplicate_count": checked["duplicate"],
                      "order_fault_count": checked["out_of_order"],
                      "digest_fault_count": checked["digest_mismatch"],
                      "temp_residue_count": checked["temp_residue"]},
        "learner": {
            "actor_backward_planned": sum(sum(row["actor_backward_by_actor"]) for row in tx),
            "actor_backward": c["actor_backward_total"],
            "actor_step_planned": sum(sum(row["actor_optimizer_step_by_actor"]) for row in tx),
            "actor_step": c["actor_optimizer_step_total"],
            "critic_backward_planned": sum(row["critic_backward"] for row in tx),
            "critic_backward": c["critic_backward_total"],
            "critic_step_planned": sum(row["critic_optimizer_step"] for row in tx),
            "critic_step": c["critic_optimizer_step_total"],
            "valid_nonzero_update": c["valid_nonzero_update"],
            "valid_zero_effective_update": c["valid_zero_effective_update"],
            "valuenorm_expected": sum(row["critic_optimizer_step"] for row in tx),
            "valuenorm_update": c["valuenorm_update_total"],
            "actor_adam_continuity": source["actor_adam_continuity"],
            "critic_adam_continuity": source["critic_adam_continuity"],
            "valuenorm_continuity": source["valuenorm_continuity"],
            "numerical_health": source["numerical_health"]},
        "event_returns": c["event_return_computations"],
        "stock_compute_returns": c["stock_compute_returns"],
        # These are explicitly hypothetical candidate flags, not the poisoned
        # RE6-R1 attempt receipt. Never feed that historical receipt to V2.
        "partial_update": False, "route_poisoned": False,
        "checkpoint_io_count": c["checkpoint_weight_io"],
        "public_activation_count": c["public_route_activation"],
        "evaluation_playback_count": c["evaluation_playback"],
    }


def synthetic_fixture(variant: int) -> dict[str, Any]:
    require(variant in (1, 2), "SYNTHETIC-VARIANT")
    w2_input = W2TEST.fixture(4 if variant == 1 else 6)
    tx = [{"transaction_index": i, "update_id": f"ppq-v2-synthetic-{variant}-tx{i:03d}",
           "s7_s8_s9_s10": [True] * 4, "finite": True} for i in range(1, 161)]
    bridges = [{"bridge_index": i, "from_update_id": tx[i - 1]["update_id"],
                "to_update_id": tx[i]["update_id"], "pass": True,
                "persistent_object_identity": True, "learner_post_to_pre_exact": True,
                "collection_preserved_learner": True, "next_s0_established": True}
               for i in range(1, 160)]
    w2_input["transactions"] = tx
    w2_input["bridges"] = bridges
    # Change identity without changing P2 semantics. Variant 2 also adds one
    # rejected claim edge, proving candidate_count != valid_count is accepted.
    env = variant
    for step in w2_input["steps"]:
        for state in step["state_rows"]:
            state["env_id"] = env
            if variant == 2:
                state["task_state"].reverse()
                state["ownership"].reverse()
                if state["next_owned_task"][0] == 0:
                    state["next_owned_task"][0] = 1
        if variant == 2:
            for assigned in step["effective_assignment"]:
                if assigned[0] == 0:
                    assigned[0] = 1
        step["effective_assignment"] = [[-1] for _ in range(env)] + step["effective_assignment"]
        for event in step["events"]:
            event["env_id"] = env
            if variant == 2:
                event["task_id"] = 1
    for decision in w2_input["decisions"]:
        decision["env_index"] = env
        if variant == 2:
            for field in ("ownership_before", "ownership_after"):
                if decision[field] == 0:
                    decision[field] = 1
    last = max(step["global_physical_step"] for step in w2_input["steps"])
    template = copy.deepcopy(w2_input["steps"][-1])
    for physical in range(last + 1, 321):
        step = copy.deepcopy(template)
        step["global_physical_step"] = physical
        step["transaction_index"] = (physical + 1) // 2
        step["effective_assignment"] = [[-1] for _ in range(env + 1)]
        step["events"] = []
        w2_input["steps"].append(step)
    if variant == 2:
        w2_input["decisions"].append({"global_physical_step": 100, "transaction_index": 50,
                                      "collection_index": 100, "physical_step_index": 2,
                                      "env_index": env, "robot_index": 0,
                                      "episode_generation": 0, "ownership_before": None,
                                      "ownership_after": 0, "decision_reason": "POLICY_DECISION_ROW",
                                      "decision_required": True, "actor_policy_call_count": 1,
                                      "proposal_produced": True, "continuation_used": False})
    selected = W2E.reconcile(w2_input)
    require(selected["pass"] is True, "SYNTHETIC-W2E")
    run_id = f"ppq-v2-synthetic-fresh-variant-{variant}"
    actor, critic, nonzero = ((120, 1280, 1279) if variant == 1 else (200, 1440, 1400))
    return {
        "source_phase": "B2-T4-RE6-R3-SYNTHETIC", "run_id": run_id,
        "worker_pid": os.getpid(), "transactions": tx, "bridges": bridges,
        "physical_transitions": 320, "production_s10": 160,
        "transaction_ledger_count": 160, "bridge_count": 159,
        "tx161_started": False, "w2e_input": w2_input,
        "retained_w2e_inventory": selected,
        "witnesses": {w: {"pass": True} for w in V2.WITNESSES},
        "task_completed_count": 3 if variant == 1 else 7,
        "completion_delta": 1 if variant == 1 else 2,
        "coverage_max": 2 if variant == 1 else 5,
        "terminal_autoreset_count": 1 if variant == 1 else 3,
        "terminal_reason_priority_pass": True,
        "post_autoreset_learned_transaction": True,
        "pw_result": {"contract_version": V2.PW_VERSION, "run_id": run_id,
                      "transaction_count": 160, "critic_actual": 6560,
                      "actor_factor_actual": 640, "missing_count": 0,
                      "duplicate_count": 0, "order_fault_count": 0,
                      "digest_fault_count": 0, "temp_residue_count": 0},
        "learner": {"actor_backward_planned": actor, "actor_backward": actor,
                    "actor_step_planned": actor, "actor_step": actor,
                    "critic_backward_planned": critic, "critic_backward": critic,
                    "critic_step_planned": critic, "critic_step": critic,
                    "valid_nonzero_update": nonzero,
                    "valid_zero_effective_update": critic - nonzero,
                    "valuenorm_expected": critic, "valuenorm_update": critic,
                    "actor_adam_continuity": True, "critic_adam_continuity": True,
                    "valuenorm_continuity": True, "numerical_health": True},
        "event_returns": 160, "stock_compute_returns": 0,
        "partial_update": False, "route_poisoned": False,
        "checkpoint_io_count": 0, "public_activation_count": 0,
        "evaluation_playback_count": 0,
    } | {"witnesses": {**{w: {"pass": True} for w in V2.WITNESSES},
                      "W2E": {"pass": True, "selected": selected["selected"]},
                      "W7": {"pass": True, "qualified_count": 160}}}


class MemoryStore:
    def __init__(self, mode: str = "normal") -> None:
        self.records: dict[str, tuple[dict[str, Any], str]] = {}
        self.mode = mode
        self.validated = False
        self.premature = False

    def write(self, path: Path, payload: Mapping[str, Any]) -> str:
        if path.name.endswith("_canonical_success.json") and not self.validated:
            self.premature = True
            raise V2.PPQV2Stop("PREMATURE-PUBLICATION")
        if self.mode == "write_fail" and path.name == "candidate_success_receipt_v2.json":
            raise OSError("simulated write failure")
        key = str(path)
        V2.need(key not in self.records, "MEMORY-DESTINATION-EXISTS")
        value = copy.deepcopy(dict(payload))
        sha = V2.digest(value)
        self.records[key] = value, sha
        return sha

    def read(self, path: Path) -> tuple[dict[str, Any], str]:
        if self.mode == "read_fail":
            raise OSError("simulated readback failure")
        payload, sha = self.records[str(path)]
        if self.mode == "digest_mismatch":
            sha = "0" * 64
        return copy.deepcopy(payload), sha

    def guard(self, _payload: dict[str, Any], _sha: str) -> None:
        self.validated = True


def call(evidence: dict[str, Any], identity_map: dict[str, str], *,
         store: MemoryStore | None = None, expected_phase: str | None = None,
         config: dict[str, int] | None = None, payload_mutator: Any = None) -> dict[str, Any]:
    store = store or MemoryStore()
    return V2.finalize_campaign(evidence, w2e_selector=W2E.reconcile, w2i_manifest=W2I,
                                pw_reconcile=generic_pw,
                                expected_phase=expected_phase or evidence.get("source_phase", ""),
                                config=config or CONFIG, identity=identity_map,
                                production_sources=PRODUCTION, pw_helper_path=PW_HELPER,
                                writer=store.write, reader=store.read,
                                readback_guard=store.guard, output_dir=Path("memory"),
                                payload_mutator=payload_mutator)


def positive_summary(evidence: dict[str, Any], identity_map: dict[str, str], label: str) -> dict[str, Any]:
    store = MemoryStore()
    result = call(evidence, identity_map, store=store)
    r = result["receipt"]
    require(result["trace"][-1] == "09_canonical_witness_publication" and
            not store.premature and len(result["publication"]) == 7, "POSITIVE-PUBLICATION")
    return {"fixture": label, "synthetic_offline": True,
            "historical_reclassification": False,
            "pass": result["pass"], "source_phase": r["source_phase"],
            "w2_candidate_count": r["w2e_candidate_count"],
            "w2_valid_count": r["w2e_valid_count"],
            "selected": {k: r[k] for k in ("w2_env", "w2_robot", "w2_task",
                                            "w2_claim_tx", "w2_completion_tx", "w2_reopen_tx")},
            "task_completed": r["task_completed_count"], "coverage": r["coverage_max"],
            "terminal": r["terminal_autoreset_count"], "receipt_sha256": result["receipt_sha256"],
            "trace": result["trace"]}


def negative_matrix(base: dict[str, Any], identity_map: dict[str, str]) -> dict[str, Any]:
    # Each mutation goes through the actual V2 helper, never an alternate validator.
    specs = [
        ("A", "wrong source phase", "phase", "B2-T4-RE6-R1"),
        ("B", "historical STOP status inserted", "receipt_add", ("historical_source_status", "STOP-POISONED")),
        ("C", "missing run_id", "evidence_drop", "run_id"),
        ("D", "missing worker_pid", "evidence_drop", "worker_pid"),
        ("E", "missing W2E SHA", "receipt_drop", "w2e_selector_sha256"),
        ("F", "wrong W2E SHA", "receipt", ("w2e_selector_sha256", "0" * 64)),
        ("G", "missing W2I SHA", "receipt_drop", "w2i_binding_manifest_sha256"),
        ("H", "wrong W2I SHA", "receipt", ("w2i_binding_manifest_sha256", "0" * 64)),
        ("I", "missing V2 helper SHA", "receipt_drop", "ppq_v2_helper_sha256"),
        ("J", "wrong V2 helper SHA", "receipt", ("ppq_v2_helper_sha256", "0" * 64)),
        ("K", "missing V2 schema SHA", "receipt_drop", "ppq_v2_schema_sha256"),
        ("L", "wrong V2 schema SHA", "receipt", ("ppq_v2_schema_sha256", "0" * 64)),
        ("M", "missing PW SHA", "receipt_drop", "pw_helper_sha256"),
        ("N", "wrong PW SHA", "receipt", ("pw_helper_sha256", "0" * 64)),
        ("O", "missing production identity", "identity_drop", "production_identity_digest"),
        ("P", "missing config identity", "identity_drop", "config_identity_digest"),
        ("Q", "candidate_count zero", "evidence", ("w2e_input.decisions", [])),
        ("R", "valid_count zero", "evidence", ("w2e_input.steps.4.events", [])),
        ("S", "valid exceeds candidate", "receipt", ("w2e_valid_count", 2)),
        ("T", "selected missing", "evidence", ("witnesses.W2E.selected", None)),
        ("U", "selected not selector valid", "evidence", ("witnesses.W2E.selected.env_id", 99)),
        ("V", "claim/completion order invalid", "receipt", ("w2_claim_tx", 2)),
        ("W", "generation mismatch", "evidence", ("witnesses.W2E.selected.episode_generation", 99)),
        ("X", "W2 clear false", "evidence", ("w2e_input.steps.4.state_rows.0.ownership.0", 0)),
        ("Y", "W2 reopen false", "evidence", ("w2e_input.steps.4.state_rows.0.next_decision_required.0", False)),
        ("Z", "task completed zero", "evidence", ("task_completed_count", 0)),
        ("AA", "completion delta zero", "evidence", ("completion_delta", 0)),
        ("AB", "coverage zero", "evidence", ("coverage_max", 0)),
        ("AC", "terminal count zero", "evidence", ("terminal_autoreset_count", 0)),
        ("AD", "post-autoreset false", "evidence", ("post_autoreset_learned_transaction", False)),
        ("AE", "transaction count mismatch", "evidence", ("transactions", [])),
        ("AF", "physical count mismatch", "evidence", ("physical_transitions", 319)),
        ("AG", "S10 mismatch", "evidence", ("production_s10", 159)),
        ("AH", "ledger mismatch", "evidence", ("transaction_ledger_count", 159)),
        ("AI", "bridge mismatch", "evidence", ("bridge_count", 158)),
        ("AJ", "tx161 started", "evidence", ("tx161_started", True)),
        ("AK", "PW critic mismatch", "evidence", ("pw_result.critic_actual", 6559)),
        ("AL", "PW actor/factor mismatch", "evidence", ("pw_result.actor_factor_actual", 639)),
        ("AM", "PW missing fault", "evidence", ("pw_result.missing_count", 1)),
        ("AN", "PW duplicate fault", "evidence", ("pw_result.duplicate_count", 1)),
        ("AO", "PW order fault", "evidence", ("pw_result.order_fault_count", 1)),
        ("AP", "PW digest fault", "evidence", ("pw_result.digest_fault_count", 1)),
        ("AQ", "PW temp residue", "evidence", ("pw_result.temp_residue_count", 1)),
        ("AR", "W1 fail", "evidence", ("witnesses.W1.pass", False)),
        ("AS", "W3 fail", "evidence", ("witnesses.W3.pass", False)),
        ("AT", "W4 fail", "evidence", ("witnesses.W4.pass", False)),
        ("AU", "W5 fail", "evidence", ("witnesses.W5.pass", False)),
        ("AV", "W6 fail", "evidence", ("witnesses.W6.pass", False)),
        ("AW", "W7 count mismatch", "evidence", ("witnesses.W7.qualified_count", 159)),
        ("AX", "actor plan mismatch", "evidence", ("learner.actor_step", 119)),
        ("AY", "critic plan mismatch", "evidence", ("learner.critic_step", 1279)),
        ("AZ", "Adam continuity false", "evidence", ("learner.actor_adam_continuity", False)),
        ("BA", "ValueNorm continuity false", "evidence", ("learner.valuenorm_continuity", False)),
        ("BB", "numerical health false", "evidence", ("learner.numerical_health", False)),
        ("BC", "event returns mismatch", "evidence", ("event_returns", 159)),
        ("BD", "stock returns positive", "evidence", ("stock_compute_returns", 1)),
        ("BE", "partial update true", "evidence", ("partial_update", True)),
        ("BF", "route poisoned true", "evidence", ("route_poisoned", True)),
        ("BG", "checkpoint count positive", "evidence", ("checkpoint_io_count", 1)),
        ("BH", "public count positive", "evidence", ("public_activation_count", 1)),
        ("BI", "evaluation count positive", "evidence", ("evaluation_playback_count", 1)),
        ("BJ", "receipt write failure", "store", "write_fail"),
        ("BK", "receipt readback failure", "store", "read_fail"),
        ("BL", "receipt digest mismatch", "store", "digest_mismatch"),
        ("BM", "unknown critical field", "receipt_add", ("critical_extra", True)),
        ("BN", "missing mandatory field", "receipt_drop", "source_phase"),
        ("BO", "wrong field type", "receipt", ("worker_pid", "not-an-int")),
        ("BP", "nonfinite numeric", "receipt", ("coverage_max", float("nan"))),
        ("BQ", "premature publication", "publication", "premature"),
        ("BR", "stale provisional witness", "publication", "stale"),
        ("BS", "hidden engine key", "evidence", ("engine", {"_base_atomic_json": True})),
        ("BT", "terminal reason priority false", "evidence", ("terminal_reason_priority_pass", False)),
        ("BU", "wrong production identity", "identity", ("production_identity_digest", "0" * 64)),
        ("BV", "wrong config identity", "identity", ("config_identity_digest", "0" * 64)),
    ]
    rows = []
    for code, label, kind, mutation in specs:
        e, ids = copy.deepcopy(base), dict(identity_map)
        store = MemoryStore(mutation if kind == "store" else "normal")
        mutate_receipt = None
        try:
            if kind == "phase":
                e["source_phase"] = mutation
            elif kind == "evidence_drop":
                e.pop(mutation)
            elif kind == "identity_drop":
                ids.pop(mutation)
            elif kind == "identity":
                ids[mutation[0]] = mutation[1]
            elif kind == "evidence":
                set_path(e, mutation[0], mutation[1])
            elif kind in ("receipt", "receipt_add"):
                mutate_receipt = lambda payload, m=mutation: payload.__setitem__(*m)
            elif kind == "receipt_drop":
                mutate_receipt = lambda payload, k=mutation: payload.pop(k)
            elif kind == "publication":
                witness = {w: {"pass": True} for w in V2.WITNESSES}
                provisional = {w: V2.digest(witness[w]) for w in witness}
                if mutation == "stale":
                    provisional["W1"] = "0" * 64
                V2.publish_witnesses(validated=mutation == "stale", receipt_sha256="a" * 64,
                                     witnesses=witness, provisional_digests=provisional,
                                     writer=store.write, output_dir=Path("memory"))
            if kind != "publication":
                call(e, ids, store=store, payload_mutator=mutate_receipt)
            rows.append({"case": code, "label": label, "expected": "STOP",
                         "actual": "UNEXPECTED_PASS", "reason": None})
        except (V2.PPQV2Stop, KeyError, IndexError, TypeError, ValueError, OSError) as exc:
            rows.append({"case": code, "label": label, "expected": "STOP",
                         "actual": "STOP", "reason": f"{type(exc).__name__}:{exc}"})
    require(len(rows) == 74, "NEGATIVE-CASE-COUNT")
    unexpected = [r for r in rows if r["actual"] != "STOP"]
    return {"case_count": len(rows), "expected_stop": len(rows),
            "actual_stop": len(rows) - len(unexpected), "unexpected_pass": len(unexpected),
            "pass": not unexpected, "cases": rows}


def set_path(value: dict[str, Any], path: str, replacement: Any) -> None:
    keys = path.split(".")
    node: Any = value
    for key in keys[:-1]:
        node = node[int(key)] if isinstance(node, list) else node[key]
    last = keys[-1]
    if isinstance(node, list):
        node[int(last)] = replacement
    else:
        node[last] = replacement


def repository_authority() -> dict[str, Any]:
    git = lambda *args: subprocess.check_output(["git", *args], cwd=ROOT)
    staged = git("ls-files", "--stage")
    paths = git("diff", "--cached", "--name-only").decode("utf-8").splitlines()
    porcelain = git("status", "--porcelain=v1", "-uall")
    value = {"branch": git("branch", "--show-current").decode().strip(),
             "HEAD": git("rev-parse", "HEAD").decode().strip(),
             "origin_main": git("rev-parse", "origin/main").decode().strip(),
             "merge_base": git("merge-base", "HEAD", "origin/main").decode().strip(),
             "full_porcelain_line_count": len(porcelain.splitlines()),
             "full_porcelain_sha256": hashlib.sha256(porcelain).hexdigest(),
             "staged_path_count": len(paths),
             "staged_index_sha256": hashlib.sha256(staged).hexdigest(),
             "monthly_path_set_sha256": hashlib.sha256(chr(10).join(paths).encode()).hexdigest(),
             "git_add_commit_push": [0, 0, 0]}
    require(value["staged_path_count"] == 359 and
            value["staged_index_sha256"] == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c" and
            value["monthly_path_set_sha256"] == "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab",
            "REPOSITORY-AUTHORITY-DRIFT")
    return value


def run_check() -> dict[str, Any]:
    source_before = source_identity()
    historical_before = historical_identity()
    authority = repository_authority()
    schema = V2.schema_document()
    schema_sha = hashlib.sha256(V2.canonical(schema)).hexdigest()
    ids = identity(schema_sha)
    historical = historical_fixture()
    fresh1 = synthetic_fixture(1)
    fresh2 = synthetic_fixture(2)
    positives = [positive_summary(e, ids, label) for e, label in
                 ((historical, "historical_evidence_compatibility"),
                  (fresh1, "fresh_variant_1"), (fresh2, "fresh_variant_2"))]
    require(all(p["pass"] for p in positives), "POSITIVE-MATRIX")
    negatives = negative_matrix(fresh1, ids)
    require(negatives["pass"], "NEGATIVE-MATRIX")
    # Direct phase contract and source-phase mismatch are checked via the helper.
    mismatch = copy.deepcopy(fresh1)
    mismatch["source_phase"] = "B2-T4-RE6-R3"
    require(call(mismatch, ids, expected_phase="B2-T4-RE6-R3")["pass"], "SECOND-FRESH-PHASE")
    try:
        call(mismatch, ids, expected_phase="B2-T4-RE6-R3-SYNTHETIC")
        raise AssertionError("PHASE-MISMATCH-UNEXPECTED-PASS")
    except V2.PPQV2Stop:
        pass
    # Simulated failure records are independent of any historical success alias.
    failure_store = MemoryStore()
    pre = V2.failure_record(stage="pre_mutation", exception=V2.PPQV2Stop("simulated"),
                            mutation_occurred=False, writer=failure_store.write,
                            output_dir=Path("memory/pre"))
    post = V2.failure_record(stage="post_mutation", exception=V2.PPQV2Stop("simulated"),
                             mutation_occurred=True, writer=failure_store.write,
                             output_dir=Path("memory/post"))
    require(pre["partial_update"] is False and pre["route_poisoned"] is False and
            post["partial_update"] is True and post["route_poisoned"] is True and
            pre["success_receipt"] is post["success_receipt"] is None and
            not pre["canonical_success_witnesses"] and not post["canonical_success_witnesses"],
            "FAILURE-RECORD-CONTRACT")
    source_after = source_identity()
    historical_after = historical_identity()
    require(source_before == source_after and historical_before == historical_after,
            "PROTECTED-DRIFT-AFTER-CHECK")
    return {"authority": authority, "source_before": source_before,
            "source_after": source_after, "historical_before": historical_before,
            "historical_after": historical_after, "schema": schema,
            "schema_sha256": schema_sha, "identity": ids,
            "positives": positives, "negatives": negatives,
            "failure_pre": pre, "failure_post": post,
            "fresh_phase_alternate_pass": True, "fresh_phase_mismatch_stop": True}


def write_qualification(result: dict[str, Any]) -> None:
    require(not OUT.exists(), "PPQ-V2-ARTIFACT-NAMESPACE-EXISTS")
    a = result
    artifacts: dict[str, dict[str, Any]] = {
        "repository_authority.json": a["authority"],
        "reviewed_starting_authority.json": {"ppq_v1": "GPT REVIEW PASS / CLOSED; RE6-R1 offline only",
            "re6_r1": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED",
            "re6_r2": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
            "re6_r3": "NOT AUTHORIZED"},
        "re6_r2_contract_gap_reproduction.json": {"reproduced": True,
            "gap": ["historical source/status", "closed direct identity fields",
                    "fixed historical W2/task values", "RE6-R1-specific PW schema"],
            "source": "RE6-R2 pre-runtime STOP and immutable PPQ-v1 helper"},
        "ppq_v1_preservation.json": {"pass": True, "helper_sha256": REVIEWED["ppq_v1_helper"],
            "schema_sha256": REVIEWED["ppq_v1_schema"], "historical_scope_only": True},
        "fresh_receipt_contract_v2.json": {"version": V2.VERSION,
            "fixed_reviewed": ["W2E", "W2I", "PW"],
            "candidate": ["PPQ-V2 helper", "PPQ-V2 schema"],
            "runtime_derived": ["W2", "task progress", "terminal", "learner", "witnesses"],
            "config_derived": ["160 transactions", "T=2", "PW cadence 41/4"],
            "success_order": a["positives"][1]["trace"]},
        "fresh_receipt_schema_v2.json": a["schema"],
        "fresh_dependency_contract_v2.json": {"required_explicit": ["normalized campaign evidence",
            "exact reviewed W2E selector", "W2I manifest path", "fresh PW reconciliation callable",
            "expected source phase", "formal config", "production source paths",
            "config identity", "PW helper path", "persistence writer", "receipt reader",
            "output namespace"], "hidden_engine_keys": 0},
        "fresh_source_phase_contract.json": {"allowed": list(V2.FRESH_PHASES),
            "exact_caller_expected_phase_required": True,
            "alternate_fresh_phase_pass": a["fresh_phase_alternate_pass"],
            "mismatch_stop": a["fresh_phase_mismatch_stop"]},
        "fresh_identity_contract.json": {"direct_sha_fields": [k for k in V2.FIELDS if k.endswith("sha256")],
            "production_digest": a["identity"]["production_identity_digest"],
            "config_digest": a["identity"]["config_identity_digest"],
            "schema_sha256": a["schema_sha256"]},
        "fresh_w2_contract.json": {"selector": V2.W2E_VERSION,
            "selector_sha256": V2.W2E_SHA, "selection": "exact deterministic first valid",
            "candidate_min": 1, "valid_min": 1, "historical_counts_fixed": False},
        "fresh_task_progress_contract.json": {"task_completed_min": 1,
            "completion_delta_positive": True, "coverage_positive": True},
        "fresh_terminal_contract.json": {"autoreset_min": 1,
            "post_autoreset_learned_transaction": True,
            "terminal_reason": "canonical priority; runtime-derived, not predetermined"},
        "fresh_pw_contract.json": {"version": V2.PW_VERSION, "reviewed_helper_sha256": V2.PW_SHA,
            "critic_per_tx": CONFIG["critic_records_per_tx"],
            "actor_factor_per_tx": CONFIG["actor_factor_records_per_tx"],
            "faults_required_zero": True},
        "fresh_campaign_invariants.json": {"config": CONFIG,
            "physical": 320, "s10": 160, "ledger": 160, "bridges": 159,
            "tx161_started": False},
        "fresh_witness_contract.json": {"required_pass": list(V2.WITNESSES),
            "W7_qualified_count": 160, "canonical_after_receipt_validation": True},
        "fresh_learner_contract.json": {"observed_equals_planned": True,
            "nonzero_plus_zero_effective_equals_critic_plan": True,
            "valuenorm_equals_critic_plan": True, "historical_totals_fixed": False},
        "fresh_route_health_contract.json": {"partial_update": False,
            "route_poisoned": False, "checkpoint_io_count": 0,
            "public_activation_count": 0, "evaluation_playback_count": 0},
        "positive_fixture_historical_evidence.json": a["positives"][0],
        "positive_fixture_fresh_variant_1.json": a["positives"][1],
        "positive_fixture_fresh_variant_2.json": a["positives"][2],
        "positive_matrix.json": {"case_count": 3, "pass_count": 3, "pass": True,
            "cases": a["positives"]},
        "negative_matrix.json": a["negatives"],
        "historical_value_decoupling.json": {"pass": True,
            "historical": a["positives"][0], "fresh_variants": a["positives"][1:]},
        "pw_fresh_contract_decoupling.json": {"pass": True,
            "required_schema": V2.PW_VERSION, "re6_r1_schema_required": False},
        "source_phase_decoupling.json": {"pass": True, "valid_phases": [
            "B2-T4-RE6-R3-SYNTHETIC", "B2-T4-RE6-R3"], "mismatch_stop": True},
        "direct_identity_field_validation.json": {"pass": True,
            "fields": [k for k in V2.FIELDS if k.endswith("sha256") or k.endswith("identity_digest")],
            "negative_cases": ["E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "BU", "BV"]},
        "post_mutation_failure_contract.json": {"pass": True, "record": a["failure_post"]},
        "pre_mutation_failure_contract.json": {"pass": True, "record": a["failure_pre"]},
        "protected_source_identity_before.json": {"sources": a["source_before"],
            "historical": a["historical_before"]},
        "protected_source_identity_after.json": {"sources": a["source_after"],
            "historical": a["historical_after"]},
        "future_re6_r3_integration_plan.json": {"status": "DESIGN ONLY / RE6-R3 NOT AUTHORIZED",
            "fresh_harness_import": str(HELPER.relative_to(ROOT)).replace("\\", "/"),
            "source_phase": "B2-T4-RE6-R3", "inputs": ["current runtime normalized evidence",
            "exact reviewed W2E selector", "W2I manifest", "reviewed PW verifier",
            "expected phase", "formal config", "production/config identities",
            "explicit writer/reader", "fresh output namespace"],
            "normalization": "current transaction/bridge/P2/decision/lifecycle/witness/learner/PW ledgers",
            "historical_constants": False, "ppq_v1_success_authority": False,
            "w2e_exact_reviewed_selector": True, "pw_reviewed_persistence_authority": True,
            "layer_A": "PPQ-V2 validated receipt", "layer_B": "EP-Q",
            "failure_record_before_env_app_close": True,
            "historical_artifact_modification": 0},
    }
    for name, payload in artifacts.items():
        artifact(name, payload)
    # This is a simulated post-mutation failure, not a historical formal file.
    V2.failure_record(stage="post_mutation_simulated", exception=V2.PPQV2Stop("synthetic"),
                      mutation_occurred=True, writer=V2.atomic_persist,
                      output_dir=OUT / "failure_record_simulation")


def final_once() -> dict[str, Any]:
    require(OUT.exists() and not (OUT / "final_dry_run").exists(), "FINAL-DRY-RUN-ALREADY-EXISTS")
    schema_path = OUT / "fresh_receipt_schema_v2.json"
    require(json.loads(schema_path.read_bytes()) == V2.schema_document(), "FROZEN-SCHEMA-DRIFT")
    ids = identity(V2.sha_file(schema_path))
    evidence = synthetic_fixture(2)
    output = OUT / "final_dry_run"
    result = V2.finalize_campaign(evidence, w2e_selector=W2E.reconcile, w2i_manifest=W2I,
                                  pw_reconcile=generic_pw, expected_phase=evidence["source_phase"],
                                  config=CONFIG, identity=ids, production_sources=PRODUCTION,
                                  pw_helper_path=PW_HELPER, writer=V2.atomic_persist,
                                  reader=V2.readback, output_dir=output)
    require(result["pass"] and len(result["publication"]) == 7 and
            result["trace"][-1] == "09_canonical_witness_publication", "FINAL-DRY-RUN")
    summary = {"pass": True, "fixture": "synthetic fresh variant 2",
               "receipt_sha256": result["receipt_sha256"],
               "source_phase": result["receipt"]["source_phase"],
               "w2e": result["w2e"], "trace": result["trace"],
               "publication": result["publication"],
               "hidden_engine_dependencies": 0}
    artifact("final_dry_run_result.json", summary)
    manifest = {"status": "CANDIDATE / AWAITING GPT REVIEW",
                "helper_sha256": V2.sha_file(HELPER),
                "runner_sha256": V2.sha_file(SELF),
                "schema_sha256": V2.sha_file(schema_path),
                "final_dry_run_result_sha256": V2.sha_file(OUT / "final_dry_run_result.json")}
    artifact("ppq_v2_source_identity_manifest.json", manifest)
    artifact("final_result.json", {"classification":
             "PHASE-B2-T4-PPQ-V2-FRESH-RUN-SUCCESS-RECEIPT-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW",
             "candidate_awaiting_independent_review": True,
             "positive_pass": 3, "negative_stop": 74, "unexpected_negative_pass": 0,
             "final_durable_dry_runs": 1, "re6_r3_formal_attempts": 0,
             "production_modifications": 0, "ppq_v1_modifications": 0,
             "historical_re6_r1_modifications": 0, "historical_re6_r2_modifications": 0,
             "AppLauncher": 0, "environment": 0, "learner": 0,
             "checkpoint_io": 0, "public_activation": 0, "evaluation_playback": 0,
             "git_add_commit_push": [0, 0, 0]})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("check", "qualify", "final"))
    args = parser.parse_args()
    if args.mode == "final":
        result = final_once()
        print(json.dumps({"mode": args.mode, "pass": result["pass"],
                          "receipt_sha256": result["receipt_sha256"]}))
        return
    result = run_check()
    if args.mode == "qualify":
        write_qualification(result)
    print(json.dumps({"mode": args.mode, "pass": True, "positive_pass": 3,
                      "negative_stop": result["negatives"]["actual_stop"],
                      "unexpected_pass": result["negatives"]["unexpected_pass"],
                      "schema_sha256": result["schema_sha256"]}))


if __name__ == "__main__":
    main()
