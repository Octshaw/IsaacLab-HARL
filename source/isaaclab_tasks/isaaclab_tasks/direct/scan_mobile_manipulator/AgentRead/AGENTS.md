# Project instructions for Codex

This repository is a Python project based on Isaac Lab / HARL.

## Environment

Use the local conda environment located at:

```text
C:\isaacenvs\isaac45_harl
```

The conda installation is located at:

```text
D:\miniconda3
```

Prefer `conda run` instead of relying on an already activated shell, because Codex may execute commands in a fresh or non-interactive shell.

Use this pattern for Python commands:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python <command>
```

If `conda` is not available from PATH, use the full conda executable path:

```powershell
D:\miniconda3\Scripts\conda.exe run -p C:\isaacenvs\isaac45_harl python <command>
```

Before running tests or scripts, verify the Python interpreter:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import sys; print(sys.executable)"
```

The expected Python executable should be under:

```text
C:\isaacenvs\isaac45_harl
```

## Testing strategy

There is no single fixed test entry point for this repository.

When modifying code, choose the smallest relevant verification command according to the changed files. Do not run full training, long simulation jobs, or GPU-heavy experiments unless explicitly requested.

Use the following order of preference.

### 1. Syntax check for changed Python files

For each changed Python file, run:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m py_compile <changed_file.py>
```

Use this when the change is local and does not require launching Isaac Lab, simulation, or training.

### 2. Import check for changed modules

If a modified file belongs to an importable module, run a lightweight import check:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -c "import <module_name>; print('import ok')"
```

Choose the module name based on the changed file. For example, if the changed file is part of a package, import the package or the specific submodule affected by the change.

### 3. Relevant pytest tests, if available

If the repository contains pytest tests related to the changed module, run only the relevant test file or test directory:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python -m pytest <relevant_test_file_or_directory>
```

Do not assume that the whole repository has a single working pytest entry point. Prefer targeted tests.

### 4. Lightweight project scripts

If there are no pytest tests for the changed code, look for lightweight validation scripts, examples, or smoke tests near the modified module.

Run only the smallest script that can verify the change.

Use this pattern:

```powershell
conda run -p C:\isaacenvs\isaac45_harl python <script_path.py>
```

Avoid commands that start long training runs, large-scale simulation, environment generation, or GPU-heavy evaluation unless explicitly requested.

### 5. If no reliable test exists

If no reliable test or lightweight check can be found, report that clearly.

In that case, at minimum:
- verify the Python interpreter,
- run `py_compile` on changed Python files when possible,
- explain why no stronger test was run.

## Development rules

- Do not create a new virtual environment.
- Do not install, remove, or upgrade packages unless explicitly requested.
- Do not modify unrelated files.
- Prefer small, local, reviewable changes.
- Preserve existing project structure and naming conventions.
- Avoid changing experiment configuration, training hyperparameters, or environment settings unless the task explicitly asks for it.
- Avoid running full Isaac Lab simulation, long training jobs, or GPU-heavy experiments unless explicitly requested.
- After making code changes, report:
  - which files were changed,
  - which verification commands were run,
  - whether the checks passed,
  - and any checks that could not be run.

## PowerShell notes

PowerShell execution policy has been configured to allow conda initialization.

Even so, prefer `conda run -p C:\isaacenvs\isaac45_harl ...` for reproducibility instead of relying on `conda activate`.

If activation is needed for manual debugging, use:

```powershell
conda activate C:\isaacenvs\isaac45_harl
```

## Long task and handoff protocol

This project may be developed across multiple Codex sessions. The available quota may not be enough to finish all requested tasks in one session.

When working on a large task, do not attempt to complete all phases at once unless explicitly requested.

Prefer the following workflow:

1. Read the task plan first.
2. Pick the smallest meaningful phase that can be completed independently.
3. Implement that phase.
4. Run the smallest relevant verification commands.
5. Update `TASK_PROGRESS.md` before stopping.
6. Report what was completed, what was tested, and what remains.

If the current session is likely to stop before the whole task is complete, pause at a clean boundary.

A clean boundary means:
- code changes are syntactically valid,
- partial implementations are not left in a confusing state,
- tests or smoke checks have been run when possible,
- `TASK_PROGRESS.md` has been updated,
- remaining work is clearly listed.

Do not start a new large phase if the previous phase has not been tested or summarized.

## Required handoff file

Maintain a file named:

```text
TASK_PROGRESS.md
```

This file is used to hand off work between Codex sessions.

Before ending a session, update `TASK_PROGRESS.md` with:

- current phase,
- completed files,
- modified files,
- newly added files,
- implementation summary,
- verification commands that were run,
- test results,
- known issues,
- unfinished tasks,
- suggested next step for the next Codex session.

The next Codex session must read `TASK_PROGRESS.md` before making changes.

The next Codex session should first verify that the previous session's changes still pass the documented checks. Only continue with new implementation after the previous changes are understood and reasonably verified.

## Stop rules for long tasks

Stop and update `TASK_PROGRESS.md` when any of the following happens:

- one planned commit/phase is completed,
- a test fails and the cause is not immediately obvious,
- the implementation requires a design decision not specified in the task,
- running further checks would require long training, GPU-heavy simulation, or GUI interaction,
- the task is becoming too large for one session,
- the repository state becomes uncertain.

When stopping, do not simply say that work is incomplete. Clearly describe:
- what is already implemented,
- what is partially implemented,
- what has not been started,
- what should be done next.

## Commit-style phase boundaries

Use the task plan's commit-style phases as default boundaries.

Recommended boundaries:

1. Assignment problem interface only.
2. Assignment controller only.
3. Baseline solvers only.
4. Headless evaluation script only.
5. GUI viewer only.

Do not mix multiple phases unless the user explicitly asks for it.

## Testing before continuing

Before starting a new phase, verify the previous phase using the commands recorded in `TASK_PROGRESS.md`.

If those checks fail, fix or report the failure before starting new functionality.


## External package / site-packages modification rules

This project depends on HARL installed inside the local conda environment:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\harl
```

Avoid modifying installed `site-packages` files by default.

When a change appears to require modifying HARL internals, first try one of the following repo-local alternatives:

* add a wrapper,
* add a shim,
* add a subclass,
* add an adapter module,
* add a project-local copy of the minimal needed logic,
* or modify the project entry scripts to route through repo-local code.

Only modify installed `site-packages` when all of the following are true:

1. the task explicitly requires it or the implementation is blocked without it;
2. a repo-local wrapper / shim / subclass is not practical;
3. the change is minimal and targeted;
4. the exact installed file path is recorded;
5. the reason for modifying `site-packages` is documented;
6. the verification commands are recorded;
7. `TASK_PROGRESS.md` is updated with a clear warning that the change is outside the git-tracked project tree.

If installed HARL files are modified, report them separately from normal project files. Include:

```text
Modified external package files:
- C:\isaacenvs\isaac45_harl\Lib\site-packages\harl\...
```

Also include a short note explaining how to reproduce or reapply the patch if the conda environment is recreated.

Do not silently modify installed packages.

## TASK_PROGRESS.md maintenance rule

`TASK_PROGRESS.md` is a concise handoff summary, not a full historical log.

Keep it focused on the current project state and the next actionable step. Do not keep appending unlimited historical details to this file.

### What `TASK_PROGRESS.md` should contain

Each update should clearly answer:

1. What is the current status?
2. What phase or task was just completed?
3. What files were changed or created?
4. What verification commands were run, and did they pass?
5. What important implementation path or architecture is currently active?
6. What remains unfinished?
7. What should the next Codex session do first?
8. What should the next Codex session avoid doing?

### Recommended structure

Use a compact structure like:

```markdown
# TASK_PROGRESS

## Current status

## Latest completed phase

## Active architecture / implementation path

## Key files

## Latest verification

## Known issues / blockers

## Do not do

## Next step

## Detailed reports / archives
```

### Length rule

As a guideline, keep `TASK_PROGRESS.md` under about 200-300 lines.

If the file becomes too long, do not keep appending to it. Instead:

1. Archive the previous full file under `AgentRead/YYYYMMDD/`, for example:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMMDD/TASK_PROGRESS_ARCHIVE_<short_description>.md
```

2. Rewrite `TASK_PROGRESS.md` as a concise current handoff summary.
3. Add the archive path under `Detailed reports / archives`.

### Daily planning and archive folder rule

All newly created plan, report, design-note, investigation, and phase-summary markdown files must be placed under a date-named folder:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMMDD/
```

Use the current local date in `YYYYMMDD` format.

Do not place new long-form plan/report documents directly under the top-level `AgentRead/` folder unless the user explicitly requests it.

The top-level `AgentRead/` folder should keep only the current concise handoff files that are meant to be read first, especially:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/TASK_PROGRESS.md
```

Every time `TASK_PROGRESS.md` is condensed, rewritten, or substantially shortened, first create a backup of the current full version under the current date folder.

Use a descriptive archive filename, for example:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMMDD/TASK_PROGRESS_ARCHIVE_BEFORE_<short_description>_YYYYMMDD.md
```

Then rewrite the top-level `TASK_PROGRESS.md` as a concise current handoff.

After creating a plan/report/archive file, add its path under the `Detailed reports / archives` section of the current `TASK_PROGRESS.md`.

Example structure:

```text
AgentRead/
  TASK_PROGRESS.md
  20260610/
    TASK_PROGRESS_ARCHIVE_BEFORE_STAGE4_PLAN_20260610.md
    STAGE4_REAL_COMPONENT_FIXEDN_EVALUATION_PLAN.md
```

When a task is documentation-only, report clearly which documentation files were created or modified, and confirm that no code, training, simulation logic, HARL files, or installed `site-packages` files were changed.

### Detailed reports

Detailed investigations, design notes, long command outputs, and phase-specific reports should be written as separate files under `AgentRead/YYYYMMDD/`, for example:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMMDD/PHASE4_ASSIGNMENT_PLAY_EVAL_REPORT.md
```

Then reference that report from `TASK_PROGRESS.md`.

### Update behavior

When finishing a task, update `TASK_PROGRESS.md` by summarizing the latest result rather than copying all previous history forward.

Do not duplicate long historical sections if they already exist in an archive or report.

Before starting a new phase, read the current `TASK_PROGRESS.md` first. If more historical detail is needed, follow the archive/report links listed there.

### Required final handoff content

Before ending a session, ensure `TASK_PROGRESS.md` includes:

* current status,
* latest completed work,
* changed files,
* verification commands and results,
* known issues,
* unfinished tasks,
* next recommended step,
* explicit constraints for the next phase,
* links or paths to detailed reports and archives.

If no code was changed, say so explicitly.

If installed `site-packages` or external package files were modified, list them separately and clearly.
