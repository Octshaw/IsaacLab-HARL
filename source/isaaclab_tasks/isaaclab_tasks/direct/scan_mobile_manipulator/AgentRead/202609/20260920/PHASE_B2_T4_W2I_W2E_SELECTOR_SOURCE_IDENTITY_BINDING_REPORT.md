# Phase B2-T4-W2I — W2E selector source-identity binding

Date: 2026-09-20. Classification: `PHASE-B2-T4-W2I-W2E-SELECTOR-SOURCE-IDENTITY-BINDING-QUALIFIED-AWAITING-GPT-REVIEW`. This is a pure/static **candidate identity baseline**, not RE6 and not a self-issued GPT review of the new SHA.

Machine evidence: [W2I artifacts](b2_t4_w2i_artifacts/). Read-only qualification entry: [W2I replay script](../../../../../../../../scripts/environments/test_assignment_phase_b2_t4_w2i_selector_identity_binding.py). It imports the unchanged W2E selector and runner, calls their pure functions, and never calls the W2E runner's artifact-rewriting `main()`.

## A. Repository authority

Before W2I evidence writes: branch `main`; HEAD, `origin/main`, merge-base all `b71d85a32f51be6ada324f870813a56bb45dd396`. Full porcelain: 9,693 lines, UTF-8/LF-with-final-newline SHA-256 `3ecc69c23547a6e2f03138d486a03ecc8edc7a5039d783a4d3e8555ebe6cbb32`. Existing staged migration: 359 paths; staged-index digest `a40169043c3bfffd481a7ed1bddf3e52663d61379bedfd2610781457d11f947c`; monthly path-set digest `0f2b8f7b52148e39196cbeb40fd9f4edd94fb762b6daf8be6279a116b80a39ab`. [Repository authority](b2_t4_w2i_artifacts/repository_authority.json) records the calculation. No staging or commit.

## B. Reviewed starting authority

The user supplies B2-T4-W2E `GPT REVIEW PASS / CLOSED` for its *semantic contract*. B2-R0–R7, B2-T0–T3 and NR/SR/ZD/EP-Q/PW retain reviewed closure. The W2E report, RE6 STOP report, progress handoff, eight named W2E artifacts, and both unchanged W2E Python files were read. This phase creates a separate candidate SHA authority; it does not claim independent review has accepted that SHA.

## C. Historical RE6 STOP preservation

RE6 remains `PHASE-B2-T4-RE6-STOP-W2E-HELPER-IDENTITY-NOT-ESTABLISHED`: pre-formal, no supervisor/worker/CUDA/AppLauncher/environment/learner, `partial_update=false`, `route_poisoned=false`. The RE6 report and final result SHA-256 stayed `4a18979217fb51981ca048e3d39297ac8948f43642bc921b1b33cef02323dbee` and `17bb6a46f821297908dd0c111139c5edf60ad6f062b262046611f05eb413b83a`. W2I neither modifies nor retrospectively passes RE6.

## D. Exact RE6 identity-preflight failure

RE6 required current selector SHA equal to a SHA in the reviewed W2E `source_identity_manifest.json`. The selector entry was absent. Thus the comparison could not be evaluated; it was not a proven unequal-hash result. No RE6 formal attempt was consumed.

## E. Historical W2E source-manifest audit

The reviewed [manifest](b2_t4_w2e_artifacts/source_identity_manifest.json) has schema `b2_t4_w2e_source_identity_v1`, 15 `source_sha256` entries covering production/B1/P2/decision sources, RE1/RE3/RE5 harnesses and PW helper. It has **no** W2E selector SHA, no W2E offline runner SHA, and no contract artifact identity. [Machine audit](b2_t4_w2i_artifacts/historical_w2e_manifest_audit.json) lists every path. Historical manifest SHA-256 `268cac782c6fe477a12450df46615797648f5a84f842723e10fc96fb2149544d` was unchanged.

## F. Identity-gap classification

`REVIEWED IDENTITY BASELINE ABSENT`, **not** `HASH MISMATCH` and not established `SOURCE DRIFT`. The candidate current hash below is not backfilled into historical W2E evidence. [Classification](b2_t4_w2i_artifacts/identity_gap_classification.json) keeps that distinction machine-readable.

## G. W2E selector path

Repository-relative: `scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py`. Absolute: `E:\Project\IsaacLab_HARL\scripts\environments\_assignment_phase_b2_t4_w2e_multi_update_completion.py`. It exists and was not edited.

## H. W2E selector raw-byte identity

15,089 exact on-disk bytes; SHA-256 `8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0`. No line-ending normalization was applied. [Selector identity](b2_t4_w2i_artifacts/selector_identity.json) calls this a **candidate** baseline awaiting review.

## I. Offline runner identity

The unchanged `test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py` is 24,156 bytes, SHA-256 `08758de24b78c9c63b97a94481f37e8a52608171fd1b6d8d048252689ea8cd58`. Its `main()` writes the historical `b2_t4_w2e_artifacts/` directory, so W2I never invokes that entry point. The W2I read-only replay calls its existing `old_replay`, `normalize`, `matrices`, and `ledger` functions without altering them.

## J. Contract artifact identity

The reviewed `w2e_contract_v2.json` has 893 raw bytes, SHA-256 `81440619e14b59b22eaca8d3928e2fd37f9ea1b39818c9f92a918a845a207c3b`. Its parsed `version` is `b2_t4_w2e_multi_update_completion_v2` and describes Layers A–E. This is a semantic contract artifact, not a substitute for the missing historical selector hash.

## K. Static selector semantic audit

[Audit](b2_t4_w2i_artifacts/selector_semantic_audit.json) maps exact source predicates: A unique policy call plus pre/post P2 and admitted effective assignment (`:64–87`); B `claim_tx < completion_tx`, continuous owner/state/generation and qualified pre-completion bridge with forced continuation (`:89–154`); C exact completion event, P2 COMPLETED and count +1 (`:156–168`); D owner/inverse-task clear (`:170–175`); E same-robot NEEDS_ASSIGNMENT/DVM and immediate policy call (`:177–192`). Release/failure, generation, proposal-only, continuation-as-claim and deterministic sorted selection are present. Static semantic match: PASS within this source audit.

## L. Legacy `task_claimed` nonauthority

The selector contains no `task_claimed` requirement. It constructs candidate claim edges from decision rows and validates B1-effective/P2 evidence. Legacy textual claim events remain relevant only to the separate old-W2 diagnostic.

## M. Approved interpreter

`conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"` resolved to `C:\isaacenvs\isaac45_harl\python.exe`. The confirmed read-only qualification used that exact executable directly.

## N. `py_compile`

One command compiled the unchanged selector and original offline runner; another compiled the new read-only W2I replay script. Both returned 0. Compilation does not establish runtime correctness; the pure replay below supplies the bounded behavioral check.

## O. Positive matrix replay

The unchanged runner's `matrices()` passed `one_boundary`, `multiple_boundaries`, and `unrelated_interleaving`: **3/3**. The Python objects matched historical `positive_matrix.json` exactly; canonical result digest `554e4bf1396aebe856960c040d08a0f4cf1070a9eddcdd1866a20812890f5617`.

## P. Negative matrix replay

All **18/18** reviewed negative families stopped; unexpected PASS **0**. The result matched historical `negative_matrix.json` exactly; canonical digest `d6d6a198c9a3ffed25bc1f3abc131fc9f4d75cb10c7c2fabdb13790daadfd18d`.

## Q. Old W2 replay

The unchanged runner's `old_replay()` found `task_claimed=0`, `task_completed=22`, eligible old pairs 0, old W2=`None`, exactly equal to historical `old_w2_replay.json`. Canonical digest `b8b342a27c4d09108ce4cb47c4237dbb8052d17089c305d26797f33731eb59c0`.

## R. Immutable RE5 retrospective replay

The unchanged `normalize()` and exact selector `reconcile()` returned **29** claim candidates and **12** valid chains. Full candidate inventory and selected replay matched historical W2E artifacts exactly; canonical full-result digest `879f54da6950b9d5b741630c0d4d7e25a89fb3c910d7a67c25aac615dcdc66a3`. The selected chain is env 1/robot 1/task 10: claim tx12/step23 → completion tx15/step30 → reopen tx16/step31. The original runner's 14 RE5 baseline artifact hashes matched before and after. No historical RE5 file was written.

## S. W1/W2 semantics cross-check

The reviewed `w1_w2_semantics_crosscheck.json` retains `ownership_definition_consistent=true`: both use canonical P2 owner and active task state plus forced continuation/no policy call at a boundary. W2E adds exact claim, completion, clear and reopen requirements. No ownership-definition drift was found.

## T. Source-before/after identity

The read-only replay hashed the selector, runner and contract artifact before and after execution. All three pairs are byte-identical. [Machine comparison](b2_t4_w2i_artifacts/source_before_after_identity.json) records the values; the selector was neither edited nor normalized.

## U. Historical W2E artifact preservation

The historical manifest, W2E report and W2E final result matched pre-recorded digests before and after replay; the RE6 STOP report/final result also matched. The original W2E runner `main()` was not invoked precisely because it rewrites those historical files. [Preservation record](b2_t4_w2i_artifacts/historical_w2e_preservation.json) is separate from the new W2I artifacts.

## V. Candidate identity-binding manifest

[Versioned binding](b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json) has schema `b2_t4_w2i_w2e_selector_identity_binding_v1` and binds selector bytes/hash, runner bytes/hash, contract artifact hash, exact matrix/replay results, and the historical identity-gap/RE6 STOP boundary. Its own SHA-256 is stored separately in [digest evidence](b2_t4_w2i_artifacts/identity_binding_manifest_digest.json), avoiding a recursive self-hash. The [source snapshot](b2_t4_w2i_artifacts/source_identity_manifest.json) adds interpreter, command, timestamp, HEAD, staged-index and result digests.

## W. Candidate selector SHA

Candidate SHA-256: `8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0`. This is not yet a `REVIEWED_SELECTOR_SHA`. Only independent GPT review of W2I may establish future reviewed identity authority.

## X. Authority boundary

W2E semantic contract: GPT REVIEW PASS / CLOSED per user-provided authority. W2I byte identity: candidate / awaiting independent GPT review. Historical RE6: retained pre-runtime STOP. A new RE6 attempt: **NOT AUTHORIZED**. Neither this replay nor the hash can retroactively qualify RE5 or RE6.

## Y. Exact execution counts

One approved-interpreter check; two `py_compile` commands; three replay commands attempted, of which one `conda run python -c` returned 0 without observable output and two direct approved-interpreter executions produced confirmed PASS (one ad hoc read-only replay and one repeatable W2I script). One extra direct-interpreter print probe diagnosed the outputless command. Thus seven Python command invocations were issued in total. Confirmed old-W2 replays: 2; confirmed RE5-v2 replays: 2; each confirmed replay exercised 3 positives and 18 negatives, with final qualification 3/3 and 18/18. AppLauncher, formal supervisors/workers, CUDA probes, environments, resets, physical steps, learners, learner mutations, checkpoint I/O, public activation, evaluation/playback and RE6 formal attempts: all **0**. Production, historical W2E, RE5 and RE6 STOP modifications: **0**. Git add/commit/push: **0/0/0**. The outputless invocation is not counted as a verified qualification.

## Z. Retained nonclaims

The current SHA is a candidate baseline only. W2I does not prove Isaac runtime behavior, training integration, checkpoint continuation, convergence, long/paper-scale readiness or public-route readiness. The public learned-policy route remains DORMANT / BLOCKED.

## AA. Final classification

`PHASE-B2-T4-W2I-W2E-SELECTOR-SOURCE-IDENTITY-BINDING-QUALIFIED-AWAITING-GPT-REVIEW`. Every bounded static/behavioral gate passed; this is **not** GPT REVIEW PASS for W2I or the selector SHA.

| Item | Path | Bytes | SHA-256 | Role |
|---|---|---:|---|---|
| W2E selector | `scripts/environments/_assignment_phase_b2_t4_w2e_multi_update_completion.py` | 15,089 | `8a4923200c4bee914985dc436e2ebf714c39578e5025fd419d9799b4a0f8abd0` | candidate selector identity |
| W2E offline runner | `scripts/environments/test_assignment_phase_b2_t4_w2e_claim_evidence_contract.py` | 24,156 | `08758de24b78c9c63b97a94481f37e8a52608171fd1b6d8d048252689ea8cd58` | qualification implementation |
| W2E v2 contract | `b2_t4_w2e_artifacts/w2e_contract_v2.json` | 893 | `81440619e14b59b22eaca8d3928e2fd37f9ea1b39818c9f92a918a845a207c3b` | machine contract |
| Historical W2E manifest | `b2_t4_w2e_artifacts/source_identity_manifest.json` | 2,849 | `268cac782c6fe477a12450df46615797648f5a84f842723e10fc96fb2149544d` | preserved; selector absent |
| New W2I binding | `b2_t4_w2i_artifacts/w2e_selector_identity_binding_v1.json` | 1,673 | `3bddfb2b34b2544167267a76beb9bb3bda77d48f49bd23fa79878296c6cdc85b` | candidate authority |

| Gate | Reviewed W2E | W2I reproduction |
|---|---:|---:|
| Positive matrix | 3/3 | 3/3 |
| Negative matrix | 18/18 | 18/18 |
| Unexpected negative PASS | 0 | 0 |
| Old W2 | None | None |
| RE5 candidates | 29 | 29 |
| Valid chains | 12 | 12 |
| Selected env/robot/task | 1/1/10 | 1/1/10 |
| Claim tx/step | 12/23 | 12/23 |
| Completion tx/step | 15/30 | 15/30 |
| Reopen tx/step | 16/31 | 16/31 |

## AB. GPT-review handoff

Review the raw selector/runner/contract hashes, the historical 15-entry manifest absence, five-layer source predicates, the read-only W2I replay's equality against all reviewed matrix/inventory/selection artifacts, the new binding manifest plus its separate digest, and unchanged W2E/RE6 historical hashes. Do **not** edit the reviewed selector or W2E manifest, launch RE6, construct AppLauncher/environment/learner, checkpoint, evaluate/play back, stage or commit. Wait for independent GPT review of W2I before any future RE6 authorization.
