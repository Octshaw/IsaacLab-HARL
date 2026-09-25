"""Focused AST/public isolation guards for the private B2-R2 probe."""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_GRADIENT_GUARDS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_gradient_guards"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_GRADIENT_GUARDS_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R2 gradient guards must be imported "
        "under their canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TRAINING_GRADIENT_GUARDS_MODULE!r}; "
        f"actual={__name__!r}"
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
        stage="r2_static_source_guard",
        field_name=identity,
        expected="only reviewed B2-R2 executable seams",
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
class B2RGradientSourceGuardEvidenceV1:
    target_digests: tuple[tuple[str, str], ...]
    backward_call_count: int
    trapped_step_call_count: int
    trapped_live_valuenorm_call_count: int
    violation_count: int
    schema_version: str = "b2r_gradient_source_guard_evidence_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


class _R2Visitor(ast.NodeVisitor):
    def __init__(self, identity: str) -> None:
        self.identity = identity
        self.functions: list[str] = []
        self.backward_calls = 0
        self.trapped_steps = 0
        self.trapped_valuenorm = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
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
            if current != "_execute_backward_v1" or name != "loss.backward":
                _fail("backward call is outside the single reviewed R2 seam", stop_code=STOP_UNAUTHORIZED_BACKWARD, identity=self.identity, observed=(name, current, node.lineno))
            self.backward_calls += 1
        if leaf == "step":
            if not receiver.endswith("trap"):
                _fail("optimizer/scheduler step call is not trapped", stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP, identity=self.identity, observed=(name, current, node.lineno))
            self.trapped_steps += 1
        if leaf == "update" and ("valuenorm" in receiver or "normalizer" in receiver):
            if not receiver.endswith("trap"):
                _fail("live ValueNorm update call is not trapped", stop_code=STOP_VALUENORM, identity=self.identity, observed=(name, current, node.lineno))
            self.trapped_valuenorm += 1
        if suffix in {"OnPolicyHARunner.train", "HAPPO.train", "HAPPO.update"} or (leaf in {"train", "update"} and receiver in {"runner", "happo"}):
            _fail("stock actor/runner training call is forbidden", stop_code=STOP_STOCK_FULL_ROW_ACTOR_PATH, identity=self.identity, observed=(name, node.lineno))
        if suffix in {"VCritic.train", "VCritic.update"} or (leaf in {"train", "update"} and receiver in {"critic", "vcritic"}):
            _fail("stock critic training call is forbidden", stop_code=STOP_CRITIC_TRAINING_SLICE, identity=self.identity, observed=(name, node.lineno))
        if leaf == "compute_returns":
            _fail("stock returns computation is forbidden", stop_code=STOP_STOCK_RETURNS_BYPASS, identity=self.identity, observed=(name, node.lineno))
        self.generic_visit(node)


def validate_r2_gradient_source_guards_v1(
    paths: Sequence[str | Path],
) -> B2RGradientSourceGuardEvidenceV1:
    targets: list[tuple[str, str]] = []
    backward = 0
    steps = 0
    valuenorm = 0
    for value in paths:
        path = Path(value).resolve()
        raw = path.read_bytes()
        tree = ast.parse(raw.decode("utf-8"), filename=str(path))
        visitor = _R2Visitor(str(path))
        visitor.visit(tree)
        targets.append((str(path), hashlib.sha256(raw).hexdigest()))
        backward += visitor.backward_calls
        steps += visitor.trapped_steps
        valuenorm += visitor.trapped_valuenorm
    if backward != 1:
        _fail("R2 implementation must contain exactly one centralized backward call", stop_code=STOP_UNAUTHORIZED_BACKWARD, identity="aggregate", observed=backward)
    return B2RGradientSourceGuardEvidenceV1(
        target_digests=tuple(sorted(targets)),
        backward_call_count=backward,
        trapped_step_call_count=steps,
        trapped_live_valuenorm_call_count=valuenorm,
        violation_count=0,
    )


def validate_r2_public_isolation_v1(
    paths: Sequence[str | Path], *, private_tokens: Sequence[str]
) -> B2RGradientSourceGuardEvidenceV1:
    targets: list[tuple[str, str]] = []
    for value in paths:
        path = Path(value).resolve()
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        ast.parse(text, filename=str(path))
        for token in private_tokens:
            if token in text:
                _fail("production route references private R2 probe", stop_code=STOP_PUBLIC_ROUTE_OPEN, identity=str(path), observed=token)
        targets.append((str(path), hashlib.sha256(raw).hexdigest()))
    return B2RGradientSourceGuardEvidenceV1(
        target_digests=tuple(sorted(targets)),
        backward_call_count=0,
        trapped_step_call_count=0,
        trapped_live_valuenorm_call_count=0,
        violation_count=0,
    )


def validate_r2_source_text_fault_v1(source: str, *, identity: str) -> None:
    visitor = _R2Visitor(identity)
    visitor.visit(ast.parse(source, filename=identity))


__all__: tuple[str, ...] = ()
