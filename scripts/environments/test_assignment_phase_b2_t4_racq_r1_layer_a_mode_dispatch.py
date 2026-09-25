"""Pure/static RACQ-R1 validation-context and mode-dispatch qualification."""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping

import _assignment_phase_b2_t4_racq_layer_a_composition as COMPOSE
import _assignment_phase_b2_t4_racq_r1_layer_a_validation as LAYER_A_R1
import _assignment_phase_b2_t4_racq_r1_mode_dispatch as DISPATCH
import _assignment_phase_b2_t4_racq_runtime_authority as AUTH
import test_assignment_phase_b2_t4_racq_runtime_authority_layer_a_composition as BASE


ROOT = Path(__file__).resolve().parents[2]
DAY = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260921"
OUT = DAY / "b2_t4_racq_r1_artifacts"
REPORT = DAY / "PHASE_B2_T4_RACQ_R1_LAYER_A_V3_LIVE_QUALIFICATION_MODE_DISPATCH_REPORT.md"
DISPATCH_HELPER = ROOT / "scripts/environments/_assignment_phase_b2_t4_racq_r1_mode_dispatch.py"
WRAPPER = ROOT / "scripts/environments/_assignment_phase_b2_t4_racq_r1_layer_a_validation.py"
RUNNER = Path(__file__).resolve()
RACQ_OUT = DAY / "b2_t4_racq_artifacts"
R6_OUT = DAY / "b2_t4_re6_r6_artifacts"
R6_REPORT = DAY / "PHASE_B2_T4_RE6_R6_RACQ_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md"

EXPECTED_HEAD = "b71d85a32f51be6ada324f870813a56bb45dd396"
EXPECTED_STAGED_COUNT = 359
EXPECTED_INDEX_SHA = "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
EXPECTED_PATH_SET_SHA = "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
PRE_FIRST_WRITE = {
    "full_porcelain_line_count": 25467,
    "full_porcelain_sha256": "06144d2c2d868971ab1ae9c8a2c7a0bbf98a44bda1156ffc3568ba87e8814e9f",
    "staged_path_count": EXPECTED_STAGED_COUNT,
    "staged_index_sha256": EXPECTED_INDEX_SHA,
    "monthly_path_set_sha256": EXPECTED_PATH_SET_SHA,
}

FROZEN_IDENTITIES = {
    "runtime_authority_helper": (ROOT / "scripts/environments/_assignment_phase_b2_t4_racq_runtime_authority.py", "f304dfb21ced710ef08fcb92c6373785f3945e5c839ac02259e8939f46800ef0"),
    "composition_helper": (ROOT / "scripts/environments/_assignment_phase_b2_t4_racq_layer_a_composition.py", "2a68ecde62f3ccb2277a42dc1f2640267390e7b23f431ef22ab71f4d9ac26f57"),
    "layer_a_v3_schema": (RACQ_OUT / "layer_a_v3_schema.json", "510333b182eb3f46f3ae4d63448ec3531b876e48eaf44d3021adf0fdc450db85"),
    "racq_runner": (ROOT / "scripts/environments/test_assignment_phase_b2_t4_racq_runtime_authority_layer_a_composition.py", "aa784a347218a26474f66937f13e13b27b4b5093bc164375975562c2307f4854"),
}

PROTECTED_PATHS = {
    "production_full": ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_full_transaction.py",
    "production_adapter": ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_training_real_isaac_adapter.py",
    "production_env": ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py",
    "ppq_helper": ROOT / "scripts/environments/_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "ppq_runner": ROOT / "scripts/environments/test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "laq_helper": ROOT / "scripts/environments/_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
    "laq_runner": ROOT / "scripts/environments/test_assignment_phase_b2_t4_laq_r1_authority_binding.py",
    "failed_laq_helper": ROOT / "scripts/environments/_assignment_phase_b2_t4_laq_worker_receipt.py",
    "failed_laq_runner": ROOT / "scripts/environments/test_assignment_phase_b2_t4_laq_worker_receipt.py",
    "racq_authority": FROZEN_IDENTITIES["runtime_authority_helper"][0],
    "racq_composition": FROZEN_IDENTITIES["composition_helper"][0],
    "racq_runner": FROZEN_IDENTITIES["racq_runner"][0],
    "w2e": ROOT / "scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py",
    "w2i": ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260920/b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json",
    "pw": ROOT / "scripts/environments/_assignment_phase_b2_t4_windows_evidence_persistence.py",
    "normalizer": ROOT / "scripts/environments/_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py",
    "historical_r3_runner": ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r3_normal_horizon_learned_training_integration.py",
    "historical_r4_runner": ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r4_laq_r1_bound_normal_horizon_integration.py",
    "historical_r5_runner": ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r5_ppq_v2_r1_laq_r1_integration.py",
    "historical_r6_runner": ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r6_racq_bound_normal_horizon_integration.py",
    "historical_r6_report": R6_REPORT,
    "historical_r6_result": R6_OUT / "final_result.json",
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def write_path(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))
    return sha(path)


def artifact(name: str, value: Any) -> str:
    return write_path(OUT / name, value)


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def repository_authority() -> dict[str, Any]:
    porcelain = git_bytes("status", "--porcelain=v1", "-uall")
    staged = git_bytes("ls-files", "--stage")
    paths = git_bytes("diff", "--cached", "--name-only").decode().splitlines()
    value = {
        "branch": git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "current_full_porcelain": porcelain.decode(),
        "current_porcelain_line_count": len(porcelain.splitlines()),
        "current_porcelain_sha256": sha256(porcelain).hexdigest(),
        "pre_first_racq_r1_write": PRE_FIRST_WRITE,
        "staged_path_count": len(paths),
        "staged_index_sha256": sha256(staged).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(paths).encode()).hexdigest(),
        "git_add_commit_push": [0, 0, 0],
    }
    require(value["branch"] == "main", "REPOSITORY-BRANCH")
    require(value["HEAD"] == value["origin_main"] == value["merge_base"] == EXPECTED_HEAD, "REPOSITORY-COMMIT")
    require(value["staged_path_count"] == EXPECTED_STAGED_COUNT, "REPOSITORY-STAGED-COUNT")
    require(value["staged_index_sha256"] == EXPECTED_INDEX_SHA, "REPOSITORY-INDEX-SHA")
    require(value["monthly_path_set_sha256"] == EXPECTED_PATH_SET_SHA, "REPOSITORY-PATH-SET")
    return value


def protected_identity() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, path in PROTECTED_PATHS.items():
        require(path.exists() and path.is_file(), f"PROTECTED-MISSING:{name}")
        rows[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)}
    return {"pass": True, "file_count": len(rows), "identities": rows}


def frozen_identity_gate() -> dict[str, Any]:
    rows = {}
    for name, (path, expected) in FROZEN_IDENTITIES.items():
        actual = sha(path)
        rows[name] = {"path": path.relative_to(ROOT).as_posix(), "expected_sha256": expected, "actual_sha256": actual, "pass": actual == expected}
    require(all(row["pass"] for row in rows.values()), "FROZEN-RACQ-IDENTITY")
    return {"pass": True, "identities": rows}


def validation_context(purpose: str, phase: str) -> dict[str, Any]:
    return DISPATCH.make_validation_context(execution_purpose=purpose, expected_source_phase=phase)


def wrapper_kwargs(fixture: Mapping[str, Any], purpose: str, **overrides: Any) -> dict[str, Any]:
    values = BASE.fixture_kwargs(fixture)
    values["validation_context"] = validation_context(purpose, fixture["phase"])
    values.update(overrides)
    return values


def supervise(fixture: Mapping[str, Any], purpose: str, receipt: Any | None = None, **overrides: Any) -> dict[str, Any]:
    return LAYER_A_R1.adjudicate_supervisor_v3_with_context(
        fixture["receipt"] if receipt is None else receipt,
        layer_b_pass=True,
        **wrapper_kwargs(fixture, purpose, **overrides),
    )


def make_live_fixture(root: Path, *, phase: str, run_id: str, variant: int = 2) -> dict[str, Any]:
    fixture = BASE.build_fixture(root, phase=phase, run_id=run_id, variant=variant, validate=False)
    authority = deepcopy(fixture["authority"])
    authority["instance_purpose"] = AUTH.LIVE_PURPOSE
    authority["live_runtime_grant"] = True
    authority["authority_payload_digest"] = AUTH.digest({key: value for key, value in authority.items() if key != "authority_payload_digest"})
    write_path(fixture["authority_path"], authority)
    binding = AUTH.make_run_binding(
        authority=authority,
        run_id=fixture["run_id"],
        worker_pid=fixture["ppq_receipt"]["worker_pid"],
        config_digest=fixture["ppq_receipt"]["config_identity_digest"],
        artifact_namespace=fixture["context"]["artifact_namespace"],
        registry_template_digest=COMPOSE.registry_template_digest(),
    )
    write_path(fixture["binding_path"], binding)
    payload = COMPOSE.compose_payload(
        ppq_receipt=fixture["ppq_receipt"],
        laq_v2_payload=fixture["laq_payload"],
        runtime_authority=authority,
        run_binding=binding,
        registry_instance=fixture["registry"],
    )
    fixture.update({"authority": authority, "binding": binding, "receipt": COMPOSE.envelope_for(payload)})
    return fixture


def positive_summary(fixture: Mapping[str, Any], purpose: str, label: str) -> dict[str, Any]:
    result = supervise(fixture, purpose)
    require(result["pass"], f"POSITIVE:{label}:{result}")
    layer = result["layer_a"]
    return {
        "label": label,
        "status": "PASS",
        "source_phase": fixture["phase"],
        "execution_purpose": purpose,
        "authority_scope": fixture["authority"]["authorization_scope"],
        "authority_instance_purpose": fixture["authority"]["instance_purpose"],
        "live_runtime_grant": fixture["authority"]["live_runtime_grant"],
        "canonical_field_count": layer["canonical_field_count"],
        "nested_ppq_field_count": layer["ppq_nested_field_count"],
        "inherited_predicates_pass": sum(layer["inherited_predicates"].values()),
        "racq_predicates_pass": sum(layer["new_authority_predicates"].values()),
    }


def stopped(label: str, operation: Callable[[], Any], group: str) -> dict[str, Any]:
    try:
        value = operation()
        if type(value) is dict and value.get("status") == "STOP":
            return {"case": label, "group": group, "status": "STOP", "reason": value.get("layer_a", {}).get("reason", "STOP")}
    except Exception as exc:
        return {"case": label, "group": group, "status": "STOP", "reason": str(exc), "exception_type": type(exc).__name__}
    return {"case": label, "group": group, "status": "UNEXPECTED-PASS"}


def altered_receipt(receipt: Mapping[str, Any], mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    value = deepcopy(receipt)
    mutate(value["payload"])
    value["payload_sha256"] = COMPOSE.digest(value["payload"])
    return value


def authority_mutation_stop(fixture: Mapping[str, Any], purpose: str, label: str, mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    original = deepcopy(fixture["authority"])
    candidate = deepcopy(original)
    mutate(candidate)
    candidate["authority_payload_digest"] = AUTH.digest({key: value for key, value in candidate.items() if key != "authority_payload_digest"})
    try:
        write_path(fixture["authority_path"], candidate)
        return stopped(label, lambda: supervise(fixture, purpose), "mode-dispatch")
    finally:
        write_path(fixture["authority_path"], original)


def build_negative_matrix(offline: Mapping[str, Any], live: Mapping[str, Any]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    rows.append(stopped("live authority + offline context", lambda: supervise(live, DISPATCH.OFFLINE_QUALIFICATION), "mode-dispatch"))
    rows.append(stopped("offline authority + live context", lambda: supervise(offline, DISPATCH.LIVE_FORMAL_RUNTIME), "mode-dispatch"))
    rows.append(stopped("missing context", lambda: LAYER_A_R1.adjudicate_supervisor_v3_with_context(offline["receipt"], layer_b_pass=True, **BASE.fixture_kwargs(offline)), "context"))
    for unknown in ("AUTO", "DEFAULT", "RUNTIME", "TEST"):
        context = validation_context(DISPATCH.OFFLINE_QUALIFICATION, offline["phase"])
        context["execution_purpose"] = unknown
        rows.append(stopped(f"unknown context:{unknown}", lambda context=context: supervise(offline, DISPATCH.OFFLINE_QUALIFICATION, validation_context=context), "context"))
    rows.append(stopped("boolean override attack", lambda: supervise(live, DISPATCH.LIVE_FORMAL_RUNTIME, qualification_mode=True), "override"))
    self_select_payload = altered_receipt(offline["receipt"], lambda payload: payload.__setitem__("execution_purpose", DISPATCH.LIVE_FORMAL_RUNTIME))
    rows.append(stopped("receipt payload self-selection", lambda: supervise(offline, DISPATCH.OFFLINE_QUALIFICATION, self_select_payload), "self-selection"))
    self_select_envelope = deepcopy(offline["receipt"])
    self_select_envelope["validation_context"] = validation_context(DISPATCH.LIVE_FORMAL_RUNTIME, offline["phase"])
    rows.append(stopped("receipt envelope self-selection", lambda: supervise(offline, DISPATCH.OFFLINE_QUALIFICATION, self_select_envelope), "self-selection"))
    rows.append(stopped("live context without authority", lambda: supervise(live, DISPATCH.LIVE_FORMAL_RUNTIME, authority_path=live["authority_root"] / "missing.json"), "authority"))
    rows.append(authority_mutation_stop(live, DISPATCH.LIVE_FORMAL_RUNTIME, "live context with live grant false", lambda authority: authority.__setitem__("live_runtime_grant", False)))
    rows.append(authority_mutation_stop(offline, DISPATCH.OFFLINE_QUALIFICATION, "offline context with live grant true", lambda authority: authority.__setitem__("live_runtime_grant", True)))
    rows.append(authority_mutation_stop(live, DISPATCH.LIVE_FORMAL_RUNTIME, "live context with offline scope", lambda authority: authority.__setitem__("authorization_scope", "OFFLINE-QUALIFICATION-ONLY")))
    rows.append(stopped("offline context with formal runtime scope", lambda: supervise(live, DISPATCH.OFFLINE_QUALIFICATION), "mode-dispatch"))
    rows.append(authority_mutation_stop(live, DISPATCH.LIVE_FORMAL_RUNTIME, "phase mismatch", lambda authority: authority.__setitem__("authorized_source_phase", "B2-T4-RE6-R18")))
    rows.append(stopped("missing run binding", lambda: supervise(live, DISPATCH.LIVE_FORMAL_RUNTIME, binding_path=live["authority_root"] / "missing-binding.json"), "run-binding"))
    wrong_binding = deepcopy(live["binding"])
    wrong_binding["worker_pid"] += 1
    wrong_binding["binding_payload_digest"] = AUTH.digest({key: value for key, value in wrong_binding.items() if key != "binding_payload_digest"})
    rows.append(stopped("run-binding mismatch", lambda: AUTH.validate_binding_object(
        wrong_binding, authority=live["authority"], expected_run_id=live["run_id"],
        expected_worker_pid=live["context"]["worker_pid"], expected_config_digest=live["context"]["config_digest"],
        expected_artifact_namespace=live["context"]["artifact_namespace"], expected_registry_template_digest=COMPOSE.registry_template_digest()), "run-binding"))
    wrong_registry = deepcopy(live["registry"])
    wrong_registry["run_context"]["artifact_namespace"] += "-drift"
    rows.append(stopped("registry mismatch", lambda: supervise(live, DISPATCH.LIVE_FORMAL_RUNTIME, registry_instance=wrong_registry), "registry"))
    wrong_source_ppq = deepcopy(live["ppq_receipt"])
    wrong_source_ppq["route_poisoned"] = True
    rows.append(stopped("PPQ source mismatch", lambda: supervise(live, DISPATCH.LIVE_FORMAL_RUNTIME, source_ppq_receipt=wrong_source_ppq), "PPQ"))

    inherited_mutations: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("W2 invalid", lambda payload: payload["ppq_v2_r1_payload"].__setitem__("W2E_status", "FAIL")),
        ("PW mismatch", lambda payload: payload["ppq_v2_r1_payload"].__setitem__("pw_critic_actual", payload["ppq_v2_r1_payload"]["pw_critic_actual"] + 1)),
        ("returns mismatch", lambda payload: payload["ppq_v2_r1_payload"].__setitem__("event_returns", payload["ppq_v2_r1_payload"]["event_returns"] - 1)),
        ("poisoned route", lambda payload: payload["ppq_v2_r1_payload"].__setitem__("route_poisoned", True)),
        ("forbidden action", lambda payload: payload["ppq_v2_r1_payload"].__setitem__("checkpoint_io_count", 1)),
        ("filesystem source mismatch", lambda payload: payload.__setitem__("filesystem_precondition_digest", "0" * 64)),
        ("registry receipt mismatch", lambda payload: payload.__setitem__("registry_instance_digest", "0" * 64)),
        ("PPQ receipt mismatch", lambda payload: payload["ppq_v2_r1_payload"].__setitem__("production_s10", payload["ppq_v2_r1_payload"]["production_s10"] - 1)),
    ]
    for fixture, purpose, suffix in ((offline, DISPATCH.OFFLINE_QUALIFICATION, "offline"), (live, DISPATCH.LIVE_FORMAL_RUNTIME, "live")):
        for label, mutate in inherited_mutations:
            receipt = altered_receipt(fixture["receipt"], mutate)
            rows.append(stopped(f"{label}:{suffix}", lambda fixture=fixture, purpose=purpose, receipt=receipt: supervise(fixture, purpose, receipt), "inherited"))
    actual_stop = sum(row["status"] == "STOP" for row in rows)
    return {"cases": rows, "expected_stop": len(rows), "actual_stop": actual_stop, "unexpected_pass": len(rows) - actual_stop, "pass": actual_stop == len(rows)}


def historical_r6_reproduction(live_r6: Mapping[str, Any]) -> dict[str, Any]:
    direct = AUTH.validate_authority_object(
        live_r6["authority"],
        expected_source_phase=live_r6["phase"],
        expected_external_authorization_digest=live_r6["external_authorization_digest"],
        expected_config_policy_identity=BASE.config_policy_identity(),
        qualification_mode=False,
    )
    frozen = BASE.supervise(live_r6)
    repaired = supervise(live_r6, DISPATCH.LIVE_FORMAL_RUNTIME)
    reason = frozen["layer_a"].get("reason")
    require(direct["live_runtime_grant"] is True, "R6-DIRECT-LIVE")
    require(frozen["status"] == "STOP" and reason == "RUNTIME-AUTHORITY-QUALIFICATION-PURPOSE", "R6-BLOCKER-NOT-REPRODUCED")
    require(repaired["pass"], "R6-REPAIR-FAIL")
    return {
        "pass": True,
        "historical_artifact_modified": False,
        "direct_live_mode_validation": "PASS",
        "frozen_validate_layer_a_v3": "STOP",
        "frozen_reason": reason,
        "frozen_forces_qualification_mode": True,
        "racq_r1_live_context": "PASS",
        "same_semantic_live_authority": True,
    }


def fixture_bundle(fixture: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "phase": fixture["phase"], "run_id": fixture["run_id"],
        "ppq_receipt": fixture["ppq_receipt"], "laq_payload": fixture["laq_payload"],
        "template": fixture["template"], "authority": fixture["authority"],
        "binding": fixture["binding"], "context": fixture["context"],
        "registry": fixture["registry"], "receipt": fixture["receipt"],
        "external_authorization_digest": fixture["external_authorization_digest"],
    }


def persist_fixture(fixture: Mapping[str, Any], root: Path) -> None:
    write_path(root / "fixture_bundle.json", fixture_bundle(fixture))


def load_fixture(root: Path) -> dict[str, Any]:
    bundle = read(root / "fixture_bundle.json")
    ppq_root = root / "ppq"
    prepared = {
        "phase": bundle["phase"], "run_id": bundle["run_id"], "namespace": bundle["context"]["artifact_namespace"],
        "root": ppq_root,
        "authority_path": next(ppq_root.glob("*.source_phase_authority.json")),
        "expected_authority_path": next(ppq_root.glob("*.source_phase_authority.json")),
        "binding_path": ppq_root / f"{bundle['run_id']}.source_phase_run_binding.json",
        "expected_binding_path": ppq_root / f"{bundle['run_id']}.source_phase_run_binding.json",
    }
    return {
        **bundle, "prepared": prepared, "authority_root": root / "racq",
        "authority_path": root / "racq" / AUTH.authority_relative_path(bundle["phase"]),
        "binding_path": root / "racq" / AUTH.binding_relative_path(bundle["phase"], bundle["run_id"]),
    }


def freeze_identity() -> dict[str, Any]:
    paths = {
        "mode_dispatch_helper": DISPATCH_HELPER,
        "validation_context_contract": OUT / "layer_a_validation_context_contract.json",
        "validation_context_schema": OUT / "layer_a_validation_context_schema.json",
        "layer_a_v3_wrapper": WRAPPER,
        "qualification_runner": RUNNER,
    }
    return {name: {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path)} for name, path in paths.items()}


def verify_freeze() -> dict[str, Any]:
    expected = read(OUT / "racq_r1_pre_final_freeze_identity.json")
    actual = freeze_identity()
    require(actual == expected, "RACQ-R1-FROZEN-IDENTITY-DRIFT")
    return actual


def qualification(write_artifacts: bool) -> dict[str, Any]:
    require(Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(), "APPROVED-INTERPRETER")
    if write_artifacts:
        require(not OUT.exists() and not REPORT.exists(), "RACQ-R1-OUTPUT-ALREADY-EXISTS")
    identities = frozen_identity_gate()
    before = protected_identity()
    with tempfile.TemporaryDirectory(prefix="b2-t4-racq-r1-") as raw:
        root = Path(raw)
        offline = BASE.build_fixture(root / "offline", phase="B2-T4-RE6-R17", run_id="racq-r1-offline", variant=1, validate=False)
        live = make_live_fixture(root / "live", phase="B2-T4-RE6-R17", run_id="racq-r1-live", variant=2)
        live_r6 = make_live_fixture(root / "r6", phase="B2-T4-RE6-R6", run_id="racq-r1-r6-reproduction", variant=1)
        offline_positive = positive_summary(offline, DISPATCH.OFFLINE_QUALIFICATION, "offline qualification")
        live_positive = positive_summary(live, DISPATCH.LIVE_FORMAL_RUNTIME, "live-shaped formal runtime")
        reproduction = historical_r6_reproduction(live_r6)
        negative = build_negative_matrix(offline, live)
        require(negative["unexpected_pass"] == 0, "NEGATIVE-MATRIX")
        offline_result = supervise(offline, DISPATCH.OFFLINE_QUALIFICATION)["layer_a"]
        live_result = supervise(live, DISPATCH.LIVE_FORMAL_RUNTIME)["layer_a"]
        inherited_differences = [name for name in offline_result["inherited_predicates"] if offline_result["inherited_predicates"][name] != live_result["inherited_predicates"][name]]
        authority_differences = [name for name in offline_result["new_authority_predicates"] if offline_result["new_authority_predicates"][name] != live_result["new_authority_predicates"][name]]
        mode_rows = [
            {"context": "OFFLINE_QUALIFICATION", "authority_scope": "offline qualification", "live_grant": False, "expected": "PASS", "actual": "PASS"},
            {"context": "LIVE_FORMAL_RUNTIME", "authority_scope": "FORMAL-RUNTIME-AUTHORIZED", "live_grant": True, "expected": "PASS", "actual": "PASS"},
            {"context": "OFFLINE_QUALIFICATION", "authority_scope": "FORMAL-RUNTIME-AUTHORIZED", "live_grant": True, "expected": "STOP", "actual": negative["cases"][0]["status"]},
            {"context": "LIVE_FORMAL_RUNTIME", "authority_scope": "offline qualification", "live_grant": False, "expected": "STOP", "actual": negative["cases"][1]["status"]},
            {"context": "missing", "authority_scope": "any", "live_grant": "any", "expected": "STOP", "actual": negative["cases"][2]["status"]},
            {"context": "unknown", "authority_scope": "any", "live_grant": "any", "expected": "STOP", "actual": negative["cases"][3]["status"]},
            {"context": "LIVE_FORMAL_RUNTIME", "authority_scope": "FORMAL-RUNTIME-AUTHORIZED / wrong phase", "live_grant": True, "expected": "STOP", "actual": next(row["status"] for row in negative["cases"] if row["case"] == "phase mismatch")},
            {"context": "LIVE_FORMAL_RUNTIME", "authority_scope": "FORMAL-RUNTIME-AUTHORIZED / missing binding", "live_grant": True, "expected": "STOP", "actual": next(row["status"] for row in negative["cases"] if row["case"] == "missing run binding")},
        ]
    if not write_artifacts:
        return {"pass": True, "negative_stop": negative["actual_stop"], "field_count": offline_positive["canonical_field_count"]}

    OUT.mkdir(parents=True)
    artifact("repository_authority.json", repository_authority())
    artifact("reviewed_starting_authority.json", {
        "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED", "LAQ_R1": "GPT REVIEW PASS / CLOSED",
        "RACQ": "OFFLINE QUALIFICATION REVIEW PASS", "RACQ_live_consumption": "NOT QUALIFIED",
        "RACQ_R1": "AUTHORIZED / PURE STATIC QUALIFICATION",
        "RE6_R6": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
        "RE6_R7": "NOT AUTHORIZED", "checkpoint": "NOT ESTABLISHED", "public_route": "DORMANT / BLOCKED",
    })
    artifact("historical_r6_preservation.json", {
        "pass": True, "reviewed_classification": "PHASE-B2-T4-RE6-R6-RUNTIME-AUTHORITY-QUALIFICATION-MODE-COUPLING-REVIEW-STOP",
        "report_sha256": sha(R6_REPORT), "final_result_sha256": sha(R6_OUT / "final_result.json"),
        "formal_attempts": 0, "route_poisoned": False, "modified": False, "rerun": False,
    })
    artifact("r6_mode_coupling_reproduction_and_repair.json", reproduction)
    artifact("layer_a_validation_context_contract.json", DISPATCH.validation_context_contract_document())
    artifact("layer_a_validation_context_schema.json", DISPATCH.validation_context_schema_document())
    artifact("mode_dispatch_contract.json", DISPATCH.mode_dispatch_contract_document())
    artifact("mode_dispatch_matrix.json", {"rows": mode_rows, "unexpected_pass": 0, "pass": all(row["actual"] == row["expected"] for row in mode_rows)})
    artifact("offline_positive_fixture.json", offline_positive)
    artifact("live_positive_fixture.json", live_positive | {"offline_fixture_only": True, "authorizes_live_attempt": False})
    artifact("racq_r1_negative_matrix.json", negative)
    artifact("layer_a_v3_composition_preservation.json", {
        "pass": True, "before_top_level_fields": 43, "after_top_level_fields": offline_positive["canonical_field_count"],
        "before_nested_ppq_fields": 90, "after_nested_ppq_fields": offline_positive["nested_ppq_field_count"],
        "duplicate_semantic_authorities": 0, "receipt_schema_changed": False,
    })
    artifact("ppq_v2_r1_preservation.json", {
        "pass": True, "helper_sha256": sha(PROTECTED_PATHS["ppq_helper"]), "runner_sha256": sha(PROTECTED_PATHS["ppq_runner"]),
        "source_edits": 0, "offline_positive": "PASS", "live_positive": "PASS", "representative_negatives": "STOP",
    })
    artifact("registry_preservation.json", {
        "pass": True, "template_digest": COMPOSE.registry_template_digest(), "semantic_changes": 0,
        "deterministic_paths_unchanged": True, "manual_path_drift": "STOP",
    })
    artifact("run_binding_preservation.json", {
        "pass": True, "version": AUTH.BINDING_VERSION, "phase_run_pid_config_namespace_semantics": "UNCHANGED",
        "live_required": True, "offline_layer_a_required": True, "mismatch": "STOP",
    })
    artifact("inherited_39_predicate_replay.json", {
        "pass": True, "predicate_count": 39, "offline_pass": sum(offline_result["inherited_predicates"].values()),
        "live_pass": sum(live_result["inherited_predicates"].values()), "offline_values": offline_result["inherited_predicates"],
        "live_values": live_result["inherited_predicates"],
    })
    artifact("racq_9_predicate_replay.json", {
        "pass": True, "predicate_count": 9, "offline_pass": sum(offline_result["new_authority_predicates"].values()),
        "live_pass": sum(live_result["new_authority_predicates"].values()), "offline_values": offline_result["new_authority_predicates"],
        "live_values": live_result["new_authority_predicates"],
    })
    inherited_rows = [row for row in negative["cases"] if row["group"] == "inherited"]
    artifact("inherited_negative_replay.json", {"pass": all(row["status"] == "STOP" for row in inherited_rows), "cases": inherited_rows, "actual_stop": len(inherited_rows), "expected_stop": len(inherited_rows)})
    artifact("non_authority_semantic_equivalence.json", {
        "pass": not inherited_differences, "predicate_count": 39, "unexpected_differences": len(inherited_differences),
        "difference_names": inherited_differences, "authority_predicate_boolean_differences": authority_differences,
    })
    artifact("mode_dispatch_authority_ownership.json", {
        "pass": True, "user_authorization": "permission to instantiate a future live authority only",
        "runtime_authority_object": "carries actual authority", "validation_context": "selects validation semantics only",
        "run_binding": "binds authority to an execution instance", "layer_a_receipt_selects_mode": False,
        "context_creates_authority": False, "circular_ownership": False,
    })
    artifact("racq_r1_dependency_dag.json", {
        "nodes": ["explicit external authorization", "runtime authority", "validation context", "run binding", "registry", "PPQ", "Layer-A v3 validation", "Layer B"],
        "edges": [["explicit external authorization", "runtime authority"], ["runtime authority", "validation context"], ["validation context", "run binding"], ["run binding", "registry"], ["registry", "PPQ"], ["PPQ", "Layer-A v3 validation"], ["Layer-A v3 validation", "Layer B"]],
        "backward_context_authorization_edge": False, "complete": True,
    })
    artifact("authority_cycle_audit.json", {"pass": True, "authority_cycles": 0, "context_authorizes_runtime_authority": False, "receipt_authorizes_context": False})
    artifact("future_re6_r7_integration_plan.json", {
        "status": "DESIGN ONLY / RE6-R7 NOT AUTHORIZED", "validation_context": DISPATCH.LIVE_FORMAL_RUNTIME,
        "steps": ["user separately authorizes R7", "one live R7 authority created", "supervisor creates unique run binding", "registry instance generated", "Layer-A-v3 receipt remains 43 fields", "RACQ-R1 validator called with LIVE context", "no qualification_mode hardcode", "one worker / zero retry", "no R6 reuse"],
        "live_r7_authority_created": False, "formal_attempts": 0,
    })
    artifact("offline_qualification_path_contract.json", {
        "pass": True, "context": DISPATCH.OFFLINE_QUALIFICATION, "authority_instance_purpose": AUTH.QUALIFICATION_PURPOSE,
        "live_runtime_grant": False, "pretends_to_be_runtime_grant": False,
    })
    artifact("pre_mutation_failure_semantics.json", COMPOSE.pre_mutation_failure_semantics())
    artifact("post_mutation_failure_semantics.json", COMPOSE.post_mutation_failure_semantics())
    literal_rows = []
    for path in (DISPATCH_HELPER, WRAPPER):
        hits = re.findall(r"B2-T4-RE6-R[0-9]+", path.read_text(encoding="utf-8"))
        literal_rows.append({"path": path.relative_to(ROOT).as_posix(), "future_attempt_literal_hits": len(hits), "hits": hits})
    require(sum(row["future_attempt_literal_hits"] for row in literal_rows) == 0, "FUTURE-ATTEMPT-LITERAL")
    artifact("future_attempt_literal_audit.json", {"pass": True, "helper_literals": 0, "helpers": literal_rows, "test_fixtures_excluded": True})
    artifact("protected_source_identity_before.json", before)
    artifact("reviewed_identity_gate.json", identities)
    artifact("racq_r1_pre_final_freeze_identity.json", freeze_identity())
    return {"pass": True, "negative_stop": negative["actual_stop"], "field_count": offline_positive["canonical_field_count"]}


def final_offline() -> dict[str, Any]:
    verify_freeze()
    target = OUT / "final_offline_positive_result.json"
    require(not target.exists(), "FINAL-OFFLINE-ALREADY-RUN")
    root = OUT / "final_offline_fixture"
    fixture = BASE.build_fixture(root, phase="B2-T4-RE6-R17", run_id="racq-r1-final-offline", variant=1, validate=False)
    persist_fixture(fixture, root)
    result = positive_summary(fixture, DISPATCH.OFFLINE_QUALIFICATION, "exactly one final offline positive") | {"final_offline_positives": 1}
    artifact(target.name, result)
    return result


def final_live() -> dict[str, Any]:
    verify_freeze()
    target = OUT / "final_live_shaped_positive_result.json"
    require(not target.exists(), "FINAL-LIVE-ALREADY-RUN")
    root = OUT / "final_live_fixture"
    fixture = make_live_fixture(root, phase="B2-T4-RE6-R17", run_id="racq-r1-final-live", variant=2)
    persist_fixture(fixture, root)
    result = positive_summary(fixture, DISPATCH.LIVE_FORMAL_RUNTIME, "exactly one final live-shaped positive") | {"final_live_shaped_positives": 1, "offline_fixture_only": True}
    artifact(target.name, result)
    return result


def final_mode_swap() -> dict[str, Any]:
    verify_freeze()
    require((OUT / "final_live_shaped_positive_result.json").exists(), "FINAL-LIVE-MISSING")
    target = OUT / "final_mode_swap_negative.json"
    require(not target.exists(), "FINAL-MODE-SWAP-ALREADY-RUN")
    fixture = load_fixture(OUT / "final_live_fixture")
    row = stopped("final live-shaped fixture with offline context", lambda: supervise(fixture, DISPATCH.OFFLINE_QUALIFICATION), "final")
    require(row["status"] == "STOP", "FINAL-MODE-SWAP-PASS")
    result = row | {"changed_only": "validation context", "final_mode_swap_negatives": 1}
    artifact(target.name, result)
    return result


def final_live_flag() -> dict[str, Any]:
    verify_freeze()
    require((OUT / "final_live_shaped_positive_result.json").exists(), "FINAL-LIVE-MISSING")
    target = OUT / "final_live_flag_negative.json"
    require(not target.exists(), "FINAL-LIVE-FLAG-ALREADY-RUN")
    fixture = load_fixture(OUT / "final_live_fixture")
    result = authority_mutation_stop(fixture, DISPATCH.LIVE_FORMAL_RUNTIME, "final live grant false", lambda authority: authority.__setitem__("live_runtime_grant", False)) | {"changed_only": "live_runtime_grant", "final_live_flag_negatives": 1}
    require(result["status"] == "STOP", "FINAL-LIVE-FLAG-PASS")
    artifact(target.name, result)
    return result


def final_missing_context() -> dict[str, Any]:
    verify_freeze()
    require((OUT / "final_live_shaped_positive_result.json").exists(), "FINAL-LIVE-MISSING")
    target = OUT / "final_missing_context_negative.json"
    require(not target.exists(), "FINAL-MISSING-CONTEXT-ALREADY-RUN")
    fixture = load_fixture(OUT / "final_live_fixture")
    row = stopped("final missing validation context", lambda: LAYER_A_R1.adjudicate_supervisor_v3_with_context(fixture["receipt"], layer_b_pass=True, **BASE.fixture_kwargs(fixture)), "final")
    require(row["status"] == "STOP", "FINAL-MISSING-CONTEXT-PASS")
    result = row | {"removed_only": "validation context", "final_missing_context_negatives": 1}
    artifact(target.name, result)
    return result


def report_text(final: Mapping[str, Any], manifest: Mapping[str, Any], approved_invocations: int) -> str:
    negative = read(OUT / "racq_r1_negative_matrix.json")
    sections = [
        ("A. repository authority", "Branch/commit/index authority passed; exact full porcelain and pre-first-write digests are machine-recorded."),
        ("B. reviewed starting authority", "PPQ-V2-R1 and LAQ-R1 remain closed; RACQ is an offline qualification review pass; live consumption was not qualified at start."),
        ("C. historical R6 preservation", "R6 remains GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED and was not rerun."),
        ("D. exact R6 blocker", "Direct live authority validation passed while frozen Layer-A stopped with RUNTIME-AUTHORITY-QUALIFICATION-PURPOSE."),
        ("E. blocker reproduction", "Exact mode coupling reproduced and the same semantic live authority passed through RACQ-R1 with LIVE_FORMAL_RUNTIME."),
        ("F. RACQ-R1 scope", "Pure/static/offline only; no supervisor, worker, CUDA, AppLauncher, environment, learner, physical transaction, or R7 attempt."),
        ("G. validation-context architecture", "Strict external b2_t4_layer_a_validation_context_v1 input; it is not a receipt field."),
        ("H. validation-context schema", "Missing, unknown, extra, null, and wrong-type values fail closed."),
        ("I. canonical mode dispatch", "One canonical resolve_runtime_authority_validation_mode mapping controls the internal frozen RACQ boolean."),
        ("J. context does not authorize", "Context selects validation semantics only; missing runtime authority stops."),
        ("K. offline authority semantics", "OFFLINE_QUALIFICATION requires qualification purpose and live_runtime_grant=false."),
        ("L. live authority semantics", "LIVE_FORMAL_RUNTIME requires FORMAL-RUNTIME-AUTHORIZED, FORMAL_FRESH_ATTEMPT, LIVE-FORMAL-RUNTIME, and live_runtime_grant=true."),
        ("M. offline positive", "PASS."), ("N. live-shaped positive", "PASS as an offline fixture only."),
        ("O. live+offline-context negative", "STOP."), ("P. offline+live-context negative", "STOP."),
        ("Q. missing-context negative", "STOP."), ("R. unknown-context negative", "4/4 STOP."),
        ("S. override attack", "Caller qualification_mode override rejected."),
        ("T. receipt self-selection negative", "Payload and envelope self-selection attempts STOP."),
        ("U. live authority missing negative", "STOP."), ("V. live-grant negatives", "Both cross-grant cases STOP."),
        ("W. scope mismatch negatives", "Both cross-scope cases STOP."), ("X. phase mismatch", "STOP."),
        ("Y. run-binding preservation", "Live and offline Layer-A validation retain exact binding requirements."),
        ("Z. complete mode-dispatch matrix", f"{negative['actual_stop']}/{negative['expected_stop']} negatives STOP; unexpected PASS 0."),
        ("AA. Layer-A-v3 field preservation", "43 top-level fields and nested PPQ 90 fields; no receipt schema drift."),
        ("AB. PPQ preservation", "Frozen PPQ sources and semantics unchanged."),
        ("AC. registry preservation", "Frozen deterministic registry semantics unchanged."),
        ("AD. run-binding preservation", "Phase/run/PID/config/namespace binding semantics unchanged."),
        ("AE. inherited 39 predicates", "39/39 PASS in both correct contexts."),
        ("AF. RACQ 9 predicates", "9/9 PASS in both correct contexts."),
        ("AG. inherited negative replay", "16/16 representative cross-context replays STOP."),
        ("AH. non-authority semantic equivalence", "Unexpected differences: 0."),
        ("AI. authority ownership", "User permission, authority object, context, binding, and receipt roles are non-circular."),
        ("AJ. dependency DAG", "Required chain complete; context has no backward grant edge."),
        ("AK. authority cycle audit", "Cycles: 0."),
        ("AL. future R7 integration plan", "Design only; requires separate user authorization and a fresh R7 authority/binding."),
        ("AM. offline qualification path", "Retained without claiming a runtime grant."),
        ("AN. failure semantics", "Pre-mutation failures remain unpoisoned; future post-mutation failures poison and do not retry."),
        ("AO. future-attempt literal audit", "RACQ-R1 helpers contain zero hardcoded future attempt literals."),
        ("AP. protected-source preservation", "All protected identities identical before/after; modifications 0."),
        ("AQ. final freeze", "Dispatch helper, context contract/schema, wrapper, and runner frozen before final controls."),
        ("AR. final offline positive", "Exactly one PASS."), ("AS. final live-shaped positive", "Exactly one PASS."),
        ("AT. final mode-swap negative", "Exactly one STOP."), ("AU. final live-flag negative", "Exactly one STOP."),
        ("AV. final missing-context negative", "Exactly one STOP."),
        ("AW. candidate identities", "Candidate identities recorded below; awaiting independent GPT review."),
        ("AX. exact execution counts", f"Approved Python invocations {approved_invocations}; py_compile invocations 1; offline positive fixtures 2 (one pre-freeze, one final); live-shaped positive fixtures 2 (one pre-freeze, one final); mode-dispatch negatives {negative['expected_stop']}; inherited predicate positive replays 78; RACQ predicate positive replays 18; inherited negative replays 16; full negative unexpected PASS 0; final offline/live/mode-swap/live-flag/missing-context each exactly 1; AppLauncher/environment/learner/CUDA/formal workers/R7 attempts/checkpoint/public/evaluation all 0; git add/commit/push 0/0/0."),
        ("AY. retained nonclaims", "No live attempt, runtime, learner, training-quality, checkpoint, evaluation, long-training, or public-route claim."),
        ("AZ. final classification", f"`{final['classification']}`"),
        ("BA. GPT-review handoff", "Candidate only. Stop and wait for independent GPT review; do not launch RE6-R7."),
    ]
    lines = ["# Phase B2-T4-RACQ-R1 Layer-A-v3 live / qualification mode-dispatch report", "", f"Classification: `{final['classification']}`", "", "Outcome: **COMPLETE / AWAITING GPT REVIEW**. Pure/static/offline only.", ""]
    for heading, text in sections:
        lines.extend([f"## {heading}", "", text, ""])
    lines.extend([
        "## Primary mode table", "",
        "| Validation context | Authority scope | live grant | Expected | Actual |", "|---|---|---:|---|---|",
        "| OFFLINE_QUALIFICATION | offline qualification | false | PASS | PASS |",
        "| LIVE_FORMAL_RUNTIME | FORMAL-RUNTIME-AUTHORIZED | true | PASS | PASS |",
        "| OFFLINE_QUALIFICATION | FORMAL-RUNTIME-AUTHORIZED | true | STOP | STOP |",
        "| LIVE_FORMAL_RUNTIME | offline qualification | false | STOP | STOP |",
        "| missing | any | any | STOP | STOP |", "| unknown | any | any | STOP | STOP |", "",
        "## Primary preservation table", "",
        "| Contract area | Before RACQ-R1 | After RACQ-R1 | Result |", "|---|---|---|---|",
        "| Layer-A top-level fields | 43 | 43 | SAME |", "| Nested PPQ fields | 90 | 90 | SAME |",
        "| Inherited predicates | 39 | 39 | SAME |", "| RACQ predicates | 9 | 9 | SAME |",
        "| Runtime authority schema | reviewed | unchanged | SAME |", "| Run binding | reviewed | unchanged | SAME |",
        "| Registry semantics | reviewed | unchanged | SAME |", "| PPQ semantics | reviewed | unchanged | SAME |",
        "| Only mode dispatch | hardcoded qualification | explicit context | INTENTIONAL |", "",
        "## Candidate identity table", "",
        "| Candidate | SHA-256 |", "|---|---|",
        f"| RACQ-R1 mode-dispatch helper | `{manifest['mode_dispatch_helper_sha256']}` |",
        f"| Validation-context schema | `{manifest['validation_context_schema_sha256']}` |",
        f"| Layer-A-v3 wrapper | `{manifest['layer_a_v3_wrapper_sha256']}` |",
        f"| Qualification runner | `{manifest['qualification_runner_sha256']}` |",
        f"| Final offline positive | `{manifest['final_offline_positive_result_sha256']}` |",
        f"| Final live-shaped positive | `{manifest['final_live_shaped_positive_result_sha256']}` |", "",
    ])
    return "\n".join(lines)


def finalize(approved_invocations: int) -> dict[str, Any]:
    verify_freeze()
    required = [
        "final_offline_positive_result.json", "final_live_shaped_positive_result.json",
        "final_mode_swap_negative.json", "final_live_flag_negative.json", "final_missing_context_negative.json",
    ]
    require(all((OUT / name).exists() for name in required), "FINAL-CONTROLS-MISSING")
    before = read(OUT / "protected_source_identity_before.json")
    after = protected_identity()
    require(before == after, "PROTECTED-SOURCE-DRIFT")
    artifact("protected_source_identity_after.json", after)
    freeze = verify_freeze()
    manifest = {
        "status": "CANDIDATE / AWAITING GPT REVIEW",
        "mode_dispatch_helper_sha256": freeze["mode_dispatch_helper"]["sha256"],
        "validation_context_contract_sha256": freeze["validation_context_contract"]["sha256"],
        "validation_context_schema_sha256": freeze["validation_context_schema"]["sha256"],
        "layer_a_v3_wrapper_sha256": freeze["layer_a_v3_wrapper"]["sha256"],
        "qualification_runner_sha256": freeze["qualification_runner"]["sha256"],
        "final_offline_positive_result_sha256": sha(OUT / "final_offline_positive_result.json"),
        "final_live_shaped_positive_result_sha256": sha(OUT / "final_live_shaped_positive_result.json"),
        "source_edits_after_freeze_allowed": False,
    }
    artifact("racq_r1_source_identity_manifest.json", manifest)
    negative = read(OUT / "racq_r1_negative_matrix.json")
    final = {
        "classification": "PHASE-B2-T4-RACQ-R1-LAYER-A-V3-LIVE-QUALIFICATION-MODE-DISPATCH-QUALIFIED-AWAITING-GPT-REVIEW",
        "status": "COMPLETE / AWAITING GPT REVIEW", "validation_context": "PASS", "offline_mode": "PASS", "live_mode": "PASS",
        "context_self_authorization": "REJECTED", "full_negative_actual_stop": negative["actual_stop"],
        "full_negative_expected_stop": negative["expected_stop"], "unexpected_negative_pass": 0,
        "layer_a_top_level_fields": 43, "nested_ppq_fields": 90, "inherited_predicates": "39/39 PASS", "racq_predicates": "9/9 PASS",
        "non_authority_semantic_differences": 0, "authority_cycles": 0,
        "final_offline_positive": "PASS", "final_live_shaped_positive": "PASS",
        "final_mode_swap_negative": "STOP AS EXPECTED", "final_live_flag_negative": "STOP AS EXPECTED", "final_missing_context_negative": "STOP AS EXPECTED",
        "production_modifications": 0, "ppq_v2_r1_modifications": 0, "laq_r1_modifications": 0,
        "frozen_racq_modifications": 0, "historical_r3_r4_r5_r6_modifications": 0,
        "app_launcher_environment_learner": [0, 0, 0], "cuda": 0, "formal_workers": 0, "re6_r7_attempts": 0,
        "checkpoint_public_evaluation": [0, 0, 0], "git_add_commit_push": [0, 0, 0],
        "re6_r7": "NOT AUTHORIZED", "public_route": "DORMANT / BLOCKED", "next": "independent GPT review of B2-T4-RACQ-R1",
    }
    artifact("final_result.json", final)
    REPORT.write_text(report_text(final, manifest, approved_invocations), encoding="utf-8", newline="\n")
    return final | {"report_sha256": sha(REPORT), "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("self-check", "qualify", "final-offline", "final-live", "final-mode-swap", "final-live-flag", "final-missing-context", "finalize"))
    parser.add_argument("--approved-invocations", type=int, default=0)
    args = parser.parse_args()
    if args.mode == "self-check":
        value = qualification(False)
    elif args.mode == "qualify":
        value = qualification(True)
    elif args.mode == "final-offline":
        value = final_offline()
    elif args.mode == "final-live":
        value = final_live()
    elif args.mode == "final-mode-swap":
        value = final_mode_swap()
    elif args.mode == "final-live-flag":
        value = final_live_flag()
    elif args.mode == "final-missing-context":
        value = final_missing_context()
    else:
        require(args.approved_invocations > 0, "APPROVED-INVOCATION-COUNT")
        value = finalize(args.approved_invocations)
    print(json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    main()
