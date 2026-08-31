"""Pure regressions for B2-I0 versioned no-clock contract reconciliation."""

from __future__ import annotations

import argparse
import contextlib
from dataclasses import FrozenInstanceError, fields
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import MappingProxyType, ModuleType
from typing import Callable, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
PROFILE_KEY = f"{PACKAGE}.assignment_profile_contract"
V2_KEY = f"{PACKAGE}.assignment_event_profile_schema_contract_v2"
PROFILE_PATH = SCAN_SOURCE / "assignment_profile_contract.py"
V2_PATH = SCAN_SOURCE / "assignment_event_profile_schema_contract_v2.py"

PROTECTED_HASHES = {
    "assignment_event_profile_schema_contract.py": "04eb153f296196e8a098f071fdea3721e27893564b4fa2df81ff91fc088859ef",
    "assignment_mrta_contract.py": "73881d20903873ddaaf7b6b6636d008771c030f739d3d2cc8ebb32b79bd1e17c",
    "assignment_profile_contract.py": "ece4a58c1636ea3f710775eaac25e12df4097972ef57ec0d15cefec5e6702500",
    "assignment_harl_wrapper.py": "f238536c8a4bed53da984e4f2d81150f7b634915e49b601d86eb407fae9fa2ae",
    "assignment_harl_training.py": "b6f32510ae663b3e443891cdd09219dd9a5c9ceb9de9c720c73192c7488597fd",
    "assignment_event_runtime_facade.py": "036082d8df61514aa3f3c424ae6559fa678536097b66bfd5bd6f632ca3479478",
    "assignment_event_proposal_adapter.py": "874b4c7b71e6c42f9e6dabeefa25a708d25d8518e3366fe91b86b9b1a739bedd",
    "assignment_initial_claim_runtime.py": "c74868c84a803108c424827afe9326393428938dce4f6cbd46693da3d4d94fda",
    "assignment_lifecycle_transaction_runtime.py": "2033be70f91a14678ed718a3a0d3d8c26a26a5c5a05b8c6e9ae5dacb3cbfd3de",
    "scan_mobile_manipulator_env.py": "f96f6b6e9a530cd0b438344a11dc67670559206f3521d641d776d4bd475c6363",
}

FORBIDDEN_CLOCK_TERMS = (
    "assignment_tick_generation",
    "decision_tick",
    "window_tick",
    "assignment_window_generation",
    "decision_generation",
    "policy_tick",
    "claim_tick",
    "policy_step_generation",
)
IDENTITY_FIELDS = {
    "p2_publication_identity",
    "episode_generations",
    "transition_generations",
    "open_window_identity",
}


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _install_namespace_packages() -> None:
    package_paths = (
        ("isaaclab_tasks", REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"),
        ("isaaclab_tasks.direct", REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct"),
        (PACKAGE, SCAN_SOURCE),
    )
    for name, path in package_paths:
        if name not in sys.modules:
            module = ModuleType(name)
            module.__package__ = name
            module.__path__ = [str(path)]
            sys.modules[name] = module


def _load(key: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(key, path)
    _assert(spec is not None and spec.loader is not None, f"loader missing: {key}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


_install_namespace_packages()
PROFILE = _load(PROFILE_KEY, PROFILE_PATH)
V2 = _load(V2_KEY, V2_PATH)


def _scale(*, M: int = 3, N: int = 12) -> Mapping[str, object]:
    return V2.build_event_policy_scale_contract_v2(
        M=M,
        N=N,
        ordered_agent_names=tuple(f"robot_{index}" for index in range(M)),
        ordered_task_ids=tuple(range(N)),
        scene_env_spacing=12.0,
        sim_dt_seconds=0.01,
        control_decimation=4,
        episode_time_limit_seconds=40.0,
    )


def _descriptor(*, M: int = 3, N: int = 12) -> Mapping[str, object]:
    return V2.build_assignment_event_profile_schema_v2_descriptor(
        scale_contract=_scale(M=M, N=N)
    )


def _captured() -> tuple[object, object, object]:
    publication = object()
    window = object()
    identity = V2.capture_event_policy_evidence_identity_v2(
        p2_publication_identity=publication,
        episode_generations=(4, 5),
        transition_generations=(12, 2),
        open_window_identity=window,
        M=3,
        N=12,
    )
    return identity, publication, window


def _validate(identity: object, publication: object, window: object, **overrides: object) -> None:
    values = {
        "p2_publication_identity": publication,
        "episode_generations": (4, 5),
        "transition_generations": (12, 2),
        "open_window_identity": window,
        "M": 3,
        "N": 12,
    }
    values.update(overrides)
    V2.validate_event_policy_evidence_identity_v2_current(identity, **values)


def _expect_code(code: str, call: Callable[[], None]) -> None:
    try:
        call()
    except V2.AssignmentEventProfileSchemaV2ContractError as exc:
        _assert(exc.failure_code == code, f"wrong failure: {exc.failure_code}")
    else:
        raise AssertionError(f"expected failure code {code}")


def test_canonical_version_and_v1_preservation() -> None:
    _assert(V2.__name__ == V2.CANONICAL_ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_MODULE, "canonical key")
    _assert(V2.ASSIGNMENT_EVENT_PROFILE_SCHEMA_V2_CONTRACT_VERSION.endswith("_v2"), "version")
    for filename, expected in PROTECTED_HASHES.items():
        actual = hashlib.sha256((SCAN_SOURCE / filename).read_bytes()).hexdigest()
        _assert(actual == expected, f"protected source drift: {filename}")


def test_no_clock_or_hidden_replacement() -> None:
    source = V2_PATH.read_text(encoding="utf-8")
    for term in FORBIDDEN_CLOCK_TERMS:
        _assert(term not in source, f"forbidden clock term in v2 source: {term}")
    descriptor = _descriptor()
    identity_schema = descriptor["identity_schema"]
    _assert(identity_schema["clock_semantics"] == "none", "clock semantics")
    _assert(identity_schema["open_window_comparison"] == "exact opaque object identity", "OPEN semantics")
    declared = {field.name for field in fields(V2.EventPolicyEvidenceIdentityV2)}
    _assert(declared == {
        "schema_version", "profile_name", "M", "N", "episode_generations",
        "transition_generations", "_p2_publication_identity", "_open_window_identity",
    }, "identity field inventory")


def test_identity_capture_is_exact_and_immutable() -> None:
    identity, publication, window = _captured()
    _validate(identity, publication, window)
    _assert(identity.p2_publication_identity is publication, "P2 reference")
    _assert(identity.open_window_identity is window, "OPEN reference")
    _expect_code(
        "direct_identity_construction_forbidden",
        lambda: V2.EventPolicyEvidenceIdentityV2(),
    )
    try:
        identity.M = 4
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("identity mutated")
    _expect_code(
        "invalid_open_window_identity",
        lambda: V2.capture_event_policy_evidence_identity_v2(
            p2_publication_identity=publication,
            episode_generations=(4, 5),
            transition_generations=(12, 2),
            open_window_identity=7,
            M=3,
            N=12,
        ),
    )


def test_wrong_p2_fails_closed() -> None:
    identity, publication, window = _captured()
    _expect_code(
        "p2_publication_identity_mismatch",
        lambda: _validate(identity, object(), window),
    )
    _validate(identity, publication, window)


def test_wrong_episode_fails_closed_without_normalization() -> None:
    identity, publication, window = _captured()
    _expect_code(
        "episode_generation_mismatch",
        lambda: _validate(identity, publication, window, episode_generations=(4, 6)),
    )
    _expect_code(
        "invalid_episode_generations",
        lambda: _validate(identity, publication, window, episode_generations=[4, 5]),
    )


def test_wrong_transition_fails_closed() -> None:
    identity, publication, window = _captured()
    _expect_code(
        "transition_generation_mismatch",
        lambda: _validate(identity, publication, window, transition_generations=(13, 2)),
    )


def test_wrong_open_window_fails_closed_by_object_identity() -> None:
    class EqualToken:
        def __eq__(self, _other: object) -> bool:
            return True

    publication = object()
    window = EqualToken()
    recreated = EqualToken()
    identity = V2.capture_event_policy_evidence_identity_v2(
        p2_publication_identity=publication,
        episode_generations=(0,),
        transition_generations=(-1,),
        open_window_identity=window,
        M=3,
        N=12,
    )
    _expect_code(
        "open_window_identity_mismatch",
        lambda: V2.validate_event_policy_evidence_identity_v2_current(
            identity,
            p2_publication_identity=publication,
            episode_generations=(0,),
            transition_generations=(-1,),
            open_window_identity=recreated,
            M=3,
            N=12,
        ),
    )
    _assert(identity.open_window_identity is window, "failure rebound identity")


def test_model_feature_exclusion() -> None:
    descriptor = _descriptor()
    for schema_name in ("actor_schema", "critic_schema"):
        schema = descriptor[schema_name]
        names = {block["name"] for block in schema["blocks"]}
        _assert(not names.intersection(IDENTITY_FIELDS), f"identity block in {schema_name}")
        _assert(set(schema["identity_metadata_fields_excluded"]) == IDENTITY_FIELDS, "exclusion oracle")
        _assert(all(block["model_input"] is True for block in schema["blocks"]), "model flag")
    slots = descriptor["future_routing_slots"]["slots"]
    _assert(all(slot["implemented_in_b2_i0"] is False for slot in slots), "routing implemented")
    _assert(all(slot["numerical_model_feature"] is False for slot in slots), "routing in model")


def test_manifest_derived_dimensions_and_no_compatibility_slot() -> None:
    descriptor = _descriptor()
    _assert(descriptor["actor_schema"]["dimension"] == 421, "M3/N12 actor width")
    _assert(descriptor["critic_schema"]["dimension"] == 418, "M3/N12 critic width")
    _assert(V2.event_policy_actor_observation_dimension_v2(M=2, N=4) == 145, "derived actor width")
    _assert(V2.event_policy_critic_observation_dimension_v2(M=2, N=4) == 143, "derived critic width")
    compatibility = descriptor["compatibility_contract"]
    _assert(compatibility["dimension_equality_required"] is False, "v1 dimension equality")
    _assert(compatibility["reserved_compatibility_slot_present"] is False, "compatibility slot")


def test_fixed_cardinality_profile_and_default_off() -> None:
    descriptor = _descriptor()
    _assert(descriptor["actor_schema"]["fixed_cardinality"] is True, "actor fixed cardinality")
    _assert(descriptor["critic_schema"]["fixed_cardinality"] is True, "critic fixed cardinality")
    _assert(descriptor["profile_binding"]["runtime_readiness"] == "interface_only", "readiness drift")
    _assert(descriptor["profile_binding"]["readiness_change_authorized"] is False, "readiness enabled")
    registry = PROFILE.get_assignment_profile_registry()
    _assert(len(registry) == 5, "profile registry changed")
    for name in (
        PROFILE.AssignmentProfileName.LEGACY,
        PROFILE.AssignmentProfileName.LIFECYCLE_ABLATION,
        PROFILE.AssignmentProfileName.LIFECYCLE_CONTRACT_C,
        PROFILE.AssignmentProfileName.DIAGNOSTICS_HIDDEN_STATE,
    ):
        resolved = PROFILE.resolve_assignment_profile(
            name, PROFILE.AssignmentProfileResolutionOrigin.FORMAL_ENTRYPOINT
        )
        _assert(resolved.runtime_readiness.value == "existing_ready", f"default profile changed: {name}")


def test_descriptor_immutability_and_scope_barriers() -> None:
    descriptor = _descriptor()
    _assert(type(descriptor) is MappingProxyType, "root mutable")
    _assert(type(descriptor["actor_schema"]) is MappingProxyType, "schema mutable")
    try:
        descriptor["actor_schema"]["dimension"] = 1
    except TypeError:
        pass
    else:
        raise AssertionError("nested descriptor mutated")
    barriers = descriptor["scope_barriers"]
    _assert(barriers["runtime_integration"] is False, "runtime enabled")
    _assert(barriers["learner_integration"] is False, "learner enabled")
    _assert(barriers["variable_cardinality"] is False, "variable cardinality enabled")


def test_canonical_alias_import_fails_before_dependencies() -> None:
    alias = "assignment_event_profile_schema_contract_v2_alias"
    sys.modules.pop(alias, None)
    profile_present = PROFILE_KEY in sys.modules
    try:
        _load(alias, V2_PATH)
    except ImportError as exc:
        _assert("CanonicalModuleIdentityError" in str(exc), "wrong alias failure")
    else:
        raise AssertionError("alias import accepted")
    finally:
        sys.modules.pop(alias, None)
    _assert((PROFILE_KEY in sys.modules) is profile_present, "alias changed dependency state")


def test_isolated_import_has_no_runtime_side_effects() -> None:
    child = f"""
import contextlib, importlib.util, io, json, os, pathlib, sys
from types import ModuleType
root=pathlib.Path({str(REPO_ROOT)!r}); scan=pathlib.Path({str(SCAN_SOURCE)!r}); package={PACKAGE!r}
for name,path in (("isaaclab_tasks",root/'source'/'isaaclab_tasks'/'isaaclab_tasks'),
                  ("isaaclab_tasks.direct",root/'source'/'isaaclab_tasks'/'isaaclab_tasks'/'direct'),
                  (package,scan)):
    m=ModuleType(name); m.__package__=name; m.__path__=[str(path)]; sys.modules[name]=m
def load(key,path):
    spec=importlib.util.spec_from_file_location(key,path); m=importlib.util.module_from_spec(spec); sys.modules[key]=m
    before=sys.dont_write_bytecode
    try: sys.dont_write_bytecode=True; spec.loader.exec_module(m)
    finally: sys.dont_write_bytecode=before
    return m
modules_before=set(sys.modules); cwd=os.getcwd(); env=dict(os.environ)
files=tuple(sorted(str(p.relative_to(pathlib.Path.cwd())) for p in pathlib.Path.cwd().rglob('*')))
out=io.StringIO(); err=io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    load(package+'.assignment_profile_contract',scan/'assignment_profile_contract.py')
    module=load(package+'.assignment_event_profile_schema_contract_v2',scan/'assignment_event_profile_schema_contract_v2.py')
    scale=module.build_event_policy_scale_contract_v2(M=3,N=12,ordered_agent_names=('robot_0','robot_1','robot_2'),ordered_task_ids=tuple(range(12)),scene_env_spacing=12.0,sim_dt_seconds=0.01,control_decimation=4,episode_time_limit_seconds=40.0)
    module.build_assignment_event_profile_schema_v2_descriptor(scale_contract=scale)
added=set(sys.modules)-modules_before
result={{'stdout':out.getvalue(),'stderr':err.getvalue(),'cwd':os.getcwd()==cwd,'env':dict(os.environ)==env,
 'files':tuple(sorted(str(p.relative_to(pathlib.Path.cwd())) for p in pathlib.Path.cwd().rglob('*')))==files,
 'forbidden':not any(name.startswith(('omni','isaaclab.app','harl','torch','numpy')) for name in added),
 'canonical':package+'.assignment_event_profile_schema_contract_v2' in sys.modules,
 'bare':'assignment_event_profile_schema_contract_v2' not in sys.modules}}
print(json.dumps(result,sort_keys=True))
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [sys.executable, "-c", child],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    for key, value in payload.items():
        if key in ("stdout", "stderr"):
            _assert(value == "", f"child output: {key}")
        else:
            _assert(value is True, f"child isolation: {key}")


TESTS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("canonical_version_and_v1_preservation", test_canonical_version_and_v1_preservation),
    ("no_clock_or_hidden_replacement", test_no_clock_or_hidden_replacement),
    ("identity_capture_is_exact_and_immutable", test_identity_capture_is_exact_and_immutable),
    ("wrong_p2_fails_closed", test_wrong_p2_fails_closed),
    ("wrong_episode_fails_closed_without_normalization", test_wrong_episode_fails_closed_without_normalization),
    ("wrong_transition_fails_closed", test_wrong_transition_fails_closed),
    ("wrong_open_window_fails_closed_by_object_identity", test_wrong_open_window_fails_closed_by_object_identity),
    ("model_feature_exclusion", test_model_feature_exclusion),
    ("manifest_derived_dimensions_and_no_compatibility_slot", test_manifest_derived_dimensions_and_no_compatibility_slot),
    ("fixed_cardinality_profile_and_default_off", test_fixed_cardinality_profile_and_default_off),
    ("descriptor_immutability_and_scope_barriers", test_descriptor_immutability_and_scope_barriers),
    ("canonical_alias_import_fails_before_dependencies", test_canonical_alias_import_fails_before_dependencies),
    ("isolated_import_has_no_runtime_side_effects", test_isolated_import_has_no_runtime_side_effects),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, object]] = []
    for name, test in TESTS:
        try:
            test()
        except Exception as exc:
            results.append({"name": name, "status": "failed", "error": f"{type(exc).__name__}: {exc}"})
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {"suite": "assignment_phase_b2_i0_versioned_no_tick_contract_reconciliation_pure", "passed": passed, "total": len(results), "results": results}
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for item in results:
            suffix = "" if item["status"] == "passed" else f": {item['error']}"
            print(f"{item['status'].upper():6} {item['name']}{suffix}")
        print(f"{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
