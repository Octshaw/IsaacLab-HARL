# TASK_PROGRESS

## Current status

```text
Lifecycle Runtime Backbone:
  COMMITTED / CLOSED

B2-D:
  REVIEW PASS / FROZEN

B2-I0 through B2-I6:
  REVIEW PASS / CLOSED

B2-V1:
  GPT REVIEW PASS / CLOSED

B2-V2-PD2-R5-K:
  GPT FORMAL REVIEW PASS / CLOSED

B2-V2:
  GPT REVIEW PASS / CLOSED

B2-R0:
  SOURCE AUDIT COMPLETE
  ARCHITECTURE DESIGN COMPLETE
  PRIOR GPT REVIEW: CONDITIONAL PASS
  TARGETED REVISION COMPLETE
  AWAITING GPT RE-REVIEW

classification:
  PHASE-B2-R0-TRAINING-UPDATE-READINESS-TARGETED-REVISION-COMPLETE-AWAITING-GPT-REVIEW

implementation:
  NOT AUTHORIZED

current-production runtime-interface readiness:
  REVIEW PASS

policy-interface readiness:
  REVIEW PASS

terminal learner-transport readiness:
  REVIEW PASS

training-update readiness:
  NOT YET ESTABLISHED

training convergence / policy quality:
  NOT ESTABLISHED

public learned-policy route:
  DORMANT / BLOCKED

training:
  NOT AUTHORIZED

long training:
  NOT AUTHORIZED

B2-R1:
  NOT STARTED
  REQUIRES EXPLICIT USER AUTHORIZATION AFTER GPT RE-REVIEW

documentation commit:
  NONE / NOT AUTHORIZED
```

## Latest completed phase

The GPT-requested B2-R0 targeted documentation revision is complete. The
existing authoritative architecture was not restarted or redesigned. The three
conditional-pass issues were hardened in place, and a concise targeted revision
summary was created.

This handoff does not self-classify B2-R0 as GPT REVIEW PASS. It awaits
independent GPT re-review and makes no new runtime or training claim.

## Starting committed authority

```text
branch:
  main

upstream:
  origin/main

HEAD:
  b71d85a32f51be6ada324f870813a56bb45dd396

HEAD parent:
  14993dee344bade0230d2eb97b5f22171331f44a

HEAD subject:
  feat(mrta): close B2 event policy and learner interface verification
```

`14993dee...` is historical parent authority, not current HEAD. The targeted
revision did not repeat or broaden the prior source audit.

## Targeted revision 1: configuration-relative counts

All dimensions and update counts are configuration-relative and must be resolved
and frozen for each authorized update:

```text
resolved_T = rollout length
resolved_E = rollout-environment count
resolved_M = actor count
resolved_N = resolved task/action cardinality
B = resolved_T * resolved_E
```

Symbolic shapes such as `[T,E,1]` use these resolved values and are not fixed
sizes. The exact config digest and update plan bind resolved `T/E/M/N`, critic
epochs/partitions, actor epochs/partitions, ValueNorm enablement, and exact
expected backward, optimizer-step, and ValueNorm call counts.

For every critic epoch, every canonical `k` in `[0,B)` appears exactly once
across approved critic minibatches. Omitted or duplicated rows fail closed.
Exact divisibility is required unless an explicitly reviewed exact-coverage
partitioner is used.

The R0-audited resolved snapshot (`T=1000`, `E=20`, `M=3`, five critic epochs,
two approved critic minibatches per epoch, ValueNorm enabled) yields 20,000 rows,
10 critic steps, and 10 ValueNorm calls for one successful update. These are
resolved snapshot results, not universal architecture constants.

## Targeted revision 2: learner termination semantics

```text
selected reason              bootstrap                                      trace
NONE                         normal current next value, gated by liveness   normal liveness
ALL_TASKS_COMPLETED          zero                                           stop
NO_FEASIBLE_TASKS_REMAIN     zero                                           stop
TIME_LIMIT                   correlated historical pre-reset timeout value  stop
```

If raw conditions overlap, the frozen environment-owned precedence is:

```text
ALL_TASKS_COMPLETED
  > NO_FEASIBLE_TASKS_REMAIN
  > TIME_LIMIT
  > NONE
```

A higher-priority zero-bootstrap terminal can never receive TIME_LIMIT
bootstrap. Pre-reset historical evidence, timeout critic correlation,
compute-once event returns, exact `returns[:-1]`, and the stock
`compute_returns()` prohibition remain unchanged.

## Targeted revision 3: checkpoint dependency branch

```text
main training-update readiness path:
  B2-R1 -> B2-R2 -> B2-R3 -> B2-R4 -> B2-R5 -> B2-R7

orthogonal checkpoint-readiness branch:
  B2-R6a  quiescent weight continuation, separately authorized
  B2-R6b  optional exact resume, separately authorized and a separate claim
```

B2-R7 depends on accepted R1-R5 evidence. R6a is not a prerequisite for one
bounded semantically correct update or B2-R7 unless a future explicit user
authorization changes scope; it may later gate long-duration or restart
workflows. R6b remains optional and is not a first-paper requirement.

## Protected architecture retained

- P2 remains sole ownership truth; proposal remains distinct from effective
  assignment.
- Actor behavior evidence remains the original proposal action plus original
  rollout behavior logprob.
- EXECUTING continuation neither resamples the actor nor creates a repeated
  claim.
- DVM remains independent of active masks and available actions. Actor
  evaluation uses DVM rows; actor loss/entropy/surrogate/gradient uses
  active-and-DVM rows.
- Forced/no-policy rows never become training rows, and their logprob sentinel
  is not PPO behavior evidence.
- Full-index factor shape remains symbolic `[T,E,1]`; off-current-actor-DVM
  ratio is exact one, and prior-actor accumulation is not reset.
- Critic training uses every physical transition row and exactly
  `critic_buffer.returns[:-1]`; the final returns slot is structural only.
- Return construction remains ValueNorm inference-only/no-mutation. Future
  critic training remains source-faithful per processed approved raw-return
  minibatch.
- Failed/partial updates poison the route and cannot roll over, checkpoint,
  begin a new rollout, or enter a public path.
- Stock full-row actor training and stock event-incompatible return computation
  remain forbidden. Installed HARL remains unmodified.
- Public learned-policy execution remains dormant and default-off.

## Documentation actions and archive

- revised the existing authoritative B2-R0 report in place;
- created `AgentRead/202609/20260901/PHASE_B2_R0_GPT_TARGETED_REVISION_SUMMARY.md`;
- created the byte-preserving pre-rewrite archive at
  `AgentRead/202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R0_GPT_TARGETED_REVISION_HANDOFF_20260901.md`;
- targeted-revision archive/source bytes: `7594 / 7594`;
- targeted-revision archive/source SHA-256:
  `18d46062fd004732392240db3a7bd947b6d6e18d7586eafd9d375a8c40c9315f`;
- targeted-revision archive/source Git blob:
  `541d187e31d49d0a397e71262d25c6f5f44031e8`;
- retained the earlier byte-exact pre-B2-R0 handoff archive unchanged;
- production/HARL/harness/checkpoint artifact changes: NONE;
- source audit restart or expansion: NONE;
- Python/tests/backward/optimizer/trainer/Isaac/training/playback/evaluation/
  checkpoint weight I/O: NONE;
- git add/commit/push: NONE.

## Retained boundaries

- B2-V2 remains closed and was not regenerated or broadened.
- Real backward, optimizer, actor/critic parameter mutation, and ValueNorm
  training mutation have not been performed.
- Training-update readiness, convergence, policy quality, arbitrary rollouts,
  public readiness, checkpoint continuation, exact resume, evaluation, and long
  training remain unestablished or unauthorized as stated above.

## Do not do

- Do not start or implement B2-R1 without a new explicit user authorization
  after GPT re-review.
- Do not modify production, installed HARL, harness behavior, public gates, or
  checkpoint artifacts.
- Do not run backward, optimizer step, trainer update, Isaac, training,
  playback, evaluation, or checkpoint weight save/load.
- Do not claim GPT REVIEW PASS, training-update readiness, convergence,
  checkpoint readiness, or public readiness.
- Do not commit this documentation revision.

## Next step

Stop for independent GPT re-review of the revised authoritative B2-R0 report and
targeted revision summary. B2-R1 remains unstarted and unauthorized.

## Authoritative reports / archives

- `AgentRead/202609/20260901/PHASE_B2_R0_TRAINING_UPDATE_READINESS_ARCHITECTURE_DESIGN.md`
- `AgentRead/202609/20260901/PHASE_B2_R0_GPT_TARGETED_REVISION_SUMMARY.md`
- `AgentRead/202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R0_GPT_TARGETED_REVISION_HANDOFF_20260901.md`
- `AgentRead/202609/20260901/TASK_PROGRESS_ARCHIVE_BEFORE_B2_R0_HANDOFF_20260901.md`
- `AgentRead/202608/20260831/PHASE_B2_V2_FINAL_CLOSURE_AND_COMMIT_READINESS_REVIEW.md`
- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5K_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/202608/20260831/PHASE_B2_V2_PD2_R5J_I5B_RETURNS_OBSERVABILITY_AND_ORACLE_REVISION_IMPLEMENTATION_REPORT.md`
