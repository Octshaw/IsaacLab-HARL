# Phase B2-V2-PD2-R5-A — Cache-Backed S0R Predicate Implementation and Static Verification

Date: 2026-08-28

Starting committed HEAD: `14993dee344bade0230d2eb97b5f22171331f44a`

Classification: `PHASE-B2-V2-PD2-R5A-CACHE-BACKED-S0R-PREDICATE-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW`

## 1. Starting authority

This was the explicitly authorized test-only `B2-V2-PD2-R5-A` implementation slice. Its sole purpose was to implement the GPT-reviewed and frozen R4/R4-TR cache-backed S0R predicate in the existing PD2 harness and verify it statically, synthetically, and against the two exact reviewed targets by read-only filesystem capture.

The starting state remained:

```text
B2-D:                         GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:          GPT REVIEW PASS / CLOSED
B2-V1:                        GPT REVIEW PASS / CLOSED
B2-V2:                        STOPPED / INCOMPLETE
B2-V2-PD1:                    GPT REVIEW PASS / FROZEN
PD2-R3:                       GPT REVIEW PASS / CLOSED
PD2-R4 / R4-TR:               GPT REVIEW PASS / FROZEN
R4-L3-PYC-01:                 CLOSED
R2 historical STOP:           RETAINED
formal PD2 re-entry / R5-B:   NOT AUTHORIZED
runtime/policy/learner:       BLOCKED
public route:                 DORMANT / BLOCKED
B2-R / training:              NOT AUTHORIZED
```

## 2. R4 GPT review closure

The controlling review classification was `PHASE-B2-V2-PD2-R4TR-REVIEW-PASS`. R5-A did not redesign authority, choose new hashes, reinterpret semantic equivalence, or edit the R4 report.

The implemented primary L3 authority is exactly `PD2_CACHE_TARGET_RAW_TREE_V1`, including every ordinary regular file, every `__pycache__` member, and every `.pyc`. Existing non-generated, Python-source, native/runtime, raw manifest/generated-manifest, and Warp raw-DLL fingerprints remain mandatory supporting/sub-guards. They cannot replace the raw-tree gate.

## 3. Authorized implementation scope

Allowed and performed:

- modification of the existing test-only PD2 harness;
- `py_compile`;
- AST/static checks;
- in-memory synthetic fixtures;
- read-only Win32 Junction inspection;
- two complete read-only filesystem captures of each exact R3-reviewed target;
- this report and a concise `TASK_PROGRESS.md` update.

Not authorized and not performed:

- formal worker or formal PD2 re-entry;
- AppLauncher or SimulationApp;
- Isaac, Torch CUDA, VCritic, actor, HARL, MRTA, or environment construction;
- optimizer, backward, training, playback, evaluation, or checkpoint work;
- production, installed HARL, official Kit, manifest, Junction, cache package, registry, or baseline modification.

## 4. Files modified

Code modified:

```text
scripts/environments/
test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py
```

Documentation created or updated:

```text
AgentRead/20260828/
PHASE_B2_V2_PD2_R5A_CACHE_BACKED_S0R_PREDICATE_IMPLEMENTATION_AND_STATIC_VERIFICATION_REPORT.md

AgentRead/TASK_PROGRESS.md
```

No helper or production module was added.

## 5. Frozen descriptor constants

The harness now contains an immutable, literal-only `REVIEWED_CACHE_BACKED_AUTHORITIES_V1` mapping with exactly two keys:

```text
usdrt.scenegraph
omni.warp.core
```

The mapping is top-level and recursively protected with `MappingProxyType` values. Static inspection proves the assignment contains literal values and `MappingProxyType` construction only. It does not call tree capture, file hashing, Junction inspection, cache search, or any runtime observation to populate expected values.

The old `CRITICAL_MANIFEST` remains unchanged and separate. It continues to carry the PD1 distribution/logical rows; R5-A does not overwrite those rows with R3 target values.

## 6. Authority-category dispatch implementation

`runtime_extension_gate()` now dispatches exclusively from the frozen expected authority category:

```text
PROJECT_LOCAL_SOURCE
  -> existing exact comparator

OFFICIAL_INSTALLED
  -> existing exact comparator

OFFICIAL_INSTALLED_CACHE
  -> reviewed two-entry cache-backed L1 + L2 + L3 predicate

missing / unknown
  -> fail closed
```

The `PROJECT_LOCAL_SOURCE` and `OFFICIAL_INSTALLED` branch retains the prior exact checks for enabled ID/state, manager and manifest versions, resolved path, manifest path/raw hash, and existing link state/target. It is not routed through the cache predicate.

A third `OFFICIAL_INSTALLED_CACHE` base ID has no descriptor and fails closed.

## 7. L1 implementation

For each cache-backed row, L1 requires exact agreement among:

- the unchanged PD1 logical row;
- the frozen reviewed R4 descriptor;
- live extension-manager enabled ID/state and manager version;
- the exact target primary-manifest version;
- parsed logical/build metadata from the exact reviewed target manifests.

The frozen usdrt checks include distribution/target basenames, required dependencies and native plugins, Kit/build version, publish date, configuration, Python target, platform, and Kit hash.

The frozen Warp checks include distribution/target basenames, two exact Python entrypoints, Kit/build version, publish date, platform, repository, and signed-build metadata.

Missing, unreadable, unparsable, or unequal required metadata fails closed. Raw manifest hashes remain separate mandatory L3 guards.

## 8. L2 Junction implementation

L2 uses the already-reviewed `inspect_windows_junction()` Win32 reader. Its source SHA-256 remains exactly:

```text
7602402aff617b69961e4d38c252787d6b093bf9a184da85c40bb4a9d15a554c
```

The predicate requires:

- runtime resolved namespace equals the exact reviewed installed namespace after Windows syntactic normalization only;
- `FILE_ATTRIBUTE_REPARSE_POINT`;
- `IO_REPARSE_TAG_MOUNT_POINT` / `0xA0000003`;
- `is_junction=true`;
- canonical substitute target equals the exact reviewed target;
- target exists and is a directory.

S0R does not invoke PowerShell. The prior PowerShell oracle remains only an independent diagnostic/prelaunch mechanism.

No realpath substitution, alternate namespace, cache scan, same-version fallback, or basename fallback exists.

## 9. L3 RAW_TREE implementation

`capture_cache_target_raw_tree()` implements the frozen algorithm:

1. begin at the exact L2 target;
2. require an ordinary non-reparse directory root;
3. enumerate each directory non-recursively;
4. inspect `st_file_attributes` and reject reparse entries before interpreting type or descending;
5. recurse only into ordinary directories;
6. include every ordinary regular file without exclusion;
7. preserve lexical entry spelling and convert separators to `/`;
8. reject ordinal duplicates and Windows case-insensitive collisions;
9. stream raw file bytes into SHA-256 and require the read byte count to equal the initial file stat;
10. ordinal-sort `(relative_path, byte_length, raw_sha256)` rows;
11. hash exact UTF-8/no-BOM path and content payloads with final LF rows.

The result carries algorithm, file count, byte count, path-set SHA-256, content SHA-256, canonical rows, and internal-reparse count.

No `__pycache__`, `.pyc`, generated, metadata, hidden, log, extension, or filename exclusion exists in the raw-tree capture.

## 10. Two-capture stability implementation

`capture_cache_target_content()` calls the raw-tree capture twice. Each call independently re-enumerates and rehashes the complete target.

PASS requires:

- canonical row sequence A exactly equals B;
- algorithm/count/bytes/path SHA/content SHA/internal-reparse count A exactly equals B.

Only after this equality is established are bounded descriptor evidence and supporting fingerprints used. The large row sequence is not copied into normal S0R summaries.

## 11. Supporting fingerprint implementation

Supporting `PD2_CACHE_TARGET_TREE_V1` evidence is derived from the exact raw rows:

- exclude only paths whose exact component is `__pycache__` for the non-generated tree;
- Python subset: `.py` and `.pyi`;
- native/runtime subset: `.dll`, `.pyd`, `.so`, `.dylib`, `.exe`, `.lib`, and `.plugin`.

The non-generated sub-guard checks count, bytes, path-set hash, and content hash. Python and native/runtime sub-guards check count, bytes, and content hash. All are exact and mandatory, but the primary full raw tree remains decisive.

## 12. Warp raw-DLL implementation

Warp additionally requires exact raw hashes:

```text
warp/bin/warp-clang.dll
  068c4383dda8281e73af39fa4dbdd06e3fe22b7fd03736d796b16e1dd89e17eb

warp/bin/warp.dll
  0b56f37fc74e364bde799c92dfb8f87e55e8277416e45214bd5c1b1f706af6f3
```

No Authenticode stripping or executable-content normalization is implemented. Any raw mismatch fails.

## 13. Fail-closed mapping

All cache-backed observation/evaluation failures map to the existing class:

```text
PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH
boundary: S0R_CRITICAL_<base_id>
```

The bounded result records `failed_layer`, `failed_field`, expected value, and safe observed value. Missing descriptor/field, read/parse/hash error, Junction mismatch, target mismatch, tree instability, raw-tree mismatch, supporting mismatch, manifest mismatch, DLL mismatch, or unknown category/package cannot warn and continue.

The ten-item formal STOP taxonomy remains exact and unchanged.

## 14. Durable evidence preservation

The existing R2 sequence remains:

```text
complete-set A/B capture and persistence
-> row STARTED
-> row PASS or FAILED
-> overall S0R PASS only after all rows pass
```

Static inspection confirmed the persistence labels remain in this order. Cache rows add bounded L1/L2/L3 evidence to the existing row DTO; they do not change complete-set or per-row lifetime semantics.

## 15. Static guards

Static verification passed all required guards:

```text
three authority categories:                 EXACT
cache allowlist:                            EXACT 2
frozen descriptor construction:             LITERAL / IMMUTABLE
runtime-generated expected descriptor:      ABSENT
raw tree includes all regular files:        PASS
reparse check before directory recursion:    PASS
two independent captures:                   PASS
canonical row sequence equality:             PASS
forbidden equivalence/search engine:          ABSENT
STOP taxonomy:                               10/10 EXACT
durable S0R ordering:                        EXACT
production warm-up copy source:              UNCHANGED
production warm-up AST equivalence:           PASS
Junction reader source/behavior boundary:     UNCHANGED / PASS
45 protected source/report hashes:            45/45 EXACT
```

The forbidden audit found no normalized-manifest acceptance, CRLF normalization acceptance, Authenticode normalizer, same-version/basename fallback, recursive alternate-package search, glob/rglob cache search, or PowerShell call in the cache predicate.

## 16. Synthetic test matrix and results

All 21 cases passed:

| ID | Case | Result |
|---|---|---|
| A | exact reviewed usdrt | PASS |
| B | usdrt wrong Junction target | expected FAIL observed |
| C | same-version usdrt alternate path | expected FAIL observed |
| D | normalized-equivalent but wrong raw manifest | expected FAIL observed |
| E | exact reviewed Warp | PASS |
| F | new raw Warp DLL hash | expected FAIL observed |
| G | Warp wrong Junction target | expected FAIL observed |
| H | third cache-backed package | expected FAIL observed |
| I | project-local positive plus mismatch regression | unchanged PASS/FAIL behavior |
| J | official-installed positive plus mismatch regression | unchanged PASS/FAIL behavior |
| K | missing required field | expected FAIL observed |
| L | approved target through another namespace | expected FAIL observed |
| M | non-generated content mismatch | expected FAIL observed |
| N1 | `.pyc` added | RAW_TREE expected FAIL observed |
| N2 | `.pyc` removed | RAW_TREE expected FAIL observed |
| N3 | `.pyc` renamed | RAW_TREE expected FAIL observed |
| N4 | `.pyc` bytes changed | RAW_TREE expected FAIL observed |
| O | internal reparse point | expected FAIL observed |
| P | unknown authority category | expected FAIL observed |
| Q | exact full reviewed raw tree | PASS |
| R | raw tree differs while supporting subsets match | expected FAIL observed |

```text
synthetic cases: 21
PASS:            21
FAIL:            0
```

These are in-memory predicate fixtures. They do not claim runtime extension-manager verification.

## 17. Real-target read-only descriptor verification

The R5-A-only entrypoint inspected both exact installed namespace Junctions and performed two complete raw-tree captures of each target. Results:

| Target | Files | Bytes | Path-set SHA-256 | Content SHA-256 | A == B | Frozen descriptor |
|---|---:|---:|---|---|---|---|
| `usdrt.scenegraph` | 536 | 31,105,760 | `8e2047e45e5c2af50785c80c9110dde1ed96289980a561416c936d56c97b3db8` | `785e278f675786a53b3160b02aeb0abb47c432f3342b6b4e2153e7b753391a43` | exact rows/descriptors | EXACT |
| `omni.warp.core` | 446 | 156,115,208 | `183bb2674fa2cd2a34dc15b7c59f79d685453afc4b6458c19bff86daab4c7f77` | `905ace881e97336901df25692a22bc3fbbfb1e7466c16daec7aaa231a443b8bb` | exact rows/descriptors | EXACT |

For both rows:

- L1 frozen metadata: PASS;
- L2 exact namespace/Junction/tag/target: PASS;
- L3 raw tree: PASS;
- raw primary/generated manifests: PASS;
- supporting fingerprints: PASS;
- Warp explicit raw DLL guards: PASS where applicable;
- internal target reparse points: 0.

This is read-only current-filesystem evidence. It is not S0R live manager evidence and is not formal PD2.

## 18. Production/startup regression integrity

The harness's copied production warm-up function source hash remains:

```text
28a85382eeca160a321b0fe54a15dc89e3ccd2af3349e13d9d09846ce5d23ce2
```

Production warm-up AST equivalence passed. Snapshot ordering, original R2 adapter tests, durable ordering, Junction-reader guards, D4-O classifier hash, current HEAD, critical static manifests, and all 45 protected source/report hashes passed.

R4, R3, R2, PD1, D4-CI, and the official headless Kit remained byte-exact at their pre-R5-A hashes.

## 19. No-runtime and no-training counters

```text
formal worker:                    0
formal PD2 executions:            0
AppLauncher / SimulationApp:      0 / 0
Isaac / Torch CUDA:               0 / 0
HARL / VCritic / actor:           0 / 0 / 0
environment construct/reset/step: 0 / 0 / 0
I0-I6 runtime calls:              0
optimizer.step / backward:        0 / 0
training/playback/evaluation:     0 / 0 / 0
checkpoint load/save:             0 / 0
public route activation:          0
```

The exact interpreter was `C:\isaacenvs\isaac45_harl\python.exe`, Python `3.10.20`.

## 20. Source integrity

Verification artifact:

```text
C:\Users\33506\AppData\Local\Temp\b2_v2_pd2_r5a_20260828.json
SHA-256: 2c860761d8f24d72e15330f90c0a14db5351c079a189dadb8820e5a838e7e675
```

Harness after implementation:

```text
SHA-256: e54d31e8b2c613fdb91d7ae0c7a71f43bd00cedf2810375fc35039eeb46cf486
```

Protected authoritative hashes before final documentation:

```text
R4:              30f9233c35d43d22e7bc50e11b61371e1d7be376a0f64c5ad75072665e211ce1
R3:              787ea307068a8223031ecdf64ab37e9a351a87461c35cf8a6a166215f788e136
R2:              843b392ab0ed81330c89c39c007d524bc1f4cb27eb8df7ba4d47a6a97ad74390
PD1:             242b782e92634d746a45b93f814b6e14286e6f46f0b85f953483924c4570fd5e
D4-CI:           ced5867e7eefdf7618a89861122562a83cc62a488ac77a0a4d0fa67109e32209
official .kit:    475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795
45 source set:    45/45 EXACT
```

`git diff --check` passed with exit code 0; Git emitted only existing LF-to-CRLF conversion warnings.

## 21. Final classification

```text
classification:
  PHASE-B2-V2-PD2-R5A-CACHE-BACKED-S0R-PREDICATE-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW

PD2-R5-A:
  IMPLEMENTATION PASS / AWAITING GPT REVIEW

cache-backed predicate:
  IMPLEMENTED / STATIC + SYNTHETIC + READ-ONLY VERIFIED
  NOT LIVE-RUNTIME VERIFIED

B2-V2:
  STOPPED / INCOMPLETE

formal PD2 re-entry / R5-B:
  NOT AUTHORIZED

S1-S6 / original VCritic boundary:
  NOT RUN / NOT REACHED

runtime / policy / learner:
  BLOCKED / BLOCKED / BLOCKED

public route:
  DORMANT / BLOCKED

B2-R / training / commit:
  NOT AUTHORIZED / NOT AUTHORIZED / NONE
```

R5-A PASS means only that the test-only frozen cache-backed S0R predicate is implemented and verified offline. It is not a live S0R PASS, PD2 PASS, B2-V2 closure, or readiness result.

## 22. Recommended next step

Stop and await GPT independent implementation review.

If and only if GPT passes R5-A and the user separately authorizes it, the next candidate is the already bounded R5-B formal runtime re-entry. Do not start it from this report alone. Do not launch AppLauncher/Isaac, run formal PD2, modify the reviewed descriptors, refresh the baseline, alter Junctions/cache packages/manifests, activate the public route, enter B2-R, train, or commit.
