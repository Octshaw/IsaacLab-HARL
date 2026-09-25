# Phase A — Pure Interface / Identity / Diagnostics Implementation Plan

```text
classification:
  PHASE-A-PLAN-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

targeted findings:
  PR-01–PR-07 RESOLVED

overall architecture:
  accepted

architectural blocker:
  none

broad redesign:
  not required

authoritative design:
  AUTHORITATIVE-DESIGN-APPROVED

authorized documentation scope:
  Phase A plan targeted revision only

current activity:
  PHASE-A-IMPLEMENTATION-PLAN-TARGETED-REVISION-COMPLETE

A1a implementation authorization:
  none -- wait for GPT/user approval

runtime behavior changed by this document:
  no
```

本文是实施方案，不是实施记录。A1～A6 是后续获得单独批准后使用的 commit-style
审核边界；它们不授权本轮修改 Python、YAML、测试、checkpoint 或 installed HARL，也不
授权 commit。

---

## 1. Classification and authorization

权威目标为
[Authoritative V2.1](Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md)。
用户已将其状态批准为：

```text
AUTHORITATIVE-DESIGN-APPROVED
```

Phase 10A 的接口兼容性分类保持：

```text
RUNNER-CHANGES-REQUIRED
```

本方案的结论是：Phase A 可以通过 repo-local、pure/static、default-off 的小型切片实施；
未发现 architectural blocker。Phase A 结束也只能证明 pure/static/manifest identity，
不能宣称 Isaac runtime、训练或 playback 行为已完成验证。

### 1.1 Targeted revision closure

| Finding | Resolution in this plan | Status |
|---|---|---|
| PR-01 | facts producer 与 lifecycle authority 使用独立 ID/stamp；B0 决定 placement | RESOLVED |
| PR-02 | lifecycle event、retry opportunity、resolver diagnostic 三套独立类型/容器 | RESOLVED |
| PR-03 | storage/policy/forced/DVM four-mask truth table；resolver 只读 policy rows | RESOLVED |
| PR-04 | package-qualified canonical module key；prelaunch primitive-only；identity regressions | RESOLVED |
| PR-05 | existing/event discriminated resolved-profile family；event 无 old runtime bool/mapping | RESOLVED |
| PR-06 | pair cardinality、mutual exclusion、owner attribution 和 result assertions | RESOLVED |
| PR-07 | detector mechanism 降为 private implementation detail，不进入 v3 compatibility | RESOLVED |

这些修订不授权 A1a，也不改变 Authoritative V2.1 的 nominal cost、local set、Top-K、
resolver objective、reward 或 HAPPO 方法语义。

---

## 2. Repository and environment baseline

### 2.1 Git baseline

```text
V2.1 verified baseline:
  e3febe417c5323e28ceb9e256ba71dcd44f3c457

current HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

current HEAD subject:
  docs(assignment): approve event-gated local MRTA design for Phase A
```

原始 plan-design pass 开始时 worktree/index 为空。targeted-revision pass 开始时 index
为空，worktree 只含上一文档 pass 已知且获准的 `TASK_PROGRESS.md` 修改、该 plan 和
pre-plan-design archive；没有 Python/YAML/JSON/runtime delta。targeted revision 不把这些
已知文档当作未知修改，也不覆盖其方法内容。

### 2.2 `[CURRENT-CODE-DELTA-SINCE-V2.1]`

`e3febe417c5323e28ceb9e256ba71dcd44f3c457..dca976001d8c53a9cfb424b468fa58d9fca367f6`
只增加或更新 `AgentRead` Markdown 文档，包括 V2/V2.1、审计、归档和批准状态。

```text
Python delta:
  none

YAML/JSON delta:
  none

runtime/checkpoint delta:
  none
```

因此没有发现与 V2.1 冻结目标冲突的当前代码变化。V2.1 的 metadata/approval 状态已过时，
但其 `[CURRENT-CODE]` 技术描述在当前 HEAD 复核后仍成立。本文使用当前代码位置，不把旧
报告行号当作唯一证据。

### 2.3 Python and HARL

```text
Python:
  C:\isaacenvs\isaac45_harl\python.exe

HARL import:
  C:\isaacenvs\isaac45_harl\lib\site-packages\harl\__init__.py

installed HARL policy:
  read-only
```

Phase A 后续实施仍必须使用 repo-local adapter/subclass/shim，不修改
`C:\isaacenvs\isaac45_harl\Lib\site-packages\harl`。

---

## 3. Current-code audit findings

### 3.1 Scenario and profile identity

当前 profile 链为：

```text
scenario YAML/JSON
→ smoke_defaults_from_config()
→ argparse Namespace
→ validate_smoke_args()
→ apply_scenario_config_to_env_cfg()
→ env_cfg
→ wrapper/training/checkpoint/playback 各自按字符串分派
```

实际代码：

- `scenario_config.py:42-47` 定义四个 profile：
  `legacy`、`lifecycle_ablation`、`lifecycle_contract_c`、
  `diagnostics_hidden_state`；
- `scenario_config.py:249-255` 读取顶层和 nested
  `assignment_lifecycle.profile`；
- `scenario_config.py:1146-1173` normalize 后只做验证，不保存 canonical identity；
- `scenario_config.py:99-166` 的 `ENV_CFG_SCENARIO_ATTRS` 没有 lifecycle profile；
- 所以 `apply_scenario_config_to_env_cfg()` 在 `scenario_config.py:479-495`
  不传播该值；
- env 最终保留 `scan_mobile_manipulator_env.py:307-308` 的 `legacy` 默认值；
- 当前 tracked YAML/JSON 没有 lifecycle profile 声明。

这是 Phase A A1 必须修复的显式 config propagation gap。修复必须只在 profile 被显式声明
时写入 canonical raw value；不得给未声明的旧 config 注入新 default 字段。

### 3.2 Wrapper, environment and resolver

- `AssignmentHarlWrapper._build_assignment_lifecycle_profile_config()` 位于
  `assignment_harl_wrapper.py:690-778`，再次 normalize、validate 并生成可变 dict；
- wrapper 在 `assignment_harl_wrapper.py:76-81` 重复维护 profile vocabulary；
- `legacy` 保持 resolver off；`lifecycle_contract_c` 保持 Contract C resolver on；
  ablation/diagnostics 保持 normal training blocked；
- `assignment_harl_wrapper.py:761-778` 是“剩余 supported profile”尾分支。若只把
  `event_gated_local_mrta` 加入集合，它会错误落入 `diagnostics_hidden_state` 路线；
- `assignment_harl_wrapper.py:396-495` 当前链路为 proposal → resolver → effective →
  controller，并在 `440-442` 分开保存 proposal/effective；
- current disabled resolver 在
  `assignment_lifecycle_resolver.py:213-224,417-440,1027-1028`
  返回 proposal clone、不写状态、不发 event；
- Contract C 在 `assignment_lifecycle_resolver.py:676-802` 将 current/noop 视为
  continue，拒绝 executing switch；claim 在 `_start_claim():767-788` 立即 mutation，
  不存在 staged transfer component；
- `get_assignment_problem()` 在
  `scan_mobile_manipulator_env.py:1686-1758` 只提供 Euclidean prototype cost、
  unassigned/completed proxy task state 和全 IDLE robot state；
- `assignment_state.py:10-42` 没有目标
  `NEEDS_ASSIGNMENT`、`WAITING_FOR_TASK`、`TEAM_INFEASIBLE` state。

现有 Phase 9G lifecycle DTO/event 是 prototype/adaptation evidence，不能重命名为新的唯一
lifecycle authority。

### 3.3 Auto-reset boundary

`DirectMARLEnv.step()` 在
`source/isaaclab/isaaclab/envs/direct_marl_env.py:384-415`：

```text
done/reward
→ _reset_idx(done envs)
→ next observation
→ return
```

wrapper 在 `_env.step()` 返回后才读取
`post_step_problem`（`assignment_harl_wrapper.py:417-420`）。因此真实 pre-reset capture
只能由 Phase B0 环境 hook 完成；Phase A 不得接该 hook，也不得把 reset 后 state 当成上一
transition facts。

### 3.4 Training and installed HARL

- repo-local `AssignmentIsaacLabEnv`：
  `assignment_harl_training.py:251-365`；
- repo-local `AssignmentOnPolicyHARunner`：
  `assignment_harl_training.py:383-740`；
- current `collect()` 在 `598-605` 只调用 installed `super().collect()`；
- installed `on_policy_base_runner.py:334-370` 每物理 step 调用所有 actor；
- installed actor buffer 没有 DVM：
  `on_policy_actor_buffer.py:13-119,121-186`；
- EP critic insert 使用 `rewards[:,0]`：
  `on_policy_base_runner.py:493-514`；
- sequential factor `[T,E,1]` 无条件乘 raw ratio：
  `on_policy_ha_runner.py:12-127`；
- HAPPO loss/entropy、active-mask reduction、advantage normalization 和 optimizer step：
  `happo.py:51-155`；
- critic GAE/return：
  `on_policy_critic_buffer_ep.py:99-202`；
- ValueNorm 更新的是 critic minibatch return：
  `harl/algorithms/critics/v_critic.py:91-95`。

这些路径在 Phase A 只作为 identity/manifest contract 被描述。runner、buffer、HAPPO、
factor、GAE、ValueNorm 的新行为全部属于 Phase C/D。

### 3.5 Reward

当前 env reward 在 `scan_mobile_manipulator_env.py:2985-3010` 是：

```text
shared global coverage/time terms
+
per-agent own coverage/duplicate/reach/action-rate terms
```

wrapper 在 `assignment_harl_wrapper.py:2199-2258` 加 per-agent assignment shaping，
`_stack_rewards()` 输出 `[E,M,1]`。当前 EP critic 只插入 robot 0 reward，不是已实现的
显式 team reducer。Phase A 只能定义 mean → component penalty → broadcast contract；
runtime reward 改造属于 D。

### 3.6 Checkpoint and playback

- current strict version：
  `assignment_checkpoint_contract.py:39` =
  `assignment_checkpoint_contract_v2`；
- strict v2 keys/parser：
  `assignment_checkpoint_contract.py:81-168,516-677`；
- canonical bytes/fingerprint：
  `assignment_checkpoint_contract.py:680-705`；
- v2 builder：
  `assignment_checkpoint_save.py:191-485`；
- shared loader：
  `assignment_checkpoint_load.py:826-884`；
- evaluation manifest builder：
  `assignment_checkpoint_load.py:887-1028`；
- training save/restore：
  `assignment_harl_training.py:607-711`；
- playback actor/manifest/load：
  `play_assignment.py:358-410`；
- playback 每步仍逐 actor inference；没有 DVM subset path。

现有 v2 parser 是 exact contract。不能原地扩宽 v2 required keys 或将其改成 polymorphic
v2/v3 class。

### 3.7 Logger, diagnostics and test entrypoints

- repo-local `AssignmentIsaacLabLogger` 在
  `assignment_harl_training.py:147-248` 只用 exact-key whitelist 控制
  `Total_Reward` 累加；其他 numeric diagnostics 仍可单独写入；
- `AssignmentIsaacLabEnv.step()` 在
  `assignment_harl_training.py:315-365` 先把 wrapper `info` flatten 到
  `log_info`，再向 HARL 返回 per-env/per-agent empty infos。因此当前 proper-time-limit
  `bad_masks` 路径看不到 wrapper facts；
- `AssignmentLifecycleDiagnosticsAdapter` 在
  `assignment_lifecycle_diagnostics.py:236-389` 是 default-off、playback-oriented
  JSONL/summary adapter；disabled 时不构造 logger 或文件，enabled 时使用 prototype
  pre/post problem rows，不是 pre-reset lifecycle authority；
- `assignment_playback_attribution_diagnostics.py` 是 pure playback-only
  proposal/effective join 与归因模块，不改变 effective assignment；
- `evaluate_assignment_rl_playback_diagnostics.py:725-756` 的 reset patch 只捕获
  coverage，且该入口在 `2205` 之后仍由 wrapper step 驱动、在 `2366-2422` 写
  diagnostics outputs；它不能替代 transition facts/result；
- 当前相关 standalone tests 位于 `scripts/environments/`。profile/config、
  manifest、resolver/observation、wrapper fake-env、logger whitelist、pure tensor
  和 playback diagnostics 入口均已逐文件盘点；§19 区分了可在 Phase A 执行与必须
  deferred 的脚本。本轮方案设计没有运行任何测试入口。

---

## 4. Authoritative V2.1 contracts carried into Phase A

Phase A 原样携带以下冻结契约，不重新设计：

1. 固定物理 step；lifecycle/opportunity 才触发 assignment tick；
2. environment raw facts 与 lifecycle-derived result 分层；
3. 先更新事实，再生成 event/local-set/cost/Top-K/mask/DVM/proposal；
4. global fixed-width observation + global task IDs + local action mask；
5. current global task ID 表示 CONTINUE；executing noop masked；
6. policy proposal 与 resolver effective assignment 永远分离；
7. resolver 只 validate/commit proposal，不搜索 matching/subset/second choice；
8. transfer component 整体接受或拒绝，commit 原子；
9. nominal cost = expected navigation time + pair-specific alignment time；
10. invalid path 使用显式 mask；
11. structural terminal pair failure 为 episode-permanent；
12. `TEAM_INFEASIBLE`、termination reason 由唯一 lifecycle authority 派生；
13. team reward 严格 mean → component-once penalty → broadcast；
14. actor valid-only，critic/GAE/ValueNorm 保留全部有效物理步；
15. nondecision HAPPO ratio 严格为 1，使用 `torch.where`，不是乘法插值；
16. resolver commit diagnostic 不自触发下一 assignment tick；
17. event-gated off 直达 resolved pre-event profile 的原实现；
18. event-gated checkpoint 是 distinct v3，shape 相同不构成 semantic compatibility。

所有 `[NUMERIC-TBD]` 保持未选定。Phase A 可以定义 required config slot 和 validator，
不能写推荐值或 runtime default。

本文后续使用两个状态标签，避免把本方案新增的 implementation choice 误称为 V2.1
原文已经冻结：

```text
[FROZEN-V2.1]
  上述方法语义；本方案不得改变。

[PHASE-A-PROPOSED-FOR-APPROVAL]
  为使接口可实施而新增的 exact schema/type/version/validation choice；
  只有 GPT/user 批准本方案后才可进入代码。
```

特别是 pair-attributed raw-signal shapes、额外 cumulative failed-pair snapshot、
canonical invalid-cost representation、terminal no-decision mask representation 和
supported immutability/alias-isolation mechanism 都属于后一个标签。

---

## 5. Phase A scope

Phase A 后续实施只包含：

- 单一 selector/registry、discriminated resolved-profile family、dispatcher 和 direct bypass；
- 两个 immutable transition schema；
- generation、consume-once ledger/receipt、authority stamp 和 assertions；
- typed event/cost/path/local-set/Top-K/DVM/proposal/component/rejection DTO；
- conditional scenario parse/apply；
- strict v2/v3 semantic dispatcher 和 manifest-only validation；
- team reward semantic config；
- typed correctness diagnostics schema；
- legacy 与 Contract C 的 pure/static/default-off identity closeout。

Phase A 可以让 `event_gated_local_mrta` 被 parse/resolve，并能创建 interface-only v3
semantic descriptor mapping；它不能让该 profile 到达 environment、current resolver、HARL actor、
checkpoint weight I/O 或 playback loop。

---

## 6. Explicit exclusions and later-phase ownership

| Work | Owning phase | Phase A action |
|---|---|---|
| real pre-reset facts capture | B0 | schema only |
| lifecycle state mutation/authority runtime | B0 | authority identity only |
| failed pair accumulation/`TEAM_INFEASIBLE`/termination runtime | B0/D | enum/schema only |
| local set/owner expansion/merge/Top-K | B | DTO only |
| event trigger scheduler | B | event-source enum/assertion only |
| action-mask/DVM runtime | B/C | snapshot DTO only |
| terminal/no-opportunity DTO → HARL facade/buffer historical-mask adaptation | B/C | present/mask contract only |
| switch/preemption/component resolver | B | request/result DTO only |
| actor subset sampling | C | route/manifest identity only |
| rollout buffer DVM | C | shape contract only |
| actor loss/entropy/advantage/factor | C | semantic manifest only |
| team reward/rejection penalty runtime | D | config/formula only |
| proper-time-limit info/bad mask | D | raw facts field only |
| training/playback/evaluation/ablation | E | prohibited |

Phase A 不修改 `assignment_state.py`、current observation/resolver behavior、reward tensor、
installed HARL 或 checkpoint weights。

---

## 7. Resolved-profile identity and dispatcher design

### 7.1 One selector, no second event flag

唯一 raw selector 继续是：

```text
assignment_lifecycle_profile
```

新增第五个非默认值：

```text
event_gated_local_mrta
```

禁止新增独立的 `event_gated_enabled=False`。否则会形成两套 authority，并改变旧 config
serialization、logger/file side effects。

```text
profile in existing four:
  event gate off

profile == event_gated_local_mrta:
  event gate on
```

### 7.2 New pure module

计划新增：

```text
assignment_profile_contract.py
```

核心类型：

```text
AssignmentProfileName(Enum)
AssignmentRuntimeRoute(Enum)
AssignmentCheckpointFamily(Enum)
AssignmentProfileSupport(Enum)
AssignmentRuntimeReadiness(Enum)

@dataclass(frozen=True, slots=True)
ResolvedExistingAssignmentProfile

@dataclass(frozen=True, slots=True)
ResolvedEventGatedAssignmentProfile

ResolvedAssignmentProfile =
  ResolvedExistingAssignmentProfile | ResolvedEventGatedAssignmentProfile
```

两类 resolved object 使用 `profile_name` 作为 discriminant，并共享以下 identity fields：

| Field | Type | Meaning |
|---|---|---|
| `profile_contract_version` | `str` | `assignment_resolved_profile_v1` |
| `profile_name` | enum | canonical selector |
| `resolution_origin` | enum | `FORMAL_ENTRYPOINT` or `DIRECT_WRAPPER_FALLBACK` |
| `runtime_route` | enum | exact existing route or event Phase-A block |
| `checkpoint_family` | enum | native v2 / explicit ablation v2 / none / v3 |
| `training_support` | enum | allowed / existing-blocked / Phase-A-blocked |
| `playback_support` | enum | normal / explicit-ablation / diagnostics / blocked |
| `runtime_readiness` | enum | existing-ready or interface-only |

`ResolvedExistingAssignmentProfile` adds the following current-runtime fields；这些字段在
event variant 上不存在：

| Field | Type | Meaning |
|---|---|---|
| `resolver_enabled` | `bool` | exact old mapping; event route has its own route id |
| `lifecycle_observation_enabled` | `bool` | exact old mapping |
| `lifecycle_mask_enabled` | `bool` | exact old mapping |
| `actor_schema_version` | `str` | exact current per-profile registry value |
| `shared_schema_version` | `str` | exact current per-profile registry value |
| `shared_construction_mode` | `str` | exact old mapping |
| `mask_contract_version` | `str` | exact old mapping |
| `budget_release_contract` | `str` | exact old mapping |
| `legacy_guardrail_profile` | `str` | exact old mapping |
| `policy_sequence_route` | `str` | exact current per-profile registry value |
| `training_semantic_contract` | frozen typed spec | exact algorithm/state/share/recurrent/save identity |

四个旧 profile 的 `to_legacy_wrapper_mapping()` 必须逐 key、逐 value、逐 insertion order
等于 current wrapper dict。只有 `ResolvedExistingAssignmentProfile` 定义该方法。

`ResolvedEventGatedAssignmentProfile` 只增加一个 event-only semantic payload：

| Field | Type | Meaning |
|---|---|---|
| `event_gated_target_semantics` | frozen `EventGatedTargetSemantics` | future event-route schema/method/training identity |

它**没有** `resolver_enabled`、`lifecycle_observation_enabled`、
`lifecycle_mask_enabled` 或 `to_legacy_wrapper_mapping()`。因此 correctness 不依赖 consumer
“先看 readiness、再忽略 true bool”；旧 boolean consumer 在类型层只能接收
`ResolvedExistingAssignmentProfile`，把 event object 传入 current Contract C route 必须
立即 `TypeError`/typed route error。

`event_gated_local_mrta` 的 proposed exact resolved identity 为：

| Field | Exact value |
|---|---|
| `profile_contract_version` | `assignment_resolved_profile_v1` |
| `profile_name` | `event_gated_local_mrta` |
| `resolution_origin` | `FORMAL_ENTRYPOINT` on supported runtime entrypoints |
| `runtime_route` | `event_gated_phase_a_interface_only_v1` |
| `checkpoint_family` | `assignment_checkpoint_contract_v3` |
| `training_support` | `phase_a_blocked` |
| `playback_support` | `blocked` |
| `runtime_readiness` | `interface_only` |
| `event_gated_target_semantics` | exact mapping below |

```text
event_gated_target_semantics:
  contract_version: event_gated_target_semantics_v1
  actor_schema_version: event_gated_global_actor_observation_v1
  shared_schema_version: event_gated_global_centralized_observation_v1
  shared_construction_mode: global_fixed_width_centralized_v1
  mask_contract_version: event_gated_global_id_local_mask_v1
  budget_release_contract: authoritative_lifecycle_release_v1
  policy_sequence_route: event_gated_decision_valid_feed_forward_v1

  training_semantic_contract:
    contract_version: event_gated_happo_ep_feed_forward_v1
    algorithm_name: happo
    state_type: EP
    share_param: false
    use_recurrent_policy: false
    use_naive_recurrent_policy: false
    actor_buffer_generator: feed_forward_generator_actor
    serialization_mode: state_dict
    save_entire_model: false
    installed_harl_mutable: false
```

dispatcher 必须对 union 做 exhaustive type/discriminant match：existing object 才可进入旧
wrapper mapping；event object 只能进入 event readiness guard，Phase A 必须 fail closed。
若 GPT/user 不批准这些 schema IDs，A1 不开始。

### 7.3 Canonical import and module identity boundary

Phase 9G-8I-3-0R-2F/R2F1 已证明：同一源文件以 bare top-level key 与 package-qualified
key 各加载一次，会生成两套 enum/dataclass/exception identity。本节依据实际仓库中的：

```text
AgentRead/202607/20260721/
  PHASE9G8I30R2F_INITIAL_CONDITION_RUNTIME_MODULE_IDENTITY_BOUNDARY_REPAIR_DESIGN.md
AgentRead/202607/20260722/
  PHASE9G8I30R2F1_INITIAL_CONDITION_MODULE_IDENTITY_REPAIR_AND_IMPORT_BOUNDARY_REGRESSION.md
```

冻结：

```text
one identity-bearing source file
→ one canonical production module key
```

Canonical package prefix：

```text
isaaclab_tasks.direct.scan_mobile_manipulator
```

| Source file | Sole production module key |
|---|---|
| `assignment_profile_contract.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract` |
| `assignment_lifecycle_transition_contract.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract` |
| `assignment_event_contract.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract` |
| `assignment_mrta_contract.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` |
| `assignment_team_reward_contract.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_team_reward_contract` |
| `assignment_event_gated_diagnostics_contract.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_gated_diagnostics_contract` |
| `assignment_checkpoint_contract_v3.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_contract_v3` |
| `assignment_checkpoint_semantic_dispatch.py` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_checkpoint_semantic_dispatch` |

Import rules：

1. package-internal production consumer 只使用相对 package import；
2. script entrypoint 只能在 `simulation_app = app_launcher.app` 和
   `import isaaclab_tasks` 后使用完整 package path；
3. 禁止 bare `import assignment_profile_contract`，也禁止
   `try relative / except ImportError: bare import` fallback；
4. 禁止 `sys.modules` alias、duck typing、对象重建或放宽 `isinstance` 来掩盖双重导入；
5. identity-bearing contract module 在 enum/dataclass/custom-exception 声明前检查 canonical
   `__name__`；bare-key load 必须在第二套类型产生前 fail-fast；
6. formal entrypoint 创建的 resolved object 原对象传递；wrapper 不通过 mapping/JSON/string
   重建实例。

Pre-AppLauncher boundary：

- raw-profile preflight 必须 import-free，或只读取 ordered primitive strings；不得导入或
  创建 canonical enum/dataclass/exception identity；
- `scenario_config.py` 只处理 primitive vocabulary、raw declaration 和 provenance，不导入
  `assignment_profile_contract`；
- prelaunch rejection 使用 built-in error + stable error code，不声称它是 canonical typed
  contract exception；
- package bootstrap 后才导入 canonical contract，并逐项、逐序比较 primitive vocabulary
  与 canonical registry；drift 在 output-dir/env/runner/actor/checkpoint/file side effect 前
  fail-fast；
- 若多个 prelaunch consumer 必须共享 vocabulary，使用不导入 Isaac/package contract
  type 的 import-free primitive-only location；禁止从完整 contract module取 enum。

Direct/fake test 不得 bare-import contract type。它必须使用不会执行
`isaaclab_tasks/__init__.py` 的 canonical namespace harness，或在 clean child process 中把
源注册到唯一完整 canonical key；同一文件不得同时注册第二 key。测试 harness 的 canonical
registration 不是 production alias。

A1a 创建完整 module-identity regression suite，并冻结 canonical module/type identity；
formal entrypoint 产生对象与 wrapper 收到相同 object/class 的 positive wiring gate 只能在
A1c 完成，A1a 不得为了提前通过而添加未使用 production import。

### 7.4 Authority and propagation

```text
raw declaration
→ assignment_profile_contract.normalize_profile_name()
→ validate declarations/conflicts
→ after all formal-entrypoint raw sources are composed,
  resolve_assignment_profile() exactly once per entrypoint process
→ immutable ResolvedAssignmentProfile
→ pass the same object to wrapper/training/checkpoint/playback consumers
```

职责：

| Stage | Responsibility |
|---|---|
| scenario parser | 收集 source/value，不自行分派 runtime |
| profile module | 唯一 normalize、validate、registry 和 resolved identity authority |
| train/play/evaluate entrypoint | compose raw sources then create one process-local identity；不写入 serialized `env_args` |
| wrapper | 只接受 canonical class；消费并 assert raw config 与 identity 一致；只有 existing subtype 保留旧 mapping property |
| runner/training contract | 只按 identity route；不重新读字符串 |
| manifest builder | 接受 identity object；v2 只读 canonical name，v3 写完整 identity |
| playback/checkpoint | 使用 wrapper 持有的同一 identity；不重新猜 profile |

为保持 `configs.json` identity，resolved object 作为显式 Python 参数传递，不插入
`args`、`env_args` 或 env cfg 的新默认字段。

两种入口模式互斥：

- formal train/play/evaluate entrypoint：prelaunch 只用 primitive vocabulary 检查可见 raw
  declaration，不导入 contract、不创建 identity；package bootstrap 后，Hydra/env cfg +
  scenario raw sources compose 并 resolve exactly once，wrapper 必须收到同一 object/class；
  identity 缺失或不一致 fail-fast；
- direct/fake unit construction：没有 formal entrypoint 时，wrapper 可以调用同一 canonical
  resolver 一次作为 test-only fallback，并在 identity 上标
  `resolution_origin=direct_wrapper_fallback`。

formal path 禁止退回 wrapper fallback；因此“resolve once”不与 fake-env compatibility
形成第二 authority。

### 7.5 Source precedence and conflicts

| Declarations | Result |
|---|---|
| no explicit declaration | 不写 env cfg；由现有 env default `legacy` 进入 resolver |
| top-level only | canonicalize and apply |
| nested only | canonicalize and apply |
| top-level + nested, canonical equal | accept once; retain both provenance labels |
| top-level + nested, different | `ProfileResolutionError` |
| empty/unknown | `ProfileResolutionError` |
| runtime identity differs from raw cfg | `ResolvedProfileMismatchError` |

不得保留当前“nested 后写 silently wins”的冲突行为。

后两类 correction 是 intentional Phase A config-validation changes，不属于 default-off
byte identity：当前 explicit scenario lifecycle profile 被 parse 但不 apply，top/nested
conflict 也没有 source-aware fail-fast。identity claim 只覆盖 absent declaration，或已经
通过 direct env cfg/完整 scenario settings 解析出同一 existing profile 且满足 §7.7
prerequisites 的 downstream route。

### 7.6 Profile matrix

| Resolved profile | Event gate | Runtime route | Checkpoint family | Phase A behavior |
|---|---:|---|---|---|
| `legacy` | off | exact `AssignmentOnPolicyHARunner` + legacy wrapper path | exact native v2 where currently supported | direct bypass |
| `lifecycle_contract_c` | off | exact current Contract C observation/mask/resolver path | exact native v2 | direct bypass; resolver remains on |
| `lifecycle_ablation` | off | exact current ablation route | explicit ablation target; no native training save | existing normal-training block |
| `diagnostics_hidden_state` | off | exact current diagnostics route | no native training checkpoint | existing diagnostics/training block |
| `event_gated_local_mrta` | on | `EVENT_GATED_PHASE_A_INTERFACE_ONLY` | distinct v3 interface descriptor only | fail before env/runner/actor/checkpoint I/O/play loop |

禁止：

```text
event-gated runner + DVM=1
```

模拟任一旧 profile。

### 7.7 Existing low-level prerequisite authority

Resolved profile identity 不生成、覆盖或放宽 current low-level config。A1 定义
`ResolvedProfilePrerequisiteSpec` 并调用 current wrapper validators；profile resolution
与 raw prerequisite consistency 是两个连续 gate：

| Profile | Existing prerequisites that remain exact |
|---|---|
| `legacy` | `assignment_lifecycle_resolver_enabled=false` |
| `lifecycle_ablation` | resolver/cooldown/redirect-guardrail/failed-pair-memory all disabled |
| `lifecycle_contract_c` | resolver enabled；cooldown enabled；trigger mode `budget` or `budget_and_streak`；duration > 0；cooldown mask false；redirect guardrail false；failed-pair-memory false |
| `diagnostics_hidden_state` | resolver enabled；existing training block retained |
| `event_gated_local_mrta` | proposed event identity exact；Phase-A readiness block occurs before current wrapper runtime validators |

scenario 只声明 profile 而没有满足某个 existing profile 的 raw prerequisites 时，仍按 current
validator fail-fast；central dispatcher 不得“帮助”补齐或静默改写这些 settings。v3 identity
同时绑定 event profile 的 HAPPO/EP/feed-forward/non-shared/state-dict contract。

---

## 8. `ExecutionTransitionFacts` schema

**Status:** `[PHASE-A-PROPOSED-FOR-APPROVAL]`

计划新增纯模块：

```text
assignment_lifecycle_transition_contract.py
```

符号：

```text
E = vectorized environments
M = fixed robots
N = fixed global tasks
```

### 8.1 Exact fields

| Field | Shape/type | dtype | Device/contract |
|---|---|---|---|
| `schema_version` | scalar | `str` | `execution_transition_facts_v1` |
| `producer_contract_version` | scalar | `str` | `execution_facts_producer_contract_v1` |
| `producer_id` | scalar | `ExecutionFactsProducerId` string enum | exact `ENV_EXECUTION_FACTS_PRODUCER_V1` |
| `env_id` | `[E]` | `torch.int64` | shared declared device; unique row ids |
| `episode_generation` | `[E]` | `torch.int64` | non-negative |
| `transition_generation` | `[E]` | `torch.int64` | per-env monotonic; never inferred from wrapper snapshot |
| `physical_terminated` | `[E]` | `torch.bool` | raw fact |
| `physical_truncated` | `[E]` | `torch.bool` | raw fact |
| `time_limit_reached` | `[E]` | `torch.bool` | raw fact |
| `bad_transition` | `[E]` | `torch.bool` | raw proper-time-limit fact |
| `completion_signals` | `[E,M,N]` | `torch.bool` | raw pair-attributed completion signal |
| `terminal_pair_failure_signals` | `[E,M,N]` | `torch.bool` | structural terminal signal only |
| `forced_release_signals` | `[E,M,N]` | `torch.bool` | raw pair-attributed release fact |
| `robot_unavailable_signals` | `[E,M]` | `torch.bool` | raw availability edge |
| `robot_recovered_signals` | `[E,M]` | `torch.bool` | raw recovery edge |
| `coverage_before_reset` | `[E,N]` | `torch.bool` | pre-reset snapshot |
| `task_state_before_transition` | `[E,N]` | `torch.int64` | pre-lifecycle state |
| `robot_state_before_transition` | `[E,M]` | `torch.int64` | pre-lifecycle state |
| `ownership_before_transition` | `[E,N]` | `torch.int64` | owner `-1..M-1` |
| `consume_once_token` | `[E]` | `torch.int64` | opaque, non-RNG, environment facts-producer-owned |

`completion_signals` 保留 robot attribution；`LifecycleTransitionResult.completed_tasks`
再沿 robot 维做 authoritative task-level derivation。Phase A 定义并测试下面的 schema
assertions；真正 lifecycle derivation 仍属于 B0。

Exact producer identity：

```text
ExecutionFactsProducerId(str, Enum):
  ENV_EXECUTION_FACTS_PRODUCER_V1 = "env_execution_facts_producer_v1"
```

定义 owner-match tensor：

```text
owner_match[e,i,j] :=
  ownership_before_transition[e,j] == i
```

constructor/batch validator 在 ledger consume 前原子验证：

```text
completion_signals.sum(dim=1) <= 1                       # each [E,N] cell
not (completion_signals & terminal_pair_failure_signals) # each [E,M,N] pair
completion_signals             => owner_match
forced_release_signals         => owner_match
terminal_pair_failure_signals  => owner_match             # default pair-failure form
not (robot_unavailable_signals & robot_recovered_signals) # each [E,M] robot
```

因此未占有 task 不能产生 owner-attributed completion/release/default terminal-failure
boolean。Phase A 不支持 external/system 对 non-owner 的 release；未来若方法需要，必须新增
typed cause/record 及独立 validator，禁止放宽上述 boolean invariant。

### 8.2 Explicitly forbidden fields

raw facts exact-key parser 必须拒绝：

```text
TEAM_INFEASIBLE
termination_reason
updated_task_state
updated_robot_state
updated_ownership
released_tasks
new_failed_pairs
updated_failed_pairs
new_team_infeasible_tasks
```

### 8.3 Device and serialization

- 所有 dense tensor 同一显式 device；
- constructor 不做隐式 CPU/GPU move；
- exact dtype，不自动 cast；
- input 使用 `detach().clone().contiguous()`，`requires_grad=False`；
- runtime facts 不 pickle、不写 checkpoint、不进入 rollout buffer；
- v3 manifest 只保存 schema version、shape/dtype、pair-attribution observable contract、
  facts producer identity 与 lifecycle authority identity；
- diagnostics 只能通过 explicit summary serializer 复制到 CPU；不能暴露 `__dict__`。

`time_limit_reached` 或 `bad_transition` 为真时，validator 要求
`physical_truncated=true`。上述任一 pair/robot invariant 失败时整批拒绝，ledger 不得
部分消费。

---

## 9. `LifecycleTransitionResult` schema

**Status:** `[PHASE-A-PROPOSED-FOR-APPROVAL]`

### 9.1 Exact fields

| Field | Shape/type | dtype | Meaning |
|---|---|---|---|
| `schema_version` | scalar | `str` | `lifecycle_transition_result_v1` |
| `authority_contract_version` | scalar | `str` | `unique_lifecycle_authority_v1` |
| `facts_producer_id` | scalar | `ExecutionFactsProducerId` string enum | exact source `ENV_EXECUTION_FACTS_PRODUCER_V1` |
| `authority_id` | scalar | `LifecycleAuthorityId` string enum | exact `LIFECYCLE_AUTHORITY_V1` |
| `env_id` | `[E]` | `torch.int64` | exact source ids |
| `episode_generation` | `[E]` | `torch.int64` | exact source generation |
| `transition_generation` | `[E]` | `torch.int64` | exact source generation |
| `completed_tasks` | `[E,N]` | `torch.bool` | derived task completion |
| `released_tasks` | `[E,N]` | `torch.bool` | derived release |
| `new_failed_pairs` | `[E,M,N]` | `torch.bool` | this transition delta |
| `updated_failed_pairs` | `[E,M,N]` | `torch.bool` | cumulative event-updated authoritative snapshot |
| `new_team_infeasible_tasks` | `[E,N]` | `torch.bool` | derived after failed-pair update |
| `updated_task_state` | `[E,N]` | `torch.int64` | resolver-pre baseline state |
| `updated_robot_state` | `[E,M]` | `torch.int64` | resolver-pre baseline state |
| `updated_ownership` | `[E,N]` | `torch.int64` | event-updated baseline `a0` |
| `termination_reason` | `[E]` | `torch.int64` encoding `TerminationReason` | exact enum below |
| `lifecycle_events` | `tuple[LifecycleEventRecord, ...]` | immutable typed records | pre-policy lifecycle subset only |
| `facts_consume_token` | `[E]` | `torch.int64` | exact source token |
| `authority_receipt_id` | `[E]` | `torch.int64` | ledger-owned monotonic receipt id |

`updated_failed_pairs` 是对 V2.1 最小字段列表的必要 authoritative snapshot 补充。没有它，
local mask/`TEAM_INFEASIBLE` 会被迫回读 current resolver `pair_state`，形成第二 authority。
该字段不改变 frozen failed-pair 方法语义。

### 9.2 Authority rules

- environment 的唯一职责是生成 immutable `ExecutionTransitionFacts`；environment
  不是 lifecycle authority，也无权构造/finalize result；
- lifecycle authority 消费合法 facts，派生 task/robot lifecycle state、termination 和
  finalized lifecycle events，并生成 `LifecycleTransitionResult`；
- Phase A 只冻结 producer/authority contract 与 identity，不冻结 runtime class、module 或
  component placement；实际 lifecycle authority 放置由 B0 review 决定；
- public caller 不能直接 finalize result；
- 只有 `LifecycleTransitionResultFactory` 接受有效
  `TransitionConsumeReceipt` 后才能构造；
- receipt、facts、result 的 producer、env/episode/transition/token 必须逐 row相同，factory
  stamp/result authority 必须是唯一 lifecycle authority；
- `completed_tasks == completion_signals.any(dim=1)`；task-level result 只能由 lifecycle
  authority 从已通过 §8 pair-attributed assertions 的 facts 派生；
- `completed_tasks[e,j]=true` 时，`updated_task_state[e,j]` 必须为 current
  `TASK_COMPLETED` encoding，且 `updated_ownership[e,j] == -1`；completed task 不得在同一
  transition 获得新 ownership；
- result finalized 后只读；
- `lifecycle_events` 只允许 §11.1 的 pre-policy lifecycle subset；retry/resolver diagnostic
  record 出现时 schema validation failure；
- resolver 只拿 read-only snapshot/accessor clone；
- resolver 不能回写 result；
- resolver effective commit 是独立 `TransferComponentResult`；
- `updated_ownership` 始终是 resolver 前的 `a0`；
- terminal result 使后续 DVM 全 0，并禁止 proposal/component commit；该行为到 B/C 实现。

Exact enums：

```text
LifecycleAuthorityId(str, Enum):
  LIFECYCLE_AUTHORITY_V1 = "lifecycle_authority_v1"

TerminationReason(IntEnum):
  NONE = 0
  ALL_TASKS_COMPLETED = 1
  NO_FEASIBLE_TASKS_REMAIN = 2
  TIME_LIMIT = 3
```

任何 raw physical terminal 无法映射到冻结 reason 时，B0 必须 fail-closed 并请求方法决策，
不能静默添加 `OTHER`。

---

## 10. Generation, consume-once, authority and immutability

**Status:** `[PHASE-A-PROPOSED-FOR-APPROVAL]`

### 10.1 External ledger, not a mutable DTO flag

不得在 frozen facts 内写 `consumed=True`。计划类型：

```text
TransitionConsumeToken
TransitionConsumeReceipt
TransitionConsumeLedger
ExecutionFactsProducerStamp
LifecycleAuthorityStamp
```

规则：

1. environment facts producer 以
   `ExecutionFactsProducerStamp(ENV_EXECUTION_FACTS_PRODUCER_V1, contract_version)`
   独占 facts/token 生成权；
2. token 为 per-env monotonic `int64`，不调用 Python/Torch/NumPy RNG；
3. lifecycle authority 以
   `LifecycleAuthorityStamp(LIFECYCLE_AUTHORITY_V1, contract_version)` 独占 ledger 与
   result finalization 权；
4. producer stamp 与 authority stamp 是不同类型，禁止互换或用 source provenance 代替；
5. batch consume 先完整 validate producer、schema 和 row invariants，再 atomic record；
   任一 row 失败则全 batch 不消费；
6. successful consume 返回绑定 facts producer 的 immutable receipt；
7. result factory 同时需要 facts、receipt、lifecycle authority stamp；
8. resolver 只能验证/读取 result，不能操作 ledger。

`episode_generation` 每 reset 增加；`transition_generation` 在进程 lifetime 内 per-env
单调增加，不因 episode reset 回零。Phase A 不指定 ledger/authority 在 environment、
wrapper 或独立 runtime component 中的实际位置；该 placement 是 B0 的显式决策。

### 10.2 Supported immutability and alias-isolation guarantee

current `@dataclass(frozen=True)` 只能防止 field rebinding，不能阻止 tensor alias 上的
`fill_()`。新 schema 对**公开、受支持 API**冻结以下可证明保证：

- metadata frozen；
- constructor 对 input `detach().clone().contiguous()`，没有 ingress alias；
- tensor storage private，不提供 public direct-storage accessor；
- public accessor 每次返回 clone，不返回 writable view；
- field rebind 失败；
- supported-path internal corruption 在 consume/serialize/read-for-resolver 前 fail-fast；
- ledger/receipt 独立于 DTO，consumer 不能通过修改 DTO 伪造 consume state。

Externally observable semantic contract 只包含：

```text
frozen metadata
+ no public writable alias
+ supported-path mutation detection
```

tensor `_version`、storage identity、private-field layout、detector name，以及未来可能使用的
digest/backing 都只是可替换的 implementation detail。它们不得进入 v3 semantic
fingerprint 或 checkpoint compatibility condition；替换 detector 而 observable behavior
不变时，不创建新 MRTA semantic family。

候选实现可以在 construction/finalization 内部记录 storage identity、shape/dtype/device 和
tensor `_version`，也可以采用其他 mechanism。这里不宣称 PyTorch storage 在 adversarial
reflection、`.data` 或未受支持的底层 storage 绕行下“数学意义的 deep immutable”，任何
候选 detector 也不是 cryptographic integrity proof。
Phase A completion 的准确名称是：

```text
frozen metadata + no public writable alias + supported-path mutation detection
```

Phase A pure tests覆盖 source mutation、accessor clone mutation、field rebind 和通过正常
in-place op 制造的 supported-path internal integrity corruption。若实现级 regression test
直接检查 `_version`，该测试不得进入 semantic descriptor/fingerprint compatibility evidence。
adversarial/unsupported bypass 不属于本 contract，不作为 Phase A 完成条件。

### 10.3 Exception hierarchy

```text
AssignmentContractError
├── ProfileResolutionError
├── PhaseAExecutionNotAuthorizedError
├── ResolvedProfileMismatchError
├── TransitionContractError
│   ├── TransitionSchemaError
│   ├── TransitionGenerationError
│   ├── DuplicateTransitionConsumeError
│   ├── TransitionTokenMismatchError
│   ├── ExecutionFactsProducerMismatchError
│   ├── LifecycleAuthorityMismatchError
│   └── FinalizedSnapshotMutationError
└── CheckpointSemanticMismatchError
```

错误 message 必须包含可用的 expected/actual env、episode、transition、token、
facts producer、lifecycle authority、profile/version；不能只抛泛化 `ValueError`。

### 10.4 Failure matrix

| Case | Expected result |
|---|---|
| correct generation first consume | pass；返回唯一 receipt |
| duplicate consume | `DuplicateTransitionConsumeError`；ledger 不变 |
| stale transition | `TransitionGenerationError(stale)` |
| future transition | `TransitionGenerationError(future)` |
| wrong env id | `TransitionGenerationError(env_id)` |
| wrong episode generation | `TransitionGenerationError(episode)` |
| result token mismatch | `TransitionTokenMismatchError` |
| resolver reads wrong generation | `TransitionGenerationError(resolver_snapshot)` |
| finalized object mutation | field rebind 或 `FinalizedSnapshotMutationError` |
| raw facts contains derived field | `TransitionSchemaError(unexpected_fields)` |
| facts built/stamped by wrong producer | `ExecutionFactsProducerMismatchError`；ledger 不变 |
| result built without receipt | `LifecycleAuthorityMismatchError` |
| result built by wrong authority | `LifecycleAuthorityMismatchError` |
| two robots complete one task | `TransitionSchemaError(completion_cardinality)`；ledger 不变 |
| same pair completes and terminal-fails | `TransitionSchemaError(pair_signal_conflict)`；ledger 不变 |
| completion pair is not current owner | `TransitionSchemaError(completion_owner)`；ledger 不变 |
| forced release pair is not current owner | `TransitionSchemaError(release_owner)`；ledger 不变 |
| terminal failure pair is not current owner | `TransitionSchemaError(failure_owner)`；ledger 不变 |
| one robot unavailable and recovered | `TransitionSchemaError(availability_edge_conflict)`；ledger 不变 |
| completed task receives new ownership | `TransitionSchemaError(completed_task_ownership)`；result not finalized |
| valid completion derivation | `completed_tasks == completion_signals.any(dim=1)` |
| input tensor mutated after construction | internal snapshot remains exact |
| accessor return mutated | internal snapshot remains exact |
| profile declarations conflict | `ProfileResolutionError` with sources |
| event profile reaches old boolean consumer | typed route error before wrapper Contract C path |
| event profile requests Phase A runtime | `PhaseAExecutionNotAuthorizedError` before side effects |

---

## 11. Typed event/cost/local-set/DVM/component interfaces

**Status:** `[PHASE-A-PROPOSED-FOR-APPROVAL]`

计划新增：

```text
assignment_event_contract.py
assignment_mrta_contract.py
```

所有 tensor DTO 使用 §10 的 alias-isolated/private storage contract，绑定：

```text
env_id
episode_generation
transition_generation
assignment_tick_generation
```

`assignment_tick_generation [E] int64` 只在 assignment opportunity 上增加；它与固定物理
`transition_generation` 不混用。

### 11.1 Three disjoint lifecycle/opportunity/diagnostic type systems

禁止用一个 universal event enum/record 表示 pre-policy lifecycle、scheduled opportunity
和 post-resolver diagnostic。三套类型、record、producer/authority 和 container 必须在类型
层彼此独立。

#### 11.1.1 Finalized pre-policy lifecycle events

`LifecycleEventType` exact enum **只有七个值**：

```text
TASK_COMPLETED
TASK_RELEASED
TERMINAL_PAIR_FAILURE_RECORDED
TASK_BECAME_TEAM_INFEASIBLE
ROBOT_BECAME_UNAVAILABLE
ROBOT_RECOVERED
ROBOT_NEEDS_ASSIGNMENT
```

`LifecycleCausalSource` exact enum：

```text
EXECUTION_FACTS
LIFECYCLE_DERIVATION
```

`LifecycleEventRecord` exact fields：

| Field | Type |
|---|---|
| `schema_version` | `lifecycle_event_record_v1` |
| `event_id` | `(env, episode, transition, ordinal)` immutable tuple |
| `causal_source` | `LifecycleCausalSource` |
| `event_type` | `LifecycleEventType` |
| `env_id` / episode/transition generation / ordinal | integers |
| `robot_id` / `task_id` | optional global ids |
| `trigger_eligible` | exact `true` |
| `facts_consume_token` | int |
| `authority_id` | exact `LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1` |
| `payload` | `TaskLifecycleEventPayload \| RobotLifecycleEventPayload \| PairFailureEventPayload` |

causal source 只描述事实来源，不授予创建权；七类 record 都由 lifecycle authority 在
policy 前 finalized，并且只能进入 `LifecycleTransitionResult.lifecycle_events`。禁止
mutable `details: dict`。

#### 11.1.2 Scheduled assignment opportunities

```text
AssignmentOpportunityType(str, Enum):
  ASSIGNMENT_RETRY_DUE = "assignment_retry_due"

AssignmentOpportunityProducerId(str, Enum):
  RETRY_SCHEDULER_V1 = "retry_scheduler_v1"
```

`AssignmentOpportunityRecord` exact fields：

| Field | Type |
|---|---|
| `schema_version` | `assignment_opportunity_record_v1` |
| `opportunity_id` | `(env, episode, transition, assignment_tick, ordinal)` immutable tuple |
| `opportunity_type` | `AssignmentOpportunityType` |
| `producer_id` | exact `RETRY_SCHEDULER_V1` |
| env/episode/transition/tick/ordinal | integers |
| `robot_id` | global robot id |
| `retry_generation` | non-negative integer |
| `trigger_eligible` | exact `true` |

retry scheduler 只能在 result finalized 后创建该 record；它从不回写
`LifecycleTransitionResult`，也不伪装成 lifecycle event。

#### 11.1.3 Post-resolver diagnostics

```text
ResolverDiagnosticType(str, Enum):
  COMPONENT_ACCEPTED = "component_accepted"
  COMPONENT_REJECTED = "component_rejected"
  OWNERSHIP_TRANSFER_COMMITTED = "ownership_transfer_committed"

ResolverDiagnosticProducerId(str, Enum):
  RESOLVER_DIAGNOSTIC_PRODUCER_V1 = "resolver_diagnostic_producer_v1"
```

`ResolverDiagnosticRecord` exact fields：

| Field | Type |
|---|---|
| `schema_version` | `resolver_diagnostic_record_v1` |
| `diagnostic_id` | `(env, episode, transition, assignment_tick, ordinal)` immutable tuple |
| `diagnostic_type` | `ResolverDiagnosticType` |
| `producer_id` | exact `RESOLVER_DIAGNOSTIC_PRODUCER_V1` |
| env/episode/transition/tick/ordinal | integers |
| `component_id` | stable component id |
| `trigger_eligible` | exact `false` |
| `payload` | typed component acceptance/rejection/transfer payload |

resolver diagnostic 只进入 diagnostic stream；它禁止进入 lifecycle result、assignment
opportunity list、local-set trigger list，或成为下一 assignment tick 的独立触发条件。

Exact lifecycle payload union：

```text
TaskLifecycleEventPayload(
  task_id: int,
  previous_task_state: int,
  updated_task_state: int,
  cause_robot_id: int,  # -1 if not pair-attributed
)

RobotLifecycleEventPayload(
  robot_id: int,
  previous_robot_state: int,
  updated_robot_state: int,
)

PairFailureEventPayload(
  robot_id: int,
  task_id: int,
  newly_recorded: bool,
)
```

Placement contract：

| Container/consumer | Allowed records | Explicitly forbidden |
|---|---|---|
| `LifecycleTransitionResult.lifecycle_events` | seven finalized `LifecycleEventRecord` types | opportunity and resolver diagnostic records |
| retry scheduler output | `AssignmentOpportunityRecord(ASSIGNMENT_RETRY_DUE)` | lifecycle-result mutation and resolver diagnostics |
| local seed/trigger collector | finalized lifecycle events + assignment opportunities | resolver diagnostics |
| resolver diagnostic stream | three `ResolverDiagnosticRecord` types, all `trigger_eligible=false` | lifecycle/opportunity insertion and next-tick trigger |

terminal branch 优先于 trigger collection，因此 terminal result 不产生 proposal。resolver
rejection 后若 robot 仍为 `NEEDS_ASSIGNMENT`，后续 tick 只能由 finalized
`ROBOT_NEEDS_ASSIGNMENT` lifecycle event 或独立 retry opportunity 触发，不能由
`COMPONENT_REJECTED` diagnostic 自触发。任何跨容器 record 都是 schema failure。

### 11.2 DTO table

| Interface | Core fields | Shape/dtype | Generation binding | Owner phase |
|---|---|---|---|---|
| `LifecycleEventRecord` | causal source/seven-value type/global ids/token/authority | scalar + immutable tuple | transition + facts token | A define；B0 authority produce |
| `AssignmentOpportunityRecord` | retry type/robot/retry generation/scheduler producer | scalar + immutable tuple | transition + assignment tick | A define；B scheduler produce |
| `ResolverDiagnosticRecord` | three-value type/component/false trigger/producer | scalar + immutable tuple | transition + assignment tick | A define；B resolver produce |
| `NominalPairCostResult` | nav/alignment/nominal/path valid/unit | four `[E,M,N]`; floats `float32`, mask bool | tick | A define；B produce |
| `LocalSetRequest` | seeds/needs/availability/state/ownership/lifecycle events/opportunities/config refs | robot `[E,M]`, task `[E,N]` | finalized result + tick | A define；B consume |
| `LocalSetResult` | local robot/task masks/owner-added/merge/overflow | `[E,M]`, `[E,N]`, enums | tick | A define；B produce |
| `TopKCandidateResult` | global ids/valid/cost/current retention | ids/valid/cost `[E,M,K]`, current `[E,M]` | cost + tick | A define；B produce |
| `DecisionValidMaskSnapshot` | provenance masks/opportunity present/action mask/legal count/DVM/forced id | action `[E,M,N+1]`, present/DVM/count/id `[E,M,1]` | tick | A define；B produce；C consume |
| `ProposalSnapshot` | storage/policy/forced/DVM masks; stored id/log-prob; policy proposal kind; historical mask | four masks/id/log-prob `[E,M,1]`, action mask `[E,M,N+1]` | DVM + tick | A define；C produce；B resolver consumes policy rows only |
| `TransferComponentRequest` | component members/`a0`/proposal/cost/hard masks/threshold refs | one env: robot `[M]`, task `[N]`, pair `[M,N]` | tick | A define；B consume |
| `TransferComponentResult` | whole accept/reject/effective/ownership/cost/count/transfer | one component | request + commit generation | A define；B produce |
| `ComponentRejectionRecord` | stable component id/reason/policy/penalty/member ids | scalars + immutable tuples | component | A define；B produce；D count |
| diagnostic envelope/payload | typed kind-specific payload | no universal dict | phase-specific | A define；B0–D produce |

### 11.3 Nominal cost invariants

```text
navigation_cost: [E,M,N] float32 expected seconds
alignment_cost:  [E,M,N] float32 expected seconds
nominal_cost:    [E,M,N] float32 = navigation + alignment
path_valid:      [E,M,N] bool
```

- factory 计算 nominal，consumer 不提交独立不一致值；
- valid cells finite and non-negative；
- invalid cells canonical `NaN`，mask 才是 authority；
- 禁止 arbitrary large finite sentinel；
- estimator/version/unit 进入 v3；
- Phase A test fixture 数值不是方法参数选择。

### 11.4 Local set and Top-K fields

`LocalSetRequest`：

```text
seed_robot_mask             [E,M] bool
needs_assignment_mask       [E,M] bool
robot_available_mask        [E,M] bool
task_state                  [E,N] int64
event_updated_ownership     [E,N] int64
lifecycle_event_records     immutable tuple[LifecycleEventRecord, ...] per env
assignment_opportunities    immutable tuple[AssignmentOpportunityRecord, ...] per env
top_k_spec / robot_cap_spec / task_cap_spec
owner_expansion_rounds      exact integer 1
```

seed/trigger collector 只读取 finalized lifecycle event 与 assignment opportunity 两个 typed
collection；`ResolverDiagnosticRecord` 没有可赋值入口，validator 对混入 diagnostic
fail-fast。

`LocalSetResult`：

```text
LocalSetOverflowDisposition(IntEnum):
  NONE = 0
  FAIL_CLOSED_NO_ASSIGNMENT = 1

local_robot_mask            [E,M] bool
local_task_mask             [E,N] bool
owner_added_robot_mask      [E,M] bool
overlap_merged              [E] bool
overflowed                  [E] bool
overflow_disposition        [E] int64 encoding LocalSetOverflowDisposition
owner_expansion_rounds_used [E] int64, only 0 or 1
```

本方案为第一版 proposed contract 选择 fail-closed，不选择 safe-mode fallback：
overflow row 不生成 proposal/component commit，并记录 non-policy-caused diagnostic。cap 的
数值仍为 `[NUMERIC-TBD]`。

`TopKCandidateResult`：

```text
global_task_ids             [E,M,K] int64, invalid slot -1
candidate_valid             [E,M,K] bool
candidate_nominal_cost      [E,M,K] float32
current_task_id             [E,M] int64
current_task_retained       [E,M] bool
```

valid task IDs 始终为 global `0..N-1`；每 row 无重复；current task 在 event-updated baseline
仍合法时必须出现，即使不在 cost Top-K。

### 11.5 Action-mask provenance and DVM

`DecisionValidMaskSnapshot` 保留组成 mask，避免只交一个不可审计结果：

```text
global_task_valid_mask          [E,N]
failed_pair_legal_mask          [E,M,N]
nominal_path_valid_mask         [E,M,N]
local_topk_or_continue_mask     [E,M,N]
ownership_preemption_legal_mask [E,M,N]
robot_available_mask            [E,M]
decision_opportunity_present    [E,M,1]
target_action_mask              [E,M,N]
noop_action_mask                [E,M,1]
available_actions               [E,M,N+1]
semantic_legal_action_count     [E,M,1]
decision_valid_mask             [E,M,1]
forced_policy_action_id         [E,M,1]
```

Assertions：

- target mask 等于 provenance conjunction；
- executing current task 强制保留；executing noop=false；
- idle/`NEEDS_ASSIGNMENT` noop=true；
- unavailable robot 的 task 全 false、DVM=false；
- terminal row `decision_opportunity_present=false`、semantic action 全 false、
  DVM=false、`forced_policy_action_id=-1`、无 proposal；
- nonterminal row 至少有一个 forced/legal action；
- semantic legal count < 2 ⇒ DVM=false；
- DVM=true ⇒ tick/local/available/nonterminal 且 count ≥ 2；
- raw mask、semantic count、DVM generation 完全相同。

Terminal all-zero semantic mask 是“没有 decision opportunity”的 DTO 表示，绝不能传给
Categorical sampler/evaluator、current `AssignmentIsaacLabEnv._assert_available_actions()`
或 PPO minibatch。固定物理 rollout 中已经发生的 action 必须保留**采样当时**的 historical
mask/action/log-prob/DVM；不得用 post-terminal all-zero snapshot 覆盖。nonterminal
DVM=false forced placeholder 必须在它自己的 historical forced mask 中合法，且该 mask
至少有 forced id 一个 true。把 event DTO 转成 facade/buffer representation、并绕开 current
`assignment_harl_training.py:336-348` 的 all-row-noop assertion，只能在 B/C 新 route
实现；Phase A event route blocked，不修改该 assertion。

### 11.6 Proposal/effective naming

不得使用模糊 `action` 字段：

```text
ProposalKind(str, Enum):
  CLAIM
  CONTINUE
  SWITCH
  NOOP_IDLE

StoredActionRowKind(str, Enum):
  POLICY_PROPOSAL
  FORCED_NONDECISION
  NO_ROW

stored_action_id:
  fixed-rollout stored id; policy/forced row in 0..N, terminal no-row -1

stored_action_log_prob:
  real policy log-prob only when policy_proposal_present_mask=true;
  forced/terminal placeholder 0 is storage-only and never policy evidence

proposed_task_id:
  decoded global task id in -1..N-1 only for a policy proposal; otherwise -1

effective_assignment:
  resolver output in -1..N-1, never stored in ProposalSnapshot
```

`ProposalSnapshot` exact presence fields：

```text
storage_row_present_mask       [E,M,1] bool
policy_proposal_present_mask   [E,M,1] bool
forced_nondecision_mask        [E,M,1] bool
decision_valid_mask            [E,M,1] bool
```

`nonterminal_mask [E,M,1]` 是 sampling/storage 时刻由 episode terminal state broadcast
得到的 historical mask，不得用 post-reset state 重算。

Frozen relations：

```text
policy_proposal_present_mask == decision_valid_mask
storage_row_present_mask == nonterminal_mask
forced_nondecision_mask ==
  storage_row_present_mask & nonterminal_mask & ~decision_valid_mask
storage_row_present_mask ==
  policy_proposal_present_mask | forced_nondecision_mask
not (policy_proposal_present_mask & forced_nondecision_mask)
```

Truth table：

| Row | storage | policy proposal | forced | DVM | Stored semantics |
|---|---:|---:|---:|---:|---|
| decision-valid | true | true | false | true | real sampled id and real log-prob；four-value `ProposalKind` |
| nonterminal forced | true | false | true | false | deterministic forced placeholder；`StoredActionRowKind.FORCED_NONDECISION`；not a proposal |
| terminal no-opportunity | false | false | false | false | id `-1`/diagnostic log-prob `0` only as tensor sentinel；no row semantics |

`NOOP_IDLE` 仍可以是 DVM=true 的真实 policy proposal；不能因 action id 是 noop 而归类
forced。rejected proposal 的 policy mask/DVM 仍为 true，且 PPO stored action/log-prob
不得被 effective assignment 覆盖。

actor evaluation/loss/sequential factor 与 resolver 都不得按 storage presence 选择样本。
resolver 只能消费 `policy_proposal_present_mask=true` 且 generation 匹配的 rows；forced 和
terminal rows 永不成为 proposal、rejection attribution 或 component member。

### 11.7 Component request/result

每个 component 使用单-env typed DTO，避免 ragged universal dict。

Canonical rejection enum：

```text
ComponentRejectionReason(str, Enum):
  NONE = "none"
  CONTENTION_LOSS = "contention_loss"
  INCOMPLETE_TRANSFER_CHAIN = "incomplete_transfer_chain"
  OWNERSHIP_COORDINATION_INVALID = "ownership_coordination_invalid"
  PREEMPTION_INELIGIBLE = "preemption_ineligible"
  ASSIGNED_UNFINISHED_COUNT_DECREASE = "assigned_unfinished_count_decrease"
  PAIR_IMPROVEMENT_NOT_MET = "pair_improvement_not_met"
  COMPONENT_IMPROVEMENT_NOT_MET = "component_improvement_not_met"
  LOCAL_SET_OVERFLOW_FAIL_CLOSED = "local_set_overflow_fail_closed"
  POST_SNAPSHOT_SYSTEM_INVALIDATION = "post_snapshot_system_invalidation"
  TERMINAL_TRANSITION = "terminal_transition"
```

若一个未 mutation component 同时失败多个 ordinary gate，canonical reason 按上表从上到下
选择第一个；完整失败集合另存 immutable
`all_rejection_reasons: tuple[ComponentRejectionReason, ...]`。historical mask
非法、generation/token mismatch、duplicate ownership in `a0` 或 staged half-mutation
属于 implementation invariant error，直接 fail-fast，不伪装成 ordinary policy rejection。

默认 attribution：

- 前七个非 `NONE` reason 只有在 snapshot facts 未变化、proposal 曾被 historical mask
  允许且 failure 可由 joint policy outcome 导致时，才
  `policy_caused=true, penalty_eligible=true`；
- overflow、post-snapshot invalidation、terminal 均
  `policy_caused=false, penalty_eligible=false`；
- `penalty_unit_count` 只能是 0/1，并与 `penalty_eligible` 精确一致。

Request 至少包含：

```text
component_id
member_robot_mask [M]
member_task_mask [N]
baseline_assignment_a0 [M]
baseline_ownership_a0 [N]
proposed_task_id [M]
proposal_kind [M]
policy_proposal_present_mask [M]
task_state [N]
robot_state [M]
pair_legal_mask [M,N]
nominal_cost [M,N]
threshold/penalty parameter specs
```

Result 至少包含：

```text
accepted
rejection_reason
all_rejection_reasons
proposal_accepted [M]
effective_assignment [M]
effective_ownership [N]
owner_change_mask [N]
assigned_count_before/after
local_cost_before/after
transfer_count
```

`proposal_accepted [M]` 只在 request 的 `policy_proposal_present_mask=true` rows 上有
policy meaning；其他 rows 必须由独立 validity mask/typed N/A 表示，禁止把 forced
placeholder 计作 accepted 或 rejected proposal。

Rejection record：

```text
component_id
reason
policy_caused
penalty_eligible
penalty_unit_count  # exactly 1 iff eligible, else 0
member_robot_ids
member_task_ids
```

Phase A 不构图、不仲裁、不计算 objective、不 commit。

---

## 12. Scenario parse/apply propagation

目标调用链：

```text
scenario declarations
→ canonical raw profile
→ conditional env_cfg apply
→ merge/assert all formal raw sources after Hydra compose
→ one process-local discriminated ResolvedAssignmentProfile
→ exact runtime dispatcher
→ wrapper identity
→ manifest/checkpoint validator
→ playback identity
```

实施规则：

1. `scenario_config.py` 只持有/消费 ordered primitive string choices，不导入 identity-bearing
   contract；post-bootstrap canonical resolver 对 vocabulary 做 ordered equality check；
2. 顶层/nested conflict fail-fast；
3. absent profile 不调用 `setattr`，保持 current default and serialization；
4. explicit profile 只写 canonical string；
5. 不把 resolved dataclass 写进 env cfg/`env_args`；
6. Hydra compose + scenario apply 后 resolve identity exactly once；
7. train entrypoint 以显式参数把 identity 传给 repo-local runner；
8. runner 把同一 object 传给 `AssignmentIsaacLabEnv` 和 wrapper；
9. playback main 把同一 object 传给 wrapper、initial-condition adapter 和 manifest；
10. wrapper assert canonical class identity 与 raw cfg/name 一致；existing subtype 才能进入
    old boolean/Contract C consumer；
11. save/load/playback validator 从 wrapper identity 取值，不再自行 normalize。

`event_gated_local_mrta` 在 Phase A：

- scenario parse/validate：允许；
- in-memory v3 interface semantic descriptor：允许；
- env construction、runner construction、actor construction、checkpoint I/O、play loop：
  `PhaseAExecutionNotAuthorizedError`。

formal entrypoint 分两层，但只 resolve final identity 一次：

1. AppLauncher 前，`RawProfilePreflight` 只用 import-free primitive strings 检查
   scenario/parser/raw Hydra token 中已经可见的 declaration；如果明确为 event profile，
   用 built-in error + stable code 立即拒绝。它不导入 canonical contract，也不创建
   `ResolvedAssignmentProfile`；
2. Hydra compose 后、任何 output-dir/env/runner/actor/checkpoint/file creation 前，合并
   env cfg 与 scenario raw sources；在 `import isaaclab_tasks` 后从完整 package path 导入
   canonical types，先核对 primitive/canonical vocabulary，再执行 conflict/prerequisite
   validation 并 resolve final identity exactly once。Hydra-only event profile 在这里
   拒绝；AppLauncher 已启动这一事实必须在 diagnostic/error 中明确，不能伪称 prelaunch
   identity evidence。

这样 preflight 与 final resolution 不共享/重复 identity object，也不共享 identity-bearing
module；它们只以 ordered primitive vocabulary 建立可检查的一致性。formal consumers 只收到
post-bootstrap final canonical object。

当前 `smoke_defaults_from_config()` runtime consumers 的 A1 inventory 必须覆盖：

```text
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/diagnose_assignment_controller_feasibility.py
```

五个 entrypoint 都执行 prelaunch-visible raw check；前三个 assignment RL/checkpoint
entrypoint 再在 Hydra-composed main 的第一条有副作用语句之前执行 final resolution/
readiness guard。后两个非 event-gated baseline/diagnostic entrypoint 对
`event_gated_local_mrta` 给 typed unsupported-route error，且不得先创建环境或文件。
Hydra-only value 只能保证 post-AppLauncher、pre-side-effect rejection。三个 AppLauncher
smoke tests 和 training-readiness test 是 test-only consumers；
它们不成为 production dispatch authority，且 Phase A 不运行其 AppLauncher paths。

---

## 13. Checkpoint v2/v3 semantic dispatch

### 13.1 Files and type boundary

保留不扩宽：

```text
assignment_checkpoint_contract.py
  AssignmentCheckpointContractManifest
  MANIFEST_FORMAT_VERSION = assignment_checkpoint_contract_v2
  v2 canonical_manifest_bytes/fingerprint/evaluate_compatibility
```

新增：

```text
assignment_checkpoint_contract_v3.py
assignment_checkpoint_semantic_dispatch.py
```

exact v3 version：

```text
assignment_checkpoint_contract_v3
```

### 13.2 V3 strict sections

**Status:** `[PHASE-A-PROPOSED-FOR-APPROVAL]`

| Section | Required semantic bindings |
|---|---|
| `identity` | exact `ResolvedEventGatedAssignmentProfile` variant/discriminant；`event_gated_target_semantics`；profile/version/semantic family；no old runtime bool or legacy mapping keys |
| `scale` | fixed `M/N`, ordered robots |
| `actor_schema` | global fixed observation schema/dim/order |
| `shared_schema` | centralized global schema/dim/order |
| `action_contract` | global IDs `0..N-1`, noop `N`, decoded `-1`, CONTINUE rule；storage/policy/forced/DVM four-mask truth table |
| `transition_contract` | facts/result schema；pre-reset capture；generation/token；`ENV_EXECUTION_FACTS_PRODUCER_V1` distinct from `LIFECYCLE_AUTHORITY_V1`；pair-attribution invariants；observable alias-isolation/mutation-detection contract |
| `event_tick_contract` | seven-value lifecycle event schema；separate retry opportunity schema；separate three-value resolver diagnostic schema；typed placement/trigger suppression |
| `local_candidate_contract` | seeds; one owner expansion; merge; caps/overflow; Top-K/current retention |
| `cost_path_contract` | expected-time units; nav+alignment; pair matrix; explicit path mask |
| `decision_valid_training_contract` | DVM definition；`policy_proposal_present_mask == DVM`；forced storage is not proposal；subset sampling；valid-only loss/entropy/advantage；zero/singleton |
| `sequential_factor_contract` | `[T,E,1]`; `torch.where`; nondecision 1; zero-valid skip |
| `component_contract` | closure; pair/component gates; whole accept/reject; transfer counting; atomic commit |
| `reward_contract` | wrapper-final mean; component-once penalty; broadcast; raw diagnostic only |
| `failure_termination_contract` | permanent failed pair; cumulative state; `TEAM_INFEASIBLE`; reason priority |
| `diagnostics_contract` | typed versions；facts producer/lifecycle authority；three disjoint record streams；storage/policy/forced proposal/effective attribution |
| `policy_sequence_contract` | HAPPO；EP；`share_param=false`；both recurrent flags false；`feed_forward_generator_actor`；repo-local future event runner；installed HARL read-only |
| `model_structure` | actor/critic/distribution structure |
| `training_contract` | state-dict；`save_entire_model=false`；standard GAE；ValueNorm return source；optimizer/rollout fixed-step contract |
| `runtime_readiness_contract` | Phase A interface-only or later fully verified gate |

V3 `identity` exact-key validator 必须拒绝 event subtype 中出现：

```text
event_gate_enabled
resolver_enabled
lifecycle_observation_enabled
lifecycle_mask_enabled
to_legacy_wrapper_mapping
```

`transition_contract` 绑定的是 externally observable
`frozen metadata + no public writable alias + supported-path mutation detection` 行为，以及
exact pair-attribution invariant contract；它禁止 `_version`、storage identity、private
field layout、detector name 或具体 digest/backing mechanism 成为 semantic key/checkpoint
compatibility condition。替换 detector 不改变 descriptor fingerprint。

`event_tick_contract` 分别保存三套 schema/type identity 和 placement rule；禁止把 retry 或
resolver diagnostic 编码回 `LifecycleEventType`。`action_contract`/DVM contract 分别绑定
fixed storage row 与真实 policy proposal；resolver gate exact 为
`policy_proposal_present_mask=true`。

V3 有一个 version string、两个 exact artifact kinds：

```text
manifest_format_version:
  assignment_checkpoint_contract_v3

manifest_kind:
  interface_semantic_descriptor
  checkpoint_ready_manifest
```

Phase A 只能构造、parse、canonicalize 和 fingerprint
`interface_semantic_descriptor`。它允许 numeric parameter 以 typed
`UnresolvedParameterSpec(name, owner_phase)` 出现，只允许 purpose
`INTERFACE_AUDIT`，不得与 weight directory 配对。

`checkpoint_ready_manifest` 使用同一 exact section schema，但要求所有 parameter concrete、
`runtime_readiness=verified` 和 later-phase evidence IDs 齐全。Phase A builder 必须拒绝创建
它；save/load/playback 也必须拒绝 interface descriptor。因而本文的 “v3 fingerprint”
默认指 interface semantic descriptor fingerprint，不表示已有可加载 checkpoint。

Top-level exact keys/order 为：

```text
manifest_format_version
manifest_kind
identity
scale
actor_schema
shared_schema
action_contract
transition_contract
event_tick_contract
local_candidate_contract
cost_path_contract
decision_valid_training_contract
sequential_factor_contract
component_contract
reward_contract
failure_termination_contract
diagnostics_contract
policy_sequence_contract
model_structure
training_contract
runtime_readiness_contract
```

每个 section 用 dedicated frozen typed dataclass，不接受 free-form nested dict 或 unknown
key。上表的 semantic bindings 是 A3/A4 代码 schema 的最小 exact key set；A4 review
package 必须附生成的 key/type inventory，任何 inventory 未经 review 改变都使 descriptor
fingerprint 改变并阻止 A4 closeout。

所有 threshold/cap/rejection scales 在 checkpoint-ready v3 中必须为 concrete canonical
decimal/int。`[NUMERIC-TBD]` 可以存在于 Phase A config spec，但
`build_checkpoint_ready_v3()` 必须拒绝 unresolved parameter。

### 13.3 Dispatcher

`assignment_checkpoint_semantic_dispatch.py` 只读取顶层
`manifest_format_version` 后分派。这个函数只接收**已经存在的 manifest mapping**：

```text
v2
→ exact current AssignmentCheckpointContractManifest.from_mapping()
→ exact current canonical bytes/fingerprint/evaluate_compatibility()

v3
→ strict AssignmentCheckpointContractManifestV3
→ strict v3 canonical bytes/fingerprint/evaluator

present mapping with other/missing manifest_format_version
→ UnsupportedCheckpointManifestVersionError
```

manifest/fingerprint metadata pair **整体不存在**不是上面的 “missing”。loader 必须继续走
current `decide_missing_metadata()` / `_legacy_load()` narrow path，并逐项保留：

```text
explicit_unversioned_legacy_fallback == true
current resolved profile == legacy
current resolver disabled
current purpose is one already allowed by v2 decision
current actor_dim == 909
current action_dim == 51
current noop_id == 50
all existing actor-file inventory guards
```

未显式请求 fallback、非 legacy、metadata pair 不完整、或 event-gated profile 均在任何
`torch.load` 前拒绝。dispatcher 不把 metadata-free checkpoint 自动包装成 v2。

Generic facade：

```text
parse_assignment_checkpoint_manifest()
canonical_assignment_checkpoint_manifest_bytes()
compute_assignment_checkpoint_manifest_sha256()
evaluate_assignment_checkpoint_semantics()
```

### 13.4 Compatibility matrix

| Current profile/family | Checkpoint | Result |
|---|---|---|
| exact legacy v2 | exact legacy v2 | current v2 decision unchanged |
| exact Contract C v2 | exact Contract C v2 | current v2 decision unchanged |
| lifecycle ablation explicit target | allowed named Contract C→ablation case only | current v2 named-ablation decision |
| diagnostics profile | native training checkpoint | current blocked behavior |
| exact legacy + metadata pair absent + explicit current fallback | unversioned legacy files | exact current `decide_missing_metadata()` result |
| exact legacy + metadata pair absent + no explicit fallback | unversioned files | exact current rejection |
| Contract C/ablation/diagnostics + metadata absent | unversioned files | exact current rejection |
| legacy/Contract C | v3 | `semantic_family_mismatch` |
| event-gated v3 | any v2 | `semantic_family_mismatch`, even equal shapes |
| event-gated profile | metadata-free/unversioned | reject before tensor I/O regardless fallback flag |
| event-gated v3 | different v3 fingerprint/semantics | exact mismatch |
| event-gated v3 Phase-A readiness | any weight I/O purpose | `runtime_not_ready` |

错误必须包含：

```text
expected_profile
actual_profile
expected_family/version
actual_family/version
purpose
classification
```

无 conversion、无 silent fallback、无 shape-only compatibility。

### 13.5 Shared validator integration

后续 A4 只做 minimal interface routing：

- `assignment_checkpoint_save.py`：old builder 仍直接产生 v2；metadata pair parser
  使用 dispatcher；v3 weight save readiness-blocked；
- `assignment_checkpoint_load.py`：在任何 `torch.load/load_state_dict` 前用 dispatcher；
- `assignment_harl_training.py`：old profile 继续 old v2 builder；
- `play_assignment.py`：old profile 继续 current load；event profile actor/checkpoint 前 block；
- `evaluate_assignment_rl_playback_diagnostics.py`：相同 guard/validator；
- `assignment_training_run_audit.py`：v2 audit logic 完全保留；只在入口识别 v3 并返回
  typed `event_gated_v3_audit_not_ready_in_phase_a`，不复用 v2 field-path checks；
- `assignment_initial_condition.py`：Phase A 不改 frozen Contract C interface，旧 route 仍传
  canonical profile name。

### 13.6 Phase A manifest-only proof

允许：

- in-memory `interface_semantic_descriptor` mapping；
- canonical UTF-8 JSON bytes；
- SHA-256；
- parser exact-key tests；
- v2 direct-vs-dispatched byte/hash equality；
- cross-version mismatch；
- checkpoint-ready builder/readiness rejection；
- spy 证明 mismatch 发生在 any tensor loader 前。

禁止：

- 读取 checkpoint directory；
- `torch.load`；
- weights conversion；
- actor/critic mutation；
- real save/load/playback。

---

## 14. Team reward semantic config and assertions

计划新增：

```text
assignment_team_reward_contract.py
```

`TeamRewardContractSpec` exact fields：

| Field | Semantic value |
|---|---|
| `schema_version` | `event_gated_team_reward_contract_v1` |
| `wrapper_reward_source` | `AssignmentHarlWrapper.final_reward` |
| `base_reducer` | `mean_over_robot_axis` |
| `penalty_order` | `after_mean_before_broadcast` |
| `penalty_unit` | `once_per_penalty_eligible_rejected_component` |
| `broadcast_mode` | `identical_all_agents` |
| `critic_reward_source` | `broadcast_team_reward` |
| `valuenorm_source` | all physical-step critic returns |
| `raw_per_agent_usage` | diagnostics only |
| `rejection_penalty_scale` | required numeric parameter spec; unresolved in Phase A |
| `base_env_reward_contract` | ordered current env reward scale identity |
| `wrapper_shaping_contract` | ordered current wrapper shaping config identity |

冻结顺序：

```text
base_team_reward[e]
= mean_i(wrapper_final_reward[e,i])

team_reward[e]
= base_team_reward[e]
 - rejection_penalty_scale
 * policy_rejected_component_count[e]

learner_reward[e,i]
= team_reward[e]
```

Phase A：

- 只定义 config/spec、canonical mapping、unresolved-parameter gate；
- pure scalar/tensor oracle 可用于 formula-order assertion，但不接 env/runner；
- v3 fingerprint 绑定完整 resolved contract；
- old profile 不创建该 config、不改变 reward/log whitelist；
- 不把 raw decomposition 送入 learner。

Phase D 才修改 runtime reward、critic input、proper-time-limit info 和 equality diagnostics。

---

## 15. Structured diagnostics

计划新增：

```text
assignment_event_gated_diagnostics_contract.py
```

不使用 universal payload dict。定义：

```text
DiagnosticEnvelope
ProfileRouteDiagnostic
TransitionAuthorityDiagnostic
AssignmentTickDiagnostic
ProposalResolutionDiagnostic
ActorUpdateDiagnostic
TeamRewardDiagnostic
CheckpointSemanticDiagnostic
DefaultOffIdentityDiagnostic
```

Envelope 只含 schema/kind/profile/generation 和 typed payload。Phase A 没有 runtime sink；
old route `sink=None`，不新增 info key、TensorBoard key、CSV/JSONL 或目录。

### 15.1 Field ownership

| Diagnostic field | First producer phase | Correctness priority |
|---|---|---|
| resolved profile/runtime route | A static; runtime assertion later | required |
| assignment tick count | B | required |
| per-robot decision count | B/C | required |
| DVM true sample count | C | required |
| skipped actor/minibatch count | C | required |
| claim/continue/switch proposal count | B/C | required |
| accepted/rejected component count | B | required |
| rejection reason/penalty eligible | B/D | required |
| transfer component size | B | paper + correctness |
| ownership transfer count | B | required |
| local cost before/after | B | paper + correctness |
| `NEEDS_ASSIGNMENT` duration | B0/B | paper + correctness |
| idle-with-available-task | B | required |
| failed-pair count | B0 | required |
| `TEAM_INFEASIBLE` count | B0 | required |
| termination reason | B0/D | required |
| lifecycle event/opportunity source and trigger eligibility | B0/B | required |
| resolver diagnostic `trigger_eligible=false` and suppression | B | required |
| facts generation/consume | B0 | required |
| facts producer/lifecycle authority/result match | B0 | required |
| proposal/effective mismatch | B | required |
| component accept/reject | B | required |
| team reward broadcast equality | D | required |
| checkpoint semantic version | A static; runtime later | required |
| default-off route identity | A static | required |
| local-set size distribution/margins | B/E | paper |
| fairness/latency breakdown | D/E | optional later |

Phase A DTO 中每个尚未有 producer 的 field 必须标
`availability=DEFINED_NOT_PRODUCED`，不能填 0 冒充 runtime measurement。

### 15.2 Exact envelope and typed payload fields

```text
DiagnosticAvailability(str, Enum):
  PRODUCED = "produced"
  DEFINED_NOT_PRODUCED = "defined_not_produced"
  NOT_APPLICABLE = "not_applicable"

DiagnosticKind(str, Enum):
  PROFILE_ROUTE
  TRANSITION_AUTHORITY
  ASSIGNMENT_TICK
  PROPOSAL_RESOLUTION
  ACTOR_UPDATE
  TEAM_REWARD
  CHECKPOINT_SEMANTIC
  DEFAULT_OFF_IDENTITY

TransitionConsumeStatus(str, Enum):
  FIRST_CONSUME
  DUPLICATE
  STALE
  FUTURE
  MISMATCH

DefaultOffCohort(str, Enum):
  D0_ABSENT
  D1_PRE_RESOLVED_VALID
  SCENARIO_CORRECTION
```

`DiagnosticEnvelope` exact fields：

| Field | Type |
|---|---|
| `schema_version` | exact `event_gated_diagnostic_envelope_v1` |
| `kind` | `DiagnosticKind` |
| `resolved_profile` | `AssignmentProfileName` |
| `env_id` | `int` |
| `episode_generation` | `int` |
| `transition_generation` | `int` |
| `assignment_tick_generation` | `int`；`-1` if not applicable |
| `availability` | `DiagnosticAvailability` |
| `payload` | one exact payload dataclass below |

Payload exact fields：

```text
ProfileRouteDiagnostic(
  profile_contract_version: str,
  resolved_variant: str,  # existing or event_gated
  runtime_route: str,
  checkpoint_family: str,
  runtime_readiness: str,
  resolution_origin: str,
  event_target_semantics_contract_version: str | None,
)

TransitionAuthorityDiagnostic(
  facts_schema_version: str,
  result_schema_version: str,
  facts_producer_id: str,
  lifecycle_authority_id: str,
  consume_token: int,
  receipt_id: int,
  consume_status: TransitionConsumeStatus,
  generation_match: bool,
  facts_producer_match: bool,
  lifecycle_authority_match: bool,
  pair_attribution_contract_version: str,
  pair_attribution_validated: bool,
  observable_immutability_contract_version: str,
)

AssignmentTickDiagnostic(
  assignment_tick_count: int,
  lifecycle_event_ids: tuple[str, ...],
  lifecycle_causal_sources: tuple[LifecycleCausalSource, ...],
  assignment_opportunity_ids: tuple[str, ...],
  assignment_opportunity_types: tuple[AssignmentOpportunityType, ...],
  trigger_eligible_count: int,
  resolver_diagnostic_count: int,
  suppressed_resolver_diagnostic_trigger_count: int,
  local_robot_count: int,
  local_task_count: int,
  per_robot_decision_count: tuple[int, ...],     # length M
  decision_valid_count: int,
  policy_proposal_count_by_kind: tuple[int, ...],# ProposalKind enum order
  forced_storage_row_count: int,
  accepted_component_count: int,
  rejected_component_count: int,
  ownership_transfer_count: int,
  needs_assignment_duration: tuple[int, ...],   # length M
  idle_with_available_task_count: int,
  failed_pair_count: int,
  team_infeasible_task_count: int,
  termination_reason: TerminationReason,
)

ProposalResolutionDiagnostic(
  robot_id: int,
  storage_row_present: bool,
  policy_proposal_present: bool,
  forced_nondecision: bool,
  decision_valid: bool,
  stored_row_kind: StoredActionRowKind,
  proposal_kind: ProposalKind | None,
  stored_action_id: int,
  proposed_task_id: int,
  effective_assignment: int,
  proposal_accepted: bool | None,
  proposal_effective_mismatch: bool | None,
  component_id: str,
  component_size: int,
  rejection_reason: ComponentRejectionReason,
  policy_caused: bool,
  penalty_eligible: bool,
  ownership_transfer_count: int,
  local_cost_before: float,
  local_cost_after: float,
)

ActorUpdateDiagnostic(
  actor_id: int,
  decision_valid_sample_count: int,
  skipped_actor_update_count: int,
  skipped_minibatch_count: int,
  singleton_advantage_fallback_count: int,
  nondecision_factor_identity_violation_count: int,
  reduction_denominator: int,
)

TeamRewardDiagnostic(
  wrapper_final_reward_mean: float,
  policy_rejected_component_count: int,
  rejection_penalty_scale: float,
  team_reward: float,
  broadcast_agent_count: int,
  broadcast_equal: bool,
)

CheckpointSemanticDiagnostic(
  manifest_format_version: str,
  manifest_kind: str,
  profile_name: str,
  checkpoint_family: str,
  fingerprint_sha256: str,
  purpose: str,
  compatibility_classification: str,
  runtime_readiness: str,
)

DefaultOffIdentityDiagnostic(
  cohort: DefaultOffCohort,
  surface: str,
  evidence_label: str,
  expected_digest: str | None,
  actual_digest: str | None,
  matched: bool,
  deferred_reason: str | None,
)
```

`proposal_accepted`/mismatch 只有在 `policy_proposal_present=true` 时非 `None`；
forced/terminal storage 不能伪造 accepted/rejected result。diagnostics 只暴露 observable
immutability contract version/status，不记录 `_version`、storage identity 或 detector
implementation。

这些 payload 是 summary/diagnostic CPU representation：整数是 Python `int`、数值是 finite
Python `float`、per-robot vector 是 fixed-length immutable tuple；不持有 live tensor
alias。`DEFINED_NOT_PRODUCED` 时 payload 不构造，envelope 只记录 kind/profile/generation
和 availability，避免使用 sentinel 0 伪造 measurement。

---

## 16. Exact file-level change plan

本节使用以下唯一、可机械展开的 repo-relative roots；表内不带目录的
`assignment_*.py` 均位于 `<TASK_SRC>`，不带目录的 `test_*.py` 和
`evaluate_*.py` 均位于 `<TEST_ROOT>`：

```text
<TASK_SRC>
= source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator

<TEST_ROOT>
= scripts/environments

<AGENTREAD>
= source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead
```

`<IMPLEMENTATION_YYYYMMDD>` 在 A6 当日按 `AGENTS.md` 解析为唯一八位本地日期；它是
未来 handoff 文档的 date-folder placeholder，不是多个候选路径。

### 16.1 Planned additions

| File | Add/Modify | Phase A responsibility | Explicit non-responsibility | Runtime risk |
|---|---|---|---|---|
| `assignment_profile_contract.py` | Add | canonical enum/exceptions；discriminated existing/event resolved family；dispatcher；canonical-name guard | no bare fallback/env/runner execution | medium |
| `assignment_lifecycle_transition_contract.py` | Add | facts producer/result authority/token/ledger/observable immutability/pair assertions | no pre-reset hook/authority placement/runtime | low |
| `assignment_event_contract.py` | Add | three disjoint lifecycle/opportunity/resolver-diagnostic type+record systems | no event production/scheduling/resolver | low |
| `assignment_mrta_contract.py` | Add | cost/local/Top-K/DVM/four-mask proposal/component DTO | no algorithm/resolver | low |
| `assignment_checkpoint_contract_v3.py` | Add | strict event-subtype v3 manifest/parser/canonical bytes；behavioral contract only | no checkpoint weights/detector details | medium |
| `assignment_checkpoint_semantic_dispatch.py` | Add | exact v2/v3 version facade under canonical key | no conversion/load/bare fallback | high |
| `assignment_team_reward_contract.py` | Add | reward spec/canonical assertions | no runtime reduction | low |
| `assignment_event_gated_diagnostics_contract.py` | Add | typed diagnostic schemas | no logger/sink/output | low |
| `test_assignment_profile_contract.py` | Add | profile/union/route + canonical module/type identity/AST/clean-child regressions | no package bootstrap/env | low |
| `test_assignment_lifecycle_transition_contract.py` | Add | schema/producer/authority/generation/token/pair-invariant/behavioral immutability tests | no hook | low |
| `test_assignment_event_gated_mrta_contract.py` | Add | three record systems；DTO/global-ID/DVM/four-mask/resolver-gate validation | no algorithm | low |
| `test_assignment_checkpoint_semantic_dispatch.py` | Add | v2 golden/v3/cross-version manifest tests | no checkpoint load | medium |
| `test_assignment_team_reward_contract.py` | Add | formula/config/unresolved tests | no reward runtime | low |
| `test_assignment_event_gated_diagnostics_contract.py` | Add | typed serialization/phase availability | no files | low |
| `test_assignment_phase_a_default_off_identity.py` | Add | legacy/Contract C identity closeout | no Isaac/training | high |

因此例如 `assignment_profile_contract.py` 的 exact path 是
`<TASK_SRC>/assignment_profile_contract.py`，而
`test_assignment_profile_contract.py` 的 exact path 是
`<TEST_ROOT>/test_assignment_profile_contract.py`。

所有 A1–A5 identity-bearing addition 均受 §7.3 的 package-qualified canonical-key、
early `__name__` guard、no-bare-fallback 和 no-`sys.modules`-alias 规则约束；这不是只对
profile module 的一次性测试。

### 16.2 Planned modifications

| File | Add/Modify | Phase A responsibility | Explicit non-responsibility | Runtime risk |
|---|---|---|---|---|
| `scenario_config.py` | Modify | primitive ordered vocabulary/raw provenance；conflict check；conditional profile apply | no contract-type import/numeric runtime config | medium |
| `assignment_harl_wrapper.py` | Modify | package-relative canonical consumer；same-object/class assert；existing-only old mapping；event fail-closed | no reconstruction/bare fallback/step/reward/mask/resolver changes | high |
| `assignment_lifecycle_training_contract.py` | Modify | package-relative identity consumer；exhaustive discriminated route | no string re-resolution/HAPPO behavior | medium |
| `assignment_harl_training.py` | Modify | pass same identity/class；old runner direct；event early block | no buffer/collect/train or `_assert_available_actions()` change | high |
| `scripts/reinforcement_learning/harl/train.py` | Modify | primitive preflight；post-bootstrap full-path canonical resolve/pass once | no prelaunch contract import/training execution change for old profile | high |
| `assignment_checkpoint_save.py` | Modify | dispatcher parsing; identity assertion; v2 exact branch | no v3 weight save | high |
| `assignment_checkpoint_load.py` | Modify | shared version validator before tensor I/O | no checkpoint load in Phase A tests | high |
| `assignment_training_run_audit.py` | Modify | preserve v2 audit；typed Phase-A-not-ready classification for v3 | no generic v3 field audit/run mutation | medium |
| `scripts/reinforcement_learning/harl/play_assignment.py` | Modify | primitive preflight；post-bootstrap full-path identity；Phase-A event block | no prelaunch contract import/DVM inference/playback change | high |
| `evaluate_assignment_rl_playback_diagnostics.py` | Modify | primitive preflight；post-bootstrap canonical version validator | no prelaunch contract import/evaluation execution change | high |
| `evaluate_assignment_methods.py` | Modify | primitive preflight；post-bootstrap typed unsupported route | no prelaunch contract import/baseline algorithm change | medium |
| `diagnose_assignment_controller_feasibility.py` | Modify | primitive preflight；post-bootstrap typed unsupported route | no prelaunch contract import/controller diagnostic change | medium |
| `<AGENTREAD>/<IMPLEMENTATION_YYYYMMDD>/PHASE_A_PURE_INTERFACE_IDENTITY_DIAGNOSTICS_IMPLEMENTATION_REPORT.md` | Add in A6 | evidence/result handoff | no runtime claim beyond executed evidence | low |
| `<AGENTREAD>/TASK_PROGRESS.md` | Modify in A6 | concise Phase A closeout and next gate | no historical log duplication | low |

### 16.3 Explicit no-change files in Phase A

| File/path | Reason |
|---|---|
| `assignment_checkpoint_contract.py` | v2 class/parser/canonical bytes/fingerprint stay byte-exact |
| `scan_mobile_manipulator_env.py` | existing raw selector default remains; pre-reset/runtime belongs B0 |
| `assignment_state.py` | target enums stay pure contract; current runtime states unchanged |
| `assignment_lifecycle_observation.py` | current Contract C tensors remain exact |
| `assignment_lifecycle_resolver.py` | current resolver behavior remains exact |
| `assignment_lifecycle_resolver_runtime.py` | no component/event-gated runtime |
| `assignment_lifecycle_diagnostics.py` | current default-off prototype output remains exact |
| `assignment_playback_attribution_diagnostics.py` | current playback diagnostics unchanged |
| `assignment_initial_condition.py` | frozen Contract C interface not broadened |
| `agents/harl_happo_cfg.yaml` and all YAML | no config/runtime parameter edit |
| installed `harl/**` | read-only; C uses repo-local subclass |

如果 A1–A6 任何切片需要修改这些 runtime files 的行为，则停止并重新审核 phase ownership。

---

## 17. Commit-style implementation slices

“Commit-style”只表示 review boundary；未获单独授权时不 commit。

### A1 — Profile identity and direct dispatcher

A1 仍是一个 phase gate，但分成三个串行 review package；每个 package 完成后停止：

```text
A1a pure registry/resolved identity
→ A1b scenario propagation + current prerequisite assertions
→ A1c production-entrypoint readiness guards
```

Prerequisite：

- clean worktree；
- record current old-profile mapping/order；
- no tracked scenario lifecycle config。

Files：

- add `assignment_profile_contract.py`；
- modify scenario/wrapper/training contract/training entry/play entry；
- modify the three `scripts/environments/` runtime consumers enumerated in §12；
- add `test_assignment_profile_contract.py`。

Work：

- central enum/normalizer/discriminated existing/event family/exhaustive matrix；
- enforce one source file → one canonical production module key；no bare fallback or alias；
- keep prelaunch checks primitive-only；canonical import/typed resolution post-bootstrap only；
- add fifth profile；
- conditional parse/apply；
- pass one identity without serializing it；
- old profile exact branches；
- event profile Phase-A fail-closed。

Tests：

- five-profile matrix；
- event subtype has no `event_gate_enabled`/old runtime booleans or legacy mapping method，
  cannot enter existing boolean/Contract C consumer，and its canonical mapping excludes those
  keys；
- top/nested same/conflict/empty/unknown；
- absent config no mutation；
- exact old wrapper dict/order；
- exact current legacy/ablation/Contract-C/diagnostics prerequisite matrix；
- event HAPPO/EP/feed-forward/`share_param=false`/state-dict matrix；
- dispatcher spy/call count；
- canonical `__module__` for public enum, both resolved dataclasses and exceptions；
- producer class `is` consumer class；enum/dataclass/exception identity equality；strict
  `isinstance` remains valid；
- AST rejects bare imports、relative→bare fallback、prelaunch contract imports and
  `sys.modules` aliases；
- clean-child duplicate-source/different-key audit；canonical key is the sole key；historical
  initial-condition duplicate-module failure is reproduced then rejected；
- primitive prelaunch vocabulary ordered-equals post-bootstrap registry；
- prelaunch-visible event profile fails before AppLauncher；Hydra-only event profile fails
  post-AppLauncher but before output-dir/env/runner/actor/checkpoint/file creation at every
  §12 production consumer；
- old training blocked/allowed states unchanged。

A1a owns profile-contract canonical-key/type/no-bare-fallback/clean-child tests and can close
pure module identity。A1b owns `scenario_config.py` primitive-only AST and
primitive-vocabulary ordered-equality gates。A1c owns formal-entrypoint prelaunch ordering and
entrypoint → wrapper same-object/same-class positive assertions after real wiring；A1a 不得用
unused production import 伪造 later-package gate。保留
`test_assignment_initial_condition_contract.py --json` 作为历史故障模式 regression。

Done gate：

```text
legacy and Contract C route exact
ablation/diagnostics blocked semantics exact
event route never reaches runtime
event subtype cannot reach old boolean consumer
one source file has one canonical production module key
```

“route exact”只适用于 §18 cohort D0/D1；explicit scenario propagation correction 单独
验收，不能用 current ignored-scenario bytes 作 expected。

### A2 — Transition schemas and authority identity

Prerequisite：A1 pass。

Files：

- add `assignment_lifecycle_transition_contract.py`；
- add transition pure test。

Work：

- exact schemas/enums；
- private tensor storage；
- atomic per-env ledger/receipt；
- distinct execution-facts producer and lifecycle-authority stamps；
- pair-attributed raw-signal assertions and authoritative task-level result derivation contract；
- result factory/authority stamp；B0 runtime placement remains undecided；
- schema descriptors。

Tests：

- all shapes/dtypes/devices；
- no implicit move/cast；
- required failure matrix；
- source/accessor/internal mutation；
- token batch atomicity；
- producer/receipt/authority/result exact binding and wrong-producer/wrong-authority cases；
- completion cardinality/pair mutual exclusion/owner-match/availability-edge/completed-task
  ownership assertions；
- detector-specific private keys absent from the A2 public transition/schema descriptor；
- raw derived-field rejection。

Done gate：supported-path alias isolation/mutation detection and consume-once are demonstrated
without environment integration；no absolute storage immutability claim。detector mechanism
remains replaceable implementation detail, not semantic fingerprint identity。

### A3 — Typed Phase A contracts

Prerequisite：A2 pass。

Files：

- add event/MRTA contract modules；
- add diagnostics/reward contract schema modules；
- add DTO/schema pure tests。

Work：

- three disjoint lifecycle-event/opportunity/resolver-diagnostic record systems and placement；
- cost/path contract；
- local/Top-K/DVM/four-mask proposal-storage/component/rejection DTO；
- exact diagnostics payload union and team-reward semantic spec；
- global-ID and raw/decoded action distinction；
- unresolved numeric parameter specs。

Tests：

- valid/invalid shapes/dtypes/device/generation；
- invalid path is mask+NaN, not large sentinel；
- Top-K global IDs/no duplicates/current retention；
- DVM semantic relation/singleton/terminal；
- decision/forced/terminal row truth table；
- proposal/effective namespace separation；forced rows never enter resolver；
- retry/resolver diagnostics rejected from lifecycle result and resolver diagnostics rejected
  from local trigger input；
- component rejection penalty unit 0/1；
- diagnostics/reward canonical mappings are stable before A4。

Done gate：no DTO performs local-set/Top-K/DVM/resolver/reward/logger behavior；A4 所需的
reward/diagnostics schema bytes 已冻结。

### A4 — Checkpoint v2/v3 semantic dispatcher

Prerequisite：A1–A3 pass；capture deterministic v2 golden bytes/hash before edits。

A4 分为：

```text
A4a pure v3 interface descriptor + version dispatcher
→ A4b minimal save/load/playback/offline-audit guards
```

每个 package 完成后停止；A4b 不得扩大成 v3 runtime audit 或 checkpoint I/O。

Files：

- add v3 contract/dispatcher；
- minimal modify save/load/offline audit/playback validator；
- add manifest-only test。

Work：

- preserve v2 class；
- strict v3 interface descriptor；checkpoint-ready builder blocked；
- generic version facade；
- family mismatch before tensor I/O；
- runtime readiness block。

Tests：

- legacy v2 direct vs dispatched canonical bytes/hash；
- Contract C v2 direct vs dispatched canonical bytes/hash；
- all current v2 compatibility classifications unchanged；
- v3 interface descriptor exact keys/fingerprint；identity is event subtype and excludes
  `event_gate_enabled`、old runtime booleans and legacy mapping；
- v3 transition contract includes producer/authority and pair invariants but rejects detector-
  specific `_version`/storage/private-layout/mechanism keys；
- checkpoint-ready v3 builder and weight purposes blocked in Phase A；
- v2↔v3 rejection even equal shapes；
- unknown/missing version；
- metadata pair absent keeps exact explicit legacy fallback decision；no flag/non-legacy/event profile reject；
- offline audit keeps v2 field checks and gives v3 typed Phase-A-not-ready classification；
- spies assert no `torch.load/load_state_dict`；
- unresolved numeric/readiness rejection。

Done gate：any v2 byte/fingerprint/classification drift is a blocker, not an expected update。

### A5 — Diagnostics and reward semantic configuration

Prerequisite：A1–A4 pass。

Files：

- extend the A3 diagnostics/reward pure tests only；no schema-key or v3 mapping change。

Work：

- typed payload union；
- phase availability；
- canonical reward spec/formula order；
- no-op/no-sink old routes；
- verify the A3-frozen v3 semantic mapping without changing it。

Tests：

- exact serialization and unknown-field rejection；
- `DEFINED_NOT_PRODUCED` fields not zero-filled；
- synthetic mean → once-per-component penalty → broadcast；
- broadcast equality assertion；
- unresolved penalty blocks checkpoint-ready v3；
- old route creates no sink/info key/file/RNG call。

Done gate：no runtime logger or reward tensor touched；A4 descriptor fingerprint remains exact。

### A6 — Default-off identity closeout

Prerequisite：A1–A5 pass。

Files：

- add dedicated identity test；
- create Phase A completion report；
- update `TASK_PROGRESS.md`。

Work：

- execute §18/§19 pure/static matrix；
- inventory deferred runtime evidence；
- inspect only Markdown/source/test diffs；
- stop before B0。

Done gate：

```text
pure/static/manifest evidence complete to its declared level
all runtime-only rows remain DEFERRED-RUNTIME-IDENTITY-EVIDENCE
no claim of full runtime identity
```

### 17.1 Dependencies

```text
A1 → A2
A2 → A3
A3 → A4
A4 → A5
A1–A5 → A6
```

该拆分在把 reward/diagnostics **schema** 前移到 A3 后才合理。A4 依赖 A2/A3，因为 v3
必须引用确切 transition/event/MRTA/reward/diagnostics schema；A5 只能做 closeout tests，
不得在 A4 之后再改变 fingerprint。A6 不能提前，B0 不应插入 A2 与 A3 之间。

---

## 18. Default-off identity verification matrix

Evidence labels：

```text
[BYTE/TENSOR-EXACT]
[STATIC-ROUTE-EXACT]
[MANIFEST-EXACT]
[NOT-EXECUTABLE-IN-PHASE-A]
[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]
```

同一 row 可同时有 static proof 和 deferred runtime proof。

### 18.1 Identity cohorts

| Cohort | Input condition | What may be called exact |
|---|---|---|
| `D0_ABSENT` | scenario/profile declaration absent | current implicit `legacy` config serialization、route and side effects |
| `D1_PRE_RESOLVED_VALID` | direct env cfg or complete scenario resolves an existing profile and already satisfies all §7.7 raw prerequisites | downstream existing profile mapping/route/manifest |
| `SCENARIO_CORRECTION` | scenario explicitly declares lifecycle profile that current apply path ignores, or top/nested conflict | intentional A1 parse/apply/validation correction；not HEAD byte/route identity |

`lifecycle_contract_c` exact evidence always means D1 with resolver/cooldown/budget prerequisites already
valid；A1 不自动补这些 fields。`SCENARIO_CORRECTION` 必须用 dedicated expected-change tests，
不能以 `[BYTE/TENSOR-EXACT]` 对比 current buggy ignore/nested-wins behavior。

### 18.2 Legacy and Contract C

下表的 `legacy` 是 D0 或 valid D1；Contract C 是 valid D1。所有 downstream input 在
dispatcher 前保持相同。

| Surface | `legacy` planned evidence | `lifecycle_contract_c` planned evidence | Residual |
|---|---|---|---|
| resolved runtime route | existing class/callable spy `[STATIC-ROUTE-EXACT]` | existing Contract C path/resolver-on `[STATIC-ROUTE-EXACT]` | startup `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| observation | fake-env `torch.equal` `[BYTE/TENSOR-EXACT]` | fake lifecycle snapshot `torch.equal` `[BYTE/TENSOR-EXACT]` | real env `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| shared observation | fake-env `torch.equal` `[BYTE/TENSOR-EXACT]` | fake lifecycle `torch.equal` `[BYTE/TENSOR-EXACT]` | real env `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| action dimension/space | fake-wrapper serialized space/equality `[BYTE/TENSOR-EXACT]` | fake-wrapper serialized space/equality `[BYTE/TENSOR-EXACT]` | real env `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| action mask | old builder `torch.equal` `[BYTE/TENSOR-EXACT]` | Contract C builder `torch.equal` `[BYTE/TENSOR-EXACT]` | real env `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| sampled action | existing actor callable/route spy `[STATIC-ROUTE-EXACT]` | existing actor callable/route spy `[STATIC-ROUTE-EXACT]` | full rollout `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| log-prob | existing evaluator callable/route spy `[STATIC-ROUTE-EXACT]` | existing evaluator callable/route spy `[STATIC-ROUTE-EXACT]` | full rollout `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| proposal | fake-wrapper `torch.equal` `[BYTE/TENSOR-EXACT]` | fake-wrapper `torch.equal` `[BYTE/TENSOR-EXACT]` | rollout `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| effective assignment | disabled-resolver clone `torch.equal` `[BYTE/TENSOR-EXACT]` | current Contract C result `torch.equal` `[BYTE/TENSOR-EXACT]` | real env `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| reward | synthetic wrapper-final `torch.equal` `[BYTE/TENSOR-EXACT]` | synthetic wrapper-final `torch.equal` `[BYTE/TENSOR-EXACT]` | base env `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| GAE/return input | installed critic-buffer callable/branch spy `[STATIC-ROUTE-EXACT]` | same installed branch spy `[STATIC-ROUTE-EXACT]` | update `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| ValueNorm input | current critic-return callable/branch spy `[STATIC-ROUTE-EXACT]` | same branch spy `[STATIC-ROUTE-EXACT]` | update `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| sequential factor | installed HA runner callable/branch spy `[STATIC-ROUTE-EXACT]` | same branch spy `[STATIC-ROUTE-EXACT]` | update `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| RNG path | no new call/field/sink in old route `[STATIC-ROUTE-EXACT]` | no new call/field/sink in old route `[STATIC-ROUTE-EXACT]` | rollout RNG `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| minibatch order | event trainer never selected `[STATIC-ROUTE-EXACT]` | event trainer never selected `[STATIC-ROUTE-EXACT]` | optimizer `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| logger output | no new sink/key + temp-dir bytes/list `[BYTE/TENSOR-EXACT]` | no new sink/key + temp-dir bytes/list `[BYTE/TENSOR-EXACT]` | real run `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| file side effects | D0 absent-profile config clone/file list `[BYTE/TENSOR-EXACT]` | valid-D1 resolved-profile no-new-side-effect spy `[STATIC-ROUTE-EXACT]` | real run `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |
| checkpoint v2 | canonical bytes/SHA `[MANIFEST-EXACT]` | canonical bytes/SHA `[MANIFEST-EXACT]` | no checkpoint load |
| playback route | current all-actor loop spy `[STATIC-ROUTE-EXACT]` | current all-actor loop spy `[STATIC-ROUTE-EXACT]` | actual playback `[NOT-EXECUTABLE-IN-PHASE-A]`; `[DEFERRED-RUNTIME-IDENTITY-EVIDENCE]` |

其中 GAE、ValueNorm、factor、minibatch 行不能仅因为 direct bypass 就标
`[BYTE/TENSOR-EXACT]`；Phase A 不执行 actor update。

### 18.3 Other existing profiles

| Profile | Route identity | Training identity | Checkpoint identity | Phase A proof |
|---|---|---|---|---|
| `lifecycle_ablation` | existing obs/mask ablation route | normal training remains blocked | named Contract C→ablation evaluation semantics only；无 native save | mapping + guard `[STATIC-ROUTE-EXACT]`; applicable v2 decision `[MANIFEST-EXACT]` |
| `diagnostics_hidden_state` | existing diagnostics route/resolver-on | remains blocked | no invented native checkpoint family | mapping + guard `[STATIC-ROUTE-EXACT]`; blocked classification `[MANIFEST-EXACT]`; explicit existing diagnostics side effects only |

不为这两个 profile 发明 v3、native training checkpoint 或新 playback support。

---

## 19. Pure/static test plan

### 19.1 New tests

| Test | Core cases |
|---|---|
| `test_assignment_profile_contract.py` | discriminated family；registry/conflicts/apply/support；canonical `__module__`/class identity；AST and clean-child duplicate-key regression；phase block |
| `test_assignment_lifecycle_transition_contract.py` | schema；facts producer vs lifecycle authority；generation/ledger/receipt；pair-owner/cardinality/mutual-exclusion assertions；observable immutability |
| `test_assignment_event_gated_mrta_contract.py` | three disjoint record placements；cost/path/local/Top-K/DVM；three-row/four-mask proposal truth table；component policy-only gate |
| `test_assignment_checkpoint_semantic_dispatch.py` | v2 golden；strict event-subtype v3；old-bool and detector-private keys rejected；mismatch-before-loader |
| `test_assignment_team_reward_contract.py` | config identity, order, unresolved gate |
| `test_assignment_event_gated_diagnostics_contract.py` | typed payload, phase availability, no sink/file |
| `test_assignment_phase_a_default_off_identity.py` | §18 complete pure/static matrix |

现有项目测试多为 standalone script；新测试遵循同一 convention，并可提供 `--json`，
不强制改造成全仓 pytest。

### 19.2 Safe existing regressions

计划运行：

```text
test_assignment_checkpoint_contract_core.py
test_assignment_lifecycle_observation_pure.py
test_assignment_lifecycle_observation_integration.py
test_assignment_lifecycle_resolver_smoke.py
test_assignment_lifecycle_resolver_runtime_smoke.py
test_assignment_lifecycle_controlled_training_gate.py
test_assignment_lifecycle_feed_forward_guard.py
test_assignment_harl_discrete_shape.py
test_assignment_rl_interface.py
test_assignment_logger_reward_whitelist.py
test_assignment_playback_attribution_diagnostics.py
test_assignment_initial_condition_contract.py
```

每个测试在执行前必须确认不会构造 Isaac environment、加载 checkpoint 或执行 actor
optimizer。若某现有脚本的实际行为超出 pure boundary，则从 A6 列表移除并标 deferred。

### 19.3 Prohibited test/run entries

不得在 Phase A 执行：

```text
test_assignment_harl_wrapper_smoke.py
test_assignment_harl_episode_reset_smoke.py
test_assignment_harl_fresh_policy_smoke.py
test_assignment_training_entry_readiness.py
test_assignment_checkpoint_save_load_continuation_smoke.py
test_assignment_checkpoint_all_loader_integration.py
test_assignment_checkpoint_save_metadata_integration.py
test_assignment_actor_critic_buffer_forward_backward_readiness.py
test_assignment_lifecycle_mask_and_harl_replay.py
train.py
play_assignment.py
evaluate_assignment*.py runtime entry
```

即使部分 checkpoint integration 使用 synthetic state dict，本 Phase A gate 明确禁止
checkpoint load/save，因此不运行。

`test_assignment_lifecycle_mask_and_harl_replay.py` 会进入 installed actor
`.update()` prelude，即使 spy 在 optimizer/backward 前中止；为避免把该调用误称为
“未执行 actor update”，本计划将其整体 deferred。

### 19.4 Planned commands

对后续实际变更：

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl `
  python -m py_compile <each changed Python file>

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl `
  python <pure test script> <supported arguments>

git status --short --untracked-files=all
git diff --name-status
git diff --check
git diff --cached --name-status
```

Per-script invocation rule：

| Scripts | Arguments |
|---|---|
| all new Phase A scripts | implement and use `--json` |
| current safe scripts containing an argparse `--json` option | use `--json` |
| `test_assignment_harl_discrete_shape.py` | no arguments |
| `test_assignment_rl_interface.py` | no arguments |
| `test_assignment_logger_reward_whitelist.py` | no arguments |

不得向不支持的脚本统一追加 `--json`。

Phase A completion report必须逐命令记录 exit code。任何需要 Isaac/AppLauncher 的 identity
row 标：

```text
DEFERRED-RUNTIME-IDENTITY-EVIDENCE
```

---

## 20. Risks, blockers and stop conditions

| Risk | Severity | Control |
|---|---|---|
| event profile 落入 diagnostics catch-all | critical | exhaustive enum match + test |
| event subtype 落入 old runtime boolean/Contract C consumer | critical | discriminated type；event has no old bool/mapping API；typed rejection |
| same contract source loaded under two module keys | critical | sole package-qualified key；prelaunch primitive-only；AST/sys.modules/clean-child identity tests |
| old profile mapping/order drift | high | golden mapping + tensor identity |
| v2 exact keys/bytes/fingerprint drift | critical | v2 untouched + golden bytes/hash |
| resolved object 注入 configs/logs | high | explicit non-serialized parameter |
| scenario explicit old profile behavior changes unexpectedly | high | conditional apply + source provenance |
| frozen dataclass 被误称 absolute deep immutable | high | scoped observable guarantee + behavioral alias-isolation/mutation tests；detector private |
| facts producer 被误当 lifecycle authority | critical | distinct typed IDs/stamps；environment facts-only；B0 placement deferred |
| wrapper/env/resolver each own generation | critical | external ledger + one lifecycle authority; no runtime hook in A |
| retry/resolver diagnostic 混入 lifecycle events | critical | three disjoint record types and container validators |
| forced rollout row 被误当 policy proposal | critical | four-mask truth table；resolver consumes policy mask only |
| invalid pair-attributed facts derive task result | high | cardinality/conflict/owner-match assertions before atomic consume |
| result lacks cumulative failed pairs | high | `updated_failed_pairs` authoritative snapshot |
| v3 claims unimplemented runtime semantics | critical | interface-only readiness; checkpoint I/O blocked |
| diagnostics creates old-profile files/keys | high | no sink; temp-dir/key assertions |
| Phase A slides into runner/reward/resolver work | critical | explicit no-change list and per-slice stop |

立即停止条件：

1. legacy 或 Contract C `torch.equal`/space/mapping identity 失败；
2. v2 canonical bytes、SHA 或 compatibility classification 改变；
3. event profile 在 Phase A 到达 env、resolver、HARL actor、checkpoint tensor I/O 或 play loop；
4. old profile 产生新 logger/info/file/RNG side effect；
5. profile 仍在多个模块独立推导；
6. identity-bearing contract 同一源出现第二 module key、bare fallback 或 `sys.modules` alias；
7. §10.2 scoped alias-isolation/mutation-detection guarantee 无法诚实实现；
8. event subtype 仍可到达 old runtime boolean consumer；
9. v3 需要扩宽或转换 v2 parser，或绑定 `_version`/storage/detector implementation；
10. 测试需要 AppLauncher、Isaac、training、playback、evaluation 或 checkpoint load/save；
11. slice 需要修改 `assignment_state.py`、current resolver/observation/reward/HARL behavior；
12. current code 与 V2.1 出现实质方法冲突；
13. worktree 出现未知非本 slice 修改；
14. 测试失败原因不能在当前小 slice 内明确定位。

停止动作：

```text
no speculative patch
no next slice
document blocker
update TASK_PROGRESS
wait for GPT/user decision
```

---

## 21. Phase A completion gate

Phase A 只有在以下全部成立时才可标完成：

- A1～A6 各自 pure/static tests 通过；
- four old profiles 在 §18 D0/D1 cohort 的 supported/blocked downstream route 无漂移；
- explicit scenario correction 被单独证明，未误标为 current byte identity；
- legacy、Contract C default-off matrix达到其标注的证据层级；
- v2 direct/dispatched canonical bytes and SHA exact；
- event v3 strict interface semantic descriptor/fingerprint 已定义；
- metadata-free explicit legacy fallback decision remains exact；
- checkpoint-ready v3 construction and all v3 weight I/O remain blocked；
- event runtime readiness 仍 fail-closed；
- event subtype 无 old runtime bool/mapping 且不能进入 old boolean consumer；
- canonical module key/type identity regressions complete；无 duplicate-source/different-key；
- facts producer 与 lifecycle authority identity/stamp 分离；B0 placement 未被 Phase A 偷渡冻结；
- facts/result schemas、ledger、pair-attribution assertions、observable immutability tests 完整；
- `_version`/storage/detector implementation 不进入 v3 fingerprint/compatibility；
- lifecycle event、retry opportunity、resolver diagnostic 三套类型/placement tests 完整；
- forced storage row 不构成 policy proposal；four-mask relation 和 resolver policy-only gate 完整；
- typed DTO 不执行 B/B0/C/D 算法；
- old routes无新 config/logger/file/RNG side effect；
- installed HARL 未修改；
- 没有 Isaac、training、playback、evaluation、checkpoint load/save；
- runtime-only rows仍明确 deferred；
- 形成 Phase A completion report 并等待进入 B0 的新批准。

Phase A completion 不自动授权 B0。

---

## 22. Recommended next action

本次 targeted revision 已关闭 PR-01～PR-07；下一次 GPT/user review 应验证这些是已冻结的
contract correction，而不是重新选择方法：

1. facts producer `ENV_EXECUTION_FACTS_PRODUCER_V1` 与 lifecycle authority
   `LIFECYCLE_AUTHORITY_V1` 分离，B0 才决定 runtime placement；
2. 七类 lifecycle event、单类 retry opportunity、三类 resolver diagnostic 使用独立
   type/record/container；
3. fixed storage row、policy proposal、forced nondecision 与 DVM 使用 four-mask truth table；
4. identity-bearing modules 只有 package-qualified canonical key，prelaunch primitive-only；
5. resolved profile 是 existing/event discriminated union，event variant 没有 old runtime
   booleans/legacy mapping；
6. `[E,M,N]` raw signals 满足 cardinality、pair mutual exclusion、owner attribution、
   availability edge 与 completed-task ownership assertions；
7. v3 只绑定 observable immutability behavior，不绑定 `_version`、storage identity 或
   detector implementation。

同时确认下列已审核选择未漂移：单一 selector、D0/D1/SCENARIO_CORRECTION、
`updated_failed_pairs`、invalid cost mask、terminal/historical mask separation、overflow
fail closed、v3 descriptor/checkpoint-ready split、metadata-free legacy fallback、
A1a→A1b→A1c、A3→A4→A5、以及 pure/static-only Phase A boundary。

只有在获得明确：

```text
A1 IMPLEMENTATION AUTHORIZATION
```

后，才推荐只实施：

```text
A1a — pure registry/resolved identity
```

完成 A1a pure tests 后停止，交付 A1a review package/report；不要自动进入 A1b/A2，
也不要 commit，除非用户另行明确授权。

---

## Final status

```text
classification:
  PHASE-A-PLAN-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

targeted findings:
  PR-01–PR-07 RESOLVED

Phase A implementation:
  not started

A1a implementation authorization:
  none -- wait for GPT/user approval

Phase B0/B/C/D/E:
  not entered
```
