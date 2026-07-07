# Phase 9G-5 Failed-Pair Memory Design Decision Review

Date: 2026-07-07

## Scope And Boundary

Phase 9G-5 is a documentation-only design decision review.

No mechanism was implemented. No Python source files were modified. No training, playback, simulation rollout, broad evaluation, or D=10 run was performed. No commit was made.

No wrapper behavior, env behavior, TTL duration default, TTL decrement timing, reward formula/scale, actor/shared observation, `available_actions` shape, assignment action id semantics, controller behavior, HARL code, baseline solver, scenario YAML, installed package, cooldown tuning, Phase 9F redirect guardrail tuning, new failure criteria, or env-level lifecycle behavior was changed.

## Files Inspected

Handoff and evidence reports:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/AGENTS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260705/PHASE9G0_ACTIVE_TASK_LIFECYCLE_DESIGN_AUDIT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G1_LIFECYCLE_RECONSTRUCTION_ANALYZER_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G2_FAILED_PAIR_RELEASE_MEMORY_IMPLEMENTATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G3_FAILED_PAIR_MEMORY_PLAYBACK_VALIDATION_REPORT.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4A_TTL_BOUNDARY_SEMANTICS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260706/PHASE9G4B_FAILED_PAIR_MEMORY_D6_PLAYBACK_VALIDATION_REPORT.md
```

Source files inspected for boundary confirmation only:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_harl_wrapper.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_state.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scenario_config.py
```

Analyzers inspected for evidence interpretation only:

```text
scripts/environments/analyze_phase9g1_lifecycle_reconstruction.py
scripts/environments/analyze_phase9g3_failed_pair_memory_validation.py
scripts/environments/analyze_phase9g4b_failed_pair_memory_d6_validation.py
```

## Evidence Chain

| Phase | Mechanism activation | Action suppression | Return delay | Total same-owner returns | Coverage improvement | Noop / fail-open |
| --- | --- | --- | --- | --- | --- | --- |
| 9G-1 offline reconstruction | No live mechanism; proxy evidence only | None | Median proxy delay 5 in existing Phase 9F histories | 12 / 12 released budget-failed segments returned to same owner | `coverage_gain_within_20_count = 0` | Not applicable |
| 9G-2 implementation | Disabled-by-default wrapper-local pair memory added | Fake-env smoke showed pair-scoped suppression can work when enabled | TTL memory added, not playback-tested | No playback result | No playback result | Smoke covered noop, fail-open, reset, coverage clear |
| 9G-3 D=5 playback | `trigger_count = 6` | `suppressed_count = 0` | Memory expired before T+6 direct return rows | `same_owner_returns = 6` | `coverage_gain_within_20_count = 0` | `noop_action_rate = 0.0`, `fail_open_count = 0` |
| 9G-4A TTL review | Fake-env only | D future decision rows confirmed | Active T+1 through T+D; inactive T+D+1 | Not a playback phase | Not a playback phase | Fake-env confirmed fail-open and noop preservation |
| 9G-4B D=6 playback | `trigger_count = 6` | `suppressed_count = 6` | Original T+6 returns were suppressed; returns shifted to T+7 | `same_owner_returns = 6` | `coverage_gain_after_release_count = 0`, `coverage_gain_within_20_count = 0` | `noop_action_rate = 0.0`, `fail_open_count = 0` |

Key distinction:

```text
Activation means the memory was recorded.
Suppression means an available target entry was actually masked.
Delay means the old return row moved later.
Success would require reducing total repeated same-owner returns or producing useful coverage behavior.
```

Phase 9G-4B proved activation and suppression, but not success.

## Why TTL-Only Memory Is Insufficient

D=6 suppressed all six previously missed T+6 reacquisition rows, but the same failed pairs were selected at T+7 immediately after memory expiry. This means the guardrail changed one decision row, not the underlying task state.

TTL-only masking does not change:

```text
task ownership
robot execution state
failure state visible to the policy
target release semantics
robot state
task state
long-term policy preference
```

The policy still sees the task through essentially the same observation semantics after the temporary mask expires. The pair was never represented as "failed for this robot but released to others" in a persistent lifecycle. It was only temporarily removed from the current robot's action mask.

Therefore the T+7 reacquisition is not surprising. Once the hidden pair memory reaches zero, the target again appears as an ordinary available assignment candidate. Since the policy preference and visible state did not change, the policy can repeat the same decision.

Temporary action suppression and explicit lifecycle state are different mechanisms:

| Concept | TTL-only failed-pair memory | Explicit active-task/release lifecycle |
| --- | --- | --- |
| State owner | Wrapper-local hidden tensor | Wrapper or env lifecycle state |
| Main effect | Temporarily masks an existing target id | Defines ownership, execution, failure, release, and reassignment |
| Policy visibility | Hidden except through `available_actions` contents | Should be visible if used during training |
| Task completion | Still only `viewpoints_covered` | Still should remain tied to `viewpoints_covered` |
| Failure meaning | Temporary pair mask | Explicit attempt termination or release reason |
| Expected effect | Delay or redirect immediate choice | Change whether a fresh assignment decision should occur |

Increasing TTL may only postpone the same decision because it extends the hidden mask window without changing the visible reason for failure, the policy's target preference, or the assignment/execution contract.

## Bounded D=10 Diagnostic

A single D=10 playback could still provide some diagnostic value:

```text
test whether the return simply shifts to T+11
observe whether a longer alternative-action window creates any coverage gain
measure overmask, noop, and fail-open pressure under a wider mask window
strengthen the evidence for stopping the TTL-only path
```

Its limitations are substantial:

```text
D=6 already demonstrated immediate post-expiry return
D=10 still does not create ownership, execution, failure, or release state
one episode cannot establish generality
longer TTL may block useful same-robot reacquisition after transient conditions
the hidden failed-pair state is not represented in observations
no evidence from D=5 or D=6 suggests coverage improvement
```

Decision:

```text
D=10 is not scientifically necessary to make the main design decision.
D=10 may be useful as an optional bounded stress test if the user wants empirical closure on "does it just shift again?"
D=10 should not be treated as the recommended next phase and should not be run automatically.
```

Would D=10 materially change the design decision? Probably not unless it unexpectedly reduces same-owner returns or creates coverage gain without noop/fail-open/overlap regressions. Given D=6, the most likely result is a later return after expiry or a longer temporary diversion without coverage gain.

## Explicit Active-Task / Release Lifecycle

The minimum lifecycle concepts that address the observed issue are:

| Concept | Meaning |
| --- | --- |
| `robot_idle` | Robot can receive a fresh assignment. |
| `robot_executing` | Robot is pursuing an active target and should not be reassigned every step unless released or failed. |
| `active_target_id` | The target currently owned by a robot. |
| `task_open` | Target is uncovered and available for assignment. |
| `task_claimed` | Target is owned by a robot attempt. |
| `task_completed` | Target became covered through `viewpoints_covered`. |
| `pair_active` | Robot-target attempt is in progress. |
| `pair_failed` | Robot-target attempt terminated by a failure criterion. |
| `pair_released` | Ownership was intentionally dropped after failure, timeout, completion by another robot, or explicit release. |
| `pair_temporarily_unavailable_to_same_robot` | Same robot should not immediately reacquire a failed/released target. |
| `ownership_transfer_to_another_robot` | Target can be claimed by a teammate without marking the task globally failed. |

A true lifecycle would change the system in ways TTL masking does not:

```text
A robot would not make a fresh assignment decision every execution step.
An assigned target would have explicit ownership.
Failure would terminate an attempt.
Release would be an explicit transition.
A failed robot-target pair could remain marked independently of target availability to teammates.
The policy or assignment layer could distinguish executing from idle.
```

Existing code already has vocabulary in `assignment_state.py` for task and robot statuses. However, `scan_mobile_manipulator_env.py` currently derives `task_status` from `viewpoints_covered` and fills `robot_status` as idle. Those fields are not yet a persistent lifecycle machine.

## Architectural Placement

| Placement | Semantic correctness | Implementation risk | Hidden-state risk | Checkpoint compatibility | Baseline comparability | Observation implications | Training implications | Variable robot/viewpoint support |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Analyzer-only | Low for behavior, high for evidence | Low | None | Full | Full | None | None | Good if CSV columns remain generic |
| Wrapper-local | Medium for pair ownership prototypes | Medium | Medium to high if used for training | Good when disabled by default | Good if disabled, altered if enabled | Playback guardrails can stay hidden; training should expose persistent state | Requires care before training | Good with `[env, robot, target]` tensors |
| Env-owned | High | High | Lower if exposed consistently | Risky unless default path preserves old spaces | Changes task semantics if enabled | Likely needs observation fields | Likely requires retraining | Best long-term place for task/robot lifecycle |
| Hybrid wrapper prototype then env promotion | High over stages | Medium | Managed by phase boundary | Good early, explicit later | Good if comparisons are versioned | Start hidden for diagnostics, expose before training | Supports evidence-first retraining decision | Good if pair tensors and status fields stay dimension-driven |

Decision:

```text
Analyzer-only is no longer enough because the evidence question has been answered.
Wrapper-local TTL memory is useful as a disabled diagnostic guardrail, but insufficient as the main path.
Env-owned lifecycle is semantically clean but too large as the next immediate phase.
Hybrid is the best route: narrow lifecycle boundary audit first, then choose wrapper prototype or env promotion deliberately.
```

## Observation And Action Semantics

A playback-only wrapper guardrail can remain hidden from the policy for diagnosis. That was acceptable for Phase 9G-3 and Phase 9G-4B because the question was whether a fixed checkpoint changes behavior under a mask overlay.

A persistent lifecycle used during training should probably be represented in observations. Otherwise the policy experiences stateful availability changes without seeing the cause, which increases hidden-state and distribution-shift risk.

`available_actions` shape can remain:

```text
[M, N+1]
```

where the final column is noop. Future lifecycle work can continue to mask existing target ids rather than adding new action ids.

However, the contents of `available_actions` may become stateful, and action semantics may change from:

```text
choose a target every step
```

to:

```text
assign a target only when the robot is idle or released
```

That is a real MDP/action-semantics change even if tensor shape and action ids remain unchanged. It should be treated as a new design phase, not as a minor guardrail extension.

## Current Failed-Pair Memory Code Decision

Decision:

```text
retain disabled-by-default as a diagnostic / experimental guardrail
do not continue TTL tuning as the main solution
do not remove it in Phase 9G-5
do not train with it enabled without a separate observation/lifecycle review
```

Rationale:

```text
Default-disabled identity passed in Phase 9G-3.
The code has useful diagnostics and fake-env coverage.
D=6 proved the mechanism can suppress target entries when the TTL covers the row.
The same D=6 evidence also proved TTL-only suppression does not solve the observed lifecycle failure.
```

The code should be documented as experimental and not described as an active-task lifecycle solution.

## Option Review

### Option A: Stop Extending TTL-Only Path Now

Recommended now: yes.

This preserves the evidence and avoids spending more phases on duration tuning after D=6 showed the policy returns after expiry. It keeps the disabled code available for diagnostics without treating it as the solution.

### Option B: One Bounded D=10 Playback Diagnostic

Recommended now: optional, not necessary.

This may provide empirical closure on whether a longer mask only shifts the return to T+11. It should be run only if explicitly authorized, with no tuning loop and no training.

### Option C: Continue TTL Tuning As Main Solution

Recommended now: no.

The mechanism has not reduced total returns or improved coverage. Continuing the same tuning path risks optimizing a hidden mask duration rather than modeling task execution and release semantics.

### Option D: Replace Direction With Explicit Lifecycle Design

Recommended now: yes, but staged.

Do not jump straight into implementation. The next smallest useful phase is an active-task/release lifecycle boundary audit that specifies ownership, idle/executing transitions, release rules, observation exposure, and compatibility constraints.

## Decision Matrix

| Option | Expected information gain | Implementation effort | Behavior-change risk | Hidden-state risk | Checkpoint compatibility | Likelihood of reducing same-owner returns | Likelihood of improving coverage | Recommended now |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Stop TTL-only path now | Medium; decision clarity | Low | None | None | Full | Indirect only | Indirect only | Yes |
| Run one D=10 bounded diagnostic | Medium; tests shift-to-expiry hypothesis | Low to medium | Playback-only if no code changes | Medium if enabled mask remains hidden | Compatible for playback | Low to medium | Low | Optional |
| Continue TTL tuning | Low after D=6 | Medium over repeated runs | Medium | High if used beyond playback | Compatible only while disabled/default | Low unless TTL becomes very long | Low | No |
| Wrapper-local active ownership prototype | Medium to high | Medium | Medium | Medium unless exposed | Good if disabled by default | Medium to high | Unknown | Not immediate; audit first |
| Env-owned lifecycle | High | High | High | Lower if observations expose it | Requires careful default compatibility | High | Unknown to medium | Not immediate; design first |
| Hybrid diagnostic/wrapper/env migration | High over stages | Medium staged | Managed by phase gates | Managed by observation review | Good early; explicit later | Medium to high | Unknown | Yes as direction |

## Recommended Next Smallest Phase

Recommended next phase:

```text
Phase 9G-6A: explicit active-task/release lifecycle boundary audit.
```

Boundary:

```text
documentation/design only
focus on ownership, robot idle/executing transitions, pair failure, release, reassignment, and observation/action semantics
no implementation
no training
no playback
no reward changes
no observation or action-shape changes
```

Optional alternative:

```text
Phase 9G-6B: one bounded D=10 playback-only diagnostic
```

Only choose 9G-6B if the user explicitly wants one final TTL stress test. It should answer only whether the return shifts again or whether a longer alternative-action window produces coverage gain. It should not become a TTL tuning loop.

Not recommended:

```text
Continue TTL tuning as the main solution.
Start a large env-level lifecycle implementation immediately.
Train with hidden failed-pair memory enabled.
```

## Final Decision

Phase 9G-5 decision:

```text
Stop extending TTL-only failed-pair memory as the main path.
Retain the current failed-pair memory code disabled-by-default as diagnostic/experimental guardrail code.
Do not run D=10 automatically; treat it as optional and not necessary for the main design decision.
Proceed toward explicit active-task/release lifecycle design through a narrow documentation-only boundary audit.
```

This decision is based on the Phase 9G evidence chain:

```text
TTL memory can activate.
TTL memory can suppress when the duration covers the row.
TTL memory can delay same-owner reacquisition.
TTL memory has not reduced total same-owner returns.
TTL memory has not improved coverage.
TTL memory is not an active-task lifecycle.
```

## Validation

Allowed validation for this documentation-only phase:

```text
git status --short --untracked-files=all
git diff --check
```

Result:

```text
git status --short --untracked-files=all: completed; worktree still contains earlier uncommitted Phase 9G files plus the new Phase 9G-5 report/archive.
git diff --check: passed with LF-to-CRLF working-copy warnings only.
```

No Python validation is required because no Python source files should be modified in Phase 9G-5.
