# Phase-B Local Artifact Cleanup Audit

Date: 2026-09-25 (Asia/Shanghai). Mode: PLANNING ONLY / NO DELETION.

Classification: **PHASE-B-LOCAL-ARTIFACT-CLEANUP-AUDIT-PARTIAL-MANUAL-REVIEW-REQUIRED**.

Phase B: **COMPLETE / GPT REVIEW PASS / CLOSED**.
The Phase-B deletion subset is ready for user review. The overall classification
is partial only because 3,602 May-July legacy experiment files cannot be
safely declared disposable under Phase-B authority. Those files are excluded
from both delete allowlists and remain on disk.

## Summary

Scope: **55,105 files / 12,595,559,380 bytes / 12.595559380 GB**.
Recommended deletion after separate approval: **50,639 files /
12,122,958,520 bytes / 12.122958520 GB / 96.2479%**.
Expected remaining audited bytes: **472,600,860**. Actual reclaimed now: **0**.

| Classification | Files | Bytes |
|---|---:|---:|
| DELETE_STRONG | 693 | 13,827,284 |
| DELETE_RECOMMENDED | 49,946 | 12,109,131,236 |
| ARCHIVE_OPTIONAL | 0 | 0 |
| KEEP_LOCAL_USEFUL | 7 | 3,343,441 |
| KEEP_REQUIRED | 646 | 8,033,687 |
| KEEP_COMPACT_EVIDENCE | 211 | 1,281,434 |
| UNKNOWN_REVIEW_REQUIRED | 3,602 | 459,942,298 |

ARCHIVE_OPTIONAL is empty: no compression is necessary to preserve the
selected evidence, and uncertain legacy results must be reviewed, not
automatically archived. KEEP_REQUIRED includes all protected documents and
tracked compact evidence within the inventory; KEEP_COMPACT_EVIDENCE is
separate, so category counts do not overlap.

Sizes are logical file lengths, decimal KB/MB/GB; not measured NTFS allocation
or a guarantee of exact physical free-space gain. Reclaim and remaining totals
apply only to the audited snapshot, not the entire repository or external Isaac
installation. Newly generated audit manifests/reports/helpers and the handoff
backup are excluded from this denominator; they are additional retained bytes.

## Git precondition and authority

Four reviewed groups are present on main:

| Group | Commit |
|---|---|
| A monthly archive migration | c107a6c892eb90ff643d549d928c555ec9f9be5b |
| B production backbone | 5e7367ce28f0dfc3d4de86fa90d751284f1159c3 |
| C test/closure evidence | 947f9261864945ab120a7958f3cc08b38b37e44a |
| D closure documentation / current HEAD | 5e62cd58d631946aa5d68a64c27c8132ae5aef84 |

These were executed under the user's explicit authorization after review of the
manual plan; the conceptual four-commit prerequisite is satisfied. Starting
worktree/index were clean. All Git queries use optional locks disabled and
long-path support. No stage, commit, tag, push, reset or clean was performed.

The optional existing `lifecycle-mrta-phase-b-complete` tag points to the older
b71d85a3 foundation, not this final HEAD. It is not used as closure authority
and was not moved. Frozen pre-commit reports/identities remain unchanged.

Starting index SHA256:
`2712362dd719e06b45c376989caa51dfe38c8a8c919bfbd3cb3d31a04ace7e8e`.
Local exclude SHA256:
`b597c89cf3526430bfab8212cf5be260c84fae225fc7323a5db29795db1bfaa5`.

## Inventory scope and protection

Filesystem enumeration includes ignored files, not just Git status:
50,815 files / 12,126,232,065 bytes in both AgentRead roots, plus
4,290 files / 469,327,315 bytes in project-local cache/legacy output roots.
The anomalous `source/isaac_tasks/.../AgentRead` R8 location is included;
its three compact STOP receipts are retained in place.

AR below means
`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead`.
All tracked files, production/test/offline-helper source, all Markdown reports
and TASK_PROGRESS archives, current docs, final source/config authority,
final accepted/G1-G10 compact evidence, CKPT1 compact JSON and Git metadata
are protected globally, including outside the inventory. No source is
classified disposable just because its filename says probe or test.
The R1 generated `transaction_table.md` is a protected mixed-tree exception.

The outer-repo scan found 6,118 files / 624,560,663 bytes excluding Git and
AgentRead; only the 4,290 generated/cache candidates enter these totals.
No reparse points were traversed. The 6,732,988-byte
`ScanRobot.usd.back` asset is protected/out of scope, not a presumed temporary.
No external simulator/conda installation was inventoried or modified.

[Inventory and complete rankings](phase_b_local_artifact_cleanup_audit/inventory_summary.json),
[cache/legacy review](phase_b_local_artifact_cleanup_audit/cache_temp_review.json).

## Largest deletion groups

These are totals over disjoint exact members, NOT instructions to delete whole
mixed parent trees. Every retained receipt/report is excluded by using exact
file/subdirectory entries; no wildcard or generic all-JSON policy is an
execution authority.

| Group | Delete files | Delete bytes | Recommendation | Why safe |
|---|---:|---:|---|---|
| b2_t4_re6_r14_artifacts | 8,260 | 2,021,729,330 | DELETE exact members | Reports + compact verdicts retained; mixed parent NOT deleted |
| b2_t4_re5_artifacts | 8,039 | 2,000,864,897 | DELETE exact members | Reports + compact verdicts retained; mixed parent NOT deleted |
| b2_t4_re6_r12_artifacts | 8,155 | 1,954,665,921 | DELETE exact members | Reports + compact verdicts retained; mixed parent NOT deleted |
| b2_t4_re6_r9_artifacts | 8,091 | 1,950,928,815 | DELETE exact members | Reports + compact verdicts retained; mixed parent NOT deleted |
| b2_t4_re6_r3_artifacts | 8,075 | 1,938,939,909 | DELETE exact members | Reports + compact verdicts retained; mixed parent NOT deleted |
| b2_t4_re6_r1_artifacts | 7,323 | 1,938,595,898 | DELETE exact members | Reports + compact verdicts retained; mixed parent NOT deleted |
| b2_t4_re4_artifacts | 941 | 175,690,285 | DELETE exact members | Reports + compact verdicts retained; mixed parent NOT deleted |
| Project-local Python/pytest caches | 681 | 9,351,526 | DELETE_STRONG | Recreated from protected source; pytest README.md kept |
| Final closure tensors + process logs | 11 | 8,653,870 | DELETE_RECOMMENDED | Closed smoke fixture; compact equality/continuity/shutdown retained |
| Three Phase-B handoff ZIPs | 3 | 547,764 | DELETE_STRONG | 158/158 entries SHA256-identical to originals |

The dominant family is 39,360 repeated `critic_progress_*.json` files in
`pw_records`, totaling 10,520,485,004 bytes. Their reviewed conclusions are
retained; no paper baseline, ablation, scaling, disturbance or multi-seed
campaign requires those old mutation-by-mutation snapshots.

## Largest retained groups

| Group | Files / bytes | Why retained |
|---|---:|---|
| May-July legacy results/outputs/logs | 3,602 / 459,942,298 | UNKNOWN; historical models, videos, ZIPs and analyzer inputs outside established Phase-B disposal case |
| Protected docs/source/committed compact records in scope | 646 / 8,033,687 | Required, including all historical Markdown and archives |
| Canonical R14 ledgers | 7 / 3,343,441 | Concrete direct support for accepted normal-horizon/repeated-learning claims |
| Additional compact historical evidence | 211 / 1,281,434 | Outcome, STOP/root-cause, witnesses, config/source and quiescence |
| Final 23 compact JSON (subset of required) | 23 / 98,023 | Accepted final/G1-G10 and checkpoint metadata |
| CKPT1 compact JSON (subset of required) | 19 / 14,701 | Committed checkpoint qualification evidence |

Seven retained canonical R14 ledgers:
transaction, bridge, lifecycle_task_progress, nonterminal_bootstrap,
runtime_p2_immutability, terminal_reconciliation and zero_dvm_actor.
The lifecycle ledger is 2,860,731 bytes; retaining this bounded direct witness
allows independent inspection of claim step23, completion30, reopen31 and
normal-horizon terminal/post-reset evidence. W1-W7 and compact source/config
records are retained too. Eight byte-identical duplicate ledgers/witness
representations are DELETE_STRONG after hash comparison.

R14's 931-byte `final_result.json` and poisoned STOP provenance stay unchanged.
Its 82,663,470-byte prefixed raw aggregate `*_final_result.json` is not the
accepted final authority and is DELETE_RECOMMENDED. RE4's WinError5/tx130
failure and RE5's missing-W2 failure retain compact receipts; CKPT2 R1/R2
failure-only and R5/R6 final-stop adjudications are also retained.

## Final checkpoint fixture

Nine tensor payloads: **DELETE_RECOMMENDED / 8,601,860 bytes**.
These are a one-update-of-12 closure-smoke fixture, not a trained paper policy.
No active production, future-paper evaluation/training or unresolved defect
consumer was identified. No checkpoint was loaded.

Keep the four checkpoint metadata JSON, digests, all 23 final compact JSON,
equality, Adam/VN/progression/LR continuity, source/config authority, G1-G10 and
accepted report. All 11 manifest component/metadata hashes matched current
files in the package review.

If deletion is later approved, the exact archived checkpoint can no longer be
loaded/replayed: a retained manifest is evidence, not tensor state.
Source and compact acceptance evidence remain; any new recreation run would
require separate runtime authorization. No exact simulator/RNG replay,
convergence or trained-policy claim is made.

## ZIP files and logs

| Phase-B ZIP | Bytes | Recommendation |
|---|---:|---|
| 20260913/b2_t4_sr_artifacts.zip | 19,126 | DELETE_STRONG; 9 exact duplicate entries |
| 20260922/b2_t4_re6_r13_artifacts.zip | 492,460 | DELETE_STRONG; 143 exact duplicate entries |
| 20260925/phase_b_git_closeout_artifacts.zip | 36,178 | DELETE_STRONG; 6 exact duplicate entries |

No Phase-B ZIP contains the only surviving copy. This is not a recommendation
to remove unrelated ZIPs in old `results`: those remain UNKNOWN. Historical
raw copies may also be recommended for deletion, but their compact outcome
and retained report still preserve the accepted conclusion.

Final process A/B logs: **DELETE_RECOMMENDED / 52,010 bytes**. They contain
startup/configuration/reset diagnostics, not unique semantic gate evidence.
Shutdown/success/equality JSON remains. Legacy non-Phase-B logs remain UNKNOWN.
The RE4 incomplete atomic-write `.json.tmp` (556,512 bytes) is DELETE_STRONG,
with its compact failure/root-cause receipt retained.

[Per-file ZIP/tensor/log hashes and comparisons](phase_b_local_artifact_cleanup_audit/package_checkpoint_review.json).

## Current code, historical replay and paper value

Source/config reference inspection found **0 active dependencies affected**.
43 matching scripts comprise 42 historical harness/helpers and the already
closed final one-shot harness. They are HISTORICAL_ONLY, not active runtime
readers of these old data. Source remains protected. The final harness's
source-only authority collector does not enumerate historical trees.

Original raw forensic replay, old inventory-preservation gates and old
checkpoint loading will not all work after approved deletion. Those losses
are explicit; this audit does not alter historical freeze identities or
pretend to preserve bit-for-bit historical reruns. Compact accepted evidence,
source development, review and writing remain supported.
[Independent dependency review](phase_b_local_artifact_cleanup_audit/compact_dependency_review.json).

## Broken historical links if deletion is later approved

543 retained Markdown files and 1,054 inline Markdown link occurrences were
scanned. **294 currently resolving historical-detail link occurrences in
14 reports** would lose their targets. **109 documents** mention affected
artifact groups; that broader count includes plain/code paths and root links
that remain valid but lose raw children. It is not 109 broken documents.
Pre-existing missing links are recorded separately, not attributed to cleanup.

Manifest report-reference counts use distinct reports naming the artifact
group as a conservative per-member basis unless exact-file counting is
explicitly specified. No false claim of exhaustive arbitrary prose-path
resolution is made. Critical current final/readiness evidence is retained.
Historical reports are not rewritten to hide prospective missing links.
These are historical-detail or redundant claim-support links, not all mere
navigation. A second review found no additional critical-only evidence gap:
PW forensic facts remain in report sections D-Q and compact failure records;
R3's old PASS-looking final_result must be read with its retained superseding
STOP/poisoned failure_receipt and report; LAQ's retained final_result records
the wrong-filesystem-digest STOP. No current final/readiness report is in the
14-report broken-link set.

| Affected report | Newly unavailable inline link occurrences |
|---|---:|
| [PHASE_B2_T4_PW_WINDOWS_EVIDENCE_PERSISTENCE_ATOMIC_WRITE_ROBUSTNESS_QUALIFICATION_REPORT.md](../20260916/PHASE_B2_T4_PW_WINDOWS_EVIDENCE_PERSISTENCE_ATOMIC_WRITE_ROBUSTNESS_QUALIFICATION_REPORT.md) | 20 |
| [PHASE_B2_T4_RE4_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md](../20260916/PHASE_B2_T4_RE4_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) | 6 |
| [PHASE_B2_T4_RE5_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md](../20260916/PHASE_B2_T4_RE5_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) | 21 |
| [PHASE_B2_T4_PPQ_FORMAL_POSTPROCESS_SUCCESS_RECEIPT_PATH_QUALIFICATION_REPORT.md](../20260920/PHASE_B2_T4_PPQ_FORMAL_POSTPROCESS_SUCCESS_RECEIPT_PATH_QUALIFICATION_REPORT.md) | 21 |
| [PHASE_B2_T4_PPQ_V2_FRESH_RUN_SUCCESS_RECEIPT_CONTRACT_QUALIFICATION_REPORT.md](../20260920/PHASE_B2_T4_PPQ_V2_FRESH_RUN_SUCCESS_RECEIPT_CONTRACT_QUALIFICATION_REPORT.md) | 34 |
| [PHASE_B2_T4_RE6_R1_W2I_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md](../20260920/PHASE_B2_T4_RE6_R1_W2I_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) | 28 |
| [PHASE_B2_T4_RE6_R2_PPQ_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md](../20260920/PHASE_B2_T4_RE6_R2_PPQ_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) | 8 |
| [PHASE_B2_T4_RE6_R3_PPQ_V2_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md](../20260920/PHASE_B2_T4_RE6_R3_PPQ_V2_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) | 59 |
| [PHASE_B2_T4_RE6_W2E_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md](../20260920/PHASE_B2_T4_RE6_W2E_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) | 3 |
| [PHASE_B2_T4_W2E_CLAIM_MULTI_UPDATE_COMPLETION_EVIDENCE_CONTRACT_RECONCILIATION_REPORT.md](../20260920/PHASE_B2_T4_W2E_CLAIM_MULTI_UPDATE_COMPLETION_EVIDENCE_CONTRACT_RECONCILIATION_REPORT.md) | 13 |
| [PHASE_B2_T4_W2I_W2E_SELECTOR_SOURCE_IDENTITY_BINDING_REPORT.md](../20260920/PHASE_B2_T4_W2I_W2E_SELECTOR_SOURCE_IDENTITY_BINDING_REPORT.md) | 11 |
| [PHASE_B2_T4_LAQ_LAYER_A_WORKER_RECEIPT_SUPERVISOR_PREDICATE_QUALIFICATION_REPORT.md](../20260921/PHASE_B2_T4_LAQ_LAYER_A_WORKER_RECEIPT_SUPERVISOR_PREDICATE_QUALIFICATION_REPORT.md) | 29 |
| [PHASE_B2_T4_LAQ_R1_RAW_RECEIPT_AUTHORITY_BINDING_REQUALIFICATION_REPORT.md](../20260921/PHASE_B2_T4_LAQ_R1_RAW_RECEIPT_AUTHORITY_BINDING_REQUALIFICATION_REPORT.md) | 34 |
| [PHASE_B2_T4_RE6_R4_LAQ_R1_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md](../20260921/PHASE_B2_T4_RE6_R4_LAQ_R1_BOUND_NORMAL_HORIZON_LEARNED_TRAINING_INTEGRATION_QUALIFICATION_REPORT.md) | 7 |

[Exact source lines, targets and affected groups](phase_b_local_artifact_cleanup_audit/report_reference_audit.json).

## Size thresholds and top-50 rankings

Strict greater-than; decimal thresholds. These counts refer to individual files.

| Threshold bytes | Files | Combined bytes |
|---|---:|---:|
| > 100,000 | 34,209 | 12,148,992,933 |
| > 1,000,000 | 214 | 1,272,304,191 |
| > 10,000,000 | 15 | 763,770,104 |
| > 50,000,000 | 8 | 643,216,550 |
| > 100,000,000 | 0 | 0 |
| > 500,000,000 | 0 | 0 |
| > 1,000,000,000 | 0 | 0 |

Directory rankings are recursive and overlap: do not sum their rows.
MIXED means keep parent/retained files and use only exact allowlisted children.

### Top 50 individual files

| Rank | Repository-relative path (AR expanded above) | Bytes | Classification |
|---|---|---:|---|
| 1 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c/b2_t4_re6_r14_normal_horizon_20260922_formal01_final_result.json` | 82,663,470 | DELETE_RECOMMENDED |
| 2 | `AR/202609/20260922/b2_t4_re6_r12_artifacts/b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2/b2_t4_re6_r12_normal_horizon_20260922_formal01_final_result.json` | 82,375,124 | DELETE_RECOMMENDED |
| 3 | `AR/202609/20260922/b2_t4_re6_r9_artifacts/b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1/b2_t4_re6_r9_normal_horizon_20260922_formal01_final_result.json` | 82,090,666 | DELETE_RECOMMENDED |
| 4 | `AR/202609/20260920/b2_t4_re6_r1_artifacts/re6_r1_worker_raw_result.json` | 81,658,067 | DELETE_RECOMMENDED |
| 5 | `AR/202609/20260920/b2_t4_re6_r3_artifacts/b2_t4_re6_r3_normal_horizon_20260920_formal01_final_result.json` | 80,000,891 | DELETE_RECOMMENDED |
| 6 | `AR/202609/20260916/b2_t4_re5_artifacts/re5_worker_raw_result.json` | 79,776,217 | DELETE_RECOMMENDED |
| 7 | `AR/202609/20260920/b2_t4_re6_r1_artifacts/b2_t4_re6_r1_normal_horizon_20260920_formal01_final_result.json` | 78,259,063 | DELETE_RECOMMENDED |
| 8 | `AR/202609/20260916/b2_t4_re5_artifacts/b2_t4_re5_normal_horizon_20260916_formal01_final_result.json` | 76,393,052 | DELETE_RECOMMENDED |
| 9 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c/runtime_layer_a_raw_final.json` | 48,712,152 | DELETE_RECOMMENDED |
| 10 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis/seed-00001-2026-07-20-17-40-33/trainData.zip` | 14,807,839 | UNKNOWN_REVIEW_REQUIRED |
| 11 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100.zip` | 12,819,533 | UNKNOWN_REVIEW_REQUIRED |
| 12 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1_short_debug_train_10k/seed-00001-2026-06-29-23-22-22/06292322.zip` | 12,775,090 | UNKNOWN_REVIEW_REQUIRED |
| 13 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/preflight/b2-t4-re6-r14-preflight-ab3f96420b5948f3af1cc2f1c5f1e351/stage_a_artifacts/repository_authority.json` | 10,489,024 | DELETE_RECOMMENDED |
| 14 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/repository_authority.json` | 10,489,024 | DELETE_RECOMMENDED |
| 15 | `AR/202609/20260922/b2_t4_re6_r13_artifacts/repository_authority.json` | 10,460,892 | DELETE_RECOMMENDED |
| 16 | `results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics/budget_aware_segment_summary.csv` | 9,616,869 | UNKNOWN_REVIEW_REQUIRED |
| 17 | `results/assignment_diagnostics/phase9e3c_budget_aware_stuck_diagnostics_strict_budget/budget_aware_segment_summary.csv` | 9,553,879 | UNKNOWN_REVIEW_REQUIRED |
| 18 | `AR/202609/20260922/b2_t4_re6_r12_artifacts/repository_authority.json` | 8,079,600 | DELETE_RECOMMENDED |
| 19 | `AR/202609/20260922/b2_t4_re6_r11_artifacts/repository_authority.json` | 8,061,659 | DELETE_RECOMMENDED |
| 20 | `AR/202609/20260922/b2_t4_re6_r10_artifacts/repository_authority.json` | 8,045,145 | DELETE_RECOMMENDED |
| 21 | `results/assignment_evaluation/phase8_baseline_n50_e10_s300/diagnostics.json` | 6,807,773 | UNKNOWN_REVIEW_REQUIRED |
| 22 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c/re6_r14_static_authority.json` | 6,574,591 | DELETE_RECOMMENDED |
| 23 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c/b2_t4_re6_r14_normal_horizon_20260922_formal01_process_config_authority.json` | 6,570,023 | DELETE_RECOMMENDED |
| 24 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/preflight/b2-t4-re6-r14-preflight-ab3f96420b5948f3af1cc2f1c5f1e351/stage_a_artifacts/b2-t4-re6-r14-preflight-70bd7bc477b942878804cec2c345186b/re6_r14_static_authority.json` | 6,554,259 | DELETE_RECOMMENDED |
| 25 | `AR/202609/20260922/b2_t4_re6_r13_artifacts/b2-t4-re6-r13-20260922-formal01-339ec669e33b4f40be9dfea9347a0ed7/re6_r13_static_authority.json` | 6,524,768 | DELETE_RECOMMENDED |
| 26 | `AR/202609/20260922/b2_t4_re6_r12_artifacts/b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2/b2_t4_re6_r12_normal_horizon_20260922_formal01_process_config_authority.json` | 6,275,429 | DELETE_RECOMMENDED |
| 27 | `AR/202609/20260922/b2_t4_re6_r12_artifacts/b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2/re6_r12_static_authority.json` | 6,272,513 | DELETE_RECOMMENDED |
| 28 | `AR/202609/20260922/b2_t4_re6_r11_artifacts/b2-t4-re6-r11-20260922-formal01-c266e95ab2b34167ba37505dcc6908d1/re6_r11_static_authority.json` | 6,253,722 | DELETE_RECOMMENDED |
| 29 | `AR/202609/20260922/b2_t4_re6_r10_artifacts/b2-t4-re6-r10-20260922-formal01-11b4e53a29764470b1831a360468fd8e/re6_r10_static_authority.json` | 6,244,560 | DELETE_RECOMMENDED |
| 30 | `AR/202609/20260922/b2_t4_re6_r9_artifacts/b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1/re6_r9_static_authority.json` | 6,003,458 | DELETE_RECOMMENDED |
| 31 | `AR/202609/20260922/b2_t4_re6_r9_artifacts/b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1/b2_t4_re6_r9_normal_horizon_20260922_formal01_process_config_authority.json` | 5,996,725 | DELETE_RECOMMENDED |
| 32 | `AR/202609/20260922/b2_t4_re6_r8_artifacts/b2-t4-re6-r8-20260922-formal01-f5c47b1ad2ba42a1baaa552f64d3a675/re6_r8_static_authority.json` | 5,989,206 | DELETE_RECOMMENDED |
| 33 | `AR/202609/20260922/b2_t4_norm_r1_artifacts/repository_authority.json` | 5,811,253 | DELETE_RECOMMENDED |
| 34 | `AR/202609/20260922/b2_t4_re6_r9_artifacts/repository_authority.json` | 5,700,911 | DELETE_RECOMMENDED |
| 35 | `AR/202609/20260922/b2_t4_re6_r8_artifacts/repository_authority.json` | 5,689,086 | DELETE_RECOMMENDED |
| 36 | `AR/202609/20260921/b2_t4_racq_r1_artifacts/repository_authority.json` | 5,648,770 | DELETE_RECOMMENDED |
| 37 | `AR/202609/20260921/b2_t4_re6_r6_artifacts/repository_authority.json` | 5,645,987 | DELETE_RECOMMENDED |
| 38 | `AR/202609/20260921/b2_t4_racq_artifacts/repository_authority.json` | 5,635,830 | DELETE_RECOMMENDED |
| 39 | `AR/202609/20260921/b2_t4_re6_r5_artifacts/repository_authority.json` | 5,633,377 | DELETE_RECOMMENDED |
| 40 | `AR/202609/20260921/b2_t4_re6_r4_artifacts/repository_authority.json` | 5,622,563 | DELETE_RECOMMENDED |
| 41 | `AR/202609/20260921/b2_t4_laq_r1_artifacts/repository_authority.json` | 5,616,620 | DELETE_RECOMMENDED |
| 42 | `AR/202609/20260921/b2_t4_laq_artifacts/repository_authority.json` | 5,610,900 | DELETE_RECOMMENDED |
| 43 | `results/assignment_evaluation/phase9b1a_plateau_diagnostic_n50_e2_s300/diagnostics.json` | 5,347,375 | UNKNOWN_REVIEW_REQUIRED |
| 44 | `results/assignment_evaluation/phase7e_actual_base_motion_crossing_e1_s300/diagnostics.json` | 5,297,549 | UNKNOWN_REVIEW_REQUIRED |
| 45 | `results/assignment_diagnostics/phase9g4b_failed_pair_memory_d6_validation/lifecycle_all/phase9g1_lifecycle_reconstructed_rows.csv` | 5,059,924 | UNKNOWN_REVIEW_REQUIRED |
| 46 | `results/assignment_evaluation/phase8_baseline_n50_e10_s300/assignment_history.csv` | 4,516,576 | UNKNOWN_REVIEW_REQUIRED |
| 47 | `results/assignment_diagnostics/real_component_n24_uncovered_level2_diagnostics.json` | 4,333,169 | UNKNOWN_REVIEW_REQUIRED |
| 48 | `results/assignment_evaluation/phase7d2_conflict_aware_baseline_e1_s300/diagnostics.json` | 4,122,902 | UNKNOWN_REVIEW_REQUIRED |
| 49 | `AR/202609/20260920/b2_t4_re6_r3_artifacts/re6_r3_static_authority.json` | 4,034,268 | DELETE_RECOMMENDED |
| 50 | `AR/202609/20260920/b2_t4_re6_r3_artifacts/b2_t4_re6_r3_normal_horizon_20260920_formal01_process_config_authority.json` | 4,031,620 | DELETE_RECOMMENDED |

### Top 50 directories

| Rank | Repository-relative directory | Files | Bytes | Recommendation |
|---|---|---:|---:|---|
| 1 | `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead` | 50,812 | 12,126,229,635 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 2 | `AR/202609` | 50,451 | 12,120,697,958 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 3 | `AR/202609/20260922` | 16,681 | 3,973,646,063 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 4 | `AR/202609/20260920` | 15,548 | 3,883,530,814 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 5 | `AR/202609/20260916` | 9,052 | 2,177,163,192 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 6 | `AR/202609/20260923` | 8,545 | 2,029,652,260 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 7 | `AR/202609/20260923/b2_t4_re6_r14_artifacts` | 8,290 | 2,025,218,270 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 8 | `AR/202609/20260916/b2_t4_re5_artifacts` | 8,046 | 2,000,995,537 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 9 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c` | 8,103 | 1,995,448,228 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 10 | `AR/202609/20260922/b2_t4_re6_r12_artifacts` | 8,165 | 1,954,738,243 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 11 | `AR/202609/20260922/b2_t4_re6_r9_artifacts` | 8,099 | 1,951,027,075 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 12 | `AR/202609/20260922/b2_t4_re6_r12_artifacts/b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2` | 8,086 | 1,946,023,253 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 13 | `AR/202609/20260922/b2_t4_re6_r9_artifacts/b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1` | 8,065 | 1,945,151,082 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 14 | `AR/202609/20260920/b2_t4_re6_r3_artifacts` | 8,082 | 1,939,038,062 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 15 | `AR/202609/20260920/b2_t4_re6_r1_artifacts` | 7,331 | 1,938,776,606 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 16 | `AR/202609/20260922/b2_t4_re6_r12_artifacts/b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2/pw_records` | 7,200 | 1,756,233,844 | DELETE_EXACT_ALLOWLIST |
| 17 | `AR/202609/20260922/b2_t4_re6_r12_artifacts/b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2/pw_records/b2-t4-re6-r12-20260922-formal01-d032823b6e9747b9a41ca1808cbe35f2` | 7,200 | 1,756,233,844 | DELETE_EXACT_ALLOWLIST |
| 18 | `AR/202609/20260922/b2_t4_re6_r9_artifacts/b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1/pw_records` | 7,200 | 1,756,219,444 | DELETE_EXACT_ALLOWLIST |
| 19 | `AR/202609/20260922/b2_t4_re6_r9_artifacts/b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1/pw_records/b2-t4-re6-r9-20260922-formal01-7ffc30b1ebf54620b17590f9afb39de1` | 7,200 | 1,756,219,444 | DELETE_EXACT_ALLOWLIST |
| 20 | `AR/202609/20260920/b2_t4_re6_r3_artifacts/pw_records/b2-t4-re6-r3-20260920-formal01-b4718cb4f54b4f589a418dad7f4c4411` | 7,200 | 1,756,219,444 | DELETE_EXACT_ALLOWLIST |
| 21 | `AR/202609/20260920/b2_t4_re6_r3_artifacts/pw_records` | 7,200 | 1,756,219,444 | DELETE_EXACT_ALLOWLIST |
| 22 | `AR/202609/20260916/b2_t4_re5_artifacts/pw_records/b2-t4-re5-20260916-formal01-ab67c2b8ba0c40b8bcdef425687fb20a` | 7,200 | 1,756,176,244 | DELETE_EXACT_ALLOWLIST |
| 23 | `AR/202609/20260916/b2_t4_re5_artifacts/pw_records` | 7,200 | 1,756,176,244 | DELETE_EXACT_ALLOWLIST |
| 24 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c/pw_records` | 7,200 | 1,755,602,164 | DELETE_EXACT_ALLOWLIST |
| 25 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c/pw_records/b2-t4-re6-r14-20260923-formal01-d21c8c835a4944af8395b7a03dee5b6c` | 7,200 | 1,755,602,164 | DELETE_EXACT_ALLOWLIST |
| 26 | `AR/202609/20260920/b2_t4_re6_r1_artifacts/pw_records` | 7,200 | 1,755,587,764 | DELETE_EXACT_ALLOWLIST |
| 27 | `AR/202609/20260920/b2_t4_re6_r1_artifacts/pw_records/b2-t4-re6-r1-20260916-formal01-81f98308e90d47208e4805993323d54f` | 7,200 | 1,755,587,764 | DELETE_EXACT_ALLOWLIST |
| 28 | `results` | 2,336 | 451,613,912 | REVIEW_KEEP_FOR_NOW |
| 29 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo` | 1,621 | 298,433,899 | KEEP |
| 30 | `results/isaaclab` | 1,621 | 298,433,899 | REVIEW_KEEP_FOR_NOW |
| 31 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0` | 1,621 | 298,433,899 | KEEP |
| 32 | `AR/202609/20260916/b2_t4_re4_artifacts` | 949 | 175,805,855 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 33 | `results/assignment_diagnostics` | 459 | 110,829,012 | REVIEW_KEEP_FOR_NOW |
| 34 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/scan_happo` | 1,326 | 49,872,744 | KEEP |
| 35 | `results/assignment_evaluation` | 245 | 42,243,554 | REVIEW_KEEP_FOR_NOW |
| 36 | `AR/202609/20260921` | 292 | 40,997,625 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 37 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1_short_debug_train_10k` | 29 | 40,529,422 | KEEP |
| 38 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/scan_happo/seed-00001-2026-06-01-12-13-22` | 1,263 | 40,077,901 | KEEP |
| 39 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/scan_happo/seed-00001-2026-06-01-12-13-22/videos/train` | 1,249 | 36,335,379 | KEEP |
| 40 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/scan_happo/seed-00001-2026-06-01-12-13-22/videos` | 1,249 | 36,335,379 | KEEP |
| 41 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis` | 23 | 32,067,019 | KEEP |
| 42 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8i1_fresh_100k_policy_noop_load_diagnosis/seed-00001-2026-07-20-17-40-33` | 23 | 32,067,019 | KEEP |
| 43 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k` | 15 | 26,933,955 | KEEP |
| 44 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9e4a_budget_m15_slack5_d5_train_100k/seed-00001-2026-07-01-14-40-47` | 15 | 26,933,955 | KEEP |
| 45 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9d1_short_debug_train_10k/seed-00001-2026-06-29-23-22-22` | 15 | 26,652,256 | KEEP |
| 46 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/preflight` | 135 | 18,954,877 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 47 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/preflight/b2-t4-re6-r14-preflight-ab3f96420b5948f3af1cc2f1c5f1e351` | 134 | 18,954,361 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 48 | `AR/202609/20260923/b2_t4_re6_r14_artifacts/preflight/b2-t4-re6-r14-preflight-ab3f96420b5948f3af1cc2f1c5f1e351/stage_a_artifacts` | 128 | 18,950,823 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 49 | `AR/202609/20260922/b2_t4_re6_r13_artifacts` | 143 | 18,905,431 | MIXED_KEEP_EXCEPT_EXACT_DELETE_ALLOWLIST |
| 50 | `results/isaaclab/Isaac-Scan-Mobile-Manipulator-Direct-v0/happo/assignment_happo_n50_phase9g8g1r2_valuenorm_v2_controlled_smoke_fresh/seed-00001-2026-07-10-15-59-12` | 22 | 15,720,694 | KEEP |

## Allowlists, validation and approval boundary

Seven mutually exclusive manifests:
[strong delete](phase_b_local_artifact_cleanup_audit/delete_strong_allowlist.json),
[recommended delete](phase_b_local_artifact_cleanup_audit/delete_recommended_allowlist.json),
[optional archive](phase_b_local_artifact_cleanup_audit/archive_optional_allowlist.json),
[local useful](phase_b_local_artifact_cleanup_audit/keep_local_useful.json),
[required](phase_b_local_artifact_cleanup_audit/keep_required.json),
[compact evidence](phase_b_local_artifact_cleanup_audit/keep_compact_evidence.json),
[unknown/manual review](phase_b_local_artifact_cleanup_audit/unknown_review_required.json).

Entries use exact repository-relative file paths or wholly homogeneous
directory prefixes. Each records count, bytes, phase, reason, references,
dependency, replacement evidence and a metadata-membership SHA256. Future
new files, changed size/time, tracked status, overlap or reparse paths must
stop execution. Generic rules in the read-only inventory helper classify this
snapshot only; they cannot extend a future deletion authorization.

[Dry-run validation](phase_b_local_artifact_cleanup_audit/dry_run_verification.json)
and [future execution plan](PHASE_B_LOCAL_ARTIFACT_DELETE_EXECUTION_PLAN.md)
govern the next step. The plan contains a labeled, non-executed deletion block.
Neither a passing dry run nor this report grants deletion permission.

[Final integrity verification](phase_b_local_artifact_cleanup_audit/audit_integrity_verification.json):
all 50,815 pre-existing AgentRead paths/sizes/mtimes matched before the targeted
handoff update; all seven manifest partitions are disjoint; source/index/HEAD
and local excludes remain unchanged. Both read-only helpers and the future
plan code fences pass PowerShell syntax parsing without executing deletion.
New report links resolve. Audit JSON/helpers add approximately 10.56 MB of
retained review material outside the original scope denominator.

Before the handoff-only update, the full TASK_PROGRESS was archived byte-exactly:
[TASK_PROGRESS archive](TASK_PROGRESS_ARCHIVE_BEFORE_LOCAL_CLEANUP_AUDIT_20260925.md),
SHA256 `8dc28b7dca33bd1e24805c5583188493d8c47981069a16dcbb2aac5287809008`.

Files deleted/moved/compressed: **0/0/0**.
Isaac/CUDA/training/evaluation/checkpoint load/save: **0**.
Git mutations: **0**. No production, test, historical report or installed HARL
file changed; only new audit material and the current handoff are permitted.
Local ignore rules are unchanged. Cleanup itself remains NOT EXECUTED.

Next: user/GPT review of the exact manifests. Separately approve or reject the
Phase-B deletion subset; review legacy UNKNOWN files independently.
**DO NOT DELETE ANYTHING YET.**
