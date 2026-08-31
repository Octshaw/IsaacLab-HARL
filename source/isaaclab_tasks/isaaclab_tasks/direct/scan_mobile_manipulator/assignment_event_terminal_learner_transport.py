"""Private B2-I5a terminal-history transport and timeout critic evaluation.

The runtime terminal artifact has already been copied and acknowledged before
anything in this module runs.  These values own bounded learner evidence only;
they are not a terminal slot, lifecycle authority, P2 view, or ACK capability.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TERMINAL_LEARNER_TRANSPORT_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_terminal_learner_transport"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_TERMINAL_LEARNER_TRANSPORT_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event terminal learner transport must "
        "execute under its canonical module key; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TERMINAL_LEARNER_TRANSPORT_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
import torch

from .assignment_event_policy_decision import EventPolicyDecisionBundle
from .assignment_event_runtime_facade import (
    EventFacadeProposalStepResult,
    EventFacadeStepResult,
)
from .assignment_event_terminal_critic_sidecar import (
    EventTerminalCriticSidecarV2,
    TerminalAuditProjectionV2,
)
from .assignment_event_terminal_transport import EventTerminalHistoricalRow
from .assignment_lifecycle_transition_contract import TerminationReason
from .assignment_profile_contract import AssignmentProfileName


EVENT_TERMINAL_LEARNER_RECORD_V2 = "event_terminal_learner_record_v2"
EVENT_TERMINAL_LEARNER_INFO_KEY_V2 = "_assignment_event_terminal_learner_v2"
EVENT_LEARNER_TRANSITION_EXPECTATION_V2 = "event_learner_transition_expectation_v2"
EVENT_TERMINAL_CORRELATION_BATCH_V2 = "event_terminal_correlation_batch_v2"
EVENT_TIMEOUT_CRITIC_INPUT_BATCH_V2 = "event_timeout_critic_input_batch_v2"
EVENT_TERMINAL_CRITIC_EVALUATION_BATCH_V2 = (
    "event_terminal_critic_evaluation_batch_v2"
)

_TRUE_TERMINAL_REASONS = (
    int(TerminationReason.ALL_TASKS_COMPLETED),
    int(TerminationReason.NO_FEASIBLE_TASKS_REMAIN),
)
_TERMINAL_REASONS = _TRUE_TERMINAL_REASONS + (int(TerminationReason.TIME_LIMIT),)


class EventTerminalLearnerTransportError(RuntimeError):
    """Fail-closed learner transport, correlation, or critic-input error."""

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


def _fail(
    message: str,
    *,
    failure_code: str,
    stage: str,
    expected: object = None,
    actual: object = None,
) -> None:
    raise EventTerminalLearnerTransportError(
        message,
        failure_code=failure_code,
        stage=stage,
        expected=expected,
        actual=actual,
    )


def _readonly_tensor(value: torch.Tensor) -> torch.Tensor:
    return value.detach().clone().contiguous()


def _readonly_metadata(value: object) -> object:
    if value is None or type(value) in (bool, int, float, str, torch.dtype, torch.device):
        return value
    if type(value) is tuple:
        return tuple(_readonly_metadata(item) for item in value)
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _readonly_metadata(item) for key, item in value.items()}
        )
    _fail(
        "learner provenance contains an unbounded or mutable value",
        failure_code="learner_metadata_contract",
        stage="learner_record_copy",
        expected="bounded scalar/tuple/mapping metadata",
        actual=type(value),
    )


def _generation_tuple(value: object, *, field_name: str) -> tuple[int, ...]:
    if (
        type(value) is not torch.Tensor
        or value.dtype is not torch.int64
        or value.ndim != 1
        or value.requires_grad
    ):
        _fail(
            "publication generation tensor has an invalid contract",
            failure_code="expectation_generation_contract",
            stage="expectation_capture",
            expected=(field_name, torch.int64, "[E]", False),
            actual=(type(value), getattr(value, "dtype", None), getattr(value, "shape", None)),
        )
    values = tuple(int(item) for item in value.detach().cpu().tolist())
    if any(item < -1 for item in values):
        _fail(
            "publication generation is outside the canonical range",
            failure_code="expectation_generation_range",
            stage="expectation_capture",
            expected=f"{field_name} >= -1",
            actual=values,
        )
    return values


@dataclass(frozen=True, slots=True)
class EventTerminalCorrelationKeyV2:
    """Bounded learner correlation value; never a lifecycle clock authority."""

    env_id: int
    episode_generation: int
    transition_generation: int

    def __post_init__(self) -> None:
        values = (self.env_id, self.episode_generation, self.transition_generation)
        if any(type(value) is not int for value in values) or any(value < 0 for value in values):
            _fail(
                "terminal correlation key requires nonnegative exact integers",
                failure_code="terminal_correlation_key",
                stage="learner_record_copy",
                expected="(env>=0, episode>=0, transition>=0)",
                actual=values,
            )

    @property
    def value(self) -> tuple[int, int, int]:
        return (self.env_id, self.episode_generation, self.transition_generation)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventLearnerTransitionExpectationV2:
    """Runner-owned pre-step identity used to correlate the completed slot t."""

    schema_version: str
    profile_name: str
    p2_publication_identity: object = field(repr=False)
    open_window_identity: object = field(repr=False)
    env_ids: tuple[int, ...]
    episode_generations: tuple[int, ...]
    source_transition_generations: tuple[int, ...]
    expected_transition_generations: tuple[int, ...]

    @classmethod
    def _create(cls, *, decision_bundle: EventPolicyDecisionBundle) -> "EventLearnerTransitionExpectationV2":
        if type(decision_bundle) is not EventPolicyDecisionBundle:
            _fail(
                "transition expectation requires the exact sealed I2 bundle",
                failure_code="expectation_bundle_type",
                stage="expectation_capture",
                expected=EventPolicyDecisionBundle,
                actual=type(decision_bundle),
            )
        identity = decision_bundle.evidence_identity
        episodes = tuple(identity.episode_generations)
        transitions = tuple(identity.transition_generations)
        if not episodes or len(episodes) != len(transitions):
            _fail(
                "decision identity does not describe one fixed E batch",
                failure_code="expectation_cardinality",
                stage="expectation_capture",
                expected="equal nonzero episode/transition cardinality",
                actual=(len(episodes), len(transitions)),
            )
        if any(type(item) is not int or item < 0 for item in episodes) or any(
            type(item) is not int or item < -1 for item in transitions
        ):
            _fail(
                "decision generations violate the canonical range",
                failure_code="expectation_generation_range",
                stage="expectation_capture",
                expected="episode>=0 and source transition>=-1",
                actual=(episodes, transitions),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "schema_version", EVENT_LEARNER_TRANSITION_EXPECTATION_V2)
        object.__setattr__(instance, "profile_name", decision_bundle.profile_name)
        object.__setattr__(instance, "p2_publication_identity", identity.p2_publication_identity)
        object.__setattr__(instance, "open_window_identity", identity.open_window_identity)
        object.__setattr__(instance, "env_ids", tuple(range(len(episodes))))
        object.__setattr__(instance, "episode_generations", episodes)
        object.__setattr__(instance, "source_transition_generations", transitions)
        object.__setattr__(
            instance,
            "expected_transition_generations",
            tuple(item + 1 for item in transitions),
        )
        return instance

    def expected_key(self, env_id: int) -> EventTerminalCorrelationKeyV2:
        if type(env_id) is not int or env_id < 0 or env_id >= len(self.env_ids):
            _fail(
                "terminal expectation env index is outside the fixed batch",
                failure_code="expectation_env_id",
                stage="terminal_correlation",
                expected=f"0 <= env_id < {len(self.env_ids)}",
                actual=env_id,
            )
        return EventTerminalCorrelationKeyV2(
            env_id,
            self.episode_generations[env_id],
            self.expected_transition_generations[env_id],
        )


def capture_event_learner_transition_expectation_v2(
    decision_bundle: EventPolicyDecisionBundle,
) -> EventLearnerTransitionExpectationV2:
    """Capture the exact pre-step decision identity without adding a clock."""

    return EventLearnerTransitionExpectationV2._create(decision_bundle=decision_bundle)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventTerminalLearnerRecordV2:
    """Immutable learner-owned copy of one already-ACK-safe historical row."""

    schema_version: str
    profile_name: str
    correlation_key: EventTerminalCorrelationKeyV2
    termination_reason: int
    terminated: bool
    truncated: bool
    result_schema_version: str
    authority_contract_version: str
    published_store_version: int
    sidecar_schema_version: str
    profile_schema_version: str
    scale_contract_version: str
    critic_schema_version: str
    critic_dimension: int
    critic_dtype: torch.dtype
    critic_device: torch.device
    bootstrap_projection_valid: bool
    source_p2_publication_identity: object = field(repr=False)
    terminal_audit: TerminalAuditProjectionV2 = field(repr=False)
    physical_provenance: Mapping[str, object] = field(repr=False)
    _bootstrap_critic_obs: torch.Tensor | None = field(repr=False)

    @classmethod
    def _create_from_historical(
        cls, *, historical: EventTerminalHistoricalRow
    ) -> "EventTerminalLearnerRecordV2":
        if type(historical) is not EventTerminalHistoricalRow:
            _fail(
                "learner record requires the exact bounded historical row",
                failure_code="learner_historical_type",
                stage="learner_record_copy",
                expected=EventTerminalHistoricalRow,
                actual=type(historical),
            )
        reason = historical.termination_reason
        expected_flags = (
            (False, True)
            if reason == int(TerminationReason.TIME_LIMIT)
            else (True, False)
        )
        if reason not in _TERMINAL_REASONS or (
            historical.terminated,
            historical.truncated,
        ) != expected_flags:
            _fail(
                "historical reason and done flags are inconsistent",
                failure_code="learner_reason_done",
                stage="learner_record_copy",
                expected=(reason, expected_flags),
                actual=(reason, historical.terminated, historical.truncated),
            )
        sidecar = historical.optional_sidecar
        if type(sidecar) is not EventTerminalCriticSidecarV2:
            _fail(
                "I5a terminal history requires the exact I4 sidecar",
                failure_code="learner_sidecar_missing",
                stage="learner_record_copy",
                expected=EventTerminalCriticSidecarV2,
                actual=type(sidecar),
            )
        sidecar._validate_artifact_binding(
            key=historical.key,
            termination_reason=reason,
            terminated=historical.terminated,
            truncated=historical.truncated,
            published_store_version=historical.published_store_version,
        )
        audit = sidecar.terminal_audit_projection
        key = EventTerminalCorrelationKeyV2(
            historical.env_id,
            historical.episode_generation,
            historical.transition_generation,
        )
        audit_binding = (
            audit.env_id,
            audit.episode_generation,
            audit.transition_generation,
            audit.termination_reason,
            audit.projection_mode,
        )
        expected_audit = (*key.value, reason, "TERMINAL_AUDIT")
        if audit_binding != expected_audit:
            _fail(
                "terminal audit metadata differs from the exact terminal row",
                failure_code="learner_audit_binding",
                stage="learner_record_copy",
                expected=expected_audit,
                actual=audit_binding,
            )
        bootstrap = sidecar.bootstrap_critic_obs
        timeout = reason == int(TerminationReason.TIME_LIMIT)
        if sidecar.bootstrap_projection_valid is not timeout or (bootstrap is not None) is not timeout:
            _fail(
                "timeout bootstrap presence differs from the final reason",
                failure_code="learner_bootstrap_presence",
                stage="learner_record_copy",
                expected=timeout,
                actual=(sidecar.bootstrap_projection_valid, bootstrap is not None),
            )
        if bootstrap is not None and (
            bootstrap.ndim != 1
            or bootstrap.shape != (sidecar.critic_dimension,)
            or bootstrap.dtype is not torch.float32
            or bootstrap.device != sidecar.critic_device
            or bootstrap.requires_grad
            or not bool(torch.isfinite(bootstrap).all().item())
        ):
            _fail(
                "historical bootstrap observation violates the critic contract",
                failure_code="learner_bootstrap_contract",
                stage="learner_record_copy",
                expected=(sidecar.critic_dimension, torch.float32, sidecar.critic_device, False),
                actual=(
                    getattr(bootstrap, "shape", None),
                    getattr(bootstrap, "dtype", None),
                    getattr(bootstrap, "device", None),
                    getattr(bootstrap, "requires_grad", None),
                ),
            )
        instance = object.__new__(cls)
        values = (
            ("schema_version", EVENT_TERMINAL_LEARNER_RECORD_V2),
            ("profile_name", AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value),
            ("correlation_key", key),
            ("termination_reason", reason),
            ("terminated", historical.terminated),
            ("truncated", historical.truncated),
            ("result_schema_version", historical.result_schema_version),
            ("authority_contract_version", historical.authority_contract_version),
            ("published_store_version", historical.published_store_version),
            ("sidecar_schema_version", sidecar.schema_version),
            ("profile_schema_version", sidecar.profile_schema_version),
            ("scale_contract_version", sidecar.scale_contract_version),
            ("critic_schema_version", sidecar.critic_schema_version),
            ("critic_dimension", sidecar.critic_dimension),
            ("critic_dtype", sidecar.critic_dtype),
            ("critic_device", sidecar.critic_device),
            ("bootstrap_projection_valid", sidecar.bootstrap_projection_valid),
            ("source_p2_publication_identity", sidecar.source_p2_publication_identity),
            ("terminal_audit", audit._clone()),
            ("physical_provenance", _readonly_metadata(sidecar.physical_provenance)),
            (
                "_bootstrap_critic_obs",
                None if bootstrap is None else _readonly_tensor(bootstrap),
            ),
        )
        for name, value in values:
            object.__setattr__(instance, name, value)
        return instance

    @property
    def env_id(self) -> int:
        return self.correlation_key.env_id

    @property
    def episode_generation(self) -> int:
        return self.correlation_key.episode_generation

    @property
    def transition_generation(self) -> int:
        return self.correlation_key.transition_generation

    @property
    def bootstrap_critic_obs(self) -> torch.Tensor | None:
        if self._bootstrap_critic_obs is None:
            return None
        return _readonly_tensor(self._bootstrap_critic_obs)


def make_event_terminal_learner_record_v2(
    historical: EventTerminalHistoricalRow,
) -> EventTerminalLearnerRecordV2:
    """Create one second bounded copy after the facade has completed runtime ACK."""

    return EventTerminalLearnerRecordV2._create_from_historical(historical=historical)


def _validate_expectation_against_facade(
    *,
    expectation: EventLearnerTransitionExpectationV2,
    facade_result: EventFacadeStepResult | EventFacadeProposalStepResult,
) -> None:
    if type(expectation) is not EventLearnerTransitionExpectationV2:
        _fail(
            "facade transport requires an exact runner transition expectation",
            failure_code="expectation_type",
            stage="six_tuple_transport",
            expected=EventLearnerTransitionExpectationV2,
            actual=type(expectation),
        )
    if type(facade_result) not in (EventFacadeStepResult, EventFacadeProposalStepResult):
        _fail(
            "learner transport requires one exact private facade step result",
            failure_code="facade_result_type",
            stage="six_tuple_transport",
            expected=(EventFacadeStepResult, EventFacadeProposalStepResult),
            actual=type(facade_result),
        )
    source = facade_result.source_publication
    source_episode = _generation_tuple(source.episode_generation, field_name="episode_generation")
    source_transition = _generation_tuple(
        source.transition_generation, field_name="transition_generation"
    )
    actual = (
        source.publication_identity,
        source_episode,
        source_transition,
    )
    expected = (
        expectation.p2_publication_identity,
        expectation.episode_generations,
        expectation.source_transition_generations,
    )
    if actual[0] is not expected[0] or actual[1:] != expected[1:]:
        _fail(
            "facade source is not the runner's exact pre-step decision identity",
            failure_code="facade_expectation_binding",
            stage="six_tuple_transport",
            expected=(id(expected[0]), *expected[1:]),
            actual=(id(actual[0]), *actual[1:]),
        )
    current = facade_result.current_publication
    current_transition = _generation_tuple(
        current.transition_generation, field_name="current_transition_generation"
    )
    if current_transition != expectation.expected_transition_generations:
        _fail(
            "returned current P2 is not the state following transition slot t",
            failure_code="current_transition_shift",
            stage="six_tuple_transport",
            expected=expectation.expected_transition_generations,
            actual=current_transition,
        )


def attach_event_terminal_infos_to_harl_step_v2(
    *,
    harl_step_result: tuple[object, object, object, torch.Tensor, object, object],
    facade_result: EventFacadeStepResult | EventFacadeProposalStepResult,
    expectation: EventLearnerTransitionExpectationV2,
) -> tuple[object, object, object, torch.Tensor, list[list[dict[str, object]]], object]:
    """Preserve six slots and attach only ACK-safe DTOs in ``infos[env][0]``."""

    _validate_expectation_against_facade(expectation=expectation, facade_result=facade_result)
    if type(harl_step_result) is not tuple or len(harl_step_result) != 6:
        _fail(
            "event learner transport preserves the existing six-element return",
            failure_code="harl_step_arity",
            stage="six_tuple_transport",
            expected="exact six-tuple",
            actual=(type(harl_step_result), getattr(harl_step_result, "__len__", lambda: None)()),
        )
    dones = harl_step_result[3]
    infos = harl_step_result[4]
    E = len(expectation.env_ids)
    if (
        type(dones) is not torch.Tensor
        or dones.dtype is not torch.bool
        or dones.ndim != 2
        or dones.shape[0] != E
        or dones.shape[1] <= 0
        or dones.requires_grad
        or not torch.equal(dones, dones[:, :1].expand_as(dones))
    ):
        _fail(
            "HARL dones must be one exact synchronized bool row per environment",
            failure_code="harl_done_contract",
            stage="six_tuple_transport",
            expected=(E, "M>0", torch.bool, "agent-synchronized"),
            actual=(getattr(dones, "shape", None), getattr(dones, "dtype", None)),
        )
    if not isinstance(infos, Sequence) or len(infos) != E:
        _fail(
            "HARL infos must preserve one row per environment",
            failure_code="harl_infos_contract",
            stage="six_tuple_transport",
            expected=E,
            actual=(type(infos), len(infos) if isinstance(infos, Sequence) else None),
        )
    M = int(dones.shape[1])
    current_episode = _generation_tuple(
        facade_result.current_publication.episode_generation,
        field_name="current_episode_generation",
    )
    expected_current_episode = tuple(
        episode + int(bool(dones[env_id, 0].item()))
        for env_id, episode in enumerate(expectation.episode_generations)
    )
    if current_episode != expected_current_episode:
        _fail(
            "returned current episode generations do not match autoreset boundaries",
            failure_code="current_episode_shift",
            stage="six_tuple_transport",
            expected=expected_current_episode,
            actual=current_episode,
        )
    copied_infos: list[list[dict[str, object]]] = []
    for env_id, env_info in enumerate(infos):
        if not isinstance(env_info, Sequence) or len(env_info) != M:
            _fail(
                "HARL info row does not match fixed agent cardinality",
                failure_code="harl_infos_contract",
                stage="six_tuple_transport",
                expected=(env_id, M),
                actual=(type(env_info), len(env_info) if isinstance(env_info, Sequence) else None),
            )
        row: list[dict[str, object]] = []
        for agent_info in env_info:
            if not isinstance(agent_info, Mapping):
                _fail(
                    "HARL agent info must be a mapping",
                    failure_code="harl_infos_contract",
                    stage="six_tuple_transport",
                    expected=Mapping,
                    actual=type(agent_info),
                )
            if EVENT_TERMINAL_LEARNER_INFO_KEY_V2 in agent_info:
                _fail(
                    "base infos already contain the reserved event learner key",
                    failure_code="harl_info_key_collision",
                    stage="six_tuple_transport",
                    expected="reserved key absent",
                    actual=env_id,
                )
            row.append(dict(agent_info))
        copied_infos.append(row)

    historical = facade_result.terminal_historical_payload
    seen_envs: set[int] = set()
    for row in historical:
        record = make_event_terminal_learner_record_v2(row)
        env_id = record.env_id
        if env_id in seen_envs:
            _fail(
                "facade terminal payload contains duplicate env records",
                failure_code="terminal_dto_duplicate",
                stage="six_tuple_transport",
                expected="one record per env/transition",
                actual=record.correlation_key.value,
            )
        seen_envs.add(env_id)
        if record.correlation_key != expectation.expected_key(env_id):
            _fail(
                "historical DTO is stale or belongs to another transition",
                failure_code="terminal_dto_stale",
                stage="six_tuple_transport",
                expected=expectation.expected_key(env_id).value,
                actual=record.correlation_key.value,
            )
        copied_infos[env_id][0][EVENT_TERMINAL_LEARNER_INFO_KEY_V2] = record

    done_envs = {int(item) for item in torch.nonzero(dones[:, 0], as_tuple=False).flatten().cpu().tolist()}
    if done_envs != seen_envs:
        _fail(
            "done rows and terminal learner DTO rows differ",
            failure_code="terminal_dto_missing",
            stage="six_tuple_transport",
            expected=tuple(sorted(done_envs)),
            actual=tuple(sorted(seen_envs)),
        )
    return (
        harl_step_result[0],
        harl_step_result[1],
        harl_step_result[2],
        dones,
        copied_infos,
        harl_step_result[5],
    )


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventTerminalCorrelationBatchV2:
    """Exact full-E terminal correlation before any critic call."""

    schema_version: str
    expectation: EventLearnerTransitionExpectationV2 = field(repr=False)
    records: tuple[EventTerminalLearnerRecordV2 | None, ...] = field(repr=False)
    _sanitized_infos: tuple[tuple[Mapping[str, object], ...], ...] = field(repr=False)
    _termination_reason: torch.Tensor = field(repr=False)
    _timeout_bootstrap_masks: torch.Tensor = field(repr=False)

    @property
    def termination_reason(self) -> torch.Tensor:
        return _readonly_tensor(self._termination_reason)

    @property
    def timeout_bootstrap_masks(self) -> torch.Tensor:
        return _readonly_tensor(self._timeout_bootstrap_masks)

    @property
    def sanitized_infos(self) -> list[list[dict[str, object]]]:
        return [
            [dict(agent_info) for agent_info in env_info]
            for env_info in self._sanitized_infos
        ]

    @property
    def terminal_keys(self) -> tuple[EventTerminalCorrelationKeyV2, ...]:
        return tuple(record.correlation_key for record in self.records if record is not None)


def correlate_event_terminal_infos_v2(
    *,
    expectation: EventLearnerTransitionExpectationV2,
    dones: torch.Tensor,
    infos: object,
) -> EventTerminalCorrelationBatchV2:
    """Fail closed on missing, duplicate, stale, wrong-key, or wrong-done DTOs."""

    E = len(expectation.env_ids) if type(expectation) is EventLearnerTransitionExpectationV2 else -1
    if E <= 0:
        _fail(
            "terminal correlation requires an exact transition expectation",
            failure_code="expectation_type",
            stage="terminal_correlation",
            expected=EventLearnerTransitionExpectationV2,
            actual=type(expectation),
        )
    if (
        type(dones) is not torch.Tensor
        or dones.dtype is not torch.bool
        or dones.ndim != 2
        or tuple(dones.shape)[0] != E
        or dones.shape[1] <= 0
        or dones.requires_grad
        or not torch.equal(dones, dones[:, :1].expand_as(dones))
    ):
        _fail(
            "terminal correlation requires synchronized HARL done rows",
            failure_code="harl_done_contract",
            stage="terminal_correlation",
            expected=(E, "M>0", torch.bool),
            actual=(getattr(dones, "shape", None), getattr(dones, "dtype", None)),
        )
    if not isinstance(infos, Sequence) or len(infos) != E:
        _fail(
            "terminal correlation requires fixed-E infos",
            failure_code="harl_infos_contract",
            stage="terminal_correlation",
            expected=E,
            actual=(type(infos), len(infos) if isinstance(infos, Sequence) else None),
        )
    M = int(dones.shape[1])
    reasons = torch.full(
        (E, 1), int(TerminationReason.NONE), dtype=torch.int64, device=dones.device
    )
    timeout_masks = torch.zeros((E, 1), dtype=torch.bool, device=dones.device)
    records: list[EventTerminalLearnerRecordV2 | None] = [None] * E
    sanitized: list[list[dict[str, object]]] = []
    seen_keys: set[tuple[int, int, int]] = set()
    for env_id, env_info in enumerate(infos):
        if not isinstance(env_info, Sequence) or len(env_info) != M:
            _fail(
                "terminal info row has the wrong agent cardinality",
                failure_code="harl_infos_contract",
                stage="terminal_correlation",
                expected=(env_id, M),
                actual=(type(env_info), len(env_info) if isinstance(env_info, Sequence) else None),
            )
        found: list[EventTerminalLearnerRecordV2] = []
        clean_row: list[dict[str, object]] = []
        for agent_id, agent_info in enumerate(env_info):
            if not isinstance(agent_info, Mapping):
                _fail(
                    "terminal agent info is not a mapping",
                    failure_code="harl_infos_contract",
                    stage="terminal_correlation",
                    expected=Mapping,
                    actual=type(agent_info),
                )
            copied = dict(agent_info)
            value = copied.pop(EVENT_TERMINAL_LEARNER_INFO_KEY_V2, None)
            if value is not None:
                if agent_id != 0 or type(value) is not EventTerminalLearnerRecordV2:
                    _fail(
                        "terminal DTO must appear exactly in infos[env][0]",
                        failure_code="terminal_dto_location",
                        stage="terminal_correlation",
                        expected=(env_id, 0, EventTerminalLearnerRecordV2),
                        actual=(env_id, agent_id, type(value)),
                    )
                found.append(value)
            clean_row.append(copied)
        is_done = bool(dones[env_id, 0].item())
        if is_done and len(found) != 1:
            _fail(
                "terminal row requires exactly one learner DTO",
                failure_code="terminal_dto_missing" if not found else "terminal_dto_duplicate",
                stage="terminal_correlation",
                expected=1,
                actual=len(found),
            )
        if not is_done and found:
            _fail(
                "nonterminal row must not carry terminal history",
                failure_code="nonterminal_dto_present",
                stage="terminal_correlation",
                expected=0,
                actual=len(found),
            )
        if found:
            record = found[0]
            if record.env_id != env_id:
                _fail(
                    "terminal DTO is stored under the wrong environment row",
                    failure_code="terminal_dto_env",
                    stage="terminal_correlation",
                    expected=env_id,
                    actual=record.env_id,
                )
            expected_key = expectation.expected_key(env_id)
            if record.correlation_key != expected_key:
                _fail(
                    "terminal DTO generation/key is stale",
                    failure_code="terminal_dto_stale",
                    stage="terminal_correlation",
                    expected=expected_key.value,
                    actual=record.correlation_key.value,
                )
            audit = record.terminal_audit
            audit_binding = (
                type(audit),
                audit.env_id,
                audit.episode_generation,
                audit.transition_generation,
                audit.termination_reason,
                audit.projection_mode,
                audit.critic_schema_version,
                audit.critic_dimension,
            )
            expected_audit = (
                TerminalAuditProjectionV2,
                record.env_id,
                record.episode_generation,
                record.transition_generation,
                record.termination_reason,
                "TERMINAL_AUDIT",
                record.critic_schema_version,
                record.critic_dimension,
            )
            if (
                record.schema_version != EVENT_TERMINAL_LEARNER_RECORD_V2
                or record.profile_name != AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value
                or audit_binding != expected_audit
            ):
                _fail(
                    "terminal learner DTO metadata/audit binding is malformed",
                    failure_code="terminal_dto_audit_binding",
                    stage="terminal_correlation",
                    expected=(EVENT_TERMINAL_LEARNER_RECORD_V2, AssignmentProfileName.EVENT_GATED_LOCAL_MRTA.value, expected_audit),
                    actual=(record.schema_version, record.profile_name, audit_binding),
                )
            audit_evidence = audit.semantic_evidence
            if (
                audit_evidence.shape != (record.critic_dimension,)
                or audit_evidence.dtype is not record.critic_dtype
                or audit_evidence.device != record.critic_device
                or audit_evidence.requires_grad
                or not bool(torch.isfinite(audit_evidence).all().item())
            ):
                _fail(
                    "terminal audit evidence violates its declared diagnostic contract",
                    failure_code="terminal_dto_audit_contract",
                    stage="terminal_correlation",
                    expected=((record.critic_dimension,), record.critic_dtype, record.critic_device, False),
                    actual=(audit_evidence.shape, audit_evidence.dtype, audit_evidence.device, audit_evidence.requires_grad),
                )
            expected_key = expectation.expected_key(env_id)
            if record.env_id != env_id:
                _fail(
                    "terminal DTO is stored under the wrong environment row",
                    failure_code="terminal_dto_env",
                    stage="terminal_correlation",
                    expected=env_id,
                    actual=record.env_id,
                )
            if record.correlation_key != expected_key:
                _fail(
                    "terminal DTO generation/key is stale",
                    failure_code="terminal_dto_stale",
                    stage="terminal_correlation",
                    expected=expected_key.value,
                    actual=record.correlation_key.value,
                )
            if record.correlation_key.value in seen_keys:
                _fail(
                    "terminal DTO key occurs more than once",
                    failure_code="terminal_dto_duplicate",
                    stage="terminal_correlation",
                    expected="unique exact key",
                    actual=record.correlation_key.value,
                )
            seen_keys.add(record.correlation_key.value)
            expected_flags = (
                (False, True)
                if record.termination_reason == int(TerminationReason.TIME_LIMIT)
                else (True, False)
            )
            if record.termination_reason not in _TERMINAL_REASONS or (
                record.terminated,
                record.truncated,
            ) != expected_flags:
                _fail(
                    "learner DTO reason/done semantics are inconsistent",
                    failure_code="terminal_dto_reason_done",
                    stage="terminal_correlation",
                    expected=expected_flags,
                    actual=(record.termination_reason, record.terminated, record.truncated),
                )
            timeout = record.termination_reason == int(TerminationReason.TIME_LIMIT)
            if record.bootstrap_projection_valid is not timeout or (
                record._bootstrap_critic_obs is not None
            ) is not timeout:
                _fail(
                    "terminal DTO bootstrap presence differs from its reason",
                    failure_code="terminal_dto_bootstrap_presence",
                    stage="terminal_correlation",
                    expected=timeout,
                    actual=(record.bootstrap_projection_valid, record._bootstrap_critic_obs is not None),
                )
            bootstrap = record.bootstrap_critic_obs
            if bootstrap is not None and (
                bootstrap.shape != (record.critic_dimension,)
                or bootstrap.dtype is not torch.float32
                or bootstrap.device != record.critic_device
                or bootstrap.requires_grad
                or not bool(torch.isfinite(bootstrap).all().item())
            ):
                _fail(
                    "terminal DTO timeout observation violates its declared critic contract",
                    failure_code="terminal_dto_bootstrap_contract",
                    stage="terminal_correlation",
                    expected=((record.critic_dimension,), torch.float32, record.critic_device, False),
                    actual=(bootstrap.shape, bootstrap.dtype, bootstrap.device, bootstrap.requires_grad),
                )
            records[env_id] = record
            reasons[env_id, 0] = record.termination_reason
            timeout_masks[env_id, 0] = timeout
        sanitized.append(clean_row)
    instance = object.__new__(EventTerminalCorrelationBatchV2)
    object.__setattr__(instance, "schema_version", EVENT_TERMINAL_CORRELATION_BATCH_V2)
    object.__setattr__(instance, "expectation", expectation)
    object.__setattr__(instance, "records", tuple(records))
    object.__setattr__(
        instance,
        "_sanitized_infos",
        tuple(
            tuple(MappingProxyType(dict(agent_info)) for agent_info in env_info)
            for env_info in sanitized
        ),
    )
    object.__setattr__(instance, "_termination_reason", _readonly_tensor(reasons))
    object.__setattr__(instance, "_timeout_bootstrap_masks", _readonly_tensor(timeout_masks))
    return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventTimeoutCriticInputBatchV2:
    """The only terminal type accepted by the timeout critic evaluator."""

    schema_version: str
    env_indices: tuple[int, ...]
    num_envs: int
    _bootstrap_critic_obs: torch.Tensor = field(repr=False)

    @property
    def bootstrap_critic_obs(self) -> torch.Tensor:
        return _readonly_tensor(self._bootstrap_critic_obs)


def _make_timeout_critic_input_batch_v2(
    correlation: EventTerminalCorrelationBatchV2,
) -> EventTimeoutCriticInputBatchV2:
    if type(correlation) is not EventTerminalCorrelationBatchV2:
        _fail(
            "timeout input requires one exact correlated terminal batch",
            failure_code="critic_input_type",
            stage="timeout_critic_input",
            expected=EventTerminalCorrelationBatchV2,
            actual=type(correlation),
        )
    env_indices = tuple(
        env_id
        for env_id, record in enumerate(correlation.records)
        if record is not None and record.termination_reason == int(TerminationReason.TIME_LIMIT)
    )
    observations = [correlation.records[env_id].bootstrap_critic_obs for env_id in env_indices]
    if any(item is None for item in observations):
        _fail(
            "correlated TIME_LIMIT row has no bootstrap critic observation",
            failure_code="critic_bootstrap_missing",
            stage="timeout_critic_input",
            expected="one observation per timeout row",
            actual=env_indices,
        )
    if observations:
        reference = observations[0]
        if any(
            item.shape != reference.shape
            or item.dtype is not torch.float32
            or item.device != reference.device
            or item.requires_grad
            or not bool(torch.isfinite(item).all().item())
            for item in observations
        ):
            _fail(
                "timeout observations do not share one finite critic contract",
                failure_code="critic_bootstrap_batch_contract",
                stage="timeout_critic_input",
                expected=(reference.shape, torch.float32, reference.device, False),
                actual=tuple(
                    (item.shape, item.dtype, item.device, item.requires_grad)
                    for item in observations
                ),
            )
        batch = torch.stack(observations, dim=0).detach().clone().contiguous()
    else:
        device = correlation._termination_reason.device
        batch = torch.empty((0, 0), dtype=torch.float32, device=device)
    instance = object.__new__(EventTimeoutCriticInputBatchV2)
    object.__setattr__(instance, "schema_version", EVENT_TIMEOUT_CRITIC_INPUT_BATCH_V2)
    object.__setattr__(instance, "env_indices", env_indices)
    object.__setattr__(instance, "num_envs", len(correlation.records))
    object.__setattr__(instance, "_bootstrap_critic_obs", batch)
    return instance


def _critic_parameter_module(critic: object) -> torch.nn.Module | None:
    if isinstance(critic, torch.nn.Module):
        return critic
    module = getattr(critic, "critic", None)
    return module if isinstance(module, torch.nn.Module) else None


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventRolloutCriticGuardV2:
    """Parameter/version identity captured before rollout optimizer updates."""

    critic_identity: object = field(repr=False)
    parameter_identity: tuple[tuple[int, int, int], ...]
    training_mode: bool | None

    @classmethod
    def _capture(cls, critic: object) -> "EventRolloutCriticGuardV2":
        if not callable(getattr(critic, "get_values", None)):
            _fail(
                "rollout critic must expose the installed get_values API",
                failure_code="critic_api",
                stage="critic_guard_capture",
                expected="callable get_values(obs, rnn, masks)",
                actual=type(critic),
            )
        module = _critic_parameter_module(critic)
        parameters = () if module is None else tuple(module.parameters())
        instance = object.__new__(cls)
        object.__setattr__(instance, "critic_identity", critic)
        object.__setattr__(
            instance,
            "parameter_identity",
            tuple((id(parameter), parameter.data_ptr(), parameter._version) for parameter in parameters),
        )
        object.__setattr__(instance, "training_mode", None if module is None else module.training)
        return instance

    def validate(self, critic: object, *, stage: str) -> None:
        if critic is not self.critic_identity:
            _fail(
                "timeout evaluation critic differs from the rollout critic",
                failure_code="critic_identity",
                stage=stage,
                expected=id(self.critic_identity),
                actual=id(critic),
            )
        module = _critic_parameter_module(critic)
        parameters = () if module is None else tuple(module.parameters())
        actual = tuple(
            (id(parameter), parameter.data_ptr(), parameter._version) for parameter in parameters
        )
        actual_mode = None if module is None else module.training
        if actual != self.parameter_identity or actual_mode is not self.training_mode:
            _fail(
                "rollout critic parameters or mode changed before timeout evidence was sealed",
                failure_code="critic_snapshot_changed",
                stage=stage,
                expected=(self.parameter_identity, self.training_mode),
                actual=(actual, actual_mode),
            )


def capture_event_rollout_critic_guard_v2(critic: object) -> EventRolloutCriticGuardV2:
    """Capture a lightweight no-update guard before rollout collection begins."""

    return EventRolloutCriticGuardV2._capture(critic)


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventTerminalCriticEvaluationBatchV2:
    """Full-E reason/mask/value evidence aligned to one transition slot t."""

    schema_version: str
    correlation: EventTerminalCorrelationBatchV2 = field(repr=False)
    timeout_env_indices: tuple[int, ...]
    critic_batch_calls: int
    _termination_reason: torch.Tensor = field(repr=False)
    _timeout_bootstrap_value_preds: torch.Tensor = field(repr=False)
    _timeout_bootstrap_masks: torch.Tensor = field(repr=False)

    @property
    def termination_reason(self) -> torch.Tensor:
        return _readonly_tensor(self._termination_reason)

    @property
    def timeout_bootstrap_value_preds(self) -> torch.Tensor:
        return _readonly_tensor(self._timeout_bootstrap_value_preds)

    @property
    def timeout_bootstrap_masks(self) -> torch.Tensor:
        return _readonly_tensor(self._timeout_bootstrap_masks)


def evaluate_event_timeout_bootstrap_values_v2(
    *,
    timeout_input: EventTimeoutCriticInputBatchV2,
    correlation: EventTerminalCorrelationBatchV2,
    critic: object,
    rollout_critic_guard: EventRolloutCriticGuardV2,
    rnn_states_critic_after_current: torch.Tensor,
) -> EventTerminalCriticEvaluationBatchV2:
    """Evaluate all and only TIME_LIMIT rows once in one no-grad critic batch."""

    if type(timeout_input) is not EventTimeoutCriticInputBatchV2:
        _fail(
            "terminal critic accepts only TIME_LIMIT_BOOTSTRAP_CRITIC input",
            failure_code="critic_input_type",
            stage="timeout_critic_evaluate",
            expected=EventTimeoutCriticInputBatchV2,
            actual=type(timeout_input),
        )
    if type(correlation) is not EventTerminalCorrelationBatchV2:
        _fail(
            "timeout evaluation requires the exact correlated batch",
            failure_code="correlation_type",
            stage="timeout_critic_evaluate",
            expected=EventTerminalCorrelationBatchV2,
            actual=type(correlation),
        )
    if type(rollout_critic_guard) is not EventRolloutCriticGuardV2:
        _fail(
            "timeout evaluation requires a pre-update rollout critic guard",
            failure_code="critic_guard_type",
            stage="timeout_critic_evaluate",
            expected=EventRolloutCriticGuardV2,
            actual=type(rollout_critic_guard),
        )
    rollout_critic_guard.validate(critic, stage="timeout_critic_pre_forward")
    E = timeout_input.num_envs
    observations = timeout_input._bootstrap_critic_obs
    device = observations.device
    if (
        type(rnn_states_critic_after_current) is not torch.Tensor
        or rnn_states_critic_after_current.ndim < 2
        or rnn_states_critic_after_current.shape[0] != E
        or rnn_states_critic_after_current.dtype is not torch.float32
        or rnn_states_critic_after_current.device != device
        or rnn_states_critic_after_current.requires_grad
        or not bool(torch.isfinite(rnn_states_critic_after_current).all().item())
    ):
        _fail(
            "timeout critic RNN placeholder/state has an invalid rollout contract",
            failure_code="critic_rnn_contract",
            stage="timeout_critic_evaluate",
            expected=(E, "...", torch.float32, device, False),
            actual=(
                getattr(rnn_states_critic_after_current, "shape", None),
                getattr(rnn_states_critic_after_current, "dtype", None),
                getattr(rnn_states_critic_after_current, "device", None),
                getattr(rnn_states_critic_after_current, "requires_grad", None),
            ),
        )
    masks = correlation._timeout_bootstrap_masks
    if masks.device != device:
        _fail(
            "terminal correlation and critic observations use different devices",
            failure_code="critic_device",
            stage="timeout_critic_evaluate",
            expected=device,
            actual=masks.device,
        )
    values = torch.zeros((E, 1), dtype=torch.float32, device=device)
    indices = timeout_input.env_indices
    calls = 0
    if indices:
        index = torch.tensor(indices, dtype=torch.int64, device=device)
        rnn_subset = rnn_states_critic_after_current.index_select(0, index).detach().clone()
        critic_masks = torch.ones((len(indices), 1), dtype=torch.float32, device=device)
        with torch.inference_mode():
            result = critic.get_values(observations, rnn_subset, critic_masks)
        calls = 1
        if type(result) is not tuple or len(result) != 2:
            _fail(
                "critic get_values must preserve the installed two-tuple API",
                failure_code="critic_output_contract",
                stage="timeout_critic_evaluate",
                expected="(values, rnn_states)",
                actual=type(result),
            )
        compact_values = result[0]
        if (
            type(compact_values) is not torch.Tensor
            or tuple(compact_values.shape) != (len(indices), 1)
            or compact_values.dtype is not torch.float32
            or compact_values.device != device
            or compact_values.requires_grad
        ):
            _fail(
                "timeout critic values violate shape/dtype/device/no-grad contract",
                failure_code="critic_value_contract",
                stage="timeout_critic_evaluate",
                expected=((len(indices), 1), torch.float32, device, False),
                actual=(
                    type(compact_values),
                    getattr(compact_values, "shape", None),
                    getattr(compact_values, "dtype", None),
                    getattr(compact_values, "device", None),
                    getattr(compact_values, "requires_grad", None),
                ),
            )
        if not bool(torch.isfinite(compact_values).all().item()):
            _fail(
                "timeout critic values must be finite before buffer insertion",
                failure_code="critic_value_nonfinite",
                stage="timeout_critic_evaluate",
                expected="finite values",
                actual=compact_values,
            )
        values.index_copy_(0, index, compact_values.detach().clone())
    rollout_critic_guard.validate(critic, stage="timeout_critic_post_forward")
    instance = object.__new__(EventTerminalCriticEvaluationBatchV2)
    object.__setattr__(instance, "schema_version", EVENT_TERMINAL_CRITIC_EVALUATION_BATCH_V2)
    object.__setattr__(instance, "correlation", correlation)
    object.__setattr__(instance, "timeout_env_indices", indices)
    object.__setattr__(instance, "critic_batch_calls", calls)
    object.__setattr__(instance, "_termination_reason", correlation.termination_reason)
    object.__setattr__(instance, "_timeout_bootstrap_value_preds", _readonly_tensor(values))
    object.__setattr__(instance, "_timeout_bootstrap_masks", correlation.timeout_bootstrap_masks)
    return instance


def prepare_and_evaluate_event_terminal_batch_v2(
    *,
    expectation: EventLearnerTransitionExpectationV2,
    dones: torch.Tensor,
    infos: object,
    critic: object,
    rollout_critic_guard: EventRolloutCriticGuardV2,
    rnn_states_critic_after_current: torch.Tensor,
) -> EventTerminalCriticEvaluationBatchV2:
    """Narrow runner collection seam; never accepts current post-reset share_obs."""

    correlation = correlate_event_terminal_infos_v2(
        expectation=expectation,
        dones=dones,
        infos=infos,
    )
    timeout_input = _make_timeout_critic_input_batch_v2(correlation)
    return evaluate_event_timeout_bootstrap_values_v2(
        timeout_input=timeout_input,
        correlation=correlation,
        critic=critic,
        rollout_critic_guard=rollout_critic_guard,
        rnn_states_critic_after_current=rnn_states_critic_after_current,
    )


__all__: tuple[str, ...] = ()
