# Phase A4b Checkpoint Entry Semantic Guard Integration Report

## 1. Classification

```text
classification:
  PHASE-A4B-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

A4b:
  complete by pure metadata, callback-spy, regression, and source/AST evidence
  stopped for GPT/user review

A5/A6:
  not entered
  not authorized

Phase B0/B/C/D/E:
  not entered
```

Phase A4b connects the existing V2/V3 semantic authorities to checkpoint save,
load, playback, and offline-audit boundaries. It does not make V3
checkpoint-ready. A valid V3 interface descriptor remains audit-only and never
authorizes checkpoint tensor I/O.

## 2. Authorization and scope

The authorized implementation scope was limited to:

- one pure shared checkpoint-entry guard;
- minimal integration in the existing save, load, and training-run audit
  modules;
- minimal entry-purpose wiring in the two existing playback/evaluation scripts;
- one pure/temp-directory integration suite;
- this report and the root handoff update performed separately by the root
  agent.

The implementation did not change the V2 contract, V3 contract, semantic
dispatcher, A1--A3x authorities, environment, wrapper, resolver, runner,
trainer, buffer, reward runtime, scenario configuration, installed HARL, or any
checkpoint weights.

No training, playback, evaluation, diagnosis, AppLauncher, Isaac simulation,
model construction, state-dict inventory extraction, real checkpoint
continuation, or real checkpoint tensor serialization/deserialization was run.

## 3. Starting repository state

The recorded A4b preflight state was:

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

starting worktree path count:
  42

starting cohort:
  known A1--A4a worktree

index:
  empty

unknown paths:
  none
```

The worktree was preserved in place. No reset, clean, checkout, inherited-file
deletion, or commit was performed.

The final root-owned repository audit after the report and
`TASK_PROGRESS.md` updates is:

```text
ending HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6

ending status/path count:
  48
  13 tracked modified + 35 untracked

ending diff name/status:
  expected inherited cohort plus the authorized A4b paths

ending index state:
  empty

ending git diff --check:
  exit 0
  inherited LF/CRLF conversion notices only

ending unknown/non-authorized paths:
  none
```

## 4. Existing save/load/playback/audit inventory

Before A4b, `AssignmentCheckpointSaveCoordinator.save_checkpoint()` was the
native V2 save authority. Its substantive path inspected state-dict mappings,
wrote actor/critic/ValueNorm artifacts, wrote the local contract pair, and
committed `assignment_training_state_manifest.json` last.

`load_assignment_checkpoint()` already owned the V2 load path. For native V2
checkpoints it read the contract pair and completion marker, evaluated V2
compatibility, verified declared files and inventories, called `torch.load`,
then performed strict mutation. For metadata-free checkpoints it used the
explicit, narrow V2 legacy fallback.

Both playback entry points already used the shared loader and had no direct
`torch.load`, `torch.save`, `torch.jit.load`, or `load_state_dict` call:

- `scripts/reinforcement_learning/harl/play_assignment.py`;
- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`.

They did not select actor, critic, or ValueNorm files themselves. Their required
`--dir` value is resolved and passed unchanged to the canonical loader. The
diagnostics helper `_exp_name_from_checkpoint()` only derives a report label;
it is not a load-path selector.

The existing training-run audit was filesystem/metadata based and contained no
checkpoint tensor deserialization. A4b adds the shared semantic guard to its
run-root and child checks without adding tensor I/O.

## 5. Files changed

New production module:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_checkpoint_entry_guard.py`.

Targeted production integrations:

- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_checkpoint_save.py`;
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_checkpoint_load.py`;
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_training_run_audit.py`.

Minimal entry-point integrations:

- `scripts/reinforcement_learning/harl/play_assignment.py`;
- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`.

New pure test and report:

- `scripts/environments/test_assignment_checkpoint_entry_guard_integration.py`;
- `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260808/PHASE_A4B_CHECKPOINT_ENTRY_SEMANTIC_GUARD_INTEGRATION_REPORT.md`.

`TASK_PROGRESS.md` is intentionally outside this report-writing subtask and is
updated separately by the root agent.

## 6. Shared entry-guard architecture

The shared architecture is:

```text
entry request
  -> exact native metadata-pair inspection
  -> strict metadata read when present
  -> generic V2/V3 dispatcher parse
  -> version-native canonical bytes and SHA-256
  -> exact stored/computed fingerprint comparison
  -> entry-purpose plus family-native semantic evaluation
  -> typed AssignmentCheckpointEntryGuardResult
  -> require_checkpoint_weight_io_authorized()
  -> existing V2 tensor path only after authorization
```

The guard is a canonical-only, pure module. It imports no torch, HARL, Isaac,
runner, trainer, environment, or model code. Semantic schema and compatibility
remain owned by:

- `assignment_checkpoint_contract.py` for V2;
- `assignment_checkpoint_contract_v3.py` for V3;
- `assignment_checkpoint_semantic_dispatch.py` for version dispatch.

The exact entry-purpose order is:

```text
SAVE
LOAD_CONTINUATION
LOAD_EVALUATION
LOAD_PLAYBACK
OFFLINE_AUDIT
```

The corresponding values are `save`, `load_continuation`, `load_evaluation`,
`load_playback`, and `offline_audit`.

`AssignmentCheckpointEntryGuardResult` carries metadata mode, manifest
version/kind, semantic family, requested purpose, fingerprint status, semantic
and weight authorization, fallback identity, classification/reason, the typed
family-native semantic decision, parsed manifest, and stored fingerprint.

## 7. Native metadata-pair states

The exact native pair is:

```text
manifest:
  assignment_contract_manifest.json

fingerprint:
  assignment_contract_fingerprint.txt

completion marker, not part of the pair:
  assignment_training_state_manifest.json
```

The exact metadata-mode order and rules are:

```text
BOTH_PRESENT / both_present:
  strict native semantic guard

BOTH_ABSENT / both_absent:
  no semantic manifest is synthesized
  only the unchanged explicit V2 legacy boundary may continue

PARTIAL / partial:
  typed fail-closed error
```

The manifest file must be exact version-native canonical UTF-8 JSON plus one
LF. The fingerprint must be exactly 64 lowercase hexadecimal SHA-256
characters plus one LF. Empty, uppercase, non-hexadecimal, wrong-length,
missing-LF, extra-LF, mismatched, malformed, non-canonical, and unknown-version
metadata are rejected.

## 8. Guard-before-I/O ordering

For save, the semantic guard is the first substantive operation in
`save_checkpoint()`. A rejected request stops before:

- manifest field access used by the V2 save implementation;
- state-dict inventory construction;
- checkpoint-directory creation;
- marker invalidation;
- `_atomic_torch_save` or `torch.save`;
- actor, critic, ValueNorm, manifest, fingerprint, or completion-marker
  artifacts.

After path-layout validation, any already present run-root or selected-child
native pair is also strictly read through the shared guard and compared with
the incoming V2 fingerprint before state-dict inventory work. Partial,
corrupt, V3, ready-kind, unknown-version, or semantically different existing
metadata therefore fails before tensor inspection or artifact write.

For supported load purposes, `_guard_assignment_checkpoint_load_entry()` runs
before `_read_native_checkpoint()` and `_native_load()`. Native metadata
parse/canonical/fingerprint validation occurs before the V2 completion marker
is consumed for semantic compatibility. Weight authorization precedes the old
artifact hash/inventory path, `torch.load`, and `_strict_mutate_all()`.

The already unsupported V2 fine-tuning and exact-resume purposes retain their
earlier hard rejection before the native load path. They still cannot reach
tensor I/O.

## 9. V2 native compatibility preservation

Native V2 metadata is parsed and fingerprinted by the generic guard, then
delegated through the semantic dispatcher to the unchanged V2
`evaluate_compatibility()` authority. The existing loader repeats its V2
completion-marker, artifact, and mutation checks after the guard allows the
request; it does not replace the proposal with a hash-only decision.

The A4b suite compares the complete direct V2 decision mapping against the
guard-carried typed V2 decision for:

- legacy native normal evaluation;
- Contract-C native normal evaluation;
- profile/evaluation-semantic mismatch;
- structural mismatch;
- validated-continuation mismatch;
- the named Contract-C-to-lifecycle-ablation evaluation.

Allowed bit, classification, requested purpose, complete ordered mismatch
records, first mismatch, reason, acknowledgement, and next action remain exact.

The entry/compatibility-purpose matrix additionally proves:

- `LOAD_EVALUATION + STRUCTURAL_INSPECTION` remains allowed for the existing
  V2 weights-only structural inventory path;
- `LOAD_PLAYBACK + STRUCTURAL_INSPECTION` is denied;
- `LOAD_CONTINUATION + NORMAL_EVALUATION` is denied;
- `OFFLINE_AUDIT + STRUCTURAL_INSPECTION` may be semantically valid but never
  authorizes weight I/O.

## 10. V2 metadata-free fallback preservation

`BOTH_ABSENT` returns a closed guard result with fallback identity:

```text
legacy_v2_metadata_absence_fallback
```

The loader permits further fallback consideration only when the current
manifest is an existing typed V2 `AssignmentCheckpointContractManifest`.
V3/event expectations are rejected before `_read_native_checkpoint()` and
`_legacy_load()` and therefore cannot synthesize or downgrade to V2.

The unchanged V2 decision remains:

```text
classification:
  legacy_evaluation_fallback

required conditions:
  NORMAL_EVALUATION
  current profile == legacy
  resolver disabled
  explicit --allow_unversioned_legacy_checkpoint
  actor dimension 909
  action dimension 51
  noop id 50
```

The structural-inspection-only historical branch is also preserved. No new
metadata-free profile, directory convention, or inferred V3 identity was
added.

A discovered integration gap was fixed during the pure suite: a metadata-free
directory with a V3 current expectation initially reached the legacy function.
The final loader now rejects it before both the native and legacy loader seams.

The loader also rejects the case where a recognized run root has a native pair
but the selected `models`, `best_model`, or recognized episode child has no
local pair. That state cannot be reinterpreted as legacy.

## 11. V3 interface save behavior

A V3 `interface_semantic_descriptor` is parsed and fingerprinted, but the save
entry result is:

```text
semantic_allowed:
  false

weight_io_authorized:
  false

classification:
  v3_interface_weight_use_denied
```

The save coordinator converts an in-memory manifest to a mapping, invokes the
shared save guard, and requires weight authorization before touching V2
state-dict data or writing any checkpoint artifact. Supplying an interface
descriptor cannot create actor, critic, ValueNorm, metadata, or marker
artifacts.

No V3 checkpoint-ready manifest was created. A claimed
`checkpoint_ready_manifest` remains rejected by the frozen V3 authority.

## 12. V3 interface load/continuation/evaluation/playback behavior

For each of the following entry purposes, a valid V3 interface descriptor is
fingerprint-valid but returns a typed denied guard result:

```text
LOAD_CONTINUATION
LOAD_EVALUATION
LOAD_PLAYBACK
```

Each result retains the typed V3 interface-audit semantic decision, which says
that the interface is valid while runtime and weight use are unauthorized.
`require_checkpoint_weight_io_authorized()` then raises a typed
`AssignmentCheckpointEntryPurposeDeniedError` carrying that same result.

There is no V3-to-V2 downgrade and no attempt to inspect weights after V3
denial. Claimed V3 ready kind, unknown family/version, and corrupt V3 metadata
fail before the old native loader.

## 13. V3 offline-audit behavior

`audit_assignment_checkpoint_semantic_metadata(checkpoint_directory)` invokes
the shared guard with `OFFLINE_AUDIT` and returns metadata-only wording that
distinguishes interface validity from runtime/weight readiness.

For the frozen V3 interface fixture, the output is:

```text
metadata_mode:
  both_present
semantic_family:
  v3
requested_purpose:
  offline_audit
fingerprint_verified:
  true
semantic_allowed:
  true
weight_io_authorized:
  false
interface_status:
  interface-valid
runtime_ready:
  false
runtime_status:
  runtime-not-ready
checkpoint_ready:
  false
weight_status:
  weight-unauthorized
```

The full training-run audit now invokes this helper for the run-root and native
checkpoint children. A V3 interface run-root is explicitly reported as valid
semantic interface metadata but as `v3_interface_not_checkpoint_ready`; its
weight-artifact/generation checks are marked not applicable rather than being
presented as successful evaluation or continuation evidence.

For the historical bare-import offline CLI, the audit installs namespace-only
canonical package shells and loads only the ordered pure authority modules. It
does not import the normal `isaaclab_tasks` registration package, environment,
AppLauncher, or HARL model code. Existing namespace roots and canonical module
keys must resolve to the current repository paths; a stale installed or second
repository copy is rejected rather than mixed into the authority graph.

The general training-run audit deliberately retains its existing preflight
requirement for `models/` and `best_model/`. Consequently a directory that
contains only an interface descriptor uses the metadata-only helper; the
full-run V3 branch is a forensic classification for a V2-shaped run layout and
does not scan V3-associated weight artifacts as if they were usable.

## 14. Partial/corrupt metadata behavior

The final fail-closed behavior is:

| Metadata state | Result |
| --- | --- |
| Valid V2 pair | evaluate unchanged V2 semantics |
| Valid V3 interface pair | offline audit only; all weights denied |
| Both absent | unchanged explicit V2 legacy boundary only |
| Manifest only | reject as `PARTIAL` |
| Fingerprint only | reject as `PARTIAL` |
| Malformed/non-object manifest | reject |
| Non-canonical manifest bytes | reject |
| Malformed fingerprint | reject |
| Fingerprint mismatch | reject |
| Unknown version | reject |
| V3 ready kind claim | reject |
| Present invalid V3 | reject; no V2 fallback |
| Run-root present/local absent | reject; no legacy fallback |

No filename, directory layout, or weight content is used to guess a semantic
family when native metadata is present.

## 15. Playback and diagnostics integration

`play_assignment.py` passes:

```text
entry_purpose:
  AssignmentCheckpointEntryPurpose.LOAD_PLAYBACK
```

`evaluate_assignment_rl_playback_diagnostics.py` passes:

```text
entry_purpose:
  AssignmentCheckpointEntryPurpose.LOAD_EVALUATION
```

Both retain their unchanged V2 `NORMAL_EVALUATION` or named-ablation
`CompatibilityPurpose`. They do not import V3 authority or semantic dispatcher
logic and do not parse checkpoint metadata themselves.

Important ordering nuance: both scripts instantiate AppLauncher before the
HARL/task/checkpoint-loader imports required by their runtime topology. They
also construct the normal playback actors before building the current V2
manifest and calling the loader. Therefore the proven claim is:

```text
post-AppLauncher
pre-checkpoint-tensor-deserialization
pre-load_state_dict mutation
pre-policy rollout/reset/act/step
```

It is not a claim that invalid checkpoint metadata is rejected before
AppLauncher starts. The A4b suite does not import or execute either script; it
uses AST/source inspection.

## 16. Save-path integration

The save coordinator preserves the existing V2 path and adds one first-entry
semantic barrier. The guard recognizes an existing V2 manifest, validates its
canonical family and in-memory fingerprint, and authorizes the established V2
save coordinator. It does not redefine V2 save semantics.

For V3 interface input, spies prove zero calls to:

- `build_tensor_inventory_from_state_dict`;
- `_atomic_torch_save`;
- `torch.save`.

The rejected test directory is not created, and there are no actor, critic,
ValueNorm, manifest, fingerprint, or completion-marker artifacts.

Existing run-root and child metadata are guarded separately before inventory.
The test matrix injects mismatched, partial, V3 interface, unknown-version, and
ready-kind existing metadata and proves zero inventory/write callbacks. A
matching V2 pair remains on the established save path.

## 17. Load-path integration

The load API now accepts the glue-only `entry_purpose` while retaining the
existing V2 `purpose`. Existing callers that omit the new argument receive a
purpose derived from the unchanged V2 request; the two playback callers pass
their intent explicitly.

For `BOTH_PRESENT`, the load order is:

1. resolve and validate entry intent;
2. check local/run-root metadata authority;
3. read exact local manifest/fingerprint bytes;
4. dispatcher parse/canonical/hash and fingerprint match;
5. for V2 only, read the completion marker after pair integrity; V3 never
   consumes or requires that V2 marker;
6. evaluate family-native semantics and require weight authorization;
7. invoke the existing V2 native loader;
8. verify artifact files/inventories;
9. deserialize with `torch.load`;
10. mutate live modules strictly and atomically with rollback.

The pure allowed-path seam proves an authorized V2 request reaches
`_native_load` exactly once. Denied cases reach neither `_native_load` nor the
legacy loader. The caller retains the successful native guard result: if the
pair disappears before the established second reader, the load now fails
closed instead of falling through to legacy.

## 18. Test and spy evidence

The new pure suite is:

```text
scripts/environments/test_assignment_checkpoint_entry_guard_integration.py

result:
  10/10 passed
```

Its ten groups cover:

1. native pair states and strict corruption;
2. full V2 direct-versus-guard decision equivalence;
3. V2 entry/compatibility-purpose matrix;
4. V3 frozen interface audit-only and all weight-purpose denials;
5. blocked V3 save before inventory/artifacts;
6. load guard before native tensor path;
7. legacy fallback non-expansion and run-root authority;
8. V3 metadata-only offline-audit output;
9. playback/diagnostics AST routing and no bypass;
10. in-process and clean-child side-effect snapshots.

The save group also covers already-present run-root metadata that is
mismatched, partial, V3 interface, unknown-version, or ready-kind. Each case
reaches zero inventory and write callbacks and leaves the filesystem snapshot
unchanged.

The load rejection spy matrix covers V3 evaluation, continuation, and playback;
fingerprint mismatch; partial metadata; unknown version; and V3 ready-kind
claim. Every rejected case records zero calls to `_read_native_checkpoint`,
`_native_load`, `_legacy_load`, `torch.load`, and the
`load_state_dict`-like `_strict_mutate_all` seam. It also covers a malformed V2
training-state marker beside a V3 pair and a present-pair-to-missing-pair
TOCTOU seam; neither can enter legacy fallback.

Offline-audit tests exercise both the metadata-only helper and the V3
`_audit_checkpoints()` branch. They fix the
`v3_interface_not_checkpoint_ready` hard error and not-applicable child,
artifact, and generation summaries; fingerprint mismatch, unknown version,
ready-kind, and partial metadata all fail through the audit wrapper with zero
tensor callbacks.

The clean child proves unchanged Python/torch RNG state, cwd, environment,
`sys.path`, root and named loggers, and cwd files. It also proves no Isaac,
AppLauncher, HARL, environment, model construction, `torch.load`, `torch.save`,
or `load_state_dict` operation. A poisoned canonical dependency `__file__`
fixture additionally proves that the offline-audit fast path rejects mixed or
stale semantic authority sources.

Required regression evidence is:

```text
A4b entry-guard integration:
  10/10

A4a semantic dispatcher:
  12/12

A3x event profile / MRTA / transition:
  9/9 + 13/13 + 12/12

other A1--A3:
  team reward 6/6
  diagnostics 8/8
  profile 16/16
  production wiring 10/10
  initial condition 9/9

A1--A3x excluding A4a and V2 core:
  83/83

V2 checkpoint core:
  28/28

training-run audit extra regression:
  4/4
```

The final joint `py_compile` passed for the guard, save, load, audit, both
entry scripts, and the new A4b suite. All effective Python validations used
the required `C:\isaacenvs\isaac45_harl\python.exe` through the fully
specified conda command.

## 19. V2 golden preservation

The V2 source and frozen canonical fixtures remain exact:

```text
assignment_checkpoint_contract.py SHA-256:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0

legacy canonical bytes:
  5509

legacy SHA-256:
  1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f

Contract-C canonical bytes:
  7234

Contract-C SHA-256:
  88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398
```

The V2 contract source was not modified. The guard does not collapse V2
compatibility to a fingerprint match; complete direct decision mappings remain
identical.

## 20. V3 interface golden preservation

The frozen V3 interface descriptor remains:

```text
canonical byte length:
  67794

interface SHA-256:
  03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a
```

The V3 schema, authority bindings, canonicalization, and fingerprint were not
modified. The hash is regression evidence, not a runtime allowlist. The guard
computes version-native fingerprints through the dispatcher.

## 21. Side-effect and scope audit

The implementation and verification performed no real checkpoint tensor I/O,
state-dict inventory, live module mutation, optimizer operation, forward or
backward pass, actor/critic construction, training, playback, evaluation,
diagnosis, Isaac launch, or AppLauncher execution. Installed HARL is unchanged.
No commit was created.

Only temporary manifest/fingerprint text metadata was created by the A4b suite,
inside `TemporaryDirectory`; it was removed automatically. No real tensor
checkpoint artifact was created or inspected.

One small command-scope deviation is recorded transparently: the root agent
once issued an unspecified-environment `python -c` line-count probe. The target
report file did not yet exist, the command failed, and it performed no write,
runtime, model, tensor, Isaac, training, playback, or evaluation action. All
effective Python verification commands after that probe used the explicitly
required conda environment.

No `TASK_PROGRESS` archive is required for this targeted in-place phase update;
the root handoff update is not a substantial condensation.

## 22. Deferred A5/A6/runtime work

Still deferred and unauthorized:

- V3 `checkpoint_ready_manifest` implementation;
- V3 weight save/load;
- state-dict semantic inventory for V3;
- runtime-evidence schema and proof;
- selection of the eleven unresolved method parameters;
- event-gated MRTA runtime behavior;
- event observation/action-mask/decision-valid buffer and HAPPO changes;
- real model/checkpoint compatibility experiments;
- real continuation, playback, training, evaluation, or ablation.

No Phase A4b result should be read as evidence that an event-profile checkpoint
can be saved, loaded, continued, evaluated, or played.

## 23. Risks and blockers

No architectural blocker was found for the narrow A4b semantic guard. Remaining
risks are:

1. playback rejection is post-AppLauncher because of the existing entry-point
   import topology; only pre-checkpoint-tensor ordering is proven;
2. playback actors are constructed to build the current V2 manifest before the
   loader guard, although the loader itself constructs no model and rejected
   paths perform no checkpoint tensor I/O;
3. canonical production imports use the shared guard, while historical bare
   imports retain a narrow V2-only compatibility path for existing pure tests;
4. native V2 metadata is deliberately revalidated by the established loader
   after the generic guard, increasing complexity but preserving fail-closed
   checks and V2 behavior;
5. current evidence is pure/temp-directory/static and does not replace later
   runtime validation;
6. V3 readiness and weight inventory remain intentionally unavailable.
7. the full training-run audit still requires its historical V2-shaped
   directory preflight; interface-only directories use the dedicated
   metadata-only audit helper, and V3 artifacts are intentionally not treated
   as a forensic weight inventory.

These are review considerations, not authorization to enter A5, A6, or a
runtime phase.

## 24. Final classification

```text
classification:
  PHASE-A4B-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

checkpoint semantic guard:
  integrated at save/load/playback/offline-audit boundaries

V2 native behavior:
  preserved

V2 metadata-free fallback:
  preserved
  not expanded

V3 interface:
  recognizable and valid for offline semantic audit only

V3 save/load/continuation/evaluation/playback:
  fail-closed

V3 checkpoint-ready:
  unavailable

checkpoint tensor I/O during A4b verification:
  none

runtime event profile:
  unavailable

Isaac/AppLauncher:
  not run

training/playback/evaluation:
  not run

installed HARL:
  unchanged

commit:
  none

A4b:
  stopped for GPT/user review

A5/A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```
