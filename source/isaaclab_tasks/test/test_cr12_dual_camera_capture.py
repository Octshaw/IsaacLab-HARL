"""Two camera owners and common setup tested on CPU; no rendering evidence."""
import ast
import copy
from contextlib import ExitStack
from fractions import Fraction
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/environments'))
import _cr12_camera_capture as camera
import _cr12_camera_mount as mount
import _cr12_runtime_support as support
import run_cr12_single_view_capture as entry
from test_cr12_camera_capture import Stream, event, runtime_fixture
from test_cr12_single_view_integration import FakeRecorder


def specs():
    rows = []
    for i in range(2):
        pose = np.eye(4); pose[:3, 3] = (0., i*2., .053)
        rows.append(dict(robot_id=i, prim_path=f'/World/CR12_{i}', expected_root_pose=pose,
            fixture_path=f'/World/CameraInterfaceFixture_R{i}', product_name=f'CR12_R{i}_Capture',
            camera_name=f'cr12_r{i}_camera', observer_name=f'cr12.r{i}.independent_completion'))
    return rows


class DualCameraTests(unittest.TestCase):
    def setUp(self):
        self.stream, self.products, self.targets = Stream(), {}, {}
        self.runtimes, self.owners, self.contexts = [], [], []
        for row in specs():
            i = row['robot_id']
            runtime = runtime_fixture()
            runtime.stream = self.stream
            runtime.context = SimpleNamespace(get_rendering_event_stream=lambda: self.stream, get_stage_id=lambda: 7)
            runtime.product_path_for_name = lambda name: '/Render/RP_' + name
            runtime.prim_exists = lambda path: path in self.products
            runtime.product_camera_targets = lambda path: self.targets.get(path, [])
            runtime.product.path = runtime.product_path_for_name(row['product_name'])
            original = runtime.create_product
            def create(path, resolution, force_new, name, *, _original=original):
                product = _original(path, resolution, force_new, name)
                self.products[product.path] = product
                self.targets[product.path] = [path]
                return product
            runtime.create_product = create
            context = dict(robot_id=i, actual_pose=[i, 2*i, .053])
            owner = camera.OwnedCameraCapture.prepare(row['prim_path']+'/link_6/SingleViewCamera', (4, 3),
                lambda context=context: context, runtime=runtime, max_requests=2, integration_mode=True,
                **{key: row[key] for key in ('product_name', 'camera_name', 'observer_name')})
            owner.initialize_off()
            self.runtimes.append(runtime); self.owners.append(owner); self.contexts.append(context)

    def tearDown(self):
        for owner in self.owners:
            owner.release()

    def begin(self, index):
        self.owners[index].begin_capture(dict(goal_id=f'g{index}', attempt_id='a', capture_id=f'c{index}',
            env_id=0, robot_id=index, task_id=2*index, claim_token=f'claim{index}',
            episode_generation=0, run_instance_id='run'), {})

    def emit(self, index, frame=101, source=Fraction(51, 10)):
        self.stream.emit(event(self.owners[index].product_path, frame, source))

    def test_two_named_products_and_all_device_resources_are_independent(self):
        record = camera.verify_camera_isolation(self.owners)
        self.assertTrue(record['pass'])
        for index, (owner, runtime) in enumerate(zip(self.owners, self.runtimes)):
            self.assertEqual(runtime.log[0][4], f'CR12_R{index}_Capture')
            self.assertTrue(runtime.log[0][3])
            self.assertEqual(runtime.log[1], ('updates', False))
            self.assertEqual(owner._observer.name, f'cr12.r{index}.independent_completion')
            self.assertEqual(owner.summary()['resource_names']['camera_name'], f'cr12_r{index}_camera')
            self.assertEqual(self.targets[owner.product_path], [owner.camera_prim_path])
            self.assertFalse(owner.read_updates_enabled())

    def test_existing_name_rejected_before_product_create(self):
        runtime = self.runtimes[0]; before = len(runtime.log)
        with self.assertRaisesRegex(camera.CameraCaptureError, 'already exists'):
            camera.OwnedCameraCapture.prepare('/Other', runtime=runtime, product_name='CR12_R0_Capture')
        self.assertEqual(len(runtime.log), before)

    def test_unexpected_suffix_and_wrong_camera_relationship_rejected(self):
        for suffix, targets in (('_01', ['/Other']), ('', ['/Wrong'])):
            runtime = runtime_fixture()
            runtime.product_path_for_name = lambda name: '/Render/Expected'
            runtime.prim_exists = lambda path: False
            runtime.product.path = '/Render/Expected' + suffix
            runtime.product_camera_targets = lambda path, targets=targets: targets
            with self.subTest(suffix=suffix, targets=targets), self.assertRaises(camera.CameraCaptureError):
                camera.OwnedCameraCapture.prepare('/Other', runtime=runtime, product_name='Named')
            self.assertFalse(runtime.product.hydra_texture.updates_enabled)
            self.assertEqual(runtime.product.destroy_count, 1)

    def test_same_global_frame_two_products_keeps_owned_source_context_and_buffers(self):
        for i in range(2):
            self.runtimes[i].pixels.fill(11 + 66*i)
            self.begin(i)
        self.emit(1); self.emit(0)  # Same time/frame, independent product events.
        snaps = [owner.poll_snapshot() for owner in self.owners]
        for i, snap in enumerate(snaps):
            self.assertEqual(snap['metadata']['rendering_frame'], 101)
            self.assertEqual(snap['metadata']['robot_id'], i)
            self.assertEqual(snap['metadata']['task_id'], 2*i)
            self.assertEqual(snap['metadata']['claim_token'], f'claim{i}')
            self.assertEqual(snap['metadata']['received_context']['robot_id'], i)
            self.assertTrue(np.all(snap['rgba'] == 11+66*i))
            self.assertFalse(snap['rgba'].flags.writeable)
            self.runtimes[i].pixels.fill(0)
            self.contexts[i]['actual_pose'][0] = -99
            self.assertEqual(snap['metadata']['received_context']['actual_pose'][0], i)
            self.assertTrue(np.all(snap['rgba'] == 11+66*i))
        self.assertFalse(np.shares_memory(snaps[0]['rgba'], snaps[1]['rgba']))
        self.assertEqual([o.summary()['unique_product_event_count'] for o in self.owners], [1, 1])

    def test_a_off_b_on_one_opportunity_per_shared_render_other_product_is_quiet(self):
        self.begin(0); self.begin(1); self.emit(0)
        self.runtimes[0].source_now = Fraction(52, 10)
        self.owners[0].request_off()
        for i in range(30):
            self.emit(1, 200+i, Fraction(53+i, 10))
            self.assertFalse(self.owners[0].observe_close(False)['confirmed'])
            evidence = self.owners[0].observe_close(True)
            self.assertEqual(evidence['opportunity_count'], i+1)
            self.assertEqual(evidence['quiet_opportunities'], i+1)
        self.assertTrue(evidence['confirmed'])
        a, b = [owner.render_evidence() for owner in self.owners]
        self.assertFalse(a['updates_enabled']); self.assertTrue(b['updates_enabled'])
        self.assertEqual(a['own_unique_completions'], 1)
        self.assertEqual(b['own_unique_completions'], 30)
        self.assertEqual(a['camera_updates'], 1)
        self.assertTrue(a['observer_active'])
        self.assertFalse(self.owners[0].summary()['errors'])

    def test_new_output_after_a_confirmed_off_invalidates_only_a(self):
        self.begin(0); self.begin(1); self.emit(0)
        self.owners[0].request_off()
        for _ in range(30): self.owners[0].observe_close()
        self.emit(0, 102)
        self.assertTrue(self.owners[0].summary()['errors'])
        self.emit(1, 103)
        self.assertIsNotNone(self.owners[1].poll_snapshot())
        self.assertFalse(self.owners[1].summary()['errors'])

    def test_releasing_a_does_not_pause_detach_or_disable_b(self):
        self.begin(1)
        identity = self.owners[1].device_identity()
        log = list(self.runtimes[1].log)
        self.owners[0].release()
        self.assertEqual(self.runtimes[1].log, log)
        self.assertTrue(self.owners[1].read_updates_enabled())
        self.emit(1)
        self.assertIsNotNone(self.owners[1].poll_snapshot())
        self.assertEqual(self.owners[1].device_identity(), identity)
        self.assertEqual(self.runtimes[1].product.destroy_count, 0)

    def test_render_evidence_copies_metadata_without_copying_or_mutating_rgba(self):
        self.begin(0); self.emit(0)
        snapshot = self.owners[0].poll_snapshot()
        log = list(self.runtimes[0].log)
        record = self.owners[0].render_evidence()
        self.assertNotIn('rgba', record)
        record['snapshot_source']['received_context']['robot_id'] = 99
        self.assertEqual(snapshot['metadata']['received_context']['robot_id'], 0)
        self.assertEqual(self.runtimes[0].log, log)

    def test_frame_dictionary_alias_is_rejected(self):
        self.owners[1].camera._current_frame = self.owners[0].camera._current_frame
        with self.assertRaisesRegex(camera.CameraCaptureError, 'dictionaries alias'):
            camera.verify_camera_isolation(self.owners)


class CommonPublicationTests(unittest.TestCase):
    def exercise(self, mutation=None):
        sim = SimpleNamespace(current_time_step_index=2, current_time=2/120)
        shared_counter, log, arrays, runs = {'count': 7}, [], [], []
        for i in range(2):
            values = [np.zeros((1, 6)), np.zeros((1, 6)), np.zeros((1, 7, 7))]
            arrays.append(values)
            def getter(index, values=values):
                return SimpleNamespace(clone=lambda: values[index].copy())
            view = SimpleNamespace(get_dof_positions=lambda getter=getter: getter(0),
                get_dof_velocities=lambda getter=getter: getter(1), get_link_transforms=lambda getter=getter: getter(2))
            robot = SimpleNamespace(root_physx_view=view)
            capture = SimpleNamespace(camera=i, assert_off=lambda phase, i=i: log.append((i, phase)))
            runs.append(dict(scene=dict(sim=sim, robot=robot), initial={'poses': {'link_6': np.eye(4)}},
                capture=capture, camera_config=object(), recorder=FakeRecorder(), resources={'app_update_counter': shared_counter}))
        def forward():
            log.append('forward')
            if mutation: mutation(arrays, sim, shared_counter)
        sim.forward = mock.Mock(side_effect=forward)
        sim.step = sim.render = mock.Mock(side_effect=AssertionError('No advancement'))
        def pose(camera, *args, phase, require_match=True, **kwargs):
            log.append((camera, phase, require_match))
            return dict(position_error_m=0., orientation_error_rad=0., **{'pass': require_match})
        with mock.patch.object(entry, 'native_validity'), mock.patch.object(mount, 'numpy_value', side_effect=lambda value: value), \
                mock.patch.object(mount, 'read_local_mount', return_value={'pass': True}), \
                mock.patch.object(mount, 'actual_camera_pose', side_effect=pose):
            try: result, error = entry.refresh_initial_camera_publications(runs), None
            except Exception as exc: result, error = None, exc
        sim.forward.assert_called_once_with(); sim.step.assert_not_called()
        return result, error, runs, log

    def test_both_snapshotted_before_one_forward_and_original_tolerances_after(self):
        result, error, runs, log = self.exercise()
        self.assertIsNone(error); self.assertEqual(len(result), 2)
        self.assertLess(log.index((1, 'initial_before_fabric_publication', False)), log.index('forward'))
        self.assertGreater(log.index((0, 'initial_after_fabric_publication', True)), log.index('forward'))
        for run in runs:
            record = run['recorder'].result['initial_fabric_publication']
            self.assertTrue(record['pass_']); self.assertEqual(record['native_arrays_equal'], [True]*3)
            self.assertEqual(record['shared_instance_count'], 2)

    def test_any_instance_native_or_common_clock_mutation_rejected(self):
        for mutation in (lambda a, s, c: a[1][2].__setitem__((0, 0, 0), 1.),
                         lambda a, s, c: c.update(count=8),
                         lambda a, s, c: setattr(s, 'current_time_step_index', 3)):
            with self.subTest(mutation=mutation):
                result, error, runs, log = self.exercise(mutation)
                self.assertIsNone(result); self.assertEqual(error.category, 'physical_invariance')
                self.assertFalse(any('pass_' in r['recorder'].result['initial_fabric_publication'] for r in runs))

    def test_wrong_independent_layout_duplicate_or_invalid_identity_rejected(self):
        for mutation in (lambda values: values[1]['expected_root_pose'].__setitem__((1, 3), 0.),
                         lambda values: values[1].update(robot_id=0),
                         lambda values: values[1].update(robot_id=2),
                         lambda values: values[1].update(robot_id=True),
                         lambda values: values[1].update(product_name='CR12_R0_Capture')):
            values = specs(); mutation(values)
            with self.assertRaises(entry.DriveCheckError): entry._validated_dual_specs(values)
        for values in (specs(), specs()[::-1]):
            checked = entry._validated_dual_specs(values)
            self.assertEqual([item['robot_id'] for item in checked], [item['robot_id'] for item in values])
            for item in checked:
                self.assertEqual(item['expected_root_pose'][1, 3], 2.*item['robot_id'])


class DualPreparationTests(unittest.TestCase):
    def test_fixture_collision_is_rejected_before_any_camera_definition(self):
        define = mock.Mock(side_effect=AssertionError('Must not author camera on fixture collision'))
        geom = SimpleNamespace(GetStageMetersPerUnit=lambda stage: 1., Camera=SimpleNamespace(Define=define))
        stage = SimpleNamespace(GetPrimAtPath=lambda path: SimpleNamespace(IsValid=lambda: True))
        with mock.patch.dict(sys.modules, {'pxr': SimpleNamespace(Gf=object(), UsdGeom=geom, UsdPhysics=object())}):
            with self.assertRaisesRegex(ValueError, 'Fixture prim already exists'):
                mount.create_camera_and_fixture(stage, {'body_paths': {'link_6': '/World/CR12_1/link_6'}},
                    object(), object(), np.eye(4), fixture_path='/World/CameraInterfaceFixture_R1')
        define.assert_not_called()

    def test_actual_preinit_hook_factories_bind_separate_cached_context_and_names(self):
        import _cr12_pose_control as pc
        import _cr12_visual_geometry as visual
        omni = ModuleType('omni'); omni.__path__ = []
        physx = ModuleType('omni.physx'); omni.physx = physx
        physx.get_physx_interface = lambda: SimpleNamespace(is_running=lambda: False)
        physx.get_physx_simulation_interface = lambda: SimpleNamespace(get_attached_stage=lambda: 0)
        sim = SimpleNamespace(physics_sim_view=None, current_time_step_index=0, current_time=0.,
            is_simulating=lambda: False, is_playing=lambda: False, is_stopped=lambda: True)
        robot = SimpleNamespace(is_initialized=False, _root_physx_view=None)
        contexts, providers = [], []
        def prepare(path, **kwargs):
            providers.append(kwargs['context_provider'])
            return SimpleNamespace(product_path='/Render/'+kwargs['product_name'], assert_off=lambda phase: None)
        with ExitStack() as stack:
            stack.enter_context(mock.patch.dict(sys.modules, {'omni': omni, 'omni.physx': physx}))
            stack.enter_context(mock.patch.object(pc.KinematicModel, 'from_derived_urdf', return_value=object()))
            mounted = stack.enter_context(mock.patch.object(mount, 'create_camera_and_fixture', return_value={'camera_prim': '/FakeCamera'}))
            stack.enter_context(mock.patch.object(visual, 'inspect_preinit_mapping', return_value={'pass': True}))
            stack.enter_context(mock.patch.object(visual, 'physical_snapshot', return_value={}))
            overlay = stack.enter_context(mock.patch.object(visual, 'CollisionVisualOverride'))
            prepared = stack.enter_context(mock.patch.object(camera.OwnedCameraCapture, 'prepare', side_effect=prepare))
            for row in specs():
                context = {'robot_id': row['robot_id']}; contexts.append(context)
                hook = entry._make_camera_pre_physics(SimpleNamespace(usd_path=entry.APPROVED_USD), FakeRecorder(), {},
                    SimpleNamespace(resolution=(640, 480)), context, prim_path=row['prim_path'],
                    nominal_root=row['expected_root_pose'], fixture_path=row['fixture_path'],
                    resource_names={key: row[key] for key in ('product_name', 'camera_name', 'observer_name')},
                    camera_request_limit=2, camera_integration=True, defer_visual_seal=True)
                hook(stage=object(), sim=sim, robot=robot, info={})
            overlay.return_value.seal_before_physics_initialization.assert_not_called()
            self.assertEqual([call.kwargs['fixture_path'] for call in mounted.call_args_list],
                ['/World/CameraInterfaceFixture_R0', '/World/CameraInterfaceFixture_R1'])
            self.assertEqual([call.kwargs['product_name'] for call in prepared.call_args_list],
                ['CR12_R0_Capture', 'CR12_R1_Capture'])
        self.assertEqual([provider()['robot_id'] for provider in providers], [0, 1])
        copied = providers[0](); contexts[0]['robot_id'] = 99
        self.assertEqual(copied['robot_id'], 0); self.assertEqual(providers[1]()['robot_id'], 1)

    def _exercise_shared_preparation(self, creation_order):
        order, rec, resources = [], FakeRecorder(), {'app_update_counter': {'count': 0}, 'external_forces_context': ()}
        rec.result['pd_selection'] = {'stiffness': [1]*6, 'damping': [1]*6}
        sim = SimpleNamespace(set_camera_view=lambda **kwargs: order.append('spectator'), current_time_step_index=2, current_time=2/120)
        world = {'sim': sim}
        def hook_factory(args, recorder, local, config, context, **kwargs):
            i = recorder.robot_id
            self.assertTrue(kwargs['defer_visual_seal']); self.assertTrue(kwargs['camera_integration'])
            self.assertEqual(kwargs['nominal_root'][1, 3], 2*i)
            local['visual_override'] = SimpleNamespace(seal_before_physics_initialization=lambda: order.append(('seal', i)),
                verify_stable=lambda phase: {'pass': True})
            local['capture'] = SimpleNamespace(camera=i, product_path=f'/Product{i}', assert_off=lambda phase: None)
            recorder.result['visual_preinit'] = {'stage_checks': []}
            order.append(('preinit', i))
            return object()
        def spawn(args, app, recorder, local, expected, **kwargs):
            return dict(sim=sim, robot=object(), resources=local, recorder=recorder, prim_path=kwargs['prim_path'])
        def contacts(scene, local, *, other_instances):
            self.assertEqual(len(other_instances), 1); order.append(('contacts', scene['recorder'].robot_id))
        def read(scene, recorder, expected, **kwargs):
            recorder.result['physx_readback'] = {'robot_id': recorder.robot_id}
        def state(args, recorder, scene):
            order.append(('state', recorder.robot_id)); return {'poses': {}, 'baseline': (2, 2/120)}
        def initialize(scene, recorder, local): order.append(('camera_initialize', recorder.robot_id))
        def publish(runs):
            order.append('forward')
            return ({'position_error_m': 0., 'orientation_error_rad': 0.},)*2
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(support, 'create_fixed_cr12_world', return_value=world))
            stack.enter_context(mock.patch.object(support, 'spawn_fixed_cr12_instance', side_effect=spawn))
            stack.enter_context(mock.patch.object(support, 'prepare_fixed_cr12_contacts', side_effect=contacts))
            reset = stack.enter_context(mock.patch.object(support, 'reset_fixed_cr12_world', side_effect=lambda *a: order.append('reset')))
            stack.enter_context(mock.patch.object(support, 'read_fixed_cr12_instance', side_effect=read))
            stack.enter_context(mock.patch.object(entry, '_make_camera_pre_physics', side_effect=hook_factory))
            stack.enter_context(mock.patch.object(entry, 'initialize_fixed_cr12_state', side_effect=state))
            stack.enter_context(mock.patch.object(entry, '_initialize_camera_off', side_effect=initialize))
            stack.enter_context(mock.patch.object(entry, 'refresh_initial_camera_publications', side_effect=publish))
            stack.enter_context(mock.patch.object(mount, 'read_optics', return_value={}))
            stack.enter_context(mock.patch.object(camera, 'verify_camera_isolation', return_value={'pass': True}))
            runs = entry.initialize_dual_capture_runs(object(), object(), rec, resources, {}, object(),
                [specs()[i] for i in creation_order])
        reset.assert_called_once()
        self.assertEqual(order, [(phase, i) for phase in ('preinit', 'contacts', 'seal') for i in creation_order]
            + ['spectator', 'reset'] + [(phase, i) for phase in ('state', 'camera_initialize') for i in creation_order]
            + ['forward'])
        self.assertIsNot(runs[0]['recorder'], runs[1]['recorder'])
        self.assertIsNot(runs[0]['resources'], runs[1]['resources'])
        self.assertIsNot(runs[0]['receive_context'], runs[1]['receive_context'])
        self.assertIs(runs[0]['scene']['sim'], runs[1]['scene']['sim'])
        self.assertEqual([run['robot_id'] for run in runs], list(creation_order))
        for run in runs:
            robot_id = run['robot_id']
            self.assertEqual(run['scene']['prim_path'], f'/World/CR12_{robot_id}')
            self.assertEqual(run['capture'].product_path, f'/Product{robot_id}')
            self.assertEqual(run['initial_parameters']['robot_id'], robot_id)
            self.assertEqual(run['recorder'].result['robot_id'], robot_id)
        self.assertEqual(len(resources['runs']), 2)
        self.assertIs(rec.result['instance_setup'][0], runs[0]['recorder'].result)

    def test_one_shared_reset_both_state_writes_before_camera_initialization_and_publication(self):
        self._exercise_shared_preparation((0, 1))

    def test_reverse_creation_order_keeps_identity_mapping_and_one_shared_initialization(self):
        self._exercise_shared_preparation((1, 0))

    def test_partial_dual_finally_releases_every_constructed_owner_preserving_primary(self):
        tree = ast.parse(Path(entry.__file__).read_text(encoding='utf-8'))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        outer = next(node for node in main.body if isinstance(node, ast.Try))
        branch = next(node for node in outer.finalbody if isinstance(node, ast.For))
        code = compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(branch)], type_ignores=[])), '<dual-finally>', 'exec')
        captures = [mock.Mock(), mock.Mock()]
        captures[0].request_off.side_effect = RuntimeError('secondary OFF failure')
        recorder = FakeRecorder(); primary = RuntimeError('primary setup failure')
        runs = [dict(robot_id=i, resources={'capture': owner}, recorder=FakeRecorder()) for i, owner in enumerate(captures)]
        runs.append(dict(robot_id=9, resources={}, recorder=FakeRecorder()))  # Partial setup has no camera.
        context = dict(resources={'runs': runs}, recorder=recorder, failure=primary, cleanup_failure=entry.cleanup_failure,
            _contact_summary=entry._contact_summary)
        exec(code, context)
        for capture in captures: capture.release.assert_called_once_with()
        self.assertIs(context['failure'], primary)
        self.assertTrue(all(run['recorder'].result['camera_resources_released'] for run in runs[:2]))

    def test_verification_does_not_release_either_camera_before_both_native_reads(self):
        import _cr12_external_forces as forces
        resources = [{'capture': mock.Mock(), 'visual_override': mock.Mock()} for _ in range(2)]
        order = []
        sim = SimpleNamespace(current_time_step_index=600, current_time=5.)
        with mock.patch.object(entry, 'native_validity'), \
                mock.patch.object(entry, '_read_physics', side_effect=lambda robot, *a: order.append(robot) or ([], [], {})), \
                mock.patch.object(forces, 'read_scene_external_forces'):
            for i in range(2):
                rec = FakeRecorder(); rec.result.update(visual_preinit={'stage_checks': []}, pose_summary={'guard_pass_counts': {'clock': 600}})
                scene = dict(sim=sim, robot=i, configuration=object(), selected_pd={}, stage=object(), setup={},
                    physx_schema=object(), usd_physics=object(), default_time=object())
                request = SimpleNamespace(step=600, arrival={'stable_samples': 121, 'stable_span_s': 1.})
                entry.verify_final_capture_scene(scene, {'bodies': {}}, rec, resources[i], {}, request)
                for own in resources: own['capture'].release.assert_not_called()
        self.assertEqual(order, [0, 1])

    def test_optional_completion_label_preserves_coverage_incomplete_without_false_pass(self):
        tree = ast.parse(Path(entry.__file__).read_text(encoding='utf-8'))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        statement = next(node for node in ast.walk(main) if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == 'update' and any(k.arg == 'classification' for k in node.value.keywords))
        code = compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(statement)], type_ignores=[])), '<completion-label>', 'exec')
        for callback, expected in ((None, 'OLD_PASS'), (lambda result: result['case_classification'], 'COVERAGE_INCOMPLETE')):
            recorder = FakeRecorder(); recorder.result['case_classification'] = 'COVERAGE_INCOMPLETE'
            exec(code, dict(recorder=recorder, success_label='OLD_PASS', completion_label=callback))
            self.assertEqual(recorder.result['classification'], expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
