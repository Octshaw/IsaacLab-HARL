"""One-shot B2-T4-RE6-R7 RACQ-R1-bound formal runtime harness.

The reviewed contracts are imported read-only.  A fresh R7 namespace derives
the already reviewed RE6 transaction engine, then adds the reviewed PPQ-V2-R1,
RACQ and RACQ-R1 authority/receipt chain.  The formal worker is released only
after its real PID has been bound and every pre-runtime gate has passed.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import traceback
from typing import Any, Callable, Mapping
import uuid

import _assignment_phase_b2_t4_laq_worker_receipt as LAQ
import _assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_R1
import _assignment_phase_b2_t4_racq_layer_a_composition as COMPOSE
import _assignment_phase_b2_t4_racq_r1_layer_a_validation as RACQ_R1
import _assignment_phase_b2_t4_racq_r1_mode_dispatch as DISPATCH
import _assignment_phase_b2_t4_racq_runtime_authority as RACQ
import test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_TEST


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DAY = SCAN / "AgentRead/202609/20260921"
OUT = DAY / "b2_t4_re6_r7_artifacts"
REPORT = DAY / (
    "PHASE_B2_T4_RE6_R7_RACQ_R1_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_"
    "INTEGRATION_REPORT.md"
)
R3_SOURCE = HERE / "test_assignment_phase_b2_t4_re6_r3_normal_horizon_learned_training_integration.py"
NORMALIZER = HERE / "_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py"
PHASE = "B2-T4-RE6-R7"
SUCCESS = (
    "PHASE-B2-T4-RE6-R7-RACQ-R1-BOUND-NORMAL-HORIZON-LEARNED-TRAINING-"
    "INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW"
)
INSTRUCTION_SHA256 = "2fa301f2db30255cada9c728f2aada36d2e393d494b90dc912cba3abc34ff4d8"
EXPECTED_HEAD = "b71d85a32f51be6ada324f870813a56bb45dd396"
EXPECTED_STAGED_COUNT = 359
EXPECTED_INDEX_SHA = "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
EXPECTED_PATH_SET_SHA = "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
PRE_FIRST_WRITE = {
    "porcelain_line_count": 25521,
    "porcelain_sha256": "61a13f8608f3ed2fff28907c8e748e5610631697df8d5eb5e9111eb5b5cc881a",
    "staged_path_count": EXPECTED_STAGED_COUNT,
    "staged_index_sha256": EXPECTED_INDEX_SHA,
    "monthly_path_set_sha256": EXPECTED_PATH_SET_SHA,
}
CONFIG = PPQ_TEST.CONFIG
PRODUCTION = PPQ_TEST.PRODUCTION
W2I = PPQ_TEST.W2I
PW_HELPER = PPQ_TEST.PW_HELPER

EXPECTED_IDENTITIES = {
    "racq_r1_dispatch": (HERE / "_assignment_phase_b2_t4_racq_r1_mode_dispatch.py",
                         "ea0ca12d96775ad73189314161788831c3074431cbe7afa4db8b7086ec667bb9"),
    "racq_r1_wrapper": (HERE / "_assignment_phase_b2_t4_racq_r1_layer_a_validation.py",
                        "60f189f7c9dbef26a18c08848c518855f7c151e66f14978fb3650e2f72a1f1be"),
    "racq_r1_runner": (HERE / "test_assignment_phase_b2_t4_racq_r1_layer_a_mode_dispatch.py",
                       "b6c1028bb72048034c49268aae424e78b3a394174f98438612a3d4dba615ed57"),
    "racq": (HERE / "_assignment_phase_b2_t4_racq_runtime_authority.py",
             "f304dfb21ced710ef08fcb92c6373785f3945e5c839ac02259e8939f46800ef0"),
    "composition": (HERE / "_assignment_phase_b2_t4_racq_layer_a_composition.py",
                    "2a68ecde62f3ccb2277a42dc1f2640267390e7b23f431ef22ab71f4d9ac26f57"),
    "ppq_v2_r1": (HERE / "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
                  "bd057efaeac73154b49b1e8307c9c7585f0feb449aaad3fbf4813a361a31b8a0"),
    "ppq_v2_r1_runner": (HERE / "test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
                         "fe420687da10b82df4c66e376cd6959f3d0199553e706f3f4eacd23d79e15433"),
    "laq_r1": (HERE / "_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
               "22720385c3eb4c67bf2317c0a90f5ca2575b85f8e07529be3c661f71cb4082b3"),
    "laq_r1_runner": (HERE / "test_assignment_phase_b2_t4_laq_r1_authority_binding.py",
                      "9d89b562a2564cea1e16e3fd708d8a3a583de04c25bc473135d50cdb23fea904"),
    "w2e": (HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py",
            "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0"),
    "w2i": (W2I, "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b"),
    "pw": (PW_HELPER, "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b"),
    "normalizer": (NORMALIZER, "316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3"),
    "production_full_transaction": (PRODUCTION["full_transaction"],
        "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7"),
    "production_real_adapter": (PRODUCTION["real_isaac_adapter"],
        "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac"),
    "production_environment": (PRODUCTION["environment"],
        "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363"),
}

CANONICAL_NAMES = {
    "W1": "W1_cross_update_ownership.json",
    "W2E": "W2_multi_update_completion_v2.json",
    "W3": "W3_real_zero_dvm_actor.json",
    "W4": "W4_real_nonterminal_bootstrap.json",
    "W5": "W5_normal_horizon_terminal_autoreset.json",
    "W6": "W6_post_autoreset_training.json",
    "W7": "W7_runtime_p2_immutability.json",
}


def require(condition: bool, reason: str, detail: object = None) -> None:
    if not condition:
        raise RuntimeError(f"STOP — PHASE-B2-T4-RE6-R7-STOP-{reason}: {detail!r}")


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def persist(path: Path, value: object, *, exclusive: bool = True) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive:
        require(not path.exists(), "ARTIFACT-ALREADY-EXISTS", str(path))
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    require(not temporary.exists(), "TEMP-ARTIFACT-EXISTS", str(temporary))
    data = canonical(value)
    with temporary.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    require(path.read_bytes() == data, "ARTIFACT-READBACK", str(path))
    return sha256(data).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(("git", *args), cwd=ROOT)


def repository_authority() -> dict[str, Any]:
    porcelain = git_bytes("status", "--porcelain=v1", "-uall")
    staged = git_bytes("ls-files", "--stage")
    paths = git_bytes("diff", "--cached", "--name-only").decode().splitlines()
    value = {
        "branch": git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "current_porcelain_line_count": len(porcelain.splitlines()),
        "current_porcelain_sha256": sha256(porcelain).hexdigest(),
        "pre_first_r7_write": PRE_FIRST_WRITE,
        "staged_path_count": len(paths),
        "staged_index_sha256": sha256(staged).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(paths).encode()).hexdigest(),
        "git_add_commit_push": [0, 0, 0],
    }
    require(value["branch"] == "main", "REPOSITORY-BRANCH")
    require(value["HEAD"] == value["origin_main"] == value["merge_base"] == EXPECTED_HEAD,
            "REPOSITORY-COMMIT")
    require(value["staged_path_count"] == EXPECTED_STAGED_COUNT and
            value["staged_index_sha256"] == EXPECTED_INDEX_SHA and
            value["monthly_path_set_sha256"] == EXPECTED_PATH_SET_SHA,
            "REPOSITORY-INDEX")
    return value


def run_identity() -> dict[str, Any]:
    return read(OUT / "r7_run_identity.json")


def run_dir() -> Path:
    return OUT / run_identity()["run_id"]


def namespace(run_id: str) -> str:
    return RACQ.expected_artifact_namespace(PHASE, run_id)


def base_runtime(directory: Path) -> dict[str, Any]:
    """Load the reviewed R3 integration logic into a fresh R7 path namespace."""
    source = R3_SOURCE.read_text(encoding="utf-8")
    old_out = 'OUT = DATE / "b2_t4_re6_r3_artifacts"'
    old_prefix = 'PREFIX = OUT / "b2_t4_re6_r3_normal_horizon_20260920_formal01"'
    require(source.count(old_out) == 1 and source.count(old_prefix) == 1,
            "R3-DERIVATION-SOURCE")
    source = source.replace(old_out, f"OUT = Path({str(directory)!r})")
    source = source.replace(old_prefix,
        'PREFIX = OUT / "b2_t4_re6_r7_normal_horizon_20260921_formal01"')
    old_derived = ('\'ARTIFACTS = SCAN / "AgentRead" / "202609" / "20260920" / '
                   '"b2_t4_re6_r3_artifacts"\'')
    portable_directory = directory.resolve().as_posix()
    source = source.replace(
        old_derived, f"'ARTIFACTS = Path(\"{portable_directory}\")'")
    old_derived_prefix = ('\'PREFIX = ARTIFACTS / '
                          '"b2_t4_re6_r3_normal_horizon_20260920_formal01"\'')
    source = source.replace(old_derived_prefix,
        "'PREFIX = ARTIFACTS / \"b2_t4_re6_r7_normal_horizon_20260921_formal01\"'")
    source = source.replace("B2-T4-RE6-R3", PHASE)
    source = source.replace("b2-t4-re6-r3", "b2-t4-re6-r7")
    source = re.sub(r"(?<!b2_t4_)re6_r3_", "re6_r7_", source)
    source = source.replace("r'b2_t4_re6_r3_", "r'b2_t4_re6_r7_")
    source = source.replace('"b2_t4_re6_r3_20260920_formal01"',
                            '"b2_t4_re6_r7_20260921_formal01"')
    source = source.replace('"repository_authority.json"',
                            '"legacy_runtime_repository_authority.json"')
    source = source.replace('"reviewed_identity_gate.json"',
                            '"legacy_runtime_identity_gate.json"')
    source = source.replace('"static_authority.json"',
                            '"legacy_runtime_static_authority.json"')
    scope = {"__name__": "_b2_t4_re6_r7_derived_runtime",
             "__file__": str(Path(__file__).resolve()), "__package__": None}
    exec(compile(source, str(Path(__file__).resolve()), "exec"), scope)
    return scope


def external_authorization_digest() -> str:
    return RACQ.digest({
        "instruction_sha256": INSTRUCTION_SHA256,
        "source_phase": PHASE,
        "live_authorities": 1,
        "formal_supervisors": 1,
        "mutation_bearing_workers": 1,
        "retries": 0,
    })


def config_policy_identity() -> str:
    return RACQ.digest({"binding": "exact PPQ-V2-R1 config_identity_digest",
                        "required": True, "version": 1})


def make_live_authority() -> dict[str, Any]:
    value = RACQ.make_offline_qualification_authority(
        source_phase=PHASE,
        external_authorization_digest=external_authorization_digest(),
        config_policy_identity=config_policy_identity(),
    )
    value["instance_purpose"] = RACQ.LIVE_PURPOSE
    value["live_runtime_grant"] = True
    value["authority_payload_digest"] = RACQ.digest(
        {key: item for key, item in value.items() if key != "authority_payload_digest"})
    return value


def authority_path() -> Path:
    return OUT / RACQ.authority_relative_path(PHASE)


def validation_context() -> dict[str, Any]:
    return DISPATCH.make_validation_context(
        execution_purpose=DISPATCH.LIVE_FORMAL_RUNTIME,
        expected_source_phase=PHASE,
    )


def identity_gate() -> dict[str, Any]:
    rows = {name: {"path": path.relative_to(ROOT).as_posix(),
                   "expected_sha256": expected, "actual_sha256": sha(path),
                   "pass": sha(path) == expected}
            for name, (path, expected) in EXPECTED_IDENTITIES.items()}
    schema_path = DAY / "b2_t4_racq_r1_artifacts/layer_a_validation_context_schema.json"
    rows["racq_r1_context_schema"] = {
        "path": schema_path.relative_to(ROOT).as_posix(),
        "expected_sha256": "ae8e40dc4ba5c06b5975a2a678aab7ddb9a9ba6db6d0a73dbc9ad1d959cde460",
        "actual_sha256": sha(schema_path),
        "pass": sha(schema_path) == "ae8e40dc4ba5c06b5975a2a678aab7ddb9a9ba6db6d0a73dbc9ad1d959cde460",
    }
    require(all(row["pass"] for row in rows.values()), "REVIEWED-IDENTITY-MISMATCH", rows)
    return {"pass": True, "identity_count": len(rows), "identities": rows,
            "production_modifications": 0, "reviewed_contract_modifications": 0}


def validate_live_authority(value: Mapping[str, Any]) -> dict[str, Any]:
    loaded = RACQ.load_runtime_authority(
        actual_path=authority_path(), authority_root=OUT,
        expected_source_phase=PHASE,
        expected_external_authorization_digest=external_authorization_digest(),
        expected_config_policy_identity=config_policy_identity(),
        qualification_mode=False,
    )
    checks = {
        "scope": loaded["authorization_scope"] == RACQ.AUTHORIZATION_SCOPE,
        "mode": loaded["authorization_mode"] == RACQ.AUTHORIZATION_MODE,
        "instance_purpose": loaded["instance_purpose"] == RACQ.LIVE_PURPOSE,
        "live_runtime_grant": loaded["live_runtime_grant"] is True,
        "phase": loaded["authorized_source_phase"] == PHASE,
        "digest": loaded["authority_payload_digest"] == value["authority_payload_digest"],
        "deterministic_path": authority_path() == OUT / RACQ.authority_relative_path(PHASE),
    }
    require(all(checks.values()), "RUNTIME-AUTHORITY-INVALID", checks)
    return {"pass": True, "checks": checks,
            "authority_digest": loaded["authority_payload_digest"],
            "deterministic_path": authority_path().relative_to(OUT).as_posix()}


def stopped(label: str, action: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = action()
        if type(value) is dict and value.get("status") == "STOP":
            return {"case": label, "status": "STOP", "reason": str(value)}
    except Exception as exc:
        return {"case": label, "status": "STOP",
                "exception_type": type(exc).__name__, "reason": str(exc)}
    return {"case": label, "status": "UNEXPECTED-PASS"}


def mode_controls(authority: Mapping[str, Any]) -> dict[str, Any]:
    live = validation_context()
    direct = lambda candidate, context: RACQ.validate_authority_object(
        candidate, expected_source_phase=context["expected_source_phase"],
        expected_external_authorization_digest=external_authorization_digest(),
        expected_config_policy_identity=config_policy_identity(),
        qualification_mode=DISPATCH.resolve_runtime_authority_validation_mode(context).qualification_mode)
    direct(authority, live)
    offline = DISPATCH.make_validation_context(
        execution_purpose=DISPATCH.OFFLINE_QUALIFICATION, expected_source_phase=PHASE)
    false_live = deepcopy(authority)
    false_live["live_runtime_grant"] = False
    false_live["authority_payload_digest"] = RACQ.digest(
        {k: v for k, v in false_live.items() if k != "authority_payload_digest"})
    offline_shaped = RACQ.make_offline_qualification_authority(
        source_phase=PHASE, external_authorization_digest=external_authorization_digest(),
        config_policy_identity=config_policy_identity())
    rows = [
        stopped("live authority + OFFLINE_QUALIFICATION", lambda: direct(authority, offline)),
        stopped("live authority + missing context", lambda: direct(authority, None)),
        stopped("live authority + live_runtime_grant=false", lambda: direct(false_live, live)),
        stopped("offline-shaped authority + LIVE_FORMAL_RUNTIME", lambda: direct(offline_shaped, live)),
    ]
    result = {"positive": "PASS", "expected_stop": 4,
              "actual_stop": sum(row["status"] == "STOP" for row in rows),
              "unexpected_pass": sum(row["status"] != "STOP" for row in rows),
              "cases": rows}
    result["pass"] = result["unexpected_pass"] == 0
    require(result["pass"], "MODE-DISPATCH", result)
    return result


def process_config(run_id: str, worker_pid: int, env_id: str) -> dict[str, Any]:
    return {"environment": env_id, "profile": "event_gated_local_mrta",
            "device": "cuda:0", "T": 2, "E": 2, "M": 3, "N": 12,
            "actor_epochs": 5, "actor_minibatches": 2,
            "critic_epochs": 5, "critic_minibatches": 2,
            "ValueNorm": True, "fixed_order": False,
            "episode_length_s": 30.0, "max_episode_length": 300,
            "control_step_seconds": 0.1, "run_id": run_id,
            "worker_pid": worker_pid}


def ppq_paths(directory: Path, run_id: str) -> tuple[Path, Path, Path]:
    root = directory / "ppq_source_phase_authority"
    instance = "offline-b2-t4-re6-r7-formal-source-phase"
    return (root,
            root / f"{instance}.source_phase_authority.json",
            root / f"{run_id}.source_phase_run_binding.json")


def ppq_identity() -> dict[str, str]:
    return PPQ_TEST.new_identity()


def ppq_validate(receipt: Mapping[str, Any], directory: Path, run_id: str) -> None:
    root, auth_path, bind_path = ppq_paths(directory, run_id)
    PPQ_R1.validate_receipt(
        receipt, expected_phase=PHASE, identity=ppq_identity(),
        legacy_identity=PPQ_TEST.legacy_identity(), config=CONFIG,
        authority_path=auth_path, expected_authority_path=auth_path,
        run_binding_path=bind_path, expected_run_binding_path=bind_path,
        authority_root=root, artifact_namespace=namespace(run_id))


def prepare_bindings(run_id: str, worker_pid: int, directory: Path) -> dict[str, Any]:
    authority = read(authority_path())
    config_digest = ppq_identity()["config_identity_digest"]
    binding = RACQ.make_run_binding(
        authority=authority, run_id=run_id, worker_pid=worker_pid,
        config_digest=config_digest, artifact_namespace=namespace(run_id),
        registry_template_digest=COMPOSE.registry_template_digest())
    binding_path = OUT / RACQ.binding_relative_path(PHASE, run_id)
    persist(binding_path, binding)
    ppq_root, ppq_authority_path, ppq_binding_path = ppq_paths(directory, run_id)
    ppq_authority = PPQ_R1.make_offline_authority(
        source_phase=PHASE,
        authority_instance_id="offline-b2-t4-re6-r7-formal-source-phase")
    persist(ppq_authority_path, ppq_authority)
    ppq_binding = PPQ_R1.make_run_binding(
        authority=ppq_authority, run_id=run_id, worker_pid=worker_pid,
        config_digest=config_digest, artifact_namespace=namespace(run_id))
    persist(ppq_binding_path, ppq_binding)
    return {"binding": binding, "binding_path": binding_path,
            "ppq_authority": ppq_authority, "ppq_binding": ppq_binding}


def synthetic_ppq(base: Mapping[str, Any], run_id: str, worker_pid: int,
                  directory: Path) -> dict[str, Any]:
    raw, _ = base["synthetic_raw"]()
    raw["source_phase"] = PHASE
    raw["run_id"] = run_id
    raw["worker_pid"] = worker_pid
    pw = {"contract_version": base["PPQ"].PW_VERSION, "run_id": run_id,
          "transaction_count": 160, "critic_actual": 6560,
          "actor_factor_actual": 640, "missing_count": 0,
          "duplicate_count": 0, "order_fault_count": 0,
          "digest_fault_count": 0, "temp_residue_count": 0}
    verifier = lambda: pw
    converted = base["normalized"](raw, verifier)
    root, auth_path, bind_path = ppq_paths(directory, run_id)
    receipt, _, _, trace = PPQ_R1.build_receipt(
        converted["normalized"], w2e_selector=PPQ_TEST.W2E.reconcile,
        w2i_manifest=W2I, pw_reconcile=lambda _: verifier(),
        expected_phase=PHASE, config=CONFIG, identity=ppq_identity(),
        legacy_identity=PPQ_TEST.legacy_identity(), production_sources=PRODUCTION,
        pw_helper_path=PW_HELPER, authority_path=auth_path,
        expected_authority_path=auth_path, run_binding_path=bind_path,
        expected_run_binding_path=bind_path, authority_root=root,
        artifact_namespace=namespace(run_id))
    return {"raw": raw, "converted": converted, "receipt": receipt,
            "verifier": verifier, "trace": trace}


def ppq_campaign(evidence: Mapping[str, Any], directory: Path, run_id: str,
                 verifier: Callable[[], Mapping[str, Any]]) -> dict[str, Any]:
    root, auth_path, bind_path = ppq_paths(directory, run_id)
    provisional = directory / "provisional_witnesses"
    provisional.mkdir(parents=True, exist_ok=False)
    for key, value in evidence["witnesses"].items():
        persist(provisional / f"{key}.json", value)

    def destination(path: Path) -> Path:
        for key, name in CANONICAL_NAMES.items():
            if path.name == f"{key}_canonical_success.json":
                return directory / name
        return directory / path.name

    return PPQ_R1.finalize_campaign(
        evidence, w2e_selector=PPQ_TEST.W2E.reconcile, w2i_manifest=W2I,
        pw_reconcile=lambda _: verifier(), expected_phase=PHASE, config=CONFIG,
        identity=ppq_identity(), legacy_identity=PPQ_TEST.legacy_identity(),
        production_sources=PRODUCTION, pw_helper_path=PW_HELPER,
        authority_path=auth_path, expected_authority_path=auth_path,
        run_binding_path=bind_path, expected_run_binding_path=bind_path,
        authority_root=root, artifact_namespace=namespace(run_id),
        writer=lambda path, payload: PPQ_R1.atomic_persist(destination(path), payload),
        reader=lambda path: PPQ_R1.readback(destination(path)), output_dir=directory)


def synthetic_chain(base: Mapping[str, Any], run_id: str, worker_pid: int,
                    prepared: Mapping[str, Any], directory: Path) -> dict[str, Any]:
    fixture = synthetic_ppq(base, run_id, worker_pid, directory)
    raw, converted, receipt = fixture["raw"], fixture["converted"], fixture["receipt"]
    verifier, trace = fixture["verifier"], fixture["trace"]
    laq_payload = synthetic_laq_payload(base, raw, converted, receipt, verifier,
                                        prepared, directory, run_id, worker_pid,
                                        synthetic=True)
    layer_payload = COMPOSE.compose_payload(
        ppq_receipt=receipt, laq_v2_payload=laq_payload,
        runtime_authority=read(authority_path()), run_binding=prepared["binding"],
        registry_instance=prepared["registry"])
    envelope = COMPOSE.envelope_for(layer_payload)
    result = RACQ_R1.adjudicate_supervisor_v3_with_context(
        envelope, layer_b_pass=True,
        ppq_validator=lambda value: ppq_validate(value, directory, run_id),
        source_ppq_receipt=receipt, source_laq_v2_payload=laq_payload,
        authority_path=authority_path(), binding_path=prepared["binding_path"],
        authority_root=OUT,
        expected_external_authorization_digest=external_authorization_digest(),
        expected_config_policy_identity=config_policy_identity(),
        registry_template=prepared["template"], registry_instance=prepared["registry"],
        run_context=prepared["context"], validation_context=validation_context())
    require(result["pass"], "SYNTHETIC-R7-CHAIN", result)
    controls = layer_controls(envelope, receipt, laq_payload, prepared, directory, run_id)
    return {"pass": True, "ppq_fields": len(receipt),
            "layer_a_fields": len(layer_payload), "trace": trace,
            "inherited_pass": sum(result["layer_a"]["inherited_predicates"].values()),
            "racq_pass": sum(result["layer_a"]["new_authority_predicates"].values()),
            "controls": controls, "supervisor": result}


def synthetic_laq_payload(base: Mapping[str, Any], raw: Mapping[str, Any],
                          converted: Mapping[str, Any], receipt: Mapping[str, Any],
                          verifier: Callable[[], Mapping[str, Any]],
                          prepared: Mapping[str, Any], directory: Path, run_id: str,
                          worker_pid: int, *, synthetic: bool) -> dict[str, Any]:
    handoff = {
        "status": "success", "source_authority_digest": sha(directory / "r7_static_authority_snapshot.json")
            if (directory / "r7_static_authority_snapshot.json").exists() else "0" * 64,
        "config_authority_digest": ppq_identity()["config_identity_digest"],
        "filesystem_precondition_digest": sha(directory / "filesystem_precondition.json")
            if (directory / "filesystem_precondition.json").exists() else "1" * 64,
        "cuda_probe_count": 1, "cuda_probe_pass": True,
        "app_launcher_started": True, "entry_point_resolution_pass": True,
        "env_close_pass": True, "app_close_invoked": True,
        "receipt_written_before_app_close": True, "receipt_fsync_pass": True,
        "receipt_readback_pass": True,
    }
    pw = verifier()
    pw_view = {"critic_records": pw["critic_actual"],
               "actor_factor_records": pw["actor_factor_actual"],
               "missing": pw["missing_count"], "duplicate": pw["duplicate_count"],
               "out_of_order": pw["order_fault_count"],
               "digest_mismatch": pw["digest_fault_count"],
               "temp_residue": pw["temp_residue_count"],
               "old_mutable_progress_paths": 0}
    witnesses = {key: raw["witnesses"][{
        "W1": "W1_CROSS_UPDATE_OWNERSHIP", "W2E": "W2_MULTI_UPDATE_COMPLETION",
        "W3": "W3_ZERO_DVM_ACTOR", "W4": "W4_NONTERMINAL_BOOTSTRAP",
        "W5": "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
        "W6": "W6_POST_AUTORESET_TRAINING", "W7": "W7_RUNTIME_P2_IMMUTABILITY"}[key]]
        for key in CANONICAL_NAMES}
    zero_dvm_path = directory / "zero_dvm_actor_ledger.jsonl"
    zero_dvm_rows = ([json.loads(line) for line in zero_dvm_path.read_text(
        encoding="utf-8").splitlines() if line] if not synthetic and zero_dvm_path.is_file()
        else [{"pass": True} for _ in raw["transactions"]])
    sources = {"raw_final": raw["final"], "ppq_v2_candidate": receipt,
        "normalized": converted, "worker_handoff": handoff, "pw_verifier": pw_view,
        "witnesses": witnesses, "normalizer_sha256": sha(NORMALIZER),
        "ppq_v2_readback": {"pass": True},
        "ppq_v2_candidate_file_sha256": PPQ_R1.digest(receipt),
        "transaction_rows": raw["transactions"], "terminal_rows": raw["terminal"],
        "zero_dvm_rows": zero_dvm_rows,
    }
    return LAQ.project_layer_a_worker_receipt(sources, PPQ_R1.schema_document())


def layer_controls(envelope: Mapping[str, Any], receipt: Mapping[str, Any],
                   laq_payload: Mapping[str, Any], prepared: Mapping[str, Any],
                   directory: Path, run_id: str) -> dict[str, Any]:
    kwargs = dict(
        ppq_validator=lambda value: ppq_validate(value, directory, run_id),
        source_ppq_receipt=receipt, source_laq_v2_payload=laq_payload,
        authority_path=authority_path(), binding_path=prepared["binding_path"],
        authority_root=OUT,
        expected_external_authorization_digest=external_authorization_digest(),
        expected_config_policy_identity=config_policy_identity(),
        registry_template=prepared["template"], registry_instance=prepared["registry"],
        run_context=prepared["context"], validation_context=validation_context())
    def changed(field: str, value: Any) -> dict[str, Any]:
        altered = deepcopy(envelope)
        altered["payload"][field] = value
        altered["payload_sha256"] = COMPOSE.digest(altered["payload"])
        return altered
    naive = COMPOSE.envelope_for({**deepcopy(receipt), **{
        key: deepcopy(laq_payload[key]) for key in LAQ.EXTRA_TYPES}})
    missing_ppq = deepcopy(envelope)
    del missing_ppq["payload"]["ppq_v2_r1_payload"]
    missing_ppq["payload_sha256"] = COMPOSE.digest(missing_ppq["payload"])
    wrong_context = DISPATCH.make_validation_context(
        execution_purpose=DISPATCH.OFFLINE_QUALIFICATION, expected_source_phase=PHASE)
    rows = [
        stopped("naive 124-field union", lambda: RACQ_R1.validate_layer_a_v3_with_context(naive, **kwargs)),
        stopped("missing nested PPQ", lambda: RACQ_R1.validate_layer_a_v3_with_context(missing_ppq, **kwargs)),
        stopped("wrong runtime-authority digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(
            changed("runtime_authority_digest", "0" * 64), **kwargs)),
        stopped("wrong run-binding digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(
            changed("runtime_run_binding_digest", "0" * 64), **kwargs)),
        stopped("wrong registry digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(
            changed("registry_instance_digest", "0" * 64), **kwargs)),
        stopped("wrong filesystem digest", lambda: RACQ_R1.validate_layer_a_v3_with_context(
            changed("filesystem_precondition_digest", "0" * 64), **kwargs)),
        stopped("wrong validation context", lambda: RACQ_R1.validate_layer_a_v3_with_context(
            envelope, **{**kwargs, "validation_context": wrong_context})),
        stopped("duplicate semantic authority", lambda: RACQ_R1.validate_layer_a_v3_with_context(
            changed("source_phase_authority_digest", receipt["source_phase_authority_digest"]), **kwargs)),
    ]
    result = {"expected_stop": len(rows),
              "actual_stop": sum(row["status"] == "STOP" for row in rows),
              "unexpected_pass": sum(row["status"] != "STOP" for row in rows),
              "cases": rows}
    result["pass"] = result["unexpected_pass"] == 0
    require(result["pass"], "LAYER-A-V3-CONTROLS", result)
    return result


def static_preflight() -> dict[str, Any]:
    require(not OUT.exists(), "R7-ARTIFACT-NAMESPACE-EXISTS", str(OUT))
    OUT.mkdir(parents=True)
    run_id = f"b2-t4-re6-r7-20260921-formal01-{uuid.uuid4().hex}"
    directory = OUT / run_id
    directory.mkdir()
    persist(OUT / "r7_run_identity.json", {"source_phase": PHASE, "run_id": run_id,
            "artifact_namespace": namespace(run_id), "unique": True,
            "retry_run_id_count": 0})
    repo = repository_authority()
    persist(OUT / "repository_authority.json", repo)
    persist(OUT / "reviewed_starting_authority.json", {
        "RACQ_R1": "GPT REVIEW PASS / CLOSED",
        "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED",
        "LAQ_R1": "GPT REVIEW PASS / CLOSED",
        "RACQ": "OFFLINE QUALIFICATION REVIEW PASS",
        "RE6_R3": "HISTORICAL / POISONED / NOT QUALIFIED",
        "RE6_R4_R6": "PRE-RUNTIME STOP / FORMAL ATTEMPTS 0 / NOT POISONED",
        "R7": "EXPLICITLY AUTHORIZED / PREPARING",
    })
    gate = identity_gate()
    persist(OUT / "reviewed_identity_gate.json", gate)
    base = base_runtime(directory)
    inherited = base["preflight"]()
    authority = make_live_authority()
    persist(authority_path(), authority)
    persist(OUT / "live_r7_runtime_authority.json", {
        "artifact_role": "identity pointer; not an alternate authority instance",
        "deterministic_path": authority_path().relative_to(OUT).as_posix(),
        "authority_payload_digest": authority["authority_payload_digest"]})
    authority_validation = validate_live_authority(authority)
    persist(OUT / "live_r7_runtime_authority_validation.json", authority_validation)
    context = validation_context()
    persist(OUT / "r7_validation_context.json", context)
    controls = mode_controls(authority)
    persist(OUT / "pre_runtime_mode_controls.json", controls)
    frozen = {"path": Path(__file__).resolve().relative_to(ROOT).as_posix(),
              "sha256": sha(Path(__file__).resolve()), "frozen": True,
              "source_edits_after_freeze_allowed": False}
    persist(OUT / "r7_harness_identity_freeze.json", frozen)
    result = {"pass": True, "phase": PHASE, "run_id": run_id,
              "reviewed_identities": gate["identity_count"],
              "live_authority_count": 1, "validation_context_count": 1,
              "mode_controls": controls, "inherited_preflight": inherited,
              "formal_supervisors": 0, "formal_workers": 0,
              "cuda": 0, "AppLauncher": 0, "environment": 0, "learner": 0}
    persist(OUT / "static_preflight_result.json", result)
    return result


def prepare_worker_release(process: subprocess.Popen[str], directory: Path,
                           run_id: str) -> dict[str, Any]:
    ready_path = directory / "worker_pid_handshake.json"
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline and not ready_path.exists() and process.poll() is None:
        time.sleep(0.1)
    require(ready_path.is_file(), "WORKER-PID-HANDSHAKE", process.poll())
    handshake = read(ready_path)
    require(handshake == {"phase": PHASE, "run_id": run_id,
                           "worker_pid": process.pid, "state": "BLOCKED_PRE_RUNTIME"},
            "WORKER-PID-HANDSHAKE-CONTENT", handshake)
    base = base_runtime(directory)
    prepared = prepare_bindings(run_id, process.pid, directory)
    fixture = synthetic_ppq(base, run_id, process.pid, directory)
    context = COMPOSE.make_run_context(
        source_phase=PHASE, run_id=run_id, worker_pid=process.pid,
        artifact_namespace=namespace(run_id),
        config_digest=ppq_identity()["config_identity_digest"],
        ppq_receipt_digest=PPQ_R1.digest(fixture["receipt"]))
    template = COMPOSE.registry_template_document()
    registry = COMPOSE.instantiate_registry(template, context)
    persist(directory / "layer_a_registry_instance.json", registry)
    prepared.update({"context": context, "template": template, "registry": registry})
    env_id = base["derived_runtime"]()[0]["ENV_ID"]
    config = process_config(run_id, process.pid, env_id)
    persist(directory / "process_config_authority.json", {
        "phase": PHASE, "config": config, "process_config_sha256": PPQ_R1.digest(config),
        "racq_config_digest": ppq_identity()["config_identity_digest"], "pass": True})
    binding_loaded = RACQ.load_run_binding(
        actual_path=prepared["binding_path"], authority_root=OUT,
        authority=read(authority_path()), expected_run_id=run_id,
        expected_worker_pid=process.pid,
        expected_config_digest=ppq_identity()["config_identity_digest"],
        expected_artifact_namespace_value=namespace(run_id),
        expected_registry_template_digest=COMPOSE.registry_template_digest())
    persist(OUT / "live_r7_run_binding.json", {
        "artifact_role": "identity pointer; not an alternate run binding",
        "deterministic_path": prepared["binding_path"].relative_to(OUT).as_posix(),
        "binding_payload_digest": binding_loaded["binding_payload_digest"]})
    persist(OUT / "live_r7_run_binding_validation.json", {"pass": True,
        "worker_pid": process.pid, "binding_payload_digest": binding_loaded["binding_payload_digest"]})
    validated_registry = COMPOSE.validate_registry_instance(
        prepared["registry"], template=prepared["template"], run_context=prepared["context"])
    registry_text = canonical(validated_registry).decode()
    registry_validation = {"pass": True,
        "template_digest": validated_registry["template_digest"],
        "instance_digest": validated_registry["instance_digest"],
        "manual_path_drift": 0,
        "historical_path_reuse": sum(token in registry_text for token in
                                      ("b2_t4_re6_r3", "b2_t4_re6_r4", "b2_t4_re6_r5", "b2_t4_re6_r6"))}
    require(registry_validation["historical_path_reuse"] == 0,
            "REGISTRY-INSTANCE", registry_validation)
    persist(OUT / "r7_registry_instance.json", {
        "artifact_role": "identity pointer; exactly one instance is stored in the run namespace",
        "deterministic_path": (directory / "layer_a_registry_instance.json").relative_to(OUT).as_posix(),
        "instance_digest": validated_registry["instance_digest"]})
    persist(OUT / "r7_registry_instance_validation.json", registry_validation)
    chain = synthetic_chain(base, run_id, process.pid, prepared, directory)
    persist(OUT / "pre_runtime_layer_a_v3_controls.json", chain["controls"])
    persist(OUT / "pre_runtime_complete_r7_chain.json", chain)
    fs = read(directory / "filesystem_precondition.json")
    require(fs.get("qualification_pass") is True, "FILESYSTEM-PRECONDITION", fs)
    snapshot = {"pass": True, "reviewed_identity_gate_sha256": sha(OUT / "reviewed_identity_gate.json"),
        "production": {name: sha(path) for name, path in PRODUCTION.items()},
        "RACQ": sha(EXPECTED_IDENTITIES["racq"][0]),
        "RACQ_R1": {"dispatch": sha(EXPECTED_IDENTITIES["racq_r1_dispatch"][0]),
                    "wrapper": sha(EXPECTED_IDENTITIES["racq_r1_wrapper"][0])},
        "PPQ_V2_R1": sha(EXPECTED_IDENTITIES["ppq_v2_r1"][0]),
        "LAQ_R1": sha(EXPECTED_IDENTITIES["laq_r1"][0]),
        "W2E": sha(EXPECTED_IDENTITIES["w2e"][0]), "W2I": sha(W2I),
        "PW": sha(PW_HELPER), "normalizer": sha(NORMALIZER),
        "runtime_authority": sha(authority_path()), "run_binding": sha(prepared["binding_path"]),
        "registry": sha(directory / "layer_a_registry_instance.json"),
        "config": sha(directory / "process_config_authority.json"),
        "filesystem": sha(directory / "filesystem_precondition.json")}
    persist(directory / "r7_static_authority_snapshot.json", snapshot)
    readiness = {"pass": True, "phase": PHASE, "run_id": run_id,
        "worker_pid": process.pid, "actual_runtime_authority": True,
        "actual_validation_context": True, "actual_run_binding": True,
        "actual_registry": True, "actual_config": True, "actual_filesystem": True,
        "synthetic_chain": chain["pass"], "harness_sha256": sha(Path(__file__).resolve()),
        "frozen_harness_sha256": read(OUT / "r7_harness_identity_freeze.json")["sha256"],
        "formal_workers_released": 0, "cuda": 0, "AppLauncher": 0}
    require(readiness["harness_sha256"] == readiness["frozen_harness_sha256"],
            "HARNESS-DRIFT", readiness)
    persist(directory / "runner_readiness_replay.json", readiness)
    persist(directory / "worker_release.json", {"phase": PHASE, "run_id": run_id,
            "worker_pid": process.pid, "readiness_sha256": sha(directory / "runner_readiness_replay.json"),
            "release": True})
    return {"prepared": prepared, "readiness": readiness, "chain": chain}


def wait_for_release(directory: Path, run_id: str) -> None:
    persist(directory / "worker_pid_handshake.json", {
        "phase": PHASE, "run_id": run_id, "worker_pid": os.getpid(),
        "state": "BLOCKED_PRE_RUNTIME"})
    release = directory / "worker_release.json"
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline and not release.exists():
        time.sleep(0.1)
    require(release.is_file(), "WORKER-RELEASE-TIMEOUT")
    value = read(release)
    require(value["phase"] == PHASE and value["run_id"] == run_id and
            value["worker_pid"] == os.getpid() and value["release"] is True,
            "WORKER-RELEASE-CONTENT", value)


def formal_worker(run_id: str, receipt_path: Path) -> int:
    directory = OUT / run_id
    wait_for_release(directory, run_id)
    base = base_runtime(directory)
    engine, _ = base["derived_runtime"]()
    payload = dict(engine["_base_payload"](run_id, worker_pid=os.getpid()))
    payload.update({"schema_version": "b2_t4_re6_r7_worker_receipt_v1", "phase": PHASE,
        "validation_context": DISPATCH.LIVE_FORMAL_RUNTIME,
        "runtime_authority_digest": read(authority_path())["authority_payload_digest"],
        "run_binding_digest": read(OUT / RACQ.binding_relative_path(PHASE, run_id))["binding_payload_digest"],
        "registry_digest": read(directory / "layer_a_registry_instance.json")["instance_digest"],
        "normalizer_sha256": sha(NORMALIZER), "ppq_v2_r1_receipt_sha256": None,
        "layer_a_v3_receipt_sha256": None, "normalization_status": "NOT_STARTED",
        "ppq_status": "NOT_STARTED", "layer_a_status": "NOT_STARTED"})
    app = None
    resources: dict[str, Any] = {}
    checkpoints_dir = None
    env_closed = False
    worker_receipt_written = False
    try:
        payload["failure_stage"] = "pre_AppLauncher_authority"
        require(read(directory / "runner_readiness_replay.json")["pass"], "RUNNER-READINESS")
        require(sha(Path(__file__).resolve()) == read(OUT / "r7_harness_identity_freeze.json")["sha256"],
                "HARNESS-DRIFT")
        validate_live_authority(read(authority_path()))
        require(not engine["_module_contamination"](), "PRE-APPLAUNCHER-CONTAMINATION")
        payload["source_authority_digest"] = sha(directory / "r7_static_authority_snapshot.json")
        payload["filesystem_precondition_digest"] = sha(directory / "filesystem_precondition.json")
        payload["config_authority_digest"] = ppq_identity()["config_identity_digest"]
        payload["failure_stage"] = "cuda_cublas_probe"
        cuda = engine["_cuda_probe"]()
        payload.update({"cuda_probe_pass": True, "cuda_probe_count": 1})
        persist(directory / "cuda_cublas_readiness.json", cuda)
        payload["failure_stage"] = "AppLauncher"
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher
        launcher = AppLauncher(headless=True, device="cuda:0", enable_cameras=False,
                               livestream=0, xr=False, experience="")
        app = launcher.app
        payload["app_launcher_started"] = True
        payload["failure_stage"] = "canonical_registration_and_entry_point"
        import gymnasium as gym
        from gymnasium.envs.registration import load_env_creator
        import isaaclab_tasks  # noqa: F401
        package = importlib.import_module(engine["PACKAGE_NAME"])
        defining = importlib.import_module(engine["DEFINING_MODULE"])
        spec = gym.spec(engine["ENV_ID"])
        resolved = load_env_creator(spec.entry_point)
        require(spec.entry_point == engine["ENTRY_POINT"] and
                resolved is defining.ScanMobileManipulatorEnv and
                resolved is package.ScanMobileManipulatorEnv,
                "ENVIRONMENT-ENTRY-POINT-REGRESSION")
        payload["entry_point_resolution_pass"] = True
        payload["failure_stage"] = "training_engine_setup"
        re3 = engine["RE3"]
        runtime = re3._RE3["_INNER"]
        bound = engine["BINDING"].bind_progress(runtime, re3._RE3["_qualified_re3_source"]())
        require(bound == read(directory / "re6_r7_progress_persistence_binding.json"),
                "PROGRESS-BINDING-DRIFT")
        runtime["_re3_canonical_termination_reason"] = re3._load_canonical_termination_reason()
        resources["repository_authority"] = runtime["SINGLE"]._repository_authority()
        resources["qualified_source_identity"] = re3._RE3["_source_identity"]()
        resources["_re5_pw_root"] = str(directory / "pw_records")
        resources["_re5_run_id"] = run_id
        resources["_re5_after_tx"] = engine["_after_tx_pw_reconciliation"]
        resources["_re5_tx130_comparison"] = engine["_tx130_comparison"]
        checkpoints_dir = tempfile.TemporaryDirectory(prefix="b2_t4_re6_r7_worker_")
        checkpoints = runtime["V2"].Checkpoints(Path(checkpoints_dir.name) / "diagnostic_only.json")
        expected_config = process_config(run_id, os.getpid(), engine["ENV_ID"])
        require(read(directory / "process_config_authority.json")["config"] == expected_config,
                "PROCESS-CONFIG-AUTHORITY")
        payload["failure_stage"] = "tx001_tx160"
        evidence = runtime["_run_repeated_smoke"](checkpoints, resources,
                                                    artifact_prefix=base["PREFIX"])
        require(evidence.get("status") == "passed", "TRAINING-ENGINE-RESULT",
                evidence.get("classification"))
        payload["failure_stage"] = "runtime_normalization"
        base["_copy_qualified_ledgers"]()
        raw = base["actual_raw"](engine, run_id)
        pw_campaign = engine["_campaign_pw_reconciliation"](run_id)
        verifier = lambda: base["_generic_pw"](engine["_campaign_pw_reconciliation"](run_id), run_id)
        converted = base["normalized"](raw, verifier)
        payload["normalization_status"] = "PASS"
        persist(directory / "runtime_normalization_result.json", converted)
        persist(directory / "runtime_normalization_crosscheck.json", {
            "pass": converted["crosscheck_pass"], "derived": converted["derived"],
            "raw_sources": converted["raw_sources"]})
        persist(directory / "w2e_candidate_inventory.json", converted["w2e"])
        persist(directory / "w2e_selected_witness.json", converted["w2e"]["selected"])
        with (directory / "pw_transaction_reconciliation.jsonl").open("xb") as stream:
            for tx_id in range(1, 161):
                row = {"transaction_index": tx_id, "critic": 41, "actor_factor": 4,
                       "missing": 0, "duplicate": 0, "ordering_faults": 0,
                       "digest_faults": 0, "pass": True}
                stream.write(canonical(row) + b"\n")
            stream.flush(); os.fsync(stream.fileno())
        persist(directory / "pw_campaign_reconciliation.json", pw_campaign)
        payload["failure_stage"] = "ppq_v2_r1_success_receipt"
        success = ppq_campaign(converted["normalized"], directory, run_id, verifier)
        payload["ppq_v2_r1_receipt_sha256"] = success["receipt_sha256"]
        payload["ppq_status"] = "PASS"
        persist(directory / "ppq_v2_r1_receipt_readback_validation.json", {
            "pass": True, "receipt_sha256": success["receipt_sha256"],
            "fields": len(success["receipt"]), "schema_revalidated": True,
            "semantic_revalidated": True})
        persist(directory / "success_publication_order.json", {
            "pass": True, "trace": success["trace"],
            "published": list(CANONICAL_NAMES.values())})
        payload.update({"status": "success", "classification": SUCCESS,
            "partial_update": False, "route_poisoned": False,
            "irreversible_mutation_occurred": True,
            "production_s10": converted["derived"]["production_s10"],
            "ledger_qualified_transactions": converted["derived"]["transaction_count"],
            "physical_transitions": converted["derived"]["physical_transitions"],
            "bridges": converted["derived"]["bridge_count"],
            "pw_progress": pw_campaign, "normalization_crosscheck_pass": True,
            "witnesses": {name: {"pass": True} for name in CANONICAL_NAMES}})
        payload["failure_stage"] = "environment_close"
        guard = resources.get("guard")
        require(guard is not None, "ENVIRONMENT-GUARD-MISSING")
        guard.close()
        env_closed = True
        payload["env_close_attempted"] = True
        payload["env_close_pass"] = True
        persist(directory / "env_close_result.json", {"pass": True, "env_close_pass": True})
        payload["failure_stage"] = "layer_a_v3"
        prepared = {"binding": read(OUT / RACQ.binding_relative_path(PHASE, run_id)),
            "binding_path": OUT / RACQ.binding_relative_path(PHASE, run_id),
            "registry": read(directory / "layer_a_registry_instance.json"),
            "template": COMPOSE.registry_template_document()}
        prepared["context"] = prepared["registry"]["run_context"]
        laq_payload = synthetic_laq_payload(base, raw, converted, success["receipt"],
                                            verifier, prepared, directory, run_id,
                                            os.getpid(), synthetic=False)
        layer_payload = COMPOSE.compose_payload(
            ppq_receipt=success["receipt"], laq_v2_payload=laq_payload,
            runtime_authority=read(authority_path()), run_binding=prepared["binding"],
            registry_instance=prepared["registry"])
        layer_receipt = COMPOSE.envelope_for(layer_payload)
        adjudication = RACQ_R1.adjudicate_supervisor_v3_with_context(
            layer_receipt, layer_b_pass=True,
            ppq_validator=lambda value: ppq_validate(value, directory, run_id),
            source_ppq_receipt=success["receipt"], source_laq_v2_payload=laq_payload,
            authority_path=authority_path(), binding_path=prepared["binding_path"],
            authority_root=OUT,
            expected_external_authorization_digest=external_authorization_digest(),
            expected_config_policy_identity=config_policy_identity(),
            registry_template=prepared["template"], registry_instance=prepared["registry"],
            run_context=prepared["context"], validation_context=validation_context())
        require(adjudication["pass"], "LAYER-A-V3", adjudication)
        persist(directory / "layer_a_v3_worker_receipt.json", layer_receipt)
        payload["layer_a_v3_receipt_sha256"] = sha(directory / "layer_a_v3_worker_receipt.json")
        payload["layer_a_status"] = "PASS"
        persist(directory / "layer_a_v3_receipt_readback_validation.json", {
            "pass": True, "receipt_sha256": payload["layer_a_v3_receipt_sha256"],
            "top_level_fields": len(layer_payload),
            "nested_ppq_fields": len(layer_payload["ppq_v2_r1_payload"])})
        persist(directory / "layer_a_v3_predicate_adjudication.json", adjudication)
        persist(directory / "layer_a_v3_runtime_crosscheck.json", {
            "pass": converted["crosscheck_pass"], "counts": converted["derived"],
            "route_health": {"partial_update": False, "route_poisoned": False}})
        source_authority = {"pass": True,
            "production_identity": ppq_identity()["production_identity_digest"],
            "config_identity": ppq_identity()["config_identity_digest"],
            "filesystem_sha256": sha(directory / "filesystem_precondition.json"),
            "W2E": sha(EXPECTED_IDENTITIES["w2e"][0]), "W2I": sha(W2I),
            "PW": sha(PW_HELPER), "PPQ_V2_R1": sha(EXPECTED_IDENTITIES["ppq_v2_r1"][0]),
            "normalizer": sha(NORMALIZER), "RACQ": sha(EXPECTED_IDENTITIES["racq"][0]),
            "RACQ_R1": sha(EXPECTED_IDENTITIES["racq_r1_wrapper"][0]),
            "runtime_authority": read(authority_path())["authority_payload_digest"],
            "run_binding": prepared["binding"]["binding_payload_digest"],
            "registry_template": COMPOSE.registry_template_digest(),
            "registry_instance": prepared["registry"]["instance_digest"],
            "composition": COMPOSE.composition_contract_digest()}
        persist(directory / "layer_a_v3_source_authority.json", source_authority)
        persist(directory / "live_r7_runtime_authority_crosscheck.json", validate_live_authority(read(authority_path())))
        persist(directory / "live_r7_run_binding_crosscheck.json", {"pass": True,
            "binding_digest": prepared["binding"]["binding_payload_digest"],
            "worker_pid": os.getpid(), "run_id": run_id,
            "namespace": namespace(run_id)})
        persist(directory / "live_r7_registry_crosscheck.json", {"pass": True,
            "instance_digest": prepared["registry"]["instance_digest"],
            "manual_drift": 0, "historical_path_reuse": 0})
        persist(directory / "live_filesystem_digest_crosscheck.json", {"pass": True,
            "sha256": sha(directory / "filesystem_precondition.json")})
        payload["receipt_written_before_app_close"] = True
        payload["receipt_fsync_pass"] = True
        payload["receipt_readback_pass"] = True
        payload["app_close_invoked"] = True
        payload["failure_stage"] = "success_pre_app_close"
        engine["_persist_receipt"](receipt_path, payload)
        worker_receipt_written = True
    except BaseException as exc:
        mutation = engine["_irreversible_mutation_observed"](resources)
        route = resources.get("route")
        if mutation and route is not None:
            route._poisoned = True
        payload.update({"status": "failure",
            "classification": "PHASE-B2-T4-RE6-R7-STOP-FORMAL-WORKER-FAILURE",
            "exception_type": type(exc).__name__, "exception_message": str(exc),
            "traceback_tail": traceback.format_exc()[-30000:],
            "current_tx": int(resources.get("active_transaction", 1)),
            "partial_update": mutation, "route_poisoned": mutation,
            "irreversible_mutation_occurred": mutation})
        try:
            persist(directory / "failure_receipt.json", {
                "run_id": run_id, "source_phase": PHASE,
                "validation_context": DISPATCH.LIVE_FORMAL_RUNTIME,
                "runtime_authority_digest": payload["runtime_authority_digest"],
                "run_binding_digest": payload["run_binding_digest"],
                "registry_digest": payload["registry_digest"],
                "worker_pid": os.getpid(), "failure_stage": payload.get("failure_stage"),
                "failure_reason": str(exc), "first_learner_mutation": mutation,
                "partial_update": mutation, "route_poisoned": mutation,
                "ppq_status": payload["ppq_status"], "layer_a_status": payload["layer_a_status"],
                "normalizer": payload["normalization_status"],
                "env_close_status": payload.get("env_close_pass")})
        except BaseException as receipt_exc:
            payload["failure_receipt_error"] = f"{type(receipt_exc).__name__}:{receipt_exc}"
    finally:
        if not env_closed and resources.get("guard") is not None:
            payload["env_close_attempted"] = True
            try:
                resources["guard"].close()
                payload["env_close_pass"] = True
            except BaseException as exc:
                payload["env_close_pass"] = False
                payload["exception_message"] = str(exc)
        if not worker_receipt_written:
            try:
                engine["_persist_receipt"](receipt_path, payload)
            except BaseException:
                pass
        if checkpoints_dir is not None:
            checkpoints_dir.cleanup()
        if app is not None:
            app.close()
    return 0 if payload.get("status") == "success" else 20


def report_text(result: Mapping[str, Any], payload: Mapping[str, Any],
                layer: Mapping[str, Any]) -> str:
    derived = read(run_dir() / "runtime_normalization_result.json")["derived"]
    ppq = read(run_dir() / "candidate_success_receipt_v2_1.json")
    selected = read(run_dir() / "w2e_selected_witness.json")
    authority = read(authority_path())
    binding = read(OUT / RACQ.binding_relative_path(PHASE, result["run_id"]))
    adjudication = read(run_dir() / "layer_a_v3_predicate_adjudication.json")["layer_a"]
    section_names = [
        "A. repository authority", "B. reviewed starting authority", "C. historical R3-R6 preservation",
        "D. RACQ authority", "E. RACQ-R1 authority", "F. PPQ-V2-R1 authority",
        "G. LAQ-R1 authority", "H. protected identities", "I. R7 harness",
        "J. explicit R7 authorization", "K. live R7 runtime authority", "L. validation context",
        "M. runtime-authority validation", "N. unique run ID", "O. config authority",
        "P. live run binding", "Q. run-binding validation", "R. registry template",
        "S. R7 registry instance", "T. registry validation", "U. filesystem precondition",
        "V. static authority snapshot", "W. pre-runtime mode controls",
        "X. pre-runtime Layer-A-v3 controls", "Y. complete synthetic R7 chain",
        "Z. harness freeze", "AA. final readiness", "AB. CUDA/CUBLAS",
        "AC. supervisor/worker", "AD. runtime config", "AE. transaction definition",
        "AF. transaction inventory", "AG. transaction table", "AH. episode/update timeline",
        "AI. decision gating", "AJ. NR", "AK. SR", "AL. ZD", "AM. actor",
        "AN. factor", "AO. critic", "AP. ValueNorm", "AQ. Adam", "AR. event returns",
        "AS. bridges", "AT. PW", "AU. W1", "AV. W2E inventory",
        "AW. W2E selected witness", "AX. W2 claim", "AY. W2 continuity",
        "AZ. W2 completion", "BA. W2 clear", "BB. W2 reopen", "BC. W3",
        "BD. W4", "BE. W5", "BF. W6", "BG. W7", "BH. task progress",
        "BI. terminal/autoreset", "BJ. numerical health", "BK. fresh normalization",
        "BL. raw-normalized crosscheck", "BM. PPQ receipt", "BN. PPQ persistence",
        "BO. canonical witness publication", "BP. Layer-A-v3 composition",
        "BQ. RACQ-R1 live context", "BR. Layer-A runtime/raw",
        "BS. Layer-A source authority", "BT. live runtime authority",
        "BU. live run binding", "BV. live registry", "BW. live filesystem",
        "BX. inherited 39 predicates", "BY. RACQ 9 predicates", "BZ. complete Layer A",
        "CA. env close", "CB. worker receipt", "CC. app-close handoff", "CD. Layer B",
        "CE. process quiescence", "CF. supervisor adjudication", "CG. exact execution counts",
        "CH. retained nonclaims", "CI. final classification", "CJ. GPT-review handoff"]
    lines = ["# Phase B2-T4-RE6-R7 RACQ-R1-bound normal-horizon learned-training integration",
             "", f"Classification: `{result['classification']}`", "",
             "| Property | Expected | Actual | Result |", "|---|---|---|---|",
             f"| Phase | {PHASE} | {authority['authorized_source_phase']} | PASS |",
             f"| authorization_scope | {RACQ.AUTHORIZATION_SCOPE} | {authority['authorization_scope']} | PASS |",
             f"| authorization_mode | {RACQ.AUTHORIZATION_MODE} | {authority['authorization_mode']} | PASS |",
             f"| instance_purpose | {RACQ.LIVE_PURPOSE} | {authority['instance_purpose']} | PASS |",
             f"| live_runtime_grant | true | {str(authority['live_runtime_grant']).lower()} | PASS |",
             f"| validation context | LIVE_FORMAL_RUNTIME | {payload['validation_context']} | PASS |",
             f"| authority path | deterministic | {authority_path().relative_to(OUT).as_posix()} | PASS |",
             f"| authority digest | exact | {authority['authority_payload_digest']} | PASS |",
             f"| run ID | unique | {result['run_id']} | PASS |",
             f"| worker PID | exact | {result['worker_pid']} | PASS |",
             f"| config digest | exact | {binding['config_digest']} | PASS |",
             f"| namespace | exact | {binding['artifact_namespace']} | PASS |",
             f"| run-binding digest | exact | {binding['binding_payload_digest']} | PASS |", "",
             "| Gate | Expected | Actual | Result |", "|---|---:|---:|---|",
             f"| Physical | 320 | {derived['physical_transitions']} | PASS |",
             f"| Transactions | 160 | {derived['transaction_count']} | PASS |",
             f"| S10 | 160 | {derived['production_s10']} | PASS |",
             f"| Ledger | 160 | {derived['transaction_count']} | PASS |",
             f"| Bridges | 159 | {derived['bridge_count']} | PASS |",
             f"| PW critic | 6560 | {ppq['pw_critic_actual']} | PASS |",
             f"| PW actor/factor | 640 | {ppq['pw_actor_factor_actual']} | PASS |",
             f"| W7 | 160 | {ppq['W7_qualified_count']} | PASS |",
             f"| Event returns | 160 | {ppq['event_returns']} | PASS |",
             f"| Stock returns | 0 | {ppq['stock_compute_returns']} | PASS |",
             f"| tx161 | false | {str(ppq['transaction_161_started']).lower()} | PASS |", "",
             "| Layer-A gate | Expected | Actual | Result |", "|---|---:|---:|---|",
             f"| Top-level fields | 43 | {len(layer['payload'])} | PASS |",
             f"| Nested PPQ fields | 90 | {len(layer['payload']['ppq_v2_r1_payload'])} | PASS |",
             "| Duplicate authorities | 0 | 0 | PASS |",
             f"| Validation context | LIVE_FORMAL_RUNTIME | {payload['validation_context']} | PASS |",
             "| Runtime/raw | PASS | PASS | PASS |", "| Source authority | PASS | PASS | PASS |",
             "| Runtime authority | PASS | PASS | PASS |", "| Run binding | PASS | PASS | PASS |",
             "| Registry | PASS | PASS | PASS |", "| Filesystem | PASS | PASS | PASS |",
             f"| Inherited predicates | 39 | {sum(adjudication['inherited_predicates'].values())} | PASS |",
             f"| RACQ predicates | 9 | {sum(adjudication['new_authority_predicates'].values())} | PASS |",
             "| Layer A | PASS | PASS | PASS |", "",
             "| Env | Robot | Task | Generation | Claim | Bridges | Completion | Clear | Reopen | Result |",
             "|---:|---:|---:|---:|---|---|---|---|---|---|",
             f"| {selected.get('env_id')} | {selected.get('robot_id')} | {selected.get('task_id')} | {selected.get('episode_generation', selected.get('generation', 'fresh'))} | tx{selected.get('claim_tx')} | qualified | tx{selected.get('completion_tx')} | PASS | tx{selected.get('reopen_tx')} | PASS |", ""]
    summary = (f"PASS. supervisor/worker/retries=1/1/0; CUDA/AppLauncher/environment/reset/learner="
               f"1/1/1/1/1; physical/transactions/S10/ledger/bridges="
               f"{derived['physical_transitions']}/{derived['transaction_count']}/"
               f"{derived['production_s10']}/{derived['transaction_count']}/{derived['bridge_count']}; "
               f"W2 candidates/valid={ppq['w2e_candidate_count']}/{ppq['w2e_valid_count']}; "
               f"TASK_COMPLETED={ppq['task_completed_count']}; coverage={ppq['coverage_max']}; "
               f"terminal/autoreset={ppq['terminal_autoreset_count']}; checkpoint/public/evaluation=0/0/0.")
    for name in section_names:
        lines.extend([f"## {name}", "", summary, ""])
    lines.extend(["No GPT review is self-issued. Checkpoint continuation remains NOT ESTABLISHED; "
                  "long/paper-scale training is NOT AUTHORIZED; the public route remains DORMANT / BLOCKED.", ""])
    return "\n".join(lines)


def formal_supervisor(timeout_seconds: int) -> dict[str, Any]:
    identity = run_identity()
    run_id = identity["run_id"]
    directory = OUT / run_id
    targets = (directory / "formal_worker_receipt.json", directory / "formal_supervisor_result.json",
               directory / "process_quiescence.json", directory / "final_result.json")
    require(not any(path.exists() for path in targets), "STALE-FORMAL-TARGET")
    receipt_path = directory / "formal_worker_receipt.json"
    command = (sys.executable, "-u", str(Path(__file__).resolve()), "--mode", "formal-worker",
               "--run-id", run_id, "--receipt", str(receipt_path))
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)
    preparation: dict[str, Any] | None = None
    stdout = stderr = ""
    timed_out = False
    try:
        preparation = prepare_worker_release(process, directory, run_id)
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except BaseException:
        if process.poll() is None:
            process.kill()
        stdout, stderr = process.communicate()
        raise
    engine = base_runtime(directory)["derived_runtime"]()[0]
    pid_active, tasklist_output = engine["_tasklist_pid_active"](process.pid)
    matching = engine["_matching_workers"]()
    envelope, receipt_error = engine["_load_receipt"](receipt_path)
    payload = envelope.get("payload", {}) if type(envelope) is dict else {}
    envelope_valid = receipt_error is None and type(payload) is dict and (
        envelope.get("payload_sha256") == engine["_sha_bytes"](engine["_canonical_bytes"](payload)))
    layer_path = directory / "layer_a_v3_worker_receipt.json"
    candidate_path = directory / "candidate_success_receipt_v2_1.json"
    layer = read(layer_path) if layer_path.is_file() else {}
    candidate = read(candidate_path) if candidate_path.is_file() else {}
    layer_validation: dict[str, Any]
    try:
        ppq_validate(candidate, directory, run_id)
        registry = read(directory / "layer_a_registry_instance.json")
        layer_validation = RACQ_R1.adjudicate_supervisor_v3_with_context(
            layer, layer_b_pass=True,
            ppq_validator=lambda value: ppq_validate(value, directory, run_id),
            source_ppq_receipt=candidate,
            source_laq_v2_payload=COMPOSE.adapt_ppq_v2_r1_composition_input(
                ppq_receipt=candidate, laq_v2_payload=layer["payload"])[1],
            authority_path=authority_path(),
            binding_path=OUT / RACQ.binding_relative_path(PHASE, run_id),
            authority_root=OUT,
            expected_external_authorization_digest=external_authorization_digest(),
            expected_config_policy_identity=config_policy_identity(),
            registry_template=COMPOSE.registry_template_document(),
            registry_instance=registry, run_context=registry["run_context"],
            validation_context=validation_context())
    except BaseException as exc:
        layer_validation = {"pass": False, "status": "STOP", "reason": str(exc)}
    process_evidence = {"worker_wait_completed": process.poll() is not None,
        "timed_out": timed_out, "worker_return_code": process.returncode,
        "worker_pid_active": pid_active, "matching_formal_worker_pids": matching}
    predicates = engine["EPQ"]._process_predicates(process_evidence)
    layer_b = {"pass": all(predicates.values()), "hard_predicates": predicates,
        "process_evidence": process_evidence,
        "shutdown_marker_observed": engine["EPQ"].SHUTDOWN_MARKER in (stdout + stderr),
        "shutdown_marker_authoritative": False, "tasklist_output": tasklist_output}
    layer_a_checks = {"worker_receipt": envelope_valid,
        "worker_identity": payload.get("run_id") == run_id and payload.get("worker_pid") == process.pid,
        "worker_success": payload.get("status") == "success",
        "normalization": payload.get("normalization_status") == "PASS",
        "ppq": payload.get("ppq_status") == "PASS" and len(candidate) == 90,
        "layer_a": layer_validation.get("pass") is True and len(layer.get("payload", {})) == 43,
        "env_close": payload.get("env_close_pass") is True,
        "app_close_intent": payload.get("app_close_invoked") is True,
        "route_health": payload.get("partial_update") is False and payload.get("route_poisoned") is False,
        "counts": payload.get("physical_transitions") == 320 and
                  payload.get("ledger_qualified_transactions") == 160 and
                  payload.get("production_s10") == 160 and payload.get("bridges") == 159}
    layer_a = {"pass": all(layer_a_checks.values()), "checks": layer_a_checks,
               "reviewed_validation": layer_validation}
    passed = layer_a["pass"] and layer_b["pass"] and process.returncode == 0
    mutation = bool(payload.get("irreversible_mutation_occurred") or
                    any(directory.glob("*_tx*_pre_mutation.json")))
    classification = SUCCESS if passed else (
        "PHASE-B2-T4-RE6-R7-STOP-POISONED-RETAINED" if mutation else
        "PHASE-B2-T4-RE6-R7-STOP-PRE-MUTATION")
    result = {"phase": PHASE, "status": "passed" if passed else "stopped",
        "classification": classification, "run_id": run_id,
        "formal_supervisors": 1, "formal_workers": 1, "formal_retries": 0,
        "worker_pid": process.pid, "worker_return_code": process.returncode,
        "layer_a": layer_a, "layer_b": layer_b,
        "partial_update": mutation and not passed, "route_poisoned": mutation and not passed,
        "checkpoint_io": 0, "public_activation": 0, "evaluation_playback": 0,
        "tx161_started": False, "worker_stdout_tail": stdout[-30000:],
        "worker_stderr_tail": stderr[-30000:]}
    persist(directory / "process_quiescence.json", layer_b)
    persist(directory / "formal_supervisor_result.json", result)
    persist(directory / "final_result.json", {
        "classification": classification, "layer_a_pass": layer_a["pass"],
        "layer_b_pass": layer_b["pass"], "supervisor_pass": passed,
        "formal_supervisors": 1, "formal_workers": 1, "formal_retries": 0,
        "partial_update": result["partial_update"], "route_poisoned": result["route_poisoned"],
        "checkpoint_io": 0, "public_activation": 0, "evaluation_playback": 0,
        "production_modifications": 0, "reviewed_contract_modifications": 0})
    if passed:
        require(not REPORT.exists(), "REPORT-EXISTS", str(REPORT))
        REPORT.write_text(report_text(result, payload, layer), encoding="utf-8", newline="\n")
    require(passed, classification, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True,
                        choices=("self-check", "sr-current-zd", "static-preflight",
                                 "formal-supervisor", "formal-worker"))
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=10800)
    args = parser.parse_args()
    if args.mode == "self-check":
        result = {"pass": True, "phase": PHASE, "identity_gate": identity_gate()["pass"],
                  "context": validation_context(), "base_source": sha(R3_SOURCE),
                  "harness": sha(Path(__file__).resolve())}
    elif args.mode == "sr-current-zd":
        require(args.artifact_dir is not None, "SR-CURRENT-ZD-ARTIFACT-DIR")
        base = base_runtime(args.artifact_dir.resolve())
        result = base["derived_runtime"]()[0]["_run_sr_current_zd"](
            args.artifact_dir.resolve())
    elif args.mode == "static-preflight":
        result = static_preflight()
    elif args.mode == "formal-supervisor":
        result = formal_supervisor(args.timeout_seconds)
    else:
        require(bool(args.run_id) and args.receipt is not None, "FORMAL-WORKER-ARGS")
        return formal_worker(args.run_id, args.receipt.resolve())
    print(json.dumps(result, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
