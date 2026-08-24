"""Pure, dormant B1W inter-step claim-window admission primitives.

This module owns no lock, StateStore, publication pointer, terminal store,
environment, wrapper, resolver, controller, or health authority.  One retained
event-profile runtime domain owns one fence and drives it only while holding
the already-existing domain operation/admission lock.
"""

from __future__ import annotations


CANONICAL_ASSIGNMENT_INTERSTEP_CLAIM_WINDOW_RUNTIME_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_interstep_claim_window_runtime"
)
ASSIGNMENT_INTERSTEP_CLAIM_WINDOW_RUNTIME_SOURCE_PURPOSE = (
    "pure dormant default-off inter-step claim-window admission foundation"
)

if __name__ != CANONICAL_ASSIGNMENT_INTERSTEP_CLAIM_WINDOW_RUNTIME_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: inter-step claim-window runtime source "
        "must execute under its canonical module key; "
        f"expected={CANONICAL_ASSIGNMENT_INTERSTEP_CLAIM_WINDOW_RUNTIME_MODULE!r}; "
        f"actual={__name__!r}"
    )


from contextvars import ContextVar
from dataclasses import dataclass, field
from enum import Enum

from .assignment_initial_claim_runtime import (
    InitialClaimRequest,
    _CurrentPublicationIdentity,
    _EventRuntimeCurrentPublication,
)


_INT64_MAX = 2**63 - 1


class InterStepClaimWindowRuntimeError(RuntimeError):
    """Typed B1W-private admission/capability failure."""

    def __init__(
        self,
        message: str,
        *,
        failure_code: str,
        stage: str,
        expected: object = None,
        actual: object = None,
    ) -> None:
        if type(failure_code) is not str or not failure_code:
            raise TypeError("failure_code must be a non-empty exact string")
        self.failure_code = failure_code
        self.stage = stage
        self.expected = expected
        self.actual = actual
        super().__init__(
            f"{message}; failure_code={failure_code!r}; stage={stage!r}; "
            f"expected={expected!r}; actual={actual!r}"
        )


class _ClaimWindowFencePhase(Enum):
    PREBOOTSTRAP_CLOSED = "prebootstrap_closed"
    OPEN = "open"
    STEP_IN_FLIGHT = "step_in_flight"
    RESET_IN_FLIGHT = "reset_in_flight"
    FAULTED = "faulted"


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _ClaimWindowIdentity:
    """Opaque domain-lifetime identity for one concrete OPEN interval."""

    serial: int
    _domain_identity: object = field(repr=False)
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        serial: int,
        domain_identity: object,
        factory_capability: object,
    ) -> "_ClaimWindowIdentity":
        _require_serial(serial, stage="window_identity")
        instance = object.__new__(cls)
        object.__setattr__(instance, "serial", serial)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _AdmissionIdentity:
    """Opaque domain-lifetime identity shared by neither windows nor claims."""

    serial: int
    kind: str
    _domain_identity: object = field(repr=False)
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        serial: int,
        kind: str,
        domain_identity: object,
        factory_capability: object,
    ) -> "_AdmissionIdentity":
        _require_serial(serial, stage="admission_identity")
        if kind not in ("physical_step", "standalone_reset"):
            raise InterStepClaimWindowRuntimeError(
                "admission identity kind is invalid",
                failure_code="admission_identity_kind",
                stage="admission_identity",
                expected=("physical_step", "standalone_reset"),
                actual=kind,
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "serial", serial)
        object.__setattr__(instance, "kind", kind)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _PhysicalStepAdmission:
    """Immutable S4 admission binding one closed window to final semantic state."""

    _domain_identity: object = field(repr=False)
    _source_window: _ClaimWindowIdentity = field(repr=False)
    _admitted_publication: _EventRuntimeCurrentPublication = field(repr=False)
    _admitted_publication_identity: _CurrentPublicationIdentity = field(repr=False)
    admitted_store_version: int
    _identity: _AdmissionIdentity = field(repr=False)
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        domain_identity: object,
        source_window: _ClaimWindowIdentity,
        admitted_publication: _EventRuntimeCurrentPublication,
        identity: _AdmissionIdentity,
        factory_capability: object,
    ) -> "_PhysicalStepAdmission":
        if (
            type(source_window) is not _ClaimWindowIdentity
            or source_window._domain_identity is not domain_identity
            or source_window._factory_capability is not factory_capability
            or type(admitted_publication) is not _EventRuntimeCurrentPublication
            or type(identity) is not _AdmissionIdentity
            or identity.kind != "physical_step"
            or identity._domain_identity is not domain_identity
            or identity._factory_capability is not factory_capability
        ):
            raise InterStepClaimWindowRuntimeError(
                "physical-step admission lacks exact factory/domain bindings",
                failure_code="physical_step_admission_context",
                stage="physical_step_admission_create",
                expected="factory-bound window/publication/admission",
                actual=(type(source_window), type(admitted_publication), type(identity)),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_source_window", source_window)
        object.__setattr__(instance, "_admitted_publication", admitted_publication)
        object.__setattr__(
            instance,
            "_admitted_publication_identity",
            admitted_publication.publication_identity,
        )
        object.__setattr__(instance, "admitted_store_version", admitted_publication.store_version)
        object.__setattr__(instance, "_identity", identity)
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance

    @property
    def identity(self) -> _AdmissionIdentity:
        return self._identity

    @property
    def source_window(self) -> _ClaimWindowIdentity:
        return self._source_window

    @property
    def admitted_publication(self) -> _EventRuntimeCurrentPublication:
        return self._admitted_publication

    @property
    def admitted_publication_identity(self) -> _CurrentPublicationIdentity:
        return self._admitted_publication_identity


@dataclass(frozen=True, slots=True, init=False, eq=False)
class _StandaloneResetAdmission:
    """Immutable O1 admission for one full standalone reset call."""

    _domain_identity: object = field(repr=False)
    _source_window: _ClaimWindowIdentity | None = field(repr=False)
    _identity: _AdmissionIdentity = field(repr=False)
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        domain_identity: object,
        source_window: _ClaimWindowIdentity | None,
        identity: _AdmissionIdentity,
        factory_capability: object,
    ) -> "_StandaloneResetAdmission":
        if (
            (
                source_window is not None
                and (
                    type(source_window) is not _ClaimWindowIdentity
                    or source_window._domain_identity is not domain_identity
                    or source_window._factory_capability is not factory_capability
                )
            )
            or type(identity) is not _AdmissionIdentity
            or identity.kind != "standalone_reset"
            or identity._domain_identity is not domain_identity
            or identity._factory_capability is not factory_capability
        ):
            raise InterStepClaimWindowRuntimeError(
                "reset admission lacks exact factory/domain bindings",
                failure_code="reset_admission_context",
                stage="reset_admission_create",
                expected="factory-bound optional window/reset admission",
                actual=(type(source_window), type(identity)),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_source_window", source_window)
        object.__setattr__(instance, "_identity", identity)
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance

    @property
    def identity(self) -> _AdmissionIdentity:
        return self._identity

    @property
    def source_window(self) -> _ClaimWindowIdentity | None:
        return self._source_window


@dataclass(frozen=True, slots=True, init=False, eq=False)
class RuntimeClaimAdmissionEnvelope:
    """Immutable W2 binding of an unchanged B1 request to one OPEN window."""

    _domain_identity: object = field(repr=False)
    _request: InitialClaimRequest = field(repr=False)
    _window: _ClaimWindowIdentity = field(repr=False)
    serial: int
    _factory_capability: object = field(repr=False)

    @classmethod
    def _create(
        cls,
        *,
        domain_identity: object,
        request: InitialClaimRequest,
        window: _ClaimWindowIdentity,
        serial: int,
        factory_capability: object,
    ) -> "RuntimeClaimAdmissionEnvelope":
        _require_serial(serial, stage="claim_envelope_identity")
        if (
            type(request) is not InitialClaimRequest
            or type(window) is not _ClaimWindowIdentity
            or window._domain_identity is not domain_identity
            or window._factory_capability is not factory_capability
        ):
            raise InterStepClaimWindowRuntimeError(
                "production claim envelope lacks exact request/window bindings",
                failure_code="claim_window_context",
                stage="claim_envelope_create",
                expected="exact B1 request and current factory-bound window",
                actual=(type(request), type(window)),
            )
        instance = object.__new__(cls)
        object.__setattr__(instance, "_domain_identity", domain_identity)
        object.__setattr__(instance, "_request", request)
        object.__setattr__(instance, "_window", window)
        object.__setattr__(instance, "serial", serial)
        object.__setattr__(instance, "_factory_capability", factory_capability)
        return instance

    @property
    def request(self) -> InitialClaimRequest:
        return self._request

    @property
    def window(self) -> _ClaimWindowIdentity:
        return self._window


@dataclass(frozen=True, slots=True, eq=False)
class _ClaimWindowFenceView:
    """Read-only private projection; never a state-writer capability."""

    phase: _ClaimWindowFencePhase
    window: _ClaimWindowIdentity | None
    active_step: _PhysicalStepAdmission | None
    active_reset: _StandaloneResetAdmission | None
    next_window_serial: int
    next_admission_serial: int
    next_envelope_serial: int


class _InterStepClaimWindowFence:
    """One lock-free state owner driven under the retained domain lock."""

    __slots__ = (
        "_domain_identity",
        "_factory_capability",
        "_phase",
        "_window",
        "_active_step",
        "_active_reset",
        "_step_entry_validated",
        "_step_finalization_validated",
        "_internal_autoreset_entry_validated",
        "_reset_entry_validated",
        "_next_window_serial",
        "_next_admission_serial",
        "_next_envelope_serial",
        "_active_call",
    )

    def __init__(self, *, domain_identity: object) -> None:
        self._domain_identity = domain_identity
        self._factory_capability = object()
        self._phase = _ClaimWindowFencePhase.PREBOOTSTRAP_CLOSED
        self._window: _ClaimWindowIdentity | None = None
        self._active_step: _PhysicalStepAdmission | None = None
        self._active_reset: _StandaloneResetAdmission | None = None
        self._step_entry_validated = False
        self._step_finalization_validated = False
        self._internal_autoreset_entry_validated = False
        self._reset_entry_validated = False
        self._next_window_serial = 0
        self._next_admission_serial = 0
        self._next_envelope_serial = 0
        self._active_call: ContextVar[object | None] = ContextVar(
            f"b1w_admission_{id(domain_identity)}",
            default=None,
        )

    def _view(self, *, poisoned: bool) -> _ClaimWindowFenceView:
        return _ClaimWindowFenceView(
            phase=(
                _ClaimWindowFencePhase.FAULTED
                if poisoned
                else self._phase
            ),
            window=(None if poisoned else self._window),
            active_step=self._active_step,
            active_reset=self._active_reset,
            next_window_serial=self._next_window_serial,
            next_admission_serial=self._next_admission_serial,
            next_envelope_serial=self._next_envelope_serial,
        )

    def _require_open_for_claim_prepare(self) -> _ClaimWindowIdentity:
        if self._phase is _ClaimWindowFencePhase.STEP_IN_FLIGHT:
            raise InterStepClaimWindowRuntimeError(
                "production claim preparation is forbidden during a physical step",
                failure_code="runtime_step_in_flight",
                stage="claim_window_prepare",
                expected=_ClaimWindowFencePhase.OPEN,
                actual=self._phase,
            )
        if self._phase is not _ClaimWindowFencePhase.OPEN or self._window is None:
            raise InterStepClaimWindowRuntimeError(
                "production claim preparation requires an OPEN window",
                failure_code="claim_window_not_open",
                stage="claim_window_prepare",
                expected=_ClaimWindowFencePhase.OPEN,
                actual=self._phase,
            )
        return self._window

    def _create_claim_envelope(
        self,
        *,
        request: InitialClaimRequest,
        window: _ClaimWindowIdentity,
    ) -> RuntimeClaimAdmissionEnvelope:
        if self._phase is not _ClaimWindowFencePhase.OPEN or self._window is not window:
            raise InterStepClaimWindowRuntimeError(
                "claim window changed during production request preparation",
                failure_code="stale_claim_window",
                stage="claim_window_prepare",
                expected=id(window),
                actual=None if self._window is None else id(self._window),
            )
        serial = self._allocate_serial("_next_envelope_serial", stage="claim_envelope_identity")
        return RuntimeClaimAdmissionEnvelope._create(
            domain_identity=self._domain_identity,
            request=request,
            window=window,
            serial=serial,
            factory_capability=self._factory_capability,
        )

    def _validate_claim_envelope(
        self,
        envelope: object,
    ) -> RuntimeClaimAdmissionEnvelope:
        if (
            type(envelope) is not RuntimeClaimAdmissionEnvelope
            or envelope._domain_identity is not self._domain_identity
            or envelope._factory_capability is not self._factory_capability
            or type(envelope._request) is not InitialClaimRequest
            or type(envelope._window) is not _ClaimWindowIdentity
        ):
            raise InterStepClaimWindowRuntimeError(
                "production claim envelope is foreign or altered",
                failure_code="claim_window_context",
                stage="claim_window_commit",
                expected="exact retained-domain envelope",
                actual=type(envelope),
            )
        if (
            self._phase is not _ClaimWindowFencePhase.OPEN
            or self._window is not envelope._window
        ):
            raise InterStepClaimWindowRuntimeError(
                "the envelope's bound claim window is no longer current and OPEN",
                failure_code="stale_claim_window",
                stage="claim_window_commit",
                expected=id(envelope._window),
                actual=(self._phase, None if self._window is None else id(self._window)),
            )
        return envelope

    def _begin_full_reset(self) -> _StandaloneResetAdmission:
        if self._phase is _ClaimWindowFencePhase.PREBOOTSTRAP_CLOSED:
            source_window = None
        elif self._phase is _ClaimWindowFencePhase.OPEN and self._window is not None:
            source_window = self._window
        else:
            raise InterStepClaimWindowRuntimeError(
                "standalone reset admission requires prebootstrap or OPEN",
                failure_code="reset_admission_required",
                stage="reset_admission_begin",
                expected=(
                    _ClaimWindowFencePhase.PREBOOTSTRAP_CLOSED,
                    _ClaimWindowFencePhase.OPEN,
                ),
                actual=self._phase,
            )
        identity = self._allocate_admission_identity(kind="standalone_reset")
        admission = _StandaloneResetAdmission._create(
            domain_identity=self._domain_identity,
            source_window=source_window,
            identity=identity,
            factory_capability=self._factory_capability,
        )
        self._phase = _ClaimWindowFencePhase.RESET_IN_FLIGHT
        self._window = None
        self._active_reset = admission
        self._reset_entry_validated = False
        self._active_call.set(admission)
        return admission

    def _begin_physical_step(
        self,
        *,
        publication: _EventRuntimeCurrentPublication,
    ) -> _PhysicalStepAdmission:
        self._require_open_for_step_begin()
        if self._window is None:
            raise AssertionError("OPEN fence lost its exact window")
        if type(publication) is not _EventRuntimeCurrentPublication:
            raise InterStepClaimWindowRuntimeError(
                "physical-step admission requires the exact current P2 publication",
                failure_code="physical_step_publication",
                stage="physical_step_admission_begin",
                expected=_EventRuntimeCurrentPublication,
                actual=type(publication),
            )
        source_window = self._window
        identity = self._allocate_admission_identity(kind="physical_step")
        admission = _PhysicalStepAdmission._create(
            domain_identity=self._domain_identity,
            source_window=source_window,
            admitted_publication=publication,
            identity=identity,
            factory_capability=self._factory_capability,
        )
        self._phase = _ClaimWindowFencePhase.STEP_IN_FLIGHT
        self._window = None
        self._active_step = admission
        self._step_entry_validated = False
        self._step_finalization_validated = False
        self._internal_autoreset_entry_validated = False
        self._active_call.set(admission)
        return admission

    def _require_open_for_step_begin(self) -> _ClaimWindowIdentity:
        if self._phase is not _ClaimWindowFencePhase.OPEN or self._window is None:
            raise InterStepClaimWindowRuntimeError(
                "physical-step admission requires an exact OPEN window",
                failure_code="physical_step_admission_required",
                stage="physical_step_admission_begin",
                expected=_ClaimWindowFencePhase.OPEN,
                actual=self._phase,
            )
        return self._window

    def _validate_step_entry(self, admission: object) -> None:
        active = self._require_active_step(admission, stage="physical_step_entry")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "physical-step entry lacks the exact call-local admission",
                failure_code="physical_step_admission_required",
                stage="physical_step_entry",
                expected=id(active),
                actual=None,
            )
        if self._step_entry_validated:
            raise InterStepClaimWindowRuntimeError(
                "physical-step entry was already validated",
                failure_code="admission_already_consumed",
                stage="physical_step_entry",
                expected=False,
                actual=True,
            )
        self._step_entry_validated = True

    def _validate_step_entry_for_active_call(self) -> None:
        """Consume the entry latch from the exact call-local step admission."""

        self._validate_step_entry(self._active_call.get())

    def _validate_step_finalization(self, admission: object) -> None:
        active = self._require_active_step(admission, stage="physical_step_finalization")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "physical finalization lacks the exact call-local admission",
                failure_code="physical_step_admission_required",
                stage="physical_step_finalization",
                expected=id(active),
                actual=None,
            )
        if not self._step_entry_validated:
            raise InterStepClaimWindowRuntimeError(
                "physical finalization requires validated environment entry",
                failure_code="physical_step_admission_required",
                stage="physical_step_finalization",
                expected=True,
                actual=False,
            )
        if self._step_finalization_validated:
            raise InterStepClaimWindowRuntimeError(
                "physical finalization was already validated",
                failure_code="admission_already_consumed",
                stage="physical_step_finalization",
                expected=False,
                actual=True,
            )
        self._step_finalization_validated = True

    def _validate_step_finalization_for_active_call(self) -> None:
        """Consume the I3 latch from the exact call-local step admission."""

        self._validate_step_finalization(self._active_call.get())

    def _validate_internal_autoreset_entry(self, admission: object) -> None:
        active = self._require_active_step(admission, stage="internal_autoreset_entry")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "internal autoreset lacks the exact call-local step admission",
                failure_code="physical_step_admission_required",
                stage="internal_autoreset_entry",
                expected=id(active),
                actual=None,
            )
        if not self._step_entry_validated or not self._step_finalization_validated:
            raise InterStepClaimWindowRuntimeError(
                "internal autoreset requires validated entry and I3 finalization",
                failure_code="physical_step_admission_required",
                stage="internal_autoreset_entry",
                expected=(True, True),
                actual=(self._step_entry_validated, self._step_finalization_validated),
            )
        if self._internal_autoreset_entry_validated:
            raise InterStepClaimWindowRuntimeError(
                "internal autoreset entry was already validated",
                failure_code="admission_already_consumed",
                stage="internal_autoreset_entry",
                expected=False,
                actual=True,
            )
        self._internal_autoreset_entry_validated = True

    def _validate_reset_entry(self, admission: object) -> None:
        active = self._require_active_reset(admission, stage="reset_entry")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "reset entry lacks the exact call-local admission",
                failure_code="reset_admission_required",
                stage="reset_entry",
                expected=id(active),
                actual=None,
            )
        if self._reset_entry_validated:
            raise InterStepClaimWindowRuntimeError(
                "reset entry was already validated",
                failure_code="admission_already_consumed",
                stage="reset_entry",
                expected=False,
                actual=True,
            )
        self._reset_entry_validated = True

    def _validate_reset_entry_for_active_call(self) -> None:
        """Consume the legal standalone-reset or internal-autoreset latch."""

        if self._phase is _ClaimWindowFencePhase.RESET_IN_FLIGHT:
            self._validate_reset_entry(self._active_call.get())
            return
        if self._phase is _ClaimWindowFencePhase.STEP_IN_FLIGHT:
            self._validate_internal_autoreset_entry(self._active_call.get())
            return
        raise InterStepClaimWindowRuntimeError(
            "environment reset entry requires an admitted reset or active step autoreset",
            failure_code="reset_admission_required",
            stage="reset_entry",
            expected=(
                _ClaimWindowFencePhase.RESET_IN_FLIGHT,
                _ClaimWindowFencePhase.STEP_IN_FLIGHT,
            ),
            actual=self._phase,
        )

    def _require_step_finalization_validation_if_active(self) -> None:
        """Guard the lifecycle port against bypass during an admitted step."""

        if self._phase is not _ClaimWindowFencePhase.STEP_IN_FLIGHT:
            return
        active = self._require_active_step(
            self._active_call.get(),
            stage="physical_step_finalization_guard",
        )
        if not self._step_finalization_validated:
            raise InterStepClaimWindowRuntimeError(
                "lifecycle finalization requires the consumed exact-Ak validation latch",
                failure_code="physical_step_admission_required",
                stage="physical_step_finalization_guard",
                expected=True,
                actual=False,
            )
        if active is not self._active_step:
            raise AssertionError("active physical-step admission identity changed")

    def _require_reset_entry_validation_if_active(self) -> None:
        """Guard I1 against bypass during an admitted reset or autoreset."""

        if self._phase is _ClaimWindowFencePhase.RESET_IN_FLIGHT:
            active = self._require_active_reset(self._active_call.get(), stage="reset_entry_guard")
            validated = self._reset_entry_validated
        elif self._phase is _ClaimWindowFencePhase.STEP_IN_FLIGHT:
            active = self._require_active_step(
                self._active_call.get(),
                stage="internal_autoreset_entry_guard",
            )
            validated = self._internal_autoreset_entry_validated
        else:
            return
        if not validated:
            raise InterStepClaimWindowRuntimeError(
                "episode rebuild requires the consumed reset-entry validation latch",
                failure_code="reset_admission_required",
                stage="reset_entry_guard",
                expected=True,
                actual=False,
            )
        if active is not self._active_call.get():
            raise AssertionError("active reset/autoreset admission identity changed")

    def _complete_physical_step(self, admission: object) -> _ClaimWindowIdentity:
        active = self._require_active_step(admission, stage="physical_step_return")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "physical-step return lacks the exact call-local admission",
                failure_code="physical_step_admission_required",
                stage="physical_step_return",
                expected=id(active),
                actual=None,
            )
        if not self._step_entry_validated or not self._step_finalization_validated:
            raise InterStepClaimWindowRuntimeError(
                "physical-step return requires entry and finalization validation",
                failure_code="physical_step_admission_required",
                stage="physical_step_return",
                expected=(True, True),
                actual=(self._step_entry_validated, self._step_finalization_validated),
            )
        self._active_step = None
        self._step_entry_validated = False
        self._step_finalization_validated = False
        self._internal_autoreset_entry_validated = False
        self._active_call.set(None)
        return self._open_next_window()

    def _complete_full_reset(self, admission: object) -> _ClaimWindowIdentity:
        active = self._require_active_reset(admission, stage="reset_return")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "reset return lacks the exact call-local admission",
                failure_code="reset_admission_required",
                stage="reset_return",
                expected=id(active),
                actual=None,
            )
        if not self._reset_entry_validated:
            raise InterStepClaimWindowRuntimeError(
                "reset return requires validated reset entry",
                failure_code="reset_admission_required",
                stage="reset_return",
                expected=True,
                actual=False,
            )
        self._active_reset = None
        self._reset_entry_validated = False
        self._active_call.set(None)
        return self._open_next_window()

    def _validate_abnormal_step(self, admission: object) -> None:
        active = self._require_active_step(admission, stage="physical_step_failure")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "physical-step failure lacks the exact call-local admission",
                failure_code="physical_step_admission_required",
                stage="physical_step_failure",
                expected=id(active),
                actual=None,
            )
        self._active_call.set(None)

    def _validate_abnormal_reset(self, admission: object) -> None:
        active = self._require_active_reset(admission, stage="reset_failure")
        if self._active_call.get() is not active:
            raise InterStepClaimWindowRuntimeError(
                "reset failure lacks the exact call-local admission",
                failure_code="reset_admission_required",
                stage="reset_failure",
                expected=id(active),
                actual=None,
            )
        self._active_call.set(None)

    def _require_active_step(
        self,
        admission: object,
        *,
        stage: str,
    ) -> _PhysicalStepAdmission:
        if (
            type(admission) is not _PhysicalStepAdmission
            or admission._domain_identity is not self._domain_identity
            or admission._factory_capability is not self._factory_capability
        ):
            raise InterStepClaimWindowRuntimeError(
                "operation requires an exact retained-domain step admission",
                failure_code="physical_step_admission_required",
                stage=stage,
                expected=_PhysicalStepAdmission,
                actual=type(admission),
            )
        if (
            self._phase is not _ClaimWindowFencePhase.STEP_IN_FLIGHT
            or self._active_step is not admission
        ):
            raise InterStepClaimWindowRuntimeError(
                "physical-step admission is stale or already consumed",
                failure_code="admission_already_consumed",
                stage=stage,
                expected=id(self._active_step) if self._active_step is not None else None,
                actual=id(admission),
            )
        return admission

    def _require_active_reset(
        self,
        admission: object,
        *,
        stage: str,
    ) -> _StandaloneResetAdmission:
        if (
            type(admission) is not _StandaloneResetAdmission
            or admission._domain_identity is not self._domain_identity
            or admission._factory_capability is not self._factory_capability
        ):
            raise InterStepClaimWindowRuntimeError(
                "operation requires an exact retained-domain reset admission",
                failure_code="reset_admission_required",
                stage=stage,
                expected=_StandaloneResetAdmission,
                actual=type(admission),
            )
        if (
            self._phase is not _ClaimWindowFencePhase.RESET_IN_FLIGHT
            or self._active_reset is not admission
        ):
            raise InterStepClaimWindowRuntimeError(
                "reset admission is stale or already consumed",
                failure_code="admission_already_consumed",
                stage=stage,
                expected=id(self._active_reset) if self._active_reset is not None else None,
                actual=id(admission),
            )
        return admission

    def _open_next_window(self) -> _ClaimWindowIdentity:
        serial = self._allocate_serial("_next_window_serial", stage="window_identity")
        window = _ClaimWindowIdentity._create(
            serial=serial,
            domain_identity=self._domain_identity,
            factory_capability=self._factory_capability,
        )
        self._phase = _ClaimWindowFencePhase.OPEN
        self._window = window
        return window

    def _allocate_admission_identity(self, *, kind: str) -> _AdmissionIdentity:
        serial = self._allocate_serial("_next_admission_serial", stage="admission_identity")
        return _AdmissionIdentity._create(
            serial=serial,
            kind=kind,
            domain_identity=self._domain_identity,
            factory_capability=self._factory_capability,
        )

    def _allocate_serial(self, field_name: str, *, stage: str) -> int:
        serial = getattr(self, field_name)
        if serial > _INT64_MAX:
            raise InterStepClaimWindowRuntimeError(
                "B1W identity space is exhausted",
                failure_code="admission_identity_overflow",
                stage=stage,
                expected=f"<= {_INT64_MAX}",
                actual=serial,
            )
        setattr(self, field_name, serial + 1)
        return serial


def _require_serial(serial: int, *, stage: str) -> None:
    if type(serial) is not int or not 0 <= serial <= _INT64_MAX:
        raise InterStepClaimWindowRuntimeError(
            "B1W identity serial must be an exact nonnegative int64",
            failure_code="admission_identity",
            stage=stage,
            expected=f"0..{_INT64_MAX}",
            actual=serial,
        )


__all__: tuple[str, ...] = ()
