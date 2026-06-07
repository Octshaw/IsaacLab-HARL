# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import gymnasium
import numpy as np
import torch


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
ADAPTER_PATH = MODULE_DIR / "assignment_harl_adapter.py"


def _load_assignment_harl_adapter():
    sys.path.insert(0, str(MODULE_DIR))
    spec = importlib.util.spec_from_file_location("assignment_harl_adapter_under_test", ADAPTER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to load module spec from {ADAPTER_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_policy_args() -> dict:
    return {
        "hidden_sizes": [16],
        "activation_func": "relu",
        "initialization_method": "orthogonal_",
        "use_feature_normalization": False,
        "gain": 0.01,
        "use_policy_active_masks": True,
        "use_naive_recurrent_policy": False,
        "use_recurrent_policy": False,
        "recurrent_n": 1,
        "std_x_coef": 1.0,
        "std_y_coef": 0.5,
    }


def test_adapter_shapes(adapter_module) -> None:
    adapter = adapter_module.AssignmentHarlAdapter(num_envs=2, num_agents=3, num_viewpoints=12, device="cpu")
    action_spaces = adapter.action_spaces

    assert set(action_spaces.keys()) == {0, 1, 2}
    assert all(space.__class__.__name__ == "Discrete" for space in action_spaces.values())
    assert all(space.n == 13 for space in action_spaces.values())
    assert adapter.max_scalar_action_dim == 1

    action_tensor = adapter.make_action_tensor()
    assert tuple(action_tensor.shape) == (2, 3, 1)
    assert action_tensor.dtype == torch.float32

    available_mask = torch.ones(2, 3, 12, dtype=torch.bool)
    available_actions = adapter.make_available_actions({"available_mask": available_mask})
    assert tuple(available_actions.shape) == (2, 3, 13)
    assert torch.all(available_actions[..., -1] == 1.0)

    discrete_actions = torch.tensor([[[0], [12], [3]], [[4], [5], [12]]])
    assignment = adapter.decode_actions(discrete_actions)
    expected = torch.tensor([[0, -1, 3], [4, 5, -1]], dtype=torch.long)
    if not torch.equal(assignment, expected):
        raise AssertionError(f"decoded assignment mismatch: expected {expected}, got {assignment}")


def test_harl_discrete_policy_and_buffer(adapter_module) -> None:
    from harl.common.buffers.on_policy_actor_buffer import OnPolicyActorBuffer
    from harl.models.policy_models.stochastic_policy import StochasticPolicy

    obs_space = gymnasium.spaces.Box(-np.inf, np.inf, shape=(5,), dtype=np.float32)
    act_space = adapter_module.make_assignment_discrete_action_space(num_viewpoints=12)

    policy = StochasticPolicy(_make_policy_args(), obs_space, act_space, device=torch.device("cpu"))
    assert policy.act.action_type == "Discrete"
    assert policy.act.action_out.__class__.__name__ == "Categorical"

    obs = torch.randn(2, 5)
    rnn_states = torch.zeros(2, 1, 16)
    masks = torch.ones(2, 1)
    available_actions = torch.zeros(2, 13)
    available_actions[:, 3] = 1.0

    actions, action_log_probs, _ = policy(obs, rnn_states, masks, available_actions=available_actions)
    assert tuple(actions.shape) == (2, 1)
    assert tuple(action_log_probs.shape) == (2, 1)
    assert torch.all(actions == 3)

    buffer_args = {
        "episode_length": 4,
        "n_rollout_threads": 2,
        "hidden_sizes": [16],
        "recurrent_n": 1,
    }
    actor_buffer = OnPolicyActorBuffer(buffer_args, obs_space, act_space, device="cpu")
    assert tuple(actor_buffer.actions.shape) == (4, 2, 1)
    assert actor_buffer.available_actions is not None
    assert tuple(actor_buffer.available_actions.shape) == (5, 2, 13)


def test_current_shape_zero_blocker(adapter_module) -> None:
    act_space = adapter_module.make_assignment_discrete_action_space(num_viewpoints=12)

    try:
        _ = act_space.shape[0]
    except IndexError:
        return

    raise AssertionError("gymnasium.spaces.Discrete.shape[0] should fail; use scalar action dim helper instead")


def main() -> None:
    adapter_module = _load_assignment_harl_adapter()
    test_adapter_shapes(adapter_module)
    test_harl_discrete_policy_and_buffer(adapter_module)
    test_current_shape_zero_blocker(adapter_module)
    print("[OK] assignment HARL Discrete shape smoke passed")


if __name__ == "__main__":
    main()
