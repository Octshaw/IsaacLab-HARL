"""CPU mathematics and bounded checks for the approved single CR12 scanner target.

No simulator or controller is imported here. The runtime supplies measured poses,
native Jacobians and the absolute q_IK returned by the installed DiffIK controller.
Transforms T_AB express frame B in A; quaternions are WXYZ.
"""

import math
import xml.etree.ElementTree as ET
from dataclasses import dataclass

import numpy as np

# Keep original standalone-file imports dependency-free. The new fixed profile
# is loaded only when explicitly selected; old formal/manual callers need none.
_SHARED_PROFILE_NAME = 'shared_m2n1'


def _shared_config():
    import _cr12_shared_task_profile
    return _cr12_shared_task_profile


DT = 1.0 / 120.0
REFERENCE_SECONDS = 4.0
MAX_STEPS = 960
MAX_SECONDS = 8.0
POSITION_TOLERANCE = 0.002
ANGLE_TOLERANCE = math.radians(0.25)
BODY_NAMES = ("agv", *(f"link_{i}" for i in range(1, 7)))
JOINT_NAMES = tuple(f"joint_{i}" for i in range(1, 7))
JOINT_LIMITS = np.array([[-3.0543, 3.0543], [-2.9671, 2.9671], *[[-3.0543, 3.0543]] * 4])
TARGET_OFFSET = np.array([0.0106981457149994, 0.0, -0.000155046722254002])
_ORIGINS = ((.105, 0, 1.062), (0, 0, .35), (0, 0, .76), (0, 0, .54), (0, -.15, 0), (0, 0, .123))
_AXES = ((0, 0, 1), (0, 1, 0), (0, 1, 0), (0, 0, 1), (0, 1, 0), (0, 0, 1))


class PoseCheckError(RuntimeError):
    def __init__(self, category, message, **details):
        super().__init__(message)
        self.category = category
        self.details = details


MANUAL_WITNESS_DEG = (0.0, 3.0, -4.5, 0.0, 4.5, 0.0)
MANUAL_WITNESS_BETA = 1.0  # Frozen before the first App after the 101-sample CPU check.


@dataclass(frozen=True)
class MotionProfile:
    """Fixed, explicitly selected profiles; no caller-supplied budgets or gains."""
    name: str = "formal"

    def __post_init__(self):
        if self.name not in ("formal", "manual_visible_local_v1", _SHARED_PROFILE_NAME):
            raise PoseCheckError("SETUP", "Unknown fixed motion profile", name=self.name)

    @property
    def manual_visual_only(self):
        return self.name == "manual_visible_local_v1"

    @property
    def reference_seconds(self):
        if self.name == _SHARED_PROFILE_NAME:
            return _shared_config().REFERENCE_SECONDS
        return 6.0 if self.manual_visual_only else REFERENCE_SECONDS

    @property
    def max_seconds(self):
        if self.name == _SHARED_PROFILE_NAME:
            return _shared_config().MAX_SECONDS
        return 10.0 if self.manual_visual_only else MAX_SECONDS

    @property
    def max_steps(self):
        if self.name == _SHARED_PROFILE_NAME:
            return _shared_config().MAX_STEPS
        return 1200 if self.manual_visual_only else MAX_STEPS

    @property
    def trust_degrees(self):
        return _shared_config().TRUST_DEG if self.name == _SHARED_PROFILE_NAME else (5.,)*6

    @property
    def witness_deg(self):
        return MANUAL_WITNESS_DEG if self.manual_visual_only else None

    @property
    def beta(self):
        return MANUAL_WITNESS_BETA if self.manual_visual_only else None


FORMAL_PROFILE = MotionProfile()
MANUAL_VISIBLE_LOCAL_V1 = MotionProfile("manual_visible_local_v1")
SHARED_M2N1 = MotionProfile(_SHARED_PROFILE_NAME)


def select_motion_profile(name="formal"):
    if name == "formal":
        return FORMAL_PROFILE
    if name == "manual_visible_local_v1":
        return MANUAL_VISIBLE_LOCAL_V1
    if name == _SHARED_PROFILE_NAME:
        return SHARED_M2N1
    raise PoseCheckError("SETUP", "Unknown fixed motion profile", name=name)


def _array(value, shape, label, category="COMMAND_REJECTED"):
    try:
        result = np.array(value, dtype=np.float64, copy=True)
    except (TypeError, ValueError) as exc:
        raise PoseCheckError(category, f"Invalid {label}") from exc
    if result.shape != shape or not np.isfinite(result).all():
        raise PoseCheckError(category, f"Invalid shape or non-finite {label}", shape=list(result.shape))
    return result


def _time(value):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise PoseCheckError("PHYSICS_GUARD", "Invalid controlled time") from exc
    if not math.isfinite(value) or value < 0:
        raise PoseCheckError("PHYSICS_GUARD", "Invalid controlled time", time=value)
    return value


def skew(vector):
    x, y, z = _array(vector, (3,), "skew vector")
    return np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])


def rotation_axis_angle(axis, angle):
    axis = _array(axis, (3,), "rotation axis")
    angle = float(angle)
    norm = float(np.linalg.norm(axis))
    if not math.isfinite(angle) or norm == 0:
        raise PoseCheckError("COMMAND_REJECTED", "Invalid axis-angle")
    cross = skew(axis / norm)
    return np.eye(3) + math.sin(angle) * cross + (1.0 - math.cos(angle)) * (cross @ cross)


def _transform(value, label="transform"):
    result = _array(value, (4, 4), label)
    if (not np.allclose(result[3], [0, 0, 0, 1], atol=1e-8, rtol=0)
            or not np.allclose(result[:3, :3].T @ result[:3, :3], np.eye(3), atol=1e-6, rtol=0)
            or abs(float(np.linalg.det(result[:3, :3])) - 1.0) > 1e-6):
        raise PoseCheckError("COMMAND_REJECTED", f"Invalid rigid {label}")
    return result


def pose_from_wxyz(position, quaternion):
    position = _array(position, (3,), "position")
    q = _array(quaternion, (4,), "WXYZ quaternion")
    norm = float(np.linalg.norm(q))
    if norm == 0 or abs(norm - 1.0) > 1e-3:
        raise PoseCheckError("COMMAND_REJECTED", "Quaternion norm outside approved tolerance", norm=norm)
    w, x, y, z = q / norm
    result = np.eye(4)
    result[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    result[:3, 3] = position
    return result


def pose_to_wxyz(transform):
    """Return (position, normalized canonical WXYZ quaternion), as independent arrays."""
    value = _transform(transform)
    r = value[:3, :3]
    trace = float(np.trace(r))
    if trace > 0:
        scale = 2.0 * math.sqrt(trace + 1.0)
        q = np.array([scale/4, (r[2, 1]-r[1, 2])/scale, (r[0, 2]-r[2, 0])/scale,
                      (r[1, 0]-r[0, 1])/scale])
    else:
        i = int(np.argmax(np.diag(r)))
        j, k = (i + 1) % 3, (i + 2) % 3
        scale = 2.0 * math.sqrt(max(0.0, 1.0 + r[i, i] - r[j, j] - r[k, k]))
        q = np.zeros(4)
        q[0] = (r[k, j] - r[j, k]) / scale
        q[i+1] = scale / 4
        q[j+1] = (r[j, i] + r[i, j]) / scale
        q[k+1] = (r[k, i] + r[i, k]) / scale
    q /= np.linalg.norm(q)
    if q[0] < 0:
        q = -q
    return value[:3, 3].copy(), q


def inverse_pose(transform):
    value = _transform(transform)
    result = np.eye(4)
    result[:3, :3] = value[:3, :3].T
    result[:3, 3] = -result[:3, :3] @ value[:3, 3]
    return result


T_ES = np.eye(4)
T_ES[:3, :3] = rotation_axis_angle([0, 0, 1], 3 * math.pi / 4)
for _constant in (T_ES, JOINT_LIMITS, TARGET_OFFSET):
    _constant.setflags(write=False)


def scanner_from_ee(transform_we):
    return _transform(transform_we) @ T_ES


def ee_from_scanner(transform_ws):
    return _transform(transform_ws) @ inverse_pose(T_ES)


def in_root(transform_wr, transform_we):
    return inverse_pose(transform_wr) @ _transform(transform_we)


def pose_error(actual, target):
    """Return Euclidean position error (m), shortest orientation error (rad)."""
    actual, target = _transform(actual), _transform(target)
    relative = np.eye(4)
    relative[:3, :3] = target[:3, :3] @ actual[:3, :3].T
    _, quaternion = pose_to_wxyz(relative)
    angle = 2.0 * math.atan2(float(np.linalg.norm(quaternion[1:])), abs(float(quaternion[0])))
    return float(np.linalg.norm(target[:3, 3] - actual[:3, 3])), angle


class FrozenPoseTarget:
    """The one approved target, frozen from a single measured initial scanner pose."""
    def __init__(self, initial):
        self._initial = _transform(initial)
        self._target = self._initial.copy()
        self._target[:3, 3] += TARGET_OFFSET
        self._target[:3, :3] = rotation_axis_angle([0, 1, 0], math.radians(1)) @ self._initial[:3, :3]
        self._initial.setflags(write=False)
        self._target.setflags(write=False)

    @property
    def initial(self):
        return self._initial.copy()

    @property
    def target(self):
        return self._target.copy()

    def reference(self, time):
        u = min(_time(time) / REFERENCE_SECONDS, 1.0)
        h = 10*u**3 - 15*u**4 + 6*u**5
        result = self._initial.copy()
        result[:3, 3] += h * TARGET_OFFSET
        # Exactly the shortest geodesic for this frozen world-Y +1-degree target.
        result[:3, :3] = rotation_axis_angle([0, 1, 0], h * math.radians(1)) @ self._initial[:3, :3]
        return result


class FrozenManualPoseTarget:
    """Manual target from actual root * fixed witness FK * T_ES, frozen once.

    The witness defines a pose only. It is never returned as a joint command.
    Reference orientation follows the generic shortest geodesic from the measured
    initial scanner rotation, including a nonidentity actual root rotation.
    """
    def __init__(self, initial_scanner, actual_root, model):
        self._initial = _transform(initial_scanner)
        self._root = _transform(actual_root)
        self._witness_q = np.radians(MANUAL_WITNESS_DEG) * MANUAL_WITNESS_BETA
        self._target = self._root @ model.forward(self._witness_q, np.eye(4))["link_6"] @ T_ES
        self._target = _transform(self._target)
        relative = np.eye(4)
        relative[:3, :3] = self._target[:3, :3] @ self._initial[:3, :3].T
        _, quaternion = pose_to_wxyz(relative)
        sine = float(np.linalg.norm(quaternion[1:]))
        self._angle = 2.0 * math.atan2(sine, max(0.0, float(quaternion[0])))
        self._axis = quaternion[1:] / sine if sine > 1e-15 else np.array([1.0, 0.0, 0.0])
        for value in (self._initial, self._root, self._witness_q, self._target, self._axis):
            value.setflags(write=False)

    @property
    def initial(self):
        return self._initial.copy()

    @property
    def target(self):
        return self._target.copy()

    @property
    def witness_q(self):
        return self._witness_q.copy()

    def reference(self, time):
        u = min(_time(time) / MANUAL_VISIBLE_LOCAL_V1.reference_seconds, 1.0)
        h = 10*u**3 - 15*u**4 + 6*u**5
        result = self._initial.copy()
        result[:3, 3] += h * (self._target[:3, 3] - self._initial[:3, 3])
        result[:3, :3] = rotation_axis_angle(self._axis, h * self._angle) @ self._initial[:3, :3]
        return result


def _indices(actual, expected, label):
    actual = list(actual)
    if len(actual) != len(expected) or len(set(actual)) != len(actual) or set(actual) != set(expected):
        raise PoseCheckError("SETUP_JACOBIAN_SEMANTICS", f"Unexpected {label}", actual=actual)
    return [actual.index(name) for name in expected]


def check_path_tube(q_actual, q_park, q_goal):
    """Require one common geometric s for all axes, never time-reference progress."""
    q = _array(q_actual, (6,), "actual tube q", "PATH_TUBE")
    park = _array(q_park, (6,), "park q", "PATH_TUBE")
    goal = _array(q_goal, (6,), "goal q", "PATH_TUBE")
    tolerance = math.radians(_shared_config().TUBE_DEG)
    lower, upper = 0.0, 1.0
    delta = goal - park
    for index in range(6):
        if delta[index] == 0.0:
            if abs(q[index] - park[index]) > tolerance:
                raise PoseCheckError("PATH_TUBE", "Zero-change axis leaves the actual path tube", joint=index+1)
        else:
            ends = ((q[index]-park[index]-tolerance)/delta[index],
                    (q[index]-park[index]+tolerance)/delta[index])
            lower, upper = max(lower, min(ends)), min(upper, max(ends))
    if lower > upper:
        raise PoseCheckError("PATH_TUBE", "No single geometric progress satisfies all six actual axes",
                             interval=[lower, upper], q_actual=q.tolist())
    progress = (lower + upper) * .5
    residual = float(np.max(np.abs(q-(park+progress*delta))))
    return {"s": progress, "s_interval": [lower, upper], "maximum_residual_rad": residual,
            "tolerance_rad": tolerance, "kind": "common_s_path_tube", "passed": True}


def check_fixed_neighborhood(q_actual, q_park):
    q = _array(q_actual, (6,), "actual fixed-neighborhood q", "PARK_NEIGHBORHOOD")
    park = _array(q_park, (6,), "fixed park q", "PARK_NEIGHBORHOOD")
    error = float(np.max(np.abs(q-park)))
    tolerance = math.radians(_shared_config().TUBE_DEG)
    if error > tolerance:
        raise PoseCheckError("PARK_NEIGHBORHOOD", "Actual joint leaves the fixed park/clear neighborhood",
                             maximum_error_rad=error, tolerance_rad=tolerance)
    return {"maximum_residual_rad": error, "tolerance_rad": tolerance,
            "kind": "fixed_park_neighborhood", "passed": True}


def resolve_mapping(body_names, joint_names, is_fixed_base):
    body_ids = _indices(body_names, BODY_NAMES, "body names")
    joint_ids = _indices(joint_names, JOINT_NAMES, "joint names")
    if not is_fixed_base or body_ids[0] != 0:
        raise PoseCheckError("SETUP_JACOBIAN_SEMANTICS", "Expected fixed agv root at body index zero")
    return {"body_ids": body_ids, "joint_ids": joint_ids, "ee_body_index": body_ids[-1],
            "jacobian_row": body_ids[-1] - 1, "body_names": list(body_names), "joint_names": list(joint_names)}


def extract_jacobian(raw, mapping):
    """Copy native float32 (1,6,6,6) data; device is checked by the runtime before CPU transfer."""
    raw = np.asarray(raw)
    if raw.shape != (1, 6, 6, 6) or raw.dtype != np.float32 or not np.isfinite(raw).all():
        raise PoseCheckError("SETUP_JACOBIAN_SEMANTICS", "Native Jacobian shape/dtype/finite check failed",
                             shape=list(raw.shape), dtype=str(raw.dtype))
    return raw[0, mapping["jacobian_row"]][:, mapping["joint_ids"]].astype(np.float64, copy=True)


def select_jacobian_adapter(native, analytic_e, analytic_c):
    arrays = [_array(v, (6, 6), "Jacobian", "SETUP_JACOBIAN_SEMANTICS")
              for v in (native, analytic_e, analytic_c)]
    errors = {}
    matches = []
    for name, analytic in zip(("actor", "com"), arrays[1:]):
        delta = np.abs(arrays[0] - analytic)
        errors[name] = {"linear_max_error": float(delta[:3].max()), "angular_max_error": float(delta[3:].max())}
        if errors[name]["linear_max_error"] <= 1e-4 and errors[name]["angular_max_error"] <= 1e-4:
            matches.append(name)
    if len(matches) != 1:
        raise PoseCheckError("SETUP_JACOBIAN_SEMANTICS", "Jacobian must match exactly one declared reference point",
                             matches=matches, candidate_errors=errors)
    return {"reference_point": matches[0], "candidate_errors": errors,
            "linear_tolerance": 1e-4, "angular_tolerance": 1e-4}


def adapt_jacobian(native, reference_point, transform_wr, transform_we, com_body):
    result = _array(native, (6, 6), "Jacobian", "SETUP_JACOBIAN_SEMANTICS")
    root, ee = _transform(transform_wr), _transform(transform_we)
    if reference_point == "com":
        offset_world = ee[:3, :3] @ _array(com_body, (3,), "COM offset")
        result[:3] += skew(offset_world) @ result[3:]
    elif reference_point != "actor":
        raise PoseCheckError("SETUP_JACOBIAN_SEMANTICS", "Unknown frozen Jacobian adapter")
    result[:3] = root[:3, :3].T @ result[:3]
    result[3:] = root[:3, :3].T @ result[3:]
    return result


class KinematicModel:
    """FK of the accepted six-joint chain only; no IK or motion planning."""
    def __init__(self, joints):
        order = _indices([j["name"] for j in joints], JOINT_NAMES, "derived joints")
        self.origins = []
        self.axes = []
        for i, index in enumerate(order):
            joint = joints[index]
            origin = _array(joint["origin_xyz"], (3,), "joint origin", "SETUP")
            rpy = _array(joint["origin_rpy"], (3,), "joint RPY", "SETUP")
            axis = _array(joint["axis"], (3,), "joint axis", "SETUP")
            if (joint["parent"] != BODY_NAMES[i] or joint["child"] != BODY_NAMES[i+1]
                    or not np.allclose(origin, _ORIGINS[i], atol=1e-10, rtol=0)
                    or not np.allclose(rpy, 0, atol=1e-10, rtol=0)
                    or not np.allclose(axis, _AXES[i], atol=1e-10, rtol=0)):
                raise PoseCheckError("SETUP", "Derived kinematics differ from accepted fixed-lift0 chain", joint=JOINT_NAMES[i])
            self.origins.append(origin)
            self.axes.append(axis)

    @classmethod
    def from_derived_urdf(cls, path):
        document = ET.parse(path).getroot()
        _indices([v.get("name") for v in document.findall("link")], BODY_NAMES, "derived links")
        joints = []
        for joint in document.findall("joint"):
            if joint.get("type") != "revolute":
                raise PoseCheckError("SETUP", "Unexpected joint type in derived six-axis URDF")
            origin = joint.find("origin")
            joints.append({"name": joint.get("name"), "parent": joint.find("parent").get("link"),
                           "child": joint.find("child").get("link"),
                           "origin_xyz": list(map(float, origin.get("xyz").split())),
                           "origin_rpy": list(map(float, origin.get("rpy").split())),
                           "axis": list(map(float, joint.find("axis").get("xyz").split()))})
        return cls(joints)

    def _chain(self, q, transform_wr):
        q = _array(q, (6,), "FK q")
        current = _transform(transform_wr)
        poses, origins, axes = {"agv": current.copy()}, [], []
        for i in range(6):
            current = current.copy()
            current[:3, 3] += current[:3, :3] @ self.origins[i]
            origins.append(current[:3, 3].copy())
            axes.append(current[:3, :3] @ self.axes[i])
            current[:3, :3] = current[:3, :3] @ rotation_axis_angle(self.axes[i], q[i])
            poses[BODY_NAMES[i+1]] = current.copy()
        return poses, origins, axes

    def forward(self, q, transform_wr):
        return self._chain(q, transform_wr)[0]

    def jacobians(self, q, transform_wr, com_body):
        poses, origins, axes = self._chain(q, transform_wr)
        ee = poses["link_6"]
        com = ee[:3, 3] + ee[:3, :3] @ _array(com_body, (3,), "COM offset")
        output = []
        for point in (ee[:3, 3], com):
            output.append(np.column_stack([np.r_[np.cross(axis, point-origin), axis]
                                           for origin, axis in zip(origins, axes)]))
        return tuple(output)

    def sanity_samples(self, q_actual, q_proposal, transform_wr):
        """Two FK samples only: this is NOT a swept-volume collision proof."""
        actual = _array(q_actual, (6,), "actual q")
        proposed = _array(q_proposal, (6,), "proposed q")
        return [("midpoint", self.forward((actual + proposed) * .5, transform_wr)),
                ("endpoint", self.forward(proposed, transform_wr))]


class CommandProposal:
    def __init__(self, owner, generation, q, dq, raw_delta):
        self._owner = owner
        self.generation = generation
        self.q = q.copy()
        self.dq = dq.copy()
        self.raw_delta = raw_delta.copy()
        for value in (self.q, self.dq, self.raw_delta):
            value.setflags(write=False)


class CommandIntegrator:
    def __init__(self, initial_q, limits=JOINT_LIMITS, dt=DT, *, profile=FORMAL_PROFILE):
        if not isinstance(profile, MotionProfile):
            raise PoseCheckError("SETUP", "Integrator requires a fixed MotionProfile")
        self.profile = profile
        self.trust_radians = np.radians(profile.trust_degrees)
        self.trust_radians.setflags(write=False)
        if not math.isfinite(float(dt)) or abs(float(dt) - DT) > 1e-12:
            raise PoseCheckError("SETUP", "The approved command period is fixed at 1/120 s")
        self.dt = DT
        self.initial_q = _array(initial_q, (6,), "initial q", "SETUP")
        self.limits = _array(limits, (6, 2), "joint limits", "SETUP")
        if not np.allclose(self.limits, JOINT_LIMITS, atol=1e-6, rtol=0):
            raise PoseCheckError("SETUP", "Joint limit readback differs from approved limits")
        self.initial_q.setflags(write=False)
        self.limits.setflags(write=False)
        self._previous = self.initial_q.astype(np.float32)
        self.generation = 0
        self._check_actual(self.initial_q, np.zeros(6))

    @property
    def previous(self):
        return self._previous.copy()

    def _check_actual(self, q, dq):
        if np.any(q < self.limits[:, 0] - 1e-3) or np.any(q > self.limits[:, 1] + 1e-3):
            raise PoseCheckError("PHYSICS_GUARD", "Actual joint exceeds hard limit")
        if float(np.max(np.abs(dq))) > .25:
            raise PoseCheckError("PHYSICS_GUARD", "Actual joint speed exceeds 0.25 rad/s")
        self._trust(q, "actual q")

    def check_actual(self, q, dq):
        self._check_actual(_array(q, (6,), "actual q", "PHYSICS_GUARD"),
                           _array(dq, (6,), "actual dq", "PHYSICS_GUARD"))

    def _trust(self, q, label):
        if np.any(np.abs(q - self.initial_q) > self.trust_radians):
            raise PoseCheckError("COMMAND_REJECTED", f"{label} exceeds the fixed initial-anchor trust region",
                                 trust_degrees=list(self.profile.trust_degrees))

    def _command_limits(self, q, label):
        if np.any(q < self.limits[:, 0] + .02) or np.any(q > self.limits[:, 1] - .02):
            raise PoseCheckError("COMMAND_REJECTED", f"{label} violates hard-limit margin")
        self._trust(q, label)

    def _proposal_limits(self, q, actual):
        self._command_limits(q, "q_proposal")
        if float(np.max(np.abs(q - actual))) > .035:
            raise PoseCheckError("COMMAND_REJECTED", "Accumulated command error exceeds 0.035 rad")
        if float(np.max(np.abs(q - self._previous.astype(np.float64)))) > .00125:
            raise PoseCheckError("COMMAND_REJECTED", "Submitted position step exceeds 0.00125 rad")

    def propose(self, actual_q, actual_dq, q_ik):
        actual = _array(actual_q, (6,), "actual q", "PHYSICS_GUARD")
        dq = _array(actual_dq, (6,), "actual dq", "PHYSICS_GUARD")
        ik = _array(q_ik, (6,), "absolute q_IK")
        self._check_actual(actual, dq)
        self._command_limits(ik, "q_IK")
        delta = ik - actual
        if float(np.max(np.abs(delta))) > .035:
            raise PoseCheckError("COMMAND_REJECTED", "Raw DLS update exceeds 0.035 rad")
        proposal = self._previous.astype(np.float64) + (self.dt * 2.0) * delta
        self._proposal_limits(proposal, actual)
        quantized = proposal.astype(np.float32)
        self._proposal_limits(quantized.astype(np.float64), actual)
        velocity = ((quantized.astype(np.float64) - self._previous.astype(np.float64)) / self.dt).astype(np.float32)
        if not np.isfinite(velocity).all() or float(np.max(np.abs(velocity))) > .15:
            raise PoseCheckError("COMMAND_REJECTED", "Command velocity exceeds 0.15 rad/s or is non-finite")
        return CommandProposal(self, self.generation, quantized, velocity, delta)

    def commit(self, proposal, submitted_q, submitted_dq):
        """Commit only after write_data_to_sim and exact actual-buffer verification."""
        if proposal._owner is not self or proposal.generation != self.generation:
            raise PoseCheckError("COMMAND_REJECTED", "Stale or foreign command proposal")
        q = _array(submitted_q, (6,), "submitted q")
        dq = _array(submitted_dq, (6,), "submitted dq")
        if not np.array_equal(q, proposal.q.astype(np.float64)) or not np.array_equal(dq, proposal.dq.astype(np.float64)):
            raise PoseCheckError("COMMAND_REJECTED", "Submitted targets differ from admitted float32 commands")
        self._previous = proposal.q.copy()
        self.generation += 1


class PoseMonitor:
    """Post-step monitor. A latched internal failure can never become POSE_REACHED."""
    def __init__(self, profile=FORMAL_PROFILE):
        if not isinstance(profile, MotionProfile):
            raise PoseCheckError("SETUP", "PoseMonitor requires a fixed MotionProfile")
        self.profile = profile
        self.last_step = 0
        self.last_sample = {}
        self.failure = None
        self.reached = False
        self.stable_start = None
        self.stable_count = 0
        self.divergent_count = 0
        self.progress_start = None
        self.progress_rho = None

    def _fail(self, category, message, **details):
        if self.failure is None:
            self.failure = PoseCheckError(category, message, **details)
        self.reached = False
        self.stable_start = None
        self.stable_count = 0
        self.last_sample.update(status="FAIL", failure_category=self.failure.category, stable_count=0)
        raise self.failure

    def fail(self, category, message, **details):
        """Latch an external contact/geometry/root/clock failure before any success is recorded."""
        self._fail(category, message, **details)

    def observe(self, step, time, actual_scanner, reference, target, dq, guards_passed=True):
        if self.failure is not None:
            raise self.failure
        self.last_sample = {"step": step, "time": time, "status": "RUNNING"}
        try:
            time = _time(time)
            if (isinstance(step, bool) or not isinstance(step, (int, float, np.integer, np.floating))
                    or not math.isfinite(float(step)) or int(step) != step or step != self.last_step + 1):
                self._fail("PHYSICS_GUARD", "Nonconsecutive controlled step", previous=self.last_step, step=step)
            if abs(time - step * DT) > 1e-5:
                self._fail("PHYSICS_GUARD", "Controlled time differs from counted steps", step=step, time=time)
            self.last_step = int(step)
            if step > self.profile.max_steps or time > self.profile.max_seconds + 1e-6:
                self._fail("TIMEOUT", "Controlled budget exceeded")
            dq = _array(dq, (6,), "post-step native dq", "PHYSICS_GUARD")
            actual_scanner = _array(actual_scanner, (4, 4), "post-step actual scanner pose", "PHYSICS_GUARD")
            position, angle = pose_error(actual_scanner, target)
            ref_position, ref_angle = pose_error(actual_scanner, reference)
            speed = float(np.max(np.abs(dq)))
            rho = max(position / POSITION_TOLERANCE, angle / ANGLE_TOLERANCE)
            self.last_sample.update(position_error_m=position, orientation_error_rad=angle,
                                    reference_position_error_m=ref_position, reference_orientation_error_rad=ref_angle,
                                    max_abs_dq=speed, rho=rho, guards_passed=bool(guards_passed))
            if not guards_passed or speed > .25:
                self._fail("PHYSICS_GUARD", "A required post-step guard failed")
            self.divergent_count = self.divergent_count + 1 if ref_position > .03 or ref_angle > math.radians(5) else 0
            self.last_sample["divergent_count"] = self.divergent_count
            if self.divergent_count >= 12:
                self._fail("DIVERGENCE", "Task-reference error exceeds the fixed bound for 12 steps")
            final_phase = time >= self.profile.reference_seconds - 1e-6
            stable = final_phase and position <= POSITION_TOLERANCE and angle <= ANGLE_TOLERANCE and speed <= .01
            if stable:
                if self.stable_start is None:
                    self.stable_start = time
                self.stable_count += 1
            else:
                self.stable_start = None
                self.stable_count = 0
            span = 0.0 if self.stable_start is None else time - self.stable_start
            self.last_sample.update(stable_count=self.stable_count, stable_span_s=span, final_phase=final_phase)
            if final_phase:
                if self.progress_start is None:
                    self.progress_start, self.progress_rho = time, rho
                elif time - self.progress_start >= 1.0 - 1e-6:
                    if rho > 1 and rho > .9 * self.progress_rho:
                        self._fail("NO_PROGRESS", "Final-pose error decreases by less than 10 percent in a full second",
                                   rho_start=self.progress_rho, rho=rho)
                    self.progress_start, self.progress_rho = time, rho
            if self.stable_count >= 121 and span >= 1.0 - 1e-6:
                self.reached = True
                self.last_sample["status"] = "POSE_REACHED"
            elif step >= self.profile.max_steps or time >= self.profile.max_seconds - 1e-6:
                self._fail("TIMEOUT", f"No complete stable arrival window within {self.profile.max_seconds:g} seconds")
            return dict(self.last_sample)
        except PoseCheckError as exc:
            if self.failure is None:
                self._fail(exc.category, str(exc), **exc.details)
            raise
