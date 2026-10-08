# 报告主题导航

更新日期：2026-10-08。先读 [TASK_PROGRESS.md](TASK_PROGRESS.md) 了解当前状态，再按主题进入主报告；交付与归档规则见 [AGENTS.md](AGENTS.md)。

以下当前状态依据最新用户/GPT审阅结论。旧报告保留形成时的事实、待审标签和路径；本页不回写历史，也不授予下一阶段实施或运行权限。辅助脚本、JSON、日志和补丁由对应主报告定位，不在此逐一列出。

## Windows 运行时与启动兼容性

- **当前状态**：局部补丁与限定 GUI/CUDA/legacy viewer 验证已获 **GPT 审阅通过**。结论限于缺省D3D12与新增共用CUDA准备的组合路径；普通模式未独立实测，train/play运行、headless、CR12、扫描相机未被代验。
- **最新主报告**：[Windows 启动补丁实施与有界验证](202609/20260929/WINDOWS_RUNTIME_BACKEND_IMPLEMENTATION_AND_VALIDATION_REPORT.md)。
- **必要前置**：[实施前的运行时兼容性评估与最小修复方案](202609/20260928/WINDOWS_RUNTIME_BACKEND_ASSESSMENT_AND_PLAN.md)。

## 机器人资产与基本关节驱动

- **当前状态**：固定底盘/lift0/v1、baseline PD、TGS8/2、显式external-forces-every-iteration=on的原720步/6秒基本关节运动与保持结果已获 **GPT REVIEW PASS**，基本驱动在该构型下完成；不推广其他构型，旧false及PD候选FAIL保留。旧入口默认inherit不提升，Windows/资产/基本驱动不重验。后续大幅往返仅该demo已获数值审阅与用户人工接受；源OBJ正常，已接受visual定位/预初始化集成与当前相机进展见下方扫描执行主题，不扩大基本驱动接受构型。
- **最新主报告**：[CR12外力逐迭代单因素实施与原条件复测](202609/20260930/CR12_EXTERNAL_FORCES_SINGLE_FACTOR_REPORT.md)。
- **必要前置**：[状态一致性与求解阶段诊断](202609/20260930/CR12_STATE_CONSISTENCY_AND_SOLVER_DIAGNOSIS_REPORT.md)（旧false对照及单因素依据）；[保持诊断与PD复测](202609/20260929/CR12_HOLD_DIAGNOSIS_AND_PD_RETEST_REPORT.md)（旧候选FAIL）；[派生资产与基本驱动实施](202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_IMPLEMENTATION_REPORT.md)（资产/参数接受）；[原参数与驱动计划](202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_PLAN.md)第5.3/6节给原判据。旧报告保留当时状态。
- **关联主题**：[Windows 启动兼容性](#windows-运行时与启动兼容性) 提供后续准备的已审阅启动基础。
- **下一层结果**：[正式单目标scanner pose](202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md)已获用户确认 **GPT REVIEW PASS**；后续manual-only显示不扩大原基本驱动或正式pose接受构型。

## 单机双视点扫描执行

- **当前状态**：双点demo及接入设计已获GPT/用户审阅；本轮完成私有E1/M1/N2真实authority接入和两个有界case，**CR12_EXECUTION_LIFECYCLE_INTEGRATION_PASS，等待GPT/用户审阅**。normal C×2；cancel在稳定WAITING_DATA无数据取消R后同机器人同task新claim，再C×2。基本/正式/visual及人工demo、Phase B CLOSED接受范围保持，未解封公共event入口。
- **已接受双点运行**：114项针对性CPU通过；唯一App完成同场景两个冻结scanner目标，600+2+60各662步、总1324步/11.033333909秒。实际状态/q_cmd/全局时钟连续；同Camera/product初始化1次、ON/OFF各2次、最终有效release1次。fresh帧571/902，各OFF30 render/30 quiet；第一份数据/结果/文件保持，六guard各1324。全树50.672秒、双exit0自然退出，App1/3，无重试/超时/Git写操作，已停止。
- **最新主报告**：[CR12 execution-to-lifecycle实施与正常/取消重认领验证](202610/20261008/CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md)：182项CPU及语法检查通过；normal 112 transitions/1344physics，cancel 167/2004，各初始化2步另计。真实数据/OFF/保持、receipt后退役、旧terminal/62维sidecar/rebuild/ACK及自然退出均通过；App2/3，无运行重试。报告链接四张实际PNG及取消metadata，交付后已停止。
- **已审接入设计**：[CR12扫描执行层与现有lifecycle authority接入分析及最小方案](202610/20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)：本轮用户已授予限定实施与运行；旧报告形成时“仅方案/等待审阅”状态保留。
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
- **实施依赖与待办**：同资产一次pre-init、原formal/manual/sweep/single/two-view默认保持。当前真实运行范围为局部双点、virtual RGBA和固定非物理fixture；追加验证仅涵盖一次稳定等待取消/同机器人重新认领。MOVING取消、sticky恢复、自然卡滞、C+U/关闭失败、非零在途、真实构件/标定、depth/pointcloud、多机和策略性能未由本轮PASS代验。owner/completed仍由真实authority决定，普通取消不记永久failed-pair。下一步仅GPT/用户审阅本轮交付，再决定新授权；不自动继续运行或训练。

## Lifecycle MRTA / Phase B 已关闭成果

- **当前状态**：**COMPLETE / GPT REVIEW PASS / CLOSED**。生命周期及学习运行骨干、真实进程优化续训验证已关闭；不重新开启验收，不据此宣称公共event入口、长期论文实验或目标机器人执行已完成。
- **关闭主报告**：[Phase B 最终运行关闭报告](202609/20260924/PHASE_B_FINAL_CLOSURE_REPORT.md)。其当时的待GPT审阅标签保留，当前接受状态以上述结论为准。
- **当前关联**：[CR12 execution-to-lifecycle实施报告](202610/20261008/CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md)及[已审接入方案](202610/20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)；复用已关闭组件接入新执行backend，未改authority/public gate、未重验Phase B。
- **关联交接**：[项目现状与机器人接入交接](202609/20260926/PROJECT_STATE_AND_ROBOT_INTEGRATION_HANDOFF.md)，用于项目结构和既有边界背景；机器人资产、角色和后续实施状态以较新报告及当前交接为准。

旧smoke checkpoint和部分raw evidence已按授权删除，不因导航建立而恢复、重建或修复历史明细链接。现有AgentRead辅助产物全部保留原位；后续新增按AGENTS的用途分工存放。
