"""Strict optimization-continuation checkpoints for assignment training.

This format is intentionally separate from the historical weight-only checkpoint
path.  It serializes every mutable learner component needed to resume an Adam
update sequence and publishes immutable generation directories atomically.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import torch

try:
    from .assignment_value_normalizer_checkpoint import (
        export_value_normalizer_checkpoint_state,
        inspect_value_normalizer_target,
        restore_value_normalizer_checkpoint_state,
        validate_value_normalizer_checkpoint_state,
    )
except ImportError:  # Direct file-based CPU qualification.
    from assignment_value_normalizer_checkpoint import (  # type: ignore
        export_value_normalizer_checkpoint_state,
        inspect_value_normalizer_target,
        restore_value_normalizer_checkpoint_state,
        validate_value_normalizer_checkpoint_state,
    )


OPTIMIZATION_CHECKPOINT_SCHEMA = "lifecycle_mrta_optimization_checkpoint_v1"
OPTIMIZATION_CHECKPOINT_POINTER_SCHEMA = "lifecycle_mrta_optimization_checkpoint_pointer_v1"
OPTIMIZATION_CHECKPOINT_PURPOSE = "optimization_continuation"
GENERATION_PATTERN = re.compile(r"^generation_(\d{8})$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class OptimizationCheckpointError(RuntimeError):
    """Base error for strict optimization checkpoint operations."""


class OptimizationCheckpointBoundaryError(OptimizationCheckpointError):
    """Raised before a save when the learner is not at a clean boundary."""


class OptimizationCheckpointValidationError(OptimizationCheckpointError):
    """Raised when a checkpoint is incomplete, incompatible, or corrupt."""


class OptimizationCheckpointLoadError(OptimizationCheckpointError):
    """Raised when applying a fully validated checkpoint fails."""


@dataclass(frozen=True)
class OptimizationCheckpointBoundaryState:
    transaction_complete: bool
    partial_update: bool
    optimizer_mutation_complete: bool
    value_normalizer_mutation_complete: bool
    active_backward: bool
    active_optimizer_step: bool
    active_load: bool
    poisoned: bool

    @classmethod
    def clean(cls) -> "OptimizationCheckpointBoundaryState":
        return cls(True, False, True, True, False, False, False, False)

    def assert_saveable(self) -> None:
        failures = []
        if not self.transaction_complete:
            failures.append("transaction_complete=false")
        if self.partial_update:
            failures.append("partial_update=true")
        if not self.optimizer_mutation_complete:
            failures.append("optimizer_mutation_complete=false")
        if not self.value_normalizer_mutation_complete:
            failures.append("value_normalizer_mutation_complete=false")
        if self.active_backward:
            failures.append("active_backward=true")
        if self.active_optimizer_step:
            failures.append("active_optimizer_step=true")
        if self.active_load:
            failures.append("active_load=true")
        if self.poisoned:
            failures.append("poisoned=true")
        if failures:
            raise OptimizationCheckpointBoundaryError(
                "OPTIMIZATION_CHECKPOINT_SAVE_BOUNDARY_REJECTED: " + ", ".join(failures)
            )


class OptimizationCheckpointRuntimeGuard:
    """Mutable runner-side guard whose snapshots gate save and load operations."""

    def __init__(self) -> None:
        self._transaction_complete = False
        self._partial_update = False
        self._optimizer_mutation_complete = False
        self._value_normalizer_mutation_complete = False
        self._active_backward = False
        self._active_optimizer_step = False
        self._active_load = False
        self._poisoned = False

    def mark_rollout_or_update_started(self) -> None:
        self._transaction_complete = False
        self._optimizer_mutation_complete = False
        self._value_normalizer_mutation_complete = False

    def mark_update_complete(self) -> None:
        self._transaction_complete = True
        self._partial_update = False
        self._optimizer_mutation_complete = True
        self._value_normalizer_mutation_complete = True
        self._active_backward = False
        self._active_optimizer_step = False

    def mark_update_failed(self) -> None:
        self._transaction_complete = False
        self._partial_update = True
        self._optimizer_mutation_complete = False
        self._value_normalizer_mutation_complete = False
        self._active_backward = False
        self._active_optimizer_step = False
        self._poisoned = True

    def begin_load(self) -> None:
        if self._active_load:
            raise OptimizationCheckpointBoundaryError(
                "OPTIMIZATION_CHECKPOINT_LOAD_REJECTED: another load is active"
            )
        if self._active_backward or self._active_optimizer_step:
            raise OptimizationCheckpointBoundaryError(
                "OPTIMIZATION_CHECKPOINT_LOAD_REJECTED: learner mutation is active"
            )
        if self._poisoned or self._partial_update:
            raise OptimizationCheckpointBoundaryError(
                "OPTIMIZATION_CHECKPOINT_LOAD_REJECTED: target learner is poisoned or partially updated"
            )
        self._active_load = True

    def end_load(self) -> None:
        self._active_load = False

    def snapshot(self) -> OptimizationCheckpointBoundaryState:
        return OptimizationCheckpointBoundaryState(
            transaction_complete=self._transaction_complete,
            partial_update=self._partial_update,
            optimizer_mutation_complete=self._optimizer_mutation_complete,
            value_normalizer_mutation_complete=self._value_normalizer_mutation_complete,
            active_backward=self._active_backward,
            active_optimizer_step=self._active_optimizer_step,
            active_load=self._active_load,
            poisoned=self._poisoned,
        )


@dataclass(frozen=True)
class OptimizationProgressionState:
    completed_update_index: int
    total_update_count: int
    next_update_index: int
    linear_lr_schedule_position: int

    def __post_init__(self) -> None:
        values = (
            self.completed_update_index,
            self.total_update_count,
            self.next_update_index,
            self.linear_lr_schedule_position,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise ValueError("optimization progression fields must be integers")
        if self.completed_update_index < 0 or self.total_update_count <= 0:
            raise ValueError("optimization progression indices must be nonnegative and total positive")
        if self.completed_update_index > self.total_update_count:
            raise ValueError("completed_update_index must not exceed total_update_count")
        if self.next_update_index != self.completed_update_index + 1:
            raise ValueError("next_update_index must equal completed_update_index + 1")
        if self.linear_lr_schedule_position != self.next_update_index:
            raise ValueError("linear_lr_schedule_position must equal next_update_index")

    @classmethod
    def after_update(cls, completed_update_index: int, total_update_count: int) -> "OptimizationProgressionState":
        return cls(
            completed_update_index=completed_update_index,
            total_update_count=total_update_count,
            next_update_index=completed_update_index + 1,
            linear_lr_schedule_position=completed_update_index + 1,
        )

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> "OptimizationProgressionState":
        required = {
            "completed_update_index",
            "total_update_count",
            "next_update_index",
            "linear_lr_schedule_position",
        }
        _require_exact_keys("progression", mapping, required)
        try:
            return cls(**{key: mapping[key] for key in required})
        except (TypeError, ValueError) as exc:
            raise OptimizationCheckpointValidationError(f"invalid progression state: {exc}") from exc

    def to_mapping(self) -> dict[str, int]:
        return {
            "completed_update_index": self.completed_update_index,
            "total_update_count": self.total_update_count,
            "next_update_index": self.next_update_index,
            "linear_lr_schedule_position": self.linear_lr_schedule_position,
        }


class OptimizationProgressionTracker:
    def __init__(self, state: OptimizationProgressionState) -> None:
        self._state = state

    @property
    def state(self) -> OptimizationProgressionState:
        return self._state

    def replace(self, state: OptimizationProgressionState) -> None:
        if not isinstance(state, OptimizationProgressionState):
            raise TypeError("progression tracker requires OptimizationProgressionState")
        self._state = state

    def record_completed_update(self) -> OptimizationProgressionState:
        completed = self._state.next_update_index
        if completed > self._state.total_update_count:
            raise OptimizationCheckpointBoundaryError(
                "optimization progression cannot advance beyond total_update_count"
            )
        self._state = OptimizationProgressionState.after_update(
            completed,
            self._state.total_update_count,
        )
        return self._state


def linear_lr_for_next_update(initial_lr: float, progression: OptimizationProgressionState) -> float:
    """Mirror HARL's linear schedule at the checkpoint's exact next position."""

    if isinstance(initial_lr, bool) or not isinstance(initial_lr, (int, float)) or not math.isfinite(initial_lr):
        raise ValueError("initial_lr must be finite numeric")
    if initial_lr < 0:
        raise ValueError("initial_lr must be nonnegative")
    position = min(progression.linear_lr_schedule_position, progression.total_update_count)
    return float(initial_lr) - float(initial_lr) * (position / progression.total_update_count)


@dataclass(frozen=True)
class OptimizationCheckpointSaveResult:
    generation: int
    generation_directory: Path
    manifest_path: Path
    manifest_sha256: str
    previous_generation_preserved: bool


@dataclass(frozen=True)
class ValidatedOptimizationCheckpoint:
    generation: int
    generation_directory: Path
    manifest: Mapping[str, Any]
    actor_states: tuple[tuple[str, Mapping[str, Any]], ...]
    actor_optimizer_states: tuple[tuple[str, Mapping[str, Any]], ...]
    critic_state: Mapping[str, Any]
    critic_optimizer_state: Mapping[str, Any]
    value_normalizer_state: Mapping[str, Any] | None
    progression: OptimizationProgressionState
    semantic_config: Mapping[str, Any]


@dataclass(frozen=True)
class OptimizationCheckpointLoadResult:
    generation: int
    generation_directory: Path
    progression: OptimizationProgressionState
    rollback_performed: bool


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_bytes_fsync(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _torch_save_fsync(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        torch.save(value, stream)
        stream.flush()
        os.fsync(stream.fileno())


def _torch_load_cpu(path: Path) -> Any:
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:  # pragma: no cover - compatibility with older torch only.
        return torch.load(path, map_location="cpu")


def _require_exact_keys(section: str, mapping: Mapping[str, Any], required: set[str]) -> None:
    if not isinstance(mapping, Mapping):
        raise OptimizationCheckpointValidationError(f"{section} must be an object")
    observed = set(mapping)
    if observed != required:
        raise OptimizationCheckpointValidationError(
            f"{section} keys mismatch: missing={sorted(required - observed)} unexpected={sorted(observed - required)}"
        )


def _validate_relative_path(value: str) -> str:
    raw = str(value)
    path = PurePosixPath(raw)
    if not raw or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts) or "\\" in raw:
        raise OptimizationCheckpointValidationError(f"invalid relative artifact path: {value!r}")
    return raw


def _validate_tensor_tree(value: Any, *, path: str, require_nonempty_mapping: bool = False) -> None:
    if isinstance(value, torch.Tensor):
        if not torch.isfinite(value).all().item():
            raise OptimizationCheckpointValidationError(f"{path} contains nonfinite tensor values")
        return
    if isinstance(value, Mapping):
        if require_nonempty_mapping and not value:
            raise OptimizationCheckpointValidationError(f"{path} must be nonempty")
        for key, item in value.items():
            _validate_tensor_tree(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _validate_tensor_tree(item, path=f"{path}[{index}]")
        return
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float) and math.isfinite(value):
        return
    raise OptimizationCheckpointValidationError(f"{path} contains unsupported/nonfinite value {value!r}")


def _cpu_clone_tree(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().clone()
    if isinstance(value, Mapping):
        return type(value)((key, _cpu_clone_tree(item)) for key, item in value.items())
    if isinstance(value, tuple):
        return tuple(_cpu_clone_tree(item) for item in value)
    if isinstance(value, list):
        return [_cpu_clone_tree(item) for item in value]
    return copy.deepcopy(value)


def _validate_module_state(state: Mapping[str, Any], target: torch.nn.Module | None, *, label: str) -> None:
    if not isinstance(state, Mapping) or not state:
        raise OptimizationCheckpointValidationError(f"{label} state must be a nonempty mapping")
    _validate_tensor_tree(state, path=label, require_nonempty_mapping=True)
    if target is None:
        return
    current = target.state_dict()
    if tuple(state.keys()) != tuple(current.keys()):
        raise OptimizationCheckpointValidationError(
            f"{label} parameter keys mismatch: expected={tuple(current.keys())} observed={tuple(state.keys())}"
        )
    for name, value in state.items():
        expected = current[name]
        if not isinstance(value, torch.Tensor):
            raise OptimizationCheckpointValidationError(f"{label}.{name} must be a tensor")
        if tuple(value.shape) != tuple(expected.shape) or value.dtype != expected.dtype:
            raise OptimizationCheckpointValidationError(
                f"{label}.{name} incompatible: expected shape/dtype={tuple(expected.shape)}/{expected.dtype} "
                f"observed={tuple(value.shape)}/{value.dtype}"
            )


def _validate_adam_state(state: Mapping[str, Any], target: torch.optim.Optimizer | None, *, label: str) -> None:
    _require_exact_keys(label, state, {"state", "param_groups"})
    optimizer_state = state["state"]
    groups = state["param_groups"]
    if not isinstance(optimizer_state, Mapping) or not optimizer_state:
        raise OptimizationCheckpointValidationError(f"{label}.state must be populated")
    if not isinstance(groups, list) or not groups:
        raise OptimizationCheckpointValidationError(f"{label}.param_groups must be nonempty")
    _validate_tensor_tree(state, path=label)
    for index, group in enumerate(groups):
        if not isinstance(group, Mapping) or not isinstance(group.get("params"), list) or not group["params"]:
            raise OptimizationCheckpointValidationError(f"{label}.param_groups[{index}] is malformed")
    for parameter_id, entry in optimizer_state.items():
        if not isinstance(entry, Mapping):
            raise OptimizationCheckpointValidationError(f"{label}.state[{parameter_id!r}] must be a mapping")
        required_moments = {"step", "exp_avg", "exp_avg_sq"}
        if not required_moments <= set(entry):
            raise OptimizationCheckpointValidationError(
                f"{label}.state[{parameter_id!r}] missing Adam fields {sorted(required_moments - set(entry))}"
            )
    if target is None:
        return
    if not isinstance(target, torch.optim.Adam):
        raise OptimizationCheckpointValidationError(
            f"{label} target must be torch.optim.Adam, observed={type(target).__name__}"
        )
    if len(groups) != len(target.param_groups):
        raise OptimizationCheckpointValidationError(f"{label} parameter-group count mismatch")
    referenced_parameter_ids: set[Any] = set()
    for index, (saved, current) in enumerate(zip(groups, target.param_groups, strict=True)):
        if len(saved["params"]) != len(current["params"]):
            raise OptimizationCheckpointValidationError(f"{label} parameter count mismatch in group {index}")
        for parameter_id, parameter in zip(saved["params"], current["params"], strict=True):
            referenced_parameter_ids.add(parameter_id)
            entry = optimizer_state.get(parameter_id)
            if entry is None:
                continue
            step = entry["step"]
            if isinstance(step, torch.Tensor) and step.numel() != 1:
                raise OptimizationCheckpointValidationError(
                    f"{label}.state[{parameter_id!r}].step must be scalar"
                )
            moment_names = ["exp_avg", "exp_avg_sq"]
            if saved.get("amsgrad", False):
                moment_names.append("max_exp_avg_sq")
            for moment_name in moment_names:
                moment = entry.get(moment_name)
                if not isinstance(moment, torch.Tensor):
                    raise OptimizationCheckpointValidationError(
                        f"{label}.state[{parameter_id!r}].{moment_name} must be a tensor"
                    )
                if tuple(moment.shape) != tuple(parameter.shape) or moment.dtype != parameter.dtype:
                    raise OptimizationCheckpointValidationError(
                        f"{label}.state[{parameter_id!r}].{moment_name} incompatible with target parameter"
                    )
    unexpected_state_ids = set(optimizer_state) - referenced_parameter_ids
    if unexpected_state_ids:
        raise OptimizationCheckpointValidationError(
            f"{label} has optimizer state for unreferenced parameters: {sorted(unexpected_state_ids, key=str)}"
        )


def _generation_directories(root: Path) -> list[tuple[int, Path]]:
    if not root.exists():
        return []
    output = []
    for child in root.iterdir():
        match = GENERATION_PATTERN.fullmatch(child.name)
        if match and child.is_dir():
            output.append((int(match.group(1)), child))
    return sorted(output)


def _resolve_generation(checkpoint_path: Path) -> Path:
    direct_manifest = checkpoint_path / "checkpoint_manifest.json"
    if direct_manifest.is_file():
        return checkpoint_path
    pointer_path = checkpoint_path / "latest.json"
    if not pointer_path.is_file():
        legacy_weight_files = tuple(checkpoint_path.glob("actor_agent*.pt")) + tuple(checkpoint_path.glob("critic_agent*.pt"))
        if legacy_weight_files:
            raise OptimizationCheckpointValidationError(
                "OPTIMIZER_STATE_REQUIRED_FOR_OPTIMIZATION_CONTINUATION: legacy weights-only checkpoint "
                "is valid only for evaluation/explicit weight loading"
            )
        raise OptimizationCheckpointValidationError("optimization checkpoint latest.json is missing")
    try:
        pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise OptimizationCheckpointValidationError(f"invalid latest.json: {exc}") from exc
    _require_exact_keys("latest pointer", pointer, {"schema", "generation", "generation_directory", "manifest_sha256"})
    if pointer["schema"] != OPTIMIZATION_CHECKPOINT_POINTER_SCHEMA:
        raise OptimizationCheckpointValidationError("unsupported latest pointer schema")
    if not isinstance(pointer["generation"], int) or pointer["generation"] < 0:
        raise OptimizationCheckpointValidationError("latest pointer generation is invalid")
    expected_name = f"generation_{pointer['generation']:08d}"
    if pointer["generation_directory"] != expected_name:
        raise OptimizationCheckpointValidationError("latest pointer generation directory mismatch")
    generation_dir = checkpoint_path / expected_name
    manifest_path = generation_dir / "checkpoint_manifest.json"
    if not manifest_path.is_file() or _sha256_path(manifest_path) != pointer["manifest_sha256"]:
        raise OptimizationCheckpointValidationError("latest pointer manifest digest mismatch")
    return generation_dir


def save_optimization_checkpoint(
    *,
    checkpoint_root: str | os.PathLike[str],
    boundary: OptimizationCheckpointBoundaryState,
    actor_modules: Sequence[tuple[str, torch.nn.Module]],
    actor_optimizers: Sequence[tuple[str, torch.optim.Optimizer]],
    critic_module: torch.nn.Module,
    critic_optimizer: torch.optim.Optimizer,
    value_normalizer: Any | None,
    progression: OptimizationProgressionState,
    semantic_config: Mapping[str, Any],
    failure_injector: Callable[[str], None] | None = None,
) -> OptimizationCheckpointSaveResult:
    """Write and atomically publish one immutable, complete generation."""

    boundary.assert_saveable()
    if not actor_modules or len(actor_modules) != len(actor_optimizers):
        raise OptimizationCheckpointValidationError("actor modules and optimizers must be nonempty and aligned")
    actor_names = tuple(name for name, _ in actor_modules)
    if actor_names != tuple(name for name, _ in actor_optimizers) or len(set(actor_names)) != len(actor_names):
        raise OptimizationCheckpointValidationError("actor identities/order must be unique and aligned")
    for name, optimizer in actor_optimizers:
        if not isinstance(optimizer, torch.optim.Adam):
            raise OptimizationCheckpointValidationError(f"actor {name!r} optimizer must be Adam")
    if not isinstance(critic_optimizer, torch.optim.Adam):
        raise OptimizationCheckpointValidationError("critic optimizer must be Adam")
    semantic_config = json.loads(_canonical_json_bytes(semantic_config))
    progression_mapping = progression.to_mapping()

    root = Path(checkpoint_root)
    root.mkdir(parents=True, exist_ok=True)
    existing = _generation_directories(root)
    generation = 0 if not existing else existing[-1][0] + 1
    final_dir = root / f"generation_{generation:08d}"
    temp_dir = root / f".generation_{generation:08d}.tmp.{uuid.uuid4().hex}"
    pointer_path = root / "latest.json"
    previous_pointer = pointer_path.read_bytes() if pointer_path.is_file() else None
    temp_dir.mkdir(parents=False, exist_ok=False)
    published = False

    def inject(phase: str) -> None:
        if failure_injector is not None:
            failure_injector(phase)

    try:
        artifacts: list[dict[str, Any]] = []
        pointer_temp: Path | None = None

        def add_torch(relative: str, value: Any, component: str, identity: str) -> None:
            path = temp_dir / relative
            _torch_save_fsync(path, _cpu_clone_tree(value))
            artifacts.append({"path": relative, "sha256": _sha256_path(path), "component": component, "identity": identity})

        for index, (name, module) in enumerate(actor_modules):
            add_torch(f"actors/{index:03d}_weights.pt", module.state_dict(), "actor_weights", name)
        for index, (name, optimizer) in enumerate(actor_optimizers):
            add_torch(f"actor_optimizers/{index:03d}_adam.pt", optimizer.state_dict(), "actor_optimizer", name)
        add_torch("critic/weights.pt", critic_module.state_dict(), "critic_weights", "central_critic")
        add_torch("critic/adam.pt", critic_optimizer.state_dict(), "critic_optimizer", "central_critic")
        value_enabled = value_normalizer is not None
        if value_enabled:
            add_torch(
                "value_normalizer/state.pt",
                export_value_normalizer_checkpoint_state(value_normalizer),
                "value_normalizer",
                "project_adapter",
            )
        progression_bytes = _canonical_json_bytes(progression_mapping)
        _write_bytes_fsync(temp_dir / "progression.json", progression_bytes)
        artifacts.append({"path": "progression.json", "sha256": _sha256_bytes(progression_bytes), "component": "progression", "identity": "update_schedule"})
        config_bytes = _canonical_json_bytes(semantic_config)
        _write_bytes_fsync(temp_dir / "semantic_config.json", config_bytes)
        artifacts.append({"path": "semantic_config.json", "sha256": _sha256_bytes(config_bytes), "component": "semantic_config", "identity": "assignment_runtime"})
        inject("after_component_writes")

        manifest = {
            "schema": OPTIMIZATION_CHECKPOINT_SCHEMA,
            "purpose": OPTIMIZATION_CHECKPOINT_PURPOSE,
            "generation": generation,
            "status": "complete",
            "serialization": "state_dict_only",
            "actor_order": list(actor_names),
            "optimizer_algorithm": "torch.optim.Adam",
            "value_normalizer_enabled": value_enabled,
            "state_coverage": {
                "actor_weights": True,
                "actor_optimizers": True,
                "critic_weights": True,
                "critic_optimizer": True,
                "value_normalizer": value_enabled,
                "progression_schedule": True,
                "semantic_reconstruction_config": True,
            },
            "semantic_config_sha256": _sha256_bytes(config_bytes),
            "artifacts": artifacts,
        }
        manifest_bytes = _canonical_json_bytes(manifest)
        manifest_path = temp_dir / "checkpoint_manifest.json"
        _write_bytes_fsync(manifest_path, manifest_bytes)
        inject("after_manifest_write")
        validate_optimization_checkpoint(
            temp_dir,
            expected_semantic_config=semantic_config,
            _allow_staging_directory=True,
        )
        inject("after_readback_validation")
        os.replace(temp_dir, final_dir)
        published = True
        inject("after_generation_publish")
        final_manifest = final_dir / "checkpoint_manifest.json"
        manifest_sha = _sha256_path(final_manifest)
        pointer = {
            "schema": OPTIMIZATION_CHECKPOINT_POINTER_SCHEMA,
            "generation": generation,
            "generation_directory": final_dir.name,
            "manifest_sha256": manifest_sha,
        }
        pointer_temp = root / f".latest.tmp.{uuid.uuid4().hex}"
        _write_bytes_fsync(pointer_temp, _canonical_json_bytes(pointer))
        inject("before_pointer_publish")
        os.replace(pointer_temp, pointer_path)
        return OptimizationCheckpointSaveResult(
            generation=generation,
            generation_directory=final_dir,
            manifest_path=final_manifest,
            manifest_sha256=manifest_sha,
            previous_generation_preserved=all(path.is_dir() for _, path in existing),
        )
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if pointer_temp is not None and pointer_temp.exists():
            pointer_temp.unlink()
        # A generation published before pointer publication is an immutable orphan;
        # the previous authoritative pointer remains byte-for-byte unchanged.
        if previous_pointer is not None and pointer_path.is_file() and pointer_path.read_bytes() != previous_pointer:
            pointer_path.write_bytes(previous_pointer)
        raise


def validate_optimization_checkpoint(
    checkpoint_path: str | os.PathLike[str],
    *,
    expected_semantic_config: Mapping[str, Any] | None = None,
    actor_modules: Sequence[tuple[str, torch.nn.Module]] | None = None,
    actor_optimizers: Sequence[tuple[str, torch.optim.Optimizer]] | None = None,
    critic_module: torch.nn.Module | None = None,
    critic_optimizer: torch.optim.Optimizer | None = None,
    value_normalizer: Any | None = None,
    _allow_staging_directory: bool = False,
) -> ValidatedOptimizationCheckpoint:
    """Fully validate and deserialize a generation without mutating targets."""

    generation_dir = _resolve_generation(Path(checkpoint_path))
    manifest_path = generation_dir / "checkpoint_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise OptimizationCheckpointValidationError(f"invalid checkpoint manifest: {exc}") from exc
    required_manifest = {
        "schema", "purpose", "generation", "status", "serialization", "actor_order",
        "optimizer_algorithm", "value_normalizer_enabled", "state_coverage",
        "semantic_config_sha256", "artifacts",
    }
    _require_exact_keys("checkpoint manifest", manifest, required_manifest)
    if manifest["schema"] != OPTIMIZATION_CHECKPOINT_SCHEMA or manifest["purpose"] != OPTIMIZATION_CHECKPOINT_PURPOSE:
        raise OptimizationCheckpointValidationError("checkpoint schema/purpose is not optimization continuation v1")
    match = GENERATION_PATTERN.fullmatch(generation_dir.name)
    staging_match = re.fullmatch(r"^\.generation_(\d{8})\.tmp\.[0-9a-f]+$", generation_dir.name)
    accepted_match = staging_match if _allow_staging_directory else match
    if accepted_match is None or manifest["generation"] != int(accepted_match.group(1)):
        raise OptimizationCheckpointValidationError("manifest generation does not match directory")
    if manifest["status"] != "complete" or manifest["serialization"] != "state_dict_only":
        raise OptimizationCheckpointValidationError("checkpoint is incomplete or uses forbidden serialization")
    if manifest["optimizer_algorithm"] != "torch.optim.Adam":
        raise OptimizationCheckpointValidationError("unsupported optimizer algorithm")
    coverage_required = {
        "actor_weights", "actor_optimizers", "critic_weights", "critic_optimizer",
        "value_normalizer", "progression_schedule", "semantic_reconstruction_config",
    }
    _require_exact_keys("state coverage", manifest["state_coverage"], coverage_required)
    for field in coverage_required - {"value_normalizer"}:
        if manifest["state_coverage"][field] is not True:
            raise OptimizationCheckpointValidationError(f"required checkpoint state missing: {field}")
    if manifest["state_coverage"]["value_normalizer"] is not manifest["value_normalizer_enabled"]:
        raise OptimizationCheckpointValidationError("ValueNorm coverage/enabled mismatch")
    if not isinstance(manifest["actor_order"], list) or not manifest["actor_order"] or len(set(manifest["actor_order"])) != len(manifest["actor_order"]):
        raise OptimizationCheckpointValidationError("manifest actor_order is invalid")
    if not isinstance(manifest["artifacts"], list) or not manifest["artifacts"]:
        raise OptimizationCheckpointValidationError("manifest artifacts must be nonempty")

    expected_files = {"checkpoint_manifest.json"}
    by_component: dict[str, list[tuple[Mapping[str, Any], Any]]] = {}
    for index, record in enumerate(manifest["artifacts"]):
        _require_exact_keys(f"artifact[{index}]", record, {"path", "sha256", "component", "identity"})
        relative = _validate_relative_path(record["path"])
        if relative in expected_files or not SHA256_PATTERN.fullmatch(str(record["sha256"])):
            raise OptimizationCheckpointValidationError(f"invalid or duplicate artifact record: {relative}")
        expected_files.add(relative)
        path = generation_dir / relative
        if not path.is_file() or _sha256_path(path) != record["sha256"]:
            raise OptimizationCheckpointValidationError(f"artifact missing or digest mismatch: {relative}")
        value = json.loads(path.read_text(encoding="utf-8")) if relative.endswith(".json") else _torch_load_cpu(path)
        by_component.setdefault(record["component"], []).append((record, value))
    observed_files = {
        path.relative_to(generation_dir).as_posix()
        for path in generation_dir.rglob("*")
        if path.is_file()
    }
    if observed_files != expected_files:
        raise OptimizationCheckpointValidationError(
            f"generation file inventory mismatch: missing={sorted(expected_files - observed_files)} "
            f"unexpected={sorted(observed_files - expected_files)}"
        )

    singleton_components = {"critic_weights", "critic_optimizer", "progression", "semantic_config"}
    allowed_components = singleton_components | {"actor_weights", "actor_optimizer", "value_normalizer"}
    unexpected_components = set(by_component) - allowed_components
    if unexpected_components:
        raise OptimizationCheckpointValidationError(
            f"unexpected checkpoint components: {sorted(unexpected_components)}"
        )
    for component in singleton_components:
        if len(by_component.get(component, [])) != 1:
            raise OptimizationCheckpointValidationError(f"component {component!r} must occur exactly once")
    expected_value_count = 1 if manifest["value_normalizer_enabled"] else 0
    if len(by_component.get("value_normalizer", [])) != expected_value_count:
        raise OptimizationCheckpointValidationError("ValueNorm artifact count mismatch")
    actor_count = len(manifest["actor_order"])
    if len(by_component.get("actor_weights", [])) != actor_count or len(by_component.get("actor_optimizer", [])) != actor_count:
        raise OptimizationCheckpointValidationError("actor weight/optimizer artifact count mismatch")

    semantic_config = by_component["semantic_config"][0][1]
    semantic_bytes = _canonical_json_bytes(semantic_config)
    if _sha256_bytes(semantic_bytes) != manifest["semantic_config_sha256"]:
        raise OptimizationCheckpointValidationError("semantic configuration digest mismatch")
    if expected_semantic_config is not None and semantic_bytes != _canonical_json_bytes(expected_semantic_config):
        raise OptimizationCheckpointValidationError("semantic reconstruction configuration mismatch")
    progression = OptimizationProgressionState.from_mapping(by_component["progression"][0][1])

    target_actor_map = None if actor_modules is None else dict(actor_modules)
    target_actor_optimizer_map = None if actor_optimizers is None else dict(actor_optimizers)
    if target_actor_map is not None and tuple(target_actor_map) != tuple(manifest["actor_order"]):
        raise OptimizationCheckpointValidationError("target actor identities/order mismatch")
    if target_actor_optimizer_map is not None and tuple(target_actor_optimizer_map) != tuple(manifest["actor_order"]):
        raise OptimizationCheckpointValidationError("target actor optimizer identities/order mismatch")

    actor_states = []
    for expected_name, (record, state) in zip(manifest["actor_order"], by_component["actor_weights"], strict=True):
        if record["identity"] != expected_name:
            raise OptimizationCheckpointValidationError("actor weight identity/order mismatch")
        _validate_module_state(state, None if target_actor_map is None else target_actor_map[expected_name], label=f"actor[{expected_name}]")
        actor_states.append((expected_name, state))
    actor_optimizer_states = []
    for expected_name, (record, state) in zip(manifest["actor_order"], by_component["actor_optimizer"], strict=True):
        if record["identity"] != expected_name:
            raise OptimizationCheckpointValidationError("actor optimizer identity/order mismatch")
        _validate_adam_state(state, None if target_actor_optimizer_map is None else target_actor_optimizer_map[expected_name], label=f"actor_optimizer[{expected_name}]")
        actor_optimizer_states.append((expected_name, state))

    critic_state = by_component["critic_weights"][0][1]
    critic_optimizer_state = by_component["critic_optimizer"][0][1]
    _validate_module_state(critic_state, critic_module, label="critic")
    _validate_adam_state(critic_optimizer_state, critic_optimizer, label="critic_optimizer")
    value_state = None
    if manifest["value_normalizer_enabled"]:
        value_state = by_component["value_normalizer"][0][1]
        if value_normalizer is None:
            if actor_modules is not None:
                raise OptimizationCheckpointValidationError("checkpoint requires an enabled ValueNorm target")
            validate_value_normalizer_checkpoint_state(value_state)
        else:
            validate_value_normalizer_checkpoint_state(
                value_state,
                target_inventory=inspect_value_normalizer_target(value_normalizer),
            )
    elif value_normalizer is not None:
        raise OptimizationCheckpointValidationError("checkpoint disables ValueNorm but target enables it")

    return ValidatedOptimizationCheckpoint(
        generation=manifest["generation"],
        generation_directory=generation_dir,
        manifest=manifest,
        actor_states=tuple(actor_states),
        actor_optimizer_states=tuple(actor_optimizer_states),
        critic_state=critic_state,
        critic_optimizer_state=critic_optimizer_state,
        value_normalizer_state=value_state,
        progression=progression,
        semantic_config=semantic_config,
    )


def load_optimization_checkpoint(
    checkpoint_path: str | os.PathLike[str],
    *,
    expected_semantic_config: Mapping[str, Any],
    actor_modules: Sequence[tuple[str, torch.nn.Module]],
    actor_optimizers: Sequence[tuple[str, torch.optim.Optimizer]],
    critic_module: torch.nn.Module,
    critic_optimizer: torch.optim.Optimizer,
    value_normalizer: Any | None,
    progression_tracker: OptimizationProgressionTracker,
    runtime_guard: OptimizationCheckpointRuntimeGuard | None = None,
    apply_failure_injector: Callable[[str], None] | None = None,
) -> OptimizationCheckpointLoadResult:
    """Validate before mutation, then apply atomically with full target rollback."""

    guard = runtime_guard or OptimizationCheckpointRuntimeGuard()
    guard.begin_load()
    try:
        validated = validate_optimization_checkpoint(
            checkpoint_path,
            expected_semantic_config=expected_semantic_config,
            actor_modules=actor_modules,
            actor_optimizers=actor_optimizers,
            critic_module=critic_module,
            critic_optimizer=critic_optimizer,
            value_normalizer=value_normalizer,
        )
        actor_map = dict(actor_modules)
        actor_optimizer_map = dict(actor_optimizers)
        actor_backups = {name: _cpu_clone_tree(module.state_dict()) for name, module in actor_modules}
        actor_optimizer_backups = {name: copy.deepcopy(optimizer.state_dict()) for name, optimizer in actor_optimizers}
        critic_backup = _cpu_clone_tree(critic_module.state_dict())
        critic_optimizer_backup = copy.deepcopy(critic_optimizer.state_dict())
        value_backup = None if value_normalizer is None else export_value_normalizer_checkpoint_state(value_normalizer)
        progression_backup = progression_tracker.state
        mutated = False
        try:
            mutated = True
            for name, state in validated.actor_states:
                actor_map[name].load_state_dict(state, strict=True)
            if apply_failure_injector:
                apply_failure_injector("after_actor_weights")
            critic_module.load_state_dict(validated.critic_state, strict=True)
            for name, state in validated.actor_optimizer_states:
                actor_optimizer_map[name].load_state_dict(state)
            if apply_failure_injector:
                apply_failure_injector("after_actor_optimizers")
            critic_optimizer.load_state_dict(validated.critic_optimizer_state)
            if value_normalizer is not None and validated.value_normalizer_state is not None:
                restore_value_normalizer_checkpoint_state(value_normalizer, validated.value_normalizer_state)
            progression_tracker.replace(validated.progression)
            if apply_failure_injector:
                apply_failure_injector("after_all_components")
            guard.mark_update_complete()
            return OptimizationCheckpointLoadResult(
                generation=validated.generation,
                generation_directory=validated.generation_directory,
                progression=validated.progression,
                rollback_performed=False,
            )
        except Exception as exc:
            rollback_errors = []
            if mutated:
                for name, state in actor_backups.items():
                    try:
                        actor_map[name].load_state_dict(state, strict=True)
                    except Exception as rollback_exc:  # pragma: no cover - defensive path.
                        rollback_errors.append(f"actor {name}: {rollback_exc}")
                try:
                    critic_module.load_state_dict(critic_backup, strict=True)
                except Exception as rollback_exc:  # pragma: no cover
                    rollback_errors.append(f"critic: {rollback_exc}")
                for name, state in actor_optimizer_backups.items():
                    try:
                        actor_optimizer_map[name].load_state_dict(state)
                    except Exception as rollback_exc:  # pragma: no cover
                        rollback_errors.append(f"actor optimizer {name}: {rollback_exc}")
                try:
                    critic_optimizer.load_state_dict(critic_optimizer_backup)
                except Exception as rollback_exc:  # pragma: no cover
                    rollback_errors.append(f"critic optimizer: {rollback_exc}")
                if value_normalizer is not None and value_backup is not None:
                    try:
                        restore_value_normalizer_checkpoint_state(value_normalizer, value_backup)
                    except Exception as rollback_exc:  # pragma: no cover
                        rollback_errors.append(f"ValueNorm: {rollback_exc}")
                progression_tracker.replace(progression_backup)
            if rollback_errors:
                guard.mark_update_failed()
                raise OptimizationCheckpointLoadError(
                    "OPTIMIZATION_CHECKPOINT_LOAD_FAILED_AND_ROLLBACK_INCOMPLETE: "
                    f"original_error={exc}; rollback_errors={rollback_errors}"
                ) from exc
            raise OptimizationCheckpointLoadError(
                "OPTIMIZATION_CHECKPOINT_LOAD_FAILED_TARGET_ROLLED_BACK: " + str(exc)
            ) from exc
    finally:
        guard.end_load()


__all__ = [
    "OPTIMIZATION_CHECKPOINT_POINTER_SCHEMA",
    "OPTIMIZATION_CHECKPOINT_PURPOSE",
    "OPTIMIZATION_CHECKPOINT_SCHEMA",
    "OptimizationCheckpointBoundaryError",
    "OptimizationCheckpointBoundaryState",
    "OptimizationCheckpointError",
    "OptimizationCheckpointLoadError",
    "OptimizationCheckpointLoadResult",
    "OptimizationCheckpointRuntimeGuard",
    "OptimizationCheckpointSaveResult",
    "OptimizationCheckpointValidationError",
    "OptimizationProgressionState",
    "OptimizationProgressionTracker",
    "ValidatedOptimizationCheckpoint",
    "load_optimization_checkpoint",
    "linear_lr_for_next_update",
    "save_optimization_checkpoint",
    "validate_optimization_checkpoint",
]
