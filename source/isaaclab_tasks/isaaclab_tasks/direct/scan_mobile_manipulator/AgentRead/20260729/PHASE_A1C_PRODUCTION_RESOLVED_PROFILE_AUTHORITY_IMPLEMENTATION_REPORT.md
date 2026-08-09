# Phase A1c Production Resolved-Profile Authority Implementation Report

## 1. Classification

```text
classification:
  PHASE-A1C-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

authorized implementation:
  A1c production resolved-profile authority only

A1a:
  complete
  review passed

A1b:
  complete
  review passed

A1c:
  complete by pure/static evidence

A2–A6:
  not entered

Phase B0/B/C/D/E:
  not entered

runtime event route:
  Phase-A fail-closed

commit:
  none
```

No A1c blocker was found. The production authority chain, same-object
parameter chain, existing-profile bypass, direct/fake fallback, and event
readiness barriers are implemented. Evidence is deliberately limited to
compile plus pure/static tests; no Isaac runtime claim is made.

## 2. Authorization and scope

The direct authorization was the user instruction classified
`PHASE-A1C-IMPLEMENTATION-AUTHORIZED`.

Implemented:

- primitive pre-AppLauncher event-profile preflight;
- post-compose canonical profile finalization;
- one formal resolved identity per formal entrypoint;
- raw/resolved/origin/class mismatch validation;
- same-object runner → env facade → wrapper propagation;
- direct/fake wrapper fallback with a distinct origin;
- exact existing-profile mapping consumption;
- event-profile fail-closed barriers;
- resolved-identity training-contract dispatch;
- five formal-entrypoint wiring;
- pure/static A1c regressions.

Not implemented:

- lifecycle transition DTOs or pre-reset facts capture;
- event-gated assignment ticks, local sets, Top-K, DVM, or proposal sampling;
- component resolver changes;
- reward, buffer, trainer, HAPPO factor, or logger changes;
- checkpoint v3 manifest/dispatcher or any checkpoint I/O;
- runtime event-profile execution.

## 3. Starting repository state

Starting and ending HEAD:

```text
dca976001d8c53a9cfb424b468fa58d9fca367f6
```

Starting log:

```text
dca97600 docs(assignment): approve event-gated local MRTA design for Phase A
e3febe41 docs(assignment): validate multi-condition late-training regression
9d31b15f add deterministic baseline and cyclic pose-slot profiles ...
```

The starting worktree matched the known Phase A/A1a/A1b cohort:

- modified `AgentRead/TASK_PROGRESS.md`;
- A1a contract/test/report and Phase A documents;
- A1b `scenario_config.py`, test extension, report, and archive.

The index was empty, `git diff --check` passed, and no unknown code,
configuration, result, or checkpoint change was present.

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

## 4. Files changed

A1c production:

- `assignment_profile_contract.py`;
- `scenario_config.py`;
- `assignment_harl_wrapper.py`;
- `assignment_lifecycle_training_contract.py`;
- `assignment_harl_training.py`;
- `scripts/reinforcement_learning/harl/train.py`;
- `scripts/reinforcement_learning/harl/play_assignment.py`;
- `scripts/environments/evaluate_assignment_rl_playback_diagnostics.py`;
- `scripts/environments/evaluate_assignment_methods.py`;
- `scripts/environments/diagnose_assignment_controller_feasibility.py`.

A1c tests:

- extended `scripts/environments/test_assignment_profile_contract.py` so its
  static wrapper golden verifies the new canonical mapping consumer;
- added
  `scripts/environments/test_assignment_profile_production_wiring.py`.

A1c documentation:

- added this report;
- updated top-level `AgentRead/TASK_PROGRESS.md`.

No A1c TASK archive was created. The existing 300-line handoff was readable and
did not meet the authorization's archive/condense threshold.

## 5. Formal resolution authority

`assignment_profile_contract.py` now defines:

- `ResolvedProfileMismatchError`;
- `PhaseAExecutionNotAuthorizedError`;
- `resolve_or_validate_assignment_profile_authority()`;
- `require_assignment_profile_runtime_ready()`.

Authority rules:

1. A missing raw declaration is explicitly interpreted as the current
   `legacy` default.
2. A supplied object must have one of the two exact canonical class identities.
3. A supplied object is returned unchanged; it is not copied, serialized, or
   re-resolved.
4. `FORMAL_ENTRYPOINT` plus a missing object fails before fallback.
5. Only `DIRECT_WRAPPER_FALLBACK` with the direct fallback enabled can resolve
   a missing object.
6. Raw profile, object profile, and expected origin must match.
7. Mismatch is checked before readiness, so event-raw/existing-object and
   existing-raw/event-object cases are mismatch failures.
8. A matching event object reaches the typed Phase A readiness failure.

Each formal entrypoint contains exactly one final lexical call:

| Entrypoint | Formal resolve count | Origin |
|---|---:|---|
| `train.py` | 1 | `FORMAL_ENTRYPOINT` |
| `play_assignment.py` | 1 | `FORMAL_ENTRYPOINT` |
| RL playback diagnostics | 1 | `FORMAL_ENTRYPOINT` |
| assignment-method evaluation | 1 | `FORMAL_ENTRYPOINT` |
| controller feasibility diagnosis | 1 | `FORMAL_ENTRYPOINT` |

The registry's import-time self-validation constructs temporary equal values.
Those are registry integrity checks, not formal final identities, and are not
counted as entrypoint resolutions.

## 6. Same-object propagation

The supported assignment training chain is:

```text
train.py local resolved object
is AssignmentOnPolicyHARunner.resolved_assignment_profile
is AssignmentIsaacLabEnv.resolved_assignment_profile
is AssignmentHarlWrapper.resolved_assignment_profile
```

The object is passed as an explicit Python constructor keyword. Runner,
facade, and wrapper validate it but never resolve it again. Runtime assertions
also check runner/facade and facade/wrapper object identity.

The installed HARL render-env branch bypasses the repo-local facade/wrapper.
A1c now fails assignment `render.use_render=True` before RNG, output, or env
initialization instead of allowing that authority bypass. The normal existing
assignment-training configuration already uses `use_render=False`.

Playback, RL diagnostics, and controller diagnosis pass their entrypoint object
through `make_assignment_harl_env()` to the wrapper. The assignment-method
baseline resolves and readiness-checks the profile but does not construct an
assignment wrapper; its already hard-blocked/unreachable assignment-RL helper
now explicitly uses formal-missing authority, so it cannot silently fall back
if the preceding hard block is ever removed.

Evidence level:

```text
pure helper object identity:
  demonstrated

production parameter chain:
  AST/static demonstrated

Isaac runtime object identity:
  DEFERRED-RUNTIME-IDENTITY-EVIDENCE
```

## 7. Direct-wrapper fallback

Direct/fake compatibility uses the distinct default context:

```text
AssignmentProfileResolutionOrigin.DIRECT_WRAPPER_FALLBACK
```

Results:

| Case | Result |
|---|---|
| direct existing profile, no object | resolve once; existing route |
| direct factory → wrapper | one total resolve; wrapper validates same object |
| direct event profile | resolve once; typed readiness failure |
| formal origin, no object | typed mismatch; zero fallback resolves |
| supplied direct object in formal context | origin mismatch |
| supplied formal object in direct context | origin mismatch |

Formal production callsites explicitly pass `FORMAL_ENTRYPOINT`; the direct
default therefore cannot act as an implicit formal-entrypoint fallback.

## 8. Existing-profile direct bypass

`AssignmentHarlWrapper` now establishes/validates authority immediately after
binding `env/unwrapped`, before agents, reward/cooldown configuration, resolver,
observation/mask layout, logger, or controller behavior.

For the four existing subtypes, `_build_assignment_lifecycle_profile_config()`
performs the existing low-level prerequisite checks and returns exactly:

```python
resolved_profile.to_legacy_wrapper_mapping()
```

The A1a golden confirms exact key/value/insertion-order identity for:

- `legacy`;
- `lifecycle_ablation`;
- `lifecycle_contract_c`;
- `diagnostics_hidden_state`.

The event subtype is rejected before this dispatch. There is no final
diagnostics catch-all and no event runner simulated with DVM all ones.

Training-contract dispatch also consumes the resolved object:

| Profile | Current policy sequence/training result |
|---|---|
| legacy | existing-config-selected policy sequence; training allowed |
| lifecycle ablation | `not_training_enabled`; training blocked |
| Contract C | HAPPO/EP/non-shared/feed-forward/state-dict checks retained |
| diagnostics hidden state | diagnostics-only; training blocked |
| event-gated local MRTA | typed Phase-A runtime block |

## 9. Event-profile fail-closed ordering

Two barriers are used.

### Prelaunch-visible declarations

`scenario_config.py` contains primitive-only helpers that inspect:

- scenario/default declarations;
- explicit Hydra CLI overrides such as
  `env.assignment_lifecycle_profile=...`;
- `+`/`++` variants of that explicit override.

Visible event profiles fail with stable code
`ASSIGNMENT_EVENT_PROFILE_PRELAUNCH_BLOCKED` before:

- `validate_smoke_args()` and its possible result-parent creation;
- path/output validators;
- CUDA warm-start;
- AppLauncher construction.

The helper imports no canonical enum/dataclass/custom exception and creates no
resolved identity.

### Post-compose values

After package bootstrap and final env/scenario composition, each formal
entrypoint:

```text
finalize primitive canonical string
→ resolve once with FORMAL_ENTRYPOINT
→ typed readiness guard
→ entrypoint-owned runtime/file work
```

Static barrier matrix:

| Entrypoint | Guard precedes |
|---|---|
| train | runner registry mutation/construction, RNG, run directory, env, actor, critic, logger, checkpoint |
| play | model path/checkpoint, env/wrapper, actor, attribution sink, play loop |
| RL diagnostics | model/output directory, env/wrapper, actor, checkpoint, diagnostic sink, evaluation loop |
| methods | seed/RNG, environment/evaluation, output paths/files |
| controller diagnosis | env/wrapper, controller diagnostics, output directory/file |

Defense-in-depth barriers also occur:

- runner before RNG/device/output/env/actor/checkpoint;
- env facade before `gym.make`;
- wrapper factory before `gymnasium.make`;
- wrapper before existing profile/resolver/observation/mask branches.

Hydra caveat: a value discoverable only through Hydra composition reaches the
original decorated `main()` after Hydra itself has run. A1c proves rejection
before every entrypoint-owned output/runtime side effect; it does not claim
that Hydra's framework internals created no bookkeeping artifact. Explicit raw
Hydra profile overrides are caught prelaunch, and the current registry default
is `legacy`.

## 10. Contract C raw/effective resolver semantics

A1c preserves the A1b/current-code interpretation:

```text
raw assignment_lifecycle_resolver_enabled:
  absent / false / true are all accepted for Contract C

effective resolver_enabled:
  true from ResolvedExistingAssignmentProfile identity
```

The three raw cases all produced:

```text
to_legacy_wrapper_mapping()["resolver_enabled"] == true
```

The existing low-level requirements remain:

- cooldown enabled;
- trigger mode `budget` or `budget_and_streak`;
- positive cooldown duration;
- cooldown action-mask application disabled;
- redirect guardrail disabled;
- failed-pair memory disabled.

No raw-true prerequisite was added.

## 11. Entrypoint coverage

Formal production wrapper/factory inventory:

- train:
  `RUNNER_REGISTRY → AssignmentOnPolicyHARunner → make_assignment_train_env
  → AssignmentIsaacLabEnv → AssignmentHarlWrapper`;
- playback: one formal `make_assignment_harl_env`;
- RL playback diagnostics: one formal factory call;
- controller feasibility: one formal factory call;
- assignment methods: one hard-blocked/unreachable formal-missing factory call.

Production-internal wrapper constructors:

- `make_assignment_harl_env → AssignmentHarlWrapper`;
- `AssignmentIsaacLabEnv → AssignmentHarlWrapper`.

Direct/fake `AssignmentHarlWrapper(...)` inventory:

- 11 calls across cooldown, failed-pair, lifecycle controlled-training,
  feed-forward, observation-integration, and lifecycle mask/replay tests.

Test-only AppLauncher factory inventory:

- wrapper smoke;
- fresh-policy smoke;
- episode-reset smoke.

No unclassified sixth formal production wrapper caller was found. The dynamic
runner call is tracked through `RUNNER_REGISTRY`; a literal-constructor-only
search would miss it.

## 12. Mismatch and error matrix

| Raw/env profile | Resolved object/context | Result |
|---|---|---|
| legacy | formal resolved legacy | pass, same object |
| Contract C | formal resolved Contract C | pass, same object |
| existing A | resolved existing B | `ResolvedProfileMismatchError` |
| event | resolved existing | mismatch before readiness |
| existing | resolved event | mismatch before readiness |
| event | matching resolved event | `PhaseAExecutionNotAuthorizedError` |
| missing raw | formal resolved legacy | pass as explicit current default |
| missing object | formal context | typed fail; no fallback |
| same-looking foreign class | any | canonical class/module identity failure |
| origin mismatch | any | typed failure |

Error strings carry raw/resolved profile context, expected/actual origin or
class, entrypoint/consumer, and the profile contract version. Event errors also
carry runtime route, readiness, current phase, consumer, and barrier.

## 13. Config/default-off identity

The resolved object exists only:

- as a local Python variable;
- as an explicit constructor parameter;
- as a process-local consumer attribute.

It is not written into:

- argparse args;
- `env_args`;
- `env_cfg`;
- Hydra/OmegaConf;
- `configs.json`;
- scenario YAML/JSON;
- checkpoint manifest;
- logger/TensorBoard/CSV/JSONL.

D0 absent behavior:

- primitive finalization selects `legacy`;
- no resolved field is injected into config;
- A1a/A1b clean-child state remains exact;
- no new diagnostic sink, info key, file, or RNG call is created.

Pure side-effect evidence recorded unchanged:

- Python random state;
- cwd;
- environment variables;
- `sys.path`;
- root logger handlers;
- temporary directory contents.

Forbidden Isaac/AppLauncher/HARL/torch modules were absent from the A1c pure
harness.

## 14. Tests and command results

Final compile:

```text
python -m py_compile <12 changed Python files>
exit code: 0
```

A1a/A1b regression:

```text
python scripts/environments/test_assignment_profile_contract.py --json
exit code: 0
A1a: 11/11
A1b: 5/5
combined: 16/16
```

A1c production wiring:

```text
python scripts/environments/test_assignment_profile_production_wiring.py --json
exit code: 0
10/10
```

Coverage includes:

- formal authority and complete mismatch matrix;
- direct fallback exact resolve counts;
- primitive scenario/Hydra preflight;
- Contract C raw resolver absent/false/true;
- same-object helper and production parameter chain;
- resolved-identity training routes;
- five-entrypoint ordering and resolve inventory;
- runner/facade/factory/wrapper barriers;
- canonical import and no-serialization AST;
- exact wrapper callsite inventory;
- pure process/file side-effect snapshots.

Historical module-identity regression:

```text
python scripts/environments/test_assignment_initial_condition_contract.py --json
final exit code: 0
9/9
```

One intermediate invocation exited 1 because an initial A1c edit changed the
textual signature of `_attach_initial_condition_request`. That nonessential
change was reverted; the resolved-profile authority chain to the wrapper was
retained, and the final historical regression passed 9/9.

No runtime smoke or checkpoint test was run.

Final repository checks:

```text
git status --short --untracked-files=all
exit code: 0
result: only the known Phase A/A1a/A1b cohort plus the authorized A1c files

git diff --name-status
exit code: 0
result: only authorized tracked production/entrypoint/TASK_PROGRESS changes

git diff --check
exit code: 0

git diff --cached --name-status
exit code: 0
result: empty index

git rev-parse HEAD
exit code: 0
result: dca976001d8c53a9cfb424b468fa58d9fca367f6
```

## 15. Side-effect audit

Not run:

- AppLauncher or Isaac environment construction;
- assignment wrapper/runtime execution;
- actor/critic construction or inference;
- training/optimizer/update;
- playback or formal evaluation;
- checkpoint metadata or tensor I/O.

Not modified:

- environment, resolver, observation, action mask, reward, buffer, trainer,
  controller, or checkpoint modules;
- YAML/JSON;
- package `__init__.py`;
- installed HARL.

No commit was created.

## 16. Deferred A2 work

Still not authorized:

- transition facts/result schema;
- facts producer/lifecycle authority stamps;
- generation/token/consume-once ledger;
- observable alias-isolation/mutation detection;
- pair-attribution assertions.

No A2 source file or test was created.

## 17. Risks and blockers

Blockers:

```text
none within A1c
```

Residual review risks:

1. Same-object production execution is supported by pure identity and AST
   evidence only. Actual Isaac startup remains deferred.
2. Hydra-internal output behavior for a config-only value is outside the
   entrypoint barrier. Explicit raw Hydra overrides are preflight-blocked.
3. Several historical fake suites still import wrapper/training files by a
   bare module name. A1c did not add a forbidden bare profile-contract fallback;
   future execution of those suites should migrate their harness to the
   canonical package key.
4. The assignment render bypass is now explicit fail-closed. Review should
   confirm this is the intended authority prerequisite for the existing
   assignment route.
5. Event profile remains interface-only; no checkpoint v3 or event runtime
   readiness may be inferred from this wiring.

## 18. Final classification

```text
classification:
  PHASE-A1C-IMPLEMENTATION-COMPLETE-AWAITING-GPT-REVIEW

evidence:
  pure/static A1c wiring complete

runtime evidence:
  none claimed

deferred runtime evidence:
  Isaac startup and process-level same-object confirmation

event runtime:
  Phase-A fail-closed

existing profiles:
  exact mapping/routes retained by pure/static evidence

Isaac/AppLauncher:
  not run

training/playback/formal evaluation:
  not run

checkpoint I/O:
  none

installed HARL:
  unchanged

commit:
  none

A1c:
  stopped for GPT/user review

A2–A6:
  not entered

Phase B0/B/C/D/E:
  not entered
```
