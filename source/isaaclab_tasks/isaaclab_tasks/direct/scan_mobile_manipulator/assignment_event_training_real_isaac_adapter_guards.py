"""Static/private dependency guards for the B2-R5I adapter."""

from __future__ import annotations


CANONICAL_ASSIGNMENT_EVENT_TRAINING_REAL_ISAAC_ADAPTER_GUARDS_MODULE = (
    "isaaclab_tasks.direct.scan_mobile_manipulator."
    "assignment_event_training_real_isaac_adapter_guards"
)
if __name__ != CANONICAL_ASSIGNMENT_EVENT_TRAINING_REAL_ISAAC_ADAPTER_GUARDS_MODULE:
    raise ImportError("CanonicalModuleIdentityError: B2-R5I guards require canonical import")


import ast
from pathlib import Path


class _CallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.r5_calls = 0
        self.event_return_calls = 0
        self.backward_calls = 0
        self.optimizer_step_calls = 0
        self.valuenorm_update_calls = 0
        self.environment_calls = 0

    def visit_Call(self, node: ast.Call) -> None:
        name = ""
        if isinstance(node.func, ast.Attribute):
            name = node.func.attr
            owner = node.func.value
            if name == "execute_full_learner_transaction_v1":
                self.r5_calls += 1
            elif name == "compute_event_returns":
                self.event_return_calls += 1
            elif name == "backward":
                self.backward_calls += 1
            elif name == "step":
                self.optimizer_step_calls += 1
            elif name == "update":
                self.valuenorm_update_calls += 1
            elif name in ("make", "collect_step", "reset"):
                if isinstance(owner, ast.Name) and owner.id in ("gym", "env", "route"):
                    self.environment_calls += 1
        self.generic_visit(node)


def validate_r5i_static_guards_v1(repo_root: Path) -> dict[str, object]:
    scan = (
        repo_root
        / "source"
        / "isaaclab_tasks"
        / "isaaclab_tasks"
        / "direct"
        / "scan_mobile_manipulator"
    )
    adapter = scan / "assignment_event_training_real_isaac_adapter.py"
    tree = ast.parse(adapter.read_text(encoding="utf-8"), filename=str(adapter))
    visitor = _CallVisitor()
    visitor.visit(tree)
    public_files = tuple(
        sorted(
            path
            for path in scan.glob("*.py")
            if not path.name.startswith("assignment_event_training_")
        )
    )
    token = "assignment_event_training_real_isaac_adapter"
    public_references = tuple(
        path.relative_to(repo_root).as_posix()
        for path in public_files
        if token in path.read_text(encoding="utf-8")
    )
    all_empty = any(
        isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "__all__"
        for node in tree.body
    )
    result = {
        "r5_coordinator_calls": visitor.r5_calls,
        "event_return_compute_calls": visitor.event_return_calls,
        "new_backward_calls": visitor.backward_calls,
        "new_optimizer_step_calls": visitor.optimizer_step_calls,
        "new_live_valuenorm_update_calls": visitor.valuenorm_update_calls,
        "environment_reset_step_make_calls_in_adapter": visitor.environment_calls,
        "public_files_scanned": len(public_files),
        "public_references": public_references,
        "private_exports_empty": all_empty,
    }
    result["pass"] = (
        visitor.r5_calls == 1
        and visitor.event_return_calls == 1
        and visitor.backward_calls == 0
        and visitor.optimizer_step_calls == 0
        and visitor.valuenorm_update_calls == 0
        and visitor.environment_calls == 0
        and not public_references
        and all_empty
    )
    if not result["pass"]:
        raise RuntimeError(f"STOP — B2-R5I STATIC_PRIVATE_GUARD: {result}")
    return result


__all__: tuple[str, ...] = ()
