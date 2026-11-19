"""Kit input refusals for absent recovery and every required conversion unit."""
from copy import deepcopy
import unittest
from student_pilot.r2_mix import table
from student_pilot.routing_requirements import blockers, require
from student_pilot import b7_inputs
from tests.test_r2_build7 import settings


class RequiredTrainingRows(unittest.TestCase):
    def test_each_missing_population_refuses_inputs(self):
        cfg=settings();counts=cfg['routing_training_counts'];mix=table()
        self.assertEqual(require(mix,counts),counts)
        self.assertEqual(blockers(mix,None),['RECOVERY_ROWS_ABSENT','UNIT_ROWS_ABSENT'])
        for count in (0,-1,True,None):
            bad=deepcopy(cfg);bad['routing_training_counts']['recovery']=count
            with self.assertRaisesRegex(ValueError,'RECOVERY_ROWS_ABSENT'):b7_inputs.validate(bad,'a0')
        for unit in ('cm','ft','in'):
            bad=deepcopy(cfg);bad['routing_training_counts']['units'][unit]=0
            with self.assertRaisesRegex(ValueError,'UNIT_ROWS_ABSENT'):b7_inputs.validate(bad,'a0')
        with self.assertRaisesRegex(ValueError,'UNIT_ROWS_ABSENT'):require(mix,dict(recovery=1,units=None))

    def test_zero_mix_refuses_even_with_positive_population(self):
        counts=settings()['routing_training_counts']
        for kind,reason in (('recovery','RECOVERY_ROWS_ABSENT'),('units','UNIT_ROWS_ABSENT')):
            mix=table()
            for cell in mix['cells']:
                if cell['type']==kind:cell.update(numerator=0,rows_per_step=0.)
            with self.assertRaisesRegex(ValueError,reason):require(mix,counts)

    def test_native_kit_records_named_refusals(self):
        from tests.test_r2_build import inputs
        from tests.test_r2_data_path import directory, LANE
        from launch_r2.build import build,verify,scan
        from student_pilot.p3_provenance import load
        for absent,reason in (('recovery','RECOVERY_ROWS_ABSENT'),('cm','UNIT_ROWS_ABSENT')):
            cfg=settings()
            cfg['init']=None
            cfg['row_stores']=None
            cfg['response_spec']={'version':'tool-response-text-v1','sha256':__import__('student_pilot.response_spec',fromlist=['sha256']).sha256()}
            if absent=='recovery':cfg['routing_training_counts']['recovery']=0
            else:cfg['routing_training_counts']['units'][absent]=0
            result=build(LANE/'work/kit07ca49df_meta/m',directory()/'kit',connector='none',records=inputs(),launch_inputs=cfg)
            self.assertIn(reason,result['blockers'])
            self.assertFalse(result['admission'])
