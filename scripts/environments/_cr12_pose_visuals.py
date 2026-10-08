"""Optional scanner-pose display; importing this module never imports Isaac/Kit.

Call only after App creation. These markers consume actual/target world poses;
they do not read robot state, advance time, or decide whether a pose is reached.
"""

from __future__ import annotations

import numpy as np


_PRIM_PATH = "/CR12PoseDebug"
_ACTUAL_LENGTH = 0.20
_TARGET_LENGTH = 0.14
_ACTUAL_RADIUS = 0.0035
_TARGET_RADIUS = 0.0025
_LINE_RADIUS = 0.0018
_ACTUAL_ORIGIN_RADIUS = 0.006
_TARGET_ORIGIN_RADIUS = 0.008


def _pose(value):
    """Copy a finite world transform without retaining a caller-owned buffer."""
    pose = np.array(value, dtype=np.float64, copy=True)
    if pose.shape != (4, 4) or not np.isfinite(pose).all():
        raise ValueError("Scanner display pose must be a finite 4x4 matrix")
    rotation = pose[:3, :3]
    if (not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-7, rtol=0)
            or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-5, rtol=0)
            or not np.isclose(np.linalg.det(rotation), 1.0, atol=1e-5, rtol=0)):
        raise ValueError("Scanner display pose must be a rigid transform")
    return pose


def _z_to_direction(direction):
    """WXYZ rotation taking the cylinder's local +Z to a world direction."""
    direction = np.asarray(direction, dtype=np.float64)
    direction = direction / np.linalg.norm(direction)
    quaternion = np.array([1.0 + direction[2], -direction[1], direction[0], 0.0])
    norm = np.linalg.norm(quaternion)
    if norm < 1e-12:
        return np.array([0.0, 1.0, 0.0, 0.0])
    return quaternion / norm


def _marker_arrays(actual, target):
    """Six positive axes, one origin line, then the two true origin spheres."""
    actual, target = _pose(actual), _pose(target)
    positions, orientations, scales = [], [], []
    for pose, length, radius in ((actual, _ACTUAL_LENGTH, _ACTUAL_RADIUS),
                                 (target, _TARGET_LENGTH, _TARGET_RADIUS)):
        for axis in range(3):
            direction = pose[:3, axis]
            positions.append(pose[:3, 3] + 0.5 * length * direction)
            orientations.append(_z_to_direction(direction))
            scales.append([radius, radius, length])
    gap = target[:3, 3] - actual[:3, 3]
    length = float(np.linalg.norm(gap))
    positions.append(0.5 * (actual[:3, 3] + target[:3, 3]))
    orientations.append(_z_to_direction(gap) if length > 1e-12 else [1.0, 0.0, 0.0, 0.0])
    scales.append([_LINE_RADIUS, _LINE_RADIUS, length] if length > 1e-12 else [0.0, 0.0, 0.0])
    for pose, radius in ((actual, _ACTUAL_ORIGIN_RADIUS), (target, _TARGET_ORIGIN_RADIUS)):
        positions.append(pose[:3, 3].copy())
        orientations.append([1.0, 0.0, 0.0, 0.0])
        scales.append([radius, radius, radius])
    return {"translations": np.asarray(positions, dtype=np.float32),
            "orientations": np.asarray(orientations, dtype=np.float32),
            "scales": np.asarray(scales, dtype=np.float32),
            "marker_indices": list(range(9))}


def spectator_view(initial_scanner_pose, preset="overall", target_scanner_pose=None):
    """Return fixed world-space eye/target values; never follow the moving wrist."""
    origin = _pose(initial_scanner_pose)[:3, 3]
    if preset == "overall":
        target = np.array([origin[0], origin[1], 0.5 * origin[2]])
        eye = target + np.array([4.0, -4.0, 2.0])
    elif preset == "wrist":
        target = origin.copy()
        eye = target + np.array([0.50, -0.65, 0.35])
    elif preset in ("wrist-oblique", "arm-oblique"):
        if target_scanner_pose is None:
            raise ValueError("Oblique views require the frozen target scanner pose")
        midpoint = 0.5 * (origin + _pose(target_scanner_pose)[:3, 3])
        if preset == "wrist-oblique":
            target = midpoint
            # The previous viewing direction was close to scanner -X at zero.
            # This oblique direction retains projected length on all three axes.
            eye = target + np.array([0.55, -0.10, 0.42])
        else:
            target = midpoint + np.array([0.0, 0.0, -0.75])
            eye = target + np.array([2.2, -2.6, 1.35])
    else:
        raise ValueError("view preset must be overall, wrist, wrist-oblique or arm-oblique")
    return {"preset": preset, "eye": eye.tolist(), "target": target.tolist()}


def set_spectator_view(initial_scanner_pose, preset="overall", target_scanner_pose=None):
    """Set the existing GUI perspective viewport, independently of markers.

    No camera sensor, render product, physics step, or render call is created.
    The caller may record a display error separately from numerical acceptance.
    """
    view = spectator_view(initial_scanner_pose, preset, target_scanner_pose)
    import omni.kit.commands
    from isaacsim.core.utils.viewports import set_camera_view
    from omni.kit.viewport.utility import get_active_viewport

    viewport = get_active_viewport()
    if viewport is None or not viewport.stage.GetPrimAtPath("/OmniverseKit_Persp").IsValid():
        raise RuntimeError("An existing GUI perspective viewport is required for pose display")
    omni.kit.commands.execute("SetViewportCamera", camera_path="/OmniverseKit_Persp", viewport_api=viewport)
    set_camera_view(np.asarray(view["eye"]), np.asarray(view["target"]),
                    camera_prim_path="/OmniverseKit_Persp", viewport_api=viewport)
    return view


class PoseDebugVisuals:
    """Actual RGB axes (20 cm), lighter target axes (14 cm), magenta origin line.

    White (6 mm radius) and yellow (8 mm) spheres mark the true origins. No
    reference frame or artificial displacement separates overlapping poses.

    All primitives are isolated under a stage-root PointInstancer. They are
    display-only cylinders and spheres, not scanner/body transforms or colliders.
    """

    def __init__(self, stage, initial_scanner_pose, preset="overall", target_scanner_pose=None):
        initial = _pose(initial_scanner_pose)
        target = initial.copy() if target_scanner_pose is None else _pose(target_scanner_pose)
        from isaacsim.core.utils.stage import get_current_stage
        from isaaclab.markers import VisualizationMarkers, VisualizationMarkersCfg
        from isaaclab.sim import CylinderCfg, PreviewSurfaceCfg, SphereCfg
        from pxr import UsdGeom, UsdPhysics

        if stage is None or stage != get_current_stage():
            raise ValueError("Pose markers require the current App stage")
        if stage.GetPrimAtPath(_PRIM_PATH).IsValid():
            raise ValueError(f"Refusing to replace existing display prim {_PRIM_PATH}")
        view = set_spectator_view(initial, preset, target_scanner_pose)
        colors = ((1.0, 0.05, 0.05), (0.05, 1.0, 0.05), (0.05, 0.25, 1.0),
                  (1.0, 0.25, 0.25), (0.25, 1.0, 0.25), (0.25, 0.45, 1.0), (1.0, 0.0, 1.0))
        names = ("actual_x", "actual_y", "actual_z", "target_x", "target_y", "target_z", "origin_gap")
        markers = {
            name: CylinderCfg(radius=1.0, height=1.0, axis="Z", rigid_props=None,
                              mass_props=None, collision_props=None, physics_material=None,
                              activate_contact_sensors=False,
                              visual_material=PreviewSurfaceCfg(diffuse_color=color))
            for name, color in zip(names, colors)
        }
        for name, color in (("actual_origin", (1.0, 1.0, 1.0)), ("target_origin", (1.0, 0.85, 0.0))):
            markers[name] = SphereCfg(radius=1.0, rigid_props=None, mass_props=None, collision_props=None,
                                      physics_material=None, activate_contact_sensors=False,
                                      visual_material=PreviewSurfaceCfg(diffuse_color=color))
        self._markers = VisualizationMarkers(VisualizationMarkersCfg(prim_path=_PRIM_PATH, markers=markers))
        pending = [stage.GetPrimAtPath(self._markers.prim_path)]
        while pending:
            prim = pending.pop()
            if (any(prim.HasAPI(schema) for schema in
                    (UsdPhysics.RigidBodyAPI, UsdPhysics.CollisionAPI, UsdPhysics.MassAPI, UsdPhysics.ArticulationRootAPI))
                    or prim.IsA(UsdPhysics.Joint)):
                raise RuntimeError(f"Unexpected physical schema on pose marker {prim.GetPath()}")
            pending.extend(prim.GetChildren())
        self.update(initial, target)
        instancer = UsdGeom.PointInstancer(stage.GetPrimAtPath(self._markers.prim_path))
        positions = instancer.GetPositionsAttr().Get()
        indices = instancer.GetProtoIndicesAttr().Get()
        prototypes = instancer.GetPrototypesRel().GetTargets()
        visibility = instancer.GetVisibilityAttr().Get()
        readback = {"instance_count": 0 if positions is None else len(positions),
                    "prototype_count": len(prototypes),
                    "instance_indices": [] if indices is None else list(indices),
                    "visibility_attr": str(visibility),
                    "visible": self._markers.is_visible(),
                    "physical_schemas_present": False}
        if (readback["instance_count"] != 9 or readback["prototype_count"] != 9
                or readback["instance_indices"] != list(range(9)) or not readback["visible"]):
            raise RuntimeError(f"Incomplete or hidden scanner-pose marker display: {readback}")
        self.metadata = {"prim_path": self._markers.prim_path, "view": view,
                         "actual_axis_length_m": _ACTUAL_LENGTH, "target_axis_length_m": _TARGET_LENGTH,
                         "actual_axis_radius_m": _ACTUAL_RADIUS, "target_axis_radius_m": _TARGET_RADIUS,
                         "origin_line_radius_m": _LINE_RADIUS,
                         "actual_origin_radius_m": _ACTUAL_ORIGIN_RADIUS,
                         "target_origin_radius_m": _TARGET_ORIGIN_RADIUS,
                         "prototype_names": list(markers), "marker_count": 9,
                         "reference_frame_shown": False, "origin_positions_are_true": True,
                         "legend": "actual RGB long/thick + white origin; target lighter RGB short/thin + yellow origin; gap magenta",
                         "depth_policy": "normal viewport depth; no global renderer override",
                         "setup_readback": readback,
                         "physical_schemas_present": False}

    def update(self, actual_4x4, target_4x4):
        """Update display from supplied snapshots; no robot or clock access."""
        self._markers.visualize(**_marker_arrays(actual_4x4, target_4x4))

    def set_visibility(self, visible):
        """Hide/show only this display group."""
        self._markers.set_visibility(bool(visible))
