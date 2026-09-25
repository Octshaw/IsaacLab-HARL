# Phase B2-R0 Training-Update Readiness Architecture Design

Date: 2026-09-01 (Asia/Shanghai)

Status: DESIGN ONLY / SOURCE AUDIT COMPLETE / TARGETED REVISION COMPLETE / IMPLEMENTATION NOT AUTHORIZED

Prior GPT review result: CONDITIONAL PASS

Targeted revision status: COMPLETE / AWAITING GPT RE-REVIEW

Current classification:

```text
PHASE-B2-R0-TRAINING-UPDATE-READINESS-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW
```

This authoritative report received a GPT conditional pass and was revised only
to parameterize resolved configuration/counts, make the four learner
termination categories and their precedence explicit, and decouple the
checkpoint branch from training-update readiness closure. The source audit was
not restarted and the accepted architecture was not redesigned. This report is
not an extension of R5, does not reopen closed B2-V2 evidence, and does not
authorize B2-R1. Neither the original pass nor this targeted revision made a
production, HARL, harness, checkpoint, or runtime change. They ran no Python,
Isaac, trainer update, backward pass, optimizer step, training, playback, or
evaluation, and created no commit.

## 1. Starting committed authority / latest HEAD

The read-only authority check established:

```text
branch:
  main

upstream:
  origin/main

HEAD:
  b71d85a32f51be6ada324f870813a56bb45dd396

HEAD parent:
  14993dee344bade0230d2eb97b5f22171331f44a

HEAD authored date:
  2026-08-31T23:35:18+08:00

HEAD subject:
  feat(mrta): close B2 event policy and learner interface verification

HEAD == origin/main:
  YES

working tree at audit start:
  CLEAN

git diff at audit start:
  EMPTY
```

The previous `14993dee...` identity is the parent of the committed B2-V2
checkpoint, not the current authority. The source `TASK_PROGRESS.md` blob at
audit start was exactly the committed HEAD blob
`867d3e08189501aacbf8a4a9551274038be43b68`.

The B2-V2 closure report and committed handoff both classify B2-V2 as GPT REVIEW
PASS / CLOSED. Therefore B2-R starts from `b71d85...` and must preserve every
closed B2-V2 semantic unless a later explicitly authorized phase reopens it.

## 2. B2-V2 closure inherited contracts

B2-R inherits the following immutable semantic boundary:

1. Current P2 is the sole ownership authority. An actor proposal is not an
   effective assignment.
2. The actor action and behavior log-probability are the original policy
   proposal pair. Resolution, P2 mutation, and the final controller action do
   not rewrite that pair.
3. EXECUTING continuation is forced. It causes no actor resampling and no
   repeated claim mutation.
4. DVM is independent of `active_masks` and `available_actions`. A forced or
   no-policy row is not silently converted into a policy row.
5. Terminal evidence is environment-owned, historical, pre-reset evidence.
   Post-autoreset state is current state and cannot reconstruct the terminal
   transition.
6. Learner termination semantics retain four distinct authoritative reason
   identities. The selected reason is environment-owned historical evidence;
   the two zero-bootstrap categories may share GAE math but may not be collapsed
   into one evidence identity.

| Authoritative selected reason | Bootstrap used by learner | GAE trace rule |
|---|---|---|
| `NONE` | Normal current next-state critic value, gated by normal liveness | Continue according to normal liveness semantics |
| `ALL_TASKS_COMPLETED` | Exact zero | Stop |
| `NO_FEASIBLE_TASKS_REMAIN` | Exact zero | Stop |
| `TIME_LIMIT` | Authoritative correlated historical pre-reset timeout critic value | Stop |

If multiple raw conditions are simultaneously observable, the frozen
environment-owned reason precedence is:

```text
ALL_TASKS_COMPLETED
  > NO_FEASIBLE_TASKS_REMAIN
  > TIME_LIMIT
  > NONE
```

The highest-priority applicable reason is selected exactly once. `NONE` is
allowed only when no higher category applies. In particular, TIME_LIMIT can
never override either higher-priority zero-bootstrap terminal and can never
cause it to receive a timeout bootstrap. Terminal evidence and timeout critic
input remain pre-reset historical evidence; post-autoreset current state cannot
reconstruct either.
7. Event GAE is computed exactly once per complete rollout.
8. The frozen returns identity is:

```text
event result:
  [T,E,1]

critic-buffer storage:
  [T+1,E,1]

critic learner target:
  critic_buffer.returns[:-1]
  [T,E,1]
  finite
  exact-value-equal to the event result
  no alias with the event result

critic_buffer.returns[-1]:
  [E,1]
  structural / diagnostic only
  never a learner target
```

9. ValueNorm is inference-only while event returns are constructed: one stable
   normalizer snapshot denormalizes the value predictions, and return
   construction must not mutate it.
10. B2-V2 Snapshot B required actors, critic, actor optimizers, critic optimizer,
    and ValueNorm to remain unchanged because no training update was authorized.
    B2-R replaces that blanket no-mutation expectation only inside a future,
    explicitly authorized update seam.
11. The event learned-policy route remains private, dormant, and default-off.
12. B2-V2 establishes runtime-interface, policy-interface, and terminal
    learner-transport readiness. It does not establish training-update,
    convergence, public-route, long-run, or exact-resume readiness.

## 3. B2-R scope

B2-R is the bounded verification program for allowing real learner mutation
without weakening lifecycle semantics. It must establish:

- an exclusive and auditable update authority;
- exact actor row ownership for the original proposal and behavior logprob;
- DVM-aware HAPPO loss and full-index sequential-factor behavior for every
  actor in the one resolved configuration (`resolved_M=3` in the R0-audited
  snapshot);
- exact critic use of the frozen I5b target;
- a source-faithful ValueNorm training schedule;
- explicit backward and optimizer-step counts and ownership;
- finite loss, gradients, parameters, optimizer state, and ValueNorm state;
- expected versus forbidden mutation for each component;
- rollout, train, rollover, and checkpoint boundary ordering;
- fail-closed evidence for every partial or rejected update; and
- a progression from pure/static checks to one bounded private real update only
  under later, separate authorization.

The conceptual owner in this design is a future repo-local
`EventTrainingUpdateCoordinatorV1`. The name describes an architecture, not an
authorized implementation. It must be the sole caller of backward and
optimizer-step seams for the event route.

### Resolved configuration authority and derived counts

Every authorized update must bind one exact frozen resolved configuration into
the update authority and config digest:

```text
resolved_T = rollout length
resolved_E = rollout-environment count
resolved_M = actor count
resolved_N = resolved task/action cardinality used by the N+1 action width

B = resolved_T * resolved_E
```

Throughout this report, symbolic `T`, `E`, `M`, and `N` in shapes and equations
mean those per-update resolved values; they are not global architecture
constants. The architecture makes no arbitrary-cardinality or zero-shot
generalization claim.

The same config digest must bind `critic_epoch`, the approved critic minibatch
count and exact partition for every epoch, actor epoch/minibatch settings, mode
flags, and ValueNorm enablement. The immutable update plan derives and freezes:

```text
expected_critic_backward_count
  = sum over critic epochs of nonempty approved critic minibatches

expected_critic_optimizer_step_count
  = expected_critic_backward_count

expected_valuenorm_update_count
  = expected_critic_optimizer_step_count, when ValueNorm is enabled
  = 0, when ValueNorm is disabled

expected_actor_backward_count[actor]
  = sum over actor epochs of nonempty approved active-and-DVM minibatches

expected_actor_optimizer_step_count[actor]
  = expected_actor_backward_count[actor]
```

When the approved critic minibatch count is constant and every approved batch is
nonempty, the critic count simplifies to
`critic_epoch * approved_critic_minibatches_per_epoch`. R2 may deliberately
authorize backward with zero optimizer steps, so its separate plan must freeze
the two counts independently rather than reuse the later mutation formula.

The current R0-audited resolved configuration is an example, not an invariant:

```text
resolved_T = 1000
resolved_E = 20
resolved_M = 3
B = 20,000
critic_epoch = 5
critic_num_mini_batch = 2
use_valuenorm = true
```

## 4. B2-R non-goals

B2-R0 does not establish or authorize:

- implementation of the coordinator or adapters;
- B2-R1 or any later slice;
- public runner registration or learned-policy route activation;
- training, evaluation, playback, convergence, policy quality, or reward claims;
- arbitrary rollout lengths, scales, seeds, or cardinalities;
- long-duration training or campaign recovery;
- exact training resume;
- a change to lifecycle, P2, terminal transport, GAE, or returns semantics;
- modification of installed HARL; or
- a checkpoint write or weight load.

Learner transport readiness, training-update readiness, convergence, public
route readiness, and long training remain separate claims.

## 5. Installed HARL training path source map

The installed dependency audited for this report is under:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl
```

| Concern | Installed source | Audited behavior | B2-R disposition |
|---|---|---|---|
| Actor optimizer construction | `algorithms/actors/on_policy_base.py:38-43` | One Adam optimizer over the actor module parameters | Reuse only after exact ownership/disjointness proof |
| Stock HAPPO update | `algorithms/actors/happo.py:27-101` | Full supplied minibatch evaluation; active mask at loss reduction; unconditional backward/step | Forbidden as the event update authority |
| Stock HAPPO epochs/generator | `algorithms/actors/happo.py:103-155` | Full-row actor-buffer generators; no DVM field | Forbidden for event rows |
| Sequential HAPPO runner | `runners/on_policy_ha_runner.py:12-132` | One full `[T,E,1]` factor, one agent order, pre/post logprob evaluation on all rows, then critic train | Reuse as a semantic reference only; full-row route is inadmissible |
| Actor buffer | `common/buffers/on_policy_actor_buffer.py:32-185` | Stores active masks/action logprobs/factor and flattens all `T*E` rows; no DVM or canonical evidence ledger | Cannot be the authoritative event actor buffer |
| Critic optimizer construction | `algorithms/critics/v_critic.py:47-50` | One Adam optimizer over critic parameters | Reuse after ownership proof |
| Critic value loss | `algorithms/critics/v_critic.py:75-114` | Updates ValueNorm from raw `return_batch`, normalizes that same target, then computes clipped/unclipped loss | Retain source-faithful semantics behind guards |
| Critic update | `algorithms/critics/v_critic.py:116-157` | Forward, loss/ValueNorm mutation, zero-grad, backward, clip, unconditional step | Direct call forbidden; guarded adapter must own mutation |
| Critic train | `algorithms/critics/v_critic.py:159-200` | Repeats configured epochs and minibatches with no event evidence or finite-state guard | Direct call forbidden |
| Critic buffer generator | `common/buffers/on_policy_critic_buffer_ep.py:204-252` | Flattens `returns[:-1]`; floor-divides batch size; a remainder can be omitted | Semantics reused only with exact coverage/divisibility guard |
| Other critic generators | `common/buffers/on_policy_critic_buffer_ep.py:254-371` | Every variant sources the target from `returns[:-1]` | Consistent with I5b, but current config is feed-forward |
| ValueNorm | `common/valuenorm.py:38-75` | Raw-batch running-stat update and later normalization | Guard and fingerprint every call |
| Runner orchestration | `runners/on_policy_base_runner.py:189-315` | Rollout, compute, `prep_training`, train, logging/save, `after_update` | Stock save/rollover boundary is unsuitable for event checkpoints |
| Mode transitions | `runners/on_policy_base_runner.py:791-801` | Explicit actor/critic train and rollout modes | Future event coordinator must own equivalent transitions |

The stock actor path is a hard semantic mismatch for event training because it
has no independent DVM. Mapping DVM into `active_masks` is not admissible: it
destroys the independent lifecycle meaning, still permits factor evaluation on
forced rows, and provides no canonical proof of mathematical exclusion.

The stock critic math is not semantically contradictory with I5b, but its direct
`train()`/`update()` calls are not readiness-safe: they lack exact row-coverage,
finite-state, ownership, step-count, and partial-mutation guards.

## 6. Repo-local lifecycle learner path source map

| Concern | Repo-local source | Frozen or current behavior | B2-R obligation |
|---|---|---|---|
| Private event orchestration | `assignment_event_learned_route.py:305-717` | Private factory; dormant; no public registration | Extend only through a future reviewed private coordinator |
| Proposal collection | `assignment_event_actor_collection.py:527-726` | Actor called only on DVM rows; original proposal/logprob scattered to full grid | Preserve exact historical identity |
| Actor slot storage | `assignment_event_actor_collection.py:737-984` | Separate DVM and active masks; action/logprob slots `[T,E,1]` | Freeze and digest before update |
| DVM-aware HAPPO math | `assignment_event_happo_policy_math.py:314-1118` | DVM evaluation, active-and-DVM loss, full-grid factor, sequential actors | Canonical actor update basis; add guards and mutation evidence |
| Terminal learner transport | `assignment_event_terminal_learner_transport.py:148-1232` | Correlation keys, historical terminal records, exact timeout critic batch and critic guard | Must be immutable before training begins |
| Event critic buffer | `assignment_event_critic_buffer.py:89-320` | Event fields, compute-once returns, copy to `returns[:-1]`, rollover reset | Sole event target container |
| Event GAE | `assignment_event_gae_returns.py:236-457` | Distinct `NONE`, `ALL_TASKS_COMPLETED`, `NO_FEASIBLE_TASKS_REMAIN`, and `TIME_LIMIT` routing plus stable inference-side ValueNorm snapshot | Never replace with stock `compute_returns()` |
| Dormant finish order | `assignment_event_learned_route.py:554-655` | Returns, actor callback, critic callback, critic rollover, ledger reset, actor rollover | Add explicit modes, evidence gates, and quiescent checkpoint boundary |
| Assignment runner | `assignment_harl_training.py:460-738` | Public readiness guards; collection delegates to stock path | Must remain blocked and must not become B2-R's trainer path |
| Checkpoint save | `assignment_checkpoint_save.py:938-1081` | V2 actors/critic/ValueNorm only; missing optimizer/counters/RNG/runtime/buffers | Insufficient for exact event training resume |
| Event V3 descriptor | `assignment_checkpoint_contract_v3.py:996-1477` | Interface descriptor only; checkpoint-ready construction and weight use denied | Requires a genuine later R6 implementation |
| Checkpoint entry guard | `assignment_checkpoint_entry_guard.py:314-548` | V3 permits offline audit only and denies weight I/O | Preserve until R6 review explicitly changes it |

No frozen B2-V2 contract contradicts a repo-local guarded update design. A hard
contradiction would arise only if the stock full-row actor trainer or stock
returns computation were selected as the event authority. This design excludes
both paths fail closed.

## 7. Actor buffer/action/logprob ownership audit

The authoritative per-actor storage shapes are:

```text
obs:                   [T+1,E,O]
available_actions:     [T+1,E,N+1]
decision_valid_masks:  [T+1,E,1] bool
active_masks:          [T+1,E,1] float
action_ids:            [T,E,1]
action_logprobs:        [T,E,1]
```

`assignment_event_actor_collection.py:606-667` creates full-grid actions from
forced IDs, invokes each actor only at that actor's DVM env indices, and scatters
the sampled original proposal and behavior logprob back only to those indices.
Lines 692-714 retain a `0.0` sentinel for forced rows and explicitly deny that it
is behavior evidence. Lines 860-882 store the current envelope at slot `t`; the
next slot receives only next observation, availability, DVM, and active state.

Resolution is later and separate in
`assignment_event_learned_route.py:486-512`. The unchanged proposal envelope is
inserted at lines 541-542. Therefore the trainer input must bind these five
historical identities at canonical index `k = t * E + e`:

```text
(agent_id, t, env_id)
historical actor observation
historical available-action mask
original proposal action
behavior-old action logprob
DVM and active-mask values
```

Effective assignment, final P2, controller action, forced action identity, and
post-reset observation are forbidden substitutes.

Three logprob concepts must have distinct DTO fields and digests:

1. `behavior_old_logprob`: recorded during rollout for the original proposal;
2. `factor_pre_logprob`: fresh evaluation immediately before this actor update;
3. `factor_post_logprob`: fresh evaluation after all authorized steps for this
   actor.

Conflating any two is `STOP — B2-R ACTOR_EVIDENCE_BINDING`.

## 8. DVM/forced-row actor-loss audit

The repo-local I3b rule is source-explicit:

```text
policy evaluation population:
  decision_valid_masks[:-1]

actor loss / entropy / surrogate / gradient population:
  decision_valid_masks[:-1] AND active_masks[:-1]
```

Evidence is in `assignment_event_happo_policy_math.py:631-674` and the
minibatch filtering at lines 861-960. The historical available actions,
original action, and masks at the same canonical indices are passed to installed
`evaluate_actions()` at lines 719-760.

Required future behavior:

- forced-only or zero-active-and-DVM actor: no policy evaluation for training,
  no loss, no backward, no optimizer step, no factor evaluation, and no actor or
  optimizer mutation;
- mixed actor: only active-and-DVM rows enter loss/entropy/ratio/backward;
- inactive DVM rows may participate in pre/post factor evaluation if the actor
  updated elsewhere, but never in actor loss;
- forced/no-policy rows never enter either actor loss or the current actor's
  pre/post factor evaluation;
- a forced row's stored `0.0` logprob sentinel must never be read as PPO behavior
  evidence; and
- actor parameter mutation caused by valid rows in a mixed actor is allowed.
  The auditable claim for forced rows is exclusion from the graph and selected
  canonical indices, not per-row parameter identity after a shared-network
  update.

Stock `HAPPO.update()` at installed `happo.py:37-101` and stock actor-buffer
generators at `on_policy_actor_buffer.py:121-185` carry no DVM boundary. Calling
them for an event rollout is `STOP — B2-R STOCK_FULL_ROW_ACTOR_PATH`.

## 9. HAPPO sequential factor audit

For one exact permutation of all `resolved_M` actors, the required factor
recurrence is below. In the current R0-audited snapshot,
`resolved_M=3` and an example order is `(a0, a1, a2)`:

```text
F0 = ones[T,E,1]

Ra[k] = exp(factor_post_logprob[k] - factor_pre_logprob[k])
        when DVM_a[k] is true

Ra[k] = 1 exactly
        when DVM_a[k] is false

F_next = F_prev * Ra
```

I3b retains a full canonical `[T,E,1]` factor and scatters only current-actor
DVM ratios at `assignment_event_happo_policy_math.py:979-1008`. Sequence
validation requires one exact permutation of all resolved `M` actors
(`M=3` in the current R0-audited snapshot) and carries the complete factor
between actors at lines 1046-1117.

This has an important cross-agent consequence: for the current actor, a forced
row contributes ratio exactly one, but that row may legitimately retain factor
accumulated by an earlier actor that was DVM-valid at the same `(t,e)`. A forced
row therefore must not reset the accumulated factor to one.

The current resolved config has `fixed_order: false`, while the private route
defaults to canonical order if none is supplied
(`assignment_event_learned_route.py:605-618`). The future coordinator must
resolve this seam by generating exactly one random permutation of all
`resolved_M` actors per update, recording the RNG provenance and explicit
order, and passing that same immutable order through planning and execution. It
must not sample a new order per epoch or actor. This is a fixed resolved-scale
contract, not a variable-cardinality policy claim.

Required factor checks are stronger than current I3b:

- initial factor exact ones, correct shape/device/dtype, finite, and strictly
  positive;
- every pre/post logprob finite;
- every DVM ratio finite and strictly positive;
- off-DVM ratio exact one bit-for-bit;
- each `factor_after` exact-value-equal to `factor_before * ratio_full`;
- skipped actor leaves factor exact unchanged;
- no compact-DVM reindexing or scatter collision; and
- final factor finite and strictly positive.

Any underflow-to-zero ratio, even if otherwise finite, fails closed.

## 10. Critic target path audit

The event GAE source at `assignment_event_gae_returns.py:374-418` applies only
after the exact environment-owned precedence selection frozen in Section 2:

- copies native critic values and installs `next_value` at the final slot;
- uses one stable current ValueNorm snapshot only to denormalize arithmetic
  values;
- gives `NONE` rows the normal current next-state value multiplied by liveness
  and continues the trace according to liveness;
- gives `ALL_TASKS_COMPLETED` rows exact-zero bootstrap and stops the trace;
- gives `NO_FEASIBLE_TASKS_REMAIN` rows exact-zero bootstrap and stops the trace;
- gives `TIME_LIMIT` rows the correlated historical pre-reset timeout bootstrap
  and stops the trace; and
- creates returns as advantages plus current arithmetic values.

Lines 420-453 reject nonfinite intermediates and return detached copies.

`assignment_event_critic_buffer.py:266-312` allows exactly one return
computation after every transition slot is complete and copies only the result
into `self.returns[:-1]`. The final slot remains structural. The installed
feed-forward critic generator at
`on_policy_critic_buffer_ep.py:204-252` then flattens exactly
`self.returns[:-1]`; all other installed generator variants also use that slice.

Installed `VCritic.update()` receives `return_batch` unchanged and performs no
terminal or bad-mask bootstrap logic (`v_critic.py:125-141`). Thus the correct
guarded path does not double-bootstrap. Calling stock runner
`critic_buffer.compute_returns()` at `on_policy_base_runner.py:520-542` would
bypass event semantics and is forbidden.

Before any future update, the coordinator must freeze:

- result digest and storage-slice digest;
- exact shape/dtype/device/finite facts;
- exact-value equality and no-alias evidence;
- final-slot exclusion evidence;
- canonical target indices for every critic minibatch; and
- exact full-grid coverage per critic epoch.

The stock feed-forward generator floor-divides
`B / critic_num_mini_batch`, where `B = resolved_T * resolved_E`. It can omit a
remainder. For every configured critic epoch, every canonical physical
transition index `k` in `[0, B)` must appear exactly once across the approved
critic minibatch plan. Omitted or duplicated rows fail closed. The guarded event
path must require positive batch sizes and exact divisibility, or use an
explicitly reviewed exact-coverage partitioner.

For the current R0-audited resolved configuration example,
`resolved_T=1000`, `resolved_E=20`, and `critic_num_mini_batch=2`; therefore
`B=20,000`, divisibility holds, and each of its five critic epochs must cover
those 20,000 canonical rows exactly once. None of these literal counts is a
global B2-R architecture constant.

Critic training includes all physical transition rows, including forced and
no-policy rows. DVM is an actor-policy mask, not a critic-target filter.

## 11. ValueNorm update audit

There are two distinct ValueNorm phases:

1. Return construction: inference-only, one stable normalizer snapshot, no
   mutation (`assignment_event_gae_returns.py:155-217,374-381`).
2. Critic training: installed `VCritic.cal_value_loss()` calls
   `value_normalizer.update(return_batch)` on the unnormalized raw target and
   then normalizes that same batch for the loss
   (`v_critic.py:90-95`). `ValueNorm.update()` mutates running mean, running
   squared mean, and debiasing term at `valuenorm.py:47-64`.

B2-R freezes the installed-source-faithful training schedule:

```text
for each configured critic epoch:
  for each exact planned critic minibatch:
    take raw return_batch from frozen critic_buffer.returns[:-1]
    validate raw target identity and finiteness
    call ValueNorm.update(raw return_batch) exactly once
    normalize that same raw return_batch using the resulting state
    compute the installed value loss
```

The exact counts are configuration-relative and are frozen in the approved
update plan:

```text
expected_critic_optimizer_step_count
  = sum over critic epochs of nonempty approved critic minibatches

expected_valuenorm_update_count
  = expected_critic_optimizer_step_count, when ValueNorm is enabled
  = 0, when ValueNorm is disabled
```

For the current R0-audited resolved configuration example only,
`critic_epoch=5`, two approved nonempty critic minibatches exist per epoch, and
`use_valuenorm=true`; therefore the derived result for one successfully
completed update is 10 critic optimizer steps and 10 ValueNorm update calls.

The minibatch permutations, canonical index sets, raw-target digests, and
pre/post normalizer fingerprints must be recorded because this update sequence
is stateful and order-sensitive. ValueNorm must not be updated from normalized
targets, advantages, value predictions, the structural final returns slot, or
an omitted/repeated row.

This R0 deliberately does not redesign ValueNorm into a single full-rollout
update. Such a change would no longer match installed `VCritic` training
semantics and must reopen B2-R0 rather than being introduced silently.

When ValueNorm is disabled, the object must be absent or exact unchanged and
the raw return target is used directly. When enabled, a controlled nondegenerate
R4 smoke must demonstrate both the exact resolved call count (10 for the current
R0-audited example) and actual normalizer state mutation.

## 12. Optimizer/backward path audit

Installed actor `HAPPO.update()` performs:

```text
evaluate -> ratio/surrogate/loss -> zero_grad -> backward -> clip -> step
```

at `happo.py:55-99`. Installed critic `VCritic.update()` performs:

```text
forward -> ValueNorm update/loss -> zero_grad -> backward -> clip -> step
```

at `v_critic.py:125-155`. Neither path provides the complete event evidence,
foreign-gradient detection, finite optimizer-state audit, exact step receipt,
or partial-mutation recovery boundary required by B2-R.

The future coordinator therefore must use guarded repo-local adapters:

- actor adapter: installed actor network/distribution, `evaluate_actions`, Adam
  optimizer, clip setting, entropy coefficient, PPO parameters, and current
  repo-local DVM/full-factor math;
- critic adapter: installed critic network, `get_values`, source-faithful
  `cal_value_loss`, Adam optimizer, clip/loss settings, and an exact event target
  plan; and
- coordinator: the sole owner of `zero_grad`, backward, clip, and optimizer
  step authorization and receipts.

Direct calls from the event route to stock `OnPolicyHARunner.train()`,
`HAPPO.train()`, `HAPPO.update()`, `VCritic.train()`, or `VCritic.update()` are
forbidden. Direct stock runner return computation is also forbidden.

Every mutation call requires a single-use capability binding:

```text
update_id
component_kind
owner_id
agent_id when applicable
epoch
minibatch
canonical_index_digest
expected backward count
expected step count
pre-state fingerprint
```

A missing, duplicated, expired, misowned, or out-of-order capability is an
authorization failure before mutation.

## 13. Mutation expectation contract

The B2-V2 all-unchanged Snapshot B contract applies before the update permit and
outside the permit. Inside a successful B2-R update, the expected contract is:

| Component/case | Backward and step expectation | Parameter/state expectation |
|---|---|---|
| Actor with zero active-and-DVM rows, including forced-only | Exactly 0 backward and 0 steps | Actor module, optimizer, gradients, and factor exact unchanged; gradients cleared/None |
| Actor with mixed rows | Only nonempty planned active-and-DVM minibatches may backward/step | Actor and its optimizer may mutate due valid rows; forced rows are proven graph-excluded |
| Actor with valid rows | Exact config-bound count of nonempty approved active-and-DVM minibatches across all actor epochs | Controlled mutation smoke selects a nonzero effective gradient and requires at least one owned parameter change; the current R0 example can derive 5 through 10 steps per eligible actor from five epochs and two planned minibatches |
| Non-current actors during one actor segment | 0 backward and 0 steps | Modules, optimizers, and gradients exact unchanged |
| Critic | All approved nonempty minibatches; exact configuration-relative derived count | Critic/optimizer may mutate; controlled nondegenerate smoke requires at least one critic parameter change; the current R0 example derives 10 steps |
| Critic in a proved zero-effective-update case | Authorized count may execute only if the test explicitly targets that case | Parameter no-change is allowed only with exact zero-effective-update evidence; optimizer state may still mutate |
| ValueNorm enabled | Exactly one raw-target update per processed approved critic minibatch; exact count equals the configuration-relative critic step count | State transition receipts required; nondegenerate R4 requires actual state mutation; the current R0 example derives 10 updates |
| ValueNorm disabled | 0 updates | Absent or exact unchanged |
| Actors during critic segment | 0 backward and 0 steps | All actor modules/optimizers exact unchanged |
| Critic during actor segments | 0 backward and 0 steps | Critic module/optimizer/ValueNorm exact unchanged |

An Adam optimizer can mutate its step counters and moments even when a parameter
delta is zero. Therefore optimizer-state expectation is based on exact authorized
step receipts and full optimizer fingerprints, not inferred from parameter
equality alone.

Before/after fingerprints must cover:

- ordered parameter names, shapes, dtypes, devices, requires-grad flags, and
  exact tensor digests;
- ordered optimizer parameter groups, hyperparameters, parameter identities,
  all tensor/scalar state, and per-parameter step values;
- complete ValueNorm state;
- gradient presence, tensor digest, finiteness, and norm per owned parameter;
- module train/eval mode; and
- factor and frozen training-input digests.

Actor optimizer parameter sets must be exact, mutually disjoint across all
`resolved_M` actors (`resolved_M=3` in the current R0-audited snapshot), and
disjoint from the critic. Critic optimizer ownership must be exact.
Shared-parameter mode is currently false; any future change to true is a
contract change requiring a new design audit.

## 14. Gradient/nonfinite safety contract

The future mutation seam must fail closed at each boundary.

Before backward:

- rollout and target state is complete and immutable;
- selected canonical rows equal the approved plan;
- observations, masks, actions, behavior logprobs, advantages, factors, values,
  raw returns, normalized targets, and scalar loss are finite;
- actor ratios and factors are finite and strictly positive;
- no stale gradient exists on owned or foreign parameters; and
- no unauthorized module or optimizer has changed since its fingerprint.

After backward and before step:

- exactly one authorized backward receipt exists;
- every present owned gradient is finite;
- the aggregate and per-parameter norms are finite;
- clipping result is finite and within the explicit policy;
- foreign components have no new gradient;
- no parameter or optimizer state has changed yet; and
- a deliberate zero-gradient case is classified explicitly rather than hidden.

After step:

- exactly one authorized step receipt exists;
- all owned parameters are finite;
- all optimizer tensor/scalar state is finite and structurally valid;
- non-owned components are exact unchanged;
- the observed mutation class matches the planned expectation; and
- any ValueNorm mutation belongs to the exact critic minibatch receipt.

The installed clipping calls do not set `error_if_nonfinite=True`; explicit
pre/post finite checks are therefore mandatory.

Failure before any irreversible mutation may reject the update cleanly. Failure
after an optimizer or ValueNorm mutation is a partial-update failure: the route
must be poisoned, no later actor/critic step may run, and rollover, ledger reset,
checkpoint, next rollout, and public use are forbidden. A controlled harness may
attempt restoration from a pre-state snapshot, but the route remains poisoned
even if byte-level restoration succeeds. If restoration cannot be proven exact,
the process is quarantined and must be destroyed.

Evidence must name the exact tensor/state field, component owner, epoch,
minibatch, canonical index or parameter name, expected condition, and observed
category. A generic `training failed` message is not acceptable.

## 15. Training-step ordering contract

One successful future event update must follow this state machine:

```text
S0  ROLLOUT_COMPLETE
    every actor/critic/event slot present; terminal correlation and the exact
    four-category selected-reason/precedence evidence closed

S1  FINAL_VALUE_EVALUATED
    critic in rollout mode; normal final value and timeout sidecars frozen

S2  EVENT_RETURNS_FROZEN
    compute_event_returns exactly once; I5b equality/no-alias/final-slot checks

S3  UPDATE_PLAN_FROZEN
    explicit permutation of all resolved M actors (M=3 in the current R0
    snapshot); actor and critic partitions; config-derived ownership/counts;
    all input, module, optimizer, ValueNorm, gradient, and mode fingerprints

S4  TRAINING_MODE_ENTERED
    actors and critic explicitly switched through reviewed prep_training seams

S5  ACTOR_SEQUENCE
    every resolved actor exactly once in the one recorded order;
    per-minibatch permits and full-index factor evidence after each actor

S6  CRITIC_SEQUENCE
    exact full target coverage; per-minibatch raw-target ValueNorm update;
    guarded critic backward and step

S7  POST_UPDATE_AUDIT
    exact receipts/counts; finite states; expected and forbidden mutations;
    frozen input and lifecycle evidence still exact

S8  ROLLOUT_MODE_RESTORED
    actors and critic explicitly switched through reviewed prep_rollout seams

S9  ROLLOVER_COMPLETE
    critic after_update; terminal-consumption ledger reset only afterward;
    actor storages rebuilt from final current slots; fresh guards established

S10 QUIESCENT
    no live rollout evidence, pending gradient, unconsumed terminal key,
    incomplete receipt, or poison; optional reviewed checkpoint boundary
```

No stage may be skipped or reordered. The actor sequence cannot begin before
the returns/advantages and complete plan are frozen. Critic training cannot
begin after a failed actor. Rollover cannot begin before the post-update audit
and mode restoration pass.

The private `finish_rollout()` currently has the broad returns -> actor ->
critic -> rollover order, but it lacks explicit mode transitions and the above
mutation/evidence gates. Those are B2-R implementation obligations, not B2-R0
changes.

## 16. Rollover ordering

The required rollover suborder is:

```text
1. verify every expected actor/critic/ValueNorm receipt;
2. verify finite and correctly attributed final training state;
3. clear or prove absent every gradient;
4. enter rollout/eval mode;
5. call critic_buffer.after_update();
6. only after that call, reset the terminal-consumption ledger;
7. rebuild each actor storage from the final current observation/mask/DVM/active slot;
8. capture new rollout guards and prove the new write cursors are at slot zero;
9. enter QUIESCENT.
```

`assignment_event_critic_buffer.py:314-320` clears event reasons, timeout values,
timeout masks, written-slot flags, and the compute-once flag during
`after_update()`. The terminal ledger already requires the buffer rollover first
at lines 345-365. This relation remains protected.

On any failure, none of steps 5-9 is allowed. Preserving failed-rollout evidence
is more important than making the object reusable.

## 17. Checkpoint/save-load implications

The current V2 saver writes actor, critic, and optional ValueNorm state, but its
training-state manifest explicitly marks actor optimizer, critic optimizer,
training counters, RNG, environment/resolver state, and rollout buffers absent
(`assignment_checkpoint_save.py:1063-1079`). The V2 contract consequently
denies training initialization and exact resume
(`assignment_checkpoint_contract.py:1212-1230`).

Event V3 remains an interface-only descriptor:

- checkpoint-ready manifests are rejected at
  `assignment_checkpoint_contract_v3.py:1031-1040`;
- `build_checkpoint_ready_v3()` always fails closed at lines 1286-1345; and
- the entry guard denies V3 weight I/O at
  `assignment_checkpoint_entry_guard.py:370-417,537-548`.

B2-R6 must therefore be genuine later implementation and should split. It is a
checkpoint-readiness claim, not an implicit prerequisite for bounded
training-update correctness or B2-R7 closure:

### B2-R6a: safe-boundary weight continuation

Potentially save actors, critic, and ValueNorm only at S10 QUIESCENT after a
fully successful update and rollover. Loading must require an explicit
acknowledgement that optimizer state, counters, RNG, environment/lifecycle/P2/
resolver state, route state, and buffers reset. This is weight continuation, not
exact resume. R6a is separately authorized and may later gate long-duration or
interruption/restart workflows; it does not gate one bounded semantically
correct learner update or B2-R7 unless a future explicit authorization changes
that scope.

### B2-R6b: exact training resume, optional and separately authorized

Exact resume additionally requires all optimizers, schedules and counters,
best-reward state, Python/NumPy/Torch CPU/CUDA RNG, environment/lifecycle/P2/
resolver/budget state, route phase/poison status, and actor/critic buffers with
DVM and terminal sidecars. If not explicitly requested, exact resume remains a
nonclaim, a separate claim, and not a first-paper requirement.

Installed runner periodic/best saves occur after training but before
`after_update()` (`on_policy_base_runner.py:280-314`), so that stock timing is
not an event-safe checkpoint boundary. No checkpoint may be saved from a
partial, poisoned, pre-rollover, gradient-bearing, or receipt-incomplete state.

## 18. Proposed B2-R slice decomposition

The labels below identify evidence slices, not a mandatory numeric execution
order. The dependency graph is:

```text
main training-update readiness path:
  B2-R1 -> B2-R2 -> B2-R3 -> B2-R4 -> B2-R5 -> B2-R7

orthogonal checkpoint-readiness branch:
  B2-R6a  quiescent weight continuation, separately authorized
  B2-R6b  optional exact resume, separately authorized and a separate claim
```

B2-R7 depends on accepted B2-R1 through B2-R5 evidence. Neither B2-R6a nor
B2-R6b is a prerequisite for B2-R7. R6a may become a prerequisite for
long-duration training or interruption/restart workflows, but not for proving
one bounded learner update semantically correct, unless future explicit user
authorization changes the scope. R6b is not silently promoted into a
first-paper requirement.

### B2-R0 — architecture and contract design

This report only. No implementation or mutation.

### B2-R1 — pure/static coordinator contracts

Add repo-local/test-only DTOs, canonical fingerprints, ownership and
disjointness checks, immutable update plans, single-use permits, source/AST
guards, and pure fault-injection tests. No backward, optimizer, Isaac, training,
or public path.

### B2-R2 — controlled backward/no-step gradient probe

Exercise selected actor and critic graphs with optimizer step trapped. Use
cloned or exactly snapshotted ValueNorm so live ValueNorm remains unchanged.
Verify DVM graph exclusion, finite gradients, foreign-gradient absence, and
post-probe gradient cleanup. This slice requires separate user authorization.

### B2-R3 — controlled actor optimizer mutation

Use the installed actor modules/optimizers behind the guarded DVM adapter.
Verify forced-only skip, mixed-DVM selection, one explicit random permutation
of all resolved `M` actors (`M=3` in the current R0 snapshot), config-derived
per-minibatch step counts, full-index factor attribution, ownership, finite
state, and fault behavior.

### B2-R4 — controlled critic and ValueNorm integration

Use the exact frozen I5b target, exact full-row critic coverage, guarded
installed critic loss/optimizer semantics, and the source-faithful per-minibatch
ValueNorm schedule. Verify target identity, exact resolved step/update counts
(10/10 for the current R0-audited example), attribution, and rollover
preconditions.

### B2-R5 — one bounded private full learner update

First perform a controlled synthetic atomic integration if needed. A single
real Isaac/full learner update is a separate explicit authorization and remains
private, bounded, default-off, and non-convergence evidence. It must not become
a public runner or long-training run.

### B2-R7 — training-update readiness closure

Review accepted R1-R5 bounded evidence and retained nonclaims. Public route
remains dormant; long training remains separately unauthorized. R6a and R6b are
not prerequisites.

### Orthogonal branch: B2-R6a — quiescent weight-continuation checkpoint

Only under separate authorization, implement and verify a reviewed event V3
weight-continuation contract at S10 with explicit reset acknowledgement. This
branch is not on the R1-R5-to-R7 dependency path.

### Optional branch: B2-R6b — exact resume

Exact resume is separately authorized, optional, and a separate claim. Do not
infer it from R6a, B2-R7, long-training aspirations, or first-paper scope.

This decomposition retains R2 because a backward-only gate materially isolates
row selection and gradient ownership from irreversible optimizer mutation.
The R6 labels are retained to avoid churn; their numbers do not imply that they
must execute before R7.

## 19. Test-only vs real-runtime verification matrix

| Claim | R1 pure/static | R2 backward/no-step | R3/R4 controlled optimizer | R5 private real runtime | R6 checkpoint branch (orthogonal) | Long training/public |
|---|---:|---:|---:|---:|---:|---:|
| DTO/schema and canonical digests | Required | Reuse | Reuse | Reuse | Reuse | Not claimed |
| Exact actor/optimizer ownership | Required statically | Runtime confirm | Required | Required | Inventory only | Not claimed |
| Original proposal/logprob binding | Pure fixtures | Required | Required | Required | Descriptor | Not claimed |
| Forced-row graph exclusion | Pure math | Required | Required | Required | N/A | Not claimed |
| Resolved-M order/factor recurrence (`M=3` in current R0 snapshot) | Pure math | Evaluate only | Required mutation evidence | Required | Descriptor | Not claimed |
| Exact I5b critic target | Pure target oracle | Gradient input | Required | Required | Descriptor | Not claimed |
| ValueNorm inference no-mutation | Existing B2-V2 | Required | Preserve | Required | State inventory | Not claimed |
| ValueNorm training mutation | Plan/count only | Live state unchanged | R4 required | Required | State save/load | Not claimed |
| Actor/critic parameter mutation | Forbidden | Forbidden | Required controlled cases | Required | Persistence only | Not claimed |
| Optimizer-state mutation | Forbidden | Forbidden | Required | Required | R6a absent/reset; R6b optional | Not claimed |
| Real terminal/autoreset correlation | Existing evidence only | Synthetic | Synthetic | Required inherited binding | Descriptor | Not claimed |
| Rollover/quiescence | Pure state machine | No rollover | Controlled | Required | Required | Not claimed |
| Checkpoint weight continuation | No | No | No | No | R6a | Not claimed |
| Exact training resume | No | No | No | No | R6b only | Not claimed |
| Convergence/policy quality | No | No | No | No | No | Separate phase |
| Public route readiness | Blocked | Blocked | Blocked | Blocked | Blocked | Separate phase |

Synthetic tensor or AST evidence is not runtime identity. Conversely, one real
bounded update is not convergence, campaign, exact-resume, or public readiness.
The matrix columns are claim/evidence scopes, not phase-dependency arrows; the
dependency graph in Section 18 is authoritative.

## 20. Required evidence DTOs / fingerprints

The future implementation should use immutable, JSON-serializable summaries
with bounded payloads and exact tensor/state digests. At minimum:

### `B2RUpdateAuthorityV1`

- committed HEAD and dirty-state classification;
- source and installed-package file hashes;
- exact config digest and resolved `T/E/M/N`;
- critic epoch/minibatch settings, actor epoch/minibatch settings, mode flags,
  and ValueNorm enablement bound by that digest;
- update ID and slice identity; and
- authorization scope and forbidden operations.

### `B2RFrozenTrainingInputsV1`

- actor storage identities and canonical full-grid digests;
- historical obs/availability/action/behavior-logprob/DVM/active digests;
- exact selected-reason `[T,E,1]` grid and digest, four-category domain and
  exactly-one-selected-category checks, precedence-resolution evidence,
  terminal correlation, and timeout critic evidence digests;
- event result, `returns[:-1]`, final-slot, value baseline, and advantage
  digests; and
- equality, no-alias, shape, dtype, device, and finite facts.

### `B2RActorUpdatePlanV1`

- authority config digest and one exact permutation of all resolved `M` actors
  (`M=3` in the current R0-audited snapshot);
- exact actor epoch/minibatch settings and approved partition digests;
- per actor/epoch/minibatch canonical planned indices;
- DVM evaluation indices and active-and-DVM loss indices;
- behavior-old/factor-pre/factor-post field identities;
- expected empty/nonempty batches and exact configuration-derived backward and
  optimizer-step counts per actor; and
- input factor digest and expected factor transition.

### `B2RCriticUpdatePlanV1`

- authority config digest, resolved `T/E/M/N`, `B = resolved_T * resolved_E`,
  critic epoch count, approved minibatch count, and exact partitions;
- exact canonical full-grid indices for every epoch/minibatch;
- positive-size, divisibility or reviewed-partitioner, and exact-once coverage
  proof for every `k` in `[0, B)` per epoch;
- raw target digest per minibatch;
- exact configuration-derived critic backward and optimizer-step counts; and
- exact configuration-derived ValueNorm call order/count, including zero when
  disabled.

### `B2RComponentFingerprintV1`

- component/owner identity;
- ordered module parameters and buffers;
- optimizer groups, hyperparameters, complete state, and step counters;
- ValueNorm state where applicable;
- gradients and module mode; and
- canonical exact digest plus finite-state summary.

### `B2RMutationPermitV1`

- single-use binding to owner, stage, epoch, minibatch, and canonical index
  digest;
- allowed operations (`backward`, `valuenorm_update`, `optimizer_step`);
- expected call counts; and
- precondition fingerprint.

### `B2RStepReceiptV1`

- consumed permit identity;
- pre-loss, loss, gradient, clip, post-parameter, optimizer, and ValueNorm
  fingerprints;
- exact mutation/no-mutation classification;
- no-foreign-mutation result; and
- stage transition evidence.

### `B2RFactorTransitionEvidenceV1`

- actor/order identity;
- factor-before, ratio-full, and factor-after digests;
- DVM and off-DVM index digests;
- strict-positivity and finite results; and
- off-DVM exact-one and recurrence checks.

### `B2ROrderingAndRolloverEvidenceV1`

- ordered S0-S10 receipts;
- mode transitions;
- buffer cursor and event-compute flags;
- terminal-ledger state;
- gradient-clear state; and
- quiescent checkpoint eligibility.

### `B2RFailureEvidenceV1`

- exact STOP code and stage;
- owner/agent/epoch/minibatch/canonical or parameter identity;
- expected versus observed bounded summaries;
- last completed receipt;
- whether any irreversible mutation occurred;
- poison, restoration, and quarantine state; and
- explicitly prohibited next actions.

Raw large tensors, complete model weights, or unbounded exception dumps should
not be embedded in reports. Use exact digests plus narrowly bounded offending
values/indices.

## 21. STOP taxonomy / failure boundaries

The coordinator must emit one precise category, not a blanket failure:

```text
STOP — B2-R AUTHORITY_DRIFT
STOP — B2-R SOURCE_CONTRACT_CONTRADICTION
STOP — B2-R PUBLIC_ROUTE_OPEN
STOP — B2-R STOCK_FULL_ROW_ACTOR_PATH
STOP — B2-R STOCK_RETURNS_BYPASS
STOP — B2-R ROLLOUT_INCOMPLETE
STOP — B2-R TERMINATION_PRECEDENCE
STOP — B2-R ACTOR_EVIDENCE_BINDING
STOP — B2-R FORCED_ROW_POLICY_LEAK
STOP — B2-R AGENT_ORDER
STOP — B2-R FACTOR
STOP — B2-R CRITIC_TRAINING_SLICE
STOP — B2-R CRITIC_ROW_COVERAGE
STOP — B2-R VALUENORM
STOP — B2-R OWNERSHIP
STOP — B2-R UNAUTHORIZED_BACKWARD
STOP — B2-R UNAUTHORIZED_OPTIMIZER_STEP
STOP — B2-R UNEXPECTED_STEP_COUNT
STOP — B2-R NONFINITE_TARGET
STOP — B2-R NONFINITE_LOSS
STOP — B2-R NONFINITE_GRADIENT
STOP — B2-R NONFINITE_PARAMETER
STOP — B2-R NONFINITE_OPTIMIZER_STATE
STOP — B2-R NONFINITE_VALUENORM_STATE
STOP — B2-R MUTATION_ATTRIBUTION
STOP — B2-R MODE_ORDER
STOP — B2-R ROLLOVER_ORDER
STOP — B2-R CHECKPOINT_BOUNDARY
STOP — B2-R RUNTIME_SMOKE
```

`SOURCE_CONTRACT_CONTRADICTION` is reserved for a genuine irreconcilable frozen
contract/source conflict. A missing implementation, guard, DTO, or test is a
planned readiness gap, not such a contradiction.

Any failure after the first irreversible mutation must additionally carry:

```text
partial_update: true
route_poisoned: true
rollover_allowed: false
checkpoint_allowed: false
next_rollout_allowed: false
public_use_allowed: false
```

## 22. Public-route activation boundary

The event route remains independently blocked at multiple layers:

- pre-AppLauncher scenario preflight (`scenario_config.py:353-392`);
- runtime profile readiness (`assignment_profile_contract.py:1222-1250`);
- the public wrapper factory, which supplies no event facade
  (`assignment_harl_wrapper.py:3114-3132`); and
- runner initialization before environment/model construction
  (`assignment_harl_training.py:471-496`).

B2-R must not weaken any of these gates. Public activation is not a single flag
change and is not implied by B2-R7. It requires a separate, atomic design and
explicit GPT/user authorization after training-update closure.

Static guards in B2-R1 should prove that no public path can instantiate the
private coordinator and that the stock public runner cannot silently select it.

## 23. Long-training authorization boundary

B2-R5, if later authorized and passed, proves at most one/few bounded private
learner updates under the exact audited configuration. It does not authorize:

- a training campaign;
- repeated updates over arbitrary rollouts;
- evaluation or playback;
- checkpoint recovery after interruption;
- convergence or policy-quality claims;
- production resource use; or
- public route activation.

Long training requires a separate phase with an explicit run budget, stop and
monitor policy, checkpoint/recovery classification, evaluation boundary,
artifact retention plan, and user authorization. Current YAML has evaluation
enabled, but event evaluation has not been established; any future bounded
training entry must explicitly suppress or separately authorize that path.

## 24. Protected invariants from B2-V2

Every B2-R slice must re-prove or preserve these invariants at its boundary:

1. proposal is not effective assignment;
2. original action/logprob pair is immutable after collection;
3. P2 is sole ownership authority;
4. final P2 drives Ak and the controller;
5. forced continuation does not resample an actor;
6. forced continuation does not create a repeated claim;
7. DVM, active mask, and available actions remain distinct;
8. historical terminal state is pre-reset and current state is post-autoreset;
9. safe historical copy precedes ACK/reset reuse;
10. timeout critic input is exactly correlated to the historical terminal row;
11. `ALL_TASKS_COMPLETED`, `NO_FEASIBLE_TASKS_REMAIN`, `TIME_LIMIT`, and
    `NONE` remain distinct selected-reason identities with precedence
    `ALL_TASKS_COMPLETED > NO_FEASIBLE_TASKS_REMAIN > TIME_LIMIT > NONE` and
    the exact bootstrap/trace semantics in Section 2;
12. event returns are computed once from complete I5a fields;
13. `returns[:-1]` is the exact finite, non-alias learner target;
14. the final returns slot is never sampled;
15. return construction does not mutate ValueNorm;
16. legacy/default profiles remain isolated and default-off;
17. failed or poisoned state cannot roll over, save, or continue; and
18. public learned-policy execution remains dormant and blocked.

Actor/critic/optimizer/ValueNorm no-mutation remains protected before an update
permit, after quiescence except for expected retained learned state, on skipped
owners, and on every non-target component. Only precisely authorized mutation
inside the coordinator changes the B2-V2 Snapshot B expectation.

## 25. Recommended next implementation slice

The next slice, only after independent GPT re-review and a new explicit user
authorization, should be B2-R1 with this exact boundary:

- repo-local/test-only immutable DTOs and canonical fingerprints;
- actor/critic/optimizer ownership and disjointness audits;
- immutable actor/critic minibatch plans and exact row-coverage proofs;
- single-use mutation permits represented but never consumed by real mutation;
- source/AST guards denying stock actor train/update, stock critic train/update,
  and stock return computation from the event route;
- pure factor, mutation-expectation, ordering, and STOP evidence tests; and
- fault injection before every future mutation boundary.

B2-R1 must not modify the public route or installed HARL, and must not execute
backward, optimizer step, Isaac, training, evaluation, playback, or checkpoint
weight I/O. It must stop for review before B2-R2.

## 26. Final classification

The source audit found no irreconcilable contradiction between the frozen B2-V2
contracts and a repo-local guarded training-update architecture. GPT then gave
the design a CONDITIONAL PASS and requested three targeted documentation
hardening items. This revision completes those requested items without
restarting the audit or changing the accepted architecture.

The stock installed/public HAPPO actor path is not admissible because it has no
DVM-aware row boundary and evaluates its sequential factor on the full rollout
grid. The stock critic target slice and installed ValueNorm/value-loss semantics
are compatible only when wrapped by exact event target, row coverage,
ownership, finite-state, step-count, and ordering guards. Existing checkpoint
contracts remain insufficient for exact resume and continue to deny V3 weight
I/O.

This document does not self-classify the design as GPT REVIEW PASS. Its current
handoff classification is:

```text
PHASE-B2-R0-TRAINING-UPDATE-READINESS-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW
```

Readiness after this report:

```text
current-production runtime-interface readiness:
  REVIEW PASS (inherited)

policy-interface readiness:
  REVIEW PASS (inherited)

terminal learner-transport readiness:
  REVIEW PASS (inherited)

B2-R0 prior GPT review:
  CONDITIONAL PASS

B2-R0:
  TARGETED REVISION COMPLETE / AWAITING GPT RE-REVIEW

implementation:
  NOT AUTHORIZED

training-update readiness:
  NOT YET ESTABLISHED

training convergence / policy quality:
  NOT ESTABLISHED

public learned-policy route:
  DORMANT / BLOCKED

long training:
  NOT AUTHORIZED

B2-R1:
  NOT STARTED / REQUIRES EXPLICIT USER AUTHORIZATION AFTER GPT RE-REVIEW
```

Stop here. Do not implement B2-R1, run a trainer, activate the public route,
modify a checkpoint, or commit as part of B2-R0.
