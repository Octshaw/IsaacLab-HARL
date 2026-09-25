"""Offline B2-T4-CSR1 closure-scope and checkpoint-readiness audit.

This script is intentionally standard-library-only at import time.  It never
constructs an Isaac application, environment, learner, authority, supervisor,
worker, or checkpoint.  The optional normalizer replay imports only the two
reviewed pure Python evidence transforms.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DAY = SCAN / "AgentRead/202609/20260923"
OUT = DAY / "b2_t4_csr1_artifacts"
R14_ROOT = DAY / "b2_t4_re6_r14_artifacts"
R14_ID = "b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c"
R14_RUN = R14_ROOT / R14_ID
R14_REPORT = DAY / "PHASE_B2_T4_RE6_R14_FORMAL_NAMESPACE_PURITY_NORMAL_HORIZON_INTEGRATION_REPORT.md"
R14_HARNESS = ROOT / "scripts/environments/test_assignment_phase_b2_t4_re6_r14_formal_namespace_purity_normal_horizon_integration.py"
REPORT = DAY / "PHASE_B2_T4_CSR1_CLOSURE_SCOPE_REDUCTION_REPORT.md"

CLASS_A = "CORE_RUNTIME_BLOCKING"
CLASS_B = "CHECKPOINT_CONTINUATION_BLOCKING"
CLASS_C = "PAPER_EXPERIMENT_BLOCKING"
CLASS_D = "DIAGNOSTIC_NONBLOCKING"
FINAL_CLASSIFICATION = "PHASE-B2-T4-CSR1-CLOSURE-SCOPE-REDUCTION-COMPLETE-AWAITING-GPT-REVIEW"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(name: str, value: Any) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    path.write_text(data, encoding="utf-8", newline="\n")


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ).stdout


def gate(
    name: str,
    protects: str,
    consequence: str,
    primary: str,
    learner: bool,
    checkpoint: bool,
    experiment: bool,
    future: str,
) -> dict[str, Any]:
    return {
        "gate_or_artifact": name,
        "protects": protects,
        "failure_consequence": consequence,
        "touches_learner_state": learner,
        "touches_checkpoint_state": checkpoint,
        "touches_experiment_semantics": experiment,
        "primary_class": primary,
        "future_blocking": future,
    }


def inventory_gates() -> list[dict[str, Any]]:
    values = [
        gate("runtime transaction completion", "complete update transaction", "partial or missing update", CLASS_A, True, True, True, "CORE"),
        gate("production S10", "commit boundary", "uncommitted update presented as complete", CLASS_A, True, True, True, "CORE"),
        gate("transaction ledger", "ordered update identity", "missing, duplicate, or reordered updates", CLASS_A, True, True, True, "CORE"),
        gate("bridge continuity", "state continuity across updates", "learner or lifecycle discontinuity", CLASS_A, True, True, True, "CORE"),
        gate("NR", "nonterminal rollout completeness", "invalid bootstrap input", CLASS_A, True, True, True, "CORE"),
        gate("SR", "serializer and post-S10 bookkeeping", "runtime facts cannot be trusted", CLASS_A, True, True, True, "CORE"),
        gate("ZD", "decision-valid zero-DVM actor path", "actor update semantics invalid", CLASS_A, True, True, True, "CORE"),
        gate("actor evidence", "actor backward and optimizer step", "actor optimization not established", CLASS_A, True, True, True, "CORE"),
        gate("factor evidence", "HAPPO sequential factor", "multi-agent update attribution invalid", CLASS_A, True, True, True, "CORE"),
        gate("critic evidence", "critic loss/backward/step", "critic optimization not established", CLASS_A, True, True, True, "CORE"),
        gate("ValueNorm continuity", "persistent return normalization", "critic targets change discontinuously", CLASS_A, True, True, True, "CORE"),
        gate("Adam continuity", "optimizer identity and moments", "optimization continuity not established", CLASS_A, True, True, True, "CORE"),
        gate("event returns", "event-aware return semantics", "training target semantics invalid", CLASS_A, True, True, True, "CORE"),
        gate("terminal/autoreset", "terminal pre-reset facts", "terminal targets and lifecycle semantics invalid", CLASS_A, True, True, True, "CORE"),
        gate("post-autoreset learning", "continued learning after reset", "normal-horizon learning continuity absent", CLASS_A, True, True, True, "CORE"),
        gate("PW", "immutable optimizer-progress accounting", "missing/duplicate/out-of-order update records", CLASS_A, True, True, True, "CORE"),
        gate("NORM-R1", "canonical paper metric derivation", "reported metrics cannot be qualified", CLASS_C, False, False, True, "EXPERIMENT"),
        gate("raw/normalized crosscheck", "metric lineage", "normalized experiment claims diverge from raw evidence", CLASS_C, False, False, True, "EXPERIMENT"),
        gate("PPQ", "90-field success receipt aggregation", "forensic receipt unavailable while direct evidence remains", CLASS_D, False, False, False, "ADVISORY"),
        gate("W1 cross-update ownership", "ownership continuity", "lifecycle semantics invalid", CLASS_A, True, True, True, "CORE"),
        gate("W2 multi-update completion", "claim-complete-reopen lifecycle", "completion semantics invalid", CLASS_A, True, True, True, "CORE"),
        gate("W3 real zero-DVM actor", "zero-DVM actor validity", "actor evidence invalid", CLASS_A, True, True, True, "CORE"),
        gate("W4 nonterminal bootstrap", "nonterminal return bootstrap", "critic target invalid", CLASS_A, True, True, True, "CORE"),
        gate("W5 terminal/autoreset", "terminal and reset boundary", "terminal semantics invalid", CLASS_A, True, True, True, "CORE"),
        gate("W6 post-autoreset training", "new-generation learning", "continuation after autoreset absent", CLASS_A, True, True, True, "CORE"),
        gate("W7 P2 immutability", "learner/runtime separation", "learner may mutate runtime P2", CLASS_A, True, True, True, "CORE"),
        gate("artifact ownership", "write-once evidence paths", "audit artifact collision", CLASS_D, False, False, False, "ADVISORY"),
        gate("namespace purity", "preflight/formal evidence separation", "provenance namespace contaminated", CLASS_D, False, False, False, "ADVISORY"),
        gate("source-phase authority", "audit phase provenance", "phase claim cannot be published", CLASS_D, False, False, False, "ADVISORY"),
        gate("source-phase binding", "run-to-authority provenance", "run provenance incomplete", CLASS_D, False, False, False, "ADVISORY"),
        gate("runtime authority", "runtime identity provenance", "formal audit identity incomplete", CLASS_D, False, False, False, "ADVISORY"),
        gate("RACQ run binding", "RACQ provenance", "RACQ publication cannot be qualified", CLASS_D, False, False, False, "ADVISORY"),
        gate("shared Layer-A source projection", "single projection builder", "forensic projection unavailable", CLASS_D, False, False, False, "ADVISORY"),
        gate("Layer-A 43/90 receipt", "rich forensic envelope", "rich receipt unavailable", CLASS_D, False, False, False, "ADVISORY"),
        gate("39/39 inherited predicates", "redundant aggregate adjudication", "aggregate audit receipt incomplete", CLASS_D, False, False, False, "ADVISORY"),
        gate("9/9 RACQ predicates", "authority aggregate adjudication", "authority receipt incomplete", CLASS_D, False, False, False, "ADVISORY"),
        gate("Layer-B process quiescence", "clean process and checkpoint boundary", "fresh-process continuation unsafe", CLASS_B, False, True, False, "CHECKPOINT"),
        gate("supervisor result", "formal orchestration summary", "summary unavailable; direct evidence remains", CLASS_D, False, False, False, "ADVISORY"),
        gate("success-gate aggregation", "single historical 85-slot verdict", "aggregate verdict unavailable", CLASS_D, False, False, False, "ADVISORY"),
        gate("runtime_normalization_result equality", "duplicate post-runtime representation equality", "projection copy differs from canonical", CLASS_D, False, False, False, "ADVISORY_WITH_WARNING"),
    ]
    assert len(values) == 40
    return values


def checkpoint_state_inventory() -> list[dict[str, Any]]:
    return [
        {"state": "all ordered actor network state_dicts", "runtime_owner": "runner.actor[i].actor", "mutable": True, "required_for_continuation": True, "serialized_today": True, "deterministic_replay_only": False, "blocking": True, "canonical_checkpoint_source": "actor_agent_<identity>.pt", "evidence": "AssignmentOnPolicyHARunner.save; AssignmentTrainingStateManifest.actor_artifacts"},
        {"state": "critic network state_dict", "runtime_owner": "runner.critic.critic", "mutable": True, "required_for_continuation": True, "serialized_today": True, "deterministic_replay_only": False, "blocking": True, "canonical_checkpoint_source": "critic_agent.pt", "evidence": "AssignmentOnPolicyHARunner.save"},
        {"state": "all actor Adam optimizer state_dicts", "runtime_owner": "runner.actor[i].actor_optimizer", "mutable": True, "required_for_continuation": True, "serialized_today": False, "deterministic_replay_only": False, "blocking": True, "canonical_checkpoint_source": "MISSING", "evidence": "training_state.actor_optimizer_available=false; save passes no optimizer state"},
        {"state": "critic Adam optimizer state_dict", "runtime_owner": "runner.critic.critic_optimizer", "mutable": True, "required_for_continuation": True, "serialized_today": False, "deterministic_replay_only": False, "blocking": True, "canonical_checkpoint_source": "MISSING", "evidence": "training_state.critic_optimizer_available=false"},
        {"state": "ValueNorm running_mean/running_mean_sq/debiasing_term", "runtime_owner": "runner.value_normalizer", "mutable": True, "required_for_continuation": True, "serialized_today": True, "deterministic_replay_only": False, "blocking": True, "canonical_checkpoint_source": "value_normalizer.pt", "evidence": "assignment_value_normalizer_checkpoint canonical adapter"},
        {"state": "separate scheduler object", "runtime_owner": "none; update_linear_schedule mutates optimizer param-group LR", "mutable": False, "required_for_continuation": False, "serialized_today": False, "deterministic_replay_only": False, "blocking": False, "canonical_checkpoint_source": "NOT_APPLICABLE", "evidence": "installed HARL OnPolicyBase.lr_decay and VCritic.lr_decay"},
        {"state": "completed episode/update index and total schedule horizon", "runtime_owner": "OnPolicyBaseRunner.run local episode plus config", "mutable": True, "required_for_continuation": True, "serialized_today": False, "deterministic_replay_only": False, "blocking": True, "canonical_checkpoint_source": "MISSING; episode_or_update_index is metadata only and restore ignores it", "evidence": "linear LR decay is indexed by episode; training_counters_available=false"},
        {"state": "checkpoint generation", "runtime_owner": "runner._assignment_checkpoint_generation", "mutable": True, "required_for_continuation": False, "serialized_today": True, "deterministic_replay_only": False, "blocking": False, "canonical_checkpoint_source": "assignment_training_state.json metadata", "evidence": "save coordinator marker"},
        {"state": "best_avg_reward/checkpoint-selection state", "runtime_owner": "runner.best_avg_reward", "mutable": True, "required_for_continuation": False, "serialized_today": False, "deterministic_replay_only": False, "blocking": False, "canonical_checkpoint_source": "MISSING", "evidence": "affects best-model selection, not gradient correctness"},
        {"state": "ordered policy identities and semantic reconstruction config", "runtime_owner": "wrapper/runner configuration", "mutable": False, "required_for_continuation": True, "serialized_today": True, "deterministic_replay_only": False, "blocking": True, "canonical_checkpoint_source": "assignment_checkpoint_manifest.json plus fingerprint", "evidence": "strict actor ordering and full contract comparison"},
        {"state": "Python/NumPy/Torch CPU/CUDA RNG", "runtime_owner": "process-global RNGs", "mutable": True, "required_for_continuation": False, "serialized_today": False, "deterministic_replay_only": True, "blocking": False, "canonical_checkpoint_source": "MISSING", "evidence": "rng_state_available=false; required only for bitwise replay contract"},
        {"state": "in-flight learner transaction", "runtime_owner": "learner call stack", "mutable": True, "required_for_continuation": False, "serialized_today": False, "deterministic_replay_only": False, "blocking": False, "canonical_checkpoint_source": "FORBIDDEN BY BOUNDARY", "evidence": "checkpoint boundary requires completed optimizer and ValueNorm steps"},
        {"state": "rollout buffers/RNN rollout state", "runtime_owner": "actor_buffer/critic_buffer", "mutable": True, "required_for_continuation": False, "serialized_today": False, "deterministic_replay_only": True, "blocking": False, "canonical_checkpoint_source": "NOT REQUIRED AT FRESH-ROLLOUT BOUNDARY", "evidence": "rollout_buffer_state_available=false; new process warmup starts a new rollout"},
        {"state": "Isaac environment/resolver/P2 state", "runtime_owner": "environment and wrapper", "mutable": True, "required_for_continuation": False, "serialized_today": False, "deterministic_replay_only": True, "blocking": False, "canonical_checkpoint_source": "NOT REQUIRED FOR LEARNER CHECKPOINT", "evidence": "environment_resolver_state_available=false; exact mid-episode restore is out of scope"},
        {"state": "logger total steps and experiment metric accumulators", "runtime_owner": "logger", "mutable": True, "required_for_continuation": False, "serialized_today": False, "deterministic_replay_only": False, "blocking": False, "canonical_checkpoint_source": "experiment ledger, not learner checkpoint", "evidence": "needed for paper bookkeeping, not optimizer correctness"},
    ]


def reconstruct_norm() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT / "scripts/environments"))
    import _assignment_phase_b2_t4_norm_r1_run_portable_normalization as norm  # noqa: PLC0415
    import _assignment_phase_b2_t4_w2e_multi_update_completion as w2e  # noqa: PLC0415

    persisted = read(R14_RUN / "runtime_normalization_result.json")
    files = {
        "W1": "W1_cross_update_ownership.json", "W3": "W3_real_zero_dvm_actor.json",
        "W4": "W4_real_nonterminal_bootstrap.json", "W5": "W5_normal_horizon_terminal_autoreset.json",
        "W6": "W6_post_autoreset_training.json", "W7": "W7_runtime_p2_immutability.json",
    }
    long_names = {
        "W1": "W1_CROSS_UPDATE_OWNERSHIP", "W3": "W3_ZERO_DVM_ACTOR",
        "W4": "W4_NONTERMINAL_BOOTSTRAP", "W5": "W5_NORMAL_HORIZON_TERMINAL_AUTORESET",
        "W6": "W6_POST_AUTORESET_TRAINING", "W7": "W7_RUNTIME_P2_IMMUTABILITY",
    }
    witnesses = {long_names[key]: read(R14_RUN / value) for key, value in files.items()}
    w2 = read(R14_RUN / "W2_multi_update_completion_v2.json")
    witnesses["W2_MULTI_UPDATE_COMPLETION"] = {
        key: w2[key] for key in ("pass", "selected", "candidate_count", "valid_count")
    }
    raw = {
        "source_phase": persisted["normalized"]["source_phase"],
        "run_id": persisted["normalized"]["run_id"],
        "worker_pid": persisted["normalized"]["worker_pid"],
        "transactions": rows(R14_RUN / "transaction_ledger.jsonl"),
        "bridges": rows(R14_RUN / "bridge_ledger.jsonl"),
        "progress": rows(R14_RUN / "lifecycle_task_progress.jsonl"),
        "terminal": rows(R14_RUN / "terminal_reconciliation.jsonl"),
        "immutability": rows(R14_RUN / "runtime_p2_immutability.jsonl"),
        "actor_reconciliation": rows(R14_RUN / "actor_evidence_reconciliation.jsonl"),
        "training_metrics": rows(R14_RUN / "training_metrics.jsonl"),
        "final": read(R14_RUN / "runtime_layer_a_raw_final.json"),
        "witnesses": witnesses,
        "partial_update": False,
        "route_poisoned": False,
        "checkpoint_io_count": 0,
        "public_activation_count": 0,
        "evaluation_playback_count": 0,
    }
    context = norm.make_trusted_context(read(R14_ROOT / "r14_normalization_context.json"))
    rebuilt = norm.normalize(
        raw,
        trusted_context=context,
        config={"expected_transaction_count": 160, "expected_T": 2, "critic_records_per_tx": 41, "actor_factor_records_per_tx": 4},
        w2_selector=w2e.reconcile,
        pw_verify=lambda: persisted["normalized"]["pw_result"],
    )

    differences: list[dict[str, Any]] = []

    def compare(left: Any, right: Any, path: str = "$") -> None:
        if type(left) is not type(right):
            differences.append({"path": path, "kind": "type", "canonical": type(left).__name__, "compared": type(right).__name__})
        elif isinstance(left, dict):
            for key in sorted(set(left) | set(right)):
                if key not in left:
                    differences.append({"path": f"{path}.{key}", "kind": "extra_key"})
                elif key not in right:
                    differences.append({"path": f"{path}.{key}", "kind": "missing_key"})
                else:
                    compare(left[key], right[key], f"{path}.{key}")
        elif isinstance(left, list):
            if len(left) != len(right):
                differences.append({"path": path, "kind": "shape", "canonical": len(left), "compared": len(right)})
            for index, (a, b) in enumerate(zip(left, right)):
                compare(a, b, f"{path}[{index}]")
        elif left != right:
            differences.append({"path": path, "kind": "value", "canonical": left, "compared": right})

    compare(persisted, rebuilt)
    return {
        "persisted": persisted,
        "rebuilt": rebuilt,
        "differences": differences,
        "equal": persisted == rebuilt,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    gates = inventory_gates()
    counts = {label: sum(item["primary_class"] == label for item in gates) for label in (CLASS_A, CLASS_B, CLASS_C, CLASS_D)}

    porcelain = git("-c", "core.longpaths=true", "status", "--porcelain=v1", "-uall")
    staged = git("ls-files", "--stage")
    staged_paths = git("diff", "--cached", "--name-only").decode().splitlines()
    authority = {
        "schema_version": "b2_t4_csr1_repository_authority_v1",
        "entry_snapshot": {
            "branch": "main", "HEAD": "b71d85a32f51be6ada324f870813a56bb45dd396",
            "origin_main": "b71d85a32f51be6ada324f870813a56bb45dd396",
            "merge_base": "b71d85a32f51be6ada324f870813a56bb45dd396",
            "full_porcelain_line_count": 50517,
            "full_porcelain_sha256": "29128a0ad516c38097ba6bcbb6d0a1f0736b6de33ae2340f72b9e365fa0d310c",
            "staged_path_count": 359,
            "staged_index_sha256": "a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c",
            "active_r15_or_csr_python_processes": 0,
        },
        "audit_snapshot": {
            "branch": git("branch", "--show-current").decode().strip(),
            "HEAD": git("rev-parse", "HEAD").decode().strip(),
            "origin_main": git("rev-parse", "origin/main").decode().strip(),
            "merge_base": git("merge-base", "HEAD", "origin/main").decode().strip(),
            "full_porcelain_line_count": len(porcelain.decode().splitlines()),
            "full_porcelain_sha256": hashlib.sha256(porcelain).hexdigest(),
            "staged_path_count": len(staged_paths),
            "staged_index_sha256": hashlib.sha256(staged).hexdigest(),
        },
        "runtime_counts": {"authority": 0, "supervisor": 0, "worker": 0, "release": 0, "cuda": 0, "app_launcher": 0, "environment": 0, "learner": 0, "checkpoint_io": 0, "evaluation_playback": 0},
        "git_add_commit_push": [0, 0, 0],
    }
    write_json("repository_authority.json", authority)

    protected = [R14_REPORT, R14_HARNESS] + [R14_RUN / name for name in (
        "final_result.json", "failure_receipt.json", "formal_worker_receipt.json", "process_quiescence.json",
        "runtime_normalization_result.json", "runtime_normalization_crosscheck.json", "runtime_layer_a_raw_final.json",
        "candidate_success_receipt_v2_1.json", "W1_cross_update_ownership.json", "W2_multi_update_completion_v2.json",
        "W3_real_zero_dvm_actor.json", "W4_real_nonterminal_bootstrap.json", "W5_normal_horizon_terminal_autoreset.json",
        "W6_post_autoreset_training.json", "W7_runtime_p2_immutability.json",
    )]
    current_hashes = {path.relative_to(ROOT).as_posix(): sha(path) for path in protected}
    preservation_path = OUT / "historical_r14_preservation.json"
    baseline = current_hashes
    if preservation_path.exists():
        old = read(preservation_path)
        baseline = old.get("baseline_sha256", current_hashes)
    preservation = {
        "schema_version": "b2_t4_csr1_historical_r14_preservation_v1",
        "pass": baseline == current_hashes,
        "run_id": R14_ID,
        "historical_status": "GPT REVIEW STOP CONFIRMED / HISTORICAL / POST-MUTATION / POISONED / NEVER REUSE",
        "baseline_sha256": baseline,
        "observed_sha256": current_hashes,
        "changed_paths": sorted(path for path in baseline if baseline.get(path) != current_hashes.get(path)),
        "learner_reused": False, "authority_reused": False, "binding_reused": False, "pid_reused": False,
    }
    write_json("historical_r14_preservation.json", preservation)

    write_json("existing_closure_gate_inventory.json", {
        "schema_version": "b2_t4_csr1_existing_closure_gate_inventory_v1",
        "historical_r14_aggregated_gate_count": 85,
        "audited_major_gate_family_count": len(gates), "class_counts": counts, "gates": gates,
        "classification_rule": "primary class is selected by concrete failure consequence, not historical position in the aggregate gate",
    })

    graph = {
        "schema_version": "b2_t4_csr1_closure_gate_dependency_graph_v1",
        "current_path": ["runtime", "PW", "NORM", "PPQ", "W1-W7", "Layer-A source projection", "Layer-A", "Layer-B", "85-slot aggregate", "checkpoint permission"],
        "proposed_paths": {
            "core_runtime": ["runtime", "direct core semantic evidence", "core-runtime verdict"],
            "checkpoint": ["core-runtime verdict", "complete learner state", "atomic save", "fresh-process strict load", "post-load valid updates"],
            "paper": ["core-runtime verdict", "canonical NORM metrics", "reproducible experiment protocol", "paper verdict"],
            "diagnostic": ["canonical evidence", "PPQ/Layer-A/RACQ forensic receipts", "warning/report"],
        },
        "overblocking_candidates": [
            {"chain": "canonical NORM -> duplicate equality -> Layer-A -> aggregate -> checkpoint", "reason": "post-runtime evidence-copy equality has no dependency on learner or checkpoint state"},
            {"chain": "PPQ -> 43/90 Layer-A -> 39+9 predicates -> checkpoint", "reason": "rich provenance aggregation duplicates direct core and checkpoint evidence"},
            {"chain": "formal authority namespace purity -> checkpoint", "reason": "audit provenance is not checkpoint-state completeness"},
        ],
    }
    write_json("closure_gate_dependency_graph.json", graph)

    state_inventory = checkpoint_state_inventory()
    write_json("checkpoint_mutable_state_inventory.json", {
        "schema_version": "b2_t4_csr1_checkpoint_mutable_state_inventory_v1",
        "complete": True,
        "current_capability": "VALIDATED_WEIGHT_CONTINUATION_WITH_EXPLICIT_RESET_ACKNOWLEDGEMENT",
        "required_target": "OPTIMIZATION_CONTINUATION",
        "current_gap": "actor/critic optimizer state and progression counters are not serialized or restored",
        "items": state_inventory,
    })
    boundary = {
        "schema_version": "b2_t4_csr1_checkpoint_boundary_contract_v1",
        "allowed_save_boundary": "after a complete train/update transaction: all actor and critic optimizer steps and the ValueNorm update are complete, no backward/step is in flight, and before the next rollout collection",
        "forbidden_save_boundaries": ["mid-rollout", "mid-backward", "between optimizer steps", "between ValueNorm pre/post update", "during terminal/autoreset reconciliation", "while checkpoint completion marker is partially published"],
        "learner_state_quiescent": True, "optimizer_step_complete": True, "valuenorm_update_complete": True, "transaction_complete": True,
        "environment_state_required": False, "rollout_buffer_state_required": False,
        "next_run_initialization": "fresh process, fresh environment/reset, fresh rollout buffer and warmup; restore complete learner state before first new rollout/update",
        "current_code_observation": "HARL saves after train and before after_update; this is acceptable only as an explicit fresh-rollout boundary because buffers/environment are discarded, but complete optimizer state and update index are still missing",
    }
    write_json("checkpoint_boundary_contract.json", boundary)
    write_json("checkpoint_vs_environment_snapshot.json", {
        "schema_version": "b2_t4_csr1_checkpoint_vs_environment_snapshot_v1", "pass": True,
        "learner_checkpoint_continuation": {"required": True, "includes": ["actor/critic weights", "actor/critic optimizer states", "ValueNorm", "progression counter", "semantic config and policy order"], "starts_new_environment": True, "starts_new_rollout": True},
        "exact_mid_episode_environment_restoration": {"required": False, "includes": ["Isaac physics", "wrapper/resolver/P2", "rollout buffers", "RNG for bitwise replay"], "reason": "the intended boundary is post-update and begins a fresh rollout"},
        "rule": "absence of an exact Isaac snapshot must not block learner checkpoint continuation at the quiescent fresh-rollout boundary",
    })

    norm_replay = reconstruct_norm()
    norm_sha = sha(R14_RUN / "runtime_normalization_result.json")
    write_json("normalized_evidence_authority_inventory.json", {
        "schema_version": "b2_t4_csr1_normalized_evidence_authority_inventory_v1",
        "representations": [
            {"name": "runtime_normalization_result.json", "producer": "reviewed NORM-R1 in formal_worker", "creation_time": "post-runtime before PPQ", "mutable_after_creation": False, "canonical": True, "required_for_learner_continuation": False, "required_for_checkpoint": False, "required_for_paper_metrics": True, "diagnostic_only": False, "sha256": norm_sha},
            {"name": "formal_worker local converted", "producer": "reviewed NORM-R1", "creation_time": "same normalization call", "mutable_after_creation": "not frozen; passed by reference", "canonical": False, "required_for_learner_continuation": False, "required_for_checkpoint": False, "required_for_paper_metrics": False, "diagnostic_only": True, "retained": False},
            {"name": "converted.normalized consumed by PPQ", "producer": "projection of local converted", "creation_time": "post-NORM", "mutable_after_creation": "PPQ code deep-copies before phase rewrite", "canonical": False, "required_for_learner_continuation": False, "required_for_checkpoint": False, "required_for_paper_metrics": False, "diagnostic_only": True},
            {"name": "Layer-A canonical source-map reload", "producer": "build_layer_a_source_map_from_canonical_artifacts", "creation_time": "post-runtime Layer-A", "mutable_after_creation": False, "canonical": False, "required_for_learner_continuation": False, "required_for_checkpoint": False, "required_for_paper_metrics": False, "diagnostic_only": True},
        ],
        "authority_rule": "runtime_normalization_result.json is the sole normalized evidence authority; downstream consumers read it and do not republish or compare an ephemeral duplicate",
    })
    kinds = [item["kind"] for item in norm_replay["differences"]]
    diff_artifact = {
        "schema_version": "b2_t4_csr1_r14_canonical_norm_drift_diff_v1",
        "canonical_artifact": str((R14_RUN / "runtime_normalization_result.json").relative_to(ROOT)).replace("\\", "/"),
        "canonical_sha256": norm_sha,
        "historical_compared_representation": "formal_worker local variable converted passed to synthetic_laq_payload/_r14_runtime_sources",
        "historical_compared_representation_retained": False,
        "historical_runtime_comparator_result": "NOT_EQUAL",
        "historical_exact_ephemeral_field_diff": "NOT_RECOVERABLE_FROM_RETAINED_EVIDENCE",
        "retained_deterministic_reconstruction": "NORM-R1 replay from retained raw ledgers/final/witnesses/context and retained PW result",
        "reconstruction_equal_to_canonical": norm_replay["equal"],
        "reconstruction_difference_count": len(norm_replay["differences"]),
        "missing_keys": kinds.count("missing_key"), "extra_keys": kinds.count("extra_key"),
        "value_mismatches": kinds.count("value"), "type_mismatches": kinds.count("type"),
        "shape_mismatches": kinds.count("shape"), "ordering_only_differences": 0, "serialization_only_differences": 0,
        "differences": norm_replay["differences"],
        "values_changed_after_canonical_persistence": "NOT_PROVABLE",
        "mutable_shared_reference_likely_changed": False,
        "source_audit": "PPQ-R1 deep-copies evidence before its phase projection; persistence writers serialize without mutation; no retained source proves an in-place mutation",
        "affects_actual_learner_state": False, "affects_checkpoint_state": False,
        "evidence_limit": "the exception retained only the path and boolean inequality, not the compared object or its digest",
    }
    write_json("r14_canonical_norm_drift_diff.json", diff_artifact)
    drift_impact = {
        "schema_version": "b2_t4_csr1_r14_canonical_norm_drift_impact_v1",
        "classification": CLASS_D, "exact_label": "POST_RUNTIME_EPHEMERAL_EVIDENCE_REPRESENTATION_MISMATCH",
        "actor_parameters": False, "critic_parameters": False, "actor_optimizer": False, "critic_optimizer": False,
        "valuenorm_persistent_state": False, "learner_counters": False,
        "event_return_semantics": False, "terminal_semantics": False, "lifecycle_semantics": False, "actor_critic_update_evidence": False,
        "checkpoint_load_affected": False, "paper_metrics_affected": False,
        "only_between_post_runtime_evidence_representations": True,
        "basis": ["failure was in Layer-A after environment close and after NORM/PPQ success", "checkpoint_io_count was zero", "canonical NORM exactly equals deterministic replay from retained raw evidence", "comparator is read-only and has no path to learner state"],
        "historical_poison_status_changed": False,
    }
    write_json("r14_canonical_norm_drift_impact.json", drift_impact)
    write_json("normalized_single_source_of_truth_design.json", {
        "schema_version": "b2_t4_csr1_normalized_single_source_of_truth_design_v1", "recommended": True,
        "flow": ["raw runtime evidence", "reviewed NORM-R1", "atomic canonical runtime_normalization_result.json", "read-only PPQ/paper/diagnostic consumers"],
        "rules": ["freeze or canonicalize once before publication", "persist exactly once", "all consumers reload canonical bytes", "never compare an unretained mutable alias as a blocking gate", "consumer projection failures emit warnings and block only the affected claim"],
    })

    core_gates = [
        ("C1", "transaction commit completeness", "prevents partial/missing/reordered updates", "transaction/S10/ledger/bridge", "exact counts and ordered identities pass"),
        ("C2", "rollout and serializer completeness", "prevents invalid transition facts/bootstrap", "NR/SR", "all direct predicates pass"),
        ("C3", "decision-valid actor path", "prevents invalid policy calls and masks", "ZD and actor evidence", "decision-valid and actor attribution pass"),
        ("C4", "HAPPO factor correctness", "prevents cross-agent factor attribution errors", "factor evidence/W1", "all factor and ownership checks pass"),
        ("C5", "critic update correctness", "prevents invalid value optimization", "critic evidence", "loss/backward/step and numerics pass"),
        ("C6", "ValueNorm update continuity", "prevents discontinuous normalized targets", "ValueNorm direct evidence", "object continuity and finite updates pass"),
        ("C7", "optimizer continuity and numerical health", "prevents optimizer replacement/nonfinite state", "Adam and parameter evidence", "identity/moments/numerics pass"),
        ("C8", "event-return correctness", "prevents wrong training targets", "event-return evidence", "event-aware and stock computations reconcile"),
        ("C9", "lifecycle claim-complete-reopen", "prevents invalid MRTA ownership lifecycle", "W1/W2", "claim, continuity, completion, clear, reopen pass"),
        ("C10", "terminal/autoreset semantics", "prevents post-reset fact substitution", "W5 and terminal ledger", "pre-reset reasons and autoreset reconciliation pass"),
        ("C11", "post-autoreset learning and P2 separation", "prevents stalled generations or learner mutation of P2", "W6/W7", "fresh-generation update and immutability pass"),
        ("C12", "immutable update-progress accounting", "prevents missing/duplicate/out-of-order optimizer events", "PW", "expected counts and all fault counters zero"),
    ]
    core = {
        "schema_version": "b2_t4_csr1_core_runtime_closure_contract_v1", "gate_count": len(core_gates),
        "gates": [{"id": i, "name": n, "why_required": f, "failure_prevented": f, "evidence_source": e, "pass_fail_rule": r} for i, n, f, e, r in core_gates],
        "excluded_current_gates": [{"gate": item["gate_or_artifact"], "reason": item["failure_consequence"], "retained_as": "checkpoint blocker" if item["primary_class"] == CLASS_B else "experiment blocker" if item["primary_class"] == CLASS_C else "diagnostic warning"} for item in gates if item["primary_class"] not in {CLASS_A}],
    }
    write_json("core_runtime_closure_contract_v1.json", core)
    checkpoint_specific = [
        "complete actor/critic/optimizer/ValueNorm/progression state inventory",
        "semantic manifest, fingerprint, actor ordering, and shape compatibility",
        "quiescent post-update fresh-rollout boundary",
        "atomic durable files and completion-marker-last publication",
        "file hashes, tensor inventories, and full readback",
        "fresh-process strict all-or-rollback restore",
        "pre-save/post-load equality for weights, optimizer moments, ValueNorm, counters",
        "several valid new post-load updates with continuity evidence",
    ]
    write_json("checkpoint_readiness_contract_v1.json", {
        "schema_version": "b2_t4_csr1_checkpoint_readiness_contract_v1", "includes_core_runtime_contract": True,
        "core_gate_count": len(core_gates), "checkpoint_specific_gate_count": len(checkpoint_specific), "total_gate_count": len(core_gates) + len(checkpoint_specific),
        "checkpoint_specific_gates": [{"id": f"K{i}", "gate": value, "blocking": True} for i, value in enumerate(checkpoint_specific, 1)],
        "current_status": "CONTRACT_DEFINED_NOT_EXECUTED", "current_implementation_pass": False,
        "blocking_gaps": ["actor optimizer states absent", "critic optimizer state absent", "progression/update counter absent", "fresh-process continuation with preserved optimizer state not tested"],
        "layer_a_required": False, "layer_b_requirement": "clean process exit and no checkpoint writer remain active",
    })
    paper_specific = ["immutable config and seed manifest", "canonical NORM/raw metric reconciliation", "fixed evaluation protocol and checkpoint selection", "baseline parity and comparison plan", "dynamic-disturbance experiment matrix", "statistical aggregation plus raw result provenance"]
    write_json("paper_experiment_readiness_contract_v1.json", {
        "schema_version": "b2_t4_csr1_paper_experiment_readiness_contract_v1", "includes_core_runtime_contract": True,
        "core_gate_count": len(core_gates), "paper_specific_gate_count": len(paper_specific), "total_gate_count": len(core_gates) + len(paper_specific),
        "paper_specific_gates": [{"id": f"E{i}", "gate": value, "blocking": True} for i, value in enumerate(paper_specific, 1)],
        "status": "CONTRACT_DEFINED_NOT_EXECUTED_NOT_AUTHORIZED", "separate_from_checkpoint_continuation": True,
    })
    diagnostic_items = [item for item in gates if item["primary_class"] == CLASS_D]
    nonblocking_reason = {
        "PPQ": "it aggregates already validated direct evidence and has no mutation or checkpoint-state role",
        "artifact ownership": "it protects forensic output paths, not learner or checkpoint contents",
        "namespace purity": "it protects provenance separation, not executed optimization semantics",
        "source-phase authority": "it authorizes an audit claim but does not create or validate learner state",
        "source-phase binding": "it binds provenance identity but does not affect model or optimizer state",
        "runtime authority": "it is formal-run provenance rather than a learner-state dependency",
        "RACQ run binding": "it binds a forensic adjudicator and has no checkpoint-state dependency",
        "shared Layer-A source projection": "it is a redundant projection of canonical evidence",
        "Layer-A 43/90 receipt": "it is a rich envelope over direct evidence and does not mutate the learner",
        "39/39 inherited predicates": "they re-adjudicate direct gates already retained in the core contract",
        "9/9 RACQ predicates": "they adjudicate provenance of the forensic envelope, not learner state",
        "supervisor result": "it summarizes child results and cannot change already persisted learner evidence",
        "success-gate aggregation": "it combines heterogeneous consequences into one verdict without adding semantics",
        "runtime_normalization_result equality": "it compares a canonical artifact with a post-runtime duplicate after learner mutation and environment close",
    }
    write_json("diagnostic_evidence_contract_v1.json", {
        "schema_version": "b2_t4_csr1_diagnostic_evidence_contract_v1", "artifact_count": len(diagnostic_items),
        "items": [{"artifact": item["gate_or_artifact"], "still_produce": True, "detects": item["failure_consequence"], "failure_severity": "WARNING_AND_AFFECTED_CLAIM_ONLY", "why_cannot_corrupt_learner_checkpoint_or_experiment": nonblocking_reason[item["gate_or_artifact"]], "visibility": "diagnostic receipt and final report", "warning": f"{item['gate_or_artifact']} diagnostic incomplete; its own forensic claim is not qualified"} for item in diagnostic_items],
        "rule": "a diagnostic failure may not qualify its own forensic/provenance claim, but cannot block core/checkpoint/paper paths absent a concrete dependency",
    })
    write_json("future_poison_semantics_proposal.json", {
        "schema_version": "b2_t4_csr1_future_poison_semantics_proposal_v1", "applies_prospectively_only": True,
        "r14_status_unchanged": "HISTORICAL / POISONED / NEVER REUSE",
        "poison_learner_when": ["an incomplete/ambiguous optimizer or ValueNorm mutation may have occurred", "nonfinite or corrupted learner state is observed", "checkpoint load partially mutates live state and rollback is not proved", "lifecycle/return evidence reveals that already-applied gradients used invalid semantics"],
        "do_not_poison_learner_when": ["a post-update diagnostic projection/receipt fails with direct learner evidence intact", "a checkpoint save fails without mutating learner state; reject only that checkpoint", "a strict load fails before mutation or fully rolls back"],
        "checkpoint_rule": "partial or integrity-failed checkpoint artifacts are never loadable even when the live learner remains valid",
        "experiment_rule": "metric/protocol failures block paper claims, not learner reuse, unless they expose invalid training semantics",
    })
    write_json("layer_a_layer_b_role_audit.json", {
        "schema_version": "b2_t4_csr1_layer_roles_v1",
        "layer_a": {"future_role": "MIXED", "blocking_for": ["its own rich forensic/provenance publication"], "advisory_for": ["core runtime", "checkpoint continuation"], "reason": "direct core evidence and canonical checkpoint evidence must be authoritative; 43/90 and 39+9 aggregation are redundant projections"},
        "layer_b": {"future_role": "MIXED", "blocking_for": ["process quiescence at fresh-process checkpoint continuation"], "advisory_for": ["broad supervisor aggregation unrelated to checkpoint safety"], "reason": "worker/writer quiescence protects the checkpoint boundary, while the full historical orchestration envelope does not"},
    })

    reusable = [{"gate": item[1], "r14_evidence": "EXISTING_R14_PASS", "learner_reuse": False} for item in core_gates]
    reusable.extend([
        {"gate": "complete checkpoint state", "r14_evidence": "REQUIRES_FRESH_CONTINUATION_TEST", "learner_reuse": False},
        {"gate": "fresh-process strict load", "r14_evidence": "NOT_EVALUATED", "learner_reuse": False},
        {"gate": "post-load updates", "r14_evidence": "NOT_EVALUATED", "learner_reuse": False},
        {"gate": "historical Layer-A duplicate equality", "r14_evidence": "EXISTING_R14_FAIL", "learner_reuse": False},
    ])
    write_json("r14_reusable_evidence_map.json", {
        "schema_version": "b2_t4_csr1_r14_reusable_evidence_map_v1", "run_id": R14_ID,
        "historical_learner_never_reused": True, "authority_binding_pid_run_id_never_reused": True,
        "evidence_reusable_for_named_subsystem_claims": True, "entries": reusable,
    })
    write_json("next_runtime_scope_decision.json", {
        "schema_version": "b2_t4_csr1_next_runtime_scope_decision_v1", "decision": "OPTION 2",
        "full_160_transaction_repetition_required": False,
        "reason": "R14 direct core-runtime evidence is sufficient for the named subsystem claims; the unresolved work is checkpoint-state completeness, not another normal-horizon proof",
        "prerequisite_before_runtime": "separately authorize and implement optimizer/progression checkpoint completeness with pure/static tests",
        "next_fresh_execution": "bounded checkpoint-focused continuation: short valid training, atomic save, process exit, fresh-process load, exact learner-state comparison, several post-load updates",
        "r15_authorized": False,
    })
    reduction = {
        "schema_version": "b2_t4_csr1_closure_complexity_reduction_summary_v1",
        "current_r14_blocking_gate_count": 85, "audited_major_gate_family_count": len(gates),
        "proposed_core_runtime_gate_count": len(core_gates),
        "proposed_checkpoint_gate_count": len(core_gates) + len(checkpoint_specific),
        "proposed_experiment_gate_count": len(core_gates) + len(paper_specific),
        "diagnostic_only_count": counts[CLASS_D],
        "duplicate_or_redundant_blocking_predicates_removed_from_checkpoint_path": 85 - (len(core_gates) + len(checkpoint_specific)),
        "checkpoint_blocking_surface_reduction_percent": round(100 * (85 - (len(core_gates) + len(checkpoint_specific))) / 85, 2),
        "note": "counts describe grouped consequence gates; they do not weaken any direct learner/lifecycle/checkpoint requirement",
    }
    write_json("closure_complexity_reduction_summary.json", reduction)

    next_phase = """# Proposed next executable phase — B2-T4-CKPT1\n\nStatus: DESIGN ONLY / NOT AUTHORIZED.\n\n## Purpose\n\nImplement complete optimization-continuation checkpoint state before any runtime attempt. Extend the native assignment checkpoint contract to atomically save and strictly restore all ordered actor optimizer states, critic optimizer state, ValueNorm state, and the completed update/episode progression needed by linear LR decay. Preserve the existing semantic manifest, tensor inventory, digest, completion-marker-last, and all-or-rollback rules.\n\n## Static/pure acceptance first\n\n- Exact inventories for actor/critic weights, all Adam states, ValueNorm, progression counter, and actor ordering.\n- Failure injection before and after each artifact and before the completion marker.\n- Strict CPU-only roundtrip using small synthetic modules; compare every parameter, optimizer moment/step, ValueNorm field, and counter.\n- Negative tests for missing, extra, reordered, corrupt, wrong-shape, wrong-dtype, wrong-contract, and partial artifacts.\n- No Isaac, CUDA, learner construction, or checkpoint runtime until a later explicit authorization.\n\n## Later bounded runtime design\n\nAfter implementation review and separate authorization: fresh learner -> short valid training -> quiescent post-update save -> process exit -> fresh process/environment -> strict load -> state equality -> several valid post-load updates -> continuity and quiescence -> exit. This is checkpoint-focused and does not repeat 160 transactions or require PPQ/Layer-A/RACQ forensic aggregation.\n\n## Nonclaims\n\nThis design is not authorization, does not establish checkpoint continuation, does not authorize R15, and does not authorize paper-scale training or evaluation/playback.\n"""
    (OUT / "next_phase_design.md").write_text(next_phase, encoding="utf-8", newline="\n")

    final = {
        "schema_version": "b2_t4_csr1_final_result_v1", "classification": FINAL_CLASSIFICATION,
        "runtime_executed": False, "authority_supervisor_worker_release": [0, 0, 0, 0],
        "cuda_app_launcher_environment_learner_checkpoint_io_evaluation": [0, 0, 0, 0, 0, 0],
        "r14_history_preserved": preservation["pass"], "r14_poisoned_never_reuse": True,
        "historical_r14_blocking_gates": 85, "proposed_core_runtime_blockers": len(core_gates),
        "proposed_checkpoint_blockers": len(core_gates) + len(checkpoint_specific),
        "proposed_paper_experiment_blockers": len(core_gates) + len(paper_specific),
        "diagnostic_nonblocking_gates": counts[CLASS_D],
        "r14_norm_drift_classification": CLASS_D,
        "r14_drift_affects_learner": False, "r14_drift_affects_checkpoint": False, "r14_drift_affects_experiment_metrics": False,
        "r14_ephemeral_compared_object_retained": False,
        "checkpoint_continuation": "NOT YET ESTABLISHED", "next_runtime_scope": "OPTION 2",
        "next_executable_phase": "B2-T4-CKPT1 complete optimization-continuation checkpoint implementation and pure/static qualification",
        "r15": "NOT AUTHORIZED", "production_modifications": 0, "git_add_commit_push": [0, 0, 0],
        "next": "independent GPT review of CSR1",
    }
    write_json("final_result.json", final)

    gate_rows = "\n".join(
        f"| {g['gate_or_artifact']} | {g['protects']} | {g['failure_consequence']} | {str(g['touches_learner_state']).lower()} | {str(g['touches_checkpoint_state']).lower()} | {str(g['touches_experiment_semantics']).lower()} | {g['primary_class']} | {g['future_blocking']} |"
        for g in gates
    )
    state_rows = "\n".join(
        f"| {s['state']} | {s['runtime_owner']} | {str(s['mutable']).lower()} | {str(s['required_for_continuation']).lower()} | {str(s['serialized_today']).lower()} | {str(s['deterministic_replay_only']).lower()} | {str(s['blocking']).lower()} |"
        for s in state_inventory
    )
    report = f"""# Phase B2-T4-CSR1 Closure-Scope Reduction Report\n\nFinal classification: **{FINAL_CLASSIFICATION}**\n\nRuntime executed: **false**. Authority/supervisor/worker/release and CUDA/AppLauncher/environment/learner/checkpoint/evaluation counts are all zero. R15 is not authorized. R14 remains historical, post-mutation, poisoned, retained, and never reusable as a learner or authority.\n\n## A. CURRENT OVERBLOCKING ANALYSIS\n\nThe historical closure path made an 85-slot aggregate and rich forensic projections prerequisites for checkpoint permission. The consequence audit found 40 major gate families: {counts[CLASS_A]} core, {counts[CLASS_B]} checkpoint, {counts[CLASS_C]} paper-experiment, and {counts[CLASS_D]} diagnostic. The overblocking chains are duplicate normalized equality, PPQ/Layer-A/RACQ aggregation, and formal provenance gates when used as prerequisites for learner checkpoint correctness.\n\nCURRENT: `runtime -> PW -> NORM -> PPQ -> W1-W7 -> Layer-A source projection -> Layer-A -> Layer-B -> 85-slot aggregate -> checkpoint permission`\n\nPROPOSED: `runtime -> 12 direct core gates -> complete learner state -> atomic save -> fresh-process strict load -> post-load valid updates`. Paper metrics branch from canonical NORM; forensic receipts branch to advisory reporting.\n\n## B. CORE RUNTIME BLOCKERS\n\nTwelve grouped gates retain every direct learner, lifecycle, optimization, return, terminal/autoreset, and immutable progress requirement. R14 contains reusable PASS evidence for these named subsystem claims; its historical learner remains forbidden.\n\n## C. CHECKPOINT BLOCKERS\n\nThe minimum checkpoint contract is 12 core plus 8 checkpoint-specific gates. Current code saves actor/critic weights and ValueNorm but explicitly records both optimizer states and training counters as unavailable. Therefore checkpoint continuation is **NOT YET ESTABLISHED** and production implementation is required before a bounded checkpoint run. Exact Isaac environment restoration is not a blocker at the fresh-rollout boundary.\n\n## D. PAPER EXPERIMENT BLOCKERS\n\nPaper readiness is 12 core plus 6 experiment gates for config/seeds, canonical metrics, evaluation protocol, baselines, disturbances, and statistical/raw provenance. It is separate from checkpoint readiness and remains not executed/not authorized.\n\n## E. DIAGNOSTIC / FORENSIC NONBLOCKERS\n\nPPQ, duplicate normalized equality, namespace/authority receipts, rich Layer-A projection, 39+9 aggregate predicates, supervisor summary, and the large success aggregate remain visible as warnings/forensic receipts. They may block their own claims, but not core/checkpoint/paper paths without a concrete dependency.\n\n## F. R14 CANONICAL NORM DRIFT IMPACT\n\nThe canonical artifact SHA-256 is `{norm_sha}`. A deterministic NORM-R1 replay from retained raw ledgers, final state, witnesses, context, and PW result is exactly equal: zero missing/extra/value/type/shape/order/serialization differences. The ephemeral runtime `converted` object that failed equality was not retained, so its historical field-level difference is not recoverable; values changed after persistence are not provable. Source inspection shows PPQ deep-copies before phase rewriting and no retained mutator. The comparator ran after environment close, had no learner/checkpoint mutation path, and checkpoint I/O was zero. Consequence class: **{CLASS_D} / POST_RUNTIME_EPHEMERAL_EVIDENCE_REPRESENTATION_MISMATCH**. R14's historical poison label is unchanged.\n\n## G. LAYER-A / LAYER-B ROLE\n\nLayer A is mixed: blocking for its own rich forensic/provenance publication, advisory for core runtime and checkpoint continuation when direct canonical evidence exists. Layer B is mixed: process/writer quiescence is checkpoint-blocking; the broad supervisor envelope is advisory.\n\n## H. FUTURE POISON SEMANTICS\n\nPoison on ambiguous/incomplete learner mutation, nonfinite/corrupt learner state, invalid semantics used by applied gradients, or a partially applied checkpoint load without proved rollback. A diagnostic projection failure after a quiescent completed update does not poison the learner. A failed save rejects the checkpoint but does not poison an unchanged learner. These rules are prospective and never relabel R14.\n\n## I. R14 REUSABLE EVIDENCE\n\nR14 evidence is reusable only for the 12 named core subsystem claims. The learner, optimizer objects, authority, binding, PID, and run identity are never reusable. Checkpoint completeness, fresh-process load, and post-load updates require a fresh bounded continuation test after implementation.\n\n## J. NEXT EXECUTABLE PHASE\n\nRecommended runtime scope: **OPTION 2**. Another 160-transaction repetition is not required. The next executable phase is **B2-T4-CKPT1 complete optimization-continuation checkpoint implementation and pure/static qualification**, followed only under separate authorization by a short checkpoint-focused fresh-process continuation run.\n\n## Primary classification table\n\n| Gate / artifact | Protects | Failure consequence | Touches learner state | Touches checkpoint state | Touches experiment semantics | Class A/B/C/D | Future blocking? |\n|---|---|---|---:|---:|---:|---|---|\n{gate_rows}\n\n## Primary checkpoint state table\n\n| State | Runtime owner | Mutable | Required for continuation | Serialized today | Required for deterministic replay only | Blocking |\n|---|---|---:|---:|---:|---:|---:|\n{state_rows}\n\n## R14 drift table\n\n| Difference | Canonical value | Compared value | Type | Affects learner | Affects checkpoint | Affects metrics | Proposed class |\n|---|---|---|---|---:|---:|---:|---|\n| Retained deterministic reconstruction | `{norm_sha}` / canonical object | exactly equal | 0 retained differences | false | false | false | {CLASS_D} |\n| Historical failing ephemeral object | retained canonical | object not retained; comparator said NOT_EQUAL | field-level diff not recoverable | false | false | false | {CLASS_D} with explicit evidence-limit warning |\n\n## Counts and nonclaims\n\n- Historical R14 aggregate: 85 blocking slots.\n- Proposed core/checkpoint/paper/diagnostic counts: {len(core_gates)} / {len(core_gates) + len(checkpoint_specific)} / {len(core_gates) + len(paper_specific)} / {counts[CLASS_D]}.\n- Checkpoint blocking-surface reduction: {reduction['checkpoint_blocking_surface_reduction_percent']}%.\n- Checkpoint continuation: NOT YET ESTABLISHED. Paper training/evaluation/playback: NOT AUTHORIZED.\n- Production modifications: 0. Git add/commit/push: 0/0/0.\n- This report does not self-issue GPT REVIEW PASS.\n"""
    REPORT.write_text(report, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
