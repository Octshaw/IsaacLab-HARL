"""Supervise only the authorized real viewer; standard library, Windows only.

The main thread never reads the output pipe.  A suspended conda process is
assigned to an exclusive kill-on-close Job Object before any of its code runs.
No process-name termination, alternate runtime, or persistent settings are used.
Run only after the production changes and their pure checks have been reviewed.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
import traceback


REPO_ROOT = Path(r"E:\Project\IsaacLab_HARL")
CONDA = r"D:\miniconda3\Scripts\conda.exe"
ENV_PREFIX = r"C:\isaacenvs\isaac45_harl"
ENTRY = "scripts/environments/view_scan_assignment.py"
OUTPUT_ROOT = Path(__file__).resolve().parent
APP_LIMIT_SECONDS = 300.0
TOTAL_LIMIT_SECONDS = 360.0
WORK_LIMIT_SECONDS = 350.0  # Reserve ten seconds of the total for owned-process cleanup.
PREFIX = b"[RUNTIME_CHECK] "
MODE_OVERRIDES = {"HEADLESS": "0", "ENABLE_CAMERAS": "0", "LIVESTREAM": "0", "XR": "0"}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_input_desktop() -> dict:
    """Read-only check; never switch desktops or substitute a headless launch."""
    user = ctypes.WinDLL("user32", use_last_error=True)
    user.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    user.OpenInputDesktop.restype = wintypes.HANDLE
    user.CloseDesktop.argtypes = [wintypes.HANDLE]
    user.CloseDesktop.restype = wintypes.BOOL
    desktop = user.OpenInputDesktop(0, False, 0x0001)  # DESKTOP_READOBJECTS
    if not desktop:
        return {"input_desktop_opened": False, "winerror": ctypes.get_last_error()}
    user.CloseDesktop(desktop)
    return {"input_desktop_opened": True, "winerror": None}


class WindowsJob:
    """Handle-scoped ownership and cleanup; breakaway is deliberately disabled."""

    def __init__(self) -> None:
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.ntdll = ctypes.WinDLL("ntdll")
        self._configure_signatures()
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_longlong),
                ("PerJobUserTimeLimit", ctypes.c_longlong),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount",
            )]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BasicLimits), ("IoInfo", IoCounters),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        limits = ExtendedLimits()
        limits.BasicLimitInformation.LimitFlags = 0x00002000  # KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def _configure_signatures(self) -> None:
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "QueryInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "IsProcessInJob": ([wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL)], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "GetExitCodeProcess": ([wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)], wintypes.BOOL),
            "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = args, result
        self.ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]
        self.ntdll.NtResumeProcess.restype = ctypes.c_long

    def assign(self, process: subprocess.Popen) -> None:
        if not self.kernel.AssignProcessToJobObject(self.handle, wintypes.HANDLE(int(process._handle))):
            raise ctypes.WinError(ctypes.get_last_error())

    def resume(self, process: subprocess.Popen) -> None:
        status = self.ntdll.NtResumeProcess(wintypes.HANDLE(int(process._handle)))
        if status < 0:
            raise OSError(f"NtResumeProcess failed: NTSTATUS=0x{status & 0xffffffff:08x}")

    def pids(self) -> list[int]:
        capacity = 32
        while capacity <= 65536:
            class PidList(ctypes.Structure):
                _fields_ = [
                    ("NumberOfAssignedProcesses", wintypes.DWORD),
                    ("NumberOfProcessIdsInList", wintypes.DWORD),
                    ("ProcessIdList", ctypes.c_size_t * capacity),
                ]
            data = PidList()
            if self.kernel.QueryInformationJobObject(self.handle, 3, ctypes.byref(data), ctypes.sizeof(data), None):
                return [int(data.ProcessIdList[i]) for i in range(data.NumberOfProcessIdsInList)]
            error = ctypes.get_last_error()
            if error != 234:  # ERROR_MORE_DATA
                raise ctypes.WinError(error)
            capacity = max(capacity * 2, data.NumberOfAssignedProcesses)
        raise RuntimeError("Unexpectedly large owned process tree")

    def open_owned_process(self, pid: int):
        handle = self.kernel.OpenProcess(0x00100000 | 0x1000, False, pid)  # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        belongs = wintypes.BOOL()
        if not self.kernel.IsProcessInJob(handle, self.handle, ctypes.byref(belongs)) or not belongs.value:
            self.kernel.CloseHandle(handle)
            raise RuntimeError(f"PID {pid} is not confirmed in this attempt's Job Object")
        return handle

    def exit_code(self, handle) -> int:
        value = wintypes.DWORD()
        if not self.kernel.GetExitCodeProcess(handle, ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        return int(value.value)

    def terminate(self) -> None:
        if not self.kernel.TerminateJobObject(self.handle, 124):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def drain_output(pipe, console_path: Path, messages: queue.Queue) -> None:
    """Preserve bytes promptly, even when an output line is incomplete."""
    pending = b""
    try:
        with console_path.open("xb", buffering=0) as console:
            while True:
                chunk = os.read(pipe.fileno(), 65536)
                if not chunk:
                    break
                console.write(chunk)
                pending += chunk
                lines = pending.split(b"\n")
                pending = lines.pop()
                for line in lines:
                    if line.startswith(PREFIX):
                        try:
                            event = json.loads(line[len(PREFIX):].decode("utf-8"))
                            if not isinstance(event, dict) or not isinstance(event.get("stage"), str):
                                raise ValueError("event must contain a stage string")
                            messages.put(("event", event, now(), time.monotonic()))
                        except (UnicodeError, ValueError) as error:
                            messages.put(("error", f"Invalid runtime event: {error}", now(), time.monotonic()))
                if len(pending) > 1024 * 1024:
                    messages.put(("error", "Console line exceeds 1 MiB; bytes remain saved", now(), time.monotonic()))
                    pending = b""
            if pending.startswith(PREFIX):
                messages.put(("error", "Runtime event missing its terminating newline", now(), time.monotonic()))
    except BaseException as error:
        messages.put(("error", f"Console drain failed: {error!r}", now(), time.monotonic()))
    finally:
        pipe.close()
        messages.put(("eof", None, now(), time.monotonic()))


def build_command(ordinary: bool) -> list[str]:
    steps = 20 if ordinary else 120
    command = [
        CONDA, "run", "--no-capture-output", "-p", ENV_PREFIX, "python", "-u", ENTRY,
        "--task", "Isaac-Scan-Mobile-Manipulator-Direct-v0", "--num_envs", "1",
        "--solver", "greedy", "--device", "cuda:0", "--max_steps", str(steps),
        "--print_interval", str(steps),
    ]
    if not ordinary:
        command.append("--runtime_check")
    command.append("--info")
    return command


def check_previous_attempts(ordinary: bool) -> None:
    previous = list(OUTPUT_ROOT.glob("*/command.json"))
    resumed_count = 0
    for command_path in previous:
        result_path = command_path.with_name("result.json")
        previous_result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
        if previous_result.get("all_owned_processes_exited") is not True:
            raise RuntimeError(f"Previous attempt has no confirmed complete process cleanup: {command_path.parent}")
        resumed_count += previous_result.get("process_resumed") is True
    if resumed_count >= 2:
        raise RuntimeError("This validation directory already has two launches; no third launch is authorized")
    if ordinary and resumed_count == 0:
        raise RuntimeError("The first authorized launch must be the 120-step runtime check")


def supervise(attempt: Path, ordinary: bool) -> int:
    command = build_command(ordinary)
    child_env = os.environ.copy()
    original_modes = {key: child_env.get(key) for key in MODE_OVERRIDES}
    child_env.update(MODE_OVERRIDES)
    command_record = {
        "recorded_at": now(), "cwd": str(REPO_ROOT), "argv": command,
        "windows_command_line": subprocess.list2cmdline(command),
        "mode": "ordinary" if ordinary else "runtime_check", "expected_steps": 20 if ordinary else 120,
        "app_limit_seconds": APP_LIMIT_SECONDS, "total_limit_seconds": TOTAL_LIMIT_SECONDS,
        "work_limit_seconds": WORK_LIMIT_SECONDS,
        "child_environment_original_modes": original_modes, "child_environment_overrides": MODE_OVERRIDES,
        "kit_args_omitted": True, "supervisor_pid": os.getpid(),
    }
    write_json(attempt / "command.json", command_record)
    result = {
        **command_record, "started_at": None, "ended_at": None, "conda_pid": None,
        "viewer_pid": None, "conda_exit_code": None, "viewer_exit_code": None,
        "timed_out": False, "timeout_phase": None, "last_stage": None, "last_completed_stage": None,
        "job_assigned": False, "process_resumed": False, "termination_requested": False,
        "all_owned_processes_exited": False, "seen_owned_pids": [], "remaining_owned_pids": [],
        "supervisor_errors": [], "failure_events": [], "pre_close_result": None,
        "stage_names": [], "console_drain_complete": False,
        "internal_work_and_process_exit_pass": False,
        "graphics_api": "NOT_CHECKED_BY_SUPERVISOR; inspect this attempt's Kit log",
    }
    job = None
    process = None
    reader = None
    viewer_handle = None
    events = queue.Queue()
    started = None
    app_created = False
    seen_pids = set()
    event_log = (attempt / "events.jsonl").open("x", encoding="utf-8", buffering=1)

    def consume_events() -> None:
        nonlocal app_created, viewer_handle
        while True:
            try:
                kind, item, received_at, received_mono = events.get_nowait()
            except queue.Empty:
                return
            if kind == "eof":
                result["console_drain_complete"] = True
            elif kind == "error":
                result["supervisor_errors"].append(item)
            else:
                record = {"received_at": received_at, "elapsed_seconds": received_mono - started, "event": item}
                event_log.write(json.dumps(record, ensure_ascii=False) + "\n")
                stage = item["stage"]
                result["last_stage"] = stage
                result["stage_names"].append(stage)
                if stage in {"startup_identity", "pre_app_cuda_ready", "app_created", "cuda_verified",
                             "environment_created", "reset_completed", "steps_completed", "environment_closed",
                             "app_close_returned"}:
                    result["last_completed_stage"] = stage
                if "pid" in item and viewer_handle is None:
                    pid = item.get("pid")
                    if type(pid) is not int or pid <= 0:
                        result["supervisor_errors"].append("Runtime event has no valid viewer pid")
                    else:
                        result["viewer_pid"] = pid
                        try:
                            viewer_handle = job.open_owned_process(pid)
                            seen_pids.add(pid)
                        except (OSError, RuntimeError) as error:
                            result["supervisor_errors"].append(f"Cannot retain owned viewer handle: {error}")
                if stage == "app_created":
                    app_created = True
                    result["app_created_elapsed_seconds"] = received_mono - started
                    if received_mono - started > APP_LIMIT_SECONDS:
                        result["timed_out"] = True
                        result["timeout_phase"] = "app_creation"
                if stage in {"failure", "close_failure"}:
                    result["failure_events"].append(item)
                if stage == "pre_close_result":
                    result["pre_close_result"] = item
                print(f"[SUPERVISOR] stage={stage} elapsed={received_mono - started:.3f}s", flush=True)

    try:
        result["desktop_preflight"] = check_input_desktop()
        if result["desktop_preflight"]["input_desktop_opened"] is not True:
            raise RuntimeError("No accessible input desktop: GUI NOT_RUN; no headless substitution")
        job = WindowsJob()
        started = time.monotonic()
        result["started_at"] = now()
        process = subprocess.Popen(
            command, cwd=REPO_ROOT, env=child_env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0,
            creationflags=0x00000004,  # CREATE_SUSPENDED; GUI is still permitted.
        )
        result["conda_pid"] = process.pid
        job.assign(process)
        result["job_assigned"] = True
        seen_pids.add(process.pid)
        reader = threading.Thread(target=drain_output, args=(process.stdout, attempt / "console.log", events), daemon=True)
        reader.start()
        job.resume(process)
        result["process_resumed"] = True
        while True:
            consume_events()
            active = job.pids()
            seen_pids.update(active)
            elapsed = time.monotonic() - started
            if elapsed >= WORK_LIMIT_SECONDS or (not app_created and elapsed >= APP_LIMIT_SECONDS):
                result["timed_out"] = True
                result["timeout_phase"] = "work_budget_reserved_cleanup" if elapsed >= WORK_LIMIT_SECONDS else "app_creation"
            if result["timed_out"] or result["supervisor_errors"]:
                break
            if process.poll() is not None and not active:
                break
            time.sleep(0.1)
    except BaseException as error:
        result["supervisor_errors"].append(f"{type(error).__name__}: {error}")
        result["supervisor_traceback"] = traceback.format_exc()
    finally:
        # Only a held process handle or this exclusive Job Object may be terminated.
        final_deadline = time.monotonic() if started is None else started + TOTAL_LIMIT_SECONDS

        def remaining_wait(maximum: float) -> float:
            return max(0.0, min(maximum, final_deadline - time.monotonic()))

        try:
            if process is not None:
                if result["job_assigned"]:
                    if job.pids():
                        result["termination_requested"] = True
                        job.terminate()
                    cleanup_deadline = min(time.monotonic() + 8.0, final_deadline - 1.0)
                    while job.pids() and time.monotonic() < cleanup_deadline:
                        time.sleep(0.05)
                    result["remaining_owned_pids"] = job.pids()
                    result["all_owned_processes_exited"] = not result["remaining_owned_pids"]
                else:
                    # Assignment failed while the child was still suspended: no child code ran.
                    if process.poll() is None:
                        result["termination_requested"] = True
                        process.terminate()
                    process.wait(timeout=remaining_wait(8.0))
                    result["all_owned_processes_exited"] = True
                result["conda_exit_code"] = process.wait(timeout=remaining_wait(1.0)) if result["all_owned_processes_exited"] else process.poll()
            else:
                result["all_owned_processes_exited"] = True
            if reader is not None:
                reader.join(timeout=remaining_wait(1.0))
            consume_events()
            if viewer_handle is not None:
                result["viewer_exit_code"] = job.exit_code(viewer_handle)
        except BaseException as error:
            result["supervisor_errors"].append(f"Cleanup: {type(error).__name__}: {error}")
        finally:
            if viewer_handle is not None:
                job.kernel.CloseHandle(viewer_handle)
            if job is not None:
                job.close()  # Last-resort kill-on-close applies only to this job.
            event_log.close()
        result["ended_at"] = now()
        result["elapsed_seconds"] = None if started is None else time.monotonic() - started
        if result["elapsed_seconds"] is not None and result["elapsed_seconds"] > TOTAL_LIMIT_SECONDS:
            result["timed_out"] = True
            result["timeout_phase"] = "total_including_cleanup"
        result["execution_status"] = "FINISHED" if result["process_resumed"] else "NOT_RUN"
        result["seen_owned_pids"] = sorted(seen_pids)
        summary = result["pre_close_result"] or {}
        required_stages = {"app_created", "environment_created", "reset_completed", "steps_completed"}
        if not ordinary:
            required_stages.update({"startup_identity", "cuda_verified"})
        result["internal_work_and_process_exit_pass"] = bool(
            summary.get("work_completed") is True
            and summary.get("runtime_check") is (not ordinary)
            and summary.get("env_close_ok") is True
            and summary.get("app_close_requested") is True
            and summary.get("failures") == []
            and type(summary.get("step_count")) is int
            and summary.get("step_count") == command_record["expected_steps"]
            and summary.get("expected_steps") == command_record["expected_steps"]
            and required_stages.issubset(result["stage_names"])
            and result["conda_exit_code"] == 0 and result["viewer_exit_code"] == 0
            and result["all_owned_processes_exited"] and result["console_drain_complete"]
            and not result["timed_out"] and not result["termination_requested"]
            and not result["supervisor_errors"] and not result["failure_events"]
        )
        write_json(attempt / "result.json", result)
    print(json.dumps({"attempt": str(attempt), "internal_work_and_process_exit_pass": result["internal_work_and_process_exit_pass"],
                      "timed_out": result["timed_out"], "last_stage": result["last_stage"],
                      "all_owned_processes_exited": result["all_owned_processes_exited"]}, ensure_ascii=False), flush=True)
    return 0 if result["internal_work_and_process_exit_pass"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, help="Unique simple name for a new evidence directory")
    parser.add_argument("--ordinary", action="store_true", help="Optional second attempt, ordinary viewer with 20 steps")
    args = parser.parse_args()
    if os.name != "nt":
        parser.error("This bounded supervisor supports only the authorized Windows environment")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", args.attempt):
        parser.error("--attempt must use 1-64 letters, digits, underscores or hyphens")
    if Path.cwd().resolve() != REPO_ROOT.resolve():
        parser.error(f"Run from the authorized repository: {REPO_ROOT}")
    check_previous_attempts(args.ordinary)
    attempt = OUTPUT_ROOT / args.attempt
    attempt.mkdir(exist_ok=False)
    return supervise(attempt, args.ordinary)


if __name__ == "__main__":
    raise SystemExit(main())
