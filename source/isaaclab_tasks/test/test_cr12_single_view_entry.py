"""CPU entry boundaries only: fake lifecycle, no App, torch, CUDA or render."""
from __future__ import annotations

import ast
from contextlib import ExitStack
import copy
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'scripts/environments'))
import run_cr12_single_view_capture as entry
import run_cr12_pose_target as old_pose


class FakeLauncher:
    @staticmethod
    def add_app_launcher_args(parser):
        parser.add_argument('--device', default='cuda:0')
        parser.add_argument('--headless', action='store_true')
        parser.add_argument('--enable_cameras', action='store_true')
        parser.add_argument('--livestream', type=int, default=-1)
        parser.add_argument('--xr', action='store_true')
        parser.add_argument('--kit_args', default='')
        parser.add_argument('--info', action='store_true')

    def __init__(self, *_args, **_kwargs):
        raise AssertionError('CPU tests must never construct an App')


class SingleViewEntryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='cr12_capture_entry_cpu_')
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name).resolve()
        self.private = self.output / 'private_config/user.config.json'
        self.private.parent.mkdir()
        self.private.write_text(json.dumps({'persistent': {'app': {'window': {
            'width': 1440, 'height': 900, 'maximized': False}}}}), encoding='utf-8')
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict('os.environ', {
            'HEADLESS': '0', 'ENABLE_CAMERAS': '1', 'LIVESTREAM': '0', 'XR': '0'}))
        self.stack.enter_context(patch('sys.stderr', new_callable=io.StringIO))

    def argv(self):
        return ['--usd-path', str(entry.APPROVED_USD), '--output-dir', str(self.output),
                '--device', 'cuda:0', '--external-forces-every-iteration', 'on',
                '--enable_cameras', '--info', '--kit_args=--/app/userConfigPath=' + self.private.as_posix()]

    def test_camera_cli_and_fixed_formal_defaults(self):
        args = entry.parse_args(FakeLauncher, self.argv())
        self.assertTrue(args.enable_cameras)
        self.assertEqual(args.private_user_config, str(self.private))
        self.assertEqual(args.external_forces_source, 'explicit_cli')
        self.assertEqual((args.motion_profile, args.physics_steps, args.pd_profile), ('formal', 960, 'baseline'))
        self.assertFalse(args.visual_debug_pose)
        self.assertFalse(args.manual_check)
        self.assertTrue(entry.parse_args(FakeLauncher, self.argv()+['--manual-check']).manual_check)

    def test_requires_camera_gui_and_explicit_on(self):
        without_camera = [x for x in self.argv() if x != '--enable_cameras']
        variants = [without_camera] + [self.argv()+extra for extra in (
            ['--device', 'cpu'], ['--headless'], ['--livestream', '1'], ['--xr'],
            ['--external-forces-every-iteration', 'inherit'])]
        for argv in variants:
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                entry.parse_args(FakeLauncher, argv)
        with patch.dict('os.environ', {'ENABLE_CAMERAS': '0'}), self.assertRaises(SystemExit):
            entry.parse_args(FakeLauncher, self.argv())

    def test_private_required_and_bound_to_own_output(self):
        variants = [self.argv()[:-1], self.argv()[:-1]+['--kit_args=--/app/userConfigPath=' + str(self.output/'other.json')]]
        wrong_output = self.argv()
        wrong_output[wrong_output.index('--output-dir')+1] = str(self.output/'other_attempt')
        variants.append(wrong_output)
        for argv in variants:
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                entry.parse_args(FakeLauncher, argv)

    def test_no_controller_or_budget_override(self):
        for extra in (['--physics_steps', '1800'], ['--motion-profile', 'manual_visible_local_v1'],
                      ['--pd-profile', 'hold_tune_01'], ['--visual-debug-pose']):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                entry.parse_args(FakeLauncher, self.argv()+extra)

    def test_old_entry_still_default_no_camera_and_noncontinuing(self):
        argv = [value for value in self.argv()[:-1] if value != '--enable_cameras']
        with patch.dict('os.environ', {'ENABLE_CAMERAS': '0'}), patch.object(sys, 'argv', ['old_pose']+argv):
            args = old_pose.parse_args(FakeLauncher)
        self.assertFalse(args.enable_cameras)
        self.assertEqual((args.motion_profile, args.physics_steps, args.pd_profile), ('formal', 960, 'baseline'))
        parameters = inspect.signature(old_pose._pose_ticks).parameters
        self.assertIs(parameters['continue_after_arrival'].default, False)
        self.assertIsNone(parameters['before_render'].default)

    def test_existing_result_is_not_overwritten_on_failure(self):
        result = self.output/'result.json'
        original = b'{"preserve_prior_evidence": true}\n'
        result.write_bytes(original)
        app_module = types.ModuleType('isaaclab.app')
        app_module.AppLauncher = FakeLauncher
        package = types.ModuleType('isaaclab'); package.__path__ = []
        package.app = app_module
        args = entry.parse_args(FakeLauncher, self.argv())
        with patch.dict(sys.modules, {'isaaclab': package, 'isaaclab.app': app_module}), \
                patch.object(entry, 'parse_args', return_value=args), patch.object(entry.Recorder, 'emit'):
            with self.assertRaises(FileExistsError):
                entry.main()
        self.assertEqual(result.read_bytes(), original)

    def test_phase_event_preserves_actual_receive_time(self):
        recorder = entry.Recorder()
        with patch.object(recorder, 'emit') as emit:
            entry.phase_saved(recorder, 'data_received', wall_time_s=123.5, count=1)
        self.assertEqual(emit.call_args.kwargs['wall_time_s'], 123.5)
        self.assertEqual(recorder.result['phase_order'], ['data_received'])

    def test_cleanup_primary_failure_is_not_replaced(self):
        recorder = entry.Recorder()
        first, second = ValueError('first failure'), OSError('close failure')
        with patch.object(recorder, 'emit'):
            self.assertIs(entry.cleanup_failure(recorder, first, 'capture', None), first)
            self.assertIs(entry.cleanup_failure(recorder, second, 'close', first), first)
        self.assertEqual(recorder.result['failures'][0]['message'], 'first failure')
        self.assertEqual(recorder.result['secondary_failures'][0]['message'], 'close failure')

    def test_app_close_attempted_even_if_close_event_save_fails(self):
        # Execute the actual final close branch in isolation with fake resources.
        tree = ast.parse(Path(entry.__file__).read_text(encoding='utf-8'))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        outer = next(node for node in main.body if isinstance(node, ast.Try))
        close_branch = next(node for node in outer.finalbody if isinstance(node, ast.If)
                            and ast.unparse(node.test) == 'app is not None')
        code = compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(close_branch)], type_ignores=[])),
                       '<real-close-branch-with-fakes>', 'exec')
        app, recorder = Mock(), entry.Recorder()
        primary = ValueError('capture failure')
        with patch.object(recorder, 'emit'):
            context = {'app': app, 'recorder': recorder, 'failure': primary,
                       'phase_saved': Mock(side_effect=OSError('event save failed')),
                       'cleanup_failure': entry.cleanup_failure}
            exec(code, context)
        app.close.assert_called_once_with()
        self.assertIs(context['failure'], primary)

    def test_finally_has_no_native_read_or_visual_reapply(self):
        tree = ast.parse(Path(entry.__file__).read_text(encoding='utf-8'))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        outer = next(node for node in main.body if isinstance(node, ast.Try))
        forbidden = {'native_validity', '_read_physics', 'actual_camera_pose', 'get_masses',
                     'get_dof_positions', 'get_dof_velocities', 'step', 'render', 'reset', 'revoke', 'apply'}
        names = {call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, 'id', '')
                 for statement in outer.finalbody for call in ast.walk(statement) if isinstance(call, ast.Call)}
        self.assertFalse(names & forbidden)

    def test_native_guard_rejects_stopped_or_missing_view(self):
        root = types.SimpleNamespace(check=Mock(return_value=True))
        view = types.SimpleNamespace(is_valid=True, check=Mock(return_value=True))
        robot = types.SimpleNamespace(is_initialized=True, _root_physx_view=root)
        sim = types.SimpleNamespace(physics_sim_view=view, is_playing=lambda: True)
        self.assertTrue(all(entry.native_validity(robot, sim).values()))
        for missing, playing in ((True, True), (False, False)):
            sim.physics_sim_view = None if missing else view
            sim.is_playing = lambda: playing
            root.check.reset_mock(); view.check.reset_mock()
            with self.subTest(missing=missing, playing=playing), self.assertRaises(entry.DriveCheckError):
                entry.native_validity(robot, sim)
            root.check.assert_not_called(); view.check.assert_not_called()

    def test_camera_and_visual_preinit_once_before_reset_then_initialize_off(self):
        import _cr12_camera_mount as mount
        import _cr12_camera_capture as capture_module
        import _cr12_pose_control as pc
        import _cr12_visual_geometry as visual
        events, context, resources = [], {'clock': 0}, {}
        recorder = entry.Recorder()
        recorder.result['simulation'] = {}
        recorder.result['initialization'] = {}
        resources['app_update_counter'] = {'count': 0}
        sim = types.SimpleNamespace(physics_sim_view=None, current_time_step_index=0, current_time=0.,
            is_simulating=lambda: False, is_playing=lambda: False, is_stopped=lambda: True)
        robot = types.SimpleNamespace(is_initialized=False, _root_physx_view=None)
        stage = object()
        scene = {'sim': sim, 'robot': robot, 'stage': stage}
        override = Mock()
        override.apply.side_effect = lambda **kw: events.append('apply_preinit') or {}
        override.seal_before_physics_initialization.side_effect = lambda: events.append('seal')
        override.verify_stable.return_value = {'pass': True}
        capture = Mock(product_path='/SyntheticOwnedProduct', unsafe=True)
        capture.assert_off.side_effect = lambda phase: events.append('off:'+phase)
        capture.initialize_off.side_effect = lambda **kw: events.append('camera_initialize_off')
        captured_context = []
        def prepare(*args, **kwargs):
            events.append('prepare_camera_off')
            captured_context.append(kwargs['context_provider'])
            return capture
        def create(*args, pre_physics, before_native_read):
            pre_physics(stage=stage, sim=sim, robot=robot, info={})
            events.append('first_reset')
            sim.current_time_step_index = 2; sim.current_time = 2/120
            sim.physics_sim_view = types.SimpleNamespace(is_valid=True, check=lambda: True)
            sim.is_playing = lambda: True
            robot.is_initialized = True
            robot._root_physx_view = types.SimpleNamespace(check=lambda: True)
            before_native_read(robot=robot, sim=sim)
            return scene
        def initialize(*args):
            events.append('initialize_robot_state')
            return {'baseline': (2, 2/120)}
        omni = types.ModuleType('omni'); omni.__path__ = []
        physx, timeline = types.ModuleType('omni.physx'), types.ModuleType('omni.timeline')
        physx.get_physx_interface = lambda: types.SimpleNamespace(is_running=lambda: False)
        physx.get_physx_simulation_interface = lambda: types.SimpleNamespace(get_attached_stage=lambda: 0)
        omni.physx, omni.timeline = physx, timeline
        args = types.SimpleNamespace(usd_path=entry.APPROVED_USD)
        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, {'omni': omni, 'omni.physx': physx, 'omni.timeline': timeline}))
            stack.enter_context(patch.object(pc.KinematicModel, 'from_derived_urdf', return_value=object()))
            stack.enter_context(patch.object(mount, 'create_camera_and_fixture', return_value={'camera_prim': '/SyntheticCamera'}))
            stack.enter_context(patch.object(visual, 'inspect_preinit_mapping', return_value={'pass': True}))
            stack.enter_context(patch.object(visual, 'physical_snapshot', return_value={'physical': 'unchanged'}))
            stack.enter_context(patch.object(visual, 'CollisionVisualOverride', return_value=override))
            stack.enter_context(patch.object(capture_module.OwnedCameraCapture, 'prepare', side_effect=prepare))
            stack.enter_context(patch.object(entry, 'create_fixed_cr12_scene', side_effect=create))
            stack.enter_context(patch.object(entry, 'initialize_fixed_cr12_state', side_effect=initialize))
            stack.enter_context(patch.object(recorder, 'emit'))
            actual, initial = entry.prepare_scene(args, object(), recorder, resources, {},
                                                 types.SimpleNamespace(resolution=(640, 480)), context)
        self.assertIs(actual, scene)
        self.assertEqual(initial['baseline'], (2, 2/120))
        self.assertEqual(events, ['apply_preinit', 'seal', 'prepare_camera_off', 'off:pre_physics_prepared',
            'first_reset', 'initialize_robot_state', 'camera_initialize_off', 'off:initialized_before_motion'])
        override.apply.assert_called_once_with(before_first_physics_initialization=True)
        override.revoke.assert_not_called()
        capture.initialize_off.assert_called_once_with(physics_sim_view=sim.physics_sim_view)
        self.assertEqual(recorder.result['camera_prepare_clock']['before'], recorder.result['camera_prepare_clock']['after'])
        self.assertEqual(recorder.result['camera_initialize_clock']['before'], recorder.result['camera_initialize_clock']['after'])
        self.assertEqual(recorder.result['initialization']['app_update_events_before_motion'], 0)
        copied = captured_context[0](); context['clock'] = 5
        self.assertEqual(copied, {'clock': 0})

    def test_real_request_orchestration_with_fake_ticks_keeps_data_save_off_separate(self):
        import numpy as np
        import _cr12_camera_mount as mount
        import _cr12_external_forces as forces
        recorder, resources, events = entry.Recorder(), {}, []
        counts = {name: 0 for name in ('clock', 'joint', 'contact', 'geometry', 'frame', 'render_clock')}
        recorder.result.update(physx_readback={'mass': 'unchanged'}, pose_summary={'guard_pass_counts': counts},
            camera_mount={'camera_prim': '/SyntheticCamera'}, visual_preinit={'stage_checks': []})
        sim = types.SimpleNamespace(current_time_step_index=2, current_time=2/120)
        scene = {'sim': sim, 'robot': object(), 'configuration': {}, 'selected_pd': {},
                 'stage': object(), 'setup': {}, 'physx_schema': object(), 'usd_physics': object(), 'default_time': None}
        initial = {'poses': {'link_6': np.eye(4)}, 'baseline': (2, 2/120)}
        class FakeCapture:
            product_path = '/SyntheticOwnedProduct'
            camera = object()
            enabled = False
            ids = None
            request = None
            event_count = 0
            opportunities = 0
            def assert_off(self, phase):
                if self.enabled:
                    raise AssertionError('expected disabled product')
                return {'updates_enabled': False}
            def read_updates_enabled(self): return self.enabled
            def summary(self): return {'product_event_count': self.event_count, 'request': copy.deepcopy(self.request)}
            def begin_capture(self, ids, boundary):
                self.ids = ids; self.enabled = True; events.append('on')
                self.request = {**copy.deepcopy(ids), 'boundary': copy.deepcopy(boundary)}
                return {'actual': True}
            def poll_snapshot(self):
                if sim.current_time_step_index % 2:
                    return None
                self.event_count = 1
                return {'rgba': np.zeros((480, 640, 4), dtype=np.uint8), 'metadata': {
                    **self.ids, 'render_product_path': self.product_path, 'fresh': True,
                    'rendering_frame': 42, 'source_time': sim.current_time, 'received_wall_time': 123.5}}
            def request_off(self, boundary):
                self.enabled = False; events.append('off')
            def observe_close(self, render_opportunity):
                self.opportunities += int(render_opportunity)
                return {'confirmed': self.opportunities >= 30, 'updates_enabled': False,
                    'opportunity_count': self.opportunities, 'quiet_opportunities': self.opportunities,
                    'independent_observer_active': True}
            def release(self):
                events.append('release')
                return {'complete': True, 'errors': []}
        capture = FakeCapture()
        resources.update(capture=capture, sim=sim, visual_override=Mock())
        resources['visual_override'].verify_stable.return_value = {'pass': True}
        def ticks(*args, **kwargs):
            self.assertIs(kwargs['continue_after_arrival'], True)
            for step in range(1, 1801):
                sim.current_time_step_index = step+2; sim.current_time = (step+2)/120
                recorder.result['completed_physics_steps'] = step
                for name in counts: counts[name] += 1
                sample = {'target_position_error_m': .001, 'target_orientation_error_rad': .001,
                          'stable_samples': 121 if step >= 600 else 0, 'stable_span_s': 1. if step >= 600 else 0.}
                tick = {'step': step, 'physics_time_s': sim.current_time, 'controlled_time_s': step/120,
                    'poses': {'link_6': np.eye(4)}, 'scanner': np.eye(4), 'dq': np.zeros(6),
                    'pose_reached': step >= 600, 'rendered': step % 2 == 0, 'sample': sample}
                if tick['rendered']: kwargs['before_render'](tick)
                yield tick
        config = types.SimpleNamespace(record=lambda: {'name': 'synthetic_virtual'})
        args = types.SimpleNamespace(output_dir=self.output)
        with ExitStack() as stack:
            stack.enter_context(patch.object(entry, 'prepare_scene', return_value=(scene, initial)))
            stack.enter_context(patch.object(entry, 'native_validity', return_value={'valid': True}))
            stack.enter_context(patch.object(entry, 'refresh_initial_camera_publication',
                return_value={'position_error_m': 0., 'orientation_error_rad': 0.}))
            stack.enter_context(patch.object(entry, '_read_physics', side_effect=lambda *args: events.append('native_final') or ([], [], {'mass': 'unchanged'})))
            stack.enter_context(patch.object(mount, 'read_optics', return_value={}))
            stack.enter_context(patch.object(mount, 'actual_camera_pose', return_value={'position_error_m': 0., 'orientation_error_rad': 0.}))
            stack.enter_context(patch.object(forces, 'read_scene_external_forces'))
            stack.enter_context(patch.object(old_pose, '_pose_ticks', side_effect=ticks))
            emit = stack.enter_context(patch.object(recorder, 'emit'))
            entry.run_capture(args, object(), recorder, resources, {'bodies': {}}, config)
        self.assertEqual(recorder.result['stage_counts'], {
            'pose_steps': 600, 'capture_steps': 2, 'close_steps': 60, 'total_controlled_steps': 662,
            'fsm_observed_steps': 662, 'unaccepted_poststep_count': 0})
        self.assertEqual(recorder.result['capture_summary']['state'], 'SUCCEEDED_OFF')
        self.assertEqual(events, ['on', 'off', 'native_final', 'release'])
        self.assertTrue(all(recorder.result['capture_summary'][k] for k in ('acquired', 'saved', 'confirmed_off')))
        self.assertEqual(recorder.result['off_confirmation']['render_opportunities'], 30)
        self.assertEqual([row.args[0] for row in emit.call_args_list],
                         ['pose_reached', 'capture_on', 'data_received', 'capture_off_requested', 'capture_off_confirmed'])
        self.assertTrue((self.output/'camera_rgba.png').is_file())
        metadata = json.loads((self.output/'capture_metadata.json').read_text(encoding='utf-8'))
        self.assertEqual(metadata['product_path'], capture.product_path)
        self.assertEqual(metadata['attempt_id'], self.output.name)


if __name__ == '__main__':
    unittest.main()
