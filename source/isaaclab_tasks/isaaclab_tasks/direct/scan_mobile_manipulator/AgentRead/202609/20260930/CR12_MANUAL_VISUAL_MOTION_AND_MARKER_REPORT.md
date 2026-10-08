# CR12 manual-only 可视化动作与 pose marker 改进报告

日期：2026-09-30（Asia/Shanghai，UTC+08:00）。仓库：`E:\Project\IsaacLab_HARL`。HEAD：`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。

**实现与 CPU 回归已完成；本次唯一 manual runtime smoke 为 FAIL。** App 构造时日志出现 D3D12 `createSwapchain failed. Width: 120, height: 0`，随后原生访问异常 `0xC0000005`；没有进入机器人场景、manual target、marker 或运动执行。所属进程全部退出，无超时、无强制终止。没有启动 App 2，没有修改冻结目标或控制参数。现交付报告等待 GPT/用户审阅。

**manual-visible profile仅用于人工观察运动连续性和marker显示，不扩展正式单目标验收范围。**

## A. 正式能力冻结与本轮边界

用户本轮已确认：[正式单目标实施报告](CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md) 获 **GPT REVIEW PASS**。正式历史为 600 受控步、约 5 秒、`POSE_REACHED`，最终 scanner 误差约 0.0695588 mm / 0.00468716°，121 个稳定样本覆盖 1 秒，native Jacobian 唯一匹配 COM，全部正式 guard 通过。本轮未重跑正式 App，未回写该报告或正式 attempt 数据。

默认 `--motion-profile formal` 保留原目标：实测初始 scanner 加世界平移 (10.698145715, 0, −0.155046722) mm、绕世界 Y +1°；reference 4 秒，最多 8 秒 / 960 步。固定底盘、lift0、v1、baseline PD、dt=1/120、TGS8/2、显式 external-forces-every-iteration=on，以及 2 mm / .25° / dq≤.01 rad/s / 连续 1 秒判据均不变。`--visual-debug-pose` 只控制显示，不选择 manual 动作。

Phase B 保持 **COMPLETE / GPT REVIEW PASS / CLOSED**。本轮未重验 Windows、基本驱动、PD/solver、外力时序或 Jacobian 参考点，也未生成/修改资产。新的原生启动失败独立记录，不推翻既有正式 pose PASS。

## B. manual-only 新增内容

### B1. 显式 profile 与目标构造

入口新增 `--motion-profile manual_visible_local_v1`。控制 profile 不暴露任意时间、witness、beta 或 guard 调参选项；省略 `--physics_steps` 时按 profile 取固定上限，显式值必须是 formal 的 960 或 manual 的 1200。结果及控制台事件明确写 `MANUAL_VISUAL_ONLY=true`。

| 项目 | manual_visible_local_v1 |
|---|---|
| joint witness（joint_1…6，度） | `(0, +3, −4.5, 0, +4.5, 0)` |
| beta | **1.0**，首次 App 前离线确定并写死；未运行后调整 |
| root | 本次初始化后真实 `agv` pose |
| target | `T_WS = T_WR_actual_initial × FK_root(q_witness)[link_6] × T_ES` |
| scanner 安装 | 原固定 `T_ES`，零平移、Rz(+135°) |
| reference | 实测初始 scanner 到冻结 target；平移 quintic、旋转最短 geodesic；6 秒 |
| 上限与稳定窗 | 10 秒 / 1200 受控步；原 1 秒稳定窗；成功可提前结束 |
| 实际控制 | 同一 scanner pose DiffIK 闭环，witness 不直接作为 joint 命令 |

源码：`scripts/environments/_cr12_pose_control.py:36` 固定 witness/beta，`MotionProfile:41`，`FrozenManualPoseTarget:233`；`run_cr12_pose_target.py:28` 参数解析，`_run_pose:185` 集成。目标由实际 root 生成，不读取旧绝对 world target；目标对象内部冻结，返回值为独立副本。manual 使用此前接受的 COM adapter，记录 `semantic_recheck_performed=false`，仅保持 native shape/name/device/finite 检查；没有再次调用参考点唯一匹配资格检查。

### B2. 首次 App 前离线检查

使用当前派生 URDF 的 CPU FK，以及正式 attempt 已记录的 10 个 collider 局部 AABB，复用当前 `_cr12_runtime_support._check_geometry`、ground 与原非相邻禁止 pair 规则，contact offset 仍为每侧 .002 m。未启动 App、IK/CUDA 或资产生成。

| 检查 | 结果 |
|---|---|
| witness/FK/scanner target 有限，最短角 | PASS；3° |
| 最大 witness 变化 | 4.5°；距离原 5° trust 还有 **0.5°** |
| 距原硬限位的最小余量 | 167.002307° |
| `q(s)=0+s·q_witness` | 101 个等距样本，包含两端 |
| 原规则禁止 AABB 重叠 | 0 |
| arm 碰撞几何最低 z（名义 root z=.053 m） | 1.239999235 m |
| 最小 expanded 非相邻 box separation | .015862956 m |
| scanner 位移 | (32.077097276, 0, −1.395165325) mm |
| 位移模 / 旋转 | **32.107423689 mm / 3°** |

离线 `T_RE_witness` 的位置为 (0.137077097276, −0.15, 2.833604834675) m，旋转为 Ry(3°)。名义 root 为单位旋转、z=.053 m 时，`T_WE_witness` 位置为 (0.137077097276, −0.15, 2.886604834675) m；`T_WS` 旋转为 Ry(3°)·Rz(135°)。这些数值是**离线示例**，不作为旧 world pose 硬编码回运行入口。

本次 App 在初始化前失败，**没有生成本次实际 root 对应的 runtime scanner target**，其实际数值为 NOT_CONSTRUCTED。上述 101 点只证明 witness 线段的离线采样通过，不能证明真实 DiffIK 轨迹、连续碰撞安全或运行可达。

### B3. 控制链与原 guard

运行接线保持：scanner reference → link_6 reference → root frame → native Jacobian → 冻结 COM adapter → absolute-pose DLS λ=.01 → 原 command integrator → 实际 q/dq targets → PhysX → 实测 link_6 与固定 T_ES 合成 actual scanner。

| 保留项目 | 原值/规则 |
|---|---|
| integrator gain / dt | 2/s；1/120 s |
| raw DLS / accumulated q_cmd−actual | 各 .035 rad |
| 每 tick q command / dq command | .00125 rad；.15 rad/s |
| actual dq / local trust | .25 rad/s；初始化附近 5° |
| hard-limit command margin | .02 rad |
| 其他检查 | finite、硬限位、contact、geometry、root/frame、clock、render clock |

每次实际下发前仍检查同一 q proposal 的中点及终点 FK 几何；下发并步进后读取真实状态，检查原 contact/geometry/frame/clock。没有 teleport、每 tick 写 joint state、关节 witness 轨迹播放、独立移动扫描相机或额外 physics/render。这里是代码接线事实；本次受控执行未发生，不能写这些 runtime guard 已 PASS。

manual 数值结果独立为 `MANUAL_VISUAL_MOTION_COMPLETED`、`MANUAL_VISUAL_MOTION_TIMEOUT`、`MANUAL_VISUAL_MOTION_GUARD_FAIL` 或 `MANUAL_VISUAL_RUNTIME_FAIL`。内部仍计算 pose error/stability；不会创建 formal acceptance。显示异常另存 `visual_errors`，不替换已有运动/物理首因。结果路径已有 `result.json` 时拒绝接管，避免覆盖正式数据。

### B4. 旧 marker 核对与显示改进

旧 helper 源码实际构造 **actual 三轴 + target 三轴 + origin 连线**，各轴使用输入旋转矩阵列方向，不是只生成绿色轴。旧人工记录 `20260930_cr12_pose_target/manual_20260930_170257_546/result.json` 的 `visual_errors=[]`，metadata 为 actual .12 m / target .08 m；说明没有记录到创建异常，**不证明每轴清晰可见**。

旧 witness 小、formal actual/target 接近；到位后两组真实 frame 本来就接近重合。旧 wrist 方向对 nominal scanner X/Y/Z 的屏幕正交投影长度比约 .410/.993/.920，红轴存在明显投影缩短。蓝轴为何不明显、是否埋入 robot visual 或被 depth 遮挡，仍需用户观察；没有从截图推断 API 只有一根轴。本轮未读取或修改机器人 visual。

| 标记 | 新尺寸/颜色 |
|---|---|
| actual scanner | RGB；轴长 .20 m、半径 .0035 m；白色原点球半径 .006 m |
| final target | 浅 RGB；轴长 .14 m、半径 .0025 m；黄色原点球半径 .008 m |
| actual→target 连线 | 品红；半径 .0018 m；端点为两个真实 origin |
| reference frame | 不显示 |
| 总实例 | 6 轴 + 1 线 + 2 球 = 9 |

继续使用本地 `VisualizationMarkers`、`CylinderCfg` 和 `SphereCfg`。轴向四元数为 WXYZ，圆柱局部 +Z 对齐真实轴；零长度 gap 使用零 scale。未人为平移 target。构造后设计为一次读取真实 PointInstancer instance/prototype 数、indices、visibility，检查 marker 下没有 RigidBody/Collision/Mass/Articulation/Joint schema；成功时记录 `setup_readback`。**本次没有运行到此处，因此没有这些成功读回。**

依据：`_cr12_pose_visuals.py:46`（数学）、`PoseDebugVisuals:118`（本地 API/读回）；本地 `source/isaaclab/isaaclab/markers/visualization_markers.py:209` 的 `is_visible`、`visualize:217` 与 `sim/spawners/shapes/shapes_cfg.py:49` 的 SphereCfg 已核对。模块顶层仅 NumPy/标准 Python；marker runtime API 只在显式 visual 分支构造时导入。

### B5. 一次性 spectator 视角

| preset | look-at | eye offset |
|---|---|---|
| overall / wrist | 旧计算原样保留 | 旧数值保留 |
| wrist-oblique | initial/target scanner 真实 midpoint | (+.55, −.10, +.42) m |
| arm-oblique | 同一 midpoint + (0,0,−.75) m | (+2.2, −2.6, +1.35) m |

新 wrist 静态投影比约 .754/.890/.799，改善旧方向的 X 轴缩短；这是构图计算，不是无遮挡结论。相机只设置一次，后续只更新 marker，不追踪 wrist；继续使用已有 `/OmniverseKit_Persp`，没有扫描相机、render product、全局 depth override 或 renderer 改动。是否能同时看清 link_5/link_6 和两组三轴仍待人工确认。

## C. CPU 回归与唯一 runtime smoke

### C1. 首次 App 前验证

| 验证 | 结果 |
|---|---|
| 原 `test_cr12_pose_control.py` | 31/31 PASS，原测试文件未修改 |
| 新 `test_cr12_manual_visual.py` | 21/21 PASS |
| 控制 AST | 22 个原定义、13 个原常量赋值不变；FrozenPoseTarget、CommandIntegrator 完全相同 |
| PoseMonitor / formal 主循环 | 仅按固定 profile 替换时长；投影回 formal 后与基线 AST 等价 |
| 监督器纯 CPU 判定 | 67/67；3 个正例、64 个拒绝例，覆盖完成、退出、局部视觉修复许可 |
| py_compile | 入口、control、visuals、新测试、新监督器，全部通过 |

新测试覆盖 profile 默认/显式选择、witness/beta 不可调、root/FK/T_ES、非单位 root、无旧 world pose 依赖、6/10/1200 与原 4/8/960、最短旋转、稳定窗、原 guard、manual 分类、marker 输入不变性、真实轴/连线端点、默认无 reference、midpoint view、不步进/不写机器人、lazy import、显示异常不覆盖首因及旧结果拒绝覆盖。

解释器先核对为 `C:\isaacenvs\isaac45_harl\python.exe`。CPU 测试通过不等于 runtime marker 或人工视觉验收通过。

实际验证命令（cwd 为仓库根；下列是执行记录，不是额外运行）：

```text
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl --no-capture-output python -B source\isaaclab_tasks\test\test_cr12_pose_control.py
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl --no-capture-output python -B source\isaaclab_tasks\test\test_cr12_manual_visual.py
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/run_cr12_pose_target.py scripts/environments/_cr12_pose_control.py scripts/environments/_cr12_pose_visuals.py source/isaaclab_tasks/test/test_cr12_manual_visual.py logs/scan_assignment/20260930_cr12_manual_visual_motion/repro/supervise_cr12_manual_visual.py
```

AST/监督判定检查由临时纯 CPU 代码执行，未创建新测试框架。交付前仅对报告两条人工 PowerShell 命令做 Parser.ParseInput 语法检查，并检查新报告相对链接；均通过，未执行命令。一次 patch 生成工具调用曾因 Windows 命令行长度上限失败，改为 stdin 传入原文后完成；它发生于首次 App 前，与 runtime 图形异常无关。

### C2. 实际运行结果

唯一运行于 **2026-09-30 17:24:13.695–17:24:36.857 +08:00**。完整 argv/cwd/临时环境在 command.json；使用现有 Windows 启动 helper 与 pre-App CUDA 顺序。GUI / cuda:0 / D3D12 请求不变，baseline、v1、explicit on、manual、wrist-oblique、1200 步均显式给出。

| 项目 | 事实 |
|---|---|
| App 次数 / 重试 | **1 / 0**；不启动 App 2 |
| pre-App CUDA | 原 helper 返回 cuda:0、torch 2.5.1+cu121、synchronized=true |
| 实际 Graphics API | 当前 console 与 Kit log 明确 **D3D12 / DX12** |
| 失败阶段 | AppLauncher → SimulationApp 构造，`app_ready` 之前 |
| 原生错误 | `Invalid desc parameters` → `createSwapchain failed. Width:120,height:0` → access violation |
| 目标进程退出码 | 3221225477 = **0xC0000005** |
| Conda 退出码 | 4294967295（−1） |
| 全树耗时 / 超时 / 强制终止 | 23.156 s / false / false |
| 所属进程 | 全部退出；无残留 |
| actual root / runtime target | 未构造 |
| 受控步数 / CSV | **0**；CSV 只有表头 |
| contact / geometry / command / frame guard | NOT_RUN |
| view / marker setup/readback | NOT_REACHED |
| visual_errors | **未知/未进入**，不能当作 [] 或 PASS |
| natural successful exit | **否**；进程异常结束，未进入 app.close |
| 最终口径 | **MANUAL_VISUAL_RUNTIME_FAIL / MANUAL_VISUAL_RUNTIME_SMOKE_FAIL** |

关键证据：

- `console.log:1–6`：真实解释器、显式 manual、UTF8=1、D3D12 参数、pre-App CUDA 与 App 构造事件。
- `console.log:11`：请求 window=1440×900、renderer=1280×720；`:3398` 却记录创建 120×0。差异原因 UNKNOWN，本轮不继续调查 Windows/共享配置/驱动。
- `console.log:2707,3502` 与同 run `kit_20260930_172417.log:2682,3450`：实际后端。
- `kit_20260930_172417.log:3357,3925–3927`：窗口尺寸及 swapchain 失败；`console.log:4047`：原生访问异常。
- 栈位于安装的 viewport window 初始化 → SimulationApp → AppLauncher → 入口 `main:489`；尚未调用 `_run_pose`。不据此声称 marker 代码、机器人资产或 manual 目标引起故障，也不推断与历史 Vulkan 故障同因。

原始 `result.json` 是 fatal crash 前最后一次写盘，仍为 RUNNING / NOT_REACHED / failures=[]；原生异常绕过 Python finally，因此这些字段**不是最终完成记录**。监督器已明确 FAIL，原始文件保持不改，另加 `runtime_failure_summary.json` 说明未到达阶段。

监督器依赖 app_ready 事件获得 Kit 路径；本次未收到，因此其原始记录保留 NOT_COPIED/UNCONFIRMED。随后仅从**本次 console 第14行明确给出的路径**复制同一 Kit log，并在补充摘要记录 D3D12 证据；未做“最新日志”搜索或重写原监督记录。

这不是允许 App 2 的局部 marker API/CLI/view 设置错误，而是原生图形初始化失败。按用户停止条件，不改变 target/beta/controller/PD/solver，不通过更换配置、窗口参数、依赖或驱动继续试跑。人工观感未验收。

## D. 文件变更、证据与后续边界

| 文件/位置 | 本轮作用 |
|---|---|
| [run_cr12_pose_target.py](../../../../../../../../scripts/environments/run_cr12_pose_target.py) | 显式 profile、manual target/COM 继承、时间上限、独立分类及 lazy visual 接入 |
| [_cr12_pose_control.py](../../../../../../../../scripts/environments/_cr12_pose_control.py) | 固定 profile/witness、manual FK target 与最短参考；monitor 仅时间参数化 |
| [_cr12_pose_visuals.py](../../../../../../../../scripts/environments/_cr12_pose_visuals.py) | 两组轴、真实 origin 球/连线、新视角、一次 setup 读回 |
| [test_cr12_manual_visual.py](../../../../../../../../source/isaaclab_tasks/test/test_cr12_manual_visual.py) | 21 个针对性 CPU 测试 |
| [supervise_cr12_manual_visual.py](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/repro/supervise_cr12_manual_visual.py) | 复用旧 Windows Job/实时排空/180s App、360s 全树监督；manual 完成条件与严格局部重试 |
| [manual_changes.patch](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/repro/manual_changes.patch) | 本轮三处实现差异及新增测试；不包含用户既有修改 |
| 本报告、[TASK_PROGRESS](../../TASK_PROGRESS.md)、[REPORT_INDEX](../../REPORT_INDEX.md) | 新报告及小范围状态/导航更新，保留旧报告当时标签 |

| 辅助证据 | 支持的结论 / 限制 |
|---|---|
| [offline_checks.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/repro/offline_checks.json) | pre-App witness、101点、CPU测试、control AST；不能代替执行 |
| [command.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/command.json) | 唯一实际命令、cwd、模式及监督预算 |
| [result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/result.json) | fatal 前快照；不是成功结果 |
| [supervisor_result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/supervisor_result.json) | 异常退出、全树退出、smoke FAIL、无第二次运行 |
| [runtime_failure_summary.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/runtime_failure_summary.json) | 故障阶段、未运行项目、同run Kit复制来源与停止决定 |
| [console.log](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/console.log) / [Kit log](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/kit_20260930_172417.log) | 当前 D3D12 / swapchain / fatal 原始证据 |
| [pose_joint_trace.csv](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/pose_joint_trace.csv) | 只有表头，0 个受控样本 |

只新增本轮必要代码、测试、日志/patch 和 Markdown 文档；Python/JSON/日志没有放进 AgentRead。既有 dirty worktree 保留，没有 Git add/commit/push/reset/restore 等写操作；既有暂存删除未改变。未清理、恢复、压缩旧历史数据，没有 ZIP、ledger、图像序列或视频框架。

**源OBJ由用户确认正常；仿真显示几何存在差异，原因待查。** 已知“封闭/填充观感”不是本轮 manual pose 新产生的结论，本轮未修复或调查 mesh/visual。没有相机、构件、双视点、MRTA、训练或更大动作实现。

下一步先审阅本次实现与启动失败证据。若继续处理窗口/原生启动异常及重试，需另行明确授权；不自动重开 Windows 资格验证。新 marker 的 runtime 读回、manual 数值完成及人工可读性均仍待验证。即使后续 manual 成功，也不扩展正式工作空间或采集能力。

## E. 用户人工查看交接（两条命令）

先看 **A arm-oblique**，再看 **B wrist-oblique**。以下使用同一冻结 manual profile，各自创建新 timestamp 目录，CLI 与当前入口一致；**本轮 Codex 没有执行这两条命令**。当前 smoke 在 App 构造失败，命令不是已通过的运行承诺；应先审阅上述故障，再决定后续运行。不要为了运行这些命令自行放宽 guard 或修改 target。

观察：整臂运动是否明显且连续、joint_2/3/5 等是否平滑、有无姿态跳变/明显自穿插/穿地；actual 是否靠近固定 target、两组 RGB 是否可辨、连线是否缩短、到达后有无持续可见抖动。DiffIK 不要求逐关节复现 witness。实际与 target 最终接近重合时，球与轴可能互相遮挡，这不应靠人为错开位置掩盖。

图例：长粗 RGB + 白球为 actual，短细浅 RGB + 黄球为 final target，品红为真实位置差连线。相机固定；若墙钟演示较快，可用系统录屏回看，不更改 physics dt、不 sleep/暂停凑时间。人工观感结论等待用户反馈。

### A. 整臂 arm-oblique

```powershell
Set-Location 'E:\Project\IsaacLab_HARL'
$env:PYTHONUTF8 = '1'
$env:HEADLESS = '0'
$env:ENABLE_CAMERAS = '0'
$env:LIVESTREAM = '0'
$env:XR = '0'
$cr12ManualOutput = Join-Path 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20260930_cr12_manual_visual_motion' ('manual_arm_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u 'scripts/environments/run_cr12_pose_target.py' --usd-path 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd' --output-dir $cr12ManualOutput --motion-profile manual_visible_local_v1 --visual-debug-pose --view-preset arm-oblique --physics_steps 1200 --pd-profile baseline --external-forces-every-iteration on --device cuda:0 --info
Write-Host "结果目录: $cr12ManualOutput"
```

### B. 末端 wrist-oblique

```powershell
Set-Location 'E:\Project\IsaacLab_HARL'
$env:PYTHONUTF8 = '1'
$env:HEADLESS = '0'
$env:ENABLE_CAMERAS = '0'
$env:LIVESTREAM = '0'
$env:XR = '0'
$cr12ManualOutput = Join-Path 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20260930_cr12_manual_visual_motion' ('manual_wrist_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u 'scripts/environments/run_cr12_pose_target.py' --usd-path 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd' --output-dir $cr12ManualOutput --motion-profile manual_visible_local_v1 --visual-debug-pose --view-preset wrist-oblique --physics_steps 1200 --pd-profile baseline --external-forces-every-iteration on --device cuda:0 --info
Write-Host "结果目录: $cr12ManualOutput"
```

