# Phase A Implementation Plan Targeted Revision Summary

```text
classification:
  PHASE-A-PLAN-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

targeted findings:
  PR-01–PR-07 RESOLVED

overall architecture:
  accepted

architectural blocker:
  none

broad redesign:
  not required

Phase A implementation:
  not started

A1a implementation authorization:
  none

Phase B0/B/C/D/E:
  not entered
```

本轮只修订：

- `PHASE_A_PURE_INTERFACE_IDENTITY_DIAGNOSTICS_IMPLEMENTATION_PLAN.md`；
- 本 summary；
- `TASK_PROGRESS.md` 及其修改前精确归档。

没有修改 Python、YAML、JSON、测试、checkpoint、installed HARL 或 runtime behavior；
没有开始 A1a。

---

## PR-01 — Facts producer and lifecycle authority

**RESOLVED**

- `ExecutionFactsProducerId.ENV_EXECUTION_FACTS_PRODUCER_V1` 只标识 environment facts
  producer；
- `LifecycleAuthorityId.LIFECYCLE_AUTHORITY_V1` 独占 facts consume、lifecycle result
  finalization 和 lifecycle event creation；
- producer stamp 与 authority stamp 是不同类型；
- environment 只产生 immutable `ExecutionTransitionFacts`，不被提前指定为 lifecycle
  authority；
- Phase A 只冻结接口，实际 runtime component placement 留给 B0；
- transition schema、failure matrix、diagnostics 和 v3 transition contract 已同步。

---

## PR-02 — Three disjoint record systems

**RESOLVED**

- `LifecycleEventType` 仅保留七类 finalized pre-policy lifecycle events；
- retry 使用独立
  `AssignmentOpportunityType.ASSIGNMENT_RETRY_DUE` /
  `AssignmentOpportunityRecord`；
- resolver commit outcome 使用独立三值
  `ResolverDiagnosticType` / `ResolverDiagnosticRecord`；
- resolver diagnostics 固定 `trigger_eligible=false`，不能进入 lifecycle result、
  opportunity list、local-set trigger 或下一 tick trigger；
- local trigger collector 只接收 finalized lifecycle events + assignment opportunities。

---

## PR-03 — Proposal versus forced storage

**RESOLVED**

`ProposalSnapshot` 明确分离：

```text
storage_row_present_mask
policy_proposal_present_mask
forced_nondecision_mask
decision_valid_mask
```

并冻结：

```text
policy_proposal_present_mask == decision_valid_mask
storage_row_present_mask == nonterminal_mask
forced_nondecision_mask ==
  storage_row_present_mask & nonterminal & ~decision_valid_mask
```

- decision-valid row 保存真实 policy action/log-prob；
- nonterminal forced row 只保存 deterministic rollout placeholder，不是 proposal；
- terminal row 没有 storage/policy/forced row；
- resolver 只能消费 `policy_proposal_present_mask=true`；
- rejected policy proposal 仍保留 proposal action，不被 effective assignment 覆盖。

---

## PR-04 — Canonical import and module identity

**RESOLVED**

冻结：

```text
one identity-bearing source file
→ one package-qualified canonical production module key
```

- production 禁止 bare contract import、relative-to-bare fallback 和 `sys.modules` alias；
- pre-AppLauncher profile check 只使用 primitive strings，不创建 enum/dataclass/exception
  identity；
- canonical contract type 只在 package bootstrap 后导入；
- direct/fake test 使用 canonical namespace harness 或 clean child；
- A1a 增加 canonical `__module__`、class `is` identity、AST、duplicate-key 和历史故障
  regression；
- A1b 才关闭 scenario primitive-only / ordered-equality gate；
- formal entrypoint → wrapper same-object/same-class positive wiring gate 留到 A1c。

指令所列 R2F design 路径经仓库核对后实际为：

```text
AgentRead/202607/20260721/
  PHASE9G8I30R2F_INITIAL_CONDITION_RUNTIME_MODULE_IDENTITY_BOUNDARY_REPAIR_DESIGN.md
```

R2F1 implementation report 位于指令所述 `AgentRead/202607/20260722/`。

---

## PR-05 — Discriminated resolved-profile family

**RESOLVED**

```text
ResolvedAssignmentProfile =
  ResolvedExistingAssignmentProfile
  | ResolvedEventGatedAssignmentProfile
```

- existing subtype 独占旧 runtime booleans 和 `to_legacy_wrapper_mapping()`；
- event subtype 只持有 `event_gated_target_semantics`、interface-only readiness 和 v3
  identity；
- event subtype 没有 `event_gate_enabled` 或旧 runtime booleans，也不能进入 current
  boolean/Contract C consumer；
- v3 identity exact keys 明确排除旧 booleans 和 legacy mapping。

---

## PR-06 — Pair-attributed signal assertions

**RESOLVED**

Phase A schema assertions 已补齐：

- 每任务同一 transition 最多一个 completion robot；
- 同一 pair 的 completion 与 terminal failure 互斥；
- completion、forced release 和默认 terminal failure 必须匹配
  `ownership_before_transition`；
- unavailable/recovered 同 robot 同 transition 互斥；
- completed task 的 event-updated ownership 必须为 `-1`；
- task-level completion 由 lifecycle authority 从合法 pair facts 唯一派生；
- future external/system non-owner release 必须增加 typed cause/record，不能放宽 bool
  invariant。

真实 lifecycle derivation 仍属于 B0。

---

## PR-07 — Mutation detector is not semantic identity

**RESOLVED**

V3 只绑定 externally observable：

```text
frozen metadata
+ no public writable alias
+ supported-path mutation detection
```

tensor `_version`、storage identity、private layout 和 detector mechanism 都是可替换实现
细节，不进入 v3 fingerprint 或 checkpoint compatibility；不声称 reflection、`.data` 或
unsupported storage bypass 下的 absolute immutability。

---

## Preserved accepted design and next gate

以下选择保持不变：

- 单一 `assignment_lifecycle_profile` selector，无第二 event flag；
- D0/D1/`SCENARIO_CORRECTION`；
- `updated_failed_pairs` authoritative snapshot；
- overflow fail closed、invalid-path mask、terminal/historical mask separation；
- v3 interface descriptor/checkpoint-ready split；
- metadata-free exact legacy fallback；
- A1a→A1b→A1c、A3→A4→A5；
- 每个 review package 后停止；
- Phase A 只允许 pure/static/manifest evidence。

下一步只能是 GPT/user 对本 targeted revision 进行 review。没有明确
`A1 IMPLEMENTATION AUTHORIZATION` 前，不得开始 A1a。
