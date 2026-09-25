"""Pure/offline B2-T4-PPQ qualification runner; never starts Isaac or HARL."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import _assignment_phase_b2_t4_ppq_postprocess as PPQ


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DATE = SCAN / "AgentRead/202609/20260920"
HISTORICAL = DATE / "b2_t4_re6_r1_artifacts"
OUTPUT = DATE / "b2_t4_ppq_artifacts"
PREFIX = "b2_t4_re6_r1_normal_horizon_20260920_formal01"
SELECTOR = HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py"
PW_HELPER = HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py"
W2I = DATE / "b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json"
HELPER = HERE / "_assignment_phase_b2_t4_ppq_postprocess.py"
SELF = Path(__file__).resolve()
EXPECTED_PYTHON = Path("C:/isaacenvs/isaac45_harl/python.exe")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(name: str, value: object, *, root: Path = OUTPUT) -> Path:
    target = root / name
    PPQ.atomic_persist(target, value if isinstance(value, dict) else {"value": value})
    return target


def read_json(name: str) -> dict[str, Any]:
    return json.loads((HISTORICAL / name).read_text(encoding="utf-8"))


def read_jsonl(name: str) -> list[dict[str, Any]]:
    with (HISTORICAL / name).open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def snapshot(root: Path) -> dict[str, dict[str, Any]]:
    return {path.relative_to(root).as_posix(): {"bytes": path.stat().st_size, "sha256": sha(path)}
            for path in sorted(root.rglob("*")) if path.is_file()}


def module_from_file(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    PPQ.require(spec is not None and spec.loader is not None, "PURE-MODULE-SPEC")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(progress: list[dict], transactions: list[dict], bridges: list[dict]) -> dict:
    """The reviewed W2E runner's exact pure normalization, without importing it."""
    steps = []
    decisions = []
    for update in progress:
        tx = int(update["transaction_index"])
        for step in update["steps"]:
            steps.append({**step, "transaction_index": tx})
        for row in update["lifecycle_rows"]:
            decisions.append({**row,
                              "global_physical_step": (tx - 1) * 2 + int(row["physical_step_index"])})
    return {"steps": steps, "decisions": decisions,
            "transactions": transactions, "bridges": bridges}


def load_evidence() -> dict[str, Any]:
    final = read_json(f"{PREFIX}_final_result.json")
    transactions = read_jsonl("transaction_ledger.jsonl")
    bridges = read_jsonl("bridge_ledger.jsonl")
    progress = read_jsonl("lifecycle_task_progress.jsonl")
    actor = read_jsonl("actor_evidence_reconciliation.jsonl")
    immutability = read_jsonl("runtime_p2_immutability.jsonl")
    metrics = read_jsonl("training_metrics.jsonl")
    pw_rows = read_jsonl("pw_transaction_reconciliation.jsonl")
    pw_campaign = read_json("pw_campaign_reconciliation.json")
    selected = read_json("w2e_selected_witness.json")
    inventory = read_json("w2e_candidate_inventory.json")
    witnesses = {key: read_json(filename) for key, filename in PPQ.WITNESS_FILES.items()}
    final_state = final["persistent_learner_identity"]["final"]
    actor_adam = [steps for actor_steps in final_state["actor_adam_steps"] for _, steps in actor_steps]
    critic_adam = [steps for _, steps in final_state["critic_adam_steps"]]
    evidence = {
        "final": final, "transactions": transactions, "bridges": bridges,
        "w2e_input": normalize(progress, transactions, bridges),
        "retained_w2e_inventory": inventory, "retained_selected": selected,
        "witnesses": witnesses, "immutability": immutability,
        "pw_rows": pw_rows, "pw_campaign": pw_campaign,
        "run_id": pw_campaign["run_id"],
        "actor_reconciliation_pass": len(actor) == 160 and all(
            row["exact_match"] is True and row["faults"] == 0 for row in actor),
        "actor_plan_exact": all(tx["transaction"]["real_audit"]["actor_expected_backward"] ==
                                tx["transaction"]["real_audit"]["actor_expected_step"] for tx in final["transactions"]),
        "factor_audit_pass": all(tx["transaction"]["r5_transaction"]["transaction_success"] is True and
                                 tx["factor_segment_count"] >= 0 for tx in final["transactions"]),
        "critic_plan_exact": all(tx["transaction"]["real_audit"]["critic_expected_backward"] == 10 and
                                 tx["transaction"]["real_audit"]["critic_expected_step"] == 10 for tx in final["transactions"]),
        "actor_adam_continuity": final["persistent_learner_identity"]["object_ids_stable"] is True and
                                 sorted(set(actor_adam)) == [25, 45, 95] and sum(set(actor_adam)) == 165,
        "critic_adam_continuity": final["persistent_learner_identity"]["object_ids_stable"] is True and
                                  all(step == 1600 for step in critic_adam),
        "valuenorm_continuity": final_state["valuenorm_state_finite"] is True and
                                final_state["valuenorm_object_id"] ==
                                final["persistent_learner_identity"]["initial"]["valuenorm_object_id"],
        "numerical_health": len(metrics) == 160 and all(row["finite"] is True for row in transactions) and
                            all(final_state[key] is True for key in
                                ("actor_parameters_finite", "actor_optimizer_states_finite",
                                 "critic_parameters_finite", "critic_optimizer_state_finite",
                                 "valuenorm_state_finite", "gradients_clean")),
    }
    return evidence


def verify_pw(PW: Any, evidence: Mapping[str, Any]) -> dict[str, Any]:
    run_id = evidence["run_id"]
    rows = evidence["pw_rows"]
    PPQ.require(len(rows) == 160 and evidence["pw_campaign"]["run_id"] == run_id,
                "PW-LEDGER-IDENTITY")
    critic = actor = 0
    for tx in range(1, 161):
        row = rows[tx - 1]
        PPQ.require(row["tx_id"] == tx and row["pass"] is True and
                    row["critic_records"] == 41 and row["actor_factor_records"] == 4,
                    "PW-TRANSACTION-LEDGER")
        critic_records = PW.verify_transaction(HISTORICAL / "pw_records", run_id=run_id,
                                               tx_id=tx, side="critic", planned_count=41)
        actor_records = PW.verify_transaction(HISTORICAL / "pw_records", run_id=run_id,
                                              tx_id=tx, side="actor", planned_count=4)
        PPQ.require(len(critic_records) == 41 and len(actor_records) == 4,
                    "PW-RECORD-COUNT")
        critic += len(critic_records)
        actor += len(actor_records)
    result = dict(evidence["pw_campaign"])
    PPQ.require(critic == result["critic_records"] and actor == result["actor_factor_records"],
                "PW-CAMPAIGN-RECORD-MISMATCH")
    return result


class MemoryReceiptStore:
    def __init__(self) -> None:
        self.records: dict[str, tuple[dict[str, Any], str]] = {}
        self.receipt_validated = False
        self.early_publication = False

    def persist(self, path: Path, payload: Mapping[str, Any]) -> str:
        if path.name in PPQ.WITNESS_FILES.values() and not self.receipt_validated:
            self.early_publication = True
            raise PPQ.PPQStop("PREMATURE-SUCCESS-PUBLICATION")
        PPQ.require(str(path) not in self.records, "MEMORY-DESTINATION-EXISTS")
        digest = PPQ.digest(payload)
        self.records[str(path)] = (copy.deepcopy(dict(payload)), digest)
        return digest

    def read(self, path: Path) -> tuple[dict[str, Any], str]:
        return copy.deepcopy(self.records[str(path)][0]), self.records[str(path)][1]

    def validated(self, _payload: dict[str, Any], _digest: str) -> None:
        self.receipt_validated = True


def negative_matrix(evidence: dict[str, Any], selector: Any, pw: Mapping[str, Any],
                    identity: dict[str, str], positive: dict[str, Any]) -> dict[str, Any]:
    base = positive["receipt"]
    cases: list[dict[str, Any]] = []

    def record(case: str, operation: Any) -> None:
        try:
            operation()
            actual, reason = "UNEXPECTED PASS", "none"
        except (PPQ.PPQStop, OSError, ValueError, TypeError) as exc:
            actual, reason = "STOP", f"{type(exc).__name__}: {exc}"
        cases.append({"case": case, "expected": "STOP", "actual": actual,
                      "reason": reason, "pass": actual == "STOP"})

    def build(*, evidence_change: Any = None, selector_change: Any = None,
              pw_change: Any = None, identity_change: Any = None) -> None:
        ev = dict(evidence)
        if evidence_change:
            evidence_change(ev)
        ids = dict(identity)
        if identity_change:
            identity_change(ids)
        sel = selector_change if selector_change else selector.reconcile
        p = pw_change if pw_change else (lambda: pw)
        payload, _, _ = PPQ.build_success_payload(ev, w2e_selector=sel,
                                                   pw_reconcile=p, identity=ids)
        PPQ.validate_success(payload)

    def mutate(case: str, change: Any) -> None:
        def operation() -> None:
            payload = dict(base)
            change(payload)
            PPQ.validate_success(payload)
        record(case, operation)

    def changed_witness(key: str, change: Any) -> Any:
        def apply(ev: dict[str, Any]) -> None:
            ev["witnesses"] = dict(ev["witnesses"])
            ev["witnesses"][key] = dict(ev["witnesses"][key])
            change(ev["witnesses"][key])
        return apply

    record("A_missing_persistence_dependency", lambda: PPQ.finalize_campaign(
        evidence, w2e_selector=selector.reconcile, pw_reconcile=lambda: pw,
        identity=identity, persistence_writer=None, receipt_reader=lambda _: ({}, ""),
        output_dir=OUTPUT / "negative"))
    record("B_hidden_engine_key", lambda: build(evidence_change=lambda ev: ev.update(
        {"hidden_engine_dependency": True})))
    record("C_missing_W2E_SHA", lambda: build(identity_change=lambda ids: ids.pop("w2e_selector_sha256")))
    record("D_wrong_W2E_SHA", lambda: build(identity_change=lambda ids: ids.update(
        {"w2e_selector_sha256": "0" * 64})))
    record("E_missing_W2I_SHA", lambda: build(identity_change=lambda ids: ids.pop("w2i_binding_manifest_sha256")))
    record("F_wrong_W2I_SHA", lambda: build(identity_change=lambda ids: ids.update(
        {"w2i_binding_manifest_sha256": "0" * 64})))
    def altered_selector(change: Any) -> Any:
        def invoke(value: Any) -> dict[str, Any]:
            result = copy.deepcopy(selector.reconcile(value))
            change(result)
            return result
        return invoke
    record("G_missing_W2_selected", lambda: build(selector_change=altered_selector(
        lambda result: result.update({"selected": None}))))
    record("H_W2_valid_zero", lambda: build(selector_change=altered_selector(
        lambda result: result.update({"valid_count": 0}))))
    record("I_W2_selected_inconsistent", lambda: build(evidence_change=lambda ev: ev.update(
        {"retained_selected": {**ev["retained_selected"], "task_id": 99}})))
    def bad_pw(key: str, value: Any) -> Any:
        return lambda: {**pw, key: value}
    record("J_PW_critic_count", lambda: build(pw_change=bad_pw("critic_records", 6559)))
    record("K_PW_actor_factor_count", lambda: build(pw_change=bad_pw("actor_factor_records", 639)))
    record("L_PW_digest_fault", lambda: build(pw_change=bad_pw("digest_mismatch", 1)))
    record("M_transaction_count", lambda: build(evidence_change=lambda ev: ev.update(
        {"transactions": ev["transactions"][:-1]})))
    record("N_bridge_count", lambda: build(evidence_change=lambda ev: ev.update(
        {"bridges": ev["bridges"][:-1]})))
    record("O_W7_count", lambda: build(evidence_change=changed_witness("W7", lambda w: w.update(
        {"equal": 159}))))
    record("P_W5_terminal", lambda: build(evidence_change=changed_witness("W5", lambda w: w.update(
        {"reason_counts": {**w["reason_counts"], "TIME_LIMIT": 0}}))))
    record("Q_W6_post_autoreset", lambda: build(evidence_change=changed_witness("W6", lambda w: w.update(
        {"fresh_rollout_and_update": False}))))
    record("R_actor_plan", lambda: build(evidence_change=lambda ev: ev.update(
        {"actor_plan_exact": False})))
    record("S_critic_plan", lambda: build(evidence_change=lambda ev: ev.update(
        {"critic_plan_exact": False})))
    record("T_Adam_continuity", lambda: build(evidence_change=lambda ev: ev.update(
        {"actor_adam_continuity": False})))
    record("U_ValueNorm_continuity", lambda: build(evidence_change=lambda ev: ev.update(
        {"valuenorm_continuity": False})))
    record("V_numerical_health", lambda: build(evidence_change=lambda ev: ev.update(
        {"numerical_health": False})))
    mutate("W_partial_update_true", lambda p: p.update({"partial_update": True}))
    mutate("X_route_poisoned_true", lambda p: p.update({"route_poisoned": True}))
    record("Y_receipt_write_failure", lambda: PPQ.finalize_campaign(
        evidence, w2e_selector=selector.reconcile, pw_reconcile=lambda: pw, identity=identity,
        persistence_writer=lambda _p, _v: (_ for _ in ()).throw(OSError("synthetic write failure")),
        receipt_reader=lambda _p: ({}, ""), output_dir=OUTPUT / "negative"))
    def readback_case(digest_fault: bool) -> None:
        store = MemoryReceiptStore()
        def wrong_read(path: Path) -> tuple[dict[str, Any], str]:
            value, sha256 = store.read(path)
            if digest_fault:
                return value, "0" * 64
            value["W1_status"] = "FAIL"
            return value, sha256
        PPQ.finalize_campaign(evidence, w2e_selector=selector.reconcile,
                              pw_reconcile=lambda: pw, identity=identity,
                              persistence_writer=store.persist, receipt_reader=wrong_read,
                              output_dir=OUTPUT / "negative", readback_validator=store.validated)
    record("Z_receipt_readback_mismatch", lambda: readback_case(False))
    record("AA_receipt_digest_mismatch", lambda: readback_case(True))
    record("AB_premature_canonical_publication", lambda: PPQ.publish_witnesses(
        validated=False, receipt_digest="0" * 64, witnesses={key: {} for key in PPQ.WITNESS_FILES},
        output_dir=OUTPUT / "negative", persist=MemoryReceiptStore().persist,
        provisional_digests={key: PPQ.digest({}) for key in PPQ.WITNESS_FILES}))
    record("AC_stale_provisional_promotion", lambda: PPQ.publish_witnesses(
        validated=True, receipt_digest="0" * 64, witnesses={key: {} for key in PPQ.WITNESS_FILES},
        output_dir=OUTPUT / "negative", persist=MemoryReceiptStore().persist,
        provisional_digests={key: "1" * 64 for key in PPQ.WITNESS_FILES}))
    mutate("AD_malformed_schema", lambda p: p.update({"unexpected_critical": "x"}))
    mutate("AE_missing_required_field", lambda p: p.pop("pw_schema_version"))
    mutate("AF_wrong_type", lambda p: p.update({"physical_transitions": "320"}))
    mutate("AG_unknown_version", lambda p: p.update({"schema_version": "future_unknown"}))
    mutate("AH_nonfinite", lambda p: p.update({"physical_transitions": float("nan")}))
    mutate("AI_critic_classification_inconsistent", lambda p: p.update({"valid_nonzero_update": 1575}))
    mutate("AJ_W2_candidate_contradiction", lambda p: p.update({"w2e_candidate_count": 0}))
    result = {"schema_version": "b2_t4_ppq_negative_matrix_v1", "cases": cases,
              "expected": len(cases), "passed": sum(case["pass"] for case in cases),
              "unexpected_passes": sum(not case["pass"] for case in cases)}
    PPQ.require(len(cases) >= 30 and result["unexpected_passes"] == 0,
                "NEGATIVE-MATRIX-FAILURE")
    return result


def repo_authority() -> dict[str, Any]:
    def command(*args: str) -> str:
        return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8").strip()
    index = command("ls-files", "--stage") + "\n"
    staged = command("diff", "--cached", "--name-only").splitlines()
    porcelain = subprocess.check_output(["git", "status", "--porcelain=v1", "-uall"],
                                        cwd=ROOT).decode("utf-8")
    return {"branch": command("branch", "--show-current"), "HEAD": command("rev-parse", "HEAD"),
            "origin_main": command("rev-parse", "origin/main"),
            "merge_base": command("merge-base", "HEAD", "origin/main"),
            "porcelain": porcelain, "porcelain_sha256": hashlib.sha256(porcelain.encode()).hexdigest(),
            "staged_path_count": len(staged),
            "staged_index_sha256": hashlib.sha256(index.encode()).hexdigest(),
            "monthly_path_set_sha256": hashlib.sha256("\n".join(staged).encode()).hexdigest()}


def main() -> None:
    PPQ.require(Path(sys.executable).resolve() == EXPECTED_PYTHON.resolve(), "APPROVED-INTERPRETER")
    PPQ.require(not OUTPUT.exists(), "PPQ-OUTPUT-ALREADY-EXISTS")
    authority = repo_authority()
    PPQ.require(authority["staged_path_count"] == 359 and
                authority["staged_index_sha256"] == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c" and
                authority["monthly_path_set_sha256"] == "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab",
                "REPOSITORY-AUTHORITY-DRIFT")
    protected_paths = {
        "production_full_transaction": SCAN / "assignment_event_training_full_transaction.py",
        "real_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
        "environment": SCAN / "scan_mobile_manipulator_env.py",
        "w2e_selector": SELECTOR, "w2i_binding": W2I, "pw_helper": PW_HELPER,
        "historical_re6_r1_harness": HERE / "test_assignment_phase_b2_t4_re6_r1_normal_horizon_learned_training_integration.py",
    }
    protected_before = {name: sha(path) for name, path in protected_paths.items()}
    identity = {"w2e_selector_sha256": protected_before["w2e_selector"],
                "w2i_binding_manifest_sha256": protected_before["w2i_binding"],
                "pw_helper_sha256": protected_before["pw_helper"]}
    for key, expected in (("w2e_selector_sha256", PPQ.W2E_SHA),
                          ("w2i_binding_manifest_sha256", PPQ.W2I_SHA),
                          ("pw_helper_sha256", PPQ.PW_SHA)):
        PPQ.require(identity[key] == expected, f"{key}-DRIFT")
    historical_before = snapshot(HISTORICAL)
    PPQ.require(len(historical_before) == 7331, "HISTORICAL-FILE-SET-DRIFT")
    OUTPUT.mkdir(parents=True, exist_ok=False)
    write_json("repository_authority.json", authority)
    write_json("re6_r1_artifact_identity.json", {
        "schema_version": "b2_t4_ppq_historical_identity_v1", "files": historical_before,
        "count": len(historical_before), "total_bytes": sum(x["bytes"] for x in historical_before.values())})
    write_json("protected_source_identity.json", {"before": protected_before, "after": None})
    write_json("inherited_postprocess_keyerror_trace.json", {
        "exact_expression": "engine['_base_atomic_json']", "file": "scripts/environments/test_assignment_phase_b2_t4_re5_normal_horizon_learned_training_integration.py",
        "function": "run_formal_worker", "line": 1144,
        "caller": "RE6-R1 main -> _ENGINE['run_formal_worker'] (RE6-R1 line 312)",
        "call_stack": ["RE6-R1 main", "RE5 run_formal_worker", "RE3._postprocess_success", "RE5 final classification rewrite", "engine['_base_atomic_json']"],
        "after": "160 mutation-bearing transactions, RE3 witness publication, before RE5 PW reconciliation and success receipt",
        "historical_origin": "RE1 outer _base_atomic_json = _INNER['_atomic_json'] at RE1 line 678; RE3 outer _RE3['_base_atomic_json'] exists, but RE5 engine is _RE3['_INNER'] and has only _atomic_json",
        "preflight_gap": "synthetic Layer-A validation exercised payload validation, not full inherited postprocess line 1144"})
    write_json("base_atomic_json_authority_classification.json", {
        "classification": "B-historical-test-harness-helper-accidentally-addressed-through-engine",
        "production_dependency": False, "redundant_alias_role": True,
        "source_chain": ["RE1:678 outer alias of inner _atomic_json", "RE1:1022-1030 inner _atomic_json wrapper delegates alias", "RE3:311,320 accesses outer _RE3 alias", "RE5:1079 selects inner engine", "RE5:1144 incorrectly accesses inner engine alias"],
        "resolution": "new PPQ helper accepts explicit persistence_writer and receipt_reader; no engine dictionary"})
    write_json("postprocess_dependency_contract.json", {
        "schema_version": "b2_t4_ppq_dependency_contract_v1",
        "required": ["transaction_evidence", "bridge_evidence", "lifecycle_evidence", "actor_evidence",
                     "PW evidence and reviewed verifier", "reviewed W2E selector", "reviewed W2I binding SHA",
                     "explicit persistence_writer", "explicit receipt_reader", "versioned receipt schema"],
        "hidden_engine_keys": "FORBIDDEN", "historical_writes": "FORBIDDEN",
        "production_modifications": 0})
    write_json("success_receipt_schema.json", PPQ.schema_document())
    write_json("success_publication_order_contract.json", {
        "schema_version": "b2_t4_ppq_success_publication_order_v1",
        "order": ["reconcile", "adjudicate", "construct", "schema_validate", "durably_write_candidate_receipt",
                  "readback", "digest_validate", "revalidate", "publish_canonical_W1_W7"],
        "pre_receipt_witnesses": "in-memory-provisional-only", "historical_RE6_R1_W1_W7": "provisional-only"})
    selector = module_from_file("b2_t4_ppq_reviewed_w2e", SELECTOR)
    PW = module_from_file("b2_t4_ppq_reviewed_pw", PW_HELPER)
    evidence = load_evidence()
    pw_positive = verify_pw(PW, evidence)
    positive_store = MemoryReceiptStore()
    positive = PPQ.finalize_campaign(
        evidence, w2e_selector=selector.reconcile, pw_reconcile=lambda: pw_positive,
        identity=identity, persistence_writer=positive_store.persist,
        receipt_reader=positive_store.read, readback_validator=positive_store.validated,
        output_dir=OUTPUT / "positive_replay")
    PPQ.require(len(positive_store.records) == 8 and positive_store.early_publication is False,
                "POSITIVE-PUBLICATION-ORDER")
    write_json("re6_r1_positive_offline_replay.json", {
        **positive, "historical_RE6_R1_reclassified": False,
        "persistence": "in-memory candidate receipt and readback; final dry run uses durable filesystem",
        "canonical_witness_count": 7})
    negatives = negative_matrix(evidence, selector, pw_positive, identity, positive)
    write_json("postprocess_negative_matrix.json", negatives)
    write_json("success_receipt_schema_tests.json", {
        "schema_version": "b2_t4_ppq_schema_tests_v1", "positive": True,
        "negative_cases": [case for case in negatives["cases"] if case["case"].startswith(("W_", "X_", "AD_", "AE_", "AF_", "AG_", "AH_", "AI_", "AJ_"))]})
    failure = PPQ.failure_receipt(
        failure_stage="postprocess_and_witness_gates", exception=PPQ.PPQStop("synthetic postprocess fault"),
        completed_transactions=160, ledger_count=160, bridge_count=159,
        witness_status={key: "PROVISIONAL" for key in PPQ.WITNESS_FILES},
        w2e_counts={"candidate_count": 29, "valid_count": 12}, pw_state=pw_positive,
        mutation_occurred=True)
    PPQ.require(failure["partial_update"] and failure["route_poisoned"] and
                failure["canonical_success_witnesses"] == [], "POST-MUTATION-FAILURE-RECEIPT")
    write_json("failure_receipt_matrix.json", {"cases": [{"name": "postmutation", "pass": True,
                                                       "receipt": failure}], "pass": True})
    premature = PPQ.failure_receipt(
        failure_stage="preflight_dependency_validation", exception=PPQ.PPQStop("missing dependency"),
        completed_transactions=0, ledger_count=0, bridge_count=0,
        witness_status={key: "NOT-STARTED" for key in PPQ.WITNESS_FILES},
        w2e_counts=None, pw_state=None, mutation_occurred=False)
    PPQ.require(premature["partial_update"] is False and premature["route_poisoned"] is False and
                premature["canonical_success_witnesses"] == [], "PRE-MUTATION-FAILURE-RECEIPT")
    write_json("pre_mutation_failure_matrix.json", {"cases": [{"name": "premutation", "pass": True,
                                                           "receipt": premature}], "pass": True})
    write_json("future_re6_r2_integration_plan.json", {
        "schema_version": "b2_t4_ppq_future_integration_plan_v1", "status": "DESIGN-ONLY-RE6-R2-NOT-AUTHORIZED",
        "import": "_assignment_phase_b2_t4_ppq_postprocess.finalize_campaign",
        "explicit_dependencies": ["normalized transaction/bridge/lifecycle/actor evidence", "reviewed W2E reconcile",
                                  "reviewed PW verify_transaction", "W2I manifest SHA", "PPQ-qualified writer",
                                  "receipt reader", "output namespace"],
        "retire": "RE3._postprocess_success followed by RE5 engine['_base_atomic_json'] success rewrite",
        "layer_a": "construct and schema-validate complete payload before persistence",
        "publication": "canonical W1-W7 only after durable candidate receipt readback and digest validation",
        "failure_receipt": "fresh RE6-R2 namespace before env close; poison on observed mutation",
        "preflight_sha_checks": ["PPQ helper SHA from candidate manifest", "runner SHA", "schema artifact SHA",
                                 "W2E selector SHA", "W2I binding SHA", "PW helper SHA"],
        "historical_RE6_R1": "immutable STOP / poisoned; never reuse learner"})
    # The one and only final frozen full-postprocess dry run starts here.
    dry = OUTPUT / "final_dry_run"
    PPQ.require(not dry.exists(), "FINAL-DRY-RUN-ALREADY-EXISTS")
    pw_final = verify_pw(PW, evidence)
    final = PPQ.finalize_campaign(
        evidence, w2e_selector=selector.reconcile, pw_reconcile=lambda: pw_final,
        identity=identity, persistence_writer=PPQ.atomic_persist,
        receipt_reader=PPQ.readback, output_dir=dry)
    PPQ.require(len(list(dry.iterdir())) == 8 and final["pass"] is True,
                "FINAL-DRY-RUN-INCOMPLETE")
    write_json("final_dry_run_result.json", {
        **final, "final_dry_run_count": 1,
        "candidate_files": {path.name: sha(path) for path in sorted(dry.iterdir())},
        "historical_RE6_R1_reclassified": False})
    historical_after = snapshot(HISTORICAL)
    protected_after = {name: sha(path) for name, path in protected_paths.items()}
    PPQ.require(historical_after == historical_before, "RE6-R1-EVIDENCE-DRIFT")
    PPQ.require(protected_after == protected_before, "PROTECTED-SOURCE-DRIFT")
    write_json("protected_source_identity_after.json", {
        "before": protected_before, "after": protected_after, "equal": True})
    final_digest = sha(OUTPUT / "final_dry_run_result.json")
    identity_manifest = {"schema_version": "b2_t4_ppq_candidate_source_identity_v1",
                         "status": "CANDIDATE / AWAITING GPT REVIEW",
                         "helper_sha256": sha(HELPER), "runner_sha256": sha(SELF),
                         "success_receipt_schema_artifact_sha256": sha(OUTPUT / "success_receipt_schema.json"),
                         "final_dry_run_result_sha256": final_digest,
                         "reviewed_dependencies": identity,
                         "historical_artifact_count": len(historical_before),
                         "historical_artifacts_unchanged": True,
                         "protected_sources_unchanged": True}
    write_json("ppq_source_identity_manifest.json", identity_manifest)
    result = {"classification": PPQ.SUCCESS_CLASSIFICATION, "status": "COMPLETE / AWAITING GPT REVIEW",
              "historical_RE6_R1": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED",
              "positive_replay": True, "negative_cases": negatives["expected"],
              "negative_passed": negatives["passed"], "unexpected_negative_passes": 0,
              "failure_receipt": True, "premutation_receipt": True,
              "final_frozen_dry_runs": 1, "final_dry_run_pass": True,
              "historical_artifacts_unchanged": True, "production_modifications": 0,
              "historical_RE6_R1_modifications": 0,
              "AppLauncher": 0, "environment": 0, "learner": 0, "CUDA": 0,
              "formal_supervisor": 0, "formal_worker": 0, "physical_steps": 0,
              "learner_mutations": 0, "checkpoint_IO": 0, "RE6_R2_attempts": 0,
              "public_activation": 0, "evaluation_playback": 0,
              "git_add_commit_push": [0, 0, 0], "candidate_helper_sha256": identity_manifest["helper_sha256"]}
    write_json("final_result.json", result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
