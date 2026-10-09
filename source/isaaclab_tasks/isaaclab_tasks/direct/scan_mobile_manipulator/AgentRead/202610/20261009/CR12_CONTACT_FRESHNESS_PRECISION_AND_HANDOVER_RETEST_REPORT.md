# CR12 接触新鲜度精度修正与共享转交复测报告

日期：2026-10-09，Asia/Shanghai（UTC+08:00）。仓库：`E:\Project\IsaacLab_HARL`。解释器：`C:\isaacenvs\isaac45_harl\python.exe`；preflight 记录 HEAD 为 `a8c618a32da65747827f1cb3f722fac24df2aec8`。保留既有工作区修改，本轮未执行 Git 写操作。

路径缩写：T=`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`；E=`scripts/environments/`；Q=`source/isaaclab_tasks/test/`；L=`logs/scan_assignment/20261009_cr12_contact_precision_retest/`。均相对仓库根。

## 1. 当前结论与范围

**本轮完成 `CR12_CONTACT_PRECISION_AND_HANDOVER_RETEST_PASS`。** 53 项针对性 CPU 检查通过；唯一新 App 从初始化完成 A 无数据取消/OFF、保留 claim 实际退出、clear→R/receipt 后退役、B 新 claim 同一任务并实际采集/OFF/C，以及共同 terminal/rebuild/ACK 和自然退出。四层结果均 PASS，使用 **1/3 个 App**，成功后停止；结果等待 GPT/用户审阅，不自行标注 GPT REVIEW PASS。

14 个实际 float32/cuda:0 sensor 各完成 9353 次受控更新，跨过 32/64 秒；首次旧增量谓词拒绝而新精确递推通过均在 global3842。总计 761 transitions、9353 受控 physics、4676 render，初始化 warm2 另计；App 构造 20.328 秒、所属全树 1482.765 秒，目标 Python、内层 Conda 和外层监督命令均 exit0，无超时、强杀、运行后修复或额外 App。

本轮授权修正项目层 contact 时间递推检查，保留原真实 sensor 更新/数据读取、物理安全和业务成功条件，再从初始化完整复测固定 `E1/M2/N1`、`shared_m2n1`、`shared_cancel_clear_handover`。没有先开 contact-only、空 GUI 或历史验收 App，也没有重新搜索布局或运行 9000 tick 名义几何准入。

[上一轮实施报告](CR12_SHARED_TASK_HANDOVER_IMPLEMENTATION_REPORT.md)和原始输出保持不变：上轮 setup 共同 221 tick、121 样本/1 秒；A 用 3000 tick 到位，真实 ON 后无数据取消并确认 OFF，59 tick/30 render；A 保留绑定退出时，在 global 3842 被旧 contact 检查拒绝。clear、R/receipt/退役、B claim/采集、共同 terminal 均未完成。上轮整体 FAIL 不因本轮修复而回写。

旧失败 tick 未保存的 timestamp、last_update、outdated 和 force 子项仍为 **UNKNOWN**。本轮 CPU 的候选值与新运行中的同类边界，只能补充因果证据，不能充当旧 tick 实测。Phase B 仍为 **COMPLETE / GPT REVIEW PASS / CLOSED**；已接受单机、分区双机范围保持，不自行宣布新的 GPT REVIEW PASS。

## 2. 本地 sensor 更新时间和读取链

本次定向阅读了当前仓库 SensorBase/ContactSensor，并只读核对当前环境的 PyTorch 加法相关头文件；没有修改或导入运行 Isaac 的 sensor 核心。

| 本地位置 | 已确认的语义 |
|---|---|
| `source/isaaclab/isaaclab/sensors/sensor_base.py:229–231` | timestamp 用 `torch.zeros(..., device=...)` 创建，last_update 用 zeros_like；此处没有显式 dtype，实际 dtype 必须读取 tensor，不能由静态源码直接断言恒为 float32。 |
| 同文件 `197–205` | 每次 `update(dt)` 执行一次 `_timestamp += dt`，按 update_period 标记 outdated；force_recompute 触发 buffer 更新。 |
| 同文件 `287–296` | 先调用实际 `_update_buffers_impl`，再把 last_update 写为当前 timestamp，最后清除 outdated。 |
| `contact_sensor/contact_sensor.py:104–107`、`320–338` | data 属性存在惰性更新；实现读取 native net force 和 filtered force matrix。正常 force_recompute 已清除 outdated 时，随后的 data 属性不再重复刷新。 |
| 本机 `torch/include/ATen/TensorIterator.h:384–386`、`ATen/native/cuda/Loops.cuh:167–189` | wrapped scalar 经目标计算类型转换；这是静态转换路径证据，未执行 CUDA 来验证这些头文件。 |

项目 `_make_contacts` 保持 update_period=0、原过滤路径及每台七个独立 sensor。普通受控 tick 的顺序为：一次 `sensor.update(dt, force_recompute=True)` → 核对 native 路径/filter 映射 → 读取 `sensor.data.force_matrix_w` → 独立复制 timestamp/last_update/outdated → 数值、矩阵、设备、有限性及原力阈值检查。不是只证明 update 被调用，也不是只比较项目自行累加的计数。

初始化与同 tick 只读区分如下：

- 首次 baseline 必须 previous=None、dt 为 Python float 0.0，执行一次原初始化数据刷新。共享 profile 在 warm-zero 检查建立 baseline，写入原批准非零初态后不再建立第二 baseline；legacy 仍在原初始化位置建立一次。
- 普通 advance 必须已有有效快照，实际 dt 为 Python float `1.0/120.0`，每 sensor 一次 update/read/check。
- 显式 readonly 必须 dt=0.0、已有 baseline，并在 data 前确认 outdated=false，避免惰性读取偷偷修复陈旧 buffer；不计为新物理更新。
- claim、retreat、clear、换 owner 和逻辑 episode rebuild 都不重置 sensor 时间或资源 generation。失败不重新锚定 previous，也不追加刷新直到通过。
- finally 只汇总已保留的普通读取证据，不补 native getter。某台某 sensor 失败后，后续 sensor 未读部分保持未覆盖，不伪造完整十四 sensor 结果。

## 3. 最终数值契约与支持范围

新增纯 CPU helper `E/_cr12_contact_time.py`。它不读取/推进 sensor，也不写 SensorBase 状态。输入是独立不可变的 previous/current 快照，以及本次实际 dt：

```text
p = dtype(previous.timestamp)
d = dtype(actual_python_float_dt)
expected_next = add(p, d, dtype=dtype)
expected_two = add(expected_next, d, dtype=dtype)
要求 current.timestamp == expected_next
同时要求 0 < ULP(p) < d，且 p < expected_next < expected_two
```

两操作数显式转换到当前支持 dtype，再在该 dtype 下做一次加法，避免依赖 NumPy/Python 混合 scalar 的隐式提升。比较是**精确可表示值相等**，没有把 1e-6 放宽、没有默认 rtol、没有以 current 倒推 expected。prev 转成 Python float 只用于无损保存原可表示值，没有声称恢复已损失的精度。

当前明确支持 float32/float64、单 sensor shape=(1,)、CPU 数值测试或本任务 cuda:0 读取。要求 timestamp/last_update 有限、非负且确实可由声明 dtype 表示；二者 dtype/device/shape 一致，last_update 等于该次 timestamp，outdated=false。previous/current 的完整 body path、sensor object identity、资源 generation、dtype/device/shape 必须一致。generation 随 sensor 对象创建，不随 authority episode 改变。

不支持 dtype、无法区分零/一/两次更新的分辨率、错误 dt/reset/stale/身份或 shape 均拒绝。previous 只有在数值、映射、force 等所有检查通过后才提交。force 连续为零可以是合法数据；时间正常也不能抵消 NaN/Inf、错 filter 或禁止接触。

原 `abs(current-previous-dt)<=1e-6` 仅作为 shadow diagnostic，记录旧拒绝/新接受的同份样本，不参与放行。独立物理 clock 继续验证真实步进；sensor 累计量化时间不被强迫等于高精度 n×dt。当前证据不证明 PhysX 内部所有实现，也不虚构未暴露的 native frame ID。

## 4. 实现、诊断和记录修正

| 文件与当前关键位置 | 本轮变化 |
|---|---|
| `E/_cr12_contact_time.py:20,34,59,87` | 不可变 ContactTimeSnapshot、freeze_snapshot、元数据检查、validate_timestamp；精确递推及 JSON 安全诊断。 |
| `E/_cr12_runtime_support.py:585,599,608,637,772` | 每 sensor 独立资源 generation/previous；小 tensor 独立复制；有界样本保留；真实 update→data→check；只汇总缓存证据。 |
| 同文件 `1051–1113` | 保留共享 warm-zero 与 legacy 初始化位置，一次 baseline；非零初态写入不重锚 contact 时钟。 |
| `E/_cr12_scan_executor.py:696–706` | 将同 tick global step、physics clock、Host/robot/segment/phase 上下文送入原 contact 调用；原物理和收尾顺序保持。 |
| `E/_cr12_lifecycle_host.py:585–639,670–692` | 按当前操作/runner 状态设置 phase，向 contact 转发同 tick 上下文；原已发生物理步和部分块计数逻辑保持。 |
| `E/run_cr12_single_view_capture.py:738–751,845–864` | 显式区分 pre_release、release 返回值、post_release；失败不能编造 post-release 快照；保存已有 contact 摘要。 |
| `E/run_cr12_shared_task_handover.py:142,205` | 成功收尾调用共同 release 记录 helper，明确两时点；保留原共享业务顺序和最终验收。 |
| `L/repro/supervise_cr12_contact_retest.py:62,134,163,225,302,329,367,402` | 本轮独立最多三 App、明确局部修复证据、十四 sensor 覆盖、四层结论、退出合取；离线重分析只能写新输出，原结果不覆盖。 |

每 sensor 保存首次 baseline、32/64 秒附近最多各六个独立时间样本、首次旧新判据分歧、累计计数/极值、最后样本和首失败。样本包含实际 dtype/device/shape、dt 类型、previous/current/last_update、expected/差分误差、outdated、读到何阶段、有限性/映射/阈值子项、最大力与对应 filter，以及同 tick 的 robot/Host/segment 上下文；不逐 tick 落盘十四套 force 矩阵。

异常时先冻结已有样本，NOT_READ/UNKNOWN 不替换成零或通过；诊断/序列化失败不能覆盖先发生的 native 或检查异常。原 `forbidden_contact >0.1 N` 和其余检查不变。failure.phase 从实时状态产生，不固定改写成 retreat。兼容字段 camera_backend 明确标为 pre_release，另存独立 post_release；旧历史文件不改。

记录格式的小差异保留为事实：baseline context.run_id记录完整output目录，受控tick记录目录名attempt_01；二者关联同次输出。样本身份和代际检查使用完整body路径、sensor对象ID和resource generation，不以这个展示字段作为身份替代。本次未为统一格式在成功运行后再修改代码。

## 5. CPU 检查、局部工程修正与版本冻结

最终 **53 项独立检查通过**，重复运行不累加为新增项。这些是 CPU 行为、fake API/文件证据和真实生产函数接线验证，不是 53 次仿真、GPU 或原生 sensor 验证。

| 分组 | 独立项 | 结果与覆盖 |
|---|---:|---|
| 数值契约 | 13 | 最终 13/13，3.36 s；实际 torch CPU float32/float64 add_，长时、边界、真陈旧、身份/快照/分辨率反例。 |
| 真实项目 contact 调用链 | 11 | 最终 11/11，2.008 s；生产函数+fake sensor，单次 update/read、零力合法、错数据/映射/力、同 tick readonly、失败保留。 |
| 本轮监督 | 16 | 最终 16/16，0.130 s；synthetic 元数据/文件 fixtures，转发、三 App/修复预算、十四 sensor、内部失败不可被 exit0 覆盖、原始失败保留。 |
| phase/release 记录 | 5 | 与下列两个 Host 用例合跑，合计 7/7，7.23 s；动态 phase、已发生失败步、独立 release 前后快照及失败。 |
| 必要 Host 回归 | 2 | 实际 CPU Host/authority/terminal 接线，物理和相机为测试替身；共享 cancel→clear→R→B→C 与旧 normal terminal。 |
| 旧 ContactTests | 4 | 与下列初始化用例合跑，合计 6/6，0.032 s；保留真正 stale、错误路径/filter 和禁止力反例。 |
| 必要初始化回归 | 2 | 非零写入一次/warm contact，以及 legacy 零态初始化不变。 |
| **合计** | **53** | 无旧 64/202/182/36 全套或 9000 tick 几何重跑。 |

数值测试从零开始，在两 dtype 各执行 **13800 次实际 CPU add_**，对应名义物理时长 **115 秒**；不声称 float32 累计 timestamp 恰好为 115。另在 32、64、128 秒附近各 dtype 各 16 次，共 96 个边界更新样本。零/两次更新、错误 dt、stale last_update/outdated、倒退/reset、NaN/Inf、错身份/shape/device、buffer 别名和分辨率不足均有拒绝例。

从零/float32/dt=1/120 的 CPU 序列中，旧 shadow 首次拒绝为 **3842**；float64 在本测试区间无旧拒绝。候选 previous=`32.007930755615234`、next=`32.016265869140625` 的旧误差为 `1.7801920572917823e-6` 秒，新精确递推接受。此数值示例明确是复现假设，不是旧运行失败 tick 的 current 实测。

App 前，Codex 自主完成了必要的局部工程修正：失败时仍保留可计算的时间误差；readonly 检查先拒绝 outdated，避免 data 惰性刷新；更新 CPU fixtures 和阶段/资源记录接线。preflight 准备脚本还曾把数值证据顶层 `passed` 误读为 `all_passed`，发生一次离线 KeyError；改读已有 `passed` 后成功。监督 preflight 中 `contact_numeric_contract.all_passed` 是汇总字段，样本及 CPU 证据的 `passed` 不改名。此修正不改旧证据，不创建 App/attempt，也不消耗 App 额度。

最终 preflight 保存 **23 份直接代码输入、14 份物理输入**的哈希，并记录 **14 个 Python 路径语法检查**通过。它冻结具体 attempt 的代码，而不是全仓 inventory；不同计数集合可能包含同一文件，不能相加宣称 37 个独立文件。数值证据 SHA256 为 `164cd695b46f4adab6e9591f387e8212b100150e9c8d2d7cf57d8b61119a6d88`。App 开始后代码、监督器和 preflight 全部冻结。

### 5.1 实际 CPU 命令

以下均已执行且 exit0，不是建议重跑命令。除专门注明外，cwd 为 `E:\Project\IsaacLab_HARL`。解释器已在测试前用 conda run 的 sys.executable 输出核对为本报告所列环境。

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B -m pytest -q source/isaaclab_tasks/test/test_cr12_contact_time.py

& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B -m unittest discover -s source/isaaclab_tasks/test -p test_cr12_contact_runtime.py -v

& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -B source/isaaclab_tasks/test/test_cr12_contact_retest_supervisor.py

& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B -X utf8 -m pytest -q source/isaaclab_tasks/test/test_cr12_contact_reporting.py source/isaaclab_tasks/test/test_cr12_shared_lifecycle_host.py::SharedHostTests::test_full_real_host_cancel_bound_retreat_clear_R_B_C_sidecar_ACK source/isaaclab_tasks/test/test_cr12_lifecycle_host.py::FullHostTests::test_normal_real_authority_and_terminal_transport
```

以下 6 项回归实际 cwd 为 `E:\Project\IsaacLab_HARL\source\isaaclab_tasks\test`：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -B -m unittest -v test_cr12_dual_runtime_support.ContactTests test_cr12_shared_runtime.SharedRuntimeTests.test_nonzero_write_once_readback_and_warm_contact_distinction test_cr12_shared_runtime.SharedRuntimeTests.test_legacy_still_writes_zero_and_checks_contacts
```

各 owner 实际执行的局部语法命令（cwd 仓库根）：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -m py_compile scripts/environments/_cr12_contact_time.py source/isaaclab_tasks/test/test_cr12_contact_time.py

& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -m py_compile scripts/environments/_cr12_runtime_support.py source/isaaclab_tasks/test/test_cr12_contact_runtime.py source/isaaclab_tasks/test/test_cr12_dual_runtime_support.py

& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -m py_compile logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/supervise_cr12_contact_retest.py source/isaaclab_tasks/test/test_cr12_contact_retest_supervisor.py
```

## 6. 实际监督启动和有界预算

主代理从仓库根实际启动的监督命令：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/supervise_cr12_contact_retest.py --attempt-dir logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01 --integration-case shared_cancel_clear_handover --preflight logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/preflight_attempt_01.json
```

`attempt_01/command.json` 记录于 **2026-10-09T11:03:27.795+08:00**。其真实子进程 argv 对应完整 PowerShell 命令如下；由监督器管理，不能用直接命令绕过所属树和预算：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_shared_task_handover.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261009_cr12_contact_precision_retest\attempt_01' --device cuda:0 --external-forces-every-iteration on --enable_cameras --info --integration-case shared_cancel_clear_handover --gui-startup-diagnostics '--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/private_config/user.config.json --/app/window/scaleToMonitor=false --/app/window/dpiScaleOverride=1.0'
```

子进程仅覆盖 `PYTHONUTF8=1, HEADLESS=0, ENABLE_CAMERAS=1, LIVESTREAM=0, XR=0`；不写持久环境。沿用已接受 Windows helper 的 D3D12 选择、pre-App CUDA、pre-init visual/Fabric 和独立 private 配置，真实 source 只读。本次实际读回 D3D12、窗口 1440×900、renderer 1280×720；12 项 GUI 启动判据全部通过，source 内容/大小/mtime 保持不变。此结果不重新调查 Windows 根因或推广默认设置。

| 边界 | 本轮上限或规则 |
|---|---|
| App | 主 1＋明确局部修复最多 2，总数最多 3；开始构造即计入，零步失败也计数；无自动循环。 |
| 构造/全树 | 180 / 2400 秒；工作段 2390 秒，余量用于所属树收尾。 |
| 物理/Host | setup≤360，Host≤1120 transitions，task physics≤13440，总受控≤13800，warm2另计。 |
| 动作/采集 | 三动作各≤3840；capture≤600 tick/60 秒 wall，close≤240 tick/30 秒 wall；受控 render≤6900。 |
| 绑定 | A≤8520、B≤4680，原块尾余量不变。 |
| 进程/重试 | owned Job、bytes 实时排空、同次 Kit 定位；只管理所属树。每次新进程/输出/private，前树退出后才允许新 attempt。 |

真实禁止接触、几何/actual 管道越界、控制失稳、数据有效性仍不明、native access violation/device-lost/OOM、需要改变核心语义或额度耗尽，均停止后续 runtime。只有有直接证据的局部实现/记录/监督错误可按本轮授权修复；不得把未解释安全异常先归成误报。完整通过立即停止，剩余额度不用于更多 case。

## 7. 本轮实际运行和完整转交结果

### 7.1 唯一 attempt、代码版本与分层结果

`attempt_01` 于 **2026-10-09 11:03:27.796+08:00** 开始，**11:28:10.578+08:00** 全树结束。Conda PID14220、目标 Python PID30228；实际 Kit 日志是同次 `kit_20261009_110331.log`，日志中 `03:xx` 为 UTC，与本地时间差八小时。构造20.328秒/上限180秒，全树1482.765秒/上限2400秒；目标和内层Conda exit0，监督命令exit0，全部所属进程退出，timeout=false、termination_requested=false、native_fault_evidence=[]、supervisor_errors=[]，主/次要运行失败均空。

| 结果层 | 本轮状态 | 直接支持 |
|---|---|---|
| CONTACT_NUMERIC_CONTRACT | PASS | 精确 dtype 递推、115秒CPU长时/128秒局部样例与真陈旧反例；生产函数接线和数值证据哈希绑定。 |
| CONTACT_RUNTIME_FRESHNESS | PASS | 14 sensor 各9353次真实受控更新，32/64秒跨界样本、last/outdated/force/mapping/shape检查完整。 |
| SHARED_HANDOVER_EXECUTION | PASS | 同一App完成原A取消/OFF/退出/clear-R、B同task新claim/fresh/OFF/C，唯一完成归属[0,1]。 |
| TERMINAL_AND_SHUTDOWN | PASS | 71维sidecar、共同terminal/rebuild/ACK、两机release和自然退出。 |

原监督11组业务/退出条件全部true，含setup_mapping、nonzero_setup、host_and_authority、a_cancel_off、clear_release_handover、b_fresh_off、resource_continuity、terminal_transport、pose_and_physics、artifact_delivery_pass、work_and_exit；不是只读PASS标题或exit0作结论。

本次运行代码版本是当前HEAD加既有未提交实现及本轮局部补丁，不能仅由HEAD复原。23份直接输入及14份物理输入在运行前冻结、运行后全部一致；profile、pose_control、camera_mount也与上轮preflight相同。完整哈希见本轮preflight，关键标识如下：

| 项目 | SHA256 |
|---|---|
| `L/repro/preflight_attempt_01.json` | `301c4af2e256316404778c5b8c0d8c12b360d461e2e1ed7be3e4d5d3625b6e4b` |
| `_cr12_contact_time.py` | `81fba40356b786707a57b8ad235a80c68c2ba0cc0224b432c885edf87263d2ca` |
| `_cr12_runtime_support.py` | `1251b39c729d442b6b7b6a4bd610e851dfdeadc525f102b4a2023cc5c3c193ed` |
| `_cr12_shared_task_profile.py` | `f9b556cbba13b386f8f4462cb071bbdccae86f5325bb6b514ffb5d981b5ae2cb` |
| 本轮supervisor | `e9a736abc9858bef3c12dea24157c5eb9c736b136da9ef736f4a23a59d891045` |

没有运行失败后的代码修复或第二App，也没有离线重分析把失败改判成功。第5节preflight字段对齐是本轮自主完成的离线工程修复，不消耗App。一次旁路查看运行中的result碰到正在写入的半份JSON，读取失败；未修改生产写入/物理流程，最终全树退出后重读完整证据，未把这次旁路解析错误归为仿真故障。仅存在attempt_01，未创建attempt_02/03。

### 7.2 实际 dtype、每sensor覆盖与两个时钟

两台的 `agv、link_1…link_6` 均实际读回 timestamp/last_update=`float32/cuda:0/[1]`，outdated=`bool/cuda:0/[1]`。每个baseline=1、advance=9353、readonly=0、update_call=9354、check_attempt=9354，first_failure=null。正常受控总更新 **130942**，加各自一次baseline后的总update调用 **130956**；没有换owner/rebuild重锚或额外补刷。

下表列出全部14个资源的独立generation前缀；每格均代表上述相同完整覆盖、32/64秒通过和0个失败，完整body路径、对象ID/generation在原JSON各自记录中：

| body | A / Robot0 generation | B / Robot1 generation | 每个advance / update / check |
|---|---|---|---|
| agv | 974e76de | 18d2cec3 | 9353 / 9354 / 9354 |
| link_1 | d44db015 | 41f815bf | 9353 / 9354 / 9354 |
| link_2 | 1b16c1d6 | a7c63c6b | 9353 / 9354 / 9354 |
| link_3 | dafb8af9 | bd702531 | 9353 / 9354 / 9354 |
| link_4 | e55ec389 | a6871638 | 9353 / 9354 / 9354 |
| link_5 | 9ee46089 | abb2ec22 | 9353 / 9354 / 9354 |
| link_6 | 85ff8678 | 05aad43c | 9353 / 9354 / 9354 |

14个对象/generation互异，各自baseline→分歧样本→last身份不变。实际filtered force matrix为torch.float32/cuda:0：agv及link_1…5 shape `[1,1,12,3]`，link_6 `[1,1,13,3]`；映射、有限性、设备和原0.1N检查全部通过，各最大filtered禁止接触力均 **0 N**。这不涵盖获准豁免的接触，也不是对native内部所有接触实现的额外证明。

全部14个sensor保留的下列样本数值一致，均 `current=expected_next=last_update`、expected_error=0、outdated=false、新判据PASS、filtered力0N：

| 邻域 | global step | sensor current / 秒 | 旧增量误差 / 秒 | old shadow |
|---|---:|---:|---:|---|
| 32 | 3838 | 31.98293113708496 | 1.2715657552071769e-7 | PASS |
| 32 | 3839 | 31.99126434326172 | 1.2715657552071769e-7 | PASS |
| 32 | 3840 | 31.999597549438477 | 1.2715657552071769e-7 | PASS |
| 32 | 3841 | 32.007930755615234 | 1.2715657552071769e-7 | PASS |
| 32 | 3842 | 32.016265869140625 | 1.7801920572917823e-6 | FAIL |
| 64 | 7678 | 63.98976135253906 | 1.7801920572917823e-6 | FAIL |
| 64 | 7679 | 63.99809646606445 | 1.7801920572917823e-6 | FAIL |
| 64 | 7680 | 64.00643157958984 | 1.7801920572917823e-6 | FAIL |
| 64 | 7681 | 64.01476287841797 | 2.0345052083332177e-6 | FAIL |

首次分歧global3842：previous=32.007930755615234，实际增量0.008335113525390625，float32表示的dt=0.008333333767950535，expected=current=32.016265869140625；若两次更新预期为32.024600982666016，零次则仍为previous，均不会通过。对应独立物理clock `[3844,32.033335004001856]`，A阶段RETREATING_BOUND、B阶段IDLE_HOLD；64秒邻域则A为IDLE_HOLD、B为APPROACHING。本次实测和CPU均支持原1e-6增量谓词会拒绝合法float32更新，但旧失败tick缺失的last/outdated/force仍不能补写，更不能排除当时未保存的其他拒绝子项。

sensor基线为0，独立physics基线为 `[2,0.01666666753590107]`。最终sensor累加 **77.94469451904297秒**；绝对physics `[9355,77.95833739917725]`，扣初始化后的实际受控时间 **77.94167073164135秒**；sensor−受控physics=**+0.0030237874016165733秒**。这是有来源的累计量化差，不是物理时钟被调快，也未强行要求两者相等。实际runtime只运行9353次，并未跑满CPU的13800次/115秒范围。

### 7.3 同一App的完整业务时序

| 全局受控步 | 事实 | authority/数据边界 |
|---:|---|---|
| 221 | 共同setup保持完成，121样本/1.000000052秒；随后A真实claim0/task0 | setup期间claim=0、authority transition=0。 |
| 3221 | A局部3000步到位，稳定后真实ON，进入WAITING_DATA；下一次physics/render之前取消 | 尚无本次数据；仍由A持有原绑定。 |
| 3280 | A无数据取消终态，OFF确认；close59步/首次30render，约9.605秒wall | acquired=false、raw不存在、无PNG；同claim/controller/integrator/trust开始退出，pending仍空。 |
| 6280 | 退出局部3000步，POSE_REACHED且CLEAR_HOLD_READY | 实际固定clear检查成立后才有提交资格。 |
| 6281 | 多1个块尾步复核clear，提交真实R；receipt送达后退役；随后B新claim1/task0 | A先AVAILABLE/unowned，完成计数[0,0]；B准入检查A OFF/clear/退役。同一个冻结scanner目标。 |
| 9281 | B局部3000步到位并真实ON | 尚无成功回执。 |
| 9282 | 实际取得唯一新帧，随后请求OFF | 本次acquired=true；capture等待1步，保存/关闭/authority分开记录。 |
| 9342 | B独立OFF确认；close60步/首次30render，约8.428秒wall | 数据继续保留，禁止未确认OFF时转入下一动作。 |
| 9353 | 多11个块尾保持/复核，C回执后退役，共同terminal、逻辑rebuild和facade ACK | 唯一累计完成归属[0,1]；无永久failed-pair。 |

A最终clear窗global6027–6281累计255样本/2.116666777秒；进入局部邻域并不提前取得资格，仍需原pose monitor在6280完成。块末clear位置误差2.94443716e-5m、姿态误差7.06563578e-6rad、park关节最大误差2.82249625e-5rad、最大实际速度5.55915103e-5rad/s。之前3281–6269的250条块末记录保持RETREATING_BOUND/holding=false/no_data=true，无提前R。

A的真实R为facts_consume_token504、receipt505、transition_generation504；B的C为token760、receipt761、generation760。Host共 **761 transitions/transactions、2次bind、759次continuation、2次delivery**，9353=setup221+761×12，task physics=9132、partial block=0；受控render=4676，warm2另计native总步9355。

两机clock/joint/contact/geometry/frame/render_clock六守卫均各9353次通过，native参数、visual预初始化和安装检查通过；原实际几何/跨机检查没有被跳过。原资产保护8项通过，未靠teleport、代理tensor或修改布局完成运行。本case没有真实构件，不把通过扩大为任意构件避障。

### 7.4 B唯一实际数据、terminal与资源收尾

B唯一图片：[camera_rgba.png](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/robot_1/task_0/claim_1/camera_rgba.png)，640×480 RGBA、90318字节，实文件SHA256=`82bb442952b40e916531d177f569cc392b0a893e58de10e585d6b2b5ac354743`，与result和metadata一致。A没有PNG、raw或该次product数据事件；没有为取消记录生成占位图。

B rendering_frame=4815，source_time=160.5；相对ON时source_time160.4666667更新了1/30秒，在受控9282/native9284收到，rendering/receive simulation_time=77.366670702秒。source时钟与physics时钟不同，不直接比较绝对数值；接收位姿也不宣称是精确曝光位姿。新帧、所属product/request和不可变raw custody依据保留；未增加任何深度比例、分割、重建或质量门槛。

共同terminated=true、truncated=false，pre-reset完成数 `[0,1]`、failed_pairs全false；历史terminal行1，critic/audit sidecar为71维，facade ACK后pending=0。logical rebuild episode_generation由0到1、transition_generation保持760，前后clock同为 `[9355,77.95833739917725]`，两机q/dq/q_cmd/scanner逐值相同；重建未重置或推进物理。

每机prepare/initialize/begin/OFF-confirm/retire各一次。`camera_backend_snapshot_at=pre_release` 的副本为released=false、release_calls/effective=0；独立 `camera_backend_post_release` 为released=true、两计数=1，camera_release.complete=true、errors=[]。两机都在simulation STOP前释放；STOP返回，App close已请求，然后目标和Conda自然exit0、所属树清空。原native快速退出方式没有留下app_close_returned字段，不能编造该字段，但完成记录和进程结束共同支持退出通过。

原日志仍有导入顺序、扩展/材质、RTx设置及关闭时hydratexture接口已释放等Warning；本轮console没有`[Error]`行，运行失败列表和监督native故障证据均空。未据这些Warning更改依赖、驱动或环境；本次通过不证明任意场景下它们均无影响。

## 8. 未改边界与结论限制

保持原 root、非零 park/goal、同一冻结 scanner 世界目标、24 秒 FK-witness reference、32 秒动作上限、轴2/5信任域、actual共同s管道/固定clear邻域、DLS/PD/effort/dt/solver/重力、原 AABB、过滤 pair、0.1 N 禁止接触阈值、640×480相机和取消/OFF规则。

未改 SensorBase/ContactSensor 核心、installed packages、torch default dtype、真实 sensor timestamp/last_update/outdated、资产/质量/惯量/碰撞体、Windows helper/驱动/真实 user.config、authority/consume-once/public event gate、学习器/reward/训练/checkpoint。没有通过缩短动作、清零时间、改 OBB、增大布局间距、跳过 agv/降低频率、伪造零力或重复刷新避开问题。

本轮 CPU 长时范围到名义115秒并局部覆盖128秒；不据此宣称任意时长/任意 dtype/任意 sensor 均可用。真实 runtime 只支持实际完成的区间；一般故障恢复、其他布局/目标、B→A反向、更多机器人、真实构件/实体设备和训练均未被代验。

## 9. 辅助证据对应表

`logs/` 下材料保留在本机，受既有忽略规则影响；不暗示新 checkout 自动包含，也未生成 ZIP、全仓 hash 或额外 ledger。表中证据用于核验，正文仍是主阅读入口。

| 结论/检查项 | 文件位置 | 关键定位 | 用途与限制 |
|---|---|---|---|
| 历史完整 FAIL 与已取得部分事实 | [上轮共享转交报告](CR12_SHARED_TASK_HANDOVER_IMPLEMENTATION_REPORT.md) | 唯一 App/global3842 | 保留当时状态，不回写。 |
| 纯数值实现 | [contact_time](../../../../../../../../scripts/environments/_cr12_contact_time.py) | freeze_snapshot / validate_timestamp | 精确递推、独立快照、支持范围。 |
| 实际项目 contact 链 | [runtime_support](../../../../../../../../scripts/environments/_cr12_runtime_support.py) | _check_contacts / _contact_summary | 一次读取及原有效性/力检查。 |
| 数值 CPU 测试与摘要 | [13项测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_contact_time.py)、[CPU证据](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/contact_numeric_cpu_evidence.json) | continuous / boundaries / negatives、source_sha256 | CPU语义证据，不是历史失败tick或GPU实测。 |
| 调用链、记录和监督反例 | [runtime测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_contact_runtime.py)、[reporting测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_contact_reporting.py)、[监督测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_contact_retest_supervisor.py) | 11 / 5 / 16项 | 直接生产函数或synthetic证据；无App。 |
| 本轮版本/输入冻结 | [preflight](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/preflight_attempt_01.json) | cpu_results、code_sha256、frozen_physics_inputs | 精确绑定App01前置状态。 |
| 本轮有界监督 | [supervisor](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/supervise_cr12_contact_retest.py) | budget_for_attempt / contact_runtime_checks / extend_result | 本轮三App上限、退出与完整业务合取。 |
| 实际启动命令 | [command.json](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/command.json) | argv、environment、budget_before | 已记录的命令事实；不是完成证据。 |
| 完整业务与每sensor原始记录 | [result.json](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/result.json) | instance_setup[*].contact_summary、shared_handover、requests、terminal_history、camera_backend_pre/post_release | 同一attempt的数值/业务/资源事实；没有旧失败tick缺失字段。 |
| 四层判定和自然退出 | [supervisor_result.json](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/supervisor_result.json) | validation_layers、completion_checks、contact_runtime_checks、exit/PID/budget | 完成记录与进程退出共同判定，App1/3。 |
| 同次原日志 | [console](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/console.log)、[Kit](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/kit_20261009_110331.log) | 本地11:03–11:28 / UTC03:03–03:28、真实stage与Graphics API | 时序和原Warning保留，不另造日志副本。 |
| B唯一采集 | [PNG](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/robot_1/task_0/claim_1/camera_rgba.png)、[metadata](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/robot_1/task_0/claim_1/capture_metadata.json) | frame4815、claim1、fresh/OFF/receipt、PNG/raw摘要 | 实际取得、保存与关闭各自核对；A无图片。 |
| 配置只读保护 | [config_runtime_summary](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/attempt_01/config_runtime_summary.json) | source_unchanged、private、期望/实际argv | 独立private/source保护；不展示无关个人配置。 |

## 10. 变更交接与停止状态

本轮生产变更：新增`E/_cr12_contact_time.py`；局部修改`_cr12_runtime_support.py`、`_cr12_scan_executor.py`、`_cr12_lifecycle_host.py`、`run_cr12_single_view_capture.py`、`run_cr12_shared_task_handover.py`。正式测试新增`test_cr12_contact_time.py`、`test_cr12_contact_runtime.py`、`test_cr12_contact_reporting.py`、`test_cr12_contact_retest_supervisor.py`，适配`test_cr12_dual_runtime_support.py`的直接ContactTests和`test_cr12_scan_executor.py`的调用夹具；未删除真正陈旧/安全断言。supervisor及一次性preflight准备放L/repro，没有把Python放入报告目录。保留所有先前单机/双机/共享任务/启动实现和原dirty worktree。

文档仅新增本文，小范围更新[任务进度](../../TASK_PROGRESS.md)和[主题导航](../../REPORT_INDEX.md)；旧主报告、原失败输出及历史接受范围不回写。收尾核对本轮文件及输入冻结，本文22个本地链接存在、两处新导航到达本文、无PENDING草稿或行末空白；相关tracked文件的`git diff --check`通过，仅提示既有LF/CRLF自动转换规则。未跑历史全目录库存/链接审计，未stage/commit/push或任何Git写操作，未清理、恢复或重建旧数据。

本任务已完整通过授权的固定case，没有需要立即改变路线的实施决策；下一步是GPT/用户审阅本文与必要原始证据。长期数值精度、一般故障恢复、其他任务/布局/机器人、真实构件、实体和训练均仍在本轮范围之外。本轮成功即停止，不为用满剩余2个App补跑，也不自动进入后续研究阶段。

