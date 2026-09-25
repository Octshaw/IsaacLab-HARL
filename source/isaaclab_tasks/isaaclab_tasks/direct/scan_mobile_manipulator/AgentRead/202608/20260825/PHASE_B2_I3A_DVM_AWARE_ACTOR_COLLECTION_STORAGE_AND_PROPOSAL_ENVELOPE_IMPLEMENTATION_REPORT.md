# Phase B2-I3a DVM-aware Actor Collection, Storage, and Proposal Envelope — Implementation Report

Date: 2026-08-25

Classification: `PHASE-B2-I3A-DVM-AWARE-ACTOR-COLLECTION-STORAGE-AND-PROPOSAL-ENVELOPE-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Status and scope boundary

```text
B2-D:                              REVIEW PASS / FROZEN
B2-I0:                             REVIEW PASS / CLOSED
B2-I1:                             REVIEW PASS / CLOSED
B2-I2:                             REVIEW PASS / CLOSED
B2-I3a:                            IMPLEMENTED / AWAITING GPT REVIEW
Phase B overall:                   NOT COMPLETE
runtime readiness:                BLOCKED
policy readiness:                 BLOCKED
learner readiness:                BLOCKED
public learned-policy event step: BLOCKED
training:                          NOT AUTHORIZED
commit:                            NONE
```

Only B2-I3a was implemented. B2-I3b, B2-I4, B2-I5a, B2-I5b, B2-I6, and later verification/readiness slices were not started.

## 2. Starting checkpoint and authority

```text
branch: main
HEAD: 14993dee344bade0230d2eb97b5f22171331f44a
subject: feat(mrta): complete lifecycle runtime backbone and wrapper integration
B2-I2 review authority: REVIEW PASS / CLOSED, supplied by the user
```

The frozen B2-D/I0/I1/I2 artifacts and all pre-existing uncommitted work were preserved. No commit was created.

## 3. Changed files

Implementation:

- `assignment_event_actor_collection.py` — new repo-local DVM subset collector, immutable proposal envelope, and bounded per-actor slot storage.

Verification:

- `scripts/environments/test_assignment_phase_b2_i3a_dvm_actor_collection_storage_proposal_envelope_pure.py` — new 15-oracle synthetic/component fixture.

Documentation:

- this report;
- `AgentRead/TASK_PROGRESS.md`.

No I2 decision source, I1 evidence source, I4-2 adapter, wrapper, runner, installed HARL file, actor loss, buffer implementation, critic, GAE, environment, DirectMARLEnv, P2/lifecycle authority, B1 transaction, Ak/controller, configuration, or checkpoint was modified.

## 4. Collector architecture

The new collector has one exact semantic input and one fixed-shape output:

```text
exact EventPolicyDecisionBundle
  + distinct per-agent actors
  + current actor RNN placeholders and masks
        |
        | gather only DVM=true rows per agent
        v
installed get_actions(subset, deterministic=False)
        |
        | scatter by canonical env indices
        v
immutable EventPolicyProposalEnvelope [E,M,1]
```

It does not recapture lifecycle evidence or execute proposals. `EventPolicyDecisionBundle` remains unchanged and is retained by exact object identity.

## 5. Per-agent subset and bypass semantics

For each agent `i` under the frozen `share_param=false` architecture:

```text
valid_env_indices_i = where(decision_valid_mask[:, i, 0])
K_i = len(valid_env_indices_i)
```

Only `obs[:,i]`, historical `available_actions[:,i]`, RNN placeholders, and masks at those canonical indices are passed to `actor_i.get_actions`. Call records retain the agent ID, exact canonical env-index tuple, and subset batch size.

When `K_i == 0`, `get_actions` is skipped completely. There is no zero-batch categorical call. Forced continuation and forced-noop rows never reach an actor, including through a one-action mask or a later overwrite.

Before inference, the collector validates that each DVM row is a `POLICY_DECISION_ROW`, exposes noop plus at least one legal task, and has I2's `-1` invalid forced-ID sentinel. It validates the two forced row forms against I2's masks and forced IDs without rederiving lifecycle state.

## 6. Fixed action/logprob scatter

The envelope always contains:

```text
action_ids       [E,M,1] int64
runner_actions   [E,M,1] float32
action_logprobs  [E,M,1] float32
```

Policy rows receive the actor's original discrete sample and exact behavior logprob at their canonical env/agent coordinate. Scatter uses the saved env indices, so compact subset index `k` cannot be confused with env index `e`.

Forced rows are initialized from I2 `forced_action_id` and never overwritten by actor output:

```text
FORCED_CONTINUATION_ROW: owned task ID
FORCED_NOOP_ROW:         raw noop ID N
```

The collector rejects a wrong tuple arity, batch/column/RNN shape mismatch, wrong device, non-integral or out-of-range discrete action, masked-out action, and non-finite action/logprob/RNN value. Policy samples are validated against the exact historical available-action tensor used for that call; there is no automatic noop correction.

## 7. Forced-row logprob sentinel

The canonical forced-row storage sentinel is `0.0`. It is storage encoding only and is jointly disambiguated by:

```text
decision_valid_mask == false
policy_proposal_present_mask == false
forced_row_mask == true
row_kind != POLICY_DECISION_ROW
```

The sentinel is not behavior-policy evidence, a valid PPO old logprob, or evidence that an actor sampled the deterministic route. Excluding these rows from evaluate-actions, ratios, entropy, losses, and HAPPO factor math remains B2-I3b work.

## 8. EventPolicyProposalEnvelope schema

`EventPolicyProposalEnvelope` is factory-only and frozen. It retains:

```text
schema/profile/collector identity
exact EventPolicyDecisionBundle reference
exact EventPolicyEvidenceSnapshot reference
exact EventPolicyEvidenceIdentityV2 reference
exact I4-2 proposal-source binding reference
P2 publication / episode / transition / OPEN identity chain through I2
action_ids [E,M,1]
runner_actions [E,M,1]
action_logprobs [E,M,1]
original_policy_proposal_ids [E,M,1], -1 on forced rows
policy_proposal_present_mask [E,M,1]
decision_valid_mask [E,M,1]
row_kind [E,M]
forced_action_id [E,M,1]
sampled_policy_row_mask [E,M,1]
forced_row_mask [E,M,1]
next_rnn_states [E,M,R,H]
per-agent subset call records and immutable provenance
```

Public tensor properties return detached contiguous clones. Mutating a returned action, logprob, mask, observation, or available-actions tensor does not mutate sealed storage. The envelope has no setter or later effective-assignment substitution path.

## 9. Original proposal/logprob and conflict preservation

For a policy row:

```text
stored action = original stochastic actor proposal
stored old logprob = that actor distribution's original behavior logprob
```

No resolver winner, arbitration result, M1 request, B1 artifact, current P2 owner, or controller target can replace either field. A fixture makes two policy rows sample the same task and proves both proposals and their distinct logprobs remain present. I3a neither chooses a winner nor converts a conflict loser to noop.

`original_policy_proposal_ids` is `-1` on forced rows, so deterministic routing remains distinguishable from an actor proposal even though `action_ids` stays fixed-shape for HARL-facing transport.

## 10. Exact decision-bundle and historical bindings

The binding chain is retained without rebind:

```text
I0 EventPolicyEvidenceIdentityV2
  -> exact I1 EventPolicyEvidenceSnapshot
  -> exact I2 EventPolicyDecisionBundle
  -> exact I3a EventPolicyProposalEnvelope
```

A numerically equal replacement decision bundle is rejected. The envelope exposes historical actor observations and available actions only from the bound I2/I1 evidence; it does not accept later replacements. Stale validation/discard/retry orchestration is intentionally not implemented in I3a.

## 11. Slot-aligned actor storage

`EventPolicyActorSlotStorageV2` is a repo-local composition boundary, one instance per actor. It owns:

```text
obs                    [T+1,E,O]
available_actions      [T+1,E,N+1]
decision_valid_masks   [T+1,E,1]
active_masks           [T+1,E,1]
action_ids             [T,E,1]
action_logprobs        [T,E,1]
exact decision-bundle reference per state slot
```

Creation initializes slot zero from the exact current decision bundle. For transition slot `t`, insertion requires an envelope bound to the same exact bundle already stored at `t`, writes its original action/logprob at `t`, then writes the returned next bundle's obs/available-actions/DVM at `t+1`.

Therefore future training views can align:

```text
obs[:-1]
available_actions[:-1]
decision_valid_masks[:-1]
actions[:]
old_logprobs[:]
```

The next bundle cannot overwrite the historical action mask at `t`. Shifted insertion, wrong current envelope, repeated slot insertion, and wrong next-slot identity fail closed.

## 12. active_masks separation and feed-forward boundary

`active_masks` has independent storage and is never assigned from DVM. I3a defines no `active_mask AND DVM` policy-loss expression; that learner meaning belongs to B2-I3b.

The frozen feed-forward/EP/HAPPO configuration is preserved. Installed actor APIs still receive required RNN and mask arguments on policy subsets. For forced rows the actor is not called, and their existing feed-forward-compatible RNN placeholder is copied unchanged into the envelope's next-RNN tensor. No recurrent redesign was introduced.

## 13. Mixed and zero-valid behavior

The mixed fixture uses `E=4`, `M=3` with policy, continuation, and forced-noop rows in the same batch. Exact actor subset sizes are:

```text
agent 0: 2, canonical env indices [0,3]
agent 1: 1, canonical env index  [1]
agent 2: 0, no actor call
```

All fixed `[E,M,1]` fields remain populated. Agent 2's output consists entirely of I2 forced route IDs and sentinel logprobs; no empty-distribution call, NaN, or dimension collapse occurs.

## 14. No lifecycle recapture and no proposal execution

Static and dynamic oracles establish that I3a does not read P2, OPEN, assignment-problem feasibility/cost, robot/task lifecycle, ownership, or failed-pair backing after the I2 bundle is sealed. Mutating those source objects after sealing changes neither the DVM subset nor historical evidence and records no new problem reads.

The new module does not import or call the I4-2 proposal adapter, arbitration, resolver, M1/B1, environment step, final-P2 capture, Ak, controller, loss, GAE, factor, or optimizer path. The proposal envelope is future routing evidence only; proposal collection is not proposal execution.

## 15. Installed HARL API/component audit

The installed interface used by the collector is:

```text
actor.get_actions(obs, rnn_states_actor, masks,
                  available_actions=None, deterministic=False)
  -> actions, action_log_probs, next_rnn_states_actor
```

The existing base runner collects over full `E` and has no DVM-aware subset boundary. Installed actor buffers store state-slot fields at `[T+1]` and transition actions/logprobs at `[T]`, but have no independent `decision_valid_masks` field. B2-I3a therefore adds repo-local composition and does not patch site-packages.

A synthetic CPU check instantiated three real installed `HAPPO` actor components with Box observations and Discrete actions, then exercised subset sizes `[2,1,0]`. Every selected action was legal under its historical mask. Actor parameters remained bitwise unchanged, optimizer state remained empty, and no optimizer step or rollout loop ran. The same check passed in the fixture's normal and `-I -B` modes.

## 16. Verification matrix

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
Python 3.10.20
```

| Suite | normal | `-I -B` |
|---|---:|---:|
| B2-I3a collector/storage/envelope | `15/15 PASS` | `15/15 PASS` |
| B2-I2 legality/DVM/decision bundle | `17/17 PASS` | `17/17 PASS` |
| B2-I1 evidence/current projectors | `14/14 PASS` | `14/14 PASS` |
| B2-I0 no-tick reconciliation | `13/13 PASS` | `13/13 PASS` |
| historical v1 schema | `9/9 PASS` | `9/9 PASS` |
| Phase-A default-off identity | `16/16 PASS` | `16/16 PASS` |
| profile contract | `16/16 PASS` | `16/16 PASS` |

The 15 I3a oracles cover subset call indices/counts, mixed/zero-valid rows, fixed scatter and dtypes, original proposal/logprob and same-task conflicts, forced routing/sentinel semantics, historical-mask legality, malformed outputs, exact identity rejection, immutability, slot-0 and `t/t+1` alignment, active-mask independence, static/dynamic no-recapture, no I4-2/loss execution, a real installed-HAPPO synthetic component check, protected hashes, and canonical isolated import.

Final `py_compile` for the new module and fixture: `2/2 PASS`. Final hygiene results are recorded in section 18.

## 17. Protected hashes

The fixture checks 13 frozen repo anchors, including I2/I1/I0, profile/default-off, wrapper/training, facade/I4-2, lifecycle/P2, and environment integration. It also checks six installed HARL files:

```text
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

New artifact hashes before documentation-only finalization:

```text
assignment_event_actor_collection.py
  3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45
test_assignment_phase_b2_i3a_dvm_actor_collection_storage_proposal_envelope_pure.py
  ee579cf054543432307d4def63c160f513c6926a9ddc5f8348c1380f2b306643
```

## 18. Hygiene and non-execution statement

Final checks:

```text
py_compile:                   2/2 PASS
git diff --check:             PASS
untracked whitespace scan:   PASS
temporary bytecode cleanup:  COMPLETE
unexpected checkpoint/log:   NONE
```

No Isaac, AppLauncher, environment rollout, training loop, playback, evaluation, optimizer step, checkpoint save/load, or public learned-policy step was run. Installed HARL was read and used only as an allowed synthetic component; it remains unchanged.

## 19. Readiness and remaining blockers

B2-I3a completion does not establish `POLICY_INTERFACE_READY`. The following remain blocked and not authorized:

- B2-I3b policy evaluate-actions, entropy, PPO ratio, decision-valid loss masking, and full-index HAPPO sequential-factor accounting;
- B2-I4 authoritative pre-reset terminal critic sidecar;
- B2-I5a terminal historical learner/value/buffer transport;
- B2-I5b TIME_LIMIT GAE/ValueNorm semantics;
- B2-I6 dormant public learned-policy event route;
- later B2-V1/V2 and runtime-readiness gates.

External path/local/retry producers and all eleven numeric TBDs remain deferred. Transformer/GNN/Set Transformer, variable cardinality, arbitrary-cardinality checkpoints, training, playback, and evaluation remain out of scope.

```text
next proposed slice: B2-I3b — full-index PPO/HAPPO accounting
status: NOT AUTHORIZED
```

## 20. Final classification

```text
classification:
  PHASE-B2-I3A-DVM-AWARE-ACTOR-COLLECTION-STORAGE-AND-PROPOSAL-ENVELOPE-COMPLETE-AWAITING-GPT-REVIEW
B2-D:
  REVIEW PASS / FROZEN
B2-I0:
  REVIEW PASS / CLOSED
B2-I1:
  REVIEW PASS / CLOSED
B2-I2:
  REVIEW PASS / CLOSED
B2-I3a:
  IMPLEMENTED / AWAITING GPT REVIEW
tests:
  PASS
Isaac:
  NOT RUN
HARL component:
  SYNTHETIC COLLECTION ONLY / PASS
training/playback/evaluation:
  NOT RUN
optimizer:
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

Stop here pending GPT independent review and explicit user authorization. Do not begin B2-I3b.
