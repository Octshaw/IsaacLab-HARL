# Phase B2-T4-SR Evidence-Ledger Serializer Repair Qualification Report

Date: 2026-09-13

## A. Repository authority

Before the phase edits, the repository was on `main`; `HEAD`, `origin/main`,
and their merge-base were all
`b71d85a32f51be6ada324f870813a56bb45dd396`. The working-tree porcelain had
490 lines and SHA-256
`9b39d90bcf09c7f5fce03339ce5a89921370cc509a0bafcc7bfce03bfef0c13c`.
The pre-existing staged monthly migration contained exactly 359 paths. Its
staged-index SHA-256 remained
`a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`,
and its monthly path-set SHA-256 remained
`0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`.
Ending verification found 359 staged paths, the same two hashes, and no SR
path in the index. No `git add`, commit, push, reset, checkout, or clean was
run.

## B. Starting reviewed authority

B2-R0 through B2-R7 and B2-T0 through B2-T3 are GPT REVIEW PASS / CLOSED.
The original B2-T4 attempt is historical and not complete. B2-T4-NR is GPT
REVIEW PASS / CLOSED. B2-T4-RE1 entered this phase as a historical STOP with
the authoritative adjudicated classification
`PHASE-B2-T4-RE1-STOP-TX001-EVIDENCE-LEDGER-SERIALIZATION-NOT-COMPLETE`.

## C. Historical RE1 STOP preservation

RE1 remains STOPPED / HISTORICAL / POISONED / NOT COMPLETE. Its tx001
production transaction reached S10 before the test-side ledger failure;
`partial_update=true`, `route_poisoned=true`, and post-mutation retry count is
0. All 12 retained RE1 JSON artifacts were hash-checked before and after the
qualification and remained byte-identical. This phase did not reuse or start
an RE1 process, AppLauncher, environment, learner, optimizer, ValueNorm,
buffer, transaction ID, or ledger.

## D. Exact serializer failure trace

The real worker captured `buffer.termination_reason.detach().clone()` as a
`torch.Tensor` with dtype `torch.int64`, device `cuda:0`, and shape `[2,2,1]`.
After the existing normalizer, the retained S10 representation was
`list[list[list[int]]]`. The old expression was:

```python
tuple(tuple(int(value) for value in row) for row in normalized["termination_reason_grid"])
```

At each `value`, the object was a singleton list such as `[0]`, producing the
observed `TypeError: int() argument must be a string, a bytes-like object or a
real number, not 'list'`. A pure regression fixture reproduced that exact
defect.

## E. Canonical reason-grid schema

The frozen canonical geometry is rank 3, `[T,E,1]`. `T` and `E` are resolved
from the current transaction evidence. The final singleton axis is preserved.
The canonical scalar at `grid[t][e][0]` is an integer in the existing
`TerminationReason` domain.

## F. Old serializer behavior

The old code implicitly treated rank-3 rows as rank-2 scalars. It neither
validated the geometry nor preserved the final singleton dimension and failed
with a raw `int(list)` TypeError on the real all-NONE tx001 evidence.

## G. Repaired serializer contract

The test-side helper validates container, rank, exact `T`, exact `E`, trailing
size 1, scalar type, and canonical reason domain in that order, then returns a
deterministic `list[list[list[int]]]`. It uses no generic `flatten()`,
`reshape(-1)`, or recursive scalar coercion. The RE1 ledger append path now
uses this single helper and records shape and schema metadata.

| Case | Old behavior | New expected | New actual |
|---|---|---|---|
| canonical `[T,E,1]` all NONE | `int(list)` TypeError | PASS | PASS |
| canonical `[T,E,1]` mixed | unsafe/failed | PASS | PASS |
| malformed `[T,E]` | accidental acceptance possible | STOP | STOP — `EVIDENCE_REASON_GRID_RANK_MISMATCH` |
| malformed `[T,E,2]` | ambiguous | STOP | STOP — `EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON` |
| invalid reason | unclear | STOP | STOP — `EVIDENCE_REASON_VALUE_INVALID` |

## H. Rank/shape validation

The helper rejects rank 2, trailing size 2, swapped axes, flattened geometry,
ragged rows, wrong nested depth, empty grids, and runtime `T`/`E` mismatches.
Tensor and ndarray shapes are checked before conversion. Nested Python inputs
are walked explicitly and must be rectangular.

## I. Reason-value validation

The helper uses the canonical production enum, loaded under its exact module
identity for pure testing without importing the package initializer. The
frozen values are `NONE=0`, `ALL_TASKS_COMPLETED=1`,
`NO_FEASIBLE_TASKS_REMAIN=2`, and `TIME_LIMIT=3`. Unknown integers, floats,
strings, nested values, NaN-like non-integers, and bool values are rejected.
No second mapping was introduced.

## J. Supported source container types

Supported inputs are `torch.Tensor`, `numpy.ndarray`, nested `list`, and nested
`tuple` (including a canonical list/tuple mixture). Tensor handling is
observational: shape is checked first, then the tensor is detached and moved
to CPU for conversion. The source is not mutated.

## K. Serialized ledger schema

The ledger field is
`nonterminal_bootstrap.termination_reason_grid`, represented as JSON arrays in
canonical `[T,E,1]` geometry with integer reason values. Accompanying fields
are `termination_reason_grid_shape` and `termination_reason_grid_schema`, with
schema `b2_t4_sr_termination_reason_grid_T_E_1_v1`. Downstream evidence does
not require `[T,E]`, flattened rows, or reason names.

## L. Deterministic serialization

Every positive case was serialized repeatedly. Python values compared equal,
and stable-key JSON byte semantics compared equal. No device string, object
address, or tensor representation enters the serialized grid.

## M. Nonmutation

Positive and negative source inputs, the retained tx001 payload, Python RNG,
NumPy RNG, and Torch CPU RNG were unchanged. The actual append replay also
verified its input payload digest before and after. Mutation count and CUDA API
call count were both 0.

## N. Positive matrix

All 7/7 cases passed: all-NONE `[2,2,1]`; mixed `[2,2,1]`; NumPy `[2,3,1]`;
tuple `[4,2,1]`; CPU tensor `[2,2,1]`; mixed list/tuple `[2,2,1]`; and repeated
determinism.

## O. Negative matrix

All 12/12 malformed cases stopped with the expected diagnostic: rank-2
`[T,E]`, trailing size 2, swapped `E/T`, ragged rows, invalid integer, wrong
depth, non-integral scalar, bool, missing grid, empty grid, `T` mismatch, and
`E` mismatch. Repaired-path raw TypeError count was 0.

## P. Precise failure diagnostics

The frozen test-side diagnostics are
`EVIDENCE_REASON_GRID_MISSING`, `EVIDENCE_REASON_GRID_RANK_MISMATCH`,
`EVIDENCE_REASON_GRID_SHAPE_MISMATCH`,
`EVIDENCE_REASON_GRID_TRAILING_DIM_NOT_SINGLETON`,
`EVIDENCE_REASON_GRID_RAGGED`, and `EVIDENCE_REASON_VALUE_INVALID`.

## Q. Real RE1 tx001 replay

The immutable retained S10 artifact with SHA-256
`e21591961c59e60a71cd9f27b6515a3f266bd7ac869ecff51e8b1600761e5649`
was read directly. Its normalized reason grid was `[2,2,1]`, all four values
remained integer NONE values, serialization passed, and source bytes were
unchanged.

## R. Append-ledger roundtrip

One synthetic transaction with the exact RE1 schema traversed the actual
`_append_transaction_ledgers(...)` path. Eight append-only ledger files and
one row per ledger were written and read back. The reason grid equaled the
input exactly at shape `[2,2,1]`; schema metadata and source nonmutation checks
passed.

## S. Full tx001 post-S10 bookkeeping replay

One replay used the retained immutable tx001 S10 payload without any learner
mutation. It created and read back the transaction, training metric,
nonterminal bootstrap, terminal reconciliation, lifecycle task progress,
learner runtime immutability, rolling health, and episode/update timeline
rows. All eight ledger counts were exactly 1; field equality, hashes, and the
`[2,2,1]` grid contract passed. No new S10 result was fabricated.

## T. Classification precedence

Future summaries now distinguish
`raw_worker_classification`, `final_phase_classification`, and
`adjudication_source` under schema
`b2_t4_sr_classification_precedence_v1`. The retained raw worker value remains
`PHASE-B2-T4-RE1-STOP-TX1-BOUNDED-SMOKE-FAILURE-NOT-COMPLETE`; the authoritative
phase value remains
`PHASE-B2-T4-RE1-STOP-TX001-EVIDENCE-LEDGER-SERIALIZATION-NOT-COMPLETE`, sourced
from `b2_t4_re1_failure_adjudication.json`.

## U. Runner repair

The candidate RE1 test runner now binds the already-imported canonical enum
into its generated worker namespace, invokes the strict helper in the ledger
append path, preserves `[T,E,1]`, and emits the precedence metadata. The runner,
helper, and dedicated suite all passed `py_compile`. The runner was not
executed against Isaac.

## V. Production source identity

Production semantic modifications were 0. Ending identities were exact:

```text
assignment_event_training_full_transaction.py:
  a6b8f4d283d5eaf14a4a7d686e1f3b6424837552d673909ea5808b2bf7d057de
assignment_event_training_real_isaac_adapter.py:
  b85034d7436de4a79c37de0f2e40a09200dfbca225994c0cae2c8f6bcd491014
```

## W. Bounded regression results

- dedicated serializer/ledger/replay suite: PASS;
- serializer positive matrix: 7/7 PASS;
- serializer negative matrix: 12/12 expected STOP;
- actual append-ledger roundtrip: 1/1 PASS;
- retained tx001 post-S10 bookkeeping replay: 1/1 PASS;
- relevant runner/helper/suite `py_compile`: PASS;
- B2-T4-NR contract suite: 5/5 PASS, terminal matrix 14/14;
- static/private/public guards: PASS;
- historical RE1 artifact identity: 12/12 unchanged;
- production source identity: 2/2 unchanged.

Two early dedicated-suite attempts stopped before serialization or artifact
mutation while the pure canonical enum binding was being isolated: first the
generated namespace did not export the enum, then a direct package import
encountered the unavailable Kit `omni` dependency. The final implementation
loads the pure source file under the canonical module identity for unit replay
and reuses the worker's existing canonical import in the future runner. These
were test-harness integration stops, not serializer false passes.

## X. Exact execution counts

```text
pure/static Python invocations: 13
serializer positive cases: 7
serializer negative cases: 12
RE1 historical replay cases: 1
append-ledger roundtrips: 1
post-S10 bookkeeping replays: 1

AppLauncher: 0
real Isaac environments: 0
CUDA readiness probes: 0
formal learners: 0
physical environment steps: 0
actor backward / optimizer.step: 0 formal / 0 formal
critic backward / optimizer.step: 0 formal / 0 formal
ValueNorm.update: 0 formal
learner mutations: 0
checkpoint I/O: 0
public activation: 0
production semantic modifications: 0
B2-T4-RE2 started: 0
git add / commit / push: 0 / 0 / 0
```

The 13 Python invocations include three diagnostic/setup checks, three
`py_compile` passes, one mistyped `py_compile` command that failed before
opening a target, three dedicated-suite invocations (two pre-serializer
isolation stops and the final PASS), one NR suite PASS, one ending-authority
attempt that exited 0 without emitting redirected-stdin output, and one
successful ending-authority verification.

## Y. Files created/modified

Modified test-side candidate:

- `scripts/environments/test_assignment_phase_b2_t4_re1_normal_horizon_learned_training_integration.py`
  — SHA-256 `44ef0a289225a34c21bb31451465422e33fa20a713eb9a3ed4a715e97a0ff5d6`.

Created test-side code:

- `scripts/environments/_assignment_phase_b2_t4_sr_reason_grid_serializer.py`
  — SHA-256 `dcf780a37387e24b4cc3c1f5ee39d006029b04875bc6422c96896cddd8cb5358`;
- `scripts/environments/test_assignment_phase_b2_t4_sr_evidence_ledger_serializer_repair.py`
  — SHA-256 `42dc427aad8caac8743e153e336a5bfae80d353c29f761a3c1070c5454a51de4`.

Created evidence under `b2_t4_sr_artifacts/`:

- `serializer_contract.json` — `64d1ae4ff2ebe82f5e1727330c71248edc8c1d2d00ebecd4406d8b7951f6fb3f`;
- `serializer_positive_matrix.json` — `856a58cb252549a722c59e2af695ebddb1e9dcbb8607045b15e718500f1a84b1`;
- `serializer_negative_matrix.json` — `ab3001b9d7e64fc6da58015f1186acbacf90037b40e3aa42457715181cefca35`;
- `old_failure_reproduction.json` — `65c69a73d472e603a93d2c96b246aa9c903cf215108db80f614e0b96f806d857`;
- `re1_tx001_serializer_replay.json` — `683b2a9e99053eeae3892602dd5ad273a52092b30198c22d7a9c018b1420491c`;
- `ledger_roundtrip.json` — `2f1f6b875b75f7dc4008bffda78bfe85bc872cdaa006b6c564560f7f474fec6b`;
- `tx001_post_s10_bookkeeping_replay.json` — `65cf6938cfb39a354b3d3581b63a66b44cf42ad8b82b353a8953122d023354fd`;
- `production_source_identity_check.json` — `edc4911f46a8666aa9d340a1834f760e3c139cbd48c7f2e43ce90d821b4044e6`;
- `final_result.json` — `5146e959a0cf82929958252748bf8d69b203752d65942bbccaa8a0a12c0154bb`.

Also created this report and the byte-exact pre-rewrite progress archive
`TASK_PROGRESS_ARCHIVE_BEFORE_B2_T4_SR_HANDOFF_20260913.md` (7,803 bytes,
SHA-256
`ff2cbf241354e4483ff17db3d5af56ca0d5d27adaf1a7e300e33cdd5014ec253`),
then updated `AgentRead/TASK_PROGRESS.md`.

## Z. Retained nonclaims

This pure test-side qualification does not establish a fresh normal-horizon
training transaction, checkpoint continuation, 160-update stability, W1-W7
overall qualification, training quality, convergence, evaluation/playback,
long or paper-scale training, or public learned-policy readiness. The public
route remains DORMANT / BLOCKED. B2-T4-RE2 and B2-R6 are not authorized.

## AA. Final classification

`PHASE-B2-T4-SR-EVIDENCE-LEDGER-SERIALIZER-REPAIR-QUALIFIED-AWAITING-GPT-REVIEW`

B2-T4-SR is evidence-ledger serializer repair COMPLETE / AWAITING GPT REVIEW.
This is not a self-classification of GPT REVIEW PASS.

## AB. GPT-review handoff

Review the strict `[T,E,1]` helper contract, the actual RE1 append-ledger
integration, the retained tx001 replay, the 7/7 positive and 12/12 fail-closed
matrices, classification precedence, immutable historical hashes, and zero
production/runtime counts. Do not start B2-T4-RE2, AppLauncher, B2-R6, long
training, checkpoint I/O, evaluation/playback, or public route activation.
