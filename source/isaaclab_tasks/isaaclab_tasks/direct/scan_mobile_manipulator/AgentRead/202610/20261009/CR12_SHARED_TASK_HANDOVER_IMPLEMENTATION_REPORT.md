# CR12 共享任务取消、物理让行与跨机器人认领实施报告

日期：2026-10-09，Asia/Shanghai（UTC+08:00）。仓库：`E:\Project\IsaacLab_HARL`。本轮 HEAD：`a8c618a32da65747827f1cb3f722fac24df2aec8`，branch `main`；保留既有双机/启动 dirty 修改，未执行 Git 写操作。

路径缩写：T=`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/`；E=`scripts/environments/`；Q=`source/isaaclab_tasks/test/`；L=`logs/scan_assignment/20261009_cr12_shared_task_handover/`。均相对仓库根。本文是阅读入口，Python 实现与测试不放入 AgentRead。

## 1. 执行结论与授权边界

本轮依据用户新授权实现已审固定 `E1/M2/N1`，没有重新搜索布局。`shared_m2n1` 显式接入原执行器、Camera FSM、Host、adapter 与真实 lifecycle authority；旧 single/dual/formal/manual 默认分支保留。64 项新增 CPU 检查通过；一次三段生产 AABB 名义推进通过，不能用它代替真实 PD、PhysX、相机或转交结果。

唯一 App 结果为 **CR12_SHARED_TASK_HANDOVER_INTEGRATION_FAIL**。启动、双实例准备、共同非零setup、A实际到位及无数据取消/OFF通过；A保留原绑定退出至第3842受控步时，被原contact新鲜度守卫拒绝。尚未到clear、没有R/receipt/退役，B未认领/采集，共同terminal未到达。全树自然退出，无超时/强杀；App **1/1已用完**。这不是启动原生故障、不是取消数据竞争NOT_HIT，也不是完整转交PASS。

App 开始后没有修改实现、测试、监督器或参数。Phase B 保持 **COMPLETE / GPT REVIEW PASS / CLOSED**；单机及分区双机已接受范围不变。本轮不自行写 GPT REVIEW PASS，不训练、不启用公共 event、不改资产/PD/solver/依赖/Windows 共用 helper。

## 2. 固定输入与实际改动

唯一物理资产为 `T/assets/rokeaCR12/derived/fixed_lift0_v1/usd/cr12_fixed_lift0.usd` 及既有引用层；数学链来自同一目录上级的 `cr12_fixed_lift0.urdf`。没有生成或修改机器人资产。

| 项目 | 冻结值 |
|---|---|
| A root | xyz=(0,0,0.053)m；WXYZ=(1,0,0,0) |
| B root | xyz=(1.0983385754148558,-0.30,0.053)m；WXYZ=(0,0,0,1) |
| A park/clear → goal，关节1…6，度 | [0,-16,20,0,-4,90] → [0,12,20,0,-32,90] |
| B park → goal，度 | [0,-16,20,0,-4,-90] → [0,12,20,0,-32,-90] |
| 唯一 task | global task_id=0；两次 claim 的冻结 world scanner matrix 完全相同 |
| T_ES / T_SC | Rz135°；相机相对 scanner 平移(0.168921722410,-0.129429244995,0.192403900145)m、旋转I |
| 独立资源 | /World/CR12_0、/World/CR12_1；各7体/6关节/10 collision、各 Camera/product/observer；本地 articulation batch始终[0] |
| 共享板 | /World/SharedTaskCameraFixture；非物理；由唯一目标×T_SC，沿 camera world-style +X 0.5m 一次创建 |
| Camera | 原640×480 RGBA、pinhole/clipping；挂本台link_6，轴转换只应用一次 |

唯一 scanner 世界目标：

```text
[-0.7071067811865477  +0.7071067811865474  0  +0.5491692877074279]
[-0.7071067811865474  -0.7071067811865477  0  -0.1500000000000000]
[ 0                    0                   1  +2.7893381484821624]
[ 0                    0                   0   1                 ]
WXYZ=(0.3826834323650896,0,0,-0.9238795325112868)
```

所有生产输入来自新纯 CPU 模块 `_cr12_shared_task_profile.py`；没有读取 logs 内旧 `final_candidate.json`。原8秒、4秒/16秒诊断及较宽轴3信任域均未接入。

| 文件/关键符号 | 本轮变化与保护范围 |
|---|---|
| E/_cr12_shared_task_profile.py：root_pose:58、FrozenJointWitnessPoseSegment:92、segment:122 | 不可变配置，rad一次转换、三段FK参考、角色和总预算唯一来源；返回冻结目标 |
| E/_cr12_pose_control.py：select_motion_profile:98、check_path_tube:305、check_fixed_neighborhood:330、CommandIntegrator:471 | 显式新profile、六轴共同进度区间求交、固定park邻域、向量信任半径；原formal/manual及原命令拒绝规则保留 |
| E/_cr12_runtime_support.py：spawn_fixed_cr12_instance:768、initialize_fixed_cr12_state:922 | 受信xy/yaw与初态参数；pre-init root/物理anchor一致；旧2m布局/零初态默认保留；原self/cross AABB数学检查未放宽 |
| E/_cr12_camera_mount.py：create_shared_fixture:145、create_camera_and_fixture:179 | 一块显式stage归属板，两个相机合法引用；不重复建板，不运行期改挂载 |
| E/run_cr12_single_view_capture.py：initialize_dual_capture_runs、main | 新profile显式接线，双实例一次reset、各一次初态写入、共同一次不推进clock的forward；保留UTF8/CUDA/App/visual顺序；异常分类保留NOT_HIT |
| E/_cr12_scan_executor.py：begin_setup_hold:415、complete_setup_hold:431、submit_bound_segment:459、prepare_tick:582 | 非阻塞setup、同binding退出段、最初trust anchor/q_cmd连续、段局部monitor/deadline；没有新增step/render循环或运行期状态回写 |
| E/_cr12_single_view_capture.py：SingleViewCaptureRequest.__init__:41 | 只对trusted shared profile使用3840 approach/4680 request；旧960/1800保留 |
| E/_cr12_capture_runner.py：delivery_ready:116、begin_retreat:153、_observe_cleanup:181、boundary:401 | Camera终态与可交付分离；OFF无成果后健康退出；固定clear+同刻peer窗；scan/cleanup目标独立记录；late raw竞争保留并NOT_HIT |
| E/_cr12_lifecycle_host.py：reset、_run_setup_hold、_advance_physics、step、_deliver | 一个物理调度器供持锁setup与合法任务块共用；clear后块末pending；真实receipt后退役；最新A clear约束B准入及执行；终态只逻辑rebuild |
| T/assignment_cr12_execution_adapter.py：ExecutionBoundaryEvidence:93、record_pending:355、build_report:386、ack_authority_deliveries:509、retire_request:546 | 固定shared_m2n1维度及clear-R证据验证，仍复用原producer/transaction/consume-once/receipt；未改核心authority |
| E/run_cr12_shared_task_handover.py | 薄入口；确定性A→B proposal，真实resolver/claim；73/71 schema及旧episode唯一完成归属检查 |
| L/repro/supervise_cr12_shared_task.py | 本任务独立max_apps=1/case/预算；只复用历史owned-process/排空/配置工具，不调用旧main或恢复旧额度 |

`_cr12_camera_capture.py`、GUI诊断、旧dual入口、旧runtime hooks测试在开始时已有修改，本轮没有覆盖它们。Git相对HEAD的完整diff包含这些既有工作，不能全部算作本轮改动。

## 3. 运动、setup、管道与时钟

参考使用固定五次时间函数 `h=10u³−15u⁴+6u⁵`，u=clip(t/24s,0,1)；将冻结关节witness输入FK，得到scanner pose参考，再经原反馈DLS λ=.01、COM Jacobian adapter和CommandIntegrator下发q_cmd/dq_cmd。没有直接下发witness曲线，也没有逆动力学前馈。monitor、提交与post-step均沿原同刻t_k。

最初q_initial信任域始终为[5,30,5,5,30,5]°，轴3没有扩展；raw DLS≤.035rad、q_cmd−actual≤.035rad、单步≤.00125rad、command速度≤.15rad/s、actual≤.25rad/s、物理限速.2rad/s、硬限位余量.02rad，沿原拒绝规则。K=[200,4000,2000,200,1000,150]，D=[20,550,166,12,37,7]，effort=[20,60,30,10,10,5]Nm均未变。

活动actual必须存在**同一个s**，使六轴同时位于park+s(goal−park)±.5°；s不等于当前参考时间进度。等待/setup/clear必须落在固定park±.5°。q_cmd允许承载偏置，但全部原命令限制和中点/终点self/cross检查继续执行；没有用actual窄管道去约束q_cmd，也没有改用OBB。

原AABB仍检查每台32个禁止self pair、原ground、跨机100个shape pair和每侧2mm余量；整机粗包围盒重叠后逐shape判断。两个机器人各7个contact sensor维持同刻fresh读取；post-step检查实际body/link位姿，不能用名义FK代替。碰撞几何/检测并不等于一般避障规划。

setup在authority rebuild锁内只走共同物理调度，不读domain/claim/finalize。初态每台仅写一次；一次共同reset含warm2步，随后共同forward只发布Fabric。SETUP_SETTLING最多360tick，两台同一个末窗需121连续post-step、跨度≥1s，scanner≤2mm/.25°、每轴native|dq|≤.01、固定park管道、OFF/健康全部同时成立，才commit reset-complete并合法OPEN。READY后丢失保持即失败，不重回settling。

每个合法任务transition依次两台prepare→联合命令几何→两台submit→唯一physics step→两台actual/native/contact/frame/管道→global cadence render→各runner/cleanup；D=12、dt=1/120、render_interval=2。setup S单列，global parity和q_cmd从首setup受控步连续；完整受控总数=S+12×已完成transition，失败块已执行步另记。

| 预算 | 冻结上限 |
|---|---|
| A进/A退/B进 | 每段reference24s；到位3840tick/32s；原发散3cm/5°连续12点、无进展及121点到位窗保留 |
| Camera capture / close | 600tick且60s wall / 240tick且30s wall；OFF至少30个正常render机会及原quiet条件 |
| Camera FSM / binding | 请求4680；A整体8520、B4680；ready后的当前块尾最多12另计 |
| Host与总clock | ≤1120 transitions、task physics≤13440、setup≤360；总受控≤13800、warm2另计、受控render≤6900 |
| 外层 | App构造≤180s，所属树≤2400s（预留10s收尾）；最多一个App，无重试 |

## 4. 取消、物理让行和真实转交

固定A raw=[[0,1]]/decoded=[[0,-1]]；没有新claim的块使用step_without_new_claim。两台feasible均true，N1 NO_CLAIM=1。A稳定到位后真实ON/WAITING_DATA，在下一次可能产帧前用已有取消边界取消一次；不暂停render、不丢弃图像。

只有CANCELLED、稳定WAITING_DATA来源、后端无raw/fresh/acquired、OFF确认且资源健康，才进入RETREATING_BOUND。Camera保持真实FAILED_OFF；原claim/binding/goal/capture保留，adapter pending仍None，Camera不retire/release/再ON。submit_bound_segment只切goal→park参考与局部monitor/deadline，不重设actual/q_cmd/trust anchor。Camera终态后不再累加旧FSM期限。

clear资格需要A固定六轴/pose/native dq窗口，且整个窗B固定park、OFF健康、同刻原守卫通过。clear后的块尾继续反馈保持，最新边界不合格就拒绝R。只在块末建立pending R，经真实typed report→producer→transaction→receipt校验→边界复核→Camera退役→adapter退役。receipt后局部失败保留已提交事实并poison，不重发/回滚。

下一OPEN确认真实task0 AVAILABLE/owner=-1、A receipt与退役完成、A最新clear/OFF和Bpark健康，才给B raw=[[1,0]]/decoded=[[-1,0]]；authority仍决定effective。B沿同一目标接近、fresh/OFF、真实C；A持续clear/OFF。B完成后不退出或重写初态，terminal只合法逻辑rebuild/五元组/历史payload/ACK。旧episode完成[0,1]与新episode归零分别记录，actor73、critic/pre-reset sidecar71。

任何A raw/acquired竞争必须保留数据并NOT_HIT，不伪造无数据R，不继续B。采集成功、文件保存、关闭确认、authority完成独立；关闭失败不能抹除已取得数据，也不能开始下一段运动。实际关节驱动力未收集时明确为NOT_COLLECTED，不用估算负载当实测。

## 5. CPU准入及一次名义生产AABB推进

新增64个不重复测试方法：profile/runtime17、executor14、runner/adapter19、真实Host7、监督器7。最后合并runner/Host/监督器为33 passed、11 subtests passed；独立方法与subtest不重复累计。相关旧pose/mount/runtime hooks17、executor及unbound保持15已通过；最后另选旧single/dual Host及adapter6项通过。未重跑旧202/182/36总套件或Phase B。

测试覆盖冻结SE(3)/单位/四元数、B误放、初态单写、setup锁内无authority/未ready拒绝、共同s与非有限拒绝、固定clear区别、原锚/q_cmd连续、t_k与段时钟、camera终态不直接pending、clear块尾劣化、receipt前清理拒绝/receipt后poison、旧A身份不能污染B、fresh竞争NOT_HIT、真实N1编码/71维sidecar/ACK、terminal无新setup/physics、内部失败不能由PNG/exit0覆盖。Host测试fake physics/events，但claim/resolver/producer/transaction/facade与Camera FSM使用生产实现，不是mock authority。

CPU联调中修正了setup摘要中list/ndarray的JSON序列化、fixture字段及监督器对retreat期间合法非clear块的统计；都发生在App前。初版测试曾因import重复收集旧类显示较多数目，最终去重，不将重复计为新增。一次Conda多行`-c`被Conda包装层拒绝，未进入Python/App；改为单行base64传递标准库检查后通过，没有修改环境。

名义推进只运行一次：实际新reference/integrator/monitor、float32提交；从本地controller/math源码AST提取相同数学方法，仅去掉JIT装饰，CPU torch无CUDA。直接调用生产self/cross AABB，没有复制放宽版guard、没有OBB fallback。两台保持/移动均推进，A实际名义终点和q_cmd传入retreat，等待者保持其控制状态。

| 名义段 | tick / 秒 | 最大参考位置误差 | 最大raw DLS | 终点位置误差 | 末窗 |
|---|---:|---:|---:|---:|---|
| A接近 | 3000 / 25 | 23.960097mm | .019044191rad | .038515mm | 121 / 1s |
| A退出 | 3000 / 25 | 23.960024mm | .019036569rad | .038560mm | 121 / 1s |
| B接近 | 3000 / 25 | 23.960096mm | .019044161rad | .038510mm | 121 / 1s |

名义合计9000tick；27002次几何调用、54004次单机器人检查、2700200个跨机逻辑pair、883200个fine pair。最小返回轴间隔0.0000479248m；它是本guard的局部分离轴统计，**不是PhysX连续距离，也不是先前报告39.429170mm几何下界**。理想actual=q_submitted不含PD/新setup承载偏置、真实contact/native/渲染；仅支持App准入。

最终编译27份直接源码/新测试，21份直接运行输入冻结；`preflight.json`记录新增检查及code SHA256。只冻结本轮调用链，没有全仓/历史哈希审计。

## 6. 唯一真实运行结果

### 6.1 最终分层

| 层 | 实际结果 | 证据/限制 |
|---|---|---|
| IMPLEMENTATION_CPU | PASS | 64新增、相关旧子集、一次名义AABB、输入冻结 |
| GUI_APP_CONSTRUCTION | PASS | 本次实际D3D12/native1440×900，12项启动读回全部true |
| STARTUP_AND_INSTANCE_SETUP | PASS | 两个独立native对象/映射、一次共同reset/warm2、各初态单写、共同forward、Jacobian语义通过 |
| NONZERO_SETUP_HOLD | PASS | S=221；共同121样本/1.000000052s；没有setup claim或假transition |
| A_APPROACH_AND_CANCEL_OFF | PASS | 实际目标到位3000tick；ON→WAITING_DATA→一次取消；无raw/fresh/acquired；59tick关闭、30render/30quiet确认 |
| A_BOUND_RETREAT_AND_CLEAR_RELEASE | FAIL | 已保留绑定真实退出，但contact_monitor在global3842拒绝；未达到固定clear、无R |
| B_SHARED_TASK_CAPTURE | NOT_REACHED | B begin=0、无claim、无数据；不是B采集失败 |
| AUTHORITY_TERMINAL_AND_SHUTDOWN | NOT_REACHED | 无业务terminal/rebuild/ACK；单独的失败收尾/自然进程退出完成 |

监督器完整完成谓词中的`a_cancel_off=false`要求已保存的最终退役request，因此没有达到；阶段层的A_APPROACH_AND_CANCEL_OFF=PASS依据live request真实OFF与阶段记录，不能把两者混为矛盾。入口的IMPLEMENTATION_CPU=NOT_REACHED是入口未负责CPU证明的占位，监督器用独立preflight记为PASS。原始JSON均保持不变。

### 6.2 时间、物理计数与部分成果

运行时间为本机`2026-10-09T09:36:15.685+08:00`至`09:44:02.272+08:00`，App构造23.234s，全所属树466.578s。目标Python与内层Conda均自然exit0；监督器依据内部失败返回1，**双exit0没有覆盖业务FAIL**。无supervisor error、native fault、timeout或强杀。simulation_stop_returned/app_close_requested均true；两产品失败清理release complete=true/errors=[]，不冒充成功请求的receipt后retire。

同次Kit为`kit_20261009_093618.log`；日志文本`01:36:20`对应UTC，与本机+08:00一致；第2688/3531行分别DX12/D3D12、driver610.60。12项读回包含窗口1440×900、renderer1280×720、private config、两项DPI、camera-enabled GUI与实际后端；不重新推定DPI唯一根因。source user.config前后UNCHANGED，21份冻结代码输入前后相同。

总受控3842tick/32.016668336s；warm2另计，实际总physics3844。已完成301次真实transition/transaction，当前失败块已执行9子步：

```text
221 setup + 301×12 task + 9 partial = 3842 controlled
```

最后完整守卫边界3841；render1920。第3842虽是偶数，但在post-step contact处失败，尚未到render，不能按floor(3842/2)补造一次渲染，也没有补满失败块。

setup共同末窗从native time0.858333378到1.858333430s，221受控步完成。A/B各自稳定样本121/155，共同取121；末时native最大|dq|分别0.000412551/0.000333674rad/s，固定park误差与pose均通过。承载q_cmd已与q_initial不同，首claim继续原控制对象与integrator，未清零偏置。

| 事件 | global受控步 | 实际含义 |
|---|---:|---|
| setup ready / A真实claim | 221 | 唯一task0；claim_token=0；原binding建立 |
| A到位 / ON / WAITING_DATA /主动cancel | 3221 | claim局部3000tick/25.000001304s；121点/1.000000052s稳定 |
| A无数据OFF确认 / 切retreat | 3280 | FSM局部3059；close59tick/30正常render/30quiet；无本产品事件/在途数据 |
| 最后完整边界 | 3841 | A仍RETREATING_BOUND、clear stable_samples=0；Bpark/OFF，pending与delivery均无 |
| contact监控拒绝 | 3842 | retreat已实际562tick/约4.683333s；第562未完成全部post-step检查 |

ON时actual scanner xyz=(0.5491403341,-0.1500006914,2.7893486023)m；相机启停/来源边界带同一claim/goal/capture/product身份。切retreat首reference与actual差0.0108606mm、4.54239e-6rad，没有回写actual或q_cmd。camera request总步数停在3059，退出段没有继续消耗其FSM期限。

A后端prepare/initialize/begin各1，正常OFF确认1，retire0；B prepare/initialize各1、begin0、retire0。两台失败保留快照均raw_copy_present/fresh_identity_validated/fsm_acquired_accepted=false、errors=[]；没有PNG，也没有虚构B metadata/成功记录。最后请求槽位是未交付A请求，失败清理释放资源不会被当作authority退役。

真实claim仅1次，301块没有R/C交付；`authority_deliveries=[]`、`acknowledged_receipts_on_failure=[]`、clear_release/b_admission均null、requests最终退役列表为空。A绑定直到停止仍保留，未用健康reset解锁，也未将普通取消记永久failed-pair。Host的cancel_consumed只在receipt后退役时置true，因此本次仍false，不否定Camera实际已取消/OFF。最终[0,1]、B custody及71维运行sidecar只在CPU联调中通过，本次真实运行未到达。

### 6.3 守卫、失败样本与只读定位

原错误为`DriveCheckError(category='contact_monitor', message='Stale or invalid contact read: agv')`。来源`E/_cr12_runtime_support.py::_check_contacts:586`，具体拒绝条件在613–616：force有限、outdated=false、timestamp与last_update相符，以及每步timestamp增量与dt差≤1e-6。**不是0.1N forbidden_contact拒绝，也不是AABB重叠拒绝或运动段32秒timeout。** 错误详情没有保存四个子条件各自值，所以不能把可能原因直接定为已证明唯一根因。

最后已保存的agv contact timestamp为32.007930755615234，A/B各7sensor有效updates均3841、禁止力峰值均0。A在3842先读到native q/dq并通过joint/tube，随后agv contact拒绝；B本tick已submit，但尚未进入observe，实际记录仍3841。B的shared_execution.failure是Host传播同一个停止异常，不是第二次独立B传感器故障。A的clock/joint计数3842，contact/geometry/frame/render_clock3841；B六项3841。不能据最后已通过值宣称第3842及后续仍安全。

部分运动统计：A最大raw DLS=.019044995rad、最大单步command=.000317425rad、最大native速度=.056279965rad/s、最大command−actual=.017795605rad；B对应=.003266165rad/.000054436rad/.044725962rad/s/.005176187rad。actual管道/固定park最大残差分别.004624603/.003277130rad，均低于.008726646rad。root读回平移/旋转漂移峰值0。跨机11526次调用、7684命令检查、3841完整actual检查、1152600逻辑pair；最小返回轴间隔0.0000898475m（仅guard统计，不是连续接触距离）。没有任何守卫放宽。

失败A native q=[0.000009141,0.188930929,0.349127620,-0.000147717,-0.538340747,1.570798397]rad；dq最大约.012876187rad/s；q_cmd=[-0.000326399,0.176564395,0.338596195,-0.017401235,-0.536167145,1.570801973]rad。最后完整scanner xyz=(.524545312,-.149986893,2.798142910)m，距固定clear仍.594307m，固定q_clear误差.468633rad、clear样本0，明确不具备R资格。

**只读推断：优先核对contact timestamp精度判据。** 本地`source/isaaclab/isaaclab/sensors/sensor_base.py:197–205`按`self._timestamp += dt`更新；229/231以torch默认浮点zeros/zeros_like建timestamp，294/296在更新后赋last_update并清outdated。用最后有效值做一次独立float32算术说明：

```text
previous = 32.007930755615234
float32(previous + float32(1/120)) = 32.016265869140625
increment = 0.008335113525390625
abs(increment - 1/120) = 1.7801920572917823e-6 > 1e-6
```

这说明约32秒量级的float32量化足以触发当前固定绝对误差判断，且与失败时点相符；该计算不是新的App/传感器实测，没有补写运行证据。真实失败tick的timestamp dtype、timestamp_last_update、outdated、force finite未单独记录，仍需以后经授权确认，不能直接说“sensor实际过期”或“已证实只是误报”。名义CPU没有真实sensor，旧短时接受范围也不代验此长时读数。

另有两个报告性限制留给后续：顶层failure.phase仍为`shared_setup_settling`（Host未在后续段更新此标签），实际阶段应由global3842和`:retreat`/事件序列判断；失败清理的camera_backend快照采于release之前，release计数0不能否定随后独立camera_release.complete=true。原始输出不改写，本轮不修这些代码。

## 7. 实际命令与复现边界

工作目录为仓库根；解释器核对为 `C:\isaacenvs\isaac45_harl\python.exe`。以下是**本轮已执行历史命令**，不是追加App授权；监督器拒绝已有attempt，不能换目录绕过额度。

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -u logs/scan_assignment/20261009_cr12_shared_task_handover/repro/supervise_cr12_shared_task.py --attempt-dir logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01 --integration-case shared_cancel_clear_handover
```

监督器实际子进程命令：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run --no-capture-output -p 'C:\isaacenvs\isaac45_harl' python -u scripts/environments/run_cr12_shared_task_handover.py --usd-path 'E:\Project\IsaacLab_HARL\source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\assets\rokeaCR12\derived\fixed_lift0_v1\usd\cr12_fixed_lift0.usd' --output-dir 'E:\Project\IsaacLab_HARL\logs\scan_assignment\20261009_cr12_shared_task_handover\attempt_01' --device cuda:0 --external-forces-every-iteration on --enable_cameras --info --integration-case shared_cancel_clear_handover --gui-startup-diagnostics '--kit_args=--/app/userConfigPath=E:/Project/IsaacLab_HARL/logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01/private_config/user.config.json --/app/window/scaleToMonitor=false --/app/window/dpiScaleOverride=1.0'
```

父进程以UTF8启动；子env继承并合并PYTHONUTF8=1、HEADLESS=0、ENABLE_CAMERAS=1、LIVESTREAM=0、XR=0；未修改持久环境。原Windows helper在App前追加vulkan=false，复用camera-enabled rendering experience、原pre-App CUDA顺序、1440×900窗口/1280×720 renderer。请求值与实际读回分开，以本次Kit/诊断为准。新private配置只允许width/height/maximized三项中0–3项差异，真实source只读；DPI仍用CLI。

CPU最后实际命令包括：

```powershell
& 'D:\miniconda3\Scripts\conda.exe' run -p 'C:\isaacenvs\isaac45_harl' python -X utf8 -m pytest -q source/isaaclab_tasks/test/test_cr12_shared_supervisor.py source/isaaclab_tasks/test/test_cr12_shared_lifecycle_host.py source/isaaclab_tasks/test/test_cr12_shared_execution_contract.py
```

前期profile/runtime两文件17项、shared_executor14项分别通过；最后六项旧回归为 `test_cr12_lifecycle_host.py::FullHostTests::{test_normal_real_authority_and_terminal_transport,test_cancel_reclaim_same_task_fresh_binding_and_data}`、`test_cr12_dual_lifecycle_integration.py::DualHostTests::{test_full_stagger_real_authority_reversed_creation_order_and_one_clock,test_second_submit_failure_never_steps_or_rolls_back_first_command}`、`test_cr12_lifecycle_execution_adapter.py::AdapterTests::{test_explicit_source_and_old_default_are_preserved,test_cancel_racing_data_cannot_be_relabelled_no_data}`，使用同一conda/Python/pytest前缀执行。不把未再次运行的旧整套检查写成本轮新通过。

## 8. 未验证范围、文档与下一步

本轮只处理健康机器人稳定WAITING_DATA取消后的受控让行。硬件失效/失去运动能力接管、运动中取消、一般共享空间互斥、同时proposal竞争、多任务/多场景、真实构件、移动底盘/lift、depth/pointcloud、实体标定和策略学习均未验证/未实施。唯一共享task的authority持有不是新空间owner，也不解决不同任务间一般协调。

本轮文档为本文，以及TASK_PROGRESS/REPORT_INDEX的小范围当前状态/链接更新。旧报告“App0/未实施”和历史失败保持当时事实；当前最新资产边界的分区双机待审描述更新为用户已接受，未重写历史。没有Git add/commit/push/reset/restore/clean，没有清理/恢复旧资产/日志，没有installed packages或系统设置修改。

推荐下一步先审阅本次部分成果与contact证据缺口，再另行决定是否授权**仅contact新鲜度/时间精度的定向处理**：保留真实更新调用、独立physics clock、outdated/last_update/finite/路径/shape/0.1N全部语义，补足拒绝子项及时间dtype证据，分析与实际浮点精度匹配的检查方式。不能单纯放宽阈值或关闭sensor来求通过；本轮没有实施该建议。若随后批准修复与新运行预算，再复测原固定共享链；没有理由据本次错误改布局、PD、轨迹时长、actual管道或改用OBB。

**已停止，等待GPT/用户审阅。App1/1已用完；共享跨机器人转交runtime仍NOT_ESTABLISHED。** 本轮结束不自动授权修复、第二App、调参、换布局或扩大guard。

## 9. 辅助证据对应表

L通常受现有Git忽略规则影响，证据保留本机，不保证新checkout自动包含；未建立ZIP、ledger或重复证据包。

| 结论/检查项 | 文件位置 | 关键字段/符号 | 用途与限制 |
|---|---|---|---|
| 唯一数值来源 | [shared profile](../../../../../../../../scripts/environments/_cr12_shared_task_profile.py) | roots、initial_q、scanner_target、segment、预算 | 生产配置，不从logs加载 |
| 真实接线 | [入口](../../../../../../../../scripts/environments/run_cr12_shared_task_handover.py)、[Host](../../../../../../../../scripts/environments/_cr12_lifecycle_host.py)、[adapter](../../../assignment_cr12_execution_adapter.py) | next_proposals、reset/step/_deliver、record_pending/receipt | 有真实authority，无第二套owner |
| 运动/采集延后 | [executor](../../../../../../../../scripts/environments/_cr12_scan_executor.py)、[runner](../../../../../../../../scripts/environments/_cr12_capture_runner.py) | setup、submit_bound_segment、delivery_ready、boundary | 目标/clear和camera/execution终态分离 |
| 原AABB名义准入 | [脚本](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/repro/admit_shared_aabb.py)、[结果](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/repro/nominal_aabb_admission.json) | segments、geometry_counts、controller_source、assumption | 一次CPU9000tick，不含PD/PhysX |
| App前冻结 | [preflight](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/repro/preflight.json) | checks、code_sha256 | 21直接输入，不是全仓审计 |
| 唯一运行 | [command](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01/command.json)、[result](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01/result.json)、[监督结果](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01/supervisor_result.json) | stages、layers、exit、计数与失败 | 内部完成与外层退出分别核验 |
| 同次原始输出 | [console](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01/console.log)、[配置保护](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01/config_runtime_summary.json) | Kit路径/后端、source前后 | 不另造运行记录 |
| 同次Kit | [kit_20261009_093618.log](../../../../../../../../logs/scan_assignment/20261009_cr12_shared_task_handover/attempt_01/kit_20261009_093618.log) | 2688/3531行、DX12/D3D12 | 本地原日志的同次最小保留副本 |
| contact定位 | [原contact守卫](../../../../../../../../scripts/environments/_cr12_runtime_support.py)、[SensorBase](../../../../../../../../source/isaaclab/isaaclab/sensors/sensor_base.py) | _check_contacts:586/613–616；update:197、timestamp:229/294 | 原判据与时间表示；未修改sensor/守卫 |
| CPU真实事务联调 | [Host测试](../../../../../../test/test_cr12_shared_lifecycle_host.py)、[监督测试](../../../../../../test/test_cr12_shared_supervisor.py) | real facade/claim/producer/transaction、failure/partial tick与退出分类 | 物理和Camera事件为fixture，不是runtime |

