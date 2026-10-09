"""The real contact update/read/check chain on independent CPU sensor fakes."""
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock
import numpy as np

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/environments'))
import _cr12_runtime_support as runtime

DT=1/120


class Tensor:
    def __init__(self,value,dtype=None,device='cpu'):
        self.array=np.asarray(value,dtype=dtype)
        self.device=device
    @property
    def dtype(self): return self.array.dtype
    @property
    def shape(self): return self.array.shape
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return self.array


class Sensor:
    def __init__(self,path='/World/CR12_0/CR12/agv',dtype=np.float32):
        self.cfg=SimpleNamespace(prim_path=path,update_period=0.)
        self.device='cpu';self.is_initialized=True;self.num_bodies=1
        self._timestamp=Tensor([0.],dtype);self._timestamp_last_update=Tensor([0.],dtype)
        self._is_outdated=Tensor([True],bool)
        self.contact_physx_view=SimpleNamespace(sensor_count=1,filter_count=2,
            sensor_paths=[path],filter_paths=[['/World/CR12_1/CR12/agv','/World/CR12_0/CR12/link_3']])
        self.matrix=Tensor(np.zeros((1,1,2,3)),dtype)
        self.events=[];self.mode='normal';self.native_refreshes=0
    def update(self,dt,force_recompute=False):
        self.events.append(('update',dt,force_recompute))
        if self.mode=='raise': raise RuntimeError('native update fault')
        if self.mode!='skip':
            count=2 if self.mode=='double' else 1
            step=dt*2 if self.mode=='wrong_dt' else dt
            for _ in range(count):
                self._timestamp.array[...] = np.add(self._timestamp.array,
                    np.asarray(step,dtype=self._timestamp.dtype),dtype=self._timestamp.dtype)
        if self.mode=='reset': self._timestamp.array[:]=0
        if self.mode!='stale_last': self._timestamp_last_update.array[:]=self._timestamp.array
        self._is_outdated.array[:]=self.mode=='outdated'
        self.native_refreshes+=1
    @property
    def data(self):
        self.events.append(('data',))
        return SimpleNamespace(force_matrix_w=self.matrix)


def prepared(path='/World/CR12_0/CR12/agv',dtype=np.float32):
    sensor=Sensor(path,dtype)
    record=runtime._new_contact_record(sensor,dict.fromkeys(sensor.contact_physx_view.filter_paths[0]),path)
    records={'agv':record}
    runtime._check_contacts(records,0.,initialize=True,context={'global_physics_step':0,'phase':'initialize'})
    return records,sensor


class ContactRuntimeTests(unittest.TestCase):
    def test_exactly_one_update_then_data_per_step_and_frozen_zero_forces(self):
        records,sensor=prepared()
        previous=records['agv']['_time_previous']
        self.assertEqual(runtime._check_contacts(records,DT,context={'global_physics_step':1,'phase':'approach'}),0.)
        self.assertEqual(sensor.events,[('update',0.,True),('data',),('update',DT,True),('data',)])
        self.assertEqual(sensor.native_refreshes,2)
        self.assertEqual(previous.timestamp,0.)
        self.assertEqual(records['agv']['diagnostics']['advance_pass_count'],1)
        self.assertTrue(all(records['agv']['diagnostics']['last_sample']['checks'].values()))

    def test_float32_runtime_chain_crosses_32_and_64_with_old_shadow(self):
        records,sensor=prepared()
        for step in range(1,7701):
            runtime._check_contacts(records,DT,context={'global_physics_step':step,'phase':'same_frozen_path'})
        d=records['agv']['diagnostics']
        first=d['first_shadow_disagreements']['old_reject_new_accept']
        self.assertEqual(first['context']['global_physics_step'],3842)
        self.assertEqual(first['previous']['timestamp'],32.007930755615234)
        self.assertEqual(first['current']['value'],32.016265869140625)
        self.assertTrue(first['time_validation']['passed'])
        self.assertFalse(first['time_validation']['old_shadow_pass'])
        self.assertEqual(d['advance_pass_count'],7700)
        self.assertEqual(d['update_call_count'],7701)
        self.assertTrue(2<=len(d['boundary_samples']['32'])<=6)
        self.assertTrue(2<=len(d['boundary_samples']['64'])<=6)

    def test_fourteen_sensor_states_same_names_are_independent(self):
        batches=[]
        for robot in (0,1):
            records={}
            for name in ('agv',*(f'link_{i}' for i in range(1,7))):
                path=f'/World/CR12_{robot}/CR12/{name}'
                sensor=Sensor(path)
                records[name]=runtime._new_contact_record(sensor,dict.fromkeys(sensor.contact_physx_view.filter_paths[0]),path)
            runtime._check_contacts(records,0.0,initialize=True)
            runtime._check_contacts(records,DT,context={'robot_id':robot,'global_physics_step':1})
            batches.append(records)
        self.assertEqual(len({r['generation'] for b in batches for r in b.values()}),14)
        previous=batches[1]['agv']['_time_previous']
        runtime._check_contacts(batches[0],DT,context={'robot_id':0,'global_physics_step':2})
        self.assertIs(batches[1]['agv']['_time_previous'],previous)
        self.assertEqual(batches[0]['agv']['updates'],2)
        self.assertEqual(batches[1]['agv']['updates'],1)

    def test_readonly_has_no_update_and_cannot_refresh_outdated(self):
        records,sensor=prepared();runtime._check_contacts(records,DT)
        count=records['agv']['updates'];refreshes=sensor.native_refreshes
        runtime._check_contacts(records,0.0,read_only=True)
        self.assertEqual(records['agv']['updates'],count)
        self.assertEqual(sensor.native_refreshes,refreshes)
        self.assertEqual(records['agv']['diagnostics']['readonly_pass_count'],1)
        sensor._is_outdated.array[:]=True
        before=len(sensor.events)
        with self.assertRaises(runtime.DriveCheckError): runtime._check_contacts(records,0.0,read_only=True)
        self.assertEqual(len(sensor.events),before)
        self.assertIs(records['agv']['diagnostics']['first_failure']['outdated']['value'],True)

    def test_skip_double_wrong_dt_reset_and_counter_only_changes_rejected(self):
        for mode in ('skip','double','wrong_dt','reset'):
            with self.subTest(mode=mode):
                records,sensor=prepared();runtime._check_contacts(records,DT)
                old=records['agv']['_time_previous'];sensor.mode=mode
                records['agv']['timestamp']=999;records['agv']['updates']+=1
                with self.assertRaises(runtime.DriveCheckError) as caught: runtime._check_contacts(records,DT)
                self.assertEqual(caught.exception.details['contact_sample']['failed_condition'],'time')
                self.assertIs(records['agv']['_time_previous'],old)

    def test_outdated_or_last_update_stale_is_not_normal_time(self):
        for mode in ('outdated','stale_last'):
            records,sensor=prepared();sensor.mode=mode
            with self.subTest(mode=mode),self.assertRaises(runtime.DriveCheckError) as caught:
                runtime._check_contacts(records,DT)
            sample=caught.exception.details['contact_sample']
            self.assertFalse(sample['checks']['time'])
            self.assertTrue(sample['checks']['force_finite'])
            self.assertTrue(sample['checks']['force_threshold'])

    def test_force_nan_inf_and_threshold_remain_independent(self):
        for value in (np.nan,np.inf,.10001):
            records,sensor=prepared();sensor.matrix.array[0,0,0,0]=value
            with self.subTest(value=value),self.assertRaises(runtime.DriveCheckError) as caught:
                runtime._check_contacts(records,DT)
            sample=caught.exception.details['contact_sample']
            self.assertTrue(sample['time_validation']['passed'])
            self.assertFalse(sample['passed'])
            self.assertEqual(caught.exception.category,'forbidden_contact' if value==.10001 else 'contact_monitor')
            if value==.10001: self.assertGreater(records['agv']['maximum_force_n'],.1)

    def test_mapping_shape_wrong_sensor_and_device_fail(self):
        for mode in ('filter','shape','sensor','device','clock_shape','clock_dtype','clock_nan'):
            records,sensor=prepared()
            if mode=='filter': sensor.contact_physx_view.filter_paths[0][0]='/WRONG'
            if mode=='shape': sensor.matrix.array=np.zeros((1,1,1,3))
            if mode=='sensor': records['agv']['sensor']=Sensor()
            if mode=='device': sensor.matrix.device='cuda:7'
            if mode=='clock_shape': sensor._timestamp.array=np.zeros((1,1),dtype=np.float32)
            if mode=='clock_dtype': sensor._timestamp.array=np.zeros(1,dtype=np.float16)
            if mode=='clock_nan': sensor._timestamp.array[:]=np.nan
            with self.subTest(mode=mode),self.assertRaises((runtime.DriveCheckError,ValueError,TypeError)):
                runtime._check_contacts(records,DT)
            self.assertIsNotNone(records['agv']['diagnostics']['first_failure'])

    def test_rebaseline_after_claim_or_rebuild_is_rejected(self):
        records,sensor=prepared();runtime._check_contacts(records,DT)
        generation=records['agv']['generation'];before=len(sensor.events)
        with self.assertRaises(runtime.DriveCheckError):
            runtime._check_contacts(records,0.0,initialize=True,context={'phase':'logical_episode_rebuild'})
        self.assertEqual(len(sensor.events),before)
        self.assertEqual(records['agv']['generation'],generation)

    def test_first_failure_sticky_partial_coverage_and_snapshot_copy(self):
        a,sa=prepared();b,sb=prepared('/World/CR12_1/CR12/agv')
        combined={'agv':a['agv'],'peer':b['agv']};sa.mode='skip'
        with self.assertRaises(runtime.DriveCheckError) as first: runtime._check_contacts(combined,DT)
        count=len(sa.events);peer_count=len(sb.events)
        summary=runtime._contact_summary(combined)
        self.assertIsNotNone(summary['agv']['diagnostics']['first_failure'])
        self.assertIsNone(summary['peer']['diagnostics']['first_failure'])
        with self.assertRaises(runtime.DriveCheckError) as second: runtime._check_contacts(combined,DT)
        self.assertIs(first.exception,second.exception)
        self.assertEqual(len(sa.events),count);self.assertEqual(len(sb.events),peer_count)
        combined['agv']['diagnostics']['check_attempt_count']=100
        self.assertNotEqual(summary['agv']['diagnostics']['check_attempt_count'],100)

    def test_native_exception_not_masked_by_diagnostic_failure(self):
        records,sensor=prepared();sensor.mode='raise'
        with mock.patch.object(runtime,'_keep_contact_sample',side_effect=ValueError('serialization failed')):
            with self.assertRaisesRegex(RuntimeError,'native update fault'):
                runtime._check_contacts(records,DT)


if __name__=='__main__': unittest.main()
