"""CPU-only representable SensorBase add_ contract and true stale counterexamples."""
from pathlib import Path
import dataclasses
import json
import math
import sys
import unittest
import numpy as np
import torch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/environments'))
import _cr12_contact_time as ct


def snapshot(value, dtype='float32', **changes):
    actual=float(np.dtype(dtype).type(value)) if dtype in ('float32','float64') else float(value)
    fields=dict(timestamp=actual,last_update=actual,dtype=dtype,last_dtype=dtype,
        device='cpu',last_device='cpu',shape=(1,),last_shape=(1,),outdated=False,
        identity=('/World/CR12_0/agv','sensor-123'),generation='run-generation')
    fields.update(changes)
    return ct.freeze_snapshot(**fields)


class ContactTimeTests(unittest.TestCase):
    def test_continuous_torch_add_to_115_seconds_float32_and_float64(self):
        for name,dtype in (('float32',torch.float32),('float64',torch.float64)):
            time=torch.zeros(1,dtype=dtype,device='cpu')
            previous=snapshot(time.item(),name)
            first_old_failure=None
            for step in range(1,13801):
                time.add_(ct.PHYSICS_DT)
                current=snapshot(time.item(),name)
                report=ct.validate_timestamp(previous,current,ct.PHYSICS_DT)
                self.assertTrue(report['passed'],(name,step,report))
                if not report['old_shadow_pass'] and first_old_failure is None:first_old_failure=step
                previous=current
            self.assertEqual(first_old_failure,3842 if name=='float32' else None)

    def test_exponent_boundaries_and_128_neighborhood_match_torch(self):
        for name,dtype in (('float32',torch.float32),('float64',torch.float64)):
            for center in (32.,64.,128.):
                time=torch.tensor([center-.05],dtype=dtype,device='cpu')
                previous=snapshot(time.item(),name)
                for _ in range(16):
                    time.add_(ct.PHYSICS_DT)
                    current=snapshot(time.item(),name)
                    self.assertTrue(ct.validate_timestamp(previous,current,ct.PHYSICS_DT)['passed'])
                    previous=current

    def test_historical_scalar_is_hypothesis_not_measured_failed_tick(self):
        previous=snapshot(32.007930755615234)
        current=snapshot(32.016265869140625)
        result=ct.validate_timestamp(previous,current,ct.PHYSICS_DT)
        self.assertTrue(result['passed']);self.assertFalse(result['old_shadow_pass'])
        self.assertAlmostEqual(result['old_increment_error'],1.7801920572917823e-6,places=17)
        self.assertEqual(result['expected_next'],current.timestamp)

    def test_zero_and_two_updates_rejected_at_each_boundary(self):
        for name,dtype in (('float32',torch.float32),('float64',torch.float64)):
            for value in (0.,31.999,32.01,63.999,64.01,114.9,127.999,128.01):
                time=torch.tensor([value],dtype=dtype,device='cpu')
                previous=snapshot(time.item(),name)
                self.assertFalse(ct.validate_timestamp(previous,snapshot(time.item(),name),ct.PHYSICS_DT)['passed'])
                time.add_(ct.PHYSICS_DT).add_(ct.PHYSICS_DT)
                self.assertFalse(ct.validate_timestamp(previous,snapshot(time.item(),name),ct.PHYSICS_DT)['passed'])

    def test_wrong_dt_rejected_even_if_representable_timestamp_matches(self):
        p=snapshot(64.)
        t=torch.tensor([p.timestamp],dtype=torch.float32);t.add_(ct.PHYSICS_DT)
        c=snapshot(t.item())
        for dt in (0.,ct.PHYSICS_DT*2,ct.PHYSICS_DT/2,ct.PHYSICS_DT+1e-15,
                   np.float32(ct.PHYSICS_DT),1,True,float('nan')):
            self.assertFalse(ct.validate_timestamp(p,c,dt)['passed'])

    def test_last_update_stale_and_outdated_rejected(self):
        p=snapshot(32.)
        t=torch.tensor([p.timestamp],dtype=torch.float32);t.add_(ct.PHYSICS_DT)
        for changes in ({'last_update':p.timestamp},{'outdated':True},{'outdated':None}):
            evidence=ct.validate_timestamp(p,snapshot(t.item(),**changes),ct.PHYSICS_DT)
            self.assertFalse(evidence['passed'])
            self.assertEqual(evidence['expected_next'],t.item())
            self.assertIsNotNone(evidence['old_increment_error'])

    def test_backward_reset_nonfinite_and_unrepresentable_input_rejected(self):
        p=snapshot(32.)
        for value in (0.,31.,-1.,float('nan'),float('inf'),-float('inf'),None,True):
            c=snapshot(0.,timestamp=value,last_update=value)
            result=ct.validate_timestamp(p,c,ct.PHYSICS_DT)
            self.assertFalse(result['passed']);json.dumps(result,allow_nan=False)
        self.assertFalse(ct.validate_timestamp(p,snapshot(0.,timestamp=.1,last_update=.1),ct.PHYSICS_DT)['passed'])

    def test_identity_generation_shape_dtype_and_device_are_bound(self):
        p=snapshot(1.)
        t=torch.tensor([p.timestamp],dtype=torch.float32);t.add_(ct.PHYSICS_DT)
        for changes in ({'identity':('/World/CR12_1/agv','sensor-123')}, {'identity':('/World/CR12_0/agv','sensor-124')},
            {'generation':'new-resource'}, {'shape':(1,1)}, {'shape':(True,)}, {'last_shape':(2,)},
            {'last_dtype':'float64'}, {'last_device':'cuda:0'}, {'device':'cuda:1','last_device':'cuda:1'},
            {'device':'cuda:0','last_device':'cuda:0'}):
            self.assertFalse(ct.validate_timestamp(p,snapshot(t.item(),**changes),ct.PHYSICS_DT)['passed'],changes)

    def test_independent_sensors_same_numeric_values_do_not_share_state(self):
        states=[snapshot(0.,identity=(f'/World/CR12_{i}/agv',str(i))) for i in (0,1)]
        nexts=[snapshot(np.float32(ct.PHYSICS_DT),identity=s.identity) for s in states]
        for i in (0,1):self.assertTrue(ct.validate_timestamp(states[i],nexts[i],ct.PHYSICS_DT)['passed'])
        self.assertFalse(ct.validate_timestamp(states[0],nexts[1],ct.PHYSICS_DT)['passed'])

    def test_baseline_once_and_same_tick_readonly_do_not_count_as_update(self):
        p=snapshot(0.)
        self.assertTrue(ct.validate_timestamp(None,p,0.,mode='baseline')['passed'])
        self.assertFalse(ct.validate_timestamp(p,p,0.,mode='baseline')['passed'])
        self.assertFalse(ct.validate_timestamp(None,p,0.,mode='readonly')['passed'])
        self.assertTrue(ct.validate_timestamp(p,snapshot(0.),0.,mode='readonly')['passed'])
        self.assertFalse(ct.validate_timestamp(p,snapshot(ct.PHYSICS_DT),0.,mode='readonly')['passed'])
        self.assertFalse(ct.validate_timestamp(p,p,ct.PHYSICS_DT)['passed'])

    def test_snapshot_cannot_alias_mutating_buffer_or_metadata(self):
        time=np.array([32.],dtype=np.float32);identity=['/World/CR12_0/agv','s'];shape=[1]
        p=snapshot(time[0],identity=identity,shape=shape)
        time+=np.float32(ct.PHYSICS_DT);identity[0]='/World/CR12_1/agv';shape[0]=2
        self.assertEqual(p.timestamp,32.);self.assertEqual(p.shape,(1,));self.assertEqual(p.identity[0],'/World/CR12_0/agv')
        with self.assertRaises(dataclasses.FrozenInstanceError):p.timestamp=0.
        self.assertTrue(ct.validate_timestamp(p,snapshot(time[0],identity=p.identity),ct.PHYSICS_DT)['passed'])

    def test_unsupported_dtype_and_resolution_loss_fail_closed(self):
        for name in ('float16','bfloat16','int64','float128','unknown'):
            self.assertFalse(ct.validate_timestamp(None,snapshot(0.,name),0.,mode='baseline')['passed'])
        for name,value in (('float32',2.**18),('float64',2.**48)):
            p=snapshot(value,name);c=snapshot(value,name)
            result=ct.validate_timestamp(p,c,ct.PHYSICS_DT)
            self.assertFalse(result['passed']);self.assertFalse(result['checks']['resolution_distinguishes_updates'])

    def test_invalid_mode_or_counter_only_change_cannot_validate_read(self):
        p=snapshot(32.)
        self.assertFalse(ct.validate_timestamp(p,p,ct.PHYSICS_DT,mode='unknown')['passed'])
        project_count=100
        project_count+=1
        self.assertEqual(project_count,101)
        self.assertFalse(ct.validate_timestamp(p,p,ct.PHYSICS_DT)['passed'])


if __name__=='__main__':unittest.main(verbosity=2)
