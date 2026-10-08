# CR12 manual GUI 120×0 swapchain 定向诊断与重试条件报告

日期：2026-09-30，Asia/Shanghai（UTC+08:00），本轮20:57起执行。仓库 `E:\Project\IsaacLab_HARL`；HEAD `24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。

## 1. 执行结论

**定向诊断完成；未实施启动修复，新增 App 为 0/1。** 用户限定“没有明确修复依据，不启动App”；当前证据尚未满足这一运行前提，因此没有消耗唯一重试额度。

已确认两次运行均请求 **window 1440×900、renderer 1280×720**，实际后端均为 **D3D12/DX12**。失败的 **120×0 首次出现在 omni.appwindow 创建原生窗口时**，早于项目 scene、target、marker、spectator 和控制器。

当前同一路径 `user.config.json` 保存 `/persistent/app/window/width=-1`、`height=-1`、`maximized=true`，mtime为 **17:03:37 +08:00**，介于formal成功与manual失败之间。这是值得验证的上游窗口状态候选，**不是已确认根因**。没有发现窗口尺寸 authored height=0；**最后的native派生步骤UNKNOWN**，−1的sentinel语义、持久与CLI尺寸的最终选择关系、120及0的具体计算来源仍未证实。

重复传入已存在的1440×900不能作为“已定位修复”。本轮未改生产代码/测试/启动脚本/资产/installed packages或任何持久配置，未启动Isaac、Kit、CUDA或仿真。完成现有31+21项CPU回归、报告和小范围交接更新后停止。

formal single-target pose与basic joint drive保持 **GPT REVIEW PASS**；Phase B保持 **COMPLETE / GPT REVIEW PASS / CLOSED**。不自行声明新的GPT REVIEW PASS。

## 2. formal成功与manual失败的启动对照

定义：**A**为 `logs/scan_assignment/20260930_cr12_pose_target/attempt_01/`；**B**为 `logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/`。当前配置文件是本轮读取的现存文件，不能当成两次运行各自的完整历史快照。

| 项目 | A formal成功 | B manual失败 | 判断 |
|---|---|---|---|
| 本地运行时间 | 16:11:52.233–16:12:55.715 +08 | 17:24:13.695–17:24:36.857 +08 | 不同；Kit正文08:xx/09:xx对应本地16:xx/17:xx |
| 外层命令 | formal supervisor | manual supervisor；外层另有no-capture-output | 不同，完整命令见下文 |
| 实际Python | `C:\isaacenvs\isaac45_harl\python.exe` | 相同 | 日志直接确认相同 |
| cwd、HEAD | 当前仓库、`24ecbad…` | 相同 | 相同；不能据相同HEAD推断dirty源码功能版本相同 |
| 已记录环境 | PYTHONUTF8=1；HEADLESS/ENABLE_CAMERAS/LIVESTREAM/XR=0 | 相同 | command.json覆盖相同；实际UTF8=1 |
| 历史DISPLAY/桌面状态 | 未记录 | 未记录 | **UNKNOWN**，不以当前进程补齐 |
| AppLauncher/project CLI | GUI/cuda:0；960；formal默认、visual关闭、overall | GUI/cuda:0；1200；manual显式、visual开、wrist-oblique、baseline显式 | 功能参数不同；项目CLI均未新增window/renderer尺寸 |
| kit_args | 原为空；追加 `--/app/vulkan=false` | 相同 | 相同 |
| experience | `E:\Project\IsaacLab_HARL\apps\isaaclab.python.kit` | 相同 | 相同 |
| D3D12来源 | helper的windows_default；日志DX12/D3D12 | 相同 | 请求与实际后端均有证据 |
| window请求CLI | `--/app/window/width=1440 --/app/window/height=900` | 相同 | 相同 |
| renderer请求CLI | `--/app/renderer/resolution/width=1280 …/height=720` | 相同 | 相同 |
| viewport/UI请求 | `/persistent/app/viewport/displayOptions=3094`、hideUi=False | 相同 | 同次Kit argv确认 |
| user config路径 | `…/omni/data/Kit/Isaac-Sim/4.5/user.config.json` | 相同 | 路径相同；历史内容是否相同 **UNKNOWN** |
| portable配置 | `--portable`；root为环境Lib/site-packages/omni | 相同 | 相同 |
| shared user.toml等 | Non-existent configs记录不存在 | 相同 | 两次未加载；当前shared user.toml亦不存在 |
| 初始settings来源 | kit-core.json、仓库experience、上述user.config；随后extension defaults | 相同路径/版本 | 同路径不能证明同内容或最终composed状态 |
| spectator/view时机 | App创建后、场景初始化后 | 源码亦如此，本次未到达 | 没有项目spectator的pre-App窗口写入 |
| manual/visual pre-App差异 | 当时无manual profile；visual参数只记录 | CPU profile选择/步数验证/标签；未调用visual API | 有CPU解析/导入差异，未发现窗口setting写入 |
| supervisor argv/env | 拷贝父env、合并5个mode项；CREATE_SUSPENDED→Job→resume | 相同机制，多manual参数 | 未增加尺寸/DPI/renderer覆盖或隐藏/最小化startupinfo |
| native窗口 | **1440×900** | **120×0** | 关键直接差异 |
| 结果 | app_ready、600步、自然exit0 | app_ready之前native异常、0步 | 失败阶段不同于控制/marker层 |

两次日志均记录Isaac Sim4.5.0、Kit106.5.0+release.162521.d02c707b.gl、驱动610.60。本轮没有驱动归因、版本迁移或重做Windows资格验证。

### 2.1 历史完整命令（本轮未执行）

cwd均为 `E:\Project\IsaacLab_HARL`。A外层依据正式主报告第5节，B外层依据上轮实际执行记录；子命令以各自command.json为准。未保存全量外层父环境，不补齐未知项。

A外层：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20260930_cr12_pose_target/repro/supervise_cr12_pose.py --attempt-dir logs/scan_assignment/20260930_cr12_pose_target/attempt_01
~~~

A实际子命令：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_pose_target.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20260930_cr12_pose_target\attempt_01' --device cuda:0 --physics_steps 960 --external-forces-every-iteration on --info
~~~

B外层：

~~~powershell
$env:PYTHONUTF8 = '1'
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20260930_cr12_manual_visual_motion/repro/supervise_cr12_manual_visual.py --attempt-dir logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01
~~~

B实际子命令：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_pose_target.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20260930_cr12_manual_visual_motion\attempt_01' --device cuda:0 --physics_steps 1200 --motion-profile manual_visible_local_v1 --visual-debug-pose --view-preset wrist-oblique --pd-profile baseline --external-forces-every-iteration on --info
~~~

## 3. 1440×900及1280×720的可确认来源

本机安装文件：

`C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\exts\isaacsim.simulation_app\isaacsim\simulation_app\simulation_app.py`

- `DEFAULT_LAUNCHER_CONFIG:57`、`:65–68`：renderer/viewport1280×720、window1440×900。
- `__init__:183–195`：建立config，应用传入launch_config。
- `_start_app:316–319`：分别生成renderer与window尺寸CLI。
- `:344–348`：未指定portable-root时追加portable；`:424–427`：打印argv、追加unknown_args、调用Kit startup。

仓库 `source/isaaclab/isaaclab/app/app_launcher.py:378–381` 接受配置字段 `width/height/window_width/window_height`（int），`:472–474` 过滤后传给SimulationApp，`:780` 构造App。**当前CR12 argparse没有注册window_width/window_height用户CLI**，不能将可传构造参数说成现成CLI。已有 `--kit_args` 在 `:754–760` 用空格split追加至sys.argv。

`_windows_runtime_startup.prepare_windows_runtime_args:57` 只处理UTF8/后端及来源，未写窗口、viewport、renderer尺寸。`run_cr12_pose_target.py:478–489` 保持参数准备 → 原 `view_scan_assignment._prepare_cuda_before_app:51` → AppLauncher的顺序。

A/B最终Kit argv中已经有同一组合法尺寸，因此没有找到“漏传尺寸”或“renderer请求0”。重复相同CLI即使碰巧成功也不足以证明修复因果。

## 4. 120×0的最深定位

### 4.1 同次失败时间链

| B原始证据 | 事实 |
|---|---|
| Kit:2682，918ms | DX12已选定 |
| console:3385–3390，1595–1597ms | omni.appwindow1.1.9 native插件启动 |
| **Kit:3357，1794ms** | **Created window: width=120,height=0** |
| console:3457，1855ms | omni.kit.mainwindow开始启动，晚于120×0 |
| console:4032，2770ms | omni.kit.viewport.window开始启动 |
| Kit:3925–3927，2796ms | Direct3D invalid desc → swapchain120×0 → graphics初始化失败 |
| console:4047 | Windows fatal exception: access violation |

swapchain的非法尺寸与较早的native app window日志一致。mainwindow docking及viewport创建晚于首条120×0，不能把后续报错栈的viewport行当成最早尺寸来源。安装的 `omni.kit.viewport.window…/window.py:75` 是 `super().__init__`；这是Python栈落点，不是证明它计算了120或0。

项目 `_run_pose` 未调用，root/target/native Jacobian/marker/view/DiffIK/joint command/contact/geometry/frame guard均未发生，不归因这些模块或robot USD。

### 4.2 native接口、可读源码与未知边界

`C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\dev\include\omni\kit\IAppWindow.h`：

- `:24–29` 区分app/window的width,height,maximized与对应persistent字段。
- `WindowDesc:103–115` 包含尺寸、scaling、windowState。
- `getDefaultWindowDesc:123–139` 默认1440×900、normal、scale-to-monitor。
- `createWindowPtrFromSettings` 为原生虚接口声明，未提供内部尺寸选择实现。

安装扩展 `isaacsim/extscache/omni.appwindow-1.1.9+d02c707b.wx64.r.cp310/config/extension.toml:23–35` 默认1440×900、maximized=false、scaleToMonitor=true、saveSizeOnExit=true；`docs/SETTINGS.md:53–67` 说明persistent字段为上次保存的尺寸/最大化状态。

本轮有限读取该146,968字节DLL的ASCII setting字符串，确认名称存在；**字符串不能证明分支、优先级或转换**。没有执行DLL、安装工具或反编译整个Kit。

**最后的native派生步骤UNKNOWN。** 最深范围是：合法CLI请求 → native设置选择/WindowDesc/Windows窗口创建 → 返回120×0。120与0各自的计算来源仍未知，不能将相似的viewport tickRate=120或layout margin=0牵强解释成窗口像素来源。

## 5. 当前持久配置与显示信息

### 5.1 当前配置读取结果

A/B的 `Applied configs` 都列出：

1. `…/omni/kernel/config/kit-core.json`；
2. `E:\Project\IsaacLab_HARL\apps\isaaclab.python.kit`；
3. `…/omni/data/Kit/Isaac-Sim/4.5/user.config.json`。

之后还有extension defaults应用；缺少失败时完整composed settings读回，不能重建native使用的最终字段优先级。

当前第三个文件114,100字节，mtime **2026-09-30 17:03:37 +08:00**。只读取/抽取窗口相关字段，未复制完整个人配置。

| 当前setting | authored值 | 意义与限制 |
|---|---|---|
| `/persistent/app/window/width`，文件:449 | **−1** | 非正保存尺寸；native是否将其作为sentinel、是否回退UNKNOWN |
| `/persistent/app/window/height`，:450 | **−1** | 不是直接authored0 |
| `/persistent/app/window/maximized`，:448 | **true** | 保存的最大化状态；不是失败时actual状态读回 |
| `/persistent/app/viewport/Viewport/Viewport0/resolution/0,1`，:2686起 | 1280、720 | 保存的viewport分辨率非零 |
| `/persistent/app/viewport/outline/width` | 2 | 轮廓线宽，不是app window宽度 |

当前JSON根只有persistent，没有额外app/window/height=0。experience `:183–186` 只设置window icon/title，`:193–194` renderer为720/1280；kernel `app/userConfigPath:121` 指向data目录下user.config.json。mainwindow扩展的margin.height=0是UI边距，不是窗口尺寸。

A native窗口1440×900（Kit:3360）；B为120×0（:3357）。配置mtime位于其间；已知用户wrist人工目录 `20260930_cr12_pose_target/manual_20260930_170257_546` 的result/CSV mtime为17:03:36，与配置写盘相邻。**仅支持时间关联，不证明该运行写入了−1，不证明保存逻辑有错，也不解释A为何正常。** 没有A当时配置内容快照或B启动时JSON字段快照，不能补写历史值。

shared `C:\Users\33506\Documents\Kit\shared\user.toml` 当前不存在，A/B的Non-existent configs也记录不存在。未创建、修改或假定其生效。

### 5.2 有依据的有限桌面检查

本地设置明确依赖scaleToMonitor/DPI/Windows状态，因此执行一次Win32只读CPU查询；未改变DPI awareness、系统缩放/分辨率/注册表/显示器配置，未创建测试窗口或GPU context。

2026-09-30 **21:01:35 +08** 的当前进程结果：

- 主显示器rect=(0,0,2560,1440)，work rect=(0,0,2560,1392)。
- 次显示器rect=(−1920,356,0,1436)，work rect=(−1920,356,0,1388)。
- SM_REMOTESESSION=0，SESSIONNAME=Console；DISPLAY/WAYLAND_DISPLAY未设置。
- 当前进程 `GetDpiForSystem` 返回96；没有把它当成物理显示器真实缩放或历史Kit DPI。
- 当前CPU Python STARTUPINFO flags=0；不能推定失败进程当时flags。
- 两个旧supervisor的Popen都只加CREATE_SUSPENDED、Job归属与resume，没有显式隐藏/最小化startupinfo。

当前工作区非零；**失败时**是否显示器变化、RDP/锁屏或窗口最小化/隐藏仍UNKNOWN。未枚举其他应用窗口或导出完整环境变量。

## 6. 实际修复决定与单因素边界

| 落点 | 证据 | 本轮决定 |
|---|---|---|
| 项目CLI / SimulationApp字段 | window_width,height受支持，但最终argv本来已有1440×900 | 不新增重复参数包装并称其为修复 |
| Kit参数层 | app/window/width,height名称确认；CLI与persistent最终选择未解 | 不无依据地重复覆盖后试跑 |
| 项目局部helper | 未找到可读证据确认只绕过可疑保存尺寸的非持久分支/开关 | 不建立猜测性helper或通用诊断框架 |
| 写persistent字段、删/重建user.config、改共享配置 | 超出本轮全局/持久设置边界；因果仍未证实 | 不执行 |
| DPI/driver/Vulkan/renderer/viewport/control变更 | 无直接支持，且不在修复范围 | 不执行 |

**实际最小修复：无。** 未同时改window、renderer、viewport，未换空用户配置。renderer保持原值，experience、Windows helper、installed源码、shared user.toml与所有persistent值均未改。

因为没有新增窗口参数逻辑，height=0/negative拒绝、用户显式值不重复覆盖等“新逻辑测试”不适用；没有为形式增加helper或测试。未将一个可疑字段提升成满足运行授权的明确修复。

## 7. CPU检查与冻结保护

先核对解释器 `C:\isaacenvs\isaac45_harl\python.exe`，UTF8=1。本轮实际命令（cwd仓库根）：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_pose_control.py
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_manual_visual.py
~~~

| 检查 | 结果 |
|---|---|
| 原formal CPU套件 | **31/31 PASS**，1.763秒 |
| 原manual CPU套件 | **21/21 PASS**，.664秒 |
| 原始argv/env/config/窗口日志对照 | 完成，逐项区分相同、不同、UNKNOWN |
| pre-App调用顺序 | profile仅CPU；visual/target均App后；未发现新增窗口写入 |
| 修改Python的py_compile | **不适用：没有Python文件变更** |
| Windows helper额外测试 | 未改helper，不重做既有Windows资格验证 |
| 新App/physics/render/CUDA | **0 / 0 / 0 / 无** |

入口、control、visuals、runtime_support、Windows helper均未由本轮修改，作了有限内容/mtime核对而非全仓哈希。formal的target/controller/Jacobian/COM/guard/4s/8s/960/容差/分类保持；manual的witness=(0,3,−4.5,0,4.5,0)°、beta=1、目标算法、6s/10s/1200、marker尺寸颜色、view presets、controller/guard保持。资产、PD、solver、dt不改。

交付核对：上述5个源码文件在文档整理前后内容摘要5/5一致；user.config仍为114,100字节、mtime17:03:37.6226958，未被本轮改写；新报告相对链接及5个历史/CPU命令块的PowerShell语法检查通过（parse-only，未执行runtime命令）。Git索引仍仅有原先已暂存的历史ZIP删除，没有本轮Git写操作；新任务目录没有attempt_01。

一次只读PowerShell查询因foreach管道语法被拒绝，改为先收集数组后完成；一次报告字符串生成因模板变量未转义失败，未写入文件，改正文表达后完成。均不是runtime故障，没有为此创建App或修改依赖。

## 8. 唯一新App、三层结果与人工查看

**本轮实际新runtime命令：无。** 未满足明确局部修复的前提，没有新attempt_01、command.json、result.json或supervisor结果，不伪造“重试失败”。

| 层级 | 本轮 | 上轮B的准确事实 |
|---|---|---|
| Level1 GUI | **NOT_RUN** | FAIL；app_ready前；D3D12、swapchain120×0、native0xC0000005 |
| Level2 scene/target/view/marker | **NOT_RUN** | NOT_REACHED；不能把缺失visual_errors当[] |
| Level3 manual motion | **NOT_RUN** | 0受控步、MANUAL MOTION NOT_RUN |
| App额度 | **0/1** | 上轮独立任务1次，原记录不回写 |
| 退出/超时/owned tree | 无本轮runtime进程/退出码 | 上轮23.156秒、目标3221225477、Conda4294967295；全树退出，无超时/强杀 |

**当前尚不能建议用户重新人工运行。** 没有新的GUI PASS + marker setup/readback PASS，因此遵守本轮第16节，不再复制两条未获运行通过的人工命令。旧报告的命令保留原文，本轮不执行、不改写、不提升为已验证可用。

## 9. 下一步与审阅事项

下一步只需补足“saved window state是否覆盖合法CLI并生成非法native尺寸”的证据：优先寻找已有同次窗口设置provenance或对应native实现说明，不重新制造Vulkan崩溃，不复验formal pose/controller。

若后续考虑**任务私有user config对照**，应先审阅精确范围与写回行为：其余设置保持一致，仅处理saved window width/height，复用1440×900，明确是否保留maximized状态并防止写回原配置。这是**待审调查方案，未创建私有副本、未实施、未获本轮额外运行授权**；不能用换整份空配置、同时改renderer/viewport/DPI来冒充单因素。当前也不能声称只有全局修改才能解决。

formal/basic drive既有GPT REVIEW PASS与上轮STATIC / CPU IMPLEMENTATION PASS保留；manual RUNTIME SMOKE FAIL / CONTROLLED STEPS=0 / MARKER=NOT_REACHED / MANUAL MOTION=NOT_RUN保留。

**manual-visible profile仅用于人工观察运动连续性和marker显示，不扩展正式单目标验收范围。**

**源OBJ由用户确认正常；仿真显示几何存在差异，原因待查。** 未修mesh、未加camera/构件、未做双视点/MRTA/训练。本轮交付后停止，等待GPT/用户审阅，不自动增加App、修改持久设置或写Git。

## 10. 文档变更与辅助证据对应表

新增本报告；小范围更新 [TASK_PROGRESS](../../TASK_PROGRESS.md)、[REPORT_INDEX](../../REPORT_INDEX.md)。只在 `logs/scan_assignment/20260930_cr12_manual_gui_retry/repro/` 新增两个证据文件，无代码patch（没有代码变化）、新runtime日志或fake attempt。旧formal/manual目录、旧报告、既有dirty工作区与暂存删除保留，未执行Git写操作。

`logs/` 证据受现有忽略规则影响，**目前仅在本机，不保证新checkout包含**。没有ZIP、ledger、全系统诊断包、图像序列、全仓hash或重复日志副本。

| 结论/检查项 | 文件位置 | 关键定位 | 用途/限制 |
|---|---|---|---|
| 本轮配置来源/差异 | [startup_comparison.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_gui_retry/repro/startup_comparison.json) | runs/current_config/current_display_read_only/unknowns/decision | 小型setting摘要与原日志摘录，不是运行结果 |
| 本轮52项CPU | [cpu_checks.txt](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_gui_retry/repro/cpu_checks.txt) | 两条命令及31/21输出 | 仅CPU逻辑回归 |
| A参数/配置/窗口 | [command.json](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/command.json)、[console.log](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/console.log)、[Kit log](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/kit_20260930_161156.log) | console10–19；Kit3360/3572 | 请求与实际1440×900/D3D12 |
| A正式结果 | [result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/result.json)、[supervisor_result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_pose_target/attempt_01/supervisor_result.json) | pose_summary、validation_pass、exit | 既有接受依据，不重跑 |
| B参数/最早异常 | [command.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/command.json)、[console.log](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/console.log)、[Kit log](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/kit_20260930_172417.log) | console11–20/3398/4039–4047；Kit3357/3925–3927 | native120×0首现及swapchain |
| B退出与未进入阶段 | [supervisor_result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/supervisor_result.json)、[runtime_failure_summary.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/runtime_failure_summary.json)、[result.json](../../../../../../../../logs/scan_assignment/20260930_cr12_manual_visual_motion/attempt_01/result.json) | 完整失败口径；result为fatal前RUNNING快照 | 缺失marker字段不能当PASS |
| 原实现及边界 | [manual报告](CR12_MANUAL_VISUAL_MOTION_AND_MARKER_REPORT.md)、[formal报告](CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md) | 上轮实现/CPU/正式结果 | 保留历史原文 |

