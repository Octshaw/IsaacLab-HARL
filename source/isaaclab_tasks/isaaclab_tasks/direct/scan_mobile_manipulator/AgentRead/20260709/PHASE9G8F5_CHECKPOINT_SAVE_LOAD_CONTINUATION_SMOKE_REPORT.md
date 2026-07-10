# Phase 9G-8F-5 Checkpoint Save / Load / Continuation Smoke Report

Date: 2026-07-09

## Classification

```text
PASS
```

Real installed HARL source models completed a native project save, shared-loader validated weight continuation into independently constructed target models, exact state/output equivalence, real post-load actor/critic updates, and a second native save.

All checkpoint artifacts were confined to Python temporary directories.

## Files

Created:

```text
scripts/environments/test_assignment_checkpoint_save_load_continuation_smoke.py
AgentRead/20260709/PHASE9G8F5_CHECKPOINT_SAVE_LOAD_CONTINUATION_SMOKE_REPORT.md
AgentRead/20260709/TASK_PROGRESS_ARCHIVE_BEFORE_PHASE9G8F5_SAVE_LOAD_CONTINUATION_SMOKE_20260709.md
```

Modified:

```text
AgentRead/TASK_PROGRESS.md
```

No production Python source required modification.

Inspected and reused:

```text
assignment_checkpoint_contract.py
assignment_checkpoint_save.py
assignment_checkpoint_load.py
assignment_harl_training.py
test_assignment_checkpoint_save_metadata_integration.py
test_assignment_checkpoint_all_loader_integration.py
test_assignment_actor_critic_buffer_forward_backward_readiness.py
```

## Toolchain

```text
Python:
  C:\isaacenvs\isaac45_harl\python.exe

PyTorch:
  2.5.1+cu121

Device:
  CPU

Temporary storage:
  tempfile.TemporaryDirectory only
```

The installed Gym maintenance warning remained non-blocking.

## Source Model Construction

Lifecycle source:

```text
3 independent real HAPPO actors
3 independent StochasticPolicy networks
3 actor Adam optimizers
1 centralized real VCritic / VNet
1 critic Adam optimizer
1 ValueNorm
feed-forward policy
EP shared state
```

Dimensions:

```text
actor: 1059
shared: 3183
action: 51
raw noop: 50
hidden sizes: [256,256]
```

Parameter counts:

```text
one actor: 353401
critic: 888543
```

## Source Preparation

Before saving:

```text
actor 0 ran one real HAPPO.update
critic ran one real VCritic.update with ValueNorm
actor 0 Adam state existed
critic Adam state existed
source losses and gradients were finite
```

The source checkpoint was therefore not a default-initialization-only fixture.

Actor/critic optimizer states were deliberately not included in the checkpoint. The completion metadata recorded:

```text
actor_optimizer_available = false
critic_optimizer_available = false
training_counters_available = false
rng_state_available = false
environment_resolver_state_available = false
rollout_buffer_state_available = false
```

## Native Save

The actual `AssignmentCheckpointSaveCoordinator` produced the first checkpoint at:

```text
temporary_run_root/models
checkpoint_kind = final
checkpoint_generation = 0
```

Checkpoint-local files:

```text
actor_agent_robot_0.pt
actor_agent_robot_1.pt
actor_agent_robot_2.pt
assignment_contract_fingerprint.txt
assignment_contract_manifest.json
assignment_training_state_manifest.json
critic_agent.pt
value_normalizer.pt
```

The run root also contained its canonical contract manifest and fingerprint.

Checkpoint-local total size:

```text
7,828,369 bytes
```

The coordinator event trace confirmed:

```text
assignment_training_state_manifest.json
```

was committed last.

## Metadata And Completion Validation

Independent test verification passed:

```text
contract manifest parses as assignment_checkpoint_contract_v1
stored SHA-256 verifies against canonical manifest
run-root and checkpoint-local fingerprints agree
training-state manifest parses as assignment_training_state_v1
training-state contract binding matches
checkpoint kind is final
checkpoint generation is 0
continuation classification is validated_weight_continuation_candidate
ordered actors are robot_0, robot_1, robot_2
all eight checkpoint-local files exist
all file sizes match
all file SHA-256 values match
all tensor inventories match source state_dict inventories
all tensor inventory SHA-256 values validate through contract parsing
```

Contract fingerprint:

```text
94fb524aae2b7cf31c91742fe590b670097f67bc599b189146ca4ce7021da158
```

The shared loader independently repeated its mandatory metadata, integrity, inventory, and compatibility validation.

## Fresh Target Before Load

Fresh lifecycle target objects were constructed with a different deterministic seed.

Verified before loading:

```text
source and target module objects differ
source and target parameter storage differs
source and target optimizers differ
all target Adam states are empty
at least one actor state tensor differs
at least one critic state tensor differs
actor probability outputs differ
critic values differ
```

This excludes identical initialization as the cause of post-load equivalence.

## Validated Weight Continuation

The shared loader was called with:

```text
purpose = VALIDATED_WEIGHT_CONTINUATION
continuation_reset_acknowledged = true
```

Result:

```text
loaded actors: robot_0, robot_1, robot_2
critic loaded: true
ValueNorm loaded: true
legacy fallback: false
named ablation: absent
checkpoint kind: final
checkpoint generation: 0
contract fingerprint: exact
continuation acknowledgement: recorded
```

No inherited HARL restore was called.

## Exact State Equality

After loading:

```text
source actor 0 == target actor 0
source actor 1 == target actor 1
source actor 2 == target actor 2
source critic == target critic
source ValueNorm == target ValueNorm
```

Results:

```text
state keys compared: 51
exact tensor matches: 51
missing keys: 0
unexpected keys: 0
shape mismatches: 0
dtype mismatches: 0
value mismatches: 0
```

## Deterministic Output Equivalence

The fixed probe used finite actor observations, shared observations, fixed valid target/noop actions, historical masks, active masks, and feed-forward RNN placeholders.

All three actors matched on:

```text
fixed-action log probabilities
entropy
categorical probabilities
returned feed-forward RNN placeholders
```

Critic matched on:

```text
centralized values
returned feed-forward RNN placeholders
```

ValueNorm matched on:

```text
state tensors
normalized fixed input
denormalized fixed input
```

Maximum absolute differences:

```text
actor outputs: 0.0
critic outputs: 0.0
ValueNorm outputs: 0.0
```

No stochastic sampled-action equality claim was used.

## Optimizer Reset Semantics

Immediately after loading:

```text
target actor optimizer states remained empty
target critic optimizer state remained empty
target optimizer parameter groups referenced target parameters
no source Adam moment or step counter was restored
```

Source optimizers already contained Adam state from source preparation.

This proves:

```text
validated weight continuation
```

not:

```text
exact resume
```

## Post-Load Continuation

The loaded target completed one real update through each installed path:

```text
HAPPO.update
VCritic.update with ValueNorm
```

Evidence:

| metric | result |
|---|---:|
| Actor policy loss | -0.2138750 |
| Actor pre-clip gradient norm | 1.7860661 |
| Critic value loss | 9.0754890 |
| Critic pre-clip gradient norm | 141.1625671 |
| Actor parameter changed | yes |
| Critic parameter changed | yes |
| Actor gradients finite | yes |
| Critic gradients finite | yes |
| Updated parameters finite | yes |
| Target actor Adam state created | yes |
| Target critic Adam state created | yes |

Installed HARL gradient clipping remained active with maximum norm `10.0`.

Only actor 0 was updated. Target actors 1 and 2 remained bitwise unchanged.

## Source Isolation

After target updates:

```text
all source actor states remained exact
source critic state remained exact
source ValueNorm state remained exact
no target optimizer referenced source parameter storage
```

## Normal Evaluation Restore

A second independently initialized target set was loaded with:

```text
purpose = NORMAL_EVALUATION
```

Verified:

```text
all completed-checkpoint file digests passed
three actors loaded
critic was not live-loaded
ValueNorm was not live-loaded
actor probabilities exactly matched source
target critic remained unchanged
target ValueNorm remained unchanged
```

No playback or evaluation loop ran.

## Named Ablation

The environment-free named ablation smoke used:

```text
lifecycle_contract_c_checkpoint_to_lifecycle_ablation_evaluation_v1
```

Verified:

```text
explicit ablation compatibility passed
three actors loaded
result recorded the exact ablation name
critic and ValueNorm were not loaded
actor probabilities exactly matched checkpoint source
```

No wrapper environment, resolver, or policy rollout was constructed.

## Native Legacy Smoke

The native legacy profile used:

```text
actor: 909
shared: 2727
action: 51
```

The real coordinator produced:

```text
native manifest/fingerprint/completion marker
three canonical actor files
critic inventory
ValueNorm inventory
```

Normal evaluation loaded the three canonical actors through the shared loader. Actor probabilities exactly matched the native legacy source.

The unversioned legacy fallback was not used.

## Corruption And Mismatch Tests

All negative checkpoints were first produced by the real save coordinator.

| case | result |
|---|---|
| Actor artifact extended with extra bytes | File integrity rejection; no actor mutation |
| Actor artifact same-size byte flip | SHA-256 rejection; no actor mutation |
| Missing completion marker | Rejected before `torch.load`; no mutation |
| Lifecycle mask-contract semantic mismatch | Rejected in Stage 1 before deserialization |
| Actor learning-rate-only mismatch, normal evaluation | Allowed |
| Actor learning-rate-only mismatch, continuation | Rejected before deserialization |
| Live actor input width 1058 | Live inventory rejection before any partial mutation |

No mismatch-ignore, force-load, tensor casting, prefix rewriting, or `strict=False` path was used.

## Re-Save After Continuation

After the target actor/critic update, the same coordinator owner saved back to the same recognized `models` directory with:

```text
checkpoint_kind = final
checkpoint_generation = 1
```

Verified:

```text
second completion marker committed last
generation advanced 0 -> 1
contract fingerprint remained unchanged
training-state binding remained valid
actor 0 file SHA-256 changed
critic file SHA-256 changed
continuation classification remained validated_weight_continuation_candidate
```

The second checkpoint was not loaded.

Generation was explicitly advanced by the same synthetic run/coordinator owner. The generation counter was not restored from checkpoint and no exact-resume claim follows.

## Tests

New Phase 9G-8F-5 smoke:

```text
PASS 22/22
```

Required regressions:

| suite | result |
|---|---|
| Phase 9G-8F-1 contract core | PASS, 27/27 |
| Phase 9G-8F-2 save integration | PASS, 15/15 |
| Phase 9G-8F-3 all-loader integration | PASS, 15/15 |
| Phase 9G-8F-4 forward/backward readiness | PASS, 15/15 |
| Phase 9G-8E mask/HARL replay | PASS, 11/11 |
| Phase 9G-8E-R feed-forward guard | PASS, 9/9 |

Total:

```text
PASS 114/114
```

Validation:

```text
py_compile: PASS
direct assignment load scan: PASS
git diff --check: PASS
```

## Direct-Load Scan

Production assignment paths contain two `torch.load` calls, both inside:

```text
assignment_checkpoint_load.py
```

Both calls use:

```text
map_location="cpu"
weights_only=True
```

Other findings:

```text
strict=False: absent
full-model pickle load: absent
*_full.pt: rejection/guard checks only
native assignment inherited HARL restore: bypassed
new smoke direct torch.save/load invocation: absent
```

The new smoke temporarily spies on `assignment_checkpoint_load.torch.load` to prove selected Stage-1 failures deserialize nothing; it does not call `torch.load` itself.

## Known Limitations

- This is a synthetic CPU checkpoint smoke, not a real environment training run.
- Validated continuation restores weights and ValueNorm only; optimizer, counters, RNG, environment/resolver, and rollout buffers reset.
- The second-generation checkpoint was verified but intentionally not loaded.
- Exact resume and fine-tuning remain unsupported.
- Lifecycle recurrent, FP critic, `share_param=true`, HATRPO, and HAA2C remain outside the official first support matrix.
- Resolver-enabled training remains prohibited pending Phase 9G-8F-6 readiness review.

## Non-Modification Confirmation

```text
installed HARL: not modified
Conda environment: not modified
production save/load/contract code: not modified
YAML defaults: not modified
actor/critic architecture: not modified
observation/shared/action schemas: not modified
resolver/mask/reward/environment behavior: not modified
real prior training checkpoint: not used
checkpoint outside temporary directories: not written
assignment environment: not constructed
environment reset/step/rollout: not run
formal training loop: not run
playback/evaluation loop: not run
AppLauncher/Isaac Sim: not launched
commit: not made
```

## Next Phase Boundary

```text
Phase 9G-8F-6:
Phase 9G-8F Readiness Review
```

No Phase 9G-8F-6 work was started.

## Final Decision

```text
PASS
```

The native coordinator, immutable metadata, shared loader, real HARL model state, deterministic outputs, optimizer reset semantics, post-load continuation update, and continuation re-save now pass end to end without an assignment environment.
