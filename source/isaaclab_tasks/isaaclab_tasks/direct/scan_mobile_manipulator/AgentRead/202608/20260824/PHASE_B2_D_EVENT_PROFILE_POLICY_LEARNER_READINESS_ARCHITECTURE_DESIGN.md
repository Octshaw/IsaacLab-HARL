# Phase B2-D Event-Profile Policy / Learner Readiness Architecture Design

Date: 2026-08-24

Repository: `E:\Project\IsaacLab_HARL`

Working label: `B2-D` (retained; no historical phase nomenclature is rewritten)

## 1. Classification

```text
classification:
  PHASE-B2-D-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

design:
  REVISED / AWAITING GPT REVIEW

implementation:
  NOT STARTED
Isaac:
  NOT RUN
HARL:
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

This is a targeted revised design result, not an implementation or runtime-readiness
claim. The source audit found no fundamental need to modify `DirectMARLEnv`,
reopen P2/Ak authority, make installed HARL mutable, or adopt variable
cardinality. Therefore the current result is **not**
`PHASE-B2-D-STOP-ARCHITECTURAL-DEPENDENCY-GAP`.

One mandatory pre-implementation contract reconciliation was found: the Phase-A
schema/DVM DTOs still contain `assignment_tick_generation`, while the committed
runtime architecture has no assignment tick and defines the exact OPEN window
as an opaque window identity, not a tick. Section 10 and slice B2-I0 define a
versioned, no-tick resolution. If independent review forbids such a versioned
amendment, implementation must stop with the designated architectural-gap
classification; it must not invent a clock or alias the OPEN window to a tick.

This targeted revision follows `PHASE-B2-D-CONDITIONAL-PASS`, not a final GPT
review pass. It closes five documentation-level issues before a second
independent review: TIME_LIMIT
bootstrap projection, full-index HAPPO factor updates, the immutable I1/I2
bundle boundary, identity-metadata/model-input separation, and narrower I3/I5
implementation slices. This status is not a review pass and authorizes no
implementation.

| Conditional-review issue | Authoritative revised location |
|---|---|
| terminal audit metadata versus TIME_LIMIT critic bootstrap | Sections 8 and 13–16; B2-I4/I5a/I5b |
| full-rollout HAPPO factor indexing | Section 11.4; B2-I3b |
| immutable I1 evidence versus I2 decision bundle | Sections 7–9; B2-I1/I2 |
| validation identity versus model input | Sections 7–9; B2-I0/I1 |
| oversized I3/I5 slices | Sections 17–18; B2-I3a/I3b and I5a/I5b |

## 2. Committed starting checkpoint / HEAD

The read-only preflight established:

```text
branch:      main
tracking:    origin/main
HEAD:        14993dee344bade0230d2eb97b5f22171331f44a
subject:     feat(mrta): complete lifecycle runtime backbone and wrapper integration
worktree:    clean at design-phase entry
```

The user-provided phase authority closes B1W-I4-4 as `GPT REVIEW PASS / CLOSED`.
The committed Lifecycle Runtime Backbone + Wrapper Integration checkpoint is
therefore the starting point, not work to reopen. Phase B as a whole remains
incomplete.

The `worktree: clean at design-phase entry` record above describes the original
B2-D audit entry. At targeted-revision entry, HEAD was still exactly the same;
the only pending paths were this uncommitted design report and the authorized
`TASK_PROGRESS.md` documentation delta. No production/test/config/checkpoint
delta was present or added.

The current authority chain remains frozen:

```text
actor action = original proposal
proposal adapter / arbitration = transaction-candidate construction
M1 / B1 = ownership mutation transaction
current P2 = sole current lifecycle / ownership truth
final current P2 -> Ak -> physical controller
```

Terminal history remains the previous episode final transition; current actor
state remains the post-autoreset episode. `ATOMIC_BATCH_EXACT_ACK` ends only the
runtime terminal-slot lifetime.

## 3. Source files audited

The audit was static and read-only. The authoritative progress file and its
current reports were read first:

- `AgentRead/TASK_PROGRESS.md`
- `AgentRead/202608/20260824/PHASE_B1W_I4_4_FOCUSED_REAL_ISAAC_WRAPPER_INTEGRATION_VERIFICATION_REPORT.md`
- `AgentRead/202608/20260824/PHASE_B1W_I4_3_TERMINAL_WRAPPER_HISTORICAL_COPY_AND_ATOMIC_BATCH_ACK_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260824/PHASE_B1W_I4_2_PROPOSAL_INTERPRETATION_AND_EFFECTIVE_COMMIT_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260823/PHASE_B1W_I4_1_EVENT_FACADE_COMPOSITION_RESET_CONTINUATION_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260823/PHASE_B1W_I4_D_WRAPPER_FACADE_AND_EFFECTIVE_COMMIT_INTEGRATION_TARGETED_DESIGN.md`

Repo-local production and contract sources audited:

- `assignment_harl_wrapper.py`
- `assignment_rl_interface.py`
- `assignment_harl_adapter.py`
- `assignment_harl_training.py`
- `assignment_profile_contract.py`
- `assignment_event_profile_schema_contract.py`
- `assignment_mrta_contract.py`
- `assignment_lifecycle_transition_contract.py`
- `assignment_initial_claim_runtime.py`
- `assignment_lifecycle_transaction_runtime.py`
- `assignment_event_profile_runtime_domain.py`
- `assignment_event_profile_synchronous_runtime.py`
- `assignment_event_runtime_facade.py`
- `assignment_event_proposal_adapter.py`
- `assignment_event_terminal_transport.py`
- `scan_mobile_manipulator_env.py`
- `source/isaaclab/isaaclab/envs/direct_marl_env.py`
- `agents/harl_happo_cfg.yaml`

Relevant static fixtures were inspected, including the Phase-A contracts,
I4-1 through I4-4 fixtures, fixed Discrete-shape fixture, and the existing
synthetic actor/critic/buffer readiness fixture. No fixture was executed.

Installed HARL sources audited under
`C:\isaacenvs\isaac45_harl\Lib\site-packages\harl` (installed metadata reports
HARL 1.0.0):

- `runners/on_policy_base_runner.py`
- `runners/on_policy_ha_runner.py`
- `common/buffers/on_policy_actor_buffer.py`
- `common/buffers/on_policy_critic_buffer_ep.py`
- `algorithms/actors/happo.py`
- `algorithms/critics/v_critic.py`
- `models/policy_models/stochastic_policy.py`
- `models/base/act.py`
- `models/base/distributions.py`

## 4. Current runtime/readiness state

The checkpoint has two deliberately different readiness statements:

1. The lifecycle runtime backbone is committed and real-Isaac verified for the
   private WR-C route, including reset, continuation, proposal/M1, terminal
   historical copy, atomic ACK, autoreset separation, and recovery.
2. The learned-policy event profile remains `INTERFACE_ONLY`; public policy
   stepping, learner transport, and training readiness remain blocked.

The source enforces the second statement:

- `assignment_profile_contract.py:781-795` defines the event profile as
  `INTERFACE_ONLY`, training `PHASE_A_BLOCKED`, and playback `BLOCKED`.
- `assignment_profile_contract.py:1222-1250` rejects the event profile at the
  generic runtime-readiness gate.
- `assignment_harl_wrapper.py:326-405` labels event actor obs, shared obs, and
  mask as provisional/not implemented.
- `assignment_harl_wrapper.py:636-645` rejects public event `step()` before
  environment mutation.
- `assignment_harl_wrapper.py:831-834` rejects event action-mask production.
- `assignment_harl_training.py:265-325` gates before `gym.make()` and does not
  compose the event domain/O1/facade route.

No readiness enum or public gate may be changed merely because an individual
module is later implemented.

## 5. Remaining blockers after source audit

The original blocker set remains valid and is refined as follows:

1. Canonical lifecycle-aware actor observation is absent.
2. Canonical global centralized/shared observation is absent.
3. The Phase-A tick-bound schema identity must be reconciled with the no-tick
   runtime identity.
4. Lifecycle legality, DVM, row class, and forced action must be produced from
   one exact snapshot.
5. Installed HARL currently samples every actor on every environment row.
6. Forced rows cannot be made PPO/HAPPO-neutral using current `active_masks`
   alone.
7. Original proposal/logprob has no event learner ledger or fixed-row binding.
8. The terminal artifact and historical DTO still hardcode
   `optional_sidecar=None`.
9. The public training facade discards wrapper `info` and therefore cannot
   transport terminal history or truncation identity.
10. Current HARL `proper_time_limits=True` does not provide the required
    pre-reset TIME_LIMIT bootstrap.
11. Public event composition and policy step remain gated.
12. A focused learned-route Isaac/HARL interface smoke and final readiness
    review have not occurred.
13. Installed eval/play routes also sample every row; the current repo runner
    delegates eval-env creation to a path with no assignment-event composition,
    while the YAML default has `eval.use_eval=true`. Event startup must either
    use one row-aware repo-local eval assembler or fail closed with eval
    explicitly disabled; it must not silently enter the installed route.

Two source-quality constraints are also blockers to a truthful policy schema:

- `get_assignment_problem()` exposes explicit `feasible_mask`, but it is the
  current assignment feasibility base, not a runtime path-planner result.
- `cost_matrix` is scanner-to-viewpoint Euclidean distance
  (`scan_mobile_manipulator_env.py:1809-1817`), not nominal remaining execution
  time. Finite cost must not be treated as feasibility or mislabeled as a path
  cost.

These are producer/readiness dependencies, not permission to choose any of the
11 numeric TBDs in this design.

## 6. AssignmentHarlWrapper and RL-interface audit

### 6.1 Exact reset/step structures

The exact-event private reset path is:

```text
facade.reset()
-> raw env reset returns (obs_mapping, extras)
-> wrapper returns (obs_dict, shared_obs, None)
```

`assignment_harl_wrapper.py:602-620` implements this. The current event actor
obs is raw environment obs; shared obs is raw actor concat repeated across the
agent axis; the mask slot is deliberately `None`.

The existing-profile public step returns:

```text
obs:               dict[agent -> Tensor[E,O]]
share_obs:         Tensor[E,M,S]
rewards:           Tensor[E,M,1]
dones:             Tensor[E,M]
info:              mapping
available_actions: Tensor[E,M,N+1]
```

Its ordering at `assignment_harl_wrapper.py:646-740` is pre-step problem/mask,
decode, legacy resolver, effective assignment/controller, env step, post-step
problem, and returned current obs/shared/mask. That route must not be reused as
event lifecycle authority.

### 6.2 Current actor and shared observations

For M=3, the task env raw actor observation is 96D. It contains own physical
state/capability, nearest-eight dynamically repacked task slots, other scanner
positions, coverage, and the previous 9D low-level action
(`scan_mobile_manipulator_env.py:2972-3019`). It has no stable global task ID for
the nearest slots and cannot align to global Discrete actions `0..N`.

`scan_mobile_manipulator_env.py:3045-3048` and
`assignment_harl_wrapper.py:1204-1225` only concatenate raw actor obs for the
current critic state. This is not the Phase-A global centralized schema and is
not a valid terminal sidecar source.

### 6.3 Available actions and decode

`assignment_rl_interface.py:11-37` only converts
`problem["available_mask"]` to float and appends an always-on noop. It has no
P2, lifecycle, ownership, failed-pair, row-class, or DVM semantics and cannot be
the event mask authority.

`decode_discrete_assignment()` at lines 40-95 is reusable as a scalar-ID
boundary: it accepts `[E,M,1]` or `[M,E,1]`, validates finite integer IDs in
`0..N`, and maps raw noop ID N to decoded `-1`, producing `[E,M]`.

Legacy validators at `assignment_harl_wrapper.py:1345-1408` and
`assignment_harl_training.py:397-409` require noop on every row and forbid
all-zero rows. Event semantics need a separate validator because EXECUTING has
current-task-only/noop-false semantics, while terminal historical state has no
action row and an all-false semantic mask.

### 6.4 Proposal storage and terminal private result

The I4-2 decision snapshot already binds exact current P2 publication identity,
episode generation, transition generation, exact OPEN window identity, and
cloned feasibility/cost evidence (`assignment_event_proposal_adapter.py:192-482`).
Before resolve/commit, it revalidates those identities and never rebinds stale
evidence (`assignment_event_proposal_adapter.py:685-774`).

Wrapper `last_assignment_proposal` and related fields are bounded post-success
diagnostics only. The wrapper has no actor-logprob storage interface, and none
of these caches may become proposal, ownership, effective-assignment, or
controller authority.

The facade's terminal result carries a bounded historical tuple distinct from
the raw post-autoreset current result. Both runtime artifact and historical DTO
still hardcode `optional_sidecar=None`:

- `assignment_lifecycle_transaction_runtime.py:2853-3015`
- `assignment_event_terminal_transport.py:110-259`

The I4-3 copy-before-ACK lifetime is otherwise already the correct transport
foundation.

### 6.5 Assignment-problem feature sources

`scan_mobile_manipulator_env.py:1800-1872` returns current device-resident
physical tensors: base/scanner pose, task pose, robot capabilities, coverage,
static/explicit feasibility masks, available mask, and `[E,M,N]` geometric
cost. These are physical/problem inputs only.

Its `task_status` is merely an unassigned/completed placeholder and
`robot_status` is initialized entirely to legacy idle. They are not event
lifecycle sources. Event task state, robot state, ownership, failed pairs,
completion attribution, and termination reason must come only from current P2.

## 7. Actor observation design

### 7.1 Design rule

Do not append lifecycle bits to the raw nearest-eight observation. The event
actor input must be one canonical, fixed-M/fixed-N, global-ID projection built
once inside the immutable B2-I1 `EventPolicyEvidenceSnapshot`. It is an
observation projection, never a second state store. B2-I2 derives DVM and row
semantics from that exact snapshot without recapturing state; DVM remains the
separate `available_actions`/policy-participation interface and is not fed back
into the I1 actor tensor.

The Phase-A 15-block fixed-width boundary remains the starting layout
(`assignment_event_profile_schema_contract.py:274-368`), with actor dimension:

```text
O = 6*M*N + 30*M + 14*N + 2
M=3, N=12 -> O=476
```

B2-I0 must issue a new semantic/schema version for the no-tick runtime binding;
it must not silently reinterpret the existing v1 generation key. The formula
above is a v1 audit reference, not a v2 compatibility requirement. B2-I0 must
derive the v2 dimension from real semantic fields after removing tick/identity
features. No learned event-profile checkpoint exists, so semantic correctness
takes priority over artificial shape preservation. If a reviewed compatibility
slot is retained, it must be constant and explicitly nonsemantic; it must never
carry a generation, window identity, or renamed serial.

### 7.2 First-paper required feature boundary

| Feature | Authoritative/current source | B2 treatment |
|---|---|---|
| actor robot identity | fixed ordered agent list | required one-hot |
| robot physical state/capability | task-env physical snapshot | required, normalized fixed table |
| robot lifecycle state | current P2 | required 4-state one-hot |
| robot availability | current P2 robot state | required; `UNAVAILABLE` false |
| current owned task | inverse of P2 active ownership | required one-hot over N+noop; fail if non-unique |
| task lifecycle state | current P2 | required 6-state one-hot |
| task ownership | current P2 | required task-to-owner one-hot |
| cumulative failed pair | current P2 | required `[M,N]` mask |
| completion/progress | P2 completion count + env episode progress | required, normalized |
| explicit physical feasibility | cloned task-env explicit mask | required legality provenance |
| path validity / path cost | separately validated producer | typed external seam when reviewed v2 requires it; never inferred from finite cost |
| current ranking cost | cloned current geometric cost | may be exposed only under an explicit geometric-cost semantic version |
| action mask / row context | B2-I2 decision bundle | required separate actor API / ledger context; not an I1 model feature |
| workload | P2 completion attribution | required completed-task fraction |

The P2 fields are already available as immutable/no-alias tensors through
`LifecycleStateSnapshot` and the current publication: task/robot state,
ownership, cumulative failed pairs, completion counts, termination reason, and
episode/transition identity (`assignment_lifecycle_transaction_runtime.py:504-610`,
`assignment_initial_claim_runtime.py:350-442`).

The following are explicitly deferred from the first policy interface:

- prior low-level action;
- attempt count/age, repeated selection, cooldown, retry history;
- raw lifecycle event records and raw generation counters as model inputs;
- same-step proposal, resolver winner, effective assignment, or actor logprob;
- transfer/preemption features and penalties;
- Transformer, GNN, Set Transformer, and variable cardinality;
- arbitrary-cardinality checkpoint compatibility.

Local/top-k and nominal path-cost blocks may remain typed input seams, but their
producers are external future dependencies, not implicit B2-I0/I1/I2 work. A
public learned route must remain blocked until each producer contract is either
implemented or a separately reviewed v2 profile explicitly omits it. This
design does not choose their numeric parameters. The environment geometric
`cost_matrix` is ranking distance, not nominal path time/cost; finiteness is
never physical feasibility.

### 7.3 Temporal boundary

The current actor observation describes the current post-event/pre-policy P2
and current physical snapshot. It must not include the outcome of the proposal
being sampled. A terminal step returns post-autoreset current obs for the next
episode; previous-episode final state is available only through terminal
history/sidecar.

## 8. Shared / centralized critic observation design

The critic input is a canonical global semantic state `[E,S]`, repeated only at
the HARL transport boundary to `[E,M,S]`. It is not actor-observation concat.
For EP HARL, the runner stores and evaluates `share_obs[:,0]`.

The existing 19-block shared boundary at
`assignment_event_profile_schema_contract.py:482-614` is the v1 audit starting
point only:

```text
S = 6*M*N + 31*M + 15*N + 8
M=3, N=12 -> S=497
semantic state: [E,S]
HARL transport: [E,M,S]
critic input:   [B,S]
```

The B2 v2 critic projection uses the same I1 physical/lifecycle/ownership/
failed/workload/progress evidence, stores global blocks once, and excludes raw
publication/window/generation identities. The formula above does not force v2
to preserve `S=497`; B2-I0 derives `S_critic` from semantic critic inputs.

Termination reason is authoritative audit/learner metadata, not a numerical
critic feature. Three typed projection modes keep that distinction exact:

| Projection mode | Source and content | May be passed to critic? |
|---|---|---:|
| `CURRENT_POLICY_CRITIC` | current physical state + current P2 lifecycle semantics | yes |
| `TERMINAL_AUDIT` | finalized pre-reset state + exact final reason for historical evidence | no |
| `TIME_LIMIT_BOOTSTRAP_CRITIC` | the exact same finalized pre-reset physical/P2 state and transition identity, projected through the ordinary critic feature schema with no terminal-only reason | yes, TIME_LIMIT only |

The authoritative reason remains in the terminal artifact, bounded historical
DTO, audit projection, and `termination_reason` buffer field. It is not removed
or rewritten. If a v2 transport keeps a reserved reason-shaped compatibility
block in critic tensors, that block is a constant/nonsemantic neutral value in
both current and timeout-bootstrap critic projections. No post-reset state is
used by either terminal projection.

The DVM is not a critic-loss mask. The critic learns from every physical
transition, including transitions whose actor rows were forced.

## 9. Policy decision snapshot and identity binding

Use two immutable types with a hard producer/consumer boundary.

**B2-I1 producer — `EventPolicyEvidenceSnapshot`.** The private event policy
facade captures authority/evidence exactly once and produces bounded detached
fields:

```text
source current P2 publication object + publication identity
episode_generation [E]
transition_generation [E]
exact OPEN window object + opaque identity
immutable physical/problem evidence + producer/provenance declarations
explicit physical feasibility and geometric ranking-cost evidence
actor_obs [E,M,O_v2]
semantic_share_obs [E,S_critic]
runner_share_obs [E,M,S_critic]
normalization/scaling/schema metadata
```

P2 publication identity, episode/transition generation, and OPEN-window identity
are validation metadata only. They are not copied into `actor_obs` or
`semantic_share_obs` and are not learning features.

**B2-I2 producer — `EventPolicyDecisionBundle`.** B2-I2 consumes the exact I1
snapshot object without mutation, rebinding, or a second capture and adds:

```text
exact immutable EventPolicyEvidenceSnapshot reference/value
available_actions/DVM [E,M,N+1]
row_kind [E,M]
decision_valid_mask [E,M,1]
forced_action_id [E,M,1]
storage/policy/forced row masks
policy_proposal_present_mask / pre-inference proposal-source routing plan
the existing I4-2 EventProposalDecisionSnapshot or its exact narrow projection
```

The actual original sampled action/logprob envelope does not exist before actor
inference. B2-I3a seals it as a distinct `EventPolicyProposalEnvelope` bound to
this final decision bundle; neither object is completed by in-place mutation.

Neither type is a new clock, writer, state store, ownership table, or lifecycle
authority. A mutable partial bundle is forbidden. B2-I2 may only project
legality and row semantics from I1 evidence; it may not reread P2, recapture
physical tensors, replace provenance, or rebind identities.

Required binding behavior:

1. B2-I1 captures P2, physical/problem evidence, and exact OPEN window once and
   seals `EventPolicyEvidenceSnapshot`.
2. B2-I2 consumes that exact snapshot and seals `EventPolicyDecisionBundle`;
   there is no recapture boundary between them.
3. Validate final bundle identity before actor sampling.
4. After inference, let existing I4-2 validation recheck exact P2 publication,
   episode/transition, and OPEN-window identity before mutation.
5. If stale, discard the sampled proposal/logprob and recapture. Since no
   physical step occurred, no rollout row is inserted.
6. Never rebind a stale proposal to a newer P2/window.

No `decision_tick`, runtime `assignment_tick_generation`, window-as-tick alias,
or renamed window serial is introduced. Raw P2 identity, episode/transition
generation, and OPEN identity remain validation metadata and must never become
actor/critic features.

This ban includes numeric encoding, normalization, hashing, one-hot encoding, or
renaming of publication/window/generation metadata. Fixed robot-ID one-hot and
physical episode-progress fraction remain legitimate task semantics; neither is
a clock alias. Legacy v1 `target_action_mask`, `noop_action_mask`, and
`assignment_trigger_context` blocks are historical inventory, not I1 v2 model
inputs, because their DVM/row semantics are produced only in I2.

## 10. Action mask, DVM, and row semantics

### 10.1 Lifecycle legality

For a nonterminal current snapshot, a new target is legal only when all are
true:

```text
robot state == NEEDS_ASSIGNMENT
task state == AVAILABLE
P2 task owner == -1
pair not in P2 cumulative_failed_pairs
explicit physical feasibility == true
validated path/local eligibility == true when that producer is active
```

Cost ranks already-eligible conflict candidates; it never makes an infeasible
pair eligible. Two policy rows may legally propose the same available task.
Both original proposals/logprobs remain policy evidence; I4-2 arbitration
chooses the transaction candidate and final P2 remains the effective authority.

Task-state treatment is exact:

| Task state | New claim | Existing owner continuation |
|---|---:|---:|
| `AVAILABLE` | allowed only by full conjunction | not applicable |
| `CLAIMED` | false | owner only |
| `NAVIGATING` | false | owner only |
| `ALIGNING` | false | owner only |
| `COMPLETED` | false | false |
| `TEAM_INFEASIBLE` | false | false |

### 10.2 Four row classes

| Row class | Lifecycle condition | Semantic mask | Actor call | Routed scalar ID |
|---|---|---|---:|---|
| `POLICY_DECISION_ROW` | nonterminal `NEEDS_ASSIGNMENT` with at least one legal target | legal targets + noop | yes | original sampled ID |
| `FORCED_CONTINUATION_ROW` | `EXECUTING` with exactly one P2-owned active task | current task only; noop false | no | current task ID |
| `FORCED_NOOP_ROW` | `NEEDS_ASSIGNMENT` with no legal target, `WAITING_FOR_TASK`, or `UNAVAILABLE` | noop only | no | N (decoded -1) |
| `TERMINAL_NO_ROW` | finalized historical terminal state | all false | no | no new action row |

`EXECUTING` is never a repeated assignment decision in this design. The current
owned task persists in P2; the forced scalar ID is only fixed-shape HARL storage
and routing evidence. It is not a new proposal or B1 claim. If current P2 says
EXECUTING but does not yield exactly one owned active task, fail closed.

Transient physical/path infeasibility must not silently convert an EXECUTING
row into actor switch/noop. Release/failure is an authoritative lifecycle
transition. Until it occurs, continuation remains P2-derived; a contradictory
snapshot fails closed.

`DVM == true` exactly for `POLICY_DECISION_ROW`. Internally all masks are bool;
only the HARL boundary converts available actions to float32. The legacy
"noop-always-on" validator is not used for the event route.

### 10.3 Important terminal timing clarification

A physical action selected at time t still has its normal storage row even if
that action causes termination. `TERMINAL_NO_ROW` means the finalized terminal
state itself does not create a new t+1 actor action/proposal row. Autoreset then
provides the new episode's current observation/DVM for the next collection
step. This preserves both rollout accounting and terminal/current separation.

## 11. HARL runner actor-sampling audit and forced-row design

### 11.1 Current installed behavior

The repo-local runner's `collect()` only performs mask-presence diagnostics and
then calls `super().collect()` (`assignment_harl_training.py:709-738`). Installed
`OnPolicyBaseRunner.collect()` calls `get_actions()` once per agent on the full E
batch, passing `obs[t]`, `masks[t]`, and `available_actions[t]`; it does not
consult row class or `active_masks` (`on_policy_base_runner.py:334-398`).

The current fixed interface is:

```text
HARL action IDs/logprobs: [E,M,1]
decoded assignment IDs:   [E,M]
available actions:        [E,M,N+1]
per-agent actor buffer:    actions/logprobs [T,E,1]
                           obs/masks/available [T+1,E,...]
```

An all-false mask is not a safe way to bypass the categorical actor: installed
distribution code masks logits but still constructs a distribution. Terminal
rows must never be passed to `get_actions()`.

### 11.2 Why `active_masks` alone is incorrect

Installed HAPPO loss and entropy use `active_masks`, but that is insufficient:

- actor-buffer `insert()` writes `active_masks` into slot t+1, while training
  consumes `active_masks[:-1]`; naively passing the current DVM there is
  one-step misaligned (`on_policy_actor_buffer.py:84-110,148-185`);
- installed `OnPolicyHARunner.train()` reevaluates old/new logprobs and updates
  the sequential HAPPO factor over all rows, without an active-mask identity
  gate (`on_policy_ha_runner.py:45-125`);
- HAPPO loss/entropy divide by the active-mask sum, and the installed path has
  no safe per-minibatch zero-valid guard;
- whole-env done rows are deliberately reset to `active_masks=1` for the new
  autoreset episode (`on_policy_base_runner.py:456-466`).

Therefore `active_masks=0` plus a fake logprob does not make forced rows neutral.
`active_masks` retains its HARL liveness/autoreset meaning. A separate,
slot-aligned `decision_valid_mask` owns policy participation.

### 11.3 Repo-local subset sampling

The event runner must override collection, insertion, and HAPPO actor training
without editing installed HARL:

1. At slot t, read the current bundle's `decision_valid_mask[t]`.
2. For each agent, gather only env rows with DVM true.
3. Call that actor's `get_actions()` only on the gathered subset.
4. Scatter sampled IDs and original logprobs into fixed `[E,M,1]` tensors.
5. Scatter deterministic continuation/noop IDs for forced rows and a canonical
   zero logprob sentinel.
6. Keep feed-forward placeholder RNN state unchanged for bypassed rows.
7. If an actor has zero policy rows, skip its actor forward call completely.
8. Validate every sampled ID against the historical bundle mask before the env
   step.

The zero sentinel on a forced row is storage encoding only. Its simultaneous
`FORCED_NONDECISION` row kind, `decision_valid=false`,
`policy_proposal_present=false`, and `proposed_task_id=-1` prove that it is not
policy evidence.

### 11.4 Buffer and HAPPO math

Use an event-only repo-local actor-buffer extension/composition. It stores a
separate `decision_valid_masks[T+1,E,1]`, initialized with the reset/current
bundle at slot 0 and updated with the returned current bundle at slot t+1. The
action at t is trained against `decision_valid_masks[:-1][t]`, exactly like
`obs[:-1]` and `available_actions[:-1]`.

Actor loss and liveness semantics are:

```text
policy_evaluation_population = decision_valid_mask
policy_loss_population = HARL_active_mask AND decision_valid_mask

policy loss / entropy / advantage population:
  policy-loss population only
```

The full rollout sample index space is the sole canonical HAPPO factor index
space. Let

```text
Omega = {(t,e) | 0 <= t < T, 0 <= e < E}
canonical flat index k = t * E + e
factor_before_i, factor_after_i: [T,E,1]
```

No agent-specific compact ordering is a factor index authority. For actor `i`:

```text
canonical_indices_i = row-major (t,e) indices where
                      decision_valid_masks_i[:-1] is true

gather stored original actions, historical available_actions,
pre/post-update actor inputs and factor values at canonical_indices_i

evaluate the exact original proposal actions only on that subset
raw_ratio_subset_i = aggregate(exp(post_update_logprob - pre_update_logprob))

ratio_full_i = ones_like(factor_before_i)
scatter ratio_full_i[canonical_indices_i] <- raw_ratio_subset_i

factor_after_i = factor_before_i * ratio_full_i
```

The stored behavior logprob remains the PPO old logprob and is never replaced
by resolver/effective-assignment evidence. Loss minibatches may compact, shuffle,
or partition policy rows, but every sample retains its canonical `(t,e)` index.
The stable pre/post factor evaluation and scatter are independent of minibatch
ordinal order. Different agents may have different valid-index sets; their
compact positions must never be treated as a shared ordering.

Required guards:

- zero-DVM-valid actor: no evaluate, optimizer, or logger update; the complete
  full-grid factor is bitwise unchanged;
- singleton valid advantage: keep finite raw advantage; do not use unbiased
  normalization;
- zero-variance/nonfinite normalization: use finite raw advantages;
- empty minibatch after filtering: skip it and normalize logging by processed
  updates only;
- forced/nondecision rows: never enter evaluate-actions, raw-ratio computation,
  entropy, or policy loss; their canonical `ratio_full_i` entries are exactly
  one, so full-grid factor multiplication leaves them unchanged;
- a legal sampled proposal rejected by conflict arbitration remains a valid
  policy sample and remains in PPO/HAPPO training.

Mandatory I3b oracles include different-agent/different-DVM patterns, mixed
forced/policy rows, canonical scatter preservation under minibatch permutation,
forced ratio exactly one, zero-valid full-factor identity, slot-t use of
`decision_valid_masks[:-1]`, and conflict-loser inclusion at its original
`(t,e)` index.

This matches the intent already recorded in
`assignment_event_profile_schema_contract.py:783-848`, but requires a real
repo-local specialization because installed HARL does not implement it.

### 11.5 Eval/play boundary

Installed eval and the repo playback helper call deterministic actor APIs for
every E row. The repo assignment runner also delegates eval-env construction to
the installed factory, which has no event IsaacLab composition, while the
current YAML enables eval by default. B2 policy startup must validate one of
these exact states:

```text
eval disabled explicitly for the training/interface run
or
repo-local eval uses the same decision bundle, subset assembler, and forced-row rules
```

Playback/evaluation implementation remains deferred and is not needed for the
current design result, but silent fallback is a readiness failure.

## 12. Proposal / logprob / effective-assignment semantics

The learner ledger must preserve four separate concepts:

| Concept | Producer | Learner treatment |
|---|---|---|
| original sampled proposal ID | actor on DVM row | stored action/proposal |
| original proposal logprob | same actor distribution and historical mask | stored old logprob |
| resolver/arbitration result | existing I4-2 adapter | environment transaction evidence, not substituted action |
| effective assignment | final current P2 | controller state/reward consequence, not policy action |

The fixed `[E,M,1]` routing tensor contains both sampled and forced scalar IDs,
but the public event proposal envelope must also carry
`policy_proposal_present_mask == DVM`. The I4-2 adapter may inspect forced rows
for fixed routing consistency, but only policy rows may be described or logged
as actor proposals. Forced continuation does not generate a repeated B1 claim.

The wrapper/facade extension must therefore validate a typed proposal envelope,
not infer policy evidence from every scalar in the fixed tensor. No M1 request,
B1 artifact, arbitration winner, synthetic effective action, or P2 assignment
may replace the actor's original action/logprob in the buffer.

## 13. Pre-reset terminal critic sidecar producer design

### 13.1 Source-audited timing

`DirectMARLEnv.step()` computes dones and reward, calls `_reset_idx()` for done
rows, and only then gets observations (`direct_marl_env.py:384-415`). A wrapper
called after env return has already lost the previous episode's physical critic
state.

The narrow repo-owned pre-reset hook is task-local
`ScanMobileManipulatorEnv._get_dones()`:

```text
post-physics
-> _stage_event_scan_progress()
-> finalize_physical_transition(report)
-> _commit_event_scan_progress(outcome)
-> return terminated/truncated
-> DirectMARLEnv autoreset
```

See `scan_mobile_manipulator_env.py:3085-3120,3206-3226`. No
`DirectMARLEnv` core change is required.

### 13.2 Narrow ownership

Sidecar production is intentionally split without creating a second authority:

1. **Task environment physical capture.** During `_get_dones()`, capture an
   immutable, detached `PreResetCriticPhysicalSnapshot` containing only the
   fixed physical feature basis needed by the canonical shared projector:
   robot physical/capability table, task pose table, and episode progress/scale
   evidence. It travels inside the existing staged pre-reset report.
2. **Lifecycle-domain identity binding and typed projection.** During the
   existing lifecycle transaction, after the finalized result and prepared
   terminal P2 view exist but before terminal-slot publication, consume the one
   physical capture exactly once. Produce `TERMINAL_AUDIT` for every final
   reason. Only when the priority-resolved reason is `TIME_LIMIT`, also produce
   `TIME_LIMIT_BOOTSTRAP_CRITIC` from the same capture, prepared P2 view, and
   exact transition identity. Its numerical projector has ordinary continuing-
   state semantics and does not accept final reason as a feature input.
3. **Existing artifact storage.** `_TerminalHandoffArtifact._create()` receives
   the exact typed sidecar for the same terminal key. All terminal rows are
   validated and installed with their sidecars in the existing all-or-none
   terminal-slot publication. No second sidecar store is introduced.

The pure projector may be passed through a narrow internal producer capability;
it receives immutable inputs and no state-writer/P2/Ak capability. Any missing,
wrong-key, wrong-schema, aliased, or wrong-shape sidecar fails before normal
terminal publication. It must never fall back to post-reset reconstruction.
I4 may reuse the pure I1 projection schema/code, but it consumes its own
authoritative pre-reset physical basis; it must not reuse or mutate a current or
post-reset I1 evidence snapshot.

This fills an already-reserved private transport field; it does not add a field
to `LifecycleTransitionResult`, change termination priority, or make the
sidecar lifecycle authority. If independent review nevertheless classifies
filling the reserved field as reopening a frozen contract, stop before B2-I4.

### 13.3 Exact sidecar payload

The bounded immutable sidecar stores:

```text
terminal sidecar / audit / critic schema versions
exact terminal key binding (env, episode_generation, transition_generation)
exact finalized-P2 publication/provenance binding metadata
terminal_audit_projection (present for every authoritative terminal)
bootstrap_critic_obs: Optional[Tensor[S_critic]]
bootstrap_projection_valid: bool
declared dtype/device/shape contracts; detached, contiguous, no alias
```

The presence rule is exact:

```text
bootstrap_projection_valid == true
bootstrap_critic_obs is present
    iff priority-resolved final reason == TIME_LIMIT

ALL_TASKS_COMPLETED or NO_FEASIBLE_TASKS_REMAIN:
    terminal_audit_projection present
    bootstrap_critic_obs absent
    bootstrap_projection_valid false
```

`TERMINAL_AUDIT` may carry exact final reason and terminal-only audit views.
`TIME_LIMIT_BOOTSTRAP_CRITIC` is what the ordinary current-state critic
projector would produce for that exact pre-reset physical/finalized-P2 state. It
preserves ordinary feasibility, cost, progress, and other semantic blocks and
applies no terminal-only false/zero transform. It need not equal the pre-step
critic observation because the transition changed state, but it is never built
from the post-reset state.

The outer terminal artifact remains the authority for finalized lifecycle
result/P2 view, termination reason, done flags, and event evidence. The sidecar
does **not** store:

- an environment object or arbitrary environment state;
- a second lifecycle/ownership table with independent authority;
- critic network/RNN state or a critic value;
- proposal/logprob, resolver winner, M1/B1 artifact, or controller action;
- learner-consumption or ACK state.

Only `bootstrap_critic_obs` is a critic observation, not a precomputed value.
The learner evaluates that optional field using the rollout critic after the
runtime artifact has already been safely copied and ACKed. The audit projection
must never be passed to critic evaluation. True-terminal sidecars remain useful
for exact identity/schema validation and evidence, but trigger zero terminal
critic forward calls and no terminal-value learning.

## 14. Historical/current lifetime and ACK design

The exact lifetime is:

```text
pre-step current policy bundle / current share_obs
  -> physical step
  -> pre-reset physical critic snapshot
  -> finalized lifecycle result + TERMINAL_AUDIT
  -> iff TIME_LIMIT, same-evidence TIME_LIMIT_BOOTSTRAP_CRITIC
  -> runtime terminal artifact with typed sidecar
  -> task-env autoreset and canonical current P2 rebuild
  -> returned current episode obs/share_obs/DVM
  -> facade copies complete bounded historical DTO including sidecar
  -> cross-validate exact batch
  -> ATOMIC_BATCH_EXACT_ACK allowed
  -> wrapper/training facade exposes bounded DTO to repo-local runner
  -> learner records audit metadata and, iff TIME_LIMIT, evaluates only
     bootstrap_critic_obs before inserting buffer transport
```

The ordering invariant is:

```text
safe historical copy complete
-> runtime ACK allowed
```

It is explicitly not:

```text
critic evaluation / buffer insertion / learner update complete
-> runtime ACK
```

After ACK, the wrapper/training facade may hold only the bounded historical DTO,
never the raw runtime artifact or a second terminal-slot authority. The next
step replaces/clears that one-step transport after exact consumption. Current
post-reset P2 is never used to reconstruct historical terminal state.

## 15. HARL buffer and learner-transport audit/design

### 15.1 Current installed schemas

Installed EP buffers store:

| Buffer | Field | Shape |
|---|---|---|
| per-agent actor | `obs` | `[T+1,E,O]` |
| | `available_actions` | `[T+1,E,N+1]` |
| | `actions`, `action_log_probs` | `[T,E,1]` |
| | `masks`, `active_masks` | `[T+1,E,1]` |
| centralized critic | `share_obs` | `[T+1,E,S]` |
| | `value_preds`, `returns` | `[T+1,E,1]` |
| | `rewards` | `[T,E,1]` |
| | `masks`, `bad_masks` | `[T+1,E,1]` |

Actor insert stores action/logprob/value evidence at t and returned current
obs/masks at t+1. EP runner stores only `share_obs[:,0]` and `rewards[:,0]`
(`on_policy_base_runner.py:493-514`). Rollout-end compute evaluates only
`critic_buffer.share_obs[-1]` (`on_policy_base_runner.py:520-542`).

### 15.2 Current information loss

Wrapper `_stack_dones()` ORs terminated/truncated. Then
`AssignmentIsaacLabEnv.step()` discards wrapper info and returns `_empty_infos()`
(`assignment_harl_training.py:372-395`). Installed insert consequently sets:

```text
all done boundaries: masks[t+1] = 0
all current assignment infos: bad_masks[t+1] = 1
```

There is no stored termination reason, terminal sidecar, or truncation bootstrap
value.

### 15.3 Event-only transport extension

Keep the six-element HARL env return shape, but make its fifth element carry
one bounded typed event record in `infos[env][0]` for EP consumption. It may
contain only safe historical DTOs and learner routing facts, never raw runtime
artifacts. It must include exact terminated/truncated/reason/key identity and
the typed terminal sidecar when done. Actual final reason remains out-of-band
learner/audit metadata and is not concatenated into critic input.

`AssignmentOnPolicyHARunner.insert()` must be overridden for the event route to:

1. correlate every done env row with exactly one historical DTO/key;
2. reject missing, duplicate, stale, wrong-reason, or nonterminal sidecars;
3. preserve returned post-reset `obs/share_obs/DVM` at t+1 as current state;
4. for TIME_LIMIT only, evaluate `bootstrap_critic_obs[S_critic]` exactly once
   under inference mode with the rollout critic before any optimizer update;
   reject any attempt to evaluate `terminal_audit_projection`;
5. insert event actor and critic extensions on the correct t/t+1 slots;
6. consume/drop the one-step DTO after successful insertion.

Use repo-local event buffer subclasses or composition; installed HARL files
remain unchanged. Required additional fields are at least:

```text
actor decision_valid_masks:       [T+1,E,1] per actor
critic termination_reason:        [T,E,1] int/auditable enum
critic time_limit_bootstrap_value_preds: [T,E,1] normalized critic-output scale
critic time_limit_bootstrap_mask: [T,E,1] bool/float gate
```

After exact optional critic evaluation, the buffer may retain only the bounded
timeout value and reason/key audit metadata. True-terminal value slots are
unreadable sentinels under a false bootstrap mask and must never enter critic,
loss, ValueNorm, or GAE. With ValueNorm enabled, timeout values have the same
normalized network-output scale as ordinary `value_preds`; B2-I5b denormalizes
both through the same normalizer.

`bad_masks=0` may continue to record TIME_LIMIT for compatibility/audit, but it
must not be used as a multiplier that deletes the timeout transition.

## 16. TIME_LIMIT / GAE audit and design

### 16.1 Current real mapping

Lifecycle authority maps:

| Final reason | Env flags |
|---|---|
| `ALL_TASKS_COMPLETED` | `terminated=true`, `truncated=false` |
| `NO_FEASIBLE_TASKS_REMAIN` | `terminated=true`, `truncated=false` |
| `TIME_LIMIT` | `terminated=false`, `truncated=true` |
| `NONE` | both false |

The wrapper currently ORs flags into done; installed runner sets the episode
mask to zero for every env done. Because public assignment infos are empty,
`bad_masks` remains one even for TIME_LIMIT.

### 16.2 Current proper-time-limit math is insufficient

The config does set:

```text
use_proper_time_limits: true
use_gae: true
gamma: 0.99
gae_lambda: 0.95
use_policy_active_masks: true
```

However `on_policy_critic_buffer_ep.py:99-202` computes, in the configured GAE
branch:

```text
delta = r + gamma * V[t+1] * masks[t+1] - V[t]
gae = delta + gamma * lambda * masks[t+1] * gae
gae = bad_masks[t+1] * gae
```

Thus a done row with bad mask 1 targets reward only; setting bad mask 0 makes
`return_t=V(s_t)`. Neither yields `r + gamma*V(pre-reset terminal state)`.

### 16.3 Required event GAE

Separate episode-trace continuation from terminal-value bootstrap:

```text
bootstrap_value_t =
    masks[t+1] * V(current_next_state[t+1])
    + time_limit_bootstrap_mask[t]
      * V(time_limit_bootstrap_projection[t])

delta_t =
    reward[t] + gamma * bootstrap_value_t - V(current_state[t])

gae_t =
    delta_t + gamma * lambda * masks[t+1] * gae[t+1]

return_t = gae_t + V(current_state[t])
```

Here `V(time_limit_bootstrap_projection[t])` is evaluated only from the optional
ordinary-semantics `bootstrap_critic_obs` produced from the exact pre-reset
physical/finalized-P2 evidence. `termination_reason[t]` gates routing and remains
auditable, but is never a numerical input to that value. `TERMINAL_AUDIT` has no
value-learning role.

When ValueNorm is enabled, every V in these equations is denormalized through
the same current `ValueNorm` before arithmetic.

Final learner semantics are:

| Final authoritative reason | Bootstrap | GAE trace across boundary |
|---|---:|---:|
| `NONE` | returned current next-state V | continue |
| `ALL_TASKS_COMPLETED` | 0 | stop |
| `NO_FEASIBLE_TASKS_REMAIN` | 0 | stop |
| `TIME_LIMIT` | `V(TIME_LIMIT_BOOTSTRAP_CRITIC)` from pre-reset evidence | stop |

The frozen reason priority remains unchanged:

```text
ALL_TASKS_COMPLETED
> NO_FEASIBLE_TASKS_REMAIN
> TIME_LIMIT
> NONE
```

If a time-limit physical fact collides with a higher-priority true-terminal
reason, the finalized higher-priority reason disables timeout bootstrap.
`bad_transition` remains a separate learner transport fact; it is not a fifth
termination reason and is not inferred from TIME_LIMIT by lifecycle authority.

## 17. Blocker dependency graph

```text
                              B2-I0
                    no-tick/versioned contracts
                                |
                                v
                              B2-I1
                 immutable policy evidence snapshot
                 + canonical actor/shared projection
                       /                 \
                      v                   v
                  B2-I2                 B2-I4
        legality/DVM/row plan       pre-reset terminal audit
        + final decision bundle     + optional TIME_LIMIT bootstrap projection
                  |                      |
                  v                      v
                B2-I3a                 B2-I5a
       DVM-aware collection/       historical DTO transport
       fixed scatter/storage       + terminal value/buffer
                  |                      |
                  v                      v
                B2-I3b                 B2-I5b
       policy loss/entropy/        TIME_LIMIT GAE/
       full-index HAPPO factor     ValueNorm semantics
                   \                    /
                    +------ merge -----+
                               |
                               v
                              B2-I6
                 dormant public learned-policy route
                 (proposal -> I4-2 -> M1/B1 -> P2 -> Ak)
                                |
                                v
                              B2-V1
                  pure/static/synthetic interface gate
                                |
                                v
                              B2-V2
                 focused real Isaac + HARL interface smoke
                                |
                                v
                               B2-R
                         final readiness review
```

Exact dependencies are: I3b requires I3a; I5a requires I4; I5b requires I5a;
and I6 requires I2, I3a, I3b, I4, I5a, and I5b. The two chains merge only after
actor collection/storage, actor mathematics, sidecar production, learner
transport/value capture, and GAE/ValueNorm are independently expressible. The
public learned-policy route remains blocked before this merge.

Separate producer/tuning capabilities are dotted external seams/readiness
dependencies. They are not work silently included in B2-I0/I1/I2 and do not
authorize numeric choices here:

```text
validated local/top-k candidate producer - - -> typed I1 evidence seam
validated path-valid / nominal-cost producer - - -> typed I1 evidence seam
assignment retry scheduler - - - - - - - - - -> OPEN opportunity supplied to I1
```

I1 records only already-supplied typed evidence and provenance. I2 consumes the
frozen I1 evidence and cannot synthesize or recapture it. A required-but-missing
producer fails closed; a separately reviewed v2 omission removes the semantic
field rather than faking true/zero producer output. Pure fixtures may inject
explicitly labeled synthetic DTOs. No slice chooses any of the 11 numeric TBDs.

## 18. Proposed Phase B implementation slices

Every slice below requires a separate authorization and GPT review before any
dependent slice. Permissions listed here describe a future authorized slice;
they do not authorize execution in this B2-D turn.

### B2-I0 — Versioned no-tick contract reconciliation

- **Goal:** define actor/shared/DVM/proposal DTO v2 identity using current P2
   publication identity, episode/transition generation, and exact OPEN window;
   remove runtime dependence on `assignment_tick_generation` without rewriting
   historical v1, and freeze those identities as validation metadata only.
- **Likely files:** `assignment_event_profile_schema_contract.py`,
  `assignment_mrta_contract.py`, `assignment_profile_contract.py`, new pure
  contract fixtures and manifest oracles.
- **Frozen invariants:** no tick clock; OPEN window is not renamed; P2 sole
  authority; proposal/effective separation; fixed M/N; default-off.
- **Exact inputs:** v1 descriptors, committed P2/window identity types, frozen
  profile identity.
- **Exact outputs:** immutable v2 descriptors, manifest-derived semantic actor/
  critic dimensions, and compatibility statement; unchanged v1 historical
  descriptors. DVM/row fields remain separate routing inputs.
- **Tests:** manifest-derived v2 dimensions/field order, no alias, no forbidden
  tick, no raw identity/generation/window value in model features, exact
  identity mismatch failures, and existing/default digest preservation. Tests
  must not require v1 `O=476`/`S=497` when no semantic replacement exists.
- **Stop:** if versioned amendment is forbidden or requires a new clock, emit
  `PHASE-B2-D-STOP-ARCHITECTURAL-DEPENDENCY-GAP`.
- **Dependency:** none; mandatory first slice.
- **Execution:** pure/static only; no Isaac, HARL, training, playback, or eval.

### B2-I1 — Immutable policy evidence snapshot and current projectors

- **Goal:** capture P2/physical/problem/OPEN evidence once and seal one
  `EventPolicyEvidenceSnapshot` containing canonical current actor obs and one
  semantic centralized share_obs; do not compute DVM or open public step.
- **Likely files:** a new task-local event policy-interface/projector module,
  `assignment_event_runtime_facade.py`, `assignment_harl_wrapper.py`, schema
  manifest fixtures.
- **Frozen invariants:** projection-only/no writer; no wrapper truth; immutable
  single capture; no actor-concat critic; current/historical separation; no
  proposal outcome, DVM, row kind, tick, or identity metadata in model input.
- **Exact inputs:** current P2 publication/reference, exact OPEN window, one
  ordered physical/problem capture, scale contract, and already-supplied typed
  external producer evidence/provenance if the reviewed schema requires it.
- **Exact outputs:** immutable `EventPolicyEvidenceSnapshot`, actor
  `[E,M,O_v2]`, semantic share `[E,S_critic]`, repeated HARL share
  `[E,M,S_critic]`, and declared source/cost semantics. I1 does not implement
  local/top-k, path-valid/cost, or retry producers.
- **Tests:** manifest-derived fixed M/N dimensions (including E=2,M=3,N=12),
  dtype/device, normalization, P2 inverse ownership, stale metadata, no alias,
  one capture/no recapture, raw-nearest exclusion, missing-required-producer
  fail-closed behavior, and default-off hashes.
- **Stop:** if current owned task cannot be uniquely derived from P2, if a
  physical feature requires post-reset guessing, if the snapshot needs a second
  lifecycle store, or if identity metadata must become a model feature.
- **Dependency:** B2-I0.
- **Execution:** pure/static fixtures only; no Isaac/HARL runtime.

### B2-I2 — Lifecycle legality, DVM, row plan, proposal ledger

- **Goal:** jointly produce semantic masks, DVM, row kinds, forced IDs, and
  policy-proposal-presence by consuming the exact B2-I1 snapshot and seal the
  final immutable `EventPolicyDecisionBundle`.
- **Likely files:** event policy-interface module, `assignment_mrta_contract.py`
  v2 DTOs, narrow `assignment_event_proposal_adapter.py` envelope extension,
  pure fixtures.
- **Frozen invariants:** EXECUTING continuation is not reassignment; cost is
  ranking only; policy rows only reach proposal logic; conflict resolution and
  M1/B1 remain unchanged; final P2->Ak.
- **Exact inputs:** the exact immutable B2-I1 `EventPolicyEvidenceSnapshot`; no
  second P2/window/physical/problem capture is permitted.
- **Exact outputs:** `[E,M,N+1]` bool/float masks, `[E,M,1]` DVM/forced IDs,
  four row masks, `policy_proposal_present_mask`, I4-2 proposal-source binding,
  and final immutable `EventPolicyDecisionBundle`. This is a pre-inference
  routing/source envelope; actual sampled action/logprob is added only by I3a
  in a separately sealed `EventPolicyProposalEnvelope`.
- **Tests:** every robot/task state combination, current-task retention,
  failed pair, ownership conflict, physical infeasibility, no-target noop,
  mixed rows, same-task conflict, terminal no-row, stale bundle, I1 object/
  provenance identity preservation, mutation/recapture rejection, and no fake
  proposal on forced rows.
- **Stop:** if EXECUTING must be stochastically resampled, forced continuation
  would issue B1, or DVM needs a new authority/clock.
- **Dependency:** B2-I1. External producer DTOs, when schema-required, must
  already be frozen inside I1; I2 never implements their producers or values.
- **Execution:** pure/static only; no Isaac/HARL runtime.

### B2-I3a — Repo-local DVM-aware actor collection and storage

- **Goal:** call `get_actions()` only on each actor's current DVM subset,
  scatter sampled and forced routing into fixed tensors, and store slot-aligned
  decision evidence. This slice does not change actor loss/math.
- **Likely files:** `assignment_harl_training.py`, new event actor-buffer/
  collection module, `assignment_lifecycle_training_contract.py`, synthetic
  fixtures.
- **Frozen invariants:** installed HARL unchanged; original proposal/logprob;
  forced sentinel never policy evidence; EXECUTING continuation never B1;
  feed-forward fixed-M/N EP/HAPPO.
- **Exact inputs:** final B2-I2 decision bundle, per-agent actors, current obs/
  masks/available actions, and fixed actor-buffer slots.
- **Exact outputs:** immutable `EventPolicyProposalEnvelope`, fixed
  `[E,M,1]` action/logprob routing tensors, original sampled IDs/logprobs only
  on DVM rows, and `decision_valid_masks[T+1,E,1]` per actor. Action slot t is
  bound to DVM[t]; returned current/autoreset bundle is stored at t+1.
- **Tests:** exact per-agent actor call subsets/counts, mixed policy/continuation/
  noop rows, fixed scatter, original logprob, forced storage sentinel, t/t+1
  alignment, zero-valid actor forward skip, stale bundle no insertion, and
  installed-package hash unchanged.
- **Stop:** if collection requires evaluating forced rows, treating a forced ID
  as policy evidence, editing site-packages, or losing fixed tensor shape.
- **Dependency:** B2-I2.
- **Execution:** separately authorized synthetic CPU/Torch and installed-HARL
  component checks permitted; no Isaac, actor optimizer/loss update, rollout
  training loop, playback, eval, or checkpoint changes.

### B2-I3b — Repo-local HAPPO policy and full-index factor math

- **Goal:** train/evaluate only policy rows and implement policy loss, entropy,
  advantages, PPO ratio, and sequential HAPPO factor with canonical full
  `(t,env)` index preservation and exact forced-row ratio one.
- **Likely files:** event actor-trainer/buffer module from I3a,
  `assignment_harl_training.py`, synthetic actor-math fixtures.
- **Frozen invariants:** installed HARL unchanged; stored original proposal and
  historical available-action mask are reevaluated; forced rows never become
  samples; legal conflict losers remain valid; factor is always `[T,E,1]`;
  agent-specific compact order is never factor authority.
- **Exact inputs:** verified I3a actor buffer, `decision_valid_masks[:-1]`, HARL
  active masks, critic advantages, stored original actions/logprobs and
  historical available actions, current full rollout factor.
- **Exact outputs:** policy-only loss/entropy/update records and, for each actor,
  subset raw ratios scattered by canonical `k=t*E+env` into a full ones tensor,
  then multiplied into the full factor. Loss minibatches retain canonical
  indices even when shuffled/compacted.
- **Tests:** different-agent/different-DVM index sets; mixed forced/policy rows;
  exact scatter/index preservation under minibatch permutation; forced ratio
  exactly one; zero-valid actor leaves full factor unchanged; singleton/nonfinite
  advantage guards; empty minibatch; slot alignment; conflict-loser inclusion;
  and installed-package hash unchanged.
- **Stop:** if factor correctness requires compact actor ordering as shared
  authority, fake forced logprob math, editing site-packages, or a recurrent/
  variable-cardinality redesign.
- **Dependency:** B2-I3a.
- **Execution:** separately authorized synthetic CPU/Torch and installed-HARL
  component checks with bounded optimizer-step oracles permitted; no Isaac,
  rollout training campaign, playback, evaluation, or checkpoint changes.

### B2-I4 — Authoritative pre-reset terminal critic sidecar

- **Goal:** before autoreset, produce authoritative terminal audit projection
  for every terminal and an optional ordinary-semantics timeout-bootstrap critic
  projection only for final `TIME_LIMIT`, then transport both in the existing
  terminal artifact.
- **Likely files:** `scan_mobile_manipulator_env.py`,
  `assignment_event_profile_runtime_domain.py`,
  `assignment_lifecycle_transaction_runtime.py`, shared projector module,
  `assignment_event_terminal_transport.py`, I4-3-derived pure fixtures.
- **Frozen invariants:** no DirectMARLEnv change; no P2/Ak/termination-priority
  change; one terminal slot store; copy-before-ACK; ACK not learner consumption.
- **Exact inputs:** immutable pre-reset physical feature basis, prepared final
  P2 view/result, coverage/completion/progress, exact terminal key.
- **Exact outputs:** typed immutable sidecar containing exact key/provenance,
  `terminal_audit_projection`, optional `bootstrap_critic_obs[S_critic]`, and
  exact presence/shape contracts in runtime artifact and bounded historical DTO.
- **Tests:** exact source timing, one physical/P2 capture, shared exact key/
  provenance, audit reason preserved, timeout bootstrap equals ordinary current-
  projector semantics and excludes reason/terminal-only zeroing, true-terminal
  bootstrap absent, priority collision, no alias, exact-key all-or-none batch,
  reset mutation isolation, ACK/recovery, wrong sidecar fail closed, defaults.
- **Stop:** if production requires wrapper reconstruction, a second terminal
  store, a DirectMARLEnv core change, or modification of frozen P2/Ak/result
  semantics.
- **Dependency:** B2-I0 and shared projector portion of B2-I1.
- **Execution:** pure/static/task-local fake integration only; no real Isaac or
  HARL in the implementation slice.

### B2-I5a — Historical learner transport, terminal value, and buffer fields

- **Goal:** consume bounded historical DTOs, validate exact terminal identity/
  reason/presence, evaluate only a valid TIME_LIMIT `bootstrap_critic_obs`, and
  store event critic-buffer transport fields. Do not change GAE or returns.
- **Likely files:** `assignment_harl_training.py`, new event EP critic-buffer
  module, learner transport DTO, synthetic transport/value fixtures.
- **Frozen invariants:** current obs at t+1 remains post-reset; audit projection
  never enters critic; true terminal has no bootstrap/critic forward; installed
  HARL unchanged; safe copy and runtime ACK precede learner evaluation.
- **Exact inputs:** six-element env return, typed infos/historical DTO, returned
  current share_obs, rollout critic, final reason and typed I4 sidecar.
- **Exact outputs:** exact `termination_reason`, timeout-bootstrap mask/value,
  terminal key/audit metadata, and verified event critic-buffer slots. Existing
  GAE/returns are byte-for-byte/behaviorally unchanged in this slice.
- **Tests:** missing/duplicate/stale/wrong-reason DTO; audit-to-critic rejection;
  TIME_LIMIT bootstrap projection evaluated exactly once; both true terminals
  produce zero critic calls; priority collision; copy-before-ACK lifetime;
  t/t+1 identity/device/shape; unchanged GAE oracle; installed hashes.
- **Stop:** if exact reason/identity cannot be correlated, only post-reset input
  exists, audit must enter critic, ACK must wait for learner, or transport cannot
  be verified independently without changing return math.
- **Dependency:** B2-I4.
- **Execution:** separately authorized synthetic Torch/installed-HARL component
  checks permitted; no Isaac, GAE change, training loop, playback, evaluation,
  optimizer update, or checkpoint.

### B2-I5b — TIME_LIMIT bootstrap, event GAE, and ValueNorm

- **Goal:** after I5a transport/value/buffer identity is independently verified,
  implement event-only TIME_LIMIT bootstrap with explicit bootstrap/trace
  separation and correct ValueNorm semantics.
- **Likely files:** event EP critic-buffer/return module from I5a,
  `assignment_harl_training.py`, synthetic return-math fixtures.
- **Frozen invariants:** current t+1 remains post-reset; only final TIME_LIMIT
  timeout value bootstraps; true terminals bootstrap zero; traces never cross an
  episode boundary; reason priority and installed HARL remain unchanged.
- **Exact inputs:** verified I5a rewards/value predictions/reason/timeout mask/
  timeout value fields, current next-state values, masks, gamma/lambda, and the
  rollout ValueNorm state.
- **Exact outputs:** event GAE/returns using separate next-state and timeout-
  bootstrap terms; normalized/denormalized values follow one current ValueNorm
  contract.
- **Tests:** hand-computed NONE/both true terminals/TIME_LIMIT targets, mixed E
  rows, higher-priority collision, no cross-reset trace, timeout value only once,
  ValueNorm and non-ValueNorm parity, nonfinite/missing-gate fail closed, and
  installed hashes.
- **Stop:** if correct timeout return requires post-reset reconstruction,
  terminal-reason critic leakage, stock `bad_masks` deletion, or unverified I5a
  transport/value identity.
- **Dependency:** B2-I5a; must not begin before I5a independent verification.
- **Execution:** separately authorized synthetic Torch/installed-HARL component
  math checks permitted; no Isaac, rollout training loop, playback, evaluation,
  optimizer campaign, or checkpoint.

### B2-I6 — Dormant public learned-policy event route

- **Goal:** compose event domain -> O1 -> facade -> wrapper in the formal
  assignment env and route a validated policy envelope through existing I4-2,
  M1/B1, final P2, and Ak while keeping readiness fail-closed.
- **Likely files:** `assignment_harl_wrapper.py`, `assignment_harl_training.py`,
  event composition roots/facade, profile gate descriptors, pure integration
  fixtures.
- **Frozen invariants:** event branch never constructs legacy resolver; final
  controller uses Ak only; forced rows are not proposals; historical/current
  separation; existing profiles unchanged; readiness not flipped in this slice.
- **Exact inputs:** B2-I1 evidence snapshot, B2-I2 final decision bundle,
  B2-I3a fixed action/logprob proposal envelope, reviewed B2-I3b actor math,
  B2-I4 sidecar, and B2-I5a/I5b learner transport/return semantics.
- **Exact outputs:** correct six-element current HARL return plus bounded typed
  historical info; one public learned proposal route behind the blocked gate.
- **Tests:** fake domain full sequence, stale-before-step no insertion, K=0/K>0,
  mixed forced/policy rows, conflict loser evidence, terminal/autoreset, no raw
  artifact retention, default-off isolation.
- **Stop:** if opening the route requires early readiness activation, wrapper
  ownership truth, actor-to-controller bypass, or loss of original logprob.
- **Dependency:** B2-I2, B2-I3a, B2-I3b, B2-I4, B2-I5a, and B2-I5b are all
  independently reviewed. The public learned route remains blocked until then.
- **Execution:** pure/static fake integration only; no Isaac/HARL runtime.

### B2-V1 — Pure/static/synthetic interface verification gate

- **Goal:** run the complete authorized B2 contract/projector/DVM/runner/buffer
  matrix without Isaac and establish exact default-off and installed-package
  preservation.
- **Likely files:** dedicated B2 verification fixture and targeted existing
  boundary fixtures; verification report only.
- **Frozen invariants:** all preceding invariants; no readiness flip.
- **Exact inputs:** implemented B2-I0, I1, I2, I3a, I3b, I4, I5a, I5b, and I6.
- **Exact outputs:** recorded per-suite counts, hashes, tensor/math oracles,
  side-effect audit.
- **Tests:** all dedicated tests plus Phase-A/profile/B1/B1W/I4 frozen boundary
  matrix in normal and isolation modes as appropriate.
- **Stop:** any digest drift, default-off effect, policy/forced leakage, terminal
  alias, or nonfinite learner math.
- **Dependency:** B2-I6.
- **Execution:** separately authorized Python/static/synthetic HARL component
  execution only; no Isaac, training/playback/evaluation, or checkpoint.

### B2-V2 — Focused real Isaac + HARL interface smoke

- **Goal:** verify interface behavior, not performance or learning, on the
  bounded real E=2/M=3/N=12 CUDA composition.
- **Likely files:** one dedicated supervisor/worker smoke fixture and a report;
  production source must already be frozen by B2-V1.
- **Frozen invariants:** exact event profile, final P2->Ak, forced rows bypass
  actors, original sampled logprob, terminal sidecar/current separation,
  timeout bootstrap-projection transport without reason leakage, true-terminal
  audit-only behavior, atomic ACK, and no training.
- **Exact inputs:** reviewed implementation checkpoint and bounded deterministic
  scenario.
- **Exact outputs:** actor call-row evidence, fixed tensor shapes, proposal/
  effective separation, sidecar identity, one buffer insertion and return-math
  verification, clean close/recovery.
- **Tests:** reset/current bundle, policy and forced mix, no-new-claim
  continuation, terminal/autoreset/history, TIME_LIMIT bootstrap-projection/
  value transport, true-terminal zero critic calls, post-ACK next step.
- **Stop:** any timeout/crash, stale identity, actor call on forced row,
  post-reset bootstrap, P2/Ak drift, or production change during verification.
- **Dependency:** B2-V1 and explicit user authorization.
- **Execution:** focused Isaac and HARL **interface inference/buffer smoke only**;
  no optimizer update, training, playback, evaluation, checkpoint, or readiness
  activation.

### B2-R — Final event-profile readiness review

- **Goal:** classify evidence against the gate in Section 19 and decide whether
  any readiness transition is authorized.
- **Likely files:** authoritative review report and `TASK_PROGRESS.md`; profile
  readiness code changes require a later explicit authorization.
- **Frozen invariants:** evidence level is not inferred from module presence;
  training readiness is separate from learned-route runtime verification.
- **Exact inputs:** B2-V1/V2 reports, unresolved-producer/TBD inventory, default-
  off and installed-hash evidence.
- **Exact outputs:** reviewed readiness classification and next authorization.
- **Tests:** none beyond review of recorded evidence unless separately ordered.
- **Stop:** any unmet criterion leaves readiness blocked.
- **Dependency:** B2-V2.
- **Execution:** review-only; no Isaac/HARL/training/playback/evaluation.

## 19. Final readiness gate

Readiness is cumulative and evidence-based:

| Level | Required evidence | Current status |
|---|---|---|
| `INTERFACE_ONLY` | canonical manifest/static contracts; no learned runtime claim | PASS, current profile state |
| `LIFECYCLE_RUNTIME_BACKBONE_VERIFIED` | B0/B1/B1W/I4 private real-Isaac backbone, terminal ACK/recovery | PASS / committed / closed |
| `POLICY_INTERFACE_READY` | no-tick evidence snapshot/final bundle, canonical actor obs, DVM/rows, I3a subset collection/storage, I3b full-index HAPPO math, original proposal/logprob, dormant public route, pure/synthetic pass | BLOCKED |
| `LEARNER_INTERFACE_READY` | canonical shared obs, typed terminal audit/timeout-bootstrap sidecar, I5a historical transport/value/buffer identity, I5b TIME_LIMIT GAE/ValueNorm, mixed-row tests | BLOCKED |
| `LEARNED_ROUTE_RUNTIME_VERIFIED` | focused real Isaac + HARL interface smoke with policy/forced/terminal evidence and no training | BLOCKED |
| `TRAINING_READY` | all above; required candidate/path/retry producers and experimental parameters explicitly resolved; reward/rollout/update configuration reviewed; authorized bounded optimizer smoke; no checkpoint/schema ambiguity | BLOCKED |

`POLICY_INTERFACE_READY` and `LEARNER_INTERFACE_READY` are independent gates
that must both pass before learned-route runtime verification. A successful
private lifecycle playback or one correct buffer module does not satisfy them.

The profile's production readiness enum and formal gates remain unchanged until
B2-R (or later) is independently reviewed and the user explicitly authorizes a
code change. `TRAINING_READY` must not be set merely because B2-V2 succeeds.
Its reviewed configuration must also either disable eval explicitly or provide
the same row-aware event composition for eval; installed fallback is forbidden.

## 20. Explicitly deferred work

This design does not select values for:

```text
top_k_tasks_per_robot
local_robot_cap
local_task_cap
pair_abs_threshold
pair_rel_threshold
component_abs_threshold
component_rel_threshold
transfer_penalty
rejection_penalty_scale
alignment_time_constant
assignment_retry_cadence
```

They remain a separate experimental tuning/producer dependency. Interface
fixtures may inject typed symbolic values, but no production default or claimed
research value is authorized here.

Also deferred:

- local-set/top-k production scheduling and empirical tuning;
- a true nominal path-time/cost producer beyond the current geometric distance;
- preemption/transfer policy and penalties;
- extended workload/history features beyond completion attribution;
- reward tuning, curriculum, performance claims, and paper experiments;
- Transformer/GNN/Set Transformer;
- variable robot/task cardinality and arbitrary-cardinality checkpoints;
- checkpoint migration/change;
- row-aware playback/evaluation implementation and policy-quality claims;
- training;
- Phase C/D/E.

## 21. No implementation / no training statement

Only this Markdown design report and the authoritative progress document are in
scope for B2-D. No production Python, test fixture, config, runner, buffer,
profile gate, checkpoint, or installed HARL source was modified. No Python test,
Isaac/AppLauncher, HARL execution, training, playback, evaluation, or commit was
run or created.

The documentation-only result is
`PHASE-B2-D-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW`. Design is revised
and awaits a second independent GPT review; implementation remains not started,
all policy/learner/runtime readiness gates remain blocked, and training remains
unauthorized.

Stop now after documentation update and await independent GPT design review.
