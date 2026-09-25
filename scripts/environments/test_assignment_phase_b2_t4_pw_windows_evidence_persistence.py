"""Pure Windows persistence qualification for B2-T4-PW; never imports Isaac."""

from __future__ import annotations

import argparse
import ast
import ctypes
import hashlib
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Mapping
from unittest.mock import patch

import _assignment_phase_b2_t4_windows_evidence_persistence as PW


ROOT = Path(__file__).resolve().parents[2]
DAY = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260916"
RE4 = DAY / "b2_t4_re4_artifacts"
OUT = DAY / "b2_t4_pw_artifacts"
PREFIX = "b2_t4_re4_normal_horizon_20260916_formal01"
V2_SOURCE = ROOT / "scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py"
PW_SOURCE = Path(PW.__file__).resolve()
THIS_SOURCE = Path(__file__).resolve()
RUN_ID = "b2-t4-pw-qualification"
PLANNED = 41
W_EXPECTED_160 = 160 * PLANNED
STRESS_WRITES = max(10000, 10 * W_EXPECTED_160)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name: str, value: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    if path.exists():
        raise RuntimeError(f"PW artifact already exists: {path}")
    data = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False).encode("utf-8") + b"\n"
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def payload(tx: int, sequence: int, *, run_id: str = RUN_ID,
            stage: str = "S6_CRITIC_MINIBATCH_COMPLETE", evidence: object = None) -> dict[str, object]:
    return {"run_id": run_id, "tx_id": tx, "stage": stage,
            "actor_or_critic": "critic", "source_evidence": evidence if evidence is not None else "X" * 20000,
            "sequence_diagnostic": sequence}


def artifact(name: str) -> Path:
    return RE4 / f"{PREFIX}_{name}"


def source_current_helper():
    """Compile exactly the historical pure file-op function, without module imports."""
    tree = ast.parse(V2_SOURCE.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "atomic_json")
    module = ast.Module(body=[node], type_ignores=[])
    ast.fix_missing_locations(module)
    namespace = {"Path": Path, "os": os, "json": json, "Mapping": Mapping,
                 "normalize": lambda x: x}
    exec(compile(module, str(V2_SOURCE), "exec"), namespace)
    return namespace["atomic_json"]


def hold_destination(path: Path):
    """Open a Windows handle that allows reads but denies FILE_SHARE_DELETE."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                                  ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    kernel.CreateFileW.restype = ctypes.c_void_p
    handle = kernel.CreateFileW(str(path), 0x80000000, 1, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_last_error(), "CreateFileW failed")
    return kernel, handle


def audit() -> None:
    paths = [RE4 / n for n in ("formal_worker_receipt.json", "formal_supervisor_result.json", "final_result.json")]
    paths += [artifact(n) for n in (
        "tx129_critic_progress.json", "tx129_actor_factor_progress.json", "tx129_pre_mutation.json",
        "tx130_critic_progress.json", "tx130_critic_progress.json.tmp",
        "tx130_actor_factor_progress.json", "tx130_pre_mutation.json", "tx130_failure.json",
        "transaction_ledger.jsonl", "training_metric_ledger.jsonl", "rolling_health_ledger.jsonl")]
    identity = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in paths}
    dump("re4_failure_artifact_identity.json", identity)
    old = json.loads(artifact("tx130_critic_progress.json").read_text(encoding="utf-8"))
    tmp_path = artifact("tx130_critic_progress.json.tmp")
    temp = json.loads(tmp_path.read_text(encoding="utf-8"))
    fail = json.loads(artifact("tx130_failure.json").read_text(encoding="utf-8"))
    forensic = {
        "stage": "S6_CRITIC_SEQUENCE", "target": str(artifact("tx130_critic_progress.json")),
        "temp": str(tmp_path), "target_existed": True,
        "target_bytes": identity[artifact("tx130_critic_progress.json").name]["bytes"],
        "temp_bytes": identity[tmp_path.name]["bytes"],
        "target_sha256": sha(artifact("tx130_critic_progress.json")), "temp_sha256": sha(tmp_path),
        "target_last_write_utc": artifact("tx130_critic_progress.json").stat().st_mtime,
        "temp_last_write_utc": tmp_path.stat().st_mtime,
        "temp_parseable": True, "temp_schema": temp.get("schema_version"),
        "temp_event_count": temp["event_count"], "temp_last_stage": temp["events"][-1]["stage"],
        "target_event_count": old["event_count"], "target_last_stage": old["events"][-1]["stage"],
        "temp_critic_steps": temp["cumulative_critic_optimizer_step_count"],
        "temp_valuenorm_updates": temp["cumulative_live_valuenorm_update_count"],
        "failure": fail, "boundary": "os.replace after temp flush/fsync/handle close; target remained seq27",
    }
    dump("tx130_forensic_audit.json", forensic)
    progress = []
    residues = []
    for tx in range(1, 130):
        p = artifact(f"tx{tx}_critic_progress.json")
        j = json.loads(p.read_text(encoding="utf-8"))
        progress.append({"tx": tx, "event_count": j["event_count"], "size": p.stat().st_size,
                         "stage": j["stage"], "last_write_ns": p.stat().st_mtime_ns})
        if list(RE4.glob(p.name + ".tmp*")):
            residues.append(tx)
    ledgers = {}
    for name in ("transaction_ledger", "training_metric_ledger", "rolling_health_ledger"):
        p = artifact(f"{name}.jsonl")
        ledgers[name] = sum(1 for line in p.open(encoding="utf-8") if line.strip())
    dump("completed_prefix_persistence_audit.json", {
        "critic_progress_files": len(progress), "all_have_41_events": all(x["event_count"] == 41 for x in progress),
        "same_destination_rewritten": True, "successful_replacements_minimum": 129 * 41 - 129,
        "successful_os_replace_calls_on_critic_progress": 129 * 41,
        "earlier_temp_residue_tx": residues, "ledgers": ledgers,
        "critic_progress_bytes_min": min(x["size"] for x in progress),
        "critic_progress_bytes_max": max(x["size"] for x in progress),
        "critic_progress_final_file_last_write_only": True,
        "per_write_timing_history_available": False,
        "entries": progress,
    })
    dump("current_write_frequency.json", {
        "critic_pre_valuenorm": 1, "critic_post_valuenorm": 1,
        "critic_pre_backward": 1, "critic_minibatch_complete": 1,
        "per_minibatch": 4, "minibatches_per_epoch": 2, "epochs": 5,
        "critic_sequence_complete": 1, "per_transaction": PLANNED,
        "W_expected_160": W_EXPECTED_160, "required_stress_writes": STRESS_WRITES,
        "observed_tx129_events": 41, "observed_tx130_final_events": 27,
        "observed_tx130_temp_events": 28,
    })


def expect_failure(name: str, fn, accepted: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    try:
        fn()
    except Exception as exc:
        observed = f"{type(exc).__name__}: {exc}"
        passed = any(token in observed for token in accepted)
    else:
        observed, passed = "UNEXPECTED_SUCCESS", False
    rows.append({"case": name, "passed": passed, "observed": observed})
    if not passed:
        raise AssertionError(f"{name}: {observed}")


def qualify() -> None:
    rows: list[dict[str, object]] = []
    current = source_current_helper()
    with tempfile.TemporaryDirectory(prefix="b2_t4_pw_current_") as td:
        target = Path(td) / "critic_progress.json"
        source_payload = {"events": ["X" * 20000], "event_count": 1}
        for i in range(41):
            source_payload["event_count"] = i + 1
            current(target, source_payload)
        assert json.loads(target.read_text(encoding="utf-8"))["event_count"] == 41
        kernel, handle = hold_destination(target)
        try:
            expect_failure("current_helper_held_open_target", lambda: current(target, source_payload),
                           ("PermissionError", "WinError 5", "WinError 32"), rows)
            assert target.with_name(target.name + ".tmp").is_file()
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
        dump("current_helper_reproduction.json", {
            "source_sha256": sha(V2_SOURCE), "exact_function_ast": "atomic_json",
            "isolated_successful_writes": 41, "held_target_result": rows[-1],
            "temp_residue_preserved_in_isolated_workspace_before_cleanup": True,
            "learner_or_app_imports": 0})

    with tempfile.TemporaryDirectory(prefix="b2_t4_pw_negative_") as td:
        root = Path(td)
        write = lambda tx, seq, **kw: PW.write_record(root, run_id=RUN_ID, tx_id=tx,
                            stage="S6_CRITIC_MINIBATCH_COMPLETE", actor_or_critic="critic",
                            progress_sequence=seq, planned_sequence_count=2,
                            payload=payload(tx, seq, **kw))
        expect_failure("malformed_payload", lambda: PW.write_record(root, run_id=RUN_ID, tx_id=1,
                       stage="S6_CRITIC_MINIBATCH_COMPLETE", actor_or_critic="critic",
                       progress_sequence=1, planned_sequence_count=2, payload={"bad": object()}),
                       ("PAYLOAD_RUN_TX_MISMATCH", "MALFORMED_PAYLOAD"), rows)
        expect_failure("out_of_order", lambda: write(2, 2),
                       ("RECORD_MISSING_OR_MALFORMED",), rows)
        expect_failure("wrong_run", lambda: write(3, 1, run_id="wrong-run"),
                       ("PAYLOAD_RUN_TX_MISMATCH",), rows)
        expect_failure("wrong_tx", lambda: PW.write_record(root, run_id=RUN_ID, tx_id=4,
                       stage="S6_CRITIC_MINIBATCH_COMPLETE", actor_or_critic="critic",
                       progress_sequence=1, planned_sequence_count=2, payload=payload(5, 1)),
                       ("PAYLOAD_RUN_TX_MISMATCH",), rows)
        first = write(5, 1)
        expect_failure("duplicate_sequence", lambda: write(5, 1),
                       ("DUPLICATE_PROGRESS_IDENTITY",), rows)
        expect_failure("wrong_run_read", lambda: PW.read_record(first, run_id="wrong", tx_id=5,
                       side="critic", sequence=1, planned_count=2),
                       ("RECORD_IDENTITY_MISMATCH",), rows)
        expect_failure("wrong_tx_read", lambda: PW.read_record(first, run_id=RUN_ID, tx_id=6,
                       side="critic", sequence=1, planned_count=2),
                       ("RECORD_IDENTITY_MISMATCH",), rows)
        expect_failure("missing_required_record", lambda: PW.verify_transaction(root, run_id=RUN_ID,
                       tx_id=5, side="critic", planned_count=2),
                       ("MISSING_OR_EXTRA_REQUIRED_RECORD",), rows)
        bad = json.loads(first.read_text(encoding="utf-8"))
        bad["payload"]["sequence_diagnostic"] = 999
        first.write_text(json.dumps(bad), encoding="utf-8")
        expect_failure("digest_mismatch", lambda: PW.read_record(first, run_id=RUN_ID,
                       tx_id=5, side="critic", sequence=1, planned_count=2),
                       ("PAYLOAD_DIGEST_MISMATCH",), rows)
        stale = root / RUN_ID / "tx007" / "critic_progress_00001.json.tmp.stale"
        stale.parent.mkdir(parents=True)
        stale.write_bytes(b"stale")
        expect_failure("stale_temp", lambda: write(7, 1),
                       ("STALE_TEMP_REQUIRES_REVIEW",), rows)
        expect_failure("temp_only_incomplete", lambda: PW.verify_transaction(root, run_id=RUN_ID,
                       tx_id=7, side="critic", planned_count=2),
                       ("TEMP_RESIDUE_REQUIRES_REVIEW",), rows)
        with patch.object(PW.os, "link", side_effect=PermissionError(5, "simulated denied")):
            expect_failure("publication_permission_denied", lambda: write(8, 1),
                           ("PermissionError",), rows)
        expect_failure("stale_after_denied", lambda: write(8, 1),
                       ("STALE_TEMP_REQUIRES_REVIEW",), rows)
        good = write(9, 1)
        kernel, handle = hold_destination(good)
        try:
            expect_failure("held_open_existing_identity", lambda: write(9, 1),
                           ("DUPLICATE_PROGRESS_IDENTITY",), rows)
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
        with patch.object(PW, "read_record", side_effect=PW.EvidencePersistenceError("READBACK_MISMATCH")):
            expect_failure("readback_mismatch", lambda: write(10, 1),
                           ("READBACK_MISMATCH",), rows)
        expect_failure("final_after_failed_readback", lambda: write(10, 1),
                       ("DUPLICATE_PROGRESS_IDENTITY",), rows)
        expect_failure("malformed_json_final", lambda: PW.read_record(stale, run_id=RUN_ID,
                       tx_id=7, side="critic", sequence=1, planned_count=2),
                       ("RECORD_MISSING_OR_MALFORMED",), rows)
    dump("negative_matrix.json", {"cases": rows, "count": len(rows),
                                  "all_pass": all(row["passed"] for row in rows)})


def stress(run_number: int) -> None:
    count = STRESS_WRITES
    timings: list[int] = []
    bytes_written = 0
    transactions = count // PLANNED
    with tempfile.TemporaryDirectory(prefix=f"b2_t4_pw_stress_{run_number}_") as td:
        root = Path(td)
        start = time.perf_counter_ns()
        for tx in range(1, transactions + 1):
            for seq in range(1, PLANNED + 1):
                p = payload(tx, seq)
                t0 = time.perf_counter_ns()
                final = PW.write_record(root, run_id=RUN_ID, tx_id=tx,
                    stage=p["stage"], actor_or_critic="critic", progress_sequence=seq,
                    planned_sequence_count=PLANNED, payload=p)
                timings.append(time.perf_counter_ns() - t0)
                bytes_written += final.stat().st_size
            if tx % 100 == 0 or tx == transactions:
                assert len(PW.verify_transaction(root, run_id=RUN_ID, tx_id=tx,
                                                  side="critic", planned_count=PLANNED)) == PLANNED
        elapsed = (time.perf_counter_ns() - start) / 1e9
        # Full-file verification of every transaction, including the 160-tx slice.
        for tx in range(1, transactions + 1):
            assert len(PW.verify_transaction(root, run_id=RUN_ID, tx_id=tx,
                                              side="critic", planned_count=PLANNED)) == PLANNED
        leftovers = list(root.rglob("*.tmp.*"))
        assert not leftovers
        s = sorted(timings)
        def ms(n: int) -> float:
            return s[min(len(s) - 1, int((len(s) - 1) * n / 100))] / 1e6
        result = {"status": "passed", "fresh_process_pid": os.getpid(), "run_number": run_number,
                  "transactions": transactions, "writes": count,
                  "W_expected_160": W_EXPECTED_160, "required_minimum": STRESS_WRITES,
                  "bytes": bytes_written, "elapsed_seconds": elapsed,
                  "mean_latency_ms": statistics.mean(timings) / 1e6,
                  "p50_ms": ms(50), "p95_ms": ms(95), "p99_ms": ms(99),
                  "max_ms": s[-1] / 1e6, "unexpected_permission_errors": 0,
                  "missing_records": 0, "duplicate_records": 0,
                  "digest_mismatches": 0, "stale_temp_promotions": 0,
                  "unreconciled_temp_residue": len(leftovers),
                  "simulation_160tx_pass": transactions >= 160,
                  "realistic_payload_bytes_per_record": len(payload(1, 1)["source_evidence"]),
                  "AppLauncher": 0, "environment": 0, "learner": 0}
        dump(f"repaired_stress_run_{run_number:02d}.json", result)
        if run_number == 1:
            dump("re4_scale_160tx_simulation.json", {
                "status": "passed", "run_number": 1, "transactions": 160,
                "records": W_EXPECTED_160, "first_160_transactions_fully_verified": True,
                "learner_or_environment": 0})


def replay() -> None:
    source = json.loads(artifact("tx130_critic_progress.json.tmp").read_text(encoding="utf-8"))
    event = source["events"][-1]
    with tempfile.TemporaryDirectory(prefix="b2_t4_pw_replay_") as td:
        root = Path(td)
        # The prior 27 events establish the exact sequence context.
        for sequence, item in enumerate(source["events"], 1):
            p = payload(130, sequence, run_id="b2-t4-pw-tx130-replay",
                        stage=item["stage"], evidence=item)
            final = PW.write_record(root, run_id=p["run_id"], tx_id=130,
                                    stage=p["stage"], actor_or_critic="critic",
                                    progress_sequence=sequence, planned_sequence_count=28,
                                    payload=p)
        records = PW.verify_transaction(root, run_id="b2-t4-pw-tx130-replay",
                                        tx_id=130, side="critic", planned_count=28)
        assert records[-1]["payload"]["source_evidence"] == event
        dump("tx130_payload_replay.json", {"status": "passed", "source_temp_sha256": sha(artifact("tx130_critic_progress.json.tmp")),
             "source_event_sequence": 28, "source_stage": event["stage"],
             "replayed_records": len(records), "final_sha256": sha(final),
             "record_digest": records[-1]["record_sha256"], "durable_readback": True,
             "learner_reconstructed": False})


def negative_extension() -> None:
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="b2_t4_pw_negative_extra_") as td:
        root = Path(td)
        malformed = payload(1, 1)
        malformed["bad_float"] = float("nan")
        expect_failure("non_json_finite_payload", lambda: PW.write_record(root, run_id=RUN_ID,
                       tx_id=1, stage=malformed["stage"], actor_or_critic="critic",
                       progress_sequence=1, planned_sequence_count=2, payload=malformed),
                       ("MALFORMED_PAYLOAD",), rows)
        assert not list(root.rglob("*.json"))
    dump("negative_matrix_extension.json", {"cases": rows, "all_pass": all(x["passed"] for x in rows)})


def reader_child(target: Path, ready: Path, stop: Path, *, held: bool) -> None:
    if held:
        kernel, handle = hold_destination(target)
        ready.write_text("ready", encoding="utf-8")
        try:
            while not stop.exists():
                time.sleep(0.005)
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
    else:
        reads = 0
        denied = 0
        ready.write_text("ready", encoding="utf-8")
        while not stop.exists():
            try:
                target.read_bytes()
                reads += 1
            except FileNotFoundError:
                pass
            except PermissionError:
                denied += 1
        print(f"reads={reads} denied={denied}")


def concurrency() -> None:
    current = source_current_helper()
    results = {}
    with tempfile.TemporaryDirectory(prefix="b2_t4_pw_concurrent_") as td:
        root = Path(td)
        target = root / "current.json"
        current(target, {"n": 0, "data": "X" * 20000})
        def launch(target_path: Path, *, held: bool):
            ready = root / f"ready_{os.urandom(4).hex()}"
            stop = root / f"stop_{os.urandom(4).hex()}"
            cmd = [sys.executable, str(THIS_SOURCE), "--mode", "reader-child",
                   "--target", str(target_path), "--ready", str(ready), "--stop", str(stop)]
            if held:
                cmd.append("--held")
            child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            deadline = time.monotonic() + 10
            while not ready.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.005)
            assert ready.exists(), child.communicate(timeout=1)
            return child, stop
        child, stop = launch(target, held=False)
        successes = 0
        failures = []
        try:
            for n in range(1, 201):
                try:
                    current(target, {"n": n, "data": "X" * 20000})
                    successes += 1
                except PermissionError as exc:
                    failures.append(f"{type(exc).__name__}: {exc}")
                    # Current helper leaves a complete temp; the next attempt reuses it.
            results["current_rapid_reader"] = {"successes": successes,
                                                "permission_failures": len(failures),
                                                "specific_reader_causality": "controlled overlap; individual failing handle not traced"}
        finally:
            stop.write_text("stop", encoding="utf-8")
            stdout, stderr = child.communicate(timeout=10)
            assert child.returncode == 0, stderr
            results["current_rapid_reader"]["reader_output"] = stdout.strip()
        child, stop = launch(target, held=True)
        try:
            try:
                current(target, {"n": 201, "data": "X" * 20000})
            except PermissionError as exc:
                results["current_independent_held_reader"] = f"{type(exc).__name__}: {exc}"
            else:
                raise AssertionError("held independent reader did not block current replacement")
        finally:
            stop.write_text("stop", encoding="utf-8")
            _, stderr = child.communicate(timeout=10)
            assert child.returncode == 0, stderr
        p1 = payload(1, 1)
        first = PW.write_record(root / "new", run_id=RUN_ID, tx_id=1, stage=p1["stage"],
                                actor_or_critic="critic", progress_sequence=1,
                                planned_sequence_count=2, payload=p1)
        child, stop = launch(first, held=True)
        try:
            p2 = payload(1, 2)
            second = PW.write_record(root / "new", run_id=RUN_ID, tx_id=1,
                                     stage=p2["stage"], actor_or_critic="critic",
                                     progress_sequence=2, planned_sequence_count=2, payload=p2)
            assert second.exists()
            results["new_independent_held_previous_reader"] = "PASS_NEW_IMMUTABLE_SEQUENCE"
        finally:
            stop.write_text("stop", encoding="utf-8")
            _, stderr = child.communicate(timeout=10)
            assert child.returncode == 0, stderr
        assert len(PW.verify_transaction(root / "new", run_id=RUN_ID, tx_id=1,
                                         side="critic", planned_count=2)) == 2
    dump("concurrent_reader_audit.json", results)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("audit", "qualify", "stress", "replay",
                                           "negative-extension", "concurrency", "reader-child"), required=True)
    parser.add_argument("--run-number", type=int, default=1)
    parser.add_argument("--target", type=Path)
    parser.add_argument("--ready", type=Path)
    parser.add_argument("--stop", type=Path)
    parser.add_argument("--held", action="store_true")
    args = parser.parse_args()
    if os.name != "nt":
        raise RuntimeError("PW qualification requires Windows")
    if args.mode == "reader-child":
        reader_child(args.target, args.ready, args.stop, held=args.held)
        return
    {"audit": audit, "qualify": qualify, "stress": lambda: stress(args.run_number),
     "replay": replay, "negative-extension": negative_extension,
     "concurrency": concurrency}[args.mode]()
    print(f"PW {args.mode} PASS pid={os.getpid()}")


if __name__ == "__main__":
    main()
