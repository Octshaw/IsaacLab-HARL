# TASK_PROGRESS

Compact handoff for the assignment-based scan-mobile-manipulator work.

## Current Status

Phase 9G-8F-3 completed all-loader compatibility integration.

Classification:

```text
PASS
```

Accepted prerequisites:

```text
Phase 9G-8F-1: PASS
Phase 9G-8F-2: PASS
```

Resolver-enabled training remains prohibited.

## Latest Completed Phase

One project-level loader now covers all audited assignment checkpoint boundaries.

Native loading enforces:

```text
completion marker
canonical manifest and SHA-256 integrity
recognized child/run-root agreement
purpose-aware compatibility
all declared file sizes and SHA-256
CPU weights_only state-dict deserialization
declared and live tensor key/shape/dtype inventories
strict live state loading
```

All required artifacts are inspected before any live model mutation.

## Entry Points

```text
training --dir:
  validated weight continuation through AssignmentOnPolicyHARunner.restore

generic play.py:
  assignment task hard-rejected before runner construction

play_assignment.py:
  normal evaluation / named ablation / explicit legacy fallback

playback diagnostics:
  same shared loader; checkpoint kind from completion marker

comparison-method loader:
  old direct loader removed; assignment RL remains hard-disabled before load
```

Native assignment checkpoints do not reach inherited HARL restore.

## Continuation And Evaluation

Assignment training `--dir` requires:

```text
--acknowledge-weight-continuation-reset
```

The acknowledgement covers optimizer, counter, best-reward, RNG, environment/resolver, and rollout-buffer resets.

Named lifecycle ablation remains exact and validator-owned.

Unversioned checkpoints are restricted to explicit resolver-disabled legacy actor evaluation. Fine-tuning remains deferred and exact resume remains unsupported.

## Files

Created:

```text
assignment_checkpoint_load.py
scripts/environments/test_assignment_checkpoint_all_loader_integration.py
AgentRead/20260709/PHASE9G8F3_ALL_LOADER_COMPATIBILITY_INTEGRATION_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F3_ALL_LOADER_INTEGRATION_20260709.md
```

Modified:

```text
assignment_checkpoint_contract.py
assignment_checkpoint_save.py
assignment_harl_training.py
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play.py
scripts/reinforcement_learning/harl/play_assignment.py
scripts/environments/evaluate_assignment_rl_playback_diagnostics.py
scripts/environments/evaluate_assignment_methods.py
scripts/environments/test_assignment_checkpoint_contract_core.py
AgentRead/TASK_PROGRESS.md
```

Installed HARL, Conda, YAML defaults, model architecture, observations/masks, resolver, reward, and environment behavior were not modified.

## Validation

Interpreter:

```text
C:\isaacenvs\isaac45_harl\python.exe
```

Results:

```text
py_compile: PASS
Phase 9G-8F-1 core: PASS, 27/27
Phase 9G-8F-2 save: PASS, 15/15
Phase 9G-8F-3 loader: PASS, 15/15
Phase 9G-8E mask/HARL replay: PASS, 11/11
Phase 9G-8E-R feed-forward guard: PASS, 9/9
direct assignment load scan: PASS
git diff --check: PASS
```

Tests loaded only temporary synthetic CPU state dictionaries. No real training checkpoint or full-model pickle was loaded.

No actor/critic forward, backward, optimizer step, training, playback, evaluation, or Isaac Sim/AppLauncher run occurred.

## Known Boundaries

Forward/backward actor/critic/buffer readiness and output-equivalence checkpoint smoke remain unimplemented.

Generic assignment playback remains intentionally rejected by generic `play.py`. Comparison-method assignment RL remains disabled.

Resolver-enabled training remains prohibited.

## Do Not Do

Do not run resolver-enabled training.

Do not bypass the shared loader or completion marker.

Do not use inherited HARL restore for native assignment checkpoints.

Do not claim exact resume or fine-tuning support.

Do not modify installed HARL or the Conda environment.

Do not commit unless explicitly requested.

## Next Step

```text
Phase 9G-8F-4:
Actor / Critic / Buffer Forward-Backward Readiness
```

## Detailed Reports / Archives

```text
AgentRead/20260709/PHASE9G8F3_ALL_LOADER_COMPATIBILITY_INTEGRATION_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F3_ALL_LOADER_INTEGRATION_20260709.md
AgentRead/20260709/PHASE9G8F2_CHECKPOINT_SAVE_METADATA_INTEGRATION_REPORT.md
AgentRead/20260709/PHASE9G8F1_MANIFEST_CANONICAL_JSON_FINGERPRINT_COMPATIBILITY_CORE_REPORT.md
AgentRead/20260709/PHASE9G8F0_CHECKPOINT_LOADER_MODEL_BUFFER_READINESS_DESIGN_AUDIT.md
```
