# 三台异构移动机械臂扫描环境

`Isaac-Scan-Mobile-Manipulator-Direct-v0` 是一个用于验证多智能体扫描任务的 Isaac Lab / HARL baseline 环境。任务场景中有三台异构移动机械臂围绕一个大型构件移动，每台机器人需要把末端扫描仪移动到若干预定义扫描视点，协作完成视点覆盖。

当前版本刻意保持在“高层任务空间”：

- 机器人状态保存在 GPU/CPU tensor 中，而不是真实 PhysX articulation。
- GUI 中的底盘、扫描仪和视点都是 USD debug marker，仅用于观察。
- 扫描成功由位置误差、姿态误差、机械臂可达性、传感器量程和 FOV 规则判定。
- 原有 9D 连续动作训练路径仍然保留；高层 viewpoint assignment 只是额外的 baseline/evaluation 路径。

## 文件结构

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
├── __init__.py
├── README.md
├── assignment_controller.py
├── assignment_wrapper_coding_tasks.md
├── scan_mobile_manipulator_env.py
├── agents/
│   ├── __init__.py
│   └── harl_happo_cfg.yaml
└── solvers/
    ├── __init__.py
    ├── base_solver.py
    ├── greedy_solver.py
    ├── nearest_solver.py
    └── random_solver.py

scripts/environments/
├── evaluate_scan_assignment.py
└── view_scan_assignment.py
```

主要文件作用：

- `__init__.py`：注册 Gym task id，并把 HARL/HAPPO 配置入口暴露给 Isaac Lab。
- `scan_mobile_manipulator_env.py`：环境主体，包含配置、状态缓存、动作积分、观测、奖励、终止、扫描覆盖和 GUI marker。
- `assignment_controller.py`：把高层 `robot_i -> viewpoint_j` 分配结果转成环境可执行的 9D 连续动作。
- `solvers/`：三个可直接用于 baseline 的高层分配器：`random`、`nearest`、`greedy`。
- `agents/harl_happo_cfg.yaml`：HARL HAPPO 配置入口，当前保留异构机器人设置。
- `evaluate_scan_assignment.py`：headless 评估脚本，可输出 summary 和 CSV。
- `view_scan_assignment.py`：GUI viewer，展示 solver/controller 在环境中的行为。

## 环境注册

环境在 `__init__.py` 中注册：

```python
id="Isaac-Scan-Mobile-Manipulator-Direct-v0"
entry_point="isaaclab_tasks.direct.scan_mobile_manipulator:ScanMobileManipulatorEnv"
```

使用 Isaac Lab / HARL 脚本时传入：

```text
--task Isaac-Scan-Mobile-Manipulator-Direct-v0
```

即可创建 `ScanMobileManipulatorEnvCfg` 和 `ScanMobileManipulatorEnv`。

## 机器人与任务模型

### Agent

当前有三台机器人，每台机器人对应一个 HARL agent：

```python
possible_agents = ["robot_0", "robot_1", "robot_2"]
action_spaces = {"robot_0": 9, "robot_1": 9, "robot_2": 9}
observation_spaces = {"robot_0": 96, "robot_1": 96, "robot_2": 96}
```

三台机器人动作维度相同，但能力参数不同，因此仍按异构 agent 处理。

### 构件代理

大型构件当前用一个轴对齐包围盒近似：

```python
component_center = (0.0, 0.0, 1.0)
component_half_extents = (3.0, 1.0, 1.0)
```

传感器量程判定使用“扫描仪到包围盒外表面”的距离。后续接真实构件 USD/mesh 时，可以把这部分替换成 raycast、surface patch 或点云覆盖模型。

### 扫描视点

`viewpoint_poses` 的每一项为：

```text
(x, y, z, qw, qx, qy, qz)
```

四元数使用 Isaac Lab 常用的 WXYZ 顺序，不是 ROS 常见的 XYZW 顺序。

### 异构能力参数

异构性主要由以下配置体现：

```python
arm_reach = (2.0, 3.0, 1.6)
scanner_min_range = (0.25, 0.35, 0.20)
scanner_max_range = (1.4, 2.0, 1.1)
scanner_fov_deg = (65.0, 90.0, 50.0)
max_base_xy_step = (0.08, 0.10, 0.06)
max_ee_xyz_step = (0.07, 0.09, 0.05)
```

含义：

- `robot_0`：中等臂展和中等扫描范围。
- `robot_1`：更大臂展、更大扫描范围、更宽 FOV。
- `robot_2`：更小臂展、更小扫描范围，移动和末端调整更慢。

这些参数会同时影响动作缩放、可行性掩码、扫描成功判定和观测中的 capability 特征。

## 9D 连续动作路径

每个 agent 的底层动作是：

```text
[base_dx, base_dy, base_dyaw, ee_dx, ee_dy, ee_dz, ee_droll, ee_dpitch, ee_dyaw]
```

动作先被 clamp 到 `[-1, 1]`，再乘以对应机器人的最大步长。当前动作不驱动物理关节，而是在 `_integrate_high_level_actions()` 中更新任务空间状态：

- `base_pos`
- `base_yaw`
- `scanner_pos`
- `scanner_quat`

如果扫描仪离底盘超过该机器人的 `arm_reach`，扫描仪位置会被裁回可达球面内，并记录 `last_reach_violation` 用于惩罚。

## 高层 assignment 路径

高层分配路径用于传统任务分配算法或后续高层 RL policy：

```python
problem = env.unwrapped.get_assignment_problem()
assignment = solver.solve(problem)
actions = viewpoint_assignment_to_actions(env.unwrapped, assignment)
obs, rewards, terminated, truncated, info = env.step(actions)
```

`assignment` 的形状为：

```text
[num_envs, num_agents]
```

每个元素是 viewpoint id；`-1` 表示该机器人 no-op。

### get_assignment_problem()

`get_assignment_problem()` 返回当前高层分配所需的结构化信息：

```python
{
    "base_pos": Tensor[num_envs, num_agents, 3],
    "base_yaw": Tensor[num_envs, num_agents],
    "scanner_pos": Tensor[num_envs, num_agents, 3],
    "scanner_quat": Tensor[num_envs, num_agents, 4],
    "viewpoint_pos": Tensor[num_envs, num_viewpoints, 3],
    "viewpoint_quat": Tensor[num_envs, num_viewpoints, 4],
    "viewpoints_covered": Tensor[num_envs, num_viewpoints],
    "cost_matrix": Tensor[num_envs, num_agents, num_viewpoints],
    "feasible_mask": Tensor[num_envs, num_agents, num_viewpoints],
    "available_mask": Tensor[num_envs, num_agents, num_viewpoints],
}
```

所有 tensor 保持在 `env.device`，便于 GPU 上直接计算。当前可行性是移动底盘任务的高层近似：只要求视点高度在机械臂可达范围内，并且视点到构件包围盒表面的距离满足对应扫描仪量程。`available_mask` 会进一步排除已经覆盖的视点。

### assignment_controller.py

`viewpoint_assignment_to_actions(env, assignment)` 会：

1. 检查 `assignment` 的 dtype、shape 和 device。
2. 对 `-1`、越界、已覆盖或不可行目标输出零动作。
3. 对有效目标生成底盘 xy/yaw 动作，让底盘朝目标靠近。
4. 生成扫描仪 xyz 动作，让末端扫描仪靠近视点。
5. 生成扫描仪 roll/pitch/yaw 动作，让姿态趋近视点四元数。
6. 返回 DirectMARLEnv 需要的 action dict。

这条路径不替代原有 action space，只是把高层离散分配转换为已有 9D 连续动作。

### Baseline solvers

`solvers/` 中的 solver 都返回同一格式的 `torch.long` assignment tensor：

- `random`：每个机器人随机选择一个 available viewpoint，并在同一环境内避免重复。
- `nearest`：每个机器人选择当前最近的 available viewpoint。
- `greedy`：按 `1 / distance` 得分贪心选择 available viewpoint。

三个 solver 都按 env 逐个处理，同时保证返回 tensor 保持在 `available_mask.device`。

## 观测

每个 agent 当前观测为 96 维：

| 部分 | 维度 | 说明 |
| --- | ---: | --- |
| `base_rel` | 3 | 底盘位置，按 env spacing 归一化 |
| `yaw_sincos` | 2 | 底盘 yaw 的 sin/cos |
| `scanner_rel` | 3 | 扫描仪位置，按 env spacing 归一化 |
| `scanner_quat` | 4 | 扫描仪四元数，WXYZ |
| `coverage_ratio` | 1 | 当前 episode 的视点覆盖比例 |
| `capability` | 4 | 臂展、传感器最小/最大距离、FOV cos |
| `viewpoint_obs` | 64 | 最近 8 个未覆盖视点，每个 8 维 |
| `other_scanners` | 6 | 另外两台机器人的扫描仪相对位置 |
| `previous_action` | 9 | 上一步动作 |

最近视点条目格式：

```text
[rel_x, rel_y, rel_z, qw, qx, qy, qz, valid]
```

当视点不足或已经覆盖时，`valid=0`。

## 扫描成功判定

`_update_scan_progress()` 在每一步 done/reward 前更新覆盖状态。一个机器人扫描到某个视点，需要同时满足：

1. 扫描仪位置接近视点位置。
2. 扫描仪姿态接近视点姿态。
3. 视点在该机器人机械臂工作空间内。
4. 扫描仪到构件代理包围盒的距离在传感器量程内。
5. 扫描仪朝向满足 FOV 约束。
6. 达到 `dwell_steps` 连续停留步数。

当前 `dwell_steps = 1`，满足条件后立即覆盖。多机器人同一帧扫描到同一个新视点时，全局覆盖只增加一次，参与机器人平分自身覆盖贡献；重复扫描已覆盖视点会产生 duplicate penalty。

## 奖励与终止

奖励由 `_get_rewards()` 计算：

```text
reward =
  global_coverage_reward_scale * 新覆盖视点数
+ own_coverage_reward_scale * 本机器人覆盖贡献
- duplicate_scan_penalty_scale * 重复扫描
- reach_violation_penalty_scale * 工作空间越界
- action_rate_penalty_scale * 动作变化
- time_penalty
```

终止条件：

- `terminated`：所有视点都被覆盖。
- `time_out`：达到最大 episode 长度。

默认 `episode_length_s = 30.0`、`dt = 1/60`、`decimation = 6`，策略步长约为 0.1 秒，一个 episode 约 300 个策略步。

## GUI debug marker 与灯光

GUI 中的可视化由 `_create_static_usd_debug_scene()` 和 `_update_usd_debug_visuals()` 负责：

- 蓝色构件块：`LargeComponentVisual`
- 三个底盘块：`Robot_0_BaseMarker` 等
- 三个扫描仪球：`Robot_0_ScannerMarker` 等
- 青色扫描视点球：`Viewpoint_00` 等

这些 prim 不参与物理仿真，只用于调试高层状态。GUI 运行和 `--video` 触发的 camera-enabled headless
渲染都会同步动态 marker；普通 headless 训练/评估没有渲染上下文时会跳过同步以减少开销。

为避免 DomeLight 带来的白色背景，同时改善 DistantLight 过暗的问题，GUI 模式下环境默认请求 Kit 的 `Camera Light` viewport lighting mode。相关开关为：

```python
use_camera_light_in_gui = True
```

## 常用命令

### 最小语法检查

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
```

### Headless viewer smoke test

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/view_scan_assignment.py --headless --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 1 --max_steps 1 --print_interval 1 --step_rate 0
```

### GUI 查看 assignment baseline

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/view_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 1 --step_rate 2
```

### Headless 评估

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 2 --num_episodes 2 --max_steps_per_episode 50 --headless
```

### HARL 小规模 smoke

HARL 的 on-policy runner 会按 `num_env_steps // episode_length // num_envs` 计算训练 episode 数。默认
`episode_length=256`，所以 `num_envs=2` 时至少需要 `num_env_steps=512` 才会真正进入一轮训练循环并打印日志。

`train.py` 会在 Isaac Kit 启动前先执行一次很小的 PyTorch CUDA Linear，用来提前初始化 cuBLAS，避免
Kit 启动后第一次 policy 前向传播时出现 `CUBLAS_STATUS_NOT_INITIALIZED`。

训练启动后脚本会打印 HARL run/model 目录；训练正常结束后还会显式保存一次最终模型，并在关闭前
finalize 正在录制的 `RecordVideo`：

```text
[INFO]: HARL run directory: ...
[INFO]: HARL model directory: ...
[INFO]: Saved final HARL model to: ...
```

如果训练时加 `--video`，HARL/Isaac Lab 的 `RecordVideo` 会在第 0 个环境步先录第一段视频，然后再按
`--video_interval` 间隔录制。因此第一段视频通常是未训练策略的早期行为；要看训练后的策略效果，可以查看
后续 interval 视频，或训练完成后用 `play.py --dir <model_dir>` 回放模型。

视频 smoke 时不要把 `--video_interval` 设成 1，否则每一步都会触发一次新录制。下面这条命令只生成一个
32 步短视频：

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py `
  --video `
  --video_length 32 `
  --video_interval 64 `
  --num_envs 1 `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --seed 1 `
  --save_interval 1 `
  --log_interval 1 `
  --exp_name video_smoke `
  --num_env_steps 32 `
  --algorithm happo `
  --headless `
  "agent.train.episode_length=32"
```

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --algorithm happo `
  --num_envs 2 `
  --num_env_steps 512 `
  --save_interval 1 `
  --log_interval 1 `
  --headless
```

如果只想做 16 个环境步的极小 smoke，可以同时覆盖 HARL 的 rollout 长度：

```powershell
.\isaaclab.bat -p scripts\reinforcement_learning\harl\train.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --algorithm happo `
  --num_envs 2 `
  --num_env_steps 16 `
  --save_interval 1 `
  --log_interval 1 `
  --headless `
  "agent.train.episode_length=8"
```

## 后续接入真实机器人

建议按以下顺序演进：

1. 替换构件几何和视点数据：把包围盒代理换成真实 USD/mesh，并导入真实扫描视点。
2. 在 `_setup_scene()` 中注册真实机器人资产：添加三台移动机械臂的 `ArticulationCfg` 或等价资产。
3. 替换 `_integrate_high_level_actions()`：从直接改 tensor 改为底盘速度控制、IK 或 operational space control。
4. 从真实 link/frame 读取扫描仪位姿：使用末端 link pose 或 `FrameTransformer` 替代当前缓存的 `scanner_pos/scanner_quat`。
5. 替换覆盖模型：用 raycast、点云覆盖率、mesh surface patch 或质量评分替代当前规则判定。
6. 加入安全约束：机器人之间、机器人与构件之间的碰撞约束，以及底盘可行驶区域。

## 当前限制

- 没有真实底盘动力学。
- 没有真实机械臂关节、关节限位和 IK 失败。
- 没有碰撞检测。
- 构件只是包围盒代理。
- 扫描质量是规则判定，不是 raycast 或点云覆盖。
- USD marker 只用于 GUI 调试，不参与训练物理。

这些限制是有意保留的，目的是先验证 MARL 任务拆分、HARL 训练流程、高层 viewpoint assignment、覆盖奖励和异构 agent 设置，再逐步替换为真实机器人与扫描模型。
