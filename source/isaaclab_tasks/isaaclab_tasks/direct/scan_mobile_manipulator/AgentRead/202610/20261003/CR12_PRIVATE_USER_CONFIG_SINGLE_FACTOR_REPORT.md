# CR12 task-private user.config 单因素验证报告

执行日期：2026-10-03，Asia/Shanghai（UTC+08:00）。本任务于9月30日完成部分准备，10月3日收到“请继续”后续做；中断前没有启动本轮App。报告按实际运行日期归档，旧准备文件保留原位。

仓库：`E:\Project\IsaacLab_HARL`；HEAD：`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`。本文以仓库根为路径基准；`T` 指 `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator`；`A` 指 `logs/scan_assignment/20261003_cr12_private_user_config/attempt_01`。

## 1. 执行结果与边界

**唯一App已执行，L0配置隔离、L1 GUI、L2场景/marker、L3 manual motion均PASS。结果为 MANUAL_VISUAL_RUNTIME_SMOKE_PASS；不是新的formal acceptance，也不自行写GPT REVIEW PASS。**

本次实际加载task-private配置，native窗口为 **1440×900**，未重现历史120×0。实际后端D3D12，进入CR12场景与marker，完成 **840受控步 / 7.000000365秒**，121点稳定1.000000052秒，全部所属进程自然退出。原source配置的大小、mtime和SHA256均未改变。

| 层级 | 结论 | 本次直接证据 |
|---|---|---|
| L0 配置隔离 | PASS | 运行前恰好三项semantic diff；最终Kit argv及实际加载均指向private；source前后不变 |
| L1 GUI/App | PASS | Created window 1440×900、AppLauncher返回app_ready、实际D3D12、420次受控render、无swapchain失败/原生崩溃、目标自然exit0 |
| L2 场景/marker | PASS | CR12及manual target构造，arm-oblique；实际9 prototypes/9 instances读回，visual_errors=[] |
| L3 manual motion | PASS | 840步，原六类guard各840 PASS，数值完成及自然退出 |
| 人工视觉验收 | **尚未完成** | 允许重新建议按private配置方式人工查看；不能由读回代替人眼确认 |

历史formal single-target pose与basic joint drive保持用户确认的 **GPT REVIEW PASS**；Phase B保持 **COMPLETE / GPT REVIEW PASS / CLOSED**。历史manual启动FAIL没有回写。

## 2. 为什么采用private配置，以及历史对照限制

9月30日历史manual运行在D3D12下请求window1440×900、renderer1280×720，却实际创建120×0，随后swapchain失败和0xC0000005，0受控步、marker NOT_REACHED。前一轮定向诊断没有找到可直接认定的根因，因此未启动新App。

此次用户单独授权：复制当前真实user.config，只改变保存窗口状态这组三个值，真实source只读；直接测试现有manual路径，不修改生产入口、控制器、目标或marker。1440×900来自本地SimulationApp默认与历史formal成功尺寸；maximized=false用于避开已保存最大化状态。本轮没有单独区分三个字段各自的作用。

| 对照项 | 历史manual失败（2026-09-30） | 本轮（2026-10-03） |
|---|---|---|
| 配置路径 | 环境默认source | 显式task-private副本 |
| 启动时三字段 | 历史完整快照缺失；之后读取为−1/−1/true | 运行前保存证据1440/900/false |
| native窗口 | 120×0 | 1440×900 |
| 后端 | D3D12 | D3D12 |
| manual/profile、机器人/控制 | 同一manual实现/v1/baseline/explicit-on | 保持冻结 |
| view preset | wrist-oblique | 用户要求的arm-oblique |
| 结果 | app_ready前原生失败、0步 | app_ready、marker、840步、自然exit0 |

view设置位于App创建和机器人初始化之后，不解释此前窗口创建阶段的120×0；但本轮与历史运行日期、目录和view参数不同，且没有同期A/B重复实验。不能把本次通过写成严格排除所有外部因素的唯一根因证明。

## 3. source、private与三项语义差异

真实source并非根据附件路径猜测：历史manual `console.log:13` 的Loading user config、同次 `kit_20260930_172417.log:5` 的Applied configs均指向该文件；当前本地 `omni/kernel/config/kit-core.json:121` 定义app/userConfigPath默认位置，文件存在并可解析。

**source canonical path：**

`C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\user.config.json`

- 114100 bytes；mtime **2026-09-30 17:03:37.6226958 +08:00**。
- SHA256：`9b3b72015f7e8ca7a74ad179a81329bc3f00966862dd0ce8f831831a12dea625`。
- JSON根为persistent；app/window仅有uiStyle、maximized、width、height。uiStyle=NvidiaDark保持不变，没有额外saved-state字段。
- JSON解析拒绝重复key和非标准NaN/Infinity；三个值也严格检查类型。

**private canonical path：**

`E:\Project\IsaacLab_HARL\logs\scan_assignment\20261003_cr12_private_user_config\attempt_01\private_config\user.config.json`

| setting | source / byte-copy | private运行前 |
|---|---:|---:|
| /persistent/app/window/width | −1（int） | 1440（int） |
| /persistent/app/window/height | −1（int） | 900（int） |
| /persistent/app/window/maximized | true（bool） | false（bool） |

准备顺序是source只读快照 → 新文件独占byte-copy → 字节/hash核对 → 解析副本 → 三项修改 → 序列化 → 完整递归semantic diff。不是字符串替换。结果 **diff_count=3、all_other_values_equal=true**；bool与int不会因Python的True==1而混淆。

运行前private为 **84107 bytes**，mtime **2026-10-03 21:30:03.458336 +08:00**，SHA256：

`8bfc571cb3a4501897f2b2bf9f4a40e53862d5eadca77326c91bd32013f70468`

大小改变来自JSON格式化，全部其他逻辑值相等。renderer请求保持1280×720；persistent viewport resolution也保持1280×720。未改变scaleToMonitor、saveSizeOnExit、docking/layout、viewport、backend或其他值。完整个人配置仅存在用户授权的private副本，不复制进本报告或摘要。

### 3.1 原配置保护及private写回

监督器在 **21:36:41.691 +08:00**、唯一子进程启动前再次读取source/private，并与准备记录逐项比较；进程退出后在 **21:37:32.748 +08:00** 记录结果。

| 文件 | 前后结果 |
|---|---|
| source | size114100、mtime、SHA256全部相同；semantic diff=0；SOURCE_CONFIG_CHANGED_DURING_RUN未触发 |
| private | size84107→114104；mtime改为21:37:29.496100 +08；hash改变；**semantic diff=0** |
| private三个值 | 运行后仍1440/900/false；其他setting也无语义变化 |

private运行后SHA256：`3544a9c7dfb61891df3ba92bd7970288affae1301a8f651524efd9e9810d495d`。这是本次Kit持久化写回的字节/格式变化，不能误报为运行前第四项输入差异。因果分析使用保存的运行前快照；运行后文件作为输出单列。

没有写入、rename、删除、chmod、设只读、替换或恢复source；未改shared user.toml。没有以“保护”为名改变系统行为。

## 4. 实际传参链与实现变更

**生产代码、测试、资产及安装包均未修改。** 仅新增两个任务repro文件和private输入/必要证据：

| 文件/符号 | 本轮用途 |
|---|---|
| `repro/prepare_private_user_config.py`：snapshot:95、validate_three_changes:113、prepare:124 | 只读source；独占创建新副本；严格三diff；CLI只输出private路径；不启动App |
| `repro/supervise_cr12_private_user_config.py`：build_command:70、verify_pre_popen:99、post_config_summary:149、supervise:520 | 复用Windows Job、实时排空与180/360秒预算；只允许attempt_01，无重试；前后配置证据与L0–L3判定 |
| 上述监督器console_evidence:368、copy_same_run_kit_log:414 | 保存最终Kit argv及实际加载/native窗口；仅复制本次明确报告的Kit路径，禁止latest-log扫描 |

两个文件位于 `logs/scan_assignment/20261003_cr12_private_user_config/repro/`，不在AgentRead。9月30日中断前生成的同任务helper和CPU检查记录保留原位；10月3日helper为字节一致副本。本轮无需生产patch。

本地源码依据：

- `scripts/environments/run_cr12_pose_target.py:28`：使用AppLauncher参数注册；`:478–489` 保持Windows helper → 原pre-App CUDA准备 → AppLauncher创建顺序。
- `scripts/environments/_windows_runtime_startup.py:57,109–115`：保留已有kit_args，将缺省D3D12追加为` --/app/vulkan=false`；不改变private路径。
- `source/isaaclab/isaaclab/app/app_launcher.py:332–338,754–760`：接收`--kit_args`，普通空格split后传入sys.argv。
- 本机 `C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\exts\isaacsim.simulation_app\isaacsim\simulation_app\simulation_app.py:57–68,316–319,347–348,424–427`：默认renderer/window尺寸，追加`--portable`，再追加unknown_args并调用Kit startup。
- 历史后端交接ZIP中的D3D12 GUI脚本使用userConfigPath并成功，但没有明确portable组合证据；**本轮实际加载日志补充证明此次组合可用**，不追溯扩大历史结果。

传入子进程的是一个无空格、绝对forward-slash路径参数：

~~~text
--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/private_config/user.config.json
~~~

helper之后的Kit tokens恰好为private路径及`--/app/vulkan=false`；没有第二个kit_args或裸backend参数。forward slash用于简单明确表达，本地证据不支持将其说成Kit的强制要求。

本次console:11–12和supervisor_result的`console_evidence.final_kit_argv`保留完整最终Kit argv；console:13确认实际加载private，Kit:5的Applied configs也一致。现有`--portable`仍在最终argv中。

请求尺寸与结果：

- CLI请求window1440×900、renderer1280×720。
- native `Created window: width=1440,height=900`：console:3384、Kit:3343。
- 五个composed窗口setting读回均为 **UNKNOWN**：冻结入口未导出这些值，本轮没有注入新运行代码、导出整个配置或增加step。JSON authored值、CLI请求、native创建日志是三种不同证据，不能相互冒充。
- swapchain可用性由正常app_ready、420次受控render和无相关失败支持；未编造额外native WindowDesc或“swapchain成功返回值”。

## 5. 检查、唯一实际命令与运行记录

### 5.1 CPU / pre-App

先核对解释器 `C:\isaacenvs\isaac45_harl\python.exe`，9月30日及10月3日一致。

| 检查 | 实际结果 |
|---|---|
| formal pose CPU tests | 31/31 PASS，1.731s；本任务9月30日准备阶段执行 |
| manual visual CPU tests | 21/21 PASS，0.663s；同上 |
| helper内存正反例 | 17/17 PASS；严格三diff、类型、额外/缺失字段拒绝 |
| supervisor完成谓词 | 14/14 PASS；只是字典判定测试，不是runtime |
| 新repro语法 | 两个新文件py_compile PASS；未扩大到未修改生产Python |
| Windows argv往返 / helper幂等 | 完整子命令list2cmdline→CommandLineToArgvW一致；D3D12不重复追加 |
| 运行前14项要求 | 全部PASS，包括source/private解析、diff3、三值、renderer、profile/witness/beta、冻结控制/PD/solver、explicit-on、D3D12、private实际路径、source不变 |
| 冻结核对 | 20个相关原实现/测试/v1文件与准备前一致，运行后仍20/20一致；另核对4个新输入供启动前检查 |

恢复任务时源码hash仍相同，因此没有为了跨日再重复52项已通过CPU测试。没有formal App、joint App、空GUI、viewer、Vulkan或第二次App。

CPU测试实际命令（本任务准备阶段）：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_pose_control.py
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_manual_visual.py
~~~

唯一运行外层命令，cwd为仓库根：

~~~powershell
$env:PYTHONUTF8='1'
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u logs/scan_assignment/20261003_cr12_private_user_config/repro/supervise_cr12_private_user_config.py --attempt-dir logs/scan_assignment/20261003_cr12_private_user_config/attempt_01
~~~

实际唯一子命令：

~~~powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_pose_target.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261003_cr12_private_user_config\attempt_01' --device cuda:0 --physics_steps 1200 --motion-profile manual_visible_local_v1 --visual-debug-pose --view-preset arm-oblique --pd-profile baseline --external-forces-every-iteration on --info '--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/private_config/user.config.json'
~~~

监督器继承父环境，仅合并进程级PYTHONUTF8=1、HEADLESS/ENABLE_CAMERAS/LIVESTREAM/XR=0。没有修改系统/用户/Conda持久环境变量。原pre-App CUDA链已实际执行，torch2.5.1+cu121、cuda:0、synchronized=true；没有另开CUDA资格测试。

### 5.2 GUI与退出

| 字段 | 本次值 |
|---|---|
| 时间 | 2026-10-03 21:36:41.676–21:37:32.623 +08；Kit正文13:36/13:37为UTC |
| Python / experience | `C:\isaacenvs\isaac45_harl\python.exe`；`E:\Project\IsaacLab_HARL\apps\isaaclab.python.kit` |
| App / Kit / driver | Isaac Sim4.5.0；Kit106.5.0+release.162521.d02c707b.gl；日志driver610.60 |
| App构造 / 全树 | 20.593s / 50.938s，分别低于180s / 360s |
| 模式 | GUI、cuda:0、D3D12；相机/livestream/XR关闭 |
| Conda / target PID | 14028 / 36516 |
| 退出码 | 两者均0；全部所属进程退出 |
| 超时 / 强杀 | false / false |
| App次数 / 重试 | **1 / 0**，没有第二次App |

实际后端见Kit:2682、3466；entry的app_ready见console:5598。先收到`app_close_begin`（console:7258），随后监督器持有的进程句柄证实自然exit0；没有编造`app_close_returned`事件。entry保留`WORK_COMPLETED_PENDING_NATURAL_EXIT`写盘状态，最终退出判定由supervisor补足，不改写原始result。

### 5.3 场景、marker与manual motion

固定v1/lift0、baseline PD、dt=1/120、TGS8/2、explicit external-forces-every-iteration=on保持。实际GPU pipeline、GPU dynamics及cuda:0 joint tensor已读回。on的after-reset/before-motion/before-exit composed USD读回均true，仍不冒充额外native flag getter。

实际目标由本次初始root × FK(witness) × 原T_ES构造，witness=(0,+3,−4.5,0,+4.5,0)°、beta=1，位移 **32.107397mm**、旋转约3°。reference6秒、上限10秒/1200步，未调整。witness只用于构造目标，不是直接播放的关节轨迹；COM adapter继承已接受formal结果，semantic_recheck_performed=false，没有重验formal资格。

| marker运行事实 | 值 |
|---|---|
| PointInstancer | 1个，`/CR12PoseDebug` |
| prototypes / instances / indices | 9 / 9 / 0…8 |
| actual frame | RGB三轴，长.20m、半径.0035m；白球半径.006m |
| final target frame | 浅RGB三轴，长.14m、半径.0025m；黄球半径.008m |
| origin gap | 品红线，半径.0018m，连接两个真实origin |
| schema检查 | marker子树无RigidBody/Collision/Mass/Articulation/Joint；不是机器人碰撞体 |
| setup/readback | visual_setup_completed=true，visible=true，visibility=inherited |
| 更新 / 错误 | 841次（初始1+受控840），visual_errors=[] |
| spectator | arm-oblique；eye=(2.321039,−2.750000,3.487302)m，look-at=(.121039,−.150000,2.137302)m |

记录源：result的visual_metadata/setup_readback及spectator，源码 `_cr12_pose_visuals.py:118` 起。实际与target最终接近时会正常重合；没有人为平移frame、额外reference marker或更改depth规则。

| 运动/guard | 实际结果 |
|---|---|
| 受控physics / CSV | 840步 / 840样本；7.000000365s |
| 初始化 | 原2步单列，未算进受控840步；无新增refresh step |
| 稳定窗 | 第720–840步，121点，1.000000052s |
| 最终位置 / 姿态误差 | **0.057746825mm / 0.006121124°** |
| 六类guard | clock、joint、contact、geometry、frame、render_clock各840 PASS |
| 下发目标检查 / 轨迹几何采样 | 840 / 1680（每次proposal中点及终点） |
| 受控render | 420次，原render_clock检查保持 |
| 禁止接触最大力 | 0N（限既有监测pair） |
| root漂移 / 固定frame最终误差 | 已记录translation/rotation为0 |
| 最大raw DLS / 单步command变化 | .019391764 / .000323197rad，原阈值未放宽 |
| 完成 | MANUAL_VISUAL_MOTION_COMPLETED；failures=[]、secondary_failures=[] |
| 最终分类 | MANUAL_VISUAL_RUNTIME_SMOKE_PASS；formal_acceptance_written=false |

CSV内部的POSE_REACHED是已有到位计算结果，外层manual分类保持独立。运动通过实际关节目标与PhysX推进，没有teleport、每步回写状态或独立移动扫描相机。此处guard PASS仅覆盖既有场景、pair及离散检查；不升级为任意构件避障或视觉mesh无穿插的证明。

### 5.4 日志警告与尚未观察的视觉效果

日志不是“零warning”。有一条与marker有关的Hydra warning：console:7242 / Kit:6938 指向 `/CR12PoseDebug.proto7_mesh_id0`，提示尚未populated；另有TLAS警告（Kit:5202–5203）及HDF5构建/运行版本警告（console:5380）。本轮没有据此修改marker、依赖或配置。

没有匹配到Error/Fatal、swapchain失败、CUDA错误或原生崩溃；marker setup/readback及visual_errors=[]仍是真实记录。这些证据支持runtime smoke，但**不能证明所有颜色、球或轴已被人眼清晰看见**，尤其origin球相关警告应在人工观察时留意。

## 6. 假设解释与不能证明的内容

本次满足L0+L1，也完成L2+L3。因此：

> task-private saved-window-state override is consistent with the hypothesis that persistent window restoration contributed to the prior failure.

即：**本次结果支持“持久窗口恢复参与历史故障”的假设**。原source未变、实际private加载、正尺寸窗口和成功退出构成证据链；不是只看参数写了false就宣称生效。

仍未证明：

- −1/−1的native sentinel具体含义、最终优先级及120/0的计算来源；
- 哪一个字段或组合是唯一根因，其他user.config字段或桌面时序已被完全排除；
- 所有未来GUI运行必然稳定，或直接使用原source已被修复；
- wrist-oblique此次已运行、人工可读性通过、visual mesh差异已解决；
- 正式pose范围扩大、扫描采集成功、相机启停、双视点或MRTA接入完成。

原source依然是−1/−1/true，因此后续人工命令必须每次新建private；不要重用旧直接启动命令或本次运行后的private输出。

## 7. 人工查看交接：两条隔离命令

**现在满足重新建议人工查看的条件（L1+L2 PASS、visual_errors=[]，且L3也PASS）。** 以下两条命令未由Codex执行，不构成本轮第二次App。先A整臂，再B末端；B的preset只经既有CPU检查，本轮实际只运行A。

每次从当前source创建新的timestamp副本，helper只改同样三项并严格校验；若source结构/原三值变化或输出存在，会非零退出，命令随即停止，不回退到原配置。每次使用全新manual输出目录。进程级环境值仅作用于当前shell及其子进程，不是持久设置。

### A. arm-oblique

~~~powershell
Set-Location 'E:\Project\IsaacLab_HARL'
$env:PYTHONUTF8='1'
$env:HEADLESS='0'
$env:ENABLE_CAMERAS='0'
$env:LIVESTREAM='0'
$env:XR='0'
$cr12Output = Join-Path 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261003_cr12_private_user_config' ('manual_arm_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
$cr12Private = Join-Path $cr12Output 'private_config\user.config.json'
$cr12Prepared = @(& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B 'logs/scan_assignment/20261003_cr12_private_user_config/repro/prepare_private_user_config.py' --source 'C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\user.config.json' --output $cr12Private)
if ($LASTEXITCODE -ne 0 -or $cr12Prepared.Count -ne 1 -or -not (Test-Path -LiteralPath $cr12Private)) { throw 'Private config preparation failed; App not started.' }
$cr12Kit = '--/app/userConfigPath=' + ([IO.Path]::GetFullPath($cr12Private)).Replace('\','/')
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_pose_target.py --usd-path 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd' --output-dir $cr12Output --motion-profile manual_visible_local_v1 --visual-debug-pose --view-preset arm-oblique --physics_steps 1200 --pd-profile baseline --external-forces-every-iteration on --device cuda:0 --info "--kit_args=$cr12Kit"
Write-Host "Exit code: $LASTEXITCODE; output: $cr12Output"
~~~

### B. wrist-oblique

~~~powershell
Set-Location 'E:\Project\IsaacLab_HARL'
$env:PYTHONUTF8='1'
$env:HEADLESS='0'
$env:ENABLE_CAMERAS='0'
$env:LIVESTREAM='0'
$env:XR='0'
$cr12Output = Join-Path 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261003_cr12_private_user_config' ('manual_wrist_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
$cr12Private = Join-Path $cr12Output 'private_config\user.config.json'
$cr12Prepared = @(& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B 'logs/scan_assignment/20261003_cr12_private_user_config/repro/prepare_private_user_config.py' --source 'C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\user.config.json' --output $cr12Private)
if ($LASTEXITCODE -ne 0 -or $cr12Prepared.Count -ne 1 -or -not (Test-Path -LiteralPath $cr12Private)) { throw 'Private config preparation failed; App not started.' }
$cr12Kit = '--/app/userConfigPath=' + ([IO.Path]::GetFullPath($cr12Private)).Replace('\','/')
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_pose_target.py --usd-path 'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd' --output-dir $cr12Output --motion-profile manual_visible_local_v1 --visual-debug-pose --view-preset wrist-oblique --physics_steps 1200 --pd-profile baseline --external-forces-every-iteration on --device cuda:0 --info "--kit_args=$cr12Kit"
Write-Host "Exit code: $LASTEXITCODE; output: $cr12Output"
~~~

观察整臂运动是否连续、是否明显跳变/抖动；actual长粗RGB/白球是否靠近target短细浅RGB/黄球，品红线是否缩短。留意两球及三轴是否实际可见，区分最终真实重合与渲染缺失。结果要同时看result中的运动/visual_errors与退出码；exit0本身不能代替完成记录。未来人工直接命令有1200步/10秒控制上限，但没有自动复用本次Job监督器的180/360秒墙钟监督；本次已执行运行才具有该全树监督证据。

## 8. 文档变更、辅助证据与停止条件

新增本报告，小范围更新 [TASK_PROGRESS](../../TASK_PROGRESS.md) 和 [REPORT_INDEX](../../REPORT_INDEX.md)。旧诊断、manual实施及formal/basic报告不改；没有历史迁移/清理、ZIP、ledger、全仓hash或视频/图像序列。

交付检查：本报告17个相对链接及新增交接导航均有效；5个PowerShell代码块仅做Parser语法检查，全部通过，未执行其中的人工命令。TASK_PROGRESS范围内git diff --check通过（仅提示既有LF/CRLF转换策略）；Git索引仍是原有单项ZIP删除，没有本轮暂存操作。独立只读复核未发现报告与运行证据不一致。

| 结论/检查项 | 文件位置 | 关键字段或定位 | 用途 |
|---|---|---|---|
| source/private准备 | [source_private_config_summary.json](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/source_private_config_summary.json) | source_before/private_bytecopy/private_pre_app | byte-copy、源值、运行前输入 |
| 仅三项差异 | [private_config_diff.json](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/private_config_diff.json) | diff_count=3、all_other_values_equal | 不包含无关个人配置 |
| 14项预检及冻结 | [preflight.json](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/preflight.json) | checks、expected_kit_tokens、freeze | 运行前通过；private hash不用于禁止Kit合法写回 |
| CPU结果 | [cpu_checks.txt](../../../../../../../../logs/scan_assignment/20260930_cr12_private_user_config/repro/cpu_checks.txt) | 31/31、21/21 | 中断前本任务真实CPU记录；代码10月3日未变 |
| 唯一实际命令 | [command.json](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/command.json) | argv/cwd/child_environment_overrides | 本次启动与预算 |
| 配置保护及写回 | [config_runtime_summary.json](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/config_runtime_summary.json) | pre_popen、source_unchanged、private_semantic_diff_count | source不变、private输出区别 |
| 原始运行结果 | [result.json](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/result.json) | manual_target、visual_metadata、pose_summary | 实际scene/marker/运动，不代替进程退出 |
| 进程及分层结果 | [supervisor_result.json](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/supervisor_result.json) | layer_checks、runtime_classification、target_exit_code | L0–L3/自然退出/无重试 |
| 原始日志 | [console.log](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/console.log) / [Kit log](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/kit_20261003_213646.log) | loading、Created window、API、warning | 实际加载/窗口/后端/警告；Kit副本只来自同run |
| 实际逐步记录 | [pose_joint_trace.csv](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/attempt_01/pose_joint_trace.csv) | 840样本、guard、stable_samples | 原入口必要单CSV，无额外raw dump |
| 准备/监督源码 | [prepare helper](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/repro/prepare_private_user_config.py) / [supervisor](../../../../../../../../logs/scan_assignment/20261003_cr12_private_user_config/repro/supervise_cr12_private_user_config.py) | prepare/build_command/verify_pre_popen/completion | 单次可复核工具，未放报告目录 |
| 历史边界 | [上轮定向诊断](../../202609/20260930/CR12_MANUAL_GUI_SWAPCHAIN_DIAGNOSIS_AND_RETRY_REPORT.md) / [manual实现与原始失败](../../202609/20260930/CR12_MANUAL_VISUAL_MOTION_AND_MARKER_REPORT.md) | 历史120×0/0步/marker未进入 | 保留当时结论 |

`logs/`证据受现有忽略规则影响，仅在本机保存，未打包/提交，不承诺新checkout自动包含。没有失败，因此未另造runtime_failure_summary或重复结果包。本机原始Kit路径为 `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\logs\Kit\Isaac-Sim\4.5\kit_20261003_213646.log`，同次副本已在表中定位。

本轮没有修改真实user.config/shared user.toml、DPI/显示器/注册表/driver、生产实现、controller/PD/solver/dt/资产；没有Vulkan、正式/基本驱动App、相机、构件、双视点、MRTA、训练或Git写操作。既有dirty worktree与已暂存历史ZIP删除保留，未替用户清理。

**下一步：等待GPT/用户审阅本报告，并由用户按private方式进行人工观察。** 相机、双视点、MRTA和visual mesh修复尚未开展；不自动继续实施或启动另一个App。

