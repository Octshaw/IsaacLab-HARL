# Phase B1W-I4-1 — Event Facade, Composition, Reset, and Continuation Implementation Report

## Classification

```text
classification:
  PHASE-B1W-I4-1-EVENT-FACADE-COMPOSITION-RESET-CONTINUATION-COMPLETE-AWAITING-GPT-REVIEW

B1W-I4-D:                         REVIEW PASS / FROZEN
B1W-I4-D-R:                       REVIEW PASS / CLOSED
event facade:                     IMPLEMENTED
WR-C composition:                 IMPLEMENTED
exact event wrapper dispatch:     IMPLEMENTED
legacy profiles:                  UNCHANGED
legacy resolver on event route:   NOT CONSTRUCTED
wrapper raw event reset/step:     NOT USED
admitted reset through O1:        PURE/STATIC PASS
no-new-claim continuation:        PURE/STATIC PASS
redundant B1 claim:               NONE
P2 sole authority:                PRESERVED
Ak-only controller source:        PRESERVED
proposal interpretation:          NOT IMPLEMENTED
conflict arbitration:             NOT IMPLEMENTED
terminal wrapper transport:       NOT IMPLEMENTED
atomic batch ACK:                 NOT IMPLEMENTED
lifecycle observation/mask:       NOT IMPLEMENTED / READINESS BLOCKER
runtime readiness:                BLOCKED
Isaac / HARL:                     NOT RUN
training/playback/evaluation:     NOT RUN
commit:                           NONE
```

This phase stops at the authorized I4-1 boundary. It does not enter I4-2 or
I4-3 and does not activate the exact-event profile for production training.

## Repository boundary

```text
working directory: E:\Project\IsaacLab_HARL
branch:            main
starting HEAD:     912b3b59831fcad8dd29ac575b2a1851bf2c21d1
ending HEAD:       912b3b59831fcad8dd29ac575b2a1851bf2c21d1
index:             empty
commit:            none
worktree:          existing Phase-A/B0/B1/B1W cohort preserved
```

No reset, cleanup, unrelated normalization, staging, or commit was performed.

## Production delta

### New B-private facade

`assignment_event_runtime_facade.py` adds:

```text
EventAssignmentRuntimeFacade
EventAssignmentRuntimeFacadeError
EventFacadeResetResult
EventFacadeStepResult
_compose_event_assignment_runtime_facade(...)
```

The module has canonical-module identity enforcement and `__all__ = ()`; the
package initializer does not export it. The facade's exact retained dataclass
members are:

```text
_runtime           one narrow O1 reference
_resolved_profile  exact ResolvedEventGatedAssignmentProfile object
_domain_identity   opaque same-domain identity
```

Result DTOs are frozen, slotted, factory-controlled, and detach the admitted
effective assignment. The facade retains no runtime domain, Store, resolver,
scheduler, terminal slot map, ownership/proposal cache, mutex, poison flag,
raw fence writer, or lifecycle writer.

Its callable runtime surface is limited to:

```text
read_current()
reset(...)
step_without_new_claim(action_builder=...)
```

It exposes no proposal interpretation, claim commit, feasibility filtering,
conflict arbitration, terminal discovery/capture/ack, or policy adapter.

### Narrow O1 extension

`assignment_event_profile_synchronous_runtime.py` adds only the I4-1 evidence
needed above the existing sequencing owner:

```text
domain_identity
read_interstep_fence()
step_environment_without_new_claim(...) -> _EventProfileNoClaimStepReceipt
```

The existing `step_environment()` behavior and raw result surface are
preserved by delegation. The private receipt carries the admitted P2, the
Ak-derived controller assignment, the environment result, and the completed
window. O1 remains the only component that performs Ak admission, derives the
controller assignment, calls `env.step`, and completes the existing fence.

### Exact-profile wrapper branch and composition

`assignment_harl_wrapper.py` now dispatches exhaustively:

```text
exact ResolvedExistingAssignmentProfile
  -> event facade must be None
  -> existing readiness barrier and legacy initialization unchanged
  -> existing stateful resolver retained

exact ResolvedEventGatedAssignmentProfile
  -> exact facade required
  -> facade/profile/environment object identities must match
  -> legacy resolver is None
  -> event reset and private no-claim continuation use facade only

anything else
  -> fail closed
```

The private `_compose_event_assignment_harl_wrapper(...)` seam validates the
exact profile/domain/environment identity, constructs exactly one O1 from the
retained domain's narrow ports, constructs the facade, discards the raw domain
from the wrapper boundary, and injects the facade into the wrapper. It is not
publicly exported and is not called by the formal production factory.

The formal `make_assignment_harl_env(...)` runtime-readiness barrier and
`assignment_harl_training.py` remain unchanged. Thus this private composition
is testable while activation remains blocked.

## Composition and sequencing graphs

### Composition

```text
exact resolved event profile + retained runtime domain + event environment
  -> private composition identity checks
  -> exactly one EventProfileSynchronousRuntimeCoordinator (O1)
  -> EventAssignmentRuntimeFacade retains O1/profile/opaque identity only
  -> AssignmentHarlWrapper retains facade only
```

The event wrapper neither constructs the legacy lifecycle resolver nor retains
O1 or the raw domain directly.

### Admitted reset

```text
wrapper.reset
  -> facade.reset
  -> O1.reset_environment
  -> standalone reset admission
  -> env.reset
  -> canonical reset P2 publication
  -> admitted return completion
  -> existing fence OPEN
  -> facade validates provenance/generations/nonterminal/open
  -> wrapper preserves raw observations and returns provisional shared state
```

Measured evidence is one O1 reset call and zero wrapper-direct raw reset calls.
The reset P2 has canonical episode-reset provenance, episode generation `0`,
transition generation `-1`, no lifecycle result, and an OPEN fence.

The returned action-mask slot is deliberately `None`; I4-1 does not fabricate
a lifecycle mask or claim runtime readiness.

### No-new-claim continuation

```text
wrapper._step_event_without_new_claim
  -> facade.step_without_new_claim
  -> O1 reads final current P2
  -> existing step admission closes OPEN window and captures P2 as Ak
  -> O1 derives assignment only from Ak.admitted_publication
  -> O1/controller callback builds physical action
  -> env.step
  -> exact same Ak finalization and explicit success completion
  -> existing next window OPEN
  -> facade returns immutable diagnostic DTO with claim_artifact=None
```

The public event `wrapper.step(actions)` fails closed before physical mutation,
because proposal interpretation and proposal-to-B1 commit belong to I4-2. The
wrapper's event `assignment_to_env_actions(...)` also fails closed; controller
conversion remains O1-only. These are explicit private/test continuation seams,
not a learned-policy entrypoint.

## Executable semantic evidence

### Example A: executing owner continues without a new claim

The dedicated fixture first establishes legal executing P2 ownership with the
already-verified B1 port outside the measured facade call. This fixture-only
seed is not a facade capability. During the measured I4-1 route:

```text
source/admitted P2 identity:   same object
source/admitted Store version: unchanged before Ak
facade claim artifact:         None
O1 deterministic-claim stage:  0 occurrences
Ak controller assignment:      [[2, -1]]
raw env received assignment:   [[2, -1]]
wrapper-direct env.step calls:  0
O1 env.step calls:              1
```

Wrapper convenience fields are deliberately filled with conflicting proposal,
assignment, and effective-assignment tensors; the actual control assignment
remains `[[2, -1]]` from Ak-bound P2. Wrapper caches therefore cannot become
authority or control source.

### NEEDS_ASSIGNMENT continues unowned

From canonical reset P2 with no fixture claim:

```text
ownership:                     all -1
Ak controller assignment:     [[-1, -1]]
claim artifact:                None
fabricated owner:              none
```

No B1 commit occurs. This is continuation of the current authoritative P2, not
an automatic claim or scheduler decision.

### Nonterminal completion

The no-claim nonterminal fixture completes the admitted Ak, opens a distinct
next window, and leaves the domain unpoisoned. P2/Store do not change between
the source read and Ak admission.

### Terminal boundary

The dedicated terminal fixture verifies fail-closed behavior after the raw
terminal return: facade raises `facade_terminal_not_supported_i4_1`, the exact
terminal slot remains pending, and facade exposes no ACK method. Wrapper copy,
historical transport, and atomic batch exact ACK are not implemented here.

## Isolation and forbidden-capability audit

Static and executable checks establish:

- all four existing profiles construct zero event facade/domain/O1 objects and
  retain their existing resolver path;
- exact-event wrapper constructs no legacy resolver;
- event reset/step never call raw environment methods from wrapper code;
- event controller conversion never calls the wrapper's legacy helper;
- facade holds no domain, Store, writer, raw fence, terminal registry, resolver,
  scheduler, cache, mutex, or poison authority;
- no new assignment generation, decision clock, opportunity tick, lock,
  coordinator, Store, or poison authority exists;
- facade and private composition helper have no package-level public export;
- proposal interpretation, feasibility arbiter, conflict arbitration, M1 B1
  effective commit, terminal wrapper copy/ACK, observation/mask/DVM, forced-row
  runner logic, critic sidecar, and learner transport are absent.

Legacy conflict-related code found elsewhere in `AssignmentHarlWrapper` is the
pre-existing exact-existing-profile branch; it is not reachable from the new
event initialization or continuation path.

## Protected hash audit

Expected authorized production changes:

| File | Pre SHA-256 | Post SHA-256 | Result |
|---|---|---|---|
| `assignment_event_runtime_facade.py` | new | `35B051346B6DFD78E6D16A79EFECA00D108A3FD947F5B9569AAA8E50A3160FF0` | new private facade |
| `assignment_event_profile_synchronous_runtime.py` | `56A7A81160A007413D56F62B982A500DEFC66F4F37E884ABB7A0C96313CAF496` | `39D495EBB4458A3DC99FAC46B3E9F9D315507493B3A38B5CF9FA7B1A51494B86` | authorized narrow O1 extension |
| `assignment_harl_wrapper.py` | `DA694C5C1CBEBEA675E3657FC0C43640D16B131BB1CD4FC5CB83E6626EED320A` | `63CAF1459939644AB64FCC16E1B0CA473D6CCA25A758540D01C7FF627B6DB5D1` | authorized exact-event branch/composition |
| `assignment_harl_training.py` | `B6F32510AE663B3E443891CDD09219DD9A5C9CEB9DE9C720C73192C7488597FD` | same | unchanged |

The preflight recorded the full values for unchanged protected files; post
values below are exact matches:

| Protected file | Pre = post SHA-256 |
|---|---|
| `assignment_event_profile_runtime_domain.py` | `545274EEF630977E97C1064D831F5841DC97E8A38AA720E4474DEB7BEC7197B7` |
| `assignment_interstep_claim_window_runtime.py` | `17DB697DFD97672EDC092BFAE79FEE26CFB356FA082590054735120CA63A7609` |
| `assignment_initial_claim_runtime.py` | `C74868C84A803108C424827AFE9326393428938DCE4F6CBD46693DA3D4D94FDA` |
| `assignment_lifecycle_transaction_runtime.py` | `FFB1885B2440DC510B7D04469B0216143BE380798B5A2F236FFFE99F9B30CAA0` |
| `assignment_controller.py` | `28FAF8D9DB9D323E14020B675D9BBFACD03D9A31D6361414A5A471F6C6803317` |
| `assignment_rl_interface.py` | `3F20B6F5C24472E2F2D0B76E693AC4664547C1D7D78A56E15CB137B002717E59` |
| `scan_mobile_manipulator_env.py` | `C19B5DE8F73D22FBC8B4C1F6B38DBFC4804D28B6E37B002CDFC4E20D5ECC9C99` |
| `source/isaaclab/isaaclab/envs/direct_marl_env.py` | `7F7714A6F32E24CE34EF184CB9EED87CC36D4DB0744C44A816CE3DA9CC505F31` |
| `assignment_lifecycle_transition_contract.py` | `1BF66C6C6B51ADB8A44292910C1B11DFB1E43F31D711D3320285F3DF587B0CC9` |
| `assignment_event_contract.py` | `22194AD8671DD299BD7ACD0B837325B4C85F50B8636CB285FF4F76879467086A` |
| `assignment_profile_contract.py` | `ECE4A58C1636EA3F710775EAAC25E12DF4097972EF57EC0D15CEFEC5E6702500` |
| `assignment_event_profile_schema_contract.py` | `04EB153F296196E8A098F071FDEA3721E27893564B4FA2DF81FF91FC088859EF` |

## Changed and new files

Production:

```text
new  assignment_event_runtime_facade.py
mod  assignment_event_profile_synchronous_runtime.py
mod  assignment_harl_wrapper.py
```

Dedicated verification:

```text
new  scripts/environments/test_assignment_phase_b1w_i4_1_event_facade_wrapper_integration_pure.py
```

Existing pure/static fixtures received only boundary-oracle updates required by
the new private composition seam and final wrapper digest:

```text
test_assignment_phase_a_default_off_identity.py
test_assignment_profile_production_wiring.py
test_assignment_phase_b1w_i1_environment_coordinator_integration_pure.py
test_assignment_phase_b1w_interstep_claim_window_fence_pure.py
test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py
test_assignment_phase_b0_3i4_environment_integration.py
```

Documentation:

```text
AgentRead/202608/20260823/PHASE_B1W_I4_1_EVENT_FACADE_COMPOSITION_RESET_CONTINUATION_IMPLEMENTATION_REPORT.md
AgentRead/TASK_PROGRESS.md
```

No training, runner, environment, controller, RL-interface, frozen-contract,
Isaac-core, config/YAML, checkpoint, or installed-package file changed in this
phase.

## Verification matrix

All commands used `D:\miniconda3\Scripts\conda.exe run -p
C:\isaacenvs\isaac45_harl python ...`.

| Suite | Normal | `-I -B` |
|---|---:|---:|
| B1W-I4-1 dedicated facade/wrapper | 15/15 | 15/15 |
| Phase-A default-off identity | 16/16 | 16/16 |
| profile contract | 16/16 | 16/16 |
| profile production wiring | 10/10 | 10/10 |
| B1W-I3 terminal consumer | 13/13 | 13/13 |
| B1W-I1 environment/O1 | 28/28 | 28/28 |
| B1W inter-step fence | 26/26 | 26/26 |
| B1 initial claim | 23/23 | 23/23 |
| B0-3I2 runtime domain capabilities | 12/12 | 12/12 |
| B0-3I4 environment integration | 12/12 | 12/12 |
| frozen lifecycle transition contract | 12/12 | 12/12 |
| event profile schema contract | 9/9 | 9/9 |
| event-gated MRTA contract | 13/13 | 13/13 |

Dedicated normal and isolated runs also preserve Python, Torch, and NumPy RNG;
cwd; environment variables; `sys.path`; root/named logging state; filesystem
inventory; and profile registry identity.

`py_compile` passed for every changed/new Python file. Final trailing-whitespace,
Markdown-fence, and `git diff --check` audits passed after documentation closeout.

No Isaac/AppLauncher, real environment, HARL runner, training, playback,
evaluation, or checkpoint process was started.

## Remaining blockers and stop boundary

Runtime readiness remains blocked because the following are deliberately not
implemented:

```text
B1W-I4-2 proposal interpretation
explicit-feasibility-first filtering and pure conflict arbitration
M1 proposal-to-effective B1 commit
B1W-I4-3 terminal wrapper historical copy and atomic batch exact ACK
final lifecycle-aware actor/shared observation schema
lifecycle action mask/DVM and forced-row sampling
critic/learner transport
```

The public exact-event `.step(actions)` and formal production composition stay
fail closed. Do not enter B1W-I4-2, flip readiness, run Isaac/HARL/training, or
commit without a new explicit user/GPT authorization.
