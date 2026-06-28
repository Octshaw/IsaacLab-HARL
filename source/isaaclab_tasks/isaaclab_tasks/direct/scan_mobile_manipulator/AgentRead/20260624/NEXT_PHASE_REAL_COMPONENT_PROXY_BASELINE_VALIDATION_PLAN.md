# Next Plan: Close Obstacle Diagnostic Branch and Return to Real-Component Proxy-Robot Task Allocation Validation

## 0. Background

The project goal is dynamic multi-robot task allocation for arbitrary-size viewpoint sets and variable numbers of robots.

The current implementation path is:

```text
simple assignment environment
-> real component mesh
-> proxy/custom small robots
-> dynamic task allocation research
```

Real robot articulation, IK, detailed collision, raycast coverage, and full motion planning are intentionally not part of the current main line because they would shift the work from task allocation to a large robotics engineering integration project.

The current real-component scenario uses:

```text
real component mesh
proxy/custom robots
CSV viewpoint input
task allocation solvers and RL environment
diagnostic-only obstacle geometry
```

Phase 7B-3 is complete. It verified that mesh-footprint obstacle diagnostics and obstacle-aware candidate comparison can run without changing live solver behavior. However, the current GUI red lines are drawn from blocked candidate pairs, not from actually selected assignment pairs. This can visually overstate how often greedy/nearest are truly choosing obstacle-intersecting assignments.

Therefore, the next work should not expand into full obstacle avoidance. It should first clarify selected assignment visualization, then return to baseline/RL validation in the real-component proxy-robot environment.

---

## 1. Overall Goal

Close the current obstacle diagnostic branch cleanly and return to the main research question:

```text
In a real-component mesh + proxy-robot environment, do the earlier dynamic task allocation problems still appear?
```

Specifically, validate whether the previous issue still exists:

```text
A viewpoint can be statically feasible, but dynamically undesirable or problematic during execution.
```

The focus should remain on task allocation, not full motion planning.

---

## 2. Phase 7B-4A: Selected Assignment Line Visualization Sanity Check

### Purpose

The current obstacle debug red lines visualize blocked candidate robot-viewpoint pairs:

```text
obstacle_debug_visualization_line_source = mesh_footprint_intersections
```

This is useful for checking whether the mesh-footprint diagnostic geometry is working, but it is not ideal for understanding solver behavior.

Add a small diagnostic visualization mode for actual solver-selected assignments.

### Goal

Add a visualization mode that can draw only the currently selected assignment pairs:

```text
obstacle_debug_visualization_line_source = selected_assignments
```

or a similarly named option.

This mode should show lines for:

```text
robot base XY -> selected viewpoint XY
```

for the actual solver output at each step or latest available assignment record.

### Requirements

Keep this diagnostic-only.

Do not change:

```text
solver behavior
available_mask
feasible_mask
static_geometric_feasible_mask
cost_matrix
reward
controller
HARL
training
environment dynamics
```

Do not promote `mesh_footprint_aware_cost_matrix` into live solver inputs.

### Expected Output

When running greedy or nearest in GUI mode, the user should be able to distinguish:

```text
blocked candidate lines
```

from:

```text
actual selected assignment lines
```

The selected assignment visualization should make it clear whether greedy/nearest are actually selecting paths that intersect the mesh footprint.

### Suggested Diagnostics Fields

If easy and low-risk, add compact diagnostics such as:

```text
selected_assignment_debug_visualization_enabled
selected_assignment_debug_visualization_line_count
selected_assignment_debug_visualization_pairs_sample
selected_assignment_debug_visualization_intersection_count
selected_assignment_debug_visualization_skipped_reason
```

Do not dump huge matrices or full histories unless explicitly requested.

### Validation Run

Run short GUI sanity checks:

```text
method = greedy
num_envs = 1
max_steps = 20 to 50
scenario = algorithm_proxy_component_mesh.yaml
obstacle diagnostics = enabled
selected assignment line visualization = enabled
```

Then repeat for:

```text
method = nearest
```

### Success Criteria

Phase 7B-4A is complete if:

```text
1. selected assignment lines are visible and correspond to actual solver-selected robot-viewpoint pairs
2. candidate blocked lines and selected assignment lines are no longer confused
3. selected assignment visualization agrees with selected_intersection statistics
4. no live solver behavior changed
5. git diff --check passes
6. TASK_PROGRESS.md is updated with a compact handoff
```

### Report

Write a concise report:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260624/PHASE7B4A_SELECTED_ASSIGNMENT_VISUALIZATION_REPORT.md
```

The report should include:

```text
what was changed
why it was needed
commands run
GUI observations
whether selected lines match statistics
whether solver behavior changed
known limitations
git diff --check result
git status summary
```

---

## 3. Phase 7B Wrap-Up: Stop Expanding Obstacle Diagnostics

After Phase 7B-4A, do not keep expanding obstacle diagnostics unless a clear bug is found.

Obstacle diagnostics should remain a supporting tool for task allocation cost analysis, not become a full path-planning or collision-avoidance subsystem.

### Keep

```text
mesh-footprint diagnostic intersection
obstacle-aware copied-problem candidate comparison
blocked candidate visualization
selected assignment visualization
compact reporting
```

### Do Not Add Now

```text
real robot articulation
IK
joint limits
3D collision checking
raycast coverage
full motion planning
local obstacle avoidance
mesh-footprint hard blocking
bbox hard blocking
RL reward changes
live solver cost replacement
```

### Wrap-Up Decision

At the end of 7B-4A, record this conclusion:

```text
Obstacle diagnostics are sufficient for current task-allocation experiments.
Further obstacle work should only happen if real-component proxy-robot baseline validation shows it is necessary.
```

---

## 4. Phase 8: Real-Component Proxy-Robot Baseline Validation

### Purpose

Return to the main task allocation question.

Use the real component mesh and proxy/custom robots to test whether earlier problems from the simple environment still exist.

The goal is not to prove final performance yet. The goal is to establish a reliable validation baseline in the upgraded environment.

### Scenario

Use the real-component proxy scenario:

```text
algorithm_proxy_component_mesh.yaml
```

or a renamed/stabilized scenario if needed.

The environment should use:

```text
real component mesh
proxy/custom robots
CSV viewpoints
existing random / nearest / greedy baselines
existing RL environment interface where applicable
diagnostic-only obstacle information
```

### Methods to Evaluate

Start with non-RL baselines:

```text
random
nearest
greedy
```

Then add RL only after baseline evaluation is stable.

### Metrics

Evaluate at least:

```text
success_rate
mean_final_coverage
mean_coverage_auc
num_completed_viewpoints
num_failed_viewpoints
num_timeout_viewpoints
num_unreachable_viewpoints
episode_length
repeated_assignment_count
stuck_or_no_progress_steps
robot_load_balance
per_robot_completed_count
mean_assignment_cost
selected_intersection_rate
selected_obstacle_penalty_sum
```

If already available, also keep:

```text
baseline_selected_intersection_rate
candidate_selected_intersection_rate
candidate_changed_assignment_rate
```

but these should remain diagnostic-only.

### Main Questions

The baseline validation should answer:

```text
1. Do random / nearest / greedy still behave reasonably in the real-component proxy environment?
2. Does nearest or greedy get stuck, repeat assignments, or fail to make coverage progress?
3. Does the previous static-feasible-but-dynamically-problematic issue still appear?
4. Are dynamic task status and robot status updates working correctly?
5. Are failures caused by task allocation logic, geometry diagnostics, or controller/proxy execution?
6. Is the environment stable enough to reintroduce RL evaluation?
```

### Suggested Run Sequence

First run smoke-level tests:

```text
num_envs = 1
num_episodes = 3
max_steps = 50
methods = random nearest greedy
```

Then run a longer baseline validation:

```text
num_envs = 1
num_episodes = 10
max_steps = 100 or 300
methods = random nearest greedy
```

Only after these are stable, run RL evaluation if the trained policy is compatible with the current observation/action interface.

### Success Criteria

Phase 8 baseline validation is complete if:

```text
1. random / nearest / greedy run successfully on the real-component proxy scenario
2. compact metrics are generated
3. failure/stall/repeated-assignment behavior is measurable
4. selected assignment visualization can help explain abnormal cases
5. no unrelated real robot engineering is added
6. results are summarized in a handoff report
```

### Report

Write:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/20260623/PHASE8_REAL_COMPONENT_PROXY_BASELINE_VALIDATION_REPORT.md
```

The report should include:

```text
scenario used
commands run
methods evaluated
episodes / max_steps
key metrics
whether earlier simple-environment problems reappear
notable failure cases
selected assignment visualization observations
whether RL evaluation is ready
known limitations
git diff --check result
git status summary
```

---

## 5. Phase 9: RL Re-Evaluation in the Real-Component Proxy Environment

Only start this after Phase 8 baseline validation is stable.

### Goal

Check whether the RL task allocation method still works when the simple environment is upgraded to:

```text
real component mesh
proxy/custom robots
CSV viewpoint set
diagnostic geometry
```

### Key Checks

Before training or evaluation, confirm:

```text
observation shape
action shape
available action mask
number of viewpoints
number of robots
noop handling
task status update
robot status update
reward compatibility
```

### Initial RL Work

Start with evaluation of the existing trained policy only if compatible.

If incompatible, document why and decide whether retraining is needed.

Do not immediately start large-scale training.

### RL Metrics

Compare RL with:

```text
random
nearest
greedy
```

using:

```text
coverage
success rate
coverage AUC
episode length
load balance
failure/stall rate
repeated assignment
selected obstacle intersection diagnostics
```

### Success Criteria

Phase 9 is complete if:

```text
1. RL evaluation or incompatibility is clearly diagnosed
2. baseline comparison is available
3. limitations are documented
4. next training or architecture changes are justified by evidence
```

---

## 6. Current Priority Order

Use this priority order:

```text
Priority 1:
Phase 7B-4A selected assignment line visualization sanity check

Priority 2:
Close obstacle diagnostic branch and update TASK_PROGRESS.md

Priority 3:
Phase 8 real-component proxy-robot baseline validation with random / nearest / greedy

Priority 4:
RL evaluation or retraining decision

Priority 5:
Only if justified, gated solver-cost experiment
```

Do not start with the gated solver-cost experiment. Current evidence shows the diagnostic tooling is ready, but the baseline selected assignment issue is not yet strongly exposed.

---

## 7. Important Boundaries

The project should stay focused on task allocation.

Do not let the next phase become:

```text
full robot simulation
full collision avoidance
motion planning
IK integration
raycast coverage
real robot articulation
```

Those can be future engineering extensions, but they are not required for the current research path.

The current research path is:

```text
dynamic multi-robot task allocation
with realistic component geometry as task/environment context
using proxy robots and diagnostic path-cost information
```

---

## 8. Final Expected Outcome

After this plan is completed, the project should have:

```text
1. real component mesh loaded
2. proxy/custom robots working
3. CSV viewpoint input working
4. obstacle diagnostics clarified
5. selected assignment visualization available
6. baseline methods evaluated in the upgraded environment
7. evidence about whether earlier dynamic task allocation problems still exist
8. a clear decision about whether RL evaluation/retraining is ready
```

This will put the project back on the main thesis path.
