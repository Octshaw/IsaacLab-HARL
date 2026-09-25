# Phase-B Implementation Change Summary

Date: 2026-09-25 (Asia/Shanghai)
Status: COMPLETE / GPT REVIEW PASS / CLOSED (accepted user review)

## Scope

This describes the completed lifecycle-aware, fixed-scale MRTA training/runtime
backbone. It separates previously committed foundations from the current
uncommitted source delta. No production code was changed in engineering closeout.

Current HEAD is b71d85a32f51be6ada324f870813a56bb45dd396. Earlier commits
14993dee and b71d85a3 already contain lifecycle/runtime and event-policy/learner
interface foundations. The pending production commit is **11 files: 2 modified,
9 new**; it is not the entire historical Phase-B implementation.

## Capability map

| Capability | Implementation / responsibility | Pending production delta? |
|---|---|---|
| Lifecycle authority | Environment-owned claim/continue/complete/release handling, ownership validation, failed-pair exclusion; history captured before autoreset | Foundations already in HEAD |
| Event-gated policy | NEEDS_ASSIGNMENT plus legal-target admission; actor proposals distinct from effective controller assignment | Foundations already in HEAD |
| Lifecycle actions / DVM | EXECUTING continues with singleton owned-task action; no-event/no-legal-target rows forced; availability, active mask and DVM are distinct | Foundations already in HEAD |
| Event returns | Timeout bootstrap differs from true terminal; trace boundaries and historical terminal ledger; one event-return computation per rollout | Foundations already in HEAD; consumed by pending transaction |
| Actor training | Active AND DVM rows, behavior logprob PPO ratio, clipped surrogate/entropy, sequential HAPPO factors; plan-zero actors skip mutation | actor_mutation, plans, gradient_probe, control, evidence |
| Critic / ValueNorm | Raw event-return target, live same-target normalization, source-faithful critic loss, finite gradients and Adam updates | critic_mutation plus canonical ValueNorm runtime extraction |
| S0-S10 coordination | Frozen plans and permits, actor then critic mutation, count/state audit, rollout mode and ordered buffer rollover, clean quiescence/poison boundary | full_transaction, control/evidence/plans |
| Real Isaac integration | Real environment/actors/critic/ValueNorm bound to the reviewed event transaction; existing learners retained across updates | real_isaac_adapter |
| Optimization checkpoint | All model/Adam/VN state, semantic config and completed/next/total/LR position; atomic generation, strict validation/load, rollback/poison safeguards | optimization_checkpoint and runner API integration |
| Qualification / final closure | Source guards, bounded real/repeated/horizon tests, CKPT1, final A-save/fresh-B-load/B-update harness and compact evidence | 96 test/helper files; 42 compact generated JSON |

Module stems in the table resolve under the scan_mobile_manipulator source
directory with the assignment_event_training_ prefix. The precise 11-file
allowlist is commit B in [the manifest](phase_b_git_closeout_artifacts/phase_b_manual_commit_paths.json).

## Current modified integration files

- assignment_harl_training.py adds the optimization runtime guard/progression
  tracker; tracks inherited HA update completion; exposes full save/validate/
  restore APIs and an explicit next-update LR application helper.
- assignment_value_normalizer_checkpoint.py extracts cloned canonical live
  mutable fields without changing device/dtype; CPU checkpoint export delegates
  to that extraction. It does not assume generic Module state APIs cover ValueNorm.

The live gradient_probe helpers are production dependencies of actor/critic
mutation and transaction cleanup. Six separate *_guards modules are static
qualification helpers, not part of the production commit.

## Reviewed event route and important non-equivalence

The event learner is:
execute_real_isaac_single_transaction_v1 ->
execute_full_learner_transaction_v1 (S0-S10).

The assignment runner's train() still delegates to the inherited HA path.
Generic runner.run/train/restore must not be described as automatically enabling
the reviewed event learner or resuming its loop index/LR. A future paper entry
must explicitly wire the reviewed coordinator and consume saved progression.
Engineering closeout does not activate the public route.

## Accepted evidence

The [readiness audit](../20260924/PHASE_B_FINAL_CLOSURE_READINESS_AUDIT.md)
reconciled the existing lifecycle, normal-horizon and repeated-learning evidence.
The [final runtime report](../20260924/PHASE_B_FINAL_CLOSURE_REPORT.md) established
the remaining real optimization continuation. Its old AWAITING-GPT-REVIEW label
is historical; the accepted closure is recorded in the
[current handoff](../../TASK_PROGRESS.md).

G1-G10: 10/10 PASS. A: one real update, actor steps (5,5,5), critic10, VN10,
then one checkpoint save. Fresh B: exact full optimization-state equality before
collection, then its own frozen plan (5,5,10), critic10, VN10.
Actor Adam (5,5,5) -> (10,10,15), critic10 -> 20; ten exact B ValueNorm
recurrences; completed1/next2 -> completed2/next3 with the saved LR schedule.
Both processes exited cleanly. These are accepted historical results, not runs
performed in closeout.

## Boundaries for paper implementation

Phase-B runtime blockers: NONE. R6 is HISTORICAL / NO RETRY; R7 NOT USED;
R15 NOT AUTHORIZED / NOT NEEDED FOR PHASE-B CLOSURE.
No convergence, policy quality, simulator/RNG trajectory resume, arbitrary
configuration migration, variable-cardinality policy, or completed paper
experiment campaign is claimed. Baselines, ablations, disturbances, scale,
multi-seed training/evaluation and campaign packaging are the next project phase.

Final smoke tensors remain local-only; manifests/hashes and compact results are
retained in Git. Historical scripts are preserved for review/provenance, not
newly requalified for a clean checkout without their local raw artifacts.
No installed HARL or environment configuration changes were made in closeout.
