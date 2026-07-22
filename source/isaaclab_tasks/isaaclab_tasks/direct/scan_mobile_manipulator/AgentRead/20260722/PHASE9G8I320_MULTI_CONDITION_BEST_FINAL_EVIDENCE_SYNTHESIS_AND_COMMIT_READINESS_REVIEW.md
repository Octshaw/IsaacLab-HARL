# Phase 9G-8I-3-2-0: Multi-Condition Best-Final Evidence Synthesis And Commit-Readiness Review

## 1. Classification

```text
COMMIT-READY
```

The complete Phase 9G-8I-3 multi-condition best-final evidence chain is
internally consistent, traceable, bounded in its claims, and ready for a
documentation-only manual commit. Independent read-only parsing reproduced the
formal pairings, five primary metrics, three condition classes, overall class,
selection-alignment class, and historical Final-A identity.

## 2. Review Boundary

This review read Markdown, JSON, CSV, and opaque file bytes only. Inline Python
was used for temporary calculations; no helper file was created. No `.pt` file
was deserialized. No runtime, environment, policy, or package code was invoked.

The closure question is limited to the accepted three-condition evidence and
documentation commit. It does not decide whether to add seeds, conditions,
intermediate checkpoints, training, or a different selection rule.

## 3. Starting Repository State

| Check | Result |
| --- | --- |
| HEAD | `9d31b15ff248d87634ae7487d0181ecf8a9349c2` |
| Last commit | `9d31b15f - add deterministic baseline and cyclic pose-slot profiles ...` |
| Starting worktree | Exactly the expected five Markdown paths |
| Starting tracked diff | `TASK_PROGRESS.md` only |
| Starting diff check | PASS; line-ending warnings only |
| Unexpected production/test/YAML/data/result/checkpoint/log paths | None |

The five starting paths were the 9G-8I-3-1-0 design, its TASK archive, the
9G-8I-3-1 execution report, its TASK archive, and `AgentRead/TASK_PROGRESS.md`.
No cleanup, reset, stash, restore, rename, staging, or commit was performed.

## 4. Authorities Reviewed

The following authority chain was read and cross-checked:

- `AgentRead/AGENTS.md` and the starting `AgentRead/TASK_PROGRESS.md`.
- Phase 9G-8I-3-1-0 frozen pairing, metric, Pareto, overall, and alignment rules.
- Phase 9G-8I-3-1 final A/B/C execution evidence.
- Phase 9G-8I-3-0R-2R best A/B/C identity and B/C repeatability evidence.
- Phase 9G-8I-2-1 historical no-selector best/final Condition-A evidence.
- Phase 9G-8F-1 checkpoint manifest, canonical JSON, and fingerprint contract.
- Phase 9G-8F-3 all-loader compatibility and actor-only evaluation boundary.
- Phase 9G-8I-1 100k training, checkpoint, and selection evidence.
- Phase 9G-8H-1 attribution row, summary, and segment schema implementation.
- Phase 9G-8I-2-0 best/final deterministic playback contract.

## 5. Production And Input Integrity

The four runtime-bearing working files were compared with `HEAD` using Git blob
identities and were exact:

| File | Working/HEAD blob | Result |
| --- | --- | --- |
| `scripts/reinforcement_learning/harl/play_assignment.py` | `b46385425832ce7ee0206f3926c5a438dbe740b7` | PASS |
| `scripts/reinforcement_learning/harl/train.py` | `6f7570915fdf9cad99c7e258f54a69508d1d6bb9` | PASS |
| `assignment_initial_condition.py` | `a6d8379cbee07daf5a9693ebed567f70a2137253` | PASS |
| `scan_mobile_manipulator_env.py` | `2e82b3f4c975b977a825afaf5631898ab7c4f5ff` | PASS |

The immutable controlled-condition inputs also matched:

| Input | Recomputed SHA-256 | Result |
| --- | --- | --- |
| Scenario YAML | `3256398cda4de7caee3b1e1d6de74018623a5d36888a86eeabe0a94392affdfd` | PASS |
| Robot YAML | `31f6be04615bdab58f06dd51fdc7185a608231b1f0c784aeff37647e4c9f5837` | PASS |
| Capability YAML | `a340f18094c117066e4f5a9e2ee0d5656bc98d54a91c4071d93808abe6e6bf29` | PASS |
| Viewpoint CSV | `f18ee898395e872037e93ff80659e6d480dc89b92460aee8da42bcbb7e2351eb` | PASS |
| Component OBJ | `9e779f2cfddbb2e9a60691217d2abb7bb780ecb2f5661c666397c55bf6119dc7` | PASS |

## 6. Checkpoint Identity And Opaque Integrity

The retained training run is:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis/
seed-00001-2026-07-20-17-40-33
```

| Field | Best | Final |
| --- | --- | --- |
| Child | `best_model` | `models` |
| Kind | `best` | `final` |
| Generation | 10 | 22 |
| Contract | `assignment_checkpoint_contract_v2` | Same |
| Canonical fingerprint | `19ef40b574c09c6c54b5e2ffea38e900b383188d2b48737a42b01d0db27c76e6` | Same |
| Contract manifest vs run root | Byte exact | Byte exact |
| Declared artifacts | 5/5 size and opaque SHA exact | 5/5 size and opaque SHA exact |
| Tensor-inventory digests | 5/5 exact | 5/5 exact |
| Completion marker | Present and not older than declared artifacts | Present and not older than declared artifacts |
| Exact checkpoint file set | PASS | PASS |

Opaque artifact identities were:

| Artifact | Best SHA-256 | Final SHA-256 |
| --- | --- | --- |
| `actor_agent_robot_0.pt` | `3dce5c7d08ea069e6c5baa8d2ff78b977180814014ce7af6e6d663769c20a1a2` | `4c93f6cb7dc0846b2f19a0257f36a5e3fe8d22cf67a870b4d6c458d571f7a775` |
| `actor_agent_robot_1.pt` | `9f84f8f50be1e3ae36a5674b2cc81837cbb21e2099d9421a978f42473aab549b` | `d464ec120ae23638e5b9341290f019122ea16a13d32a13fa760f22015c415b5d` |
| `actor_agent_robot_2.pt` | `842781b3a1daf041016e8d9e5e6c9c94a2dd379d7f182773ea48a92316e1b623` | `cbbb7576a79a1bb52247fc25515d27c910cfb82ab3ca5d669324ea30d004444b` |
| `critic_agent.pt` | `73b7e10e148e1ae922b2645698b56392f6ff5a979f1d05ceca29acccbe74f502` | `711e151005571044f0524b6fc34456bbe1036fcccb25f1c22e111cdad014720f` |
| `value_normalizer.pt` | `c2ed67cc5a0ecea7ebb833a85efc07aa50fddce65f49d21f088fd778b1f016eb` | `ce0216c788731b74b176418fbe5feb24989de959033c484da01033ffff9a0ec2` |

Thus best and final use the same inference/checkpoint contract but different
actor weight artifacts. Normal evaluation validates all declared native files
and loads only the three ordered actor state dictionaries; critic and ValueNorm
are not live evaluation targets. This review performed no load at all.

## 7. Attribution Evidence Inventory And Hashes

Each formal best/final directory contained exactly the four required files.
Historical Final A contained exactly its three accepted attribution files. All
27 full SHA-256 values matched the accepted reports:

| Evidence | Manifest | Rows | Summary | Segments |
| --- | --- | --- | --- | --- |
| Best A | `f1bd7aa087950daa287f7532ceb05a3cf117934e9dba1c085a0738b3b33f4df0` | `6a331aa1ad490016161804497aca84d1dc6ea1f445872e8a29fe0f517f786499` | `ce5d56d7f4004be22f5274c943efd6fd93320f7d995dbf0f6de113eecbf47229` | `76c9d09e85dd5c7048d3b6b9f307a0f1135a79f713c92d96e7649d5f551d6362` |
| Best B1 | `0943a54dea17c962b69ac73f79a81c0c93625d5f4684a8aaeb6e7247e43c6e12` | `9abbee8be7b97f5da9cbcd8a470d9306b90d73fda807872288c2ad40fd94aa92` | `84ecb7810fa11630f78e8f6dc8c167a5959105856c1eef308f50fc034b91fbf5` | `70ce639199c8c452dab42ec7f6f42099aa71db5efa44f6cb8d2961ba5ef7309d` |
| Best C1 | `1b7c1d5ccdabaaa40abb363c91fe823074dd59850c080cc228b0da5803354433` | `a2867da6a68e1f5305266458584e6494b7588373cc26b60171593fb3009a2c7e` | `beb7b2344ea5dd4b281caddedc6f262c36a621d6e85fd9ae79477e47c9fd8461` | `177e91d41101adf36e80db395458711b78efd21b5aa1cc31257f8c02e6698abc` |
| Final A | `ec258497080a2361005ad4abaf11051169e81f28f1fe63ef728aa1e050698d42` | `f02c5b236bb81db1221cba713b245aa385724b2052a1bae32f24d412cf7cfbf1` | `2397b87c7f7137b14a2bd80020975fb3159a2a9d0343f784ec8fe635ae2e6258` | `f3d85fc0bb14492f3f10046e13de6f82a195e7d7de234022ca5dd8974d96df15` |
| Final B | `8ed81d6cc7f6e2e44b1f178241ea7421e998ee566334637b584f1e37af7bce6f` | `602b13b33316dab4968d841c877c60e9713d3d48f9c8b62cc6e98cadfe48c397` | `a63445ddfb98111505feec073fb46fa02b8645d93e20807841dc3a9285708263` | `f496013bde0f3283d532168ce41ff24071d6be6c341f5c2cce0a4a95678909e6` |
| Final C | `38eaee04c3d4b869f4c3a228b531b4b22ec5c9b1e1500aa8c590fac7f96762c1` | `2c1d9b9f90e61b2f96b57f8f30b1a67f2d613ff3d6719d1dfd09bd072e43e485` | `c587355c2768e08bef794a94caf4c30f55495892ddbb5552acfd1f49ed6940b9` | `f339ba2aa63a0120657091334de08bd3915339ad774ede42a7718f35afdf793f` |
| Historical Final A | N/A | `f02c5b236bb81db1221cba713b245aa385724b2052a1bae32f24d412cf7cfbf1` | `4f95ada2ea130ad37fb00de31160e533493954bcfe7c65ebf634d015d528bad6` | `f3d85fc0bb14492f3f10046e13de6f82a195e7d7de234022ca5dd8974d96df15` |

Best B1/B2 and C1/C2 rows and segments were also byte exact, and summaries
were exact after `artifact_paths` normalization. The formal pairs retain B1 and
C1 as frozen by the design.

## 8. Condition Pairing Verification

The fingerprint was independently recomputed as SHA-256 of canonical JSON for
the complete `condition_contract` identity mapping, excluding only
`profile_description`. Each best/final pair had exact full-contract equality.

| Condition | Profile | Robot-to-slot mapping | Recomputed fingerprint | Result |
| --- | --- | --- | --- | --- |
| A | `baseline_identity` | `r0:S0, r1:S1, r2:S2` | `d22778fbe70a5300999c58044177f2632b3c782c931d3414e086142035c516bc` | PASS |
| B | `pose_cycle_forward` | `r0:S1, r1:S2, r2:S0` | `e9b92541c293de20277a97c61037b1592c01d72e6a84e8e6ba0e3fbe68da630f` | PASS |
| C | `pose_cycle_reverse` | `r0:S2, r1:S0, r2:S1` | `9f476403513ffb4377405d809fc71e537e1982f4ea30e17fad4ea3f3ec97f320` | PASS |

Exact equality covered resolved poses and scanner offsets, scenario/component/
viewpoint identities, robot/capability bindings, `M=3`, `N=50`, interface
1059/3183/51, seed 1, one environment, 300 decisions, deterministic masked
actions, lifecycle overrides, feed-forward HAPPO/EP, `share_param=false`,
normal evaluation, no legacy fallback, and attribution schema v1.

The intended semantic difference is checkpoint weight identity. Best manifests
record commit `167bafaa...`; final manifests record `9d31b15f...`. Repository
commit is run provenance outside the canonical condition contract and was not
erased or treated as a pairing failure.

All six artifacts contained 900 unique robot rows, 300 joint decision keys,
robots 0/1/2 at every key, finite audited numeric fields, no invariant failures,
and exact completion/release event cross-checks.

## 9. Historical Final-A Reproduction

Fresh explicit Final A reproduced historical no-selector Final A:

| Check | Result |
| --- | --- |
| Rows | Byte exact |
| Segments | Byte exact |
| Summary | Exact after removing only `artifact_paths` |
| Action/effective/controller identity | All 900 robot rows exact |
| First difference | None |

This confirms that the explicit initial-condition interface preserves the
historical final-checkpoint Condition-A behavior.

## 10. Independent Primary Metrics And Classes

Metrics were recalculated directly from rows and producer summaries. Coverage
is maximum applicable pre-reset team coverage; completions and releases were
cross-checked against row events; fairness was recomputed from completion
vectors; the float tie tolerance was `1e-12`.

| Condition | Coverage Best -> Final | Completions Best -> Final | Jain fairness Best -> Final | Zero-progress Best -> Final | Budget release Best -> Final | Class |
| --- | --- | --- | --- | --- | --- | --- |
| A | `0.699999988079071 -> 0.6800000071525574` Best | `20 -> 20` tie | `0.9803921568627451 -> 0.7490636704119851` Best | `31 -> 129` Best | `1 -> 4` Best | `BEST-DOMINANT` |
| B | `0.699999988079071 -> 0.6800000071525574` Best | `22 -> 19` Best | `0.937984496124031 -> 0.7037037037037037` Best | `15 -> 113` Best | `1 -> 5` Best | `BEST-DOMINANT` |
| C | `0.6200000047683716 -> 0.6800000071525574` Final | `17 -> 15` Best | `0.9003115264797508 -> 0.7575757575757576` Best | `15 -> 95` Best | `0 -> 4` Best | `MIXED` |

Metric-condition win counts and observed ranges were:

| Metric | Best/final/tie wins | Best min/max/range | Final min/max/range |
| --- | --- | --- | --- |
| Coverage | `2/1/0` | `0.6200000047683716 / 0.699999988079071 / 0.07999998331069946` | `0.6800000071525574 / 0.6800000071525574 / 0` |
| Completions | `2/0/1` | `17 / 22 / 5` | `15 / 20 / 5` |
| Jain fairness | `3/0/0` | `0.9003115264797508 / 0.9803921568627451 / 0.08008063038299429` | `0.7037037037037037 / 0.7575757575757576 / 0.05387205387205385` |
| Zero-progress | `3/0/0` | `15 / 31 / 16` | `95 / 129 / 34` |
| Budget releases | `3/0/0` | `0 / 1 / 1` | `4 / 5 / 1` |

At least two conditions are `BEST-DOMINANT`, none is `FINAL-DOMINANT`, and no
primary metric favors final in two or more conditions. Applying the frozen
precedence independently therefore gives:

```text
CONSISTENT-LATE-TRAINING-REGRESSION
```

This class describes only the three frozen deterministic conditions.

## 11. Selection Alignment

Source/report tracing confirms that `best_model` was retained by a strict
training-rollout `Total_Reward > best_avg_reward` rule, not by the A/B/C suite.
The last strict record was rollout 107 at step 32100 (`Total_Reward=170.783157`),
and the retained best contains post-update-107 weights. The score came from the
pre-update policy that collected that rollout. Final contains post-update-333
weights at step 99900. Checkpoint generation 10 is save-generation metadata,
not the optimizer update index.

Applying the frozen alignment rule to the independently reproduced overall
class gives:

```text
SELECTION-ALIGNED
```

The retained Total_Reward-selected checkpoint is aligned with the
three-condition robustness evidence in this experiment. This does not show
that `Total_Reward` is a globally optimal checkpoint-selection rule.

## 12. Secondary Evidence Synthesis

Every artifact had execution vector `[300,300,300]`, mean active robots `3.0`,
and Jain execution fairness `1.0`. Full participation therefore did not ensure
productive balance:

| Condition | Best completion vector | Final completion vector |
| --- | --- | --- |
| A | `[6,8,6]` | `[12,5,3]` |
| B | `[6,10,6]` | `[11,7,1]` |
| C | `[7,7,3]` | `[7,7,1]` |

Final also showed consistently greater stagnation evidence:

| Condition | Zero-progress Best -> Final | Budget releases Best -> Final | Zero-base-motion Best -> Final |
| --- | --- | --- | --- |
| A | `31 -> 129` | `1 -> 4` | `100 -> 201` |
| B | `15 -> 113` | `1 -> 5` | `94 -> 216` |
| C | `15 -> 95` | `0 -> 4` | `74 -> 179` |

Together these diagnostics support an engineering interpretation of degraded
productive motion/progress behavior late in training, rather than robots simply
becoming idle. A zero-base-motion row is not by itself proof of physical stall.

Condition C remains an important tradeoff: Final raises coverage from 0.62 to
0.68, while Best retains more completions, better completion fairness, fewer
zero-progress rows, and fewer budget releases. Coverage and productive
completion are related but not interchangeable signals.

## 13. Claim Boundary

### 13.1 Directly Supported

- The three formal best/final condition pairs are valid and traceable.
- Best is Pareto-dominant in A and B; C is mixed.
- Best has higher completion fairness and lower zero-progress/release counts in
  all three conditions.
- The pre-frozen rules classify these three conditions as consistent
  late-training regression and the retained checkpoint as selection-aligned.
- Explicit Final A exactly reproduces historical no-selector Final-A behavior
  at the rows, segments, normalized summary, and 900-action levels.

### 13.2 Engineering Interpretations

- The final policy appears to stay active while distributing productive work
  less evenly.
- Its degradation is more consistent with assignment/progress quality than
  with robots becoming idle.
- Recurring low productivity for some robots across pose permutations suggests
  the issue is not solely one fixed start slot.

These are bounded interpretations, not proven causal mechanisms.

### 13.3 Unsupported Or Prohibited

The evidence does not establish statistical significance, population-level or
arbitrary-condition regression, all-seed generalization, convergence or
divergence, global checkpoint optimality, reward-function causality,
actor-specific causality, physical collision safety, or real-robot performance.

## 14. Research Contribution Mapping

The evidence block contributes traceable support for dynamic assignment
lifecycle analysis, productive load-balance evaluation, task progress and
release diagnostics, checkpoint robustness under controlled robot-start
changes, and reproducible evaluation contracts.

It does not claim a contribution to viewpoint generation, ROI importance,
model-free NBV, arbitrary-scale generalization, or real articulated-robot
validation.

## 15. Limitations

The evidence is descriptive for one best/final checkpoint pair, one seed, three
fixed robot-slot permutations, one vector environment, and 300 deterministic
decisions. Coverage includes environment events not always attributable to a
single robot. The artifacts do not establish arm/joint motion, rotation
quality, collision safety, or selected path-cost optimality. Best-selection
score and retained post-update weights have the documented one-update
association limit.

## 16. Evidence Retention

Result directories are preserved locally as runtime evidence and are not to be
staged. Console logs remain local supporting evidence and are not to be staged.
Checkpoint directories remain local and are not to be staged. No runtime
artifact was copied into `AgentRead`, and no ZIP archive was created.

## 17. Exact Manual Staging Set

Only the following seven Markdown files are recommended for manual staging:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260722/PHASE9G8I310_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_DESIGN.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I310_MULTI_CONDITION_COMPARISON_DESIGN_20260722.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260722/PHASE9G8I31_PAIRED_BEST_FINAL_MULTI_CONDITION_ROBUSTNESS_COMPARISON_EXECUTION.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I31_MULTI_CONDITION_COMPARISON_EXECUTION_20260722.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260722/PHASE9G8I320_MULTI_CONDITION_BEST_FINAL_EVIDENCE_SYNTHESIS_AND_COMMIT_READINESS_REVIEW.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260722/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I320_EVIDENCE_SYNTHESIS_COMMIT_READINESS_20260722.md
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

No result, log, checkpoint, source, test, YAML, or data path belongs in the
staging set.

## 18. Recommended Commit Message

```text
docs(assignment): validate multi-condition late-training regression

- formalize paired best-final comparison across three controlled start conditions
- verify exact condition-contract and fingerprint pairing
- reproduce historical final baseline behavior through explicit Condition A
- classify A and B as best-dominant and C as mixed
- document consistent late-training regression under frozen comparison rules
- record completion-balance, stagnation, and budget-release evidence
- preserve descriptive limits for one checkpoint pair, seed, and horizon
```

The commit was not run.

## 19. Final Repository Verification

Final `git status --short --untracked-files=all` contains exactly the seven
Markdown paths listed above: one modified `TASK_PROGRESS.md`, the four expected
carry-forward design/execution documents and archives, and the two new 9G-8I-3-2-0
documents. The complete Markdown content was inspected. No path is staged, and
no production, test, YAML/data, result, checkpoint, or console-log path appears.

`git diff --name-status` and `git diff --stat` contain only the tracked
`TASK_PROGRESS.md`; the six new Markdown files are untracked by design.
`git diff --check` passes, with only the repository's informational LF-to-CRLF
warning. This is the expected documentation-only final scope.

## 20. Explicit Non-Actions

No source, test, YAML/data, result, checkpoint, console log, installed HARL, or
Conda package was modified. No AppLauncher, Isaac Sim, environment, playback,
evaluation, checkpoint tensor load, training, continuation, new seed, new
condition, stochastic action, GUI/video, staging, or commit occurred.

## 21. Post-Commit Boundary

The only immediate recommendation is for the user to review, manually stage
the exact seven Markdown files, and manually commit with the reviewed message.
No new experiment is authorized. A later GPT-reviewed roadmap decision may
return to viewpoint-scale expansion, real robot/capability constraints, or
paper-level evaluation design without this phase choosing among them.
