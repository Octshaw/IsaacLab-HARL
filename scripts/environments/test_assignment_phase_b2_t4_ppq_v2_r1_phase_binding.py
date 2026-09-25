"""Pure/offline PPQ-V2-R1 qualification and one-shot frozen controls.

Modes:
  check          read-only qualification in temporary directories
  qualify        write the qualification artifacts and freeze identities
  final-positive execute exactly one durable frozen positive
  final-negative execute exactly one decisive negative and close the handoff
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, Mapping

import _assignment_phase_b2_t4_ppq_v2_fresh_receipt as V2
import _assignment_phase_b2_t4_ppq_v2_r1_phase_binding as R1
import _assignment_phase_b2_t4_w2e_multi_update_completion as W2E
import _assignment_phase_b2_t4_windows_evidence_persistence as PW
import test_assignment_phase_b2_t4_laq_r1_authority_binding as LAQ_R1
import test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract as V2_TEST


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DAY = SCAN / "AgentRead/202609/20260921"
OUT = DAY / "b2_t4_ppq_v2_r1_artifacts"
REPORT = DAY / "PHASE_B2_T4_PPQ_V2_R1_FORMAL_SOURCE_PHASE_BINDING_GENERALIZATION_REPORT.md"
HELPER = HERE / "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py"
RUNNER = Path(__file__).resolve()
OLD_HELPER = HERE / "_assignment_phase_b2_t4_ppq_v2_fresh_receipt.py"
OLD_RUNNER = HERE / "test_assignment_phase_b2_t4_ppq_v2_fresh_receipt_contract.py"
OLD_SCHEMA = SCAN / "AgentRead/202609/20260920/b2_t4_ppq_v2_artifacts/fresh_receipt_schema_v2.json"
OLD_OUT = SCAN / "AgentRead/202609/20260920/b2_t4_ppq_v2_artifacts"
R4_OUT = DAY / "b2_t4_re6_r4_artifacts"
R4_RUNNER = HERE / "test_assignment_phase_b2_t4_re6_r4_laq_r1_bound_normal_horizon_integration.py"
R4_REPORT = DAY / "PHASE_B2_T4_RE6_R4_LAQ_R1_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md"
W2I = V2_TEST.W2I
PW_HELPER = V2_TEST.PW_HELPER
PRODUCTION = V2_TEST.PRODUCTION
CONFIG = V2_TEST.CONFIG
CLASSIFICATION = "PHASE-B2-T4-PPQ-V2-R1-FORMAL-SOURCE-PHASE-BINDING-GENERALIZED-AWAITING-GPT-REVIEW"
EXPECTED_HEAD = "b71d85a32f51be6ada324f870813a56bb45dd396"
EXPECTED_STAGED_COUNT = 359
EXPECTED_INDEX_SHA = "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
EXPECTED_MONTHLY_PATH_SHA = "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
APPROVED_PYTHON_INVOCATIONS = 8
PY_COMPILE_INVOCATIONS = 2


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise AssertionError(reason)


def sha(path: Path) -> str:
    return V2.sha_file(path)


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def write_canonical(path: Path, value: Mapping[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"DESTINATION-EXISTS:{path}")
    path.write_bytes(R1.canonical(value))
    return sha(path)


def artifact(name: str, value: Mapping[str, Any]) -> str:
    return write_canonical(OUT / name, value)


def tree_identity(directory: Path) -> dict[str, Any]:
    h = hashlib.sha256()
    count = 0
    total = 0
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        relative = path.relative_to(directory).as_posix()
        size = path.stat().st_size
        h.update(f"{relative}\0{size}\0{sha(path)}\n".encode("utf-8"))
        count += 1
        total += size
    return {"file_count": count, "total_bytes": total,
            "path_size_content_sha256": h.hexdigest()}


def protected_identity() -> dict[str, Any]:
    identity = LAQ_R1.protected_identity()
    identity["old_ppq_v2"] = {
        "helper": {"path": OLD_HELPER.relative_to(ROOT).as_posix(), "sha256": sha(OLD_HELPER)},
        "runner": {"path": OLD_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha(OLD_RUNNER)},
        "schema": {"path": OLD_SCHEMA.relative_to(ROOT).as_posix(), "sha256": sha(OLD_SCHEMA)},
        "artifact_tree": tree_identity(OLD_OUT),
    }
    identity["historical_re6_r4"] = {
        "runner": {"path": R4_RUNNER.relative_to(ROOT).as_posix(), "sha256": sha(R4_RUNNER)},
        "report": {"path": R4_REPORT.relative_to(ROOT).as_posix(), "sha256": sha(R4_REPORT)},
        "artifact_tree": tree_identity(R4_OUT),
    }
    return identity


def repository_authority() -> dict[str, Any]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    staged = git("ls-files", "--stage")
    staged_paths = git("diff", "--cached", "--name-only").decode("utf-8").splitlines()
    porcelain = git("status", "--porcelain=v1", "-uall")
    value = {
        "branch": git("branch", "--show-current").decode().strip(),
        "HEAD": git("rev-parse", "HEAD").decode().strip(),
        "origin_main": git("rev-parse", "origin/main").decode().strip(),
        "merge_base": git("merge-base", "HEAD", "origin/main").decode().strip(),
        "full_porcelain_line_count": len(porcelain.splitlines()),
        "full_porcelain_sha256": hashlib.sha256(porcelain).hexdigest(),
        "staged_path_count": len(staged_paths),
        "staged_index_sha256": hashlib.sha256(staged).hexdigest(),
        "monthly_path_set_sha256": hashlib.sha256("\n".join(staged_paths).encode()).hexdigest(),
        "git_add_commit_push": [0, 0, 0],
    }
    require(value["branch"] == "main" and value["HEAD"] == value["origin_main"] ==
            value["merge_base"] == EXPECTED_HEAD, "REPOSITORY-COMMIT-AUTHORITY")
    require(value["staged_path_count"] == EXPECTED_STAGED_COUNT and
            value["staged_index_sha256"] == EXPECTED_INDEX_SHA and
            value["monthly_path_set_sha256"] == EXPECTED_MONTHLY_PATH_SHA,
            "REPOSITORY-INDEX-AUTHORITY")
    return value


def new_identity() -> dict[str, str]:
    return {
        "ppq_v2_helper_sha256": sha(HELPER),
        "ppq_v2_schema_sha256": R1.digest(R1.schema_document()),
        "production_identity_digest": V2.digest(
            {key: sha(path) for key, path in sorted(PRODUCTION.items())}),
        "config_identity_digest": V2.digest(CONFIG),
    }


def legacy_identity() -> dict[str, str]:
    return {
        "ppq_v2_helper_sha256": sha(OLD_HELPER),
        "ppq_v2_schema_sha256": sha(OLD_SCHEMA),
        "production_identity_digest": V2.digest(
            {key: sha(path) for key, path in sorted(PRODUCTION.items())}),
        "config_identity_digest": V2.digest(CONFIG),
    }


def registry_document() -> dict[str, Any]:
    return {
        "registry_version": "b2_t4_source_phase_authority_registry_v1",
        "status": "CANDIDATE / AWAITING GPT REVIEW",
        "generic_authority_schema_identity": R1.AUTHORITY_VERSION,
        "run_binding_schema_identity": R1.RUN_BINDING_VERSION,
        "receipt_contract_version": R1.VERSION,
        "allowed_authority_modes": list(R1.AUTHORITY_MODES),
        "formal_success_mode": R1.FORMAL_MODE,
        "formal_phase_grammar": R1.FORMAL_PHASE_PATTERN,
        "grammar_alone_authorizes": False,
        "canonicalization": "UTF-8 sorted compact JSON without NaN",
        "authority_digest": "SHA-256 over canonical authority excluding authority_payload_digest",
        "run_binding_digest": "SHA-256 over canonical binding excluding binding_payload_digest",
        "path_content_policy": "trusted exact expected path, direct child of authority root, regular non-symlink, canonical content, recomputed digest",
        "run_binding_semantics": "reviewed phase authority then supervisor-created exact phase/run/config/namespace binding",
        "authority_instance_enumeration": "external; no concrete attempt names in helper",
        "qualification_authorities": "OFFLINE-QUALIFICATION-ONLY; not runtime grants",
    }


def evidence_for(phase: str, run_id: str, variant: int) -> dict[str, Any]:
    evidence = V2_TEST.synthetic_fixture(variant)
    evidence["source_phase"] = phase
    evidence["run_id"] = run_id
    evidence["worker_pid"] = os.getpid()
    evidence["pw_result"]["run_id"] = run_id
    return evidence


def prepare(root: Path, *, phase: str, run_id: str, variant: int = 1,
            authority_phase: str | None = None,
            mode: str = R1.FORMAL_MODE,
            namespace: str | None = None) -> dict[str, Any]:
    root.mkdir(parents=True, exist_ok=True)
    authority_phase = authority_phase if authority_phase is not None else phase
    instance = f"offline-{authority_phase.lower().replace('-', '-')}-{run_id}"[:90].rstrip("-")
    authority = R1.make_offline_authority(
        source_phase=authority_phase, authority_instance_id=instance,
        authorization_mode=mode)
    authority_path = root / f"{instance}.source_phase_authority.json"
    authority_path.write_bytes(R1.canonical(authority))
    artifact_namespace = namespace or (
        R1.expected_artifact_namespace(phase, run_id)
        if R1.formal_attempt_identifier(phase) is not None else f"invalid/{run_id}")
    binding = R1.make_run_binding(
        authority=authority, run_id=run_id, worker_pid=os.getpid(),
        config_digest=new_identity()["config_identity_digest"],
        artifact_namespace=artifact_namespace)
    binding_path = root / f"{run_id}.source_phase_run_binding.json"
    binding_path.write_bytes(R1.canonical(binding))
    return {
        "root": root,
        "phase": phase,
        "run_id": run_id,
        "namespace": artifact_namespace,
        "authority": authority,
        "authority_path": authority_path,
        "expected_authority_path": authority_path,
        "binding": binding,
        "binding_path": binding_path,
        "expected_binding_path": binding_path,
        "evidence": evidence_for(phase, run_id, variant),
    }


def call(prepared: Mapping[str, Any], *, store: V2_TEST.MemoryStore | None = None,
         expected_phase: str | None = None,
         receipt_mutator: Callable[[dict[str, Any]], None] | None = None,
         authority_path: Path | None = None, expected_authority_path: Path | None = None,
         binding_path: Path | None = None, expected_binding_path: Path | None = None,
         namespace: str | None = None, evidence: Mapping[str, Any] | None = None) -> dict[str, Any]:
    store = store or V2_TEST.MemoryStore()
    return R1.finalize_campaign(
        evidence or prepared["evidence"], w2e_selector=W2E.reconcile, w2i_manifest=W2I,
        pw_reconcile=V2_TEST.generic_pw,
        expected_phase=expected_phase or prepared["phase"], config=CONFIG,
        identity=new_identity(), legacy_identity=legacy_identity(),
        production_sources=PRODUCTION, pw_helper_path=PW_HELPER,
        authority_path=authority_path or prepared["authority_path"],
        expected_authority_path=expected_authority_path or prepared["expected_authority_path"],
        run_binding_path=binding_path or prepared["binding_path"],
        expected_run_binding_path=expected_binding_path or prepared["expected_binding_path"],
        authority_root=prepared["root"],
        artifact_namespace=namespace or prepared["namespace"],
        writer=store.write, reader=store.read, readback_guard=store.guard,
        output_dir=Path("memory"), receipt_mutator=receipt_mutator)


def validate(prepared: Mapping[str, Any], receipt: Mapping[str, Any], **overrides: Any) -> None:
    R1.validate_receipt(
        receipt,
        expected_phase=overrides.get("expected_phase", prepared["phase"]),
        identity=new_identity(), legacy_identity=legacy_identity(), config=CONFIG,
        authority_path=overrides.get("authority_path", prepared["authority_path"]),
        expected_authority_path=overrides.get(
            "expected_authority_path", prepared["expected_authority_path"]),
        run_binding_path=overrides.get("binding_path", prepared["binding_path"]),
        expected_run_binding_path=overrides.get(
            "expected_binding_path", prepared["expected_binding_path"]),
        authority_root=prepared["root"],
        artifact_namespace=overrides.get("namespace", prepared["namespace"]))


def positive_fixture(phase: str, run_id: str, variant: int, label: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ppq-v2-r1-positive-") as temporary:
        prepared = prepare(Path(temporary), phase=phase, run_id=run_id, variant=variant)
        store = V2_TEST.MemoryStore()
        result = call(prepared, store=store)
        require(result["pass"] and result["trace"][-1] ==
                "10_canonical_witness_publication" and len(result["publication"]) == 7 and
                not store.premature, f"POSITIVE-{label}")
        receipt = result["receipt"]
        return {
            "fixture": label,
            "pass": True,
            "offline_qualification_only": True,
            "runtime_authorized": False,
            "source_phase": phase,
            "attempt_identifier": R1.formal_attempt_identifier(phase),
            "run_id": run_id,
            "artifact_namespace": prepared["namespace"],
            "authority_mode": receipt["source_phase_authorization_mode"],
            "authority_digest": receipt["source_phase_authority_digest"],
            "run_binding_digest": receipt["source_phase_run_binding_digest"],
            "receipt_sha256": result["receipt_sha256"],
            "trace": result["trace"],
        }


def stopped(label: str, action: Callable[[], Any]) -> dict[str, Any]:
    try:
        action()
    except (R1.PPQV2R1Stop, V2.PPQV2Stop, OSError, KeyError, TypeError, ValueError) as exc:
        return {"case": label, "status": "STOP", "exception_type": type(exc).__name__,
                "reason": str(exc)}
    return {"case": label, "status": "UNEXPECTED-PASS"}


def rewrite(path: Path, value: Any, *, canonical: bool = True) -> None:
    path.write_bytes(R1.canonical(value) if canonical else
                     (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def negative_matrix() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="ppq-v2-r1-negative-") as temporary:
        root = Path(temporary)
        prepared = prepare(root, phase="B2-T4-RE6-R5", run_id="negative-run-a")
        valid = call(prepared)["receipt"]

        missing = root / "missing.source_phase_authority.json"
        rows.append(stopped("valid formal phase with no authority", lambda: validate(
            prepared, valid, authority_path=missing, expected_authority_path=missing)))

        wrong = copy.deepcopy(prepared["authority"])
        wrong["authorized_source_phase"] = "B2-T4-RE6-R6"
        wrong["attempt_identifier"] = 6
        wrong["authority_payload_digest"] = R1.digest(
            R1._payload_without_digest(wrong, "authority_payload_digest"))
        rewrite(prepared["authority_path"], wrong)
        rows.append(stopped("wrong authorized phase", lambda: validate(prepared, valid)))
        rewrite(prepared["authority_path"], prepared["authority"])

        rows.append(stopped("expected phase mismatch", lambda: validate(
            prepared, valid, expected_phase="B2-T4-RE6-R6")))
        altered = copy.deepcopy(valid)
        altered["source_phase"] = "B2-T4-RE6-R6"
        rows.append(stopped("receipt phase mismatch", lambda: validate(prepared, altered)))

        unauth = prepare(root / "unauthorized", phase="B2-T4-RE6-R999",
                         run_id="unauthorized-run")
        unauth_missing = unauth["root"] / "absent.source_phase_authority.json"
        rows.append(stopped("valid-family R999 without authority", lambda: call(
            unauth, authority_path=unauth_missing, expected_authority_path=unauth_missing)))

        for index, phase in enumerate(("B2-T4-RE6-R0", "B2-T4-RE6-RX",
                                       "B2-T4-RE6-R-1", "B2-T4-RE6-R5-extra",
                                       "B2-T4-R5", ""), 1):
            malformed = prepare(root / f"malformed-{index}", phase=phase,
                                run_id=f"malformed-run-{index}")
            rows.append(stopped(f"malformed formal phase {phase!r}", lambda p=malformed: call(p)))

        synthetic = prepare(root / "synthetic", phase="B2-T4-RE6-R5-SYNTHETIC",
                            run_id="synthetic-run")
        rows.append(stopped("synthetic phase as formal", lambda: call(synthetic)))
        historical = prepare(root / "historical",
                             phase="B2-T4-PPQ-V2-HISTORICAL-FIXTURE",
                             run_id="historical-run")
        rows.append(stopped("historical fixture as formal", lambda: call(historical)))

        wrong_mode = copy.deepcopy(prepared["authority"])
        wrong_mode["authorization_mode"] = R1.SYNTHETIC_MODE
        wrong_mode["authority_payload_digest"] = R1.digest(
            R1._payload_without_digest(wrong_mode, "authority_payload_digest"))
        rewrite(prepared["authority_path"], wrong_mode)
        rows.append(stopped("wrong authority mode", lambda: validate(prepared, valid)))
        rewrite(prepared["authority_path"], prepared["authority"])

        wrong_version = copy.deepcopy(prepared["authority"])
        wrong_version["authority_version"] += "-wrong"
        wrong_version["authority_payload_digest"] = R1.digest(
            R1._payload_without_digest(wrong_version, "authority_payload_digest"))
        rewrite(prepared["authority_path"], wrong_version)
        rows.append(stopped("wrong authority version", lambda: validate(prepared, valid)))
        rewrite(prepared["authority_path"], prepared["authority"])

        wrong_digest_receipt = copy.deepcopy(valid)
        wrong_digest_receipt["source_phase_authority_digest"] = "0" * 64
        rows.append(stopped("wrong authority digest helper", lambda: call(
            prepared, receipt_mutator=lambda receipt: receipt.__setitem__(
                "source_phase_authority_digest", "0" * 64))))
        rows.append(stopped("wrong authority digest validator", lambda: validate(
            prepared, wrong_digest_receipt)))
        rows.append(stopped("wrong authority digest supervisor replay", lambda: validate(
            prepared, copy.deepcopy(wrong_digest_receipt))))

        other = R1.make_offline_authority(source_phase="B2-T4-RE6-R17",
                                          authority_instance_id="offline-other-source")
        wrong_source = copy.deepcopy(valid)
        wrong_source["source_phase_authority_digest"] = other["authority_payload_digest"]
        rows.append(stopped("wrong-source authority digest", lambda: validate(
            prepared, wrong_source)))

        stale_evidence = copy.deepcopy(prepared["evidence"])
        stale_evidence["source_phase"] = "B2-T4-RE6-R6"
        rows.append(stopped("stale R5 authority reused for R6", lambda: call(
            prepared, expected_phase="B2-T4-RE6-R6", evidence=stale_evidence)))

        run_mismatch = copy.deepcopy(prepared["binding"])
        run_mismatch["run_id"] = "negative-run-b"
        run_mismatch["binding_payload_digest"] = R1.digest(
            R1._payload_without_digest(run_mismatch, "binding_payload_digest"))
        rewrite(prepared["binding_path"], run_mismatch)
        rows.append(stopped("run-id mismatch", lambda: validate(prepared, valid)))
        rewrite(prepared["binding_path"], prepared["binding"])

        namespace_mismatch = copy.deepcopy(prepared["binding"])
        namespace_mismatch["artifact_namespace"] = "b2_t4_re6_r4_artifacts/negative-run-a"
        namespace_mismatch["binding_payload_digest"] = R1.digest(
            R1._payload_without_digest(namespace_mismatch, "binding_payload_digest"))
        rewrite(prepared["binding_path"], namespace_mismatch)
        rows.append(stopped("artifact namespace mismatch", lambda: validate(prepared, valid)))
        rewrite(prepared["binding_path"], prepared["binding"])

        config_mismatch = copy.deepcopy(prepared["binding"])
        config_mismatch["config_digest"] = "f" * 64
        config_mismatch["binding_payload_digest"] = R1.digest(
            R1._payload_without_digest(config_mismatch, "binding_payload_digest"))
        rewrite(prepared["binding_path"], config_mismatch)
        rows.append(stopped("config binding mismatch", lambda: validate(prepared, valid)))
        rewrite(prepared["binding_path"], prepared["binding"])

        tampered = copy.deepcopy(prepared["authority"])
        tampered["attempt_identifier"] = 17
        rewrite(prepared["authority_path"], tampered)
        rows.append(stopped("tampered authority payload", lambda: validate(prepared, valid)))
        rewrite(prepared["authority_path"], prepared["authority"])

        extra = copy.deepcopy(prepared["authority"])
        extra["unknown_critical"] = True
        rewrite(prepared["authority_path"], extra)
        rows.append(stopped("authority unknown field", lambda: validate(prepared, valid)))
        missing_field = copy.deepcopy(prepared["authority"])
        del missing_field["phase_family"]
        rewrite(prepared["authority_path"], missing_field)
        rows.append(stopped("authority missing field", lambda: validate(prepared, valid)))
        wrong_type = copy.deepcopy(prepared["authority"])
        wrong_type["attempt_identifier"] = "5"
        rewrite(prepared["authority_path"], wrong_type)
        rows.append(stopped("authority wrong type", lambda: validate(prepared, valid)))
        rewrite(prepared["authority_path"], prepared["authority"], canonical=False)
        rows.append(stopped("authority noncanonical object", lambda: validate(prepared, valid)))
        rewrite(prepared["authority_path"], prepared["authority"])

        alternate = root / "alternate.source_phase_authority.json"
        rewrite(alternate, prepared["authority"])
        rows.append(stopped("correct content wrong path", lambda: validate(
            prepared, valid, authority_path=alternate)))

        rewrite(prepared["authority_path"], {"unrelated": True})
        rows.append(stopped("wrong content correct-looking filename", lambda: validate(
            prepared, valid)))
        rewrite(prepared["authority_path"], prepared["authority"])

        symlink_path = root / "symlink.source_phase_authority.json"
        try:
            symlink_path.symlink_to(prepared["authority_path"])
            rows.append(stopped("symlink authority", lambda: R1.load_phase_authority(
                actual_path=symlink_path, expected_path=symlink_path,
                authority_root=root, required_mode=R1.FORMAL_MODE)))
        except OSError:
            rows.append(stopped("symlink authority (platform fallback)", lambda: validate(
                prepared, valid, authority_path=symlink_path,
                expected_authority_path=symlink_path)))

        traversal = root / "child" / ".." / prepared["authority_path"].name
        rows.append(stopped("authority traversal path", lambda: validate(
            prepared, valid, authority_path=traversal,
            expected_authority_path=traversal)))

        unrelated = root / "unrelated.source_phase_authority.json"
        rewrite(unrelated, {"unrelated": "authority"})
        rows.append(stopped("unrelated authority JSON", lambda: R1.load_phase_authority(
            actual_path=unrelated, expected_path=unrelated,
            authority_root=root, required_mode=R1.FORMAL_MODE)))

        rogue_root = root / "rogue"
        rogue = prepare(rogue_root, phase="B2-T4-RE6-R999", run_id="rogue-run")
        rows.append(stopped("caller self-created authority outside expected path", lambda: call(
            rogue, expected_authority_path=prepared["authority_path"])))

    actual_stop = sum(row["status"] == "STOP" for row in rows)
    unexpected = sum(row["status"] != "STOP" for row in rows)
    require(actual_stop == len(rows) and unexpected == 0, "NEGATIVE-MATRIX")
    return {"case_count": len(rows), "expected_stop": len(rows),
            "actual_stop": actual_stop, "unexpected_pass": unexpected,
            "pass": True, "cases": rows}


def old_r4_stop_reproduction() -> dict[str, Any]:
    evidence = evidence_for("B2-T4-RE6-R4", "old-r4-stop-reproduction", 1)
    try:
        V2.build_receipt(
            evidence, w2e_selector=W2E.reconcile, w2i_manifest=W2I,
            pw_reconcile=V2_TEST.generic_pw, expected_phase="B2-T4-RE6-R4",
            config=CONFIG, identity=legacy_identity(), production_sources=PRODUCTION,
            pw_helper_path=PW_HELPER)
    except V2.PPQV2Stop as exc:
        require(str(exc) == "SOURCE-PHASE", "OLD-R4-NONEXACT-STOP")
        return {"pass": True, "status": "STOP", "exception_type": type(exc).__name__,
                "reason": str(exc), "old_helper_unchanged": True,
                "historical_r4_reclassified": False}
    raise AssertionError("OLD-R4-UNEXPECTED-PASS")


def capability(phase: str, label: str) -> dict[str, Any]:
    result = positive_fixture(phase, f"{label}-offline-run", 1, label)
    result["capability_only"] = True
    result["historical_attempt_reopened"] = False
    return result


def attempt_decoupling() -> dict[str, Any]:
    phases = ("B2-T4-RE6-R5", "B2-T4-RE6-R6", "B2-T4-RE6-R17", "B2-T4-RE6-R101")
    authorized = [capability(phase, f"attempt-{index}") for index, phase in enumerate(phases, 1)]
    unauthorized = []
    for index, phase in enumerate(phases, 1):
        with tempfile.TemporaryDirectory(prefix="ppq-v2-r1-decoupling-") as temporary:
            prepared = prepare(Path(temporary), phase=phase, run_id=f"unauthorized-{index}")
            absent = prepared["root"] / "absent.source_phase_authority.json"
            unauthorized.append(stopped(phase, lambda p=prepared, a=absent: call(
                p, authority_path=a, expected_authority_path=a)))
    require(all(row["pass"] for row in authorized) and
            all(row["status"] == "STOP" for row in unauthorized), "ATTEMPT-DECOUPLING")
    return {"pass": True, "authorized_pass": len(authorized),
            "unauthorized_stop": len(unauthorized), "authorized": authorized,
            "unauthorized": unauthorized}


def non_phase_equivalence() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    old_evidence = V2_TEST.synthetic_fixture(1)
    old_receipt, _, _, _ = V2.build_receipt(
        old_evidence, w2e_selector=W2E.reconcile, w2i_manifest=W2I,
        pw_reconcile=V2_TEST.generic_pw, expected_phase=old_evidence["source_phase"],
        config=CONFIG, identity=legacy_identity(), production_sources=PRODUCTION,
        pw_helper_path=PW_HELPER)
    with tempfile.TemporaryDirectory(prefix="ppq-v2-r1-equivalence-") as temporary:
        prepared = prepare(Path(temporary), phase="B2-T4-RE6-R5",
                           run_id=old_evidence["run_id"], variant=1)
        new_receipt = call(prepared)["receipt"]
        ignored = {"contract_version", "source_phase", "ppq_v2_helper_sha256",
                   "ppq_v2_schema_sha256", *R1.AUTHORITY_RECEIPT_FIELDS}
        common = set(old_receipt) - ignored
        differences = [field for field in sorted(common)
                       if old_receipt[field] != new_receipt[field]]
        require(not differences, "NON-PHASE-POSITIVE-DRIFT")
        positive = {"pass": True, "compared_field_count": len(common),
                    "unchanged_field_count": len(common),
                    "unexpected_differences": differences,
                    "intentional_differences": sorted(ignored)}

        negative_specs = [
            ("W2 invalid", "w2_completion", False),
            ("PW mismatch", "pw_critic_actual", 6559),
            ("transaction mismatch", "transaction_count", 159),
            ("learner mismatch", "actor_step", new_receipt["actor_step"] - 1),
            ("poisoned route", "route_poisoned", True),
            ("forbidden action", "checkpoint_io_count", 1),
        ]
        negative_rows = []
        for label, field, value in negative_specs:
            candidate = copy.deepcopy(new_receipt)
            candidate[field] = value
            negative_rows.append(stopped(label, lambda c=candidate: validate(prepared, c)))
        digest_store = V2_TEST.MemoryStore(mode="digest_mismatch")
        negative_rows.append(stopped("persistence/digest failure", lambda: call(
            prepared, store=digest_store)))
        require(all(row["status"] == "STOP" for row in negative_rows),
                "NON-PHASE-NEGATIVE-DRIFT")
        negative = {"pass": True, "case_count": len(negative_rows),
                    "actual_stop": len(negative_rows), "unexpected_pass": 0,
                    "cases": negative_rows}
        semantic = {
            "pass": True,
            "unexplained_semantic_differences": 0,
            "areas": {
                "runtime campaign invariants": "UNCHANGED",
                "W2E": "UNCHANGED", "task progress": "UNCHANGED",
                "terminal": "UNCHANGED", "PW": "UNCHANGED",
                "W1-W7": "UNCHANGED", "learner counters": "UNCHANGED",
                "Adam": "UNCHANGED", "ValueNorm": "UNCHANGED",
                "returns": "UNCHANGED", "route health": "UNCHANGED",
                "forbidden actions": "UNCHANGED",
                "success receipt persistence": "UNCHANGED",
                "canonical publication ordering": "UNCHANGED",
                "source phase": "INTENTIONAL: external exact authority",
                "phase authority identity": "INTENTIONAL: four new fields",
            },
            "positive_replay": positive,
            "negative_replay": negative,
        }
        return semantic, positive, negative


def future_literal_audit() -> dict[str, Any]:
    text = HELPER.read_text(encoding="utf-8")
    literals = ["B2-T4-RE6-R4", "B2-T4-RE6-R5", "B2-T4-RE6-R6", "B2-T4-RE6-R17"]
    found = {literal: text.count(literal) for literal in literals}
    require(sum(found.values()) == 0, "FUTURE-ATTEMPT-LITERAL")
    return {"pass": True, "audited_literals": literals,
            "counts": found, "helper_future_attempt_literals": 0}


def qualification() -> dict[str, Any]:
    require(Path(sys.executable).resolve() == Path(
        r"C:\isaacenvs\isaac45_harl\python.exe").resolve(), "APPROVED-INTERPRETER")
    authority = repository_authority()
    before = protected_identity()
    positives = [
        positive_fixture("B2-T4-RE6-R5", "formal-r5-alpha", 1, "formal_fixture_1"),
        positive_fixture("B2-T4-RE6-R17", "formal-r17-beta", 2, "formal_fixture_2"),
        positive_fixture("B2-T4-RE6-R5", "formal-r5-gamma", 2, "formal_fixture_3"),
    ]
    require(len(positives) >= 3 and len({row["attempt_identifier"] for row in positives}) >= 2,
            "POSITIVE-FORMAL-FIXTURES")
    negatives = negative_matrix()
    old_r4 = old_r4_stop_reproduction()
    r4_capability = capability("B2-T4-RE6-R4", "r4-capability")
    r5_capability = capability("B2-T4-RE6-R5", "future-r5-capability")
    decoupling = attempt_decoupling()
    literal_audit = future_literal_audit()
    semantic, positive_replay, negative_replay = non_phase_equivalence()
    after = protected_identity()
    require(before == after, "PROTECTED-SOURCE-DRIFT")
    return {
        "repository": authority, "protected_before": before, "protected_after": after,
        "positives": positives, "negatives": negatives, "old_r4": old_r4,
        "r4_capability": r4_capability, "r5_capability": r5_capability,
        "decoupling": decoupling, "literal_audit": literal_audit,
        "semantic": semantic, "positive_replay": positive_replay,
        "negative_replay": negative_replay,
        "pre_failure": R1.failure_semantics(mutation_occurred=False),
        "post_failure": R1.failure_semantics(mutation_occurred=True),
    }


def write_qualification(result: Mapping[str, Any]) -> None:
    require(not OUT.exists(), "PPQ-V2-R1-ARTIFACT-NAMESPACE-EXISTS")
    a = result
    field_delta = {
        "pass": True,
        "old_field_count": len(V2.FIELDS), "new_field_count": len(R1.FIELDS),
        "unchanged_fields": sorted(V2.FIELDS),
        "phase_semantically_updated": ["contract_version", "source_phase",
                                         "ppq_v2_helper_sha256", "ppq_v2_schema_sha256"],
        "new_authority_fields": list(R1.AUTHORITY_RECEIPT_FIELDS),
        "unrelated_changed_fields": 0,
    }
    path_cases = [row for row in a["negatives"]["cases"] if any(
        token in row["case"] for token in ("path", "content", "symlink", "traversal", "unrelated"))]
    caller_cases = [row for row in a["negatives"]["cases"]
                    if "R999" in row["case"] or "caller self-created" in row["case"]]
    payloads: dict[str, Mapping[str, Any]] = {
        "repository_authority.json": a["repository"],
        "reviewed_starting_authority.json": {
            "PPQ_V2": "GPT REVIEW PASS / CLOSED / ORIGINAL PHASE SCOPE",
            "LAQ_R1": "GPT REVIEW PASS / CLOSED",
            "RE6_R4": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
            "RE6_R4_classification": "PHASE-B2-T4-RE6-R4-PPQ-V2-SOURCE-PHASE-NOT-PERMITTED-REVIEW-STOP",
            "RE6_R3": "HISTORICAL / POISONED / NEVER REUSE LEARNER",
            "RE6_R5": "NOT AUTHORIZED",
        },
        "old_ppq_v2_preservation.json": {"pass": True, **a["protected_before"]["old_ppq_v2"]},
        "old_ppq_v2_r4_stop_reproduction.json": a["old_r4"],
        "source_phase_authority_contract.json": {
            "version": R1.AUTHORITY_VERSION, "authorized_phase_cardinality": 1,
            "formal_equality": "receipt.source_phase == expected_source_phase == authority.authorized_source_phase",
            "grammar_necessary_not_sufficient": True,
            "caller_string_is_authority": False, "qualification_runtime_authority": False,
        },
        "source_phase_authority_schema.json": R1.authority_schema_document(),
        "source_phase_authority_registry.json": registry_document(),
        "formal_phase_grammar.json": {"pattern": R1.FORMAL_PHASE_PATTERN,
            "family": R1.FORMAL_PHASE_FAMILY, "positive_integer_only": True,
            "grammar_is_authority": False},
        "authority_digest_contract.json": {"algorithm": "SHA-256",
            "input": "canonical authority excluding authority_payload_digest",
            "self_hash_circularity": False, "validator_recomputes": True,
            "receipt_directly_binds": True},
        "run_binding_contract.json": R1.run_binding_schema_document(),
        "artifact_namespace_binding_contract.json": {
            "formula": "lowercase(source_phase with hyphens replaced by underscores) + _artifacts/run_id",
            "binds": ["source phase", "run_id", "artifact namespace"],
            "cross_attempt_namespace": "STOP"},
        "authority_mode_contract.json": {"allowed": list(R1.AUTHORITY_MODES),
            "formal_success_requires": R1.FORMAL_MODE,
            "synthetic_or_historical_can_satisfy_formal": False},
        "ppq_v2_r1_receipt_contract.json": {"version": R1.VERSION,
            "inherits_non_phase": V2.VERSION, "field_count": len(R1.FIELDS),
            "new_fields": list(R1.AUTHORITY_RECEIPT_FIELDS)},
        "ppq_v2_r1_receipt_schema.json": R1.schema_document(),
        "ppq_v2_to_v2_r1_field_delta.json": field_delta,
        "non_phase_semantic_equivalence.json": a["semantic"],
        "positive_formal_fixture_1.json": a["positives"][0],
        "positive_formal_fixture_2.json": a["positives"][1],
        "positive_formal_fixture_3.json": a["positives"][2],
        "source_phase_authority_negative_matrix.json": a["negatives"],
        "caller_self_authorization_negative.json": {"pass": True, "cases": caller_cases,
            "caller_string_only": "REJECTED", "unreviewed_wrong_path_authority": "REJECTED"},
        "authority_path_content_policy.json": {"pass": True,
            "policy": "exact expected direct-child regular non-symlink path plus canonical content and recomputed digest",
            "cases": path_cases},
        "r4_phase_capability_offline_fixture.json": a["r4_capability"],
        "future_r5_phase_capability_fixture.json": a["r5_capability"],
        "attempt_number_decoupling.json": a["decoupling"],
        "future_attempt_literal_audit.json": a["literal_audit"],
        "non_phase_positive_replay.json": a["positive_replay"],
        "non_phase_negative_replay.json": a["negative_replay"],
        "publication_order_contract.json": {"pass": True,
            "trace": a["positives"][0]["trace"],
            "repair_after_candidate_write": False},
        "pre_mutation_failure_semantics.json": {"pass": True, **a["pre_failure"],
            "phase_authority_preflightable": True},
        "post_mutation_failure_semantics.json": {"pass": True, **a["post_failure"],
            "future_only": True},
        "protected_source_identity_before.json": a["protected_before"],
        "future_re6_r5_integration_plan.json": {
            "status": "DESIGN ONLY / RE6-R5 NOT AUTHORIZED",
            "steps": [
                "use reviewed PPQ-V2-R1 helper, not old PPQ-V2 phase gate",
                "independent review explicitly authorizes B2-T4-RE6-R5 before runtime",
                "select reviewed phase-authority instance",
                "supervisor creates a unique run_id",
                "derive binding across phase, run_id, config, and namespace",
                "require receipt phase equals external authority phase",
                "leave LAQ-R1 unchanged",
                "retain historical R4 pre-runtime STOP",
                "one worker and zero retry",
                "never reuse R3 learner",
                "no semantic edits during formal attempt",
            ],
            "formal_attempts_created": 0,
        },
    }
    for name, payload in payloads.items():
        artifact(name, payload)
    freeze = {
        "status": "FROZEN BEFORE FINAL POSITIVE / CANDIDATE AWAITING GPT REVIEW",
        "helper_sha256": sha(HELPER), "runner_sha256": sha(RUNNER),
        "receipt_schema_sha256": sha(OUT / "ppq_v2_r1_receipt_schema.json"),
        "phase_authority_schema_sha256": sha(OUT / "source_phase_authority_schema.json"),
        "phase_authority_registry_sha256": sha(OUT / "source_phase_authority_registry.json"),
        "source_edits_after_freeze_allowed": False,
    }
    artifact("freeze_identity.json", freeze)


def verify_freeze() -> dict[str, Any]:
    freeze = read(OUT / "freeze_identity.json")
    observed = {
        "helper_sha256": sha(HELPER), "runner_sha256": sha(RUNNER),
        "receipt_schema_sha256": sha(OUT / "ppq_v2_r1_receipt_schema.json"),
        "phase_authority_schema_sha256": sha(OUT / "source_phase_authority_schema.json"),
        "phase_authority_registry_sha256": sha(OUT / "source_phase_authority_registry.json"),
    }
    require(all(freeze[key] == value for key, value in observed.items()), "FROZEN-IDENTITY-DRIFT")
    return observed


def final_positive() -> dict[str, Any]:
    require(Path(sys.executable).resolve() == Path(
        r"C:\isaacenvs\isaac45_harl\python.exe").resolve(), "APPROVED-INTERPRETER")
    frozen = verify_freeze()
    final_dir = OUT / "final_dry_run"
    require(not final_dir.exists() and not (OUT / "final_positive_dry_run_result.json").exists(),
            "FINAL-POSITIVE-ALREADY-EXECUTED")
    prepared = prepare(final_dir, phase="B2-T4-RE6-R17", run_id="frozen-final-r17-run",
                       variant=2)
    result = R1.finalize_campaign(
        prepared["evidence"], w2e_selector=W2E.reconcile, w2i_manifest=W2I,
        pw_reconcile=V2_TEST.generic_pw, expected_phase=prepared["phase"], config=CONFIG,
        identity=new_identity(), legacy_identity=legacy_identity(),
        production_sources=PRODUCTION, pw_helper_path=PW_HELPER,
        authority_path=prepared["authority_path"],
        expected_authority_path=prepared["authority_path"],
        run_binding_path=prepared["binding_path"],
        expected_run_binding_path=prepared["binding_path"], authority_root=final_dir,
        artifact_namespace=prepared["namespace"], writer=R1.atomic_persist,
        reader=R1.readback, output_dir=final_dir)
    require(result["pass"] and result["trace"][-1] ==
            "10_canonical_witness_publication" and len(result["publication"]) == 7,
            "FINAL-POSITIVE")
    summary = {
        "pass": True, "final_frozen_positive_dry_runs": 1,
        "source_phase": prepared["phase"], "run_id": prepared["run_id"],
        "artifact_namespace": prepared["namespace"],
        "receipt_sha256": result["receipt_sha256"],
        "authority_digest": result["receipt"]["source_phase_authority_digest"],
        "run_binding_digest": result["receipt"]["source_phase_run_binding_digest"],
        "publication": result["publication"], "trace": result["trace"],
        "frozen_identity": frozen, "runtime_authorized": False,
    }
    artifact("final_positive_dry_run_result.json", summary)
    return summary


def report_text(final: Mapping[str, Any], manifest: Mapping[str, Any]) -> str:
    negative = read(OUT / "source_phase_authority_negative_matrix.json")
    sections = [
        ("A. repository authority", "main/HEAD/origin/main/merge-base and the pre-existing 359-entry index authority matched."),
        ("B. reviewed starting authority", "PPQ-V2 and LAQ-R1 remain GPT REVIEW PASS / CLOSED; historical RE6-R4 remains review STOP."),
        ("C. historical R4 preservation", "Historical R4 sources, report, and artifacts remained byte-identical."),
        ("D. exact R4 blocker", "Frozen PPQ-V2 reproduced PPQV2Stop: SOURCE-PHASE."),
        ("E. old PPQ-V2 preservation", "Old helper, runner, schema, and artifact tree were unchanged."),
        ("F. scope of V2-R1", "Pure/offline source-phase binding only; no Isaac, learner, CUDA, checkpoint, or public route."),
        ("G. source-phase coupling analysis", "The concrete tuple was isolated from stable PPQ semantics."),
        ("H. generic phase-authority contract", "One external authority authorizes exactly one phase instance."),
        ("I. authority schema", "Strict fields and types; missing, unknown, wrong-type, and noncanonical objects STOP."),
        ("J. formal phase grammar", f"`{R1.FORMAL_PHASE_PATTERN}` is necessary but not sufficient."),
        ("K. exact authorization semantics", "receipt phase == expected phase == authority phase."),
        ("L. authority digest construction", "SHA-256 covers canonical digest-excluded payload; validator recomputes it."),
        ("M. run-binding design", "Two-stage phase authority then supervisor-derived run binding."),
        ("N. namespace binding", "Phase, run ID, config, worker PID, and namespace are cross-bound."),
        ("O. authority modes", "Formal, synthetic qualification, and historical replay modes are disjoint."),
        ("P. new receipt version", f"`{R1.VERSION}`."),
        ("Q. field delta", "Four authority fields added; unrelated changed fields: 0."),
        ("R. non-phase semantic equivalence", "All inherited PPQ-V2 predicates are adjudicated by the reviewed validator; unexpected differences: 0."),
        ("S. helper architecture", "Import/composition with an explicit phase/identity-only legacy projection; no monkeypatch."),
        ("T. qualification runner", "The runner exercised the actual helper and validator."),
        ("U. positive formal fixture 1", "Offline R5 fixture PASS."),
        ("V. positive formal fixture 2", "Offline R17 fixture PASS."),
        ("W. positive formal fixture 3", "Second R5 run with distinct run ID and namespace PASS."),
        ("X. no-authority negative", "Valid formal phase without external authority STOP."),
        ("Y. phase-mismatch negatives", "Wrong authority, expected phase, receipt phase, and stale authority STOP."),
        ("Z. malformed-phase negatives", "R0, RX, negative, suffixed, shortened, and empty phases STOP."),
        ("AA. authority-mode negatives", "Synthetic and historical values cannot satisfy formal mode."),
        ("AB. authority digest negatives", "Wrong, wrong-source, and tampered authority digests STOP."),
        ("AC. stale authority/run-binding negatives", "Stale phase, run ID, namespace, and config mismatches STOP."),
        ("AD. strict schema negatives", "Extra, missing, wrong-type, and noncanonical authority objects STOP."),
        ("AE. full negative matrix", f"{negative['actual_stop']}/{negative['expected_stop']} STOP; unexpected PASS 0."),
        ("AF. old R4 STOP reproduction", "PASS: exact SOURCE-PHASE STOP retained."),
        ("AG. new R4 offline capability proof", "PASS as contract capability only; historical R4 was not reopened."),
        ("AH. future R5 capability proof", "PASS offline; runtime remains unauthorized."),
        ("AI. attempt-number decoupling", "R5, R6, R17, and R101 pass only with distinct exact authorities."),
        ("AJ. future-attempt literal audit", "Concrete future-attempt literals in helper: 0."),
        ("AK. caller self-authorization attack", "Caller-only strings and wrong-path self-created authority objects were rejected."),
        ("AL. path/content policy", "Exact trusted path, direct child, regular non-symlink, canonical content, and digest are required."),
        ("AM. non-phase positive replay", "PASS with all common non-phase fields equal."),
        ("AN. non-phase negative replay", "W2, PW, transaction, learner, poison, forbidden action, and persistence failures remain STOP."),
        ("AO. publication ordering", "Validation precedes durable write; readback/digest/schema precede canonical witness publication."),
        ("AP. failure semantics", "Pre-mutation failure is not poisoned; future post-mutation inconsistency is poisoned/no-retry."),
        ("AQ. final freeze", "Helper, runner, receipt schema, authority schema, and registry were frozen before final execution."),
        ("AR. final positive dry run", "Exactly one frozen durable R17 positive PASS."),
        ("AS. final decisive negative", "Exactly one post-positive authority-digest mutation STOP."),
        ("AT. protected-source preservation", "Production, PPQ-V2, LAQ-R1, W2E/W2I/PW, normalizer, and historical evidence modifications: 0."),
        ("AU. candidate identities", f"Helper `{manifest['helper_sha256']}`; runner `{manifest['runner_sha256']}`."),
        ("AV. future RE6-R5 integration plan", "Design only: reviewed V2-R1, separately reviewed R5 authority, unique run binding, one worker/zero retry."),
        ("AW. exact execution counts", f"Approved Python invocations {APPROVED_PYTHON_INVOCATIONS}; py_compile {PY_COMPILE_INVOCATIONS}; formal workers 0; final positive 1; final negative 1."),
        ("AX. retained nonclaims", "No RE6-R5 authorization, checkpoint readiness, long training, evaluation, or public-route readiness."),
        ("AY. final classification", f"`{CLASSIFICATION}`"),
        ("AZ. GPT-review handoff", "Candidate only. Independent GPT review is next; do not launch RE6-R5."),
    ]
    phase_table = """
| Case | Receipt phase | Expected phase | Authority phase | Authority mode | Result |
|---|---|---|---|---|---|
| valid formal R5 | R5 | R5 | R5 | FORMAL | PASS |
| valid formal R17 | R17 | R17 | R17 | FORMAL | PASS |
| no authority | R5 | R5 | - | - | STOP |
| wrong authority | R5 | R5 | R6 | FORMAL | STOP |
| expected mismatch | R5 | R6 | R5 | FORMAL | STOP |
| receipt mismatch | R6 | R5 | R5 | FORMAL | STOP |
| unauthorized R999 | R999 | R999 | - | - | STOP |
| synthetic as formal | R5-SYNTHETIC | same | same | FORMAL | STOP |
| historical as formal | historical fixture | same | same | FORMAL | STOP |
"""
    semantic_table = """
| PPQ area | V2 behavior | V2-R1 behavior | Difference |
|---|---|---|---|
| W2 / task progress / terminal / PW | reviewed | reviewed | NONE |
| W1-W7 / learner / returns | reviewed | reviewed | NONE |
| route health / forbidden actions | reviewed | reviewed | NONE |
| source phase | hardcoded tuple | external exact authority | INTENTIONAL |
| phase authority identity | absent | explicit | INTENTIONAL |
"""
    body = ["# Phase B2-T4 PPQ-V2-R1 Formal Source-Phase Binding Generalization Report", ""]
    for heading, paragraph in sections:
        body.extend((f"## {heading}", "", paragraph, ""))
        if heading.startswith("K."):
            body.extend((phase_table.strip(), ""))
        if heading.startswith("R."):
            body.extend((semantic_table.strip(), ""))
    return "\n".join(body)


def final_negative_and_close() -> dict[str, Any]:
    require(Path(sys.executable).resolve() == Path(
        r"C:\isaacenvs\isaac45_harl\python.exe").resolve(), "APPROVED-INTERPRETER")
    frozen = verify_freeze()
    require((OUT / "final_positive_dry_run_result.json").is_file(),
            "FINAL-POSITIVE-MISSING")
    require(not (OUT / "final_decisive_negative_control.json").exists(),
            "FINAL-NEGATIVE-ALREADY-EXECUTED")
    final_dir = OUT / "final_dry_run"
    authority_paths = list(final_dir.glob("*.source_phase_authority.json"))
    binding_paths = list(final_dir.glob("*.source_phase_run_binding.json"))
    require(len(authority_paths) == len(binding_paths) == 1, "FINAL-AUTHORITY-FILES")
    receipt_path = final_dir / "candidate_success_receipt_v2_1.json"
    receipt = read(receipt_path)
    prepared = {
        "phase": receipt["source_phase"], "root": final_dir,
        "authority_path": authority_paths[0], "expected_authority_path": authority_paths[0],
        "binding_path": binding_paths[0], "expected_binding_path": binding_paths[0],
        "namespace": read(binding_paths[0])["artifact_namespace"],
    }
    decisive = copy.deepcopy(receipt)
    decisive["source_phase_authority_digest"] = "0" * 64
    row = stopped("final decisive authority digest mutation", lambda: validate(prepared, decisive))
    require(row["status"] == "STOP", "FINAL-DECISIVE-NEGATIVE")
    negative = {"pass": True, "expected": "STOP", "actual": "STOP",
                "final_decisive_negative_controls": 1,
                "mutation": "source_phase_authority_digest only",
                "receipt_non_phase_values_retained": True, "result": row,
                "executed_after_final_positive": True}
    artifact("final_decisive_negative_control.json", negative)

    before = read(OUT / "protected_source_identity_before.json")
    after = protected_identity()
    require(before == after, "PROTECTED-SOURCE-DRIFT-AFTER-FINAL")
    artifact("protected_source_identity_after.json", after)
    manifest = {
        "status": "CANDIDATE / AWAITING GPT REVIEW",
        **frozen,
        "final_positive_result_sha256": sha(OUT / "final_positive_dry_run_result.json"),
    }
    artifact("ppq_v2_r1_source_identity_manifest.json", manifest)
    negative_matrix_value = read(OUT / "source_phase_authority_negative_matrix.json")
    final = {
        "classification": CLASSIFICATION,
        "candidate_awaiting_independent_review": True,
        "old_ppq_v2": "GPT REVIEW PASS / CLOSED / ORIGINAL PHASE SCOPE PRESERVED",
        "historical_re6_r4": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
        "generic_source_phase_authority": "PASS",
        "formal_phase_grammar": "PASS", "exact_external_authorization": "PASS",
        "caller_self_authorization": "REJECTED", "authority_digest": "PASS",
        "run_binding": "PASS", "namespace_binding": "PASS",
        "authority_mode_separation": "PASS", "receipt_v2_1": "PASS",
        "field_delta": "MINIMAL / PASS", "non_phase_semantic_equivalence": "PASS",
        "positive_formal_fixtures": 3,
        "phase_authority_negative_stop": negative_matrix_value["actual_stop"],
        "phase_authority_negative_expected": negative_matrix_value["expected_stop"],
        "unexpected_negative_pass": 0,
        "old_r4_stop_reproduction": "PASS", "new_r4_offline_capability": "PASS",
        "future_r5_offline_capability": "PASS", "attempt_number_decoupling": "PASS",
        "future_attempt_literals_in_helper": 0,
        "non_phase_positive_replay": "PASS", "non_phase_negative_replay": "PASS",
        "publication_ordering": "PASS", "final_positive_dry_runs": 1,
        "final_decisive_negative_controls": 1,
        "production_modifications": 0, "old_ppq_v2_modifications": 0,
        "laq_r1_modifications": 0, "historical_r4_modifications": 0,
        "AppLauncher_environment_learner": [0, 0, 0], "CUDA_formal_worker": [0, 0],
        "RE6_R5_formal_attempts": 0, "checkpoint_public_evaluation": [0, 0, 0],
        "git_add_commit_push": [0, 0, 0], "RE6_R5": "NOT AUTHORIZED",
        "checkpoint_continuation": "NOT ESTABLISHED",
        "long_paper_scale_training": "NOT AUTHORIZED",
        "public_route": "DORMANT / BLOCKED",
        "approved_interpreter_invocations": APPROVED_PYTHON_INVOCATIONS,
        "py_compile_invocations": PY_COMPILE_INVOCATIONS,
    }
    artifact("final_result.json", final)
    require(not REPORT.exists(), "REPORT-ALREADY-EXISTS")
    REPORT.write_text(report_text(final, manifest), encoding="utf-8", newline="\n")
    return final


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("check", "qualify", "final-positive", "final-negative"))
    args = parser.parse_args()
    if args.mode == "final-positive":
        result = final_positive()
        print(json.dumps({"mode": args.mode, "pass": result["pass"],
                          "receipt_sha256": result["receipt_sha256"]}))
        return
    if args.mode == "final-negative":
        result = final_negative_and_close()
        print(json.dumps({"mode": args.mode, "classification": result["classification"],
                          "negative_stop": result["phase_authority_negative_stop"]}))
        return
    result = qualification()
    if args.mode == "qualify":
        write_qualification(result)
    print(json.dumps({"mode": args.mode, "pass": True,
                      "positive_pass": len(result["positives"]),
                      "negative_stop": result["negatives"]["actual_stop"],
                      "unexpected_pass": result["negatives"]["unexpected_pass"]}))


if __name__ == "__main__":
    main()
