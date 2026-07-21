# Phase 9G-8I-2-1: Sequential Best/Final Bounded Attribution Playback Execution And Comparison

## 1. Classification

~~~text
BEST-FINAL-ATTRIBUTION-COMPARISON-COMPLETE
~~~

The two frozen deterministic playbacks ran exactly once and sequentially. The
`best_model` run passed every technical check before the `final models` run was
started. Both runs exited normally, produced the exact three-artifact attribution
contract, and passed row, resolver, controller, segment, reset, and finite-value
validation.

Behavioral outcome:

~~~text
Mixed Outcome A1 + Outcome A3

A1:
  Deterministic participation improved materially from the one-update baseline.

A3:
  best_model is healthier than final models on completion distribution,
  budget-release burden, coverage, and robot_1/robot_2 motion-progress quality.

Final also has Outcome-B-like completion concentration, but it does not exhibit
a renewed deterministic noop/idle collapse.
~~~

Checkpoint decision:

~~~text
prefer best_model
~~~

This is a bounded one-seed attribution decision, not a statistical performance or
convergence claim.

## 2. Starting State And Preflight

| Check | Result |
| --- | --- |
| Starting HEAD | `0e610f9edc403a51a285777b672b3ea996681542` |
| Starting commit | `0e610f9e feat(assignment): add offline training run audit tool` |
| Worktree | Only the accepted Phase 9G-8I-1/9G-8I-2-0 documentation chain and `TASK_PROGRESS.md` were modified/untracked |
| Production/test/YAML changes | None |
| `git diff --check` before execution | PASS; line-ending warning only |
| Relevant running process | None before best; none before final |
| GPU | NVIDIA GeForce RTX 4060 Ti, 8188 MiB total, 1022 MiB used, 6940 MiB free, 3% utilization |
| Checkpoint metadata | Both checkpoint children passed contract, completion-marker, inventory, size, and SHA-256 checks as opaque bytes |
| Tensor deserialization during preflight | None |
| Output/log collisions | All four frozen output/log paths were absent immediately before use |

No unknown process was terminated. The final run was not launched until the best
run and its complete artifact validation had passed.

## 3. Checkpoint Identities

Training run root:

~~~text
E:\Project\IsaacLab_HARL\results\isaaclab\
Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\
assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\
seed-00001-2026-07-20-17-40-33
~~~

| Field | Best | Final |
| --- | --- | --- |
| Child | `best_model` | `models` |
| Checkpoint kind | `best` | `final` |
| Generation | 10 | 22 |
| Contract | `assignment_checkpoint_contract_v2` | `assignment_checkpoint_contract_v2` |
| Profile | `lifecycle_contract_c` | `lifecycle_contract_c` |
| Algorithm | HAPPO | HAPPO |
| M / N | 3 / 50 | 3 / 50 |
| Actor/shared/action dimensions | 1059 / 3183 / 51 | 1059 / 3183 / 51 |
| Sequence/share mode | feed-forward / `share_param=false` | feed-forward / `share_param=false` |
| Ordered actors | `robot_0`, `robot_1`, `robot_2` | `robot_0`, `robot_1`, `robot_2` |
| Fingerprint | `19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6` | same |
| Load purpose | `normal_evaluation` | `normal_evaluation` |
| Restore boundary | actor-only; no critic or ValueNorm restore | actor-only; no critic or ValueNorm restore |
| Legacy fallback | `False` | `False` |

## 4. Frozen Command Identity And Run Records

Both commands were the unchanged PowerShell blocks from Sections 12 and 13 of
`PHASE9G8I20_BEST_VS_FINAL_PROPOSAL_EFFECTIVE_ATTRIBUTION_COMPARISON_DESIGN.md`.
They used the repository `play_assignment.py`, the pinned Conda environment,
HAPPO, one environment, seed 1, 300 decisions, headless CUDA, deterministic
masked `Categorical.mode()`, `lifecycle_contract_c`, feed-forward actors,
`share_param=false`, diagnostic interval 1, and the existing attribution
collector. Per-row console printing remained disabled.

| Field | Best | Final |
| --- | --- | --- |
| Checkpoint | `...\best_model` | `...\models` |
| Start | `2026-07-20T23:53:20.6368140+08:00` | `2026-07-20T23:58:33.0608067+08:00` |
| End | `2026-07-20T23:56:48.6482359+08:00` | `2026-07-21T00:02:06.1221039+08:00` |
| Elapsed | 208.011 s | 213.061 s |
| Process exit | 0 | 0 |
| Loader evidence | `kind=best generation=10 purpose=normal_evaluation legacy_fallback=False` | `kind=final generation=22 purpose=normal_evaluation legacy_fallback=False` |
| Completion evidence | `completed steps=300, max_steps=300` | `completed steps=300, max_steps=300` |

Console logs:

~~~text
best:
  C:\Users\33506\AppData\Local\Temp\
  phase9g8i21_best_attribution_console_20260720.log

final:
  C:\Users\33506\AppData\Local\Temp\
  phase9g8i21_final_attribution_console_20260720.log
~~~

Output directories:

~~~text
best:
  E:\Project\IsaacLab_HARL\results\isaaclab\
  Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\
  assignment_happo_n50_phase9g8i21_best_100k_proposal_effective_attribution\
  seed-00001

final:
  E:\Project\IsaacLab_HARL\results\isaaclab\
  Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\
  assignment_happo_n50_phase9g8i21_final_100k_proposal_effective_attribution\
  seed-00001
~~~

## 5. Technical Validation

Both outputs contain exactly these files and no extras:

| Artifact | Best bytes | Final bytes |
| --- | ---: | ---: |
| `assignment_proposal_effective_rows.csv` | 832226 | 824623 |
| `assignment_proposal_effective_summary.json` | 26290 | 25792 |
| `assignment_target_segments.csv` | 7641 | 8352 |

| Validation | Best | Final |
| --- | --- | --- |
| Schema `phase9g8h1_assignment_proposal_effective_attribution_v1` | PASS | PASS |
| Robot rows / unique environment decisions | 900 / 300 | 900 / 300 |
| Exactly robots 0, 1, 2 per decision | PASS | PASS |
| Duplicate row keys | 0 | 0 |
| Summary row count | 900 | 900 |
| `invariant_failures` | empty | empty |
| Resolver enabled throughout | PASS | PASS |
| Raw action decoding | exact | exact |
| Proposal/effective changed field | exact | exact |
| Controller equals effective assignment | PASS | PASS |
| Selected probabilities finite and in `[0,1]` | PASS | PASS |
| Unclassified primary attribution rows | 0 | 0 |
| Duplicate effective targets per decision | 0 | 0 |
| Nonfinite non-null physical values | 0 | 0 |
| Valid post-state rows | 897 | 897 |
| Done decisions / reset rows | 1 / 3 | 1 / 3 |
| Episode increment and decision restart | PASS | PASS |
| Segment continuity/duration | PASS | PASS |
| Attempts / segments | 27 / 27 | 30 / 30 |
| `invariant_break` releases | 0 | 0 |
| Traceback/exception/shutdown-failure log matches | 0 | 0 |
| Normal application close and no residual process | PASS | PASS |

The done decision has three deliberately unavailable post-state rows, one per
robot. Null post-reset physical values were not treated as nonfinite failures.

## 6. Full-Horizon Per-Agent Metrics

All counts below are recomputed from each 900-row CSV. Streaks break at episode
reset. The final decision starts episode 1, so full-horizon starts/segments include
one new truncated segment per robot after reset.

| Metric | Best r0 | Best r1 | Best r2 | Final r0 | Final r1 | Final r2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw proposal noop | 0 | 0 | 0 | 0 | 0 | 0 |
| Raw proposal target | 300 | 300 | 300 | 300 | 300 | 300 |
| Effective idle | 0 | 0 | 0 | 0 | 0 | 0 |
| Effective executing | 300 | 300 | 300 | 300 | 300 | 300 |
| Proposal/effective changed | 0 | 0 | 0 | 0 | 0 | 0 |
| Attempt started | 9 | 10 | 8 | 14 | 10 | 6 |
| Continued same target | 291 | 290 | 292 | 286 | 290 | 294 |
| Contract-C noop continuation | 0 | 0 | 0 | 0 | 0 | 0 |
| Target completed | 6 | 8 | 6 | 12 | 5 | 3 |
| Budget failure | 1 | 0 | 0 | 0 | 3 | 1 |
| Release budget failure | 1 | 0 | 0 | 0 | 3 | 1 |
| Reset event | 1 | 1 | 1 | 1 | 1 | 1 |
| Resolver rejection, all canonical reasons | 0 | 0 | 0 | 0 | 0 | 0 |
| Exact claim-conflict win / loss | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Target segments | 9 | 10 | 8 | 14 | 10 | 6 |
| Longest executing segment | 71 | 55 | 70 | 64 | 68 | 101 |
| Longest effective-idle streak | 0 | 0 | 0 | 0 | 0 | 0 |
| Longest raw-noop streak | 0 | 0 | 0 | 0 | 0 | 0 |
| Longest identical real-target proposal streak | 71 | 55 | 70 | 64 | 68 | 101 |
| Valid post-state rows | 299 | 299 | 299 | 299 | 299 | 299 |
| Translational base-motion rows | 236 | 292 | 269 | 256 | 223 | 217 |
| Zero-command rows | 0 | 0 | 0 | 0 | 0 | 0 |
| Zero-base-motion while executing | 63 | 7 | 30 | 43 | 76 | 82 |
| Zero target-distance progress | 31 | 0 | 0 | 11 | 63 | 55 |

Release types reconcile exactly with the segment files. Best has 20 completed,
one budget-failure, three reset, and three playback-truncated segment releases.
Final has 20 completed, four budget-failure, three reset, and three
playback-truncated releases.

## 7. Team Metrics And First-Episode Coverage

| Metric | Best | Final |
| --- | ---: | ---: |
| Executing-step vector | `[300,300,300]` | `[300,300,300]` |
| Idle-step vector | `[0,0,0]` | `[0,0,0]` |
| Completion vector | `[6,8,6]` | `[12,5,3]` |
| Total starts | 27 | 30 |
| Total completions | 20 | 20 |
| Budget failures / releases | 1 / 1 | 4 / 4 |
| Resolver rejections | 0 | 0 |
| Contract-C continuations | 0 | 0 |
| Mean active robots | 3.0 | 3.0 |
| Steps with 3 / 2 / 1 / 0 active | `300 / 0 / 0 / 0` | `300 / 0 / 0 / 0` |
| Jain executing fairness | 1.0 | 1.0 |
| Jain completion fairness | 0.9803921569 | 0.7490636704 |

Coverage was derived for completed episode 0 by taking unique target ids from
projected `target_completed` resolver events, adding unprojected environment
completion events, and deduplicating by episode/environment/target.

| Coverage evidence | Best | Final |
| --- | ---: | ---: |
| Assigned target completions | 20 | 20 |
| Unprojected unique environment completions | 15 | 14 |
| Deduplicated unique completed targets | 35 | 34 |
| Event-derived coverage | `35/50 = 0.70` | `34/50 = 0.68` |
| Last finite pre-reset `coverage_ratio` | 0.6999999881 | 0.6800000072 |
| Agreement | PASS | PASS |

The step-300 rows belong to the reset episode and show coverage zero; they were
not substituted for the last finite pre-reset coverage.

## 8. Frozen Three-Way Comparison

| Metric | One-update baseline | 100k best_model | 100k final models | Preferred direction | Interpretation |
| --- | ---: | ---: | ---: | --- | --- |
| robot_0 proposal noop | 300 | 0 | 0 | materially lower | Full deterministic noop collapse removed in both |
| robot_1 proposal noop | 0 | 0 | 0 | contextual | All three policies propose targets directly |
| robot_2 proposal noop | 248 | 0 | 0 | lower idle-noop burden | Prior asymmetry removed in both |
| robot_0 executing steps | 0 | 300 | 300 | useful increase | Nontrivial accepted segments and completions |
| robot_1 executing steps | 300 | 300 | 300 | maintain useful work | Maintained |
| robot_2 executing steps | 61 | 300 | 300 | useful increase | Full participation; final progress is weaker |
| robot_0 longest idle streak | 299 | 0 | 0 | materially lower | Collapse removed |
| robot_1 longest idle streak | 0 | 0 | 0 | low | No idle burden |
| robot_2 longest idle streak | 153 | 0 | 0 | materially lower | Primary baseline asymmetry removed |
| robot_0 longest raw-noop streak | 299 | 0 | 0 | materially lower | Collapse removed at proposal source |
| robot_1 longest raw-noop streak | 0 | 0 | 0 | contextual | No noop sampling |
| robot_2 longest raw-noop streak | 162 | 0 | 0 | materially lower | No Contract-C masking of an idle-noop problem |
| robot_0 completions | 0 | 6 | 12 | nonzero and useful | Both improve; final concentrates work on r0 |
| robot_1 completions | 5 | 8 | 5 | contextual | Best improves; final returns to baseline count |
| robot_2 completions | 2 | 6 | 3 | maintain/improve | Both improve; best is stronger |
| Total completions | 7 | 20 | 20 | higher | Both materially improve |
| First-episode coverage | 0.36 | 0.70 | 0.68 | higher | Best is slightly stronger |
| Budget releases | 2 | 1 | 4 | lower when completion holds | Best improves; final doubles baseline burden |
| Contract-C continuations | 9 | 0 | 0 | contextual | Noops no longer account for execution |
| Resolver rejections | 0 | 0 | 0 | zero or rare | Resolver is not the limiting mechanism |
| Jain executing fairness | 0.4635069337 | 1.0 | 1.0 | higher diagnostically | Both keep all three active |
| Jain completion fairness | 0.5632183908 | 0.9803921569 | 0.7490636704 | higher diagnostically | Best is balanced; final is concentrated |
| Mean active robots | 1.2033333333 | 3.0 | 3.0 | useful parallelism | Motion/segments confirm real execution |
| All-three-active steps | 0 | 300 | 300 | increase when useful | Full horizon in both |
| Two-active steps | 61 | 0 | 0 | contextual | Shifted to all-three active |
| One-active steps | 239 | 0 | 0 | lower concentration | Shifted to all-three active |
| Zero-active steps | 0 | 0 | 0 | avoid | None |

The accepted baseline totals were also checked against its authoritative 900-row
artifact. No contradiction was found, so the frozen baseline was not altered.

## 9. Compact Per-Agent Comparison

Each cell is `[robot_0, robot_1, robot_2]`.

| Metric | One-update baseline | Best | Final |
| --- | --- | --- | --- |
| Proposal target | `[0,300,52]` | `[300,300,300]` | `[300,300,300]` |
| Attempt starts | `[0,8,4]` | `[9,10,8]` | `[14,10,6]` |
| Segment count | `[0,8,4]` | `[9,10,8]` | `[14,10,6]` |
| Longest executing segment | `[0,61,46]` | `[71,55,70]` | `[64,68,101]` |
| Translational base-motion rows | `[0,259,36]` | `[236,292,269]` | `[256,223,217]` |
| Zero-base-motion while executing | `[0,40,25]` | `[63,7,30]` | `[43,76,82]` |

Rotational-motion steps, separate linear/angular command components, and arm or
joint-motion attribution are unsupported by the current schema and were not
inferred.

## 10. Per-Robot Behavioral Assessment

### Robot 0

Best and final classification:

~~~text
useful deterministic participation
~~~

Robot 0 moved from 300 raw noops, zero starts, zero execution, and zero
completions to 300 target proposals and 300 executing rows in both runs. Best has
9 segments and 6 completions; final has 14 segments and 12 completions. There are
no rejected/unavailable proposals or idle streaks. Best has 31 zero-progress rows
and one budget release, while final has 11 and zero, so robot 0 itself improves in
the final checkpoint. Neither run supports noop, narrow-target, or
execution-without-progress collapse for this robot.

### Robot 1

Best classification:

~~~text
useful deterministic participation
~~~

Final classification:

~~~text
useful deterministic participation with degraded completion efficiency and
execution-progress quality
~~~

Robot 1 remains active for all 300 decisions and uses 9 real targets in each
run. Best yields 8 completions, no budget releases, 292 motion rows, and no
zero-progress rows. Final yields 5 completions, 3 budget releases, 223 motion
rows, 76 zero-motion executing rows, and 63 zero-progress rows. It does not carry
the workload because peers are idle; all three are active. The regression is in
completion efficiency/progress, not resolver rejection or unstable switching.

### Robot 2

Best classification:

~~~text
useful deterministic participation
~~~

Final classification:

~~~text
narrow but useful specialization with an execution-without-progress concern
~~~

Robot 2 moves from 248 baseline noops and a 153-step idle streak to 300 target
proposals and 300 execution rows in both 100k runs. Best has 8 segments, 6
completions, no budget release, and 269 motion rows. Final narrows to 6 segments,
3 completions, one budget release, a 101-step repeated-target/segment streak, 82
zero-motion executing rows, and 55 zero-progress rows. This is not noop collapse
or a budget-release loop, but it is a bounded final-checkpoint progress concern.

## 11. Resolver, Budget, Motion, And Load Interpretation

Resolver attribution is clean: both checkpoints have zero proposal rejection,
zero exact-target conflict win/loss, zero duplicate effective target, zero
proposal/effective change, and zero controller/effective mismatch. The comparison
does not reopen resolver, Contract C, ownership, arbitration, or mask design.

Budget failure does not dominate either run: both still complete 20 targets and
reach at least 0.68 event-derived coverage. It does distinguish the checkpoints.
Best has one release, on robot 0. Final has four: three on robot 1 and one on
robot 2.

All applicable controller commands are nonzero in both runs. Base XY motion and
distance-progress evidence nevertheless show a final-checkpoint shift away from
robots 1 and 2: their combined zero-motion executing rows rise from 37 to 158,
and combined zero-progress rows rise from 0 to 118. This is physical attribution,
not proof of full robot stationarity, because rotation and arm/joint motion are
not present in the schema.

Execution load is perfectly even in both runs (`[300,300,300]`). Completion load
is nearly even for best (`[6,8,6]`) and concentrated toward robot 0 for final
(`[12,5,3]`). Jain completion fairness is diagnostic only; capability and path
cost can legitimately produce unequal work. Here it aligns with higher final
budget pressure and weaker robot 1/2 progress, so it is meaningful supporting
evidence rather than the sole selection rule.

## 12. Outcome And Checkpoint Preference

The primary one-update artifact is resolved in deterministic playback:

~~~text
Outcome A1: deterministic participation improvement
~~~

All robots select real targets, execute throughout, create multiple valid
segments, and complete tasks. Neither 100k checkpoint retains the baseline
robot-0 noop collapse or robot-2 long idle-noop pattern.

The best/final comparison adds:

~~~text
Outcome A3: best healthy, final regressed
~~~

Final is not technically broken and robot 0 improves, but it does not improve
team completions over best. It has lower coverage (0.68 versus 0.70), four times
the budget releases, substantially less balanced completions, and weaker
robot-1/robot-2 motion-progress evidence. This also gives final an Outcome-B-like
completion concentration. Outcomes C and D are not supported.

Following the frozen decision order, the selected checkpoint is:

~~~text
prefer best_model
~~~

Both have equal technical integrity, complete participation, no noop/idle
collapse, and 20 completions. Best then wins on coverage, budget burden,
completion distribution, and cross-robot segment/motion stability. Generation or
training recency was not used as a preference signal.

## 13. Remaining Limitations

- One deterministic 300-decision trajectory and one seed do not establish expected performance or generalization.
- Playback used deterministic masked `Categorical.mode()`; it does not characterize sampled training behavior.
- The exact training update at which `best_model` was retained is not established by these playback artifacts.
- Coverage and completion attribution is event-based; incidental completion has no reliable per-robot source.
- Base-motion attribution covers translational XY displacement only. Rotation, arm motion, and joint progress are unsupported.
- Jain diagnostics are not optimizer objectives and do not prove that unequal completion is avoidable.
- No GUI/video inspection, stochastic evaluation, second seed, checkpoint continuation, or 300k training was performed.

## 14. Files And Non-Actions

Created documentation:

~~~text
AgentRead/20260720/
PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md

AgentRead/20260720/
TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I21_BEST_FINAL_ATTRIBUTION_EXECUTION_20260720.md
~~~

Updated:

~~~text
AgentRead/TASK_PROGRESS.md
~~~

Runtime artifacts are referenced only at the exact output paths above. They were
not copied into `AgentRead`.

Explicit boundary:

~~~text
No production source behavior was modified.
No test or YAML file was modified.
No command argument or runtime configuration was changed.
Neither playback was retried or run concurrently.
No training, checkpoint continuation, stochastic evaluation, or second seed ran.
No GUI or video operation ran.
No 300k continuation ran.
No installed HARL or Conda file was modified.
No commit was made.
~~~

Final documentation validation:

~~~text
git diff --check:
  PASS (line-ending warning only)

git status --short --untracked-files=all:
  only the accepted Phase 9G-8I-1/9G-8I-2-0 documentation chain,
  this Phase 9G-8I-2-1 report/archive, and TASK_PROGRESS.md

new-document trailing whitespace:
  0

new-document final newline:
  present

active assignment process after final:
  none
~~~

## 15. Next-Phase Recommendation

Recommend one bounded reviewed step only:

~~~text
Phase 9G-8I-3-0:
Late-Training Policy-Drift Diagnosis Design Using best_model As Candidate
~~~

That recommendation is motivated by the A3 evidence. This phase does not start
it and does not authorize 300k continuation, reward/resolver modification, a
second seed, GUI/video, or broader evaluation before review.
