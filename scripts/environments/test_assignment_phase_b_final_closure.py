"""One A update/save/exit and one fresh B load/update: final Phase-B closure.

The supervisor never constructs a learner. No automatic retry is implemented.
Only this file owns orchestration; historical helpers supply construction utilities,
not a historical training loop, inventory gate, or inherited acceptance predicate.
"""
from __future__ import annotations

import argparse
import ast
import dataclasses
import enum
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator"
OUT = SCAN / "AgentRead/202609/20260924/phase_b_final_closure_artifacts"
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
HELPER = Path(__file__).with_name("test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py")
PASS = "PHASE-B-FINAL-CLOSURE-RUNTIME-QUALIFIED-AWAITING-GPT-REVIEW"
PREFIX = "PHASE-B-FINAL-CLOSURE-STOP-"
VN_FIELDS = ("running_mean", "running_mean_sq", "debiasing_term")
AUDITED = {
    "assignment_optimization_checkpoint.py": "b0fec513bad87af961450345f1ee5849cca04c4da5429a483af5f31f8a6e76b9",
    "assignment_harl_training.py": "31295d60a01d11657b924e6d8332f160b278eeeb236109b59409bfbf55f7e787",
    "assignment_event_training_full_transaction.py": "a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7",
    "assignment_event_training_real_isaac_adapter.py": "57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac",
    "scan_mobile_manipulator_env.py": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}


class ClosureStop(RuntimeError):
    def __init__(self, boundary, detail):
        self.boundary = boundary
        super().__init__(f"{PREFIX}{boundary}: {detail}")


def need(condition, boundary, detail):
    if not condition:
        raise ClosureStop(boundary, detail)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plain(value):
    if dataclasses.is_dataclass(value):
        return {f.name: plain(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise TypeError(f"unsupported evidence type: {type(value)}")


def digest(value):
    return hashlib.sha256(json.dumps(plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(plain(value), stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_authority():
    # Current source only; never enumerate the historical artifact tree.
    files = set(SCAN.glob("assignment_event_*.py"))
    files.update(SCAN / name for name in AUDITED)
    files.update(SCAN / name for name in (
        "assignment_value_normalizer_checkpoint.py", "assignment_harl_wrapper.py",
        "assignment_lifecycle_transition_contract.py", "assignment_lifecycle_transaction_runtime.py",
        "assignment_initial_claim_runtime.py", "assignment_profile_contract.py",
        "assignment_rl_interface.py", "agents/harl_happo_cfg.yaml"))
    files.update((HELPER, ROOT / "source/isaaclab/isaaclab/envs/direct_marl_env.py"))
    external = [HARL / name for name in (
        "algorithms/actors/happo.py", "algorithms/actors/on_policy_base.py",
        "algorithms/actors/haa2c.py", "algorithms/critics/v_critic.py", "common/valuenorm.py",
        "models/policy_models/stochastic_policy.py", "models/value_function_models/v_net.py")]
    return {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "index_sha256": sha(ROOT / ".git/index"),
        "staged_path_count": len(subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).splitlines()),
        "repository_sources": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in sorted(files)},
        "installed_harl_sources": {str(p): sha(p) for p in external},
    }


def check_freeze():
    freeze = read(OUT / "final_closure_harness_freeze.json")
    need(sha(__file__) == freeze["harness_sha256"], "PRE-MUTATION-HARNESS", "harness freeze changed")
    need(source_authority() == read(OUT / "repository_source_authority.json"), "PRE-MUTATION-HARNESS", "source/index authority changed")
    return freeze["harness_sha256"]


def bind_plan(payload, worker):
    # Counts originate ONLY in the immutable plans, not resolved_config or observations.
    actor = tuple(payload["expected_actor_optimizer_step"])
    backward = tuple(payload["expected_actor_backward"])
    need(tuple(i for i, _ in actor) == (0, 1, 2), "PRE-MUTATION-HARNESS", "actor plan identities")
    need(all(type(n) is int and n >= 0 for _, n in actor), "PRE-MUTATION-HARNESS", "actor plan counts")
    need(actor == backward, "PRE-MUTATION-HARNESS", "backward/step plan mismatch")
    need(all(payload[k] == 0 for k in ("actor_optimizer_steps_before_emit", "critic_optimizer_steps_before_emit", "live_valuenorm_updates_before_emit")), "PRE-MUTATION-HARNESS", "mutation preceded observer")
    need(payload["durable_before_first_actor_optimizer_step"], "PRE-MUTATION-HARNESS", "observer ordering")
    need(payload["expected_critic_optimizer_step"] > 0, "PRE-MUTATION-HARNESS", "empty critic plan")
    if worker == "a":
        need(all(n > 0 for _, n in actor), "PRE-MUTATION-HARNESS", "REJECTED_FIXTURE: actor Adam would remain empty; no mutation authorized")
    keys = ("actor_order", "actor_plan_digest", "critic_plan_digest", "expected_actor_backward",
            "expected_actor_optimizer_step", "expected_critic_backward", "expected_critic_optimizer_step",
            "expected_live_valuenorm_update", "actor_optimizer_steps_before_emit", "critic_optimizer_steps_before_emit",
            "live_valuenorm_updates_before_emit", "current_s0_s4_state_history", "current_stage_before_first_actor_mutation",
            "durable_before_first_actor_optimizer_step", "resolved_config", "event_return_compute_count")
    return {k: plain(payload[k]) for k in keys}


def preflight():
    need(Path(sys.executable).resolve() == PYTHON.resolve(), "PRE-MUTATION-HARNESS", "wrong interpreter")
    need(not (OUT / "process_a").exists(), "PRE-MUTATION-HARNESS", "existing attempt: never overwrite/retry")
    for name, expected in AUDITED.items():
        need(sha(SCAN / name) == expected, "PRE-MUTATION-HARNESS", f"readiness source drift: {name}")
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    compile(tree, __file__, "exec")
    need(not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("train", "run") and isinstance(n.func.value, ast.Name) and n.func.value.id == "runner" for n in ast.walk(tree)), "PRE-MUTATION-HARNESS", "generic runner entry")
    adapter = (SCAN / "assignment_event_training_real_isaac_adapter.py").read_text()
    need("R5.execute_full_learner_transaction_v1(" in adapter, "PRE-MUTATION-HARNESS", "event path")
    # One positive DTO-binding check with deliberately nonuniform plan counts.
    fake = {k: 0 for k in ("actor_optimizer_steps_before_emit", "critic_optimizer_steps_before_emit", "live_valuenorm_updates_before_emit")}
    fake.update(expected_actor_optimizer_step=((0, 1), (1, 2), (2, 3)), expected_actor_backward=((0, 1), (1, 2), (2, 3)),
                expected_critic_optimizer_step=10, expected_critic_backward=10, expected_live_valuenorm_update=10,
                actor_order=(2, 0, 1), actor_plan_digest="a" * 64, critic_plan_digest="b" * 64,
                current_s0_s4_state_history=[], current_stage_before_first_actor_mutation="S5_ACTOR_SEQUENCE",
                durable_before_first_actor_optimizer_step=True, resolved_config={"provenance_only": True}, event_return_compute_count=1)
    need(bind_plan(fake, "a")["expected_actor_optimizer_step"] == [[0, 1], [1, 2], [2, 3]], "PRE-MUTATION-HARNESS", "direct binder")
    authority = source_authority()
    write(OUT / "repository_source_authority.json", authority)
    write(OUT / "final_closure_harness_freeze.json", {
        "status": "PREFLIGHT_PASS_FROZEN", "harness_sha256": sha(__file__), "source_authority_digest": digest(authority),
        "checks": ["syntax", "audited_source_identity", "real_event_path", "no_generic_runner", "direct_nonuniform_plan_binding", "explicit_AB_config_LR_progression"],
        "python": sys.executable, "preflight_ns": time.time_ns(), "refreeze_at_plan_required": True,
    })
    print("Final closure minimal preflight PASS", flush=True)


def tensor_record(tensor):
    import torch
    value = tensor.detach().cpu().contiguous()
    need(bool(torch.isfinite(value).all()), "POISONED", "nonfinite learner tensor")
    return {"shape": list(value.shape), "dtype": str(value.dtype), "sha256": hashlib.sha256(value.numpy().tobytes()).hexdigest()}


def state_record(value):
    import torch
    if isinstance(value, torch.Tensor):
        return tensor_record(value)
    if isinstance(value, dict):
        return {str(k): state_record(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [state_record(v) for v in value]
    if isinstance(value, float):
        need(math.isfinite(value), "POISONED", "nonfinite optimizer scalar")
    return plain(value)


def steps(opt):
    return [int(s["step"].item()) if hasattr(s["step"], "item") else int(s["step"]) for s in opt.state.values()]


def vn_state(vn):
    return {name: tensor_record(getattr(vn, name)) for name in VN_FIELDS}


def snapshot(handles, progression, config):
    groups = {"actor_weights": [state_record(m.state_dict()) for _, m in handles["actor_modules"]],
              "actor_adam": [state_record(o.state_dict()) for _, o in handles["actor_optimizers"]],
              "critic_weights": state_record(handles["critic_module"].state_dict()),
              "critic_adam": state_record(handles["critic_optimizer"].state_dict()),
              "valuenorm": vn_state(handles["value_normalizer"]),
              "progression": progression.state.to_mapping(), "semantic_config": config}
    return {"group_digests": {k: digest(v) for k, v in groups.items()},
            "actor_adam_steps": [steps(o) for _, o in handles["actor_optimizers"]],
            "critic_adam_steps": steps(handles["critic_optimizer"]),
            "optimizer_groups": [state_record(o.state_dict()["param_groups"]) for o in [*(o for _, o in handles["actor_optimizers"]), handles["critic_optimizer"]]],
            "valuenorm": groups["valuenorm"], "progression": groups["progression"], "finite": True}


def device_check(handles):
    import torch
    rows = []
    for (name, module), (_, opt) in zip([*handles["actor_modules"], ("critic", handles["critic_module"])], [*handles["actor_optimizers"], ("critic", handles["critic_optimizer"])], strict=True):
        devices = sorted({str(p.device) for p in module.parameters()})
        incompatible = [(field, str(value.device), str(p.device)) for p, state in opt.state.items() for field, value in state.items()
                        if isinstance(value, torch.Tensor) and value.device != p.device and not (field == "step" and value.numel() == 1 and value.device.type == "cpu")]
        need(devices == ["cuda:0"] and not incompatible, "STRICT-LOAD", f"device mismatch {name}")
        rows.append({"name": name, "parameter_devices": devices, "state_devices": sorted({str(v.device) for state in opt.state.values() for v in state.values() if isinstance(v, torch.Tensor)}), "compatible": True})
    need(all(str(getattr(handles["value_normalizer"], f).device) == "cuda:0" for f in VN_FIELDS), "STRICT-LOAD", "ValueNorm device")
    return rows


def construct(resources, helper):
    import gymnasium as gym
    import torch
    import isaaclab_tasks
    from harl.algorithms.actors.happo import HAPPO
    from harl.algorithms.critics.v_critic import VCritic
    from harl.common.valuenorm import ValueNorm
    from harl.utils.envs_tools import set_seed
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_critic_buffer import EventOnPolicyCriticBufferEPV2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_learned_route import _compose_dormant_event_learned_policy_route_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import seal_current_event_policy_decision_bundle_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_evidence import capture_current_event_policy_evidence_snapshot_v2, capture_event_policy_physical_problem_evidence_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import _EventProfileLifecycleDomainSpec, _EventProfileLifecycleRuntimeDomain
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import build_assignment_event_profile_schema_v2_descriptor
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import _compose_event_assignment_harl_wrapper
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import AssignmentProfileName, AssignmentProfileResolutionOrigin, resolve_assignment_profile
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import assignment_to_env_actions
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import ScanMobileManipulatorEnvCfg

    need(Path(isaaclab_tasks.__file__).resolve() == ROOT / "source/isaaclab_tasks/isaaclab_tasks/__init__.py", "PRE-MUTATION-HARNESS", "real task package identity")
    algo = helper.load_production_algo_args()
    algo["train"].update(episode_length=2, n_rollout_threads=2, use_linear_lr_decay=True)
    set_seed(dict(algo["seed"]))
    cfg = ScanMobileManipulatorEnvCfg()
    cfg.scene.num_envs = 2
    profile = resolve_assignment_profile(AssignmentProfileName.EVENT_GATED_LOCAL_MRTA, AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
    cfg.assignment_lifecycle_profile = profile.profile_name.value
    device = torch.device(cfg.sim.device)
    need(str(device) == "cuda:0" and len(cfg.possible_agents) == 3 and len(cfg.viewpoint_poses) == 12, "PRE-MUTATION-HARNESS", "fixed scale/device")
    domain = _EventProfileLifecycleRuntimeDomain(_EventProfileLifecycleDomainSpec(profile, device=device, env_ids=torch.arange(2, dtype=torch.int64, device=device), num_robots=3, num_tasks=12))
    env = gym.make("Isaac-Scan-Mobile-Manipulator-Direct-v0", cfg=cfg, resolved_assignment_profile=profile, event_lifecycle_runtime_domain=domain, event_admission_validation_port=domain.environment_admission_validation_port)
    resources["env"] = env
    raw = env.unwrapped
    wrapper = _compose_event_assignment_harl_wrapper(env=helper.WrapperGuard(env), resolved_assignment_profile=profile, runtime_domain=domain, assignment_profile_entrypoint="PHASE-B-FINAL-CLOSURE")
    scale = raw._event_terminal_critic_scale_contract_v2
    schema = build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale)

    def current_bundle():
        physical = capture_event_policy_physical_problem_evidence_v2(assignment_problem=raw.get_assignment_problem(), episode_progress_steps=raw.episode_length_buf, scale_contract=scale)
        evidence = capture_current_event_policy_evidence_snapshot_v2(current_publication=domain.current_read_port.read_current(), current_open_window_view=domain.interstep_fence_read_port.read(), physical_evidence=physical, scale_contract=scale)
        return seal_current_event_policy_decision_bundle_v2(evidence_snapshot=evidence)

    def validate_current(bundle):
        bundle.evidence_snapshot.validate_current(current_publication=domain.current_read_port.read_current(), current_open_window_view=domain.interstep_fence_read_port.read())

    resources["effective_assignments"] = []

    def action_builder(environment, assignment):
        need(environment is raw, "PRE-MUTATION-HARNESS", "P2 environment identity")
        resources["effective_assignments"].append(assignment.detach().clone())
        return assignment_to_env_actions(environment, assignment)

    def forbidden(*args, **kwargs):
        raise ClosureStop("PRE-MUTATION-HARNESS", "parallel trainer/stock returns forbidden")

    args = {**algo["model"], **algo["algo"]}
    actors = tuple(HAPPO(args, helper.Box((int(schema["actor_schema"]["dimension"]),)), gym.spaces.Discrete(13), device=device) for _ in range(3))
    critic = VCritic(args, helper.Box((int(schema["critic_schema"]["dimension"]),)), device=device)
    vn = ValueNorm(1, device=device)
    buffer = EventOnPolicyCriticBufferEPV2({**algo["train"], **args}, helper.Box((int(schema["critic_schema"]["dimension"]),)), device=device)
    buffer.compute_returns = forbidden
    for actor in actors:
        actor.prep_rollout()
        actor.actor_optimizer.zero_grad(set_to_none=True)
    critic.prep_rollout()
    critic.critic_optimizer.zero_grad(set_to_none=True)
    route = _compose_dormant_event_learned_policy_route_v2(episode_length=2, actors=actors, critic=critic, critic_buffer=buffer, admitted_reset=wrapper.reset, current_decision_supplier=current_bundle, current_decision_validator=validate_current, capture_i42_decision=wrapper._capture_event_proposal_decision, step_i42_proposals=wrapper._step_event_proposals, action_builder=action_builder, actor_trainer=forbidden, critic_trainer=forbidden, value_normalizer=vn, actor_rnn_shape=(1, 256))
    resources.update(route=route, actors=actors, critic=critic, vn=vn, algo=algo)
    handles = {"actor_modules": tuple((f"actor_{i:03d}", a.actor) for i, a in enumerate(actors)), "actor_optimizers": tuple((f"actor_{i:03d}", a.actor_optimizer) for i, a in enumerate(actors)), "critic_module": critic.critic, "critic_optimizer": critic.critic_optimizer, "value_normalizer": vn}
    config = {"environment": "Isaac-Scan-Mobile-Manipulator-Direct-v0", "profile": profile.profile_name.value, "device": str(device), "T": route.episode_length, "E": buffer.n_rollout_threads, "M": len(actors), "N": len(cfg.viewpoint_poses), "actor_epochs": [a.ppo_epoch for a in actors], "actor_minibatches": [a.actor_num_mini_batch for a in actors], "critic_epochs": critic.critic_epoch, "critic_minibatches": critic.critic_num_mini_batch, "valuenorm": vn is not None, "fixed_order": algo["algo"]["fixed_order"], "total_updates": 12, "actor_base_lr": [a.lr for a in actors], "critic_base_lr": critic.critic_lr, "model": algo["model"], "algorithm": algo["algo"], "buffer_train": algo["train"], "seed": algo["seed"], "normalizer": {k: getattr(vn, k) for k in ("input_shape", "norm_axes", "beta", "per_element_update", "epsilon")}, "environment_horizon_seconds": float(cfg.episode_length_s), "environment_horizon_steps": int(raw.max_episode_length), "control_dt": float(raw.step_dt), "actor_architecture": str(actors[0].actor), "critic_architecture": str(critic.critic), "actor_rnn_shape": [1, 256], "lr_save_convention": "save current optimizer LR; apply saved NEXT schedule position after exact B-load equality, before collection", "fresh_environment_rng": "same declared seed; simulator/rollout/RNG restoration not claimed"}
    need(config["actor_epochs"] == [5] * 3 and config["actor_minibatches"] == [2] * 3 and config["critic_epochs"] == 5 and config["critic_minibatches"] == 2 and config["valuenorm"] and not config["fixed_order"], "PRE-MUTATION-HARNESS", "effective learner settings")
    resources["config"] = plain(config)
    return handles


def learner_run(worker, resources):
    import torch
    from isaaclab_tasks.direct.scan_mobile_manipulator import assignment_optimization_checkpoint as ckpt
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_evidence import B2RSourceDigestV1, fingerprint_tensor_v1
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_real_isaac_adapter import execute_real_isaac_single_transaction_v1
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_training_full_transaction import validate_quiescence_claim_v1
    directory = OUT / f"process_{worker}"
    h, config = resources["handles"], resources["config"]
    route, vn = resources["route"], resources["vn"]
    progression = ckpt.OptimizationProgressionTracker(ckpt.OptimizationProgressionState.after_update(0, 12))
    guard = ckpt.OptimizationCheckpointRuntimeGuard()
    resources["guard"] = guard
    initial = snapshot(h, progression, config)
    need(not any(initial["actor_adam_steps"]) and not initial["critic_adam_steps"], "PRE-MUTATION-HARNESS", "not a fresh learner")
    if worker == "a":
        write(OUT / "effective_config.json", config)
    else:
        resources["boundary"] = "STRICT-LOAD"
        need(config == read(OUT / "effective_config.json"), "STRICT-LOAD", "effective config mismatch")
        result = ckpt.load_optimization_checkpoint(OUT / "checkpoint", expected_semantic_config=config, progression_tracker=progression, runtime_guard=guard, **h)
        loaded = snapshot(h, progression, config)
        saved = read(OUT / "process_a/a_save_state.json")["state"]
        equality = {k: loaded["group_digests"][k] == saved["group_digests"][k] for k in saved["group_digests"]}
        equality.update(actor_adam_steps=loaded["actor_adam_steps"] == saved["actor_adam_steps"], critic_adam_steps=loaded["critic_adam_steps"] == saved["critic_adam_steps"], optimizer_groups=loaded["optimizer_groups"] == saved["optimizer_groups"])
        devices = device_check(h)
        write(OUT / "cross_process_state_equality.json", {"pass": all(equality.values()), "exact_checks": equality, "device_restoration": devices, "loaded_state": loaded})
        need(all(equality.values()) and loaded == saved, "STATE-EQUALITY", equality)
        write(directory / "load_result.json", {"pass": True, "result": result, "before_any_collection": True, "collection_steps": 0, "loaded_state": loaded, "fresh_default_valuenorm": initial["valuenorm"]})
    update_position = progression.state.next_update_index
    need(update_position == (1 if worker == "a" else 2), "PROGRESSION-LR-CONTINUITY", "wrong update position")
    lrs = []
    for (_, optimizer), base in zip([*h["actor_optimizers"], ("critic", h["critic_optimizer"])], [*config["actor_base_lr"], config["critic_base_lr"]], strict=True):
        rate = ckpt.linear_lr_for_next_update(base, progression.state)
        need(rate > 0 and rate == base - base * (update_position / 12), "PROGRESSION-LR-CONTINUITY", "LR schedule")
        for group in optimizer.param_groups:
            group["lr"] = rate
        lrs.append({"base": base, "position": update_position, "effective": rate})
    route.reset()
    guard.mark_rollout_or_update_started()
    before = snapshot(h, progression, config)
    resources["before"] = before
    for _ in range(2):
        route.collect_step()
    need(snapshot(h, progression, config) == before, "PROGRESSION-LR-CONTINUITY", "collection mutated learner/LR")
    # This smoke reuses the reviewed normal-horizon fixture, no terminal campaign.
    reasons = route.critic_buffer.termination_reason
    need(not bool(reasons.any()) and not route.collector.consumed_terminal_keys, "PRE-MUTATION-HARNESS", "unexpected terminal in two-step fixture")
    state = {"worker": worker, "pid": os.getpid(), "status": "COLLECTED_BEFORE_MUTATION", "update_position": update_position, "lr": lrs, "collection_steps": 2, "collection_preserved_learner": True, "before": before, "vn_updates": []}
    write(directory / "update_result.json", state)
    shadow = {f: getattr(vn, f).detach().clone() for f in VN_FIELDS}
    plan = {}

    def persist_plan(payload):
        plan.update(bind_plan(payload, worker))
        config_dto = payload["resolved_config"]
        need((config_dto.resolved_T, config_dto.resolved_E, config_dto.resolved_M, config_dto.resolved_N) == (2, 2, 3, 12), "PRE-MUTATION-HARNESS", "resolved DTO scale")
        need(config_dto.actor_epoch_count == 5 and config_dto.actor_minibatch_count == 2 and config_dto.critic_epoch_count == 5 and config_dto.critic_minibatch_count == 2 and config_dto.valuenorm_enabled and not config_dto.fixed_order, "PRE-MUTATION-HARNESS", "resolved DTO provenance")
        plan.update(harness_sha256=check_freeze(), source_authority_digest=digest(read(OUT / "repository_source_authority.json")), all_A_actor_Adam_will_populate=all(n > 0 for _, n in plan["expected_actor_optimizer_step"]), pid=os.getpid(), update_position=update_position)
        write(directory / "pre_mutation_plan.json", plan)
        resources["mutation_authorized"] = True
        state["status"] = "PLAN_FROZEN_BEFORE_FIRST_MUTATION"
        write(directory / "update_result.json", state)

    def observe_critic(payload):
        stage = payload["stage"]
        if stage == "S6_VALUENORM_PRE_UPDATE_BOUND":
            need(all(torch.equal(shadow[f], getattr(vn, f)) for f in VN_FIELDS), "VALUENORM-CONTINUITY", "VN not continued from previous state")
            target = route.critic_buffer.returns[:-1].reshape(4, 1)[torch.tensor(payload["canonical_physical_rows"], device="cuda:0", dtype=torch.long)]
            need(fingerprint_tensor_v1(target).content_digest == payload["raw_target_digest"], "VALUENORM-CONTINUITY", "VN target binding")
            weight = vn.beta ** math.prod(target.shape[:vn.norm_axes]) if vn.per_element_update else vn.beta
            shadow["running_mean"].mul_(weight).add_(target.mean(dim=tuple(range(vn.norm_axes))) * (1.0 - weight))
            shadow["running_mean_sq"].mul_(weight).add_((target ** 2).mean(dim=tuple(range(vn.norm_axes))) * (1.0 - weight))
            shadow["debiasing_term"].mul_(weight).add_(1.0 * (1.0 - weight))
        elif stage == "S6_VALUENORM_POST_UPDATE_OBSERVED":
            resources["mutated"] = True
            need(all(torch.equal(shadow[f], getattr(vn, f)) for f in VN_FIELDS) and payload["canonical_state_finite"], "VALUENORM-CONTINUITY", "VN recurrence mismatch")
            state["vn_updates"].append({"epoch": payload["critic_epoch"], "minibatch": payload["critic_minibatch"], "rows": payload["canonical_physical_rows"], "raw_target_digest": payload["raw_target_digest"], "exact_continuation": True, "state": vn_state(vn)})
            write(directory / "update_result.json", state)

    def failure(payload):
        resources["adapter_failure"] = plain(payload)
        resources["mutated"] = bool(payload["partial_update"])
        state.update(status="ADAPTER_FAILED", failure=plain(payload))
        write(directory / "update_result.json", state)

    authority = read(OUT / "repository_source_authority.json")
    repo = tuple(B2RSourceDigestV1(k, v) for k, v in sorted(authority["repository_sources"].items()))
    external = tuple(B2RSourceDigestV1(k, v) for k, v in sorted(authority["installed_harl_sources"].items()))
    resources["boundary"] = f"{worker.upper()}-LEARNER-SEMANTICS"
    transaction = execute_real_isaac_single_transaction_v1(repository_head=authority["head"], dirty_state_classification="preserved reviewed worktree plus authorized compact final closure", repo_source_hashes=repo, installed_harl_source_hashes=external, route=route, actors=resources["actors"], critic=resources["critic"], live_value_normalizer=vn, algo_args=resources["algo"], environment_identity=config["environment"], profile_name=config["profile"], real_environment_resets=1, real_rollout_steps=2, precedence_resolution_evidence_digest=digest(state_record(reasons)), terminal_correlation_evidence_digest=digest({"actual_terminal_keys": [], "actual_reasons": state_record(reasons)}), timeout_critic_evidence_digest=digest({"timeout_count": 0, "actual_reasons": state_record(reasons)}), effective_assignment_evidence_digest=digest([state_record(v) for v in resources["effective_assignments"]]), proposal_effective_authority_separate=True, update_id=f"phase-b-final-{worker}-{os.getpid()}-update{update_position}", order_seed=int(config["seed"]["seed"]) + update_position - 1, classification=PASS, pre_mutation_observer=persist_plan, critic_progress_observer=observe_critic, post_failure_observer=failure)
    resources.update(mutated=True, transaction_returned=True)
    counts = dict(transaction.exact_execution_counts)
    q = transaction.r5_transaction.quiescence_evidence
    validate_quiescence_claim_v1(q)
    need(transaction.r5_transaction.transaction_success and transaction.next_rollout_ready and not route.poisoned, resources["boundary"], "S10/poison")
    expected_actor = [n for _, n in plan["expected_actor_optimizer_step"]]
    need(list(counts["actor_optimizer_step_by_actor"]) == expected_actor and list(counts["actor_backward_by_actor"]) == [n for _, n in plan["expected_actor_backward"]], resources["boundary"], "actor plan counts")
    need(counts["critic_optimizer_step"] == plan["expected_critic_optimizer_step"] and counts["critic_backward"] == plan["expected_critic_backward"] and counts["live_valuenorm_update"] == plan["expected_live_valuenorm_update"] == len(state["vn_updates"]), resources["boundary"], "critic/VN plan counts")
    need(counts["successful_real_full_learner_transactions"] == counts["s10_entries"] == transaction.real_audit.event_return_compute_count == 1, resources["boundary"], "exact transaction/event-return count")
    need(all(p.grad is None for _, m in [*h["actor_modules"], ("critic", h["critic_module"])] for p in m.parameters()), resources["boundary"], "gradients not clear")
    progression.record_completed_update()
    guard.mark_update_complete()
    after = snapshot(h, progression, config)
    for prior, post, expected in zip([*before["actor_adam_steps"], before["critic_adam_steps"]], [*after["actor_adam_steps"], after["critic_adam_steps"]], [*expected_actor, plan["expected_critic_optimizer_step"]], strict=True):
        need(bool(post) and (not prior or len(prior) == len(post)), "OPTIMIZER-CONTINUITY", "Adam population changed/reset")
        need(all(b - a == expected for a, b in zip(prior or [0] * len(post), post, strict=True)), "OPTIMIZER-CONTINUITY", "Adam deltas")
    for optimizer in [*(o for _, o in h["actor_optimizers"]), h["critic_optimizer"]]:
        need(any(bool((s["exp_avg_sq"] != 0).any()) for s in optimizer.state.values()), "OPTIMIZER-CONTINUITY", "trivial Adam moments")
    need(after["progression"] == ckpt.OptimizationProgressionState.after_update(update_position, 12).to_mapping(), "PROGRESSION-LR-CONTINUITY", "advance exactly once")
    need(after["valuenorm"] != initial["valuenorm"] and all(torch.equal(shadow[f], getattr(vn, f)) for f in VN_FIELDS), "VALUENORM-CONTINUITY", "VN reset/final recurrence")
    state.update(status="PASS", pass_update=True, counts=counts, expected_actor_steps=expected_actor, quiescence=q, ordering=transaction.r5_transaction.ordering_evidence, event_return_compute_count=transaction.real_audit.event_return_compute_count, stock_compute_returns_calls=0, after=after, optimizer_continuity=True, valuenorm_continuity=True, progression_lr_continuity=True, source_freeze_unchanged=check_freeze())
    write(directory / "update_result.json", state)
    if worker == "a":
        resources["boundary"] = "CHECKPOINT-SAVE"
        write(directory / "a_save_state.json", {"state": after, "actual_S10": q, "guard": guard.snapshot(), "lr_convention": config["lr_save_convention"]})
        result = ckpt.save_optimization_checkpoint(checkpoint_root=OUT / "checkpoint", boundary=guard.snapshot(), progression=progression.state, semantic_config=config, **h)
        validated = ckpt.validate_optimization_checkpoint(OUT / "checkpoint", expected_semantic_config=config, **h)
        need(snapshot(h, progression, config) == after, "CHECKPOINT-SAVE", "save mutated learner")
        generations = list((OUT / "checkpoint").glob("generation_*"))
        need(len(generations) == 1 and result.generation == validated.generation, "CHECKPOINT-SAVE", "one complete generation")
        write(directory / "checkpoint_save_result.json", {"pass": True, "result": result, "strict_readback": True, "save_nonmutation": True, "generation_count": 1, "manifest": validated.manifest})
        write(directory / "success_receipt.json", {"pass": True, "pid": os.getpid(), "real_updates": 1, "S10": True, "save_validate": True, "save_nonmutation": True, "checkpoint_generation": result.generation, "manifest_sha256": result.manifest_sha256, "source_freeze": check_freeze()})
    else:
        write(directory / "continuity_result.json", {"pass": True, "loaded_equals_A_saved": True, "before": before, "after": after, "optimizer_deltas_equal_plan": True, "vn_exact_recurrence_updates": len(state["vn_updates"]), "saved_next_position_consumed": update_position, "lr": lrs, "S10": q})
    resources["semantic_success"] = True


def worker_main(worker):
    directory = OUT / f"process_{worker}"
    directory.mkdir(exist_ok=False)
    resources = {"boundary": "PRE-MUTATION-HARNESS", "worker": worker}
    app = None
    identity = {"pid": os.getpid(), "parent_pid": os.getppid(), "python": sys.executable, "worker": worker, "fresh_process": True}
    write(directory / "runtime_identity.json", identity)
    try:
        need(Path(sys.executable).resolve() == PYTHON.resolve(), "PRE-MUTATION-HARNESS", "wrong worker interpreter")
        identity["harness_sha256"] = check_freeze()
        sys.argv = [sys.argv[0]]
        helper = importlib.import_module(HELPER.stem)
        from isaaclab.app import AppLauncher

        class StartupLog:
            def emit(self, stage, status, detail=None):
                print(f"startup {stage}: {status}", flush=True)

        need(str(helper._warm_start_torch_cuda("cuda:0", StartupLog())) == "cuda:0", "PRE-MUTATION-HARNESS", "CUDA warmup")
        launcher = AppLauncher(headless=True, device="cuda:0", enable_cameras=False, livestream=0, xr=False, experience="")
        app = launcher.app
        resources["handles"] = construct(resources, helper)
        identity.update(cuda_ready=True, app_launcher_normal=True, real_environment_constructions=1, fresh_learner_constructions=1, real_task_package=str(sys.modules["isaaclab_tasks"].__file__), effective_config_digest=digest(resources["config"]), source_authority_digest=digest(read(OUT / "repository_source_authority.json")))
        write(directory / "runtime_identity.json", identity)
        learner_run(worker, resources)
    except BaseException as exc:
        failure = {"pass": False, "classification": PREFIX + getattr(exc, "boundary", resources["boundary"]), "error": str(exc), "traceback": traceback.format_exc(), "learner_mutated": resources.get("mutated", False), "mutation_authorized": resources.get("mutation_authorized", False), "transaction_returned": resources.get("transaction_returned", False), "route_poisoned": bool(getattr(resources.get("route"), "poisoned", False)), "guard": resources["guard"].snapshot() if "guard" in resources else None, "adapter_failure": resources.get("adapter_failure")}
        write(directory / "failure.json", failure)
        print(failure["traceback"], flush=True)
    finally:
        shutdown = {"pid": os.getpid(), "semantic_success": resources.get("semantic_success", False), "environment_closed": False, "simulation_app_close_requested": False}
        try:
            if "env" in resources:
                resources["env"].close()
                shutdown["environment_closed"] = True
        except BaseException as exc:
            shutdown["environment_close_error"] = str(exc)
        shutdown["simulation_app_close_requested"] = app is not None
        # app.close() can terminate the interpreter: parent wait/PID absence is final authority.
        write(directory / "shutdown.json", shutdown)
        if app is not None:
            app.close()
    return 0 if resources.get("semantic_success") else 1


def launch(worker):
    with (OUT / f"process_{worker}.log").open("xb") as log:
        child = subprocess.Popen([str(PYTHON), "-u", str(Path(__file__).resolve()), "--worker", worker], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        print(f"Process {worker.upper()} PID {child.pid} launched", flush=True)
        while child.poll() is None:
            try:
                child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                print(f"Process {worker.upper()} PID {child.pid} active", flush=True)
        directory = OUT / f"process_{worker}"
        shutdown = read(directory / "shutdown.json") if (directory / "shutdown.json").exists() else {}
        shutdown.update(parent_wait_returncode=child.returncode, parent_wait_completed=True, pid_inactive=child.poll() is not None, pid=child.pid)
        write(directory / "shutdown.json", shutdown)
        print(f"Process {worker.upper()} exited {child.returncode}", flush=True)
        return shutdown


def supervise():
    gates = {f"G{i}": "NOT_RUN" for i in range(1, 11)}
    try:
        check_freeze()
        need(not (OUT / "process_a").exists() and not (OUT / "process_b").exists(), "PRE-MUTATION-HARNESS", "existing attempt; no automatic retry")
        a_exit = launch("a")
        if (OUT / "process_a/failure.json").exists():
            failure = read(OUT / "process_a/failure.json")
            raise ClosureStop(failure["classification"].removeprefix(PREFIX), failure["error"])
        receipt = read(OUT / "process_a/success_receipt.json")
        a_update = read(OUT / "process_a/update_result.json")
        need(a_exit["parent_wait_returncode"] == 0 and a_exit["pid_inactive"] and a_exit["environment_closed"] and a_exit["simulation_app_close_requested"] and a_exit["semantic_success"] and receipt["pass"] and receipt["pid"] == a_exit["pid"] and receipt["real_updates"] == 1 and receipt["S10"] and a_update["pass_update"], "A-TO-B-GATE", "A semantic/exit gate")
        # Direct CPU-only production import; no task-package placeholders in either worker.
        sys.path.insert(0, str(SCAN))
        ckpt = importlib.import_module("assignment_optimization_checkpoint")
        validated = ckpt.validate_optimization_checkpoint(OUT / "checkpoint", expected_semantic_config=read(OUT / "effective_config.json"))
        need(validated.generation == receipt["checkpoint_generation"] and sha(validated.generation_directory / "checkpoint_manifest.json") == receipt["manifest_sha256"] and len(list((OUT / "checkpoint").glob("generation_*"))) == 1, "A-TO-B-GATE", "checkpoint gate")
        check_freeze()
        write(OUT / "a_to_b_gate.json", {"pass": True, "A_pid": a_exit["pid"], "A_inactive": True, "durable_semantic_receipt": True, "strict_parent_validation": True, "generation": validated.generation, "gate_ns": time.time_ns()})
        gates.update({f"G{i}": "PASS" for i in (2, 3, 4, 5)})
        b_exit = launch("b")
        if (OUT / "process_b/failure.json").exists():
            failure = read(OUT / "process_b/failure.json")
            raise ClosureStop(failure["classification"].removeprefix(PREFIX), failure["error"])
        a_id, b_id = (read(OUT / f"process_{w}/runtime_identity.json") for w in ("a", "b"))
        need(a_id["pid"] != b_id["pid"] and all(a_id[k] == b_id[k] for k in ("harness_sha256", "effective_config_digest", "source_authority_digest")), "STATE-EQUALITY", "A/B source/config/process identity")
        gates["G1"] = "PASS"
        need(read(OUT / "cross_process_state_equality.json")["pass"] and read(OUT / "process_b/load_result.json")["before_any_collection"], "STATE-EQUALITY", "B equality gate")
        gates["G6"] = "PASS"
        b_update = read(OUT / "process_b/update_result.json")
        continuity = read(OUT / "process_b/continuity_result.json")
        need(b_update["pass_update"] and continuity["pass"] and continuity["saved_next_position_consumed"] == 2, "B-LEARNER-SEMANTICS", "B update/continuity")
        gates.update({f"G{i}": "PASS" for i in (7, 8, 9)})
        need(b_exit["parent_wait_returncode"] == 0 and b_exit["pid_inactive"] and b_exit["environment_closed"] and b_exit["simulation_app_close_requested"] and b_exit["semantic_success"], "B-LEARNER-SEMANTICS", "B close")
        check_freeze()
        need(all((OUT / p).is_file() for p in ("process_a/pre_mutation_plan.json", "process_a/a_save_state.json", "process_a/checkpoint_save_result.json", "process_a/success_receipt.json", "process_b/pre_mutation_plan.json", "process_b/load_result.json", "process_b/continuity_result.json")), "A-TO-B-GATE", "missing core evidence")
        gates["G10"] = "PASS"
        final = {"classification": PASS, "gates": gates, "A_pid": a_id["pid"], "B_pid": b_id["pid"], "A_real_updates": 1, "B_real_updates": 1, "generation": validated.generation, "both_workers_inactive": True, "source_index_preserved": True, "phase_B": "ALL IMPLEMENTATION/RUNTIME CLOSURE REQUIREMENTS SATISFIED / AWAITING FINAL GPT REVIEW", "paper_experiments": "NOT STARTED"}
    except BaseException as exc:
        final = {"classification": PREFIX + getattr(exc, "boundary", "A-TO-B-GATE"), "gates": gates, "error": str(exc), "traceback": traceback.format_exc(), "retry": "FORBIDDEN after learner mutation; no automatic retry performed"}
    write(OUT / "final_result.json", final)
    print(json.dumps(final, indent=2), flush=True)
    return 0 if final["classification"] == PASS else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--worker", choices=("a", "b"))
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.worker:
        raise SystemExit(worker_main(args.worker))
    else:
        raise SystemExit(supervise())
