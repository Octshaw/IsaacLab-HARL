# Phase B2-T3 Task-Progress and Horizon Qualification Report

Date: 2026-09-12

Classification:
`PHASE-B2-T3-TASK-PROGRESS-HORIZON-QUALIFIED-AWAITING-GPT-REVIEW`

## A. repository authority

The closing repository snapshot is:

```text
branch: main
HEAD: b71d85a32f51be6ada324f870813a56bb45dd396
origin/main: b71d85a32f51be6ada324f870813a56bb45dd396
merge-base: b71d85a32f51be6ada324f870813a56bb45dd396
HEAD == origin/main == merge-base: true
working-tree porcelain lines before final documentation update: 402
staged paths: 359
staged-index SHA-256: a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c
monthly-migration path-set SHA-256: 0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab
```

No `git add`, commit, push, reset, checkout, or clean operation occurred. The
pre-existing 359-path staged monthly migration was preserved byte-for-byte in
the index.

## B. starting reviewed authority

The user-supplied starting authority is accepted exactly: B2-R0 through B2-R7,
B2-T0-LD, B2-T0-RE1, B2-T0, B2-T1, and B2-T2 are `GPT REVIEW PASS / CLOSED`.
Training-update readiness, lifecycle decision gating, repeated-update
continuity, persistent learner continuity, bounded short-training stability,
medium-length training stability, and training observability are established.
Task progress and real completion were not established at entry. Long training
and B2-R6 were not authorized; checkpoint continuation remains not established;
the public learned-policy route remains `DORMANT / BLOCKED`.

## C. T2 zero-progress observation

B2-T2 ran 300 learner updates and 600 physical steps, but observed coverage 0,
completed viewpoints 0, `TASK_COMPLETED` 0, `TASK_RELEASED` 0, and failure events
0 while roughly 5–6 tasks remained claimed/executing. B2-T3 does not reinterpret
that run as performance evidence. It isolates the horizon authority and obtains
a separate controlled normal-horizon completion witness.

## D. source identities

The B2-T3 sources are:

| Source | SHA-256 |
|---|---|
| `_assignment_phase_b2_t3_progress_observer.py` | `c8edd97c1327c0d2f2084725449edd916e8b6190bbee3eab3ac04a1dc31cbf59` |
| `test_assignment_phase_b2_t3_task_progress_horizon_qualification.py` | `14030c790bf24c8b4dda41ed3c4b0b7c6e72bacc6b144145653f63aa66b71ce7` |
| `scan_mobile_manipulator_env.py` | `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363` |
| `assignment_harl_wrapper.py` | `f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae` |
| `assignment_event_actor_collection.py` | `3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45` |
| `assignment_event_learned_route.py` | `b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b` |
| `assignment_event_profile_schema_contract_v2.py` | `9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955` |

The T2 static guard reconfirmed the reviewed production and installed-source
identities, including HAPPO `dd44fe78...5cf96`, VCritic
`ae663907...08bf3`, VNet `a3760b3f...427c3`, and ValueNorm
`a35471b1...f8b0`.

## E. files created/modified

Created:

- `scripts/environments/_assignment_phase_b2_t3_progress_observer.py`;
- `scripts/environments/test_assignment_phase_b2_t3_task_progress_horizon_qualification.py`;
- `AgentRead/202609/20260912/b2_t3_artifacts/` bounded JSON artifacts;
- this report;
- `TASK_PROGRESS_ARCHIVE_BEFORE_B2_T3_HANDOFF_20260912.md`.

Modified after the byte-exact archive: `AgentRead/TASK_PROGRESS.md`. No
production or installed HARL source was modified.

## F. T2 timeout authority trace

The inherited T0/T2 harness sets `resolved_T = 2`, builds the V2
`PD2_SEMANTIC_HORIZON_STEPS = 3` fixture, and assigns the fixture's `0.3` seconds
to `cfg.episode_length_s`. With simulation `dt = 1/60` and decimation 6, one
physical control step is 0.1 seconds and the instantiated
`raw.max_episode_length` is 3. The environment timeout predicate is
`episode_length_buf >= max_episode_length - 1`, so TIME_LIMIT/autoreset is
observed on the second physical transition.

## G. rollout T definition

`T = 2` is the learner rollout storage/update collection length. It controls the
number of environment transitions collected per learner transaction and the
rollout-buffer cursor. It is not the environment's production episode limit.

## H. episode/time-limit definition

The environment episode limit is derived from `episode_length_s / step_dt`.
For T2's harness-only fixture it is 0.3 seconds / 0.1 seconds = 3 configured
steps, with timeout at the transition where the pre-reset episode buffer reaches
`3 - 1`. For the production task configuration it is 30 seconds / 0.1 seconds =
300 configured steps.

## I. event-gated/runtime budget definition

Lifecycle decision authority is row-local. `NEEDS_ASSIGNMENT` opens policy
selection; a legal claim moves the robot/task into `EXECUTING`/`CLAIMED`;
subsequent rows are forced continuations with no target-robot resampling until a
terminal lifecycle event reopens the decision. This budget is independent of
both rollout T and episode length. In the controlled witness, one claim required
21 continuation boundaries before completion.

## J. normal execution horizon

The source-authoritative environment default is `episode_length_s = 30.0`,
simulation `dt = 1/60`, decimation 6, step time 0.1 seconds, and
`max_episode_length = 300`. The HARL YAML `train.episode_length = 1000` is a
third, learner-side training configuration and does not override the task's
environment time-limit in this witness. T3-B used the environment default with
no harness episode override.

## K. horizon classification

`HORIZON-A`: T2 used an intentionally ultra-short test-only qualification
horizon. Its zero-completion/zero-coverage observation is therefore classified
as `SHORT-HORIZON QUALIFICATION ARTIFACT`. It remains a valid learner stability
result, not a normal task-progress trial.

## L. task-completion contract trace

`_compute_scan_candidate()` evaluates scanner position/orientation tolerance,
arm reach, sensor min/max range, and field of view. `_stage_event_scan_progress()`
combines the candidate with `dwell_steps = 1` and stages facts without directly
mutating coverage/rewards. The environment-owned lifecycle authority finalizes
the transition. A genuine completion produces `task_completed`, maps the P2
task to `COMPLETED`, clears ownership to `-1`, moves the robot to
`NEEDS_ASSIGNMENT`, emits `robot_needs_assignment`, increments the robot's
completion count, and updates coverage from completed tasks.

The production source has no separate named `NAVIGATING` or `ALIGNING` task
state, named arrival flag, no-progress counter, or per-task elapsed counter.
Progress is therefore reported from the existing lifecycle state, physical
positions/distance, scan candidate/dwell, events, completion count, and coverage;
no unavailable phase is invented.

## M. task-progress observability

The 17-signal observer schema records episode generation/progress, global step,
boundary/decision status, proposal/effective assignment, robot/task state,
ownership, base/scanner/target positions, distance, candidate/dwell, events,
terminal reason, completed/covered counts, coverage ratio, robot completion
count, and policy-call count. The schema artifact and pure qualification are
durable under `b2_t3_artifacts/` and the observer source.

## N. observer nonmutation

The observer hashes its authoritative source projection immediately before and
after every capture. All 24 T3-B rows had identical before/after digests and
`observer_mutation_count = 0`. The standalone pure qualification also passed.

## O. controlled proposal mechanism

At the initial decision boundary, the harness enumerated canonical legal and
feasible pairs and deterministically selected the minimum current geometric-cost
pair whose initial distance exceeded scan tolerance plus one controller scanner
increment. It proposed that action only where policy was required. The normal
production controller, wrapper, P2 resolver, lifecycle authority, completion
predicate, and coverage path remained unchanged.

## P. selected robot-task pair

Robot 0 / task 0 was selected. It was available and feasible. Initial scanner
distance was `1.6770509481430054`; position tolerance was
`0.18000000715255737`; maximum scanner XYZ increment was
`0.07000000029802322`. Thus completion could not occur in the claim transition
or one controller step.

## Q. T3-B exact runtime config

```text
fresh process PID: 15184
E/M/N: 1/3/12
device: cuda:0
profile: event_gated_local_mrta
episode_length_s: 30.0
max_episode_length: 300
sim dt / control step: 1/60 s / 0.1 s
AppLauncher lifetimes: 1
environment constructions: 1
learner constructed: false
checkpoint I/O: 0
public activation: 0
```

## R. T3-B lifecycle/progress trajectory

The target row progressed from policy-required unowned/available at step 0, to
claimed/executing at step 1, through 21 forced continuations, to completion at
step 22. Step 23 proved the post-completion decision gate reopened. Distance
decreased monotonically at the sampled milestones from 1.67705 to 0.11000; total
scanner displacement was 1.5689481496810913.

## S. claim evidence

The legal claim occurred at physical step 1, store version 2. Robot state became
`EXECUTING`, task state became `CLAIMED`, owner became robot 0, and effective
assignment became task 0. Claim and completion were distinct transitions.

## T. continuation evidence

Steps 2 through 22 contain 21 genuine forced-continuation target rows. Each had
`decision_required = false`, retained effective assignment 0, and target robot
policy-call count 0. No continuation-resample fault occurred. Other robots were
still legitimately evaluated at their own decision boundaries.

## U. physical/controller progress evidence

Target distance decreased from 1.6770509481 before claim to 1.5966528654 at
step 1, 1.5184532404 at step 2, 0.9500006437 at step 10,
0.2500005960 at step 20, 0.1800005436 at step 21, and
0.1100004911 at step 22. Runtime state stayed finite. This is direct physical
progress through the unmodified controller, not a synthetic completion flip.

## V. completion evidence

At step 22 the authoritative candidate became true, dwell reached 1, exactly one
`task_completed` event was emitted for robot 0/task 0, and robot completion count
increased from 0 to 1. There were no release or failure events.

## W. P2 completed-state evidence

On the same transition, task 0's P2 state became numeric state 4,
`COMPLETED`. The lifecycle result and published row agreed; no stale terminal
evidence or post-reset reconstruction was used.

## X. coverage transition evidence

Covered-viewpoint count changed 0 -> 1, coverage ratio changed 0 -> 1/12
(`0.0833333358168602`), and completed-task count changed 0 -> 1. All three
changes coincide with the single genuine completion.

## Y. ownership transition evidence

Ownership was `-1` before claim, robot 0 while task 0 was claimed/executing, and
`-1` after completion. The robot became `NEEDS_ASSIGNMENT`; step 23 showed one
new target-row policy call with effective assignment `-1`. Ownership and
decision reopening are consistent.

## Z. timeout/autoreset evidence

Completion occurred at step 22, far before the normal 300-step configured
horizon. Timeout boundaries, autoreset boundaries, and terminal reasons before
completion were all 0. No timeout invalidated the witness.

## AA. T3-C frozen-policy witness if executed

T3-C was attempted only after T3-B passed, but no attempt formed an accepted
frozen-policy episode. Five fresh processes were started, all with zero physical
steps and zero learner mutation:

| Attempt | PID | Stop boundary | Result |
|---:|---:|---|---|
| 1 | 14432 | first VCritic forward | `CUBLAS_STATUS_NOT_INITIALIZED` |
| 2 | 8100 | first VCritic forward; intended seed-order fix had not actually been applied | same |
| 3 | 12592 | first HAPPO actor forward in critic-free slice | same |
| 4 | 6412 | first HAPPO actor forward; warm-up was on the inactive helper | same |
| 5 | 14760 | explicit CUBLAS probe before environment construction | same |

The fifth probe establishes that this local Isaac/CUDA process cannot create a
CUBLAS handle even before the environment and actor are constructed. Attempts
1–4 constructed four environments; attempt 5 did not. The repeated corrections
were test-harness-only and never crossed the first physical-step or mutation
boundary. The exact excess-attempt history is retained rather than represented
as the requested idealized `0 or 1` worker count.

## AB. T3-C interpretation

T3-C is `NOT EXECUTED AS AN ACCEPTED WITNESS — INFRASTRUCTURE BLOCKED`. It is
neither C1 nor C2 because actor inference did not complete, and it is not C3
because no lifecycle/runtime contract was reached or contradicted. This does not
establish frozen-actor performance or runtime validity. T3-C is supplementary;
the controlled T3-B result is the required execution/completion capability
witness and independently establishes the T2 horizon root cause.

## AC. horizon comparison table

| Property | T2 qualification profile | Normal execution profile |
|---|---:|---:|
| rollout T | 2 | not changed or used as episode authority |
| episode/time-limit horizon | 0.3 s / configured max 3 | 30.0 s / configured max 300 |
| source of horizon | V2/T0 harness-only integral fixture | task config default |
| physical steps before timeout | timeout on transition 2 | timeout predicate near transition 299 |
| task continuation possible >2 steps? | no | yes |
| completion observed? | no | yes, step 22 |
| coverage >0? | no | yes, 1/12 |

## AD. completion-witness table

States: robot `0=EXECUTING`, `1=NEEDS_ASSIGNMENT`; task `0=AVAILABLE`,
`1=CLAIMED`, `4=COMPLETED`.

| Step | Episode gen | Robot | Task | Robot state | Task state | Decision? | Effective assignment | Progress signal | Event | Completed count | Coverage |
|---:|---:|---:|---:|---|---|---|---:|---|---|---:|---:|
| 0 | 0 | 0 | 0 | NEEDS_ASSIGNMENT | AVAILABLE | yes | — | distance 1.677051; pre-claim | — | 0 | 0/12 |
| 1 | 0 | 0 | 0 | EXECUTING | CLAIMED | yes | 0 | claim; distance 1.596653 | — | 0 | 0/12 |
| 2 | 0 | 0 | 0 | EXECUTING | CLAIMED | no | 0 | continuation; distance 1.518453 | — | 0 | 0/12 |
| 10 | 0 | 0 | 0 | EXECUTING | CLAIMED | no | 0 | continuation; distance 0.950001 | — | 0 | 0/12 |
| 20 | 0 | 0 | 0 | EXECUTING | CLAIMED | no | 0 | continuation; distance 0.250001 | — | 0 | 0/12 |
| 21 | 0 | 0 | 0 | EXECUTING | CLAIMED | no | 0 | continuation; distance 0.180001 | — | 0 | 0/12 |
| 22 | 0 | 0 | 0 | NEEDS_ASSIGNMENT | COMPLETED | no | 0 | candidate true; dwell 1; distance 0.110000 | `task_completed`; `robot_needs_assignment` | 1 | 1/12 |
| 23 | 0 | 0 | 0 | NEEDS_ASSIGNMENT | COMPLETED | yes | -1 | decision reopened; one policy call | — | 1 | 1/12 |

Intermediate continuation is not elided from the durable 24-row trajectory;
the table samples milestones while the JSON contains every step 2–22 row.

## AE. root-cause classification

Primary outcome: **OUTCOME A — SHORT-HORIZON QUALIFICATION ARTIFACT**.

The same unmodified completion/controller/lifecycle path completed a genuinely
claimed task in 22 transitions under the source-authoritative normal horizon,
whereas T2 forcibly timed out/autoreset on its second transition. There is no
source evidence of a controller, progress, lifecycle, or coverage defect in the
qualified slice.

## AF. production semantic modification count

Production semantic modifications: **0**. Reward, lifecycle, controller,
completion, coverage, environment timing defaults, public routing, and installed
HARL were not changed.

## AG. learner mutation count

```text
actor backward: 0
actor optimizer.step: 0
critic backward: 0
critic optimizer.step: 0
ValueNorm.update: 0
event learner transactions: 0
checkpoint weight I/O: 0
```

No learner was constructed in T3-B. The failed T3-C processes stopped before a
physical step and before any mutation.

## AH. static/private/public guards

`py_compile` passed for both B2-T3 sources. The B2-T0-LD pure qualification
passed 13/13 with mutation count 0. The T2 observer pure qualification passed
with mutation count 0. The T2 static-only source/config guard passed and
reconfirmed reviewed production/installed identities and dormant public-route
guards. The new T3 progress-observer pure qualification passed. Only private
test routes were used; public activation count is 0.

## AI. exact execution counts

```text
formal source/static horizon audits: 1
formal real T3-B workers: 1
T3-C worker attempts: 5
successful / accepted T3-C workers: 0 / 0
AppLauncher lifetimes: 6
environment constructions: 5
normal-horizon environment initializations: 5
accepted normal-horizon trajectories: 1
physical environment steps across all workers: 23
policy decision boundaries in accepted T3-B witness: 23
continuation boundaries in accepted T3-B witness: 21
target policy calls during continuation: 0
TASK_COMPLETED events: 1
completed-task count delta: +1
coverage count delta: +1
release events in accepted witness: 0
failure events in accepted witness: 0
timeout / autoreset boundaries in accepted witness: 0 / 0
illegal lifecycle actor-call faults: 0
actor / critic backward: 0 / 0
actor / critic optimizer.step: 0 / 0
ValueNorm.update: 0
checkpoint weight I/O: 0
public activation: 0
```

The four failed T3-C environment initializations did not become physical-step
episodes; the fifth attempt stopped before environment construction. Their
infrastructure failures are separately counted and are not merged into the
accepted lifecycle/event counts.

## AJ. retained nonclaims

This phase does not establish learned-policy quality, convergence, improvement,
paper-scale performance, frozen-actor success, long-training readiness,
checkpoint continuation, public-route readiness, B2-R6, reward correctness
beyond the observed slice, or any normal-horizon training result. T3-B is a
controlled task-progress capability witness, not a policy-performance result.

## AK. final classification

```text
B2-R0 through B2-R7: GPT REVIEW PASS / CLOSED
B2-T0-LD / B2-T0-RE1 / B2-T0 / B2-T1 / B2-T2: GPT REVIEW PASS / CLOSED
B2-T3: TASK-PROGRESS / HORIZON QUALIFICATION COMPLETE; AWAITING GPT REVIEW
T2 zero-completion cause: SHORT-HORIZON QUALIFICATION ARTIFACT
rollout-vs-episode horizon: QUALIFIED / AWAITING GPT REVIEW
normal-horizon real task completion: PASS / AWAITING GPT REVIEW
task-progress capability: ESTABLISHED / AWAITING GPT REVIEW
learner mutation: 0
long training: NOT AUTHORIZED
checkpoint continuation: NOT ESTABLISHED
public learned-policy route: DORMANT / BLOCKED
```

Classification:
`PHASE-B2-T3-TASK-PROGRESS-HORIZON-QUALIFIED-AWAITING-GPT-REVIEW`

This is not a self-granted GPT review pass.

## AL. GPT-review handoff

Independent review should verify the T3-A horizon separation, the complete
24-row T3-B trajectory and step-22 completion, completion/P2/coverage/ownership
consistency, zero learner mutation, and the transparent five-attempt T3-C
infrastructure history. No commit is authorized or created. The next action is
independent GPT review of B2-T3.
