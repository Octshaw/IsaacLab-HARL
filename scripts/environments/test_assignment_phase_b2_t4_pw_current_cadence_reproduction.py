"""Pure, paced reproduction of the frozen current cumulative JSON pattern."""

import ctypes
import json
import os
import tempfile
import time
from pathlib import Path

from test_assignment_phase_b2_t4_pw_windows_evidence_persistence import (
    OUT, dump, hold_destination, source_current_helper,
)


def main() -> None:
    current = source_current_helper()
    with tempfile.TemporaryDirectory(prefix="b2_t4_pw_current_paced_") as td:
        target = Path(td) / "tx001_critic_progress.json"
        events = []
        sizes = []
        started = time.perf_counter()
        for sequence in range(1, 42):
            # RE4's final cumulative file was 796,580 bytes / 41 events.
            # The source-equivalent primitive event size is approximately 19 KB.
            events.append({"sequence": sequence, "diagnostic": "X" * 19000})
            current(target, {"stage": "S6_CRITIC_PROGRESS", "event_count": sequence,
                             "events": events})
            sizes.append(target.stat().st_size)
            time.sleep(0.12)
        assert json.loads(target.read_text(encoding="utf-8"))["event_count"] == 41
        kernel, handle = hold_destination(target)
        try:
            try:
                current(target, {"stage": "S6_CRITIC_PROGRESS", "event_count": 42,
                                 "events": events + [{"sequence": 42, "diagnostic": "X" * 19000}]})
            except PermissionError as exc:
                denial = f"{type(exc).__name__}: {exc}"
            else:
                raise AssertionError("Expected WinError on held-open target")
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
        assert target.with_name(target.name + ".tmp").exists()
        dump("current_helper_cadence_reproduction.json", {
            "status": "passed", "isolated_process_pid": os.getpid(),
            "writes": 41, "cadence_sleep_seconds": 0.12,
            "first_final_bytes": sizes[0], "last_final_bytes": sizes[-1],
            "elapsed_seconds": time.perf_counter() - started,
            "held_target_result": denial,
            "temp_residue_before_isolated_workspace_cleanup": True,
            "AppLauncher": 0, "environment": 0, "learner": 0})


if __name__ == "__main__":
    main()
