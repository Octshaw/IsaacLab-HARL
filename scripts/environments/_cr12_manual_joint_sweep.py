"""Fixed manual CR12 joint-space reference, actual-state checks, and wall pacing.

Pure NumPy/stdlib: no simulator, controller, FK, asset writes, or state setters.
The angle is a source-frozen profile choice, never a runtime tuning parameter.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
import math
import time

import numpy as np

from _cr12_asset_math import JOINT_LIMITS, JOINT_NAMES


DT = 1.0 / 120.0
MAX_STEPS = 2520
GEOMETRY_MODE = "aabb_then_obb_margin_v1"
COMMAND_MARGIN_RAD = 0.02
COMMAND_INCREMENT_RAD = 0.00125
COMMAND_SPEED_RAD_S = 0.15
ACTUAL_SPEED_RAD_S = 0.25
TRACKING_RAD = math.radians(1.0)
HOLD_SPEED_RAD_S = 0.01
HARD_LIMIT_TOLERANCE_RAD = 1e-3  # Same numerical tolerance as the accepted driver.
CLOCK_TOLERANCE_S = 1e-5


class SweepCheckError(RuntimeError):
    def __init__(self, category, message, **details):
        super().__init__(message)
        self.category = category
        self.details = details


@dataclass(frozen=True, init=False)
class SweepProfile:
    name: str = "j3_visible_roundtrip_v1"
    joint_name: str = "joint_3"
    angle_deg: float = 20.0
    motion_seconds: float = 8.0
    max_seconds: float = 21.0
    max_steps: int = MAX_STEPS
    manual_joint_visual_only: bool = True
    geometry_mode: str = GEOMETRY_MODE


PROFILE = SweepProfile()


def select_profile(name=PROFILE.name):
    if name != PROFILE.name:
        raise SweepCheckError("SETUP", "Only the frozen manual joint profile is supported", requested=name)
    return PROFILE


def resolve_joint_names(joint_names):
    """Return canonical-name -> supplied-order index; reject aliases/extra names."""
    names = tuple(joint_names)
    if len(names) != 6 or len(set(names)) != 6 or set(names) != set(JOINT_NAMES):
        raise SweepCheckError("SETUP", "Expected exactly the six unique CR12 joint names", names=list(names))
    return {name: names.index(name) for name in JOINT_NAMES}


def _array(value, shape, label, category="state_invalid"):
    try:
        result = np.array(value, dtype=np.float64, copy=True)
    except (TypeError, ValueError) as exc:
        raise SweepCheckError(category, "Invalid " + label) from exc
    if result.shape != shape or not np.all(np.isfinite(result)):
        raise SweepCheckError(category, "Expected finite " + label, expected_shape=list(shape))
    return result


def _scanner_pose(value):
    pose = _array(value, (4, 4), "actual scanner pose")
    rotation = pose[:3, :3]
    if (not np.allclose(pose[3], [0, 0, 0, 1], atol=1e-8, rtol=0)
            or not np.allclose(rotation.T @ rotation, np.eye(3), atol=1e-6, rtol=0)
            or abs(np.linalg.det(rotation) - 1) > 1e-6):
        raise SweepCheckError("state_invalid", "Actual scanner pose must be a rigid world transform")
    return pose


def _readonly(value):
    result = np.array(value, copy=True)
    result.setflags(write=False)
    return result


def _step(value):
    if type(value) is not int or not 0 <= value <= MAX_STEPS:
        raise SweepCheckError("physics_count", "Reference step must be an integer in [0,2520]", step=value)
    return value


def _time(value):
    if isinstance(value, (bool, np.bool_)):
        raise SweepCheckError("physics_count", "Invalid simulation time")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise SweepCheckError("physics_count", "Invalid simulation time") from exc
    if not math.isfinite(result) or result < 0:
        raise SweepCheckError("physics_count", "Simulation time must be finite and nonnegative")
    return result


def quintic(u):
    """Return normalized position and analytical derivative, not a difference."""
    u = _time(u)
    if u > 1:
        raise SweepCheckError("COMMAND_REJECTED", "Quintic parameter is outside [0,1]")
    return 10*u**3 - 15*u**4 + 6*u**5, 30*u**2 - 60*u**3 + 30*u**4


def phase_at_step(step):
    seconds = _step(step) * DT
    if seconds < 1:
        return "START_HOLD"
    if seconds < 9:
        return "OUTBOUND"
    if seconds < 11:
        return "OUTBOUND_HOLD"
    if seconds < 19:
        return "RETURN"
    return "RETURN_HOLD"


@dataclass(frozen=True)
class Reference:
    step: int
    time_s: float
    phase: str
    q: np.ndarray
    dq: np.ndarray


class SweepPlan:
    def __init__(self, q_start, joint_names=JOINT_NAMES):
        self.joint_names = tuple(joint_names)
        self.mapping = resolve_joint_names(self.joint_names)
        self.moving_index = self.mapping[PROFILE.joint_name]
        self.profile = PROFILE
        self.q_start = _readonly(_array(q_start, (6,), "initial native joint position", "SETUP"))
        self.limits = _readonly(np.array([JOINT_LIMITS[JOINT_NAMES.index(name)] for name in self.joint_names]))
        q_out = self.q_start.copy()
        q_out[self.moving_index] += math.radians(PROFILE.angle_deg)
        self.q_out = _readonly(q_out)
        for name, q in (("start", self.q_start), ("outbound", self.q_out)):
            if np.any(q < self.limits[:, 0] + COMMAND_MARGIN_RAD) or np.any(q > self.limits[:, 1] - COMMAND_MARGIN_RAD):
                raise SweepCheckError("SETUP", "Frozen reference violates command hard-limit margin", endpoint=name)

    def reference(self, step):
        step = _step(step)
        seconds = step * DT
        q = self.q_start.copy()
        dq = np.zeros(6)
        distance = self.q_out[self.moving_index] - self.q_start[self.moving_index]
        if seconds <= 1:
            h = velocity = 0.0
        elif seconds < 9:
            h, derivative = quintic((seconds - 1) / PROFILE.motion_seconds)
            velocity = derivative * distance / PROFILE.motion_seconds
        elif seconds <= 11:
            h, velocity = 1.0, 0.0
        elif seconds < 19:
            progress, derivative = quintic((seconds - 11) / PROFILE.motion_seconds)
            h, velocity = 1.0 - progress, -derivative * distance / PROFILE.motion_seconds
        else:
            h = velocity = 0.0
        q[self.moving_index] += h * distance
        dq[self.moving_index] = velocity
        return Reference(step, seconds, phase_at_step(step), _readonly(q), _readonly(dq))

    def validate_command(self, q, dq, previous_q, dtype=np.float32):
        """Validate the actual submission dtype without clamp or state feedback."""
        if np.dtype(dtype) != np.dtype(np.float32):
            raise SweepCheckError("COMMAND_REJECTED", "The accepted PhysX command dtype is float32")
        position = _array(q, (6,), "position command", "COMMAND_REJECTED").astype(dtype)
        velocity = _array(dq, (6,), "velocity command", "COMMAND_REJECTED").astype(dtype)
        previous = _array(previous_q, (6,), "previous submitted position", "COMMAND_REJECTED")
        if not np.all(np.isfinite(position)) or not np.all(np.isfinite(velocity)):
            raise SweepCheckError("COMMAND_REJECTED", "Submission dtype overflow")
        if np.any(position < self.limits[:, 0] + COMMAND_MARGIN_RAD) or np.any(position > self.limits[:, 1] - COMMAND_MARGIN_RAD):
            raise SweepCheckError("COMMAND_REJECTED", "Command violates original hard-limit margin")
        if np.any(np.abs(position.astype(np.float64) - previous) > COMMAND_INCREMENT_RAD):
            raise SweepCheckError("COMMAND_REJECTED", "Per-tick position command increment exceeds limit")
        if np.any(np.abs(velocity) > COMMAND_SPEED_RAD_S):
            raise SweepCheckError("COMMAND_REJECTED", "Velocity command exceeds limit")
        return _readonly(position), _readonly(velocity)

    def command(self, step, previous_q, dtype=np.float32):
        reference = self.reference(step)
        q, dq = self.validate_command(reference.q, reference.dq, previous_q, dtype)
        return Reference(reference.step, reference.time_s, reference.phase, q, dq)


def _window(start_step, end_step):
    return {"start_step": start_step, "end_step": end_step, "count": 0,
            "first_time_s": None, "last_time_s": None, "span_s": 0.0,
            "max_abs_error_deg": [0.0]*6, "max_abs_dq_rad_s": [0.0]*6,
            "complete": False, "all_passed": False}


class SweepMonitor:
    """Statistics from supplied native joints and measured scanner transforms only.

    Physics/contact/geometry/frame/render guards remain the runtime caller's
    responsibility. Pass their failures to mark_failure; success here is internal.
    """

    def __init__(self, plan, scanner_start_actual_matrix):
        self.plan = plan
        self.scanner_start = _readonly(_scanner_pose(scanner_start_actual_matrix))
        self.failure = None
        self.last_sample = None
        self._error = None
        self._summary = {"status": "RUNNING", "profile": PROFILE.name, "angle_deg": PROFILE.angle_deg,
                         "geometry_mode": GEOMETRY_MODE, "joint_names": list(plan.joint_names),
                         "completed_physics_steps": 0, "last_time_s": 0.0, "complete": False,
                         "all_passed": False, "failure": None,
                         "joint_excursion_deg": 0.0, "joint_excursion_step": 0, "joint_excursion_time_s": 0.0,
                         "positive_joint_excursion_deg": 0.0, "positive_joint_excursion_step": 0,
                         "positive_joint_excursion_time_s": 0.0,
                         "scanner_excursion_m": 0.0, "scanner_excursion_step": 0, "scanner_excursion_time_s": 0.0,
                         "max_joint_excursion_deg": [0.0]*6, "max_abs_dq_rad_s": [0.0]*6,
                         "max_tracking_error_deg": [0.0]*6, "amplitude_pass": False, "direction_pass": False,
                         "q_start_rad": plan.q_start.tolist(), "scanner_start_m": self.scanner_start[:3, 3].tolist(),
                         "endpoint_windows": {"outbound": _window(1200, 1320), "return": _window(2400, 2520)},
                         "endpoints": {"outbound": None, "return": None}}

    def mark_failure(self, category, message, **details):
        if self.failure is None:
            self.failure = {"category": category, "message": message, "details": copy.deepcopy(details)}
            self._error = SweepCheckError(category, message, **details)
        self._summary.update(status="FAILED", all_passed=False, failure=copy.deepcopy(self.failure))
        if self.last_sample is not None:
            self.last_sample.update(status="FAILED", failure_category=self.failure["category"])

    def observe(self, step, time_s, q_native, dq_native, scanner_actual_matrix):
        if self.failure is not None:
            raise self._error
        self.last_sample = {"step": step, "time_s": time_s, "status": "CHECKING", "failure_category": None}
        # Preserve a failed finite/shape check's supplied sample for the caller's
        # evidence writer; these raw values never enter maxima or acceptance.
        for key, value in (("q_rad", q_native), ("dq_rad_s", dq_native),
                           ("scanner_pose", scanner_actual_matrix)):
            try:
                self.last_sample[key] = np.asarray(value).tolist()
            except (TypeError, ValueError):
                self.last_sample[key] = None
        try:
            return self._observe(step, time_s, q_native, dq_native, scanner_actual_matrix)
        except SweepCheckError as error:
            self.mark_failure(error.category, str(error), **error.details)
            raise self._error

    def _observe(self, step, time_s, q_native, dq_native, scanner_actual_matrix):
        step = _step(step)
        seconds = _time(time_s)
        previous = self._summary["completed_physics_steps"]
        if step != previous + 1 or abs(seconds - step*DT) > CLOCK_TOLERANCE_S:
            raise SweepCheckError("physics_count", "Expected consecutive post-step samples at the reference time", step=step)
        if abs(seconds - self._summary["last_time_s"] - DT) > 1e-6:
            raise SweepCheckError("physics_count", "Actual sample time did not advance exactly one physics dt")
        self._summary.update(completed_physics_steps=step, last_time_s=seconds)
        reference = self.plan.reference(step)
        q = _array(q_native, (6,), "native joint position")
        dq = _array(dq_native, (6,), "native joint velocity")
        scanner = _scanner_pose(scanner_actual_matrix)
        error = np.abs(q-reference.q)
        speed = np.abs(dq)
        excursion = q-self.plan.q_start
        index = self.plan.moving_index
        angle_deg = math.degrees(float(excursion[index]))
        distance = float(np.linalg.norm(scanner[:3, 3] - self.scanner_start[:3, 3]))
        sample = {"step": step, "time_s": seconds, "reference_time_s": reference.time_s, "phase": reference.phase,
                  "q_rad": q.tolist(), "dq_rad_s": dq.tolist(), "q_reference_rad": reference.q.tolist(),
                  "dq_reference_rad_s": reference.dq.tolist(), "tracking_error_deg": np.degrees(error).tolist(),
                  "scanner_position_m": scanner[:3, 3].tolist(), "joint3_signed_excursion_deg": angle_deg,
                  "scanner_distance_from_start_m": distance, "status": "RUNNING", "failure_category": None}
        self.last_sample = sample
        stats = self._summary
        stats.update(completed_physics_steps=step, last_time_s=seconds)
        for key, values in (("max_joint_excursion_deg", np.degrees(np.abs(excursion))),
                            ("max_abs_dq_rad_s", speed), ("max_tracking_error_deg", np.degrees(error))):
            stats[key] = np.maximum(stats[key], values).tolist()
        for prefix, value in (("joint_excursion", abs(angle_deg)), ("positive_joint_excursion", angle_deg),
                              ("scanner_excursion", distance)):
            unit = "m" if prefix == "scanner_excursion" else "deg"
            if value > stats[prefix + "_" + unit]:
                stats[prefix + "_" + unit] = value
                stats[prefix + "_step"] = step
                stats[prefix + "_time_s"] = seconds
        stats["amplitude_pass"] = stats["joint_excursion_deg"] > 10.0 and stats["scanner_excursion_m"] > 0.10
        stats["direction_pass"] = stats["positive_joint_excursion_deg"] > 10.0
        active_window = None
        for label, window in stats["endpoint_windows"].items():
            if window["start_step"] <= step <= window["end_step"]:
                active_window = label
                window["count"] += 1
                if window["first_time_s"] is None:
                    window["first_time_s"] = seconds
                window["last_time_s"] = seconds
                window["span_s"] = seconds-window["first_time_s"]
                window["max_abs_error_deg"] = np.maximum(window["max_abs_error_deg"], np.degrees(error)).tolist()
                window["max_abs_dq_rad_s"] = np.maximum(window["max_abs_dq_rad_s"], speed).tolist()
                window["complete"] = (step == window["end_step"] and window["count"] == 121
                                      and abs(window["span_s"]-1.0) <= CLOCK_TOLERANCE_S)
                window["all_passed"] = (window["complete"] and max(window["max_abs_error_deg"]) <= 1.0
                                        and max(window["max_abs_dq_rad_s"]) <= HOLD_SPEED_RAD_S)
                if step == window["end_step"]:
                    stats["endpoints"][label] = {key: copy.deepcopy(sample[key]) for key in
                                                ("step", "time_s", "q_rad", "dq_rad_s", "scanner_position_m")}
                    stats["endpoints"][label]["scanner_pose"] = scanner.tolist()
        if np.any(q < self.plan.limits[:, 0]-HARD_LIMIT_TOLERANCE_RAD) or np.any(q > self.plan.limits[:, 1]+HARD_LIMIT_TOLERANCE_RAD):
            raise SweepCheckError("joint_limit", "Actual native state exceeds the original hard joint limit")
        if np.any(speed > ACTUAL_SPEED_RAD_S):
            raise SweepCheckError("tracking", "Actual joint speed exceeds 0.25 rad/s")
        if np.any(error > TRACKING_RAD):
            raise SweepCheckError("tracking", "Actual joint error exceeds the same-time one-degree reference tolerance")
        if excursion[index] < -TRACKING_RAD or excursion[index] > math.radians(PROFILE.angle_deg)+TRACKING_RAD:
            raise SweepCheckError("tracking", "Actual joint_3 leaves the approved start-relative range")
        other = [i for i in range(6) if i != index]
        if np.any(np.abs(excursion[other]) > TRACKING_RAD):
            raise SweepCheckError("tracking", "A held joint moves more than one degree from its actual start")
        if active_window is not None and np.any(speed > HOLD_SPEED_RAD_S):
            raise SweepCheckError("holding", "Native velocity exceeds 0.01 rad/s in the endpoint window", window=active_window)
        if step == MAX_STEPS:
            stats["complete"] = all(window["complete"] for window in stats["endpoint_windows"].values())
            if not stats["complete"] or not all(window["all_passed"] for window in stats["endpoint_windows"].values()):
                raise SweepCheckError("holding", "Both endpoint windows must contain all 121 valid samples")
            if not stats["amplitude_pass"] or not stats["direction_pass"]:
                raise SweepCheckError("VISIBLE_AMPLITUDE_NOT_MET", "Measured joint/scanner excursion did not exceed the visible-motion thresholds")
            stats.update(status="INTERNAL_CHECKS_PASS", all_passed=True)
            sample["status"] = "INTERNAL_CHECKS_PASS"
        return copy.deepcopy(sample)

    def summary(self):
        return copy.deepcopy(self._summary)


class RealtimePacer:
    """Absolute monotonic deadlines; no physics/render callback or catch-up steps."""

    def __init__(self, clock=time.monotonic, sleeper=time.sleep):
        self._clock, self._sleep = clock, sleeper
        self.start = self._now()
        self._last_wall = self.start
        self.pace_calls = 0
        self.total_sleep_s = 0.0

    def _now(self):
        value = float(self._clock())
        if not math.isfinite(value):
            raise SweepCheckError("physics_count", "Non-finite monotonic clock")
        return value

    def pace(self, sim_time_s):
        seconds = _time(sim_time_s)
        expected = self.pace_calls + 1
        if expected > MAX_STEPS or abs(seconds-expected*DT) > CLOCK_TOLERANCE_S:
            raise SweepCheckError("physics_count", "Pacer requires exactly one call after each completed physics tick")
        current = self._now()
        if current < self._last_wall:
            raise SweepCheckError("physics_count", "Monotonic clock moved backwards")
        remaining = self.start + seconds-current
        requested = max(0.0, remaining)
        if requested:
            self._sleep(requested)
            self.total_sleep_s += requested
        after = self._now()
        if after < current:
            raise SweepCheckError("physics_count", "Monotonic clock moved backwards during pacing")
        self._last_wall = after
        self.pace_calls += 1
        return requested

    def summary(self, sim_time_s):
        seconds = _time(sim_time_s)
        current = self._now()
        if current < self._last_wall:
            raise SweepCheckError("physics_count", "Monotonic clock moved backwards before its summary")
        wall = current-self.start
        return {"simulation_time_s": seconds, "controlled_wall_time_s": wall,
                "playback_ratio": seconds/wall if wall > 0 else None,
                "total_sleep_s": self.total_sleep_s, "pace_calls": self.pace_calls}
