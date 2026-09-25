"""RE6-R4 pre-runtime integration gate.

This runner intentionally has no formal-worker mode.  The reviewed PPQ-V2
contract rejects the required B2-T4-RE6-R4 source phase, so the task's explicit
fail-before-AppLauncher rule terminates R4 before a runtime harness can exist.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DAY = SCAN / "AgentRead/202609/20260921"
OUT = DAY / "b2_t4_re6_r4_artifacts"
LAQ_R1_OUT = DAY / "b2_t4_laq_r1_artifacts"
R3 = SCAN / "AgentRead/202609/20260920/b2_t4_re6_r3_artifacts"
PPQ_SCHEMA = SCAN / "AgentRead/202609/20260920/b2_t4_ppq_v2_artifacts/fresh_receipt_schema_v2.json"
sys.path.insert(0, str(HERE))
import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as PPQ  # noqa: E402
import test_assignment_phase_b2_t4_laq_worker_receipt as LAQ_OLD  # noqa: E402
import test_assignment_phase_b2_t4_laq_r1_authority_binding as LAQ_R1  # noqa: E402


CLASSIFICATION = "PHASE-B2-T4-RE6-R4-STOP-PPQ-V2-SOURCE-PHASE-NOT-PERMITTED"
R3_PREFIX = "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260920/b2_t4_re6_r3_artifacts"
R4_PREFIX = "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260921/b2_t4_re6_r4_artifacts"
EXPECTED = {
    "laq_r1_helper": "22720385c3eb4c67bf2317c0a90f5ca2575b85f8e07529be3c661f71cb4082b3",
    "laq_r1_runner": "9d89b562a2564cea1e16e3fd708d8a3a583de04c25bc473135d50cdb23fea904",
    "laq_r1_contract": "677839292827599fdef36128c05deaa96f0e9cb1f76e3975f338259231f68956",
    "laq_r1_registry": "3f79dfe33e252c13b13fccb26a9f476b00aeb72bf73eae2c2fff5684a7247751",
    "ppq_v2_helper": "115d681d5e8473aa171e6232b6beca8c985139a58926d6d15850c2940785f903",
    "ppq_v2_runner": "134a8c290949385854a4bf4e0cea11748f447a94fba503b4c6f2454118ab92dc",
    "ppq_v2_schema": "0742a9a0ed44cb1f3410fae8885e348f7a40b7dbc35ac089ca6cf920d89126d5",
    "normalizer": "316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3",
    "w2e": "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0",
    "w2i": "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b",
    "pw": "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b",
    "production_full": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "production_adapter": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
    "production_env": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}
PATHS = {
    "laq_r1_helper": HERE / "_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
    "laq_r1_runner": HERE / "test_assignment_phase_b2_t4_laq_r1_authority_binding.py",
    "laq_r1_contract": LAQ_R1_OUT / "layer_a_r1_contract.json",
    "laq_r1_registry": LAQ_R1_OUT / "authority_source_registry.json",
    "ppq_v2_helper": HERE / "_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py",
    "ppq_v2_runner": HERE / "test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract.py",
    "ppq_v2_schema": PPQ_SCHEMA,
    "normalizer": HERE / "_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py",
    "w2e": HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py",
    "w2i": SCAN / "AgentRead/202609/20260920/b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json",
    "pw": HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py",
    "production_full": SCAN / "assignment_event_training_full_transaction.py",
    "production_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
    "production_env": SCAN / "scan_mobile_manipulator_env.py",
}


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def write(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True,
                                      ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def repository_authority() -> dict[str, Any]:
    porcelain = git_bytes("status", "--porcelain=v1", "-uall")
    staged = git_bytes("ls-files", "--stage")
    paths = git_bytes("diff", "--cached", "--name-only").decode().strip().splitlines()
    result = {
        "branch": git_bytes("branch", "--show-current").decode().strip(),
        "head": git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "full_porcelain": porcelain.decode(), "porcelain_rows": len(porcelain.decode().splitlines()),
        "porcelain_sha256": sha256(porcelain).hexdigest(),
        "pre_first_r4_write": {"porcelain_rows": 25299,
                               "porcelain_sha256": "2033a9750fc99628332448b206e0e3db05c257ca012bccc17dff9a43fabcc58a"},
        "staged_path_count": len(paths), "staged_index_sha256": sha256(staged).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(paths).encode()).hexdigest(),
    }
    if not (result["branch"] == "main" and
            result["head"] == result["origin_main"] == result["merge_base"] ==
            "b71d85a32f51be6ada324f870813a56bb45dd396" and
            result["staged_path_count"] == 359 and
            result["staged_index_sha256"] == "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c" and
            result["monthly_path_set_sha256"] == "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"):
        raise RuntimeError("REPOSITORY-AUTHORITY-DRIFT")
    return result


def rebind(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace(R3_PREFIX, R4_PREFIX)
    if isinstance(value, list):
        return [rebind(item) for item in value]
    if isinstance(value, dict):
        return {key: rebind(item) for key, item in value.items()}
    return value


def main() -> None:
    if Path(sys.executable).resolve() != Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve():
        raise RuntimeError("APPROVED-INTERPRETER")
    repository = repository_authority()
    identity_rows = {name: {"path": path.relative_to(ROOT).as_posix(),
                            "bytes": path.stat().st_size, "expected_sha256": EXPECTED[name],
                            "actual_sha256": sha(path), "pass": sha(path) == EXPECTED[name]}
                     for name, path in PATHS.items()}
    if not all(row["pass"] for row in identity_rows.values()):
        raise RuntimeError("REVIEWED-IDENTITY-MISMATCH")
    allowed = list(PPQ.schema_document()["source_phase"])
    if allowed != list(PPQ.FRESH_PHASES):
        raise RuntimeError("PPQ-SCHEMA-SOURCE-PHASE-DRIFT")
    candidate = json.loads((R3 / "candidate_success_receipt.json").read_text(encoding="utf-8"))
    identity = {key: candidate[key] for key in ("ppq_v2_helper_sha256", "ppq_v2_schema_sha256",
                                                "production_identity_digest", "config_identity_digest")}
    config = {"expected_transaction_count": 160, "expected_T": 2,
              "critic_records_per_tx": 41, "actor_factor_records_per_tx": 4}
    reason = None
    try:
        PPQ.validate_receipt(candidate, expected_phase="B2-T4-RE6-R4",
                             identity=identity, config=config)
    except PPQ.PPQV2Stop as exc:
        reason = str(exc)
    if reason != "SOURCE-PHASE" or "B2-T4-RE6-R4" in allowed:
        raise RuntimeError("PPQ-R4-SOURCE-PHASE-PROBE-NOT-DECISIVE")

    reviewed_registry = json.loads(PATHS["laq_r1_registry"].read_text(encoding="utf-8"))
    r4_registry = rebind(reviewed_registry)
    reversed_registry = json.loads(json.dumps(r4_registry).replace(R4_PREFIX, R3_PREFIX))
    equivalence = {
        "schema_version": "b2_t4_re6_r4_registry_equivalence_v1",
        "status": "STRUCTURAL-TEMPLATE-EQUIVALENT / NOT ACTIVATED",
        "field_count": len(r4_registry["fields"]),
        "field_set_identical": set(r4_registry["fields"]) == set(reviewed_registry["fields"]),
        "categories_identical": all(r4_registry["fields"][key]["category"] ==
                                    reviewed_registry["fields"][key]["category"]
                                    for key in reviewed_registry["fields"]),
        "computations_identical": all(r4_registry["fields"][key]["computation"] ==
                                      reviewed_registry["fields"][key]["computation"]
                                      for key in reviewed_registry["fields"]),
        "path_policy_identical": r4_registry["source_path_policy"] == reviewed_registry["source_path_policy"],
        "only_r3_to_r4_namespace_rebinding": reversed_registry == reviewed_registry,
        "runtime_sources_exist": False,
        "formal_activation_blocker": "PPQ-V2 SOURCE-PHASE",
    }
    if not all(equivalence[key] for key in ("field_set_identical", "categories_identical",
                                            "computations_identical", "path_policy_identical",
                                            "only_r3_to_r4_namespace_rebinding")):
        raise RuntimeError("R4-REGISTRY-TEMPLATE-NOT-EQUIVALENT")

    current_protected = LAQ_R1.protected_identity()
    prior_protected = json.loads((LAQ_R1_OUT / "protected_source_identity_after.json").read_text(encoding="utf-8"))
    if current_protected != prior_protected:
        raise RuntimeError("PROTECTED-SOURCE-DRIFT")
    write("repository_authority.json", repository)
    write("reviewed_starting_authority.json", {
        "LAQ_R1": "GPT REVIEW PASS / CLOSED",
        "LAQ_R1_classification": "PHASE-B2-T4-LAQ-R1-RAW-RECEIPT-AUTHORITY-BINDING-REVIEW-PASS",
        "PPQ_V2": "GPT REVIEW PASS / CLOSED",
        "RE6_R3": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED",
        "historical_LAQ": "HISTORICAL OFFLINE STOP / NOT QUALIFIED",
        "RE6_R4": "AUTHORIZED / PRE-RUNTIME STOP",
    })
    write("reviewed_identity_gate.json", {"pass": True, "identities": identity_rows})
    write("r4_authority_source_registry.json", r4_registry)
    write("r4_registry_equivalence.json", equivalence)
    write("r4_static_authority_snapshot.json", {"pass": True, "identities": identity_rows,
                                                 "runtime_authorities": "PREDETERMINED / NOT CREATED"})
    write("ppq_v2_source_phase_contract_gap.json", {
        "status": "STOP BEFORE FORMAL RUN", "classification": CLASSIFICATION,
        "required_source_phase": "B2-T4-RE6-R4", "allowed_source_phases": allowed,
        "r4_allowed": False, "exact_validator_reason": reason,
        "helper_path": PATHS["ppq_v2_helper"].relative_to(ROOT).as_posix(),
        "helper_sha256": identity_rows["ppq_v2_helper"]["actual_sha256"],
        "source_lines": {"FRESH_PHASES": 25, "validator_gate": [162, 163],
                         "build_gate": [246, 247]},
        "semantic_contract_modification_permitted": False,
        "formal_attempt_started": False,
    })
    write("protected_source_identity.json", {"matches_laq_r1_post_final": True,
                                               "identity": current_protected})
    write("pre_runtime_stop_receipt.json", {
        "status": "STOP", "classification": CLASSIFICATION,
        "failure_stage": "pre_runtime_ppq_v2_source_phase_contract",
        "reason": "Reviewed PPQ-V2 closed phase family excludes B2-T4-RE6-R4",
        "learner_mutation_occurred": False, "partial_update": False,
        "route_poisoned": False, "formal_supervisors": 0, "formal_workers": 0,
        "retries": 0, "cuda_probes": 0, "app_launcher": 0, "environment": 0,
        "reset": 0, "learner": 0, "physical": 0, "transactions": 0,
        "checkpoint_io": 0, "public_activation": 0, "evaluation_playback": 0,
    })
    write("final_result.json", {
        "status": "PRE-RUNTIME STOP / NOT POISONED",
        "classification": CLASSIFICATION,
        "decisive_gate": "PPQ-V2 SOURCE-PHASE",
        "reviewed_identity_gate": "PASS",
        "registry_template": "STRUCTURALLY EQUIVALENT / NOT ACTIVATED",
        "formal_supervisors_workers_retries": [0, 0, 0],
        "cuda_app_environment_reset_learner": [0, 0, 0, 0, 0],
        "partial_update": False, "route_poisoned": False,
        "historical_re6_r3": "STOP / POISONED / RETAINED / LEARNER NEVER REUSE",
        "checkpoint_public_evaluation": [0, 0, 0],
        "production_modifications": 0, "ppq_v2_modifications": 0,
        "laq_r1_modifications": 0, "historical_r3_modifications": 0,
        "git_add_commit_push": [0, 0, 0],
    })
    print(json.dumps({"classification": CLASSIFICATION, "formal_workers": 0,
                      "reason": reason, "allowed_source_phases": allowed}))


if __name__ == "__main__":
    main()
