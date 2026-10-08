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

Before ending a session, update `TASK_PROGRESS.md` with the current status, recent changes and verification summary, important boundaries, unfinished work, and the next step. Link the topic navigation in `REPORT_INDEX.md` and the current main report; keep detailed commands, file/interface changes, and evidence mapping in that report rather than duplicating its full inventory.

The next Codex session must read `TASK_PROGRESS.md` before making changes, then follow `REPORT_INDEX.md` to the relevant main report. Review the recorded evidence and its limits first. Rerun checks only when necessary and within the current authorization; handoff rules do not authorize runtime, historical acceptance reruns, or reopening a closed phase.

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

Before starting a new phase, review the previous phase's accepted result and relevant main report. When additional verification is necessary and authorized, use the smallest relevant documented checks; report or fix failures within that scope before continuing.

Documentation-only rule/index maintenance requires content, new-link, and scoped-diff checks, not Python tests or runtime. Previously accepted results and closed phases are not automatically rerun by this rule.


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

`TASK_PROGRESS.md` 是当前交接摘要。它只保留当前状态、最近完成事项、关键实现与验证摘要、重要边界、未完成项、下一步，以及主题索引和当前主报告链接；不持续复制全部 commit 表、历史清理明细、原始证据列表或旧阶段全文。

### What `TASK_PROGRESS.md` should contain

每次更新应回答：当前处于什么状态；最近完成什么、涉及哪些关键文件；采用了什么路径、做过什么验证及其结果；什么尚未完成或未验证；下一步是什么、不能自动做什么。详细命令、数字、失败经过和证据定位由主报告承载。

### Recommended structure

```markdown
# TASK_PROGRESS

## Current status

## Latest completed work / verification summary

## Active architecture / boundaries

## Known issues / next step

## Reports / navigation
```

`Reports / navigation`（已有文件可继续使用 `Detailed reports / archives` 标题）优先链接 `REPORT_INDEX.md` 和当前主报告；必要时保留相关交接归档，不为每个新文件追加入口。

### Length rule

约 200–300 行是交接摘要的整理参考，不是省略关键事实的硬性限制。若确需大幅压缩、重写或显著缩短 `TASK_PROGRESS.md`，先在当日本地日期目录保存一份原文完整、字节一致的归档，再整理并链接该归档，例如：

```text
AgentRead/YYYYMM/YYYYMMDD/TASK_PROGRESS_ARCHIVE_BEFORE_<topic>_YYYYMMDD.md
```

小范围状态更新无需每次生成全量备份。没有重写授权时，保留既有历史段落，本轮只更新必要状态和导航。

### Monthly-grouped daily planning and archive folder rule

新建的主报告、必要设计说明、调查/阶段说明和交接归档仍使用：

```text
source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/AgentRead/YYYYMM/YYYYMMDD/
```

按执行机器的本地日期确定 `YYYYMMDD`，取前六位为 `YYYYMM`；先有月份目录，再有日期目录，不退回单层日期结构。此规则适用于人类可读文档，**不表示所有任务产物都放入 AgentRead**。报告直接展示所需的少量图片可随文档保留，但不由此引入整套运行数据。

AgentRead 顶层允许保留三个阅读/规则入口：

```text
AgentRead/
  AGENTS.md
  TASK_PROGRESS.md
  REPORT_INDEX.md
  YYYYMM/
    YYYYMMDD/
      <MAIN_REPORT>.md
      <necessary_design_or_handoff_archive>.md
```

长篇主报告放在月/日目录。后续新增默认遵守下述用途分工；已存在的混放文件保持原位，按需另行处理，不追溯批量迁移。

### Detailed reports — Markdown 主报告优先

需要正式报告的独立任务，原则上一份 Markdown 主报告。用户仅阅读正文应能理解：

- 本次目标、范围、重要前提，以及推荐或实际采用方案和理由；
- 主要实现变化、关键文件与接口；
- 做过哪些验证、配置与关键数字；涉及运行时的工作目录、解释器、关键参数及完整命令；
- 发生过的失败、修复与重试；
- 已确认事实、推断、未验证能力和范围外事项的区别；
- 下一步及确实需要用户决定的问题。

路径可用明确定义的缩写，但不能让读者到多个文件拼接执行命令。不能只写“PASS，详见 result.json”；数字、失败原因、关键差异和结论边界必须写进正文。报告应自足，不复制整份源码、完整日志、逐步张量、大量重复 JSON 或无关环境信息；复杂任务可展开，不用硬性篇幅限制省略关键事实。

小修补、重试和排版修正优先更新同一主报告，保留必要的“失败 → 修复 → 重测”摘要，不抹掉失败历史。独立方案评估与后续实施验证可以分别成文。已审阅报告的历史结论不得被后来的结果无说明覆盖；后续变化使用新任务报告或明确勘误说明。

改标题、修链接、文档规则与索引维护等小任务，在 TASK_PROGRESS 和最终回复说明即可，不强制另写长报告或专门验收报告。

### Auxiliary evidence — 主报告与原始事实

主报告是阅读入口；原始日志、机器可读结果、源码和补丁按需用于核验。发现矛盾应明确指出、核查并更正结论，不得修改原始输出来迁就报告，也不得把缺失证据补写成通过。“用户主要看 Markdown”不免除必要的源码/补丁/日志审查；只读 PASS 标题不能证明代码正确或运行真实。

正式主报告末尾设置简短的“辅助证据对应表”：

| 结论/检查项 | 文件位置 | 关键字段或定位 | 用途 |
|---|---|---|---|
| 本次需要核验的事实 | 对应文件的相对链接 | 字段、行号、阶段或符号 | 说明它支持什么及其限制 |

只列必要证据；没有需保留的辅助材料时说明即可，不为填表制造新文件或另一套完整 manifest/index JSON。使用清楚的相对链接；必要时明确路径以仓库根为基准。跨机器无法直接访问的原生日志路径标为本机路径，关键保留副本链接到实际位置。

报告正文的历史执行命令保留当时真实路径；未来如另行授权迁移，可以说明新位置并修复导航，不能静默把历史命令改成从未执行过的新命令。

### File placement — 按用途存放

以下路径均以仓库根为基准。后续新任务的首选分工为：

| 用途 | 首选位置与规则 |
|---|---|
| 主报告、必要设计说明、交接归档 | `T/AgentRead/YYYYMM/YYYYMMDD/`；此处 `T/` 为 `source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/` |
| 正式实现与可复用工具 | 所属源码/工具目录；例如既有 `scripts/environments/`、对应任务源码目录 |
| 可复用测试 | 按代码归属沿用已有测试组织，例如 `source/isaaclab_tasks/test/`；没有合适位置时提出一个专用位置，不新建整套测试框架 |
| 本任务运行日志、JSON、必要补丁快照 | **`logs/scan_assignment/YYYYMMDD_<topic>/attempt_01/`** |
| 确实影响复现的一次性脚本 | 同一证据任务目录的 `repro/`，即 `logs/scan_assignment/YYYYMMDD_<topic>/repro/`；主报告说明其作用 |
| 机器人资产、派生模型、扫描数据、checkpoint | 各自资产/数据/实验目录，不复制到 AgentRead |

运行证据首选目录沿用已存在的 `logs/scan_assignment` 约定（见 `scripts/environments/env_readme.md` 的 `--save_csv` 示例）。同一任务重试共用 `YYYYMMDD_<topic>` 目录，依次使用 `attempt_01`、`attempt_02`，不覆盖原始记录；同日不同任务用清楚的 topic/后缀区分。

合理例外仅限既有接口已经固定了输出位置，或 Kit 等原生日志不能直接改到首选位置：保留实际路径并在主报告解释，通过对应表关联；确需保留的最小副本放入本次证据目录。不为统一命名强改已有接口，也不同时引入多个含糊的默认目录。用户明确指定的交付位置优先，并在报告中说明。

`logs/` 下的证据及部分日志受现有忽略规则影响；报告必须说明它们是否仅在本机可取、是否随交付提供，不能暗示新 checkout 自动包含。需要外部审阅时再提供与问题相关的最小材料，不自行修改忽略规则或提交证据。

生产代码和可复用测试不得依赖某一天 AgentRead 内的脚本才能运行。一次性临时检查不要求全部长期保存；仅在确实影响复现时保留到 `repro/`，否则不为交付额外生成脚本。测试版本、配置或未提交补丁按实际需要保留，不默认复制整个源码或为每次检查建立快照。

“默认少生成、少复制”不授权删除已有文件。历史 py/json/log/patch/ZIP 等保持原位；迁移、保留策略和清理必须另行明确范围，迁移前核对脚本路径依赖与报告引用，不能仅按扩展名搬动。已删除的 checkpoint/USD 不因导航维护而恢复。

### Topic navigation — REPORT_INDEX.md

`REPORT_INDEX.md` 是简短主题导航，不是第二份进度全文。按稳定中文主题组织，每个主题只给当前状态、最新主报告、少量必要前置/关联报告；同一报告支撑多个主题时可交叉指向相应条目，避免重复罗列。

索引不逐个列出 JSON、日志、脚本，它们由主报告的辅助证据对应表关联。不再建立全局/月度/每日三套索引，也不要求读者记住日期。早期阶段优先链接最终交接/关闭报告，不逐份展开 R 系列。

当前状态以用户/GPT最新审阅结论和明确授权边界为准，同时说明旧报告保留当时历史状态；不得把索引状态更新当成实施或运行授权。

### Update behavior

结束任务时只将当前结果摘要写入 TASK_PROGRESS，并维护相关主题条目的最新主报告和必要关联。不要将每份计划、证据或文件都加入交接，也不持续复制全部 commit 表、清理明细和旧阶段记录。本轮若只做小范围更新，不借机全面重写历史。

开始下一任务先读 TASK_PROGRESS，再由 REPORT_INDEX 进入相关主报告，按需核对对应源码/证据。规则/索引维护只检查条款是否冲突或重复、本次新增/修改导航链接是否指向实际文档，以及本轮文档差异是否在范围内；不要求全目录链接审计、旧raw evidence修复、历史验收或runtime。

### Required final handoff content — 最小交付

最终回复优先给主报告位置、主要结论和重要未完成项；辅助文件通过主报告定位，不默认铺开全部路径。文档规则/索引维护没有新主报告时，链接实际更新的文档并简述结果即可。

不默认生成完整ZIP、多个重复汇总JSON、全仓库哈希清单、ledger、全目录链接扫描或独立验收报告。外部审阅、转交或复现确有需要时，提供与具体问题相关的最小补充；不能承诺任何任务仅一份MD就足以审查源码正确性或运行真实性。

交接应准确区分本次修改、已运行验证、未验证项、下一步与授权边界。文档任务明确说明未改代码/资产/依赖、未运行runtime、未执行Git写操作（按实际情况记录）；如修改installed packages则按前文另列。以上整理规则不改变执行权限、项目研究边界或Phase B CLOSED状态。
