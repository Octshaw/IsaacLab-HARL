# Phase 9G-8H-1: Playback Proposal-Effective Attribution Diagnostic Implementation And Fake Regression

Date: 2026-07-20

## 1. Classification

`BOUNDED-PLAYBACK-READY`

The reviewed default-off, playback-only attribution collector is implemented. All new fake-sequence and architecture regressions pass, as do the four required existing non-environment lifecycle suites. No playback, checkpoint load, AppLauncher, Isaac Sim, training, or evaluation ran.

## 2. Starting Baseline

```text
HEAD:
  3f79af53b731dd880dcda22766000313c317b93a

commit:
  3f79af53 fix(assignment): persist runtime ValueNorm state in native checkpoints
```

The pre-existing worktree changes were documentation-only:

```text
modified:
  AgentRead/TASK_PROGRESS.md

untracked historical 9G-8G reports/archives:
  AgentRead/20260710/PHASE9G8G1R2T_TIMEOUT_CORRECTED_CONTROLLED_SMOKE_EXECUTION_REPORT.md
  AgentRead/20260710/PHASE9G8G1R2_VALUENORM_FIXED_CONTROLLED_TRAINING_SMOKE_RETRY_EXECUTION_REPORT.md
  AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R2T_TIMEOUT_CORRECTED_SMOKE_20260710.md
  AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R2_SMOKE_RETRY_EXECUTION_20260710.md

untracked Phase 9G-8H-0 documents:
  AgentRead/20260720/PHASE9G8H0_PLAYBACK_PROPOSAL_EFFECTIVE_ATTRIBUTION_AND_LOAD_BALANCE_DIAGNOSTIC_DESIGN.md
  AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8H0_PLAYBACK_ATTRIBUTION_DESIGN_20260720.md
```

No pre-existing production Python, test, or YAML change was present. All pre-existing documents were preserved.

## 3. Files

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  assignment_playback_attribution_diagnostics.py

scripts/environments/
  test_assignment_playback_attribution_diagnostics.py

AgentRead/20260720/
  PHASE9G8H1_PLAYBACK_PROPOSAL_EFFECTIVE_ATTRIBUTION_DIAGNOSTIC_IMPLEMENTATION_AND_FAKE_REGRESSION.md
  TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8H1_ATTRIBUTION_IMPLEMENTATION_20260720.md
```

Modified:

```text
scripts/reinforcement_learning/harl/play_assignment.py
AgentRead/TASK_PROGRESS.md
```

Explicitly not modified:

```text
assignment_harl_wrapper.py
assignment_lifecycle_resolver.py
assignment_lifecycle_resolver_runtime.py
assignment_controller.py
scan_mobile_manipulator_env.py
observation/shared-observation/mask/reward modules
checkpoint save/load modules
all YAML files
installed HARL and the Conda environment
```

## 4. Collector Architecture

`AssignmentPlaybackAttributionCollector` is project-local and playback-only. It owns diagnostic continuity and aggregation only. It has no resolver, runtime-adapter, environment callback, controller callback, or state-transition ownership.

Inputs are clone-owned at the collector boundary:

```text
raw actor action ids
selected action probabilities
pre/post physical and task snapshots
cloned wrapper lifecycle-resolution payload
effective/controller assignment
exact wrapper-produced controller command tensors
done/reset validity metadata
```

`AssignmentPlaybackPhysicalSnapshot` captures copied `base_pos`, `scanner_pos`, `viewpoint_pos`, coverage, availability, and feasibility tensors. Nested payloads and returned rows/summaries are copied so caller mutation cannot alter collector state and collector processing cannot alter runtime state.

## 5. Event-Draining Proof

The existing owner chain remains unchanged:

```text
resolver event drain
  -> runtime adapter only

runtime-adapter event drain
  -> AssignmentHarlWrapper.step() only

collector input
  -> wrapper.get_last_assignment_lifecycle_resolution() clone accessor
```

The collector source contains no event-drain call. `play_assignment.py` reads the clone accessor exactly once per enabled decision and only inside `if attribution_collector is not None`.

## 6. CLI And Default-Off Identity

Added playback-only flags:

```text
--log_assignment_proposal_effective
--assignment_proposal_effective_output_dir PATH
--print_assignment_proposal_effective
```

CLI contract validation occurs before `AppLauncher(args_cli)`:

- Logging without an output directory is an error.
- An output directory without logging is an error.
- A path that is an existing regular file is an error.
- Any collision with a frozen target artifact is an error.
- Printing alone creates an in-memory collector and no files.

With all flags unset:

```text
collector factory is not called
collector is absent
no extra physical snapshot is captured
wrapper lifecycle payload is not read
no output path or file is created
action selection and wrapper.step() are unchanged
existing aggregate console lines are unchanged
```

The new module is not imported by the training entry point.

## 7. Joined Row Contract

Schema:

```text
phase9g8h1_assignment_proposal_effective_attribution_v1
```

One row is assembled atomically for every:

```text
(method_name, episode_id, env_id, decision_step, robot_id)
```

It includes the frozen identity, raw action, decoded proposal, pre owner/mask/pair state, effective/controller assignment, rejection reason, projected events, post active state, completion/release flags, controller norm, base motion, target distance/progress, coverage split, and reset validity fields.

The active/owner/pair pre-state is the collector's copied previous resolver post snapshot. Initial explicit-reset state is canonical idle/unowned/pair-none. Active-owner consistency, action decoding, proposal/effective changed, controller/effective equality, and segment continuity are hard invariants.

Leading initial reset events are stored as episode-boundary events and excluded from the first action's primary attribution. Done-step reset remains attached to the executed decision and outranks completion/release only as the primary label; completion/release flags remain true.

## 8. Event Projection And Primary Attribution

Robot-specific events use authoritative `robot_id`. Exact conflicts are projected only through explicit `claiming_robot_ids`, `winner_robot_id`, and loser fields. Robot-less events with no authoritative claimant remain in `unprojected_environment_events`.

Projected event lists retain source order and full event objects. Event names are counted dynamically rather than through a closed enumeration.

The frozen priority is implemented exactly from `reset` through `noop_idle`, with `unclassified` as the fallback. In particular:

```text
release_budget_failure > budget_failure
target_completed > ordinary continuation/start
active_target_infeasible_deferred > continuation/switch rejection
claim_lost is the conflict loser label
the conflict winner remains attempt_started
```

## 9. Coverage And Motion Semantics

`controller_action_l2_norm` uses the exact 9D command already produced by the wrapper. Base motion is XY displacement. Target distance is scanner-to-effective-target distance, never raw-proposal distance.

For non-done decisions, coverage delta is copied from true caller-visible pre/post state. Authoritative robot-specific `target_completed` events provide assigned completion credit. The current environment does not expose a reliable robot source for incidental coverage, so incidental ids remain empty and remaining deltas are explicitly unattributed. No nearest-distance guess is used.

For done decisions without a pre-reset physical capture:

```text
post_state_pre_reset_available = false
base motion and post-distance fields = null
coverage post/delta fields = null
```

Reset state is never substituted as executed post state. No environment reset hook was added.

## 10. Summary And Segments

Per-robot summaries include all frozen proposal/effective, rejection, continuation, conflict, completion/release, idle/executing, coverage, zero-command, zero-motion, zero-progress, and segment counters.

The exact identities are checked:

```text
idle_step_count + executing_step_count == total_decision_steps
proposal_noop_count + proposal_target_count == total_decision_steps
```

Work accounting uses effective assignment. Contract-C noop continuation, rejected switching while active, and deferred active infeasibility are executing even when command and motion are zero.

Segments start only on an actual `attempt_started` event, and that event is asserted to agree with `new_claim_started`. They continue across same-target, Contract-C noop, rejected switch, and deferred infeasibility rows. Completion, budget release, reset, and finalize close them with the frozen release types. An unexplained active-target change closes with `invariant_break` and raises `AttributionInvariantError`.

Episode load summaries include per-robot execution/start/completion/release/coverage vectors, ranges, fractions, zero-work robot ids, and Jain values. A zero-total Jain value is null. These values are labeled diagnostics only, not reward terms, optimizer objectives, or automatic pass/fail criteria.

## 11. Output Behavior

Logging writes exactly:

```text
assignment_proposal_effective_rows.csv
assignment_proposal_effective_summary.json
assignment_target_segments.csv
```

Rows append only after a complete environment decision is assembled. Finalize closes open segments as `playback_truncated`, writes segment/summary artifacts, and is idempotent. CSV JSON cells and summary JSON parse successfully in regression tests.

Compact console rows are emitted only with `--print_assignment_proposal_effective` and only at the existing playback diagnostic cadence. Full event JSON is not printed.

## 12. Fake And Architecture Tests

New test result:

```text
scripts/environments/test_assignment_playback_attribution_diagnostics.py
  16 cases passed
```

Coverage includes:

```text
default-off factory isolation and CLI validation
output collision and print-only no-file behavior
snapshot/controller/payload/input nonmutation
idle noop and initial reset boundary
accepted target and continuous segment
same-target and Contract-C noop continuation
switch rejection and active infeasibility priority
exact-conflict winner/loser projection
owned, covered, unavailable, and failed-pair rejection
completion, budget failure/release, and done reset
assigned versus unattributed coverage
variable E/M/N, multiple environments, and subset reset
robot-less unprojected events
Jain values and zero-total null
open segment truncation and invariant break
CSV/JSON parsing and idempotent finalize
compact formatting and static playback architecture
```

## 13. Existing Regression Results

All required existing non-environment suites passed:

```text
test_assignment_lifecycle_resolver_smoke.py
  20 cases passed

test_assignment_lifecycle_resolver_runtime_smoke.py
  12 cases passed

test_assignment_lifecycle_runtime_integration_smoke.py
  10 cases passed

test_assignment_lifecycle_transition_logger_smoke.py
  11 sequences passed
```

Total existing cases/sequences passed: `53`.

One initial batch command incorrectly supplied `--json` to the runtime-integration script, whose parser does not support it. That invocation exited at argument parsing. The corrected commands were then run independently and all passed as listed above.

## 14. Syntax And Static Validation

The configured interpreter was verified as:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

`py_compile` passed for:

```text
assignment_playback_attribution_diagnostics.py
play_assignment.py
test_assignment_playback_attribution_diagnostics.py
```

Static results:

```text
git diff --check: PASS
changed-file trailing whitespace scan: PASS
collector event-drain dependency scan: PASS
default-off guarded payload-access assertion: PASS
training-import isolation assertion: PASS
```

The only textual `pop_events(` occurrence added by this phase is the test assertion that forbids it from the collector source.

## 15. Deviations And Limitations

The instruction's historical `AgentRead/20260710` deliverable paths were corrected to the current local date `AgentRead/20260720` as required by `AGENTS.md`.

No wrapper change and no pre-reset hook were needed. Consequently, done-step physical and coverage post values are explicitly null rather than reconstructed.

Incidental coverage is not attributed because current source cannot establish a reliable robot owner. Environment-wide coverage delta and unattributed ids are context fields replicated on robot rows; assigned completion remains the robot-specific workload signal.

This phase proves only pure composition and static playback integration. It does not prove real runtime payload timing, output volume, checkpoint interaction, visual behavior, or policy quality.

## 16. Next Recommendation

After review and explicit authorization, one bounded Phase 9G-8H-2 proposal/effective diagnostic playback may be considered. This phase does not authorize or begin it.

No commit was made.
