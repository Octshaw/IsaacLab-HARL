"""R6 RACQ-bound integration gate.

This new harness is intentionally fail-before-runtime.  It instantiates the
single live R6 authority authorized by the user, validates it in live mode,
and then exercises the frozen canonical Layer-A-v3 validator.  The reviewed
validator currently reloads every authority with qualification_mode=True, so
it rejects the live instance.  Contract edits, worker launch, CUDA, Isaac,
environment construction, and learner construction are forbidden after that
decisive pre-runtime STOP.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Mapping

import _assignment_phase_b2_t4_laq_r1_worker_receipt as LAQ_R1
import _assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_R1
import _assignment_phase_b2_t4_racq_layer_a_composition as COMPOSE
import _assignment_phase_b2_t4_racq_runtime_authority as AUTH
import test_assignment_phase_b2_t4_laq_r1_authority_binding as LAQ_TEST
import test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_TEST


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DAY = SCAN / "AgentRead/202609/20260921"
OUT = DAY / "b2_t4_re6_r6_artifacts"
REPORT = DAY / (
    "PHASE_B2_T4_RE6_R6_RACQ_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_"
    "INTEGRATION_QUALIFICATION_REPORT.md"
)
RACQ_OUT = DAY / "b2_t4_racq_artifacts"
PPQ_OUT = DAY / "b2_t4_ppq_v2_r1_artifacts"
LAQ_OUT = DAY / "b2_t4_laq_r1_artifacts"
SOURCE_PHASE = "B2-T4-RE6-R6"
CLASSIFICATION = "PHASE-B2-T4-RE6-R6-STOP-RUNTIME-AUTHORITY-INVALID"
REVIEWED_R5_CLASSIFICATION = "PHASE-B2-T4-RE6-R5-PHASE-AUTHORITY-INVALID-REVIEW-STOP"
USER_INSTRUCTION_SHA256 = "090ff31d26ed6800c483a52f8476f530f6fa8b41ded1c8543be50f5eaa7554c9"
EXPECTED_HEAD = "b71d85a32f51be6ada324f870813a56bb45dd396"
EXPECTED_STAGED_COUNT = 359
EXPECTED_INDEX_SHA = "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
EXPECTED_PATH_SET_SHA = "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
PRE_FIRST_WRITE = {
    "porcelain_line_count": 25449,
    "porcelain_sha256": "ebeba8ad084062f9d05ee5b6425cb5ecdd2e25c115ccff4b298bbc3681c29cc7",
    "staged_path_count": EXPECTED_STAGED_COUNT,
    "staged_index_sha256": EXPECTED_INDEX_SHA,
    "monthly_path_set_sha256": EXPECTED_PATH_SET_SHA,
}

PATHS = {
    "racq_runtime_helper": HERE / "_assignment_phase_b2_t4_racq_runtime_authority.py",
    "racq_composition_helper": HERE / "_assignment_phase_b2_t4_racq_layer_a_composition.py",
    "racq_runner": HERE / "test_assignment_phase_b2_t4_racq_runtime_authority_layer_a_composition.py",
    "racq_layer_a_schema": RACQ_OUT / "layer_a_v3_schema.json",
    "racq_registry_schema": RACQ_OUT / "layer_a_registry_template_schema.json",
    "racq_runtime_schema": RACQ_OUT / "runtime_authority_schema.json",
    "racq_binding_schema": RACQ_OUT / "run_binding_schema.json",
    "racq_final_positive": RACQ_OUT / "final_positive_dry_run_result.json",
    "ppq_helper": HERE / "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "ppq_runner": HERE / "test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "ppq_receipt_schema": PPQ_OUT / "ppq_v2_r1_receipt_schema.json",
    "ppq_authority_schema": PPQ_OUT / "source_phase_authority_schema.json",
    "ppq_registry": PPQ_OUT / "source_phase_authority_registry.json",
    "laq_helper": HERE / "_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
    "laq_runner": HERE / "test_assignment_phase_b2_t4_laq_r1_authority_binding.py",
    "laq_contract": LAQ_OUT / "layer_a_r1_contract.json",
    "laq_registry": LAQ_OUT / "authority_source_registry.json",
    "w2e": HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py",
    "w2i": SCAN / "AgentRead/202609/20260920/b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json",
    "pw": HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py",
    "normalizer": HERE / "_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py",
    "production_full": SCAN / "assignment_event_training_full_transaction.py",
    "production_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
    "production_env": SCAN / "scan_mobile_manipulator_env.py",
}

EXPECTED = {
    "racq_runtime_helper": "f304dfb21ced710ef08fcb92c6373785f3945e5c839ac02259e8939f46800ef0",
    "racq_composition_helper": "2a68ecde62f3ccb2277a42dc1f2640267390e7b23f431ef22ab71f4d9ac26f57",
    "racq_runner": "aa784a347218a26474f66937f13e13b27b4b5093bc164375975562c2307f4854",
    "racq_layer_a_schema": "510333b182eb3f46f3ae4d63448ec3531b876e48eaf44d3021adf0fdc450db85",
    "racq_registry_schema": "c0d510a67589475fd65b60e7c5951ea1648b225c7a89d8dc5c4317d1868eb107",
    "racq_runtime_schema": "6422a344febc31b95e8cee1d97578db4a5f007ee0d42781f903a821800387ef3",
    "racq_binding_schema": "551c29d9cdab283d77962e2239148aa2de214ee27ec609a78e1f10a0fa4a95c2",
    "racq_final_positive": "45757a9538e5e56284edc545c056b615f95f1053c19198504a660f2743871b09",
    "ppq_helper": "bd057efaeac73154b49b1e8307c9c7585f0feb449aaad3fbf4813a361a31b8a0",
    "ppq_runner": "fe420687da10b82df4c66e376cd6959f3d0199553e706f3f4eacd23d79e15433",
    "ppq_receipt_schema": "d9e28e050616bc1e2f38abfdc32d21ba884b282311d6f141a1c240632582adef",
    "ppq_authority_schema": "874bc9dee78d9d118878bdc7ea3357b70daff1715f098d8876c9d69011938c3e",
    "ppq_registry": "534f7561a8ceb9567e37793a14a74b1ca023ae2c479f7e3128bbf60a5e55ddd2",
    "laq_helper": "22720385c3eb4c67bf2317c0a90f5ca2575b85f8e07529be3c661f71cb4082b3",
    "laq_runner": "9d89b562a2564cea1e16e3fd708d8a3a583de04c25bc473135d50cdb23fea904",
    "laq_contract": "677839292827599fdef36128c05deaa96f0e9cb1f76e3975f338259231f68956",
    "laq_registry": "3f79dfe33e252c13b13fccb26a9f476b00aeb72bf73eae2c2fff5684a7247751",
    "w2e": "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0",
    "w2i": "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b",
    "pw": "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b",
    "normalizer": "316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3",
    "production_full": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "production_adapter": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
    "production_env": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"DESTINATION-EXISTS:{path}")
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_canonical(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.exists(), f"DESTINATION-EXISTS:{path}")
    path.write_bytes(AUTH.canonical(value))
    require(path.read_bytes() == AUTH.canonical(value), f"READBACK:{path}")


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
        "pre_first_r6_write": PRE_FIRST_WRITE,
        "staged_path_count": len(paths),
        "staged_index_sha256": sha256(staged).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(paths).encode()).hexdigest(),
        "git_add_commit_push": [0, 0, 0],
    }
    require(value["branch"] == "main", "REPOSITORY-BRANCH")
    require(
        value["HEAD"] == value["origin_main"] == value["merge_base"] == EXPECTED_HEAD,
        "REPOSITORY-COMMIT",
    )
    require(value["staged_path_count"] == EXPECTED_STAGED_COUNT, "REPOSITORY-STAGED-COUNT")
    require(value["staged_index_sha256"] == EXPECTED_INDEX_SHA, "REPOSITORY-INDEX-SHA")
    require(value["monthly_path_set_sha256"] == EXPECTED_PATH_SET_SHA, "REPOSITORY-PATH-SET")
    return value


def tree_identity(path: Path) -> dict[str, Any]:
    digest = sha256()
    count = 0
    size = 0
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        relative = item.relative_to(path).as_posix()
        item_size = item.stat().st_size
        digest.update(f"{relative}\0{item_size}\0{sha(item)}\n".encode())
        count += 1
        size += item_size
    return {"file_count": count, "total_bytes": size,
            "path_size_content_sha256": digest.hexdigest()}


def protected_identity() -> dict[str, Any]:
    return {
        "reviewed_files": {name: sha(path) for name, path in PATHS.items()},
        "artifact_trees": {
            "racq": tree_identity(RACQ_OUT),
            "ppq_v2_r1": tree_identity(PPQ_OUT),
            "laq_r1": tree_identity(LAQ_OUT),
            "re6_r3": tree_identity(SCAN / "AgentRead/202609/20260920/b2_t4_re6_r3_artifacts"),
            "re6_r4": tree_identity(DAY / "b2_t4_re6_r4_artifacts"),
            "re6_r5": tree_identity(DAY / "b2_t4_re6_r5_artifacts"),
        },
    }


def identity_gate() -> dict[str, Any]:
    rows = {
        name: {"path": path.relative_to(ROOT).as_posix(), "expected_sha256": EXPECTED[name],
               "actual_sha256": sha(path), "pass": sha(path) == EXPECTED[name]}
        for name, path in PATHS.items()
    }
    manifest = read(RACQ_OUT / "racq_source_identity_manifest.json")
    manifest_checks = {
        "runtime_authority_helper": manifest["runtime_authority_helper_sha256"] == rows["racq_runtime_helper"]["actual_sha256"],
        "composition_helper": manifest["composition_helper_sha256"] == rows["racq_composition_helper"]["actual_sha256"],
        "composition_adapter": manifest["composition_adapter_sha256"] == rows["racq_composition_helper"]["actual_sha256"],
        "registry_template_helper": manifest["registry_template_helper_sha256"] == rows["racq_composition_helper"]["actual_sha256"],
        "qualification_runner": manifest["qualification_runner_sha256"] == rows["racq_runner"]["actual_sha256"],
        "layer_a_v3_schema": manifest["layer_a_v3_schema_sha256"] == rows["racq_layer_a_schema"]["actual_sha256"],
        "registry_template_schema": manifest["registry_template_schema_sha256"] == rows["racq_registry_schema"]["actual_sha256"],
        "runtime_authority_schema": manifest["runtime_authority_schema_sha256"] == rows["racq_runtime_schema"]["actual_sha256"],
        "run_binding_schema": manifest["run_binding_schema_sha256"] == rows["racq_binding_schema"]["actual_sha256"],
        "final_positive": manifest["final_positive_result_sha256"] == rows["racq_final_positive"]["actual_sha256"],
        "source_frozen": manifest["source_edits_after_freeze_allowed"] is False,
    }
    require(all(row["pass"] for row in rows.values()), "REVIEWED-IDENTITY-MISMATCH")
    require(all(manifest_checks.values()), "RACQ-MANIFEST-MISMATCH")
    return {"pass": True, "identities": rows, "racq_manifest_checks": manifest_checks,
            "racq_review_state": "GPT REVIEW PASS / CLOSED"}


def config_policy_identity() -> str:
    return AUTH.digest({
        "binding": "exact PPQ-V2-R1 config_identity_digest",
        "required": True,
        "version": 1,
    })


def external_authorization_provenance() -> dict[str, Any]:
    return {
        "authority": "EXPLICIT-USER-AUTHORIZATION",
        "instruction_sha256": USER_INSTRUCTION_SHA256,
        "authorized_source_phase": SOURCE_PHASE,
        "live_runtime_authority_instances": 1,
        "formal_supervisors": 1,
        "mutation_bearing_workers": 1,
        "retries": 0,
    }


def make_live_authority() -> dict[str, Any]:
    provenance_digest = AUTH.digest(external_authorization_provenance())
    payload: dict[str, Any] = {
        "authority_version": AUTH.AUTHORITY_VERSION,
        "authorization_scope": AUTH.AUTHORIZATION_SCOPE,
        "authorization_mode": AUTH.AUTHORIZATION_MODE,
        "authorized_source_phase": SOURCE_PHASE,
        "phase_family": AUTH.PHASE_FAMILY,
        "qualification_parent_version": AUTH.PPQ_PARENT_VERSION,
        "qualification_parent_helper_sha256": AUTH.PPQ_PARENT_HELPER_SHA256,
        "qualification_parent_schema_sha256": AUTH.PPQ_PARENT_SCHEMA_SHA256,
        "expected_ppq_contract": AUTH.PPQ_PARENT_VERSION,
        "allowed_run_binding_contract": AUTH.BINDING_VERSION,
        "namespace_policy": AUTH.NAMESPACE_POLICY,
        "config_policy_identity": config_policy_identity(),
        "external_authorization_digest": provenance_digest,
        "instance_purpose": AUTH.LIVE_PURPOSE,
        "live_runtime_grant": True,
    }
    payload["authority_payload_digest"] = AUTH.digest(payload)
    return payload


def old_laq_payload() -> dict[str, Any]:
    sources, context, _, registry = LAQ_TEST.baseline()
    return LAQ_R1.project_layer_a_r1(sources, context["ppq_schema"], registry)["payload"]


def observe_canonical_live_authority_stop(
    authority: Mapping[str, Any], authority_path: Path,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="b2-t4-re6-r6-live-authority-gate-") as raw:
        root = Path(raw)
        run_id = "r6-pre-runtime-live-authority-gate"
        prepared = PPQ_TEST.prepare(root / "ppq", phase=SOURCE_PHASE, run_id=run_id, variant=1)
        ppq_result = PPQ_TEST.call(prepared)
        ppq_receipt = ppq_result["receipt"]
        template = COMPOSE.registry_template_document()
        context = COMPOSE.make_run_context(
            source_phase=SOURCE_PHASE, run_id=run_id,
            worker_pid=ppq_receipt["worker_pid"], artifact_namespace=prepared["namespace"],
            config_digest=ppq_receipt["config_identity_digest"],
            ppq_receipt_digest=COMPOSE.digest(ppq_receipt),
        )
        binding = AUTH.make_run_binding(
            authority=authority, run_id=run_id, worker_pid=ppq_receipt["worker_pid"],
            config_digest=ppq_receipt["config_identity_digest"],
            artifact_namespace=prepared["namespace"],
            registry_template_digest=COMPOSE.registry_template_digest(),
        )
        registry = COMPOSE.instantiate_registry(template, context)
        laq_payload = old_laq_payload()
        payload = COMPOSE.compose_payload(
            ppq_receipt=ppq_receipt, laq_v2_payload=laq_payload,
            runtime_authority=authority, run_binding=binding, registry_instance=registry,
        )
        receipt = COMPOSE.envelope_for(payload)
        before = deepcopy(receipt)
        try:
            COMPOSE.validate_layer_a_v3(
                receipt,
                ppq_validator=lambda value: PPQ_TEST.validate(prepared, value),
                source_ppq_receipt=ppq_receipt,
                source_laq_v2_payload=laq_payload,
                authority_path=authority_path,
                binding_path=OUT / AUTH.binding_relative_path(SOURCE_PHASE, run_id),
                authority_root=OUT,
                expected_external_authorization_digest=authority["external_authorization_digest"],
                expected_config_policy_identity=config_policy_identity(),
                registry_template=template,
                registry_instance=registry,
                run_context=context,
            )
        except AUTH.RACQAuthorityStop as exc:
            reason = str(exc)
        else:
            raise RuntimeError("LIVE-AUTHORITY-UNEXPECTEDLY-ACCEPTED")
        require(receipt == before, "SUPERVISOR-MUTATED-RECEIPT")
        require(reason == "RUNTIME-AUTHORITY-QUALIFICATION-PURPOSE",
                f"UNEXPECTED-LAYER-A-STOP:{reason}")
        return {
            "status": "STOP AS EXPECTED",
            "reason": reason,
            "frozen_validator": "COMPOSE.validate_layer_a_v3",
            "frozen_validator_forces_qualification_mode": True,
            "live_authority_required_values": {
                "instance_purpose": authority["instance_purpose"],
                "live_runtime_grant": authority["live_runtime_grant"],
            },
            "qualification_values_required_by_call": {
                "instance_purpose": AUTH.QUALIFICATION_PURPOSE,
                "live_runtime_grant": False,
            },
            "ppq_v2_r1_validator_reached_and_passed": True,
            "binding_file_read": False,
            "supervisor_mutations": 0,
        }


SECTIONS = [
    "A. repository authority", "B. reviewed starting authority", "C. historical STOP preservation",
    "D. RACQ authority", "E. PPQ-V2-R1 authority", "F. LAQ-R1 authority",
    "G. protected identities", "H. R6 harness", "I. explicit R6 authorization",
    "J. live runtime-authority instance", "K. runtime-authority validation",
    "L. unique run identity", "M. config authority", "N. live run binding",
    "O. run-binding validation", "P. registry template", "Q. R6 registry instance",
    "R. registry validation", "S. filesystem precondition", "T. static authority snapshot",
    "U. pre-runtime authority negatives", "V. pre-runtime Layer-A-v3 negatives",
    "W. complete synthetic R6 chain", "X. harness freeze", "Y. runner readiness",
    "Z. CUDA/CUBLAS", "AA. supervisor/worker", "AB. runtime config",
    "AC. transaction definition", "AD. transaction inventory", "AE. transaction table",
    "AF. episode/update timeline", "AG. decision gating", "AH. NR", "AI. SR", "AJ. ZD",
    "AK. zero-DVM", "AL. actor plan", "AM. actor evidence", "AN. factor", "AO. critic",
    "AP. ValueNorm", "AQ. Adam continuity", "AR. event returns", "AS. bridges",
    "AT. PW transaction", "AU. PW campaign", "AV. W1", "AW. W2E inventory",
    "AX. W2E selected witness", "AY. W2 claim", "AZ. W2 continuity",
    "BA. W2 completion", "BB. W2 clear", "BC. W2 reopen", "BD. W3", "BE. W4",
    "BF. W5", "BG. W6", "BH. W7", "BI. task progress", "BJ. terminal/autoreset",
    "BK. numerical health", "BL. fresh normalization", "BM. normalization/raw",
    "BN. PPQ-V2-R1 receipt", "BO. PPQ validation", "BP. PPQ persistence/readback",
    "BQ. canonical witness publication", "BR. Layer-A-v3 composition",
    "BS. Layer-A-v3 schema", "BT. Layer-A runtime/raw", "BU. Layer-A source authority",
    "BV. live R6 runtime authority", "BW. live run binding", "BX. live registry",
    "BY. live filesystem digest", "BZ. inherited 39 predicates", "CA. new 9 RACQ predicates",
    "CB. complete Layer A", "CC. env close", "CD. worker receipt durability",
    "CE. app-close handoff", "CF. EP-Q Layer B", "CG. process quiescence",
    "CH. supervisor final adjudication", "CI. exact execution counts",
    "CJ. retained nonclaims", "CK. final classification", "CL. GPT-review handoff",
]


def report_text(validation: Mapping[str, Any], authority: Mapping[str, Any]) -> str:
    special = {
        "A. repository authority": "Repository commit/index authority passed; exact current and pre-first-write porcelain digests are in repository_authority.json.",
        "B. reviewed starting authority": "RACQ, PPQ-V2-R1, and LAQ-R1 are treated as GPT REVIEW PASS / CLOSED per explicit user authority.",
        "C. historical STOP preservation": "R3 remains historical/poisoned; R4/R5 remain pre-runtime STOPs. No namespace or learner was reused.",
        "D. RACQ authority": "All reviewed RACQ source and schema identities matched the frozen manifest.",
        "E. PPQ-V2-R1 authority": "All five reviewed PPQ-V2-R1 identities matched.",
        "F. LAQ-R1 authority": "All four reviewed LAQ-R1 identities matched.",
        "G. protected identities": "Protected identities before and after the pre-runtime gate are identical.",
        "H. R6 harness": f"New pure pre-runtime harness SHA-256 `{sha(Path(__file__))}`; it imports no Isaac, HARL, torch, or CUDA.",
        "I. explicit R6 authorization": f"Exact instruction SHA-256 `{USER_INSTRUCTION_SHA256}` authorizes only {SOURCE_PHASE} and one live authority instance.",
        "J. live runtime-authority instance": f"Exactly one authority was persisted at `{AUTH.authority_relative_path(SOURCE_PHASE).as_posix()}` with live_runtime_grant=true.",
        "K. runtime-authority validation": "Direct live-mode RACQ validation PASS; canonical Layer-A-v3 integration STOP: `RUNTIME-AUTHORITY-QUALIFICATION-PURPOSE`.",
        "L. unique run identity": "NOT CREATED — stopped at the earlier canonical Layer-A runtime-authority integration gate.",
        "M. config authority": "NOT CREATED — stopped at the earlier canonical Layer-A runtime-authority integration gate.",
        "N. live run binding": "NOT CREATED — the live authority cannot pass the frozen Layer-A-v3 loader mode.",
        "O. run-binding validation": "NOT RUN — stopped before run binding.",
        "P. registry template": "Reviewed template identity PASS; no live instance was created.",
        "Q. R6 registry instance": "NOT CREATED — stopped before run context existed.",
        "R. registry validation": "NOT RUN — stopped before registry instantiation.",
        "BR. Layer-A-v3 composition": "STOP: the frozen validator hardcodes qualification_mode=True while this authorized instance must be live.",
        "BV. live R6 runtime authority": "Isolated live contract validation PASS; canonical Layer-A consumption FAIL.",
        "CH. supervisor final adjudication": "NOT RUN / PRE-RUNTIME STOP.",
        "CI. exact execution counts": "Approved Python invocations 4 (repository check, py_compile, self-check, decisive pre-runtime harness); live authorities 1; live bindings/registry instances 0/0; formal supervisor/worker/retry 0/0/0; CUDA/AppLauncher/environment/reset/learner 0/0/0/0/0; physical/transactions 0/0; git add/commit/push 0/0/0.",
        "CJ. retained nonclaims": "No runtime, learner, training-quality, checkpoint, evaluation/playback, public-route, or successful Layer-A/B claim. partial_update=false; route_poisoned=false.",
        "CK. final classification": f"`{CLASSIFICATION}`",
        "CL. GPT-review handoff": "Pre-runtime STOP. Do not launch a worker or edit RACQ to force acceptance; independent GPT review is required.",
    }
    lines = ["# Phase B2-T4-RE6-R6 RACQ-bound normal-horizon integration report", "",
             f"Classification: `{CLASSIFICATION}`", "",
             "Outcome: **PRE-RUNTIME STOP / FORMAL ATTEMPTS 0 / NOT POISONED**.", ""]
    for section in SECTIONS:
        lines.extend([f"## {section}", "", special.get(
            section, "NOT RUN — stopped at the earlier frozen runtime-authority/Layer-A integration gate."), ""])
    lines.extend([
        "## Primary runtime-authority table", "",
        "| Property | Expected | Actual | Result |", "|---|---|---|---|",
        "| Scope | FORMAL-RUNTIME-AUTHORIZED | FORMAL-RUNTIME-AUTHORIZED | PASS |",
        "| live_runtime_grant | true | true | PASS |",
        "| Phase | B2-T4-RE6-R6 | B2-T4-RE6-R6 | PASS |",
        f"| Authority digest | exact | `{authority['authority_payload_digest']}` | PASS |",
        f"| Authority path | RACQ-derived | `{AUTH.authority_relative_path(SOURCE_PHASE).as_posix()}` | PASS |",
        "| Canonical Layer-A loader mode | live | qualification | **STOP** |",
        "| Run ID / binding | unique / exact | not created | NOT RUN |", "",
        "## Primary Layer-A-v3 table", "",
        "| Subgate | Expected | Actual | Result |", "|---|---:|---:|---|",
        "| Top-level fields | 43 | synthetic envelope 43 | REACHED |",
        "| Nested PPQ fields | 90 | synthetic PPQ 90 | PASS |",
        "| Runtime authority | PASS | RUNTIME-AUTHORITY-QUALIFICATION-PURPOSE | **STOP** |",
        "| Remaining complete Layer A | PASS | not run | NOT RUN |", "",
        "## Primary runtime table", "",
        "| Gate | Expected | Actual | Result |", "|---|---:|---:|---|",
        "| Physical | 320 | 0 | NOT RUN |", "| Transactions | 160 | 0 | NOT RUN |",
        "| S10 | 160 | 0 | NOT RUN |", "| Ledger | 160 | 0 | NOT RUN |",
        "| Bridges | 159 | 0 | NOT RUN |", "| PW critic | 6560 | 0 | NOT RUN |",
        "| PW actor/factor | 640 | 0 | NOT RUN |", "| W7 | 160 | 0 | NOT RUN |",
        "| Event returns | 160 | 0 | NOT RUN |", "| Stock returns | 0 | 0 | NOT RUN |",
        "| tx161 | false | false | NOT STARTED |", "",
        "## Primary W2 table", "", "No fresh W2 evidence exists because runtime did not start.", "",
        "## Decisive evidence", "",
        f"- Direct RACQ live-mode validation: `{validation['direct_live_validation']}`.",
        f"- Frozen Layer-A-v3 validation: `{validation['layer_a_integration']['reason']}`.",
        "- The frozen composition helper passes `qualification_mode=True` unconditionally.",
        "- The reviewed live contract requires `LIVE-FORMAL-RUNTIME` and `live_runtime_grant=true`.",
        "- Contract modification is explicitly prohibited, so no worker was launched.", "",
    ])
    return "\n".join(lines)


def self_check() -> dict[str, Any]:
    require(Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(),
            "APPROVED-INTERPRETER")
    require(not OUT.exists() and not REPORT.exists(), "R6-OUTPUT-ALREADY-EXISTS")
    identity_gate()
    source = PATHS["racq_composition_helper"].read_text(encoding="utf-8")
    require("qualification_mode=True" in source, "DECISIVE-CALL-NOT-FOUND")
    require(AUTH.LIVE_PURPOSE != AUTH.QUALIFICATION_PURPOSE, "LIVE-QUALIFICATION-NOT-DISJOINT")
    return {"pass": True, "decisive_expected_stop": "RUNTIME-AUTHORITY-QUALIFICATION-PURPOSE",
            "runtime_imports": 0, "formal_workers": 0}


def pre_runtime_stop() -> dict[str, Any]:
    require(Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(),
            "APPROVED-INTERPRETER")
    require(not OUT.exists() and not REPORT.exists(), "R6-OUTPUT-ALREADY-EXISTS")
    repo = repository_authority()
    identities = identity_gate()
    protected_before = protected_identity()
    write("repository_authority.json", repo)
    write("reviewed_starting_authority.json", {
        "RACQ": "GPT REVIEW PASS / CLOSED", "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED",
        "LAQ_R1": "GPT REVIEW PASS / CLOSED",
        "RE6_R3": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED",
        "RE6_R4": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
        "RE6_R5": "GPT REVIEW STOP CONFIRMED / PRE-RUNTIME / FORMAL ATTEMPTS 0 / NOT POISONED",
        "RE6_R5_reviewed_classification": REVIEWED_R5_CLASSIFICATION,
        "RE6_R6": "EXPLICITLY AUTHORIZED / PRE-RUNTIME GATE",
    })
    write("reviewed_identity_gate.json", identities)
    write("protected_source_identity_before.json", protected_before)
    write("explicit_r6_authorization_provenance.json", external_authorization_provenance() | {
        "external_authorization_digest": AUTH.digest(external_authorization_provenance())})

    authority = make_live_authority()
    authority_path = OUT / AUTH.authority_relative_path(SOURCE_PHASE)
    write_canonical(authority_path, authority)
    loaded = AUTH.load_runtime_authority(
        actual_path=authority_path, authority_root=OUT,
        expected_source_phase=SOURCE_PHASE,
        expected_external_authorization_digest=authority["external_authorization_digest"],
        expected_config_policy_identity=config_policy_identity(), qualification_mode=False,
    )
    require(loaded == authority, "DIRECT-LIVE-AUTHORITY-VALIDATION")
    layer_a_stop = observe_canonical_live_authority_stop(authority, authority_path)
    validation = {
        "direct_live_validation": "PASS",
        "direct_qualification_validation": "NOT USED",
        "authority_path": authority_path.relative_to(OUT).as_posix(),
        "authority_file_sha256": sha(authority_path),
        "authority_payload_digest": authority["authority_payload_digest"],
        "live_runtime_authority_instances": 1,
        "layer_a_integration": layer_a_stop,
        "pass": False,
        "status": "STOP BEFORE FORMAL RUNTIME",
    }
    write("live_r6_runtime_authority.json", {
        "logical_role": "single live R6 runtime authority instance",
        "authoritative_path": authority_path.relative_to(OUT).as_posix(),
        "duplicate_instance": False,
        "authority_payload_digest": authority["authority_payload_digest"],
        "scope": authority["authorization_scope"], "mode": authority["authorization_mode"],
        "phase": authority["authorized_source_phase"],
        "instance_purpose": authority["instance_purpose"],
        "live_runtime_grant": authority["live_runtime_grant"],
    })
    write("live_r6_runtime_authority_validation.json", validation)
    write("r6_static_authority_snapshot.json", {
        "pass": True, "reviewed_identities": identities,
        "live_authority_path": authority_path.relative_to(OUT).as_posix(),
        "live_authority_file_sha256": sha(authority_path),
        "live_authority_payload_digest": authority["authority_payload_digest"],
        "snapshot_stage": "PRE-RUNTIME / BEFORE RUN-ID-BINDING-REGISTRY",
    })
    write("pre_runtime_complete_r6_success_chain.json", {
        "pass": False, "status": "STOP",
        "reason": layer_a_stop["reason"],
        "chain_reached": ["explicit authorization", "live RACQ authority", "PPQ-V2-R1 synthetic validation", "Layer-A-v3 authority load"],
        "chain_not_reached": ["live run binding", "live registry instance", "worker", "Layer B"],
    })
    protected_after = protected_identity()
    require(protected_after == protected_before, "PROTECTED-SOURCE-DRIFT")
    write("protected_source_identity_after.json", protected_after)
    failure = {
        "classification": CLASSIFICATION, "source_phase": SOURCE_PHASE,
        "run_id": None, "runtime_authority_digest": authority["authority_payload_digest"],
        "run_binding_digest": None, "registry_instance_digest": None, "worker_pid": None,
        "failure_stage": "pre-runtime canonical Layer-A-v3 live-authority integration",
        "failure_reason": layer_a_stop["reason"], "first_learner_mutation_occurred": False,
        "partial_update": False, "route_poisoned": False,
        "physical": 0, "transactions": 0, "S10": 0, "ledger": 0, "bridges": 0,
        "PPQ_status": "SYNTHETIC VALIDATOR REACHED / NO LIVE RECEIPT",
        "Layer_A_v3_status": "STOP", "W1_W7_W2": "NOT RUN", "PW": "NOT RUN",
        "normalizer": "NOT RUN", "env_close": "NOT RUN",
        "formal_supervisors": 0, "formal_workers": 0, "retries": 0,
    }
    write("failure_receipt.json", failure)
    final = {
        "classification": CLASSIFICATION,
        "status": "PRE-RUNTIME STOP / FORMAL ATTEMPTS 0 / NOT POISONED",
        "decisive_reason": layer_a_stop["reason"],
        "live_runtime_authority_instances": 1,
        "live_runtime_authority_isolated_validation": "PASS",
        "canonical_layer_a_live_authority_integration": "STOP",
        "live_run_bindings": 0, "r6_registry_instances": 0,
        "formal_supervisors": 0, "formal_workers": 0, "formal_retries": 0,
        "cuda": 0, "app_launcher": 0, "environment": 0, "reset": 0,
        "learner": 0, "physical": 0, "transactions": 0, "tx161_started": False,
        "partial_update": False, "route_poisoned": False,
        "checkpoint": 0, "public_activation": 0, "evaluation_playback": 0,
        "production_modifications": 0, "racq_modifications": 0,
        "ppq_v2_r1_modifications": 0, "laq_r1_modifications": 0,
        "historical_r3_r4_r5_modifications": 0,
        "git_add_commit_push": [0, 0, 0],
        "next": "independent GPT review of the frozen RACQ live-authority integration blocker",
    }
    write("final_result.json", final)
    REPORT.write_text(report_text(validation, authority), encoding="utf-8")
    return final


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("self-check", "pre-runtime-stop"))
    args = parser.parse_args()
    result = self_check() if args.mode == "self-check" else pre_runtime_stop()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
