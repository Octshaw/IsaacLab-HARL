# Phase A Pure Interface / Identity / Diagnostics Implementation Report

## 1. Current classification after A6-R

```text
classification:
  PHASE-A-PURE-INTERFACE-IDENTITY-DIAGNOSTICS-COMPLETE-AWAITING-GPT-REVIEW
Phase A:
  complete to the declared pure/static/manifest evidence level
  stopped for final GPT/user review
runtime identity:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE
event runtime:
  not implemented
B0:
  not entered
  not authorized
B/C/D/E:
  not entered
commit:
  none
```

A6-R repaired the one confirmed production regression with exactly one added
binding inside `_build_assignment_observation_schema_manifest()`:

```python
profile_name = self._resolved_assignment_profile.profile_name.value
```

This uses the wrapper's already-authoritative resolved identity and does not
create a second resolver or reinterpret raw scenario/CLI/checkpoint text. The
wrapper changed from 147,233 bytes and SHA-256
`d3efaf823b07892f8396eaf575f7c9fb9cefeef5d2f3ee054ca5fddbf473c5cb`
to 147,309 bytes and SHA-256
`da694c5c1cbebea675e3657fc0c43640d16b131bb1cd4fc5cb83e6626eed320a`.
Legacy, Contract-C, lifecycle-ablation, and diagnostics-hidden-state schema
manifests now obtain `profile_name` from that canonical object. The event
profile still fails closed before the existing-wrapper schema path.

A6-R also closes hardening H1--H4. The strengthened dedicated suite had one
intermediate `15/16` run in which all primary independent `torch.equal`
observation/shared/mask comparisons passed and only an old secondary
reproducibility digest remained stale. After correcting that non-authoritative
secondary fixture, the final dedicated result was `16/16`. The canonical
A1--A5 matrix remained `143/143`, the seven audited-safe historical scripts
remained `100/100`, V2/V3 stayed frozen exact, all 11 numeric-TBDs stayed
unresolved, and all 23 machine-inventoried runtime rows stayed deferred.

### 1.1 Original A6 stop (historical record preserved)

The following is the original A6 classification and blocker record. It is
historical evidence and is intentionally not rewritten as a first-pass success.

```text
classification:
  STOP — PHASE-A DEFAULT-OFF IDENTITY GAP
Phase A:
  incomplete; blocked at the A6 dedicated identity gate
runtime identity:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE
event runtime:
  not implemented
B0:
  not entered
  not authorized
B/C/D/E:
  not entered
commit:
  none
```

The dedicated pure test found a production frozen-contract regression before
Phase A could close. `AssignmentHarlWrapper.assignment_observation_schema_manifest`
calls `_build_assignment_observation_schema_manifest()`, whose return mapping
still reads the local name `profile_name` even though the Phase-A diff removed
that function-local binding. Both the legacy and Contract-C fake-wrapper rows
therefore raise `NameError`. This property is consumed by production
save/load/playback paths, so the failure cannot be dismissed as a test-only
diagnostic or bypassed to obtain a green result.

Exact production chain at the original A6 stop was
`assignment_harl_wrapper.py:418-419 -> :1018 -> :1048`; wrapper source SHA-256
at that stop was
`d3efaf823b07892f8396eaf575f7c9fb9cefeef5d2f3ee054ca5fddbf473c5cb`.
Direct consumers include `assignment_checkpoint_save.py:1099`,
`assignment_checkpoint_load.py:1181`, and `play_assignment.py:490`. The Phase-A
diff shows the former local assignment
`profile_name = str(self._assignment_lifecycle_profile_config["profile_name"])`
was removed while `"profile_name": profile_name` remained in the result.

The remaining evidence is still useful but does not override this stop. No
claim is made that a real Isaac environment, rollout, actor update, checkpoint
weight path, or playback trajectory is byte-identical.

```text
dedicated A6 suite:
  13/15 passed; exit 1; BLOCKED
  failed groups: legacy_observation_shared_action_mask,
                 contract_c_observation_shared_action_mask
dedicated A6 test SHA-256:
  6cf14f02b27be9a8e4c391a28848b1aa0899fa29aa2e0961f94c816ca94a0bab
dedicated A6 test py_compile:
  passed
```

## 2. Phase A authorization and scope

A1 through A5 had passed review before A6 was authorized as
`PHASE-A6-DEFAULT-OFF-IDENTITY-AND-PHASE-A-FINAL-CLOSEOUT-AUTHORIZED`.
A6 authorized only one standalone `--json` identity test, this completion
report, and a concise `TASK_PROGRESS.md` closeout (with an archive only if root
performs substantial condensation).

Original A6 production-Python modification count was zero. After its dedicated
gate stopped at `13/15`, A6-R was separately authorized to modify exactly one
production file, `assignment_harl_wrapper.py`, plus the dedicated test and
closeout documents. A6-R did not authorize any other production source or any
change in observation/action/mask/checkpoint/runtime semantics.

Across A6 and A6-R, Isaac/AppLauncher execution, environment reset/step,
actor/critic update, optimizer/backward, training, playback, evaluation, real
checkpoint tensor I/O, V2/V3 golden changes, installed-HARL changes, B0 entry,
and commit remained prohibited and did not occur.

```text
pure/static/manifest evidence:
  COMPLETE TO ITS DECLARED LEVEL — final dedicated suite 16/16
all runtime-only rows remain:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE
no claim of full runtime identity
```

## 3. Repository baseline and final state

```text
starting HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6
starting worktree:
  49 paths = 13 tracked modifications + 36 untracked paths
starting index:
  empty
starting unknown paths:
  none
starting git diff --check:
  exit 0; inherited LF/CRLF notices only
active interpreter:
  C:\isaacenvs\isaac45_harl\python.exe

ending HEAD:
  dca976001d8c53a9cfb424b468fa58d9fca367f6
original A6 ending worktree:
  51 paths = 13 tracked modifications + 38 untracked paths
original A6 ending index:
  empty
production changes during original A6:
  none
unknown original-A6 paths:
  none

A6-R report-update snapshot:
  52 paths = 13 tracked modifications + 39 untracked paths
A6-R production delta:
  assignment_harl_wrapper.py only; one canonical binding line
A6-R test delta:
  test_assignment_phase_a_default_off_identity.py only
A6-R documentation delta:
  PHASE_A6R_TARGETED_DEFAULT_OFF_IDENTITY_REPAIR_REPORT.md
  this report
A6-R index:
  empty
A6-R unknown paths:
  none
A6-R git diff --check:
  exit 0; inherited LF/CRLF notices only
```

The worktree is intentionally not clean: it contains the inherited, documented
A1--A5 cohort. Scope conclusions use its starting inventory plus the accepted
reports, not a false `git status clean` requirement.

## 4. Actual Phase A implementation timeline

The history is not rewritten as though all final details existed initially.

| Date | Package | Actual result | Plan/revision relation |
|---|---|---|---|
| 2026-07-27 | targeted plan revision | PR-01--PR-07 frozen; implementation still blocked | approved correction before A1 |
| 2026-07-27 | A1a | five-profile registry and discriminated resolved identity | original A1 package 1 |
| 2026-07-29 | A1b | scenario primitive propagation, provenance/conflict checks, prerequisites | original A1 package 2; intentional scenario correction |
| 2026-07-29 | A1c | formal authority, same-object parameter chain, bypass and fail-closed guards | original A1 package 3 |
| 2026-07-29 | A2 | facts/result, producer/authority split, consume-once ledger/receipt | original A2 |
| 2026-07-29 | A3 | typed event/opportunity/MRTA/proposal/reward/diagnostics contracts | original A3 |
| 2026-07-29 | first A4a entry | `STOP -- A3 SCHEMA-FREEZE GAP`; no A4a production implementation | prescribed fail-closed stop |
| 2026-08-03 | A3x-0/A3x-0R | schema-freeze and terminal-row/descriptor design revision | separately approved blocker extension |
| 2026-08-03 | A3x-1 | aggregate and descriptor-v2 projections | separately authorized descriptor-only implementation |
| 2026-08-07 | A4a-R | pure V3 interface descriptor and V2/V3 dispatcher | restarted after A3x review |
| 2026-08-08 | A4b | minimal save/load/playback/offline-audit entry guards | separately authorized half of A4a/A4b split |
| 2026-08-08 | A5 | diagnostics/reward test-only closeout | no production schema change |
| 2026-08-09 | A6 | default-off matrix and deferred inventory; `13/15` stop on production `NameError` | prescribed stop before repair/B0 |
| 2026-08-09 | A6-R | one-line canonical wrapper repair plus H1--H4 evidence hardening; final `16/16` | separately authorized targeted repair; stops for final review |

The targeted plan already split A4 into A4a/A4b. A3x was not silently part of
the original A3: it was approved only after the first A4a attempt found missing
actor/shared/terminal and ownership schema needed for deterministic V3 identity.

## 5. A1 profile identity and fail-closed routing

A1 establishes the ordered profiles `legacy`, `lifecycle_ablation`,
`lifecycle_contract_c`, `diagnostics_hidden_state`, and
`event_gated_local_mrta`. Only `ResolvedExistingAssignmentProfile` owns old
runtime booleans and `to_legacy_wrapper_mapping()`;
`ResolvedEventGatedAssignmentProfile` is interface-only and cannot fall through
the old boolean/Contract-C consumer.

A1a added `assignment_profile_contract.py`. A1b implemented primitive scenario
parse/apply and conflict validation. A1c installed formal authority, direct
fallback, exact existing-profile bypass, and event readiness gates. The static
parameter chain is:

```text
formal entrypoint resolved object
is runner.resolved_assignment_profile
is env facade.resolved_assignment_profile
is wrapper.resolved_assignment_profile
```

Pure helper identity and AST routing support that chain; real process-level
same-object propagation is `DEFERRED-RUNTIME-IDENTITY-EVIDENCE`.

Legacy retains the old disabled resolver route. Valid Contract-C retains its
existing effective resolver-on route, but raw cooldown/budget/guardrail
prerequisites must already be valid; Phase A does not auto-fill them. Visible
event declarations and post-compose event identities fail closed before the
old runtime route. This is not event runtime readiness.

## 6. A2 transition authority contracts

A2 separates `ENV_EXECUTION_FACTS_PRODUCER_V1`, which creates raw immutable
`ExecutionTransitionFacts`, from `LIFECYCLE_AUTHORITY_V1`, which consumes facts,
finalizes `LifecycleTransitionResult`, and later owns lifecycle-event creation.

The facts/result contracts pin exact `[E]`, `[E,M]`, `[E,N]`, and `[E,M,N]`
shapes/dtypes, generations, pair-attributed completion/failure/release,
availability edges, pre-transition states/ownership, cumulative failure and
termination outputs. The ledger validates producer, generation, token,
consume-once, batch atomicity, and deterministic receipts without RNG.

Supported-path alias isolation/mutation detection is proven, while private
storage/version mechanisms are not semantic identity. No runtime producer or
lifecycle authority was placed into environment/wrapper/resolver; B0 owns that.

## 7. A3 event/MRTA/reward/diagnostic contracts

A3 keeps seven lifecycle events, one scheduled assignment opportunity, and
three trigger-ineligible resolver diagnostics in distinct type systems. It
freezes, but does not execute, cost/path validity, local-set request/result,
one-round owner expansion, overflow fail-close, global-ID Top-K/current
retention, action-mask/DVM relations, proposal/forced-row separation,
policy-only components, whole-component results, and rejection attribution.

```text
policy_proposal_present_mask == decision_valid_mask
forced nondecision storage row != policy proposal
effective assignment is not a ProposalSnapshot field
rejected policy proposal remains a proposal
```

The reward target is wrapper-final reward mean, then one penalty per eligible
rejected component, then identical agent broadcast. Diagnostics is an exact
eight-payload typed union with no free-form bag and no runtime producer/sink.

## 8. A3x schema-freeze extension

A3x was the separately approved response to the A4a schema gap. It froze the
15-block actor formula `6MN + 30M + 14N + 2`, the 19-block shared formula
`6MN + 31M + 15N + 8`, ordinary forced-row versus terminal no-row semantics,
the terminal pre-reset critic sidecar, exactly 11 ordered numeric-TBDs, 19
uniquely owned V3 semantic sections, and local/cost/component/failure/model/
training projections.

A3x-1 added `assignment_event_profile_schema_contract.py` and descriptor-v2
projections in MRTA/event/transition. Existing DTO/record schema identities and
field orders remained unchanged. The model projection records the actually
consumed `(256,256)/(256,256)` actor/critic route; unconsumed YAML
`hidden_sizes_critic: [512,256]` is not adopted. This remains interface identity,
not runtime model evidence.

## 9. A4 V2/V3 semantic checkpoint boundary

A4a-R added a pure V3 authority with 21 root keys (two discriminators plus 19
typed sections) and a strict version dispatcher. Only
`interface_semantic_descriptor` is constructible in Phase A;
`checkpoint_ready_manifest`, runtime execution, and weight use remain blocked.

A4b added a shared entry guard and minimal save/load/training-audit/playback
integrations. The guard performs family-native parse, canonicalization,
fingerprint comparison, purpose evaluation, and authorization before the
established V2 tensor path. V3 remains metadata-only offline-audit capable.

Playback's existing topology still places this guard after AppLauncher and
normal actor construction, but before checkpoint tensor deserialization,
`load_state_dict`, reset, act, or step. Phase A did not run playback. The narrow
metadata-free V2 legacy fallback was preserved and not expanded.

## 10. A5 diagnostics/reward semantic closeout

A5 modified only the reward and diagnostics pure tests. It independently pins
enum/envelope/payload field orders, typed mapping reconstruction, phase
availability, four proposal-resolution row relations, mean -> component-once
penalty -> broadcast, equal `[E,M,1]` broadcast, unresolved penalty identity,
unchanged V3 projections, and no new event sink/info/file/logger/RNG path for
exercised old profiles.

The production reward, diagnostics, event-profile, and V3 sources were
byte-identical before and after A5. A5 did not transport team reward to critic,
produce diagnostics, or resolve a numeric penalty.

## 11. A6 default-off identity methodology

The A6 script is standalone, pure/static, and supports `--json`. Its V2/V3 and
profile mapping expectations come from accepted authorities. Original A6 used
six observation/shared/mask tensor digests that had been frozen after an
initial production probe. Independent review correctly classified them as
secondary reproducibility fixtures rather than an independent identity oracle.
It also found that the Contract-C resolver fixture did not discriminate an
enabled resolver from a proposal clone, the clean child covered only profile
resolution, and two surface literals were not exact. Those findings are the
historical evidence-gap record that motivated H1--H4; they are not erased.

A6-R closes those four gaps at the same pure/static boundary:

- H1 constructs legacy and Contract-C expected actor observations, shared
  observations, and masks independently from frozen semantics and explicit
  primitives, then compares every tensor with `torch.equal`; shape, dtype,
  device, content, flattening, ordering, and every mask entry are pinned;
- H2 independently pins the exact ordered 19-surface tuple, including
  `action dimension / action space` and `sampled-action route`, and asserts
  exact equality, length 19, and no duplicates;
- H3 uses a conflicting Contract-C proposal fixture whose exact effective
  assignment differs from the proposal, so disabled proposal-clone behavior
  would fail;
- H4 expands the isolated clean child through D0, valid legacy and Contract-C
  D1, pure scenario propagation, fake wrapper construction, and public schema
  manifest access while snapshotting Python/Torch RNG, cwd, environment,
  `sys.path`, root/named logger state (including `disabled`), files, and registry
  identity/content; stderr is empty and stdout is exactly one intentional JSON
  line.

Its required groups cover evidence/cohorts; D0; valid D1; scenario correction;
legacy and Contract-C observation/shared/action/mask; proposal/effective/reward;
actor/log-prob/GAE/ValueNorm/factor static routing; RNG/minibatch/logger/files;
V2; other profiles; event/V3; playback routing; deferred inventory; and
production scope. A6-R adds the explicit four-existing-profile
`wrapper_schema_manifest_profile_name_binding` regression, taking the suite
from 15 to 16 groups.

Historical execution reached `13/15`: both observation groups raised the same
production `NameError` at public schema-manifest access, and the test correctly
did not bypass the property. After the wrapper repair and hardening, one
intermediate strengthened-fixture run reached `15/16`; the primary independent
`torch.equal` oracle had already passed, and the only failure was the old
secondary Contract-C actor digest. That secondary, non-authoritative
reproducibility fixture was corrected without changing any manifest golden.
Final execution passed `16/16`.
Forbidden operations include Isaac/AppLauncher, assignment `gym.make`,
reset/step, actor update, optimizer/backward, `torch.load`, `torch.save`,
`load_state_dict`, training, playback, and evaluation. Static route inspection
uses AST/source text. An explicit `DEFERRED_RUNTIME_ROWS` table prevents a
deferred row from being reported as runtime verified or runtime byte-exact.

## 12. Evidence vocabulary

| Exact label | Meaning |
|---|---|
| `BYTE/TENSOR-EXACT` | exact pure bytes/structure or fake/synthetic tensor shape, dtype, content, and order |
| `STATIC-ROUTE-EXACT` | exact branch/callable/AST route without deferred runtime execution |
| `MANIFEST-EXACT` | exact canonical manifest bytes and SHA-256 |
| `NOT-EXECUTABLE-IN-PHASE-A` | operation prohibited by the Phase-A gate |
| `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` | real runtime proof is owned by a later phase |

Labels are non-exclusive. Across the 19-row master matrix, association counts
are:

```text
BYTE/TENSOR-EXACT:                    9 surfaces
STATIC-ROUTE-EXACT:                  10 surfaces
MANIFEST-EXACT:                       1 surface
NOT-EXECUTABLE-IN-PHASE-A:            8 surfaces
DEFERRED-RUNTIME-IDENTITY-EVIDENCE:  18 surfaces
```

These count surface/label associations, not independent tests.

The test now pins the authoritative 19-name tuple independently and exactly;
the previous `action dimension/action space` and `sampled action route`
spellings are retained only in this historical note. Association counts remain
unchanged because H2 corrects the oracle, not the evidence classification.

## 13. D0 / D1 / scenario-correction cohorts

| Cohort | Boundary | Phase-A result |
|---|---|---|
| `D0_ABSENT` | no scenario/profile declaration | implicit `legacy`; absent config unchanged; resolved object process-local and not serialized into args/env config/scenario/checkpoint/logger |
| `D1_PRE_RESOLVED_VALID` | direct config or complete scenario resolves an existing profile and already satisfies raw prerequisites | existing mapping/route/manifest can be compared; no prerequisite auto-fill |
| `SCENARIO_CORRECTION` | explicit profile was previously ignored, or top/nested declarations conflict | intentional parse/apply/validation correction, never byte/route identity versus the old bug |

| Top-level | Nested | Exact expected result |
|---|---|---|
| valid A | absent | canonical A applied; expected correction |
| absent | valid A | canonical A applied; expected correction |
| valid A | valid A | accepted; both source records retained |
| valid A | valid B | stable source-aware conflict rejection |
| unknown | any/absent | fail closed; never default to legacy |
| empty/whitespace | any/absent | fail closed; explicit empty is not absence |

Explicit `null` is also present-invalid. Contract-C D1 requires its existing
cooldown, budget/streak, mask, redirect, and failed-pair prerequisites. Its
effective resolver is true without inventing a raw-resolver-true requirement.

## 14. Legacy default-off identity matrix

This is the required 19-surface master table. “Exact” means exact only at the
declared fake/pure/static/manifest boundary.

Original A6 stopped before the observation/shared/mask digest checks and left
the effective-assignment and clean-child evidence non-discriminating or narrow.
The table below is the final A6-R state; the original partial state and `13/15`
failure remain recorded in sections 1.1 and 11.

| Surface | Legacy evidence | Contract C evidence | Phase-A classification | Residual |
|---|---|---|---|---|
| resolved runtime route | legacy selection and canonical schema-manifest profile exact | Contract-C selection and canonical schema-manifest profile exact | `STATIC-ROUTE-EXACT` | startup `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| observation | independently assembled fake tensor equals production tensor exactly | independently assembled lifecycle tensor equals production tensor exactly | `BYTE/TENSOR-EXACT` | real env `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| shared observation | independently assembled fake shared tensor exact | independently assembled Contract-C shared tensor exact | `BYTE/TENSOR-EXACT` | real env `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| action dimension / action space | fake dimension/space exact | fake dimension/space exact | `BYTE/TENSOR-EXACT` | real env `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| action mask | independently assembled every entry, shape, dtype, and noop exact | independently assembled every entry, shape, dtype, and noop exact | `BYTE/TENSOR-EXACT` | real env `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| sampled-action route | existing all-actor callable; no event subset sampler | same existing callable | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | rollout `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| log-prob route | existing evaluate-actions route | same existing route | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | rollout `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| proposal | fake proposal exact | fake Contract-C proposal exact | `BYTE/TENSOR-EXACT` | rollout stream `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| effective assignment | disabled resolver proposal-clone semantics exact | conflicting fixture produces independently expected arbitration result different from proposal | `BYTE/TENSOR-EXACT` | real env `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| reward | synthetic wrapper-final output exact | synthetic wrapper-final output exact | `BYTE/TENSOR-EXACT` | base env `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| GAE / return input | installed critic-buffer branch selected | same branch selected | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | update `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| ValueNorm input | existing critic-return branch selected | same branch selected | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | update `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| sequential factor | existing HA-runner branch selected | same branch; no event DVM factor | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | update `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| RNG path | no new profile/event/diagnostic RNG | same | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | rollout RNG `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| minibatch order | event trainer not selected | event trainer not selected | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | optimizer `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| logger output | expanded scenario/fake-wrapper clean-child state unchanged | same expanded boundary | `BYTE/TENSOR-EXACT` | real run `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| file side effects | expanded clean-child inventory unchanged | same expanded boundary | `BYTE/TENSOR-EXACT`; `STATIC-ROUTE-EXACT` | real run `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |
| checkpoint V2 | legacy canonical bytes/hash exact | Contract-C canonical bytes/hash exact | `MANIFEST-EXACT` | no checkpoint load |
| playback route | all-actor loop and pre-tensor guard route | same | `STATIC-ROUTE-EXACT`; `NOT-EXECUTABLE-IN-PHASE-A` | actual playback `DEFERRED-RUNTIME-IDENTITY-EVIDENCE` |

No event V3 dimension proves old-profile identity. Static actor/GAE/ValueNorm/
factor/minibatch evidence is never mislabeled runtime byte identity.

## 15. Contract-C default-off identity matrix

Contract-C evidence is limited to valid D1 inputs. Raw resolver absent, false,
or true is accepted while the resolved mapping has effective
`resolver_enabled=true`; all existing cooldown/budget/mask/guardrail
prerequisites remain mandatory.

Within this boundary, observation/shared/action-mask tensors now match an
independently assembled exact oracle, and the public schema manifest reports
the canonical Contract-C profile. The conflicting resolver fixture produces
an independently expected effective assignment that differs from its proposal,
so proposal-clone semantics would fail. Proposal and synthetic reward remain
exact. HAPPO/EP/non-shared/feed-forward/state-dict, all-actor sampling,
log-prob, GAE, ValueNorm, factor, and minibatch routes remain static evidence
only. No real Contract-C trajectory was run, and its nearest-8 or
actor-concatenated shared layout is not reused as the event V3 schema.

## 16. Other existing-profile identity

| Profile | Route | Training | Checkpoint/playback | Evidence |
|---|---|---|---|---|
| `lifecycle_ablation` | existing observation/mask ablation | blocked | named Contract-C -> ablation evaluation only; no native save/new playback | `STATIC-ROUTE-EXACT`; applicable `MANIFEST-EXACT` |
| `diagnostics_hidden_state` | existing diagnostics/resolver-on | blocked | no invented native family | `STATIC-ROUTE-EXACT`; applicable blocked `MANIFEST-EXACT` |

Historical diagnostics may have side effects. The exact Phase-A claim is only
that event-gated diagnostics added no new old-route sink/info/file/logger key;
it is not a repository-wide “zero diagnostics output” claim.

## 17. Event-profile Phase-A fail-closed identity

```text
profile:                 event_gated_local_mrta
profile contract:        assignment_resolved_profile_v1
runtime route:           event_gated_phase_a_interface_only_v1
checkpoint family:       assignment_checkpoint_contract_v3
runtime readiness:       interface_only
training:                phase_a_blocked
playback:                blocked
runtime execution:       unauthorized
checkpoint weight use:   unauthorized
```

Schema and `interface_semantic_descriptor` are `MANIFEST-EXACT`.
Runtime/training/playback/weight purposes are `NOT-EXECUTABLE-IN-PHASE-A`.
There is no event `BYTE/TENSOR-EXACT` runtime claim because event runtime does
not exist.

## 18. Checkpoint V2/V3 identity preservation

```text
assignment_checkpoint_contract.py SHA-256:
  8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0
legacy V2 canonical bytes / SHA-256:
  5509
  1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f
Contract-C V2 canonical bytes / SHA-256:
  7234
  88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398
V3 interface canonical bytes / SHA-256:
  67794
  03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a
```

V2 direct/dispatched bytes, decisions, mismatch order, and metadata-free
fallback remain exact. V3 is interface-only. No V3 ready golden was created,
no golden was updated, and no checkpoint tensor was loaded or saved.

## 19. Logger/RNG/filesystem side-effect evidence

Original A6 clean-child evidence covered profile resolution only; that narrower
boundary remains part of the historical review record. A6-R's expanded child
snapshots Python/Torch RNG, cwd, environment, `sys.path`, root and named logger
state (names, levels, handlers, propagation, and disabled state), file
inventory, and canonical profile-registry identity/content while exercising D0,
valid legacy and Contract-C D1, pure scenario propagation, fake wrapper
construction, and public schema-manifest access. All snapshots are unchanged,
stderr is empty, stdout is exactly one intentional JSON line, and no
Isaac/Omni/HARL runtime module is imported. Source hashes are checked separately
in the parent process. A4b used temporary manifest/fingerprint text only and
removed it automatically.

Real logger output, run-directory effects, and rollout RNG remain
`DEFERRED-RUNTIME-IDENTITY-EVIDENCE`.

| A5-protected source | Exact SHA-256 |
|---|---|
| `assignment_team_reward_contract.py` | `21c27d60ade6008fdeaa77e726bfdb7930fa1acf84a02c9a9457bab6335ca97c` |
| `assignment_event_gated_diagnostics_contract.py` | `d013044170914df3b62bbb09dfbce34f29497ab644b7fb47225cbc4496e19a0a` |
| `assignment_checkpoint_contract_v3.py` | `7995432b63c5e0befd8eae1d6f793889f681b07f61c53fadeba103932c787d16` |
| `assignment_event_profile_schema_contract.py` | `04eb153f296196e8a098f071fdea3721e27893564b4fa2df81ff91fc088859ef` |

## 20. Safe pure/static regression matrix

The dedicated identity chronology is exact:

```text
original A6:
  13/15; STOP on legacy and Contract-C schema-manifest NameError
intermediate A6-R strengthened fixture:
  15/16; primary independent torch.equal oracle passed;
  only the old secondary Contract-C actor digest failed
final A6-R:
  16/16 passed
```

The canonical A1--A5 matrix passed:

| Suite | Result |
|---|---:|
| profile contract | 16/16 |
| profile production wiring | 10/10 |
| initial-condition contract | 9/9 |
| lifecycle transition contract | 12/12 |
| event-gated MRTA contract | 13/13 |
| team reward contract | 12/12 |
| event-gated diagnostics contract | 12/12 |
| event-profile schema contract | 9/9 |
| checkpoint semantic dispatch | 12/12 |
| checkpoint entry guard integration | 10/10 |
| checkpoint V2 core | 28/28 |

```text
required canonical total:  143/143 passed
optional training-run audit: 4/4 passed
required plus optional:     147/147 passed
```

The 12 historical candidates were re-audited at their current source state.
Seven were safe and ran successfully:

| Script | Classification | Result/boundary |
|---|---|---|
| `test_assignment_checkpoint_contract_core.py` | `AUDITED-SAFE-AND-RUN` | 28/28; pure manifest authority |
| `test_assignment_lifecycle_observation_pure.py` | `AUDITED-SAFE-AND-RUN` | 11/11; synthetic tensors |
| `test_assignment_lifecycle_resolver_smoke.py` | `AUDITED-SAFE-AND-RUN` | 20/20; fake problems/pure resolver |
| `test_assignment_lifecycle_resolver_runtime_smoke.py` | `AUDITED-SAFE-AND-RUN` | 12/12; fake adapter/controller, no Isaac env |
| `test_assignment_rl_interface.py` | `AUDITED-SAFE-AND-RUN` | 4/4 internal checks; one aggregate self-check printed |
| `test_assignment_playback_attribution_diagnostics.py` | `AUDITED-SAFE-AND-RUN` | 16/16; synthetic/temp/static |
| `test_assignment_initial_condition_contract.py` | `AUDITED-SAFE-AND-RUN` | 9/9; pure/fake/static |

```text
safe historical audit:
  7 scripts
  100/100 groups passed
```

V2 core (28) and initial-condition (9) are already in the canonical 143 and
are not double-counted as an additional 37 canonical groups.

## 21. Prohibited/deferred test entries

| Script | Current classification | Reason |
|---|---|---|
| `test_assignment_lifecycle_observation_integration.py` | `DEFERRED-CURRENT-SCRIPT-EXCEEDS-PHASE-A` | six bodies require canonical wrapper/package registration; one audit attempt failed before test execution in `isaaclab.envs` import with `ModuleNotFoundError` for `omni.kit`; no AppLauncher/env/reset/step/rollout |
| `test_assignment_lifecycle_controlled_training_gate.py` | `DEFERRED-CURRENT-SCRIPT-EXCEEDS-PHASE-A` | ten groups import the wrapper/training and installed-HARL stack |
| `test_assignment_lifecycle_feed_forward_guard.py` | `DEFERRED-CURRENT-SCRIPT-EXCEEDS-PHASE-A` | nine groups import the same training/HARL boundary |
| `test_assignment_logger_reward_whitelist.py` | `DEFERRED-CURRENT-SCRIPT-EXCEEDS-PHASE-A` | one aggregate group imports `assignment_harl_training` |
| `test_assignment_harl_discrete_shape.py` | `DEFERRED-CURRENT-SCRIPT-EXCEEDS-PHASE-A` | three checks construct `StochasticPolicy`/`OnPolicyActorBuffer`, random tensors, and action/log-prob forward paths |

The observation-integration attempt is a transparent pre-test import failure,
not a pass or runtime identity proof. It changed no file and launched no
simulation.

Wrapper/episode-reset/fresh-policy smokes, training-entry readiness,
checkpoint continuation/all-loader/save-metadata integrations,
actor-critic-buffer forward/backward readiness, lifecycle-mask/HARL replay,
`train.py`, `play_assignment.py`, runtime evaluation, and runtime diagnosis
entrypoints were not run.

## 22. Deferred runtime identity evidence matrix

Deferred means “outside the declared Phase-A evidence boundary,” not “bug.”

| Runtime evidence | Owner phase |
|---|---|
| pre-reset facts capture | B0 |
| lifecycle state mutation / authoritative transition runtime | B0 |
| failed-pair accumulation | B0 |
| TEAM_INFEASIBLE runtime | B0 / D |
| termination runtime | B0 / D |
| completion attribution | B0 |
| scheduled retry opportunities | B |
| local robot/task set | B |
| owner expansion / overlap merge | B |
| Top-K runtime | B |
| expected-time cost/path estimator | B |
| action mask runtime | B / C |
| DVM runtime | B / C |
| proposal sampling | C |
| transfer component resolver | B |
| atomic ownership commit | B |
| terminal HARL storage adaptation | B / C |
| actor subset sampling | C |
| rollout-buffer DVM | C |
| actor loss/entropy DVM masking | C |
| zero-valid actor skip | C |
| singleton advantage fallback runtime | C |
| sequential factor `torch.where` runtime | C |
| team reward runtime | D |
| rejection penalty runtime | D |
| critic reward transport | D |
| GAE/ValueNorm runtime verification | C / D |
| proper-time-limit/bad-mask integration | D |
| diagnostic runtime producers/sinks | B0/B/C/D |
| checkpoint-ready V3 | later runtime/checkpoint gate |
| state-dict semantic inventory | later checkpoint gate |
| V3 weight save/load | later checkpoint gate |
| training | E |
| playback | E |
| evaluation | E |
| ablation/statistical evaluation | E |

The machine inventory also names real Isaac startup, real observation/shared/
mask tensors, sampled trajectory, runtime log-prob, rollout proposal/effective
stream, base reward, rollout RNG, optimizer/minibatch order, real logger/files,
actual playback, runtime same-object propagation, event scheduler/cost/Top-K,
DVM/buffer/trainer, team reward, diagnostic producers, and V3/state-dict
readiness. None is classified runtime verified.

## 23. Eleven unresolved numeric parameters

1. `top_k_tasks_per_robot`
2. `local_robot_cap`
3. `local_task_cap`
4. `pair_abs_threshold`
5. `pair_rel_threshold`
6. `component_abs_threshold`
7. `component_rel_threshold`
8. `transfer_penalty`
9. `rejection_penalty_scale`
10. `alignment_time_constant`
11. `assignment_retry_cadence`

```text
numeric values selected in Phase A:
  none
```

Synthetic values are test data, not defaults, paper settings, configuration,
checkpoint-ready values, or evidence that an owner phase is complete.

## 24. Production/source/test/doc diff inventory

Because Phase A remains uncommitted, this inventory combines the worktree with
the temporal reports rather than attributing every untracked path to one phase.

Production source added:

1. `assignment_profile_contract.py` (A1a; authority extended A1c)
2. `assignment_lifecycle_transition_contract.py` (A2; event/descriptor extensions)
3. `assignment_event_contract.py` (A3; descriptor v2 later)
4. `assignment_mrta_contract.py` (A3; descriptor v2 later)
5. `assignment_team_reward_contract.py` (A3)
6. `assignment_event_gated_diagnostics_contract.py` (A3)
7. `assignment_event_profile_schema_contract.py` (A3x-1)
8. `assignment_checkpoint_contract_v3.py` (A4a-R)
9. `assignment_checkpoint_semantic_dispatch.py` (A4a-R)
10. `assignment_checkpoint_entry_guard.py` (A4b)

Existing production/integration source modified under A1b/A1c/A4b authority:

- `scenario_config.py`;
- `assignment_harl_wrapper.py`;
- `assignment_lifecycle_training_contract.py`;
- `assignment_harl_training.py`;
- `assignment_checkpoint_save.py`;
- `assignment_checkpoint_load.py`;
- `assignment_training_run_audit.py`;
- `scripts/reinforcement_learning/harl/train.py`;
- `scripts/reinforcement_learning/harl/play_assignment.py`;
- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`;
- `scripts/environments/evaluate_assignment_methods.py`;
- `scripts/environments/diagnose_assignment_controller_feasibility.py`.

A1c is authority/readiness wiring; A4b is the approved semantic-entry exception;
A6-R adds only the canonical resolved-profile binding in the wrapper schema
manifest. None is event runtime MRTA implementation.

Tests added (and in several cases extended in later packages):

- `test_assignment_profile_contract.py`;
- `test_assignment_profile_production_wiring.py`;
- `test_assignment_lifecycle_transition_contract.py`;
- `test_assignment_event_gated_mrta_contract.py`;
- `test_assignment_team_reward_contract.py`;
- `test_assignment_event_gated_diagnostics_contract.py`;
- `test_assignment_event_profile_schema_contract.py`;
- `test_assignment_checkpoint_semantic_dispatch.py`;
- `test_assignment_checkpoint_entry_guard_integration.py`;
- `test_assignment_phase_a_default_off_identity.py`.

Temporal changes are explicit: profile tests grew in A1b/A1c; transition and
MRTA tests grew for events/A3x; reward/diagnostic tests grew in A5.

The pre-A6 untracked documentation cohort is:

- `AgentRead/20260727/PHASE_A_IMPLEMENTATION_PLAN_TARGETED_REVISION_SUMMARY.md`;
- `AgentRead/20260727/PHASE_A_PURE_INTERFACE_IDENTITY_DIAGNOSTICS_IMPLEMENTATION_PLAN.md`;
- `AgentRead/20260727/PHASE_A1A_PURE_PROFILE_REGISTRY_RESOLVED_IDENTITY_IMPLEMENTATION_REPORT.md`;
- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A_PLAN_DESIGN_20260727.md`;
- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A_PLAN_TARGETED_REVISION_20260727.md`;
- `AgentRead/20260727/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A1A_IMPLEMENTATION_20260727.md`;
- `AgentRead/20260729/PHASE_A1B_SCENARIO_PROFILE_PROPAGATION_IMPLEMENTATION_REPORT.md`;
- `AgentRead/20260729/PHASE_A1C_PRODUCTION_RESOLVED_PROFILE_AUTHORITY_IMPLEMENTATION_REPORT.md`;
- `AgentRead/20260729/PHASE_A2_TRANSITION_AUTHORITY_CONTRACT_IMPLEMENTATION_REPORT.md`;
- `AgentRead/20260729/PHASE_A3_TYPED_EVENT_MRTA_REWARD_DIAGNOSTICS_CONTRACT_IMPLEMENTATION_REPORT.md`;
- `AgentRead/20260729/PHASE_A4A_V3_INTERFACE_DESCRIPTOR_AND_SEMANTIC_DISPATCH_REPORT.md`;
- `AgentRead/20260729/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE_A1B_IMPLEMENTATION_20260729.md`;
- `AgentRead/20260803/PHASE_A3X0_EVENT_SCHEMA_FREEZE_DESIGN.md`;
- `AgentRead/20260803/PHASE_A3X1_EVENT_PROFILE_SCHEMA_DESCRIPTOR_IMPLEMENTATION_REPORT.md`;
- `AgentRead/20260807/PHASE_A4A_V3_INTERFACE_DESCRIPTOR_AND_SEMANTIC_DISPATCH_IMPLEMENTATION_REPORT.md`;
- `AgentRead/20260808/PHASE_A4B_CHECKPOINT_ENTRY_SEMANTIC_GUARD_INTEGRATION_REPORT.md`;
- `AgentRead/20260808/PHASE_A5_DIAGNOSTICS_AND_REWARD_SEMANTIC_CONFIGURATION_REPORT.md`.

Original A6 added its dedicated test and this report. A6-R then modified only
`assignment_harl_wrapper.py` and that dedicated test in production/test scope,
added `PHASE_A6R_TARGETED_DEFAULT_OFF_IDENTITY_REPAIR_REPORT.md`, and updated
this report. `TASK_PROGRESS.md` is maintained in place; this report records no
new TASK archive.

Explicit runtime-sensitive paths not modified by Phase A are:

- `assignment_checkpoint_contract.py`;
- `scan_mobile_manipulator_env.py`;
- `assignment_state.py`;
- `assignment_lifecycle_observation.py`;
- `assignment_lifecycle_resolver.py`;
- `assignment_lifecycle_resolver_runtime.py`;
- `assignment_lifecycle_diagnostics.py`;
- `assignment_playback_attribution_diagnostics.py`;
- `assignment_initial_condition.py`;
- `agents/harl_happo_cfg.yaml` and all YAML;
- installed `harl/**`.

This means “Phase A did not modify the path,” not “the repository has always
matched upstream.”

## 25. Installed HARL/no-runtime-change audit

Installed HARL was read-only where static callable/branch evidence was needed
and was not modified. No optimizer step, actor update, backward, full replay,
training, or package write occurred.

```text
Isaac/AppLauncher execution:          none
assignment env reset/step in A6:      none
actor update/optimizer/backward:      none
training/playback/evaluation:         none
real checkpoint tensor save/load:     none
load_state_dict/live model mutation:  none
installed HARL modification:          none
commit:                               none
```

One observation-integration audit attempt crossed only Python package import
and stopped on missing `omni.kit` before any test body, AppLauncher, environment,
reset/step, or rollout. It is a deferred-audit fact, not runtime evidence.

## 26. Known limitations and risk

The original A6 review recorded four material pure-evidence gaps in addition to
the production `NameError`: first-probe digests, a non-discriminating
Contract-C resolver fixture, a profile-only clean child, and two inexact
surface literals. A6-R closes all four through H1--H4 and repairs the one
production regression. The final `16/16` result therefore closes, at the
declared pure/static/manifest level:

- canonical profile identity and default-off route selection;
- existing-profile mapping semantics and frozen V2/V3 manifest goldens;
- typed lifecycle/MRTA/reward/diagnostic interfaces;
- distinct event V3 semantic identity;
- Phase-A checkpoint fail-closed boundaries;
- legacy/Contract-C default-off pure/static identity;
- no unintended event sink/config/file/RNG expansion in exercised pure paths.

The six tensor digests remain secondary reproducibility evidence only. Primary
tensor identity is independent test-side assembly plus exact `torch.equal`;
this distinction is a standing evidence limitation, not an unresolved gap.

Phase A does **not** prove:

- real Isaac environment runtime identity;
- real pre-reset lifecycle capture;
- real lifecycle mutation/termination;
- event local-set/Top-K/cost execution;
- event resolver/atomic commit;
- DVM actor sampling or trainer behavior;
- rollout-buffer DVM;
- HAPPO valid-only loss;
- sequential-factor runtime identity;
- team reward runtime;
- diagnostic runtime producer/sink;
- real checkpoint-ready V3;
- V3 state-dict compatibility or weight save/load;
- training, playback, evaluation, or statistical performance.

The largest risk is Phase C runner/trainer integration: per-actor DVM,
zero-valid complete skip, finite singleton handling, and exact nondecision
factor ratio one must coexist with all-valid-physical-step critic GAE/ValueNorm.
Other risks are pre-reset authority/terminal-sidecar ordering, remaining-time
estimation, component closure/atomicity, runtime same-object propagation,
reward transport, diagnostic throughput, and V3 state-dict identity. The
`M=3,N=50` V3 golden proves none of those runtime obligations.

## 27. Phase A done-gate assessment

| Done-gate item | Assessment |
|---|---|
| A1--A5 review passed | satisfied by A6 authority |
| D0, D1 legacy, D1 Contract C, scenario correction | exact pure cohorts pass; canonical manifest binding passes |
| all 19 surfaces classified | independent exact ordered tuple, length, uniqueness, and evidence counts pass |
| observation/shared/action/mask | independent assembly plus exact `torch.equal`, shape/dtype/device/order/every-mask-entry checks pass |
| proposal/effective/reward | exact; Contract-C conflict fixture discriminates enabled resolver from clone; rollout/env deferred |
| actor/log-prob/GAE/ValueNorm/factor/minibatch | `STATIC-ROUTE-EXACT`; execution prohibited/deferred |
| logger/RNG/files | expanded clean-child exact/static pure boundary; real run deferred |
| V2 | 5509/7234 bytes and frozen hashes exact |
| V3 | 67794 bytes and frozen hash exact |
| ablation/diagnostics routes | unchanged static/manifest identity |
| event | interface-only and fail-closed |
| runtime rows | machine inventory exactly 23/23 `DEFERRED-RUNTIME-IDENTITY-EVIDENCE`; broader ownership table remains deferred |
| numeric TBDs | exactly 11, all unresolved |
| canonical regressions | 143/143 plus optional 4/4 |
| historical audit | seven scripts 100/100; five explicitly deferred |
| original A6 result | historical `13/15`; STOP on `NameError` preserved |
| A6-R production change | `assignment_harl_wrapper.py` only; one canonical binding line |
| A6-R hardening/result | H1--H4 complete; intermediate 15/16 secondary-digest-only failure; final 16/16 |
| installed HARL change | none |
| Isaac/training/playback/eval/tensor I/O | none |
| B0 | not entered |
| commit | none |
| **Phase A done gate** | **PASSED at the declared pure/static/manifest evidence level; awaiting GPT/user review** |

```text
dedicated suite:
  original A6: 13/15; STOP; NameError
  final A6-R: 16/16; pass
completion gate:
  COMPLETE TO DECLARED PURE/STATIC/MANIFEST LEVEL
runtime identity:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE
```

## 28. Next gate: final GPT/user review; B0 not authorized

The targeted A6-R repair and pure/static/manifest revalidation are complete.
The next gate is final GPT/user review of Phase A, not B0. This report does not
authorize runtime identity work or any B0/B/C/D/E implementation.

Only after Phase A receives final review could B0 be considered. A future
explicit B0 authorization would still
need pre-autoreset capture, producer/authority placement, generation/token
alignment, completed/released ownership, cumulative failed pair,
`TEAM_INFEASIBLE`, termination, terminal critic-sidecar ordering, completion
attribution, and diagnostics at that boundary.

B0 must not assume that fake tensors prove Isaac startup, that scheduler/local
set exists, that DVM reaches HARL, that V3 is checkpoint-ready, or that any of
the 11 numeric values is chosen. This report authorizes no B0/B/C/D/E work.

## 29. Final classification

```text
classification:
  PHASE-A-PURE-INTERFACE-IDENTITY-DIAGNOSTICS-COMPLETE-AWAITING-GPT-REVIEW

Phase A:
  complete to declared pure/static/manifest evidence level
  stopped for final GPT/user review
default-off identity:
  CLOSED AT PURE/STATIC/MANIFEST EVIDENCE LEVEL
original A6 closeout:
  STOP — PHASE-A DEFAULT-OFF IDENTITY GAP
  13/15 passed; exit 1
  NameError: name 'profile_name' is not defined
A6-R:
  canonical one-line wrapper repair complete
  H1--H4 evidence hardening complete
dedicated A6 suite:
  final 16/16 passed
canonical A1--A5:
  143/143 passed
historical audited-safe:
  100/100 passed
runtime identity:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE
event runtime assignment behavior:
  not implemented
V3 interface:
  implemented
V3 checkpoint-ready:
  unavailable
V3 weight use:
  unauthorized
11 numeric method parameters:
  unresolved
Isaac/AppLauncher:
  not run
actor update/optimizer:
  not run
training/playback/evaluation:
  not run
real checkpoint tensor I/O:
  none
installed HARL:
  unchanged
commit:
  none
B0:
  not entered
  not authorized
B/C/D/E:
  not entered
```

Phase A stops here for final GPT/user review. Its declared pure/static/manifest
evidence is complete; runtime identity remains deferred. B0 is not entered and
not authorized, and this report authorizes no B/C/D/E work.
