# Phase A3x-0 Event Schema-Freeze Design — A3x-0R Targeted Revision

## 1. Classification

```text
classification:
  PHASE-A3X0-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

authorized slice:
  A3x-0R documentation-only targeted revision

production code changed:
  no

A3x-1 implementation:
  not entered

A4a restart:
  not restarted
```

本报告是一个 exact、单版本、无自由字段的设计提案。它冻结后续 A3x-1 应实现的
public descriptor 语义，但不声称这些语义已经接入 environment、wrapper、runner、HARL
或 checkpoint。仓库起始 HEAD 为
`dca976001d8c53a9cfb424b468fa58d9fca367f6`；预检时 index 为空，34 个已知 status
path 与 A1--A4a handoff 一致，没有未知修改。

完成分类的含义是“SF-01/SF-02 已在设计中闭环，等待 GPT/user targeted
review”，不是 A3x-1、A4a 或 runtime-ready。
本轮没有选择任何方法数值、没有创建 Python contract/test、没有加载模型或 checkpoint。

## 2. Blocker being resolved

A4a 在实现前正确触发了 `STOP -- A3 SCHEMA-FREEZE GAP`。本设计对六个 blocker 给出
唯一候选解：

| A4a gap | 本报告的冻结结果 |
|---|---|
| event actor layout 缺失 | 15 个 ordered blocks，固定 dtype/shape/flatten/normalization，公式 `6MN + 30M + 14N + 2` |
| event shared layout 缺失 | 19 个 ordered blocks，semantic `[E,S]` 与 transport `[E,M,S]` 分离，公式 `6MN + 31M + 15N + 8` |
| parameter identity 不完整 | 恰好 11 个 ordered numeric-TBD，typed owner vocabulary 和完整 triple/类型/单位/域 |
| descriptor ownership 不完整 | 19 个 V3 semantic sections 各有唯一 projection owner；domain authority 只引用、不复制 |
| local/cost/component/failure/model/training projection 不完整 | 每个 projection 都有 exact ordered key inventory、公式、版本与 source owner |
| 21/19 计数歧义 | 21 top-level keys = 2 discriminators + 19 typed semantic section dataclasses |

本设计没有把 Contract-C 改名为 event schema，也没有让 A4a 从文档散文复制出第二套
authority。第 23 节五项方法边界已 5/5 accepted；本轮只关闭 terminal-row
语义冲突和 serialized descriptor inventory 不完整两个 targeted findings。

## 3. Sources and authority boundary

证据优先级如下：

1. `Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md`；
2. approved Phase A implementation plan 与 targeted revision；
3. A1--A3 public contract/descriptor 和 tests；
4. 当前 production/runtime 代码，只用于确认 primitive、transport 与缺口；
5. installed HARL，只读确认当前 HAPPO/model 路径，不提升为 event authority。

重点代码证据：

- `scan_mobile_manipulator_env.py:1686-1745,2852-2928`：当前 assignment problem、96D
  raw observation 和 nearest-8 local packing；
- `assignment_lifecycle_observation.py:40-55,619-762`：Contract-C 的 3N lifecycle
  add-on、2M critic budget 和维度公式；
- `assignment_harl_wrapper.py:223-270,916-962,2306-2425`：现有 actor extension、
  actor-concat shared state、normalization 和 agent-axis repeat；
- `assignment_profile_contract.py:650-670`：event profile 已有 schema/version identity，
  但没有 exact fields；
- `assignment_mrta_contract.py:3942-4087`：当前 A3 DTO schemas、mask equations 与缺失的
  domain projections；
- `assignment_lifecycle_transition_contract.py:2730-2805`：当前 A2 descriptor 尚未拥有
  task/robot state enum 与完整 failure projection；
- `assignment_harl_training.py:525-526`：实际 assignment runner 的 actor/critic 都读取
  `model.hidden_sizes`；
- installed `harl/runners/on_policy_ha_runner.py:16-127` 和
  `harl/algorithms/actors/happo.py:76-155`：当前 factor、advantage 和 update 行为。

状态标签：本报告中的 `FROZEN-PROPOSAL` 是待 review 的 exact 设计；`CURRENT-CODE` 是
只读事实；`DEFERRED-RUNTIME-EVIDENCE` 表示必须到 B0/B/C 或 checkpoint-ready gate 才能
验证。后者不能被 A4a interface fingerprint 误写为 runtime pass。

## 4. Existing observation/runtime inventory

当前 raw actor observation 的符号维度为：

```text
raw_actor_dim(M)
= base_rel(3) + yaw_sincos(2) + scanner_rel(3) + scanner_quat(4)
  + coverage(1) + capability(4) + nearest_slots(8*8)
  + other_scanners(3*(M-1)) + previous_low_level_action(9)
= 87 + 3M

raw_actor_dim(3) = 96
```

Contract-C wrapper 在 raw observation 后追加每 task 17 列、5 个 noop context、
`N+1` previous assignment one-hot、7 个 dynamic scalar 和 N 个 covered flags：

```text
contract_c_actor_dim(M,N)
= (87 + 3M) + 17N + 5 + (N+1) + 7 + N
= 100 + 3M + 19N

contract_c_actor_dim(3,50) = 1059

contract_c_shared_dim(M,N)
= M * contract_c_actor_dim(M,N) + 2M

contract_c_shared_dim(3,50) = 3183
```

| Current capability | Read-only finding | Event treatment |
|---|---|---|
| raw nearest-8 task slots | 距离排序后局部重排，slot 不保留 global task identity | 禁止复用 layout |
| Contract-C task rows | 14 legacy + 3 lifecycle proxy fields | primitive 可取，schema identity 不可复用 |
| Contract-C shared | concat all actor obs + critic budget 2M | 不作为 centralized event state |
| current cost | scanner-to-viewpoint Euclidean distance | 仅 prototype；不满足 expected-time contract |
| current lifecycle state | completed/unassigned proxy，robot 全 idle placeholder | 不足以构造 target six/four-state lifecycle |
| A3 DVM DTO | 完整 mask provenance 与 generation fields | 可由 MRTA projection 继续拥有 |
| event runtime route | `event_gated_phase_a_interface_only_v1` | 不可执行、不可构造模型、不可做 checkpoint I/O |
| configured critic hidden sizes | YAML 写 `[512,256]` | 当前 assignment runner 未读取该 key |
| actual runner critic hidden sizes | 与 actor 同取 `[256,256]` | 作为 current config projection，非 runtime compatibility evidence |

因此 event actor/shared 必须是新的 fixed-global identity。当前代码能提供一部分物理
primitive 和 transport precedent，但不能证明新 schema 已可运行。

## 5. Event actor observation exact schema

### 5.1 Identity, scope and ordering

```text
schema_version:
  event_gated_global_actor_observation_v1

scope:
  one fixed-width observation per actor over the complete fixed M-robot/N-task state

robot reference frame:
  scenario environment-local Cartesian frame; actor identity is explicit

global robot order:
  scale_contract.ordered_agent_names, IDs 0..M-1

global task order:
  scenario task IDs 0..N-1

flatten:
  block order below; inside a table, outer global ID first, feature/task ID last,
  C row-major; no local repacking or renumbering

output dtype:
  torch.float32 for every concatenated block
```

M and N are positive fixed checkpoint dimensions. `NO_OWNER` is the final column of an
`M+1` one-hot; `NO_TASK` is the final column of an `N+1` one-hot. The snapshot is taken after
execution facts and lifecycle updates have finalized `a0`, and before proposal sampling.

### 5.2 Exact ordered blocks

| # | Canonical block | Category / treatment | Shape | dtype before concat | Flatten rule | Semantic source and policy-visible reason |
|---:|---|---|---:|---|---|---|
| 1 | `actor_robot_identity_one_hot` | A / `EVENT_SPECIFIC` | `[M]` | torch.bool | robot ID | 识别本 actor；global IDs 不因 local set 改变 |
| 2 | `global_robot_physical_table` | B / `REUSE_PRIMITIVE` | `[M,16]` | torch.float32 | robot, feature | 全队 base/scanner pose 与 capability；transfer decision 需要 global robot state |
| 3 | `global_robot_lifecycle_table` | B / `EVENT_SPECIFIC` | `[M,5]` | torch.bool | robot, feature | four-state lifecycle + availability；显式区分 unavailable/needs-assignment |
| 4 | `global_task_pose_table` | C / `REUSE_PRIMITIVE` | `[N,7]` | torch.float32 | task, feature | 所有 task 按 global ID 的 pose；不使用 nearest slots |
| 5 | `global_task_lifecycle_one_hot` | C / `EVENT_SPECIFIC` | `[N,6]` | torch.bool | task, state | 完整 task phase，含 `TEAM_INFEASIBLE` |
| 6 | `event_updated_task_ownership_one_hot` | D / `REUSE_PRIMITIVE` | `[N,M+1]` | torch.bool | task, owner | policy 前 finalized ownership，末列 `NO_OWNER` |
| 7 | `event_updated_baseline_assignment_one_hot` | D / `REUSE_PRIMITIVE` | `[M,N+1]` | torch.bool | robot, task | policy 前 event-updated baseline `a0`，末列 `NO_TASK` |
| 8 | `episode_permanent_failed_pair_mask` | E / `EVENT_SPECIFIC` | `[M,N]` | torch.bool | robot, task | episode-cumulative structural terminal pair failure |
| 9 | `assignment_tick_nominal_path_valid_mask` | E / `EVENT_SPECIFIC` | `[M,N]` | torch.bool | robot, task | tick-conditioned invalid-path legality/value companion |
| 10 | `assignment_tick_normalized_nominal_remaining_cost` | E / `EVENT_SPECIFIC` | `[M,N]` | torch.float32 | robot, task | tick-conditioned expected-time nominal sum；owner 用 remaining cost |
| 11 | `target_action_mask` | F / `EVENT_SPECIFIC` | `[M,N]` | torch.bool | robot, global task | pre-policy/forced-storage legality，仍保留 global task ID |
| 12 | `noop_action_mask` | F / `EVENT_SPECIFIC` | `[M]` | torch.bool | robot | 每个 robot 的 raw noop ID `N` legality |
| 13 | `assignment_trigger_context` | F / `EVENT_SPECIFIC` | `[M,5]` | torch.bool | robot, feature | event/retry/opportunity/DVM/CONTINUE 的 pre-policy context |
| 14 | `per_robot_workload` | G / `REUSE_PRIMITIVE` | `[M,1]` | torch.float32 | robot | 当前 episode authoritative completion attribution 的 normalized count |
| 15 | `episode_context` | G / `REUSE_PRIMITIVE` | `[2]` | torch.float32 | feature | assignment tick presence 与 physical episode progress |

严格列顺序：

```text
global_robot_physical_table:
  base_x, base_y, base_z,
  base_yaw_sin, base_yaw_cos,
  scanner_x, scanner_y, scanner_z,
  scanner_qw, scanner_qx, scanner_qy, scanner_qz,
  arm_reach, scanner_min_range, scanner_max_range, scanner_fov_cos

global_robot_lifecycle_table:
  EXECUTING, NEEDS_ASSIGNMENT, WAITING_FOR_TASK, UNAVAILABLE, robot_available

global_task_pose_table:
  task_x, task_y, task_z, task_qw, task_qx, task_qy, task_qz

global_task_lifecycle_one_hot:
  AVAILABLE, CLAIMED, NAVIGATING, ALIGNING, COMPLETED, TEAM_INFEASIBLE

assignment_trigger_context:
  lifecycle_event_seed,
  scheduled_retry_opportunity,
  decision_opportunity_present,
  decision_valid,
  current_task_continue_legal

per_robot_workload:
  completed_task_fraction

episode_context:
  assignment_tick_present, episode_progress_fraction
```

Cross-block invariants：

```text
robot_available[i] == (robot_state[i] != UNAVAILABLE)

decision_opportunity_present[i]
== assignment_tick_present
   AND local_robot_mask[i]

current_task_continue_legal[i]
== false, when current_task_id[i] == NO_TASK
== false, when terminal
== target_action_mask[i,current_task_id[i]], otherwise

available_actions[i]
== concat(target_action_mask[i,:], noop_action_mask[i])

decision_valid[i]
== decision_opportunity_present[i]
   AND robot_available[i]
   AND semantic_legal_action_count[i] >= 2
   AND not terminal

task_state[j] in {AVAILABLE, COMPLETED, TEAM_INFEASIBLE}
=> owner[j] == NO_OWNER

task_state[j] in {CLAIMED, NAVIGATING, ALIGNING}
=> exactly one owner[j] in 0..M-1

robot_state[i] == EXECUTING
=> exactly one current_task_id[i] in 0..N-1
   AND owner[current_task_id[i]] == i
   AND task_state[current_task_id[i]] in {CLAIMED, NAVIGATING, ALIGNING}

robot_state[i] in {NEEDS_ASSIGNMENT, WAITING_FOR_TASK, UNAVAILABLE}
=> current_task_id[i] == NO_TASK
```

每个 **nonterminal stored action row** 至少一个 legal action；只有一个 semantic legal
action 时 DVM 必须为 0。terminal 是 `terminal_no_row`，不是 action row：其 target/noop/
available masks 全 false、semantic count 为 0、forced ID 为 `-1`，且没有 action/log-prob
storage。仅对 `storage_row_present=true` 的 nonterminal rows，actor distribution/historical
storage 接收的 `available_actions[i]` 必须与该 row snapshot 同 generation 且 exact equal，
不能用下一时刻 mask 重解释已保存 action。

`snapshot_generation_valid` 不进入 policy feature。assignment-tick builder 必须先断言
observation、cost、local set、DVM 与 lifecycle result 的
`(env_id, episode_generation, transition_generation, assignment_tick_generation)` exact equality，
再计算上述 blocks；不匹配直接 fail-fast。ordinary nonterminal no-tick 与 terminal 只校验
lifecycle result、row class 和 observation/sidecar generation；cost/local-set/
`DecisionValidMaskSnapshot` tick DTO 必须 absent。ordinary forced one-action mask 是
ProposalSnapshot historical-storage encoding，不得伪装成 A3 DVM snapshot；terminal 若 fixed-shape
carrier 保留 canonical `NO_ROW` tensor slot，该 slot 仍不表示 semantic storage/proposal/forced row。

`event_updated_task_ownership_one_hot` 与
`event_updated_baseline_assignment_one_hot` 必须是同一 `a0` 的 mutual inverse；重复信息是
显式 assignment/ownership contract，不是两套 authority。

### 5.2.1 Actor public descriptor serialized inventory

未来 event-profile public descriptor 的 `actor_schema` mapping exact top-level key order 恰好
18 项：

```text
schema_version
scope
robot_reference_frame
global_robot_order_source
global_task_order_source
output_dtype
flatten_order
block_record_field_order
block_count
blocks
dimension_formula
reference_dimension
normalization_contract
generation_binding
temporal_boundary
ordinary_no_tick_contract
terminal_row_contract
excluded_fields
```

exact scalar/string values：

```text
schema_version: event_gated_global_actor_observation_v1
scope: global_fixed_width_per_actor_complete_team_state_v1
robot_reference_frame: scenario_environment_local_cartesian_v1
global_robot_order_source: scale_contract.ordered_agent_names
global_task_order_source: scale_contract.ordered_task_ids
output_dtype: torch.float32
flatten_order: block_order_then_c_row_major_global_id_outer_feature_or_task_id_inner
block_count: 15
dimension_formula: 6*M*N + 30*M + 14*N + 2
temporal_boundary: fact_updated_a0_pre_policy_no_same_tick_resolver_outcome_v1
```

`block_record_field_order` exact 12-key tuple：

```text
order
name
category
treatment
shape
source_dtype
serialized_dtype
flatten_rule
column_order
semantic_source
visibility
normalization_rule
```

`shape` 是 deterministic primitive tuple；symbolic dimensions 序列化 exact strings
`M`、`N`、`M+1`、`N+1`，固定维度序列化 exact ints。dtype 也序列化为下表 exact strings。
没有 named feature columns 的 block 使用 exact empty tuple `()`；动态 identity axis 的顺序由
`flatten_rule` 与 scale source 冻结。

| `order` | `name` | `category` | `treatment` | `shape` | `source_dtype` | `serialized_dtype` | `flatten_rule` | `column_order` | `semantic_source` | `visibility` | `normalization_rule` |
|---:|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `actor_robot_identity_one_hot` | `A` | `EVENT_SPECIFIC` | `("M",)` | `torch.bool` | `torch.float32` | `global_robot_id_ascending` | `()` | `actor_id_against_scale_contract_ordered_agent_names` | `policy_visible` | `bool_to_float32_0_1` |
| 2 | `global_robot_physical_table` | `B` | `REUSE_PRIMITIVE` | `("M",16)` | `torch.float32` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(base_x,base_y,base_z,base_yaw_sin,base_yaw_cos,scanner_x,scanner_y,scanner_z,scanner_qw,scanner_qx,scanner_qy,scanner_qz,arm_reach,scanner_min_range,scanner_max_range,scanner_fov_cos)` | `finalized_pre_policy_global_robot_physical_state` | `policy_visible` | `robot_physical_normalization_v1` |
| 3 | `global_robot_lifecycle_table` | `B` | `EVENT_SPECIFIC` | `("M",5)` | `torch.bool` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(EXECUTING,NEEDS_ASSIGNMENT,WAITING_FOR_TASK,UNAVAILABLE,robot_available)` | `finalized_pre_policy_robot_lifecycle_state` | `policy_visible` | `bool_to_float32_0_1` |
| 4 | `global_task_pose_table` | `C` | `REUSE_PRIMITIVE` | `("N",7)` | `torch.float32` | `torch.float32` | `global_task_id_outer_column_order_inner` | `(task_x,task_y,task_z,task_qw,task_qx,task_qy,task_qz)` | `finalized_pre_policy_global_task_pose` | `policy_visible` | `task_pose_normalization_v1` |
| 5 | `global_task_lifecycle_one_hot` | `C` | `EVENT_SPECIFIC` | `("N",6)` | `torch.bool` | `torch.float32` | `global_task_id_outer_column_order_inner` | `(AVAILABLE,CLAIMED,NAVIGATING,ALIGNING,COMPLETED,TEAM_INFEASIBLE)` | `finalized_pre_policy_task_lifecycle_state` | `policy_visible` | `bool_to_float32_0_1` |
| 6 | `event_updated_task_ownership_one_hot` | `D` | `REUSE_PRIMITIVE` | `("N","M+1")` | `torch.bool` | `torch.float32` | `global_task_id_outer_global_robot_id_then_no_owner_inner` | `()` | `finalized_pre_policy_a0_ownership` | `policy_visible` | `bool_to_float32_0_1` |
| 7 | `event_updated_baseline_assignment_one_hot` | `D` | `REUSE_PRIMITIVE` | `("M","N+1")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_then_no_task_inner` | `()` | `finalized_pre_policy_a0_assignment` | `policy_visible` | `bool_to_float32_0_1` |
| 8 | `episode_permanent_failed_pair_mask` | `E` | `EVENT_SPECIFIC` | `("M","N")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `episode_cumulative_updated_failed_pairs` | `policy_visible` | `bool_to_float32_0_1` |
| 9 | `assignment_tick_nominal_path_valid_mask` | `E` | `EVENT_SPECIFIC` | `("M","N")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `assignment_tick_cost_path_valid_else_false` | `policy_visible` | `bool_to_float32_0_1` |
| 10 | `assignment_tick_normalized_nominal_remaining_cost` | `E` | `EVENT_SPECIFIC` | `("M","N")` | `torch.float32` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `assignment_tick_nominal_cost_else_zero` | `policy_visible` | `valid_cost_divide_episode_time_limit_else_zero` |
| 11 | `target_action_mask` | `F` | `EVENT_SPECIFIC` | `("M","N")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `tick_policy_or_ordinary_forced_or_terminal_zero_target_mask` | `policy_visible` | `bool_to_float32_0_1` |
| 12 | `noop_action_mask` | `F` | `EVENT_SPECIFIC` | `("M",)` | `torch.bool` | `torch.float32` | `global_robot_id_ascending` | `()` | `tick_policy_or_ordinary_forced_or_terminal_zero_noop_mask` | `policy_visible` | `bool_to_float32_0_1` |
| 13 | `assignment_trigger_context` | `F` | `EVENT_SPECIFIC` | `("M",5)` | `torch.bool` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(lifecycle_event_seed,scheduled_retry_opportunity,decision_opportunity_present,decision_valid,current_task_continue_legal)` | `finalized_row_class_trigger_context` | `policy_visible` | `bool_to_float32_0_1` |
| 14 | `per_robot_workload` | `G` | `REUSE_PRIMITIVE` | `("M",1)` | `torch.float32` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(completed_task_fraction,)` | `authoritative_completion_attribution` | `policy_visible` | `completed_task_count_divide_N` |
| 15 | `episode_context` | `G` | `REUSE_PRIMITIVE` | `(2,)` | `torch.float32` | `torch.float32` | `column_order` | `(assignment_tick_present,episode_progress_fraction)` | `finalized_row_class_and_episode_progress` | `policy_visible` | `tick_identity_and_elapsed_steps_divide_horizon` |

`reference_dimension` exact 3-key order/value：

```text
M: 3
N: 50
dimension: 1692
```

`generation_binding` exact 3-key order/value：

```text
association_key:
  (env_id, episode_generation, transition_generation, assignment_tick_generation)
required_equal_sources:
  (lifecycle_transition_result,
   local_set_result_when_assignment_tick_present,
   nominal_pair_cost_result_when_assignment_tick_present,
   decision_valid_mask_snapshot_when_assignment_tick_present)
mismatch_behavior:
  fail_closed_before_observation_construction
```

Tick DTO sources 在 ordinary no-tick/terminal 必须 absent；这条 conditional absence 是
`required_equal_sources` literal 的一部分，不允许 implementation-time optional source。

### 5.3 Encoding and normalization ownership

- environment-local position、arm reach 和 scanner range 除以 resolved positive
  `scene.env_spacing`；yaw 只用 `sin/cos`；FOV 使用 cosine；
- quaternion 先归一为 unit `wxyz`，再取唯一 hemisphere representative：若 `qw<0` 整体
  乘 `-1`；若 `qw==0`，则使 `(qx,qy,qz)` 中第一个非零分量为正；zero norm fail-fast；
- underlying cost descriptor 始终保存 seconds。actor/shared observation 将 valid nominal
  cost 除以 resolved positive episode time-limit seconds，不裁剪；
- invalid pair 在 cost DTO 中仍是 canonical NaN；assignment-tick observation 中 value 填
  `0.0`，且 `assignment_tick_nominal_path_valid_mask=0`，禁止大有限 sentinel；
- `completed_task_fraction = completed_by_robot_count / N`，限定 `[0,1]`，episode reset 清零；
- `episode_progress_fraction = elapsed_physical_steps / episode_horizon_steps`，限定 `[0,1]`；
- bool/one-hot 精确编码 `0.0/1.0`；每行 categorical one-hot 恰好一项为 1；
- 上述 pre-model semantic normalization 由 actor/shared schema descriptor 拥有。HARL
  `use_feature_normalization` 是 model-layer identity，不能替代或改变这些编码。

event-profile root 的 `scale_contract` mapping exact key order 恰好 11 项：

```text
contract_version
M
N
ordered_agent_names
ordered_task_ids
scene_env_spacing
sim_dt_seconds
control_decimation
physical_control_step_seconds
episode_time_limit_seconds
episode_horizon_steps
```

```text
contract_version: event_gated_scale_contract_v1
M > 0
N > 0
len(ordered_agent_names) == M
ordered_agent_names are unique nonempty strings
ordered_task_ids == tuple(range(N))
physical_control_step_seconds == sim_dt_seconds * control_decimation
episode_horizon_steps
== ceil(episode_time_limit_seconds / physical_control_step_seconds)
```

所有项在 interface descriptor build 时从 resolved scenario/config 取得 concrete immutable
value；`scene_env_spacing/sim_dt_seconds/episode_time_limit_seconds` 是 finite float `>0`，
`control_decimation/episode_horizon_steps` 是 exact int `>=1`。派生式：

```text
physical_control_step_seconds = sim_dt_seconds * control_decimation
episode_horizon_steps = ceil(episode_time_limit_seconds / physical_control_step_seconds)
```

`num_agents`、`action_dimension`、`noop_raw_id`、`noop_decoded_value` 明确不属于
`scale_contract`；它们只由第 17 节 MRTA `action_contract` 拥有。future V3 top-level section 名
仍是 `scale`，其内容 exact 投影 `scale_contract`；这是 projection rename，不是第二 owner。

actor/shared normalization projection exact keys 为
`(normalization_contract_version, position_length_denominator_source,
cost_denominator_source, episode_progress_denominator_source, quaternion_order,
quaternion_sign_rule, invalid_cost_observation_fill,
model_feature_normalization_contract)`，分别引用
`scale_contract.scene_env_spacing`、`scale_contract.episode_time_limit_seconds`、
`scale_contract.episode_horizon_steps`；future V3 `scale.*` 只是同一 mapping 的 section
projection。resolved values 和 projection 必须进入 V3 fingerprint。
environment episode horizon 与 HARL `train.episode_length` 是两个独立 identity，禁止互换。

`normalization_contract` exact 8-key order/value：

```text
normalization_contract_version: event_gated_observation_normalization_v1
position_length_denominator_source: scale_contract.scene_env_spacing
cost_denominator_source: scale_contract.episode_time_limit_seconds
episode_progress_denominator_source: scale_contract.episode_horizon_steps
quaternion_order: wxyz
quaternion_sign_rule: unit_then_qw_nonnegative_then_first_nonzero_xyz_positive_when_qw_zero
invalid_cost_observation_fill: 0.0
model_feature_normalization_contract: separate_model_layer_use_feature_normalization_identity
```

`alignment_time_constant` 不直接成为 observation feature。它只通过 cost/path authority
构造的 alignment cost 影响 nominal sum，因此不会改变 actor block order 或 normalization
公式。Top-K、pair gate 和 component objective 都只消费
`nominal=navigation+alignment`，而 NAVIGATING/ALIGNING 已由 lifecycle one-hot 显式表示；
因此 policy 只观察 nominal sum。navigation/alignment 分解保留在 cost DTO 用于 contract
validation/diagnostics，不作为 resolver objective 未消费的额外 policy signal。若未来改为两
个分量 block，actor/shared 各增加 `MN`，`M=3,N=50` 将分别变为 `1842/1901`，必须 bump
schema/fingerprint，不能保持 v1 identity。

### 5.4 Explicit exclusions and temporal boundary

`actor_schema.excluded_fields` 是 exact 15-item ordered tuple，不是 set：

```text
nearest_or_local_task_repacking
local_robot_or_task_renumbering
previous_low_level_action
attempt_count_or_age
same_target_or_repeated_assignment_history
contract_c_budget_state
private_mutation_detector_or_capability
raw_record_ids_or_generation_counters
raw_event_payload
policy_proposal
proposal_log_probability
proposal_acceptance_or_rejection
same_tick_resolver_result
same_tick_effective_assignment
future_execution_facts
```

这些 names 只进入 descriptor exclusion identity，不会把对应值重新加入 observation。

上一 tick 已提交且已成为本次 lifecycle current state 的 assignment 可以进入新的 `a0`；
本 tick post-policy outcome 绝不进入同一 observation。

terminal transition 不构造可供 actor sampling/storage 的 per-actor row。为构造第 6 节的
pre-reset critic sidecar，可按同一 block layout 序列化 finalized physical/lifecycle/a0 facts 与
全零 action semantics；该 semantic sidecar 不是 actor input invocation、proposal snapshot 或
forced placeholder。

### 5.5 Every-physical-step construction

critic 使用全部有效 physical steps，因此 ordinary nonterminal no-tick row 也必须
唯一编码；terminal 则只提供同一末端 transition 的 pre-reset critic boundary sidecar，
不另造 transition/loss sample。本设计冻结
`cost_visibility_mode=assignment_tick_fresh_else_zero_v1`：

| Block class | Assignment-tick row | Ordinary no-tick row |
|---|---|---|
| physical/lifecycle/a0/failed/workload/progress | 从本 transition finalized current state 构造 | 同样从本 transition finalized current state 构造，不 carry stale state |
| tick path/cost blocks | 从本 tick 单一 finalized `NominalPairCostResult` 映射 | path-valid 全 false、normalized cost 全 `0.0`；不构造/复用旧 cost DTO |
| trigger context | event/retry/opportunity/DVM/CONTINUE 的本 tick facts | event/retry/opportunity/DVM 为 false；executing robot 的 CONTINUE-legal 为 true，其余 false |
| shared local masks/flags | final merged `LocalSetResult` | `local_robot/local_task/owner_added/overlap/overflow` 全 false |
| executing robot action row | event mask，current task 必须保留 | 仅 current task true；noop false |
| non-executing robot action row | event mask | 仅 noop true；所有 task false |

这里 non-executing 包括 `NEEDS_ASSIGNMENT`、`WAITING_FOR_TASK`、`UNAVAILABLE`。ordinary
nonterminal no-tick row 每个 robot 的 semantic legal count 恰好 1，
`decision_opportunity_present=0`、`DVM=0`，只保存 deterministic forced storage row，不调用
actor sampling。executing robot 只允许 current task；available non-executing robot 只允许
noop；unavailable robot 也只允许 deterministic noop storage encoding，但它不是 policy
proposal。每行 `forced_policy_action_id` 必须指向该唯一 legal action，
`policy_proposal_present=false`、`forced_nondecision=true`。

`actor_schema.ordinary_no_tick_contract` exact 11-key order/value：

```text
row_class: nonterminal_forced_nondecision
terminal: false
assignment_tick_present: false
semantic_action_count: 1
decision_valid: false
storage_row_present: true
policy_proposal_present: false
forced_nondecision_present: true
actor_sampling: not_called
executing_action_rule: current_task_only_and_noop_illegal
nonexecuting_action_rule: deterministic_noop_only_storage_encoding_including_unavailable
```

A3 compatibility boundary：只有 assignment-tick semantic masks 构造
`DecisionValidMaskSnapshot`。该 DTO 的 no-opportunity row 继续要求 all-false actions/count 0；
ordinary no-tick 的 one-action mask 只作为 nonterminal forced row 的 historical
available-action/storage encoding 进入 `ProposalSnapshot`，不送入或改写 DVM DTO。terminal 的
canonical `NO_ROW` carrier slot（若 batching 保留）必须维持 action ID `-1`、log-prob `0`、
historical mask all false，且不算 storage/proposal/forced row。

tick-conditioned path/cost block 的全零只表示“本 step 没有 assignment cost snapshot”，不能
推导实际 no-path；`assignment_tick_present` 是其 mandatory companion。该选择保留 event-gated
cost computation，同时让 fixed physical-step feed-forward rollout transport 保持确定形状。

非 terminal ordinary no-tick snapshot 若存在 available `NEEDS_ASSIGNMENT` robot、trigger-eligible
lifecycle event 或 due opportunity，则违反 §11 seed/tick obligation，必须 fail closed；上表为所有
state 定义 forced encoding，不授权 scheduler 跳过必需的 assignment tick。

terminal 与 ordinary no-tick 不共享 forced-row 规则。
`actor_schema.terminal_row_contract` exact 13-key order/value 是：

```text
row_class: terminal_no_row
terminal: true
assignment_tick_present: false
target_actions: all_false
noop_action: all_false
semantic_action_count: 0
decision_valid: false
forced_policy_action_id: -1
storage_row_present: false
policy_proposal_present: false
forced_nondecision_present: false
actor_sampling: not_called
resolver_consumption: false
```

由 `target_actions/noop_action` 派生的 `available_actions` exact all false，且
`decision_opportunity_present=false`；这两项是 cross-block invariants，不向上述 frozen 13-key
record 添加字段。

terminal 不创建 assignment tick、local set、cost DTO、proposal snapshot、component 或 forced
placeholder；不调用 actor，也不写 action/log-prob storage row。其 finalized pre-reset critic
sidecar 规则见第 6 节。

## 6. Event shared observation exact schema

### 6.1 Identity and construction

```text
schema_version:
  event_gated_global_centralized_observation_v1

construction_mode:
  global_fixed_width_centralized_v1

semantic state:
  [E,S]

runner transport:
  [E,M,S], produced only by wrapper/runner broadcast adapter

runner_transport_mode:
  repeat_identical_semantic_shared_state_across_agent_axis_v1

EP critic minibatch input:
  [B,S]
```

Centralized state 不是 `concat(all actor observations)`。actor blocks 2--15 中每个 global
fact 只存一次，不存 actor identity；随后追加五个 pre-policy critic-only local/terminal blocks。
所有 blocks 按下表顺序 C row-major flatten，最终 float32。

未来 event-profile public descriptor 的 `shared_schema` mapping exact top-level key order 恰好
19 项：

```text
schema_version
construction_mode
semantic_state_shape
runner_transport_shape
critic_input_shape
runner_transport_mode
output_dtype
flatten_order
block_record_field_order
block_count
blocks
dimension_formula
reference_dimension
normalization_contract_reference
generation_binding
temporal_boundary
ordinary_no_tick_contract_reference
terminal_shared_state_contract
excluded_fields
```

exact values/reference literals：

```text
schema_version: event_gated_global_centralized_observation_v1
construction_mode: global_fixed_width_centralized_v1
semantic_state_shape: ("E","S")
runner_transport_shape: ("E","M","S")
critic_input_shape: ("B","S")
runner_transport_mode: repeat_identical_semantic_shared_state_across_agent_axis_v1
output_dtype: torch.float32
flatten_order: block_order_then_c_row_major_global_id_outer_feature_or_task_id_inner
block_count: 19
dimension_formula: 6*M*N + 31*M + 15*N + 8
normalization_contract_reference: actor_schema.normalization_contract
temporal_boundary: fact_updated_pre_policy_or_terminal_pre_reset_no_same_tick_resolver_outcome_v1
ordinary_no_tick_contract_reference: actor_schema.ordinary_no_tick_contract
```

上述 shape 值的 serialized primitive 是 exact tuple of strings，人类张量记法分别为
`[E,S]`/`[E,M,S]`/`[B,S]`；不序列化 free-form bracket string。

`generation_binding` 是 exact inline 3-key record，与
`actor_schema.generation_binding` 的 key order/value exact equal；不是 free-form reference。terminal
source boundary 另由 `terminal_shared_state_contract` 冻结。

`reference_dimension` exact 4-key order/value：

```text
M: 3
N: 50
semantic_dimension: 1751
runner_agent_count: 3
```

### 6.2 Exact ordered blocks

`block_record_field_order` exact 10-key tuple：

```text
order
name
shape
source_dtype
serialized_dtype
flatten_rule
column_order
visibility
semantic_source
construction_rule
```

`visibility` 只允许 exact literals `actor_visible`、`critic_only`。exact 19 records：

| `order` | `name` | `shape` | `source_dtype` | `serialized_dtype` | `flatten_rule` | `column_order` | `visibility` | `semantic_source` | `construction_rule` |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | `global_robot_physical_table` | `("M",16)` | `torch.float32` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(base_x,base_y,base_z,base_yaw_sin,base_yaw_cos,scanner_x,scanner_y,scanner_z,scanner_qw,scanner_qx,scanner_qy,scanner_qz,arm_reach,scanner_min_range,scanner_max_range,scanner_fov_cos)` | `actor_visible` | `finalized_pre_policy_global_robot_physical_state` | `exact_actor_block_2_snapshot_stored_once_without_actor_identity` |
| 2 | `global_robot_lifecycle_table` | `("M",5)` | `torch.bool` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(EXECUTING,NEEDS_ASSIGNMENT,WAITING_FOR_TASK,UNAVAILABLE,robot_available)` | `actor_visible` | `finalized_pre_policy_robot_lifecycle_state` | `exact_actor_block_3_snapshot_stored_once_without_actor_identity` |
| 3 | `global_task_pose_table` | `("N",7)` | `torch.float32` | `torch.float32` | `global_task_id_outer_column_order_inner` | `(task_x,task_y,task_z,task_qw,task_qx,task_qy,task_qz)` | `actor_visible` | `finalized_pre_policy_global_task_pose` | `exact_actor_block_4_snapshot_stored_once_without_actor_identity` |
| 4 | `global_task_lifecycle_one_hot` | `("N",6)` | `torch.bool` | `torch.float32` | `global_task_id_outer_column_order_inner` | `(AVAILABLE,CLAIMED,NAVIGATING,ALIGNING,COMPLETED,TEAM_INFEASIBLE)` | `actor_visible` | `finalized_pre_policy_task_lifecycle_state` | `exact_actor_block_5_snapshot_stored_once_without_actor_identity` |
| 5 | `event_updated_task_ownership_one_hot` | `("N","M+1")` | `torch.bool` | `torch.float32` | `global_task_id_outer_global_robot_id_then_no_owner_inner` | `()` | `actor_visible` | `finalized_pre_policy_a0_ownership` | `exact_actor_block_6_snapshot_stored_once_without_actor_identity` |
| 6 | `event_updated_baseline_assignment_one_hot` | `("M","N+1")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_then_no_task_inner` | `()` | `actor_visible` | `finalized_pre_policy_a0_assignment` | `exact_actor_block_7_snapshot_stored_once_without_actor_identity` |
| 7 | `episode_permanent_failed_pair_mask` | `("M","N")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `actor_visible` | `episode_cumulative_updated_failed_pairs` | `exact_actor_block_8_snapshot_stored_once_without_actor_identity` |
| 8 | `assignment_tick_nominal_path_valid_mask` | `("M","N")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `actor_visible` | `assignment_tick_cost_path_valid_else_false` | `exact_actor_block_9_snapshot_stored_once_without_actor_identity` |
| 9 | `assignment_tick_normalized_nominal_remaining_cost` | `("M","N")` | `torch.float32` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `actor_visible` | `assignment_tick_nominal_cost_else_zero` | `exact_actor_block_10_snapshot_stored_once_without_actor_identity` |
| 10 | `target_action_mask` | `("M","N")` | `torch.bool` | `torch.float32` | `global_robot_id_outer_global_task_id_inner` | `()` | `actor_visible` | `tick_policy_or_ordinary_forced_or_terminal_zero_target_mask` | `exact_actor_block_11_snapshot_stored_once_without_actor_identity` |
| 11 | `noop_action_mask` | `("M",)` | `torch.bool` | `torch.float32` | `global_robot_id_ascending` | `()` | `actor_visible` | `tick_policy_or_ordinary_forced_or_terminal_zero_noop_mask` | `exact_actor_block_12_snapshot_stored_once_without_actor_identity` |
| 12 | `assignment_trigger_context` | `("M",5)` | `torch.bool` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(lifecycle_event_seed,scheduled_retry_opportunity,decision_opportunity_present,decision_valid,current_task_continue_legal)` | `actor_visible` | `finalized_row_class_trigger_context` | `exact_actor_block_13_snapshot_stored_once_without_actor_identity` |
| 13 | `per_robot_workload` | `("M",1)` | `torch.float32` | `torch.float32` | `global_robot_id_outer_column_order_inner` | `(completed_task_fraction,)` | `actor_visible` | `authoritative_completion_attribution` | `exact_actor_block_14_snapshot_stored_once_without_actor_identity` |
| 14 | `episode_context` | `(2,)` | `torch.float32` | `torch.float32` | `column_order` | `(assignment_tick_present,episode_progress_fraction)` | `actor_visible` | `finalized_row_class_and_episode_progress` | `exact_actor_block_15_snapshot_stored_once_without_actor_identity` |
| 15 | `local_robot_mask` | `("M",)` | `torch.bool` | `torch.float32` | `global_robot_id_ascending` | `()` | `critic_only` | `final_merged_local_set_robot_membership` | `tick_result_else_all_false` |
| 16 | `local_task_mask` | `("N",)` | `torch.bool` | `torch.float32` | `global_task_id_ascending` | `()` | `critic_only` | `final_merged_local_set_task_membership` | `tick_result_else_all_false` |
| 17 | `owner_added_robot_mask` | `("M",)` | `torch.bool` | `torch.float32` | `global_robot_id_ascending` | `()` | `critic_only` | `one_round_owner_expansion_attribution` | `tick_result_else_all_false` |
| 18 | `local_set_flags` | `(2,)` | `torch.bool` | `torch.float32` | `column_order` | `(overlap_merged,overflowed)` | `critic_only` | `final_merged_local_set_flags` | `tick_result_else_all_false` |
| 19 | `termination_reason_one_hot` | `(4,)` | `torch.bool` | `torch.float32` | `column_order` | `(NONE,ALL_TASKS_COMPLETED,NO_FEASIBLE_TASKS_REMAIN,TIME_LIMIT)` | `critic_only` | `pre_reset_finalized_lifecycle_transition_result` | `exact_one_hot_for_same_transition` |

shared state 包含全部 robot physical/lifecycle、全部 task pose/lifecycle、完整 ownership、
failed/path/cost matrices、assignment opportunity/DVM、current workload/progress、local set 和
termination context。它不含 proposal 或 same-tick effective outcome。terminal snapshot 可携带
非 `NONE` reason，但此时 action masks 全 false、DVM false，并且不存在 actor storage row、
proposal、resolver consumption 或 commit。

`termination_reason_one_hot` 的唯一 source 是同 transition、pre-reset finalized
`LifecycleTransitionResult.termination_reason`。DirectMARLEnv auto-reset 后的新 episode
observation 不得把上一 transition terminal reason 静默改为 `NONE`。未来 B0/C transport 必须
提供 pre-reset terminal shared-state sidecar，并先把该 terminal row 交给 critic buffer；reset
state 是新 `episode_generation` 的初始 row、reason 为 `NONE`。如果 repo-local runner 无法同时
保持该边界，必须 typed fail-closed 并停在 runtime gate，不能从 reset 后 state 反推。

terminal semantic shared sidecar 的 physical/lifecycle/a0/failed/workload/progress 使用 finalized
pre-reset state；tick path/cost value 全零且 path-valid false，local blocks 全 false，
`assignment_tick_present=false`，target/noop/available masks 全 false，DVM false。它不继承
ordinary no-tick 的 current-task/noop legal action，不产生 forced action。`bad_transition` 仍由
critic mask/transport sidecar 处理，不新增 policy feature。

terminal sidecar 虽无 action/storage row，仍必须先写入 critic buffer，再处理 environment reset
和新 episode initial row；不得从 autoreset 后 observation 反推上一 episode terminal state。
这里“先写入”是将 sidecar 作为同一末端 physical transition 的 finalized pre-reset
critic boundary/next-state slot，不是额外创建一个 physical transition、action row 或独立
critic-loss sample。

`shared_schema.terminal_shared_state_contract` exact 15-key order/value：

```text
contract_version: event_gated_terminal_shared_state_v1
source_snapshot: finalized_pre_reset_transition
physical_lifecycle_a0_state: finalized_pre_reset_physical_lifecycle_a0_failed_workload_progress
termination_reason_source: LifecycleTransitionResult.termination_reason
assignment_tick_present: false
path_cost_blocks: zero_value_and_false_validity
local_set_blocks: all_false
semantic_action_masks: all_false
decision_valid: false
storage_row_present: false
policy_proposal_present: false
forced_nondecision_present: false
pre_reset_sidecar_required: true
reset_state_alias_forbidden: true
critic_buffer_ordering: terminal_sidecar_before_new_episode_initial_row
```

`shared_schema.excluded_fields` 是 exact 17-item ordered tuple，即 actor 的 exact 15 项后
只追加下列两项：

```text
nearest_or_local_task_repacking
local_robot_or_task_renumbering
previous_low_level_action
attempt_count_or_age
same_target_or_repeated_assignment_history
contract_c_budget_state
private_mutation_detector_or_capability
raw_record_ids_or_generation_counters
raw_event_payload
policy_proposal
proposal_log_probability
proposal_acceptance_or_rejection
same_tick_resolver_result
same_tick_effective_assignment
future_execution_facts
actor_identity_one_hot
duplicated_actor_observation_concat
```

这些 exclusion names 只是 deterministic descriptor identity，不会把对应值重新加入
shared observation。

semantic `[E,S]` 的唯一构造 owner 是未来 event schema builder；沿 agent axis 的 repeat 由
HARL transport adapter 拥有，repetition 不进入 fingerprint 的 semantic dimension。当前
wrapper 的 `[E,S] -> [E,M,S]` 只是 transport precedent，不是 schema identity 复用。新的
`runner_transport_mode` literal 必须进入 shared/V3 fingerprint；只是 `M*S` element count 不
能冒充 semantic dimension `S`。

## 7. Actor/shared dimension formulas and M=3,N=50 example

Actor 每 block 维度：

```text
M
+ 16M
+ 5M
+ 7N
+ 6N
+ N(M+1)
+ M(N+1)
+ MN
+ MN
+ MN
+ MN
+ M
+ 5M
+ M
+ 2

actor_obs_dim(M,N)
= 6MN + 30M + 14N + 2

actor_obs_dim(3,50)
= 6*3*50 + 30*3 + 14*50 + 2
= 1692
```

Shared state 先取 actor blocks 2--15，即 `actor_obs_dim - M`，再追加
`local_robot(M) + local_task(N) + owner_added(M) + flags(2) + reason(4)`：

```text
shared_obs_dim(M,N)
= actor_obs_dim(M,N) - M + M + N + M + 2 + 4
= 6MN + 31M + 15N + 8

shared_obs_dim(3,50)
= 6*3*50 + 31*3 + 15*50 + 8
= 1751
```

```text
actor block count:
  15

shared block count:
  19

action dimension:
  A = N + 1 = 51 when N=50

semantic shared dimension:
  S = 1751

runner-facing repeated tensor:
  [E,3,1751]
```

`[E,3,1751]` 的总 element count 不是 shared semantic dimension，不能写成 checkpoint
schema dimension。

row presence 不改变 schema width：ordinary forced row 仍使用 1692D actor/1751D shared
layout；terminal 没有 actor action/storage row，但其 critic pre-reset sidecar 仍是 1751D semantic
shared state。该区分不改变 15/19 blocks、dimension formulas 或 `1692/1751`。

## 8. Contract-C primitive reuse and explicit exclusions

| Existing Contract-C/raw block | Event treatment | Exact reason |
|---|---|---|
| self base/scanner position, yaw, quaternion, capability | reshape/globalize primitive | 变为 global robot table；不继承 raw order/identity |
| nearest-8 viewpoint slots | replace | 距离重排且丢失 global task row identity |
| other-scanner relative positions | replace | global robot table 已按 fixed robot ID 表示 |
| previous 9D low-level action | exclude | execution history，不是 frozen high-level MRTA state |
| per-task relative position/quaternion | reshape/globalize | global task pose 与 global robot pose 分开存储 |
| covered flag/vector | replace | six-state task lifecycle 是唯一 event identity |
| available/feasible/static flags | replace | path-valid + event target mask 拥有新 legality identity |
| Euclidean selected path cost | replace | 不是 expected-time nominal remaining cost |
| attempted count/last-attempt age | exclude | legacy shaping/history，不属于 frozen method state |
| `self_active_target` | replace | 完整 global `a0` assignment table |
| `task_owned_by_teammate` | replace | 完整 global ownership table |
| `self_pair_failed_or_released` | replace | permanent failed pair 与 transient release 不得合并 |
| previous assignment one-hot | replace | current authoritative `a0`，历史 proposal 不可冒充 |
| same-target/repeated/no-progress history | exclude | 未被 event MRTA 方法冻结 |
| per-robot completed count | globalize primitive | 只保留 normalized authoritative completion workload |
| episode progress | reuse primitive once | fixed physical-step/time-limit context |
| Contract-C critic budget 2M | exclude | budget release 不是 structural failure/lifecycle authority |
| Contract-C shared actor concat | replace | event centralized facts 每项只存一次 |

结论：可复用的是 pose/capability/progress 等 primitive value source，而不是 Contract-C
actor/shared schema version、field order、dimension、mask 或 budget semantics。

## 9. Canonical unresolved-parameter owner vocabulary

未来 `assignment_event_profile_schema_contract.py` 定义单一 typed enum：

```python
class UnresolvedParameterOwner(str, Enum):
    PHASE_B_RUNTIME = "phase_b"
    PHASE_D_REWARD = "phase_d"
    PHASE_E_EVALUATION = "phase_e"
    PHASE_B_RUNTIME_AND_PHASE_E_EVALUATION = "phase_b_e"
    PHASE_D_REWARD_AND_PHASE_E_EVALUATION = "phase_d_e"
```

责任边界：

- `phase_b`：runtime algorithm/cap/scheduler 必须在 Phase B 实现前具体化并验证；
- `phase_d`：reward/termination runtime 必须在 Phase D 接入前具体化；
- `phase_e`：只由 evaluation/ablation 选择的量；
- `phase_b_e`：Phase B 给出可执行值，Phase E 对其做消融/最终确认；
- `phase_d_e`：Phase D 给出 reward 可执行值，Phase E 做消融/最终确认。

允许的 multi-stage owner 只有 enum 中显式列出的联合值；不接受自由字符串、任意阶段集合
或 `A/B/E` 的静默转换。Phase A 只冻结 identity，不是 numeric owner。

现有 `UnresolvedParameterSpec.owner_phase` 仍是 exact `str`。domain descriptor 保存 enum 的
canonical serialized value；高层 aggregate 用 `UnresolvedParameterOwner(value)` 验证，并在
需要构造 DTO 时写入 `.value`。lower-level domain module 不反向 import 高层 enum，因而不
破坏第 18 节 DAG；canonical vocabulary 的唯一 public typed owner 仍是 event-profile schema
module。不改变旧 DTO field type/schema version。checkpoint-ready builder 必须由 owner phase
将每个 unresolved spec 替换为合法 concrete value；interface descriptor 只能保留 unresolved
identity，不能用于 weight I/O。

## 10. Ordered unresolved-parameter inventory

完整 inventory 恰好 11 项，顺序如下；没有第 12 项。

| # | `name` | `owner_phase` | Exact `semantic_purpose` | Exact `expected_concrete_type` | Exact `unit` | Exact `legal_domain` | Unique triple owner |
|---:|---|---|---|---|---|---|---|
| 1 | `top_k_tasks_per_robot` | `phase_b_e` | `maximum_nominal_cost_ranked_tasks_per_local_robot_before_current_task_retention` | `exact_int` | `tasks_per_robot` | `1 <= value <= N` | MRTA/local-candidate |
| 2 | `local_robot_cap` | `phase_b` | `maximum_robots_in_merged_local_assignment_set` | `exact_int` | `robots` | `1 <= value <= M` | MRTA/local-candidate |
| 3 | `local_task_cap` | `phase_b` | `maximum_tasks_in_merged_local_assignment_set` | `exact_int` | `tasks` | `1 <= value <= N` | MRTA/local-candidate |
| 4 | `pair_abs_threshold` | `phase_b_e` | `strict_absolute_expected_time_improvement_for_active_preemption` | `finite_float` | `expected_time_seconds` | `value >= 0` | MRTA/component |
| 5 | `pair_rel_threshold` | `phase_b_e` | `strict_relative_expected_time_improvement_for_active_preemption` | `finite_float` | `dimensionless_ratio` | `0 <= value < 1` | MRTA/component |
| 6 | `component_abs_threshold` | `phase_b_e` | `strict_absolute_expected_time_improvement_for_equal_count_component_acceptance` | `finite_float` | `expected_time_seconds` | `value >= 0` | MRTA/component |
| 7 | `component_rel_threshold` | `phase_b_e` | `strict_relative_expected_time_improvement_for_equal_count_component_acceptance` | `finite_float` | `dimensionless_ratio` | `0 <= value < 1` | MRTA/component |
| 8 | `transfer_penalty` | `phase_b_e` | `expected_time_regularizer_per_owner_change_in_equal_count_component_objective` | `finite_float` | `expected_time_seconds_per_owner_change` | `value >= 0` | MRTA/component |
| 9 | `rejection_penalty_scale` | `phase_d_e` | `once_per_penalty_eligible_rejected_component` | `finite_float` | `team_reward_units_per_rejected_component` | `value >= 0` | team-reward |
| 10 | `alignment_time_constant` | `phase_b_e` | `robot_specific_expected_terminal_alignment_time` | `tuple_finite_float_len_M` | `expected_time_seconds_per_robot_entry` | `len(value) == M AND all entries finite and >= 0 AND tuple index i == global robot_id i` | MRTA/cost-path |
| 11 | `assignment_retry_cadence` | `phase_b` | `physical_step_interval_for_persistent_unassigned_retry_opportunities` | `exact_int` | `physical_transitions` | `value >= 1` | event/opportunity |

type literals 的 validator 语义也冻结：`exact_int` 要求 `type(value) is int`（排除 bool）；
`finite_float` 要求 `type(value) is float` 且 finite；`tuple_finite_float_len_M` 要求 exact tuple、
长度 M、每项 `type(entry) is float` 且 finite。合法域在 type validation 后应用。

authority 按字段拆分且不重叠：domain descriptor 唯一拥有
`(name, owner_phase, semantic_purpose)` triple 及领域方程；event-profile aggregate 唯一拥有
11-item global order 和 checkpoint value contract metadata
`(expected_concrete_type, unit, legal_domain)`。这允许 reward descriptor 保持 v1：其现有
triple 继续 authoritative，而 synthetic oracle 的 int/float test acceptance 不成为 future
checkpoint concrete-type authority。

aggregate exact ordered keys：

```text
contract_version
owner_enum_order
triple_field_order
reference_record_field_order
unresolved_parameter_order
unresolved_parameter_references
```

`contract_version` 的 exact value 是
`event_gated_unresolved_parameter_inventory_v1`。
`triple_field_order` 的 exact value 为
`(name, owner_phase, semantic_purpose)`。

每个 `unresolved_parameter_references` record 的 exact field order：

```text
name
triple_owner_module
triple_owner_contract_version
triple_descriptor_key_path
expected_concrete_type
unit
legal_domain
```

exact 11 references：

| # | Name | Canonical triple-owner module / contract version | Exact descriptor key path |
|---:|---|---|---|
| 1 | `top_k_tasks_per_robot` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `local_candidate_semantics.unresolved_parameters[0]` |
| 2 | `local_robot_cap` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `local_candidate_semantics.unresolved_parameters[1]` |
| 3 | `local_task_cap` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `local_candidate_semantics.unresolved_parameters[2]` |
| 4 | `pair_abs_threshold` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `component_semantics.unresolved_parameters[0]` |
| 5 | `pair_rel_threshold` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `component_semantics.unresolved_parameters[1]` |
| 6 | `component_abs_threshold` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `component_semantics.unresolved_parameters[2]` |
| 7 | `component_rel_threshold` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `component_semantics.unresolved_parameters[3]` |
| 8 | `transfer_penalty` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `component_semantics.unresolved_parameters[4]` |
| 9 | `rejection_penalty_scale` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_team_reward_contract` / `assignment_team_reward_contract_v1` | `unresolved_parameter` |
| 10 | `alignment_time_constant` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_mrta_contract` / `assignment_mrta_contract_v2` | `cost_path_semantics.unresolved_parameters[0]` |
| 11 | `assignment_retry_cadence` | `isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_contract` / `assignment_event_contract_v2` | `scheduled_assignment_opportunity_semantics.unresolved_parameter` |

aggregate 按 path 解引用，并按 `triple_field_order` 从 domain mapping 提取三个 authoritative
字段、解析 typed owner enum、逐字段 equality-check。未来 MRTA/event v2 新 entry 必须是 exact
three-key mapping；现有 reward v1 `unresolved_parameter` 保持其既有五键 mapping
`(name, owner_phase, semantic_purpose, required_type, numeric_value_selected)`，不得为满足 aggregate
而修改/bump。reward 的两个额外字段仍由 reward v1 拥有，但不替代 aggregate-owned concrete
value metadata。module/version/path、global order、提取后的 triple 或 aggregate-owned
`expected_concrete_type/unit/legal_domain` 任一漂移都改变 future fingerprint；aggregate 不复制
domain triple。

特殊语义：

- `alignment_time_constant[i]` 是无 real pair estimator 时的 robot-specific seconds fallback，
  广播成 `[M,N]` alignment matrix；它属于 cost/path，不属于 observation parameter；
- `assignment_retry_cadence` 以 finalized physical `transition_generation` delta 计数，不能用
  assignment tick 计数，否则形成“依赖 tick 才能生成 tick”的循环。独立 event 可以提前触发；
- `transfer_penalty` 只进入 equal-count component objective `Jp`，不进入 Top-K、pair nominal
  cost 或 reward；
- `rejection_penalty_scale` 只在 wrapper-final mean 之后按唯一 penalty-eligible component
  扣一次，再 broadcast。它与 transfer penalty 的单位和 owner 均不同。

event v2 还应唯一拥有
`event_gated_scheduled_assignment_opportunity_semantics_v1`，ordered keys 为
`(projection_version, unresolved_parameter, counter_source, unit,
persistent_unassigned_equation, anchor_initialization_rule, anchor_refresh_rule,
due_equation, retry_generation_rule, lifecycle_early_trigger_rule,
unavailable_terminal_suppression,
output_record_schema)`。精确 scheduler 语义：

```text
persistent_unassigned[e,i]
== current_assignment[e,i] == NO_TASK
   AND robot_state[e,i] in {NEEDS_ASSIGNMENT, WAITING_FOR_TASK}
   AND robot_available[e,i]
   AND not terminal[e]

retry_due[e,i]
== same_episode_as_anchor
   AND persistent_unassigned[e,i]
   AND transition_generation[e] - retry_anchor_transition_generation[e,i]
       >= assignment_retry_cadence
```

anchor 在 robot 首次进入 persistent-unassigned 时初始化；任何包含该 robot 的 assignment
tick 结束后若仍 persistent-unassigned，则刷新为该 finalized physical transition generation。
独立 lifecycle event 可在 cadence 到期前触发 tick，并遵循同一 refresh；assigned、unavailable、
terminal 或 episode reset 使旧 anchor 失效。到期输出现有
`AssignmentOpportunityRecord(ASSIGNMENT_RETRY_DUE)`，不得新增 lifecycle event type。
`retry_generation` 是每个 `(env_id, episode_generation, robot_id)` 的 episode-local emitted-retry
序号：episode/reset 时从 0 重新开始，首条 emitted due opportunity 取 0，之后每实际发出一条才
+1；early lifecycle tick 不产生 retry record、因而不增加它。association 同时包含
`episode_generation`，所以 reset 后的 0 不与上一 episode alias。

`event_retry_cadence` 是旧别名，禁止；`lambda_align` 被 authoritative design 禁止；real
navigation/alignment estimators 与 baseline adapters 是 implementation-evidence-TBD，不是
numeric-TBD；gamma/lambda/lr 等 config binding 也不进入这 11 项。

## 11. Local-candidate semantic projection

唯一 owner：未来 `assignment_mrta_contract_v2` 的
`local_candidate_semantics`。projection version：
`event_gated_local_candidate_semantics_v1`。exact ordered keys：

```text
projection_version
seed_sources
seed_robot_mask_equation
trigger_record_robot_rule
forbidden_trigger_records
candidate_prefilter_order
candidate_eligibility_equation
top_k_sort_order
occupied_task_candidate_rule
current_task_retention_rule
owner_expansion_rounds
owner_expansion_equation
second_layer_owner_recursion
outside_set_owner_preemption_rule
overlap_identity
overlap_merge_rule
post_merge_recomputation_order
post_merge_owner_expansion
global_robot_identity
global_task_identity
local_observation_repacking
overflow_behavior
request_result_association_key
unresolved_parameters
```

冻结方程和顺序：

```text
seed_robot_mask[e,i]
= needs_assignment_mask[e,i]
  OR any trigger-eligible LifecycleEventRecord with robot_id == i
  OR any AssignmentOpportunityRecord with robot_id == i
```

只有 finalized lifecycle event 和 scheduled opportunity 可 seed；
`ResolverDiagnosticRecord` 永不 seed。task-related event 的 robot attribution 必须使用其
canonical record/payload cause binding，不能由 wrapper 猜测。

为消除 cost/Top-K/owner-expansion 循环，单个 assignment tick 的 exact staged order 是：

1. capture 一份 immutable fact-updated physical/lifecycle snapshot；
2. derive seed rows；对每个 seed 的全部 global task pair 至多估计一次并写入 tick-local cache；
3. seed candidate prefilter/Top-K/current retention；
4. 从 seed Top-K occupied tasks 做唯一一轮 owner expansion；
5. 对新增 owner 尚未 cache 的 pair 各估计一次，生成其 Top-K/current retention；
6. 形成 preliminary sets，按 overlap relation transitive merge；
7. 补齐 cache 中尚未计算的所有 global `[M,N]` cells，每个 pair 整个 tick 恰好估计一次；
8. 由 cache 一次性 finalize 唯一 `NominalPairCostResult`；
9. 对 final merged memberships 从该 finalized result 重算 Top-K/current retention、
   available actions 和 DVM；不得重新 owner expansion。

candidate prefilter 顺序是：global task valid；task 不为 `COMPLETED`/
`TEAM_INFEASIBLE`；pair 未 permanent failed；final/partial cache 中对应 path valid。occupied task
不在 Top-K 前过滤。按 `(nominal_cost ASC, global_task_id ASC)` deterministic 排序并取
unresolved K；event-updated baseline 中仍合法的 current task无论 rank 都追加为 CONTINUE。

第一轮：

```text
owner_added
= owners(seed Top-K 中 occupied tasks) minus seeds
```

新增 owner 生成自己的 Top-K/current retention；只做一轮。新 owner Top-K 中由集合外
owner 占有的 task 可以保留为 candidate fact，但本 tick preemption mask 必须为 false，且
不得再递归加入 owner。

任意 preliminary set 的 robot mask 或 task mask 有交集即建立 overlap relation；按该关系
transitive closure 合并。所有 partial/final ranking 都消费同一 tick cache；已有 pair 禁止重估，
因此不存在 `bitwise/contract-equal` 二选一。global robot/task ID 始终保留，不构造 local
observation。

cap 对最终 merged set 生效；overflow exact behavior 为
`FAIL_CLOSED_NO_ASSIGNMENT`，DVM 全 0、baseline 不变并产生非 policy diagnostic，不允许静默
截断或可选 safe mode。

`LocalSetRequest`/`LocalSetResult` 的未来 row association key 精确为：

```text
(env_id, episode_generation, transition_generation, assignment_tick_generation)
```

前提是每 env/tick 只存在一个 canonical merged request/result；无需给现有 DTO 加 nonce，
但 A3x-1 descriptor/test 必须冻结 exact equality 和唯一性 obligation。

## 12. Cost/path semantic projection

唯一 owner：未来 `assignment_mrta_contract_v2` 的 `cost_path_semantics`。projection version：
`event_gated_cost_path_semantics_v1`。exact ordered keys：

```text
projection_version
cost_unit
tensor_shapes
tensor_dtypes
cost_generation_key
refresh_rule
snapshot_consistency_rule
navigation_cost_semantics
alignment_cost_semantics
nominal_cost_equation
current_owner_navigation_rule
current_owner_alignment_rule
nonowner_cost_rule
alignment_fallback_rule
unresolved_parameters
path_valid_authority
valid_pair_rule
invalid_path_encoding
finite_invalid_sentinel_allowed
top_k_penalty_rule
pair_gate_cost_source
component_penalty_scope
```

冻结接口：

```text
cost unit:
  expected_time_seconds

navigation_cost, alignment_cost, nominal_cost:
  [E,M,N] torch.float32

nominal_path_valid:
  [E,M,N] torch.bool

nominal_cost[e,i,j]
= navigation_cost[e,i,j] + alignment_cost[e,i,j]
```

所有 cost 使用第 11 节 staged order 和同一 fact-updated immutable snapshot，并绑定 local
association 四元组。tick-local cache 每个 `[i,j]` 至多写一次；finalized full `[M,N]`
`NominalPairCostResult` 只生成一次，之后 Top-K/mask/resolver 全只读，不能读取后续 physical
state，也不存在 pair 重估/equality fallback。

canonical naming/mapping：cost DTO 的 authority field 是
`NominalPairCostResult.path_valid`；assignment-tick observation block 是其 float-concat 前的
exact bool copy `assignment_tick_nominal_path_valid_mask`；DVM snapshot field
`nominal_path_valid_mask` 在同 generation 也必须 exact equal。三者是一个 source 的 typed
projection，不是三个 validity authority。ordinary nonterminal no-tick 与 terminal observation
都按 §5.5 明确置零且不创建 cost/local-set/DVM tick snapshot；前者的一动作仅属于 forced
historical storage mask，后者为 zero-action semantic no-row，不能把二者都称作 DVM
no-opportunity row。

current owner 的设计选择已精确化：若 task 尚在 `NAVIGATING`，navigation 是从当前
execution state 到 terminal alignment region 的 remaining expected seconds；若已在
`ALIGNING`，navigation 必须为 0，alignment 是 remaining expected terminal alignment
seconds。nonowner 从其当前 physical state估计完整 navigation 与 pair-specific alignment。
无 pair alignment estimator 时，用 `alignment_time_constant[i]` seconds 广播 over j。

path-valid 由 cost/path estimator authority 唯一给出。valid pair 的三项 cost 都 finite、
nonnegative 且严格满足 sum；invalid pair 的三项全部 canonical NaN。禁止任意大有限
sentinel。Top-K 不含 transfer/switch penalty；pair gate 使用 nominal remaining cost；
`transfer_penalty` 只进入完整 equal-count component `Jp`。

real remaining-time/route/alignment estimator identity 与 runtime evidence 仍 deferred；A3x-1
只冻结接口和 fallback reference，不能把当前 Euclidean distance 认证为 expected time。

## 13. Component semantic projection

唯一 owner：未来 `assignment_mrta_contract_v2` 的 `component_semantics`。projection version：
`event_gated_component_semantics_v1`。exact ordered keys：

```text
projection_version
baseline_a0_identity
component_scope
proposal_source
contention_order
contention_loser_rule
component_closure_rule
whole_component_outcome
partial_policy_acceptance_rule
covered_continue_override_rule
assigned_unfinished_count_equation
assigned_count_gate
active_preemption_definition
pair_improvement_equations
pair_gate_conjunction
baseline_cost_equation
staged_cost_equation
owner_change_count_equation
count_increase_rule
count_equal_improvement_equations
count_decrease_rule
canonical_rejection_order
nonpolicy_rejection_reasons
policy_penalty_attribution_rule
penalty_unit_equation
invariant_failure_rule
forbidden_resolver_behaviors
unresolved_parameters
```

`a0` 精确等于唯一 lifecycle authority 在 completion/release/failure/availability/
`TEAM_INFEASIBLE` 后 finalized 的 `LifecycleTransitionResult.updated_ownership`。其全局 mutual
inverse 必须按下式唯一构造，resolver 前只读：

```text
a0_assignment[i]
= unique global task j for which a0_ownership[j] == i, otherwise -1

fail closed if more than one global task maps to robot i
fail closed if a0_assignment and a0_ownership are not mutual inverses
for each member robot i with a0_assignment[i] >= 0:
  member_task_mask[a0_assignment[i]] must be true
outside-component baseline assignment and ownership remain unchanged
```

同 task contention 顺序：non-preemptible current owner；hard/pair legal；improvement
descending；new nominal cost ascending；robot ID ascending。loser reason 为
`CONTENTION_LOSS`；winner component 后续失败时不提升 runner-up、不重建 subset。

每个 connected transfer component 全接受或全拒绝。accepted component 中 CLAIM、SWITCH、
NOOP policy rows 不得部分拒绝；唯一 covered exception 是 current-owner CONTINUE：当另一
accepted member 提议并有效接管同一 task 时，该 CONTINUE 可
`proposal_accepted=false, effective_assignment=-1`。除此以外 partial outcome 非法。

```text
assigned_count(a)
= sum_j 1[member_task_mask[j]
          AND event-updated task j is unfinished
          AND owner_a[j] >= 0]

active_preemption(i,j)
= member_task_mask[j]
  AND event-updated task j is unfinished
  AND a0_owner[j] >= 0
  AND staged_owner[j] == i
  AND i != a0_owner[j]
```

每条 active preemption 同时满足：

```text
C(a0_owner[j],j) - C(i,j) > pair_abs_threshold

C(i,j) < (1 - pair_rel_threshold) * C(a0_owner[j],j)
```

component cost：

```text
J0
= sum_j 1[member_task_mask[j]
          AND event-updated task j is unfinished
          AND a0_owner[j] >= 0]
        * C(a0_owner[j], j)

N_owner_changes
= sum_j 1[member_task_mask[j]
           AND event-updated task j is unfinished
           AND a0_owner[j] >= 0
           AND staged_owner[j] >= 0
           AND staged_owner[j] != a0_owner[j]]

Jp
= sum_j 1[member_task_mask[j]
          AND event-updated task j is unfinished
          AND staged_owner[j] >= 0]
        * C(staged_owner[j], j)
  + transfer_penalty * N_owner_changes
```

`J0`/`Jp` 只对 component member tasks 求和；`Jp` 只消费通过 hard/pair/closure/
uniqueness 检查后的 staged ownership。任一 component 外 task/robot 被 staging 改写，或任一
member unfinished task 的所需 nominal pair cost 无效，均 fail closed，不能把它从求和中静默
省略。

unowned claim 和 forced-release-after-`a0=-1` claim 都计 0 transfer；two-task bilateral swap
计 2。count increase 仍须 hard/pair/closure/uniqueness/atomic staging 全通过；count equal
还须：

```text
J0 - Jp > component_abs_threshold
Jp < (1 - component_rel_threshold) * J0
```

count decrease 拒绝；forced lifecycle release 已在 a0 中，不属于 proposal decrease。

canonical first-reason order 原样冻结：

```text
NONE
CONTENTION_LOSS
INCOMPLETE_TRANSFER_CHAIN
OWNERSHIP_COORDINATION_INVALID
PREEMPTION_INELIGIBLE
ASSIGNED_UNFINISHED_COUNT_DECREASE
PAIR_IMPROVEMENT_NOT_MET
COMPONENT_IMPROVEMENT_NOT_MET
LOCAL_SET_OVERFLOW_FAIL_CLOSED
POST_SNAPSHOT_SYSTEM_INVALIDATION
TERMINAL_TRANSITION
```

snapshot/generation/mask 稳定时，前七个非-NONE ordinary rejection 为
`(policy_caused, penalty_eligible, penalty_unit_count)=(true,true,1)`；最后三个为
`(false,false,0)`。generation mismatch、历史 mask 不一致、duplicate ownership、half mutation
等 implementation invariant 必须 typed fail-fast，不能伪装成 learning rejection。

resolver 仍禁止 matching/search、proposal subset、second candidate、runner-up promotion、
policy 未提出任务和顺序半提交。本 projection 不实现 graph/objective/commit。

## 14. Failure/termination semantic projection

这里确认存在：

```text
STATE ENUM OWNER GAP
```

A3x-1 应由 `assignment_lifecycle_transition_contract.py` 唯一新增 public enums 和
`event_gated_failure_termination_semantics_v1` projection。task/robot exact numeric order：

```text
TaskLifecycleState(IntEnum):
  AVAILABLE = 0
  CLAIMED = 1
  NAVIGATING = 2
  ALIGNING = 3
  COMPLETED = 4
  TEAM_INFEASIBLE = 5

RobotLifecycleState(IntEnum):
  EXECUTING = 0
  NEEDS_ASSIGNMENT = 1
  WAITING_FOR_TASK = 2
  UNAVAILABLE = 3
```

`ROBOT_RECOVERED` 仍是 transient lifecycle event，不进入 robot state enum。现有
`TerminationReason` order/value 保持：

```text
NONE = 0
ALL_TASKS_COMPLETED = 1
NO_FEASIBLE_TASKS_REMAIN = 2
TIME_LIMIT = 3
```

failure/termination projection exact ordered keys：

```text
projection_version
task_state_enum_order
robot_state_enum_order
transient_event_exclusion
termination_reason_order
failed_pair_source
new_failed_pairs_equation
updated_failed_pairs_equation
failed_pair_episode_reset_rule
team_infeasible_equation
new_team_infeasible_equation
path_invalid_non_equivalence
terminal_task_ownership_release_rule
event_updated_baseline_order
termination_priority
physical_terminal_mapping_boundary
bad_transition_boundary
unmappable_physical_terminal_rule
terminal_assignment_rule
episode_generation_rule
transition_generation_rule
assignment_tick_generation_rule
```

```text
new_failed_pair
= terminal_pair_failure_signal AND NOT cumulative_failed_before

updated_failed_pair
= cumulative_failed_before OR new_failed_pair

TEAM_INFEASIBLE(j)
= task j not COMPLETED AND all_i updated_failed_pair[i,j]

new_team_infeasible(j)
= NOT prior_team_infeasible[j]
  AND event-updated task j is not COMPLETED
  AND all_i updated_failed_pair[i,j]
```

cumulative failed pair 只在 episode reset 清零；path-valid 全 false 不等价于
`TEAM_INFEASIBLE`。`COMPLETED` 优先于 infeasible 推导。两类 terminal task 的 ownership
都必须在形成 a0 前 release；`new_team_infeasible_tasks` 精确等于上式为 true 的 task IDs，
只表示本 transition delta。episode reset 必须从新 episode authoritative initial facts 重建
task state、robot state、ownership、assignment、failed-pair cumulative snapshot、retry anchors 和
termination state；上一 episode 的任何 lifecycle/MRTA state 均不得 carry over。

termination priority：all completed；否则 all tasks in completed/team-infeasible；否则 time
limit；否则 NONE。raw physical flags 只定义 mapping boundary：derived all-task reason 可以由
authority 形成；time-limit 映射 TIME_LIMIT。若 `physical_terminated OR physical_truncated`
最终仍为 NONE，或存在不受支持的 non-time-limit truncation/bad-transition boundary，则 typed
fail-closed，DVM 全 0、无 proposal、无 commit；不得发明第五个 reason。`bad_transition` 只作
bootstrap/transport fact。

`terminal_assignment_rule` 精确引用 §5.5/§6：terminal target/noop/available masks 全 false，
semantic count 0，forced ID `-1`，无 actor sampling、action/log-prob storage、proposal、forced
nondecision、resolver 或 component；唯一保留的是 finalized pre-reset critic shared sidecar。

generation 规则：episode generation 每 reset +1；transition generation per env 在 process
lifetime 单调增加、不因 reset 回零；assignment tick generation 同样 per env process-lifetime
单调。每次真正形成一个 canonical merged assignment tick 时恰好 +1，无论它由 lifecycle
event、retry opportunity 或二者合并触发；同一 physical transition 的重叠触发只形成一个 tick
和一次增量。无 tick 的 physical step 不增加。`AssignmentOpportunityRecord` 和本 tick 全部
request/result 使用该新增后的同一 tick generation。任何 stale/duplicate/future association
fail-fast；retry generation 另按 §10 的 episode-local per-robot 规则。

## 15. Model-structure semantic projection

唯一 owner：新 `assignment_event_profile_schema_contract.py` 中
`event_gated_model_structure_projection_v1`。exact ordered keys：

```text
projection_version
projection_status
actor_class
critic_class
action_distribution_class
actor_input_schema_version
actor_input_dimension_source
critic_input_schema_version
critic_input_dimension_source
action_dimension_formula
actor_hidden_sizes
critic_hidden_sizes
activation
feature_normalization
share_param
number_of_actor_networks_formula
ordered_actor_network_names_source
critic_architecture
harl_state_type
use_recurrent_policy
use_naive_recurrent_policy
recurrent_n
initialization_method
action_gain
serialization_mode
save_entire_model
state_dict_key_contract_version
state_dict_inventory_binding
```

exact proposed current-config projection：

| Field | Value/binding | Evidence status |
|---|---|---|
| `projection_status` | `interface_identity_only_not_runtime_verified` | frozen |
| actor | HAPPO `StochasticPolicy` | current route identity |
| critic | `VCritic`/centralized V network | current route identity |
| distribution | discrete `Categorical` | action contract `N+1` |
| actor input | actor schema version + dimension section reference | frozen reference |
| critic input | shared schema version + dimension section reference | frozen reference |
| hidden sizes | actor `(256,256)`, critic `(256,256)` | actual assignment runner projection |
| activation/normalization | `relu`, feature normalization true | config-bound current identity |
| parameter sharing | false; M non-shared actors named by ordered agents | A1 identity |
| critic/state | centralized V, EP | A1/current route identity |
| recurrent flags | both false; `recurrent_n=1` transport shape only | feed-forward identity |
| initialization | `orthogonal_`, action gain `0.01` | config-bound current identity |
| serialization | `state_dict`, `save_entire_model=false` | frozen identity |
| state-dict inventory | `event_gated_state_dict_inventory_contract_v1`; deferred to checkpoint-ready manifest | no model construction/I/O |

A3x-1 必须序列化下面的 exact typed values，不能从上表 prose 自行改名：

```text
projection_version: event_gated_model_structure_projection_v1
projection_status: interface_identity_only_not_runtime_verified
actor_class: HAPPO/StochasticPolicy
critic_class: VCritic/VNet
action_distribution_class: Categorical
actor_input_schema_version: event_gated_global_actor_observation_v1
actor_input_dimension_source: actor_schema.dimension_formula
critic_input_schema_version: event_gated_global_centralized_observation_v1
critic_input_dimension_source: shared_schema.dimension_formula
action_dimension_formula: action_contract.action_dimension
actor_hidden_sizes: (256, 256)
critic_hidden_sizes: (256, 256)
activation: relu
feature_normalization: true
share_param: false
number_of_actor_networks_formula: action_contract.num_agents
ordered_actor_network_names_source: scale_contract.ordered_agent_names
critic_architecture: centralized_v_network
harl_state_type: EP
use_recurrent_policy: false
use_naive_recurrent_policy: false
recurrent_n: 1
initialization_method: orthogonal_
action_gain: 0.01
serialization_mode: state_dict
save_entire_model: false
state_dict_key_contract_version: event_gated_state_dict_inventory_contract_v1
state_dict_inventory_binding: deferred_checkpoint_ready_manifest
```

这里的 reference fields 不产生第二 authority：`actor_input_*`/`critic_input_*` 分别引用
actor/shared schema 中实际存在的 `dimension_formula` key，并用同一
`scale_contract.M/N` 求值；`action_dimension_formula` 引用 MRTA-owned action value；
`ordered_actor_network_names_source` 引用 scale contract；`harl_state_type`、
`share_param`、两个 recurrent flags、`serialization_mode`、`save_entire_model` 必须与
`resolved_event_profile_mapping.event_gated_target_semantics.training_semantic_contract` 对应字段
exact equal。model projection 唯一拥有的是网络/输入/action/初始化结构以及 deferred
state-dict inventory binding。

YAML 中的 `hidden_sizes_critic: [512,256]` 目前没有被 assignment runner 消费；runner lines
525--526 实际让 actor/critic 都取 `model.hidden_sizes=[256,256]`。本提案选择真实 constructed
route 的结构 identity，避免 A4a fingerprint 一个当前代码不会构造的 critic。它不证明 V2
weights 与 event schema 兼容，也不证明 state-dict keys；若要新 event critic 使用
`(512,256)`，必须作为新的 architecture decision 明确授权，不能在 A3x-1 暗改 runner。
未消费的 `model.hidden_sizes_critic` 值本身不得进入 event interface fingerprint；A3x-1 drift
test 应验证 projection 来源仍是 runner 实际消费的 `model.hidden_sizes`，而不是绑定 unused key。

## 16. Training-contract semantic projection

唯一 aggregate owner：新 event-profile schema module 中
`event_gated_training_contract_projection_v1`。顶层 exact order：

```text
projection_version
algorithm_identity
rollout_return_semantics
optimizer_config_identity
ppo_config_identity
decision_valid_training_contract_ref
sequential_factor_contract_ref
serialization_contract
runtime_evidence_status
```

顶层 `runtime_evidence_status` 的 exact literal 是 `DEFERRED_RUNTIME_EVIDENCE`。该 aggregate
只拥有 section 顺序、config bindings 和 event-specific actor-update/factor references；A1 已
拥有的 training/policy-sequence identity 必须以 canonical key-path reference 投影并 exact
equality-check，不得在新 module 建第二个 semantic authority。

```text
decision_valid_training_contract_ref: event_gated_decision_valid_actor_training_v1
sequential_factor_contract_ref: event_gated_happo_sequential_factor_v1
```

所有 `*_binding` 使用同一 frozen typed record，key order 为：

```text
source_path
expected_type
legal_domain
current_config_value
semantic_status
runtime_evidence_status
```

其中 `semantic_status=CONFIG_BOUND_CURRENT_IDENTITY`，
`runtime_evidence_status=DEFERRED_RUNTIME_EVIDENCE`。current value 是被审计 config 的
snapshot，不是 A3x-0 新选的 paper default；value/config path 变化必须改变 future
fingerprint。

### 16.1 Nested key inventories

本节所有 `resolved_event_profile_mapping.*` key path 的 canonical root 精确指：对
`AssignmentProfileName.EVENT_GATED_LOCAL_MRTA` 的 canonical resolved profile 调用 public
`isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract.
resolved_assignment_profile_to_mapping(...)` 所得 mapping；不得引用 private registry object。

```text
algorithm_identity:
  algorithm_family
  algorithm_name
  state_type
  share_param
  policy_sequence_mode
  use_recurrent_policy
  use_naive_recurrent_policy
  actor_buffer_generator
  installed_harl_mutable

exact values and sources:
  algorithm_family: HAPPO
  algorithm_name: happo
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.algorithm_name
  state_type: EP
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.state_type
  share_param: false
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.share_param
  policy_sequence_mode: event_gated_decision_valid_feed_forward_v1
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            policy_sequence_route
  use_recurrent_policy: false
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.use_recurrent_policy
  use_naive_recurrent_policy: false
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.use_naive_recurrent_policy
  actor_buffer_generator: feed_forward_generator_actor
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.actor_buffer_generator
  installed_harl_mutable: false
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.installed_harl_mutable
```

```text
rollout_return_semantics:
  time_axis
  episode_length_semantics
  episode_length_config_binding
  standard_gae
  use_gae_config_binding
  gamma_config_binding
  gae_lambda_config_binding
  proper_time_limits_config_binding
  critic_reward_source
  critic_return_sample_set
  decision_valid_excluded_from_gae_returns_critic
  valuenorm_enabled_config_binding
  valuenorm_source
  valuenorm_epsilon
```

time axis 是 fixed physical steps；GAE 保持 standard；critic reward 是
`broadcast_team_reward`；critic returns/ValueNorm 使用全部 valid physical steps；DVM 不进入
GAE、return、critic loss 或 ValueNorm。`standard_gae=true` 且必须由
`algo.use_gae` 的 exact-true binding 支持；`gamma`、`gae_lambda`、episode length、
proper-time-limit 和 ValueNorm enabled 只冻结 exact config key/type/domain/current snapshot
binding，不提升为论文 method default。ValueNorm/advantage numerical epsilon 绑定当前
supported literal `1e-5`。

```text
rollout_return_semantics exact non-binding values:
  time_axis: fixed_physical_transitions
  episode_length_semantics: transitions_per_rollout
  standard_gae: true
  critic_reward_source: broadcast_team_reward
  critic_return_sample_set: all_valid_physical_steps
  decision_valid_excluded_from_gae_returns_critic: true
  valuenorm_source: all_valid_physical_step_returns
  valuenorm_epsilon: 0.00001
```

| Rollout/return binding | Source path | Type/domain | Current snapshot |
|---|---|---|---:|
| episode length | `train.episode_length` | exact int, `>=1` physical transitions | `1000` |
| use GAE | `algo.use_gae` | exact bool; event contract requires true | `true` |
| gamma | `algo.gamma` | finite float, `(0,1]` | `0.99` |
| GAE lambda | `algo.gae_lambda` | finite float, `[0,1]` | `0.95` |
| proper time limits | `train.use_proper_time_limits` | exact bool | `true` |
| ValueNorm enabled | `train.use_valuenorm` | exact bool | `true` |

```text
optimizer_config_identity:
  optimizer_family
  actor_learning_rate_binding
  critic_learning_rate_binding
  optimizer_epsilon_binding
  weight_decay_binding

ppo_config_identity:
  ppo_epoch_binding
  critic_epoch_binding
  actor_minibatches_binding
  critic_minibatches_binding
  clip_coefficient_binding
  value_loss_coefficient_binding
  entropy_coefficient_binding
  gradient_clipping_enabled_binding
  max_gradient_norm_binding
  clipped_value_loss_binding
  huber_loss_binding
  huber_delta_binding
  action_aggregation_binding
  fixed_agent_order_binding
  policy_active_masks_binding
```

`optimizer_family` 的 exact literal 为 `Adam`。上述所有 numeric training values 都是
`CONFIG_BOUND_CURRENT_IDENTITY`，不是 11-item method numeric-TBD，也不是 A3x-0 选择的新
hyperparameter。runtime tensor/model/state-dict evidence 仍 deferred。

| Optimizer/PPO binding | Source path | Type/domain | Current snapshot |
|---|---|---|---:|
| actor learning rate | `model.lr` | finite float, `>0` | `0.0005` |
| critic learning rate | `model.critic_lr` | finite float, `>0` | `0.0005` |
| optimizer epsilon | `model.opti_eps` | finite float, `>0` | `0.00001` |
| weight decay | `model.weight_decay` | finite float, `>=0` | `0` |
| PPO epoch | `algo.ppo_epoch` | exact int, `>=1` | `5` |
| critic epoch | `algo.critic_epoch` | exact int, `>=1` | `5` |
| actor minibatches | `algo.actor_num_mini_batch` | exact int, `>=1` | `2` |
| critic minibatches | `algo.critic_num_mini_batch` | exact int, `>=1` | `2` |
| clip coefficient | `algo.clip_param` | finite float, `(0,1)` | `0.2` |
| value-loss coefficient | `algo.value_loss_coef` | finite float, `>=0` | `1` |
| entropy coefficient | `algo.entropy_coef` | finite float, `>=0` | `0.01` |
| gradient clipping | `algo.use_max_grad_norm` | exact bool | `true` |
| max gradient norm | `algo.max_grad_norm` | finite float, `>0` | `10.0` |
| clipped value loss | `algo.use_clipped_value_loss` | exact bool | `true` |
| Huber loss | `algo.use_huber_loss` | exact bool | `true` |
| Huber delta | `algo.huber_delta` | finite float, `>0` | `10.0` |
| action aggregation | `algo.action_aggregation` | exact supported string | `prod` |
| fixed agent order | `algo.fixed_order` | exact bool | `false` |
| policy active masks | `algo.use_policy_active_masks` | exact bool | `true` |

### 16.2 Decision-valid sibling contract

由 event-profile schema module 唯一拥有
`event_gated_decision_valid_actor_training_v1`；MRTA v2 仍唯一拥有 DVM construction mask
facts。exact key order：

```text
contract_version
buffer_mask_shape
training_slice
actor_valid_equation
policy_loss_reduction
entropy_reduction
advantage_population
zero_valid_actor_rule
singleton_advantage_rule
multi_sample_advantage_rule
advantage_std_epsilon
empty_minibatch_rule
rejected_proposal_included
critic_dvm_usage
```

```text
decision_valid_mask buffer shape = [T+1,E,1] per actor
training slice = decision_valid_mask[:-1]
actor_valid = active_mask AND decision_valid_mask
masked_mean(x) = sum(actor_valid*x) / sum(actor_valid)
```

policy loss 与 entropy 都按有效数归一。advantage population 是该 actor 整个 rollout 的
actor-valid samples，不在 minibatch 重算：0 valid 时不 forward/backward/optimizer/factor；
1 valid 时用 finite raw advantage；>=2 时 `unbiased=False` mean/std，std nonfinite 或
`<1e-5` 回退 finite raw advantage。empty minibatch 完整跳过，logger 除以真实 processed
updates。rejected proposal 仍有效；critic 完全不使用 DVM。active mask 与 DVM 独立存储，
因为前者是 alive/episode boundary，后者是 assignment choice boundary。

这里 `[T+1,E,1]` 的 terminal boundary slot 可以携带 false DVM/critic boundary state，但不等于
存在 terminal actor action row。actor 的 `training slice` 只遍历实际
`storage_row_present=true` 的 nonterminal rows；terminal sidecar 不写 action/log-prob、proposal
或 forced placeholder，也不进入 advantage normalization population。

### 16.3 Sequential-factor sibling contract

唯一 owner：event-profile schema module 的 `event_gated_happo_sequential_factor_v1`。
exact key order：

```text
contract_version
factor_shape
initial_value
agent_update_order_source
raw_ratio_equation
effective_ratio_equation
factor_update_equation
nondecision_identity
per_agent_dvm_rule
zero_valid_actor_rule
agent_axis_rule
```

```python
factor = ones([T,E,1])
raw_ratio = aggregate(exp(new_log_prob - old_log_prob))
effective_ratio = torch.where(
    decision_valid_mask,
    raw_ratio,
    torch.ones_like(raw_ratio),
)
factor *= effective_ratio
```

每个 actor 使用自己的 DVM 更新共同 `[T,E,1]` factor，不新增 agent axis。zero-valid actor
不 evaluate pre/post ratio，factor 不变。禁止用代数式 `DVM*ratio + ...`，因为
`0*NaN` 仍可能传播 NaN。只在最终 actor loss 外乘 DVM 不足以阻止 nondecision row 污染
后续 agent factor。agent order 精确引用 config `algo.fixed_order`；当前 snapshot 为 false，
即使用 runner 的 random permutation 规则，而不是另造固定顺序。

terminal `terminal_no_row` 不占 `[T,E,1]` action/factor row，不计算 ratio；其 critic sidecar 仅
提供 pre-reset centralized state/boundary。ordinary nonterminal forced row 才以 DVM=false、
effective ratio one 保持 factor identity。

### 16.4 Serialization

```text
serialization_contract:
  serialization_mode
  save_entire_model
  state_dict_key_contract_version
  checkpoint_ready_inventory_required
  interface_descriptor_weight_use_authorized

exact values:
  serialization_mode: state_dict
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.serialization_mode
  save_entire_model: false
    source: resolved_event_profile_mapping.event_gated_target_semantics.
            training_semantic_contract.save_entire_model
  state_dict_key_contract_version: event_gated_state_dict_inventory_contract_v1
    source: model_structure.state_dict_key_contract_version
  checkpoint_ready_inventory_required: true
  interface_descriptor_weight_use_authorized: false
```

因此 A4a interface descriptor 只能 fingerprint semantic identity，不能加载/保存 weights。

## 17. Public descriptor ownership matrix

未来 `assignment_event_profile_schema_contract_v1` public descriptor exact top-level key order
恰好 11 项：

```text
contract_version
scale_contract
actor_schema
shared_schema
unresolved_parameter_inventory
decision_valid_training_contract
sequential_factor_contract
model_structure
training_contract
runtime_readiness_contract
v3_section_ownership
```

`contract_version` exact value 是 `assignment_event_profile_schema_contract_v1`。不允许
free-form `metadata`/`notes`/`extensions` 或 arbitrary mapping。各 nested mapping 的 exact
top-level key count 与本报告 authority 是：

| Nested key | Exact key count | Freeze location |
|---|---:|---|
| `scale_contract` | 11 | §5.3 |
| `actor_schema` | 18 | §5.2.1--§5.5 |
| `shared_schema` | 19 | §6 |
| `unresolved_parameter_inventory` | 6 | §10 |
| `decision_valid_training_contract` | 14 | §16.2 |
| `sequential_factor_contract` | 11 | §16.3 |
| `model_structure` | 28 | §15 |
| `training_contract` | 9 | §16 |
| `runtime_readiness_contract` | 6 | 本节 |
| `v3_section_ownership` | 5 | 本节 |

MRTA v2 唯一拥有 `action_contract`。event-profile aggregate/V3 只引用这个
projection，不在 `scale_contract` 复制 action identity。`action_contract` exact 10-key
order/value 冻结为：

```text
contract_version: event_gated_action_contract_v1
num_agents: scale_contract.M
action_dimension: scale_contract.N + 1
target_action_id_domain: global_task_ids_0_through_scale_contract.N_minus_1
noop_raw_id: scale_contract.N
noop_decoded_value: -1
available_action_order: target_global_task_ids_ascending_then_noop
decision_valid_mask_contract_version: decision_valid_mask_snapshot_v1
proposal_mask_contract_version: proposal_snapshot_v1
cross_section_invariants:
  ("num_agents == scale_contract.M",
   "action_dimension == scale_contract.N + 1",
   "target_action_id_domain == global task IDs 0..scale_contract.N-1",
   "noop_raw_id == scale_contract.N",
   "noop_decoded_value == -1",
   "available_action_order == target global task IDs followed by noop",
   "len(scale_contract.ordered_agent_names) == num_agents")
```

上面 code block 的 key order 就是 exact serialized order；`cross_section_invariants` 是
exact ordered tuple，不是 set。`num_agents/action_dimension/noop_*` 只在 action contract
拥有 concrete derived value；`M/N/ordered identities/time/normalization scales` 只在
scale contract 拥有。Assignment-tick semantic action mask 才关联
`decision_valid_mask_snapshot_v1`；ordinary no-tick 的 one-action mask 是
`proposal_snapshot_v1` historical forced-storage encoding，terminal 是 all-false `NO_ROW`
carrier/no storage。A3x-1 只扩展 MRTA public descriptor v2，不创建 V3 section class；
V3 dataclass 仍属于重新授权后的 A4a。

下表给 19 个 semantic sections 各指定一个 V3 projection owner。`Required extension` 是
A3x-1 的 descriptor-only 工作；V3 只存 owner descriptor 的 typed projection/reference，
不复制 documentary text。

| V3 section | Unique public projection owner | Existing key/source | A3x-1 extension | Documentary authority |
|---|---|---|---|---|
| `identity` | `assignment_profile_contract.py` | resolved event profile | none | A1 registry |
| `scale` | `assignment_event_profile_schema_contract_v1` | resolved profile/scenario references | exact M/N/ordered-agent/task identity projection | Phase A plan + this schema |
| `actor_schema` | `assignment_event_profile_schema_contract_v1` | version string only | 15-block descriptor | this report §§5,7 |
| `shared_schema` | `assignment_event_profile_schema_contract_v1` | version/mode strings only | 19-block descriptor | this report §§6,7 |
| `action_contract` | `assignment_mrta_contract_v2` | action/mask/four-mask equations | typed projection/reference | Authoritative §§8,10 + A3 |
| `transition_contract` | `assignment_lifecycle_transition_contract.py` | facts/result schemas | existing reference; descriptor version update also carries enum refs | A2 |
| `event_tick_contract` | `assignment_event_contract.py` | three record systems | retry cadence projection/reference | Authoritative §§4,9 + A3 |
| `local_candidate_contract` | `assignment_mrta_contract.py` | DTO schemas/round/overflow | exact semantic projection | this report §11 |
| `cost_path_contract` | `assignment_mrta_contract.py` | cost DTO/sum/NaN | exact semantic projection | this report §12 |
| `decision_valid_training_contract` | new event-profile schema module | MRTA DVM construction reference | actor-training projection | Authoritative §§19--20 |
| `sequential_factor_contract` | new event-profile schema module | none | exact factor projection | Authoritative §21 |
| `component_contract` | `assignment_mrta_contract.py` | component DTO/result validator | exact semantic projection | this report §13 |
| `reward_contract` | `assignment_team_reward_contract.py` | complete v1 descriptor | none | A3 reward contract |
| `failure_termination_contract` | `assignment_lifecycle_transition_contract.py` | result field + reason enum | states/equations projection | this report §14 |
| `diagnostics_contract` | `assignment_event_gated_diagnostics_contract.py` | complete v1 descriptor | none | A3 diagnostics |
| `policy_sequence_contract` | `assignment_profile_contract.py` | `event_gated_target_semantics.policy_sequence_route` + `training_semantic_contract` | none; event-profile aggregate stores only canonical references and exact-equality checks | A1 registry |
| `model_structure` | new event-profile schema module | current config/code evidence | exact model projection | this report §15 |
| `training_contract` | new event-profile schema module | A1 identity + domain refs | exact aggregate key order | this report §16 |
| `runtime_readiness_contract` | new event-profile schema module | A1 `runtime_readiness=interface_only` canonical reference | exact readiness projection carrying the unresolved-inventory reference | A1 fail-closed profile + this report §10 |

`v3_section_ownership` 不是任意的 Markdown-derived mapping。它的 exact 5-key order/value
冻结为：

```text
contract_version: event_gated_v3_section_ownership_v1
section_order:
  (identity,
   scale,
   actor_schema,
   shared_schema,
   action_contract,
   transition_contract,
   event_tick_contract,
   local_candidate_contract,
   cost_path_contract,
   decision_valid_training_contract,
   sequential_factor_contract,
   component_contract,
   reward_contract,
   failure_termination_contract,
   diagnostics_contract,
   policy_sequence_contract,
   model_structure,
   training_contract,
   runtime_readiness_contract)
record_field_order:
  (order,
   section_name,
   owner_module,
   owner_contract_version,
   descriptor_key_path,
   projection_mode)
records: exact 19 records below
unique_authority_rule: exactly_one_owner_per_semantic_field_no_documentary_fallback
```

`projection_mode` 只允许 exact literals `inline_owned_mapping` 与 `canonical_reference`。
record key order 恰好 6 项；19 records 的 `order` 必须是 `1..19`：

| `order` | `section_name` | `owner_module` | `owner_contract_version` | `descriptor_key_path` | `projection_mode` |
|---:|---|---|---|---|---|
| 1 | `identity` | `assignment_profile_contract` | `assignment_resolved_profile_v1` | `resolved_event_profile_mapping` | `canonical_reference` |
| 2 | `scale` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `scale_contract` | `inline_owned_mapping` |
| 3 | `actor_schema` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `actor_schema` | `inline_owned_mapping` |
| 4 | `shared_schema` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `shared_schema` | `inline_owned_mapping` |
| 5 | `action_contract` | `assignment_mrta_contract` | `assignment_mrta_contract_v2` | `action_contract` | `canonical_reference` |
| 6 | `transition_contract` | `assignment_lifecycle_transition_contract` | `assignment_lifecycle_transition_contract_v2` | `$` | `canonical_reference` |
| 7 | `event_tick_contract` | `assignment_event_contract` | `assignment_event_contract_v2` | `$` | `canonical_reference` |
| 8 | `local_candidate_contract` | `assignment_mrta_contract` | `assignment_mrta_contract_v2` | `local_candidate_semantics` | `canonical_reference` |
| 9 | `cost_path_contract` | `assignment_mrta_contract` | `assignment_mrta_contract_v2` | `cost_path_semantics` | `canonical_reference` |
| 10 | `decision_valid_training_contract` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `decision_valid_training_contract` | `inline_owned_mapping` |
| 11 | `sequential_factor_contract` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `sequential_factor_contract` | `inline_owned_mapping` |
| 12 | `component_contract` | `assignment_mrta_contract` | `assignment_mrta_contract_v2` | `component_semantics` | `canonical_reference` |
| 13 | `reward_contract` | `assignment_team_reward_contract` | `assignment_team_reward_contract_v1` | `$` | `canonical_reference` |
| 14 | `failure_termination_contract` | `assignment_lifecycle_transition_contract` | `assignment_lifecycle_transition_contract_v2` | `failure_termination_semantics` | `canonical_reference` |
| 15 | `diagnostics_contract` | `assignment_event_gated_diagnostics_contract` | `assignment_event_gated_diagnostics_contract_v1` | `$` | `canonical_reference` |
| 16 | `policy_sequence_contract` | `assignment_profile_contract` | `assignment_resolved_profile_v1` | `resolved_event_profile_mapping.event_gated_target_semantics` | `canonical_reference` |
| 17 | `model_structure` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `model_structure` | `inline_owned_mapping` |
| 18 | `training_contract` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `training_contract` | `inline_owned_mapping` |
| 19 | `runtime_readiness_contract` | `assignment_event_profile_schema_contract` | `assignment_event_profile_schema_contract_v1` | `runtime_readiness_contract` | `inline_owned_mapping` |

表中 module literals 是 canonical package-relative basename；builder 使用第 18 节
canonical package prefix 解析，不允许 bare-import fallback。`$` 表示 owner 的
canonical public descriptor getter 返回的 complete root，因而 transition/event A3x-1 只 bump
并扩展现有 root，不需发明未冻结的第二层 key。
`resolved_event_profile_mapping` 表示第 16.1 节已冻结的 canonical
`resolved_assignment_profile_to_mapping(...)` return root，后续 dotted path 从该 root
解引。其余 non-`$` paths 均是本报告已 exact 冻结、将由对应 v2 暴露的
projection keys。该 serialized inventory 只使现有 19-row ownership matrix
machine-checkable，不改变任何 section owner 或第 19 节计数。

Parameter triple ownership 另遵守 domain rule：local/cost/component triples 只在 MRTA v2；retry
triple 只在 event v2；rejection triple 只在 reward v1。event-profile aggregate 只保存
domain triple 的 canonical module/key-path reference 并 drift-check；它另外唯一拥有 11-item
global order 与 `expected_concrete_type/unit/legal_domain` value metadata。
同样，`M/N/ordered identities/time and normalization scales` 只属于
`scale_contract`；`num_agents/action_dimension/noop encoding` 只属于 MRTA
`action_contract`。两者之间只做上述 exact equality-check，不建立第二 authority。

为让固定 19-section V3 实际覆盖该 cross-cutting aggregate，
`runtime_readiness_contract` 的 event-profile projection exact keys/order 冻结为：

```text
projection_version
profile_runtime_readiness_ref
unresolved_parameter_inventory_projection
unresolved_parameter_resolution_status
runtime_execution_authorized
checkpoint_weight_use_authorized

exact values:
  projection_version: event_gated_runtime_readiness_projection_v1
  profile_runtime_readiness_ref:
    canonical_module: isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract
    descriptor_key_path: resolved_event_profile_mapping.runtime_readiness
    expected_value: interface_only
  unresolved_parameter_inventory_projection:
    exact typed inline to_mapping of event_gated_unresolved_parameter_inventory_v1
    with the complete ordered keys and 11 ordered records frozen in section 10
  unresolved_parameter_resolution_status: all_11_unresolved
  runtime_execution_authorized: false
  checkpoint_weight_use_authorized: false
```

`profile_runtime_readiness_ref` nested record field order 是
`(canonical_module, descriptor_key_path, expected_value)`。inventory 字段禁止只存 version
string 或 bare pointer；它必须 inline serialize §10 的完整 aggregate mapping，因此 11-item
order/reference/value-metadata 任一 content drift 即使忘记 bump version，也会改变 V3 canonical
bytes/hash；builder 还必须对 domain descriptor reference 做 exact drift-check。

该 section projection 是 aggregate/reference owner；A1 仍唯一拥有底层 `interface_only`
readiness value，各 domain descriptor 仍唯一拥有自己的 triple，因而没有第二 semantic authority。

## 18. Canonical module/import dependency plan

新 module identity：

```text
file:
  assignment_event_profile_schema_contract.py

canonical module key:
  isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract

contract version:
  assignment_event_profile_schema_contract_v1
```

依赖 DAG：

```text
assignment_profile_contract
assignment_lifecycle_transition_contract
        -> assignment_event_contract
        -> assignment_mrta_contract
        -> assignment_team_reward_contract

existing domain descriptors + assignment_event_gated_diagnostics_contract
        -> assignment_event_profile_schema_contract
        -> future assignment_checkpoint_contract_v3
        -> future semantic dispatcher
```

event-profile schema module 只能 package-relative 向下 import public constants/getters；任何
基础 contract 不得反向 import 它。future V3 从 unique owners 取 typed sections 并验证
projection version/reference，不从 Markdown 复制值。

特别地，`policy_sequence_contract` 的 unique owner 保持 A1
`assignment_profile_contract.py`；新 event-profile module 的 `algorithm_identity` 与 training
aggregate 只能引用该 owner。DVM actor-update 和 sequential-factor sibling contracts 是本报告
冻结的新增 event-specific training semantics，但不得重写 A1 的 algorithm/state/share/recurrent/
buffer/serialization 或 `policy_sequence_route` fields。

所有新增/修改 module 的 canonical `__name__` guard 必须位于 identity-bearing type、torch 和
dependency import 之前；禁止 bare fallback、`sys.modules` alias、private tensor detector、
storage identity 或 ledger capability 进入 public descriptor/fingerprint。

## 19. V3 21-key/19-section clarification

正式计数：

```text
top-level mapping keys:
  21

discriminators:
  2
  manifest_format_version
  manifest_kind

typed semantic section dataclasses:
  19
```

exact top-level order：

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

因此“`manifest_format_version` 后有 20 entries”包含另一个 discriminator
`manifest_kind`，不等于“20 semantic section dataclasses”。不得新增虚构 section。

## 20. Versioning and fingerprint migration

| Contract/schema | A3x-1 version rule | Reason |
|---|---|---|
| profile registry | keep `assignment_resolved_profile_v1` | event identity 未变 |
| actor schema string | keep `event_gated_global_actor_observation_v1` | 首次完整定义该既有 identity |
| shared schema string/mode | keep existing v1 strings | 首次完整定义，不存在旧 event layout |
| MRTA public descriptor | bump `assignment_mrta_contract_v1 -> v2` | 新增 local/cost/component projections/triples |
| event public descriptor | bump `assignment_event_contract_v1 -> v2` | 新增 retry cadence projection/triple |
| transition public descriptor | bump `assignment_lifecycle_transition_contract_v1 -> v2` | 新增 state enums/failure projection |
| team reward | keep v1 | rejection triple 已完整 authoritative |
| diagnostics | keep v1 | 无字段变化 |
| all A2/A3 DTO/record schemas | keep all v1 field orders | descriptor-only extension，不破坏 DTO mapping |
| unresolved parameter DTO | keep `unresolved_parameter_spec_v1` | enum `.value` 仍序列化 exact string |
| event-profile aggregate | new `assignment_event_profile_schema_contract_v1` | 新 public owner |

A3x-1 不创建 V3 或 checkpoint golden。当前没有已发布 V3 canonical bytes/fingerprint，因此
不存在 V3 dual-schema migration；A4a 首次实现时只接受本次 freeze 后的一个 schema 并首次
生成 interface-descriptor golden。V2 parser、bytes、hash 和 compatibility classifications
必须 byte-exact 不变。

future V3 fingerprint 必须覆盖 ordered blocks/columns/dimensions、normalization、projection
versions/key orders/equations、11-item parameter references、enum orders、current model/config
projection 和 training refs。任一变化都产生 semantic mismatch；equal dimension 不能绕过。
`interface_semantic_descriptor` 仍拒绝 weight use，只有所有 11 项 concrete、runtime readiness
verified、state-dict inventory/evidence 完整的 `checkpoint_ready_manifest` 才能用于 save/load。

A3x-1 完成后 A3 可表述为 `complete after targeted schema-freeze extension`。应运行新增
descriptor tests 与完整 A1--A3 72/72 regression；不更新 checkpoint golden，只增加/更新
literal descriptor expectations。

## 21. Proposed A3x-1 implementation files

只有在 GPT/user 明确授权 A3x-1 后才可进行：

| File | Change | Expected responsibility |
|---|---|---|
| `assignment_event_profile_schema_contract.py` | new | exact 11-key root；scale/actor/shared/ordinary/terminal/terminal-sidecar descriptors；owner enum；11-item aggregate references；model/training projections；typed 19-row V3 ownership inventory |
| `assignment_mrta_contract.py` | modify | public descriptor v2；exact 10-key action projection；local/cost/component projections；9 个非-reward/non-retry domain triples；不改 DTO schemas/versions |
| `assignment_event_contract.py` | modify | public descriptor v2；retry cadence projection/triple；不改 record schemas |
| `assignment_lifecycle_transition_contract.py` | modify | public descriptor v2；task/robot enums；failure/termination projection；不改 facts/result fields |
| `scripts/environments/test_assignment_event_profile_schema_contract.py` | new | aggregate schema/key order/dim/owner/import/version pure tests |
| `scripts/environments/test_assignment_event_gated_mrta_contract.py` | modify | MRTA/event v2 projection/triple/equation regression |
| `scripts/environments/test_assignment_lifecycle_transition_contract.py` | modify | enum/order/failure projection regression |

`assignment_team_reward_contract.py`、profile contract、lifecycle training、wrapper/env/runner、
YAML、V2 checkpoint files 和 installed HARL 都不需要在 A3x-1 修改。若实现发现必须改这些
文件，应停止并重新申请授权，不得扩大 slice。

## 22. Proposed A3x-1 pure tests

建议 pure/static gate：

1. event-profile root exact 11-key order；scale exact 11-key order/rules；unknown/missing/reordered
   semantic key 一律 fail closed；
2. actor exact 18-key order、block-record exact 12-key order/15 records、reference/normalization/
   generation/ordinary/terminal nested order、exact 15-item exclusions；多组 M/N 公式，
   `M=3,N=50 -> 1692`；任一 unknown/missing/reordered actor/nested/record key 拒绝；
3. shared exact 19-key order、block-record exact 10-key order/19 records、reference/terminal-sidecar
   nested order、exact 17-item exclusions；shape 是 exact tuple-of-string primitive；shared
   generation-binding 与 actor exact inline equal；semantic/transport shapes 分离，
   `M=3,N=50 -> 1751`；任一 unknown/missing/reordered shared/nested/record key 拒绝；
4. ordinary nonterminal no-tick 每 robot 恰好一个 legal forced storage action，不调
   actor；A3 DVM no-opportunity row 仍 all false/count 0；terminal target/noop/available
   all false、count 0、forced ID `-1`、无 storage/proposal/forced/resolver/component；
   terminal shared sidecar 携带 finalized pre-reset state/reason，先写 boundary slot 再 reset，
   但不新增 physical-transition/critic-loss sample；
5. action projection exact 10-key order，DVM/proposal schema-version binding，
   `num_agents/action_dimension/noop` 与 scale 的七项 ordered cross-invariant exact；
   scale 不得复制 action-owned fields；unknown/missing/reordered action key/invariant 拒绝；
6. `v3_section_ownership` exact 5-key order、6-key record order、19 records/owner/path/mode；
   19-section order 与 §19 exact equal；unknown/missing/reordered ownership key/record 拒绝；
   每个 `owner_module/owner_contract_version/descriptor_key_path` 必须按本节 root/path
   semantics 成功解引；
7. invalid cost DTO NaN 与 observation zero+valid-mask mapping；one-hot/mutual-inverse assertions；
8. Contract-C version/dims/layout 不被引用为 event identity；nearest/local repack 被拒绝；
9. owner enum exact order/value；11 names exact order/unique；aggregate reference 与 domain
   owner triple equality；每项 `expected_concrete_type/unit/legal_domain` exact bytes/order；reward
   v1 五键记录只提取 frozen triple；runtime-readiness inline inventory content drift 改变
   canonical bytes；不存在第 12 项；
10. local seed equality、trigger prohibition、Top-K tie-break、one-round owner expansion、overlap
   transitive merge、post-merge recompute、association four-tuple、overflow fail-closed literals；
11. cost seconds/sum/current-owner ALIGNING rule/NaN/no-sentinel/fallback reference；
12. component pair gates、count/J0/Jp/transfer formulas、covered CONTINUE、reason order、penalty
   attribution 和 forbidden behavior literals；
13. task/robot/termination enum numeric order、failed-pair delta/cumulative、completed priority、
   team-infeasible、terminal mapping fail-closed 和 generation rules；
14. model key order、actual critic `(256,256)` projection 来源必须是 runner 消费的
    `model.hidden_sizes`；unused `model.hidden_sizes_critic` 不进入 fingerprint；model
    refs 必须可解引为 `actor_schema.dimension_formula`、
    `shared_schema.dimension_formula`、`action_contract.action_dimension/num_agents`、
    `scale_contract.ordered_agent_names`；
15. training nested key order、DVM valid-only/zero/singleton/empty rules、factor `torch.where`、
    no agent axis、state-dict interface-only rule；
16. all descriptors deeply read-only、deterministic、no alias；descriptor private runtime/detector
    fields absent；content mutation 会改变 future canonical bytes；canonical module guard/import DAG；
17. old DTO `to_mapping` fields/schema versions exact unchanged；V2 contract bytes/hash unchanged；
18. existing A1--A3 72/72 regression。

测试只 import pure modules；不得构造 actor/critic、调用 optimizer、Isaac/AppLauncher、
training/playback/evaluation 或 checkpoint I/O。A3x-1 不创建 V3/checkpoint golden；那属于重新
授权后的 A4a。

## 23. Accepted method boundaries and targeted review gate

以下五项方法边界已由 targeted review **5/5 accepted**，A3x-0R 不重新设计：

1. actor 看全队 `[M,N]` failed/path/nominal-cost/target-mask 和全队
   opportunity/DVM context；
2. observation 只暴露 normalized nominal sum，navigation/alignment decomposition 仍只由
   cost descriptor authoritative；
3. actor 只看 `lifecycle_event_seed` 与 `scheduled_retry_opportunity` cause summary，
   不看七类 raw event one-hot/payload；
4. workload/history 只保留 authoritative per-robot completion fraction 与 episode progress；
5. model projection 采用当前 assignment runner 实际 critic `(256,256)`，不采用
   YAML 未消费的 `(512,256)`。

这五项、actor/shared blocks 与维度、top-level 21/19、Contract-C identity 不复用、
11-item inventory、local/cost/component/failure/model/training projections 和 unique ownership 全部
保持不变。本轮 GPT/user gate 只复核 SF-01/SF-02 的 targeted closure，不重开
broad method review，也不授权 A3x-1。

## 24. Risks

| Risk | Severity | Consequence | Mitigation/gate |
|---|---|---|---|
| full-team pair/mask visibility 形成过强 coordinator information | high-method | 论文信息边界或可扩展性受影响 | 第 23.1 明确 review；checkpoint 绑定 exact layout |
| current-owner remaining-time estimator 不存在 | high-runtime | cost contract 无法真实执行 | A3x 只冻结 interface；B0/B 必须 estimator evidence gate |
| critic YAML/runner hidden-size divergence | high-compatibility | fingerprint 与实际 state dict 不一致 | 采用实际 `(256,256)`；A3x-1 static drift test；checkpoint-ready inventory 后验 |
| DVM 只用于 final loss 而未用于 factor | high-training | nondecision row 污染后续 actor correction | separate factor descriptor + Phase C `torch.where`/zero-skip tests |
| ordinary forced mask 被伪装为 A3 DVM no-opportunity snapshot | high-contract | 破坏 all-false/count-0 DTO 不变式或把 forced row 误当决策 | DVM 只在 assignment tick 构造；ordinary mask 只进 ProposalSnapshot historical storage；exact row tests |
| terminal sidecar 被当成 forced/action 或额外 critic sample | high-training | terminal 产生伪 proposal/factor ratio 或重复 physical-step loss | zero-action/no-storage contract；pre-reset boundary-slot ordering；no-extra-sample test |
| reset observation 与 terminal sidecar alias | high-runtime | 上一 episode reason/final facts 丢失 | `reset_state_alias_forbidden=true`；B0/C pre-reset transport gate |
| serialized key/record order 或 arbitrary mapping 漂移 | high-schema | future canonical bytes 不稳定或隐藏 semantic change | exact root/nested/record inventories；unknown/missing/reordered rejection；deep-readonly/content-drift tests |
| target mask/DVM/observation generation 不一致 | high-correctness | 历史 action 被新 mask 重解释 | 四元 generation equality、historical mask buffer、mutual assertions |
| local merge 后错误开启第二轮 owner expansion | high-method | locality/complexity语义漂移 | exact order literal + overlap/one-round pure and B tests |
| task/robot enum second authority | high-schema | fingerprint 和 runtime int meaning 漂移 | transition module 唯一 owner；其他 section 只引用 |
| completed workload 需要新的 authoritative attribution ledger | medium-runtime | schema field 无可靠 producer | B0 consume-once lifecycle authority owns derivation；无证据则 fail closed |
| episode-horizon cost normalization 改变时 checkpoint 漂移 | medium-compatibility | 相同 seconds 映射不同 | resolved horizon/config 进入 scale/schema fingerprint |
| duplicate ownership/assignment tables 不一致 | medium-correctness | policy 接收矛盾 state | same a0 mutual-inverse assertion，单一 lifecycle source |
| retry anchor/tick generation 循环或 stale alias | medium-runtime | starvation/重复 tick | physical transition cadence；process-lifetime tick generation；deterministic tests |
| interface descriptor 被误当 checkpoint-ready | high-safety | 未验证模型被加载/保存 | artifact-kind gate，interface weight use=false，无 checkpoint I/O |

最大技术风险不是 dataclass 编写，而是 Phase C 对 repo-local runner/trainer 的 DVM subset、
zero/singleton 和 sequential factor 语义接入。A3x-1 只提供 fingerprint authority，不能消除
该 runtime 风险。

## 25. Final recommendation

```text
recommendation:
  review SF-01 and SF-02 targeted closure in this A3x-0R revision
  preserve the five already accepted method boundaries
  authorize A3x-1 separately only after this targeted review passes

do not:
  restart A4a before A3x-1 implementation and review
  enter A4b/A5/A6 or B0/B/C/D/E
  modify runtime/HARL/checkpoint behavior
```

本报告已关闭 SF-01 的 ordinary nonterminal forced-storage row/terminal no-row 分层，
以及 SF-02 的 root/scale/action/actor/shared/terminal-sidecar/ownership exact serialized
inventory；同时保持 actor/shared blocks、dimension、11-item inventory、六个
semantic projections、unique ownership、import/version/fingerprint 和 A3x-1 file/test plan 不变。
没有 production patch、numeric selection、runtime evidence 或 commit。`TASK_PROGRESS.md`
仅做 targeted in-place 替换，保持在 200--300 行范围，因此未触发实质重写/
缩短的 archive 规则，不创建 archive。

先前 A3x-0 pure baseline 已使用指定 interpreter 运行：event/MRTA contract `12/12`、lifecycle
transition contract `11/11`，合计 `23/23` passed。该结果只证明现有 A2/A3 baseline 未被
文档工作影响，不是未来 A3x-1 descriptor、runtime、模型或 checkpoint evidence。
A3x-0R 本轮未重跑 23/23 或 72/72，只执行静态文档/git 检查。未运行
Isaac/AppLauncher、actor/critic construction、training、playback、evaluation 或 checkpoint
I/O。

```text
A3x-0R:
  stopped for GPT/user review

A3x-1:
  not entered

A4a:
  not restarted

A4b/A5/A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```
