# Phase B1W-I1 — Environment Validation and Synchronous Coordinator Implementation Report

## Classification

```text
classification:
  PHASE-B1W-I1-ENVIRONMENT-VALIDATION-AND-SYNCHRONOUS-COORDINATOR-COMPLETE-AWAITING-GPT-REVIEW

B0:                         CLOSED
B1:                         REVIEW PASS
B1W:                        REVIEW PASS
B1W-I-D:                    REVIEW PASS / FROZEN
O1 generic coordinator:     IMPLEMENTED
HARL independence:          VERIFIED
event admission validation: IMPLEMENTED
step-entry exact Ak:        IMPLEMENTED
I3 exact Ak:                IMPLEMENTED
standalone-reset exact Rk:  IMPLEMENTED
internal-autoreset Ak:      IMPLEMENTED
AN1:                        PRESERVED
Ak-bound control mapping:   IMPLEMENTED / PURE VERIFIED
zero-claim continuation:    VERIFIED
deterministic claim -> Ak:  VERIFIED
raw event step/reset:       FAIL-STOP VERIFIED IN PURE/STATIC SCOPE
real Isaac / B1W-I2:        NOT RUN / NOT ENTERED
terminal discovery/ack:     NOT IMPLEMENTED
wrapper integration:        NOT IMPLEMENTED
scheduler/resolver:         NOT ENTERED
runtime readiness:          BLOCKED
training/playback/eval:     NOT RUN
commit:                     NONE
```

This phase implements only the reviewed B1W-I1 production boundary and its pure/static proof. It does not claim real-Isaac runtime evidence or activate the event profile.

## Repository boundary

```text
working directory: E:\Project\IsaacLab_HARL
branch:            main
starting HEAD:     912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:       912b3b59831fcad8dd29ac575b2a1851bf2c21d1
index:             empty before and after
worktree:          pre-existing Phase-A/B0/B1/B1W changes preserved
commit:            none
```

No reset, cleanup, normalization, or commit was performed. The wrapper, Isaac core, frozen contracts, controller, and RL interface stayed byte-identical to preflight.

## Changed and new files

Production/runtime scope:

```text
MOD scan_mobile_manipulator_env.py
MOD assignment_event_profile_runtime_domain.py
MOD assignment_interstep_claim_window_runtime.py
NEW assignment_event_profile_synchronous_runtime.py
```

Pure/static verification scope:

```text
NEW scripts/environments/test_assignment_phase_b1w_i1_environment_coordinator_integration_pure.py
MOD scripts/environments/test_assignment_phase_b1w_interstep_claim_window_fence_pure.py
MOD scripts/environments/test_assignment_phase_b0_3i4_environment_integration.py
MOD scripts/environments/test_assignment_phase_b0_3i3_staged_prereset_facts_adapter_pure.py
MOD scripts/environments/test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
MOD scripts/environments/test_assignment_phase_a_default_off_identity.py
```

The B1W fixture now recognizes the authorized event validation wiring while continuing to reject admission creators in the environment and all wrapper wiring. The I2/I3 capability inventories recognize only the new opaque `domain_identity` property. The Phase-A default-off suite refreshes the derived event-environment source digest after the intentional authorized source change; its behavioral/tensor/manifest oracles are unchanged.

Documentation:

```text
NEW AgentRead/20260822/PHASE_B1W_I1_ENVIRONMENT_VALIDATION_AND_SYNCHRONOUS_COORDINATOR_IMPLEMENTATION_REPORT.md
MOD AgentRead/TASK_PROGRESS.md
```

No TASK_PROGRESS archive was needed: the current handoff was updated in place and remains within the AGENTS.md guideline.

## O1 implementation and capability graph

`EventProfileSynchronousRuntimeCoordinator` is a private, HARL-independent synchronous caller. Its module has `__all__ = ()` and is not exported from any package initializer.

It retains only:

```text
one synchronous environment call reference (reset/step)
current P2 read port
production W2 claim port
physical-step admission port
standalone-reset admission port
optional read-only fence inspection port
optional observational stage callback
```

Construction checks that every port is the exact expected type and carries the same opaque domain identity. A cross-domain mixture rejects before use. O1 does not retain a full runtime domain, StateStore, lifecycle writer, publication lock, raw fence, poison bit, current-assignment cache, terminal consumer, resolver, scheduler, policy, wrapper, or HARL object. It introduces no lock or second state authority.

The optional stage callback is best-effort and observational. Callback failure is swallowed and cannot open/close the fence, alter validation, or prevent a failure report.

## Exact event constructor migration

The exact event profile now requires all three composition-root objects:

```text
resolved_assignment_profile
event_lifecycle_runtime_domain
event_admission_validation_port
```

The validation port must be the exact object issued by that same domain. The existing profile-object, device, env-ID, M, N, and action-noise checks remain. After construction, the environment retains only:

```text
_EventProfileLifecycleEnvironmentPort
_EventProfileEnvironmentAdmissionValidationPort
```

The full domain is used only during construction identity checks and is not retained. The environment receives no claim/admission creator, current read port, Store, fence writer, O1, terminal consumer, or ack capability.

The four existing/default profiles accept neither event capability and continue through their previous branches without B1W validation.

## Environment validation boundary

### Physical entry

The first event task-hook semantic action in `_pre_physics_step()` is now:

```text
_validate_event_physical_step_entry()
  -> validate_physical_step_entry_for_active_call()
```

The validation port resolves the exact active Ak from the fence-owned `ContextVar`, requires `STEP_IN_FLIGHT`, consumes the entry latch once, and then re-applies R3 defensively through the existing terminal-slot authority. Only after success may action copy/clamp or task-space mutation occur.

`DirectMARLEnv.step()` still performs host-level action device conversion before the task hook. AN1 remains enforced: the event constructor rejects every non-`None` action-noise model before base construction. The proven boundary is therefore before event task-state mutation and physics, not before every Python/action operation.

Missing, foreign-context, wrong-type, or duplicate event entry poisons the existing coordinator and rejects. A raw event `env.step()` cannot reopen the same window.

### I3 finalization

Event `_get_dones()` keeps report/dwell staging nonmutating, then executes:

```text
validate_physical_finalization_for_active_call()
environment_port.finalize_physical_transition(report)
```

The exact active Ak must already have consumed its entry latch; the distinct I3 latch is single-use. While a step is in flight, the lifecycle environment port independently requires that consumed latch before beginning the I3 route. Thus production I3 cannot bypass validation. No Ak/window metadata was added to facts or lifecycle results.

### Reset and autoreset

The first event `_reset_idx()` semantic action is `_validate_event_reset_entry()`, before env-ID normalization, native reset, scan-buffer mutation, or I1.

The same no-argument validation capability distinguishes:

```text
RESET_IN_FLIGHT(Rk): exact standalone reset; consume reset-entry latch
STEP_IN_FLIGHT(Ak):  exact same Ak after entry+I3; consume autoreset latch
```

The episode-rebuild port requires the corresponding consumed latch whenever a reset or step admission is active. The pre-existing dormant B0 direct-port fixtures remain legal when no production admission is in flight.

Internal autoreset does not complete Ak and never opens a window. Native reset, I1 publication, and post-reset observation remain inside the outer `STEP_IN_FLIGHT`; O1 opens the next window only after the external `env.step()` returns normally.

A raw event `env.reset()` poisons at the first controllable event hook. `DirectMARLEnv.reset()` may already have performed seed/host-level setup before `_reset_idx()`; no task/native reset mutation after the hook is permitted.

## Fence/runtime-domain extension

The fence adds one boolean single-use latch, `_internal_autoreset_entry_validated`. It remains lock-free and is driven under the existing domain operation lock. The original explicit pure B1W validation APIs remain for frozen regression semantics; the production no-argument APIs add fail-stop projection through the one coordinator poison authority.

Conditional lifecycle-port guards apply only while the fence is `STEP_IN_FLIGHT` or `RESET_IN_FLIGHT`. This seals the admitted production boundary without rewriting dormant B0 transaction semantics.

No new `Lock`, `RLock`, `Condition`, `Semaphore`, health flag, Store, publication pointer, assignment/admission/scheduler tick, or open/close writer was added.

## Reset orchestration

O1 `reset_environment()` implements:

```text
begin exact Rk
-> RESET_IN_FLIGHT
-> call env.reset(...)
-> event reset validation + I1
-> normal external return
-> explicit Rk success completion
-> OPEN Wnext
```

Any exception after admission—including event validation, I1/native reset, observation construction, external return processing, or success-prerequisite failure—is reported through the reset admission port. The existing poison authority enters fail-stop and no window is reopened. There is no `finally: commit_successful_return()`.

The pure bootstrap proof establishes `PREBOOTSTRAP -> R1 -> reset validation -> semantic reset -> return -> W1` with no bypass flag or temporary validation disable.

## Physical-step orchestration and control source

O1 exposes a deterministic B1 claim facade for pure/direct composition but no scheduler API. It also supports a normal zero-claim step.

`step_environment()` performs:

```text
zero-claim continuation marker (or a prior explicit deterministic claim commit)
-> begin Ak; primary R3; close exact Wk
-> read only Ak.admitted_publication
-> derive fixed [E,M] controller assignment
-> build continuous action
-> call env.step(actions)
-> exact event entry validation
-> exact I3 validation/finalization
-> optional same-Ak autoreset
-> normal external return
-> explicit Ak success completion
-> OPEN Wk+1
```

The pure projection helper accepts only an exact `_PhysicalStepAdmission`. It reads only the admitted P2 lifecycle task/robot/ownership tensors, maps active `CLAIMED`, `NAVIGATING`, and `ALIGNING` ownership from `[E,N]` to controller `[E,M]`, and uses `-1` for unassigned robots. It rejects inactive-owned, active-unowned, out-of-range ownership, and more than one active task per robot as fail-stop invariant failures after Ak.

The returned tensor is a detached clone. Mutating caller proposals/effective-assignment caches cannot change it. The existing controller adapter may read fresh geometry after Ak; geometry affects physical action construction but cannot change admitted task IDs.

O1 does not force a claim on every step. Zero-claim continuation admits the exact current P2 unchanged. A deterministic legal B1 claim remains within Wk, publishes P2, and the subsequent Ak captures that post-claim publication. Claims attempted after Ak reject before Store/P2 mutation.

## Failure ordering

```text
pre-admission proposal/claim rejection:
  ordinary existing typed rejection; OPEN may remain

action projection/build failure after Ak:
  report Ak abnormal failure; poison; no reopen

env.step exception after Ak:
  report Ak abnormal failure; poison; no reopen

env.reset exception after Rk:
  report Rk abnormal failure; poison; no reopen

completion without entry/I3 validation:
  completion rejects; O1 reports failure; poison

raw/missing/foreign/duplicate environment validation:
  poison/fail-stop

duplicate already-successful outer completion:
  existing ordinary consumed-admission rejection; no extra window
```

Success completion is in the `else`-equivalent normal-return path, never `finally`.

## Diagnostics

The pure coordinator emits bounded private stages covering S0, S1, S3–S9, and S12–S14. The faithful fake environment supplies S2, S10, and S11 at the actual validation boundaries. Failure markers cover reset admission, action build/step failure, and validation failures are visible through typed exceptions plus actual FAULTED state. Tests determine correctness from domain/fence/P2 state, not logger or stage output.

## Dedicated B1W-I1 results

Runner:

```text
scripts/environments/test_assignment_phase_b1w_i1_environment_coordinator_integration_pure.py
```

Results:

```text
normal:  I1-T1..I1-T28  28/28 passed
-I -B:   I1-T1..I1-T28  28/28 passed
```

Coverage includes same-domain composition, first/later reset, raw reset, exact/duplicate/foreign Ak entry, I3 ordering, same-Ak autoreset, zero claim, deterministic claim, cache/no-alias, geometry separation, post-Ak claim rejection, action/step/reset failures, premature and duplicate completion, static environment ordering, AN1, default isolation, no wrapper wiring, fail-stop classification, semantic neutrality, P2/B1/B1W compatibility, frozen hashes, and global side effects.

Both modes reported Python/Torch RNG, cwd, environment, `sys.path`, root/named logger, filesystem inventory, and assignment-profile registry identity/content unchanged.

## Regression results

```text
B1W normal / -I -B                    26/26 + 26/26
B1 normal / -I -B                     23/23 + 23/23

B0-3I4 terminal handoff               16/16
B0-3I4 environment static             12/12
B0-3I3 staged adapter                  16/16
B0-3I2 runtime domain                  12/12
B0-3I1 episode rebuild                 12/12
B0-2 authority transaction             18/18
B0-1A facts producer                     9/9
B0-1B generation clock                  12/12
B0 subtotal                           107/107

lifecycle transition contract          12/12
assignment profile contract             16/16
event-profile schema                      9/9
Phase-A default-off identity             16/16
profile production wiring                10/10
event-gated MRTA contract                13/13
frozen subtotal                          76/76

all recorded pure/static checks         337/337
```

No real environment reset/step, Isaac, AppLauncher, Omni, PXr, HARL, training, playback, or evaluation was run.

## Hash audit

Unchanged protected files:

```text
7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31  direct_marl_env.py
DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A  assignment_harl_wrapper.py
1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9  assignment_lifecycle_transition_contract.py
22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A  assignment_event_contract.py
ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500  assignment_profile_contract.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
28FAF8D9DB9D323E14020B675D9BBFACD03D9A31D6361414A5A471F6C6803317  assignment_controller.py
3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59  assignment_rl_interface.py
```

Authorized production changes:

```text
scan_mobile_manipulator_env.py
  pre:  030EFB1BE030C6F1BB22BB2DCF5918D0235305CB5D543D01569C1066836501D5
  post: C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99

assignment_event_profile_runtime_domain.py
  pre:  106ED050552BA21717A0EB0D94ADE8CE9E9C008CF6F0731A81E2CE94CEBE98D0
  post: 484808FDA25CBC2DE74249B972005A6F4FF3C10D2C41D67457F5A48E9B565232

assignment_interstep_claim_window_runtime.py
  pre:  3C3BE13E60D71B353677A64E53BFF171D93AD9EB00073E52F576ED46DCF8EAA4
  post: 17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609

assignment_event_profile_synchronous_runtime.py
  new:  EFA334C1745F9BBDA17798A57A5E5EE21418B60FDB54771CFDD52FD71A94A309
```

## Static and scope audits

```text
py_compile changed/new Python: passed
O1 symbol scope:                private coordinator/domain/event env/tests/docs only
wrapper/training/playback O1:   zero hits
HARL/Isaac imports in O1:       zero
package public export:          zero; __all__ empty
environment capabilities:       lifecycle + validation only
O1 authority duplication:       none
new mutex primitives:           none
assignment/admission ticks:     none
11 numeric TBD values:          untouched
variable-cardinality work:      absent
git diff --check:               passed (pre-existing CRLF warnings only)
```

The old B0-3I4 real-smoke source was not modified or rerun. Its historical result is unchanged. Because the exact event constructor now requires a validation port and raw event reset/step is intentionally rejected, that script requires explicit B1W-I2 composition migration before any future execution; this phase makes no runtime claim from it.

## Deferred boundary

```text
B1W-I2 real nonterminal Isaac smoke: not entered
B1W-I3 terminal discovery/capture/ack: not entered
B1W-I4 wrapper facade: not entered
terminal consumer in O1: absent
scheduler/resolver/policy: absent
runtime-ready activation: blocked
training/playback/evaluation: not run
11 numeric TBDs: unresolved
variable cardinality / Transformer / GNN: not entered
```

No implementation STOP condition was reached: no wrapper, Isaac core, full-domain capability, I3 bypass, bootstrap bypass, ambiguous control source, second authority, action-noise expansion, scheduler, or terminal dependency was required.

## Phase boundary

Phase B1W-I1 is complete in the authorized pure/static scope. Stop here and await GPT/user review. Do not enter B1W-I2, B1W-I3, B1W-I4, scheduler/resolver, readiness, Isaac runtime, training, playback, or evaluation without a new explicit authorization.
