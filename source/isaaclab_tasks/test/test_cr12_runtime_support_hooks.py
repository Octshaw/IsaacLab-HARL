"""Small CPU call-order tests; fake backends are not native lifecycle evidence."""

import ast
import copy
import inspect
from pathlib import Path
import types
import unittest
import numpy as np


SOURCE = Path(__file__).resolve().parents[3] / "scripts/environments/_cr12_runtime_support.py"


class SceneFixture:
    """Run the actual scene function with only its imports replaced by CPU fakes."""

    def __init__(self):
        self.events = []
        self.robot = types.SimpleNamespace(is_initialized=False)
        self.physics_context = types.SimpleNamespace(
            prim_path="/physicsScene", use_gpu_pipeline=True,
            is_gpu_dynamics_enabled=lambda: True, get_solver_type=lambda: "TGS")
        self.sim = types.SimpleNamespace(
            device="cuda:0", physics_sim_view=None, index=0, time=0.0,
            get_physics_dt=lambda: 1 / 120,
            get_physics_context=lambda: self.physics_context,
            is_simulating=lambda: self.sim.physics_sim_view is not None,
            is_playing=lambda: self.robot.is_initialized,
            is_stopped=lambda: not self.robot.is_initialized,
            reset=self.reset,
            set_camera_view=lambda **kw: self.events.append("camera"))
        ground = types.SimpleNamespace(IsValid=lambda: True, HasAPI=lambda schema: True)
        self.stage = types.SimpleNamespace(GetPrimAtPath=lambda path: ground)
        self.info = {"body_paths": {"agv": "/World/CR12/agv"}}
        self.recorder = types.SimpleNamespace(
            result={"pd_selection": {"stiffness": [1] * 6, "damping": [2] * 6}}, phase="",
            emit=lambda *a, **kw: None, save=lambda: None)
        self.resources = {}
        self.args = types.SimpleNamespace(device="cuda:0", usd_path="accepted.usd",
                                          external_forces_every_iteration="on", external_forces_source="explicit_cli")
        context_api = types.SimpleNamespace(
            get_physx_interface=lambda: types.SimpleNamespace(is_running=lambda: self.robot.is_initialized),
            get_physx_simulation_interface=lambda: types.SimpleNamespace(get_attached_stage=lambda: 0))
        timeline_api = types.SimpleNamespace(get_timeline_interface=lambda: types.SimpleNamespace(
            is_playing=lambda: self.robot.is_initialized, is_stopped=lambda: not self.robot.is_initialized))
        contact_schema = types.SimpleNamespace(
            CreateContactOffsetAttr=lambda value: None, CreateRestOffsetAttr=lambda value: None)
        configuration = types.SimpleNamespace(
            PHYSICS_DT=1 / 120, CONTACT_OFFSET=.002, REST_OFFSET=0, ASSET_MODEL_ID="accepted",
            make_cr12_cfg=lambda *a, **kw: object())
        namespace = {
            "copy": copy,
            "_validated_root_pose": lambda value: np.array([[1.,0,0,0], [0,1.,0,0], [0,0,1.,.053], [0,0,0,1.]]),
            "DriveCheckError": RuntimeError,
            "sim_utils": types.SimpleNamespace(
                PhysxCfg=lambda **kw: types.SimpleNamespace(**kw),
                SimulationCfg=lambda **kw: types.SimpleNamespace(**kw),
                SimulationContext=lambda cfg: self.record("scene", self.sim),
                DomeLightCfg=lambda **kw: types.SimpleNamespace(func=lambda *a: self.events.append("light"))),
            "Articulation": lambda cfg: self.record("robot", self.robot),
            "configuration": configuration,
            "get_current_stage": lambda: self.stage,
            "add_ground_plane": lambda *a: self.record("ground", "/World/Ground"),
            "Gf": types.SimpleNamespace(Vec3f=lambda x: x),
            "PhysxSchema": types.SimpleNamespace(PhysxCollisionAPI=types.SimpleNamespace(Apply=lambda p: contact_schema)),
            "Usd": types.SimpleNamespace(TimeCode=types.SimpleNamespace(Default=lambda: "default")),
            "UsdPhysics": types.SimpleNamespace(CollisionAPI="CollisionAPI"),
            "ASSET_VERSION": "accepted", "ROOT_TRANSLATION": (0, 0, .053),
            "inspect_usd_stage": lambda *a: self.record("inspect", self.info),
            "check_source_collision_bounds": lambda *a: self.record("bounds", {}),
            "apply_scene_external_forces": lambda *a: self.record("external_flags", {
                "mode": "on", "scene_path": "/physicsScene", "before": {}, "after": {}, "readbacks": []}),
            "read_scene_external_forces": lambda *a: self.events.append("external_after_reset"),
            "SceneExternalForcesError": ValueError,
            "omni": types.SimpleNamespace(physx=context_api, timeline=timeline_api),
            "_calibrate_root_anchor": lambda *a: self.record("anchor", {}),
            "_frame_locals": lambda *a: self.record("frames", {}),
            "_make_contacts": lambda *a, **kw: self.record("contacts", {}),
            "_clock": lambda sim: (sim.index, sim.time),
            "_assert_active": lambda *a: self.events.append("active"),
            "_read_physics": lambda *a: self.record("native_read", ([0], [0], {})),
        }
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        names = ("create_fixed_cr12_world", "spawn_fixed_cr12_instance", "prepare_fixed_cr12_contacts",
                 "reset_fixed_cr12_world", "read_fixed_cr12_instance", "create_fixed_cr12_scene")
        functions = [copy.deepcopy(n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
        # No Kit/Isaac imports are executed. Every remaining statement is production code.
        for function in functions:
            function.body = [n for n in function.body if not isinstance(n, (ast.Import, ast.ImportFrom))]
        module = ast.fix_missing_locations(ast.Module(body=functions, type_ignores=[]))
        exec(compile(module, str(SOURCE), "exec"), namespace)
        self.create = namespace["create_fixed_cr12_scene"]

    def record(self, event, value):
        self.events.append(event)
        return value

    def reset(self):
        self.events.extend(["reset", "native_attach", "view_create"])
        self.robot.is_initialized = True
        self.sim.physics_sim_view = object()
        self.sim.index, self.sim.time = 2, 2 / 120

    def run(self, **hooks):
        return self.create(self.args, object(), self.recorder, self.resources, {"bodies": {}}, **hooks)


class SharedSceneHookTests(unittest.TestCase):
    def test_old_caller_without_keywords_keeps_original_setup_order(self):
        fixture = SceneFixture()
        scene = fixture.run()
        self.assertEqual(fixture.events, [
            "scene", "external_flags", "ground", "light", "robot", "inspect", "bounds", "anchor", "frames",
            "contacts", "camera", "reset", "native_attach", "view_create", "external_after_reset", "active", "native_read"])
        self.assertIs(scene["sim"], fixture.sim)
        self.assertIs(scene["robot"], fixture.robot)
        self.assertEqual(scene["after_reset"], (2, 2 / 120))

    def test_keywords_are_optional_and_keyword_only(self):
        fixture = SceneFixture()
        signature = inspect.signature(fixture.create)
        for name in ("pre_physics", "before_native_read"):
            self.assertIs(signature.parameters[name].default, None)
            self.assertEqual(signature.parameters[name].kind, inspect.Parameter.KEYWORD_ONLY)

    def test_pre_physics_once_after_anchor_before_contacts_reset_and_views(self):
        fixture = SceneFixture()
        calls = []
        def pre_physics(**context):
            self.assertFalse(context["robot"].is_initialized)
            self.assertIsNone(context["sim"].physics_sim_view)
            self.assertIs(context["stage"], fixture.stage)
            self.assertIs(context["info"], fixture.info)
            self.assertEqual(fixture.events[-2:], ["anchor", "frames"])
            self.assertNotIn("contacts", fixture.events)
            self.assertNotIn("reset", fixture.events)
            calls.append(context)
            fixture.events.append("overlay")
        fixture.run(pre_physics=pre_physics)
        self.assertEqual(len(calls), 1)
        self.assertLess(fixture.events.index("overlay"), fixture.events.index("native_attach"))
        self.assertLess(fixture.events.index("overlay"), fixture.events.index("view_create"))

    def test_native_guard_once_after_views_immediately_before_native_read(self):
        fixture = SceneFixture()
        calls = []
        def guard(**context):
            self.assertIs(context["robot"], fixture.robot)
            self.assertIs(context["sim"], fixture.sim)
            self.assertTrue(context["robot"].is_initialized)
            self.assertIn("view_create", fixture.events)
            self.assertNotIn("native_read", fixture.events)
            calls.append(context)
            fixture.events.append("native_guard")
        fixture.run(before_native_read=guard)
        self.assertEqual(len(calls), 1)
        self.assertEqual(fixture.events[-2:], ["native_guard", "native_read"])

    def test_pre_physics_failure_prevents_initialization_and_preserves_error(self):
        fixture = SceneFixture()
        primary = ValueError("overlay rejected")
        def reject(**context):
            raise primary
        with self.assertRaises(ValueError) as caught:
            fixture.run(pre_physics=reject)
        self.assertIs(caught.exception, primary)
        self.assertNotIn("reset", fixture.events)
        self.assertNotIn("native_read", fixture.events)
        self.assertIs(fixture.resources["sim"], fixture.sim)

    def test_native_guard_failure_prevents_parameter_getters_and_preserves_error(self):
        fixture = SceneFixture()
        primary = ValueError("NATIVE_VIEW_INVALID")
        def reject(**context):
            raise primary
        with self.assertRaises(ValueError) as caught:
            fixture.run(before_native_read=reject)
        self.assertIs(caught.exception, primary)
        self.assertIn("view_create", fixture.events)
        self.assertNotIn("native_read", fixture.events)
        self.assertEqual(fixture.events.count("reset"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
