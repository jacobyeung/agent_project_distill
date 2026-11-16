import offline_guard
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import f1f2 as F


def fixture(step, away=None, main=1, toward=1, alike=False):
    if away is None:
        away = {k: v/100 for k, v in F.BASELINE_AWAY.items()} if step == 544 else 1
    rows=[]
    for task in F.F1_TYPES+F.F1_INFORMATION_TYPES:
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
                    prediction=answer,answer_content=answer,score=(score[level] if isinstance(score,dict) else score),scoring_basis='answer',
                    budget=2048,step=step,pair_id=level+str(i),count_kind=None))
    return rows


class VerdictTests(unittest.TestCase):
    def test_step100_has_no_verdict(self):
        r=F.evaluate(fixture(544),fixture(100,main=0),100,strict=False)
        self.assertIsNone(r['verdict'])
        self.assertEqual(r['reasons'],['step 100 gives no verdict'])
        self.assertTrue(r['f1_fail']);self.assertFalse(r['f2_fail'])
        self.assertIsNone(r['guards']['total']['passes'])
        self.assertFalse(r['guards']['single']['passes'])

    def test_f1_stop_dominates(self):
        r=F.evaluate(fixture(544),fixture(200,main=0),200,strict=False)
        self.assertEqual(r['verdict'],'STOP')
        self.assertTrue(r['f1_fail'])

    def test_continue(self):
        self.assertEqual(F.evaluate(fixture(544),fixture(200),200,strict=False)['verdict'],'CONTINUE')

    def test_f1_has_seven_types_and_extras_cannot_stop(self):
        for task in F.F1_INFORMATION_TYPES:
            b=fixture(200)
            for row in b:
                if row['task_type']==task:row['score']=0
            result=F.evaluate(fixture(544),b,200,strict=False)
            self.assertEqual(len(result['f1']),7)
            self.assertEqual(result['f1_information_only'][task]['ci95_pp'],[-100,-100])
            self.assertFalse(result['f1_fail']);self.assertEqual(result['verdict'],'CONTINUE')

    def test_each_registered_f1_type_can_stop(self):
        for task in F.F1_TYPES:
            b=fixture(200)
            for row in b:
                if row['family']=='main' and row['task_type']==task:row['score']=0
            result=F.evaluate(fixture(544),b,200,strict=False)
            self.assertTrue(result['f1'][task]['fail'])
            self.assertEqual(result['verdict'],'STOP')

    def test_cli_accepts_all_steps_and_prints_both_readings(self):
        import contextlib,io,sys
        for step in F.READ_STEPS:
            with self.subTest(step=step):
                prev=fixture(F.PREVIOUS_STEP[step]) if step in F.PREVIOUS_STEP else None
                result=F.evaluate(fixture(544),fixture(step),step,prev,strict=False)
                output=io.StringIO()
                argv=['f1f2.py','--a','a','--b','b','--step',str(step)]
                rows=[fixture(544),fixture(step)]
                if prev is not None:argv+=['--prev','prev'];rows.append(prev)
                with patch.object(sys,'argv',argv),patch.object(F,'load',side_effect=rows), \
                     patch.object(F,'evaluate',return_value=result) as evaluate,contextlib.redirect_stdout(output):
                    F.main()
                self.assertEqual(evaluate.call_args.args,(rows[0],rows[1],step,prev))
                self.assertIn('f2_point_estimate_information_only',json.loads(output.getvalue()))

    def test_later_reads_f1_stops_independently_of_f2(self):
        for step in (400,600,800):
            for f1_fail in (False,True):
                for f2_fail in (False,True):
                    with self.subTest(step=step,f1_fail=f1_fail,f2_fail=f2_fail):
                        b=fixture(step,main=0 if f1_fail else 1,alike=f2_fail)
                        r=F.evaluate(fixture(544),b,step,fixture(F.PREVIOUS_STEP[step]),strict=False)
                        self.assertEqual(r['f1_fail'],f1_fail);self.assertEqual(r['f2_fail'],f2_fail)
                        self.assertEqual(r['verdict'],'STOP' if f1_fail else 'CONTINUE')

    def test_point_reading_is_information_only(self):
        actual=F.bootstrap
        def interval(rows,b=None):
            result=actual(rows,b)
            if b is None and rows[0]['family']=='away' and rows[0]['step']!=544:
                result['ci95_pp']=[0,100]
            return result
        for step in (200,400,600,800):
            prev=fixture(F.PREVIOUS_STEP[step]) if step in F.PREVIOUS_STEP else None
            b=fixture(step,away=dict(zip(F.LEVELS,(.60,.46,.42))))
            with patch.object(F,'bootstrap',side_effect=interval):
                result=F.evaluate(fixture(544),b,step,prev,strict=False)
                b_low_point=fixture(step,away=.39)
                other=F.evaluate(fixture(544),b_low_point,step,prev,strict=False)
            self.assertTrue(result['f2_fail'])
            self.assertFalse(result['f2_point_estimate_information_only']['fail'])
            self.assertTrue(other['f2_point_estimate_information_only']['fail'])
            self.assertEqual(result['verdict'],other['verdict'])
            self.assertEqual(result['verdict'],'CONTINUE' if step==200 else 'STOP')
            self.assertNotIn('verdict',result['f2_point_estimate_information_only'])
        b=fixture(200,away={k:v/100 for k,v in F.THRESHOLDS.items()})
        result=F.evaluate(fixture(544),b,200,strict=False)
        self.assertFalse(result['f2_point_estimate_information_only']['fail'])

    def test_step200_away_below_baseline_stops(self):
        r=F.evaluate(fixture(544),fixture(200,away=0),200,strict=False)
        self.assertTrue(r['f2_fail']);self.assertEqual(r['verdict'],'STOP')
        for level in F.LEVELS:
            self.assertTrue(any(level in reason and 'away200=' in reason and 'away544=' in reason
                                for reason in r['reasons']))

    def test_step200_f2_failure_with_all_levels_above_continues(self):
        r=F.evaluate(fixture(544),fixture(200,alike=True),200,strict=False)
        self.assertFalse(r['f1_fail']);self.assertTrue(r['f2_fail'])
        self.assertEqual(r['verdict'],'CONTINUE')
        self.assertEqual(r['reasons'],['no stop condition met'])

    def test_step200_equal_one_level_stops_just_above_all_continues(self):
        for level in F.LEVELS:
            means={k:v/100+1e-6 for k,v in F.BASELINE_AWAY.items()}
            means[level]=F.BASELINE_AWAY[level]/100
            r=F.evaluate(fixture(544),fixture(200,away=means),200,strict=False)
            self.assertEqual(r['verdict'],'STOP')
            self.assertTrue(any(level in reason for reason in r['reasons']))
        means={k:v/100+1e-6 for k,v in F.BASELINE_AWAY.items()}
        self.assertEqual(F.evaluate(fixture(544),fixture(200,away=means),200,strict=False)['verdict'],'CONTINUE')

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

    def test_f1_upper_zero_and_just_negative_at_every_read(self):
        actual=F.bootstrap
        for step in (200,400,600,800):
            for upper in (0,-1e-9):
                def boundary(rows,b=None):
                    out=actual(rows,b)
                    if b is not None and rows[0]['task_type']==F.F1_TYPES[0]:
                        out['ci95_pp']=[-1,upper]
                    return out
                with self.subTest(step=step,upper=upper),patch.object(F,'bootstrap',side_effect=boundary):
                    prev=fixture(F.PREVIOUS_STEP[step]) if step in F.PREVIOUS_STEP else None
                    r=F.evaluate(fixture(544),fixture(step),step,prev,strict=False)
                    self.assertEqual(r['verdict'],'STOP' if upper<0 else 'CONTINUE')

    def test_two_levels_below_with_f2_failing_stops(self):
        self.check_later_facing((.9,.9,1),True,'STOP')

    def test_two_levels_below_with_f2_passing_continues(self):
        self.check_later_facing((.9,.9,1),False,'CONTINUE')

    def test_one_level_below_continues(self):
        self.check_later_facing((.9,1,1),True,'CONTINUE')

    def test_two_levels_equal_continues(self):
        self.check_later_facing((1,1,.9),True,'CONTINUE')

    def check_later_facing(self,values,f2_fail,expected):
        for step in (400,600,800):
            with self.subTest(step=step):
                r=F.evaluate(fixture(544),fixture(step,away=dict(zip(F.LEVELS,values)),alike=f2_fail),
                             step,fixture(F.PREVIOUS_STEP[step]),strict=False)
                self.assertEqual(r['f2_fail'],f2_fail);self.assertEqual(r['verdict'],expected)
                if expected=='STOP':
                    self.assertEqual(len(r['reasons']),2)
                    for level in ('easy','medium'):
                        self.assertTrue(any(level in reason and f'away{step}=90.0' in reason
                            and f'away{F.PREVIOUS_STEP[step]}=100.0' in reason for reason in r['reasons']))

    def test_prev_missing_refused(self):
        for step in F.PREVIOUS_STEP:
            with self.subTest(step=step),self.assertRaisesRegex(ValueError,'--prev'):
                F.evaluate(fixture(544),fixture(step),step,strict=False)

    def test_prev_wrong_step_refused(self):
        for step in F.PREVIOUS_STEP:
            with self.subTest(step=step),self.assertRaisesRegex(ValueError,'Wrong step'):
                F.evaluate(fixture(544),fixture(step),step,fixture(100),strict=False)

    def test_prev_wrong_membership_or_metadata_refused(self):
        for step in F.PREVIOUS_STEP:
            for mode in ('missing','duplicate','metadata'):
                prev=fixture(F.PREVIOUS_STEP[step])
                if mode=='missing':prev=prev[1:]
                elif mode=='duplicate':prev+=prev[:1]
                else:prev[0]['scene']='wrong'
                with self.subTest(step=step,mode=mode),self.assertRaises(ValueError):
                    F.evaluate(fixture(544),fixture(step),step,prev,strict=False)

    def test_baseline_544_must_be_38_20_6(self):
        for level in F.LEVELS:
            means={k:v/100 for k,v in F.BASELINE_AWAY.items()};means[level]+=1e-6
            with self.subTest(level=level),self.assertRaisesRegex(ValueError,'38 / 20 / 6'):
                F.evaluate(fixture(544,away=means),fixture(200),200,strict=False)

    def test_alike_exactly_twenty_passes_above_fails(self):
        actual=F.twins
        for alike in (20,20.0001):
            def boundary(rows):
                return dict(actual(rows),alike_pct=alike)
            with patch.object(F,'twins',side_effect=boundary):
                r=F.evaluate(fixture(544),fixture(200),200,strict=False)
            self.assertEqual(r['f2_fail'],alike>20)
            self.assertEqual(r['verdict'],'CONTINUE')

    def test_toward_interval_upper_zero_passes_negative_fails(self):
        actual=F.bootstrap
        for upper in (0,-1e-9):
            def boundary(rows,b=None):
                out=actual(rows,b)
                if b is not None and rows[0]['family']=='forward':out['ci95_pp']=[-1,upper]
                return out
            with patch.object(F,'bootstrap',side_effect=boundary):
                r=F.evaluate(fixture(544),fixture(200),200,strict=False)
            self.assertEqual(r['f2_fail'],upper<0)
            self.assertEqual(r['verdict'],'CONTINUE')

    def test_final_export_gives_final_and_f2_decision(self):
        for fails in (False,True):
            r=F.evaluate(fixture(544),fixture(1000,main=0,alike=fails),1000,fixture(800),strict=False)
            self.assertEqual(r['verdict'],'FINAL');self.assertTrue(r['f1_fail'])
            self.assertEqual(r['f2_decision'],'FAIL' if fails else 'PASS')
            self.assertEqual(r['facing_comparison']['reference_step'],800)
            self.assertEqual(set(r['facing_comparison']['levels']),set(F.LEVELS))
            self.assertEqual(len(r['f1']),7)

    def test_all_fired_rules_are_reported(self):
        r=F.evaluate(fixture(544),fixture(200,main=0,away=0),200,strict=False)
        self.assertEqual(len(r['reasons']),10)
        for task in F.F1_TYPES:self.assertTrue(any(task in reason for reason in r['reasons']))


if __name__=='__main__':unittest.main()
