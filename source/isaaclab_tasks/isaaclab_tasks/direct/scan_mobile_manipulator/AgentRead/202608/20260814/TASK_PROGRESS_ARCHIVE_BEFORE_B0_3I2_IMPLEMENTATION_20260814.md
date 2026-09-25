# TASK_PROGRESS

## Current status

    classification:
      PHASE-B0-3I1-PURE-EPISODE-REBUILD-TRANSACTION-COMPLETE-AWAITING-GPT-REVIEW

    Phase A:
      final review passed; previously committed by user

    B0-1A / B0-1B / B0-2:
      review passed; regressions remain green

    B0-3D / B0-3D-R / B0-3D-R2:
      design closed

    B0-3I1:
      complete at pure/default-off episode-rebuild level
      awaiting GPT/user review

    event-profile readiness:
      interface_only / Phase-A blocked

    environment integration:
      not implemented

    B0-3I2 / B0-3I3 / B0-3I4:
      not entered; not authorized

    Phase B/C/D/E:
      not entered; not authorized

    Isaac/AppLauncher/training/playback/evaluation:
      not run

    commit:
      none

## Latest completed phase

B0-3I1 adds one pure, dormant episode-rebuild primitive inside the existing
B0-2 transaction/publication domain. It creates no facts, token, consume,
receipt, result, lifecycle event, reward, or transition-generation increment.

Implemented semantics:

- exact event-profile-only reset input gate;
- one immutable/no-alias B0-private reset input;
- the same primitive handles initial `-1 -> 0` bootstrap and later `k -> k+1`;
- full or partial selected-row rebuild;
- selected task state becomes AVAILABLE;
- selected robot state becomes NEEDS_ASSIGNMENT;
- selected ownership becomes -1;
- selected failed pairs, completion counters, and termination reason reset to
  false, zero, and NONE;
- unselected lifecycle and generation rows remain bit-exact;
- StateStore global version increments exactly once per successful rebuild;
- selected episode generation increments exactly once;
- transition generation remains unchanged;
- selected outstanding transition candidates reject before mutation;
- reset publication uses `PublishedLifecycleView(result=None)` with false
  terminated/truncated flags.

## Active architecture / implementation path

The B0-2 coordinator still exposes only its reviewed public surface. B0-3I1 is
a B0-private context protocol:

    coordinator._episode_rebuild(reset_inputs)
      -> context.commit_physical_reset_complete()

Preparation occurs while holding the existing publication lock:

    reject poison
    -> validate exact profile/domain/selection/reset tensors
    -> capture and cross-check StateStore, clock, and current publication
    -> reject selected outstanding transition candidates
    -> build and validate one full-domain merged reset state
    -> prepare StateStore swap and reset view before the physical-success signal

Before the signal, no lifecycle state, clock, publication, or ledger changes.
Exiting the context without the signal is a non-poison abort.

After the signal, the no-fail success tail is:

    StateStore prepared pointer swap
    -> LifecycleGenerationClock.advance_episode(selected)
    -> exact full-domain generation validation
    -> one reset PublishedLifecycleView installation

Any post-signal failure poisons the coordinator, publishes no new view, and
does not roll back or continue. Readers use the same publication lock and can
observe only old-state/old-episode or reset-state/new-episode.

The context exposes no raw store, clock, writer, generation-advance, ledger,
factory, receipt, or publication-install capability. Existing B0-2 public
exports and coordinator public API are unchanged.

## Changed / new files

Current B0-3I1 authorized delta:

- modified
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_lifecycle_transaction_runtime.py`;
- added
  `scripts/environments/test_assignment_phase_b0_3i1_episode_rebuild_transaction_pure.py`;
- added
  `AgentRead/202608/20260814/PHASE_B0_3I1_PURE_EPISODE_REBUILD_TRANSACTION_IMPLEMENTATION_REPORT.md`;
- archived the prior handoff as
  `AgentRead/202608/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_3I1_IMPLEMENTATION_20260814.md`;
- rewrote this current handoff.

The worktree already contained uncommitted/untracked B0-1A, B0-1B, B0-2,
design, test, and report files. They were preserved; the frozen contracts and
production environment/wrapper/resolver/controller routes were not edited.

## Verification

Interpreter:

    C:\isaacenvs\isaac45_harl\python.exe

Syntax and dedicated suite:

- changed/new Python `py_compile`: passed;
- B0-3I1 normal mode: 12/12 passed;
- B0-3I1 `-I -B`: 12/12 passed;
- deterministic publication checks use `threading.Event`, not sleep.

Regression results:

- B0-2 lifecycle authority transaction: 18/18 passed;
- B0-1A execution facts producer: 9/9 passed;
- B0-1B generation clock: 12/12 passed;
- lifecycle transition contract: 12/12 passed;
- assignment profile contract: 16/16 passed;
- event-profile schema contract: 9/9 passed;
- Phase-A default-off identity: 16/16 passed;
- profile production wiring: 10/10 passed;
- event-gated MRTA contract: 13/13 passed.

Closeout checks:

- frozen contract hash audit: passed;
- no B0-3I1 production wiring: passed;
- environment/wrapper/resolver/controller/HARL/config/checkpoint changes: none;
- no Isaac/AppLauncher/training/playback/evaluation run;
- `git diff --check`, whitespace, Markdown, path, scope, and final hash checks:
  passed.

## Known issues / unfinished work

- no environment `_reset_idx` or autoreset invocation;
- no dormant domain aggregate/capability-port production composition;
- no pre-reset reporter/facts adapter;
- no terminal slot, destructive acknowledgement, or synchronous pre-step guard;
- no real failure/release/health reporters;
- no event wrapper/controller/resolver integration;
- no Phase-B assignment commit, scheduling, Top-K/local sets, component solve,
  DVM, cost, retry, checkpoint, or training route;
- no Isaac/runtime/performance evidence.

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

## Do not do

Without explicit authorization:

- do not begin B0-3I2, B0-3I3, B0-3I4, or Phase B/C/D/E;
- do not wire the rebuild into environment, wrapper, resolver, controller, HARL,
  config, checkpoint, training, playback, or evaluation routes;
- do not add a terminal slot/ack protocol or pre-step guard in I1;
- do not add pre-reset reporters, physical completion reconstruction, coverage,
  reward, or owner-gating environment hooks in I1;
- do not weaken readiness or modify frozen contracts;
- do not add rollback/cancellation/automatic retry or a second authority;
- do not select numeric TBDs;
- do not run Isaac/AppLauncher/training/playback/evaluation or commit.

## Next step

Review the pure B0-3I1 implementation report and dedicated 12-group evidence.
Do not infer authorization for B0-3I2 or production environment integration.

## Detailed reports / archives

- AgentRead/202608/20260814/PHASE_B0_3I1_PURE_EPISODE_REBUILD_TRANSACTION_IMPLEMENTATION_REPORT.md
- AgentRead/202608/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_3I1_IMPLEMENTATION_20260814.md
- AgentRead/202608/20260814/PHASE_B0_3DR2_SYNCHRONOUS_TERMINAL_ACK_PROTOCOL_CLOSEOUT.md
- AgentRead/202608/20260814/PHASE_B0_3DR_TARGETED_ENVIRONMENT_INTEGRATION_SEMANTIC_REVISION.md
- AgentRead/202608/20260814/PHASE_B0_3D_ENVIRONMENT_PRE_RESET_AND_EPISODE_RESET_INTEGRATION_DESIGN.md
- AgentRead/202608/20260814/PHASE_B0_2_PURE_LIFECYCLE_AUTHORITY_TRANSACTION_IMPLEMENTATION_REPORT.md
- AgentRead/202608/20260814/PHASE_B0_2DR_TARGETED_LIFECYCLE_AUTHORITY_SEMANTIC_REVISION.md
- AgentRead/202608/20260814/PHASE_B0_2D_LIFECYCLE_AUTHORITY_SEMANTIC_CLOSEOUT_DESIGN.md
- AgentRead/202608/20260809/PHASE_B0_1B_PURE_GENERATION_CLOCK_IMPLEMENTATION_REPORT.md
- AgentRead/202608/20260809/PHASE_B0_1A_PURE_EXECUTION_FACTS_PRODUCER_IMPLEMENTATION_REPORT.md

