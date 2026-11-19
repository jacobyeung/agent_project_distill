"""Addressing is a scheduled identity probe, not a learned-routing gate."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from student_pilot.acceptance_evidence import addressing_evidence, check_addressing, save, stage_assertions
from student_pilot.hrp_reread import Backend, Config
from student_pilot.scripted_calls import validate_reference


class Addressing(unittest.TestCase):
    def setUp(self):
        self.image=np.zeros((3,4,3),dtype=np.uint8)
        self.config=Config({20:self.image},tuple(range(32)))
        self.row=dict(id='test',name='bathtub',anchor_slot=20,source_index=19,
                      frame_rgb_sha256=hashlib.sha256(self.image.tobytes()).hexdigest())
        self.query=dict(name='bathtub',backend='hrp_reread',rows=[dict(frame=20,obj='bathtub',source_index=19,
            pixel_sha256=self.row['frame_rgb_sha256'],raw_output='{}',parse_status='invalid')])
        self.record=dict(heads=dict(ground_queries=[self.query]),finish='eos',errors=[],tokens=[],text='',calls=[])
    def evidence(self):return addressing_evidence(self.row,self.image,self.config,self.record)
    def test_strict_identity_and_input_dump(self):
        self.assertEqual(check_addressing(self.evidence())['frame'],20)
        directory=Path(tempfile.mkdtemp(prefix='addressing_'))
        save(directory/'inputs.json',self.evidence())
        saved=json.loads((directory/'inputs.json').read_text())
        self.assertEqual(saved['ground_rows'][0]['pixel_sha256'],self.row['frame_rgb_sha256'])
        self.assertEqual(saved['reread_config']['frame_indices'],list(range(32)))
        self.assertEqual(saved['generation']['finish'],'eos')
    def test_zero_several_and_digest_branches_remain_strict(self):
        original=deepcopy(self.record)
        for queries,branch in (([],'zero_rows'),([self.query,self.query],'several_rows')):
            self.record['heads']['ground_queries']=queries
            evidence=self.evidence();self.assertEqual(evidence['branch'],branch)
            with self.assertRaisesRegex(AssertionError,branch):check_addressing(evidence)
        self.record=original;self.record['heads']['ground_queries'][0]['rows'][0]['pixel_sha256']='wrong'
        with self.assertRaisesRegex(AssertionError,'digest_mismatch'):check_addressing(self.evidence())
    def test_name_slot_and_source_are_not_normalized_away(self):
        original=deepcopy(self.record)
        for change in ('name','frame','source_index','obj','backend'):
            self.record=deepcopy(original);q=self.record['heads']['ground_queries'][0]
            if change in ('name','backend'):q[change]='Bathtub'
            else:q['rows'][0][change]=21 if change!='obj' else 'Bathtub'
            with self.assertRaises(AssertionError):check_addressing(self.evidence())
    def test_repeated_exact_ground_is_cached_and_hashes_original_rgb(self):
        backend=Backend(None,None,None,self.config)
        with patch('student_pilot.hrp_reread.read_image',return_value=dict(raw_output='{}',parse_status='invalid')) as read, \
             patch('student_pilot.hrp_reread.render',return_value=('bathtub: not seen',{})):
            backend.ground('bathtub',None);backend.ground('bathtub',None)
        self.assertEqual(read.call_count,1)
        self.assertEqual(len(backend.queries),1)
        self.assertEqual(backend.queries[0]['rows'][0]['pixel_sha256'],self.row['frame_rgb_sha256'])
    def test_scheduled_addressing_requires_exactly_one_unboxed_target(self):
        ref=dict(schema='addressing-call-v1',free_answer=True,name='bathtub',
                 segments=[dict(call='<ground obj="bathtub">',text='<think>\n<ground obj="bathtub">')])
        self.assertEqual(len(validate_reference(ref)),1)
        for field,value in [('name','Bathtub'),('free_answer',False),('segments',ref['segments']*2)]:
            bad=dict(ref);bad[field]=value
            with self.assertRaises(ValueError):validate_reference(bad)
    def test_all_stage_wrappers_retain_nested_assertion_inputs(self):
        for stage in (4,5,6):
            directory=Path(tempfile.mkdtemp(prefix=f'stage_{stage}_'))
            @stage_assertions(stage)
            def failing(args):
                operand=dict(target='bathtub',pixel_sha256='changed')
                assert operand['pixel_sha256']=='expected','injected assertion'
            with self.assertRaisesRegex(AssertionError,'injected assertion'):
                failing(SimpleNamespace(out=directory))
            files=list(directory.glob('ASSERTION_*.json'));self.assertEqual(len(files),1)
            data=json.loads(files[0].read_text())
            self.assertEqual(data['frames'][-1]['inputs']['operand']['pixel_sha256'],'changed')

if __name__=='__main__':unittest.main()
