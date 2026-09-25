# Phase B2-I6 Dormant Learned-policy Event Route Composition — Implementation Report

Date: 2026-08-26  
Starting committed HEAD: `14993dee344bade0230d2eb97b5f22171331f44a`

## Classification

`PHASE-B2-I6-DORMANT-LEARNED-POLICY-EVENT-ROUTE-COMPOSITION-COMPLETE-AWAITING-GPT-REVIEW`

```text
B2-D:                         GPT REVIEW PASS / FROZEN
B2-I0 through B2-I5b:         GPT REVIEW PASS / CLOSED
B2-I6:                        IMPLEMENTED / AWAITING GPT REVIEW
reviewed primitive composition: IMPLEMENTED
public activation:            BLOCKED
runtime readiness:            BLOCKED
policy readiness:             BLOCKED
learner readiness:            BLOCKED
Phase B overall:              NOT COMPLETE
Isaac / AppLauncher:          NOT RUN
HARL environment rollout:     NOT RUN
actor or critic optimizer:    NOT RUN
training/playback/evaluation: NOT RUN
checkpoint operation:         NOT RUN
commit:                       NONE
```

No B2-V1, B2-V2, or B2-R work was started.

## Authoritative basis and source audit

The frozen B2-D and reviewed I3a/I3b/I4/I5a/I5b reports were used as the implementation authority. The following current sources were audited before composition:

- `assignment_harl_wrapper.py`: public event `step()` remains fail-closed; private admitted reset, I4-2 decision capture, proposal decode, proposal/effective step, and six-slot legacy behavior.
- `assignment_harl_training.py`: public runner construction still crosses `require_assignment_profile_runtime_ready`; stock warmup/collect/insert remains unsuitable for forced-row/DVM semantics and was not selected.
- `assignment_event_runtime_facade.py`: exact P2/window proposal capture, pure resolution, zero-or-one B1 batch, final P2/Ak physical step, terminal historical copy, ACK, and returned current P2.
- `assignment_event_proposal_adapter.py`: fixed `[E,M]` routing input, raw `N -> -1` decode, continuation interpretation, deterministic conflict resolution, and proposal-source validation.
- reviewed I1–I5b implementation sources named by the authorization.
- installed HARL `on_policy_base_runner.py`, `on_policy_ha_runner.py`, and `on_policy_critic_buffer_ep.py`, read only.

Installed runner facts retained by I6:

- stock collection samples every agent row and therefore is not used for the event route;
- stock EP insertion stores current value at transition slot `t` and returned current share state at `t+1`;
- stock EP active masks return to one on synchronized autoreset, while recurrent masks become zero;
- stock `OnPolicyHARunner.train()` derives ValueNorm advantages as `returns[:-1] - value_normalizer.denormalize(value_preds[:-1])`, otherwise `returns[:-1] - value_preds[:-1]`;
- stock actor order is sequential HAPPO before critic training;
- stock `compute()` invokes installed `compute_returns()` and is therefore excluded from the event route;
- installed `after_update()` rolls final critic state to slot zero.

## Changed files

Implementation:

- `assignment_event_learned_route.py` — new private/dormant B2-I6 composition module.

Verification:

- `scripts/environments/test_assignment_phase_b2_i6_dormant_learned_event_route_composition_pure.py` — new pure/synthetic composition fixture.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No wrapper, runner/training, environment, lifecycle, proposal-adapter, I1–I5b semantic source, DirectMARLEnv, package export, or installed HARL file was changed by B2-I6.

## Composition architecture and dormant gate

`EventDormantLearnedPolicyRouteV2` is constructed only through the underscored repo-local factory `_compose_dormant_event_learned_policy_route_v2`. The module has an empty `__all__`, is not imported by `assignment_harl_wrapper.py` or `assignment_harl_training.py`, and is not registered in any public runner or environment path.

The normal event profile therefore still fails at the existing readiness barrier/public wrapper `step()`. There is no CLI flag, environment variable, readiness override, temporary bypass, or silent stock fallback.

The route owns only:

- call ordering;
- exact binding validation;
- fixed rollout actor RNN/mask slots;
- transport into reviewed actor and critic storage;
- event-return/trainer selection;
- fail-closed poisoning after an irreversible physical step;
- post-update rollover.

It owns no lifecycle, ownership, legality, arbitration, terminal, critic projection, GAE, PPO, or HAPPO algorithm.

## Exact reset and rollout-step order

Reset performs:

```text
admitted private wrapper reset
  -> current I1 capture
  -> current I2 seal
  -> one I3a actor storage per fixed actor at slot 0
  -> I5a critic buffer current share_obs at slot 0
  -> actor/critic recurrent masks and states at slot 0
  -> rollout critic guard
```

No actor is sampled during reset. Actor slot zero and critic slot zero are derived from the same exact current I1/I2 object.

Each transition performs:

```text
validate exact current I1/P2/OPEN binding
  -> capture EventLearnerTransitionExpectationV2
  -> ordinary current critic V(t)
  -> I3a DVM-subset actor collection
  -> capture actual I4-2 decision
  -> validate actual I4-2 decision against the exact I1/I2 binding
  -> existing I4-2 resolve / zero-or-one M1-B1 / final P2-Ak / physical step
  -> returned current P2 and safe historical terminal DTOs after runtime ACK
  -> next current I1/I2 exactly once
  -> validate next I1/I2 against facade returned current P2
  -> construct the existing six-element HARL result
  -> I5a attach helper writes learner DTO only to `infos[env][0]`
  -> I5a terminal correlation and timeout critic evaluation
  -> I5a event critic-buffer insertion at transition t/current state t+1
  -> deterministic I3a actor-slot insertion at action t/current bundle t+1
```

The six returned slots remain `(obs, share_obs, rewards, dones, infos, available_actions)`. Returned `obs`, `share_obs`, and `available_actions` come from next current I1/I2, including the post-autoreset current episode for done environments.

## I1 -> I2 -> I3a -> I4-2 binding

The route retains one exact current `EventPolicyDecisionBundle`; it never recaptures an equivalent bundle for actor collection. I3a receives that exact object and its proposal envelope retains it by identity.

After I3a collection, the existing I4-2 capture is called with:

- feasibility: exact I1 `explicit_physical_feasibility`;
- cost: exact I1 `geometric_pair_ranking_cost`;
- available task mask: I2 legal task mask restricted to policy rows.

The restriction is important: I2's fixed action mask also contains the current owned task for a forced-continuation row, but I4-2 `available_mask` means legal new-claim pairs and must imply physical feasibility. Forced routing is therefore kept in the full action tensor but excluded from new-claim availability.

The actual I4-2 decision is rejected unless P2 publication identity, OPEN window identity, episode generations, transition generations, physical feasibility, cost, and legal policy-task mask all exactly match the bound I1/I2 evidence. No decision tick or rebinding was introduced.

## Policy proposals, forced routing, and effective assignment

I3a remains the only actor sampling seam. It calls each distinct actor only for its DVM-true subset and returns fixed `[E,M,1]` actions/logprobs plus the exact policy-proposal presence mask.

The route deliberately keeps two simultaneous facts:

```text
full fixed routing tensor:
  required by the reviewed I4-2 adapter to validate every robot row

policy_proposal_present_mask:
  sole indicator that an action/logprob is an actor proposal
```

- Policy noop: raw `N`, decoded `-1`, DVM true, proposal present true, original actor logprob retained.
- Forced noop: raw `N`, decoded `-1`, DVM false, proposal present false, forced logprob sentinel only.
- Forced continuation: raw current owned task, DVM false, proposal present false; I4-2 must interpret it as `CONTINUE_EXISTING`.

The full routing tensor is necessary for I4-2 fixed-row consistency, but the route rejects any candidate/selected/conflict status on a proposal-absent forced row. Consequently only policy-present rows can populate new-claim arbitration; forced continuation/noop cannot create an M1 request.

Existing cost arbitration and B1 are reused unchanged. The E=4 oracle samples two robots proposing the same task, chooses the lower-cost robot as the effective winner, and proves that both original proposal IDs and behavior logprobs remain in actor storage. The admitted effective assignment is never copied over actor evidence.

The next all-continuation/noop step produces no B1 artifact and zero claims. Physical control remains final current P2 -> Ak -> controller through the reviewed synchronous runtime.

## Terminal/current transport and timeout critic

I6 does not access a runtime terminal slot. The facade first completes I4 safe copy and runtime exact ACK; only its bounded historical payload is passed to I5a. I5a creates a second learner-owned immutable record in `infos`, correlates it with the pre-step expectation, and evaluates all and only TIME_LIMIT bootstrap observations.

The mandatory E=4 mixed step contains:

- env 0 and env 3: nonterminal;
- env 1: TIME_LIMIT, truncated, pre-reset timeout critic value;
- env 2: ALL_TASKS_COMPLETED, terminated, no critic bootstrap.

The timeout rows are gathered into exactly one critic call, scattered into the full-E I5a fields, and inserted at transition slot `t`. Returned/post-autoreset current share state is stored at `t+1`; it is never used to reconstruct terminal history or TIME_LIMIT bootstrap input.

## Event returns, advantages, and trainers

At rollout completion, the route uses this exact order:

```text
all actor/critic transition slots complete
  -> all TIME_LIMIT values already sealed by I5a
  -> ordinary final current next-value prediction
  -> EventOnPolicyCriticBufferEPV2.compute_event_returns()
  -> stock-compatible advantage derivation
  -> injected I3b sequence actor trainer
  -> injected critic trainer
  -> critic buffer after_update()
  -> terminal consumption ledger reset
  -> actor storage/RNN/mask slot-zero rebuild
  -> new rollout critic guard
```

The event route never calls installed/stock critic-buffer `compute_returns()`. The actor trainer default is the reviewed `train_event_policy_happo_sequence_v2`; the verification injects a call recorder so no optimizer executes. It receives one full `[T,E,1]` factor and the fixed actor order. No stock `OnPolicyHARunner.train()` path is called.

Advantages are computed before either trainer can mutate a model:

```text
ValueNorm OFF:
  returns[:-1] - value_preds[:-1]

ValueNorm ON:
  returns[:-1] - value_normalizer.denormalize(value_preds[:-1])
```

This is the audited installed-HARL EP derivation. I5b remains the owner of event return/GAE and ValueNorm arithmetic; I6 adds no loss, ratio, entropy, factor, bootstrap, trace, or normalization algorithm.

The critic trainer is an injected repo-local seam. Verification uses a recorder returning `optimizer_calls=0`; no real critic trainer or optimizer was run.

## Rollover and failure atomicity

Installed critic-buffer insertion wraps its step counter to zero at the end of a full rollout. Completion is therefore validated from all event slots written plus every I3a actor storage reaching `next_action_slot == T`, not from the wrapped counter alone.

After successful actor and critic trainer calls:

- critic `after_update()` preserves its final current state at slot zero and clears reason/mask/value/event-return fields;
- only then may the I5a terminal consumption ledger clear;
- the completed I3a actor storages remain immutable rollout evidence for the returned result;
- one replacement storage per actor is created from the exact final current I2 at new slot zero;
- final actor RNN state and recurrent mask are rolled to slot zero;
- previous-rollout DTO keys do not survive.

Before physical execution, current binding, expectation, actor/critic outputs, and I4-2 source binding are validated without inserting either storage. After physical execution, next current, six-tuple, DTO, and all actor storage inputs are prevalidated before deterministic commits. A pre-step failure leaves both actor and critic slots unchanged and permits no rebinding. Any failure after the physical step poisons the route, preventing retry, duplicate learner consumption, or continued collection from a partially advanced environment. The fixture proves a post-step next-capture failure leaves actor/critic slots at zero and all later calls fail closed as poisoned.

## Default-off and public readiness

- `assignment_harl_wrapper.py` and `assignment_harl_training.py` do not import the I6 module.
- Existing/default profiles make zero I0–I6 composition calls.
- Public event `AssignmentHarlWrapper.step()` still raises the existing not-runtime-ready error before the physical environment step.
- The public training runner still fails at its existing readiness barrier.
- No stock fallback exists if the private event route cannot complete.
- The composition descriptor states `blocked_pending_B2_V1_V2_R`.

Thus B2-I6 establishes only a dormant reviewed-primitives composition. It does not establish runtime, policy, learner, or training readiness.

## Verification

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

Results:

- B2-I6 dedicated composition fixture: `10/10 PASS` normal and `10/10 PASS` under `-I -B`.
- B2-I4 regression: `6/6 PASS` normal and `6/6 PASS` under `-I -B`.
- B2-I5a regression: `11/11 PASS` normal and `11/11 PASS` under `-I -B`.
- B2-I5b regression: `14/14 PASS` normal and `14/14 PASS` under `-I -B`.
- Phase-A default-off identity: `16/16 PASS`.
- assignment profile contract: `16/16 PASS`.
- protected I1/I2/I3a/I3b/I4/I5a/I5b, wrapper, training, facade, and proposal-adapter hashes: `12/12 unchanged`.
- installed HARL runner/base runner/EP critic buffer hashes: `3/3 unchanged`.
- static forbidden stock paths and no duplicated optimizer/math oracle: PASS.
- `py_compile`: PASS.
- `git diff --check`: PASS.

Dedicated fixture scope includes reset slot zero; mixed policy/continuation/noop; policy noop versus forced noop; same-task conflict; proposal/effective separation; normal/TIME_LIMIT/true-terminal mixed E; autoreset current `t+1`; timeout critic exactly once; actor and critic `t/t+1`; explicit event returns; recorder I3b and critic trainers; full-index factor; stock-path exclusion; no-alias; rollover; stale binding; pre-step no-partial insertion; post-step poison; default-off isolation; and public fail-closed behavior.

No I3b optimizer fixture was rerun. The I6 actor and critic trainers were recorders only. The ordinary and timeout critic calls used a synthetic no-grad recording critic, not a real/installed critic network.

## Protected hashes

```text
assignment_event_learned_route.py
  b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b

test_assignment_phase_b2_i6_dormant_learned_event_route_composition_pure.py
  ba8820a6c8268531101c00e6ec9992510e6c4db2cd1bde6f2ff1f0d7fe4a2102
```

Protected reviewed/installed hashes are encoded and checked by the dedicated fixture.

## Remaining blockers and stop boundary

Successful B2-I6 composition does not authorize or prove:

- B2-V1 pure/static/synthetic integration verification;
- B2-V2 focused real Isaac + HARL interface smoke;
- B2-R final readiness review;
- public learned-policy event stepping;
- real HARL runner rollout;
- optimizer or training readiness;
- training, playback, evaluation, or checkpoints.

External path/local/retry producers and the eleven numeric TBDs remain separate experimental dependencies. Transformer/GNN/Set Transformer, variable cardinality, recurrent redesign, and arbitrary-cardinality checkpoints remain deferred.

## No forbidden execution statement

B2-I6 performed no Isaac/AppLauncher launch, real environment rollout, real HARL rollout, actor optimizer, critic optimizer, training, playback, evaluation, or checkpoint operation. Installed HARL was read only. No commit was created.

Stop here and wait for GPT independent review. Proposed next slice `B2-V1` is **NOT AUTHORIZED**.
