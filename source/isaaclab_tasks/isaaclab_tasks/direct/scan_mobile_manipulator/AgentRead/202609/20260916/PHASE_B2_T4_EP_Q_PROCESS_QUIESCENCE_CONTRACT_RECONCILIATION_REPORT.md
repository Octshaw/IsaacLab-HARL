# Phase B2-T4-EP-Q — Process-Quiescence Contract Reconciliation Report

Date: 2026-09-16  
Classification: `PHASE-B2-T4-EP-Q-PROCESS-QUIESCENCE-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`

## A. Repository authority

Before modification, the repository was on branch `main`; `HEAD`, `origin/main`, and their merge-base were all `b71d85a32f51be6ada324f870813a56bb45dd396`. The full working-tree porcelain contained 620 lines with SHA-256 `8cf52a579ad9e47398abef19b64b69835a89005c0f8f48068c9bce49585909d3`.

The pre-existing monthly migration remained exactly 359 staged paths. Its staged-index SHA-256 was `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`; its monthly path-set SHA-256 was `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. No index-changing Git command was used.

## B. Starting reviewed authority

The complete B2-T4-EP-P report, historical B2-T4-EP report, historical B2-T4-RE3 report, and current `TASK_PROGRESS.md` were read. The frozen EP-P harness and the immutable formal worker receipt, supervisor result, process-quiescence, reset/structure, and final-result artifacts were inspected.

Closed and historical phase states were retained. EP-Q was treated only as a pure test-side process-quiescence contract reconciliation. It was not treated as B2-T4-RE4 authorization.

## C. Historical EP-P preservation

B2-T4-EP-P remains permanently:

`PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED`

The historical report, harness, worker receipt, supervisor result, process-quiescence artifact, reset/structure artifact, and final result were not modified. EP-Q created only new source and evidence under its own v2 contract.

## D. EP-P formal evidence summary

The preserved worker receipt is valid and durable. It binds run ID `b2-t4-ep-p-20260916-formal01-96eeee85a87243989f7223289db785ee` to worker PID `15116`; reset, structural assertions, pre-App-close persistence, flush/`fsync`, readback, `env.close()`, and `app_close_invoked` all passed. Physical steps, learner constructions, and learner mutations were 0.

The external supervisor recorded wait completion, return code 0, no timeout, original PID absent, and no matching formal worker. It recorded `shutdown_observed=false`. These externally captured facts, rather than the worker's own receipt, are the process-termination authority.

## E. Old process-quiescence predicate

The frozen EP-P source SHA-256 is `82491e3200ad8106f4d5d447f40fef02e0e1fa4399feac29b12abe277a85b6c6`. Its actual source expressions were:

- line 939: `shutdown_observed = "Simulation App Shutting Down" in (stdout + stderr)`;
- line 950: `"pass": bool(process.poll() is not None and not pid_active and not matching_workers and not timed_out and shutdown_observed),`;
- line 952: `supervisor_pass = bool(validation["qualification_pass"] and process_quiescence["pass"])`.

Therefore the exact old composition was:

```text
receipt qualification
AND wait completed
AND worker PID absent
AND matching worker set empty
AND not timed out
AND shutdown marker observed
```

Return code 0 was enforced within `validation["qualification_pass"]`, not in the local line-950 process expression.

## F. Direct process-state evidence

Layer B uses facts supplied by an external supervisor/process handle:

- subprocess wait completed;
- timeout is false;
- return code is 0;
- original worker PID is no longer active;
- no matching formal-worker process remains.

These facts directly address whether the specific worker terminated and whether an isolated matching worker remains.

## G. Log-observation evidence

Layer C records whether the Simulation App shutdown marker appears in captured stdout/stderr and records SHA-256 digests and byte counts for both streams. Such text can support a shutdown narrative, but it is an observation of captured logging, not direct process state.

## H. Evidence-layer separation

The frozen v2 contract defines:

- Layer A — durable worker pre-shutdown qualification;
- Layer B — external process termination;
- Layer C — supplemental shutdown diagnostics.

Only Layers A and B are hard gates. Layer C is machine-readable but non-authoritative for process quiescence.

## I. New v2 quiescence contract

Schema: `b2_t4_ep_q_process_quiescence_v2`.

```text
worker_pre_shutdown_qualified
AND subprocess_wait_completed
AND NOT timed_out
AND return_code == 0
AND worker_pid_absent
AND matching_formal_worker_pids == empty
= PROCESS_QUIESCENCE_PASS
```

`shutdown_marker_observed` does not participate in this conjunction.

BEFORE: process quiescence required direct process disappearance and observation of a specific Simulation App shutdown text marker.

AFTER: process quiescence is established by a valid pre-shutdown worker receipt plus direct external child-termination evidence; shutdown text is retained only as supplemental diagnostic evidence.

## J. Claim boundary

The permitted v2 PASS claim is only:

> The formal worker process reached externally observed process-level quiescence.

It does not establish that `SimulationApp.close()` returned normally to Python, every internal Kit shutdown callback executed, or captured stdout/stderr contains the complete Kit shutdown lifecycle. The receipt establishes only that `app_close_invoked=true` was persisted before termination.

## K. Shutdown-marker nonauthority

For the narrow question “does the formal worker still exist?”, direct process state has priority over captured log text. A marker cannot override a live PID or residual matching worker. A missing marker cannot override completed wait, return code 0, absent original PID, and an empty matching-worker set.

The reconciler has no `SHUTDOWN_MARKER_MISSING` STOP reason.

## L. Canonical reconciler

The canonical pure helper is `scripts/environments/_assignment_phase_b2_t4_ep_q_process_quiescence.py`, SHA-256 `bb56c8c6ebe7b93353640b4c161845f88ed281a6bc991acf35a376ad6b39b52d`. Its authority function is `reconcile_process_quiescence_v2(...)`.

It validates the envelope and payload schemas, payload digest, run ID, PID binding, worker status, reset/structure, persistence, close, and zero forbidden counters separately from external process predicates. It returns hard predicates, three evidence layers, ordered fail-closed reasons, diagnostics, claim, and nonclaims. It imports no Isaac, environment, or learner code.

## M. Positive matrix

All 3 synthetic positives passed:

| Receipt valid | Wait done | Timeout | RC | PID absent | Matching workers | Marker | Expected | Observed |
|---|---|---|---:|---|---|---|---|---|
| yes | yes | no | 0 | yes | none | yes | PASS | PASS |
| yes | yes | no | 0 | yes | none | no | PASS | PASS |
| yes | yes | no | 0 | yes | none | empty streams | PASS | PASS |

Every positive still required a valid Layer A receipt.

## N. Negative matrix

All 15 negatives stopped with no unexpected PASS:

| Case | Expected/observed reason |
|---|---|
| marker present, worker PID active | `WORKER_PID_STILL_ACTIVE` |
| marker present, matching worker remains | `MATCHING_WORKER_PROCESS_REMAINS` |
| marker present, wait incomplete | `PROCESS_WAIT_NOT_COMPLETE` |
| marker present, timeout true | `PROCESS_TIMEOUT` |
| marker present, nonzero return | `PROCESS_RETURN_CODE_NONZERO` |
| process gone, receipt missing | `WORKER_RECEIPT_MISSING` |
| process gone, receipt malformed | `WORKER_RECEIPT_MALFORMED` |
| process gone, wrong run ID | `RUN_ID_MISMATCH` |
| process gone, wrong PID binding | `PID_BINDING_MISMATCH` |
| process gone, `env_close_pass=false` | `ENV_CLOSE_NOT_QUALIFIED` |
| process gone, `app_close_invoked=false` | `APP_CLOSE_NOT_INVOKED` |
| process gone, `reset_pass=false` | `RESET_NOT_QUALIFIED` |
| process gone, structure false | `STRUCTURE_NOT_QUALIFIED` |
| process gone, learner mutation nonzero | `LEARNER_MUTATIONS_NONZERO` |
| stale receipt from another attempt | `RUN_ID_MISMATCH` |

## O. Marker-present but process-live witness

With a valid receipt and marker present, setting the original worker PID active produced STOP with `WORKER_PID_STILL_ACTIVE`. A second witness with a residual matching worker produced `MATCHING_WORKER_PROCESS_REMAINS`. This proves the marker cannot substitute for process termination.

## P. Marker-absent but process-gone witness

With a valid receipt, wait complete, timeout false, return code 0, original PID absent, and no matching worker, marker absence produced PASS. Empty captured streams with the same direct evidence also produced PASS. This is the preserved EP-P evidence pattern.

## Q. Receipt/run/PID fail-closed evidence

Missing, malformed, wrong-run, wrong-PID, and stale receipts all stopped. Run ID plus worker PID binding remains mandatory. The worker cannot self-certify external termination: receipt fields qualify Layer A only, while wait/return/PID/process-scan facts must be supplied independently to Layer B.

## R. PID/process-identity reasoning

For future use, the direct subprocess handle's completed wait and return code are the primary authority for the specific child. The immediate original-PID absence check and matching-command-line worker scan are additional fail-closed isolation checks, not substitutes for the handle.

PID reuse is bounded without a new dependency: a completed handle already proves the original child terminated. An immediately reused PID can at worst make the absence check conservatively STOP; it cannot make a live original child appear successfully waited. The empty matching-worker scan adds independent isolation.

## S. Immutable EP-P artifact identities

All required historical identities passed before replay:

| Artifact | SHA-256 |
|---|---|
| `formal_worker_receipt.json` | `47b5a5156b95c6a829bb45d6dd844a1e281221d1aef2b15cd301b28c033f4af0` |
| `formal_supervisor_result.json` | `f8af60a6fe2887e8899b445b5725719f6fc723741d74a4ccc1a2429120b6fea5` |
| `process_quiescence.json` | `8ae58d1d0efeb74971af756a1a1433821bc5c781ae1c0a59e13db8c208d522fe` |
| `reset_structural_evidence.json` | `7f695e9eebc9b283cfb87c0d3a71264ba4d2b59a84b744beabf054f6182186aa` |
| `final_result.json` | `8e0bad06a92defb3715d9ba36b6589958c4c2a2930cb71c0db2b13d4a9b6b583` |

## T. Old-contract EP-P replay

The source-faithful old reconciler consumed the immutable EP-P receipt qualification, captured process facts, and captured streams. It reproduced:

```text
worker receipt qualified: true
direct process exit pass: true
shutdown marker observed: false
old process quiescence: false
old supervisor pass: false
classification: PHASE-B2-T4-EP-P-STOP-PROCESS-QUIESCENCE-NOT-ESTABLISHED
```

## U. EP-Q-v2 EP-P replay

The same immutable evidence passed the exact canonical v2 reconciler: every Layer A and Layer B hard predicate was true; Layer C recorded marker false, stdout digest `926fc134448290fe1e25bb11695ccebe17ef392dd2d4bb3af5d6a9b8aa068476`, and empty-stderr digest `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

Primary replay table:

| Predicate | Preserved EP-P value | Old EP-P role | New EP-Q role |
|---|---|---|---|
| valid worker receipt | true | required | required |
| `env.close` PASS | true | required | required |
| `app_close_invoked` | true | required | required |
| wait completed | true | required | required |
| timeout | false | required | required |
| return code | 0 | required via receipt validation | required in Layer B |
| worker PID absent | true | required | required |
| matching workers | none | required | required |
| shutdown marker | false | required, caused STOP | diagnostic only |
| overall | — | STOP | PASS under v2 |

## V. Historical non-reclassification statement

The EP-P historical classification remains STOP. EP-Q v2 only establishes that the preserved EP-P direct process evidence satisfies the newly versioned process-quiescence contract. It does not rewrite or reinterpret EP-P as having passed its own historical contract.

## W. Diagnostic output schema

Each v2 result separates `hard_predicates` from `layers.C_supplemental_shutdown_diagnostics`. Layer C exposes:

- `shutdown_marker_observed`;
- `captured_stdout_digest` and byte count;
- `captured_stderr_digest` and byte count;
- `authoritative_for_process_quiescence=false`.

The result explicitly identifies `source_contract` and `evaluation_contract`, preventing silent reinterpretation of historical artifacts.

## X. Production/source preservation

Protected identities remained exact:

- full transaction: `a45db23b863c51334b15205b3c50fa5997ab8f5e4a32f8c4a801242365b583d7`;
- real adapter: `57419d52caa77160609f77b289979ed6785fc645eab1b17320e9cbda1e9500ac`;
- scan environment: `f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363`;
- frozen EP-P harness: `82491e3200ad8106f4d5d447f40fef02e0e1fa4399feac29b12abe277a85b6c6`.

Production source modifications and EP-P harness modifications were 0. The EP-Q qualification runner SHA-256 was `a2f091e7d52fd95560cf7dd38c68924f18c661ac765322e8ab17bd7997901305`.

## Y. Exact execution counts

```text
pure/static Python invocations: 3
canonical reconciler qualification runs: 19
synthetic positive cases: 3
synthetic negative cases: 15
unexpected negative passes: 0
immutable EP-P retrospective replays: 2 (old + v2)
AppLauncher lifetimes: 0
real environment constructions: 0
environment resets: 0
physical environment steps: 0
learner constructions: 0
learner mutations: 0
actor backward/step: 0/0
critic backward/step: 0/0
ValueNorm updates: 0
checkpoint I/O: 0
public activation: 0
evaluation/playback: 0
production source modifications: 0
historical EP-P harness modifications: 0
B2-T4-RE4: NOT STARTED
git add/commit/push: 0/0/0
```

The three Python invocations were approved-interpreter identity, one `py_compile` command for both new files, and one pure qualification runner. None imported or launched AppLauncher.

## Z. Retained nonclaims

EP-Q does not establish that `SimulationApp.close()` returned, that internal Kit shutdown callbacks completed, or that log capture was complete. It does not qualify environment semantics, lifecycle/P2 changes, NR/SR/ZD changes, learner behavior, optimizer or ValueNorm behavior, checkpoint continuation, public-route readiness, evaluation/playback, RE4, normal-horizon training, or long/paper-scale training.

## AA. Final classification

All 33 success requirements applicable to this contract-only phase passed. The classification is:

`PHASE-B2-T4-EP-Q-PROCESS-QUIESCENCE-CONTRACT-QUALIFIED-AWAITING-GPT-REVIEW`

Recommended state:

```text
B2-T4-EP-P: STOPPED / HISTORICAL / NOT QUALIFIED
B2-T4-EP-Q: COMPLETE / AWAITING GPT REVIEW
worker pre-shutdown evidence: QUALIFIED
direct external process termination: QUALIFIED
shutdown log marker: DIAGNOSTIC / NON-BLOCKING
immutable EP-P replay under EP-Q v2: PASS / AWAITING GPT REVIEW
AppLauncher / environment / learner: 0 / 0 / 0
B2-T4-RE4: NOT AUTHORIZED
```

This is not a self-issued GPT REVIEW PASS.

## AB. GPT-review handoff

Independent review should inspect the exact old-source predicate, Layer A/B separation, marker nonauthority witnesses, all 15 negative cases, immutable artifact hashes, and the explicit historical non-reclassification statement. The machine-readable evidence is under `202609/20260916/b2_t4_ep_q_artifacts/`.

Do not start B2-T4-RE4, launch AppLauncher, construct an environment or learner, begin B2-R6, perform checkpoint I/O, activate the public learned-policy route, or run evaluation/playback or long training. Stop and wait for independent review.
