# 报告主题导航

更新日期：2026-10-09。先读 [TASK_PROGRESS.md](TASK_PROGRESS.md) 了解当前状态，再按主题进入主报告；交付与归档规则见 [AGENTS.md](AGENTS.md)。

以下当前状态依据最新用户/GPT审阅结论。旧报告保留形成时的事实、待审标签和路径；本页不回写历史，也不授予下一阶段实施或运行权限。辅助脚本、JSON、日志和补丁由对应主报告定位，不在此逐一列出。

## Windows 运行时与启动兼容性

- **当前状态**：局部补丁与限定 GUI/CUDA/legacy viewer 验证已获 **GPT 审阅通过**。结论限于缺省D3D12与新增共用CUDA准备的组合路径；普通模式未独立实测，train/play运行、headless、CR12、扫描相机未被代验。
- **最新主报告**：[Windows 启动补丁实施与有界验证](202609/20260929/WINDOWS_RUNTIME_BACKEND_IMPLEMENTATION_AND_VALIDATION_REPORT.md)。
- **必要前置**：[实施前的运行时兼容性评估与最小修复方案](202609/20260928/WINDOWS_RUNTIME_BACKEND_ASSESSMENT_AND_PLAN.md)。
- **最新运行事件**：[双机GUI启动诊断与唯一复测](202610/20261008/CR12_DUAL_GUI_STARTUP_DIAGNOSIS_AND_RETEST_REPORT.md)：App1/1采用窗口DPI同组CLI候选，native1440×900/D3D12、六层及完整双机case实际PASS，现已获 **GPT/用户报告级审阅通过**。构造26.438秒/全树202.672秒自然exit0。窗口定向诊断停止；显式候选仅保留为成功启动条件，不证明唯一根因、不推广默认。旧[双机启动120×0 FAIL](202610/20261008/CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_REPORT.md)保留；旧额度耗尽，后续新case须新预算与授权。

## 机器人资产与基本关节驱动

- **当前状态**：固定底盘/lift0/v1、baseline PD、TGS8/2、显式external-forces-every-iteration=on的原720步/6秒基本关节运动与保持结果已获 **GPT REVIEW PASS**，基本驱动在该构型下完成；不推广其他构型，旧false及PD候选FAIL保留。旧入口默认inherit不提升，Windows/资产/基本驱动不重验。后续大幅往返仅该demo已获数值审阅与用户人工接受；源OBJ正常，已接受visual定位/预初始化集成与当前相机进展见下方扫描执行主题，不扩大基本驱动接受构型。
- **最新主报告**：[CR12外力逐迭代单因素实施与原条件复测](202609/20260930/CR12_EXTERNAL_FORCES_SINGLE_FACTOR_REPORT.md)。
- **必要前置**：[状态一致性与求解阶段诊断](202609/20260930/CR12_STATE_CONSISTENCY_AND_SOLVER_DIAGNOSIS_REPORT.md)（旧false对照及单因素依据）；[保持诊断与PD复测](202609/20260929/CR12_HOLD_DIAGNOSIS_AND_PD_RETEST_REPORT.md)（旧候选FAIL）；[派生资产与基本驱动实施](202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_IMPLEMENTATION_REPORT.md)（资产/参数接受）；[原参数与驱动计划](202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_PLAN.md)第5.3/6节给原判据。旧报告保留当时状态。
- **关联主题**：[Windows 启动兼容性](#windows-运行时与启动兼容性) 提供后续准备的已审阅启动基础。
- **下一层结果**：[正式单目标scanner pose](202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md)已获用户确认 **GPT REVIEW PASS**；后续manual-only显示不扩大原基本驱动或正式pose接受构型。

## 单机双视点扫描执行

- **当前状态**：用户已确认 **CR12_CONTACT_PRECISION_AND_HANDOVER_RETEST — GPT REVIEW PASS**。固定E1/M2/N4分区并行和shared_m2n1的A无数据取消/OFF→保留claim实际退出→fixed clear后R/receipt退役→B新claim同冻结task/pose真实RGBA/OFF/C、[0,1]与terminal/rebuild/ACK/自然退出已接受。contact真实覆盖14sensor各9353受控步、跨32/64秒；115/128秒仅CPU样例。共享转交限确定性proposal及稳定等待主动取消。本轮仅依赖/版本核对和文档收口，**READY FOR MANUAL COMMIT；App0、未重跑测试、未暂存/提交**；Phase B CLOSED/公共gate保持。
- **最新主报告**：[CR12双机执行与共享转交阶段收口及提交准备](202610/20261009/CR12_DUAL_EXECUTION_AND_HANDOVER_COMMIT_READINESS.md)：最新23份直接代码与当前逐字节一致，45个精确候选含4份必要ignored Python；4份实际USD是本机前置，未在HEAD。给出手动add/审阅/commit命令，尚未执行。
- **已接受共享运行**：[CR12 contact精度修正与共享转交完整复测](202610/20261009/CR12_CONTACT_FRESHNESS_PRECISION_AND_HANDOVER_RETEST_REPORT.md)：761 transitions/9353受控physics/4676render，warm2另计；App20.328秒/全树1482.765秒、目标/Conda/监督自然exit0。53项CPU、传感器覆盖/old-new分歧、完整A→B时序及唯一PNG见正文。旧报告当时待审标签保留，最新接受状态以上文用户确认为准。
- **历史原始失败**：[共享转交首次实施](202610/20261009/CR12_SHARED_TASK_HANDOVER_IMPLEMENTATION_REPORT.md)：原setup221/A到位3000/无数据OFF事实保持，retreat在global3842被旧contact判据拒绝，整体FAIL、无R/B采集/terminal；缺失的失败子项仍UNKNOWN，不回写为本轮实测。
- **已审共享方案**：[真正共享视点物理可行性与跨机器人转交方案](202610/20261008/CR12_SHARED_TASK_FEASIBILITY_AND_HANDOVER_PLAN.md)：固定root/非零初态/唯一SE(3)、24秒FK参考、clear-R；旧App0/未实施为当时历史状态，不回写。
- **已接受双机运行**：[CR12双机GUI启动定向诊断与唯一复测](202610/20261008/CR12_DUAL_GUI_STARTUP_DIAGNOSIS_AND_RETEST_REPORT.md)：1440×900/D3D12、118 transitions/1416受控physics/708 render、四fresh/独立OFF、并行隔离、[2,2]终态/143维sidecar/rebuild/自然退出；已获报告级审阅通过。旧App1/1耗尽，窗口诊断停止，不要求再次人工启动。
- **已保留实现与历史失败**：[CR12固定双机器人lifecycle实施与唯一运行](202610/20261008/CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_REPORT.md)：旧202项成果和120×0构造FAIL/0受控步均保持当时事实，不用本次PASS回写。
- **已审双机设计**：[CR12固定双机器人接入评估与最小方案](202610/20261008/CR12_DUAL_ROBOT_LIFECYCLE_INTEGRATION_PLAN.md)：同朝向Y间距2m、双Articulation/Camera、唯一clock/domain/authority、四目标与72tick错峰；保留形成时“仅静态/待审”历史状态，不回写正文。
- **已接受双点运行**：114项针对性CPU通过；唯一App完成同场景两个冻结scanner目标，600+2+60各662步、总1324步/11.033333909秒。实际状态/q_cmd/全局时钟连续；同Camera/product初始化1次、ON/OFF各2次、最终有效release1次。fresh帧571/902，各OFF30 render/30 quiet；第一份数据/结果/文件保持，六guard各1324。全树50.672秒、双exit0自然退出，App1/3，无重试/超时/Git写操作，已停止。
- **已接受单机主报告**：[CR12 execution-to-lifecycle实施与正常/取消重认领验证](202610/20261008/CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md)：182项CPU及语法检查通过；normal 112 transitions/1344physics，cancel 167/2004，各初始化2步另计。真实数据/OFF/保持、receipt后退役、旧terminal/62维sidecar/rebuild/ACK及自然退出均通过；App2/3，无运行重试。报告链接四张实际PNG及取消metadata；当时待审标签保留，当前接受状态依据最新用户确认。
- **已审接入设计**：[CR12扫描执行层与现有lifecycle authority接入分析及最小方案](202610/20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)：后续单机实施与有限运行已经完成并获审阅通过；旧报告形成时“仅方案/等待审阅”状态保留，不构成本轮双机运行授权。
- **已接受双点前置**：[CR12双视点连续按需相机采集](202610/20261007/CR12_TWO_VIEW_CAMERA_CAPTURE_REPORT.md)，含两张原始PNG、连续交接/资源身份/fresh/OFF证据及fresh-private有界人工命令；无需为验收重新启动App。
- **已接受单点前置**：[CR12单视点到位后按需相机采集](202610/20261007/CR12_SINGLE_VIEW_CAMERA_CAPTURE_REPORT.md)，当前GPT REVIEW PASS依据最新用户确认，旧报告当时待审及App01失败保留。
- **已接受显示前置**：[CR12 visual预初始化集成与有界运行收尾](202610/20261007/CR12_VISUAL_PREINIT_INTEGRATION_REPORT.md)，一次apply/seal、120步/native首末与两图；当前已审通过及用户外观接受以本索引为准，旧报告当时待审标签保留。
- **已审定位与历史失败**：[CR12扫描前视觉几何一致性](202610/20261004/CR12_VISUAL_GEOMETRY_CONSISTENCY_REPORT.md)：源visual/遮挡定位与方向已获认可；旧四图与最终native FAIL保持，本轮通过不证明上轮唯一根因。
- **已接受demo依据**：[CR12有界OBB精化与大幅关节往返](202610/20261004/CR12_OBB_REFINEMENT_AND_LARGE_JOINT_SWEEP_REPORT.md)：2520步、实际20.797719°/25.220625cm；旧报告保留当时人工待确认标签，最新用户反馈只接受该demo。OBB显式模式不自动推广旧入口。
- **原阻断记录**：[CR12 manual-only大幅关节往返](202610/20261003/CR12_MANUAL_LARGE_JOINT_SWEEP_REPORT.md)：旧AABB规则下20°/15°均PREFLIGHT_BLOCKED、App0；该事实保留，新授权精化不回写历史。
- **已接受运行前置**：[CR12 task-private user.config单因素验证](202610/20261003/CR12_PRIVATE_USER_CONFIG_SINGLE_FACTOR_REPORT.md)：原source不变、实际D3D12/native1440×900、GUI/marker/manual runtime smoke通过；旧小动作命令不能替代新大幅观察。历史120×0原生失败保留，不重新调查唯一根因。
- **诊断前置**：[CR12 manual GUI swapchain诊断与重试条件](202609/20260930/CR12_MANUAL_GUI_SWAPCHAIN_DIAGNOSIS_AND_RETRY_REPORT.md)，保留当时新App0/1、原故障及未知项。
- **manual实现依据**：[CR12 manual-only动作与marker改进](202609/20260930/CR12_MANUAL_VISUAL_MOTION_AND_MARKER_REPORT.md)，保留CPU结果、原始失败及当时人工命令，不视为新的运行授权或人工验收。
- **正式能力依据**：[CR12单目标scanner pose实施与有限验证](202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md)，保留形成时待审标签；当前GPT REVIEW PASS以最新用户确认及本索引为准。
- **必要前置**：[已审单目标实施方案](202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_PLAN.md)；[单机双视点原评估](202609/20260928/SINGLE_ROBOT_TWO_VIEWPOINT_IMPLEMENTATION_ASSESSMENT.md)。旧评估保留当时状态；本轮相机结果见最新主报告，POSE_REACHED本身仍不等于采集。
- **实施依赖与待办**：下一步由用户核对提交清单并手动提交，原运行预算不延续，不追加App。已接受固定共享取消—让行—跨机认领不代表MOVING取消、硬件失效接管、一般故障恢复、任意布局/目标、反向B→A、更多机器人、真实构件/标定、depth/pointcloud、实体或策略性能。owner/completed继续由真实authority管理，普通取消不写永久failed-pair；不自动进入训练或清理。

## Lifecycle MRTA / Phase B 已关闭成果

- **当前状态**：**COMPLETE / GPT REVIEW PASS / CLOSED**。生命周期及学习运行骨干、真实进程优化续训验证已关闭；不重新开启验收，不据此宣称公共event入口、长期论文实验或目标机器人执行已完成。
- **关闭主报告**：[Phase B 最终运行关闭报告](202609/20260924/PHASE_B_FINAL_CLOSURE_REPORT.md)。其当时的待GPT审阅标签保留，当前接受状态以上述结论为准。
- **当前关联**：[CR12 execution-to-lifecycle实施报告](202610/20261008/CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md)及[已审接入方案](202610/20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)；复用已关闭组件接入新执行backend，未改authority/public gate、未重验Phase B。
- **关联交接**：[项目现状与机器人接入交接](202609/20260926/PROJECT_STATE_AND_ROBOT_INTEGRATION_HANDOFF.md)，用于项目结构和既有边界背景；机器人资产、角色和后续实施状态以较新报告及当前交接为准。

旧smoke checkpoint和部分raw evidence已按授权删除，不因导航建立而恢复、重建或修复历史明细链接。现有AgentRead辅助产物全部保留原位；后续新增按AGENTS的用途分工存放。
