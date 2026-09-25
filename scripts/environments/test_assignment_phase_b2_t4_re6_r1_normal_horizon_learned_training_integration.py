"""Fresh RE6-R1 qualification: RE5 gates with reviewed W2E as sole W2 authority.

The frozen RE5 harness is source-derived into a distinct artifact namespace.  The
only witness-route change is replacement of the old textual-claim W2 result by
the reviewed W2E reconciler.  Historical RE5 files are never written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from _assignment_phase_b2_t4_w2e_multi_update_completion import reconcile
import test_assignment_phase_b2_t4_w2e_claim_evidence_contract as W2E_RUNNER


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
DATE_ROOT = SCAN / "AgentRead/202609/20260920"
ARTIFACTS = DATE_ROOT / "b2_t4_re6_r1_artifacts"
PREFIX = ARTIFACTS / "b2_t4_re6_r1_normal_horizon_20260920_formal01"
RE5_SOURCE = HERE / "test_assignment_phase_b2_t4_re5_normal_horizon_learned_training_integration.py"
SELECTOR = HERE / "_assignment_phase_b2_t4_w2e_multi_update_completion.py"
W2I_BINDING = DATE_ROOT / "b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json"
W2E_CONTRACT = DATE_ROOT / "b2_t4_w2e_artifacts/w2e_contract_v2.json"
RE5_ARTIFACTS = SCAN / "AgentRead/202609/20260916/b2_t4_re5_artifacts"
RE5_PREFIX = "b2_t4_re5_normal_horizon_20260916_formal01"
EXPECTED = {
    "re5_harness": (RE5_SOURCE, "4ae8e721e4dfbb42f53dd49bf91c002b502f7f2cf29757e2cf756bbe067ca2d8"),
    "w2e_selector": (SELECTOR, "8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0"),
    "w2e_runner": (HERE / "test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py", "08758de24b78c9c63b97a94481f37e8a52608171fd1b6d8d048252689ea8cd58"),
    "w2e_contract": (W2E_CONTRACT, "81440619e14b59b22eaca8d3928e2fd37f9ea1b39818c9f92a918a845a207c3b"),
    "w2i_binding": (W2I_BINDING, "3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b"),
}
PASS = "PHASE-B2-T4-RE6-R1-W2I-BOUND-NORMAL-HORIZON-LEARNED-TRAINING-INTEGRATION-QUALIFIED-AWAITING-GPT-REVIEW"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok: bool, code: str, detail: object = None) -> None:
    if not ok:
        raise RuntimeError(f"STOP — PHASE-B2-T4-RE6-R1-STOP-{code}: {detail!r}")


def identities() -> dict[str, object]:
    observed = {name: {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size,
                       "expected_sha256": expected} for name, (path, expected) in EXPECTED.items()}
    require(observed["w2e_selector"]["bytes"] == 15089, "W2E-REVIEWED-IDENTITY-MISMATCH", observed["w2e_selector"])
    require(all(row["sha256"] == row["expected_sha256"] for row in observed.values()),
            "W2E-REVIEWED-IDENTITY-MISMATCH", observed)
    return {"schema_version": "b2_t4_re6_r1_reviewed_identity_v1", "sources": observed, "pass": True}


def replace_once(source: str, old: str, new: str) -> str:
    require(source.count(old) == 1, "QUALIFIED-SOURCE-DRIFT", {"fragment": old, "count": source.count(old)})
    return source.replace(old, new)


def derive_re5() -> tuple[str, dict[str, object]]:
    identities()
    source = RE5_SOURCE.read_text(encoding="utf-8")
    replacements = {
        'ARTIFACTS = DATE_ROOT / "b2_t4_re5_artifacts"':
            'ARTIFACTS = SCAN / "AgentRead" / "202609" / "20260920" / "b2_t4_re6_r1_artifacts"',
        'PREFIX = ARTIFACTS / "b2_t4_re5_normal_horizon_20260916_formal01"':
            'PREFIX = ARTIFACTS / "b2_t4_re6_r1_normal_horizon_20260920_formal01"',
    }
    for old, new in replacements.items():
        source = replace_once(source, old, new)
    artifact_names = (
        "re5_static_authority.json", "re5_runner_readiness_replay.json",
        "re5_preflight_summary.json", "re5_progress_persistence_binding.json",
        "re5_process_config_authority.json", "re5_cuda_cublas_readiness.json",
        "re5_worker_raw_result.json",
    )
    for old in artifact_names:
        source = source.replace(f'"{old}"', f'"{old.replace("re5_", "re6_r1_", 1)}"')
    source = source.replace('"re5_runner"', '"re6_r1_runner"')
    source = source.replace('"B2-T4-RE5"', '"B2-T4-RE6-R1"')
    source = source.replace('PHASE-B2-T4-RE5-', 'PHASE-B2-T4-RE6-R1-')
    source = source.replace('b2-t4-re5-', 'b2-t4-re6-r1-')
    source = re.sub(r'b2_t4_re5_([a-z_]+_v1)', r'b2_t4_re6_r1_\1', source)
    source = source.replace('"b2_t4_re5_20260916_formal01"', '"b2_t4_re6_r1_20260920_formal01"')
    receipt = {"schema_version": "b2_t4_re6_r1_source_derivation_v1",
               "re5_source_sha256": sha(RE5_SOURCE),
               "transformed_source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
               "artifact_namespace": str(ARTIFACTS),
               "witness_route_change": "old W2 diagnostic only; reviewed W2E reconcile sole W2 authority",
               "other_re5_gates": "source-identical except phase, artifact namespace, and schema labels"}
    return source, receipt


_SOURCE, DERIVATION = derive_re5()
_ENGINE: dict[str, object] = {"__name__": "_b2_t4_re6_r1_derived_harness", "__file__": str(Path(__file__).resolve()), "__package__": None}
exec(compile(_SOURCE, str(Path(__file__).resolve()), "exec"), _ENGINE)
_ENGINE["PASS"] = PASS
RE3 = _ENGINE["RE3"]
_OLD_FIND = RE3._find_witnesses
_LEDGERS = (
    "transaction", "bridge", "lifecycle_task_progress", "terminal_reconciliation",
    "nonterminal_bootstrap", "zero_dvm_actor", "learner_runtime_immutability",
    "actor_evidence_reconciliation",
)


def _rows(prefix: Path, name: str) -> list[dict]:
    path = prefix.parent / f"{prefix.name}_{name}_ledger.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _w2e_witness(prefix: Path) -> dict[str, object]:
    normalized = W2E_RUNNER.normalize(
        _rows(prefix, "lifecycle_task_progress"), _rows(prefix, "transaction"), _rows(prefix, "bridge"))
    result = reconcile(normalized)
    _ENGINE["_durable_json"](prefix.parent / "w2e_v2_reconciliation.json", result)
    selected = result.get("selected") or {}
    return {"pass": result["pass"], "contract_version": result["schema_version"],
            "selected": selected, "candidate_count": result["candidate_count"],
            "valid_count": result["valid_count"],
            "claim_tx_lt_completion_tx": bool(selected and selected["claim_tx"] < selected["completion_tx"]),
            "transaction_index": selected.get("claim_tx"),
            "completion": {"transaction_index": selected["completion_tx"]} if selected else None}


def _find_witnesses(prefix: Path) -> dict[str, object]:
    witnesses = dict(_OLD_FIND(prefix))
    old = witnesses.get("W2_MULTI_UPDATE_COMPLETION")
    _ENGINE["_durable_json"](prefix.parent / "legacy_w2_diagnostic.json",
        {"schema_version": "b2_t4_re6_r1_legacy_w2_diagnostic_v1",
         "authoritative_for_RE6_R1": False, "old_w2": old})
    witnesses["W2_MULTI_UPDATE_COMPLETION"] = _w2e_witness(prefix)
    required = ("W1_CROSS_UPDATE_OWNERSHIP", "W2_MULTI_UPDATE_COMPLETION",
                "W3_ZERO_DVM_ACTOR", "W4_NONTERMINAL_BOOTSTRAP",
                "W5_NORMAL_HORIZON_TERMINAL_AUTORESET", "W6_POST_AUTORESET_TRAINING",
                "W7_RUNTIME_P2_IMMUTABILITY", "ACTOR_EVIDENCE_RECONCILIATION")
    counts = witnesses["ledger_counts"]
    witnesses["pass"] = bool(
        all(isinstance(witnesses.get(key), dict) and witnesses[key].get("pass") is True for key in required)
        and witnesses["task_progress_gate"]["pass"]
        and counts["transactions"] == 160 and counts["bridges"] == 159)
    return witnesses


# The inherited RE1 postprocessor resolves this name in the derived RE3
# namespace.  The old selector still runs inside _OLD_FIND, but its result is
# overwritten before the mandatory gate and persisted only as a diagnostic.
RE3._RE3["_find_witnesses"] = _find_witnesses


def historical_route_replay() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="b2_t4_re6_r1_w2_replay_") as name:
        prefix = Path(name) / "historical_re5_copy"
        for ledger in _LEDGERS:
            source = RE5_ARTIFACTS / f"{RE5_PREFIX}_{ledger}_ledger.jsonl"
            shutil.copyfile(source, prefix.parent / f"{prefix.name}_{ledger}_ledger.jsonl")
        witnessed = _find_witnesses(prefix)
        legacy = json.loads((prefix.parent / "legacy_w2_diagnostic.json").read_text(encoding="utf-8"))
        v2 = json.loads((prefix.parent / "w2e_v2_reconciliation.json").read_text(encoding="utf-8"))
    require(legacy["old_w2"] is None and legacy["authoritative_for_RE6_R1"] is False,
            "LEGACY-W2-STILL-AUTHORITATIVE", legacy)
    require(v2["candidate_count"] == 29 and v2["valid_count"] == 12 and witnessed["pass"],
            "W2E-INPUT-EVIDENCE-NOT-AVAILABLE", {"witness_pass": witnessed["pass"], "v2": v2})
    return {"schema_version": "b2_t4_re6_r1_historical_route_replay_v1", "pass": True,
            "legacy_w2": None, "legacy_authoritative": False,
            "w2e_candidate_count": v2["candidate_count"], "w2e_valid_count": v2["valid_count"],
            "selected": v2["selected"], "all_witnesses_pass": witnessed["pass"]}


def preflight() -> dict[str, object]:
    identity = identities()
    replay = historical_route_replay()
    w2i = subprocess.run(
        (sys.executable, str(HERE / "test_assignment_phase_b2_t4_w2i_selector_identity_binding.py")),
        cwd=ROOT, capture_output=True, text=True, timeout=600, check=False)
    require(w2i.returncode == 0, "W2E-REVIEWED-IDENTITY-MISMATCH", w2i.stderr[-4000:])
    w2i_result = json.loads(w2i.stdout)
    require(w2i_result["status"] == "PASS" and w2i_result["positive_cases"] == 3
            and w2i_result["negative_cases"] == 18 and w2i_result["candidate_count"] == 29
            and w2i_result["valid_count"] == 12, "W2E-REVIEWED-REPLAY-NOT-QUALIFIED", w2i_result)
    result = _ENGINE["run_preflight"]()
    _ENGINE["_durable_json"](ARTIFACTS / "re6_r1_reviewed_identity.json", identity)
    _ENGINE["_durable_json"](ARTIFACTS / "re6_r1_historical_route_replay.json", replay)
    _ENGINE["_durable_json"](ARTIFACTS / "re6_r1_w2i_read_only_replay.json", w2i_result)
    commands = {row["name"]: bool(row["pass"]) for row in result["qualified_gates"]}
    receipt = json.loads((ARTIFACTS / "preflight_receipt_layer_b.json").read_text(encoding="utf-8"))
    tests = (
        ("approved interpreter", bool(json.loads((ARTIFACTS / "re6_r1_static_authority.json").read_text(encoding="utf-8"))["approved_interpreter_pass"])),
        ("py_compile", result["py_compile"]["pass"]),
        ("production hashes", result["static_authority_pass"]),
        ("W2E selector exact reviewed SHA", identity["pass"]),
        ("W2I binding exact SHA", identity["pass"]),
        ("PW helper exact SHA", result["static_authority_pass"]),
        ("NTFS same volume", result["filesystem_precondition"]["qualification_pass"]),
        ("environment import order", commands["registration_import_order"]),
        ("RE5 to RE6-R1 gate equivalence", result["pass"] and replay["pass"]),
        ("legacy W2 nonmandatory", replay["legacy_authoritative"] is False and replay["all_witnesses_pass"]),
        ("W2E sole W2 authority", replay["pass"]),
        ("W2E input sufficiency", replay["pass"]),
        ("W2E positives 3 of 3", w2i_result["positive_cases"] == 3),
        ("W2E negatives 18 of 18", w2i_result["negative_cases"] == 18 and w2i_result["unexpected_negative_passes"] == 0),
        ("W2E old W2 none", w2i_result["old_w2"] is None),
        ("W2E RE5 29 candidates 12 valid", w2i_result["candidate_count"] == 29 and w2i_result["valid_count"] == 12),
        ("PW focused qualification", result["pw_synthetic_positive"]["pass"] and result["pw_negative_sanity"]["pass"]),
        ("PW binding audit", result["pw_binding"]["pass"] and result["bound_callback_replay"]["pass"]),
        ("NR reviewed suite", commands["nr"]),
        ("NR terminal matrix", commands["nr"]),
        ("SR positives", commands["sr"]),
        ("SR negatives", commands["sr"]),
        ("retained RE1 replay", commands["sr"]),
        ("ledger roundtrip", commands["sr"]),
        ("post-S10 bookkeeping", result["after_tx_bookkeeping_replay"]["pass"]),
        ("ZD positive modes", commands["zd"]),
        ("ZD negatives", commands["zd"]),
        ("retained RE2 replay", commands["zd"]),
        ("I5b", commands["i5b"]),
        ("LD", commands["ld"]),
        ("controlled R5", commands["controlled_r5"]),
        ("row geometry", commands["row_geometry"]),
        ("CG", commands["critic_cg"]),
        ("ValueNorm", commands["valuenorm"]),
        ("T2 and T3 observer nonmutation", commands["t2_observer"] and commands["t3_observer"]),
        ("private and public guards", result["static_authority_pass"]),
        ("RE6-R1 Layer A synthetic success", receipt["layer_a_success"]["pass"]),
        ("RE6-R1 Layer A synthetic failure", not receipt["layer_a_failure"]["pass"]),
        ("EP-Q Layer B positives and negatives", all(receipt["layer_b_positive"].values()) and all(row["fail_closed"] for row in receipt["layer_b_negatives"].values())),
    )
    require(len(tests) == 39 and all(bool(ok) for _, ok in tests),
            "PRE-RUNTIME-QUALIFICATION-NOT-COMPLETE", [(name, ok) for name, ok in tests])
    _ENGINE["_durable_json"](ARTIFACTS / "re6_r1_pre_runtime_39_gate_matrix.json",
        {"schema_version": "b2_t4_re6_r1_pre_runtime_39_gate_matrix_v1",
         "gates": [{"index": index, "name": name, "pass": bool(ok)} for index, (name, ok) in enumerate(tests, 1)],
         "pass": True, "AppLauncher": 0, "formal_workers": 0})
    unchanged_gates = (
        "W1 cross-update ownership", "W3 zero-DVM actor", "W4 nonterminal bootstrap",
        "W5 normal-horizon terminal/autoreset", "W6 post-autoreset training",
        "W7 P2 runtime immutability", "S10", "transaction ledger qualification",
        "159 bridges", "NR", "SR", "ZD", "PW immutable progress",
        "actor plans", "critic plans", "HAPPO factor", "Adam continuity",
        "ValueNorm", "event returns", "numerical health", "Layer A receipt",
        "EP-Q Layer B", "irreversible-mutation poison semantics",
        "entry-point import order", "filesystem NTFS/same-volume", "single CUDA probe",
        "single worker and supervisor", "no checkpoint/public/evaluation route",
    )
    audit = {"schema_version": "b2_t4_re6_r1_gate_equivalence_v1", "pass": bool(result["pass"] and replay["pass"]),
             "source_derivation": DERIVATION, "unchanged_gate_source": sha(RE5_SOURCE),
             "sole_semantic_substitution": "W2 textual-claim result -> reviewed W2E reconcile result",
             "unchanged_gate_comparison": [
                 {"gate": name, "re5": "mandatory", "re6_r1": "mandatory",
                  "implementation": "source-derived unchanged RE5 gate", "pass": result["pass"]}
                 for name in unchanged_gates],
             "W2_comparison": {"re5": "textual task_claimed mandatory",
                               "re6_r1": "reviewed W2E-v2 reconcile mandatory",
                               "legacy_textual_claim": "diagnostic only",
                               "replay_pass": replay["pass"]},
             "legacy_w2_mandatory": False, "re5_preflight_pass": result["pass"],
             "historical_re5_copy_replay": replay, "w2i_read_only_replay_pass": True}
    _ENGINE["_durable_json"](ARTIFACTS / "re5_re6_r1_gate_equivalence.json", audit)
    mapping = {"schema_version": "b2_t4_re6_r1_w2e_normalization_mapping_v1",
               "reviewed_runner_sha256": sha(EXPECTED["w2e_runner"][0]),
               "function": "test_assignment_phase_b2_t4_w2e_claim_evidence_contract.normalize",
               "steps": "lifecycle_task_progress_ledger[*].steps[*] plus parent transaction_index",
               "decisions": "lifecycle_task_progress_ledger[*].lifecycle_rows[*] plus global_physical_step=(transaction_index-1)*2+physical_step_index",
               "transactions": "transaction_ledger rows unchanged",
               "bridges": "bridge_ledger rows unchanged",
               "authority": "reviewed selector reconcile(normalized) only; old W2 diagnostic",
               "historical_re5_input_replay_pass": replay["pass"]}
    _ENGINE["_durable_json"](ARTIFACTS / "re6_r1_w2e_normalization_mapping.json", mapping)
    require(audit["pass"], "GATE-EQUIVALENCE-NOT-ESTABLISHED", audit)
    return {"pass": True, "identity": identity, "replay": replay, "inherited_preflight": result}


def readiness() -> dict[str, object]:
    require((ARTIFACTS / "re5_re6_r1_gate_equivalence.json").is_file(), "READINESS-MISSING-PREFLIGHT")
    result = _ENGINE["run_readiness"]()
    replay = historical_route_replay()
    result["W2E_production_shaped_claim_bridge_continuation_complete_clear_reopen"] = replay
    result["legacy_old_W2_none_nonblocking"] = replay["legacy_w2"] is None and replay["all_witnesses_pass"]
    result["pass"] = bool(result["pass"] and replay["pass"] and result["legacy_old_W2_none_nonblocking"])
    _ENGINE["_durable_json"](ARTIFACTS / "re6_r1_runner_readiness_replay.json", result)
    require(result["pass"], "RUNNER-READINESS-NOT-QUALIFIED", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("preflight", "readiness", "formal-worker", "formal-supervisor", "sr-current-zd"))
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--run-id")
    parser.add_argument("--receipt")
    parser.add_argument("--timeout-seconds", type=int, default=10800)
    args = parser.parse_args()
    if args.mode == "preflight":
        result = preflight()
    elif args.mode == "readiness":
        result = readiness()
    elif args.mode == "sr-current-zd":
        require(args.artifact_dir is not None, "SR-CURRENT-ZD-ARTIFACT-DIR")
        result = _ENGINE["_run_sr_current_zd"](args.artifact_dir)
    elif args.mode == "formal-worker":
        identities()
        require((ARTIFACTS / "re6_r1_runner_readiness_replay.json").is_file(), "FORMAL-READINESS-MISSING")
        return _ENGINE["run_formal_worker"](args)
    else:
        identities()
        require((ARTIFACTS / "re6_r1_runner_readiness_replay.json").is_file(), "FORMAL-READINESS-MISSING")
        result = _ENGINE["run_formal_supervisor"](args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
