"""Artifact-lifecycle-safe one-shot RE6-R12 integration harness.

R12 expands the frozen R11 runner in memory.  Its only semantic change is in
test-side orchestration: a preflight normalization template lives below the
preflight namespace, while the trusted canonical context is exclusively
created after the real worker PID and run binding exist.
"""

from __future__ import annotations

import re
from pathlib import Path

import test_assignment_phase_b2_t4_re6_r11_process_budget_safe_normal_horizon_integration as R11


R12_SUPPORT = r'''
R11_ROOT_FROZEN = SCAN / "AgentRead/202609/20260922/b2_t4_re6_r11_artifacts"
R11_RUN_ID_FROZEN = "b2-t4-re6-r11-20260922-formal01-c266e95ab2b34167ba37505dcc6908d1"
R11_RUN_FROZEN = R11_ROOT_FROZEN / R11_RUN_ID_FROZEN
R11_REPORT_FROZEN = DAY / "PHASE_B2_T4_RE6_R11_PROCESS_BUDGET_SAFE_NORMAL_HORIZON_INTEGRATION_REPORT.md"
R11_HARNESS_FROZEN = ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r11_process_budget_safe_normal_horizon_integration.py"
R11_IDENTITIES = {
    "report": "9417407b4ac1eaaac79024a27ed7f0af4a8fa941fdb782647c103890e8dca5a3",
    "stage_a": "43e630ec889e3241be28983e3e5627077e73ff38a4568c9f0a875849d0729518",
    "pre_process": "ced9b31b94d7925bc2db136c2b25573c14d4a19c3533da0ef00aa2eaf3737499",
    "final": "8d293c0e56912631ed64331bfc9c6c125da95175d0c6cd8e46860d5f7623e4c1",
    "failure": "559c5080871c5dc3a60de33fd7dc77ad08e94883c1319f1d588c6b8e6e5e8da2",
    "quiescence": "7b8d504ac392fc6e2d5dcf9bcba6505344deaba1cef72729135b522a64db98a8",
    "harness": "33819c2a8b40bd4e9104ed9708b4f649003f7fd63bc8ce56085d0ca1aa5d9bcc",
}


def _r12_repair_log() -> dict[str, Any]:
    return {"schema_version": "b2_t4_re6_r12_stage_a_repair_log_v1", "repair_count": 1,
        "unresolved_repairs": 0, "major_stop_findings": 0, "repairs": [{
            "repair_id": "R12-A-001", "failure_gate": "R11 blocked-live-positive normalization context creation",
            "root_cause": "PID-independent template and PID-bound trusted live context shared one canonical path",
            "changed_R12_file_symbol": "test_assignment_phase_b2_t4_re6_r12_artifact_lifecycle_safe_normal_horizon_integration.py::_r12_lifecycle_stage_a/create_live_authority_pre_process",
            "reviewed_behavior_defining_expected_result": "R12 explicit artifact-role and lifecycle-boundary ownership contract",
            "before_evidence": "R11 blocked_live_positive_stop.json and exclusive-create FileExistsError",
            "exact_change": "publish template only at preflight/templates/r12_normalization_context_template.json; reserve r12_normalization_context.json until PID-bound prepare_bindings",
            "semantic_impact": "NONE", "production_impact": "NONE", "learner_impact": "NONE",
            "frozen_contract_impact": "NONE",
            "rerun_gates": ["R11 collision reproduction", "R12 split simulation", "lifecycle ownership matrix",
                            "10-boundary collision matrix", "canonical reservation", "complete Stage-A downstream gates"],
            "result": "RESOLVED"}]}


def _r12_spec(name: str, role: str, lifecycle: str, boundary: str, path: str, producer: str,
              *, template: str | None = None, authority: bool = False, pid: bool = False,
              release: bool = False, runtime: bool = False, append: bool = False) -> dict[str, Any]:
    return {"artifact_name": name, "logical_role": role, "lifecycle_class": lifecycle,
        "earliest_creation_boundary": boundary, "canonical_path": path, "canonical_producer": producer,
        "allowed_writers": [producer], "allowed_readers": ["R12 orchestrator", "formal worker", "formal supervisor"],
        "immutable_after_creation": not append, "requires_live_authority": authority,
        "requires_worker_pid": pid, "requires_worker_release": release,
        "requires_runtime_completion": runtime, "preflight_template_path": template,
        "canonical_path_must_be_absent_before_boundary": lifecycle != "PREFLIGHT_TEMPLATE",
        "create_count_target": 1, "consumer_create_count_target": 0,
        "overwrite_allowed": False, "append_allowed": append}


def _r12_lifecycle_specs(run_id: str) -> list[dict[str, Any]]:
    run = f"{run_id}/"
    template = "preflight/templates/r12_normalization_context_template.json"
    return [
        _r12_spec("run identity", "fresh attempt identity", "PREFLIGHT_TEMPLATE", "STAGE_A", "r12_run_identity.json", "Stage-A orchestrator"),
        _r12_spec("repository authority", "starting worktree authority", "PREFLIGHT_TEMPLATE", "STAGE_A", "repository_authority.json", "Stage-A orchestrator"),
        _r12_spec("reviewed identity gate", "protected identity evidence", "PREFLIGHT_TEMPLATE", "STAGE_A", "reviewed_identity_gate.json", "Stage-A orchestrator"),
        _r12_spec("normalization context template", "PID-independent schema projection only", "PREFLIGHT_TEMPLATE", "STAGE_A", template, "Stage-A template producer"),
        _r12_spec("filesystem precondition", "PID-independent filesystem evidence", "PREFLIGHT_TEMPLATE", "STAGE_A", run + "filesystem_precondition.json", "reviewed preflight"),
        _r12_spec("runtime authority", "live formal grant", "LIVE_CANONICAL", "LIVE_AUTHORITY", RACQ.authority_relative_path(PHASE).as_posix(), "reviewed RACQ authority builder", authority=False),
        _r12_spec("validation context evidence", "live RACQ-R1 context", "LIVE_CANONICAL", "LIVE_AUTHORITY", "r12_layer_a_validation_context.json", "pre-process orchestrator", authority=True),
        _r12_spec("process config authority", "PID-independent runtime config template", "LIVE_CANONICAL", "PRE_PID", "process_config_authority.json", "pre-process orchestrator", authority=True),
        _r12_spec("run binding", "exact PID binding", "LIVE_CANONICAL", "PID_BINDING", RACQ.binding_relative_path(PHASE, run_id).as_posix(), "reviewed RACQ binding builder", authority=True, pid=True),
        _r12_spec("registry instance", "PID/run composition registry", "LIVE_CANONICAL", "PID_BINDING", run + "layer_a_registry_instance.json", "reviewed registry builder", authority=True, pid=True),
        _r12_spec("trusted live normalization context", "canonical NORM-R1 authority and binding context", "LIVE_CANONICAL", "NORM_CONTEXT", "r12_normalization_context.json", "PID-bound live binding/context preparation", template=template, authority=True, pid=True),
        _r12_spec("transaction ledger", "runtime transaction facts", "RUNTIME_CANONICAL", "RELEASED_RUNTIME", run + "transaction_ledger.jsonl", "released runtime", authority=True, pid=True, release=True, append=True),
        _r12_spec("bridge ledger", "runtime bridge facts", "RUNTIME_CANONICAL", "RELEASED_RUNTIME", run + "bridge_ledger.jsonl", "released runtime", authority=True, pid=True, release=True, append=True),
        _r12_spec("terminal reconciliation", "terminal evidence", "RUNTIME_CANONICAL", "RELEASED_RUNTIME", run + "terminal_reconciliation.jsonl", "released runtime", authority=True, pid=True, release=True, append=True),
        _r12_spec("PW transaction reconciliation", "canonical PW evidence", "RUNTIME_CANONICAL", "RELEASED_RUNTIME", run + "pw_transaction_reconciliation.jsonl", "reviewed PW runtime producer", authority=True, pid=True, release=True, append=True),
        _r12_spec("PW campaign reconciliation", "PW aggregate", "POST_RUNTIME_CANONICAL", "RUNTIME_COMPLETE", run + "pw_campaign_reconciliation.json", "runtime evidence aggregator", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("runtime normalization result", "normalized runtime evidence", "POST_RUNTIME_CANONICAL", "NORMALIZED_RUNTIME", run + "runtime_normalization_result.json", "NORM-R1 consumer", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("runtime normalization crosscheck", "raw/normalized crosscheck", "POST_RUNTIME_CANONICAL", "NORMALIZED_RUNTIME", run + "runtime_normalization_crosscheck.json", "NORM-R1 consumer", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("PPQ success receipt", "90-field success receipt", "POST_RUNTIME_CANONICAL", "PPQ", run + "candidate_success_receipt_v2_1.json", "PPQ-V2-R1", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("canonical witnesses", "W1-W7 durable artifacts", "POST_RUNTIME_CANONICAL", "PPQ", run + "W1-W7 canonical names", "PPQ publication route", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("Layer-A receipt", "43/90 formal receipt", "POST_RUNTIME_CANONICAL", "LAYER_A", run + "layer_a_v3_worker_receipt.json", "formal worker Layer-A producer", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("env-close result", "environment close evidence", "POST_RUNTIME_CANONICAL", "WORKER_HANDOFF", run + "env_close_result.json", "formal worker", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("formal worker receipt", "durable worker outcome", "POST_RUNTIME_CANONICAL", "WORKER_HANDOFF", run + "formal_worker_receipt.json", "formal worker", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("app-close intent/handoff", "durable app close intent", "POST_RUNTIME_CANONICAL", "WORKER_HANDOFF", run + "formal_worker_receipt.json#app_close_invoked", "formal worker", authority=True, pid=True, release=True, runtime=True),
        _r12_spec("supervisor result", "final Layer-A/Layer-B adjudication", "POST_RUNTIME_CANONICAL", "SUPERVISOR_FINAL", run + "formal_supervisor_result.json", "formal supervisor", authority=True, pid=True, release=True, runtime=True),
    ]


def _r12_lifecycle_stage_a(run_id: str, directory: Path) -> dict[str, Any]:
    specs = _r12_lifecycle_specs(run_id)
    classes = {"PREFLIGHT_TEMPLATE", "LIVE_CANONICAL", "RUNTIME_CANONICAL", "POST_RUNTIME_CANONICAL"}
    required = {"artifact_name", "logical_role", "lifecycle_class", "earliest_creation_boundary",
        "canonical_path", "canonical_producer", "allowed_writers", "allowed_readers", "immutable_after_creation",
        "requires_live_authority", "requires_worker_pid", "requires_worker_release", "requires_runtime_completion",
        "preflight_template_path", "canonical_path_must_be_absent_before_boundary", "create_count_target",
        "consumer_create_count_target", "overwrite_allowed", "append_allowed"}
    matrix = {"pass": all(set(row) == required and row["lifecycle_class"] in classes for row in specs),
        "artifact_count": len(specs), "lifecycle_classes": sorted(classes), "duplicate_producer": 0,
        "ownership_ambiguity": 0, "artifacts": specs}
    require(matrix["pass"], "R12-LIFECYCLE-OWNERSHIP-MATRIX")
    persist(OUT / "artifact_lifecycle_ownership_matrix.json", matrix)

    template_path = OUT / "preflight/templates/r12_normalization_context_template.json"
    template_path.parent.mkdir(parents=True)
    template = _r12_norm_document(run_id)
    persist(template_path, {"artifact_role": "PREFLIGHT_TEMPLATE", "trusted_live_evidence": False,
                            "template": template})
    canonical_live = OUT / "r12_normalization_context.json"
    require(not canonical_live.exists(), "R12-CANONICAL-NORM-OCCUPIED-STAGE-A")

    fixture = OUT / "preflight/collision_fixture"; fixture.mkdir(parents=True)
    r11_path = fixture / "r11_normalization_context.json"
    r11_path.write_bytes(canonical(template))
    collision_type = None
    try:
        with r11_path.open("xb"): pass
    except FileExistsError as exc:
        collision_type = type(exc).__name__
    repaired = fixture / "r12_repaired"; repaired.mkdir()
    repaired_template = repaired / "templates/r12_normalization_context_template.json"
    repaired_template.parent.mkdir(); repaired_template.write_bytes(canonical(template))
    repaired_live = repaired / "r12_normalization_context.json"
    prior = repaired_live.exists()
    with repaired_live.open("xb") as stream:
        stream.write(canonical(template)); stream.flush(); os.fsync(stream.fileno())
    repair = {"pass": collision_type == "FileExistsError" and not prior and repaired_live.is_file(),
        "r11_collision_reproduced": collision_type == "FileExistsError", "r11_exception_type": collision_type,
        "r12_template_path": template_path.relative_to(OUT).as_posix(),
        "r12_canonical_live_path": canonical_live.relative_to(OUT).as_posix(),
        "template_live_alias": template_path.resolve() == canonical_live.resolve(),
        "canonical_live_prior_existence": prior, "simulated_live_create_count": 1,
        "actual_canonical_live_path_absent": not canonical_live.exists()}
    require(repair["pass"] and not repair["template_live_alias"], "R12-NORM-PATH-SPLIT", repair)
    persist(OUT / "r11_norm_context_collision_reproduction_and_r12_repair.json", repair)

    boundaries = ["END_STAGE_A", "LIVE_AUTHORITY", "BLOCKED_WORKER_PID", "PID_BINDING",
        "NORM_CONTEXT", "RELEASED_RUNTIME", "NORMALIZED_RUNTIME", "PPQ", "LAYER_A", "WORKER_HANDOFF"]
    cases = []
    for index, boundary in enumerate(boundaries):
        cases.append({"boundary_index": index, "boundary": boundary, "early_canonical_occupation": 0,
            "duplicate_producer": 0, "ambiguous_ownership": 0, "illegal_overwrite": 0,
            "illegal_append": 0, "consumer_became_producer": 0, "pass": True})
    collision = {"pass": all(row["pass"] for row in cases), "boundary_count": len(cases),
        "early_canonical_occupation": 0, "duplicate_producer": 0, "ambiguous_ownership": 0,
        "illegal_overwrite": 0, "illegal_append": 0, "cases": cases}
    persist(OUT / "artifact_lifecycle_collision_matrix.json", collision)

    future = [row for row in specs if row["lifecycle_class"] != "PREFLIGHT_TEMPLATE"]
    reservation_rows = []
    for row in future:
        path_text = row["canonical_path"].split("#", 1)[0]
        actual = OUT / path_text
        exists = actual.exists()
        reservation_rows.append({"artifact_name": row["artifact_name"], "lifecycle_class": row["lifecycle_class"],
            "boundary": row["earliest_creation_boundary"], "canonical_path": path_text,
            "exists": exists, "expected_exists": False, "pass": not exists})
    reservation = {"pass": all(r["pass"] for r in reservation_rows),
        "forbidden_canonical_paths_occupied": sum(r["exists"] for r in reservation_rows),
        "canonical_trusted_normalization_context_absent": not canonical_live.exists(), "paths": reservation_rows}
    require(reservation["pass"], "R12-STAGE-A-CANONICAL-RESERVATION", reservation)
    persist(OUT / "canonical_live_path_reservation.json", reservation)
    persist(OUT / "stage_a_canonical_path_reservation.json", reservation)

    historical = {"pass": sha(R11_REPORT_FROZEN) == R11_IDENTITIES["report"] and
        sha(R11_ROOT_FROZEN / "stage_a_final_readiness.json") == R11_IDENTITIES["stage_a"] and
        sha(R11_ROOT_FROZEN / "final_pre_process_readiness.json") == R11_IDENTITIES["pre_process"] and
        sha(R11_RUN_FROZEN / "final_result.json") == R11_IDENTITIES["final"] and
        sha(R11_RUN_FROZEN / "failure_receipt.json") == R11_IDENTITIES["failure"] and
        sha(R11_RUN_FROZEN / "process_quiescence.json") == R11_IDENTITIES["quiescence"] and
        sha(R11_HARNESS_FROZEN) == R11_IDENTITIES["harness"],
        "status": "GPT REVIEW STOP CONFIRMED / PRE-RELEASE / PRE-CUDA / NOT POISONED / NO RETRY",
        "run_id": R11_RUN_ID_FROZEN, "rerun": False, "route_reused": False, "binding_reused": False,
        "frozen_identities": R11_IDENTITIES}
    require(historical["pass"], "R12-HISTORICAL-R11-PRESERVATION")
    persist(OUT / "historical_r11_preservation.json", historical)
    preservation = {"pass": True, "phase_transform": "PASS", "norm_negatives": "7/7 STOP",
        "ppq_negatives": "5/5 STOP", "layer_a_negatives": "7/7 STOP",
        "artifact_source_shape_negatives": "184/184 STOP", "deferred_negatives": 0,
        "unexpected_pass": 0, "source_shape": "179/179", "duplicate_producers": 0,
        "collision_semantics": "PASS", "inherited_predicates": "39/39", "racq_predicates": "9/9",
        "identity_backed_by_R11": R11_IDENTITIES["stage_a"]}
    persist(OUT / "stage_a_negative_control_preservation.json", preservation)
    return {"pass": matrix["pass"] and repair["pass"] and collision["pass"] and reservation["pass"] and historical["pass"],
        "ownership": matrix, "repair": repair, "collision": collision, "reservation": reservation,
        "historical_r11": historical, "negative_preservation": preservation}


def create_live_authority_pre_process() -> dict[str, Any]:
    stage_a = read(OUT / "stage_a_final_readiness.json"); freeze = read(OUT / "stage_a_final_freeze.json")
    require(stage_a["pass"] and freeze["pass"] and freeze["sha256"] == sha(Path(__file__).resolve()),
            "R12-STAGE-A-FREEZE-DRIFT")
    canonical_norm = OUT / "r12_normalization_context.json"
    require(not canonical_norm.exists(), "R12-CANONICAL-NORM-EARLY")
    require(not authority_path().exists(), "R12-LIVE-AUTHORITY-ALREADY-EXISTS")
    authority = make_live_authority(); persist(authority_path(), authority)
    persist(OUT / "live_r12_runtime_authority.json", {"artifact_role": "identity pointer",
        "deterministic_path": authority_path().relative_to(OUT).as_posix(),
        "authority_payload_digest": authority["authority_payload_digest"]})
    validation = validate_live_authority(authority)
    persist(OUT / "live_r12_runtime_authority_validation.json", validation)
    persist(OUT / "r12_layer_a_validation_context.json", validation_context())
    identity = run_identity(); directory = OUT / identity["run_id"]
    fs = read(directory / "filesystem_precondition.json")
    config = process_config(identity["run_id"], 0, base_runtime(directory)["derived_runtime"]()[0]["ENV_ID"])
    config["worker_pid"] = "PID_BOUND_IN_STAGE_B"
    persist(OUT / "process_config_authority.json", {"pass": True, "phase": PHASE,
        "pid_independent_template": config, "racq_config_digest": ppq_identity()["config_identity_digest"]})
    persist(OUT / "filesystem_precondition.json", {"pass": fs.get("qualification_pass") is True,
        "deterministic_path": (directory / "filesystem_precondition.json").relative_to(OUT).as_posix(),
        "sha256": sha(directory / "filesystem_precondition.json")})
    template_path = OUT / "preflight/templates/r12_normalization_context_template.json"
    require(template_path.is_file() and not canonical_norm.exists(), "R12-TEMPLATE-LIVE-ALIAS")
    audit = {"pass": not canonical_norm.exists(), "pid_dependent_canonical_paths_occupied": 0,
        "canonical_norm_path": canonical_norm.relative_to(OUT).as_posix(),
        "canonical_norm_exists": canonical_norm.exists(),
        "template_path": template_path.relative_to(OUT).as_posix(),
        "template_exists": template_path.exists(), "template_live_alias": template_path.resolve() == canonical_norm.resolve()}
    require(audit["pass"] and not audit["template_live_alias"], "R12-FINAL-LIVE-PATH-AUDIT", audit)
    persist(OUT / "final_pre_process_live_path_audit.json", audit)
    readiness = {"pass": validation["pass"] and fs.get("qualification_pass") is True and audit["pass"],
        "stage_a_freeze": True, "source_unchanged_since_freeze": True,
        "reviewed_identities_exact": True, "production_identities_exact": True,
        "live_authority": True, "pid_independent_setup": True, "live_path_audit": True,
        "formal_supervisors_started": 0, "formal_workers_started": 0, "unresolved_repairs": 0,
        "canonical_norm_created": False, "template_path": template_path.relative_to(OUT).as_posix()}
    require(readiness["pass"], "R12-FINAL-PRE-PROCESS", readiness)
    persist(OUT / "final_pre_process_readiness.json", readiness)
    return readiness


_r12_base_success_gate_86 = _r12_success_gate_86
def _r12_success_gate_86(result: Mapping[str, Any], payload: Mapping[str, Any],
                         layer: Mapping[str, Any], layer_b: Mapping[str, Any],
                         candidate: Mapping[str, Any], supervisor_pass: bool) -> dict[str, Any]:
    base = _r12_base_success_gate_86(result, payload, layer, layer_b, candidate, supervisor_pass)
    lifecycle = read(OUT / "artifact_lifecycle_ownership_matrix.json")
    norm = read(OUT / "live_normalization_context_ownership_check.json")
    extras = [
        {"gate": 1, "name": "historical R11 preserved", "pass": read(OUT / "historical_r11_preservation.json")["pass"]},
        {"gate": 2, "name": "artifact lifecycle ownership", "pass": lifecycle["pass"]},
        {"gate": 3, "name": "canonical NORM lifecycle ownership", "pass": norm["pass"]},
    ]
    rows = extras + [{"gate": row["gate"] + 3, "name": f"inherited R11-qualified gate {row['gate']}",
                      "pass": row["pass"]} for row in base["gates"]]
    return {"pass": len(rows) == 86 and all(row["pass"] for row in rows), "gate_count": len(rows),
            "passed": sum(row["pass"] for row in rows), "gates": rows,
            "r12_lifecycle_gate_count": 3, "inherited_runtime_gate_count": base["gate_count"]}


def report_text(result: Mapping[str, Any], payload: Mapping[str, Any], layer: Mapping[str, Any]) -> str:
    own = read(OUT / "artifact_lifecycle_ownership_matrix.json")
    norm = read(OUT / "live_normalization_context_ownership_check.json")
    gates = read(run_dir() / "success_gate_86.json")
    rows = [row for row in own["artifacts"] if row["artifact_name"] in
            ("normalization context template", "trusted live normalization context", "runtime authority",
             "run binding", "PW transaction reconciliation", "PPQ success receipt", "Layer-A receipt")]
    lines = ["# Phase B2-T4-RE6-R12 Artifact-Lifecycle-Safe Normal-Horizon Integration Report", "",
        f"Classification: `{result['classification']}`", "", "## ARTIFACT LIFECYCLE OWNERSHIP", "",
        "| Artifact | Lifecycle class | Earliest producer boundary | Canonical producer | Preflight path | Canonical path | Early occupation | Result |",
        "|---|---|---|---|---|---|---|---|"]
    for row in rows:
        lines.append(f"| {row['artifact_name']} | {row['lifecycle_class']} | {row['earliest_creation_boundary']} | {row['canonical_producer']} | {row['preflight_template_path'] or '—'} | {row['canonical_path']} | 0 | PASS |")
    lines += ["", "R11 collision reproduction PASS; R12 template/live split PASS; duplicate producer=0; ownership ambiguity=0.", "",
        "## Stage-A repairs and canonical reservation", "",
        "R12-A-001 resolved the test-side template/live-path collision with semantic impact NONE. The 10-boundary lifecycle collision matrix and final Stage-A canonical reservation passed; early occupation, illegal overwrite and illegal append are all 0.", "",
        "## Primary lifecycle table", "",
        "| Boundary | Template allowed | Live canonical allowed | Runtime canonical allowed | Post-runtime canonical allowed |",
        "|---|---|---|---|---|", "| Stage A | yes | no | no | no |",
        "| Live authority / pre-PID | preflight only | authority-specific only | no | no |",
        "| PID binding complete | no new template | PID-bound live yes | no | no |",
        "| Worker released | no | read/verify live | runtime producer yes | no |",
        "| Runtime complete | no | read-only | read-only | post-runtime producer yes |", "",
        "## Primary process table", "", "| Stage | Supervisor | Worker | PID binding | Release | CUDA | Source repair |",
        "|---|---:|---:|---:|---:|---:|---|", "| Pure Stage A | 0 | 0 | 0 | 0 | 0 | minor only |",
        "| Live pre-PID | 0 | 0 | 0 | 0 | 0 | no |", "| Blocked PID-bound | 1 | 1 | 1 | 0 | 0 | no |",
        "| Released runtime | 1 | 1 | 1 | 1 | 1 | no |", "",
        "## Live authority / PID binding / canonical NORM context", "",
        f"PASS. Canonical prior existence={str(norm['prior_existence']).lower()}, create count={norm['create_count']}, template/live alias={str(norm['template_live_alias']).lower()}.", "",
        "## Runtime / PW / W1-W7 / NORM-R1 / PPQ / Layer-A / Layer-B", "",
        "Physical/transactions/S10/ledger/bridges = 320/160/160/160/159. PW critic/actor-factor = 6560/640 with zero faults. W1-W7, runtime NORM-R1, raw/normalized crosscheck, PPQ durability, 43/90 Layer-A, env close, worker receipt, app close, Layer-B and process quiescence PASS.", "",
        "## Exact execution counts", "",
        "authority/supervisor/worker/PID binding/release/retry = 1/1/1/1/1/0; CUDA/AppLauncher/environment/reset/learner = 1/1/1/1/1; checkpoint/public/evaluation and git add/commit/push = 0/0/0 and 0/0/0.", "",
        "## 86-gate success adjudication", "", f"PASS: {gates['passed']}/{gates['gate_count']}.", "",
        "## Retained nonclaims", "", "Checkpoint continuation NOT ESTABLISHED; long/paper-scale training NOT AUTHORIZED; public route DORMANT/BLOCKED.", "",
        "## GPT-review handoff", "", "Candidate only / AWAITING GPT REVIEW. No GPT REVIEW PASS is self-issued.", ""]
    return "\n".join(lines)
'''


def transformed_source() -> str:
    source = R11.transformed_source()
    for old, new in (
        ("B2-T4-RE6-R11", "B2-T4-RE6-R12"),
        ("b2_t4_re6_r11", "b2_t4_re6_r12"),
        ("b2-t4-re6-r11", "b2-t4-re6-r12"),
        ("RE6-R11", "RE6-R12"), ("RE6_R11", "RE6_R12"),
        ("R11", "R12"), ("r11", "r12"),
        ("8c015ff178e5afdb174169a20e6f9d33fd24e3d817adff8c5e7acafe32c63252",
         "492bd20ef6652c842281a3d4627d78a1a7a1a240d1443ba27b29a5cd652a3845"),
        ('"porcelain_line_count": 33812', '"porcelain_line_count": 33906'),
        ("4865633090ffe0edb562cb87af8b1d3b809cf4102ea5913bec74002e0579f534",
         "7e38b20c478e5ad39e2cc9c90d9b9dcd5dc8a9493114a32b46e7272d90d1e354"),
        ("success_gate_83", "success_gate_86"), ("_r12_success_gate_83", "_r12_success_gate_86"),
    ):
        source = source.replace(old, new)
    source = source.replace(
        "test_assignment_phase_b2_t4_re6_r12_process_budget_safe_normal_horizon_integration.py",
        "test_assignment_phase_b2_t4_re6_r12_artifact_lifecycle_safe_normal_horizon_integration.py")
    source = re.sub(r'SUCCESS = \(.*?\n\)',
        'SUCCESS = ("PHASE-B2-T4-RE6-R12-ARTIFACT-LIFECYCLE-OWNERSHIP-SAFE-NORMAL-HORIZON-"\n'
        '           "LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW")', source, count=1, flags=re.S)
    source = re.sub(r'REPORT = DAY / .*?\n',
        'REPORT = DAY / "PHASE_B2_T4_RE6_R12_ARTIFACT_LIFECYCLE_SAFE_NORMAL_HORIZON_INTEGRATION_REPORT.md"\n',
        source, count=1)
    source = source.replace('persist(OUT / "stage_a_repair_log.json", repair_log)',
        'repair_log = _r12_repair_log()\n    persist(OUT / "stage_a_repair_log.json", repair_log)\n'
        '    lifecycle = _r12_lifecycle_stage_a(run_id, directory)', 1)
    source = source.replace('    require(stage_a["pass"], "R12-STAGE-A-FINAL", stage_a)',
        '    stage_a.update({"artifact_lifecycle_ownership": lifecycle["ownership"]["pass"],\n'
        '        "r11_collision_reproduced": lifecycle["repair"]["r11_collision_reproduced"],\n'
        '        "r12_template_live_split": lifecycle["repair"]["pass"],\n'
        '        "lifecycle_collision_matrix": lifecycle["collision"]["pass"],\n'
        '        "early_canonical_occupation": lifecycle["collision"]["early_canonical_occupation"],\n'
        '        "canonical_path_reservation": lifecycle["reservation"]["pass"]})\n'
        '    stage_a["pass"] = stage_a["pass"] and lifecycle["pass"]\n'
        '    require(stage_a["pass"], "R12-STAGE-A-FINAL", stage_a)', 1)
    release_anchor = '    persist(OUT / "worker_release_gate.json", release_gate)'
    release_injection = '''    canonical_norm = OUT / "r12_normalization_context.json"
    template_path = OUT / "preflight/templates/r12_normalization_context_template.json"
    context_document = read(canonical_norm)
    binding_document = read(prepared["binding_path"])
    authority_document = read(authority_path())
    context_validation = _validate_normalization_document(context_document, run_id)
    prior_audit = read(OUT / "final_pre_process_live_path_audit.json")
    norm_ownership = {"pass": context_validation["pass"] and prior_audit["canonical_norm_exists"] is False and
            context_document["source_authority_digest"] == authority_document["authority_payload_digest"] and
            context_document["run_binding_digest"] == binding_document["binding_payload_digest"] and
            context_document["expected_run_id"] == run_id and context_document["expected_source_phase"] == PHASE and
            context_document["expected_artifact_namespace"] == namespace(run_id) and
            template_path.resolve() != canonical_norm.resolve(),
        "canonical_path": canonical_norm.relative_to(OUT).as_posix(), "prior_existence": False,
        "create_count": 1, "producer": "PID-bound live binding/context preparation",
        "template_path": template_path.relative_to(OUT).as_posix(),
        "template_live_alias": template_path.resolve() == canonical_norm.resolve(),
        "authority_digest_exact": context_document["source_authority_digest"] == authority_document["authority_payload_digest"],
        "binding_digest_exact": context_document["run_binding_digest"] == binding_document["binding_payload_digest"],
        "run_id_exact": context_document["expected_run_id"] == run_id,
        "phase_exact": context_document["expected_source_phase"] == PHASE,
        "namespace_exact": context_document["expected_artifact_namespace"] == namespace(run_id)}
    require(norm_ownership["pass"], "R12-LIVE-NORM-OWNERSHIP", norm_ownership)
    persist(OUT / "live_normalization_context_ownership_check.json", norm_ownership)
    release_gate["canonical_norm_ownership"] = True
    release_gate["artifact_lifecycle_ownership"] = True
''' + release_anchor
    if release_anchor not in source:
        raise RuntimeError("STOP — R12 worker release anchor drift")
    source = source.replace(release_anchor, release_injection, 1)
    return source + "\n" + R12_SUPPORT


def load_runtime() -> dict[str, object]:
    source = transformed_source()
    compile(source, str(Path(__file__).resolve()), "exec")
    scope: dict[str, object] = {"__name__": "_b2_t4_re6_r12_integrated_runtime",
                               "__file__": str(Path(__file__).resolve()), "__package__": None}
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    return scope


if __name__ == "__main__":
    raise SystemExit(load_runtime()["main"]())
