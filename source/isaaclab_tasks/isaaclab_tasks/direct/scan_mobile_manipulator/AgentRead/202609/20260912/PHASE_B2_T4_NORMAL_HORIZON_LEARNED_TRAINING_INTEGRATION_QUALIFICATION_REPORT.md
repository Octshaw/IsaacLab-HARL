# Phase B2-T4 Normal-Horizon Learned-Training Integration Qualification Report

Date: 2026-09-12

Classification:
`PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED`

This phase stopped during the mandatory pure/static preflight. No CUDA/CUBLAS
readiness probe, AppLauncher, environment, formal learner, rollout, or learner
transaction was started.

## A. repository authority

Starting and closing authority is `main` at
`b71d85a32f51be6ada324f870813a56bb45dd396`, equal to `origin/main` and the
merge-base. The pre-existing index contains 359 staged monthly-migration paths;
its SHA-256 is
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`.
The migration path-set SHA-256 is
`0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.
No index operation or commit occurred.

## B. starting reviewed authority

The user-supplied starting authority is accepted: B2-R0 through B2-R7 and
B2-T0 through B2-T3 are `GPT REVIEW PASS / CLOSED`. T3-C's five local CUBLAS
startup failures remain historical infrastructure evidence only. Checkpoint
continuation is not established; long training and B2-R6 are not authorized;
the public learned-policy route remains `DORMANT / BLOCKED`.

## C. T3 handoff / horizon basis

T3 established the distinction between learner rollout `T=2`, T0/T2's
test-only 0.3-second horizon, and the source-authoritative 30-second environment
horizon. T3's controlled task-progress witness does not establish the B2-T4
learned-training integration.

## D. source identities

All reviewed sources checked before the STOP remained exact. Key hashes are:

| Source | SHA-256 |
|---|---|
| `assignment_event_training_actor_mutation.py` | `08eb3442ac52dc4f7fd69434486ee7ec77920c64e614d0a19944f4b163b078e3` |
| `assignment_event_training_critic_mutation.py` | `9719bcd059cfe9a670cc9715117ef00e965f708c82134a59c3a1f77296173dde` |
| `assignment_event_training_full_transaction.py` | `ec42cb68db274f42144489f4e8ef199311c557016c4859475057c1deed417c35` |
| `assignment_event_training_real_isaac_adapter.py` | `bff37075343795703b3ad4c7f7d27727278fd23e095e81d2de6b62a94821560e` |
| `scan_mobile_manipulator_env.py` | `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363` |
| `assignment_lifecycle_transaction_runtime.py` | `2033be70f91a14678ed718a3a0d3d8c26a26a5c5a05b8c6e9ae5dacb3cbfd3de` |
| `assignment_event_policy_evidence.py` | `7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a` |
| `assignment_event_policy_decision.py` | `d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697` |
| `assignment_event_actor_collection.py` | `3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45` |
| `assignment_event_learned_route.py` | `b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b` |
| T2 observer | `b93ccbad1762e6d4df2fdb8a81c174b40a07a5acfba87b9bc5b248434931e356` |
| T3 observer | `c8edd97c1327c0d2f2084725449edd916e8b6190bbee3eab3ac04a1dc31cbf59` |

Installed HAPPO/VCritic/VNet/ValueNorm hashes are respectively
`dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96`,
`ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3`,
`a3760b3fdf290c73bb13a752c0b0d39f69fd6fa207560272954b44a027f427c3`,
and `a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0`.
The complete digest set is in `b2_t4_artifacts/source_identities.json`.

## E. files created/modified

Created one test-side preflight, five bounded JSON artifacts, this report, and
the byte-exact TASK_PROGRESS archive. `AgentRead/TASK_PROGRESS.md` was updated
only after that archive. Production semantic modifications and installed HARL
modifications are both 0.

## F. CUDA/CUBLAS readiness

`NOT REACHED`. The mandatory preflight found the integration blocker before
the intended formal worker. Readiness probes: 0; retry: 0. This is not a CUDA
infrastructure failure classification.

## G. preflight

The approved interpreter and 15-file `py_compile` passed. Geometry passed;
ValueNorm passed 53 assertions; CPU CG classification passed; LD passed 13/13;
T2 and T3 observers passed repeat-exact/nonmutation checks; I3B passed 16/16;
I5B passed 14/14; static/private/public guards passed with public references 0.
The zero-DVM and lower-level nonterminal-return cases passed. The integrated
R5 nonterminal case failed, so the full preflight did not authorize the formal
worker.

There were 18 pure/static Python invocations. Three test-side diagnostic
invocations failed before yielding evidence (two preflight fixture authoring
errors and one inline CG import-path error); each was corrected without
production changes. Pre-mutation harness workers: 0.

## H. zero-DVM pure qualification

PASS. A controlled `T/E/M/B=2/3/3/6` full R5 transaction used zero DVM and
zero active rows for every actor. Expected and observed actor backward/step
counts were `[0,0,0]`/`[0,0,0]`; all three segments skipped; actor parameters
and optimizer state were unchanged; the full factor remained identity. Critic
backward/step and ValueNorm update were `1/1/1`; S7/S8/S9/S10 were `1/1/1/1`.

## I. nonterminal-bootstrap pure qualification

The lower-level event-return path passed for `T/E=2/3` with six `NONE` rows.
The final bootstrap was the supplied current-next-state critic values
`[[7],[8],[9]]`, not zero. Shape was `[2,3,1]`, all values were finite and
nonaliased, timeout sidecar/critic uses were 0, event-return computations were
1, and stock `compute_returns` calls were 0.

Integrated qualification failed: the reviewed real-Isaac adapter requires
`tuple(route.collector.consumed_terminal_keys)` and dynamically rejects an
empty ledger with
`STOP — B2-R5I REAL_EVIDENCE_BINDING: real terminal learner ledger is empty`.
The R5 S0 validator independently contains `or not keys`. A valid normal-horizon
T=2 continuation rollout has all reasons `NONE` and therefore no terminal
consumption key. Continuing would require a production contract/semantic
change, which B2-T4 forbids.

## J. fresh formal process

Not started. Formal mutation-bearing workers: 0; AppLauncher lifetimes: 0;
environments: 0; explicit resets: 0; learner constructions: 0.

## K. exact runtime config

Intended but not instantiated: `Isaac-Scan-Mobile-Manipulator-Direct-v0`,
profile `event_gated_local_mrta`, `T/E/M/N=2/2/3/12`, actor and critic
epochs/minibatches `5/2`, ValueNorm enabled, `fixed_order=false`, `cuda:0`.

## L. horizon separation

Source audit retains 30.0 seconds, 0.1-second control steps, and configured
`max_episode_length=300`, separate from rollout `T=2`. Runtime resolution was
not instantiated because preflight stopped first. No 0.3-second override ran.

## M. 160-update definition

The requested definition remains tx001 through tx160, two physical transitions
then one S0-S10 transaction each, with no learner-boundary environment reset.
It was not executed.

## N. update-ID inventory

Unique formal update IDs: 0. Tx001 was not created; tx161 was not started.

## O. episode-generation trajectory

Not observed. Formal episode generations: 0.

## P. lifecycle decision summary

Not observed formally. Policy-required, continuation, and forced-noop rows are
all 0 in the unstarted formal route.

## Q. actor-order distribution

No formal actor permutation was generated. The controlled zero-DVM preflight
used one reviewed seeded permutation only as pure evidence.

## R. zero-DVM actor statistics

Formal actor-transaction pairs: 0. Pure witness: 3 zero-DVM actor segments,
all three skipped backward and optimizer step, with zero Adam increments.

## S. all-zero-decision transaction evidence

Formal count: 0. One pure controlled full-transaction witness passed with all
actor DVM populations zero, critic and ValueNorm active, and S10 reached.

## T. actor update counts

Formal actor backward/step: 0/0. Pure all-zero witness: 0/0.

## U. factor audits

Formal audits: 0. The pure all-zero witness audited three identity/no-op actor
segments and exact initial-to-final factor identity.

## V. critic classifications

Formal `VALID_NONZERO_UPDATE`/`VALID_ZERO_EFFECTIVE_UPDATE`: 0/0. Focused CPU
CG preflight passed both reviewed classifications and negative gates.

## W. critic/ValueNorm counts

Formal critic minibatches/backward/step/ValueNorm.update: 0/0/0/0. The separate
pure all-zero witness used 1/1/1/1 and is not counted as formal B2-T4 training.

## X. nonterminal return/bootstrap evidence

Formal transactions: 0. The pure lower-level witness passed one all-NONE
rollout, but current R5 integration rejected its necessarily empty terminal
ledger before S0. Therefore integrated nonterminal bootstrap is not qualified.

## Y. terminal return/bootstrap evidence

No formal terminal branch ran. Existing reviewed terminal semantics were not
reclassified by this STOP.

## Z. actor Adam continuity

No formal bridge exists. Pure zero-DVM actor Adam state was unchanged.

## AA. critic Adam continuity

No formal bridge or formal critic Adam transition exists.

## AB. ValueNorm continuity

No formal bridge exists. Formal ValueNorm updates: 0.

## AC. 159-bridge summary

0/159 executed. The requested continuity gate remains untested.

## AD. collection learner immutability

No formal collection occurred; no formal collection-induced learner mutation
occurred. This is not a runtime PASS claim.

## AE. learner-update runtime/P2 immutability

No formal S0-S10 transaction occurred; learner-induced runtime/P2 mutations:
0. This is not a runtime PASS claim.

## AF. cross-update ownership witness

Not obtained because tx001 did not start.

## AG. multi-update completion witness

Not obtained.

## AH. task-progress trajectory

No B2-T4 formal trajectory exists. T3's prior controlled witness remains
historical and was not reused as learned-training evidence.

## AI. completion/P2/coverage consistency

Not observed formally. TASK_COMPLETED events, completed-count delta, and B2-T4
coverage observations are 0/not observed.

## AJ. completion -> reopen evidence

Not observed in B2-T4.

## AK. terminal/autoreset evidence

No formal terminal/autoreset boundary was attempted or observed.

## AL. post-autoreset learned-training evidence

Not obtained.

## AM. terminal-ledger continuity

No formal ledger existed. The preflight blocker is precisely that the current
adapter/coordinator require a nonempty terminal ledger for every transaction,
which is incompatible with a valid all-NONE T=2 rollout.

## AN. event-return compute-once continuity

Formal event-return computations: 0; formal stock `compute_returns`: 0. The
targeted pure nonterminal witness used event returns exactly once and stock
returns zero times.

## AO. S7/S8/S9/S10 counts

Formal counts: `0/0/0/0`. Pure all-zero transaction counts: `1/1/1/1`.

## AP. numerical health

Formal numerical health is not evaluated. Pure return, actor, critic, factor,
and ValueNorm checks were finite and passed.

## AQ. normal-horizon training diagnostics

Not available because the normal-horizon formal route did not start.

## AR. rolling health

No formal windows or sentinel transactions exist.

## AS. artifact inventory

Durable artifacts under `b2_t4_artifacts/` are
`zero_dvm_pure_qualification.json`,
`nonterminal_bootstrap_pure_qualification.json`, `integration_gap.json`,
`source_identities.json`, and `final_result.json`. The test-side source is
`scripts/environments/test_assignment_phase_b2_t4_normal_horizon_integration_preflight.py`.

## AT. static/private/public guards

PASS for the unchanged static guard suite: private exports 0, public faults 1,
stock faults 6, guarded production files 57. Public activation references and
activations are 0. Static mutation ownership remained unique.

## AU. exact execution counts

```text
CUDA/CUBLAS readiness probes: 0
formal mutation-bearing workers: 0
pre-mutation harness workers: 0
pure/static Python invocations: 18 (15 passed, 3 diagnostic failures)
AppLauncher / environment / reset / learner: 0 / 0 / 0 / 0
successful learner updates / unique IDs / rollout batches: 0 / 0 / 0
physical environment steps / bridges: 0 / 0
terminal/autoreset boundaries: 0
formal actor backward / optimizer.step: 0 / 0
formal critic backward / optimizer.step / ValueNorm.update: 0 / 0 / 0
formal event-return / stock compute_returns: 0 / 0
formal S7 / S8 / S9 / S10: 0 / 0 / 0 / 0
critic rollovers / ledger resets / actor rollovers: 0 / 0 / 0
learner-induced runtime/P2 mutations: 0
collection-induced learner mutations: 0
checkpoint weight I/O / public activation / evaluation-playback: 0 / 0 / 0
tx001 started / tx161 started: 0 / 0
production semantic modifications: 0
post-mutation retries: 0
```

## AV. retained nonclaims

This work does not establish B2-T4 normal-horizon learned-training integration,
160-update stability, 159 bridges, task ownership across updates, multi-update
completion, runtime/P2 immutability, terminal/autoreset continuity, training
quality, convergence, checkpoint continuation, public-route readiness, or
paper-scale training readiness.

## AW. final quiescence

The formal route is quiescent by non-entry: no AppLauncher, environment,
learner, transaction, gradient, mutation, ledger, or retry exists. Repository
staging remained untouched.

## AX. final classification

`PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED`.

Lower-level nonterminal return math is qualified, but the required current
learned-route plus R5 integration is not. The current reviewed adapter and S0
coordinator reject the empty terminal-key state required by ordinary
nonterminal rollouts. Production modification was forbidden, so execution
stopped before CUDA readiness and formal mutation.

## AY. GPT-review handoff

B2-T4 is `STOPPED AT PREFLIGHT / AWAITING INDEPENDENT GPT REVIEW`, not complete.
The next step is an independently authorized design/reconciliation task for an
R5 rollout-completeness contract that can distinguish valid nonterminal
completion from missing terminal evidence without weakening terminal
historical-evidence checks. Do not start tx001/tx161, B2-R6, checkpoint I/O,
public activation, evaluation/playback, or long/paper-scale training under this
authorization.
