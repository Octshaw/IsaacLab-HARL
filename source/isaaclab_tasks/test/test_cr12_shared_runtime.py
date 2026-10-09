"""Shared preparation and unchanged AABB checks with CPU fake APIs only."""
from contextlib import ExitStack
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'scripts/environments'))
import _cr12_runtime_support as support
import _cr12_shared_task_profile as profile
import _cr12_pose_control as pc
import _cr12_camera_mount as mount
from test_cr12_shared_profile import URDF
from test_cr12_dual_runtime_support import info


class SharedRuntimeTests(unittest.TestCase):
    def test_initial_profile_root_q_and_legacy_gates(self):
        for robot in (0, 1):
            path = f'/World/CR12_{robot}'
            np.testing.assert_array_equal(support._validated_initial_configuration(profile.PROFILE_NAME,
                path, profile.root_pose(robot), profile.initial_q(robot)), profile.initial_q(robot))
        self.assertEqual(support._validated_initial_configuration('legacy', '/World/CR12', None, None), (0.,)*6)
        for name, path, root, q in (
            ('legacy', '/World/CR12', None, profile.initial_q(0)),
            (profile.PROFILE_NAME, '/World/CR12_1', profile.root_pose(0), profile.initial_q(1)),
            (profile.PROFILE_NAME, '/World/CR12_1', profile.root_pose(1), np.zeros(6)),
            (profile.PROFILE_NAME, '/World/CR12_1', profile.root_pose(1), np.full(6, np.nan)),
            ('other', '/World/CR12_1', profile.root_pose(1), profile.initial_q(1))):
            with self.assertRaises(support.DriveCheckError):
                support._validated_initial_configuration(name, path, root, q)

    def test_nonzero_write_once_readback_and_warm_contact_distinction(self):
        self._initialize_case(shared=True)

    def test_legacy_still_writes_zero_and_checks_contacts(self):
        self._initialize_case(shared=False)

    def _initialize_case(self, shared):
        model = pc.KinematicModel.from_derived_urdf(URDF)
        q = profile.initial_q(1) if shared else np.zeros(6)
        root = profile.root_pose(1) if shared else profile.root_pose(0)
        events = []
        class Tensor:
            def __init__(self, value): self.value, self.device = np.array(value), 'cuda:0'
        def write(position, velocity, **kw):
            events.append(('write', position.value.copy(), velocity.value.copy(), kw))
        robot = SimpleNamespace(device='cuda:0', data=SimpleNamespace(joint_pos=Tensor(q),joint_vel=Tensor(q*0)),
            write_joint_state_to_sim=write, set_joint_position_target=mock.Mock(), set_joint_velocity_target=mock.Mock(),
            reset=mock.Mock(), update=mock.Mock())
        fake_torch = SimpleNamespace(device=lambda v:v, float32=np.float32,
            zeros=lambda shape, **kw:Tensor(np.zeros(shape, dtype=np.float32)),
            tensor=lambda value, **kw:Tensor(np.asarray(value, dtype=np.float32)))
        rec = SimpleNamespace(result={'physical_backend':{}, 'initialization':{}})
        scene = {'sim': object(), 'robot':robot, 'configuration':SimpleNamespace(CONTACT_OFFSET=.002),
                 'body_ids':list(range(7)), 'joint_ids':list(reversed(range(6))), 'info':{'colliders':[]},
                 'contacts':{}, 'after_reset':(2,2/120), 'expected_root_pose':root,
                 'profile_name':profile.PROFILE_NAME if shared else 'legacy',
                 'prim_path':'/World/CR12_1' if shared else '/World/CR12',
                 'initial_q':q, 'usd_path':URDF.parent/'usd/cr12_fixed_lift0.usd'}
        with ExitStack() as stack:
            stack.enter_context(mock.patch.dict(sys.modules, {'torch':fake_torch}))
            for name, value in {'_joint_state':lambda *a:(q.tolist(),(q*0).tolist()),
                                '_body_poses':lambda *a:model.forward(q,root),
                                '_check_contacts':lambda *a,**kw:events.append(('contact',)),
                                '_contact_summary':lambda *a:{'updates':0},
                                '_clock':lambda *a:(2,2/120)}.items():
                stack.enter_context(mock.patch.object(support,name,value))
            result = support.initialize_fixed_cr12_state(SimpleNamespace(device='cuda:0'),rec,scene,
                                                        geometry_check=lambda *a:1.)
            with self.assertRaises(support.DriveCheckError):
                support.initialize_fixed_cr12_state(SimpleNamespace(device='cuda:0'),rec,scene)
        writes = [v for v in events if v[0]=='write']
        self.assertEqual(len(writes),1)
        np.testing.assert_array_equal(writes[0][1], q[None].astype(np.float32))
        np.testing.assert_array_equal(writes[0][2], np.zeros((1,6)))
        self.assertEqual(writes[0][3]['joint_ids'],list(reversed(range(6))))
        self.assertEqual(rec.result['initialization']['root_state_writes'],0)
        self.assertEqual(result['baseline'],(2,2/120))
        if shared:
            self.assertEqual(events[0][0],'contact')
            self.assertIn('NOT_OBSERVED',rec.result['initialization']['nonzero_contact_status'])
        else:
            self.assertEqual(events[0][0],'write')
            self.assertNotIn('nonzero_contact_status',rec.result['initialization'])

    def test_production_self_guard_keeps_ground_and_adjacency_rules(self):
        colliders = info('/World/CR12_0')['colliders']
        poses = {name:np.eye(4) for name in pc.BODY_NAMES}
        for index,name in enumerate(pc.BODY_NAMES): poses[name][:3,3]=[index,0,1]
        self.assertAlmostEqual(support._check_geometry(colliders,poses,.002),.9)
        poses['link_3'] = poses['link_1'].copy()
        with self.assertRaises(support.DriveCheckError) as caught:
            support._check_geometry(colliders,poses,.002)
        self.assertEqual(caught.exception.category,'geometry_guard')
        poses['link_3'][:3,3]=[3,0,-.2]
        with self.assertRaises(support.DriveCheckError) as caught:
            support._check_geometry(colliders,poses,.002)
        self.assertIn('ground',str(caught.exception))

    def test_production_cross_guard_all_pairs_and_double_margin(self):
        scenes = [profile.geometry_scene(i,info('/World/CR12')['colliders']) for i in (0,1)]
        poses = [{name:np.eye(4) for name in pc.BODY_NAMES} for _ in range(2)]
        for robot in (0,1):
            for value in poses[robot].values(): value[:3,3]=[0,robot*.2041,1]
        record = support.check_cross_geometry(scenes[0],poses[0],scenes[1],poses[1])
        self.assertEqual(record['logical_pairs'],100)
        self.assertGreater(record['minimum_axis_gap_m'],0)
        for value in poses[1].values(): value[1,3]=.2039
        with self.assertRaises(support.DriveCheckError) as caught:
            support.check_cross_geometry(scenes[0],poses[0],scenes[1],poses[1])
        self.assertFalse(caught.exception.details['contact_proven'])
        self.assertEqual(caught.exception.details['statistics']['fine_pairs_checked'],1)


class FixtureTests(unittest.TestCase):
    def setUp(self):
        self.prims = {}
        class Prim:
            def __init__(self,path,kind='',matrix=None): self.path,self.kind,self.matrix=path,kind,matrix
            def IsValid(self): return bool(self.kind)
            def HasAPI(self,api): return False
            def IsA(self,kind): return self.kind==kind
        self.Prim=Prim
        self.stage=SimpleNamespace(GetPrimAtPath=lambda path:self.prims.get(path,Prim(path)))
        self.config=mount.VirtualCameraConfig((.168921722410,-.129429244995,.192403900145),(0,0,0),(1,1,1),'none','none')
        self.pxr=SimpleNamespace(UsdGeom=SimpleNamespace(GetStageMetersPerUnit=lambda s:1.,Mesh='Mesh',
            Xformable=lambda prim:SimpleNamespace(GetResetXformStack=lambda:False,
                GetLocalTransformation=lambda:prim.matrix.T)),
            UsdPhysics=SimpleNamespace(MassAPI='Mass',RigidBodyAPI='Rigid',CollisionAPI='Collision',Joint='Joint'))
        self.create_calls=[]

    def create(self,stage,path,matrix):
        self.create_calls.append(path)
        self.prims[path]=self.Prim(path,'Xform',matrix.copy())
        self.prims[path+'/ColorPlate']=self.Prim(path+'/ColorPlate','Mesh')

    def test_shared_fixture_one_create_two_owned_references(self):
        with mock.patch.dict(sys.modules,{'pxr':self.pxr}),mock.patch.object(mount,'_create_fixture',self.create):
            handle=mount.create_shared_fixture(self.stage,self.config,profile.scanner_target())
            for _ in (0,1):
                np.testing.assert_array_equal(mount._validate_shared_fixture(self.stage,handle,self.config),handle.world_matrix)
            with self.assertRaises(ValueError): mount.create_shared_fixture(self.stage,self.config,profile.scanner_target())
        self.assertEqual(len(self.create_calls),1)

    def test_shared_fixture_wrong_stage_or_mutated_pose_rejected(self):
        with mock.patch.dict(sys.modules,{'pxr':self.pxr}),mock.patch.object(mount,'_create_fixture',self.create):
            handle=mount.create_shared_fixture(self.stage,self.config,profile.scanner_target())
            with self.assertRaises(ValueError): mount._validate_shared_fixture(object(),handle,self.config)
            self.prims[handle.path].matrix[0,3]+=.01
            with self.assertRaises(ValueError): mount._validate_shared_fixture(self.stage,handle,self.config)


if __name__=='__main__': unittest.main()
