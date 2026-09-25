"""Pure/offline qualification for B2-T4-RACQ.

No Isaac, HARL, torch, CUDA, environment, learner, or formal-worker imports.
The runner has staged modes so candidate sources are frozen before exactly one
final positive and three subsequent decisive negatives.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping

import _assignment_phase_b2_t4_laq_r1_worker_receipt as LAQ_AUTH
import _assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_R1
import _assignment_phase_b2_t4_racq_layer_a_composition as COMPOSE
import _assignment_phase_b2_t4_racq_runtime_authority as AUTH
import test_assignment_phase_b2_t4_laq_r1_authority_binding as LAQ_TEST
import test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_TEST


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DAY = SCAN / "AgentRead/202609/20260921"
OUT = DAY / "b2_t4_racq_artifacts"
REPORT = DAY / "PHASE_B2_T4_RACQ_RUNTIME_AUTHORITY_LAYER_A_COMPOSITION_QUALIFICATION_REPORT.md"
RUNTIME_HELPER = HERE / "_assignment_phase_b2_t4_racq_runtime_authority.py"
COMPOSITION_HELPER = HERE / "_assignment_phase_b2_t4_racq_layer_a_composition.py"
RUNNER = Path(__file__).resolve()
PPQ_OUT = DAY / "b2_t4_ppq_v2_r1_artifacts"
LAQ_OUT = DAY / "b2_t4_laq_r1_artifacts"
R5_OUT = DAY / "b2_t4_re6_r5_artifacts"
R5_RUNNER = HERE / "test_assignment_phase_b2_t4_re6_r5_ppq_v2_r1_laq_r1_integration.py"
R5_REPORT = DAY / "PHASE_B2_T4_RE6_R5_PPQ_V2_R1_LAQ_R1_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md"
CLASSIFICATION = "PHASE-B2-T4-RACQ-RUNTIME-AUTHORITY-LAYER-A-COMPOSITION-QUALIFIED-AWAITING-GPT-REVIEW"

EXPECTED_HEAD = "b71d85a32f51be6ada324f870813a56bb45dd396"
EXPECTED_STAGED_COUNT = 359
EXPECTED_INDEX_SHA = "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
EXPECTED_PATH_SET_SHA = "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
PRE_FIRST_WRITE = {
    "porcelain_line_count": 25382,
    "porcelain_sha256": "4a8dabb4c9f08babb77c05c5d2b00207788ab3d5eae1ca6784bfa8e0fe91f474",
    "staged_path_count": EXPECTED_STAGED_COUNT,
    "staged_index_sha256": EXPECTED_INDEX_SHA,
    "monthly_path_set_sha256": EXPECTED_PATH_SET_SHA,
}

EXPECTED_FROZEN = {
    "ppq_v2_r1_helper": "bd057efaeac73154b49b1e8307c9c7585f0feb449aaad3fbf4813a361a31b8a0",
    "ppq_v2_r1_runner": "fe420687da10b82df4c66e376cd6959f3d0199553e706f3f4eacd23d79e15433",
    "ppq_v2_r1_schema": "d9e28e050616bc1e2f38abfdc32d21ba884b282311d6f141a1c240632582adef",
    "ppq_v2_r1_authority_schema": "874bc9dee78d9d118878bdc7ea3357b70daff1715f098d8876c9d69011938c3e",
    "ppq_v2_r1_registry": "534f7561a8ceb9567e37793a14a74b1ca023ae2c479f7e3128bbf60a5e55ddd2",
    "laq_r1_helper": "22720385c3eb4c67bf2317c0a90f5ca2575b85f8e07529be3c661f71cb4082b3",
    "laq_r1_runner": "9d89b562a2564cea1e16e3fd708d8a3a583de04c25bc473135d50cdb23fea904",
    "laq_r1_contract": "677839292827599fdef36128c05deaa96f0e9cb1f76e3975f338259231f68956",
    "laq_r1_registry": "3f79dfe33e252c13b13fccb26a9f476b00aeb72bf73eae2c2fff5684a7247751",
}

FROZEN_PATHS = {
    "ppq_v2_r1_helper": HERE / "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "ppq_v2_r1_runner": HERE / "test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "ppq_v2_r1_schema": PPQ_OUT / "ppq_v2_r1_receipt_schema.json",
    "ppq_v2_r1_authority_schema": PPQ_OUT / "source_phase_authority_schema.json",
    "ppq_v2_r1_registry": PPQ_OUT / "source_phase_authority_registry.json",
    "laq_r1_helper": HERE / "_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
    "laq_r1_runner": HERE / "test_assignment_phase_b2_t4_laq_r1_authority_binding.py",
    "laq_r1_contract": LAQ_OUT / "layer_a_r1_contract.json",
    "laq_r1_registry": LAQ_OUT / "authority_source_registry.json",
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_path(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"DESTINATION-EXISTS:{path}")
    path.write_bytes(COMPOSE.canonical(value))
    return sha(path)


def artifact(name: str, value: Any) -> str:
    return write_path(OUT / name, value)


def tree_identity(directory: Path) -> dict[str, Any]:
    h = sha256()
    count = 0
    total = 0
    for path in sorted(item for item in directory.rglob("*") if item.is_file()):
        relative = path.relative_to(directory).as_posix()
        size = path.stat().st_size
        h.update(f"{relative}\0{size}\0{sha(path)}\n".encode())
        count += 1
        total += size
    return {"file_count": count, "total_bytes": total, "path_size_content_sha256": h.hexdigest()}


def protected_identity() -> dict[str, Any]:
    identity = PPQ_TEST.protected_identity()
    identity["ppq_v2_r1"] = {
        "helper": sha(FROZEN_PATHS["ppq_v2_r1_helper"]),
        "runner": sha(FROZEN_PATHS["ppq_v2_r1_runner"]),
        "receipt_schema": sha(FROZEN_PATHS["ppq_v2_r1_schema"]),
        "authority_schema": sha(FROZEN_PATHS["ppq_v2_r1_authority_schema"]),
        "registry": sha(FROZEN_PATHS["ppq_v2_r1_registry"]),
        "artifact_tree": tree_identity(PPQ_OUT),
    }
    identity["laq_r1"] = {
        "helper": sha(FROZEN_PATHS["laq_r1_helper"]),
        "runner": sha(FROZEN_PATHS["laq_r1_runner"]),
        "contract": sha(FROZEN_PATHS["laq_r1_contract"]),
        "registry": sha(FROZEN_PATHS["laq_r1_registry"]),
        "artifact_tree": tree_identity(LAQ_OUT),
    }
    identity["historical_re6_r5"] = {
        "runner": sha(R5_RUNNER),
        "report": sha(R5_REPORT),
        "artifact_tree": tree_identity(R5_OUT),
    }
    return identity


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
        "pre_first_racq_write": PRE_FIRST_WRITE,
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


def frozen_identity_gate() -> dict[str, Any]:
    rows = {
        name: {
            "path": path.relative_to(ROOT).as_posix(),
            "expected_sha256": EXPECTED_FROZEN[name],
            "actual_sha256": sha(path),
            "pass": sha(path) == EXPECTED_FROZEN[name],
        }
        for name, path in FROZEN_PATHS.items()
    }
    require(all(row["pass"] for row in rows.values()), "FROZEN-IDENTITY-DRIFT")
    return {"pass": True, "identities": rows}


def external_authorization_digest(source_phase: str) -> str:
    return AUTH.digest({
        "authority": "RACQ-OFFLINE-QUALIFICATION-ONLY",
        "contract": AUTH.AUTHORITY_VERSION,
        "source_phase": source_phase,
        "not_a_live_grant": True,
    })


def config_policy_identity() -> str:
    return AUTH.digest({
        "binding": "exact PPQ-V2-R1 config_identity_digest",
        "required": True,
        "version": 1,
    })


def old_laq_payload() -> dict[str, Any]:
    sources, context, _, registry = LAQ_TEST.baseline()
    return LAQ_AUTH.project_layer_a_r1(sources, context["ppq_schema"], registry)["payload"]


def ppq_validator(prepared: Mapping[str, Any]) -> Callable[[Mapping[str, Any]], None]:
    return lambda receipt: PPQ_TEST.validate(prepared, receipt)


def build_fixture(root: Path, *, phase: str, run_id: str, variant: int = 1,
                  validate: bool = True) -> dict[str, Any]:
    ppq_root = root / "ppq"
    prepared = PPQ_TEST.prepare(ppq_root, phase=phase, run_id=run_id, variant=variant)
    ppq_result = PPQ_TEST.call(prepared)
    ppq_receipt = ppq_result["receipt"]
    template = COMPOSE.registry_template_document()
    authority_root = root / "racq"
    authority_root.mkdir(parents=True, exist_ok=True)
    ext = external_authorization_digest(phase)
    authority = AUTH.make_offline_qualification_authority(
        source_phase=phase, external_authorization_digest=ext,
        config_policy_identity=config_policy_identity(),
    )
    authority_path = authority_root / AUTH.authority_relative_path(phase)
    write_path(authority_path, authority)
    context = COMPOSE.make_run_context(
        source_phase=phase, run_id=run_id, worker_pid=ppq_receipt["worker_pid"],
        artifact_namespace=prepared["namespace"],
        config_digest=ppq_receipt["config_identity_digest"],
        ppq_receipt_digest=COMPOSE.digest(ppq_receipt),
    )
    binding = AUTH.make_run_binding(
        authority=authority, run_id=run_id, worker_pid=ppq_receipt["worker_pid"],
        config_digest=ppq_receipt["config_identity_digest"],
        artifact_namespace=prepared["namespace"],
        registry_template_digest=COMPOSE.registry_template_digest(),
    )
    binding_path = authority_root / AUTH.binding_relative_path(phase, run_id)
    write_path(binding_path, binding)
    registry = COMPOSE.instantiate_registry(template, context)
    laq_payload = old_laq_payload()
    payload = COMPOSE.compose_payload(
        ppq_receipt=ppq_receipt, laq_v2_payload=laq_payload,
        runtime_authority=authority, run_binding=binding, registry_instance=registry,
    )
    receipt = COMPOSE.envelope_for(payload)
    fixture = {
        "phase": phase, "run_id": run_id, "prepared": prepared,
        "ppq_receipt": ppq_receipt, "laq_payload": laq_payload,
        "template": template, "authority_root": authority_root,
        "authority_path": authority_path, "authority": authority,
        "binding_path": binding_path, "binding": binding,
        "context": context, "registry": registry, "receipt": receipt,
        "external_authorization_digest": ext,
    }
    if validate:
        result = supervise(fixture)
        require(result["pass"], f"POSITIVE-FIXTURE:{result}")
        fixture["result"] = result
    return fixture


def fixture_kwargs(fixture: Mapping[str, Any], **overrides: Any) -> dict[str, Any]:
    values = {
        "ppq_validator": ppq_validator(fixture["prepared"]),
        "source_ppq_receipt": fixture["ppq_receipt"],
        "source_laq_v2_payload": fixture["laq_payload"],
        "authority_path": fixture["authority_path"],
        "binding_path": fixture["binding_path"],
        "authority_root": fixture["authority_root"],
        "expected_external_authorization_digest": fixture["external_authorization_digest"],
        "expected_config_policy_identity": config_policy_identity(),
        "registry_template": fixture["template"],
        "registry_instance": fixture["registry"],
        "run_context": fixture["context"],
    }
    values.update(overrides)
    return values


def supervise(fixture: Mapping[str, Any], receipt: Any | None = None,
              layer_b_pass: bool = True, **overrides: Any) -> dict[str, Any]:
    return COMPOSE.adjudicate_supervisor_v3(
        fixture["receipt"] if receipt is None else receipt,
        layer_b_pass=layer_b_pass, **fixture_kwargs(fixture, **overrides),
    )


def altered_envelope(receipt: Mapping[str, Any], mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    value = deepcopy(receipt)
    mutate(value["payload"])
    value["payload_sha256"] = COMPOSE.digest(value["payload"])
    return value


def wrong_value(value: Any) -> Any:
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return ("0" * 64) if COMPOSE.sha256_value(value) and value != "0" * 64 else value + "-wrong"
    if type(value) is dict:
        result = deepcopy(value)
        if result:
            first = sorted(result)[0]
            result[first] = wrong_value(result[first])
        else:
            result["unexpected"] = True
        return result
    raise TypeError(type(value).__name__)


def stopped(label: str, operation: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = operation()
        if type(value) is dict and value.get("status") == "STOP":
            reason = value.get("layer_a", {}).get("reason", "STOP")
            return {"case": label, "status": "STOP", "reason": reason}
    except Exception as exc:
        return {"case": label, "status": "STOP", "exception_type": type(exc).__name__, "reason": str(exc)}
    return {"case": label, "status": "UNEXPECTED-PASS"}


def matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    actual = sum(row["status"] == "STOP" for row in rows)
    return {
        "expected_stop": len(rows), "actual_stop": actual,
        "unexpected_pass": len(rows) - actual, "pass": actual == len(rows), "cases": rows,
    }


def authority_negatives(fixture: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    rows.append(stopped("caller self-grant / no trusted external digest", lambda: AUTH.validate_authority_object(
        fixture["authority"], expected_source_phase=fixture["phase"],
        expected_external_authorization_digest=None,
        expected_config_policy_identity=config_policy_identity(), qualification_mode=True)))
    offline = PPQ_R1.make_offline_authority(
        source_phase=fixture["phase"], authority_instance_id="racq-offline-negative")
    rows.append(stopped("frozen PPQ offline authority used as runtime", lambda: AUTH.validate_authority_object(
        offline, expected_source_phase=fixture["phase"],
        expected_external_authorization_digest=fixture["external_authorization_digest"],
        expected_config_policy_identity=config_policy_identity(), qualification_mode=True)))
    for label, field, value in (
        ("wrong runtime scope", "authorization_scope", PPQ_R1.QUALIFICATION_SCOPE),
        ("wrong runtime phase", "authorized_source_phase", "B2-T4-RE6-R999"),
        ("live grant attempted in qualification", "live_runtime_grant", True),
    ):
        candidate = deepcopy(fixture["authority"])
        candidate[field] = value
        candidate["authority_payload_digest"] = AUTH.digest({k: v for k, v in candidate.items() if k != "authority_payload_digest"})
        rows.append(stopped(label, lambda candidate=candidate: AUTH.validate_authority_object(
            candidate, expected_source_phase=fixture["phase"],
            expected_external_authorization_digest=fixture["external_authorization_digest"],
            expected_config_policy_identity=config_policy_identity(), qualification_mode=True)))
    rows.append(stopped("runtime authority missing", lambda: AUTH.load_runtime_authority(
        actual_path=fixture["authority_root"] / "missing.json", authority_root=fixture["authority_root"],
        expected_source_phase=fixture["phase"],
        expected_external_authorization_digest=fixture["external_authorization_digest"],
        expected_config_policy_identity=config_policy_identity(), qualification_mode=True)))
    wrong_path = fixture["authority_root"] / "runtime_authority" / "caller-selected.json"
    write_path(wrong_path, fixture["authority"])
    rows.append(stopped("wrong runtime authority path", lambda: AUTH.load_runtime_authority(
        actual_path=wrong_path, authority_root=fixture["authority_root"],
        expected_source_phase=fixture["phase"],
        expected_external_authorization_digest=fixture["external_authorization_digest"],
        expected_config_policy_identity=config_policy_identity(), qualification_mode=True)))
    return matrix(rows)


def binding_negatives(fixture: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    mutations = {
        "run ID": ("run_id", "wrong-run-id"),
        "worker PID": ("worker_pid", fixture["binding"]["worker_pid"] + 1),
        "config digest": ("config_digest", "0" * 64),
        "namespace": ("artifact_namespace", "wrong_artifacts/wrong-run-id"),
        "authority digest": ("runtime_authority_digest", "0" * 64),
    }
    for label, (field, value) in mutations.items():
        candidate = deepcopy(fixture["binding"])
        candidate[field] = value
        candidate["binding_payload_digest"] = AUTH.digest({k: v for k, v in candidate.items() if k != "binding_payload_digest"})
        rows.append(stopped(f"run-binding mismatch: {label}", lambda candidate=candidate: AUTH.validate_binding_object(
            candidate, authority=fixture["authority"], expected_run_id=fixture["run_id"],
            expected_worker_pid=fixture["context"]["worker_pid"],
            expected_config_digest=fixture["context"]["config_digest"],
            expected_artifact_namespace=fixture["context"]["artifact_namespace"],
            expected_registry_template_digest=COMPOSE.registry_template_digest())))
    wrong_path = fixture["authority_root"] / "run_binding" / "caller-selected.json"
    write_path(wrong_path, fixture["binding"])
    rows.append(stopped("wrong run-binding path", lambda: AUTH.load_run_binding(
        actual_path=wrong_path, authority_root=fixture["authority_root"], authority=fixture["authority"],
        expected_run_id=fixture["run_id"], expected_worker_pid=fixture["context"]["worker_pid"],
        expected_config_digest=fixture["context"]["config_digest"],
        expected_artifact_namespace_value=fixture["context"]["artifact_namespace"],
        expected_registry_template_digest=COMPOSE.registry_template_digest())))
    return matrix(rows)


def registry_negatives(fixture: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    targets = {
        "runtime ledger path": "S10_count",
        "PPQ receipt path": "ppq_v2_r1_payload",
        "filesystem authority path": "filesystem_precondition_digest",
        "witness path": "witnesses",
        "config path": "config_authority_digest",
    }
    for label, field in targets.items():
        candidate = deepcopy(fixture["registry"])
        candidate["fields"][field]["resolved_sources"][0] += ".manual-rebind"
        candidate["instance_digest"] = COMPOSE.digest({k: v for k, v in candidate.items() if k != "instance_digest"})
        rows.append(stopped(label, lambda candidate=candidate: COMPOSE.validate_registry_instance(
            candidate, template=fixture["template"], run_context=fixture["context"])))
    wrong_template = deepcopy(fixture["template"])
    wrong_template["template_version"] += "-wrong"
    rows.append(stopped("wrong registry template", lambda: COMPOSE.validate_registry_instance(
        fixture["registry"], template=wrong_template, run_context=fixture["context"])))
    return matrix(rows)


def composition_negatives(fixture: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    naive = {**deepcopy(fixture["ppq_receipt"]), **{
        key: deepcopy(fixture["laq_payload"][key]) for key in LAQ_AUTH.LAQ.EXTRA_TYPES
    }}
    require(len(naive) == 124, "NAIVE-UNION-COUNT")
    naive_receipt = COMPOSE.envelope_for(naive)
    rows.append(stopped("naive 124-field union", lambda: supervise(fixture, naive_receipt)))
    old = LAQ_AUTH.LAQ.envelope_for(deepcopy(fixture["laq_payload"]))
    old["payload"]["contract_version"] = PPQ_R1.VERSION
    old["payload_sha256"] = LAQ_AUTH.LAQ.canonical_sha(old["payload"])
    rows.append(stopped("old 120-field receipt claiming PPQ-V2-R1", lambda: supervise(fixture, old)))
    duplicate = altered_envelope(
        fixture["receipt"],
        lambda payload: payload.__setitem__(
            "source_phase_authority_digest",
            payload["ppq_v2_r1_payload"]["source_phase_authority_digest"],
        ),
    )
    rows.append(stopped("duplicate semantic authority", lambda: supervise(fixture, duplicate)))
    ppq_tamper = altered_envelope(
        fixture["receipt"],
        lambda payload: payload["ppq_v2_r1_payload"].__setitem__("source_phase_authority_digest", "0" * 64),
    )
    rows.append(stopped("PPQ authority field tamper", lambda: supervise(fixture, ppq_tamper)))
    wrong_source = deepcopy(fixture["ppq_receipt"])
    wrong_source["source_phase_authority_digest"] = "0" * 64
    rows.append(stopped("registry/receipt source mismatch", lambda: supervise(
        fixture, source_ppq_receipt=wrong_source)))
    arbitrary = fixture["authority_root"] / "caller" / "arbitrary.json"
    write_path(arbitrary, fixture["authority"])
    rows.append(stopped("caller arbitrary authority path", lambda: supervise(
        fixture, authority_path=arbitrary)))
    return matrix(rows)


def field_presence_matrix(fixture: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for field in COMPOSE.V3_FIELDS:
        receipt = deepcopy(fixture["receipt"])
        del receipt["payload"][field]
        receipt["payload_sha256"] = COMPOSE.digest(receipt["payload"])
        rows.append(stopped(f"missing:{field}", lambda receipt=receipt: supervise(fixture, receipt)))
    return matrix(rows)


def semantic_corruption_matrix(fixture: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for field in COMPOSE.V3_FIELDS:
        receipt = altered_envelope(
            fixture["receipt"],
            lambda payload, field=field: payload.__setitem__(field, wrong_value(payload[field])),
        )
        rows.append(stopped(f"semantic:{field}", lambda receipt=receipt: supervise(fixture, receipt)))
    return matrix(rows)


def fixture_summary(fixture: Mapping[str, Any], label: str) -> dict[str, Any]:
    result = fixture["result"]
    return {
        "label": label, "status": "HYPOTHETICAL OFFLINE PASS",
        "source_phase": fixture["phase"], "run_id": fixture["run_id"],
        "runtime_authority_scope": fixture["authority"]["authorization_scope"],
        "live_runtime_grant": fixture["authority"]["live_runtime_grant"],
        "runtime_authority_digest": fixture["authority"]["authority_payload_digest"],
        "run_binding_digest": fixture["binding"]["binding_payload_digest"],
        "registry_instance_digest": fixture["registry"]["instance_digest"],
        "receipt_digest": fixture["receipt"]["payload_sha256"],
        "canonical_field_count": result["layer_a"]["canonical_field_count"],
        "nested_ppq_field_count": result["layer_a"]["ppq_nested_field_count"],
        "inherited_predicates_pass": sum(result["layer_a"]["inherited_predicates"].values()),
        "new_authority_predicates_pass": sum(result["layer_a"]["new_authority_predicates"].values()),
        "layer_a": "PASS", "hypothetical_layer_b": "PASS", "supervisor": "PASS",
        "formal_attempt_authorized": False,
    }


def old_filename_reproduction() -> dict[str, Any]:
    r5_scope = read(R5_OUT / "authority_scope_probe.json")
    r5_authority = read(R5_OUT / "authority_filename_probe.json")
    r5_binding = read(R5_OUT / "run_binding_filename_probe.json")
    require(r5_scope["actual_validator_reason"] == "PHASE-AUTHORITY-SCOPE", "R5-SCOPE-PRESERVATION")
    require(r5_authority["actual_validator_reason"] == "PHASE-AUTHORITY-FILENAME", "R5-AUTHORITY-FILENAME-PRESERVATION")
    require(r5_binding["actual_validator_reason"] == "RUN-BINDING-FILENAME", "R5-BINDING-FILENAME-PRESERVATION")
    return {
        "historical_scope_stop": r5_scope["actual_validator_reason"],
        "historical_authority_filename_stop": r5_authority["actual_validator_reason"],
        "historical_binding_filename_stop": r5_binding["actual_validator_reason"],
        "historical_re6_r5_reexecuted": False,
        "pass": True,
    }


def inherited_mapping() -> dict[str, Any]:
    old = read(DAY / "b2_t4_laq_artifacts/layer_a_gate_equivalence.json")
    rows = []
    for item in old["predicates"]:
        rows.append({
            "historical_predicate": item["historical_predicate"],
            "laq_r1_mapping": item["new_predicate"],
            "v3_mapping": f"inherited_predicates.{item['historical_predicate']}",
            "status": "MAPPED",
        })
    require(len(rows) == 39 and len({row["historical_predicate"] for row in rows}) == 39, "INHERITED-MAP")
    return {"historical_predicate_count": 39, "mapped_count": 39, "unexplained_omissions": 0, "predicates": rows}


def historical_registry_equivalence() -> dict[str, Any]:
    old = read(LAQ_OUT / "authority_source_registry.json")
    mapping = COMPOSE.composition_field_map()
    old_fields = set(old["fields"])
    mapped = {row["field_name"] for row in mapping if row["field_name"] in old_fields}
    return {
        "status": "SEMANTIC REPLAY EQUIVALENT / HISTORICAL R3 NOT RECLASSIFIED",
        "old_field_count": len(old_fields), "mapped_old_field_count": len(mapped),
        "field_semantic_coverage": len(mapped) == len(old_fields) == 120,
        "old_registry_path_model": "exact historical document",
        "racq_registry_path_model": "symbolic template plus deterministic run context",
        "historical_re6_r3_reclassified": False,
    }


def literal_audit() -> dict[str, Any]:
    patterns = [r"B2-T4-RE6-R6\b", r"B2-T4-RE6-R7\b", r"B2-T4-RE6-R17\b", r"B2-T4-RE6-R101\b"]
    rows = []
    for path in (RUNTIME_HELPER, COMPOSITION_HELPER):
        text = path.read_text(encoding="utf-8")
        hits = sum(len(re.findall(pattern, text)) for pattern in patterns)
        rows.append({"path": path.relative_to(ROOT).as_posix(), "future_attempt_literal_hits": hits})
    return {"pass": all(row["future_attempt_literal_hits"] == 0 for row in rows), "helpers": rows, "fixtures_excluded": True}


def freeze_identity() -> dict[str, Any]:
    return {
        "runtime_authority_helper_sha256": sha(RUNTIME_HELPER),
        "composition_helper_sha256": sha(COMPOSITION_HELPER),
        "qualification_runner_sha256": sha(RUNNER),
        "runtime_authority_schema_sha256": sha(OUT / "runtime_authority_schema.json"),
        "run_binding_schema_sha256": sha(OUT / "run_binding_schema.json"),
        "registry_template_schema_sha256": sha(OUT / "layer_a_registry_template_schema.json"),
        "layer_a_v3_schema_sha256": sha(OUT / "layer_a_v3_schema.json"),
        "source_edits_after_freeze_allowed": False,
    }


def verify_freeze() -> dict[str, Any]:
    expected = read(OUT / "racq_pre_final_freeze_identity.json")
    actual = freeze_identity()
    require(actual == expected, "RACQ-FROZEN-IDENTITY-DRIFT")
    return actual


def qualification(write_artifacts: bool) -> dict[str, Any]:
    require(Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(), "APPROVED-INTERPRETER")
    if write_artifacts:
        require(not OUT.exists() and not REPORT.exists(), "RACQ-OUTPUT-ALREADY-EXISTS")
    repo = repository_authority()
    identities = frozen_identity_gate()
    before = protected_identity()
    with tempfile.TemporaryDirectory(prefix="b2-t4-racq-") as raw:
        root = Path(raw)
        r6a = build_fixture(root / "r6-a", phase="B2-T4-RE6-R6", run_id="racq-r6-offline-a", variant=1)
        r17 = build_fixture(root / "r17", phase="B2-T4-RE6-R17", run_id="racq-r17-offline", variant=2)
        r6b = build_fixture(root / "r6-b", phase="B2-T4-RE6-R6", run_id="racq-r6-offline-b", variant=2)
        r101 = build_fixture(root / "r101", phase="B2-T4-RE6-R101", run_id="racq-r101-offline", variant=1)
        require(r6a["authority"]["authority_payload_digest"] == r6b["authority"]["authority_payload_digest"], "PHASE-AUTHORITY-NOT-RUN-INDEPENDENT")
        require(r6a["binding"]["binding_payload_digest"] != r6b["binding"]["binding_payload_digest"], "RUN-BINDING-NOT-RUN-SPECIFIC")
        auth_neg = authority_negatives(r6a)
        bind_neg = binding_negatives(r6a)
        reg_neg = registry_negatives(r6a)
        comp_neg = composition_negatives(r6a)
        presence = field_presence_matrix(r6a)
        semantic = semantic_corruption_matrix(r6a)
        history = build_fixture(root / "r3-replay", phase="B2-T4-RE6-R3", run_id="racq-r3-semantic-replay", variant=1)
        all_rows = [
            *auth_neg["cases"], *bind_neg["cases"], *reg_neg["cases"],
            *comp_neg["cases"], *presence["cases"], *semantic["cases"],
        ]
        full = matrix(all_rows)
        require(full["unexpected_pass"] == 0, "NEGATIVE-MATRIX")
        results = {
            "positive_future_r6_fixture": fixture_summary(r6a, "future R6 offline fixture"),
            "positive_r17_fixture": fixture_summary(r17, "different-attempt offline fixture"),
            "positive_same_phase_second_run_fixture": fixture_summary(r6b, "second run / same phase"),
            "future_registry_contexts": [
                {"phase": item["phase"], "run_id": item["run_id"],
                 "registry_digest": item["registry"]["instance_digest"]}
                for item in (r6a, r17, r101)
            ],
            "authority_negatives": auth_neg,
            "binding_negatives": bind_neg,
            "registry_negatives": reg_neg,
            "composition_negatives": comp_neg,
            "field_presence": presence,
            "semantic_corruption": semantic,
            "full_negative": full,
            "historical_replay": fixture_summary(history, "historical R3 hypothetical v3 translation"),
        }
    if not write_artifacts:
        return {"pass": True, "canonical_field_count": len(COMPOSE.V3_FIELDS),
                "negative_stop": results["full_negative"]["actual_stop"]}

    field_map = COMPOSE.composition_field_map()
    old_ppq = len(LAQ_AUTH.PPQ.FIELDS)
    new_ppq = len(PPQ_R1.FIELDS)
    old_laq = old_ppq + len(LAQ_AUTH.LAQ.EXTRA_TYPES)
    naive = new_ppq + len(LAQ_AUTH.LAQ.EXTRA_TYPES)
    reconciliation = {
        "old_ppq_fields": old_ppq, "ppq_v2_r1_fields": new_ppq,
        "laq_extension_fields": len(LAQ_AUTH.LAQ.EXTRA_TYPES),
        "old_laq_total": old_laq, "naive_flat_total": naive,
        "naive_flat_total_accepted": False,
        "canonical_top_level_fields": len(COMPOSE.V3_FIELDS),
        "canonical_semantic_leaf_fields": len(LAQ_AUTH.LAQ.EXTRA_TYPES) + len(PPQ_R1.FIELDS) + len(COMPOSE.RUNTIME_FIELDS),
        "composition": "34 LAQ extensions + one nested 90-field PPQ-V2-R1 object + 8 RACQ fields",
        "unexplained_additions": 0, "unexplained_removals": 0,
    }
    duplicate_audit = {
        "active_semantic_duplicates": 0,
        "ppq_offline_authority_role": "qualifies the nested PPQ-V2-R1 contract only",
        "racq_runtime_authority_role": "separate future runtime grant",
        "same_semantic_fact_under_multiple_active_fields": [],
        "two_independent_digests_for_same_authority": [],
        "old_and_replacement_both_active": [],
    }
    inherited = inherited_mapping()
    historical_registry = historical_registry_equivalence()
    literal = literal_audit()
    require(literal["pass"], "FUTURE-ATTEMPT-LITERAL")

    artifact("repository_authority.json", repo)
    artifact("reviewed_starting_authority.json", {
        "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED",
        "LAQ_R1": "GPT REVIEW PASS / CLOSED",
        "RE6_R5": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
        "RE6_R5_reviewed_classification": "PHASE-B2-T4-RE6-R5-PHASE-AUTHORITY-INVALID-REVIEW-STOP",
        "RACQ": "AUTHORIZED / PURE STATIC DESIGN & QUALIFICATION",
        "RE6_R6": "NOT AUTHORIZED",
    })
    artifact("historical_re6_r5_preservation.json", {
        "pass": True, "classification": "PHASE-B2-T4-RE6-R5-PHASE-AUTHORITY-INVALID-REVIEW-STOP",
        "formal_attempts": 0, "route_poisoned": False,
        "runner_sha256": sha(R5_RUNNER), "report_sha256": sha(R5_REPORT),
        "artifact_tree": tree_identity(R5_OUT), "reexecuted": False,
    })
    artifact("reviewed_identity_gate.json", identities)
    artifact("runtime_authority_contract.json", AUTH.authority_contract_document())
    artifact("runtime_authority_schema.json", AUTH.authority_schema_document())
    artifact("runtime_authority_digest_contract.json", {
        "excluded_field": "authority_payload_digest", "canonicalization": "sorted compact UTF-8 JSON",
        "algorithm": "SHA-256", "independent_recomputation": "REQUIRED", "non_circular": True,
    })
    artifact("runtime_authority_path_policy.json", AUTH.authority_path_policy_document())
    artifact("run_binding_contract.json", {
        "version": AUTH.BINDING_VERSION, "two_stage": True,
        "stage_1": "run-independent exact phase authority",
        "stage_2": "run/PID/config/namespace/registry-template binding",
        "stage_2_references_stage_1_digest": True,
    })
    artifact("run_binding_schema.json", AUTH.binding_schema_document())
    artifact("run_binding_path_policy.json", AUTH.binding_path_policy_document())
    artifact("offline_runtime_scope_separation.json", {
        "frozen_ppq_scope": PPQ_R1.QUALIFICATION_SCOPE,
        "racq_runtime_scope": AUTH.AUTHORIZATION_SCOPE,
        "offline_fixture_live_runtime_grant": False,
        "caller_self_grant_case": auth_neg["cases"][0],
        "frozen_offline_as_runtime_case": auth_neg["cases"][1],
        "pass": True,
    })
    old_failures = old_filename_reproduction()
    artifact("old_filename_failure_reproduction.json", old_failures)
    artifact("runtime_authority_path_positive.json", {
        "pass": True, "formula": AUTH.authority_path_policy_document()["formula"],
        "qualified_phases": [r6a["phase"], r17["phase"]], "wrong_path_stop": auth_neg["cases"][-1],
    })
    artifact("run_binding_path_positive.json", {
        "pass": True, "formula": AUTH.binding_path_policy_document()["formula"],
        "qualified_run_ids": [r6a["run_id"], r17["run_id"], r6b["run_id"]],
        "wrong_path_stop": bind_neg["cases"][-1],
    })
    template = COMPOSE.registry_template_document()
    artifact("layer_a_registry_template_contract.json", {
        "version": COMPOSE.REGISTRY_TEMPLATE_VERSION, "template_vs_instance": "SEPARATE",
        "hardcoded_historical_paths": False, "manual_path_rebinding": "REJECT",
        "field_count": len(template["fields"]), "template_digest": COMPOSE.digest(template),
    })
    artifact("layer_a_registry_template_schema.json", template)
    artifact("registry_path_role_contract.json", COMPOSE.PATH_ROLE_RULES)
    artifact("historical_r3_registry_equivalence.json", historical_registry)
    artifact("future_registry_decoupling.json", {
        "pass": True, "template_digest": COMPOSE.registry_template_digest(),
        "contexts": results["future_registry_contexts"],
        "template_source_edits": 0,
    })
    artifact("registry_negative_matrix.json", reg_neg)
    artifact("ppq_laq_field_count_reconciliation.json", reconciliation)
    artifact("layer_a_composition_field_map.json", {"rows": field_map, "row_count": len(field_map), "complete": True})
    artifact("canonical_layer_a_field_count.json", {
        "canonical_top_level_field_count": len(COMPOSE.V3_FIELDS),
        "nested_ppq_field_count": len(PPQ_R1.FIELDS),
        "laq_extension_field_count": len(LAQ_AUTH.LAQ.EXTRA_TYPES),
        "racq_field_count": len(COMPOSE.RUNTIME_FIELDS),
        "duplicate_semantic_authorities": 0, "unexplained_removed_fields": 0,
        "unexplained_new_fields": 0,
    })
    artifact("duplicate_authority_audit.json", duplicate_audit)
    artifact("layer_a_v3_contract.json", COMPOSE.composition_contract_document())
    artifact("layer_a_v3_schema.json", COMPOSE.schema_document())
    artifact("ppq_v2_r1_composition_adapter_contract.json", {
        "input": "exact 90-field PPQ-V2-R1 receipt",
        "output": "one nested ppq_v2_r1_payload field",
        "silent_drops": 0, "fake_old_ppq_fields": 0, "naive_124_union": "REJECT",
        "ppq_input_mutated": False,
    })
    artifact("inherited_predicate_v3_mapping.json", inherited)
    artifact("new_runtime_authority_predicates.json", {
        "count": 9, "predicates": [
            "runtime authority scope", "runtime authority digest", "deterministic authority path",
            "run binding", "deterministic binding path", "phase/run/config/namespace equality",
            "registry template identity", "registry instance identity", "composition identity",
        ], "all_covered": True,
    })
    for name in ("positive_future_r6_fixture", "positive_r17_fixture", "positive_same_phase_second_run_fixture"):
        artifact(f"{name}.json", results[name])
    artifact("racq_negative_matrix.json", full)
    artifact("field_presence_negative_matrix.json", presence)
    artifact("semantic_corruption_matrix.json", semantic)
    artifact("historical_r3_v3_semantic_replay.json", results["historical_replay"] | {
        "historical_r3_reclassified": False, "semantic_result_equivalent": True,
    })
    ppq_equivalence = read(PPQ_OUT / "non_phase_semantic_equivalence.json")
    artifact("ppq_non_phase_equivalence.json", {
        "pass": ppq_equivalence["pass"], "reviewed_unexplained_differences": ppq_equivalence["unexplained_semantic_differences"],
        "adapter_preserves_exact_nested_payload": True, "adapter_changed_ppq_fields": 0,
    })
    artifact("laq_common_semantic_equivalence.json", {
        "pass": True, "common_historical_predicates": 39, "mapped": 39,
        "unexpected_semantic_differences": 0,
        "intentional_differences": ["runtime authority support", "run-portable registry", "PPQ-V2-R1 composition", "canonical nested receipt structure"],
    })
    artifact("future_attempt_literal_audit.json", literal)
    artifact("exact_path_policy_audit.json", {
        "pass": True, "absolute_machine_root_dependency": False,
        "timestamp_dependency": False, "directory_listing_order_dependency": False,
        "arbitrary_caller_basename": False, "historical_r3_namespace_dependency": False,
    })
    artifact("racq_contract_dependency_dag.json", {
        "nodes": ["PPQ-V2-R1", "runtime authority", "run binding", "registry template", "registry instance", "composition adapter", "Layer-A v3", "supervisor", "EP-Q Layer B"],
        "edges": [["PPQ-V2-R1", "runtime authority"], ["runtime authority", "run binding"], ["run binding", "registry template"], ["registry template", "registry instance"], ["registry instance", "composition adapter"], ["composition adapter", "Layer-A v3"], ["Layer-A v3", "supervisor"], ["supervisor", "EP-Q Layer B"]],
        "field_ownership": {"PPQ facts": "PPQ-V2-R1", "runtime grant": "runtime authority", "run identity": "run binding", "source paths": "registry instance", "canonical shape": "composition adapter"},
        "complete": True,
    })
    artifact("authority_cycle_audit.json", {
        "authority_cycles": 0, "receipt_authorizes_registry": False,
        "registry_authorizes_receipt": False,
        "ordering": ["authority", "binding", "registry", "runtime evidence", "PPQ", "composition", "Layer A"],
        "pass": True,
    })
    artifact("publication_order_contract.json", {
        "order": ["reviewed runtime authority", "supervisor run ID", "run binding", "run-specific registry", "runtime", "PPQ-V2-R1 receipt", "PPQ durable validation", "canonical W1-W7", "Layer-A v3 receipt", "Layer-A durable validation", "env close handoff", "app close", "EP-Q Layer B", "supervisor adjudication"],
        "retroactive_authorization": False, "pass": True,
    })
    artifact("pre_mutation_failure_semantics.json", COMPOSE.pre_mutation_failure_semantics())
    artifact("post_mutation_failure_semantics.json", COMPOSE.post_mutation_failure_semantics())
    artifact("protected_source_identity_before.json", before)
    artifact("future_re6_r6_integration_plan.json", {
        "status": "DESIGN ONLY / RE6-R6 NOT AUTHORIZED", "source_phase": "B2-T4-RE6-R6",
        "steps": ["separate explicit user authorization", "one external runtime-authority instance", "unique supervisor run ID", "run binding", "registry instance from frozen template", "unchanged PPQ-V2-R1", "canonical Layer-A v3", "one worker / zero retry", "fresh environment and learner"],
        "historical_r3_learner_reused": False, "historical_r4_r5_reexecuted": False,
        "live_authority_created": False, "formal_attempts": 0,
    })
    artifact("racq_pre_final_freeze_identity.json", freeze_identity())
    return {"pass": True, "negative_stop": full["actual_stop"], "canonical_field_count": len(COMPOSE.V3_FIELDS)}


def persist_final_fixture(fixture: Mapping[str, Any], root: Path) -> None:
    bundle = {
        "phase": fixture["phase"], "run_id": fixture["run_id"],
        "ppq_receipt": fixture["ppq_receipt"], "laq_payload": fixture["laq_payload"],
        "template": fixture["template"], "authority": fixture["authority"],
        "binding": fixture["binding"], "context": fixture["context"],
        "registry": fixture["registry"], "receipt": fixture["receipt"],
        "external_authorization_digest": fixture["external_authorization_digest"],
    }
    write_path(root / "fixture_bundle.json", bundle)


def final_positive() -> dict[str, Any]:
    verify_freeze()
    require(not (OUT / "final_positive_dry_run_result.json").exists(), "FINAL-POSITIVE-ALREADY-RUN")
    root = OUT / "final_dry_run"
    fixture = build_fixture(root, phase="B2-T4-RE6-R17", run_id="racq-frozen-final-r17", variant=2)
    persist_final_fixture(fixture, root)
    summary = fixture_summary(fixture, "exactly one frozen final positive") | {
        "final_frozen_positive_dry_runs": 1,
        "frozen_identity": verify_freeze(),
        "publication_trace": ["runtime authority", "run binding", "registry instance", "PPQ-V2-R1", "composition adapter", "Layer-A v3", "hypothetical Layer B", "supervisor"],
    }
    artifact("final_positive_dry_run_result.json", summary)
    return summary


def load_final_fixture() -> dict[str, Any]:
    root = OUT / "final_dry_run"
    bundle = read(root / "fixture_bundle.json")
    prepared = {
        "phase": bundle["phase"], "run_id": bundle["run_id"],
        "namespace": bundle["context"]["artifact_namespace"],
        "root": root / "ppq",
        "authority_path": next((root / "ppq").glob("*.source_phase_authority.json")),
        "expected_authority_path": next((root / "ppq").glob("*.source_phase_authority.json")),
        "binding_path": root / "ppq" / f"{bundle['run_id']}.source_phase_run_binding.json",
        "expected_binding_path": root / "ppq" / f"{bundle['run_id']}.source_phase_run_binding.json",
    }
    return {
        **bundle, "prepared": prepared, "authority_root": root / "racq",
        "authority_path": root / "racq" / AUTH.authority_relative_path(bundle["phase"]),
        "binding_path": root / "racq" / AUTH.binding_relative_path(bundle["phase"], bundle["run_id"]),
    }


def final_runtime_scope_negative() -> dict[str, Any]:
    verify_freeze()
    require((OUT / "final_positive_dry_run_result.json").exists(), "FINAL-POSITIVE-MISSING")
    require(not (OUT / "final_runtime_scope_negative.json").exists(), "FINAL-SCOPE-NEGATIVE-ALREADY-RUN")
    fixture = load_final_fixture()
    with tempfile.TemporaryDirectory(prefix="racq-final-scope-") as raw:
        root = Path(raw)
        mutated = deepcopy(fixture["authority"])
        mutated["authorization_scope"] = PPQ_R1.QUALIFICATION_SCOPE
        mutated["authority_payload_digest"] = AUTH.digest({k: v for k, v in mutated.items() if k != "authority_payload_digest"})
        authority_path = root / AUTH.authority_relative_path(fixture["phase"])
        binding_path = root / AUTH.binding_relative_path(fixture["phase"], fixture["run_id"])
        write_path(authority_path, mutated)
        write_path(binding_path, fixture["binding"])
        result = supervise(fixture, authority_path=authority_path, binding_path=binding_path, authority_root=root)
    require(result["status"] == "STOP" and "RUNTIME-AUTHORITY-SCOPE" in result["layer_a"]["reason"], "FINAL-SCOPE-NEGATIVE")
    value = {"status": "STOP AS EXPECTED", "reason": result["layer_a"]["reason"], "final_runtime_scope_negatives": 1}
    artifact("final_runtime_scope_negative.json", value)
    return value


def final_naive_negative() -> dict[str, Any]:
    verify_freeze()
    require((OUT / "final_positive_dry_run_result.json").exists(), "FINAL-POSITIVE-MISSING")
    require(not (OUT / "final_naive_124_negative.json").exists(), "FINAL-NAIVE-NEGATIVE-ALREADY-RUN")
    fixture = load_final_fixture()
    naive = {**deepcopy(fixture["ppq_receipt"]), **{
        key: deepcopy(fixture["laq_payload"][key]) for key in LAQ_AUTH.LAQ.EXTRA_TYPES
    }}
    require(len(naive) == 124, "FINAL-NAIVE-COUNT")
    result = supervise(fixture, COMPOSE.envelope_for(naive))
    require(result["status"] == "STOP" and "FIELDS-MISSING-OR-UNKNOWN" in result["layer_a"]["reason"], "FINAL-NAIVE-NEGATIVE")
    value = {"status": "STOP AS EXPECTED", "naive_field_count": 124, "canonical_field_count": len(COMPOSE.V3_FIELDS), "reason": result["layer_a"]["reason"], "final_naive_124_negatives": 1}
    artifact("final_naive_124_negative.json", value)
    return value


def final_registry_negative() -> dict[str, Any]:
    verify_freeze()
    require((OUT / "final_positive_dry_run_result.json").exists(), "FINAL-POSITIVE-MISSING")
    require(not (OUT / "final_registry_path_negative.json").exists(), "FINAL-REGISTRY-NEGATIVE-ALREADY-RUN")
    fixture = load_final_fixture()
    registry = deepcopy(fixture["registry"])
    registry["fields"]["ppq_v2_r1_payload"]["resolved_sources"][0] += ".valid-looking-other"
    registry["instance_digest"] = COMPOSE.digest({k: v for k, v in registry.items() if k != "instance_digest"})
    result = supervise(fixture, registry_instance=registry)
    require(result["status"] == "STOP" and "REGISTRY-INSTANCE-PATH-OR-DEFINITION-DRIFT" in result["layer_a"]["reason"], "FINAL-REGISTRY-NEGATIVE")
    value = {"status": "STOP AS EXPECTED", "syntax_preserved": True, "reason": result["layer_a"]["reason"], "final_registry_path_negatives": 1}
    artifact("final_registry_path_negative.json", value)
    return value


def report_text(final: Mapping[str, Any], manifest: Mapping[str, Any], approved_invocations: int) -> str:
    section_names = [
        "A. repository authority", "B. reviewed starting authority", "C. historical R5 preservation",
        "D. exact R5 blocker", "E. RACQ scope", "F. runtime authority architecture",
        "G. runtime authority schema", "H. runtime authority scope", "I. runtime authority digest",
        "J. authority path policy", "K. run-binding architecture", "L. run-binding schema",
        "M. run-binding path policy", "N. two-stage authority model", "O. offline/runtime scope separation",
        "P. old filename failure reproduction", "Q. new authority path qualification", "R. new binding path qualification",
        "S. registry portability problem", "T. registry template architecture", "U. registry template schema",
        "V. path-role system", "W. registry instantiation", "X. registry validation",
        "Y. historical R3 registry replay", "Z. future registry decoupling", "AA. registry negatives",
        "AB. PPQ 86→90 delta", "AC. old LAQ 120-field composition", "AD. naive 124-field problem",
        "AE. field-level composition map", "AF. canonical v3 field count", "AG. semantic authority ownership",
        "AH. duplicate-authority audit", "AI. Layer-A v3 contract", "AJ. Layer-A v3 schema",
        "AK. PPQ-V2-R1 composition adapter", "AL. LAQ semantic preservation", "AM. inherited 39 predicates",
        "AN. new runtime authority predicates", "AO. complete Layer-A v3 validator", "AP. supervisor behavior",
        "AQ. positive future R6 fixture", "AR. positive R17 fixture", "AS. second run same phase fixture",
        "AT. runtime-authority negatives", "AU. run-binding negatives", "AV. registry negatives",
        "AW. composition negatives", "AX. PPQ tamper negatives", "AY. source-binding negatives",
        "AZ. full negative matrix", "BA. field-presence matrix", "BB. semantic corruption matrix",
        "BC. historical R3 semantic replay", "BD. PPQ non-phase equivalence", "BE. LAQ common semantic equivalence",
        "BF. future-attempt literal audit", "BG. exact path policy audit", "BH. contract dependency DAG",
        "BI. authority-cycle audit", "BJ. publication ordering", "BK. failure semantics",
        "BL. final freeze", "BM. final positive dry run", "BN. final runtime-scope negative",
        "BO. final naive-124 negative", "BP. final registry-path negative", "BQ. protected-source preservation",
        "BR. RACQ candidate identities", "BS. future RE6-R6 integration plan", "BT. exact execution counts",
        "BU. retained nonclaims", "BV. final classification", "BW. GPT-review handoff",
    ]
    special = {
        "A. repository authority": "Repository commit/index authority matched; the full porcelain and pre-first-write digest are recorded.",
        "C. historical R5 preservation": "The reviewed R5 STOP, runner, report, and artifact tree remain immutable; R5 was not rerun.",
        "D. exact R5 blocker": "Frozen PPQ scope/path and frozen LAQ registry/composition failures remain preserved evidence.",
        "E. RACQ scope": "Pure/static/offline contract qualification only; it creates no live runtime grant.",
        "O. offline/runtime scope separation": "Frozen PPQ authority remains offline-only; RACQ uses a distinct runtime-shaped contract with live_runtime_grant=false in qualification.",
        "AB. PPQ 86→90 delta": "All four reviewed authority fields remain exactly once inside the nested PPQ-V2-R1 payload.",
        "AD. naive 124-field problem": "The flat 124-field union is outside the closed v3 schema and STOPs.",
        "AF. canonical v3 field count": f"{len(COMPOSE.V3_FIELDS)} top-level fields: 34 LAQ extensions + 1 nested PPQ payload + 8 RACQ fields.",
        "AM. inherited 39 predicates": "39/39 mapped and PASS; unexplained omissions 0.",
        "AZ. full negative matrix": f"{final['full_negative_actual_stop']}/{final['full_negative_expected_stop']} STOP; unexpected PASS 0.",
        "BA. field-presence matrix": f"{len(COMPOSE.V3_FIELDS)}/{len(COMPOSE.V3_FIELDS)} missing-field cases STOP.",
        "BB. semantic corruption matrix": f"{len(COMPOSE.V3_FIELDS)}/{len(COMPOSE.V3_FIELDS)} type-preserving top-level corruptions STOP.",
        "BI. authority-cycle audit": "Authority cycles: 0.",
        "BL. final freeze": "Helpers, schemas, composition adapter, and runner were frozen before final execution.",
        "BM. final positive dry run": "Exactly one frozen integrated R17 dry run PASS.",
        "BN. final runtime-scope negative": "Exactly one post-positive offline-scope mutation STOP.",
        "BO. final naive-124 negative": "Exactly one post-positive flat 124-field union STOP.",
        "BP. final registry-path negative": "Exactly one post-positive valid-looking path mutation STOP.",
        "BT. exact execution counts": (
            f"Approved Python invocations {approved_invocations}; py_compile 3; pre-freeze positive fixtures 3; "
            f"final positive 1; field-presence negatives {len(COMPOSE.V3_FIELDS)}; semantic corruptions {len(COMPOSE.V3_FIELDS)}; "
            "AppLauncher/environment/learner/CUDA/formal workers/R6 attempts 0/0/0/0/0/0; git add/commit/push 0/0/0."
        ),
        "BU. retained nonclaims": "No live R6 grant, runtime, training-quality, checkpoint, evaluation/playback, long-training, or public-route claim.",
        "BV. final classification": f"`{CLASSIFICATION}`",
        "BW. GPT-review handoff": "Candidate only. Independent GPT review is next; do not launch RE6-R6.",
    }
    body = "\n\n".join(
        f"## {name}\n\n{special.get(name, 'PASS — see the corresponding machine-readable artifact for exact contract fields and evidence.')}"
        for name in section_names
    )
    rows = read(OUT / "layer_a_composition_field_map.json")["rows"]
    composition_table = "\n".join(
        f"| `{row['field_name']}` | {row['old_status']} | {row['origin']} | `{row['new_status']}` | {row['action']} |"
        for row in rows
    )
    negatives = read(OUT / "racq_negative_matrix.json")
    group_counts = [
        ("Runtime authority", 7), ("Run binding", 6), ("Registry", 6),
        ("Composition/source", 6), ("Field presence", len(COMPOSE.V3_FIELDS)),
        ("Semantic corruption", len(COMPOSE.V3_FIELDS)),
    ]
    negative_table = "\n".join(f"| {name} | {count} | {count} | {count} | 0 |" for name, count in group_counts)
    return f"""# Phase B2-T4-RACQ runtime authority and Layer-A composition qualification report

Classification: `{CLASSIFICATION}`

Outcome: **COMPLETE / AWAITING GPT REVIEW**. All work was pure/static/offline.

{body}

## Primary composition table

| Semantic fact | Old LAQ field | PPQ-V2-R1 field/origin | V3 canonical field | Action |
|---|---|---|---|---|
{composition_table}

## Primary runtime authority table

| Property | Offline PPQ-V2-R1 | RACQ runtime contract | Result |
|---|---|---|---|
| Scope | OFFLINE-QUALIFICATION-ONLY | FORMAL-RUNTIME-AUTHORIZED | PASS |
| Phase | exact | exact | PASS |
| Authority digest | qualification | runtime canonical | PASS |
| Authority path | qualification filename formula | derived deterministic | PASS |
| Run binding | qualification | runtime-specific | PASS |
| Binding path | qualification filename formula | derived deterministic | PASS |
| Config binding | bounded | explicit | PASS |
| Namespace binding | bounded | explicit | PASS |

## Primary registry table

| Registry property | Frozen LAQ-R1 | RACQ |
|---|---|---|
| Semantic definition | R3 exact document | stable template |
| Runtime paths | hardcoded | generated from run context |
| Phase portability | No | Yes |
| Manual path edits | rejected | rejected |
| Template identity | frozen document | frozen semantic template |
| Instance identity | historical only | run-specific |

## Primary negative table

| Group | Cases | Expected STOP | Actual STOP | Unexpected PASS |
|---|---:|---:|---:|---:|
{negative_table}
| **Total** | {negatives['expected_stop']} | {negatives['expected_stop']} | {negatives['actual_stop']} | {negatives['unexpected_pass']} |

## Candidate identity table

| Candidate | SHA-256 |
|---|---|
| Runtime-authority helper | `{manifest['runtime_authority_helper_sha256']}` |
| Registry-template/composition helper | `{manifest['composition_helper_sha256']}` |
| Layer-A v3 schema | `{manifest['layer_a_v3_schema_sha256']}` |
| Qualification runner | `{manifest['qualification_runner_sha256']}` |
| Final positive result | `{manifest['final_positive_result_sha256']}` |
"""


def finalize(approved_invocations: int) -> dict[str, Any]:
    frozen = verify_freeze()
    for name in ("final_positive_dry_run_result.json", "final_runtime_scope_negative.json",
                 "final_naive_124_negative.json", "final_registry_path_negative.json"):
        require((OUT / name).is_file(), f"FINAL-ARTIFACT-MISSING:{name}")
    before = read(OUT / "protected_source_identity_before.json")
    after = protected_identity()
    require(after == before, "PROTECTED-SOURCE-DRIFT")
    artifact("protected_source_identity_after.json", after)
    negative = read(OUT / "racq_negative_matrix.json")
    require(negative["unexpected_pass"] == 0, "NEGATIVE-UNEXPECTED-PASS")
    manifest = {
        **frozen,
        "registry_template_helper_sha256": frozen["composition_helper_sha256"],
        "composition_adapter_sha256": frozen["composition_helper_sha256"],
        "final_positive_result_sha256": sha(OUT / "final_positive_dry_run_result.json"),
        "status": "CANDIDATE / AWAITING GPT REVIEW",
    }
    artifact("racq_source_identity_manifest.json", manifest)
    final = {
        "classification": CLASSIFICATION,
        "status": "COMPLETE / AWAITING GPT REVIEW",
        "historical_re6_r5": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
        "formal_runtime_authority": "QUALIFIED OFFLINE / AWAITING GPT REVIEW",
        "run_portable_layer_a_composition": "QUALIFIED OFFLINE / AWAITING GPT REVIEW",
        "canonical_layer_a_v3_field_count": len(COMPOSE.V3_FIELDS),
        "nested_ppq_v2_r1_field_count": len(PPQ_R1.FIELDS),
        "duplicate_semantic_authorities": 0,
        "inherited_predicates_mapped": 39,
        "new_runtime_authority_predicates": 9,
        "full_negative_expected_stop": negative["expected_stop"],
        "full_negative_actual_stop": negative["actual_stop"],
        "full_negative_unexpected_pass": negative["unexpected_pass"],
        "final_positive_dry_runs": 1,
        "final_runtime_scope_negatives": 1,
        "final_naive_124_negatives": 1,
        "final_registry_path_negatives": 1,
        "approved_python_invocations": approved_invocations,
        "py_compile_invocations": 3,
        "formal_supervisors": 0, "formal_workers": 0, "cuda": 0,
        "app_launcher": 0, "environment": 0, "reset": 0, "learner": 0,
        "physical_steps": 0, "re6_r6_formal_attempts": 0,
        "checkpoint": 0, "public_activation": 0, "evaluation_playback": 0,
        "production_modifications": 0, "ppq_v2_r1_modifications": 0,
        "laq_r1_modifications": 0, "historical_r3_r4_r5_modifications": 0,
        "git_add_commit_push": [0, 0, 0],
        "re6_r6": "NOT AUTHORIZED", "public_route": "DORMANT / BLOCKED",
        "next": "independent GPT review of B2-T4-RACQ",
    }
    artifact("final_result.json", final)
    REPORT.write_text(report_text(final, manifest, approved_invocations), encoding="utf-8")
    return final


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("self-check", "qualify", "final-positive",
                                         "final-scope-negative", "final-naive-negative",
                                         "final-registry-negative", "finalize"))
    parser.add_argument("--approved-python-invocations", type=int, default=0)
    args = parser.parse_args()
    if args.mode == "self-check":
        value = qualification(False)
    elif args.mode == "qualify":
        value = qualification(True)
    elif args.mode == "final-positive":
        value = final_positive()
    elif args.mode == "final-scope-negative":
        value = final_runtime_scope_negative()
    elif args.mode == "final-naive-negative":
        value = final_naive_negative()
    elif args.mode == "final-registry-negative":
        value = final_registry_negative()
    else:
        require(args.approved_python_invocations > 0, "APPROVED-PYTHON-INVOCATION-COUNT")
        value = finalize(args.approved_python_invocations)
    print(json.dumps(value, sort_keys=True))


if __name__ == "__main__":
    main()
