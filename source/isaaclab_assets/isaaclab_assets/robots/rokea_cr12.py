# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

"""Approved fixed-lift CR12 configuration for the bounded joint-drive experiment.

Import after AppLauncher. These are simulation debugging parameters, not
manufacturer-identified dynamics or hardware ratings. The complete expected
mass properties are independently checked from the validated derived URDF.
"""

import math
from pathlib import Path

import isaaclab.sim as sim_utils
from isaaclab.actuators import ImplicitActuatorCfg
from isaaclab.assets import ArticulationCfg

ASSET_MODEL_ID = "cr12_fixed_lift0_visual_box_v1"
EXPECTED_BODY_NAMES = ("agv", "link_1", "link_2", "link_3", "link_4", "link_5", "link_6")
JOINT_NAMES = tuple(f"joint_{index}" for index in range(1, 7))
EXPECTED_TOTAL_MASS_KG = 82.860365324
STIFFNESS = (200.0, 4000.0, 2000.0, 200.0, 1000.0, 150.0)
DAMPING = (20.0, 550.0, 166.0, 12.0, 37.0, 7.0)
EFFORT_LIMITS = (20.0, 60.0, 30.0, 10.0, 10.0, 5.0)
VELOCITY_LIMIT = 0.2
PHYSICS_DT = 1.0 / 120.0
PHYSICS_STEPS = 720
CONTACT_OFFSET = 0.002
REST_OFFSET = 0.0


def make_cr12_cfg(
    usd_path: str | Path, prim_path: str = "/World/CR12", *, stiffness=None, damping=None
) -> ArticulationCfg:
    """Load an explicit, previously inspected USD; never convert or edit it."""
    path = Path(usd_path).expanduser().resolve(strict=True)
    if not path.is_file() or path.suffix.lower() != ".usd":
        raise ValueError(f"Expected an existing explicit CR12 USD file: {path}")
    # Explicit experiment selection only; the accepted baseline remains the default.
    selected_k = tuple(STIFFNESS if stiffness is None else stiffness)
    selected_d = tuple(DAMPING if damping is None else damping)
    if any(len(values) != 6 or any(not math.isfinite(value) or value <= 0 for value in values)
           for values in (selected_k, selected_d)):
        raise ValueError("CR12 requires six finite positive stiffness and damping values")
    return ArticulationCfg(
        prim_path=prim_path,
        spawn=sim_utils.UsdFileCfg(
            usd_path=str(path),
            activate_contact_sensors=True,
            mass_props=None,
            rigid_props=sim_utils.RigidBodyPropertiesCfg(disable_gravity=False, kinematic_enabled=False),
            collision_props=sim_utils.CollisionPropertiesCfg(
                collision_enabled=True, contact_offset=CONTACT_OFFSET, rest_offset=REST_OFFSET
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=True,
                fix_root_link=None,
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=2,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.053),
            rot=(1.0, 0.0, 0.0, 0.0),
            joint_pos={name: 0.0 for name in JOINT_NAMES},
            joint_vel={name: 0.0 for name in JOINT_NAMES},
        ),
        soft_joint_pos_limit_factor=1.0,
        actuators={
            "arm": ImplicitActuatorCfg(
                joint_names_expr=list(JOINT_NAMES),
                stiffness=dict(zip(JOINT_NAMES, selected_k)),
                damping=dict(zip(JOINT_NAMES, selected_d)),
                effort_limit_sim=dict(zip(JOINT_NAMES, EFFORT_LIMITS)),
                velocity_limit_sim=VELOCITY_LIMIT,
                # Preserve imported defaults; no invented friction or rotor inertia.
                armature=None,
                friction=None,
            )
        },
    )
