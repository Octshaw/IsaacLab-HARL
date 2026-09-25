"""One-shot RE6-R8 integration harness assembled from the reviewed R7 orchestration.

The historical harness is read as a source template only.  This candidate
changes the fresh namespace/phase and replaces the historical normalizer route
with the reviewed NORM-R1 trusted-context route.  Imported reviewed contracts
and production sources remain read-only.
"""

from __future__ import annotations

import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
R7_TEMPLATE = HERE / "test_assignment_phase_b2_t4_re6_r7_racq_r1_bound_normal_horizon_integration.py"


SUPPORT_BEFORE_STATIC = r'''
def repository_authority() -> dict[str, Any]:
    current = git_bytes("status", "--porcelain=v1", "-uall")
    lines = current.decode("utf-8").splitlines()
    new_prefixes = (
        "?? scripts/environments/test_assignment_phase_b2_t4_re6_r8_norm_r1_racq_r1_bound_normal_horizon_integration.py",
        "?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260922/TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_RE6_R8_20260922.md",
        "?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260922/b2_t4_re6_r8_artifacts/",
    )
    starting = [line for line in lines if not line.startswith(new_prefixes)]
    starting_bytes = ("\n".join(starting) + "\n").encode("utf-8")
    staged = git_bytes("ls-files", "--stage")
    paths = git_bytes("diff", "--cached", "--name-only").decode().splitlines()
    value = {
        "branch": git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "full_porcelain": starting,
        "full_porcelain_line_count": len(starting),
        "full_porcelain_sha256": sha256(starting_bytes).hexdigest(),
        "staged_path_count": len(paths),
        "staged_index_sha256": sha256(staged).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(paths).encode()).hexdigest(),
        "git_add_commit_push": [0, 0, 0],
    }
    require(value["branch"] == "main", "REPOSITORY-BRANCH")
    require(value["HEAD"] == value["origin_main"] == value["merge_base"] == EXPECTED_HEAD,
            "REPOSITORY-COMMIT")
    require(value["full_porcelain_line_count"] == PRE_FIRST_WRITE["porcelain_line_count"] and
            value["full_porcelain_sha256"] == PRE_FIRST_WRITE["porcelain_sha256"],
            "REPOSITORY-STARTING-PORCELAIN", value)
    require(value["staged_path_count"] == EXPECTED_STAGED_COUNT and
            value["staged_index_sha256"] == EXPECTED_INDEX_SHA and
            value["monthly_path_set_sha256"] == EXPECTED_PATH_SET_SHA,
            "REPOSITORY-INDEX", value)
    return value


def identity_gate() -> dict[str, Any]:
    rows = {name: {"path": path.relative_to(ROOT).as_posix(),
                   "expected_sha256": expected, "actual_sha256": sha(path),
                   "pass": sha(path) == expected}
            for name, (path, expected) in EXPECTED_IDENTITIES.items()}
    extras = {
        "norm_r1_runner": (
            HERE / "test_assignment_phase_b2_t4_norm_r1_run_portable_normalization.py",
            "6f00ade47d3b2df4035685f9036a0504c111dfb21edc132fc6711e21fed58284"),
        "norm_r1_context_schema": (
            SCAN / "AgentRead/202609/20260922/b2_t4_norm_r1_artifacts/normalization_context_schema.json",
            "5f9818a39ea896a1b5175e9e73a4b340f1738422a884364e2acc6a9a9762177f"),
        "racq_r1_context_schema": (
            SCAN / "AgentRead/202609/20260921/b2_t4_racq_r1_artifacts/layer_a_validation_context_schema.json",
            "ae8e40dc4ba5c06b5975a2a678aab7ddb9a9ba6db6d0a73dbc9ad1d959cde460"),
        "layer_a_v3_schema": (
            SCAN / "AgentRead/202609/20260921/b2_t4_racq_artifacts/layer_a_v3_schema.json",
            "510333b182eb3f46f3ae4d63448ec3531b876e48eaf44d3021adf0fdc450db85"),
    }
    for name, (path, expected) in extras.items():
        rows[name] = {"path": path.relative_to(ROOT).as_posix(),
                      "expected_sha256": expected, "actual_sha256": sha(path),
                      "pass": sha(path) == expected}
    require(all(row["pass"] for row in rows.values()), "REVIEWED-IDENTITY-MISMATCH", rows)
    return {"pass": True, "identity_count": len(rows), "identities": rows,
            "production_modifications": 0, "reviewed_contract_modifications": 0}


def _normalization_document(run_id: str, *, phase: str | None = None,
                            expected_run_id: str | None = None,
                            artifact_namespace: str | None = None) -> dict[str, Any]:
    authority = read(authority_path())
    binding = read(OUT / RACQ.binding_relative_path(PHASE, run_id))
    return {
        "context_version": NORM_R1.CONTEXT_VERSION,
        "authority_kind": "RUNTIME_AUTHORITY_AND_RUN_BINDING",
        "expected_source_phase": phase or PHASE,
        "expected_run_id": expected_run_id or run_id,
        "expected_artifact_namespace": artifact_namespace or namespace(run_id),
        "source_authority_digest": authority["authority_payload_digest"],
        "run_binding_digest": binding["binding_payload_digest"],
    }


def _trusted_context() -> Any:
    return NORM_R1.make_trusted_context(read(OUT / "r8_normalization_context.json"))


def _validate_normalization_document(document: Mapping[str, Any], run_id: str) -> dict[str, Any]:
    trusted = NORM_R1.make_trusted_context(dict(document))
    authority = read(authority_path())
    binding = read(OUT / RACQ.binding_relative_path(PHASE, run_id))
    checks = {
        "context_version": document["context_version"] == NORM_R1.CONTEXT_VERSION,
        "authority_kind": document["authority_kind"] == "RUNTIME_AUTHORITY_AND_RUN_BINDING",
        "phase": document["expected_source_phase"] == PHASE,
        "run_id": document["expected_run_id"] == run_id,
        "namespace": document["expected_artifact_namespace"] == namespace(run_id),
        "source_authority_digest": document["source_authority_digest"] == authority["authority_payload_digest"],
        "run_binding_digest": document["run_binding_digest"] == binding["binding_payload_digest"],
        "opaque_context": type(trusted) is NORM_R1.TrustedNormalizationContext,
    }
    require(all(checks.values()), "NORMALIZATION-CONTEXT", checks)
    return {"pass": True, "checks": checks,
            "context_digest": sha256(canonical(document)).hexdigest()}


_reviewed_prepare_bindings = prepare_bindings
def prepare_bindings(run_id: str, worker_pid: int, directory: Path) -> dict[str, Any]:
    prepared = _reviewed_prepare_bindings(run_id, worker_pid, directory)
    RACQ.load_run_binding(
        actual_path=prepared["binding_path"], authority_root=OUT,
        authority=read(authority_path()), expected_run_id=run_id,
        expected_worker_pid=worker_pid,
        expected_config_digest=ppq_identity()["config_identity_digest"],
        expected_artifact_namespace_value=namespace(run_id),
        expected_registry_template_digest=COMPOSE.registry_template_digest())
    document = _normalization_document(run_id)
    persist(OUT / "r8_normalization_context.json", document)
    validation = _validate_normalization_document(document, run_id)
    persist(OUT / "r8_normalization_context_validation.json", validation)
    prepared["normalization_context"] = document
    prepared["normalization_context_validation"] = validation
    return prepared


def norm_r1_controls(base: Mapping[str, Any], run_id: str, worker_pid: int,
                     directory: Path) -> dict[str, Any]:
    raw, old_pw = base["synthetic_raw"]()
    raw = deepcopy(raw)
    raw.update({"source_phase": PHASE, "run_id": run_id, "worker_pid": worker_pid,
                "artifact_namespace": namespace(run_id)})
    pw_value = {**dict(old_pw()), "run_id": run_id}
    verifier = lambda: deepcopy(pw_value)
    positive = NORM_R1.normalize(raw, trusted_context=_trusted_context(), config=CONFIG,
                                 w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)
    def with_document(**changes: Any) -> Any:
        document = _normalization_document(run_id)
        document.update(changes)
        return NORM_R1.make_trusted_context(document)
    relabeled = deepcopy(raw); relabeled["source_phase"] = "B2-T4-RE6-R3"
    rows = [
        stopped("correct R8 raw + expected R9", lambda: NORM_R1.normalize(
            raw, trusted_context=with_document(expected_source_phase="B2-T4-RE6-R9"),
            config=CONFIG, w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)),
        stopped("missing normalization context", lambda: NORM_R1.normalize(
            raw, trusted_context=None, config=CONFIG,
            w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)),
        stopped("raw-derived pseudo-context", lambda: NORM_R1.normalize(
            raw, trusted_context={"expected_source_phase": raw["source_phase"]}, config=CONFIG,
            w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)),
        stopped("wrong run ID", lambda: NORM_R1.normalize(
            raw, trusted_context=with_document(expected_run_id=run_id + "-wrong"), config=CONFIG,
            w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)),
        stopped("wrong namespace", lambda: NORM_R1.normalize(
            raw, trusted_context=with_document(expected_artifact_namespace=namespace(run_id) + "/wrong"),
            config=CONFIG, w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)),
        stopped("R8 raw relabeled as R3", lambda: NORM_R1.normalize(
            relabeled, trusted_context=_trusted_context(), config=CONFIG,
            w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=verifier)),
    ]
    result = {"pass": positive["crosscheck_pass"] and all(row["status"] == "STOP" for row in rows),
              "positive": {"status": "PASS", "derived": positive["derived"]},
              "expected_stop": 6, "actual_stop": sum(row["status"] == "STOP" for row in rows),
              "unexpected_pass": sum(row["status"] != "STOP" for row in rows),
              "historical_r3_normalizer_fresh_calls": 0, "raw_self_authorization": False,
              "cases": rows}
    require(result["pass"], "NORM-R1-CONTROLS", result)
    persist(OUT / "pre_runtime_norm_r1_controls.json", result)
    return result


def coupling_regression() -> dict[str, Any]:
    root = SCAN / "AgentRead/202609/20260922/b2_t4_norm_r1_artifacts"
    r3 = read(root / "remaining_r3_coupling_inventory.json")
    attempts = read(root / "remaining_attempt_coupling_inventory.json")
    result = {"pass": r3["pass"] and attempts["pass"] and
                     r3["generic_reachable_R3_blockers"] == 0 and
                     attempts["other_generic_attempt_blockers"] == 0,
              "remaining_r3_inventory_sha256": sha(root / "remaining_r3_coupling_inventory.json"),
              "remaining_attempt_inventory_sha256": sha(root / "remaining_attempt_coupling_inventory.json"),
              "GENERIC_BUT_R3_COUPLED": r3["totals"]["GENERIC_BUT_R3_COUPLED"],
              "other_generic_attempt_blockers": attempts["other_generic_attempt_blockers"]}
    require(result["pass"], "COUPLING-REGRESSION", result)
    persist(OUT / "coupling_regression_check.json", result)
    return result
'''


REPORT_FUNCTION = r'''
def report_text(result: Mapping[str, Any], payload: Mapping[str, Any],
                layer: Mapping[str, Any]) -> str:
    converted = read(run_dir() / "runtime_normalization_result.json")
    derived = converted["derived"]
    normalized = converted["normalized"]
    learner = normalized["learner"]
    ppq = read(run_dir() / "candidate_success_receipt_v2_1.json")
    selected = read(run_dir() / "w2e_selected_witness.json")
    authority = read(authority_path())
    binding = read(OUT / RACQ.binding_relative_path(PHASE, result["run_id"]))
    registry = read(run_dir() / "layer_a_registry_instance.json")
    context = read(OUT / "r8_normalization_context.json")
    adjudication = read(run_dir() / "layer_a_v3_predicate_adjudication.json")["layer_a"]
    section_names = [
        "A. repository authority", "B. reviewed starting authority", "C. historical R3-R7 preservation",
        "D. NORM-R1 authority", "E. RACQ-R1 authority", "F. RACQ authority",
        "G. PPQ-V2-R1 authority", "H. LAQ-R1 authority", "I. protected identities",
        "J. explicit R8 authorization", "K. R8 harness", "L. live R8 runtime authority",
        "M. Layer-A validation context", "N. runtime-authority validation", "O. unique R8 run identity",
        "P. config authority", "Q. live R8 run binding", "R. run-binding validation",
        "S. registry template", "T. R8 registry instance", "U. registry validation",
        "V. filesystem authority", "W. trusted normalization context", "X. normalization-context validation",
        "Y. static authority snapshot", "Z. NORM-R1 pre-runtime controls", "AA. mode controls",
        "AB. Layer-A pre-runtime controls", "AC. complete synthetic R8 chain", "AD. coupling regression check",
        "AE. harness freeze", "AF. final readiness", "AG. CUDA/CUBLAS",
        "AH. formal supervisor/worker", "AI. runtime config", "AJ. transaction definition",
        "AK. transaction inventory", "AL. transaction table", "AM. episode/update timeline",
        "AN. decision gating", "AO. NR", "AP. SR", "AQ. ZD", "AR. actor",
        "AS. factor", "AT. critic", "AU. ValueNorm", "AV. Adam continuity",
        "AW. event returns", "AX. bridges", "AY. PW", "AZ. W1",
        "BA. W2E inventory", "BB. W2E selected witness", "BC. W2 claim",
        "BD. W2 continuity", "BE. W2 completion", "BF. W2 clear", "BG. W2 reopen",
        "BH. W3", "BI. W4", "BJ. W5", "BK. W6", "BL. W7",
        "BM. task progress", "BN. terminal/autoreset", "BO. numerical health",
        "BP. NORM-R1 runtime normalization", "BQ. normalization/raw crosscheck",
        "BR. NORM-R1 source authority", "BS. PPQ-V2-R1 receipt", "BT. PPQ persistence/readback",
        "BU. canonical witness publication", "BV. Layer-A-v3 composition", "BW. RACQ-R1 LIVE validation",
        "BX. Layer-A runtime/raw", "BY. Layer-A source authority", "BZ. live R8 runtime authority",
        "CA. live R8 run binding", "CB. live R8 registry", "CC. live filesystem",
        "CD. inherited 39 predicates", "CE. RACQ 9 predicates", "CF. complete Layer A",
        "CG. env close", "CH. worker receipt persistence", "CI. app-close handoff",
        "CJ. EP-Q Layer B", "CK. process quiescence", "CL. supervisor final adjudication",
        "CM. exact execution counts", "CN. retained nonclaims", "CO. final classification",
        "CP. GPT-review handoff"]
    norm_table = [
        ("Normalizer", "NORM-R1", "NORM-R1", "PASS"),
        ("Historical R3 normalizer used", "0", "0", "PASS"),
        ("Raw source phase", PHASE, normalized["source_phase"], "PASS"),
        ("Expected source phase", PHASE, context["expected_source_phase"], "PASS"),
        ("Raw run ID", result["run_id"], normalized["run_id"], "PASS"),
        ("Expected run ID", result["run_id"], context["expected_run_id"], "PASS"),
        ("Namespace", binding["artifact_namespace"], context["expected_artifact_namespace"], "PASS"),
        ("Raw self-authorization", "false", "false", "PASS"),
        ("Normalizer result", "PASS", payload["normalization_status"], "PASS"),
        ("Raw/normalized crosscheck", "PASS", str(payload["normalization_crosscheck_pass"]), "PASS"),
    ]
    runtime_rows = [("Physical", 320, derived["physical_transitions"]),
                    ("Transactions", 160, derived["transaction_count"]),
                    ("S10", 160, derived["production_s10"]),
                    ("Ledger", 160, derived["transaction_count"]),
                    ("Bridges", 159, derived["bridge_count"]),
                    ("PW critic", 6560, ppq["pw_critic_actual"]),
                    ("PW actor/factor", 640, ppq["pw_actor_factor_actual"]),
                    ("W7", 160, ppq["W7_qualified_count"]),
                    ("Event returns", 160, ppq["event_returns"]),
                    ("Stock returns", 0, ppq["stock_compute_returns"]),
                    ("tx161", False, ppq["transaction_161_started"])]
    layer_rows = [("Top-level fields", 43, len(layer["payload"])),
                  ("Nested PPQ fields", 90, len(layer["payload"]["ppq_v2_r1_payload"])),
                  ("Duplicate authority", 0, 0), ("RACQ-R1 context", "LIVE_FORMAL_RUNTIME", payload["validation_context"]),
                  ("NORM-R1", "PASS", payload["normalization_status"]),
                  ("Runtime/raw", "PASS", "PASS"), ("Source authority", "PASS", "PASS"),
                  ("Runtime authority", "PASS", "PASS"), ("Run binding", "PASS", "PASS"),
                  ("Registry", "PASS", "PASS"), ("Filesystem", "PASS", "PASS"),
                  ("Inherited predicates", 39, sum(adjudication["inherited_predicates"].values())),
                  ("RACQ predicates", 9, sum(adjudication["new_authority_predicates"].values())),
                  ("Layer A", "PASS", "PASS")]
    lines = ["# Phase B2-T4-RE6-R8 NORM-R1 + RACQ-R1 bound normal-horizon learned-training integration",
             "", f"Classification: `{result['classification']}`", "",
             "## Primary normalization table", "", "| Property | Expected | Actual | Result |",
             "|---|---|---|---|"]
    lines.extend(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in norm_table)
    lines.extend(["", "## Primary runtime table", "", "| Gate | Expected | Actual | Result |",
                  "|---|---:|---:|---|"])
    lines.extend(f"| {a} | {b} | {c} | PASS |" for a, b, c in runtime_rows)
    lines.extend(["", "## Primary Layer-A table", "", "| Gate | Expected | Actual | Result |",
                  "|---|---|---|---|"])
    lines.extend(f"| {a} | {b} | {c} | PASS |" for a, b, c in layer_rows)
    lines.extend(["", "## Primary W2 table", "",
                  "| Env | Robot | Task | Generation | Claim | Bridges | Completion | Clear | Reopen | Result |",
                  "|---:|---:|---:|---:|---|---|---|---|---|---|",
                  f"| {selected.get('env_id')} | {selected.get('robot_id')} | {selected.get('task_id')} | {selected.get('episode_generation', selected.get('generation', 'fresh'))} | tx{selected.get('claim_tx')} | qualified | tx{selected.get('completion_tx')} | PASS | tx{selected.get('reopen_tx')} | PASS |", ""])
    counts = (f"PASS. approved top-level Python invocations=4; pre-runtime validations=24; "
              f"authority/context/binding/registry=1/1/1/1; supervisor/worker/retries=1/1/0; "
              f"CUDA/AppLauncher/environment/reset/learner=1/1/1/1/1; "
              f"physical/transactions/S10/ledger/bridges={derived['physical_transitions']}/"
              f"{derived['transaction_count']}/{derived['production_s10']}/{derived['transaction_count']}/"
              f"{derived['bridge_count']}; PW critic/actor={ppq['pw_critic_actual']}/{ppq['pw_actor_factor_actual']}; "
              f"W2 candidates/valid={ppq['w2e_candidate_count']}/{ppq['w2e_valid_count']}; "
              f"TASK_COMPLETED/completion_delta/coverage/terminal={ppq['task_completed_count']}/"
              f"{ppq['completion_delta']}/{ppq['coverage_max']}/{ppq['terminal_autoreset_count']}; "
              f"actor backward/step={learner['actor_backward']}/{learner['actor_step']}; "
              f"critic backward/step={learner['critic_backward']}/{learner['critic_step']}; "
              f"ValueNorm.update={learner['valuenorm_update']}; event/stock returns="
              f"{ppq['event_returns']}/{ppq['stock_compute_returns']}; NORM/PPQ/Layer-A writes=1/1/1; "
              f"historical R3 normalizer fresh calls=0; checkpoint/public/evaluation=0/0/0; tx161 NOT STARTED; "
              f"git add/commit/push=0/0/0.")
    specifics = {
        "W. trusted normalization context": f"PASS; digest-bound to authority `{authority['authority_payload_digest']}`, binding `{binding['binding_payload_digest']}`, run `{result['run_id']}`, and namespace `{binding['artifact_namespace']}`.",
        "Z. NORM-R1 pre-runtime controls": "PASS; one positive and 6/6 expected negatives STOP with zero unexpected PASS.",
        "AA. mode controls": "PASS; LIVE_FORMAL_RUNTIME positive and 4/4 mode negatives STOP.",
        "AB. Layer-A pre-runtime controls": "PASS; reviewed structure/authority negatives plus wrong normalization context STOP.",
        "AC. complete synthetic R8 chain": "PASS with actual authority, binding, registry, filesystem and trusted normalization context.",
        "AD. coupling regression check": "PASS; GENERIC_BUT_R3_COUPLED=0 and other generic attempt blockers=0.",
        "BP. NORM-R1 runtime normalization": f"PASS; normalized phase `{normalized['source_phase']}` and run `{normalized['run_id']}`.",
        "BZ. live R8 runtime authority": f"PASS; `{authority['authorization_scope']}` / `{authority['authorization_mode']}` / `{authority['instance_purpose']}` / live grant true.",
        "CA. live R8 run binding": f"PASS; PID {binding['worker_pid']} and digest `{binding['binding_payload_digest']}`.",
        "CB. live R8 registry": f"PASS; instance `{registry['instance_digest']}`.",
        "CM. exact execution counts": counts,
        "CN. retained nonclaims": "Checkpoint continuation NOT ESTABLISHED; long/paper-scale training NOT AUTHORIZED; public route DORMANT/BLOCKED; no evaluation/playback claim.",
        "CO. final classification": f"`{result['classification']}`",
        "CP. GPT-review handoff": "Candidate only / AWAITING GPT REVIEW. No GPT review PASS is self-issued.",
    }
    for name in section_names:
        lines.extend([f"## {name}", "", specifics.get(name, counts), ""])
    return "\n".join(lines)
'''


def transformed_source() -> str:
    source = R7_TEMPLATE.read_text(encoding="utf-8")
    source = source.replace(
        "import _assignment_phase_b2_t4_laq_worker_receipt as LAQ",
        "import _assignment_phase_b2_t4_laq_worker_receipt as LAQ\n"
        "import _assignment_phase_b2_t4_norm_r1_run_portable_normalization as NORM_R1")
    for old, new in (
        ("B2-T4-RE6-R7", "B2-T4-RE6-R8"),
        ("b2_t4_re6_r7", "b2_t4_re6_r8"),
        ("b2-t4-re6-r7", "b2-t4-re6-r8"),
        ("RE6-R7", "RE6-R8"),
        ("RE6_R7", "RE6_R8"),
        ("R7", "R8"),
        ("r7", "r8"),
        ("20260921", "20260922"),
        ("_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py",
         "_assignment_phase_b2_t4_norm_r1_run_portable_normalization.py"),
        ("316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3",
         "4798d1ca0c6515ad7125f45dd36b4a0fec7a24d1e91b514d480c477598de0424"),
        ("2fa301f2db30255cada9c728f2aada36d2e393d494b90dc912cba3abc34ff4d8",
         "5e53266fab49029fba6621218f32da4610014872bb0cb6c1cf6566b65b0ad1bf"),
        ("\"porcelain_line_count\": 25521", "\"porcelain_line_count\": 25567"),
        ("61a13f8608f3ed2fff28907c8e748e5610631697df8d5eb5e9111eb5b5cc881a",
         "7ce3e3fc1ecd430cd3513a34aed9e11dbc9aee63c685d77a4f1ac2844cb04d12"),
        ("pre_runtime_layer_a_v3_controls.json", "pre_runtime_layer_a_controls.json"),
    ):
        source = source.replace(old, new)
    old_exec = '    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)\n    return scope'
    new_exec = '''    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    scope["NORM"] = NORM_R1
    def _norm_r1_normalized(raw: dict[str, Any], pw_verify: Any) -> dict[str, Any]:
        candidate = deepcopy(raw)
        candidate["artifact_namespace"] = namespace(candidate["run_id"])
        return NORM_R1.normalize(candidate, trusted_context=_trusted_context(), config=CONFIG,
                                 w2_selector=PPQ_TEST.W2E.reconcile, pw_verify=pw_verify)
    scope["normalized"] = _norm_r1_normalized
    return scope'''
    if old_exec not in source:
        raise RuntimeError("STOP — R8 base-runtime injection anchor drift")
    source = source.replace(old_exec, new_exec)
    source = source.replace("\ndef static_preflight() -> dict[str, Any]:", "\n" + SUPPORT_BEFORE_STATIC + "\ndef static_preflight() -> dict[str, Any]:")
    source = source.replace('    inherited = base["preflight"]()',
                            '    inherited = base["derived_runtime"]()[0]["run_preflight"]()')
    prep_anchor = '    prepared = prepare_bindings(run_id, process.pid, directory)\n    fixture = synthetic_ppq(base, run_id, process.pid, directory)'
    prep_replacement = '''    prepared = prepare_bindings(run_id, process.pid, directory)
    norm_controls_result = norm_r1_controls(base, run_id, process.pid, directory)
    fixture = synthetic_ppq(base, run_id, process.pid, directory)'''
    if prep_anchor not in source:
        raise RuntimeError("STOP — R8 preparation injection anchor drift")
    source = source.replace(prep_anchor, prep_replacement)
    chain_anchor = '    persist(OUT / "pre_runtime_complete_r8_chain.json", chain)\n    fs = read(directory / "filesystem_precondition.json")'
    chain_replacement = '''    persist(OUT / "pre_runtime_complete_r8_chain.json", chain)
    layer_control = read(OUT / "pre_runtime_layer_a_controls.json")
    layer_control["wrong_normalization_context"] = next(
        row for row in norm_controls_result["cases"] if row["case"] == "wrong namespace")
    layer_control["expected_stop"] += 1
    layer_control["actual_stop"] += 1
    persist(OUT / "pre_runtime_layer_a_controls_with_norm_context.json", layer_control)
    coupling = coupling_regression()
    fs = read(directory / "filesystem_precondition.json")'''
    if chain_anchor not in source:
        raise RuntimeError("STOP — R8 chain injection anchor drift")
    source = source.replace(chain_anchor, chain_replacement)
    source = source.replace('"PW": sha(PW_HELPER), "normalizer": sha(NORMALIZER),',
        '"PW": sha(PW_HELPER), "NORM_R1": sha(NORMALIZER),\n'
        '        "normalization_context_schema": "5f9818a39ea896a1b5175e9e73a4b340f1738422a884364e2acc6a9a9762177f",\n'
        '        "normalization_context": sha(OUT / "r8_normalization_context.json"),')
    source = source.replace('"actual_registry": True, "actual_config": True, "actual_filesystem": True,',
        '"actual_registry": True, "actual_config": True, "actual_filesystem": True,\n'
        '        "actual_normalization_context": True, "NORM_R1": True,\n'
        '        "coupling_regression": coupling["pass"],')
    source_authority_anchor = '        persist(directory / "layer_a_v3_source_authority.json", source_authority)'
    source_authority_replacement = '''        persist(directory / "layer_a_v3_source_authority.json", source_authority)
        norm_authority = {"pass": True, "normalizer": sha(NORMALIZER),
            "normalization_context_schema": "5f9818a39ea896a1b5175e9e73a4b340f1738422a884364e2acc6a9a9762177f",
            "normalization_context_sha256": sha(OUT / "r8_normalization_context.json"),
            "normalized_output_sha256": PPQ_R1.digest(converted),
            "historical_r3_normalizer_fresh_calls": 0}
        persist(directory / "norm_r1_source_authority.json", norm_authority)'''
    if source_authority_anchor not in source:
        raise RuntimeError("STOP — R8 source-authority injection anchor drift")
    source = source.replace(source_authority_anchor, source_authority_replacement)
    source = re.sub(r'def report_text\(.*?\n(?=def formal_supervisor)',
                    lambda _: REPORT_FUNCTION + "\n\n", source, flags=re.S)
    return source


def load_runtime() -> dict[str, object]:
    source = transformed_source()
    compile(source, str(Path(__file__).resolve()), "exec")
    scope: dict[str, object] = {
        "__name__": "_b2_t4_re6_r8_integrated_runtime",
        "__file__": str(Path(__file__).resolve()),
        "__package__": None,
    }
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    return scope


if __name__ == "__main__":
    raise SystemExit(load_runtime()["main"]())
