# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Gym registration entry point for the heterogeneous mobile-manipulator scanning task.

Importing this package registers `Isaac-Scan-Mobile-Manipulator-Direct-v0` so Isaac Lab and HARL scripts can create the
environment from a task id. The environment implementation itself lives in `scan_mobile_manipulator_env.py`.
"""

import gymnasium as gym

from . import agents
from .scan_mobile_manipulator_env import ScanMobileManipulatorEnv, ScanMobileManipulatorEnvCfg

# Register the DirectMARLEnv task and attach the HARL/HAPPO yaml entry point. `disable_env_checker=True` follows Isaac
# Lab direct-task conventions because the environment uses Isaac's vectorized MARL API rather than plain Gym spaces.
gym.register(
    id="Isaac-Scan-Mobile-Manipulator-Direct-v0",
    entry_point="isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": ScanMobileManipulatorEnvCfg,
        "harl_happo_cfg_entry_point": f"{agents.__name__}:harl_happo_cfg.yaml",
    },
)
