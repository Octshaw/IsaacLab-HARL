# TASK_PROGRESS

## Current Status

Phase 9G-8H-0 completed the documentation-only design and static source audit for playback proposal/effective attribution and per-robot load diagnostics.

Classification: `DIAGNOSTIC-DESIGN-READY`.

The accepted visual playback showed a strongly imbalanced workload, but the current console cannot determine whether a motionless robot proposed noop, continued an active target under Contract C, had a target proposal rejected, or received a zero controller command for an infeasible active target.

## Latest Finding

Current `play_assignment.py` output:

```text
assignment=[...]
  = wrapper.last_assignment
  = effective_assignment
  = high-level controller input assignment
```

The same line's selected availability, selected probability, and selected distance describe the raw policy action. Raw proposal and effective execution are therefore mixed and need an explicit joined diagnostic.

The selected design uses a default-off playback-only collector. It reads raw policy actions/probabilities, copied pre/post physical state, and the wrapper's cloned lifecycle-resolution payload. It records per-robot proposal/effective rows, resolver attribution, completion/release flags, motion/distance fields, target segments, and episode load-balance summaries.

The collector will not call `pop_events()`. The runtime adapter remains the only resolver-event drainer, and the wrapper remains the only adapter-event drainer.

## Active Boundaries

- No source, tests, or YAML changed in Phase 9G-8H-0.
- No resolver, Contract C, observation, mask, reward, controller, environment, or checkpoint behavior changed.
- No training, playback, evaluation, checkpoint load, AppLauncher, or Isaac Sim ran.
- The successful 300-step controlled training smoke remains accepted; no performance conclusion is inferred from it.

## Next Step

After review and acceptance, the next possible phase is:

```text
Phase 9G-8H-1:
Playback Proposal-Effective Attribution Diagnostic Implementation
and Fake Regression
```

Phase 9G-8H-1 may implement only the default-off playback diagnostics and fake/non-environment regressions. A new bounded playback requires separate authorization.

## Detailed Reports / Archives

- `AgentRead/20260720/PHASE9G8H0_PLAYBACK_PROPOSAL_EFFECTIVE_ATTRIBUTION_AND_LOAD_BALANCE_DIAGNOSTIC_DESIGN.md`
- `AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8H0_PLAYBACK_ATTRIBUTION_DESIGN_20260720.md`
- `AgentRead/20260710/PHASE9G8G1R2T_TIMEOUT_CORRECTED_CONTROLLED_SMOKE_EXECUTION_REPORT.md`
- `AgentRead/20260710/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8G1R2T_TIMEOUT_CORRECTED_SMOKE_20260710.md`
