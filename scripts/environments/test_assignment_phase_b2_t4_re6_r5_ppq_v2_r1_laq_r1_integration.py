"""Pure pre-runtime gate for the requested RE6-R5 integration.

This runner deliberately has no formal-worker mode.  It exercises the frozen
PPQ-V2-R1 and LAQ-R1 validators and emits a fail-closed record when their
reviewed contracts cannot represent the requested formal R5 runtime without a
semantic change.  It never imports Isaac Lab, HARL, torch, or CUDA.
"""

from __future__ import annotations

import copy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DAY = SCAN / "AgentRead/202609/20260921"
OUT = DAY / "b2_t4_re6_r5_artifacts"
REPORT = DAY / (
    "PHASE_B2_T4_RE6_R5_PPQ_V2_R1_LAQ_R1_BOUND_NORMAL_HORIZON_"
    "LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md"
)
PPQ_R1_OUT = DAY / "b2_t4_ppq_v2_r1_artifacts"
LAQ_R1_OUT = DAY / "b2_t4_laq_r1_artifacts"

sys.path.insert(0, str(HERE))
import _assignment_phase_b2_t4_laq_r1_worker_receipt as LAQ_AUTH  # noqa: E402
import _assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_R1  # noqa: E402
import test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding as PPQ_R1_RUNNER  # noqa: E402


CLASSIFICATION = "PHASE-B2-T4-RE6-R5-STOP-PHASE-AUTHORITY-INVALID"
SOURCE_PHASE = "B2-T4-RE6-R5"
REQUESTED_AUTHORITY_NAME = "r5_source_phase_authority.json"
REQUESTED_BINDING_NAME = "r5_source_phase_run_binding.json"
EXPECTED_HEAD = "b71d85a32f51be6ada324f870813a56bb45dd396"
EXPECTED_STAGED_COUNT = 359
EXPECTED_INDEX_SHA = "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c"
EXPECTED_MONTHLY_PATH_SHA = "0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab"
PRE_FIRST_R5_WRITE = {
    "full_porcelain_line_count": 25366,
    "full_porcelain_sha256": "1c40d111e895c50585efa5436b946e14cf63a2abe6a26d6a4f169f62d4c0b015",
    "staged_path_count": EXPECTED_STAGED_COUNT,
    "staged_index_sha256": EXPECTED_INDEX_SHA,
    "monthly_path_set_sha256": EXPECTED_MONTHLY_PATH_SHA,
}

EXPECTED = {
    "ppq_v2_r1_helper": "bd057efaeac73154b49b1e8307c9c7585f0feb449aaad3fbf4813a361a31b8a0",
    "ppq_v2_r1_runner": "fe420687da10b82df4c66e376cd6959f3d0199553e706f3f4eacd23d79e15433",
    "ppq_v2_r1_receipt_schema": "d9e28e050616bc1e2f38abfdc32d21ba884b282311d6f141a1c240632582adef",
    "ppq_v2_r1_authority_schema": "874bc9dee78d9d118878bdc7ea3357b70daff1715f098d8876c9d69011938c3e",
    "ppq_v2_r1_authority_registry": "534f7561a8ceb9567e37793a14a74b1ca023ae2c479f7e3128bbf60a5e55ddd2",
    "laq_r1_helper": "22720385c3eb4c67bf2317c0a90f5ca2575b85f8e07529be3c661f71cb4082b3",
    "laq_r1_runner": "9d89b562a2564cea1e16e3fd708d8a3a583de04c25bc473135d50cdb23fea904",
    "laq_r1_contract": "677839292827599fdef36128c05deaa96f0e9cb1f76e3975f338259231f68956",
    "laq_r1_registry": "3f79dfe33e252c13b13fccb26a9f476b00aeb72bf73eae2c2fff5684a7247751",
    "normalizer": "316b58f76934de073c32bf81f510c321917decb6645d1244436031ed360e92e3",
    "w2e": "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0",
    "w2i": "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b",
    "pw": "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b",
    "production_full": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "production_adapter": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
    "production_env": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}

PATHS = {
    "ppq_v2_r1_helper": HERE / "_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "ppq_v2_r1_runner": HERE / "test_assignment_phase_b2_t4_ppq_v2_r1_phase_binding.py",
    "ppq_v2_r1_receipt_schema": PPQ_R1_OUT / "ppq_v2_r1_receipt_schema.json",
    "ppq_v2_r1_authority_schema": PPQ_R1_OUT / "source_phase_authority_schema.json",
    "ppq_v2_r1_authority_registry": PPQ_R1_OUT / "source_phase_authority_registry.json",
    "laq_r1_helper": HERE / "_assignment_phase_b2_t4_laq_r1_worker_receipt.py",
    "laq_r1_runner": HERE / "test_assignment_phase_b2_t4_laq_r1_authority_binding.py",
    "laq_r1_contract": LAQ_R1_OUT / "layer_a_r1_contract.json",
    "laq_r1_registry": LAQ_R1_OUT / "authority_source_registry.json",
    "normalizer": HERE / "_assignment_phase_b2_t4_re6_r3_ppq_v2_normalization.py",
    "w2e": HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py",
    "w2i": SCAN / "AgentRead/202609/20260920/b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json",
    "pw": HERE / "_assignment_phase_b2_t4_windows_evidence_persistence.py",
    "production_full": SCAN / "assignment_event_training_full_transaction.py",
    "production_adapter": SCAN / "assignment_event_training_real_isaac_adapter.py",
    "production_env": SCAN / "scan_mobile_manipulator_env.py",
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    require(not path.exists(), f"DESTINATION-EXISTS:{path}")
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def repository_authority() -> dict[str, Any]:
    porcelain = git_bytes("status", "--porcelain=v1", "-uall")
    staged = git_bytes("ls-files", "--stage")
    staged_paths = git_bytes("diff", "--cached", "--name-only").decode("utf-8").splitlines()
    value = {
        "branch": git_bytes("branch", "--show-current").decode().strip(),
        "HEAD": git_bytes("rev-parse", "HEAD").decode().strip(),
        "origin_main": git_bytes("rev-parse", "origin/main").decode().strip(),
        "merge_base": git_bytes("merge-base", "HEAD", "origin/main").decode().strip(),
        "current_full_porcelain": porcelain.decode("utf-8"),
        "current_full_porcelain_line_count": len(porcelain.splitlines()),
        "current_full_porcelain_sha256": sha256(porcelain).hexdigest(),
        "pre_first_r5_write": PRE_FIRST_R5_WRITE,
        "staged_path_count": len(staged_paths),
        "staged_index_sha256": sha256(staged).hexdigest(),
        "monthly_path_set_sha256": sha256("\n".join(staged_paths).encode()).hexdigest(),
        "git_add_commit_push": [0, 0, 0],
    }
    require(value["branch"] == "main", "REPOSITORY-BRANCH-AUTHORITY")
    require(
        value["HEAD"] == value["origin_main"] == value["merge_base"] == EXPECTED_HEAD,
        "REPOSITORY-COMMIT-AUTHORITY",
    )
    require(
        value["staged_path_count"] == EXPECTED_STAGED_COUNT
        and value["staged_index_sha256"] == EXPECTED_INDEX_SHA
        and value["monthly_path_set_sha256"] == EXPECTED_MONTHLY_PATH_SHA,
        "REPOSITORY-INDEX-AUTHORITY",
    )
    return value


def stop_reason(operation: Callable[[], Any]) -> str:
    try:
        operation()
    except PPQ_R1.PPQV2R1Stop as exc:
        return str(exc)
    raise RuntimeError("EXPECTED-PPQ-V2-R1-STOP-NOT-OBSERVED")


def persist_canonical(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    PPQ_R1.atomic_persist(path, value)


def authority_probes() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="b2-t4-re6-r5-preflight-") as raw:
        base = Path(raw)

        offline_root = base / "offline-control"
        offline_root.mkdir()
        offline = PPQ_R1.make_offline_authority(
            source_phase=SOURCE_PHASE,
            authority_instance_id="r5-offline-control",
            authorization_mode=PPQ_R1.FORMAL_MODE,
        )
        offline_path = offline_root / "r5-offline-control.source_phase_authority.json"
        persist_canonical(offline_path, offline)
        loaded = PPQ_R1.load_phase_authority(
            actual_path=offline_path,
            expected_path=offline_path,
            authority_root=offline_root,
            required_mode=PPQ_R1.FORMAL_MODE,
        )

        scope_root = base / "runtime-scope-negative"
        scope_root.mkdir()
        runtime = PPQ_R1.make_offline_authority(
            source_phase=SOURCE_PHASE,
            authority_instance_id="r5-runtime-scope-probe",
            authorization_mode=PPQ_R1.FORMAL_MODE,
        )
        runtime["qualification_scope"] = "FORMAL-RUNTIME-AUTHORIZED"
        runtime["authority_payload_digest"] = PPQ_R1.digest(
            {key: item for key, item in runtime.items() if key != "authority_payload_digest"}
        )
        runtime_path = scope_root / "r5-runtime-scope-probe.source_phase_authority.json"
        persist_canonical(runtime_path, runtime)
        scope_stop = stop_reason(
            lambda: PPQ_R1.load_phase_authority(
                actual_path=runtime_path,
                expected_path=runtime_path,
                authority_root=scope_root,
                required_mode=PPQ_R1.FORMAL_MODE,
            )
        )

        filename_root = base / "authority-filename-negative"
        filename_root.mkdir()
        filename_authority = PPQ_R1.make_offline_authority(
            source_phase=SOURCE_PHASE,
            authority_instance_id="r5-filename-probe",
            authorization_mode=PPQ_R1.FORMAL_MODE,
        )
        requested_authority_path = filename_root / REQUESTED_AUTHORITY_NAME
        persist_canonical(requested_authority_path, filename_authority)
        authority_filename_stop = stop_reason(
            lambda: PPQ_R1.load_phase_authority(
                actual_path=requested_authority_path,
                expected_path=requested_authority_path,
                authority_root=filename_root,
                required_mode=PPQ_R1.FORMAL_MODE,
            )
        )

        binding_root = base / "binding-filename-negative"
        binding_root.mkdir()
        binding = PPQ_R1.make_run_binding(
            authority=loaded,
            run_id="r5-offline-binding-probe",
            worker_pid=1,
            config_digest="0" * 64,
            artifact_namespace=PPQ_R1.expected_artifact_namespace(
                SOURCE_PHASE, "r5-offline-binding-probe"
            ),
        )
        requested_binding_path = binding_root / REQUESTED_BINDING_NAME
        persist_canonical(requested_binding_path, binding)
        binding_filename_stop = stop_reason(
            lambda: PPQ_R1.load_run_binding(
                actual_path=requested_binding_path,
                expected_path=requested_binding_path,
                authority_root=binding_root,
            )
        )

    require(scope_stop == "PHASE-AUTHORITY-SCOPE", "SCOPE-NEGATIVE-NOT-DECISIVE")
    require(
        authority_filename_stop == "PHASE-AUTHORITY-FILENAME",
        "AUTHORITY-FILENAME-NEGATIVE-NOT-DECISIVE",
    )
    require(
        binding_filename_stop == "RUN-BINDING-FILENAME",
        "BINDING-FILENAME-NEGATIVE-NOT-DECISIVE",
    )
    return {
        "offline_control": {
            "status": "PASS",
            "authorization_mode": loaded["authorization_mode"],
            "qualification_scope": loaded["qualification_scope"],
            "runtime_authority": False,
            "persisted_after_probe": False,
        },
        "runtime_scope_negative": {
            "status": "STOP",
            "requested_scope": "FORMAL-RUNTIME-AUTHORIZED",
            "actual_validator_reason": scope_stop,
            "persisted_after_probe": False,
        },
        "requested_authority_filename_negative": {
            "status": "STOP",
            "requested_filename": REQUESTED_AUTHORITY_NAME,
            "required_filename_formula": "<authority_instance_id>.source_phase_authority.json",
            "actual_validator_reason": authority_filename_stop,
            "persisted_after_probe": False,
        },
        "requested_binding_filename_negative": {
            "status": "STOP",
            "requested_filename": REQUESTED_BINDING_NAME,
            "required_filename_formula": "<run_id>.source_phase_run_binding.json",
            "actual_validator_reason": binding_filename_stop,
            "persisted_after_probe": False,
        },
        "temporary_offline_authority_fixtures": 3,
        "temporary_offline_binding_fixtures": 1,
        "formal_runtime_authority_instances": 0,
        "formal_run_bindings": 0,
    }


def replace_strings(value: Any, old: str, new: str) -> Any:
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace_strings(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: replace_strings(item, old, new) for key, item in value.items()}
    return value


def laq_integration_probe() -> dict[str, Any]:
    reviewed = LAQ_AUTH.registry_document()
    r3_prefix = (
        "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/"
        "AgentRead/202609/20260920/b2_t4_re6_r3_artifacts"
    )
    r5_prefix = (
        "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/"
        "AgentRead/202609/20260921/b2_t4_re6_r5_artifacts"
    )
    rebased = replace_strings(reviewed, r3_prefix, r5_prefix)
    try:
        LAQ_AUTH._checked_registry(rebased)
    except LAQ_AUTH.LAQ.LayerAStop as exc:
        registry_stop = str(exc)
    else:
        raise RuntimeError("EXPECTED-LAQ-R1-REGISTRY-STOP-NOT-OBSERVED")
    old_ppq_fields = len(LAQ_AUTH.PPQ.FIELDS)
    ppq_v2_r1_fields = len(PPQ_R1.FIELDS)
    laq_extra_fields = len(LAQ_AUTH.LAQ.EXTRA_TYPES)
    projected_fields = len(set(PPQ_R1.FIELDS) | set(LAQ_AUTH.LAQ.EXTRA_TYPES))
    contract = read(LAQ_R1_OUT / "layer_a_r1_contract.json")
    require(registry_stop == "AUTHORITY-REGISTRY-PATH-OR-DEFINITION-DRIFT", "LAQ-STOP-DRIFT")
    require(len(reviewed["fields"]) == contract["required_mandatory_fields"] == 120, "LAQ-FIELD-COUNT")
    return {
        "status": "SECONDARY INDEPENDENT CONTRACT/RUNTIME GAP",
        "actual_validator_reason_for_r5_path_rebinding": registry_stop,
        "reviewed_registry_is_exact_hardcoded_r3_document": True,
        "reviewed_source_path_policy": reviewed["source_path_policy"],
        "reviewed_laq_r1_required_fields": contract["required_mandatory_fields"],
        "reviewed_laq_r1_ppq_v2_fields": old_ppq_fields,
        "ppq_v2_r1_fields": ppq_v2_r1_fields,
        "laq_extra_fields": laq_extra_fields,
        "naive_ppq_v2_r1_plus_laq_r1_field_count": projected_fields,
        "requested_layer_a_field_count": 120,
        "semantic_adapter_required": True,
        "semantic_adapter_authorized_during_r5": False,
    }


def report_text(identity_rows: dict[str, Any], probes: dict[str, Any],
                laq_gap: dict[str, Any]) -> str:
    not_run = "NOT RUN — stopped at the earlier frozen phase-authority integration gate."
    sections = [
        ("A. repository authority", "main/HEAD/origin/main/merge-base and the pre-existing 359-entry index authority matched; the pre-first-write porcelain digest was retained."),
        ("B. reviewed starting authority", "PPQ-V2-R1 and LAQ-R1 are GPT REVIEW PASS / CLOSED. The user authorized bounded R5 preparation, subject to unchanged reviewed contracts."),
        ("C. historical STOP preservation", "RE6-R3 remains historical/poisoned and RE6-R4 remains a zero-attempt pre-runtime STOP; neither namespace nor learner was reused."),
        ("D. PPQ-V2-R1 authority", "Identity PASS. Its frozen registry says qualification authorities are OFFLINE-QUALIFICATION-ONLY and are not runtime grants."),
        ("E. LAQ-R1 authority", "Identity PASS. Its frozen registry is an exact R3-path document and its validator rejects R5 path rebinding."),
        ("F. protected source identities", "PASS: current protected identities equal the PPQ-V2-R1 post-final manifest; production semantic modifications are zero."),
        ("G. R5 harness", "Pure/static pre-runtime gate only; it has no formal-worker mode and imports no Isaac, HARL, torch, or CUDA."),
        ("H. exact R5 source-phase authority", "STOP: no formal-runtime authority instance was created because the reviewed schema can validate only its offline qualification scope."),
        ("I. authority validation", "The actual validator accepted the offline control and rejected FORMAL-RUNTIME-AUTHORIZED with PHASE-AUTHORITY-SCOPE."),
        ("J. unique run identity", not_run),
        ("K. run-specific binding", "NOT CREATED. The requested fixed binding filename was also proven incompatible with the frozen filename formula."),
        ("L. artifact namespace binding", not_run),
        ("M. R5 authority registry", "NOT ACTIVATED. LAQ-R1 rejected an otherwise path-only R3-to-R5 registry rebind with AUTHORITY-REGISTRY-PATH-OR-DEFINITION-DRIFT."),
        ("N. registry equivalence", "STOP: a run-specific R5 registry cannot pass the frozen exact-document validator without changing reviewed semantics."),
        ("O. filesystem precondition", not_run),
        ("P. config authority", not_run),
        ("Q. static authority snapshot", not_run),
        ("R. pre-runtime PPQ R5 capability", "The reviewed R5 fixture proves offline contract capability only; it explicitly does not grant runtime authority."),
        ("S. phase-authority negative replay", "2/2 decisive actual-validator negatives STOP: runtime scope and requested authority filename."),
        ("T. Layer-A authority negative replay", "1/1 decisive actual-validator negative STOP: R5 path-rebound registry."),
        ("U. complete synthetic R5 success chain", not_run),
        ("V. preformal freeze", "Protected reviewed identities PASS; formal freeze was not reached because authority construction failed."),
        ("W. final static readiness", "STOP — reviewed contracts cannot integrate as requested without semantic modification."),
        ("X. CUDA/CUBLAS", not_run),
        ("Y. fresh supervisor/worker", "0/0; retries 0."),
        ("Z. runtime config", not_run),
    ]
    remaining = [
        "AA. transaction definition", "AB. transaction inventory", "AC. transaction table",
        "AD. episode/update timeline", "AE. decision gating", "AF. NR", "AG. SR", "AH. ZD",
        "AI. zero-DVM", "AJ. actor plan", "AK. actor evidence", "AL. factor", "AM. critic",
        "AN. ValueNorm", "AO. Adam continuity", "AP. event returns", "AQ. bridges",
        "AR. PW per transaction", "AS. PW campaign", "AT. W1", "AU. W2E inventory",
        "AV. W2E witness", "AW. W2 claim", "AX. W2 continuity", "AY. W2 completion",
        "AZ. W2 clear", "BA. W2 reopen", "BB. W3", "BC. W4", "BD. W5", "BE. W6",
        "BF. W7", "BG. task progress", "BH. terminal/autoreset", "BI. numerical health",
        "BJ. fresh normalization", "BK. normalization/raw crosscheck", "BL. PPQ-V2-R1 receipt",
        "BM. PPQ phase authority", "BN. PPQ run binding", "BO. PPQ persistence/readback",
        "BP. canonical witness publication", "BQ. Layer-A worker receipt",
        "BR. Layer-A structural validation", "BS. Layer-A runtime crosscheck",
        "BT. Layer-A source authority", "BU. live R5 phase authority",
        "BV. live filesystem digest", "BW. inherited predicates", "BX. new authority predicates",
        "BY. complete Layer A", "BZ. env close", "CA. worker receipt durability",
        "CB. app-close handoff", "CC. EP-Q Layer B", "CD. process quiescence",
        "CE. supervisor final adjudication", "CF. exact execution counts",
        "CG. retained nonclaims", "CH. final classification", "CI. GPT-review handoff",
    ]
    custom = {
        "CF. exact execution counts": (
            "Approved-interpreter Python invocations 3 (interpreter check, py_compile, harness); "
            "formal authority/run binding/supervisor/worker/retry 0/0/0/0/0; CUDA/AppLauncher/"
            "environment/reset/learner 0/0/0/0/0; physical/transactions 0/0; git add/commit/push 0/0/0."
        ),
        "CG. retained nonclaims": (
            "No runtime, learner, Layer-A/B, checkpoint, long-training, evaluation/playback, "
            "public-route, or training-quality claim. partial_update=false; route_poisoned=false."
        ),
        "CH. final classification": f"`{CLASSIFICATION}`",
        "CI. GPT-review handoff": (
            "Pre-runtime STOP. A separately reviewed contract revision is required; do not reinterpret "
            "the offline scope as runtime authority and do not retry R5 under this frozen contract set."
        ),
    }
    sections.extend((title, custom.get(title, not_run)) for title in remaining)
    body = "\n\n".join(f"## {title}\n\n{text}" for title, text in sections)
    phase_table = f"""
| Property | Expected | Actual | Result |
|---|---|---|---|
| Source phase | {SOURCE_PHASE} | not instantiated | STOP |
| Expected phase | {SOURCE_PHASE} | not instantiated | STOP |
| Authority phase | {SOURCE_PHASE} | no formal-runtime authority | STOP |
| Authority mode | FORMAL_FRESH_ATTEMPT | offline control only | STOP |
| Authority scope | formal runtime grant | {PPQ_R1.QUALIFICATION_SCOPE} | STOP |
| Authority digest | frozen | not created | STOP |
| Run ID | unique current | not created | NOT RUN |
| Worker PID | current worker | absent | NOT RUN |
| Config digest | R5 config | not created | NOT RUN |
| Namespace | R5 namespace | not activated | NOT RUN |
"""
    layer_table = """
| Layer-A subgate | Result |
|---|---|
| 120 mandatory fields | FROZEN R3 CONTRACT ONLY |
| Structural/schema | NOT RUN |
| Runtime/raw crosscheck | NOT RUN |
| Source authority | STOP: R5 registry rejected |
| PPQ phase authority | STOP: runtime scope not representable |
| PPQ run binding | NOT CREATED |
| Filesystem digest | NOT RUN |
| Production/config identity | production identity PASS; config NOT RUN |
| W1-W7 / PW | NOT RUN |
| Close handoff | NOT RUN |
| Layer A overall | NOT RUN / PRE-RUNTIME STOP |
"""
    runtime_table = """
| Gate | Expected | Actual | Result |
|---|---:|---:|---|
| Physical | 320 | 0 | NOT RUN |
| S10 | 160 | 0 | NOT RUN |
| Ledger | 160 | 0 | NOT RUN |
| Bridges | 159 | 0 | NOT RUN |
| PW critic | 6560 | 0 | NOT RUN |
| PW actor/factor | 640 | 0 | NOT RUN |
| W7 | 160 | 0 | NOT RUN |
| Event returns | 160 | 0 | NOT RUN |
| Stock returns | 0 | 0 | NOT RUN |
| tx161 | false | false | NOT STARTED |
"""
    return f"""# Phase B2-T4-RE6-R5 PPQ-V2-R1 / LAQ-R1 integration qualification report

Classification: `{CLASSIFICATION}`

Outcome: **PRE-RUNTIME STOP / FORMAL ATTEMPTS 0 / NOT POISONED**.

The user's R5 authorization was recognized, but the frozen reviewed contract set cannot encode
that authorization as a formal-runtime authority without changing semantics. The decisive
PPQ-V2-R1 validator accepts only `{PPQ_R1.QUALIFICATION_SCOPE}` and its reviewed contract says
qualification authority is not a runtime grant. The exact requested authority and binding
filenames also fail the frozen path policy. Independently, frozen LAQ-R1 rejects an R5 path-only
registry rebind and is built over the 86-field PPQ-V2 payload rather than the 90-field PPQ-V2-R1
payload. Section 6 therefore requires STOP before the formal run.

{body}

## Primary phase-authority table

{phase_table.strip()}

## Primary Layer-A table

{layer_table.strip()}

## Primary runtime table

{runtime_table.strip()}

## Primary W2 table

No fresh witness exists because runtime did not start.

## Decisive machine evidence

- PPQ runtime-scope negative: `{probes['runtime_scope_negative']['actual_validator_reason']}`.
- PPQ requested authority filename negative: `{probes['requested_authority_filename_negative']['actual_validator_reason']}`.
- PPQ requested binding filename negative: `{probes['requested_binding_filename_negative']['actual_validator_reason']}`.
- LAQ R5 registry negative: `{laq_gap['actual_validator_reason_for_r5_path_rebinding']}`.
- Reviewed identity rows passing: `{sum(row['pass'] for row in identity_rows.values())}/{len(identity_rows)}`.
"""


def main() -> None:
    require(
        Path(sys.executable).resolve() == Path(r"C:\isaacenvs\isaac45_harl\python.exe").resolve(),
        "APPROVED-INTERPRETER",
    )
    require(not OUT.exists(), "R5-ARTIFACT-NAMESPACE-ALREADY-EXISTS")
    require(not REPORT.exists(), "R5-REPORT-ALREADY-EXISTS")

    repository = repository_authority()
    identity_rows = {
        name: {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "expected_sha256": EXPECTED[name],
            "actual_sha256": sha(path),
            "pass": sha(path) == EXPECTED[name],
        }
        for name, path in PATHS.items()
    }
    require(all(row["pass"] for row in identity_rows.values()), "REVIEWED-IDENTITY-MISMATCH")

    current_protected = PPQ_R1_RUNNER.protected_identity()
    prior_protected = read(PPQ_R1_OUT / "protected_source_identity_after.json")
    require(current_protected == prior_protected, "PROTECTED-SOURCE-DRIFT")

    contract = read(PPQ_R1_OUT / "source_phase_authority_contract.json")
    registry = read(PPQ_R1_OUT / "source_phase_authority_registry.json")
    require(contract["qualification_runtime_authority"] is False, "PPQ-RUNTIME-NONCLAIM-DRIFT")
    require(
        registry["qualification_authorities"] == "OFFLINE-QUALIFICATION-ONLY; not runtime grants",
        "PPQ-QUALIFICATION-SCOPE-DRIFT",
    )

    probes = authority_probes()
    laq_gap = laq_integration_probe()

    write("repository_authority.json", repository)
    write(
        "reviewed_starting_authority.json",
        {
            "PPQ_V2_R1": "GPT REVIEW PASS / CLOSED",
            "LAQ_R1": "GPT REVIEW PASS / CLOSED",
            "PPQ_V2": "GPT REVIEW PASS / CLOSED / ORIGINAL PHASE SCOPE",
            "RE6_R3": "HISTORICAL / POISONED / NEVER REUSE LEARNER",
            "RE6_R4": "HISTORICAL PRE-RUNTIME STOP / FORMAL ATTEMPTS 0 / NOT POISONED",
            "RE6_R5": "AUTHORIZED / PREPARATION ENTERED / PRE-RUNTIME STOP",
        },
    )
    write("reviewed_identity_gate.json", {"pass": True, "identities": identity_rows})
    write(
        "protected_source_identity.json",
        {"matches_ppq_v2_r1_post_final": True, "identity": current_protected},
    )
    write(
        "ppq_v2_r1_formal_runtime_authority_gap.json",
        {
            "status": "STOP BEFORE FORMAL RUN",
            "classification": CLASSIFICATION,
            "required_source_phase": SOURCE_PHASE,
            "required_authority_mode": PPQ_R1.FORMAL_MODE,
            "required_runtime_scope": "formal runtime grant",
            "reviewed_qualification_scope": PPQ_R1.QUALIFICATION_SCOPE,
            "reviewed_contract_qualification_runtime_authority": contract[
                "qualification_runtime_authority"
            ],
            "reviewed_registry_statement": registry["qualification_authorities"],
            "semantic_contract_modification_permitted": False,
            "formal_attempt_started": False,
        },
    )
    write("authority_scope_probe.json", probes["runtime_scope_negative"] | {
        "offline_control": probes["offline_control"]
    })
    write("authority_filename_probe.json", probes["requested_authority_filename_negative"])
    write("run_binding_filename_probe.json", probes["requested_binding_filename_negative"])
    write("laq_r1_r5_integration_gap.json", laq_gap)
    write(
        "r5_source_phase_authority_validation.json",
        {
            "status": "STOP",
            "classification": CLASSIFICATION,
            "schema": "NO FORMAL-RUNTIME INSTANCE CREATED",
            "mode": "FORMAL_FRESH_ATTEMPT REPRESENTABLE ONLY INSIDE OFFLINE SCOPE",
            "grammar": "B2-T4-RE6-R5 PASS",
            "exact_phase": "B2-T4-RE6-R5 PASS",
            "canonical_digest": "NOT CREATED",
            "external_runtime_authorization": "NOT REPRESENTABLE BY FROZEN CONTRACT",
            "requested_filename": "REJECTED BY ACTUAL VALIDATOR",
            "formal_authority_instances": 0,
        },
    )
    stop_receipt = {
        "status": "PRE-RUNTIME STOP / NOT POISONED",
        "classification": CLASSIFICATION,
        "failure_stage": "exact_r5_phase_authority_creation",
        "reason": "Frozen PPQ-V2-R1 cannot represent a formal-runtime grant without semantic change",
        "secondary_reason": "Frozen LAQ-R1 rejects R5 path rebinding and PPQ-V2-R1 field composition",
        "learner_mutation_occurred": False,
        "partial_update": False,
        "route_poisoned": False,
        "formal_authority_instances": 0,
        "formal_run_bindings": 0,
        "formal_supervisors": 0,
        "formal_workers": 0,
        "retries": 0,
        "cuda_probes": 0,
        "app_launcher": 0,
        "environment": 0,
        "reset": 0,
        "learner": 0,
        "physical": 0,
        "transactions": 0,
        "checkpoint_io": 0,
        "public_activation": 0,
        "evaluation_playback": 0,
        "git_add_commit_push": [0, 0, 0],
    }
    write("pre_runtime_stop_receipt.json", stop_receipt)
    write(
        "final_result.json",
        stop_receipt
        | {
            "decisive_gate": "PPQ-V2-R1 FORMAL RUNTIME AUTHORITY",
            "reviewed_identity_gate": "PASS",
            "temporary_probe_counts": {
                "offline_authority_fixtures": probes["temporary_offline_authority_fixtures"],
                "offline_binding_fixtures": probes["temporary_offline_binding_fixtures"],
                "phase_authority_negatives": 2,
                "run_binding_negatives": 1,
                "laq_registry_negatives": 1,
            },
            "production_modifications": 0,
            "ppq_v2_r1_modifications": 0,
            "laq_r1_modifications": 0,
            "historical_r3_r4_modifications": 0,
            "next": "separate reviewed contract revision; do not retry this frozen R5 integration",
        },
    )

    REPORT.write_text(report_text(identity_rows, probes, laq_gap), encoding="utf-8")
    print(
        json.dumps(
            {
                "classification": CLASSIFICATION,
                "status": "PRE-RUNTIME STOP / NOT POISONED",
                "formal_authorities": 0,
                "formal_workers": 0,
                "ppq_scope_stop": probes["runtime_scope_negative"]["actual_validator_reason"],
                "laq_registry_stop": laq_gap["actual_validator_reason_for_r5_path_rebinding"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
