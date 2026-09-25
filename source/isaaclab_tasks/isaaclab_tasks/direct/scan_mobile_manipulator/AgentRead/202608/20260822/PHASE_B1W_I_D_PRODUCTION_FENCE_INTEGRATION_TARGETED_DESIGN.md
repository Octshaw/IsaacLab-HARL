# Phase B1W-I-D — Production Fence Integration and Synchronous Runtime Wiring Targeted Design

## 0. Classification and authorization boundary

**Classification:**

`PHASE-B1W-I-D-PRODUCTION-FENCE-INTEGRATION-DESIGN-COMPLETE-AWAITING-GPT-REVIEW`

This phase is a targeted, documentation-only integration design. It does not implement production wiring, change Python/configuration, run Python tests, start Isaac/AppLauncher, run training/playback/evaluation, change runtime-readiness, or commit. The design preserves the accepted B0 lifecycle authority, B1 initial-claim transaction, and B1W inter-step fence semantics.

Following the local `AGENTS.md` daily-folder rule, this newly created report is stored under `AgentRead/202608/20260822/`, matching the current local date.

## 1. Read-only recovery and evidence basis

After the machine restart, the repository was recovered at:

- worktree: `E:\Project\IsaacLab_HARL`
- branch: `main`
- HEAD: `912b3b59831fcad8dd29ac575b2a1851bf2c21d1`
- index: empty
- pre-existing modified/untracked worktree content: retained; not cleaned or overwritten
- target report before this phase: absent

The phase instruction, local `AGENTS.md`, `TASK_PROGRESS.md`, and all eight mandatory B1W/B1/B0 design, implementation, runtime-smoke, and closeout reports were read in full before this design was frozen.

Read-only source anchors used for the integration mapping:

| Source | Relevant current boundary |
|---|---|
| `source/isaaclab/isaaclab/envs/direct_marl_env.py` | `reset()` calls task `_reset_idx()`; `step()` performs action conversion/noise, `_pre_physics_step()`, physics, `_get_dones()`, autoreset, observations, then returns |
| `scan_mobile_manipulator_env.py` | event constructor validates domain identity; `_pre_physics_step()` contains the current defensive R3 check; event `_get_dones()` stages and finalizes I3; event `_reset_idx()` runs I1 inside `episode_rebuild` |
| `assignment_harl_wrapper.py` | current `reset()` directly calls raw `env.reset()`; current `step()` proposes/resolves, builds continuous action, then directly calls raw `env.step()` |
| `assignment_rl_interface.py` and `assignment_controller.py` | current continuous action conversion consumes an assignment tensor but reads fresh physical problem geometry from the environment |
| `assignment_event_profile_runtime_domain.py` | owns the one fence/coordinator/store/operation lock and exposes narrow lifecycle, read, claim, admission, validation, and terminal-consumer ports |
| `assignment_interstep_claim_window_runtime.py` | owns PREBOOTSTRAP/OPEN/RESET_IN_FLIGHT/STEP_IN_FLIGHT state and current-call admission identity/latches |
| B0-3I4 runtime smoke | current diagnostic composition constructs profile/domain/environment, but still invokes raw `reset()` and `step()` |
| current playback/training composition | rejects the event profile through runtime-readiness gates and does not construct the event runtime domain |

Pre-design SHA-256 evidence:

| File | SHA-256 |
|---|---|
| `direct_marl_env.py` | `7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31` |
| `scan_mobile_manipulator_env.py` | `030EFB1BE030C6F1BB22BB2DCF5918D0235305CB5D543D01569C1066836501D5` |
| `assignment_harl_wrapper.py` | `DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A` |
| `assignment_event_profile_runtime_domain.py` | `106ED050552BA21717A0EB0D94ADE8CE9E9C008CF6F0731A81E2CE94CEBE98D0` |
| `assignment_interstep_claim_window_runtime.py` | `3C3BE13E60D71B353677A64E53BFF171D93AD9EB00073E52F576ED46DCF8EAA4` |
| `assignment_initial_claim_transaction.py` | `C74868C84A803108C424827AFE9326393428938DCE4F6CBD46693DA3D4D94FDA` |
| `assignment_lifecycle_transaction.py` | `28D61BAEA7760F091EE47AC1C3E818DDC7D911EC7BEB587C22023D27DE5593A7` |

These hashes describe the audited source basis, not a claim that the dirty worktree is generally clean.

## 2. Current exact call graph

### 2.1 Current wrapper step route

```text
AssignmentHARLWrapper.step(actions)
  -> env.get_assignment_problem()
  -> decode policy proposal
  -> legacy resolver.resolve_pre_step(...)
  -> effective_assignment (wrapper/resolver-side value)
  -> assignment_to_env_actions(effective_assignment)
       -> AssignmentRLInterface
       -> viewpoint_assignment_to_actions(...)
       -> env.get_assignment_problem() for fresh geometry
  -> raw env.step(continuous_actions)
       -> DirectMARLEnv.step
            -> actions.to(device)
            -> action noise, if configured
            -> task _pre_physics_step()
                 -> current event defensive R3 assertion
                 -> action copy/clamp and task-state integration
            -> physics loop
            -> episode counters
            -> task _get_dones()
                 -> stage event facts/report
                 -> environment lifecycle port.finalize_physical_transition(report) [I3]
            -> task _get_rewards()
            -> task _reset_idx(done envs) [internal autoreset]
                 -> environment lifecycle port.episode_rebuild(...)
                 -> native reset mutation
                 -> I1 commit
            -> observations
            -> five-tuple return
  -> legacy resolver post-step and wrapper diagnostics
```

This route has no primary B1W step admission. The `_pre_physics_step()` R3 check can only reject; it cannot safely manufacture `Ak`. The action source is also not yet proven to be the ownership captured by `Ak`.

### 2.2 Current reset and construction routes

```text
make_assignment_harl_env(...)
  -> require_assignment_profile_runtime_ready(...)
  -> gym.make(...)
  -> AssignmentHARLWrapper(...)

AssignmentHARLWrapper.reset()
  -> raw env.reset()
       -> DirectMARLEnv.reset()
       -> task _reset_idx(all envs)
```

The current production helper rejects the event profile before construction and does not create the event runtime domain. The B0-3I4 diagnostic script creates the exact domain before the environment, but it also calls raw `reset()`/`step()` and predates B1W production admission.

`DirectMARLEnv.__init__()` calls `sim.reset()` but does not call task `_reset_idx()`. Therefore no constructor-triggered lifecycle reset exists in the audited route: the first explicit reset can be placed behind reset admission without a bootstrap exception.

## 3. Frozen target production call graph

### 3.1 Chosen O1 owner

Choose **O1-B**: a new B-private, HARL-independent `EventProfileSynchronousRuntimeCoordinator` is the behavioral owner of synchronous orchestration. **O1-C is used only as construction placement**: the event-profile composition root creates and connects this object. The wrapper is a client of a narrower facade and is not O1.

The coordinator orders existing authority operations; it does not decide lifecycle semantics, completion/failure facts, TEAM, termination reason, policy, proposal, or resolver outcome. It is not a second StateStore/fence/lifecycle authority.

### 3.2 Target construction route

```text
event-profile composition root
  -> resolve the exact event profile
  -> build environment cfg
  -> construct exactly one AssignmentEventProfileRuntimeDomain
  -> obtain its narrow environment validation port
  -> gym.make(cfg, same profile, same domain, validation_port)
  -> environment retains only lifecycle-environment + admission-validation ports
  -> construct one EventProfileSynchronousRuntimeCoordinator
       with env + current-read + production-claim + step-admission
       + reset-admission + terminal-consumer ports
  -> optionally construct wrapper with only a narrow orchestration facade
  -> coordinator.reset_environment() for the first explicit reset
```

The existing domain argument may remain transiently available to the environment constructor for exact retained-domain/profile/device/cardinality validation during migration. After construction, the environment must retain only the two frozen narrow ports, not the domain object.

### 3.3 Target reset route

```text
PREBOOTSTRAP
  -> synchronous coordinator.begin_reset_admission()
       PREBOOTSTRAP -> RESET_IN_FLIGHT R1
  -> env.reset()
       -> DirectMARLEnv.reset()
       -> task _reset_idx(all envs), first statement validates active R1
       -> native reset + I1 episode rebuild
       -> return
  -> synchronous coordinator.complete_reset_success(R1)
       RESET_IN_FLIGHT -> OPEN W1
```

Any exception after R1 begins is explicitly reported as reset failure and poisons/fail-stops the domain. There is no `finally` reopen. Existing/default profiles stay on their unchanged legacy route; admission is exact-event-profile and default-off.

### 3.4 Target physical-step route

```text
previous reset/step has fully returned
  -> fence OPEN Wk
  -> coordinator handles any pending terminal artifact first (TA1)
  -> coordinator reads current P2
  -> proposal/resolver phase, if an assignment opportunity exists
  -> zero or more legal B1 production claim commits under Wk
  -> final P2 ownership publication established
  -> coordinator.begin_step_admission()
       primary R3
       OPEN Wk -> STEP_IN_FLIGHT Ak
       Ak captures final P2 identity + Store version
  -> coordinator reconstructs immutable [E,M] control assignment from Ak.P2 ownership
  -> existing assignment_to_env_actions(Ak-derived assignment)
       fresh physical geometry read is permitted; assignment truth is not
  -> env.step(continuous_actions)
       -> task first hook validates the exact active Ak, then mutates task action state
       -> physics
       -> staged facts/report
       -> I3 consumes exact-Ak finalization latch
       -> lifecycle transition and optional terminal slot publication
       -> reward/bookkeeping
       -> internal autoreset validates exact active Ak/autoreset context
       -> observations and external return
  -> coordinator.complete_step_success(Ak), only after normal env.step return
       STEP_IN_FLIGHT -> OPEN Wk+1
  -> caller consumes returned outputs
```

The only exact caller boundary for primary `begin_step_admission()` is the coordinator immediately after claim/terminal handling and immediately before continuous action construction. It must not be moved into `_pre_physics_step()`.

## 4. Exact capability ownership graph

| Component | May retain | Must not retain or decide |
|---|---|---|
| `AssignmentEventProfileRuntimeDomain` | exactly one fence, lifecycle coordinator, StateStore, operation lock; creation of all narrow ports; poison/fail-stop machinery | policy, proposal, resolver decision, physical actions |
| synchronous runtime coordinator | environment call capability; current-P2 read; production claim; reset admission; step admission; designated terminal consumer; explicit failure reporting | full domain, raw store, raw fence, lifecycle writer, poison writer, policy/resolver authority |
| environment | lifecycle environment port; admission validation port | step/reset admission creation, production claim, terminal consumer, current store, full domain/fence/coordinator |
| wrapper adapter | narrow orchestration facade; policy/proposal/resolver responsibilities already belonging to the wrapper layer | raw admissions, validation port, store/fence/domain, lifecycle writer, direct event-profile raw `env.step/reset` |
| controller/action builder | Ak-derived ownership tensor plus read-only current physical geometry | mutable wrapper assignment cache as authority; claim/admission/lifecycle capabilities |
| terminal consumer | capture pending exact artifact/key and acknowledge that exact key | lifecycle publication, window open, P2 mutation, arbitrary store access |
| I1 environment rebuild | lifecycle environment transaction within already validated reset/autoreset call | reset admission, step admission, opening W, terminal ack |
| I3 environment finalization | lifecycle environment finalization after exact-Ak latch validation | creating or completing Ak, opening W, terminal consumption |

No bundled “runtime domain port” is approved. Lifecycle mutation and admission validation remain separate environment capabilities so that one leaked object cannot silently widen authority. The wrapper likewise receives a facade with business-level `reset_environment`, `step_environment`, claim/proposal coordination, and terminal handling—not the underlying ports.

## 5. Admission validation hooks

### 5.1 Environment physical entry

The future event path makes the first task hook statement a no-argument admission validation call such as:

```text
admission_validation_port.validate_physical_step_entry_for_active_call()
```

The port resolves the active call from the fence-owned per-instance `ContextVar`, requires the same exact active `Ak`, consumes a single-use step-entry latch, and performs defensive R3. It returns no mutable authority. Missing, foreign, duplicate, inactive, or wrong-type admission poisons/fail-stops before task-state mutation or physics.

`DirectMARLEnv.step()` already converts the action tensor to the device before `_pre_physics_step()`. Consequently the guarantee is “before task mutation and physics,” not literally “before every host operation.” This is acceptable only with the frozen event action-noise policy below.

### 5.2 I3 finalization

Immediately before the environment lifecycle port is allowed to finalize the staged report, the event route calls:

```text
admission_validation_port.validate_physical_finalization_for_active_call()
```

It resolves the same active `Ak`, requires that its entry latch was consumed, consumes a distinct single-use finalization latch, and binds the subsequent I3 call to that call context. The lifecycle environment port must also require this consumed latch, preventing a direct bypass. Facts/report DTOs do not carry or synthesize `Ak`; thread identity is not guessed from lifecycle facts.

### 5.3 Standalone reset and internal autoreset

The first statement of event `_reset_idx()`—before ID normalization, buffer reset, scene mutation, or I1—is:

```text
admission_validation_port.validate_reset_entry_for_active_call()
```

The validation port discriminates two legal callers:

- `RESET_IN_FLIGHT` with the exact active reset admission: consume the standalone-reset entry latch.
- `STEP_IN_FLIGHT` with the exact active `Ak`, after both its step-entry and finalization latches: consume a dedicated single-use internal-autoreset entry latch.

`OPEN`, `PREBOOTSTRAP`, absent context, wrong admission type, foreign call, or duplicate entry is poison/fail-stop. I1 remains incapable of opening a claim window. The outer coordinator alone completes R1/Ak after the outer `env.reset()`/`env.step()` has returned normally.

## 6. Ak-bound continuous control contract

The current controller accepts `[E,M]` ownership but obtains fresh task geometry from `env.get_assignment_problem()`. That split remains usable under this contract:

1. `Ak` is created only after the final production claim commit and captures the authoritative P2/store version.
2. The coordinator obtains ownership only from `Ak.admitted_publication`; it must not read a later wrapper cache or treat a proposal as effective assignment.
3. It validates the fixed-cardinality invariant and deterministically inverts P2 robot ownership into the controller’s `[E,M]` assignment tensor (at most one task per robot, with the existing unassigned sentinel/representation).
4. It may then call the existing `assignment_to_env_actions()` conversion. Fresh geometry/coverage/feasibility reads are physical inputs only; they cannot replace or modify Ak-bound ownership.
5. An action-building exception occurs after the window has closed, so the coordinator reports Ak failure and the domain poisons/fail-stops. It never reopens Wk.

For the first deterministic smoke, use legal fixed C2 task IDs and the existing controller with the Ak-derived ownership. No scheduler, policy-quality claim, or new assignment semantics is introduced. A genuinely empty legal ownership publication may yield the existing neutral/no-task physical behavior; “neutral” must still be derived from that admitted ownership, never used to bypass it.

### Action-noise verdict

Choose **AN1**: the exact event route continues to require `action_noise_model is None`. Noise would transform control after Ak-bound construction and before the environment validation hook, broadening the first integration proof. Any future event-profile action noise requires a separate semantic review. Existing/default profiles are unchanged.

## 7. Terminal transition, autoreset, capture, and ack

Choose deterministic **TA1 terminal-first inter-step ordering**:

```text
terminal Ak finalization publishes exact terminal artifact/key
  -> internal autoreset executes while the same Ak remains STEP_IN_FLIGHT
  -> env.step returns
  -> coordinator completes Ak successfully
  -> Wnext becomes OPEN while the terminal slot remains occupied
  -> before any next proposal/claim/admission:
       designated consumer captures the exact stored artifact/key
       delivers/copies it to its bounded downstream holder
       acknowledges that exact key
  -> read current post-reset P2
  -> proposal/claim for the new episode
  -> next begin_step_admission()
```

Ack is intentionally not required before successful completion of the terminal Ak. The accepted G2/R3 semantics allow `OPEN + occupied terminal slot`: G2 blocks claims and R3 blocks the next step until exact ack. Ack neither opens a window nor creates P2.

The current terminal-consumer port can read/ack only when given an exact key, while the environment’s exact terminal-key tuple is not exposed in the external `env.step()` return. Therefore a later terminal integration slice must add the smallest designated-consumer discovery/capture capability, for example `capture_pending_terminal_artifacts()`, under the existing publication lock. It returns exact immutable stored keys/artifacts; it must not reconstruct a key or artifact from post-autoreset P2. This is a narrow integration dependency, not authorization for a critic sidecar, learner transport, or full HARL terminal pipeline.

If capture/delivery/ack fails, the slot remains occupied. The next claim fails G2 and the next admission fails R3; there is no implicit ack or reopen. This fail-closed state is observable and recoverable only through the exact designated-consumer protocol.

## 8. Long-task and proposal/effective-assignment semantics

- A step window permits zero or more B1 commits; it does not require a claim every physical step.
- With zero commits, the final current P2 is admitted into Ak unchanged. This is the normal long-task continuation path.
- A proposal remains merely a proposal. Only a successful production claim commit changes authoritative P2.
- The controller consumes admitted effective ownership, not the proposal and not a wrapper-local mutable “effective assignment.”
- After a terminal autoreset, the next episode’s current P2 must be read only after terminal capture/ack. A new-episode assignment may be zero, unchanged, or updated only through legal B1 claims.
- Fixed `E/M/N` cardinality and existing tensor schemas remain frozen. Numeric thresholds remain unresolved TBDs.

The fence therefore remains an inter-step mutation boundary; it must not degenerate into a “reassign on every step” scheduler.

## 9. Failure and poison matrix

| Condition | Classification | Frozen behavior |
|---|---|---|
| missing Ak at event step entry | poison/fail-stop | reject before task mutation/physics; report domain corruption |
| foreign Ak/context at step entry | poison/fail-stop | reject; never substitute the current admission |
| duplicate Ak entry validation | poison/fail-stop | single-use latch detects duplicate |
| missing reset admission | poison/fail-stop | reject at first event `_reset_idx()` statement |
| wrong reset admission type | poison/fail-stop | reject unless exact R1 or validated internal-autoreset Ak case |
| duplicate reset/autoreset entry | poison/fail-stop | reject through single-use latch |
| I3 finalization with missing/foreign/wrong Ak | poison/fail-stop | no lifecycle finalization is permitted |
| Ak completion before I3 finalization | poison/fail-stop | completion rejects; O1 explicitly reports Ak failure |
| action construction exception after begin Ak | poison/fail-stop | report Ak failure; never reopen Wk |
| `env.step()` exception after begin Ak | poison/fail-stop | explicit Ak failure report; never success-complete in `finally` |
| `env.reset()` exception after begin R1 | poison/fail-stop | explicit R1 failure report; never open W1 in `finally` |
| raw event `env.step()` while OPEN/PREBOOTSTRAP | poison/fail-stop | reaches event first hook without active Ak and is rejected before task mutation/physics |
| raw event `env.reset()` | poison/fail-stop | reaches first event `_reset_idx()` statement without legal R1/Ak and is rejected before native/task reset mutation |
| R3 rejection at begin step | ordinary typed reject | no Ak is created and no state is changed; caller must handle/ack pending terminal |
| G2 rejection of a claim | ordinary typed reject | no claim mutation; terminal slot remains pending |
| stale W2 claim | ordinary typed reject | preserve existing B1/B1W typed-rejection semantics |
| proposal/resolver exception before admission | ordinary caller failure | W remains OPEN if no shared state was corrupted |
| legal B1 prepare/commit rejection before admission | ordinary typed reject | W remains OPEN and current P2 is unchanged |
| duplicate outer completion after already successful completion | ordinary typed reject | preserve accepted pure consumed-admission behavior; no new poisoning rule |
| B1 impossible post-swap failure | existing poison/fail-stop | preserve accepted B1 poison path |

The distinction is temporal: ordinary pre-admission business rejection does not poison the fence; a contradiction or execution failure after an admission has closed the window cannot be rolled back and therefore poisons/fail-stops.

## 10. Future auditable diagnostic sequence

The first implementation must emit bounded, flushed stage markers at these semantic points (names may be encoded constants, but ordering may not change):

| Stage | Evidence |
|---|---|
| S0 | exact event domain constructed |
| S1 | reset admission begun |
| S2 | environment reset entry validated |
| S3 | external reset returned |
| S4 | R1 completed and W1 OPEN |
| S5 | deterministic claim prepared/committed, or explicit zero-claim continuation |
| S6 | authoritative P2 publication observed |
| S7 | step admission begin requested |
| S8 | exact Ak active and W closed |
| S9 | continuous action built from Ak-bound ownership |
| S10 | environment exact-Ak entry validated |
| S11 | I3 exact-Ak finalization validated |
| S12 | external `env.step()` returned |
| S13 | exact Ak success-completed |
| S14 | W2 OPEN |

The mandatory later terminal smoke adds:

| Stage | Evidence |
|---|---|
| T0 | terminal step admitted |
| T1 | terminal lifecycle publication occurred |
| T2 | exact terminal slot installed |
| T3 | autoreset occurred while the same Ak remained STEP_IN_FLIGHT |
| T4 | external step returned |
| T5 | Ak completed and Wnext OPEN |
| T6 | exact stored terminal artifact/key captured |
| T7 | exact-key ack succeeded |
| T8 | post-ack step retry reaches and passes the R3 check |
| T9 | the next step is admitted |

To prove the blocking half of R3 as well as the required T0–T9 success sequence, the terminal smoke adds one separately labelled bounded negative admission attempt between T5 and T6. That attempt must reject without changing the OPEN window; T6/T7 then capture and ack, T8 retries, and T9 records successful admission. Normal production orchestration proactively handles the slot and does not use rejection as control flow.

Future real-Isaac smokes must be focused, bounded, staged, and use flushed output. No training, playback, evaluation, learned scheduler, or long opaque run belongs to the first wiring proof.

## 11. Implementation strategy comparison and frozen slicing

| Strategy | Assessment |
|---|---|
| A: direct generic runtime first, wrapper later | selected; isolates lifecycle/admission correctness from HARL and provides a reusable bounded smoke caller |
| B: environment validation and wrapper/HARL together | rejected; couples authority wiring, control adaptation, wrapper readiness, and learner transport in one failure surface |
| C: environment validation alone, coordinator later | semantically possible but leaves event environment intentionally unusable except through a special harness; combine validation and generic coordinator in one atomic code slice |

Recommended minimum slices:

1. **B1W-I1 — Environment validation + generic coordinator atomic wiring.** Add the narrow current-call step/finalization/reset/autoreset validation protocol; add the B-private synchronous coordinator and deterministic pure/static harness. Preserve default-off routing and do not touch wrapper/HARL readiness.
2. **B1W-I2 — Focused real-Isaac nonterminal direct smoke.** Compose one real event environment, admitted initial reset, legal deterministic C2 claim (or separately asserted zero-claim continuation), Ak-bound existing action conversion, one nonterminal admitted step, I3 validation, external return, Ak completion, and W2. Use staged/flushed bounded execution.
3. **B1W-I3 — Exact terminal consumer discovery and real terminal smoke.** Add only the minimal pending-key/artifact capture surface; prove terminal publication, slot, same-Ak autoreset, return/completion, capture, deliberate R3/G2 protection, exact ack, and next admission.
4. **B1W-I4 — Wrapper facade integration.** Route the event-profile wrapper through the coordinator facade and Ak-bound action source. Do not add scheduler/policy/HARL learner transport; keep runtime-ready false until all mandatory runtime gates and a separate readiness review pass.

This is intentionally four reviewable slices rather than one wrapper-first patch. The first production success target is the direct nonterminal event route; the terminal path remains a mandatory gate before runtime readiness.

## 12. Explicit answers to the 15 required questions

1. **Who holds O1?** The new B-private, HARL-independent `EventProfileSynchronousRuntimeCoordinator`; the composition root constructs it, and the wrapper only calls its narrow facade.
2. **Where are domain/env/wrapper constructed and connected?** In the event-profile composition root: exactly one domain first, then env with the same profile/domain plus validation port, then O1 from env and narrow domain ports, then optional wrapper from the O1 facade.
3. **How does first reset open W1 from PREBOOTSTRAP?** O1 begins exact R1, calls `env.reset()`, environment validates R1 before `_reset_idx()` mutation/I1, and O1 success-completes R1 only after external return, producing OPEN W1.
4. **How is raw reset stopped?** The first event `_reset_idx()` statement requires the exact active R1 or the exact validated internal-autoreset Ak. Missing/wrong/foreign/duplicate context poisons and rejects before native reset mutation.
5. **What exact boundary begins step admission?** O1, after terminal handling and all claims establish final P2, immediately before Ak-bound continuous action construction and the sole event `env.step()` call.
6. **Where is continuous action generated?** Inside O1 after `Ak` exists, by invoking the existing `assignment_to_env_actions()` controller adapter with an assignment reconstructed from Ak-bound ownership.
7. **How is Ak-bound ownership guaranteed?** The assignment tensor is derived only from `Ak.admitted_publication` P2; fresh environment reads may supply geometry but never assignment authority; wrapper proposal/cache is not accepted as control truth.
8. **How does the first environment hook verify the same Ak?** Its first statement calls the narrow validation port, which resolves the active per-fence call context, checks exact object/identity/type/state, and consumes Ak’s entry latch.
9. **How does I3 verify the same Ak?** A second validation immediately before lifecycle finalization requires the same active Ak and consumed entry latch, consumes Ak’s finalization latch, and the lifecycle port refuses finalization without it.
10. **Why can autoreset not open early?** Autoreset runs inside `DirectMARLEnv.step()` while Ak remains STEP_IN_FLIGHT; it only validates a dedicated autoreset latch and executes I1. I1 has no window-open capability; O1 completes Ak only after the outer step returns.
11. **Who completes Ak after return?** The same synchronous coordinator that began it, and only on a normal `env.step()` return after validated I3; all post-admission exceptions take explicit failure/poison paths.
12. **When are terminal artifacts captured/acked?** Under TA1, after terminal Ak external return and success completion opens Wnext, but before reading new-episode P2, proposal, claim, or next admission. A diagnostic subcase may attempt one pre-ack step to prove R3.
13. **How do slot, G2, R3, and OPEN coexist?** `OPEN + occupied slot` is legal. G2 blocks claim mutation, R3 blocks physical admission, and exact ack clears only the slot; ack neither opens the fence nor changes P2.
14. **What are raw/bad call failure rules?** Missing/foreign/duplicate admissions, wrong hook/finalization/reset context, raw event step/reset, and any post-admission execution failure poison/fail-stop. Pre-admission proposal/claim/G2/R3/stale-window rejections retain their accepted ordinary typed behavior unless shared state is corrupted.
15. **What are the minimum next slices?** B1W-I1 validation plus generic coordinator; B1W-I2 bounded real nonterminal direct smoke; B1W-I3 minimal exact-terminal capture plus real terminal/autoreset/ack smoke; B1W-I4 wrapper facade integration. Training/readiness remains later.

## 13. Final verdict table

| Decision | Frozen verdict |
|---|---|
| synchronous coordinator owner | O1-B, new B-private HARL-independent coordinator |
| composition-root construction | event-profile root creates one domain -> env -> O1 -> optional wrapper |
| environment future capabilities | lifecycle environment port + admission validation port only |
| wrapper future capabilities | narrow O1 orchestration facade only for event path |
| initial reset bootstrap route | R1 begin -> env reset entry validation -> I1/native reset -> external return -> R1 success -> W1 |
| standalone reset validation hook | first event `_reset_idx()` statement |
| physical step admission site | O1 immediately before action build/env.step |
| continuous action build site | O1 after Ak, via existing controller with Ak-derived `[E,M]` ownership |
| Ak environment entry validation | first event `_pre_physics_step()` statement, exact active-call latch |
| Ak I3 finalization validation | immediately before lifecycle `finalize_physical_transition`, distinct exact-Ak latch |
| Ak outer success completion | O1 immediately after normal external `env.step()` return |
| terminal capture/ack order | TA1: complete terminal Ak/open Wnext -> capture exact stored artifact/key -> exact ack -> new P2/proposal/claim/admission |
| G2/R3 | preserved; protect occupied terminal slot even while fence is OPEN |
| raw event `env.step()` | reject and poison before task mutation/physics |
| raw event `env.reset()` | reject and poison before event/native reset mutation |
| event action noise | AN1: must remain `None` pending separate review |
| implementation slicing | I1 generic atomic wiring; I2 nonterminal Isaac; I3 terminal Isaac; I4 wrapper facade |
| scheduler/policy dependency | none for the first integration; deterministic legal claim only |
| Isaac core patch | prohibited and unnecessary |
| B1/B1W semantics | preserved; narrow integration extensions only |
| event runtime readiness | remains false/default-off pending later runtime gates and review |

## 14. Readiness checklist

- [x] B1 pure/default-off initial-claim implementation accepted
- [x] B1W pure/default-off inter-step fence implementation accepted
- [ ] B1W-I1 environment validation and generic synchronous coordinator implemented/reviewed
- [ ] B1W-I2 focused real-Isaac admitted reset + nonterminal step verified
- [ ] B1W-I3 terminal/autoreset/slot/capture/ack/G2/R3 real-Isaac gate verified
- [ ] B1W-I4 event wrapper facade integration implemented/reviewed
- [ ] production proposal/resolver/scheduler semantics separately designed and accepted
- [ ] full terminal learner/critic transport separately designed and accepted
- [ ] runtime-readiness review explicitly authorizes the event profile
- [ ] training/playback/evaluation explicitly authorized and verified

All numeric thresholds and variable-cardinality extensions remain unresolved and out of scope.

## 15. STOP-condition audit

| Stop condition | Result |
|---|---|
| control source ambiguity | resolved: only Ak-admitted P2 ownership is authoritative |
| reset bootstrap gap | absent in audited constructor; first explicit reset can be admitted |
| environment bypass cannot fail closed | resolved by first-hook current-call validation design |
| I3 admission identity gap | resolved by distinct same-Ak finalization latch design |
| second lifecycle/store authority required | no; O1 only sequences narrow ports |
| Isaac core patch required | no |
| B1/B1W semantic rewrite required | no; only narrow production validation extension is proposed |
| scheduler/HARL dependency required for first proof | no; direct deterministic legal claim and existing controller suffice |

No stop condition remains at the design level. This is not an implementation-readiness or runtime-readiness declaration: the next phase requires explicit authorization and review of this design.

## 16. Phase boundary

This report and the corresponding `TASK_PROGRESS.md` update are the only authorized writes. No code, tests, configuration, wrapper, environment, resolver/controller, HARL, readiness, or checkpoint artifact was changed. No Python test, Isaac/AppLauncher process, training, playback, or evaluation was run.

**STOP. Await GPT review. Do not enter B1W-I1 implementation without a new explicit phase authorization.**
