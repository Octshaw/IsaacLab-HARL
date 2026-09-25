# Phase B2-I5a Historical Learner Transport, Timeout Critic, and Buffer — Implementation Report

Date: 2026-08-25

Classification: `PHASE-B2-I5A-HISTORICAL-LEARNER-TRANSPORT-TIMEOUT-CRITIC-AND-BUFFER-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and authorization boundary

```text
B2-D:                              REVIEW PASS / FROZEN
B2-I0:                             REVIEW PASS / CLOSED
B2-I1:                             REVIEW PASS / CLOSED
B2-I2:                             REVIEW PASS / CLOSED
B2-I3a:                            REVIEW PASS / CLOSED
B2-I3b:                            REVIEW PASS / CLOSED
B2-I4:                             REVIEW PASS / CLOSED
B2-I5a:                            IMPLEMENTED / AWAITING GPT REVIEW
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-I5a was implemented. B2-I5b return/GAE/ValueNorm semantics, B2-I6 public composition, B2-V1/V2 verification, and B2-R readiness review were not started.

## 2. Starting checkpoint and frozen authority

```text
branch:  main
HEAD:    14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
B2-I4 review authority: REVIEW PASS / CLOSED, supplied by the user
```

The committed Lifecycle Runtime Backbone checkpoint and all uncommitted B2-D through I4 artifacts were preserved. No commit was created.

The implementation preserves:

- P2 as sole current lifecycle/ownership authority;
- proposal distinct from effective assignment and original actor logprob semantics;
- M1/B1 as the proposal-driven ownership mutation transaction;
- final current P2 -> Ak -> controller as the only physical-control chain;
- EXECUTING continuation as persistent ownership, not repeated selection;
- previous-episode terminal history distinct from post-autoreset current state;
- safe historical copy before runtime ACK;
- runtime ACK distinct from learner consumption, critic evaluation, buffer insertion, or training;
- default-off and fixed M/N MLP/HAPPO boundaries.

No I4 lifecycle/sidecar authority was redesigned.

## 3. Source interface audit

The implementation began from the frozen B2-D, I4, and I3b reports plus `TASK_PROGRESS.md` and `AgentRead/AGENTS.md`.

Repo-local source audited:

- `assignment_event_terminal_transport.py`
- `assignment_event_terminal_critic_sidecar.py`
- `assignment_event_runtime_facade.py`
- `assignment_harl_wrapper.py`
- `assignment_harl_training.py`
- `assignment_event_policy_decision.py`
- `assignment_event_policy_evidence.py`
- `assignment_lifecycle_transaction_runtime.py`

Installed HARL was read only:

- `harl/runners/on_policy_base_runner.py`
- `harl/runners/on_policy_ha_runner.py`
- `harl/common/buffers/on_policy_critic_buffer_ep.py`
- `harl/algorithms/critics/v_critic.py`

The real interfaces are:

```text
VCritic.get_values(cent_obs, rnn_states_critic, masks)
  -> (values, next_rnn_states_critic)

OnPolicyCriticBufferEP.insert(...), at current buffer step t:
  share_obs[t+1]
  rnn_states_critic[t+1]
  value_preds[t]
  rewards[t]
  masks[t+1]
  bad_masks[t+1]
```

Installed `OnPolicyBaseRunner.insert()` resets done-row RNN state, builds masks, derives `bad_masks` only from `infos[env][0]["bad_transition"]`, and inserts returned share observations at state slot `t+1`. Installed proper-time-limit GAE cannot express the required pre-reset timeout bootstrap. No installed source was modified.

## 4. Changed files

Implementation:

- `assignment_event_terminal_learner_transport.py` — new bounded learner DTO, pre-step expectation, six-tuple infos attachment, exact runner correlation, typed timeout-only critic input, critic snapshot guard, batched no-grad evaluation, and full-E scatter result.
- `assignment_event_critic_buffer.py` — new repo-local EP critic-buffer subclass with I5a transition fields and a dormant/private exactly-once collector.

Verification:

- `scripts/environments/test_assignment_phase_b2_i5a_historical_learner_transport_timeout_critic_buffer_pure.py` — new 11-oracle pure/static/synthetic fixture.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No wrapper, public runner, training entrypoint, actor collection/math, policy/DVM, I4 sidecar/terminal transport, lifecycle transaction, environment, DirectMARLEnv, installed HARL, configuration, checkpoint, or readiness gate was modified.

## 5. Historical learner DTO schema

`EventTerminalLearnerRecordV2` is constructed only from an exact `EventTerminalHistoricalRow` after the facade has already completed safe copy and runtime ACK. It retains bounded values only:

```text
schema/profile identity
exact (env_id, episode_generation, transition_generation) correlation key
termination_reason
terminated / truncated
result and authority contract versions
published store version
I4 sidecar/profile/scale/critic schema versions
critic dimension/dtype/device
bootstrap_projection_valid
opaque finalized-P2 publication identity metadata
cloned TERMINAL_AUDIT projection
bounded immutable physical provenance metadata
optional cloned bootstrap_critic_obs
```

The learner record does not retain a runtime artifact, terminal slot, historical-row pointer, environment object, lifecycle writer, P2 view, ACK capability, critic value, optimizer state, proposal, resolver result, effective assignment, or controller input.

Both audit and timeout tensors receive a second detached contiguous clone. The DTO therefore remains valid after the runtime slot is acknowledged, destroyed, or reused.

## 6. Six-element HARL return and infos transport

`attach_event_terminal_infos_to_harl_step_v2()` is a dormant/private transport helper. It requires:

- an exact six-element HARL result;
- one exact private facade step result;
- one runner-owned pre-step transition expectation captured from the sealed I2 decision bundle.

It returns exactly six elements and preserves object identity for slots 0, 1, 2, 3, and 5. Only the fifth element is copied and augmented:

```text
infos[env_id][0]["_assignment_event_terminal_learner_v2"]
  = EventTerminalLearnerRecordV2
```

No seventh return value was added. Nonterminal rows carry no DTO. The reserved DTO key must be absent from base infos and only agent cell zero may carry it. Correlation removes the private typed value into a sanitized copied infos structure before ordinary logging.

The current public event-policy `AssignmentHarlWrapper.step()` remains blocked. `AssignmentIsaacLabEnv` and `AssignmentOnPolicyHARunner` remain unchanged; B2-I6 must later compose this already-tested private transport rather than activating it in I5a.

## 7. Exact transition expectation and correlation

`EventLearnerTransitionExpectationV2` is captured from the exact sealed `EventPolicyDecisionBundle` before the physical step. It retains validation metadata only:

```text
P2 publication identity
OPEN window identity
episode_generation[E]
source transition_generation[E]
expected completed transition_generation[E] = source + 1
```

It adds no clock or decision tick. The facade transport validates the exact source P2 identity and generations. It also verifies:

```text
current transition generation = source + 1
current episode generation = source episode + done/autoreset indicator
```

Runner correlation cross-validates each terminal DTO against:

```text
infos env row
exact expected key
episode generation
transition generation
authoritative reason
terminated/truncated semantics
I4 audit key/reason/schema/dimension
bootstrap presence rule
HARL done row
```

It fails closed for missing, duplicate, stale, wrong-env, wrong-key, wrong-reason, wrong-done, nonterminal DTO, missing/malformed I4 sidecar, malformed audit, and malformed timeout observation. There is no fallback to returned post-reset observation.

## 8. Current versus historical lifetime

The implemented ordering is:

```text
physical transition t
  -> I4 pre-reset sidecar
  -> I4 bounded historical row copy
  -> ATOMIC_BATCH_EXACT_ACK
  -> EventTerminalLearnerRecordV2 second bounded copy
  -> six-element return infos[env][0]
  -> exact runner correlation
  -> optional timeout critic evaluation
  -> critic buffer transition fields[t]

returned current obs/share_obs
  -> ordinary state slot[t+1]
```

The dedicated ACK oracle mutates the retained runtime-artifact tensors and reuses the runtime after ACK. Learner DTO values remain unchanged. The buffer oracle independently mutates the learner DTO, source bootstrap observation, critic output tensor, and returned current share observation after insertion; buffer values remain unchanged.

## 9. TIME_LIMIT critic evaluation seam

The only critic-consumable terminal type is `EventTimeoutCriticInputBatchV2`. It can be created only from an exact correlated batch and contains only gathered I4 `TIME_LIMIT_BOOTSTRAP_CRITIC` observations.

`TerminalAuditProjectionV2` is rejected by exact type before any critic call. Returned current/post-reset `share_obs` is not an argument to the timeout evaluator.

The evaluator:

1. validates the rollout critic identity and parameter snapshot;
2. gathers only final `TIME_LIMIT` env rows in canonical env order;
3. gathers the corresponding rollout critic RNN state/placeholder before done-row zeroing;
4. uses same-episode continuation masks of one for the pre-reset terminal state;
5. calls the installed `get_values(obs, rnn, masks)` API once under `torch.inference_mode()`;
6. validates exact `[K,1]` float32/device/no-grad/finite output;
7. scatters cloned values to exact full-E env indices;
8. revalidates critic parameter identity/version and train/eval mode after forward.

The rollout critic guard is captured before rollout optimizer updates. Any parameter identity, data pointer, version, or mode change before evaluation fails before the critic call. Parameter mutation during forward fails before buffer insertion. The evaluator never changes critic mode.

## 10. True terminal and exactly-once semantics

For final reasons:

```text
ALL_TASKS_COMPLETED
NO_FEASIBLE_TASKS_REMAIN
```

the timeout gather is empty and `critic.get_values()` is never called. The implementation does not evaluate and discard a value.

For one or more TIME_LIMIT rows, one batched critic call is made. Semantic evaluation remains once per row. The collector reserves every exact terminal key before critic evaluation and keeps a bounded one-rollout consumption ledger. A repeated DTO fails before a second critic call. Any evaluation or insertion failure poisons the collector, preventing retry-driven double evaluation. The ledger may clear only after the repo-local buffer has completed `after_update()` and cleared its fixed rollout slots.

## 11. Batched gather/scatter

The mandatory synthetic oracle uses timeout env indices `[1,3]` and pre-reset critic evidence whose first values are `[10,30]`.

```text
critic input compact row 0 <- env 1
critic input compact row 1 <- env 3

full timeout value storage:
  env 0 = 0 sentinel, mask false
  env 1 = 10,         mask true
  env 2 = 0 sentinel, mask false
  env 3 = 30,         mask true
```

There is exactly one critic batch call. Compact positions never become storage env indices.

## 12. Critic-buffer fields and slot alignment

`EventOnPolicyCriticBufferEPV2` is a repo-local subclass/composition boundary around the unchanged installed EP buffer. It adds:

```text
termination_reason                [T,E,1] int64
timeout_bootstrap_value_preds     [T,E,1] float32
timeout_bootstrap_masks           [T,E,1] bool
```

The false mask is the sole authority for invalid timeout values. Invalid rows use deterministic `0.0`; reason is never inferred from value. The mask is validated as exactly `reason == TIME_LIMIT`.

`insert_event()` prevalidates all event fields, calls the installed base insertion, then commits the cloned I5a fields at the pre-insert transition slot `t`. Returned current share observation remains in the installed base buffer at `t+1`. Stock `insert()` is rejected for this event subclass so an event caller cannot silently omit I5a fields.

`bad_masks[t+1]` retains compatibility/audit encoding (`0` only for TIME_LIMIT), but is not the reason or timeout-value authority. No return computation is called in I5a; the dormant event route remains blocked until B2-I5b replaces stock proper-time-limit consumption with reviewed event GAE/ValueNorm semantics.

## 13. Mixed E=4 evidence

The mandatory mixed batch is:

```text
env0 NONE
env1 TIME_LIMIT
env2 ALL_TASKS_COMPLETED
env3 NO_FEASIBLE_TASKS_REMAIN
```

Verified result at transition slot zero:

```text
termination_reason = exact four authoritative enum values
timeout mask       = [false, true, false, false]
critic input rows  = env1 only
true-terminal calls = zero
current share_obs  = returned post-reset/current tensor at state slot one
```

The post-reset trap uses `current share_obs = -999` and pre-reset timeout evidence `= 10`. The critic receives `10`, never `-999`.

## 14. No GAE, ValueNorm, or actor-side change

B2-I5a does not implement or call:

- `compute_returns`;
- GAE/delta/return recursion;
- ValueNorm normalization or denormalization;
- actor sampling, actor evaluation, policy loss, entropy, PPO ratio, or HAPPO factor;
- any optimizer method.

Timeout values are stored in the critic's native output scale. B2-I5b is the only future slice allowed to define their return/GAE/ValueNorm consumption.

I3a/I3b, wrapper, and training source were protected by SHA-256 and not executed. In particular, the historical I3b fixture and its optimizer oracle were not rerun.

## 15. Verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Verification | Normal | `-I -B` |
|---|---:|---:|
| B2-I5a dedicated pure/static/synthetic fixture | `11/11 PASS` | `11/11 PASS` |

The eleven oracles cover:

1. I4 safe copy -> ACK -> six-return infos -> runtime mutation/reuse with no alias;
2. missing/duplicate/stale/wrong-env/wrong-reason/wrong-done/nonterminal/missing-sidecar rejection;
3. mixed E=4 TIME_LIMIT-only call and t/t+1 separation;
4. timeout `[1,3]` batched gather/scatter to `[10,30]`;
5. both true terminals zero calls and audit-to-critic type rejection;
6. duplicate consumption fails before a second forward;
7. pre-update guard, no-grad, and parameter-mutation rejection;
8. wrong shape, NaN, dtype, and device output rejection before storage;
9. DTO/bootstrap/critic-output/current-share no-alias storage;
10. NONE rows require no DTO and sanitize infos by copy;
11. no-return-math AST oracle plus actor/wrapper/training/installed hashes.

The installed Gym deprecation notice is emitted while importing the read-only installed buffer class. It does not launch a runner or environment and does not affect the results.

Two fixture-authoring runs failed before the final matrix: one test attempted to mutate a Torch inference tensor outside inference mode, and an expanded nonterminal-negative test omitted the required valid DTO for a different done row. Both were fixture-only oracle corrections; no Isaac, optimizer, or production fallback was involved.

## 16. Protected hashes

Frozen repo anchors:

```text
assignment_event_actor_collection.py
  3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45
assignment_event_happo_policy_math.py
  3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4
assignment_harl_wrapper.py
  f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae
assignment_harl_training.py
  b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd
```

Installed read-only anchors:

```text
harl/common/buffers/on_policy_critic_buffer_ep.py
  0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f
harl/algorithms/critics/v_critic.py
  ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
```

New artifacts:

```text
assignment_event_terminal_learner_transport.py
  e61644a1fde332232a0135a2f673df2e7cf6f220d1074acd6392617a69bbdfe4
assignment_event_critic_buffer.py
  7561a29598881e9b754dbcadb112baffdb835d4eff23f86b51302ccfd86068d3
test_assignment_phase_b2_i5a_historical_learner_transport_timeout_critic_buffer_pure.py
  35d5d92a654638ee09850df3fae37c8de200c2708f903f2f77180b49edcdca50
```

These new-artifact hashes describe the pre-documentation final implementation state and are rechecked in the final handoff.

## 17. Execution boundary and hygiene

```text
py_compile:                       3/3 PASS
dedicated fixture normal:         11/11 PASS
dedicated fixture -I -B:          11/11 PASS
critic:                           SYNTHETIC FORWARD ONLY / torch.inference_mode
critic parameters:                UNCHANGED on accepted forwards
actor/critic optimizer:           NOT RUN
historical I3a/I3b fixtures:      NOT RUN
Isaac/AppLauncher:                NOT RUN
environment/HARL rollout:         NOT RUN
training/playback/evaluation:     NOT RUN
checkpoint operations:            NONE
installed HARL modifications:     NONE
git diff --check:                 PASS
commit:                           NONE
```

## 18. Remaining blockers

B2-I5a completion does not establish learner readiness. Remaining unauthorized work includes:

- B2-I5b TIME_LIMIT return/GAE/ValueNorm semantics;
- B2-I6 dormant public learned-policy event composition;
- B2-V1 pure/static/synthetic interface gate;
- B2-V2 focused real Isaac + HARL interface smoke;
- B2-R final readiness review.

External path/local/retry producers and all eleven numeric TBDs remain deferred. Transformer/GNN/Set Transformer, recurrent redesign, variable cardinality, arbitrary-cardinality checkpoints, training, playback, and evaluation remain out of scope.

```text
next proposed slice: B2-I5b — TIME_LIMIT GAE and ValueNorm semantics
status: NOT AUTHORIZED
```

## 19. Final classification

```text
classification:
  PHASE-B2-I5A-HISTORICAL-LEARNER-TRANSPORT-TIMEOUT-CRITIC-AND-BUFFER-COMPLETE-AWAITING-GPT-REVIEW
B2-D through B2-I4:
  REVIEW PASS / FROZEN OR CLOSED
B2-I5a:
  IMPLEMENTED / AWAITING GPT REVIEW
tests:
  PASS
Isaac:
  NOT RUN
HARL rollout:
  NOT RUN
critic:
  SYNTHETIC FORWARD ONLY
optimizer:
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

Stop here pending GPT independent review and explicit user authorization. Do not begin B2-I5b.
