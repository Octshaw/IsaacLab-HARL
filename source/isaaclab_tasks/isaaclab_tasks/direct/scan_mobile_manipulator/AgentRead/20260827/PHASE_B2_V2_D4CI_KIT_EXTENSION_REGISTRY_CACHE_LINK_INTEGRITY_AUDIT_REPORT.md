# Phase B2-V2-D4-CI Kit Extension Registry / Cache / Link Integrity Audit

## 1. Classification

```text
classification:
  PHASE-B2-V2-D4CI-FINAL-HANDOFF-VERIFICATION-PASS

audit classification:
  PHASE-B2-V2-D4CI-KIT-REGISTRY-CACHE-LINK-INTEGRITY-AUDIT-COMPLETE-AWAITING-GPT-REVIEW

B2-V2-D4-CI:
  COMPLETE / READY FOR GPT REVIEW

core audit / final integrity verification:
  COMPLETE / PASS

cache_provenance_status:
  PARTIALLY_ATTRIBUTED

baseline_restoration_status:
  NOT_PROVABLY_RESTORABLE

future_diagnostic_contamination_risk:
  HIGH

shared_runtime_equivalence_to_pre_R8:
  NOT_ESTABLISHED

cleanup / registry mutation:
  NOT PERFORMED / NOT PERFORMED

Isaac / AppLauncher / SimulationApp:
  NOT RUN / NOT RUN / NOT RUN

CUDA / Torch CUDA / matmul / Linear:
  NOT RUN / NOT RUN / 0 / 0

MRTA / HARL / VCritic / HAPPO / I0-I6:
  NOT RUN

original B2-V2 / R8 / R variants:
  NOT RERUN

B2-R / training:
  NOT AUTHORIZED / NOT AUTHORIZED

commit:
  NONE
```

This is a bounded, evidence-driven, read-only audit of the shared Kit extension resolution state affected during D4-R R8. It is not cleanup, repair, CUDA diagnosis, experience isolation, or an authorization to continue D4-R.

## 2. Starting checkpoint and frozen phase state

- Starting repository `HEAD`: `14993dee344bade0230d2eb97b5f22171331f44a`.
- B2-D remains `REVIEW PASS / FROZEN`.
- B2-I0 through B2-I6 and B2-V1 remain `REVIEW PASS / CLOSED`.
- B2-V2 remains `STOPPED / INCOMPLETE`.
- D1 and D2 remain closed; D3 core remains frozen at `APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY`.
- D4-O remains closed. D4-R remains stopped/incomplete under the reviewed classification `PHASE-B2-V2-D4R-STOP-REVIEW-CONFIRMED-WITH-SHARED-KIT-STATE-MUTATION`.
- Runtime, policy, learner, and public learned-policy readiness remain blocked; B2-R and training remain unauthorized.

No D1/D2/D3/D4-O or lifecycle/P2/Ak/I0-I6 conclusion is reopened here. In particular, R8 did not reach CUDA and supplies no CUDA evidence.

## 3. Audit scope and authoritative evidence

Read inputs:

- `AgentRead/20260827/PHASE_B2_V2_D4R_RESTARTED_HEADLESS_EXPERIENCE_NARROW_ISOLATION_REPORT.md`
- `AgentRead/20260827/PHASE_B2_V2_D4O_SIMULATIONAPP_SHUTDOWN_OBSERVABILITY_CONTRACT_REPORT.md`
- `AgentRead/20260827/PHASE_B2_V2_D4_HEADLESS_EXPERIENCE_REMAINING_GROUP_NARROW_ISOLATION_DIAGNOSTIC_REPORT.md`
- `AgentRead/20260826/PHASE_B2_V2_D3_APPLAUNCHER_EXPERIENCE_EXTENSION_CONFIG_BOUNDARY_DIAGNOSTIC_REPORT.md`
- `AgentRead/TASK_PROGRESS.md`
- `%TEMP%\b2_v2_d4r_formal_result_20260827_a.json`
- `%TEMP%\b2_v2_d4r_static_parity_20260827_a.json`
- the evidence-related, pre-existing `%TEMP%\b2_v2_d4r_static_revalidation.json`
- bounded filesystem objects selected from the R8 paths, timestamps, cache database, manifests, and installed extension namespace
- the official headless experience and local `isaaclab` manifest, read statically

The two required top-level JSON files remain diagnostic evidence and are non-blocking. They were not removed or modified.

No complete R8 stdout/stderr file exists in the audited paths. The formal result preserves a 50-line tail out of 141 total stdout/stderr lines plus a full-stream SHA-256. Consequently, its 15 visible archive/download/link events are an exact observed subset, not proof that only 15 downloads occurred.

## 4. Audited paths

```text
USER_CACHE_ROOT:
  C:\Users\33506\AppData\Local\ov\data\exts\v2

INSTALLED_LINK_ROOT:
  C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3

FORMAL_RESULT:
  C:\Users\33506\AppData\Local\Temp\b2_v2_d4r_formal_result_20260827_a.json

STATIC_PARITY:
  C:\Users\33506\AppData\Local\Temp\b2_v2_d4r_static_parity_20260827_a.json
```

The audit did not scan the whole system drive. Candidate objects came only from the D4-R evidence and known Kit cache/resolution locations.

## 5. D4-R STOP and exact R8 startup result

R8 removed the `app.exts.folders` setting from the exact headless experience variant. Its only formal repeat produced:

```text
repeat:                    1
worker exit code:          55
elapsed:                   33.125 s
constructor returned:      false
diagnostic class:          STARTUP_FAILURE
O4 worker finally entered: yes
O5 close returned:         no
O6 process exit observed:  no
shutdown class:            UNSAFE_OR_INCONCLUSIVE_TERMINATION
CUDA reached:              no
```

R8 repeat 2 and R5/R6/R7/R4 were correctly not run. The 37 protected production/framework/HARL paths were unchanged, but those hashes did not cover the mutable Kit cache or the installed extension-resolution namespace.

## 6. R8 side-effect event timeline

Times below are UTC and correlate the formal worker clock with NTFS metadata. Filesystem time is corroborating evidence, not the sole provenance authority.

| Event | Time/evidence | Observation |
|---|---:|---|
| E0 | monotonic `56352.531`, PID `26616` | R8 worker starts. |
| E1 | monotonic `56352.609` | direct `SimulationApp` constructor entered. |
| E2 | 05:38:02–05:38:05 | three pre-existing registry indexes/locks and one URL-cache ZIP are refreshed/touched. |
| E3 | 05:38:06.951–05:38:35.020 | 43 cache package directories and 43 paired installed-namespace junctions are created in the R8 process interval. |
| E4 | visible log tail | 15 exact `download -> unpack -> creating link` sequences are preserved. |
| E5 | 05:38:35.028 | pre-existing `cache_db.json` is modified 8 ms after the final observed junction creation and now maps the 43 packages to the installed namespace. |
| E6 | log at 05:38:35 (`32,783 ms`) | dependency solving rejects registry candidate `isaaclab-4.5.22` as untrusted. |
| E7 | monotonic about `56385.5` | O3/O4 reached; constructor never returned; worker exits 55 without O5/O6. |

This chronology supports a startup-resolution side effect. It does not establish that any downloaded extension caused the previously observed cuBLAS behavior.

## 7. Exact archive actions retained in the R8 log tail

All 15 temporary archive paths named by the retained log tail are currently absent, consistent with unpack-and-remove behavior. Their unpacked package directories and junctions remain. Items 1–12 used the logged HTTPS registry host `d4i3qtqj3r0z5.cloudfront.net`; items 13–15 used the same host over HTTP.

| # | Logged archive | Extension/version |
|---:|---|---|
| 1 | `omni.physx.foundation-106.5.3+106.5.0.wx64.r.cp310.ub3f.zip` | `omni.physx.foundation` 106.5.3 |
| 2 | `omni.localcache-106.5.3+106.5.0.wx64.r.cp310.ub3f.zip` | `omni.localcache` 106.5.3 |
| 3 | `usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310.zip` | `usdrt.scenegraph` 7.5.1 |
| 4 | `omni.physx.cooking-106.5.3+106.5.0.wx64.r.cp310.ub3f.zip` | `omni.physx.cooking` 106.5.3 |
| 5 | `omni.kit.usd.layers-2.2.0+d02c707b.wx64.r.cp310.zip` | `omni.kit.usd.layers` 2.2.0 |
| 6 | `omni.physx-106.5.3+106.5.0.wx64.r.cp310.ub3f.zip` | `omni.physx` 106.5.3 |
| 7 | `omni.physx.stageupdate-106.5.3+106.5.0.wx64.r.cp310.ub3f.zip` | `omni.physx.stageupdate` 106.5.3 |
| 8 | `omni.kit.numpy.common-0.1.2+d02c707b.wx64.r.cp310.zip` | `omni.kit.numpy.common` 0.1.2 |
| 9 | `omni.isaac.dynamic_control-1.3.16+106.5.0.wx64.r.cp310.zip` | `omni.isaac.dynamic_control` 1.3.16 |
| 10 | `omni.physics.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f.zip` | `omni.physics.tensors` 106.5.3 |
| 11 | `omni.warp.core-1.5.0+wx64.zip` | `omni.warp.core` 1.5.0 |
| 12 | `omni.physx.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f.zip` | `omni.physx.tensors` 106.5.3 |
| 13 | `omni.kit.stage_template.core-1.1.22+d02c707b.zip` | `omni.kit.stage_template.core` 1.1.22 |
| 14 | `omni.kit.primitive.mesh-1.0.17+d02c707b.zip` | `omni.kit.primitive.mesh` 1.0.17 |
| 15 | `omni.kit.stage_templates-1.2.6+d02c707b.zip` | `omni.kit.stage_templates` 1.2.6 |

These 15 package/link pairs have Tier-1 provenance: exact R8 action text plus an exact current filesystem target/link match.

## 8. Cache package and installed-junction inventory

For every row below:

- `Cache package` is under `USER_CACHE_ROOT`.
- `Installed object` is the same extension/version name under `INSTALLED_LINK_ROOT`.
- the installed object is a Windows junction, its target is the listed cache package directory, and the target currently exists;
- potential extension-resolution impact is `HIGH`, because the junction directly adds an object to the installed resolution namespace;
- provenance is `CONFIRMED_R8_CREATED`.

Tier 1 (`T1`) means exact log action plus object match. Strong Tier 2 (`T2`) means the paired cache directory and junction were both created within the exact 33-second R8 interval, their manifest identity and `cache_db` mapping agree, and their creation sequence forms the prefix immediately preceding the 15 retained exact log-tail actions. Because the log prefix was not retained, T2 is not promoted to T1.

| # | Installed extension identity | Manifest version | Cache bytes | Junction creation UTC | Evidence |
|---:|---|---:|---:|---:|---|
| 1 | `omni.stats-1.0.1+d02c707b.wx64.r.cp310` | 1.0.1 | 391,250 | 05:38:06.985 | T2 |
| 2 | `omni.client-1.2.2+d02c707b.wx64.r` | 1.2.2 | 233,987 | 05:38:07.185 | T2 |
| 3 | `omni.gpu_foundation.shadercache.vulkan-1.0.0+d02c707b.wx64.r` | 1.0.0 | 26,613 | 05:38:07.367 | T2 |
| 4 | `omni.assets.plugins-0.0.0+d02c707b.wx64.r` | unspecified | 4,756,491 | 05:38:07.631 | T2 |
| 5 | `omni.gpu_foundation-0.0.0+d02c707b.wx64.r.cp310` | unspecified | 274,927,477 | 05:38:10.544 | T2 |
| 6 | `omni.kit.pipapi-0.0.0+d02c707b` | unspecified | 20,965 | 05:38:10.713 | T2 |
| 7 | `omni.kit.pip_archive-0.0.0+d02c707b.wx64.cp310` | unspecified | 111,959,297 | 05:38:14.138 | T2 |
| 8 | `omni.usd.config-1.0.5+d02c707b` | 1.0.5 | 11,187 | 05:38:14.317 | T2 |
| 9 | `omni.gpucompute.plugins-0.0.0+d02c707b.wx64.r` | unspecified | 251,887 | 05:38:14.533 | T2 |
| 10 | `omni.usd.libs-1.0.1+d02c707b.wx64.r.cp310` | 1.0.1 | 92,425,899 | 05:38:15.558 | T2 |
| 11 | `omni.kit.telemetry-0.5.1+d02c707b.wx64.r.cp310` | 0.5.1 | 4,722,435 | 05:38:15.941 | T2 |
| 12 | `omni.usd.schema.semantics-0.0.0+d02c707b.wx64.r.cp310` | unspecified | 180,712 | 05:38:16.230 | T2 |
| 13 | `omni.usd.schema.audio-0.0.0+d02c707b.wx64.r.cp310` | unspecified | 297,826 | 05:38:16.431 | T2 |
| 14 | `omni.usd.schema.physx-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 5,193,791 | 05:38:16.720 | T2 |
| 15 | `carb.audio-0.1.0+d02c707b.wx64.r.cp310` | 0.1.0 | 3,148,170 | 05:38:16.931 | T2 |
| 16 | `omni.timeline-1.0.11+d02c707b.wx64.r.cp310` | 1.0.11 | 586,489 | 05:38:17.126 | T2 |
| 17 | `omni.kit.audiodeviceenum-1.0.1+d02c707b.wx64.r.cp310` | 1.0.1 | 355,894 | 05:38:17.311 | T2 |
| 18 | `omni.usdphysics-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 22,080,316 | 05:38:17.614 | T2 |
| 19 | `omni.kit.actions.core-1.0.0+d02c707b.wx64.r.cp310` | 1.0.0 | 898,155 | 05:38:17.802 | T2 |
| 20 | `omni.usd_resolver-1.0.0+d02c707b.wx64.r.cp310` | 1.0.0 | 33,754,280 | 05:38:18.286 | T2 |
| 21 | `omni.graph.exec-0.9.4+d02c707b.wx64.r` | 0.9.4 | 3,440,800 | 05:38:18.522 | T2 |
| 22 | `omni.kit.commands-1.4.9+d02c707b.wx64.r.cp310` | 1.4.9 | 610,146 | 05:38:18.713 | T2 |
| 23 | `omni.usd.core-1.4.2+d02c707b.wx64.r` | 1.4.2 | 1,641,969 | 05:38:18.913 | T2 |
| 24 | `omni.kit.usd_undo-0.1.8+d02c707b` | 0.1.8 | 75,593 | 05:38:19.027 | T2 |
| 25 | `omni.kit.exec.core-0.13.4+d02c707b.wx64.r.cp310` | 0.13.4 | 1,315,734 | 05:38:19.341 | T2 |
| 26 | `omni.convexdecomposition-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 27,719,699 | 05:38:19.837 | T2 |
| 27 | `omni.usd-1.12.4+d02c707b.wx64.r.cp310` | 1.12.4 | 2,572,876 | 05:38:20.150 | T2 |
| 28 | `omni.kvdb-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 8,254,734 | 05:38:20.407 | T2 |
| 29 | `omni.physx.foundation-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 256,624,512 | 05:38:22.549 | T1 |
| 30 | `omni.localcache-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 6,004,639 | 05:38:23.057 | T1 |
| 31 | `usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310` | 7.5.1 | 31,086,951 | 05:38:24.176 | T1 |
| 32 | `omni.physx.cooking-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 72,134,435 | 05:38:25.195 | T1 |
| 33 | `omni.kit.usd.layers-2.2.0+d02c707b.wx64.r.cp310` | 2.2.0 | 2,172,600 | 05:38:25.559 | T1 |
| 34 | `omni.physx-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 144,617,027 | 05:38:26.615 | T1 |
| 35 | `omni.physx.stageupdate-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 6,065,953 | 05:38:27.029 | T1 |
| 36 | `omni.kit.numpy.common-0.1.2+d02c707b.wx64.r.cp310` | 0.1.2 | 189,992 | 05:38:27.211 | T1 |
| 37 | `omni.isaac.dynamic_control-1.3.16+106.5.0.wx64.r.cp310` | 1.3.16 | 4,102,502 | 05:38:31.074 | T1 |
| 38 | `omni.physics.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 32,353,824 | 05:38:31.619 | T1 |
| 39 | `omni.warp.core-1.5.0+wx64` | 1.5.0 | 155,478,178 | 05:38:34.010 | T1 |
| 40 | `omni.physx.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f` | 106.5.3 | 39,895,437 | 05:38:34.565 | T1 |
| 41 | `omni.kit.stage_template.core-1.1.22+d02c707b` | 1.1.22 | 29,761 | 05:38:34.681 | T1 |
| 42 | `omni.kit.primitive.mesh-1.0.17+d02c707b` | 1.0.17 | 1,202,822 | 05:38:34.828 | T1 |
| 43 | `omni.kit.stage_templates-1.2.6+d02c707b` | 1.2.6 | 289,980 | 05:38:35.020 | T1 |

Aggregate current size of the 43 R8-attributed cache directories is 1,354,103,285 bytes. This is an inventory fact, not cleanup authorization.

Bounded manifest SHA-256 values were recorded during the audit for all 43 package targets. They are suitable for identifying the current post-R8 objects, but they do not supply missing pre-R8 bytes and therefore do not make exact restoration provable.

## 9. Pre-existing and touched-existing objects

### 9.1 Clearly pre-existing objects

The installed namespace has 45 current top-level entries: the 43 R8-window junctions above and two regular directories created months earlier:

| Object | Type | Created UTC | Provenance | Potential impact |
|---|---|---:|---|---|
| `INSTALLED_LINK_ROOT\omni.kit.menu.file-1.1.15+d02c707b` | regular directory | 2026-05-22 09:39:53 | PREEXISTING | LOW/unchanged by observed R8 actions |
| `INSTALLED_LINK_ROOT\omni.kit.menu.edit-1.1.25+d02c707b` | regular directory | 2026-05-22 09:40:00 | PREEXISTING | LOW/unchanged by observed R8 actions |

Other clearly pre-existing cache-root entries are `index`, `urls`, two May 2026 menu-extension cache directories, and two June 2026 CAD conversion package directories. Their top-level existence predates R8. The separately classified metadata inside `index`/`urls` was touched during R8.

### 9.2 Possibly R8-touched existing metadata

These objects were created before R8 but modified in the exact startup interval. Without pre-R8 byte copies, the precise content delta is unavailable.

| Object under `USER_CACHE_ROOT` | Current bytes | Modified UTC | Current SHA-256/content | Provenance | Potential impact |
|---|---:|---:|---|---|---|
| `cache_db.json` | 10,308 | 05:38:35.028 | `48adb85c55a405d457dfb9337663079acc137c17e2e9418c98c15b2716758a24` | POSSIBLY_R8_TOUCHED_EXISTING | HIGH |
| `index\242af5a8\registry.json` | 35,750 | 05:38:03.910 | `adb577168b0366d42dae27518615219ff6e391c6570f8c7fa171d605ffb04af9` | POSSIBLY_R8_TOUCHED_EXISTING | MEDIUM/HIGH |
| `index\242af5a8\registry.lock` | 0 | 05:38:02.333 | empty | POSSIBLY_R8_TOUCHED_EXISTING | LOW |
| `index\2e8f67e3\registry.json` | 20,888 | 05:38:04.106 | `01cf86ac1e827a3d22518bf854765aaa86c25f22cf5608efbd213806eb145870` | POSSIBLY_R8_TOUCHED_EXISTING | MEDIUM/HIGH |
| `index\2e8f67e3\registry.lock` | 0 | 05:38:03.932 | empty | POSSIBLY_R8_TOUCHED_EXISTING | LOW |
| `index\f6f0b2d0\registry.json` | 21 | 05:38:05.733 | `2b369d9be82570908aaf18c31c2969dbef16c052eee1c79cd28aac53c403510f`; `{"files":{}}` | POSSIBLY_R8_TOUCHED_EXISTING | MEDIUM |
| `index\f6f0b2d0\registry.lock` | 0 | 05:38:04.122 | empty | POSSIBLY_R8_TOUCHED_EXISTING | LOW |
| `urls\d3e0...` | 46,416 | 05:38:05.818 | `0975649240b28a339827e7fd88ae9336a894de460b26029adcf71b47be5e24a1` | POSSIBLY_R8_TOUCHED_EXISTING | MEDIUM/HIGH |

The current `cache_db.json` maps all 43 R8-attributed cache packages into the `isaac45_harl` installed namespace. Its `links_since_last_prune` value is 42 even though 43 relevant mappings are present; no undocumented counter semantics are inferred.

### 9.3 Unknown provenance

No additional top-level candidate in the two bounded roots required `UNKNOWN_PROVENANCE`: the observed objects were classifiable as confirmed R8-created, pre-existing, or possibly touched existing. This is not a claim about objects outside the evidence-driven scope, and the missing R8 log prefix prevents a fully attributed audit of every individual registry write/download action.

## 10. Trust and extension-resolution chain

Static source and R8 evidence establish the following narrow chain:

1. `apps/isaaclab.python.headless.kit` normally defines `app.exts.folders` (line 154) and requests `isaaclab` plus related local extensions (lines 187–191).
2. The local `source/isaaclab/config/extension.toml` identifies local `isaaclab` version `0.36.23`.
3. The experience keeps three registries configured, `skipPublishVerification = false`, and `registryEnabled = true` (lines 90–99).
4. R8 removed `app.exts.folders`, including the local `${app}/../source` search route, without disabling the registry.
5. The refreshed registry URL-cache ZIP contains an index entry for registry candidate `isaaclab-4.5.22`, identified with `trusted: 0` and archive metadata referring to IsaacLab `v3.0.0-beta`.
6. The R8 log then reports `extension 'isaaclab-4.5.22' is untrusted`, and dependency solving/startup exits before constructor return.

Evidence therefore supports: removing `app.exts.folders` changed the extension resolution path so that registry/cache resolution was exercised and the untrusted registry candidate became relevant. It does not support: `app.exts.folders`, the registry candidate, or any downloaded extension caused the cuBLAS failure, because R8 never reached CUDA.

## 11. Pre-R8 baseline evidence and restoration feasibility

There is **no complete pre-R8 cache snapshot**.

- D3/D4/D4-O/D4-R protected manifests excluded the user extension cache and installed extension namespace.
- Earlier enabled-extension lists and hashes document extensions used by valid runs, but not the complete byte state of these mutable roots.
- Current NTFS times, paired junction targets, manifests, `cache_db`, and the retained log tail strongly attribute the 43 current pairs to R8.
- No pre-R8 byte copies exist for the eight touched-existing metadata objects.
- The exact stdout prefix containing the first 28 download/link actions was not retained.

Therefore:

```text
cache_provenance_status:
  PARTIALLY_ATTRIBUTED

baseline_restoration_status:
  NOT_PROVABLY_RESTORABLE
```

Deleting the 43 bounded junctions and cache targets would not prove restoration. It could leave stale or historically different registry indexes and `cache_db`, and there is no authoritative pre-R8 content with which to restore those files. No cleanup trial is justified by this audit.

## 12. Shared-state layer matrix

| State layer | D4-CI finding | Evidence/qualification |
|---|---|---|
| Git repository protected source | UNCHANGED | D4-R 37/37 post-hashes rechecked; no mismatch. |
| Installed HARL source | UNCHANGED | Included in protected set; no D4-CI write. |
| Official `.kit` files | UNCHANGED | R8 used a temporary variant; official source remains unchanged. |
| Installed extension source contents | NO protected-source mutation observed | Distinct from namespace mutation. |
| Installed extension namespace | MUTATED BY R8 | 43 current junctions created in the R8 interval and targeting the user cache. |
| Kit user extension cache | MUTATED BY R8 / PARTIALLY ATTRIBUTED | 43 confirmed package directories; aggregate 1.354 GB. |
| Registry/cache metadata | POSSIBLY R8-TOUCHED EXISTING | eight pre-existing objects modified during R8; no pre-R8 bytes. |
| `%TEMP%` evidence | PRESENT / NON-BLOCKING | required formal/static JSON retained; not removed. |
| Whole Kit/Isaac runtime equivalence | NOT ESTABLISHED | mutable resolution layers were outside prior protected hashes. |

The statement “37/37 protected files unchanged” must not be rewritten as “the installed extension area/environment was unchanged.”

## 13. Future diagnostic contamination assessment

```text
future_diagnostic_contamination_risk:
  HIGH

shared_runtime_equivalence_to_pre_R8:
  NOT_ESTABLISHED
```

The risk is high because 43 new junctions now directly occupy the installed extension-resolution namespace, while cache database and registry indexes were refreshed. A later startup can potentially select a cached path/version or avoid/repeat a registry action differently from pre-R8. This is a resolution-path risk assessment, not proof that a later run will differ.

Consequently, R5/R6/R7/R4 or any further Isaac startup diagnostic in this shared state cannot automatically claim pre-R8 equivalence. Under the task decision rule:

```text
NO FURTHER ISAAC STARTUP DIAGNOSTICS IN CURRENT SHARED STATE
until a reviewed remediation or isolation path is authorized.
```

## 14. Cleanup eligibility

```text
precise cleanup scope identified:
  PARTIAL — 43 paired junctions/cache targets are mechanically bounded

exact baseline restore eligibility:
  NOT ELIGIBLE

B2-V2-D4-CLEAN recommendation:
  NOT RECOMMENDED FROM CURRENT EVIDENCE

cleanup performed:
  NO
```

The missing pre-R8 metadata bytes are decisive. A mechanically precise removal list is not the same as an exact restoration plan. Cleanup, cache redirection, registry changes, junction reconstruction, and post-cleanup startup all require a separately reviewed authorization.

## 15. Future options (assessment only)

| Option | Benefit | Risk / scope impact | Evidence required before authorization | Current assessment |
|---|---|---|---|---|
| A — precise cleanup/restore | Could remove the 43 attributed pairs and reclaim the shared namespace/cache footprint. | May delete shared packages while leaving inconsistent or non-baseline `cache_db`/indexes; cannot reconstruct eight pre-R8 metadata objects. | Authoritative pre-R8 metadata copies or another validated restoration authority; reviewed exact object/action manifest. | **Not eligible / not recommended.** |
| B — isolated diagnostic cache and extension-resolution state | Prevents further contamination of the current shared environment and can establish a controlled baseline. | Requires a separately designed, supported isolation configuration; a divergent path could weaken comparison with production. | Officially supported cache/registry/path isolation mechanisms, exact path/version parity, and external safe-shutdown controls. | Viable only as a new design slice if root-cause bisection remains necessary. |
| C — clean cloned/new Isaac environment for diagnostics only | Strongest separation and repeatability; preserves current evidence. | Storage/time cost; package and driver/runtime equivalence must be frozen and proven. | Reproducible environment manifest, exact Isaac/Torch/HARL/version parity, isolated cache and no production route mutation. | Preferred over further R variants in the contaminated shared environment if forensics is still justified. |
| D — stop extension isolation; move to reviewed production-startup validation | Returns effort to Lifecycle-aware Dynamic MRTA. D2 already freezes that train/play entrypoints use pre-App CUDA/cuBLAS initialization behavior different from the failing V2 harness order. | Root cause remains unresolved; a production startup-path validation/workaround cannot be assumed safe or correct and needs its own review. | A narrow design proving semantic relevance, no hidden production mutation, bounded real verification, and explicit authorization. | Strongest engineering-relevance candidate; assessment only, not authorization. |

## 16. Engineering relevance and recommended next decision

The accumulated valid evidence already places the B2-V2 failure below the MRTA/HARL semantic layer: plain cuBLAS behavior changes at the AppLauncher/experience/startup-order boundary before the intended actor or physical learned-policy step is reached. Continuing to identify a single Kit extension or setting would be platform forensics, not lifecycle-aware MRTA implementation.

Recommended review decision:

1. Do not continue R variants in the current shared environment.
2. Do not authorize D4-CLEAN from this evidence.
3. Prefer Option D: first design a reviewed production-startup-path validation slice using the already frozen D2 ordering observation, without yet deploying a workaround.
4. If the independent reviewer determines single-extension root-cause isolation is still essential, use Option B or C under a new authorization; Option C provides the clearest separation.

This recommendation does not activate the public route, retry B2-V2, or authorize B2-R/training.

## 17. Protected hashes and D4-CI mutation accounting

Before documentation edits:

```text
D4-R protected set:
  37/37 current hashes equal formal D4-R post-hashes

D4-R harness SHA-256:
  273b8fa0075a2d018540f67a57a35fb31f4f7065e4436d971f0c5cae943381a7

D4-R report SHA-256:
  3b484564f09a02fed890d7a856641d2702b6eecd907208d0121582770283d922

bounded shared-state fingerprint before D4-CI documentation:
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
```

The bounded shared-state fingerprint covers 103 inventory rows: 45 installed-root objects, 50 cache-root objects, and 8 metadata records. It is an audit comparison fingerprint, not a pre-R8 baseline.

D4-CI authorized writes are limited to this report and `AgentRead/TASK_PROGRESS.md`. No helper was added.

Final handoff verification after documentation writes:

```text
final protected hashes:
  37/37 unchanged; mismatch count 0

final D4-R harness SHA-256:
  273b8fa0075a2d018540f67a57a35fb31f4f7065e4436d971f0c5cae943381a7
  EXACT MATCH

final D4-R report SHA-256:
  3b484564f09a02fed890d7a856641d2702b6eecd907208d0121582770283d922
  EXACT MATCH

final bounded shared-state fingerprint:
  ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f
  103 rows / EXACT MATCH

D4-CI-induced shared Kit mutation:
  NONE OBSERVED

TEMP evidence:
  RETAINED / NON-BLOCKING

git diff --check:
  PASS (exit 0; existing LF-to-CRLF conversion warnings only)

final mutation accounting:
  DOCUMENTATION ONLY
```

Git status scope was reviewed. This finalization changed only this D4-CI report and `AgentRead/TASK_PROGRESS.md`; the other modified/untracked paths are the pre-existing reviewed B2-D through B2-I6/V1/V2 worktree state. No runtime, source, harness, installed-package, cache, registry, or link file was changed by D4-CI-F.

## 18. Explicit causal non-claims and non-execution statement

- No claim is made that Isaac, Kit, HARL, any extension, registry download, or `app.exts.folders` contains a cuBLAS defect.
- No claim is made that the first 28 T2 packages were seen in the retained 50-line log tail.
- No claim is made that current cache contents equal pre-R8 contents.
- No claim is made that removing the 43 pairs would restore pre-R8 behavior.
- No claim is made that D4-CI passes B2-V2 or establishes runtime/policy/learner readiness.

During D4-CI there was no package installation, cleanup, shared-cache/link mutation, registry setting change, source/HARL/official-experience change, environment-variable mutation, Isaac/AppLauncher/SimulationApp launch, CUDA operation, MRTA environment/reset/step, HARL/VCritic/HAPPO/ValueNorm/I0-I6 call, optimizer/backward, training, playback, evaluation, checkpoint action, public-route activation, B2-V2 rerun, or commit.

## 19. Final integrity checklist

- [x] D4-R protected hashes 37/37 exact.
- [x] D4-R harness hash exact.
- [x] D4-R report hash exact.
- [x] Bounded shared-state fingerprint exact (103 rows).
- [x] No D4-CI-induced Kit mutation observed.
- [x] TEMP evidence retained.
- [x] No Isaac/AppLauncher/SimulationApp.
- [x] No CUDA, allocation, matmul, or Linear.
- [x] No MRTA/HARL/I0-I6; optimizer/backward 0/0.
- [x] Original B2-V2 not rerun.
- [x] No cleanup or registry/link mutation.
- [x] `git diff --check` passed.
- [x] Git status scope reviewed.
- [x] Report pending fields resolved.
- [x] `TASK_PROGRESS.md` updated for final handoff.

## 20. Stop boundary

D4-CI ends with the integrity audit and decision above. B2-V2 remains stopped/incomplete. Any cleanup, isolation implementation, new environment, production-startup validation, Isaac run, CUDA run, R variant, B2-V2 retry, or B2-R work requires separate authorization after GPT independent review.
