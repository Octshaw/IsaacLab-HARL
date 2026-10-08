# Windows Isaac Sim 4.5 项目运行时兼容性：定向评估与最小修复方案

日期：2026-09-28，Asia/Shanghai（+08:00）。状态：**静态评估完成，等待 GPT/用户审阅；尚未修复、尚未运行验证。**

仓库：`E:\Project\IsaacLab_HARL`。下文 `T/`＝`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`；`L/`＝`source/isaaclab/isaaclab/`；`I/`＝`C:/isaacenvs/isaac45_harl/Lib/site-packages/isaacsim/`；`Z/`＝[交接ZIP](IsaacSim45_Backend_Handoff_20260928.zip)内的`IsaacSim45_Backend_Handoff_20260928/`。ZIP文件行号指解码后的文本行，不是新生成的证据副本。

证据分类：**U**用户确认；**R**已有运行记录；**S**当前源码/配置/元数据直接确认；**P**推断或方案；**V**尚需运行验证；**Q**需用户决定。历史报告保留当时结论，本报告只追加当前来源和边界。

## 1. 执行摘要

**现在没有证据认定“当前项目代码入口与独立GUI发生了同类闪退”。** 交接中可核对的是`isaac45`独立GUI的Vulkan失败、D3D12成功；[单机双视点评估](SINGLE_ROBOT_TWO_VIEWPOINT_IMPLEMENTATION_ASSESSMENT.md)明确没有运行Isaac。定向检查也未定位到该静态评估之后的项目入口运行日志。项目端应写 **尚未验证**，不能写“Codex也同样崩溃”或“项目已修复”。

**推荐一个项目内最小方案：Windows启动参数helper＋现有入口的少量接入。** 对没有显式后端选择的Windows项目启动，经本地真实支持的`args_cli.kit_args`传入`--/app/vulkan=false`；保留用户显式选择、全部其他Kit参数、experience、设备、业务gate及原pre-App CUDA准备。采用现成`view_scan_assignment.py`的有界实际任务循环承载未来验证，不另写只能打开GUI的启动器，不解封event入口、不启动训练。

当前有两项重要环境事实：

- U：`isaac45_harl`由`isaac45`通过Conda复制，前者为主要开发环境，后者保留为纯净环境。S：当前两者editable Isaac Lab指向不同checkout，元数据也不同；克隆关系不证明当前运行内容完全一致。
- S：`isaac45_harl/conda-meta/state`已经存在`env_vars.PYTHONUTF8="1"`。本次标准库`conda run`检查确认为UTF8 mode 1；直接启动同一个绝对Python而不经激活时为0。**无需默认再修改Conda变量、注册表或共享配置；必须保证真实父进程采用正确启动方式。**

D3D12是有GUI证据支持的候选规避路径，仍须在项目Python、项目experience和既有初始化顺序下验证。没有依据将驱动610.60、显存、DLL本身或某个Python菜单函数定为唯一根因。Phase B保持 **COMPLETE / GPT REVIEW PASS / CLOSED**。

## 2. GUI与项目证据对照

### 2.1 已有运行记录及时间边界

先读`Z/00_README_HANDOFF.md`，再读其指定材料。[外部同名Markdown](IsaacSim45_Backend_Handoff_20260928.md)与ZIP内README字节一致。`Z/FILES.md:3/8–20`明确区分原始日志副本、事件摘录、已测试BAT和未执行候选PY。没有执行包内脚本或批量展开ZIP。

| 字段 | 原配置Vulkan GUI | 独立配置Vulkan GUI | 独立配置D3D12 GUI | 本轮项目代码入口 |
|---|---|---|---|---|
| 时间 | Windows事件2026-09-28 11:17:07 | test_info开始11:30:04.17、结束11:30:40.88；事件11:30:18 | Kit文件名11:37:41；精确结束墙钟时间UNKNOWN | 未运行；静态评估文件保存于11:18:27 +08:00，本次读取约22:54以后 |
| 时区 | 原摘录无显式时区 | Kit正文03:30:04与本地11:30相差8小时 | Kit正文03:37:41与文件名11:37相差8小时 | 本机明确Asia/Shanghai +08:00；GUI的8小时时差按此对应解释，不伪装成日志显式时区字段 |
| Python/环境 | 事件指向`C:\isaacenvs\isaac45\python.exe` | 同左；test_info确认Python路径 | BAT固定`isaac45`，原始Kit日志的full experience/ext目录也指向该环境 | 静态解释器实测`C:\isaacenvs\isaac45_harl\python.exe`；未来runtime尚未启动 |
| 入口/experience | 完整命令UNKNOWN；交接称GUI | `Scripts/isaacsim.exe isaacsim.exp.full --vulkan`，另传独立userConfigPath | 同一exe与full experience，改为`--/app/vulkan=false`，另传独立userConfigPath | 尚无此次运行命令；现有入口链见第3节，双点入口未创建 |
| cwd、checkout/HEAD | UNKNOWN | BAT无cd且未记录cwd；checkout/HEAD UNKNOWN | 同左 | 静态cwd为本仓库；main/`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`，不能移作GUI运行HEAD |
| 用户配置 | 交接称原用户配置，具体当时内容UNKNOWN | `C:\Users\33506\isaacsim_gui_clean_17041_8848\user.config.json`，BAT创建空JSON | `C:\Users\33506\isaacsim_dx12_17903_10736\user.config.json`，BAT创建空JSON | 当前共享TOML未发现；未来实际加载位置待日志确认 |
| 实际Graphics API | 交接记录Vulkan；该次完整控制台未附 | 原始日志明确Vulkan | 原始日志明确D3D12 | UNKNOWN/尚未运行，不能由拟传false推断 |
| GPU/驱动 | 该次完整GPU表未附，不从另次补齐 | RTX4060Ti，7949MB，610.60 | 同设备、显存和驱动字段 | 本次未查询GPU、未创建CUDA context；不将GUI记录写成项目runtime实测 |
| 失败阶段/异常 | Event1000，具体完整启动过程UNKNOWN | `app ready`后Windows fatal exception/access violation；Python栈含menu/hotkey/update | 用户确认GUI/菜单稳定，正常关闭 | 没有新的项目异常记录可比 |
| 原生特征 | `rtx.scenedb.plugin.dll` / `0xc0000005` / `0x00000000000d6d4b` | 同左 | 未记录相应故障；事件查询未匹配不是独立无故障证明 | UNKNOWN，不编造相同模块或偏移 |
| 完成/退出 | 完整退出码UNKNOWN | app ready 12.330s；EXITCODE=-1073741819 | app ready 10.994s；Full App loaded 114.467s；EXITCODE=0＋用户操作反馈 | 无完成记录、无退出结果，项目端尚未验证 |

原始来源：`Z/evidence/02_vulkan_gui_failed.txt:1–3/69/75/83–87/562/565–568/600–622`；`03_vulkan_test_info.txt:1–17`；`04_vulkan_windows_error_excerpt.md:3–4/13–33/42–56`；`05_d3d12_gui_passed.txt:1–3/67/73/81–85/562/565–571`；`06_d3d12_windows_events.txt:1`。04是Windows事件**结构化摘录**，不称完整原始事件文件。

两条GUI命令可由BAT及日志对应恢复如下；这些是**历史GUI命令，不是本轮要执行的项目命令**：

```text
"C:\isaacenvs\isaac45\Scripts\isaacsim.exe" isaacsim.exp.full --vulkan "--/app/userConfigPath=C:\Users\33506\isaacsim_gui_clean_17041_8848\user.config.json"
"C:\isaacenvs\isaac45\Scripts\isaacsim.exe" isaacsim.exp.full --/app/vulkan=false "--/app/userConfigPath=C:\Users\33506\isaacsim_dx12_17903_10736\user.config.json"
```

BAT来源：`Z/scripts_tested_gui/isaacsim_gui_clean_config_test.bat:21–24/38/60–64`与`isaacsim_gui_d3d12_test.bat:22–25/37/61–65`。实际重定向分别到上述独立目录的`gui_console.txt`；两者都进程局部设置UTF8、faulthandler和unbuffered，没有记录cwd。独立空JSON只隔离该persistent-settings文件，不能说隔离了全部共享配置、缓存和系统因素。

GBK问题：最初`isaacsim.sensors.rtx.ui/.../extension.py:54`的`json.load`解码错误及启用UTF8后消失，由README和用户反馈记录，原始完整失败日志未附；后续环境记录UTF8 mode 1。它与app ready之后的原生异常分别归类。两种后端日志都出现TLAS警告（02/05各566–567行），故该警告不足以证明OOM。

### 2.2 当前版本来源和项目记录的有限搜索

| 来源 | isaac45（GUI/base） | isaac45_harl（主要开发） | 解释 |
|---|---|---|---|
| 用户说明 | 保留纯净环境 | 从base复制后用于开发 | 环境用途/来源，不能代替当前包检查 |
| 当前editable isaaclab元数据 | 0.41.3，指向`E:/Project/IsaacLab/source/isaaclab` | 0.36.23，指向`E:/Project/IsaacLab_HARL/source/isaaclab` | 标准库读取METADATA/direct_url.json，不导入Isaac Lab |
| 对应checkout VERSION | `E:/Project/IsaacLab/VERSION`为2.1.1 | 本仓库`VERSION:1`为2.1.0；`source/isaaclab/config/extension.toml:4`为0.36.23 | 仓库版本和Python扩展版本是不同字段；历史v2.1.1有另一checkout来源，不据此升级/降级 |
| 当前关键包metadata | isaacsim4.5.0.0、torch2.5.1+cu121、torchvision0.20.1+cu121 | 对应三项相同 | 未进行全依赖等同性审计；相同元数据不证明完整环境等价 |
| GUI实际日志版本 | 02/05:562显示4.5.0-rc.36 | 无此次项目日志 | 运行显示版本与pip发行版本分别保留 |
| 本轮标准库Python | 不启动其runtime | Python3.10.20；conda run的sys.executable、UTF8 mode及isaacsim顶层spec都指向harl | 只证明当前离线读取进程，不证明历史或未来runtime状态 |

当前Isaac Lab元数据的具体来源是`C:/isaacenvs/isaac45/Lib/site-packages/isaaclab-0.41.3.dist-info/METADATA:3`及`direct_url.json:1`，以及harl对应的`C:/isaacenvs/isaac45_harl/Lib/site-packages/isaaclab-0.36.23.dist-info/METADATA:3`及`direct_url.json:1`。GUI环境其余当时版本见`Z/evidence/01_environment_isaac45.txt:1–44/1025/1969–2000`：numpy1.26.4、scipy1.13.1、osqp0.6.7.post3、qdldl0.1.7.post4、h5py3.10.0，pip check无破损依赖。这是附件已有结果，本轮未执行pip check或GPU工具。

只定向查看交接指向的Kit日志位置、已知harl portable日志、同日AgentRead，以及仓库`logs/scan_assignment`、`outputs`、`results`的当前层近期记录，没有递归扫描所有历史实验。评估11:18:27之后定位到的同日Full GUI记录为11:30 Vulkan和11:37 D3D12，没有项目脚本/本仓库运行链标志。**未找到不等于证明任何其他位置绝无日志；已有材料足以继续方案分析，无需为作同因判断重新制造Vulkan崩溃。**

定向日志索引（读取文件时间与内容，不用目录mtime代替）：

| 实际位置 | 本次定位到的记录 |
|---|---|
| `C:/isaacenvs/isaac45_harl/Lib/site-packages/omni/logs/Kit/Isaac-Sim/4.5/` | 最新`kit_20260924_190406.log`，mtime为09-24 19:04:19 +08:00；没有09-28记录 |
| 同harl日志根的`Isaac-Sim Python/4.5/` | 最新`kit_20260827_133137.log`，mtime为08-27 13:31:52 +08:00；不将其旧结果搬作本次证据 |
| `C:/Users/33506/.nvidia-omniverse/logs/Kit/Isaac-Sim Full/4.5/` | 当日8份GUI日志；`kit_20260928_113004.log:5/4461`明确base/full、显式--vulkan、实际Vulkan；`kit_20260928_113741.log:5/4453/7004`明确base/full、false、D3D12、app ready。后者mtime为14:21:57 +08:00，mtime不等于精确进程退出时间 |

另有当天`kit_20260928_092445.log:5`和`kit_20260928_092648.log:5`，其Cmd首项出现`isaac45_harl/Scripts/isaacsim`，但experience/ext路径来自base `isaac45`。静态读取当前`C:/isaacenvs/isaac45_harl/Scripts/isaacsim.exe`与base同名exe，两者字节相同，均在byte offset108032包含`#!C:\isaacenvs\isaac45\python.exe`。**当前克隆目录的GUI console launcher仍指base解释器**，与上述混合路径线索一致；当前字节不能单独证明所有历史行为。这不是项目MRTA/双点脚本运行记录，也不是本轮要修复的项目入口。未来直接使用明确的harl Python启动项目脚本，可避开这个console launcher；本轮不重装或改写exe。

## 3. 实际启动调用链与配置来源

### 3.1 外层命令和入口范围

当前没有本次项目runtime父进程记录。后续建议由PowerShell在仓库cwd通过绝对Conda命令启动目标Python；Conda负责激活环境/继承设置，Python内AppLauncher启动Kit，不是另造一个Python GUI子进程。

`isaaclab.bat:42–69`优先从`CONDA_PREFIX`选择Python，否则找`_isaac_sim/python.bat`或系统Python；`:402–432`通过`for %%a in (%*)`拼回参数再执行。它存在Windows额外拆分/引号层，不能假定任意含空格Kit值都无损。不为本次问题重构该通用BAT；推荐已有绝对`conda run -p ... python ...`路径，仍需未来记录实际argv。用户若改用IDE/另一父进程，需要在那个真实启动点确认UTF8和环境继承。

| 入口 | 当前调用链及源码位置 | 本轮适用边界 |
|---|---|---|
| `scripts/reinforcement_learning/harl/train.py` | `:40–47`场景pre-parser；`:96–100`默认合并/parse_known/preflight；`:123–128`video联动相机、清理argv；`:131–150`pre-App CUDA；`:175`AppLauncher；`:202`Hydra main；`:304–332`runner/run/save/close | 真实训练入口；没有可拿来本次无训练检查的现成no-train模式，不运行它来测试图形 |
| `scripts/reinforcement_learning/harl/play_assignment.py` | `:174–195`parse/preflight/argv；`:198–214`CUDA；`:216`AppLauncher；`:617/645`运行gate及env wrapper；后续actor/checkpoint/playback | 有checkpoint/策略路径，本阶段不使用，也不假装有限viewer证明它通过 |
| `scripts/environments/view_scan_assignment.py` | `:16–28`CLI；`:30`AppLauncher；`:85`parse_env_cfg；`:94`gym.make；`:107`env.reset；`:119–127`solver→actions→env.step；`:139/144`正常关闭 | 已存在、无训练、支持`--max_steps`与`--duration`；最小实际任务验证载体 |
| `scripts/environments/evaluate_scan_assignment.py` | `:39`AppLauncher；`:295/304/307`cfg/make/reset；`:354`step，含episode预算和统计 | 能有界，但首轮比viewer多统计/重置逻辑，不作为默认兼容性检查 |
| `scripts/environments/random_agent.py` | `:27`AppLauncher后构造env，`while simulation_app.is_running()` | 无现成步数上限，不优先使用 |
| 拟建`run_single_robot_two_viewpoint_scan.py` | 只有上轮方案，无实现文件 | 以后复用同一启动处理；当前不能填写启动PASS |
| `test_assignment_phase_b_final_closure.py:429–449`及其指定helper | 历史worker清argv→pre-App CUDA→AppLauncher→受控构造/学习 | 只读此局部解释历史顺序；不运行、恢复或当作新有界检查入口 |

viewer默认任务为`Isaac-Scan-Mobile-Manipulator-Direct-v0`，注册在`T/__init__.py:19`附近；`ScanMobileManipulatorEnvCfg.assignment_lifecycle_profile="legacy"`（env文件337行），默认`scenario_config_path/robot_config_path/component_mesh_path/viewpoint_csv_path`分别在134/137/173/278行为空。后续只用该现有合法默认profile、`num_envs=1`作运行兼容性检查。它是原proxy任务，不是CR12实际关节执行环境，也不是event learner资格重验。

公共event preflight：`T/scenario_config.py:353–392`在AppLauncher前拒绝`event_gated_local_mrta`；train100和play_assignment177调用。错误包含`AppLauncher_constructed=False`，这种拒绝不是图形崩溃。保持现有authority/gate，不能通过换入口或改profile标签绕过。

### 3.2 参数转发、设备和初始化

- **业务参数先解析**：train/play_assignment用`parse_known_args()`把未知参数留给Hydra，再重写`sys.argv=[script]+hydra_args`；已知`kit_args`保存在Namespace里，不因argv清理丢失。viewer用`parse_args()`，裸未知Kit参数会被拒绝。统一使用受支持的`--kit_args="--/app/vulkan=false"`；不能假定把裸`--vulkan`放到任意入口都合法。
- **场景默认值**：`scenario_config.smoke_defaults_from_config:583–594`可给headless/device等提供默认，train/play随后`parser.set_defaults`，显式CLI通常再覆盖它；此函数未找到kit_args/experience默认映射。video会把enable_cameras设True。后端修复不更改这些约定。
- **AppLauncher**：`L/app/app_launcher.py:447–474`依次解析livestream/headless/camera/XR、device、experience、kit_args；`:754–760`以普通`str.split()`拆Kit字符串并追加到argv；`:780`创建SimulationApp；成功返回后`:787–794`按token值清理附加参数。因此无空格的D3D12 token可经该实际通道传递；嵌套引号/带空格的userConfigPath不能仅靠外层引号保证安全，暂不新增这类参数。
- **不要用错误接口**：`AppLauncher._SIM_APP_CFG_TYPES:371–395`不含`vulkan`或`extra_args`，`:472–474`会过滤不在白名单内的字段。不能将`AppLauncher(vulkan=False)`或传extra_args写成此版本已支持的修复。`renderer="RaytracedLighting"`表示渲染模式，不等于D3D12。
- **SimulationApp**：`I/exts/isaacsim.simulation_app/isaacsim/simulation_app/simulation_app.py:_start_app:303–427`构造experience及配置参数，读取argv的unknown_args，最终`:423–427`追加并调用同进程`app.startup`。这解释了kit_args的有效到达位置；是否实际选中D3D12仍看未来日志。
- **既有CUDA顺序必须保留**：train`_warm_start_torch_cuda:131–150`和play_assignment`:198–214`在AppLauncher之前创建CUDA tensor、执行Linear.forward并synchronize，不是仅查is_available。CUDA不可用时会直接返回，且未读回核验已知数值；不能把helper返回当CUDA验收通过。历史helper也在pre-App，但不是本次需要重启的验收体系。
- **设备分层**：AppLauncher`:620–668`解析CLI device并设active_gpu/physics_gpu；train/play的env_cfg与HARL learner设备另由Hydra/agent_cfg决定，不能由一处CLI设备补齐整条链。viewer的`parse_env_cfg`经`isaaclab_tasks/utils/parse_cfg.py:128`明确写`cfg.sim.device`，更适合作为首轮有界检查。CUDA张量通过不等于PhysX GPU机器人步进通过。

没有在上述真实viewer/train路径中发现用于启动另一个Isaac Python的subprocess。play_assignment`:495–506`的subprocess是只读`git rev-parse HEAD`，没有env替换，不是runtime子进程。若未来外层确需子进程，应继承`os.environ.copy()`再合并少量键、用参数列表而非字符串拼接，并保留cwd、退出码及异常分类；本方案不默认引入Python自重启或新的进程框架。

### 3.3 UTF8、experience和配置优先级

S：KnownFolder(MyDocuments)当前为`C:\Users\33506\Documents`，其`Kit/shared/user.toml`不存在。Process/User/Machine作用域的PYTHONUTF8在本次父进程读取中未设置；`C:/isaacenvs/isaac45_harl/conda-meta/state:3`的选定键已为1，base没有同一state文件。不能将附件的共享TOML建议写成已经落地，也不能说所有绝对路径harl Python天然处于UTF8模式。

当前已存在的harl portable用户配置为`C:/isaacenvs/isaac45_harl/Lib/site-packages/omni/data/Kit/Isaac-Sim/4.5/user.config.json`，mtime为09-24 19:04:19 +08:00；仅定向检查的相关键/文本中未发现vulkan或userConfigPath覆盖，未输出其余个人设置。未来是否仍加载这个文件由同次Kit日志确认，不凭旧mtime推断。

本次标准库检查：经`D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c ...`，`sys.executable`为harl、`sys.flags.utf8_mode=1`、`PYTHONUTF8=1`；直接绝对Python调用为0/未设置。UTF8模式在解释器启动时决定，在已运行脚本里仅写`os.environ["PYTHONUTF8"]="1"`不能改变当前解释器。推荐保留现有Conda设置和规范父进程调用，Windows入口只检查/提示；直接Python方式可在启动时用`-X utf8`，不自动递归重启。

当前离线进程的顶层`isaacsim`spec指向harl安装目录；`ISAAC_PATH/EXP_PATH/CARB_APP_PATH/ISAACLAB_PATH`在该进程导入runtime之前均未设置。`I/__init__.py:20/47–52`按文件位置推导路径且只在相应环境键为空时赋值。因此未来必须记录**实际**导入路径/experience，不能仅看Conda环境名；不为取证输出整份环境变量。

| 配置层 | 当前来源/作用 | 后续处理 |
|---|---|---|
| 应用CLI/Namespace | task、device、headless、enable_cameras、experience、kit_args | 保留全部既有值，补丁只处理缺省backend及明确冲突 |
| HEADLESS/ENABLE_CAMERAS/LIVESTREAM | AppLauncher`:476–618`读取；未显式CLI时可能参与，livestream会联动headless | 本次conda标准库进程三项均未设置；未来记录有效值，不能从CLI未写headless推断永远GUI |
| 项目experience | GUI默认`apps/isaaclab.python.kit`；headless默认`isaaclab.python.headless.kit`；相机改用rendering变体，`:670–752`解析绝对路径 | 不改experience选择逻辑，不用`isaacsim.exp.full`替换项目experience |
| experience后端配置 | `apps/isaaclab.python.kit:178`显式vulkan=true；headless`:79`、headless.rendering`:84`同样true；rendering依赖python基础experience | Windows候选CLI默认覆盖这一后端请求；Linux原路径不动。headless并不代表无需图形后端 |
| userConfigPath/portable | SimulationApp`:345–348`默认追加portable；GUI附件显式独立userConfigPath | 未来项目日志记录实际加载路径；不把GUI独立JSON复制成项目配置 |
| shared user.toml | 当前实际Documents目标文件不存在 | 不新增、不覆盖；全局影响多个Kit应用且难追踪，不是推荐落点 |
| 最终生效 | argv/config/experience由Kit解析 | 同时检查启动请求、启动后`/app/vulkan`及Kit实际Graphics API；不只凭源码字符串/false值宣称成功 |

源码能确认参数传递位置与experience值，不能仅由这些Python文件穷尽Kit二进制内部的全部配置覆盖顺序。建议项目显式CLI默认优先于包内experience后端值；自定义experience路径保持原样并明确记录该覆盖意图，用户可用显式backend选择保留所需路径。遇到配置冲突或最终后端不符，停止并核对同次加载记录，不修改多层配置去碰运气。

## 4. 问题、缺口与差异化故障

| 事项/阶段 | 已有证据 | 能下的结论及下一步 |
|---|---|---|
| 文本解码 | U＋交接中的GBK错误，后续UTF8 mode1 | 保证真实Python启动UTF8；与RTX原生崩溃分开 |
| shell/Conda多行解析 | 上轮离线`-c`包装拒绝，改只读传参后完成 | 命令包装问题，不是Isaac或CUDA运行失败 |
| 离线pxr不可发现 | 上轮静态解释器find_spec结果 | 不等于USD损坏、Kit启动失败或渲染故障 |
| 业务preflight | scenario_config明确AppLauncher_constructed=False | 按声明/profile处理；不能为查backend解封event |
| CUDA初始化/运算 | 现有代码存在pre-App准备；本轮未运算 | 若未来在App前失败，先查实际设备/torch/上下文顺序，不套用app ready之后的GUI故障 |
| Vulkan RTX原生访问异常 | GUI有同DLL、code、offset，且D3D12对照成功 | 支持后端候选规避；跨环境同因、驱动唯一根因均未证明 |
| D3D12仍失败或另一模块失败 | 当前项目没有此记录 | 未来按实际API/阶段/module/code/offset另列；不自动回滚驱动或重建环境 |
| viewer退出证据不足 | 当前main无整体try/finally；提前关窗可走正常结束且没有预算完成记录 | 未来增加简洁完成/失败记录及资源收尾；EXITCODE=0不能单独代表120步完成 |
| 设备配置差异 | CLI、env sim和learner来源分离 | 验证时分别记录；首轮限定viewer/显式cuda:0，不顺手重构训练设备配置 |

最小缺失证据是**一个经批准的项目入口D3D12运行**的完整命令、cwd、源路径/HEAD、启动阶段、实际API、阶段完成记录和进程退出结果。无需主动重现Vulkan原生崩溃。若后端日志仍Vulkan，先查参数转发；若D3D12且App正常、env构造失败，查任务/资产/PhysX具体错误；只有出现新证据才考虑更大环境或驱动分支。当前不建议批量降级、537.58回滚、清缓存或重建环境。

## 5. 推荐最小修复方案（未实施）

推荐限定四个文件；新增helper是为避免三处复制后端冲突规则，并可被以后双点入口复用，不建立全仓库启动框架。无需新GUI launcher、共享TOML、Conda变量写入或多份kit修改。

| 拟改文件/符号 | 当前行为 | 建议改动 | Windows范围 | 保留行为 | 风险/待验证 | 撤销方式 |
|---|---|---|---|---|---|---|
| 新增 `scripts/environments/_windows_runtime_startup.py`，拟`prepare_windows_runtime_args` | 不存在 | 纯标准库参数helper；检查UTF8、识别显式backend/冲突、仅缺省时添加D3D12 token；给简洁来源记录 | 仅win32应用缺省，Linux原样返回 | 其他kit_args字节内容、全部业务参数 | 与本地split规则一致；最终API仍需运行确认 | 经批准只移除新文件与对应调用，不触及既有文件其他内容 |
| `scripts/environments/view_scan_assignment.py`，parse后/AppLauncher前与main收尾 | 现成有界legacy任务循环，无pre-App CUDA探针，无完整异常收尾/预算完成记录 | 调helper；拟加显式`--runtime_check`模式，复用当前循环完成有限CUDA检查、启动身份、预算和收尾记录 | 后端缺省只Windows；诊断模式须显式开启 | task/solver/device/max_steps/duration/default profile，不加入训练/相机 | GPU验证逻辑为未来新增，当前不能宣称已有；提前关窗必须单列 | 仅撤销本次新增flag/helper调用/诊断与收尾hunk，保留用户原改动 |
| `scripts/reinforcement_learning/harl/train.py`，preflight后、argv清理/warmup前 | 现有gate→warmup→AppLauncher→训练 | 仅接入相同参数helper，记录原argv | 只Windows缺省backend | preflight、warmup位置及行为、Hydra、video、runner、checkpoint等 | 不执行train作本轮兼容性验证；其完整运行仍未验证 | 只反向应用新增hook/import hunk，不整文件restore |
| `scripts/reinforcement_learning/harl/play_assignment.py`，同一边界 | gate→warmup→AppLauncher→actor/checkpoint | 同上，只接helper | 同上 | checkpoint/profile/归因/初始化顺序 | 不借此进行checkpoint恢复/推理 | 同上 |

viewer可直接从同目录导入helper；train/play利用已有REPO_ROOT，通过标准库`importlib.util`按绝对文件路径加载该单文件，使用唯一模块名。不要从`isaaclab_tasks.direct.scan_mobile_manipulator`规范包路径作pre-App导入，因为`T/__init__.py:15`会导入环境实现。helper不导入torch/Isaac，不创建context，不改sys.path。原train/play CUDA helper保留原位置；不因附件示例先创建App而换序。

viewer的未来诊断收尾边界应涵盖App构造、env构造及循环；只关闭已经获得的有效句柄，保留原异常和非零退出。构造期间原生崩溃无法保证Python finally运行，因此外层进程结果始终是必要证据，不能要求一定有close后的print，也不能把缺失完成记录当成功。

后端处理契约（P）：

1. 在参数解析前留存原argv；在已有业务preflight成功后、argv清理和warmup前处理。viewer在其parse之后、App之前处理。原业务拒绝不因兼容性补丁变成可运行。
2. Linux不注入、不改默认backend。Windows对`kit_args`按本地AppLauncher的空白token规则检查，但不重写其他token或重新格式化整串。
3. 识别本地已见的显式`--vulkan`和`--/app/vulkan=true|false`。只有false则保持；只有true/--vulkan则保持并记录显式选择；两种相反值共存时pre-App报清楚的配置冲突，不采用“最后一个赢”。同值重复不新增；helper重复调用不重复追加false。
4. 没有显式选择才追加一个`--/app/vulkan=false`，标记来源为Windows项目缺省。它有意覆盖项目experience的vulkan=true；不默默把用户显式true改成false。遇到不可识别backend写法或与裸未知argv冲突，提示使用入口支持的规范kit_args写法，不猜测后继续叠加。
5. 不把裸Kit参数迁移进Hydra，不改经验文件/headless/device/camera/episode参数。不替换AppLauncher，也不把相同token清理的框架行为扩成此次重构。带空格路径是已知转发限制，若日后需要独立userConfig再针对该参数另审，不在此堆补丁。
6. 不在运行中的主脚本设置PYTHONUTF8后宣布生效。当前Conda入口已可满足；Windows检测不符时在启动Kit前给出正确父进程调用提示。没有必要重启Python；若未来另行采用包装器，必须明示必要性、完整参数/env继承/退出码转交和单次重启上限。

后续实施前只需记录这四个目标文件当时的相关hunk/既有差异，补丁单独可审查。撤销只反向撤销本次hunk，不用整仓reset/restore覆盖既有dirty工作区；本轮没有创建这些实现文件或补丁。无需为此建立hash freeze或ledger。

## 6. 附件候选检查脚本静态审查

对象：`Z/proposed_not_validated/check_isaaclab_runtime_defaults.py`。未执行、未修改；其注释的Isaac Lab2.1.1不能作为当前项目版本证据。

| 检查点 | 实际内容与行号 | 适用性 |
|---|---|---|
| UTF8 | 15–20打印并拒绝Windows UTF8 mode非1 | 可复用检查思路；不在进程内伪修复 |
| kit_args/default | 30–31拒绝非空kit_args；34直接AppLauncher；43–50要求/app/vulkan严格False | 它检查已经生效的默认配置，不注入后端；不要求一定来自共享TOML，但错误信息指向它。不能原样验收本方案显式kit_args/helper路径 |
| CUDA初始化顺序 | torch导入40、运算54–55，都在AppLauncher之后 | 与真实train/play的pre-App warmup不同，不应拿它替代当前项目顺序 |
| 真实计算/CPU | device来自CLI；ones×2再sum.item，检查64.0（53–58） | 明确cuda时确有张量运算和读取，不只是is_available；但没有矩阵/cuBLAS覆盖，也未拒绝cpu。不存在源码中的异常捕获后自动CPU回退；准确问题是显式cpu也可打印TENSOR_OK，不能据此叫CUDA通过 |
| 场景 | 61–70只创建SimulationContext，reset并默认120step | 是空场景；不是gym任务env.reset/step，不证明CR12/物理关节/HARL/相机 |
| 预算 | 25/28–29正步数；67–71提前关闭抛异常 | 可复用有限步数和提前退出判据；无进程总超时 |
| 异常/关闭 | try从37开始，AppLauncher创建34在外；74–77 finally close | 构造失败不受该finally保护，原生崩溃也不保证Python收尾；正常异常不被吞掉，但仍需外层退出记录 |
| 完成 | 72 STEP_OK、73 TEST_BODY_OK在close之前；没有单独指定sys.exit | 正常Python路径可0退出，未捕获异常通常非0；Kit关闭行为须看外层结果。完成标志＋退出码共同判断，不能只看某个print或EXITCODE=0 |

可复用“UTF8检查、真实小计算、显式device、有限steps、早退失败、finally”的思想；不原样复制其空场景、后置CUDA初始化或禁止kit_args规则。相机/策略/checkpoint不纳入本次未来启动验证。

## 7. 后续最小验证计划（均需另行授权，均未执行）

先审阅第5节四文件方案，再做局部实现与纯参数检查，最后决定有界运行。纯参数检查只覆盖有意义的分支：Windows空值/显式true/false/冲突/重复调用/保留其他参数，以及Linux不变；不导入Kit，也不建立大型qualification框架。

主运行载体推荐修改后的viewer，`legacy`默认任务、1个env、CUDA:0、GUI、无相机/视频/learner/checkpoint。理由是它已经走实际项目cfg、gym.make、env.reset/step且无训练；不是用无关GUI替代真实链。第一次只覆盖所需GUI；未来需要headless自动执行时，另一次相同预算、显式`--headless`验证其不同experience，不能把GUI结果直接复制过去。

| 层 | 目标入口/配置与预算 | 成功依据 | 失败分类与最小记录 |
|---|---|---|---|
| 1. 真实启动链 | 同一个viewer进程；明确项目Python、cwd、task/default legacy、num_envs1、device cuda:0；App启动建议最多300s、全进程最多360s | 记录Python、UTF8、源码/HEAD、输入和最终kit_args、实际experience/config路径；App创建完成，日志实际D3D12与请求一致 | argv/preflight、UTF8、pre-App CUDA、App构造/RTX、超时分别记录；保留console与对应Kit日志 |
| 2. 真实CUDA | 未来`--runtime_check`内：pre-App保留train同类Linear/context/sync准备；App后小型已知矩阵计算、synchronize、读取核对；同一明确CUDA设备 | 显式cuda:0及tensor实际cuda设备一致；例如16×16全1矩阵乘积每项16、总和4096，读取符合；记录前/后阶段 | CUDA不可用、设备不符、异常、结果错各自失败；不能默默CPU fallback。原warmup跳过不是PASS；不修改train现有helper以混入此验收 |
| 3. 实际项目reset/step/退出 | 同进程gym.make该默认任务→env.reset一次→现有solver/controller→env.step最多120次，默认5Hz；仍受360s总预算 | 实际env类/来源、cfg.sim.device与env.device、reset完成、120/120步完成、无提前关窗、收尾记录与外层退出0同时成立 | 构造、reset、step、提前退出、close、进程异常/timeout单列；不是策略完成率0、零分或学习失败 |

第2层计算实现应保持既有pre-App CUDA准备的相对位置，明确新增的post-App计算只是检查上下文仍可用，不把第一笔CUDA准备移到App后。GPU张量结果不代表PhysX GPU已通过；第3层也只证明该legacy proxy场景的有限reset/step，未包含实际articulation受力/关节、CR12、双视点采集或HARL learner。

现有源码已经支持下面的**命令语法**，但它缺少本方案拟增加的CUDA/完整完成记录，且本轮不运行：

```powershell
# cwd: E:\Project\IsaacLab_HARL；未来若单独批准现有入口取证，才执行
& D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts/environments/view_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --num_envs 1 --solver greedy --device cuda:0 --max_steps 120 --print_interval 120 --kit_args="--/app/vulkan=false" --info
```

完整推荐验证命令是**实施后命令**：保留上述task/device/预算参数，增加拟建`--runtime_check`；首次验证helper缺省时省略`--kit_args`，核对日志显示helper实际追加false。该flag当前不存在，不能现在运行，也不能仅去掉flag就声称等价验证。`--max_steps`只约束App成功构造后的loop；360s总预算须由未来父进程监督，超时记录并结束本次尝试，不无限重试、不增加复杂进程框架。

若实际env失败且无法区分基础场景/任务原因，才考虑另审一次空SimulationContext隔离；它只能证明App与空场景，随后仍须回到上述同一启动处理下的真实viewer。附件候选脚本不因有120step就成为项目验收。以后独立双点入口建成，还必须在同一helper下补做其实际工作入口验证；train/playback的完整执行不由viewer代验，也不在此恢复训练或checkpoint。

结果保持简洁：一份阶段完成/失败记录＋console/对应Kit日志＋外层进程退出/timeout。记录实际命令、cwd、Python、源码位置、HEAD、experience、UTF8、设备、API和步数；失败时补精确时间/PID匹配的Windows事件。成功用“计划工作完成记录＋正常退出”共同判定。若数据/日志未生成而进程崩溃，外层记基础设施失败，不能造一个正常任务结果。无需逐步raw dump、全库哈希或历史checkpoint。

## 8. 与单机双视点计划的衔接及未决事项

U：新机器人USD已在当时遇到运行环境问题后手动删除。**不再待提供路径、不寻找或恢复、不据删除认定文件损坏。** 原静态报告保留当时“未定位”的事实；当前TASK_PROGRESS更新为这一最新状态。

推荐顺序保持：**Windows项目启动链处理及有界验证 → 资产与基本关节驱动 → 单视点运动和采集 → 双视点连续循环 → 后续MRTA接入。**

- 后端稳定后，才经另行授权由现有URDF准备派生资产。上轮八个link惯性问题独立于图形后端；用户尚未批准自动重算或近似，本轮也不批准。后续应审阅可靠原值或明确的仿真近似策略。
- 固定底盘与升降保持/锁定的具体方式仍需明确；fixed root不自动锁升降。基本关节驱动可先在合法安全初态做有限检查，不把完整通用规划器设成该步骤前置条件。
- 双视点运动检查必须使用与实际下发/跟踪一致的运动参考及误差/停止余量；终点可达不能代替过程安全，启用collider不能代替避障。只对所选小场景建立必要检查，不扩大路径规划研究。
- 相机安装可先提出明确的仿真固定外参/轴约定，不要求先做实体标定。仍按任务开启/关闭，不改常开筛帧；不增加深度比例、点云、重建或精度门槛。
- **采集结果与关闭结果分开**：已取得本次数据应保留`data_received=true`；随后关闭失败不能反写成未采集，但`capture_stopped`未确认就不能开始下一运动。正常等待数据不是失败。
- 上述全部是后续执行环境实现事项，不纳入当前启动兼容补丁；不动owner/completed/claim-release authority、奖励、mask、统计或学习器。

本轮真正需要审阅的决定只有：是否采用第5节四文件范围与第7节首次GUI有界验证范围。惯性策略留到资产阶段决定；无需再次询问机器人角色、扫描成功条件、USD路径或独立环境方向。当前没有必须等待额外资料才能交付本静态方案的阻断。

## 9. 本次只读操作、限制和文档变更

1. 阅读适用`AgentRead/AGENTS.md`与当前[TASK_PROGRESS](../../TASK_PROGRESS.md)，核对根及相关祖先/源码目录指令；阅读同日双点报告和20260926交接中入口/边界局部。通用测试建议未被当成运行授权；未重启Phase B/R系列验收。
2. 直接读取ZIP内README、环境、Vulkan/D3D12控制台、测试信息、事件摘录、两个BAT和候选PY；比较外部Markdown与README一致。对GBK文本采用相应解码，未改原日志、未批量解压、未执行附件。
3. 阅读当前项目入口、scenario preflight、AppLauncher、安装SimulationApp、相关experience、Conda选定设置、包METADATA/direct_url和有限日志来源。路径/通配符不匹配时改用精确路径继续只读，未安装工具或改变导入路径绕过。
4. 先核对指定Python解释器，再用标准库进行有限sys/os/importlib元数据与顶层spec检查。没有import torch/Isaac/Kit，未创建CUDA context、张量运算、App、仿真或相机。直接Python与conda run的UTF8差异仅对应这些离线进程。
5. Git只读：起始及交付核对HEAD为`24ecbad7dd1bdcd006399b64bfb757a86b71aeec`；已有暂存删除`20260925/phase_b_local_artifact_cleanup_execution.zip`，TASK_PROGRESS已有未暂存修改，同日/20260926文档和rokeaCR12资产有untracked内容。均保留，不以dirty为阻断；未执行Git写操作。没有恢复旧checkpoint、做历史全目录hash/库存/链接审计或清理任何资产。
6. 文档操作仅新增本文，并小范围更新TASK_PROGRESS的本轮状态、USD最新说明和链接；不重写旧双点评估或GUI交接。不涉及实现、测试/harness、启动脚本、运行配置、资产、installed packages、驱动、环境变量、共享TOML或shell profile修改。

交付文档：本文`AgentRead/202609/20260928/WINDOWS_RUNTIME_BACKEND_ASSESSMENT_AND_PLAN.md`；小范围更新`AgentRead/TASK_PROGRESS.md`。本报告四条本地链接均可解析，正文无行末空白；TASK_PROGRESS的scoped diff whitespace检查通过，HEAD及Git index内容与起始检查一致。仅检查本次新增链接、正文及目标文档diff，不审计已授权删除的历史原始证据。所有后续命令/代码改动/运行均为方案，尚未实施。

**静态兼容性评估已完成，等待 GPT/用户审阅；尚未修复、尚未启动Isaac/CUDA/仿真验证，未执行Git写操作。** 返回报告后停止，不自动导入机器人、修复环境、训练或提交。
