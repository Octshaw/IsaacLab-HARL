# Phase B2-V2-PD2-R4 — Cache-Backed S0R Authority Predicate Refinement Design

Date: 2026-08-28

Starting committed HEAD: `14993dee344bade0230d2eb97b5f22171331f44a`

Classification: `PHASE-B2-V2-PD2-R4-TARGETED-RAW-TREE-HARDENING-COMPLETE-AWAITING-GPT-REVIEW`

## 1. Starting authority

This report contains the authorized `B2-V2-PD2-R4` design and its documentation-only targeted hardening revision `B2-V2-PD2-R4-TR`. R4 converted the reviewed R3 cache-backed evidence into a narrow, per-entry, implementable, fail-closed future S0R predicate. R4-TR closes only `R4-L3-PYC-01` by hardening the future primary target authority to the complete raw regular-file tree.

The starting state is:

```text
B2-D:                         GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:          GPT REVIEW PASS / CLOSED
B2-V1:                        GPT REVIEW PASS / CLOSED
B2-V2:                        STOPPED / INCOMPLETE
B2-V2-PD1:                    GPT REVIEW PASS / FROZEN
PD-A:                         CURRENT-PRODUCTION-RUNTIME-VALIDATION / FROZEN MODE
PD2 initial Junction defect:  CLOSED
PD2-R1 S0R adapter defect:    CLOSED
PD2-R2 adapter/persistence:   CLOSED
PD2-R3:                       GPT REVIEW PASS / CLOSED
R2 formal STOP:               RETAINED AS HISTORICAL VALID RESULT
S0:                           REAL PASS / VALID POSITIVE EVIDENCE
S0R complete set:             REAL PASS / DURABLE
S0R ordinary rows 1-11:       REAL PASS
S1-S6:                        NOT RUN
original VCritic boundary:    NOT REACHED
runtime/policy/learner:       BLOCKED
public route:                 DORMANT / BLOCKED
B2-R / training:              NOT AUTHORIZED
```

The frozen lifecycle, P2/Ak, proposal/effective-assignment, terminal transport, seed, complete-set A/B, D4-O, and postrun contracts are outside R4 and remain unchanged.

## 2. R3 GPT review result

The user-provided authoritative review state closes R3 with:

```text
usdrt.scenegraph: A — EXPECTED_RUNTIME_INDIRECTION / FROZEN
omni.warp.core:   A — EXPECTED_RUNTIME_INDIRECTION / FROZEN
global result:    CACHE-BACKED-AUTHORITY-RECONCILED-AS-INDIRECTION
```

R3 approved two specific current targets. It did not approve a package-search algorithm, arbitrary path normalization, normalized-manifest fallback, or Authenticode-stripping runtime rule.

GPT's targeted R4 review passed the substantive architecture, authority-category separation, L1, L2, and the L3 concept. It required one correction, `R4-L3-PYC-01`: the future acceptance tree must include the exact reviewed target's `__pycache__` and `.pyc` files rather than generically excluding them. Sections 8–15 and 19 incorporate that correction without reopening the passed architecture.

The governing translation is:

```text
R3 approval evidence:
  WHY THESE TWO SPECIFIC TARGETS WERE APPROVED

future S0R predicate:
  VERIFY THESE EXACT REVIEWED TARGETS
```

## 3. Why the R2 exact cache comparator is insufficient

The current test-only harness has one common exact comparator for all authority categories. Its frozen `CRITICAL_MANIFEST` stores each cache-backed row's distribution root under `isaacsim/extscache`, then `runtime_extension_gate()` requires the runtime-resolved root, manifest path, and raw primary-manifest SHA to equal that distribution row.

For the current reviewed Kit resolution:

```text
frozen distribution package
  != current runtime namespace path

current runtime namespace path
  = exact Windows Junction
  -> exact reviewed cache target
```

R2 therefore correctly stopped at `S0R_CRITICAL_usdrt.scenegraph` under its then-frozen comparator. The different path and raw manifest SHA were real.

The current comparator also uses `os.path.islink()`/`os.readlink()` for its per-row link fields. Those fields do not express the reviewed Windows Junction relation; the harness's separate Win32 reparse-point reader is the authoritative read-only Junction detector. Finally, the current `authority` field is recorded but does not dispatch to category-specific predicates.

R4 addresses only that expressiveness gap in design. It does not alter the historical implementation or declare R2 retroactively passing.

## 4. Authority-category separation

The future expected authority category comes only from the frozen test authority, never from runtime self-description. Dispatch is exhaustive:

| Frozen category | Future predicate | R4 effect |
|---|---|---|
| `PROJECT_LOCAL_SOURCE` | Existing exact source identity | Unchanged |
| `OFFICIAL_INSTALLED` | Existing exact installed identity | Unchanged |
| `OFFICIAL_INSTALLED_CACHE` | Exact L1 + L2 + L3 reviewed descriptor | Defined only for two frozen entries |
| missing/unknown/duplicate category | Fail closed | `PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH` |

Conceptual dispatch:

```text
if expected.authority == PROJECT_LOCAL_SOURCE:
    exact_source_identity(existing_row)
elif expected.authority == OFFICIAL_INSTALLED:
    exact_installed_identity(existing_row)
elif expected.authority == OFFICIAL_INSTALLED_CACHE:
    descriptor = exact_frozen_descriptor_lookup(expected.base_id)
    exact_logical_identity(expected, runtime, descriptor)       # L1
    exact_reviewed_indirection(runtime, descriptor)             # L2
    exact_reviewed_target_content(descriptor)                   # L3
else:
    fail_closed()
```

There is no fallback from one category to another. An `OFFICIAL_INSTALLED` row cannot use a cache descriptor, and a cache row without one of the two exact descriptor keys fails closed.

## 5. Three-layer cache-backed authority model

An `OFFICIAL_INSTALLED_CACHE` row passes only when all three layers pass:

```text
L1 — FROZEN LOGICAL IDENTITY
  exact extension/package/build identity

L2 — REVIEWED INSTALLED INDIRECTION IDENTITY
  exact selected namespace Junction and exact target

L3 — REVIEWED TARGET CONTENT IDENTITY
  exact content of the already-approved target

row PASS = L1 PASS and L2 PASS and L3 PASS
```

No layer can be skipped, downgraded to a warning, or inferred from another. A matching L3 target reached through a different namespace fails L2. A matching namespace redirected to another target fails L2. A same-version target with different bytes fails L3.

The design keeps two authority moments distinct:

- `PRELAUNCH` proves the reviewed shared-state baseline before worker startup: 45 protected hashes, 103-row fingerprint, 43/43 dual Junction oracle, critical static manifests, and startup environment.
- `S0R` proves what the live extension manager actually selected after AppLauncher returns and before environment construction.

PRELAUNCH is unchanged and is not merged into S0R. The cache descriptor cites the reviewed PRELAUNCH provenance, while S0R independently checks the selected runtime namespace and its current exact target/content.

## 6. `PROJECT_LOCAL_SOURCE` predicate

The old comparator remains exact and unchanged:

```text
base ID                     exact
actual enabled ID           exact
enabled                     true
manager version             exact
manifest version            exact
resolved project path       exact expected project-local path
manifest path               exact
raw manifest SHA-256        exact
authority category          PROJECT_LOCAL_SOURCE exact
link state/target           existing exact expectation
```

No Junction handling, CRLF/LF normalization, content-equivalence fallback, signature normalization, or cache descriptor is allowed for this category.

## 7. `OFFICIAL_INSTALLED` predicate

The old installed comparator remains exact and unchanged:

```text
base ID / enabled ID / enabled state    exact
manager and manifest version            exact
resolved official installed path        exact
manifest path and raw SHA-256            exact
authority category                       OFFICIAL_INSTALLED exact
link state/target                         existing exact expectation
```

R3 supplies no authority to relax any `OFFICIAL_INSTALLED` row.

## 8. `OFFICIAL_INSTALLED_CACHE` predicate

Only the following descriptor keys are valid:

```text
usdrt.scenegraph
omni.warp.core
```

The future harness should add a separate frozen mapping such as `REVIEWED_CACHE_BACKED_AUTHORITIES_V1`. It must not rewrite the existing PD1 `CRITICAL_MANIFEST`; that manifest remains the frozen distribution/logical evidence chain.

### 8.1 L1 exact logical predicate

Required exact fields are:

- expected base ID and actual enabled ID;
- enabled state `true`;
- manager version and target primary-manifest version;
- distribution/package basename and reviewed cache-target basename;
- reviewed Kit version, build number/date, platform, configuration, Python target, Kit hash, or repository/signed-build metadata where present;
- required extension entrypoint/dependency metadata, with the raw reviewed primary manifest also protected by L3.

Any missing/unreadable/parse-failed field fails closed.

### 8.2 L2 exact indirection predicate

Required exact fields are:

- runtime manager `resolved_path` equals the descriptor's reviewed installed namespace path after only Windows syntactic normalization (absolute path, separator/case and long-path-prefix handling); no `realpath` replacement or alternative namespace search;
- the object exists and is a directory with `FILE_ATTRIBUTE_REPARSE_POINT`;
- the existing read-only Win32 detector reports `IO_REPARSE_TAG_MOUNT_POINT` (`0xA0000003`) and `is_junction=true`;
- the canonical substitute target equals the exact descriptor target;
- the exact target exists and is a directory;
- the descriptor carries D4-CI `Tier 1 / CONFIRMED_R8_CREATED` provenance and the exact reviewed `cache_db` pair.

The historical D4-CI log and cache-db provenance are descriptor-admission authority, not data to rediscover at runtime. PRELAUNCH continues to verify the frozen 103-row/cache-db/43-pair baseline. S0R does not scan `cache_db` for alternatives; it directly validates the selected namespace's Junction relation.

These all fail L2: another Junction, another `exts/3` path, the same version elsewhere, the same basename with another target, the approved target through another namespace, a symlink instead of a Junction, or an unreadable reparse point.

### 8.3 L3 exact target predicate

L3 verifies the descriptor's fixed target. It never searches the cache. Its authority is deliberately split:

```text
PD2_CACHE_TARGET_RAW_TREE_V1:
  PRIMARY EXACT ACCEPTANCE AUTHORITY

PD2_CACHE_TARGET_TREE_V1 non-generated tree:
  REQUIRED SUPPORTING FAILURE-ATTRIBUTION SUB-GUARD

Python/native subset fingerprints:
  REQUIRED SUPPORTING FAILURE-ATTRIBUTION SUB-GUARDS

raw manifest/gen and special raw-file hashes:
  REQUIRED EXPLICIT SUB-GUARDS
```

Every required guard must pass, but no supporting fingerprint can substitute for a raw-tree PASS.

#### `PD2_CACHE_TARGET_RAW_TREE_V1`

The future implementation must follow this exact algorithm:

1. Start only at the exact L2-reviewed target root. The root must exist as a regular directory and must not itself be a reparse point.
2. Enumerate each directory non-recursively. Inspect every child entry's reparse attribute **before** testing directory/file type or descending.
3. If any internal file or directory is a reparse point, stop immediately; never traverse through it.
4. Push only ordinary directories for later traversal. Directory rows and empty directories are not identity-bearing; they only delimit traversal.
5. Include every ordinary regular file without exception: primary/generated manifests, Python source, native binaries, metadata, generated files, every `__pycache__` entry, every `.pyc`, and all other regular files.
6. Reject any entry that is neither an ordinary directory nor an ordinary regular file.
7. Derive the relative path lexically beneath the exact root, replace `\` separators with `/`, and preserve the actual entry-name spelling. Do not resolve an alternative root or target.
8. Reject duplicate ordinal relative paths and Windows case-insensitive path collisions.
9. Represent `byte_length` as unsigned base-10 ASCII with no sign, grouping, padding, or leading zero except the value `0`.
10. Represent each file SHA-256 as exactly 64 lowercase hexadecimal ASCII characters over the raw file bytes.
11. Ordinal-sort relative-path rows. Path-set payload is `relative_path<LF>` for every row. Content payload is `relative_path<TAB>byte_length<TAB>raw_file_sha256<LF>` for every row. The final row also ends in LF.
12. Encode both payloads as UTF-8 without BOM and hash them with SHA-256, represented as lowercase hexadecimal.
13. Record exact regular-file count, total byte count, path-set SHA-256, content SHA-256, and algorithm ID `PD2_CACHE_TARGET_RAW_TREE_V1`.
14. Perform two complete back-to-back captures. Each capture independently re-enumerates and rehashes the target. Require the full canonical path/content row sequences and all four descriptor values to be exactly equal. Any difference or capture error is an in-capture stability failure.

This two-capture guard is the complete stability mechanism; no background watcher, filesystem snapshot framework, or Merkle-tree subsystem is introduced.

The existing `PD2_CACHE_TARGET_TREE_V1` supporting algorithm remains as previously defined: it excludes paths below `__pycache__`, then fingerprints the remaining relative paths and raw file content; Python (`.py`, `.pyi`) and native/runtime (`.dll`, `.pyd`, `.so`, `.dylib`, `.exe`, `.lib`, `.plugin`) subsets use the same canonical content-row form. These values are required for precise failure attribution, but the full raw tree is the primary acceptance authority.

The target primary and generated manifests are checked by exact raw SHA-256. Warp's two target DLL raw hashes remain explicit required sub-guards. No target difference is accepted merely because a supporting semantic/code subset still matches.

## 9. `usdrt.scenegraph` reviewed descriptor

Descriptor ID: `PD2_CACHE_TARGET_USDRT_SCENEGRAPH_7_5_1_R3_V1`.

### 9.1 L1 — frozen logical identity

| Field | Exact value | Authority source |
|---|---|---|
| authority category | `OFFICIAL_INSTALLED_CACHE` | PD1 critical manifest |
| base ID | `usdrt.scenegraph` | PD1/R3 |
| enabled ID | `usdrt.scenegraph-7.5.1` | PD1; R2 runtime evidence |
| version | `7.5.1` | PD1; R2; R3 |
| distribution basename | `usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310` | PD1/R3 |
| reviewed target basename | `usdrt.scenegraph-60ef2a9cb390fac8` | D4-CI/R3 |
| retained archive action | `usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310.zip` | D4-CI Tier 1 |
| `kitVersion` / `buildNumber` | `106.5.0+release.162521.d02c707b.gl` / same | R3 reviewed target `extension.gen.toml` |
| publish date | `1734046497` | R3 reviewed target |
| target config / Python / platform / Kit hash | `release` / `cp310` / `windows-x86_64` / `d02c707b` | R3 reviewed target |
| required dependencies | `omni.usd.libs`, `omni.gpucompute.plugins` | R3 reviewed primary manifest |
| native plugin entrypoints | `bin/usdrt.scenegraph.plugin`, `bin/usdrt.xformcache.plugin` | R3 reviewed primary manifest |

### 9.2 L2 — reviewed installed indirection

| Field | Exact value | Authority source |
|---|---|---|
| installed namespace | `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3\usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310` | R2 retained runtime path; R3 |
| object kind | Windows directory Junction; `IO_REPARSE_TAG_MOUNT_POINT=0xA0000003` | D4-CI; reviewed harness Win32 oracle |
| exact Junction target | `C:\Users\33506\AppData\Local\ov\data\exts\v2\usdrt.scenegraph-60ef2a9cb390fac8` | D4-CI row 31; R3 |
| provenance | `Tier 1 / CONFIRMED_R8_CREATED` | D4-CI exact archive/link action |
| cache-db pair | installed basename -> `usdrt.scenegraph-60ef2a9cb390fac8` | D4-CI; frozen PRELAUNCH pair inventory |
| runtime selection | installed namespace registered and started | retained R2 Kit log; R3 |

### 9.3 L3 — reviewed target content

| Field | Exact value | Runtime role / source |
|---|---|---|
| target `extension.toml` raw SHA-256 | `e155eeba2044deb2602bc229f68fe57b7f60e1f5adacc5283737488918a0d5fe` | Required runtime gate; D4-CI/R3 |
| target `extension.gen.toml` raw SHA-256 | `85e970a0ded7363ee8b605558757e0110c56347366884ee7fbd6ad05b7fa847f` | Required runtime gate; R3 reviewed target hash |
| internal reparse-point count | `0` | Required runtime gate; R4 read-only derivation on R3 target |
| raw-tree algorithm | `PD2_CACHE_TARGET_RAW_TREE_V1` | Primary exact acceptance authority; R4-TR deterministic derivative |
| raw-tree regular files / bytes | `536` / `31,105,760` | Primary exact acceptance authority; exact R3 target |
| raw-tree relative-path-set SHA-256 | `8e2047e45e5c2af50785c80c9110dde1ed96289980a561416c936d56c97b3db8` | Primary exact acceptance authority |
| raw-tree content SHA-256 | `785e278f675786a53b3160b02aeb0abb47c432f3342b6b4e2153e7b753391a43` | Primary exact acceptance authority |
| raw-tree repeated derivation | `A == B`, full canonical row sequences exact | R4-TR read-only stability evidence |
| non-generated files / bytes | `517` / `31,086,951` | Required supporting failure-attribution sub-guard |
| non-generated relative-path-set SHA-256 | `6d8c5ca45d0adb88ab5797c76200a3c2266c075eb85e510d0a08829bdcd00bb9` | Required supporting `PD2_CACHE_TARGET_TREE_V1` sub-guard |
| non-generated-content SHA-256 | `f2fb3e83b9713b17cbbee5db4bc57a1fd96661151159bf062ad518999b23407b` | Required supporting `PD2_CACHE_TARGET_TREE_V1` sub-guard |
| Python-source files / bytes | `41` / `574,044` | Required supporting failure-attribution sub-guard |
| Python-source SHA-256 | `ab00914d309ae589092d080038e8639994a278b54201fbb45299c2d034e4228f` | Required supporting failure-attribution sub-guard |
| native/runtime files / bytes | `38` / `13,705,208` | Required supporting failure-attribution sub-guard |
| native/runtime SHA-256 | `26db73bb0920fa73ef1c0f29b8f6a16f66013dd21f53d13dfa65381f53dd2c5e` | Required supporting failure-attribution sub-guard |

R3's normalized primary-manifest hash is `e155eeba...`; it proved that the frozen CRLF distribution manifest and reviewed LF target manifest are semantically identical. Future S0R does not normalize candidate manifests. It requires the target raw hash above.

## 10. `omni.warp.core` reviewed descriptor

Descriptor ID: `PD2_CACHE_TARGET_OMNI_WARP_CORE_1_5_0_R3_V1`.

### 10.1 L1 — frozen logical identity

| Field | Exact value | Authority source |
|---|---|---|
| authority category | `OFFICIAL_INSTALLED_CACHE` | PD1 critical manifest |
| base ID | `omni.warp.core` | PD1/R3 |
| enabled ID | `omni.warp.core-1.5.0` | PD1/R3 retained runtime evidence |
| version | `1.5.0` | PD1/R3 |
| distribution/installed basename | `omni.warp.core-1.5.0+wx64` | PD1/D4-CI/R3 |
| reviewed target basename | `omni.warp.core-1.5.0+wx64` | D4-CI/R3 |
| retained archive action | `omni.warp.core-1.5.0+wx64.zip` | D4-CI Tier 1 |
| `kitVersion` | `106.2.0+release.142336.833efde4.gl` | R3 reviewed target `extension.gen.toml` |
| `buildNumber` | `1.5.0+v1.5.0.5261.75544dfa.gl` | R3 reviewed target |
| publish date / platform | `1733883300` / `windows-x86_64` | R3 reviewed target |
| repository / signed-build metadata | `warp` / `1` | R3 reviewed target |
| Python entrypoints | `omni.warp.core`; `warp` at `.` with `public=true` | R3 reviewed primary manifest |

`signed=1` is frozen package-generation metadata. It does not assert that the current two target DLL files carry Authenticode signatures.

### 10.2 L2 — reviewed installed indirection

| Field | Exact value | Authority source |
|---|---|---|
| installed namespace | `C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3\omni.warp.core-1.5.0+wx64` | retained R2 Kit log; R3 |
| object kind | Windows directory Junction; `IO_REPARSE_TAG_MOUNT_POINT=0xA0000003` | D4-CI; reviewed harness Win32 oracle |
| exact Junction target | `C:\Users\33506\AppData\Local\ov\data\exts\v2\omni.warp.core-1.5.0+wx64` | D4-CI row 39; R3 |
| provenance | `Tier 1 / CONFIRMED_R8_CREATED` | D4-CI exact archive/link action |
| cache-db pair | installed basename -> same exact target basename | D4-CI; frozen PRELAUNCH pair inventory |
| runtime selection | installed namespace registered and started | retained R2 Kit log; R3 |

### 10.3 L3 — reviewed target content

| Field | Exact value | Runtime role / source |
|---|---|---|
| target `extension.toml` raw SHA-256 | `6bac2a8a0bec9061165ec9dfcd4d18f151498335a3014c949fa2b2a2dd75cf6e` | Required runtime gate; D4-CI/R3 |
| target `extension.gen.toml` raw SHA-256 | `061fe90b4c7423f7d16103c9b0ae0a0a306c2b25d80630d93da3fe2407a0268a` | Required runtime gate; R3 reviewed target hash |
| internal reparse-point count | `0` | Required runtime gate; R4 read-only derivation on R3 target |
| raw-tree algorithm | `PD2_CACHE_TARGET_RAW_TREE_V1` | Primary exact acceptance authority; R4-TR deterministic derivative |
| raw-tree regular files / bytes | `446` / `156,115,208` | Primary exact acceptance authority; exact R3 target |
| raw-tree relative-path-set SHA-256 | `183bb2674fa2cd2a34dc15b7c59f79d685453afc4b6458c19bff86daab4c7f77` | Primary exact acceptance authority |
| raw-tree content SHA-256 | `905ace881e97336901df25692a22bc3fbbfb1e7466c16daec7aaa231a443b8bb` | Primary exact acceptance authority |
| raw-tree repeated derivation | `A == B`, full canonical row sequences exact | R4-TR read-only stability evidence |
| non-generated files / bytes | `425` / `155,478,178` | Required supporting failure-attribution sub-guard |
| non-generated relative-path-set SHA-256 | `2a11e9f920076932958176641fc892165bce6c5b378927a3bd43fa9b99a5e00f` | Required supporting `PD2_CACHE_TARGET_TREE_V1` sub-guard |
| non-generated-content SHA-256 | `fad9cede98a7e59160ba330922131cc5fc4bc47bad66c3716f11459466eec609` | Required supporting `PD2_CACHE_TARGET_TREE_V1` sub-guard |
| Python-source files / bytes | `312` / `5,403,100` | Required supporting failure-attribution sub-guard |
| Python-source SHA-256 | `c0c89dc0ca65f7b1b1b15d046d06d958596a8989bf74d3929cb6933cdf8cddd4` | Required supporting failure-attribution sub-guard |
| native/runtime files / bytes | `2` / `143,626,752` | Required supporting failure-attribution sub-guard |
| native/runtime SHA-256 | `758c53a4e2491d1f7e495a6c1b66d0bdacc31a34f855703c26a3ecc72d2bf97c` | Required supporting failure-attribution sub-guard |
| target `warp/bin/warp-clang.dll` raw SHA-256 | `068c4383dda8281e73af39fa4dbdd06e3fe22b7fd03736d796b16e1dd89e17eb` | Required explicit raw-DLL gate; R3 |
| target `warp/bin/warp.dll` raw SHA-256 | `0b56f37fc74e364bde799c92dfb8f87e55e8277416e45214bd5c1b1f706af6f3` | Required explicit raw-DLL gate; R3 |

### 10.4 Historical R3 PYC evidence versus future acceptance

R3 excluded generated `.pyc`/`__pycache__` differences only while explaining why the frozen distribution and the already-reviewed targets could represent the same bounded runtime implementation. That was one historical approval decision between two known trees.

Future S0R does not repeat that equivalence analysis. It verifies the exact R3-approved target, including the target's current 19 usdrt and 21 Warp regular files beneath `__pycache__`. Adding, removing, renaming, or changing any `.pyc`/cache file changes `PD2_CACHE_TARGET_RAW_TREE_V1` and fails closed. The two authority moments are distinct.

## 11. Line-ending approval evidence versus runtime gate

For both extensions, R3 proved the frozen distribution `extension.toml` and current target `extension.toml` differ only by CRLF versus LF and normalize to identical text. That is bounded approval evidence connecting the distribution authority to the target.

Future runtime logic must not normalize a newly observed manifest and accept it. The gate compares the current target's raw bytes to the exact reviewed target raw SHA. A third raw encoding, even if normalized text matches, stops and requires a new authority review.

## 12. Archive-host evidence handling

R3 disclosed that the frozen and target `extension.gen.toml` files use different CDN hosts while retaining exact archive basename and build/target metadata.

Future S0R does not ignore or parse-away arbitrary host differences. It checks the complete reviewed target `extension.gen.toml` raw SHA. A new host, URL, field order, line ending, or other byte change fails L3. The parsed build/target fields in L1 improve failure attribution but do not weaken the raw hash.

## 13. Warp Authenticode evidence handling

R3 compared the signed frozen Warp DLLs with the unsigned current target DLLs and established exact Authenticode-normalized executable-content hashes. That comparison explains why the current target received bounded runtime-implementation approval.

It is not a future acceptance algorithm. Future S0R requires the two current target raw DLL hashes in section 10.3. It must not strip certificates from an arbitrary new DLL, compare normalized executable content, and pass it. A new raw DLL hash stops even when its normalized executable hash matches either reviewed distribution or target evidence.

The frozen distribution is signed and the reviewed current target is unsigned. R3/R4 do not claim that signature absence is globally benign or that trust/security semantics are equivalent.

## 14. Fail-closed conditions

Every condition below maps to the existing exact formal class:

```text
PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH
boundary: S0R_CRITICAL_<base_id>
```

Fail closed when:

- the authority category is missing, unknown, duplicated, or differs from the frozen expected row;
- a cache-backed base ID has no exact descriptor or more than one descriptor;
- any L1 field is absent, unreadable, unparsable, disabled, or unequal;
- runtime resolves another namespace, even when version/basename/target matches;
- the namespace is absent, not a Junction, has another reparse tag, or cannot be inspected;
- the Junction target differs, is unreadable, or does not exist as a directory;
- descriptor/provenance inputs are unavailable or PRELAUNCH did not pass;
- target enumeration is incomplete, changes during capture, contains an internal reparse point, or any required hash cannot be computed;
- the two complete raw-tree captures differ, or the raw file count/bytes/path-set/content identity differs from the descriptor;
- any `.pyc` or other file beneath `__pycache__` is added, removed, renamed, or changed;
- either target raw manifest differs or cannot be parsed as required;
- path count, byte total, path-set hash, complete content hash, Python-source hash, or native/runtime hash differs;
- either Warp target raw DLL hash differs;
- a manifest is merely normalized-equal, a DLL is merely Authenticode-normalized-equal, or a same-version/same-basename package is found elsewhere.

The gate never skips a field, warns and continues, uses the nearest match, or changes the frozen descriptor.

## 15. Future static/synthetic test matrix

These tests are designed only; none ran in R4 or R4-TR.

| ID | Synthetic/static case | Expected result |
|---|---|---|
| A | Exact reviewed usdrt L1/L2/L3 descriptor and full raw tree | PASS |
| B | usdrt namespace Junction points to another target | FAIL / frozen STOP |
| C | Same-version usdrt at another installed path | FAIL / frozen STOP |
| D | usdrt manifest is normalized-equal but raw hash is not the approved target hash | FAIL / frozen STOP |
| E | Exact reviewed Warp L1/L2/L3 descriptor, full raw tree, and exact raw DLLs | PASS |
| F | New Warp raw DLL with identical Authenticode-normalized executable content | FAIL / frozen STOP |
| G | Warp namespace Junction points to another target | FAIL / frozen STOP |
| H | Unknown or third `OFFICIAL_INSTALLED_CACHE` package | FAIL / frozen STOP |
| I | Existing `PROJECT_LOCAL_SOURCE` positive and mismatch fixtures | Behavior byte-for-byte/semantically unchanged |
| J | Existing `OFFICIAL_INSTALLED` positive and mismatch fixtures | Behavior byte-for-byte/semantically unchanged |
| K | Missing/unreadable descriptor field, manifest, target, or content hash | FAIL / frozen STOP |
| L | Approved target through another namespace | FAIL / frozen STOP |
| M | Extra/missing/changed non-generated target file | FAIL / frozen STOP |
| N | Only a `__pycache__`/`.pyc` file is added, removed, renamed, or changed | RAW_TREE mismatch / FAIL / frozen STOP |
| O | Internal target reparse point/path escape | FAIL / frozen STOP |
| P | Unknown authority category | FAIL / frozen STOP |
| Q | Exact reviewed full raw tree, including every current `.pyc`/cache file | PASS |
| R | Raw count/path/content mismatch while all semantic/supporting subsets still match | FAIL / frozen STOP |

Static guards must also prove:

- category dispatch is exhaustive and the two exact cache keys are the complete allowlist;
- no recursive cache scan, glob fallback, same-version fallback, normalized-manifest comparator, or Authenticode normalizer exists in the runtime predicate;
- `PD2_CACHE_TARGET_RAW_TREE_V1` includes every regular file and contains no `__pycache__`, `.pyc`, generated-file, metadata-file, or other regular-file exclusion;
- reparse inspection occurs before recursion, and the two complete capture row sequences must be exact;
- existing `PROJECT_LOCAL_SOURCE` and `OFFICIAL_INSTALLED` comparator code/fixtures are unchanged;
- every required exception and mismatch uses `PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH`;
- durable per-row STARTED/PASS/FAILED and complete-set evidence ordering remains unchanged.

## 16. Future implementation boundary

If separately authorized after R4 review, the next implementation may modify only:

```text
scripts/environments/
test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
```

Its bounded job is to add the separate two-entry descriptor mapping, category-aware S0R dispatch, exact Win32 Junction inspection for cache rows, primary `PD2_CACHE_TARGET_RAW_TREE_V1`, supporting `PD2_CACHE_TARGET_TREE_V1`, and static/synthetic tests.

It may not modify production, PD1, the frozen distribution manifest, package manifests/bytes, Junctions, cache mappings, the 103-row baseline, the 43-pair inventory, source hashes, lifecycle/P2/Ak/I0-I6, installed HARL, official Kit, or public admission.

Implementation/static verification does not itself authorize AppLauncher or formal PD2. A controlled formal re-entry requires an additional explicit authorization after implementation review.

## 17. Historical R2 non-retroactivity

The historical result remains:

```text
PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH
first boundary: S0R_CRITICAL_usdrt.scenegraph
```

R2 used the valid frozen exact comparator available at that time. R4 defines a future category-aware predicate based on later reviewed R3 evidence. It does not alter the R2 artifact, reinterpret its emitted evidence, or label that run PASS.

## 18. No runtime / no mutation statement

```text
formal worker:                    0
AppLauncher / SimulationApp:      0 / 0
Isaac / CUDA:                     0 / 0
HARL / VCritic / actor:           0 / 0 / 0
environment construct/reset/step: 0 / 0 / 0
I0-I6 calls:                      0
optimizer / backward:             0 / 0
training/playback/evaluation:     0 / 0 / 0
formal PD2 rerun:                 NOT RUN / NOT AUTHORIZED

production changes:               NONE
PD1/R2/R3/D4-CI changes:          NONE
PD2 harness changes:              NONE
installed HARL/I0-I6 changes:     NONE
official Kit changes:             NONE
cache package/Junction changes:   NONE
baseline/manifest changes:        NONE
commit:                           NONE
```

R4/R4-TR used only read/list/stat/hash/compare operations and documentation writes. The target-tree fingerprints in sections 9 and 10 are deterministic derivatives of the exact R3-approved targets; they do not approve new targets. R4-TR repeated each full raw-tree derivation twice, and both full canonical row sequences and descriptor tuples were exact.

Final read-only integrity evidence:

```text
protected production/framework/I0-I6/HARL/reports: 33/33 EXACT; 0 mismatches
PD2 harness SHA-256:                                77ad85ae...1697ec39 / EXACT
R3 report SHA-256:                                  787ea307...f788e136 / EXACT
official headless Kit SHA-256:                      475bb23c...e1bc795 / EXACT

usdrt RAW_TREE derivations:                         A == B == final recheck
Warp RAW_TREE derivations:                          A == B == final recheck
internal target reparse points:                     0 / 0
installed namespace Junctions/targets:              2/2 EXACT / targets exist

production / installed HARL / I0-I6:               UNCHANGED
PD1 / R3 / harness / official Kit:                  UNCHANGED
target packages / Junctions / baseline constants:  UNCHANGED
git diff --check:                                   PASS (exit 0; line-ending warnings only)
documentation trailing-whitespace lines:            0
```

## 19. Targeted review closure — `R4-L3-PYC-01`

```text
GPT issue:
  R4-L3-PYC-01

old design:
  paths beneath __pycache__ were excluded from the future acceptance tree

revised design:
  PD2_CACHE_TARGET_RAW_TREE_V1 is the primary exact authority
  and includes every regular file, including __pycache__ and .pyc

historical PYC reconciliation:
  R3 approval evidence only

future PYC/cache mutation:
  raw-tree mismatch -> fail closed
  -> PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH

supporting fingerprints:
  retained as required failure-attribution sub-guards
  and cannot replace raw-tree PASS

status:
  CLOSED
```

The substantive R4 category architecture, L1, L2, per-entry namespace/Junction authority, line-ending approval rule, archive-host handling, Warp Authenticode rule, and historical R2 result remain unchanged.

## 20. Recommended next slice

Stop after this design and await GPT independent review.

If and only if R4-TR passes GPT review and the user separately authorizes it, the next candidate is:

```text
B2-V2-PD2-R5-A
Test-Only Cache-Backed S0R Predicate Implementation
and Static/Synthetic Verification

allowed implementation:
  current test-only PD2 harness only

runtime/formal PD2:
  NOT INCLUDED; requires later explicit authorization
```

R4-TR completion means only that the two frozen R3 indirections now have a specific, implementable, fail-closed predicate design whose primary authority includes the entire reviewed regular-file tree. It does not mean the predicate is implemented, S0R runtime PASS, PD2 PASS, VCritic reached, runtime readiness, learner readiness, B2-R authorization, or training readiness.

Final state:

```text
classification:
  PHASE-B2-V2-PD2-R4-TARGETED-RAW-TREE-HARDENING-COMPLETE-AWAITING-GPT-REVIEW

PD2-R3:
  GPT REVIEW PASS / CLOSED

PD2-R4:
  TARGETED REVISION COMPLETE / AWAITING GPT REVIEW

R4-L3-PYC-01:
  CLOSED

cache-backed authority:
  RECONCILED / FROZEN

cache-backed predicate:
  DESIGNED / HARDENED / NOT IMPLEMENTED

B2-V2:
  STOPPED / INCOMPLETE

runtime/policy/learner:
  BLOCKED

public route:
  DORMANT / BLOCKED

B2-R / training:
  NOT AUTHORIZED

commit:
  NONE
```
