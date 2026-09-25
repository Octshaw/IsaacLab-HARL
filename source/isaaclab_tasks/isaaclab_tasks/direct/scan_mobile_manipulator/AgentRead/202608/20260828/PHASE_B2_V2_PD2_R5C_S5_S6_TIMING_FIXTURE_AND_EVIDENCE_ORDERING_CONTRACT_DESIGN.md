# Phase B2-V2-PD2-R5-C — S5/S6 Timing Fixture and Evidence-Ordering Contract Design

Date: 2026-08-28

Classification: `PHASE-B2-V2-PD2-R5C-TARGETED-S5-POSTSTATE-SEPARATION-REVISION-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Starting authority

```text
committed HEAD:       14993dee344bade0230d2eb97b5f22171331f44a
B2-D:                 GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:  GPT REVIEW PASS / CLOSED
B2-V1:                GPT REVIEW PASS / CLOSED
B2-V2:                STOPPED / INCOMPLETE
B2-V2-PD1:            GPT REVIEW PASS / FROZEN
PD-A:                 CURRENT-PRODUCTION-RUNTIME-VALIDATION / FROZEN MODE
PD2-R3:               GPT REVIEW PASS / CLOSED
PD2-R4 / R4-TR:       GPT REVIEW PASS / FROZEN
PD2-R5-A:             GPT REVIEW PASS / CLOSED
PD2-R5-B:             HISTORICAL FORMAL STOP RETAINED
PD2-R5-C-TR:          GPT REVIEW PASS / CLOSED
PD2-R5-C-TR2:         DESIGN-ONLY TARGETED REVISION
B2-R / training:      NOT AUTHORIZED / NOT AUTHORIZED
commit:               NONE
```

R5-C is design-only. It defines a future test-only fixture and evidence contract; it does not modify or execute the formal harness.

This second targeted revision changes only the structural separation between the required S5 preterminal DTO and optional post-return diagnostics. The reviewed preterminal S5 authority, `T=2`, desired terminal transition `2`, required `max_episode_length=3`, derived midpoint ratio `2.5`, early timing gate, S5-then-S6 external adjudication order, and S2 fingerprint contract remain frozen and unchanged.

Authoritative documents read completely:

- R5-B controlled formal re-entry report;
- R5-A cache-backed S0R implementation report;
- R4/R4-TR cache-backed authority design;
- PD1 production-startup validation design;
- current `TASK_PROGRESS.md`.

Read-only source audit covered:

- `test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py`;
- `DirectMARLEnv.max_episode_length` and step-counter ordering;
- `ScanMobileManipulatorEnv` timeout staging and `_get_dones()`;
- dormant I6 `collect_step()` ordering;
- the current test-only `CriticRecorder`.

## 2. R5-B GPT review interpretation

The controlling review classification is:

```text
PHASE-B2-V2-PD2-R5B-STOP-REVIEW-CONFIRMED-TEST-ONLY-S5S6-FIXTURE-CONTRACT-MISMATCH
```

Reviewed blocker:

```text
TEST-ONLY TIMEOUT FIXTURE
+
S5/S6 ASSERTION-ORDER CONTRACT
```

The review does not establish a DirectMARLEnv, lifecycle, terminal transport, HARL, VCritic, actor, P2, or Ak defect. It authorizes no runtime retry and no repair in R5-C.

Subsequent GPT review accepted the timing and S2 portions but identified one targeted ambiguity:

```text
GPT issue: R5C-S5-AUTHORITY-01
problem:   S5 authority was ambiguous across the transition-2
           terminal/autoreset boundary
old risk:  "second/current P2" could mean the post-autoreset P2
revision:  S5 uses only immutable transition-2 PRE-TERMINAL
           effective/controller/decision evidence
status:    CLOSED BY THIS TARGETED DESIGN REVISION
```

The subsequent review accepted that authority closure and identified one residual structural dependency:

```text
GPT issue: R5C-S5-POSTSTATE-02
problem:   post-return/autoreset diagnostics were structurally mixed
           into the required S5 DTO
revision:  the required S5 DTO contains PRETERMINAL evidence ONLY
post-return state:
           separate optional diagnostic; not S5 authority
post-autoreset interpretation:
           valid only after S6 proves terminal/autoreset semantics
S5 independence:
           post-return diagnostics are NOT REQUIRED FOR S5 PASS
status:    CLOSED BY THIS SECOND TARGETED DESIGN REVISION
```

## 3. Historical formal STOP preservation

R5-B remains exactly:

```text
classification: PD2-STOP-TERMINAL-TRANSPORT-FAIL
first boundary: S6_TIME_LIMIT
result:         STOPPED / INCOMPLETE
```

R5-C explains the mechanism prospectively. It does not edit the R5-B report or artifact, mark R5-B PASS, or apply a future contract retroactively.

## 4. Positive R5-B real-runtime evidence

The following evidence is frozen positive evidence and is not rerun:

| Stage | Reviewed evidence |
|---|---|
| S0 | production startup path PASS |
| S0R | live extension-manager PASS; stable 67-entry set |
| cache-backed rows | live usdrt and Warp L1/L2/L3 PASS |
| S1 | real environment/reset/I1/I2 PASS |
| I1/I2 shapes | actor `[2,3,421]`; critic `[2,3,418]`; available actions `[2,3,13]`; six DVM rows |
| S2 | installed VCritic `[2,418] -> [2,1]`, finite, float32, cuda:0 PASS |
| S3 | real HAPPO actor PASS |
| S4 | first physical learned-policy event step PASS |
| shutdown | safe `EXTERNAL_CLEAN_TERMINATION` |
| postrun | `NO_OBSERVED_STATE_CHANGE` |

The original VCritic CUDA failure was not reproduced under the reviewed current production-startup path. R5-C does not return to CUDA forensics.

## 5. Current timing fixture arithmetic

Current frozen harness:

```text
E/M/N/T = 2/3/12/2
EPISODE_HORIZON_CONTROL_STEPS = 3

cfg.episode_length_s =
  float(cfg.sim.dt) * int(cfg.decimation) * 3
```

Current environment facts:

```text
sim.dt:          1/60
decimation:      6
control step:    0.1
episode_length_s:0.30000000000000004
raw ratio:       3.0000000000000004
ceil(raw ratio): 4
```

Production `DirectMARLEnv` computes:

```text
max_episode_length = ceil(
  episode_length_s / (sim.dt * decimation)
)
```

It increments `episode_length_buf` before `_get_dones()`. The event environment then computes:

```text
time_out = episode_length_buf >= max_episode_length - 1
```

The old fixture therefore yields:

```text
transition 1 -> buffer 1 -> 1 >= 3 false
transition 2 -> buffer 2 -> 2 >= 3 false
transition 3 -> buffer 3 -> 3 >= 3 true
```

The R5-B harness instead required transition 2 to be terminal. Its STOP is consequently explained by the test fixture, not by terminal transport evidence.

## 6. T=2 semantic audit

PD1 is unambiguous:

- S5 is the “second and final bounded `collect_step`”;
- S6 says “With `T=2`” the second transition exercises TIME_LIMIT and terminal transport;
- PD1 calls the entire validation a “two-transition forward-only smoke”;
- the I6 route admits slots only while `slot < episode_length`, so `T=2` provides exactly slots 0 and 1.

Authoritative R5-C decision:

```text
T=2 FORMAL CONTRACT:
  exactly two physical transitions are collected and stored

transition 1:
  S4 first physical learned-policy step
  must be nonterminal

transition 2:
  S5 continuation/control semantics
  and S6 TIME_LIMIT/terminal semantics
  on the same physical transition

third transition:
  forbidden by this contract
```

There is no frozen-document conflict and no reason to use the R5-C STOP classification.

## 7. Desired terminal-transition derivation

Freeze:

```text
PD2_DESIRED_TERMINAL_TRANSITION = 2
```

At `_get_dones()`:

```text
transition k -> episode_length_buf = k
TIME_LIMIT iff k >= max_episode_length - 1
```

Required behavior:

```text
transition 1 nonterminal:
  1 < max_episode_length - 1

transition 2 terminal:
  2 >= max_episode_length - 1
```

These inequalities jointly require:

```text
max_episode_length - 1 = 2
max_episode_length = 3
```

## 8. Required max_episode_length contract

Freeze the semantic integer outcome first:

```text
PD2_REQUIRED_MAX_EPISODE_LENGTH =
  PD2_DESIRED_TERMINAL_TRANSITION + 1
  = 3
```

This integer is the fixture authority. `episode_length_s` is only its encoding through the unchanged DirectMARLEnv arithmetic.

The misleading name `EPISODE_HORIZON_CONTROL_STEPS` should not survive a future R5-D implementation. It conflates the desired physical terminal transition with the integer returned by `max_episode_length`.

## 9. Candidate timing-fixture designs

### Candidate A — literal fractional ratio

Set ratio to literal `2.5`, then set duration to `control_step * 2.5`.

Advantages: simple, exactly inside the `ceil == 3` bucket. Limitation: without derivation, `2.5` looks like an unexplained magic number.

### Candidate B — derived bucket midpoint

Derive the open bucket interior from the required integer:

```text
lower = PD2_REQUIRED_MAX_EPISODE_LENGTH - 1 = 2
upper = PD2_REQUIRED_MAX_EPISODE_LENGTH     = 3
ratio = (lower + upper) / 2                 = 2.5
```

Then encode `episode_length_s = control_step * ratio`.

Advantages: semantic integer authority, maximum symmetric distance from both bucket boundaries, readable derivation, no tolerance constant, and no production change.

### Candidate C — boundary subtraction or direct seconds

Examples include `3 * control_step - epsilon`, `nextafter`, or hard-coded `0.25` seconds.

Rejected: epsilon/nextafter is boundary-adjacent and platform-sensitive; hard-coded seconds hides the relationship with the current control step and becomes stale if dt or decimation changes.

## 10. Chosen deterministic fixture

Choose Candidate B: the derived bucket midpoint.

Future test-only constants/derivation:

```text
PD2_DESIRED_TERMINAL_TRANSITION = 2
PD2_REQUIRED_MAX_EPISODE_LENGTH = 3

PD2_TIMEOUT_BUCKET_LOWER =
  PD2_REQUIRED_MAX_EPISODE_LENGTH - 1
  = 2

PD2_TIMEOUT_BUCKET_UPPER =
  PD2_REQUIRED_MAX_EPISODE_LENGTH
  = 3

PD2_TIMEOUT_FIXTURE_RATIO =
  (PD2_TIMEOUT_BUCKET_LOWER + PD2_TIMEOUT_BUCKET_UPPER) / 2
  = 2.5

control_step = float(cfg.sim.dt) * int(cfg.decimation)
cfg.episode_length_s = control_step * PD2_TIMEOUT_FIXTURE_RATIO
```

For the reviewed configuration:

```text
control_step:     0.1
episode_length_s: 0.25
raw ratio:        2.5
ceil result:      3
```

`2.5` is not a magic epsilon. It is the exact midpoint of the only acceptable ceil bucket selected by the desired terminal transition.

## 11. Floating-boundary robustness rationale

For `ceil(ratio) == 3`:

```text
2 < ratio <= 3
```

R5-C deliberately strengthens the fixture target to:

```text
2 < ratio < 3
```

The midpoint has mathematical margin `0.5` from both boundaries. The future gate does not use an approximate-equality tolerance. It directly proves:

```text
lower < observed_raw_ratio < upper
math.ceil(observed_raw_ratio) == 3
```

It also persists the observed lower and upper margins. No `1e-6`, `1e-9`, machine epsilon, or `nextafter` value is accepted by the future static audit.

## 12. Environment early assertion contract

Immediately after `gym.make(...)` and obtaining the unwrapped environment, but before route reset, model forward, or physical transition, future R5-D must calculate and persist:

```text
desired_terminal_transition
required_max_episode_length
sim_dt
decimation
control_step
episode_length_s
raw_ratio
ceil_result
lower_margin = raw_ratio - 2
upper_margin = 3 - raw_ratio
actual env.max_episode_length
```

Required joint predicate:

```text
control_step > 0
2 < raw_ratio < 3
ceil_result == 3
env.max_episode_length == 3
```

On PASS, emit a durable S1 checkpoint such as:

```text
stage: S1
label: timing_fixture_contract_pass
```

On mismatch, stop before reset/model forward/physical transition:

```text
classification: PD2-STOP-PHYSICAL-STEP-FAIL
boundary:       S1_TIMING_FIXTURE_CONTRACT
```

This class is preferable to terminal-transport failure: the mismatch is a test-only physical timeline setup defect detected before any terminal artifact exists. It is not startup-prefix or production admission failure.

## 13. Current S5/S6 order defect

The current external harness order after the second receipt is:

```text
second collect_step returns
-> S6 all-done assertion
-> S5 controller/continuation/forced-row assertions
```

Thus a TIME_LIMIT fixture mismatch prevents independent S5 adjudication, even though the second physical call returned. This contradicts PD1's conceptual S4 -> S5 -> S6 evidence hierarchy.

## 14. Revised S4/S5/S6 evidence order

Freeze the future harness adjudication order:

```text
FIRST collect_step
  -> S4 adjudicate first physical transition

SECOND collect_step
  -> S5 adjudicate second-transition continuation/control using only
     immutable PRE-TERMINAL transition-2 evidence
  -> persist S5 PASS
  -> S6 adjudicate same transition done/reason
  -> persist S6 terminal-predicate PASS
  -> adjudicate terminal sidecar/history/ACK/I5a/I5b/GAE
  -> Snapshot B
```

S5 and S6 are two evidence layers over the same second transition. They do not imply an additional step.

## 15. S5 independent adjudication contract — targeted revision

S5 answers exactly:

> What effective assignment and controller command were authoritative for the second physical transition?

It does not answer what assignment is current after `collect_step()` returns. S5 must not depend on done, TIME_LIMIT reason, terminal sidecar, ACK, bootstrap, GAE, terminal historical ownership, POST-RETURN state, or a later S6 interpretation of that state as POST-AUTORESET.

### 15.1 Frozen transition-2 authority timeline

```text
transition-2 sealed decision bundle
-> forced-continuation / genuine-policy classification
-> original actor proposal/logprob for policy rows only
-> pure resolver result
-> optional zero-or-one M1/B1 claim artifact
-> immutable final PRE-TERMINAL admitted P2
-> Ak assignment derived from that admitted P2
-> test-only controller-time assignment copy
-> physical environment step
-> TIME_LIMIT/lifecycle terminal facts
-> historical copy / ACK / autoreset
-> NEW post-autoreset current P2
```

Only the portion through controller execution is S5 authority. The later portion belongs to S6.

### 15.2 Source-audit result

The current route already preserves enough non-invasive evidence. No production or I6 field is required.

- `EventDormantLearnedStepReceiptV2` retains the exact transition slot, PRETERMINAL `decision_bundle`, `proposal_envelope`, `facade_result`, POST-RETURN `next_decision_bundle`, and HARL result (`assignment_event_learned_route.py:86-97`).
- `collect_step()` binds `bundle` before critic/actor/proposal work and returns that same object in the receipt after internal terminal transport (`assignment_event_learned_route.py:457-548`).
- `EventPolicyEvidenceSnapshot` stores cloned task state, robot state, ownership, current-owned-task ID, generations, P2 identity, and OPEN-window identity (`assignment_event_policy_evidence.py:627-729`).
- `EventPolicyDecisionBundle` stores cloned row-kind, policy, forced-continuation, forced-noop, forced-action, and DVM masks (`assignment_event_policy_decision.py:234-353`). Its forced-continuation action is the authoritative current owned task ID (`assignment_event_policy_decision.py:640-656`).
- `EventPolicyProposalEnvelope` stores cloned original proposal IDs, behavior logprobs, proposal/DVM/forced masks, and immutable per-agent actor call records (`assignment_event_actor_collection.py:145-275`). Actor subsets are constructed only from DVM indices (`assignment_event_actor_collection.py:606-733`).
- `EventFacadeProposalStepResult` retains `source_publication`, `post_claim_publication`, `admitted_publication`, the cloned `admitted_effective_assignment`, pure resolution, optional immutable claim artifact, and a separately named POST-RETURN `current_publication` (`assignment_event_runtime_facade.py:405-490`).
- The facade proves `receipt.admitted_publication is post_claim` before terminal handoff and only later reads the POST-RETURN current P2 for the result (`assignment_event_runtime_facade.py:609-716`). Thus `admitted_publication`, not `current_publication`, is the transition-2 control authority.
- The synchronous runtime captures physical admission before control, derives the assignment from that admitted P2, passes it to `action_builder`, and only then calls `environment.step()` (`assignment_event_profile_synchronous_runtime.py:446-480`).
- The existing test-only `action_builder` clones the exact assignment argument before the physical step (`test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py:2621-2626`). This is the observed controller-time assignment.
- Terminal handoff reads a POST-RETURN current P2, copies historical terminal data, and ACKs it (`assignment_event_runtime_facade.py:201-302`). That current P2 is only POST-RETURN diagnostic evidence until S6 proves terminal/autoreset semantics; the historical/ACK/current separation fields are S6 evidence, never S5 authority.

Although `_EventProfileNoClaimStepReceipt.admitted_control_assignment` is materialized into the receipt after `environment.step()` returns, its value was derived from the locally retained pre-controller admission and is never reconstructed from POST-RETURN state. For the strongest timing proof, future R5-D uses the already-existing pre-step `action_builder` clone as actual controller evidence and the immutable admitted P2 / admitted assignment as expected authority.

### 15.3 Evidence eligibility table

| Evidence field | Existing source | Relative to controller | Relative to terminal/autoreset | Immutable? | S5 authority eligible? | Reason |
|---|---|---|---|---|---|---|
| transition-2 lifecycle/ownership/current-owned-task | `second.decision_bundle.evidence_snapshot` | captured before actor/controller | before terminal and autoreset | yes; cloned tensors | yes, continuation authority | exact transition-2 pre-control P2 snapshot |
| continuation/policy/forced masks and forced task ID | `second.decision_bundle` | sealed before actor/controller | before terminal and autoreset | yes; cloned tensors | yes | authoritative I2 row classification for this transition |
| proposal IDs/logprobs and actor call rows | `second.proposal_envelope` | captured before resolver/controller | before terminal and autoreset | yes; cloned tensors/frozen records | yes, policy evidence only | exact original policy evidence; never effective authority |
| proposal P2/window/generations | bundle binding plus `facade_result.resolution` | captured before B1/controller | before terminal and autoreset | yes | yes, genuine-policy identity | exact source identity; not POST-RETURN state |
| claim-mutated rows | `facade_result.claim_artifact` or zero artifact | M1/B1 occurs before controller | before terminal and autoreset | yes; artifact tensors cloned | yes | proves which genuine decision rows entered ownership mutation |
| final effective P2 | `facade_result.admitted_publication` | captured by physical admission before controller | captured before terminal/autoreset; immutable reference remains available after return | yes; publication contains immutable/no-alias lifecycle snapshot | **primary S5 control authority** | facade proves it is the final post-claim P2 admitted to Ak |
| final effective assignment | `facade_result.admitted_effective_assignment` | value derived before `action_builder`; receipt clone assembled after return | derived before terminal/autoreset; copy materialized after return from retained local value, with no live-state reread | yes; cloned tensor | yes | bounded Ak projection of admitted P2 |
| actual controller-time assignment | test-only `control_assignments[1]` | cloned inside `action_builder` before `environment.step()` | before terminal and autoreset | yes; test-only clone | **primary observed controller evidence** | exact assignment used to build physical controls |
| terminal historical row | `facade_result.terminal_historical_payload` | after physical control | terminal history copied before ACK | yes | no | S6 historical evidence; may contain completion/release changes |
| POST-RETURN current P2 | `facade_result.current_publication` | after controller/physical return | terminal/autoreset meaning not established by S5 | yes | **forbidden** | optional separation diagnostic; only S6 may prove POST-AUTORESET interpretation |
| POST-RETURN next policy state | `second.next_decision_bundle` | after physical return | terminal/autoreset meaning not established by S5 | yes | **forbidden** | optional next-state diagnostic, not transition-2 authority |

No required S5 field is `NOT AVAILABLE`. The existing harness recorder plus existing immutable receipt is sufficient, so the architectural STOP condition is not triggered.

### 15.4 S5 authority hierarchy

```text
A. TRANSITION-2 CONTROL AUTHORITY
   admitted_publication
   -> admitted_effective_assignment (Ak projection)
   -> action_builder controller-time assignment copy

B. CONTINUATION AUTHORITY
   transition-2 decision_bundle.evidence_snapshot
   + forced_continuation_mask
   + forced_action_id/current_owned_task_id

C. POLICY AND MUTATION EVIDENCE
   proposal_envelope
   + resolution source P2/window/generations
   + optional claim_artifact

D. POST-RETURN STATE
   current_publication / next_decision_bundle
   -> separation diagnostic only
   -> never S5 authority
   -> POST-AUTORESET interpretation requires S6 proof
```

P2 remains the sole lifecycle/ownership authority. This hierarchy introduces no second P2, shadow resolver, parallel lifecycle store, or inferred post-hoc assignment.

### 15.5 Exact continuation and controller assertions

After the second receipt returns, future S5 must perform these assertions without reading live wrapper/environment current ownership:

1. The receipt is slot `1`, representing physical transition `2`, and the HARL result is a six-tuple without yet inspecting its done value.
2. Exactly two controller-time recorder entries exist; entry `1` is the transition-2 assignment copy.
3. Require the exact identity chain: the decision bundle and resolution bind `facade_result.source_publication`; a zero-claim result keeps source/post-claim identical, while a claim result advances exactly through its immutable claim artifact; finally `facade_result.admitted_publication is facade_result.post_claim_publication`. Persist canonical publication serials, store versions, episode/transition generations, and source-window serial.
4. Re-project the exact bounded assignment from `admitted_publication`; require equality with `admitted_effective_assignment` and with `control_assignments[1]` over all rows.
5. Define continuation rows only from `second.decision_bundle.forced_continuation_mask[..., 0]`—the transition-2 pre-control classification—not from POST-RETURN ownership.
6. On those rows, require `forced_action_id[..., 0] == evidence_snapshot.current_owned_task_id == admitted_effective_assignment == controller-time assignment`.
7. For a row owned during transition 1 but no longer classified EXECUTING at the transition-2 pre-control snapshot, record its exact pre-control robot/task/ownership facts as `PRECONTROL_CONTINUATION_INELIGIBLE`; do not use a later terminal fact to justify the change.
8. TIME_LIMIT, completion, release, terminal ownership clearing, ACK, autoreset, or a new P2 produced after transition-2 control cannot change the S5 verdict.

The ambiguous prior phrase “unless a frozen lifecycle terminal fact authoritatively changes it” is withdrawn. The replacement rule is:

> For S5 adjudication, only lifecycle facts authoritative before transition-2 controller execution may alter continuation eligibility. Terminal/autoreset facts produced by or after that physical transition cannot retroactively alter its continuation verdict.

### 15.6 Repeated-claim, forced-row, and proposal assertions

- Build `claim_mutated_row_mask[E,M]` only from the immutable claim artifact's selected environment rows and `requested_task_by_robot >= 0`; use all-false when the artifact is `None`.
- Require `claim_mutated_row_mask & continuation_row_mask` to be empty.
- Require every continuation-row resolution/committed interpretation to be `CONTINUE_EXISTING`, never a new-claim/conflict status.
- For each agent, require `actor_call_record.valid_env_indices` to equal exactly the transition-2 policy-row indices and `actor_batch_size` to equal their count. Every continuation row must be absent.
- On continuation rows, require proposal-present and sampled-policy masks false, original proposal ID equal the forced invalid sentinel, and stored logprob equal the forced sentinel while explicitly retaining that the sentinel is not behavior-policy evidence.
- On genuine policy rows, require original proposal IDs, finite original behavior logprobs, decision identity, proposal-source publication serial, OPEN-window serial, and episode/transition generations to remain exact.
- Proposal/effective values may happen to coincide, but effective/controller authority is established only through admitted P2 -> Ak -> controller. A proposal is never promoted to authority by equality.

### 15.7 Future bounded test-only S5 evidence DTO

Future R5-D may define one harness-local immutable DTO, provisionally `PD2S5PreterminalEvidenceV1`, assembled after `collect_step()` returns exclusively from the retained receipt and controller-time recorder:

```text
schema_version
transition_index = 2
transition_slot = 1

preterminal_source_p2_serial
preterminal_source_store_version
preterminal_admitted_p2_serial
preterminal_admitted_store_version
preterminal_episode_generations
preterminal_transition_generations
preterminal_source_window_serial

preterminal_effective_assignment[E,M]
controller_expected_assignment_transition2[E,M]
controller_actual_assignment_transition2[E,M]

continuation_row_mask[E,M]
continuation_expected_task[E,M]
policy_decision_row_mask[E,M]
forced_row_mask[E,M]
forced_noop_row_mask[E,M]
claim_mutated_row_mask[E,M]

original_proposal_ids[E,M]
proposal_logprob_finite_mask[E,M]
proposal_present_mask[E,M]
actor_call_records[M]
resolution_interpretations[E,M]
```

The exact `[E,M]` assignments and masks are already bounded (`E=2`, `M=3`) and are preferable to a hash-only representation. Publication/window identity uses their canonical integer `serial` fields rather than process-local `id(...)`; exact object-identity checks may remain additional in-process evidence. All tensor fields are detached clones made by the test helper or existing immutable DTO accessors. No whole environment, Store, resolver, or lifecycle object is persisted.

This required DTO contains only transition-2 PRETERMINAL and CONTROLLER-TIME evidence. It contains no `post_return_*`, `post_autoreset_*`, `terminal_*`, or `next_episode_*` field. Its builder depends only on the receipt's retained preterminal evidence and the controller-time recorder. It must not call or read `facade_result.current_publication`, `second.next_decision_bundle`, `wrapper.current_p2`, `facade.read_current()`, `domain.current_read_port.read_current()`, environment ownership getters, live generation getters, or a new I1 capture after the second return.

### 15.8 S5 independence theorem and durable checkpoint

If every required preterminal S5 field is present and exact, S5 may PASS even when:

- S6 has not yet been adjudicated;
- the later TIME_LIMIT predicate fails;
- terminal or autoreset semantics are not established;
- post-return current state is absent, unreadable, or intentionally not captured;
- terminal sidecar or historical transport evidence is absent or unavailable.

Future R5-D must construct, validate, and durably persist `PD2S5PreterminalEvidenceV1` and `continuation_second_step_pass` before invoking the external S6 done/reason assertion. The checkpoint payload and its construction/call graph must have no dependency on the optional post-return diagnostic DTO or any S6-only helper. Thus an S5 checkpoint can exist independently while S6 is still `NOT ADJUDICATED`.

### 15.9 Separate optional post-return diagnostic contract

Future R5-D may separately define an immutable, harness-local, test-only DTO named `PD2PostReturnStateDiagnosticV1`:

```text
schema_version
transition_index = 2

post_return_current_p2_serial
post_return_current_store_version
post_return_current_episode_generations
post_return_current_transition_generations

post_return_next_bundle_p2_serial
post_return_next_bundle_episode_generations
post_return_next_bundle_transition_generations

terminal_status_proven = false
autoreset_status_proven = false
```

This DTO may be built after the second `collect_step()` returns from `facade_result.current_publication` and `second.next_decision_bundle`. It is optional, bounded test evidence only: it is not required for S5 PASS and is not P2, lifecycle, controller, resolver, learner, or buffer authority. Absence or unreadability cannot retroactively fail S5.

The two `*_status_proven` values record capture-time status and therefore remain false in this immutable DTO. A later successful S6 adjudication records its proof in a separate S6 evidence/checkpoint object; it does not flip these fields.

Before S6 done/reason and terminal/autoreset evidence PASS, every such field remains temporally qualified as `post_return_current_*` or `post_return_next_*`. `post_return` means only “observed after the call returned”; it does not prove terminal or autoreset semantics. Names such as `post_autoreset_*` are forbidden in the S5 DTO and premature in the post-return DTO.

After S5 PASS, S6 done/reason PASS, and terminal/autoreset evidence confirms that the observed current publication is the new episode state, S6 may reference the unchanged post-return DTO under an S6-specific interpretation as proven `post_autoreset_current_*` evidence. It must not rename or mutate the DTO in place, mutate the prior S5 DTO, or rewrite the durable S5 artifact.

### 15.10 Required architecture and temporal interpretation

```text
TRANSITION 2

PRETERMINAL CONTROL EVIDENCE
  decision_bundle
  proposal_envelope
  resolver / optional B1 claim artifact
  admitted P2
  Ak effective assignment
  CONTROLLER-TIME assignment copy
              |
              v
      PD2S5PreterminalEvidenceV1
              |
              v
           S5 PASS
    continuation_second_step_pass
              |
              v
       POST-RETURN RECEIPT
              |
              +--> optional PD2PostReturnStateDiagnosticV1
              |      post_return_current_*
              |      post_return_next_*
              |      (not S5 authority)
              |
              v
        S6 done/reason PASS
              |
              v
    terminal/autoreset evidence PASS
              |
              v
same immutable post-return evidence may be interpreted by S6
as proven post_autoreset_current_* evidence
```

The S5 artifact remains immutable across the entire lower branch. An S6 failure leaves S5 PASS intact and leaves post-return state unpromoted.

### 15.11 S5/S6 dependency table

| Evidence | Required for S5? | Required for S6? | Available PRETERMINAL? | Available POST-RETURN? | Authority role |
|---|---:|---:|---:|---:|---|
| transition-2 `decision_bundle` | yes | no | yes | retained in receipt | S5 continuation/row-class/decision identity |
| `admitted_publication` | yes | no | yes, before controller | retained in receipt | primary S5 P2 control authority |
| `admitted_effective_assignment` | yes | no | derived before controller | retained clone | S5 Ak projection of admitted P2 |
| controller-time assignment copy | yes | no | yes, inside `action_builder` | retained by test recorder | observed transition-2 controller input |
| claim artifact | yes when claim exists; exact zero-artifact otherwise | no | yes | retained in facade result | S5 ownership-mutation evidence only |
| proposal envelope | yes for policy/forced-row proof | no | yes | retained in receipt | original proposal/logprob evidence; never effective authority |
| `current_publication` | no | conditional separation evidence | no | yes | optional POST-RETURN diagnostic; S6 may later prove post-autoreset meaning |
| `next_decision_bundle` | no | conditional separation evidence | no | yes | optional POST-RETURN next-policy-state diagnostic |
| terminal historical payload | no | yes | no | yes after internal terminal handoff | S6 authoritative pre-reset historical evidence |
| exact ACK evidence | no | yes | no | yes after safe historical copy | S6 runtime terminal-slot lifetime evidence only |
| timeout critic evidence | no | yes | no | yes after terminal transport | S6 TIME_LIMIT bootstrap-input evidence |
| I5a buffer transport | no | yes | no | yes after terminal transport | S6 learner/buffer insertion evidence |
| I5b returns/GAE/ValueNorm | no | yes | no | yes after I5a inputs | S6 learner semantics evidence |

“Available POST-RETURN” does not itself mean POST-AUTORESET. That interpretation requires the S6 proof chain described above.

### 15.12 S5 PASS, failure, and no-retroactive-influence rule

S5 PASS requires all of the following before any external S6 assertion:

- immutable transition-2 preterminal authority is present;
- admitted P2 -> Ak assignment -> controller-time assignment is exact;
- transition-2 continuation rows retain their pre-control owned task;
- continuation rows are neither re-claimed nor actor sampled;
- genuine policy rows preserve original proposal/logprob and source identity;
- proposal/effective authority separation is exact;
- the required S5 DTO contains only preterminal/controller-time evidence;
- the bounded DTO and `continuation_second_step_pass` checkpoint are durably persisted.

Missing preterminal evidence stops as:

```text
classification: PD2-STOP-PHYSICAL-STEP-FAIL
detail:         S5_PRETERMINAL_EVIDENCE_UNAVAILABLE
```

Controller/P2/Ak/continuation/repeated-claim/proposal-effective mismatches retain `PD2-STOP-PHYSICAL-STEP-FAIL` with a precise `S5_*` detail. A forced continuation row entering actor sampling retains `PD2-STOP-ACTOR-FORWARD-FAIL / S5_FORCED_ROW_BYPASS`. No new STOP class is introduced, and no missing evidence may be reconstructed from POST-RETURN current state.

Missing/unreadable optional post-return diagnostics, unproven autoreset, or unavailable terminal evidence do not fail S5. They are adjudicated only after S5 under the precise S6 terminal/separation boundary. A later S6 failure never changes the already persisted S5 verdict.

**NO RETROACTIVE TERMINAL INFLUENCE RULE:** once transition-2 controller execution has occurred, later TIME_LIMIT, terminal sidecar, ACK, autoreset, new generation, or new P2 evidence cannot change what effective assignment controlled transition 2. Those later facts are independently adjudicated under S6.

## 16. S6 terminal-entry contract

Only after durable S5 PASS may the harness adjudicate S6:

```text
S6-A terminal predicate:
  second HARL done matrix is true for every required row
  buffer slot 0 reason == NONE
  buffer slot 1 reason == TIME_LIMIT

S6-B terminal evidence:
  authoritative pre-reset sidecar present
  terminal history != post-autoreset current state
  safe historical copy before exact runtime ACK
  runtime terminal slots absent after ACK
  timeout critic exact-once input match
  I5a buffer fields and bootstrap values exact
  I5b returns/GAE/ValueNorm semantics exact
  recorder-only trainer seams exact
  buffer rollover exact
```

Important execution/adjudication distinction: frozen I6 performs terminal-info attachment and collector/buffer work inside `collect_step()` before returning the receipt. R5-C does not and cannot delay that internal atomic execution without reopening I0-I6. “S5 before S6” therefore governs external durable adjudication and PASS claims:

- if S5 fails, S6 is `NOT ADJUDICATED`, even if frozen internal transport work already occurred;
- if S5 passes but done/reason fails, terminal transport is not claimed PASS;
- only after done/reason passes may the harness inspect and certify the already-produced terminal artifacts.

This distinction closes the evidence-order problem without changing terminal runtime semantics.

## 17. S2 bounded critic-input fingerprint design

Future instrumentation attaches to the actual `obs` argument entering the first `CriticRecorder.get_values()` call, before calling `self.wrapped.get_values(...)`.

Algorithm ID:

```text
PD2_TORCH_CPU_CONTIGUOUS_RAW_BYTES_SHA256_V1
```

Capture sequence:

1. inspect the actual input tensor's shape, stride, dtype, device, contiguous state, finiteness, `numel`, and `requires_grad`;
2. use `obs.detach()`; do not clone or modify the CUDA source;
3. make one diagnostic CPU copy preserving dtype and logical values;
4. make the CPU copy C-contiguous;
5. hash exactly `cpu_tensor.numpy().tobytes(order="C")` with SHA-256;
6. store only bounded metadata and the digest, not the full tensor;
7. emit a durable `first_real_vcritic_input_captured` checkpoint;
8. call the wrapped VCritic exactly once with the original unchanged CUDA tensor.

For the reviewed `[2,418]` float32 input:

```text
numel: 836
raw bytes: 3,344
```

Required durable fields:

```text
fingerprint_algorithm
content_sha256
shape
stride
dtype
device
contiguous
finite
requires_grad
numel
nbytes
CPU byte order
RNN state shape
mask shape
capture index
```

The device-to-host copy is read-only and introduces a synchronization point. This is disclosed, not hidden. The existing recorder already performs a pre-forward CUDA finiteness reduction followed by `.item()`, so S2 already contains a pre-forward synchronization boundary. The fingerprint adds no model invocation, no observation recomputation, no dtype conversion, no gradient edge, no seed call, and no actor reordering.

## 18. Runtime-class evidence design

Persist:

```text
critic_runtime_class =
  type(self.wrapped).__module__
  + "."
  + type(self.wrapped).__qualname__
```

Expected current diagnostic identity:

```text
harl.algorithms.critics.v_critic.VCritic
```

Also persist effective hidden sizes `[256,256]` from the frozen construction evidence. These fields are diagnostic identity only; they do not enter HARL math, checkpoint semantics, or training state.

## 19. Formal STOP mapping

No eleventh class is introduced.

| Failure | Existing class | Boundary/detail |
|---|---|---|
| timing fixture setup/assertion | `PD2-STOP-PHYSICAL-STEP-FAIL` | `S1_TIMING_FIXTURE_CONTRACT` |
| required transition-2 preterminal S5 evidence unavailable | `PD2-STOP-PHYSICAL-STEP-FAIL` | `S5_PRETERMINAL_EVIDENCE_UNAVAILABLE` |
| second controller/P2/Ak/continuation/repeated-claim/proposal-effective failure | `PD2-STOP-PHYSICAL-STEP-FAIL` | precise `S5_*` boundary |
| forced continuation/noop row enters actor sampling | `PD2-STOP-ACTOR-FORWARD-FAIL` | `S5_FORCED_ROW_BYPASS` |
| S5 fails | corresponding class above | S6 `NOT ADJUDICATED` |
| S5 passes, second done/reason fails | `PD2-STOP-TERMINAL-TRANSPORT-FAIL` | `S6_TIME_LIMIT` |
| optional POST-RETURN diagnostic or terminal/current separation fails after S5 PASS | `PD2-STOP-TERMINAL-TRANSPORT-FAIL` | precise `S6_<separation boundary>` |
| later sidecar/ACK/I5a/I5b/GAE failure | `PD2-STOP-TERMINAL-TRANSPORT-FAIL` | existing precise `S6_*` boundary |
| required S2 input capture or pre-forward persistence fails | `PD2-STOP-VCritic-CUDA-FAIL` | `S2_CRITIC_INPUT_EVIDENCE` |

The S2 mapping is fail-closed because no existing class names a critic evidence-contract failure and this instrumentation is located at the critic-side CUDA/input boundary. Its exception detail must say whether failure occurred in CUDA observation, CPU-byte capture, hashing, class identity, or persistence, and must not falsely claim that the VCritic forward itself failed. If capture fails before the forward, persist `VCritic forward attempts: 0`.

## 20. Future R5-D static/synthetic matrix

R5-D must remain test-only and run no AppLauncher/Isaac runtime.

| ID | Static/pure case | Required result |
|---|---|---|
| A | derived midpoint fixture with production-like float arithmetic | strict bucket interior; `ceil == 3` |
| B | synthetic timeline from buffer 0 | transition 1 nonterminal; transition 2 TIME_LIMIT |
| C | historical `dt=1/60`, decimation 6, multiplier 3 | duration `0.30000000000000004`; ratio >3; `ceil == 4` |
| D | constructed actual max length differs from 3 | early `S1_TIMING_FIXTURE_CONTRACT` STOP before reset/step |
| E | second receipt path | S5 assertions occur before S6 assertions |
| F | S5 continuation failure | S5 first boundary; S6 not adjudicated |
| G | S5 PASS plus done/reason failure | `S6_TIME_LIMIT` first boundary |
| H | S5 and terminal predicate PASS | terminal evidence adjudication entered |
| I | same critic tensor captured twice by pure helper | identical digest |
| J | one tensor value changes | digest changes |
| K | fingerprint capture | source tensor values/version/grad contract unchanged |
| L | runtime-class formatting | deterministic module-qualified class name |
| M | instrumented recorder call | exactly one wrapped VCritic invocation |
| N | preterminal task X controls transition 2; S6-proven POST-AUTORESET P2 differs | S5 PASS; later P2 is ignored as S5 authority |
| O | preterminal admitted P2 projects task X, controller recorder contains task Y, POST-RETURN P2 happens to contain Y | S5 `S5_P2_AK` failure; POST-RETURN state cannot rescue it |
| P | preterminal continuation is exact; same transition later TIME_LIMIT-clears ownership | S5 PASS; S6 adjudicates the terminal ownership change separately |
| Q | static S5 helper source/call graph | no live current-P2/ownership/generation query and no dependency on any POST-RETURN diagnostic helper |
| R | all required S5 preterminal evidence is complete/exact; S6 is not adjudicated; optional POST-RETURN diagnostic is absent | S5 PASS; `continuation_second_step_pass` persisted; S6 remains `NOT ADJUDICATED` |
| S | receipt contains `current_publication` and `next_decision_bundle`, but S6 TIME_LIMIT has not passed | fields may be captured only as `post_return_current_*` / `post_return_next_*`; no S5 influence |
| T | S5 PASS; POST-RETURN current state exists; S6 done/reason fails | S5 remains PASS; first S6 boundary is `S6_TIME_LIMIT`; evidence is never promoted to proven POST-AUTORESET |
| U | S5 PASS; S6 terminal/autoreset PASS; terminal history is prior state and POST-RETURN current publication is a new generation/P2 | S5 remains unchanged; S6 proves historical/current separation and may interpret the unchanged diagnostic as POST-AUTORESET evidence |

Static guards additionally reject:

- a third `collect_step`;
- `1e-6`, `1e-9`, machine-epsilon, or `nextafter` fixture hacks;
- changes to DirectMARLEnv timeout arithmetic or increment order;
- S6 done assertion before the S5 PASS checkpoint;
- any S5 equality against `facade_result.current_publication`, `next_decision_bundle`, wrapper current P2, or live environment ownership;
- any `post_return_*`, `post_autoreset_*`, `terminal_*`, or `next_episode_*` field in `PD2S5PreterminalEvidenceV1`;
- any S5 DTO/checkpoint construction dependency on `facade_result.current_publication`, `second.next_decision_bundle`, or an S6/post-return diagnostic helper;
- any in-place relabeling or mutation of POST-RETURN evidence or the prior S5 artifact during S6 interpretation;
- ambiguous S5 DTO field names such as unqualified `current_p2`, `current_assignment`, or `current_generation`;
- a second VCritic call, dummy critic, recomputed observation, dtype conversion, or actor-before-critic reordering;
- any new STOP taxonomy member.

## 21. No runtime and no mutation statement

```text
formal worker:                    0
AppLauncher / SimulationApp:      0 / 0
Isaac / CUDA forward:             0 / 0
HARL / VCritic / actor:           0 / 0 / 0
environment construct/reset/step: 0 / 0 / 0
optimizer / backward:             0 / 0
training/playback/evaluation:     0 / 0 / 0
formal retry:                     0

formal harness changes:           NONE
production changes:               NONE
DirectMARLEnv changes:             NONE
I0-I6 changes:                     NONE
installed HARL changes:            NONE
R5-B/R5-A/R4/R3/R2/PD1 changes:   NONE
Kit/Junction/cache/baseline:       UNCHANGED
commit:                            NONE
```

R5-C-TR2 changes documentation only: this authoritative report and the concise top-level `TASK_PROGRESS.md` handoff.

### Protected-integrity evidence

The following SHA-256 values were captured before the documentation edit and compared again after it. Every protected row is exact:

| Protected artifact | SHA-256 before and after |
|---|---|
| formal PD2 harness | `e54d31e8b2c613fdb91d7ae0c7a71f43bd00cedf2810375fc35039eeb46cf486` |
| DirectMARLEnv | `7f7714a6f32e24ce34ef184cb9eed87cc36d4db0744c44a816ce3da9cc505f31` |
| scan environment | `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363` |
| dormant learned route | `b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b` |
| R5-B report | `5bb3d68ac50c9e788de4ace060b8938ed72a212f2b16703f042b86e7ab6cbd59` |
| R5-A report | `d98c1d3567654dc3ade38808526f83b0db5f4761b567ab986134b2a28406d2d1` |
| R4 design/descriptors | `30f9233c35d43d22e7bc50e11b61371e1d7be376a0f64c5ad75072665e211ce1` |
| R3 report | `787ea307068a8223031ecdf64ab37e9a351a87461c35cf8a6a166215f788e136` |
| R2 report | `843b392ab0ed81330c89c39c007d524bc1f4cb27eb8df7ba4d47a6a97ad74390` |
| PD1 design | `242b782e92634d746a45b93f814b6e14286e6f46f0b85f953483924c4570fd5e` |
| D4-O report | `eda1524388d6eff6858a52c7b2815956d8e008c69958452ac2e76ef441b86e70` |
| D4-CI report | `ced5867e7eefdf7618a89861122562a83cc62a488ac77a0a4d0fa67109e32209` |

R5-C-TR2 captured and compared the same expanded 39-file before/after set covering DirectMARLEnv, the environment/wrapper/training path, lifecycle/runtime/facade/receipt modules, the I0-I6 policy/critic/terminal modules, the formal harness, installed HARL actor/critic/buffer/runner/ValueNorm sources, and every protected historical report named by this slice. Result: `39/39 EXACT`.

No write command targeted production, DirectMARLEnv, I0-I6, installed HARL, the formal harness, historical reports, Kit, Junctions, cache, or baselines. `git diff --check` exits `0`; its only output is pre-existing working-tree line-ending warnings.

## 22. Recommended next slice

Stop for GPT independent design review.

Only after R5-C-TR2 review PASS and separate user authorization may the next candidate begin:

```text
B2-V2-PD2-R5-D
Test-Only S5/S6 Timing Fixture
and Pre-Terminal S5 Evidence
+ Post-Return Diagnostic Separation
+ S2 Fingerprint Implementation
+ Static/Synthetic Verification
```

R5-D may modify only the test-only formal harness and may not run AppLauncher, Isaac, CUDA forward, HARL, or formal PD2. A later R5-E would require separate authorization for exactly one formal re-entry.

R5-C-TR2 completion means only that required S5 evidence is structurally independent from POST-RETURN, TERMINAL, and POST-AUTORESET evidence. It does not mean the harness is modified, S5/S6/terminal transport/Snapshot B pass, B2-V2 is closed, or any readiness gate is open.

Final status:

```text
classification:       PHASE-B2-V2-PD2-R5C-TARGETED-S5-POSTSTATE-SEPARATION-REVISION-COMPLETE-AWAITING-GPT-REVIEW
R5-C-TR2:             SECOND TARGETED REVISION COMPLETE / AWAITING GPT REVIEW
R5C-S5-AUTHORITY-01:  CLOSED
R5C-S5-POSTSTATE-02:  CLOSED
timing fixture:       FROZEN / NOT IMPLEMENTED
S5 evidence authority:PRETERMINAL / IMMUTABLE / FROZEN / NOT IMPLEMENTED
S5 required DTO:      PRETERMINAL ONLY / NOT IMPLEMENTED
post-return diagnostic:SEPARATE / OPTIONAL / NOT IMPLEMENTED
post-autoreset meaning:S6-DEPENDENT
S5/S6 ordering:       FROZEN / NOT IMPLEMENTED
S2 evidence hardening:FROZEN / NOT IMPLEMENTED
B2-V2:                STOPPED / INCOMPLETE
S5:                   NOT YET ADJUDICATED
S6 terminal transport:NOT YET REACHED
runtime/policy/learner:BLOCKED
public route:          DORMANT / BLOCKED
B2-R / training:       NOT AUTHORIZED / NOT AUTHORIZED
commit:                NONE
```

Stop here.
