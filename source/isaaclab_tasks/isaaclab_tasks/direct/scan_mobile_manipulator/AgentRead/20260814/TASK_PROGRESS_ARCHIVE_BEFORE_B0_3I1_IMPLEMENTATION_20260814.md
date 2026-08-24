# TASK_PROGRESS

## Current status

    classification:
      PHASE-B0-3DR2-SYNCHRONOUS-TERMINAL-ACK-PROTOCOL-CLOSEOUT-COMPLETE-AWAITING-GPT-REVIEW

    Phase A:
      final review passed; previously committed by user

    B0-1A / B0-1B / B0-2:
      review passed

    B0-3D:
      conditional review completed

    B0-3D-R:
      R1/R2 closed

    B0-3D-R2:
      R3 synchronous terminal ack design complete
      awaiting GPT/user review

    R1 owner-consistent physical termination:
      frozen

    R2 single destructive terminal ack authority:
      closed

    R3 synchronous ack-before-next-step:
      frozen

    pending-transition resume / concurrent terminal consumer:
      not required

    B0-3 implementation:
      not authorized

    environment pre-reset integration:
      not implemented

    episode reset integration:
      not implemented

    event-profile readiness:
      interface_only / Phase-A blocked

    Phase B/C/D/E:
      not entered; not authorized

    Python/runtime changes:
      none in B0-3D-R2

    Isaac/AppLauncher/training/playback/evaluation:
      not run

    commit:
      none

## B0-3D decision

No design stop condition was reached:

- the pair-shaped scan candidate exists inside current _get_dones before task
  reduction, coverage mutation, and autoreset;
- frozen ExecutionTransitionFacts needs no new field;
- a domain aggregate can reserve generation contexts internally while the
  environment retains only a narrow pre-reset/reset port;
- a prepared reset StateStore replacement, clock advance, and immutable reset
  view can be committed under the existing publication/poison model.

Frozen outcomes:

    current runtime order: audited
    pre-reset integration point: frozen
    runtime stack ownership/lifetime: frozen
    transition-context reservation: frozen
    raw facts source matrix: frozen
    completion attribution hook: frozen
    coverage/reward ordering: frozen
    termination projection: frozen
    terminal handoff strategy: frozen
    episode reset transaction: frozen
    episode/transition generation reset semantics: frozen
    reset publication atomicity: frozen
    existing-profile isolation: frozen
    Phase-A contract revision: none
    B0 contract/runtime gap: none

Targeted B0-3D-R closeout:

    R1:
      raw pair candidate
      -> transaction-private prestate
      -> owner-qualified completion_signals
      -> prospective canonical coverage
      -> physical_terminated = all canonical tasks prospectively covered

    R2:
      multiple approved read-only terminal observers
      exactly one designated destructive consumer capability
      exact (env, episode, transition) acknowledgement only
      permissive one-slot persistence remains a private storage capability

Targeted B0-3D-R2 closeout:

    R3 normal synchronous route:
      terminal step completes, autoresets, and returns
      -> designated consumer captures and exact-acks terminal artifact
      -> only then may the next full-batch env.step begin

    pre-step guard:
      first statement of event-only task _pre_physics_step
      any unacked row rejects the full batch before physical/task mutation
      typed protocol rejection; no poison, wait, polling, or auto-ack

## Frozen integration outline

    every physical step, all E rows:
      stage raw scan report without mutation
      -> reserve exact contexts inside capability-limited port
      -> owner-gate pair completion from StateStore prestate
      -> build canonical facts
      -> B0-2 consume/finalize/state-swap/clock-commit/publication
      -> install terminal per-env read/ack slots
      -> commit coverage/reward bookkeeping
      -> _get_rewards
      -> native DirectMARLEnv autoreset
      -> env.step returns
      -> designated consumer capture + exact ack
      -> next physical step permission

    selected episode rebuild:
      validate no outstanding transition
      -> prepare merged reset state and reset PublishedLifecycleView
      -> native physical/task _reset_idx work
      -> prepared StateStore swap, version +1
      -> episode_generation +1 as final internal marker
      -> publish reset state with unchanged transition_generation and result None

Every successful physical step commits a transition generation even when no
lifecycle event occurs. Reset creates no physical transition, facts, result,
reward, receipt, event, or terminal handoff.

## Capability and handoff boundary

One event-profile domain later owns one retained producer, clock, StateStore,
transaction coordinator, poison/publication boundary, and terminal handoff
store. The environment receives only transition-finalize and episode-rebuild
operations plus a narrow event-only pre-step permission check. External readers
receive only immutable current view and terminal observer ports. Exactly one
domain-lifetime designated consumer gets destructive acknowledgement.

Raw producer, clock, store, ledger, receipt, result factory, authority stamp,
and publication-install capabilities are never distributed to environment or
wrapper.

The chosen terminal protocol is one persistent per-env slot keyed by
(env_id, episode_generation, transition_generation). It survives autoreset
until exact acknowledgement. The post-reset current view is a different
identity: new episode generation, unchanged transition generation, reset
state, and result absent.

Wrong/stale reads or acknowledgements receive typed rejection without poison.
An internal overwrite or terminal identity mismatch is fatal/poison. An
occupied slot may coexist with episode rebuild, but the normal synchronous
route rejects the next full-batch physical step until exact ack. The older
nonterminal-progress rule remains only a lower-level storage capability;
B0-3D-R2 controls production scheduling.

## Reporter boundary

Ready or narrowly adaptable from current source:

- stable env IDs and internal generations;
- horizon/time-limit tensors;
- pre-mutation coverage;
- local pair-shaped scan candidate;
- task/robot/ownership prestate from StateStore.

Real reporters remain deferred for:

- structural terminal pair failure;
- forced release;
- robot unavailable;
- robot recovered;
- independent non-time-limit bad-transition classification.

All-false pure fixtures are not runtime reporter evidence.

## Existing-profile/default-off identity

The four existing profiles construct no event aggregate, port, clock, store, or
publication lock and keep current scan/done/reward/reset/wrapper paths. The
event profile remains blocked by the unchanged runtime-ready gate. B0-3D does
not authorize dormant production wiring.

## Planned implementation slices

The design recommends separately authorized slices:

1. B0-3I1: pure episode rebuild transaction;
2. B0-3I2: dormant domain aggregate and capability ports;
3. B0-3I3: staged pre-reset reporter/facts adapter;
4. B0-3I4: terminal handoff and reset integration.

No slice is authorized by this handoff.

## Known unfinished work

- no environment pre-reset invocation;
- no episode reset transaction implementation;
- no real failure/release/health reporters;
- no terminal critic-sidecar tensor or HARL transport;
- no event wrapper/controller/resolver integration;
- no Phase-B assignment commit, scheduling, Top-K/local sets, cost, retry,
  component solving, DVM, or checkpoint use;
- no Isaac/runtime/training/performance evidence.

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

## B0-3D-R2 documentation scope

Authorized delta:

- new synchronous terminal-ack protocol closeout;
- updated current handoff.

No new archive was needed: this update remains a concise in-place handoff
revision below the AGENTS.md limit. The prior B0-3D archive remains unchanged.

## Do not do

Without explicit authorization:

- do not begin a B0-3 implementation slice;
- do not edit environment/wrapper/resolver/controller/HARL/runtime Python;
- do not weaken readiness or change frozen contracts;
- do not add rollback/cancellation/auto-retry or a second authority;
- do not select numeric TBDs;
- do not run Isaac, AppLauncher, training, playback, evaluation, or commit.

## Verification

    allowed checks:
      read-only source inspection
      git status
      git diff --check
      Markdown fence/trailing-whitespace/path/classification checks
      changed-file scope and pre-existing-file hash audit

    Python tests / Isaac:
      not run

    completed results:
      B0-3D-R2 report 608 lines; no trailing whitespace
      current handoff remains below 300 lines; no trailing whitespace
      classification/path/R3/guard/stop markers present
      B0-3D and B0-3D-R authorities byte-identical to preflight
      env/wrapper/B0-2 transaction Python targets 3/3 byte-identical
      git diff --check passed; no tracked Python diff
      HEAD 912b3b59831fcad8dd29ac575b2a1851bf2c21d1 unchanged
      index empty

## Next step

Review the B0-3D-R2 synchronous ack closeout. Do not infer B0-3I1 or
environment integration authorization.

## Detailed reports / archives

- AgentRead/20260814/PHASE_B0_3DR2_SYNCHRONOUS_TERMINAL_ACK_PROTOCOL_CLOSEOUT.md
- AgentRead/20260814/PHASE_B0_3DR_TARGETED_ENVIRONMENT_INTEGRATION_SEMANTIC_REVISION.md
- AgentRead/20260814/PHASE_B0_3D_ENVIRONMENT_PRE_RESET_AND_EPISODE_RESET_INTEGRATION_DESIGN.md
- AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_3D_ENVIRONMENT_RESET_DESIGN_20260814.md
- AgentRead/20260814/PHASE_B0_2_PURE_LIFECYCLE_AUTHORITY_TRANSACTION_IMPLEMENTATION_REPORT.md
- AgentRead/20260814/PHASE_B0_2DR_TARGETED_LIFECYCLE_AUTHORITY_SEMANTIC_REVISION.md
- AgentRead/20260814/PHASE_B0_2D_LIFECYCLE_AUTHORITY_SEMANTIC_CLOSEOUT_DESIGN.md
- AgentRead/20260809/PHASE_B0_PRE_RESET_LIFECYCLE_AUTHORITY_RUNTIME_DESIGN.md
- AgentRead/20260809/PHASE_B0_1B_PURE_GENERATION_CLOCK_IMPLEMENTATION_REPORT.md
- AgentRead/20260809/PHASE_B0_1A_PURE_EXECUTION_FACTS_PRODUCER_IMPLEMENTATION_REPORT.md

