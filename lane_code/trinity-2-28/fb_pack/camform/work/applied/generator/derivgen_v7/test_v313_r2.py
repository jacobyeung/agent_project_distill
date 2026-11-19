"""Review regressions: inspect serialized text, independent of formatter internals."""
import copy
import json
import os
import re
import unittest
from collections import Counter
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import numpy as np
from derivgen.ground_v312_quality import shuffled_item
from derivgen.ground_v313 import witness_pair
from test_v313 import ROOT, backend, session


def points(body, role):
    pattern = r'^P\d+: (.+?) '+role+r' cam(\d+) \(([^)]+)\) m; f1 \(([^)]+)\) m$'
    return [(name, int(frame), tuple(map(Decimal, cam.split(', '))),
             tuple(map(Decimal, f1.split(', '))))
            for name, frame, cam, f1 in re.findall(pattern, body, re.M)]


def distance(a, b):
    return sum((x-y)**2 for x,y in zip(a,b)).sqrt().quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN)


class PrintedFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ.get('V313_FIXTURES', ROOT/'out/fixtures_r2'))
        cls.rows = {p.stem:[json.loads(line) for line in p.read_text().splitlines()]
                    for p in cls.path.glob('*.jsonl')}

    def test_every_row_and_gap_from_printed_points(self):
        self.assertEqual(len(self.rows),10)
        counts = Counter()
        for family, rows in self.rows.items():
            self.assertEqual(len(rows),20)
            for row in rows:
                self.assertFalse(row['training_admitted'])
                self.assertLessEqual(row['suffix_tokens'],5000)
                for event in row['events']:
                    body=event['response']; ps=points(body,'nearest point')
                    if not ps:continue
                    if event['call'].startswith('<gap '):
                        values=[]
                        for a,b in zip(ps[::2],ps[1::2]):
                            value=distance(a[3],b[3]);values.append((b[0],value))
                            prefix='' if len(ps)==2 else re.escape(b[0])+': '
                            printed=re.search(r'^'+prefix+r'(\d+\.\d{2}) m$',body,re.M)
                            self.assertIsNotNone(printed)
                            self.assertEqual(value,Decimal(printed[1]),row['qid'])
                            counts['mask_pairs']+=1
                        if len(ps)>2:
                            minimum=min(v for _,v in values)
                            names=','.join('"'+n+'"' for n,v in values if v==minimum)
                            self.assertIn(f'min {names} {minimum:.2f} m',body)
                    else:
                        value=distance(ps[0][3],ps[1][3])
                        for label in ['visible pair distance','full surface gap']:
                            printed=re.search(r'^'+label+r' (\d+\.\d{2}) m$',body,re.M)
                            if printed:self.assertEqual(value,Decimal(printed[1]),row['qid'])
                        counts['surface_pairs']+=1
        self.assertEqual(counts,{'mask_pairs':60,'surface_pairs':40})

    def test_every_surface_facing_membership_and_common_frame(self):
        for family in ['surface_pair','surface_pair_full']:
            for row in self.rows[family]:
                body=row['events'][-1]['response']
                cs=points(body,'support centroid');ps=points(body,'nearest point')
                self.assertEqual(len(cs),2);self.assertEqual(len(ps),2)
                direction=[b-a for a,b in zip(cs[0][3],cs[1][3])]
                self.assertTrue(any(direction))
                for j,(c,p) in enumerate(zip(cs,ps)):
                    self.assertEqual(c[:2],p[:2])
                    dot=sum((x-y)*d*(1 if j==0 else -1) for x,y,d in zip(p[3],c[3],direction))
                    self.assertGreaterEqual(dot,0,row['qid'])
                    audit=row['surface_audit'];pair=audit['pair']
                    cloud=np.array(audit['surfaces'][p[0]][str(p[1])])
                    raw=np.array(pair['positions'][j])
                    self.assertTrue(np.any(np.all(cloud==raw,axis=1)))
                    from test_v313 import Geometry
                    for raw_point,printed in [(raw,p),(np.median(cloud,axis=0),c)]:
                        cam,f1=backend.public_centres(Geometry(),p[1],raw_point)
                        self.assertEqual(tuple(Decimal(backend.number(x)) for x in cam),printed[2])
                        self.assertEqual(tuple(Decimal(backend.number(x)) for x in f1),printed[3])
                if family=='surface_pair_full':
                    self.assertTrue(pair['full_surface_authority'])
                    A,B=[np.array(audit['surfaces'][n][str(f)]) for n,f in zip(['stand','face'],pair['frames'])]
                    self.assertAlmostEqual(np.linalg.norm(A[:,None]-B[None,:],axis=2).min(),pair['full_surface_distance_m'])
                else:self.assertIn('full surface gap unavailable',body)

    def test_shuffle_letter_balance_and_answer_mapping(self):
        for family in ['appearance_order','relative_gap_witness']:
            rows=self.rows[family]
            self.assertEqual(Counter(r['answer'] for r in rows),{'A':10,'B':10})
            for r in rows:
                options=['A. face','B. far'] if family=='relative_gap_witness' else ['A. chair, table','B. table, chair']
                source=dict(qid=r['qid'],type=r['type'],question=r['question'],options=options,gt_answer='A')
                expected=shuffled_item(source)
                self.assertEqual(r['options'],expected['options'])
                self.assertEqual(r['answer'],expected['gt_answer'])
                self.assertEqual(r['options'][ord(r['answer'])-65][3:],r['answer_content'])
                if family=='relative_gap_witness':
                    candidates=re.findall(r' b="([^"]+)"',r['events'][-1]['call'])
                    self.assertEqual(candidates,[x[3:] for x in r['options']])
                else:
                    first=r['program_audit']['first_frames']
                    self.assertEqual(r['answer_content'],', '.join(sorted(first,key=first.get)))

    def test_counting_singular_plural(self):
        for r in self.rows['counting']:
            n=int(r['answer']);noun='instance' if n==1 else 'instances'
            self.assertIn(f'The tool found {n} observed {noun}.',r['suffix'])

    def test_benchmark_question_templates(self):
        absolute='Measuring from the closest point of each object, what is the distance between the stand and the face (in meters)?'
        for family,rows in self.rows.items():
            for r in rows:
                if family=='gap_witness' or family.startswith('surface_pair'):
                    self.assertEqual(r['question'],absolute)
                elif family in ('counting','instances','unresolved'):
                    self.assertEqual(r['question'],'How many chair(s) do we have in this room?')
                elif family=='appearance_order':
                    self.assertEqual(r['question'],'What will be the first-time appearance order of the following categories in the video: chair, table?')
                elif family=='relative_gap_witness':
                    names=', '.join(o[3:] for o in r['options'])
                    self.assertEqual(r['question'],f'Measuring from the closest point of each object, which of these objects ({names}) is the closest to the stand?')

    def test_extent_fixtures_byte_identical(self):
        self.assertEqual((self.path/'extent_ends.jsonl').read_bytes(),
                         (ROOT/'out/fixtures/extent_ends.jsonl').read_bytes())


class SurfaceAdmissionTests(unittest.TestCase):
    def prepared(self):
        s=session(keypoint_calls=True)
        for n in ['stand','face']:s.execute(f'<ground obj="{n}">')
        result=dict(status='ok',observed_surface_points=True,
                    **witness_pair(backend,s.objects['stand'],s.objects['face']))
        s.keypoint_provider=lambda *_:result
        return s,result

    def test_far_side_member_and_nonmember_refuse_atomically(self):
        for nonmember in [False,True]:
            s,r=self.prepared()
            # A real member on the far side must fail independently of membership.
            cloud=np.array(s.objects['stand']['points'][str(r['frames'][0])])
            r['positions'][0]=cloud[np.argmin(cloud[:,0])].copy()
            if nonmember:r['positions'][0]+=np.array([-.001,0,0])
            r['distance_m']=float(np.linalg.norm(np.subtract(*r['positions'])))
            before=copy.deepcopy(s.registry._points)
            self.assertEqual(s.execute('<surface_pair a="stand" b="face" mode="closest_visible">'),'unavailable')
            self.assertEqual(s.registry._points,before)

    def test_full_gap_requires_authority_and_visibility(self):
        for authority,visible in [(False,True),(True,False),(True,True)]:
            s,r=self.prepared()
            r.update(full_surface_distance_m=r['distance_m'],true_closest_visible=visible)
            if authority:r['full_surface_authority']='synthetic complete reference'
            body=s.execute('<surface_pair a="stand" b="face" mode="closest_visible">')
            self.assertEqual('full surface gap unavailable' in body,not(authority and visible))


if __name__=='__main__':unittest.main()
