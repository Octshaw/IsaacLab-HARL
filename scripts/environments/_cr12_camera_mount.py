"""Virtual camera v1: one source scanner bound, fixed mounting and optics.

CPU configuration is resolved before App creation. Runtime helpers only author
the new nonphysical camera/fixture before reset, or read their current poses.
No scanner, articulation, asset or optical pose is rewritten during execution.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import _cr12_pose_control as pc

# Local Isaac Sim 4.5 camera.py W_U_TRANSFORM, not a quaternion-order shortcut.
WORLD_TO_USD_AXES = np.array(((0., 0., -1.), (-1., 0., 0.), (0., 1., 0.)))


@dataclass(frozen=True)
class VirtualCameraConfig:
    translation_sc_m: tuple
    source_bounds_min_s_m: tuple
    source_bounds_max_s_m: tuple
    scanner_source: str
    scanner_source_sha256: str
    resolution: tuple = (640, 480)
    horizontal_fov_deg: float = 60.0
    horizontal_aperture_m: float = .036
    near_m: float = .01
    far_m: float = 10.0
    name: str = 'virtual_camera_mount_v1'
    channel: str = 'RGBA'

    @property
    def focal_length_m(self):
        return self.horizontal_aperture_m / (2 * math.tan(math.radians(self.horizontal_fov_deg) / 2))

    @property
    def t_sc(self):
        result = np.eye(4)
        result[:3, 3] = self.translation_sc_m
        return result

    @property
    def t_ec(self):
        return pc.scanner_from_ee(np.eye(4)) @ self.t_sc

    def record(self):
        from dataclasses import asdict
        data = asdict(self)
        focal_px = self.resolution[0] * self.focal_length_m / self.horizontal_aperture_m
        data.update(T_ES=pc.scanner_from_ee(np.eye(4)).tolist(), T_SC=self.t_sc.tolist(), T_EC=self.t_ec.tolist(),
                    focal_length_m=self.focal_length_m,
                    vertical_aperture_m=self.horizontal_aperture_m * self.resolution[1] / self.resolution[0],
                    expected_intrinsics_px=[[focal_px, 0, self.resolution[0]/2],
                                            [0, focal_px, self.resolution[1]/2], [0, 0, 1]],
                    calibration='virtual interface test only; not manufacturer data or hand-eye calibration',
                    world_axes='+X forward, +Z up', usd_axes='-Z forward, +Y up',
                    WORLD_TO_USD_AXES=WORLD_TO_USD_AXES.tolist(), distortion='none', depth_of_field=False)
        return data


def resolve_virtual_mount(derived_urdf):
    """Read only scanner visual vertices; apply scale and T_ES exactly once."""
    from _cr12_visual_source import _rotation
    path = Path(derived_urdf).resolve(strict=True)
    root = ET.fromstring(path.read_bytes())
    node = root.find("link[@name='link_6']/visual[@name='scanner_visual']")
    if node is None:
        raise ValueError('Accepted scanner visual metadata missing')
    mesh, origin = node.find('geometry/mesh'), node.find('origin')
    transform = np.eye(4)
    transform[:3, :3] = _rotation([float(x) for x in origin.get('rpy').split()])
    transform[:3, 3] = [float(x) for x in origin.get('xyz').split()]
    t_es = pc.scanner_from_ee(np.eye(4))
    if not np.allclose(transform, t_es, rtol=0, atol=1e-12):
        raise ValueError('Scanner source visual origin differs from accepted T_ES')
    scale = np.array([float(x) for x in mesh.get('scale').split()])
    if not np.array_equal(scale, np.full(3, .001)):
        raise ValueError('Unexpected scanner source units')
    mesh_path = (path.parent / mesh.get('filename')).resolve(strict=True)
    raw = mesh_path.read_bytes()
    points = []
    for line in raw.decode('utf-8-sig').splitlines():
        fields = line.split()
        if fields and fields[0] == 'v':
            if len(fields) != 4:
                raise ValueError('Unexpected scanner vertex format')
            points.append([float(x) for x in fields[1:]])
    points = np.asarray(points) * scale
    if not len(points) or not np.isfinite(points).all():
        raise ValueError('Invalid scanner visual vertices')
    points_e = points @ transform[:3, :3].T + transform[:3, 3]
    points_s = (points_e - t_es[:3, 3]) @ t_es[:3, :3]
    lo, hi = points_s.min(0), points_s.max(0)
    center = (lo + hi) / 2
    return VirtualCameraConfig((float(hi[0] + .02), float(center[1]), float(center[2])),
                               tuple(lo), tuple(hi), str(mesh_path), hashlib.sha256(raw).hexdigest())


def usd_camera_transform(world_style_transform):
    result = np.array(world_style_transform, copy=True)
    result[:3, :3] = result[:3, :3] @ WORLD_TO_USD_AXES
    return result


def nominal_fixture_pose(config, model, initial_root):
    initial_scanner = pc.scanner_from_ee(model.forward(np.zeros(6), initial_root)['link_6'])
    target = pc.FrozenPoseTarget(initial_scanner).target
    camera = target @ config.t_sc
    board = camera.copy()
    board[:3, 3] += camera[:3, 0] * .5
    return board


def _author_transform(prim, matrix):
    from pxr import Gf, UsdGeom
    xform = UsdGeom.Xformable(prim)
    xform.AddTransformOp().Set(Gf.Matrix4d(np.asarray(matrix).T.tolist()))
    if xform.GetResetXformStack():
        raise ValueError('New camera/fixture cannot reset the parent stack')


@dataclass(frozen=True)
class SharedFixture:
    stage: object
    path: str
    world_matrix: tuple


def shared_fixture_pose(config, scanner_target):
    import _cr12_shared_task_profile as shared
    target = pc._transform(scanner_target)
    if not np.array_equal(target, shared.scanner_target()):
        raise ValueError('Shared fixture must use the one frozen scanner task target')
    camera = target @ config.t_sc
    board = camera.copy()
    board[:3, 3] += camera[:3, 0] * .5
    return board


def create_shared_fixture(stage, config, scanner_target, *, fixture_path='/World/SharedTaskCameraFixture'):
    from pxr import UsdGeom
    import _cr12_shared_task_profile as shared
    if fixture_path != shared.SHARED_FIXTURE_PATH or stage.GetPrimAtPath(fixture_path).IsValid():
        raise ValueError('Shared fixture requires its new, fixed world prim path')
    if abs(UsdGeom.GetStageMetersPerUnit(stage) - 1.0) > 1e-12:
        raise ValueError('Shared fixture requires the accepted metre stage')
    matrix = shared_fixture_pose(config, scanner_target)
    _create_fixture(stage, fixture_path, matrix)
    return SharedFixture(stage, fixture_path, tuple(tuple(float(v) for v in row) for row in matrix))


def _validate_shared_fixture(stage, shared_fixture, config):
    from pxr import UsdGeom, UsdPhysics
    import _cr12_shared_task_profile as shared
    if not isinstance(shared_fixture, SharedFixture) or shared_fixture.stage is not stage:
        raise ValueError('Shared fixture must be the owned handle from this stage')
    expected = shared_fixture_pose(config, shared.scanner_target())
    if shared_fixture.path != shared.SHARED_FIXTURE_PATH or not np.array_equal(shared_fixture.world_matrix, expected):
        raise ValueError('Shared fixture handle differs from the frozen placement')
    prim = stage.GetPrimAtPath(shared_fixture.path)
    mesh = stage.GetPrimAtPath(shared_fixture.path + '/ColorPlate')
    if not prim.IsValid() or not mesh.IsValid() or not mesh.IsA(UsdGeom.Mesh):
        raise ValueError('Owned shared fixture or its plate is missing')
    transform = UsdGeom.Xformable(prim)
    if transform.GetResetXformStack() or not np.allclose(
            np.asarray(transform.GetLocalTransformation()).T, expected, rtol=0, atol=1e-12):
        raise ValueError('Shared fixture transform changed')
    for item in (prim, mesh):
        if any(item.HasAPI(schema) for schema in (UsdPhysics.MassAPI, UsdPhysics.RigidBodyAPI, UsdPhysics.CollisionAPI)) or item.IsA(UsdPhysics.Joint):
            raise ValueError('Shared fixture must remain nonphysical')
    return expected


def create_camera_and_fixture(stage, info, config, model, nominal_root, *,
                              fixture_path='/World/CameraInterfaceFixture', shared_fixture=None):
    from pxr import Gf, UsdGeom, UsdPhysics
    if abs(UsdGeom.GetStageMetersPerUnit(stage) - 1.0) > 1e-12:
        raise ValueError('Camera v1 requires the accepted metre stage')
    camera_path = info['body_paths']['link_6'] + '/SingleViewCamera'
    if (not isinstance(fixture_path, str) or not fixture_path.startswith('/World/')
            or fixture_path.endswith('/') or fixture_path == camera_path
            or fixture_path.startswith(info['body_paths']['link_6'] + '/')):
        raise ValueError('Fixture must have its own absolute world prim path')
    if shared_fixture is not None:
        fixture_pose = _validate_shared_fixture(stage, shared_fixture, config)
        fixture_path = shared_fixture.path
    elif stage.GetPrimAtPath(fixture_path).IsValid():
        raise ValueError('Fixture prim already exists')
    if stage.GetPrimAtPath(camera_path).IsValid():
        raise ValueError('Camera prim already exists')
    camera = UsdGeom.Camera.Define(stage, camera_path)
    _author_transform(camera.GetPrim(), usd_camera_transform(config.t_ec))
    camera.CreateProjectionAttr('perspective')
    # USD focal/aperture attributes are tenths of stage length units. The
    # installed Camera getters divide these authored values by ten.
    camera.CreateHorizontalApertureAttr(config.horizontal_aperture_m * 10)
    camera.CreateVerticalApertureAttr(config.horizontal_aperture_m * 10 * config.resolution[1] / config.resolution[0])
    camera.CreateFocalLengthAttr(config.focal_length_m * 10)
    camera.CreateClippingRangeAttr(Gf.Vec2f(config.near_m, config.far_m))
    camera.CreateFStopAttr(0.0)
    if shared_fixture is None:
        fixture_pose = nominal_fixture_pose(config, model, nominal_root)
        _create_fixture(stage, fixture_path, fixture_pose)
    if any(camera.GetPrim().HasAPI(schema) for schema in
           (UsdPhysics.MassAPI, UsdPhysics.RigidBodyAPI, UsdPhysics.CollisionAPI)):
        raise ValueError('Camera must remain nonphysical')
    return {'camera_prim': camera_path, 'fixture_prim': fixture_path,
            'fixture_world_matrix': fixture_pose.tolist(), 'fixture_size_m': [.2, .2],
            'fixture_source': ('shared frozen task camera pose; owned fixture reused'
                if shared_fixture is not None else 'one nominal final camera pose, authored once before physics'),
            'nonphysical': True, 'camera_world_pose_writes_during_run': 0}


def _create_fixture(stage, fixture_path, fixture_pose):
    from pxr import UsdGeom, UsdPhysics
    fixture = UsdGeom.Xform.Define(stage, fixture_path)
    _author_transform(fixture.GetPrim(), fixture_pose)
    # One double-sided, asymmetric four-face colour plate in local Y/Z.
    # The unequal split and distinct colours make camera axes readable.
    points, faces, colors = [], [], []
    for y0, y1, z0, z1, color in (
        (-.10, .02, -.10, -.025, (.05, .2, .9)),
        (.02, .10, -.10, -.025, (.05, .8, .12)),
        (-.10, .02, -.025, .10, (.95, .8, .04)),
        (.02, .10, -.025, .10, (.9, .04, .04)),
    ):
        start = len(points)
        points.extend(((0, y0, z0), (0, y1, z0), (0, y1, z1), (0, y0, z1)))
        faces.extend(range(start, start+4)); colors.append(color)
    mesh = UsdGeom.Mesh.Define(stage, fixture_path + '/ColorPlate')
    mesh.CreatePointsAttr(points)
    mesh.CreateFaceVertexCountsAttr([4]*4)
    mesh.CreateFaceVertexIndicesAttr(faces)
    mesh.CreateSubdivisionSchemeAttr('none')
    mesh.CreateDoubleSidedAttr(True)
    mesh.CreateDisplayColorPrimvar(UsdGeom.Tokens.uniform).Set(colors)
    for prim in (fixture.GetPrim(), mesh.GetPrim()):
        if any(prim.HasAPI(schema) for schema in (UsdPhysics.MassAPI, UsdPhysics.RigidBodyAPI, UsdPhysics.CollisionAPI)) or prim.IsA(UsdPhysics.Joint):
            raise ValueError('Camera/fixture must remain nonphysical')


def numpy_value(value):
    if hasattr(value, 'detach'):
        return value.detach().cpu().numpy()
    return np.asarray(value)


def read_optics(camera, config):
    intrinsic = numpy_value(camera.get_intrinsics_matrix())
    values = {'resolution': list(camera.get_resolution()), 'projection': camera.get_projection_type(),
              'focal_length_m': float(camera.get_focal_length()),
              'horizontal_aperture_m': float(camera.get_horizontal_aperture()),
              'vertical_aperture_m': float(camera.get_vertical_aperture()),
              'clipping_range_m': list(camera.get_clipping_range()), 'intrinsics_px': intrinsic.tolist(),
              'usd_raw': {name: camera.prim.GetAttribute(name).Get() for name in
                          ('focalLength', 'horizontalAperture', 'verticalAperture', 'fStop')}}
    if (values['resolution'] != list(config.resolution) or values['projection'] != 'pinhole'
            or not np.allclose(intrinsic, config.record()['expected_intrinsics_px'], rtol=1e-6, atol=1e-5)
            or not np.allclose(values['clipping_range_m'], [config.near_m, config.far_m], rtol=1e-6, atol=1e-7)):
        raise ValueError('Camera optics readback differs from frozen virtual configuration')
    return values


def actual_camera_pose(camera, actual_link_pose, config, *, clock, phase, require_match=True):
    """Independent installed camera/Fabric read vs native link composition.

    Called at an explicitly recorded publication/render boundary; this function
    never advances Fabric. This is a read-time pose, not an exposure pose.
    """
    import usdrt
    from isaacsim.core.utils.prims import get_prim_at_path
    position, orientation = camera.get_world_pose(camera_axes='world')
    actual = pc.pose_from_wxyz(numpy_value(position), numpy_value(orientation))
    expected = np.asarray(actual_link_pose) @ config.t_ec
    distance, angle = pc.pose_error(actual, expected)
    lineage = []
    path = camera.prim_path
    for _ in range(4):
        prim = get_prim_at_path(path, fabric=True)
        xform = usdrt.Rt.Xformable(prim)
        lineage.append({'prim': path, 'fabric_world': bool(xform.HasWorldXform()),
                        'fabric_local': bool(xform.HasLocalXform())})
        if xform.HasWorldXform():
            break
        path = path.rsplit('/', 1)[0]
    if not any(row['fabric_world'] for row in lineage):
        raise ValueError('No actual Fabric world transform in camera mount lineage')
    matched = distance <= 1e-4 and angle <= 1e-4
    if require_match and not matched:
        raise ValueError(f'Camera actual mount mismatch: {distance} m, {angle} rad')
    return {'phase': phase, 'physics_clock': list(clock), 'actual_world_style_matrix': actual.tolist(),
            'expected_native_link_composition': expected.tolist(), 'position_error_m': distance,
            'orientation_error_rad': angle, 'source': 'Camera.get_world_pose(world) -> installed Fabric-aware xforms',
            'time_semantics': ('initialization read before/after the recorded non-rendering Fabric publication; not exposure pose'
                if phase.startswith('initial_') else
                'read after normal render at recorded simulation clock; not precise exposure pose'),
            'fabric_lineage': lineage, 'pass': matched}


def read_local_mount(camera, config):
    from pxr import UsdGeom
    local = UsdGeom.Xformable(camera.prim)
    matrix = np.asarray(local.GetLocalTransformation()).T
    expected = usd_camera_transform(config.t_ec)
    if local.GetResetXformStack() or not np.allclose(matrix, expected, rtol=0, atol=1e-6):
        raise ValueError('Camera authored local mounting differs from frozen T_EC/optical conversion')
    return {'actual_local_usd_matrix': matrix.tolist(), 'expected_local_usd_matrix': expected.tolist(),
            'reset_xform_stack': False, 'pass': True}
