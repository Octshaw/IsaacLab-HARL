# Read-only Task: Diagnose the RL Assignment-to-Motion Pipeline

## 0. Purpose

The current goal is **diagnosis only**.

The non-RL baselines such as `nearest` and `greedy` can correctly traverse viewpoints, and the RL evaluation has been reported to load the intended 10M checkpoint. However, the trained RL policy does not appear to move robots to viewpoints during evaluation.

Please inspect the full pipeline from RL policy output to viewpoint coverage and write a diagnostic report. **Do not modify source code, environment code, training code, controller code, solver code, configs, or reward logic in this task.**

The only allowed repository output is a Markdown report, for example:

```text
RL_ASSIGNMENT_PIPELINE_DIAGNOSTIC_REPORT.md
```

If a runtime value cannot be observed without adding instrumentation, do **not** add instrumentation in this task. Instead, document exactly what could not be verified and list the minimal future instrumentation needed.

---

## 1. Read these files first

Before doing anything else, read:

```text
AGENTS.md
TASK_PROGRESS.md
```

Use the environment, command, and stop-rule conventions from `AGENTS.md`. In particular, use the project conda environment and avoid full training, long simulation jobs, or GPU-heavy experiments unless explicitly requested.

Also review the current assignment-related implementation status in `TASK_PROGRESS.md`, especially:

- `get_assignment_problem()` has already been added.
- `assignment_controller.py` has already been added.
- `random`, `nearest`, and `greedy` solvers have already been added.
- `evaluate_scan_assignment.py` and `view_scan_assignment.py` have already been added.
- The assignment controller intentionally turns invalid, covered, infeasible, or out-of-range assignments into zero actions.

---

## 2. Hard constraints

### Do not modify code

Do **not** edit any of the following in this task:

```text
*.py
*.yaml
*.toml
*.json
*.cfg
README.md
training scripts
environment files
controller files
solver files
HARL files
```

Do not add debug prints to the code. Do not add new CLI flags. Do not change reward functions. Do not change hyperparameters. Do not change evaluation behavior. Do not silently repair invalid assignments.

### Allowed actions

You may:

- inspect files with `Get-Content`, `rg`, `git grep`, or similar read-only commands;
- inspect existing logs and CSV files;
- run very small existing read-only smoke/evaluation commands if they already exist and do not require code changes;
- create one Markdown diagnostic report;
- optionally use temporary shell commands that do not modify repository files.

### Required safety check

At the beginning and end, record the repository state:

```powershell
git status --short
```

The final report must explicitly state whether any repository files were modified. If only the diagnostic report was created, say so.

---

## 3. Environment command pattern

Use the project conda environment.

Prefer:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python <command>
```

Before running any Python command, verify the interpreter:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

Expected executable path should be under:

```text
C:\isaacenvs\isaac45_harl
```

Do not run full training. Do not run long GPU jobs. Do not launch GUI unless explicitly necessary and approved.

---

## 4. Pipeline to diagnose

Diagnose this full chain:

```text
RL checkpoint loaded
  -> RL policy forward pass
  -> raw policy action
  -> action / assignment decoding
  -> assignment tensor
  -> assignment validity checks
  -> viewpoint_assignment_to_actions(...)
  -> 9D continuous action dict
  -> env.step(actions)
  -> base/scanner state update
  -> distance to assigned viewpoint decreases
  -> viewpoint reached / covered
```

The main question is:

> Is the RL policy actually producing valid high-level viewpoint assignments that are converted into nonzero controller actions and lead to progress toward viewpoints?

---

## 5. Key files and locations to inspect

Inspect these files if they exist in the repository:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assignment_controller.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/scan_mobile_manipulator_env.py
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/solvers/*.py
scripts/environments/evaluate_scan_assignment.py
scripts/environments/view_scan_assignment.py
scripts/reinforcement_learning/harl/train.py
scripts/reinforcement_learning/harl/play.py
scripts/reinforcement_learning/harl/*.py
```

Also search for these names:

```text
viewpoint_assignment_to_actions
get_assignment_problem
assignment
available_mask
feasible_mask
viewpoints_covered
coverage_ratio
new_viewpoints
duplicate_scans
reach_violation
runner.restore
restore
checkpoint
load
save_dir
run_dir
deterministic
sample
argmax
mode
entropy
log_prob
```

Suggested read-only search commands:

```powershell
rg "viewpoint_assignment_to_actions|get_assignment_problem|feasible_mask|viewpoints_covered|available_mask" .
rg "deterministic|sample|argmax|mode|entropy|log_prob" scripts source
rg "restore|checkpoint|load|save_dir|run_dir" scripts source
```

---

## 6. Diagnostic questions to answer

### 6.1 Checkpoint and eval mode

Answer:

1. Which script is used for RL evaluation or playback?
2. Which checkpoint path is loaded?
3. Is the loaded checkpoint path printed clearly?
4. Is the actor placed in evaluation mode?
5. Is evaluation deterministic or stochastic?
6. If actions are sampled stochastically during evaluation, where does that happen?
7. Does the evaluation path expose entropy, log probability, action probabilities, or logits?

Evidence to collect:

```text
file path
function / class name
relevant code snippet or line description
actual command used, if any
```

Do not change eval behavior. Only document it.

---

### 6.2 RL action semantics

Determine whether the RL policy outputs:

```text
A. high-level viewpoint IDs / assignment actions
```

or

```text
B. low-level 9D continuous environment actions
```

This is critical.

If the RL policy directly outputs 9D continuous actions, then the trained policy is not using the high-level assignment controller. In that case, the failure is not necessarily invalid viewpoint assignment; the RL policy may be learning the full low-level control problem directly.

Answer:

1. What is the RL action space shape?
2. Is the RL action discrete or continuous?
3. Does the RL policy output one action per robot?
4. Does the RL output represent viewpoint IDs, or normalized 9D control values?
5. Is there any decoding step from raw RL action to `assignment: torch.long`?
6. Does the decoded assignment have shape `[num_envs, num_agents]`?
7. Does the decoded assignment have dtype `torch.long`?
8. Does the decoded assignment use viewpoint indices in `[0, num_viewpoints - 1]`?

Evidence to collect:

```text
raw action source
assignment decode location
expected action shape
actual action shape, if available from existing logs or code
```

---

### 6.3 Whether RL calls `viewpoint_assignment_to_actions`

Answer:

1. Does the RL evaluation/playback path call `viewpoint_assignment_to_actions(env, assignment)`?
2. If yes, where exactly?
3. If no, does it pass RL actions directly to `env.step(...)`?
4. Does the training path call `viewpoint_assignment_to_actions`, or only the baseline scripts do?
5. Do `nearest` and `greedy` share the same controller path as RL, or are they separate pipelines?

Classify the pipeline as one of:

```text
Pipeline A:
RL policy -> viewpoint assignment -> assignment_controller -> 9D action -> env.step

Pipeline B:
RL policy -> 9D continuous action directly -> env.step

Pipeline C:
RL policy -> other wrapper/decoder -> env.step

Pipeline D:
Cannot determine from read-only inspection
```

---

### 6.4 Assignment validity logic

Inspect the controller validity logic. The expected logic is conceptually:

```python
in_range = (assignment >= 0) & (assignment < num_viewpoints)
target_covered = problem["viewpoints_covered"][env_ids, safe_assignment]
target_feasible = problem["feasible_mask"][env_ids, agent_ids, safe_assignment]
valid = in_range & (~target_covered) & target_feasible
actions = torch.where(valid.unsqueeze(-1), actions, torch.zeros_like(actions))
```

Answer:

1. What makes an assignment invalid?
2. What happens to invalid assignments?
3. Are already covered viewpoints converted to zero actions?
4. Are infeasible robot-viewpoint pairs converted to zero actions?
5. Are out-of-range viewpoint IDs converted to zero actions?
6. Is `-1` treated as no-op?
7. Does the controller prevent duplicate assignments across robots?
8. If duplicate assignments are not prevented in the controller, do solvers prevent them?
9. Does the RL policy have any mechanism to avoid duplicates?

Important distinction:

- Post-controller invalid-action zeroing is not the same as action masking in the policy distribution.
- If the policy is not masked before sampling, it may frequently generate invalid or unhelpful assignments.

Do not add masking in this task. Only document whether masking appears to exist.

---

### 6.5 Action mask / feasibility mask usage in RL

Answer:

1. Does the RL observation include `available_mask`, `feasible_mask`, `viewpoints_covered`, or equivalent mask information?
2. Does the RL policy apply a mask to logits before sampling or selecting actions?
3. If the action space is continuous 9D, is there any assignment-level mask at all?
4. Are infeasible or already covered targets only handled after the action is chosen?
5. Is there any invalid-action penalty in reward or info logs?

Look for code patterns like:

```python
logits[invalid_actions] = -1e10
masked_logits = ...
Categorical(logits=...)
```

or HARL equivalents.

If no mask exists, state that clearly.

---

### 6.6 Baseline pipeline comparison

Because `nearest` and `greedy` can traverse viewpoints, compare their pipeline to the RL pipeline.

Answer:

1. How do `nearest` and `greedy` obtain the assignment problem?
2. Do they use `env.get_assignment_problem()`?
3. Do they return `torch.long` assignments?
4. Do they avoid duplicate viewpoint assignments?
5. Do they avoid covered viewpoints?
6. Do they avoid infeasible robot-viewpoint pairs?
7. Do they call `viewpoint_assignment_to_actions`?
8. Do they pass the resulting 9D action dict to `env.step`?
9. Which parts of the baseline pipeline are shared with RL?
10. Which parts differ?

Create a table in the final report:

| Pipeline stage | nearest/greedy | RL | Same or different? | Evidence |
|---|---|---|---|---|
| assignment problem source | | | | |
| action type | | | | |
| assignment decode | | | | |
| validity filtering | | | | |
| controller call | | | | |
| env.step action | | | | |
| coverage tracking | | | | |

---

### 6.7 Movement and coverage semantics

Inspect how environment state changes after an action.

Answer:

1. Which tensors represent base position, scanner position, base yaw, scanner orientation, and coverage state?
2. Does `env.step` update high-level tensors directly, or real PhysX articulations?
3. How is a viewpoint marked as covered?
4. Does coverage require position tolerance, orientation tolerance, FOV direction, or other conditions?
5. Are `coverage_ratio`, `new_viewpoints`, `duplicate_scans`, and `reach_violation` logged during training/evaluation?
6. Is there any difference between visible marker motion and internal tensor motion?

Do not change any state update or coverage logic.

---

### 6.8 Reward and learning signal inspection

Without changing reward code, inspect whether the reward appears able to distinguish useful assignments.

Answer:

1. What reward terms exist?
2. Which terms reward newly covered viewpoints?
3. Which terms penalize duplicate scans or invalid/reach violations?
4. Is there a distance-to-target shaping reward?
5. Does reward depend on assignment validity directly?
6. Are reward terms exposed through `info["log"]` or TensorBoard?
7. Could a policy receive mostly negative or weak signal before reaching the first viewpoint?

This section should be analytical only. Do not propose reward changes as implemented changes. Put possible future reward investigations in a separate “future work” section.

---

### 6.9 Observation content inspection

Inspect the RL observation construction.

Answer:

1. Does each agent observe its own pose?
2. Does each agent observe viewpoint positions?
3. Does each agent observe covered/uncovered status?
4. Does each agent observe feasibility or capability information?
5. Does each agent observe other robots?
6. Does observation support variable-size viewpoint sets, or is it fixed-size/flattened?
7. Is the observation sufficient to choose a valid next viewpoint?
8. Does training observation match evaluation observation?

Do not change observation code.

---

### 6.10 Runtime evidence from existing scripts, if possible

If existing scripts already expose enough information without code changes, run a very small read-only command.

Examples for baseline only, if appropriate:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver nearest --num_envs 1 --num_episodes_per_env 1 --max_steps_per_episode 20 --headless

D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python scripts\environments\evaluate_scan_assignment.py --task Isaac-Scan-Mobile-Manipulator-Direct-v0 --solver greedy --num_envs 1 --num_episodes_per_env 1 --max_steps_per_episode 20 --headless
```

Only run an RL playback/evaluation command if an existing script supports it and the command can be very short. Do not run long training.

If runtime values such as RL `assignment`, `valid`, `action_norm`, or `dist_decrease` are not exposed by existing scripts, document:

```text
Not observable without adding diagnostic instrumentation.
```

Then propose a future minimal instrumentation task, but do not implement it.

---

## 7. Failure cases to classify

At the end, classify the most likely failure mode using this list. More than one may apply.

```text
Case A:
RL assignments are mostly invalid and would be converted to zero actions.

Case B:
RL assignments are valid, but controller actions are near zero.

Case C:
RL assignments are valid and controller actions are nonzero, but env.step produces little or no actual movement.

Case D:
RL assignments are valid and robots move, but distance to assigned viewpoints does not decrease.

Case E:
RL assignments are valid and robots move toward viewpoints, but coverage is not triggered.

Case F:
RL evaluation/training does not use assignment_controller at all.

Case G:
RL eval is stochastic and high-entropy, causing unstable assignment selection.

Case H:
RL repeatedly assigns duplicate viewpoints to multiple robots.

Case I:
RL repeatedly assigns already covered viewpoints.

Case J:
RL assigns infeasible viewpoints to heterogeneous robots.

Case K:
The read-only inspection cannot determine the runtime failure because required tensors are not logged.
```

For each selected case, provide:

```text
confidence: high / medium / low
evidence:
missing evidence:
recommended next task:
```

---

## 8. Required final report structure

Create a Markdown report with this structure:

```markdown
# RL Assignment-to-Motion Pipeline Diagnostic Report

## 1. Executive summary

- Most likely failure case(s):
- Confidence:
- Main evidence:
- What could not be verified without code changes:

## 2. Repository state

- Initial `git status --short`:
- Final `git status --short`:
- Files modified:
- Files created:

## 3. Commands run

| Command | Purpose | Result |
|---|---|---|

## 4. Pipeline map

```text
RL checkpoint -> policy -> raw action -> decode -> assignment -> controller -> env.step -> coverage
```

Explain the actual pipeline found in the code.

## 5. Checkpoint and eval mode

## 6. RL action semantics

## 7. Whether RL calls assignment_controller

## 8. Assignment validity and zero-action behavior

## 9. Action mask / feasibility mask usage

## 10. Baseline vs RL pipeline comparison

| Pipeline stage | nearest/greedy | RL | Same or different? | Evidence |
|---|---|---|---|---|

## 11. Movement and coverage semantics

## 12. Reward and learning signal inspection

## 13. Observation content inspection

## 14. Failure-case classification

| Case | Applies? | Confidence | Evidence | Missing evidence |
|---|---|---|---|---|

## 15. Minimal future diagnostic instrumentation, if needed

Only list future changes here. Do not implement them in this task.

Suggested future runtime metrics may include:

- raw RL action
- decoded assignment
- `in_range`
- `target_covered`
- `target_feasible`
- `valid`
- action norm
- commanded base/scanner movement
- actual base/scanner movement
- distance-to-assigned-viewpoint decrease
- newly covered viewpoint count

## 16. Conclusion
```

---

## 9. Important interpretation rules

### Rule 1: Baseline success does not automatically imply RL uses the same pipeline

`nearest` and `greedy` succeeding only proves the baseline assignment-controller-environment path works for valid handcrafted assignments. It does not prove the RL policy outputs valid assignments or even uses the same controller.

### Rule 2: Invalid assignment zeroing is a post-processing effect

If the controller converts invalid assignments to zero actions, the robot will appear not to move. However, this can only be confirmed for RL if RL actually produces assignments that pass through this controller.

### Rule 3: No runtime tensor means no definitive runtime claim

If existing code does not expose `assignment`, `valid`, or `action_norm` for RL, do not claim they are definitely invalid. Say that this is a likely hypothesis and list the missing evidence.

### Rule 4: Keep diagnosis separate from fixes

Do not implement fixes in this task. Do not add masks, logging, reward shaping, new wrappers, or new evaluation options. Put such ideas into the future instrumentation section only.

---

## 10. Expected outcome

The final deliverable is a Markdown diagnostic report that answers:

1. Does RL use high-level viewpoint assignment or direct low-level 9D continuous control?
2. Does RL call `viewpoint_assignment_to_actions`?
3. If RL uses assignments, could invalid assignments be converted to zero actions?
4. Is there evidence of deterministic vs stochastic eval behavior?
5. Are masks used before action selection, or only after action selection?
6. How does the RL pipeline differ from `nearest` and `greedy`?
7. What evidence is missing because code changes were not allowed?
8. What should be the next minimal implementation task if runtime diagnostics are required?

Stop after producing the report.
