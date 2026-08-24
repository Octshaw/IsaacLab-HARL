# TASK_PROGRESS

## Current status

    classification:
      PHASE-B0-3I2-DORMANT-RUNTIME-DOMAIN-AND-CAPABILITY-PORTS-COMPLETE-AWAITING-GPT-REVIEW

    Phase A:
      final review passed; previously committed by user

    B0-1A / B0-1B / B0-2:
      review passed; regressions remain green

    B0-3 design:
      B0-3D / B0-3D-R / B0-3D-R2 closed

    B0-3I1:
      review passed; pure episode rebuild remains exact

    B0-3I2:
      complete at pure/default-off domain-composition level
      awaiting GPT/user review

    event-profile runtime readiness:
      interface_only / Phase-A blocked

    environment production wiring:
      not implemented

    B0-3I3 / B0-3I4:
      not entered; not authorized

    Phase B/C/D/E:
      not entered; not authorized

    Isaac/AppLauncher/training/playback/evaluation:
      not run

    commit:
      none

## Latest completed phase

B0-3I2 adds a dormant B0-private runtime-domain composition module. One
`_EventProfileLifecycleRuntimeDomain` retains one canonical event-profile stack
for one vector-domain lifetime:

- exact canonical resolved event-profile identity;
- stable device, environment IDs, E, M, and N;
- one `EnvironmentExecutionFactsProducer`;
- one `LifecycleGenerationClock`;
- one `LifecycleStateStore`;
- one `LifecycleAuthorityTransactionCoordinator`;
- the coordinator's exact unique `LifecycleAuthorityRuntime` and
  `TransitionConsumeLedger`.

No alternate producer, clock, StateStore, authority, ledger, or coordinator is
created. No process-wide singleton or mutable domain registry was added.

## Active architecture / implementation path

Construction uses frozen `_EventProfileLifecycleDomainSpec` identity:

    exact event profile
    + explicit device
    + unique nonnegative int64 env IDs
    + positive exact-int M/N

The domain captures its own independent identity copy and constructs canonical
dormant pre-bootstrap state:

    task AVAILABLE
    robot NEEDS_ASSIGNMENT
    ownership -1
    failed pairs false
    completion count 0
    reason NONE
    store version 0
    episode -1
    transition -1
    result None

Construction does not bootstrap an episode, request a transition, allocate a
facts token, consume the ledger, issue a receipt, or fabricate a result/event.

The environment capability supports exactly:

    episode_rebuild(
      selected_env_ids,
      initial_task_state,
      initial_robot_state,
      initial_ownership)

It injects domain-owned profile/device and delegates to the reviewed I1
primitive. Its context exposes only `commit_physical_reset_complete()`.

The read capability supports exactly:

    read_current()

It delegates directly to `coordinator.read_published_view()` and never joins a
raw StateStore snapshot with a raw clock snapshot.

Domain supported surface is limited to identity plus the two retained ports.
There is no supported getter for producer, clock, StateStore, authority, ledger,
coordinator, receipt, writer capability, lock, components, or publication
installation.

## Retained lifetime and poison

Observable same-domain continuity is:

    construct: version 0, episode -1, transition -1
    rebuild 1: version 1, episode  0, transition -1
    rebuild 2: version 2, episode  1, transition -1
    rebuild 3: version 3, episode  2, transition -1

Episode rebuild reconstructs none of the retained authorities or ports. Partial
rebuild and I1 ordering remain unchanged.

Coordinator poison is the only poison authority. After a controlled I1
post-swap failure, both fresh read and environment rebuild reject. The domain
adds no independent poison/reset/retry/rollback path.

## Explicitly absent scope

I2 does not implement:

- transition-context reservation or physical-transition finalization;
- facts building, raw scan reporting, owner-qualified completion, termination,
  coverage, reward, or health/failure/release adapters;
- terminal slot/store, terminal reader/ack, designated consumer, or observer;
- R3 synchronous ack-before-step guard;
- `_reset_idx`, `_get_dones`, `_get_rewards`, wrapper, resolver, controller,
  HARL, config, training, playback, or task-entrypoint wiring.

No I3/I4 placeholder methods were added.

## Changed / new files

Current B0-3I2 authorized delta:

- added
  `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_event_profile_runtime_domain.py`;
- added
  `scripts/environments/test_assignment_phase_b0_3i2_runtime_domain_capabilities_pure.py`;
- added
  `AgentRead/20260814/PHASE_B0_3I2_DORMANT_RUNTIME_DOMAIN_AND_CAPABILITY_PORTS_IMPLEMENTATION_REPORT.md`;
- archived the prior handoff at
  `AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_3I2_IMPLEMENTATION_20260814.md`;
- rewrote this concise current handoff.

The pre-existing dirty B0 cohort was preserved. Frozen contracts, I1/B0
foundations, environment, wrapper, resolver, controller, HARL, config, and
checkpoint files were not edited.

## Verification

Interpreter:

    C:\isaacenvs\isaac45_harl\python.exe

Results:

- new Python `py_compile`: passed;
- B0-3I2 normal mode: 12/12 passed;
- B0-3I2 `-I -B`: 12/12 passed;
- B0-3I1: 12/12 passed;
- B0-2: 18/18 passed;
- B0-1A: 9/9 passed;
- B0-1B: 12/12 passed;
- lifecycle transition contract: 12/12 passed;
- assignment profile contract: 16/16 passed;
- event-profile schema contract: 9/9 passed;
- Phase-A default-off identity: 16/16 passed;
- profile production wiring: 10/10 passed;
- event-gated MRTA contract: 13/13 passed.

Closeout checks passed:

- frozen and retained-runtime hash audit;
- no production wiring and empty module-export audit;
- no terminal/reporter/facts capability audit;
- `git diff --check`, trailing whitespace, Markdown, classification/path,
  changed-scope, HEAD/branch/empty-index checks.

No Isaac/AppLauncher, environment, training, playback, or evaluation was run.

## Known issues / unfinished work

- no B0-3I3 pre-reset reporter/facts orchestration;
- no B0-3I4 terminal handoff/ack/pre-step permission system;
- no environment production composition root or real autoreset integration;
- no wrapper/resolver/controller/HARL transport;
- no Phase-B assignment commit, scheduling, Top-K/local sets, component solve,
  DVM, cost, retry, checkpoint, training, or runtime performance evidence.

All eleven numeric TBDs remain unresolved:

    top_k_tasks_per_robot
    local_robot_cap
    local_task_cap
    pair_abs_threshold
    pair_rel_threshold
    component_abs_threshold
    component_rel_threshold
    transfer_penalty
    rejection_penalty_scale
    alignment_time_constant
    assignment_retry_cadence

## Do not do

Without explicit authorization:

- do not begin B0-3I3, B0-3I4, or Phase B/C/D/E;
- do not wire the domain into environment/package/wrapper/HARL/config routes;
- do not expose raw producer/clock/store/ledger/authority/coordinator getters;
- do not add transition reporter/facts APIs to the environment port;
- do not add terminal slot/ack/observer/designated-consumer/pre-step guard APIs;
- do not modify runtime readiness or frozen contracts;
- do not select numeric TBDs;
- do not run Isaac/AppLauncher/training/playback/evaluation or commit.

## Next step

Review the B0-3I2 retained-domain and capability-port implementation. Do not
infer B0-3I3, B0-3I4, or production environment-integration authorization.

## Detailed reports / archives

- AgentRead/20260814/PHASE_B0_3I2_DORMANT_RUNTIME_DOMAIN_AND_CAPABILITY_PORTS_IMPLEMENTATION_REPORT.md
- AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_3I2_IMPLEMENTATION_20260814.md
- AgentRead/20260814/PHASE_B0_3I1_PURE_EPISODE_REBUILD_TRANSACTION_IMPLEMENTATION_REPORT.md
- AgentRead/20260814/TASK_PROGRESS_ARCHIVE_BEFORE_B0_3I1_IMPLEMENTATION_20260814.md
- AgentRead/20260814/PHASE_B0_3DR2_SYNCHRONOUS_TERMINAL_ACK_PROTOCOL_CLOSEOUT.md
- AgentRead/20260814/PHASE_B0_3DR_TARGETED_ENVIRONMENT_INTEGRATION_SEMANTIC_REVISION.md
- AgentRead/20260814/PHASE_B0_3D_ENVIRONMENT_PRE_RESET_AND_EPISODE_RESET_INTEGRATION_DESIGN.md
- AgentRead/20260814/PHASE_B0_2_PURE_LIFECYCLE_AUTHORITY_TRANSACTION_IMPLEMENTATION_REPORT.md
- AgentRead/20260809/PHASE_B0_1B_PURE_GENERATION_CLOCK_IMPLEMENTATION_REPORT.md
- AgentRead/20260809/PHASE_B0_1A_PURE_EXECUTION_FACTS_PRODUCER_IMPLEMENTATION_REPORT.md

