# Phase 10A — Authoritative V2.1 Targeted Revision Summary

```text
classification:
  TARGETED-REVISION-COMPLETE-AWAITING-USER-APPROVAL

document_status:
  AUTHORITATIVE-DESIGN-CANDIDATE-V2.1

verified_against_head:
  e3febe417c5323e28ceb9e256ba71dcd44f3c457

implementation_authorization:
  none -- awaiting explicit user approval

enter Phase A:
  no -- wait for explicit user approval
```

---

## 1. Revision reason and scope

Targeted GPT review accepted the V2 method route and found only three residual
documentation-contract issues:

1. raw execution facts and lifecycle-derived results were mixed in one pre-reset DTO；
2. default-off was described too narrowly as always dispatching to legacy；
3. resolver-commit ownership changes could be misread as a new assignment trigger。

This revision closes only TR-01～TR-03. It does not reopen or redesign nominal cost、
Top-K、action/DVM、fallback、pair/component objective、transfer counting、reward、
HAPPO、checkpoint version route、baseline fairness or Phase A–E sequencing.

---

## 2. Files and supersede chain

Current candidate:

- [Authoritative V2.1](Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_1_20260727.md)

Preserved inputs:

- [Authoritative V2](Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Authoritative_V2_20260727.md)
- [20260724 backup](../20260724/Lifecycle_Aware_Event_Gated_Local_MRTA_Design_Backup_20260724.md)
- [V2 revision summary](PHASE10A_AUTHORITATIVE_V2_REVISION_SUMMARY.md)
- [Phase 10A interface audit](../20260724/PHASE10A_EVENT_GATED_LOCAL_MRTA_HAPPO_INTERFACE_AUDIT.md)

```text
20260724 backup:
  historical discussion snapshot

V2:
  superseded design candidate

V2.1:
  current authoritative design candidate
```

The backup and V2 were not modified. Their preserved SHA256 values are:

```text
20260724 backup:
  A9DD70253EC78575C14394B4F566505A5C85F0BFD0440D76E2F44403E55A42FC

Authoritative V2:
  39F6C9F4857135E790DC897A2820FD83AA03CBA1CEAF93FC6824F7326899D517
```

---

## 3. TR-01 — Two-layer transition authority

**Resolution:** `RESOLVED`

V2.1 replaces the mixed DTO with two immutable, generation-bound objects.

### `ExecutionTransitionFacts`

The environment captures raw facts before any `_reset_idx()`:

- physical termination/truncation/time-limit facts；
- raw completion、terminal pair failure and forced-release signals；
- raw robot unavailable/recovered signals；
- pre-reset coverage and pre-lifecycle state/ownership snapshots；
- consume-once token。

It explicitly excludes final `termination_reason`、`TEAM_INFEASIBLE`、derived release
results and lifecycle-updated state/ownership.

### `LifecycleTransitionResult`

The unique lifecycle authority consumes the raw facts and derives:

- completed/released tasks；
- new failed pairs and new `TEAM_INFEASIBLE` tasks；
- updated task/robot state and event-updated ownership baseline；
- final termination reason；
- lifecycle events used by the local MRTA seed collector。

The result binds the source generation/token and is immutable after finalization.
Resolver commit output cannot retroactively modify it.

The canonical order now explicitly separates environment capture、lifecycle
derivation、terminal branching and non-terminal policy/resolver work.

---

## 4. TR-02 — Profile-aware default-off dispatcher

**Resolution:** `RESOLVED`

V2.1 freezes:

```text
event-gated feature off
→ direct dispatch to the existing pre-event-gated implementation
  selected by the resolved current profile
```

The dispatcher preserves each supported profile:

```text
legacy:
  existing legacy path

lifecycle_contract_c:
  existing Contract C path

another already-versioned pre-event-gated profile:
  existing profile-specific supported/blocked path

event_gated_local_mrta:
  new Phase A–D path
```

Event-gated off does not disable Contract C resolver semantics or alter a resolved
profile's observation、mask、reward、RNG、checkpoint or playback identity. A new
event-gated trainer with DVM forced to all ones is forbidden as a compatibility
substitute.

---

## 5. TR-03 — Resolver-commit trigger suppression

**Resolution:** `RESOLVED`

V2.1 defines:

```text
event_source:
  EXECUTION
  LIFECYCLE_AUTHORITY
  RETRY_SCHEDULER
  RESOLVER_COMMIT_DIAGNOSTIC
```

`RESOLVER_COMMIT_DIAGNOSTIC` records the current assignment tick outcome but is not
inserted into the assignment-triggering event set:

```text
resolver commit
→ update effective assignment/ownership
→ next physical execution step

resolver commit alone
≠ new assignment-triggering lifecycle event
```

A later assignment opportunity still occurs when a robot remains
`NEEDS_ASSIGNMENT`、a new execution/lifecycle event arrives、retry cadence expires、
external feasibility/availability changes or the commit explicitly leaves pending
assignment work.

---

## 6. Residual finding resolution matrix

| Residual finding | Severity | V2.1 section | Resolution |
|---|---|---|---|
| TR-01 Raw facts 与 derived lifecycle results 混合 | HIGH | Raw execution facts / lifecycle result；strict order | RESOLVED |
| TR-02 Default-off “legacy”表述过窄 | MEDIUM | Default-off direct bypass | RESOLVED |
| TR-03 Resolver commit ownership change 自触发风险 | LOW | Ownership-change event provenance | RESOLVED |

```text
targeted residual findings:
  RESOLVED: 3
  unresolved HIGH/MEDIUM/LOW: 0
```

---

## 7. Inherited findings and method status

The original V2 DR-01～DR-21 matrix is retained unchanged:

```text
original DR findings:
  21/21 remain RESOLVED

unresolved CRITICAL/HIGH documentation findings:
  0
```

`RESOLVED` remains a documentation status. It does not mean code implementation、
numeric selection、runtime validation or user approval.

No additional broad review is required for these three corrections. Explicit user
approval is still required before Phase A.

---

## 8. Phase ownership after V2.1

Phase A defines and versions:

- `ExecutionTransitionFacts`；
- `LifecycleTransitionResult`；
- generation、consume-once and authority contracts；
- event-source provenance and resolved-profile dispatcher。

Phase B0 implements the environment raw-facts hook and lifecycle authority/result
pipeline. Phase B filters resolver-commit diagnostics out of assignment triggers and
implements the local MRTA/resolver path. Phase C/D/E responsibilities remain unchanged.

```text
overall Phase 10A classification:
  RUNNER-CHANGES-REQUIRED

architecture route:
  Phase A → Phase B0 → Phase B → Phase C → Phase D → Phase E
```

---

## 9. Approval and execution boundary

```text
enter Phase A:
  no -- wait for explicit user approval

runtime behavior changed:
  no

training/playback/evaluation:
  not run

Isaac Sim/AppLauncher:
  not run

checkpoint load/modify:
  none

source/test/YAML modified:
  no

installed HARL modified:
  no

staged/commit:
  none
```

The only authorized next action is user review/approval of the V2.1 candidate.
