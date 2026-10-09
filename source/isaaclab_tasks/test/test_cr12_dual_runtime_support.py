"""CPU checks of dual-instance mapping, shared reset and cross-robot guards."""
import ast
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts/environments'))
import _cr12_runtime_support as support
import _cr12_asset_math as am
import _cr12_pose_control as pc
import _cr12_external_forces as flags

DERIVED = ROOT/'source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf'


def info(root):
    bodies = {name: root+'/'+name for name in am.BODY_NAMES}
    joints = {name: root+'/'+name for name in am.JOINT_NAMES}
    collision_bodies = ['agv']*3 + list(am.BODY_NAMES[1:6]) + ['link_6']*2
    return {'body_paths': bodies, 'joint_paths': joints,
            'articulation_roots': [root+'/root_joint'], 'fixed_joint': root+'/root_joint',
            'fixed_bindings': [[], [bodies['agv']]],
            'joints': {name: {'body0': [bodies[am.BODY_NAMES[i]]], 'body1': [bodies[am.BODY_NAMES[i+1]]]}
                       for i,name in enumerate(am.JOINT_NAMES)},
            'colliders': [{'body': body, 'path': bodies[body]+f'/collision_{i}',
                           'local_bbox_min': [-.1]*3, 'local_bbox_max': [.1]*3}
                          for i,body in enumerate(collision_bodies)]}


def make_scene(index):
    root = f'/World/CR12_{index}'
    transform = np.eye(4)
    transform[:3, 3] = [0, 2*index, .053]
    record = SimpleNamespace(result={}, phase='', emit=mock.Mock(), save=mock.Mock())
    return {'prim_path': root, 'info': info(root), 'expected_root_pose': transform,
            'strict_instance': True, 'configuration': SimpleNamespace(CONTACT_OFFSET=.002),
            'robot': object(), 'recorder': record, 'usd_path': DERIVED.parent/'usd/cr12_fixed_lift0.usd'}


def poses(index):
    result = {name: np.eye(4) for name in am.BODY_NAMES}
    for pose in result.values():
        pose[:3, 3] = [0, 2*index, 1]
    return result


class InstanceTests(unittest.TestCase):
    def test_explicit_mapping_rejects_escaped_or_shared_namespaces(self):
        a = info('/World/CR12_1')
        support._validate_instance_paths(a, '/World/CR12_1')
        for kind in ('body_paths', 'joint_paths'):
            broken = copy.deepcopy(a)
            key = next(iter(broken[kind]))
            broken[kind][key] = broken[kind][key].replace('CR12_1', 'CR12_0')
            with self.assertRaises(support.DriveCheckError):
                support._validate_instance_paths(broken, '/World/CR12_1')

    def test_world_fixed_joint_must_bind_own_agv(self):
        a = info('/World/CR12_1')
        a['fixed_bindings'] = [[], ['/World/CR12_0/agv']]
        with self.assertRaises(support.DriveCheckError):
            support._validate_instance_paths(a, '/World/CR12_1')

    def test_body_and_joint_order_changes_are_name_mapped(self):
        s = make_scene(1)
        body_names = list(reversed(am.BODY_NAMES))
        joint_names = list(reversed(am.JOINT_NAMES))
        view = SimpleNamespace(prim_paths=s['info']['articulation_roots'],
            link_paths=[[s['info']['body_paths'][n] for n in body_names]],
            dof_paths=[[s['info']['joint_paths'][n] for n in joint_names]])
        s['robot'] = SimpleNamespace(is_initialized=True, is_fixed_base=True, num_instances=1,
                                    body_names=body_names, joint_names=joint_names, root_physx_view=view)
        result = support._check_native_instance(s)
        self.assertEqual(result['body_indices'], list(reversed(range(7))))
        self.assertEqual(result['joint_indices'], list(reversed(range(6))))
        self.assertEqual(set(s['_native_paths']), set(s['info']['body_paths'].values()))

    def test_native_robot1_bound_to_robot0_is_rejected(self):
        s = make_scene(1)
        wrong = info('/World/CR12_0')
        s['robot'] = SimpleNamespace(is_initialized=True, is_fixed_base=True, num_instances=1,
            body_names=list(am.BODY_NAMES), joint_names=list(am.JOINT_NAMES),
            root_physx_view=SimpleNamespace(prim_paths=wrong['articulation_roots'],
                link_paths=[list(wrong['body_paths'].values())], dof_paths=[list(wrong['joint_paths'].values())]))
        with self.assertRaises(support.DriveCheckError):
            support._check_native_instance(s)

    def test_independent_spawn_expectation_rejects_robot1_at_origin(self):
        s = make_scene(1)
        model = pc.KinematicModel.from_derived_urdf(DERIVED)
        wrong_root = np.eye(4)
        wrong_root[2,3] = .053
        wrong = model.forward(np.zeros(6), wrong_root)
        class Prim:
            def __init__(self, path): self.path = path
            def IsValid(self): return True
            def HasAPI(self, unused): return True
        s['stage'] = SimpleNamespace(GetPrimAtPath=Prim)
        pxr = SimpleNamespace(UsdPhysics=SimpleNamespace(RigidBodyAPI=object()))
        with mock.patch.dict(sys.modules, {'pxr': pxr}), mock.patch.object(
                support, '_usd_world_matrix', side_effect=lambda prim: wrong[prim.path.rsplit('/',1)[1]]):
            with self.assertRaises(support.DriveCheckError) as caught:
                support._check_instance_composition(s)
        self.assertEqual(caught.exception.category, 'instance_mapping')
        self.assertEqual(caught.exception.details['path'], '/World/CR12_1/agv')

    def test_expected_root_pose_is_validated_and_copied(self):
        expected = np.eye(4)
        actual = support._validated_root_pose(expected)
        actual[1,3] = 2
        self.assertEqual(expected[1,3], 0)
        for bad in (np.full((4,4), np.nan), np.zeros((4,4)), np.eye(3)):
            with self.assertRaises(support.DriveCheckError):
                support._validated_root_pose(bad)

    def test_dual_preinit_accepts_reverse_instance_order(self):
        scenes = [make_scene(1), make_scene(0)]
        world = {'stage': SimpleNamespace(Traverse=lambda: [])}
        for scene, other in ((scenes[0],scenes[1]),(scenes[1],scenes[0])):
            scene['contacts'] = {name: {'targets': dict.fromkeys(other['info']['body_paths'].values()),
                                       'body_path': scene['info']['body_paths'][name]}
                                 for name in am.BODY_NAMES}
        with mock.patch.dict(sys.modules, {'pxr': SimpleNamespace(UsdPhysics=object())}), \
                mock.patch.object(support, '_check_instance_composition', return_value={'verified':True}) as checks:
            support._check_dual_preinit(world, scenes)
        self.assertEqual(checks.call_count, 2)

    def test_dual_preinit_rejects_missing_peer_filters(self):
        scenes = [make_scene(0),make_scene(1)]
        for scene in scenes:
            scene['contacts'] = {name: {'targets': {}, 'body_path': scene['info']['body_paths'][name]}
                                 for name in am.BODY_NAMES}
        with mock.patch.dict(sys.modules, {'pxr': SimpleNamespace(UsdPhysics=object())}), \
                mock.patch.object(support, '_check_instance_composition', return_value={}):
            with self.assertRaises(support.DriveCheckError):
                support._check_dual_preinit({'stage':None}, scenes)

    def test_dual_preinit_rejects_empty_contact_set(self):
        scenes = [make_scene(0), make_scene(1)]
        for scene in scenes: scene['contacts'] = {}
        with mock.patch.dict(sys.modules, {'pxr': SimpleNamespace(UsdPhysics=object())}), \
                mock.patch.object(support, '_check_instance_composition', return_value={}):
            with self.assertRaises(support.DriveCheckError) as caught:
                support._check_dual_preinit({'stage': None}, scenes)
        self.assertEqual(caught.exception.category, 'contact_monitor')


class CrossGeometryTests(unittest.TestCase):
    def test_coarse_separation_reports_coverage_not_fake_fine_checks(self):
        result = support.check_cross_geometry(make_scene(0), poses(0), make_scene(1), poses(1))
        self.assertEqual(result['logical_pairs'], 100)
        self.assertEqual(result['fine_pairs_checked'], 0)
        self.assertTrue(result['coarse_separated'])
        self.assertAlmostEqual(result['minimum_axis_gap_m'], 1.796)
        self.assertEqual(result['gap_basis'], 'whole_robot_AABB_separation_lower_bound')

    def test_coarse_failure_falls_back_to_all_100_pairs(self):
        p0, p1 = poses(0), poses(0)
        for i,name in enumerate(am.BODY_NAMES):
            p0[name][0,3] = 4*i
            p1[name][0,3] = 4*i+2
        result = support.check_cross_geometry(make_scene(0), p0, make_scene(1), p1)
        self.assertFalse(result['coarse_separated'])
        self.assertEqual(result['fine_pairs_checked'], 100)
        self.assertAlmostEqual(result['minimum_axis_gap_m'], 1.796)

    def test_same_named_agv_has_no_cross_instance_exemption(self):
        with self.assertRaises(support.DriveCheckError) as caught:
            support.check_cross_geometry(make_scene(0), poses(0), make_scene(1), poses(0))
        self.assertIn('/CR12_0/agv/', caught.exception.details['left'])
        self.assertIn('/CR12_1/agv/', caught.exception.details['right'])
        self.assertFalse(caught.exception.details['contact_proven'])

    def test_missing_shape_nonfinite_and_wrong_margin_rejected(self):
        for mode in ('missing', 'nan', 'offset'):
            a, b = make_scene(0),make_scene(1)
            p = poses(1)
            if mode == 'missing': b['info']['colliders'].pop()
            if mode == 'nan': p['link_1'][0,0] = np.nan
            if mode == 'offset': b['configuration'].CONTACT_OFFSET = 0
            with self.assertRaises(support.DriveCheckError):
                support.check_cross_geometry(a, poses(0), b, p)


class ContactTests(unittest.TestCase):
    def contacts(self):
        sensors = SimpleNamespace(ContactSensorCfg=lambda **kw: SimpleNamespace(**kw),
                                  ContactSensor=lambda cfg: SimpleNamespace(cfg=cfg))
        with mock.patch.dict(sys.modules, {'isaaclab.sensors':sensors}):
            return support._make_contacts(info('/World/CR12_0'), '/World/Ground/CollisionPlane',
                extra_filter_paths=list(info('/World/CR12_1')['body_paths'].values()))

    def test_all_seven_peer_paths_on_every_body_including_agv(self):
        contacts = self.contacts()
        peer = set(info('/World/CR12_1')['body_paths'].values())
        for name, record in contacts.items():
            self.assertTrue(peer.issubset(record['targets']))
            self.assertEqual(len(peer.intersection(record['sensor'].cfg.filter_prim_paths_expr)), 7)
            self.assertEqual('/World/Ground/CollisionPlane' in record['targets'], name!='agv')

    def test_duplicate_or_own_body_filter_is_rejected(self):
        sensors = SimpleNamespace(ContactSensorCfg=object, ContactSensor=object)
        for extras in (['/World/CR12_1/agv']*2, ['/World/CR12_0/agv']):
            with mock.patch.dict(sys.modules, {'isaaclab.sensors':sensors}):
                with self.assertRaises(support.DriveCheckError):
                    support._make_contacts(info('/World/CR12_0'), '/World/Ground/CollisionPlane',
                                           extra_filter_paths=extras)

    def native_record(self):
        from test_cr12_contact_runtime import Sensor, Tensor
        paths = list(info('/World/CR12_1')['body_paths'].values())
        matrix = np.zeros((1,1,7,3))
        sensor = Sensor('/World/CR12_0/agv',np.float64)
        sensor.contact_physx_view.filter_paths=[paths]
        sensor.contact_physx_view.filter_count=7
        sensor.matrix=Tensor(matrix)
        contacts={'agv':support._new_contact_record(sensor,dict.fromkeys(paths),'/World/CR12_0/agv')}
        support._check_contacts(contacts,0.0,initialize=True)
        return contacts,matrix

    def test_native_filters_dimensions_freshness_and_peer_force(self):
        contacts, matrix = self.native_record()
        self.assertEqual(support._check_contacts(contacts, pc.DT), 0)
        self.assertEqual(contacts['agv']['updates'], 1)
        contacts, matrix = self.native_record()
        matrix[0,0,0,0] = .11
        with self.assertRaises(support.DriveCheckError) as caught:
            support._check_contacts(contacts, pc.DT)
        self.assertEqual(caught.exception.category, 'forbidden_contact')
        self.assertAlmostEqual(contacts['agv']['maximum_force_n'], .11)

    def test_native_mapping_and_stale_time_rejected(self):
        for mode in ('filter', 'time', 'shape'):
            contacts, matrix = self.native_record()
            sensor = contacts['agv']['sensor']
            if mode=='filter': sensor.contact_physx_view.filter_paths[0][0]='/World/CR12_0/link_2'
            if mode=='time': sensor.mode='skip'
            if mode=='shape': sensor.matrix.array=np.zeros((1,1,6,3))
            with self.assertRaises(support.DriveCheckError):
                support._check_contacts(contacts, pc.DT)


class SharedResetTests(unittest.TestCase):
    def world(self, delta=2):
        scenes = [make_scene(1),make_scene(0)]
        sim = SimpleNamespace(clock=(0,0))
        def reset(): sim.clock=(delta,delta*pc.DT)
        sim.reset=mock.Mock(side_effect=reset)
        world = {'_reset_started':False,'_instances':scenes,'sim':sim,
            'cfg':SimpleNamespace(dt=pc.DT,render_interval=2,gravity=(0,0,-9.81),
                                  physx=SimpleNamespace(solver_type=1)),
            'ground_path':'/World/Ground/CollisionPlane','stage':None,'setup':{},
            'physx_schema':None,'usd_physics':None,'default_time':None}
        for scene in scenes: scene.update(world=world, contacts={})
        recorder=SimpleNamespace(result={},phase='')
        return world, scenes, recorder

    def test_reverse_order_two_instances_one_two_tick_reset(self):
        world, scenes, recorder=self.world()
        with mock.patch.object(support,'_check_dual_preinit'), mock.patch.object(support,'_clock',side_effect=lambda s:s.clock), \
                mock.patch.object(support,'_assert_active'), mock.patch.object(flags,'read_scene_external_forces'):
            support.reset_fixed_cr12_world(world,None,recorder,scenes)
            with self.assertRaises(support.DriveCheckError):
                support.reset_fixed_cr12_world(world,None,recorder,scenes)
        world['sim'].reset.assert_called_once()
        self.assertEqual(scenes[0]['after_reset'],scenes[1]['after_reset'])
        self.assertIsNot(scenes[0]['recorder'].result['initialization'],scenes[1]['recorder'].result['initialization'])

    def test_missing_peer_or_four_init_steps_is_rejected(self):
        world, scenes, recorder=self.world(4)
        with mock.patch.object(support,'_check_dual_preinit'), mock.patch.object(support,'_clock',side_effect=lambda s:s.clock), \
                mock.patch.object(support,'_assert_active'), mock.patch.object(flags,'read_scene_external_forces'):
            with self.assertRaises(support.DriveCheckError):
                support.reset_fixed_cr12_world(world,None,recorder,scenes)
        self.assertEqual(recorder.result['initialization']['after_reset_clock'][0],4)
        world,scenes,recorder=self.world()
        with self.assertRaises(support.DriveCheckError):
            support.reset_fixed_cr12_world(world,None,recorder,scenes[:1])
        world['sim'].reset.assert_not_called()

    def test_no_scene_reset_in_spawn_or_instance_read(self):
        tree=ast.parse((ROOT/'scripts/environments/_cr12_runtime_support.py').read_text(encoding='utf-8'))
        names=('spawn_fixed_cr12_instance','read_fixed_cr12_instance','prepare_fixed_cr12_contacts')
        for fn in (n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names):
            calls=[ast.unparse(n.func) for n in ast.walk(fn) if isinstance(n,ast.Call)]
            self.assertFalse(any(name.endswith('.reset') or name.endswith('.step') for name in calls),fn.name)


if __name__ == '__main__':
    unittest.main(verbosity=2)

