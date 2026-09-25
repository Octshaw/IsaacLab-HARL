# TASK_PROGRESS

Updated: 2026-08-29

Authoritative classification: `PHASE-B2-V2-PD2-R5D-TR2-TIMEOUT-CALL-IDENTITY-PASS-AWAITING-GPT-REVIEW`

## Current status

```text
committed checkpoint HEAD:         14993dee344bade0230d2eb97b5f22171331f44a
Lifecycle Runtime Backbone:        COMMITTED / CLOSED CHECKPOINT
B1W-I4-4:                          GPT REVIEW PASS / CLOSED
B2-D:                              GPT REVIEW PASS / FROZEN
B2-I0 through B2-I6:               GPT REVIEW PASS / CLOSED
B2-V1:                             GPT REVIEW PASS / CLOSED

B2-V2:                             STOPPED / INCOMPLETE
B2-V2-D1:                          GPT REVIEW PASS / CLOSED
D1 boundary:                       APP_LAUNCHER_CUDA_CONTEXT_INTERACTION
B2-V2-D2:                          GPT REVIEW PASS / CLOSED
D2 characterization:               APPLAUNCHER_TORCH_CUDA_FIRST_USE_ORDER_SENSITIVE_BEHAVIOR
B2-V2-D3 core:                     GPT REVIEW PASS / FROZEN
D3 boundary:                       APPLAUNCHER_EXPERIENCE_SUFFICIENT_BOUNDARY
B2-V2-D3 overall:                  STOPPED / INCOMPLETE
old B2-V2-D4:                      STOPPED / INCOMPLETE
B2-V2-D4-O:                        GPT REVIEW PASS / CLOSED
B2-V2-D4-R:                        STOPPED / INCOMPLETE
D4-R review:                       STOP REVIEW CONFIRMED WITH SHARED KIT STATE MUTATION
B2-V2-D4-CI:                       GPT REVIEW PASS / CLOSED
D4-CI final integrity:             PASS
B2-V2-PD1:                         GPT REVIEW PASS / FROZEN
PD1-R R1/R2/R3/R4:                 CLOSED / CLOSED / CLOSED / CLOSED
PD1-RF C1/C2/C3:                   CLOSED / CLOSED / CLOSED
PD-A:                              CURRENT-PRODUCTION-RUNTIME-VALIDATION / FROZEN MODE
B2-V2-PD2 initial:                 STOP REVIEW CONFIRMED / TEST-ONLY JUNCTION PREDICATE DEFECT
initial formal classification:     PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH / RETAINED
B2-V2-PD2-R1-A:                    JUNCTION CORRECTION PASS / FORMAL REENTRY ELIGIBLE
B2-V2-PD2-R1-B:                    GPT REVIEW PASS / CLOSED AS HISTORICAL S0R ADAPTER STOP
historical R1 classification:      PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH / RETAINED
B2-V2-PD2-R2-A:                    S0R ADAPTER CORRECTION PASS / FORMAL REENTRY ELIGIBLE
B2-V2-PD2-R2-B:                    STOPPED AT S0R_CRITICAL_usdrt.scenegraph
R2 formal classification:          PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH
R2 worker/AppLauncher/Isaac:       1 / 1 / 0
R2 environment reset/step:         0 / 0
B2-V2-PD2-R3:                      GPT REVIEW PASS / CLOSED
R3 usdrt.scenegraph:               A — EXPECTED_RUNTIME_INDIRECTION
R3 omni.warp.core:                 A — EXPECTED_RUNTIME_INDIRECTION
R3 global authority result:        CACHE-BACKED-AUTHORITY-RECONCILED-AS-INDIRECTION
B2-V2-PD2-R4:                      GPT REVIEW PASS / FROZEN
R4-L3-PYC-01:                      CLOSED
cache-backed predicate:            IMPLEMENTED / STATIC + SYNTHETIC + READ-ONLY VERIFIED
cache-backed live S0R:              PASS / R5-B REAL RUNTIME VERIFIED
B2-V2-PD2-R5-A:                    GPT REVIEW PASS / CLOSED
B2-V2-PD2-R5-B:                    HISTORICAL FORMAL STOP RETAINED
R5-B GPT review:                   STOP REVIEW CONFIRMED / TEST-ONLY S5/S6 FIXTURE CONTRACT MISMATCH
R5-B first boundary:               S6_TIME_LIMIT
R5-B classification:               PD2-STOP-TERMINAL-TRANSPORT-FAIL
R5-B S0/S0R/S1/S2/S3/S4:          GPT REVIEW PASS / REAL RUNTIME EVIDENCE
R5-B S5:                           NOT YET ADJUDICATED
R5-B terminal I4/I5a/I5b:         NOT REACHED
R5-B Snapshot B:                   NOT REACHED
R5-B shutdown/postrun:             SAFE / PASS
R5-B formal executions:            1 SUPERVISOR / 1 WORKER / 1 APPLAUNCHER
R5-B retry/repair:                 0 / 0
B2-V2-PD2-R5-C:                    GPT REVIEW PASS / FROZEN
R5C-S5-AUTHORITY-01:               CLOSED
R5C-S5-POSTSTATE-02:               CLOSED
R5-C timing/evidence contract:     FROZEN
R5-C formal runtime:               NOT AUTHORIZED / NOT RUN
B2-V2-PD2-R5-D:                    TARGETED REVISION 2 COMPLETE / AWAITING GPT REVIEW
R5-D mutation scope:               TEST-ONLY FORMAL HARNESS + DOCUMENTATION
R5-D timing fixture:               IMPLEMENTED / STATIC+SYNTHETIC PASS
R5-D early timing gate:            IMPLEMENTED / NOT RUNTIME-EXECUTED
R5-D S5 required DTO:              PRETERMINAL ONLY / IMPLEMENTED
R5-D S5 authority/adjudicator:     IMPLEMENTED / STATIC+SYNTHETIC PASS
R5-D post-return diagnostic:       SEPARATE / OPTIONAL / IMPLEMENTED
R5-D S5/S6 evidence ordering:      IMPLEMENTED / STATIC PASS
R5-D S2 evidence hardening:        IMPLEMENTED / CPU SYNTHETIC PASS
R5-D original synthetic matrix:    A-Y 25/25 PASS / RETAINED
R5D-S6-EXACTINPUT-01:              CLOSED
R5D-S6-CALLIDENTITY-02:            CLOSED
S6 timeout call identity:          CURSOR/ROLE-BASED + EXACTLY ONE
S6 timeout input correlation:      DESIGNATED CALL + EXACT torch.equal + BOUNDED DIGEST
R5-D-TR targeted matrix:           Z-AF 7/7 PASS
R5-D-TR2 new matrix:               AG-AL 6/6 PASS
R5-D-TR2 total synthetic matrix:   A-AL 38/38 PASS
R5-D CUDA initialized:             0
R5-D formal runtime:               NOT AUTHORIZED / NOT RUN
R5-E:                              NOT AUTHORIZED
R2 formal STOP:                    RETAINED / NO RERUN / NOT RETROACTIVELY CHANGED

cache provenance:                  PARTIALLY_ATTRIBUTED
baseline restoration:              NOT_PROVABLY_RESTORABLE
future diagnostic contamination:   HIGH
pre-R8 runtime equivalence:         NOT_ESTABLISHED

runtime readiness:                 BLOCKED
policy readiness:                  BLOCKED
learner readiness:                 BLOCKED
public learned-policy event route: DORMANT / BLOCKED
B2-R:                              NOT AUTHORIZED
training:                          NOT AUTHORIZED
commit:                            NONE
```

## Latest work — B2-V2-PD2-R5-D-TR2

R5-D-TR2 closed only `R5D-S6-CALLIDENTITY-02` in the existing test-only harness. Timeout-call role is now established independently from tensor values using the captured second-collect critic cursor, the frozen current-before-terminal call order, one second-collect `I5a_critic_buffer_insert` event, and its `critic_batch_calls == 1` evidence. The designated timeout call is the new slice's relative index 1; only that invocation's private actual input is compared with the authoritative pre-reset sidecar stack.

The S6 path no longer scans calls for a matching tensor or digest and has no earlier-call fallback. Exact shape/dtype/device/numel/`torch.equal` and bounded expected/observed SHA-256 remain frozen after identity selection. Role identification, comparison, and fingerprinting add no critic forward.

Pure/static evidence:

- existing A-AF: `32/32 PASS`;
- AG duplicate current/timeout values and AH earlier-matching-call rejection: `2/2 PASS`;
- AI missing timeout, AJ extra call, AK duplicate digest/value, AL arbitrary current plus exact timeout: `4/4 PASS`;
- combined A-AL: `38/38 PASS`;
- CUDA initialized before/after: `0 / 0`.

R5-D-TR2 supplies no real S5/S6/TIME_LIMIT evidence and does not change B2-V2 status.

## Prior work — B2-V2-PD2-R5-D-TR

R5-D-TR closed only `R5D-S6-EXACTINPUT-01` in the existing test-only harness. The S6 TIME_LIMIT oracle now compares the authoritative pre-reset sidecar-derived critic tensor with a private ephemeral clone of the actual argument passed to the recorded critic seam. Exact shape, dtype, device, numel, and `torch.equal` value equality are required; expected and observed SHA-256 values remain bounded supporting evidence and cannot independently produce PASS.

The full observed tensor is not persisted to JSON, checkpoints, reports, or buffers. The comparison adds no critic invocation. R5-C, the reviewed R5-D timing/S5/post-return/S2 contracts, R5-B historical STOP, production, I0-I6, DirectMARLEnv, installed HARL, and Kit remain unchanged.

Targeted pure evidence:

- existing A-Y: `25/25 PASS`;
- Z exact clone and AA one-value mismatch: `2/2 PASS`;
- AB stale-digest guard, AC dtype mismatch, AD shape mismatch, AE no-mutation, AF exact-once fake critic: `5/5 PASS`;
- combined A-AF: `32/32 PASS`;
- AF critic calls/comparisons/second critic call: `1 / 1 / 0`;
- CUDA initialized before/after: `0 / 0`.

R5-D-TR supplies no real S5/S6/TIME_LIMIT evidence and does not change B2-V2 status.

## Prior work — B2-V2-PD2-R5-D

R5-D implemented the GPT-reviewed/frozen R5-C contract only in the existing test-only formal harness. No production, DirectMARLEnv, I0-I6, installed HARL, Kit, or shared extension state was changed, and no runtime path was started.

Implemented test evidence:

- immutable derived timeout fixture at strict ratio `2.5`, with `ceil == 3`, plus an early `S1_TIMING_FIXTURE_CONTRACT` gate before reset/model forward/physical step;
- immutable bounded `PD2S5PreterminalEvidenceV1` with exactly the frozen PRETERMINAL/controller-time fields and no POST-RETURN/terminal/current-authority fields;
- exact decision/source-window/resolution/claim/admitted-P2/Ak/controller authority-chain checks;
- continuation from the transition-2 decision bundle only, claim-mutation disjointness, forced-row actor bypass, and original proposal/logprob preservation;
- independent S5 adjudication and durable `continuation_second_step_pass` checkpoint before external S6 done/reason assertions;
- separate optional immutable `PD2PostReturnStateDiagnosticV1`, never required for S5 and never promoted to post-autoreset evidence before S6 proof;
- actual-first-critic-input SHA-256 evidence using `PD2_TORCH_CPU_CONTIGUOUS_RAW_BYTES_SHA256_V1`, persisted before the sole wrapped VCritic call;
- `--r5d-only` pure/static verification entry with A-Y, 25/25 PASS, and zero CUDA initialization;
- updated `--static-only` guards for exact two-step count, DTO fields, forbidden dependencies, evidence order, single critic call site, frozen hashes, and exact ten-class STOP taxonomy.

R5-B remains historically `PD2-STOP-TERMINAL-TRANSPORT-FAIL` at `S6_TIME_LIMIT`. R5-D does not retroactively adjudicate R5-B S5 and supplies no real S5/S6/TIME_LIMIT evidence.

## Verification and integrity
```text
R5-C/R5-D/R5-D-TR frozen hashes:        EXACT / EXACT / EXACT
R5-D-TR2 test-only implementation:      COMPLETE
py_compile exact interpreter:           PASS / EXIT 0
--static-only:                          PASS / EXIT 0
--r5d-only A-AL:                        38/38 PASS / EXIT 0
A-AF regression subset:                 32/32 PASS
AG/AH + AI-AL targeted subset:          6/6 PASS
pre-TR2 harness SHA-256:                436ae4ea5db6264ed644eeb43defd12790d0e0af24078de3f2eea01eb2a35401
post-TR2 harness SHA-256:               96c220b895b5410d1aca37bfde4f97f09c5e79da785a2b8377642a4c3de9c6d5
protected frozen SHA-256 set:           53/53 EXACT
formal supervisor/worker/AppLauncher:   0 / 0 / 0
Isaac/CUDA/HARL/VCritic/actor:          0 / 0 / 0 / 0 / 0
environment construct/reset/step:       0 / 0 / 0
optimizer/backward/training:            0 / 0 / 0
production/HARL/harness edits:          NONE / NONE / TEST-ONLY ONLY
DirectMARLEnv/I0-I6 edits:              NONE / NONE
Kit/Junction/cache/package mutation:    NONE
commit:                                 NONE
git diff --check:                       PASS / EXIT 0
```

Only `py_compile`, static harness inspection, and bounded CPU Torch synthetic verification ran. No AppLauncher, SimulationApp, Isaac, CUDA initialization, HARL/VCritic/actor forward, environment construction/reset/step, optimizer, backward, training, playback, evaluation, checkpoint, or formal PD2 command ran.

## Active architecture / frozen invariants
- Current P2 remains the sole lifecycle/ownership authority.
- Actor actions remain proposals, never effective assignments; proposal logprob remains attached to the original proposal.
- M1/B1 is the only ownership mutation transaction; current P2 is the effective result.
- Physical control remains final P2 -> Ak -> controller.
- Lifecycle continuation is not a repeated claim.
- Terminal historical data remains separate from post-autoreset current state.
- Runtime terminal ACK ends runtime artifact lifetime only; it is not learner consumption or buffer insertion.
- Event profile remains default-off; the public learned-policy route remains dormant and blocked.
- D1, D2, D3 core, D4-O, B2-D, and B2-I0 through I6 remain frozen/closed as stated above.

## What did not run or change in PD2-R5-D
```text
formal supervisor / worker:    0 / 0
AppLauncher / SimulationApp:   0 / 0
Isaac / CUDA forward:          0 / 0
MRTA environment/reset/step:   0 / 0 / 0
installed VCritic/actor:       0 / 0
optimizer / backward:          0 / 0
formal retry:                  0
training/playback/evaluation:  NOT RUN
production source edits:       NONE
test harness edits:            ONE AUTHORIZED EXISTING HARNESS
DirectMARLEnv/I0-I6 edits:     NONE
installed HARL edits:          NONE
official .kit edits:           NONE
manifest/Junction/cache edits: NONE
commit:                        NONE
```

The repository remains intentionally dirty with prior reviewed, uncommitted B2-D through B2-I6/V1/V2 diagnostic artifacts. R5-D changes only the authorized test-only harness, this handoff, and the current-date R5-D report; prior production, package, and historical artifacts are preserved.

## Known blockers

- B2-V2 remains stopped/incomplete. R5-B passed the former real VCritic CUDA boundary but stopped later at `S6_TIME_LIMIT`.
- The exact headless experience reproducibly changes plain Torch cuBLAS behavior, but the causal settings/extension subset is unresolved.
- D4-R stopped at R8 startup/shutdown lifecycle violation; R8 repeat 2 and R5/R6/R7/R4 have no runtime evidence.
- Shared runtime equivalence to pre-R8 is not established: 43 direct installed-namespace junctions remain, and eight touched-existing metadata objects have no pre-R8 byte snapshots.
- Baseline restoration is not provable, so precise cleanup is not eligible from current evidence.
- Future startup diagnostic contamination risk in the current shared state is high.
- The event profile remains blocked by production runtime-ready gates; future PD2 can use only the reviewed private dormant route while keeping the public fence closed.
- The initial PD2 Junction predicate and R1 S0R adapter defects are corrected and verified; neither is the active R2 boundary.
- PD2-R2 stopped at a real frozen-manifest comparison: runtime `usdrt.scenegraph` matched enabled ID/version/state but had a different installed-namespace path and raw manifest SHA.
- R3 reconciles both PD1 cache-backed rows as frozen provenance-backed current-runtime indirections; R4 designs their exact fail-closed predicate without retroactively passing R2.
- The hardened cache-backed predicate now has live extension-manager/S0R PASS evidence for the two reviewed cache rows. This does not retroactively alter historical R2.
- S1, S2, S3, and S4 have historical real PASS evidence. R5-D corrects the future test-only external S5/S6 adjudication order, but S5 still has no new real-runtime adjudication.
- S6 stopped before terminal sidecar/ACK/buffer/TIME_LIMIT bootstrap/GAE/rollover. Snapshot B was not reached.
- The historical harness timing fixture produced `max_episode_length=4`. R5-D implements the reviewed strict-interior test fixture and early gate, but it has not run under Isaac; no DirectMARLEnv or lifecycle defect is established.
- The existing receipt provides sufficient immutable preterminal S5 authority. R5-D implements its DTO/adjudicator and separates optional POST-RETURN diagnostics, but real S5 remains unverified.
- R5-D implements the bounded S2 current-input hash and runtime-class evidence, but no installed VCritic forward ran and no real S2 artifact was produced.
- Any R5-E/formal execution requires GPT review plus separate authorization and must preserve one-run discipline.
- Runtime, policy, learner, public-route, B2-R, and training readiness remain blocked or unauthorized.

External path/local/retry producers and all eleven numeric TBDs remain separate dependencies. Transformer/GNN/Set Transformer, recurrent redesign, variable cardinality, arbitrary-cardinality checkpoints, training, playback, and evaluation remain deferred.

## Do not do

- Do not mark B2-V2 or D4-R PASS/CLOSED.
- Do not retry R8 repeat 1, run R8 repeat 2, or continue R5/R6/R7/R4 without explicit authorization.
- Do not rerun historical G1-G4, old D4 B0, or original B2-V2.
- Do not clean, mutate, or treat the shared Kit extension cache/link state as unchanged or pre-R8-equivalent.
- Do not continue R5/R6/R7/R4. Do not run any new current-state Isaac startup diagnostic unless the PD1 design passes review and that exact bounded slice receives explicit authorization.
- Do not deploy pre-App CUDA/cuBLAS warm-up or change AppLauncher/SimulationApp/official experiences.
- Do not retry PD2-R2, refresh the reviewed descriptors/baseline, normalize arbitrary runtime paths, or treat R5-A offline PASS as live S0R evidence.
- Do not retry R5-B or add a third physical transition under the current authorization.
- Do not enter R5-E, rerun R5-B, or execute the modified formal harness without GPT review and separate authorization.
- Do not change DirectMARLEnv, production episode semantics, lifecycle termination, or frozen I0-I6 to make the formal harness pass.
- Do not alter the corrected 43-pair reader, expected baseline, 103-row fingerprint, critical manifest, or formal stage semantics merely to continue.
- Do not treat the existing production warm-up as a root-cause repair.
- Do not modify frozen lifecycle/P2/Ak/I0-I6, DirectMARLEnv, production wrapper/training, or installed HARL semantics.
- Do not activate the public route, enter B2-R, run training/playback/evaluation/checkpoint work, or commit.

## Next step

Wait for GPT independent review of R5-D-TR2. R5-E/formal PD2 remains unauthorized. Do not rerun R5-B, launch AppLauncher/Isaac/CUDA/HARL, modify production or DirectMARLEnv, activate the public route, enter B2-R, train, or commit.

## Key files

- `AgentRead/202608/20260827/PHASE_B2_V2_PD1_PRODUCTION_STARTUP_PATH_VALIDATION_DESIGN.md`
- `AgentRead/202608/20260827/PHASE_B2_V2_PD2_CURRENT_PRODUCTION_STARTUP_REAL_ISAAC_HARL_INTERFACE_VALIDATION_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R1_WINDOWS_JUNCTION_PREDICATE_CORRECTION_AND_REENTRY_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R2_S0R_ADAPTER_CORRECTION_AND_REENTRY_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R3_CACHE_BACKED_CRITICAL_EXTENSION_AUTHORITY_RECONCILIATION_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R4_CACHE_BACKED_S0R_AUTHORITY_PREDICATE_REFINEMENT_DESIGN.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5A_CACHE_BACKED_S0R_PREDICATE_IMPLEMENTATION_AND_STATIC_VERIFICATION_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5B_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5C_S5_S6_TIMING_FIXTURE_AND_EVIDENCE_ORDERING_CONTRACT_DESIGN.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TEST_ONLY_S5_S6_FIXTURE_EVIDENCE_AND_S2_FINGERPRINT_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TR_S6_EXACT_TIMEOUT_CRITIC_INPUT_CORRELATION_REPORT.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TR2_TIMEOUT_CRITIC_INVOCATION_IDENTITY_REPORT.md`
- `scripts/environments/test_assignment_phase_b2_v2_pd2_production_startup_path_real_interface_smoke.py`
- `scripts/environments/test_assignment_phase_b2_v2_d4r_headless_experience_narrow_isolation.py`
- `AgentRead/202608/20260827/PHASE_B2_V2_D4CI_KIT_EXTENSION_REGISTRY_CACHE_LINK_INTEGRITY_AUDIT_REPORT.md`
- `AgentRead/202608/20260827/PHASE_B2_V2_D4R_RESTARTED_HEADLESS_EXPERIENCE_NARROW_ISOLATION_REPORT.md`
- this file.

## Detailed reports / archives

- `AgentRead/202608/20260827/PHASE_B2_V2_PD1_PRODUCTION_STARTUP_PATH_VALIDATION_DESIGN.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R1_WINDOWS_JUNCTION_PREDICATE_CORRECTION_AND_REENTRY_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R2_S0R_ADAPTER_CORRECTION_AND_REENTRY_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R3_CACHE_BACKED_CRITICAL_EXTENSION_AUTHORITY_RECONCILIATION_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R4_CACHE_BACKED_S0R_AUTHORITY_PREDICATE_REFINEMENT_DESIGN.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5A_CACHE_BACKED_S0R_PREDICATE_IMPLEMENTATION_AND_STATIC_VERIFICATION_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5B_CONTROLLED_FORMAL_REENTRY_REPORT.md`
- `AgentRead/202608/20260828/PHASE_B2_V2_PD2_R5C_S5_S6_TIMING_FIXTURE_AND_EVIDENCE_ORDERING_CONTRACT_DESIGN.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TEST_ONLY_S5_S6_FIXTURE_EVIDENCE_AND_S2_FINGERPRINT_IMPLEMENTATION_REPORT.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TR_S6_EXACT_TIMEOUT_CRITIC_INPUT_CORRELATION_REPORT.md`
- `AgentRead/202608/20260829/PHASE_B2_V2_PD2_R5D_TR2_TIMEOUT_CRITIC_INVOCATION_IDENTITY_REPORT.md`
- `AgentRead/202608/20260827/PHASE_B2_V2_D4R_RESTARTED_HEADLESS_EXPERIENCE_NARROW_ISOLATION_REPORT.md`
- `AgentRead/202608/20260827/PHASE_B2_V2_D4O_SIMULATIONAPP_SHUTDOWN_OBSERVABILITY_CONTRACT_REPORT.md`
- `AgentRead/202608/20260827/PHASE_B2_V2_D4_HEADLESS_EXPERIENCE_REMAINING_GROUP_NARROW_ISOLATION_DIAGNOSTIC_REPORT.md`
- `AgentRead/202608/20260827/TASK_PROGRESS_ARCHIVE_BEFORE_D4R_HANDOFF_20260827.md`
- `AgentRead/202608/20260826/PHASE_B2_V2_D3_APPLAUNCHER_EXPERIENCE_EXTENSION_CONFIG_BOUNDARY_DIAGNOSTIC_REPORT.md`
- `AgentRead/202608/20260826/PHASE_B2_V2_D2_APPLAUNCHER_TORCH_FIRST_USE_CHARACTERIZATION_REPORT.md`
- `AgentRead/202608/20260826/PHASE_B2_V2_D1_CUDA_CUBLAS_CONTEXT_ISOLATION_DIAGNOSTIC_REPORT.md`
- `AgentRead/202608/20260826/PHASE_B2_V2_FOCUSED_REAL_ISAAC_HARL_INTERFACE_VERIFICATION_REPORT.md`
- `AgentRead/202608/20260826/PHASE_B2_V1_PURE_STATIC_SYNTHETIC_INTEGRATION_VERIFICATION_REPORT.md`
- Earlier authoritative reports remain under their dated `AgentRead/` folders.

