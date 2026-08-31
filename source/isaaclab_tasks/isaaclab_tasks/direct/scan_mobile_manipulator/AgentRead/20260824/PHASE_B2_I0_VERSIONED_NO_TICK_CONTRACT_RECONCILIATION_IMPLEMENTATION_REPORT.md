# Phase B2-I0 Versioned No-Tick Contract Reconciliation — Implementation Report

Date: 2026-08-24
Classification: `PHASE-B2-I0-VERSIONED-NO-TICK-CONTRACT-RECONCILIATION-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and boundary

The frozen B2-D architecture remains `PHASE-B2-D-REVIEW-PASS / FROZEN`. This slice implements only the pure contract/schema prerequisite B2-I0. It does not implement B2-I1 or a later slice.

```text
Phase B overall:                   NOT COMPLETE
B2-I0 implementation:             COMPLETE, AWAITING GPT REVIEW
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Isaac, AppLauncher, HARL rollout, training, playback, evaluation, and optimizer execution were not run.

## 2. Starting checkpoint

```text
branch: main
starting HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
```

The pre-existing working tree already contained the B2-D design report and its `TASK_PROGRESS.md` update. They were preserved. No commit was created.

## 3. Files changed by B2-I0

Implementation and verification:

- `assignment_event_profile_schema_contract_v2.py` — new isolated pure v2 contract/schema module.
- `scripts/environments/test_assignment_phase_b2_i0_versioned_no_tick_contract_reconciliation_pure.py` — new pure/static 13-oracle fixture.

Documentation/handoff:

- this implementation report;
- `AgentRead/TASK_PROGRESS.md` — rewritten as the concise current handoff;
- `AgentRead/20260824/TASK_PROGRESS_ARCHIVE_BEFORE_B2_I0_HANDOFF_20260824.md` — exact pre-condense handoff archive, required by `AGENTS.md` because the previous file exceeded the concise handoff guideline.

No existing production, runtime, wrapper, runner, buffer, environment, lifecycle-authority, P2/Ak, or installed HARL file was modified by B2-I0.

## 4. Exact v1/v2 strategy

Historical v1 remains the authoritative Phase-A record:

```text
module:  assignment_event_profile_schema_contract.py
version: assignment_event_profile_schema_contract_v1
policy:  preserve byte and semantic identity; never reinterpret in place
```

B2-I0 adds a separate canonical module:

```text
module:  assignment_event_profile_schema_contract_v2.py
version: assignment_event_profile_schema_contract_v2
profile: event_gated_local_mrta
scope:   pure immutable identity, manifest, shape, and validation contracts
```

The v2 module does not import v1 and does not depend on its historical association tuple. It records v1 only as a historical reference. This prevents silent reinterpretation and lets both contracts coexist.

## 5. No-tick identity contract

`EventPolicyEvidenceIdentityV2` captures only:

```text
exact current P2 publication object reference
episode_generations tuple [E]
transition_generations tuple [E]
exact OPEN window object reference
fixed M / fixed N
profile and schema identity
```

There is no assignment-decision clock. The v2 source contains no dependency on the historical assignment tick and no replacement field such as a decision/window/policy/claim tick or decision/window generation.

The two runtime identities are held as private opaque references. Primitive scalar/string identities are rejected at capture, so an OPEN serial cannot be substituted. Validation uses object identity (`is`) for current P2 publication and OPEN window and exact tuple equality for episode/transition generations. A recreated equality-comparable window object is rejected. There is no mutation, normalization, serialization, or rebind path.

Mismatch failures are stable and fail closed:

- `p2_publication_identity_mismatch`;
- `episode_generation_mismatch`;
- `transition_generation_mismatch`;
- `open_window_identity_mismatch`;
- malformed metadata and fixed-cardinality mismatches also fail before acceptance.

This type is binding metadata for the future B2-I1 snapshot. It is not `EventPolicyEvidenceSnapshot`; that producer/projector remains unimplemented.

## 6. Identity metadata exclusion from model inputs

The actor and critic descriptors expose an explicit exclusion oracle. None of these fields occurs in either numerical block list:

```text
p2_publication_identity
episode_generations
transition_generations
open_window_identity
```

The identity descriptor separately freezes `numeric_encoding: forbidden in all model feature forms`, `clock_semantics: none`, and `mutation_or_rebinding: forbidden`. Raw integers, normalization, one-hot encoding, hashing, embedding IDs, relative counters, and window age therefore have no contract route into actor/shared/critic features. Robot-ID one-hot and physical episode progress remain semantic features and are separate from runtime identity metadata.

## 7. Semantic v2 numerical manifests

The manifest retains fixed M/fixed N MLP/HAPPO-compatible shapes. It declares layout but does not build tensors.

| Actor block | Shape |
|---|---:|
| actor robot identity one-hot | `M` |
| robot physical snapshot | `M*16` |
| robot lifecycle state plus availability | `M*5` |
| task pose | `N*7` |
| task lifecycle state | `N*6` |
| task ownership including unowned | `N*(M+1)` |
| current robot owned task including none | `M*(N+1)` |
| failed-pair state | `M*N` |
| explicit physical feasibility | `M*N` |
| explicitly named geometric ranking cost | `M*N` |
| robot workload/completion attribution | `M` |
| physical episode progress fraction | `1` |

The geometric block is explicitly scanner-to-viewpoint Euclidean ranking distance. It is ranking-only and never a feasibility inference. Path validity/path cost, local candidate selection, and retry opportunity remain typed external seams omitted without synthetic defaults.

Dimensions are calculated by resolving and multiplying every manifest block shape and summing the results:

```text
O_v2        = 5*M*N + 24*M + 14*N + 1
M=3, N=12  -> O_v2=421

S_critic_v2 = 5*M*N + 23*M + 14*N + 1
M=3, N=12   -> S_critic_v2=418
```

The centralized critic uses the same global semantic evidence but omits actor-row identity. It is not an actor-observation concatenation. The formulas are audit summaries, not hardcoded return values. A second scale oracle (`M=2,N=4`) derives `O_v2=145` and `S_critic_v2=143`.

Historical `476/497` values remain only compatibility references. Equality to them is not required, no learned event-profile checkpoint is claimed, and no compatibility slot is present. Termination reason remains transition/audit metadata rather than a critic numerical feature.

## 8. Scale, profile, and routing boundaries

The v2 scale contract validates exact fixed M/N, canonical agent/task order, finite positive physical scales, control-step derivation, and integral episode horizon. It adds no variable-cardinality route.

The profile binding resolves frozen `event_gated_local_mrta`, retains `interface_only` readiness, and states that no readiness change is authorized. Existing/default profile files are unchanged.

I0 declares only future routing slot descriptors and shapes for `row_kind`, `forced_action_id`, `policy_sampled`, `decision_valid_mask`, and `available_actions`. Every slot is marked `implemented_in_b2_i0=false`, `numerical_model_feature=false`, and owned by B2-I2. No lifecycle legality, DVM, row classification, forced action, proposal routing, sampling, logprob, or PPO/HAPPO behavior is implemented.

## 9. Historical/default-off preservation evidence

The new fixture checks these protected SHA-256 digests:

| Protected file | SHA-256 |
|---|---|
| `assignment_event_profile_schema_contract.py` | `04eb153f296196e8a098f071fdea3721e27893564b4fa2df81ff91fc088859ef` |
| `assignment_mrta_contract.py` | `73881d20903873ddaaf7b6b6636d008771c030f739d3d2cc8ebb32b79bd1e17c` |
| `assignment_profile_contract.py` | `ece4a58c1636ea3f710775eaac25e12df4097972ef57ec0d15cefec5e6702500` |
| `assignment_harl_wrapper.py` | `f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae` |
| `assignment_harl_training.py` | `b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd` |
| `assignment_event_runtime_facade.py` | `036082d8df61514aa3f3c424ae6559fa678536097b66bfd5bd6f632ca3479478` |
| `assignment_event_proposal_adapter.py` | `874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd` |
| `assignment_initial_claim_runtime.py` | `c74868c84a803108c424827afe9326393428938dce4f6cbd46693da3d4d94fda` |
| `assignment_lifecycle_transaction_runtime.py` | `f7b80540ef1ca39ca103855b7d1db2ffedde950242ec223061d0bf01f32e7c5c` |
| `scan_mobile_manipulator_env.py` | `c19b5de8f73d22fbc8b4c1f6b38dbfc4804d28b6e37b002cdfc4e20d5ecc9c99` |

This directly protects v1, profile/default-off, wrapper/training, runtime facade/adapter, lifecycle mutation, and P2/Ak environment integration. Installed HARL was not modified.

New implementation artifact digests at final verification:

```text
assignment_event_profile_schema_contract_v2.py
  9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955
test_assignment_phase_b2_i0_versioned_no_tick_contract_reconciliation_pure.py
  48065681d27e16850d8c9a8d85ee3a63327d95ea7ef0db8635624eba0e4ef7f4
```

## 10. Pure verification

Verified interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Suite | Mode | Result |
|---|---|---:|
| new B2-I0 pure fixture | normal | `13/13 PASS` |
| new B2-I0 pure fixture | `-I -B` | `13/13 PASS` |
| historical v1 schema fixture | normal | `9/9 PASS` |
| historical v1 schema fixture | `-I -B` | `9/9 PASS` |
| Phase-A default-off identity | normal | `16/16 PASS` |
| Phase-A default-off identity | `-I -B` | `16/16 PASS` |
| profile contract fixture | normal | `16/16 PASS` |
| profile contract fixture | `-I -B` | `16/16 PASS` |
| `py_compile` for new module and fixture | conda interpreter | `2/2 PASS` |

The first authoring run of the new fixture reported `12/13`: the implementation-derived `M=2,N=4` result was correct, while the manually entered test expectation was arithmetically wrong. The oracle was corrected from `151/149` to the manifest-derived `145/143`; implementation semantics were not changed for that failure. Both final modes then passed `13/13`.

Import/isolation coverage proves canonical-module fail-fast behavior, no bare alias, no stdout/stderr, no current-directory/environment/file mutation, and no import of Isaac, HARL, torch, or numpy. Temporary bytecode outputs used for compilation were removed.

Final `git diff --check` and the separate untracked-file trailing-whitespace scan passed. Protected hashes matched, the changed-file scope matched this report, and no temporary compile output remained.

## 11. Remaining blockers

B2-I0 resolves only the versioned contract prerequisite. Remaining blockers include B2-I1 evidence capture/projectors; B2-I2 DVM/row/decision bundle; subset sampling and full-index HAPPO accounting; the pre-reset terminal critic sidecar; learner/buffer transport and TIME_LIMIT/GAE semantics; learned proposal/logprob transport; the public learned-policy route; and final readiness review.

External path/local/retry producers and all eleven numeric TBDs remain separately deferred. Transformer, GNN, Set Transformer, variable cardinality, and arbitrary-cardinality checkpoints remain out of scope.

## 12. Stop and next authorization boundary

No B2-I0 architectural STOP condition was encountered. The contract layer represents frozen P2/episode/transition/OPEN binding without a new clock, historical rewrite, runtime-authority change, DirectMARLEnv change, installed HARL change, projector, DVM, or variable-cardinality redesign.

```text
next proposed slice: B2-I1 — Immutable policy evidence snapshot and current projectors
status: NOT AUTHORIZED
```

Work stops here pending GPT independent review and explicit user authorization.

## 13. Final classification

```text
classification:
  PHASE-B2-I0-VERSIONED-NO-TICK-CONTRACT-RECONCILIATION-COMPLETE-AWAITING-GPT-REVIEW
design:
  B2-D FROZEN
implementation:
  B2-I0 COMPLETE
tests:
  PASS
Isaac:
  NOT RUN
HARL runtime:
  NOT RUN
training/playback/evaluation:
  NOT RUN
runtime readiness:
  BLOCKED
policy readiness:
  BLOCKED
learner readiness:
  BLOCKED
training:
  NOT AUTHORIZED
commit:
  NONE
```
