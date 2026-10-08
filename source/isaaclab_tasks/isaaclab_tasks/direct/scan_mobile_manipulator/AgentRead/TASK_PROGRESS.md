# TASK_PROGRESS

## Current status

PHASE-B-FINAL-CLOSURE: **GPT REVIEW PASS / CLOSED**.
Phase B: **COMPLETE / GPT REVIEW PASS / CLOSED**.
Phase-B engineering closeout: **COMPLETE / LOCAL COMMITS RECORDED**.
Classification: `PHASE-B-ENGINEERING-GIT-CLOSEOUT-COMMITTED`.

2026-10-08（CR12 execution-to-lifecycle 实施与有限验证，最新）：接入方案已获GPT/用户设计审阅及本轮实施授权。已完成私有E1/M1/N2 Host、非阻塞CR12执行器、真实resolver/claim/Store/P2/producer/authority/facade、raw custody及receipt后退役。182项针对性CPU、17项抽取对照与语法检查通过；两个GUI/D3D12/private/cuda:0 App均通过：**NORMAL_CASE_PASS**（112 transitions、1344受控physics/672render、C×2）及 **CANCEL_THEN_RECLAIM_CASE_PASS**（167 transitions、2004physics/1002render、稳定WAITING_DATA无数据取消R×1、同任务新claim后C×2）。各初始化2步另计、各两张真实RGBA；同App相机/控制对象连续，块末重新确认OFF/保持/健康，真实receipt后退役，旧episode完成数2、62维sidecar、逻辑rebuild及facade ACK均完成。全树84.875/126.734秒、双exit0自然退出，无超时/强杀/运行修复；App2/3后停止。**CR12_EXECUTION_LIFECYCLE_INTEGRATION_PASS，等待GPT/用户审阅，不自行写GPT REVIEW PASS。** 详见[实施主报告](202610/20261008/CR12_EXECUTION_LIFECYCLE_INTEGRATION_REPORT.md)及原图/日志链接。Phase B COMPLETE / GPT REVIEW PASS / CLOSED、basic/formal/visual和已接受demo范围保持；单机一次取消不代表多机仲裁/重分配、一般故障恢复或可变规模策略。未改核心authority/public gate、资产/物理/Windows配置；无Git写操作，不进入训练、额外case或后续实施。

2026-10-07（CR12 execution-to-lifecycle 接入分析，历史记录）：用户已确认 **TWO_VIEW_CAPTURE_INTEGRATION GPT REVIEW PASS**，独立单机双视点正常执行最小目标完成。本轮仅定向源码/契约分析与方案设计，已形成[接入主报告](202610/20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)：推荐私有E1/M1/N2 Host复用真实domain/Store/resolver/claim/P2/producer/authority，外部统一physics/render推进，长请求绑定claim来源并消费一次。正常完成建议在本次数据有效持有、OFF及保持确认后提交；PNG保存独立，普通取消/超时不自动成为永久failed-pair。主要缺口为非阻塞抽取、身份/结果接线、健康无数据请求复用和terminal/rebuild协作。**未实施adapter/Host或恢复接口，未运行集成；等待GPT/用户审阅具体方案。** Phase B COMPLETE / GPT REVIEW PASS / CLOSED及basic/formal/visual、人工demo接受范围保持；多机、异常恢复和真实MRTA执行未由双点PASS代验。仅报告及导航更新，未启动Isaac/CUDA/仿真/测试，无Git写操作，不自动继续实施。

2026-10-07（CR12双视点连续按需采集，历史记录）：单视点采集已由用户确认 **GPT REVIEW PASS**；本轮按新授权完成固定两目标顺序、连续pose context及同Camera/product顺序请求复用。114项针对性CPU与语法检查通过。唯一GUI/D3D12/private/cuda:0 App完成 **TWO_VIEW_CAPTURE_INTEGRATION_PASS**：两个goal各600+2+60=662步、总1324步/11.033333909秒，各121样本稳定1秒；真实新帧571/902，各OFF30 render/30 quiet、在途0。初始化/scene/reset/joint-state写入各1；prepare/initialize各1、begin/OFF确认各2、最终有效release1；实际状态/q_cmd/global clock连续，第一份数组/结果/文件未变，六guard各1324。全树50.672秒、双exit0、全部所属自然退出，无超时/强杀/重试，App1/3成功后停止。详见[双视点采集主报告](202610/20261007/CR12_TWO_VIEW_CAMERA_CAPTURE_REPORT.md)，含两张原PNG、交接/源时间证据及fresh-private有界人工命令。**等待GPT/用户审阅，不自行写本轮GPT REVIEW PASS。** 原资产/物理/显示接受范围、Phase B CLOSED保持，未改任务authority，无Git写操作。多机、真实构件、depth/pointcloud、异常恢复runtime与MRTA接入未验证/未实施；后续须另行讨论授权。

2026-10-07（CR12单视点按需相机采集，历史记录）：用户已确认scanner/车体两张修正图无问题，VISUAL_PREINIT_INTEGRATION已有GPT REVIEW PASS，显示分支收口。本轮按新授权完成专属Camera/product、虚拟安装/光学配置、post-super新帧快照、Hydra启停/独立OFF观察、单请求状态机及旧pose默认不变的最小抽取。最终107/107针对性CPU与语法检查通过。App01在0受控步时因初始化native/Fabric读回时序失配FAIL；一次OFF状态sim.forward修复保持native数组和clock/App计数不变。App02完成 **SINGLE_VIEW_CAPTURE_INTEGRATION_PASS**：pose600+capture2+close60=662步/5.516666954秒，121点稳定1秒，运动产品事件0；同源frame558的640×480 RGBA真实取得并保存，OFF后30次正常render/30次quiet、在途0，六guard各662通过、native参数未变。全树35.203秒、双exit0、全部所属自然退出，无超时/强杀；App2/3成功后不补跑。acquired/saved/confirmed_off均true；原始PNG和fresh-private有界人工命令见[本轮相机主报告](202610/20261007/CR12_SINGLE_VIEW_CAMERA_CAPTURE_REPORT.md)，可直接看图，无需再开App。**等待GPT/用户审阅，不自行写新GPT REVIEW PASS；本轮已停止。** source配置及v1资产保持，无Git写操作。未实施depth/pointcloud、真实结构光/曝光标定、真实构件、双视点或目标机器人MRTA接入；Phase B/basic/formal/已接受demo结论保持。

2026-10-07（CR12 visual预初始化集成，历史记录）：上轮正确源visual保留、guide collision遮挡及十Mesh render-only方向已获GPT/用户审阅认可；本轮完成显式pre-init一次apply/seal、初始化后不撤销/重应用、native首末独立快照、固定120步保持与暂停后两张完整修正图。helper31/31、entry19/19、shared6/6、supervisor11/11 CPU及语法检查通过。唯一GUI/D3D12/private/cuda:0 App取得 **VISUAL_PREINIT_INTEGRATION_PASS**：初始化2步另计，120受控步/1.000000052秒、六guard各120、render60；首末native参数逐值相同，四阶段覆盖不变。两图各15次UI更新、暂停后无native getter/physics；scanner头部/支架完整入镜。App18.281秒、全树31.109秒，目标/Conda自然exit0、全部所属退出，无失败/超时/强杀；App1/2，不补跑。原28项资产与真实source配置未变，旧入口默认保持，无Git写操作。详见[预初始化集成主报告](202610/20261007/CR12_VISUAL_PREINIT_INTEGRATION_REPORT.md)，第7节给fresh private有界人工命令，也可直接看PNG。**等待GPT/用户审阅，外观PENDING_USER_REVIEW；不自行写新GPT REVIEW PASS，不证明上轮native唯一根因。** Phase B/basic/formal及大幅demo接受范围保持；已停止，不自动接相机/构件/双视点/MRTA或清理。

2026-10-04（CR12扫描前visual一致性，历史记录）：原OBJ→派生→USD的20项几何映射通过；当前viewport显示guide collision，精确隐藏十个独立collision Mesh后，车体层次和末端开放支架重新可见。已新增显式render-only helper、独立检查入口与37/37 CPU测试，四张同视角原PNG保留；旧入口默认不变。**整体VISUAL_GEOMETRY_RENDER_FAIL**：首App暂停API与监督收尾失败经局部修正，第二App四图后在native get_masses访问异常退出；最终native物理不变性/完成记录/正常关闭未通过。App2/2已用完，初始化各2步、额外保持0，停止runtime和实现修正。原28份输入/v1资产、15份既有代码及真实user.config未变，无Git写操作。**用户已确认此前20°往返demo完整且平稳，无明显异常；该demo数值审阅与人工接受成立，marker反馈保持，不推广六轴/全工作空间。** 本次两处外观仍待用户确认，scanner近景顶部裁切已披露。详见[visual一致性主报告](202610/20261004/CR12_VISUAL_GEOMETRY_CONSISTENCY_REPORT.md)。不提供声称已通过的新人工命令；等待GPT/用户审阅native集成缺口，下一研究步骤仍为单视点按需相机采集，本轮不自动实施。

2026-10-04（CR12有界OBB精化与大幅关节往返，历史记录）：已新增显式 `aabb_then_obb_margin_v1` 与独立joint-space入口，保留原10份collision、全部禁止pair、每侧2mm世界余量和旧AABB默认。20°/15°各201点全pair精化通过，按授权首次App前冻结20°；几何20/20、轨迹26/26、入口13/13 CPU测试及监督110/110断言通过。唯一GUI/D3D12/private App完成2520受控步/21.000001秒完整往返，两窗各121点稳定1秒；实测joint_3最大+20.797719°、scanner最大离起点0.252206m，六类guard各2520 PASS。墙钟56.797秒，实际0.369738×；1440×900、marker9/9且2521次更新，source配置未变。全树82.125秒自然退出，App1/3、受控1/2、无runtime重试，**MANUAL_JOINT_SWEEP_RUNTIME_PASS；大幅动作人工观感PENDING_USER_REVIEW，不自行写新GPT REVIEW PASS。** 详见[本轮主报告](202610/20261004/CR12_OBB_REFINEMENT_AND_LARGE_JOINT_SWEEP_REPORT.md)，第9节给每次新private/新输出的人工命令。原AABB阻断仍为历史事实，新精化是本轮明确授权；formal/basic接受状态及Phase B CLOSED保持。未改资产/物理参数/旧默认/真实user.config，无Git写操作。**停止，等待GPT/用户审阅和人工反馈；不再启动App、不修visual、不接相机/构件/双视点/MRTA。**

2026-10-03（CR12 manual-only大幅关节往返，历史记录）：完成joint_3 +20°/+15°的当前FK、各201点原几何检查与六轴重力/惯性估计。名义scanner位移0.230257484/0.173077731m，估计峰值最高占effort限值65.70%/51.56%；但两候选均由link_4_collision与link_6/scanner_collision世界AABB重叠阻断，首失败10.6°/10.575°。两形状名义相对位姿不变，支持保守投影重叠解释，不证明真实接触。**PREFLIGHT_BLOCKED；未选定角度，App0/3、受控0/2，无新sweep入口/模块/测试，实际角度与位移NOT_RUN，往返未完成。** 按用户两候选均不适合即停止的要求，没有放宽守卫、缩成小动作或推荐GUI命令。只新增任务repro离线核对及0–3项幂等private helper；helper67/67 CPU通过，真实配置未准备。**marker可见性已有用户正面反馈，但机械臂运动幅度仍不足，运动连续性/穿插等人工判断尚未完成。** formal/basic drive既有GPT REVIEW PASS、旧manual/private已接受记录和Phase B CLOSED保持。详见[大幅关节往返主报告](202610/20261003/CR12_MANUAL_LARGE_JOINT_SWEEP_REPORT.md)。未改生产代码/资产/物理参数、未启动Isaac/CUDA/仿真、未执行Git写操作。**停止，等待GPT/用户审阅保守几何守卫阻断；不自动精化守卫或启动App。**

2026-10-03（CR12 task-private user.config单因素验证，历史记录）：用户授权唯一manual App；原source只读，副本仅width/height/maximized三项语义差异（−1/−1/true→1440/900/false）。实际private加载、D3D12 native窗口1440×900，未重现120×0；L0隔离/L1 GUI/L2 marker/L3 motion均PASS。9 prototypes/9 instances、visual_errors=[]、841次更新；840受控步/7.000000365秒，六类guard各840 PASS，121点稳定1秒，最终0.057746825mm/0.006121124°。App20.593秒/全树50.938秒，Conda及目标自然exit0，无超时/强杀，App1/1，无重试。source大小/mtime/hash不变；Kit仅重写private格式，语义diff0。**MANUAL_VISUAL_RUNTIME_SMOKE_PASS，等待GPT/用户审阅；支持窗口恢复参与历史故障的假设，不证明−1/−1唯一根因，不自行写新GPT REVIEW PASS。** formal/basic drive既有GPT REVIEW PASS、Phase B CLOSED及历史120×0 FAIL保留。31+21 CPU通过，原代码/资产跨日与运行后均未变；只新增private/repro/证据及文档。现在可按[本次主报告](202610/20261003/CR12_PRIVATE_USER_CONFIG_SINGLE_FACTOR_REPORT.md)两条每次新private的命令人工查看；marker相关Hydra warning已披露，人眼可读性尚未验收。camera/双视点/MRTA/visual mesh修复未开展，未执行Git写操作。**报告交付后停止，不再启动App或自动进入下一阶段。**

2026-09-30（CR12 manual GUI 120×0定向诊断，历史记录）：已对照formal成功与manual失败的真实命令、配置、源码和同次日志；两者均请求window1440×900/renderer1280×720并实际D3D12。120×0最早出现在native omni.appwindow创建时，早于scene/marker/view；当前同一路径user.config保存width/height=−1/−1、maximized=true，mtime17:03:37位于两次运行之间，但历史内容、覆盖关系及最后native派生步骤仍UNKNOWN，不能认定因果。当前桌面工作区非零，仅代表本轮只读观察。**未找到满足授权前提的明确局部修复，因此未改代码/持久配置、新App0/1，未执行重试。** 原31/31与manual21/21 CPU测试通过。formal/basic drive GPT REVIEW PASS、manual实现/CPU PASS及上轮runtime FAIL/0步/marker NOT_REACHED均保留；当前不建议重新人工运行。详见[GUI诊断与重试条件主报告](202609/20260930/CR12_MANUAL_GUI_SWAPCHAIN_DIAGNOSIS_AND_RETRY_REPORT.md)。只新增报告/小型证据并更新交接导航；无Isaac/CUDA/仿真/Git写操作。**停止，等待GPT/用户审阅后决定如何验证saved window state；不自动换配置、改系统或使用剩余App额度。** camera/双视点/MRTA未实施，Phase B CLOSED及历史清理边界不变。

2026-09-30（CR12 manual-only动作与marker改进，历史记录）：用户确认正式单目标pose已有 **GPT REVIEW PASS**，本轮不重跑、不回写正式历史。已新增显式 `manual_visible_local_v1`（默认formal保持），冻结witness=(0,3,−4.5,0,4.5,0)°、beta=1、6秒reference/10秒1200步；离线32.107mm/3°、101点原几何检查通过。原31/31、新21/21 CPU测试、formal AST回归、67项监督判定及语法检查通过；新增粗细RGB轴、真实origin球/连线、arm-oblique/wrist-oblique一次视角。**唯一manual App在AppLauncher构造阶段D3D12窗口120×0/createSwapchain失败并原生0xC0000005退出，MANUAL_VISUAL_RUNTIME_SMOKE_FAIL；0受控步，target/marker/view均未进入，不能宣称visual_errors=[]或运动完成。** 全树23.156秒退出，无超时/强制终止；App1/2、无重试，不因原生故障使用局部修复额度。详见[本轮主报告](202609/20260930/CR12_MANUAL_VISUAL_MOTION_AND_MARKER_REPORT.md)，末节给出两条未由Codex执行的人工命令。manual-visible profile仅用于人工观察运动连续性和marker显示，不扩展正式单目标验收范围。源OBJ由用户确认正常；仿真显示几何存在差异，原因待查。未改资产、Windows启动、controller/PD/solver/guard或Git索引；相机/双视点/MRTA未实施。**停止并等待GPT/用户审阅；后续启动故障处理、runtime及人工效果仍待决定，不自动重跑。** Phase B CLOSED及旧清理边界保留。

2026-09-30（CR12单目标scanner pose实施与有限验证，历史记录）：已审方案按本轮授权完成最小共享抽取、pose控制/纯CPU测试及visual debug入口。旧driver展开122条语句AST等价；31/31控制CPU测试、6/6共享回归、11项监督完成检查及语法检查通过。唯一正式GUI/D3D12/cuda:0 App在v1/fixed-base/lift0/baseline/explicit-on不变条件下，首次native Jacobian唯一匹配COM（linear误差4.3159e−7），无额外刷新步；600受控步/5.000000261秒取得 **POSE_REACHED / 数值PASS**，最终0.0695588mm/0.00468716°，第480–600步121点稳定1.000000052秒，六类guard各600 PASS。初始化2步单列；App24.343秒，全树63.484秒，Conda/目标自然exit0、全部所属进程退出，无失败/超时/重试；App1/2，不补跑。v1七文件内容未变，未执行Git写操作。详见[实施主报告](202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_IMPLEMENTATION_REPORT.md)，第9节有同一正式目标的wrist/overall人工查看命令。marker正式关闭，仅源码/CPU检查；overall spectator已运行成功。**结果等待GPT/用户审阅与人工反馈，不自行写本轮GPT REVIEW PASS。** 基本joint drive既有GPT REVIEW PASS保持；源OBJ由用户确认正常，仿真显示几何差异仍待后续；未调查/修visual，未实施camera、双视点或目标机器人MRTA接入。Phase B CLOSED与历史清理边界不变；交付后停止。

2026-09-30（CR12单目标scanner pose实施设计，历史记录）：用户确认上一轮explicit external-forces-every-iteration=on、fixed-base/lift0/v1、baseline PD、TGS8/2下原720步/6秒基本关节运动与保持已获 **GPT REVIEW PASS**；不重验或推广其他构型。本轮完成静态源码核对、CPU FK/几何Jacobian及单次线性预测，形成[单目标scanner pose实施方案](202609/20260930/CR12_SINGLE_TARGET_POSE_EXECUTION_PLAN.md)：link_6为控制刚体，固定scanner frame换算，内置absolute-pose DLS λ=.01与受限位置命令积分；首个目标相对实测初态世界平移(10.698146,0,−0.155047)mm、绕世界Y转+1°，候选到位2mm/.25°/dq≤.01rad/s连续1秒；下一轮建议最多8秒/960受控步。native Jacobian参考点与新闭环均待运行校核，未把静态计算写成到位PASS。**设计完成，等待GPT/用户审阅；未新增实现/测试代码、未启动Isaac/CUDA或运行IK/仿真，未改资产或执行Git写操作。** 源OBJ由用户确认正常；仿真显示几何存在差异，原因待查；本轮不调查，加入构件/相机/正式视点前须解决显示一致性。IK执行、相机、双视点及目标机器人MRTA接入仍未实施；不自动进入下一阶段。历史当时的待审/FAIL口径保留，Phase B CLOSED及清理边界不变。

2026-09-30（CR12外力逐迭代单因素实施与复测，历史记录）：用户选择方案A并新授权实施/有限运行。新增显式 inherit/on/off，默认inherit不变，仅对本次匿名scene session设置on；v1、baseline、原轨迹/步长/solver/判据和读取次序不变。首App在写属性/reset前因GetPropertyStack缺时间参数失败，0步；局部API修复后唯一重试完成720步/6.000000313秒，原运动/保持验收PASS，末秒121/121，五类检查各720 PASS。共同4–5秒轴5/6的|R|由0.023184910/0.025973621降至4.293512e-8/2.103638e-8rad。最终16/16新增CPU测试、15/15原状态测试、8/8监督CPU检查通过；main1/repair1/matched_false0、App2/3，两次全部自然退出无超时，不补跑false。**当前显式on通过原完整驱动判据，等待GPT/用户审阅；不自行写GPT REVIEW PASS或推广到其他构型。** 旧false/PD候选FAIL及旧未授权记录保留。详见[本轮主报告](202609/20260930/CR12_EXTERNAL_FORCES_SINGLE_FACTOR_REPORT.md)。人工查看已发生：整体比例无明显问题，5°不足确认细微运动/穿插/保持；**源OBJ由用户确认正常；仿真显示几何存在差异，原因待查。** 外观调查后置，本轮不改显示配置/资产。Phase B CLOSED、Windows与v1接受状态保留；未执行Git写操作。**停止，等待审阅；不自动调参、提升默认、修视觉、进入IK/相机/双视点/MRTA。**

2026-09-30（CR12同刻状态与求解阶段诊断，历史记录）：上一轮诊断及预算收口已获GPT/用户审阅认可，完整驱动FAIL保留。本轮新增同刻缓存/native/link状态探针，15/15新CPU测试、12/12原诊断测试及6/6监督器CPU检查通过；唯一GUI/D3D12/cuda:0 baseline运行取得受控1…600步完整对照，600读块无clock推进，15条快照复查均未改写。六轴缓存/native q与dq最大差全0；link角/native q最大差5.302e-7rad、父子角速度投影/native dq最大差4.471e-8rad/s。4–5秒位置端差仍约1e-7rad，而轴5/6速度积分约−0.02318/−0.02597rad；未发现明确局部读取错误，转向求解时序的条件性调查。**状态对照目标完成；原完整关节运动与保持验收仍FAIL，第600/720步、t=5停止，基本驱动阶段未关闭。** A1/2、B0/1、App1/3，进程自然退出，无超时；不为用满预算继续运行。v1、baseline、物理设置、判据、Windows及Phase B不变，未执行Git写操作。只提出外力逐TGS位置迭代false→true的单因素建议，尚未实施/运行。详见[本轮主报告](202609/20260930/CR12_STATE_CONSISTENCY_AND_SOLVER_DIAGNOSIS_REPORT.md)，第8节有同一drive入口的人工查看命令，人工结果待用户确认。**停止，等待GPT/用户审阅和可视化反馈；不自动进入solver试验、PD、IK、相机、双视点或MRTA。** 后续历史段落保留当时口径，当前状态以本段和主题索引为准。

2026-09-29（CR12保持诊断与PD复测，历史记录）：上轮v1资产与分层参数检查成果已获GPT/用户接受，完整保持FAIL保留。本轮按新授权完成定向源码核对、真实目标/q/dq独立CSV、失败样本与统计窗口修正，以及baseline、hold_tune_01、hold_tune_02三次GUI/D3D12/cuda:0原条件试验；未发现明确目标下发或缓存刷新错误。三次均在600/720步、t=5秒触发轴5/6末秒速度超限，**完整运动与保持验收仍FAIL，基本驱动阶段未关闭**。最终两轴绝对速度0.020183425/0.022130456rad/s，较基线下降12.95%/14.80%，仍超过0.01；位置趋稳但原生dq持续非零的差异尚未解释。末秒真实1/121样本、接触600步、geometry/frame599步均明确记录。最终12/12针对性CPU测试通过；A3/3、B0/2、App3/5，所有所属进程自然退出，无超时；不再运行或调参。baseline默认未改，失败候选保留显式profile。详见[保持诊断与PD复测主报告](202609/20260929/CR12_HOLD_DIAGNOSIS_AND_PD_RETEST_REPORT.md)。**等待GPT/用户审阅；下一步建议先核对同一物理时刻的状态来源，再决定后续授权。** 未改v1资产、Windows启动、物理设置/阈值或MRTA，未执行Git写操作；IK/相机/双视点未被代验。

2026-09-29（CR12派生资产与基本驱动实施，历史记录）：参数计划已获GPT/用户审阅，本轮资产生成和有限GUI运行已明确授权。已新增CPU准备/校验模块、USD准备入口、机器人配置、独立驱动入口及针对性测试；最终14/14 CPU测试通过。`assets/rokeaCR12/derived/fixed_lift0_v1/` 派生URDF/USD及最终PhysX参数检查通过，7体/6轴、固定底盘和升降q0=0，原输入21/21未变。一次USD导入通过；首次驱动在动作前因惯量重复旋转读回错误停止，局部修正后重试在第600/720步、5秒触发joint_5/6末秒保持速度超限，**完整运动与保持验收FAIL**。三次App均实际D3D12/cuda:0、自然退出、无超时；内部失败不因exit0改写。驱动2/2额度已用完，无PD调参或第三次驱动。接触读回覆盖600步，几何/frame检查覆盖599步，未扩大为完整循环通过。详见[实施主报告](202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_IMPLEMENTATION_REPORT.md)。**等待GPT/用户审阅最终结果；进一步诊断/调参/运行需另行授权。** 未改已接受Windows代码、MRTA、依赖或原资产，未执行Git写操作；IK、构件避障、相机、双视点未被代验。

2026-09-29（CR12参数与基本驱动方案）：已完成原URDF/20条引用mesh的定向CPU计算、原完整惯量检查、逐link与固定组合并候选值、导入设置及有限关节驱动计划。主报告推荐原质量暂用+visual均匀盒惯性，升降q0=0、预合并7体/6轴；下一轮候选为joint_2的5°平滑运动、1+2+3秒共720physics steps，具体PD/限制/阈值待审。**尚未生成派生URDF/USD、尚未运行关节驱动**；原资产、已接受启动代码和既有工作区修改保留。本次仅新增主报告并更新索引/本文，无Isaac/CUDA/仿真/训练/Git写操作。Windows启动兼容性和报告组织规则已审阅通过，Phase B保持COMPLETE / GPT REVIEW PASS / CLOSED，不重验。

2026-09-29（文档交付与主题导航）：已在 [AGENTS.md](AGENTS.md) 协调主报告自足、辅助证据对应表、按用途存放与最小交付规则，并建立 [REPORT_INDEX.md](REPORT_INDEX.md) 四主题入口。后续文档沿用月/日目录，运行证据首选仓库 `logs/scan_assignment/YYYYMMDD_<topic>/attempt_01/`，必要一次性复现脚本放同任务 `repro/`；历史混放文件保留原位。本次仅修改规则、索引和本文，核对条款、新导航链接及文档差异；未运行旧检查或runtime，未改代码/资产/依赖，未执行Git写操作。

最新资产边界：v1原质量暂用、visual均匀盒COM/惯量与固定组合并成果已获接受，参数仅用于首版仿真调试，不是厂家真值。用户删除的旧USD不恢复；原URDF/mesh与v1派生层保持。basic drive、formal scanner pose既有GPT REVIEW PASS不变；大幅joint_3 demo已数值审阅与人工接受，仅限该demo，marker已有正面反馈。源visual保留、guide collision遮挡及pre-init render-only集成已获GPT REVIEW PASS，2026-10-07两处完整外观已由用户确认，显示分支收口；旧native FAIL保留，不推定唯一根因。本轮新相机入口显式复用一次pre-init覆盖，虚拟T_SC/pinhole参数非真实标定；单视点到位→ON→真实RGBA→OFF确认→保存/正常退出已获GPT REVIEW PASS；同场景两目标连续执行、同Camera/product重复启停及两份结果保留已获GPT/用户确认TWO_VIEW_CAPTURE_INTEGRATION GPT REVIEW PASS，独立最小闭环完成；当前仅完成execution-to-lifecycle接入分析，具体方案待审、尚未实现/运行集成。旧入口inherit/AABB默认与原控制不变，OBB/visual/camera不自动推广。depth/pointcloud、真实构件及MRTA尚未实施，非零在途/异常恢复runtime未验证；下一阶段须另行决定，不继续运行或历史清理。历史段落保留当时口径，当前状态以最新说明和索引为准。

2026-09-29（Windows 局部实施与有限验证）：四个启动文件补丁与限定GUI/CUDA/legacy viewer验证已获 **GPT 审阅通过**；12/12纯参数测试、语法与源码/AST检查完成。唯一一次真实 legacy proxy viewer GUI（num_envs=1、三个agent）确认实际D3D12、cuda:0矩阵每项16/总和4096、显式reset完成、120次env.step返回及环境关闭；viewer/Conda自然exit0，全部所属进程在218.515秒内退出，无超时/强制终止。普通/诊断共用本次新增Windows/CUDA准备是源码事实，普通模式未独立运行；训练/playback/headless/Linux/CR12/扫描相机/checkpoint均未被代验。结果仅证明本次后端缺省与共用准备的组合路径。未改资产/依赖/驱动/共享配置，未执行Git写操作。Phase B CLOSED/清理边界不变；后续实施及运行不由本次文档维护自动授权。

2026-09-28（运行时兼容性）：已完成 Windows 后端定向静态评估与最小修复方案，等待 GPT/用户审阅；尚未修复、尚未运行验证。GUI 的 D3D12 成功不能代替项目入口通过；当前未定位到上次静态评估之后的项目运行失败日志。推荐项目内 Windows 参数 helper 接入现有入口，以有界 legacy viewer 验证；保留既有 CUDA 初始化、公共 event gate、Phase B CLOSED 和清理边界。本次仅新增报告并小范围更新本文，未改代码/配置/资产，未启动 Isaac/CUDA/仿真，未执行 Git 写操作；后续实施及运行需另行授权。

2026-09-28（单机双视点）：已完成扫描执行环境的静态实施评估，等待 GPT/用户审阅；尚未实施、尚未进行仿真验证。用户现已确认新 USD 在遇到运行环境问题后手动删除，不再待提供路径、不恢复，也不据此认定模型损坏。后续在启动兼容性验证后沿 URDF 准备派生资产；惯性自动重算/近似尚未批准。原静态评估保留当时结论，后续实施与有限仿真需另行授权，Phase B CLOSED 及既有清理边界不变。

2026-09-26：已完成项目现状与机器人接入交接，等待用户/GPT讨论下一步。Phase B COMPLETE 状态不变；本次仅静态整理，未运行、未修改实现、未执行 Git 写操作；后续实施未授权。

Lifecycle/runtime backbone, real repeated learning, normal-horizon dynamic
lifecycle, optimization checkpoint and real fresh-process optimization
continuation: COMPLETE. Production/runtime qualification: COMPLETE.
G1-G10: 10/10 PASS. Phase-B implementation/runtime blockers: NONE.

The user explicitly authorized Codex to execute the previously reviewed
four-commit plan on 2026-09-25. This supersedes the earlier manual-only execution
boundary; it does not authorize push, tag, deletion or runtime experiments.

## Latest completed work / local commits

Branch: main. Original audited base:
b71d85a32f51be6ada324f870813a56bb45dd396.

| Group | Commit | Scope |
|---|---|---|
| A | c107a6c892eb90ff643d549d928c555ec9f9be5b | 359 monthly moves with path repairs, AGENTS and migration report; 361 current paths |
| B | 5e7367ce28f0dfc3d4de86fa90d751284f1159c3 | 11 production files |
| C | 947f9261864945ab120a7958f3cc08b38b37e44a | 96 test/helper files, 42 compact evidence JSON and root .gitignore; 139 paths |
| D | This containing docs commit: docs(mrta): finalize Phase B closure records | 233 original allowlisted docs plus the pre-execution handoff archive; 234 paths |

The local four-commit sequence is recorded in git log. D's own hash is intentionally
not embedded in its contents. The only extension to the reviewed path allowlist
is the byte-exact handoff archive required before this update.
Total: 745 current paths plus 359 old migration path deletions.

The original closeout reports, manual manifest and source/config/index freeze
identities remain unchanged historical pre-commit records. Their earlier
NOT PERFORMED / READY FOR MANUAL COMMIT wording is superseded by this handoff,
not retroactively rewritten.

Git add / commit: performed under the user's new authorization, four groups.
Git push / tag: NOT PERFORMED. Runtime rerun: 0.
No production, harness, installed HARL or runtime artifact contents were edited
during commit execution. Only this handoff was updated and its archive added.

## Checks and retained local work

- Initial branch/HEAD/index matched the reviewed manual plan.
- One additional untracked phase_b_git_closeout_artifacts.zip was detected:
  left on disk, excluded from all commits.
- 52 repository/installed source hashes and 34 final artifact hashes matched
  the accepted authority before staging.
- All original 744 allowlisted files existed, were distinct and were below 1 MB.
- Every commit used exact NUL-delimited file paths and an exact staged-path guard;
  committed path-scope checks passed. A-C staged whitespace checks passed.
- D retains 27 pre-existing whitespace notices in 12 historical Markdown reports
  (25 trailing-space/hard-break lines and 2 extra EOF blank lines). Their byte
  hashes match the pre-commit snapshot; historical reports were not reformatted.
  The newly edited handoff passes its scoped whitespace check.
- A includes 720 raw add/delete/modified paths; B11, C139, D234.
- Git's automatic internal object packing during A completed; no runtime
  artifact cleanup was performed.
- The index is empty after the completed sequence. A clean worktree is NOT
  expected: historical generated data, the newly noticed ZIP and the unrelated
  .vscode/.gitignore edit are intentionally outside these commits.

Pre-execution handoff archive SHA-256:
9b622fe42ff83510a0bf388587b59b4dc062aa7fdb77fbeb497ddd4df8d2fad0.
Its bytes were verified identical before this rewrite.

## Active architecture / accepted result

Reviewed event learner:
execute_real_isaac_single_transaction_v1 ->
execute_full_learner_transaction_v1, with frozen plans and S0-S10 coordination.

Environment-owned lifecycle and pre-reset terminal authority; row-local
event/DVM decisions; actor PPO/HAPPO factor updates; critic/live ValueNorm;
ordered rollover and quiescence; complete optimization checkpoint state.
Generic runner.train() still delegates to inherited HA training: a paper entry
must explicitly use the reviewed event coordinator and saved progression.

Accepted final closure, not rerun here: A actor steps (5,5,5), critic10, VN10,
one checkpoint save; fresh B strict full-state load before collection, then its
own plan (5,5,10), critic10, VN10. Adam/VN/progression/LR continuity and clean
process exits passed. No convergence, policy-quality, simulator/RNG trajectory
resume, variable-cardinality or completed paper-campaign claim is made.

## Remaining work / boundaries

Phase-B approved local artifact cleanup: COMPLETE.
Classification: PHASE-B-LOCAL-ARTIFACT-CLEANUP-EXECUTED.
Phase B remains COMPLETE / GPT REVIEW PASS / CLOSED.

The original two hash-bound delete manifests and original validator remain
unchanged. The user's supplement permits exactly one ALREADY_ABSENT entry:
202609/20260925/phase_b_git_closeout_artifacts.zip (36,178 manifest bytes).
It was absent before execution; cause remains UNKNOWN. It was not recreated
and is not counted as deleted or as space reclaimed by this task.

Originally approved: 50,639 files / 12,122,958,520 logical bytes.
Effective approved set: 50,638 files / 12,122,922,342 logical bytes.
Actually deleted: 50,638 files / 12,122,922,342 logical bytes.
Failed file deletions / remaining effective targets: 0 / 0. Added targets: 0.
Physical free-space delta was not measured; logical bytes are not that delta.

Original STOP-PRECHECK (missing ZIP, zero deletions) remains unchanged.
The first single-absence wrapper also stopped before deletion (empty
ARCHIVE_OPTIONAL aggregation under strict mode). Its zero-deletion records
remain unchanged. A new wrapper corrected only empty-set summation and used
new output names; the original/adapted validators and deletion checks did not
change. Full precheck and bound Recheck then passed before actual deletion.

Postchecks: all 50,638 effective targets absent; 6,326 non-target files retain
their pre-delete content hashes and all 2,884 directories remain. Required646,
compact211, local-useful7 and UNKNOWN3,602 remain. Final23 JSON and seven R14
ledgers match original audit hashes; CKPT1 retains19 unchanged compact JSON.
This handoff is the only existing document updated after those checks.

Final historical smoke checkpoint tensors: DELETED AS APPROVED /
EXACT OLD CHECKPOINT NO LONGER LOADABLE. Historical raw replay/detail links:
INTENTIONALLY PARTIALLY UNAVAILABLE (audit: 14 reports / 294 detail links).
No artifact backup, move, compression or directory deletion. Deleted untracked
bytes cannot be restored through Git. UNKNOWN legacy data: RETAINED / NOT CLEANED.
Retained core evidence: PRESERVED. Historical reports/STOP records unchanged.

Tracked deletions: 0. HEAD/index/tag refs/root ignore/local exclude unchanged.
Runtime, checkpoint load/save and Git add/commit/push/tag operations: 0.
No production, test, harness or installed HARL source changed. Only cleanup
adapters/new execution records/report/archive and this handoff were added/edited.
The handoff was archived byte-exactly before this update (SHA256:
40d8668cecc7c0ab131ab03abd1cf3ab6f16e57e2b8f916ee752a814c5435bbc).
All new/modified files remain unstaged/uncommitted.

Next: STOP. Approved cleanup scope is complete. Do not rerun pre-deletion
existence validators on the now-deleted snapshot. Do not clean UNKNOWN,
repair the lifecycle tag, stage/commit/push or start experiments.
PAPER-1 EXPERIMENT IMPLEMENTATION AND PROTOCOL requires separate authorization.

R6: HISTORICAL / NO RETRY. R7: NOT USED.
R15: NOT AUTHORIZED / NOT NEEDED FOR PHASE-B CLOSURE.
Do not reopen Phase B, rewrite historical verdicts/freeze identities, activate
public routes, change installed HARL, push or tag without further authorization.
Optional tag remains lifecycle-mrta-phase-b-complete; not created.

## Detailed reports / archives

- [报告主题导航（优先按主题查找当前主报告）](REPORT_INDEX.md)
- [CR12扫描执行层与lifecycle authority接入方案（2026-10-07，仅源码/契约分析，未实施/运行，待审）](202610/20261007/CR12_EXECUTION_LIFECYCLE_INTEGRATION_PLAN.md)
- [CR12双视点连续按需采集（2026-10-07，同场景/同Camera复用、1324步PASS，现已获GPT REVIEW PASS，旧报告保留当时状态）](202610/20261007/CR12_TWO_VIEW_CAMERA_CAPTURE_REPORT.md)
- [CR12单视点按需相机采集（2026-10-07，真实RGBA/独立OFF/正常退出PASS，现已获GPT REVIEW PASS，旧报告保留当时状态）](202610/20261007/CR12_SINGLE_VIEW_CAMERA_CAPTURE_REPORT.md)
- [CR12 visual预初始化集成（2026-10-07，已有GPT REVIEW PASS，两处外观用户已确认）](202610/20261007/CR12_VISUAL_PREINIT_INTEGRATION_REPORT.md)
- [CR12扫描前visual一致性（2026-10-04，四图支持局部修复；native复核失败，整体FAIL，历史FAIL保留）](202610/20261004/CR12_VISUAL_GEOMETRY_CONSISTENCY_REPORT.md)
- [CR12有界OBB精化与大幅关节往返（2026-10-04，该demo现已数值审阅与人工接受；旧报告保留当时状态）](202610/20261004/CR12_OBB_REFINEMENT_AND_LARGE_JOINT_SWEEP_REPORT.md)
- [CR12外力逐迭代单因素实施与原条件复测（2026-09-30，显式on完整720步PASS，待审阅）](202609/20260930/CR12_EXTERNAL_FORCES_SINGLE_FACTOR_REPORT.md)
- [CR12保持诊断与PD复测（2026-09-29，三次保持FAIL，待审）](202609/20260929/CR12_HOLD_DIAGNOSIS_AND_PD_RETEST_REPORT.md)
- [CR12派生资产生成与基本关节驱动实施报告（2026-09-29，完整保持验收FAIL，待审）](202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_IMPLEMENTATION_REPORT.md)
- [CR12派生资产参数与基本关节驱动实施方案（2026-09-29）](202609/20260929/CR12_DERIVED_ASSET_AND_JOINT_DRIVE_PLAN.md)
- [Windows 启动补丁实施与有界GUI/CUDA/viewer验证（2026-09-29）](202609/20260929/WINDOWS_RUNTIME_BACKEND_IMPLEMENTATION_AND_VALIDATION_REPORT.md)
- [Windows 运行时后端：静态兼容性评估与最小修复方案（2026-09-28）](202609/20260928/WINDOWS_RUNTIME_BACKEND_ASSESSMENT_AND_PLAN.md)
- [单机器人双视点扫描执行环境：静态实施评估（2026-09-28）](202609/20260928/SINGLE_ROBOT_TWO_VIEWPOINT_IMPLEMENTATION_ASSESSMENT.md)
- [项目现状与目标机器人接入交接（2026-09-26）](202609/20260926/PROJECT_STATE_AND_ROBOT_INTEGRATION_HANDOFF.md)
- [Approved cleanup completed: single-absence execution](202609/20260925/PHASE_B_LOCAL_ARTIFACT_CLEANUP_EXECUTION_SINGLE_ABSENCE_REPORT.md)
- [Final cleanup execution result](202609/20260925/phase_b_local_artifact_cleanup_execution/execution_result_single_absence_final.json)
- [Byte-exact handoff before completed-cleanup update](202609/20260925/TASK_PROGRESS_ARCHIVE_BEFORE_LOCAL_CLEANUP_SINGLE_ABSENCE_20260925.md)
- [Cleanup execution: STOP-PRECHECK, zero deletions](202609/20260925/PHASE_B_LOCAL_ARTIFACT_CLEANUP_EXECUTION_REPORT.md)
- [Execution authority, stop log and result](202609/20260925/phase_b_local_artifact_cleanup_execution/)
- [Byte-exact pre-execution-update handoff](202609/20260925/TASK_PROGRESS_ARCHIVE_BEFORE_LOCAL_CLEANUP_EXECUTION_20260925.md)
- [Local cleanup audit: partial legacy review, no deletion](202609/20260925/PHASE_B_LOCAL_ARTIFACT_CLEANUP_AUDIT.md)
- [Future delete execution plan: approval required](202609/20260925/PHASE_B_LOCAL_ARTIFACT_DELETE_EXECUTION_PLAN.md)
- [Exact cleanup manifests and read-only verification](202609/20260925/phase_b_local_artifact_cleanup_audit/)
- [Byte-exact pre-cleanup-audit handoff](202609/20260925/TASK_PROGRESS_ARCHIVE_BEFORE_LOCAL_CLEANUP_AUDIT_20260925.md)
- [Byte-exact pre-commit handoff](202609/20260925/TASK_PROGRESS_ARCHIVE_BEFORE_AUTHORIZED_PHASE_B_COMMITS_20260925.md)
- [Engineering closeout, historical pre-commit audit](202609/20260925/PHASE_B_ENGINEERING_GIT_CLOSEOUT_REPORT.md)
- [Change classification](202609/20260925/PHASE_B_GIT_CLOSEOUT_CHANGE_CLASSIFICATION.md)
- [Implementation summary](202609/20260925/PHASE_B_IMPLEMENTATION_CHANGE_SUMMARY.md)
- [Reviewed four-commit plan](202609/20260925/PHASE_B_MANUAL_COMMIT_PLAN.md)
- [Original closeout JSON audits and allowlists](202609/20260925/phase_b_git_closeout_artifacts/)
- [Final runtime report](202609/20260924/PHASE_B_FINAL_CLOSURE_REPORT.md)
- [Final runtime result](202609/20260924/phase_b_final_closure_artifacts/final_result.json)
- [Readiness audit, reviewed closed](202609/20260924/PHASE_B_FINAL_CLOSURE_READINESS_AUDIT.md)
