# Phase B0-3D-R2 Synchronous Terminal Ack Protocol Closeout

## 1. Classification and decision

    classification:
      PHASE-B0-3DR2-SYNCHRONOUS-TERMINAL-ACK-PROTOCOL-CLOSEOUT-COMPLETE-AWAITING-GPT-REVIEW

    B0-1A / B0-1B / B0-2:
      review passed

    B0-3D:
      conditional review completed

    B0-3D-R:
      R1/R2 closed

    B0-3D-R2:
      targeted closeout complete

    R1:
      closed

    R2:
      closed

    R3 synchronous ack-before-next-step:
      frozen

    pending-transition resume:
      not required

    concurrent terminal consumer:
      not required

    Phase-A contract revision:
      none

    B0 contract/runtime gap:
      none

    Python/runtime changes:
      none

    B0-3 implementation:
      not authorized

    Phase B/C/D/E:
      not entered

    Isaac/training/playback/evaluation:
      not run

    commit:
      none

No stop condition was reached:

    STOP — B0-3 SYNCHRONOUS PRE-STEP GUARD GAP:
      not reached

    STOP — B0 CONTRACT/RUNTIME GAP:
      not reached

    STOP — B0-3D-R2 CONTROL-FLOW GAP:
      not reached

This is a documentation-only targeted closeout. It adds no runtime code,
terminal slot, consumer, wrapper transport, test, configuration, checkpoint,
or readiness wiring.

## 2. Base authorities and targeted precedence

The base authorities remain:

    PHASE_B0_3D_ENVIRONMENT_PRE_RESET_AND_EPISODE_RESET_INTEGRATION_DESIGN.md

    PHASE_B0_3DR_TARGETED_ENVIRONMENT_INTEGRATION_SEMANTIC_REVISION.md

Precedence is exact:

    R1 owner-qualified physical_terminated:
      controlled by B0-3D-R

    R2 terminal storage and capability semantics:
      controlled by B0-3D-R

    R3 normal synchronous production scheduling:
      controlled by B0-3D-R2

R3 does not delete the permissive B0-private one-slot storage capability. It
narrows the normal synchronous environment route: an outstanding terminal slot
is allowed to exist across autoreset, but the next physical step cannot begin
until its designated destructive consumer has acknowledged it.

All other B0-3D/B0-3D-R semantics remain unchanged, including R1 equations,
exact terminal key, observer/consumer split, autoreset transaction, partial
reset, all-E transition identity, coverage/reward order, poison rules,
existing-profile isolation, and event readiness.

## 3. Exact current source-order audit

### 3.1 DirectMARLEnv step prefix

DirectMARLEnv.step at source/isaaclab/isaaclab/envs/direct_marl_env.py:328-392
currently performs:

    convert caller action tensors to env device
    -> optional action-noise application
    -> task _pre_physics_step(actions)
    -> query rendering state
    -> decimated _apply_action / scene.write / sim.step / scene.update
    -> increment episode/common counters
    -> dones and reward

The first task-owned hook is _pre_physics_step at line 361. No simulator write,
simulator step, scene update, episode counter, or task physical integration has
occurred before it.

### 3.2 Current task hook

The scan task _pre_physics_step at
scan_mobile_manipulator_env.py:2805-2812 currently starts by:

    write previous_actions
    -> clamp/write current actions
    -> integrate base/scanner task-space state
    -> mark USD debug dirty

Therefore the event-profile permission guard can be the first statement in
this task hook, before every current task-state mutation.

### 3.3 Action-noise boundary

DirectMARLEnvCfg declares action_noise_model=None by default at
direct_marl_env_cfg.py:214. ScanMobileManipulatorEnvCfg does not override it.
The exact current scan route therefore performs only local action tensor device
conversion before _pre_physics_step; it does not consume action-noise state or
RNG before the guard.

The future B0-3 event integration MUST retain action_noise_model=None unless a
separate source-order review provides an earlier supported guard. Enabling
action noise on the event route without that review would invalidate the
zero-new-step-work claim because noise application occurs before the task hook.
This closeout does not authorize such a configuration change.

### 3.4 Synchronous wrapper control flow

The current wrapper calls _env.step at
assignment_harl_wrapper.py:482. It regains control only after environment
reward/autoreset/observation return, performs synchronous post-step work, and
returns at line 560.

A future designated terminal consumer can therefore:

    receive completed env.step result
    -> read exact terminal artifact
    -> capture it into transport-owned immutable storage
    -> acknowledge exact key
    -> return control for the next step request

No environment callback is needed while env.step is executing. There is no
env-step/wrapper-ack circular wait.

## 4. Selected normal synchronous protocol

Option A is frozen:

    terminal physical transition
    -> lifecycle transaction success
    -> terminal handoff installed
    -> reward
    -> autoreset
    -> env.step returns
    -> designated consumer reads exact artifact
    -> consumer successfully captures/transports artifact
    -> designated consumer acknowledges exact key
    -> only then may the next env.step begin

The acknowledgement boundary is:

    ack-before-reset:
      not required

    ack-before-current-step-return:
      not required

    ack-before-next-physical-step:
      required

The terminal transition must always complete its lifecycle, reward, autoreset,
and return normally. R3 introduces no wait or re-entry inside _get_dones,
_get_rewards, or _reset_idx.

## 5. Storage capability versus production scheduling

The B0-private terminal storage capability remains:

    slot survives autoreset
    slot is immutable and generation-bound
    approved observers may repeatedly read it
    slot may coexist with reset current PublishedLifecycleView
    designated consumer alone may destructively acknowledge it

The normal synchronous production policy is stricter:

    any required unacknowledged terminal slot
      blocks the next full-batch physical step request

Thus B0-3D-R line-of-thought that an old slot could coexist with later
nonterminal work remains a lower-level storage capability or possible future
alternate-route property. B0-3D-R2 controls for the normal synchronous
environment route: that route performs no later physical work before ack.

## 6. Pre-step permission port

The environment receives a narrow lifecycle-domain permission operation,
conceptually:

    assert_physical_step_allowed()

The exact implementation name may differ, but its semantics may not.

At the first statement of the event-profile _pre_physics_step:

    if any env row has a terminal slot requiring designated acknowledgement:
      raise typed synchronous terminal-ack protocol rejection
    else:
      return normally

The environment invokes the operation but never reads terminal-store state
directly. It receives no:

    terminal slot object
    terminal artifact mutation capability
    destructive acknowledgement capability
    terminal-store lock
    ack authority identity

The runtime domain checks the obligation under its supported terminal
permission boundary.

## 7. Exact guard placement and zero-work guarantee

For the current event scan configuration, the guard is:

    after:
      action argument tensors are locally moved to the environment device

    before:
      previous_actions write
      current actions write/clamp
      base/scanner integration
      USD debug mutation
      _apply_action
      scene.write_data_to_sim
      sim.step
      scene.update
      simulation-step counter increment
      episode/common counter increment
      raw reporter capture
      lifecycle transaction or token allocation

If the guard rejects, no new physical or task transition has begun. Local
device-converted action temporaries are discarded and are not environment
state.

The implementation MUST place the guard before the existing first statement of
the task hook. Checking later in _pre_physics_step, _get_dones, or the
coordinator transaction is not the R3 normal-route guard.

The implementation MUST NOT copy or override the whole DirectMARLEnv.step
method merely to add the check.

## 8. Typed rejection semantics

Missing required acknowledgement at the next step request is classified as:

    synchronous terminal-consumer protocol precondition violation

The future implementation must raise a B0-private typed runtime error, with a
conceptual classification such as:

    SynchronousTerminalAckRequiredError

It carries no terminal artifact and grants no ack capability. It may report
immutable diagnostic identities for blocked rows:

    env_id
    required episode_generation
    required transition_generation

The error is raised synchronously; the guard does not:

    sleep
    poll
    wait on a callback
    auto-ack
    clear/drop/overwrite the slot
    start physics then fail
    mutate lifecycle state or generation
    poison the runtime

After the designated consumer performs the exact valid ack, another step
request rechecks the guard and may proceed normally.

## 9. Full-vector semantics

DirectMARLEnv.step advances one synchronized full vector batch. R3 therefore
freezes:

    if any env row has required unacknowledged terminal slot:
      reject the entire next env.step before physical mutation

Example:

    env 0:
      unacknowledged terminal slot

    env 1..3:
      no slot

    result:
      no row begins the next physical transition

B0-3 does not attempt row-local physics freezing while other rows continue.
This preserves all-E transition-generation identity.

The full-batch backpressure is bounded and non-deadlocking in the normal route:
the preceding env.step has returned, the designated consumer has control, and
it can synchronously read, capture, ack, then issue the next step.

## 10. Successful capture and acknowledgement

R2 remains exact:

    terminal key =
      (env_id, episode_generation, transition_generation)

The designated consumer must:

    read_terminal(exact key)
    -> copy/capture all required immutable artifact content into
       consumer-owned immutable in-process transport storage
    -> verify capture succeeded
    -> acknowledge_terminal(same exact key)

read_terminal alone is not successful capture and never acknowledges.

If capture fails:

    slot remains occupied
    next physical step remains blocked
    consumer may retry capture/read
    no lifecycle poison occurs

Wrong/stale/future/no-slot/duplicate acknowledgement remains a typed R2
rejection. It does not satisfy the R3 obligation, so the next step remains
blocked while the exact slot is occupied.

No ack-latest, ack-all, ack-by-env-only, or implicit read-ack API is introduced.

## 11. Read-only observers

Approved diagnostic/logger/debug/evaluation observers may:

    read the exact terminal artifact
    retain immutable no-alias historical copies

They do not:

    own destructive ack
    satisfy the R3 guard
    delay or veto designated consumer acknowledgement

After successful designated ack frees the slot, observer copies already
obtained remain valid historical data. Production need not keep the live slot
because an observer wants to inspect it later.

## 12. Autoreset and current view

The terminal slot is installed before autoreset and survives it. Autoreset is
not delayed for acknowledgement.

After env.step returns:

    terminal slot:
      episode p
      transition g
      terminal result/artifact

    current PublishedLifecycleView:
      episode p+1
      transition g
      reset state
      result None

The wrapper/environment may use the current reset view to construct the
completed step's post-reset observations. The designated consumer separately
captures the historical terminal slot. The next physical step remains blocked
until exact ack.

Ack removes only terminal-slot lifetime state. It does not mutate or republish
the current view.

## 13. No pending-transition resume

The normal synchronous route has no:

    resume_pending_transition
    continue_previous_step
    reenter_get_dones
    wait-inside-env-step callback
    concurrent terminal-consumer thread requirement

Once a physical step starts, it completes and returns. Ack happens between
steps.

The B0-3D-R same-staged-report/context retry remains valid only for ordinary
receipt-free facts/semantic failures and as a defensive lower-level behavior.
It is not part of normal R3 acknowledgement flow.

## 14. Defensive occupied-slot guard

The B0-3D-R receipt-free rule remains:

    new terminal candidate sees occupied slot
      -> reject before ledger consume
      -> no result/state/generation/reward/reset mutation

Under correct normal synchronous R3 scheduling, this state is unreachable
because the pre-step permission guard rejects before physics.

The occupied-slot guard is retained to detect:

    bypassed pre-step guard
    unsupported direct coordinator/transaction invocation
    internal protocol bug
    future alternate execution route

It is not a production wait point and does not imply that an already executed
physical step normally pauses and resumes after ack.

An external/direct receipt-free capacity rejection follows the lower-level
defensive retry semantics already frozen by R2. An impossible attempt to
overwrite an occupied slot after authoritative success remains fatal/poison.

## 15. Poison boundary

| Condition | Result | Poison |
|---|---|---:|
| next step requested before required ack | typed precondition rejection before physics | no |
| diagnostic observer reads slot | immutable read; obligation unchanged | no |
| wrong/stale consumer ack | typed R2 rejection; obligation unchanged | no |
| exact consumer capture fails | slot retained; next step blocked | no |
| exact consumer ack succeeds | slot freed; next step may pass guard | no |
| occupied slot reaches defensive receipt-free candidate check | typed defensive rejection | no |
| internal slot overwrite/identity corruption | fatal; no overwrite/publication | yes |
| post-authority impossible success-tail failure | fatal | yes |

Forgetting to ack is a synchronous protocol error, not state corruption.

## 16. Existing-profile and readiness isolation

The guard applies only to the future event_gated_local_mrta domain.

The existing profiles:

    legacy
    lifecycle_contract_c
    lifecycle_ablation
    diagnostics_hidden_state

receive no:

    pre-step terminal-ack guard
    lifecycle runtime domain
    terminal slot
    terminal observer/consumer capability

Their current _pre_physics_step and wrapper/environment routes remain
unchanged.

Event runtime readiness remains interface_only/blocked.
require_assignment_profile_runtime_ready remains unchanged. No training or
playback route is enabled.

## 17. Contract and capability verdict

R3 needs only a B0-private scheduling permission operation over the R2 slot
state. It changes no:

    ExecutionTransitionFacts
    LifecycleTransitionResult
    LifecycleEvent
    TaskLifecycleState
    RobotLifecycleState
    TerminationReason
    profile/checkpoint descriptor

The current task hook is early enough under the exact current no-action-noise
configuration, and the synchronous wrapper regains control between environment
steps. Therefore:

    STOP — B0-3 SYNCHRONOUS PRE-STEP GUARD GAP:
      not reached

    STOP — B0 CONTRACT/RUNTIME GAP:
      not reached

    STOP — B0-3D-R2 CONTROL-FLOW GAP:
      not reached

## 18. Future implementation impact

Existing proposed slices remain:

    B0-3I1:
      pure episode rebuild transaction

    B0-3I2:
      dormant domain aggregate and capability ports

    B0-3I3:
      staged pre-reset reporter/facts adapter

    B0-3I4:
      terminal handoff and environment/reset integration

The later authorized environment wiring MUST include the event-only pre-step
permission guard, either in I4 or a separately reviewed narrow slice. This
document does not authorize either.

## 19. Future R3 test oracle

No test is run in this design phase. A future implementation must prove:

1. R3-T1: terminal env.step completes and returns without in-step ack;
2. R3-T2: terminal slot survives autoreset;
3. R3-T3: next step before ack rejects at the first task hook statement before
   actions/task state/simulator/counter mutation;
4. R3-T4: missing-ack rejection does not poison or mutate;
5. R3-T5: exact designated capture and ack allows the next step;
6. R3-T6: wrong/stale ack rejects and next step remains blocked;
7. R3-T7: diagnostic read does not satisfy the obligation;
8. R3-T8: retained observer copy remains valid after ack;
9. R3-T9: one blocked row rejects the full E-row physical step;
10. R3-T10: defensive occupied-slot receipt-free guard remains but is
    unreachable through the correct synchronous route;
11. R3-T11: four existing profiles execute no guard;
12. R3-T12: event runtime readiness remains blocked;
13. guard tests snapshot task/action/counter/simulator-facing buffers and prove
    bit-exact no mutation on rejection;
14. no test uses sleeps or concurrent consumer timing.

If a future event configuration enables action noise, a separate test/review
must prove a guard before noise-state mutation or stop the integration.

## 20. Numeric and phase boundary

All eleven numeric TBDs remain unresolved:

    top_k_tasks_per_robot
    local_robot_cap
    local_task_cap
    pair_abs_threshold
    pair_rel_threshold
    component_abs_threshold
    component_rel_threshold
    transfer_penalty
    rejection_penalty_scale
    alignment_time_constant
    assignment_retry_cadence

No value is selected.

This phase does not implement wrapper transport, HARL buffer sidecar, critic
terminal state, ack consumer class, runner changes, terminal slot, domain port,
or environment hook.

## 21. Final handoff

    classification:
      PHASE-B0-3DR2-SYNCHRONOUS-TERMINAL-ACK-PROTOCOL-CLOSEOUT-COMPLETE-AWAITING-GPT-REVIEW

    targeted precedence:
      R3 normal synchronous scheduling only

    selected protocol:
      terminal env.step completes and autoresets
      -> designated consumer capture/ack
      -> next full-batch physical step allowed

    pre-step guard:
      event-only
      first statement of current task _pre_physics_step
      typed non-poison rejection

    pending resume / concurrent consumer:
      not required

    Phase-A schema change:
      none

    B0-3 implementation:
      not authorized

    next action:
      GPT/user review; do not begin B0-3I1 or environment integration
