# Phase 9G-8H-2: Bounded Proposal-Effective Attribution Playback Runtime Validation

Date: 2026-07-20

## 1. Classification

`PASS`

The one authorized deterministic headless playback completed naturally. The three diagnostic artifacts contain exactly 900 joined robot rows for 300 environment decisions and 12 target segments. Row invariants, event projection, primary attribution, physical/null validity, coverage accounting, summary aggregation, segment continuity, and load-balance recalculation all passed. There were no unclassified rows, invariant breaks, duplicate keys, or duplicate effective target assignments.

The behavioral result is unambiguous:

- `robot_0` remained motionless because its policy selected raw noop on all 300 decisions. No resolver rejection was involved.
- `robot_1` remained lifecycle-executing on all 300 decisions. Its target changes followed five completions, one budget release, one episode reset, and one final truncated segment, not rejected switching.
- `robot_2` worked in short segments but was effectively idle for 239 decisions because its policy selected idle noop. Nine additional noop proposals occurred while active and were correctly interpreted by Contract C as continuation.

## 2. Starting State And Worktree Preflight

| Check | Result |
| --- | --- |
| HEAD | `3f79af53b731dd880dcda22766000313c317b93a` |
| Commit | `3f79af53 fix(assignment): persist runtime ValueNorm state in native checkpoints` |
| Accepted 8H-0 state | `DIAGNOSTIC-DESIGN-READY` |
| Accepted 8H-1 state | `BOUNDED-PLAYBACK-READY` |
| Expected production change | Modified `play_assignment.py` only |
| Expected new implementation/test | Collector module and fake regression only |
| Other worktree changes | AgentRead reports, archives, and `TASK_PROGRESS.md` only |
| YAML changes | None |
| Wrapper/resolver/controller/environment/checkpoint changes | None |
| `git diff --check` before launch | PASS; line-ending warnings only |

The only uncommitted production/test files were the reviewed Phase 9G-8H-1 set:

```text
M  scripts/reinforcement_learning/harl/play_assignment.py
?? scripts/environments/test_assignment_playback_attribution_diagnostics.py
?? source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
   assignment_playback_attribution_diagnostics.py
```

No unexpected behavior file was present, so runtime execution was allowed. The Conda interpreter resolved to `C:\isaacenvs\isaac45_harl\python.exe`.

## 3. Checkpoint, Process, And Output Preflight

Checkpoint directory:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh/
seed-00001-2026-07-10-15-59-12/models
```

Read-only checkpoint checks passed:

```text
checkpoint_kind: final
checkpoint_generation: 2
manifest_format_version: assignment_checkpoint_contract_v2
contract fingerprint:
  19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6
actors:
  actor_agent_robot_0.pt
  actor_agent_robot_1.pt
  actor_agent_robot_2.pt
completion marker:
  assignment_training_state_manifest.json
```

The loader later confirmed `purpose=normal_evaluation` and `legacy_fallback=False`. No critic or ValueNorm state was restored.

The process scan found no repository-associated Python, conda-run, Isaac Sim, or Kit process. The frozen semantic parent, exact `seed-00001` directory, and all three frozen artifact paths were absent. Nothing was deleted, renamed, reused, or overwritten.

## 4. Exact Execution

Execution mechanism: one attached foreground PowerShell process, with stdout and stderr tee'd to a temporary path outside the repository and a 600-second tool timeout.

Temporary console path:

```text
C:\Users\33506\AppData\Local\Temp\
phase9g8h2_bounded_attribution_console_20260720_151050.log
```

Frozen command executed exactly once from the repository root:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl --no-capture-output python -u scripts\reinforcement_learning\harl\play_assignment.py `
  --task Isaac-Scan-Mobile-Manipulator-Direct-v0 `
  --algorithm happo `
  --assignment_rl `
  --scenario_config source\isaaclab_tasks\isaaclab_tasks\direct\scan_mobile_manipulator\configs\scenarios\algorithm_proxy_component_mesh.yaml `
  --num_envs 1 `
  --dir results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh\seed-00001-2026-07-10-15-59-12\models `
  --max_steps 300 `
  --seed 1 `
  --device cuda:0 `
  --headless `
  --log_assignment_proposal_effective `
  --assignment_proposal_effective_output_dir results\isaaclab\Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\assignment_happo_n50_phase9g8h2_bounded_proposal_effective_playback\seed-00001 `
  --print_assignment_proposal_effective `
  env.assignment_lifecycle_profile=lifecycle_contract_c `
  env.assignment_cooldown_enabled=true `
  env.assignment_cooldown_trigger_mode=budget `
  env.assignment_cooldown_apply_to_action_mask=false `
  env.assignment_redirect_guardrail_enabled=false `
  agent.device.cuda=true `
  agent.device.cuda_deterministic=true `
  agent.model.use_recurrent_policy=false `
  agent.model.use_naive_recurrent_policy=false `
  agent.algo.share_param=false
```

| Field | Result |
| --- | --- |
| Start | `2026-07-20T15:10:50.8145810+08:00` |
| End | `2026-07-20T15:13:13.0387079+08:00` |
| Elapsed | `142.2241269` seconds |
| External limit | 600 seconds; not reached |
| Real process exit code | `0` |
| Automatic retry | None |

## 5. Runtime Contract And Console Result

The runtime established:

```text
algorithm: happo
assignment RL: enabled
checkpoint: final generation 2
checkpoint purpose: normal_evaluation
legacy fallback: false
profile: lifecycle_contract_c
policy sequence: feed-forward
share_param: false
seed: 1
E/M/N: 1/3/50
actor/shared/action widths: 1059/3183/51
raw/decoded noop: 50/-1
reset available_actions: [1,3,51] on cuda:0
max_steps: 300
headless: true
```

The actor/shared dimensions and profile are bound by the successfully validated contract-v2 manifest and fingerprint. Actor construction and state-dict loading exercised width 1059; the frozen shared contract records width 3183. Playback remained actor-only and performed no learning update.

Console counts:

| Item | Count |
| --- | ---: |
| Aggregate decision lines | 300 |
| Compact per-robot lines | 900 |
| Tracebacks | 0 |
| Runtime errors | 0 |
| Attribution invariant errors | 0 |
| Aggregate lines with nonzero duplicate count | 0 |

The environment constructed, reset completed, all three actors loaded, 300 wrapper decisions completed, the collector finalized, the application closed normally, and the process exited 0.

## 6. Artifact Inventory

Output directory:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8h2_bounded_proposal_effective_playback/
seed-00001
```

Exactly three files were created:

| File | Bytes | Parse result |
| --- | ---: | --- |
| `assignment_proposal_effective_rows.csv` | 709657 | PASS |
| `assignment_proposal_effective_summary.json` | 23573 | PASS |
| `assignment_target_segments.csv` | 3651 | PASS |

There were no temporary, checkpoint, TensorBoard, model, or video artifacts in this directory.

## 7. Joined Row Validation

| Contract | Result |
| --- | --- |
| Schema | `phase9g8h1_assignment_proposal_effective_attribution_v1` |
| Row count | 900 |
| Environment decisions | 300 |
| Episode split | episode 0: 299 decisions; episode 1: 1 decision |
| Rows per decision | Exactly robot ids 0, 1, 2 |
| Duplicate join keys | 0 |
| Raw action range/decode | PASS |
| Proposal/effective/controller range | PASS |
| Controller equals effective assignment | PASS, 900/900 |
| Proposal/effective changed flags | PASS, 900/900 |
| Noop flags | PASS, 900/900 |
| Selected probabilities | All finite and in `[0,1]` |
| Resolver event JSON and source ordering | PASS |
| Canonical rejection reasons | PASS; observed value was `none` |
| Primary attribution vocabulary | PASS |
| Unclassified rows | 0 |
| Duplicate projected events in one row | 0 |
| Duplicate effective target decisions | 0 |

Work accounting used effective assignment: `-1` is idle and `>=0` is executing. All nine Contract-C noop continuations were counted as executing.

## 8. Physical, Reset, And Coverage Validity

```text
post-state-valid rows:   897
post-state-invalid rows: 3
```

The three invalid rows are the three robots on the episode-0 done/reset decision. Their base motion, post distance, distance progress, post coverage, and coverage-delta fields are null. Reset-state values were not substituted. Every applicable value on the other 897 rows was finite. Effective-noop rows had null target-distance fields as designed.

Coverage checks passed:

- Every count matched its JSON id list.
- Assigned completion, incidental, and unattributed sets did not overlap.
- Incidental coverage remained empty; no nearest-distance guess was made.
- Seven robot-owned completions were attributed to robots.
- Eleven robot-less `target_completed` events remained unprojected environment events.
- Episode 0 covered 18 of 50 targets before reset. The environment-wide delta context is deliberately replicated on robot rows, so the summary's `[18,18,18]` coverage-delta vector is not per-robot credit. Assigned completion `[0,5,2]` is the authoritative robot workload signal.

Console `distance_to_selected_viewpoint=nan` values occurred only for raw noop selections in the pre-existing aggregate diagnostic. They are expected noop sentinels and are separate from the validated nullable effective-target fields.

## 9. Event, Summary, And Segment Reconciliation

Projected row-event totals:

| Event | Count |
| --- | ---: |
| `noop_idle` | 539 |
| `attempt_started` | 12 |
| `attempt_continued_same_target` | 340 |
| `attempt_continued_noop_contract_c` | 9 |
| `target_completed` | 7 |
| `budget_failure` | 2 |
| `release_budget_failure` | 2 |
| `reset` | 3 |

Three initial reset events were correctly retained as episode-boundary events rather than first-action causes. The 11 unprojected environment events were all robot-less target completions.

The summary metadata, six per-episode/per-robot groups, two episode load summaries, validity counters, event counters, rejection counters, coverage counters, and segment counts independently reconciled with the rows. Total robot decisions across summaries were 900. `invariant_failures` was empty.

All 12 segments passed start/end/duration, identity, target, terminal-event, overlap, and row-continuity checks:

```text
target_completed:   7
budget_failure:     2
reset:              1
playback_truncated: 2
invariant_break:    0
```

The 12 `attempt_started` events matched the 12 segment starts exactly.

## 10. Per-Robot Attribution Counts

| Metric | robot_0 | robot_1 | robot_2 |
| --- | ---: | ---: | ---: |
| Total decisions | 300 | 300 | 300 |
| Proposal noop | 300 | 0 | 248 |
| Proposal target | 0 | 300 | 52 |
| Nonrejected target proposals | 0 | 300 | 52 |
| Effective idle | 300 | 0 | 239 |
| Effective executing | 0 | 300 | 61 |
| Proposal/effective changed | 0 | 0 | 9 |
| Rejected proposals | 0 | 0 | 0 |
| `noop_idle` event | 300 | 0 | 239 |
| Contract-C noop continuation | 0 | 0 | 9 |
| Attempt started | 0 | 8 | 4 |
| Same-target continuation | 0 | 292 | 48 |
| Switch rejected | 0 | 0 | 0 |
| Claim lost | 0 | 0 | 0 |
| Exact-conflict win | 0 | 0 | 0 |
| Owned-target rejected | 0 | 0 | 0 |
| Covered-target rejected | 0 | 0 | 0 |
| Failed-pair rejected | 0 | 0 | 0 |
| Unavailable-target rejected | 0 | 0 | 0 |
| Active infeasible deferred | 0 | 0 | 0 |
| Target completed | 0 | 5 | 2 |
| Budget release | 0 | 1 | 1 |
| Zero controller command | 300 | 0 | 239 |
| Zero base motion, valid rows | 299 | 40 | 263 |
| Zero target-distance progress | 0 | 20 | 14 |
| Target segments | 0 | 8 | 4 |

A reset can outrank another event as the primary label. Thus `robot_0` has 300 `noop_idle` events but primary attribution is 299 `noop_idle` plus one `reset`; similarly `robot_2` has 239 `noop_idle` events but 238 primary noop labels plus one reset.

## 11. Robot 0 Diagnosis

`robot_0` proposed raw noop on all 300 decisions and proposed no real target. Therefore:

```text
real-target proposals:             0
accepted real-target proposals:    0
changed to noop/another target:    0
resolver rejections:               0
active-target decisions:           0
nonzero controller commands:       0
nonzero base-motion valid rows:    0
target completions/releases:       0 / 0
```

The factual cause of motionlessness was policy choice, not resolver rejection or physical controller failure. The policy chose noop on every decision; the resolver preserved idle noop; the controller produced a zero command; and the base had zero motion on all 299 physically valid rows. The reset row's physical post fields are correctly null.

## 12. Robot 1 Diagnosis And Segments

`robot_1` proposed a target on all 300 decisions, had no rejected proposal, and remained effectively executing on all 300. Every controller command was nonzero. Forty valid executing rows had zero base displacement because reaching/scanning can retain a nonzero 9D command while the base remains stationary.

| Ep/seg | Target | Steps | Duration | Min/final distance | Dwell / zero-progress / zero-base | Complete / budget | Infeasible / switch-reject | Release |
| --- | ---: | --- | ---: | --- | --- | --- | --- | --- |
| 0/1 | 17 | 1-50 | 50 | 0.2214 / 0.2214 | 1 / 0 / 11 | 1 / 0 | 0 / 0 | completed |
| 0/2 | 35 | 51-96 | 46 | 0.2390 / 0.2390 | 1 / 0 / 0 | 1 / 0 | 0 / 0 | completed |
| 0/3 | 2 | 97-135 | 39 | 0.1962 / 0.1962 | 1 / 0 / 1 | 1 / 0 | 0 / 0 | completed |
| 0/4 | 25 | 136-195 | 60 | 0.1663 / 0.1663 | 1 / 0 / 4 | 1 / 0 | 0 / 0 | completed |
| 0/5 | 46 | 196-224 | 29 | 0.2250 / 0.2250 | 1 / 0 / 0 | 1 / 0 | 0 / 0 | completed |
| 0/6 | 3 | 225-285 | 61 | 0.0000 / 0.0000 | 24 / 20 / 24 | 0 / 1 | 0 / 0 | budget failure |
| 0/7 | 10 | 286-299 | 14 | 2.3319 / 2.3319 | 0 / 0 / 0 | 0 / 0 | 0 / 0 | reset |
| 1/8 | 17 | 1-1 | 1 | 5.9474 / 5.9474 | 0 / 0 / 0 | 0 / 0 | 0 / 0 | playback truncated |

The observed waiting before target changes was lifecycle continuation, not an accepted policy switch:

- The first five target changes followed authoritative target completion.
- Target 3 remained active for 61 steps. It spent 24 steps within the position tolerance, with 20 zero-progress steps, then received budget failure/release at step 285.
- Target 10 ended because the environment reset on episode-0 step 299.
- The final target 17 was still active when playback ended and was closed as `playback_truncated`.
- There were no switch rejections and no active-target infeasibility events.

The diagnostic cannot attribute scan-orientation, FOV, or controller-internal causes beyond these directly recorded lifecycle, distance, command, and motion facts.

## 13. Robot 2 Diagnosis

`robot_2` proposed noop 248 times and a real target 52 times. All 52 target proposals were nonrejected; no proposal was changed by rejection. Its nine proposal/effective changes were Contract-C noop continuation: the proposal was `-1` while the active target remained effective.

```text
effective idle/executing: 239 / 61
episode-0 idle intervals:
  steps 50-135: 86 decisions
  steps 147-299: 153 decisions
```

Every one of the 239 effective-idle decisions carried `noop_idle`; no ownership, failed-pair, covered, unavailable, claim-loss, or other resolver rejection occurred. The long idle intervals were therefore policy noop intervals.

Target segments:

| Ep/seg | Target | Steps | Duration | Noop continue | Zero-base / zero-progress | Release |
| --- | ---: | --- | ---: | ---: | --- | --- |
| 0/1 | 28 | 1-46 | 46 | 0 | 15 / 8 | completed |
| 0/2 | 24 | 47-49 | 3 | 0 | 1 / 0 | completed |
| 0/3 | 44 | 136-146 | 11 | 9 | 9 / 6 | budget failure |
| 1/4 | 28 | 1-1 | 1 | 0 | 0 / 0 | playback truncated |

There were 25 valid active-target rows with zero base motion: target 28 steps 32-46, target 24 step 49, and target 44 steps 138-146. All 61 executing rows had nonzero controller commands. Thus these were active execution/dwell rows, not resolver idle and not zero-command rows.

Robot 2's intermittent work was a mixture of accepted active execution, two completions, one budget release, and long policy-noop idle intervals. Resolver rejection did not contribute.

## 14. Load Balance

Recalculated over all 300 decisions:

| Metric | Values for robots 0/1/2 |
| --- | --- |
| Executing steps | `[0,300,61]` |
| Idle steps | `[300,0,239]` |
| Target starts | `[0,8,4]` |
| Target completions | `[0,5,2]` |
| Budget releases | `[0,1,1]` |
| Assigned completion credit | `[0,5,2]` |
| Executing fractions | `[0.0000,0.8310,0.1690]` |
| Completion fractions | `[0.0000,0.7143,0.2857]` |
| Executing-step range | `300` |
| Completion-count range | `5` |
| Robots with zero starts | `[0]` |
| Robots with zero completions | `[0]` |
| Jain executing fairness | `0.4635069337` |
| Jain completion fairness | `0.5632183908` |

The main source of imbalance was policy output: robot 0 always selected noop and robot 2 selected idle noop for 239 decisions. Contract C correctly converted nine robot-2 noops into active continuation. There were no proposal rejections in this trajectory.

These values are descriptive playback diagnostics only. They are not a reward recommendation, convergence result, or policy-quality acceptance criterion.

## 15. Exact-Target Conflict And Duplicate Evidence

```text
exact_claim_conflict_resolved: 0
claim_lost by robot:           [0,0,0]
exact-conflict wins:           [0,0,0]
owned_target_rejected:         [0,0,0]
duplicate effective targets:   0 of 300 decisions
aggregate duplicate_count:     0 on all 300 console lines
```

Exact-target exclusivity held throughout the observed playback. No simultaneous exact-target claim occurred, so this trajectory did not exercise the lowest-cost/robot-id winner branch. The evidence supports correct ownership preservation in the observed run but does not prove collision avoidance, path separation, or safe physical spacing.

## 16. Nonblocking Warnings And Limitations

Fourteen warning lines represented familiar startup categories: SimulationApp import-order advice, no crash reporter, missing optional rendering-mode configuration, MaterialX advice, inaccessible OmniHub, deprecated dynamic control, duplicate unsupported-Intel-GPU notices, Gym maintenance advice, and fixed-N checkpoint warnings. None blocked construction, playback, artifact finalization, shutdown, or exit 0.

Remaining limits:

- One deterministic 300-decision playback is not a performance evaluation.
- The run exercised no exact-claim conflict or resolver rejection branch.
- Incidental coverage remains deliberately unassigned.
- Done-step physical values remain null without a pre-reset capture.
- Base stationarity does not imply that every scanner/arm/controller component was stationary.
- No visual claim is made because playback was headless and no video was recorded.

## 17. Files And Boundary Confirmation

Created by runtime:

```text
results/.../assignment_happo_n50_phase9g8h2_bounded_proposal_effective_playback/
seed-00001/assignment_proposal_effective_rows.csv
seed-00001/assignment_proposal_effective_summary.json
seed-00001/assignment_target_segments.csv
```

Created as documentation:

```text
AgentRead/20260720/
PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md
TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8H2_BOUNDED_ATTRIBUTION_PLAYBACK_20260720.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

Explicitly not modified by Phase 9G-8H-2:

```text
production Python
tests
YAML/runtime configuration
resolver or Contract C
observations, masks, or rewards
controller or environment behavior
checkpoint behavior
installed HARL or Conda environment
```

The frozen command ran exactly once. There was no retry, second playback, training, evaluation, continuation, critic/ValueNorm restore, GUI, visual inspection, video recording, or commit.

## 18. Next Recommendation

Review the uncommitted Phase 9G-8H-0 through 9G-8H-2 implementation and runtime evidence. The runtime result exposes no diagnostic defect requiring a repair phase. Any commit decision remains with GPT/user review; this phase does not commit or authorize broader playback, evaluation, continuation, or training.
