# Phase B1W-I4-D-R — Wrapper Facade and Proposal-to-Effective-Commit Integration Targeted Design Revision

This is the targeted in-place revision of the B1W-I4-D design. It closes only
the two review conditions concerning conflict feasibility/cost ordering and
multi-row terminal ACK atomicity. WR-C, W-T1, ACK-A, P2/Ak authority, action
semantics, M1 batching, default-off isolation, and all implementation gates are
unchanged.

## 1. Design verdict

```text
classification:
  PHASE-B1W-I4-D-R-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

parent B1W-I4-D:
  CONDITIONAL ISSUES RESOLVED

wrapper architecture:
  WR-C
  existing AssignmentHarlWrapper remains the HARL adaptation boundary
  exact event branch delegates to one B-private EventAssignmentRuntimeFacade

authority:
  current P2 in the retained event runtime domain is the only ownership truth
  B1 production claim is the only proposal-driven ownership mutation
  Ak-bound P2 is the only controller assignment source

terminal transport:
  W-T1 + ACK-A
  wrapper owns synchronous capture -> bounded immutable copy -> atomic batch exact ack
  learner consumption is a later and separate lifetime

conflict candidate eligibility:
  EXPLICIT-FEASIBILITY-FIRST
  cost is ranking data only and cannot make an infeasible pair eligible

multi-row terminal acknowledgement:
  ATOMIC_BATCH_EXACT_ACK
  full-batch validation -> one terminal-slot publication -> exact stored artifacts

WR-C / W-T1 / ACK-A: preserved
current P2 authority: preserved
Ak controller source: preserved
legacy resolver event route: bypassed
infeasible candidate re-entry: prohibited
partial successful ACK: impossible

Python source: unchanged
Isaac / AppLauncher / HARL: not run
training / playback / evaluation: not run
B1W-I4 implementation: not entered
runtime readiness: blocked
commit: none
```

This design is complete because the current repository provides all required
linearization points. The event route can bypass the stateful legacy resolver,
batch task-disjoint new claims through the existing W2/B1/C2 transaction, let
O1 bind final P2 to Ak, and synchronously move exact terminal evidence to a
bounded wrapper-owned historical value before one atomic batch acknowledgement.
No second Store, ownership mirror, resolver authority, fence, terminal registry,
or poison path is required.

The design does **not** claim runtime readiness. Event actor/shared observation
construction, event masks/DVM, runner forced-row behavior, the full pre-reset
critic sidecar, learner-buffer insertion, and production entrypoint activation
remain implementation/review work.

## 2. Scope and protected boundaries

This phase was a read-only source audit plus documentation update. It did not
modify Python, tests, configuration, YAML, wrapper/runtime/resolver/HARL source,
or readiness gates. It did not run Python tests, Isaac, AppLauncher, HARL,
training, playback, or evaluation.

The audit preserved these already-closed invariants:

- one retained event domain and one `LifecycleStateStore` writer;
- current P2 as the authoritative publication;
- G2 per-env terminal claim exclusion and R3 global next-step exclusion;
- C2 batched independent initial claims;
- S4 split physical/reset admission, W2 claim envelopes, and F1 outside P2;
- exact Ak capture before control construction;
- exact terminal artifact identity and exact-key acknowledgement;
- default-off isolation of all four existing profiles;
- no new assignment-tick clock.

## 3. Audited current reality

### 3.1 Current wrapper reset graph

```text
AssignmentIsaacLabEnv.reset()
  -> AssignmentHarlWrapper.reset()
     -> raw wrapped env.reset()
     -> unwrapped.get_assignment_problem()
     -> wrapper-local diagnostic reset
     -> legacy AssignmentLifecycleResolverRuntimeAdapter.reset_envs()
     -> wrapper lifecycle episode-generation increment
     -> wrapper legacy lifecycle snapshot capture
     -> wrapper actor observation augmentation
     -> concat actor observations into shared_obs
     -> wrapper legacy/lifecycle available-actions construction
     -> return (obs, shared_obs, available_actions)
```

The current wrapper directly calls the raw environment and always constructs a
legacy resolver adapter. Its profile configuration requires the exact
`ResolvedExistingAssignmentProfile` identity, so it cannot currently construct
an exact event branch.

### 3.2 Current wrapper step graph

```text
HARL actor action tensor
  -> AssignmentHarlWrapper.step()
     -> get pre-step physical assignment problem
     -> build pre-step available_actions
     -> decode raw IDs into proposal[E,M], noop -> -1
     -> legacy resolver.resolve_pre_step(proposal)
        -> legacy effective_assignment[E,M]
        -> legacy resolver mutates its own active/owner/pair state when enabled
     -> assignment_to_env_actions(effective_assignment)
     -> raw wrapped env.step(continuous actions)
     -> get post-step physical assignment problem
     -> stack rewards and dones
     -> update wrapper-local reward/attempt/cooldown diagnostics
     -> legacy resolver.observe_post_step(...)
     -> reset wrapper-local rows selected by all-agent done
     -> capture post-step legacy lifecycle snapshot
     -> augment returned observations
     -> build current shared_obs and available_actions
     -> return six-tuple
```

The current `last_effective_assignment` is therefore a legacy resolver output,
not event-domain P2. That name may remain on the four existing routes but is not
an event authority and cannot be reused as such.

### 3.3 Current environment/O1 graph

The exact event environment already requires the same retained domain and its
exact admission-validation port. `_pre_physics_step()` validates active Ak;
`_get_dones()` finalizes the exact-Ak lifecycle transition before autoreset;
`_reset_idx()` rebuilds the episode through the event environment port.

O1 currently provides:

```text
read_current()
commit_deterministic_initial_claim(...)
reset_environment(...)
step_environment(...)
capture_pending_terminal_artifacts()
acknowledge_terminal_artifact(exact_key)
```

`step_environment()` begins S4 admission, derives the controller assignment
only from the admitted publication, builds continuous actions, calls the real
environment, and completes Ak/Wnext after the outer return. This is the correct
control-order primitive and must not be duplicated in the wrapper.

### 3.4 Current HARL boundary

The repo-local `AssignmentIsaacLabEnv` expects the wrapper reset three-tuple and
step six-tuple. It currently discards the wrapper `info` and returns fresh empty
per-env/per-agent infos. The installed HARL runner then inserts the returned
`share_obs` directly into the critic buffer; on an autoreset terminal step that
value is the new-episode current state, not a final pre-reset historical state.

This does not require changing installed HARL core. Future terminal learner
transport and forced-row sampling can be implemented in the repo-local
`AssignmentIsaacLabEnv` / `AssignmentOnPolicyHARunner` specialization. They are
deferred and remain readiness blockers.

### 3.5 Feasibility and cost are separate current inputs

The environment computes `cost_matrix` from scanner/viewpoint distance,
publishes `feasible_mask` independently, and derives
`available_mask = feasible_mask & ~viewpoints_covered`. The RL interface builds
its action mask from `available_mask`, not from cost. The legacy resolver also
checks availability and the supplied feasibility mask before adding a proposal to
`pending_claims`; only then does `_choose_claim_winner()` rank the surviving
candidates by finite cost and robot ID.

Consequently, feasibility is not derivable from cost. A pair can be explicitly
infeasible while retaining a finite geometric distance. Defensively, an
explicitly feasible candidate may also carry a non-finite cost at the resolver
boundary because no current contract couples feasibility to finiteness. The
event adapter must therefore preserve the source ordering:

```text
proposal
  -> P2 structural legality
  -> explicit current physical feasibility
  -> eligible candidate set
  -> cost-based conflict ranking within that set only
```

The no-finite-cost fallback is totality for an already explicitly feasible
candidate set. It is never an eligibility fallback and cannot reintroduce a
candidate rejected by structural or physical feasibility checks.

### 3.6 Existing terminal authority supports atomic batch ACK

The coordinator already protects one `_terminal_slots` dictionary with one
`_publication_lock`. Capture validates the designated terminal consumer and
returns the exact stored artifacts in env-ID order. Existing single-key ACK,
under that same lock, validates coordinator health, consumer capability, exact
key type, slot presence, and exact env/episode/transition identity; it then
publishes one replacement slot dictionary and returns the exact stored artifact.
R3 observes the same slot dictionary under the same lock.

Therefore a future batch helper needs no second lock, registry, cache, clock, or
authority. It can validate every requested row and prepare both the exact return
tuple and full replacement dictionary before one publication to
`_terminal_slots`. Existing single-key ACK remains unchanged for direct and
diagnostic use.

## 4. Architecture choice: WR-C

The chosen structure is:

```text
formal assignment entrypoint / composition root
  owns resolved exact event profile
  constructs one retained event domain
  passes only domain + validation port into gym environment construction
  constructs O1 from the raw environment and narrow same-domain ports
  constructs one EventAssignmentRuntimeFacade from O1
  injects only that facade into AssignmentHarlWrapper's exact event branch

AssignmentHarlWrapper
  existing profiles -> unchanged current path
  exact event profile -> EventAssignmentRuntimeFacade only
```

The facade is B-private and profile-discriminated. It is not a new authority.
It owns proposal interpretation, pure conflict arbitration, B1 claim submission,
O1 sequencing, terminal handoff copying, and immutable diagnostics. It must not
own a Store, current ownership tensor, fence state, terminal slots, poison state,
generation clock, lifecycle derivation, scheduler, or resolver lifecycle.

The wrapper may retain the facade object, but it must not receive the full
domain, raw B1 port, raw terminal consumer capability, raw fence, Store,
coordinator, or O1 internals. The composition root proves exact profile/domain
identity once and injects the already-bound facade.

## 5. Capability graph

| Component | May hold/use | Must not hold/use |
|---|---|---|
| composition root | exact resolved profile; retained domain; env construction args; O1 construction ports; event facade construction | lifecycle mutation outside domain transactions |
| retained domain | Store, coordinator, P2, W2/F1, G2/R3, terminal slots, narrow ports | wrapper, policy, scheduler, HARL runner |
| O1 | exact same-domain current/claim/admission/reset/terminal capabilities, including the future narrow batch-ACK method; raw synchronous env callable | Store writer, raw fence writer, ownership mirror, resolver, scheduler, policy, terminal cache |
| event proposal adapter inside facade | immutable P2 read; proposal-source identity; physical cost/feasibility snapshot; pure arbitration rule | mutation, Store, terminal slots, legacy resolver state |
| event facade | O1 public-private surface; bounded immutable diagnostics/terminal copy result | domain object, raw ports, second P2, raw env calls |
| wrapper exact event branch | event facade; action decoder; HARL output/cache adaptation | raw event env reset/step; legacy resolver; domain/ports; lifecycle mutation |
| wrapper existing branches | current raw env, resolver, controller, observation/mask path | event facade/domain capabilities |
| environment | event environment port and exact validation port | terminal consumer, policy proposals, wrapper/HARL state |
| legacy resolver | existing-route proposal/effective lifecycle behavior | any event-route ownership or P2 mutation |
| terminal transport owner | wrapper-owned immutable historical step payload after copy; facade-mediated O1 batch ACK | raw terminal consumer capability, terminal slot authority, P2, R3/G2, lifecycle mutation |

## 6. Target event reset call graph

```text
AssignmentHarlWrapper.reset() [exact event branch]
  -> EventAssignmentRuntimeFacade.reset_environment(...)
     -> O1.reset_environment(...)
        -> begin_full_reset_admission()
        -> raw env.reset(...)
           -> environment validates reset entry
           -> environment episode_rebuild(...)
           -> physical reset
           -> publish canonical reset P2
        -> commit_successful_return(reset admission)
        -> Wnext OPEN
     -> read exact current P2
     -> verify reset publication is nonterminal/current
     -> construct current event actor/shared/mask snapshot requirement
  -> clear/rederive event-route wrapper caches from current P2
  -> return (post-reset actor obs, current shared_obs, available_actions)
```

The exact event branch never calls raw `env.reset()` itself. Existing routes
continue to do exactly what they do today.

## 7. Target event step call graph

```text
HARL-facing action batch
  -> wrapper decodes raw IDs but preserves raw proposal diagnostics/log-prob link
  -> EventAssignmentRuntimeFacade.step(proposal batch, bound decision identity)
     -> read current P2
     -> verify proposal source identity/generations are still current
     -> classify rows as continuation / new-claim candidate / noop / invalid
     -> filter P2 structural legality
     -> filter explicit current physical feasibility, independently of cost
     -> arbitrate each same-task eligible set by finite cost then robot ID
     -> if at least one new claim survives:
          build one task-disjoint C2 request for selected env rows
          O1 submits one W2-bound B1 production claim batch
          receive one EffectiveAssignmentCommitArtifact
        else:
          no B1 request and no Store-version increment
     -> read final current P2
     -> O1.step_environment()
        -> begin physical-step admission
        -> Ak captures final P2
        -> derive controller assignment from admitted P2 only
        -> assignment_to_env_actions(raw env, Ak assignment)
        -> raw env.step(actions)
           -> exact-Ak environment lifecycle finalization
           -> optional terminal/autoreset
        -> outer env return
        -> complete Ak and open Wnext
     -> capture pending terminal artifacts
     -> make and validate the full bounded immutable historical copy
     -> build the canonical env-ID-ordered tuple of exact captured keys
     -> O1 atomically batch-acknowledges the full tuple
        -> validate the entire batch under the terminal publication lock
        -> publish one replacement terminal-slot dictionary
        -> return the exact stored artifacts in env-ID order
     -> read current P2 after any autoreset
     -> return facade step result
  -> wrapper constructs current actor obs/current shared_obs/mask
  -> wrapper exposes copied terminal history on its private step-result side channel
  -> return HARL six-tuple
```

Capture/copy/ack occurs after outer env return, Ak completion, and Wnext OPEN,
and before the next policy inference or physical admission.

## 8. Answers to Q1–Q20

| Question | Frozen answer |
|---|---|
| Q1 | Yes, but only indirectly under WR-C: the event wrapper holds one `EventAssignmentRuntimeFacade`, which encapsulates O1. It does not receive O1 ports or internals. |
| Q2 | No on the exact event branch. Reset/step must go through the facade/O1. Yes, unchanged, on the four existing branches. |
| Q3 | A policy output is a proposal bound to the last emitted authoritative decision snapshot. It is neither ownership nor controller input. Ordinary no-tick forced rows are not policy proposals. |
| Q4 | Only on existing routes as a legacy diagnostic name. A legacy resolver output must never be called the authoritative event effective assignment. Event effective state means P2 after any B1 commit. |
| Q5 | Classify against current P2, discard continuations/noops/invalids, arbitrate duplicate task candidates, create one selected-env/task-disjoint `[K,M]` request with `-1` for nonclaiming robots, then prepare+commit one W2-bound B1 transaction. |
| Q6 | Same owned task is continuation. Other task is rejected/deferred and cannot mutate B1. The current authoritative task continues into Ak. |
| Q7 | Frozen schema decides this: for `EXECUTING`, noop is illegal, not continuation; current-task action is continuation. For `NEEDS_ASSIGNMENT`, noop means no new claim. Waiting/unavailable use deterministic noop storage only. |
| Q8 | Before B1, inside the facade's pure proposal adapter: first reject candidates failing P2 structural legality, then reject candidates failing explicit current physical feasibility. Cost never determines eligibility. Within the remaining same-task set, choose minimum finite cost then lowest robot ID; only if that already-feasible set has no finite cost, choose its lowest robot ID. An infeasible candidate cannot re-enter through fallback. |
| Q9 | Only winning legal candidates enter one B1 production batch. The returned commit artifact is immutable history; the subsequently read P2 is the effective current state. |
| Q10 | Same-task continuation, noop/no-claim, waiting/unavailable task proposals, executing switch proposals, illegal/covered/owned/failed/infeasible/stale proposals, and arbitration losers do not change P2. |
| Q11 | The facade never builds control from proposal or commit artifact. It calls O1 only after final P2 is published; S4/Ak captures that P2 and O1 derives control from the admission. |
| Q12 | After real `env.step` has returned, exact Ak has completed, and Wnext is OPEN; before next actor inference and before wrapper return completes. |
| Q13 | First into a bounded immutable wrapper-owned private step payload. Future repo-local env/runner transport copies the terminal critic sidecar into the learner buffer before the new-episode initial row. |
| Q14 | ACK-A uses `ATOMIC_BATCH_EXACT_ACK`: capture, complete and validate the full bounded immutable copy, validate every exact key under the one terminal publication lock, remove all addressed slots with one slot-map publication, return the exact stored artifacts, then return from the facade. Any row failure rejects the whole batch and removes none. Ack means runtime slot lifetime complete, not learner consumption. |
| Q15 | From the current post-autoreset environment observation, augmented only with current post-reset P2. Never from the terminal artifact. |
| Q16 | From an authoritative pre-reset terminal sidecar associated with the exact terminal artifact/key. It enters via the wrapper-private historical payload and a future repo-local runner adapter, not via current returned `share_obs`. Current artifact has no full physical critic sidecar, so producing that sidecar remains a deferred prerequisite. |
| Q17 | P2 ownership persists. Ordinary no-tick executing rows force the current task; assignment-tick same-task proposals are continuation. Neither path calls B1 or increments Store version. |
| Q18 | Reuse the decoded ID convention and the resolver's ordered semantic: explicit availability/feasibility filters first, then deterministic finite-cost/robot-ID conflict ranking. Bypass the stateful resolver object, its active/owner/pair state, pre/post lifecycle mutation, cooldown/release semantics, and its event authority. |
| Q19 | Exact type/profile dispatch occurs before event facade use. The existing four profiles receive no event domain/facade and retain the current reset, step, resolver, controller, observation, mask, diagnostics, and output behavior. |
| Q20 | Implement I4-1 facade/composition/reset/no-claim continuation; I4-2 pure structural/explicit-feasibility filtering, conflict arbitration, and B1 batch; I4-3 terminal capture/copy/atomic-batch-exact-ACK wrapper transport; I4-4 bounded integration smoke. Event observation/mask/forced-row and learner critic transport stay separately gated. |

## 9. Proposal interpretation table

`current task` below means the unique active task owned by an `EXECUTING`
robot. It is structurally absent for every other robot state.

| Robot P2 state | Action | Interpretation | B1 mutation? | P2 change? | Controller source |
|---|---|---|---|---|---|
| `EXECUTING` | current task | explicit `CONTINUE_EXISTING`; preserve active ownership | no | no | final Ak-bound P2 current task |
| `EXECUTING` | other task | invalid switch/reassign proposal; diagnostic rejection; current work continues | no | no | final Ak-bound P2 current task |
| `EXECUTING` | noop | illegal by frozen event action contract; fail/reject proposal diagnostic, never reinterpret as release or claim | no | no | final Ak-bound P2 current task |
| `NEEDS_ASSIGNMENT` | current task | not applicable because no active owned task; any contradictory P2 is invariant failure | no | no | final Ak-bound P2 |
| `NEEDS_ASSIGNMENT` | other task | new-claim candidate only after P2 structural legality and explicit current physical-feasibility filters pass; cost ranks eligible conflicts only. Current window must be OPEN and the row not terminal-blocked; otherwise reject | zero or one batched commit | only if winner commits | final post-commit Ak-bound P2 |
| `NEEDS_ASSIGNMENT` | noop | no claim this opportunity | no | no | final Ak-bound P2, normally no task for this robot |
| `WAITING_FOR_TASK` | current task | not applicable; owned-current would violate state invariant | no | no | final Ak-bound P2 |
| `WAITING_FOR_TASK` | other task | invalid; wrapper cannot promote the robot to needs | no | no | final Ak-bound P2 |
| `WAITING_FOR_TASK` | noop | remain waiting; deterministic forced encoding when no decision | no | no | final Ak-bound P2 |
| `UNAVAILABLE` | current task | not applicable and invariant-invalid | no | no | final Ak-bound P2 |
| `UNAVAILABLE` | other task | invalid; no claim and no wrapper-side recovery | no | no | final Ak-bound P2 |
| `UNAVAILABLE` | noop | only legal deterministic storage encoding; not a policy proposal on an ordinary row | no | no | final Ak-bound P2 |

### 9.1 Noop and continuation

The current legacy resolver treats noop during execution as Contract-C
continuation. The frozen exact event schema does not. Its ordinary no-tick rule
is `current_task_only_and_noop_illegal`; nonexecuting rows use a deterministic
noop-only storage encoding. Consequently:

- exact event `EXECUTING + current task` is continuation;
- exact event `EXECUTING + noop` is an illegal action if it reaches the facade;
- exact event `NEEDS_ASSIGNMENT + noop` is a legal no-claim choice when the row
  is a real decision opportunity;
- forced ordinary rows are not proposals and do not carry policy log-probability.

This preserves the earlier action contract and prevents a hidden semantic fork.

## 10. Arbitration and B1 mapping

### 10.1 Pure boundary

Arbitration consumes only captured immutable inputs:

```text
proposal source P2 identity/generations
P2 task/robot/ownership/failed-pair state
explicit physical availability/feasibility snapshot
separate physical cost snapshot
decoded proposal[E,M]
decision/row classification
```

It produces a pure resolution record containing the original proposal,
structural and feasibility rejection reasons per robot, winning task-disjoint
candidates, loser diagnostics, and the exact source identity. It has no mutation
capability.

### 10.2 Candidate eligibility rule

The frozen model is `EXPLICIT-FEASIBILITY-FIRST`. For each proposed
`NEEDS_ASSIGNMENT` pair, the pure adapter applies this exact order:

1. verify proposal/source identity and P2 structural legality, including robot
   state, task availability/ownership, cumulative failed-pair state, and the
   already-authoritative G2/W2 envelope conditions;
2. require `feasible_mask == true` from the separate current physical
   feasibility snapshot captured with the decision inputs; `available_mask` may
   additionally provide a producer-consistency rejection but cannot replace P2
   structural truth or `feasible_mask` physical truth;
3. only after both filters pass, admit the pair to the eligible candidate set;
4. use cost only when ranking a same-task conflict within that eligible set.

`feasible == false` with finite cost is rejected. `feasible == true` with
`inf`/`NaN` remains eligible but non-finite for ranking. A transient physical
infeasibility/path-validity result is a proposal rejection only; the facade has
no authority to turn it into cumulative `failed_pair` history.

Prefilter survival is not a promise of mutation. B1 remains authoritative and
may still reject a stale P2/source generation, closed or changed W2 window, G2
terminal exclusion, or any other production transaction precondition.

### 10.3 Conflict cost rule

For each env/task with multiple structurally legal and explicitly feasible
`NEEDS_ASSIGNMENT` candidates:

1. form the finite-cost subset of the already eligible candidates;
2. if it is nonempty, choose its lowest current cost and break equal cost by
   lowest global robot ID;
3. if it is empty, choose the lowest global robot ID from the already eligible
   candidate set;
4. mark all other candidates as conflict losers with no effective claim.

The fallback never scans rejected candidates, so an infeasible candidate cannot
re-enter arbitration. This reuses the current resolver's ordered filtering and
deterministic ranking semantics, not its stateful object. Calling its private
`_choose_claim_winner()` through a live resolver is forbidden because that would
expose a second lifecycle authority.

### 10.4 M1 batch construction

One wrapper action batch maps to zero or one commit artifact:

```text
selected_env_ids[K] = env rows with >=1 winning new claim
requested_task_by_robot[K,M] = winner task IDs, otherwise -1
```

The adapter verifies uniqueness per env, current P2 identity, B1 legality, and
OPEN window immediately before prepare. W2 binds the exact B1 request to the
window; C2 commits all independent winners atomically. Continuation and rejected
robots remain `-1` in the claim request but remain fully represented in the
proposal/effective diagnostics.

If `K == 0`, no request is prepared, no artifact is created, and P2/store
version must remain unchanged. Sequential M2 commits are not used.

### 10.5 Proposal/effective diagnostics

The event route records separately:

- raw policy action ID and decoded proposal;
- proposal-present versus forced-nondecision row;
- proposal-source P2 identity and generations;
- structural rejection, explicit-feasibility rejection, and conflict
  winner/loser;
- optional B1 commit artifact identity and requested/effective claim rows;
- final P2-derived effective assignment admitted by Ak;
- proposal-to-effective difference without rewriting the actor action or its
  log probability.

The actor loss remains attached to the sampled proposal. No synthetic
`logprob(effective_task)` is allowed.

## 11. Stale proposal rule

The wrapper caches the identity of the authoritative decision snapshot from
which it built the actor observation/mask. This is a read-only association, not
an ownership cache. On step entry, the facade requires that identity and its
env/episode/transition/publication generations still match current P2. A
mismatch fails closed before B1 preparation or Ak admission; the proposal is
never silently rebound to newer P2.

W2 then independently prevents a prepared request from crossing to another
window. These two checks cover proposal staleness and claim-envelope staleness
without a new clock.

## 12. Terminal transport state machine

This is a synchronous transport workflow, not lifecycle authority:

| Transport state | Meaning | Allowed next operation | Authority effect |
|---|---|---|---|
| `NO_TERMINAL` | capture returns `()` | build current outputs and return | none |
| `CAPTURED_NOT_COPIED` | exact slot artifact identities were captured; R3 remains active | copy all required fields into bounded immutable step payload; failure aborts without ack | none |
| `COPIED_NOT_ACKED` | no-alias payload is complete and key/reason/done/generation checks pass for the full tuple | submit one canonical tuple to atomic batch exact ACK | none |
| `ATOMIC_ACKED` | all addressed runtime slots were removed by one slot-map publication; returned objects are the exact stored artifacts | expose private payload; allow later physical admission | slot lifetime only; no P2 change |

The normal implementation performs all four states inside one facade/wrapper
call. It must not persist a second terminal registry. A copy/validation failure
must not acknowledge the slot; the call fails with R3 still protecting the next
physical step. Partial successful acknowledgement is impossible: validate/copy
the full captured tuple first, then call one batch operation.

The future coordinator operation
`_acknowledge_terminal_batch(keys, consumer_capability)` is frozen as follows:

1. acquire the existing terminal publication lock and validate coordinator
   health plus the exact designated terminal-consumer capability once;
2. require an exact tuple of exact terminal-transition keys, with unique env
   rows and no duplicate key;
3. for every key, require an occupied slot and exact
   env/episode-generation/transition-generation equality; any foreign, stale,
   missing, duplicate, or wrong key rejects the whole batch;
4. before mutation, prepare the env-ID-ascending tuple of exact stored artifact
   identities and a full replacement dictionary with all addressed slots
   removed;
5. after every validation and preparation succeeds, perform exactly one
   publication assignment to `_terminal_slots`, then return the prepared exact
   artifact tuple.

Any expected prevalidation or copy/preparation failure performs no publication,
removes no slot, and leaves R3 intact. The empty tuple is a legal no-op returning
`()`, after health/capability validation; the facade normally avoids calling it
when capture is empty. A successful batch changes terminal-slot occupancy only:
P2, Store version, W2, generations, and poison state do not change.

There is one mutation point and no rollback protocol. The operation prepares its
return tuple before that point. If an unexpected internal failure is detected
after publication, the coordinator must fail-stop through its existing poison
authority before releasing the locked operation and must not report success.
It must not restore slots, partially report acknowledgement, or create a second
poison path.

The capability path is narrow and same-domain:

```text
coordinator._acknowledge_terminal_batch(...)
  -> terminal-consumer port.acknowledge_terminal_batch(...)
  -> O1.acknowledge_terminal_artifacts(...)
  -> event facade after full wrapper-owned copy validation
```

The wrapper never receives the raw consumer capability. Existing single-key
`acknowledge_terminal_artifact()` remains available and unchanged for direct or
diagnostic use; the synchronous multi-row facade path must use only the atomic
batch operation.

### 12.1 Bounded copy success definition

Before ACK-A, the wrapper-owned immutable payload must preserve, without alias:

- `env_id`, `episode_generation`, `transition_generation` exact key;
- authoritative termination reason, terminated, and truncated;
- exact finalized lifecycle result/history needed by later projection;
- final pre-reset coverage and authoritative lifecycle state;
- consume token, authority receipt, and lifecycle event evidence required for
  diagnostics;
- when implemented upstream, the authoritative pre-reset centralized physical
  critic sidecar and its schema/generation binding.

The current `_TerminalHandoffArtifact.optional_sidecar` is exactly `None` and
does not yet contain the full physical centralized critic state. I4-3 may prove
artifact copy/ack, but runtime readiness cannot claim correct terminal critic
transport until a separately authorized upstream sidecar/projector supplies
that data before autoreset.

The copied payload is a historical value. It cannot participate in P2, G2, R3,
ownership, lifecycle derivation, reset, or controller construction.

## 13. Wrapper output requirements

The DirectMARLEnv five-tuple remains unchanged. The wrapper retains its existing
HARL reset/step arity. The exact event branch must satisfy:

| Output | Exact event requirement |
|---|---|
| actor next obs | current post-step observation; for done/autoreset rows this is new-episode post-reset physical state plus current post-reset P2 |
| `share_obs` | current centralized state used for the next value evaluation; terminal rows are still current post-reset here |
| reward | reward for the just-completed physical transition; proposal/effective attribution remains separate |
| done/truncated | HARL done tensor derived from environment return; authoritative reason comes from terminal artifact, not reconstruction |
| available actions | current event mask bound to the same current observation/P2; terminal historical row has no action mask |
| proposal diagnostic | original sampled action/proposal and log-probability association; forced rows marked nonproposal |
| effective diagnostic | final P2-derived Ak assignment plus optional B1 commit evidence; never a second authority tensor |
| terminal historical payload | wrapper-private immutable per-step subset keyed by env/generations; separate from actor obs/current `share_obs` |

Do not place terminal artifacts into raw environment obs, reward, terminated,
truncated, or info. The event wrapper keeps a private step side channel. A later
repo-local `AssignmentIsaacLabEnv` / runner adapter may consume/copy that side
channel into learner transport; current `_empty_infos()` is not a safe carrier.

## 14. Actor-current versus critic-historical split

```text
terminal physical transition at episode e
  -> exact pre-reset lifecycle result and future critic sidecar: HISTORY(e)
  -> internal autoreset/rebuild
  -> current publication and returned actor observation: CURRENT(e+1)

wrapper return actor obs       = CURRENT(e+1)
wrapper return share_obs       = CURRENT(e+1)
wrapper private terminal copy  = HISTORY(e)
```

The future critic-buffer adapter must insert `HISTORY(e)` at the terminal
boundary before inserting/using the new episode's initial current row. TIME_LIMIT
retains its authoritative reason/truncated flag for a later proper-time-limit
design; this phase does not define GAE or bootstrap policy.

## 15. Cache reset semantics

For exact event rows that autoreset, the wrapper/facade must clear or rederive:

- prior proposal-source identity and event decision snapshot;
- any local effective-assignment projection;
- current action-mask/observation generation association;
- previous assignment/action convenience mirrors;
- per-episode proposal/rejection/reward diagnostics not explicitly historical;
- any event-route physical-problem snapshot used for arbitration.

The replacements are derived from current post-reset P2 and current returned
environment state. The copied terminal payload remains only in the bounded
step result long enough for downstream copy. Proposal/effective/terminal
diagnostic history may be logged as immutable history but cannot seed the new
episode or create a claim.

Existing-profile cache/reset behavior is unchanged.

## 16. Worked examples

### Example A — normal continuation

```text
P2: robot0 EXECUTING, owns active task2
row: ordinary no-tick
forced action: task2 (not a sampled proposal)
classification: CONTINUE_EXISTING
B1: no request, no artifact, no Store increment
Ak: captures unchanged P2
control: task2
result: task remains active unless exact execution facts finalize/release it
```

At an assignment tick, a sampled `proposal=task2` has the same no-mutation
continuation result. A noop is not used for continuation on the exact event
route.

### Example B — new claim

```text
P2: robot0 NEEDS_ASSIGNMENT; task4 AVAILABLE/unowned; pair legal
proposal: robot0 -> task4
classification: NEW_CLAIM_CANDIDATE
arbitration: robot0 wins
B1 M1 request: selected env row, [task4, -1, ...]
commit: one EffectiveAssignmentCommitArtifact
P2: task4 CLAIMED by robot0; robot0 EXECUTING
Ak/control: final P2 task4
```

### Example C — conflict

```text
P2: robot1 and robot2 NEEDS_ASSIGNMENT; task4 AVAILABLE/unowned
proposals: robot1 -> task4, robot2 -> task4
explicit feasibility: robot1=true, robot2=true
costs: robot1=3.0, robot2=2.0
pure arbiter: robot2 winner, robot1 conflict loser
B1 M1 request: robot1=-1, robot2=task4
P2: exactly robot2 owns task4
Ak/control: robot2 task4; robot1 no task
diagnostics: both proposals preserved, winner/loser explicit
```

Equal finite costs select the lower robot ID. If both explicitly feasible
candidates instead carry `inf`/`NaN`, the finite subset is empty and the lower
robot ID wins. If robot1 is explicitly infeasible while retaining finite cost
`1.0`, it is rejected before ranking and cannot beat or re-enter against an
eligible robot2.

### Example D — executing robot proposes another task

```text
P2: robot0 EXECUTING, owns task2
proposal: task4
classification: INVALID_SWITCH_WHILE_EXECUTING
B1: no request for robot0
P2: unchanged, robot0 still owns task2
Ak/control: task2
diagnostic: proposal task4 versus effective task2
```

No release, steal, reassignment, or deferred auto-claim is invented.

### Example E — terminal step

```text
final P2 admitted to Ak
  -> control built only from Ak P2
  -> environment finalizes terminal result and internally rebuilds episode
  -> env.step returns post-reset observation
  -> O1 completes Ak and opens Wnext
  -> facade captures pending terminal artifact subset
  -> full wrapper-owned immutable historical payload copied and validated
  -> canonical env-ID-ordered exact-key tuple submitted once
  -> all captured slots atomically acknowledged by one slot-map publication
  -> current post-reset P2 read
  -> actor/current share/mask built from new episode
  -> terminal historical payload exposed separately
```

The terminal reason is copied from the authoritative artifact. It is not
inferred from the HARL done tensor.

## 17. Default-off isolation

The constructor/factory dispatch must be exhaustive on exact canonical profile
type:

```text
ResolvedExistingAssignmentProfile
  -> current constructor fields and current reset/step path unchanged
  -> current resolver/controller/observation/mask behavior unchanged
  -> event facade argument must be None

ResolvedEventGatedAssignmentProfile
  -> exact same-profile event facade required
  -> legacy resolver must not be constructed or called
  -> raw event reset/step from wrapper forbidden
```

`make_assignment_harl_env` and `AssignmentIsaacLabEnv` are composition roots
that will require event-specific construction before the current runtime-ready
gate can move. Default/four existing routes must not construct a domain, O1, or
event facade, and their call graph must remain byte-for-byte behaviorally
equivalent.

## 18. Minimal implementation slices

### B1W-I4-1 — event facade, composition, reset, and no-claim continuation

- introduce the B-private exact event facade and immutable facade result types;
- construct domain -> env -> O1 -> facade -> wrapper at formal entrypoints;
- exact profile dispatch with existing-route negative isolation;
- route reset and zero-claim/continuation step through O1;
- prove proposal/control separation and Ak-bound control;
- keep readiness blocked.

### B1W-I4-2 — proposal interpretation and effective B1 commit

- pure P2-bound classification and stale-source check;
- pure structural legality then explicit physical-feasibility filtering;
- pure finite-cost/robot-ID conflict ranking within eligible candidates only;
- M1 task-disjoint request construction;
- zero-or-one W2/B1/C2 artifact per action batch;
- proposal/effective/rejection/conflict diagnostics;
- executing same-task continuation and different-task/noop rejection.

### B1W-I4-3 — terminal wrapper handoff

- wrapper/facade capture after Ak completion;
- full-tuple immutable copy and validation;
- one same-domain atomic batch exact acknowledgement with no partial success;
- bounded private step payload and cache reset;
- failure-before-ack and next-step R3 verification;
- no learner insertion yet.

### B1W-I4-4 — focused bounded integration verification

- pure facade identity/order/default-off checks;
- real admitted reset/nonterminal continuation/new claim/conflict where fixture
  scope is authorized;
- real terminal/autoreset/copy/ack/recovery verification;
- protected hashes and readiness negative checks.

### Separately gated after I4

- exact event actor/shared observation projector and lifecycle mask/DVM;
- repo-local runner forced-row behavior so ordinary rows do not call actor
  sampling;
- authoritative pre-reset physical centralized critic sidecar;
- learner-buffer historical terminal insertion and TIME_LIMIT semantics;
- runtime readiness review, training, playback, and evaluation.

## 19. Stop-condition audit

| Candidate stop | Result | Reason |
|---|---|---|
| resolver authority conflict | avoided | event route bypasses the stateful resolver; only its ordered explicit-feasibility and pure ranking semantics are reused |
| feasibility/cost eligibility ambiguity | closed | explicit physical feasibility is an eligibility filter; cost ranks only surviving candidates and fallback cannot re-enter rejected pairs |
| action semantic gap | closed for this design | frozen event schema resolves continuation/noop; full event mask implementation remains deferred |
| control-order gap | closed | O1 already supplies final-P2 -> Ak -> control -> env -> completion order |
| terminal transport gap | closed at wrapper runtime-copy boundary | exact capture and atomic batch ACK are separate; bounded copy owner is the wrapper facade; full critic sidecar remains a readiness prerequisite |
| multi-row partial ACK risk | closed | full-batch validation and preparation precede one terminal-slot publication; any row rejection removes none |
| HARL API integration gap | no installed-core blocker | wrapper-private side channel plus repo-local env/runner specialization is sufficient; learner wiring is deferred |
| assignment authority duplication | avoided | facade holds no Store/P2 mutation and legacy resolver is absent from the event branch |
| learner scope dependency | not required for first I4 | ACK-A only requires bounded historical copy, not completed learner consumption |

## 20. Final design verdict table

| Required field | Verdict |
|---|---|
| wrapper architecture choice | `WR-C` |
| event wrapper reset route | frozen: wrapper -> event facade -> O1 -> admitted raw reset -> current P2 outputs |
| event wrapper step route | frozen: structural/explicit-feasibility filtering -> conflict ranking -> optional one B1 batch -> final P2 -> O1/Ak control -> atomic terminal handoff |
| O1 facade ownership | frozen: encapsulated by event facade; wrapper gets no raw ports/domain |
| proposal semantics | frozen: P2-bound proposal only; forced ordinary row is not proposal |
| noop semantics | frozen: executing noop illegal; needs noop no claim; waiting/unavailable deterministic noop encoding |
| same-task continuation | frozen: no B1 mutation/version increment |
| different-task-during-execution | frozen: reject/defer, current P2 task continues |
| conflict candidate eligibility | frozen: `EXPLICIT-FEASIBILITY-FIRST`; cost cannot create eligibility |
| conflict cost arbitration | frozen: among eligible candidates, lowest finite cost then robot ID; if no finite cost, lowest robot ID in that eligible set |
| infeasible fallback re-entry | prohibited |
| legacy resolver role | frozen: existing routes only; event route bypasses stateful resolver, reuses only ordered filtering/ranking semantics |
| B1 candidate batch construction | frozen: M1 selected-env task-disjoint `[K,M]`, zero or one artifact |
| P2 authoritative source | frozen: retained event domain current publication only |
| Ak control source | frozen: final P2 captured by S4 admission only |
| terminal capture timing | frozen: after outer return/Ak completion/Wnext OPEN, before wrapper return/next inference |
| terminal copy owner | frozen: bounded immutable wrapper-facade step payload |
| multi-row ACK model | frozen: `ATOMIC_BATCH_EXACT_ACK`; all-or-none removal by one slot-map publication |
| partial successful ACK | impossible by contract |
| exact ack timing | frozen: ACK-A after full-copy and full-batch validation, before return/next admission |
| actor next obs | frozen: current post-reset observation + current P2 |
| historical terminal critic payload | frozen interface requirement: exact-key pre-reset sidecar, separate from current `share_obs` |
| wrapper cache reset | frozen: clear/rederive from current post-reset P2 |
| default profiles | unchanged |
| learner transport | deferred |
| observation/mask implementation | deferred and readiness-blocking |
| implementation slicing | frozen as I4-1 through I4-4 plus separately gated learner/schema work |

## 21. Source evidence snapshot

The read-only audit used these source snapshots:

```text
DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A  assignment_harl_wrapper.py
B6F32510AE663B3E443891CDD09219DD9A5C9CEB9DE9C720C73192C7488597FD  assignment_harl_training.py
7F64183C638697F16EFA45769978127C7E3575599E87CFA76A5BA26F20EABADB  assignment_lifecycle_resolver.py
03483727573974BB57F96309D9D8A1EC446D87580915747BC57014BB4CC7F754  assignment_lifecycle_resolver_runtime.py
56A7A81160A007413D56F62B982A500DEFC66F4F37E884ABB7A0C96313CAF496  assignment_event_profile_synchronous_runtime.py
545274EEF630977E97C1064D831F5841DC97E8A38AA720E4474DEB7BEC7197B7  assignment_event_profile_runtime_domain.py
C74868C84A803108C424827AFE9326393428938DCE4F6CBD46693DA3D4D94FDA  assignment_initial_claim_runtime.py
17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609  assignment_interstep_claim_window_runtime.py
FFB1885B2440DC510B7D04469B0216143BE380798B5A2F236FFFE99F9B30CAA0  assignment_lifecycle_transaction_runtime.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99  scan_mobile_manipulator_env.py
3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59  assignment_rl_interface.py
5D99E0FA6F70F0BBFF4D5B0F00F45FAA3E4B543E1531F5259900480F1842044F  installed HARL on_policy_base_runner.py
```

## 22. Documentation-only validation

```text
Q1-Q20 answer rows:                    20/20
Markdown fence parity:                 even
required targeted revision sections:   present
EXPLICIT-FEASIBILITY-FIRST verdict:     present
ATOMIC_BATCH_EXACT_ACK verdict:         present
required Examples A-E:                 present
old ambiguous conflict/ACK wording:     absent
trailing whitespace in edited docs:    none
protected audited Python hashes:        exact
git diff --check for tracked handoff:   pass
Python tests:                           not run
Isaac / AppLauncher / HARL:             not run
training / playback / evaluation:       not run
```

The dirty worktree contains the authorized prior phase cohort and user-owned
changes. This targeted revision modified only this existing authoritative report
and `TASK_PROGRESS.md`; it did not alter or clean unrelated files.

## 23. Phase boundary

B1W-I4 implementation is not authorized by this targeted revision. Do not modify wrapper,
resolver, runtime, environment, HARL integration, observations/masks, terminal
sidecars, learner buffers, readiness, or configuration; do not run Isaac,
training, playback, or evaluation; and do not commit. Await GPT/user review.
