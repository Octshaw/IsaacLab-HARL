# Phase B2-V2-PD2-R3 — Cache-Backed Critical Extension Authority Reconciliation

Date: 2026-08-28

Starting committed HEAD: `14993dee344bade0230d2eb97b5f22171331f44a`

Classification: `PHASE-B2-V2-PD2-R3-CACHE-BACKED-AUTHORITY-RECONCILED-AS-INDIRECTION-AWAITING-GPT-REVIEW`

## 1. Scope and authority

This was the authorized read-only/design-evidence slice `B2-V2-PD2-R3`. It reconciled every PD1 `OFFICIAL_INSTALLED_CACHE` critical-extension row against the current installed namespace, D4-CI cache/Junction provenance, package content, and retained R2 Kit evidence.

The governing principle was **classify, do not repair**. This slice did not change the PD1 manifest, PD2 harness, installed namespace, Junctions, package bytes, production code, HARL, Isaac, or any frozen lifecycle contract. It did not launch AppLauncher/Isaac, run CUDA/HARL, or rerun formal PD2.

The frozen R2 result remains historically and procedurally valid:

```text
PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH
first boundary: S0R_CRITICAL_usdrt.scenegraph
```

R3 asks a narrower authority question: whether a current runtime path different from the frozen distribution path is a provenance-backed indirection to the same reviewed extension implementation, a distinct selected package, or unresolved.

## 2. Starting state

```text
B2-D:                         REVIEW PASS / FROZEN
B2-I0 through B2-I6:          REVIEW PASS / CLOSED
B2-V1:                        GPT REVIEW PASS / CLOSED
B2-V2:                        STOPPED / INCOMPLETE
B2-V2-PD2-R2 formal stop:     RETAINED
runtime/policy/learner ready: BLOCKED
public route:                 DORMANT / BLOCKED
B2-R / training:              NOT AUTHORIZED
```

The R2 worker had passed PRELAUNCH, S0, complete-set durability, and the first eleven critical rows. It stopped on row 12 because `usdrt.scenegraph` resolved through the installed `omni/data/Kit/.../exts/3` namespace rather than the frozen `isaacsim/extscache` directory, and the raw manifest hashes differed.

## 3. Classification model

Each `OFFICIAL_INSTALLED_CACHE` entry was assigned exactly one class:

- **A — `EXPECTED_RUNTIME_INDIRECTION`**: the current runtime path is a provenance-backed cache/install indirection to the reviewed logical extension and its current runtime implementation is boundedly equivalent to the frozen package.
- **B — `DISTINCT_BUT_CURRENTLY_SELECTED_PACKAGE`**: Kit currently selects a genuinely distinct package/implementation, requiring authority-model revision.
- **C — `UNRESOLVED_OR_AMBIGUOUS`**: the available evidence cannot establish either A or B.

Class A does not mean raw path equality, raw directory-fingerprint equality, or permission to normalize arbitrary differences. It requires an explicit link/provenance chain plus reviewed identity, metadata, source, and runtime-content evidence.

## 4. Sources audited

The audit covered:

- PD1 critical-extension authority rows and the frozen manifest expectations;
- the current test-only PD2 harness, without changing it;
- R2 S0R persisted evidence and retained Kit log;
- the D4-CI report, exact link inventory, cache provenance, and retained archive actions;
- `apps/isaaclab.python.headless.kit` and the AppLauncher extension-search setup;
- both current installed namespace Junctions and their exact targets;
- both frozen and target `config/extension.toml` and `config/extension.gen.toml` files;
- complete package path/byte inventories, Python sources, native files, and generated `.pyc` artifacts;
- PE/Authenticode-normalized evidence for the two differing Warp DLLs.

No historical report, harness, application file, package, Junction, or manifest was modified.

## 5. Complete `OFFICIAL_INSTALLED_CACHE` inventory

PD1 contains exactly two `OFFICIAL_INSTALLED_CACHE` entries. No entry was omitted.

| Extension | Frozen logical ID/version | Frozen distribution path | Current installed namespace | Current exact Junction target | Result |
|---|---|---|---|---|---|
| `usdrt.scenegraph` | `usdrt.scenegraph-7.5.1` / `7.5.1` | `C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\extscache\usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310` | `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3\usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310` | `C:\Users\33506\AppData\Local\ov\data\exts\v2\usdrt.scenegraph-60ef2a9cb390fac8` | **A** |
| `omni.warp.core` | `omni.warp.core-1.5.0` / `1.5.0` | `C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim\extscache\omni.warp.core-1.5.0+wx64` | `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3\omni.warp.core-1.5.0+wx64` | `C:\Users\33506\AppData\Local\ov\data\exts\v2\omni.warp.core-1.5.0+wx64` | **A** |

Both installed namespace objects are existing Windows Junctions; both targets exist. D4-CI records both as Tier-1 exact archive/link events. `cache_db.json` maps each target cache key to the exact installed namespace path.

## 6. Search order and current runtime selection

The official headless experience explicitly depends on both extensions and exposes the Isaac extension-cache folders. AppLauncher additionally registers the Isaac extension and app directories.

The retained R2 Kit log is:

```text
C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\logs\Kit\Isaac-Sim\4.5\kit_20260828_091110.log
size:   351511 bytes
SHA256: 3a2843f247ca042bb0af5f8b00cdcce55b530666fd6aa4ebe2d54490570e17aa
```

That log registers the installed namespace `.../omni/data/Kit/Isaac-Sim/4.5/exts/3` before the frozen `.../isaacsim/extscache` location. It records duplicate logical IDs from both locations, then starts `usdrt.scenegraph` and `omni.warp.core` from the installed namespace/Junction paths. Therefore, for this retained R2 run, both current runtime selections are known exactly; they are not inferred solely from directory existence.

This is observed current-run ordering, not a claim about every possible Kit search-order configuration.

## 7. `usdrt.scenegraph` reconciliation

### 7.1 Identity and provenance

- Enabled ID/version: `usdrt.scenegraph-7.5.1` / `7.5.1`.
- Installed namespace Junction target is exactly the D4-CI Tier-1 cache target.
- The retained R2 log registers and starts the extension from that namespace.
- The retained D4-CI archive action names the exact package archive `usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310.zip`.

### 7.2 Manifest evidence

Raw `config/extension.toml` differs:

```text
frozen size/hash: 2673 / a52a69b609100538429406619e9576e81fb1a18a279ddc40628d9fa932358818
target size/hash: 2550 / e155eeba2044deb2602bc229f68fe57b7f60e1f5adacc5283737488918a0d5fe
```

The difference is completely explained by 123 CRLF line endings in the frozen file versus 123 LF line endings in the target. Normalized text is exact, with normalized SHA-256 `e155eeba2044deb2602bc229f68fe57b7f60e1f5adacc5283737488918a0d5fe`. Package identity, dependencies, Python modules, native plugin entries, tests, and configuration are semantically identical.

`config/extension.gen.toml` differs in raw hash and by one byte. After line-ending normalization, the only structured-field difference is the `archivePath` CDN host:

```text
frozen host: d2cerybs4newgl.cloudfront.net
target host: d4i3qtqj3r0z5.cloudfront.net
```

The archive basename and all build/target metadata are exact, including Kit/build `106.5.0+release.162521.d02c707b.gl`, build date, platform, Python target, and commit tag. The host difference is retained as archive-provenance metadata; it is not erased or generalized as harmless.

### 7.3 Package content

Raw directory fingerprints differ:

```text
frozen: 540 files / 88 dirs / 31139580 bytes / 68dbed1d32fcc14830877c056b72df6216d1e16bf0fb6c153c0c3482b3566afa
target: 536 files / 86 dirs / 31105760 bytes / ff5183b77ad734e78c1e9577c4a5af1bbe1e3d63e482daf4d3d8f875693ffcee
```

The extra/differing cache objects are `.pyc` files plus the two TOML files above. Excluding generated `__pycache__`/`.pyc` artifacts, both distributions contain exactly 517 paths; only the two TOML files differ raw. All Python source and native/runtime files are byte-exact.

### 7.4 Per-entry judgment

`usdrt.scenegraph` is **A — `EXPECTED_RUNTIME_INDIRECTION`**. The different current path is an exact, provenance-backed Junction selected and started by Kit; the logical manifest is semantically exact, and the executable/source content is exact. The R2 raw path/hash comparator nevertheless correctly stopped under its frozen exact predicate.

## 8. `omni.warp.core` reconciliation

### 8.1 Identity and provenance

- Enabled ID/version: `omni.warp.core-1.5.0` / `1.5.0`.
- Installed namespace Junction target is exactly the D4-CI Tier-1 cache target.
- The retained R2 log registers and starts the extension from that namespace.
- The retained D4-CI archive action names `omni.warp.core-1.5.0+wx64.zip`.

### 8.2 Manifest evidence

Raw `config/extension.toml` differs only by 52 CRLF versus LF line endings:

```text
frozen size/hash: 1266 / 62d55511ee3d3d9e150f34c5b6196f983af8915e5cf5afe17fe97e96348408df
target size/hash: 1214 / 6bac2a8a0bec9061165ec9dfcd4d18f151498335a3014c949fa2b2a2dd75cf6e
normalized hash:  6bac2a8a0bec9061165ec9dfcd4d18f151498335a3014c949fa2b2a2dd75cf6e (both)
```

The `extension.gen.toml` structured difference is again only the archive CDN host shown above. Archive basename, package/build metadata, target OS, repository, signed-build metadata, and build timestamp are exact.

### 8.3 Package content and signed DLL disclosure

Raw directory fingerprints differ:

```text
frozen: 736 files / 63 dirs / 159237356 bytes / f9b9e8dc42b38883cb4e1b05ebbe6f49b5a4a846afcbd35802d5d68a48fe1614
target: 446 files / 45 dirs / 156115208 bytes / 26fca7a93dabaa8d1bc96e66b06dcc2ed6670d20cb51e15e1362d8cdbdb47bf0
```

The large count difference is generated `.pyc`/`__pycache__` content. Excluding those artifacts, both packages contain exactly 425 paths. Four files differ raw: the two TOMLs and two DLLs. All Python source files and all other native/runtime files are byte-exact.

The frozen DLLs carry valid NVIDIA Authenticode certificate overlays; the current cache-target DLLs are unsigned. This raw/security-packaging difference is explicitly retained:

| DLL | Frozen signed SHA-256 | Target raw SHA-256 | Authenticode executable-content hash, both |
|---|---|---|---|
| `warp-clang.dll` | `11f8229d5770d8a8ec765343881a21a4ca9d8813383973db6adb255508e157c4` | `068c4383dda8281e73af39fa4dbdd06e3fe22b7fd03736d796b16e1dd89e17eb` | `a793390e75201e951278844bdc01f59ce3e3085fd291425d3a61a31711da636c` |
| `warp.dll` | `c66b66b5a459368287b2c87a393e9e5c721e1fb3cd24029ef73256af5521974d` | `0b56f37fc74e364bde799c92dfb8f87e55e8277416e45214bd5c1b1f706af6f3` | `34ca9b6dc1daaa70f90d7adca60f7f68f003f8dc9a886f406a032cb9859edf4d` |

For both files, the target size equals the frozen PE certificate-table offset, and the frozen certificate overlay size is 9,752 bytes. Authenticode-normalized executable content—excluding the checksum field, security-directory entry, and certificate overlay—is exact. This supports bounded runtime-implementation equivalence; it does not assert that absent signatures are globally security-equivalent or acceptable for unrelated trust decisions.

### 8.4 Per-entry judgment

`omni.warp.core` is **A — `EXPECTED_RUNTIME_INDIRECTION`**. Its selected namespace is an exact provenance-backed Junction; extension/build identity and code-bearing content match the frozen distribution under the disclosed transformations. Raw package and signature identities remain different and are not hidden.

## 9. Main evidence matrix

| Predicate | `usdrt.scenegraph` | `omni.warp.core` |
|---|---|---|
| Exact current Junction and existing target | PASS | PASS |
| D4-CI per-entry provenance | Tier 1 | Tier 1 |
| `cache_db.json` namespace mapping | EXACT | EXACT |
| Retained R2 registration/start path | installed namespace | installed namespace |
| Logical ID/version | EXACT | EXACT |
| Primary manifest semantic fields | EXACT | EXACT |
| Generated metadata build/target fields | EXACT | EXACT |
| Non-generated path set | EXACT | EXACT |
| Python source | BYTE-EXACT | BYTE-EXACT |
| Native executable content | BYTE-EXACT | AUTHENTICODE-CONTENT-EXACT; raw signatures differ |
| Raw path / raw package fingerprint | DIFFERENT | DIFFERENT |
| Classification | **A** | **A** |

## 10. Global authority result

All and only the two `OFFICIAL_INSTALLED_CACHE` entries classify as A. Therefore:

```text
CACHE-BACKED-AUTHORITY-RECONCILED-AS-INDIRECTION
```

The evidence supports a three-part authority model for these reviewed cache-backed extensions:

1. frozen logical authority: extension ID, version, build/target identity, and required semantics;
2. installed indirection authority: exact installed namespace Junction, exact target, and per-entry provenance;
3. content authority: bounded semantic/source/executable-content equivalence with every accepted transformation stated explicitly.

This is not unrestricted path canonicalization and does not make all cache copies authoritative. A future row must independently satisfy the same bounded evidence requirements.

## 11. Relationship to the R2 STOP

R3 does not rewrite history or retroactively turn R2 into PASS. R2 used the frozen exact resolved-path, manifest-path, and raw-manifest-SHA predicates. The current runtime path and raw manifest hash genuinely differ, so `S0R_CRITICAL_usdrt.scenegraph` was the correct first boundary under that contract.

R3 establishes that the mismatch is authority-model expressiveness, not current evidence of a different `usdrt.scenegraph` runtime implementation. Any refinement of S0R remains a separately authorized, test-only design/implementation slice followed by independent review. The harness and critical manifest remain unchanged here.

## 12. Limits and non-claims

- Overall D4-CI cache provenance remains `PARTIALLY_ATTRIBUTED`; only these two rows have the cited Tier-1 evidence.
- Pre-R8 runtime equivalence and provable baseline restoration remain unestablished.
- Raw path, raw manifest hash, raw directory fingerprint, and Warp signature packaging are not equal.
- No claim is made that archive-host or signature differences are globally benign.
- No claim is made about packages outside the two reviewed PD1 rows.
- No claim is made that B2-V2, S1-S6, VCritic, actor, physical step, terminal transport, or any readiness gate passed.

## 13. Protected integrity

The following authoritative artifacts were treated as protected and remained unchanged during R3:

```text
apps/isaaclab.python.headless.kit
PD1 design
D4-CI report
D4-R report
PD2 R1 report
PD2 R2 report
current PD2 test-only harness
all production and installed HARL files
both installed namespace Junctions and targets
both frozen and target manifests/packages
```

Final protected SHA-256 evidence:

| Protected artifact | SHA-256 |
|---|---|
| `apps/isaaclab.python.headless.kit` | `475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795` |
| current PD2 test-only harness | `77ad85ae71ea5babfa5215b5ac621a6fa4219998f4e358e821aa696c1697ec39` |
| PD1 design | `242b782e92634d746a45b93f814b6e14286e6f46f0b85f953483924c4570fd5e` |
| D4-CI report | `ced5867e7eefdf7618a89861122562a83cc62a488ac77a0a4d0fa67109e32209` |
| D4-R report | `3b484564f09a02fed890d7a856641d2702b6eecd907208d0121582770283d922` |
| PD2 R1 report | `65d9ef7abb51740456d5fa552c6622dc2e225a374ccfb3fabc8749680124fcc0` |
| PD2 R2 report | `843b392ab0ed81330c89c39c007d524bc1f4cb27eb8df7ba4d47a6a97ad74390` |

The final read-only Junction check returned `LinkType=Junction`, the same exact targets recorded in section 5, and `target_exists=True` for both rows.

R3 created only this dated Markdown report and updated the top-level concise handoff. No cleanup, relink, baseline refresh, package write, or runtime startup occurred.

Final `git diff --check` passed with exit code 0; Git reported only existing working-tree line-ending conversion warnings. Both R3 documentation files contain zero trailing-whitespace lines after finalization.

## 14. Execution statement

```text
AppLauncher / SimulationApp / Isaac: 0 / 0 / 0
CUDA / Torch forward:               0 / 0
environment construct/reset/step:   0 / 0 / 0
HARL / VCritic / HAPPO:             0 / 0 / 0
I0-I6:                              0
optimizer / backward:               0 / 0
training/playback/evaluation:       NOT RUN
formal PD2 rerun:                   NO
production changes:                 NONE
harness/manifest/Junction changes:  NONE
installed HARL changes:             NONE
commit:                             NONE
```

All commands in R3 were read-only filesystem, metadata, hash, text/package comparison, retained-log inspection, and Git integrity commands.

## 15. Required readiness state

```text
B2-V2:             STOPPED / INCOMPLETE
runtime readiness: BLOCKED
policy readiness:  BLOCKED
learner readiness: BLOCKED
public route:      DORMANT / BLOCKED
B2-R:              NOT AUTHORIZED
training:          NOT AUTHORIZED
```

The R3 authority result is documentation/design evidence only; it does not advance any runtime or learner gate.

## 16. Recommended next decision

After GPT independent review, the narrow next candidate is a **design-only, test-only S0R authority-predicate refinement**. It should specify how the frozen logical identity, exact reviewed installed indirection, and bounded content-equivalence evidence are represented without weakening fail-closed behavior or accepting arbitrary path/hash differences.

Do not implement that refinement, refresh the baseline, edit the critical manifest, rerun formal PD2, clean shared state, or retry B2-V2 under the present authorization.

## 17. Final classification

```text
classification:
  PHASE-B2-V2-PD2-R3-CACHE-BACKED-AUTHORITY-RECONCILED-AS-INDIRECTION-AWAITING-GPT-REVIEW

per-entry result:
  usdrt.scenegraph: A — EXPECTED_RUNTIME_INDIRECTION
  omni.warp.core:   A — EXPECTED_RUNTIME_INDIRECTION

global result:
  CACHE-BACKED-AUTHORITY-RECONCILED-AS-INDIRECTION

R2 formal STOP:
  RETAINED

implementation:
  NOT STARTED

runtime/formal rerun:
  NOT RUN

production/HARL/harness changes:
  NONE

B2-V2:
  STOPPED / INCOMPLETE

B2-R / training:
  NOT AUTHORIZED

commit:
  NONE
```

Stop here and await GPT independent review.
