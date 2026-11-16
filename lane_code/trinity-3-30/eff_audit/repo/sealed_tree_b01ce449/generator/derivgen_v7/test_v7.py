"""Revision 6 admission boundaries and delivered measurement definitions."""
import json,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from derivgen import box_v313 as B, ground_v312 as old
from derivgen.ground_v312_degenerate import degeneracy_reasons
from test_v313_r3 import session
class RelativeAdmission(unittest.TestCase):
    def test_overlap_exception_is_scoped_and_other_gates_remain(self):
        def box(c,size=1):return dict(centroid=c,axesLengths=[size]*3,normalizedAxes=np.eye(3))
        boxes={'a':box([0,0,0]),'b':box([.8,0,0]),'c':box([3,0,0])}
        masks={n:np.zeros((1,2,2),bool) for n in boxes}
        item=dict(type='object_rel_distance',target_distance_rule=B.RULE)
        self.assertEqual(degeneracy_reasons(item,boxes,masks),[])
        for typ,rule in [('object_rel_distance','visible_surface'),('object_abs_distance',B.RULE),('object_rel_distance',None)]:
            self.assertIn('operand_box_overlap',degeneracy_reasons(dict(type=typ,target_distance_rule=rule),boxes,masks))
        boxes['b']=box([0,0,0],.2)
        self.assertIn('operand_box_containment',degeneracy_reasons(item,boxes,masks))
        masks['a'][:]=True;masks['b'][:]=True
        self.assertIn('operand_mask_overlap',degeneracy_reasons(item,boxes,masks))
    def render_measurements(self,values,label='A'):
        class Provider:
            provider_id='controlled_measurement_fixture'
            def __call__(self,n,*args):return B.box([{'stand':0,'face':1,'query':2}[n],0,2],[1,1,1],np.eye(3))
        item=dict(qid='margin',type='object_rel_distance',roles=dict(target='stand',cands=['face','query']),
                  question='Which candidate is closest?',options=['A. face','B. query'],gt_answer=label,gt_authority='independent fixture')
        with patch.object(B,'sampled_box_512',lambda a,b:values[int(b['centre'][0])-1]):
            return B.render(item,session(box_provider=Provider()),len)
    def test_decimal_threshold_is_inclusive_and_raw_threshold_is_not_required(self):
        # Raw separation is below .02, but the printed 1.00/1.02 margin is exactly .02.
        self.assertEqual(self.render_measurements([1.004,1.016])['answer'],'A')
    def test_ties_small_margins_and_wrong_labels_refuse(self):
        for values in [[1.,1.],[1.,1.01]]:
            with self.assertRaises(old.RowRefusal):self.render_measurements(values)
        with self.assertRaisesRegex(old.RowRefusal,'independent_box_winner_disagreement'):
            self.render_measurements([1.,1.02],label='B')


class PilotDefinition(unittest.TestCase):
    def test_measurement_definition_once(self):
        root=Path(__file__).resolve().parents[2]
        for line in (root/'out/pilot_v7/candidates.jsonl').read_text().splitlines():
            row=json.loads(line)
            if row['type'] not in ('object_abs_distance','object_rel_distance') or row['not_seen']:continue
            start='Each' if row['type']=='object_rel_distance' else 'The'
            sentence=start+" sampled-box gap is the smallest distance between points sampled inside the two objects' full boxes, which is how this benchmark defines the answer."
            self.assertEqual(row['suffix'].count(sentence),1)
            self.assertTrue(row['suffix'].split('</tool_response>\n')[-1].startswith(sentence+'\n'))
            self.assertTrue(all(sentence not in e['response'] for e in row['events']))
