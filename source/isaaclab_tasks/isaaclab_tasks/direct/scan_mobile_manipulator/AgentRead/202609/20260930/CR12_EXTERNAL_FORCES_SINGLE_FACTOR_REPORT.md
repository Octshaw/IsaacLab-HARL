# CR12 外力逐迭代设置：单因素实施与原条件复测报告

日期：2026-09-30（Asia/Shanghai，UTC+08:00）。状态：**已实施；显式 on 的原 720 步运动/保持验收 PASS；等待 GPT/用户审阅。** 本报告不自行赋予 GPT REVIEW PASS，不自动关闭后续机器人接入事项。

## 1. 结论与边界

用户明确选择方案 A，并授权单因素实施、CPU 检查及有限 GUI 运行。本轮在原独立 CR12 场景添加 `--external-forces-every-iteration {inherit,on,off}`，**默认仍为 inherit**。实际唯一物理改动是将 `/physicsScene.physxScene:enableExternalForcesEveryIteration` 从 resolved=false、unauthored 改为本次匿名 session layer 的显式 true。

结果分开记录：

- **原完整驱动验收 PASS**：显式 on 的 attempt_02 完成 720 个受控步、6.000000312924385 秒、360 次原渲染调用；原 5–6 秒窗口完整 121/121 样本，六轴均通过原位置/原生速度标准，joint_2 最终 5.297713713°。clock/joint/contact/geometry/frame 各 720 PASS，未放宽阈值或替换验收速度。
- **积分差异明显改善**：共同 4–5 秒内，轴 5 的 |R| 从 0.02318491017 降为 4.293512053e-8 rad；轴 6 从 0.02597362052 降为 2.103638338e-8 rad。相对各自旧 |R| 下降 99.9998148% / 99.9999190%。
- **不是一次无失败的运行过程**：attempt_01 在写属性及首次 reset 前因 `GetPropertyStack` 缺少本地要求的时间参数失败，0 个受控步；修正这处来源记录 API 后，使用唯一获授权的局部修复重试取得上述结果。两次 App 全部自然退出，App 2/3；main 1/1、repair_retry 1/1、matched_false 0/1。不再运行。
- 保留旧 false / 旧 PD 候选 FAIL。新配置结果支持该设置在**当前固定底盘、lift0、v1、baseline、TGS 8/2、指定 5° 轨迹**中改善此前差异并通过原判据；不能证明 SDK 唯一根因、内部具体求解阶段，或所有构型/负载/轨迹均成立。

建议经审阅后在当前独立 CR12 场景继续**显式选择 on**，本轮不提升默认，不修改全局设置。Phase B 保持 COMPLETE / GPT REVIEW PASS / CLOSED；已接受 Windows 启动与 v1 成果不重开。

## 2. 用户视觉反馈与未变条件

人工可视化**已经发生**。用户认为整体比例没有明显问题，但 5° 动作太小，尚不能据此确认细微跳变、穿插或保持稳定；底盘、末端等仿真显示像被封闭/填充。准确记录：

> 源OBJ由用户确认正常；仿真显示几何存在差异，原因待查。

本轮遵用户决定后置显示调查；没有检查或修复 visual/collision 显示、visibility/purpose、材质、mesh、导入逻辑或 viewport，没有扩大角度、慢放或另开演示 App。不能把这次有限物理守卫通过写成人工完整可视化 PASS，也不能由此断言显示差异不影响后续碰撞或扫描。

唯一使用资产：[fixed_lift0_v1/usd/cr12_fixed_lift0.usd](../../../assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd) 及其现有引用层。没有生成 v2，没有导入/转换/保存/导出 USD，没有改原始或派生 URDF、mesh、质量、COM、惯量、固定关系或驱动限制。

| 项目 | 历史 false 与本轮 true 共同条件 |
|---|---|
| PD | K=(200,4000,2000,200,1000,150)，D=(20,550,166,12,37,7)，profile=baseline |
| 执行器限制 | effort=(20,60,30,10,10,5) Nm；velocity_limit_sim=0.2 rad/s |
| 场景/物理 | 固定底盘、升降 q0=0；dt=1/120，render_interval=2，GPU pipeline/dynamics，TGS，articulation 8/2 |
| 重力/solver clamp | (0,0,-9.81)；position min/max=1/255，velocity=0/255 |
| 其余参数 | 原 sleep/stabilization、摩擦、armature、contact/rest offset、自碰撞和过滤不变 |
| 初始化 | 原一次 root anchor 校准；reset 一次含 2 个初始化物理步；一次初始关节状态写入；无 root 状态写入、无额外 settle/reset |
| 控制 | 0–1s 保持；1–3s joint_2 五次轨迹 0→5°；3–6s 保持；其他轴目标 0；同时下发原位置及解析速度目标 |
| 状态与监测 | 原 normal update 后 q/dq 验收快照、同刻 native/link 探针及同步/复制顺序；原接触→关节→body pose→geometry/frame→偶数 render 顺序 |

## 3. 实施落点、时机与证据层级

### 3.1 局部改动

| 文件/关键符号 | 本轮变更 |
|---|---|
| `scripts/environments/run_cr12_joint_drive.py:131` `_parse_args` | 新选项及 explicit_cli/default_inherit 来源；PD 和诊断开关不决定 flag |
| 同文件 `_run_drive:658`；构造前 :677、构造后 :692、设置 :715 | 记录并检查 native running、timeline、tensor-view 状态；读取实际 scene path；首次 reset 前应用局部设置 |
| 同文件 :775 / :836 / :1065 | after_first_reset、before_motion、before_exit 配置读回；退出读回失败保留既有首因，不强行报告完整通过 |
| `scripts/environments/_cr12_external_forces.py:26,31,42,60,95,114` | CLI、类型/scene/API 校验、属性来源、session 写入与 edit target 恢复、模式期望和失败粘性；不导入 runtime |
| `scripts/environments/_cr12_state_consistency.py:330` `StateConsistencyTrace.summary` | 只补 all_controlled=1…720、observed_comparison_complete；保留旧 requested_1_600 和原 FAIL，不动采样/计算 |
| `source/isaaclab_tasks/test/test_cr12_external_forces.py` | fake scene/API、真实 drive parser、失败和 600/720 覆盖测试 |
| `logs/scan_assignment/20260930_cr12_external_forces/repro/supervise_cr12_external.py` | 沿用原 Windows Job/输出排空/180s与360s监督；显式转发 on/off、三种运行预算、配置/诊断/原运动验收分开 |

本轮修改前文本与当前源码对照确认：`check_clock/check_joint_sample/_calibrate_root_anchor/_read_physics/_body_poses/_check_geometry/_check_frames/_make_contacts/_check_contacts/_joint_state/_state_joint_frames/_solver_observation/_probe_state/_capture_submitted_targets` 及受控循环未改；特别保留 `_body_poses` 引发的既有 kinematic 刷新位置。使用本轮增量补丁判断，不以 HEAD 或旧 PASS 标题代替工作区检查。

### 3.2 首次初始化之前设置的依据

本地安装前缀 `P=C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim/`。定向源码调用链：

1. `source/isaaclab/isaaclab/sim/simulation_context.py:233–241,619–629` 调 core 构造并配置场景。
2. `P/exts/isaacsim.core.api/isaacsim/core/api/simulation_context/simulation_context.py:1285–1312` 创建 PhysicsContext；同包 `physics_context/physics_context.py:234–238` 定义 PhysicsScene、应用 PhysxSceneAPI。构造中的 render/app.update 禁止 physics playback，并非“构造没有 app.update”。
3. 首次 `sim.reset()` 经 core `simulation_context.py:598–601,848–865` 调 PLAY，再经 `P/exts/isaacsim.core.simulation_manager/isaacsim/core/simulation_manager/impl/simulation_manager.py:107–130` 执行 force_load_physics_from_usd→start_simulation→warm-up→tensor view。当前同步路径没有调用另一条异步 reset 分支。
4. 本轮设置插在构造返回后，机器人构造及上述 reset 前。实际 scene path 来自 `PhysicsContext.prim_path`（`physics_context.py:197–198`），没有仅凭 cfg 猜路径。

运行保护并非只检查 tensor view。构造前和构造后 `native_physics.is_running=false`，`timeline_playing=false`、`timeline_stopped=true`；构造后 `sim.is_simulating=false`、`reset_started=false`。`omni.physx/.../bindings/_physx.pyi:1696–1700` 的 is_running 文档覆盖 PLAY 或 attach；`:1272–1277` 的 get_attached_stage 只记录读到的 0，未把未文档化哨兵当成独立“未 attach”证明。构造前保护避免 core 自动 stop 既有 timeline 掩盖早期活动。

`PhysxSceneAPI.GetEnableExternalForcesEveryIterationAttr` 来源：`P/extsPhysics/omni.usd.schema.physx/pxr/PhysxSchema/__init__.pyi:2020`。没有扩展 SimulationCfg、修改框架或换成全局 carb 猜测键。

### 3.3 默认与写层语义

- inherit：不 Set、不 Apply API、不切换 edit target；保留原始 resolved/authored/opinion。若原状态不是旧 false 基线，则如实记录差异，不由默认选项强制覆盖。
- on/off：期望从 CLI 模式固定映射为 true/false。初始状态不满足 `resolved=false 且 authored=false` 时，报 SETUP_CONFIG_FAILED，避免掩盖额外来源。
- 写入前验证 PhysicsScene、已应用 API、有效 bool 属性；只有匿名 session layer 可写。切换后先确认实际 edit target 是 session，再 Set；finally 恢复原 edit target，核对成功。没有 Save/Export。
- 四阶段读回一致才通过配置核验；不存在属性、错误类型、错误意见来源或值不符均失败。退出前读回失败不能由 work_completed 或 exit0 覆盖。

attempt_02 实际属性与意见来源：

| 时刻 | resolved | authored | 意见来源 |
|---|---|---|---|
| before | false | false | property_stack=[]，schema fallback |
| after_apply | true | true | 匿名 session default=true |
| after_first_reset | true | true | 同一 session |
| before_motion | true | true | 同一 session |
| before_exit（stop/close 前最后读回） | true | true | 同一 session |

session identifier：`anon:000001B06E72CEC0:World0-session.usda`；路径 `/physicsScene.physxScene:enableExternalForcesEveryIteration`；source=explicit_cli；edit_target_restored=true；四次 matches_expected=true。这证明**composed USD/schema 配置及其来源**，没有 native scene flag getter，也没有直接测量内部逐迭代外力执行；实际轨迹变化是另一个结果证据。

## 4. 旧 false 对照的可比较性

旧对照仅使用 `logs/scan_assignment/20260930_cr12_state_consistency/attempt_01/` 保留的 result、joint/body CSV、同次日志及相关源码增量。其 false 是 resolved=false、authored=false；600 步、5.000000260770321 秒，t=5 因轴 5/6 原生速度超过 0.01 rad/s 停止。其 FAIL 保持原记录。

对实际 on 结果做递归字段对照，资产路径、derived URDF SHA256、运行源码路径、解释器、HEAD、PD、v1 参数、USD/native mass/COM/inertia/限制、碰撞参数及过滤、root anchor、初始化、零 q/dq、初始实际 body poses、dt/render/gravity、GPU/solver、pre-App CUDA 记录均相同；solver_observation 的唯一差异是该 flag 的 `value false→true` 和 `authored false→true`。

共同 CSV 为基线+1…600 共 601 行：六轴 position/velocity 目标及实际 physics 时间逐值相同；独立复核亦确认 elapsed/reference 时间相同。两次 q/dq 和 link 轨迹允许因 flag 改变而不同，不以“轨迹必须相同”否定试验。

共同环境：`C:\isaacenvs\isaac45_harl\python.exe`，UTF8=1；torch 2.5.1+cu121/cuda:0，原 pre-App CUDA 准备及同步保留；`apps/isaaclab.python.kit`、GUI/D3D12；本次 Kit 4.5.0/106.5.0 日志与 RTX 4060 Ti、驱动 610.60 一致。HEAD 为 `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`，它只作定位。

限度：旧记录没有所有 USD 引用层的历史字节 hash，不能宣称历史全资产逐字节冻结；本轮未改资产，且保留的相关参数/执行方式相符，足以支持本次有条件单因素比较。精确 PhysX SDK 版本仍 UNKNOWN。不重新做全仓库库存/哈希，不为补齐表格重跑 false。

## 5. CPU 检查、两次 App 与实际命令

### 5.1 CPU 检查及局部修复

使用已核对的目标解释器，所有改动 Python 文件 py_compile 通过。初版新增 15/15 测试、原状态诊断 15/15、监督器 8/8 CPU fixtures 通过；初版 fake 的无参 GetPropertyStack 过宽，未捕获本机绑定签名要求。真实 attempt_01 暴露后，仅将 helper 的 apply/read 增加必填 default_time，由真实入口统一传 `Usd.TimeCode.Default()`。本地 `P/extscache/omni.usd.libs-1.0.1+d02c707b.wx64.r.cp310/pxr/Usd/__init__.pyi:8591` 和真实异常均确认要求时间参数。

修复后 fake `GetPropertyStack(self,time)` 拒绝缺参、拒绝错误 sentinel，覆盖 before/after/各阶段透传；最终 **16/16 CPU 测试通过**（0.124s）。原状态测试 15/15（0.218s）、监督器 fixtures 8/8（0.079s）通过。合成 720 步只验证记录逻辑，不算仿真通过。

相关命令（均已执行，路径均相对仓库根；监督器 fixtures 是纯标准库临时测试，不新增测试框架）：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -m py_compile scripts/environments/run_cr12_joint_drive.py scripts/environments/_cr12_external_forces.py scripts/environments/_cr12_state_consistency.py source/isaaclab_tasks/test/test_cr12_external_forces.py logs/scan_assignment/20260930_cr12_external_forces/repro/supervise_cr12_external.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B 'source/isaaclab_tasks/test/test_cr12_external_forces.py'
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -c "import sys,unittest;sys.path.insert(0,'scripts/environments');suite=unittest.defaultTestLoader.discover('source/isaaclab_tasks/test',pattern='test_cr12_state_consistency.py');result=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not result.wasSuccessful())"
```

说明：py_compile 实际按各责任文件分批执行，上面合并列出相同文件集合，未额外运行整套历史验证。原测试通过进程内 sys.path 使用新增 helper，没有改旧测试文件、安装包或持久环境。

运行全部结束后，另删除配置异常 handler 中一次冗余 `recorder.save()`，防止保存 I/O 失败遮盖原 SceneExternalForcesError；交给原外层安全 fail 保存。该行位于成功运行未经过的异常分支，记录在 `post_run_recording.patch` 并通过 py_compile；**此最终异常分支收口没有再次运行 App**，不能声称真实注入过磁盘故障。没有运行中热改源码。

### 5.2 运行预算与结果

| 记录（本地 +08:00） | 用途/结果 | App 构造 | 所属树墙钟 | 受控步 | 退出 |
|---|---|---|---|---|---|
| attempt_01，11:29:41.873–11:30:05.608 | main/on；配置来源读回 API 参数错误，写属性/reset 前 FAIL | 15.188s | 23.734s | 0 | Python/Conda 0；监督结果/外层 1 |
| attempt_02，11:33:01.525–11:33:41.370 | repair_retry/on；配置、状态对照、原驱动全部 PASS | 14.906s | 39.844s | 720 | Python/Conda/监督外层均 0 |

第一轮控制未开始，joint CSV 仅表头；`authored_by_helper=false`，不能作 true 物理效果记录。原异常单独保留，不因退出码 0 改写成功。第二轮无内部/secondary failure。两次 Windows Job 全部所属进程自然退出，输出排空，无超时/强杀或记录到的 native GPU/CUDA 故障；均低于 180s/360s。PID：第一次 supervisor/Conda/Python=5324/18180/2824；第二次=5644/11740/18084。没有结束无关进程。

本轮最终 App=2/3，实际受控试验 1 次；局部修复重试额度已使用；匹配 false 额度未使用，因旧对照可比较且结果已有充分记录而停止，不用剩余额度调参。

### 5.3 实际完整命令及转发

工作目录固定 `E:\Project\IsaacLab_HARL`。以下为**已经执行的记录**；输出目录已存在，不能原样再次运行以覆盖证据。

外层主运行：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20260930_cr12_external_forces/repro/supervise_cr12_external.py --attempt-dir logs/scan_assignment/20260930_cr12_external_forces/attempt_01 --usd-path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd --pd-profile baseline --record-joint-trace --diagnose-state-consistency --run-kind main --external-forces-every-iteration on
```

外层唯一重试：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20260930_cr12_external_forces/repro/supervise_cr12_external.py --attempt-dir logs/scan_assignment/20260930_cr12_external_forces/attempt_02 --usd-path source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd --pd-profile baseline --record-joint-trace --diagnose-state-consistency --run-kind repair_retry --external-forces-every-iteration on --decision-note 'attempt_01 stopped before author/reset at zero controlled steps: local USD GetPropertyStack requires an explicit Usd.TimeCode. Pass Usd.TimeCode.Default throughout provenance reads; 16 CPU tests passed; all owned processes exited; physical settings and acceptance unchanged.'
```

监督器以 argv list 创建真实 Conda 子进程，attempt_02 的完整转发命令为：

```text
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/run_cr12_joint_drive.py --usd-path E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd --physics_steps 720 --output-dir E:\Project\IsaacLab_HARL\logs\scan_assignment\20260930_cr12_external_forces\attempt_02 --device cuda:0 --pd-profile baseline --record-joint-trace --diagnose-state-consistency --external-forces-every-iteration on --info
```

attempt_01 转发相同选项，仅 output-dir 为 attempt_01；两次实际 original_argv 都包含 explicit on、baseline、trace、state probe、720、cuda:0。子进程继承环境，仅保留原监督的 HEADLESS/ENABLE_CAMERAS/LIVESTREAM/XR=0；目标进程 UTF8=1。原 Windows helper 把空 kit_args 变为 `--/app/vulkan=false`。同次 Kit 日志分别 `kit_20260930_112945.log:3522`、`kit_20260930_113304.log:3556` 显示 Graphics API: D3D12，后者 :2799/:3461 为 RTX 4060 Ti，:3 为实际 App/Kit 版本。Kit 文本时间比本地记录早 8 小时，与 UTC 一致；跨日志比较用带 +08:00 的 supervisor 时间和同次路径配对。

## 6. 原运动、保持与监测验收

acceptance 输入仍为 normal robot.update 后的原关节 q/dq 快照，已逐值核对 native getters；没有用差分速度、积分速度、投影、均值或最后合格样本替代。

| 轴 | 全程max位置误差(°) | 全程max \|dq\|(rad/s) | 5–6s max误差(°) | 5–6s max \|dq\|(rad/s) |
|---|---|---|---|---|
| 1 | 0.030082 | 6.303408e-3 | 0.006145 | 9.544046e-9 |
| 2 | 0.329112 | 8.763550e-2 | 0.297714 | 8.708406e-8 |
| 3 | 0.338154 | 1.329950e-2 | 0.303813 | 2.315890e-8 |
| 4 | 0.155165 | 9.226156e-3 | 0.128993 | 9.928975e-8 |
| 5 | 0.179956 | 3.653382e-2 | 0.169813 | 7.574864e-8 |
| 6 | 0.100681 | 2.351943e-2 | 0.083628 | 5.595209e-8 |

全程位置误差均 ≤0.5°，|dq|≤0.25 rad/s；末秒全部逐样本 |dq|≤0.01 rad/s、误差≤0.5°。新运行全程最大位置误差 0.338154155°，最大速度 0.0876355022 rad/s；末秒最大速度 9.928974976e-8 rad/s。joint_2 在 t=2 为 2.624001371°，原进展守卫通过；最终 5.297713713°≥4.5°。原硬限位及有限状态检查通过。

| 检查/覆盖 | false 历史记录 | true 本次记录 |
|---|---|---|
| 控制步/物理时长 | 600 / 5.000000260770321s | 720 / 6.000000312924385s |
| 初始化 | reset1次、2步、0.01666666753590107s | 相同；不计入720 |
| joint CSV / body CSV | 601 / 600 行 | 721（基线+720）/720 行 |
| clock/contact | 各600 PASS | 各720 PASS |
| joint | 599 PASS，step600 FAIL | 720 PASS |
| geometry/frame | 各599 PASS，step600未检查 | 各720 PASS |
| 末秒600…720 | 1/121，不能认作完整末秒 | 121/121，原标准逐样本PASS |
| 同刻状态有效性 | 600有效，无clock推进 | 720有效，0 invalid；15条快照复查均未改写，无clock推进 |
| 渲染 | 299次（失败在step600的render前） | 360次，无额外物理步 |

新运行七个接触监测器各更新720次，原禁止 pairs 最大法向力0 N（原阈值0.1 N）；root 位移/转角最大0，elevate/base_link/tool/scanner 原固定 frame 误差均0；原 arm collision bound 最低 z=1.2399987636920686 m。原地面支撑/过滤规则不变。结果仅证明本次轨迹下原有限监测全部通过，不扩展成任意构件避障、视觉拓扑正确或全部碰撞情形保证。

## 7. 六轴离线状态与积分比较

按原端点选择：1–3s 使用 step120…360（241）；3–4s 使用360…480（121）；4–5s 使用480…600（121）；新5–6s使用600…720（121）。t 标签是原名义受控时刻，实际物理起点包含初始化基线0.01666666753590107s。所有积分使用 CSV 的 **actual_time_s** 梯形积分，非简单采样均值乘名义 dt：

`R=(q_end−q_start)−Σ[(dq_i+dq_(i+1))/2 · (t_(i+1)−t_i)]`。

link角用既有连续关节角表达；投影角速度用原父子 world 角速度沿关节轴的投影，未新增过滤或算法。R是诊断量，未添加“必须为0”的验收阈值。dq均值=积分/实际区间时长，RMS=√(梯形积分(dq²)/时长)，最大值为取得样本的最大绝对值。

### 1–3 秒：241 个端点包含样本

实际积分时长 2.0000001043081284 秒，两次时钟一致。角度相关列单位均为 rad。

| flag | 轴 | native Δq | ∫native dq dt | R = Δq − ∫dq | link角端差 | ∫投影ω dt |
|---|---|---|---|---|---|---|
| false | 1 | 3.241093e-4 | 1.122555e-2 | -1.090144e-2 | 3.239621e-4 | 1.122554e-2 |
| false | 2 | 9.205038e-2 | 9.256348e-2 | -5.131019e-4 | 9.205032e-2 | 9.256346e-2 |
| false | 3 | 3.495600e-3 | -2.357467e-3 | 5.853067e-3 | 3.495724e-3 | -2.357467e-3 |
| false | 4 | 2.747924e-3 | 1.547812e-2 | -1.273019e-2 | 2.747856e-3 | 1.547812e-2 |
| false | 5 | 8.175827e-4 | -4.725643e-2 | 4.807402e-2 | 8.175721e-4 | -4.725642e-2 |
| false | 6 | -1.514458e-3 | -5.035433e-2 | 4.883987e-2 | -1.514464e-3 | -5.035432e-2 |
| true | 1 | 3.209317e-4 | 2.949384e-4 | 2.599322e-5 | 3.209659e-4 | 2.949384e-4 |
| true | 2 | 9.205487e-2 | 9.204924e-2 | 5.635362e-6 | 9.205481e-2 | 9.204922e-2 |
| true | 3 | 3.493195e-3 | 3.499632e-3 | -6.437484e-6 | 3.493109e-3 | 3.499631e-3 |
| true | 4 | 2.748848e-3 | 2.751317e-3 | -2.468705e-6 | 2.748605e-3 | 2.751317e-3 |
| true | 5 | 8.153389e-4 | 8.471406e-4 | -3.180167e-5 | 8.153203e-4 | 8.471403e-4 |
| true | 6 | -1.508620e-3 | -1.487945e-3 | -2.067512e-5 | -1.508479e-3 | -1.487945e-3 |

native dq 的时间加权 RMS、均值和逐样本最大绝对值（rad/s）；均值保留符号，最后一列为正/负/零样本数。

| flag | 轴 | dq RMS | dq均值 | max \|dq\| | 正/负/零 |
|---|---|---|---|---|---|
| false | 1 | 5.810616e-3 | 5.612772e-3 | 7.328204e-3 | 241/0/0 |
| false | 2 | 5.575122e-2 | 4.628174e-2 | 8.791593e-2 | 231/10/0 |
| false | 3 | 2.741886e-3 | -1.178734e-3 | 5.420950e-3 | 102/139/0 |
| false | 4 | 7.928491e-3 | 7.739058e-3 | 9.828521e-3 | 241/0/0 |
| false | 5 | 2.365059e-2 | -2.362822e-2 | 2.567042e-2 | 0/241/0 |
| false | 6 | 2.524459e-2 | -2.517716e-2 | 2.722340e-2 | 0/241/0 |
| true | 1 | 9.452189e-4 | 1.474692e-4 | 1.727593e-3 | 145/96/0 |
| true | 2 | 5.553261e-2 | 4.602462e-2 | 8.763550e-2 | 233/8/0 |
| true | 3 | 2.985125e-3 | 1.749816e-3 | 4.804518e-3 | 165/76/0 |
| true | 4 | 2.353285e-3 | 1.375658e-3 | 3.764917e-3 | 165/76/0 |
| true | 5 | 8.228822e-4 | 4.235703e-4 | 1.290385e-3 | 162/79/0 |
| true | 6 | 1.379393e-3 | -7.439726e-4 | 2.176475e-3 | 78/163/0 |

### 3–4 秒：121 个端点包含样本

实际积分时长 1.0000000521540642 秒，两次时钟一致。角度相关列单位均为 rad。

| flag | 轴 | native Δq | ∫native dq dt | R = Δq − ∫dq | link角端差 | ∫投影ω dt |
|---|---|---|---|---|---|---|
| false | 1 | -2.287899e-4 | 5.762456e-3 | -5.991246e-3 | -2.288333e-4 | 5.762455e-3 |
| false | 2 | -4.121438e-4 | -1.727116e-3 | 1.314972e-3 | -4.123418e-4 | -1.727115e-3 |
| false | 3 | -3.413619e-4 | -2.830051e-3 | 2.488689e-3 | -3.415526e-4 | -2.830050e-3 |
| false | 4 | -2.262078e-4 | 5.895436e-3 | -6.121644e-3 | -2.262084e-4 | 5.895435e-3 |
| false | 5 | -6.845943e-5 | -2.325242e-2 | 2.318396e-2 | -6.853809e-5 | -2.325242e-2 |
| false | 6 | 1.246687e-4 | -2.584896e-2 | 2.597363e-2 | 1.247028e-4 | -2.584895e-2 |
| true | 1 | -2.290827e-4 | -2.298087e-4 | 7.260220e-7 | -2.292078e-4 | -2.298087e-4 |
| true | 2 | -4.107952e-4 | -4.119705e-4 | 1.175256e-6 | -4.108376e-4 | -4.119703e-4 |
| true | 3 | -3.414666e-4 | -3.426189e-4 | 1.152248e-6 | -3.411822e-4 | -3.426188e-4 |
| true | 4 | -2.265153e-4 | -2.274387e-4 | 9.233878e-7 | -2.265831e-4 | -2.274387e-4 |
| true | 5 | -6.861240e-5 | -6.911144e-5 | 4.990471e-7 | -6.852748e-5 | -6.911146e-5 |
| true | 6 | 1.248975e-4 | 1.255793e-4 | -6.818235e-7 | 1.250253e-4 | 1.255793e-4 |

native dq 的时间加权 RMS、均值和逐样本最大绝对值（rad/s）；均值保留符号，最后一列为正/负/零样本数。

| flag | 轴 | dq RMS | dq均值 | max \|dq\| | 正/负/零 |
|---|---|---|---|---|---|
| false | 1 | 5.791864e-3 | 5.762456e-3 | 6.286386e-3 | 121/0/0 |
| false | 2 | 1.887453e-3 | -1.727116e-3 | 3.558160e-3 | 0/121/0 |
| false | 3 | 2.953121e-3 | -2.830051e-3 | 5.167365e-3 | 0/121/0 |
| false | 4 | 5.932581e-3 | 5.895436e-3 | 6.447106e-3 | 121/0/0 |
| false | 5 | 2.325369e-2 | -2.325242e-2 | 2.404995e-2 | 0/121/0 |
| false | 6 | 2.585205e-2 | -2.584896e-2 | 2.612724e-2 | 0/121/0 |
| true | 1 | 6.278245e-4 | -2.298087e-4 | 1.644465e-3 | 45/76/0 |
| true | 2 | 8.602814e-4 | -4.119704e-4 | 2.226689e-3 | 42/79/0 |
| true | 3 | 9.032995e-4 | -3.426189e-4 | 2.647730e-3 | 47/74/0 |
| true | 4 | 6.924401e-4 | -2.274387e-4 | 2.108496e-3 | 47/74/0 |
| true | 5 | 2.555797e-4 | -6.911144e-5 | 8.750740e-4 | 52/69/0 |
| true | 6 | 4.185013e-4 | 1.255793e-4 | 1.447058e-3 | 73/48/0 |

### 4–5 秒：121 个端点包含样本

实际积分时长 1.0000000521540642 秒，两次时钟一致。角度相关列单位均为 rad。

| flag | 轴 | native Δq | ∫native dq dt | R = Δq − ∫dq | link角端差 | ∫投影ω dt |
|---|---|---|---|---|---|---|
| false | 1 | 3.630121e-7 | 5.992161e-3 | -5.991798e-3 | 3.745736e-7 | 5.992159e-3 |
| false | 2 | 1.117587e-7 | -1.313070e-3 | 1.313182e-3 | 3.862222e-7 | -1.313070e-3 |
| false | 3 | 3.101304e-7 | -2.486485e-3 | 2.486796e-3 | 3.720353e-7 | -2.486484e-3 |
| false | 4 | 3.816094e-7 | 6.124077e-3 | -6.123696e-3 | 3.745523e-7 | 6.124075e-3 |
| false | 5 | 1.306180e-7 | -2.318478e-2 | 2.318491e-2 | 3.810611e-7 | -2.318478e-2 |
| false | 6 | -1.522712e-7 | -2.597377e-2 | 2.597362e-2 | -4.176790e-7 | -2.597377e-2 |
| true | 1 | 3.240420e-7 | 3.222466e-7 | 1.795400e-9 | 3.744499e-7 | 3.222465e-7 |
| true | 2 | 0.000000e+0 | -2.438094e-7 | 2.438094e-7 | -7.943077e-10 | -2.438094e-7 |
| true | 3 | 2.705492e-7 | 2.729410e-7 | -2.391743e-9 | 0.000000e+0 | 2.729409e-7 |
| true | 4 | 3.599562e-7 | 3.092655e-7 | 5.069064e-8 | 3.747510e-7 | 3.092654e-7 |
| true | 5 | 1.280569e-7 | 8.512173e-8 | 4.293512e-8 | -3.108624e-15 | 8.512171e-8 |
| true | 6 | -1.466833e-7 | -1.256469e-7 | -2.103638e-8 | -3.561140e-7 | -1.256469e-7 |

native dq 的时间加权 RMS、均值和逐样本最大绝对值（rad/s）；均值保留符号，最后一列为正/负/零样本数。

| flag | 轴 | dq RMS | dq均值 | max \|dq\| | 正/负/零 |
|---|---|---|---|---|---|
| false | 1 | 5.992161e-3 | 5.992161e-3 | 5.993649e-3 | 121/0/0 |
| false | 2 | 1.313070e-3 | -1.313070e-3 | 1.315365e-3 | 0/121/0 |
| false | 3 | 2.486485e-3 | -2.486485e-3 | 2.487408e-3 | 0/121/0 |
| false | 4 | 6.124077e-3 | 6.124077e-3 | 6.125753e-3 | 121/0/0 |
| false | 5 | 2.318478e-2 | -2.318478e-2 | 2.318505e-2 | 0/121/0 |
| false | 6 | 2.597377e-2 | -2.597377e-2 | 2.597456e-2 | 0/121/0 |
| true | 1 | 7.073005e-7 | 3.222466e-7 | 1.866885e-6 | 44/77/0 |
| true | 2 | 6.237098e-7 | -2.438094e-7 | 3.202118e-6 | 21/100/0 |
| true | 3 | 6.110096e-7 | 2.729409e-7 | 1.603336e-6 | 57/64/0 |
| true | 4 | 7.508668e-7 | 3.092655e-7 | 1.984685e-6 | 41/80/0 |
| true | 5 | 2.936673e-7 | 8.512173e-8 | 8.874260e-7 | 42/79/0 |
| true | 6 | 3.210902e-7 | -1.256469e-7 | 9.661836e-7 | 74/47/0 |


### 7.4 改善幅度与同一 t=5 对照

4–5s 的六轴 |R| 依次从 `(5.991798e-3,1.313182e-3,2.486796e-3,6.123696e-3,2.318491e-2,2.597362e-2)` 降至 `(1.795400e-9,2.438094e-7,2.391743e-9,5.069064e-8,4.293512e-8,2.103638e-8)` rad。百分比定义 `100·(1−|R_true|/|R_false|)`；轴5/6为99.9998148%/99.9999190%。未用接近0的 Δq 作分母。

同一 step600 / 名义 t=5 的原生速度（rad/s）：

| 轴 | false t=5 dq | true t=5 dq | 绝对速度下降 |
|---|---|---|---|
| 5 | -2.318492e-2 | -6.269349e-8 | 99.999730% |
| 6 | -2.597362e-2 | 4.514852e-8 | 99.999826% |

旧4–5s轴5/6均连续121个负速度样本；true同段变为小幅正负交替，时间加权均值约8.51e-8/−1.26e-7rad/s。运动1–3s仍存在非零积分残差（例如轴5约−3.18017e-5rad、轴6约−2.06751e-5rad），不可写成“所有状态积分完全一致”。两次都使用同一离散采样/积分方法；这些残余不改变原运动验收结果，也不在本轮继续逆向解释。

### 7.5 true 独有的 5–6 秒

false 没有这段完整观测；不补零、不外推、不与旧t=5对新t=6混比。新段实际时长1.0000000521540642s，完整121样本：

| 轴 | native Δq(rad) | ∫dq(rad) | R(rad) | link角端差(rad) | ∫投影ω(rad) | dq RMS(rad/s) | 均值(rad/s) | max \|dq\|(rad/s) |
|---|---|---|---|---|---|---|---|---|
| 1 | -2.328306e-10 | -3.457824e-9 | 3.224993e-9 | 0.000000e+0 | -3.457823e-9 | 4.021023e-9 | -3.457824e-9 | 9.544046e-9 |
| 2 | 0.000000e+0 | -8.318401e-8 | 8.318401e-8 | 0.000000e+0 | -8.318400e-8 | 8.319649e-8 | -8.318401e-8 | 8.708406e-8 |
| 3 | 0.000000e+0 | -1.661637e-8 | 1.661637e-8 | 0.000000e+0 | -1.661636e-8 | 1.707110e-8 | -1.661637e-8 | 2.315890e-8 |
| 4 | 0.000000e+0 | -8.170855e-8 | 8.170855e-8 | 0.000000e+0 | -8.170853e-8 | 8.204091e-8 | -8.170854e-8 | 9.928975e-8 |
| 5 | 0.000000e+0 | -6.769912e-8 | 6.769912e-8 | 0.000000e+0 | -6.769910e-8 | 6.786675e-8 | -6.769912e-8 | 7.574864e-8 |
| 6 | 1.164153e-10 | 3.875596e-8 | -3.863955e-8 | 0.000000e+0 | 3.875596e-8 | 3.929607e-8 | 3.875596e-8 | 5.595209e-8 |

此段 dq 符号计数（正/负/零）按轴1…6分别为 `2/119/0、0/121/0、0/121/0、0/121/0、0/121/0、121/0/0`；值均极小但不强行记0。保持原始浮点状态即可，不需要过滤让结果通过。

### 7.6 缓存/native/link 表达一致性

下表为 false 1…600 与 true 1…720 的最大绝对表达差异；true共同1…600得到同样的各轴最大值。两种配置六轴缓存/native q、dq全为0差异。

| 轴 | 缓存−native q/dq最大差 | false link角−q (rad) | true link角−q (rad) | false 投影ω−dq (rad/s) | true 投影ω−dq (rad/s) |
|---|---|---|---|---|---|
| 1 | 0 / 0 | 3.736313e-7 | 3.688681e-7 | 3.725290e-9 | 1.396984e-9 |
| 2 | 0 / 0 | 4.936847e-7 | 5.219344e-7 | 4.470145e-8 | 3.722289e-8 |
| 3 | 0 / 0 | 3.366732e-7 | 3.307769e-7 | 2.471705e-8 | 2.775741e-8 |
| 4 | 0 / 0 | 3.699818e-7 | 3.605973e-7 | 8.313187e-9 | 4.185587e-9 |
| 5 | 0 / 0 | 3.013250e-7 | 2.966336e-7 | 3.435635e-8 | 2.989447e-8 |
| 6 | 0 / 0 | 5.301669e-7 | 4.495486e-7 | 2.517636e-8 | 6.133981e-9 |

true link角/native q总体最大5.219344e-7rad、投影ω/native dq最大3.722289e-8rad/s；不把微小残余归为新读取故障。link与广义状态来自同一个 PhysX articulation，并非独立物理真值。新结果支持前轮未发现缓存读取错误的判断，但不提供 SDK 内部 flag getter 或求解阶段逐迭代跟踪。

## 8. 解释、未决事项与停止

**证据直接确认**：显式 session 配置早于本轮首次原生初始化链；四阶段schema读回一致；共同输入/执行方式匹配；原有判据完整通过；积分差异在共同窗口显著下降；退出完成。

**支持的推断**：外力逐迭代选项与当前TGS场景下此前“位置趋稳、dq持续非零”的差异有关，当前显式 true 是有效的局部配置。仍不能证明内部哪个阶段唯一导致差异、SDK唯一缺陷或其他构型都适用；无需为硬作同因结论再制造 false 失败。

**建议**：审阅本报告后，当前独立CR12后续工作显式沿用 on；默认继续 inherit。旧 false、PD候选及本轮零步失败均保持历史原结果。本报告只标记本次原驱动验收通过，阶段审阅/关闭由GPT/用户决定。

**用户已确认而尚未解决**：源OBJ正常，仿真显示几何差异待查；人工微小运动、穿插、保持观感尚未完整确认。本轮不查原因，不声称“源mesh简化/已填充/凸包替换造成外观”。后续是否先调查显示几何及其对碰撞/扫描的影响，由用户另行决定；不要求为了本次对照重新观看或扩大动作。

**后续未实施**：视觉资产修复、其他物理/PD调参、IK/末端位姿执行、相机、双视点、MRTA适配、实体设备。没有Git写操作、清理、依赖/驱动/installed-package/共享配置修改。保留既有dirty worktree及原索引状态，包括此前已暂存的历史删除，不进行恢复或提交。

本轮实施、有限运行与分析已完成；停止，等待 GPT/用户审阅。

## 9. 文档变更及辅助证据对应

文档仅新增本主报告，小范围更新 `AgentRead/TASK_PROGRESS.md` 与 `REPORT_INDEX.md`，记录本轮新授权、显式on结果、实际人工反馈和等待审阅；旧报告及其当时“未授权/未实施/FAIL”口径不改。报告目录未新增Python/JSON/log/ZIP。

源代码新增/修改见第3.1节；本轮一次性监督脚本仅在logs/repro。最终异常分支一行收口、初版增量及重试兼容修复分别保留小补丁。代码和旧工作区大多尚未跟踪；运行日志受本地日志规则管理，**不承诺全新checkout含有本机raw证据**。未复制资产、未建立全仓hash/ledger/ZIP。

| 主文结论 | 辅助材料（相对仓库根） | 用途/保留理由 |
|---|---|---|
| 旧false可比输入与600步失败 | [旧result](../../../../../../../../logs/scan_assignment/20260930_cr12_state_consistency/attempt_01/result.json)、[joint CSV](../../../../../../../../logs/scan_assignment/20260930_cr12_state_consistency/attempt_01/joint_trace.csv)、[body CSV](../../../../../../../../logs/scan_assignment/20260930_cr12_state_consistency/attempt_01/body_state_trace.csv) | 已有原始对照，保持原位/原结果 |
| 首次配置API失败 | [attempt_01 result](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_01/result.json)、[监督结果](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_01/supervisor_result.json)、[命令](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_01/command.json)、[console](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_01/console.log)、[Kit日志](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_01/kit_20260930_112945.log) | 0步、未author、首因及退出；同目录事件/表头CSV保留，不删除失败 |
| 完整on结果与窗口 | [attempt_02 result](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/result.json)、[joint CSV](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/joint_trace.csv)、[body CSV](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/body_state_trace.csv)、[监督结果](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/supervisor_result.json) | 原样本、覆盖/FAIL粘性、原判据及退出 |
| 命令、初始化、D3D12时序 | [命令](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/command.json)、[事件](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/events.jsonl)、[console](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/console.log)、[Kit日志](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/kit_20260930_113304.log) | 同次实际进程/Kit来源，非扫描latest日志 |
| 离线积分/字段比较 | [comparison.json](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/comparison.json) | 标准库CSV读取、实际时间梯形积分；正文已列关键全轴数字，不以JSON替代报告 |
| 本轮源码增量 | [初版增量](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_01/implementation.patch)、[TimeCode修复](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/repair.patch)、[运行后异常保存调整](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/attempt_02/post_run_recording.patch) | 相对本轮开始的未跟踪源码增量，不依赖仅HEAD判断 |
| 预算/转发复现 | [supervise_cr12_external.py](../../../../../../../../logs/scan_assignment/20260930_cr12_external_forces/repro/supervise_cr12_external.py) | 本轮一次性监督副本；旧副本未改 |
| CPU行为保障 | [test_cr12_external_forces.py](../../../../../../../../source/isaaclab_tasks/test/test_cr12_external_forces.py) | fake场景与真实parser测试，无Isaac导入；记录覆盖不等于物理PASS |
| 后续阅读入口 | [TASK_PROGRESS](../../TASK_PROGRESS.md)、[REPORT_INDEX](../../REPORT_INDEX.md) | 最新状态与主题导航 |

必要前置：[前轮状态一致性与求解阶段诊断](CR12_STATE_CONSISTENCY_AND_SOLVER_DIAGNOSIS_REPORT.md)、[原保持诊断与PD复测](../20260929/CR12_HOLD_DIAGNOSIS_AND_PD_RETEST_REPORT.md)。本轮没有重跑Windows、资产生成、Phase B或历史训练/检查点验收。
