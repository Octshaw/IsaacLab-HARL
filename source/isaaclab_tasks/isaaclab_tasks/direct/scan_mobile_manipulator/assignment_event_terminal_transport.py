"""B-private bounded historical transport for exact terminal handoff.

This module copies authoritative runtime terminal artifacts into immutable
one-step values.  It owns no terminal slot, P2, Store, fence, environment,
consumer capability, acknowledgement, learner, critic, or policy authority.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TERMINAL_TRANSPORT_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_terminal_transport"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_TERMINAL_TRANSPORT_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event terminal transport source must "
        "execute under its canonical module key; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TERMINAL_TRANSPORT_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping
from dataclasses import dataclass, field, replace

import torch

from .assignment_initial_claim_runtime import _EventRuntimeCurrentPublication
from .assignment_lifecycle_transaction_runtime import (
    _TerminalHandoffArtifact,
    _TerminalTransitionKey,
)
from .assignment_lifecycle_transition_contract import TerminationReason
from .assignment_event_terminal_critic_sidecar import EventTerminalCriticSidecarV2


_HISTORICAL_ROW_FACTORY_CAPABILITY = object()
_RESULT_ROW_TENSOR_FIELDS = (
    "completed_tasks",
    "released_tasks",
    "new_failed_pairs",
    "updated_failed_pairs",
    "new_team_infeasible_tasks",
    "updated_task_state",
    "updated_robot_state",
    "updated_ownership",
)


class EventTerminalTransportError(RuntimeError):
    """Typed copy/validation failure that always occurs before batch ACK."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str,
        expected: object = None,
        actual: object = None,
    ) -> None:
        self.failure_code = failure_code
        self.stage = stage
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; stage={stage!r}; "
            f"expected={expected!r}; actual={actual!r}"
        )


def _clone_tensor(value: object, *, field_name: str) -> torch.Tensor:
    if type(value) is not torch.Tensor or value.requires_grad:
        raise EventTerminalTransportError(
            "terminal historical evidence requires an exact no-grad tensor",
            failure_code="historical_tensor_contract",
            stage="terminal_history_copy",
            expected=(field_name, torch.Tensor, False),
            actual=(type(value), getattr(value, "requires_grad", None)),
        )
    return value.detach().clone().contiguous()


def _copy_lifecycle_events(events: object) -> tuple[object, ...]:
    if type(events) is not tuple:
        raise EventTerminalTransportError(
            "terminal lifecycle events must be an exact tuple",
            failure_code="historical_events_contract",
            stage="terminal_history_copy",
            expected=tuple,
            actual=type(events),
        )
    copied: list[object] = []
    for event in events:
        try:
            copied.append(replace(event, payload=replace(event.payload)))
        except (AttributeError, TypeError, ValueError) as exc:
            raise EventTerminalTransportError(
                "terminal lifecycle event is not a copyable immutable value",
                failure_code="historical_event_copy",
                stage="terminal_history_copy",
                expected="frozen lifecycle event and payload",
                actual=type(event),
            ) from exc
    return tuple(copied)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventTerminalHistoricalRow:
    """One bounded no-alias historical terminal row copied before ACK-A."""

    env_id: int
    episode_generation: int
    transition_generation: int
    termination_reason: int
    terminated: bool
    truncated: bool
    facts_consume_token: int
    authority_receipt_id: int
    result_schema_version: str
    authority_contract_version: str
    facts_producer_id: object
    authority_id: object
    published_store_version: int
    lifecycle_events: tuple[object, ...] = field(repr=False)
    optional_sidecar: EventTerminalCriticSidecarV2 | None = field(default=None, repr=False)
    _coverage_after_transition: torch.Tensor = field(repr=False)
    _completion_count: torch.Tensor = field(repr=False)
    _completed_tasks: torch.Tensor = field(repr=False)
    _released_tasks: torch.Tensor = field(repr=False)
    _new_failed_pairs: torch.Tensor = field(repr=False)
    _updated_failed_pairs: torch.Tensor = field(repr=False)
    _new_team_infeasible_tasks: torch.Tensor = field(repr=False)
    _updated_task_state: torch.Tensor = field(repr=False)
    _updated_robot_state: torch.Tensor = field(repr=False)
    _updated_ownership: torch.Tensor = field(repr=False)

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise EventTerminalTransportError(
            "terminal historical rows require the bounded transport factory",
            failure_code="historical_factory_required",
            stage="terminal_history_copy",
            expected="facade terminal-copy helper",
            actual="direct constructor",
        )

    @classmethod
    def _create(
        cls,
        *,
        artifact: _TerminalHandoffArtifact,
        factory_capability: object,
    ) -> "EventTerminalHistoricalRow":
        if (
            factory_capability is not _HISTORICAL_ROW_FACTORY_CAPABILITY
            or type(artifact) is not _TerminalHandoffArtifact
        ):
            raise EventTerminalTransportError(
                "terminal historical copy requires an exact captured artifact",
                failure_code="historical_factory",
                stage="terminal_history_copy",
                expected=_TerminalHandoffArtifact,
                actual=type(artifact),
            )
        key = artifact.key
        if type(key) is not _TerminalTransitionKey:
            raise EventTerminalTransportError(
                "captured terminal artifact has a noncanonical key",
                failure_code="historical_key_type",
                stage="terminal_history_copy",
                expected=_TerminalTransitionKey,
                actual=type(key),
            )
        result = artifact.result
        result.validate_finalized()
        result_mapping = result.to_mapping()
        env_ids = result_mapping["env_id"]
        matching = torch.nonzero(env_ids == key.env_id, as_tuple=False).flatten()
        if int(matching.numel()) != 1:
            raise EventTerminalTransportError(
                "captured terminal env has no unique finalized result row",
                failure_code="historical_result_row",
                stage="terminal_history_copy",
                expected=key.env_id,
                actual=env_ids,
            )
        row = int(matching[0].item())
        observed_key = (
            int(result_mapping["env_id"][row].item()),
            int(result_mapping["episode_generation"][row].item()),
            int(result_mapping["transition_generation"][row].item()),
        )
        exact_key = (key.env_id, key.episode_generation, key.transition_generation)
        if observed_key != exact_key:
            raise EventTerminalTransportError(
                "copied finalized result row differs from the exact terminal key",
                failure_code="historical_key_binding",
                stage="terminal_history_copy",
                expected=exact_key,
                actual=observed_key,
            )

        view = artifact.published_view
        state = view.lifecycle_state
        state_env_ids = state.env_id
        state_matching = torch.nonzero(state_env_ids == key.env_id, as_tuple=False).flatten()
        if int(state_matching.numel()) != 1:
            raise EventTerminalTransportError(
                "captured terminal env has no unique published lifecycle row",
                failure_code="historical_state_row",
                stage="terminal_history_copy",
                expected=key.env_id,
                actual=state_env_ids,
            )
        state_row = int(state_matching[0].item())
        source_tensors = {
            name: result_mapping[name][row]
            for name in _RESULT_ROW_TENSOR_FIELDS
        }
        source_tensors["coverage_after_transition"] = artifact.coverage_after_transition
        source_tensors["completion_count"] = state.completion_count[state_row]
        copied_tensors = {
            name: _clone_tensor(value, field_name=name)
            for name, value in source_tensors.items()
        }
        for name, source in source_tensors.items():
            copied = copied_tensors[name]
            if source.numel() and source.data_ptr() == copied.data_ptr():
                raise EventTerminalTransportError(
                    "terminal historical tensor aliases runtime evidence",
                    failure_code="historical_tensor_alias",
                    stage="terminal_history_copy",
                    expected=f"detached storage for {name}",
                    actual="shared data_ptr",
                )
        source_sidecar = artifact.optional_sidecar
        if source_sidecar is None:
            copied_sidecar = None
        else:
            if type(source_sidecar) is not EventTerminalCriticSidecarV2:
                raise EventTerminalTransportError(
                    "runtime terminal sidecar has a noncanonical type",
                    failure_code="historical_sidecar_type",
                    stage="terminal_history_copy",
                    expected=EventTerminalCriticSidecarV2,
                    actual=type(source_sidecar),
                )
            source_sidecar._validate_artifact_binding(
                key=key,
                termination_reason=artifact.termination_reason,
                terminated=artifact.terminated,
                truncated=artifact.truncated,
                published_store_version=view.store_version,
            )
            copied_sidecar = source_sidecar._clone_for_historical()
            if copied_sidecar is source_sidecar:
                raise EventTerminalTransportError(
                    "terminal sidecar historical copy retained runtime identity",
                    failure_code="historical_sidecar_alias",
                    stage="terminal_history_copy",
                    expected="distinct immutable sidecar value",
                    actual="same object identity",
                )
            source_audit = source_sidecar._terminal_audit_projection._semantic_evidence
            copied_audit = copied_sidecar._terminal_audit_projection._semantic_evidence
            if source_audit.numel() and source_audit.data_ptr() == copied_audit.data_ptr():
                raise EventTerminalTransportError(
                    "terminal audit projection aliases runtime sidecar storage",
                    failure_code="historical_sidecar_alias",
                    stage="terminal_history_copy",
                    expected="detached audit storage",
                    actual="shared data_ptr",
                )
            source_bootstrap = source_sidecar._bootstrap_critic_obs
            copied_bootstrap = copied_sidecar._bootstrap_critic_obs
            if (
                source_bootstrap is not None
                and copied_bootstrap is not None
                and source_bootstrap.numel()
                and source_bootstrap.data_ptr() == copied_bootstrap.data_ptr()
            ):
                raise EventTerminalTransportError(
                    "timeout bootstrap observation aliases runtime sidecar storage",
                    failure_code="historical_sidecar_alias",
                    stage="terminal_history_copy",
                    expected="detached bootstrap storage",
                    actual="shared data_ptr",
                )

        instance = object.__new__(cls)
        for name, value in (
            ("env_id", key.env_id),
            ("episode_generation", key.episode_generation),
            ("transition_generation", key.transition_generation),
            ("termination_reason", artifact.termination_reason),
            ("terminated", artifact.terminated),
            ("truncated", artifact.truncated),
            ("facts_consume_token", artifact.facts_consume_token),
            ("authority_receipt_id", artifact.authority_receipt_id),
            ("result_schema_version", result.schema_version),
            ("authority_contract_version", result.authority_contract_version),
            ("facts_producer_id", result.facts_producer_id),
            ("authority_id", result.authority_id),
            ("published_store_version", view.store_version),
            ("lifecycle_events", _copy_lifecycle_events(artifact.lifecycle_events)),
            ("optional_sidecar", copied_sidecar),
        ):
            object.__setattr__(instance, name, value)
        for name, value in copied_tensors.items():
            object.__setattr__(instance, f"_{name}", value)
        return instance

    @property
    def key(self) -> _TerminalTransitionKey:
        return _TerminalTransitionKey(
            self.env_id,
            self.episode_generation,
            self.transition_generation,
        )

    def _tensor_copy(self, name: str) -> torch.Tensor:
        return getattr(self, f"_{name}").detach().clone().contiguous()

    @property
    def coverage_after_transition(self) -> torch.Tensor:
        return self._tensor_copy("coverage_after_transition")

    @property
    def completion_count(self) -> torch.Tensor:
        return self._tensor_copy("completion_count")

    @property
    def completed_tasks(self) -> torch.Tensor:
        return self._tensor_copy("completed_tasks")

    @property
    def released_tasks(self) -> torch.Tensor:
        return self._tensor_copy("released_tasks")

    @property
    def new_failed_pairs(self) -> torch.Tensor:
        return self._tensor_copy("new_failed_pairs")

    @property
    def updated_failed_pairs(self) -> torch.Tensor:
        return self._tensor_copy("updated_failed_pairs")

    @property
    def new_team_infeasible_tasks(self) -> torch.Tensor:
        return self._tensor_copy("new_team_infeasible_tasks")

    @property
    def updated_task_state(self) -> torch.Tensor:
        return self._tensor_copy("updated_task_state")

    @property
    def updated_robot_state(self) -> torch.Tensor:
        return self._tensor_copy("updated_robot_state")

    @property
    def updated_ownership(self) -> torch.Tensor:
        return self._tensor_copy("updated_ownership")


def _aggregate_done_rows(
    value: object,
    *,
    field_name: str,
    num_envs: int,
    device: torch.device,
) -> torch.Tensor:
    values = tuple(value.values()) if isinstance(value, Mapping) else (value,)
    if not values:
        raise EventTerminalTransportError(
            "environment terminal mapping must not be empty",
            failure_code="environment_done_contract",
            stage="terminal_history_validate",
            expected=f"nonempty {field_name} tensors",
            actual=(),
        )
    aggregate = torch.zeros((num_envs,), dtype=torch.bool, device=device)
    for item in values:
        if (
            type(item) is not torch.Tensor
            or item.dtype is not torch.bool
            or item.device != device
            or tuple(item.shape) != (num_envs,)
            or item.requires_grad
        ):
            raise EventTerminalTransportError(
                "environment terminal flags have an invalid tensor contract",
                failure_code="environment_done_contract",
                stage="terminal_history_validate",
                expected=(field_name, torch.bool, (num_envs,), device, False),
                actual=(type(item), getattr(item, "dtype", None), getattr(item, "shape", None)),
            )
        aggregate |= item
    return aggregate


def _copy_and_validate_terminal_history(
    *,
    captured_artifacts: tuple[_TerminalHandoffArtifact, ...],
    environment_result: object,
    current_publication: _EventRuntimeCurrentPublication,
) -> tuple[EventTerminalHistoricalRow, ...]:
    """Copy and fully validate one synchronous terminal batch before ACK-A."""

    if type(captured_artifacts) is not tuple or any(
        type(item) is not _TerminalHandoffArtifact for item in captured_artifacts
    ):
        raise EventTerminalTransportError(
            "terminal capture must be the exact immutable runtime tuple",
            failure_code="terminal_capture_contract",
            stage="terminal_history_validate",
            expected="tuple[_TerminalHandoffArtifact, ...]",
            actual=type(captured_artifacts),
        )
    env_ids = tuple(item.key.env_id for item in captured_artifacts)
    if env_ids != tuple(sorted(env_ids)) or len(set(env_ids)) != len(env_ids):
        raise EventTerminalTransportError(
            "captured terminal artifacts are not canonical unique env rows",
            failure_code="terminal_capture_order",
            stage="terminal_history_validate",
            expected="unique ascending env IDs",
            actual=env_ids,
        )
    if type(current_publication) is not _EventRuntimeCurrentPublication:
        raise EventTerminalTransportError(
            "terminal history validation requires exact current P2",
            failure_code="terminal_current_publication",
            stage="terminal_history_validate",
            expected=_EventRuntimeCurrentPublication,
            actual=type(current_publication),
        )
    if type(environment_result) is not tuple or len(environment_result) != 5:
        raise EventTerminalTransportError(
            "terminal history requires the exact physical five-tuple",
            failure_code="environment_result_contract",
            stage="terminal_history_validate",
            expected="five-tuple",
            actual=type(environment_result),
        )

    current_env_ids = current_publication.env_id
    num_envs = int(current_env_ids.numel())
    device = current_env_ids.device
    terminated = _aggregate_done_rows(
        environment_result[2],
        field_name="terminated",
        num_envs=num_envs,
        device=device,
    )
    truncated = _aggregate_done_rows(
        environment_result[3],
        field_name="truncated",
        num_envs=num_envs,
        device=device,
    )
    done_rows = torch.nonzero(terminated | truncated, as_tuple=False).flatten().tolist()
    returned_env_ids = tuple(
        sorted(int(current_env_ids[row].item()) for row in done_rows)
    )
    if returned_env_ids != env_ids:
        raise EventTerminalTransportError(
            "physical terminal rows differ from captured terminal artifact rows",
            failure_code="terminal_return_capture_mismatch",
            stage="terminal_history_validate",
            expected=env_ids,
            actual=returned_env_ids,
        )

    copied = tuple(
        EventTerminalHistoricalRow._create(
            artifact=artifact,
            factory_capability=_HISTORICAL_ROW_FACTORY_CAPABILITY,
        )
        for artifact in captured_artifacts
    )
    if len(copied) != len(captured_artifacts):
        raise EventTerminalTransportError(
            "terminal historical copy cardinality differs from capture",
            failure_code="terminal_copy_cardinality",
            stage="terminal_history_validate",
            expected=len(captured_artifacts),
            actual=len(copied),
        )

    current_episode = current_publication.episode_generation
    current_transition = current_publication.transition_generation
    current_reason = current_publication.lifecycle_state.termination_reason
    current_terminated = current_publication.terminated
    current_truncated = current_publication.truncated
    if current_publication.result is not None:
        raise EventTerminalTransportError(
            "terminal handoff current P2 must be the post-autoreset publication",
            failure_code="terminal_current_history_overlap",
            stage="terminal_history_validate",
            expected="current result is None",
            actual=type(current_publication.result),
        )
    row_by_env = {
        int(current_env_ids[row].item()): row for row in range(num_envs)
    }
    for artifact, historical in zip(captured_artifacts, copied, strict=True):
        key = artifact.key
        row = row_by_env[key.env_id]
        historical_key = (
            historical.env_id,
            historical.episode_generation,
            historical.transition_generation,
        )
        exact_key = (
            key.env_id,
            key.episode_generation,
            key.transition_generation,
        )
        if (
            historical_key != exact_key
            or historical.termination_reason != artifact.termination_reason
            or historical.terminated is not artifact.terminated
            or historical.truncated is not artifact.truncated
            or historical.facts_consume_token != artifact.facts_consume_token
            or historical.authority_receipt_id != artifact.authority_receipt_id
            or (historical.optional_sidecar is None) != (artifact.optional_sidecar is None)
        ):
            raise EventTerminalTransportError(
                "copied historical row differs from authoritative terminal evidence",
                failure_code="terminal_copy_binding",
                stage="terminal_history_validate",
                expected=exact_key,
                actual=historical_key,
            )
        if historical.optional_sidecar is not None:
            historical.optional_sidecar._validate_artifact_binding(
                key=key,
                termination_reason=artifact.termination_reason,
                terminated=artifact.terminated,
                truncated=artifact.truncated,
                published_store_version=artifact.published_view.store_version,
            )
        if len(historical.lifecycle_events) != len(artifact.lifecycle_events) or any(
            copied_event is source_event or copied_event != source_event
            for copied_event, source_event in zip(
                historical.lifecycle_events,
                artifact.lifecycle_events,
                strict=True,
            )
        ):
            raise EventTerminalTransportError(
                "copied lifecycle events differ from or retain runtime event objects",
                failure_code="terminal_event_copy_binding",
                stage="terminal_history_validate",
                expected="equal value copies with distinct identity",
                actual=(historical.lifecycle_events, artifact.lifecycle_events),
            )
        if (
            bool(terminated[row].item()) is not artifact.terminated
            or bool(truncated[row].item()) is not artifact.truncated
        ):
            raise EventTerminalTransportError(
                "physical done flags differ from authoritative terminal artifact",
                failure_code="terminal_done_binding",
                stage="terminal_history_validate",
                expected=(artifact.terminated, artifact.truncated),
                actual=(bool(terminated[row].item()), bool(truncated[row].item())),
            )
        current_binding = (
            int(current_episode[row].item()),
            int(current_transition[row].item()),
            int(current_reason[row].item()),
            bool(current_terminated[row].item()),
            bool(current_truncated[row].item()),
        )
        expected_current = (
            key.episode_generation + 1,
            key.transition_generation,
            int(TerminationReason.NONE),
            False,
            False,
        )
        if current_binding != expected_current:
            raise EventTerminalTransportError(
                "terminal history and current reset P2 lifetimes are not separated",
                failure_code="terminal_current_history_separation",
                stage="terminal_history_validate",
                expected=expected_current,
                actual=current_binding,
            )
    return copied


__all__: tuple[str, ...] = ()
