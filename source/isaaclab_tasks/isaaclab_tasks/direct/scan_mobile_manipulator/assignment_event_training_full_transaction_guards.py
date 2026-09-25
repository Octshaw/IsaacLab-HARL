"""Static/private dependency guards for the B2-R5 coordinator."""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_FULL_TRANSACTION_GUARDS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_full_transaction_guards"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_FULL_TRANSACTION_GUARDS_MODULE:
    raise ImportError("CanonicalModuleIdentityError: B2-R5 guards require canonical import")


import ast
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Mapping, Sequence

from .assignment_event_training_evidence import B2RContractError, canonical_digest_v1


STOP_PUBLIC_ROUTE_OPEN = "STOP — B2-R PUBLIC_ROUTE_OPEN"
STOP_UNAUTHORIZED_BACKWARD = "STOP — B2-R UNAUTHORIZED_BACKWARD"
STOP_UNAUTHORIZED_OPTIMIZER_STEP = "STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP"
STOP_VALUENORM = "STOP — B2-R VALUENORM"
STOP_STOCK_FULL_ROW_ACTOR_PATH = "STOP — B2-R STOCK_FULL_ROW_ACTOR_PATH"
STOP_CRITIC_TRAINING_SLICE = "STOP — B2-R CRITIC_TRAINING_SLICE"
STOP_STOCK_RETURNS_BYPASS = "STOP — B2-R STOCK_RETURNS_BYPASS"
STOP_AUTHORITY_DRIFT = "STOP — B2-R AUTHORITY_DRIFT"


def _fail(message: str, *, stop_code: str, identity: str, observed: object) -> None:
    raise B2RContractError(
        message, stop_code=stop_code, stage="r5_static_dependency_guard",
        field_name=identity, expected="reviewed unique private execution graph",
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
class B2R5DependencyGuardEvidenceV1:
    target_digests: tuple[tuple[str, str], ...]
    dependency_edges: tuple[tuple[str, str], ...]
    backward_executor_count: int
    actor_step_executor_count: int
    critic_step_executor_count: int
    live_valuenorm_executor_count: int
    r5_actor_sequence_call_count: int
    r5_critic_sequence_call_count: int
    scheduler_step_count: int
    violation_count: int
    schema_version: str = "b2r5_dependency_guard_evidence_v1"

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


class _ExecutionVisitor(ast.NodeVisitor):
    def __init__(self, identity: str, stem: str) -> None:
        self.identity = identity
        self.stem = stem
        self.functions: list[str] = []
        self.backward = 0
        self.actor_step = 0
        self.critic_step = 0
        self.valuenorm = 0
        self.r5_actor = 0
        self.r5_critic = 0
        self.scheduler = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node.func)
        leaf = name.split(".")[-1]
        current = self.functions[-1] if self.functions else "<module>"
        if leaf == "backward":
            if self.stem == "assignment_event_training_gradient_probe" and current == "_execute_backward_v1" and name == "loss.backward":
                self.backward += 1
            else:
                _fail("second/unreviewed backward executor", stop_code=STOP_UNAUTHORIZED_BACKWARD, identity=self.identity, observed=(name, current, node.lineno))
        if leaf == "step":
            if "scheduler" in name.lower():
                self.scheduler += 1
                _fail("scheduler step is forbidden", stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP, identity=self.identity, observed=(name, current, node.lineno))
            elif self.stem == "assignment_event_training_actor_mutation" and current == "_execute_actor_optimizer_step_v1" and name == "target.actor_optimizer.step":
                self.actor_step += 1
            elif self.stem == "assignment_event_training_critic_mutation" and current == "_execute_critic_optimizer_step_v1" and name == "critic.critic_optimizer.step":
                self.critic_step += 1
            elif current == "step" and ("trap" in self.identity.lower() or self.stem in {"assignment_event_training_gradient_probe", "assignment_event_training_actor_mutation", "assignment_event_training_critic_mutation"}):
                pass
            else:
                _fail("second/unreviewed optimizer executor", stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP, identity=self.identity, observed=(name, current, node.lineno))
        if leaf == "update":
            if self.stem == "assignment_event_training_critic_mutation" and current == "update" and name == "self.value_normalizer.update":
                self.valuenorm += 1
            elif current == "update" and "Trap" in self.identity:
                pass
            elif "valuenorm" in name.lower() or "normalizer" in name.lower():
                _fail("second/unreviewed live ValueNorm executor", stop_code=STOP_VALUENORM, identity=self.identity, observed=(name, current, node.lineno))
        if name == "R3.execute_actor_sequence_v1":
            self.r5_actor += 1
        if name == "R4.execute_critic_sequence_v1":
            self.r5_critic += 1
        if name in {"HAPPO.train", "HAPPO.update"}:
            _fail("stock HAPPO path is forbidden", stop_code=STOP_STOCK_FULL_ROW_ACTOR_PATH, identity=self.identity, observed=(name, node.lineno))
        if name in {"VCritic.train", "VCritic.update"}:
            _fail("stock VCritic path is forbidden", stop_code=STOP_CRITIC_TRAINING_SLICE, identity=self.identity, observed=(name, node.lineno))
        if leaf == "compute_returns":
            _fail("stock returns path is forbidden", stop_code=STOP_STOCK_RETURNS_BYPASS, identity=self.identity, observed=(name, node.lineno))
        self.generic_visit(node)


def _private_import_edges(tree: ast.AST, stem: str) -> tuple[tuple[str, str], ...]:
    edges: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module.startswith("assignment_event_training_"):
                edges.add((stem, module))
            for alias in node.names:
                if alias.name.startswith("assignment_event_training_"):
                    edges.add((stem, alias.name))
    return tuple(sorted(edges))


def validate_r5_dependency_graph_v1(
    paths: Sequence[str | Path], *, expected_edges: Sequence[tuple[str, str]]
) -> B2R5DependencyGuardEvidenceV1:
    totals = {"backward": 0, "actor": 0, "critic": 0, "vn": 0, "r5_actor": 0, "r5_critic": 0, "scheduler": 0}
    targets: list[tuple[str, str]] = []
    edges: set[tuple[str, str]] = set()
    for value in paths:
        path = Path(value).resolve()
        raw = path.read_bytes()
        tree = ast.parse(raw.decode("utf-8"), filename=str(path))
        visitor = _ExecutionVisitor(str(path), path.stem)
        visitor.visit(tree)
        totals["backward"] += visitor.backward
        totals["actor"] += visitor.actor_step
        totals["critic"] += visitor.critic_step
        totals["vn"] += visitor.valuenorm
        totals["r5_actor"] += visitor.r5_actor
        totals["r5_critic"] += visitor.r5_critic
        totals["scheduler"] += visitor.scheduler
        edges.update(_private_import_edges(tree, path.stem))
        targets.append((str(path), hashlib.sha256(raw).hexdigest()))
    expected_counts = (1, 1, 1, 1, 1, 1, 0)
    observed_counts = tuple(totals[key] for key in ("backward", "actor", "critic", "vn", "r5_actor", "r5_critic", "scheduler"))
    if observed_counts != expected_counts:
        _fail("unique executor cardinality drifted", stop_code=STOP_AUTHORITY_DRIFT, identity="aggregate", observed=observed_counts)
    actual_edges = tuple(sorted(edges))
    if actual_edges != tuple(sorted(expected_edges)):
        _fail("private dependency graph drifted", stop_code=STOP_AUTHORITY_DRIFT, identity="dependency_graph", observed=actual_edges)
    return B2R5DependencyGuardEvidenceV1(
        tuple(sorted(targets)), actual_edges,
        totals["backward"], totals["actor"], totals["critic"], totals["vn"],
        totals["r5_actor"], totals["r5_critic"], totals["scheduler"], 0,
    )


def validate_r5_public_isolation_v1(paths: Sequence[str | Path], *, private_tokens: Sequence[str]) -> B2R5DependencyGuardEvidenceV1:
    targets: list[tuple[str, str]] = []
    for value in paths:
        path = Path(value).resolve()
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        ast.parse(text, filename=str(path))
        for token in private_tokens:
            if token in text:
                _fail("production file references R5 private coordinator", stop_code=STOP_PUBLIC_ROUTE_OPEN, identity=str(path), observed=token)
        targets.append((str(path), hashlib.sha256(raw).hexdigest()))
    return B2R5DependencyGuardEvidenceV1(tuple(sorted(targets)), (), 0, 0, 0, 0, 0, 0, 0, 0)


def validate_r5_source_text_fault_v1(source: str, *, identity: str) -> None:
    visitor = _ExecutionVisitor(identity, "synthetic_fault")
    visitor.visit(ast.parse(source, filename=identity))


def validate_r5_public_source_text_v1(source: str, *, identity: str, private_tokens: Sequence[str]) -> None:
    ast.parse(source, filename=identity)
    for token in private_tokens:
        if token in source:
            _fail("public source references R5 private coordinator", stop_code=STOP_PUBLIC_ROUTE_OPEN, identity=identity, observed=token)


__all__: tuple[str, ...] = ()
