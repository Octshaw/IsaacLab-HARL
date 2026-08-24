# Phase B1W-I4-2 — Proposal Interpretation and Effective Commit Implementation Report

## Classification

```text
classification:
  PHASE-B1W-I4-2-PROPOSAL-INTERPRETATION-AND-EFFECTIVE-COMMIT-COMPLETE-AWAITING-GPT-REVIEW

B1W-I4-1:                      REVIEW PASS / CLOSED
event proposal interpretation: IMPLEMENTED
proposal-source P2 identity:    ENFORCED
structural legality filter:     PASS
explicit physical feasibility: PASS
cost eligibility authority:    NONE
conflict arbitration:           PASS
infeasible fallback re-entry:   IMPOSSIBLE
M1 C2 batch:                    PASS
one action batch:               ZERO OR ONE B1 ARTIFACT
continuation:                   NO REDUNDANT CLAIM
P2 sole ownership authority:    PRESERVED
Ak-only controller source:      PRESERVED
stateful legacy resolver:       NOT USED ON EVENT ROUTE
terminal wrapper transport:     NOT IMPLEMENTED
atomic terminal batch ACK:      NOT IMPLEMENTED
lifecycle obs/mask:             NOT IMPLEMENTED / BLOCKER
runtime readiness:              BLOCKED
Isaac / HARL:                   NOT RUN
training/playback/evaluation:   NOT RUN
commit:                         NONE
```

This implementation stops at the authorized I4-2 boundary. It does not enter
I4-3 terminal wrapper copy/atomic ACK or I4-4 real integration.

## Repository boundary

```text
working directory: E:\Project\IsaacLab_HARL
report path:       AgentRead/20260824/PHASE_B1W_I4_2_PROPOSAL_INTERPRETATION_AND_EFFECTIVE_COMMIT_IMPLEMENTATION_REPORT.md
branch:            main
starting HEAD:     912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:       912b3b59831fcad8dd29ac575b2a1851bf2c21d1
index:             empty
commit:            none
worktree:          existing Phase-A/B0/B1/B1W cohort preserved
```

No reset, cleanup, unrelated normalization, staging, or commit was performed.

## Changed and new files

Production delta:

- new `assignment_event_proposal_adapter.py`;
- extended `assignment_event_runtime_facade.py` with the private I4-2 route;
- generalized the O1 claim surface in
  `assignment_event_profile_synchronous_runtime.py` without changing B1;
- added private decision/proposal proof seams and bounded diagnostics in
  `assignment_harl_wrapper.py`.

Evidence delta:

- new `test_assignment_phase_b1w_i4_2_proposal_effective_commit_pure.py`;
- refreshed the Phase-A wrapper digest after the authorized wrapper change;
- refreshed two stale inventories so I4-1 permits only the exact I4-2 proposal
  methods and B0-I3 recognizes private wrapper composition;
- updated this report and `TASK_PROGRESS.md`.

The existing environment, controller, RL interface, lifecycle transaction,
B1 transaction, runtime domain, fence, legacy resolver, DirectMARLEnv,
contracts, training code, runner, and configuration were not modified by I4-2.

## Proposal adapter architecture and retained capabilities

The new B-private adapter is canonical-module guarded, has an empty public
export tuple, and is not exported by the package initializer. Its instance
retains exactly the resolved event-profile object. It retains no environment,
domain, Store, B1/fence port, resolver, controller, terminal registry, cache,
lock, coordinator, poison state, or RNG.

The decision and resolution DTOs are frozen, slotted, factory-controlled, and
clone all tensor inputs and outputs. A decision snapshot binds:

```text
exact source P2 publication identity
exact OPEN-window identity
episode-generation tuple
transition-generation tuple
explicit feasible_mask snapshot
cost_matrix snapshot
optional consistency-only available_mask snapshot
```

No assignment tick or parallel generation clock was introduced. Revalidation
before pure resolution and again before B1/Ak rejects stale P2 or window
identity; neither object may be rebound.

## Interpretation, feasibility, and arbitration

The pure order is exactly:

```text
raw actor action ID
  -> decode task ID / NO_CLAIM
  -> current P2 structural legality
  -> explicit physical feasible_mask
  -> eligible conflict set
  -> cost ranking of eligible members only
  -> deterministic task-disjoint winners
  -> C2-shaped M1 request
```

Structural interpretation distinguishes continuation, no-claim, executing
switch rejection, executing-noop rejection, invalid robot state, unavailable
task, owned task, and failed pair. Physical infeasibility is a separate typed
classification and mask. Conflict losers are distinct from both pure proposal
rejection classes.

`feasible_mask` is the eligibility authority. `cost_matrix` is ranking evidence
only: a finite cost cannot admit a physically infeasible pair. Among eligible
candidates for one `(env, task)`, the minimum finite cost wins, then the lowest
robot ID. If every already-feasible candidate cost is NaN or infinity, the
lowest robot ID among that feasible set wins. No fallback can re-add an
infeasible or structurally rejected candidate.

Conflict grouping is per `(env, task)`. Independent tasks and environments are
preserved. Winner construction validates that every selected C2 row contains
at least one claim and that its nonnegative task IDs are unique.

## M1 and synchronous commit

The adapter produces the frozen B1 representation without modifying B1:

```text
selected_env_ids[K]
requested_task_by_robot[K,M]
```

O1 submits this already-resolved request once through the existing W2
production claim port. One actor action batch therefore yields:

- `K=0`: no prepare, token, B1 artifact, Store mutation, or P2 publication;
  the existing I4-1 no-new-claim route proceeds directly to Ak;
- `K>0`: exactly one C2/M1 B1 artifact for the full batch, one Store-version
  increment, one new P2, and no window replacement before Ak.

There is no per-robot M2 loop. The facade validates the zero-or-one artifact
invariant and checks Store/P2/window accounting before physical admission.

The mandatory mixed case is verified as:

```text
source P2:  [2, -1, -1]
proposal:   [2,  4, -1]
M1:         [-1, 4, -1]
final P2:   [2,  4, -1]
Ak/control: [2,  4, -1]
```

The executing owner continues without a redundant claim while the independent
new claim commits in the same single batch.

## Authority, mutation, and failure evidence

The physical route is:

```text
proposal diagnostics
  -> optional one B1 M1 commit
  -> final current P2
  -> existing O1 Ak admission
  -> Ak-derived assignment
  -> controller callback
  -> env.step
```

Proposal tensors, winner masks, M1 requests, commit artifacts, and wrapper
convenience caches are never controller inputs. A hostile-cache test writes
conflicting proposal/assignment/effective tensors and still observes the exact
final P2-derived `[2,4,-1]` at the raw environment.

| Case | B1 artifacts | Store delta | P2 before Ak | Window before Ak |
|---|---:|---:|---|---|
| continuation/no claim | 0 | 0 | identical object | identical object |
| one or more selected rows | 1 | +1 for full batch | exactly one new P2 | identical object |
| pure rejection/conflict loser only | 0 | 0 | identical object | identical object |
| authoritative B1 rejection | 0 | 0 | unchanged | unchanged |

Stale-P2 evidence rejects at `proposal_source_validate` before B1, Ak, or
environment entry. A W1-bound envelope committed after W2 is rejected as
`stale_claim_window` and is not rebound. With a pending terminal slot, pure
proposal interpretation can complete, but authoritative B1 rejects with
`terminal_slot_occupied`; the facade reports `facade_b1_rejected`, while P2,
window, terminal slot, and poison state remain unchanged.

Result diagnostics preserve original actor raw IDs, decoded proposal, source
identity/generations, structural/feasibility rejection masks, winner/loser
masks, task-disjoint M1 request, zero-or-one B1 artifact, admitted final P2
assignment, and committed interpretation. Actor log-probability ownership
therefore remains attached to the original proposal, not the effective result.

## Readiness and terminal boundaries

The wrapper exposes only private/dedicated proof seams for explicit decision
snapshots and proposal stepping. Public learned-policy event `step(actions)`
still fails closed because lifecycle actor/shared observations and action
mask/DVM identity are not implemented. No synthetic observation or mask was
introduced to bypass that blocker.

The proposal route accepts only a nonterminal fixture. Terminal discovery,
historical wrapper copy, terminal transport, and atomic batch exact ACK remain
absent. A terminal result fails closed after existing O1 leaves the canonical
slot pending; no I4-3 capability is exposed.

## Dedicated evidence and regressions

The dedicated suite passes 22/22 in both normal and `-I -B` modes. It covers
factory/capability isolation, snapshot identity/aliasing, continuation/new/mixed
claims, deterministic conflict ranking, nonfinite fallback, infeasible
non-reentry, multi-env one-artifact M1, stale P2/window, G2 rejection, hostile
caches, immutable diagnostics, four-profile isolation, readiness boundaries,
and process/RNG/import side effects.

Every regression row also passed in both modes:

| Suite | Result per mode |
|---|---:|
| I4-2 dedicated proposal/effective commit | 22/22 |
| I4-1 facade/reset/continuation | 15/15 |
| Phase-A default-off identity | 16/16 |
| profile contract | 16/16 |
| profile production wiring | 10/10 |
| B1 initial claim | 23/23 |
| B1W fence | 26/26 |
| B1W-I1 coordinator/environment admission | 28/28 |
| B1W-I3 terminal consumer | 13/13 |
| B0-3I1 rebuild transaction | 12/12 |
| B0-3I2 runtime domain | 12/12 |
| B0-3I3 staged reporter | 16/16 |
| B0-3I4 terminal handoff | 16/16 |
| B0-3I4 environment integration | 12/12 |
| frozen lifecycle transition contract | 12/12 |
| frozen event profile schema contract | 9/9 |
| frozen event-gated MRTA contract | 13/13 |

This is 271 passing cases per mode across the recorded matrix.

## Side-effect, compile, and diff checks

The dedicated audit observed unchanged Python/Torch RNG, working directory,
environment, `sys.path`, logger/profile registries, filesystem inventory, and
child-process inventory. It imported no Isaac, Omniverse, pxr, or HARL module.
No new lock, Store, coordinator, poison state, ownership tensor, tick, or
package export was found.

`py_compile` passed for adapter, O1, facade, wrapper, and dedicated test.
`git diff --check` passed. No Isaac/AppLauncher, HARL, training, playback,
evaluation, or runtime smoke was run.

## Protected hashes

Preflight and postflight hashes are identical for every protected file:

```text
C74868C84A803108C424827AFE9326393428938DCE4F6CBD46693DA3D4D94FDA  assignment_initial_claim_runtime.py
545274EEF630977E97C1064D831F5841DC97E8A38AA720E4474DEB7BEC7197B7  assignment_event_profile_runtime_domain.py
FFB1885B2440DC510B7D04469B0216143BE380798B5A2F236FFFE99F9B30CAA0  assignment_lifecycle_transaction_runtime.py
17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609  assignment_interstep_claim_window_runtime.py
28FAF8D9DB9D323E14020B675D9BBFACD03D9A31D6361414A5A471F6C6803317  assignment_controller.py
3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59  assignment_rl_interface.py
7F64183C638697F16EFA45769978127C7E3575599E87CFA76A5BA26F20EABADB  assignment_lifecycle_resolver.py
03483727573974BB57F96309D9D8A1EC446D87580915747BC57014BB4CC7F754  assignment_lifecycle_resolver_runtime.py
C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99  scan_mobile_manipulator_env.py
7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31  direct_marl_env.py
1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9  assignment_lifecycle_transition_contract.py
22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A  assignment_event_contract.py
ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500  assignment_profile_contract.py
04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF  assignment_event_profile_schema_contract.py
B6F32510AE663B3E443891CDD09219DD9A5C9CEB9DE9C720C73192C7488597FD  assignment_harl_training.py
```

Authorized production postflight hashes:

```text
874B4C7B71E6C42F9E6DABEEFA25A708D25D8518E3366FE91B86B9B1A739BEDD  assignment_event_proposal_adapter.py
63E3038488C9249583678A58AFD38875EDEB78ABA11036E69A6CF0ACBB59F14C  assignment_event_profile_synchronous_runtime.py
AEB293E4E1ED302D1C0B595C7C562E08B52A5F709D7E69BA93AFF41B069A30DD  assignment_event_runtime_facade.py
B47C136AA7708D6C8F96A038A34B525A589083763F553F2EABEBCF0612773FF3  assignment_harl_wrapper.py
```

## Stop boundary

B1W-I4-2 is complete and awaits review. B1W-I4-3 was not entered. No terminal
wrapper copy, atomic batch ACK, terminal critic sidecar, HARL runner change,
forced-row actor sampling, lifecycle observation/mask/DVM, readiness flip,
runtime execution, or commit was performed.
