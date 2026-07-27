# Phase 10A — Authoritative V2 Revision Summary

```text
classification:
  REVISION-COMPLETE-AWAITING-GPT-REVIEW

document_status:
  AUTHORITATIVE-DESIGN-CANDIDATE

verified_against_head:
  e3febe417c5323e28ceb9e256ba71dcd44f3c457

implementation_authorization:
  none -- documentation gate only

enter Phase A:
  no -- wait for targeted GPT re-review and user confirmation
```

---

## 1. Revision scope

本轮根据：

- [Phase 10A HAPPO/HARL 接口审计](../20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md)；
- [原 design backup 独立审核](../20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_DESIGN_BACKUP_REVIEW.md)；
- 当前 HEAD；
- 当前环境实际 import 的 installed HARL；
- 用户在本轮明确冻结的目标契约；

创建了：

- [Lifecycle-Aware Event-Gated Local MRTA Authoritative V2](Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_20260727.md)。

本轮只修订文档和 contract provenance。没有修改 environment、wrapper、resolver、reward、
runner、trainer、buffer、checkpoint、YAML、测试或 installed HARL。

---

## 2. 原文件状态

原文件：

- [Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Backup_20260724.md](../20260724/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Backup_20260724.md)

处理：

```text
retained:
  yes

modified:
  no

status:
  historical discussion snapshot -- superseded by V2 for design recovery

pre-revision SHA-256:
  A9DD70253EC78575C14394B4F566505A5C85F0BFD0440D76E2F44403E55A42FC
```

V2 与 `TASK_PROGRESS.md` 标记 superseded；没有在原文件顶部增加提示，因此原正文和哈希应
保持不变。

---

## 3. V2 修订内容

V2：

1. 增加精确 metadata、HEAD、review basis 和 candidate approval gate；
2. 定义五个统一状态标签；
3. 明确第一篇 fixed-cardinality 与第二篇 variable-cardinality 边界；
4. 冻结唯一 canonical strict order 和 event taxonomy；
5. 分离 task lifecycle、robot lifecycle 与 current prototype；
6. 完整冻结 local set、Top-K、一轮 owner expansion、overlap merge 和 cap overflow；
7. 删除 objective-level `lambda_align`，恢复 expected-time direct sum；
8. 冻结 semantic action、executing-noop mask 和 DVM；
9. 分离 rejected SWITCH 与 rejected CLAIM fallback；
10. 冻结 proposal/effective/controller 数据流；
11. 冻结 transfer graph、component closure、pair gate、objective、transfer counting 和
    deterministic arbitration；
12. 冻结 failed pair、`TEAM_INFEASIBLE`、termination 与指标；
13. 冻结 component-once rejection 与 mean-then-penalty team reward；
14. 冻结 HAPPO DVM、zero/singleton、empty minibatch 和 sequential factor；
15. 明确 DirectMARLEnv 的确定 auto-reset，并冻结 pre-reset DTO；
16. 冻结 feature-off direct bypass 和 checkpoint v2/v3 dispatch；
17. 新增 baseline fairness boundary；
18. 新增参数/证据/owner-phase/validation 表；
19. 补全 Phase A/B0/B/C/D/E；
20. 新增 current-vs-target、verification gates、quick recovery 和 glossary；
21. 增加 DR-01～DR-21 resolution matrix。

所有目标行为均标记为 `[FROZEN-TARGET-NOT-IMPLEMENTED]`，没有写成当前已经实现。

---

## 4. Finding resolution matrix

`RESOLVED` 表示 V2 已关闭文档问题，不表示代码实现、数值确定、实验完成或最终批准。

| Finding | Severity | V2 section | Resolution |
|---|---|---|---|
| DR-01 | CRITICAL | Nominal cost contract | RESOLVED |
| DR-02 | HIGH | 固定物理步、事件和唯一 strict order | RESOLVED |
| DR-03 | HIGH | Local set、Top-K 与 observation | RESOLVED |
| DR-04 | HIGH | Action semantics 与 decision-valid mask | RESOLVED |
| DR-05 | HIGH | Assignment-tick retry；Resolver；Transfer component | RESOLVED |
| DR-06 | HIGH | Pair gate、component objective 与 transfer counting | RESOLVED |
| DR-07 | HIGH | Authoritative pre-reset transition facts | RESOLVED |
| DR-08 | HIGH | Default-off direct bypass；Checkpoint semantic contract | RESOLVED |
| DR-09 | HIGH | Metadata；状态标签；当前代码能力快照 | RESOLVED |
| DR-10 | HIGH | Baseline fairness boundary | RESOLVED |
| DR-11 | MEDIUM | 研究范围与论文边界 | RESOLVED |
| DR-12 | MEDIUM | Task 与 Robot lifecycle | RESOLVED |
| DR-13 | MEDIUM | Failed pair；Episode termination 与指标 | RESOLVED |
| DR-14 | MEDIUM | Rejection reward | RESOLVED |
| DR-15 | MEDIUM | Team reward contract | RESOLVED |
| DR-16 | MEDIUM | HAPPO decision-valid contract | RESOLVED |
| DR-17 | MEDIUM | Zero-valid 与 singleton advantage | RESOLVED |
| DR-18 | MEDIUM | Phase A–E implementation route | RESOLVED |
| DR-19 | MEDIUM | 参数、证据与消融边界 | RESOLVED |
| DR-20 | MEDIUM | Authority、证据与 Quick recovery checklist | RESOLVED |
| DR-21 | LOW | 标题层级与 Glossary | RESOLVED |

```text
findings:
  total:               21
  RESOLVED:            21
  PARTIALLY-RESOLVED:   0
  NOT-APPLICABLE:       0

unresolved CRITICAL:
  0

unresolved HIGH:
  0
```

---

## 5. 尚存开放项

以下是显式管理的后续工作，不是未解决 review finding：

### `[NUMERIC-TBD]`

- Top-K；
- local robot/task caps；
- pair absolute/relative thresholds；
- component absolute/relative thresholds；
- transfer penalty；
- rejection penalty；
- alignment time constant；
- assignment retry cadence。

### `[IMPLEMENTATION-EVIDENCE-TBD]`

- real navigation expected-time estimator；
- real terminal-alignment expected-time estimator；
- authoritative execution/lifecycle signal；
- per-baseline adapter。

### 尚未实现

- event-gated local-set/mask/DVM；
- transfer-component resolver；
- pre-reset DTO/hook；
- DVM-aware repo-local HAPPO；
- explicit team reducer/rejection penalty；
- formal `TEAM_INFEASIBLE` termination；
- new semantic checkpoint version。

这些项目已经分配到 Phase A–E，不需要重新设计整体方法。

---

## 6. 为什么总体路线不变

Phase 10A 已确认现有：

- global fixed-width observation；
- global task IDs；
- historical action mask storage；
- proposal/effective 分离；
- effective-to-controller path；
- fixed-step rollout/GAE；
- EP centralized critic skeleton；
- `[T,E,1]` HAPPO factor shape；

可以复用。

所需变更集中在 repo-local typed interface、runner/buffer/HAPPO、lifecycle authority、
local mask、atomic resolver、reward 和 semantic checkpoint，不构成 architecture blocker。

因此仍为：

```text
RUNNER-CHANGES-REQUIRED
```

路线仍为：

```text
Phase A
→ Phase B0
→ Phase B
→ Phase C
→ Phase D
→ Phase E
```

---

## 7. 为什么尚不能进入 Phase A

V2 当前是：

```text
AUTHORITATIVE-DESIGN-CANDIDATE
```

文档 finding 已 21/21 解决，但尚未经过 targeted GPT re-review，也尚未获得用户确认。
本轮没有实现授权。因此：

```text
enter Phase A:
  no -- wait for targeted GPT re-review and user confirmation
```

targeted review 通过后，只进入 Phase A；不跨越到 B0/B/C/D/E。

---

## 8. 推荐 targeted GPT review 重点

1. nominal cost 是否完全移除 objective-level `lambda_align`；
2. canonical order 是否只有一个且 terminal branch 正确；
3. current-task retention 是否只作用于 event-updated baseline 中仍合法的 task；
4. semantic action count、executing noop 和 singleton DVM；
5. rejected SWITCH/CLAIM fallback；
6. component closure 与 “CONTINUE 可被覆盖”是否不允许 resolver 发明任务；
7. count-increase 是否仍经过 pair gate；
8. transfer counting 和 unowned conflict arbitration；
9. team reward 是否严格 mean → component penalty → broadcast；
10. zero/singleton、empty minibatch 与 factor identity；
11. pre-reset DTO authority/generation/consume-once；
12. feature-off direct bypass 与 v2/v3 compatibility；
13. baseline fairness；
14. current-code statements 与 HEAD；
15. DR-01～DR-21 是否恰好各解决一次。

targeted V2 review 尚未生成；后续文件路径应由最新 `TASK_PROGRESS.md` 路由。

---

## 9. 本轮边界

```text
runtime behavior changed:
  no

training:
  not run

playback/evaluation:
  not run

Isaac Sim/AppLauncher:
  not run

checkpoint load/modify:
  none

installed HARL modified:
  no

commit:
  none
```

