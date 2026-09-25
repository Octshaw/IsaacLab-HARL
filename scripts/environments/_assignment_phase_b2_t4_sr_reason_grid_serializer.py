"""Strict test-side B2-T4 reason-grid serialization and metadata contracts."""

from __future__ import annotations

from numbers import Integral
from typing import Iterable


REASON_GRID_SCHEMA_VERSION = "b2_t4_sr_termination_reason_grid_v1"
CLASSIFICATION_PRECEDENCE_SCHEMA_VERSION = "b2_t4_sr_classification_precedence_v1"

EVIDENCE_REASON_GRID_MISSING = "EVIDENCE_REASON_GRID_MISSING"
EVIDENCE_REASON_GRID_RANK_MISMATCH = "EVIDENCE_REASON_GRID_RANK_MISMATCH"
EVIDENCE_REASON_GRID_SHAPE_MISMATCH = "EVIDENCE_REASON_GRID_SHAPE_MISMATCH"
EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON = (
    "EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON"
)
EVIDENCE_REASON_GRID_RAGGED = "EVIDENCE_REASON_GRID_RAGGED"
EVIDENCE_REASON_VALUE_INVALID = "EVIDENCE_REASON_VALUE_INVALID"


class EvidenceReasonGridError(RuntimeError):
    """Deliberate fail-closed diagnostic for malformed test evidence."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"STOP — B2-T4-SR {code}: {detail}")


def _stop(code: str, detail: str) -> None:
    raise EvidenceReasonGridError(code, detail)


def _validate_expected_axes(expected_t: int, expected_e: int) -> tuple[int, int]:
    if (
        isinstance(expected_t, bool)
        or isinstance(expected_e, bool)
        or not isinstance(expected_t, Integral)
        or not isinstance(expected_e, Integral)
        or int(expected_t) <= 0
        or int(expected_e) <= 0
    ):
        _stop(
            EVIDENCE_REASON_GRID_SHAPE_MISMATCH,
            f"expected axes must be positive integers, got T={expected_t!r}, E={expected_e!r}",
        )
    return int(expected_t), int(expected_e)


def _validate_array_shape(
    shape: tuple[int, ...], expected_t: int, expected_e: int
) -> None:
    if len(shape) != 3:
        _stop(
            EVIDENCE_REASON_GRID_RANK_MISMATCH,
            f"expected rank 3 [T,E,1], got rank {len(shape)} shape={shape}",
        )
    if shape[2] != 1:
        _stop(
            EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON,
            f"expected trailing dimension 1, got shape={shape}",
        )
    if shape[0] != expected_t or shape[1] != expected_e:
        _stop(
            EVIDENCE_REASON_GRID_SHAPE_MISMATCH,
            f"expected shape=({expected_t},{expected_e},1), got shape={shape}",
        )


def _validate_nested_shape(
    source: list[object] | tuple[object, ...], expected_t: int, expected_e: int
) -> list[list[list[object]]]:
    if len(source) == 0:
        _stop(EVIDENCE_REASON_GRID_SHAPE_MISMATCH, "canonical grid must not be empty")
    if len(source) != expected_t:
        _stop(
            EVIDENCE_REASON_GRID_SHAPE_MISMATCH,
            f"expected T={expected_t}, got T={len(source)}",
        )
    if any(not isinstance(row, (list, tuple)) for row in source):
        _stop(
            EVIDENCE_REASON_GRID_RANK_MISMATCH,
            "every T row must be a list or tuple containing E rows",
        )
    row_lengths = tuple(len(row) for row in source)
    if len(set(row_lengths)) != 1:
        _stop(EVIDENCE_REASON_GRID_RAGGED, f"ragged E dimensions={row_lengths}")
    if row_lengths[0] != expected_e:
        _stop(
            EVIDENCE_REASON_GRID_SHAPE_MISMATCH,
            f"expected E={expected_e}, got E={row_lengths[0]}",
        )
    cells = tuple(cell for row in source for cell in row)
    if any(not isinstance(cell, (list, tuple)) for cell in cells):
        _stop(
            EVIDENCE_REASON_GRID_RANK_MISMATCH,
            "expected explicit trailing singleton containers at grid[t][e]",
        )
    cell_lengths = tuple(len(cell) for cell in cells)
    if len(set(cell_lengths)) != 1:
        _stop(EVIDENCE_REASON_GRID_RAGGED, f"ragged trailing dimensions={cell_lengths}")
    if cell_lengths[0] != 1:
        _stop(
            EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON,
            f"expected trailing dimension 1, got sizes={cell_lengths}",
        )
    return [[list(cell) for cell in row] for row in source]


def _valid_reason_domain(valid_reason_values: Iterable[object]) -> frozenset[int]:
    rows = tuple(valid_reason_values)
    if not rows or any(
        isinstance(value, bool) or not isinstance(value, Integral) for value in rows
    ):
        _stop(
            EVIDENCE_REASON_VALUE_INVALID,
            f"canonical reason domain must contain only non-bool integers, got {rows!r}",
        )
    return frozenset(int(value) for value in rows)


def classification_precedence_metadata_v1(
    *,
    raw_worker_classification: str,
    final_phase_classification: str,
    adjudication_source: str,
) -> dict[str, str]:
    """Return explicit raw-versus-final test-side classification metadata."""

    values = {
        "raw_worker_classification": raw_worker_classification,
        "final_phase_classification": final_phase_classification,
        "adjudication_source": adjudication_source,
    }
    for name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a nonempty string")
    return {
        "classification_precedence_schema": CLASSIFICATION_PRECEDENCE_SCHEMA_VERSION,
        **values,
    }


def serialize_termination_reason_grid_v1(
    source: object,
    *,
    expected_t: int,
    expected_e: int,
    valid_reason_values: Iterable[object],
) -> list[list[list[int]]]:
    """Validate and serialize one canonical ``[T,E,1]`` reason grid.

    Geometry is validated before scalar coercion. The output preserves the
    canonical trailing singleton dimension and contains JSON-native integers.
    """

    expected_t, expected_e = _validate_expected_axes(expected_t, expected_e)
    if source is None:
        _stop(EVIDENCE_REASON_GRID_MISSING, "termination_reason_grid is required")

    nested: list[list[list[object]]]
    try:
        import torch
    except ImportError:  # pragma: no cover - the project runtime supplies torch.
        torch = None  # type: ignore[assignment]
    if torch is not None and isinstance(source, torch.Tensor):
        shape = tuple(int(value) for value in source.shape)
        _validate_array_shape(shape, expected_t, expected_e)
        integer_dtypes = {
            torch.uint8,
            torch.int8,
            torch.int16,
            torch.int32,
            torch.int64,
        }
        if source.dtype not in integer_dtypes:
            _stop(
                EVIDENCE_REASON_VALUE_INVALID,
                f"torch reason dtype must be integral and non-bool, got {source.dtype}",
            )
        nested = source.detach().cpu().tolist()
    else:
        try:
            import numpy as np
        except ImportError:  # pragma: no cover - the project runtime supplies numpy.
            np = None  # type: ignore[assignment]
        if np is not None and isinstance(source, np.ndarray):
            shape = tuple(int(value) for value in source.shape)
            _validate_array_shape(shape, expected_t, expected_e)
            if source.dtype.kind not in ("i", "u"):
                _stop(
                    EVIDENCE_REASON_VALUE_INVALID,
                    f"numpy reason dtype must be integral and non-bool, got {source.dtype}",
                )
            nested = source.tolist()
        elif isinstance(source, (list, tuple)):
            nested = _validate_nested_shape(source, expected_t, expected_e)
        else:
            _stop(
                EVIDENCE_REASON_GRID_RANK_MISMATCH,
                f"unsupported reason-grid container type {type(source).__name__}",
            )

    result: list[list[list[int]]] = []
    domain = _valid_reason_domain(valid_reason_values)
    for t_index, row in enumerate(nested):
        serialized_row: list[list[int]] = []
        for e_index, cell in enumerate(row):
            value = cell[0]
            if isinstance(value, (list, tuple)):
                _stop(
                    EVIDENCE_REASON_GRID_RANK_MISMATCH,
                    f"unexpected nested scalar at [{t_index},{e_index},0]",
                )
            if isinstance(value, bool) or not isinstance(value, Integral):
                _stop(
                    EVIDENCE_REASON_VALUE_INVALID,
                    f"reason at [{t_index},{e_index},0] must be a non-bool integer, got {value!r}",
                )
            reason = int(value)
            if reason not in domain:
                _stop(
                    EVIDENCE_REASON_VALUE_INVALID,
                    f"reason at [{t_index},{e_index},0]={reason} is outside {sorted(domain)}",
                )
            serialized_row.append([reason])
        result.append(serialized_row)
    return result
