# Windows 项目启动补丁实施与有界 GUI/CUDA/viewer 验证报告

执行日期：2026-09-29；本机时区：Asia/Shanghai（UTC+08:00）。
仓库：`E:\Project\IsaacLab_HARL`；分支 `main`；HEAD：`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。
本报告依据本轮局部实施及有限运行授权；上一轮静态报告的“尚未运行”保留为当时记录。

本文 `T/` 指 `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`，`V/` 指本报告同级的 `windows_runtime_backend_validation/`。源码行号对应本次最终工作树，未提交。

## 1. 结论与覆盖范围

已完成四个授权启动文件的局部补丁，纯参数测试 **12/12 PASS**，语法及针对性源码/AST检查通过。只启动了 **1 次真实项目 viewer GUI**：首次省略 `--kit_args`，helper 追加 Windows 缺省 D3D12；同次 Kit 日志确认实际 **D3D12**。App 创建后在 **cuda:0** 完成固定矩阵运算、同步及读回，结果每项 16、总和 4096；实际 legacy 环境显式 reset 一次，随后 **120 次 env.step 成功返回**；环境关闭成功，viewer 与 Conda 均自然退出 **0**，全部本次所属进程退出，无超时、无强制终止。

这是“Windows 缺省后端处理 + 本次新增 viewer 共用 pre-App CUDA 准备”的**组合路径**成功。没有运行隔离对照，不能宣称仅 D3D12 一项已被证明是根因修复，也不能宣称新增 CUDA 准备普遍必要。此前没有对应的新项目失败日志，本轮没有复现 Vulkan 崩溃。

| 项目 | 结果与准确边界 |
|---|---|
| 四文件实施 | 已实施，未暂存/提交；仅启动、参数、诊断和收尾范围 |
| helper / 语法 / AST | PASS；helper 测试无 Isaac/torch 导入 |
| viewer GUI + runtime_check | 本次有界组合路径 PASS；实际 D3D12 |
| CUDA 已知数值 | PASS；不以 is_available 代替运算，不回退 CPU |
| 项目 reset/step | 真实 ScanMobileManipulatorEnv；legacy；num_envs=1，**三个 proxy agents**；120 步 |
| 收尾 | 内部完成事实与外层退出共同通过；总计 218.515 秒 |
| 普通 viewer 模式 | 源码确认共用必要启动准备；**未独立运行** |
| train / play_assignment | 仅静态接入检查；**未运行** |
| Linux / headless / 显式 Vulkan | 未运行；非 Windows 仅参数分支模拟测试 |
| CR12、关节驱动、碰撞安全、扫描相机、双视点、checkpoint | 本轮未实施/未验证 |

Phase B 保持 **COMPLETE / GPT REVIEW PASS / CLOSED**。本次不是论文评估，也不产生策略任务失败率、算法分数或研究结论。

## 2. 实施文件与最小补丁

| 文件 / 关键符号 | 本次变化与保留行为 |
|---|---|
| `scripts/environments/_windows_runtime_startup.py:57`，`prepare_windows_runtime_args` | 新增纯标准库 helper；只处理 Windows UTF8、后端参数和来源记录，不导入 torch/Isaac/Kit，不改 sys.path 或配置文件 |
| `scripts/environments/view_scan_assignment.py:26,51,69,123,216` | 接入 helper、新增 `--runtime_check`、新增共用 Windows/CUDA 准备、诊断数值与实际步数记录，完善构造/执行/关闭异常边界；保留真实环境、solver/controller 和原有步进调用 |
| `scripts/reinforcement_learning/harl/train.py:130` | 新增两个标准库 import 和一个绝对文件加载/helper 调用及记录块，共 17 行；原代码字节保留 |
| `scripts/reinforcement_learning/harl/play_assignment.py:198` | 同上，共 17 行；既有 warmup、业务 gate、Hydra、video/camera、runner/checkpoint 逻辑保留 |

可审阅补丁：[windows_runtime_startup.patch](windows_runtime_backend_validation/windows_runtime_startup.patch)。补丁包含上述四个生产文件以及本轮新增的一个纯参数测试、一个外层监督脚本。三个既有生产文件在本轮开始时无原有 diff，因此其限定路径 diff 属于本轮；新 helper 以新增文件纳入。补丁不包含既有 TASK_PROGRESS 改动、旧报告、资产或原有 staged 删除，不含运行日志。

附加文件仅为 `V/test_windows_runtime_startup.py`、`V/supervise_viewer.py`、本报告和必要验证记录；小范围更新 `T/AgentRead/TASK_PROGRESS.md`。没有建立新的生产启动框架。

如未来决定撤销，应审阅本补丁并仅反向移除本轮 hunk；两个新生产/测试辅助路径也需先确认没有后续修改。**本轮未执行撤销操作**，不使用整文件 restore/reset 覆盖用户工作。

### 2.1 参数、UTF8 与平台边界

本地 `source/isaaclab/isaaclab/app/app_launcher.py:759–760` 用 `kit_args.split()` 追加至 `sys.argv`，`:780` 创建 SimulationApp。helper 按同样 token 规则检查，保留整个原始无关参数字符串及引号/空白，只在无显式选择时追加一次 `--/app/vulkan=false`。没有尝试修复 AppLauncher 原有的空格/引号 token 局限。

helper `:79` 非 Windows 直接返回；`:82` 核对实际 `sys.flags.utf8_mode`，不合格时要求在父命令中采用已核对的 Conda 环境或 `python -X utf8`，不在运行中的解释器里伪造 UTF8 状态，不递归重启、不写持久环境变量。`:91–102` 拒绝含糊后端写法、裸后端参数、相反选择及重复 CLI `--kit_args` 隐藏早先参数的情形。显式 `--vulkan`、`--/app/vulkan=true`、false 保留；同值重复不再追加；无关未知 Kit 参数不被一概拒绝。来源记录区分 `windows_default`、`explicit`、`non_windows_unchanged`；请求不代替实际 API。

train 顺序为既有 preflight `:102` → helper `:139` → argv 清理 `:145` → **原** warmup 调用 `:167` → AppLauncher `:192`。play 顺序为 `:179` → `:207` → `:212` → `:231` → `:233`。二者均通过 `importlib.util` 绝对路径加载 helper，先保留原 argv，未在 pre-App 导入任务包。后置 readiness gate 仍在 train `:235`、play `:634`，未解封公共 event 入口。

### 2.2 普通与诊断模式共用路径

viewer `main:216` 的顺序为参数解析 → helper `:233` → `_prepare_cuda_before_app` `:247` → AppLauncher `:250` → 实际环境 `:266`。共用准备和 App 构造均在 `runtime_check` 条件外；普通模式没有缺少该准备。

**viewer 的 pre-App CUDA 准备是本次新增行为**（原 viewer 没有）。函数 `:51` 仅在 Windows 且请求 CUDA 时导入 torch、选择设备、用固定 16×16 ones 矩阵相乘并 synchronize；Linux/CPU 在 `:53` 返回，不无条件创建 context。无 RNG、seed、全局精度、网络、learner 或 optimizer 改动；CUDA 不可用直接失败。train/play 原有 warmup 没有重构。

诊断模式额外提供身份/设备一致性、合法 legacy profile、App 后 CUDA 数值和严格步数检查。它没有换环境、改设备或 experience，也没有特殊初始化捷径。普通关窗不会触发诊断专用的未满步数异常（`:208`）。未使用第二次运行去重复确认普通模式，因此其独立实测状态仍是 NOT_RUN。

### 2.3 真实执行与收尾

`_run_environment:123` 保留 `parse_env_cfg → gym.make → env.reset → solver.solve → viewpoint_assignment_to_actions → env.step`。原校验函数和关键调用 AST 与本轮前一致；`:195` 成功返回后才在 `:196` 计数，不把 physics substeps、打印次数或代理状态更新冒充 env.step。未修改任务 profile、机器人数量、done/reset authority 或统计口径。

`main:267–296` 覆盖 App/环境构造及执行异常，只关闭已获得的有效句柄；主异常保留并重抛，关闭异常单独记录，不覆盖主因。`:284` 在 `app.close:290` 前 flush 完成、步数、环境关闭和失败事实。

本地 SimulationApp 的 `simulation_app.py:79` 默认 `fast_shutdown=True`，`:321` 转发设置，`:616` 调用原生 shutdown；因此不假设 app.close 后必有 Python 打印。本次无 `app_close_returned`，但有完整 pre-close 事实、无失败记录及实际进程退出 0，符合本轮成功判据。

## 3. 纯检查命令与结果

均在仓库根目录、指定 Conda/解释器下执行；没有 import viewer/train/play 顶层，也没有运行这两个入口的 `--help`。

```powershell
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable); print(sys.flags.utf8_mode)"

# $v 仅为下列记录目录的缩写，不是持久环境设置。
$v = 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260929/windows_runtime_backend_validation'
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python "$v/test_windows_runtime_startup.py"
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -m py_compile scripts/environments/_windows_runtime_startup.py scripts/environments/view_scan_assignment.py scripts/reinforcement_learning/harl/train.py scripts/reinforcement_learning/harl/play_assignment.py "$v/test_windows_runtime_startup.py" "$v/supervise_viewer.py"
```

解释器确认 `C:\isaacenvs\isaac45_harl\python.exe`、UTF8 mode=1。helper 12 个测试覆盖缺省/显式、相反冲突、同值重复/幂等、无关内容保留、UTF8拒绝、非Windows不处理、可疑/裸参数、重复 CLI 参数及无运行时导入/全局状态副作用，全部通过，退出 0。语法检查六个文件通过，退出 0。

另外执行限定文件的标准库源码/AST检查：比对既有函数/调用、train/play 插入前字节、共用启动位置与异常收尾；`git diff --check -- <三个既有生产文件>` 通过，仅 Git 的 LF/CRLF 提示，没有空白错误。没有全仓库 pytest、旧 smoke 或 Phase B 检查。

记录：[参数测试](windows_runtime_backend_validation/helper_parameter_tests.txt)、[语法检查](windows_runtime_backend_validation/syntax_checks.txt)、[train/play 静态检查](windows_runtime_backend_validation/train_play_static_checks.txt)、[viewer 静态检查](windows_runtime_backend_validation/viewer_static_checks.txt)。

## 4. 唯一一次实际 GUI 运行

工作目录 `E:\Project\IsaacLab_HARL`。外层实际命令：

```powershell
& D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260929/windows_runtime_backend_validation/supervise_viewer.py --attempt attempt_01_runtime_check
```

监督器传给真实 viewer 的完整命令：

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/view_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --solver greedy --device cuda:0 --max_steps 120 --print_interval 120 --runtime_check --info
```

首次**省略 kit_args**，无 duration、headless、camera/video、learner 或 checkpoint 参数。未调用克隆目录 `Scripts/isaacsim.exe`，未换成 `isaacsim.exp.full`，未添加独立 userConfigPath。默认 step_rate=5Hz，实际执行保持原有节流逻辑；120 是真实 env.step 返回数。

监督器采用标准库 ctypes 的独立 Windows Job Object：Conda 先挂起创建、归入本 Job 后恢复；只监督此进程树，不按进程名终止其他应用。独立读线程连续排空合并 stdout/stderr 并保存 console；主线程单调时钟不受阻塞读影响。App 上限 300 秒，总上限 360 秒，工作预算 350 秒预留 10 秒收尾。桌面只读预检成功，无 headless 替代。

子进程环境从父环境复制，只在本次子进程设置 `HEADLESS=0, ENABLE_CAMERAS=0, LIVESTREAM=0, XR=0`，原值均未设置。UTF8=1由实际启动后解释器确认；没有在脚本中改 PYTHONUTF8，也没有改 Conda 持久变量。

| 事实 | 本次记录 |
|---|---|
| 开始 / 结束 | 2026-09-29 08:59:57.434 / 09:03:35.953，均 +08:00 |
| 监督器 / Conda / viewer PID | 2464 / 28724 / 36004；中间 shell PID 33692 为 viewer 的实际 parent |
| Python / UTF8 | `C:\isaacenvs\isaac45_harl\python.exe` / 1 |
| AppLauncher 来源 | 本仓库 `source/isaaclab/isaaclab/app/app_launcher.py` |
| experience | 本仓库 `apps/isaaclab.python.kit` |
| 有效模式 | GUI；headless=false，enable_cameras=false，livestream=0 |
| 后端请求 / 设置 | source=windows_default；final kit_args=`--/app/vulkan=false`；`/app/vulkan=false` |
| **实际 Graphics API** | **D3D12**；同次 Kit 日志 `:3341`，另 `:2682` 记 DX12 |
| GPU / 驱动 | NVIDIA GeForce RTX 4060 Ti，GPU0 active，7949MB；610.60；Kit `:3314,3341,3347` |
| 版本来源 | Kit `:3`：Isaac-Sim 4.5.0，Kit 106.5.0；仓库 VERSION=2.1.0，扩展 metadata=0.36.23，分别记录，不混为一个版本 |
| torch 来源 | harl 环境 `torch/__init__.py`；2.5.1+cu121（pre-App event） |
| App 创建记录 | 从外层启动至 app_created 共 30.640 秒（不是只计算构造调用耗时） |
| CUDA 数值 | App 后 cuda:0；16×16 ones @ ones，每项16，总和4096，finite=true，同步成功 |
| 实际环境 | `ScanMobileManipulatorEnv`；本仓库源码；legacy；num_envs=1；robot_0/robot_1/robot_2 |
| reset / step | viewer 显式 env.reset 返回一次；120/120 env.step 返回，未抑制环境内部自动 reset |
| 收尾 | env_close_ok=true，work_completed=true，app_close_requested=true，failures=[] |
| 退出 | viewer=0，Conda=0，监督器工具进程=0；无超时、无终止请求、无剩余所属PID；输出排空 |

同次配置来源在 Kit 日志 `:5`：环境内 `kit-core.json`、仓库 experience、环境内 portable `omni/data/Kit/Isaac-Sim/4.5/user.config.json`。`:6` 列出 shared `user.toml` 等不存在；本次没有生成或修改共享配置/experience。Kit `:4` 真实命令包含最终后端参数，实际API另由图形初始化日志确认。

原 Kit 文件：`C:/isaacenvs/isaac45_harl/lib/site-packages/omni/logs/Kit/Isaac-Sim/4.5/kit_20260929_090002.log`。只复制这一文件至本次尝试目录，没有复制整个日志目录。其文件路径同时由当前 viewer 的 settings 输出（events 第5行）及 console 第12行记录，Kit `:2724,2747` 还记录父进程36004。Kit 日志时间文本如 `01:00:02` 未自带时区后缀，与本机 `09:00:02+08:00` 对应；报告以监督器带偏移时间为主，不混用两种显示时间。

## 5. 完成证据、等待与失败/重试历史

`events.jsonl` 第1–2行是启动来源/身份；第3行为共用准备；第5行为App；第6行CUDA；第7–8行真实环境配置/身份；第9行reset；第10行120步；第11–12行环境关闭和pre-close事实。

从外层启动计，5.078秒共用pre-App准备完成，30.719秒App后CUDA完成，32.125秒显式reset完成，57.359秒120步完成，57.765秒环境关闭与pre-close事实完成。整个所属进程树在218.515秒自然结束，包含后续原生/辅助进程收尾时间，不能把57.765秒当最终退出时间。

等待期间曾只读观察到本次 viewer 创建的 telemetry transmitter（PID10812、parent36004、创建约09:00:04）仍在收尾；同次Kit `:2747`也记录该辅助启动。最终 Job 清空且原始 result 明确 `timed_out=false`、`termination_requested=false`，**没有发生超时，也没有实施辅助进程清理或监督器修复**。不从等待时间推断未证实的 handle 根因。

没有实际 GUI 失败、热修改或第二次尝试。首次运行前完成局部实现/纯检查；运行后未更改被验证代码。离线结果整理曾遇到工具 JavaScript 不提供 TextEncoder，改用ASCII十六进制编码传入标准库命令后完成；这不是 viewer 故障，没有因此重新运行 Isaac，原始日志/结果未覆盖。

同次Kit没有检出 `[Error]` / `[Fatal]` 行，仍有非致命警告，例如可选扩展配置缺失、OmniHub不可达、忽略Intel GPU、menu/弃用提示、TLAS预算警告（`:5214–5215`）。console另有 pre-SimulationApp模块提示（`:7–8`）和 h5py/HDF5构建版本警告（`:5384`）。这些未阻止本次完成；保留原文，不将 TLAS 警告认定为OOM，不因本次结果更改依赖或声称全无风险。成功依据是完整阶段事实加进程结果，日志关键字检查只是补充。

没有失败需要匹配 Windows 故障事件，因此未新增事件摘录或扫描历史事件日志。不存在“退出码0覆盖已有失败”的情形：内部失败数组、监督器失败/错误数组均为空。

## 6. 证据索引与工作区保护

- [简洁汇总 JSON](windows_runtime_backend_validation/validation_result.json)：分项覆盖、实际API、CUDA/环境事实与退出依据。保留原始 supervisor 的“API待核对”字段，在汇总层另列同次日志确认，未追改原始结果。
- [完整命令及启动身份](windows_runtime_backend_validation/attempt_01_runtime_check/command.json)、[控制台](windows_runtime_backend_validation/attempt_01_runtime_check/console.log)、[阶段事件](windows_runtime_backend_validation/attempt_01_runtime_check/events.jsonl)。
- [外层原始结果](windows_runtime_backend_validation/attempt_01_runtime_check/result.json)、[同次Kit日志](windows_runtime_backend_validation/attempt_01_runtime_check/kit_20260929_090002.log)。
- [纯参数测试脚本](windows_runtime_backend_validation/test_windows_runtime_startup.py)、[本次外层监督器](windows_runtime_backend_validation/supervise_viewer.py)、[限定补丁](windows_runtime_backend_validation/windows_runtime_startup.patch)。

本轮前已有 TASK_PROGRESS 未暂存修改、20260926/20260928文档和 rokeaCR12 资产未跟踪目录，以及一个旧清理ZIP的已暂存删除；均保留。本次结束时HEAD未变，Git index SHA256仍为 `3563D58E2F15D225A032C35E59AFD0B60B907772DE45B4309BE4B901AEB9F67D`，与开始一致。只做必要只读Git状态/差异检查，未 add/commit/push/tag/reset/restore/checkout/clean/stash；不是全仓库资产或历史库存审计。

没有修改任务生命周期、resolver、reward、mask、仿真动力学、profile authority、HARL installed packages、AppLauncher/SimulationApp、驱动/依赖、持久环境或共享配置。启动Kit按其自身流程产生的当次日志/运行缓存不等于实施了配置补丁；本轮不清理这些产物。

## 7. 未验证能力、后续建议与停止

当前没有阻断本次限定GUI目标的未解决失败。普通模式仅有共用启动源码证明；train/play仅静态；Linux/headless未实测。CUDA矩阵通过不单独证明PhysX GPU功能覆盖、训练、真实关节动力学或任意场景可靠性；本次实际legacy reset/step只证明所记录环境循环。没有进行CR12、机器人资产导入、扫描相机、采集、碰撞规划或两视点运动。

后续顺序仍建议：**先审阅本次补丁和结果 → 另行授权资产与基本关节驱动 → 单视点运动/按需采集 → 双视点连续循环 → 后续MRTA接入**。不必为了此次已通过的目标再制造Vulkan崩溃或追加运行矩阵。

新USD已由用户删除，不寻找、不恢复，不据此推断文件损坏。沿URDF准备派生资产属于后续授权；八个link惯性问题仍独立存在，自动重算/近似尚未批准。固定底盘、升降保持方式、运动参考与碰撞检查一致性仍需在执行实现时确定。采集成功与随后关闭失败必须分别记录，关闭未确认不能开始下一段运动；本轮没有实施这些功能。

本次文档变更为新建本报告和紧凑验证记录、在TASK_PROGRESS中增加当前结果及链接，旧报告不改写。**局部启动实施与限定GUI/CUDA/viewer验证已完成，等待GPT/用户审阅；本任务到此停止，不自动进入下一阶段。**
