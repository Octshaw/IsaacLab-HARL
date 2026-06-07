# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import importlib.util
from pathlib import Path

import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
    / "assignment_rl_interface.py"
)


def _load_assignment_rl_interface():
    spec = importlib.util.spec_from_file_location("assignment_rl_interface_under_test", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec from {MODULE_PATH}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_tensor_equal(actual: torch.Tensor, expected: torch.Tensor, message: str) -> None:
    if not torch.equal(actual, expected):
        raise AssertionError(f"{message}: expected {expected}, got {actual}")


def test_make_assignment_action_mask(interface) -> None:
    available_mask = torch.tensor(
        [
            [[True, False, True], [False, True, False]],
            [[False, False, True], [True, True, False]],
        ],
        dtype=torch.bool,
    )
    problem = {"available_mask": available_mask}

    mask = interface.make_assignment_action_mask(problem)

    assert tuple(mask.shape) == (2, 2, 4)
    assert mask.dtype == torch.float32
    assert mask.device == available_mask.device
    _assert_tensor_equal(mask[..., :3], available_mask.to(dtype=torch.float32), "viewpoint mask mismatch")
    _assert_tensor_equal(mask[..., 3], torch.ones(2, 2), "no-op column mismatch")


def test_decode_discrete_assignment(interface) -> None:
    env_agent_actions = torch.tensor([[[0], [3]], [[2], [1]]])
    expected = torch.tensor([[0, -1], [2, 1]], dtype=torch.long)

    decoded_env_agent = interface.decode_discrete_assignment(
        env_agent_actions,
        num_viewpoints=3,
        num_envs=2,
        num_agents=2,
        layout="env_agent_action",
    )
    _assert_tensor_equal(decoded_env_agent, expected, "env_agent_action decode mismatch")
    assert decoded_env_agent.dtype == torch.long
    assert decoded_env_agent.device == env_agent_actions.device

    agent_env_actions = torch.tensor([[[0], [2]], [[3], [1]]])
    decoded_agent_env = interface.decode_discrete_assignment(
        agent_env_actions,
        num_viewpoints=3,
        num_envs=2,
        num_agents=2,
        layout="agent_env_action",
    )
    _assert_tensor_equal(decoded_agent_env, expected, "agent_env_action decode mismatch")
    assert decoded_agent_env.dtype == torch.long


def test_compute_assignment_duplicate_count(interface) -> None:
    assignment = torch.tensor(
        [
            [1, 1, -1, 2],
            [-1, 2, 2, 2],
            [0, -1, 1, 2],
        ],
        dtype=torch.long,
    )

    duplicates = interface.compute_assignment_duplicate_count(assignment)

    _assert_tensor_equal(duplicates, torch.tensor([1.0, 2.0, 0.0]), "duplicate count mismatch")
    assert duplicates.device == assignment.device


def test_strict_invalid_action_raises(interface) -> None:
    invalid_actions = torch.tensor([[[4], [0]], [[1], [2]]])

    try:
        interface.decode_discrete_assignment(
            invalid_actions,
            num_viewpoints=3,
            num_envs=2,
            num_agents=2,
            layout="env_agent_action",
            strict=True,
        )
    except ValueError:
        return

    raise AssertionError("strict=True should raise ValueError for invalid action ids")


def main() -> None:
    interface = _load_assignment_rl_interface()
    test_make_assignment_action_mask(interface)
    test_decode_discrete_assignment(interface)
    test_compute_assignment_duplicate_count(interface)
    test_strict_invalid_action_raises(interface)
    print("[OK] assignment_rl_interface self-check passed")


if __name__ == "__main__":
    main()
