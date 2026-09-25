"""Pure attempt-3 logging checks; no Isaac, optimizer steps, or live VN updates.

Dummy functions below exist only in this test process. They qualify observer
passthrough and failure diagnostics, never the real learner transaction.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
from unittest.mock import patch

import torch


sys.path.insert(0, str(Path(__file__).resolve().parent))
import _assignment_phase_b2_r1_contract_helpers as H  # noqa: E402
from harl.common.valuenorm import ValueNorm  # noqa: E402


A = H.load_canonical("assignment_event_training_real_isaac_adapter.py")
R3, R4 = A.R3, A.R4
ASSERTIONS = 0
FIELDS = ("running_mean", "running_mean_sq", "debiasing_term")
SYMBOLS = (
    (R3, "validate_factor_segment_contract_v1"),
    (R3, "execute_actor_sequence_v1"),
    (R4, "B2R4PermittedLiveValueNormProxyV1"),
    (R4, "B2R4CriticStepReceiptV1"),
    (R4, "execute_critic_sequence_v1"),
)


def check(condition: bool, message: str) -> None:
    global ASSERTIONS
    ASSERTIONS += 1
    if not condition:
        raise AssertionError(message)


def bindings() -> tuple[object, ...]:
    return tuple(getattr(module, name) for module, name in SYMBOLS)


def check_bindings(expected: tuple[object, ...]) -> None:
    check(all(a is b for a, b in zip(bindings(), expected)), "scoped symbols leaked")


def scope(*, factor=None, critic=None):
    return A._scoped_attempt3_progress_observers_v1(
        update_id="b2-r5i-re2-pure-diagnostic-only",
        actor_inputs={0: NS(decision_valid_mask=torch.tensor([[True], [False]]))},
        route_state=NS(machine=NS(current=NS(value="PURE_OBSERVER_TEST"))),
        factor_segment_observer=factor,
        critic_progress_observer=critic,
    )


@contextmanager
def runtime_cpu_fixture():
    previous = torch.get_default_dtype()
    try:
        torch.set_default_dtype(torch.float64)
        value_normalizer = ValueNorm(1, device=torch.device("cpu"))
    finally:
        torch.set_default_dtype(previous)
    yield value_normalizer


def factor_receipt():
    return NS(
        actor_id=0, actor_order_position=0, factor_before_digest="before",
        factor_pre_logprob_digest="pre", factor_post_logprob_digest="post",
        factor_transition=NS(
            ratio_full_digest="ratio", factor_after_digest="after", off_dvm_exact_one=True,
        ),
        dvm_indices=(0,), prior_accumulation_preserved=True,
        observed_backward_count=0, observed_step_count=0,
    )


def test_binding_lifetimes() -> dict[str, int]:
    original = bindings()
    with scope():
        check_bindings(original)
    check_bindings(original)
    with scope(factor=lambda event: None, critic=lambda event: None):
        check(all(a is not b for a, b in zip(bindings(), original)), "observers not installed")
    check_bindings(original)
    failure = RuntimeError("test-only scope body failure")
    try:
        with scope(factor=lambda event: None, critic=lambda event: None):
            raise failure
    except RuntimeError as exc:
        check(exc is failure, "scope body exception replaced")
    else:
        raise AssertionError("scope body failure disappeared")
    check_bindings(original)
    return {"scope_lifetime_cases": 3}


def test_factor_passthrough_and_failures() -> dict[str, int]:
    receipt = factor_receipt()
    sequence = NS(actor_segments=(receipt,), actor_order=(0,), initial_factor_digest="before", final_factor_digest="after")
    marker = object()
    validator_calls, sequence_calls, events = [], [], []

    def validator(candidate, *, expected_dvm_indices):
        validator_calls.append((candidate, expected_dvm_indices))

    def execute(*args, **kwargs):
        sequence_calls.append((args, kwargs))
        return sequence

    with patch.object(R3, "validate_factor_segment_contract_v1", validator), patch.object(R3, "execute_actor_sequence_v1", execute):
        original = bindings()
        with scope(factor=events.append):
            result = R3.validate_factor_segment_contract_v1(receipt, expected_dvm_indices=(0,))
            check(result is None, "validator result changed")
            check(R3.execute_actor_sequence_v1(marker, proof=marker) is sequence, "actor receipt identity changed")
        check_bindings(original)
    check(len(validator_calls) == 1 and validator_calls[0][0] is receipt, "validator not called exactly once")
    check(validator_calls[0][1] == (0,), "validator indices changed")
    check(len(sequence_calls) == 1 and sequence_calls[0][0][0] is marker and sequence_calls[0][1]["proof"] is marker, "actor call arguments changed")
    check(tuple(event["stage"] for event in events) == ("S5_ACTOR_SEGMENT_COMPLETE", "S5_ACTOR_SEQUENCE_COMPLETE"), "factor event order")
    check(events[0]["off_dvm_rows"] == (1,) and events[0]["factor_post_audit_pass"], "factor row evidence")
    check(events[1]["complete_actor_sequence"] and events[1]["final_factor_digest"] == "after", "final factor evidence")

    observer_error = OSError("test-only factor sink failure")

    def failing_observer(event):
        check(len(validator_calls) == 2, "observer ran before original validator")
        raise observer_error

    with patch.object(R3, "validate_factor_segment_contract_v1", validator):
        original = bindings()
        try:
            with scope(factor=failing_observer):
                R3.validate_factor_segment_contract_v1(receipt, expected_dvm_indices=(0,))
        except OSError as exc:
            check(exc is observer_error, "factor callback failure replaced")
        else:
            raise AssertionError("factor callback failure swallowed")
        check_bindings(original)

    validation_error = H.E.B2RContractError("test-only invalid factor", stop_code=R3.STOP_FACTOR, stage="pure_observer_test")
    rejected_events = []

    def rejected_validator(*args, **kwargs):
        raise validation_error

    with patch.object(R3, "validate_factor_segment_contract_v1", rejected_validator):
        original = bindings()
        try:
            with scope(factor=rejected_events.append):
                R3.validate_factor_segment_contract_v1(receipt, expected_dvm_indices=(0,))
        except H.E.B2RContractError as exc:
            check(exc is validation_error, "original factor STOP replaced")
        else:
            raise AssertionError("original factor STOP swallowed")
        check_bindings(original)
    check(rejected_events == [], "rejected factor published a PASS receipt")
    return {"factor_passthrough_cases": 1, "factor_callback_failure_cases": 1, "factor_validator_failure_cases": 1, "factor_progress_events": len(events)}


def test_critic_receipt_passthrough() -> dict[str, int]:
    original_constructor = R4.B2R4CriticStepReceiptV1
    constructor_calls, sequence_calls, events = [], [], []
    marker = object()
    sequence = NS(step_receipts=(), observed_backward_count=0, observed_step_count=0, observed_valuenorm_count=0, partitions_by_epoch=(), gradients_clean_after=True)

    def constructor(*args, **kwargs):
        constructor_calls.append((args, kwargs))
        return original_constructor(*args, **kwargs)

    def execute(*args, **kwargs):
        sequence_calls.append((args, kwargs))
        return sequence

    values = dict(
        epoch=0, minibatch=0, canonical_indices=(0, 1), raw_target_digest="raw",
        normalized_target_digest="normalized", final_slot_digest="final", valuenorm_receipt=None,
        backward_permit_id="backward", step_permit_id="step", loss_value=1.0,
        aggregate_gradient_norm=1.0, clip_result=1.0, critic_parameter_digest_before="parameter-before",
        critic_parameter_digest_after="parameter-after", critic_optimizer_digest_before="optimizer-before",
        critic_optimizer_digest_after="optimizer-after", optimizer_step_vector_before=(),
        optimizer_step_vector_after=(), critic_parameter_mutated=True, critic_optimizer_mutated=True,
        valuenorm_mutated=False, actors_unchanged=True, gradients_clean_after=True,
    )
    with patch.object(R4, "B2R4CriticStepReceiptV1", constructor), patch.object(R4, "execute_critic_sequence_v1", execute):
        original = bindings()
        with scope(critic=events.append):
            receipt = R4.B2R4CriticStepReceiptV1(**values)
            check(type(receipt) is original_constructor, "critic receipt class changed")
            check(R4.execute_critic_sequence_v1(marker, proof=marker) is sequence, "critic sequence receipt changed")
        check_bindings(original)
    check(len(constructor_calls) == 1 and constructor_calls[0] == ((), values), "critic constructor passthrough")
    check(len(sequence_calls) == 1 and sequence_calls[0][0][0] is marker and sequence_calls[0][1]["proof"] is marker, "critic sequence passthrough")
    check(tuple(event["stage"] for event in events) == ("S6_CRITIC_MINIBATCH_COMPLETE", "S6_CRITIC_SEQUENCE_COMPLETE"), "critic event order")
    check(events[0]["receipt_complete"] and events[0]["raw_return_digest"] == "raw", "critic receipt evidence")
    return {"critic_constructor_passthrough_cases": 1, "critic_sequence_passthrough_cases": 1, "critic_progress_events": len(events)}


def test_valuenorm_error_diagnostics(*, nonfinite: bool, sink_failure: bool) -> dict[str, int]:
    stop_code = H.E.STOP_NONFINITE_VALUENORM_STATE if nonfinite else R4.STOP_MUTATION_ATTRIBUTION
    source_error = H.E.B2RContractError("test-only original proxy STOP", stop_code=stop_code, stage="pure_observer_test")
    calls, events = [], []
    raw = torch.tensor([[1.0], [2.0]], dtype=torch.float32)
    marker = object()

    class DummyOriginalProxy:
        def __init__(self, argument, *, value_normalizer):
            calls.append(("init", argument, value_normalizer))
            self.value_normalizer = value_normalizer
            self.epoch, self.minibatch = 0, 0
            self.canonical_indices = (0, 1)
            self.raw_digest = A._tensor_digest(raw)
            self.counter = NS(critic_backward_executed=0, critic_step_executed=0, live_valuenorm_executed=0)

        def update(self, input_vector):
            check(len(events) == 1 and events[0]["stage"] == "S6_VALUENORM_PRE_UPDATE_BOUND", "pre-state observation did not precede original proxy call")
            calls.append(("update", input_vector))
            # Fixture state only: never call installed ValueNorm.update.
            if nonfinite:
                self.value_normalizer.running_mean.fill_(float("nan"))
            self.counter.live_valuenorm_executed = 1  # Synthetic diagnostic counter.
            raise source_error

    def observe(event):
        events.append(event)
        if sink_failure and event["stage"] == "S6_VALUENORM_POST_UPDATE_OBSERVED":
            raise OSError("test-only critic diagnostic sink failure")

    with runtime_cpu_fixture() as value_normalizer, patch.object(R4, "B2R4PermittedLiveValueNormProxyV1", DummyOriginalProxy):
        original = bindings()
        before = A._canonical_valuenorm_observation_v1(value_normalizer)
        try:
            with scope(critic=observe):
                proxy = R4.B2R4PermittedLiveValueNormProxyV1(marker, value_normalizer=value_normalizer)
                proxy.update(raw)
        except H.E.B2RContractError as exc:
            check(exc is source_error and exc.stop_code == stop_code, "qualified proxy STOP replaced")
        else:
            raise AssertionError("qualified proxy STOP swallowed")
        check_bindings(original)
        check(len(calls) == 2 and calls[0][0] == "init" and calls[0][1] is marker and calls[0][2] is value_normalizer and calls[1] == ("update", raw), "proxy original call count/identity changed")
        check(tuple(event["stage"] for event in events) == ("S6_VALUENORM_PRE_UPDATE_BOUND", "S6_VALUENORM_POST_UPDATE_OBSERVED"), "ValueNorm error diagnostics lost")
        post_event = events[-1]
        after = post_event["valuenorm_post"]
        check(post_event["valuenorm_pre_fingerprint"] == before["canonical_fingerprint"], "ValueNorm pre-fingerprint lost")
        check(post_event["raw_target_digest"] == A._tensor_digest(raw) and post_event["update_call_index"] == 1, "ValueNorm target/update-index lost")
        check(stop_code in post_event["qualified_source_error"], "qualified STOP diagnostic lost")
        check(after["canonical_field_names"] == FIELDS and len(after["canonical_fields"]) == 3, "canonical diagnostic fields lost")
        check(after["native_state_dict_key_count_diagnostic_only"] == 0, "native state_dict diagnostic not preserved")
        check(after["all_finite"] is (not nonfinite), "ValueNorm finiteness diagnostic wrong")
        check(bool(json.dumps(events, allow_nan=False)), "diagnostics are not strict JSON")
        if nonfinite:
            check(after["canonical_fingerprint"] in (None, ""), "invalid state was assigned a qualified canonical fingerprint")
            check(post_event["canonical_mutation"] is None, "invalid-state fallback became mutation truth")
            nonfinite_field = next(field for field in after["canonical_fields"] if field["name"] == "running_mean")
            check(not nonfinite_field["finite"] and bool(nonfinite_field["digest"]) and bool(nonfinite_field["bounded_values"]), "nonfinite field detail missing")
        else:
            check(after["canonical_fingerprint"] == before["canonical_fingerprint"], "no-mutation fixture fingerprint changed")
            check(post_event["changed_valuenorm_fields"] == () and not post_event["canonical_mutation"], "no-mutation diagnostic changed mutation truth")
    return {"nonfinite": int(nonfinite), "diagnostic_sink_failure": int(sink_failure), "preserved_original_stops": 1, "valuenorm_progress_events": len(events), "dummy_proxy_init_calls": 1, "dummy_proxy_update_calls": 1}


def main() -> int:
    original = bindings()
    results = {
        "bindings": test_binding_lifetimes(),
        "factor": test_factor_passthrough_and_failures(),
        "critic": test_critic_receipt_passthrough(),
        "valuenorm_cases": tuple(
            test_valuenorm_error_diagnostics(nonfinite=nonfinite, sink_failure=sink_failure)
            for nonfinite, sink_failure in ((False, False), (True, False), (True, True))
        ),
    }
    check_bindings(original)
    print(json.dumps({
        "status": "PASS", "classification": "PURE-LOGGING-OBSERVABILITY-ONLY",
        "assertions": ASSERTIONS, "results": results,
        "real_isaac_runs": 0, "actor_optimizer_steps": 0, "critic_optimizer_steps": 0,
        "installed_valuenorm_updates": 0, "full_learner_transactions": 0,
        "checkpoint_io": 0, "training_evaluation_playback": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
