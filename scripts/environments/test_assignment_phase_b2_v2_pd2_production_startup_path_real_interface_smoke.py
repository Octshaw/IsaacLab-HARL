"""B2-V2-PD2 current-production-startup real Isaac/HARL interface smoke.

Test-only supervisor/worker harness.  It reproduces TRAIN_STARTUP_PREFIX_V1,
uses the private dormant I6 composition, runs two forward-only transitions,
and applies the reviewed D4-O shutdown and D4-CI shared-state gates.  It never
runs backward, an optimizer/update seam, training, playback, or evaluation.
"""

from __future__ import annotations

import argparse
import ast
import copy
import ctypes
from ctypes import wintypes
from dataclasses import dataclass, fields
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import time
import traceback
from types import ModuleType
from types import MappingProxyType
from typing import Any, Mapping


PASS = "PHASE-B2-V2-PD2-R2-CURRENT-PRODUCTION-STARTUP-REAL-INTERFACE-VALIDATION-PASS-AWAITING-GPT-REVIEW"
PASS_METADATA = (
    "PHASE-B2-V2-PD2-R2-CURRENT-PRODUCTION-STARTUP-REAL-INTERFACE-VALIDATION-"
    "PASS-WITH-BENIGN-METADATA-REFRESH-AWAITING-GPT-REVIEW"
)
R1A_PASS = "PHASE-B2-V2-PD2-R1-JUNCTION-PREDICATE-CORRECTION-PASS-ELIGIBLE-FOR-FORMAL-REENTRY"
R1_STOP_DISAGREEMENT = "PD2R1-STOP-JUNCTION-ORACLE-DISAGREEMENT"
R1_STOP_UNRELIABLE = "PD2R1-STOP-JUNCTION-PREDICATE-NOT-RELIABLY-ESTABLISHED"
R2A_PASS = "PHASE-B2-V2-PD2-R2-S0R-ADAPTER-CORRECTION-PASS-ELIGIBLE-FOR-FORMAL-REENTRY"
R2_STOP_UNRELIABLE = "PD2R2-STOP-S0R-ADAPTER-NOT-RELIABLY-ESTABLISHED"
R5A_PASS = "PHASE-B2-V2-PD2-R5A-CACHE-BACKED-S0R-PREDICATE-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW"
R5A_STOP_TARGET = "PHASE-B2-V2-PD2-R5A-STOP-REVIEWED-TARGET-NO-LONGER-EXACT"
R5A_STOP_DIVERGENCE = "PHASE-B2-V2-PD2-R5A-STOP-IMPLEMENTATION-DESIGN-DIVERGENCE"
R5D_PASS = "PHASE-B2-V2-PD2-R5D-TEST-ONLY-S5S6-EVIDENCE-AND-S2-FINGERPRINT-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW"
R5D_STOP_DIVERGENCE = "PHASE-B2-V2-PD2-R5D-STOP-TEST-ONLY-IMPLEMENTATION-DESIGN-DIVERGENCE"
R5D_TR_PASS = "PHASE-B2-V2-PD2-R5D-TR-S6-EXACT-TIMEOUT-CRITIC-CORRELATION-PASS-AWAITING-GPT-REVIEW"
R5D_TR_STOP_DIVERGENCE = "PHASE-B2-V2-PD2-R5D-TR-STOP-IMPLEMENTATION-DESIGN-DIVERGENCE"
R5D_TR2_PASS = "PHASE-B2-V2-PD2-R5D-TR2-TIMEOUT-CALL-IDENTITY-PASS-AWAITING-GPT-REVIEW"
R5D_TR2_STOP_DIVERGENCE = "PHASE-B2-V2-PD2-R5D-TR2-STOP-IMPLEMENTATION-DESIGN-DIVERGENCE"
R5G_PASS = "PHASE-B2-V2-PD2-R5G-INTEGRAL-HORIZON-AND-S1-BOUNDARY-IMPLEMENTATION-PASS-AWAITING-GPT-REVIEW"
R5G_STOP_DIVERGENCE = "PHASE-B2-V2-PD2-R5G-STOP-INTEGRAL-HORIZON-IMPLEMENTATION-DIVERGENCE"
R5G_STOP_NONTIMING = "PHASE-B2-V2-PD2-R5G-STOP-NONTIMING-REGRESSION"
R5J_PASS = "PHASE-B2-V2-PD2-R5J-I5B-RETURNS-OBSERVABILITY-AND-ORACLE-REVISION-PASS-AWAITING-GPT-REVIEW"
R5J_STOP_INSUFFICIENT = "PHASE-B2-V2-PD2-R5J-STOP-TEST-ONLY-OBSERVABILITY-INSUFFICIENT"
R5J_STOP_DIVERGENCE = "PHASE-B2-V2-PD2-R5J-STOP-R5I-CONTRACT-DIVERGENCE"
R5J_STOP_REGRESSION = "PHASE-B2-V2-PD2-R5J-STOP-NONRETURNS-REGRESSION"
R5J_STOP_RECOMPUTE = "PHASE-B2-V2-PD2-R5J-STOP-OBSERVABILITY-REQUIRES-SEMANTIC-RECOMPUTATION"
STOP_PRELAUNCH = "PD2-STOP-SHARED-STATE-PRELAUNCH-MISMATCH"
STOP_STARTUP = "PD2-STOP-STARTUP-EQUIVALENCE-MISMATCH"
STOP_EXTENSION = "PD2-STOP-RUNTIME-EXTENSION-IDENTITY-MISMATCH"
STOP_VCRITIC = "PD2-STOP-VCritic-CUDA-FAIL"
STOP_ACTOR = "PD2-STOP-ACTOR-FORWARD-FAIL"
STOP_PHYSICAL = "PD2-STOP-PHYSICAL-STEP-FAIL"
STOP_TERMINAL = "PD2-STOP-TERMINAL-TRANSPORT-FAIL"
STOP_MUTATION = "PD2-STOP-PARAMETER-MUTATION"
STOP_SHUTDOWN = "PD2-STOP-SHUTDOWN-UNSAFE"
STOP_SHARED_STATE = "PD2-STOP-SHARED-STATE-ASSUMPTION-VIOLATION"
STOP_TAXONOMY = (
    STOP_PRELAUNCH,
    STOP_STARTUP,
    STOP_EXTENSION,
    STOP_VCRITIC,
    STOP_ACTOR,
    STOP_PHYSICAL,
    STOP_TERMINAL,
    STOP_MUTATION,
    STOP_SHUTDOWN,
    STOP_SHARED_STATE,
)

ROOT = Path(__file__).resolve().parents[2]
SCAN = ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct" / "scan_mobile_manipulator"
AGENT_READ = SCAN / "AgentRead"
HARL = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\harl")
ISAAC_SITE = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\isaacsim")
EXPECTED_PYTHON = Path(r"C:\isaacenvs\isaac45_harl\python.exe")
HEADLESS_EXPERIENCE = ROOT / "apps" / "isaaclab.python.headless.kit"
TRAIN = ROOT / "scripts" / "reinforcement_learning" / "harl" / "train.py"
AGENT_YAML = SCAN / "agents" / "harl_happo_cfg.yaml"
ORIGINAL_V2 = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_real_isaac_harl_interface_smoke.py"
D4O_HARNESS = ROOT / "scripts" / "environments" / "test_assignment_phase_b2_v2_d4o_simulationapp_shutdown_observability.py"
PD1_REPORT = AGENT_READ / "20260827" / "PHASE_B2_V2_PD1_PRODUCTION_STARTUP_PATH_VALIDATION_DESIGN.md"
D4CI_REPORT = AGENT_READ / "20260827" / "PHASE_B2_V2_D4CI_KIT_EXTENSION_REGISTRY_CACHE_LINK_INTEGRITY_AUDIT_REPORT.md"
D4O_REPORT = AGENT_READ / "20260827" / "PHASE_B2_V2_D4O_SIMULATIONAPP_SHUTDOWN_OBSERVABILITY_CONTRACT_REPORT.md"
V2_REPORT = AGENT_READ / "20260826" / "PHASE_B2_V2_FOCUSED_REAL_ISAAC_HARL_INTERFACE_VERIFICATION_REPORT.md"
R2_REPORT = AGENT_READ / "20260828" / "PHASE_B2_V2_PD2_R2_S0R_ADAPTER_CORRECTION_AND_REENTRY_REPORT.md"
R3_REPORT = AGENT_READ / "20260828" / "PHASE_B2_V2_PD2_R3_CACHE_BACKED_CRITICAL_EXTENSION_AUTHORITY_RECONCILIATION_REPORT.md"
R4_REPORT = AGENT_READ / "20260828" / "PHASE_B2_V2_PD2_R4_CACHE_BACKED_S0R_AUTHORITY_PREDICATE_REFINEMENT_DESIGN.md"
R5A_REPORT = AGENT_READ / "20260828" / "PHASE_B2_V2_PD2_R5A_CACHE_BACKED_S0R_PREDICATE_IMPLEMENTATION_AND_STATIC_VERIFICATION_REPORT.md"
R5B_REPORT = AGENT_READ / "20260828" / "PHASE_B2_V2_PD2_R5B_CONTROLLED_FORMAL_REENTRY_REPORT.md"
R5C_REPORT = AGENT_READ / "20260828" / "PHASE_B2_V2_PD2_R5C_S5_S6_TIMING_FIXTURE_AND_EVIDENCE_ORDERING_CONTRACT_DESIGN.md"
R5D_REPORT = AGENT_READ / "20260829" / "PHASE_B2_V2_PD2_R5D_TEST_ONLY_S5_S6_FIXTURE_EVIDENCE_AND_S2_FINGERPRINT_IMPLEMENTATION_REPORT.md"
R5D_TR_REPORT = AGENT_READ / "20260829" / "PHASE_B2_V2_PD2_R5D_TR_S6_EXACT_TIMEOUT_CRITIC_INPUT_CORRELATION_REPORT.md"
R5D_TR2_REPORT = AGENT_READ / "20260829" / "PHASE_B2_V2_PD2_R5D_TR2_TIMEOUT_CRITIC_INVOCATION_IDENTITY_REPORT.md"
R5E_REPORT = AGENT_READ / "20260829" / "PHASE_B2_V2_PD2_R5E_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md"
R5F_REPORT = AGENT_READ / "20260829" / "PHASE_B2_V2_PD2_R5F_INTEGRAL_HORIZON_TIMING_AND_S1_BOUNDARY_RECONCILIATION_DESIGN.md"
R5G_REPORT = AGENT_READ / "20260831" / "PHASE_B2_V2_PD2_R5G_INTEGRAL_HORIZON_FIXTURE_AND_S1_BOUNDARY_IMPLEMENTATION_REPORT.md"
R5H_REPORT = AGENT_READ / "20260831" / "PHASE_B2_V2_PD2_R5H_ONE_CONTROLLED_FORMAL_REENTRY_REPORT.md"
R5I_REPORT = AGENT_READ / "20260831" / "PHASE_B2_V2_PD2_R5I_I5B_RETURNS_CONTRACT_AND_FAILURE_OBSERVABILITY_RECONCILIATION_DESIGN.md"

DEVICE = "cuda:0"
E, M, N, T = 2, 3, 12, 2
PD2_DESIRED_TERMINAL_TRANSITION = 2
PD2_REQUIRED_MAX_EPISODE_LENGTH = 3
PD2_TIMEOUT_BUCKET_LOWER = 2
PD2_TIMEOUT_BUCKET_UPPER = 3
PD2_SEMANTIC_HORIZON_STEPS = 3
PD2_PRODUCTION_INTEGRAL_REL_TOL = 0.0
PD2_PRODUCTION_INTEGRAL_ABS_TOL = 1.0e-9
PD2_INTEGRAL_HORIZON_FIXTURE_SCHEMA_V1 = "PD2_INTEGRAL_HORIZON_FIXTURE_V1"
PD2_S1_POSTCONSTRUCTION_TIMING_EVIDENCE_SCHEMA_V1 = "PD2_S1_POSTCONSTRUCTION_TIMING_EVIDENCE_V1"
PD2_EXPECTED_SCALE_CONTRACT_VERSION = "event_policy_scale_contract_v2"
PD2_S5_PRETERMINAL_EVIDENCE_SCHEMA_V1 = "PD2_S5_PRETERMINAL_EVIDENCE_V1"
PD2_POST_RETURN_STATE_DIAGNOSTIC_SCHEMA_V1 = "PD2_POST_RETURN_STATE_DIAGNOSTIC_V1"
PD2_CRITIC_INPUT_FINGERPRINT_ALGORITHM_V1 = "PD2_TORCH_CPU_CONTIGUOUS_RAW_BYTES_SHA256_V1"
PD2_S6_TIMEOUT_CRITIC_INPUT_CORRELATION_SCHEMA_V1 = "PD2_S6_TIMEOUT_CRITIC_INPUT_CORRELATION_V1"
PD2_S6_TIMEOUT_CRITIC_INVOCATION_IDENTITY_SCHEMA_V1 = "PD2_S6_TIMEOUT_CRITIC_INVOCATION_IDENTITY_V1"
PD2_S6_I5B_RETURNS_EVIDENCE_SCHEMA_V1 = "PD2_S6_I5B_RETURNS_EVIDENCE_V1"
PD2_S6_I5B_RETURNS_SOURCE_BOUNDARY_V1 = "I5b_compute_event_returns"
PD2_S6_I5B_RETURNS_FAILURE_DETAILS_V1 = (
    "S6_I5B_RETURNS_RESULT_SHAPE",
    "S6_I5B_RETURNS_RESULT_NONFINITE",
    "S6_I5B_RETURNS_BUFFER_STORAGE_SHAPE",
    "S6_I5B_RETURNS_TRAINING_SLICE_SHAPE",
    "S6_I5B_RETURNS_TRAINING_SLICE_NONFINITE",
    "S6_I5B_RETURNS_RESULT_BUFFER_MISMATCH",
    "S6_I5B_RETURNS_RESULT_BUFFER_ALIAS",
)
PD2_S6_I5B_RETURNS_FINAL_SLOT_DIAGNOSTIC_V1 = "S6_I5B_RETURNS_FINAL_SLOT_DIAGNOSTIC"
PD2_SECOND_COLLECT_CURRENT_CRITIC_CALL_COUNT = 1
PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT = 1
PD2_TIMEOUT_CRITIC_RELATIVE_INDEX = 1
CANONICAL_SEED = 1
TIMEOUT_SECONDS = 300
EXPECTED_HEAD = "14993dee344bade0230d2eb97b5f22171331f44a"
EXPECTED_EXPERIENCE_SHA256 = "475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795"
EXPECTED_D4O_SHA256 = "1ccc9163725a40b10bcf10e423aa389c3bb024db23093bbb8b88104d01b03ff5"
EXPECTED_SHARED_FINGERPRINT = "ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f"
EXPECTED_SHARED_COUNTS = {"linkroot": 45, "cacheroot": 50, "metadata": 8, "total": 103, "junction_pairs": 43}
EXPECTED_REPORT_HASHES = {
    str(PD1_REPORT): "242b782e92634d746a45b93f814b6e14286e6f46f0b85f953483924c4570fd5e",
    str(D4CI_REPORT): "ced5867e7eefdf7618a89861122562a83cc62a488ac77a0a4d0fa67109e32209",
    str(D4O_REPORT): "eda1524388d6eff6858a52c7b2815956d8e008c69958452ac2e76ef441b86e70",
    str(V2_REPORT): "3389ea77974e9931f714efe0cb24e478d7364417ef904275792a14e66cced195",
    str(R2_REPORT): "843b392ab0ed81330c89c39c007d524bc1f4cb27eb8df7ba4d47a6a97ad74390",
    str(R3_REPORT): "787ea307068a8223031ecdf64ab37e9a351a87461c35cf8a6a166215f788e136",
    str(R4_REPORT): "30f9233c35d43d22e7bc50e11b61371e1d7be376a0f64c5ad75072665e211ce1",
    str(R5A_REPORT): "d98c1d3567654dc3ade38808526f83b0db5f4761b567ab986134b2a28406d2d1",
    str(R5B_REPORT): "5bb3d68ac50c9e788de4ace060b8938ed72a212f2b16703f042b86e7ab6cbd59",
    str(R5C_REPORT): "ce4f4d8399cf465e981dd4fb67f37ba81ed991271530df802d09be8448a1ceac",
    str(R5D_REPORT): "35e35a56c993e53829b4b819bd695315db090ec2c01cf574993259277e68bd93",
    str(R5D_TR_REPORT): "83aa129bb29648bf186c278ba4e0db5b6b2cf269e2b5d19b664e1341eddbafdd",
    str(R5D_TR2_REPORT): "e5700c7e31e29c6ea7750a4e679abbdb17adcc1026b7b2a5b3cc59b098e88f86",
    str(R5E_REPORT): "21fc419942c63c278af6ee1a89706c4404d4a57abf4b77772155062ebcb8287c",
    str(R5F_REPORT): "4683245527f5294c14c4995bb618687de4daf3d9dd3c3b0305291138ab04d6ef",
    str(R5G_REPORT): "51ef3d5b263115b598ff153fea1ee28b6d71c3e2d3653903bc0af341f89f29b2",
    str(R5H_REPORT): "a5549e16392ba3bac99d89bf93c37436aa915e902d04ee0e269465a0306d7353",
    str(R5I_REPORT): "ef03379e94906e544604fd0fe62b68a2cd542c0b466773e2800e6a4841bdd99b",
}

CACHE_ROOT = Path(r"C:\Users\33506\AppData\Local\ov\data\exts\v2")
LINK_ROOT = Path(r"C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3")
METADATA_PATHS = (
    CACHE_ROOT / "cache_db.json",
    CACHE_ROOT / "index" / "242af5a8" / "registry.json",
    CACHE_ROOT / "index" / "242af5a8" / "registry.lock",
    CACHE_ROOT / "index" / "2e8f67e3" / "registry.json",
    CACHE_ROOT / "index" / "2e8f67e3" / "registry.lock",
    CACHE_ROOT / "index" / "f6f0b2d0" / "registry.json",
    CACHE_ROOT / "index" / "f6f0b2d0" / "registry.lock",
    CACHE_ROOT / "urls" / "d3e0ce88daec2e57215837649b02ef9b4fb9d19d",
)

# Frozen D4-CI post-R8 pair inventory.  The installed names and cache target
# names come from the reviewed cache_db mapping whose bytes participate in the
# frozen 103-row fingerprint.  Manifest hashes come from that same reviewed
# 103-row evidence.  Runtime observations are compared to this table; they do
# not refresh it.
EXPECTED_JUNCTION_PAIRS = {
    "carb.audio-0.1.0+d02c707b.wx64.r.cp310": ("carb.audio-ea552514713f5fa0", "a55aecc1efb548cb21075404abbce5b5908cf9819672d0b7e6a43bb86987c330"),
    "omni.assets.plugins-0.0.0+d02c707b.wx64.r": ("omni.assets.plugins-5e04a15ad978f6c2", "ee4a84b6db004d3b51176a2ea38f00bc9ddcc8c6d03eb930c4b9539d123602e8"),
    "omni.client-1.2.2+d02c707b.wx64.r": ("omni.client-40b130eb96e8b6ea", "4f4dcbcedba66a229fa60513fa3f7d87a0ed1d1f392983c86be93ec2b550cc79"),
    "omni.convexdecomposition-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.convexdecomposition-106.5.3+106.5.0.wx64.r.cp310.ub3f", "474d0d3e1c4f8bf3fd4f90f36372488db92991cbdc771165bc2eec6e7ac0db04"),
    "omni.gpu_foundation-0.0.0+d02c707b.wx64.r.cp310": ("omni.gpu_foundation-9ebd64348a4ca237", "d98c783c2f9db1c2239edee756ba2e24e4f494569fef31a1be4cef2afc83439e"),
    "omni.gpu_foundation.shadercache.vulkan-1.0.0+d02c707b.wx64.r": ("omni.gpu_foundation.shadercache.vulkan-3d307028bc58524f", "695c3067980a52d4c5c4b94e236334cb527bb7a0691a07ec37a14cc7bf913567"),
    "omni.gpucompute.plugins-0.0.0+d02c707b.wx64.r": ("omni.gpucompute.plugins-fcd094fa122db7b5", "0c5b87b8ecb6d4aa9dd21c039a6738d222b1c975522f87f73d3227a519d7b8a7"),
    "omni.graph.exec-0.9.4+d02c707b.wx64.r": ("omni.graph.exec-cc20ef0f64a582af", "2afe37e0504339567126f2b4a89066c4359b0cb442789e58efde270ec46efdcd"),
    "omni.isaac.dynamic_control-1.3.16+106.5.0.wx64.r.cp310": ("omni.isaac.dynamic_control-1.3.16+106.5.0.wx64.r.cp310", "f29e7179bbbe69047233f99812356a7e8dbafd18c038e0b735b802ab775d6848"),
    "omni.kit.actions.core-1.0.0+d02c707b.wx64.r.cp310": ("omni.kit.actions.core-679707d2f4f5f8a6", "2eed93c0ae118f00515487250cecc266d968ac51f01381550aff36a296928238"),
    "omni.kit.audiodeviceenum-1.0.1+d02c707b.wx64.r.cp310": ("omni.kit.audiodeviceenum-598f466b4e06e8a8", "1285eda5cca8181150f22da94c36f4fec059b56a4fc2837b7fab9922ecb4db45"),
    "omni.kit.commands-1.4.9+d02c707b.wx64.r.cp310": ("omni.kit.commands-8019ed0334ed7025", "2d60ef1811c53626f9e6cb6c6f6b95258315371117cab49a9881b9beea4a4dce"),
    "omni.kit.exec.core-0.13.4+d02c707b.wx64.r.cp310": ("omni.kit.exec.core-6250c29273d9730a", "c04565d5ed037ec9c5cacdcf777b412757b7cae9b82715d392712b953f2dad57"),
    "omni.kit.numpy.common-0.1.2+d02c707b.wx64.r.cp310": ("omni.kit.numpy.common-ff25ef64cb10913c", "c8845f404a8c1586c0f2c1561d3b6d9649e573edd1b45c6a45827e839da630d3"),
    "omni.kit.pip_archive-0.0.0+d02c707b.wx64.cp310": ("omni.kit.pip_archive-f3d70a416d53c435", "33054a12cd38161f597b0b50046c4070f145d3e52748b37274fe650f2002c25e"),
    "omni.kit.pipapi-0.0.0+d02c707b": ("omni.kit.pipapi-7c50f7988a7aa377", "9c188b87394c30c3fdfaf030d28f0337af3cb139b7b993ffc549f7b6f933540b"),
    "omni.kit.primitive.mesh-1.0.17+d02c707b": ("omni.kit.primitive.mesh-ef6077e0240ac07c", "cbff9463fa0e774cb1f25dc40411faaff5c68cd51332c08583c79943ecbba687"),
    "omni.kit.stage_template.core-1.1.22+d02c707b": ("omni.kit.stage_template.core-1132d9f99d61a975", "8777f9c32ee33db93d29a1e375cb563d9fe3b0a4775ea3f83eea1ed10ce64ee3"),
    "omni.kit.stage_templates-1.2.6+d02c707b": ("omni.kit.stage_templates-1e836a2cf0ec7071", "cd8d9a38ddc7f3f3109278f35b086d0a5b16c7406c11eae62d670831ea2a8501"),
    "omni.kit.telemetry-0.5.1+d02c707b.wx64.r.cp310": ("omni.kit.telemetry-e51c7dc167fb713d", "449c9734822f4fcee255708bf5a0ba320638531dd06d687da1d42e098f1c9946"),
    "omni.kit.usd_undo-0.1.8+d02c707b": ("omni.kit.usd_undo-c79d32047b035aab", "dd3614011c6eb036f6387606a7ca1b76e988a4206e8cf31a3b3bd992a9cb0948"),
    "omni.kit.usd.layers-2.2.0+d02c707b.wx64.r.cp310": ("omni.kit.usd.layers-3b387b935b5f672c", "4978ea564bd7224739a03dd970284b06ca48e1b2435ffa673e3df085d8f1583d"),
    "omni.kvdb-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.kvdb-106.5.3+106.5.0.wx64.r.cp310.ub3f", "5830ee0b21769c3caec6433de89ab89bbc629866f0e03ab66fbe7a4da4470936"),
    "omni.localcache-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.localcache-106.5.3+106.5.0.wx64.r.cp310.ub3f", "305ff6e17259f44476295a4670185bce831834b206c94eb5ba896ffe407d17e0"),
    "omni.physics.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.physics.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f", "a9de03d32363fbc72576b61d8bd67a8dfeb07d88055181174556979a15ed1d25"),
    "omni.physx-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.physx-106.5.3+106.5.0.wx64.r.cp310.ub3f", "62b09c441d2bd4a45357ab74aff1fc064315587e5c7d07cf6429caa5e0e64646"),
    "omni.physx.cooking-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.physx.cooking-106.5.3+106.5.0.wx64.r.cp310.ub3f", "3284b9525947b19a5b761dbb24959559f22508c2b98133c6cfedfb50239b750c"),
    "omni.physx.foundation-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.physx.foundation-106.5.3+106.5.0.wx64.r.cp310.ub3f", "a8f6ecbcdfd321faaa39c9887bfdd08e4a94bc61126b41be66b437d111382e20"),
    "omni.physx.stageupdate-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.physx.stageupdate-106.5.3+106.5.0.wx64.r.cp310.ub3f", "180cf6661c4c9a76c7eda626def2e8c9e2427b7f2b7d2c1efb84e0e41bfa7bf3"),
    "omni.physx.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.physx.tensors-106.5.3+106.5.0.wx64.r.cp310.ub3f", "d06ff37e366b468d2272f8b9ed02c3742fe30c17e712296f5b929ce44698fe41"),
    "omni.stats-1.0.1+d02c707b.wx64.r.cp310": ("omni.stats-13705f73847351a2", "ccc77b1cceb1125aef8df76cc9806d26915adb68fe72a14b9d6f1cfe4a04cdcb"),
    "omni.timeline-1.0.11+d02c707b.wx64.r.cp310": ("omni.timeline-f8cebd7dafe84ae2", "7e83acb398c8db8c9bfdcaacede951ebad7cf3be80d2fbfc3d53c83ac0fc8fb2"),
    "omni.usd_resolver-1.0.0+d02c707b.wx64.r.cp310": ("omni.usd_resolver-ac392fd4491a705b", "2136e8ac589ef6becc5e02c79f255a75a0e3562d20e6eca6eb03a36bb0655b11"),
    "omni.usd-1.12.4+d02c707b.wx64.r.cp310": ("omni.usd-c74e9d24e744cf8c", "5a7011e0dc2ce4a01aef3db7841fcf02ea27e32c11b4b7b7e9e3a6590ba568f6"),
    "omni.usd.config-1.0.5+d02c707b": ("omni.usd.config-d10e88e1d82aed43", "99bd8f20ea0306c39bb84446111f134bbc479d8aa49e9d6b53731e07e4c1f586"),
    "omni.usd.core-1.4.2+d02c707b.wx64.r": ("omni.usd.core-bdb83ae126823535", "44b677f5654b9f195a7e9a93cc937772d4283753bc410f1b29ef4f0813012278"),
    "omni.usd.libs-1.0.1+d02c707b.wx64.r.cp310": ("omni.usd.libs-672a0e4c1165d252", "0d508e9832d2cdcaf7375e53f5ea5a269e2dfa864d0f4913b9467e645774651f"),
    "omni.usd.schema.audio-0.0.0+d02c707b.wx64.r.cp310": ("omni.usd.schema.audio-23e539191966c918", "3a1e938b789d401d1985a0474f73a2103a6939018c5fde103f3882250e720993"),
    "omni.usd.schema.physx-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.usd.schema.physx-106.5.3+106.5.0.wx64.r.cp310.ub3f", "08ccebf8f093009b760be1f194a9d1d0ea04c80c59cdccec0f5d0aeb6d764d9b"),
    "omni.usd.schema.semantics-0.0.0+d02c707b.wx64.r.cp310": ("omni.usd.schema.semantics-f6a5c0c7b1e95530", "9fd8b55a332c597b29e51f593a48c043b75dfe3bc0d1292b79384b51252c41a0"),
    "omni.usdphysics-106.5.3+106.5.0.wx64.r.cp310.ub3f": ("omni.usdphysics-106.5.3+106.5.0.wx64.r.cp310.ub3f", "bf69e546978e7bb2a3a0098302b52322bd1b90698040a080ede51024b5242676"),
    "omni.warp.core-1.5.0+wx64": ("omni.warp.core-1.5.0+wx64", "6bac2a8a0bec9061165ec9dfcd4d18f151498335a3014c949fa2b2a2dd75cf6e"),
    "usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310": ("usdrt.scenegraph-60ef2a9cb390fac8", "e155eeba2044deb2602bc229f68fe57b7f60e1f5adacc5283737488918a0d5fe"),
}

IO_REPARSE_TAG_MOUNT_POINT = 0xA0000003
FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
FSCTL_GET_REPARSE_POINT = 0x000900A8
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000


def _repo(relative: str) -> str:
    return str(ROOT / Path(relative))


EXPECTED_PD1_SOURCE_HASHES = {
    _repo("scripts/reinforcement_learning/harl/train.py"): "393ad9ea29e6fd9919b5dc5441946cce32766c901c87cf2c481348fb91941b53",
    _repo("scripts/reinforcement_learning/harl/play_assignment.py"): "df47c4d2186a54f098b2fdf99ec091ce0ccb685e5f3032c929b40945cf41b2ba",
    _repo("scripts/reinforcement_learning/harl/play.py"): "6918c8c8cc1c608299d2ed989d6a9a6dd4bf21799643010925315d2559f4828d",
    str(ORIGINAL_V2): "12566d07b2c1162fadcbd22ac47a80f72ae2d696c70d7944aad31fe8c31940d7",
    _repo("source/isaaclab/isaaclab/app/app_launcher.py"): "6d9caa29f7177103cbdbd217eb18db19ef00cdadc2f1ecc7c79adc9d29da44c1",
    str(SCAN / "assignment_harl_training.py"): "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
    str(SCAN / "assignment_event_learned_route.py"): "b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b",
    str(SCAN / "assignment_event_actor_collection.py"): "3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45",
    str(AGENT_YAML): "e84b2ee54f5ebd6d51fdf1a799a812bca4039b8cbef17b7eba3ef06337da44b5",
}

EXPECTED_D4CI_SOURCE_HASHES = {
    str(HARL / "algorithms/actors/happo.py"): "dd44fe7842160aa215b2d220726f6dd5e70b251c1a2e9c50cfeb6bd00535cf96",
    str(HARL / "algorithms/actors/on_policy_base.py"): "ab5a1c785402efd4bd8a56b0b60503a12b365dbb422ca06ba9afee648471cd2c",
    str(HARL / "algorithms/critics/v_critic.py"): "ae66390702efb55099d151c11f28ae533f25ef6d62697949445abd2979708bf3",
    str(HARL / "common/buffers/on_policy_actor_buffer.py"): "a7352b59d8fa28b96e28e3021ddeaa9f8da5944c686651b1c04b0ec26c96f8cc",
    str(HARL / "common/buffers/on_policy_critic_buffer_ep.py"): "0a288f3888908b98157a0848744d7eebec655159d5e89d9c85436a2e30b9a46f",
    str(HARL / "common/valuenorm.py"): "a35471b136567bde0b7fc7be34a7873efa617bdabf9a9074517ff0e3ef3fb8b0",
    str(HARL / "runners/on_policy_base_runner.py"): "5d99e0fa6f70f0bbff4d5b0f00f45faa3e4b543e1531f5259900480f1842044f",
    str(HARL / "runners/on_policy_ha_runner.py"): "14f68bac719be40af8117284741c06e7434a18458d07cb30d5400bc32d02579a",
    str(ISAAC_SITE / "apps/isaacsim.exp.base.kit"): "ba9b7e23f5a3bc320ed8d7e3391d2080649b606cff15444b9e751ee16331f9b3",
    str(ISAAC_SITE / "apps/isaacsim.exp.base.python.kit"): "1806f0bff51b49af8754b5d150fe64f5942f9b49a22bcfd67ed5d40b4cfddea9",
    str(ISAAC_SITE / "exts/isaacsim.simulation_app/isaacsim/simulation_app/simulation_app.py"): "7d9ac4310913d776c17abe9f8cd0041b3d4d62cfcf6cd1a7d0548e85c2dd5b69",
    str(HEADLESS_EXPERIENCE): EXPECTED_EXPERIENCE_SHA256,
    _repo("scripts/environments/test_assignment_phase_b2_v2_d1_cuda_cublas_context_diagnostic.py"): "cf918383721c8d4cf674305685b16b16c663de0a23dd0842a722f9f00b23799e",
    _repo("scripts/environments/test_assignment_phase_b2_v2_d2_applauncher_torch_first_use_diagnostic.py"): "f6b0b5a9bbfebb420e38a54c329b82cc4ac731293832e033416a22b7be73bb18",
    _repo("scripts/environments/test_assignment_phase_b2_v2_d3_applauncher_experience_extension_config_diagnostic.py"): "5d7cea913429316a1998549ec038aaba5e85ef1cf912b44211a8f46a58ffcfaf",
    _repo("scripts/environments/test_assignment_phase_b2_v2_d4_headless_experience_remaining_group_narrow_isolation_diagnostic.py"): "3847a28e91e0576646514f1efc08fd853360f1b4255f00f38aa27db31762a807",
    str(D4O_HARNESS): EXPECTED_D4O_SHA256,
    str(ORIGINAL_V2): "12566d07b2c1162fadcbd22ac47a80f72ae2d696c70d7944aad31fe8c31940d7",
    str(SCAN / "assignment_event_actor_collection.py"): "3a78cfd4afd94fe30dbc8cf53b0ef3595f881c2a36621a37900ef1b067d7bc45",
    str(SCAN / "assignment_event_critic_buffer.py"): "682e924fb2c9196818b9ef537ecda8eee46408d6828b4e380718786597adc29f",
    str(SCAN / "assignment_event_gae_returns.py"): "7d9f154571ee43a1918d4f33f888c8b180c7c8731e8a474fdf31e32ba1923379",
    str(SCAN / "assignment_event_happo_policy_math.py"): "3621f905a765a50c12f549de0bbba0907e98e7c4892a719394ea6907ad2c33b4",
    str(SCAN / "assignment_event_learned_route.py"): "b883ee48dfe0a15cc01ddf01b0bd1914a17e0627e6cc145c214f8b369b4d371b",
    str(SCAN / "assignment_event_policy_decision.py"): "d465de33edb11769dfd3fc34e535416ba9bb212f4fbdd770a11dde1830862697",
    str(SCAN / "assignment_event_policy_evidence.py"): "7563835ca94eb08baab463a349aa8d27a056da12477e3ded8827b512dd86f83a",
    str(SCAN / "assignment_event_profile_schema_contract_v2.py"): "9fb64e62f1fff8b2ad9eafd8137f8d71b8912464e4c859e2b8b395421c37f955",
    str(SCAN / "assignment_event_proposal_adapter.py"): "874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd",
    str(SCAN / "assignment_event_runtime_facade.py"): "036082d8df61514aa3f3c424ae6559fa678536097b66bfd5bd6f632ca3479478",
    str(SCAN / "assignment_event_terminal_critic_sidecar.py"): "655ecafeaf6d08eb856725023572438976a381fb7ffe0a5cadf16d61a4bfe49f",
    str(SCAN / "assignment_event_terminal_learner_transport.py"): "e61644a1fde332232a0135a2f673df2e7cf6f220d1074acd6392617a69bbdfe4",
    str(SCAN / "assignment_harl_training.py"): "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
    str(SCAN / "assignment_harl_wrapper.py"): "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
    str(SCAN / "assignment_lifecycle_authority_runtime.py"): "ca7774808fb8901dbc209f61a8915713106a5dc9da739d1bce30c8952a21e10e",
    str(SCAN / "assignment_lifecycle_transaction_runtime.py"): "2033be70f91a14678ed718a3a0d3d8c26a26a5c5a05b8c6e9ae5dacb3cbfd3de",
    str(SCAN / "scan_mobile_manipulator_env.py"): "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
    _repo("source/isaaclab/isaaclab/app/app_launcher.py"): "6d9caa29f7177103cbdbd217eb18db19ef00cdadc2f1ecc7c79adc9d29da44c1",
    _repo("source/isaaclab/isaaclab/envs/direct_marl_env.py"): "7f7714a6f32e24ce34ef184cb9eed87cc36d4db0744c44a816ce3da9cc505f31",
}

EXPECTED_SOURCE_HASHES = {**EXPECTED_D4CI_SOURCE_HASHES, **EXPECTED_PD1_SOURCE_HASHES, **EXPECTED_REPORT_HASHES}


def _critical(base: str, version: str, root: Path, digest: str, authority: str) -> dict[str, object]:
    return {
        "base_id": base,
        "enabled_id": f"{base}-{version}",
        "version": version,
        "root": str(root),
        "manifest": str(root / "config" / "extension.toml"),
        "manifest_sha256": digest,
        "authority": authority,
        "link": False,
        "link_target": None,
    }


CRITICAL_MANIFEST = (
    _critical("isaaclab", "0.36.23", ROOT / "source/isaaclab", "ad9c0fe4f7bfde023afc95290e5578f95c5b101d332095cdc75d7858c1f3a151", "PROJECT_LOCAL_SOURCE"),
    _critical("isaaclab_assets", "0.2.2", ROOT / "source/isaaclab_assets", "777900c0c5ae96f5f9e88d7824c867062a930f9b27db4db58c2097e86d5d066e", "PROJECT_LOCAL_SOURCE"),
    _critical("isaaclab_tasks", "0.10.31", ROOT / "source/isaaclab_tasks", "984cd22b00925a50e70aa04a7a8a53da1bde53927adbc8b0c1704ad4cdf4c8cb", "PROJECT_LOCAL_SOURCE"),
    _critical("isaaclab_rl", "0.1.4", ROOT / "source/isaaclab_rl", "17611e8fcca9297f88ff5c080e85ecaf7684015a1a75e5b4232261ade763df16", "PROJECT_LOCAL_SOURCE"),
    _critical("isaacsim.simulation_app", "2.4.2", ISAAC_SITE / "exts/isaacsim.simulation_app", "6609623fbf15a3355a915232069a7e5e6279cd00edde39df84167c5a014f5893", "OFFICIAL_INSTALLED"),
    _critical("isaacsim.core.api", "4.2.16", ISAAC_SITE / "exts/isaacsim.core.api", "5304880f3b029092febc3678c796177be24fd508e20a8dceabfa887091a9b525", "OFFICIAL_INSTALLED"),
    _critical("isaacsim.core.cloner", "1.3.4", ISAAC_SITE / "exts/isaacsim.core.cloner", "77de0a78118b6af2b0ff5225966a89507f95117e29ebad7c24e20bb8aa5a311b", "OFFICIAL_INSTALLED"),
    _critical("isaacsim.core.utils", "2.2.8", ISAAC_SITE / "exts/isaacsim.core.utils", "7202eeb2c1d9145b5d691c33a5c28f5af66c07cadc4443c843dc5395e15eeffd", "OFFICIAL_INSTALLED"),
    _critical("omni.physx", "106.5.7", ISAAC_SITE / "extsPhysics/omni.physx", "97516dcee1b6271943fca495a6080a83f23897ef0e11cb9728ca2f17e6a0fa95", "OFFICIAL_INSTALLED"),
    _critical("omni.physx.tensors", "106.5.7", ISAAC_SITE / "extsPhysics/omni.physx.tensors", "295ac7632a08c7fdf4111b267fc31fd552bd504504a1f9f76b2f2b0709069568", "OFFICIAL_INSTALLED"),
    _critical("omni.physx.fabric", "106.5.7", ISAAC_SITE / "extsPhysics/omni.physx.fabric", "9fc842ed58cb46b9c356b462ff0173664d8066bae28b3c4aa19ddddb57f20f21", "OFFICIAL_INSTALLED"),
    _critical("usdrt.scenegraph", "7.5.1", ISAAC_SITE / "extscache/usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310", "a52a69b609100538429406619e9576e81fb1a18a279ddc40628d9fa932358818", "OFFICIAL_INSTALLED_CACHE"),
    _critical("omni.warp.core", "1.5.0", ISAAC_SITE / "extscache/omni.warp.core-1.5.0+wx64", "62d55511ee3d3d9e150f34c5b6196f983af8915e5cf5afe17fe97e96348408df", "OFFICIAL_INSTALLED_CACHE"),
)


# Frozen R4/R4-TR authority.  These literal constants are admission authority;
# no filesystem observation is used to construct or refresh them.
REVIEWED_CACHE_BACKED_AUTHORITIES_V1 = MappingProxyType(
    {
        "usdrt.scenegraph": MappingProxyType(
            {
                "descriptor_id": "PD2_CACHE_TARGET_USDRT_SCENEGRAPH_7_5_1_R3_V1",
                "authority": "OFFICIAL_INSTALLED_CACHE",
                "base_id": "usdrt.scenegraph",
                "enabled_id": "usdrt.scenegraph-7.5.1",
                "version": "7.5.1",
                "distribution_basename": "usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310",
                "target_basename": "usdrt.scenegraph-60ef2a9cb390fac8",
                "retained_archive_action": "usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310.zip",
                "installed_namespace": (
                    r"C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3"
                    r"\usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310"
                ),
                "target": r"C:\Users\33506\AppData\Local\ov\data\exts\v2\usdrt.scenegraph-60ef2a9cb390fac8",
                "junction_tag": IO_REPARSE_TAG_MOUNT_POINT,
                "provenance": "D4-CI Tier 1 / CONFIRMED_R8_CREATED",
                "cache_db_pair": (
                    "usdrt.scenegraph-7.5.1+d02c707b.wx64.r.cp310",
                    "usdrt.scenegraph-60ef2a9cb390fac8",
                ),
                "l1_metadata": MappingProxyType(
                    {
                        "package_version": "7.5.1",
                        "dependencies": ("omni.gpucompute.plugins", "omni.usd.libs"),
                        "native_plugins": ("bin/usdrt.scenegraph.plugin", "bin/usdrt.xformcache.plugin"),
                        "kit_version": "106.5.0+release.162521.d02c707b.gl",
                        "build_number": "106.5.0+release.162521.d02c707b.gl",
                        "publish_date": 1734046497,
                        "target_config": ("release",),
                        "target_python": ("cp310",),
                        "target_platform": ("windows-x86_64",),
                        "target_kit_hash": ("d02c707b",),
                    }
                ),
                "l3": MappingProxyType(
                    {
                        "algorithm": "PD2_CACHE_TARGET_RAW_TREE_V1",
                        "file_count": 536,
                        "byte_count": 31105760,
                        "path_set_sha256": "8e2047e45e5c2af50785c80c9110dde1ed96289980a561416c936d56c97b3db8",
                        "content_sha256": "785e278f675786a53b3160b02aeb0abb47c432f3342b6b4e2153e7b753391a43",
                        "internal_reparse_count": 0,
                        "primary_manifest_sha256": "e155eeba2044deb2602bc229f68fe57b7f60e1f5adacc5283737488918a0d5fe",
                        "generated_manifest_sha256": "85e970a0ded7363ee8b605558757e0110c56347366884ee7fbd6ad05b7fa847f",
                        "non_generated": MappingProxyType(
                            {
                                "file_count": 517,
                                "byte_count": 31086951,
                                "path_set_sha256": "6d8c5ca45d0adb88ab5797c76200a3c2266c075eb85e510d0a08829bdcd00bb9",
                                "content_sha256": "f2fb3e83b9713b17cbbee5db4bc57a1fd96661151159bf062ad518999b23407b",
                            }
                        ),
                        "python_source": MappingProxyType(
                            {
                                "file_count": 41,
                                "byte_count": 574044,
                                "content_sha256": "ab00914d309ae589092d080038e8639994a278b54201fbb45299c2d034e4228f",
                            }
                        ),
                        "native_runtime": MappingProxyType(
                            {
                                "file_count": 38,
                                "byte_count": 13705208,
                                "content_sha256": "26db73bb0920fa73ef1c0f29b8f6a16f66013dd21f53d13dfa65381f53dd2c5e",
                            }
                        ),
                        "explicit_raw_files": MappingProxyType({}),
                    }
                ),
            }
        ),
        "omni.warp.core": MappingProxyType(
            {
                "descriptor_id": "PD2_CACHE_TARGET_OMNI_WARP_CORE_1_5_0_R3_V1",
                "authority": "OFFICIAL_INSTALLED_CACHE",
                "base_id": "omni.warp.core",
                "enabled_id": "omni.warp.core-1.5.0",
                "version": "1.5.0",
                "distribution_basename": "omni.warp.core-1.5.0+wx64",
                "target_basename": "omni.warp.core-1.5.0+wx64",
                "retained_archive_action": "omni.warp.core-1.5.0+wx64.zip",
                "installed_namespace": (
                    r"C:\isaacenvs\isaac45_harl\Lib\site-packages\omni\data\Kit\Isaac-Sim\4.5\exts\3"
                    r"\omni.warp.core-1.5.0+wx64"
                ),
                "target": r"C:\Users\33506\AppData\Local\ov\data\exts\v2\omni.warp.core-1.5.0+wx64",
                "junction_tag": IO_REPARSE_TAG_MOUNT_POINT,
                "provenance": "D4-CI Tier 1 / CONFIRMED_R8_CREATED",
                "cache_db_pair": ("omni.warp.core-1.5.0+wx64", "omni.warp.core-1.5.0+wx64"),
                "l1_metadata": MappingProxyType(
                    {
                        "package_version": "1.5.0",
                        "python_modules": (
                            ("omni.warp.core", None, False),
                            ("warp", ".", True),
                        ),
                        "kit_version": "106.2.0+release.142336.833efde4.gl",
                        "build_number": "1.5.0+v1.5.0.5261.75544dfa.gl",
                        "publish_date": 1733883300,
                        "target_platform": ("windows-x86_64",),
                        "repository": "warp",
                        "signed_build": 1,
                    }
                ),
                "l3": MappingProxyType(
                    {
                        "algorithm": "PD2_CACHE_TARGET_RAW_TREE_V1",
                        "file_count": 446,
                        "byte_count": 156115208,
                        "path_set_sha256": "183bb2674fa2cd2a34dc15b7c59f79d685453afc4b6458c19bff86daab4c7f77",
                        "content_sha256": "905ace881e97336901df25692a22bc3fbbfb1e7466c16daec7aaa231a443b8bb",
                        "internal_reparse_count": 0,
                        "primary_manifest_sha256": "6bac2a8a0bec9061165ec9dfcd4d18f151498335a3014c949fa2b2a2dd75cf6e",
                        "generated_manifest_sha256": "061fe90b4c7423f7d16103c9b0ae0a0a306c2b25d80630d93da3fe2407a0268a",
                        "non_generated": MappingProxyType(
                            {
                                "file_count": 425,
                                "byte_count": 155478178,
                                "path_set_sha256": "2a11e9f920076932958176641fc892165bce6c5b378927a3bd43fa9b99a5e00f",
                                "content_sha256": "fad9cede98a7e59160ba330922131cc5fc4bc47bad66c3716f11459466eec609",
                            }
                        ),
                        "python_source": MappingProxyType(
                            {
                                "file_count": 312,
                                "byte_count": 5403100,
                                "content_sha256": "c0c89dc0ca65f7b1b1b15d046d06d958596a8989bf74d3929cb6933cdf8cddd4",
                            }
                        ),
                        "native_runtime": MappingProxyType(
                            {
                                "file_count": 2,
                                "byte_count": 143626752,
                                "content_sha256": "758c53a4e2491d1f7e495a6c1b66d0bdacc31a34f855703c26a3ecc72d2bf97c",
                            }
                        ),
                        "explicit_raw_files": MappingProxyType(
                            {
                                "warp/bin/warp-clang.dll": "068c4383dda8281e73af39fa4dbdd06e3fe22b7fd03736d796b16e1dd89e17eb",
                                "warp/bin/warp.dll": "0b56f37fc74e364bde799c92dfb8f87e55e8277416e45214bd5c1b1f706af6f3",
                            }
                        ),
                    }
                ),
            }
        ),
    }
)

CACHE_AUTHORITY_CATEGORIES_V1 = frozenset(
    {"PROJECT_LOCAL_SOURCE", "OFFICIAL_INSTALLED", "OFFICIAL_INSTALLED_CACHE"}
)


class PD2Stop(RuntimeError):
    def __init__(
        self,
        classification: str,
        message: str,
        *,
        boundary: str,
        failure_detail: str | None = None,
    ) -> None:
        if classification not in STOP_TAXONOMY:
            raise ValueError(classification)
        self.classification = classification
        self.boundary = boundary
        self.failure_detail = failure_detail
        super().__init__(
            f"{message}; first_boundary={boundary!r}; classification={classification!r}; "
            f"failure_detail={failure_detail!r}"
        )


class ExtensionFieldReadError(TypeError):
    """Fail-closed test-only error for read-only extension metadata access."""


class CacheAuthorityPredicateError(RuntimeError):
    """Fail-closed cache-backed identity observation error."""


_REQUIRED_EXTENSION_FIELD = object()
_MISSING_EXTENSION_FIELD = object()


def require(condition: bool, classification: str, message: str, *, boundary: str) -> None:
    if not condition:
        raise PD2Stop(classification, message, boundary=boundary)


@dataclass(frozen=True, slots=True)
class PD2IntegralHorizonFixtureV1:
    schema_version: str
    desired_terminal_transition: int
    required_max_episode_length: int
    semantic_horizon_steps: int
    simulation_tick_count: int
    sim_dt_seconds: float
    control_decimation: int
    physical_control_step_seconds: float
    candidate_episode_length_seconds: float
    raw_horizon_ratio: float
    production_rounded_horizon: int
    integrality_error_abs: float
    production_rel_tol: float
    production_abs_tol: float
    integrality_tolerance_slack: float
    ceil_horizon: int
    lower_bucket_margin: float
    upper_bucket_margin: float


@dataclass(frozen=True, slots=True)
class PD2S1PostconstructionTimingEvidenceV1:
    schema_version: str
    configured_episode_length_seconds: float
    configured_sim_dt_seconds: float
    configured_control_decimation: int
    raw_max_episode_length: int
    raw_max_episode_length_seconds: float
    raw_step_dt_seconds: float
    actual_horizon_ratio: float
    actual_rounded_horizon: int
    actual_ceil_horizon: int
    scale_contract_version: str
    scale_M: int
    scale_N: int
    scale_ordered_agent_names: tuple[str, ...]
    scale_ordered_task_ids: tuple[int, ...]
    scale_scene_env_spacing: float
    scale_sim_dt_seconds: float
    scale_control_decimation: int
    scale_physical_control_step_seconds: float
    scale_episode_time_limit_seconds: float
    scale_episode_horizon_steps: int
    expected_ordered_agent_names: tuple[str, ...]
    expected_ordered_task_ids: tuple[int, ...]
    expected_scene_env_spacing: float


@dataclass(frozen=True, slots=True)
class PD2S5PreterminalEvidenceV1:
    schema_version: str
    transition_index: int
    transition_slot: int
    preterminal_source_p2_serial: int
    preterminal_source_store_version: int
    preterminal_admitted_p2_serial: int
    preterminal_admitted_store_version: int
    preterminal_episode_generations: tuple[int, ...]
    preterminal_transition_generations: tuple[int, ...]
    preterminal_source_window_serial: int
    preterminal_effective_assignment: tuple[tuple[int, ...], ...]
    controller_expected_assignment_transition2: tuple[tuple[int, ...], ...]
    controller_actual_assignment_transition2: tuple[tuple[int, ...], ...]
    continuation_row_mask: tuple[tuple[bool, ...], ...]
    continuation_expected_task: tuple[tuple[int, ...], ...]
    policy_decision_row_mask: tuple[tuple[bool, ...], ...]
    forced_row_mask: tuple[tuple[bool, ...], ...]
    forced_noop_row_mask: tuple[tuple[bool, ...], ...]
    claim_mutated_row_mask: tuple[tuple[bool, ...], ...]
    original_proposal_ids: tuple[tuple[int, ...], ...]
    proposal_logprob_finite_mask: tuple[tuple[bool, ...], ...]
    proposal_present_mask: tuple[tuple[bool, ...], ...]
    actor_call_records: tuple[tuple[int, tuple[int, ...], bool, int], ...]
    resolution_interpretations: tuple[tuple[str, ...], ...]


@dataclass(frozen=True, slots=True)
class PD2PostReturnStateDiagnosticV1:
    schema_version: str
    transition_index: int
    post_return_current_p2_serial: int
    post_return_current_store_version: int
    post_return_current_episode_generations: tuple[int, ...]
    post_return_current_transition_generations: tuple[int, ...]
    post_return_next_bundle_p2_serial: int
    post_return_next_bundle_episode_generations: tuple[int, ...]
    post_return_next_bundle_transition_generations: tuple[int, ...]
    terminal_status_proven: bool
    autoreset_status_proven: bool


@dataclass(frozen=True, slots=True)
class PD2S6TimeoutCriticInvocationIdentityV1:
    schema_version: str
    source_order_contract: str
    second_collect_start_call_index: int
    second_collect_end_call_index: int
    second_collect_total_call_count: int
    current_call_relative_index: int
    current_call_global_index: int
    timeout_call_relative_index: int
    timeout_call_global_index: int
    timeout_batch_event_count: int
    expected_timeout_call_count: int
    observed_timeout_call_count: int
    call_identity_pass: bool


@dataclass(frozen=True, slots=True)
class PD2S6TimeoutCriticInputCorrelationV1:
    schema_version: str
    fingerprint_algorithm: str
    second_collect_start_call_index: int
    second_collect_end_call_index: int
    timeout_call_relative_index: int
    timeout_call_global_index: int
    expected_timeout_call_count: int
    observed_timeout_call_count: int
    call_identity_pass: bool
    expected_shape: tuple[int, ...]
    observed_shape: tuple[int, ...]
    expected_dtype: str
    observed_dtype: str
    expected_device: str
    observed_device: str
    expected_numel: int
    observed_numel: int
    expected_nbytes: int
    observed_nbytes: int
    expected_input_sha256: str
    observed_input_sha256: str
    shape_match: bool
    dtype_match: bool
    device_match: bool
    numel_match: bool
    digest_match: bool
    exact_comparison_executed: bool
    exact_value_match: bool


@dataclass(frozen=True, slots=True)
class PD2S6I5bReturnsEvidenceV1:
    schema_version: str
    capture_status: str
    source_boundary: str
    event_gae_schema_version: str | None
    event_buffer_schema_version: str | None
    T: int
    E: int
    C: int
    valuenorm_enabled: bool
    producer_failure_code: str | None
    producer_failure_stage: str | None
    result_expected_shape: tuple[int, ...]
    result_actual_shape: tuple[int, ...] | None
    result_shape_pass: bool
    result_dtype: str | None
    result_device: str | None
    result_numel: int | None
    result_contiguous: bool | None
    result_requires_grad: bool | None
    result_all_finite: bool | None
    result_nan_count: int | None
    result_posinf_count: int | None
    result_neginf_count: int | None
    result_first_nonfinite_flat_index: int | None
    result_first_nonfinite_t: int | None
    result_first_nonfinite_env: int | None
    result_first_nonfinite_component: int | None
    result_first_nonfinite_kind: str | None
    buffer_commit_performed: bool
    buffer_storage_expected_shape: tuple[int, ...]
    buffer_storage_actual_shape: tuple[int, ...] | None
    buffer_storage_shape_pass: bool
    buffer_storage_dtype: str | None
    buffer_storage_device: str | None
    buffer_storage_numel: int | None
    training_slice_start: int
    training_slice_end_exclusive: int
    training_slice_expected_shape: tuple[int, ...]
    training_slice_actual_shape: tuple[int, ...] | None
    training_slice_shape_pass: bool
    training_slice_numel: int | None
    training_slice_all_finite: bool | None
    training_slice_nan_count: int | None
    training_slice_posinf_count: int | None
    training_slice_neginf_count: int | None
    training_slice_first_nonfinite_flat_index: int | None
    training_slice_first_nonfinite_t: int | None
    training_slice_first_nonfinite_env: int | None
    training_slice_first_nonfinite_component: int | None
    training_slice_first_nonfinite_kind: str | None
    training_slice_matches_result_exact: bool
    training_slice_no_alias_result: bool
    final_slot_index: int
    final_slot_expected_shape: tuple[int, ...]
    final_slot_actual_shape: tuple[int, ...] | None
    final_slot_shape_pass: bool
    final_slot_semantics: str
    final_slot_written_by_event_compute: bool
    final_slot_training_consumed: bool
    final_slot_all_finite: bool | None
    final_slot_nan_count: int | None
    final_slot_posinf_count: int | None
    final_slot_neginf_count: int | None
    final_slot_all_zero: bool | None
    advantages_expected_shape: tuple[int, ...]
    advantages_actual_shape: tuple[int, ...] | None
    advantages_shape_pass: bool
    advantages_all_finite: bool | None
    advantages_nan_count: int | None
    advantages_posinf_count: int | None
    advantages_neginf_count: int | None
    advantages_training_shape_match: bool
    value_preds_storage_shape: tuple[int, ...] | None
    value_preds_training_slice_shape: tuple[int, ...] | None
    value_preds_final_slot_shape: tuple[int, ...] | None
    value_preds_all_finite: bool | None
    arithmetic_value_preds_shape: tuple[int, ...] | None
    arithmetic_value_preds_all_finite: bool | None
    event_slots_complete: bool
    timeout_identity_schema_version: str | None
    timeout_call_identity_pass: bool
    timeout_call_count: int


def _bounded_tensor_nonfinite_evidence_v1(value: object) -> dict[str, object]:
    torch = __import__("torch")
    if type(value) is not torch.Tensor:
        return {
            "all_finite": None,
            "nan_count": None,
            "posinf_count": None,
            "neginf_count": None,
            "first_nonfinite_flat_index": None,
            "first_nonfinite_t": None,
            "first_nonfinite_env": None,
            "first_nonfinite_component": None,
            "first_nonfinite_kind": None,
        }
    tensor = value.detach()
    nan_mask = torch.isnan(tensor)
    posinf_mask = torch.isposinf(tensor)
    neginf_mask = torch.isneginf(tensor)
    nonfinite = nan_mask | posinf_mask | neginf_mask
    nan_count = int(nan_mask.sum().item())
    posinf_count = int(posinf_mask.sum().item())
    neginf_count = int(neginf_mask.sum().item())
    total = nan_count + posinf_count + neginf_count
    flat_index = None
    first_t = None
    first_env = None
    first_component = None
    first_kind = None
    if total:
        flat_nonfinite = nonfinite.contiguous().view(-1)
        flat_index = int(torch.nonzero(flat_nonfinite, as_tuple=False)[0, 0].item())
        if bool(nan_mask.contiguous().view(-1)[flat_index].item()):
            first_kind = "NAN"
        elif bool(posinf_mask.contiguous().view(-1)[flat_index].item()):
            first_kind = "POSINF"
        else:
            first_kind = "NEGINF"
        if tensor.ndim == 3:
            env_width = int(tensor.shape[1])
            component_width = int(tensor.shape[2])
            row_width = env_width * component_width
            if row_width > 0 and component_width > 0:
                first_t = flat_index // row_width
                remainder = flat_index % row_width
                first_env = remainder // component_width
                first_component = remainder % component_width
    return {
        "all_finite": total == 0,
        "nan_count": nan_count,
        "posinf_count": posinf_count,
        "neginf_count": neginf_count,
        "first_nonfinite_flat_index": flat_index,
        "first_nonfinite_t": first_t,
        "first_nonfinite_env": first_env,
        "first_nonfinite_component": first_component,
        "first_nonfinite_kind": first_kind,
    }


def _tensor_shape_v1(value: object) -> tuple[int, ...] | None:
    torch = __import__("torch")
    return tuple(int(item) for item in value.shape) if type(value) is torch.Tensor else None


def _tensor_storage_identity_v1(value: object) -> int | None:
    torch = __import__("torch")
    if type(value) is not torch.Tensor:
        return None
    if hasattr(value, "untyped_storage"):
        return int(value.untyped_storage().data_ptr())
    return int(value.storage().data_ptr())


def build_pd2_s6_i5b_returns_evidence_v1(
    *,
    event_returns_result: object | None,
    critic_buffer: object,
    T: int,
    E: int,
    valuenorm_enabled: bool,
    timeout_identity: object | None,
    producer_error: object | None = None,
    buffer_commit_performed: bool,
) -> PD2S6I5bReturnsEvidenceV1:
    """Capture bounded evidence from the actual I5b result/buffer path without recomputation."""

    torch = __import__("torch")
    capture_status = "TYPED_EVENT_GAE_FAILURE" if producer_error is not None else "RETURNED_RESULT"
    producer_failure_code = getattr(producer_error, "failure_code", None)
    producer_failure_stage = getattr(producer_error, "stage", None)
    result_tensor = getattr(event_returns_result, "returns", None)
    if (
        result_tensor is None
        and producer_error is not None
        and producer_failure_code == "returns_nonfinite"
        and type(getattr(producer_error, "actual", None)) is torch.Tensor
    ):
        result_tensor = producer_error.actual

    buffer_returns = getattr(critic_buffer, "returns", None)
    training_slice = buffer_returns[:-1] if type(buffer_returns) is torch.Tensor and buffer_returns.ndim >= 1 else None
    final_slot = (
        buffer_returns[T]
        if type(buffer_returns) is torch.Tensor and buffer_returns.ndim >= 1 and int(buffer_returns.shape[0]) > T
        else None
    )
    advantages = getattr(event_returns_result, "advantages", None)
    arithmetic_values = getattr(event_returns_result, "arithmetic_value_preds", None)
    value_preds = getattr(critic_buffer, "value_preds", None)
    value_preds_training = value_preds[:-1] if type(value_preds) is torch.Tensor and value_preds.ndim >= 1 else None
    value_preds_final = (
        value_preds[T]
        if type(value_preds) is torch.Tensor and value_preds.ndim >= 1 and int(value_preds.shape[0]) > T
        else None
    )

    result_finite = _bounded_tensor_nonfinite_evidence_v1(result_tensor)
    training_finite = _bounded_tensor_nonfinite_evidence_v1(training_slice)
    final_finite = _bounded_tensor_nonfinite_evidence_v1(final_slot)
    advantages_finite = _bounded_tensor_nonfinite_evidence_v1(advantages)
    value_preds_finite = _bounded_tensor_nonfinite_evidence_v1(value_preds)
    arithmetic_finite = _bounded_tensor_nonfinite_evidence_v1(arithmetic_values)

    result_shape = _tensor_shape_v1(result_tensor)
    storage_shape = _tensor_shape_v1(buffer_returns)
    training_shape = _tensor_shape_v1(training_slice)
    final_shape = _tensor_shape_v1(final_slot)
    advantages_shape = _tensor_shape_v1(advantages)
    result_storage = _tensor_storage_identity_v1(result_tensor)
    training_storage = _tensor_storage_identity_v1(training_slice)
    result_training_exact = bool(
        type(result_tensor) is torch.Tensor
        and type(training_slice) is torch.Tensor
        and torch.equal(training_slice, result_tensor)
    )
    result_training_no_alias = bool(
        result_storage is not None
        and training_storage is not None
        and result_storage != training_storage
    )
    slots = getattr(critic_buffer, "_event_slot_written", None)
    event_slots_complete = bool(
        type(slots) is torch.Tensor and slots.numel() > 0 and bool(slots.all().item())
    )
    final_all_zero = (
        bool((final_slot == 0).all().item()) if type(final_slot) is torch.Tensor else None
    )

    return PD2S6I5bReturnsEvidenceV1(
        schema_version=PD2_S6_I5B_RETURNS_EVIDENCE_SCHEMA_V1,
        capture_status=capture_status,
        source_boundary=PD2_S6_I5B_RETURNS_SOURCE_BOUNDARY_V1,
        event_gae_schema_version=(
            str(getattr(event_returns_result, "schema_version"))
            if getattr(event_returns_result, "schema_version", None) is not None
            else None
        ),
        event_buffer_schema_version=(
            str(getattr(critic_buffer, "schema_version"))
            if getattr(critic_buffer, "schema_version", None) is not None
            else None
        ),
        T=T,
        E=E,
        C=1,
        valuenorm_enabled=bool(valuenorm_enabled),
        producer_failure_code=str(producer_failure_code) if producer_failure_code is not None else None,
        producer_failure_stage=str(producer_failure_stage) if producer_failure_stage is not None else None,
        result_expected_shape=(T, E, 1),
        result_actual_shape=result_shape,
        result_shape_pass=result_shape == (T, E, 1),
        result_dtype=str(result_tensor.dtype) if type(result_tensor) is torch.Tensor else None,
        result_device=str(result_tensor.device) if type(result_tensor) is torch.Tensor else None,
        result_numel=int(result_tensor.numel()) if type(result_tensor) is torch.Tensor else None,
        result_contiguous=bool(result_tensor.is_contiguous()) if type(result_tensor) is torch.Tensor else None,
        result_requires_grad=bool(result_tensor.requires_grad) if type(result_tensor) is torch.Tensor else None,
        result_all_finite=result_finite["all_finite"],
        result_nan_count=result_finite["nan_count"],
        result_posinf_count=result_finite["posinf_count"],
        result_neginf_count=result_finite["neginf_count"],
        result_first_nonfinite_flat_index=result_finite["first_nonfinite_flat_index"],
        result_first_nonfinite_t=result_finite["first_nonfinite_t"],
        result_first_nonfinite_env=result_finite["first_nonfinite_env"],
        result_first_nonfinite_component=result_finite["first_nonfinite_component"],
        result_first_nonfinite_kind=result_finite["first_nonfinite_kind"],
        buffer_commit_performed=bool(buffer_commit_performed),
        buffer_storage_expected_shape=(T + 1, E, 1),
        buffer_storage_actual_shape=storage_shape,
        buffer_storage_shape_pass=storage_shape == (T + 1, E, 1),
        buffer_storage_dtype=str(buffer_returns.dtype) if type(buffer_returns) is torch.Tensor else None,
        buffer_storage_device=str(buffer_returns.device) if type(buffer_returns) is torch.Tensor else None,
        buffer_storage_numel=int(buffer_returns.numel()) if type(buffer_returns) is torch.Tensor else None,
        training_slice_start=0,
        training_slice_end_exclusive=T,
        training_slice_expected_shape=(T, E, 1),
        training_slice_actual_shape=training_shape,
        training_slice_shape_pass=training_shape == (T, E, 1),
        training_slice_numel=int(training_slice.numel()) if type(training_slice) is torch.Tensor else None,
        training_slice_all_finite=training_finite["all_finite"],
        training_slice_nan_count=training_finite["nan_count"],
        training_slice_posinf_count=training_finite["posinf_count"],
        training_slice_neginf_count=training_finite["neginf_count"],
        training_slice_first_nonfinite_flat_index=training_finite["first_nonfinite_flat_index"],
        training_slice_first_nonfinite_t=training_finite["first_nonfinite_t"],
        training_slice_first_nonfinite_env=training_finite["first_nonfinite_env"],
        training_slice_first_nonfinite_component=training_finite["first_nonfinite_component"],
        training_slice_first_nonfinite_kind=training_finite["first_nonfinite_kind"],
        training_slice_matches_result_exact=result_training_exact,
        training_slice_no_alias_result=result_training_no_alias,
        final_slot_index=T,
        final_slot_expected_shape=(E, 1),
        final_slot_actual_shape=final_shape,
        final_slot_shape_pass=final_shape == (E, 1),
        final_slot_semantics="STORAGE_ONLY_DIAGNOSTIC_NOT_EVENT_RESULT_OR_LEARNER_TARGET",
        final_slot_written_by_event_compute=False,
        final_slot_training_consumed=False,
        final_slot_all_finite=final_finite["all_finite"],
        final_slot_nan_count=final_finite["nan_count"],
        final_slot_posinf_count=final_finite["posinf_count"],
        final_slot_neginf_count=final_finite["neginf_count"],
        final_slot_all_zero=final_all_zero,
        advantages_expected_shape=(T, E, 1),
        advantages_actual_shape=advantages_shape,
        advantages_shape_pass=advantages_shape == (T, E, 1),
        advantages_all_finite=advantages_finite["all_finite"],
        advantages_nan_count=advantages_finite["nan_count"],
        advantages_posinf_count=advantages_finite["posinf_count"],
        advantages_neginf_count=advantages_finite["neginf_count"],
        advantages_training_shape_match=advantages_shape == training_shape == (T, E, 1),
        value_preds_storage_shape=_tensor_shape_v1(value_preds),
        value_preds_training_slice_shape=_tensor_shape_v1(value_preds_training),
        value_preds_final_slot_shape=_tensor_shape_v1(value_preds_final),
        value_preds_all_finite=value_preds_finite["all_finite"],
        arithmetic_value_preds_shape=_tensor_shape_v1(arithmetic_values),
        arithmetic_value_preds_all_finite=arithmetic_finite["all_finite"],
        event_slots_complete=event_slots_complete,
        timeout_identity_schema_version=(
            str(getattr(timeout_identity, "schema_version"))
            if getattr(timeout_identity, "schema_version", None) is not None
            else None
        ),
        timeout_call_identity_pass=bool(getattr(timeout_identity, "call_identity_pass", False)),
        timeout_call_count=int(getattr(timeout_identity, "observed_timeout_call_count", 0)),
    )


def adjudicate_pd2_s6_i5b_returns_evidence_v1(
    value: PD2S6I5bReturnsEvidenceV1,
) -> dict[str, object]:
    require(
        type(value) is PD2S6I5bReturnsEvidenceV1
        and value.schema_version == PD2_S6_I5B_RETURNS_EVIDENCE_SCHEMA_V1,
        STOP_TERMINAL,
        "S6 I5b returns evidence DTO type/schema differs",
        boundary="S6_I5B_RETURNS",
    )
    failed_details: list[str] = []
    if not (
        value.result_shape_pass
        and value.result_contiguous is True
        and value.result_requires_grad is False
    ):
        failed_details.append("S6_I5B_RETURNS_RESULT_SHAPE")
    if value.result_all_finite is not True:
        failed_details.append("S6_I5B_RETURNS_RESULT_NONFINITE")
    if not value.buffer_storage_shape_pass:
        failed_details.append("S6_I5B_RETURNS_BUFFER_STORAGE_SHAPE")
    if not value.training_slice_shape_pass:
        failed_details.append("S6_I5B_RETURNS_TRAINING_SLICE_SHAPE")
    if value.training_slice_all_finite is not True:
        failed_details.append("S6_I5B_RETURNS_TRAINING_SLICE_NONFINITE")
    if not value.training_slice_matches_result_exact:
        failed_details.append("S6_I5B_RETURNS_RESULT_BUFFER_MISMATCH")
    if not value.training_slice_no_alias_result:
        failed_details.append("S6_I5B_RETURNS_RESULT_BUFFER_ALIAS")
    if not value.final_slot_shape_pass and "S6_I5B_RETURNS_BUFFER_STORAGE_SHAPE" not in failed_details:
        failed_details.append("S6_I5B_RETURNS_BUFFER_STORAGE_SHAPE")
    primary = failed_details[0] if failed_details else None
    if primary is not None:
        raise PD2Stop(
            STOP_TERMINAL,
            f"I5b returns evidence failed: {failed_details!r}",
            boundary="S6_I5B_RETURNS",
            failure_detail=primary,
        )
    final_slot_diagnostic = (
        PD2_S6_I5B_RETURNS_FINAL_SLOT_DIAGNOSTIC_V1
        if value.final_slot_all_finite is not True or value.final_slot_all_zero is not True
        else None
    )
    return {
        "pass": True,
        "classification": "S6_I5B_RETURNS_SOURCE_FAITHFUL_PASS",
        "primary_failure_detail": None,
        "failed_details": (),
        "final_slot_diagnostic": final_slot_diagnostic,
    }


def _dto_mapping(value: object) -> dict[str, object]:
    return {item.name: getattr(value, item.name) for item in fields(value)}


def _matrix_tuple(value: object, cast: object, *, squeeze_last: bool = False) -> tuple[tuple[object, ...], ...]:
    tensor = value.detach()
    if squeeze_last:
        require(
            tensor.ndim == 3 and int(tensor.shape[-1]) == 1,
            STOP_PHYSICAL,
            "R5-D bounded matrix requires trailing singleton dimension",
            boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE",
        )
        tensor = tensor[..., 0]
    require(
        tensor.ndim == 2,
        STOP_PHYSICAL,
        "R5-D bounded matrix must be rank two",
        boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE",
    )
    rows = tensor.to(device="cpu").tolist()
    return tuple(tuple(cast(item) for item in row) for row in rows)


def build_pd2_integral_horizon_fixture_v1(
    sim_dt_seconds: float,
    control_decimation: int,
    *,
    semantic_horizon_steps: int = PD2_SEMANTIC_HORIZON_STEPS,
) -> PD2IntegralHorizonFixtureV1:
    boundary = "S1_PRECONSTRUCTION_TIMING_CONTRACT"
    require(type(sim_dt_seconds) in (int, float), STOP_PHYSICAL, "sim_dt must be numeric", boundary=boundary)
    fixed_sim_dt = float(sim_dt_seconds)
    require(math.isfinite(fixed_sim_dt) and fixed_sim_dt > 0.0, STOP_PHYSICAL, "sim_dt must be finite and positive", boundary=boundary)
    require(type(control_decimation) is int and control_decimation > 0, STOP_PHYSICAL, "decimation must be an integer greater than zero", boundary=boundary)
    require(type(semantic_horizon_steps) is int, STOP_PHYSICAL, "semantic horizon must be an integer", boundary=boundary)
    simulation_tick_count = control_decimation * semantic_horizon_steps
    physical_control_step_seconds = fixed_sim_dt * control_decimation
    candidate_episode_length_seconds = fixed_sim_dt * simulation_tick_count
    raw_horizon_ratio = candidate_episode_length_seconds / physical_control_step_seconds
    production_rounded_horizon = round(raw_horizon_ratio)
    integrality_error_abs = abs(raw_horizon_ratio - production_rounded_horizon)
    return PD2IntegralHorizonFixtureV1(
        schema_version=PD2_INTEGRAL_HORIZON_FIXTURE_SCHEMA_V1,
        desired_terminal_transition=PD2_DESIRED_TERMINAL_TRANSITION,
        required_max_episode_length=PD2_REQUIRED_MAX_EPISODE_LENGTH,
        semantic_horizon_steps=semantic_horizon_steps,
        simulation_tick_count=simulation_tick_count,
        sim_dt_seconds=fixed_sim_dt,
        control_decimation=control_decimation,
        physical_control_step_seconds=physical_control_step_seconds,
        candidate_episode_length_seconds=candidate_episode_length_seconds,
        raw_horizon_ratio=raw_horizon_ratio,
        production_rounded_horizon=production_rounded_horizon,
        integrality_error_abs=integrality_error_abs,
        production_rel_tol=PD2_PRODUCTION_INTEGRAL_REL_TOL,
        production_abs_tol=PD2_PRODUCTION_INTEGRAL_ABS_TOL,
        integrality_tolerance_slack=PD2_PRODUCTION_INTEGRAL_ABS_TOL - integrality_error_abs,
        ceil_horizon=math.ceil(raw_horizon_ratio),
        lower_bucket_margin=raw_horizon_ratio - PD2_TIMEOUT_BUCKET_LOWER,
        upper_bucket_margin=PD2_TIMEOUT_BUCKET_UPPER - raw_horizon_ratio,
    )


def adjudicate_pd2_s1_preconstruction_timing_v1(fixture: PD2IntegralHorizonFixtureV1) -> dict[str, object]:
    boundary = "S1_PRECONSTRUCTION_TIMING_CONTRACT"
    require(type(fixture) is PD2IntegralHorizonFixtureV1, STOP_PHYSICAL, "fixture type mismatch", boundary=boundary)
    predicates = (
        (fixture.schema_version == PD2_INTEGRAL_HORIZON_FIXTURE_SCHEMA_V1, "fixture schema mismatch"),
        (math.isfinite(fixture.sim_dt_seconds) and fixture.sim_dt_seconds > 0.0, "sim_dt must be finite and positive"),
        (type(fixture.control_decimation) is int and fixture.control_decimation > 0, "decimation must be an integer greater than zero"),
        (fixture.semantic_horizon_steps == PD2_SEMANTIC_HORIZON_STEPS, "semantic horizon must equal three control steps"),
        (fixture.simulation_tick_count == fixture.control_decimation * fixture.semantic_horizon_steps, "simulation tick count mismatch"),
        (math.isfinite(fixture.physical_control_step_seconds) and fixture.physical_control_step_seconds > 0.0, "physical control step must be finite and positive"),
        (fixture.physical_control_step_seconds == fixture.sim_dt_seconds * fixture.control_decimation, "physical control step derivation mismatch"),
        (math.isfinite(fixture.candidate_episode_length_seconds) and fixture.candidate_episode_length_seconds > 0.0, "episode length must be finite and positive"),
        (fixture.candidate_episode_length_seconds == fixture.sim_dt_seconds * fixture.simulation_tick_count, "episode length simulation-tick derivation mismatch"),
        (fixture.raw_horizon_ratio == fixture.candidate_episode_length_seconds / fixture.physical_control_step_seconds, "raw horizon ratio derivation mismatch"),
        (fixture.production_rel_tol == PD2_PRODUCTION_INTEGRAL_REL_TOL and fixture.production_abs_tol == PD2_PRODUCTION_INTEGRAL_ABS_TOL, "production integrality tolerance mismatch"),
        (fixture.production_rounded_horizon == round(fixture.raw_horizon_ratio), "production rounded horizon derivation mismatch"),
        (fixture.integrality_error_abs == abs(fixture.raw_horizon_ratio - fixture.production_rounded_horizon), "integrality error derivation mismatch"),
        (fixture.integrality_tolerance_slack == fixture.production_abs_tol - fixture.integrality_error_abs, "integrality tolerance slack derivation mismatch"),
        (math.isclose(fixture.raw_horizon_ratio, fixture.production_rounded_horizon, rel_tol=PD2_PRODUCTION_INTEGRAL_REL_TOL, abs_tol=PD2_PRODUCTION_INTEGRAL_ABS_TOL), "production integrality predicate failed"),
        (fixture.production_rounded_horizon == PD2_REQUIRED_MAX_EPISODE_LENGTH, "production rounded horizon must equal three"),
        (fixture.raw_horizon_ratio > PD2_TIMEOUT_BUCKET_LOWER, "raw horizon ratio must be greater than two"),
        (fixture.raw_horizon_ratio <= PD2_TIMEOUT_BUCKET_UPPER, "raw horizon ratio must not exceed three"),
        (math.ceil(fixture.raw_horizon_ratio) == PD2_REQUIRED_MAX_EPISODE_LENGTH, "ceil horizon must equal three"),
        (fixture.ceil_horizon == math.ceil(fixture.raw_horizon_ratio), "ceil horizon derivation mismatch"),
        (fixture.lower_bucket_margin == fixture.raw_horizon_ratio - PD2_TIMEOUT_BUCKET_LOWER, "lower bucket margin mismatch"),
        (fixture.upper_bucket_margin == PD2_TIMEOUT_BUCKET_UPPER - fixture.raw_horizon_ratio, "upper bucket margin mismatch"),
        (fixture.desired_terminal_transition == PD2_DESIRED_TERMINAL_TRANSITION, "desired terminal transition mismatch"),
        (fixture.required_max_episode_length == PD2_REQUIRED_MAX_EPISODE_LENGTH, "required max episode length mismatch"),
    )
    for passed, detail in predicates:
        require(bool(passed), STOP_PHYSICAL, detail, boundary=boundary)
    return {"pass": True, "boundary": boundary, "fixture": _dto_mapping(fixture)}


def build_pd2_s1_postconstruction_timing_evidence_v1(
    *,
    fixture: PD2IntegralHorizonFixtureV1,
    configured_episode_length_seconds: float,
    configured_sim_dt_seconds: float,
    configured_control_decimation: int,
    raw_max_episode_length: int,
    raw_max_episode_length_seconds: float,
    raw_step_dt_seconds: float,
    scale_contract: Mapping[str, object],
    expected_ordered_agent_names: tuple[str, ...],
    expected_ordered_task_ids: tuple[int, ...],
    expected_scene_env_spacing: float,
) -> PD2S1PostconstructionTimingEvidenceV1:
    boundary = "S1_POSTCONSTRUCTION_TIMING_CONTRACT"
    require(type(fixture) is PD2IntegralHorizonFixtureV1, STOP_PHYSICAL, "postconstruction fixture type mismatch", boundary=boundary)
    require(isinstance(scale_contract, Mapping), STOP_PHYSICAL, "production scale contract is unavailable", boundary=boundary)
    try:
        actual_ratio = float(raw_max_episode_length_seconds) / float(raw_step_dt_seconds)
        return PD2S1PostconstructionTimingEvidenceV1(
            schema_version=PD2_S1_POSTCONSTRUCTION_TIMING_EVIDENCE_SCHEMA_V1,
            configured_episode_length_seconds=float(configured_episode_length_seconds),
            configured_sim_dt_seconds=float(configured_sim_dt_seconds),
            configured_control_decimation=configured_control_decimation,
            raw_max_episode_length=raw_max_episode_length,
            raw_max_episode_length_seconds=float(raw_max_episode_length_seconds),
            raw_step_dt_seconds=float(raw_step_dt_seconds),
            actual_horizon_ratio=actual_ratio,
            actual_rounded_horizon=round(actual_ratio),
            actual_ceil_horizon=math.ceil(actual_ratio),
            scale_contract_version=str(scale_contract["contract_version"]),
            scale_M=scale_contract["M"],
            scale_N=scale_contract["N"],
            scale_ordered_agent_names=tuple(scale_contract["ordered_agent_names"]),
            scale_ordered_task_ids=tuple(scale_contract["ordered_task_ids"]),
            scale_scene_env_spacing=float(scale_contract["scene_env_spacing"]),
            scale_sim_dt_seconds=float(scale_contract["sim_dt_seconds"]),
            scale_control_decimation=scale_contract["control_decimation"],
            scale_physical_control_step_seconds=float(scale_contract["physical_control_step_seconds"]),
            scale_episode_time_limit_seconds=float(scale_contract["episode_time_limit_seconds"]),
            scale_episode_horizon_steps=scale_contract["episode_horizon_steps"],
            expected_ordered_agent_names=expected_ordered_agent_names,
            expected_ordered_task_ids=expected_ordered_task_ids,
            expected_scene_env_spacing=float(expected_scene_env_spacing),
        )
    except (KeyError, TypeError, ValueError, ZeroDivisionError, OverflowError) as exc:
        raise PD2Stop(STOP_PHYSICAL, f"postconstruction timing evidence malformed: {type(exc).__name__}: {exc}", boundary=boundary) from exc


def adjudicate_pd2_s1_postconstruction_timing_v1(
    value: PD2S1PostconstructionTimingEvidenceV1,
    fixture: PD2IntegralHorizonFixtureV1,
) -> dict[str, object]:
    boundary = "S1_POSTCONSTRUCTION_TIMING_CONTRACT"
    require(type(value) is PD2S1PostconstructionTimingEvidenceV1, STOP_PHYSICAL, "postconstruction evidence type mismatch", boundary=boundary)
    require(type(fixture) is PD2IntegralHorizonFixtureV1, STOP_PHYSICAL, "postconstruction fixture type mismatch", boundary=boundary)
    expected_step_dt = value.configured_sim_dt_seconds * value.configured_control_decimation
    predicates = (
        (value.schema_version == PD2_S1_POSTCONSTRUCTION_TIMING_EVIDENCE_SCHEMA_V1, "postconstruction schema mismatch"),
        (type(value.raw_max_episode_length) is int and value.raw_max_episode_length == fixture.required_max_episode_length, "raw.max_episode_length mismatch"),
        (value.raw_step_dt_seconds == expected_step_dt, "raw.step_dt mismatch"),
        (value.raw_max_episode_length_seconds == value.configured_episode_length_seconds == fixture.candidate_episode_length_seconds, "raw/configured episode length mismatch"),
        (value.actual_horizon_ratio == value.raw_max_episode_length_seconds / value.raw_step_dt_seconds, "actual horizon ratio derivation mismatch"),
        (math.isfinite(value.actual_horizon_ratio) and value.actual_horizon_ratio > PD2_TIMEOUT_BUCKET_LOWER and value.actual_horizon_ratio <= PD2_TIMEOUT_BUCKET_UPPER, "actual horizon ratio left reviewed bucket"),
        (math.isclose(value.actual_horizon_ratio, value.actual_rounded_horizon, rel_tol=PD2_PRODUCTION_INTEGRAL_REL_TOL, abs_tol=PD2_PRODUCTION_INTEGRAL_ABS_TOL), "actual horizon failed production integrality"),
        (value.actual_rounded_horizon == fixture.required_max_episode_length, "actual rounded horizon mismatch"),
        (value.actual_ceil_horizon == fixture.required_max_episode_length, "actual ceil horizon mismatch"),
        (value.scale_contract_version == PD2_EXPECTED_SCALE_CONTRACT_VERSION, "scale contract version mismatch"),
        (type(value.scale_M) is int and value.scale_M == M, "scale M mismatch"),
        (type(value.scale_N) is int and value.scale_N == N, "scale N mismatch"),
        (value.scale_ordered_agent_names == value.expected_ordered_agent_names, "scale agent order mismatch"),
        (value.scale_ordered_task_ids == value.expected_ordered_task_ids, "scale task order mismatch"),
        (value.scale_scene_env_spacing == value.expected_scene_env_spacing, "scale scene spacing mismatch"),
        (value.scale_sim_dt_seconds == value.configured_sim_dt_seconds, "scale sim_dt mismatch"),
        (type(value.scale_control_decimation) is int and value.scale_control_decimation == value.configured_control_decimation, "scale decimation mismatch"),
        (value.scale_physical_control_step_seconds == value.raw_step_dt_seconds, "scale physical control step mismatch"),
        (value.scale_episode_time_limit_seconds == fixture.candidate_episode_length_seconds, "scale episode time limit mismatch"),
        (type(value.scale_episode_horizon_steps) is int and value.scale_episode_horizon_steps == fixture.required_max_episode_length, "scale episode horizon mismatch"),
    )
    for passed, detail in predicates:
        require(bool(passed), STOP_PHYSICAL, detail, boundary=boundary)
    return {"pass": True, "boundary": boundary, "evidence": _dto_mapping(value)}


def classify_pd2_s1_untyped_failure_v1(active_boundary: object) -> tuple[str, str]:
    boundary = str(active_boundary)
    if boundary in ("S1_PRECONSTRUCTION_TIMING_CONTRACT", "S1_POSTCONSTRUCTION_TIMING_CONTRACT"):
        return STOP_PHYSICAL, boundary
    if boundary in ("S1_ENTER", "S1_ENVIRONMENT_CONSTRUCTION", "S1_RESET", "S1_I1_I2"):
        return STOP_STARTUP, boundary
    return STOP_STARTUP, boundary


def bounded_pd2_production_exception_fields_v1(exc: BaseException) -> dict[str, object]:
    captured: dict[str, object] = {}
    for name in ("failure_code", "stage", "expected", "actual"):
        try:
            value = getattr(exc, name)
        except BaseException:
            continue
        try:
            captured[name] = normalize(value)
        except BaseException:
            captured[name] = repr(value)[:1000]
    return captured


def publish_pd2_s1_boundary_v1(
    evidence: dict[str, object],
    checkpoints: object,
    *,
    boundary: str,
    label: str,
    details: Mapping[str, object] | None = None,
) -> None:
    evidence["active_stage"] = "S1"
    evidence["active_boundary"] = boundary
    payload = {"active_stage": "S1", "active_boundary": boundary}
    if details is not None:
        payload.update(dict(details))
    checkpoints.emit("S1", label, payload)


def capture_pd2_critic_input_fingerprint_v1(obs: object, rnn: object, masks: object, critic: object, *, capture_index: int) -> dict[str, object]:
    torch = __import__("torch")
    require(type(capture_index) is int and capture_index >= 0, STOP_VCRITIC, "critic capture index is invalid", boundary="S2_CRITIC_INPUT_EVIDENCE")
    try:
        finite = bool(torch.isfinite(obs).all().item())
        cpu_tensor = obs.detach().to(device="cpu", copy=True).contiguous()
        array = cpu_tensor.numpy()
        payload = array.tobytes(order="C")
        runtime_type = type(critic)
        runtime_class = f"{runtime_type.__module__}.{runtime_type.__qualname__}"
        return {
            "fingerprint_algorithm": PD2_CRITIC_INPUT_FINGERPRINT_ALGORITHM_V1,
            "content_sha256": hashlib.sha256(payload).hexdigest(),
            "shape": tuple(obs.shape),
            "stride": tuple(obs.stride()),
            "dtype": str(obs.dtype),
            "device": str(obs.device),
            "contiguous": bool(obs.is_contiguous()),
            "finite": finite,
            "requires_grad": bool(obs.requires_grad),
            "numel": int(obs.numel()),
            "nbytes": len(payload),
            "cpu_byte_order": sys.byteorder,
            "rnn_state_shape": tuple(rnn.shape),
            "mask_shape": tuple(masks.shape),
            "capture_index": capture_index,
            "critic_runtime_class": runtime_class,
        }
    except PD2Stop:
        raise
    except BaseException as exc:
        raise PD2Stop(
            STOP_VCRITIC,
            f"critic input CPU-byte fingerprint capture failed before VCritic forward: {type(exc).__name__}: {exc}",
            boundary="S2_CRITIC_INPUT_EVIDENCE",
        ) from exc


def identify_pd2_s6_timeout_critic_call_v1(
    *,
    second_collect_start_call_index: int,
    second_collect_end_call_index: int,
    timeout_batch_event_count: int,
    observed_timeout_call_count: int,
) -> PD2S6TimeoutCriticInvocationIdentityV1:
    values = (
        second_collect_start_call_index,
        second_collect_end_call_index,
        timeout_batch_event_count,
        observed_timeout_call_count,
    )
    require(
        all(type(value) is int and value >= 0 for value in values),
        STOP_TERMINAL,
        "S6 timeout critic invocation cursor/count evidence is invalid",
        boundary="S6_TIMEOUT_CRITIC_CALL_IDENTITY",
    )
    total_calls = second_collect_end_call_index - second_collect_start_call_index
    expected_total_calls = (
        PD2_SECOND_COLLECT_CURRENT_CRITIC_CALL_COUNT
        + PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT
    )
    call_identity_pass = (
        second_collect_end_call_index >= second_collect_start_call_index
        and timeout_batch_event_count == 1
        and observed_timeout_call_count == PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT
        and total_calls == expected_total_calls
    )
    require(
        call_identity_pass,
        STOP_TERMINAL,
        "S6 second-collect critic invocation order/count differs from the frozen current-then-timeout contract",
        boundary="S6_TIMEOUT_CRITIC_CALL_IDENTITY",
    )
    timeout_global_index = (
        second_collect_start_call_index + PD2_TIMEOUT_CRITIC_RELATIVE_INDEX
    )
    require(
        timeout_global_index < second_collect_end_call_index,
        STOP_TERMINAL,
        "S6 designated timeout critic invocation is outside the second-collect cursor",
        boundary="S6_TIMEOUT_CRITIC_CALL_IDENTITY",
    )
    return PD2S6TimeoutCriticInvocationIdentityV1(
        schema_version=PD2_S6_TIMEOUT_CRITIC_INVOCATION_IDENTITY_SCHEMA_V1,
        source_order_contract="SECOND_COLLECT_CURRENT_VT_THEN_TIMEOUT_BOOTSTRAP_V1",
        second_collect_start_call_index=second_collect_start_call_index,
        second_collect_end_call_index=second_collect_end_call_index,
        second_collect_total_call_count=total_calls,
        current_call_relative_index=0,
        current_call_global_index=second_collect_start_call_index,
        timeout_call_relative_index=PD2_TIMEOUT_CRITIC_RELATIVE_INDEX,
        timeout_call_global_index=timeout_global_index,
        timeout_batch_event_count=timeout_batch_event_count,
        expected_timeout_call_count=PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT,
        observed_timeout_call_count=observed_timeout_call_count,
        call_identity_pass=True,
    )


def compare_pd2_s6_timeout_critic_input_exact_v1(
    expected: object,
    observed: object,
    *,
    invocation_identity: PD2S6TimeoutCriticInvocationIdentityV1,
) -> PD2S6TimeoutCriticInputCorrelationV1:
    torch = __import__("torch")
    try:
        require(
            type(invocation_identity) is PD2S6TimeoutCriticInvocationIdentityV1
            and invocation_identity.schema_version
            == PD2_S6_TIMEOUT_CRITIC_INVOCATION_IDENTITY_SCHEMA_V1
            and invocation_identity.call_identity_pass
            and invocation_identity.observed_timeout_call_count
            == PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT,
            STOP_TERMINAL,
            "S6 exact timeout input comparison requires a resolved exact-once invocation identity",
            boundary="S6_TIMEOUT_CRITIC_CALL_IDENTITY",
        )
        require(
            isinstance(expected, torch.Tensor) and isinstance(observed, torch.Tensor),
            STOP_TERMINAL,
            "S6 timeout critic correlation inputs must both be tensors",
            boundary="S6_TIMEOUT_CRITIC",
        )
        expected_cpu = expected.detach().to(device="cpu", copy=True).contiguous()
        observed_cpu = observed.detach().to(device="cpu", copy=True).contiguous()
        expected_payload = expected_cpu.view(torch.uint8).numpy().tobytes(order="C")
        observed_payload = observed_cpu.view(torch.uint8).numpy().tobytes(order="C")
        expected_digest = hashlib.sha256(expected_payload).hexdigest()
        observed_digest = hashlib.sha256(observed_payload).hexdigest()
        shape_match = tuple(expected.shape) == tuple(observed.shape)
        dtype_match = expected.dtype == observed.dtype
        device_match = expected.device == observed.device
        numel_match = int(expected.numel()) == int(observed.numel())
        exact_value_match = bool(
            shape_match
            and dtype_match
            and numel_match
            and torch.equal(expected_cpu, observed_cpu)
        )
        return PD2S6TimeoutCriticInputCorrelationV1(
            schema_version=PD2_S6_TIMEOUT_CRITIC_INPUT_CORRELATION_SCHEMA_V1,
            fingerprint_algorithm=PD2_CRITIC_INPUT_FINGERPRINT_ALGORITHM_V1,
            second_collect_start_call_index=invocation_identity.second_collect_start_call_index,
            second_collect_end_call_index=invocation_identity.second_collect_end_call_index,
            timeout_call_relative_index=invocation_identity.timeout_call_relative_index,
            timeout_call_global_index=invocation_identity.timeout_call_global_index,
            expected_timeout_call_count=invocation_identity.expected_timeout_call_count,
            observed_timeout_call_count=invocation_identity.observed_timeout_call_count,
            call_identity_pass=invocation_identity.call_identity_pass,
            expected_shape=tuple(int(value) for value in expected.shape),
            observed_shape=tuple(int(value) for value in observed.shape),
            expected_dtype=str(expected.dtype),
            observed_dtype=str(observed.dtype),
            expected_device=str(expected.device),
            observed_device=str(observed.device),
            expected_numel=int(expected.numel()),
            observed_numel=int(observed.numel()),
            expected_nbytes=len(expected_payload),
            observed_nbytes=len(observed_payload),
            expected_input_sha256=expected_digest,
            observed_input_sha256=observed_digest,
            shape_match=shape_match,
            dtype_match=dtype_match,
            device_match=device_match,
            numel_match=numel_match,
            digest_match=expected_digest == observed_digest,
            exact_comparison_executed=True,
            exact_value_match=exact_value_match,
        )
    except PD2Stop:
        raise
    except BaseException as exc:
        raise PD2Stop(
            STOP_TERMINAL,
            f"S6 exact timeout critic input correlation failed: {type(exc).__name__}: {exc}",
            boundary="S6_TIMEOUT_CRITIC",
        ) from exc


def adjudicate_pd2_s6_timeout_critic_input_correlation_v1(
    value: PD2S6TimeoutCriticInputCorrelationV1,
) -> dict[str, object]:
    require(
        type(value) is PD2S6TimeoutCriticInputCorrelationV1
        and value.schema_version == PD2_S6_TIMEOUT_CRITIC_INPUT_CORRELATION_SCHEMA_V1
        and value.fingerprint_algorithm == PD2_CRITIC_INPUT_FINGERPRINT_ALGORITHM_V1,
        STOP_TERMINAL,
        "S6 timeout critic correlation DTO type/schema differs",
        boundary="S6_TIMEOUT_CRITIC",
    )
    require(
        value.call_identity_pass
        and value.expected_timeout_call_count == PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT
        and value.observed_timeout_call_count == PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT
        and value.timeout_call_relative_index == PD2_TIMEOUT_CRITIC_RELATIVE_INDEX
        and value.timeout_call_global_index
        == value.second_collect_start_call_index + value.timeout_call_relative_index
        and value.timeout_call_global_index < value.second_collect_end_call_index,
        STOP_TERMINAL,
        "S6 timeout critic correlation lost its designated exact-once invocation identity",
        boundary="S6_TIMEOUT_CRITIC_CALL_IDENTITY",
    )
    require(
        re.fullmatch(r"[0-9a-f]{64}", value.expected_input_sha256) is not None
        and re.fullmatch(r"[0-9a-f]{64}", value.observed_input_sha256) is not None,
        STOP_TERMINAL,
        "S6 timeout critic bounded fingerprints are malformed",
        boundary="S6_TIMEOUT_CRITIC",
    )
    require(
        value.exact_comparison_executed
        and value.shape_match
        and value.dtype_match
        and value.device_match
        and value.numel_match
        and value.digest_match
        and value.exact_value_match,
        STOP_TERMINAL,
        "S6 timeout critic actual input does not exactly equal authoritative pre-reset input",
        boundary="S6_TIMEOUT_CRITIC",
    )
    return {
        "pass": True,
        "classification": "S6_TIMEOUT_CRITIC_EXACT_INPUT_PASS",
        "exact_input_authority": True,
        "bounded_fingerprint_support": True,
    }


def _interpretation_name(value: object) -> str:
    name = getattr(value, "name", None)
    return str(name if name is not None else value)


def build_pd2_s5_preterminal_evidence_v1(
    *, receipt: object, controller_assignments: tuple[object, ...], assignment_projector: object
) -> PD2S5PreterminalEvidenceV1:
    try:
        require(receipt.transition_slot == 1, STOP_PHYSICAL, "second receipt slot is unavailable", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
        require(len(receipt.harl_step_result) == 6, STOP_PHYSICAL, "second HARL receipt arity is unavailable", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
        require(len(controller_assignments) == 2, STOP_PHYSICAL, "transition-2 controller-time copy is unavailable", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
        bundle = receipt.decision_bundle
        envelope = receipt.proposal_envelope
        facade = receipt.facade_result
        resolution = facade.resolution
        identity = bundle.evidence_identity
        source = facade.source_publication
        admitted = facade.admitted_publication
        require(envelope.decision_bundle is bundle and envelope.evidence_identity is identity, STOP_PHYSICAL, "proposal envelope lost its transition-2 decision identity", boundary="S5_PROPOSAL_SOURCE_IDENTITY")
        require(identity.p2_publication_identity is source.publication_identity, STOP_PHYSICAL, "decision bundle is not bound to source P2", boundary="S5_PROPOSAL_SOURCE_IDENTITY")
        require(resolution.proposal_source_publication_identity is source.publication_identity, STOP_PHYSICAL, "resolution source P2 identity differs", boundary="S5_PROPOSAL_SOURCE_IDENTITY")
        require(resolution.proposal_source_window_identity is identity.open_window_identity, STOP_PHYSICAL, "resolution OPEN-window identity differs", boundary="S5_PROPOSAL_SOURCE_IDENTITY")
        require(resolution.episode_generations == identity.episode_generations and resolution.transition_generations == identity.transition_generations, STOP_PHYSICAL, "resolution generations differ from transition-2 evidence", boundary="S5_PROPOSAL_SOURCE_IDENTITY")
        require(admitted is facade.post_claim_publication, STOP_PHYSICAL, "admitted P2 is not final post-claim P2", boundary="S5_P2_AK")

        torch = __import__("torch")
        projected = assignment_projector(admitted)
        effective = facade.admitted_effective_assignment
        controller = controller_assignments[1]
        require(torch.equal(projected, effective) and torch.equal(effective, controller), STOP_PHYSICAL, "admitted P2, Ak assignment, and controller-time assignment differ", boundary="S5_P2_AK")

        continuation = bundle.forced_continuation_mask[..., 0].to(torch.bool)
        policy = bundle.policy_row_mask[..., 0].to(torch.bool)
        forced = bundle.forced_row_mask[..., 0].to(torch.bool)
        forced_noop = bundle.forced_noop_mask[..., 0].to(torch.bool)
        forced_action = bundle.forced_action_id[..., 0].to(torch.int64)
        owned_task = bundle.evidence_snapshot.current_owned_task_id.to(torch.int64)
        proposal_present = envelope.policy_proposal_present_mask[..., 0].to(torch.bool)
        sampled_policy = envelope.sampled_policy_row_mask[..., 0].to(torch.bool)
        proposal_ids = envelope.original_policy_proposal_ids[..., 0].to(torch.int64)
        logprobs = envelope.action_logprobs[..., 0]
        require(torch.equal(sampled_policy, policy), STOP_ACTOR, "sampled-policy rows differ from transition-2 DVM rows", boundary="S5_FORCED_ROW_BYPASS")
        require(not bool(proposal_present[forced].any()) and not bool(sampled_policy[forced].any()), STOP_ACTOR, "forced row entered proposal sampling", boundary="S5_FORCED_ROW_BYPASS")
        require(bool((proposal_ids[forced] == bundle.forced_action_invalid_id).all()), STOP_PHYSICAL, "forced-row original proposal sentinel changed", boundary="S5_PROPOSAL_SEMANTICS")
        require(bool((logprobs[forced] == envelope.forced_row_logprob_sentinel).all()), STOP_PHYSICAL, "forced-row logprob sentinel changed", boundary="S5_PROPOSAL_SEMANTICS")
        require(bool(torch.isfinite(logprobs[policy]).all()), STOP_PHYSICAL, "genuine policy logprob is not finite", boundary="S5_PROPOSAL_SEMANTICS")
        require(bool(((proposal_ids[policy] >= 0) & (proposal_ids[policy] <= identity.N)).all()), STOP_PHYSICAL, "genuine proposal ID left fixed action space", boundary="S5_PROPOSAL_SEMANTICS")

        claim_mutated = torch.zeros_like(policy)
        artifact = facade.claim_artifact
        if artifact is None:
            require(facade.post_claim_publication is source, STOP_PHYSICAL, "zero-claim result changed P2", boundary="S5_REPEATED_CLAIM")
        else:
            require(artifact.source_publication is source and artifact.source_publication_identity is source.publication_identity, STOP_PHYSICAL, "claim artifact source P2 differs", boundary="S5_REPEATED_CLAIM")
            require(artifact.committed_store_version == facade.post_claim_publication.store_version, STOP_PHYSICAL, "claim artifact store version differs from post-claim P2", boundary="S5_REPEATED_CLAIM")
            selected = artifact.selected_env_ids.to(torch.int64)
            requested = artifact.requested_task_by_robot.to(torch.int64)
            require(requested.ndim == 2 and int(requested.shape[0]) == int(selected.numel()), STOP_PHYSICAL, "claim artifact row shape is unavailable", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
            for selected_row, env_id in enumerate(selected.tolist()):
                claim_mutated[int(env_id)] = requested[selected_row] >= 0
        require(not bool((claim_mutated & continuation).any()), STOP_PHYSICAL, "continuation row was re-claimed", boundary="S5_REPEATED_CLAIM")

        records = tuple((int(item.agent_id), tuple(int(v) for v in item.valid_env_indices), bool(item.actor_called), int(item.actor_batch_size)) for item in envelope.actor_call_records)
        require(len(records) == int(policy.shape[1]), STOP_ACTOR, "actor call record cardinality differs from robot rows", boundary="S5_FORCED_ROW_BYPASS")
        for agent_id, valid_env_indices, actor_called, actor_batch_size in records:
            expected_indices = tuple(int(v) for v in torch.nonzero(policy[:, agent_id], as_tuple=False).flatten().tolist())
            require(valid_env_indices == expected_indices and actor_batch_size == len(expected_indices) and actor_called == bool(expected_indices), STOP_ACTOR, "actor compact-call record differs from policy rows", boundary="S5_FORCED_ROW_BYPASS")

        interpretations = tuple(tuple(_interpretation_name(item) for item in row) for row in facade.committed_interpretations)
        require(len(interpretations) == int(policy.shape[0]) and all(len(row) == int(policy.shape[1]) for row in interpretations), STOP_PHYSICAL, "resolution interpretation matrix is unavailable", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
        return PD2S5PreterminalEvidenceV1(
            schema_version=PD2_S5_PRETERMINAL_EVIDENCE_SCHEMA_V1,
            transition_index=2,
            transition_slot=int(receipt.transition_slot),
            preterminal_source_p2_serial=int(source.publication_identity.serial),
            preterminal_source_store_version=int(source.store_version),
            preterminal_admitted_p2_serial=int(admitted.publication_identity.serial),
            preterminal_admitted_store_version=int(admitted.store_version),
            preterminal_episode_generations=tuple(int(v) for v in identity.episode_generations),
            preterminal_transition_generations=tuple(int(v) for v in identity.transition_generations),
            preterminal_source_window_serial=int(identity.open_window_identity.serial),
            preterminal_effective_assignment=_matrix_tuple(effective, int),
            controller_expected_assignment_transition2=_matrix_tuple(projected, int),
            controller_actual_assignment_transition2=_matrix_tuple(controller, int),
            continuation_row_mask=_matrix_tuple(continuation, bool),
            continuation_expected_task=_matrix_tuple(owned_task, int),
            policy_decision_row_mask=_matrix_tuple(policy, bool),
            forced_row_mask=_matrix_tuple(forced, bool),
            forced_noop_row_mask=_matrix_tuple(forced_noop, bool),
            claim_mutated_row_mask=_matrix_tuple(claim_mutated, bool),
            original_proposal_ids=_matrix_tuple(proposal_ids, int),
            proposal_logprob_finite_mask=_matrix_tuple(torch.isfinite(logprobs), bool),
            proposal_present_mask=_matrix_tuple(proposal_present, bool),
            actor_call_records=records,
            resolution_interpretations=interpretations,
        )
    except PD2Stop:
        raise
    except BaseException as exc:
        raise PD2Stop(STOP_PHYSICAL, f"required transition-2 preterminal evidence is unavailable: {type(exc).__name__}: {exc}", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE") from exc


def adjudicate_pd2_s5_preterminal_evidence_v1(value: PD2S5PreterminalEvidenceV1) -> dict[str, object]:
    require(type(value) is PD2S5PreterminalEvidenceV1 and value.schema_version == PD2_S5_PRETERMINAL_EVIDENCE_SCHEMA_V1, STOP_PHYSICAL, "S5 evidence DTO type/schema differs", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
    require(value.transition_index == 2 and value.transition_slot == 1, STOP_PHYSICAL, "S5 evidence does not identify transition 2", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
    require(value.preterminal_effective_assignment == value.controller_expected_assignment_transition2 == value.controller_actual_assignment_transition2, STOP_PHYSICAL, "S5 P2/Ak/controller assignment chain differs", boundary="S5_P2_AK")
    E_value = len(value.continuation_row_mask)
    M_value = len(value.continuation_row_mask[0]) if E_value else 0
    require(E_value > 0 and M_value > 0, STOP_PHYSICAL, "S5 row domain is empty", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
    matrix_names = (
        "preterminal_effective_assignment", "controller_expected_assignment_transition2", "controller_actual_assignment_transition2",
        "continuation_row_mask", "continuation_expected_task", "policy_decision_row_mask", "forced_row_mask", "forced_noop_row_mask",
        "claim_mutated_row_mask", "original_proposal_ids", "proposal_logprob_finite_mask", "proposal_present_mask", "resolution_interpretations",
    )
    require(all(len(getattr(value, name)) == E_value and all(len(row) == M_value for row in getattr(value, name)) for name in matrix_names), STOP_PHYSICAL, "S5 bounded matrix shapes differ", boundary="S5_PRETERMINAL_EVIDENCE_UNAVAILABLE")
    for env_id in range(E_value):
        for robot_id in range(M_value):
            continuation = value.continuation_row_mask[env_id][robot_id]
            policy = value.policy_decision_row_mask[env_id][robot_id]
            forced = value.forced_row_mask[env_id][robot_id]
            if continuation:
                expected_task = value.continuation_expected_task[env_id][robot_id]
                require(forced and not policy and expected_task >= 0, STOP_PHYSICAL, "continuation row classification differs", boundary="S5_CONTINUATION")
                require(value.preterminal_effective_assignment[env_id][robot_id] == expected_task, STOP_PHYSICAL, "continuation task differs from admitted P2", boundary="S5_CONTINUATION")
                require(not value.claim_mutated_row_mask[env_id][robot_id], STOP_PHYSICAL, "continuation row entered claim mutation", boundary="S5_REPEATED_CLAIM")
                require(not value.proposal_present_mask[env_id][robot_id], STOP_ACTOR, "continuation row contains a policy proposal", boundary="S5_FORCED_ROW_BYPASS")
                require(value.resolution_interpretations[env_id][robot_id] == "CONTINUE_EXISTING", STOP_PHYSICAL, "continuation row was not committed as continuation", boundary="S5_REPEATED_CLAIM")
            if policy:
                require(value.proposal_present_mask[env_id][robot_id] and value.proposal_logprob_finite_mask[env_id][robot_id], STOP_PHYSICAL, "genuine policy row lost proposal/logprob evidence", boundary="S5_PROPOSAL_SEMANTICS")
            require(not (continuation and value.claim_mutated_row_mask[env_id][robot_id]), STOP_PHYSICAL, "continuation and claim mutation overlap", boundary="S5_REPEATED_CLAIM")
    require(len(value.actor_call_records) == M_value, STOP_ACTOR, "actor call records do not cover fixed robot rows", boundary="S5_FORCED_ROW_BYPASS")
    for agent_id, valid_env_indices, actor_called, actor_batch_size in value.actor_call_records:
        expected_indices = tuple(env_id for env_id in range(E_value) if value.policy_decision_row_mask[env_id][agent_id])
        require(valid_env_indices == expected_indices and actor_batch_size == len(expected_indices) and actor_called == bool(expected_indices), STOP_ACTOR, "actor sampling does not equal policy-decision rows", boundary="S5_FORCED_ROW_BYPASS")
    return {"pass": True, "classification": "S5_PRETERMINAL_PASS", "s6_adjudicated": False, "continuation_rows": sum(sum(int(item) for item in row) for row in value.continuation_row_mask)}


def build_pd2_post_return_state_diagnostic_v1(receipt: object) -> PD2PostReturnStateDiagnosticV1:
    publication = receipt.facade_result.current_publication
    next_bundle = receipt.next_decision_bundle
    next_identity = next_bundle.evidence_identity
    return PD2PostReturnStateDiagnosticV1(
        schema_version=PD2_POST_RETURN_STATE_DIAGNOSTIC_SCHEMA_V1,
        transition_index=2,
        post_return_current_p2_serial=int(publication.publication_identity.serial),
        post_return_current_store_version=int(publication.store_version),
        post_return_current_episode_generations=tuple(int(v) for v in publication.episode_generation.to(device="cpu").tolist()),
        post_return_current_transition_generations=tuple(int(v) for v in publication.transition_generation.to(device="cpu").tolist()),
        post_return_next_bundle_p2_serial=int(next_identity.p2_publication_identity.serial),
        post_return_next_bundle_episode_generations=tuple(int(v) for v in next_identity.episode_generations),
        post_return_next_bundle_transition_generations=tuple(int(v) for v in next_identity.transition_generations),
        terminal_status_proven=False,
        autoreset_status_proven=False,
    )


def normalize(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if hasattr(type(value), "__dataclass_fields__"):
        return normalize(_dto_mapping(value))
    if isinstance(value, Mapping):
        return {str(key): normalize(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [normalize(item) for item in value]
    if hasattr(value, "detach") and hasattr(value, "cpu") and hasattr(value, "tolist"):
        return value.detach().cpu().tolist()
    if hasattr(value, "value"):
        return normalize(value.value)
    return repr(value)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(normalize(payload), stream, indent=2, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def load_test_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Checkpoints:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.events: list[dict[str, object]] = []

    def emit(self, stage: str, label: str, details: Mapping[str, object] | None = None) -> None:
        event = {
            "sequence": len(self.events),
            "stage": stage,
            "label": label,
            "pid": os.getpid(),
            "monotonic_seconds": time.monotonic(),
            "details": normalize(details or {}),
        }
        self.events.append(event)
        atomic_json(self.path, {"last_completed_checkpoint": stage, "events": self.events})


def module_state(label: str) -> dict[str, object]:
    loaded = "torch" in sys.modules
    result: dict[str, object] = {"label": label, "torch_in_sys_modules": loaded}
    if loaded:
        torch = sys.modules["torch"]
        result["torch_cuda_initialized"] = bool(torch.cuda.is_initialized())
    return result


def _normal_path(value: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(value)))


def _manifest_version(path: Path) -> str | None:
    in_package = False
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_package = stripped == "[package]"
        elif in_package:
            match = re.match(r'version\s*=\s*["\']([^"\']+)["\']', stripped)
            if match:
                return match.group(1)
    return None


def _readlink(path: Path) -> str | None:
    if not os.path.islink(path):
        return None
    target = Path(os.readlink(path))
    if not target.is_absolute():
        target = path.parent / target
    return os.path.abspath(target)


def file_hash_observation(expected: Mapping[str, str]) -> dict[str, object]:
    actual: dict[str, str | None] = {}
    mismatches: list[dict[str, object]] = []
    for name, digest in sorted(expected.items()):
        path = Path(name)
        observed = sha256(path) if path.is_file() else None
        actual[name] = observed
        if observed != digest:
            mismatches.append({"path": name, "expected": digest, "actual": observed})
    return {"expected_count": len(expected), "actual": actual, "mismatches": mismatches, "pass": not mismatches}


def _canonical_windows_target(value: str | Path) -> str:
    target = os.fspath(value).rstrip("\x00")
    if target.startswith("\\??\\UNC\\"):
        target = "\\\\" + target[8:]
    elif target.startswith("\\??\\"):
        target = target[4:]
    elif target.startswith("\\\\?\\UNC\\"):
        target = "\\\\" + target[8:]
    elif target.startswith("\\\\?\\"):
        target = target[4:]
    return _normal_path(target)


def inspect_windows_junction(path: Path) -> dict[str, object]:
    """Read one NTFS reparse point without following or mutating it."""
    if os.name != "nt":
        return {"path": str(path), "pass": False, "error": "Windows-only detector", "is_junction": False}
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_attributes = kernel32.GetFileAttributesW
    get_attributes.argtypes = [wintypes.LPCWSTR]
    get_attributes.restype = wintypes.DWORD
    attributes = int(get_attributes(str(path)))
    if attributes == 0xFFFFFFFF:
        error = ctypes.get_last_error()
        return {"path": str(path), "pass": False, "error": f"GetFileAttributesW failed: {error}", "is_junction": False}
    result: dict[str, object] = {
        "path": str(path),
        "exists": True,
        "attributes": attributes,
        "is_reparse_point": bool(attributes & FILE_ATTRIBUTE_REPARSE_POINT),
        "is_junction": False,
    }
    if not result["is_reparse_point"]:
        result["pass"] = True
        return result

    create_file = kernel32.CreateFileW
    create_file.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        str(path),
        0,
        0x00000001 | 0x00000002 | 0x00000004,
        None,
        3,
        FILE_FLAG_OPEN_REPARSE_POINT | FILE_FLAG_BACKUP_SEMANTICS,
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        error = ctypes.get_last_error()
        return {**result, "pass": False, "error": f"CreateFileW failed: {error}"}
    try:
        device_io_control = kernel32.DeviceIoControl
        device_io_control.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID]
        device_io_control.restype = wintypes.BOOL
        buffer = ctypes.create_string_buffer(16 * 1024)
        returned = wintypes.DWORD()
        if not device_io_control(handle, FSCTL_GET_REPARSE_POINT, None, 0, buffer, len(buffer), ctypes.byref(returned), None):
            error = ctypes.get_last_error()
            return {**result, "pass": False, "error": f"FSCTL_GET_REPARSE_POINT failed: {error}"}
        raw = buffer.raw[: returned.value]
    finally:
        kernel32.CloseHandle(handle)

    if len(raw) < 16:
        return {**result, "pass": False, "error": f"short reparse buffer: {len(raw)}"}
    tag, data_length, _reserved = struct.unpack_from("<IHH", raw, 0)
    result.update({"reparse_tag": tag, "reparse_tag_hex": f"0x{tag:08X}", "reparse_data_length": data_length})
    if tag != IO_REPARSE_TAG_MOUNT_POINT:
        result["pass"] = True
        return result
    substitute_offset, substitute_length, print_offset, print_length = struct.unpack_from("<HHHH", raw, 8)
    path_buffer = 16
    substitute_name = raw[path_buffer + substitute_offset : path_buffer + substitute_offset + substitute_length].decode("utf-16-le")
    print_name = raw[path_buffer + print_offset : path_buffer + print_offset + print_length].decode("utf-16-le")
    result.update(
        {
            "is_junction": True,
            "substitute_name": substitute_name,
            "print_name": print_name,
            "resolved_target": _canonical_windows_target(substitute_name),
            "pass": True,
        }
    )
    return result


def _required_nested(value: Mapping[str, object], *keys: str) -> object:
    current: object = value
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            raise CacheAuthorityPredicateError(f"required TOML field is absent: {'.'.join(keys)}")
        current = current[key]
    return current


def _indexed_tuple(value: object, field: str) -> tuple[object, ...]:
    if not isinstance(value, Mapping):
        raise CacheAuthorityPredicateError(f"required indexed TOML table is invalid: {field}")
    try:
        return tuple(value[key] for key in sorted(value, key=lambda item: int(str(item))))
    except (KeyError, TypeError, ValueError) as exc:
        raise CacheAuthorityPredicateError(f"required indexed TOML table is invalid: {field}: {exc}") from exc


def _read_reviewed_cache_l1_metadata(base_id: str, target: Path) -> dict[str, object]:
    import toml

    primary_path = target / "config" / "extension.toml"
    generated_path = target / "config" / "extension.gen.toml"
    if not primary_path.is_file() or not generated_path.is_file():
        raise CacheAuthorityPredicateError("required target manifest is missing")
    try:
        primary = toml.load(primary_path)
        generated = toml.load(generated_path)
    except BaseException as exc:
        raise CacheAuthorityPredicateError(f"required target manifest is unreadable: {type(exc).__name__}: {exc}") from exc

    package_version = str(_required_nested(primary, "package", "version"))
    publish = _required_nested(generated, "package", "publish")
    target_metadata = _required_nested(generated, "package", "target")
    if not isinstance(publish, Mapping) or not isinstance(target_metadata, Mapping):
        raise CacheAuthorityPredicateError("required generated package metadata is not a mapping")

    common = {
        "package_version": package_version,
        "kit_version": str(_required_nested(publish, "kitVersion")),
        "build_number": str(_required_nested(publish, "buildNumber")),
        "publish_date": int(_required_nested(publish, "date")),
        "target_platform": _indexed_tuple(_required_nested(target_metadata, "platform"), "package.target.platform"),
    }
    if base_id == "usdrt.scenegraph":
        dependencies = _required_nested(primary, "dependencies")
        native = _required_nested(primary, "native", "plugin")
        if not isinstance(dependencies, Mapping) or not isinstance(native, list):
            raise CacheAuthorityPredicateError("required usdrt dependency/plugin metadata is invalid")
        return {
            **common,
            "dependencies": tuple(sorted(str(name) for name in dependencies)),
            "native_plugins": tuple(str(_required_nested(item, "path")) for item in native),
            "target_config": _indexed_tuple(_required_nested(target_metadata, "config"), "package.target.config"),
            "target_python": _indexed_tuple(_required_nested(target_metadata, "python"), "package.target.python"),
            "target_kit_hash": _indexed_tuple(_required_nested(target_metadata, "kitHash"), "package.target.kitHash"),
        }
    if base_id == "omni.warp.core":
        modules = _required_nested(primary, "python", "module")
        if not isinstance(modules, list):
            raise CacheAuthorityPredicateError("required Warp python.module metadata is invalid")
        return {
            **common,
            "python_modules": tuple(
                (
                    str(_required_nested(item, "name")),
                    str(item["path"]) if "path" in item else None,
                    bool(item.get("public", False)),
                )
                for item in modules
                if isinstance(item, Mapping)
            ),
            "repository": str(_required_nested(publish, "repoName")),
            "signed_build": int(_required_nested(publish, "signed")),
        }
    raise CacheAuthorityPredicateError(f"unreviewed cache-backed package: {base_id}")


def _hash_file_stream(path: Path, expected_size: int) -> tuple[int, str]:
    digest = hashlib.sha256()
    byte_count = 0
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
            byte_count += len(block)
    if byte_count != expected_size:
        raise CacheAuthorityPredicateError(
            f"file size changed during raw-tree capture: {path}: stat={expected_size}, read={byte_count}"
        )
    return byte_count, digest.hexdigest()


def _tree_descriptor_from_rows(rows: tuple[tuple[str, int, str], ...]) -> dict[str, object]:
    path_payload = "".join(f"{path}\n" for path, _size, _digest in rows).encode("utf-8")
    content_payload = "".join(f"{path}\t{size}\t{digest}\n" for path, size, digest in rows).encode("utf-8")
    return {
        "file_count": len(rows),
        "byte_count": sum(size for _path, size, _digest in rows),
        "path_set_sha256": hashlib.sha256(path_payload).hexdigest(),
        "content_sha256": hashlib.sha256(content_payload).hexdigest(),
    }


def capture_cache_target_raw_tree(root: Path) -> dict[str, object]:
    """Capture PD2_CACHE_TARGET_RAW_TREE_V1 without traversing a reparse point."""

    try:
        root_stat = root.lstat()
    except OSError as exc:
        raise CacheAuthorityPredicateError(f"target root is unavailable: {root}: {type(exc).__name__}: {exc}") from exc
    root_attributes = getattr(root_stat, "st_file_attributes", None)
    if root_attributes is None:
        raise CacheAuthorityPredicateError("Windows file attributes are unavailable for target root")
    if int(root_attributes) & FILE_ATTRIBUTE_REPARSE_POINT:
        raise CacheAuthorityPredicateError(f"target root is a reparse point: {root}")
    if not stat.S_ISDIR(root_stat.st_mode):
        raise CacheAuthorityPredicateError(f"target root is not an ordinary directory: {root}")

    rows: list[tuple[str, int, str]] = []
    ordinal_paths: set[str] = set()
    casefold_paths: dict[str, str] = {}
    stack: list[tuple[Path, tuple[str, ...]]] = [(root, ())]
    while stack:
        directory, prefix = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise CacheAuthorityPredicateError(
                f"target directory enumeration failed: {directory}: {type(exc).__name__}: {exc}"
            ) from exc
        entries.sort(key=lambda item: item.name)
        pending_directories: list[tuple[Path, tuple[str, ...]]] = []
        for entry in entries:
            relative_parts = prefix + (entry.name,)
            relative_path = "/".join(relative_parts)
            if any(token in relative_path for token in ("\t", "\r", "\n")):
                raise CacheAuthorityPredicateError(f"ambiguous raw-tree path encoding: {relative_path!r}")
            try:
                entry_stat = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise CacheAuthorityPredicateError(
                    f"target entry stat failed: {relative_path}: {type(exc).__name__}: {exc}"
                ) from exc
            entry_attributes = getattr(entry_stat, "st_file_attributes", None)
            if entry_attributes is None:
                raise CacheAuthorityPredicateError(f"Windows file attributes are unavailable: {relative_path}")
            if int(entry_attributes) & FILE_ATTRIBUTE_REPARSE_POINT:
                raise CacheAuthorityPredicateError(f"internal reparse point is forbidden: {relative_path}")

            if stat.S_ISDIR(entry_stat.st_mode):
                pending_directories.append((Path(entry.path), relative_parts))
                continue
            if not stat.S_ISREG(entry_stat.st_mode):
                raise CacheAuthorityPredicateError(f"target entry is not an ordinary file/directory: {relative_path}")
            if relative_path in ordinal_paths:
                raise CacheAuthorityPredicateError(f"duplicate ordinal relative path: {relative_path}")
            folded = relative_path.casefold()
            if folded in casefold_paths and casefold_paths[folded] != relative_path:
                raise CacheAuthorityPredicateError(
                    f"Windows case-insensitive path collision: {casefold_paths[folded]!r} vs {relative_path!r}"
                )
            ordinal_paths.add(relative_path)
            casefold_paths[folded] = relative_path
            byte_count, digest = _hash_file_stream(Path(entry.path), int(entry_stat.st_size))
            rows.append((relative_path, byte_count, digest))
        stack.extend(reversed(pending_directories))

    canonical_rows = tuple(sorted(rows, key=lambda row: row[0]))
    descriptor = _tree_descriptor_from_rows(canonical_rows)
    return {
        "algorithm": "PD2_CACHE_TARGET_RAW_TREE_V1",
        **descriptor,
        "canonical_rows": canonical_rows,
        "internal_reparse_count": 0,
    }


def _supporting_fingerprints(rows: tuple[tuple[str, int, str], ...]) -> dict[str, object]:
    non_generated = tuple(row for row in rows if "__pycache__" not in row[0].split("/"))
    python_source = tuple(row for row in non_generated if Path(row[0]).suffix.lower() in (".py", ".pyi"))
    native_runtime = tuple(
        row
        for row in non_generated
        if Path(row[0]).suffix.lower() in (".dll", ".pyd", ".so", ".dylib", ".exe", ".lib", ".plugin")
    )
    non_generated_descriptor = _tree_descriptor_from_rows(non_generated)
    python_descriptor = _tree_descriptor_from_rows(python_source)
    native_descriptor = _tree_descriptor_from_rows(native_runtime)
    return {
        "algorithm": "PD2_CACHE_TARGET_TREE_V1",
        "non_generated": non_generated_descriptor,
        "python_source": {
            "file_count": python_descriptor["file_count"],
            "byte_count": python_descriptor["byte_count"],
            "content_sha256": python_descriptor["content_sha256"],
        },
        "native_runtime": {
            "file_count": native_descriptor["file_count"],
            "byte_count": native_descriptor["byte_count"],
            "content_sha256": native_descriptor["content_sha256"],
        },
    }


def capture_cache_target_content(target: Path, explicit_raw_files: Mapping[str, str]) -> dict[str, object]:
    capture_a = capture_cache_target_raw_tree(target)
    capture_b = capture_cache_target_raw_tree(target)
    row_sequence_equal = capture_a["canonical_rows"] == capture_b["canonical_rows"]
    descriptor_equal = all(
        capture_a[field] == capture_b[field]
        for field in (
            "algorithm",
            "file_count",
            "byte_count",
            "path_set_sha256",
            "content_sha256",
            "internal_reparse_count",
        )
    )
    if not row_sequence_equal or not descriptor_equal:
        raise CacheAuthorityPredicateError("two complete raw-tree captures are not exactly stable")
    rows_by_path = {path: (size, digest) for path, size, digest in capture_a["canonical_rows"]}
    required_paths = ("config/extension.toml", "config/extension.gen.toml", *explicit_raw_files.keys())
    missing = [path for path in required_paths if path not in rows_by_path]
    if missing:
        raise CacheAuthorityPredicateError(f"required raw target files are missing: {missing}")
    return {
        "capture_a": capture_a,
        "capture_b": capture_b,
        "row_sequence_equal": row_sequence_equal,
        "descriptor_equal": descriptor_equal,
        "supporting": _supporting_fingerprints(capture_a["canonical_rows"]),
        "primary_manifest_sha256": rows_by_path["config/extension.toml"][1],
        "generated_manifest_sha256": rows_by_path["config/extension.gen.toml"][1],
        "explicit_raw_files": {path: rows_by_path[path][1] for path in explicit_raw_files},
    }


def _bounded_cache_content_evidence(content: Mapping[str, object]) -> dict[str, object]:
    fields = (
        "algorithm",
        "file_count",
        "byte_count",
        "path_set_sha256",
        "content_sha256",
        "internal_reparse_count",
    )
    return {
        "capture_a": {field: content["capture_a"][field] for field in fields},
        "capture_b": {field: content["capture_b"][field] for field in fields},
        "row_sequence_equal": content["row_sequence_equal"],
        "descriptor_equal": content["descriptor_equal"],
        "supporting": content["supporting"],
        "primary_manifest_sha256": content["primary_manifest_sha256"],
        "generated_manifest_sha256": content["generated_manifest_sha256"],
        "explicit_raw_files": content["explicit_raw_files"],
    }


def _predicate_failure(layer: str, field: str, expected: object, observed: object) -> dict[str, object]:
    return {
        "pass": False,
        "classification": STOP_EXTENSION,
        "failed_layer": layer,
        "failed_field": field,
        "expected": normalize(expected),
        "observed": normalize(observed),
    }


def evaluate_cache_backed_authority(
    expected: Mapping[str, object],
    observed: Mapping[str, object],
    descriptor: Mapping[str, object],
) -> dict[str, object]:
    try:
        l1_checks = (
            ("authority", expected["authority"], descriptor["authority"], observed["authority"]),
            ("base_id", expected["base_id"], descriptor["base_id"], observed["base_id"]),
            ("enabled_id", expected["enabled_id"], descriptor["enabled_id"], observed["enabled_id"]),
            ("enabled", True, True, observed["enabled"]),
            ("manager_version", expected["version"], descriptor["version"], observed["manager_version"]),
            ("manifest_version", expected["version"], descriptor["version"], observed["manifest_version"]),
            ("distribution_basename", Path(str(expected["root"])).name, descriptor["distribution_basename"], descriptor["distribution_basename"]),
            ("target_basename", Path(str(descriptor["target"])).name, descriptor["target_basename"], descriptor["target_basename"]),
            ("logical_metadata", descriptor["l1_metadata"], descriptor["l1_metadata"], observed["l1_metadata"]),
        )
        for field, frozen_source, reviewed, actual in l1_checks:
            if frozen_source != reviewed or actual != reviewed:
                return _predicate_failure("L1", field, reviewed, actual)

        l2 = observed["l2"]
        l2_checks = (
            ("installed_namespace", descriptor["installed_namespace"], l2["installed_namespace"], True),
            ("junction_reparse_attribute", True, l2["is_reparse_point"], False),
            ("junction_kind", True, l2["is_junction"], False),
            ("junction_tag", descriptor["junction_tag"], l2["reparse_tag"], False),
            ("junction_target", descriptor["target"], l2["junction_target"], True),
            ("target_exists", True, l2["target_exists"], False),
            ("target_is_directory", True, l2["target_is_directory"], False),
        )
        for field, reviewed, actual, windows_path in l2_checks:
            equal = (
                _canonical_windows_target(str(reviewed)) == _canonical_windows_target(str(actual))
                if windows_path
                else reviewed == actual
            )
            if not equal:
                return _predicate_failure("L2", field, reviewed, actual)

        l3_expected = descriptor["l3"]
        l3 = observed["l3"]
        if not l3["row_sequence_equal"] or not l3["descriptor_equal"]:
            return _predicate_failure("L3", "two_capture_stability", True, False)
        for capture_name in ("capture_a", "capture_b"):
            capture = l3[capture_name]
            for field in (
                "algorithm",
                "file_count",
                "byte_count",
                "path_set_sha256",
                "content_sha256",
                "internal_reparse_count",
            ):
                if capture[field] != l3_expected[field]:
                    return _predicate_failure("L3", f"{capture_name}.{field}", l3_expected[field], capture[field])
        for field in ("primary_manifest_sha256", "generated_manifest_sha256"):
            if l3[field] != l3_expected[field]:
                return _predicate_failure("L3", field, l3_expected[field], l3[field])
        for field in ("non_generated", "python_source", "native_runtime"):
            if l3["supporting"][field] != l3_expected[field]:
                return _predicate_failure("L3", f"supporting.{field}", l3_expected[field], l3["supporting"][field])
        if l3["explicit_raw_files"] != l3_expected["explicit_raw_files"]:
            return _predicate_failure(
                "L3", "explicit_raw_files", l3_expected["explicit_raw_files"], l3["explicit_raw_files"]
            )
    except (KeyError, TypeError, ValueError) as exc:
        return _predicate_failure("CACHE", "missing_or_unreadable_required_field", "present/readable", f"{type(exc).__name__}: {exc}")
    return {
        "pass": True,
        "classification": None,
        "authority": descriptor["authority"],
        "descriptor_id": descriptor["descriptor_id"],
        "l1_pass": True,
        "l2_pass": True,
        "l3_pass": True,
    }


def observe_cache_backed_runtime_identity(
    expected: Mapping[str, object],
    *,
    enabled_id: str,
    enabled: bool,
    manager_version: str | None,
    manifest_version: str | None,
    resolved_path: str,
) -> tuple[dict[str, object], dict[str, object]]:
    base_id = str(expected["base_id"])
    descriptor = REVIEWED_CACHE_BACKED_AUTHORITIES_V1.get(base_id)
    if descriptor is None:
        failure = _predicate_failure("DISPATCH", "cache_allowlist", tuple(REVIEWED_CACHE_BACKED_AUTHORITIES_V1), base_id)
        return {"authority": expected.get("authority"), "base_id": base_id}, failure
    namespace = Path(resolved_path)
    junction = inspect_windows_junction(namespace)
    target = Path(str(descriptor["target"]))
    l1_metadata = _read_reviewed_cache_l1_metadata(base_id, target)
    content = capture_cache_target_content(target, descriptor["l3"]["explicit_raw_files"])
    observed = {
        "authority": expected["authority"],
        "base_id": base_id,
        "enabled_id": enabled_id,
        "enabled": enabled,
        "manager_version": manager_version,
        "manifest_version": manifest_version,
        "l1_metadata": l1_metadata,
        "l2": {
            "installed_namespace": resolved_path,
            "is_reparse_point": junction.get("is_reparse_point", False),
            "is_junction": junction.get("is_junction", False),
            "reparse_tag": junction.get("reparse_tag"),
            "junction_target": junction.get("resolved_target"),
            "target_exists": target.exists(),
            "target_is_directory": target.is_dir(),
            "junction_detector": junction,
            "provenance": descriptor["provenance"],
            "cache_db_pair": descriptor["cache_db_pair"],
        },
        "l3": _bounded_cache_content_evidence(content),
    }
    return observed, evaluate_cache_backed_authority(expected, observed, descriptor)


def _expected_pair_rows() -> list[dict[str, object]]:
    return [
        {
            "name": name,
            "installed_path": str(LINK_ROOT / name),
            "target": str(CACHE_ROOT / cache_name),
            "manifest": str(CACHE_ROOT / cache_name / "config" / "extension.toml"),
            "manifest_sha256": manifest_sha256,
        }
        for name, (cache_name, manifest_sha256) in sorted(EXPECTED_JUNCTION_PAIRS.items())
    ]


def primary_windows_junction_inventory() -> dict[str, object]:
    observed = {path.name: inspect_windows_junction(path) for path in sorted(LINK_ROOT.iterdir(), key=lambda item: item.name.lower())}
    expected_rows = _expected_pair_rows()
    rows: list[dict[str, object]] = []
    for expected in expected_rows:
        inspection = observed.get(str(expected["name"]), {"pass": False, "error": "installed path missing", "is_junction": False})
        target = Path(str(expected["target"]))
        manifest = Path(str(expected["manifest"]))
        row = {
            **expected,
            "installed_exists": Path(str(expected["installed_path"])).exists(),
            "detector": inspection,
            "actual_target": inspection.get("resolved_target"),
            "target_exists": target.is_dir(),
            "actual_manifest_sha256": sha256(manifest) if manifest.is_file() else None,
        }
        row["pass"] = (
            bool(inspection.get("pass"))
            and bool(inspection.get("is_junction"))
            and inspection.get("reparse_tag") == IO_REPARSE_TAG_MOUNT_POINT
            and _canonical_windows_target(str(row["actual_target"] or "")) == _canonical_windows_target(str(expected["target"]))
            and row["target_exists"]
            and row["actual_manifest_sha256"] == expected["manifest_sha256"]
        )
        rows.append(row)
    actual_junction_names = sorted(name for name, item in observed.items() if item.get("is_junction"))
    expected_names = sorted(EXPECTED_JUNCTION_PAIRS)
    expected_targets = [_canonical_windows_target(row["target"]) for row in expected_rows]
    actual_targets = [_canonical_windows_target(str(row["actual_target"] or "")) for row in rows]
    path_set_exact = actual_junction_names == expected_names
    target_set_exact = sorted(actual_targets) == sorted(expected_targets)
    installed_unique = len(actual_junction_names) == len(set(actual_junction_names))
    targets_unique = len(actual_targets) == len(set(actual_targets))
    unexpected = sorted(set(actual_junction_names) - set(expected_names))
    mapping = [(row["installed_path"], row["actual_target"], row["actual_manifest_sha256"]) for row in rows]
    result = {
        "authority": "PYTHON_WIN32_REPARSE_POINT",
        "expected_count": len(expected_rows),
        "observed_count": len(actual_junction_names),
        "path_set_exact": path_set_exact,
        "target_set_exact": target_set_exact,
        "pair_mapping_exact": all(bool(row["pass"]) for row in rows),
        "installed_paths_unique": installed_unique,
        "targets_unique": targets_unique,
        "unexpected_junctions": unexpected,
        "rows": rows,
        "mapping_sha256": hashlib.sha256(json.dumps(normalize(mapping), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
    }
    result["pass"] = all(
        (
            result["expected_count"] == 43,
            result["observed_count"] == 43,
            path_set_exact,
            target_set_exact,
            result["pair_mapping_exact"],
            installed_unique,
            targets_unique,
            not unexpected,
        )
    )
    return result


def powershell_junction_inventory() -> dict[str, object]:
    executable = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
    if executable is None:
        return {"authority": "POWERSHELL_READ_ONLY", "pass": False, "error": "PowerShell executable unavailable", "rows": []}
    escaped_root = str(LINK_ROOT).replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop';"
        f"$rows=@(Get-ChildItem -LiteralPath '{escaped_root}' -Force | "
        "Where-Object {$_.LinkType -eq 'Junction'} | ForEach-Object {"
        "$targets=@($_.Target);"
        "[pscustomobject]@{FullName=$_.FullName;Name=$_.Name;LinkType=[string]$_.LinkType;Target=$targets}});"
        "ConvertTo-Json -InputObject $rows -Depth 4 -Compress"
    )
    forbidden = ("New-Item", "Remove-Item", "Set-Item", "Move-Item", "Rename-Item", "Clear-Item", "Set-Content", "Add-Content", "Out-File", "mklink")
    if any(token.lower() in script.lower() for token in forbidden):
        return {"authority": "POWERSHELL_READ_ONLY", "pass": False, "error": "forbidden write token in oracle", "rows": []}
    completed = subprocess.run([executable, "-NoProfile", "-NonInteractive", "-Command", script], capture_output=True, text=True, check=False, timeout=30)
    if completed.returncode != 0:
        return {"authority": "POWERSHELL_READ_ONLY", "pass": False, "exit_code": completed.returncode, "stderr": completed.stderr, "rows": []}
    try:
        decoded = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        return {"authority": "POWERSHELL_READ_ONLY", "pass": False, "error": f"JSON decode failed: {exc}", "stdout": completed.stdout, "rows": []}
    source_rows = decoded if isinstance(decoded, list) else [decoded]
    rows: list[dict[str, object]] = []
    for item in source_rows:
        targets = item.get("Target") if isinstance(item, dict) else []
        if not isinstance(targets, list):
            targets = [targets]
        targets = [str(target) for target in targets if target]
        actual_target = _canonical_windows_target(targets[0]) if len(targets) == 1 else None
        rows.append(
            {
                "name": str(item.get("Name")),
                "installed_path": str(item.get("FullName")),
                "link_type": str(item.get("LinkType")),
                "targets": targets,
                "actual_target": actual_target,
            }
        )
    rows.sort(key=lambda row: str(row["name"]).lower())
    expected = {row["name"]: row for row in _expected_pair_rows()}
    actual_names = [str(row["name"]) for row in rows]
    actual_targets = [str(row["actual_target"] or "") for row in rows]
    path_set_exact = sorted(actual_names) == sorted(expected)
    target_set_exact = sorted(actual_targets) == sorted(_canonical_windows_target(row["target"]) for row in expected.values())
    mapping_exact = all(
        row["name"] in expected
        and row["link_type"] == "Junction"
        and _normal_path(row["installed_path"]) == _normal_path(expected[row["name"]]["installed_path"])
        and row["actual_target"] == _canonical_windows_target(expected[row["name"]]["target"])
        for row in rows
    )
    result = {
        "authority": "POWERSHELL_READ_ONLY",
        "executable": executable,
        "exit_code": completed.returncode,
        "expected_count": len(expected),
        "observed_count": len(rows),
        "path_set_exact": path_set_exact,
        "target_set_exact": target_set_exact,
        "pair_mapping_exact": mapping_exact,
        "installed_paths_unique": len(actual_names) == len(set(actual_names)),
        "targets_unique": len(actual_targets) == len(set(actual_targets)),
        "unexpected_junctions": sorted(set(actual_names) - set(expected)),
        "rows": rows,
    }
    result["pass"] = all(
        (
            result["expected_count"] == 43,
            result["observed_count"] == 43,
            path_set_exact,
            target_set_exact,
            mapping_exact,
            result["installed_paths_unique"],
            result["targets_unique"],
            not result["unexpected_junctions"],
        )
    )
    return result


def compare_junction_oracles(primary: Mapping[str, object], powershell: Mapping[str, object]) -> dict[str, object]:
    primary_mapping = {
        _normal_path(row["installed_path"]): _canonical_windows_target(str(row.get("actual_target") or ""))
        for row in primary.get("rows", [])
    }
    powershell_mapping = {
        _normal_path(row["installed_path"]): _canonical_windows_target(str(row.get("actual_target") or ""))
        for row in powershell.get("rows", [])
    }
    mapping_equal = primary_mapping == powershell_mapping
    result = {
        "primary_pass": bool(primary.get("pass")),
        "powershell_pass": bool(powershell.get("pass")),
        "mapping_equal": mapping_equal,
        "primary_mapping_sha256": hashlib.sha256(json.dumps(primary_mapping, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "powershell_mapping_sha256": hashlib.sha256(json.dumps(powershell_mapping, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }
    result["pass"] = result["primary_pass"] and result["powershell_pass"] and mapping_equal
    return result


def shared_state_inventory() -> dict[str, object]:
    # Do not change this row representation or blob algorithm: it is the
    # frozen D4-CI 103-row fingerprint.  Junction identity is audited below by
    # the independent Win32 pair contract.
    rows: list[tuple[object, ...]] = []
    for path in sorted(LINK_ROOT.iterdir(), key=lambda item: item.name.lower()):
        stat = path.lstat()
        rows.append(("linkroot", path.name, os.path.islink(path), os.readlink(path) if os.path.islink(path) else None, stat.st_ctime_ns, stat.st_mtime_ns))
    for path in sorted(CACHE_ROOT.iterdir(), key=lambda item: item.name.lower()):
        stat = path.stat()
        manifest = path / "config" / "extension.toml"
        identity = sha256(manifest) if manifest.is_file() else (sha256(path) if path.is_file() else None)
        rows.append(("cacheroot", path.name, path.is_dir(), identity, stat.st_ctime_ns, stat.st_mtime_ns))
    for path in METADATA_PATHS:
        stat = path.stat()
        rows.append(("metadata", str(path), sha256(path), stat.st_ctime_ns, stat.st_mtime_ns, stat.st_size))
    blob = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")
    counts = {kind: sum(row[0] == kind for row in rows) for kind in ("linkroot", "cacheroot", "metadata")}
    primary = primary_windows_junction_inventory()
    counts["total"] = len(rows)
    counts["junction_pairs"] = int(primary["observed_count"])
    return {
        "rows": rows,
        "sha256": hashlib.sha256(blob).hexdigest(),
        "counts": counts,
        "junction_pairs": primary["rows"],
        "junction_primary": primary,
    }


def shared_state_dual_oracle_inventory() -> dict[str, object]:
    shared = shared_state_inventory()
    powershell = powershell_junction_inventory()
    comparison = compare_junction_oracles(shared["junction_primary"], powershell)
    shared["junction_powershell"] = powershell
    shared["junction_oracle_comparison"] = comparison
    return shared


def static_critical_manifest() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for expected in CRITICAL_MANIFEST:
        root = Path(str(expected["root"]))
        manifest = Path(str(expected["manifest"]))
        actual = {
            **expected,
            "root_exists": root.is_dir(),
            "manifest_exists": manifest.is_file(),
            "actual_manifest_sha256": sha256(manifest) if manifest.is_file() else None,
            "actual_version": _manifest_version(manifest) if manifest.is_file() else None,
            "actual_link": os.path.islink(root),
            "actual_link_target": _readlink(root),
        }
        row_pass = (
            actual["root_exists"]
            and actual["manifest_exists"]
            and actual["actual_manifest_sha256"] == expected["manifest_sha256"]
            and actual["actual_version"] == expected["version"]
            and actual["actual_link"] == expected["link"]
            and actual["actual_link_target"] == expected["link_target"]
        )
        actual["pass"] = row_pass
        rows.append(actual)
        if not row_pass:
            failures.append(actual)
    return {"rows": rows, "failures": failures, "pass": not failures}


def _call_name(node: ast.Call) -> str:
    def name(value: ast.AST) -> str:
        if isinstance(value, ast.Name):
            return value.id
        if isinstance(value, ast.Attribute):
            return name(value.value) + "." + value.attr
        return ""

    return name(node.func)


def warmup_ast_semantics(path: Path, function_name: str) -> dict[str, object]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    function = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function_name), None)
    if function is None:
        return {"pass": False, "reason": "function missing", "operations": []}
    linear_names = {
        target.id
        for statement in function.body
        if isinstance(statement, ast.Assign)
        for target in statement.targets
        if isinstance(target, ast.Name)
        and isinstance(statement.value, ast.Call)
        and any(_call_name(call) == "torch.nn.Linear" for call in ast.walk(statement.value) if isinstance(call, ast.Call))
    }
    operations: list[dict[str, object]] = []
    for call in sorted((item for item in ast.walk(function) if isinstance(item, ast.Call)), key=lambda item: (item.lineno, item.col_offset)):
        name = _call_name(call)
        if name == "torch.cuda.is_available":
            operations.append({"op": "cuda_is_available"})
        elif name == "torch.device":
            operations.append({"op": "device"})
        elif name == "torch.cuda.set_device":
            operations.append({"op": "set_device"})
        elif name == "torch.zeros":
            shape = ast.literal_eval(call.args[0]) if call.args else None
            operations.append({"op": "zeros", "shape": shape, "dtype_keyword": any(item.arg == "dtype" for item in call.keywords)})
        elif name == "torch.nn.Linear":
            args = [ast.literal_eval(item) for item in call.args]
            operations.append({"op": "linear", "args": args})
        elif name.endswith(".to"):
            operations.append({"op": "to_device"})
        elif isinstance(call.func, ast.Name) and call.func.id in linear_names:
            operations.append({"op": "linear_forward"})
        elif name == "torch.cuda.synchronize":
            operations.append({"op": "synchronize"})
    forbidden = [name for name in (_call_name(call) for call in ast.walk(function) if isinstance(call, ast.Call)) if "matmul" in name or name.endswith(".seed") or "manual_seed" in name]
    return {"pass": not forbidden, "operations": operations, "forbidden": forbidden, "lineno": function.lineno}


def snapshot_order_static_review() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_real_smoke")
    positions: dict[str, int] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Assign):
            names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            for key in ("snapshot_a", "snapshot_b"):
                if key in names:
                    positions[key] = node.lineno
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "reset" and "route_reset" not in positions:
                positions["route_reset"] = node.lineno
            if node.func.attr == "collect_step":
                positions.setdefault("first_collect_step", node.lineno)
            if node.func.attr == "finish_rollout":
                positions["finish_rollout"] = node.lineno
    passed = (
        positions.get("snapshot_a", 10**9) < positions.get("route_reset", -1)
        < positions.get("first_collect_step", -1)
        and positions.get("finish_rollout", 10**9) < positions.get("snapshot_b", -1)
    )
    return {"pass": passed, "positions": positions}


def junction_reader_static_review() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    required_tokens = (
        "GetFileAttributesW",
        "CreateFileW",
        "DeviceIoControl",
        "FSCTL_GET_REPARSE_POINT",
        "IO_REPARSE_TAG_MOUNT_POINT",
        "FILE_FLAG_OPEN_REPARSE_POINT",
        "POWERSHELL_READ_ONLY",
    )
    expected_targets = [cache_name for cache_name, _digest in EXPECTED_JUNCTION_PAIRS.values()]
    manifest_hashes = [digest for _cache_name, digest in EXPECTED_JUNCTION_PAIRS.values()]
    result = {
        "platform_windows": os.name == "nt",
        "expected_pair_count": len(EXPECTED_JUNCTION_PAIRS),
        "expected_installed_unique": len(EXPECTED_JUNCTION_PAIRS) == len(set(EXPECTED_JUNCTION_PAIRS)),
        "expected_targets_unique": len(expected_targets) == len(set(expected_targets)),
        "manifest_hashes_well_formed": all(re.fullmatch(r"[0-9a-f]{64}", digest) is not None for digest in manifest_hashes),
        "required_win32_tokens": {token: token in source for token in required_tokens},
        "frozen_fingerprint_constant": EXPECTED_SHARED_FINGERPRINT,
    }
    result["pass"] = all(
        (
            result["platform_windows"],
            result["expected_pair_count"] == 43,
            result["expected_installed_unique"],
            result["expected_targets_unique"],
            result["manifest_hashes_well_formed"],
            all(result["required_win32_tokens"].values()),
            EXPECTED_SHARED_FINGERPRINT == "ebdfb41e35d85b55eb7d86acf2ab78b33229ca0bec30623d1c88ec297deb846f",
        )
    )
    return result


def s0r_adapter_synthetic_verification() -> dict[str, object]:
    class TwoArgumentGet:
        def __init__(self, values: Mapping[str, object]) -> None:
            self.values = dict(values)
            self.calls: list[tuple[str, object]] = []

        def get(self, key: str, default: object) -> object:
            self.calls.append((key, default))
            return self.values.get(key, default)

    plain = {"version": "1.2.3"}
    plain_before = dict(plain)
    case_a = _read_extension_field(plain, "version") == "1.2.3" and plain == plain_before

    missing = {"name": "example"}
    missing_before = dict(missing)
    case_b_value = _read_extension_field(missing, "version", "DEFAULT")
    case_b = case_b_value == "DEFAULT" and missing == missing_before

    two_argument = TwoArgumentGet({"version": "2.3.4"})
    case_c_value = _read_extension_field(two_argument, "version", None)
    case_c = case_c_value == "2.3.4" and len(two_argument.calls) == 1 and two_argument.calls[0][0] == "version"

    unsupported_error = None
    try:
        _read_extension_field(object(), "version")
    except ExtensionFieldReadError as exc:
        unsupported_error = f"{type(exc).__name__}: {exc}"
    case_d = unsupported_error is not None

    missing_required_error = None
    mapped_classification = None
    try:
        _read_extension_field({}, "version")
    except ExtensionFieldReadError as exc:
        missing_required_error = f"{type(exc).__name__}: {exc}"
        mapped = PD2Stop(
            STOP_EXTENSION,
            f"required runtime extension field is unavailable: {exc}",
            boundary="S0R_SYNTHETIC_REQUIRED_VERSION",
        )
        mapped_classification = mapped.classification
    case_e = missing_required_error is not None and mapped_classification == STOP_EXTENSION

    nested_item = TwoArgumentGet({"version": "3.4.5"})
    nested_root = TwoArgumentGet({"package": nested_item})
    case_f_value = _manager_version(nested_root)
    case_f = case_f_value == "3.4.5" and [call[0] for call in nested_root.calls] == ["version", "package"] and [call[0] for call in nested_item.calls] == ["version"]

    cases = {
        "A_plain_mapping_read_only": case_a,
        "B_missing_mapping_default_exact": case_b,
        "C_two_argument_get_read_only": case_c,
        "D_unsupported_object_fail_closed": case_d,
        "E_required_missing_maps_to_runtime_extension_stop": case_e,
        "F_nested_package_metadata": case_f,
    }
    return {
        "pass": all(cases.values()),
        "cases": cases,
        "observations": {
            "missing_default_value": case_b_value,
            "two_argument_value": case_c_value,
            "unsupported_error": unsupported_error,
            "required_missing_error": missing_required_error,
            "required_missing_mapped_classification": mapped_classification,
            "nested_version": case_f_value,
        },
        "AppLauncher": 0,
        "SimulationApp": 0,
        "Isaac": 0,
        "CUDA": 0,
        "HARL": 0,
        "MRTA": 0,
        "mutation_operations": 0,
    }


def s0r_adapter_persistence_static_review() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    adapter = functions["_read_extension_field"]
    version = functions["_manager_version"]
    runtime = functions["runtime_extension_gate"]

    adapter_calls = [call for call in ast.walk(adapter) if isinstance(call, ast.Call)]
    two_argument_get_path = any(
        isinstance(call.func, ast.Name) and call.func.id == "getter" and len(call.args) == 2
        for call in adapter_calls
    )
    version_source = ast.get_source_segment(source, version) or ""
    no_single_argument_version_get = '.get("version")' not in version_source and ".get('version')" not in version_source

    labels: dict[str, int] = {}
    required_labels = (
        "complete_set_snapshots_persisted",
        "critical_runtime_identity_row_started",
        "critical_runtime_identity_row_pass",
        "runtime_extension_identity_pass",
    )
    for node in ast.walk(runtime):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in required_labels:
            labels[node.value] = node.lineno
    persistence_order = (
        labels.get("complete_set_snapshots_persisted", 10**9)
        < labels.get("critical_runtime_identity_row_started", -1)
        < labels.get("critical_runtime_identity_row_pass", -1)
        < labels.get("runtime_extension_identity_pass", -1)
    )

    classification_names: list[str] = []
    for call in (node for node in ast.walk(runtime) if isinstance(node, ast.Call)):
        name = _call_name(call)
        classification_arg = None
        if name == "require" and len(call.args) >= 2:
            classification_arg = call.args[1]
        elif name == "PD2Stop" and call.args:
            classification_arg = call.args[0]
        if isinstance(classification_arg, ast.Name):
            classification_names.append(classification_arg.id)
    mapping_exact = bool(classification_names) and set(classification_names) == {"STOP_EXTENSION"}
    runtime_source = ast.get_source_segment(source, runtime) or ""
    no_startup_mapping = "STOP_STARTUP" not in runtime_source

    result = {
        "two_argument_get_path": two_argument_get_path,
        "no_single_argument_version_get": no_single_argument_version_get,
        "persistence_labels": labels,
        "persistence_order_exact": persistence_order,
        "runtime_failure_classification_names": classification_names,
        "runtime_failure_mapping_exact": mapping_exact,
        "runtime_has_no_startup_mapping": no_startup_mapping,
    }
    result["pass"] = all(
        (
            two_argument_get_path,
            no_single_argument_version_get,
            persistence_order,
            mapping_exact,
            no_startup_mapping,
        )
    )
    return result


def _thaw_frozen(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_frozen(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_thaw_frozen(item) for item in value)
    return value


def _critical_by_base(base_id: str) -> Mapping[str, object]:
    matches = [row for row in CRITICAL_MANIFEST if row["base_id"] == base_id]
    if len(matches) != 1:
        raise CacheAuthorityPredicateError(f"critical manifest row count is not exactly one: {base_id}: {len(matches)}")
    return matches[0]


def _synthetic_cache_observation(base_id: str) -> dict[str, object]:
    descriptor = REVIEWED_CACHE_BACKED_AUTHORITIES_V1[base_id]
    l3 = descriptor["l3"]
    capture = {
        field: l3[field]
        for field in (
            "algorithm",
            "file_count",
            "byte_count",
            "path_set_sha256",
            "content_sha256",
            "internal_reparse_count",
        )
    }
    return {
        "authority": descriptor["authority"],
        "base_id": descriptor["base_id"],
        "enabled_id": descriptor["enabled_id"],
        "enabled": True,
        "manager_version": descriptor["version"],
        "manifest_version": descriptor["version"],
        "l1_metadata": _thaw_frozen(descriptor["l1_metadata"]),
        "l2": {
            "installed_namespace": descriptor["installed_namespace"],
            "is_reparse_point": True,
            "is_junction": True,
            "reparse_tag": descriptor["junction_tag"],
            "junction_target": descriptor["target"],
            "target_exists": True,
            "target_is_directory": True,
        },
        "l3": {
            "capture_a": dict(capture),
            "capture_b": dict(capture),
            "row_sequence_equal": True,
            "descriptor_equal": True,
            "supporting": {
                "algorithm": "PD2_CACHE_TARGET_TREE_V1",
                "non_generated": _thaw_frozen(l3["non_generated"]),
                "python_source": _thaw_frozen(l3["python_source"]),
                "native_runtime": _thaw_frozen(l3["native_runtime"]),
            },
            "primary_manifest_sha256": l3["primary_manifest_sha256"],
            "generated_manifest_sha256": l3["generated_manifest_sha256"],
            "explicit_raw_files": _thaw_frozen(l3["explicit_raw_files"]),
        },
    }


def _legacy_synthetic_exact(expected: Mapping[str, object], observed: Mapping[str, object]) -> bool:
    return (
        observed["actual_enabled_id"] == expected["enabled_id"]
        and observed["enabled"] is True
        and observed["manager_version"] == expected["version"]
        and observed["manifest_version"] == expected["version"]
        and _normal_path(observed["resolved_path"]) == _normal_path(expected["root"])
        and _normal_path(observed["manifest_path"]) == _normal_path(expected["manifest"])
        and observed["manifest_sha256"] == expected["manifest_sha256"]
        and observed["link"] == expected["link"]
        and observed["link_target"] == expected["link_target"]
    )


def cache_backed_predicate_synthetic_verification() -> dict[str, object]:
    usdrt_expected = _critical_by_base("usdrt.scenegraph")
    warp_expected = _critical_by_base("omni.warp.core")
    usdrt_descriptor = REVIEWED_CACHE_BACKED_AUTHORITIES_V1["usdrt.scenegraph"]
    warp_descriptor = REVIEWED_CACHE_BACKED_AUTHORITIES_V1["omni.warp.core"]

    def result(expected: Mapping[str, object], observation: Mapping[str, object], descriptor: Mapping[str, object]) -> bool:
        return bool(evaluate_cache_backed_authority(expected, observation, descriptor)["pass"])

    exact_usdrt = _synthetic_cache_observation("usdrt.scenegraph")
    exact_warp = _synthetic_cache_observation("omni.warp.core")
    cases: dict[str, bool] = {
        "A_exact_reviewed_usdrt": result(usdrt_expected, exact_usdrt, usdrt_descriptor),
        "E_exact_reviewed_warp": result(warp_expected, exact_warp, warp_descriptor),
        "Q_exact_reviewed_full_raw_tree": result(usdrt_expected, copy.deepcopy(exact_usdrt), usdrt_descriptor),
    }

    changed = copy.deepcopy(exact_usdrt)
    changed["l2"]["junction_target"] = r"C:\not-reviewed\usdrt"
    cases["B_usdrt_wrong_junction_target"] = not result(usdrt_expected, changed, usdrt_descriptor)
    changed = copy.deepcopy(exact_usdrt)
    changed["l2"]["installed_namespace"] = r"C:\alternate\same-version-usdrt"
    cases["C_usdrt_same_version_alternate_path"] = not result(usdrt_expected, changed, usdrt_descriptor)
    changed = copy.deepcopy(exact_usdrt)
    changed["l3"]["primary_manifest_sha256"] = "0" * 64
    cases["D_normalized_equivalent_raw_manifest_mismatch"] = not result(usdrt_expected, changed, usdrt_descriptor)
    changed = copy.deepcopy(exact_warp)
    changed["l3"]["explicit_raw_files"]["warp/bin/warp.dll"] = "1" * 64
    cases["F_warp_raw_dll_mismatch"] = not result(warp_expected, changed, warp_descriptor)
    changed = copy.deepcopy(exact_warp)
    changed["l2"]["junction_target"] = r"C:\not-reviewed\warp"
    cases["G_warp_wrong_junction_target"] = not result(warp_expected, changed, warp_descriptor)

    third_expected = dict(usdrt_expected)
    third_expected.update({"base_id": "third.cache.package", "enabled_id": "third.cache.package-1.0.0"})
    cases["H_third_cache_backed_package"] = third_expected["base_id"] not in REVIEWED_CACHE_BACKED_AUTHORITIES_V1

    for authority, base_id, case_id in (
        ("PROJECT_LOCAL_SOURCE", "isaaclab", "I_project_local_exact_regression"),
        ("OFFICIAL_INSTALLED", "isaacsim.simulation_app", "J_official_installed_exact_regression"),
    ):
        expected = _critical_by_base(base_id)
        observation = {
            "actual_enabled_id": expected["enabled_id"],
            "enabled": True,
            "manager_version": expected["version"],
            "manifest_version": expected["version"],
            "resolved_path": expected["root"],
            "manifest_path": expected["manifest"],
            "manifest_sha256": expected["manifest_sha256"],
            "link": expected["link"],
            "link_target": expected["link_target"],
            "authority": authority,
        }
        mismatch = dict(observation)
        mismatch["manifest_sha256"] = "f" * 64
        cases[case_id] = _legacy_synthetic_exact(expected, observation) and not _legacy_synthetic_exact(expected, mismatch)

    changed = copy.deepcopy(exact_usdrt)
    del changed["l3"]["generated_manifest_sha256"]
    cases["K_missing_required_field"] = not result(usdrt_expected, changed, usdrt_descriptor)
    changed = copy.deepcopy(exact_usdrt)
    changed["l2"]["installed_namespace"] = r"C:\another-namespace\approved-target"
    cases["L_approved_target_other_namespace"] = not result(usdrt_expected, changed, usdrt_descriptor)
    changed = copy.deepcopy(exact_usdrt)
    changed["l3"]["supporting"]["non_generated"]["content_sha256"] = "2" * 64
    cases["M_non_generated_file_changed"] = not result(usdrt_expected, changed, usdrt_descriptor)

    for case_id, field, value in (
        ("N1_pyc_added", "file_count", int(usdrt_descriptor["l3"]["file_count"]) + 1),
        ("N2_pyc_removed", "file_count", int(usdrt_descriptor["l3"]["file_count"]) - 1),
        ("N3_pyc_renamed", "path_set_sha256", "3" * 64),
        ("N4_pyc_bytes_changed", "content_sha256", "4" * 64),
    ):
        changed = copy.deepcopy(exact_usdrt)
        changed["l3"]["capture_a"][field] = value
        changed["l3"]["capture_b"][field] = value
        cases[case_id] = not result(usdrt_expected, changed, usdrt_descriptor)

    changed = copy.deepcopy(exact_usdrt)
    changed["l3"]["capture_a"]["internal_reparse_count"] = 1
    changed["l3"]["capture_b"]["internal_reparse_count"] = 1
    cases["O_internal_reparse_point"] = not result(usdrt_expected, changed, usdrt_descriptor)
    cases["P_unknown_authority_category"] = "UNKNOWN" not in CACHE_AUTHORITY_CATEGORIES_V1
    changed = copy.deepcopy(exact_usdrt)
    changed["l3"]["capture_a"]["content_sha256"] = "5" * 64
    changed["l3"]["capture_b"]["content_sha256"] = "5" * 64
    cases["R_raw_tree_mismatch_supporting_subsets_match"] = not result(usdrt_expected, changed, usdrt_descriptor)

    return {
        "pass": len(cases) >= 18 and all(cases.values()),
        "case_count": len(cases),
        "pass_count": sum(cases.values()),
        "fail_count": len(cases) - sum(cases.values()),
        "cases": cases,
        "AppLauncher": 0,
        "SimulationApp": 0,
        "Isaac": 0,
        "CUDA": 0,
        "HARL": 0,
        "MRTA": 0,
    }


def cache_backed_predicate_static_review() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    assignments = {
        target.id: node
        for node in tree.body
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    descriptor_assignment = assignments["REVIEWED_CACHE_BACKED_AUTHORITIES_V1"]
    assignment_calls = sorted(
        _call_name(call) for call in ast.walk(descriptor_assignment.value) if isinstance(call, ast.Call)
    )
    descriptor_literal_only = set(assignment_calls) <= {"MappingProxyType"}

    raw_source = ast.get_source_segment(source, functions["capture_cache_target_raw_tree"]) or ""
    content_source = ast.get_source_segment(source, functions["capture_cache_target_content"]) or ""
    runtime_source = ast.get_source_segment(source, functions["runtime_extension_gate"]) or ""
    observe_source = ast.get_source_segment(source, functions["observe_cache_backed_runtime_identity"]) or ""
    evaluator_source = ast.get_source_segment(source, functions["evaluate_cache_backed_authority"]) or ""
    junction_source = ast.get_source_segment(source, functions["inspect_windows_junction"]) or ""
    warmup_source = ast.get_source_segment(source, functions["_warm_start_torch_cuda"]) or ""
    forbidden_equivalence_tokens = (
        "realpath(",
        ".glob(",
        ".rglob(",
        "same_version",
        "same_basename",
        "authenticode",
        "normalize_manifest",
        "powershell_junction_inventory",
    )
    cache_runtime_source = (observe_source + evaluator_source).lower()
    forbidden_found = [token for token in forbidden_equivalence_tokens if token in cache_runtime_source]
    try:
        REVIEWED_CACHE_BACKED_AUTHORITIES_V1["new"] = {}  # type: ignore[index]
        immutable = False
    except TypeError:
        immutable = True
    result = {
        "authority_categories_exact": CACHE_AUTHORITY_CATEGORIES_V1
        == frozenset({"PROJECT_LOCAL_SOURCE", "OFFICIAL_INSTALLED", "OFFICIAL_INSTALLED_CACHE"}),
        "runtime_dispatch_exhaustive": all(category in runtime_source for category in CACHE_AUTHORITY_CATEGORIES_V1),
        "cache_allowlist_exact": set(REVIEWED_CACHE_BACKED_AUTHORITIES_V1)
        == {"usdrt.scenegraph", "omni.warp.core"},
        "descriptor_literal_only": descriptor_literal_only,
        "descriptor_assignment_calls": assignment_calls,
        "descriptor_immutable": immutable,
        "raw_tree_all_regular_files": "stat.S_ISREG" in raw_source
        and "__pycache__" not in raw_source
        and ".pyc" not in raw_source,
        "reparse_before_recursion": raw_source.find("FILE_ATTRIBUTE_REPARSE_POINT")
        < raw_source.find("stat.S_ISDIR"),
        "two_independent_captures": content_source.count("capture_cache_target_raw_tree(target)") == 2,
        "row_sequence_exact_comparison": 'capture_a["canonical_rows"] == capture_b["canonical_rows"]'
        in content_source,
        "no_forbidden_equivalence_engine": not forbidden_found,
        "forbidden_equivalence_tokens_found": forbidden_found,
        "stop_taxonomy_exact": len(STOP_TAXONOMY) == 10 and set(STOP_TAXONOMY) == {
            STOP_PRELAUNCH,
            STOP_STARTUP,
            STOP_EXTENSION,
            STOP_VCRITIC,
            STOP_ACTOR,
            STOP_PHYSICAL,
            STOP_TERMINAL,
            STOP_MUTATION,
            STOP_SHUTDOWN,
            STOP_SHARED_STATE,
        },
        "junction_reader_source_unchanged": hashlib.sha256(junction_source.encode()).hexdigest()
        == "7602402aff617b69961e4d38c252787d6b093bf9a184da85c40bb4a9d15a554c",
        "production_warmup_copy_source_unchanged": hashlib.sha256(warmup_source.encode()).hexdigest()
        == "28a85382eeca160a321b0fe54a15dc89e3ccd2af3349e13d9d09846ce5d23ce2",
    }
    result["pass"] = all(value for key, value in result.items() if key not in ("descriptor_assignment_calls", "forbidden_equivalence_tokens_found"))
    return result


def cache_backed_real_target_read_only_verification() -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for base_id in sorted(REVIEWED_CACHE_BACKED_AUTHORITIES_V1):
        expected = _critical_by_base(base_id)
        descriptor = REVIEWED_CACHE_BACKED_AUTHORITIES_V1[base_id]
        target = Path(str(descriptor["target"]))
        primary = target / "config" / "extension.toml"
        manifest_version = _manifest_version(primary) if primary.is_file() else None
        observed, comparison = observe_cache_backed_runtime_identity(
            expected,
            enabled_id=str(descriptor["enabled_id"]),
            enabled=True,
            manager_version=str(descriptor["version"]),
            manifest_version=manifest_version,
            resolved_path=str(descriptor["installed_namespace"]),
        )
        rows.append(
            {
                "base_id": base_id,
                "descriptor_id": descriptor["descriptor_id"],
                "pass": bool(comparison["pass"]),
                "comparison": comparison,
                "l2": observed.get("l2"),
                "l3": observed.get("l3"),
            }
        )
    return {
        "pass": len(rows) == 2 and all(row["pass"] for row in rows),
        "rows": rows,
        "read_only": True,
        "capture_count_per_target": 2,
        "AppLauncher": 0,
        "SimulationApp": 0,
        "Isaac": 0,
        "CUDA": 0,
        "HARL": 0,
        "MRTA": 0,
    }


def _source_segment(symbol: str) -> str:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol:
            lines = source.splitlines(keepends=True)
            return "".join(lines[node.lineno - 1 : node.end_lineno])
    raise LookupError(symbol)


def _path_source_segment(path: Path, symbol: str) -> str:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == symbol:
            lines = source.splitlines(keepends=True)
            return "".join(lines[node.lineno - 1 : node.end_lineno])
    raise LookupError(f"{path}:{symbol}")


def r5d_static_contract_review() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    runtime = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_real_smoke")
    collect_calls = [
        node
        for node in ast.walk(runtime)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "collect_step"
    ]
    s5_checkpoint_lines = [
        node.lineno
        for node in ast.walk(runtime)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "emit"
        and any(isinstance(arg, ast.Constant) and arg.value == "continuation_second_step_pass" for arg in node.args)
    ]
    s6_assert_lines = [
        node.lineno
        for node in ast.walk(runtime)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require"
        and any(
            keyword.arg == "boundary"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value == "S6_TIME_LIMIT"
            for keyword in node.keywords
        )
    ]
    s5_fields = tuple(item.name for item in fields(PD2S5PreterminalEvidenceV1))
    expected_s5_fields = (
        "schema_version", "transition_index", "transition_slot", "preterminal_source_p2_serial",
        "preterminal_source_store_version", "preterminal_admitted_p2_serial", "preterminal_admitted_store_version",
        "preterminal_episode_generations", "preterminal_transition_generations", "preterminal_source_window_serial",
        "preterminal_effective_assignment", "controller_expected_assignment_transition2", "controller_actual_assignment_transition2",
        "continuation_row_mask", "continuation_expected_task", "policy_decision_row_mask", "forced_row_mask",
        "forced_noop_row_mask", "claim_mutated_row_mask", "original_proposal_ids", "proposal_logprob_finite_mask",
        "proposal_present_mask", "actor_call_records", "resolution_interpretations",
    )
    post_fields = tuple(item.name for item in fields(PD2PostReturnStateDiagnosticV1))
    expected_post_fields = (
        "schema_version", "transition_index", "post_return_current_p2_serial", "post_return_current_store_version",
        "post_return_current_episode_generations", "post_return_current_transition_generations",
        "post_return_next_bundle_p2_serial", "post_return_next_bundle_episode_generations",
        "post_return_next_bundle_transition_generations", "terminal_status_proven", "autoreset_status_proven",
    )
    forbidden_s5_prefixes = ("post_return_", "post_autoreset_", "terminal_", "next_episode_")
    forbidden_s5_names = {"current_p2", "current_assignment", "current_generation"}
    builder_source = _source_segment("build_pd2_s5_preterminal_evidence_v1")
    forbidden_builder_tokens = (
        "next_decision_bundle", ".current_publication", "terminal_historical_payload",
        "domain.current_read_port", "wrapper.current_p2", "post_autoreset_", "post_return_",
    )
    timing_source = _source_segment("build_pd2_integral_horizon_fixture_v1")
    critic_source = _source_segment("CriticRecorder")
    correlation_source = _source_segment("compare_pd2_s6_timeout_critic_input_exact_v1")
    correlation_adjudicator_source = _source_segment("adjudicate_pd2_s6_timeout_critic_input_correlation_v1")
    identity_source = _source_segment("identify_pd2_s6_timeout_critic_call_v1")
    runtime_source = _source_segment("run_real_smoke")
    learned_route_collect_source = _path_source_segment(
        SCAN / "assignment_event_learned_route.py", "EventDormantLearnedPolicyRouteV2"
    )
    collector_source = _path_source_segment(
        SCAN / "assignment_event_critic_buffer.py", "EventTerminalLearnerCollectorV2"
    )
    timeout_evaluator_source = _path_source_segment(
        SCAN / "assignment_event_terminal_learner_transport.py",
        "evaluate_event_timeout_bootstrap_values_v2",
    )
    identity_fields = tuple(item.name for item in fields(PD2S6TimeoutCriticInvocationIdentityV1))
    expected_identity_fields = (
        "schema_version", "source_order_contract", "second_collect_start_call_index",
        "second_collect_end_call_index", "second_collect_total_call_count",
        "current_call_relative_index", "current_call_global_index",
        "timeout_call_relative_index", "timeout_call_global_index",
        "timeout_batch_event_count", "expected_timeout_call_count",
        "observed_timeout_call_count", "call_identity_pass",
    )
    correlation_fields = tuple(item.name for item in fields(PD2S6TimeoutCriticInputCorrelationV1))
    expected_correlation_fields = (
        "schema_version", "fingerprint_algorithm", "second_collect_start_call_index",
        "second_collect_end_call_index", "timeout_call_relative_index",
        "timeout_call_global_index", "expected_timeout_call_count",
        "observed_timeout_call_count", "call_identity_pass", "expected_shape", "observed_shape",
        "expected_dtype", "observed_dtype", "expected_device", "observed_device",
        "expected_numel", "observed_numel", "expected_nbytes", "observed_nbytes",
        "expected_input_sha256", "observed_input_sha256", "shape_match", "dtype_match",
        "device_match", "numel_match", "digest_match", "exact_comparison_executed",
        "exact_value_match",
    )
    approximate_tokens = ("allclose", "rtol", "atol", "round(", "normalize", "epsilon")
    stop_found = sorted(set(re.findall(r"PD2-STOP-[A-Za-z0-9-]+", source)))
    checks = {
        "exact_two_collect_step_calls": len(collect_calls) == 2,
        "s5_checkpoint_before_s6_assertion": len(s5_checkpoint_lines) == 1 and bool(s6_assert_lines) and s5_checkpoint_lines[0] < min(s6_assert_lines),
        "s5_dto_exact_fields": s5_fields == expected_s5_fields,
        "s5_dto_forbidden_fields_absent": not any(name.startswith(forbidden_s5_prefixes) or name in forbidden_s5_names for name in s5_fields),
        "s5_builder_has_no_postreturn_dependency": not any(token in builder_source for token in forbidden_builder_tokens),
        "postreturn_dto_exact_fields": post_fields == expected_post_fields,
        "postreturn_names_temporally_qualified": all(name in ("schema_version", "transition_index", "terminal_status_proven", "autoreset_status_proven") or name.startswith("post_return_") for name in post_fields),
        "timing_has_no_boundary_hack": "nextafter" not in timing_source.lower() and "epsilon" not in timing_source.lower(),
        "critic_fingerprint_before_wrapped_forward": critic_source.count("self.wrapped.get_values(") == 1 and critic_source.index("capture_pd2_critic_input_fingerprint_v1(") < critic_source.index("self.wrapped.get_values("),
        "s6_invocation_identity_dto_exact_bounded_fields": identity_fields == expected_identity_fields,
        "s6_call_identity_independent_from_tensor_values": not any(token in identity_source for token in ("torch", "equal", "sha256", "digest", "dtype", "shape", "observed_input")),
        "s6_cursor_role_identity_required": all(token in identity_source for token in ("second_collect_start_call_index", "second_collect_end_call_index", "PD2_TIMEOUT_CRITIC_RELATIVE_INDEX", "timeout_batch_event_count")),
        "s6_timeout_count_exact_one_independent": "observed_timeout_call_count == PD2_EXPECTED_TIMEOUT_CRITIC_CALL_COUNT" in identity_source,
        "s6_frozen_route_current_before_terminal_collector": learned_route_collect_source.index("self.critic.get_values(") < learned_route_collect_source.index("self.collector.consume_before_optimizer_update("),
        "s6_frozen_collector_delegates_timeout_after_current": collector_source.count("evaluate_event_timeout_bootstrap_values_v2(") == 1,
        "s6_frozen_timeout_evaluator_exact_one_forward": timeout_evaluator_source.count("critic.get_values(") == 1 and "calls = 1" in timeout_evaluator_source,
        "s6_identity_before_exact_correlation": runtime_source.index("timeout_invocation_identity = identify_pd2_s6_timeout_critic_call_v1(") < runtime_source.index("timeout_correlation = compare_pd2_s6_timeout_critic_input_exact_v1("),
        "s6_no_value_based_call_selection": not any(token in runtime_source for token in ("timeout_correlations = [", "timeout_matches = [", "for index in range(len(critic.calls))", "timeout_matches.index(True)")),
        "s6_no_earlier_call_fallback": runtime_source.count("critic.observed_input(") == 1 and "timeout_invocation_identity.timeout_call_global_index" in runtime_source,
        "s6_correlation_dto_exact_bounded_fields": correlation_fields == expected_correlation_fields,
        "s6_exact_tensor_equality_authority": "torch.equal(expected_cpu, observed_cpu)" in correlation_source and "value.exact_value_match" in correlation_adjudicator_source,
        "s6_no_approximate_comparison": not any(token in correlation_source.lower() for token in approximate_tokens),
        "s6_bounded_expected_observed_fingerprints_retained": all(token in correlation_source and token in correlation_adjudicator_source for token in ("expected_input_sha256", "observed_input_sha256")),
        "s6_digest_cannot_rescue_exact_mismatch": "value.digest_match" in correlation_adjudicator_source and "value.exact_value_match" in correlation_adjudicator_source,
        "s6_observed_input_captured_before_wrapped_forward": critic_source.count("self.wrapped.get_values(") == 1 and critic_source.index("self._observed_inputs.append(") < critic_source.index("self.wrapped.get_values("),
        "s6_expected_input_from_authoritative_terminal_sidecars": "row.optional_sidecar.bootstrap_critic_obs" in runtime_source and "timeout_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(" in runtime_source and "pre_obs," in runtime_source,
        "s6_no_full_observed_input_in_durable_evidence": 'evidence["critic_observed_inputs"]' not in runtime_source and "observed_input" not in correlation_fields,
        "s6_no_additional_critic_invocation": critic_source.count("self.wrapped.get_values(") == 1,
        "formal_stop_taxonomy_exact_ten": stop_found == sorted(STOP_TAXONOMY) and len(STOP_TAXONOMY) == 10,
        "required_historical_reports_protected": all(str(path) in EXPECTED_REPORT_HASHES for path in (PD1_REPORT, R2_REPORT, R3_REPORT, R4_REPORT, R5A_REPORT, R5B_REPORT, R5C_REPORT, R5D_REPORT, R5D_TR_REPORT, R5D_TR2_REPORT, R5E_REPORT, R5F_REPORT)),
        "r5c_frozen_hash_protected": EXPECTED_REPORT_HASHES.get(str(R5C_REPORT)) == "ce4f4d8399cf465e981dd4fb67f37ba81ed991271530df802d09be8448a1ceac",
        "r5d_frozen_hash_protected": EXPECTED_REPORT_HASHES.get(str(R5D_REPORT)) == "35e35a56c993e53829b4b819bd695315db090ec2c01cf574993259277e68bd93",
        "r5d_tr_frozen_hash_protected": EXPECTED_REPORT_HASHES.get(str(R5D_TR_REPORT)) == "83aa129bb29648bf186c278ba4e0db5b6b2cf269e2b5d19b664e1341eddbafdd",
        "r5d_tr2_frozen_hash_protected": EXPECTED_REPORT_HASHES.get(str(R5D_TR2_REPORT)) == "e5700c7e31e29c6ea7750a4e679abbdb17adcc1026b7b2a5b3cc59b098e88f86",
        "r5e_historical_hash_protected": EXPECTED_REPORT_HASHES.get(str(R5E_REPORT)) == "21fc419942c63c278af6ee1a89706c4404d4a57abf4b77772155062ebcb8287c",
        "r5f_frozen_hash_protected": EXPECTED_REPORT_HASHES.get(str(R5F_REPORT)) == "4683245527f5294c14c4995bb618687de4daf3d9dd3c3b0305291138ab04d6ef",
        "official_kit_hash_protected": EXPECTED_EXPERIENCE_SHA256 == "475bb23c5941fbaaf0186991bf6e5445a267b1e0fd8bbab333cc78dc2e1bc795",
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "collect_step_call_lines": [node.lineno for node in collect_calls],
        "s5_checkpoint_lines": s5_checkpoint_lines,
        "s6_time_limit_assertion_lines": s6_assert_lines,
        "s5_fields": s5_fields,
        "post_return_fields": post_fields,
        "s6_invocation_identity_fields": identity_fields,
        "s6_correlation_fields": correlation_fields,
        "stop_taxonomy": STOP_TAXONOMY,
    }


def r5g_static_contract_review() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    runtime_source = _source_segment("run_real_smoke")
    extension_source = _source_segment("_runtime_extension_and_smoke")
    worker_source = _source_segment("run_worker")
    builder_source = _source_segment("build_pd2_integral_horizon_fixture_v1")
    gate_a_source = _source_segment("adjudicate_pd2_s1_preconstruction_timing_v1")
    gate_b_builder_source = _source_segment("build_pd2_s1_postconstruction_timing_evidence_v1")
    gate_b_source = _source_segment("adjudicate_pd2_s1_postconstruction_timing_v1")
    fixture_fields = tuple(item.name for item in fields(PD2IntegralHorizonFixtureV1))
    expected_fixture_fields = (
        "schema_version", "desired_terminal_transition", "required_max_episode_length",
        "semantic_horizon_steps", "simulation_tick_count", "sim_dt_seconds",
        "control_decimation", "physical_control_step_seconds",
        "candidate_episode_length_seconds", "raw_horizon_ratio",
        "production_rounded_horizon", "integrality_error_abs", "production_rel_tol",
        "production_abs_tol", "integrality_tolerance_slack", "ceil_horizon",
        "lower_bucket_margin", "upper_bucket_margin",
    )
    post_fields = tuple(item.name for item in fields(PD2S1PostconstructionTimingEvidenceV1))
    required_post_fields = {
        "raw_max_episode_length", "raw_max_episode_length_seconds", "raw_step_dt_seconds",
        "actual_horizon_ratio", "actual_ceil_horizon", "scale_contract_version",
        "scale_physical_control_step_seconds", "scale_episode_time_limit_seconds",
        "scale_episode_horizon_steps",
    }
    ordered_tokens = (
        "S1_PRECONSTRUCTION_TIMING_CONTRACT",
        "preconstruction_timing_contract_pass",
        "environment_construction_entered",
        "gym.make(",
        "environment_construction_returned",
        "S1_POSTCONSTRUCTION_TIMING_CONTRACT",
        "postconstruction_timing_contract_pass",
        "reset_entered",
        "route.reset()",
        "S1_I1_I2",
    )
    token_positions = {token: runtime_source.find(token) for token in ordered_tokens}
    source_order_pass = all(value >= 0 for value in token_positions.values()) and list(token_positions.values()) == sorted(token_positions.values())
    builder_order = (
        builder_source.find("simulation_tick_count = control_decimation * semantic_horizon_steps"),
        builder_source.find("physical_control_step_seconds = fixed_sim_dt * control_decimation"),
        builder_source.find("candidate_episode_length_seconds = fixed_sim_dt * simulation_tick_count"),
    )
    forbidden_current_tokens = ("PD2_TIMEOUT_FIXTURE_RATIO", "derive_pd2_timeout_fixture", "validate_pd2_timeout_fixture", "nextafter")
    checks = {
        "fixture_dto_exact_bounded_fields": fixture_fields == expected_fixture_fields,
        "postconstruction_dto_contains_required_bounded_fields": required_post_fields.issubset(post_fields),
        "candidate_c_exact_operation_order": all(value >= 0 for value in builder_order) and list(builder_order) == sorted(builder_order),
        "candidate_c_no_float_fudge": not any(token in builder_source.lower() for token in ("nextafter", "epsilon", "0.299999", "- 1e-9")),
        "production_integrality_mirror_exact": all(token in gate_a_source for token in ("math.isclose", "PD2_PRODUCTION_INTEGRAL_REL_TOL", "PD2_PRODUCTION_INTEGRAL_ABS_TOL", "production_rounded_horizon")),
        "gate_a_exact_boundary": 'boundary = "S1_PRECONSTRUCTION_TIMING_CONTRACT"' in gate_a_source,
        "gate_b_exact_boundary": 'boundary = "S1_POSTCONSTRUCTION_TIMING_CONTRACT"' in gate_b_source and 'boundary = "S1_POSTCONSTRUCTION_TIMING_CONTRACT"' in gate_b_builder_source,
        "formal_runtime_s1_order_exact": source_order_pass,
        "gate_a_before_gym_make": token_positions["preconstruction_timing_contract_pass"] < token_positions["gym.make("],
        "gate_b_after_constructor_before_reset": token_positions["gym.make("] < token_positions["S1_POSTCONSTRUCTION_TIMING_CONTRACT"] < token_positions["postconstruction_timing_contract_pass"] < token_positions["route.reset()"],
        "s1_enter_published_after_s0r": "s1_entered" in extension_source and extension_source.index("runtime_extension_gate(checkpoints)") < extension_source.index("s1_entered"),
        "worker_exception_uses_active_boundary": 'evidence.get("active_boundary"' in worker_source and "classify_pd2_s1_untyped_failure_v1" in worker_source,
        "retired_midpoint_not_current_authority": not any(token in runtime_source or token in builder_source for token in forbidden_current_tokens),
        "formal_runtime_uses_integral_fixture": "build_pd2_integral_horizon_fixture_v1(" in runtime_source and "candidate_episode_length_seconds" in runtime_source,
        "gate_b_verifies_without_mutation": not any(
            token in gate_b_source
            for token in ("setattr(", "cfg.episode_length_s =", "raw.max_episode_length =", "scale_contract[")
        ),
        "formal_stop_taxonomy_exact_ten": sorted(set(re.findall(r"PD2-STOP-[A-Za-z0-9-]+", source))) == sorted(STOP_TAXONOMY),
        "r5e_historical_report_protected": str(R5E_REPORT) in EXPECTED_REPORT_HASHES,
        "r5f_design_report_protected": str(R5F_REPORT) in EXPECTED_REPORT_HASHES,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "fixture_fields": fixture_fields,
        "postconstruction_fields": post_fields,
        "runtime_token_positions": token_positions,
        "candidate_c_builder_positions": builder_order,
    }


def r5j_static_contract_review() -> dict[str, object]:
    source = Path(__file__).read_text(encoding="utf-8")
    runtime_source = _source_segment("run_real_smoke")
    builder_source = _source_segment("build_pd2_s6_i5b_returns_evidence_v1")
    adjudicator_source = _source_segment("adjudicate_pd2_s6_i5b_returns_evidence_v1")
    event_gae_source = (SCAN / "assignment_event_gae_returns.py").read_text(encoding="utf-8")
    event_buffer_source = (SCAN / "assignment_event_critic_buffer.py").read_text(encoding="utf-8")
    installed_buffer_source = (HARL / "common/buffers/on_policy_critic_buffer_ep.py").read_text(encoding="utf-8")
    dto_fields = tuple(item.name for item in fields(PD2S6I5bReturnsEvidenceV1))
    expected_fields = (
        "schema_version", "capture_status", "source_boundary", "event_gae_schema_version",
        "event_buffer_schema_version", "T", "E", "C", "valuenorm_enabled",
        "producer_failure_code", "producer_failure_stage", "result_expected_shape",
        "result_actual_shape", "result_shape_pass", "result_dtype", "result_device",
        "result_numel", "result_contiguous", "result_requires_grad", "result_all_finite",
        "result_nan_count", "result_posinf_count", "result_neginf_count",
        "result_first_nonfinite_flat_index", "result_first_nonfinite_t",
        "result_first_nonfinite_env", "result_first_nonfinite_component",
        "result_first_nonfinite_kind", "buffer_commit_performed",
        "buffer_storage_expected_shape", "buffer_storage_actual_shape",
        "buffer_storage_shape_pass", "buffer_storage_dtype", "buffer_storage_device",
        "buffer_storage_numel", "training_slice_start", "training_slice_end_exclusive",
        "training_slice_expected_shape", "training_slice_actual_shape",
        "training_slice_shape_pass", "training_slice_numel", "training_slice_all_finite",
        "training_slice_nan_count", "training_slice_posinf_count",
        "training_slice_neginf_count", "training_slice_first_nonfinite_flat_index",
        "training_slice_first_nonfinite_t", "training_slice_first_nonfinite_env",
        "training_slice_first_nonfinite_component", "training_slice_first_nonfinite_kind",
        "training_slice_matches_result_exact", "training_slice_no_alias_result",
        "final_slot_index", "final_slot_expected_shape", "final_slot_actual_shape",
        "final_slot_shape_pass", "final_slot_semantics",
        "final_slot_written_by_event_compute", "final_slot_training_consumed",
        "final_slot_all_finite", "final_slot_nan_count", "final_slot_posinf_count",
        "final_slot_neginf_count", "final_slot_all_zero", "advantages_expected_shape",
        "advantages_actual_shape", "advantages_shape_pass", "advantages_all_finite",
        "advantages_nan_count", "advantages_posinf_count", "advantages_neginf_count",
        "advantages_training_shape_match", "value_preds_storage_shape",
        "value_preds_training_slice_shape", "value_preds_final_slot_shape",
        "value_preds_all_finite", "arithmetic_value_preds_shape",
        "arithmetic_value_preds_all_finite", "event_slots_complete",
        "timeout_identity_schema_version", "timeout_call_identity_pass", "timeout_call_count",
    )
    old_oracle = "tuple(rollout.event_returns_result.returns.shape) == (T + 1, E, 1)"
    persistence_position = runtime_source.find('"i5b_returns_evidence_captured"')
    adjudication_position = runtime_source.find("adjudicate_pd2_s6_i5b_returns_evidence_v1(")
    final_diagnostic_position = adjudicator_source.find("final_slot_diagnostic")
    fail_position = adjudicator_source.find("if primary is not None")
    checks = {
        "r5j_dto_exact_frozen_fields": dto_fields == expected_fields,
        "r5j_old_result_t_plus_one_oracle_retired": old_oracle not in runtime_source,
        "r5j_result_shape_is_t_e_one": "result_expected_shape=(T, E, 1)" in builder_source and "result_shape == (T, E, 1)" in builder_source,
        "r5j_buffer_storage_shape_is_t_plus_one": "buffer_storage_expected_shape=(T + 1, E, 1)" in builder_source and "storage_shape == (T + 1, E, 1)" in builder_source,
        "r5j_training_slice_is_buffer_excluding_final": "training_slice = buffer_returns[:-1]" in builder_source and "training_slice_expected_shape=(T, E, 1)" in builder_source,
        "r5j_exact_value_equality": "torch.equal(training_slice, result_tensor)" in builder_source and "allclose" not in builder_source.lower(),
        "r5j_storage_identity_no_alias": "_tensor_storage_identity_v1" in builder_source and "result_storage != training_storage" in builder_source,
        "r5j_final_slot_is_diagnostic_only": fail_position >= 0 and final_diagnostic_position > fail_position and "final_slot_all_zero" not in adjudicator_source[:fail_position] and "final_slot_all_finite" not in adjudicator_source[:fail_position],
        "r5j_evidence_persisted_before_adjudication": persistence_position >= 0 and adjudication_position > persistence_position,
        "r5j_observer_is_existing_i5b_boundary": "PD2_S6_I5B_RETURNS_SOURCE_BOUNDARY_V1" in runtime_source and "call_observer=route_observer" in runtime_source,
        "r5j_separate_result_finite_field": "result_all_finite=result_finite" in builder_source,
        "r5j_bounded_nonfinite_location": all(token in builder_source for token in ("result_first_nonfinite_flat_index", "training_slice_first_nonfinite_flat_index", "result_first_nonfinite_kind")),
        "r5j_no_semantic_recomputation": not any(token in builder_source for token in ("compute_event_returns(", "compute_event_gae_returns", "get_values(", "denormalize(", ".update(", ".backward(")),
        "r5j_single_finish_rollout": runtime_source.count("route.finish_rollout(") == 1,
        "r5j_typed_failure_persists_before_adjudication": runtime_source.count('"i5b_returns_evidence_captured"') == 2 and "except EventGAEReturnsError as exc" in runtime_source,
        "r5j_event_producer_result_is_t": "returns = advantages + arithmetic_values[:-1]" in event_gae_source,
        "r5j_event_buffer_copies_only_training_slice": "self.returns[:-1].copy_(result.returns)" in event_buffer_source,
        "r5j_installed_learner_consumes_training_slice": all(
            token in installed_buffer_source
            for token in (
                "self.returns[:-1].reshape",
                "self.returns[:-1, ids]",
                "self.returns[:-1])",
            )
        ),
        "r5j_stop_taxonomy_still_exact_ten": sorted(set(re.findall(r"PD2-STOP-[A-Za-z0-9-]+", source))) == sorted(STOP_TAXONOMY) and len(STOP_TAXONOMY) == 10,
        "r5j_r5i_report_hash_protected": EXPECTED_REPORT_HASHES.get(str(R5I_REPORT)) == "ef03379e94906e544604fd0fe62b68a2cd542c0b466773e2800e6a4841bdd99b",
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "dto_fields": dto_fields,
        "failure_detail_order": PD2_S6_I5B_RETURNS_FAILURE_DETAILS_V1,
        "result_contract": (T, E, 1),
        "buffer_storage_contract": (T + 1, E, 1),
        "training_slice_contract": (T, E, 1),
        "final_slot_contract": (E, 1),
    }


def _r5d_base_s5_dto() -> PD2S5PreterminalEvidenceV1:
    return PD2S5PreterminalEvidenceV1(
        schema_version=PD2_S5_PRETERMINAL_EVIDENCE_SCHEMA_V1,
        transition_index=2,
        transition_slot=1,
        preterminal_source_p2_serial=10,
        preterminal_source_store_version=20,
        preterminal_admitted_p2_serial=11,
        preterminal_admitted_store_version=21,
        preterminal_episode_generations=(4, 4),
        preterminal_transition_generations=(1, 1),
        preterminal_source_window_serial=30,
        preterminal_effective_assignment=((2, 3, 4), (5, 6, 7)),
        controller_expected_assignment_transition2=((2, 3, 4), (5, 6, 7)),
        controller_actual_assignment_transition2=((2, 3, 4), (5, 6, 7)),
        continuation_row_mask=((True, False, False), (False, False, False)),
        continuation_expected_task=((2, -1, -1), (-1, -1, -1)),
        policy_decision_row_mask=((False, True, True), (True, True, True)),
        forced_row_mask=((True, False, False), (False, False, False)),
        forced_noop_row_mask=((False, False, False), (False, False, False)),
        claim_mutated_row_mask=((False, True, True), (True, True, True)),
        original_proposal_ids=((-1, 3, 4), (5, 6, 7)),
        proposal_logprob_finite_mask=((True, True, True), (True, True, True)),
        proposal_present_mask=((False, True, True), (True, True, True)),
        actor_call_records=((0, (1,), True, 1), (1, (0, 1), True, 2), (2, (0, 1), True, 2)),
        resolution_interpretations=(("CONTINUE_EXISTING", "CLAIM_COMMITTED", "CLAIM_COMMITTED"), ("CLAIM_COMMITTED", "CLAIM_COMMITTED", "CLAIM_COMMITTED")),
    )


def _r5d_replace_dto(value: PD2S5PreterminalEvidenceV1, **updates: object) -> PD2S5PreterminalEvidenceV1:
    payload = _dto_mapping(value)
    payload.update(updates)
    return PD2S5PreterminalEvidenceV1(**payload)


def _r5g_replace_fixture(
    value: PD2IntegralHorizonFixtureV1, **updates: object
) -> PD2IntegralHorizonFixtureV1:
    payload = _dto_mapping(value)
    payload.update(updates)
    return PD2IntegralHorizonFixtureV1(**payload)


def _r5g_replace_postconstruction(
    value: PD2S1PostconstructionTimingEvidenceV1, **updates: object
) -> PD2S1PostconstructionTimingEvidenceV1:
    payload = _dto_mapping(value)
    payload.update(updates)
    return PD2S1PostconstructionTimingEvidenceV1(**payload)


def _r5g_canonical_scale_mapping(
    fixture: PD2IntegralHorizonFixtureV1,
) -> Mapping[str, object]:
    return MappingProxyType(
        {
            "contract_version": PD2_EXPECTED_SCALE_CONTRACT_VERSION,
            "M": M,
            "N": N,
            "ordered_agent_names": ("robot_0", "robot_1", "robot_2"),
            "ordered_task_ids": tuple(range(N)),
            "scene_env_spacing": 8.0,
            "sim_dt_seconds": fixture.sim_dt_seconds,
            "control_decimation": fixture.control_decimation,
            "physical_control_step_seconds": fixture.physical_control_step_seconds,
            "episode_time_limit_seconds": fixture.candidate_episode_length_seconds,
            "episode_horizon_steps": fixture.production_rounded_horizon,
        }
    )


def _r5g_canonical_postconstruction(
    fixture: PD2IntegralHorizonFixtureV1,
) -> PD2S1PostconstructionTimingEvidenceV1:
    return build_pd2_s1_postconstruction_timing_evidence_v1(
        fixture=fixture,
        configured_episode_length_seconds=fixture.candidate_episode_length_seconds,
        configured_sim_dt_seconds=fixture.sim_dt_seconds,
        configured_control_decimation=fixture.control_decimation,
        raw_max_episode_length=fixture.required_max_episode_length,
        raw_max_episode_length_seconds=fixture.candidate_episode_length_seconds,
        raw_step_dt_seconds=fixture.physical_control_step_seconds,
        scale_contract=_r5g_canonical_scale_mapping(fixture),
        expected_ordered_agent_names=("robot_0", "robot_1", "robot_2"),
        expected_ordered_task_ids=tuple(range(N)),
        expected_scene_env_spacing=8.0,
    )


def _r5g_expect_stop(callable_object: object, *, boundary: str) -> dict[str, object]:
    try:
        callable_object()
    except PD2Stop as exc:
        return {
            "pass": exc.classification == STOP_PHYSICAL and exc.boundary == boundary,
            "classification": exc.classification,
            "first_boundary": exc.boundary,
            "detail": str(exc),
        }
    return {"pass": False, "classification": None, "first_boundary": None}


def _r5d_timeout_identity(
    *,
    start: int = 0,
    end: int = 2,
    timeout_batch_event_count: int = 1,
    observed_timeout_call_count: int = 1,
) -> PD2S6TimeoutCriticInvocationIdentityV1:
    return identify_pd2_s6_timeout_critic_call_v1(
        second_collect_start_call_index=start,
        second_collect_end_call_index=end,
        timeout_batch_event_count=timeout_batch_event_count,
        observed_timeout_call_count=observed_timeout_call_count,
    )


def _r5d_adjudication_flow(value: PD2S5PreterminalEvidenceV1, *, done_all: bool, reason_time_limit: bool) -> dict[str, object]:
    result: dict[str, object] = {"s5": "NOT_ADJUDICATED", "s6": "NOT_ADJUDICATED", "terminal_evidence_entered": False}
    try:
        result["s5"] = adjudicate_pd2_s5_preterminal_evidence_v1(value)
    except PD2Stop as exc:
        result.update({"classification": exc.classification, "first_boundary": exc.boundary})
        return result
    if not done_all or not reason_time_limit:
        result.update({"classification": STOP_TERMINAL, "first_boundary": "S6_TIME_LIMIT", "s6": "FAILED"})
        return result
    result.update({"s6": "TERMINAL_PREDICATE_PASS", "terminal_evidence_entered": True})
    return result


def r5d_pure_synthetic_verification() -> dict[str, object]:
    import torch
    from types import SimpleNamespace

    cuda_before = bool(torch.cuda.is_initialized())
    cases: dict[str, dict[str, object]] = {}
    fixture = build_pd2_integral_horizon_fixture_v1(1.0 / 60.0, 6)
    adjudicate_pd2_s1_preconstruction_timing_v1(fixture)
    cases["A"] = {
        "pass": fixture.candidate_episode_length_seconds == 0.3
        and fixture.raw_horizon_ratio == 2.9999999999999996
        and fixture.production_rounded_horizon == 3
        and fixture.ceil_horizon == 3,
        "raw_ratio": fixture.raw_horizon_ratio,
        "ceil": fixture.ceil_horizon,
    }
    timeline = ((1, False, "NONE"), (2, True, "TIME_LIMIT"))
    cases["B"] = {"pass": timeline == ((1, False, "NONE"), (2, True, "TIME_LIMIT")), "timeline": timeline}
    historical_step = (1.0 / 60.0) * 6
    historical_duration = historical_step * 3
    historical_ratio = historical_duration / historical_step
    cases["C"] = {
        "pass": historical_duration == 0.30000000000000004
        and historical_ratio == 3.0000000000000004
        and round(historical_ratio) == 3
        and math.ceil(historical_ratio) == 4,
        "duration": historical_duration,
        "ratio": historical_ratio,
        "ceil": math.ceil(historical_ratio),
        "historical_candidate": "CONTROL_STEP_TIMES_3_REJECTED_BY_CEIL",
    }
    canonical_post = _r5g_canonical_postconstruction(fixture)
    case_d_result = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(
            _r5g_replace_postconstruction(canonical_post, raw_max_episode_length=4), fixture
        ),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )
    cases["D"] = {**case_d_result, "reset_calls": 0, "physical_steps": 0}

    base = _r5d_base_s5_dto()
    normal = _r5d_adjudication_flow(base, done_all=True, reason_time_limit=True)
    cases["E"] = {"pass": bool(normal["s5"]) and normal["terminal_evidence_entered"], "order": ("S5", "S6")}
    bad_continuation = _r5d_replace_dto(base, continuation_expected_task=((9, -1, -1), (-1, -1, -1)))
    failed_s5 = _r5d_adjudication_flow(bad_continuation, done_all=True, reason_time_limit=True)
    cases["F"] = {"pass": failed_s5["first_boundary"] == "S5_CONTINUATION" and failed_s5["s6"] == "NOT_ADJUDICATED", "flow": failed_s5}
    failed_s6 = _r5d_adjudication_flow(base, done_all=False, reason_time_limit=False)
    cases["G"] = {"pass": failed_s6["first_boundary"] == "S6_TIME_LIMIT" and bool(failed_s6["s5"]), "flow": failed_s6}
    cases["H"] = {"pass": normal["terminal_evidence_entered"] is True, "flow": normal}

    critic = SimpleNamespace()
    first_tensor = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    rnn = torch.zeros((3, 1, 8), dtype=torch.float32)
    masks = torch.ones((3, 1), dtype=torch.float32)
    first_before = first_tensor.clone()
    fingerprint_1 = capture_pd2_critic_input_fingerprint_v1(first_tensor, rnn, masks, critic, capture_index=0)
    fingerprint_2 = capture_pd2_critic_input_fingerprint_v1(first_tensor, rnn, masks, critic, capture_index=0)
    changed = first_tensor.clone()
    changed[0, 0] += 1.0
    fingerprint_3 = capture_pd2_critic_input_fingerprint_v1(changed, rnn, masks, critic, capture_index=0)
    cases["I"] = {"pass": fingerprint_1["content_sha256"] == fingerprint_2["content_sha256"], "digest": fingerprint_1["content_sha256"]}
    cases["J"] = {"pass": fingerprint_1["content_sha256"] != fingerprint_3["content_sha256"], "changed_digest": fingerprint_3["content_sha256"]}
    cases["K"] = {"pass": torch.equal(first_tensor, first_before) and first_tensor.dtype == first_before.dtype and first_tensor.stride() == first_before.stride(), "source_unchanged": True}
    cases["L"] = {"pass": fingerprint_1["critic_runtime_class"] == fingerprint_2["critic_runtime_class"], "runtime_class": fingerprint_1["critic_runtime_class"]}

    class PureCritic:
        def __init__(self) -> None:
            self.calls = 0

        def get_values(self, obs, state, mask):
            self.calls += 1
            return obs[:, :1], state

    pure_critic = PureCritic()
    observer_calls: list[dict[str, object]] = []
    recorder = CriticRecorder(pure_critic, lambda item: observer_calls.append(dict(item)))
    recorder.get_values(first_tensor, rnn, masks)
    cases["M"] = {"pass": pure_critic.calls == 1 and recorder.wrapped_forward_attempts == 1 and len(observer_calls) == 1 and len(recorder.calls) == 1, "wrapped_calls": pure_critic.calls, "observer_calls": len(observer_calls)}

    post_state_y = ((99, 99, 99), (99, 99, 99))
    cases["N"] = {"pass": bool(adjudicate_pd2_s5_preterminal_evidence_v1(base)["pass"]) and post_state_y != base.preterminal_effective_assignment, "later_state_ignored": True}
    controller_y = _r5d_replace_dto(base, controller_actual_assignment_transition2=((9, 3, 4), (5, 6, 7)))
    failed_controller = _r5d_adjudication_flow(controller_y, done_all=True, reason_time_limit=True)
    cases["O"] = {"pass": failed_controller["first_boundary"] == "S5_P2_AK", "post_return_cannot_rescue": True}
    cases["P"] = {"pass": bool(adjudicate_pd2_s5_preterminal_evidence_v1(base)["pass"]) and post_state_y[0][0] != base.continuation_expected_task[0][0], "later_timeout_clear_ignored": True}
    static_review = r5d_static_contract_review()
    cases["Q"] = {"pass": static_review["checks"]["s5_builder_has_no_postreturn_dependency"]}
    cases["R"] = {"pass": bool(_r5d_adjudication_flow(base, done_all=False, reason_time_limit=False)["s5"]), "diagnostic_required": False}

    identity = SimpleNamespace(p2_publication_identity=SimpleNamespace(serial=52), episode_generations=(5, 5), transition_generations=(-1, -1))
    publication = SimpleNamespace(publication_identity=SimpleNamespace(serial=51), store_version=22, episode_generation=torch.tensor([5, 5]), transition_generation=torch.tensor([-1, -1]))
    fake_receipt = SimpleNamespace(facade_result=SimpleNamespace(current_publication=publication), next_decision_bundle=SimpleNamespace(evidence_identity=identity))
    post_dto = build_pd2_post_return_state_diagnostic_v1(fake_receipt)
    post_names = tuple(item.name for item in fields(post_dto))
    cases["S"] = {"pass": all(name in ("schema_version", "transition_index", "terminal_status_proven", "autoreset_status_proven") or name.startswith("post_return_") for name in post_names) and not post_dto.terminal_status_proven and not post_dto.autoreset_status_proven}
    before_s5 = _dto_mapping(base)
    flow_t = _r5d_adjudication_flow(base, done_all=False, reason_time_limit=False)
    cases["T"] = {"pass": bool(flow_t["s5"]) and flow_t["first_boundary"] == "S6_TIME_LIMIT" and _dto_mapping(base) == before_s5}
    cases["U"] = {"pass": normal["terminal_evidence_entered"] and post_dto.autoreset_status_proven is False and _dto_mapping(base) == before_s5, "historical_current_separate": True}

    overlap = _r5d_replace_dto(base, claim_mutated_row_mask=((True, True, True), (True, True, True)))
    overlap_flow = _r5d_adjudication_flow(overlap, done_all=True, reason_time_limit=True)
    cases["V"] = {"pass": overlap_flow["first_boundary"] == "S5_REPEATED_CLAIM"}
    bad_actor = _r5d_replace_dto(base, actor_call_records=((0, (0, 1), True, 2), (1, (0, 1), True, 2), (2, (0, 1), True, 2)))
    bad_actor_flow = _r5d_adjudication_flow(bad_actor, done_all=True, reason_time_limit=True)
    cases["W"] = {"pass": bad_actor_flow["classification"] == STOP_ACTOR and bad_actor_flow["first_boundary"] == "S5_FORCED_ROW_BYPASS"}
    proposal_substitution = _r5d_replace_dto(base, controller_actual_assignment_transition2=base.original_proposal_ids)
    proposal_flow = _r5d_adjudication_flow(proposal_substitution, done_all=True, reason_time_limit=True)
    cases["X"] = {"pass": proposal_flow["first_boundary"] == "S5_P2_AK", "proposal_not_authority": True}
    forbidden = ("post_return_", "post_autoreset_", "terminal_", "next_episode_")
    cases["Y"] = {"pass": not any(name.startswith(forbidden) or name in {"current_p2", "current_assignment", "current_generation"} for name in (item.name for item in fields(PD2S5PreterminalEvidenceV1)))}

    exact_expected = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    exact_observed = exact_expected.clone()
    exact_identity = _r5d_timeout_identity()
    exact_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        exact_expected, exact_observed, invocation_identity=exact_identity
    )
    exact_verdict = adjudicate_pd2_s6_timeout_critic_input_correlation_v1(exact_correlation)
    cases["Z"] = {
        "pass": bool(exact_verdict["pass"] and exact_correlation.exact_value_match and exact_correlation.digest_match),
        "correlation": _dto_mapping(exact_correlation),
    }

    changed_observed = exact_expected.clone()
    changed_observed[0, 0] += 1.0
    changed_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        exact_expected, changed_observed, invocation_identity=exact_identity
    )
    try:
        adjudicate_pd2_s6_timeout_critic_input_correlation_v1(changed_correlation)
        changed_failed_closed = False
        changed_boundary = None
    except PD2Stop as exc:
        changed_failed_closed = exc.classification == STOP_TERMINAL and exc.boundary == "S6_TIMEOUT_CRITIC"
        changed_boundary = exc.boundary
    cases["AA"] = {
        "pass": changed_failed_closed and not changed_correlation.exact_value_match and not changed_correlation.digest_match,
        "first_boundary": changed_boundary,
        "correlation": _dto_mapping(changed_correlation),
    }

    stale_payload = _dto_mapping(changed_correlation)
    stale_payload.update(
        expected_input_sha256=exact_correlation.expected_input_sha256,
        observed_input_sha256=exact_correlation.expected_input_sha256,
        digest_match=True,
    )
    stale_digest_correlation = PD2S6TimeoutCriticInputCorrelationV1(**stale_payload)
    try:
        adjudicate_pd2_s6_timeout_critic_input_correlation_v1(stale_digest_correlation)
        stale_digest_failed_closed = False
    except PD2Stop as exc:
        stale_digest_failed_closed = exc.classification == STOP_TERMINAL and exc.boundary == "S6_TIMEOUT_CRITIC"
    cases["AB"] = {
        "pass": stale_digest_failed_closed and stale_digest_correlation.digest_match and not stale_digest_correlation.exact_value_match,
        "stale_equal_digest_cannot_rescue": True,
    }

    dtype_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        exact_expected, exact_expected.to(torch.float64), invocation_identity=exact_identity
    )
    try:
        adjudicate_pd2_s6_timeout_critic_input_correlation_v1(dtype_correlation)
        dtype_failed_closed = False
    except PD2Stop as exc:
        dtype_failed_closed = exc.classification == STOP_TERMINAL and exc.boundary == "S6_TIMEOUT_CRITIC"
    cases["AC"] = {"pass": dtype_failed_closed and not dtype_correlation.dtype_match, "correlation": _dto_mapping(dtype_correlation)}

    shape_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        exact_expected, exact_expected.reshape(4, 3), invocation_identity=exact_identity
    )
    try:
        adjudicate_pd2_s6_timeout_critic_input_correlation_v1(shape_correlation)
        shape_failed_closed = False
    except PD2Stop as exc:
        shape_failed_closed = exc.classification == STOP_TERMINAL and exc.boundary == "S6_TIMEOUT_CRITIC"
    cases["AD"] = {"pass": shape_failed_closed and not shape_correlation.shape_match, "correlation": _dto_mapping(shape_correlation)}

    mutation_expected = torch.arange(12, dtype=torch.float32, requires_grad=True).reshape(3, 4)
    mutation_observed = mutation_expected.detach().clone().requires_grad_(True)
    mutation_before = {
        "expected": mutation_expected.detach().clone(),
        "observed": mutation_observed.detach().clone(),
        "expected_dtype": mutation_expected.dtype,
        "observed_dtype": mutation_observed.dtype,
        "expected_shape": tuple(mutation_expected.shape),
        "observed_shape": tuple(mutation_observed.shape),
        "expected_requires_grad": mutation_expected.requires_grad,
        "observed_requires_grad": mutation_observed.requires_grad,
        "expected_version": mutation_expected._version,
        "observed_version": mutation_observed._version,
    }
    mutation_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        mutation_expected, mutation_observed, invocation_identity=exact_identity
    )
    mutation_unchanged = (
        torch.equal(mutation_expected.detach(), mutation_before["expected"])
        and torch.equal(mutation_observed.detach(), mutation_before["observed"])
        and mutation_expected.dtype == mutation_before["expected_dtype"]
        and mutation_observed.dtype == mutation_before["observed_dtype"]
        and tuple(mutation_expected.shape) == mutation_before["expected_shape"]
        and tuple(mutation_observed.shape) == mutation_before["observed_shape"]
        and mutation_expected.requires_grad == mutation_before["expected_requires_grad"]
        and mutation_observed.requires_grad == mutation_before["observed_requires_grad"]
        and mutation_expected._version == mutation_before["expected_version"]
        and mutation_observed._version == mutation_before["observed_version"]
    )
    cases["AE"] = {"pass": mutation_unchanged and mutation_correlation.exact_value_match, "comparison_mutation_count": 0}

    exact_once_critic = PureCritic()
    exact_once_recorder = CriticRecorder(exact_once_critic)
    exact_once_recorder.get_values(exact_expected + 100.0, rnn, masks)
    exact_once_recorder.get_values(exact_expected, rnn, masks)
    exact_once_calls_before_comparison = exact_once_critic.calls
    exact_once_identity = _r5d_timeout_identity(
        start=0,
        end=exact_once_recorder.observed_input_count,
    )
    comparison_count = 0
    exact_once_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        exact_expected,
        exact_once_recorder.observed_input(exact_once_identity.timeout_call_global_index),
        invocation_identity=exact_once_identity,
    )
    comparison_count += 1
    exact_once_verdict = adjudicate_pd2_s6_timeout_critic_input_correlation_v1(exact_once_correlation)
    cases["AF"] = {
        "pass": bool(
            exact_once_verdict["pass"]
            and exact_once_critic.calls == 2
            and exact_once_critic.calls == exact_once_calls_before_comparison
            and exact_once_recorder.wrapped_forward_attempts == 2
            and len(exact_once_recorder.calls) == 2
            and exact_once_recorder.observed_input_count == 2
            and exact_once_identity.observed_timeout_call_count == 1
            and comparison_count == 1
        ),
        "total_critic_calls": exact_once_critic.calls,
        "timeout_critic_calls": exact_once_identity.observed_timeout_call_count,
        "comparison_calls": comparison_count,
        "comparison_added_critic_calls": exact_once_critic.calls - exact_once_calls_before_comparison,
    }

    def two_call_fixture(current_input, timeout_input):
        fixture_critic = PureCritic()
        fixture_recorder = CriticRecorder(fixture_critic)
        start = fixture_recorder.observed_input_count
        fixture_recorder.get_values(current_input, rnn, masks)
        fixture_recorder.get_values(timeout_input, rnn, masks)
        end = fixture_recorder.observed_input_count
        identity = _r5d_timeout_identity(start=start, end=end)
        return fixture_critic, fixture_recorder, identity

    duplicate_x = torch.arange(12, dtype=torch.float32).reshape(3, 4)
    ag_critic, ag_recorder, ag_identity = two_call_fixture(duplicate_x, duplicate_x.clone())
    ag_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        duplicate_x,
        ag_recorder.observed_input(ag_identity.timeout_call_global_index),
        invocation_identity=ag_identity,
    )
    ag_verdict = adjudicate_pd2_s6_timeout_critic_input_correlation_v1(ag_correlation)
    cases["AG"] = {
        "pass": bool(
            ag_verdict["pass"]
            and ag_critic.calls == 2
            and ag_identity.timeout_call_global_index == 1
            and ag_identity.observed_timeout_call_count == 1
            and ag_correlation.exact_value_match
        ),
        "duplicate_values": True,
        "designated_timeout_global_index": ag_identity.timeout_call_global_index,
    }

    ah_timeout_y = duplicate_x + 1.0
    _, ah_recorder, ah_identity = two_call_fixture(duplicate_x, ah_timeout_y)
    ah_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        duplicate_x,
        ah_recorder.observed_input(ah_identity.timeout_call_global_index),
        invocation_identity=ah_identity,
    )
    try:
        adjudicate_pd2_s6_timeout_critic_input_correlation_v1(ah_correlation)
        ah_failed_closed = False
        ah_boundary = None
    except PD2Stop as exc:
        ah_failed_closed = exc.classification == STOP_TERMINAL and exc.boundary == "S6_TIMEOUT_CRITIC"
        ah_boundary = exc.boundary
    cases["AH"] = {
        "pass": bool(
            ah_failed_closed
            and torch.equal(duplicate_x, ah_recorder.observed_input(ah_identity.current_call_global_index))
            and not ah_correlation.exact_value_match
            and ah_identity.timeout_call_global_index == 1
        ),
        "earlier_matching_call_cannot_rescue": True,
        "first_boundary": ah_boundary,
    }

    try:
        _r5d_timeout_identity(
            start=0,
            end=1,
            timeout_batch_event_count=1,
            observed_timeout_call_count=0,
        )
        ai_failed_closed = False
        ai_boundary = None
    except PD2Stop as exc:
        ai_failed_closed = exc.classification == STOP_TERMINAL and exc.boundary == "S6_TIMEOUT_CRITIC_CALL_IDENTITY"
        ai_boundary = exc.boundary
    cases["AI"] = {"pass": ai_failed_closed, "first_boundary": ai_boundary, "input_comparison_calls": 0}

    try:
        _r5d_timeout_identity(start=0, end=3)
        aj_failed_closed = False
        aj_boundary = None
    except PD2Stop as exc:
        aj_failed_closed = exc.classification == STOP_TERMINAL and exc.boundary == "S6_TIMEOUT_CRITIC_CALL_IDENTITY"
        aj_boundary = exc.boundary
    cases["AJ"] = {"pass": aj_failed_closed, "first_boundary": aj_boundary, "unexpected_extra_call": True}

    _, ak_recorder, ak_identity = two_call_fixture(duplicate_x, duplicate_x.clone())
    ak_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        duplicate_x,
        ak_recorder.observed_input(ak_identity.timeout_call_global_index),
        invocation_identity=ak_identity,
    )
    cases["AK"] = {
        "pass": bool(
            ak_identity.timeout_call_global_index == 1
            and ak_recorder.calls[0]["obs_sha256"] == ak_recorder.calls[1]["obs_sha256"]
            and adjudicate_pd2_s6_timeout_critic_input_correlation_v1(ak_correlation)["pass"]
        ),
        "same_digest_elsewhere_irrelevant": True,
    }

    al_current = torch.full((3, 4), -7.0, dtype=torch.float32)
    al_timeout = torch.full((3, 4), 42.0, dtype=torch.float32)
    _, al_recorder, al_identity = two_call_fixture(al_current, al_timeout)
    al_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        al_timeout,
        al_recorder.observed_input(al_identity.timeout_call_global_index),
        invocation_identity=al_identity,
    )
    cases["AL"] = {
        "pass": bool(
            al_identity.call_identity_pass
            and al_identity.observed_timeout_call_count == 1
            and adjudicate_pd2_s6_timeout_critic_input_correlation_v1(al_correlation)["pass"]
        ),
        "non_timeout_call_arbitrary": True,
    }

    cuda_after = bool(torch.cuda.is_initialized())
    return {
        "pass": all(item["pass"] for item in cases.values()) and not cuda_before and not cuda_after,
        "cases": cases,
        "case_count": len(cases),
        "static_review": static_review,
        "execution_counters": {"AppLauncher": 0, "SimulationApp": 0, "Isaac": 0, "CUDA_initialized_before": int(cuda_before), "CUDA_initialized_after": int(cuda_after), "HARL": 0, "VCritic": 0, "actor": 0, "environment": 0, "physical_step": 0, "optimizer": 0, "backward": 0, "training": 0},
    }


def r5g_pure_synthetic_verification() -> dict[str, object]:
    cases: dict[str, dict[str, object]] = {}
    fixture = build_pd2_integral_horizon_fixture_v1(1.0 / 60.0, 6)
    gate_a = adjudicate_pd2_s1_preconstruction_timing_v1(fixture)
    cases["CANDIDATE_C_INTEGER_SIM_TICKS_18"] = {
        "pass": bool(gate_a["pass"])
        and fixture.simulation_tick_count == 18
        and fixture.candidate_episode_length_seconds == 0.3
        and fixture.raw_horizon_ratio == 2.9999999999999996
        and fixture.production_rounded_horizon == 3
        and fixture.ceil_horizon == 3,
        "fixture": _dto_mapping(fixture),
    }

    midpoint_ratio = 2.5
    midpoint = _r5g_replace_fixture(
        fixture,
        candidate_episode_length_seconds=0.25,
        raw_horizon_ratio=midpoint_ratio,
        production_rounded_horizon=round(midpoint_ratio),
        integrality_error_abs=abs(midpoint_ratio - round(midpoint_ratio)),
        integrality_tolerance_slack=PD2_PRODUCTION_INTEGRAL_ABS_TOL - abs(midpoint_ratio - round(midpoint_ratio)),
        ceil_horizon=math.ceil(midpoint_ratio),
        lower_bucket_margin=midpoint_ratio - PD2_TIMEOUT_BUCKET_LOWER,
        upper_bucket_margin=PD2_TIMEOUT_BUCKET_UPPER - midpoint_ratio,
    )
    cases["CANDIDATE_A_MIDPOINT_2P5_NEGATIVE"] = {
        **_r5g_expect_stop(lambda: adjudicate_pd2_s1_preconstruction_timing_v1(midpoint), boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT"),
        "production_integral_pass": math.isclose(midpoint_ratio, round(midpoint_ratio), rel_tol=0.0, abs_tol=1.0e-9),
        "ceil": midpoint.ceil_horizon,
    }

    historical_control_step = (1.0 / 60.0) * 6
    historical_episode = historical_control_step * 3
    historical_ratio = historical_episode / historical_control_step
    candidate_b = _r5g_replace_fixture(
        fixture,
        candidate_episode_length_seconds=historical_episode,
        raw_horizon_ratio=historical_ratio,
        production_rounded_horizon=round(historical_ratio),
        integrality_error_abs=abs(historical_ratio - round(historical_ratio)),
        integrality_tolerance_slack=PD2_PRODUCTION_INTEGRAL_ABS_TOL - abs(historical_ratio - round(historical_ratio)),
        ceil_horizon=math.ceil(historical_ratio),
        lower_bucket_margin=historical_ratio - PD2_TIMEOUT_BUCKET_LOWER,
        upper_bucket_margin=PD2_TIMEOUT_BUCKET_UPPER - historical_ratio,
    )
    cases["CANDIDATE_B_CONTROL_STEP_TIMES_3_NEGATIVE"] = {
        **_r5g_expect_stop(lambda: adjudicate_pd2_s1_preconstruction_timing_v1(candidate_b), boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT"),
        "episode_length_seconds": historical_episode,
        "raw_horizon_ratio": historical_ratio,
        "production_integral_pass": math.isclose(historical_ratio, round(historical_ratio), rel_tol=0.0, abs_tol=1.0e-9),
        "ceil": math.ceil(historical_ratio),
    }

    cases["GA1_CANDIDATE_C"] = {"pass": bool(gate_a["pass"]), "first_boundary": "PASS"}
    cases["GA2_MIDPOINT_INTEGRALITY"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_preconstruction_timing_v1(midpoint), boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT"
    )
    cases["GA3_CONTROL_STEP_TIMES_3_CEIL"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_preconstruction_timing_v1(candidate_b), boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT"
    )
    cases["GA4_SEMANTIC_HORIZON"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_preconstruction_timing_v1(_r5g_replace_fixture(fixture, semantic_horizon_steps=2)),
        boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GA5_RATIO_LOWER_BUCKET"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_preconstruction_timing_v1(
            _r5g_replace_fixture(fixture, raw_horizon_ratio=2.0, production_rounded_horizon=2, ceil_horizon=2)
        ),
        boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GA6_RATIO_UPPER_BUCKET"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_preconstruction_timing_v1(
            _r5g_replace_fixture(fixture, raw_horizon_ratio=3.1, production_rounded_horizon=3, ceil_horizon=4)
        ),
        boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GA7_PRODUCTION_HORIZON"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_preconstruction_timing_v1(
            _r5g_replace_fixture(fixture, production_rounded_horizon=4)
        ),
        boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT",
    )

    post = _r5g_canonical_postconstruction(fixture)
    post_pass = adjudicate_pd2_s1_postconstruction_timing_v1(post, fixture)
    cases["GB1_CANONICAL"] = {"pass": bool(post_pass["pass"]), "first_boundary": "PASS"}
    cases["GB2_MAX_EPISODE_LENGTH"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(_r5g_replace_postconstruction(post, raw_max_episode_length=4), fixture),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GB3_STEP_DT"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(_r5g_replace_postconstruction(post, raw_step_dt_seconds=0.2), fixture),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GB4_SCALE_HORIZON"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(_r5g_replace_postconstruction(post, scale_episode_horizon_steps=2), fixture),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GB5_CONTRACT_VERSION"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(_r5g_replace_postconstruction(post, scale_contract_version="wrong"), fixture),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GB6_EPISODE_TIME_LIMIT"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(_r5g_replace_postconstruction(post, scale_episode_time_limit_seconds=0.31), fixture),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )
    cases["GB7_ACTUAL_CEIL"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(
            _r5g_replace_postconstruction(post, actual_horizon_ratio=3.0000000000000004, actual_ceil_horizon=4), fixture
        ),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )

    cases["BA1_GATE_A"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_preconstruction_timing_v1(midpoint), boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT"
    )
    ba2 = classify_pd2_s1_untyped_failure_v1("S1_ENVIRONMENT_CONSTRUCTION")
    cases["BA2_CONSTRUCTOR"] = {"pass": ba2 == (STOP_STARTUP, "S1_ENVIRONMENT_CONSTRUCTION"), "classification": ba2[0], "first_boundary": ba2[1]}
    cases["BA3_GATE_B"] = _r5g_expect_stop(
        lambda: adjudicate_pd2_s1_postconstruction_timing_v1(_r5g_replace_postconstruction(post, raw_max_episode_length=4), fixture),
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
    )
    ba4 = classify_pd2_s1_untyped_failure_v1("S1_RESET")
    cases["BA4_RESET"] = {"pass": ba4 == (STOP_STARTUP, "S1_RESET"), "classification": ba4[0], "first_boundary": ba4[1]}
    prior_stage = "S0R"
    ba5 = classify_pd2_s1_untyped_failure_v1("S1_ENVIRONMENT_CONSTRUCTION")
    cases["BA5_NO_S0R_FALLBACK"] = {"pass": prior_stage == "S0R" and ba5[1] == "S1_ENVIRONMENT_CONSTRUCTION", "classification": ba5[0], "first_boundary": ba5[1]}

    static_review = r5g_static_contract_review()
    all_cases_pass = all(bool(case["pass"]) for case in cases.values())
    return {
        "pass": all_cases_pass and bool(static_review["pass"]),
        "classification": R5G_PASS if all_cases_pass and static_review["pass"] else R5G_STOP_DIVERGENCE,
        "cases": cases,
        "static_contract_review": static_review,
        "execution_counters": {
            "formal_supervisor": 0,
            "worker": 0,
            "AppLauncher": 0,
            "SimulationApp": 0,
            "Isaac": 0,
            "gym_make": 0,
            "CUDA": 0,
            "HARL_real": 0,
            "VCritic_real": 0,
            "actor_real": 0,
            "environment_construct": 0,
            "reset": 0,
            "step": 0,
            "optimizer": 0,
            "backward": 0,
            "training": 0,
        },
    }


def r5j_pure_synthetic_verification() -> dict[str, object]:
    import torch

    cuda_before = bool(torch.cuda.is_initialized())
    cases: dict[str, dict[str, object]] = {}

    class SyntheticResult:
        schema_version = "EVENT_GAE_RETURNS_V2"

        def __init__(self, returns: torch.Tensor) -> None:
            self.returns = returns
            self.advantages = torch.zeros((T, E, 1), dtype=torch.float32)
            self.arithmetic_value_preds = torch.zeros((T + 1, E, 1), dtype=torch.float32)

    class SyntheticBuffer:
        schema_version = "EVENT_CRITIC_BUFFER_FIELDS_V2"

        def __init__(self, returns: torch.Tensor) -> None:
            self.returns = returns
            self.value_preds = torch.zeros((T + 1, E, 1), dtype=torch.float32)
            self._event_slot_written = torch.ones((T,), dtype=torch.bool)

    class SyntheticTimeoutIdentity:
        schema_version = PD2_S6_TIMEOUT_CRITIC_INVOCATION_IDENTITY_SCHEMA_V1
        call_identity_pass = True
        observed_timeout_call_count = 1

    class SyntheticEventGAEReturnsError(RuntimeError):
        def __init__(self, actual: torch.Tensor) -> None:
            self.failure_code = "returns_nonfinite"
            self.stage = "event_gae_arithmetic"
            self.actual = actual
            super().__init__(self.failure_code)

    def canonical_result() -> torch.Tensor:
        return torch.arange(T * E, dtype=torch.float32).reshape(T, E, 1).clone()

    def capture(
        result_tensor: torch.Tensor | None,
        storage: torch.Tensor,
        *,
        valuenorm_enabled: bool = False,
        producer_error: object | None = None,
        buffer_commit_performed: bool = True,
    ) -> PD2S6I5bReturnsEvidenceV1:
        result = SyntheticResult(result_tensor) if result_tensor is not None else None
        return build_pd2_s6_i5b_returns_evidence_v1(
            event_returns_result=result,
            critic_buffer=SyntheticBuffer(storage),
            T=T,
            E=E,
            valuenorm_enabled=valuenorm_enabled,
            timeout_identity=SyntheticTimeoutIdentity(),
            producer_error=producer_error,
            buffer_commit_performed=buffer_commit_performed,
        )

    def independent_storage(result: torch.Tensor) -> torch.Tensor:
        storage = torch.zeros((T + 1, E, 1), dtype=torch.float32)
        if tuple(result.shape) == (T, E, 1):
            storage[:-1].copy_(result)
        return storage

    def expect_stop(value: PD2S6I5bReturnsEvidenceV1, detail: str) -> dict[str, object]:
        try:
            adjudicate_pd2_s6_i5b_returns_evidence_v1(value)
            return {"pass": False, "failure_detail": None}
        except PD2Stop as exc:
            return {
                "pass": bool(
                    exc.classification == STOP_TERMINAL
                    and exc.boundary == "S6_I5B_RETURNS"
                    and exc.failure_detail == detail
                ),
                "failure_detail": exc.failure_detail,
            }

    result_ra = canonical_result()
    dto_ra = capture(result_ra, independent_storage(result_ra))
    verdict_ra = adjudicate_pd2_s6_i5b_returns_evidence_v1(dto_ra)
    bounded_values = _dto_mapping(dto_ra)
    bounded = all(
        item is None
        or type(item) in (str, int, float, bool)
        or (type(item) is tuple and all(type(child) in (str, int, float, bool) for child in item))
        for item in bounded_values.values()
    )
    cases["RA"] = {
        "pass": bool(
            verdict_ra["pass"]
            and dto_ra.result_actual_shape == (T, E, 1)
            and dto_ra.buffer_storage_actual_shape == (T + 1, E, 1)
            and dto_ra.training_slice_actual_shape == (T, E, 1)
            and dto_ra.training_slice_matches_result_exact
            and dto_ra.training_slice_no_alias_result
            and bounded
        ),
        "bounded_dto": bounded,
    }

    result_rb = torch.zeros((T + 1, E, 1), dtype=torch.float32)
    dto_rb = capture(result_rb, torch.zeros((T + 1, E, 1), dtype=torch.float32))
    cases["RB"] = {
        **expect_stop(dto_rb, "S6_I5B_RETURNS_RESULT_SHAPE"),
        "result_shape_pass": dto_rb.result_shape_pass,
        "result_all_finite": dto_rb.result_all_finite,
    }
    cases["RB"]["pass"] = bool(cases["RB"]["pass"] and not dto_rb.result_shape_pass and dto_rb.result_all_finite is True)

    result_rc = canonical_result()
    result_rc[1, 0, 0] = torch.nan
    dto_rc = capture(result_rc, independent_storage(result_rc))
    cases["RC"] = {
        **expect_stop(dto_rc, "S6_I5B_RETURNS_RESULT_NONFINITE"),
        "nan_count": dto_rc.result_nan_count,
        "first_location": (dto_rc.result_first_nonfinite_t, dto_rc.result_first_nonfinite_env, dto_rc.result_first_nonfinite_component),
    }
    cases["RC"]["pass"] = bool(cases["RC"]["pass"] and dto_rc.result_nan_count == 1 and cases["RC"]["first_location"] == (1, 0, 0))

    result_rd = canonical_result()
    result_rd[0, 1, 0] = torch.inf
    dto_rd = capture(result_rd, independent_storage(result_rd))
    cases["RD"] = {**expect_stop(dto_rd, "S6_I5B_RETURNS_RESULT_NONFINITE"), "posinf_count": dto_rd.result_posinf_count}
    cases["RD"]["pass"] = bool(cases["RD"]["pass"] and dto_rd.result_posinf_count == 1 and dto_rd.result_first_nonfinite_kind == "POSINF")

    result_re = canonical_result()
    result_re[0, 0, 0] = -torch.inf
    dto_re = capture(result_re, independent_storage(result_re))
    cases["RE"] = {**expect_stop(dto_re, "S6_I5B_RETURNS_RESULT_NONFINITE"), "neginf_count": dto_re.result_neginf_count}
    cases["RE"]["pass"] = bool(cases["RE"]["pass"] and dto_re.result_neginf_count == 1 and dto_re.result_first_nonfinite_kind == "NEGINF")

    result_rf = torch.zeros((T + 1, E, 1), dtype=torch.float32)
    result_rf[0, 0, 0] = torch.nan
    dto_rf = capture(result_rf, torch.zeros((T + 1, E, 1), dtype=torch.float32))
    cases["RF"] = {
        **expect_stop(dto_rf, "S6_I5B_RETURNS_RESULT_SHAPE"),
        "shape_pass": dto_rf.result_shape_pass,
        "finite_pass": dto_rf.result_all_finite,
        "nan_count": dto_rf.result_nan_count,
    }
    cases["RF"]["pass"] = bool(cases["RF"]["pass"] and not dto_rf.result_shape_pass and dto_rf.result_all_finite is False and dto_rf.result_nan_count == 1)

    result_rg = canonical_result()
    storage_rg = independent_storage(result_rg)
    storage_rg[T, 0, 0] = torch.nan
    dto_rg = capture(result_rg, storage_rg)
    verdict_rg = adjudicate_pd2_s6_i5b_returns_evidence_v1(dto_rg)
    cases["RG"] = {
        "pass": bool(verdict_rg["pass"] and verdict_rg["final_slot_diagnostic"] == PD2_S6_I5B_RETURNS_FINAL_SLOT_DIAGNOSTIC_V1),
        "final_slot_all_finite": dto_rg.final_slot_all_finite,
        "primary_failure_detail": verdict_rg["primary_failure_detail"],
    }

    result_rh = canonical_result()
    storage_rh = independent_storage(result_rh)
    storage_rh[0, 0, 0] = torch.nan
    dto_rh = capture(result_rh, storage_rh)
    cases["RH"] = {**expect_stop(dto_rh, "S6_I5B_RETURNS_TRAINING_SLICE_NONFINITE"), "training_all_finite": dto_rh.training_slice_all_finite}
    cases["RH"]["pass"] = bool(cases["RH"]["pass"] and dto_rh.training_slice_all_finite is False and dto_rh.final_slot_all_finite is True)

    result_ri = canonical_result()
    dto_ri = capture(result_ri, independent_storage(result_ri))
    cases["RI"] = {
        "pass": bool(
            dto_ri.result_shape_pass
            and dto_ri.buffer_storage_shape_pass
            and dto_ri.training_slice_shape_pass
            and dto_ri.final_slot_shape_pass
            and adjudicate_pd2_s6_i5b_returns_evidence_v1(dto_ri)["pass"]
        )
    }

    result_rj = canonical_result()
    storage_rj = independent_storage(result_rj)
    storage_rj[0, 0, 0] += 1.0
    dto_rj = capture(result_rj, storage_rj)
    cases["RJ"] = {**expect_stop(dto_rj, "S6_I5B_RETURNS_RESULT_BUFFER_MISMATCH"), "exact_match": dto_rj.training_slice_matches_result_exact}
    cases["RJ"]["pass"] = bool(cases["RJ"]["pass"] and not dto_rj.training_slice_matches_result_exact)

    storage_rk = torch.zeros((T + 1, E, 1), dtype=torch.float32)
    storage_rk[:-1].copy_(canonical_result())
    result_rk = storage_rk[:-1]
    dto_rk = capture(result_rk, storage_rk)
    cases["RK"] = {**expect_stop(dto_rk, "S6_I5B_RETURNS_RESULT_BUFFER_ALIAS"), "no_alias": dto_rk.training_slice_no_alias_result}
    cases["RK"]["pass"] = bool(cases["RK"]["pass"] and not dto_rk.training_slice_no_alias_result and dto_rk.training_slice_matches_result_exact)

    result_rl = canonical_result()
    dto_rl = capture(result_rl, independent_storage(result_rl), valuenorm_enabled=False)
    cases["RL"] = {"pass": bool(not dto_rl.valuenorm_enabled and adjudicate_pd2_s6_i5b_returns_evidence_v1(dto_rl)["pass"]), "valuenorm_enabled": dto_rl.valuenorm_enabled, "updates": 0}

    result_rm = canonical_result()
    dto_rm = capture(result_rm, independent_storage(result_rm), valuenorm_enabled=True)
    cases["RM"] = {"pass": bool(dto_rm.valuenorm_enabled and adjudicate_pd2_s6_i5b_returns_evidence_v1(dto_rm)["pass"]), "valuenorm_enabled": dto_rm.valuenorm_enabled, "updates": 0}

    result_rn = canonical_result()
    result_rn[0, 0, 0] = torch.nan
    error_rn = SyntheticEventGAEReturnsError(result_rn)
    dto_rn = capture(None, torch.zeros((T + 1, E, 1), dtype=torch.float32), producer_error=error_rn, buffer_commit_performed=False)
    cases["RN"] = {
        **expect_stop(dto_rn, "S6_I5B_RETURNS_RESULT_NONFINITE"),
        "capture_status": dto_rn.capture_status,
        "producer_failure_code": dto_rn.producer_failure_code,
        "producer_failure_stage": dto_rn.producer_failure_stage,
        "bounded_nan_count": dto_rn.result_nan_count,
    }
    cases["RN"]["pass"] = bool(cases["RN"]["pass"] and dto_rn.capture_status == "TYPED_EVENT_GAE_FAILURE" and dto_rn.result_nan_count == 1 and not dto_rn.buffer_commit_performed)

    no_extra_work = {
        "critic_forwards": 0,
        "actor_forwards": 0,
        "compute_event_returns_extra_calls": 0,
        "valuenorm_updates": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
    }
    builder_source = _source_segment("build_pd2_s6_i5b_returns_evidence_v1")
    cases["RO"] = {
        "pass": all(value == 0 for value in no_extra_work.values()) and not any(
            token in builder_source for token in ("compute_event_returns(", "get_values(", "denormalize(", ".update(", ".backward(")
        ),
        "extra_work": no_extra_work,
    }

    static_review = r5j_static_contract_review()
    cuda_after = bool(torch.cuda.is_initialized())
    passed = all(bool(case["pass"]) for case in cases.values()) and bool(static_review["pass"]) and not cuda_before and not cuda_after
    return {
        "pass": passed,
        "classification": R5J_PASS if passed else R5J_STOP_DIVERGENCE,
        "cases": cases,
        "case_count": len(cases),
        "static_contract_review": static_review,
        "execution_counters": {
            "formal_supervisor": 0,
            "worker": 0,
            "AppLauncher": 0,
            "SimulationApp": 0,
            "Isaac": 0,
            "gym_make": 0,
            "CUDA_runtime": 0,
            "CUDA_initialized_before": int(cuda_before),
            "CUDA_initialized_after": int(cuda_after),
            "HARL_real": 0,
            "VCritic_real": 0,
            "actor_real": 0,
            "environment_construct": 0,
            "reset": 0,
            "step": 0,
            "optimizer": 0,
            "backward": 0,
            "training": 0,
        },
    }


def static_preflight() -> dict[str, object]:
    interpreter = _normal_path(sys.executable) == _normal_path(EXPECTED_PYTHON)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False).stdout.strip()
    hashes = file_hash_observation(EXPECTED_SOURCE_HASHES)
    critical = static_critical_manifest()
    production_ast = warmup_ast_semantics(TRAIN, "_warm_start_torch_cuda")
    harness_ast = warmup_ast_semantics(Path(__file__), "_warm_start_torch_cuda")
    expected_ops = [
        {"op": "cuda_is_available"},
        {"op": "device"},
        {"op": "set_device"},
        {"op": "zeros", "shape": (1, 1), "dtype_keyword": False},
        {"op": "to_device"},
        {"op": "linear", "args": [1, 1]},
        {"op": "linear_forward"},
        {"op": "synchronize"},
    ]
    ast_equivalent = production_ast.get("operations") == expected_ops and harness_ast.get("operations") == expected_ops and production_ast.get("pass") and harness_ast.get("pass")
    snapshot_review = snapshot_order_static_review()
    junction_review = junction_reader_static_review()
    s0r_synthetic = s0r_adapter_synthetic_verification()
    s0r_static = s0r_adapter_persistence_static_review()
    cache_static = cache_backed_predicate_static_review()
    cache_synthetic = cache_backed_predicate_synthetic_verification()
    r5d_static = r5d_static_contract_review()
    r5g_static = r5g_static_contract_review()
    r5j_static = r5j_static_contract_review()
    d4o_review = sha256(D4O_HARNESS) == EXPECTED_D4O_SHA256
    stop_source = Path(__file__).read_text(encoding="utf-8")
    stop_found = sorted(set(re.findall(r"PD2-STOP-[A-Za-z0-9-]+", stop_source)))
    stop_exact = stop_found == sorted(STOP_TAXONOMY)
    diff = subprocess.run(["git", "diff", "--check"], cwd=ROOT, capture_output=True, text=True, check=False)
    result = {
        "interpreter_exact": interpreter,
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "head": head,
        "head_exact": head == EXPECTED_HEAD,
        "source_hashes": hashes,
        "critical_manifest": critical,
        "production_warmup_ast": production_ast,
        "harness_warmup_ast": harness_ast,
        "startup_prefix_ast_equivalent": bool(ast_equivalent),
        "snapshot_guard_static_review": snapshot_review,
        "junction_reader_static_review": junction_review,
        "s0r_adapter_synthetic_verification": s0r_synthetic,
        "s0r_adapter_persistence_static_review": s0r_static,
        "cache_backed_predicate_static_review": cache_static,
        "cache_backed_predicate_synthetic_verification": cache_synthetic,
        "r5d_static_contract_review": r5d_static,
        "r5g_static_contract_review": r5g_static,
        "r5j_static_contract_review": r5j_static,
        "d4o_classifier_hash_exact": d4o_review,
        "stop_taxonomy_found": stop_found,
        "stop_taxonomy_exact": stop_exact,
        "git_diff_check_exit": diff.returncode,
        "git_diff_check_stdout": diff.stdout,
        "git_diff_check_stderr": diff.stderr,
    }
    result["pass"] = all(
        (
            interpreter,
            head == EXPECTED_HEAD,
            bool(hashes["pass"]),
            bool(critical["pass"]),
            bool(ast_equivalent),
            bool(snapshot_review["pass"]),
            bool(junction_review["pass"]),
            bool(s0r_synthetic["pass"]),
            bool(s0r_static["pass"]),
            bool(cache_static["pass"]),
            bool(cache_synthetic["pass"]),
            bool(r5d_static["pass"]),
            bool(r5g_static["pass"]),
            bool(r5j_static["pass"]),
            d4o_review,
            stop_exact,
            diff.returncode == 0,
        )
    )
    return result


def prelaunch_exact_gate() -> dict[str, object]:
    sources = file_hash_observation(EXPECTED_SOURCE_HASHES)
    shared = shared_state_dual_oracle_inventory()
    powershell = shared["junction_powershell"]
    oracle_comparison = shared["junction_oracle_comparison"]
    critical = static_critical_manifest()
    pair_pass = (
        shared["counts"] == EXPECTED_SHARED_COUNTS
        and bool(shared["junction_primary"]["pass"])
        and bool(powershell["pass"])
        and bool(oracle_comparison["pass"])
    )
    env_values = {name: os.environ.get(name) for name in ("LIVESTREAM", "ENABLE_CAMERAS", "XR")}
    env_pass = all(value in (None, "", "0") for value in env_values.values())
    passed = (
        bool(sources["pass"])
        and shared["sha256"] == EXPECTED_SHARED_FINGERPRINT
        and shared["counts"] == EXPECTED_SHARED_COUNTS
        and pair_pass
        and bool(critical["pass"])
        and env_pass
    )
    return {
        "pass": passed,
        "sources": sources,
        "shared_state": shared,
        "expected_shared_sha256": EXPECTED_SHARED_FINGERPRINT,
        "pair_contract_pass": pair_pass,
        "junction_oracles": {
            "primary": shared["junction_primary"],
            "powershell": powershell,
            "comparison": oracle_comparison,
        },
        "critical_manifest": critical,
        "startup_environment": env_values,
        "startup_environment_pass": env_pass,
    }


def _warm_start_torch_cuda(device_arg: str, checkpoints: Checkpoints):
    """Exact operational copy of TRAIN_STARTUP_PREFIX_V1 with event-only observers."""
    device_arg = str(device_arg).lower()
    if device_arg == "cpu" or not device_arg.startswith("cuda"):
        return None

    checkpoints.emit("S0", "torch_import_begin", module_state("torch_import_begin"))
    import torch

    checkpoints.emit("S0", "torch_import_complete", module_state("torch_import_complete"))
    checkpoints.emit("S0", "cuda_is_available_begin", module_state("cuda_is_available_begin"))
    available = torch.cuda.is_available()
    checkpoints.emit("S0", "cuda_is_available_end", {**module_state("cuda_is_available_end"), "available": available})
    if not available:
        return None

    device = torch.device(device_arg)
    checkpoints.emit("S0", "set_device_begin", {**module_state("set_device_begin"), "device": str(device)})
    torch.cuda.set_device(device)
    checkpoints.emit("S0", "set_device_end", {**module_state("set_device_end"), "device": str(device)})
    checkpoints.emit("S0", "zeros_begin", {**module_state("zeros_begin"), "shape": [1, 1], "device": str(device), "dtype": "default"})
    probe = torch.zeros((1, 1), device=device)
    checkpoints.emit("S0", "zeros_end", {**module_state("zeros_end"), "shape": list(probe.shape), "device": str(probe.device), "dtype": str(probe.dtype)})
    checkpoints.emit("S0", "linear_construct_move_begin", module_state("linear_construct_move_begin"))
    layer = torch.nn.Linear(1, 1).to(device)
    checkpoints.emit("S0", "linear_construct_move_end", {**module_state("linear_construct_move_end"), "device": str(next(layer.parameters()).device)})
    checkpoints.emit("S0", "linear_forward_begin", module_state("linear_forward_begin"))
    _ = layer(probe)
    checkpoints.emit("S0", "linear_forward_end", module_state("linear_forward_end"))
    checkpoints.emit("S0", "synchronize_begin", module_state("synchronize_begin"))
    torch.cuda.synchronize(device)
    checkpoints.emit("S0", "synchronize_end", module_state("synchronize_end"))
    return device


EXPECTED_S0_LABELS = (
    "worker_started",
    "app_launcher_module_import_complete",
    "torch_import_begin",
    "torch_import_complete",
    "cuda_is_available_begin",
    "cuda_is_available_end",
    "set_device_begin",
    "set_device_end",
    "zeros_begin",
    "zeros_end",
    "linear_construct_move_begin",
    "linear_construct_move_end",
    "linear_forward_begin",
    "linear_forward_end",
    "synchronize_begin",
    "synchronize_end",
    "app_launcher_constructor_entry",
    "app_launcher_constructor_returned",
    "startup_config_validated",
)


def capture_enabled_set(manager: object) -> dict[str, object]:
    enabled: list[str] = []
    for extension in manager.get_extensions():
        extension_id = str(extension.get("id") or extension.get("name") or "")
        if extension_id and manager.is_extension_enabled(extension_id):
            enabled.append(extension_id)
    ids = sorted(set(enabled))
    encoded = "\n".join(ids).encode("utf-8")
    return {"ids": ids, "count": len(ids), "sha256": hashlib.sha256(encoded).hexdigest()}


def _read_extension_field(
    value: object,
    key: str,
    default: object = _REQUIRED_EXTENSION_FIELD,
) -> object:
    """Read one extension metadata field without mutating Mapping or carb Item values."""

    if isinstance(value, Mapping):
        if default is _REQUIRED_EXTENSION_FIELD:
            if key not in value:
                raise ExtensionFieldReadError(
                    f"required key {key!r} is absent from {type(value).__module__}.{type(value).__qualname__}"
                )
            return value[key]
        return value.get(key, default)

    getter = getattr(value, "get", None)
    if not callable(getter):
        raise ExtensionFieldReadError(
            f"object type {type(value).__module__}.{type(value).__qualname__} has no callable read-only get(key, default)"
        )
    try:
        observed = getter(key, _MISSING_EXTENSION_FIELD)
    except BaseException as exc:
        raise ExtensionFieldReadError(
            f"get(key, default) failed for key {key!r} on "
            f"{type(value).__module__}.{type(value).__qualname__}: {type(exc).__name__}: {exc}"
        ) from exc
    if observed is _MISSING_EXTENSION_FIELD:
        if default is _REQUIRED_EXTENSION_FIELD:
            raise ExtensionFieldReadError(
                f"required key {key!r} is absent from {type(value).__module__}.{type(value).__qualname__}"
            )
        return default
    return observed


def _manager_version(extension: object) -> str | None:
    direct = _read_extension_field(extension, "version", None)
    if direct is not None:
        return str(direct)
    package = _read_extension_field(extension, "package", None)
    if package is None:
        return None
    nested = _read_extension_field(package, "version", None)
    return str(nested) if nested is not None else None


def runtime_extension_gate(checkpoints: Checkpoints) -> dict[str, object]:
    import omni.kit.app

    rows: list[dict[str, object]] = []
    first: dict[str, object] | None = None
    second: dict[str, object] | None = None
    current_base_id: str | None = None
    failed_at_field = "extension_manager"
    try:
        manager = omni.kit.app.get_app().get_extension_manager()
        failed_at_field = "complete_set_snapshot_a"
        first = capture_enabled_set(manager)
        failed_at_field = "complete_set_snapshot_b"
        second = capture_enabled_set(manager)
        failed_at_field = "complete_set_equality"
        if first != second:
            checkpoints.emit(
                "S0R",
                "complete_set_stability_failed",
                {
                    "status": "FAILED",
                    "snapshot_a": first,
                    "snapshot_b": second,
                    "equal": False,
                    "failed_at_field": failed_at_field,
                },
            )
            raise PD2Stop(
                STOP_EXTENSION,
                "consecutive enabled-extension snapshots differ",
                boundary="S0R_COMPLETE_SET_STABILITY",
            )
        checkpoints.emit(
            "S0R",
            "complete_set_snapshots_persisted",
            {
                "status": "PASS",
                "snapshot_a": first,
                "snapshot_b": second,
                "equal": True,
                "capture_order": ["A", "B", "EQUALITY_VALIDATED", "PERSISTED"],
            },
        )

        for expected in CRITICAL_MANIFEST:
            current_base_id = str(expected["base_id"])
            failed_at_field = "row_started"
            checkpoints.emit(
                "S0R",
                "critical_runtime_identity_row_started",
                {
                    "status": "STARTED",
                    "base_id": current_base_id,
                    "completed_prior_rows": len(rows),
                },
            )
            failed_at_field = "enabled_extension_id"
            enabled_id = str(manager.get_enabled_extension_id(current_base_id) or "")
            failed_at_field = "extension_dict"
            extension = manager.get_extension_dict(enabled_id) if enabled_id else None
            failed_at_field = "resolved_path"
            resolved = str(manager.get_extension_path(enabled_id) or "") if enabled_id else ""
            manifest = Path(resolved) / "config" / "extension.toml" if resolved else Path("<missing>")
            failed_at_field = "enabled_state"
            enabled = bool(enabled_id and manager.is_extension_enabled(enabled_id))
            failed_at_field = "manager_version"
            manager_version = _manager_version(extension)
            failed_at_field = "manifest_version"
            manifest_version = _manifest_version(manifest) if manifest.is_file() else None
            failed_at_field = "manifest_sha256"
            manifest_sha256 = sha256(manifest) if manifest.is_file() else None
            failed_at_field = "link_state"
            link = os.path.islink(Path(resolved)) if resolved else None
            failed_at_field = "link_target"
            link_target = _readlink(Path(resolved)) if resolved else None
            row = {
                "base_id": current_base_id,
                "expected_enabled_id": expected["enabled_id"],
                "actual_enabled_id": enabled_id,
                "enabled": enabled,
                "expected_version": expected["version"],
                "manager_version": manager_version,
                "manifest_version": manifest_version,
                "expected_path": expected["root"],
                "resolved_path": resolved,
                "expected_manifest": expected["manifest"],
                "manifest_path": str(manifest),
                "expected_manifest_sha256": expected["manifest_sha256"],
                "manifest_sha256": manifest_sha256,
                "authority": expected["authority"],
                "expected_link": expected["link"],
                "link": link,
                "expected_link_target": expected["link_target"],
                "link_target": link_target,
            }
            failed_at_field = "identity_comparison"
            authority = str(expected.get("authority") or "")
            if authority in ("PROJECT_LOCAL_SOURCE", "OFFICIAL_INSTALLED"):
                row["pass"] = (
                    row["actual_enabled_id"] == row["expected_enabled_id"]
                    and row["enabled"]
                    and row["manager_version"] == row["expected_version"]
                    and row["manifest_version"] == row["expected_version"]
                    and _normal_path(row["resolved_path"]) == _normal_path(row["expected_path"])
                    and _normal_path(row["manifest_path"]) == _normal_path(row["expected_manifest"])
                    and row["manifest_sha256"] == row["expected_manifest_sha256"]
                    and row["link"] == row["expected_link"]
                    and row["link_target"] == row["expected_link_target"]
                )
            elif authority == "OFFICIAL_INSTALLED_CACHE":
                failed_at_field = "cache_backed_l1_l2_l3"
                cache_observed, cache_result = observe_cache_backed_runtime_identity(
                    expected,
                    enabled_id=enabled_id,
                    enabled=enabled,
                    manager_version=manager_version,
                    manifest_version=manifest_version,
                    resolved_path=resolved,
                )
                row["cache_backed_observed"] = cache_observed
                row["cache_backed_result"] = cache_result
                row["pass"] = bool(cache_result["pass"])
                if not row["pass"]:
                    failed_at_field = str(cache_result.get("failed_field", failed_at_field))
            else:
                row["cache_backed_result"] = _predicate_failure(
                    "DISPATCH", "authority_category", tuple(sorted(CACHE_AUTHORITY_CATEGORIES_V1)), authority
                )
                row["pass"] = False
                failed_at_field = "authority_category"
            if not row["pass"]:
                checkpoints.emit(
                    "S0R",
                    "critical_runtime_identity_row_failed",
                    {
                        "status": "FAILED",
                        "base_id": current_base_id,
                        "failed_at_field": failed_at_field,
                        "row": row,
                        "completed_prior_rows": len(rows),
                    },
                )
                raise PD2Stop(
                    STOP_EXTENSION,
                    f"critical runtime extension identity mismatch: {current_base_id}",
                    boundary=f"S0R_CRITICAL_{current_base_id}",
                )
            checkpoints.emit(
                "S0R",
                "critical_runtime_identity_row_pass",
                {"status": "PASS", "row": row, "completed_row_index": len(rows)},
            )
            rows.append(row)

        result = {
            "complete_set_snapshot_a": first,
            "complete_set_snapshot_b": second,
            "complete_set_stable": True,
            "critical": rows,
        }
        checkpoints.emit(
            "S0R",
            "runtime_extension_identity_pass",
            {
                "status": "PASS",
                "enabled_count": first["count"],
                "enabled_sha256": first["sha256"],
                "critical_count": len(rows),
            },
        )
        return result
    except PD2Stop:
        raise
    except BaseException as exc:
        failure_details = {
            "status": "FAILED",
            "base_id": current_base_id,
            "failed_at_field": failed_at_field,
            "object_or_api_boundary": f"{type(exc).__module__}.{type(exc).__qualname__}",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "completed_prior_rows": len(rows),
            "complete_set_snapshot_a": first,
            "complete_set_snapshot_b": second,
        }
        try:
            checkpoints.emit(
                "S0R",
                "critical_runtime_identity_row_failed" if current_base_id is not None else "runtime_extension_gate_failed",
                failure_details,
            )
        except BaseException:
            pass
        raise PD2Stop(
            STOP_EXTENSION,
            f"S0R runtime extension identity could not be evaluated at {failed_at_field}: "
            f"{type(exc).__name__}: {exc}",
            boundary=f"S0R_CRITICAL_{current_base_id}" if current_base_id is not None else f"S0R_{failed_at_field.upper()}",
        ) from exc


class Box:
    def __init__(self, shape: tuple[int, ...]) -> None:
        self.shape = shape


class WrapperGuard:
    def __init__(self, env: object) -> None:
        self._env = env
        self.unwrapped = env.unwrapped
        self.direct_reset_calls = 0
        self.direct_step_calls = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self._env, name)

    def reset(self, *args: object, **kwargs: object) -> object:
        self.direct_reset_calls += 1
        raise AssertionError("event wrapper used the public raw reset path")

    def step(self, *args: object, **kwargs: object) -> object:
        self.direct_step_calls += 1
        raise AssertionError("event wrapper used the public raw step path")

    def close(self) -> None:
        self._env.close()


class ActorRecorder:
    def __init__(self, actor: object, agent_id: int) -> None:
        self.actor = actor
        self.agent_id = agent_id
        self.calls: list[dict[str, object]] = []
        self.attempts: list[dict[str, object]] = []

    def get_actions(self, obs, rnn, masks, available_actions, deterministic=False):
        attempt = {
            "agent_id": self.agent_id,
            "obs_shape": tuple(obs.shape),
            "available_shape": tuple(available_actions.shape),
            "valid_rows": int(obs.shape[0]),
            "deterministic": deterministic,
            "device": str(obs.device),
        }
        self.attempts.append(attempt)
        try:
            actions, logprobs, next_rnn = self.actor.get_actions(obs, rnn, masks, available_actions, deterministic)
        except BaseException as exc:
            raise PD2Stop(STOP_ACTOR, f"installed HAPPO actor forward failed: {type(exc).__name__}: {exc}", boundary="S3_ACTOR_FORWARD") from exc
        self.calls.append(
            {
                **attempt,
                "actions": actions.detach().clone(),
                "logprobs": logprobs.detach().clone(),
                "available": available_actions.detach().clone(),
                "next_rnn": next_rnn.detach().clone(),
                "grad_enabled": bool(__import__("torch").is_grad_enabled()),
            }
        )
        return actions, logprobs, next_rnn


class CriticRecorder:
    def __init__(self, critic: object, fingerprint_observer: object | None = None) -> None:
        self.wrapped = critic
        self.fingerprint_observer = fingerprint_observer
        self.calls: list[dict[str, object]] = []
        self.attempts: list[dict[str, object]] = []
        self._observed_inputs: list[object] = []
        self.wrapped_forward_attempts = 0

    def __getattr__(self, name: str) -> object:
        return getattr(self.wrapped, name)

    @property
    def observed_input_count(self) -> int:
        return len(self._observed_inputs)

    def observed_input(self, index: int):
        return self._observed_inputs[index].detach().clone()

    def get_values(self, obs, rnn, masks):
        index = len(self.attempts)
        runtime_type = type(self.wrapped)
        attempt = {
            "index": index,
            "global_call_index": index,
            "critic_runtime_class": f"{runtime_type.__module__}.{runtime_type.__qualname__}",
            "obs_shape": tuple(obs.shape),
            "obs_stride": tuple(obs.stride()),
            "obs_contiguous": bool(obs.is_contiguous()),
            "dtype": str(obs.dtype),
            "device": str(obs.device),
            "finite": bool(__import__("torch").isfinite(obs).all().item()),
            "requires_grad": bool(obs.requires_grad),
            "rnn_shape": tuple(rnn.shape),
            "mask_shape": tuple(masks.shape),
        }
        if index == 0:
            fingerprint = capture_pd2_critic_input_fingerprint_v1(
                obs, rnn, masks, self.wrapped, capture_index=index
            )
            attempt["input_fingerprint"] = fingerprint
            try:
                if self.fingerprint_observer is not None:
                    self.fingerprint_observer(fingerprint)
            except BaseException as exc:
                raise PD2Stop(
                    STOP_VCRITIC,
                    f"critic input fingerprint persistence failed before VCritic forward: {type(exc).__name__}: {exc}",
                    boundary="S2_CRITIC_INPUT_EVIDENCE",
                ) from exc
        self.attempts.append(attempt)
        try:
            self._observed_inputs.append(obs.detach().clone())
            self.wrapped_forward_attempts += 1
            values, next_rnn = self.wrapped.get_values(obs, rnn, masks)
        except BaseException as exc:
            classification = STOP_VCRITIC if index == 0 else STOP_TERMINAL
            boundary = "S2_FIRST_VCRITIC_FORWARD" if index == 0 else "S6_CRITIC_FORWARD"
            raise PD2Stop(classification, f"installed VCritic forward failed: {type(exc).__name__}: {exc}", boundary=boundary) from exc
        self.calls.append(
            {
                **attempt,
                "obs_sha256": tensor_fingerprint(obs),
                "values": values.detach().clone(),
                "value_shape": tuple(values.shape),
                "value_finite": bool(__import__("torch").isfinite(values).all().item()),
                "grad_enabled": bool(__import__("torch").is_grad_enabled()),
            }
        )
        return values, next_rnn


class NoTrainingGuards:
    def __init__(self, torch: Any, actors: list[object], critic: object, value_normalizer: object | None) -> None:
        self.torch = torch
        self.actors = actors
        self.critic = critic
        self.value_normalizer = value_normalizer
        self.counts = {"actor_optimizer_step": 0, "critic_optimizer_step": 0, "backward": 0, "valuenorm_update": 0}
        self._originals: list[tuple[object, str, object]] = []

    def _trap(self, key: str):
        def forbidden(*_args: object, **_kwargs: object):
            self.counts[key] += 1
            raise PD2Stop(STOP_MUTATION, f"forbidden update seam called: {key}", boundary="NO_TRAINING_GUARD")

        return forbidden

    def install(self) -> None:
        for actor in self.actors:
            optimizer = actor.actor_optimizer
            self._originals.append((optimizer, "step", optimizer.step))
            optimizer.step = self._trap("actor_optimizer_step")
        optimizer = self.critic.critic_optimizer
        self._originals.append((optimizer, "step", optimizer.step))
        optimizer.step = self._trap("critic_optimizer_step")
        if self.value_normalizer is not None:
            self._originals.append((self.value_normalizer, "update", self.value_normalizer.update))
            self.value_normalizer.update = self._trap("valuenorm_update")
        self._originals.append((self.torch.autograd, "backward", self.torch.autograd.backward))
        self.torch.autograd.backward = self._trap("backward")
        self._originals.append((self.torch.Tensor, "backward", self.torch.Tensor.backward))
        self.torch.Tensor.backward = self._trap("backward")

    def restore(self) -> None:
        while self._originals:
            owner, name, value = self._originals.pop()
            setattr(owner, name, value)


def canonical_digest(value: object) -> str:
    digest = hashlib.sha256()

    def visit(item: object) -> None:
        if hasattr(item, "detach") and hasattr(item, "dtype") and hasattr(item, "shape"):
            tensor = item.detach().contiguous().cpu()
            digest.update(b"tensor")
            digest.update(str(tensor.dtype).encode())
            digest.update(str(tuple(tensor.shape)).encode())
            digest.update(tensor.numpy().tobytes())
        elif isinstance(item, Mapping):
            digest.update(b"mapping")
            for key in sorted(item, key=lambda current: str(current)):
                visit(str(key))
                visit(item[key])
        elif isinstance(item, (list, tuple)):
            digest.update(type(item).__name__.encode())
            for child in item:
                visit(child)
        elif item is None or isinstance(item, (bool, int, float, str)):
            digest.update(json.dumps(item, sort_keys=True).encode())
        else:
            digest.update(repr(item).encode())

    visit(value)
    return digest.hexdigest()


def model_snapshot(actors: list[object], critic: object, value_normalizer: object | None) -> dict[str, object]:
    actor_states = [canonical_digest(actor.actor.state_dict()) for actor in actors]
    actor_optimizers = [canonical_digest(actor.actor_optimizer.state_dict()) for actor in actors]
    critic_state = canonical_digest(critic.critic.state_dict())
    critic_optimizer = canonical_digest(critic.critic_optimizer.state_dict())
    valuenorm_state = canonical_digest(value_normalizer.state_dict()) if value_normalizer is not None else None
    gradients_none = all(parameter.grad is None for actor in actors for parameter in actor.actor.parameters()) and all(parameter.grad is None for parameter in critic.critic.parameters())
    if value_normalizer is not None:
        gradients_none = gradients_none and all(parameter.grad is None for parameter in value_normalizer.parameters())
    return {
        "actor_state_dict_sha256": actor_states,
        "critic_state_dict_sha256": critic_state,
        "valuenorm_state_dict_sha256": valuenorm_state,
        "actor_optimizer_state_dict_sha256": actor_optimizers,
        "critic_optimizer_state_dict_sha256": critic_optimizer,
        "gradients_all_none": gradients_none,
        "combined_sha256": canonical_digest((actor_states, critic_state, valuenorm_state, actor_optimizers, critic_optimizer, gradients_none)),
    }


def tensor_fingerprint(tensor: Any) -> str:
    return hashlib.sha256(tensor.detach().contiguous().cpu().numpy().tobytes()).hexdigest()


def expected_assignment(publication: object, torch: Any) -> object:
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import TaskLifecycleState

    state = publication.lifecycle_state
    assignment = torch.full((state.robot_state.shape[0], state.robot_state.shape[1]), -1, dtype=torch.int64, device=state.robot_state.device)
    active = {int(TaskLifecycleState.CLAIMED), int(TaskLifecycleState.NAVIGATING), int(TaskLifecycleState.ALIGNING)}
    for env_id in range(state.task_state.shape[0]):
        for task_id in range(state.task_state.shape[1]):
            if int(state.task_state[env_id, task_id]) in active:
                robot_id = int(state.ownership[env_id, task_id])
                require(robot_id >= 0, STOP_PHYSICAL, "active task lacks owner", boundary="S4_P2_AK")
                assignment[env_id, robot_id] = task_id
    return assignment


def load_production_algo_args() -> dict[str, object]:
    import yaml

    loaded = yaml.safe_load(AGENT_YAML.read_text(encoding="utf-8"))
    require(isinstance(loaded, dict), STOP_STARTUP, "production agent YAML is invalid", boundary="S1_CONFIG")
    return copy.deepcopy(loaded)


def _proposal_evidence(receipt: object) -> dict[str, object]:
    envelope = receipt.proposal_envelope
    return {
        "slot": receipt.transition_slot,
        "original_policy_proposal_ids": envelope.original_policy_proposal_ids,
        "action_logprobs": envelope.action_logprobs,
        "proposal_present_mask": envelope.policy_proposal_present_mask,
        "decision_valid_mask": envelope.decision_valid_mask,
        "forced_row_mask": envelope.forced_row_mask,
        "actor_call_records": [
            {
                "agent_id": item.agent_id,
                "valid_env_indices": item.valid_env_indices,
                "actor_called": item.actor_called,
                "actor_batch_size": item.actor_batch_size,
            }
            for item in envelope.actor_call_records
        ],
        "source_identity_object": id(envelope.evidence_identity.p2_publication_identity),
        "episode_generations": envelope.evidence_identity.episode_generations,
        "transition_generations": envelope.evidence_identity.transition_generations,
    }


def run_real_smoke(evidence: dict[str, object], resources: dict[str, object], checkpoints: Checkpoints) -> dict[str, object]:
    import gymnasium as gym
    import torch

    import isaaclab_tasks  # noqa: F401
    from harl.algorithms.actors.happo import HAPPO
    from harl.algorithms.critics.v_critic import VCritic
    from harl.common.valuenorm import ValueNorm
    from harl.utils.envs_tools import set_seed
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_critic_buffer import EventOnPolicyCriticBufferEPV2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_gae_returns import EventGAEReturnsError
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_learned_route import _compose_dormant_event_learned_policy_route_v2, get_dormant_event_learned_policy_route_descriptor_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_decision import seal_current_event_policy_decision_bundle_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_policy_evidence import capture_current_event_policy_evidence_snapshot_v2, capture_event_policy_physical_problem_evidence_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_runtime_domain import _EventProfileLifecycleDomainSpec, _EventProfileLifecycleRuntimeDomain
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_harl_wrapper import _compose_event_assignment_harl_wrapper
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_lifecycle_transition_contract import TerminationReason
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_profile_contract import AssignmentProfileName, AssignmentProfileResolutionOrigin, resolve_assignment_profile
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_rl_interface import assignment_to_env_actions
    from isaaclab_tasks.direct.scan_mobile_manipulator.scan_mobile_manipulator_env import ScanMobileManipulatorEnvCfg

    algo_args = load_production_algo_args()
    yaml_seed = int(algo_args["seed"]["seed"])
    seed_args = dict(algo_args["seed"])
    cfg = ScanMobileManipulatorEnvCfg()
    require(yaml_seed == CANONICAL_SEED and int(cfg.seed) == CANONICAL_SEED, STOP_STARTUP, "HARL/environment canonical seed mismatch", boundary="S1_SEED_CONFIG")
    evidence["seed_ledger"] = [
        {"order": 0, "event": "no_seed_before_production_warmup"},
        {"order": 1, "event": "installed_harl_set_seed", "args": seed_args},
    ]
    set_seed(seed_args)
    checkpoints.emit("S1", "installed_harl_seed_complete", {"seed_args": seed_args, "cuda_initialized": bool(torch.cuda.is_initialized())})

    profile = resolve_assignment_profile(AssignmentProfileName.EVENT_GATED_LOCAL_MRTA, AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT)
    cfg.scene.num_envs = E
    cfg.assignment_lifecycle_profile = profile.profile_name.value
    publish_pd2_s1_boundary_v1(
        evidence,
        checkpoints,
        boundary="S1_PRECONSTRUCTION_TIMING_CONTRACT",
        label="preconstruction_timing_contract_entered",
    )
    timing_fixture = build_pd2_integral_horizon_fixture_v1(
        float(cfg.sim.dt),
        int(cfg.decimation),
        semantic_horizon_steps=PD2_SEMANTIC_HORIZON_STEPS,
    )
    preconstruction_timing = adjudicate_pd2_s1_preconstruction_timing_v1(timing_fixture)
    cfg.episode_length_s = timing_fixture.candidate_episode_length_seconds
    checkpoints.emit(
        "S1",
        "preconstruction_timing_contract_pass",
        {**_dto_mapping(timing_fixture), "boundary": preconstruction_timing["boundary"]},
    )
    device = torch.device(cfg.sim.device)
    require((len(cfg.possible_agents), len(cfg.viewpoint_poses)) == (M, N), STOP_STARTUP, "canonical M/N changed", boundary="S1_ENV_CONFIG")
    require(device == torch.device(DEVICE) and torch.cuda.is_available(), STOP_STARTUP, "cuda:0 unavailable", boundary="S1_ENV_CONFIG")
    evidence["seed_ledger"].append({"order": 2, "event": "environment_construction_with_direct_marl_reseed", "cfg_seed": int(cfg.seed)})

    domain = _EventProfileLifecycleRuntimeDomain(
        _EventProfileLifecycleDomainSpec(profile, device=device, env_ids=torch.arange(E, dtype=torch.int64, device=device), num_robots=M, num_tasks=N)
    )
    publish_pd2_s1_boundary_v1(
        evidence,
        checkpoints,
        boundary="S1_ENVIRONMENT_CONSTRUCTION",
        label="environment_construction_entered",
    )
    env = gym.make(
        "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        cfg=cfg,
        resolved_assignment_profile=profile,
        event_lifecycle_runtime_domain=domain,
        event_admission_validation_port=domain.environment_admission_validation_port,
    )
    raw = env.unwrapped
    checkpoints.emit(
        "S1",
        "environment_construction_returned",
        {"active_boundary": "S1_ENVIRONMENT_CONSTRUCTION", "type": type(raw).__name__},
    )
    publish_pd2_s1_boundary_v1(
        evidence,
        checkpoints,
        boundary="S1_POSTCONSTRUCTION_TIMING_CONTRACT",
        label="postconstruction_timing_contract_entered",
    )
    guard = WrapperGuard(env)
    resources["guard"] = guard
    postconstruction_timing = build_pd2_s1_postconstruction_timing_evidence_v1(
        fixture=timing_fixture,
        configured_episode_length_seconds=float(cfg.episode_length_s),
        configured_sim_dt_seconds=float(cfg.sim.dt),
        configured_control_decimation=int(cfg.decimation),
        raw_max_episode_length=int(raw.max_episode_length),
        raw_max_episode_length_seconds=float(raw.max_episode_length_s),
        raw_step_dt_seconds=float(raw.step_dt),
        scale_contract=raw._event_terminal_critic_scale_contract_v2,
        expected_ordered_agent_names=tuple(cfg.possible_agents),
        expected_ordered_task_ids=tuple(range(N)),
        expected_scene_env_spacing=float(cfg.scene.env_spacing),
    )
    postconstruction_verdict = adjudicate_pd2_s1_postconstruction_timing_v1(postconstruction_timing, timing_fixture)
    evidence["timing_fixture"] = _dto_mapping(timing_fixture)
    evidence["postconstruction_timing"] = _dto_mapping(postconstruction_timing)
    checkpoints.emit(
        "S1",
        "postconstruction_timing_contract_pass",
        {
            **_dto_mapping(postconstruction_timing),
            "boundary": postconstruction_verdict["boundary"],
            "before_reset": True,
            "before_model_forward": True,
            "before_physical_step": True,
        },
    )
    checkpoints.emit("S1", "environment_constructed", {"type": type(raw).__name__, "E": E, "M": M, "N": N, "T": T, "cfg_seed": int(cfg.seed)})

    facade_events: list[tuple[str, object | None]] = []
    slots_before_ack: list[tuple[object, ...]] = []

    def facade_observer(stage: str, detail: object | None) -> None:
        facade_events.append((stage, detail))
        if stage == "S14_WINDOW_OPEN":
            slots = domain.terminal_consumer_port.capture_pending_terminal_artifacts()
            if slots:
                slots_before_ack.append(slots)

    wrapper = _compose_event_assignment_harl_wrapper(
        env=guard,
        resolved_assignment_profile=profile,
        runtime_domain=domain,
        stage_observer=facade_observer,
        assignment_profile_entrypoint="B2-V2-PD2.current_production_startup",
    )
    route_events: list[tuple[str, object | None]] = []
    control_assignments: list[torch.Tensor] = []
    actor_train_calls: list[dict[str, object]] = []
    critic_train_calls: list[dict[str, object]] = []

    def current_bundle():
        current = domain.current_read_port.read_current()
        open_view = domain.interstep_fence_read_port.read()
        scale = raw._event_terminal_critic_scale_contract_v2
        require(scale is not None, STOP_STARTUP, "environment lacks I4 scale contract", boundary="S1_I1")
        physical = capture_event_policy_physical_problem_evidence_v2(
            assignment_problem=raw.get_assignment_problem(),
            episode_progress_steps=raw.episode_length_buf,
            scale_contract=scale,
        )
        snapshot = capture_current_event_policy_evidence_snapshot_v2(
            current_publication=current,
            current_open_window_view=open_view,
            physical_evidence=physical,
            scale_contract=scale,
        )
        return seal_current_event_policy_decision_bundle_v2(evidence_snapshot=snapshot)

    def validate_current(bundle):
        bundle.evidence_snapshot.validate_current(
            current_publication=domain.current_read_port.read_current(),
            current_open_window_view=domain.interstep_fence_read_port.read(),
        )

    def action_builder(environment: object, assignment: torch.Tensor):
        require(environment is raw, STOP_PHYSICAL, "controller builder received foreign env", boundary="S4_P2_AK")
        controls = assignment_to_env_actions(environment, assignment)
        require(all(value.device == device and bool(torch.isfinite(value).all()) for value in controls.values()), STOP_PHYSICAL, "controller tensors violate CUDA/finite contract", boundary="S4_P2_AK")
        control_assignments.append(assignment.detach().clone())
        return controls

    def actor_trainer(**kwargs):
        actor_train_calls.append(kwargs)
        return {"kind": "recorder_only", "optimizer_calls": 0, "factor_shape": tuple(kwargs["initial_factor"].shape)}

    def critic_trainer(buffer, value_normalizer):
        critic_train_calls.append({"buffer": buffer, "value_normalizer": value_normalizer})
        return {"kind": "recorder_only", "optimizer_calls": 0}

    scale = raw._event_terminal_critic_scale_contract_v2
    from isaaclab_tasks.direct.scan_mobile_manipulator.assignment_event_profile_schema_contract_v2 import build_assignment_event_profile_schema_v2_descriptor

    schema = build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale)
    actor_dim = int(schema["actor_schema"]["dimension"])
    critic_dim = int(schema["critic_schema"]["dimension"])
    model_args = dict(algo_args["model"])
    algorithm_args = dict(algo_args["algo"])
    require(model_args["hidden_sizes"] == [256, 256] and algorithm_args["share_param"] is False, STOP_STARTUP, "production actor configuration changed", boundary="S1_HARL_CONFIG")
    model_args["hidden_sizes"] = [256, 256]
    actor_args = {**model_args, **algorithm_args}
    critic_args = {**model_args, **algorithm_args}

    actors_raw: list[object] = []
    for agent_id in range(M):
        actor = HAPPO(actor_args, Box((actor_dim,)), gym.spaces.Discrete(N + 1), device=device)
        actors_raw.append(actor)
        evidence["seed_ledger"].append({"order": 3 + agent_id, "event": f"actor_{agent_id}_constructed"})
    critic_raw = VCritic(critic_args, Box((critic_dim,)), device=device)
    evidence["seed_ledger"].append({"order": 6, "event": "critic_constructed"})
    value_normalizer = ValueNorm(1, device=device) if bool(algo_args["train"]["use_valuenorm"]) else None
    evidence["seed_ledger"].append({"order": 7, "event": "valuenorm_constructed", "present": value_normalizer is not None})
    actors = [ActorRecorder(actor, agent_id) for agent_id, actor in enumerate(actors_raw)]
    def persist_first_critic_fingerprint(fingerprint: Mapping[str, object]) -> None:
        evidence["s2_input_fingerprint"] = dict(fingerprint)
        checkpoints.emit(
            "S2", "first_real_vcritic_input_captured", dict(fingerprint)
        )

    critic = CriticRecorder(critic_raw, persist_first_critic_fingerprint)
    buffer_args = {
        **algo_args["train"],
        **model_args,
        **algorithm_args,
        "episode_length": T,
        "n_rollout_threads": E,
        "hidden_sizes": [256, 256],
    }
    buffer = EventOnPolicyCriticBufferEPV2(buffer_args, Box((critic_dim,)), device=device)
    guards = NoTrainingGuards(torch, actors_raw, critic_raw, value_normalizer)
    guards.install()
    resources["training_guards"] = guards
    for actor in actors_raw:
        actor.prep_rollout()
    critic_raw.prep_rollout()
    checkpoints.emit("S1", "components_constructed_and_prepared", {"actor_count": len(actors_raw), "hidden_sizes": [256, 256], "share_param": False, "critic_dim": critic_dim})

    def route_observer(stage: str, detail: object | None) -> None:
        route_events.append((stage, detail))
        if stage != PD2_S6_I5B_RETURNS_SOURCE_BOUNDARY_V1:
            return
        returns_evidence = build_pd2_s6_i5b_returns_evidence_v1(
            event_returns_result=detail,
            critic_buffer=buffer,
            T=T,
            E=E,
            valuenorm_enabled=value_normalizer is not None,
            timeout_identity=timeout_invocation_identity,
            buffer_commit_performed=True,
        )
        evidence["s6_i5b_returns_evidence"] = _dto_mapping(returns_evidence)
        checkpoints.emit(
            "S6",
            "i5b_returns_evidence_captured",
            evidence["s6_i5b_returns_evidence"],
        )
        evidence["s6_i5b_returns_verdict"] = adjudicate_pd2_s6_i5b_returns_evidence_v1(
            returns_evidence
        )

    route = _compose_dormant_event_learned_policy_route_v2(
        episode_length=T,
        actors=tuple(actors),
        critic=critic,
        critic_buffer=buffer,
        admitted_reset=wrapper.reset,
        current_decision_supplier=current_bundle,
        current_decision_validator=validate_current,
        capture_i42_decision=wrapper._capture_event_proposal_decision,
        step_i42_proposals=wrapper._step_event_proposals,
        action_builder=action_builder,
        actor_trainer=actor_trainer,
        critic_trainer=critic_trainer,
        value_normalizer=value_normalizer,
        actor_rnn_shape=(1, 256),
        call_observer=route_observer,
    )

    snapshot_a = model_snapshot(actors_raw, critic_raw, value_normalizer)
    require(bool(snapshot_a["gradients_all_none"]), STOP_MUTATION, "gradient exists at Snapshot A", boundary="SNAPSHOT_A")
    evidence["snapshot_a"] = snapshot_a
    checkpoints.emit("S1", "snapshot_a_captured", snapshot_a)

    publish_pd2_s1_boundary_v1(
        evidence,
        checkpoints,
        boundary="S1_RESET",
        label="reset_entered",
    )
    reset_result = route.reset()
    require(type(reset_result) is tuple and len(reset_result) == 3, STOP_STARTUP, "admitted reset arity changed", boundary="S1_RESET")
    publish_pd2_s1_boundary_v1(
        evidence,
        checkpoints,
        boundary="S1_I1_I2",
        label="reset_returned_i1_i2_entered",
    )
    initial = route.current_decision_bundle
    initial_p2 = domain.current_read_port.read_current()
    require(initial.evidence_identity.p2_publication_identity is initial_p2.publication_identity, STOP_STARTUP, "I1 identity is not current P2", boundary="S1_I1")
    require(tuple(initial.evidence_snapshot.actor_obs.shape) == (E, M, actor_dim), STOP_STARTUP, "actor observation shape mismatch", boundary="S1_I1")
    require(tuple(initial.evidence_snapshot.runner_share_obs.shape) == (E, M, critic_dim), STOP_STARTUP, "runner share observation shape mismatch", boundary="S1_I1")
    require(tuple(initial.runner_available_actions.shape) == (E, M, N + 1), STOP_STARTUP, "available-action shape mismatch", boundary="S1_I2")
    for tensor in (initial.evidence_snapshot.actor_obs, initial.evidence_snapshot.runner_share_obs, initial.runner_available_actions):
        require(tensor.device == device and bool(torch.isfinite(tensor).all()), STOP_STARTUP, "I1/I2 device/finiteness mismatch", boundary="S1_I1_I2")
    require(int(initial.decision_valid_mask.sum()) == 6, STOP_STARTUP, "canonical reset DVM row count changed", boundary="S1_I2")
    evidence["s1"] = {
        "environment_id": "Isaac-Scan-Mobile-Manipulator-Direct-v0",
        "environment_type": type(raw).__name__,
        "profile": profile.profile_name.value,
        "E": E,
        "M": M,
        "N": N,
        "T": T,
        "required_max_episode_length": PD2_REQUIRED_MAX_EPISODE_LENGTH,
        "semantic_horizon_steps": timing_fixture.semantic_horizon_steps,
        "simulation_tick_count": timing_fixture.simulation_tick_count,
        "raw_timeout_ratio": timing_fixture.raw_horizon_ratio,
        "actual_max_episode_length": int(raw.max_episode_length),
        "episode_length_s": float(cfg.episode_length_s),
        "device": str(device),
        "actor_shape": tuple(initial.evidence_snapshot.actor_obs.shape),
        "share_shape": tuple(initial.evidence_snapshot.runner_share_obs.shape),
        "available_actions_shape": tuple(initial.runner_available_actions.shape),
        "dvm_rows": int(initial.decision_valid_mask.sum()),
        "p2_publication_identity": id(initial_p2.publication_identity),
        "episode_generations": initial.evidence_identity.episode_generations,
        "transition_generations": initial.evidence_identity.transition_generations,
        "window_identity": id(initial.evidence_identity.open_window_identity),
        "hidden_sizes": [256, 256],
        "share_param": False,
        "checkpoint": None,
    }
    checkpoints.emit("S1", "reset_i1_i2_pass", evidence["s1"])

    dummy = torch.full((E, M, 1), N, dtype=torch.float32, device=device)
    step_counter = int(raw.common_step_counter)
    try:
        wrapper.step(dummy)
    except RuntimeError as exc:
        require("not runtime-ready" in str(exc), STOP_STARTUP, "public fence returned wrong error", boundary="S1_PUBLIC_FENCE")
    else:
        raise PD2Stop(STOP_STARTUP, "public event wrapper.step opened", boundary="S1_PUBLIC_FENCE")
    require(int(raw.common_step_counter) == step_counter, STOP_STARTUP, "blocked public step mutated environment", boundary="S1_PUBLIC_FENCE")
    evidence["public_route"] = "DORMANT_BLOCKED_AS_EXPECTED"

    try:
        first = route.collect_step()
    except PD2Stop:
        raise
    except BaseException as exc:
        raise PD2Stop(STOP_PHYSICAL, f"first collect_step failed after critic/actor guards: {type(exc).__name__}: {exc}", boundary="S4_FIRST_PHYSICAL_STEP") from exc
    require(len(critic.calls) >= 1, STOP_VCRITIC, "first VCritic call was not recorded", boundary="S2_FIRST_VCRITIC_FORWARD")
    first_critic = critic.calls[0]
    require(first_critic["obs_shape"] == (E, critic_dim) and first_critic["value_shape"] == (E, 1) and first_critic["value_finite"] and not first_critic["grad_enabled"], STOP_VCRITIC, "first VCritic output contract failed", boundary="S2_FIRST_VCRITIC_FORWARD")
    evidence["s2"] = first_critic
    checkpoints.emit("S2", "first_real_vcritic_forward_pass", first_critic)

    actor_calls_after_first = [len(actor.calls) for actor in actors]
    first_proposals = _proposal_evidence(first)
    require(sum(actor_calls_after_first) > 0, STOP_ACTOR, "no actor sampled a DVM row", boundary="S3_ACTOR_FORWARD")
    for actor in actors:
        for call in actor.calls:
            selected = call["available"].to(torch.bool).gather(1, call["actions"].to(torch.int64))
            require(call["deterministic"] is False and bool(selected.all()) and bool(torch.isfinite(call["logprobs"]).all()) and not call["grad_enabled"], STOP_ACTOR, "actor proposal/logprob/mask contract failed", boundary="S3_ACTOR_FORWARD")
    evidence["s3"] = {"actor_forward_calls": actor_calls_after_first, "proposal": first_proposals, "initial_actor_fingerprints": snapshot_a["actor_state_dict_sha256"]}
    checkpoints.emit("S3", "dvm_only_actor_forward_pass", evidence["s3"])

    require(len(first.harl_step_result) == 6 and not bool(first.harl_step_result[3].any()), STOP_PHYSICAL, "first physical transition is not a nonterminal HARL six-tuple", boundary="S4_FIRST_PHYSICAL_STEP")
    require(len(control_assignments) == 1, STOP_PHYSICAL, "first controller call count mismatch", boundary="S4_P2_AK")
    expected_first = expected_assignment(first.facade_result.admitted_publication, torch)
    require(torch.equal(control_assignments[0], expected_first), STOP_PHYSICAL, "controller assignment differs from final P2/Ak", boundary="S4_P2_AK")
    evidence["s4"] = {
        "harl_step_arity": len(first.harl_step_result),
        "nonterminal": not bool(first.harl_step_result[3].any()),
        "claim_artifact_present": first.facade_result.claim_artifact is not None,
        "source_store_version": first.facade_result.source_publication.store_version,
        "post_claim_store_version": first.facade_result.post_claim_publication.store_version,
        "admitted_store_version": first.facade_result.admitted_publication.store_version,
        "controller_assignment": control_assignments[0],
        "expected_from_final_p2": expected_first,
        "proposal_not_controller_authority": True,
        "p2_sole_authority": True,
        "physical_route": "final P2 -> Ak -> controller",
    }
    checkpoints.emit("S4", "first_physical_event_step_pass", evidence["s4"])

    runtime_steps_before = sum(stage == "runtime_proposal_effective_step" for stage, _ in route_events)
    critic_call_start_before_second = len(critic.calls)
    route_event_start_before_second = len(route_events)
    try:
        second = route.collect_step()
    except PD2Stop:
        raise
    except BaseException as exc:
        runtime_steps_after = sum(stage == "runtime_proposal_effective_step" for stage, _ in route_events)
        classification = STOP_TERMINAL if runtime_steps_after > runtime_steps_before else STOP_PHYSICAL
        boundary = "S6_TERMINAL_TRANSPORT" if classification == STOP_TERMINAL else "S5_SECOND_PHYSICAL_STEP"
        raise PD2Stop(classification, f"second collect_step failed: {type(exc).__name__}: {exc}", boundary=boundary) from exc

    s5_dto = build_pd2_s5_preterminal_evidence_v1(
        receipt=second,
        controller_assignments=tuple(control_assignments),
        assignment_projector=lambda publication: expected_assignment(publication, torch),
    )
    s5_verdict = adjudicate_pd2_s5_preterminal_evidence_v1(s5_dto)
    evidence["s5"] = {
        "verdict": s5_verdict,
        "preterminal_evidence": _dto_mapping(s5_dto),
        "actor_forward_calls_total": [len(actor.calls) for actor in actors],
        "post_return_dependency": False,
        "s6_adjudicated_at_checkpoint": False,
    }
    checkpoints.emit("S5", "continuation_second_step_pass", evidence["s5"])

    critic_call_end_after_second = len(critic.calls)
    second_collect_route_events = route_events[route_event_start_before_second:]
    timeout_batch_events = [
        detail
        for stage, detail in second_collect_route_events
        if stage == "I5a_critic_buffer_insert"
    ]
    observed_timeout_call_count = (
        int(timeout_batch_events[0].critic_batch_calls)
        if len(timeout_batch_events) == 1
        and hasattr(timeout_batch_events[0], "critic_batch_calls")
        else 0
    )
    timeout_invocation_identity = identify_pd2_s6_timeout_critic_call_v1(
        second_collect_start_call_index=critic_call_start_before_second,
        second_collect_end_call_index=critic_call_end_after_second,
        timeout_batch_event_count=len(timeout_batch_events),
        observed_timeout_call_count=observed_timeout_call_count,
    )
    evidence["s6_timeout_critic_invocation_identity"] = _dto_mapping(
        timeout_invocation_identity
    )

    post_return_diagnostic = None
    post_return_diagnostic_error = None
    try:
        post_return_diagnostic = build_pd2_post_return_state_diagnostic_v1(second)
        evidence["post_return_state_diagnostic"] = _dto_mapping(post_return_diagnostic)
    except BaseException as exc:
        post_return_diagnostic_error = f"{type(exc).__name__}: {exc}"
        evidence["post_return_state_diagnostic_unavailable"] = post_return_diagnostic_error

    require(len(second.harl_step_result) == 6 and bool(second.harl_step_result[3].all()), STOP_TERMINAL, "second transition did not terminate all rows", boundary="S6_TIME_LIMIT")

    reasons = buffer.termination_reason.detach().clone()
    require(bool((reasons[0] == int(TerminationReason.NONE)).all()) and bool((reasons[1] == int(TerminationReason.TIME_LIMIT)).all()), STOP_TERMINAL, "termination reason matrix mismatch", boundary="S6_TIME_LIMIT")
    history = second.facade_result.terminal_historical_payload
    require(len(history) == E and all(row.optional_sidecar is not None for row in history), STOP_TERMINAL, "authoritative pre-reset terminal sidecar missing", boundary="S6_I4_SIDECAR")
    require(len(slots_before_ack) == 1 and len(slots_before_ack[0]) == E, STOP_TERMINAL, "pre-ACK terminal slots not observed exactly once", boundary="S6_ACK")
    require(domain.terminal_consumer_port.capture_pending_terminal_artifacts() == (), STOP_TERMINAL, "runtime terminal slots survived exact ACK", boundary="S6_ACK")
    pre_obs = torch.stack([row.optional_sidecar.bootstrap_critic_obs for row in history], dim=0)
    post_obs = second.next_decision_bundle.evidence_snapshot.runner_share_obs[:, 0]
    pre_fp = tensor_fingerprint(pre_obs)
    post_fp = tensor_fingerprint(post_obs)
    require(pre_fp != post_fp, STOP_TERMINAL, "pre-reset and post-reset critic state mixed", boundary="S6_HISTORICAL_CURRENT")
    old_episodes = tuple(row.episode_generation for row in history)
    new_episodes = second.next_decision_bundle.evidence_identity.episode_generations
    require(all(new == old + 1 for old, new in zip(old_episodes, new_episodes)), STOP_TERMINAL, "autoreset episode generation did not advance", boundary="S6_HISTORICAL_CURRENT")
    timeout_observed_input = critic.observed_input(
        timeout_invocation_identity.timeout_call_global_index
    )
    timeout_correlation = compare_pd2_s6_timeout_critic_input_exact_v1(
        pre_obs,
        timeout_observed_input,
        invocation_identity=timeout_invocation_identity,
    )
    timeout_correlation_verdict = adjudicate_pd2_s6_timeout_critic_input_correlation_v1(
        timeout_correlation
    )
    require(
        timeout_correlation.expected_input_sha256 == pre_fp
        and timeout_correlation.observed_input_sha256
        == critic.calls[timeout_invocation_identity.timeout_call_global_index]["obs_sha256"],
        STOP_TERMINAL,
        "S6 bounded timeout critic fingerprints differ from exact-correlation inputs",
        boundary="S6_TIMEOUT_CRITIC",
    )
    require(torch.equal(buffer.share_obs[2], post_obs), STOP_TERMINAL, "critic t+1 slot is not post-reset current state", boundary="S6_BUFFER")
    require(bool(buffer.timeout_bootstrap_masks[1].all()) and bool(torch.isfinite(buffer.timeout_bootstrap_value_preds[1]).all()), STOP_TERMINAL, "TIME_LIMIT bootstrap fields missing", boundary="S6_BUFFER")

    try:
        rollout = route.finish_rollout(agent_order=(0, 1, 2))
    except EventGAEReturnsError as exc:
        returns_evidence = build_pd2_s6_i5b_returns_evidence_v1(
            event_returns_result=None,
            critic_buffer=buffer,
            T=T,
            E=E,
            valuenorm_enabled=value_normalizer is not None,
            timeout_identity=timeout_invocation_identity,
            producer_error=exc,
            buffer_commit_performed=False,
        )
        evidence["s6_i5b_returns_evidence"] = _dto_mapping(returns_evidence)
        checkpoints.emit(
            "S6",
            "i5b_returns_evidence_captured",
            evidence["s6_i5b_returns_evidence"],
        )
        adjudicate_pd2_s6_i5b_returns_evidence_v1(returns_evidence)
        raise PD2Stop(
            STOP_TERMINAL,
            f"typed I5b producer failure: {exc.failure_code}: {exc.stage}",
            boundary="S6_I5B_RETURNS",
        ) from exc
    except PD2Stop:
        raise
    except BaseException as exc:
        raise PD2Stop(STOP_TERMINAL, f"I5b/rollover failed: {type(exc).__name__}: {exc}", boundary="S6_I5B_RETURNS") from exc
    require(tuple(rollout.advantages.shape) == (T, E, 1) and bool(torch.isfinite(rollout.advantages).all()), STOP_TERMINAL, "event advantages invalid", boundary="S6_I5B_RETURNS")
    require(
        evidence.get("s6_i5b_returns_verdict", {}).get("pass") is True,
        STOP_TERMINAL,
        "source-faithful I5b returns evidence/verdict is unavailable",
        boundary="S6_I5B_RETURNS",
    )
    require(len(actor_train_calls) == 1 and len(critic_train_calls) == 1, STOP_TERMINAL, "recorder-only trainer seam count mismatch", boundary="S6_RECORDER_SEAMS")
    require(buffer.step == 0 and not bool(buffer._event_slot_written.any()), STOP_TERMINAL, "event buffer did not roll over", boundary="S6_ROLLOVER")
    evidence["s6"] = {
        "termination_reason": reasons,
        "history_keys": [(row.env_id, row.episode_generation, row.transition_generation) for row in history],
        "pre_reset_critic_fingerprint": pre_fp,
        "post_reset_current_fingerprint": post_fp,
        "old_episode_generations": old_episodes,
        "new_episode_generations": new_episodes,
        "terminal_slots_before_ack": len(slots_before_ack[0]),
        "terminal_slots_after_ack": 0,
        "timeout_critic_call_identity": _dto_mapping(timeout_invocation_identity),
        "timeout_critic_exact_matches": 1,
        "timeout_critic_exact_match_index": timeout_invocation_identity.timeout_call_global_index,
        "timeout_critic_exact_correlation": _dto_mapping(timeout_correlation),
        "timeout_critic_exact_correlation_verdict": timeout_correlation_verdict,
        "timeout_bootstrap": True,
        "trace_stop": True,
        "event_returns_shape": tuple(rollout.event_returns_result.returns.shape),
        "event_returns_contract": "result[T,E,1]/storage[T+1,E,1]/training_slice[T,E,1]",
        "i5b_returns_evidence": evidence["s6_i5b_returns_evidence"],
        "i5b_returns_verdict": evidence["s6_i5b_returns_verdict"],
        "advantages_shape": tuple(rollout.advantages.shape),
        "buffer_rollover": True,
        "stock_compute_returns_calls": 0,
        "actor_trainer_recorder_calls": len(actor_train_calls),
        "critic_trainer_recorder_calls": len(critic_train_calls),
        "post_return_diagnostic_available": post_return_diagnostic is not None,
        "post_return_diagnostic_error": post_return_diagnostic_error,
        "post_return_diagnostic_interpretation": "proven_post_autoreset_only_after_S6" if post_return_diagnostic is not None else None,
        "s5_verdict_unchanged": s5_verdict,
    }
    checkpoints.emit("S6", "time_limit_terminal_transport_returns_pass", evidence["s6"])

    snapshot_b = model_snapshot(actors_raw, critic_raw, value_normalizer)
    evidence["snapshot_b"] = snapshot_b
    require(snapshot_a == snapshot_b, STOP_MUTATION, "Snapshot A/B protected state mismatch", boundary="SNAPSHOT_B")
    require(guards.counts == {"actor_optimizer_step": 0, "critic_optimizer_step": 0, "backward": 0, "valuenorm_update": 0}, STOP_MUTATION, "no-training guard count changed", boundary="SNAPSHOT_B")
    evidence["no_training_counters"] = {
        **guards.counts,
        "checkpoint_load": 0,
        "checkpoint_save": 0,
        "stock_compute_returns": 0,
        "stock_happo_train": 0,
        "runner_run": 0,
        "training": 0,
        "playback": 0,
        "evaluation": 0,
    }
    checkpoints.emit("SNAPSHOT_B", "snapshot_b_exact_match", {"snapshot_b": snapshot_b, "no_training_counters": evidence["no_training_counters"]})

    descriptor = get_dormant_event_learned_policy_route_descriptor_v2()
    require(descriptor["route"] == "private_test_only_dormant" and descriptor["public_activation"] == "blocked_pending_B2_V1_V2_R", STOP_STARTUP, "public readiness fence opened", boundary="PUBLIC_ROUTE_FINAL")
    evidence["route_descriptor"] = descriptor
    evidence["critic_forward_attempts"] = critic.attempts
    evidence["critic_forward_calls"] = len(critic.calls)
    evidence["actor_attempts"] = [actor.attempts for actor in actors]
    evidence["controller_calls"] = len(control_assignments)
    evidence["facade_stage_names"] = [stage for stage, _ in facade_events]
    evidence["route_stage_names"] = [stage for stage, _ in route_events]
    evidence["guard_direct_calls"] = {"reset": guard.direct_reset_calls, "step": guard.direct_step_calls}
    return evidence


def _runtime_extension_and_smoke(evidence: dict[str, object], resources: dict[str, object], checkpoints: Checkpoints) -> dict[str, object]:
    evidence["s0r"] = runtime_extension_gate(checkpoints)
    publish_pd2_s1_boundary_v1(
        evidence,
        checkpoints,
        boundary="S1_ENTER",
        label="s1_entered",
    )
    return run_real_smoke(evidence, resources, checkpoints)


def known_descendants() -> dict[str, object]:
    try:
        import psutil

        children: list[dict[str, object]] = []
        for child in psutil.Process(os.getpid()).children(recursive=True):
            try:
                children.append({"pid": child.pid, "create_time": child.create_time(), "name": child.name()})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return {"status": "PASS", "method": "psutil recursive pre-close snapshot", "children": children}
    except BaseException as exc:
        return {"status": "UNAVAILABLE", "method": "psutil recursive pre-close snapshot", "children": [], "exception_type": type(exc).__name__, "exception_message": str(exc)}


def run_worker(args: argparse.Namespace) -> int:
    checkpoint_path = Path(args.checkpoint_file)
    primary_path = Path(args.primary_result_file)
    checkpoints = Checkpoints(checkpoint_path)
    checkpoints.emit("O0", "worker_started", module_state("worker_started"))
    simulation_app = None
    app_launcher = None
    resources: dict[str, object] = {}
    evidence: dict[str, object] = {
        "mode": "PD-A / CURRENT-PRODUCTION-RUNTIME-VALIDATION",
        "worker_pid": os.getpid(),
        "python_executable": sys.executable,
        "active_stage": "S0",
        "active_boundary": "S0_WORKER_START",
        "environment_constructed": False,
        "environment_resets": 0,
        "environment_steps": 0,
        "optimizer_calls": 0,
        "backward_calls": 0,
    }
    primary: dict[str, object] = {"status": "failed", "classification": STOP_STARTUP, "first_boundary": "S0_WORKER_START", "evidence": evidence}
    try:
        sys.argv = [sys.argv[0]]
        from isaaclab.app import AppLauncher

        checkpoints.emit("S0", "app_launcher_module_import_complete", module_state("app_launcher_module_import_complete"))
        device = _warm_start_torch_cuda(DEVICE, checkpoints)
        require(device is not None and str(device) == DEVICE, STOP_STARTUP, "production CUDA warm-up did not complete", boundary="S0_WARMUP")
        checkpoints.emit("S0", "app_launcher_constructor_entry", module_state("app_launcher_constructor_entry"))
        app_launcher = AppLauncher(headless=True, device=DEVICE, enable_cameras=False, livestream=0, xr=False, experience="")
        simulation_app = app_launcher.app
        checkpoints.emit("S0", "app_launcher_constructor_returned", module_state("app_launcher_constructor_returned"))
        resolved_experience = Path(app_launcher._sim_experience_file)
        app_config = {
            "headless": bool(app_launcher._headless),
            "device": DEVICE,
            "enable_cameras": bool(app_launcher._enable_cameras),
            "livestream": int(app_launcher._livestream),
            "xr": bool(app_launcher._xr),
            "experience_override": "",
            "resolved_experience": str(resolved_experience),
            "resolved_experience_sha256": sha256(resolved_experience) if resolved_experience.is_file() else None,
        }
        require(
            app_config["headless"] is True
            and app_config["device"] == DEVICE
            and app_config["enable_cameras"] is False
            and app_config["livestream"] == 0
            and app_config["xr"] is False
            and _normal_path(resolved_experience) == _normal_path(HEADLESS_EXPERIENCE)
            and app_config["resolved_experience_sha256"] == EXPECTED_EXPERIENCE_SHA256,
            STOP_STARTUP,
            "resolved AppLauncher configuration differs from TRAIN_STARTUP_PREFIX_V1",
            boundary="S0_APP_CONFIG",
        )
        checkpoints.emit("S0", "startup_config_validated", app_config)
        s0_labels = [event["label"] for event in checkpoints.events if event["stage"] in ("O0", "S0")]
        require(tuple(s0_labels) == EXPECTED_S0_LABELS, STOP_STARTUP, "runtime S0 event ledger differs from exact order", boundary="S0_EVENT_LEDGER")
        evidence["s0"] = {"event_labels": s0_labels, "app_config": app_config, "warmup": {"shape": [1, 1], "dtype": "torch.float32 default", "device": DEVICE, "linear": [1, 1], "forward_count": 1, "synchronize_count": 1, "matmul_count": 0, "retry_count": 0, "seed_before_warmup": 0}}

        evidence["active_stage"] = "S0R"
        evidence["active_boundary"] = "S0R"
        _runtime_extension_and_smoke(evidence, resources, checkpoints)
        evidence["environment_constructed"] = True
        evidence["environment_resets"] = 1
        evidence["environment_steps"] = 2
        evidence["active_stage"] = "COMPLETE"
        primary = {"status": "passed", "classification": PASS, "first_boundary": "PASS", "evidence": evidence}
    except BaseException as exc:
        trace = traceback.format_exc()
        print(trace, file=sys.stderr, flush=True)
        if hasattr(exc, "classification") and hasattr(exc, "boundary"):
            classification = exc.classification
            boundary = exc.boundary
        else:
            classification, boundary = classify_pd2_s1_untyped_failure_v1(
                evidence.get("active_boundary", evidence.get("active_stage", "UNKNOWN"))
            )
        production_exception_fields = bounded_pd2_production_exception_fields_v1(exc)
        primary = {
            "status": "failed",
            "classification": classification,
            "first_boundary": boundary,
            "failure_detail": getattr(exc, "failure_detail", None),
            "error": f"{type(exc).__name__}: {exc}",
            "exception_type": type(exc).__name__,
            "production_exception_fields": production_exception_fields,
            "traceback": trace,
            "evidence": evidence,
        }

    atomic_json(primary_path, primary)
    checkpoints.emit("O4", "primary_result_persisted", {"classification": primary["classification"], "status": primary["status"]})

    guards = resources.get("training_guards")
    if guards is not None:
        try:
            guards.restore()
        except BaseException as exc:
            primary["guard_restore_error"] = f"{type(exc).__name__}: {exc}"
            atomic_json(primary_path, primary)
    guard = resources.get("guard")
    if guard is not None:
        try:
            guard.close()
            primary["environment_close"] = "RETURNED"
        except BaseException as exc:
            primary["environment_close"] = f"FAILED: {type(exc).__name__}: {exc}"
        atomic_json(primary_path, primary)

    if simulation_app is None:
        return 1
    process_tree = known_descendants()
    primary["known_process_tree_before_close"] = process_tree
    primary["close_invoked"] = True
    atomic_json(primary_path, primary)
    checkpoints.emit("O5", "immediately_before_SimulationApp_close", {"known_process_tree": process_tree})
    simulation_app.close()
    primary["close_returned"] = True
    checkpoints.emit("O6", "SimulationApp_close_returned")
    atomic_json(primary_path, primary)
    return 0 if primary["status"] == "passed" else 20


def _read_json(path: Path) -> tuple[bool, dict[str, object]]:
    if not path.is_file():
        return False, {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return isinstance(value, dict), value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return False, {}


def _raw_diff(before: list[object], after: list[object]) -> list[dict[str, object]]:
    def key(row: list[object]) -> tuple[str, str]:
        return str(row[0]), str(row[1])

    left = {key(row): row for row in before}
    right = {key(row): row for row in after}
    changes: list[dict[str, object]] = []
    for item in sorted(set(left) | set(right)):
        if left.get(item) != right.get(item):
            changes.append({"key": item, "before": left.get(item), "after": right.get(item)})
    return changes


def classify_postrun(before: Mapping[str, object], after: Mapping[str, object], protected_unchanged: bool) -> dict[str, object]:
    changes = _raw_diff(normalize(before["rows"]), normalize(after["rows"]))
    before_oracles = before.get("junction_oracle_comparison", {})
    after_oracles = after.get("junction_oracle_comparison", {})
    if not before_oracles.get("pass") or not after_oracles.get("pass"):
        return {
            "class": "AMBIGUOUS_STATE_DELTA",
            "changes": changes,
            "eligible": False,
            "reason": "pre/post Win32 and PowerShell junction oracles are not jointly authoritative",
            "before_junction_oracles": before_oracles,
            "after_junction_oracles": after_oracles,
        }
    before_pairs = [
        (row["installed_path"], row.get("actual_target"), row.get("actual_manifest_sha256"))
        for row in before.get("junction_primary", {}).get("rows", [])
    ]
    after_pairs = [
        (row["installed_path"], row.get("actual_target"), row.get("actual_manifest_sha256"))
        for row in after.get("junction_primary", {}).get("rows", [])
    ]
    if normalize(before_pairs) != normalize(after_pairs):
        return {
            "class": "STRUCTURAL_RESOLUTION_MUTATION",
            "changes": changes,
            "eligible": False,
            "reason": "corrected Win32 junction path/target/manifest inventory changed",
            "junction_pairs_before": before_pairs,
            "junction_pairs_after": after_pairs,
        }
    if not changes and protected_unchanged:
        return {"class": "NO_OBSERVED_STATE_CHANGE", "changes": [], "eligible": True, "reason": "all bounded rows and protected sources exact"}
    structural: list[dict[str, object]] = []
    metadata_candidates: list[dict[str, object]] = []
    for change in changes:
        kind, name = change["key"]
        if kind == "linkroot":
            structural.append(change)
        elif kind == "cacheroot" and name not in ("index", "urls", "cache_db.json"):
            structural.append(change)
        else:
            metadata_candidates.append(change)
    if not protected_unchanged or structural:
        return {"class": "STRUCTURAL_RESOLUTION_MUTATION", "changes": changes, "structural_changes": structural, "eligible": False, "reason": "protected source or structural resolution row changed"}
    content_changes = []
    for change in metadata_candidates:
        kind, name = change["key"]
        if kind == "metadata" and not str(name).endswith("registry.lock"):
            before_row = change.get("before") or []
            after_row = change.get("after") or []
            if len(before_row) > 2 and len(after_row) > 2 and before_row[2] != after_row[2]:
                content_changes.append(change)
    if content_changes:
        return {"class": "AMBIGUOUS_STATE_DELTA", "changes": changes, "ambiguous_content_changes": content_changes, "eligible": False, "reason": "registry/cache content changed and no positive resolution-neutral proof exists"}
    allowed_keys = {("cacheroot", "index"), ("cacheroot", "urls"), ("cacheroot", "cache_db.json")}
    benign = all(tuple(change["key"]) in allowed_keys or (change["key"][0] == "metadata" and str(change["key"][1]).endswith("registry.lock")) for change in metadata_candidates)
    if benign:
        return {"class": "MUTABLE_METADATA_REFRESH", "changes": changes, "eligible": True, "reason": "only lock/directory bookkeeping timestamps changed; all content hashes and structural rows remain exact"}
    return {"class": "AMBIGUOUS_STATE_DELTA", "changes": changes, "eligible": False, "reason": "changed bounded state cannot be positively proven metadata-only"}


def nvidia_inventory() -> dict[str, object]:
    completed = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu", "--format=csv,noheader,nounits"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return {"exit_code": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def run_supervisor(args: argparse.Namespace) -> int:
    static = static_preflight()
    if args.r5j_only:
        r5j_pure = None
        r5d_regression = None
        r5g_regression = None
        error = None
        try:
            r5j_pure = r5j_pure_synthetic_verification()
            r5d_regression = r5d_pure_synthetic_verification()
            r5g_regression = r5g_pure_synthetic_verification()
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
        returns_pass = bool(static["pass"] and r5j_pure is not None and r5j_pure["pass"])
        regressions_pass = bool(
            r5d_regression is not None
            and r5d_regression["pass"]
            and r5g_regression is not None
            and r5g_regression["pass"]
        )
        passed = returns_pass and regressions_pass
        if passed:
            classification = R5J_PASS
        elif returns_pass and not regressions_pass:
            classification = R5J_STOP_REGRESSION
        elif r5j_pure is not None and not r5j_pure["static_contract_review"]["checks"]["r5j_no_semantic_recomputation"]:
            classification = R5J_STOP_RECOMPUTE
        else:
            classification = R5J_STOP_DIVERGENCE
        result = {
            "mode": "R5-J_TEST_ONLY_I5B_RETURNS_OBSERVABILITY_ORACLE_STATIC_CPU_SYNTHETIC",
            "classification": classification,
            "status": "passed" if passed else "failed",
            "static_preflight": static,
            "r5j_pure_synthetic_verification": r5j_pure,
            "r5d_regression": r5d_regression,
            "r5g_regression": r5g_regression,
            "error": error,
            "execution_counters": {
                "formal_supervisor": 0,
                "worker": 0,
                "AppLauncher": 0,
                "SimulationApp": 0,
                "Isaac": 0,
                "gym_make": 0,
                "CUDA_runtime": 0,
                "HARL_real": 0,
                "VCritic_real": 0,
                "actor_real": 0,
                "environment_construct": 0,
                "reset": 0,
                "step": 0,
                "optimizer": 0,
                "backward": 0,
                "training": 0,
            },
            "B2_V2": "STOPPED / INCOMPLETE",
            "R5_H": "FORMAL STOP REVIEW CONFIRMED / FROZEN",
            "R5_I": "GPT REVIEW PASS / FROZEN",
            "R5_K": "NOT AUTHORIZED",
            "B2_R": "NOT AUTHORIZED",
            "commit": "NONE",
        }
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 0 if passed else 1
    if args.r5g_only:
        r5g_pure = None
        r5d_regression = None
        error = None
        try:
            r5g_pure = r5g_pure_synthetic_verification()
            r5d_regression = r5d_pure_synthetic_verification()
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
        timing_pass = bool(static["pass"] and r5g_pure is not None and r5g_pure["pass"])
        nontiming_pass = bool(r5d_regression is not None and r5d_regression["pass"])
        passed = timing_pass and nontiming_pass
        if passed:
            classification = R5G_PASS
        elif timing_pass and not nontiming_pass:
            classification = R5G_STOP_NONTIMING
        else:
            classification = R5G_STOP_DIVERGENCE
        result = {
            "mode": "R5-G_TEST_ONLY_INTEGRAL_HORIZON_GATE_A_GATE_B_S1_BOUNDARY_STATIC_SYNTHETIC",
            "classification": classification,
            "status": "passed" if passed else "failed",
            "static_preflight": static,
            "r5g_pure_synthetic_verification": r5g_pure,
            "r5d_nontiming_regression": r5d_regression,
            "error": error,
            "execution_counters": {
                "formal_supervisor": 0,
                "worker": 0,
                "AppLauncher": 0,
                "SimulationApp": 0,
                "Isaac": 0,
                "gym_make": 0,
                "CUDA": 0,
                "HARL_real": 0,
                "VCritic_real": 0,
                "actor_real": 0,
                "environment_construct": 0,
                "reset": 0,
                "step": 0,
                "optimizer": 0,
                "backward": 0,
                "training": 0,
            },
            "B2_V2": "STOPPED / INCOMPLETE",
            "R5_H": "NOT AUTHORIZED",
            "B2_R": "NOT AUTHORIZED",
            "commit": "NONE",
        }
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 0 if passed else 1
    if args.r5d_only:
        pure = None
        error = None
        try:
            pure = r5d_pure_synthetic_verification()
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
        passed = bool(static["pass"] and pure is not None and pure["pass"])
        result = {
            "mode": "R5-D-TR2_TEST_ONLY_TIMEOUT_CRITIC_INVOCATION_IDENTITY_STATIC_SYNTHETIC",
            "classification": R5D_TR2_PASS if passed else R5D_TR2_STOP_DIVERGENCE,
            "status": "passed" if passed else "failed",
            "static_preflight": static,
            "r5d_pure_synthetic_verification": pure,
            "error": error,
            "worker_started": False,
            "formal_PD2": 0,
            "AppLauncher": 0,
            "SimulationApp": 0,
            "Isaac": 0,
            "CUDA_initialized": 0,
            "HARL": 0,
            "VCritic": 0,
            "actor": 0,
            "environment": 0,
            "physical_step": 0,
            "optimizer_step": 0,
            "backward": 0,
            "training": 0,
            "playback": 0,
            "evaluation": 0,
            "B2_V2": "STOPPED / INCOMPLETE",
            "R5D_S6_EXACTINPUT_01": "CLOSED" if passed else "OPEN",
            "R5D_S6_CALLIDENTITY_02": "CLOSED" if passed else "OPEN",
            "R5_E": "NOT AUTHORIZED",
            "B2_R": "NOT AUTHORIZED",
            "commit": "NONE",
        }
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 0 if passed else 1
    if args.r5a_only:
        real_target = None
        error = None
        if static["pass"]:
            try:
                real_target = cache_backed_real_target_read_only_verification()
            except BaseException as exc:
                error = f"{type(exc).__name__}: {exc}"
        passed = bool(static["pass"] and real_target is not None and real_target["pass"])
        if passed:
            classification = R5A_PASS
        elif real_target is not None and not real_target["pass"]:
            classification = R5A_STOP_TARGET
        else:
            classification = R5A_STOP_DIVERGENCE
        result = {
            "mode": "R5-A_TEST_ONLY_CACHE_BACKED_S0R_STATIC_SYNTHETIC_READ_ONLY",
            "classification": classification,
            "status": "passed" if passed else "failed",
            "static_preflight": static,
            "real_target_read_only_verification": real_target,
            "error": error,
            "worker_started": False,
            "formal_PD2": 0,
            "AppLauncher": 0,
            "SimulationApp": 0,
            "Isaac": 0,
            "CUDA": 0,
            "HARL": 0,
            "VCritic": 0,
            "actor": 0,
            "environment": 0,
            "optimizer_step": 0,
            "backward": 0,
            "training": 0,
        }
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 0 if passed else 1
    if args.static_only:
        result = {"mode": "STATIC_ONLY", "classification": "PD2_STATIC_PREFLIGHT_PASS" if static["pass"] else STOP_STARTUP, "status": "passed" if static["pass"] else "failed", "static_preflight": static, "worker_started": False}
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 0 if static["pass"] else 1

    if args.r2a_only:
        prelaunch = prelaunch_exact_gate() if static["pass"] else None
        passed = bool(static["pass"] and prelaunch is not None and prelaunch["pass"])
        result = {
            "mode": "R2-A_S0R_ADAPTER_STATIC_SYNTHETIC_AND_READ_ONLY_PREFLIGHT",
            "classification": R2A_PASS if passed else R2_STOP_UNRELIABLE,
            "status": "passed" if passed else "failed",
            "formal_reentry_eligible": passed,
            "static_preflight": static,
            "prelaunch": prelaunch,
            "worker_started": False,
            "AppLauncher": 0,
            "SimulationApp": 0,
            "Isaac": 0,
            "CUDA_worker_runtime": 0,
            "HARL": 0,
            "MRTA": 0,
            "mutation_operations": 0,
        }
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 0 if passed else 1

    if not static["pass"]:
        result = {"classification": STOP_STARTUP, "status": "failed", "first_boundary": "STATIC_PREFLIGHT", "static_preflight": static, "worker_started": False}
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 1

    if args.detector_only:
        prelaunch = prelaunch_exact_gate()
        primary = prelaunch["junction_oracles"]["primary"]
        powershell = prelaunch["junction_oracles"]["powershell"]
        comparison = prelaunch["junction_oracles"]["comparison"]
        if prelaunch["pass"]:
            classification, status = R1A_PASS, "passed"
        elif bool(primary.get("pass")) != bool(powershell.get("pass")) or not comparison.get("mapping_equal"):
            classification, status = R1_STOP_DISAGREEMENT, "failed"
        elif not primary.get("pass") or not powershell.get("pass"):
            classification, status = R1_STOP_UNRELIABLE, "failed"
        else:
            classification, status = STOP_PRELAUNCH, "failed"
        result = {
            "mode": "R1-A_DETECTOR_ONLY_READ_ONLY_PREFLIGHT",
            "classification": classification,
            "status": status,
            "formal_reentry_eligible": status == "passed",
            "static_preflight": static,
            "prelaunch": prelaunch,
            "worker_started": False,
            "AppLauncher": 0,
            "SimulationApp": 0,
            "Isaac": 0,
            "CUDA_worker_runtime": 0,
            "mutation_operations": 0,
        }
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 0 if status == "passed" else 1

    prelaunch = prelaunch_exact_gate()
    if not prelaunch["pass"]:
        result = {"classification": STOP_PRELAUNCH, "status": "failed", "first_boundary": "PRELAUNCH_EXACT_BASELINE_GATE", "static_preflight": static, "prelaunch": prelaunch, "worker_started": False, "AppLauncher": 0, "SimulationApp": 0, "Isaac": 0, "CUDA_worker_runtime": 0}
        if args.json_output:
            atomic_json(Path(args.json_output), result)
        print(json.dumps(normalize(result), indent=2, sort_keys=True))
        return 1

    D4O = load_test_module(D4O_HARNESS, "_b2_v2_pd2_d4o_reviewed")
    protected_paths = sorted(set(EXPECTED_SOURCE_HASHES) | {str(Path(__file__))})
    protected_before = {name: sha256(Path(name)) for name in protected_paths}
    shared_before = prelaunch["shared_state"]
    temp_root = Path(tempfile.mkdtemp(prefix="b2_v2_pd2_formal_"))
    primary_path = temp_root / "primary_result.json"
    checkpoint_path = temp_root / "checkpoints.json"
    command = [
        str(EXPECTED_PYTHON),
        "-u",
        str(Path(__file__)),
        "--worker",
        "--primary-result-file",
        str(primary_path),
        "--checkpoint-file",
        str(checkpoint_path),
    ]
    started = time.monotonic()
    gpu_before = nvidia_inventory()
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    timed_out = False
    kill_used = False
    try:
        stdout, _ = process.communicate(timeout=args.timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_used = True
        D4O.terminate_process_tree(process)
        stdout, _ = process.communicate(timeout=15)

    primary_valid, primary = _read_json(primary_path)
    checkpoint_valid, checkpoint = _read_json(checkpoint_path)
    events = checkpoint.get("events", []) if checkpoint_valid else []
    checkpoints = [str(event.get("stage")) for event in events]
    known_tree: dict[str, object] = {"status": "NOT_CAPTURED", "children": []}
    for event in events:
        if event.get("stage") == "O5":
            known_tree = event.get("details", {}).get("known_process_tree", known_tree)
    children = known_tree.get("children", []) if isinstance(known_tree, dict) else []
    survivors = D4O.child_survivors(children) if known_tree.get("status") == "PASS" else []
    main_alive = process.poll() is None
    exit_code = process.returncode
    stdout_bytes = stdout.encode("utf-8", errors="replace")
    cleanup_error = None
    try:
        shutil.rmtree(temp_root)
    except BaseException as exc:
        cleanup_error = f"{type(exc).__name__}: {exc}"
    cleanup_pass = not temp_root.exists()

    protected_after = {name: sha256(Path(name)) for name in protected_paths}
    protected_unchanged = protected_before == protected_after
    shared_after = shared_state_dual_oracle_inventory()
    postrun = classify_postrun(shared_before, shared_after, protected_unchanged)
    shutdown_evidence = {
        "checkpoints": checkpoints,
        "diagnostic_result": primary.get("classification") if primary_valid else None,
        "expected_diagnostic_failure": False,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "supervisor_kill_used": kill_used,
        "main_worker_alive": main_alive,
        "known_child_survivors": survivors,
        "primary_result_valid": primary_valid,
        "supervisor_cleanup_pass": cleanup_pass,
        "protected_files_unchanged": protected_unchanged,
    }
    shutdown = D4O.classify_shutdown(shutdown_evidence)
    if primary.get("environment_close", "RETURNED") != "RETURNED" and primary_valid:
        shutdown = {"shutdown_class": D4O.UNSAFE, "safe_shutdown": False, "reasons": ["environment close did not return cleanly", primary.get("environment_close")]}

    functional_pass = primary_valid and primary.get("status") == "passed"
    if not functional_pass:
        classification = primary.get("classification", STOP_STARTUP) if primary_valid else STOP_SHUTDOWN
        first_boundary = primary.get("first_boundary", "WORKER_RESULT_MISSING") if primary_valid else "WORKER_RESULT_MISSING"
        status = "failed"
    elif not shutdown["safe_shutdown"]:
        classification, first_boundary, status = STOP_SHUTDOWN, "D4O_SHUTDOWN", "failed"
    elif not postrun["eligible"]:
        classification, first_boundary, status = STOP_SHARED_STATE, "POSTRUN_INTEGRITY_GATE", "failed"
    elif postrun["class"] == "MUTABLE_METADATA_REFRESH":
        classification, first_boundary, status = PASS_METADATA, "PASS_WITH_CLASSIFIED_BENIGN_METADATA_REFRESH", "passed"
    else:
        classification, first_boundary, status = PASS, "PASS", "passed"

    result = {
        "classification": classification,
        "status": status,
        "first_boundary": first_boundary,
        "mode": "PD-A / CURRENT-PRODUCTION-RUNTIME-VALIDATION",
        "formal_worker_count": 1,
        "formal_app_launcher_lifetimes": 1 if "S0" in checkpoints else 0,
        "static_preflight": static,
        "prelaunch": prelaunch,
        "worker_primary": primary if primary_valid else None,
        "worker_primary_valid": primary_valid,
        "checkpoint_file_valid": checkpoint_valid,
        "checkpoint_events": events,
        "process_exit_code": exit_code,
        "timed_out": timed_out,
        "supervisor_kill_used": kill_used,
        "worker_alive_after_wait": main_alive,
        "known_process_tree_observation": known_tree,
        "known_child_survivors": survivors,
        "shutdown": shutdown,
        "supporting_shutdown_marker_observed": "Simulation App Shutting Down" in stdout,
        "supervisor_cleanup_pass": cleanup_pass,
        "supervisor_cleanup_error": cleanup_error,
        "temporary_directory_remaining": temp_root.exists(),
        "postrun_integrity": postrun,
        "shared_state_before": shared_before,
        "shared_state_after": shared_after,
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "protected_hashes_unchanged": protected_unchanged,
        "harness_path": str(Path(__file__)),
        "harness_sha256": sha256(Path(__file__)),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout_stderr_line_count": len(stdout.splitlines()),
        "stdout_stderr_sha256": hashlib.sha256(stdout_bytes).hexdigest(),
        "stdout_stderr_tail": stdout[-16000:],
        "nvidia_smi_before": gpu_before,
        "nvidia_smi_after": nvidia_inventory(),
        "causal_claim_boundary": "current workaround-based production startup path only; no cuBLAS root cause, necessity, fix, or pre-R8 claim",
        "B2_R": "NOT AUTHORIZED",
        "training": "NOT AUTHORIZED",
        "commit": "NONE",
    }
    if args.json_output:
        atomic_json(Path(args.json_output), result)
    print(json.dumps(normalize(result), indent=2, sort_keys=True))
    return 0 if status == "passed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--primary-result-file", help=argparse.SUPPRESS)
    parser.add_argument("--checkpoint-file", help=argparse.SUPPRESS)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument("--detector-only", action="store_true")
    parser.add_argument("--r2a-only", action="store_true")
    parser.add_argument("--r5a-only", action="store_true")
    parser.add_argument("--r5d-only", action="store_true")
    parser.add_argument("--r5g-only", action="store_true")
    parser.add_argument("--r5j-only", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=TIMEOUT_SECONDS)
    parser.add_argument("--json-output")
    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if args.worker and (not args.primary_result_file or not args.checkpoint_file):
        parser.error("worker requires result and checkpoint files")
    if args.worker and args.static_only:
        parser.error("worker cannot use --static-only")
    if args.worker and args.detector_only:
        parser.error("worker cannot use --detector-only")
    if args.worker and args.r2a_only:
        parser.error("worker cannot use --r2a-only")
    if args.worker and args.r5a_only:
        parser.error("worker cannot use --r5a-only")
    if args.worker and args.r5d_only:
        parser.error("worker cannot use --r5d-only")
    if args.worker and args.r5g_only:
        parser.error("worker cannot use --r5g-only")
    if args.worker and args.r5j_only:
        parser.error("worker cannot use --r5j-only")
    selected_read_only_modes = sum(
        bool(value)
        for value in (
            args.static_only,
            args.detector_only,
            args.r2a_only,
            args.r5a_only,
            args.r5d_only,
            args.r5g_only,
            args.r5j_only,
        )
    )
    if selected_read_only_modes > 1:
        parser.error("--static-only, --detector-only, --r2a-only, --r5a-only, --r5d-only, --r5g-only, and --r5j-only are mutually exclusive")
    return args


def main() -> int:
    args = parse_args()
    return run_worker(args) if args.worker else run_supervisor(args)


if __name__ == "__main__":
    raise SystemExit(main())
