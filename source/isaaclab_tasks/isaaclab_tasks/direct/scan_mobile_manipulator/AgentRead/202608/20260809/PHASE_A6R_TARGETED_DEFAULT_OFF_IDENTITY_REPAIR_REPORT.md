# Phase A6-R Targeted Default-Off Identity Repair Report

## 1. Classification

```text
authorization:
  PHASE-A6R-TARGETED-DEFAULT-OFF-REPAIR-AUTHORIZED

classification:
  PHASE-A-PURE-INTERFACE-IDENTITY-DIAGNOSTICS-COMPLETE-AWAITING-GPT-REVIEW

A6-R:
  targeted production repair complete
  four evidence hardenings complete
  pure/static/manifest revalidation complete

Phase A:
  complete to the declared pure/static/manifest evidence level
  stopped for final GPT/user review

runtime identity:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE

B0/B/C/D/E:
  not entered
  not authorized

commit:
  none
```

The dedicated 16-group suite, canonical 143-group matrix, historical 100-group
safe matrix, immutable V2/V3 goldens, and protected production cohort all
passed. This classification makes no runtime-readiness claim.

## 2. Authorization and scope

A6-R authorizes one narrowly bounded production repair plus test-evidence
hardening and documentation closeout. The sole permitted production file is:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  assignment_harl_wrapper.py
```

The production change count must be exactly one file. The repair is limited to
restoring a valid canonical `profile_name` local inside
`_build_assignment_observation_schema_manifest()`.

Permitted supporting work is limited to the A6 dedicated test, this report,
the existing Phase-A final report, and `TASK_PROGRESS.md`. This report does not
authorize changes to profile, observation, mask, resolver, reward, runner,
trainer, buffer, checkpoint semantic authority, environment, scenario data,
installed HARL, or any B0/B/C/D/E runtime path.

Prohibited throughout A6-R:

- Isaac/AppLauncher, `gym.make`, environment reset/step, or wrapper runtime
  smoke requiring Isaac;
- training, actor update, optimizer/minibatch execution, playback, evaluation,
  or runtime diagnosis;
- real checkpoint tensor save/load, model construction, or `load_state_dict`;
- changing V2/V3 goldens or selecting any numeric method parameter;
- modifying installed HARL or creating a commit.

## 3. Original A6 blocker

The original A6 dedicated suite ended at the authorized stop boundary:

```text
original A6 dedicated suite:
  13/15 passed
  exit code: 1

failed groups:
  legacy_observation_shared_action_mask
  contract_c_observation_shared_action_mask

exception:
  NameError: name 'profile_name' is not defined
```

The failure occurred through the public production interface:

```text
AssignmentHarlWrapper.assignment_observation_schema_manifest
→ AssignmentHarlWrapper._build_assignment_observation_schema_manifest()
→ returned mapping evaluates "profile_name": profile_name
```

The public manifest is consumed by checkpoint save, checkpoint load, and
assignment playback. Therefore the failure was a production interface
regression, not a test-only gap. A6 correctly stopped without patching it under
the earlier authorization.

The original blocker and 13/15 history must remain present in the Phase-A final
report after A6-R; the history must not be rewritten as a first-attempt pass.

## 4. Root cause

Before Phase A, the function obtained a string through the wrapper compatibility
mapping:

```python
profile_name = str(
    self._assignment_lifecycle_profile_config["profile_name"]
)
```

Phase A1c correctly moved training-contract dispatch to the resolved-profile
authority:

```python
policy_sequence_contract_for_profile(self._resolved_assignment_profile)
```

During that change, the old compatibility-mapping local was removed, but the
manifest result still contained:

```python
"profile_name": profile_name
```

Python compilation remained valid because the defect was an undefined local at
execution time. Both legacy and Contract-C fake-wrapper manifest access exposed
the same defect. The required repair did not require changing any schema,
dimension, route, mask, checkpoint, or profile semantics.

## 5. Canonical profile-name authority

The approved A1c authority chain is:

```text
formal entrypoint resolves one canonical object
→ runner/facade/factory pass the same object
→ AssignmentHarlWrapper validates raw/object/origin agreement
→ require_assignment_profile_runtime_ready narrows to
  ResolvedExistingAssignmentProfile
→ wrapper stores that object as self._resolved_assignment_profile
```

For direct/fake wrapper compatibility, only the explicit
`DIRECT_WRAPPER_FALLBACK` context may resolve a missing object. Formal paths may
not silently use that fallback. A supplied resolved object is validated and
returned unchanged; it is not copied, serialized, inferred again, or resolved
again.

The canonical manifest string is therefore:

```python
self._resolved_assignment_profile.profile_name.value
```

This source is authoritative because:

1. `profile_name` is the canonical `AssignmentProfileName` enum carried by the
   resolved identity;
2. registry validation pins it to the exhaustive existing-profile definition;
3. `.value` yields the historical manifest string expected by save/load/
   playback consumers;
4. it does not reinterpret scenario text, checkpoint metadata, CLI text, or a
   raw config mapping;
5. it introduces neither a fallback default nor a second resolver.

## 6. Exact production patch

Exactly one logical line was added in the one authorized production file.

Broken A6 code:

```python
def _build_assignment_observation_schema_manifest(self) -> dict[str, Any]:
    policy_sequence_contract = policy_sequence_contract_for_profile(
        self._resolved_assignment_profile
    )
```

Repaired A6-R code:

```python
def _build_assignment_observation_schema_manifest(self) -> dict[str, Any]:
    profile_name = self._resolved_assignment_profile.profile_name.value
    policy_sequence_contract = policy_sequence_contract_for_profile(
        self._resolved_assignment_profile
    )
```

Exact A6-R production delta:

```diff
+        profile_name = self._resolved_assignment_profile.profile_name.value
```

File evidence captured immediately around the repair:

```text
before repair:
  bytes: 147233
  lines: 2826
  SHA-256: d3efaf823b07892f8396eaf575f7c9fb9cefeef5d2f3ee054ca5fddbf473c5cb
  Git blob: 6ad15830f7fafdace0e8805206f6c9eba233c4fe

after repair:
  bytes: 147309
  lines: 2827
  SHA-256: da694c5c1cbebea675e3657fc0c43640d16b131bb1cd4fc5cb83e6626eed320a
  Git blob: 14d9f9eedd6839e64c39cb5830908179205ce71b
```

Targeted syntax verification:

```text
interpreter:
  C:\isaacenvs\isaac45_harl\python.exe

python -m py_compile assignment_harl_wrapper.py:
  PASS

git diff --check -- assignment_harl_wrapper.py:
  PASS
```

The patch does not alter actor/shared dimensions, action dimensions, action
spaces, masks, resolver flags, profile routes, policy-sequence semantics, V2,
or V3.

## 7. Existing-profile manifest identity

The repaired manifest must expose the exact canonical string for all four
existing profiles:

| Resolved profile | Required `manifest["profile_name"]` |
|---|---|
| `AssignmentProfileName.LEGACY` | `legacy` |
| `AssignmentProfileName.LIFECYCLE_CONTRACT_C` | `lifecycle_contract_c` |
| `AssignmentProfileName.LIFECYCLE_ABLATION` | `lifecycle_ablation` |
| `AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE` | `diagnostics_hidden_state` |

The regression must compare the manifest result against the canonical resolved
object, not against a separately parsed scenario/config string:

```python
manifest["profile_name"] == resolved.profile_name.value
```

No compatibility mapping, dimension, action space, or route is changed by the
one-line binding.

`test_wrapper_schema_manifest_profile_name_binding` passed all four exact rows:

```text
legacy:
  legacy
lifecycle_contract_c:
  lifecycle_contract_c
lifecycle_ablation:
  lifecycle_ablation
diagnostics_hidden_state:
  diagnostics_hidden_state
```

For every row, the public manifest value, canonical resolved enum value, and
requested canonical profile string were equal.

## 8. Event-profile fail-closed preservation

Event-gated local MRTA remains interface-only. Wrapper initialization still
executes the following barrier before agents, profile branches, resolver,
observation/mask layout, logger, controller behavior, or schema-manifest access:

```python
self._resolved_assignment_profile = require_assignment_profile_runtime_ready(
    authoritative_profile,
    ...,
    barrier=(
        "before wrapper profile branches, resolver, observation, mask, "
        "logger, and controller"
    ),
)
```

`require_assignment_profile_runtime_ready()` returns only the canonical
`ResolvedExistingAssignmentProfile`. A matching
`ResolvedEventGatedAssignmentProfile` raises
`PhaseAExecutionNotAuthorizedError`. Consequently an event profile cannot
reach `_build_assignment_observation_schema_manifest()` merely because the
local name has been repaired.

The A6-R test explicitly proved that event profile construction/access does
not silently enter the old wrapper schema path.

The event regression passed: constructing the fake wrapper with a pre-resolved
`event_gated_local_mrta` identity raised
`PhaseAExecutionNotAuthorizedError` before the existing-wrapper schema path.
The recorded result was
`phase_a_fail_closed_before_existing_wrapper_schema`.

## 9. Independent observation/shared/mask oracle

Hardening H1 replaces the original self-referential digest evidence with an
independent test-side oracle for both legacy and Contract C.

Required construction:

- use explicit synthetic robot/task/lifecycle primitives;
- assemble expected legacy actor observation from the frozen legacy field
  order without invoking the production observation builder;
- assemble expected Contract-C actor observation from the frozen Contract-C
  row, tail, lifecycle, budget, and ordering semantics without invoking the
  production builder;
- independently assemble shared observation in its frozen construction order;
- independently construct every available-action entry, including noop;
- use explicit test-side `torch.cat`, `torch.stack`, reshape, and indexing where
  needed.

Required primary assertions for both profiles:

```text
actor observation:
  exact shape, dtype, device, element content, flatten/order
shared observation:
  exact shape, dtype, element content, ordering
action mask:
  exact shape, dtype, every entry
primary equality:
  torch.equal(actual, expected)
```

The six tensor digests may remain only as secondary reproducibility fixtures;
they cannot generate or define expected values.

The implemented independent oracle passed for nonzero legacy and Contract-C
fixtures with `E=2`, `M=3`, `N=50`, and `float32` tensors:

| Profile | Actor per agent | Shared transport | Action mask |
|---|---|---|---|
| legacy | `[2,909]` | `[2,3,2727]` | `[2,3,51]` |
| Contract C | `[2,1059]` | `[2,3,3183]` | `[2,3,51]` |

The test independently assembles actor rows/tails, robot-major shared state,
and every action-mask entry. Contract-C nonzero state includes task 7 ownership
and active-target facts, task 9 released-pair state, task 11 failed-pair state,
and robot 1 budget progress `3/10`. For all three agents under both profiles,
actor shape/dtype/device/content/order passed exact `torch.equal`; shared and
mask shape/dtype/device/content/order also passed exact `torch.equal`.

After the nonzero Contract-C fixture was strengthened, one intermediate run was
`15/16`: every primary independent `torch.equal` assertion had passed, and the
only failure was the now-stale secondary Contract-C digest fixture. The
secondary reproducibility digests were then synchronized to the independently
validated nonzero fixture, and the final run passed `16/16`. Thus no digest was
used as the primary oracle.

## 10. Exact 19-surface inventory hardening

Hardening H2 pins the master surface tuple independently and in this exact
order:

```text
1.  resolved runtime route
2.  observation
3.  shared observation
4.  action dimension / action space
5.  action mask
6.  sampled-action route
7.  log-prob route
8.  proposal
9.  effective assignment
10. reward
11. GAE / return input
12. ValueNorm input
13. sequential factor
14. RNG path
15. minibatch order
16. logger output
17. file side effects
18. checkpoint V2
19. playback route
```

The literals `action dimension / action space` and `sampled-action route` are
part of the identity and must not be replaced by slash/hyphen variants. The
test must assert:

```python
actual_surface_tuple == EXPECTED_SURFACE_TUPLE
len(actual_surface_tuple) == 19
len(set(actual_surface_tuple)) == 19
```

The final test passed exact tuple equality against the independent literal,
`len == 19`, and duplicate count zero. Evidence-label counts also remained
exact: `BYTE/TENSOR-EXACT=9`, `STATIC-ROUTE-EXACT=10`,
`MANIFEST-EXACT=1`, `NOT-EXECUTABLE-IN-PHASE-A=8`, and
`DEFERRED-RUNTIME-IDENTITY-EVIDENCE=18`.

## 11. Contract-C resolver-discriminating fixture

Hardening H3 must ensure the Contract-C fixture distinguishes the enabled
resolver from a disabled resolver or proposal clone. Its pure synthetic input
must contain conflict and/or transfer conditions for which frozen Contract-C
resolver semantics yield:

```text
resolved profile:
  lifecycle_contract_c
effective resolver flag:
  true
proposal:
  explicit synthetic tensor/input
effective assignment:
  independently specified exact expected result
proposal != effective assignment:
  true for at least one robot
```

The expected effective assignment may not be produced by calling the resolver
under test and copying its result. It must follow the frozen conflict,
ownership, safety, and transfer semantics. If resolver execution were replaced
by `effective = proposal`, the fixture must fail.

This remains a pure resolver fixture. It must not construct an Isaac
environment or modify resolver production.

The pure Contract-C discriminator passed with this exact fixture:

```text
proposal:
  [[5, 5, -1],
   [7, 7,  7]]

independent expected effective assignment:
  [[5, -1, -1],
   [7, -1, -1]]
```

The resolved profile was `lifecycle_contract_c`, its effective resolver flag
was `true`, and the production resolver returned the exact independent
expectation. Robots 1 in environment 0 and robots 1/2 in environment 1 differ
from proposal, so a disabled resolver or `effective = proposal` clone would
fail this test.

## 12. Expanded clean-child evidence

Hardening H4 widens the clean-child operation boundary from profile resolution
alone to:

```text
D0 profile resolution
valid legacy D1
valid Contract-C D1
scenario/profile propagation using pure helpers
fake wrapper construction
assignment_observation_schema_manifest access
```

Before and after those operations, the child must snapshot and compare:

- Python RNG and Torch RNG;
- cwd, complete environment, and `sys.path`;
- root logger level and handlers;
- all named logger names, levels, handlers, `propagate`, and `disabled` flags;
- working/temp directory file inventory;
- profile-registry object identity and representation.

No AppLauncher, Isaac env, `gym.make`, reset, or step is permitted. Child
stderr must be empty. Child stdout must contain only one intentional final JSON
line and no additional output.

The expanded child passed under an isolated command shaped as:

```text
python -I -B -c <pure-child-source>
```

It ran in a temporary working directory, exited zero, emitted exactly one
intentional JSON stdout line, and emitted no stderr. D0, valid legacy D1, valid
Contract-C D1, pure scenario propagation, fake-wrapper construction, and
manifest access all passed. The manifest sequence was exactly
`["legacy", "legacy", "lifecycle_contract_c"]`.

Python RNG, Torch RNG, cwd, environment, `sys.path`, root logger, full named
logger inventory, recursive file inventory, profile-registry identity, and
profile-registry representation were unchanged. The blocked Isaac/Omni/HARL
module inventory was empty.

## 13. Dedicated A6 rerun

Historical result retained:

```text
original A6:
  13/15 passed
  blocked by NameError in legacy and Contract-C manifest access
```

A6-R required command:

```powershell
D:\miniconda3\Scripts\conda.exe run `
  -p C:\isaacenvs\isaac45_harl `
  python scripts/environments/test_assignment_phase_a_default_off_identity.py --json
```

Final joint syntax verification passed for both the repaired wrapper and the
dedicated test. The dedicated JSON suite then returned:

```text
status: passed
total: 16
passed: 16
failed: 0
exit code: 0
runtime_identity: DEFERRED-RUNTIME-IDENTITY-EVIDENCE
evidence_label_counts:
  BYTE/TENSOR-EXACT: 9
  STATIC-ROUTE-EXACT: 10
  MANIFEST-EXACT: 1
  NOT-EXECUTABLE-IN-PHASE-A: 8
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE: 18
```

The final dedicated test artifact is 54,134 bytes with SHA-256
`5f31f111cc0eeea2323e33913b383bff123bc7a6da95a044176149c8735834c4`.
The chronology remains explicit: original A6 `13/15`, strengthened nonzero
Contract-C intermediate `15/16` from stale secondary digests only, final A6-R
`16/16`.

## 14. Wrapper-sensitive regressions

The wrapper repair requires re-audit and rerun of every still-pure/static
wrapper-sensitive test. The minimum inventory is:

| Test | Prior safe baseline | A6-R result |
|---|---:|---|
| `test_assignment_profile_production_wiring.py` | 10/10 | 10/10, pass |
| `test_assignment_initial_condition_contract.py` | 9/9 | 9/9, pass |
| `test_assignment_lifecycle_observation_pure.py` | 11/11 | 11/11, pass |
| `test_assignment_rl_interface.py` | 4/4 | 4/4, pass |

Tests importing the Isaac wrapper integration boundary remain deferred even if
their filename contains `wrapper`, `integration`, or `smoke`.

The final audited pure/fake-wrapper inventory above passed `34/34`; each script
exited zero. Isaac-dependent wrapper integration/smoke entries were not run.

## 15. Checkpoint/playback static regressions

Required pure/static checkpoint and playback checks are:

| Test | Prior baseline | A6-R result |
|---|---:|---|
| `test_assignment_checkpoint_semantic_dispatch.py` | 12/12 | 12/12, pass |
| `test_assignment_checkpoint_entry_guard_integration.py` | 10/10 | 10/10, pass |
| `test_assignment_checkpoint_contract_core.py` | 28/28 | 28/28, pass |
| `test_assignment_playback_attribution_diagnostics.py` | 16/16 | 16/16, pass |

Consumer static audit targets remain:

```text
assignment_checkpoint_save.py:
  wrapper.assignment_observation_schema_manifest
assignment_checkpoint_load.py:
  wrapper.assignment_observation_schema_manifest
play_assignment.py:
  wrapper.assignment_observation_schema_manifest
```

The one-line repair adds no second profile-name path. No real save, load,
playback, model, or tensor I/O is authorized.

All four listed regression scripts passed `66/66` and exited zero. The consumer
AST audit found exactly one public
`assignment_observation_schema_manifest` access in each of checkpoint save,
checkpoint load, and playback, and found no second
`resolved_assignment_profile` attribute path in any consumer.

## 16. Canonical A1-A5 regressions

The canonical matrix retained its previous aggregate:

```text
test_assignment_profile_contract.py
test_assignment_profile_production_wiring.py
test_assignment_initial_condition_contract.py
test_assignment_lifecycle_transition_contract.py
test_assignment_event_gated_mrta_contract.py
test_assignment_team_reward_contract.py
test_assignment_event_gated_diagnostics_contract.py
test_assignment_event_profile_schema_contract.py
test_assignment_checkpoint_semantic_dispatch.py
test_assignment_checkpoint_entry_guard_integration.py
test_assignment_checkpoint_contract_core.py

required aggregate:
  143/143
```

Final per-script counts, in the required order, were:

```text
profile contract:              16/16
profile production wiring:     10/10
initial-condition contract:     9/9
lifecycle transition:          12/12
event-gated MRTA:               13/13
team reward:                    12/12
event diagnostics:              12/12
event-profile schema:            9/9
checkpoint semantic dispatch:   12/12
checkpoint entry guard:         10/10
checkpoint V2 core:             28/28

aggregate:
  143/143
```

Every canonical command exited zero.

## 17. Historical safe-test regression

The seven previously audited safe scripts were rerun:

| Script | Prior groups |
|---|---:|
| `test_assignment_checkpoint_contract_core.py` | 28 |
| `test_assignment_lifecycle_observation_pure.py` | 11 |
| `test_assignment_lifecycle_resolver_smoke.py` | 20 |
| `test_assignment_lifecycle_resolver_runtime_smoke.py` | 12 |
| `test_assignment_rl_interface.py` | 4 |
| `test_assignment_playback_attribution_diagnostics.py` | 16 |
| `test_assignment_initial_condition_contract.py` | 9 |
| **Total** | **100** |

The checkpoint-core and initial-condition scripts overlap the canonical 143
and must not be double-counted when reporting a unique aggregate.

All seven scripts exited zero with the exact per-script counts
`28, 11, 20, 12, 4, 16, 9`, totaling `100/100`.

The following scripts remain deferred and must not be run:

```text
test_assignment_lifecycle_observation_integration.py
test_assignment_lifecycle_controlled_training_gate.py
test_assignment_lifecycle_feed_forward_guard.py
test_assignment_logger_reward_whitelist.py
test_assignment_harl_discrete_shape.py
```

## 18. V2/V3 golden preservation

A6-R verified these immutable values without updating a golden:

```text
V2 source SHA-256:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0

legacy V2:
  5509 bytes
  1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f

Contract-C V2:
  7234 bytes
  88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398

V3 interface descriptor:
  67794 bytes
  03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a
```

V3 remains interface-only, not checkpoint-ready, and unauthorized for weight
save/load/use. Metadata-free V2 fallback remains unchanged and unexpanded.

All four byte/hash comparisons matched exactly. V2 direct/dispatch semantics
and its metadata-free fallback remained unchanged; the semantic-dispatch suite
passed `12/12`. V3 remained the same interface-only descriptor and did not
become checkpoint-ready.

## 19. Production-scope audit

Authorized production delta:

```text
production files changed by A6-R:
  assignment_harl_wrapper.py only

logical production patch:
  one canonical profile-name binding line
```

All other protected production sources retained their pre-A6-R hashes,
especially:

```text
assignment_profile_contract.py
assignment_checkpoint_contract.py
assignment_checkpoint_contract_v3.py
assignment_checkpoint_semantic_dispatch.py
assignment_checkpoint_entry_guard.py
assignment_checkpoint_save.py
assignment_checkpoint_load.py
assignment_lifecycle_transition_contract.py
assignment_event_contract.py
assignment_mrta_contract.py
assignment_team_reward_contract.py
assignment_event_gated_diagnostics_contract.py
assignment_event_profile_schema_contract.py
```

No YAML/JSON, installed HARL, environment, runtime observation, mask, resolver,
reward, runner, trainer, buffer, logger, or checkpoint artifact may change.

The protected production cohort contained 26 files. Twenty-five were exact
before/after hash matches. The only changed production member was the authorized
wrapper:

```text
assignment_harl_wrapper.py:
  before: 147233 bytes
          d3efaf823b07892f8396eaf575f7c9fb9cefeef5d2f3ee054ca5fddbf473c5cb
  after:  147309 bytes
          da694c5c1cbebea675e3657fc0c43640d16b131bb1cd4fc5cb83e6626eed320a
```

Installed HARL was unchanged. Starting and ending HEAD were both
`dca976001d8c53a9cfb424b468fa58d9fca367f6`; no commit was created.

Final repository audit after the documentation closeout:

```text
worktree paths:
  52 total = 13 tracked modifications + 39 untracked paths
A6-R worktree delta:
  51 -> 52 paths
index:
  empty
unknown paths:
  none
HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6
git diff --name-status:
  13 expected tracked Phase-A paths; no unexpected tracked path
git diff --check:
  exit 0; no whitespace error (only existing LF/CRLF notices)
commit:
  none
```

The A6-R-scoped delta is exactly the authorized wrapper repair, hardened
dedicated test, new A6-R report, updated Phase-A final report, and this targeted
`TASK_PROGRESS.md` closeout. The remaining worktree paths belong to the
pre-existing, preserved Phase-A cohort.

## 20. Deferred runtime evidence

The A6-R repair and pure/static test hardening do not upgrade any runtime row.
All of the following remain `DEFERRED-RUNTIME-IDENTITY-EVIDENCE`:

| Runtime evidence row | Later owner/gate |
|---|---|
| real Isaac startup identity | B0/E |
| real env observation | B/C |
| real env shared observation | B/C |
| real env action mask | B/C |
| sampled action trajectory | C |
| runtime log-prob | C |
| rollout proposal/effective stream | B/C |
| base environment reward identity | D |
| GAE execution | C/D |
| ValueNorm execution | C/D |
| sequential factor execution | C |
| rollout RNG sequence | C/E |
| optimizer/minibatch execution order | C/E |
| real logger output | B0/B/C/D |
| real filesystem side effects | B0/B/C/D/E |
| actual playback | E |
| runtime same-object propagation | B0 |
| pre-reset lifecycle authority | B0 |
| event scheduler/local-set/cost/Top-K | B |
| event DVM/buffer/trainer | B/C |
| team reward runtime | D |
| diagnostic runtime producers | B0/B/C/D |
| checkpoint-ready V3/state-dict inventory | later checkpoint gate |

No passing pure fake-wrapper, resolver, tensor-oracle, manifest, or AST check
may be described as real environment or training evidence.

## 21. Remaining limitations

The exact 11 method numeric-TBDs remain ordered and unresolved:

```text
top_k_tasks_per_robot
local_robot_cap
local_task_cap
pair_abs_threshold
pair_rel_threshold
component_abs_threshold
component_rel_threshold
transfer_penalty
rejection_penalty_scale
alignment_time_constant
assignment_retry_cadence
```

A6-R selects no value, default, threshold, cadence, or penalty scale.

Even after a green pure/static/manifest closeout, the following limitations
remain:

- no Isaac/AppLauncher startup or runtime same-object confirmation;
- no real observation/shared/mask trajectory;
- no event scheduler, local-set/Top-K, DVM, transfer-component runtime, or
  team-infeasible termination implementation;
- no actor/critic rollout, GAE, ValueNorm, sequential factor, optimizer, or
  zero-valid actor update evidence;
- no real reward/diagnostic/logger throughput;
- no checkpoint-ready V3 state-dict inventory or weight compatibility;
- no playback, training, evaluation, ablation, or performance result.

The largest later risk remains Phase C runner/trainer integration: nondecision
ratios must be exactly one while actor loss/entropy/advantage normalization use
only valid decisions and critic GAE/ValueNorm retain all valid physical steps.

B0 remains not entered and not authorized. This successful A6-R closeout
authorizes only a stop for final GPT/user review.

## 22. Final classification

```text
classification:
  PHASE-A-PURE-INTERFACE-IDENTITY-DIAGNOSTICS-COMPLETE-AWAITING-GPT-REVIEW

original A6 closeout:
  STOP — production default-off identity gap
  13/15

A6-R repair:
  canonical one-line production repair applied

A6-R hardening/results:
  H1 independent nonzero tensor oracles: pass
  H2 exact 19-surface tuple: pass
  H3 resolver-discriminating fixture: pass
  H4 expanded isolated clean-child: pass
  four existing profile manifest identities: pass
  event existing-wrapper barrier: pass

A6-R dedicated suite:
  16/16 passed

A1-A5 canonical:
  143/143 passed

historical safe:
  100/100 passed

V2/V3:
  frozen exact

11 numeric TBDs:
  unresolved

runtime identity:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE

Phase A:
  complete to declared pure/static/manifest evidence level
  stopped for final GPT/user review

B0:
  not entered
  not authorized

B/C/D/E:
  not entered

Isaac/AppLauncher:
  not run

training/playback/evaluation:
  not run

real checkpoint tensor I/O:
  none

installed HARL:
  unchanged

commit:
  none
```
