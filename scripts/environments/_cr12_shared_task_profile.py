"""Frozen CPU-only inputs for the approved E1/M2/N1 handover.

No logs, simulator imports, CLI overrides or asset generation. Public matrix
and vector accessors return copies; the authoritative values are tuples.
"""
from dataclasses import dataclass
from types import SimpleNamespace
import numpy as np

PROFILE_NAME = 'shared_m2n1'
CASE = 'shared_cancel_clear_handover'
DT = 1.0 / 120.0
BLOCK_STEPS = 12
RENDER_INTERVAL = 2
REFERENCE_SECONDS = 24.0
MAX_SECONDS = 32.0
MAX_STEPS = POSE_STEPS = CLEANUP_STEPS = 3840
SETUP_MAX_STEPS = 360
CAPTURE_MAX_STEPS = 600
CLOSE_MAX_STEPS = 240
CAPTURE_WALL_SECONDS = 60.0
CLOSE_WALL_SECONDS = 30.0
REQUEST_MAX_STEPS = REQUEST_STEPS = B_BIND_MAX_STEPS = B_BINDING_STEPS = 4680
A_BIND_MAX_STEPS = A_BINDING_STEPS = 8520
HOST_MAX_TRANSITIONS = 1120
TASK_MAX_STEPS = 13440
TOTAL_CONTROLLED_MAX_STEPS = 13800
TOTAL_PHYSICS_MAX_STEPS = 13802
MAX_RENDER_OPPORTUNITIES = 6900
APP_CONSTRUCTOR_SECONDS = 180.0
WALL_SECONDS = 2400.0
HOST_TRANSITIONS = HOST_MAX_TRANSITIONS
A_BINDING_TICKS = A_BIND_MAX_STEPS
B_BINDING_TICKS = B_BIND_MAX_STEPS
SETUP_MAX_TICKS = SETUP_MAX_STEPS
TOTAL_CONTROLLED_TICKS = TOTAL_CONTROLLED_MAX_STEPS
STABLE_SAMPLES = 121
STABLE_SECONDS = 1.0
TUBE_DEG = 0.5
TRUST_DEG = (5., 30., 5., 5., 30., 5.)
ROOT_TRANSLATIONS = ((0., 0., .053), (1.0983385754148558, -.30, .053))
ROOT_QUATERNIONS_WXYZ = ((1., 0., 0., 0.), (0., 0., 0., 1.))
INITIAL_DEG = ((0., -16., 20., 0., -4., 90.), (0., -16., 20., 0., -4., -90.))
GOAL_DEG = ((0., 12., 20., 0., -32., 90.), (0., 12., 20., 0., -32., -90.))
SCANNER_TARGET = ((-.7071067811865477, .7071067811865474, 0., .5491692877074279),
                  (-.7071067811865474, -.7071067811865477, 0., -.15),
                  (0., 0., 1., 2.7893381484821624), (0., 0., 0., 1.))
SCANNER_WXYZ = (.3826834323650896, 0., 0., -.9238795325112868)
SHARED_FIXTURE_PATH = '/World/SharedTaskCameraFixture'


def _robot(robot_id):
    if isinstance(robot_id, (bool, np.bool_)) or not isinstance(robot_id, (int, np.integer)) or robot_id not in (0, 1):
        raise ValueError('This fixed profile requires robot_id 0 or 1')
    return int(robot_id)


def root_pose(robot_id):
    robot_id = _robot(robot_id)
    result = np.eye(4, dtype=np.float64)
    result[:3, 3] = ROOT_TRANSLATIONS[robot_id]
    if robot_id == 1:
        result[:3, :3] = np.diag([-1., -1., 1.])
    return result


def initial_q(robot_id):
    return np.radians(INITIAL_DEG[_robot(robot_id)])


q_park = initial_q
clear_q = initial_q


def goal_q(robot_id):
    return np.radians(GOAL_DEG[_robot(robot_id)])


def scanner_target():
    return np.array(SCANNER_TARGET, dtype=np.float64)


task_target = scanner_target


def park_pose(model, robot_id):
    import _cr12_pose_control as pc
    return pc.scanner_from_ee(model.forward(initial_q(robot_id), root_pose(robot_id))['link_6'])


@dataclass(frozen=True)
class FrozenJointWitnessPoseSegment:
    model: object
    robot_id: int
    kind: str

    def __post_init__(self):
        _robot(self.robot_id)
        if self.kind not in ('approach', 'retreat', 'park') or (self.kind == 'retreat' and self.robot_id != 0):
            raise ValueError('Only A approach/retreat, B approach and fixed parks are approved')

    @property
    def initial(self):
        return scanner_target() if self.kind == 'retreat' else park_pose(self.model, self.robot_id)

    @property
    def target(self):
        return scanner_target() if self.kind == 'approach' else park_pose(self.model, self.robot_id)

    def reference(self, time):
        import _cr12_pose_control as pc
        time = pc._time(time)
        if self.kind == 'park':
            return self.target
        u = min(time / REFERENCE_SECONDS, 1.0)
        h = 10*u**3 - 15*u**4 + 6*u**5
        park, goal = initial_q(self.robot_id), goal_q(self.robot_id)
        q = park + h*(goal-park) if self.kind == 'approach' else goal + h*(park-goal)
        return pc.scanner_from_ee(self.model.forward(q, root_pose(self.robot_id))['link_6'])


def segment(model, robot_id, kind='approach'):
    return FrozenJointWitnessPoseSegment(model, _robot(robot_id), kind)


def geometry_scene(robot_id, colliders):
    """CPU facade for the unchanged production AABB guard; no OBB fallback."""
    import copy
    prefix = f'/World/CR12_{_robot(robot_id)}'
    values = copy.deepcopy(colliders)
    for value in values:
        path = value['path']
        if not path.startswith('/World/CR12') or '/' not in path[len('/World/'):]:
            raise ValueError('Expected an explicit accepted collision prim path')
        value['path'] = prefix + '/' + path.split('/', 3)[3]
    return {'prim_path': prefix, 'info': {'colliders': values},
            'configuration': SimpleNamespace(CONTACT_OFFSET=.002)}


def record():
    return {'profile': PROFILE_NAME, 'case': CASE, 'roots': [root_pose(i).tolist() for i in (0, 1)],
            'initial_q_rad': [initial_q(i).tolist() for i in (0, 1)],
            'goal_q_rad': [goal_q(i).tolist() for i in (0, 1)], 'scanner_target': scanner_target().tolist(),
            'trust_degrees': list(TRUST_DEG), 'tube_degrees': TUBE_DEG,
            'reference_seconds': REFERENCE_SECONDS, 'segment_max_steps': MAX_STEPS,
            'setup_max_steps': SETUP_MAX_STEPS, 'request_max_steps': REQUEST_MAX_STEPS,
            'binding_max_steps': [A_BIND_MAX_STEPS, B_BIND_MAX_STEPS],
            'host_max_transitions': HOST_MAX_TRANSITIONS, 'total_controlled_max_steps': TOTAL_CONTROLLED_MAX_STEPS}
