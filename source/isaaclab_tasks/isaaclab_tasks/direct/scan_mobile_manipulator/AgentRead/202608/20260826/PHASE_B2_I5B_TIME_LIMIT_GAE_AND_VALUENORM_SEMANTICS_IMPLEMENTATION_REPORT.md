# Phase B2-I5b TIME_LIMIT GAE and ValueNorm Semantics — Implementation Report

Date: 2026-08-26

Classification: `PHASE-B2-I5B-TIME-LIMIT-GAE-AND-VALUENORM-SEMANTICS-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and authorization boundary

```text
B2-D:                              REVIEW PASS / FROZEN
B2-I0:                             REVIEW PASS / CLOSED
B2-I1:                             REVIEW PASS / CLOSED
B2-I2:                             REVIEW PASS / CLOSED
B2-I3a:                            REVIEW PASS / CLOSED
B2-I3b:                            REVIEW PASS / CLOSED
B2-I4:                             REVIEW PASS / CLOSED
B2-I5a:                            REVIEW PASS / CLOSED
B2-I5b:                            IMPLEMENTED / AWAITING GPT REVIEW
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-I5b was implemented. B2-I6, B2-V1, B2-V2, B2-R, public route activation, and training were not started.

## 2. Starting checkpoint and frozen architecture

```text
branch:  main
HEAD:    14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
B2-I5a review authority: REVIEW PASS / CLOSED, supplied by the user
```

The committed Lifecycle Runtime Backbone and uncommitted reviewed B2-D through I5a artifacts were preserved. No commit was created.

The implementation does not touch P2, proposal/effective assignment, M1/B1, Ak/controller, EXECUTING continuation, terminal capture, historical/current separation, runtime ACK, wrapper/public runner, or default profiles. Fixed M/N feed-forward EP/HAPPO remains the architecture.

## 3. Changed files

Implementation:

- `assignment_event_gae_returns.py` — new repo-local fixed-EP event GAE arithmetic with authoritative reason routing, separate bootstrap/trace masks, same-current-ValueNorm denormalization, validation, and immutable audit result.
- `assignment_event_critic_buffer.py` — narrow extension adding explicit once-per-rollout `compute_event_returns()` and atomic commit into the existing I5a event buffer.

Verification:

- `scripts/environments/test_assignment_phase_b2_i5b_time_limit_gae_valuenorm_semantics_pure.py` — new 14-oracle pure/static/numerical fixture.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

Installed HARL, runner, critic, ValueNorm, actor math, wrapper, training entrypoint, I4 terminal producer/transport, and I5a learner transport were not modified.

## 4. Installed HARL return / GAE / ValueNorm audit

Read-only sources audited:

- `harl/common/buffers/on_policy_critic_buffer_ep.py`
- `harl/common/valuenorm.py`
- `harl/algorithms/critics/v_critic.py`
- `harl/runners/on_policy_base_runner.py`
- `harl/runners/on_policy_ha_runner.py`

Installed EP buffer storage is:

```text
value_preds: [T+1,E,1] critic-native output scale
returns:     [T+1,E,1] unnormalized critic targets
rewards:     [T,E,1]
masks:       [T+1,E,1]
bad_masks:   [T+1,E,1]
```

The installed configured proper-time-limit GAE computes normalized/native critic values through `ValueNorm.denormalize()` before arithmetic, but then multiplies the completed GAE by `bad_masks[t+1]`. Thus `bad_masks==0` replaces a truncation target with `V(s_t)` and deletes the physical reward/timeout delta. With `bad_masks==1` and `masks==0`, it gives reward-only zero bootstrap. Neither expresses the required TIME_LIMIT target.

Installed `ValueNorm` exposes `running_mean_var()`, `normalize()`, `denormalize()`, and `update()`. `VCritic.cal_value_loss()` updates the normalizer from unnormalized `return_batch` during critic training, then normalizes return targets for loss. Therefore I5b stores unnormalized returns and does not update normalizer statistics.

## 5. Authoritative reason, bootstrap, and trace contract

`termination_reason[t]` and the exact I5a timeout mask/value fields are the event authority. `masks[t+1]` retains only EP liveness for `NONE`; `bad_masks` is not read by I5b.

| Reason | Bootstrap source | Bootstrap | Trace |
|---|---|---:|---:|
| `NONE` | current `V(s_{t+1})`, gated by normal EP liveness | yes | continue while live |
| `ALL_TASKS_COMPLETED` | zero | no | stop |
| `NO_FEASIBLE_TASKS_REMAIN` | zero | no | stop |
| `TIME_LIMIT` | I5a `timeout_bootstrap_value_preds[t]` | yes | stop |

The final arithmetic is:

```text
delta_t = reward_t + gamma * bootstrap_value_t - V_t

gae_t = delta_t
        + gamma * gae_lambda * trace_continue_t * gae_{t+1}

return_t = gae_t + V_t
```

Rows are routed independently in `[T,E,1]`; no batch-global done branch exists. Both authoritative terminal kinds must have stopped EP boundary masks. `NONE` combines reason routing with the existing liveness mask, preserving stock behavior when event terminal fields are inactive.

## 6. Transition t versus state t+1 and autoreset trap

The event buffer keeps I5a reason/timeout evidence at transition slot `t`; ordinary HARL `value_preds[t+1]` may be the autoreset episode state after a done transition.

I5b behavior is exact:

```text
NONE:          may use value_preds[t+1]
TRUE TERMINAL: ignores value_preds[t+1], bootstrap zero
TIME_LIMIT:    ignores value_preds[t+1], uses timeout value[t]
```

The fixture uses `V_timeout=10`, post-reset `V(t+1)=999`, and a large next-episode advantage. TIME_LIMIT uses 10 and receives no trace contribution. True terminal uses neither 10 nor 999. Only `NONE` uses 999 and continues the trace. New-episode reward/value/advantage therefore cannot leak backward across either event terminal boundary.

## 7. ValueNorm-consistent arithmetic

I5a timeout values and ordinary `value_preds` remain in critic-native output scale. For ValueNorm ON, I5b:

1. validates the canonical installed `ValueNorm` API and device;
2. snapshots its full state and train/eval mode;
3. concatenates all native rollout values and only mask-selected timeout values;
4. performs one `denormalize()` call under inference mode;
5. verifies the normalizer snapshot is unchanged;
6. performs all delta, GAE, and return arithmetic in the resulting unnormalized scale.

No historical/second normalizer is stored or created. No timeout value is normalized during I4/I5a capture. No normalized-space delta is computed. I5b never calls `ValueNorm.update()`.

The nonidentity oracle sets:

```text
denormalize(x) = 2*x + 10
```

and proves `V_t`, `V_next`, and `V_timeout` all use that same transformation. A normalizer that mutates its state during the pass fails before buffer returns are committed. ValueNorm OFF uses critic-native values directly.

## 8. Reason/mask/value validation

Before arithmetic, I5b validates:

- exact `[T,E,1]` shapes, dtype, device, and no-grad contracts;
- known authoritative termination enum values;
- exact equivalence `TIME_LIMIT <=> timeout_bootstrap_mask`;
- false timeout mask for `NONE` and both true terminals;
- finite timeout value only at true timeout-mask positions;
- binary EP liveness masks and stopped terminal boundary masks;
- finite rewards/current values/required next value;
- finite gamma/lambda in `[0,1]`;
- complete I5a event slots before buffer computation.

Unknown reason, mask/reason mismatch, timeout NaN/inf/wrong shape, nonbinary liveness, or terminal mask contradiction fails closed before return commit. There is no fallback to post-reset `V(t+1)` or zero timeout bootstrap.

False-mask timeout slots are not denormalized or used. A fixture replaces them with NaN, a huge positive value, and a huge negative value; returns remain bitwise equal to the zero-sentinel baseline. Mask, never sentinel value, is the authority.

## 9. Buffer API, lifetime, and exactly-once behavior

The private event buffer now exposes:

```text
compute_event_returns(next_value, value_normalizer=None)
```

It requires `use_gae=True`, a fully written fixed rollout, and no prior successful event return computation. The pure function computes and validates detached results first; only success commits `value_preds[-1]` and `returns[:-1]`. A failed computation leaves returns and the once guard unchanged. The returned audit DTO does not alias buffer storage. `after_update()` clears the I5a fields and the I5b once guard.

The installed `compute_returns()` implementation is neither modified nor overridden. The dormant event route must explicitly call `compute_event_returns()` in a separately authorized B2-I6 composition. This keeps I5b private and prevents a runner/public-route change in this slice.

## 10. Rewards, critic target scale, and actor/DVM separation

Physical `rewards[t]` are used unchanged for every row. TIME_LIMIT neither zeros reward nor replaces it with a value.

`returns[:-1]` are unnormalized critic training targets, matching installed `VCritic.cal_value_loss()` behavior. Normalizer statistics remain owned by the existing future critic training path.

The I5b module has no `decision_valid_masks`, actor row kinds, proposal masks, action/logprob, HAPPO factor, actor module, or active-mask input. Forced-continuation and forced-noop rows remain physical critic transitions. A dedicated oracle uses DVM=false external labels for two `NONE` rows and proves both rewards remain in critic returns.

## 11. No critic forward, terminal DTO, or runtime access

I5b consumes only critic-buffer tensors and one optional current ValueNorm. It does not import or access:

- terminal learner DTOs or I4 runtime artifacts;
- wrapper infos or facade state;
- actor policy/DVM/proposal math;
- critic network or `get_values()`;
- any optimizer or training method.

TIME_LIMIT critic evaluation remains exactly the reviewed I5a operation. I5b never reevaluates the terminal critic.

## 12. Numerical and compatibility evidence

The dedicated fixture includes:

1. hand-computed `T=3,E=4` mixed reason delta/GAE/returns;
2. TIME_LIMIT/true-terminal trace-stop and post-autoreset `999` trap;
3. all reason/timeout-mask mismatches plus unknown enum rejection;
4. timeout NaN, inf, and wrong shape rejection;
5. false-mask NaN/huge sentinel exclusion;
6. nonidentity ValueNorm same-scale arithmetic and zero stats updates;
7. ValueNorm OFF native-scale arithmetic;
8. same-normalizer mutation failure before commit;
9. stock installed EP all-`NONE` parity with ValueNorm OFF and ON;
10. deliberate TIME_LIMIT difference from stock bad-mask suppression;
11. full-rollout/once/no-alias buffer behavior;
12. liveness-mask failure contracts;
13. DVM exclusion plus forced-row critic-transition preservation;
14. static scope and protected-hash preservation.

The all-`NONE` stock comparison uses identical rewards, masks, native values, gamma/lambda, and equal ValueNorm state. Returns match at tight tolerance with ValueNorm OFF and ON. This proves I5b preserves stock EP GAE when event features are inactive.

The TIME_LIMIT specialization intentionally differs:

```text
stock bad-mask target:  V(s_t) = 1
event TIME_LIMIT target: reward + gamma*V_timeout = 2 + 0.9*10 = 11
```

This is the frozen event semantics, not a regression.

## 13. Verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Verification | Normal | `-I -B` |
|---|---:|---:|
| B2-I5b dedicated event return fixture | `14/14 PASS` | `14/14 PASS` |
| B2-I5a learner transport/buffer regression | `11/11 PASS` | `11/11 PASS` |
| B2-I4 pre-reset terminal sidecar regression | `6/6 PASS` | `6/6 PASS` |

Additional checks:

```text
py_compile (I5b module, extended buffer, fixture): 3/3 PASS
I0/I1/I2 protected source hashes:                  UNCHANGED
actor/HAPPO/wrapper/training protected hashes:      UNCHANGED
installed buffer/ValueNorm/critic hashes:           UNCHANGED
git diff --check:                                   PASS
```

The installed Gym deprecation notice appears during read-only buffer import. It launches no environment or runner and does not affect the fixture.

## 14. Protected hashes

Frozen repo anchors include:

```text
assignment_event_profile_schema_contract_v2.py
  9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955
assignment_event_policy_evidence.py
  7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a
assignment_event_policy_decision.py
  d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697
assignment_event_actor_collection.py
  3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45
assignment_event_happo_policy_math.py
  3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4
assignment_event_terminal_learner_transport.py
  e61644a1fde332232a0135a2f673df2e7cf6f220d1074acd6392617a69bbdfe4
assignment_harl_wrapper.py
  f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae
assignment_harl_training.py
  b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd
```

Installed read-only anchors:

```text
harl/common/buffers/on_policy_critic_buffer_ep.py
  0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f
harl/common/valuenorm.py
  a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0
harl/algorithms/critics/v_critic.py
  ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
```

New/final I5b artifacts before documentation-only finalization:

```text
assignment_event_gae_returns.py
  7d9f154571ee43a1918d4f33f888c8b180c7c8731e8a474fdf31e32ba1923379
assignment_event_critic_buffer.py
  682e924fb2c9196818b9ef537ecda8eee46408d6828b4e380718786597adc29f
test_assignment_phase_b2_i5b_time_limit_gae_valuenorm_semantics_pure.py
  01108be4a7305f3052c58def032b0e464981a6e113e7d6c9d282ca191366f5af
```

## 15. Execution boundary and hygiene

```text
Isaac/AppLauncher:            NOT RUN
environment/HARL rollout:    NOT RUN
actor inference:             NOT RUN
critic forward (I5b/real):   NOT RUN
I5a regression recorder:     SYNTHETIC EXISTING FIXTURE ONLY
actor/critic optimizer:      NOT RUN
training/playback/evaluation: NOT RUN
checkpoint operations:       NONE
installed HARL modifications: NONE
commit:                      NONE
```

HARL use was limited to pure synthetic `OnPolicyCriticBufferEP.compute_returns()` comparison and read-only `ValueNorm.denormalize()` arithmetic. I5b made zero `get_values()` calls and no real/network critic component was invoked. The required I5a regression replayed only its existing synthetic `RecordingCritic.get_values()` oracle.

## 16. Remaining blockers and next slice

B2-I5b completion does not establish learner, policy, runtime, or training readiness. Remaining unauthorized work is:

- B2-I6 dormant public learned-policy event composition;
- B2-V1 pure/static/synthetic interface gate;
- B2-V2 focused real Isaac + HARL interface smoke;
- B2-R final readiness review.

External path/local/retry producers and all eleven numeric TBDs remain deferred. Transformer/GNN/Set Transformer, recurrent redesign, variable cardinality, arbitrary-cardinality checkpoints, training, playback, evaluation, and checkpoint work remain out of scope.

```text
next proposed slice: B2-I6 — dormant public learned-policy event route
status: NOT AUTHORIZED
```

## 17. Final classification

```text
classification:
  PHASE-B2-I5B-TIME-LIMIT-GAE-AND-VALUENORM-SEMANTICS-COMPLETE-AWAITING-GPT-REVIEW
B2-D through B2-I5a:
  REVIEW PASS / FROZEN OR CLOSED
B2-I5b:
  IMPLEMENTED / AWAITING GPT REVIEW
tests:
  PASS
Isaac:
  NOT RUN
HARL rollout:
  NOT RUN
critic forward (I5b/real HARL):
  NOT RUN
I5a regression recorder:
  SYNTHETIC EXISTING FIXTURE ONLY
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

Stop here pending GPT independent review and explicit user authorization. Do not begin B2-I6.
