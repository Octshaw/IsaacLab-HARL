# Phase 9G-8G-1R-0: Runtime ValueNorm Checkpoint Root-Cause and Adapter Design

Date: 2026-07-10

## Classification

```text
ADAPTER-DESIGN-READY
```

The empty runtime mapping is reproduced with the installed HARL `ValueNorm` on
the exact CUDA construction used by the assignment runner. The CPU synthetic
blind spot is reproduced and explained. A project-local strict export/import
adapter, its manifest requirements, and its save/load test matrix are frozen
below. No installed HARL modification is required.

## Scope And Inputs

Read completely:

```text
AgentRead/AGENTS.md
AgentRead/TASK_PROGRESS.md
AgentRead/20260710/PHASE9G8G1_CONTROLLED_TRAINING_SMOKE_EXECUTION_REPORT.md
AgentRead/20260710/PHASE9G8G0_CONTROLLED_TRAINING_SMOKE_DESIGN_AND_PREFLIGHT.md
AgentRead/20260709/PHASE9G8F5_CHECKPOINT_SAVE_LOAD_CONTINUATION_SMOKE_REPORT.md
AgentRead/20260709/PHASE9G8F4_ACTOR_CRITIC_BUFFER_FORWARD_BACKWARD_READINESS_REPORT.md
```

Inspected project boundaries:

```text
assignment_checkpoint_contract.py
assignment_checkpoint_save.py
assignment_checkpoint_load.py
assignment_harl_training.py
scripts/environments/test_assignment_checkpoint_save_metadata_integration.py
scripts/environments/test_assignment_checkpoint_all_loader_integration.py
scripts/environments/test_assignment_actor_critic_buffer_forward_backward_readiness.py
scripts/environments/test_assignment_checkpoint_save_load_continuation_smoke.py
```

Installed HARL was inspected read-only at:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\common\valuenorm.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\algorithms\critics\v_critic.py
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\runners\on_policy_base_runner.py
```

## Failure Evidence And Call Chain

The accepted 9G-8G-1 run established that the lifecycle resolver, Contract C
mask, actor/shared observation schemas, historical available-actions, HAPPO
actor update, VCritic loss/update, fresh result directory, state-dict-only
setting, and absence of continuation all passed through the first 300-step
update. The failure was later, at the first best-checkpoint save.

The exact project call chain is:

```text
OnPolicyBaseRunner.run():295-297
  -> AssignmentOnPolicyHARunner.save(best_model):605-675
  -> self.value_normalizer.state_dict():659-663
  -> AssignmentCheckpointSaveCoordinator.save_checkpoint():805+
  -> build_tensor_inventory_from_state_dict(..., "value normalizer"):846-852
  -> empty-mapping rejection: assignment_checkpoint_save.py:501-502
```

`AssignmentOnPolicyHARunner.__init__()` constructs a non-null normalizer when
`use_valuenorm` is true. The real smoke used `ValueNorm(1, device=cuda:0)` at
`assignment_harl_training.py:549-552`. Installed `VCritic.cal_value_loss()`
calls `value_normalizer.update(return_batch)` before normalization at
`v_critic.py:90-95`, and the smoke emitted finite critic loss/gradient metrics.
Thus runtime ValueNorm state existed and was updated before the coordinator
received its empty mapping.

## Installed HARL ValueNorm Audit

`ValueNorm` inherits `torch.nn.Module`. Its constructor is:

```python
ValueNorm(
    input_shape,
    norm_axes=1,
    beta=0.99999,
    per_element_update=False,
    epsilon=1e-5,
    device=torch.device("cpu"),
)
```

It stores immutable semantic configuration in `input_shape`, `norm_axes`,
`beta`, `per_element_update`, and `epsilon`; `tpdv` is a runtime conversion
dictionary fixed by this implementation to `dtype=torch.float32` and the passed
device. It declares no buffers.

| Mutable field | Source expression | Runtime shape for runner `ValueNorm(1)` | Update behavior |
| --- | --- | --- | --- |
| `running_mean` | `nn.Parameter(torch.zeros(input_shape), requires_grad=False).to(**tpdv)` | `[1]` | in-place EMA mean |
| `running_mean_sq` | same pattern | `[1]` | in-place EMA squared mean |
| `debiasing_term` | `nn.Parameter(torch.tensor(0.0), requires_grad=False).to(**tpdv)` | `[]` | in-place EMA debias term |

For input `x`, the implementation computes `batch_mean` and `batch_sq_mean`
over dimensions `range(norm_axes)`. Its weight is `beta`, or
`beta ** prod(x.size()[:norm_axes])` when `per_element_update` is true. It then
mutates each field with `field = field * weight + batch_value * (1-weight)`.
`running_mean_var()` divides by `debiasing_term.clamp(min=epsilon)` and clamps
the derived variance to at least `1e-2`. `normalize()` subtracts that mean and
divides by the square root of the variance; `denormalize()` performs the inverse.
All input operations first apply `.to(**tpdv)`.

The three fields have `requires_grad=False`. `update()` is decorated
`@torch.no_grad()` and uses `mul_`/`add_`, so it mutates existing tensor objects
instead of replacing them.

## Isolated Reproduction Results

An isolated temporary script used the installed `harl.common.valuenorm.ValueNorm`
with PyTorch `2.5.1+cu121`. It called direct `update`, `normalize`, and
`denormalize` with finite tensors. The temporary script was removed after use.

| Construction | Mutable attribute type | named parameters | named buffers | `state_dict()` | Update / round trip |
| --- | --- | --- | --- | --- | --- |
| CPU, default float32, no effective `.to()` conversion | `nn.Parameter` | all three canonical fields | none | three keys | all fields changed in place; finite; zero reconstruction error |
| CPU, forced float64 default then HARL `.to(float32)` | `torch.Tensor` | none | none | empty | all fields changed in place; finite; zero reconstruction error |
| CUDA `ValueNorm(1, device=cuda:0)` | `torch.Tensor` on `cuda:0` | none | none | empty | all fields changed in place; finite; zero reconstruction error |

The CPU effective-conversion case is produced without altering HARL by setting
PyTorch's default dtype to float64 only during construction. HARL creates a
float64 Parameter and then effectively converts it to its fixed float32 `tpdv`.
The real runner creates CPU float32 Parameters and then effectively converts
them to CUDA float32.

For all three construction cases, the field shapes were `[1]`, `[1]`, and `[]`
in canonical order `running_mean`, `running_mean_sq`, `debiasing_term`; all
fields had `requires_grad=False`. Their Python object identities were unchanged
by `update()`, and state-dictionary visibility did not change after update.

The PyTorch control reproduction independently showed:

| Assignment form | Attribute type | named parameters | `state_dict()` |
| --- | --- | --- | --- |
| `self.value = nn.Parameter(...)` | `Parameter` | `value` | `value` |
| `self.value = nn.Parameter(...).to(dtype=torch.float64)` | `Tensor` | none | empty |

On the CUDA runtime-style object, `load_state_dict()` with the otherwise
canonical three-field mapping fails strictly with all keys reported as
unexpected. This proves that both generic export and generic strict restore are
invalid for the real runner object.

## Proven Root Cause

The root cause is **effective device or dtype conversion after Parameter
construction**, specifically HARL's `nn.Parameter(...).to(**self.tpdv)` pattern.
When `.to()` is a no-op, it returns the original `Parameter`, preserving module
registration. When it changes device or dtype, it returns a plain `Tensor`; the
subsequent attribute assignment does not register it as a parameter or buffer.

This is registration/object-replacement behavior, not a resolver, mask,
observation, action-history, HAPPO, VCritic-loss, directory, full-model, or
continuation defect. The detached tensors continue to be live mutable runtime
state, which explains the successful critic update and finite normalize/
denormalize behavior despite the empty `state_dict()`.

## Phase 9G-8F-5 Blind Spot

Phase 9G-8F-4 defines `DEVICE = torch.device("cpu")` and constructs the real
installed class as `ValueNorm(1, device=DEVICE)`. Phase 9G-8F-5 imports that
same CPU `_construct_components()` helper. Therefore both source and target
ValueNorms used a no-op float32 CPU `.to()` conversion, remained registered
Parameters, exposed the three normal `state_dict` keys, and allowed direct
`load_state_dict(strict=True)`.

The 8F-5 smoke did use the real extraction path:

```python
value_normalizer_state_dict=components.value_normalizer.state_dict()
```

It did not use a fake or prebuilt ValueNorm mapping in that real CPU smoke. The
generic save-metadata test does use synthetic tensor dictionaries, and the
all-loader integration test uses tracking test modules; neither test exercised
installed CUDA ValueNorm registration. Thus 8F-5 passed because its CPU
conversion was a no-op, not because it covered the CUDA runtime construction.

## Frozen ValueNorm Checkpoint State

The `value_normalizer.pt` artifact must remain a plain, deterministic ordered
tensor mapping. Its complete mutable state is exactly:

| Canonical key | Live attribute | Shape rule | Dtype rule | Meaning |
| --- | --- | --- | --- | --- |
| `running_mean` | `running_mean` | exact target attribute shape; runner `[1]` | exact target dtype, currently `torch.float32` | exponentially weighted raw mean |
| `running_mean_sq` | `running_mean_sq` | exact target attribute shape; runner `[1]` | exact target dtype, currently `torch.float32` | exponentially weighted raw squared mean |
| `debiasing_term` | `debiasing_term` | exact target attribute shape; runner `[]` | exact target dtype, currently `torch.float32` | exponential debias denominator |

All three fields change during every installed ValueNorm update, must be tensors,
must be finite, and must be preserved exactly. No optimizer, device identifier,
`__dict__`, module registration metadata, or unrelated object state belongs in
the artifact.

The immutable checkpoint contract must capture these semantics separately from
the mutable tensor artifact:

```text
adapter_contract_version: harl_valuenorm_runtime_state_v1
class_path: harl.common.valuenorm.ValueNorm
canonical_state_keys:
  running_mean
  running_mean_sq
  debiasing_term
input_shape: [1]
norm_axes: 1
beta: 0.99999
epsilon: 0.00001
per_element_update: false
tensor_dtype: torch.float32
```

`device` is deliberately excluded from immutable compatibility. Exports are
CPU tensors, and restoration may transfer only between CPU and the compatible
live target device without changing dtype.

## Frozen Project-Side Adapter

The next implementation phase should add a project-local module named
`assignment_value_normalizer_checkpoint.py` unless a clearer local name is
established during implementation. Its responsibilities are separated as:

```python
export_value_normalizer_checkpoint_state(value_normalizer) -> OrderedDict[str, Tensor]
inspect_value_normalizer_target(value_normalizer) -> ValueNormalizerTargetInventory
restore_value_normalizer_checkpoint_state(
    value_normalizer,
    checkpoint_state,
    *,
    strict: bool = True,
) -> None
```

The canonical order is fixed as `running_mean`, `running_mean_sq`, then
`debiasing_term`.

### Export Contract

Export must require a non-null ValueNorm when the immutable contract enables it;
read only the three named live attributes; require each to be a tensor; reject
missing fields, an empty mapping, nonfinite values, and unexpected layout. It
must `detach().clone().cpu()` every tensor, preserve its dtype, return an
`OrderedDict` in canonical order, and never mutate the live ValueNorm.

### Target Inspection Contract

Inspection must not mutate the target. It must require the exact three
attributes and accept either `Tensor` or `Parameter` attribute objects. It must
record canonical field shape, dtype, and device separately; confirm all fields
share the expected target dtype/device; and reject a class/layout inconsistent
with the frozen HARL ValueNorm contract. It must not use `target.state_dict()`.

### Strict Restore And Rollback Contract

Restore must require `strict=True`, exact canonical key equality, tensor values
only, exact shape, exact dtype, and finite values. Device transfer alone is
allowed. It must prevalidate all fields before mutating any field, clone live
target values for rollback, then copy with `torch.no_grad()` and `copy_` into
the existing attributes. It must not use `setattr`, replace an attribute object,
cast dtype, use `strict=False`, or invoke generic `load_state_dict()`.

After copying, it must verify exact imported values on the target device. If a
copy or verification fails, it must restore every field from its backup before
raising a project-specific error. Any rollback failure must be included in that
error. This preserves the target Tensor/Parameter registration and object
identity regardless of the installed HARL construction behavior.

## Save-Side Integration Freeze

The narrow production change is at `assignment_harl_training.py:659-663`:

```text
current:   self.value_normalizer.state_dict()
corrected: export_value_normalizer_checkpoint_state(self.value_normalizer)
```

No other coordinator ownership changes are needed. The adapter output continues
through `AssignmentCheckpointSaveCoordinator.save_checkpoint()` as the existing
plain tensor mapping. It therefore retains the existing atomic
`value_normalizer.pt` filename, `torch.save` path, file size/SHA-256, canonical
tensor key/shape/dtype inventory, inventory SHA-256, child contract pair, and
completion-marker binding. Export/inventory failure occurs before metadata or a
completed checkpoint is committed, preserving the current failure-atomicity
boundary.

## Load-Side Integration Freeze

Validated continuation must retain this ordering:

```text
1. Validate manifest, fingerprint, compatibility, artifact names, and file digests.
2. CPU `weights_only=True` deserialize each declared artifact.
3. Validate every artifact tensor inventory against declared metadata.
4. Prevalidate live actor, critic, and ValueNorm target layouts before mutation.
5. Snapshot actor, critic, and ValueNorm live states for rollback.
6. Strict-load actors and critic; adapter-restore ValueNorm.
7. Verify all writes; rollback every mutated target on any failure.
```

`assignment_checkpoint_load.py` currently uses generic target
`state_dict()` inventory at lines 412-430 and generic strict loading at
438-468. Those paths remain correct for actors and critic only. The ValueNorm
artifact needs a role-specific inspected target using the adapter's target
inventory and a role-specific restore operation.

All target schemas, including ValueNorm's three field shapes/dtypes, must be
validated before actor or critic mutation. The global transaction owns actor and
critic state-dict backups plus an adapter ValueNorm backup. The adapter owns its
field-level rollback during its own restore; the global transaction still
restores all three target categories if any later operation fails. Normal
evaluation and named actor-only ablation remain actor-only and must neither
inspect for mutation nor restore a live ValueNorm.

## Metadata And Schema Decision

The current generic artifact format can be preserved: `value_normalizer.pt`
remains an ordered CPU tensor mapping with the same three canonical keys and
the existing tensor-inventory/file-integrity machinery. However, the current
contract records only `value_norm_enabled`; it does not bind `input_shape`,
`norm_axes`, `beta`, `epsilon`, `per_element_update`, canonical key order, or
the project adapter extraction semantics.

Decision:

```text
a specific contract/schema field and version must change
```

The implementation must introduce a new manifest format version, for example
`assignment_checkpoint_contract_v2`, with an exact immutable
`value_normalizer_contract` object under `training_contract`.

It must include the frozen configuration block above plus:

```text
artifact_state_format: harl_runtime_attribute_tensor_mapping_v1
```

This makes the artifact description truthful: it is a state-dict-compatible
tensor mapping, but not a successful `nn.Module.state_dict()` export on CUDA.
The new ordered object participates in canonical JSON and SHA-256 fingerprinting.
The implementation phase must update all exact-key validators, manifest builders,
compatibility paths, and regression fixtures together; it must not silently add
an unvalidated field to v1.

## Backward Compatibility And Disabled Path

No completed native assignment checkpoint manifest exists under the current
results tree. The Phase 9G-8F synthetic checkpoints were temporary and are gone;
the failed 9G-8G-1 run wrote no checkpoint artifacts. No migration is required
for an artifact that was never validly completed.

For v2 native checkpoints, the loader may accept a registered CPU
`ValueNorm.state_dict()` mapping when it has exactly the frozen canonical keys,
shapes, dtypes, and matching v2 immutable contract. The mapping's origin is not
semantic. Empty mappings remain invalid whenever `value_norm_enabled=true`.
Unversioned legacy actor-evaluation fallback remains actor-only and retains its
existing explicit boundaries; it does not gain ValueNorm continuation support.

When ValueNorm is disabled, the immutable contract records `value_norm_enabled`
as false. No ValueNorm artifact is declared, exported, deserialized, inspected,
or restored. The adapter must not run. Evaluation and continuation continue to
reject a mismatch between the contract's enabled value and the live runtime
presence of a ValueNorm target.

## Corrective Test Matrix

The implementation phase must add or extend project-local tests covering all of
the following without AppLauncher or an assignment environment:

1. Installed HARL registration regression: default CPU, forced CPU effective
   conversion, and CUDA runtime-style construction when CUDA is available;
   assert state-dict visibility and adapter export behavior.
2. Runtime-style export: prove an empty native CUDA `state_dict()` but nonempty
   adapter mapping with exact canonical keys, shapes, dtypes, and finite values.
3. Mutation evidence: after real `ValueNorm.update`, exported state changes and
   `normalize`/`denormalize` remain internally consistent.
4. Round trip: runtime-style source -> adapter export -> weights-only-compatible
   tensor mapping -> fresh runtime-style target -> adapter restore; assert exact
   field equality and identical normalize/denormalize output.
5. Strict rejection: empty/missing/unexpected keys, wrong shape, wrong dtype,
   non-tensor data, NaN/Inf, and incompatible target layout.
6. No mutation on failure: every rejected restore leaves all target fields
   bitwise unchanged.
7. Save coordinator integration: runtime-style converted ValueNorm produces a
   nonempty `value_normalizer.pt` inventory and valid completion marker.
8. Shared loader continuation: prevalidate actors, critic, and ValueNorm; load
   all through one rollback transaction; preserve fresh optimizer semantics.
9. Evaluation isolation: normal evaluation and named ablation never mutate or
   restore ValueNorm.
10. ValueNorm-disabled profile: no artifact or adapter call; native metadata and
    loader behavior stay consistent.
11. Blind-spot closure: extend 8F-5 so CPU no-op construction alone cannot pass
    the checkpoint continuation claim; include forced conversion and CUDA when
    available.

## Required Conclusions

| Question | Frozen answer |
| --- | --- |
| Why is runtime `state_dict()` empty? | Effective `.to(**tpdv)` conversion returns ordinary tensors and loses Module registration. |
| Is this device, dtype, replacement, or registration behavior? | All four are linked: device/dtype conversion replaces the Parameter result with an unregistered Tensor attribute. |
| Why did CPU 8F-5 pass? | Its CPU float32 `.to()` was a no-op, so the original registered Parameters remained visible to generic export/load. |
| Mutable checkpoint tensors | `running_mean`, `running_mean_sq`, `debiasing_term`, in the frozen order. |
| Immutable behavior settings | ValueNorm class/layout, input shape, norm axes, beta, epsilon, per-element mode, fixed tensor dtype, and adapter state-format version. |
| Can artifact inventory remain? | Yes. Preserve `value_normalizer.pt` as an ordered tensor mapping and use the existing inventory/digest coordinator. |
| Does schema change? | Yes. v2 must bind the ValueNorm configuration and project attribute-mapping semantics into the fingerprint. |
| Strict restore and rollback | Prevalidate all values, copy into existing fields without replacement, verify, and restore field/global backups on failure. |
| ValueNorm-disabled behavior | No ValueNorm artifact or adapter call; contract/runtime mismatch remains a hard error. |
| Required evidence before another real smoke | All corrective adapter/save/load/rollback/disabled-path regressions above must pass, then receive review. |

## Design-Phase Validation And Limits

```text
Python interpreter: C:\isaacenvs\isaac45_harl\python.exe
Installed ValueNorm CPU no-op reproduction: PASS
Installed ValueNorm forced CPU conversion reproduction: PASS
Installed ValueNorm CUDA runtime-style reproduction: PASS
PyTorch control registration reproduction: PASS
Direct CUDA strict generic load rejection: PASS
Runtime mutation / normalize / denormalize evidence: PASS
Temporary diagnostic script: removed from system temp directory
```

No production code, tests, YAML/runtime defaults, installed HARL, Conda package,
or checkpoint artifact was modified or created. No AppLauncher, Isaac Sim,
assignment environment, `train.py`, smoke retry, playback, evaluation, visual
inspection, or long training ran.

## Files

Created:

```text
AgentRead/20260710/PHASE9G8G1R0_VALUENORM_CHECKPOINT_ROOT_CAUSE_AND_ADAPTER_DESIGN.md
AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R0_VALUENORM_DESIGN_20260710.md
```

Updated:

```text
AgentRead/TASK_PROGRESS.md
```

Explicitly not modified:

```text
production Python
project tests
YAML/runtime defaults
installed HARL
Conda environment
assignment environment/resolver/Contract C behavior
checkpoint artifacts or failed result directory
```

## Next-Phase Boundary

```text
Phase 9G-8G-1R-1:
ValueNorm Checkpoint Adapter Implementation and Regression
```
