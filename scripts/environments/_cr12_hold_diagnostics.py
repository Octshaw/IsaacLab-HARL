"""Bounded, CPU-only joint trace and explicit PD profiles for the CR12 hold test.

This module observes values supplied by the driver; it neither obtains runtime
state nor changes commands. A complete window describes coverage, not acceptance.
Only one CSV contains the samples; JSON summaries never duplicate that trace.
"""

from __future__ import annotations

import copy
import csv
import math
from pathlib import Path


CHECK_NAMES = ("clock", "contact", "joint", "geometry", "frame")
CHECK_STATUSES = ("NOT_CHECKED", "STARTED", "PASS", "FAIL", "ERROR")
WINDOWS = {
    "all_controlled": (1, 720), "initial_hold": (1, 120), "motion": (121, 360),
    "hold_3_4": (360, 480), "hold_4_5": (480, 600), "strict_hold": (600, 720),
}
BASELINE_K = (200., 4000., 2000., 200., 1000., 150.)
BASELINE_D = (20., 550., 166., 12., 37., 7.)
EFFORT_LIMITS = (20., 60., 30., 10., 10., 5.)
AXIS_INERTIA_ESTIMATES = (.405887645, 18.794490640, 3.448809055, .158322694, .336662855, .083248887)
PD_PROFILES = {
    "baseline": {"name": "baseline", "stiffness": list(BASELINE_K), "damping": list(BASELINE_D),
                 "effort_limits": list(EFFORT_LIMITS), "velocity_limit": .2,
                 "J": list(AXIS_INERTIA_ESTIMATES),
                 "rationale": "Unchanged approved baseline; no holding diagnosis inferred."},
    "hold_tune_01": {
        "name": "hold_tune_01", "stiffness": list(BASELINE_K),
        "damping": [20., 550., 166., 12.,
                    1.2*(2*math.sqrt(BASELINE_K[4]*AXIS_INERTIA_ESTIMATES[4])),
                    1.2*(2*math.sqrt(BASELINE_K[5]*AXIS_INERTIA_ESTIMATES[5]))],
        "effort_limits": list(EFFORT_LIMITS), "velocity_limit": .2,
        "J": list(AXIS_INERTIA_ESTIMATES),
        "rationale": (
            "Baseline held constant targets; joint_5/6 q peak-to-peak over 4-5 s was "
            "8.51e-6/9.79e-6 deg while native dq stayed near -0.02318/-0.02597 rad/s. "
            "Post-state PD estimates reached only 20.6%/8.2% of effort limits; this "
            "does not establish saturation. Keep every stiffness and other axis unchanged; "
            "set only joint_5/6 damping to the approved upper bound 1.2*(2*sqrt(K*J)). "
            "This sensitivity trial tests whether increased velocity feedback reduces "
            "persistent native dq; it does not establish an underdamping root cause. "
            "Native dq remains the acceptance signal and thresholds remain unchanged."
        ),
    },
    "hold_tune_02": {
        "name": "hold_tune_02",
        "stiffness": [200., 4000., 2000., 200., 1.25*BASELINE_K[4], 1.25*BASELINE_K[5]],
        "damping": [20., 550., 166., 12.,
                    1.2*(2*math.sqrt((1.25*BASELINE_K[4])*AXIS_INERTIA_ESTIMATES[4])),
                    1.2*(2*math.sqrt((1.25*BASELINE_K[5])*AXIS_INERTIA_ESTIMATES[5]))],
        "effort_limits": list(EFFORT_LIMITS), "velocity_limit": .2,
        "J": list(AXIS_INERTIA_ESTIMATES),
        "rationale": (
            "hold_tune_01 reduced joint_5/6 native absolute dq at 5 s to "
            "0.0214484669268/0.0236112158746 rad/s, improvements of 7.49%/9.10% "
            "against baseline, but both still failed the unchanged hold criterion. "
            "Position deviations remained stable and below the tracking threshold. "
            "This final sensitivity trial tests a larger approved gain scale: only "
            "joint_5/6 K becomes 1.25 times the original baseline and D becomes "
            "1.2*(2*sqrt(selected K*original J)); the other four axes and limits stay unchanged. "
            "Limited prior improvement does not establish a root cause or guarantee a pass. "
            "Native dq remains the acceptance signal and thresholds remain unchanged."
        ),
    },
}


def _six(values):
    result = tuple(float(value) for value in values)
    if len(result) != 6:
        raise ValueError("Expected six values in joint_1 through joint_6 order")
    return result


def validate_pd_profile(profile):
    """Validate an explicitly selected candidate against the original baseline."""
    value = copy.deepcopy(profile)
    k, d = _six(value["stiffness"]), _six(value["damping"])
    if not all(math.isfinite(number) and number > 0 for number in (*k, *d)):
        raise ValueError("PD gains must be positive finite numbers")
    if (_six(value["effort_limits"]) != EFFORT_LIMITS or value["velocity_limit"] != .2
            or _six(value["J"]) != AXIS_INERTIA_ESTIMATES):
        raise ValueError("PD selection cannot change effort/velocity limits or approved J estimates")
    changed = []
    for i, (ki, di) in enumerate(zip(k, d)):
        if not .8*BASELINE_K[i] <= ki <= 1.25*BASELINE_K[i]:
            raise ValueError(f"joint_{i+1} stiffness exceeds the original-baseline bounds")
        if (ki, di) != (BASELINE_K[i], BASELINE_D[i]):
            critical_scale = 2*math.sqrt(ki*AXIS_INERTIA_ESTIMATES[i])
            if not .8*critical_scale <= di <= 1.2*critical_scale:
                raise ValueError(f"joint_{i+1} damping exceeds the approved estimate-based bounds")
            changed.append(f"joint_{i+1}")
    if value["name"] == "baseline" and changed:
        raise ValueError("The baseline profile must retain its original numerical values")
    if value["name"] != "baseline" and not changed:
        raise ValueError("An unchanged confirmation run must use the baseline profile")
    value.update(stiffness=list(k), damping=list(d), changed_joints=changed)
    return value


def select_pd_profile(name):
    if name not in PD_PROFILES:
        raise ValueError(f"PD profile has not been defined from evidence: {name}")
    return validate_pd_profile(PD_PROFILES[name])


def add_diagnostic_arguments(parser):
    parser.add_argument("--record-joint-trace", action="store_true", help="Write one bounded six-axis CSV trace.")
    parser.add_argument("--pd-profile", choices=tuple(PD_PROFILES), default="baseline",
                        help="Explicit preselected runtime PD profile; baseline is unchanged.")


def phase_at(reference_time, step=None):
    if not math.isfinite(reference_time):
        return "INVALID"
    if step == 0:
        return "baseline"
    if reference_time <= 1.0 + 1e-10:
        return "initial_hold"
    if reference_time <= 3.0 + 1e-10:
        return "motion"
    if reference_time < 5.0 - 1e-10:
        return "post_motion_hold"
    return "strict_hold"


def _safe(number):
    return number if math.isfinite(number) else None


class JointTrace:
    """At most baseline + 720 immutable numeric snapshots, with check coverage.

    append() precedes predicates. mark_check() can also precede append() when a
    clock/contact failure prevents obtaining a state. A pending CSV row is
    committed by the next append or flush. Flush at phase boundaries, exceptions,
    and before native close. A late failure after a flush remains in the summary;
    already written CSV rows are never rewritten. The caller preserves primary
    runtime exceptions if diagnostic I/O itself fails.
    """

    def __init__(self, path=None, *, state_consistency=False):
        self.path = None if path is None else Path(path)
        self.state_consistency = bool(state_consistency)
        self._state_comparisons = {}
        self._rows = {}
        self._checks = {}
        self._written = set()
        self._stream = None
        self._writer = None
        self._closed = False
        self.failures = []
        self.recording_error = None
        self.post_write_check_updates = []
        if self.path is not None:
            # The driver owns the attempt directory; never silently replace a trace.
            self._stream = self.path.open("x", encoding="utf-8", newline="")
            self._writer = csv.writer(self._stream)
            try:
                self._writer.writerow(self._header(self.state_consistency))
                self._stream.flush()
            except BaseException:
                self._stream.close()
                raise

    @staticmethod
    def _header(state_consistency=False):
        fields = ["step", "actual_time_s", "elapsed_time_s", "reference_time_s", "phase", "sample_valid",
                  "reference_source"]
        for prefix, unit in (("q_target", "rad"), ("dq_target", "rad_s"), ("q", "rad"), ("dq", "rad_s")):
            fields.extend(f"{prefix}_{i}_{unit}" for i in range(1, 7))
        if state_consistency:
            for prefix, unit in (("native_q", "rad"), ("native_dq", "rad_s")):
                fields.extend(f"{prefix}_{i}_{unit}" for i in range(1, 7))
        return fields + [f"check_{name}" for name in CHECK_NAMES] + ["failure_categories"]

    def set_state_comparison(self, step, native_q=None, native_dq=None):
        """Attach independent native snapshots before this row is flushed; never alter acceptance q/dq."""
        if not self.state_consistency or step not in self._rows or step in self._written:
            raise ValueError("Native comparison requires an enabled, observed, unflushed sample")
        self._state_comparisons[step] = {
            "native_q": None if native_q is None else _six(native_q),
            "native_dq": None if native_dq is None else _six(native_dq),
        }

    def _error(self, exc):
        if self.recording_error is None:
            self.recording_error = f"{type(exc).__name__}: {exc}"

    def append(self, step, actual_time, elapsed_time, reference_time, q_target, dq_target, q, dq, *, q_reference=None):
        if self._closed:
            self._error(RuntimeError("Cannot append to a closed trace"))
            raise RuntimeError(self.recording_error)
        if isinstance(step, bool) or not isinstance(step, int) or step != len(self._rows) or not 0 <= step <= 720:
            self._error(ValueError("Trace requires baseline step 0 followed by consecutive controlled steps 1..720"))
            raise ValueError(self.recording_error)
        # Copy this observed step before committing earlier rows: an I/O failure
        # must not discard a state that the driver has already obtained.
        try:
            values = {key: _six(source) for key, source in (
                ("q_target", q_target), ("dq_target", dq_target), ("q", q), ("dq", dq))}
            reference = _six(q_target if q_reference is None else q_reference)
            times = tuple(float(value) for value in (actual_time, elapsed_time, reference_time))
        except (TypeError, ValueError, OverflowError) as exc:
            self._error(exc)
            raise
        finite = all(math.isfinite(value) for vector in (*values.values(), reference, times) for value in vector)
        timing_valid = finite and abs(times[2] - step/120.0) <= 1e-8 and abs(times[1] - times[2]) <= 1e-4
        if step and finite:
            timing_valid = timing_valid and times[0] > self._rows[step-1]["actual_time_s"]
        self._rows[step] = {"step": step, "actual_time_s": times[0], "elapsed_time_s": times[1],
                            "reference_time_s": times[2], "phase": phase_at(times[2], step),
                            "sample_valid": bool(timing_valid), "finite": finite,
                            "reference_source": "mathematical_reference" if q_reference is not None else "command_target_fallback",
                            "q_reference": reference, **values}
        if not finite:
            self.mark_failure("state_invalid", "Non-finite recorded state, command, reference, or time", step=step)
        elif not timing_valid:
            self.mark_failure("trace_timing", "Recorded sample time does not match the approved controlled step", step=step)
        self._write_rows([previous for previous in self._rows if previous < step and previous not in self._written])

    def mark_check(self, name, status="PASS", step=None, details=None):
        if name not in CHECK_NAMES or status not in CHECK_STATUSES:
            raise ValueError("Unknown diagnostic check or status")
        step = max(self._rows, default=0) if step is None else step
        if isinstance(step, bool) or not isinstance(step, int) or not 0 <= step <= min(720, len(self._rows)):
            raise ValueError("Check step must identify an observed or next attempted step")
        states = self._checks.setdefault(step, {})
        old = states.get(name, "NOT_CHECKED")
        if old in ("FAIL", "ERROR") and status not in ("FAIL", "ERROR"):
            raise ValueError("A failed check cannot be changed back to success")
        states[name] = status
        if step in self._written and old != status:
            self.post_write_check_updates.append({"step": step, "check": name, "status": status})
        if status in ("FAIL", "ERROR"):
            self.mark_failure(name, str(details) if details is not None else f"{name} check {status}", step=step)

    def mark_failure(self, category, message, step=None):
        # No I/O and no exception on a row already flushed: preserve the primary failure.
        step = max(self._rows, default=0) if step is None else step
        self.failures.append({"step": step, "category": str(category), "message": str(message),
                              "row_already_written": step in self._written})

    def _write_rows(self, steps):
        for step in steps:
            row = self._rows[step]
            fields = [row[name] for name in ("step", "actual_time_s", "elapsed_time_s", "reference_time_s",
                                             "phase", "sample_valid", "reference_source")]
            for name in ("q_target", "dq_target", "q", "dq"):
                fields.extend(row[name])
            if self.state_consistency:
                comparison = self._state_comparisons.get(step, {})
                for name in ("native_q", "native_dq"):
                    values = comparison.get(name)
                    fields.extend([None] * 6 if values is None else values)
            fields.extend(self._checks.get(step, {}).get(name, "NOT_CHECKED") for name in CHECK_NAMES)
            fields.append(";".join(failure["category"] for failure in self.failures if failure["step"] == step))
            try:
                if self._writer is not None:
                    self._writer.writerow(fields)
                self._written.add(step)
            except BaseException as exc:
                self._error(exc)
                raise

    def flush(self):
        self._write_rows([step for step in self._rows if step not in self._written])
        if self._stream is not None and not self._stream.closed:
            try:
                self._stream.flush()
            except BaseException as exc:
                self._error(exc)
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
                except BaseException as exc:
                    self._error(exc)
                    raise

    def _range(self, steps):
        if not steps:
            return {"start_step": None, "end_step": None,
                    **{f"{edge}_{kind}_time_s": None for edge in ("start", "end") for kind in ("actual", "elapsed", "reference")}}
        result = {"start_step": min(steps), "end_step": max(steps)}
        for edge, step in (("start", min(steps)), ("end", max(steps))):
            row = self._rows.get(step)
            for kind in ("actual", "elapsed", "reference"):
                result[f"{edge}_{kind}_time_s"] = None if row is None else _safe(row[f"{kind}_time_s"])
        return result

    def _window(self, first, last):
        steps = [step for step in self._rows if first <= step <= last]
        rows = [self._rows[step] for step in steps]
        finite = [row for row in rows if row["finite"]]
        return {**self._range(steps), "sample_count": len(rows), "finite_sample_count": len(finite),
                "expected_sample_count": last-first+1,
                "complete": steps == list(range(first, last+1)),
                "max_abs_error_rad": None if not finite else [max(abs(row["q"][i]-row["q_reference"][i]) for row in finite) for i in range(6)],
                "max_abs_speed_rad_s": None if not finite else [max(abs(row["dq"][i]) for row in finite) for i in range(6)]}

    def summary(self):
        coverage = {}
        for name in CHECK_NAMES:
            attempted = [step for step, states in self._checks.items() if step > 0 and states.get(name, "NOT_CHECKED") != "NOT_CHECKED"]
            checked = [step for step in attempted if self._checks[step][name] in ("PASS", "FAIL")]
            ranges = self._range(attempted)
            coverage[name] = {**ranges, "first_step": ranges["start_step"], "last_step": ranges["end_step"],
                              "attempted_sample_count": len(attempted), "checked_sample_count": len(checked),
                              "passed_sample_count": sum(self._checks[step][name] == "PASS" for step in attempted),
                              "failed_sample_count": sum(self._checks[step][name] in ("FAIL", "ERROR") for step in attempted),
                              "not_checked_sample_count": 720-len(attempted),
                              "expected_sample_count": 720, "complete": sorted(checked) == list(range(1, 721))}
        baseline = self._rows.get(0)
        return {"csv_path": None if self.path is None else str(self.path), "closed": self._closed,
                "sample_count": len(self._rows), "controlled_sample_count": max(0, len(self._rows)-1),
                "invalid_sample_count": sum(not row["sample_valid"] for row in self._rows.values()),
                "math_reference_sample_count": sum(step > 0 and row["reference_source"] == "mathematical_reference" for step, row in self._rows.items()),
                "baseline": {"observed": baseline is not None, "sample_valid": None if baseline is None else baseline["sample_valid"],
                             "checks": {name: self._checks.get(0, {}).get(name, "NOT_CHECKED") for name in CHECK_NAMES}},
                "windows": {name: self._window(*bounds) for name, bounds in WINDOWS.items()},
                "coverage": coverage, "has_failure": bool(self.failures or self.recording_error),
                "recording_error": self.recording_error, "failures": copy.deepcopy(self.failures),
                "post_write_check_updates": copy.deepcopy(self.post_write_check_updates)}
