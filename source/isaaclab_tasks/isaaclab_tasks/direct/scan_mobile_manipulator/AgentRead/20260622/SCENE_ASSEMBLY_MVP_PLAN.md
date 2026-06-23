# Scene Assembly MVP Plan

Date: 2026-06-22

## Purpose

Scene Assembly MVP Phase 6S creates a stable, repeatable scene configuration before further core algorithm work. The goal is to gather scene inputs into explicit files and verify that the existing task-space proxy environment, robot config loader, scenario config, wrapper smoke, and baseline evaluator can load them without changing behavior.

## Scene Inputs Required

- Component visual asset path.
- Real-layout task-space proxy robot YAML.
- Optional robot visual USD paths as metadata.
- Scenario YAML that references the robot config, component visual asset, component proxy settings, and a legal smoke viewpoint CSV.
- Lightweight wrapper/evaluator smoke outputs.

## Current Available Assets

- Existing visual-only component OBJ:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/Model/aircraft_skin_with_frame.obj
```

- Existing fixed/default viewpoint path:

```text
builtin_fixed_12
```

- Existing synthetic smoke viewpoint CSVs:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/synthetic_smoke_n50.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/synthetic_smoke_n100.csv
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/viewpoints/synthetic_smoke_n200.csv
```

- Existing robot proxy configs:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_two_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_three_proxy.yaml
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/configs/robots/robots_four_proxy.yaml
```

## Expected File Layout

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/
  assets/scene/README.md
  configs/robots/robots_real_proxy.yaml
  configs/scenarios/real_scene_proxy_headless.yaml
  AgentRead/20260622/SCENE_ASSEMBLY_MVP_PLAN.md
```

Future optional visual assets can be staged under:

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/component/
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/scene/robots/
```

## In Scope

- Add `robots_real_proxy.yaml` with three enabled task-space proxy robots.
- Preserve optional `visual_usd_path` metadata in robot config diagnostics.
- Add scene asset README documentation.
- Add a headless scene scenario that references the real proxy robot YAML, existing visual-only component OBJ, and a legal smoke viewpoint CSV.
- Run lightweight loader, wrapper, and evaluator smokes.

## Out Of Scope

- Real robot articulation.
- IK, collision, joint limits, or raycast coverage.
- Controller math, reward logic, HARL core, training behavior, or assignment-RL evaluation.
- Final real planned viewpoint CSV validation.
- Committing large STEP, USD, mesh, or generated binary assets.
- Treating temporary or synthetic viewpoint CSVs as final benchmark data.

STEP, mesh, and USD visual assets are for scene assembly only in this phase. They do not imply physical robot behavior or coverage fidelity.

## Smoke Validation Matrix

Minimum Phase 6S checks:

```text
robots_real_proxy.yaml loader check
real_scene_proxy_headless wrapper smoke: N=50, M=3
real_scene_proxy_headless evaluator smoke: N=50, M=3, methods=random/nearest/greedy
```

Expected shapes:

```text
noop_id = N
available_actions = [1, 3, N + 1]
available_mask = [1, 3, N]
cost_matrix = [1, 3, N]
task_status = [1, N]
robot_status = [1, 3]
```

The expected output is scene-interface readiness evidence, not final algorithm-performance evidence.
