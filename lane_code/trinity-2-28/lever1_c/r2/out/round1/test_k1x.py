"""Tests for the registered parity stop; no claim of raw geometry replay."""
import ast
import hashlib
import json
import math
from pathlib import Path
import unittest

import numpy as np
import k1x as K


class ParityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads((K.ROOT/'out/K1X.json').read_text())
        cls.copies=json.loads((K.ROOT/'vendor/COPIES.json').read_text())

    def test_copies_change_only_root(self):
        for record in self.copies:
            original=Path(record['source']).read_text()
            copied=Path(record['copy']).read_text()
            expected=original
            if Path(record['copy']).name.endswith('harness.py'):
                expected=expected.replace('ROOT = Path(__file__).resolve().parent',f'ROOT = Path({str(K.ROOT)!r})')
                expected=expected.replace(f'assert ROOT == Path({str(Path(record["source"]).parent)!r})',
                                          f'assert ROOT == Path({str(K.ROOT)!r})')
            self.assertEqual(expected,copied)
            self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),record['source_sha256'])
            self.assertEqual(hashlib.sha256(copied.encode()).hexdigest(),record['copy_sha256'])

    def test_copied_scorers_per_item(self):
        for record in self.copies:
            if Path(record['copy']).name=='gravity_guard.py':
                continue
            original=K.declaration(record['source'],'mra')
            copied=K.declaration(record['copy'],'mra')
            for rows in self.result['parity_rows'].values():
                for row in rows:
                    p,t=row['source_prediction'],row['corrected_label']
                    self.assertEqual(original(p,t),copied(p,t))
                    self.assertEqual(copied(p,t),row['source_score'])

    def test_strict_thresholds_and_refusals(self):
        self.assertEqual(K.mra(None,1),0)
        self.assertEqual(K.mra(float('nan'),1),0)
        self.assertEqual(K.mra(1,0),0)
        self.assertEqual(K.mra(1.5,1),0)
        self.assertEqual(K.mra(1,1),1)
        # Exactly 25% relative error excludes the 75% threshold.
        self.assertEqual(K.mra(1.25,1),.5)

    def test_guard_copy_synthetic_rotations(self):
        class Error(ValueError):
            pass
        source=next(r['source'] for r in self.copies if Path(r['copy']).name=='gravity_guard.py')
        threshold=next(ast.literal_eval(n.value) for n in ast.parse(Path(source).read_text()).body
                       if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='UP_PLANE_MIN' for t in n.targets))
        bindings=dict(GeometryError=Error,UP_PLANE_MIN=threshold)
        old=K.declaration(source,'validate_up_convention',bindings)
        new=K.declaration(K.ROOT/'vendor/gravity_guard.py','validate_up_convention',bindings)
        for angle in [-math.pi/2,math.pi/2,0,math.pi/12,-math.pi/12]:
            c,s=math.cos(angle),math.sin(angle)
            rotation=np.array([[1,0,0],[0,c,-s],[0,s,c]])
            outcomes=[]
            for function in (old,new):
                try:
                    function(np.repeat(rotation[None],32,axis=0))
                    outcomes.append('accepted')
                except Error as exc:
                    outcomes.append(str(exc))
            self.assertEqual(*outcomes)
            if angle==math.pi/2:
                self.assertEqual(outcomes[0],K.REFUSAL)
            if angle==-math.pi/2:
                self.assertEqual(outcomes[0],'accepted')

    def test_bootstrap_identity_and_room_weighting(self):
        equal=[dict(room='a',score=.6),dict(room='b',score=.6)]
        result=K.bootstrap(equal)
        self.assertAlmostEqual(result['mean'],60)
        np.testing.assert_allclose(result['ci95'],[60,60])
        unequal=[dict(room='a',score=0)]+[dict(room='b',score=1)]*3
        result=K.bootstrap(unequal)
        self.assertEqual(result['mean'],75)
        self.assertEqual(result['ci95'],[0,100])
        self.assertEqual(result,K.bootstrap(unequal))

    def test_reference_targets_and_guard_attribution(self):
        checks={r['key']:r for r in self.result['parity']}
        for name in ['heldout_served_gt_masks','heldout_gt_geometry']:
            self.assertTrue(checks[name]['passed'])
        for name,expected in [('train_deployed_masks',56.48987463837995),('train_gt_masks',73.6162005785921)]:
            self.assertFalse(checks[name]['passed'])
            self.assertAlmostEqual(checks[name]['observed'],expected)
        for item,total in zip(self.result['guard_attribution'],[2.9,3.7]):
            self.assertEqual(item['affected_rows'],12)
            self.assertAlmostEqual(item['removed_score_sum'],total)
            self.assertAlmostEqual(item['original']-item['reviewed'],100*total/1037)
            self.assertEqual({r['capture'] for r in item['per_row']},
                             {'scannetpp/0f69aefe3d','scannetpp/2c7c10379b'})

    def test_registered_rows_labels_and_refusals(self):
        labels={r['id']:r for r in map(json.loads,Path('/scratch/jjyeung/n30_mirror/gt_audit/gt_audit/work/k1audit/K1_LABELS_CORRECTED.jsonl').read_text().splitlines())}
        gdpath=Path('/scratch/jjyeung/orch_n30/k1_ops3/work/e3gd/out/PER_ITEM.jsonl')
        gd={}
        with gdpath.open() as stream:
            for line in stream:
                if '"arm": "GD_reviewed"' in line:
                    r=json.loads(line)
                    if r['type']=='object_abs_distance':
                        gd[r['row_id']]=r
                        self.assertEqual(K.mra(r['pred'],r['gt']),r['mra'])
        for name,rows in self.result['parity_rows'].items():
            self.assertEqual(len(rows),216 if name.startswith('heldout') else 1037)
            self.assertEqual(len({r['row_id'] for r in rows}),len(rows))
            for r in rows:
                self.assertEqual(r['corrected_label'],labels[r['row_id']]['corrected'])
                if r['reviewed_guard_refused']:
                    self.assertIn(K.REFUSAL,gd[r['row_id']]['refusal_code'])
                    self.assertIsNone(gd[r['row_id']]['pred'])
                    self.assertEqual(r['score'],0)
                    self.assertIsNone(r['prediction'])

    def test_no_post_gate_results(self):
        self.assertEqual(self.result['status'],'PARITY_STOP')
        self.assertEqual(len(self.result['registered_cells']),16)
        for row in self.result['registered_cells']:
            self.assertEqual(row['status'],K.STOP)
        for contrast in self.result['contrasts'].values():
            self.assertEqual(contrast['verdict'],'WITHHELD')
            self.assertIsNone(contrast['estimate'])
        self.assertFalse(self.result['statistics']['contrasts_evaluated'])

    def test_report_length(self):
        self.assertLessEqual(len((K.ROOT/'out/REPORT_R2.md').read_text().splitlines()),100)


if __name__=='__main__':
    unittest.main()
