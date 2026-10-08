"""CPU checks with synthetic USD interfaces; these are not rendering evidence."""

import ast
import copy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
HELPER = ROOT / "scripts/environments/_cr12_visual_geometry.py"
spec = importlib.util.spec_from_file_location("_cr12_visual_geometry_cpu", HELPER)
geometry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(geometry)


def mapping_fixture():
    records = []
    for i in range(10):
        body, shape = f"link_{i % 7}", f"shape_{i}"
        for kind in ("visual", "collision"):
            container = "visuals" if kind == "visual" else "collisions"
            records.append({
                "name": f"{shape}_{kind}", "kind": kind, "body": body,
                "path": f"/World/CR12/{body}/{container}/{shape}_{kind}/mesh",
                "source": f"source/{shape}.obj", "has_collision_api": kind == "collision",
                "role_schema_matches": True, "effective_visibility": "inherited",
                "comparison": {"points_match": True, "triangle_geometry_match": True},
            })
    return {"pass": True, "meshes": records, "errors": []}


class FakePath(str):
    def IsPropertyPath(self):
        return "." in self

    def GetPrimPath(self):
        return FakePath(self.split(".", 1)[0])


class FakeLayer:
    registry = {}

    def __init__(self, identifier):
        self.identifier = identifier
        self.subLayerPaths = []
        self.opinions = {}
        self.specs = {}
        self.registry[identifier] = self

    @classmethod
    def CreateAnonymous(cls, label):
        return cls(f"anon:{len(cls.registry)}:{label}")

    def GetObjectAtPath(self, path):
        return self.specs[str(path)]

    def Traverse(self, path, callback):
        callback(FakePath("/"))
        for name in self.specs:
            callback(FakePath(name))

    def ExportToString(self):
        return repr((self.opinions, {key: vars(value) for key, value in self.specs.items()}))


class FakeVisibility:
    def __init__(self, prim):
        self.prim = prim

    def Set(self, value):
        stage, path = self.prim.stage, self.prim.path
        if path == stage.fail_write_path:
            raise RuntimeError("synthetic visibility write failure")
        layer = stage.edit_target
        layer.opinions[path] = value
        layer.specs[path] = types.SimpleNamespace(specifier="over", typeName="")
        layer.specs[path + ".visibility"] = types.SimpleNamespace(name="visibility")
        stage.writes.append((layer.identifier, path, "visibility", value))
        return True


class FakePrim:
    def __init__(self, stage, path):
        self.stage, self.path = stage, path
        self.children = []
        self.composition_specs = []
        self.kind = "Mesh"
        self.physics = {"CollisionAPI"} if "/collisions/" in path else set()
        self.parent = None
        self.transform = np.eye(4)
        self.point_spec = ""

    def GetPath(self):
        return FakePath(self.path)

    def GetPrimStack(self):
        return self.composition_specs

    def IsA(self, schema):
        return schema is FakeMesh and self.kind == "Mesh"

    def HasAPI(self, schema):
        return schema in self.physics

    def GetParent(self):
        return self.parent

    def GetPointsAttr(self):
        prim = self
        class Points:
            def GetPropertyStack(self, time):
                if time != "default_time":
                    raise AssertionError("Expected explicit default TimeCode")
                return [types.SimpleNamespace(layer=prim.stage.root, path=prim.point_spec)]

            def Get(self):
                raise AssertionError("Metadata-only mapping must not read points")
        return Points()

    def GetChildren(self):
        return self.children

    def CreateVisibilityAttr(self):
        return FakeVisibility(self)

    def ComputeVisibility(self):
        if self.path in self.stage.session.opinions:
            return self.stage.session.opinions[self.path]
        for name in self.stage.session.subLayerPaths:
            layer = FakeLayer.registry[name]
            if self.path in layer.opinions:
                return layer.opinions[self.path]
        return "inherited"


class FakeChild:
    def __init__(self, kind="GeomSubset", applied=(), physics=(), children=()):
        self.kind, self.applied, self.physics, self.children = kind, applied, physics, children

    def IsA(self, schema):
        return self.kind == schema

    def GetChildren(self):
        return self.children

    def GetAppliedSchemas(self):
        return self.applied

    def HasAPI(self, schema):
        return schema in self.physics


class FakeStage:
    def __init__(self, mapping):
        FakeLayer.registry = {}
        self.session, self.root = FakeLayer("session"), FakeLayer("source.usd")
        FakeLayer("existing_session_overlay")
        self.session.subLayerPaths = ["existing_session_overlay"]
        self.edit_target = self.root
        self.prims = {r["path"]: FakePrim(self, r["path"]) for r in mapping["meshes"]}
        self.robot_root = FakePrim(self, "/World/CR12")
        self.robot_root.kind = "Xform"
        self.fail_write_path, self.writes = None, []

    def GetSessionLayer(self):
        return self.session

    def GetPrimAtPath(self, path):
        if path == "/World/CR12":
            return self.robot_root
        return self.prims.get(path)


class FakeMesh:
    def __new__(cls, prim):
        return prim


class FakeMatrix:
    def __init__(self, matrix):
        self.matrix = matrix

    def __mul__(self, other):
        return FakeMatrix(self.matrix @ other.matrix)

    def GetInverse(self):
        return FakeMatrix(np.linalg.inv(self.matrix))

    def __array__(self, dtype=None):
        return np.asarray(self.matrix, dtype=dtype)


class FakeEditContext:
    def __init__(self, stage, layer):
        self.stage, self.layer = stage, layer

    def __enter__(self):
        self.previous = self.stage.edit_target
        self.stage.edit_target = self.layer

    def __exit__(self, *exc):
        self.stage.edit_target = self.previous


def fake_pxr():
    module = types.ModuleType("pxr")
    module.Sdf = types.SimpleNamespace(Layer=FakeLayer, SpecifierOver="over")
    module.Usd = types.SimpleNamespace(EditContext=FakeEditContext,
        TimeCode=types.SimpleNamespace(Default=lambda: "default_time"),
        PrimRange=lambda root: [root, *root.stage.prims.values()])
    module.UsdGeom = types.SimpleNamespace(Imageable=lambda prim: prim, Subset="GeomSubset",
        Mesh=FakeMesh, XformCache=lambda time: types.SimpleNamespace(
            GetLocalToWorldTransform=lambda prim: FakeMatrix(prim.transform.T)),
        Tokens=types.SimpleNamespace(invisible="invisible"))
    module.UsdPhysics = types.SimpleNamespace(CollisionAPI="CollisionAPI", RigidBodyAPI="RigidBodyAPI")
    return mock.patch.dict(sys.modules, {"pxr": module})


class CollisionSelectionTests(unittest.TestCase):
    def test_selects_only_ten_distinct_collision_mesh_leaves(self):
        mapping = mapping_fixture()
        before = copy.deepcopy(mapping)
        result = geometry.select_collision_leaves(mapping)
        self.assertEqual(len(result), 10)
        self.assertEqual(result, [r["path"] for r in mapping["meshes"] if r["kind"] == "collision"])
        self.assertEqual(mapping, before)

    def test_unresolved_mapping_rejected(self):
        for state in (False, None):
            mapping = mapping_fixture()
            mapping["pass"] = state
            with self.subTest(state=state), self.assertRaises(ValueError):
                geometry.select_collision_leaves(mapping)

    def test_missing_visual_and_wrong_body_rejected(self):
        for mutation in (lambda m: m["meshes"].pop(0),
                         lambda m: m["meshes"][0].update(body="another_body")):
            mapping = mapping_fixture()
            mutation(mapping)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                geometry.select_collision_leaves(mapping)

    def test_shared_visual_collision_prim_rejected(self):
        mapping = mapping_fixture()
        mapping["meshes"][0]["path"] = mapping["meshes"][1]["path"]
        with self.assertRaises(ValueError):
            geometry.select_collision_leaves(mapping)

    def test_visual_with_collider_or_collision_without_schema_rejected(self):
        for index, value in ((0, True), (1, False)):
            mapping = mapping_fixture()
            mapping["meshes"][index]["has_collision_api"] = value
            with self.subTest(index=index), self.assertRaises(ValueError):
                geometry.select_collision_leaves(mapping)

    def test_role_and_geometry_proofs_required_for_both_shapes(self):
        for index in (0, 1):
            for key in ("role_schema_matches", "points_match", "triangle_geometry_match"):
                mapping = mapping_fixture()
                record = mapping["meshes"][index]
                (record if key == "role_schema_matches" else record["comparison"])[key] = False
                with self.subTest(index=index, key=key), self.assertRaises(ValueError):
                    geometry.select_collision_leaves(mapping)

    def test_parent_body_and_visual_paths_cannot_be_selected(self):
        for path in ("/World/CR12/link_0", "/World/CR12/link_0/collisions",
                     "/World/CR12/link_0/collisions/shape_0_collision",
                     "/World/CR12/link_0/visuals/shape_0_visual/mesh"):
            mapping = mapping_fixture()
            mapping["meshes"][1]["path"] = path
            with self.subTest(path=path), self.assertRaises(ValueError):
                geometry.select_collision_leaves(mapping)

    def test_hidden_correct_visual_rejected(self):
        mapping = mapping_fixture()
        mapping["meshes"][0]["effective_visibility"] = "invisible"
        with self.assertRaises(ValueError):
            geometry.select_collision_leaves(mapping)

    def test_missing_extra_and_duplicate_collision_rejected(self):
        for mutation in (lambda m: m["meshes"].pop(),
                         lambda m: m["meshes"].append(copy.deepcopy(m["meshes"][1])),
                         lambda m: m["meshes"][3].update(path=m["meshes"][1]["path"])):
            mapping = mapping_fixture()
            mutation(mapping)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                geometry.select_collision_leaves(mapping)


class SessionOverrideTests(unittest.TestCase):
    def setUp(self):
        self.mapping = mapping_fixture()
        self.stage = FakeStage(self.mapping)
        self.patch = fake_pxr()
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.override = geometry.CollisionVisualOverride(self.stage, self.mapping)

    def test_apply_revoke_restores_target_and_session_and_keeps_visuals(self):
        previous_paths = list(self.stage.session.subLayerPaths)
        previous_target = self.stage.edit_target
        metadata = self.override.apply(before_first_physics_initialization=True)
        self.assertFalse(metadata["saved_to_disk"])
        self.assertIs(self.stage.edit_target, previous_target)
        self.assertEqual(self.stage.session.subLayerPaths[1:], previous_paths)
        self.assertEqual(len(self.stage.writes), 10)
        self.assertEqual({w[2:] for w in self.stage.writes}, {("visibility", "invisible")})
        self.assertEqual(self.stage.root.opinions, {})
        for record in self.mapping["meshes"]:
            self.assertEqual(self.stage.prims[record["path"]].ComputeVisibility(),
                             "invisible" if record["kind"] == "collision" else "inherited")
        self.override.revoke()
        self.assertEqual(self.stage.session.subLayerPaths, previous_paths)
        self.assertIs(self.stage.edit_target, previous_target)
        self.assertTrue(all(p.ComputeVisibility() == "inherited" for p in self.stage.prims.values()))
        self.override.revoke()  # Idempotent once the precise layer has been removed.

    def test_partial_write_exception_rolls_back_composition_and_edit_target(self):
        self.stage.fail_write_path = self.override.paths[4]
        with self.assertRaisesRegex(RuntimeError, "synthetic visibility"):
            self.override.apply(before_first_physics_initialization=True)
        self.assertEqual(len(self.stage.writes), 4)
        self.assertEqual(self.stage.session.subLayerPaths, ["existing_session_overlay"])
        self.assertIs(self.stage.edit_target, self.stage.root)
        self.assertIsNone(self.override.layer)
        self.assertTrue(all(p.ComputeVisibility() == "inherited" for p in self.stage.prims.values()))

    def test_missing_or_nonleaf_prim_rolls_back_without_hiding_parent(self):
        for missing in (True, False):
            stage = FakeStage(self.mapping)
            override = geometry.CollisionVisualOverride(stage, self.mapping)
            if missing:
                del stage.prims[override.paths[0]]
            else:
                stage.prims[override.paths[0]].children = [FakeChild(kind="Mesh")]
            with self.subTest(missing=missing), self.assertRaises(ValueError):
                override.apply(before_first_physics_initialization=True)
            self.assertEqual(stage.writes, [])
            self.assertEqual(stage.session.subLayerPaths, ["existing_session_overlay"])
            self.assertIs(stage.edit_target, stage.root)

    def test_nonphysical_geom_subsets_are_allowed_without_child_edits(self):
        children = [FakeChild(), FakeChild(applied=("MaterialBindingAPI",))]
        self.stage.prims[self.override.paths[0]].children = children
        self.override.apply(before_first_physics_initialization=True)
        self.assertEqual(len(self.stage.writes), 10)
        self.assertEqual([w[1] for w in self.stage.writes], self.override.paths)
        self.assertEqual(self.stage.prims[self.override.paths[0]].children, children)
        self.assertTrue(self.override.verify())
        self.override.revoke()
        self.assertEqual(self.stage.session.subLayerPaths, ["existing_session_overlay"])
        self.assertIs(self.stage.edit_target, self.stage.root)

    def test_physical_schema_or_nested_subset_children_rejected_and_rolled_back(self):
        for child in (FakeChild(applied=("PhysicsCollisionAPI",)),
                      FakeChild(physics=("CollisionAPI",)),
                      FakeChild(physics=("RigidBodyAPI",)),
                      FakeChild(children=(FakeChild(),))):
            stage = FakeStage(self.mapping)
            override = geometry.CollisionVisualOverride(stage, self.mapping)
            stage.prims[override.paths[0]].children = [child]
            with self.subTest(child=child), self.assertRaisesRegex(ValueError, "nonphysical"):
                override.apply(before_first_physics_initialization=True)
            self.assertEqual(stage.writes, [])
            self.assertEqual(stage.session.subLayerPaths, ["existing_session_overlay"])
            self.assertIs(stage.edit_target, stage.root)
            self.assertIsNone(override.layer)

    def test_stronger_session_opinion_is_not_overwritten(self):
        path = self.override.paths[0]
        self.stage.session.opinions[path] = "inherited"
        with self.assertRaisesRegex(ValueError, "did not take effect"):
            self.override.apply(before_first_physics_initialization=True)
        self.assertEqual(self.stage.session.opinions, {path: "inherited"})
        self.assertEqual(self.stage.session.subLayerPaths, ["existing_session_overlay"])
        self.assertIs(self.stage.edit_target, self.stage.root)

    def test_double_apply_rejected_without_layer_leak(self):
        self.override.apply(before_first_physics_initialization=True)
        paths = list(self.stage.session.subLayerPaths)
        with self.assertRaisesRegex(ValueError, "already applied"):
            self.override.apply(before_first_physics_initialization=True)
        self.assertEqual(self.stage.session.subLayerPaths, paths)
        self.override.revoke()

    def test_external_session_change_is_preserved_and_reported(self):
        self.override.apply(before_first_physics_initialization=True)
        self.stage.session.subLayerPaths.append("external_new_layer")
        current = list(self.stage.session.subLayerPaths)
        with self.assertRaisesRegex(ValueError, "changed externally"):
            self.override.revoke()
        self.assertEqual(self.stage.session.subLayerPaths, current)

    def test_layer_property_whitelist_rejects_physical_attribute(self):
        self.override.apply(before_first_physics_initialization=True)
        self.override.layer.specs[self.override.paths[0] + ".physics:collisionEnabled"] = types.SimpleNamespace(
            name="physics:collisionEnabled")
        with self.assertRaisesRegex(ValueError, "Unexpected render override property"):
            self.override.verify()
        self.override.revoke()

    def test_layer_whitelist_rejects_new_typed_prim(self):
        self.override.apply(before_first_physics_initialization=True)
        self.override.layer.specs[self.override.paths[0]].typeName = "Mesh"
        with self.assertRaisesRegex(ValueError, "must not define"):
            self.override.verify()
        self.override.revoke()

    def test_apply_requires_explicit_prephysics_attestation_before_any_write(self):
        for value in (False, None, 1):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Caller must verify"):
                self.override.apply(before_first_physics_initialization=value)
        self.assertEqual(self.stage.writes, [])
        self.assertEqual(self.override.apply_count, 0)

    def test_sealed_lifecycle_is_read_only_and_cannot_revoke_or_reapply(self):
        self.override.apply(before_first_physics_initialization=True)
        sealed = self.override.seal_before_physics_initialization()
        self.assertEqual(sealed["apply_count"], 1)
        self.assertEqual(sealed["collision_leaves_invisible"], 10)
        self.assertEqual(sealed["visuals_visible"], 10)
        before = (list(self.stage.writes), list(self.stage.session.subLayerPaths))
        for phase in ("after_initialization", "after_hold", "after_render", "before_close"):
            self.assertTrue(self.override.verify_stable(phase)["pass"])
        with self.assertRaisesRegex(ValueError, "cannot be revoked"):
            self.override.revoke()
        with self.assertRaisesRegex(ValueError, "reapplication"):
            self.override.apply(before_first_physics_initialization=True)
        self.assertEqual((self.stage.writes, self.stage.session.subLayerPaths), before)

    def test_unsealed_or_missing_layer_cannot_claim_runtime_stability(self):
        with self.assertRaises(ValueError):
            self.override.seal_before_physics_initialization()
        self.override.apply(before_first_physics_initialization=True)
        with self.assertRaises(ValueError):
            self.override.verify_stable("runtime")
        self.override.seal_before_physics_initialization()
        self.stage.session.subLayerPaths.remove(self.override.layer.identifier)
        with self.assertRaisesRegex(ValueError, "missing or duplicated"):
            self.override.verify_stable("runtime")

    def test_revoke_before_seal_does_not_permit_second_apply(self):
        self.override.apply(before_first_physics_initialization=True)
        self.override.revoke()
        with self.assertRaisesRegex(ValueError, "reapplication"):
            self.override.apply(before_first_physics_initialization=True)
        self.assertEqual(len(self.stage.writes), 10)

    def test_sealed_layer_change_detected_without_cleanup(self):
        self.override.apply(before_first_physics_initialization=True)
        self.override.seal_before_physics_initialization()
        self.override.layer.specs[self.override.paths[0]].new_metadata = "unexpected"
        paths = list(self.stage.session.subLayerPaths)
        with self.assertRaisesRegex(ValueError, "composition changed"):
            self.override.verify_stable("after_render")
        self.assertEqual(self.stage.session.subLayerPaths, paths)

    def test_correct_visual_must_remain_visible(self):
        self.override.apply(before_first_physics_initialization=True)
        self.override.seal_before_physics_initialization()
        self.stage.session.opinions[self.override.visual_paths[0]] = "invisible"
        with self.assertRaisesRegex(ValueError, "no longer visible"):
            self.override.verify_stable("after_hold")

    def test_robot_reference_change_detected_but_unrelated_kit_layer_allowed(self):
        self.override.apply(before_first_physics_initialization=True)
        self.override.seal_before_physics_initialization()
        FakeLayer("hydra_unrelated_layer")
        self.stage.session.subLayerPaths.append("hydra_unrelated_layer")
        self.assertTrue(self.override.verify_stable("render_resource_creation")["pass"])
        self.stage.robot_root.composition_specs.append(types.SimpleNamespace(
            layer=self.stage.root, path=FakePath("/World/CR12"),
            ListInfoKeys=lambda: ["references"], GetInfo=lambda key: "different_robot.usd"))
        with self.assertRaisesRegex(ValueError, "composition changed"):
            self.override.verify_stable("runtime")

    def test_no_implicit_revoke_protocol(self):
        for method in ("__enter__", "__exit__", "__del__", "close", "cleanup"):
            self.assertNotIn(method, geometry.CollisionVisualOverride.__dict__)


def metadata_fixture():
    robot = ET.Element("robot", name="accepted")
    mapping = {"meshes": []}
    bodies = {"agv": "agv", "elevate": "agv", "base_link": "agv",
              **{f"link_{i}": f"link_{i}" for i in range(1, 7)}, "scanner": "link_6"}
    transforms, specs = {}, {}
    for shape, body in bodies.items():
        node = next((n for n in robot if n.get("name") == body), None)
        if node is None:
            node = ET.SubElement(robot, "link", name=body)
        for kind in ("visual", "collision"):
            name = shape + "_" + kind
            representation = ET.SubElement(node, kind, name=name)
            xyz = {"elevate": (0, 0, .314), "base_link": (.105, 0, 1.062)}.get(shape, (0, 0, 0))
            yaw = 3*np.pi/4 if shape == "scanner" else 0
            ET.SubElement(representation, "origin", xyz=" ".join(map(str, xyz)), rpy=f"0 0 {yaw}")
            mesh_geometry = ET.SubElement(representation, "geometry")
            ET.SubElement(mesh_geometry, "mesh", filename=f"../../model/{shape}_{kind}.obj", scale="0.001 0.001 0.001")
            path = f"/World/CR12/{body}/{'visuals' if kind == 'visual' else 'collisions'}/{name}/mesh"
            mapping["meshes"].append({"path": path})
            matrix = np.eye(4)
            matrix[:3, :3] = .001*np.array([[np.cos(yaw), -np.sin(yaw), 0],
                                          [np.sin(yaw), np.cos(yaw), 0], [0, 0, 1]])
            matrix[:3, 3] = xyz
            transforms[path], specs[path] = matrix, f"/meshes/{shape}_{kind}/mesh.points"
    stage = FakeStage(mapping)
    stage.root.identifier = str(Path("accepted.urdf").resolve().parent / "usd" / "configuration" / "cr12_fixed_lift0_base.usd")
    for path, prim in stage.prims.items():
        owner = FakePrim(stage, path.split("/visuals/")[0].split("/collisions/")[0])
        owner.kind, owner.physics = "Xform", {"RigidBodyAPI"}
        prim.parent, prim.transform, prim.point_spec = owner, transforms[path], specs[path]
    return ET.ElementTree(robot), stage


class PreinitMetadataMappingTests(unittest.TestCase):
    def inspect(self, tree, stage):
        with fake_pxr(), mock.patch.object(ET, "parse", return_value=tree), mock.patch.object(
                geometry, "display_state", return_value={"effective_visibility": "inherited", "effective_purpose": "default"}):
            return geometry.inspect_preinit_mapping(stage, "/World/CR12", "accepted.urdf")

    def test_metadata_only_mapping_preserves_source_evidence_boundary(self):
        tree, stage = metadata_fixture()
        result = self.inspect(tree, stage)
        self.assertTrue(result["pass"])
        self.assertEqual(result["mesh_count"], 20)
        self.assertEqual(result["source_geometry_evidence"], "previous accepted audit; not repeated")
        self.assertEqual(len(geometry.select_collision_leaves(result)), 10)
        for record in result["meshes"]:
            self.assertNotIn("points_match", record["comparison"])
            self.assertTrue(record["metadata_identity_matches"])
            self.assertEqual(record["paths"], [record["leaves"][0]["path"]])
        self.assertEqual(stage.writes, [])

    def test_metadata_source_transform_schema_and_extra_mesh_mismatch_rejected(self):
        for mutation in (lambda p, s: setattr(p, "point_spec", "/meshes/wrong/mesh.points"),
                         lambda p, s: setattr(s.root, "identifier", "unaccepted_same_internal_mesh_paths.usd"),
                         lambda p, s: p.transform.__setitem__((0, 3), .1),
                         lambda p, s: p.physics.add("CollisionAPI"),
                         lambda p, s: s.prims.update({"/World/CR12/extra": FakePrim(s, "/World/CR12/extra")})):
            tree, stage = metadata_fixture()
            mutation(next(iter(stage.prims.values())), stage)
            with self.subTest(mutation=mutation):
                result = self.inspect(tree, stage)
                self.assertFalse(result["pass"])
                with self.assertRaises(ValueError):
                    geometry.select_collision_leaves(result)

    def test_derived_metadata_missing_duplicate_and_wrong_scale_rejected(self):
        for change in ("missing", "duplicate", "scale"):
            tree, stage = metadata_fixture()
            link = tree.getroot()[0]
            if change == "missing":
                link.remove(link.find("visual"))
            elif change == "duplicate":
                link.append(copy.deepcopy(link.find("visual")))
            else:
                link.find("visual/geometry/mesh").set("scale", "1 1 1")
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.inspect(tree, stage)


class ScopeAstTests(unittest.TestCase):
    def test_helper_has_no_save_or_physics_mutation_and_only_visibility_set(self):
        tree = ast.parse(HELPER.read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        forbidden = {"Save", "SaveAs", "Export", "SetActive", "Apply",
                     "SetTargets", "CreateMassAttr", "CreateCollisionEnabledAttr", "CreateRigidBodyEnabledAttr"}
        self.assertFalse(forbidden.intersection(n.func.attr for n in calls))
        setters = [n for n in calls if n.func.attr == "Set"]
        self.assertEqual(len(setters), 1)
        self.assertIsInstance(setters[0].func.value, ast.Call)
        self.assertEqual(setters[0].func.value.func.attr, "CreateVisibilityAttr")
        imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        names = [n.module or "" if isinstance(n, ast.ImportFrom) else a.name
                 for n in imports for a in (n.names if isinstance(n, ast.Import) else [None])]
        self.assertFalse(any(name.startswith(("pxr", "omni", "isaac", "torch")) for name in names))


if __name__ == "__main__":
    unittest.main(verbosity=2)
