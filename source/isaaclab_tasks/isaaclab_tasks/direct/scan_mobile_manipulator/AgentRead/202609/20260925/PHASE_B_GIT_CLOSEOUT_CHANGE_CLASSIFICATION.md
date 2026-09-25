# Phase-B Git Closeout Change Classification

Date: 2026-09-25 (Asia/Shanghai)
Classification: PHASE-B-ENGINEERING-GIT-CLOSEOUT-READY-FOR-MANUAL-COMMIT

## Scope and counting

Phase B is COMPLETE / GPT REVIEW PASS / CLOSED by the user's accepted review.
This is a repository-closeout audit, not a new runtime qualification.
All counts are logical porcelain entries: one rename pair counts once at its
current path. Categories describe the actual pending change, not the age or
subject of a document. A file has exactly one primary category.

Before this closeout: 50,906 entries (50,542 untracked, 359 staged renames,
271 unstaged paths overlapping 266 renames). Resumption after the byte-exact
handoff archive: 50,907. Final: 50,909, including ten new closeout documents/JSON
and the root ignore edit; nine initial tensor entries are now ignored, not deleted.

| Category | Final visible paths | Meaning |
|---|---:|---|
| A PHASE_B_PRODUCTION | 11 | 2 modified and 9 new runtime modules |
| B PHASE_B_TEST_AND_CLOSURE | 96 | 89 environment scripts, 6 static guard modules, 1 offline audit helper |
| C PHASE_B_DOCUMENTATION | 234 | Reports/archives, current handoff, compact offline audits and administrative closeout policy |
| D MONTHLY_ARCHIVE_MIGRATION | 361 | 359 staged Markdown moves, AGENTS, migration report |
| E PAPER_EXPERIMENT_WORK | 0 | No experiment implementation/execution started |
| F GENERATED_RUNTIME_ARTIFACT | 50,206 | Ordinary status after ignoring the nine final fixture tensors |
| G UNRELATED_EXISTING_WORK | 1 | Existing .vscode/.gitignore modification |
| H DISPOSABLE / TEMPORARY | 0 | No files proven to lack remaining evidence/debugging value |

C includes the root .gitignore edit as administrative retention policy, although
it is scheduled with commit C (tests). CSR1's paper-readiness contract describes
future, unexecuted work: documentation C, not experiment work E.

## Commit and retention matrix

Paths below are relative to the repository; AR denotes
`source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead`. Exact source/doc paths and generated prefix partitions are in
[the classification JSON](phase_b_git_closeout_artifacts/phase_b_change_classification.json).
[The manual allowlist](phase_b_git_closeout_artifacts/phase_b_manual_commit_paths.json)
contains every proposed committed file, without directory-wide staging.

| Path/group | Git state | Category | Keep in repo? | Proposed commit |
|---|---|---|---:|---|
| AR/202606, 202607, 202608: 359 migrated Markdown targets | 93 R; 266 RM | D | Yes | A |
| AR/AGENTS.md; 20260901 migration report | Modified; untracked | D | Yes | A |
| assignment_harl_training.py; assignment_value_normalizer_checkpoint.py | Modified | A | Yes | B |
| Nine event-training / optimization runtime modules | Untracked | A | Yes | B |
| scripts/environments: 89 qualification/helper scripts | Untracked | B | Yes | C |
| Six assignment_event_training_*_guards.py modules | Untracked | B | Yes | C |
| 20260924/b2_t4_ckpt2_r6_hr1_artifacts/hr1_offline_reconciliation.py | Untracked | B | Yes, historical helper | C |
| Current handoff, dated reports/archives, 8 readiness + 22 CSR1 + 18 HR1 offline artifacts, closeout files | Modified/untracked | C | Yes | D |
| Root .gitignore: one exact-fixture tensor rule | Modified | C | Yes | C |
| Final closure artifacts: 23 JSON; CKPT1: 19 compact JSON | Untracked | F | Yes | C |
| Final checkpoint: 9 .pt files; final 2 logs | Ignored (tensors initially untracked) | F | Local only | None |
| All other historical runtime JSON/JSONL, generated transaction table, two ZIPs | Untracked | F | Local only | None |
| Three R8 STOP receipts under source/isaac_tasks/.../AgentRead | Untracked | F | Local only; preserve anomalous historical location | None |
| .vscode/.gitignore | Modified | G | Preserve existing local change; exclude this task | None |

The gradient_probe module is A because live actor/critic mutation and transaction
code import its execution/gradient helpers. Its name does not make it test-only.
The six *_guards modules are B: static source/public-route isolation checks.
Historical qualification scripts remain historical; retaining them does not
authorize retrying them. No existing source or history was rewritten.

## Existing staged group

All 359 entries are genuine exact monthly moves: 359 identical old/new blob IDs,
359 equal modes, 359 .md files and correct month/date mapping. June95, July172,
August92. Production/test/generated/unrelated staged entries: 0 each.
Git already detects 359 R100 renames; disabling rename detection exposes
359 deletions + 359 additions, not an additional set of changes.

The 266 unstaged migrated documents contain only path-reference adjustments;
stage those corrected destinations together with the already-staged moves.
No unstaging is needed for the inspected index. AGENTS' change is the permanent
monthly layout rule. Historical document subjects do not change this D classification.
[Staged audit](phase_b_git_closeout_artifacts/staged_359_path_audit.json).

## Generated artifacts and large-file boundary

Initial changed/untracked F: 50,215 files, 12,117,709,453 bytes. This includes the
nine tensors subsequently ignored. The two already-ignored final logs add
52,010 bytes; unrelated ignored caches/logs elsewhere were not inventoried.

Recommend Git: 42 compact generated JSON, 112,724 bytes.
Local-only within this audited scope: 50,175 files, 12,117,648,739 bytes,
including the two final logs. Safe-to-delete/deleted: 0/0. The two ZIP archives
were not proven byte-redundant; preservation is intentional.

Thresholds use decimal MB and strict greater-than: >1 MB 63; >10 MB 12;
>50 MB 8; >100 MB 0. All 63 are F, excluded from recommended commits.
Four of the >1 MB files are now-ignored final Adam payloads; the original
audit is retained rather than silently shrinking it to 59 visible files.
[All 63 paths](phase_b_git_closeout_artifacts/phase_b_large_file_audit.json).

Final artifacts: 34 files / 8,751,893 bytes; 23 JSON / 98,023 bytes in Git,
9 tensors / 8,601,860 bytes and 2 logs / 52,010 bytes local-only.
Checkpoint subtree: 13 files / 8,607,629 bytes. This is an A-update1-of12
closure-smoke fixture, not a trained paper policy. A Git-only checkout keeps
evidence-only manifests; it does NOT contain a loadable checkpoint.
[Per-file roles, sizes, hashes and decisions](phase_b_git_closeout_artifacts/phase_b_artifact_retention.json).

## Ignore policy and portability

Existing root rules already ignore logs, Python caches, common output/results
directories and temporary files. Add only this anchored rule:

```gitignore
/source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/202609/20260924/phase_b_final_closure_artifacts/checkpoint/generation_*/*/*.pt
```

It matches only tensor payloads under this final fixture, not arbitrary paper
models, JSON, reports, sources or harnesses. No tracked files match it.
The pre-existing .vscode/.gitignore is unrelated and not an effective substitute
for the root artifact rule; leave it untouched.

Bulk historical data stays on disk and remains outside the commit allowlist.
Some old report links, forensic scripts and frozen inventories require that
local data or old workspace/session paths. A Git-only checkout preserves code,
reports and selected compact evidence, not every raw historical forensic
reconstruction. Do not rewrite history or frozen source/HEAD identities after
the user commits. Future paper artifact policy belongs to the next phase.

See [manual commit plan](PHASE_B_MANUAL_COMMIT_PLAN.md) and
[engineering report](PHASE_B_ENGINEERING_GIT_CLOSEOUT_REPORT.md).
