"""Repository-local AST guards for the pure/static B2-R1 contract slice."""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_STATIC_GUARDS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_static_guards"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_STATIC_GUARDS_MODULE:
    raise ImportError(
        "CanonicalModuleIdentityError: B2-R1 static guards must be imported "
        "under their canonical module key before declaring types; "
        f"expected={CANONICAL_ASSIGNMENT_EVENT_TRAINING_STATIC_GUARDS_MODULE!r}; "
        f"actual={__name__!r}"
    )


import ast
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Sequence

from .assignment_event_training_evidence import B2RContractError, canonical_digest_v1


B2R_STATIC_GUARD_EVIDENCE_V1 = "b2r_static_guard_evidence_v1"

STOP_PUBLIC_ROUTE_OPEN = "STOP — B2-R PUBLIC_ROUTE_OPEN"
STOP_STOCK_FULL_ROW_ACTOR_PATH = "STOP — B2-R STOCK_FULL_ROW_ACTOR_PATH"
STOP_STOCK_RETURNS_BYPASS = "STOP — B2-R STOCK_RETURNS_BYPASS"
STOP_CRITIC_TRAINING_SLICE = "STOP — B2-R CRITIC_TRAINING_SLICE"
STOP_UNAUTHORIZED_BACKWARD = "STOP — B2-R UNAUTHORIZED_BACKWARD"
STOP_UNAUTHORIZED_OPTIMIZER_STEP = "STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP"
STOP_VALUENORM = "STOP — B2-R VALUENORM"


def _fail(message: str, *, stop_code: str, path: str, observed: object) -> None:
    raise B2RContractError(
        message,
        stop_code=stop_code,
        stage="static_source_guard",
        field_name=path,
        expected="no forbidden executable call/reference",
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


def _parsed(path: Path) -> tuple[str, ast.AST, str]:
    if not path.is_file():
        _fail("static guard target is not a file", stop_code=STOP_PUBLIC_ROUTE_OPEN, path=str(path), observed="missing")
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
        tree = ast.parse(text, filename=str(path))
    except (UnicodeDecodeError, SyntaxError) as exc:
        _fail("static guard target is not valid UTF-8 Python", stop_code=STOP_PUBLIC_ROUTE_OPEN, path=str(path), observed=str(exc))
    return text, tree, hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True, slots=True)
class B2RStaticGuardTargetV1:
    path: str
    source_sha256: str


@dataclass(frozen=True, slots=True)
class B2RStaticGuardEvidenceV1:
    guard_identity: str
    targets: tuple[B2RStaticGuardTargetV1, ...]
    checked_call_count: int
    violation_count: int
    schema_version: str = B2R_STATIC_GUARD_EVIDENCE_V1

    @property
    def evidence_digest(self) -> str:
        return canonical_digest_v1(self)


def _evidence(identity: str, targets: list[B2RStaticGuardTargetV1], calls: int) -> B2RStaticGuardEvidenceV1:
    return B2RStaticGuardEvidenceV1(
        guard_identity=identity,
        targets=tuple(sorted(targets, key=lambda item: item.path)),
        checked_call_count=calls,
        violation_count=0,
    )


def validate_no_stock_trainer_calls_v1(paths: Sequence[str | Path]) -> B2RStaticGuardEvidenceV1:
    """Reject direct use of the frozen stock trainer/update/return entrypoints."""

    targets: list[B2RStaticGuardTargetV1] = []
    checked = 0
    exact = {
        "OnPolicyHARunner.train",
        "HAPPO.train",
        "HAPPO.update",
        "VCritic.train",
        "VCritic.update",
    }
    for value in paths:
        path = Path(value).resolve()
        _, tree, digest = _parsed(path)
        targets.append(B2RStaticGuardTargetV1(str(path), digest))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            checked += 1
            name = _call_name(node.func)
            suffix = ".".join(name.split(".")[-2:])
            receiver = name.split(".")[-2].lower() if "." in name else ""
            leaf = name.split(".")[-1]
            forbidden = (
                suffix in exact
                or leaf == "compute_returns"
                or (leaf in {"train", "update"} and receiver in {"runner", "happo", "vcritic", "critic"})
            )
            if forbidden:
                if leaf == "compute_returns":
                    stop_code = STOP_STOCK_RETURNS_BYPASS
                elif receiver in {"vcritic", "critic"} or suffix.startswith("VCritic."):
                    stop_code = STOP_CRITIC_TRAINING_SLICE
                else:
                    stop_code = STOP_STOCK_FULL_ROW_ACTOR_PATH
                _fail("stock HARL trainer path is forbidden in B2-R1", stop_code=stop_code, path=str(path), observed=(name, node.lineno))
    return _evidence("no_stock_trainer_calls_v1", targets, checked)


def validate_no_training_mutation_calls_v1(paths: Sequence[str | Path]) -> B2RStaticGuardEvidenceV1:
    """Reject executable backward, optimizer-step, and ValueNorm-update calls."""

    targets: list[B2RStaticGuardTargetV1] = []
    checked = 0
    for value in paths:
        path = Path(value).resolve()
        _, tree, digest = _parsed(path)
        targets.append(B2RStaticGuardTargetV1(str(path), digest))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            checked += 1
            name = _call_name(node.func)
            parts = name.split(".")
            leaf = parts[-1]
            receiver = parts[-2].lower() if len(parts) > 1 else ""
            if leaf == "backward":
                _fail("backward execution is forbidden in B2-R1", stop_code=STOP_UNAUTHORIZED_BACKWARD, path=str(path), observed=(name, node.lineno))
            if leaf == "step" and ("optim" in receiver or "optimizer" in receiver):
                _fail("optimizer step execution is forbidden in B2-R1", stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP, path=str(path), observed=(name, node.lineno))
            if leaf == "update" and receiver in {"valuenorm", "value_normalizer", "normalizer"}:
                _fail("ValueNorm update execution is forbidden in B2-R1", stop_code=STOP_VALUENORM, path=str(path), observed=(name, node.lineno))
    return _evidence("no_training_mutation_calls_v1", targets, checked)


def validate_public_route_isolation_v1(
    paths: Sequence[str | Path], *, private_module_tokens: Sequence[str]
) -> B2RStaticGuardEvidenceV1:
    """Reject executable imports/references from current public route files."""

    tokens = tuple(private_module_tokens)
    targets: list[B2RStaticGuardTargetV1] = []
    checked = 0
    for value in paths:
        path = Path(value).resolve()
        text, tree, digest = _parsed(path)
        targets.append(B2RStaticGuardTargetV1(str(path), digest))
        checked += sum(1 for _ in ast.walk(tree))
        for token in tokens:
            if token in text:
                _fail("public/default route references private B2-R1 implementation", stop_code=STOP_PUBLIC_ROUTE_OPEN, path=str(path), observed=token)
    return _evidence("public_route_isolation_v1", targets, checked)


def validate_stock_trainer_source_text_v1(source: str, *, identity: str) -> B2RStaticGuardEvidenceV1:
    """Synthetic-fixture entrypoint for precise stock-path fault injection."""

    tree = ast.parse(source, filename=identity)
    checked = 0
    exact = {"OnPolicyHARunner.train", "HAPPO.train", "HAPPO.update", "VCritic.train", "VCritic.update"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        checked += 1
        name = _call_name(node.func)
        suffix = ".".join(name.split(".")[-2:])
        receiver = name.split(".")[-2].lower() if "." in name else ""
        leaf = name.split(".")[-1]
        if suffix in exact or leaf == "compute_returns" or (leaf in {"train", "update"} and receiver in {"runner", "happo", "vcritic", "critic"}):
            if leaf == "compute_returns":
                stop_code = STOP_STOCK_RETURNS_BYPASS
            elif receiver in {"vcritic", "critic"} or suffix.startswith("VCritic."):
                stop_code = STOP_CRITIC_TRAINING_SLICE
            else:
                stop_code = STOP_STOCK_FULL_ROW_ACTOR_PATH
            _fail("stock HARL trainer path is forbidden in B2-R1", stop_code=stop_code, path=identity, observed=(name, node.lineno))
    target = B2RStaticGuardTargetV1(identity, hashlib.sha256(source.encode("utf-8")).hexdigest())
    return _evidence("synthetic_no_stock_trainer_calls_v1", [target], checked)


def validate_training_mutation_source_text_v1(source: str, *, identity: str) -> B2RStaticGuardEvidenceV1:
    """Synthetic-fixture entrypoint for forbidden-mutation fault injection."""

    tree = ast.parse(source, filename=identity)
    checked = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        checked += 1
        name = _call_name(node.func)
        parts = name.split(".")
        leaf = parts[-1]
        receiver = parts[-2].lower() if len(parts) > 1 else ""
        if leaf == "backward":
            _fail("backward execution is forbidden in B2-R1", stop_code=STOP_UNAUTHORIZED_BACKWARD, path=identity, observed=(name, node.lineno))
        if leaf == "step" and ("optim" in receiver or "optimizer" in receiver):
            _fail("optimizer step execution is forbidden in B2-R1", stop_code=STOP_UNAUTHORIZED_OPTIMIZER_STEP, path=identity, observed=(name, node.lineno))
        if leaf == "update" and receiver in {"valuenorm", "value_normalizer", "normalizer"}:
            _fail("ValueNorm update execution is forbidden in B2-R1", stop_code=STOP_VALUENORM, path=identity, observed=(name, node.lineno))
    target = B2RStaticGuardTargetV1(identity, hashlib.sha256(source.encode("utf-8")).hexdigest())
    return _evidence("synthetic_no_training_mutation_calls_v1", [target], checked)


def validate_public_route_source_text_v1(source: str, *, identity: str, private_module_tokens: Sequence[str]) -> B2RStaticGuardEvidenceV1:
    """Synthetic-fixture entrypoint for public-route isolation faults."""

    tree = ast.parse(source, filename=identity)
    for token in private_module_tokens:
        if token in source:
            _fail("public/default route references private B2-R1 implementation", stop_code=STOP_PUBLIC_ROUTE_OPEN, path=identity, observed=token)
    target = B2RStaticGuardTargetV1(identity, hashlib.sha256(source.encode("utf-8")).hexdigest())
    return _evidence("synthetic_public_route_isolation_v1", [target], sum(1 for _ in ast.walk(tree)))


__all__: tuple[str, ...] = ()
