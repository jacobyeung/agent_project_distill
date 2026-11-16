import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import f1f2 as F


def fixture(step, away=1, main=1, toward=1, alike=False):
    rows=[]
    for task in F.F1_TYPES:
        for i in range(3):
            rows.append(dict(id=task+str(i),family='main',task_type=task,level=None,
                room=str(i),scene=str(i),prediction='x',answer_content='x',score=main,
                scoring_basis='answer',budget=2048,step=step,pair_id=None,
                count_kind='single' if task=='object_counting' else None))
    for level in F.LEVELS:
        for i in range(3):
            for family,score,answer in [('away',away,'left'),('forward',toward,'left' if alike else 'right')]:
                rows.append(dict(id=family+level+str(i),family=family,
                    task_type='object_rel_direction_'+level,level=level,room=str(i),scene=str(i),
                    prediction=answer,answer_content=answer,score=score,scoring_basis='answer',
                    budget=2048,step=step,pair_id=level+str(i),count_kind=None))
    return rows


class VerdictTests(unittest.TestCase):
    def test_step100_has_no_verdict(self):
        r=F.evaluate(fixture(544),fixture(100),100,strict=False)
        self.assertNotIn('verdict',r)
        self.assertFalse(r['f1_fail']);self.assertFalse(r['f2_fail'])
        self.assertIsNone(r['guards']['total']['passes'])
        self.assertTrue(r['guards']['single']['passes'])

    def test_f1_stop_dominates(self):
        r=F.evaluate(fixture(544),fixture(200,main=0),200,strict=False)
        self.assertEqual(r['verdict'],'STOP')
        self.assertTrue(r['f1_fail'])

    def test_continue(self):
        self.assertEqual(F.evaluate(fixture(544),fixture(200),200,strict=False)['verdict'],'CONTINUE')

    def test_f2_fail_without_trend_stops(self):
        r=F.evaluate(fixture(544),fixture(200,away=0),200,fixture(100),strict=False)
        self.assertTrue(r['f2_fail']);self.assertEqual(r['verdict'],'STOP')

    def test_trend_extension(self):
        r=F.evaluate(fixture(544,away=0),fixture(200,alike=True),200,fixture(100,away=0),strict=False)
        self.assertFalse(r['f1_fail']);self.assertTrue(r['f2_fail'])
        self.assertEqual(r['verdict'],'CONTINUE_TO_400')

    def test_trend_strict_equalities_and_two_levels(self):
        base=dict.fromkeys(F.LEVELS,0);old=dict.fromkeys(F.LEVELS,50)
        for new,expected in [({'easy':60,'medium':60,'hard':50},'CONTINUE_TO_400'),
                             ({'easy':60,'medium':50,'hard':50},'STOP'),
                             ({'easy':60,'medium':60,'hard':0},'STOP')]:
            self.assertEqual(F.stop_rule(False,True,new,old,base),expected)
        with self.assertRaisesRegex(ValueError,'Step-100'):
            F.stop_rule(False,True,base,None,base)

    def test_bootstrap_sign_zero_boundary_and_cluster_weighting(self):
        a=fixture(544)[:3];b=copy.deepcopy(a)
        for r in b:r['score']=0
        self.assertEqual(F.bootstrap(b,a)['ci95_pp'],[-100,-100])
        self.assertEqual(F.bootstrap(a,a)['ci95_pp'],[0,0])
        rows=[dict(a[0],id='x',room='big',score=1),dict(a[0],id='y',room='big',score=1),
              dict(a[0],id='z',room='small',score=0)]
        result=F.accuracy(rows)
        self.assertAlmostEqual(result['accuracy_pct'],200/3)
        self.assertEqual(result['rooms'],2);self.assertEqual(result['replicates'],10000)
        self.assertEqual(result['ci95_pct'],[0,100])

    def test_f2_interval_and_alike_boundaries(self):
        actual=F.bootstrap
        def boundary(rows,b=None):
            result=actual(rows,b)
            if b is None and rows[0]['family']=='away':
                result['ci95_pp']=[F.THRESHOLDS[rows[0]['level']],100]
            return result
        with patch.object(F,'bootstrap',side_effect=boundary):
            r=F.evaluate(fixture(544),fixture(100),100,strict=False)
        self.assertTrue(r['f2_fail'])
        rows=fixture(100)
        # Exactly 20% passes, using five complete pairs.
        away=[r for r in rows if r['family']=='away'][:5]
        forward=[r for r in rows if r['family']=='forward'][:5]
        forward[0]['answer_content']='left'
        self.assertEqual(F.twins(away+forward)['alike_pct'],20)

    def test_toward_regression(self):
        r=F.evaluate(fixture(544),fixture(100,toward=0),100,strict=False)
        self.assertTrue(r['f2']['toward_delta']['fail'])

    def test_refuse_bad_records(self):
        a=fixture(544);b=fixture(100)
        for field,value in [('room','bad'),('scene','bad'),('task_type','bad')]:
            changed=copy.deepcopy(b);changed[0][field]=value
            with self.assertRaises(ValueError):F.align(a,changed)
        for bad in [b+b[:1],b[1:]]:
            with self.assertRaises(ValueError):F.align(a,bad)
        with self.assertRaises(ValueError):F.evaluate(a,b,200,strict=False)
        b[0]['score']=float('nan')
        with self.assertRaises(ValueError):F.index(b)

    def test_twins_refuse_missing_and_duplicate(self):
        rows=fixture(100)
        with self.assertRaises(ValueError):F.twins(rows[:-1])
        twin=next(r for r in rows if r['family']=='away')
        with self.assertRaises(ValueError):F.twins(rows+[twin])

    def test_missing_answers_do_not_count_as_answered_alike(self):
        rows=fixture(100)
        for r in rows:
            if r['family'] in ('away','forward'):r['answer_content']=None
        result=F.twins(rows)
        self.assertEqual(result['alike_pct'],0)
        self.assertEqual(result['unparsed_pairs'],9)

    def test_optional_camera_is_outside_verdict(self):
        b=fixture(100)
        camera=dict(b[0],family='camera')
        result=F.evaluate(fixture(544),b+[camera],100,strict=False)
        self.assertFalse(result['f1_fail'])

    def test_bootstrap_is_exact_reviewed_function(self):
        import ast
        import room_bootstrap
        source=Path('kit/reader/work/vendor/r5/report.py').read_text()
        candidate=Path(room_bootstrap.__file__).read_text()
        def body(s):return ast.dump(next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='paired'),include_attributes=False)
        self.assertEqual(body(source),body(candidate))

    def test_accepted_evidence(self):
        rows=F.load('evidence/A544.jsonl')
        result=F.twins(rows)
        self.assertEqual(result['pairs'],150);self.assertEqual(result['alike_pairs'],74)
        with self.assertRaises(ValueError):F.evaluate(rows,fixture(100),100)


if __name__=='__main__':unittest.main()
