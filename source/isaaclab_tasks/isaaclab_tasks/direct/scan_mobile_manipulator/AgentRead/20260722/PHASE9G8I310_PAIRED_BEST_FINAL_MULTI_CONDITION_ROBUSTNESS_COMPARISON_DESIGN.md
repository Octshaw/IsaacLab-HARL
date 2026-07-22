# Phase 9G-8I-3-1-0: Paired Best-vs-Final Multi-Condition Robustness Comparison Design

## 1. Classification And Frozen Decision

```text
classification:
  PAIRED-MULTI-CONDITION-COMPARISON-DESIGN-READY

MINIMUM NEW RUN SET:
  explicit final A: baseline_identity
  explicit final B: pose_cycle_forward
  explicit final C: pose_cycle_reverse

TOTAL NEW RUNS:
  3
```

The validated explicit best A/B/C artifacts are reusable. B2 and C2 are exact
repeatability evidence and are not additional samples to average. The historical
no-selector final-A artifact is semantically equivalent to Condition A but lacks
the frozen condition manifest and fingerprint, so it is retained only as a
reproducibility cross-check. A fresh explicit final A is required for the formal
paired table.

One final execution per condition is sufficient. The policy action path is
deterministic masked `Categorical.mode()`, the checkpoint actors are fixed, the
three condition contracts are fixed, and independent best-side B/C repeats
already established process-level determinism for the condition interface. No
final-checkpoint-specific random consumer was found. Repeating final B/C would
retest interface repeatability rather than answer the paired checkpoint question.

No decision that blocks Phase 9G-8I-3-1 remains unresolved.

## 2. Starting State And Preflight

The required static preflight was run from the repository root.

| Check | Result |
| --- | --- |
| `git rev-parse HEAD` | `9d31b15ff248d87634ae7487d0181ecf8a9349c2` |
| `git log -1 --oneline` | `9d31b15f - add deterministic baseline and cyclic pose-slot profiles ...` |
| `git status --short --untracked-files=all` | empty |
| `git diff --name-status` | empty |
| `git diff --check` | PASS, no output |

The current commit contains the complete accepted Phase 9G-8I-3-0 through
9G-8I-3-0R-2R implementation, test, repair, and validation chain. The worktree
was clean before this documentation phase began. Preflight therefore passes.

The commit range from the runtime-validation base to the current HEAD is:

```text
167bafaac84f7f8f527af40ed786e4834a7db704
  ..
9d31b15ff248d87634ae7487d0181ecf8a9349c2
```

Static inspection confirmed that this range contains the accepted initial-
condition implementation, playback/training guards, environment integration,
tests, repair, reports, and handoff documents. No later production delta exists.

## 3. Scope And Research Questions

The primary question is frozen as:

```text
Does the late-training difference between the retained best and final
checkpoints persist across multiple deterministic same-task initial conditions?
```

Two conclusions must be kept separate:

1. **Late-training behavior:** whether final became worse, less balanced, or
   more stalled than best across A/B/C.
2. **Checkpoint-selection alignment:** whether the training-trajectory
   `Total_Reward` rule happened to retain the checkpoint that is more robust
   across A/B/C.

This is not a search for a globally best checkpoint, a convergence claim, a
random-seed generalization study, or a statistical significance test. It covers
one retained checkpoint pair, three deterministic pose-slot permutations, seed
1, one environment, and 300 deterministic decisions per process.

## 4. Static Authorities Inspected

The following accepted authorities were read in full:

```text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260720/PHASE9G8I21_SEQUENTIAL_BEST_FINAL_BOUNDED_ATTRIBUTION_PLAYBACK_EXECUTION_AND_COMPARISON.md
AgentRead/20260721/PHASE9G8I30_BEST_FINAL_ROBUSTNESS_AND_LATE_TRAINING_REGRESSION_DIAGNOSIS_DESIGN.md
AgentRead/20260721/PHASE9G8I30R_CONTROLLED_INITIAL_CONDITION_VARIATION_INTERFACE_AND_CONTRACT_DESIGN.md
AgentRead/20260722/PHASE9G8I30R2R_CONTROLLED_INITIAL_CONDITION_RUNTIME_IDENTITY_VALIDATION_RETRY.md
```

Checkpoint contract, loader, retained-history, attribution, and training
selection details were cross-checked against the Phase 9G-8F-1, 9G-8F-3,
9G-8I-1, 9G-8H-1, and 9G-8I-2-0 reports and the current source boundaries:

```text
assignment_initial_condition.py
scripts/reinforcement_learning/harl/play_assignment.py
checkpoint contract/training-state JSON metadata under best_model/ and models/
attribution rows/summary/segment artifacts
initial-condition manifests
retained console logs for historical best/final A
```

Only JSON, CSV, text, file inventory, source, and opaque-byte hashes were read.
No checkpoint `.pt` file was deserialized or loaded.

## 5. Retained Checkpoint Identities

Training run root:

```text
E:\Project\IsaacLab_HARL\results\isaaclab\
Isaac-Scan-Mobile-Manipulator-Direct-v0\happo\
assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis\
seed-00001-2026-07-20-17-40-33
```

| Field | Retained best | Retained final |
| --- | --- | --- |
| Child | `best_model` | `models` |
| Kind | `best` | `final` |
| Generation | 10 | 22 |
| Associated training point | post-update 107 | post-update 333 |
| Step | 32100 record rollout | 99900 final rollout |
| Contract | `assignment_checkpoint_contract_v2` | same |
| Contract fingerprint | `19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6` | same |
| Profile / algorithm / state | `lifecycle_contract_c` / HAPPO / EP | same |
| Sequence / sharing | feed-forward / `share_param=false` | same |
| M / N | 3 / 50 | same |
| Actor / shared / action | 1059 / 3183 / 51 | same |
| Evaluation load | actor-only, `normal_evaluation`, `legacy_fallback=false` | same |

Static metadata and accepted audits establish completion markers, contract
fingerprints, actor inventories, sizes, and opaque-byte SHA-256 integrity for
both children. Critic and ValueNorm artifacts are part of checkpoint integrity,
but normal evaluation loads only the three actors.

### 5.1 Best-Selection Rule

For each 300-step training rollout, the runner collected a trajectory, performed
actor and critic updates, logged the rollout, and then applied a strict record
comparison:

```text
Total_Reward(rollout q) =
  sum over t=1..300 of
    mean over environments and robots of final_reward[q,t]

if logger.total_reward > best_avg_reward:
    save post-update weights to best_model/
```

Ties do not replace `best_model`, and evaluation did not select it. The last
strict record was rollout 107 at step 32100 (`Total_Reward=170.783157`), so the
retained best contains post-update-107 weights. The score itself was generated
by the pre-update policy for that rollout; this one-update association remains a
known interpretation limit. Final contains post-update-333 weights at step
99900.

The best rule directly optimizes training-trajectory reward, not completion
fairness, zero-progress counts, budget releases, or A/B/C robustness.

## 6. Existing Artifact Inventory

All exact paths below are under this absolute root:

```text
E:\Project\IsaacLab_HARL\results\isaaclab\
Isaac-Scan-Mobile-Manipulator-Direct-v0\happo
```

| ID | Exact child path under root | Files | Rows / decisions / segments | Condition provenance | Checkpoint | Source commit |
| --- | --- | ---: | --- | --- | --- | --- |
| Explicit best A | `assignment_happo_n50_phase9g8i30r2r_baseline_identity_best_runtime_identity/seed-00001` | 4 | 900 / 300 / 27 | explicit A + manifest + fingerprint | best / gen 10 | `167bafaac84f7f8f527af40ed786e4834a7db704` |
| Explicit best B1 | `assignment_happo_n50_phase9g8i30r2r_pose_cycle_forward_run1_best_runtime_identity/seed-00001` | 4 | 900 / 300 / 29 | explicit B + manifest + fingerprint | best / gen 10 | `167bafa...` |
| Explicit best B2 | `assignment_happo_n50_phase9g8i30r2r_pose_cycle_forward_run2_best_runtime_identity/seed-00001` | 4 | 900 / 300 / 29 | exact B repeat | best / gen 10 | `167bafa...` |
| Explicit best C1 | `assignment_happo_n50_phase9g8i30r2r_pose_cycle_reverse_run1_best_runtime_identity/seed-00001` | 4 | 900 / 300 / 23 | explicit C + manifest + fingerprint | best / gen 10 | `167bafa...` |
| Explicit best C2 | `assignment_happo_n50_phase9g8i30r2r_pose_cycle_reverse_run2_best_runtime_identity/seed-00001` | 4 | 900 / 300 / 23 | exact C repeat | best / gen 10 | `167bafa...` |
| Historical best A | `assignment_happo_n50_phase9g8i21_best_100k_proposal_effective_attribution/seed-00001` | 3 | 900 / 300 / 27 | implicit no-selector; no condition manifest | best / gen 10 | `0e610f9edc403a51a285777b672b3ea996681542` |
| Historical final A | `assignment_happo_n50_phase9g8i21_final_100k_proposal_effective_attribution/seed-00001` | 3 | 900 / 300 / 30 | implicit no-selector; no condition manifest | final / gen 22 | `0e610f9e...` |

The 300-decision count is the count of unique
`(env_id, episode_id, decision_step)` keys. There are 299 decisions in episode
0 and one post-reset decision in episode 1; every decision has exactly robot ids
0, 1, and 2, yielding 900 rows.

All rows, summaries, and segments use:

```text
phase9g8h1_assignment_proposal_effective_attribution_v1
```

Every explicit result additionally uses:

```text
manifest schema:  assignment_initial_condition_manifest_v1
condition schema: assignment_initial_condition_contract_v1
```

All seven candidates used seed 1, one environment, 300 deterministic decisions,
the `algorithm_proxy_component_mesh.yaml` scenario, HAPPO/EP/feed-forward actors,
`lifecycle_contract_c`, masked `Categorical.mode()`, CUDA deterministic mode,
budget-triggered cooldown, no cooldown mask overlay, redirect guardrail disabled,
and actor-only normal-evaluation loading with no legacy fallback. Historical
loader logs explicitly report best generation 10 and final generation 22 and
successful 300-step completion.

### 6.1 Explicit Condition Contracts

| Condition | Profile | Robot-to-slot mapping | Fingerprint |
| --- | --- | --- | --- |
| A | `baseline_identity` | r0:S0, r1:S1, r2:S2 | `d22778fbe70a5300999c58044177f2632b3c782c931d3414e086142035c516bc` |
| B | `pose_cycle_forward` | r0:S1, r1:S2, r2:S0 | `e9b92541c293de20277a97c61037b1592c01d72e6a84e8e6ba0e3fbe68da630f` |
| C | `pose_cycle_reverse` | r0:S2, r1:S0, r2:S1 | `9f476403513ffb4377405d809fc71e537e1982f4ea30e17fad4ea3f3ec97f320` |

The current immutable source identities match the accepted manifests:

| Input | SHA-256 |
| --- | --- |
| Scenario YAML | `3256398cda4de7caee3b1e1d6de74018623a5d36888a86eeabe0a94392affdfd` |
| Robot YAML | `31f6be04615bdab58f06dd51fdc7185a608231b1f0c784aeff37647e4c9f5837` |
| Capability YAML | `a340f18094c117066e4f5a9e2ee0d5656bc98d54a91c4071d93808abe6e6bf29` |
| Viewpoint CSV | `f18ee898395e872037e93ff80659e6d480dc89b92460aee8da42bcbb7e2351eb` |
| Component OBJ | `9e779f2cfddbb2e9a60691217d2abb7bb780ecb2f5661c666397c55bf6119dc7` |

### 6.2 Deterministic Identity Evidence

| Comparison | Rows SHA-256 | Segments SHA-256 | Result |
| --- | --- | --- | --- |
| Explicit A and historical best A | `6a331aa1ad490016161804497aca84d1dc6ea1f445872e8a29fe0f517f786499` | `76c9d09e85dd5c7048d3b6b9f307a0f1135a79f713c92d96e7649d5f551d6362` | exact |
| B1 and B2 | `9abbee8be7b97f5da9cbcd8a470d9306b90d73fda807872288c2ad40fd94aa92` | `70ce639199c8c452dab42ec7f6f42099aa71db5efa44f6cb8d2961ba5ef7309d` | exact |
| C1 and C2 | `a2867da6a68e1f5305266458584e6494b7588373cc26b60171593fb3009a2c7e` | `177e91d41101adf36e80db395458711b78efd21b5aa1cc31257f8c02e6698abc` | exact |

B1/B2 and C1/C2 summaries differ only in output-specific provenance paths and
timestamps; canonical behavior is exact. This is repeatability evidence, not
four independent condition samples.

The historical final-A hashes retained for the future cross-check are:

```text
rows:
  f02c5b236bb81db1221cba713b245aa385724b2052a1bae32f24d412cf7cfbf1

segments:
  f3d85fc0bb14492f3f10046e13de6f82a195e7d7de234022ca5dd8974d96df15

summary:
  4f95ada2ea130ad37fb00de31160e533493954bcfe7c65ebf634d015d528bad6
```

### 6.3 Formal Best-Side Metric Baselines

The selected explicit best artifacts produce these frozen comparison baselines:

| Condition | Completion vector | Total | Coverage | Jain completion fairness | Zero-progress rows | Budget releases |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| A | `[6,8,6]` | 20 | 0.70 | 0.980392 | 31 | 1 |
| B | `[6,10,6]` | 22 | 0.70 | 0.937984 | 15 | 1 |
| C | `[7,7,3]` | 17 | 0.62 | 0.900312 | 15 | 0 |

Coverage is displayed to two decimal places; comparisons use the serialized
source values (`0.699999988079071` for A/B and `0.6200000047683716` for C) under
the frozen tolerance. These rows are pre-existing evidence, not newly observed
final-checkpoint results.

## 7. Formal Reuse Decisions

| Evidence | Frozen use |
| --- | --- |
| Explicit best A | Formal best side of Condition A |
| Explicit best B1 | Formal best side of Condition B |
| Explicit best B2 | Identity confirmation only; do not average |
| Explicit best C1 | Formal best side of Condition C |
| Explicit best C2 | Identity confirmation only; do not average |
| Historical best A | No-selector compatibility evidence only; explicit A supersedes it formally |
| Historical final A | Prior behavior and future reproducibility cross-check only |

No best checkpoint execution is required again.

## 8. Historical Final-A Reuse Analysis

### 8.1 Semantic Equivalence

The historical no-selector final result can be attributed semantically to A:

1. The old no-selector path used the baseline robot-to-start-pose mapping
   r0:S0, r1:S1, r2:S2.
2. Explicit `baseline_identity` is defined as exactly that mapping and leaves
   robot identity, capabilities, actor bindings, task, and checkpoint semantics
   unchanged.
3. Historical best A and explicit best A have byte-identical rows and segments
   and behaviorally identical summaries after removing `artifact_paths`.
4. Historical final A used the same scenario, immutable inputs, seed, lifecycle
   overrides, deterministic action mode, horizon, and normal-evaluation loader
   contract as historical best A.
5. The explicit pose mapping is checkpoint-independent; no final-checkpoint-
   specific profile transform exists.

Semantic classification:

```text
SEMANTICALLY-REUSABLE-BUT-NOT-FORMAL-PAIR
```

### 8.2 Formal Provenance

Historical final A has only the three attribution artifacts. It does not contain:

```text
assignment_initial_condition_manifest.json
assignment_initial_condition_contract_v1
the Condition A fingerprint
an explicit robot-to-slot mapping
condition/checkpoint provenance separation
```

It therefore cannot satisfy the formal same-fingerprint pair requirement. The
frozen decision is to run one fresh explicit final A and use the historical
result only as a reproducibility cross-check.

### 8.3 Mandatory Future Cross-Check

Before B or C may run, fresh explicit final A must match historical final A as
follows:

```text
rows CSV:       byte/behavior exact
segments CSV:   byte/behavior exact
summary JSON:   canonical equality after normalizing artifact_paths only
raw actions:    exact for all 300 decision keys and all three robots
```

Keys must be joined by `(env_id, episode_id, decision_step, robot_id)`, not by
`decision_step` alone. On mismatch, Phase 9G-8I-3-1 must stop before B/C,
identify the first differing key and field, and classify the comparison
`COMPARISON-INVALID`. It must not retry or patch the runtime.

## 9. Minimum New Execution Set

```text
reuse:
  explicit best A
  explicit best B1
  explicit best C1

identity evidence only:
  best B2
  best C2
  historical best A

prior/cross-check evidence only:
  historical final A

new:
  explicit final A
  explicit final B
  explicit final C

total new executions:
  3
```

Three is the minimum set that gives every formal pair the same four-file
contract and an exactly equal condition fingerprint while avoiding redundant
best or repeatability runs.

## 10. Frozen Pairing Contract

The primary key of a formal pair is `(profile_id, condition_fingerprint)`.
Folder names are never sufficient.

| Pair | Required fingerprint |
| --- | --- |
| Best A vs Final A | `d22778fbe70a5300999c58044177f2632b3c782c931d3414e086142035c516bc` |
| Best B vs Final B | `e9b92541c293de20277a97c61037b1592c01d72e6a84e8e6ba0e3fbe68da630f` |
| Best C vs Final C | `9f476403513ffb4377405d809fc71e537e1982f4ea30e17fad4ea3f3ec97f320` |

Within each pair, require exact equality of:

```text
manifest schema and condition contract schema
full canonical condition_contract mapping
condition fingerprint
profile id and robot-to-slot mapping
baseline slots and resolved full poses
scenario/component/viewpoint identities and hashes
robot/capability identities, bindings, and hashes
M=3 and N=50
policy interface contract 1059/3183/51
seed=1
one environment and 300-decision horizon
lifecycle/cooldown/guardrail overrides
feed-forward/recurrent/share_param state
masked deterministic action mode
normal_evaluation and legacy_fallback=false
attribution schema
```

Expected checkpoint/run differences are:

```text
best checkpoint child/kind/generation/artifact identity
  best_model / best / 10 / best actor hashes

final checkpoint child/kind/generation/artifact identity
  models / final / 22 / final actor hashes

run timestamp
output directory
console path
```

### 10.1 Repository-Commit Provenance Exception

The explicit best manifests record repository commit `167bafa...` because the
accepted initial-condition chain was present as reviewed worktree changes when
those runs were made. Current clean commit `9d31b15f...` commits that exact
accepted chain. A future final manifest is therefore expected to record the
current committed source lineage rather than `167bafa...`.

This does not weaken condition pairing:

- `repository_commit` is run provenance, not part of `condition_contract`.
- `compute_condition_fingerprint` hashes canonical
  `condition_contract.identity_mapping()`; run provenance is stored separately.
- Current immutable scenario, component, viewpoint, robot, capability, policy
  interface, and profile hashes match the accepted best manifests.
- The known commit-field difference must be reported, never silently erased.

Phase 9G-8I-3-1 preflight must verify that the production implementation still
matches committed `9d31b15f` content. A later documentation-only commit is
acceptable only after a diff audit proves no production/test/YAML/data change.
Any substantive runtime change requires renewed design review.

## 11. Frozen Future Runtime Contract

Every new final run must resolve to:

```text
checkpoint child:             models
checkpoint kind/generation:   final / 22
load purpose:                 normal_evaluation
legacy fallback:              false
checkpoint contract:          assignment_checkpoint_contract_v2
checkpoint fingerprint:       19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6

algorithm/state:              HAPPO / EP
profile:                      lifecycle_contract_c
policy sequence:              feed_forward
share_param:                  false
recurrent flags:              false / false

seed:                         1
num_envs:                     1
max_steps:                    300
headless:                     true
device:                       cuda:0
deterministic actor action:   masked Categorical.mode()

M/N:                          3 / 50
actor/shared/action widths:   1059 / 3183 / 51
raw/decoded noop:             50 / -1

cooldown enabled:             true
cooldown trigger:             budget
cooldown action-mask overlay: false
redirect guardrail:           false
attribution logging:          enabled
initial condition:            explicit A, B, or C
```

Only the explicit profile, fresh output path, console path, and run label may
vary among the three new executions. Exact commands and output names remain a
Phase 9G-8I-3-1 preflight responsibility so path collisions and the then-current
committed HEAD can be checked immediately before launch.

## 12. Required Final Artifacts And Technical Validity

Each new explicit final result must contain exactly:

```text
assignment_proposal_effective_rows.csv
assignment_proposal_effective_summary.json
assignment_target_segments.csv
assignment_initial_condition_manifest.json
```

Each run must satisfy:

```text
normal process exit and simulator shutdown
900 rows
300 unique (env, episode, decision) keys
exact robot ids 0/1/2 per decision
zero duplicate row keys
zero duplicate effective targets
zero invariant failures
zero unclassified rows
zero nonfinite applicable values
valid segment continuity and reset grouping
loader identity final/models/generation 22
normal_evaluation with no legacy fallback
condition manifest and recomputed fingerprint exact
```

Any missing artifact, wrong schema, identity mismatch, malformed grouping,
runtime exception, or nonzero exit invalidates that pair.

## 13. Frozen Execution Order And Stop Rules

```text
1. final A
2. technical/artifact validation
3. exact Condition A contract/fingerprint pairing with best A
4. best-A versus final-A metrics
5. fresh final-A versus historical final-A cross-check

6. final B
7. technical/artifact validation
8. exact Condition B contract/fingerprint pairing with best B1
9. best-B versus final-B metrics

10. final C
11. technical/artifact validation
12. exact Condition C contract/fingerprint pairing with best C1
13. best-C versus final-C metrics

14. cross-condition synthesis
```

Stop on the first:

```text
checkpoint/load identity mismatch
runtime-contract mismatch
technical runtime failure or nonzero exit
artifact/schema/invariant/nonfinite failure
condition contract or fingerprint mismatch
fresh-final-A historical cross-check mismatch
unexpected nondeterministic/corrupted evidence
```

There is no automatic retry, source/config patch, alternate output name, or
continuation after failure.

## 14. Frozen Metric Definitions

All metrics must be computed from the existing rows, summary, and segment
schemas. Integer counts are compared exactly. Derived floating metrics are ties
when `abs(final - best) <= 1e-12`; this is a serialization tolerance, not a
statistical equivalence margin.

### 14.1 Primary Metrics

| Metric | Exact definition | Better direction |
| --- | --- | --- |
| Coverage | Maximum applicable pre-reset team `coverage_ratio` over the 300 decisions; monotonic within the episode and robust to the final reset row | higher |
| Total completions | Sum of per-robot `assigned_target_completion_count`, aggregated across episode summaries; cross-check against row completion events | higher |
| Jain completion fairness | `(sum c_r)^2 / (M * sum c_r^2)` from the completion vector; N/A if total completions is zero | higher |
| Total zero-distance-progress rows | Sum of producer-defined per-robot `zero_progress_step_count`; do not invent a new epsilon | lower |
| Total budget releases | Sum of per-robot `release_budget_failure_count`, cross-checked against release events | lower |

The five primary metrics span three families:

```text
outcome:
  coverage
  total completions

balance:
  Jain completion fairness

stagnation:
  total zero-distance-progress rows
  total budget releases
```

No weighted composite score is permitted.

### 14.2 Secondary Diagnostics

Task outcome:

```text
coverage trajectory after deduplicating team state by decision key
completion vector and event timing
target segment count
```

Load distribution:

```text
mean active robots per decision
executing-step vector
Jain execution fairness
completion share by robot
max-minus-min completion count
dominant-robot completion fraction
```

Motion/stagnation:

```text
zero-base-motion executing rows
longest, mean, and median valid segment duration
Contract-C noop and same-target continuation counts
repeated-target attempt counts
```

Assignment/policy behavior:

```text
proposal-noop vector
first raw action per robot
first exact raw-action trajectory divergence
proposal/effective/controller trajectories
resolver rejection counts and reasons
duplicate-effective-target checks
release reasons
```

Arm motion, rotation quality, joint-space behavior, physical collision safety,
and exact selected path-cost quality are unavailable from the frozen artifacts
and must not be inferred.

## 15. Pairwise Delta Contract

For every primary and supported secondary scalar:

```text
delta = final - best
```

| Metric | Favorable final delta |
| --- | --- |
| Coverage | positive |
| Total completions | positive |
| Jain completion fairness | positive |
| Zero-distance-progress rows | negative |
| Budget releases | negative |

The required pairwise table is:

| Condition | Metric | Best | Final | Final-Best | Favored checkpoint |
| --- | --- | ---: | ---: | ---: | --- |

Vector and trajectory diagnostics must report both values and the first
diverging key where applicable; they are not reduced to an arbitrary scalar.

## 16. Cross-Condition Aggregation

For each metric, report:

```text
best-win condition count
final-win condition count
tie count
minimum and maximum across A/B/C for each checkpoint
range (maximum - minimum) across A/B/C for each checkpoint
```

Required table:

| Metric | Best wins | Final wins | Ties | Best range | Final range | Interpretation |
| --- | ---: | ---: | ---: | --- | --- | --- |

Do not average incompatible metrics into one score. Three deterministic
conditions support descriptive counts and ranges only; no p-value, confidence
interval, or statistical generalization claim is allowed.

## 17. Frozen Condition-Level Classes

Apply these classes only after technical and fingerprint validity passes:

- **BEST-DOMINANT:** best is no worse on every available primary metric and
  strictly better on at least one. This is primary-metric Pareto dominance.
- **FINAL-DOMINANT:** final is no worse on every available primary metric and
  strictly better on at least one.
- **MIXED:** each checkpoint wins at least one available primary metric, so the
  evidence contains an outcome/balance/stagnation tradeoff.
- **EQUIVALENT-WITHIN-OBSERVED-METRICS:** all available primary metrics tie.
  Secondary trajectory differences are still reported but do not manufacture a
  primary winner.
- **INVALID:** technical, checkpoint, manifest, pairing, determinism, or
  artifact validity fails.

If completion fairness is N/A because a checkpoint has zero total completions,
the metric is excluded from Pareto comparison and the zero-completion outcome is
reported explicitly. At least the remaining four primary metrics still apply.

## 18. Frozen Overall Outcome Classes

Apply the following precedence exactly:

1. **COMPARISON-INVALID** if any condition is `INVALID` or the final-A historical
   cross-check fails.
2. **CONSISTENT-LATE-TRAINING-REGRESSION** if at least two of A/B/C are
   `BEST-DOMINANT`, none is `FINAL-DOMINANT`, and no individual primary metric
   favors final in two or more conditions. This is the frozen meaning of
   regression across most conditions without a compensating consistent final
   advantage.
3. **CONDITION-SENSITIVE-LATE-TRAINING-REGRESSION** if at least one condition is
   `BEST-DOMINANT` but rule 2 is not met. The best/final ranking therefore
   depends materially on the initial robot-slot assignment.
4. **NO-ROBUST-LATE-TRAINING-REGRESSION-EVIDENCE** if no condition is
   `BEST-DOMINANT` and either at least two are `FINAL-DOMINANT` or all three are
   in `{FINAL-DOMINANT, EQUIVALENT-WITHIN-OBSERVED-METRICS}`.
5. **MIXED-CHECKPOINT-TRADEOFF** for every other valid result, including
   persistent cross-family conflicts without Pareto dominance.

These rules describe the three frozen conditions only. They do not prove that
late training generally regressed or improved.

## 19. Checkpoint-Selection Alignment Classes

The best checkpoint was selected from rollout `Total_Reward` on the training
trajectory, not from multi-condition evaluation. Report a separate class:

- **SELECTION-ALIGNED:** overall result is
  `CONSISTENT-LATE-TRAINING-REGRESSION`.
- **SELECTION-PARTIALLY-ALIGNED:** overall result is condition-sensitive, or is
  mixed while best has more primary metric-condition wins than final and at
  least one `BEST-DOMINANT` condition.
- **SELECTION-MISALIGNED:** overall result has no robust regression evidence,
  at least two conditions are `FINAL-DOMINANT`, and none is `BEST-DOMINANT`.
- **SELECTION-INCONCLUSIVE:** comparison is invalid, all primary evidence is
  equivalent, or remaining mixed evidence satisfies none of the above.

This assessment does not claim that the selection rule was intended to optimize
the A/B/C condition suite or that another rule is globally optimal.

## 20. Historical A Evidence Before New Results

The accepted historical Condition-A-equivalent comparison remains prior
evidence, not a substitute for the formal pair:

| Metric | Best | Historical final |
| --- | ---: | ---: |
| Completion vector | `[6,8,6]` | `[12,5,3]` |
| Total completions | 20 | 20 |
| Coverage | 0.70 | 0.68 |
| Jain completion fairness | 0.980392 | 0.749064 |
| Zero-distance-progress rows | 31 | 129 |
| Budget releases | 1 | 4 |

This motivated the robustness question and currently favors best on balance and
stagnation, but no formal A/B/C conclusion is assigned before fresh explicit
final A/B/C evidence exists.

## 21. Limitations

- One checkpoint pair, one seed, one environment, and one 300-decision
  deterministic trajectory per condition do not estimate expected performance.
- A/B/C are three fixed permutations of the same baseline pose slots, not
  arbitrary pose, task, dynamics, sensor, or robot-capability randomization.
- Masked mode actions describe deterministic policy behavior, not sampled
  training behavior.
- Best contains post-update weights associated with a pre-update record rollout.
- Only retained best and final checkpoints exist; no intermediate trajectory of
  policy changes can be reconstructed.
- Coverage can include incidental events that the current environment cannot
  reliably attribute to one robot.
- Formal condition fingerprints protect the controlled contract, not physical
  correctness or collision safety.
- A successful paired result cannot authorize long training, new seeds,
  stochastic evaluation, GUI/video, checkpoint continuation, or broader claims.

## 22. Explicit Non-Actions

This phase performed no:

```text
production source change
test change
YAML/data/CSV/OBJ change
result or checkpoint modification
console-log modification
installed HARL or Conda modification
AppLauncher or Isaac Sim launch
environment construction
playback or evaluation
checkpoint tensor load
training or continuation
new seed
GUI/video operation
commit
```

Only this report, the required TASK_PROGRESS archive, and the concise top-level
TASK_PROGRESS handoff were created or updated.

## 23. Next-Phase Boundary

After review and explicit acceptance, the only recommended next phase is:

```text
Phase 9G-8I-3-1:
Paired Best-vs-Final Multi-Condition Robustness Comparison Execution
```

That phase may execute only the frozen three-run final A/B/C set, in the frozen
order and with the frozen stop rules. It must not begin automatically from this
design phase.
