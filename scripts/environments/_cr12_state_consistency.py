"""CPU-only CR12 state-expression comparison; never advances or writes physics.

Physical poses are link-frame xyz + XYZW, angular velocities are world rad/s.
USD joint local rotations are WXYZ. Body1 relative to body0 defines the sign.
Agreement between expressions does not prove an independent physical truth.
"""

from __future__ import annotations

import copy
import csv
import math
from pathlib import Path

import numpy as np


DERIVED_FIELDS = ("angle_rad", "dq_projected_rad_s", "off_axis_rad", "axis_alignment_rad",
                  "anchor_separation_m", "omega_off_axis_rad_s")


def _array(value, shape, name):
    result = np.array(value, dtype=np.float64, copy=True)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError(f"{name} must be finite with shape {shape}")
    return result


def _quat(value, name="quaternion"):
    value = _array(value, (4,), name)
    norm = float(np.linalg.norm(value))
    if abs(norm - 1.0) > 1e-3:
        raise ValueError(f"{name} is not a unit quaternion")
    return value / norm


def _mul(a, b):
    return np.r_[a[0]*b[0] - np.dot(a[1:], b[1:]),
                 a[0]*b[1:] + b[0]*a[1:] + np.cross(a[1:], b[1:])]


def _conj(q):
    return q * np.array([1., -1., -1., -1.])


def _rotate(q, v):
    return _mul(_mul(q, np.r_[0., v]), _conj(q))[1:]


def bind_joint_frames(records, joint_names, body_names):
    """Bind USD records by exact names, independent of joint/body array order.

    Required record keys: name, body0, body1, axis (X/Y/Z), localPos0/1,
    localRot0/1 (WXYZ). No missing physical frame is replaced with identity.
    """
    joint_names, body_names = list(joint_names), list(body_names)
    if len(joint_names) != 6 or len(set(joint_names)) != 6:
        raise ValueError("Expected six unique joint names")
    if len(body_names) != 7 or len(set(body_names)) != 7:
        raise ValueError("Expected seven unique body names")
    by_name = {}
    for record in records:
        if record["name"] in by_name:
            raise ValueError(f"Duplicate joint record: {record['name']}")
        by_name[record["name"]] = record
    result = []
    for name in joint_names:
        if name not in by_name:
            raise ValueError(f"Missing joint record: {name}")
        row = copy.deepcopy(by_name[name])
        for side in (0, 1):
            body = row[f"body{side}"]
            if body not in body_names:
                raise ValueError(f"{name}: unknown body{side}: {body}")
            row[f"body{side}_index"] = body_names.index(body)
            row[f"localPos{side}"] = _array(row[f"localPos{side}"], (3,), "local position").tolist()
            row[f"localRot{side}"] = _quat(row[f"localRot{side}"], "local WXYZ rotation").tolist()
        if row["body0"] == row["body1"] or row["axis"] not in ("X", "Y", "Z"):
            raise ValueError(f"{name}: invalid body pair or joint axis")
        result.append(row)
    return result


def analyze_links(bindings, poses, velocities, previous_angles=None):
    """Compare actual link poses/velocities; no generalized q is accepted here.

    velocities[:, :3] is world COM linear velocity (unused), [:, 3:] is world
    angular velocity. The fixed parent joint axis is always used for projection.
    A singular swing/twist decomposition is reported as a null angle, not zero.
    """
    poses = _array(poses, (7, 7), "link poses XYZW")
    velocities = _array(velocities, (7, 6), "world COM/angular velocities")
    if len(bindings) != 6:
        raise ValueError("Expected six joint bindings")
    previous = [None]*6 if previous_angles is None else list(previous_angles)
    if len(previous) != 6:
        raise ValueError("Expected six previous angles")
    rotations = [_quat(np.r_[pose[6], pose[3:6]], "link XYZW rotation") for pose in poses]
    result = {name: [] for name in DERIVED_FIELDS}
    result.update(axis_world=[], valid=[], errors=[])
    for index, row in enumerate(bindings):
        parent, child = row["body0_index"], row["body1_index"]
        qp = _mul(rotations[parent], _quat(row["localRot0"]))
        qc = _mul(rotations[child], _quat(row["localRot1"]))
        relative = _mul(_conj(qp), qc)
        axis = np.eye(3)[("X", "Y", "Z").index(row["axis"])]
        world_axis, child_axis = _rotate(qp, axis), _rotate(qc, axis)
        omega_delta = velocities[child, 3:] - velocities[parent, 3:]
        projected = float(np.dot(omega_delta, world_axis))
        component = float(np.dot(relative[1:], axis))
        norm = math.hypot(float(relative[0]), component)
        angle = off_axis = None
        if norm > 1e-12:
            twist = np.r_[relative[0], component*axis] / norm
            angle = (2*math.atan2(component, float(relative[0])) + math.pi) % (2*math.pi) - math.pi
            if previous[index] is not None:
                if not math.isfinite(float(previous[index])):
                    raise ValueError("Previous angles must be finite or None")
                angle = float(previous[index]) + (angle-float(previous[index])+math.pi) % (2*math.pi) - math.pi
            swing = _mul(relative, _conj(twist))
            off_axis = 2*math.atan2(float(np.linalg.norm(swing[1:])), abs(float(swing[0])))
        else:
            result["errors"].append({"joint": row["name"], "reason": "singular twist angle"})
        p0 = poses[parent, :3] + _rotate(rotations[parent], row["localPos0"])
        p1 = poses[child, :3] + _rotate(rotations[child], row["localPos1"])
        values = (angle, projected, off_axis,
                  math.acos(float(np.clip(np.dot(world_axis, child_axis), -1., 1.))),
                  float(np.linalg.norm(p1-p0)), float(np.linalg.norm(omega_delta-projected*world_axis)))
        for name, value in zip(DERIVED_FIELDS, values):
            result[name].append(value)
        result["axis_world"].append(world_axis.tolist())
        result["valid"].append(angle is not None)
    return result


def _clock(value):
    step, time = (value["step"], value["time"]) if isinstance(value, dict) else value
    if isinstance(step, bool) or int(step) != step or not math.isfinite(float(time)):
        raise ValueError("Clock must contain an integer physics step and finite time")
    return {"step": int(step), "time": float(time)}


class SnapshotReadError(RuntimeError):
    """A read failed; sample retains acquired values and null unobserved fields."""

    def __init__(self, message, sample):
        super().__init__(message)
        self.sample = sample


def snapshot_read(cached_getters, native_getters, copy_value, synchronize, read_clock):
    """Copy cache, fence, then native getter/fence/copy/fence for each field.

    copy_value must return independent CPU storage. Callbacks must not advance,
    render, refresh, or write physics. A nonfinite cached value stops native reads.
    Clock drift is returned for diagnosis; no alternative state is substituted.
    """
    sample = {"cached": {name: None for name in cached_getters},
              "native": {name: None for name in native_getters}, "clock_before": None,
              "clock_after": None, "clock_unchanged": False, "complete": False, "errors": []}
    field = "clock_before"
    try:
        sample["clock_before"] = _clock(read_clock())
        for name, getter in cached_getters.items():
            field = f"cached.{name}"
            value = copy_value(getter())
            sample["cached"][name] = value
            if value is None or not np.isfinite(np.asarray(value)).all():
                raise ValueError(f"{field} is missing or nonfinite")
        field = "cached_synchronize"
        synchronize()
        for name, getter in native_getters.items():
            field = f"native.{name}"
            native_value = getter()
            synchronize()
            value = copy_value(native_value)
            sample["native"][name] = value
            synchronize()
            if value is None or not np.isfinite(np.asarray(value)).all():
                raise ValueError(f"{field} is missing or nonfinite")
        field = "clock_after"
        sample["clock_after"] = _clock(read_clock())
        sample["clock_unchanged"] = sample["clock_before"] == sample["clock_after"]
        sample["complete"] = True
        return sample
    except Exception as exc:
        sample["errors"].append({"field": field, "type": type(exc).__name__, "message": str(exc)})
        # Do not make another native/clock call after an invalid state or handle.
        raise SnapshotReadError(f"State snapshot failed at {field}: {exc}", sample) from exc


def _nullable(value):
    if isinstance(value, (list, tuple)):
        return [_nullable(item) for item in value]
    if isinstance(value, dict):
        return {key: _nullable(item) for key, item in value.items()}
    if isinstance(value, np.ndarray):
        return _nullable(value.tolist())
    if isinstance(value, (float, np.floating)) and not math.isfinite(value):
        return None
    return value


class StateConsistencyTrace:
    """One small linked CSV; diagnostic coverage never changes drive acceptance."""

    def __init__(self, path, metadata):
        self.path = None if path is None else Path(path)
        self.metadata = copy.deepcopy(metadata)
        self.body_names = list(metadata["body_names"])
        self.joint_names = list(metadata["joint_names"])
        if len(self.body_names) != 7 or len(self.joint_names) != 6:
            raise ValueError("Metadata requires seven body names and six joint names")
        self._rows, self._written, self.failures = {}, set(), []
        self.recording_error, self._closed = None, False
        self._stream = None if self.path is None else self.path.open("x", encoding="utf-8", newline="")
        self._writer = None if self._stream is None else csv.writer(self._stream)
        if self._writer is not None:
            try:
                self._writer.writerow(self._header())
                self._stream.flush()
            except Exception:
                self._stream.close()
                raise

    def _header(self):
        fields = ["step", "actual_time_s", "elapsed_time_s", "reference_time_s", "status", "diagnostic_valid",
                  "read_before_step", "read_before_time_s", "read_after_step", "read_after_time_s", "clock_unchanged"]
        for body in self.body_names:
            fields.extend(f"{body}_{suffix}" for suffix in ("x_m", "y_m", "z_m", "qx", "qy", "qz", "qw",
                                                            "omega_x_rad_s", "omega_y_rad_s", "omega_z_rad_s"))
        for name in DERIVED_FIELDS:
            fields.extend(f"{joint}_{name}" for joint in self.joint_names)
        return fields

    def append(self, step, actual_time, elapsed_time, reference_time, poses=None, velocities=None,
               analysis=None, clock_before=None, clock_after=None, status="OBSERVED", comparison_valid=False):
        if self._closed or isinstance(step, bool) or not isinstance(step, int) or not 0 <= step <= 720:
            raise ValueError("Trace is closed or step is outside baseline + 720 steps")
        if step in self._rows or (self._rows and step <= max(self._rows)):
            raise ValueError("State trace samples must have unique increasing steps")
        row = {"step": step, "actual_time_s": float(actual_time), "elapsed_time_s": float(elapsed_time),
               "reference_time_s": float(reference_time), "status": str(status), "diagnostic_valid": False,
               "clock_unchanged": False, "clock_before": None, "clock_after": None,
               "poses": None, "omega": None, "analysis": None, "errors": []}
        # Preserve observed values before validation or any CSV write can fail.
        self._rows[step] = row
        try:
            if poses is not None:
                row["poses"] = np.array(poses, dtype=np.float64, copy=True).tolist()
            if velocities is not None:
                row["omega"] = np.array(velocities, dtype=np.float64, copy=True)[:, 3:].tolist()
            if analysis is not None:
                row["analysis"] = copy.deepcopy(analysis)
            if clock_before is not None:
                row["clock_before"] = _clock(clock_before)
            if clock_after is not None:
                row["clock_after"] = _clock(clock_after)
            row["clock_unchanged"] = (row["clock_before"] is not None and row["clock_before"] == row["clock_after"])
            _array(poses, (7, 7), "trace poses")
            _array(velocities, (7, 6), "trace velocities")
            for name in DERIVED_FIELDS:
                _array(None if analysis is None else analysis.get(name), (6,), name)
            times = _array([actual_time, elapsed_time, reference_time], (3,), "trace times")
            time_valid = (abs(times[2]-step/120.) <= 1e-8 and abs(times[1]-times[2]) <= 1e-4
                          and row["clock_after"] is not None and abs(times[0]-row["clock_after"]["time"]) <= 1e-10)
            row["diagnostic_valid"] = bool(comparison_valid and row["clock_unchanged"] and time_valid
                                            and status == "OBSERVED" and all(analysis.get("valid", []))
                                            and len(analysis.get("valid", [])) == 6)
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            row["errors"].append(f"{type(exc).__name__}: {exc}")
        self._write_rows([old for old in self._rows if old < step and old not in self._written])

    def mark_failure(self, category, message, step=None, *, affects_comparison=False):
        step = max(self._rows, default=None) if step is None else step
        self.failures.append({"step": step, "category": str(category), "message": str(message),
                              "affects_comparison": bool(affects_comparison), "row_already_written": step in self._written})
        if affects_comparison and step in self._rows:
            self._rows[step]["diagnostic_valid"] = False

    def _write_rows(self, steps):
        for step in steps:
            row = self._rows[step]
            fields = [row[name] for name in ("step", "actual_time_s", "elapsed_time_s", "reference_time_s",
                                             "status", "diagnostic_valid")]
            for name in ("clock_before", "clock_after"):
                clock = row[name]
                fields.extend([None, None] if clock is None else [clock["step"], clock["time"]])
            fields.append(row["clock_unchanged"])
            for i in range(7):
                for name, width in (("poses", 7), ("omega", 3)):
                    value = row[name]
                    valid_shape = (isinstance(value, (list, tuple)) and len(value) == 7
                                   and isinstance(value[i], (list, tuple)) and len(value[i]) == width)
                    fields.extend(value[i] if valid_shape else [None]*width)
            for name in DERIVED_FIELDS:
                value = None if row["analysis"] is None else row["analysis"].get(name)
                fields.extend(value if isinstance(value, (list, tuple, np.ndarray)) and len(value) == 6 else [None]*6)
            try:
                if self._writer is not None:
                    self._writer.writerow(_nullable(fields))
                self._written.add(step)
            except Exception as exc:
                self.recording_error = self.recording_error or f"{type(exc).__name__}: {exc}"
                raise

    def flush(self):
        try:
            self._write_rows([step for step in self._rows if step not in self._written])
            if self._stream is not None and not self._stream.closed:
                self._stream.flush()
        except Exception as exc:
            self.recording_error = self.recording_error or f"{type(exc).__name__}: {exc}"
            raise

    def close(self):
        if self._closed:
            return
        try:
            self.flush()
        finally:
            self._closed = True
            if self._stream is not None:
                try:
                    self._stream.close()
                except Exception as exc:
                    self.recording_error = self.recording_error or f"{type(exc).__name__}: {exc}"
                    raise

    def summary(self):
        def window(first, last):
            rows = [row for step, row in self._rows.items() if first <= step <= last]
            valid = [row for row in rows if row["diagnostic_valid"]]
            return {"sample_count": len(rows), "valid_sample_count": len(valid), "expected_sample_count": last-first+1,
                    "start_step": None if not rows else rows[0]["step"], "end_step": None if not rows else rows[-1]["step"],
                    "start_actual_time_s": None if not rows else rows[0]["actual_time_s"],
                    "end_actual_time_s": None if not rows else rows[-1]["actual_time_s"],
                    "complete": [row["step"] for row in valid] == list(range(first, last+1)),
                    "max_abs": {name: None if not valid else np.max(np.abs([row["analysis"][name] for row in valid]), axis=0).tolist()
                                for name in DERIVED_FIELDS}}
        windows = {name: window(*bounds) for name, bounds in {
            "all_controlled": (1, 720), "requested_1_600": (1, 600), "motion": (120, 360), "hold_3_4": (360, 480),
            "hold_4_5": (480, 600), "strict_hold": (600, 720)}.items()}
        diagnostic_failure = any(item["affects_comparison"] for item in self.failures)
        recheck_failed = any(key in check and not bool(check[key])
                             for check in self.metadata.get("snapshot_rechecks", [])
                             for key in ("unchanged", "acceptance_snapshot_unchanged"))
        controlled = [row for step, row in self._rows.items() if step > 0]
        observed_complete = (bool(controlled) and [row["step"] for row in controlled if row["diagnostic_valid"]]
                             == list(range(1, controlled[-1]["step"]+1)))
        return _nullable({"csv_path": None if self.path is None else str(self.path), "metadata": copy.deepcopy(self.metadata),
                          "first_step": min(self._rows, default=None), "last_step": max(self._rows, default=None),
                          "trace_saved": self.path is not None and self.path.is_file() and bool(self._rows)
                          and len(self._written) == len(self._rows) and self.recording_error is None,
                          "sample_count": len(self._rows), "controlled_sample_count": sum(step > 0 for step in self._rows),
                          "invalid_sample_count": sum(not row["diagnostic_valid"] for row in self._rows.values()),
                          "windows": windows, "complete_requested_comparison": windows["requested_1_600"]["complete"]
                          and not diagnostic_failure and not recheck_failed and self.recording_error is None,
                          "observed_comparison_complete": observed_complete and not diagnostic_failure
                          and not recheck_failed and self.recording_error is None,
                          "snapshot_recheck_failed": recheck_failed,
                          "recording_error": self.recording_error, "failures": copy.deepcopy(self.failures),
                          "invalid_samples": [{"step": step, "errors": row["errors"], "status": row["status"]}
                                              for step, row in self._rows.items() if not row["diagnostic_valid"]],
                          "closed": self._closed})
