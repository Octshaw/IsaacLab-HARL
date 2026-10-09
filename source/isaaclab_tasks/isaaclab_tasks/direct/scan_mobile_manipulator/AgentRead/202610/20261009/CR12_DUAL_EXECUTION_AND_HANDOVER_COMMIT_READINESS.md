# CR12 双机执行与共享任务转交：阶段收口与提交准备

日期：2026-10-09（Asia/Shanghai，UTC+08:00）。仓库：`E:\Project\IsaacLab_HARL`。
本轮状态：**READY FOR MANUAL COMMIT；未暂存、未提交；App=0、测试运行=0。**

## 1. 结论与接受边界

已具备在当前机器上保存本阶段代码基线的手动提交条件，推荐一个 commit。下文清单共 **45 个文件**：15 份生产源码、17 份常规测试、4 份必要监督/helper Python、9 份 Markdown。本轮只新增本报告、局部更新 TASK_PROGRESS 和 REPORT_INDEX；生产、测试、资产及既有六份阶段报告未改。

用户本轮明确确认 **CR12_CONTACT_PRECISION_AND_HANDOVER_RETEST — GPT REVIEW PASS**。接受范围为：

- 固定 E1/M2/N4 分区双机：并行执行、独立按需采集、共同生命周期终态。
- 固定 E1/M2/N1 shared_m2n1：A 在稳定 WAITING_DATA 无数据取消并确认 OFF，保留 claim 实际退出；fixed clear 后提交 R，真实 receipt 后退役；B 用新 claim 接同一冻结 task0/scanner 世界位姿，取得真实 RGBA、OFF、C；唯一完成归属 [0,1]、terminal/rebuild/ACK 和自然退出。
- contact 按实际 dtype 精确递推；14 个 float32/cuda:0 sensor 在此次 **9353 受控步**中的有效性与新鲜度检查。真实跨越 32/64 秒；115/128 秒仅有既有 CPU 样例，不写成真实运行覆盖。

这些是 **private fixed-cardinality execution fixtures，deterministic proposals**；取消发生在仍能受控运动的稳定等待阶段，不证明失去运动能力后的接管、任意布局/路径、一般故障恢复、反向转交或策略性能。训练、可变规模 checkpoint、真实构件/设备不在本阶段接受范围。**Phase B COMPLETE / GPT REVIEW PASS / CLOSED；public entrypoint gates unchanged。**

旧 global3842 contact FAIL、旧 120×0 窗口 FAIL 及其未知字段 UNKNOWN 保留。历史报告的“等待审阅”正文不回写；最新接受状态由本报告及当前导航说明。Windows DPI 参数是显式成功启动条件，不是唯一根因结论或全入口默认值。

## 2. 当前 Git 状态与实际保存范围

本轮只读快照：

| 项目 | 事实 |
|---|---|
| branch / HEAD | `main` / `a8c618a32da65747827f1cb3f722fac24df2aec8` |
| HEAD subject | `feat(cr12): establish single-robot scan execution and lifecycle integration` |
| 最近历史 | 前一条 `e5f91b13` 同主题；再前为 `24ecbad7` Phase B 清理交接、`5e62cd58` 关闭记录、`947f9261` fresh-process continuation |
| 已暂存 | **0**；不存在 staged/worktree 同文件版本冲突或混入其他暂存项 |
| tracked 未暂存 | **14**：10 生产、2 测试、2 导航文档 |
| 非 ignored 新文件 | 开始时 **26**：5 生产、15 测试、6 阶段报告；新增本报告后 **27** |
| 必要 ignored 候选 | **4** 个精确 Python 路径，见第 7 节 |
| 归属不明或不相关修改 | 本轮查看的 Git 状态和定向依赖中未发现；没有据此推断整个 ignored 工作区均无其他文件 |
| 合并冲突 | `git ls-files -u` 空；候选 Python 未发现冲突标记 |

本次保存 HEAD 加目前已验证的组合工作区，不人为拆分同一 Host/runtime/runner 文件的单机、双机和共享 hunk。以下缩写均以仓库根为基准：

- `E/` = `scripts/environments/`
- `T/` = `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`
- `Q/` = `source/isaaclab_tasks/test/`

| 生产范围 | 精确文件（M=tracked 修改，U=新文件） |
|---|---|
| 双相机/逐请求采集 | M：`E/_cr12_camera_capture.py`、`E/_cr12_camera_mount.py`、`E/_cr12_capture_runner.py` |
| 多 binding、单事务聚合、receipt 后退役 | M：`E/_cr12_lifecycle_host.py`、`T/assignment_cr12_execution_adapter.py` |
| 共同时钟、物理/接触检查、非阻塞执行、setup/retreat | M：`E/_cr12_runtime_support.py`、`E/_cr12_scan_executor.py`、`E/_cr12_pose_control.py` |
| 共用请求/启动/记录路径 | M：`E/_cr12_single_view_capture.py`、`E/run_cr12_single_view_capture.py` |
| dtype 时间递推、固定 shared profile、可选启动观测 | U：`E/_cr12_contact_time.py`、`E/_cr12_shared_task_profile.py`、`E/_cr12_gui_startup_diagnostics.py` |
| 两个固定场景入口 | U：`E/run_cr12_dual_lifecycle_integration.py`、`E/run_cr12_shared_task_handover.py` |

测试为第 7 节列出的 17 个 Q 文件，其中 `test_cr12_runtime_support_hooks.py` 与 `test_cr12_scan_executor.py` 是 M，其余 15 个是 U。前两者更新 mock/fixture 以适配实例、world/contact 与段参数；本轮没有修改测试或删除断言。

文档为第 7 节的九个 Markdown：TASK_PROGRESS、REPORT_INDEX，10-08 的双机设计/实施、启动复测、共享方案四份，10-09 的共享首次实施、contact 完整复测、本收口报告三份。计划和旧失败报告也应保存，以保留来源与边界。

## 3. 依赖完整性与不纳入的前置

### A. 正式源码/配置

两个入口分别在 `E/run_cr12_dual_lifecycle_integration.py:227` 和 `E/run_cr12_shared_task_handover.py:243` 调用共用 `run_cr12_single_view_capture.main:753`。对本地 imports、动态路径载入作定向 AST/文本追踪，覆盖 47 个 E/T 生产源码：15 个在候选中，其余已在 HEAD、当前未改；没有发现生产入口导入或读取仓库 logs/AgentRead 的一次性脚本。

必须纳入 `_cr12_shared_task_profile.py`：`_cr12_lifecycle_host.py:73` 构造时直接导入，遗漏会影响旧 Host 路径；`_cr12_runtime_support.py:646` 直接使用新 `_cr12_contact_time.py`，不能仅提交调用方。

该闭包中 **32 个已在 HEAD、未修改、无需重复 add** 的路径如下（E/T 缩写见第 2 节）：

```text
E/_cr12_asset_math.py
E/_cr12_collision_refinement.py
E/_cr12_external_forces.py
E/_cr12_hold_diagnostics.py
E/_cr12_manual_joint_sweep.py
E/_cr12_pose_continuation.py
E/_cr12_pose_visuals.py
E/_cr12_visual_geometry.py
E/_cr12_visual_source.py
E/_windows_runtime_startup.py
E/prepare_cr12_fixed_asset.py
E/run_cr12_lifecycle_integration.py
E/run_cr12_manual_joint_sweep.py
E/run_cr12_pose_target.py
E/view_scan_assignment.py
T/assignment_controller.py
T/assignment_event_contract.py
T/assignment_event_policy_evidence.py
T/assignment_event_profile_runtime_domain.py
T/assignment_event_profile_schema_contract_v2.py
T/assignment_event_profile_synchronous_runtime.py
T/assignment_event_proposal_adapter.py
T/assignment_event_runtime_facade.py
T/assignment_event_terminal_critic_sidecar.py
T/assignment_event_terminal_transport.py
T/assignment_initial_claim_runtime.py
T/assignment_interstep_claim_window_runtime.py
T/assignment_lifecycle_authority_runtime.py
T/assignment_lifecycle_transaction_runtime.py
T/assignment_lifecycle_transition_contract.py
T/assignment_profile_contract.py
T/assignment_rl_interface.py
```

另外核对的既有前置也无需 add：`source/isaaclab_assets/isaaclab_assets/robots/rokea_cr12.py`、`apps/isaaclab.python.rendering.kit`、`.gitignore`、`.gitattributes`；它们不计入上述 47 个 E/T 源码。

D3D12 缺省来自既有 Windows helper。显式 DPI 候选来自 `logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/supervise_cr12_dual_gui_startup.py:45,73–81` 的 CLI：`scaleToMonitor=false`、`dpiScaleOverride=1.0`，shared/contact 监督器继承它。共用生产入口的诊断选项及采样（`run_cr12_single_view_capture.py:28,789–796`）和诊断模块 `:315–317` 是检查，不会注入 DPI 默认值。不得把直接裸跑入口等同于既有完整成功启动命令。

### B. 必要测试/复现脚本

`Q/test_cr12_contact_retest_supervisor.py:12` 与 `Q/test_cr12_shared_supervisor.py:12` 按路径引用如下闭包，**四个都需要保存**：

```text
20261009_cr12_contact_precision_retest/repro/supervise_cr12_contact_retest.py
  → 20261009_cr12_shared_task_handover/repro/supervise_cr12_shared_task.py
  → 20261008_cr12_dual_gui_startup/repro/supervise_cr12_dual_gui_startup.py
  → 20261008_cr12_dual_gui_startup/repro/prepare_private_user_config.py
（统一前缀：logs/scan_assignment/）
```

传递引用见 contact 监督器 :21–24、shared :28–31、dual GUI :61–67；shared :26 还引用候选 `E/_cr12_shared_task_profile.py`。四者均由 `.gitignore:64` 的 `**/logs/*` 忽略，本次仅建议逐文件 `git add -f`，保持原路径/代码、不改忽略规则。

导入阶段仅载入 Python/profile、构造路径/常量/正则与引用；实际 JSON/private config/Kit 读取、WinDLL/Popen/App 均在显式运行函数中。上述两份 Q 测试用临时目录构造 fixture 结果和 PNG，不依赖已有真实 attempt JSON。其他相关测试仍需要项目包、NumPy/CPU torch 或 HEAD 中的派生 URDF；本轮未执行测试，不能声称无依赖发布或所有新 checkout 自足。

本地 repro 中旧 `test_startup_supervisor_cpu.py`、`test_supervisor_cpu.py`、`compare_startup_inputs.py` 不属于本次 Q 常规测试闭包，未纳入；前者存在旧 AST 源码对照、后者读取历史 attempt 输入，不能把它们当成通用新 checkout 测试。一次性 `prepare_contact_preflight.py` 也非本次测试导入依赖，保留本地、不提交。未加入 skip 掩盖本地前置。

监督器的历史 result/preflight、已使用 attempt 额度与 Python 源码是不同类别。提交四份源码**不恢复运行额度、不授权再执行、不保证新 checkout 可直接重放旧 case**；保留原 gate、预算和真实前置，不制作假 PASS 输入。

### C. 既有环境/资产

| 前置 | 当前状态与处理 |
|---|---|
| Python / Isaac 环境 | 本轮核对解释器为 `C:\isaacenvs\isaac45_harl\python.exe`；使用 `D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl`。未导入 Isaac/torch、未变更包/驱动/配置 |
| 用户配置输入 | 监督器明确引用本机 `C:/isaacenvs/isaac45_harl/Lib/site-packages/omni/data/Kit/Isaac-Sim/4.5/user.config.json`；文件存在，private 副本由既有 helper 准备；原配置及 private 内容不提交 |
| 原 URDF | `T/assets/rokeaCR12/rokea_cr12_7DOF.urdf` 已在 HEAD、未改 |
| v1 派生源与配置 | `T/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf`、同目录 `usd/.asset_hash`、`usd/config.yaml` 已在 HEAD、未改 |
| mesh | 派生 URDF 的 20 条 OBJ 引用均存在，已由 HEAD 的 LFS 指针管理，本机有展开数据；新机器仍需取得 LFS payload，本轮不安装 LFS 或重复 add |
| 实际 USD 引用层 | 下列四份存在于本机，**未在 HEAD**，由 `.gitignore:12` 的 `**/*.usd` 忽略；本次不加入大资产、不导入/转换 |

四份本机 USD 的准确相对路径（统一前缀 `T/assets/rokeaCR12/derived/fixed_lift0_v1/usd/`）：

- `cr12_fixed_lift0.usd`（3170 bytes）
- `configuration/cr12_fixed_lift0_base.usd`（4231823 bytes）
- `configuration/cr12_fixed_lift0_physics.usd`（4193 bytes）
- `configuration/cr12_fixed_lift0_sensor.usd`（670 bytes）

这些是已有准备流程 `E/prepare_cr12_fixed_asset.py` 产生并被既有运行使用的本机前置；HEAD 中有准备入口/派生 URDF/config，但不等于 Git 已保存四个 USD。`.gitattributes` 的 LFS 规则也不等于实际 tracked。**本次 commit 能保存代码基线，单独新 checkout 不能据此直接运行机器人。** 跨机器资产提供或重新派生需以后单独决定；本轮不重新生成，亦不承诺重导出字节相同。用户删除的旧原始 USD 不恢复。

### D. 本地证据：保留，但不纳入 commit

下表路径都以 `logs/scan_assignment/` 为前缀；本轮只定向确认/读取，未复制、移动、删除或压缩。

| 保留位置 | 用途 |
|---|---|
| `20261008_cr12_dual_gui_startup/attempt_01/`，同 topic `repro/preflight.json` | 已接受 M2/N4 成功：结果、四份采集、console/Kit/启动与退出证据 |
| `20261009_cr12_contact_precision_retest/attempt_01/` | 最新共享完整成功：唯一 B 采集、逐阶段与传感器摘要、自然退出 |
| `20261009_cr12_contact_precision_retest/repro/preflight_attempt_01.json`、`contact_numeric_cpu_evidence.json` | 最新 23 份代码来源、dtype 数值对照；CPU 长时间样例与真实运行分开 |
| `20261008_cr12_dual_lifecycle_integration/attempt_01/` | 原 120×0 启动 FAIL，不回写 |
| `20261009_cr12_shared_task_handover/attempt_01/`，同 topic `repro/preflight.json` | 原 global3842 contact FAIL 及当时 setup/A/OFF 事实、缺失字段 UNKNOWN |
| `20261009_cr12_shared_task_handover/repro/nominal_aabb_admission.json` | 已有名义三段几何前置，只读保留 |

PNG、result/preflight JSON、raw、console/Kit 大日志、private user.config、缓存/pyc/视频以及其他历史 repro 不在第 7 节清单中。不提交整个 logs，不新建证据包。历史报告中的本机证据链接继续有效于此机器，**不会随 Git 源码自动提供**。已授权删除的旧 smoke checkpoint/raw 不恢复、不重新审计。

## 4. 接受版本与当前内容的对应

最新成功运行不是 HEAD 单独运行，而是 **HEAD + 当时工作区 + 本机依赖**。使用已有 `preflight_attempt_01.json` 的直接输入清单作一次有限原始字节 SHA256 对照：**23/23 与当前文件完全相同**。

| 最新 23 项在当前仓库中的状态 | 数量 |
|---|---:|
| 已在 HEAD、未改：单机 lifecycle/pose 入口和三个既有 event 支持模块 | 5 |
| tracked 未暂存生产修改（本报告的全部 10 个 M） | 10 |
| 新源码：contact_time、gui_startup_diagnostics、shared_task_profile、shared 入口 | 4 |
| 必要 ignored 监督/helper 闭包 | 4 |

未把 14 份物理输入扩成新的资产哈希审计。另仅针对最新 23 项未涵盖的双机入口，与其成功 `20261008_cr12_dual_gui_startup/attempt_01/preflight.json` 对照，当前原始 SHA256 为 `38a7e9a6c780eb19fc5390ffaf60ef9295910c4f6f972726cc3811748c413809`，一致。GUI 诊断模块在最新 23 项中，当前/双机成功/最新 contact 三者一致（`8ebe63ce8627fbd71f4d8cd148f7b70690ccf511e2f2026837a299db5ee50f63`）。没有扩展成全部旧 31 项或全仓/历史库存核对。

验证层级保留：

- M2/N4 的已接受真实运行：118 transitions、1416 受控 physics、708 render、四份 fresh 数据、[2,2]、143 维 sidecar；1128 tick 运动重叠、72 tick 错峰。
- 最新 M2/N1/contact 真实运行：761 transitions、9353 受控 physics、4676 render，warm2 另计；[0,1]、71 维 sidecar；App 20.328 秒、全树 1482.765 秒、目标/Conda/监督自然 exit0，完成记录 PASS。详细时序及证据见原主报告。
- 共享扩展后旧 profile 默认有既有 CPU 保护；共享 Host/runtime/runner 后来扩展过，**不能把双机入口字节未变写成最终组合版本全部 profile 重新 runtime PASS**。
- 本轮仅版本/依赖/文档核对，没有新的 runtime 或 CPU 行为测试通过声明。

Git 提示过现有 LF→CRLF 转换警告；本轮原始字节对照仍全部一致，未更改换行、`core.autocrlf` 或 `.gitattributes`。用户暂存可能按既有规则规范化文本；不要为“修 hash”覆盖文件。

## 5. 本轮检查与文档改动

已做：读取适用 AGENTS、当前交接/索引和必要阶段报告；只读 branch/HEAD/log、tracked/untracked/index/diff/ignore；定向源码/测试/资产路径依赖；一次最新 23 项与上述有限双机来源对照。使用已核对的 conda Python 标准库解析 **36 份候选 Python AST，全部成功**，未 import 候选模块、未生成 pyc。冲突标记及明显私钥/令牌特征定向检查未发现命中，不表示全面安全审计。

`git diff --check`、`git diff --cached --check` 无错误，`git ls-files -u` 空；新增报告/导航链接与精确候选路径作局部检查。此轮不重跑 53/64/202/182 项、历史场景或任何 App。未发现需要改变已验证生产版本的明确阻断；提交准备结论不代替行为测试。

仅三份本轮文档变更：

1. 新增本报告，提供精确文件清单、依赖边界和手动命令。
2. `T/AgentRead/TASK_PROGRESS.md`：当前首条与最新资产边界更新为用户已确认 GPT REVIEW PASS、提交准备完成；保留历史正文和 Phase B CLOSED。
3. `T/AgentRead/REPORT_INDEX.md`：扫描执行主题状态、主报告与下一步导航更新。

不新增实现、测试、脚本、manifest/ledger/ZIP；不改 AGENTS；小范围导航更新无需全量交接归档。无 Git 写操作、无包/驱动/环境变更、无资产变更、无运行或数据清理。

## 6. 用户尚需处理的事项

当前没有待决的生产修复或归属不明修改。用户只需核对下面 **41 个普通路径 + 4 个 ignored Python** 的内容与范围，决定并手动暂存、审阅 staged diff、提交。四份脚本纳入是已发现测试依赖的闭包，不是将日志纳入源码。

本轮不承接任何剩余 App 额度，不进入策略/评估/论文实验。四份本机 USD 的跨机器交付是之后的资产管理事项，不阻断本机代码基线 commit；若希望单次提交同时成为跨机可运行包，应另行明确资产范围，本轮不擅自扩大。

## 7. 精确手动命令（本轮未执行）

以下 PowerShell 从实际仓库根执行。**先暂存，单独审阅，再由用户决定 commit**。若 HEAD 已变或暂存区已非空，先核对新情况；不自动撤销任何暂存。清单中的文件应保存当前完整组合版本，不拆 hunk。

```powershell
Set-Location -LiteralPath 'E:\Project\IsaacLab_HARL'
git status --short
$cr12ExpectedHead = 'a8c618a32da65747827f1cb3f722fac24df2aec8'
$cr12CurrentHead = git rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $cr12CurrentHead -ne $cr12ExpectedHead) {
    throw 'HEAD 已变化或读取失败，请重新核对差异；不要直接套用旧清单。'
}
git diff --cached --name-status
$cr12ExistingStaged = @(git diff --cached --name-only)
if ($LASTEXITCODE -ne 0 -or $cr12ExistingStaged.Count -ne 0) {
    throw '暂存区读取失败或已有内容，请先人工核对归属；此处不自动取消暂存。'
}
$cr12StagePaths = @(
    'scripts/environments/_cr12_camera_capture.py'
    'scripts/environments/_cr12_camera_mount.py'
    'scripts/environments/_cr12_capture_runner.py'
    'scripts/environments/_cr12_contact_time.py'
    'scripts/environments/_cr12_gui_startup_diagnostics.py'
    'scripts/environments/_cr12_lifecycle_host.py'
    'scripts/environments/_cr12_pose_control.py'
    'scripts/environments/_cr12_runtime_support.py'
    'scripts/environments/_cr12_scan_executor.py'
    'scripts/environments/_cr12_shared_task_profile.py'
    'scripts/environments/_cr12_single_view_capture.py'
    'scripts/environments/run_cr12_dual_lifecycle_integration.py'
    'scripts/environments/run_cr12_shared_task_handover.py'
    'scripts/environments/run_cr12_single_view_capture.py'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202610/20261008/CR12_DUAL_GUI_STARTUP_DIAGNOSIS_AND_RETEST_REPORT.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202610/20261008/CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_PLAN.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202610/20261008/CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_REPORT.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202610/20261008/CR12_SHARED_TASK_FEASIBILITY_AND_HANDOVER_PLAN.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202610/20261009/CR12_CONTACT_FRESHNESS_PRECISION_AND_HANDOVER_RETEST_REPORT.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202610/20261009/CR12_DUAL_EXECUTION_AND_HANDOVER_COMMIT_READINESS.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202610/20261009/CR12_SHARED_TASK_HANDOVER_IMPLEMENTATION_REPORT.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/REPORT_INDEX.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md'
    'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_cr12_execution_adapter.py'
    'source/isaaclab_tasks/test/test_cr12_contact_reporting.py'
    'source/isaaclab_tasks/test/test_cr12_contact_retest_supervisor.py'
    'source/isaaclab_tasks/test/test_cr12_contact_runtime.py'
    'source/isaaclab_tasks/test/test_cr12_contact_time.py'
    'source/isaaclab_tasks/test/test_cr12_dual_camera_capture.py'
    'source/isaaclab_tasks/test/test_cr12_dual_execution_adapter.py'
    'source/isaaclab_tasks/test/test_cr12_dual_lifecycle_integration.py'
    'source/isaaclab_tasks/test/test_cr12_dual_runtime_support.py'
    'source/isaaclab_tasks/test/test_cr12_gui_startup_diagnostics.py'
    'source/isaaclab_tasks/test/test_cr12_runtime_support_hooks.py'
    'source/isaaclab_tasks/test/test_cr12_scan_executor.py'
    'source/isaaclab_tasks/test/test_cr12_shared_execution_contract.py'
    'source/isaaclab_tasks/test/test_cr12_shared_executor.py'
    'source/isaaclab_tasks/test/test_cr12_shared_lifecycle_host.py'
    'source/isaaclab_tasks/test/test_cr12_shared_profile.py'
    'source/isaaclab_tasks/test/test_cr12_shared_runtime.py'
    'source/isaaclab_tasks/test/test_cr12_shared_supervisor.py'
)
git add -- $cr12StagePaths
if ($LASTEXITCODE -ne 0) { throw '普通文件暂存失败；停止并检查，不自动提交。' }

$cr12ReproPaths = @(
    'logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/supervise_cr12_contact_retest.py'
    'logs/scan_assignment/20261009_cr12_shared_task_handover/repro/supervise_cr12_shared_task.py'
    'logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/supervise_cr12_dual_gui_startup.py'
    'logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/prepare_private_user_config.py'
)
git add -f -- $cr12ReproPaths
if ($LASTEXITCODE -ne 0) { throw '必要 repro 脚本暂存失败；停止并检查，不自动提交。' }

git diff --cached --stat
git diff --cached --name-status
git diff --cached --check
git diff --cached
```

预期上述清单共 **45 个唯一文件**（36 Python + 9 Markdown）；数量只是辅助，仍需查看完整 staged 内容，确认无私有配置/日志/模型、无他人新加入项、无清单之外的变化。若与本报告不同，暂停提交并核对，不执行 reset/restore/clean。本轮没有替用户运行上述 add。

建议完整 commit message：

```text
feat(cr12): add dual-robot execution and shared-task handover

Integrate dual CR12 execution with the existing lifecycle authority.
Support claim-bound retreat and clear-before-release task handover.
Validate on-demand capture, result ownership, and terminal acknowledgement.
Use dtype-aware contact timestamp validation without relaxing safety checks.

Scope: private fixed-cardinality execution fixtures with deterministic proposals.
Phase B closure and public entrypoint gates unchanged.
```

完成 staged 内容人工审阅后，再**单独**执行以下等价单次提交命令（每个 `-m` 形成一个正文段落）：

```powershell
git commit -m 'feat(cr12): add dual-robot execution and shared-task handover' -m 'Integrate dual CR12 execution with the existing lifecycle authority. Support claim-bound retreat and clear-before-release task handover. Validate on-demand capture, result ownership, and terminal acknowledgement. Use dtype-aware contact timestamp validation without relaxing safety checks.' -m 'Scope: private fixed-cardinality execution fixtures with deterministic proposals. Phase B closure and public entrypoint gates unchanged.'
git status --short
git log -1 --oneline
```

没有 push/tag 命令；本报告状态仍为准备完成，不能提前记录 COMMITTED。用户完成 commit 后再讨论下一研究阶段。

## 8. 辅助证据对应表

| 结论/检查项 | 文件位置 | 关键字段/定位 | 用途与限制 |
|---|---|---|---|
| 当前审阅状态与导航 | [TASK_PROGRESS](../../TASK_PROGRESS.md)、[REPORT_INDEX](../../REPORT_INDEX.md) | 当前首条/扫描执行主题 | 新用户确认；历史正文不回写 |
| 最新运行与版本来源 | [contact 主报告](CR12_CONTACT_FRESHNESS_PRECISION_AND_HANDOVER_RETEST_REPORT.md)、[已有 preflight](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/preflight_attempt_01.json) | 9353 tick、23 项代码输入 | 已有运行 + 本轮一次原始字节对照；JSON 本地保留 |
| dtype 长时间样例 | [既有 CPU 数值证据](../../../../../../../../logs/scan_assignment/20261009_cr12_contact_precision_retest/repro/contact_numeric_cpu_evidence.json) | 实际 dtype 递推、115/128 秒样例 | 不是 115/128 秒真实物理验证 |
| 已接受分区双机 | [双机 GUI 复测报告](../20261008/CR12_DUAL_GUI_STARTUP_DIAGNOSIS_AND_RETEST_REPORT.md)、[对应 preflight](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/attempt_01/preflight.json) | 118 transitions、四图、入口代码项 | 旧运行层级保留，非最终全部 profile 复验 |
| 原 contact 失败 | [共享首次实施报告](CR12_SHARED_TASK_HANDOVER_IMPLEMENTATION_REPORT.md) | global3842 FAIL/UNKNOWN | 保留先前结果 |
| 原启动失败与设计来源 | [双机实施报告](../20261008/CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_REPORT.md)、[双机方案](../20261008/CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_PLAN.md)、[共享方案](../20261008/CR12_SHARED_TASK_FEASIBILITY_AND_HANDOVER_PLAN.md) | 120×0 FAIL、固定布局/目标/退让设计 | 旧报告纳入，原待审正文保留 |
| 测试直接引用 | [contact 监督测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_contact_retest_supervisor.py)、[shared 监督测试](../../../../../../../../source/isaaclab_tasks/test/test_cr12_shared_supervisor.py) | 各 :12 的路径载入；第 3 节传递 helper | 四份 ignored Python 必须精确纳入；本轮未执行 |
| DPI/私有配置来源 | [双机监督器](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/supervise_cr12_dual_gui_startup.py)、[private helper](../../../../../../../../logs/scan_assignment/20261008_cr12_dual_gui_startup/repro/prepare_private_user_config.py) | SOURCE :34、KIT :45、helper :61–67 | 保存源码；真实 user.config 与运行额度不提交 |

阶段收口与手动提交准备已完成；本轮未暂存、未提交、未运行，停止于用户手动审阅/提交边界。

