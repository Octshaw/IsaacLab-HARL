# Codex 修改任务：完善 random / nearest / greedy 任务分配 baseline 评估脚本

## 背景

当前项目包含 Isaac Lab 任务 `Isaac-Scan-Mobile-Manipulator-Direct-v0`。该任务用于三台异构移动机械臂协作扫描大型构件。当前已经实现了高层 viewpoint assignment 路径：

```python
problem = env.unwrapped.get_assignment_problem()
assignment = solver.solve(problem)
actions = viewpoint_assignment_to_actions(env.unwrapped, assignment)
obs, rewards, terminated, truncated, info = env.step(actions)
```

当前 baseline solver 包括：

- `random`
- `nearest`
- `greedy`

本次任务只修改/完善传统 baseline 的评估脚本，暂时不要接入 RL / HARL / HAPPO。RL policy 的评估后续单独新写脚本。

主要目标是把 `scripts/environments/evaluate_scan_assignment.py` 打磨成一个更可靠、更清晰、更适合后续实验表格统计的 baseline evaluator。

---

## 修改范围

主要修改文件：

```text
scripts/environments/evaluate_scan_assignment.py
```

如有必要，可以少量修改 README 或添加注释，但不要改环境动力学、reward、solver 策略本身，也不要改 `scan_mobile_manipulator_env.py` 的核心逻辑。

---

## 总体目标

请完成以下改动：

1. 保持当前脚本只支持 `random / nearest / greedy` 三个 assignment solver。
2. 不接入 RL，不加载 checkpoint，不修改 HARL 训练流程。
3. 改善 episode 统计语义，避免 `num_episodes` 在 vectorized env 下产生误解。
4. 拆分重复统计指标，区分：
   - 同一步 assignment 中多个机器人选择同一个 viewpoint；
   - 环境实际发生的重复扫描已覆盖 viewpoint。
5. 增加更适合比较 baseline 的指标：
   - `steps_to_50_coverage`
   - `steps_to_80_coverage`
   - `coverage_auc`
   - 可选：`mean_action_norm`
   - 可选：`mean_action_delta`
6. 增强 seed 控制与 done tensor 处理鲁棒性。
7. 保持脚本可以 headless 运行，并能输出 summary 与 CSV。

---

## 具体修改要求

### 1. CLI 参数语义调整

当前参数：

```python
parser.add_argument("--num_episodes", type=int, default=1, help="Number of episodes to collect.")
```

在 vectorized env 下，当前实现的含义是“总共收集多少条 episode record”，而不是“每个并行环境跑多少个 episode”。这容易在实验统计时误解。

请改成以下两种方案之一。优先采用方案 A。

#### 方案 A，推荐

新增参数：

```python
--num_episodes_per_env
```

含义：每个并行环境收集多少个完整 episode record。

例如：

```bash
--num_envs 8 --num_episodes_per_env 20
```

最终应收集：

```python
target_records = num_envs * num_episodes_per_env
```

为了兼容旧命令，可以保留 `--num_episodes`，但建议：

- 将其标记为 deprecated；
- 如果用户传入 `--num_episodes` 且没有传入 `--num_episodes_per_env`，则把它解释为旧语义：总 record 数；
- print warning 说明推荐使用 `--num_episodes_per_env`。

如果实现兼容逻辑太麻烦，可以直接替换为 `--num_episodes_per_env`，但需要同步更新脚本中的 help 文本和 README 命令。

#### 方案 B，次选

保留 `--num_episodes`，但明确 help 文本：

```python
help="Total number of vector-env episode records to collect, not episodes per environment."
```

并在 print 信息中显示：

```text
num_envs=..., target_episode_records=...
```

---

### 2. 拆分 duplicate 指标

当前脚本里 `duplicate_count` 同时累加了：

```python
duplicate_count += _assignment_duplicate_count(assignment)
```

以及：

```python
if hasattr(unwrapped, "last_duplicate_scans"):
    duplicate_count += unwrapped.last_duplicate_scans.sum(dim=1)
```

请把它拆成两个独立指标。

#### 新增变量

```python
assignment_duplicate_count = torch.zeros(num_envs, dtype=torch.float32, device=device)
scan_duplicate_count = torch.zeros(num_envs, dtype=torch.float32, device=device)
```

#### 每步统计

```python
assignment_duplicate_count += _assignment_duplicate_count(assignment)

if hasattr(unwrapped, "last_duplicate_scans"):
    scan_duplicate_count += unwrapped.last_duplicate_scans.sum(dim=1)
```

#### CSV 字段

删除或不再使用旧的：

```text
duplicate_count
```

改为：

```text
assignment_duplicate_count
scan_duplicate_count
```

#### summary 字段

新增：

```text
mean_assignment_duplicate_count
mean_scan_duplicate_count
```

不要把这两种重复行为混在一个字段里。

---

### 3. 增加 coverage 过程指标

请增加以下 episode-level 指标。

#### 3.1 steps_to_50_coverage

每个 env 在当前 episode 中第一次达到覆盖率 `>= 0.5` 的 step。

如果 episode 结束前没有达到，则记录：

```python
-1
```

#### 3.2 steps_to_80_coverage

每个 env 在当前 episode 中第一次达到覆盖率 `>= 0.8` 的 step。

如果没有达到，则记录：

```python
-1
```

#### 3.3 coverage_auc

统计每个 episode 覆盖率曲线的面积，用于衡量覆盖推进速度。可以采用简单离散平均：

```python
coverage_auc += current_coverage
```

episode 结束时：

```python
coverage_auc_normalized = coverage_auc / episode_length
```

CSV 中建议字段名为：

```text
coverage_auc
```

这个值越大，说明整个 episode 中覆盖推进越快。

#### 实现提示

新增 tensor：

```python
steps_to_50 = torch.full((num_envs,), -1, dtype=torch.long, device=device)
steps_to_80 = torch.full((num_envs,), -1, dtype=torch.long, device=device)
coverage_auc = torch.zeros(num_envs, dtype=torch.float32, device=device)
```

每步得到 `step_coverage` 后：

```python
coverage_auc += step_coverage

hit_50 = (steps_to_50 < 0) & (step_coverage >= 0.5)
steps_to_50[hit_50] = episode_lengths[hit_50]

hit_80 = (steps_to_80 < 0) & (step_coverage >= 0.8)
steps_to_80[hit_80] = episode_lengths[hit_80]
```

生成 record 时，如果 `episode_length > 0`：

```python
coverage_auc_record = coverage_auc[env_id] / episode_lengths[env_id]
```

---

### 4. 可选增加动作统计

如果实现方便，请增加下面两个指标。如果担心改动过大，可以跳过，但不要影响前面必做项。

#### 4.1 mean_action_norm

统计每个 env 每一步所有 agent action 的平均 L2 norm。

伪代码：

```python
def _action_norm(actions, agents, num_envs, device):
    values = []
    for agent in agents:
        action = actions[agent].to(device=device).reshape(num_envs, -1)
        values.append(torch.linalg.norm(action, dim=-1))
    return torch.stack(values, dim=0).mean(dim=0)
```

每步：

```python
action_norm_sum += _action_norm(actions, agents, num_envs, device)
```

episode 结束时：

```python
mean_action_norm = action_norm_sum / episode_length
```

#### 4.2 mean_action_delta

统计动作变化幅度，反映是否抖动。

需要维护上一帧 action。建议实现一个 helper，把 action dict stack 成 `[num_envs, num_agents, action_dim]`。

第一步没有 previous action，可以不计入 delta。记录 `action_delta_count` 避免除零。

---

### 5. 增强 seed 控制

当前脚本只设置了 env config seed 和 `env.reset(seed=args_cli.seed)`。请增加 Python、NumPy、PyTorch 的随机种子控制。

在 parse args 之后或 `main()` 开始处添加 helper：

```python
def _set_global_seeds(seed: int | None):
    if seed is None:
        return
    import random
    import numpy as np

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
```

注意：`torch` 是在 AppLauncher 之后 import 的，所以 helper 位置要放在 `import torch` 之后。

在 `main()` 中创建 env/solver 前调用：

```python
_set_global_seeds(args_cli.seed)
```

---

### 6. 增强 `_as_bool_tensor` 鲁棒性

当前实现：

```python
def _as_bool_tensor(value, num_envs: int, device: torch.device) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.to(device=device, dtype=torch.bool).reshape(num_envs)
    return torch.as_tensor(value, dtype=torch.bool, device=device).reshape(num_envs)
```

请改成能够处理 scalar bool、list、tensor 的版本。

建议实现：

```python
def _as_bool_tensor(value, num_envs: int, device: torch.device) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        tensor = value.to(device=device, dtype=torch.bool)
    else:
        tensor = torch.as_tensor(value, dtype=torch.bool, device=device)

    tensor = tensor.flatten()
    if tensor.numel() == 1:
        return tensor.expand(num_envs)
    if tensor.numel() != num_envs:
        raise RuntimeError(f"done tensor size mismatch: expected {num_envs}, got {tensor.numel()}")
    return tensor
```

---

### 7. 记录字段更新

请同步更新 `_make_record()`、`_summarize()` 和 `_write_csv()`。

建议最终每条 CSV record 至少包含：

```text
episode_id
solver
env_id
coverage_ratio
success
episode_length
total_reward
assignment_duplicate_count
scan_duplicate_count
reach_violation_count
steps_to_50_coverage
steps_to_80_coverage
coverage_auc
robot_0_coverage_gain
robot_1_coverage_gain
robot_2_coverage_gain
```

如果实现了动作统计，再加：

```text
mean_action_norm
mean_action_delta
```

注意：当前 `robot_coverage` 实际更像累计 coverage gain，不建议继续命名为 `robot_i_coverage`，容易被理解成比例。请改名为：

```text
robot_i_coverage_gain
```

summary 中建议包含：

```text
episodes
mean_coverage_ratio
success_rate
mean_episode_length
mean_total_reward
mean_assignment_duplicate_count
mean_scan_duplicate_count
mean_reach_violation
mean_steps_to_50_coverage
mean_steps_to_80_coverage
mean_coverage_auc
mean_per_robot_coverage_gain
```

对于 `steps_to_50_coverage == -1` 或 `steps_to_80_coverage == -1` 的 episode，summary 可以同时给出两类结果：

1. `mean_steps_to_50_coverage_reached_only`：只统计达到阈值的 episode；
2. `steps_to_50_coverage_reach_rate`：达到 50% 覆盖率的 episode 比例；

80% 同理。

如果不想增加太多字段，至少保证 `-1` 不会被直接混进均值导致结果误导。

---

### 8. episode reset 与 solver reset

当前脚本在任意 env done 后调用：

```python
solver.reset()
```

当前 random/nearest/greedy 可能是无状态 solver，因此问题不大。但为了后续扩展，建议：

- 如果 solver 没有 per-env 状态，可以保留，但加注释说明当前 baseline solver 是 stateless；
- 如果 solver 支持 `reset(done_ids)`，则优先按 done env reset；
- 不要为了这个任务大改 solver 接口。

建议简单做法：

```python
# Current assignment baselines are stateless; keep a full reset for compatibility.
solver.reset()
```

---

### 9. coverage 统计逻辑

当前代码对 `post_coverage` 的处理比较绕：

```python
post_coverage = unwrapped.viewpoints_covered.float().mean(dim=-1)
step_coverage = torch.where(env_done & (~terminated_tensor), pre_coverage, post_coverage)
step_coverage = torch.where(terminated_tensor, torch.ones_like(step_coverage), step_coverage)
max_coverage = torch.maximum(max_coverage, step_coverage)
```

请检查这段逻辑是否仍然必要。

原则：

- 对正常未结束 step，用 step 后的 coverage；
- 对 terminated step，coverage 应为 1.0 或 step 后 coverage；
- 对 truncated/time-out step，尽量记录 episode 结束时真实 coverage，不要低估最后一步刚产生的新覆盖；
- 如果 Isaac Lab wrapper 在 env done 后已经自动 reset，导致 `unwrapped.viewpoints_covered` 读到 reset 后状态，则需要保留 `pre_coverage` 或从 info 中找 final coverage。

本任务不要大改环境。如果无法可靠获取 done 前 final coverage，请在代码注释中说明当前为什么使用 `pre_coverage` 或 `post_coverage`。

---

## 输出与命令

请保证以下命令仍能运行。

### 语法检查

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/evaluate_scan_assignment.py
```

### random smoke test

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/evaluate_scan_assignment.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --solver random `
  --num_envs 2 `
  --num_episodes_per_env 1 `
  --max_steps_per_episode 50 `
  --headless
```

### nearest smoke test

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/evaluate_scan_assignment.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --solver nearest `
  --num_envs 2 `
  --num_episodes_per_env 1 `
  --max_steps_per_episode 50 `
  --headless
```

### greedy smoke test

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/evaluate_scan_assignment.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --solver greedy `
  --num_envs 2 `
  --num_episodes_per_env 1 `
  --max_steps_per_episode 50 `
  --headless
```

### CSV 输出测试

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/evaluate_scan_assignment.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --solver greedy `
  --num_envs 2 `
  --num_episodes_per_env 1 `
  --max_steps_per_episode 50 `
  --save_csv logs/scan_assignment/greedy_eval.csv `
  --headless
```

---

## 验收标准

完成后请确认：

1. `evaluate_scan_assignment.py` 可以通过 `py_compile`。
2. `random / nearest / greedy` 三个 solver 都可以 headless 跑通。
3. summary 中不再出现含义混杂的 `duplicate_count`。
4. CSV 中包含独立的：
   - `assignment_duplicate_count`
   - `scan_duplicate_count`
   - `steps_to_50_coverage`
   - `steps_to_80_coverage`
   - `coverage_auc`
5. `robot_i_coverage` 已改名为 `robot_i_coverage_gain`，或至少新增更清晰的字段名。
6. 多环境运行时，episode record 数符合新的参数语义。
7. 设置相同 `--seed` 时，random baseline 的结果应尽量可复现。
8. 不要引入 RL / HARL policy 相关依赖。
9. 不要修改 solver 策略逻辑本身。
10. 修改后请在最终回复中列出：
    - 修改了哪些文件；
    - 新增/改名了哪些 CSV 字段；
    - 执行了哪些测试命令；
    - 哪些测试通过，哪些没跑或失败。

---

## 额外建议

如果时间和上下文额度允许，可以额外添加一个简短的打印表格，让 summary 更容易读，例如：

```text
[RESULT]: Scan assignment evaluation summary
solver: greedy
episodes: 16
mean_coverage_ratio: ...
success_rate: ...
mean_episode_length: ...
mean_total_reward: ...
mean_assignment_duplicate_count: ...
mean_scan_duplicate_count: ...
mean_reach_violation: ...
mean_coverage_auc: ...
mean_per_robot_coverage_gain: [..., ..., ...]
```

但不要为了漂亮输出牺牲核心统计逻辑。
