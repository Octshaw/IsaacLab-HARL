# Isaac Sim 4.5：Windows Vulkan 闪退与 D3D12 GUI 成功的交接说明

日期：2026-09-28  
用途：反馈给另一个 GPT 窗口，并与 Codex 当前的项目评估报告对照。  
范围：本机运行时与启动配置排查，不是重新安装指南，也不是 HARL 评估完成报告。

## 先读这一段

本窗口在 `C:\isaacenvs\isaac45` 中验证到：RTX LiDAR UI 的 GBK 解码错误在启用 `PYTHONUTF8=1` 后消失；随后 Vulkan GUI 在 `app ready` 后出现原生访问异常，Windows 事件定位到 `rtx.scenedb.plugin.dll`。换独立用户配置、仍用 Vulkan 时继续复现。保持驱动 610.60 和现有环境，使用 `--/app/vulkan=false` 切到 D3D12 后，GUI 稳定、菜单可操作，日志退出码为 0。

**已经验证的是独立 Isaac Sim GUI；还没有在本窗口验证当前驱动下的 Isaac Lab/HARL 实际代码入口、headless、CUDA reset/step、checkpoint 推理或评估。Codex 当前也发现问题是用户的最新反馈，但其报告、命令和日志未在本窗口提供，不能直接认定两边故障完全相同。**

## 1. 证据所对应的环境

下表对应 GUI 诊断环境，不能直接视为 `isaac45_harl` 的实测环境清单。

| 项目 | 记录 |
|---|---|
| 系统 | Windows 11 Home China 24H2；日志内核版本 10.0.26100.9457 |
| GPU | NVIDIA GeForce RTX 4060 Ti，8GB 专用显存 |
| RAM | 本次日志 Total Memory 32430 MB，约 32GB |
| CPU | Intel Core i7-13700 |
| 驱动 | 两组图形后端对照日志均为 610.60 |
| Python | `C:\isaacenvs\isaac45\python.exe`，3.10.20 |
| Isaac Sim | pip 元数据 4.5.0.0；界面日志版本 4.5.0-rc.36 |
| torch / torchvision | 2.5.1+cu121 / 0.20.1+cu121 |
| numpy / scipy | 1.26.4 / 1.13.1 |
| osqp / qdldl | 0.6.7.post3 / 0.1.7.post4 |
| h5py | 3.10.0 |
| UTF-8 | 诊断进程中 `UTF8 mode: 1` |
| 依赖元数据检查 | `pip check`: `No broken requirements found.` |

来源：`evidence/01_environment_isaac45.txt`、`03_vulkan_test_info.txt`、`05_d3d12_gui_passed.txt`。依赖元数据一致不等于所有运行时功能通过。

历史背景：用户先前确认 Isaac Lab 为 v2.1.1，并为 HARL 使用独立环境/项目。当前 Codex 评估究竟使用什么 Python、哪个 checkout 和 commit，仍以其实际运行记录为准。

## 2. 本次排查经过及证据

### 2.1 独立的文本解码错误

最初在 RTX LiDAR UI 扩展启动时出现：

```text
UnicodeDecodeError: 'gbk' codec can't decode byte 0xa0 in position 1096
json.load
isaacsim.sensors.rtx.ui/.../extension.py(54): on_startup
```

用户确认，在启动前设置 `PYTHONUTF8=1` 后，这条错误消失。该项来自本窗口对话中的报错和用户反馈；本包没有单独附上最初解码失败的完整原日志。后续诊断记录确认 UTF8 mode 为 1。

这和之后的原生访问异常应分开记录，不能归并为一个“显卡错误”。

### 2.2 Vulkan 仍然闪退

| 对照 | 结果 |
|---|---|
| 原用户配置 + Vulkan | GUI 启动后访问异常；11:17 Windows 记录定位 RTX DLL |
| 新建独立空用户配置 + Vulkan | 仍失败；11:30 记录同一 DLL、同一异常代码、同一偏移 |

独立配置运行记录：

```text
Experience: isaacsim.exp.full
Graphics API: Vulkan
Driver: 610.60
[12.330s] app ready
Windows fatal exception: access violation
EXITCODE=-1073741819
```

Windows 原生异常特征：

```text
Faulting module: rtx.scenedb.plugin.dll
Exception code: 0xc0000005
Fault offset: 0x00000000000d6d4b
```

故障模块位于 Isaac Sim 的 `omni.hydra.rtx` 扩展目录，见 `04_vulkan_windows_error_excerpt.md`。Python 堆栈中还有菜单/快捷键函数，但不能据此认定菜单代码是根因。

证据：
- `02_vulkan_gui_failed.txt` 第 69 行：驱动和图形后端；
- 第 565–568 行：app ready 后访问异常；
- 第 622 行：退出码；
- `03_vulkan_test_info.txt`：实际 Python、参数、版本；
- `04_vulkan_windows_error_excerpt.md`：原 Windows 事件字段摘录。

独立用户配置未解决此问题；这并不等于已排除所有缓存或系统因素。

### 2.3 D3D12 GUI 对照通过

保留环境与驱动，测试脚本仍设置 UTF-8、仍为新建独立空用户配置；图形启动参数改为：

```text
--/app/vulkan=false
```

实际启动命令见 `scripts_tested_gui/isaacsim_gui_d3d12_test.bat`。该脚本没有安装、卸载依赖或修改驱动；实际日志显示：

```text
Driver Version: 610.60 | Graphics API: D3D12
[10.994s] app ready
[114.467s] Isaac Sim Full App is loaded.
EXITCODE=0
```

用户明确反馈：“界面保持了稳定，菜单操作什么的也都正常”。

证据：`05_d3d12_gui_passed.txt` 第 67 行及第 565–571 行。成功日志中仍有 `TLAS limit` 警告，因此该警告本身不足以认定显存不足或判定运行失败。

`06_d3d12_windows_events.txt` 只说明查询未返回匹配的近期事件；不能单独证明没有崩溃。主要成功依据是用户操作反馈及成功运行日志。

## 3. 当前结论：分清事实与推断

**已证实：** 同一本机环境、日志中同为驱动 610.60，Vulkan GUI 失败；独立配置不能消除该失败；使用 D3D12 的一次 GUI 操作测试通过并以 0 退出。

**合理推断：** 当前故障与本机的图形后端运行路径有关，D3D12 是已有 GUI 证据支持的候选规避方案。

**尚未证实：**
- 610.60 驱动自身是唯一根因，或该版本对所有机器/Isaac Sim 工作流都有问题；
- `rtx.scenedb.plugin.dll` 自身存在某个已确认的软件缺陷；
- 当前错误由显存不足导致；
- `isaac45_harl` 和 `isaac45` 的依赖、导入路径、启动参数完全相同；
- Codex 评估失败具有相同的原生故障特征；
- D3D12 已经成为默认，或已经在项目代码入口生效；
- CUDA 运算、仿真 reset/step、推理、评估、相机采集均已通过。

**因此不要将本结论写成“项目评估已修复”或“回滚驱动解决了问题”。**

## 4. 上一窗口提出、尚未收到执行结果的方案

以下只作为待检查的候选实现，不是已经完成的修改记录：

1. 使用 Windows Kit 共享 `Documents\Kit\shared\user.toml` 设置 `[app]` 下的 `vulkan = false`。需由实际启动日志确认配置路径、覆盖优先级和后端；本窗口没有收到此文件或应用后的测试日志。
2. 在真实项目的 `AppLauncher` / `SimulationApp` 创建之前，通过该入口实际支持的参数或配置，显式选择 D3D12；仅针对 Windows。上一窗口给过 `args_cli.kit_args` 追加 `--/app/vulkan=false` 的示意，但尚未基于 HARL 本地入口完成审查或验证。
3. 保证实际 Python 进程启动时 `PYTHONUTF8=1`，而不只在偶尔手工调试时设置。
4. 已提供 `proposed_not_validated/check_isaaclab_runtime_defaults.py`。它用于空场景的默认配置、真实 CUDA 张量运算及 reset/120 steps 检查，刻意不注入图形后端。**没有本机运行结果，也不是 HARL 评估通过证据。** 引用或运行前应审查是否适合实际工程及既有 CUDA 初始化顺序。

不要把生成了脚本当成已经运行了脚本，也不要同时修改多个启动层却不记录最终生效的配置来源。

## 5. 需要接收窗口与 Codex 优先完成的工作

### 5.1 先确认是不是同一类问题

请先阅读 Codex 当前报告和真实失败日志，对照：失败阶段、实际 Graphics API、退出码、Python 堆栈、原生故障模块。只看到“闪退”或同样的 0xc0000005 还不足以证明完全同因；如果评估已经使用 D3D12 或崩在其他组件，应单独分析，不能硬套 GUI 结论。

### 5.2 只在真实代码入口做最小必要处理

用户主要从 Python/评估脚本启动，偶尔手动打开 `isaacsim`。最终目标是实际入口稳定，不是再做一个仅能启动 GUI 的快捷方式。

检查实际 interpreter、环境变量、工作目录、源码导入路径、repo commit、experience `.kit`、参数转发、子进程继承和现有启动前初始化逻辑。尤其不要把 `isaac45` 的验证直接迁移成 `isaac45_harl` 的结果。

优先保持当前包版本和驱动，用可追踪、可撤销、Windows 限定的入口设置验证候选规避方案。不要盲改 installed HARL、系统范围配置或工程全部 `.kit` 文件；不要覆盖现有生命周期/控制/训练初始化约定。若要改用户全局 Kit 配置，需要明确作用范围与实际生效记录。

### 5.3 用分层结果恢复评估，不跳过验证

建议先做与当前故障相关的小测试，再恢复现有评估：

- 实际代码入口能启动；日志记录 UTF8 状态、Python、Graphics API、最终 `/app/vulkan` 和仿真 device；
- 真正的 CUDA 张量运算及结果读取成功，不仅仅是 `torch.cuda.is_available()`；
- 真实使用的环境能 reset 并有限步 step；如项目需要 GUI 和 headless，则分别验证；
- 再执行当前评估所需的 checkpoint 加载、策略推理/短评估、结果保存与进程退出；
- 只有本次评估用到相机时，才在该范围内验证实际相机数据；不要扩展成新的传感器或执行控制项目。

启动失败不能混入任务完成率等算法指标当成“策略得零分”。此次运行时事件也不能自动否定以前已经完成的项目阶段。

## 6. 请另补的 Codex 材料（本包没有）

提供一个最小评估补充包即可：

1. 当前评估报告，失败的完整命令/工作目录、原始控制台日志、对应 Kit 日志；
2. 实际 Python 路径与依赖简表、GPU/驱动、源码 checkout 路径/commit；
3. 创建 AppLauncher/SimulationApp 的入口及共用启动 helper；有子进程时包含调用处；
4. 本次已修改的启动配置/脚本 diff，以及修改后运行结果。未修改则明确写“未实施”。

如果已经按上一窗口建议创建 `user.toml`、保存 Conda 环境变量或修改入口，请补充实际文件/设置输出；不能只把建议文本当成实施证据。

不必发送整个 conda 环境、全部缓存、5 月完整安装记录、大型模型资产或所有历史实验目录。代码若尚未进入 checkpoint 加载阶段，首轮排查通常也无需搬运模型权重。

## 7. 研究与协作边界

这是当前 Windows 运行时兼容性事件。先按证据审查，再决定最小修复，不为绕过启动异常而改动 MRTA lifecycle、resolver、reward、action mask、策略/优化器或评估统计口径；也不要改变 Linux 服务器后端或据此宣称跨平台验证完成。

本窗口没有读取 Codex 当前评估报告。接收窗口应整合两边证据并标注“已证实/推测/待验证”，而不是直接批准所有既有建议。
