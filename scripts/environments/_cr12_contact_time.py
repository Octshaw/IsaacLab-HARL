"""Exact, dtype-aware SensorBase clock recurrence for CR12 contact reads.

SensorBase.update uses tensor += Python float(dt). For float32/float64 the
wrapped scalar is converted to the tensor dtype and the sum rounded to that
dtype. This module predicts that representable sum, not real-valued n * dt.
It does not update/read sensors, validate forces, advance clocks or commit state.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numbers
import numpy as np

PHYSICS_DT = 1.0 / 120.0
_DTYPES = {'float32': np.dtype('float32'), 'float64': np.dtype('float64')}


@dataclass(frozen=True)
class ContactTimeSnapshot:
    timestamp: float | None
    last_update: float | None
    dtype: str
    device: str
    shape: tuple
    last_dtype: str
    last_device: str
    last_shape: tuple
    outdated: bool | None
    identity: tuple
    generation: str | int | None


def freeze_snapshot(*, timestamp, last_update, dtype, device, shape,
                    last_dtype, last_device, last_shape, outdated, identity, generation):
    """Copy scalar values and immutable metadata; retain no live tensor/array aliases.

    Caller takes each value from its one normal buffer read. Bad/non-scalar values
    become None and are rejected by validate_timestamp, never substituted by zero.
    generation is the sensor resource generation, not an authority episode number.
    """
    def scalar(value):
        return float(value) if isinstance(value, numbers.Real) and not isinstance(value, (bool, np.bool_)) else None
    def dimensions(value):
        if not isinstance(value, (tuple, list)):
            return ()
        return tuple(int(v) if isinstance(v, numbers.Integral) and not isinstance(v, (bool, np.bool_)) else None for v in value)
    ident = tuple(identity) if isinstance(identity, (tuple, list)) else ()
    # Only immutable scalar identity parts are allowed. No shared mutable buffers.
    if not ident or not all(type(v) in (str, int) and (not isinstance(v, str) or bool(v)) for v in ident):
        ident = ()
    if not (type(generation) is str and generation or type(generation) is int and generation >= 0):
        generation = None
    return ContactTimeSnapshot(scalar(timestamp), scalar(last_update), str(dtype), str(device), dimensions(shape),
        str(last_dtype), str(last_device), dimensions(last_shape),
        bool(outdated) if isinstance(outdated, (bool, np.bool_)) else None, ident, generation)


def _valid_snapshot(snapshot):
    if not isinstance(snapshot, ContactTimeSnapshot):
        return {'snapshot_type': False}
    finite = (snapshot.timestamp is not None and snapshot.last_update is not None
              and math.isfinite(snapshot.timestamp) and math.isfinite(snapshot.last_update))
    supported = snapshot.dtype in _DTYPES
    representable = False
    if finite and supported:
        with np.errstate(over='ignore', invalid='ignore'):
            kind = _DTYPES[snapshot.dtype].type
            representable = (float(kind(snapshot.timestamp)) == snapshot.timestamp
                             and float(kind(snapshot.last_update)) == snapshot.last_update)
    return {'snapshot_type': True, 'dtype_supported': supported,
        'shape_one_sensor': snapshot.shape == (1,), 'last_shape_matches': snapshot.last_shape == snapshot.shape,
        'last_dtype_matches': snapshot.last_dtype == snapshot.dtype,
        'device_supported': snapshot.device in ('cpu', 'cuda:0'),
        'last_device_matches': snapshot.last_device == snapshot.device,
        'finite_time': bool(finite), 'nonnegative_time': bool(finite and snapshot.timestamp >= 0 and snapshot.last_update >= 0),
        'values_representable': bool(representable),
        'outdated_false': snapshot.outdated is False,
        'last_update_matches_timestamp': bool(finite and snapshot.timestamp == snapshot.last_update),
        'identity_present': bool(snapshot.identity), 'resource_generation_present': snapshot.generation is not None}


def _number(value):
    return float(value) if isinstance(value, numbers.Real) and math.isfinite(float(value)) else None


def validate_timestamp(previous, current, dt, *, mode='advance'):
    """Return JSON-safe diagnostics; caller commits current only after ALL guards.

    baseline: one explicit first dt=0 data refresh, previous must be None.
    advance: one fixed 1/120-s Python-float update and refreshed data are required.
    readonly: dt=0, exact same valid clock/readback, no new update count.

    Exact comparison and an ULP smaller than dt preserve distinguishability of
    zero/one/two updates. Unsupported dtype/resolution fails closed. This cannot
    attest to unexposed native frame IDs; data/force/path/clock checks stay outside.
    """
    checks = {'mode_supported': mode in ('baseline', 'advance', 'readonly'),
              'dt_python_float_finite': type(dt) is float and math.isfinite(dt)}
    checks.update({'current_' + k: v for k, v in _valid_snapshot(current).items()})
    previous_valid = isinstance(previous, ContactTimeSnapshot) and all(_valid_snapshot(previous).values())
    if mode == 'baseline':
        checks['first_baseline_only'] = previous is None
        checks['dt_matches_mode'] = type(dt) is float and dt == 0.0
    else:
        checks['previous_valid_snapshot'] = bool(previous_valid)
        checks['dt_matches_mode'] = type(dt) is float and dt == (PHYSICS_DT if mode == 'advance' else 0.0)
        if isinstance(previous, ContactTimeSnapshot) and isinstance(current, ContactTimeSnapshot):
            for key in ('identity', 'generation', 'dtype', 'device', 'shape'):
                checks['same_' + key] = getattr(previous, key) == getattr(current, key)
        else:
            checks['same_identity'] = False
    result = {'mode': mode, 'dt': _number(dt), 'dt_type': type(dt).__name__,
        'previous': _number(previous.timestamp) if isinstance(previous, ContactTimeSnapshot) else None,
        'current': _number(current.timestamp) if isinstance(current, ContactTimeSnapshot) else None,
        'last_update': _number(current.last_update) if isinstance(current, ContactTimeSnapshot) else None,
        'expected_next': None, 'expected_two_updates': None, 'represented_dt': None,
        'ulp_at_previous': None, 'actual_delta': None, 'expected_error': None,
        'old_increment_error': None, 'old_shadow_pass': None,
        'dtype': current.dtype if isinstance(current, ContactTimeSnapshot) else None,
        'device': current.device if isinstance(current, ContactTimeSnapshot) else None,
        'comparison': 'exact representable dtype recurrence; no tolerance/rtol', 'checks': checks}
    arithmetic_read = (isinstance(previous, ContactTimeSnapshot) and isinstance(current, ContactTimeSnapshot)
        and _number(previous.timestamp) is not None and _number(current.timestamp) is not None
        and checks['dt_python_float_finite'])
    if arithmetic_read:
        prev, observed = previous.timestamp, current.timestamp
        result['actual_delta'] = observed-prev
        result['old_increment_error'] = abs(observed-prev-dt)
        result['old_shadow_pass'] = bool(abs(observed-prev-dt) <= 1e-6)
        if mode == 'readonly':
            result['expected_next'] = prev
            result['expected_error'] = observed-prev
            checks['exact_same_readonly_timestamp'] = observed == prev
        elif mode == 'advance' and previous.dtype == current.dtype and current.dtype in _DTYPES:
            dtype = _DTYPES[current.dtype]
            with np.errstate(over='ignore', invalid='ignore', under='ignore'):
                # Explicit operand casts avoid NumPy/Python scalar promotion differences.
                prior = dtype.type(prev)
                increment = dtype.type(dt)
                expected = np.add(prior, increment, dtype=dtype)
                twice = np.add(expected, increment, dtype=dtype)
                spacing = np.nextafter(prior, dtype.type(np.inf), dtype=dtype)-prior
            next_value, two_value, ulp = float(expected), float(twice), float(spacing)
            result.update(expected_next=_number(next_value), expected_two_updates=_number(two_value),
                represented_dt=_number(increment), ulp_at_previous=_number(ulp),
                expected_error=_number(observed-next_value))
            checks['finite_recurrence'] = all(math.isfinite(v) for v in (next_value, two_value, ulp))
            checks['resolution_distinguishes_updates'] = bool(checks['finite_recurrence']
                and 0 < ulp < float(increment) and prev < next_value < two_value)
            checks['exact_single_update'] = observed == next_value
    elif mode in ('advance', 'readonly'):
        checks['recurrence_inputs_valid'] = False
    result['failures'] = [key for key, passed in checks.items() if passed is not True]
    result['passed'] = not result['failures']
    return result
