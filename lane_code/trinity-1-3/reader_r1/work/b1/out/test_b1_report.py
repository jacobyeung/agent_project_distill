import json
from pathlib import Path
import unittest
import b1_report as B

class ReportFixture(unittest.TestCase):
    def test_paired_units_and_missing_diagnostics(self):
        root=Path(__file__).resolve().parents[1]/'work/report_fixture';root.mkdir(exist_ok=True)
        items={str(i):dict(id=str(i),room_key='room'+str(i//2),dataset='fixture',question_type='object_abs_distance',
              question='How far in '+('metres' if i%2 else 'centimetres')+'?',ground_truth=2 if i%2 else 200) for i in range(4)}
        files=[]
        for rule in B.RULES:
            values=[]
            for i,it in items.items():
                d=dict(rule=rule,sam3={'kept_per_frame':[1]*32},linked_candidates=1,chosen_index=-1 if rule==B.RULES[0] else 0,null_would_win=True)
                vals=dict(id=i,arm='own',mode='none',output=dict(finish='eos',scores={'answer':.3 if rule==B.RULES[0] else .5},calls={'records':[
                    dict(family='ground',call='<ground obj="lamp" mode="box">',response='lamp: not seen' if rule==B.RULES[0] else 'lamp: frames 1',stage1=d),
                    dict(family='gap',call='<gap a="lamp" b="box" rule="box_grid_5cm">',response='distance 2.00 m')]}))
                values.append(vals)
            path=root/(rule+'.jsonl');path.write_text('\n'.join(json.dumps(v) for v in values));files.append(path)
        r=B.analyse(files,items)
        self.assertAlmostEqual(r['paired_all']['delta'],.2)
        self.assertEqual(r['null_argmax']['not_seen_reads'],4)
        self.assertEqual(r['candidates_argmax']['metre_items'],2)
        self.assertEqual(r['candidates_argmax']['gap_errors'][0]['absolute_error_m'],0)
        self.assertEqual(r['paired_all']['rooms'],2)
        self.assertEqual(r,B.analyse(files,items))

if __name__=='__main__':unittest.main(verbosity=2)
