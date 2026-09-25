"""AST and public-isolation guards for the private B2-R3 mutation seam."""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_ACTOR_MUTATION_GUARDS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_actor_mutation_guards"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_ACTOR_MUTATION_GUARDS_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R3 mutation guards require the "
        "canonical module key"
    )


import ast
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Sequence

from .assignment_event_training_evidence import B2RContractError, canonical_digest_v1


STOP_PUBLIC_ROUTE_OPEN = "STOP — B2-R PUBLIC_ROUTE_OPEN"
STOP_STOCK_FULL_ROW_ACTOR_PATH = "STOP — B2-R STOCK_FULL_ROW_ACTOR_PATH"
STOP_STOCK_RETURNS_BYPASS = "STOP — B2-R STOCK_RETURNS_BYPASS"
STOP_CRITIC_TRAINING_SLICE = "STOP — B2-R CRITIC_TRAINING_SLICE"
STOP_UNAUTHORIZED_BACKWARD = "STOP — B2-R UNAUTHORIZED_BACKWARD"
STOP_UNAUTHORIZED_OPTIMIZER_STEP = "STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP"
STOP_VALUENORM = "STOP — B2-R VALUENORM"


def _fail(message: str, *, stop_code: str, identity: str, observed: object) -> None:
    raise B2RContractError(
        message,
        stop_code=stop_code,
        stage="r3_static_source_guard",
        field_name=identity,
        expected="only the reviewed B2-R3 actor mutation seam",
        observed=observed,
    )


def _call_name(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


@dataclass(frozen=True, slots=True)
class B2R3MutationSourceGuardEvidenceV1:
    target_digests: tuple[tuple[str, str], ...]
    actor_step_call_count: int
    backward_call_count: int
    scheduler_step_call_count: int
    live_valuenorm_update_call_count: int
    violation_count: int
    schema_version: str = "b2r3_mutation_source_guard_evidence_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


class _R3Visitor(ast.NodeVisitor):
    def __init__(self, identity: str) -> None:
        self.identity = identity
        self.functions: list[str] = []
        self.actor_steps = 0
        self.backward_calls = 0
        self.scheduler_steps = 0
        self.valuenorm_updates = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)
        parts = name.split(".")
        leaf = parts[-1]
        receiver = parts[-2].lower() if len(parts) > 1 else ""
        current = self.functions[-1] if self.functions else "<module>"
        suffix = ".".join(parts[-2:])
        if leaf == "backward":
            self.backward_calls += 1
            _fail(
                "R3 must reuse the reviewed R2 backward seam",
                stop_code=STOP_UNAUTHORIZED_BACKWARD,
                identity=self.identity,
                observed=(name, current, node.lineno),
            )
        if leaf == "step":
            if receiver.endswith("trap"):
                pass
            elif current != "_execute_actor_optimizer_step_v1" or name != "target.actor_optimizer.step":
                if "scheduler" in name.lower():
                    self.scheduler_steps += 1
                _fail(
                    "step call is outside the one reviewed actor optimizer seam",
                    stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP,
                    identity=self.identity,
                    observed=(name, current, node.lineno),
                )
            else:
                self.actor_steps += 1
        if leaf == "update" and ("valuenorm" in receiver or "normalizer" in receiver):
            if not receiver.endswith("trap"):
                self.valuenorm_updates += 1
                _fail(
                    "live ValueNorm update is forbidden in R3",
                    stop_code=STOP_VALUENORM,
                    identity=self.identity,
                    observed=(name, current, node.lineno),
                )
        if suffix in {"OnPolicyHARunner.train", "HAPPO.train", "HAPPO.update"} or (
            leaf in {"train", "update"} and receiver in {"runner", "happo"}
        ):
            _fail("stock actor training is forbidden", stop_code=STOP_STOCK_FULL_ROW_ACTOR_PATH, identity=self.identity, observed=(name, node.lineno))
        if suffix in {"VCritic.train", "VCritic.update"} or (
            leaf in {"train", "update"} and receiver in {"critic", "vcritic"}
        ):
            _fail("critic training is forbidden", stop_code=STOP_CRITIC_TRAINING_SLICE, identity=self.identity, observed=(name, node.lineno))
        if leaf == "compute_returns":
            _fail("stock returns computation is forbidden", stop_code=STOP_STOCK_RETURNS_BYPASS, identity=self.identity, observed=(name, node.lineno))
        self.generic_visit(node)


def validate_r3_mutation_source_guards_v1(
    paths: Sequence[str | Path],
) -> B2R3MutationSourceGuardEvidenceV1:
    targets: list[tuple[str, str]] = []
    actor_steps = backward = scheduler = valuenorm = 0
    for value in paths:
        path = Path(value).resolve()
        raw = path.read_bytes()
        visitor = _R3Visitor(str(path))
        visitor.visit(ast.parse(raw.decode("utf-8"), filename=str(path)))
        targets.append((str(path), hashlib.sha256(raw).hexdigest()))
        actor_steps += visitor.actor_steps
        backward += visitor.backward_calls
        scheduler += visitor.scheduler_steps
        valuenorm += visitor.valuenorm_updates
    if actor_steps != 1 or backward != 0 or scheduler != 0 or valuenorm != 0:
        _fail(
            "R3 reviewed call-site cardinality drifted",
            stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP,
            identity="aggregate",
            observed=(actor_steps, backward, scheduler, valuenorm),
        )
    return B2R3MutationSourceGuardEvidenceV1(
        tuple(sorted(targets)), actor_steps, backward, scheduler, valuenorm, 0
    )


def validate_r3_public_isolation_v1(
    paths: Sequence[str | Path], *, private_tokens: Sequence[str]
) -> B2R3MutationSourceGuardEvidenceV1:
    targets: list[tuple[str, str]] = []
    for value in paths:
        path = Path(value).resolve()
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        ast.parse(text, filename=str(path))
        for token in private_tokens:
            if token in text:
                _fail("production route references private R3 seam", stop_code=STOP_PUBLIC_ROUTE_OPEN, identity=str(path), observed=token)
        targets.append((str(path), hashlib.sha256(raw).hexdigest()))
    return B2R3MutationSourceGuardEvidenceV1(tuple(sorted(targets)), 0, 0, 0, 0, 0)


def validate_r3_source_text_fault_v1(source: str, *, identity: str) -> None:
    visitor = _R3Visitor(identity)
    visitor.visit(ast.parse(source, filename=identity))


def validate_r3_public_source_text_v1(
    source: str, *, identity: str, private_tokens: Sequence[str]
) -> None:
    ast.parse(source, filename=identity)
    for token in private_tokens:
        if token in source:
            _fail(
                "public source references private R3 seam",
                stop_code=STOP_PUBLIC_ROUTE_OPEN,
                identity=identity,
                observed=token,
            )


__all__: tuple[str, ...] = ()
