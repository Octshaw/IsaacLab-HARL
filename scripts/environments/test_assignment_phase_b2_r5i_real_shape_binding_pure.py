"""Pure regression for the real [B,1] R3 mask/index binding found by R5I."""

from __future__ import annotations

from pathlib import Path
import sys

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r1_contract_helpers as R1  # noqa: E402


R3 = R1.load_canonical("assignment_event_training_actor_mutation.py")


def main() -> int:
    one_dimensional = torch.tensor([True, True, False, False], dtype=torch.bool)
    two_dimensional = one_dimensional.reshape(4, 1)
    expected_dvm = (0, 1)
    expected_off_dvm = (2, 3)
    dvm_by_shape = (
        R3._canonical_true_row_indices_v1(one_dimensional),
        R3._canonical_true_row_indices_v1(two_dimensional),
    )
    off_dvm_by_shape = (
        R3._canonical_true_row_indices_v1(~one_dimensional),
        R3._canonical_true_row_indices_v1(~two_dimensional),
    )
    assert dvm_by_shape == (expected_dvm, expected_dvm)
    assert off_dvm_by_shape == (expected_off_dvm, expected_off_dvm)
    for rows in (*dvm_by_shape, *off_dvm_by_shape):
        assert len(rows) == len(set(rows))
        assert all(0 <= row < one_dimensional.numel() for row in rows)
    assert 0 not in off_dvm_by_shape[1]
    try:
        R3._canonical_true_row_indices_v1(torch.ones((4, 2), dtype=torch.bool))
    except R1.E.B2RContractError as exc:
        assert exc.stop_code == R3.STOP_FACTOR
    else:
        raise AssertionError("noncanonical mask shape did not fail closed")
    print(
        {
            "status": "PASS",
            "one_dimensional_dvm": expected_dvm,
            "two_dimensional_dvm": expected_dvm,
            "one_dimensional_off_dvm": expected_off_dvm,
            "two_dimensional_off_dvm": expected_off_dvm,
            "accepted_shape_encodings": 2,
            "true_row_cases": 2,
            "off_dvm_row_cases": 2,
            "duplicate_rows": 0,
            "out_of_range_rows": 0,
            "false_row_zero_injections": 0,
            "fail_closed_wider_shape_cases": 1,
            "real_runtime_actions": 0,
            "learner_mutations": 0,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
