# Phase B2-V1 Pure / Static / Synthetic Integration Verification Report

Date: 2026-08-26

Classification: `PHASE-B2-V1-PURE-STATIC-SYNTHETIC-INTEGRATION-VERIFICATION-PASS-AWAITING-GPT-REVIEW`

## 1. Status and authorization boundary

```text
B2-D:                              GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:              GPT REVIEW PASS / CLOSED
B2-V1:                            VERIFICATION PASS / AWAITING GPT REVIEW
Phase B overall:                  NOT COMPLETE
reviewed primitive composition:   IMPLEMENTED / DORMANT
public learned-policy event step: DORMANT / BLOCKED
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-V1 was executed. This was a verification gate, not a new implementation slice. B2-V2, B2-R, public activation, real rollout, and training were not started.

## 2. Starting checkpoint and working-tree scope

```text
branch:  main
HEAD:    14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
```

The committed Lifecycle Runtime Backbone and the uncommitted, reviewed B2-D through I6 artifacts were preserved.

B2-V1 changed only:

- one test-support helper;
- four dedicated pure/static/synthetic verification fixtures;
- this report;
- `AgentRead/TASK_PROGRESS.md`.

Production source changes by B2-V1: **none**. No narrow integration repair was needed. Existing production modifications in the working tree belong to prior reviewed phases and were not edited by V1.

## 3. Verification fixture structure

Shared test-only composition support:

- `scripts/environments/_assignment_phase_b2_v1_event_route_helpers.py`

Independent oracle groups:

- `test_assignment_phase_b2_v1_a_static_scale_contract_gate_pure.py` — authority, public/default isolation, fixed scales, device/shape contracts, hashes;
- `test_assignment_phase_b2_v1_b_multistep_lifecycle_actor_gate_pure.py` — lifecycle transitions, DVM, conflicts, noops, actor population and slots;
- `test_assignment_phase_b2_v1_c_terminal_learner_rollover_gate_pure.py` — partial terminal/autoreset, I4→I5a→I5b, historical lifetime, ledger and rollover;
- `test_assignment_phase_b2_v1_d_failure_readiness_gate_pure.py` — pre-step rejection, post-step poison, partial commit, readiness attacks, fallback exclusion.

The helper uses the real reviewed production I1/I2/I3a, event runtime/proposal adapter, I4, I5a, I5b, and I6. Only the physical boundary, actor outputs, critic outputs, and actor/critic trainers are recorders/fakes. No fake I0–I6 semantic implementation was introduced.

## 4. I0–I6 authority matrix

| Authority | Reviewed production owner used by V1 | V1 evidence |
|---|---|---|
| schema/scale and no-tick identity | I0 `assignment_event_profile_schema_contract_v2.py` | manifest-derived fixed dimensions; no added tick |
| physical/lifecycle actor and critic evidence | I1 `assignment_event_policy_evidence.py` | one sealed current capture, CPU/no-grad, exact P2/OPEN generations |
| legality, DVM, forced routing | I2 `assignment_event_policy_decision.py` | policy/continuation/noop row transitions and fail-closed identity |
| subset actor sampling and actor storage | I3a `assignment_event_actor_collection.py` | only DVM rows sampled; fixed scatter and slot alignment |
| actor-loss population and full-grid factor | I3b `assignment_event_happo_policy_math.py` | `active & DVM`; canonical `k=t*E+e`; no compact factor authority |
| pre-reset terminal evidence | I4 `assignment_event_terminal_critic_sidecar.py` plus existing terminal transport | TIME_LIMIT bootstrap projection, true-terminal audit, copy before ACK |
| learner DTO, timeout critic, critic buffer | I5a learner transport and event critic buffer | six tuple, exact correlation, timeout-only calls, sanitized infos |
| return/GAE/ValueNorm authority | I5b `assignment_event_gae_returns.py` | TIME_LIMIT bootstrap/trace stop; true-terminal zero bootstrap/trace stop |
| call ordering and rollover | I6 `assignment_event_learned_route.py` | exact private composition, poison boundary, event returns, after-update rollover |

AST/source oracles confirm I6 imports and calls the reviewed seams. It does not duplicate lifecycle ownership, PPO/HAPPO ratio math, GAE arithmetic, critic return math, or optimizer behavior.

## 5. Public/private route and default-off audit

Production Python outside `assignment_event_learned_route.py` contains zero imports or string references to the dormant I6 module. The module has empty `__all__`; its descriptor remains:

```text
route:             private_test_only_dormant
public_activation: blocked_pending_B2_V1_V2_R
```

Attack results:

- direct event `AssignmentHarlWrapper.step()`: failed before physical execution;
- `AssignmentIsaacLabEnv` construction: failed at the profile readiness barrier before `gym.make`;
- `AssignmentOnPolicyHARunner` construction: failed before RNG/device/output/env/actor/critic initialization;
- direct `EventDormantLearnedPolicyRouteV2` construction: rejected by private capability;
- private underscored factory in a verification fixture: callable, as intended;
- event profile configuration: did not open runtime/training readiness.

Legacy, lifecycle-contract-C, lifecycle-ablation, and diagnostics wrappers retained zero event facade objects. Phase-A default-off and profile wiring regressions also passed. No CLI, registry, environment, dynamic import, profile, or manual public factory bypass was found.

## 6. Fixed-cardinality scales and tensor contracts

Two mandatory fixed scales used real production composition:

| Scale | E | M | N | T | Reset | Transition/storage | Full returns/rollover |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 4 | 3 | 4 | 3 | PASS | 3 transitions | PASS |
| B | 2 | 2 | 4 | 2 | PASS | 2 transitions | PASS |

Both scales performed reset, at least one real composed transition, actor/critic storage insertion, and six-element adaptation. Both also completed a fixed rollout in the combined V1 matrix; scale B explicitly completes it in V1-A, while scale A completes it in V1-B/C.

Verified shapes include:

```text
actor obs:            [E,M,S_actor]
share obs:            [E,M,S_critic]
available actions:    [E,M,N+1]
DVM:                  [E,M,1]
actor state slots:    [T+1,E,...]
actor action/logprob: [T,E,1]
critic state slots:   [T+1,E,...]
critic transitions:   [T,E,1]
factor:               [T,E,1]
```

Float tensors remained float32, detached/no-grad, and on CPU. Bool/int64 contracts remained exact. Wrong shape, wrong dtype, and a CPU/meta device mismatch all failed closed. CUDA was not used.

## 7. Multi-step lifecycle and continuation evidence

The scale-A rollout contains this authoritative env3/robot0 sequence:

```text
t0 NEEDS_ASSIGNMENT / POLICY_DECISION
   -> proposal task 2
   -> M1/B1 claim
   -> current P2 owner robot0 / EXECUTING

t1 FORCED_CONTINUATION task 2
   -> CONTINUE_EXISTING
   -> no proposal evidence and no repeated claim for that row
   -> physical completion
   -> task COMPLETED, ownership -1, robot NEEDS_ASSIGNMENT

t2 POLICY_DECISION
   -> proposal task 3
   -> new claim through existing M1/B1
```

P2 supplied every lifecycle/ownership assertion. Actor proposals, masks, wrapper state, and storage were never used as effective-assignment authority. Physical actions remained the existing final P2 -> Ak -> controller path in the production facade.

## 8. Conflict, policy noop, and forced noop evidence

At `t0`, env0 robots 0 and 1 both proposed task 0. Original proposal IDs and logprobs remained `(0,0)` and `(-0.10,-0.20)`. Existing deterministic cost arbitration selected robot1; P2 published robot1 as owner. On `t1`, the winner was `CONTINUE_EXISTING` with no policy proposal evidence. The loser did not gain ownership.

The same rollout also proves:

- policy noop: env1/robot0 sampled action `N` at `t0`, retained proposal presence/original logprob, stayed eligible, and was sampled again at `t1`;
- forced noop: env2/robot1 had DVM false and no proposal at `t0`; after autoreset and a new physical-feasibility input it became a policy row at `t1` and received fresh proposal evidence;
- neither noop became ownership, continuation, terminal evidence, or future proposal contamination.

## 9. Partial terminal/autoreset and repeated terminal evidence

At scale A transition zero:

```text
env0 NONE
env1 TIME_LIMIT
env2 ALL_TASKS_COMPLETED
env3 NONE
```

The next current bundle had episode generations `(0,1,1,0)` and exact post-transition generations `(3,3,3,3)`. Env0/env3 continued the same episode; env1/env2 used post-autoreset current state.

Env1 then terminated by TIME_LIMIT again at transition two. The two env1 terminal keys had different episode/transition generations and were each consumed exactly once. With the env2 true terminal, the one-rollout ledger held three unique keys. No stale collision occurred.

Every step result remained exactly six elements across nonterminal, mixed terminal, autoreset, and repeated terminal transitions.

## 10. Full I4→I5a→I5b terminal learner chain

The TIME_LIMIT trap intentionally made the pre-reset terminal critic evidence `A` and returned post-reset current critic state `B` numerically distinct.

Verified TIME_LIMIT path:

```text
I4 pre-reset bootstrap critic observation A
  -> ACK-safe learner DTO
  -> one timeout-subset recording-critic call
  -> I5a timeout value/mask at transition t
  -> I5b reward + gamma*A bootstrap
  -> trace stop
```

Verified `ALL_TASKS_COMPLETED` path:

```text
I4 terminal audit only
  -> no timeout critic row
  -> I5a timeout mask false
  -> I5b zero bootstrap
  -> reward-only terminal target
  -> trace stop
```

I5b used `A`, never `B`, for the timeout target. `B` was retained as the next actor/critic current state. Existing I5b regressions additionally covered `NO_FEASIBLE_TASKS_REMAIN`, ValueNorm ON/OFF, false-mask sentinels, and stock all-NONE parity.

## 11. Historical/current and ACK lifetime

The correlation batch returned sanitized copied infos with no private learner DTO key. The six-tuple infos retained the bounded DTO only at `infos[env][0]` for exact terminal rows.

At the `I5a_terminal_infos` observer boundary, runtime pending terminal slots were already empty. A dedicated oracle immediately rebuilt/reused the relevant runtime rows after ACK and before collector consumption; learner correlation, timeout evaluation, and critic storage still succeeded from the bounded historical DTO. Mutating a DTO getter after ACK did not mutate its stored value.

Therefore:

```text
safe historical copy complete -> runtime ACK allowed
runtime ACK != learner consumption / critic evaluation / buffer insertion
post-reset current state != terminal history reconstruction
```

## 12. Actor versus critic populations and factor indexing

One actor storage row was injected with `DVM=true, active=false` before collection. The policy proposal was still sampled and stored because DVM owns proposal eligibility. The exact `active & DVM` mask excluded that row from actor-loss normalization. All physical critic transition slots remained written.

The injected actor trainer received full `[T,E,1] = [3,4,1]` factor input. For every actor, DVM indices matched canonical flattening `k=t*E+e`; no per-agent compact factor became an authority.

Actor storage alignment was verified as:

```text
obs / available_actions / DVM / active: [0..T]
actions / original logprobs:            [0..T-1]
decision bundle ref at t:               exact receipt.decision_bundle
```

Critic reason, reward, timeout value/mask, and actor proposal/action evidence aligned to the same composed physical transition `t`.

## 13. Rollover and terminal ledger

The full scale-A rollout executed:

```text
event returns
-> fake actor trainer
-> fake critic trainer
-> critic after_update
-> terminal ledger reset
-> final-current actor/critic slot-0 rebuild
-> second rollout first transition
```

Before successful `after_update`, explicit ledger reset failed closed. A synthetic critic-trainer failure poisoned the route and retained all three keys/event slots. After successful `after_update`, old keys and event fields cleared, actor storage objects were replaced, action/logprob arrays were fresh, final current state occupied slot zero, and the next rollout's first transition inserted at slot zero without old-key reactivation.

## 14. Pre-step failure matrix

| Injection | Result | Physical calls | Actor/critic commits | Retry evidence |
|---|---|---:|---:|---|
| stale P2 | exact current validation reject | 0 | 0 | old bundle intentionally remains stale |
| stale OPEN identity | fail closed | 0 | 0 | succeeds after restoring unchanged current window |
| wrong transition generation | fail closed | 0 | 0 | succeeds after restoring unchanged generation |
| bad I2 evidence identity | fail closed | 0 | 0 | succeeds after restoring exact bundle validator |
| invalid actor output | I3a rejects out-of-range action | 0 | 0 | succeeds with valid recorder actor |
| I4-2 source mismatch | exact P2/window binding reject | 0 | 0 | succeeds after restoring exact capture |

The I4-2 case had already performed a side-effect-free actor forward. The test recorder call cursor was rewound for retry; production actor RNN/storage was never committed. No stock actor, legacy assignment, heuristic action, or physical fallback was invoked.

## 15. Post-step failure and partial-commit matrix

| Injection after irreversible physical step | Result | Continued rollout/retry |
|---|---|---|
| next I1 supplier failure | route poisoned before buffer commits | rejected |
| next I2 type/validation failure | route poisoned before buffer commits | rejected |
| terminal DTO missing/mismatch | route poisoned before learner insert | rejected |
| critic insertion failure | route and collector poisoned; reserved keys retained | rejected |
| actor insertion failure | critic committed; actor slots `(1,0,0)`; route poisoned | rejected |

The actor insertion oracle deliberately created the dangerous `critic committed / actor partial` state. I6 did not pretend to roll it back and could not continue or execute another physical step. This is the required deterministic fail-stop behavior. No duplicate terminal consumption or hidden fallback occurred.

## 16. Stock fallback and optimizer exclusions

Static/call-recorder evidence remained:

```text
stock full-row actor sampling: 0
stock HAPPO full-row train:    0
stock critic compute_returns:  0
event compute_event_returns:   selected
actor optimizer calls:         0
critic optimizer calls:        0
```

All trainers were recorders. No I3b optimizer fixture was rerun. No real actor/critic network was instantiated or executed; timeout and current values came from the recording sum critic under inference mode.

## 17. Protected source hashes

V1 protected 17 reviewed repo sources, including I0–I6, event facade, proposal adapter, lifecycle transaction/authority, wrapper, training, and environment. It separately protected repo `DirectMARLEnv`.

Key anchors include:

```text
assignment_event_profile_schema_contract_v2.py  9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955
assignment_event_policy_evidence.py             7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a
assignment_event_policy_decision.py             d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697
assignment_event_actor_collection.py            3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45
assignment_event_happo_policy_math.py            3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4
assignment_event_terminal_critic_sidecar.py      655ecafeaf6d08eb856725023572438976a381fb7ffe0a5cadf16d61a4bfe49f
assignment_event_terminal_learner_transport.py   e61644a1fde332232a0135a2f673df2e7cf6f220d1074acd6392617a69bbdfe4
assignment_event_critic_buffer.py                682e924fb2c9196818b9ef537ecda8eee46408d6828b4e380718786597adc29f
assignment_event_gae_returns.py                  7d9f154571ee43a1918d4f33f888c8b180c7c8731e8a474fdf31e32ba1923379
assignment_event_learned_route.py                b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b
assignment_harl_wrapper.py                       f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae
assignment_harl_training.py                      b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd
scan_mobile_manipulator_env.py                    f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363
source/isaaclab/.../direct_marl_env.py            7f7714a6f32e24ce34ef184cb9eed87cc36d4db0744c44a816ce3da9cc505f31
```

Installed HARL remained read only before and after V1:

```text
runners/on_policy_base_runner.py                 5d99e0fa6f70f0bbff4d5b0f00f45faa3e4b543e1531f5259900480f1842044f
runners/on_policy_ha_runner.py                   14f68bac719be40af8117284741c06e7434a18458d07cb30d5400bc32d02579a
common/buffers/on_policy_actor_buffer.py         a7352b59d8fa28b96e28e3021ddeaa9f8da5944c686651b1c04b0ec26c96f8cc
common/buffers/on_policy_critic_buffer_ep.py      0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f
algorithms/actors/happo.py                        dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96
algorithms/critics/v_critic.py                    ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3
common/valuenorm.py                               a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0
```

V1 fixture hashes:

```text
_assignment_phase_b2_v1_event_route_helpers.py                         bd6892eac031bea3b077a289f7c90b288acbd7301c754105159f466a84eacec3
test_assignment_phase_b2_v1_a_static_scale_contract_gate_pure.py      ebf22a729c5496060c4538e509c87c7d5abbb33082fff96666e10072fa8f7116
test_assignment_phase_b2_v1_b_multistep_lifecycle_actor_gate_pure.py  0b653b6c5bd8eabd985f579bf870d60277e8ce16d86efa525f97d8c2a57ab3e4
test_assignment_phase_b2_v1_c_terminal_learner_rollover_gate_pure.py  b6f5a50c5a890049a6ef65f8daec6d00880f635fa8002133d8399b1300fd5e35
test_assignment_phase_b2_v1_d_failure_readiness_gate_pure.py          3929c4ba3678387aaf3d6c38a19cd91017b37eb0873ae708db1a1352498b6082
```

## 18. Verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Verification | Normal | `-I -B` |
|---|---:|---:|
| V1-A static/scale | `6/6 PASS` | `6/6 PASS` |
| V1-B lifecycle/actor | `5/5 PASS` | `5/5 PASS` |
| V1-C terminal/learner/rollover | `6/6 PASS` | `6/6 PASS` |
| V1-D failure/readiness | `7/7 PASS` | `7/7 PASS` |
| Combined dedicated V1 | `24/24 PASS` | `24/24 PASS` |

Safe regressions:

| Regression | Normal | `-I -B` |
|---|---:|---:|
| Phase-A default-off identity | `16/16 PASS` | `16/16 PASS` |
| profile contract | `16/16 PASS` | `16/16 PASS` |
| historical event schema | `9/9 PASS` | `9/9 PASS` |
| profile production wiring | `10/10 PASS` | `10/10 PASS` |
| B2-I4 | `6/6 PASS` | `6/6 PASS` |
| B2-I5a | `11/11 PASS` | `11/11 PASS` |
| B2-I5b | `14/14 PASS` | `14/14 PASS` |
| B2-I6 | `10/10 PASS` | `10/10 PASS` |

Additional checks:

```text
py_compile (V1 helper + four fixtures): PASS
protected reviewed repo hashes:         17/17 unchanged
DirectMARLEnv hash:                     unchanged
installed HARL hashes:                  7/7 unchanged
git diff --check:                       PASS
```

The installed Gym deprecation notice is emitted during read-only HARL buffer import. It does not launch a runner or environment.

During source-path inspection, one read-only Python probe attempted to import `isaaclab.envs.direct_marl_env` and failed immediately on missing `omni.kit`; no `AppLauncher`, simulator, environment, or Isaac runtime was created. The hash was then obtained by direct static filesystem access. This authoring probe is not runtime evidence.

## 19. Execution boundary

```text
Isaac runtime:                   NOT RUN
AppLauncher:                     NOT RUN
real environment rollout:        NOT RUN
real HARL rollout:               NOT RUN
real actor network:              NOT RUN
real critic network:             NOT RUN
actor optimizer:                 NOT RUN
critic optimizer:                NOT RUN
training:                        NOT RUN
playback:                        NOT RUN
evaluation:                      NOT RUN
checkpoint operations:           NONE
CUDA:                            NOT RUN
installed HARL modifications:    NONE
production source changes by V1: NONE
commit:                          NONE
```

No performance, coverage-quality, reward-quality, convergence, or load-balancing claim is made. No numeric TBD was selected or written to production configuration.

## 20. Remaining blockers and readiness meaning

B2-V1 PASS means only:

```text
PURE_STATIC_SYNTHETIC_INTERFACE_GATE_PASS
```

It does not mean:

```text
GPT REVIEW PASS
B2-V1 CLOSED
RUNTIME_VERIFIED
POLICY_INTERFACE_READY
LEARNER_INTERFACE_READY
TRAINING_READY
```

The public learned-policy event route remains dormant and fail closed. Runtime, policy, learner, and training readiness remain blocked pending separately authorized V2 and B2-R evidence.

Deferred work remains:

- B2-V2 focused real Isaac + HARL interface smoke — not authorized;
- B2-R final readiness review — not authorized;
- public event-route activation;
- external path/local/retry producers;
- eleven numeric experimental TBDs;
- Transformer/GNN/Set Transformer, recurrent redesign, variable cardinality, and arbitrary-cardinality checkpoints;
- training, playback, evaluation, performance claims, and checkpoint work.

## 21. Final classification

```text
classification:
  PHASE-B2-V1-PURE-STATIC-SYNTHETIC-INTEGRATION-VERIFICATION-PASS-AWAITING-GPT-REVIEW

B2-D through B2-I6:
  REVIEW PASS / FROZEN OR CLOSED

B2-V1:
  VERIFICATION PASS / AWAITING GPT REVIEW

production semantic changes:
  NONE

public learned-policy event step:
  DORMANT / BLOCKED

Isaac:
  NOT RUN

HARL real rollout:
  NOT RUN

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

Stop here pending GPT independent review. Do not begin B2-V2.
