# Copyright (c) 2022-2025, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from itertools import product
from typing import Any

import torch

from .base_solver import BaseAssignmentSolver
from .greedy_solver import GreedyAssignmentSolver
from .nearest_solver import NearestAssignmentSolver


class ConflictAwareAssignmentSolver(BaseAssignmentSolver):
    """Gated baseline variant with a small selected-target conflict-aware top-k search.

    This solver is intentionally a separate method from the existing baselines. It uses the same unary distance cost
    basis as nearest/greedy in this environment, then scores small joint combinations with a selected-target conflict
    penalty. It does not mutate masks, rewards, environment state, or controller behavior.
    """

    def __init__(self, *, method_name: str, base_method: str):
        self.method_name = str(method_name)
        self.base_method = str(base_method)
        if self.base_method == "nearest":
            self._base_solver = NearestAssignmentSolver()
        elif self.base_method == "greedy":
            self._base_solver = GreedyAssignmentSolver()
        else:
            raise ValueError(f"Unsupported conflict-aware base method: {base_method!r}")
        self.latest_diagnostics: dict[str, Any] = {}

    def reset(self):
        self._base_solver.reset()
        self.latest_diagnostics = {}

    def solve(self, problem):
        base_assignment = self._base_solver.solve(problem)
        self.latest_diagnostics = {}

        enabled = bool(problem.get("conflict_aware_baseline_enabled", True))
        allowed_methods = tuple(str(value).strip().lower() for value in problem.get("conflict_aware_baseline_methods", ()))
        if allowed_methods and self.method_name.lower() not in allowed_methods:
            self._set_fallback_diagnostics(
                problem,
                base_assignment,
                enabled=False,
                reason=f"method_not_enabled:{self.method_name}",
            )
            return base_assignment
        if not enabled:
            self._set_fallback_diagnostics(problem, base_assignment, enabled=False, reason="disabled")
            return base_assignment

        tensors, reason = self._required_tensors(problem)
        if tensors is None:
            self._set_fallback_diagnostics(problem, base_assignment, enabled=True, reason=reason)
            return base_assignment

        mode = str(problem.get("conflict_aware_baseline_mode", "gated_solver_variant")).strip().lower()
        if mode != "gated_solver_variant":
            self._set_fallback_diagnostics(problem, base_assignment, enabled=True, reason=f"unsupported_mode:{mode}")
            return base_assignment

        cost_matrix = tensors["cost_matrix"]
        available_mask = tensors["available_mask"].to(dtype=torch.bool)
        viewpoint_pos = tensors["viewpoint_pos"]
        num_envs = int(problem["num_envs"])
        num_agents = int(problem["num_agents"])
        device = available_mask.device

        top_k = max(1, int(problem.get("conflict_aware_top_k", 10)))
        target_radius = float(problem.get("conflict_aware_target_conflict_radius", 0.35))
        target_margin = float(problem.get("conflict_aware_target_conflict_safety_margin", 0.15))
        target_threshold = (2.0 * target_radius) + target_margin
        target_penalty = float(problem.get("conflict_aware_target_conflict_penalty", 100.0))
        duplicate_penalty = float(problem.get("conflict_aware_duplicate_penalty", 1_000_000.0))
        fallback_to_base = bool(problem.get("conflict_aware_fallback_to_base_method", True))
        max_pairs_sample = max(0, int(problem.get("conflict_aware_max_pairs_sample", 20)))

        assignment = torch.full((num_envs, num_agents), -1, dtype=torch.long, device=device)
        combination_count = torch.zeros(num_envs, dtype=torch.long, device=device)
        selected_score = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
        selected_unary_sum = torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device)
        selected_conflict_count = torch.zeros(num_envs, dtype=torch.long, device=device)
        selected_duplicate_count = torch.zeros(num_envs, dtype=torch.long, device=device)
        fallback_used = torch.zeros(num_envs, dtype=torch.bool, device=device)
        fallback_reasons: list[str] = []
        conflict_pairs_sample: list[dict[str, Any]] = []
        duplicate_pairs_sample: list[dict[str, Any]] = []

        viewpoint_ids = [int(value) for value in problem.get("viewpoint_ids", list(range(int(problem["num_viewpoints"]))))]
        agent_names = list(problem.get("agent_names", [f"robot_{idx}" for idx in range(num_agents)]))

        for env_id in range(num_envs):
            candidate_lists = [
                self._top_k_candidates(cost_matrix, available_mask, env_id, agent_id, top_k)
                for agent_id in range(num_agents)
            ]
            combo_total = 1
            for candidates in candidate_lists:
                combo_total *= max(1, len(candidates))
            combination_count[env_id] = int(combo_total)

            best_combo = None
            best_metrics = None
            best_score = float("inf")
            for combo in product(*candidate_lists):
                metrics = self._score_combo(
                    combo,
                    env_id=env_id,
                    viewpoint_pos=viewpoint_pos,
                    target_threshold=target_threshold,
                    target_penalty=target_penalty,
                    duplicate_penalty=duplicate_penalty,
                )
                score = float(metrics["score"])
                if score < best_score:
                    best_score = score
                    best_combo = combo
                    best_metrics = metrics

            if best_combo is None or best_metrics is None:
                if fallback_to_base:
                    assignment[env_id] = base_assignment[env_id]
                    fallback_used[env_id] = True
                    fallback_reasons.append("no_valid_candidate_combination")
                continue

            for agent_id, (viewpoint_index, _) in enumerate(best_combo):
                assignment[env_id, agent_id] = int(viewpoint_index)
            selected_score[env_id] = float(best_metrics["score"])
            selected_unary_sum[env_id] = float(best_metrics["unary_cost_sum"])
            selected_conflict_count[env_id] = int(best_metrics["target_conflict_pair_count"])
            selected_duplicate_count[env_id] = int(best_metrics["duplicate_pair_count"])
            self._extend_pair_samples(
                conflict_pairs_sample,
                duplicate_pairs_sample,
                best_metrics,
                env_id=env_id,
                agent_names=agent_names,
                viewpoint_ids=viewpoint_ids,
                max_pairs_sample=max_pairs_sample,
            )

        changed = (assignment != base_assignment) & ~((assignment < 0) & (base_assignment < 0))
        changed_count = changed.sum(dim=1).to(dtype=torch.long)
        changed_rate = changed_count.to(dtype=torch.float32) / float(max(1, num_agents))
        changed_pairs_sample = self._changed_pairs_sample(
            assignment,
            base_assignment,
            agent_names=agent_names,
            viewpoint_ids=viewpoint_ids,
            max_pairs_sample=max_pairs_sample,
        )

        self.latest_diagnostics = {
            "conflict_aware_solver_enabled": True,
            "conflict_aware_solver_method": self.method_name,
            "conflict_aware_solver_base_method": self.base_method,
            "conflict_aware_top_k": top_k,
            "conflict_aware_target_conflict_threshold": target_threshold,
            "conflict_aware_target_conflict_penalty": target_penalty,
            "conflict_aware_duplicate_penalty": duplicate_penalty,
            "conflict_aware_candidate_combination_count": combination_count,
            "conflict_aware_selected_score": selected_score,
            "conflict_aware_selected_unary_cost_sum": selected_unary_sum,
            "conflict_aware_selected_target_conflict_pair_count": selected_conflict_count,
            "conflict_aware_selected_target_conflict_penalty_sum": selected_conflict_count.to(dtype=torch.float32)
            * target_penalty,
            "conflict_aware_selected_duplicate_pair_count": selected_duplicate_count,
            "conflict_aware_fallback_used": fallback_used,
            "conflict_aware_fallback_reasons": sorted(set(fallback_reasons)),
            "conflict_aware_changed_vs_base_count": changed_count,
            "conflict_aware_changed_vs_base_rate": changed_rate,
            "conflict_aware_changed_pairs_sample": changed_pairs_sample,
            "conflict_aware_target_conflict_pairs_sample": conflict_pairs_sample,
            "conflict_aware_duplicate_pairs_sample": duplicate_pairs_sample,
        }
        return assignment

    @staticmethod
    def _required_tensors(problem: dict) -> tuple[dict[str, torch.Tensor] | None, str | None]:
        required = {
            "cost_matrix": problem.get("cost_matrix"),
            "available_mask": problem.get("available_mask"),
            "viewpoint_pos": problem.get("viewpoint_pos"),
        }
        missing = [name for name, value in required.items() if not isinstance(value, torch.Tensor)]
        if missing:
            return None, f"missing_required_tensors:{','.join(missing)}"
        cost_shape = tuple(required["cost_matrix"].shape)
        if tuple(required["available_mask"].shape) != cost_shape:
            return None, f"available_mask_shape_mismatch expected={cost_shape} got={tuple(required['available_mask'].shape)}"
        expected_viewpoint_shape = (cost_shape[0], cost_shape[2])
        if tuple(required["viewpoint_pos"].shape[:2]) != expected_viewpoint_shape:
            return None, (
                "viewpoint_pos_shape_mismatch "
                f"expected_prefix={expected_viewpoint_shape} got={tuple(required['viewpoint_pos'].shape)}"
            )
        return required, None

    @staticmethod
    def _top_k_candidates(
        cost_matrix: torch.Tensor,
        available_mask: torch.Tensor,
        env_id: int,
        agent_id: int,
        top_k: int,
    ) -> list[tuple[int, float]]:
        candidates = torch.nonzero(available_mask[env_id, agent_id], as_tuple=False).flatten()
        if candidates.numel() == 0:
            return [(-1, 0.0)]

        costs = cost_matrix[env_id, agent_id, candidates]
        k = min(int(top_k), int(candidates.numel()))
        top_values, top_indices = torch.topk(costs, k=k, largest=False)
        result: list[tuple[int, float]] = []
        for local_rank in range(k):
            cost = top_values[local_rank]
            if not torch.isfinite(cost):
                continue
            viewpoint_index = int(candidates[top_indices[local_rank]].item())
            result.append((viewpoint_index, float(cost.item())))
        return result if result else [(-1, 0.0)]

    @staticmethod
    def _score_combo(
        combo: tuple[tuple[int, float], ...],
        *,
        env_id: int,
        viewpoint_pos: torch.Tensor,
        target_threshold: float,
        target_penalty: float,
        duplicate_penalty: float,
    ) -> dict[str, Any]:
        unary_cost_sum = sum(float(cost) for viewpoint_index, cost in combo if int(viewpoint_index) >= 0)
        target_conflict_pair_count = 0
        duplicate_pair_count = 0
        target_conflict_pairs: list[dict[str, Any]] = []
        duplicate_pairs: list[dict[str, Any]] = []
        for robot_i in range(len(combo)):
            viewpoint_i = int(combo[robot_i][0])
            if viewpoint_i < 0:
                continue
            for robot_j in range(robot_i + 1, len(combo)):
                viewpoint_j = int(combo[robot_j][0])
                if viewpoint_j < 0:
                    continue
                if viewpoint_i == viewpoint_j:
                    duplicate_pair_count += 1
                    duplicate_pairs.append(
                        {
                            "robot_i": int(robot_i),
                            "robot_j": int(robot_j),
                            "viewpoint_i": viewpoint_i,
                            "viewpoint_j": viewpoint_j,
                        }
                    )
                    continue
                delta = viewpoint_pos[env_id, viewpoint_i, :2] - viewpoint_pos[env_id, viewpoint_j, :2]
                distance = float(torch.linalg.norm(delta).item())
                clearance = distance - float(target_threshold)
                if clearance < 0.0:
                    target_conflict_pair_count += 1
                    target_conflict_pairs.append(
                        {
                            "robot_i": int(robot_i),
                            "robot_j": int(robot_j),
                            "viewpoint_i": viewpoint_i,
                            "viewpoint_j": viewpoint_j,
                            "distance": distance,
                            "clearance": clearance,
                            "threshold": float(target_threshold),
                        }
                    )
        score = (
            unary_cost_sum
            + (float(target_conflict_pair_count) * float(target_penalty))
            + (float(duplicate_pair_count) * float(duplicate_penalty))
        )
        return {
            "score": score,
            "unary_cost_sum": unary_cost_sum,
            "target_conflict_pair_count": target_conflict_pair_count,
            "duplicate_pair_count": duplicate_pair_count,
            "target_conflict_pairs": target_conflict_pairs,
            "duplicate_pairs": duplicate_pairs,
        }

    @staticmethod
    def _viewpoint_id(viewpoint_ids: list[int], viewpoint_index: int) -> int:
        if viewpoint_index < 0:
            return -1
        if viewpoint_index < len(viewpoint_ids):
            return int(viewpoint_ids[viewpoint_index])
        return int(viewpoint_index)

    @staticmethod
    def _extend_pair_samples(
        conflict_pairs_sample: list[dict[str, Any]],
        duplicate_pairs_sample: list[dict[str, Any]],
        metrics: dict[str, Any],
        *,
        env_id: int,
        agent_names: list[str],
        viewpoint_ids: list[int],
        max_pairs_sample: int,
    ) -> None:
        for source, target in (
            (metrics.get("target_conflict_pairs", []), conflict_pairs_sample),
            (metrics.get("duplicate_pairs", []), duplicate_pairs_sample),
        ):
            for pair in source:
                if len(target) >= max_pairs_sample:
                    break
                robot_i = int(pair["robot_i"])
                robot_j = int(pair["robot_j"])
                enriched = {
                    "env_id": int(env_id),
                    "robot_i": robot_i,
                    "robot_j": robot_j,
                    "robot_i_name": agent_names[robot_i] if robot_i < len(agent_names) else f"robot_{robot_i}",
                    "robot_j_name": agent_names[robot_j] if robot_j < len(agent_names) else f"robot_{robot_j}",
                    "viewpoint_i": ConflictAwareAssignmentSolver._viewpoint_id(
                        viewpoint_ids, int(pair["viewpoint_i"])
                    ),
                    "viewpoint_j": ConflictAwareAssignmentSolver._viewpoint_id(
                        viewpoint_ids, int(pair["viewpoint_j"])
                    ),
                }
                for key in ("distance", "clearance", "threshold"):
                    if key in pair:
                        enriched[key] = float(pair[key])
                target.append(enriched)

    def _changed_pairs_sample(
        self,
        assignment: torch.Tensor,
        base_assignment: torch.Tensor,
        *,
        agent_names: list[str],
        viewpoint_ids: list[int],
        max_pairs_sample: int,
    ) -> list[dict[str, Any]]:
        sample: list[dict[str, Any]] = []
        changed = (assignment != base_assignment) & ~((assignment < 0) & (base_assignment < 0))
        for env_id, agent_id in torch.nonzero(changed, as_tuple=False).detach().cpu().tolist():
            if len(sample) >= max_pairs_sample:
                break
            base_index = int(base_assignment[env_id, agent_id].item())
            selected_index = int(assignment[env_id, agent_id].item())
            sample.append(
                {
                    "env_id": int(env_id),
                    "robot_id": int(agent_id),
                    "robot_name": agent_names[agent_id] if agent_id < len(agent_names) else f"robot_{agent_id}",
                    "base_viewpoint": self._viewpoint_id(viewpoint_ids, base_index),
                    "conflict_aware_viewpoint": self._viewpoint_id(viewpoint_ids, selected_index),
                }
            )
        return sample

    def _set_fallback_diagnostics(
        self,
        problem: dict,
        base_assignment: torch.Tensor,
        *,
        enabled: bool,
        reason: str | None,
    ) -> None:
        num_envs = int(problem.get("num_envs", base_assignment.shape[0]))
        num_agents = int(problem.get("num_agents", base_assignment.shape[1]))
        device = base_assignment.device
        self.latest_diagnostics = {
            "conflict_aware_solver_enabled": bool(enabled),
            "conflict_aware_solver_method": self.method_name,
            "conflict_aware_solver_base_method": self.base_method,
            "conflict_aware_top_k": int(problem.get("conflict_aware_top_k", 10)),
            "conflict_aware_target_conflict_threshold": (
                2.0 * float(problem.get("conflict_aware_target_conflict_radius", 0.35))
                + float(problem.get("conflict_aware_target_conflict_safety_margin", 0.15))
            ),
            "conflict_aware_target_conflict_penalty": float(
                problem.get("conflict_aware_target_conflict_penalty", 100.0)
            ),
            "conflict_aware_duplicate_penalty": float(problem.get("conflict_aware_duplicate_penalty", 1_000_000.0)),
            "conflict_aware_candidate_combination_count": torch.zeros(num_envs, dtype=torch.long, device=device),
            "conflict_aware_selected_score": torch.full((num_envs,), float("nan"), dtype=torch.float32, device=device),
            "conflict_aware_selected_unary_cost_sum": torch.full(
                (num_envs,), float("nan"), dtype=torch.float32, device=device
            ),
            "conflict_aware_selected_target_conflict_pair_count": torch.zeros(
                num_envs, dtype=torch.long, device=device
            ),
            "conflict_aware_selected_target_conflict_penalty_sum": torch.zeros(
                num_envs, dtype=torch.float32, device=device
            ),
            "conflict_aware_selected_duplicate_pair_count": torch.zeros(num_envs, dtype=torch.long, device=device),
            "conflict_aware_fallback_used": torch.full((num_envs,), True, dtype=torch.bool, device=device),
            "conflict_aware_fallback_reasons": [] if reason is None else [str(reason)],
            "conflict_aware_changed_vs_base_count": torch.zeros(num_envs, dtype=torch.long, device=device),
            "conflict_aware_changed_vs_base_rate": torch.zeros(num_envs, dtype=torch.float32, device=device),
            "conflict_aware_changed_pairs_sample": [],
            "conflict_aware_target_conflict_pairs_sample": [],
            "conflict_aware_duplicate_pairs_sample": [],
        }
