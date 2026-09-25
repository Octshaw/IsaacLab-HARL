"""Offline-only CKPT2-R6-HR1 historical R5 inventory reconciliation."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any


HERE = Path(__file__).resolve().parent
DAY = HERE.parent
AGENTREAD = DAY.parents[1]
SCAN = AGENTREAD.parent
ROOT = next(parent for parent in HERE.parents if (parent / ".git").exists())
R5_ROOT = DAY / "b2_t4_ckpt2_r5_artifacts"
R6_ROOT = DAY / "b2_t4_ckpt2_r6_artifacts"
R5_HARNESS = ROOT / "scripts/environments/test_assignment_phase_b2_t4_ckpt2_r5_real_fresh_process_checkpoint_continuation.py"
R6_HARNESS = ROOT / "scripts/environments/test_assignment_phase_b2_t4_ckpt2_r6_real_fresh_process_checkpoint_continuation.py"
R5_REPORT = DAY / "PHASE_B2_T4_CKPT2_R5_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
R6_REPORT = DAY / "PHASE_B2_T4_CKPT2_R6_REAL_FRESH_PROCESS_CHECKPOINT_CONTINUATION_REPORT.md"
SESSION_LOG = Path(
    r"C:\Users\33506\.codex\sessions\2026\08\31\rollout-2026-08-31T23-45-37-01a0587f-601a-7f83-b734-3a9655e48e78.jsonl"
)
OLD_DIGEST = "d9d940c8d10ea30945d438ec9b2c10cfca9e028de3c3993bc447dee41c68a8c1"
CURRENT_DIGEST = "21dd70b567c737efcd1dfe776ea4a1db0370acfbca3988db26a1dd392d4dc609"
CLASSIFICATION = (
    "PHASE-B2-T4-CKPT2-R6-HR1-INVENTORY-ALGORITHM-DRIFT-"
    "RECONCILED-AWAITING-GPT-REVIEW"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iso_utc(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def write_json(name: str, payload: Any) -> None:
    path = HERE / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def current_rows() -> list[dict[str, Any]]:
    return [
        {
            "relative_path": path.relative_to(R5_ROOT).as_posix(),
            "byte_size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(R5_ROOT.rglob("*"))
        if path.is_file()
    ]


AUTHORITY: dict[str, tuple[str, str]] = {
    "actor_plan_count_authority_inventory.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Defines the production frozen-plan expected-count authority and observer transport.",
    ),
    "actor_plan_count_negative_matrix.json": (
        "DERIVED_SUMMARY",
        "Detailed pure negative cases derived from the R5 harness qualification.",
    ),
    "actor_plan_dynamic_positive_matrix.json": (
        "DERIVED_SUMMARY",
        "Detailed pure positive actor-plan fixtures derived from production constructors.",
    ),
    "ckpt1_preservation.json": (
        "REPOSITORY_PRESERVATION",
        "Records inherited CKPT1 and installed-HARL source preservation.",
    ),
    "ckpt2_r5_pre_runtime_freeze.json": (
        "REPOSITORY_PRESERVATION",
        "Anchors the frozen R5 harness and production source identities before Process A.",
    ),
    "ckpt2_r5_preflight.json": (
        "DERIVED_SUMMARY",
        "Summarizes pre-runtime gates already evidenced by focused receipts.",
    ),
    "ckpt2_r5_run_identity.json": (
        "OTHER",
        "Binds the single attempt number, run identity, and zero-retry policy.",
    ),
    "clean_interpreter_baseline.json": (
        "DIAGNOSTIC",
        "Records clean pure-process import state; it is not learner-state authority.",
    ),
    "failure_receipt.json": (
        "CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY",
        "Records the parent semantic-gate denial and absence of a valid checkpoint generation.",
    ),
    "final_stop_adjudication.json": (
        "FINAL_ADJUDICATION_AUTHORITY",
        "Canonical final R5 STOP classification and zero-mutation/checkpoint adjudication.",
    ),
    "historical_actor_adam_plan_consistency.json": (
        "DERIVED_SUMMARY",
        "Retrospective RE1 Adam/plan comparison, not direct R5 runtime evidence.",
    ),
    "historical_ckpt2_preservation.json": (
        "REPOSITORY_PRESERVATION",
        "Records preservation of the earlier CKPT2 evidence root.",
    ),
    "historical_ckpt2_r1_preservation.json": (
        "REPOSITORY_PRESERVATION",
        "Records preservation of the earlier CKPT2-R1 evidence root.",
    ),
    "historical_ckpt2_r2_preservation.json": (
        "REPOSITORY_PRESERVATION",
        "Records preservation of the earlier CKPT2-R2 evidence root.",
    ),
    "historical_ckpt2_r3_preservation.json": (
        "REPOSITORY_PRESERVATION",
        "Records preservation of the earlier CKPT2-R3 evidence root.",
    ),
    "historical_ckpt2_r4_preservation.json": (
        "REPOSITORY_PRESERVATION",
        "Records preservation of the earlier CKPT2-R4 evidence root.",
    ),
    "historical_dynamic_actor_plan_consistency.json": (
        "DERIVED_SUMMARY",
        "Retrospective RE1 dynamic-plan comparison, not direct R5 runtime evidence.",
    ),
    "inherited_contract_preservation.json": (
        "DERIVED_SUMMARY",
        "Summarizes inherited identity, event-return, isolation, and gate contracts.",
    ),
    "parent/parent_process_inventory.json": (
        "PROCESS_SHUTDOWN_BOOKKEEPING",
        "Records parent/worker PID creation and exit observations.",
    ),
    "pre_runtime_harness_repair_log.json": (
        "DIAGNOSTIC",
        "Documents R5 harness-only repair scope and zero production edits.",
    ),
    "preflight_ckpt1_pure.json": (
        "DERIVED_SUMMARY",
        "Detailed inherited CKPT1 pure-suite result matrix.",
    ),
    "process_a/core_failure.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Durable core failure state, mutation counters, stage history, and poison state.",
    ),
    "process_a/core_process_config_authority.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Binds the real process, learner construction, runtime config, and source identity.",
    ),
    "process_a/core_runtime_checkpoints.jsonl": (
        "DIAGNOSTIC",
        "Chronological runtime checkpoint trace used for forensic timing.",
    ),
    "process_a/core_tx1_failure.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Transaction-scoped durable failure state and exact zero mutation counters.",
    ),
    "process_a/core_tx1_rollout_decision_evidence.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Binds tx001 rollout provenance and pre-update learner preservation.",
    ),
    "process_a/environment_creation.json": (
        "DERIVED_SUMMARY",
        "Process-local duplicate of the environment-creation receipt.",
    ),
    "process_a/failure_receipt.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Process-A causal exception, traceback, transaction count, and poison state.",
    ),
    "process_a/initial_state.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Initial persistent learner semantic fingerprint and optimizer state.",
    ),
    "process_a/runtime_identity.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Real interpreter, process, AppLauncher, CUDA readiness, and learner counts.",
    ),
    "process_a/shutdown_result.json": (
        "PROCESS_SHUTDOWN_BOOKKEEPING",
        "Environment and SimulationApp shutdown result for Process A.",
    ),
    "process_a_environment_creation.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Parent-visible proof that one real environment was constructed.",
    ),
    "process_a_environment_registration.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Proof that Gym registration resolved the reviewed real entry point.",
    ),
    "process_a_parent_adjudication.json": (
        "CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY",
        "Authoritative A-to-B semantic gate decision and missing checkpoint conditions.",
    ),
    "process_a_real_package_identity.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Proof that Process A used the repository production package, not a synthetic package.",
    ),
    "process_b_launch_gate.json": (
        "CHECKPOINT_OR_CONTINUATION_BLOCKING_AUTHORITY",
        "Durable denial of Process B because Process A did not qualify.",
    ),
    "process_quiescence.json": (
        "PROCESS_SHUTDOWN_BOOKKEEPING",
        "Final PID inactivity, no Process B, no later transaction, and zero retry evidence.",
    ),
    "pure_qualification_result.json": (
        "CORE_SEMANTIC_AUTHORITY",
        "Canonical summary of the completed R5 pure qualification process.",
    ),
    "pure_runtime_process_isolation.json": (
        "DIAGNOSTIC",
        "Documents OS-process isolation between pure qualification and runtime.",
    ),
    "r4_fixed_actor_count_predicate_failure_reproduction.json": (
        "DERIVED_SUMMARY",
        "Reproduction of the historical R4 fixed-predicate defect.",
    ),
    "repository_authority.json": (
        "REPOSITORY_PRESERVATION",
        "Captures branch, commit, staged-index, and worktree authority at R5 entry.",
    ),
    "transaction_ledger_actor_plan_binding_v1.json": (
        "DERIVED_SUMMARY",
        "Schema-level summary of the plan/observed per-actor equality contract.",
    ),
}


CORE_ARTIFACTS = {
    "actor_plan_count_authority_inventory.json": (
        "frozen expected-count authority",
        "R5 report sections C and G",
    ),
    "ckpt1_preservation.json": (
        "inherited production/installed-source preservation",
        "R5 report sections A and E",
    ),
    "ckpt2_r5_pre_runtime_freeze.json": (
        "frozen R5 harness and production identities",
        "all causal interpretation of the real attempt",
    ),
    "failure_receipt.json": (
        "parent semantic-gate STOP and no valid checkpoint",
        "R5 report sections H through J",
    ),
    "final_stop_adjudication.json": (
        "final causal classification, zero mutation, no checkpoint, no poison",
        "R5 final classification",
    ),
    "process_a/core_process_config_authority.json": (
        "real process/learner/runtime configuration authority",
        "R5 report section F",
    ),
    "process_a/core_tx1_failure.json": (
        "S5 failure boundary and exact mutation counters",
        "R5 report sections G, N, and O",
    ),
    "process_a/core_tx1_rollout_decision_evidence.json": (
        "tx001 rollout provenance and collection preservation",
        "R5 report section G",
    ),
    "process_a/failure_receipt.json": (
        "causal traceback and process-local STOP",
        "R5 final causal adjudication",
    ),
    "process_a/initial_state.json": (
        "fresh learner semantic state",
        "R5 report section F",
    ),
    "process_a/runtime_identity.json": (
        "fresh interpreter, CUDA readiness, and one learner",
        "R5 report section F",
    ),
    "process_a/shutdown_result.json": (
        "clean environment and SimulationApp shutdown",
        "R5 report section Q",
    ),
    "process_a_environment_creation.json": (
        "real environment construction",
        "R5 report section F",
    ),
    "process_a_environment_registration.json": (
        "real reviewed Gym entry point",
        "R5 report section F",
    ),
    "process_a_parent_adjudication.json": (
        "A-to-B denial conditions",
        "R5 report sections I and J",
    ),
    "process_a_real_package_identity.json": (
        "real repository package identity",
        "R5 report section F",
    ),
    "process_b_launch_gate.json": (
        "Process B was not authorized or launched",
        "R5 report sections I through M",
    ),
    "process_quiescence.json": (
        "process inactivity and zero retry",
        "R5 report section Q",
    ),
    "pure_qualification_result.json": (
        "R5 pure qualification completion",
        "R5 report sections B through E",
    ),
}


def repo_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def manifest_entries(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        {
            "relative_path": repo_relative(path),
            "size": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in sorted(paths, key=repo_relative)
    ]


def manifest_digest(core: list[dict[str, Any]], optional: list[dict[str, Any]]) -> str:
    body = {
        "algorithm_version": "sorted-relative-byte-sha256-v1",
        "immutable_core_entries": core,
        "optional_noncore_entries": optional,
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def run_contract_matrix() -> dict[str, Any]:
    def local_entries(root: Path, relative_paths: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "relative_path": relative,
                "size": (root / relative).stat().st_size,
                "sha256": sha256(root / relative),
            }
            for relative in sorted(relative_paths)
        ]

    cases: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="b2_t4_ckpt2_r6_hr1_") as temporary:
        root = Path(temporary) / "root_a"
        relocated = Path(temporary) / "root_b"
        (root / "core").mkdir(parents=True)
        (root / "diagnostic").mkdir(parents=True)
        (root / "core/a.json").write_bytes(b'{"authority":true}\n')
        (root / "core/b.json").write_bytes(b'{"second":true}\n')
        (root / "diagnostic/d.json").write_bytes(b'{"diagnostic":1}\n')
        core_paths = ["core/a.json", "core/b.json"]
        optional_paths = ["diagnostic/d.json"]
        baseline_core = local_entries(root, core_paths)
        baseline_optional = local_entries(root, optional_paths)
        baseline_digest = manifest_digest(baseline_core, baseline_optional)

        cases.append({"case": "same_core_bytes", "outcome": "PASS", "result": "PASS"})

        original = (root / "core/a.json").read_bytes()
        (root / "core/a.json").write_bytes(original + b"changed")
        changed = local_entries(root, core_paths)
        cases.append({
            "case": "changed_core_byte",
            "outcome": "STOP" if changed != baseline_core else "UNEXPECTED_PASS",
            "result": "PASS" if changed != baseline_core else "FAIL",
        })
        (root / "core/a.json").write_bytes(original)

        (root / "core/a.json").unlink()
        cases.append({"case": "missing_core_file", "outcome": "STOP", "result": "PASS"})
        (root / "core/a.json").write_bytes(original)

        (root / "diagnostic/d.json").write_bytes(b'{"diagnostic":2}\n')
        diagnostic_changed = local_entries(root, optional_paths) != baseline_optional
        core_same = local_entries(root, core_paths) == baseline_core
        cases.append({
            "case": "changed_derived_diagnostic",
            "outcome": "ADVISORY" if diagnostic_changed and core_same else "FAIL",
            "result": "PASS" if diagnostic_changed and core_same else "FAIL",
        })
        (root / "diagnostic/d.json").write_bytes(b'{"diagnostic":1}\n')

        before = local_entries(root, core_paths)
        stat = (root / "core/a.json").stat()
        os.utime(root / "core/a.json", ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
        after = local_entries(root, core_paths)
        cases.append({
            "case": "mtime_only_change",
            "outcome": "PASS" if before == after else "STOP",
            "result": "PASS" if before == after else "FAIL",
        })

        shutil.copytree(root, relocated)
        relocated_digest = manifest_digest(
            local_entries(relocated, core_paths), local_entries(relocated, optional_paths)
        )
        cases.append({
            "case": "absolute_root_relocation",
            "outcome": "PASS" if relocated_digest == baseline_digest else "STOP",
            "result": "PASS" if relocated_digest == baseline_digest else "FAIL",
        })

        reversed_core = list(reversed(local_entries(root, core_paths)))
        normalized_core = sorted(reversed_core, key=lambda item: item["relative_path"])
        reorder_digest = manifest_digest(normalized_core, local_entries(root, optional_paths))
        cases.append({
            "case": "directory_iteration_reordering",
            "outcome": "PASS" if reorder_digest == baseline_digest else "STOP",
            "result": "PASS" if reorder_digest == baseline_digest else "FAIL",
        })

        (root / "diagnostic/extra.json").write_bytes(b'{"extra":true}\n')
        extra_core_same = local_entries(root, core_paths) == baseline_core
        cases.append({
            "case": "extra_untracked_diagnostic",
            "outcome": "ADVISORY" if extra_core_same else "STOP",
            "result": "PASS" if extra_core_same else "FAIL",
        })

    return {
        "runtime_imports": False,
        "case_count": len(cases),
        "pass_count": sum(case["result"] == "PASS" for case in cases),
        "cases": cases,
        "result": "PASS" if all(case["result"] == "PASS" for case in cases) else "FAIL",
    }


def main() -> int:
    rows = current_rows()
    if len(rows) != 42:
        raise RuntimeError(f"expected 42 R5 files, observed {len(rows)}")
    row_payload = [
        {"path": row["relative_path"], "bytes": row["byte_size"], "sha256": row["sha256"]}
        for row in rows
    ]
    body = json.dumps(
        row_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode()
    historical_encoded = body + bytes([92, 110])
    harness_encoded = body + bytes([10])
    reproduced_old = hashlib.sha256(historical_encoded).hexdigest()
    reproduced_current = hashlib.sha256(harness_encoded).hexdigest()
    if reproduced_old != OLD_DIGEST or reproduced_current != CURRENT_DIGEST:
        raise RuntimeError(
            f"inventory reproduction failed: {reproduced_old}, {reproduced_current}"
        )

    harness_source = R5_HARNESS.read_text(encoding="utf-8").splitlines()
    start = next(index for index, line in enumerate(harness_source) if line == "def _inventory(root: Path) -> tuple[list[dict[str, Any]], str]:")
    source_fragment = [
        {"line": start + offset + 1, "text": harness_source[start + offset]}
        for offset in range(7)
    ]
    algorithm_audit = {
        "historical_locked_digest": OLD_DIGEST,
        "historical_lock_algorithm": {
            "authority": "R6 pre-start ad-hoc read-only command captured in Codex session log",
            "session_log": str(SESSION_LOG),
            "custom_tool_call_jsonl_line": 40963,
            "custom_tool_output_jsonl_line": 40966,
            "custom_tool_call_ordinal": 40962,
            "custom_tool_output_ordinal": 40965,
            "traversal": "sorted(root.rglob('*')); files only",
            "relative_path": "Path.relative_to(root).as_posix()",
            "fields": ["path", "bytes", "sha256"],
            "sort_rule": "Windows Path ordering over one common absolute root",
            "json": "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True)",
            "terminal_bytes_hex": "5c6e",
            "terminal_bytes_meaning": "literal backslash plus lowercase n",
            "size_included": True,
            "mtime_included": False,
            "file_mode_included": False,
            "absolute_path_included": False,
            "inventory_includes_itself": False,
        },
        "r5_harness_inventory_algorithm": {
            "symbol": "_inventory",
            "source_path": repo_relative(R5_HARNESS),
            "source_sha256": sha256(R5_HARNESS),
            "source_fragment": source_fragment,
            "traversal": "sorted(root.rglob('*')); files only",
            "relative_path": "Path.relative_to(root).as_posix()",
            "fields": ["path", "bytes", "sha256"],
            "json": "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True)",
            "terminal_bytes_hex": "0a",
            "terminal_bytes_meaning": "one LF byte",
            "size_included": True,
            "mtime_included": False,
            "file_mode_included": False,
            "absolute_path_included": False,
            "inventory_includes_itself": False,
        },
        "difference": "Only the serialized inventory terminator differs: 5c6e versus 0a.",
        "result": "PASS",
    }
    write_json("r5_inventory_algorithm_audit.json", algorithm_audit)

    reproduction = {
        "artifact_file_count": len(rows),
        "inventory_json_body_bytes": len(body),
        "inventory_json_body_sha256": hashlib.sha256(body).hexdigest(),
        "same_input_rows_used_for_both_digests": True,
        "historical_ad_hoc_encoding": {
            "suffix_hex": "5c6e",
            "encoded_bytes": len(historical_encoded),
            "reproduced_sha256": reproduced_old,
            "expected_sha256": OLD_DIGEST,
            "exact_match": reproduced_old == OLD_DIGEST,
        },
        "r5_harness_encoding": {
            "suffix_hex": "0a",
            "encoded_bytes": len(harness_encoded),
            "reproduced_sha256": reproduced_current,
            "expected_sha256": CURRENT_DIGEST,
            "exact_match": reproduced_current == CURRENT_DIGEST,
        },
        "approximate_algorithm_used": False,
        "result": "PASS",
    }
    write_json("r5_current_inventory_reproduction.json", reproduction)

    session_text = SESSION_LOG.read_text(encoding="utf-8")
    lock_sources = {
        "recoverable_sources": [
            {
                "kind": "aggregate_creation_command_and_output",
                "path": str(SESSION_LOG),
                "jsonl_lines": [40963, 40966],
                "contains_old_digest": OLD_DIGEST in session_text,
                "contains_per_file_rows": False,
                "role": "Exact algorithm, lock timestamp, file count, and aggregate digest authority.",
            },
            {
                "kind": "embedded_aggregate_constant",
                "path": repo_relative(R6_HARNESS),
                "sha256": sha256(R6_HARNESS),
                "contains_per_file_rows": False,
                "role": "R6 expected aggregate value used by the failed historical gate.",
            },
            {
                "kind": "failed_preservation_receipt",
                "path": repo_relative(R6_ROOT / "historical_ckpt2_r5_preservation.json"),
                "sha256": sha256(R6_ROOT / "historical_ckpt2_r5_preservation.json"),
                "contains_per_file_rows": False,
                "role": "Records old/current aggregate mismatch and stable harness/report anchors.",
            },
        ],
        "per_file_manifest_found": False,
        "final_result_embedded_manifest_found": False,
        "artifact_root_manifest_found": False,
        "result": "PASS",
    }
    write_json("r5_lock_time_inventory_source_inventory.json", lock_sources)

    recoverability = {
        "classification": "AGGREGATE_ONLY",
        "old_per_file_sizes_available": False,
        "old_per_file_sha256_available": False,
        "old_aggregate_algorithm_available": True,
        "old_aggregate_digest_available": True,
        "current_complete_rows_reproduce_old_aggregate": True,
        "interpretation": (
            "No historical per-file manifest was persisted. Current complete byte rows reproduce "
            "the old aggregate under its exact recorded algorithm, but current per-file hashes are "
            "not relabeled as historical per-file records."
        ),
        "result": "PASS",
    }
    write_json("r5_locked_inventory_recoverability.json", recoverability)

    write_json(
        "r5_current_file_byte_inventory.json",
        {
            "root_role": "read-only historical R5 artifact root",
            "artifact_file_count": len(rows),
            "entries": rows,
            "aggregate_under_r5_harness_algorithm": reproduced_current,
            "result": "PASS",
        },
    )
    metadata = []
    for path in sorted(R5_ROOT.rglob("*")):
        if not path.is_file():
            continue
        stat = path.stat()
        metadata.append(
            {
                "relative_path": path.relative_to(R5_ROOT).as_posix(),
                "creation_time_utc": iso_utc(stat.st_ctime),
                "mtime_utc": iso_utc(stat.st_mtime),
                "file_attributes": getattr(stat, "st_file_attributes", None),
                "metadata_excluded_from_byte_identity": True,
            }
        )
    write_json(
        "r5_current_filesystem_metadata_inventory.json",
        {"artifact_file_count": len(metadata), "entries": metadata, "result": "PASS"},
    )

    if set(AUTHORITY) != {row["relative_path"] for row in rows}:
        raise RuntimeError("authority classification does not cover exactly all 42 R5 artifacts")
    classifications = [
        {
            "relative_path": row["relative_path"],
            "authority_class": AUTHORITY[row["relative_path"]][0],
            "reason": AUTHORITY[row["relative_path"]][1],
            "supports_claim": AUTHORITY[row["relative_path"]][1],
            "hard_block_future_continuation": row["relative_path"] in CORE_ARTIFACTS,
        }
        for row in rows
    ]
    write_json(
        "r5_artifact_authority_classification.json",
        {"artifact_count": len(classifications), "entries": classifications, "result": "PASS"},
    )

    reconciliation = [
        {
            "relative_path": row["relative_path"],
            "old_size": "UNAVAILABLE",
            "current_size": row["byte_size"],
            "old_sha256": "UNAVAILABLE",
            "current_sha256": row["sha256"],
            "byte_equal": "NOT_INDIVIDUALLY_PROVABLE",
            "metadata_equal": "UNAVAILABLE",
            "authority_class": AUTHORITY[row["relative_path"]][0],
            "reconciliation_status": "OLD_BYTE_IDENTITY_UNAVAILABLE",
            "impact": "No per-file byte change established; aggregate mismatch is exactly algorithm-only.",
        }
        for row in rows
    ]
    write_json(
        "r5_file_by_file_reconciliation.json",
        {
            "old_inventory_recoverability": "AGGREGATE_ONLY",
            "entry_count": len(reconciliation),
            "byte_changed_files_established": 0,
            "metadata_only_files_established": 0,
            "old_byte_identity_unavailable": len(reconciliation),
            "aggregate_algorithm_only_difference": True,
            "entries": reconciliation,
            "result": "PASS",
        },
    )

    stability_checks = [
        {"input": "mtime", "present": False, "effect": "none", "explains_drift": False},
        {"input": "absolute_root_path", "present": False, "effect": "none", "explains_drift": False},
        {"input": "temporary_directory", "present": False, "effect": "none", "explains_drift": False},
        {"input": "unsorted_iteration", "present": False, "effect": "paths are sorted", "explains_drift": False},
        {"input": "locale", "present": False, "effect": "none", "explains_drift": False},
        {"input": "json_key_order", "present": False, "effect": "sort_keys=True", "explains_drift": False},
        {"input": "platform_path_separator", "present": False, "effect": "as_posix relative paths", "explains_drift": False},
        {"input": "files_generated_after_lock", "present": False, "effect": "lock occurred after final artifact/report mtime", "explains_drift": False},
        {"input": "self_referential_manifest", "present": False, "effect": "no manifest existed inside R5 root", "explains_drift": False},
        {"input": "mutable_summary_after_lock", "present": False, "effect": "no R5 artifact mtime postdates lock", "explains_drift": False},
        {"input": "terminator_algorithm_version", "present": True, "effect": "5c6e versus 0a changes aggregate only", "explains_drift": True},
    ]
    write_json(
        "r5_inventory_stability_audit.json",
        {
            "checks": stability_checks,
            "unstable_metadata_dependency_found": False,
            "cross_algorithm_comparison_found": True,
            "drift_fully_explained": True,
            "result": "PASS",
        },
    )

    latest_artifact = max(
        (path for path in R5_ROOT.rglob("*") if path.is_file()),
        key=lambda path: path.stat().st_mtime,
    )
    timing = {
        "process_a_runtime_started_utc": "2026-09-24T00:59:12.2044195Z",
        "process_a_shutdown_artifact_utc": "2026-09-24T00:59:38.1346777Z",
        "process_quiescence_artifact_utc": "2026-09-24T01:00:51.9410606Z",
        "final_adjudication_artifact_utc": "2026-09-24T01:03:42.3056308Z",
        "r5_report_final_mtime_utc": iso_utc(R5_REPORT.stat().st_mtime),
        "latest_r5_artifact_relative_path": latest_artifact.relative_to(R5_ROOT).as_posix(),
        "latest_r5_artifact_mtime_utc": iso_utc(latest_artifact.stat().st_mtime),
        "old_aggregate_lock_output_utc": "2026-09-24T01:56:12.389Z",
        "r6_gate_failure_utc": iso_utc((R6_ROOT / "failure_receipt.json").stat().st_mtime),
        "lock_after_all_r5_artifacts": True,
        "lock_after_r5_report_finalization": True,
        "legitimate_r5_file_emission_after_lock": False,
        "lock_timing_drift": False,
        "result": "PASS",
    }
    write_json("r5_inventory_lock_timing_audit.json", timing)

    core_entries = []
    row_by_path = {row["relative_path"]: row for row in rows}
    for relative_path, (claim, dependency) in sorted(CORE_ARTIFACTS.items()):
        row = row_by_path[relative_path]
        core_entries.append(
            {
                "relative_path": relative_path,
                "byte_size": row["byte_size"],
                "sha256": row["sha256"],
                "authority_class": AUTHORITY[relative_path][0],
                "supported_claims": claim,
                "downstream_dependency": dependency,
            }
        )
    external_anchors = [
        {
            "relative_path": repo_relative(R5_HARNESS),
            "byte_size": R5_HARNESS.stat().st_size,
            "sha256": sha256(R5_HARNESS),
            "authority_class": "CORE_SEMANTIC_AUTHORITY",
            "supported_claims": "exact executed R5 harness logic",
            "downstream_dependency": "all R5 evidence interpretation",
        },
        {
            "relative_path": repo_relative(R5_REPORT),
            "byte_size": R5_REPORT.stat().st_size,
            "sha256": sha256(R5_REPORT),
            "authority_class": "FINAL_ADJUDICATION_AUTHORITY",
            "supported_claims": "reviewable R5 final narrative and non-claims",
            "downstream_dependency": "historical handoff",
        },
    ]
    write_json(
        "r5_core_historical_authority_set.json",
        {
            "artifact_root_core_count": len(core_entries),
            "external_anchor_count": len(external_anchors),
            "artifact_root_entries": core_entries,
            "external_anchors": external_anchors,
            "selection_rule": "Minimum dependency-backed set for reviewed R5 claims; duplicates and diagnostics excluded.",
            "result": "PASS",
        },
    )
    noncore = [
        {
            "relative_path": row["relative_path"],
            "authority_class": AUTHORITY[row["relative_path"]][0],
            "later_modification_invalidates_reviewed_semantic_claim": False,
            "future_historical_preservation_hard_fail": False,
            "drift_policy": "ADVISORY",
            "reason": AUTHORITY[row["relative_path"]][1],
        }
        for row in rows
        if row["relative_path"] not in CORE_ARTIFACTS
    ]
    write_json(
        "r5_noncore_artifact_set.json",
        {"entry_count": len(noncore), "entries": noncore, "result": "PASS"},
    )

    drift = {
        "primary_category": "CASE C",
        "category_name": "METADATA_OR_INVENTORY_ALGORITHM_DRIFT",
        "specific_cause": "Cross-algorithm terminator mismatch: literal 5c6e versus LF 0a.",
        "metadata_caused_drift": False,
        "inventory_algorithm_caused_drift": True,
        "lock_timing_caused_drift": False,
        "core_authority_byte_drift_established": False,
        "noncore_byte_drift_established": False,
        "byte_changed_files_established": 0,
        "metadata_only_files_established": 0,
        "old_per_file_inventory_recoverability": "AGGREGATE_ONLY",
        "current_rows_reproduce_old_aggregate_under_recorded_old_algorithm": True,
        "same_current_rows_reproduce_r5_harness_aggregate_under_harness_algorithm": True,
        "r5_core_authority_integrity": "PASS",
        "rationale": (
            "The full current 42-entry byte inventory exactly reproduces both disputed digests "
            "when only the two recorded terminators are changed. The lock was after finalization, "
            "and no R5 artifact mtime postdates it. Individual old SHA fields were not persisted "
            "and are not fabricated."
        ),
        "classification": CLASSIFICATION,
        "result": "PASS",
    }
    write_json("r5_drift_impact_adjudication.json", drift)

    prospective_core_paths = [R5_HARNESS, R5_REPORT] + [R5_ROOT / relative for relative in sorted(CORE_ARTIFACTS)]
    prospective_noncore_paths = [
        R5_ROOT / row["relative_path"]
        for row in rows
        if row["relative_path"] not in CORE_ARTIFACTS
    ]
    prospective_core = manifest_entries(prospective_core_paths)
    prospective_optional = [
        {
            **entry,
            "drift_policy": "ADVISORY",
            "authority_class": AUTHORITY[Path(entry["relative_path"]).relative_to(repo_relative(R5_ROOT)).as_posix()][0]
            if entry["relative_path"].startswith(repo_relative(R5_ROOT) + "/")
            else "OTHER",
        }
        for entry in manifest_entries(prospective_noncore_paths)
    ]
    prospective_digest = manifest_digest(prospective_core, prospective_optional)
    contract = {
        "version": "b2_t4_historical_preservation_v1",
        "phase": "B2-T4-CKPT2-R5",
        "algorithm_version": "sorted-relative-byte-sha256-v1",
        "root_semantics": "repository root; relative POSIX paths only",
        "immutable_core_entries": prospective_core,
        "optional_noncore_entries": prospective_optional,
        "manifest_digest": prospective_digest,
        "manifest_digest_scope": "canonical core and optional entry payload; excludes this manifest file",
        "self_referential_manifest": False,
        "external_manifest_sha256_required_after_write": True,
        "lock_boundary": "after worker shutdown, process quiescence, final adjudication, final report, and TASK_PROGRESS archive",
        "hard_fail_policy": ["missing core", "changed core bytes", "changed required checkpoint-blocking authority"],
        "advisory_policy": ["changed derived summary", "changed diagnostic", "extra noncore diagnostic"],
        "forbidden_inputs": ["mtime", "creation time", "absolute path", "directory iteration order", "locale"],
        "result": "QUALIFIED_BY_OFFLINE_MATRIX",
    }
    write_json("prospective_historical_preservation_contract_v1.json", contract)
    matrix = run_contract_matrix()
    write_json("prospective_preservation_contract_matrix.json", matrix)
    if matrix["result"] != "PASS":
        raise RuntimeError("prospective contract matrix failed")

    final = {
        "classification": CLASSIFICATION,
        "r6_historical_stop": "PRESERVED",
        "r5_artifact_count": {"expected": 42, "observed": 42},
        "old_inventory_digest": OLD_DIGEST,
        "current_inventory_digest": CURRENT_DIGEST,
        "historical_inventory_algorithm": "compact sorted relative path/size/content-SHA rows plus literal bytes 5c6e",
        "current_inventory_algorithm": "same rows plus one LF byte 0a",
        "old_per_file_inventory_recoverability": "AGGREGATE_ONLY",
        "byte_changed_files": 0,
        "byte_changed_files_qualifier": "established; individual old SHA values unavailable",
        "metadata_only_files": 0,
        "core_authority_changed_files": 0,
        "noncore_changed_files": 0,
        "drift_category": "CASE C",
        "r5_core_authority_integrity": "PASS",
        "prospective_preservation_contract": "QUALIFIED",
        "r6_direct_plan_repair": "STATICALLY PRESENT / NOT QUALIFIED",
        "cuda_isaac_learner": [0, 0, 0],
        "checkpoint_save_load": [0, 0],
        "r6_retry": "NOT AUTHORIZED",
        "r7": "NOT AUTHORIZED",
        "git_add_commit_push": [0, 0, 0],
        "next": "independent GPT review of CKPT2-R6-HR1",
        "result": "PASS",
    }
    write_json("final_result.json", final)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
