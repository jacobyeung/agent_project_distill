"""Processor compatibility checks; no weights, GPU, files, or production rows."""
import copy
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from student_pilot import carrier_c1_run as run, carrier_c1_data as data, pose_samples
from student_pilot.b7_inputs import layout


class Compatibility(unittest.TestCase):
    def processor(self, cfg):
        value = SimpleNamespace(tokenizer=SimpleNamespace())
        with patch.object(run, 'processor_for', return_value=value), patch.object(
                run.rehearsal, 'fixture_manifest', return_value={}), patch.object(run.routing, 'add_routing_tokens'):
            return run.processor_for_receipt({'root':'unused'}, cfg)

    def test_legacy_r1_does_not_enable_b7(self):
        p = self.processor(dict(training_mode='final', frame_layout='duplicate', frame_markers=True))
        n = self.processor(dict(training_mode='final', r1_training={'enabled':True},
                                min_pixels=None, max_pixels=None, frame_count=32,
                                frame_layout='duplicate', frame_markers=True))
        self.assertFalse(hasattr(p, '_b7_layout'))
        self.assertFalse(hasattr(n, '_b7_layout'))
        self.assertEqual(n.tokenizer._c1_frame_count, 32)
        self.assertTrue(n.tokenizer._c1_frame_markers)
        self.assertEqual(vars(p.tokenizer), vars(n.tokenizer))

    def test_b7_still_requires_exact_pins(self):
        with self.assertRaisesRegex(ValueError, 'processor_resolution_pin_missing'):
            self.processor(dict(b7_inputs={'enabled':True}))
        pins=dict(min_pixels=16384,max_pixels=147456,frame_count=32,frame_layout='duplicate',frame_markers=True)
        p=self.processor(dict(frame_count=32,b7_inputs=pins))
        self.assertEqual(p._b7_layout,layout(pins))

    def test_legacy_encoder_uses_identical_bounds_and_arrays(self):
        p=self.processor(dict(training_mode='final',frame_markers=True))
        n=self.processor(dict(training_mode='final',frame_markers=True,r1_training={'enabled':True}))
        b7=self.processor(dict(training_mode='final',frame_count=32,b7_inputs=dict(
            min_pixels=16384,max_pixels=147456,frame_count=32,frame_layout='duplicate',frame_markers=True)))
        for count in (32,31):
            row=dict(dataset='fixture',scene='room',target='A',student_input=dict(question='Q',
                frames=[{} for _ in range(count)],frame_indices=list(range(count)),
                timestamps=[i/30 for i in range(count)],fps=30,total_num_frames=count))
            arrays=np.arange(count*2*2*3,dtype=np.uint8).reshape(count,2,2,3)
            captured=[]
            def encode(proc,q,options,rgb,metadata,target,pixels,limit):
                captured.append((rgb.copy(),pixels,metadata.frames_indices,limit));return {},{}
            with patch.object(pose_samples,'load_frames',return_value=arrays),patch.object(pose_samples,'encode_frames',side_effect=encode):
                data.encode_layout_row(p,row,'duplicate',None)
                data.encode_layout_row(n,row,'duplicate',None)
                if count==31:
                    with self.assertRaisesRegex(ValueError,'row_training_frame_count_mismatch'):
                        data.encode_layout_row(b7,row,'duplicate',None)
            self.assertTrue(np.array_equal(captured[0][0],captured[1][0]))
            self.assertEqual(captured[0][1:],captured[1][1:])
            self.assertEqual(captured[0][1],(16384,147456))
            self.assertEqual(captured[0][0].shape[0],count*2)


if __name__=='__main__':unittest.main()
