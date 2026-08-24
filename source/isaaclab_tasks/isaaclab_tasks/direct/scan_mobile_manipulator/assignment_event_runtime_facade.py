"""B-private I4 facade for reset, proposal/M1 commit, and physical admission.

The facade is deliberately narrower than O1.  It exposes only the I4-1 reset /
zero-claim route and the I4-2 explicit-decision proposal route; it exposes no
terminal-consumer, Store, domain-writer, fence-writer, legacy resolver, or
controller capability.  Runtime readiness and lifecycle observation/mask
construction stay outside this slice.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_RUNTIME_FACADE_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_runtime_facade"
)

if __name__ != CANONICAL_ASSIGNMENT_EVENT_RUNTIME_FACADE_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: event runtime facade source must execute "
        "under its canonical module key; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_RUNTIME_FACADE_MODULE!r}; "
        f"actual={__name__!r}"
    )


from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

import torch

from .assignment_event_profile_runtime_domain import (
    _EventProfileLifecycleRuntimeDomain,
)
from .assignment_event_profile_synchronous_runtime import (
    EventProfileSynchronousRuntimeCoordinator,
    _EventProfileNoClaimStepReceipt,
)
from .assignment_event_proposal_adapter import (
    EventProposalAdapter,
    EventProposalDecisionSnapshot,
    EventProposalResolution,
    _EventProposalInterpretation,
    _committed_interpretations,
)
from .assignment_event_terminal_transport import (
    EventTerminalHistoricalRow,
    _copy_and_validate_terminal_history,
)
from .assignment_initial_claim_runtime import (
    EffectiveAssignmentCommitArtifact,
    _CurrentPublicationProvenanceKind,
    _EventRuntimeCurrentPublication,
)
from .assignment_interstep_claim_window_runtime import (
    _ClaimWindowFencePhase,
    _ClaimWindowFenceView,
)
from .assignment_profile_contract import ResolvedEventGatedAssignmentProfile


_FACADE_FACTORY_CAPABILITY = object()
_RESET_RESULT_FACTORY_CAPABILITY = object()
_STEP_RESULT_FACTORY_CAPABILITY = object()
_PROPOSAL_STEP_RESULT_FACTORY_CAPABILITY = object()


class EventAssignmentRuntimeFacadeError(RuntimeError):
    """Typed fail-closed I4 facade construction or routing failure."""

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


def _generation_values(value: object, *, field_name: str) -> tuple[int, ...]:
    if type(value) is not torch.Tensor or value.dtype != torch.int64 or value.ndim != 1:
        raise EventAssignmentRuntimeFacadeError(
            "event publication generation has an invalid tensor contract",
            failure_code="publication_generation_contract",
            stage="facade_publication_validate",
            expected=f"{field_name}: int64[E]",
            actual=(type(value), getattr(value, "dtype", None), getattr(value, "shape", None)),
        )
    return tuple(int(item) for item in value.detach().cpu().tolist())


def _require_open_fence(view: object, *, stage: str) -> _ClaimWindowFenceView:
    if type(view) is not _ClaimWindowFenceView or view.phase is not _ClaimWindowFencePhase.OPEN:
        raise EventAssignmentRuntimeFacadeError(
            "event facade requires the existing inter-step fence to be OPEN",
            failure_code="facade_fence_not_open",
            stage=stage,
            expected=_ClaimWindowFencePhase.OPEN,
            actual=(type(view), getattr(view, "phase", None)),
        )
    return view


def _validate_reset_publication(
    publication: object,
) -> tuple[_EventRuntimeCurrentPublication, tuple[int, ...], tuple[int, ...]]:
    if type(publication) is not _EventRuntimeCurrentPublication:
        raise EventAssignmentRuntimeFacadeError(
            "event reset lost the exact current P2 publication",
            failure_code="facade_reset_publication_type",
            stage="facade_reset_validate",
            expected=_EventRuntimeCurrentPublication,
            actual=type(publication),
        )
    if any(
        item.kind is not _CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET
        for item in publication.provenance
    ):
        raise EventAssignmentRuntimeFacadeError(
            "event reset P2 provenance is not canonical episode reset",
            failure_code="facade_reset_provenance",
            stage="facade_reset_validate",
            expected=_CurrentPublicationProvenanceKind.CANONICAL_EPISODE_RESET,
            actual=tuple(item.kind for item in publication.provenance),
        )
    if publication.result is not None:
        raise EventAssignmentRuntimeFacadeError(
            "event reset P2 must not retain a lifecycle result",
            failure_code="facade_reset_result",
            stage="facade_reset_validate",
            expected=None,
            actual=type(publication.result),
        )
    if bool(publication.terminated.any().item()) or bool(publication.truncated.any().item()):
        raise EventAssignmentRuntimeFacadeError(
            "event reset P2 must be nonterminal",
            failure_code="facade_reset_terminal",
            stage="facade_reset_validate",
            expected="terminated=false and truncated=false",
            actual=(publication.terminated, publication.truncated),
        )
    episode = _generation_values(publication.episode_generation, field_name="episode_generation")
    transition = _generation_values(publication.transition_generation, field_name="transition_generation")
    if len(episode) != len(publication.provenance) or len(transition) != len(episode):
        raise EventAssignmentRuntimeFacadeError(
            "event reset generation rows do not match P2 provenance rows",
            failure_code="facade_reset_generation_rows",
            stage="facade_reset_validate",
            expected=len(publication.provenance),
            actual=(len(episode), len(transition)),
        )
    if any(value < 0 for value in episode) or any(value < -1 for value in transition):
        raise EventAssignmentRuntimeFacadeError(
            "event reset generations must be initialized",
            failure_code="facade_reset_generation_state",
            stage="facade_reset_validate",
            expected="episode generation >= 0 and canonical reset transition >= -1",
            actual=(episode, transition),
        )
    return publication, episode, transition


def _environment_result_is_terminal(result: object) -> bool:
    if type(result) is not tuple or len(result) != 5:
        return False
    for value in result[2:4]:
        tensors = value.values() if isinstance(value, Mapping) else (value,)
        for tensor in tensors:
            if type(tensor) is torch.Tensor and bool(tensor.to(dtype=torch.bool).any().item()):
                return True
    return False


def _require_terminal_historical_payload(
    value: object,
) -> tuple[EventTerminalHistoricalRow, ...]:
    if type(value) is not tuple or any(
        type(row) is not EventTerminalHistoricalRow for row in value
    ):
        raise EventAssignmentRuntimeFacadeError(
            "facade result requires an exact immutable historical-row tuple",
            failure_code="facade_terminal_payload_type",
            stage="facade_step_result_create",
            expected="tuple[EventTerminalHistoricalRow, ...]",
            actual=type(value),
        )
    return value


def _finalize_terminal_handoff_after_step(
    *,
    runtime: EventProfileSynchronousRuntimeCoordinator,
    receipt: _EventProfileNoClaimStepReceipt,
) -> tuple[EventTerminalHistoricalRow, ...]:
    """Copy all terminal history, then atomically end runtime slot lifetime."""

    current = runtime.read_current()
    fence = _require_open_fence(
        runtime.read_interstep_fence(),
        stage="facade_terminal_post_step",
    )
    if fence.window is not receipt.completed_window:
        raise EventAssignmentRuntimeFacadeError(
            "terminal handoff must begin only after exact Ak completion opened Wnext",
            failure_code="facade_terminal_window_completion",
            stage="facade_terminal_post_step",
            expected=id(receipt.completed_window),
            actual=id(fence.window),
        )
    captured = runtime.capture_pending_terminal_artifacts()
    is_terminal = _environment_result_is_terminal(receipt.environment_result)
    if not is_terminal:
        if captured:
            raise EventAssignmentRuntimeFacadeError(
                "nonterminal physical return unexpectedly has terminal slots",
                failure_code="facade_terminal_return_capture_mismatch",
                stage="facade_terminal_post_step",
                expected=(),
                actual=tuple(artifact.key for artifact in captured),
            )
        return ()
    if not captured:
        raise EventAssignmentRuntimeFacadeError(
            "terminal physical return has no authoritative terminal artifacts",
            failure_code="facade_terminal_capture_missing",
            stage="facade_terminal_post_step",
            expected="one exact artifact per returned terminal env row",
            actual=(),
        )

    # This helper completes every copy and cross-lifetime validation before it
    # calls the sole atomic acknowledgement operation.
    historical = _copy_and_validate_terminal_history(
        captured_artifacts=captured,
        environment_result=receipt.environment_result,
        current_publication=current,
    )
    exact_keys = tuple(row.key for row in historical)
    current_identity = current.publication_identity
    current_store_version = current.store_version
    current_episode = _generation_values(current.episode_generation, field_name="episode_generation")
    current_transition = _generation_values(
        current.transition_generation,
        field_name="transition_generation",
    )
    acknowledged = runtime.acknowledge_terminal_artifacts(exact_keys)
    if len(acknowledged) != len(captured) or any(
        returned is not source
        for returned, source in zip(acknowledged, captured, strict=True)
    ):
        raise EventAssignmentRuntimeFacadeError(
            "atomic batch ACK did not return the exact captured artifact identities",
            failure_code="facade_terminal_ack_identity",
            stage="facade_terminal_acknowledge",
            expected=tuple(id(item) for item in captured),
            actual=tuple(id(item) for item in acknowledged),
        )

    after = runtime.read_current()
    after_fence = _require_open_fence(
        runtime.read_interstep_fence(),
        stage="facade_terminal_acknowledge",
    )
    after_episode = _generation_values(after.episode_generation, field_name="episode_generation")
    after_transition = _generation_values(
        after.transition_generation,
        field_name="transition_generation",
    )
    if (
        after.publication_identity is not current_identity
        or after.store_version != current_store_version
        or after_episode != current_episode
        or after_transition != current_transition
        or after_fence.window is not fence.window
    ):
        raise EventAssignmentRuntimeFacadeError(
            "terminal batch ACK changed current P2, Store, generations, or window",
            failure_code="facade_terminal_ack_neutrality",
            stage="facade_terminal_acknowledge",
            expected=(id(current_identity), current_store_version, current_episode, current_transition, id(fence.window)),
            actual=(id(after.publication_identity), after.store_version, after_episode, after_transition, id(after_fence.window)),
        )
    if runtime.capture_pending_terminal_artifacts():
        raise EventAssignmentRuntimeFacadeError(
            "successful full terminal batch ACK left an addressed slot occupied",
            failure_code="facade_terminal_ack_incomplete",
            stage="facade_terminal_acknowledge",
            expected=(),
            actual="pending terminal artifacts remain",
        )
    return historical


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventFacadeResetResult:
    """Immutable I4-1 reset result; P2 remains the sole current authority."""

    environment_result: object = field(repr=False)
    current_publication: _EventRuntimeCurrentPublication = field(repr=False)
    publication_identity: object = field(repr=False)
    episode_generations: tuple[int, ...]
    transition_generations: tuple[int, ...]
    route_diagnostic: str

    @classmethod
    def _create(
        cls,
        *,
        environment_result: object,
        current_publication: _EventRuntimeCurrentPublication,
        episode_generations: tuple[int, ...],
        transition_generations: tuple[int, ...],
        factory_capability: object,
    ) -> "EventFacadeResetResult":
        if factory_capability is not _RESET_RESULT_FACTORY_CAPABILITY:
            raise EventAssignmentRuntimeFacadeError(
                "event reset result requires the facade factory",
                failure_code="facade_reset_result_factory",
                stage="facade_reset_result_create",
                expected="facade reset-result factory capability",
                actual=type(factory_capability),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "environment_result", environment_result)
        object.__setattr__(instance, "current_publication", current_publication)
        object.__setattr__(instance, "publication_identity", current_publication.publication_identity)
        object.__setattr__(instance, "episode_generations", episode_generations)
        object.__setattr__(instance, "transition_generations", transition_generations)
        object.__setattr__(instance, "route_diagnostic", "admitted_event_reset_i4_1_provisional")
        return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventFacadeStepResult:
    """Immutable I4-1 receipt for one no-new-claim continuation step."""

    environment_result: object = field(repr=False)
    source_publication: _EventRuntimeCurrentPublication = field(repr=False)
    admitted_publication: _EventRuntimeCurrentPublication = field(repr=False)
    current_publication: _EventRuntimeCurrentPublication = field(repr=False)
    admitted_effective_assignment: torch.Tensor = field(repr=False)
    claim_artifact: None
    terminal_historical_payload: tuple[EventTerminalHistoricalRow, ...]
    route_diagnostic: str

    @classmethod
    def _create(
        cls,
        *,
        environment_result: object,
        source_publication: _EventRuntimeCurrentPublication,
        receipt: _EventProfileNoClaimStepReceipt,
        current_publication: _EventRuntimeCurrentPublication,
        terminal_historical_payload: tuple[EventTerminalHistoricalRow, ...],
        factory_capability: object,
    ) -> "EventFacadeStepResult":
        if factory_capability is not _STEP_RESULT_FACTORY_CAPABILITY:
            raise EventAssignmentRuntimeFacadeError(
                "event step result requires the facade factory",
                failure_code="facade_step_result_factory",
                stage="facade_step_result_create",
                expected="facade step-result factory capability",
                actual=type(factory_capability),
            )
        if type(receipt) is not _EventProfileNoClaimStepReceipt:
            raise EventAssignmentRuntimeFacadeError(
                "event step result requires the exact O1 no-claim receipt",
                failure_code="facade_step_receipt_type",
                stage="facade_step_result_create",
                expected=_EventProfileNoClaimStepReceipt,
                actual=type(receipt),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "environment_result", environment_result)
        object.__setattr__(instance, "source_publication", source_publication)
        object.__setattr__(instance, "admitted_publication", receipt.admitted_publication)
        object.__setattr__(instance, "current_publication", current_publication)
        object.__setattr__(
            instance,
            "admitted_effective_assignment",
            receipt.admitted_control_assignment.detach().clone().contiguous(),
        )
        object.__setattr__(instance, "claim_artifact", None)
        object.__setattr__(
            instance,
            "terminal_historical_payload",
            _require_terminal_historical_payload(terminal_historical_payload),
        )
        object.__setattr__(instance, "route_diagnostic", "no_new_claim_continuation_i4_1")
        return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventFacadeProposalStepResult:
    """Immutable I4-2 proposal/effective diagnostics around one physical step."""

    environment_result: object = field(repr=False)
    resolution: EventProposalResolution = field(repr=False)
    claim_artifact: EffectiveAssignmentCommitArtifact | None = field(repr=False)
    source_publication: _EventRuntimeCurrentPublication = field(repr=False)
    post_claim_publication: _EventRuntimeCurrentPublication = field(repr=False)
    admitted_publication: _EventRuntimeCurrentPublication = field(repr=False)
    current_publication: _EventRuntimeCurrentPublication = field(repr=False)
    admitted_effective_assignment: torch.Tensor = field(repr=False)
    committed_interpretations: tuple[tuple[_EventProposalInterpretation, ...], ...]
    terminal_historical_payload: tuple[EventTerminalHistoricalRow, ...]
    route_diagnostic: str

    @classmethod
    def _create(
        cls,
        *,
        environment_result: object,
        resolution: EventProposalResolution,
        claim_artifact: EffectiveAssignmentCommitArtifact | None,
        source_publication: _EventRuntimeCurrentPublication,
        post_claim_publication: _EventRuntimeCurrentPublication,
        receipt: _EventProfileNoClaimStepReceipt,
        current_publication: _EventRuntimeCurrentPublication,
        terminal_historical_payload: tuple[EventTerminalHistoricalRow, ...],
        factory_capability: object,
    ) -> "EventFacadeProposalStepResult":
        if factory_capability is not _PROPOSAL_STEP_RESULT_FACTORY_CAPABILITY:
            raise EventAssignmentRuntimeFacadeError(
                "proposal step result requires the facade factory",
                failure_code="facade_proposal_result_factory",
                stage="facade_proposal_result_create",
                expected="proposal-step result factory capability",
                actual=type(factory_capability),
            )
        if type(resolution) is not EventProposalResolution:
            raise EventAssignmentRuntimeFacadeError(
                "proposal step result requires the exact pure resolution",
                failure_code="facade_proposal_resolution_type",
                stage="facade_proposal_result_create",
                expected=EventProposalResolution,
                actual=type(resolution),
            )
        if type(receipt) is not _EventProfileNoClaimStepReceipt:
            raise EventAssignmentRuntimeFacadeError(
                "proposal step result requires the exact O1 receipt",
                failure_code="facade_proposal_receipt_type",
                stage="facade_proposal_result_create",
                expected=_EventProfileNoClaimStepReceipt,
                actual=type(receipt),
            )
        selected_count = int(resolution.selected_env_ids.numel())
        if (selected_count == 0) != (claim_artifact is None):
            raise EventAssignmentRuntimeFacadeError(
                "one proposal batch must produce zero or one coherent B1 artifact",
                failure_code="facade_proposal_artifact_cardinality",
                stage="facade_proposal_result_create",
                expected="K=0 iff artifact is None",
                actual=(selected_count, type(claim_artifact)),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "environment_result", environment_result)
        object.__setattr__(instance, "resolution", resolution)
        object.__setattr__(instance, "claim_artifact", claim_artifact)
        object.__setattr__(instance, "source_publication", source_publication)
        object.__setattr__(instance, "post_claim_publication", post_claim_publication)
        object.__setattr__(instance, "admitted_publication", receipt.admitted_publication)
        object.__setattr__(instance, "current_publication", current_publication)
        object.__setattr__(
            instance,
            "admitted_effective_assignment",
            receipt.admitted_control_assignment.detach().clone().contiguous(),
        )
        object.__setattr__(
            instance,
            "committed_interpretations",
            _committed_interpretations(resolution, committed=claim_artifact is not None),
        )
        object.__setattr__(
            instance,
            "terminal_historical_payload",
            _require_terminal_historical_payload(terminal_historical_payload),
        )
        object.__setattr__(instance, "route_diagnostic", "proposal_to_effective_m1_i4_2")
        return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class EventAssignmentRuntimeFacade:
    """Exact-event, HARL-independent WR-C facade through the I4-2 surface."""

    _runtime: EventProfileSynchronousRuntimeCoordinator = field(repr=False)
    _resolved_profile: ResolvedEventGatedAssignmentProfile = field(repr=False)
    _domain_identity: object = field(repr=False)

    def __init__(
        self,
        *,
        synchronous_runtime: EventProfileSynchronousRuntimeCoordinator,
        resolved_assignment_profile: ResolvedEventGatedAssignmentProfile,
        domain_identity: object,
        factory_capability: object,
    ) -> None:
        if factory_capability is not _FACADE_FACTORY_CAPABILITY:
            raise EventAssignmentRuntimeFacadeError(
                "event facade must be constructed by the exact composition helper",
                failure_code="facade_factory",
                stage="facade_construct",
                expected="event facade composition capability",
                actual=type(factory_capability),
            )
        if type(resolved_assignment_profile) is not ResolvedEventGatedAssignmentProfile:
            raise EventAssignmentRuntimeFacadeError(
                "event facade requires the exact canonical event profile",
                failure_code="facade_profile_type",
                stage="facade_construct",
                expected=ResolvedEventGatedAssignmentProfile,
                actual=type(resolved_assignment_profile),
            )
        if type(synchronous_runtime) is not EventProfileSynchronousRuntimeCoordinator:
            raise EventAssignmentRuntimeFacadeError(
                "event facade requires the exact O1 runtime type",
                failure_code="facade_runtime_type",
                stage="facade_construct",
                expected=EventProfileSynchronousRuntimeCoordinator,
                actual=type(synchronous_runtime),
            )
        if synchronous_runtime.domain_identity is not domain_identity:
            raise EventAssignmentRuntimeFacadeError(
                "event facade O1 belongs to another retained domain",
                failure_code="facade_domain_identity",
                stage="facade_construct",
                expected=id(domain_identity),
                actual=id(synchronous_runtime.domain_identity),
            )
        object.__setattr__(self, "_runtime", synchronous_runtime)
        object.__setattr__(self, "_resolved_profile", resolved_assignment_profile)
        object.__setattr__(self, "_domain_identity", domain_identity)

    @property
    def resolved_assignment_profile(self) -> ResolvedEventGatedAssignmentProfile:
        return self._resolved_profile

    @property
    def domain_identity(self) -> object:
        return self._domain_identity

    def read_current(self) -> _EventRuntimeCurrentPublication:
        return self._runtime.read_current()

    def capture_proposal_decision(
        self,
        *,
        feasible_mask: torch.Tensor,
        cost_matrix: torch.Tensor,
        available_mask: torch.Tensor | None = None,
    ) -> EventProposalDecisionSnapshot:
        """Capture one explicit physical snapshot against exact current P2/W."""

        current = self._runtime.read_current()
        fence = _require_open_fence(
            self._runtime.read_interstep_fence(),
            stage="facade_proposal_decision_capture",
        )
        if fence.window is None:
            raise EventAssignmentRuntimeFacadeError(
                "OPEN proposal decision has no exact window identity",
                failure_code="facade_proposal_window_missing",
                stage="facade_proposal_decision_capture",
                expected="opaque OPEN window",
                actual=None,
            )
        return EventProposalAdapter(self._resolved_profile).capture_decision(
            current_publication=current,
            current_window_identity=fence.window,
            feasible_mask=feasible_mask,
            cost_matrix=cost_matrix,
            available_mask=available_mask,
        )

    def resolve_proposals(
        self,
        *,
        raw_action_ids: torch.Tensor,
        decoded_proposal: torch.Tensor,
        decision: EventProposalDecisionSnapshot,
    ) -> EventProposalResolution:
        """Purely resolve one exact P2/window-bound proposal batch."""

        current = self._runtime.read_current()
        fence = _require_open_fence(
            self._runtime.read_interstep_fence(),
            stage="facade_proposal_resolve",
        )
        return EventProposalAdapter(self._resolved_profile).resolve(
            current_publication=current,
            current_window_identity=fence.window,
            decision=decision,
            raw_action_ids=raw_action_ids,
            decoded_proposal=decoded_proposal,
        )

    def step_resolved_proposals(
        self,
        *,
        resolution: EventProposalResolution,
        action_builder: Callable[[object, torch.Tensor], object] | None = None,
    ) -> EventFacadeProposalStepResult:
        """Commit zero-or-one M1 B1 batch, then step only from final Ak P2."""

        adapter = EventProposalAdapter(self._resolved_profile)
        source = self._runtime.read_current()
        source_fence = _require_open_fence(
            self._runtime.read_interstep_fence(),
            stage="facade_proposal_precommit",
        )
        adapter.validate_resolution_current(
            current_publication=source,
            current_window_identity=source_fence.window,
            resolution=resolution,
        )
        selected_env_ids = resolution.selected_env_ids
        requested_task_by_robot = resolution.requested_task_by_robot
        claim_artifact: EffectiveAssignmentCommitArtifact | None = None
        if int(selected_env_ids.numel()) > 0:
            try:
                claim_artifact = self._runtime.commit_initial_claim_batch(
                    selected_env_ids=selected_env_ids,
                    requested_task_by_robot=requested_task_by_robot,
                )
            except Exception as exc:
                raise EventAssignmentRuntimeFacadeError(
                    "authoritative B1 transaction rejected the resolved proposal batch",
                    failure_code="facade_b1_rejected",
                    stage="facade_proposal_b1_commit",
                    expected="one exact W2/B1/C2 M1 commit",
                    actual=(type(exc), getattr(exc, "failure_code", None)),
                ) from exc
            if type(claim_artifact) is not EffectiveAssignmentCommitArtifact:
                raise EventAssignmentRuntimeFacadeError(
                    "O1 returned a noncanonical B1 commit artifact",
                    failure_code="facade_b1_artifact_type",
                    stage="facade_proposal_b1_commit",
                    expected=EffectiveAssignmentCommitArtifact,
                    actual=type(claim_artifact),
                )
        post_claim = self._runtime.read_current()
        post_claim_fence = _require_open_fence(
            self._runtime.read_interstep_fence(),
            stage="facade_proposal_postcommit",
        )
        if post_claim_fence.window is not source_fence.window:
            raise EventAssignmentRuntimeFacadeError(
                "B1 commit must not create or rebind the inter-step window",
                failure_code="facade_b1_window_changed",
                stage="facade_proposal_postcommit",
                expected=id(source_fence.window),
                actual=id(post_claim_fence.window),
            )
        if claim_artifact is None:
            if post_claim is not source or post_claim.store_version != source.store_version:
                raise EventAssignmentRuntimeFacadeError(
                    "K=0 proposal resolution changed P2 or Store before Ak",
                    failure_code="facade_zero_claim_mutation",
                    stage="facade_proposal_postcommit",
                    expected=(id(source), source.store_version),
                    actual=(id(post_claim), post_claim.store_version),
                )
        elif (
            post_claim is source
            or post_claim.store_version != source.store_version + 1
            or claim_artifact.committed_store_version != post_claim.store_version
        ):
            raise EventAssignmentRuntimeFacadeError(
                "one M1 claim batch did not publish exactly one new Store/P2 version",
                failure_code="facade_m1_publication",
                stage="facade_proposal_postcommit",
                expected=("new P2", source.store_version + 1),
                actual=(post_claim is source, post_claim.store_version),
            )

        receipt = self._runtime.step_environment_without_new_claim(
            action_builder=action_builder,
        )
        if receipt.admitted_publication is not post_claim:
            raise EventAssignmentRuntimeFacadeError(
                "physical admission did not capture the final post-commit P2",
                failure_code="facade_proposal_ak_source",
                stage="facade_proposal_step",
                expected=id(post_claim),
                actual=id(receipt.admitted_publication),
            )
        _require_open_fence(
            self._runtime.read_interstep_fence(),
            stage="facade_proposal_step_post_return",
        )
        terminal_history = _finalize_terminal_handoff_after_step(
            runtime=self._runtime,
            receipt=receipt,
        )
        return EventFacadeProposalStepResult._create(
            environment_result=receipt.environment_result,
            resolution=resolution,
            claim_artifact=claim_artifact,
            source_publication=source,
            post_claim_publication=post_claim,
            receipt=receipt,
            current_publication=self._runtime.read_current(),
            terminal_historical_payload=terminal_history,
            factory_capability=_PROPOSAL_STEP_RESULT_FACTORY_CAPABILITY,
        )

    def resolve_and_step_proposals(
        self,
        *,
        raw_action_ids: torch.Tensor,
        decoded_proposal: torch.Tensor,
        decision: EventProposalDecisionSnapshot,
        action_builder: Callable[[object, torch.Tensor], object] | None = None,
    ) -> EventFacadeProposalStepResult:
        """Resolve purely, then execute the single synchronous I4-2 route."""

        resolution = self.resolve_proposals(
            raw_action_ids=raw_action_ids,
            decoded_proposal=decoded_proposal,
            decision=decision,
        )
        return self.step_resolved_proposals(
            resolution=resolution,
            action_builder=action_builder,
        )

    def reset(self, *args: object, **kwargs: object) -> EventFacadeResetResult:
        environment_result = self._runtime.reset_environment(*args, **kwargs)
        current, episode, transition = _validate_reset_publication(self._runtime.read_current())
        _require_open_fence(
            self._runtime.read_interstep_fence(),
            stage="facade_reset_validate",
        )
        return EventFacadeResetResult._create(
            environment_result=environment_result,
            current_publication=current,
            episode_generations=episode,
            transition_generations=transition,
            factory_capability=_RESET_RESULT_FACTORY_CAPABILITY,
        )

    def step_without_new_claim(
        self,
        *,
        action_builder: Callable[[object, torch.Tensor], object] | None = None,
    ) -> EventFacadeStepResult:
        source = self._runtime.read_current()
        receipt = self._runtime.step_environment_without_new_claim(
            action_builder=action_builder,
        )
        _require_open_fence(
            self._runtime.read_interstep_fence(),
            stage="facade_step_post_return",
        )
        terminal_history = _finalize_terminal_handoff_after_step(
            runtime=self._runtime,
            receipt=receipt,
        )
        current = self._runtime.read_current()
        return EventFacadeStepResult._create(
            environment_result=receipt.environment_result,
            source_publication=source,
            receipt=receipt,
            current_publication=current,
            terminal_historical_payload=terminal_history,
            factory_capability=_STEP_RESULT_FACTORY_CAPABILITY,
        )


def _compose_event_assignment_runtime_facade(
    *,
    resolved_assignment_profile: ResolvedEventGatedAssignmentProfile,
    runtime_domain: _EventProfileLifecycleRuntimeDomain,
    synchronous_runtime: EventProfileSynchronousRuntimeCoordinator,
) -> EventAssignmentRuntimeFacade:
    """Validate profile/domain/O1 identity, then discard the raw domain."""

    if type(resolved_assignment_profile) is not ResolvedEventGatedAssignmentProfile:
        raise EventAssignmentRuntimeFacadeError(
            "event facade composition requires the exact event profile",
            failure_code="facade_composition_profile_type",
            stage="facade_compose",
            expected=ResolvedEventGatedAssignmentProfile,
            actual=type(resolved_assignment_profile),
        )
    if type(runtime_domain) is not _EventProfileLifecycleRuntimeDomain:
        raise EventAssignmentRuntimeFacadeError(
            "event facade composition requires the exact retained domain type",
            failure_code="facade_composition_domain_type",
            stage="facade_compose",
            expected=_EventProfileLifecycleRuntimeDomain,
            actual=type(runtime_domain),
        )
    identity = runtime_domain.identity
    if identity.profile is not resolved_assignment_profile:
        raise EventAssignmentRuntimeFacadeError(
            "event facade profile is not the retained domain profile object",
            failure_code="facade_composition_profile_identity",
            stage="facade_compose",
            expected=id(identity.profile),
            actual=id(resolved_assignment_profile),
        )
    domain_identity = runtime_domain.current_read_port.domain_identity
    return EventAssignmentRuntimeFacade(
        synchronous_runtime=synchronous_runtime,
        resolved_assignment_profile=resolved_assignment_profile,
        domain_identity=domain_identity,
        factory_capability=_FACADE_FACTORY_CAPABILITY,
    )


__all__: tuple[str, ...] = ()
