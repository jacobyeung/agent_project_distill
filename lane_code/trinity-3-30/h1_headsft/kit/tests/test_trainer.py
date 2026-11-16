import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import torch
from tests.fixtures import camera_fixtures, tiny, packed, routing_batch, Processor, K
from student_pilot import h1_faithful as F
from student_pilot import h1, carrier_c1_routing as R, carrier_c1_run as run


class Trainer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw, cls.clip, _ = camera_fixtures()

    def test_faithful_identity_raw_and_packed(self):
        for raw in self.raw:
            values={e['call_id']:e for e in raw['events'] if e['kind']=='tool_response'}
            self.assertEqual(h1.materialize(raw,values)['target'],raw['target'])
            self.assertEqual(h1.materialize(h1.canonical_row(packed(raw,self.clip)),values)['target'],raw['target'])

    def test_own_full_suffix_and_decision(self):
        model,base,_=tiny()
        for raw in self.raw:
            row=packed(raw,self.clip)
            batch,_=routing_batch(base,row)
            p=torch.tensor(raw['gt_pose9']).numpy();p[:, :3]*=-2
            # Reverse turn by reflecting the synthetic yaw about the gravity axis.
            if raw['question_type']=='camera_rotation': p[:,4]*=-1
            out,target,spans,segments=h1.faithful(row,R.OwnGeometry(p,raw['gt_up'],None))
            self.assertNotEqual(target,raw['target'])
            self.assertNotEqual(out['answer'],raw['answer'])
            b,a=R.encode_own(Processor(),row,batch,target,spans,segments,faithful=True)
            ids,mask,offsets=R.suffix_tokens(Processor(),row,target,spans)
            start=int(b['aux_suffix_start'][0]);labs=b['labels'][0,start:start+len(ids)]
            self.assertEqual((labs!=-100).tolist(),mask)
            self.assertTrue(all(mask[i] for i,(lo,hi) in enumerate(offsets) if lo>=spans[-1]['end']-len(R.THINK)))
            printed=h1.printed_camera(raw,target,spans)['c1']
            if raw['question_type']=='camera_movement_direction':
                dx,_,dz=printed['delta']; scores=dict(left=-dx,right=dx,forward=dz,backward=-dz)
                best=max(scores,key=scores.get)
                self.assertEqual(out['answer'],next(x[0] for x in raw['options'] if x[3:]==best))
                self.assertNotEqual([e['text'] for e in out['events'] if e['kind']=='canonical_text'],
                                    [e['text'] for e in raw['events'] if e['kind']=='canonical_text'])
            elif raw['question_type']=='camera_displacement': self.assertEqual(float(out['answer']),printed['distance'])
            else: self.assertEqual(int(out['answer']),printed['value'])

    def test_pose_loss_and_missing(self):
        model,batch,_=tiny()
        row=packed(self.raw[0],self.clip)
        batch,_=routing_batch(batch,row)
        targets,counts=h1.pose_targets(row,batch,{})
        result=model(batch,targets,stream='routing')
        self.assertTrue(torch.isfinite(result['loss']))
        self.assertGreater(float(result['components']['pose']),0)
        self.assertEqual(counts['supervised'],1)
        self.assertAlmostEqual(float(result['loss']),float(result['components']['routing'])*model.recipe['weights'].get('routing',0)+float(result['components']['pose'])*model.recipe['weights']['pose'],places=5)
        row=copy.deepcopy(row);row['routing'].pop('gt_pose9')
        targets,counts=h1.pose_targets(row,batch,{})
        result=model(batch,targets,stream='routing')
        self.assertEqual(float(result['components']['pose']),0)
        self.assertEqual(counts['missing'],1)

    def test_refusal_gt_and_ground_gate(self):
        model,base,_=tiny(); row=packed(self.raw[0],self.clip);batch,a=routing_batch(base,row)
        class Rows:
            processor=Processor();h1={'faithful_own_camera_rows':True}
            def row(self,*args): return row, None
        with patch.object(F,'faithful',side_effect=h1.MaterializeRefusal('test_reason')):
            b, audit=run.own_values(model,Rows(),batch,a,0,(True,True),torch.device('cpu'))
        self.assertIs(b,batch);self.assertEqual(audit['h1']['refused'],'test_reason')
        # A depth-only draw must not demand a camera pose substitution.
        b,audit=run.own_values(model,Rows(),batch,a,0,(True,False),torch.device('cpu'))
        self.assertIs(b,batch); self.assertEqual(audit['h1']['values'],'gt')

    def test_gt_fields_survive_pack(self):
        for raw in self.raw:
            row=packed(raw,self.clip)
            self.assertEqual(row['routing']['gt_pose9'],raw['gt_pose9'])
            self.assertEqual(row['routing']['gt_up'],raw['gt_up'])

if __name__=='__main__': unittest.main()
