# TASK_PROGRESS

Compact handoff for assignment-based scan-mobile-manipulator lifecycle training.

## Current Status

Phase 9G-8G-1R-0 completed the ValueNorm checkpoint root-cause and adapter
design audit.

Classification:

```text
ADAPTER-DESIGN-READY
```

The Phase 9G-8G-1 runtime failure is reproduced and explained. Installed HARL
constructs ValueNorm state as `nn.Parameter(...).to(**tpdv)`. A no-op CPU
conversion preserves registered Parameters, while effective dtype conversion and
the real CUDA construction produce unregistered mutable Tensors. Runtime
ValueNorm update/normalization works, but generic `state_dict()` is empty and
generic strict `load_state_dict()` rejects the canonical keys.

## Accepted Runtime Boundary

The one permitted resolver-enabled smoke reached all of the following before
the checkpoint-save failure:

```text
lifecycle_contract_c; HAPPO / EP; feed-forward; share_param=false
M/N = 3/50; actor/shared/action/noop = 1059/3183/51/50
one environment; 300 policy steps; one HAPPO/VCritic update
finite TensorBoard actor, critic, environment, mask, and cooldown metrics
```

The failed boundary is ValueNorm checkpoint-state extraction only. Resolver,
Contract C, lifecycle observations, lifecycle mask, historical-mask replay, and
the first actor/critic update remain valid runtime evidence.

## Frozen Corrective Design

```text
mutable artifact keys:
  running_mean
  running_mean_sq
  debiasing_term

export:
  project-side ordered CPU tensor mapping; detach/clone; finite/nonempty strict

restore:
  prevalidate exact keys/shapes/dtypes; torch.no_grad copy_ into existing fields;
  no setattr, no dtype cast, no generic ValueNorm load_state_dict; rollback on failure

metadata:
  preserve value_normalizer.pt and coordinator inventory/digest flow
  introduce v2 immutable ValueNorm contract/fingerprint binding
```

No completed native manifest is present in the current results tree. The failed
smoke wrote no valid checkpoint, manifest, fingerprint, or completion marker.

## Do Not Do

```text
do not retry the 300-step smoke
do not run general or long resolver-enabled training
do not load or continue from the failed run
do not run playback, evaluation, comparison, or additional seeds
do not modify installed HARL or the Conda environment
do not change resolver, Contract C, observation, mask, or training defaults
```

## Next Step

After review, the next phase is:

```text
Phase 9G-8G-1R-1:
ValueNorm Checkpoint Adapter Implementation and Regression
```

The real training smoke remains prohibited until that implementation and its
runtime-style regression evidence are reviewed.

## Latest Verification

```text
installed ValueNorm CPU no-op reproduction: PASS
forced CPU effective-conversion reproduction: PASS
CUDA runtime-style reproduction: PASS
PyTorch registration control: PASS
direct generic CUDA ValueNorm strict-load rejection: PASS
temporary diagnostic script removed: PASS
```

No production Python, tests, YAML, runtime defaults, installed HARL, or Conda
files changed. No AppLauncher, Isaac Sim, assignment environment, `train.py`,
checkpoint creation/load, playback, evaluation, visual inspection, long
training, or commit occurred in Phase 9G-8G-1R-0.

## Detailed Reports / Archives

```text
AgentRead/20260710/PHASE9G8G1R0_VALUENORM_CHECKPOINT_ROOT_CAUSE_AND_ADAPTER_DESIGN.md
AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R0_VALUENORM_DESIGN_20260710.md
AgentRead/20260710/PHASE9G8G1_CONTROLLED_TRAINING_SMOKE_EXECUTION_REPORT.md
AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1_SMOKE_EXECUTION_20260710.md
AgentRead/20260710/PHASE9G8G0_CONTROLLED_TRAINING_SMOKE_DESIGN_AND_PREFLIGHT.md
```
