"""Plain PyTorch qualification for the B2-R5I-VF ValueNorm fingerprint seam."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
import json
from pathlib import Path
import sys

import torch


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import _assignment_phase_b2_r1_contract_helpers as H  # noqa: E402
import _assignment_phase_b2_r4_critic_mutation_helpers as R4H  # noqa: E402

E = H.E
R4 = R4H.R4
from harl.common.valuenorm import ValueNorm  # noqa: E402


FIELDS = ("running_mean", "running_mean_sq", "debiasing_term")
ASSERTIONS = 0


def check(condition: bool, message: str) -> None:
    global ASSERTIONS
    ASSERTIONS += 1
    if not condition:
        raise AssertionError(message)


def expect_stop(stop_code: str, function) -> None:
    global ASSERTIONS
    try:
        function()
    except E.B2RContractError as exc:
        ASSERTIONS += 1
        if exc.stop_code != stop_code:
            raise AssertionError(f"wrong STOP {exc.stop_code}; expected {stop_code}") from exc
    else:
        raise AssertionError(f"expected {stop_code}")


@contextmanager
def forced_runtime_style_cpu():
    original = torch.get_default_dtype()
    torch.set_default_dtype(torch.float64)
    try:
        yield ValueNorm(1, device=torch.device("cpu"))
    finally:
        torch.set_default_dtype(original)


def fingerprint(value_normalizer: ValueNorm):
    return E.fingerprint_component_v1(
        component_kind="live_valuenorm",
        owner_identity="live_valuenorm",
        value_normalizer=value_normalizer,
    )


def live_values(value_normalizer: ValueNorm) -> dict[str, torch.Tensor]:
    return {
        name: getattr(value_normalizer, name).detach().clone()
        for name in FIELDS
    }


def representation_probe(
    *, name: str, value_normalizer: ValueNorm, raw_batch: torch.Tensor
) -> dict[str, object]:
    native_pre = {key: value.detach().clone() for key, value in value_normalizer.state_dict().items()}
    live_pre = live_values(value_normalizer)
    pre = fingerprint(value_normalizer)
    repeat = fingerprint(value_normalizer)
    check(pre == repeat, f"{name}: nondeterministic fingerprint")
    check(len(pre.valuenorm_state) == 3, f"{name}: incomplete canonical field set")
    check(
        tuple(item.name.split(".")[-1] for item in pre.valuenorm_state) == FIELDS,
        f"{name}: wrong canonical field order",
    )
    check(all(item.tensor.finite for item in pre.valuenorm_state), f"{name}: nonfinite pre-state")

    value_normalizer.update(raw_batch)
    live_post = live_values(value_normalizer)
    post = fingerprint(value_normalizer)
    changed = tuple(field for field in FIELDS if not torch.equal(live_pre[field], live_post[field]))
    native_post = value_normalizer.state_dict()
    native_equal = tuple(native_pre) == tuple(native_post) and all(
        torch.equal(native_pre[key], native_post[key]) for key in native_pre
    )
    check(pre.fingerprint_digest != post.fingerprint_digest, f"{name}: canonical mutation missed")
    check(bool(changed), f"{name}: no live field changed")
    check(all(item.tensor.finite for item in post.valuenorm_state), f"{name}: nonfinite post-state")
    return {
        "name": name,
        "field_types": tuple(type(getattr(value_normalizer, field)).__name__ for field in FIELDS),
        "native_state_dict_keys": tuple(native_post),
        "native_pre_post_equal": native_equal,
        "canonical_fields": tuple(item.name.split(".")[-1] for item in post.valuenorm_state),
        "canonical_pre": pre.fingerprint_digest,
        "canonical_post": post.fingerprint_digest,
        "changed_fields": changed,
        "shapes": tuple(tuple(item.tensor.shape) for item in post.valuenorm_state),
        "dtypes": tuple(item.tensor.dtype for item in post.valuenorm_state),
        "devices": tuple(item.tensor.device for item in post.valuenorm_state),
        "live_updates": 1,
    }


def test_representation_matrix() -> dict[str, object]:
    zero_cpu = torch.zeros((4, 1), dtype=torch.float32)
    default = representation_probe(
        name="cpu_default_registered",
        value_normalizer=ValueNorm(1, device=torch.device("cpu")),
        raw_batch=zero_cpu,
    )
    with forced_runtime_style_cpu() as runtime_cpu:
        runtime = representation_probe(
            name="cpu_runtime_unregistered",
            value_normalizer=runtime_cpu,
            raw_batch=zero_cpu,
        )
    check(default["field_types"] == ("Parameter",) * 3, "CPU default must remain registered Parameters")
    check(runtime["field_types"] == ("Tensor",) * 3, "CPU runtime style must use ordinary Tensors")
    check(runtime["native_state_dict_keys"] == (), "CPU runtime native state_dict must expose blind spot")
    check(runtime["native_pre_post_equal"] is True, "CPU runtime native state_dict must miss mutation")
    check(runtime["changed_fields"] == ("debiasing_term",), "fresh zero batch must change debiasing term")

    if not torch.cuda.is_available():
        raise AssertionError("cuda:0 is required by B2-R5I-VF")
    cuda = representation_probe(
        name="cuda_runtime_unregistered",
        value_normalizer=ValueNorm(1, device=torch.device("cuda:0")),
        raw_batch=torch.tensor([[1.0], [-2.0], [3.5]], dtype=torch.float32, device="cuda:0"),
    )
    check(cuda["field_types"] == ("Tensor",) * 3, "CUDA runtime style must use ordinary Tensors")
    check(cuda["native_state_dict_keys"] == (), "CUDA native state_dict must expose blind spot")
    check(cuda["native_pre_post_equal"] is True, "CUDA native state_dict must miss mutation")
    check(cuda["changed_fields"] == FIELDS, "CUDA controlled batch must change all live fields")
    return {
        "probes": (default, runtime, cuda),
        "cpu_live_updates": 2,
        "cuda_live_updates": 1,
        "canonical_mutations_detected": 3,
        "native_state_dict_blind_spot_witnesses": 2,
    }


def test_fingerprint_fail_closed_matrix() -> dict[str, object]:
    registered = ValueNorm(1, device=torch.device("cpu"))
    with forced_runtime_style_cpu() as runtime:
        check(fingerprint(registered).fingerprint_digest == fingerprint(runtime).fingerprint_digest, "Parameter/Tensor logical identity")

    for missing in FIELDS:
        with forced_runtime_style_cpu() as candidate:
            delattr(candidate, missing)
            expect_stop(E.STOP_VALUENORM, lambda candidate=candidate: fingerprint(candidate))
    with forced_runtime_style_cpu() as candidate:
        candidate.running_mean = torch.zeros(2, dtype=torch.float32)
        expect_stop(E.STOP_VALUENORM, lambda: fingerprint(candidate))
    with forced_runtime_style_cpu() as candidate:
        candidate.running_mean = [0.0]
        expect_stop(E.STOP_VALUENORM, lambda: fingerprint(candidate))
    for field in FIELDS:
        with forced_runtime_style_cpu() as candidate:
            getattr(candidate, field).fill_(float("inf"))
            expect_stop(E.STOP_NONFINITE_VALUENORM_STATE, lambda candidate=candidate: fingerprint(candidate))

    with forced_runtime_style_cpu() as candidate:
        before = fingerprint(candidate).fingerprint_digest
        candidate.running_mean.add_(1.0)
        check(before != fingerprint(candidate).fingerprint_digest, "one-field change not detected")
    with forced_runtime_style_cpu() as candidate:
        before = fingerprint(candidate).fingerprint_digest
        candidate.debiasing_term.add_(1.0)
        check(before != fingerprint(candidate).fingerprint_digest, "scalar change not detected")
    return {"missing_fields": 3, "wrong_shape": 1, "unsupported_type": 1, "nonfinite_fields": 3}


def make_r4_cuda_proxy(*, permit_changes: dict[str, object] | None = None):
    context = R4H.make_context(suffix="vf-cuda")
    value_normalizer = ValueNorm(1, device=torch.device("cuda:0"))
    raw_target = torch.tensor([[1.0], [-2.0], [3.5]], dtype=torch.float32, device="cuda:0")
    indices = (0, 1, 2)
    pre = R4._valuenorm_digest(value_normalizer)
    critic_fp = E.canonical_digest_v1("vf-critic")
    optimizer_fp = E.canonical_digest_v1("vf-optimizer")
    permit = R4._make_permit_v1(
        authority=context.authority,
        component_kind="live_valuenorm",
        epoch=0,
        minibatch=0,
        indices=indices,
        raw_digest=E.fingerprint_tensor_v1(raw_target).content_digest,
        operation=H.C.B2RPermitOperationV1.VALUENORM_UPDATE,
        critic_parameter_digest=critic_fp,
        critic_optimizer_digest=optimizer_fp,
        valuenorm_digest=pre,
    )
    if permit_changes:
        permit = replace(permit, **permit_changes)
    counter = R4.B2R4ExecutionCounterV1()
    proxy = R4.B2R4PermittedLiveValueNormProxyV1(
        value_normalizer=value_normalizer,
        authority=context.authority,
        route_state=R4.B2R4RouteStateV1(),
        ledger=R4.B2R4PermitLedgerV1(),
        permit=permit,
        epoch=0,
        minibatch=0,
        canonical_indices=indices,
        raw_target=raw_target,
        critic_parameter_fingerprint=critic_fp,
        critic_optimizer_fingerprint=optimizer_fp,
        counter=counter,
    )
    return proxy, counter, raw_target, pre


def test_r4_cuda_evidence_and_permits() -> dict[str, object]:
    proxy, counter, raw, pre = make_r4_cuda_proxy()
    proxy.update(raw)
    proxy.normalize(raw)
    proxy.normalize(raw)
    receipt = proxy.receipt()
    check(counter.live_valuenorm_executed == 1, "R4 CUDA update count")
    check(receipt.pre_fingerprint == pre, "R4 CUDA prestate binding")
    check(receipt.pre_fingerprint != receipt.post_fingerprint, "R4 CUDA mutation attribution")
    check(receipt.state_mutated and receipt.finite, "R4 CUDA finite mutation receipt")
    check(receipt.normalize_same_object and receipt.normalize_same_digest, "R4 CUDA same-raw normalization")
    check(receipt.debiasing_term_values != (0.0,), "R4 CUDA scalar state evidence")

    stale, _, stale_raw, _ = make_r4_cuda_proxy(
        permit_changes={"expected_valuenorm_fingerprint": E.canonical_digest_v1("stale")}
    )
    expect_stop(E.STOP_VALUENORM, lambda: stale.update(stale_raw))
    wrong, _, wrong_raw, _ = make_r4_cuda_proxy(
        permit_changes={"expected_valuenorm_fingerprint": E.canonical_digest_v1("wrong")}
    )
    expect_stop(E.STOP_VALUENORM, lambda: wrong.update(wrong_raw))
    bad_minibatch, _, bad_minibatch_raw, _ = make_r4_cuda_proxy(
        permit_changes={"minibatch": 1}
    )
    expect_stop(E.STOP_VALUENORM, lambda: bad_minibatch.update(bad_minibatch_raw))
    bad_raw, _, bad_raw_tensor, _ = make_r4_cuda_proxy(
        permit_changes={"raw_target_digest": E.canonical_digest_v1("wrong-raw")}
    )
    expect_stop(E.STOP_VALUENORM, lambda: bad_raw.update(bad_raw_tensor))
    duplicate, duplicate_counter, duplicate_raw, _ = make_r4_cuda_proxy()
    duplicate.update(duplicate_raw)
    expect_stop(E.STOP_VALUENORM, lambda: duplicate.update(duplicate_raw))
    check(duplicate_counter.live_valuenorm_executed == 1, "duplicate permit caused second live update")
    return {
        "successful_sequences": 1,
        "live_updates": 2,
        "receipts": 1,
        "permit_faults": 5,
        "canonical_mutations_detected": 2,
        "receipt_pre": receipt.pre_fingerprint,
        "receipt_post": receipt.post_fingerprint,
        "running_mean_digest": receipt.running_mean_digest,
        "running_mean_sq_digest": receipt.running_mean_sq_digest,
        "debiasing_term_digest": receipt.debiasing_term_digest,
        "running_mean_values": receipt.running_mean_values,
        "running_mean_sq_values": receipt.running_mean_sq_values,
        "debiasing_term_values": receipt.debiasing_term_values,
    }


if __name__ == "__main__":
    matrix = test_representation_matrix()
    failures = test_fingerprint_fail_closed_matrix()
    r4_cuda = test_r4_cuda_evidence_and_permits()
    print(json.dumps({
        "status": "PASS",
        "assertions": ASSERTIONS,
        "representation_matrix": matrix,
        "failure_matrix": failures,
        "r4_cuda": r4_cuda,
        "isaac_actions": 0,
        "checkpoint_weight_io": 0,
        "training_evaluation_playback": 0,
    }, sort_keys=True))
