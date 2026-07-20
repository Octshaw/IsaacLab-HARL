# Phase 9G-8I-0A: Controlled Training Post-Run Offline Audit Tool Implementation and Regression

## Classification

```text
OFFLINE-AUDIT-READY
```

The project now has an opt-in, CPU-capable offline audit path for the future Phase 9G-8I-1 timestamped training result. It validates the frozen run contract, all 63 TensorBoard scalar series, technical completion, aggregate trends, and native-v2 checkpoint metadata without constructing the assignment environment or deserializing checkpoint tensors.

This phase did not execute or change the frozen Phase 9G-8I-1 training experiment.

## Starting Baseline

```text
HEAD:
  fadda4248b33d958d3798ef90013f21457358564

git log -1 --oneline:
  fadda424 docs(assignment): define fresh 100k policy-noop training experiment

starting worktree:
  clean

starting git diff --name-status:
  empty

starting git diff --check:
  PASS
```

The committed HEAD is the reviewed Phase 9G-8I-0 documentation baseline.

## Files

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  assignment_training_run_audit.py

scripts/reinforcement_learning/harl/
  audit_assignment_training_run.py

scripts/environments/
  test_assignment_training_run_audit.py

source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
AgentRead/20260720/
  PHASE9G8I0A_CONTROLLED_TRAINING_POSTRUN_OFFLINE_AUDIT_TOOL_IMPLEMENTATION_AND_REGRESSION.md
  TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I0A_OFFLINE_TRAINING_AUDIT_TOOL_20260720.md
```

Updated:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
AgentRead/TASK_PROGRESS.md
```

Explicitly not modified:

```text
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play_assignment.py
assignment_checkpoint_contract.py
assignment_checkpoint_save.py
assignment_lifecycle_training_contract.py
assignment_harl_wrapper.py
resolver, controller, environment, reward, observation, mask, and YAML files
installed HARL and the Conda environment
all existing result directories and checkpoint artifacts
```

## Source Boundaries Inspected

The implementation was based on the real current boundaries rather than assumed schemas:

```text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260720/PHASE9G8I0_POLICY_NOOP_LOAD_IMBALANCE_CONTROLLED_TRAINING_DESIGN_AND_PREFLIGHT.md
AgentRead/20260720/PHASE9G8H2_BOUNDED_PROPOSAL_EFFECTIVE_ATTRIBUTION_PLAYBACK_REPORT.md
AgentRead/20260720/PHASE9G8G1R2T_TIMEOUT_CORRECTED_CONTROLLED_SMOKE_EXECUTION_REPORT.md

scripts/reinforcement_learning/harl/train.py
assignment_checkpoint_contract.py
assignment_checkpoint_save.py
assignment_lifecycle_training_contract.py
installed HARL runner/logger event and save behavior, read-only
```

The accepted native-v2 smoke and historical 100k event inventories were inspected read-only. The current accepted lifecycle smoke contains all 63 current scalar tags at its single update; the historical Phase 9G-8E-2 100k result showed every then-existing scalar at all 333 rollout steps. The frozen current audit therefore requires all 63 current expected tags at every rollout; no expected tag has sparse semantics.

## Module Architecture

The pure implementation is:

```text
assignment_training_run_audit.py
```

Its public boundary is:

```text
AuditExpectations
AuditPreflightError
audit_assignment_training_run(...)
render_assignment_training_run_audit_json(...)
render_assignment_training_run_audit_markdown(...)
```

The processing order is:

```text
safe path/input/output preflight
-> configs.json contract and fresh-start audit
-> optional TensorBoard event discovery/merge/audit
-> optional native-v2 checkpoint metadata/hash audit
-> progress.txt advisory check
-> PASS / PASS WITH WARNINGS / FAIL classification
-> deterministic JSON and Markdown rendering
-> write exactly two files to the explicit output directory
```

The module has no mutable global run state and does not modify its inputs.

## Dependency Boundary

Allowed dependencies used:

```text
Python standard library
TensorBoard event_accumulator, imported lazily only for event scope
project-local pure assignment_checkpoint_contract metadata types/helpers
```

Absent dependencies and behaviors:

```text
no AppLauncher or SimulationApp
no omni or Isaac runtime import
no HARL runner/model import
no GPU or CUDA requirement
no actor, critic, or ValueNorm construction
no checkpoint tensor deserialization
no checkpoint restoration
```

`.pt` artifacts are opened only as binary byte streams for file size and SHA-256 calculation. The implementation contains no checkpoint deserialization call.

## CLI Contract

The thin CLI is:

```text
scripts/reinforcement_learning/harl/audit_assignment_training_run.py
```

Required path and scope arguments:

```text
--run_dir PATH
--output_dir PATH
--scope {full,events,checkpoints}
```

`full` is the default scope. All frozen run expectations are explicit CLI values:

```text
--expected-exp-name
--expected-algorithm
--expected-seed
--expected-num-envs
--expected-num-agents
--expected-num-tasks
--expected-episode-length
--expected-configured-num-env-steps
--expected-final-step
--expected-rollouts
--expected-log-points
--expected-save-interval
--expected-log-interval
--expected-profile
--expected-actor-obs-width
--expected-shared-obs-width
--expected-action-width
--expected-raw-noop-id
```

The task and state type are also exposed as `--expected-task` and `--expected-state-type`, with documented current defaults.

Exit codes:

| Result | Exit code | Output behavior |
| --- | ---: | --- |
| `PASS` | 0 | JSON and Markdown written |
| `PASS WITH WARNINGS` | 0 | JSON and Markdown written |
| `FAIL` after safe preflight | 1 | Complete failure JSON and Markdown written |
| Parser, unsafe preflight, collision, or internal input error | 2/nonzero | No new audit output written |

## Output Schema

Schema version:

```text
phase9g8i0a_assignment_training_run_audit_v1
```

Exactly these tool-owned files are written:

```text
assignment_training_run_audit.json
assignment_training_run_audit.md
```

The JSON authority contains:

```text
schema_version
classification
run_dir
scope
tool_metadata
resolved_expectations
config_audit
tensorboard_audit
checkpoint_audit
progress_audit
evidence
trend_summaries
checkpoint_summaries
artifact_inventory
errors
warnings
limitations
next_recommended_action
output_files
```

Rendering uses standard JSON with `allow_nan=False`; unavailable values are `null`. Nonfinite evidence is represented safely rather than emitted as an invalid JSON numeric token. The Markdown is a compact rendering of the same result and does not dump all scalar points or full manifests.

## Safe Preflight

Hard preflight validates:

```text
run_dir exists and is a directory
run_dir name is one exact timestamped seed directory
experiment parents are never auto-resolved to a child
configs.json exists and parses as an object
logs and at least one event file exist for events/full
models and best_model exist for checkpoints/full
output_dir resolves outside run_dir
neither output file already exists
```

The output directory is not created until all input/path checks and the enabled audit have completed. Output collision is checked again immediately before final write.

## Configuration Audit

The current `configs.json` structure was inspected directly. Canonical checks include:

```text
Args.task
Args.exp_name
Args.algorithm
Args.assignment_rl
Args.seed
Args.num_envs
Args.assignment_episode_length
Args.num_env_steps
Args.save_interval
Args.log_interval
Args.dir
Args.acknowledge_weight_continuation_reset
Args.video
Args.expect_num_viewpoints, when present

Algo Args.seed.seed
Algo Args.train.n_rollout_threads
Algo Args.train.episode_length
Algo Args.train.num_env_steps
Algo Args.train.eval_interval       (the installed runner save interval)
Algo Args.train.log_interval
Algo Args.train.model_dir
Algo Args.eval.use_eval
Algo Args.model.use_recurrent_policy
Algo Args.model.use_naive_recurrent_policy
Algo Args.algo.share_param
```

The lifecycle profile is extracted from the actual `Env Args.config` dataclass representation when it is not present as a direct structured field. EP is recorded as the project runner default when no explicit state-type field exists.

Fresh start requires both directory fields to be null and continuation acknowledgement to be false. The native contract independently binds state-dict serialization, lifecycle profile, sequence mode, architecture, and interface dimensions.

## TensorBoard Audit

### Discovery And Merge

All canonical event files under `logs/` are discovered recursively and sorted by resolved POSIX path. Each file is loaded independently with unlimited scalar retention. Scalar points retain:

```text
tag
global step
wall time
source event file
value
```

Non-scalar summaries are ignored and inventoried. Merge order is deterministic.

Duplicate policy:

```text
same tag/step + identical finite value:
  deterministically retain one and emit a warning

same tag/step + conflicting or nonfinite value:
  hard FAIL with both files and values recorded
```

### Tag And Step Contract

The exact frozen tuple contains 63 canonical tags. Reports divide them into:

```text
expected and present
expected but missing
unexpected extras
present but empty
present with nonfinite values
present with duplicate steps
```

For the future run, every expected tag must contain exactly:

```text
333 points
steps 300, 600, ..., 99900
strictly increasing after deterministic deduplication
no negative or above-final step
```

Configured `num_env_steps=100000` is deliberately not treated as a required step 100000. The source-derived terminal boundary remains 99900.

Unexpected extra scalar tags are warnings. There are no allowed sparse expected tags in the frozen current contract.

### Finiteness And Invariants

Every scalar point is tested with `math.isfinite`. Any NaN or infinity is a hard failure and suppresses trend interpretation.

Cross-tag/range checks include:

```text
assignment_rl.noop_count + assignment_rl.valid_action_count == M
coverage_ratio in [0, 1]
assignment_rl.selected_available_mask in [0, 1]
noop_count in [0, M]
valid_action_count in [0, M]
budget_ratio_mean and budget_ratio_max nonnegative
```

The noop identity uses tolerance `1e-5` and records compared steps, maximum residual, and violating steps. No unsupported reward or loss bounds were invented.

## Trend Contract

For a 333-point result, frozen windows are positional and exact:

| Window | Point indices | Steps |
| --- | --- | --- |
| Early | 1-33 | 300-9900 |
| Middle | 151-183 | 45300-54900 |
| Late | 301-333 | 90300-99900 |

Each principal tag records:

```text
point count
mean/minimum/maximum/population standard deviation
first/last value and step
direction: higher-is-better, lower-is-better, or descriptive-only
direction-aware best observed value and step
final value and step
late mean minus early mean
relative change where meaningful
```

The principal inventory includes coverage, new viewpoints, reward, noop/valid action count, no-progress reward, budget trigger/ratio, all three actor loss/entropy/gradient series, and critic loss/gradient/reward series.

For non-333 evidence, the tool emits a reduced-evidence warning and does not fabricate the frozen middle window. It never labels a policy converged or production-ready.

## Checkpoint Metadata-Only Audit

The checkpoint scope validates:

```text
run-root assignment contract manifest and fingerprint
best_model native contract, fingerprint, and completion marker
models native contract, fingerprint, and completion marker
canonical semantic fingerprint equality across all three locations
manifest format assignment_checkpoint_contract_v2
training-state format assignment_training_state_v1
best kind and final kind
nonnegative generation and final > best
source-derived minimum final generation
canonical actor identities and actor-file mapping
critic and ValueNorm role/file mapping
validated_weight_continuation_candidate classification
state-dict-only unavailable optimizer/counter/RNG/environment/buffer state
```

The source-derived final-generation lower bound is:

```text
1 + floor(rollouts / save_interval)
```

For 333 rollouts and save interval 20, the final generation must be at least 17. This follows the unconditional initial best save, 16 regular save opportunities, and explicit final save generation advancement. Best-save frequency may make the actual generation larger, so no exact final generation is required.

Required child files are:

```text
actor_agent_robot_0.pt
actor_agent_robot_1.pt
actor_agent_robot_2.pt
critic_agent.pt
value_normalizer.pt
assignment_contract_manifest.json
assignment_contract_fingerprint.txt
assignment_training_state_manifest.json
```

Each declared artifact must be nonempty and have a nonempty, digest-valid tensor inventory in metadata. The audit compares actual opaque-byte size and SHA-256 to the completion marker. It never reads tensor contents.

Recursive hard-failure scans cover:

```text
*.tmp / *.partial / *.part and atomic-temp variants
legacy actor_agent0.pt / actor0.pt / numeric actor forms
*_full.pt inherited full-model artifacts
non-v2 assignment contract manifests
```

Unrecognized non-forbidden checkpoint child files are reported as warnings.

## Classification Behavior

```text
PASS:
  every enabled hard check passes and no warning exists

PASS WITH WARNINGS:
  every enabled hard check passes; only noncritical evidence exists

FAIL:
  one or more enabled hard checks fail
```

An absent or empty `progress.txt` is advisory when TensorBoard and native completion evidence are authoritative. Missing or empty checkpoint markers, fingerprint/hash failures, wrong final steps, missing tags, and nonfinite values can never be downgraded to warnings.

## Regression Evidence

### Synthetic Success

One complete pure fixture passed through the CLI:

```text
333 rollout steps
63 expected tags at every step
steps 300..99900
all finite values
fresh configs.json
native-v2 run-root/best/final contracts
best generation 0
final generation 17
three opaque actor byte files
one opaque critic byte file
one opaque ValueNorm byte file
all declared sizes/SHA-256/inventory digests exact
no temporary, legacy, or full-model artifacts
```

Assertions passed for classification, exit code, exact output names, JSON parsing, Markdown generation, exact tag/step counts, exact frozen windows, artifact integrity, deterministic repeated rendering, standard finite JSON tokens, and unchanged input-tree byte hashes.

### Failure Matrix

All 31 failure fixtures produced a nonzero CLI result and precise evidence:

| Group | Cases |
| --- | --- |
| Preflight | missing config; missing logs/events; missing best; missing models; output collision; experiment parent |
| Fresh/config | non-null CLI dir; non-null model dir; wrong algorithm; seed; profile; M; N; actor width |
| Events | missing tag; nonfinite scalar; wrong final step; conflicting duplicate; noop invariant; coverage range |
| Checkpoints | wrong kind; invalid generation order; missing actor; critic; ValueNorm; marker; fingerprint mismatch; size mismatch; SHA mismatch |
| Artifact hygiene | temporary artifact; legacy actor filename |

Safe preflight failures wrote no new report. Analysis failures after preflight wrote complete `FAIL` JSON and Markdown reports. A separate identical-duplicate fixture returned `PASS WITH WARNINGS` and exit code 0.

### Architecture Safety

Static/runtime regressions passed for:

```text
no checkpoint deserialization call in module or CLI
no AppLauncher import
no omni/Isaac runtime import
no HARL runner/model import
train.py does not import the audit module/CLI
play_assignment.py does not import the audit module/CLI
input run tree remains byte-identical
output is confined to output_dir
output collision is rejected
success JSON contains no NaN/Infinity token
```

## Existing Project Evidence

Read-only source run:

```text
results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/
assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh/
seed-00001-2026-07-10-15-59-12
```

Checkpoint-only result:

```text
classification: PASS WITH WARNINGS
hard errors: 0
warning: progress_file_empty
best generation: 0
final generation: 2
opaque artifacts validated: 10
```

Output was written outside the repository to:

```text
C:/Users/33506/AppData/Local/Temp/
phase9g8i0a_checkpoint_final_1212c1392bf54517921802f517c292f4/
```

Events-only result:

```text
classification: PASS WITH WARNINGS
hard errors: 0
warnings: non_333_trend_evidence, progress_file_empty
event files: 1
expected tags present: 63/63
nonfinite points: 0
noop + valid-action invariant: PASS
```

Output was written outside the repository to:

```text
C:/Users/33506/AppData/Local/Temp/
phase9g8i0a_event_evidence_97d4425997124511bb6a54cedf8dadd7/
```

The warnings are expected properties of the one-update historical smoke, not audit defects. No existing result file was modified.

## Validation Results

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Commands and results:

```text
python -m py_compile <new module> <new CLI> <new test>
  PASS

python scripts/environments/test_assignment_training_run_audit.py --json
  PASS: 4/4 groups
  synthetic success fixtures: 1
  required failure cases: 31

python scripts/environments/test_assignment_checkpoint_contract_core.py --json
  PASS: 28/28 tests

checkpoint-only accepted-smoke audit
  PASS WITH WARNINGS; 0 hard failures

events-only accepted-smoke audit
  PASS WITH WARNINGS; 0 hard failures

forbidden import/call and training-entry isolation scans
  PASS

The regression source intentionally contains the literal `AppLauncher` only as
the subject of a negative assertion. The audit module and CLI have zero such
imports/references, and all three new Python files have zero Isaac/omni/HARL
runtime imports.

trailing-whitespace scan
  PASS

git diff --check
  PASS
```

No AppLauncher, Isaac environment, policy, checkpoint loader, or GPU process was invoked by these checks.

## Future Phase 9G-8I-1 Audit Command

After the user manually completes the already frozen training command, run this offline command with fresh paths:

```powershell
C:\isaacenvs\isaac45_harl\python.exe `
  scripts\reinforcement_learning\harl\audit_assignment_training_run.py `
  --run_dir <TIMESTAMPED_SEED_RUN_DIR> `
  --output_dir <FRESH_AUDIT_OUTPUT_DIR> `
  --scope full `
  --expected-exp-name assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis `
  --expected-algorithm happo `
  --expected-seed 1 `
  --expected-num-envs 1 `
  --expected-num-agents 3 `
  --expected-num-tasks 50 `
  --expected-episode-length 300 `
  --expected-configured-num-env-steps 100000 `
  --expected-final-step 99900 `
  --expected-rollouts 333 `
  --expected-log-points 333 `
  --expected-save-interval 20 `
  --expected-log-interval 1 `
  --expected-profile lifecycle_contract_c `
  --expected-actor-obs-width 1059 `
  --expected-shared-obs-width 3183 `
  --expected-action-width 51 `
  --expected-raw-noop-id 50
```

This command is offline. It must target the exact timestamped seed child and a new output directory outside that run.

## Limitations

The tool can establish:

```text
technical completion
fresh-start identity
global aggregate trends
aggregate effective-idle/noop trend
actor/critic scalar numerical health
native checkpoint metadata and opaque-byte integrity
```

It cannot establish:

```text
which actor proposed noop
which robot completed each task
per-agent execution/completion fairness
resolver rejection causes
visual behavior
policy convergence
generalization or production readiness
```

Those questions remain subject to a separately reviewed best/final proposal-effective attribution playback phase. The offline report must not be used to infer per-agent participation from aggregate scalars.

## Next Phase Boundary

The only recommended next phase is:

```text
Phase 9G-8I-1:
User-Executed Fresh 100k Controlled Training
```

The user runs the already frozen command manually. After the result exists, run this offline audit and review both outputs before considering any separately authorized best/final attribution playback. Codex must not launch the 100k run automatically.

## Explicit Non-Actions

```text
No training was run.
No playback or evaluation was run.
No AppLauncher or Isaac Sim was launched.
No environment was constructed.
No checkpoint was loaded or restored.
No actor, critic, or ValueNorm was instantiated.
No checkpoint tensor was deserialized.
No training/playback/runtime source behavior changed.
No test or YAML behavior outside the new offline regression changed.
No installed HARL or Conda file changed.
No existing result was modified.
No commit was made.
```
