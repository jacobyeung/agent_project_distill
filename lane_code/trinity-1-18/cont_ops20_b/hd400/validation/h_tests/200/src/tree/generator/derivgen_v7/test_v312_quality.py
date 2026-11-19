"""Production-defect regressions; CPU-only, small deterministic fixtures."""
import copy
from collections import Counter
import json
from pathlib import Path
import unittest
import numpy as np
from test_v312_ground import item
from derivgen.ground_v312 import RowRefusal, direct_continuation, render, Session, select_balanced
from derivgen.ground_v312_quality import (shuffled_item, question_identity, deduplicate,
    miss_candidates, validate_join, set_report)
from derivgen.ground_v312_degenerate import degeneracy_reasons, overlaps


def joined(q, body):
    q.update(scene='s',frame_indices=list(range(32)),gt_answer='A')
    q['direct_canonical'] = dict(scene=q['scene'],frame_indices=q['frame_indices'],
        question=q['question'],options=q['options'],answer=q['gt_answer'],body=body,
        form='vqa_canonical',source_sha256='fixture')
    return q


def box(c, lengths=(1,1,1), angle=0):
    a=np.deg2rad(angle);axes=[[np.cos(a),np.sin(a),0],[-np.sin(a),np.cos(a),0],[0,0,1]]
    return dict(centroid=c,axesLengths=lengths,normalizedAxes=axes)


class QualityTests(unittest.TestCase):
    def test_shuffle_all_letters_question_final_and_answer(self):
        from test_v312_ground import Geometry, masks, BACKEND
        from derivgen.ground_v312 import load_backend
        backend=load_backend(BACKEND)
        changes=0
        for i in range(24):
            q=item('object_rel_distance');q.update(qid=str(i),gt_answer='A')
            q['question']='Which is closest (face, far)?\nA. face\nB. far'
            shuffled=shuffled_item(q)
            self.assertEqual(shuffled,shuffled_item(q))
            row=render(shuffled,Session(backend,Geometry(),masks),len)
            self.assertEqual(row['answer'],shuffled['gt_answer'])
            self.assertIn('so the answer is '+row['answer']+'.',row['suffix'])
            self.assertTrue(row['suffix'].endswith('<answer>'+row['answer']+'</answer>'))
            self.assertIn('('+', '.join(o.split('. ',1)[1] for o in row['options'])+')', row['question'])
            self.assertEqual(shuffled,shuffled_item(shuffled))
            changes+=shuffled['options']!=q['options']
        self.assertGreater(changes,0)

    def test_shuffle_uniform_and_content_cap(self):
        typ='object_rel_direction_hard';rows=[]
        counts={'front-left':160,'front-right':152,'back-left':29,'back-right':32}
        for i in range(4000):
            q=item(typ);q.update(qid=str(i),question='question '+str(i),scene='s',frame_indices=[1],gt_answer='A' if i%2 else 'B')
            q=shuffled_item(q);q.update(answer=q['gt_answer'],answer_content='front-left' if i%2 else 'front-right')
            rows.append(q)
        selected,report=select_balanced(rows,{typ:{'content':counts}},2000)
        letters=Counter(r['answer'] for r in selected)
        self.assertEqual(len(set(letters.values())),1)
        self.assertEqual(set(letters),set('ABCD'))
        for k,n in Counter(r['answer_content'] for r in selected).items():
            self.assertLessEqual(n,report[typ]['target'][k])

    def test_dedup_cross_types_ids_and_normalized_question(self):
        q=dict(qid='1',type='object_abs_distance',scene='s',frame_indices=[1,2],question=' Distance  A B? ',roles={'a':'A','b':'B'})
        dupe=dict(q,qid='2',type='absolute_distance_object',question='distance a b?')
        unique,report=deduplicate([q,dupe])
        self.assertEqual(len(unique),1)
        self.assertEqual(report,{'absolute_distance_object':1})
        for key,value in [('scene','other'),('frame_indices',[2,1]),('roles',{'a':'A','b':'C'})]:
            self.assertNotEqual(question_identity(q),question_identity(dict(q,**{key:value})))

    def test_relative_balance_option_counts_separate(self):
        rows=[]
        for n in [3,4]:
            for i in range(70):
                rows.append(dict(qid=f'{n}-{i}',type='object_rel_distance',question=f'{n}-{i}',scene='s',frame_indices=[1],
                    answer=chr(65+(i%n)),answer_content='x',options=[f'{chr(65+j)}. object{j}' for j in range(n)]))
        selected,report=select_balanced(rows,{'object_rel_distance':{'letters':dict.fromkeys('ABCD',1)}},120)
        stats=set_report(selected)['object_rel_distance']['by_option_count']
        self.assertEqual(set(stats),{'3','4'})
        for n,entry in stats.items():
            self.assertEqual(set(entry['letters']),set('ABCD'[:int(n)]))
            self.assertEqual(len(set(entry['letters'].values())),1)

    def test_no_join_stays_normal_and_rate_targets_whole_set(self):
        body='Step 1: locate the stand, face and query in the video. Step 2: the query is on my left.'
        rows=[dict(item('object_rel_direction_medium'),qid=str(i)) for i in range(100)]
        for q in rows[:20]:joined(q,body)
        ids,reasons,eligible=miss_candidates(rows,.1)
        self.assertEqual(len(ids),10)
        self.assertEqual(eligible,20)
        self.assertTrue(ids <= {str(i) for i in range(20)})
        self.assertEqual(miss_candidates(rows[20:],.1)[0],set())
        self.assertEqual(miss_candidates(rows,.1)[0],ids)

    def test_join_checks_all_fields_before_shuffle(self):
        q=joined(item('object_rel_direction_medium'),'Step 1: locate all three objects in the frames. Step 2: the query is on my left.')
        for key,value in [('scene','x'),('frame_indices',[9]),('question','x'),('options',['A. right']),('answer','B')]:
            bad=copy.deepcopy(q);bad['direct_canonical'][key]=value
            with self.assertRaisesRegex(RowRefusal,'direct_join_mismatch'):direct_continuation(bad)
        body,answer=direct_continuation(shuffled_item(q))
        self.assertEqual(body,q['direct_canonical']['body'])
        self.assertEqual(answer,shuffled_item(q)['gt_answer'])

    def test_partition_deduplicates_before_scene_build(self):
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import patch
        from derivgen.ground_v312_production import partition
        root=Path(tempfile.mkdtemp(prefix='partition_v2_',dir=Path(__file__).parents[2]/'out'))
        q=dict(item(),scene='s',frame_indices=[1],qid='first')
        source=root/'source.jsonl'
        source.write_text(json.dumps(q)+'\n'+json.dumps(dict(q,qid='second'))+'\n')
        args=SimpleNamespace(output=str(root),direct_joins=None,rkit_root='unused',input=[str(source)],
            prepared_items=True,max_scenes=None,max_rows_per_scene=None)
        with patch('derivgen.ground_v312_production.reference',return_value=(SimpleNamespace(T=None),None,None)):
            receipt=partition(args,{'s':{}},{},{'fingerprint':'fixture'})
        self.assertEqual(receipt['duplicates_removed'],{'object_abs_distance':1})
        config=json.loads(Path(receipt['configs']['s']).read_text())
        self.assertEqual(len(Path(config['items']['path']).read_text().splitlines()),1)

    def test_medium_wording_refuses_behind_right(self):
        q=joined(item('object_rel_direction_medium'),'Step 1: locate the three objects in the frames. Step 2: the query lies 111 degrees left of straight ahead, behind. So the query is on my left.')
        with self.assertRaisesRegex(RowRefusal,'canonical_wording_contradiction'):direct_continuation(q)
        ids,reasons,_=miss_candidates([q],1)
        self.assertFalse(ids)
        self.assertEqual(reasons[q['type']]['canonical_wording_contradiction'],1)
        q['direct_canonical']['body']=q['direct_canonical']['body'].replace('111','33').replace('behind','in front')
        self.assertEqual(direct_continuation(q)[0],q['direct_canonical']['body'])

    def test_hard_and_relative_contradictions(self):
        q=joined(item('object_rel_direction_hard'),'Step 1: locate all three objects in the frames. Step 2: the query lies 111 degrees left of straight ahead, behind. So the query is at my front-left.')
        with self.assertRaisesRegex(RowRefusal,'canonical_wording_contradiction'):direct_continuation(q)
        q=joined(item('object_rel_distance'),'Step 1: locate all objects and compare their distances in the frames. The closest is the far.')
        with self.assertRaisesRegex(RowRefusal,'canonical_wording_contradiction'):direct_continuation(q)

    def test_operand_masks_boxes_containment_and_projected_size(self):
        q=item('object_rel_direction_medium')
        masks={k:np.zeros((2,8,8),bool) for k in ('stand','face','query')}
        boxes={'stand':box([0,0,0]),'face':box([3,0,0]),'query':box([0,3,0])}
        self.assertEqual(degeneracy_reasons(q,boxes,masks),[])
        masks['stand'][0,0,0]=masks['face'][0,0,0]=True
        self.assertIn('operand_mask_overlap',degeneracy_reasons(q,boxes,masks))
        masks['stand'][:]=False
        boxes['query']=box([3.3,0,0])
        self.assertIn('operand_box_overlap',degeneracy_reasons(q,boxes,masks))
        boxes['query']=box([3,0,0],(.2,.2,.2))
        self.assertIn('operand_box_containment',degeneracy_reasons(q,boxes,masks))
        boxes={'stand':box([0,0,0],(4,1,1)),'face':box([3,0,0]),'query':box([0,6,0])}
        self.assertIn('facing_vector_below_object_extent',degeneracy_reasons(q,boxes,masks))
        boxes['stand']=box([0,0,0],(4,1,1),90)
        self.assertNotIn('facing_vector_below_object_extent',degeneracy_reasons(q,boxes,masks))

    def test_lifted_heading_uses_projected_full_extent(self):
        from derivgen.ground_v312_degenerate import lifted_facing_too_short
        q=item('object_rel_direction_medium')
        q['facing_extent_boxes']=[dict(axes_f1=np.eye(3).tolist(),lengths=[4,1,1])]*2
        objects={'stand':{'f1':[0,0,0]},'face':{'f1':[3,0,0]}}
        self.assertTrue(lifted_facing_too_short(q,objects))
        objects['face']['f1']=[0,0,3]
        self.assertFalse(lifted_facing_too_short(q,objects))

    def test_rotated_box_sat_does_not_use_aabb(self):
        a=box([0,0,0],(4,.2,1),45);b=box([0,1,0],(4,.2,1),45)
        self.assertFalse(overlaps(a,b))

    def test_qualifier_must_equal_literal_gt_label(self):
        from types import SimpleNamespace
        from derivgen.ground_v312_io import GTClip
        clip=GTClip.__new__(GTClip)
        clip.programs=SimpleNamespace(T=SimpleNamespace(match_labels=lambda n,ls:['table'] if 'table' in n else ['bed']))
        clip.geo=SimpleNamespace(labels=['table','bed'],ids=[1,2],has=lambda k:True,
            obb={1:box([0,0,0]),2:box([4,0,0])})
        def masks(n):
            mask=np.zeros((32,8,8),bool);mask[0,1,1 if n=='table' else 6]=True
            return mask,mask.any(axis=(1,2)).astype(float)
        clip.masks=masks
        q=item();q['roles']={'a':'wooden table','b':'bed'}
        with self.assertRaisesRegex(RowRefusal,'unresolved_qualified_name'):clip.validate_operands(q)
        q['roles']['a']='table';clip.validate_operands(q)

    def test_best_camera_axes_and_y_sign_independent_expected_values(self):
        from test_v312_ground import Geometry,masks,BACKEND
        from derivgen.ground_v312 import load_backend
        class Known(Geometry):
            def cam(self,k):
                r=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
                if k==4:return np.array([[0.,-1,0],[1,0,0],[0,0,1]])@r,np.array([1.,2,3])
                return r,np.zeros(3)
            def lift(self,k,uv,mode='center'):
                offsets=(uv-np.median(uv,axis=0))/1000
                p=np.column_stack((offsets,np.zeros(len(uv))))+[-3,6,7]
                r,t=self.cam(k)
                return p,(p-t)@r,np.zeros(len(p))
        m,p=masks('stand')
        result=load_backend(BACKEND).lift_object('stand',m,p,Known(),tau=.5)
        self.assertEqual(result['best'],4)
        np.testing.assert_allclose(result['camera'],[4,4,4],atol=1e-12)
        np.testing.assert_allclose(result['f1'],[-3,7,6],atol=1e-12)

    def test_mixed_edge_spreads_use_only_retained_points(self):
        from test_v312_ground import Geometry,BACKEND
        from derivgen.ground_v312 import load_backend
        class Spread(Geometry):
            def lift(self,k,uv,mode='center'):
                p,pc,_=super().lift(k,uv,mode)
                edge=np.min(np.minimum(uv,1000-uv),axis=1)<=40
                alternating=np.arange(len(uv))%3==0
                spread=np.where(edge,np.where(alternating,.08,.15),np.where(alternating,.20,.40))
                self.expected=p[np.where(edge,spread<=.10,spread<=.25)]
                return p,pc,spread
        geo=Spread();mask=np.zeros((32,80,112),bool);mask[3]=True
        result=load_backend(BACKEND).lift_object('wide',mask,mask.any(axis=(1,2)).astype(float),geo,tau=.5)
        self.assertTrue(result['seen'])
        np.testing.assert_array_equal(result['points']['4'],geo.expected)
        self.assertEqual(result['spread'],.20)

    def test_packer_cannot_relabel_legacy_rows_as_v3122(self):
        from derivgen.ground_v312_pack import training_row
        with self.assertRaisesRegex(ValueError,'rendered revision 3.12.2'):
            training_row({'spec_version':'3.12.1'})

    def test_backend_and_spec_revision_must_agree(self):
        from types import SimpleNamespace
        from derivgen.ground_v312_io import validate_revision
        root=Path(__file__).parent
        validate_revision(SimpleNamespace(VERSION='3.12.2'),root/'SPEC_v3.12.2.md')
        with self.assertRaisesRegex(ValueError,'spec revision'):
            validate_revision(SimpleNamespace(VERSION='3.12.2'),root/'SPEC_v3.12.1.md')
        with self.assertRaisesRegex(ValueError,'lifting revision'):
            validate_revision(SimpleNamespace(VERSION='3.12.1'),root/'SPEC_v3.12.2.md')

    def test_production_requires_reviewed_backend_pin(self):
        import os, subprocess, sys
        from test_v312_ground import BACKEND
        command=[sys.executable,'-B','-m','derivgen.ground_v312_production',
            '--backend',BACKEND,'--backend-sha256','wrong','--manifest','missing',
            '--manifest-sha256','wrong','--gt-root','missing','--output','missing',
            '--spec','missing','--tokenizer','missing','--benchmark','missing',
            '--rkit-root','missing','--input','missing','--set-policy','v2']
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
                 OPENBLAS_NUM_THREADS='1',RAYON_NUM_THREADS='1')
        run=subprocess.run(command,capture_output=True,text=True,env=env)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('backend pin mismatch',run.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
