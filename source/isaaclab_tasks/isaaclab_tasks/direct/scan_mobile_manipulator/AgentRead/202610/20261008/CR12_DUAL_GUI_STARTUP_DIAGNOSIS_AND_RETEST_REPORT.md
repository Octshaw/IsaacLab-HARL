# CR12 双机 GUI 启动定向诊断与唯一条件化复测

日期：2026-10-08，Asia/Shanghai（UTC+08:00）。**本轮唯一 App 完成 CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_PASS，六层均 PASS；等待 GPT/用户审阅，不自行授予 GPT REVIEW PASS。** native 窗口1440×900、实际D3D12；在同一App内完成原冻结双机case、四份fresh RGBA及独立OFF、并行/产品隔离、共同terminal/rebuild和自然退出。构造26.438秒，全树202.672秒；118 transitions、1416受控physics/708 render，共同初始化2步另计。App **1/1**，未再运行。

上一轮双机实现/202项CPU成果、120×0启动失败分类及停止处理已经用户/GPT接受，历史FAIL不回写。**本次候选条件下窗口与真实双机入口可运行；DPI是否为唯一根因仍未确定。** 第1节保留首App前冻结的实验说明，其余章节为本轮实际结果。

仓库 `E:\Project\IsaacLab_HARL`；本轮只读 HEAD 为 `main / a8c618a32da65747827f1cb3f722fac24df2aec8`。原双机未提交代码及历史文档保留。`T=source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`，`E=scripts/environments/`，`Q=source/isaaclab_tasks/test/`，`L=logs/scan_assignment/20261008_cr12_dual_gui_startup/`，均为仓库相对路径。

## 1. 首 App 前冻结的唯一实验意图

冻结时间：2026-10-08 22:00 +08:00；**选项 B：窗口 DPI 路径的最小行为组候选，配合同一目标进程的只读观测**。不是已证实根因的修复，不做参数矩阵或原样盲重启。

支持依据：最近两次单机成功与上次双机失败，在保存的运行前摘要中，整个 private 文件 hash/size 相同，不只是三个窗口字段相同；进程创建代码也相同。上次故障在 `AppLauncher/SimulationApp` 构造期，`run_dual` 未调用，不支持归因于双机器人或双扫描 product。请求尺寸与native尺寸之间存在未被记录的窗口创建/缩放/桌面边界。

本地 `omni.appwindow 1.1.9` 文档与 `IAppWindow.h` 明确提供 monitor DPI 缩放及 override。安装包 `omni.kit.mainwindow` 自带测试参数也配套使用以下两值。因此采用同一含义的一组 **CLI 覆盖**，排查窗口尺寸自动缩放路径；不改变系统/进程 DPI awareness 或显示器设置。

| 精确 setting | 本地默认依据 | 本轮显式 CLI | 文件与历史状态 |
|---|---|---|---|
| `/app/window/scaleToMonitor` | extension.toml= true，SETTINGS.md:33–35，IAppWindow.h:69–72、135–138 | `false` | 不写入源/private文件；历史composed值UNKNOWN |
| `/app/window/dpiScaleOverride` | SETTINGS.md:77–79 / WindowDesc default=-1.0 | `1.0` | 不写入源/private文件；历史composed值UNKNOWN |

仅上述两条是新增行为设置；保留原 private路径、D3D12和所有业务参数。private基础白名单仍为 `/persistent/app/window/{width,height,maximized}` → `1440/900/false` 的0–3项语义差异，无额外文件字段。GUI renderer1280×720、扫描相机640×480不变。新诊断开关默认关闭；本次显式开启后，只读取实际目标Python的 startup flags/尺寸字段单位、session、window station/desktop、monitor/work area及DPI状态，并在App成功返回后立即读窗口尺寸和composed值。

预期：不随monitor缩放、DPI固定1.0时，AppWindow读回必须是 **1440×900**。构造成功后还必须确认D3D12、rendering experience、private来源和两个候选setting，再创建机器人场景；不接受120×0或任意非零尺寸替代判据。没有新增physics/render/update/等待。前后观测耗时纳入原480s全树预算。

解释边界：若窗口通过，只支持“本次候选条件下启动成功”，不能证明DPI是唯一根因，也不能排除未控制的桌面/时间差异及观测开销。若仍失败，保留实际子进程边界证据；一次负结果不能排除所有窗口恢复机制。`/app`、`/persistent`、native派生和Win32 STARTUPINFO的最终择值如本地源码不可见，保持UNKNOWN，不编造120或0的算式。

运行条件：局部CPU/语法、strict JSON/private保护、完整argv与输入冻结通过后，只开 **1个App**，直接真实双机入口 `--integration-case dual_normal_staggered`。构造成功即在同App继续原冻结case；任何App失败后不再启动第二次，不修改Host/adapter/控制器/相机FSM/验收谓词。

## 2. 成功与失败的真实输入比较

仅定向读取同日三个历史attempt：单机 `logs/scan_assignment/20261008_cr12_lifecycle_integration/attempt_01`（normal，记S1）、同目录 `attempt_02`（cancel_then_reclaim，记S2），双机 `logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01`（记F）。没有执行其中命令、查找全盘或恢复历史raw。

| 维度 | S1 / S2成功 | F失败 | 支持的结论/限制 |
|---|---|---|---|
| Python / Conda / cwd | `C:\isaacenvs\isaac45_harl\python.exe` / `D:\miniconda3\Scripts\conda.exe` / 当前仓库 | 相同 | 不是base isaac45；harl环境沿用 |
| 实际启动模式 | GUI、camera-enabled、cuda:0、UTF8=1、D3D12 | 相同 | F也已实际选择D3D12，不能用Vulkan旧故障替代 |
| experience | 同仓库 `apps/isaaclab.python.rendering.kit` | 相同 | 本地仓库VERSION2.1.0、metadata0.36.23是不同层字段；实际日志IsaacSim4.5、torch2.5.1+cu121、驱动610.60 |
| 入口/case | `run_cr12_lifecycle_integration.py` / normal或cancel_then_reclaim | `run_cr12_dual_lifecycle_integration.py` / dual_normal_staggered | 均转入shared main；物理/Host/domain在App返回后，parse/pre_app_validator在App前 |
| Kit基础argv及顺序 | renderer1280×720、window1440×900在基础参数；后拼原脚本unknown argv、展开private与vulkan=false | 同样顺序，case/output/private路径等合理差异 | 子Python入口名不同；Kit的argv[0]均为安装simulation_app.py，不把二者混同。未发现width/height冲突；顺序不证明native最终优先级 |
| App前实际逻辑 | S2额外读取已通过normal监督结果；纯CPU资产/virtual mount/保护输入/PD选择后，helper→CUDA→App | validate_case只核固定case/manual；同样基础准备 | 跨单/双7个hash变化文件中mount/shared入口参与App前，不能概括全部差异只在App后；这些准备未创建双机器人/product，没有证据解释120×0 |
| 进程环境 | `os.environ.copy()`，覆盖PYTHONUTF8=1/HEADLESS=0/ENABLE_CAMERAS=1/LIVESTREAM=0/XR=0 | 相同 | 完整历史inherited环境未采，不能用当前环境反推 |
| 监督创建方式 | Popen，cwd/env明确；stdin DEVNULL、stdout PIPE、stderr STDOUT、bufsize0、CREATE_SUSPENDED(0x4)，assign owned Job后resume | 相同代码 | 未显式传STARTUPINFO/show/尺寸/shell选项；Python/Conda后续子进程实际startup字段历史UNKNOWN |
| source→private（A类比较） | 基础窗口三字段改为1440/900/false，其他semantic相等 | 相同 | A的三项本身不能证明跨运行等价，需下行B |
| 运行前private（B类比较） | 两次84107 bytes，SHA256 `8bfc571cb3a4501897f2b2bf9f4a40e53862d5eadca77326c91bd32013f70468` | 完整相同 | 当次pre-popen摘要证明输入文件整体字节一致，证据强于只比三值 |
| source历史摘要 | 三次114100 bytes，SHA256 `9b3b72015f7e8ca7a74ad179a81329bc3f00966862dd0ce8f831831a12dea625`、mtime_ns1790759017622695800 | 同左 | 历史摘要支持，不从今天source倒推 |
| private运行后文件 | Kit正常写回；摘要仅新增一个console来源bool字段，JSON格式也改变 | 未写回 | 当前成功private是after-run文件，不能直接称为当时startup输入；严格语义比较保留此限制 |
| 配置加载 | Kit core → rendering experience → 对应private；同次日志列共享user.toml等不存在 | 同样来源顺序 | 加载private成功不等于其宽高被native最终采用 |
| authored / CLI / composed / native | authored1440/900/false；CLI窗口1440×900；历史composed UNKNOWN；native1440×900 | 前三者相同证据范围；native120×0 | 关键分歧在请求到native边界 |
| 桌面、monitor、DPI、实际子startup flags | 未采样，UNKNOWN | 未采样，UNKNOWN | 不把监督父进程input-desktop可打开代替目标子进程状态 |
| 最早窗口结果 | S1 console:3383、S2:3342，Created1440×900并app_ready | F:3356 Created120×0；3924–3932 swapchain/访问异常 | 均在robot/product创建之前 |

S1 15:44:49.218→15:46:14.096 +08，构造22.656s、全树84.875s，目标/Conda exit0；S2 15:46:40.839→15:48:47.560 +08，全树126.734s、双exit0。F 18:08:50.456→18:09:13.781 +08，全树23.328s，目标0xC0000005、Conda0xFFFFFFFF；无app_ready、0受控步。历史退出/接受状态均保持，不要求重开单机人工观看。

严格JSON检查拒绝重复key、NaN/Infinity，比较保留bool/int/float类型；完整配置不复制进Markdown或摘要。本轮仅保留相关差异。完整历史inherited环境、native内部尺寸派生、创建瞬间composed settings没有记录，明确不补齐。

历史父监督与子命令分开：三次`command.json`均记录监督器启动的Conda子命令，不是启动supervisor的父argv。F完整父命令见旧双机报告第4节，实际为：

```powershell
$env:PYTHONUTF8='1'
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/repro/supervise_cr12_dual_lifecycle_integration.py --attempt-dir logs/scan_assignment/20261008_cr12_dual_lifecycle_integration/attempt_01 --integration-case dual_normal_staggered
```

以上是**历史记录，本轮未执行**。S1/S2旧单机报告第7.2节说明用项目Python `-X utf8`及对应监督脚本/参数，但限定证据未保留完整父argv原件，故该层完整命令UNKNOWN；不将等价重建命令写成历史实际命令。三次完整Conda子argv、目标Python argv及最终Kit参数则均保留于command/console及本轮比较摘要。

子Conda命令公共顺序为 `conda run --no-capture-output -p <harl> python -u <entry> --usd-path <共同v1 USD> --output-dir <S1/S2/F目录> --device cuda:0 --external-forces-every-iteration on --enable_cameras --info --integration-case <case> --kit_args=--/app/userConfigPath=<本次private>`；仅S2随后有 `--normal-result <S1/supervisor_result.json>`。目录、入口、case在上表和本节首段逐一对应，共同USD为第5节完整命令所列路径。

最终Kit来源为各自console:10–11。S1/F为共同22项基础+15项追加=37项；S2为22+17=39项。公共前缀依次为安装simulation_app.py、同仓rendering experience、exe-path、viewport displayOptions3094、materialDb/hydra/syncUsdLoads三个true、renderer宽高、window宽高、multiGpu true、fastShutdown true、installSignalHandlers0、两个ext-folder及其路径、activeGpu0、cudaDevice0、portable、hideUiFalse。追加部分保持上述子命令从`--usd-path`开始的顺序（不含Python entry），再追加展开的private setting、vulkan=false；S2的normal-result在整体kit_args token之后、展开private之前。最终实际argv不仅是三个窗口值比较，也没有把整体kit_args字符串当成已经拆开的单个setting。

## 3. 请求到native的本地边界

`run_cr12_single_view_capture.parse_args` 接收全部项目参数，`:728–747`先执行pre_app_validator、纯CPU load_accepted_inputs、resolve_virtual_mount、输入保护与PD选择；单机S2的前置校验见`run_cr12_lifecycle_integration.validate_case_prerequisite:20–32`，双机见`run_cr12_dual_lifecycle_integration.validate_case:26–28`。现有Windows helper保留原kit_args并追加D3D12。原pre-App CUDA准备先于App构造，未被替换；双机入口顶层仅引入shared main和普通Python依赖，Host/domain/runtime导入位于`run_dual`内。新增观测放在CUDA返回后、AppLauncher紧前，因此不通过提前import大量omni/pxr改变原顺序。

当前仓库 `source/isaaclab/isaaclab/app/app_launcher.py:754–760` 将kit_args按`str.split()`追加到sys.argv；:780创建SimulationApp。安装 `isaacsim/exts/isaacsim.simulation_app/isaacsim/simulation_app/simulation_app.py:303–319` 先写renderer/window默认请求，:341–344取unknown args，:424–427后追加再调用`app.startup`。路径无空格；DPI覆盖在一个kit_args值内传递，没有第二个kit_args或Windows引号拆分问题。原脚本选项仍可能进入Kit unknown argv，与历史路径一致。

`apps/isaaclab.python.rendering.kit:17–19`依赖base；`apps/isaaclab.python.kit:176`启用persistent，:183–185只配置窗口icon/title。实际 `omni.appwindow-1.1.9+d02c707b.wx64.r.cp310/config/extension.toml:24–30`定义窗口尺寸和scaleToMonitor默认。其 `docs/SETTINGS.md:57–67`将persistent三字段描述为previous saved；`omni/dev/include/omni/kit/IAppWindow.h:23–43,160–166`定义两组key并说明startup从carb settings取参，未公开二者最终择值算法。

F日志的appwindow设置先应用，native DLL startup随后创建120×0，再import appwindow Python；因此单靠App成功后的Python读取，不能回填创建前composed值。`carb/settings/ISettings.h:992–1030`的setDefault语义只是在key不存在时设置，不等同于一个已证实的`/defaults`恢复优先级。未找到受支持的`ignoreStartupInfo`或“禁止启动恢复”setting；`saveSizeOnExit`只说明退出保存，不能当禁用启动读取使用。

候选两值直接依据为本地appwindow文档、`IAppWindow.h:69–72,103–115,135–138`和 `omni.kit.mainwindow-1.0.3+d02c707b/config/extension.toml:34–38`配套测试参数。没有借用测试中的headless/hideUi，不改experience/扩展依赖/installed files，也没有反编译DLL。

## 4. 实际启动局部改动及运行前检查

| 文件/符号（仓库相对路径） | 本轮变化及用途 | 默认、撤销与边界 |
|---|---|---|
| `E/run_cr12_single_view_capture.py:28,758–765`，`parse_args/main` | 增加默认false的`--gui-startup-diagnostics`及App紧前/返回后两个条件调用；共7行接线 | 未启用时不import新helper、不采样；移除本轮接线即可撤销，不能从HEAD恢复整个含既有双机修改的文件 |
| `E/_cr12_gui_startup_diagnostics.py:175,188,211,229,268,300,338` | 新增stdlib只读Win32采样、字段单位/错误记录、post-App setting/IAppWindow读取、同次Kit后端读取及冻结条件核对 | 顶层不启动Isaac、无DPI setter；实际carb/omni读取在App返回后。失败先记录再拒绝建scene；原初始化/业务不变 |
| `Q/test_cr12_gui_startup_diagnostics.py` | 可复用CPU/fake/AST检查 | 不是runtime证据，不放AgentRead |
| `L/repro/supervise_cr12_dual_gui_startup.py:85,613,805,854,1097,1140` | 从旧监督复制本轮独立版本，加入两条CLI候选、诊断开关、唯一新attempt授权及六层结果 | 原`completion_checks`及13个关键既有helper的AST保持；180/480s、owned Job、输出排空及原完整双机谓词保持；没有自动重试或清历史故障 |
| `L/repro/prepare_private_user_config.py` | 本任务独立private准备，拒绝重复key/非法数值，类型保真，0–3项白名单 | source只读；旧helper不改，运行后写回另列 |
| `L/repro/compare_startup_inputs.py`、`test_startup_supervisor_cpu.py` | 三次历史输入定向比较、监督器CPU检查 | 只检查本轮所需输入/分类，不形成全仓审计体系 |

两条DPI候选只在本轮监督器显式CLI中加入，**没有改Windows共用helper或所有入口的默认值**。`_windows_runtime_startup.py`、`view_scan_assignment._prepare_cuda_before_app`、AppLauncher/SimulationApp安装文件、experience、run_dual/Host/adapter/控制器/相机FSM/原验收谓词均未在本轮修改。回退仅需撤销新接线及本轮候选使用；局部[接线补丁](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/shared_gui_startup.patch)以本轮开始时dirty版本为基准，保留用户既有工作。本轮未执行回退或Git写操作。

实际CPU命令，cwd均为仓库根，正确解释器已先核对：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_gui_startup_diagnostics.py
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/test_startup_supervisor_cpu.py
```

结果分别 **24/24、12/12**，合计36个不同方法：31项含CPU行为断言（含2项摘取真实main启动前缀AST后执行），5项纯AST/source。修改/新增Python语法检查通过。24项最终耗时0.091秒，12项0.134秒；不叠加中间版本、不重跑或重计旧202/182项。去除7行接线后，parse/main AST与本轮开始时原文一致；不是拿HEAD覆盖dirty版本。Win32本地签名与IAppWindow getter经静态复核，真实采样只来自下节唯一目标进程。

只读工具曾遇到一个多行`conda python -c`元数据命令被Conda拒绝，以及历史比较的路径分隔符字段定位错误；改为单行元数据及规范化字段后完成。均在App前、无runtime。对本轮31个直接相关代码/检查输入的冻结摘要在运行前核对通过，运行后再次只读核对 **31/31一致**，没有业务中途修补。不是全仓hash清单。

## 5. 唯一运行的完整命令、来源与窗口结果

执行工作目录 `E:\Project\IsaacLab_HARL`。实际父监督命令如下；监督器自行从只读source准备fresh private、检查输入，然后只创建一个真实双机App：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/supervise_cr12_dual_gui_startup.py --attempt-dir logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01 --integration-case dual_normal_staggered
```

实际监督子命令（由监督执行，**不是建议绕过监督直接启动**）：

```powershell
D:\miniconda3\Scripts\conda.exe run --no-capture-output -p C:\isaacenvs\isaac45_harl python -u scripts/environments/run_cr12_dual_lifecycle_integration.py --usd-path E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd --output-dir E:\Project\IsaacLab_HARL\logs\scan_assignment\20261008_cr12_dual_gui_startup\attempt_01 --device cuda:0 --external-forces-every-iteration on --enable_cameras --info --integration-case dual_normal_staggered --gui-startup-diagnostics "--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/private_config/user.config.json --/app/window/scaleToMonitor=false --/app/window/dpiScaleOverride=1.0"
```

实际目标 `C:\isaacenvs\isaac45_harl\python.exe` PID18052，受监督Conda PID13804。source路径为 `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\user.config.json`；private为上述当前attempt路径。父进程`-X utf8`生效；对子链按原逻辑在启动前以env copy合并`PYTHONUTF8=1,HEADLESS=0,ENABLE_CAMERAS=1,LIVESTREAM=0,XR=0`，实际目标`utf8_mode=1`。未导出完整环境。

最终Kit顺序由console:11–12、17确认：原SimulationApp基础参数（renderer1280×720、window1440×900、activeGpu0/physics cudaDevice0、portable/hideUiFalse等）→ 原脚本unknown参数（含一个整体kit_args值）→ 展开的`userConfigPath` → `scaleToMonitor=false` → `dpiScaleOverride=1.0` → helper追加的`vulkan=false`。四个展开setting各一次，无后续同key冲突；既有Kit参数保留。console:18记录Kit core→本仓`apps/isaaclab.python.rendering.kit`→当前private顺序。

**复现命令的限制：**以上是已实现、已实际执行的fresh-private有界监督命令。该监督器严格只准本主题`attempt_01`，额度现已消耗；在当前工作区重跑会拒绝，不能简单换输出路径后声称可运行。本轮没有实现额外manual授权/目录入口，也未绕过监督。无需用户重新启动才能接受已有结果；若将来确需新的可运行复现，应另行授权最小的新输出/预算接线，保留同等监督。当前不要求人工观看或新App。

### 5.1 四层窗口证据与配置保护

| 层次 | 本轮读到的值 | 来源与时点 |
|---|---|---|
| authored private | persistent width1440/height900/maximized=false；DPI两key仍未写入private | `source_private_config_summary.json`准备期三项diff，其他值相等 |
| CLI请求 | window1440×900，renderer1280×720；候选false/1.0；vulkan=false | console:11–12、17实际Kit argv |
| native创建 | **Created window: width=1440,height=900** | console:3354，Kit原文2026-10-08 14:14:21（该行未标时区，与本地UTC+08墙钟相差8小时），startup+1055ms；未见createSwapchain错误 |
| App后composed与IAppWindow | `/app/window`1440/900/false/1.0；persistent1440/900/false；native getter1440/900、dpi_scale1.0、override1.0、非maximized | 同PID在App返回后紧接采样；不能反推窗口创建瞬间的composed值，也不宣称Win32 client/outer rect |

console:2700及同次Kit:2688是DX12，console:3529及Kit:3517为D3D12；不是仅依据`vulkan=false`。同次Kit来源为 `/log/file`/app_ready指向的 `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\logs\Kit\Isaac-Sim\4.5\kit_20261008_221420.log`；有当前attempt内副本，没有选目录latest。App后建scene前12项冻结条件全部通过，包含真实同次日志D3D12、窗口、DPI两值、experience、private、GUI/camera及renderer。

source运行前后size114100、mtime_ns1790759017622695800、SHA256 `9b3b72015f7e8ca7a74ad179a81329bc3f00966862dd0ce8f831831a12dea625`均不变，semantic diff0。运行前private仍与S1/S2/F完整字节相同（84107 bytes，`8bfc…468`）；本轮额外候选在CLI，不冒称source/private新增字段。Kit退出正常写回private后114157 bytes、`a5dfc82e…1b0`，仅新增 `/persistent/app/extensions/console/sources/omni.usd-abi.plugin` bool来源项；格式变化亦导致字节不同。该项是**运行输出**，不是偷偷增加的第四项启动输入。无source外部改变证据。

### 5.2 实际目标进程的只读桌面采样

采样在原pre-App CUDA返回后/App紧前，以及App返回后，均PID18052、线程27536。记录API、状态、单位及错误；本轮这些读取均OK，不用默认0代替失败。

| 字段/API | App前 → App后 | 解释范围 |
|---|---|---|
| `ProcessIdToSessionId` | session1 → 1 | 当前目标进程，不代表历史故障时状态 |
| `GetProcessWindowStation/GetUserObjectInformationW` | WinSta0，flags1，visible=true → 相同 | 可见display surfaces |
| `GetThreadDesktop/UOI_IO` | Default，receiving_input=true → 相同 | 当前线程桌面；未切换/解锁/模拟输入 |
| `GetStartupInfoW` | flags0；requested `Winsta0\Default` → 相同 | position raw[0,1]、window size raw[100,100]、console buffer raw[0,0]、show raw1的启用位均false；不是有效尺寸指令，字符数不等于像素 |
| `EnumDisplayMonitors/GetMonitorInfoW` | primary monitor[0,0,2560,1440]/work[0,0,2560,1392]；second[-1920,356,0,1436]/work[-1920,356,0,1388]；前后相同 | caller DPI上下文的虚拟桌面坐标，不是renderer像素 |
| `GetThreadDpiAwarenessContext/GetAwarenessFromDpiAwarenessContext` | unaware(0) → per_monitor_aware(2) | Kit构造前后读数不同；诊断没有调用任何DPI setter，不把观察称为我们修改了awareness |
| `GetDpiForSystem` | 96 → 96 | caller视角DPI，不是raw monitor DPI；不能据此推断所有monitor均100%缩放 |

当前采样没有揭示120×0的算式。历史三次没有这组采样，不能把今天桌面状态补回F；也不能仅凭两个monitor或DPI变化认定唯一原因。

## 6. 原冻结双机case的分层实际结果

| 层 | 结果 | 关键证据 |
|---|---|---|
| CONFIG_AND_LAUNCH_INPUT | PASS | 31份直接输入匹配、fresh private/白名单/source保护、实际argv/UTF8/GUI/cuda:0正确 |
| GUI_APP_CONSTRUCTION | PASS | native1440×900、同次D3D12、12项post条件；构造26.438s≤180s |
| DUAL_SETUP | PASS | 两实例预期Y间距2m，pre-init映射/anchor/native映射先验证后冻结四任务；一个SimulationContext、共同初始化2步；两独立Camera/product |
| DUAL_BUSINESS | PASS | 4次真实绑定/4份fresh/4次独立OFF/4次C、真实authority receipt后退役；118块末全域事务；没有业务局部修复 |
| PARALLEL_AND_PRODUCT_ISOLATION | PASS | 1128个实际运动重叠tick；混合阶段成立；72tick错峰；同一render上一个产品OFF另一个fresh的原始片段成立 |
| TERMINAL_AND_SHUTDOWN | PASS | 四任务完成、累计[2,2]、143维真实sidecar、共同terminal/逻辑rebuild/一行facade历史ACK；两相机各release一次；双exit0、全所属自然退出 |

完整旧监督的9组完成谓词均true，不是只通过新增窗口检查：`work_and_exit, setup_mapping, host_and_authority, capture_save_off, resource_continuity, terminal_transport, pose_and_physics, artifact_delivery_pass, parallel_product_isolation`。`original_dual_validation_pass, integration_runtime_pass, process_exit_pass, coverage_complete`均true，分类 **CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_PASS**，不是COVERAGE_INCOMPLETE。

### 6.1 四次按需采集与隔离

下表global tick为受控clock（不含初始化2步）。各请求局部均600步到位（121样本/1.000000052秒稳定）、2步取得实际数据、60步关闭观察；共662步，30次OFF机会/30次quiet、在途0。块末再次检查OFF/保持/健康后才提交authority，尾部额外保持10步、5次正常render后，块末`off_confirmation`记录为35次机会/35次quiet（与首次确认30/30为不同时间的快照）。每份RGBA为640×480 uint8；成功由实际fresh数据及独立OFF等原条件决定，不以PNG内容不同代验。

| robot/task/claim | 开始tick | ON tick | fresh接收tick / source frame | SUCCEEDED_OFF / 块末退役tick | 原始PNG（本机） |
|---|---:|---:|---|---|---|
| 0 / 0 / 0 | 0 | 600 | 602 / 537 | 662 / 672 | [R0 T0](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/robot_0/task_0/claim_0/camera_rgba.png) |
| 1 / 2 / 0 | 0 | 600 | 602 / 537 | 662 / 672 | [R1 T2](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/robot_1/task_2/claim_0/camera_rgba.png) |
| 0 / 1 / 1 | 672 | 1272 | 1274 / 873 | 1334 / 1344 | [R0 T1](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/robot_0/task_1/claim_1/camera_rgba.png) |
| 1 / 3 / 2 | 744 | 1344 | 1346 / 909 | 1406 / 1416 | [R1 T3](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/robot_1/task_3/claim_2/camera_rgba.png) |

产品分别 `/Render/OmniverseKit/HydraTextures/CR12_R0_Capture`、`CR12_R1_Capture`，挂到各自 `/World/CR12_0|1/link_6/SingleViewCamera`。前两次source frame都537合法：同一渲染时间线下不同product产生各自数据，身份还包括product/Camera/robot/task/claim及本次ON来源，不能只用全局frame号判断串台。每台同Camera/product连续两次请求，prepare/initialize各一次、ON/OFF各两次、有效release各一次；原始custody保留至receipt，逻辑rebuild不反写已取得的数据。

关键隔离片段为 **global tick1274 / render637**：R1产品`updates_enabled=false`，完成事件数1→1；R0从启用状态收到自己的source frame873，完成数1→2并转入关闭。该片段来自同一次正常render的before/after及本次来源事件，未增加渲染或改错峰。A/B表示OFF/fresh角色，此处A=R1、B=R0。阶段区间还包含673–744的MOVING_OFF/IDLE_HOLD、1272–1333的WAITING_DATA或CAPTURE_CLOSING/MOVING_OFF及1345以后的IDLE_HOLD/采集关闭。实际重叠1128tick支持并行，不是串行代验。

### 6.2 守卫、authority与终态

E1/M2/N4、Y2m、dt1/120、render interval2、decimation12、原资产/PD/solver/external-forces-on及全部guard保持。两台各六类guard各1416次通过。cross geometry总4249次：初始1、实际1416、命令中点/终点2832；每次覆盖100个逻辑cross pair，424900次逻辑pair覆盖。整机AABB始终分离，最小分离下界1.135999748m，因此细分pair执行0是合法coarse early-out，**不写成424900次精细OBB检查**。self/contact及状态/frame/clock守卫按原判据通过；不推广为任意障碍规划或全工作空间安全。

同批多binding、块末118次全域事务、4个authority交付及receipt后退役；共同terminal前四任务完成、两机累计[2,2]。actor维度145、critic/真实terminal sidecar143；历史行/ACK各一，安全逻辑rebuild后新episode状态重建。rebuild前后native clock都是1418 / 11.816667282953858秒，机器人q/dq/q_cmd/scanner保持，不以teleport重置机器人冒充continuation。有效生命周期内两机最终native参数一致性检查通过，在stop前各释放一次相机资源。

### 6.3 预算、退出与警告

监督时间 **22:14:17.115→22:17:39.785 +08:00**，单调时钟全树202.672秒≤480；App构造26.438秒≤180。Kit自身`app ready`日志不是目标AppLauncher返回时间，构造预算采用监督阶段标记。运行118 transitions≤420，受控1416 physics≤5040、708 normal render≤2520，初始化2步，总1418≤5042；受控模拟时间11.800000615秒。每请求662≤1800（pose600≤960/capture2≤600/close60≤240）；新请求保留原1812tick准入余量，capture/close墙钟未超60/30秒。没有重置监督起点或额外UI/物理采样步。

目标和Conda均exit0，supervisor本身exit0；`all_owned_processes_exited=true`、remaining PIDs=[]、无timeout/termination_requested/native_fault/supervisor_errors。工作完成、simulation_stop返回、app_close_begin与进程退出共同成立。原`result.json`保留正常的 **WORK_COMPLETED_PENDING_PROCESS_EXIT**，退出由监督器最终确认，未伪造改写为另一个终态。

console仍有扩展/默认setting、TLAS limit `within:false`（5228–5229）、两相机`xformOp:transform`（7016/7018）、DLSS/host-copy（7070/7071）、Hydra接口已释放及退出removePath（7154）等warning；它们没有伴随本次failure字段、native故障或完整谓词失败，不把日志表述为“无任何warning”，也不在本任务顺手修改业务/installed files。源事件、窗口、物理、相机/authority结果和自然退出是本次PASS依据，warning不构成新的任意场景或长期稳定性保证。

## 7. 本次能下的结论、未知项与停止点

用户已确认的是先前实现/CPU和启动FAIL分类可保留、单机接受基线及Phase B关闭；**本轮runtime PASS来自上述新原始运行证据，审阅尚待GPT/用户**。当前代码事实是只加启动候选/默认关闭观测，双机业务及原完整验收未变。

S1/S2/F与本轮private启动字节、监督创建机制、experience及原window/renderer请求相同；本轮明确差异为两项DPI行为组和只读观测/日志核对。当前一次成功支持将该组作为**已跑通一次的局部候选**保留使用，但不能证明它是必要条件、唯一修复或今后永不复发。历史目标进程桌面/DPI/STARTUPINFO、native内部派生与创建瞬间composed值仍UNKNOWN，观测时序和未控制桌面因素尚未排除。本轮没有A/B重复实验，也没有全局推广候选。

完整冻结双机case现已跑通，没有新暴露的阻断性双机缺口需要本轮修补；无需为追唯一native根因继续占用App。建议停止窗口诊断，先审阅本次固定双机结果，再另行决定研究下一步。共享任务竞争/跨机转交 **NOT_ESTABLISHED**；动态重分配、取消/关闭失败的双机恢复、任意轨迹/真实构件、标定、depth/pointcloud、可变规模策略和学习性能都不由本次PASS代验。固定区域allowlist与非物理fixture仍是本case范围；不重开单机人工观看、公共event、Phase B、训练或checkpoint。

## 8. 文档变更与辅助证据对应表

本轮只新增这一份Markdown主报告，小范围更新 `AgentRead/TASK_PROGRESS.md` 和 `REPORT_INDEX.md`；历史S1/S2/F、旧report/helper/attempt均保持。没有把Python/JSON放入报告日期目录，没有新ZIP、视频、全环境dump或全仓库存。实现/测试/一次性脚本分别按第4节放E/Q/L。所有 `logs/` 证据受既有Git忽略规则影响，当前仅本机可取，不保证新checkout自动包含；未改忽略规则或提交证据。

| 结论/检查项 | 文件位置 | 关键字段/定位 | 用途 |
|---|---|---|---|
| 三次历史输入比较 | [比较摘要](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/evidence_comparison.json)、[比较器](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/compare_startup_inputs.py) | S1/S2/F command、pre-popen/private after、typed diff、进程创建AST | 不把after文件当startup输入 |
| 本轮局部接线/CPU | [patch](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/shared_gui_startup.patch)、[CPU记录](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/gui_startup_cpu_checks.txt)、[preflight](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/preflight.json) | 默认关闭、原dirty AST、36项分层与31输入 | 不重计旧202项 |
| 实际监督及命令 | [supervisor](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/supervise_cr12_dual_gui_startup.py)、[command](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/command.json) | main/budget/完整旧completion_checks及唯一App | 180/480s、冻结case，现额度耗尽 |
| 配置保护 | [准备摘要](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/source_private_config_summary.json)、[运行前后摘要](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/config_runtime_summary.json) | source_unchanged、typed diff、private写回 | 不在正文复制完整个人配置 |
| native窗口/后端/首因 | [console](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/console.log)、[同次Kit](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/kit_20261008_221420.log) | console3354、2700/3529、11–18 | 1440×900、D3D12、真实参数顺序及warning |
| 上下文及完整双机事实 | [result](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/result.json) | gui_startup_diagnostics、requests、parallel_evidence、terminal、native | 只读采样与四份实际数据分开；四PNG见第6节 |
| 六层与最终退出 | [supervisor_result](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/supervisor_result.json) | startup_layers、completion_checks、classification、exit、budget_after | 完成记录加自然退出，不只看exit0 |

收尾只读检查：相关31代码输入运行前后相同，HEAD仍a8c618a32da65747827f1cb3f722fac24df2aec8；Git索引无暂存路径，既有dirty双机修改保留。文档新增链接作本轮范围核对，不扫描旧归档链接。未改资产、依赖、系统/共享配置或用户环境变量；未执行Git add/commit/push/reset/restore等写操作。**已停止，等待GPT/用户审阅；不启动第二App，不自动进入共享任务转交、训练、提交或历史清理。**

