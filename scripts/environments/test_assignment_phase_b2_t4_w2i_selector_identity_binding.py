"""Read-only W2I identity replay using the unchanged W2E selector and runner.

This deliberately does not call the W2E runner's main(): that entry point
rewrites historical W2E artifacts. All results are printed to stdout only.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import test_assignment_phase_b2_t4_w2e_claim_evidence_contract as w2e
from _assignment_phase_b2_t4_w2e_multi_update_completion import CONTRACT_VERSION, reconcile


ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ROOT / "scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py"
RUNNER = ROOT / "scripts/environments/test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py"
CONTRACT = w2e.OUT / "w2e_contract_v2.json"
HISTORICAL = {
    "w2e_manifest": (w2e.OUT / "source_identity_manifest.json", "268cac782c6fe477a12450df46615797648f5a84f842723e10fc96fb2149544d"),
    "w2e_report": (w2e.AGENT / "202609/20260920/PHASE_B2_T4_W2E_CLAIM_MULTI_UPDATE_COMPLETION_EVIDENCE_CONTRACT_RECONCILIATION_REPORT.md", "513ff58c248d492aaf9c0e4efcbc81325e11ec4e83fabf08a2ef23d0134e26fe"),
    "w2e_final": (w2e.OUT / "final_result.json", "135decb5e0e02cdb9fafd4b254f84d8352b2522c1a20ffb9f3bbe094798995b0"),
    "re6_stop_report": (w2e.AGENT / "202609/20260920/PHASE_B2_T4_RE6_W2E_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md", "4a18979217fb51981ca048e3d39297ac8948f43642bc921b1b33cef02323dbee"),
    "re6_stop_result": (w2e.AGENT / "202609/20260920/b2_t4_re6_artifacts/final_result.json", "17bb6a46f821297908dd0c111139c5edf60ad6f062b262046611f05eb413b83a"),
}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise RuntimeError(f"STOP — B2-T4-W2I {reason}")


def digest(value: object) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def historical_hashes() -> dict[str, str]:
    return {name: w2e.sha(path) for name, (path, _) in HISTORICAL.items()}


def main() -> None:
    require(Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(), "INTERPRETER-IDENTITY")
    source_before = {name: w2e.sha(path) for name, path in (("selector", SELECTOR), ("offline_runner", RUNNER), ("contract_artifact", CONTRACT))}
    historical_before = historical_hashes()
    require(historical_before == {name: expected for name, (_, expected) in HISTORICAL.items()}, "HISTORICAL-W2E-OR-RE6-DRIFT-BEFORE")
    reviewed_manifest = json.loads(HISTORICAL["w2e_manifest"][0].read_text(encoding="utf-8"))
    entries = reviewed_manifest["source_sha256"]
    require(len(entries) == 15, "HISTORICAL-MANIFEST-STRUCTURE")
    require("scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py" not in entries, "HISTORICAL-BASELINE-NOT-ABSENT")
    require("scripts/environments/test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py" not in entries, "HISTORICAL-RUNNER-BASELINE-NOT-ABSENT")
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract["version"] == CONTRACT_VERSION == "b2_t4_w2e_multi_update_completion_v2", "CONTRACT-VERSION")

    re5_before = {name: w2e.sha(w2e.RE5 / name) for name in w2e.RE5_BASELINE_SHA256}
    require(re5_before == w2e.RE5_BASELINE_SHA256, "HISTORICAL-RE5-DRIFT-BEFORE")
    progress = w2e.ledger("lifecycle_task_progress")
    transactions = w2e.ledger("transaction")
    bridges = w2e.ledger("bridge")
    old = w2e.old_replay(progress)
    v2 = reconcile(w2e.normalize(progress, transactions, bridges))
    positive, negative = w2e.matrices()

    def reviewed(name: str) -> object:
        return json.loads((w2e.OUT / name).read_text(encoding="utf-8"))

    require(old == reviewed("old_w2_replay.json"), "OLD-W2-REPLAY-DRIFT")
    require(positive == reviewed("positive_matrix.json"), "POSITIVE-MATRIX-DRIFT")
    require(negative == reviewed("negative_matrix.json"), "NEGATIVE-MATRIX-DRIFT")
    inventory = {key: v2[key] for key in ("schema_version", "selection_order", "claim_edge_count", "completion_event_count", "candidate_count", "valid_count", "inventory")}
    require(inventory == reviewed("re5_w2_v2_candidate_inventory.json"), "RE5-INVENTORY-DRIFT")
    replay = reviewed("re5_w2_v2_replay.json")
    require(all(v2[key] == replay[key] for key in ("schema_version", "pass", "selected", "valid_count", "candidate_count")), "RE5-REPLAY-DRIFT")
    w1_w2 = reviewed("w1_w2_semantics_crosscheck.json")
    require(w1_w2["pass"] is True and w1_w2["ownership_definition_consistent"] is True, "W1-W2-SEMANTICS-DRIFT")
    require(positive["pass"] and len(positive["cases"]) == 3 and all(row["actual_pass"] for row in positive["cases"]), "POSITIVE-MATRIX-COUNT")
    require(negative["pass"] and len(negative["cases"]) == 18 and negative["unexpected_pass_count"] == 0, "NEGATIVE-MATRIX-COUNT")
    require(old["recorded_task_claimed"] == 0 and old["recorded_task_completed"] == 22 and old["W2_MULTI_UPDATE_COMPLETION"] is None, "OLD-W2-SEMANTICS")
    require(v2["candidate_count"] == 29 and v2["valid_count"] == 12, "RE5-REPLAY-COUNT")
    selected = v2["selected"]
    selected_keys = ("env_id", "robot_id", "task_id", "claim_tx", "claim_physical_step", "completion_tx", "completion_physical_step", "reopen_tx", "reopen_physical_step")
    require(tuple(selected[key] for key in selected_keys) == (1, 1, 10, 12, 23, 15, 30, 16, 31), "DETERMINISTIC-SELECTION-DRIFT")

    re5_after = {name: w2e.sha(w2e.RE5 / name) for name in w2e.RE5_BASELINE_SHA256}
    source_after = {name: w2e.sha(path) for name, path in (("selector", SELECTOR), ("offline_runner", RUNNER), ("contract_artifact", CONTRACT))}
    historical_after = historical_hashes()
    require(re5_after == re5_before, "HISTORICAL-RE5-DRIFT-AFTER")
    require(source_after == source_before, "SOURCE-CHANGED-DURING-QUALIFICATION")
    require(historical_after == historical_before, "HISTORICAL-W2E-OR-RE6-DRIFT-AFTER")
    print(json.dumps({
        "status": "PASS", "schema_version": "b2_t4_w2i_read_only_replay_v1",
        "qualification_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "interpreter": sys.executable, "contract_version": CONTRACT_VERSION,
        "source_before_sha256": source_before, "source_after_sha256": source_after,
        "historical_before_sha256": historical_before, "historical_after_sha256": historical_after,
        "historical_re5_unchanged": re5_after == re5_before,
        "positive_cases": len(positive["cases"]), "negative_cases": len(negative["cases"]),
        "unexpected_negative_passes": negative["unexpected_pass_count"],
        "old_task_claimed": old["recorded_task_claimed"], "old_task_completed": old["recorded_task_completed"],
        "old_w2": old["W2_MULTI_UPDATE_COMPLETION"], "candidate_count": v2["candidate_count"],
        "valid_count": v2["valid_count"], "selected": {key: selected[key] for key in selected_keys},
        "result_sha256": {"positive": digest(positive), "negative": digest(negative), "old_w2": digest(old), "re5_v2": digest(v2)},
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
