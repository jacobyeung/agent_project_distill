import ast
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
import uuid
B=Path(__file__).resolve().parents[1];R=B.parents[1]
sys.path.append(str(B/'code'))
from adapter import *
import engine,policy,scorer,report,proof
from boundary import Boundary,drive
SPEC=dict(tree=str(R/'from113/work/tree'),artifact={'path':'fixture','sha256':digest('fixture')},config={'path':'fixture','sha256':digest('fixture')})
engine.initialize(SPEC)

class Read(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=B/'work'/('test_'+uuid.uuid4().hex);cls.root.mkdir()
        cls.bound=prepare(R/'in/vsti/vstibench_repr_450_v3.json',R/'in/vsti/media.json',R/'in/vsti/frames_sample',cls.root/'i',True)
        cls.raw=engine.tower(cls.bound,SPEC,cls.root/'raw',True)
        cls.geometry=engine.prepare_geometry(cls.bound,SPEC,cls.raw,cls.root/'g',Boundary())
        cls.complete=engine.run(cls.root/'i/BOUND.json',SPEC,cls.geometry,cls.root/'j',boundary=Boundary())
        cls.merged=engine.merge(cls.root/'i/BOUND.json',[cls.root/'j'],cls.root/'MERGED.json')
        import perception as P
        from routed import trainer_row
        tasks=rows(cls.root/'i/TASKS.jsonl');captures=load(cls.root/'i/FRAMES.json')['captures']
        cls.geo=P.load_geometry(load(cls.geometry),trainer_row(tasks[0],captures[0],cls.bound['frames_root'])) if tasks[0]['native']==captures[0]['native'] else None
    def test_adapter_truth_separation(self):
        tasks=rows(self.root/'i/TASKS.jsonl');self.assertEqual(len(tasks),9)
        self.assertTrue(all('ground_truth' not in t for t in tasks))
        self.assertTrue(all(t['id'].startswith('q') and t['dataset']=='d0' for t in tasks))
        for c in load(self.root/'i/FRAMES.json')['captures']:
            self.assertEqual(len(c['frames']),32)
            for f in c['frames']:self.assertEqual(sha(Path(self.bound['frames_root'])/f['path']),f['sha256'])
    def test_pair(self):
        self.assertEqual(frame_pair('between frame 8 and frame 20 of 32?'),(8,20))
        self.assertEqual(frame_pair('frame 8 of 32 to frame 20 of 32'),(8,20))
        for text in ('frame 0 and frame 20 of 32','frame 1 and frame 33 of 32','frame 8 of 32'):
            with self.assertRaises(ValueError):frame_pair(text)
    def test_fixed_canary(self):
        items=load(R/'in/vsti/vstibench_repr_450_v3.json')
        tasks=[dict(id='q'+str(t['id']),question_type=t['question_type']) for t in items]
        canary,rest=order(tasks);lookup={t['id']:t for t in tasks}
        from collections import Counter
        self.assertEqual(Counter(lookup[k]['question_type'] for k in canary),COUNTS)
        self.assertEqual(len(rest),440)
        self.assertTrue(all(lookup[k]['question_type'] in CAMERA for k in rest[:96]))
        dump(B/'out/CANARY_KEYS.json',dict(canary=canary,post_canary=rest))
    def test_all_refusals_continue(self):
        from reader_policy import CALL_NAMES
        names=[n for n in CALL_NAMES if n not in policy.SERVED]
        for name in names:
            decoded=drive('<think>\n<'+name+' x=1>\n</think>\nA',self.geo)
            self.assertEqual(decoded['finish'],'eos');self.assertEqual(scorer.final_text(decoded),'A')
            self.assertEqual(decoded['calls'][0]['response'],policy.RESPONSE)
            self.assertEqual(policy.records(decoded)[0]['refused'],True)
            self.assertNotEqual(decoded['finish'],'program_refusal')
            self.assertTrue(engine.replay(decoded,self.geo)['byte_equal'])
    def test_text_tags_remain_text(self):
        for tag in ('<frame 5>','<obj>','<mystery x=1>','<move_other x=1>'):
            decoded=drive('<think>'+tag+'</think>A',self.geo)
            self.assertEqual(decoded['calls'],[])
            self.assertIn(tag,decoded['text'])
            self.assertEqual(scorer.final_text(decoded),'A')
    def test_camera_dispatch(self):
        for call in ('<move from=1 to=2>','<turn from=1 to=2>','<pose frame=2>'):
            decoded=drive('<think>'+call+'</think>1',self.geo)
            self.assertFalse(policy.records(decoded)[0]['refused'])
            self.assertNotEqual(policy.records(decoded)[0]['kind'],'error')
    def test_fields(self):
        values=self.merged['items'];self.assertTrue(any(r['refused'] for r in values))
        for r in values:
            for c in r['calls']:
                self.assertTrue({'name','text','position','response','refused'}<=set(c))
                self.assertIsInstance(c['position'],int)
    def test_budget_close_scores_recorded_answer(self):
        import reader_policy as Q
        d=drive('<think>'+'x'*2100+'\n</think>\nA',self.geo,budget=Q.DECODE_BUDGET)
        self.assertTrue(d['decode_budget']['fired'])
        self.assertEqual(scorer.score('',dict(options=['A'],ground_truth='A'))['score'],0)
        self.assertEqual(scorer.score('A',dict(options=['A'],ground_truth='A'))['score'],1)
    def test_canary_receipt(self):
        c=load(self.root/'j/CANARY.json');self.assertTrue(c['pass_']);self.assertGreater(c['refused'],0);self.assertGreater(c['served'],0)
        data=deepcopy(self.merged['items']);data[0]['replay']['byte_equal']=False
        self.assertFalse(engine.canary_check(data,self.bound['canary'],load(self.root/'j/REQUEST.json'))['pass_'])
    def test_shard_partitions(self):
        full=load(B/'out/CANARY_KEYS.json');full['keys']=full['canary']+full['post_canary']
        parts=[shard_keys(full,f'{k}/4') for k in range(4)]
        flat=sum(parts,[]);self.assertEqual(len(flat),len(set(flat)));self.assertEqual(set(flat),set(full['keys']))
        self.assertEqual(shard_keys(full,'0/1'),full['keys'])
        for invalid in ('1/1','0/0','-1/3'):
            with self.assertRaises(ValueError):shard_keys(full,invalid)
    def test_merge_overlap(self):
        with self.assertRaisesRegex(ValueError,'overlap'):engine.merge(self.root/'i/BOUND.json',[self.root/'j',self.root/'j'],self.root/'bad.json')
    def test_partial(self):
        dest=self.root/'limited';c=engine.run(self.root/'i/BOUND.json',SPEC,self.geometry,dest,limit=1e-9,boundary=Boundary())
        self.assertEqual(c['keys'],[]);self.assertEqual(c['reason'],'time_limit')
        with self.assertRaises(ValueError):engine.merge(self.root/'i/BOUND.json',[dest],self.root/'bad2.json')
        m=engine.merge(self.root/'i/BOUND.json',[dest],self.root/'partial.json',True)
        self.assertEqual(m['missing'],self.bound['keys']);self.assertFalse(m['complete'])
    def test_report(self):
        result=report.build(self.root/'MERGED.json',self.root/'report',[R/'in/comparators/f17.per_question_scores.jsonl',R/'in/comparators/p1m200.per_question_scores.jsonl'])
        self.assertEqual(len(result['per_type']),9);self.assertEqual(len(result['subtasks']),5)
        self.assertIsNone(result['primary']['score']);self.assertIn('every other call is refused',result['disclosure'])
        self.assertIn('room_interval',result['per_type']['camera_displacement'])
    def test_comparators(self):
        result=scorer.comparator_check([R/'in/comparators/f17.per_question_scores.jsonl',R/'in/comparators/p1m200.per_question_scores.jsonl'],B/'out/SCORER_CHECK.json')
        self.assertEqual([r['primary_pct'] for r in result.values()],[66.95,68.71])
    def test_formula_authority(self):
        source=(R/'in/scorer/score_record_core.py').read_text();tree=ast.parse(source)
        node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='AGGREGATION_FORMULAS' for t in n.targets))
        value=eval(compile(ast.Expression(node.value),'authority','eval'),{'DEVELOPMENT_CATEGORIES':[],'VSTI_CATEGORIES':scorer.TYPES})
        groups=value['vstibench-official-5subtask-v1']['collapse_groups']
        self.assertEqual([tuple(v) for v in scorer.GROUPS.values() if len(v)>1],groups)
    def test_proof_comparison(self):
        reference=load(B/'work/proof_reference.json');out=self.root/'PROOF.json'
        result=proof.compare(reference,deepcopy(reference),deepcopy(reference),out,True)
        self.assertEqual(result['identical_count'],10);self.assertFalse(result['proven'])
        changed=deepcopy(reference);changed[0]['decode']['tokens'][0]+=1
        result=proof.compare(reference,changed,reference,out,True)
        self.assertEqual(result['identical_count'],9);self.assertEqual(result['records'][0]['first_divergence']['field'],'tokens')
    def test_two_shards_match_single(self):
        local=self.root/'split';local.mkdir()
        b=deepcopy(self.bound);b['canary']=b['keys'][:2];b['post_canary']=b['keys'][2:]
        b['binding']=digest({k:v for k,v in b.items() if k!='binding'});dump(local/'BOUND.json',b)
        g=load(self.geometry);g['binding']=b['binding'];dump(local/'GEOMETRY.json',g)
        for shard in ('0/2','1/2'):
            engine.run(local/'BOUND.json',SPEC,local/'GEOMETRY.json',local/shard[0],shard=shard,
                       canary_receipt=local/'0/CANARY.json' if shard[0]=='1' else None,boundary=Boundary())
        merged=engine.merge(local/'BOUND.json',[local/'0',local/'1'],local/'MERGED.json')
        expected={(r['key'],r['arm']):(r['decode'],r['score']) for r in self.merged['items']}
        actual={(r['key'],r['arm']):(r['decode'],r['score']) for r in merged['items']}
        self.assertEqual(expected,actual)
    def test_all_camera_pairs_parse(self):
        items=load(R/'in/vsti/vstibench_repr_450_v3.json')
        self.assertEqual(sum(bool(frame_pair(i['question'])) for i in items if i['question_type'] in CAMERA),100)
    def test_canary_failure_stops(self):
        from unittest.mock import patch
        with patch.object(engine,'canary_check',return_value=dict(pass_=False)):
            with self.assertRaisesRegex(ValueError,'canary failed'):
                engine.run(self.root/'i/BOUND.json',SPEC,self.geometry,self.root/'stop',boundary=Boundary())
        self.assertEqual(load(self.root/'stop/COMPLETE.json')['reason'],'canary_failed')
    def test_interrupted_journal_prefix(self):
        local=self.root/'tail';local.mkdir()
        values=self.merged['items'][:2]
        blob=''.join(json.dumps(v)+'\n' for v in values).encode()
        journal=local/'items.jsonl';journal.write_bytes(blob)
        c=deepcopy(self.complete);c.update(reason='running',keys=[values[0]['key']],
            missing=[q for q in self.bound['keys'] if q!=values[0]['key']],journal=pin(journal),journal_bytes=len(blob))
        with journal.open('ab') as stream:stream.write(b'{incomplete')
        dump(local/'COMPLETE.json',c)
        result=engine.merge(self.root/'i/BOUND.json',[local],local/'MERGED.json',True)
        self.assertEqual(len(result['items']),2);self.assertEqual(result['missing'],c['missing']);self.assertFalse(result['complete'])
    def test_shard_pin_rejection(self):
        destination=self.root/'foreign';destination.mkdir()
        c=deepcopy(self.complete);c['config']={'sha256':'foreign'};dump(destination/'COMPLETE.json',c)
        with self.assertRaisesRegex(ValueError,'pins differ'):engine.merge(self.root/'i/BOUND.json',[self.root/'j',destination],self.root/'bad3.json')
    def test_namespace_shared_memory(self):
        from venue import namespace
        args=namespace(self.root/'namespace',[],cpu=True)
        self.assertEqual(args[0],str(self.root/'namespace/bwrap'))
        self.assertNotIn('--dev-bind',args)
        index=args.index('/dev/shm');self.assertEqual(args[index-1],str(self.root/'namespace/shm'))
if __name__=='__main__':unittest.main(verbosity=2)
