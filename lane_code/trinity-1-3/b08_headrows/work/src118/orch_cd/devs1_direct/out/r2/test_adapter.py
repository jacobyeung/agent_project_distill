"""CPU metadata, bind-contract, frame-integrity and paired-report regression tests."""
import collections
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import adapter as A
import report as R
LANE=ROOT.parents[1]
WORK=LANE/'work/r2'

class Metadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root,cls.pins,cls.rows,cls.captures=A.payload(ROOT)
        cls.items=A.jsonl(ROOT/'ITEMS.jsonl');cls.excluded=A.jsonl(ROOT/'EXCLUDED.jsonl')
        cls.withhold=json.loads((ROOT/'WITHHOLD_SCENES.json').read_text())
    def test_partition_exactly_once(self):
        ids=[r['id'] for r in self.rows]+[r['qid'] for r in self.excluded]
        self.assertEqual(len(ids),2136);self.assertEqual(len(set(ids)),2136)
        self.assertEqual(set(ids),{r['qid'] for r in self.items})
    def test_fixed_count_correction(self):
        self.assertEqual(len(self.rows),1525);self.assertEqual(len(self.excluded),611)
        c=collections.Counter(r['question_type'] for r in self.rows)
        self.assertEqual(c,{**dict.fromkeys(set(A.SCORERS)-{'relative_count','room_size_estimation'},150),'relative_count':139,'room_size_estimation':36})
    def test_excluded_reasons(self):
        self.assertEqual(collections.Counter(r['type'] for r in self.excluded),{**dict.fromkeys(A.EXCLUDED,150),'room_size_estimation':11})
        for r in self.excluded:
            if r['type'] in A.EXCLUDED:self.assertEqual(r['reason'],A.EXCLUDED[r['type']])
            else:self.assertIn('neither canonical nor released',r['reason'])
    def test_all_ordered_anchors(self):
        for r in self.rows:self.assertEqual(r['source_frame_indices'],self.captures[r['native']]['anchor_indices'])
        for c in self.captures.values():
            self.assertEqual(len(c['frames']),32);self.assertEqual([p['index'] for p in c['frames']],c['anchor_indices'])
    def test_outside_plan_refused(self):
        x={**self.items[0],'native':'d1/scene9999_00'}
        with self.assertRaisesRegex(ValueError,'outside'):A.validate_membership(x,self.captures,self.withhold)
    def test_unwithheld_room_refused(self):
        x={**self.items[0],'room':'d1/scene9999'}
        with self.assertRaisesRegex(ValueError,'withheld'):A.validate_membership(x,self.captures,self.withhold)
    def test_wrong_scene_refused(self):
        x={**self.items[0],'scene':'scannet/bad'}
        with self.assertRaisesRegex(ValueError,'mismatch'):A.validate_membership(x,self.captures,self.withhold)
    def test_same_item_keys(self):
        k=json.loads((ROOT/'CELL_ITEMS.json').read_text());self.assertEqual(k['cp1m200'],k['f17'])
    def test_strata_reproducible(self):
        self.assertEqual([A.strata(r) for r in self.rows]+A.excluded_strata(self.excluded),A.jsonl(ROOT/'STRATA.jsonl'))
        self.assertEqual(A.sha(ROOT/'STRATA.jsonl'),(ROOT/'STRATA.jsonl.sha256').read_text().split()[0])
    def test_scorer_selection(self):
        for r in self.rows:self.assertEqual(r['scorer'],A.SCORERS[r['question_type']])
    def test_missing_never_agreement_or_disagreement(self):
        c=collections.Counter(r['stratum'] for r in self.rows)
        self.assertEqual(c,{'primary':1375,'missing_released':150})
    def test_source_room_units_and_prompts(self):
        for r in self.rows:
            if r['id'].startswith('room_'):
                self.assertIn('square meters',r['question'])
                if r['answer'] is not None:self.assertIn('square meters',r['label_provenance']['label_transfer'])
    def test_two_cell_protocols(self):
        for model in ('cp1m200','f17'):A.validate_cell(json.loads((ROOT/f'cells_{model}.json').read_text())[0],model)
    def test_dry_bind_both_kit_copies(self):
        for name in ('cp1','f17'):
            d=WORK/('dry_release_'+name);c=json.loads((d/'request.json').read_text())
            self.assertTrue(c['build_only']);self.assertEqual(json.loads((d/'BIND_STATUS.json').read_text())['tasks'],1525)
            self.assertTrue((d/'kit/evaluator/worker.py').is_file())
            self.assertEqual(A.sha(d/'kit/source.tar'),c['source_sha256'])
    def test_prompts_identical_between_kits(self):
        a=json.loads((WORK/'dry_release_cp1/PROMPT_PINS.json').read_text());b=json.loads((WORK/'dry_release_f17/PROMPT_PINS.json').read_text())
        self.assertEqual(a,b);self.assertEqual(len(a),1525)
    def test_dry_receipt_expansions(self):
        for name,rep in [('cp1',2),('f17',1)]:
            rs=json.loads((WORK/f'dry_release_{name}/RECEIPT_TEMPLATES.json').read_text())
            for r in rs:
                anchors=r['audit']['anchor_indices'];expected=[i for i in anchors for _ in range(rep)]
                self.assertEqual([p['index'] for p in r['frames']],expected)
                self.assertEqual(r['audit']['metadata']['frames_indices'],expected)
    def test_dry_cannot_launch(self):
        # Adapter self-pin may change while developing; either changed or dry is refused.
        with self.assertRaisesRegex(ValueError,'Dry bind'):A.verify_bound(WORK/'dry_release_cp1')

class StratumRules(unittest.TestCase):
    def mc(self,a='A',b='B',options=None,released_options=None):
        return dict(id='x',room='r',question_type='object_rel_distance',answer=a,released_answer=b,
                    options=options or ['A. red','B. blue'],released_options=released_options)
    def test_different_letters_same_content_primary(self):
        r=self.mc(released_options=['A. blue','B. RED'])
        self.assertEqual(A.strata(r)['stratum'],'primary')
        self.assertEqual(A.scoring_label(r,'released_answer'),'A')
    def test_same_letter_different_content_disagreement(self):
        r=self.mc(b='A',released_options=['A. blue','B. red'])
        self.assertEqual(A.strata(r)['stratum'],'disagreement')
        self.assertEqual(A.scoring_label(r,'released_answer'),'B')
    def test_whitespace_and_case_only(self):
        r=self.mc(options=['A. Office  Chair','B. blue'],released_options=['A. blue','B. office\tchair'])
        self.assertEqual(A.strata(r)['stratum'],'primary')
        self.assertNotEqual(A.normalize_text('chair'),A.normalize_text('office chair'))
        self.assertNotEqual(A.normalize_text('back-left'),A.normalize_text('back left'))
    def test_missing_option_text_is_explicit(self):
        r=self.mc()
        self.assertEqual(A.strata(r)['stratum'],'released_text_unavailable')
        self.assertIsNone(A.strata(r)['agree'])
        self.assertIsNone(A.scoring_label(r,'released_answer'))
    def test_ambiguous_displayed_mapping_refused(self):
        r=self.mc(options=['A. red','B. RED'],released_options=['A. blue','B. red'])
        with self.assertRaisesRegex(ValueError,'unique option'):A.scoring_label(r,'released_answer')
    def test_release_content_absent_from_prompt_refused(self):
        r=self.mc(released_options=['A. green','B. yellow'])
        with self.assertRaisesRegex(ValueError,'unique option'):A.scoring_label(r,'released_answer')
    def numeric(self,a,b):return A.strata(dict(id='x',room='r',question_type='object_abs_distance',answer=a,released_answer=b))['stratum']
    def test_ten_percent_inclusive(self):self.assertEqual(self.numeric('11','10'),'primary')
    def test_above_ten_percent(self):self.assertEqual(self.numeric('11.000001','10'),'disagreement')
    def test_denominator_released(self):self.assertEqual(self.numeric('10','9'),'disagreement')
    def test_zero(self):self.assertEqual(self.numeric(0,0),'primary');self.assertEqual(self.numeric(1,0),'disagreement')
    def test_nonfinite_refused(self):
        with self.assertRaises(ValueError):self.numeric('NaN',1)
    def test_option_content_and_letter(self):self.assertEqual(A.option('red',['A. red','B. blue']),'A')
    def test_bad_option_refused(self):
        with self.assertRaises(ValueError):A.option('C',['A. red','B. blue'])

class FramesAndScoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.media,cls.official=A.kit_import(WORK/'dry_release_cp1/kit')
        cls.score=staticmethod(importlib.import_module('scoring').score_item)
    def test_actual_kit_scorers_all_types(self):
        rows=A.jsonl(ROOT/'TASKS.jsonl')
        for typ in A.SCORERS:
            r=next(r for r in rows if r['question_type']==typ)
            gt=A.effective_ground_truth(r)
            t={**r,'benchmark':'devrows','ground_truth':gt,'thinking':True}
            self.assertEqual(self.score(t,'</think>\n'+str(gt),10)['score'],1.0,typ)
            self.assertEqual(self.score(t,'still thinking',10)['score'],0.0,typ)
    def test_cap_contract_matches_base(self):
        t=dict(benchmark='devrows',question_type='object_counting',ground_truth='2',thinking=True)
        # Base contract scores a parseable closed answer, even when finish=length.
        v=self.score(t,'</think>\n2',16384,finish='length')
        self.assertTrue(v['hit_token_cap']);self.assertEqual(v['score'],1.0)
    def test_released_letter_is_remapped_for_real_kit(self):
        r=next(r for r in A.jsonl(ROOT/'TASKS.jsonl') if r['answer_type']=='multiple_choice'
               and r['released_answer'] is not None and r['answer']!=r['released_answer'])
        self.assertEqual(self.score({**r,'benchmark':'devrows'},'</think>\n'+r['answer'],10)['score'],1.0)
        self.assertEqual(self.score({**r,'benchmark':'devrows'},'</think>\n'+r['released_answer'],10)['score'],0.0)
    def test_disagreement_scores_both_labels_in_displayed_order(self):
        r=dict(benchmark='devrows',question_type='object_rel_distance',options=['A. red','B. blue'],
               released_options=['A. blue','B. red'],answer='A',released_answer='A',thinking=True)
        scores={field:self.score(dict(r,ground_truth=A.scoring_label(r,field)),'</think>\nA',10)['score']
                for field in ('answer','released_answer')}
        self.assertEqual(scores,dict(answer=1.0,released_answer=0.0))
    def test_frame_escape_refused(self):
        with self.assertRaises(ValueError):A.safe_frame(LANE,'../bad.png')
    def test_real_png_receipt_round_trip_and_tamper(self):
        import numpy as np
        from PIL import Image
        d=Path(tempfile.mkdtemp(prefix='frames_',dir=WORK));src=d/'src';src.mkdir()
        frames=[]
        for i in range(32):
            p=src/f'{i}.png';Image.fromarray(np.full((2,3,3),i,dtype=np.uint8)).save(p)
            frames.append(dict(index=i,path=p.name,sha256=A.sha(p)))
        c=dict(native='d1/test',anchor_indices=list(range(32)),frames=frames,fps=1,total_num_frames=32,hw=[2,3])
        task=dict(benchmark='devrows',example_id='x',video_path='identity-only',native='d1/test',source_frame_indices=list(range(32)))
        for layout in ('spread','duplicate'):
            cfg=dict(cells=[dict(layout=layout)],binding='binding',source_sha256='source',devs1=dict(payload=str(ROOT)))
            cache=d/layout;h=A.make_frames(cfg,[task],{'d1/test':c},self.media,src,cache)
            arr,audit=self.media.load(task,layout,cache,h)
            expected=list(range(32)) if layout=='spread' else [i for i in range(32) for _ in range(2)]
            self.assertEqual(arr[:,0,0,0].tolist(),expected)
            self.assertEqual(audit['metadata']['frames_indices'],expected)
        (src/'0.png').write_bytes(b'corrupt')
        with self.assertRaisesRegex(ValueError,'PNG pin'):self.media.load(task,'spread',d/'spread',A.sha(d/'spread/0.json'))
    def test_report_wrong_order_refused(self):
        t=dict(source_frame_indices=[1,2]);r=dict(key='x',status='complete',layout='duplicate',media=dict(anchor_indices=[1,2],metadata=dict(frames_indices=[1,2,1,2])))
        with self.assertRaises(ValueError):R.check_frames(r,t,dict(layout='duplicate'))

class AdditionalGates(unittest.TestCase):
    def test_missing_png_refused(self):
        _,media,_=A.kit_import(WORK/'dry_release_cp1/kit')
        d=Path(tempfile.mkdtemp(prefix='absent_',dir=WORK))
        c=dict(frames=[dict(path='missing.png',sha256='0'*64)])
        with self.assertRaisesRegex(ValueError,'Missing PNG'):
            A.make_frames({},[],{'capture':c},media,d,d/'cache')
    def test_cell_layout_mutation_refused(self):
        c=json.loads((ROOT/'cells_cp1m200.json').read_text())[0];c['layout']='spread'
        with self.assertRaises(ValueError):A.validate_cell(c,'cp1m200')
    def test_unbound_model_refused(self):
        models=json.loads((ROOT/'MODELS.reference.json').read_text());models['cp1m200']['sha256']='0'*64
        with self.assertRaises(ValueError):A.check_model_specs(models,'cp1m200')
    def test_live_bind_allows_unavailable_then_requires_frames(self):
        import subprocess
        d=Path(tempfile.mkdtemp(prefix='blocked_bind_',dir=WORK))
        result=subprocess.run([sys.executable,'-I','-s',str(ROOT/'adapter.py'),'bind','--cell','cp1m200',
            '--kit',str(WORK/'dry_release_cp1/kit'),'--models',str(ROOT/'MODELS.reference.json'),
            '--frames-root',str(d/'absent_frames'),'--dest',str(d/'bound')],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Missing PNG',result.stderr)
        self.assertNotIn('lack canonical/released',result.stderr)
        self.assertFalse((d/'bound/frames/0.json').exists())
        self.assertFalse(json.loads((d/'bound/BIND_STATUS.json').read_text())['ready'])
    def test_wrong_checkpoint_refused(self):
        models=json.loads((ROOT/'MODELS.reference.json').read_text());models['cp1m200']['sha256']='a'*64
        with self.assertRaisesRegex(ValueError,'Checkpoint'):A.check_model_specs(models,'cp1m200')
    def test_unavailable_released_scoring_is_null(self):
        r=next(r for r in A.jsonl(ROOT/'TASKS.jsonl') if r['question_type']=='route_planning')
        self.assertIsNone(A.scoring_label(r,'released_answer'))
        self.assertEqual(A.effective_ground_truth(r),r['answer'])
    def test_all_items_have_frozen_stratum(self):
        ss=A.jsonl(ROOT/'STRATA.jsonl');self.assertEqual(len(ss),2136)
        self.assertEqual(len({r['qid'] for r in ss}),2136)

class Reporting(unittest.TestCase):
    def test_three_views_keep_unavailable_out_of_primary(self):
        rows=self.rows()
        rows[1]['stratum']='missing_released';rows[1]['scores']['released_answer']=None
        rows[2]['stratum']='released_text_unavailable';rows[2]['scores']['released_answer']=None
        result=R.summarize(rows)
        self.assertEqual(result['primary']['released_answer']['overall']['items'],1)
        self.assertEqual(result['unavailable']['answer']['overall']['items'],2)
        self.assertIsNone(result['unavailable']['released_answer']['overall']['score_pct'])
        self.assertIsNone(result['disagreement']['answer']['overall']['score_pct'])
    def rows(self):
        return [dict(key=str(i),question_type='object_counting',room='a' if i<2 else 'b',stratum='primary',
                     scores=dict(released_answer=float(i<2),answer=1),capped=i==0,unanswered=False,unparsed=False) for i in range(3)]
    def test_paired_identical_zero(self):
        a=self.rows();p=R.paired(a,a,'released_answer',200)
        self.assertEqual(p['delta_pp'],0);self.assertEqual(p['ci95_pp'],[0,0]);self.assertEqual(p['rooms'],2)
    def test_paired_cluster_weight(self):
        a=self.rows();b=copy.deepcopy(a)
        for r in b:r['scores']['released_answer']=0
        p=R.paired(a,b,'released_answer',200)
        self.assertAlmostEqual(p['delta_pp'],200/3);self.assertEqual(p['ci95_pp'],[0,100])
    def test_paired_reproducible(self):
        a=self.rows();self.assertEqual(R.paired(a,a,'released_answer',200),R.paired(a,a,'released_answer',200))
    def test_unmatched_pairs_refused(self):
        with self.assertRaises(ValueError):R.paired(self.rows(),self.rows()[:2],'released_answer',200)
    def test_missing_metric_null(self):self.assertIsNone(R.aggregate([],'answer')['score_pct'])
    def test_report_counts(self):
        r=R.summarize(self.rows());self.assertEqual(r['primary']['released_answer']['overall']['capped'],1)

class AuditEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=json.loads((ROOT/'LABEL_AGREEMENT.json').read_text())
        cls.samples=A.jsonl(ROOT/'TRAIN_SAMPLE.jsonl')
    def test_training_counts_match_manifest(self):
        manifest=json.loads((LANE.parent/'dose_pool/out/POOL_S1/MANIFEST.json').read_text())
        totals=collections.Counter()
        for group in manifest['sets']:
            # Final counts were computed from the concrete exclusion lists.
            totals.update(group.get('rows_per_type',{}))
        for t,n in self.audit['training_raw_counts'].items():self.assertEqual(n,totals[t])
    def test_training_sample_unique_and_hash_ordered(self):
        keys=[(r['source_set'],r['qid']) for r in self.samples]
        self.assertEqual(len(keys),len(set(keys)))
        for t,c in self.audit['training_final_counts'].items():
            rows=[r for r in self.samples if r['question_type']==t]
            self.assertEqual(len(rows),min(3000,c))
            hashes=[hashlib.sha256(('devs1-r2|'+t+'|'+r['source_set']+'|'+r['qid']).encode()).hexdigest() for r in rows]
            self.assertEqual(hashes,sorted(hashes))
    def test_training_rates_recomputed_from_selected_text(self):
        counts=collections.defaultdict(collections.Counter)
        for r in self.samples:
            a=A.selected_content(r['answer'],r['options']);b=A.selected_content(r['released_answer'],r['released_options'])
            counts[r['question_type']]['agree']+=A.normalize_text(a)==A.normalize_text(b)
        for t,v in self.audit['training'].items():self.assertEqual(counts[t]['agree'],v['content_agree'])
    def test_all_training_mismatches_are_intermediate_renamings(self):
        changed=0
        for r in self.samples:
            a=A.selected_content(r['answer'],r['options']);b=A.selected_content(r['released_answer'],r['released_options'])
            j=r['source_join'];c=A.selected_content(j['gt_answer'],j['options'])
            self.assertEqual(A.normalize_text(a),A.normalize_text(c))
            changed+=A.normalize_text(a)!=A.normalize_text(b)
        self.assertEqual(changed,324)
    def test_upstream_gate_totals_match_census(self):
        census=json.loads((LANE.parent/'dose_pool/out/pool_v0/CENSUS.json').read_text())['stages']
        gate=self.audit['upstream_release_gate']
        direction=[gate['object_rel_direction_'+x] for x in ('easy','medium','hard')]
        self.assertEqual(sum(v.get('passed',0)+v.get('dropped',0) for v in direction),census['relative_direction_object']['program_ok'])
        self.assertEqual(sum(v.get('dropped',0) for v in direction),8)
        for t,old in [('object_rel_distance','relative_distance_object'),('relative_count','relative_count'),('relative_size_object','relative_size_object')]:
            self.assertEqual(gate[t]['dropped'],census[old]['drop:agreement'])
            self.assertEqual(sum(gate[t].values()),census[old]['program_ok'])
    def test_original_items_prompts_and_raw_labels_preserved(self):
        self.assertEqual(A.sha(ROOT/'ITEMS.jsonl'),A.sha(LANE/'out/ITEMS.jsonl'))
        old={r['id']:r for r in A.jsonl(LANE/'out/TASKS.jsonl')}
        for r in A.jsonl(ROOT/'TASKS.jsonl'):
            for key in ('question','options','answer','released_answer','source_frame_indices'):
                self.assertEqual(r[key],old[r['id']][key])
    def test_missing_rooms_excluded_and_listed(self):
        rooms=A.jsonl(ROOT/'EXCLUDED_MISSING_ROOM.jsonl')
        self.assertEqual(len(rooms),11)
        for r in rooms:self.assertIsNone(r['answer']);self.assertIsNone(r['released_answer'])

if __name__=='__main__':unittest.main(verbosity=2)
