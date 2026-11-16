"""CPU contract edge cases; malformed inputs are explicit negative fixtures."""
import builtins
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np


class ContractEdges(unittest.TestCase):
    def test_metric_basis_missing_and_invalid_frames(self):
        from trace_format.contracts import private_metric_basis,contract_epoch
        from student_pilot.ground_lifting import public_centres
        def rotations(frame):
            if frame==2:raise IndexError('missing fixture frame')
            if frame==3:return np.full((3,3),np.nan)
            return np.eye(3)
        self.assertTrue(np.isfinite(private_metric_basis(rotations,np.array([0.,0.,1.]))).all())
        self.assertIsNone(private_metric_basis(lambda frame:np.zeros((3,3)),np.array([0.,0.,1.])))
        def cam(frame):
            if frame!=1:raise IndexError('no nonreference frame')
            return np.eye(3),np.zeros(3)
        with contract_epoch(True):
            camera,level=public_centres(SimpleNamespace(cam=cam),1,np.array([1.,2.,3.]),metric_only=True)
        np.testing.assert_array_equal(camera,[1.,-2.,3.]);np.testing.assert_array_equal(level,[1.,3.,2.])

    def test_empty_cache_alias_frame_and_dictionary_binding(self):
        from student_pilot.phrases import cache_view
        from student_pilot.training_contract import audit_training_contract
        from trace_format.contracts import contract_epoch
        cache={'phrases':['table'],'frames':{}}
        self.assertIs(cache_view(cache,'chair')[0],cache)
        empty={'phrases':['Chair','chair'],'frames':{'1':{'phrases':{}}}}
        result,name=cache_view(empty,'chair')
        self.assertEqual(name,'chair');self.assertEqual(result['frames']['1']['phrases'],{})
        row=dict(question='Where is the chair?',candidate_manifest={'phrases':{'phrases':['chair']}},
                 events=[dict(call='<ground obj="chair">',response='error: fixture unavailable')],
                 target='<think>\nThe tool response does not locate the chair.\n</think>\n<answer>unavailable</answer>')
        with contract_epoch(True):self.assertEqual(audit_training_contract([row]),[None])

    def test_generator_calculator_invalid_registration_and_absent_optional_contract(self):
        from generator.derivgen_v7.derivgen import calculator as C
        from trace_format.contracts import contract_epoch
        with contract_epoch(True):
            registry=C.PrintedPointRegistry()
            with self.assertRaises(C.CalculatorError):
                registry.register(camera=[],f1=[],spread=0,requested_frame=2)
        original=builtins.__import__
        def unavailable(name,globals=None,locals=None,fromlist=(),level=0):
            if name=='trace_format' and 'contracts' in fromlist:raise ImportError('optional contract unavailable fixture')
            return original(name,globals,locals,fromlist,level)
        with patch.object(builtins,'__import__',side_effect=unavailable):
            registry=C.PrintedPointRegistry()
        self.assertIsInstance(registry,C._SealedPointRegistry)

    def test_inconsistent_exclusion_count_refuses(self):
        from student_pilot.r2_admission import family_admission
        reports=[dict(family='units',counts={'units':dict(seen=2,admitted=2,refused=0)},
                      refusals=[dict(reason='excluded:withheld_room')])]
        with self.assertRaisesRegex(ValueError,'Invalid family admission counts'):family_admission(reports)
