# Phase B2-T4-W2E claim/multi-update completion evidence-contract reconciliation

Date: 2026-09-20. Classification: `PHASE-B2-T4-W2E-CLAIM-MULTI-UPDATE-COMPLETION-EVIDENCE-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`. This is a new, offline, retrospective contract. Historical RE5 remains **GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED**; no learner was resumed and no RE6 was started.

Machine evidence: [W2E artifacts](b2_t4_w2e_artifacts/). Historical immutable evidence: [RE5 artifacts](../20260916/b2_t4_re5_artifacts/) and [RE5 report](../20260916/PHASE_B2_T4_RE5_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md). The pure [selector](../../../../../../../../scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py) and [offline matrix/replay](../../../../../../../../scripts/environments/test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py) are test-side only.

## A. repository authority

Before W2E writes: branch `main`; HEAD, `origin/main`, merge-base `b71d85a32f51be6ada324f870813a56bb45dd396`. Full `git status --porcelain=v1 -uall`: 9,665 lines, UTF-8/LF-with-final-newline SHA-256 `dca69338acee9bcf08f35aa4bd2d268a180978ffeacb71dfebb164f0dbf34698`. Existing staged migration: 359 paths; `git ls-files --stage` UTF-8/LF-with-final-newline SHA-256 `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`. The 359 path names joined with LF without final newline yield monthly path-set SHA-256 `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No index operation was performed.

## B. starting reviewed authority

B2-R0–R7, B2-T0–T3, B2-T4-NR/SR/ZD/EP-Q/PW remain reviewed closed. This task accepts the user's independent RE5 STOP confirmation and does not issue a new RE5 review. Earlier historical STOPs are unchanged.

## C. historical RE5 preservation

The formal RE5 classification remains `PHASE-B2-T4-RE5-STOP-FORMAL-WORKER-FAILURE`; the narrower source-backed handoff remains `PHASE-B2-T4-RE5-STOP-W2-MULTI-UPDATE-COMPLETION-WITNESS-NOT-ESTABLISHED-AFTER-MUTATION`. Formal `partial_update=true`, `route_poisoned=true`, Layer A false, Layer B true. [Identity manifest](b2_t4_w2e_artifacts/re5_artifact_identity.json) freezes 14 consumed formal artifacts before and after the offline replay; all hashes match exactly. No historical formal file was rewritten, normalized, appended, promoted, renamed or deleted.

## D. RE5 formal evidence summary

The single historical attempt recorded 320 physical transitions, 160/160 production S10 and transaction rows, 159/159 bridges, 6,560/6,560 critic PW, 640/640 actor/factor PW, 22 `task_completed` lifecycle events, and zero `task_claimed` lifecycle events. W1 and W3–W7 individually passed; W2 did not. tx150 observed normal-horizon TIME_LIMIT/autoreset, tx151 trained post-reset. The episode/update, runtime/P2 immutability, actor-evidence, terminal, bootstrap and rolling ledgers each have 160 ordered rows; immutability equality and actor exact-match are 160/160, actor faults 0. These are historical observations, not RE5 qualification.

## E. exact old W2 failure

The inherited selector collected the first `task_claimed` event per `(env,robot,task)` and later `task_completed` events. RE5 had zero claim events, 22 completion events and zero eligible event pairs; therefore `W2_MULTI_UPDATE_COMPLETION=None`. This matches the immutable worker exception and does not prove no runtime claims occurred.

## F. B1 source authority

`assignment_event_proposal_adapter.py:484-681` checks proposal, current P2 availability/ownership/failed pair/feasibility and resolves conflicts to one deterministic winner per task. `assignment_event_runtime_facade.py:609-717` commits zero or one resolved B1 batch before physical admission. `assignment_initial_claim_runtime.py:665-775` requires `AVAILABLE`/unowned and `NEEDS_ASSIGNMENT`, then derives `CLAIMED`, owner=robot, robot `EXECUTING`. `assignment_lifecycle_transaction_runtime.py:4591-4703` performs the authoritative StateStore swap and publishes an `EffectiveAssignmentCommitArtifact`. Proposal alone is not a claim. Within the event-profile proposal route, B1 is the proposal-driven ownership mutation.

## G. P2 ownership semantics

Canonical encodings in `assignment_lifecycle_transition_contract.py:84-104`: task `AVAILABLE=0`, `CLAIMED=1`, `NAVIGATING=2`, `ALIGNING=3`, `COMPLETED=4`; robot `EXECUTING=0`, `NEEDS_ASSIGNMENT=1`; no owner `-1`. B1 turns task state `0→1` and owner `-1→robot`, and sets robot `EXECUTING`. The policy evidence's `current_owned_task_id` is an inverse view of P2 ownership, not an independent ownership writer. The facade checks that physical admission uses final post-B1 P2.

## H. explicit claim-event audit

The exact production `LifecycleEventType` enum in `assignment_event_contract.py:57-67` has `TASK_COMPLETED`, release and robot events, but **no `TASK_CLAIMED`**. The production Python source search found no literal `task_claimed` emission. `assignment_lifecycle_resolver.py:767-806` has an `attempt_started` diagnostic in a distinct resolver path; it is not a P2 lifecycle `task_claimed` event. Classification: **EXPLICIT CLAIM EVENT NOT PART OF CANONICAL RUNTIME CONTRACT**. See [audit](b2_t4_w2e_artifacts/explicit_task_claimed_event_audit.json).

## I. completion-event audit

`assignment_lifecycle_transaction_runtime.py:1667-1737` derives completion from execution facts: task state becomes `COMPLETED`, owner becomes `-1`, completion count increments, and the robot becomes `NEEDS_ASSIGNMENT` when legal work remains. Its event builder at `:1995-2025` emits `TASK_COMPLETED` from the completion signal, so 22 such events appear in RE5. Completion is independently evidenced; it is not used to infer an earlier claim.

## J. claim/completion instrumentation asymmetry

B1 claim is a separate StateStore/P2 swap and effective-assignment publication, without a lifecycle claim event. Completion is a physical-step lifecycle derivation with a typed `task_completed` event. The old W2 test selector required a textual event outside that production lifecycle-event vocabulary. This is an observer/evidence-contract mismatch, not an established production lifecycle defect.

## K. W1 evidence semantics

`test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py:1057-1094` established W1 from P2 task owner and active state on both sides of tx001→tx002, same episode generation, plus next decision row `decision_required=false` and zero policy calls. It did **not** use `task_claimed`. The W2E continuity layer uses the same P2 owner/active semantics and additionally requires exact qualified bridge identity.

## L. old W2 exact predicate

The inherited source at `test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py:1095-1122` uses the first event named `task_claimed` per exact `(env_id,robot_id,task_id)`, a matching `task_completed` event, `claim.transaction_index < completion.transaction_index`, a completion-step P2 `task_state[task]==4`, and `ownership[task]==-1`. It *records* `decision_reopened=bool(state["next_decision_required"][robot])` but does **not gate** W2 on that boolean. It has no explicit episode or intervening release/reassign guard. RE3 wraps this RE1 selector to add actor reconciliation (`test_assignment_phase_b2_t4_re3_normal_horizon_learned_training_integration.py:257-275`); RE5 calls the inherited postprocessor. W2E does not edit or reinterpret the old selector.

## M. old-contract RE5 replay

[Old replay](b2_t4_w2e_artifacts/re5_old_w2_contract_replay.json) and [old W2 replay](b2_t4_w2e_artifacts/old_w2_replay.json) independently record claim candidates 0, completions 22, eligible pairs 0, W2 `null`. The historical STOP is reproduced. Neither replay writes a historical witness file.

## N. claim-authority candidates

| Evidence | Runtime authority? | Present in RE5? | Suitable claim authority? | Reason |
|---|---|---|---|---|
| explicit `task_claimed` event | no canonical production event | no | no | absent from typed event enum |
| P2 task.owner transition | yes | yes, before/after state | necessary | actual ownership relation |
| robot.current_task transition | derived inverse of P2 | yes | corroboration | must agree with owner; not separate writer |
| task.state transition | yes | yes | necessary | `AVAILABLE→CLAIMED/active` |
| B1 mutation receipt | yes | indirect admitted B1/P2 evidence | source authority | per-claim artifact not separately serialized in ledger |
| effective assignment | admitted B1 result | yes | corroboration only | proposal alone could be rejected |
| P2 conjunction plus B1-effective binding | yes | yes for post-initial claims | **selected** | excludes proposal-only and continuation |

The full classification is in [candidate audit](b2_t4_w2e_artifacts/claim_authority_candidates.json).

## O. selected canonical claim authority

The authoritative runtime operation is successful B1 StateStore mutation/P2 publication: exact `AVAILABLE`/unowned task becomes `CLAIMED`/owned by robot, robot becomes `EXECUTING`, and admitted effective assignment equals the task. RE5's before/after P2 snapshots and decision/effective rows are observational evidence of that operation. tx001 claims lack a retained pre-physical-step P2 snapshot, so the v2 selector rejects them rather than assuming reset state.

## P. observer vs runtime authority

Task state, owner, robot state and completion count originate in production P2; `next_owned_task` and DVM are production decision-bundle projections. Effective assignment is the facade's admitted B1 result. `lifecycle_rows` and `step.state_rows` are read-only test observers of those sources; `transaction` and `bridge` ledgers are test-side durable qualifications. The v2 selector never promotes an observer-only textual claim event into runtime authority.

## Q. v2 contract

The new pure contract is `b2_t4_w2e_multi_update_completion_v2`, separate from historical RE5 W2. It is implemented in [selector](../../../../../../../../scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py) and machine-described in [contract](b2_t4_w2e_artifacts/w2e_contract_v2.json). PASS requires A claim authority **and** B cross-update continuity **and** C completion **and** D owner clear **and** E decision reopen for one exact env/robot/task and episode generation.

## R. claim hard predicates

The decision row must be unique, current-step-bound, policy-required, called once, proposal-bearing and pre-unowned. The immediately prior P2 snapshot must show the task `AVAILABLE`/unowned and robot without another owned task; the post-step P2 must show same-generation active task owned by that robot and robot `EXECUTING`. Admitted effective assignment must equal the task, and the claim transaction must be S7–S10/finite qualified. No completion-derived claim inference is allowed.

## S. continuity hard predicates

`claim_tx < completion_tx`. Every intervening physical-step P2 state must retain that exact owner, active task, executing robot and episode generation. At least one **pre-completion** qualified bridge must bind the exact adjacent update IDs and preserve learner/collection identity; its next decision row must be forced continuation with no policy call and same ownership. Release, failure or early-completion event for the identity fails closed.

## T. completion hard predicates

A later exact `task_completed` event must match env/robot/task. Same-generation post-step P2 task state must be `COMPLETED`; the matching robot's completion count must rise by one from the immediately previous state. The completion transaction must be S7–S10/finite qualified.

## U. ownership-clear predicates

After that completion, P2 task owner must be `-1`, and the inverse current-task projection for that robot must no longer point at the completed task. Event text alone is insufficient.

## V. decision-reopen predicates

The completion post-state must show the *same* robot `NEEDS_ASSIGNMENT` and `next_decision_required=true`. Its immediately following same-generation decision row must be unique, policy-required and have exactly one actor policy call, with no current owned task. Unlike old W2, this is an actual gate.

## W. episode-generation safety

Claim, every continuity state, completion and reopen must have one episode generation. tx150 terminal/autoreset-derived apparent claim edges cannot be joined to a prior generation. Synthetic generation-change negative fails.

## X. release/reassign safety

Every intervening P2 owner/task/current-task state and explicit release/failure event is checked. A release, failed-pair invalidation, ownership transfer or reassignment breaks the chain even if a later same-task completion exists. No release/reclaim interval is silently joined.

## Y. positive matrix

[Positive matrix](b2_t4_w2e_artifacts/positive_matrix.json): one qualified boundary, multiple qualified boundaries, and unrelated interleaving each PASS (3/3 final cases). All use the same production-shaped P2 encodings and exact layer predicates; they are synthetic logic tests, not environment runs.

## Z. negative matrix

[Negative matrix](b2_t4_w2e_artifacts/negative_matrix.json): 18/18 STOP, unexpected PASS 0. It covers completion without claim, same tx, wrong robot/task, owner transfer, release/reassignment, generation change, missing count increment, uncleared owner, no reopen, continuation-as-claim, proposal-only, duplicate claim, stale P2 observer, wrong bridge identity, a release event hidden by a misleading post-state, and stale collection identity.

## AA. immutable RE5 candidate inventory

[Candidate inventory](b2_t4_w2e_artifacts/re5_w2_v2_candidate_inventory.json) enumerates all 29 observed unowned→owned robot decision edges, each with ordered layer reasons, source pointers and state digests; 12 complete chains pass. Six tx001 edges fail closed for missing retained pre-claim P2, three otherwise matched chains fail reopen, two earlier claims lack completion, and six tx150 post-reset edges lack completion. One of the 22 completion events has no preceding matching claim edge. No candidate was manually cherry-picked.

| Env | Robot | Task | Claim tx | Claim step | Bridge tx(s) | Completion tx | Completion step | Clear | Reopen tx/step | Generation | PASS |
|---:|---:|---:|---:|---:|---|---:|---:|---|---|---:|---|
| 1 | 1 | 10 | 12 | 23 | 12–14 | 15 | 30 | yes | 16/31 | 0 | yes |
| 1 | 1 | 7 | 16 | 32 | 16–25 | 26 | 52 | yes | 27/53 | 0 | yes |
| 1 | 2 | 2 | 16 | 32 | 16–45 | 46 | 91 | yes | 46/92 | 0 | yes |
| 0 | 1 | 0 | 26 | 52 | 26–59 | 60 | 119 | yes | 60/120 | 0 | yes |
| 1 | 1 | 5 | 27 | 53 | 27–42 | 43 | 85 | yes | 43/86 | 0 | yes |
| 1 | 0 | 8 | 34 | 68 | 34–52 | 53 | 105 | yes | 53/106 | 0 | yes |
| 0 | 0 | 11 | 37 | 73 | 37–42 | 43 | 86 | yes | 44/87 | 0 | yes |
| 1 | 1 | 6 | 43 | 86 | 43–49 | 50 | 100 | yes | 51/101 | 0 | yes |
| 0 | 0 | 3 | 44 | 87 | 44–62 | 63 | 125 | yes | 63/126 | 0 | yes |
| 0 | 1 | 1 | 60 | 120 | 60–66 | 67 | 134 | yes | 68/135 | 0 | yes |
| 0 | 0 | 2 | 63 | 126 | 63–71 | 72 | 144 | yes | 73/145 | 0 | yes |
| 0 | 1 | 8 | 68 | 135 | 68–83 | 84 | 167 | yes | 84/168 | 0 | yes |

## AB. deterministic witness selection

All candidate pairs are enumerated before selection. Ordering: claim tx, claim physical step, completion tx, env, robot, task ascending. The selected first passing chain is env 1/robot 1/task 10, not a visually selected example. See [replay](b2_t4_w2e_artifacts/re5_w2_v2_replay.json).

## AC. selected retrospective W2 witness

At step 22, env 1 task 10 was `AVAILABLE`, owner `-1`, robot 1 without an owned task. At step 23/tx12 the unique policy row called once; admitted effective assignment=10; post P2 became `CLAIMED`, owner=1, robot `EXECUTING`, inverse task=10. tx12→13, tx13→14 and tx14→15 qualified bridges retained exact ownership and no policy call. Step 29 still had owner=1. Step 30/tx15 emitted exact `task_completed`, changed task state `1→4`, owner `1→-1`, robot completion count `2→3`, robot `NEEDS_ASSIGNMENT`, DVM true. Step 31/tx16 was the same robot's policy-required row with one call and no prior owned task. Selected pre/post state digests and row pointers are in the replay/inventory. This is retrospective W2E evidence only.

## AD. W1/W2 semantics cross-check

Both W1 and W2E use P2 owner and active task state, same generation, and forced-continuation/no-policy evidence at a qualified boundary. W2E additionally requires an independent claim transition, completion, owner clear and same-robot reopen. No ownership-definition contradiction was found. [Cross-check](b2_t4_w2e_artifacts/w1_w2_semantics_crosscheck.json).

## AE. RE5 old-vs-v2 replay

| Requirement | Historical W2 | W2E v2 |
|---|---|---|
| Claim authority | explicit `task_claimed` event | B1-committed P2 transition plus effective binding |
| Multi-update | `claim_tx < completion_tx` | retained, with qualified pre-completion bridge |
| Ownership continuity | no full interval guard | every P2 step and forced continuation |
| Completion | `task_completed` and P2 state 4 | same plus exact count increment |
| Ownership clear | P2 owner `-1` | owner `-1` and inverse task cleared |
| Decision reopen | boolean recorded, not gated | same-robot DVM/NEEDS + next policy call required |
| Episode identity | no explicit guard | same generation throughout |
| Release/reassign safety | no explicit guard | event and full P2 interval guard |
| RE5 result | W2=`None`; formal STOP | 12 retrospective v2 chains; **formal RE5 unchanged** |

## AF. event-emission gap classification

`EXPLICIT CLAIM EVENT NOT PART OF CANONICAL RUNTIME CONTRACT`. Zero RE5 claim-event entries are expected under the typed production event vocabulary, while authoritative claims are visible through B1/P2 and effective assignment. The mismatch is in the inherited test-only W2 event requirement.

## AG. production-defect assessment

No production lifecycle defect is established by this evidence. B1/P2 claim transition, completion event, count, owner clear and decision reopen align for 12 retrospective chains. This does not prove all production trajectories correct; it only reconciles this narrow evidence contract. No production or RE5 harness patch was made. No `REPAIR REQUIRED` production action follows from W2E.

## AH. source/artifact preservation

[Source manifest](b2_t4_w2e_artifacts/source_identity_manifest.json) freezes protected production files, B1/P2/decision sources, RE1/RE3 witness selectors, RE5 harness and PW helper. [RE5 identity manifest](b2_t4_w2e_artifacts/re5_artifact_identity.json) proves all 14 consumed formal files byte-identical before/after replay. Production semantic modifications 0; historical RE5 harness/artifact modifications 0. The pre-existing staged migration must remain unchanged.

## AI. exact execution counts

This W2E work used 9 pure/static Python invocations: 1 interpreter verification, 4 `py_compile`, 4 offline replay/matrix runs. Eight named source-trace entries were recorded. Old W2 replay ran 4 times. The pure v2 reconciler ran 84 times across development/final offline runs (4 RE5 replays, 12 positive synthetic cases, 68 negative synthetic cases); final matrix is 3 positive and 18 negative cases, all expected, unexpected negative PASS 0. Candidate chains 29; valid 12; selected witness 1. AppLauncher/environment/physical steps/learner constructions/learner mutations/checkpoint I/O/public activation/evaluation-playback all 0. Production/historical RE5 modifications 0/0; RE6 not started; git add/commit/push 0/0/0.

## AJ. retained nonclaims

W2E PASS does not reclassify historical RE5, unpoison its learner, qualify overall normal-horizon training, prove training quality/convergence, authorize checkpoint continuation, RE6, B2-R6, public-policy activation, playback/evaluation or long training. This phase did not launch an environment or learner.

## AK. final classification

`PHASE-B2-T4-W2E-CLAIM-MULTI-UPDATE-COMPLETION-EVIDENCE-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`. W2E is complete awaiting independent review; v2 retrospective RE5 evidence PASS. Historical RE5 is still GPT REVIEW STOP CONFIRMED / HISTORICAL / POISONED / NOT QUALIFIED. No self-issued GPT REVIEW PASS.

## AL. GPT-review handoff

Review the exact B1/P2 source operation, typed event vocabulary, old W2 source and replay, all 29 inventory rows, the selected tx12→15→16 chain, 3/3 positive and 18/18 negative matrix, source/artifact identities, and the formal RE5 STOP boundary. Do not launch RE6 or rerun RE5; do not construct AppLauncher/environment/learner, checkpoint, activate the public route, stage or commit. A future fresh run requires separate authorization.
