"""Status constants for the dynamic assignment interface MVP."""

from __future__ import annotations

from collections.abc import Mapping

import torch


TASK_UNASSIGNED = 0
TASK_ASSIGNED = 1
TASK_IN_PROGRESS = 2
TASK_COMPLETED = 3
TASK_FAILED = 4
TASK_UNREACHABLE = 5
TASK_TIMEOUT = 6

ROBOT_IDLE = 0
ROBOT_MOVING = 1
ROBOT_SCANNING = 2
ROBOT_BLOCKED = 3
ROBOT_FAILED = 4
ROBOT_DISABLED = 5

TASK_STATUS_NAMES: dict[int, str] = {
    TASK_UNASSIGNED: "unassigned",
    TASK_ASSIGNED: "assigned",
    TASK_IN_PROGRESS: "in_progress",
    TASK_COMPLETED: "completed",
    TASK_FAILED: "failed",
    TASK_UNREACHABLE: "unreachable",
    TASK_TIMEOUT: "timeout",
}

ROBOT_STATUS_NAMES: dict[int, str] = {
    ROBOT_IDLE: "idle",
    ROBOT_MOVING: "moving",
    ROBOT_SCANNING: "scanning",
    ROBOT_BLOCKED: "blocked",
    ROBOT_FAILED: "failed",
    ROBOT_DISABLED: "disabled",
}


def status_counts(status: torch.Tensor, names: Mapping[int, str]) -> dict[str, dict[str, int | str]]:
    """Return JSON-friendly counts keyed by status id.

    Missing statuses are included with count zero so downstream diagnostics have a stable schema across resets and
    one-step smoke runs.
    """

    if not isinstance(status, torch.Tensor):
        raise TypeError(f"status must be a torch.Tensor, got {type(status).__name__}")

    status_cpu = status.detach().to(device="cpu", dtype=torch.long)
    result: dict[str, dict[str, int | str]] = {}
    for status_id, name in names.items():
        count = int((status_cpu == int(status_id)).sum().item())
        result[str(int(status_id))] = {"name": str(name), "count": count}
    return result


__all__ = [
    "ROBOT_BLOCKED",
    "ROBOT_DISABLED",
    "ROBOT_FAILED",
    "ROBOT_IDLE",
    "ROBOT_MOVING",
    "ROBOT_SCANNING",
    "ROBOT_STATUS_NAMES",
    "TASK_ASSIGNED",
    "TASK_COMPLETED",
    "TASK_FAILED",
    "TASK_IN_PROGRESS",
    "TASK_STATUS_NAMES",
    "TASK_TIMEOUT",
    "TASK_UNASSIGNED",
    "TASK_UNREACHABLE",
    "status_counts",
]
