"""Partial report and refusal disclosure regressions."""
from pathlib import Path
from unittest.mock import patch
import sys,unittest,uuid
import numpy as np
B=Path(__file__).resolve().parents[1];sys.path.append(str(B/'code'))
import report
from adapter import dump,pin
from scorer import TYPES,GROUPS,collapse

class ReportChanges(unittest.TestCase):
    def row(self,t,i,score=1.,refused=False):
        return dict(key=t+str(i),question_type=t,arm='native',score=score,
            scene='scene'+str(i%3)+'_00',room='scene'+str(i%3),
            calls=[dict(name='depth_at',kind='error',refused=True)] if refused else [],
            answer='A' if score else '',forced_close=False,no_final_answer=not bool(score),
            geometry_refusal=None,seconds=1.)
    def build(self,rows,complete=False):
        root=B/'work'/('report_d_'+uuid.uuid4().hex);root.mkdir()
        dump(root/'truth.json',{r['key']:dict(scene=r['scene'],room=r['room']) for r in rows})
        bound=dict(inputs={'SCORES.json':pin(root/'truth.json')})
        dump(root/'bound.json',bound)
        dump(root/'merged.json',dict(bound=pin(root/'bound.json'),synthetic=True,items=rows,
            complete=complete,missing=[],completions=[]))
        with patch.object(report,'validate_bound',return_value=bound):
            value=report.build(root/'merged.json',root)
        return value,(root/'REPORT.md').read_text()
    def test_partial_type_score_count_and_scene_bootstrap(self):
        rows=[self.row(TYPES[0],i,float(i%3==0)) for i in range(49)]
        value,text=self.build(rows)
        m=value['per_type'][TYPES[0]]
        self.assertEqual(m['status'],'PARTIAL');self.assertEqual(m['items'],49)
        self.assertAlmostEqual(m['score'],17/49)
        weights=np.random.default_rng(544).multinomial(3,[1/3]*3,size=2000)
        boot=(weights@np.array([17.,0.,0.]))/(weights@np.array([17.,16.,16.]))
        expected=np.quantile(boot,[.025,.975])
        self.assertEqual([m['scene_interval']['low'],m['scene_interval']['high']],list(expected))
        line=next(x for x in text.splitlines() if x.startswith('| '+TYPES[0]+' |'))
        for token in ('49/50','34.69%','PARTIAL','['):self.assertIn(token,line)
        self.assertIsNone(value['primary']['score'])
    def test_partial_subtask_uses_only_completed_items(self):
        name,types=next((g,ts) for g,ts in GROUPS.items() if len(ts)==3)
        rows=[self.row(types[0],i,1.) for i in range(3)]+[self.row(types[1],0,0.)]
        value,text=self.build(rows);m=value['subtasks'][name]
        self.assertEqual(m['score'],.75);self.assertEqual(m['items'],4)
        self.assertIsNotNone(m['scene_interval']);self.assertIsNotNone(m['room_interval'])
        line=next(x for x in text.splitlines() if x.startswith('| '+name+' |'))
        for token in ('4/150','75.00%','PARTIAL','['):self.assertIn(token,line)
    def test_complete_subtask_preserves_v1c_estimator_and_interval(self):
        import types
        old=types.ModuleType('v1c_report')
        source=B.parent/'03_vsti_c/code/report.py'
        exec(compile(source.read_text(),str(source),'exec'),old.__dict__)
        name,ts=next((g,ts) for g,ts in GROUPS.items() if len(ts)==3)
        rows=[self.row(t,i,float((i+j)%4==0)) for j,t in enumerate(ts) for i in range(50)]
        self.assertEqual(report.estimate(rows,ts),old.estimate(rows,ts))
        self.assertEqual(report.interval(rows,ts),old.interval(rows,ts))
        self.assertEqual(report.interval(rows,ts,'room'),old.interval(rows,ts,'room'))
    def test_empty_rows_have_no_imputed_score(self):
        value,text=self.build([])
        for m in list(value['per_type'].values())+list(value['subtasks'].values()):
            self.assertEqual(m['items'],0);self.assertEqual(m['status'],'PARTIAL')
            self.assertIsNone(m['score']);self.assertIsNone(m['scene_interval'])
        headline=next(x for x in text.splitlines() if x.startswith('Primary:'))
        self.assertIn('Primary: PARTIAL',headline)
        for name in GROUPS:self.assertIn(name,headline)
        self.assertIn('0/50',text)
    def test_primary_requires_all_five_complete_subtasks(self):
        rows=[self.row(t,i,float(j%2)) for j,t in enumerate(TYPES) for i in range(50)]
        partial,text=self.build(rows[:-1],complete=True)
        missing=next(g for g,ts in GROUPS.items() if TYPES[-1] in ts)
        self.assertEqual(partial['primary']['incomplete_subtasks'],[missing])
        self.assertIsNone(partial['primary']['score'])
        headline=next(x for x in text.splitlines() if x.startswith('Primary:'))
        self.assertIn('PARTIAL; incomplete subtasks: '+missing,headline)
        full,text=self.build(rows,complete=True)
        self.assertAlmostEqual(full['primary']['score'],collapse({t:float(j%2) for j,t in enumerate(TYPES)})['primary'])
        self.assertIsNotNone(full['primary']['scene_interval'])
        self.assertNotIn('PARTIAL',next(x for x in text.splitlines() if x.startswith('Primary:')))
    def test_refusal_distribution_score_and_wording(self):
        rows=[self.row(TYPES[0],0,1.,True),self.row(TYPES[0],1,0.,True),self.row(TYPES[0],2,1.)]
        value,text=self.build(rows);cost=value['per_type'][TYPES[0]]['refusal_cost']
        self.assertEqual(cost['items'],2);self.assertEqual(cost['answers'],{'A':1,'<none>':1})
        self.assertEqual(cost['score'],.5);self.assertEqual(len(cost['per_item']),2)
        self.assertEqual(value['refusal_note'],report.REFUSAL_NOTE)
        self.assertLess(text.index(report.REFUSAL_NOTE),text.index('| Type | Forced closes'))
        self.assertLess(text.index(report.REFUSAL_NOTE),text.index('Refusal-answer distributions'))
        for phrase in ("runtime's recoverable error format (trace 3.13)",'0 of 165 checked by the reviewer','step 544 has no trained recovery after a refused call'):
            self.assertIn(phrase,text);self.assertIn(phrase,(B/'out/LEGALITY.md').read_text())
        self.assertIn('50.00%',text)

if __name__=='__main__':unittest.main()
