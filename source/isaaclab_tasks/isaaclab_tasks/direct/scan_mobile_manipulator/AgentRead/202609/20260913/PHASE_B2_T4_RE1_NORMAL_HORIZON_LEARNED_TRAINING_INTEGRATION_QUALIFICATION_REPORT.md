# Phase B2-T4-RE1 Normal-Horizon Learned-Training Integration Qualification Report

Date: 2026-09-13 (Asia/Shanghai)

## A. repository authority

Branch `main`; HEAD, `origin/main`, and merge-base are all
`b71d85a32f51be6ada324f870813a56bb45dd396`. The pre-existing 359 staged
monthly-migration paths were untouched. Staged-index SHA-256 is
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`;
monthly path-set SHA-256 is
`0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.

## B. starting reviewed authority

B2-R0 through B2-R7 and B2-T0 through B2-T3 remain GPT REVIEW PASS/CLOSED.
The user declared B2-T4-NR GPT REVIEW PASS/CLOSED before authorizing this fresh
RE1 run.

## C. historical T4 STOP preservation

The original B2-T4 classification remains historical and unchanged:
`PHASE-B2-T4-STOP-NONTERMINAL-BOOTSTRAP-NOT-QUALIFIED`. It remains
STOPPED/HISTORICAL/NOT COMPLETE with zero updates and is not reclassified by
this run.

## D. B2-T4-NR authority

NR empty/empty, mixed, and fail-closed semantics were treated as current
production authority. The dedicated suite passed 5/5 and its 14-case terminal
expectation matrix passed all positive and negative cases.

## E. source identities

The two current NR identities were exact at preflight and worker startup:

- full transaction: `a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de`
- real-Isaac adapter: `b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014`

The formal test-side runner identity was
`ed1a52c71824563192b943f5d4471fecd58363e1f4edb5e657f42c14e42f025f`.
The remaining reviewed production, installed HARL, LD, T2, and T3 identities
matched the runner's locked manifest.

## F. files created/modified

Created the test-side RE1 runner, preflight source-authority draft and summary,
formal supervisor/result artifacts, failure adjudication, byte-exact
TASK_PROGRESS archive, and this report. Only
`AgentRead/TASK_PROGRESS.md` was rewritten after the archive. Production
semantic files and installed HARL files were not modified.

The final layout keeps all 12 phase JSON files together under
`b2_t4_re1_artifacts/`; the Markdown report/archive remain in the date
directory and the test-side runner remains under `scripts/environments/`.

## G. preflight

PASS before the formal worker: approved interpreter; relevant `py_compile`;
NR hashes; NR 5/5; I5b 14/14; zero-DVM full transaction; LD 13/13; row
geometry; CPU CG classification; CPU ValueNorm fingerprint/fail-closed; T2/T3
observer nonmutation; and static/private/public guards. The known legacy
`_scoped_attempt3_progress_observers_v1` debt test was not run or edited.
Preflight CUDA probes, AppLaunchers, environments, and formal mutations were 0.

## H. CUDA/CUBLAS readiness

PASS in the one formal worker before importing/constructing AppLauncher. One
deterministic `torch.mm` 2x2 FP32 operation on `cuda:0` returned
`[[19,22],[43,50]]`. Readiness probes: 1; retries: 0.

## I. fresh formal process

One mutation-bearing worker, PID 11120, used one AppLauncher lifetime, one real
environment construction, one explicit initial reset, one private route, and
one persistent learner. No second formal worker or retry was started.

## J. exact runtime config

Runtime resolved `Isaac-Scan-Mobile-Manipulator-Direct-v0`, profile
`event_gated_local_mrta`, `T/E/M/N=2/2/3/12`, `cuda:0`, actor and critic
epochs/minibatches `5/2`, ValueNorm enabled, and `fixed_order=false`.
Environment timing was 30.0 s, max 300 steps, sim dt 1/60 s, decimation 6, and
control step 0.1 s. There was no horizon override.

## K. horizon separation

The learner rollout length remained `T=2`; the environment horizon remained
30.0 s / 300 physical steps. They were not equated.

## L. 160-update definition

The required definition was tx001 through tx160, two physical transitions per
transaction. Actual: tx001 collected two transitions and reached production
S10, but failed during its first append-only ledger serialization. Therefore
ledger-qualified updates are 0/160 and overall RE1 is NOT COMPLETE.

## M. update-ID inventory

Only `b2-t4-re1-normal-horizon-training-11120-tx001` was created. tx002 and
tx161 were not started.

## N. episode/update/physical-step timeline

Global physical steps 1-2 belonged to tx001 and episode generation 0. Both
steps were nonterminal. No source-authoritative terminal/autoreset occurred;
there was no learner-boundary reset.

## O. lifecycle decision summary

Across 12 `E x M x T` row receipts, 6 were policy decision rows and 6 genuine
continuation rows; forced no-op rows were 0. Exactly 6 policy batch
participations occurred. Missing, duplicate, and continuation-resample faults
were all 0.

## P. actor-order distribution

The sole actor permutation was `[1,2,0]`. A 160-update distribution was not
reached.

## Q. zero-DVM runtime statistics

tx001 had DVM populations `[2,2,2]`; real zero-DVM actor/transaction rows were
0. The required real W3 witness was not reached. The separate preflight
zero-DVM full transaction passed but does not replace W3.

## R. all-zero-decision runtime statistics

No real all-zero-decision transaction occurred. It is optional, not the cause
of STOP.

## S. actor plan/update counts

tx001 expected and observed actor backward/optimizer steps were `[5,5,5]` and
`[5,5,5]`, totals 15/15.

## T. factor audits

All three tx001 actor factor segments completed and passed the reviewed factor
audit. A 160-transaction factor total was not reached.

## U. critic classifications

tx001 produced 5 `VALID_NONZERO_UPDATE` and 5
`VALID_ZERO_EFFECTIVE_UPDATE` critic minibatches; every one of its 10
minibatches was classified.

## V. critic/ValueNorm counts

tx001 critic backward/optimizer steps were 10/10 and ValueNorm updates were 10.
The 160-update totals were not reached.

## W. nonterminal bootstrap evidence

tx001 was all-NONE: four NONE rows, expected terminal keys 0, observed keys 0,
adapter PASS, event returns once, stock `compute_returns` 0, and S0-S10 PASS.
This is direct real-runtime nonterminal evidence, but the dedicated W4 ledger
artifact was not emitted because the serializer failed while producing the
first ledger batch; W4 overall remains NOT QUALIFIED.

## X. terminal bootstrap evidence

Not reached. No terminal or TIME_LIMIT row occurred in the two physical steps.

## Y. terminal reconciliation runtime evidence

tx001 reconciled expected `()` to observed `()` exactly. There were no missing,
extra, duplicate, stale, or wrong-generation keys.

## Z. actor Adam continuity

All actor parameter Adam counters advanced exactly 0 -> 5 in tx001. Cross-tx
continuity was not reached.

## AA. critic Adam continuity

All critic parameter Adam counters advanced exactly 0 -> 10 in tx001.
Cross-tx continuity was not reached.

## AB. ValueNorm continuity

The live ValueNorm update count was 10 and its state remained finite. No bridge
existed for cross-update continuity.

## AC. 159-bridge summary

0/159. tx002 never started.

## AD. collection learner immutability

PASS for tx001: actor, actor optimizer, critic, critic optimizer, and ValueNorm
snapshots were unchanged during its two-step rollout collection.

## AE. learner-update runtime/P2 immutability

PASS for the one reached update. Before/after digest was identically
`082a1f29e089a41952c3e550d4c371b44299edf9c8513b6608a8361cb0eaadff`;
environment common step remained 2 -> 2. Aggregate: 1/160, not the required
160/160.

## AF. W1 cross-update ownership witness

NOT REACHED. No next rollout/bridge was allowed after the tx001 post-mutation
evidence failure.

## AG. W2 multi-update completion witness

NOT REACHED. No task-completion event occurred in steps 1-2 and no second
transaction began.

## AH. W3 zero-DVM witness

NOT REACHED. All three tx001 actors had two DVM rows.

## AI. W4 nonterminal bootstrap witness

Semantic candidate present in tx001 as described in W, but required dedicated
artifact/gate not completed. Final status: NOT QUALIFIED.

## AJ. W5 normal-horizon terminal/autoreset witness

NOT REACHED. The run stopped at physical step 2, before the max-300 boundary.

## AK. W6 post-autoreset learned-training witness

NOT REACHED because W5 was not reached.

## AL. W7 learner-update runtime/P2 immutability summary

1/160 exact, with zero learner-induced simulation advancement in tx001.
Required 160/160 was not reached.

## AM. task-progress trajectory

At step 1, six tasks were claimed across two environments; step 2 continued
the same six assignments. Coverage remained 0 and TASK_COMPLETED events were 0.
No performance interpretation is made from this two-step prefix.

## AN. completion/P2/coverage consistency

Not applicable: no completion was observed. The required capability gate
`TASK_COMPLETED>=1`, positive completed-count delta, and coverage max > 0 was
not reached.

## AO. completion -> reopen evidence

NOT REACHED.

## AP. terminal-ledger continuity

The tx001 terminal ledger was empty as required for its all-NONE rollout and
was reconciled before mutation. No S10-to-next-S0 continuity boundary existed.

## AQ. event-return compute-once continuity

tx001 event-return construction: 1; stock HARL `compute_returns`: 0. Required
run totals 160/0 were not reached.

## AR. S7/S8/S9/S10 summary

Production tx001 reached `1/1/1/1`, proven by its durable S10 artifact.
Overall required `160/160/160/160` was not reached. The base worker's
`successful_transactions_before_failure=0` reflects that the test-side ledger
exception occurred before its outer transaction list/bookkeeping increment,
not that production S10 was absent.

## AS. numerical health

tx001 actor/optimizer, critic/optimizer, ValueNorm, losses, gradients, returns,
and factors were finite. No later numerical claim is available.

## AT. diagnostic training metrics

Two-step team reward sum was approximately `-0.07066666894`; coverage,
duplicate scans, reach violations, completion/release/failure events were all
0. Actor loss/gradient receipts numbered 15; critic loss/gradient receipts
numbered 10. These are descriptive only.

## AU. rolling health checkpoints

No append-only rolling-health ledger row was emitted because the first ledger
batch failed before any ledger write. The durable tx001 S10 artifact retains
the complete learner snapshots and numerical receipts.

## AV. artifact inventory

Retained evidence outside the artifact directory:

- formal runner under `scripts/environments/`: 56862 bytes, SHA-256 `ed1a52c71824563192b943f5d4471fecd58363e1f4edb5e657f42c14e42f025f`
- pre-rewrite TASK_PROGRESS archive in the date directory: 8352 bytes, SHA-256 `389699f454c4f5285ace1336fd13f57d24f9abeaa5b59576e11bae6089f35be1`

All phase-level machine-readable evidence is retained under
`202609/20260913/b2_t4_re1_artifacts/`:

- `re1_static_draft.json` (static source-authority draft): 200746 bytes, SHA-256 `920a48bdd51b558e5dafaa27c125dc867a76b7a36a38c0683e0b8846ed9a31a0`
- `b2_t4_re1_preflight_summary.json`: 830 bytes, SHA-256 `6f6afbd4a893d814d3cc2ae0617ac74463b1e52143a7611a4be2473085abd136`
- `b2_t4_re1_formal_supervisor_result.json`: 220053 bytes, SHA-256 `f63608a379adb3406ab8580f5f0ab74dfa226124aeee23cadab8030f0fdca0b9`

- CUDA receipt: 213 bytes, SHA-256 `a57b28dc04fd0c0f283eab0ca1de6c3170b8a9330e832d42509ca0211d17a212`
- process/config authority: 214114 bytes, SHA-256 `1a655e2de413a2c113658ddc3db30edf442711a8b8a28ac38997a73ce5df218c`
- tx001 rollout decision: 29786 bytes, SHA-256 `2a2ff13446b8c65b0e1e34b510d1393bf0ec282ed76ab14ecb79c861900c0878`
- tx001 pre-mutation: 25249 bytes, SHA-256 `18fdb7d1c3d5827711d03599530397643da1fef61a7e1659e9517b171fe2cca3`
- tx001 actor progress: 6723 bytes, SHA-256 `49ba9c7c1923b9cf080d4fa7cc5a0db8c9826affb824f8822bbf11ba42e51319`
- tx001 critic progress: 787315 bytes, SHA-256 `62be57c6e43e873735c214650c7c754e9318b2c0f78aa9552cd4cc6ae40b292e`
- tx001 S10: 465213 bytes, SHA-256 `e21591961c59e60a71cd9f27b6515a3f266bd7ac869ecff51e8b1600761e5649`
- original worker failure: 2222 bytes, SHA-256 `ed5558af4f401fe77dd27fb7c7538292cc36bcbb4f5c184186b506afcbda5247`
- final failure adjudication: 2415 bytes, SHA-256 `1cc0998de076d7cd3c2bdaac740d3ad252b4ebaf64fd8d83cc2c13b2da8360cd`

The failure adjudication records the final evidence classification. No
model-weight file exists. Embedded old top-level path strings inside frozen
`working_tree_status` receipts remain the exact historical pre-move snapshots;
they were intentionally not rewritten as live references.

## AW. static/private/public guards

PASS. Private test-only route construction was 1; public activation was 0.
Checkpoint I/O, evaluation, playback, video, and baseline comparison were 0.

## AX. exact execution counts

```text
pre-runtime qualification Python invocations: 15 (13 PASS, 2 harness-authoring source-drift failures)
formal supervisors / mutation-bearing workers: 1 / 1
CUDA-CUBLAS readiness probes / PASS / retries: 1 / 1 / 0
AppLauncher / real environment / explicit reset / persistent learner: 1 / 1 / 1 / 1
fresh rollout batches / physical steps: 1 / 2
production transactions reaching S10 / ledger-qualified transactions: 1 / 0
distinct update IDs / bridges: 1 / 0
actor backward / optimizer.step: 15 / 15
critic backward / optimizer.step / ValueNorm.update: 10 / 10 / 10
event returns / stock compute_returns: 1 / 0
S7 / S8 / S9 / S10: 1 / 1 / 1 / 1 production receipts
runtime-P2 immutability: 1 / 160
terminal-autoreset events: 0
TASK_COMPLETED / completed delta / coverage max: 0 / 0 / 0
checkpoint I/O / public activation / evaluation-playback: 0 / 0 / 0
production semantic modifications / post-mutation retries: 0 / 0
tx002 / tx161 started: 0 / 0
```

## AY. retained nonclaims

This does not establish B2-T4-RE1 completion, 160-update stability, W1-W7,
normal-horizon terminal handling, task-progress capability, training quality,
convergence, checkpoint continuation, long/paper-scale training readiness, or
public learned-policy readiness.

## AZ. final quiescence

The production tx001 S10 receipt was quiescent, but the subsequent test-side
evidence exception occurred after irreversible learner mutation. The worker
therefore marked the route poisoned and stopped. Overall final quiescence gate:
FAIL/NOT COMPLETE.

## BA. final classification

`PHASE-B2-T4-RE1-STOP-TX001-EVIDENCE-LEDGER-SERIALIZATION-NOT-COMPLETE`

Root cause: test-side evidence code attempted `int(list)` because it flattened
the actual `[T,E,1]` termination-reason grid as though it were `[T,E]`. This
occurred after the tx001 S10 JSON was durable. It is not a production semantic
defect. Mutation had begun, `partial_update=true`, route poisoning is required,
and the single-run authorization forbids repair-and-retry in this phase.

## BB. GPT-review handoff

Review the formal source identity, CUDA receipt, tx001 S10 receipt, original
worker failure, and failure adjudication together. Any future retry requires a
new explicit authorization and a new fresh formal process; this report does
not authorize one. The test-side serializer defect may be repaired only as a
separately reviewed preparation for such a future authorization.
