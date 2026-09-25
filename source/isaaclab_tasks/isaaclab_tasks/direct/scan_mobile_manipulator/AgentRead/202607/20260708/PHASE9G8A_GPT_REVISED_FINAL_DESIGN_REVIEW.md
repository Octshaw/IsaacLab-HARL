# Phase 9G-8A 修订后最终设计判断

## A. Phase 9G-8A 最终结论

```text
PASS WITH REQUIRED REVISIONS
```

Codex 已正确识别 resolver 引入的主要隐藏行为状态，并正确选择了：

```text
lifecycle-aware observation
+
lifecycle-aware available-action mask
+
resolver final safety boundary
```

同时保留：

```text
action dimension = N + 1
raw noop id = N
decoded noop = -1
executing + noop = continue active target
```

这些核心方向应继续保留。

但 Phase 9G-8A 尚未充分冻结以下关键 contract：

```text
真实 budget progress source of truth
observation/shared observation/mask 的原子快照边界
PPO update 对采样时 mask 的复用
legacy guardrail 与 resolver 的唯一行为状态源
checkpoint schema manifest/fingerprint
结构加载、evaluation 和 training resume 的不同兼容性
```

此外，原报告提出的四个 actor lifecycle 字段中，`task_owned_by_self` 很可能与 `self_active_target` 重复；critic/shared observation 也需要在低风险拼接方案与 compact global 方案之间重新论证，而不能直接冻结。原报告中 actor 4N 扩展、shared observation 直接拼接 actor observation 等内容因此需要修订。

在进入任何 observation builder 实现前，应先完成：

```text
Phase 9G-8B:
Lifecycle Observation / Mask / Checkpoint Contract Revision and Freeze
```

9G-8B 通过前，resolver-enabled training 继续保持禁止。

---

## B. 必须修订项

### B.1 审计真实 budget release 状态

必须区分：

```text
resolver attempt_start_step / attempt_age
```

和真正触发 budget failure/release 的 wrapper budget tracker，例如：

```text
budget_attempt_steps
budget_expected_steps
budget_steps
budget progress
remaining budget
```

9G-8B 必须从当前实现中确认：

1. 哪一个 tensor 或 tensor 组合是 release predicate 的唯一 source of truth；
2. budget state 在 attempt start、每个 post-step、completion、failure、reset 时如何更新；
3. `budget_steps` 是否在 attempt 开始后保持固定；
4. release 是否严格等价于类似：

```text
budget_attempt_steps >= budget_steps
```

5. 当前 actor/shared observation 是否能够精确重建该 predicate；
6. 最小充分的归一化表示是什么。

不能使用 resolver `attempt_age` 代替真实 budget progress，除非能够逐项证明二者在所有 reset、continuation 和 release 路径中严格等价。

最低 contract：

```text
exact active budget progress
必须进入 critic/shared observation，
除非证明 critic 当前输入能够精确重建 release predicate。
```

### B.2 明确 actor 是否需要 budget progress

当前 Contract C 下，executing robot 只能在以下两个 continuation alias 中采样：

```text
active target
noop
```

没有：

```text
switch
abort
manual release
retry
```

因此 budget progress 当前不会改变 actor 可选择的有效 transition：两种允许动作都会继续当前 active target。

推荐冻结：

```text
budget progress:
  critic-required
  actor-not-required
```

但报告必须明确写出其依据是“当前 action controllability”，而不是“budget progress 不影响环境 transition”。

未来一旦加入 abort、switch、主动 release 或 retry action，必须重新审计 actor 是否需要该状态。

### B.3 定义原子 lifecycle decision snapshot

必须冻结下一决策时刻的顺序：

```text
environment transition / post-step diagnostics
→ resolver observe_post_step
→ completion / budget release / ownership update
→ reset done environments
→ capture immutable lifecycle decision snapshot
→ build actor observation
→ build critic/shared observation
→ build available_actions
→ policy sampling
```

这里的 snapshot 应同时包含至少：

```text
resolver active_target state
task ownership
failed/released pair memory
真实 budget tracker state
completion/coverage-related lifecycle state
environment/task feasibility state needed by mask
reset generation
```

必须设计：

```text
lifecycle_snapshot_generation
```

或语义等价的 generation/version 标识。

同一个 decision step 中：

```text
actor observation generation
==
shared observation generation
==
available_actions generation
```

不允许 observation 使用旧 ownership、mask 使用新 ownership，也不允许 budget progress 来自不同 update phase。

### B.4 冻结 PPO mask replay contract

必须静态审计完整路径：

```text
policy sampling
→ rollout buffer insertion
→ feed-forward generator / recurrent generator
→ PPO evaluate_actions
→ current action log-prob calculation
→ stored old action log-prob comparison
```

必须冻结：

```text
mask_used_for_sampling[t]
==
mask_stored_in_rollout_buffer[t]
==
mask_used_by_evaluate_actions_for_sample_t
```

PPO update 不得根据 update 时的当前 resolver state 重新生成历史 mask。

需要确保：

* buffer 保存的是采样时 mask 的副本，而不是可能被后续修改的引用；
* feed-forward 和 recurrent generator 都传递对应样本的 mask；
* actor `evaluate_actions` 使用 generator 返回的历史 mask；
* resume、save/load 和 recurrent chunking 不改变 mask 与 transition 的时间对齐；
* mask dtype、shape 和 noop index 在全链路一致。

### B.5 冻结 legacy guardrail profile

第一版正式 resolver-enabled lifecycle training profile 推荐保留：

```text
budget tracker / budget trigger
```

但它只作为：

```text
resolver budget-failure / release 的信号源
```

正式 profile 中关闭：

```text
legacy cooldown action-mask suppression overlay
redirect guardrail
legacy failed-pair TTL memory
```

尤其禁止：

```text
legacy failed-pair TTL eligibility
+
resolver episode-persistent failed-pair rejection
```

同时作为两个行为 source of truth。

任何被保留的 legacy guardrail 都必须单独完成：

```text
hidden-state audit
actor/critic/mask destination classification
snapshot timing definition
checkpoint metadata versioning
training-readiness validation
```

否则不得进入正式 lifecycle training profile。

### B.6 强化 checkpoint contract

不能只检查：

```text
actor observation dimension
shared observation dimension
schema version string
```

必须设计 ordered schema manifest，并由 manifest 生成稳定 fingerprint。

至少覆盖：

```text
actor feature names and ordering
actor per-task row ordering
critic/shared feature names and ordering
shared-state construction mode
feature shapes
feature dtype
feature normalization
feature source tensor
feature timing/snapshot semantics
resolver contract version
mask contract version
budget-release contract version
legacy guardrail profile
M
N
actor observation dimension
shared observation dimension
action dimension
noop raw id
noop decoded value
training-time resolver mode
```

应区分：

```text
A. Structural load compatibility
   参数 shape 是否能够加载

B. Evaluation / ablation compatibility
   是否允许有意识地在不同 resolver/mask 模式下评估

C. Training resume compatibility
   是否仍是同一 observation、transition、mask 和 lifecycle contract
```

三者不能混为一谈。

### B.7 旧 checkpoint 无 metadata 时的边界

旧 checkpoint 仅在以下组合中允许 legacy playback/evaluation：

```text
explicit profile = legacy
schema = legacy_v1
resolver disabled
legacy mask contract
actor shape exact match
critic shape exact match
action dimension exact match
noop id exact match
```

默认不允许旧 checkpoint：

```text
resume training
进入 lifecycle schema
启用 resolver
启用 lifecycle mask
```

不能通过零填充、截断 observation、部分 state-dict load 或 warning 后继续运行来伪造兼容性。

---

## C. 可选优化项

以下内容不是第一版 lifecycle training readiness 的阻塞项：

```text
compact global critic state
Transformer/GNN task-token architecture
variable M across checkpoints
variable N across checkpoints
task_valid padding
active-target infeasibility release
failed-pair TTL
retry policy
stranded-task recovery
failure/release reason embedding
resolver event history
explicit continue action
```

它们可以在后续独立阶段设计，不应混入当前 observation contract freeze。

---

## D. 冻结后的 actor schema

### D.1 必须首先证明的 invariant

9G-8B 必须检查所有合法路径：

```text
idle target claim
same-target continuation
noop continuation
simultaneous arbitration
completion
budget failure/release
partial reset
full reset
```

并证明：

```text
task_owned_by_self[j]
始终等价于
self_active_target[j]
```

即不存在合法状态：

```text
owned by self but not active
active but not owned by self
```

若该 invariant 不成立，9G-8B 不得冻结 3N schema，必须报告反例并停止进入实现。

### D.2 推荐冻结的 actor lifecycle 字段

在 invariant 成立时，每个 task row 增加三个字段：

```text
1. self_active_target[j]
2. task_owned_by_teammate[j]
3. self_pair_failed_or_released[j]
```

语义：

```text
self_active_target:
  当前机器人正在执行 task j；
  同时表达 task j owned by self。

task_owned_by_teammate:
  task j 当前由任一其他机器人持有；
  actor 不需要知道具体 owner id。

self_pair_failed_or_released:
  当前 robot-task pair 已进入 resolver 的 episode-persistent
  budget failed/released rejection state。
```

派生但不进入网络：

```text
is_executing = any(self_active_target)
is_idle = not is_executing
task_owned_by_self = self_active_target
task_unowned =
    not self_active_target
    and not task_owned_by_teammate
```

`task_owned_by_self` 保留为 builder 内部断言字段，不作为 actor 输入。

### D.3 字段布局

推荐直接加入现有 per-task row：

```text
legacy per-task row: 14
lifecycle per-task row: 17
```

而不是在 observation 末尾追加三个语义分离的 N 维向量。

这样每个 task row 都是完整 task token，更适合未来 Transformer/GNN。

### D.4 actor 维度

当前通用公式：

```text
legacy_actor_dim = 100 + 3M + 16N
```

增加 `3N` 后：

```text
lifecycle_actor_dim
  = legacy_actor_dim + 3N
  = 100 + 3M + 19N
```

当前：

```text
M = 3
N = 50
legacy_actor_dim = 909
lifecycle_actor_dim = 1059
```

### D.5 actor 不加入的状态

当前第一版不加入：

```text
task_owned_by_self 独立 bit
raw owner robot id
owner one-hot
resolver attempt_age
attempt_start_step
真实 budget progress
teammate failed-pair matrix
failure reason
release reason
infeasibility streak
stranded streak
resolver event history
```

---

## E. Critic/shared 两方案比较与推荐

### 方案 A：保持当前 HARL shared-state 构造

```text
shared observation =
concat(all revised lifecycle actor observations)
+
exact active budget progress block
```

假设每个 robot 使用一个精确的 active budget progress sufficient statistic：

```text
budget_progress_block shape = [E, M]
```

通用 shared dimension：

```text
shared_dim_A
  = M * lifecycle_actor_dim + M
  = M * (100 + 3M + 19N) + M
```

当前：

```text
M = 3
N = 50

shared_dim_A
  = 3 * 1059 + 3
  = 3180
```

优点：

```text
与当前 wrapper 和 HARL EP 模式一致
shared observation 仍以 actor concat 为主体
修改范围较小
rollout buffer 和 critic space 迁移更直接
所有 actor-visible lifecycle state 自动进入 critic
验证风险较低
```

缺点：

```text
重复 task/global features
ownership 等关系信息存在冗余
shared dimension 较大
不是真正 compact global representation
variable M 仍改变 critic 输入维度
```

### 方案 B：compact global lifecycle block

```text
shared observation =
legacy shared flat
+
all-robot active-target matrix
+
all-robot failed-pair matrix
+
exact active budget progress
+
经证明必要的其他全局 lifecycle sufficient statistics
```

基础 lifecycle block 可考虑：

```text
active_target_matrix: [E, M, N]
failed_pair_matrix:   [E, M, N]
budget_progress:      [E, M]
```

优点：

```text
全局语义清晰
较少重复 lifecycle 字段
ownership 可由 active-target matrix 推导
更接近未来 graph/token state
```

缺点：

```text
改变当前 shared-state 构造逻辑
需要单独定义 global robot/task ordering
需要更大范围的 wrapper、buffer、checkpoint 和验证迁移
actor 与 critic schema 不再自然同步
更容易引入漏字段或时序不一致
```

### 推荐选择

第一版 lifecycle training-readiness 推荐：

```text
选择方案 A
```

理由：

1. Phase 9G-8 的目标是修复 resolver-enabled hidden state，而不是同时重构 centralized critic；
2. 方案 A 与当前 HARL EP shared-observation convention 最接近；
3. 实现、buffer、checkpoint 和 legacy isolation 风险更低；
4. 虽然存在冗余，但没有明显缺失；
5. exact budget progress 可作为独立 critic-only block补齐；
6. compact critic 应作为后续架构优化，而非当前安全迁移的前置条件。

但 9G-8B 必须通过静态代码审计确认：

```text
concat lifecycle actor observations + exact budget progress
```

在当前所有 transition 下 Markov-sufficient。

若发现其他会改变 transition/reward、但无法从该 shared observation 重建的状态，则必须补充，不得仅因选择方案 A 而忽略。

---

## F. Mask contract

动作空间保持：

```text
target actions: 0 ... N-1
raw noop: N
decoded noop: -1
action dimension: N+1
```

### F.1 Idle robot

target `j` available 当且仅当：

```text
task slot valid
physically feasible / available
uncovered
not owned by teammate
not failed/released for this robot
```

并且：

```text
noop always available
```

### F.2 Executing robot with active target k

只允许：

```text
target k
noop
```

屏蔽：

```text
all j != k
```

其中：

```text
executing + target k = continue k
executing + noop = continue k
```

不得屏蔽 noop。

在当前 Contract C 下，即使 active target 的物理 feasibility 临时变为 false，也不能仅由 mask 自动 release；active-target infeasibility 仍是 diagnostics-only。

如果出现：

```text
active target already covered
```

但 resolver 尚未清除 active/ownership，应作为 lifecycle ordering/invariant 错误处理，而不是由 mask 静默修复。

### F.3 同步 claim arbitration

多个 idle robot 同时看到同一个 unowned task 时，该 target 可以同时在多个 actor mask 中为 1。

winner 仍由 resolver 根据：

```text
lowest path cost
then robot-id tie-break
```

决定。

### F.4 resolver 仍是最终安全边界

resolver 必须继续检查：

```text
invalid id
covered target
ownership conflict
same-pair failed/released
executing switch
simultaneous claim conflict
```

mask 用于定义策略支持集和减少确定性 rejected proposals，不能取代 resolver。

---

## G. Atomic snapshot contract

### G.1 决策周期

冻结为：

```text
T 时刻动作执行
→ environment step
→ 收集 completion/budget/coverage 结果
→ resolver observe_post_step
→ 更新 active target / owner / pair state
→ reset done environments
→ reset resolver 与 budget state
→ capture decision snapshot for T+1
→ build actor obs
→ build shared obs
→ build available_actions
→ sample T+1 action
```

### G.2 snapshot 内容

至少包含：

```text
generation id
environment/task validity and feasibility
coverage/completion state
active_target_id
task_owner
failed/released pair memory
budget attempt active flags
budget release sufficient statistic
reset generation / episode identity
```

### G.3 snapshot 不可变性

在当前 policy decision 完成前，snapshot 不得被 post-step/reset 逻辑修改。

builder 接收 snapshot，而不是分别从多个可变 owner 对象临时读取。

### G.4 generation 验证

每次输出应可在 debug metadata 中检查：

```text
actor_obs_generation
shared_obs_generation
available_actions_generation
```

并断言：

```text
三者完全一致
```

generation 不必进入神经网络 observation，但必须可用于 smoke validation 和 diagnostics。

---

## H. PPO mask replay contract

每个 rollout transition 必须存储：

```text
obs[t]
share_obs[t]
available_actions[t]
action[t]
action_log_prob[t]
reward[t]
mask/rnn mask[t]
```

其中：

```text
available_actions[t]
```

必须是采样 `action[t]` 时实际使用的 lifecycle mask。

训练 update 时：

```text
evaluate_actions(obs[t], action[t], available_actions[t])
```

必须使用 buffer 中的历史 mask。

禁止：

```text
evaluate_actions(
  obs[t],
  action[t],
  rebuild_mask_from_current_resolver_state()
)
```

训练 gate 必须覆盖：

```text
feed-forward generator
naive recurrent generator
recurrent generator
mini-batch permutation
chunking
device transfer
save/load/resume
```

并验证 mask 与其对应 transition 没有错位。

---

## I. Budget progress contract

### I.1 source of truth

9G-8B 必须标明实际字段名和代码路径，确认 release predicate。

不能在文档中仅使用抽象的 `attempt_age`。

### I.2 最小充分表示

若实现证明：

```text
budget_steps 在 attempt start 时锁存
release iff budget_attempt_steps >= budget_steps
```

则推荐 critic 使用：

```text
active_budget_progress_norm =
    clamp(
        budget_attempt_steps / max(budget_steps, 1),
        0,
        1
    )
```

inactive robot：

```text
active_budget_progress_norm = 0
```

还必须有 active-target state，避免将 inactive 0 与刚开始 attempt 的 0 混淆；active-target matrix 已提供这一信息。

若 `budget_steps` 会在 attempt 中动态变化，或者 release predicate 还依赖其他不可重建状态，则单一 ratio 不足，必须改为能够精确决定 predicate 的 sufficient-statistic block。

### I.3 更新与 reset

必须冻结：

```text
attempt start 时初始化
每次有效 continuation post-step 后更新
completion 时清除
budget release 时清除或记录 release 后状态
done-env reset 时清零
partial reset 只影响对应 env
```

### I.4 actor/critic destination

当前冻结：

```text
actor: 不加入
critic/shared: 必须加入
mask: 不直接使用
diagnostics: 可输出 raw numerator/denominator
```

---

## J. Checkpoint manifest/fingerprint contract

### J.1 manifest

推荐使用 canonical structured manifest，例如 JSON。

对象 key 可以稳定排序，但 feature list 必须保留真实网络输入顺序。

manifest 至少包含：

```text
profile_name
actor_schema_version
actor_ordered_features
actor_task_row_order
actor_dim

shared_schema_version
shared_construction_mode
shared_ordered_features
shared_dim

feature_normalization_contract
snapshot_contract_version
resolver_contract_version
mask_contract_version
budget_release_contract_version
legacy_guardrail_profile

M
N
action_dim
noop_raw_id
noop_decoded_value

training_time_resolver_enabled
training_time_profile
HARL state type / EP mode
```

每个 feature 条目建议包含：

```text
name
source
shape
dtype
normalization
timing
padding semantics
```

### J.2 fingerprint

由 canonical manifest 生成稳定 hash，例如：

```text
SHA-256
```

fingerprint 是生成的只读 metadata，不应由用户手工填写以绕过校验。

### J.3 保存位置

manifest/fingerprint 应随 checkpoint 保存在 loader 能稳定找到的位置，并覆盖：

```text
run root
models
best_model
```

或由统一 loader 从 run root 向上解析。

### J.4 load 规则

loader 必须先完成 project-level compatibility check，再调用 HARL state-dict load。

禁止依赖：

```text
PyTorch shape mismatch
HARL warning
silent observation slicing
partial load
```

作为 schema 检查机制。

---

## K. Legacy guardrail profile

正式第一版：

```text
profile: lifecycle_contract_c
```

保留：

```text
shared AssignmentLifecycleResolver
Contract C
budget tracker
budget trigger → resolver budget release
```

关闭：

```text
legacy cooldown mask overlay
redirect guardrail
legacy failed-pair TTL eligibility memory
任何与 resolver 重复的 ownership/failed-pair行为逻辑
```

legacy profile 保持原有 legacy 行为，但不得与 lifecycle checkpoint 混用。

任何未来重新启用的 guardrail 必须拥有新的：

```text
guardrail profile version
hidden-state audit
observation contract
mask contract
checkpoint fingerprint
```

---

## L. 合法/非法配置矩阵

推荐采用：

```text
高层 profile
+
内部解析出的不可变 contract versions
```

而不是让用户自由组合多个 boolean。

### L.1 Profile：legacy

```text
observation = legacy_v1
mask = legacy_v1
resolver = disabled
guardrails = legacy profile
```

支持：

```text
legacy checkpoint playback/evaluation
legacy training
有 metadata 的 exact-match legacy resume
```

无 metadata 的旧 checkpoint：

```text
只支持显式 legacy playback/evaluation
默认不支持 resume training
```

### L.2 Profile：lifecycle_ablation

```text
observation = lifecycle_v1
resolver = disabled
mask/profile = 明确的 ablation contract
guardrails = 不得隐式继承 resolver-on profile
```

用途：

```text
显式 evaluation/ablation
必要的 schema smoke
```

不得自动认为：

```text
resolver-on lifecycle checkpoint 可以 resume training
```

是否允许从头训练 lifecycle_ablation，应作为单独显式实验模式，而不是兼容性推断。

### L.3 Profile：lifecycle_contract_c

```text
observation = lifecycle_v1
mask = lifecycle_contract_c_v1
resolver = enabled
guardrails = lifecycle frozen profile
budget release = frozen contract
```

支持：

```text
新 resolver-enabled training
exact-contract checkpoint evaluation
exact-contract training resume
```

前提是 training-readiness gate 全部通过。

### L.4 Diagnostics-only profile

可定义内部 diagnostics profile，用于 bounded state inspection，但：

```text
禁止训练
禁止正式 performance evaluation
禁止保存可被误认为正式模型的 checkpoint
必须显著标记非 Markov / non-standard contract
```

若当前已不再需要 hidden-state playback，建议不向普通用户暴露该 profile。

### L.5 启动时 hard error

以下组合必须启动即报错：

```text
resolver enabled + legacy observation
lifecycle mask + legacy observation
legacy checkpoint + lifecycle schema
legacy checkpoint + resolver enabled
resolver-on lifecycle checkpoint + legacy schema
resume training 时 resolver mode 不同
resume training 时 mask contract 不同
resume training 时 guardrail profile 不同
resume training 时 budget-release contract 不同
schema version 相同但 fingerprint 不同
actor/critic/action/noop shape 不匹配
```

### L.6 Evaluation-only 显式允许

以下组合只可在显式 ablation/evaluation profile 下允许：

```text
resolver-on lifecycle checkpoint
+
resolver disabled
```

它表示改变环境 contract 的跨模式实验，不属于 training resume，也不能被默认加载路径自动接受。

---

## M. 修订后的后续阶段拆分

### Phase 9G-8B

```text
Lifecycle Observation / Mask / Checkpoint Contract Revision and Freeze
```

内容：

```text
documentation/design only
静态代码审计
冻结本报告中的 contract
不修改 Python
不运行训练
不运行 playback/evaluation
不 commit
```

### Phase 9G-8C

```text
Pure Lifecycle Snapshot and Tensor Builders
```

范围：

```text
immutable snapshot data contract
actor 3N lifecycle task-row builder
critic exact budget progress builder
generation validation
pure tensor/invariant tests
```

不接入 HARL，不改 mask，不训练。

### Phase 9G-8D

```text
Lifecycle Actor/Shared Observation Integration
```

范围：

```text
legacy_v1 exact isolation
lifecycle_v1 actor integration
选择并实现冻结后的 shared 方案
observation spaces
snapshot ordering
schema manifest generation
```

不训练。

### Phase 9G-8E

```text
Lifecycle Available-Action Mask and Rollout Replay Integration
```

范围：

```text
Contract C mask
same-snapshot validation
rollout available-actions storage
generator/evaluate_actions mask replay
resolver final boundary
```

不训练。

### Phase 9G-8F

```text
Checkpoint / Loader / Buffer / Forward-Backward Readiness
```

范围：

```text
manifest/fingerprint
all model loaders
actor/critic construction
rollout buffers
feed-forward and recurrent generator smokes
synthetic forward/backward
checkpoint save/load compatibility matrix
```

不运行正式环境训练。

### Phase 9G-8G

```text
Bounded Runtime Lifecycle Validation
```

范围：

```text
resolver-disabled legacy exact identity
resolver-enabled snapshot consistency
budget progress consistency
mask/resolver consistency
reset ordering
passive diagnostics coexistence
```

不训练，不做 performance evaluation。

### Phase 9G-8H

```text
Very Short Resolver-Enabled Training and Checkpoint Smoke
```

仅在此前全部通过后允许：

```text
very short training smoke
buffer insertion
mask replay
actor/critic optimizer step
save/load/resume
invalid checkpoint hard-error validation
```

这不是性能训练。

### Phase 9G-8I

```text
Commit-Readiness Review
```

确认：

```text
default-off legacy identity
single lifecycle behavior source
frozen schema/fingerprint
frozen mask replay contract
checkpoint boundaries
training-readiness evidence
无 retry/TTL/infeasibility-release 越界实现
```
