# Phase B2-I3b Decision-valid HAPPO Policy Math and Full-index Factor — Implementation Report

Date: 2026-08-25

Classification: `PHASE-B2-I3B-DECISION-VALID-HAPPO-POLICY-MATH-AND-FULL-INDEX-FACTOR-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and boundary

```text
B2-D:                              REVIEW PASS / FROZEN
B2-I0:                             REVIEW PASS / CLOSED
B2-I1:                             REVIEW PASS / CLOSED
B2-I2:                             REVIEW PASS / CLOSED
B2-I3a:                            REVIEW PASS / CLOSED
B2-I3b:                            IMPLEMENTED / AWAITING GPT REVIEW
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-I3b was implemented. B2-I4, B2-I5a, B2-I5b, B2-I6, B2-V1, B2-V2, and readiness work were not started.

## 2. Starting checkpoint

```text
branch: main
HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
B2-I3a review authority: REVIEW PASS / CLOSED, supplied by the user
```

All frozen B2-D/I0/I1/I2/I3a artifacts and pre-existing uncommitted work were preserved. No commit was created.

## 3. Changed files

Implementation:

- `assignment_event_happo_policy_math.py` — new repo-local feed-forward HAPPO specialization with decision-valid filtering and canonical full-grid sequential factor.

Verification:

- `scripts/environments/test_assignment_phase_b2_i3b_decision_valid_happo_policy_math_full_index_factor_pure.py` — new 16-oracle synthetic/installed-component fixture.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No B2-I3a/I2/I1 source, wrapper, public runner, installed actor buffer, installed HAPPO source, critic/critic buffer, GAE, terminal transport, environment, DirectMARLEnv, P2/lifecycle authority, proposal adapter, M1/B1, Ak/controller, configuration, or checkpoint was modified.

## 4. Installed HARL audit findings

The static audit confirmed:

- installed `OnPolicyHARunner.train()` allocates one full `[T,E,1]` factor, but calls pre/post `evaluate_actions()` over every flattened row and multiplies factor ratios without a DVM gate;
- installed `HAPPO.update()` evaluates the supplied entire minibatch, computes PPO ratios from its old logprobs, and divides policy loss by `active_masks_batch.sum()`;
- installed policy entropy uses the same active-mask denominator and has no safe zero-valid denominator guard;
- installed `HAPPO.train()` normalizes EP advantages against `active_masks`, has a singleton-unbiased-std NaN risk, processes planned actor minibatches, and divides logs by the planned minibatch count;
- installed feed-forward actor-buffer generation shuffles full flattened indices but carries no canonical index ledger or `decision_valid_masks`;
- installed runner pre/post factor evaluation uses `available_actions[:-1]`, actions, and active masks over the full rollout.

Therefore stock HARL cannot express forced-row mathematical absence by setting a sentinel or reusing `active_masks`. The implementation retains installed actor/distribution/optimizer intent while replacing only the population, reduction, index-ledger, and factor-scatter boundary. Installed HARL remains read-only.

## 5. Repo-local specialization architecture

The new module consumes one completed exact B2-I3a per-actor storage plus explicit feed-forward HARL placeholders and critic-provided advantages:

```text
EventPolicyActorSlotStorageV2
  obs[:-1]
  historical available_actions[:-1]
  original action_ids
  original behavior action_logprobs
  decision_valid_masks[:-1]
  active_masks[:-1]
+ feed-forward RNN/mask placeholders
+ synthetic/current critic advantages [T,E,1]
+ factor_before [T,E,1]
        |
        v
canonical k=t*E+env ledger
        |
        +-> active&DVM policy update subsets
        +-> DVM-only pre/post factor evaluation subsets
        v
ratio_full initialized to ones [T,E,1]
scatter only at canonical DVM k
factor_after = factor_before * ratio_full
```

The module provides bounded per-actor and sequential multi-actor APIs. The sequential API requires an exact agent-order permutation and feeds each actor's full `factor_after` directly into the next actor. It never reinitializes or compacts factor state.

## 6. Frozen policy populations

The implementation makes the populations explicit and separate:

```text
policy_evaluation_population = decision_valid_masks[:-1]
policy_loss_population       = active_masks[:-1] AND decision_valid_masks[:-1]
```

Only DVM rows may reach any `evaluate_actions` call. Minibatch policy evaluation is further restricted to active-and-DVM rows because only those rows contribute to loss, entropy, or gradient. Pre/post sequential-factor evaluation uses all DVM rows when that actor actually updates.

If DVM rows exist but all are inactive, the result retains their canonical evaluation identity but performs no evaluation or optimizer update. Since the actor did not change, its full ratio remains the identity without unnecessary probability calls.

`active_masks` and DVM remain separately stored and unchanged. The specialization never writes one into the other.

## 7. Original action and historical mask reevaluation

Every policy evaluation gathers:

```text
action = I3a original actor-sampled action_id at t
obs = I3a historical obs[t]
available_actions = I3a historical available_actions[t]
old_logprob = I3a original behavior logprob[t]
```

The rollout validator rejects a DVM action masked out by the historical mask and rejects a nonfinite DVM behavior logprob. It does not validate or read forced-row sentinel values as policy evidence.

No resolver winner, conflict outcome, effective assignment, final P2 owner, or controller target is accepted as an input. A same-task conflict oracle proves both original proposals remain actor-learning samples without reading which robot would later win.

## 8. PPO behavior ratio and actor loss

For each active-and-DVM minibatch:

```text
ppo_ratio = prod(exp(current_logprob(original_action)
                     - stored_behavior_logprob))

surr1 = ppo_ratio * normalized_advantage
surr2 = clip(ppo_ratio, 1-clip_param, 1+clip_param)
        * normalized_advantage

policy_loss = -sum(factor_before * min(surr1,surr2))
              / active_and_DVM_count_in_processed_minibatch
```

The actor network, installed `evaluate_actions` distribution semantics, optimizer, clip parameter, entropy coefficient, and max-gradient-norm behavior are reused. Only selected policy-loss rows are evaluated for the optimizer step, so forced rows cannot contribute numerator, denominator, ratio, entropy, loss, or gradient.

Every loss, entropy, importance weight, gradient, gradient norm, parameter, pre/post ratio, and full factor is checked for finiteness at the narrow boundary.

## 9. Entropy semantics

Entropy is computed by installed actor distribution code on active-and-DVM subsets only. The passed active mask is an all-one tensor matching that already-filtered subset, so installed entropy reduction divides by the actual actor-valid count.

There is no forced categorical distribution, zero-entropy sentinel, or full-grid entropy average. Empty filtered minibatches are skipped before `evaluate_actions`, backward, or optimizer calls.

## 10. Advantage handling

Actor advantages are projected into a separate tensor containing values only at active-and-DVM indices. Invalid/forced physical-transition advantages are not deleted from critic evidence; they are simply absent from actor math.

Normalization rules are exact:

| Population | Rule |
|---|---|
| zero actor-valid rows | skip actor update; output actor projection is zero |
| one actor-valid row | use the finite raw advantage |
| multiple, finite nonzero variance | stock-compatible unbiased std and `(adv-mean)/(std+1e-5)` |
| zero variance | use finite raw advantages |
| nonfinite mean/std/candidate from finite raw values | use finite raw advantages |
| nonfinite raw actor-valid advantage | fail closed |

An extreme finite pair that overflows variance verifies the explicit finite fallback. Nonfinite values outside the actor-loss population are ignored and projected to zero rather than contaminating actor normalization.

## 11. Empty minibatch and logging behavior

The feed-forward plan starts from a full canonical permutation of `Omega`. Every planned minibatch retains its full canonical indices, then filters to active-and-DVM indices. A filtered-empty minibatch records `processed=false` and performs:

```text
zero evaluate_actions calls
zero backward calls
zero optimizer steps
zero logging contribution
```

Policy loss, entropy, gradient norm, and PPO ratio logs divide by the number of actually processed updates. The full rollout size must partition exactly across the configured minibatch count so no canonical row can be silently dropped.

## 12. Canonical full-index HAPPO factor

The only factor identity space is:

```text
Omega = {(t,e) | 0 <= t < T, 0 <= e < E}
k = t*E + e
factor_before / ratio_full / factor_after: [T,E,1]
```

If the actor has any active-and-DVM update:

1. evaluate original actions under the pre-update actor on the row-major DVM index tuple;
2. perform policy updates using canonical minibatch ledgers;
3. evaluate the same actions/obs/historical masks under the post-update actor on the same DVM tuple;
4. compute `prod(exp(post_logprob-pre_logprob))` on that tuple;
5. initialize `ratio_full` to exact float32 ones;
6. scatter raw ratios only at those canonical indices;
7. multiply the complete prior factor by the complete ratio grid.

Forced rows get exact factor ratio `1.0` from ones initialization, not from `exp(0-0)`. Compact minibatch order never becomes a scatter coordinate.

## 13. Different-agent DVM and sequential evidence

The mandatory `T=2, E=3, M=3` oracle uses:

```text
agent 0 DVM k = [0,4]
agent 1 DVM k = [2]
agent 2 DVM k = []
```

Agent 0 can change ratio only at k 0/4. Agent 1 receives agent 0's entire factor and can change ratio only at k 2. Agent 2 receives agent 1's entire factor, performs no evaluation/optimizer mutation, and returns it bitwise unchanged. This proves equal compact ordinals across agents are never treated as shared sample identities.

A separate shuffled oracle uses DVM indices `[1,4,7]` and optimizer processing order `[7,1,4]`; final ratios scatter to k 1/4/7 rather than compact positions 0/1/2.

## 14. Zero-valid and inactive-DVM behavior

For a zero-DVM actor:

```text
evaluate_actions calls: 0
optimizer steps:         0
parameter change:        none, bitwise
optimizer state change:  none
ratio_full:              exact ones
factor_after:            bitwise equal factor_before
```

For DVM=true but active=false rows, those canonical positions remain part of DVM identity but not the loss/entropy/gradient population. If another active DVM row updates the actor, pre/post factor evaluation still covers both DVM positions. If no active-and-DVM row exists, the actor and factor are skipped unchanged.

## 15. Forced sentinel and conflict-loser evidence

The mixed fixture deliberately replaces forced-row stored logprob sentinels with NaN. I3b still passes with finite actor results because no forced old logprob is read. Forced factor positions remain exact one and the prior full factor remains unchanged there.

Two agents that both originally selected task 0 both retain canonical policy-loss index 0 and reevaluate action 0. There is no arbitration/effective-assignment input or loser filter in the module.

## 16. Stock-consistency and bounded optimizer evidence

The all-policy oracle instantiates a real installed `HAPPO` Discrete actor and a real installed `OnPolicyActorBuffer`. From identical initial actor parameters, original sampled actions/logprobs, full active/DVM population, historical masks, advantages, factor, and random seed:

- stock `HAPPO.train()` performs one reference optimizer update;
- repo-local I3b performs one event optimizer update;
- final parameters match at `atol=rtol=2e-7`;
- policy loss, distribution entropy, and PPO ratio logs match within `2e-6`.

This verifies retained stock core policy semantics when DVM filtering is an identity operation. Other fixture updates use tiny synthetic actors, one epoch, and bounded batches solely as mathematical oracles. No rollout training loop or experiment ran.

## 17. No recapture, proposal execution, critic, or public route

The new module imports only the frozen I3a storage type and profile identity. It has no P2, OPEN, environment problem, feasibility/cost, lifecycle transaction, I4-2, resolver, M1/B1, Ak/controller, environment-step, critic buffer, terminal, GAE, ValueNorm, or DirectMARLEnv input/capability.

It does not alter `assignment_harl_training.py` or open the runner. The public learned-policy event route and readiness gate remain blocked.

## 18. Verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Suite | normal | `-I -B` |
|---|---:|---:|
| B2-I3b decision-valid HAPPO/full-index factor | `16/16 PASS` | `16/16 PASS` |
| B2-I3a collector/storage/envelope | `15/15 PASS` | `15/15 PASS` |
| B2-I2 legality/DVM/decision bundle | `17/17 PASS` | `17/17 PASS` |
| B2-I1 evidence/current projectors | `14/14 PASS` | `14/14 PASS` |
| B2-I0 no-tick reconciliation | `13/13 PASS` | `13/13 PASS` |
| historical v1 schema | `9/9 PASS` | `9/9 PASS` |
| Phase-A default-off identity | `16/16 PASS` | `16/16 PASS` |
| profile contract | `16/16 PASS` | `16/16 PASS` |

The initial fixture authoring run reported `15/16`: its child-import oracle incorrectly treated I3a's already-frozen dependency graph containing a module name with `runtime` as evidence that I3b recaptured runtime state. The oracle was narrowed to the true import boundary; the separate AST oracle continues to prove the I3b source itself imports no runtime/lifecycle/proposal-execution module. Production code was unchanged. Both final modes then passed `16/16`.

Final `py_compile` for the new module and fixture is `2/2 PASS`. Final hygiene is recorded in section 20.

## 19. Protected hashes

The fixture checks ten frozen repo anchors, including I3a/I2/I1, wrapper/training, I4-2, lifecycle/P2, and environment integration. It also checks seven installed HARL anchors:

```text
runners/on_policy_ha_runner.py
  14f68bac719be40af8117284741c06e7434a18458d07cb30d5400bc32d02579a
algorithms/actors/on_policy_base.py
  ab5a1c785402efd4bd8a56b0b60503a12b365dbb422ca06ba9afee648471cd2c
algorithms/actors/happo.py
  dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96
common/buffers/on_policy_actor_buffer.py
  a7352b59d8fa28b96e28e3021ddeaa9f8da5944c686651b1c04b0ec26c96f8cc
models/policy_models/stochastic_policy.py
  e8744557a8c9ed79261702660836e7e3ff55e78de1d18e3b77cdd7cec9f52c35
models/base/act.py
  807342555af8819894750c5171cf3c0ba2b7f18e913cc51b3e0faa7991211915
models/base/distributions.py
  086b4c05eb3ad511b0728c9720d1bec70354a967d62a01fe854b3ca4503576cf
```

New artifact hashes:

```text
assignment_event_happo_policy_math.py
  3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4
test_assignment_phase_b2_i3b_decision_valid_happo_policy_math_full_index_factor_pure.py
  3dfca9f25444b63c72b784590a36fd7517934adea17807dca4b60bc4e187f061
```

## 20. Hygiene and non-execution statement

```text
py_compile:                   2/2 PASS
git diff --check:             PASS
untracked whitespace scan:   PASS
temporary bytecode cleanup:  COMPLETE
unexpected checkpoint/log:   NONE
installed HARL hashes:       UNCHANGED
```

No Isaac, AppLauncher, environment rollout, training campaign, playback, evaluation, critic/GAE execution, public learned-policy step, or checkpoint save/load was run. HARL use was limited to synthetic component evaluation and the bounded stock/event optimizer comparison described above.

## 21. Remaining blockers and readiness

B2-I3b completion still does not establish `POLICY_INTERFACE_READY`. Remaining unauthorized blockers include:

- B2-I4 authoritative pre-reset terminal audit and TIME_LIMIT bootstrap critic sidecar;
- B2-I5a historical learner/value/buffer transport;
- B2-I5b TIME_LIMIT GAE/ValueNorm semantics;
- B2-I6 dormant public learned-policy event route;
- B2-V1/V2 interface verification and final readiness review.

External path/local/retry producers and all eleven numeric TBDs remain deferred. Transformer/GNN/Set Transformer, recurrent redesign, variable cardinality, arbitrary-cardinality checkpoints, training, playback, and evaluation remain out of scope.

```text
next proposed slice: B2-I4 — authoritative pre-reset terminal critic sidecar
status: NOT AUTHORIZED
```

## 22. Final classification

```text
classification:
  PHASE-B2-I3B-DECISION-VALID-HAPPO-POLICY-MATH-AND-FULL-INDEX-FACTOR-COMPLETE-AWAITING-GPT-REVIEW
B2-D:
  REVIEW PASS / FROZEN
B2-I0:
  REVIEW PASS / CLOSED
B2-I1:
  REVIEW PASS / CLOSED
B2-I2:
  REVIEW PASS / CLOSED
B2-I3a:
  REVIEW PASS / CLOSED
B2-I3b:
  IMPLEMENTED / AWAITING GPT REVIEW
tests:
  PASS
Isaac:
  NOT RUN
HARL:
  SYNTHETIC COMPONENT / BOUNDED OPTIMIZER ORACLE ONLY
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

Stop here pending GPT independent review and explicit user authorization. Do not begin B2-I4.
