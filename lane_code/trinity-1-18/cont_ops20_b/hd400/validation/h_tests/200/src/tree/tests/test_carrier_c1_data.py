import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

import numpy as np
from PIL import Image

from student_pilot.carrier_c1_data import build_stream
from student_pilot.p3_provenance import file_pin,write


class DataTests(unittest.TestCase):
    def fixture(self):
        root=Path(tempfile.mkdtemp(prefix='c1_data_',dir=os.environ['LANE_TEST_OUTPUT']))
        Image.new('RGB',(8,8),(30,40,50)).save(root/'rgb.png')
        mask=np.zeros((8,8),dtype=bool);mask[1:3,4:7]=True
        np.savez(root/'mask.npz',mask=mask)
        frame=file_pin(root/'rgb.png')
        write(root/'division.json',dict(schema='diagnostic-whole-scene-division-v1',training_only=True,
                                       train_scenes=['d/train'],heldout_scenes=['d/held']))
        row=dict(qid='q0',dataset='d',scene='train',target='answer',student_input=dict(
            frames=[frame]*32,frame_indices=list(range(32)),question='Point to the chair in frame 2.',options=[]),
            pointing=dict(kind='gt_instance_mask',frame=2,rgb_sha256=frame['sha256'],
                          instance_id='chair_1',mask=file_pin(root/'mask.npz')))
        return root,row

    def build(self,root,row,stream,out='built'):
        source=root/(out+'.jsonl');source.write_text(json.dumps(row)+'\n')
        return build_stream(file_pin(source),file_pin(root/'division.json'),root/out,stream)

    def test_verified_point_target_and_answer_only_stream_receipts(self):
        root,row=self.fixture()
        for stream in ('vqa','pointing'):
            receipt=self.build(root,row,stream,stream)
            self.assertEqual(receipt['count'],1)
            self.assertEqual(receipt['heldout_overlap'],0)
            with sqlite3.connect(receipt['database']['path']) as conn:
                saved=json.loads(conn.execute('SELECT row FROM rows').fetchone()[0])
            self.assertEqual(saved['student_input'],row['student_input'])
            if stream=='pointing':
                point=json.loads(saved['target'].split('</think>\n\n')[1])['point_2d']
                self.assertTrue(all(type(v) is int and 0<=v<=1000 for v in point))
                self.assertTrue(np.load(root/'mask.npz')['mask'][point[1]*8//1000,point[0]*8//1000])
                self.assertEqual(saved['pointing']['selected']['shape'],[8,8])
                self.assertTrue(receipt['gt_masks_only'])
            else:
                self.assertEqual(saved['target'],'answer')

    def test_absent_object_targets_null_only_with_empty_evidence(self):
        root,row=self.fixture()
        np.savez(root/'frame.npz',absent_lamp=np.zeros((8,8),dtype=bool),chair_1=np.load(root/'mask.npz')['mask'])
        absent=dict(kind='gt_absent',frame=2,rgb_sha256=row['pointing']['rgb_sha256'],label='lamp',
                    mask=file_pin(root/'frame.npz'),key='absent_lamp')
        receipt=self.build(root,{**row,'pointing':absent},'pointing','absent')
        with sqlite3.connect(receipt['database']['path']) as conn:
            saved=json.loads(conn.execute('SELECT row FROM rows').fetchone()[0])
        self.assertEqual(saved['target'],'<think>\n\n</think>\n\n{"point_2d": null}')
        with self.assertRaisesRegex(ValueError,'empty'):
            self.build(root,{**row,'pointing':{**absent,'key':'chair_1'}},'pointing','nonempty')

    def test_rejects_heldout_estimated_masks_and_rgb_mismatch(self):
        for mutation,expected in ((dict(scene='held'),'division'),
                                 (dict(pointing=dict(kind='sam3')),'provenance'),
                                 (dict(pointing=dict(rgb_sha256='0'*64)),'provenance')):
            root,row=self.fixture()
            if 'pointing' in mutation:
                mutation={'pointing':{**row['pointing'],**mutation['pointing']}}
            with self.assertRaisesRegex(ValueError,expected):
                self.build(root,{**row,**mutation},'pointing')


if __name__=='__main__':
    unittest.main()
