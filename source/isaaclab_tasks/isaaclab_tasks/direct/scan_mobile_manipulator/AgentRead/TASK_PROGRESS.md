# TASK_PROGRESS

## Current Status

Phase 9G-8I-0A implemented and validated the pure offline post-run audit tool for the planned fresh 100k `lifecycle_contract_c` training.

Classification: `OFFLINE-AUDIT-READY`.

The current committed baseline is `fadda4248b33d958d3798ef90013f21457358564` (`docs(assignment): define fresh 100k policy-noop training experiment`). Phase 9G-8I-0A changes are uncommitted as required.

## Latest Completed Phase

The new opt-in audit path reads:

```text
configs.json
TensorBoard scalar events
native-v2 contract manifests/fingerprints
training-state completion markers
checkpoint artifacts as opaque bytes for size/SHA-256 only
```

It audits fresh-start identity, all 63 expected scalar tags, exact 300..99900 step coverage, finiteness, noop/valid invariants, frozen trend windows, best/final kinds and generations, artifact inventories/hashes, and temporary/legacy artifact absence.

It writes exactly:

```text
assignment_training_run_audit.json
assignment_training_run_audit.md
```

## Key Files

Created:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_training_run_audit.py
scripts/reinforcement_learning/harl/audit_assignment_training_run.py
scripts/environments/test_assignment_training_run_audit.py
```

No existing training, playback, environment, checkpoint save/load, resolver, observation, mask, reward, controller, test, or YAML behavior file was modified.

## Latest Verification

```text
py_compile for module, CLI, and regression:
  PASS

test_assignment_training_run_audit.py:
  PASS, 4/4 groups
  1 complete 333-step/63-tag success fixture
  31 required failure cases

test_assignment_checkpoint_contract_core.py:
  PASS, 28/28

accepted native-v2 smoke checkpoint-only audit:
  PASS WITH WARNINGS, 0 hard failures

accepted native-v2 smoke events-only audit:
  PASS WITH WARNINGS, 63/63 tags, 0 nonfinite points

forbidden import/deserialization and entry-isolation scans:
  PASS

git diff/trailing-whitespace checks:
  PASS
```

The real-evidence warnings were expected: empty historical `progress.txt` and reduced one-point trend evidence.

## Safety Boundary

The tool has no checkpoint tensor deserialization, actor/critic/ValueNorm construction, AppLauncher, Isaac/omni runtime import, or HARL runner/model import. Existing result directories are read-only; audit output must be outside the audited timestamped seed directory.

No training, playback, evaluation, checkpoint load/restore, environment construction, AppLauncher, Isaac Sim, GUI, HARL/Conda modification, or commit occurred.

## Next Step

The next phase remains:

```text
Phase 9G-8I-1:
User-Executed Fresh 100k Controlled Training
```

The user manually runs the unchanged command frozen by Phase 9G-8I-0. After it completes, run the offline audit against the exact timestamped seed child and review its JSON/Markdown before authorizing any best/final attribution playback.

Codex must not launch the 100k run automatically. Do not infer per-agent participation, load balance, convergence, or production readiness from aggregate TensorBoard metrics.

## Detailed Reports / Archives

- `AgentRead/20260720/PHASE9G8I0A_CONTROLLED_TRAINING_POSTRUN_OFFLINE_AUDIT_TOOL_IMPLEMENTATION_AND_REGRESSION.md`
- `AgentRead/20260720/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8I0A_OFFLINE_TRAINING_AUDIT_TOOL_20260720.md`
- `AgentRead/20260720/PHASE9G8I0_POLICY_NOOP_LOAD_IMBALANCE_CONTROLLED_TRAINING_DESIGN_AND_PREFLIGHT.md`
