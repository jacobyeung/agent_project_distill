"""Score, budget provenance, prefix and launch regressions for the specialized fork."""
import asyncio,json,sys,tempfile,unittest,ast,hashlib
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'evaluator'),str(ROOT/'local')]
import merge,budget_merge
from budget import derive,source_lines,Journal,CLOSE
from scoring import score_item,benchmark_summary
from worker import append
from evalpath.items import digest
from token_audit import prefix_score
ON=dict(model='t0m800',layout='duplicate',benchmarks=['revsi'],decoding='greedy',thinking=True,max_tokens=16384)

class Tokenizer:
    def encode(self,text,**kw):
        out=[]
        while text:
            if text.startswith('</think>'):out.append(1);text=text[8:]
            else:out.append(ord(text[0]));text=text[1:]
        return out
    def decode(self,ids,**kw):return ''.join('</think>' if i==1 else chr(i) for i in ids)
TOK=Tokenizer()

def task(i=1):return dict(benchmark='revsi',example_id=str(i),question_type='object_size_estimation',ground_truth=str(i+2),options=[],question='How many?',source_frame_indices=list(range(32)))

def row(i=1,text=None):
    t=task(i);text=text if text is not None else 'reason</think>\n'+t['ground_truth'];ids=TOK.encode(text)
    r=dict(t,key='revsi:'+str(i),binding=digest(dict(request='request',cell=0)),status='complete',layout='duplicate',frames=32,thinking=True,model='t0m800',decoding='greedy',raw_generation=text,token_ids=ids,token_ids_sha256=digest(ids),finish_reason='stop',anchor_indices=None,media={'metadata':{'frames_indices':[x for x in range(32) for _ in range(2)]}})
    r.update(score_item(r,text,len(ids),cap=16384))
    short=TOK.decode(ids[:4096]);r['at_4096']=dict(raw_generation=short,**score_item(r,short,min(len(ids),4096),cap=4096,finish='length' if len(ids)>=4096 else 'stop'))
    return r

def retained():return Path(tempfile.mkdtemp(dir=ROOT/'checks'))

class Fork(unittest.TestCase):
    def test_B1_capped_parseable_answer_matches_base_contract(self):
        t=dict(task(),thinking=True)
        r=score_item(t,'reason</think>\n3',64,cap=64,finish='length')
        self.assertEqual(r['score'],1);self.assertTrue(r['hit_token_cap'])
        s=benchmark_summary([dict(t,status='complete',**r)],[t],True)
        self.assertEqual(s['overall_score'],1);self.assertEqual(s['per_type']['object_size_estimation']['score'],1);self.assertEqual(s['cap_hits'],1)

    def test_B1_capped_unclosed_and_unparsed_stay_in_denominator(self):
        t=dict(task(),thinking=True);rows=[]
        for raw in ('reason','reason</think>\ninvalid'):
            r=score_item(t,raw,64,cap=64,finish='length');self.assertEqual(r['score'],0)
            rows.append(dict(t,status='complete',**r))
        s=benchmark_summary(rows[:1],[t],True);self.assertEqual(s['per_type']['object_size_estimation']['score'],0);self.assertEqual(s['completed'],1)

    def test_B2_ordinary_budget_spoof_refused(self):
        r=row();r['budget']=123
        with self.assertRaisesRegex(ValueError,'authenticated'):merge.check_row(r,task(),32,ON)

    def test_B2_ordinary_scoring_override_never_used(self):
        r=row(text='reason</think>\n0');r['scoring_text']='reason</think>\n3'
        merge.check_row(r,task(),32,ON)
        r['score']=1;r['response_text']='3'
        with self.assertRaisesRegex(ValueError,'score'):merge.check_row(r,task(),32,ON)

    def test_B2_cfg_flag_cannot_authenticate_budget(self):
        with self.assertRaisesRegex(ValueError,'authenticated'):merge.merge(dict(cells=[ON],budget_arm={'budget':2048}),0,'a')

    def test_B3_model_decoding_and_diagnostics(self):
        for name,value in [('model','cp1m200'),('decoding','qwen_sampling'),('thinking',False),('hit_token_cap',True),('parse_failed',True),('empty_think',True)]:
            with self.subTest(field=name):
                r=row();r[name]=value
                with self.assertRaises(ValueError):merge.check_row(r,task(),32,ON)

    def test_B3_error_metadata_must_match_cell(self):
        r=row();r.update(status='error',model='other')
        with self.assertRaisesRegex(ValueError,'model'):merge.check_row(r,task(),32,ON)

    def test_B1_item_and_summary_equal_sealed_base(self):
        base=Path('/scratch/jjyeung/orch_cd/evalx/work/aws_vl64r/evaluator/scoring.py')
        ns={'__file__':str(base)};exec(compile(base.read_text(),str(base),'exec'),ns)
        t=dict(task(),thinking=True)
        for text,tokens,finish in [('r</think>\n3',64,'length'),('unclosed',64,'length'),('r</think>\ninvalid',64,'length'),('r</think>\n3',6,'stop')]:
            expected=ns['score_item'](t,text,tokens,cap=64,finish=finish)
            actual=score_item(t,text,tokens,cap=64,finish=finish)
            self.assertEqual(actual,expected)
            rows=[dict(t,status='complete',**actual)]
            self.assertEqual(benchmark_summary(rows,[t],True),ns['benchmark_summary'](rows,[t],True))

    def test_B3_prefix_recomputed_and_overlay_whitelisted(self):
        r=row();prefix_score(r,task(),ON,TOK)
        for change in ({'score':0},{'raw_generation':'other</think>\n3'},{'benchmark':'vsi500'},{'hit_token_cap':True}):
            bad=deepcopy(r);bad['at_4096'].update(change)
            with self.assertRaisesRegex(ValueError,'prefix'):prefix_score(bad,task(),ON,TOK)

    def test_B3_token_prefix_requires_count_digest_and_raw(self):
        for name,val in [('output_tokens',1),('token_ids_sha256','0'*64),('raw_generation','spoof')]:
            r=row();r[name]=val
            with self.assertRaises(ValueError):prefix_score(r,task(),ON,TOK)

    def test_B5_error_row_requires_layout(self):
        r=row();r['status']='error';r.pop('layout')
        with self.assertRaisesRegex(ValueError,'layout'):merge.check_row(r,task(),32,ON)

    def test_B6_complete_duplicate_merge_and_budget_load(self):
        d=retained();(d/'0').mkdir();r=row();p=d/'0/g0.jsonl'
        cfg=dict(cells=[ON],datasets=[dict(benchmark='revsi')],roots={},binding='request',output=str(d),gpus=1)
        append(p,r);append(p,dict(r))
        with patch('merge.tasks_for',return_value=[task()]),patch('merge.probe_tasks',return_value=[]):
            self.assertEqual(merge.merge(cfg,0,'a',tokenizer=TOK)['benchmarks']['revsi']['completed'],1)
        self.assertEqual(len(source_lines(p)),1)
        append(p,dict(r,seconds=9))
        with self.assertRaisesRegex(ValueError,'Conflicting'):source_lines(p,latest=True)
        with patch('merge.tasks_for',return_value=[task()]),patch('merge.probe_tasks',return_value=[]):
            with self.assertRaisesRegex(ValueError,'Conflicting'):merge.merge(cfg,0,'b',tokenizer=TOK)

    def derived(self,*,failure=False,long_reuse=False):
        d=retained();(d/'0').mkdir();cfg=dict(cells=[ON],datasets=[dict(benchmark='revsi')],roots={},binding='request',output=str(d),gpus=1)
        rows=[row(1,'r</think>\n'+' '*80+'3' if long_reuse else None),row(2,'x'*4100),row(3,'y'*4100)]
        for r in rows:append(d/'0/g0.jsonl',r)
        before=(d/'0/g0.jsonl').read_bytes();calls=[]
        class Engine:
            async def generate(self,req,params,request_id):
                await asyncio.sleep(0)
                key=request_id.split(':',1)[1];answer=str(int(key.split(':')[1])+2)
                calls.append((key,list(req['prompt_token_ids'])))
                yield NS(prompt_token_ids=req['prompt_token_ids'],outputs=[NS(text=answer,token_ids=TOK.encode(answer),finish_reason='stop')])
        async def request_for(r):
            if failure and r['key']=='revsi:2':raise RuntimeError('synthetic request failure')
            return dict(prompt='prompt-'+r['key']),r['media']
        kwargs=dict(sources=source_lines(d/'0/g0.jsonl'),cell=ON,source_binding=rows[0]['binding'],request_binding='request',cell_index=0,budgets=(2048,4096),tokenizer=TOK,engine=Engine(),params=NS(max_tokens=64,temperature=0),request_for=request_for,path_for=lambda b:d/'0'/f'budget_{b}.g0.jsonl',inflight=3)
        asyncio.run(derive(**kwargs));self.assertEqual((d/'0/g0.jsonl').read_bytes(),before)
        return d,cfg,rows,calls,kwargs

    def merge_arms(self,cfg):
        with patch('merge.tasks_for',return_value=[task(i) for i in (1,2,3)]),patch('budget_merge.tasks_for',return_value=[task(i) for i in (1,2,3)]),patch('merge.probe_tasks',return_value=[]):
            budget_merge.merge_budgets(cfg,0,'a',tokenizer=TOK)

    def test_B4_B8_concurrent_distinct_answers_and_on_bytes(self):
        d,cfg,rows,calls,kwargs=self.derived(long_reuse=True);self.merge_arms(cfg)
        self.assertEqual(len(calls),4)
        for b in (2048,4096):
            records=source_lines(d/'0'/f'budget_{b}.g0.jsonl')
            self.assertEqual(records['revsi:1'][1],source_lines(d/'0/g0.jsonl')['revsi:1'][1])
            for i in (2,3):self.assertEqual(records[f'revsi:{i}'][0]['response_text'],str(i+2))
            summary=json.loads((d/f'budget_{b}/0/summary_a.json').read_text())
            self.assertEqual(summary['benchmarks']['revsi']['per_type']['object_size_estimation']['score'],1)
            self.assertIn('reuse_full_on_answer',summary['budget_arm']['answer_cap_policy'])
        before=len(calls);asyncio.run(derive(**kwargs));self.assertEqual(len(calls),before)

    def test_B2_budget_scoring_text_reconstructed_despite_receipt_rehash(self):
        d,cfg,rows,calls,kwargs=self.derived();p=d/'0/budget_2048.g0.jsonl';meta=p.with_suffix('.meta.jsonl')
        rr=source_lines(p);mm=source_lines(meta);bad=rr['revsi:2'][0];bad['scoring_text']='evil</think>\n4';raw=json.dumps(bad)
        rr['revsi:2']=(bad,raw);oldkey=next(k for k,v in mm.items() if v[0]['source_key']=='revsi:2');mm[oldkey][0]['record_sha256']=digest(raw);mm[oldkey][0]['key']='revsi:2:'+digest(raw)
        p.write_text(''.join(v[1]+'\n' for v in rr.values()));meta.write_text(''.join(json.dumps(v[0])+'\n' for v in mm.values()))
        with self.assertRaisesRegex(ValueError,'reconstructed'):self.merge_arms(cfg)

    def test_B9_derivation_error_stays_zero_and_complete(self):
        d,cfg,rows,calls,kwargs=self.derived(failure=True);self.merge_arms(cfg)
        for b in (2048,4096):
            summary=json.loads((d/f'budget_{b}/0/summary_a.json').read_text())
            self.assertEqual(summary['benchmarks']['revsi']['completed'],3)
            self.assertAlmostEqual(summary['benchmarks']['revsi']['per_type']['object_size_estimation']['score'],2/3,places=5)
            self.assertEqual(summary['derivation']['per_type']['object_size_estimation']['derivation_error'],1)

    def test_B9_budget_interrupted_tail_and_conflicting_receipts(self):
        d,cfg,rows,calls,kwargs=self.derived();p=d/'0/budget_2048.g0.jsonl'
        with p.open('a') as f:f.write('{"partial":')
        asyncio.run(derive(**kwargs));self.merge_arms(cfg)
        meta=p.with_suffix('.meta.jsonl');r=next(iter(source_lines(meta).values()))[0];append(meta,dict(r,score=88))
        with self.assertRaisesRegex(ValueError,'Conflicting'):asyncio.run(derive(**kwargs))

    def test_B9_orphan_receipt_recomputes_without_conflicting_rows(self):
        d,cfg,rows,calls,kwargs=self.derived()
        alt=retained()
        for budget in (2048,4096):
            source=d/'0'/f'budget_{budget}.g0.meta.jsonl'
            # Only receipts survived; the original test journal is retained.
            (alt/f'budget_{budget}.g0.meta.jsonl').write_bytes(source.read_bytes())
        kwargs['path_for']=lambda b:alt/f'budget_{b}.g0.jsonl'
        asyncio.run(derive(**kwargs))
        asyncio.run(derive(**kwargs))
        for b in (2048,4096):self.assertEqual(len(source_lines(alt/f'budget_{b}.g0.jsonl')),3)

    def test_B7_fork_stays_specialized(self):
        from think_settings import validate
        for bad in (dict(ON,benchmarks=['vsi500'],thinking=None),dict(ON,layout='spread'),dict(ON,model='base')):
            with self.assertRaises(ValueError):validate(bad)
        with self.assertRaisesRegex(ValueError,'explicit boolean'):score_item(task(),'3',1)

    def test_B8_launch_must_merge_budgets(self):
        import launch
        d=retained();cfg=dict(gpus=1,models={'base':{},'t0m800':{}},cells=[ON]);p=d/'request.json';p.write_text(json.dumps(cfg))
        with patch.dict(sys.modules,{'vllm':NS(__version__='0.32.0')}),patch.dict('os.environ',{'SLURM_JOB_ID':'job','CUDA_VISIBLE_DEVICES':'synthetic-device'}),patch('launch.prepare_frames',return_value='pin'),patch('launch.prepare',return_value=d),patch('token_audit.load_tokenizer',return_value=TOK),patch('launch.subprocess.Popen',return_value=NS(wait=lambda:0)),patch('launch.merge') as main,patch('budget_merge.merge_budgets') as arms:
            launch.main(str(p),d)
        main.assert_called_once();arms.assert_called_once_with(cfg,0,'job',tokenizer=TOK)

    def test_B9_trainer_adapter_preserves_pinned_source(self):
        pin=json.loads((ROOT/'inputs/TRAINER_ADAPTER.json').read_text())
        original=(ROOT/'inputs/trainer_sources/batches.py').read_bytes();adapted=(ROOT/'evaluator/trainer/batches.py').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),pin['original_sha256'])
        self.assertEqual(hashlib.sha256(adapted).hexdigest(),pin['adapted_sha256'])
        def funcs(s):return {n.name:ast.get_source_segment(s,n) for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)}
        for name,body in funcs(adapted.decode()).items():
            self.assertEqual(body.replace(pin['added_branch'],''),funcs(original.decode())[name])

    def test_B9_trainer_off_boundary_adapter(self):
        from trainer.batches import training_text
        class Processor:
            _student_pilot_student='qwen35'
            tokenizer=NS(eos_token='<|im_end|>',eos_token_id=248046,encode=lambda *a,**k:[248044])
            def apply_chat_template(self,messages,**kw):
                prompt='<|im_start|>assistant\n<think>\n\n</think>\n\n'
                return prompt if kw['add_generation_prompt'] else prompt+messages[-1]['content'].rstrip('\n')+'<|im_end|>\n'
        p,full=training_text(Processor(),'How many?',[],'3\n')
        self.assertEqual(full,'3\n<|im_end|><|endoftext|>')
    def test_B5_worker_records_layout_on_success_and_error(self):
        import worker,numpy as np
        d=retained();off=dict(ON,thinking=False,max_tokens=4096)
        cfg=dict(cells=[off],datasets=[dict(benchmark='revsi')],roots={},binding='request',output=str(d/'out'),gpus=1,max_model_len=49152,max_seqs=2,inflight=2)
        p=d/'cfg.json';p.write_text(json.dumps(cfg))
        processor=NS(tokenizer=TOK)
        class Engine:
            @classmethod
            def from_engine_args(cls,args):return cls()
            def shutdown(self):pass
            async def generate(self,req,params,request_id):
                yield NS(prompt_token_ids=[1],outputs=[NS(text='3',token_ids=TOK.encode('3'),finish_reason='stop')])
        modules={'vllm':NS(SamplingParams=lambda **kw:NS(**kw)),
            'vllm.engine.arg_utils':NS(AsyncEngineArgs=lambda **kw:NS(**kw)),
            'vllm.sampling_params':NS(RequestOutputKind=NS(FINAL_ONLY='final')),
            'vllm.v1.engine.async_llm':NS(AsyncLLM=Engine)}
        modules['vllm'].__version__='synthetic'
        def load(t,*a,**kw):
            if t['example_id']=='2':raise RuntimeError('synthetic decode failure')
            return np.zeros((64,2,2,3),dtype=np.uint8),{'metadata':{'frames_indices':[x for x in range(32) for _ in range(2)]}}
        async def direct(function,*args,**kw):return function(*args,**kw)
        args=NS(config=str(p),cell=0,rank=0,world=1,model='synthetic',cache=str(d),frames_sha256='pin',attempt='a')
        with patch.dict(sys.modules,modules),patch('transformers.AutoProcessor.from_pretrained',return_value=processor),patch('worker.tasks_for',return_value=[task(1),task(2)]),patch('worker.load',side_effect=load),patch('worker.prompt',return_value='prompt'),patch('worker.compare',return_value={'example_id':'1','prompt_equal':True}),patch('worker.visual_report',return_value={}),patch('worker.asyncio.to_thread',side_effect=direct):
            asyncio.run(asyncio.wait_for(worker.run(args),timeout=10))
        rows=[json.loads(l) for l in (d/'out/0/g0.jsonl').read_text().splitlines() if l.strip()]
        self.assertEqual({r['status'] for r in rows},{'complete','error'})
        for r in rows:self.assertEqual(r['layout'],'duplicate');merge.check_row(r,task(int(r['example_id'])),32,off)

    def test_B6_two_attempts_merge_514_plus_485_exactly_999(self):
        from worker import read_journal
        d=retained();(d/'0').mkdir();p=d/'0/g0.jsonl'
        rows=[row(i) for i in range(1,1000)]
        p.write_text(''.join(json.dumps(r)+'\n' for r in rows[:514]))
        done=read_journal(p,rows[0]['binding'],'duplicate');self.assertEqual(len(done),514)
        with p.open('a') as stream:
            for r in rows:
                if r['key'] not in done:stream.write(json.dumps(r)+'\n')
            stream.write(json.dumps(rows[0])+'\n')
        cfg=dict(cells=[ON],datasets=[dict(benchmark='revsi')],roots={},binding='request',output=str(d),gpus=1)
        with patch('merge.tasks_for',return_value=[task(i) for i in range(1,1000)]),patch('merge.probe_tasks',return_value=[]):
            summary=merge.merge(cfg,0,'second',tokenizer=TOK)['benchmarks']['revsi']
            self.assertEqual((summary['completed'],summary['expected'],summary['missing']),(999,999,0))
            merged=[json.loads(l)['key'] for l in (d/'0/items_second.jsonl').read_text().splitlines()]
            self.assertEqual(len(merged),len(set(merged)));self.assertEqual(set(merged),{r['key'] for r in rows})
            with self.assertRaisesRegex(ValueError,'binding'):merge.merge(dict(cfg,binding='rebound'),0,'third',tokenizer=TOK)

