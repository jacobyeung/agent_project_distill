"""CPU-only legacy budget annotation and isolated continuation-cap regressions."""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import test_fork_r2 as fixtures
from budget import derive, source_lines, CLOSE
from budget_admission import BudgetContext
from budget_annotation import annotate_budget, verify_budget_annotation
from provenance import annotate, sha
from evalpath.items import digest
from scoring import score_item
import budget_merge

TOK=fixtures.TOK


class BudgetN(unittest.TestCase):
    def legacy(self):
        d=fixtures.retained();original=d/'original';original.mkdir()
        archive=d/'code.tar';archive.write_bytes(b'sealed legacy code fixture')
        cfg=dict(cells=[deepcopy(fixtures.ON)],datasets=[dict(benchmark='revsi')],roots={},gpus=1,
                 thinking=True,max_tokens=16384,models={},source_sha256=sha(archive))
        cfg['binding']=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
        cfg['output']=str(original)
        request=d/'request.json';request.write_text(json.dumps(cfg))
        sources=[fixtures.row(1,'r</think>\n'+' '*80+'3'),fixtures.row(2,'x'*4100),fixtures.row(3,'y'*4100)]
        for r in sources:r['binding']=digest(dict(request=cfg['binding'],cell=0))
        on=original/'g0.jsonl';on.write_text(''.join(json.dumps(r)+'\n' for r in sources))
        class Engine:
            async def generate(self,req,params,request_id):
                answer=str(int(request_id.rsplit(':',1)[1])+2)
                yield NS(prompt_token_ids=req['prompt_token_ids'],outputs=[NS(text=answer,token_ids=TOK.encode(answer),finish_reason='stop')])
        async def request_for(r):return dict(prompt='prompt'),r['media']
        asyncio.run(derive(sources=source_lines(on),cell=cfg['cells'][0],source_binding=sources[0]['binding'],
            request_binding=cfg['binding'],cell_index=0,budgets=(2048,4096),tokenizer=TOK,
            engine=Engine(),params=NS(max_tokens=64,temperature=0),request_for=request_for,
            path_for=lambda b:original/f'budget_{b}.g0.jsonl'))
        # Match sealed writer bytes: no source layout, no cap policy, item-key receipts.
        for r in sources:r.pop('layout')
        on.write_text(''.join(json.dumps(r)+'\n' for r in sources))
        for b in (2048,4096):
            arm=original/f'budget_{b}.g0.jsonl';receipts=arm.with_suffix('.meta.jsonl')
            rows=list(source_lines(arm).values());metas={m['source_key']:m for m,_ in source_lines(receipts).values()}
            text=[];metadata=[]
            for row,raw in rows:
                row.pop('layout',None);row.pop('answer_cap_policy',None);raw=json.dumps(row)
                m=metas[row['key']];m.pop('answer_cap_policy',None)
                m.update(key=row['key'],record_sha256=digest(raw),source_sha256=digest(next(r for r in sources if r['key']==row['key'])))
                text.append(raw+'\n');metadata.append(json.dumps(m)+'\n')
            arm.write_text(''.join(text));receipts.write_text(''.join(metadata))
        result=d/'reviewed/0';result.mkdir(parents=True)
        annotate(request,archive,on,result/'g0.jsonl',0)
        return d,request,archive,original,result,cfg

    def annotate_arm(self,p,a,original,result,b):
        with patch('budget_annotation.tasks_for',return_value=[fixtures.task(i) for i in (1,2,3)]):
            return annotate_budget(p,a,original/f'budget_{b}.g0.jsonl',result/f'budget_{b}.g0.jsonl',0,b,result/'g0.jsonl',TOK)

    def verify_arm(self,result,cfg,b):
        with patch('budget_annotation.tasks_for',return_value=[fixtures.task(i) for i in (1,2,3)]):
            return verify_budget_annotation(result/f'budget_{b}.g0.jsonl',cfg,0,b,result/'g0.jsonl',TOK)

    def test_N2_both_legacy_arms_annotate_and_merge_on_cpu(self):
        d,p,a,original,result,cfg=self.legacy()
        before={f.name:f.read_bytes() for f in original.iterdir()}
        for b in (2048,4096):
            self.annotate_arm(p,a,original,result,b)
            receipts=[r for r,_ in source_lines(result/f'budget_{b}.g0.meta.jsonl').values()]
            self.assertEqual({r['answer_cap_policy'] for r in receipts},{'continuation_64','reuse_full_on_answer'})
            for r in receipts:self.assertEqual(r['key'],r['source_key']+':'+r['record_sha256'])
            self.assertEqual(source_lines(result/f'budget_{b}.g0.jsonl')['revsi:1'],source_lines(result/'g0.jsonl')['revsi:1'])
        cfg=dict(cfg,output=str(result.parent))
        tasks=[fixtures.task(i) for i in (1,2,3)]
        with patch('merge.tasks_for',return_value=tasks),patch('merge.probe_tasks',return_value=[]),patch('budget_merge.tasks_for',return_value=tasks),patch('budget_annotation.tasks_for',return_value=tasks):
            budget_merge.merge_budgets(cfg,0,'test',tokenizer=TOK)
        for b in (2048,4096):
            summary=json.loads((result.parent/f'budget_{b}/0/summary_test.json').read_text())
            self.assertEqual(summary['benchmarks']['revsi']['completed'],3)
            self.assertEqual(summary['annotations'][0]['budget'],b)
        self.assertEqual({f.name:f.read_bytes() for f in original.iterdir()},before)

    def test_N2_annotation_cli_dispatches_budget_arm(self):
        import annotate_legacy, io
        d,p,a,original,result,cfg=self.legacy()
        argv=['annotate_legacy','--request',str(p),'--source-archive',str(a),
              '--journal',str(original/'budget_2048.g0.jsonl'),
              '--output',str(result/'budget_2048.g0.jsonl'),'--budget','2048',
              '--on-journal',str(result/'g0.jsonl')]
        with patch('sys.argv',argv),patch('sys.stdout',io.StringIO()),patch('token_audit.load_tokenizer',return_value=TOK),patch('budget_annotation.tasks_for',return_value=[fixtures.task(i) for i in (1,2,3)]):
            annotate_legacy.main()
        self.verify_arm(result,cfg,2048)

    def test_N1_missing_partial_remains_missing_in_merge(self):
        import merge
        d,p,a,original,result,cfg=self.legacy()
        on=original/'g0.jsonl';rows=source_lines(on)
        on.write_text(rows['revsi:1'][1]+'\n'+rows['revsi:3'][1]+'\n'+
                      '{"key":"revsi:2","raw_generation":"interrupted')
        target=d/'missing/0/g0.jsonl';meta=annotate(p,a,on,target,0)
        tasks=[fixtures.task(i) for i in (1,2,3)]
        with patch('merge.tasks_for',return_value=tasks),patch('merge.probe_tasks',return_value=[]):
            summary=merge.merge(dict(cfg,output=str(target.parent.parent)),0,'test',tokenizer=TOK)
        self.assertEqual(meta['missing_keys'],['revsi:2'])
        self.assertEqual(summary['benchmarks']['revsi']['missing'],1)
        self.assertEqual(summary['benchmarks']['revsi']['completed'],2)

    def test_N2_interrupted_budget_and_receipt_lines_audited(self):
        d,p,a,original,result,cfg=self.legacy();arm=original/'budget_2048.g0.jsonl';receipt=arm.with_suffix('.meta.jsonl')
        for f in (arm,receipt):
            f.write_text('{"key":"revsi:2","value":\n'+f.read_text()+'{"key":"missing","value":')
        meta=self.annotate_arm(p,a,original,result,2048)
        self.assertEqual(meta['skipped_line_count'],2)
        self.assertEqual(meta['receipt_recovery']['skipped_line_count'],2)
        self.assertEqual(meta['missing_keys'],['missing'])
        self.verify_arm(result,cfg,2048)

    def test_N2_wrong_binding_hash_and_classification_refused(self):
        for field,value in [('binding','wrong'),('source_sha256','wrong'),('record_sha256','wrong'),('forced_close',True),('answer_cap_policy','invented')]:
            with self.subTest(field=field):
                d,p,a,original,result,cfg=self.legacy();f=original/'budget_2048.g0.meta.jsonl'
                rows=[json.loads(x) for x in f.read_text().splitlines() if x.strip()];rows[0][field]=value
                f.write_text(''.join(json.dumps(r)+'\n' for r in rows))
                with self.assertRaises(ValueError):self.annotate_arm(p,a,original,result,2048)
                self.assertFalse((result/'budget_2048.g0.jsonl').exists())

    def test_N2_recomputed_request_binding_required(self):
        d,p,a,original,result,cfg=self.legacy();cfg['cells'][0]['model']='cp1m200';p.write_text(json.dumps(cfg))
        with self.assertRaisesRegex(ValueError,'recomputed'):self.annotate_arm(p,a,original,result,2048)

    def test_N2_rehashed_budget_copy_tampering_refused(self):
        d,p,a,original,result,cfg=self.legacy();meta=self.annotate_arm(p,a,original,result,2048)
        arm=result/'budget_2048.g0.jsonl';rows=[json.loads(x) for x in arm.read_text().splitlines()]
        rows[0]['seconds']=12345;arm.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        meta['annotated_sha256']=sha(arm);arm.with_suffix('.annotation.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'changed original content'):self.verify_arm(result,cfg,2048)

    def test_N2_merge_checks_annotation_content(self):
        d,p,a,original,result,cfg=self.legacy()
        for b in (2048,4096):self.annotate_arm(p,a,original,result,b)
        arm=result/'budget_2048.g0.jsonl';sidecar=arm.with_suffix('.annotation.json')
        meta=json.loads(sidecar.read_text());rows=[json.loads(x) for x in arm.read_text().splitlines()]
        rows[1]['seconds']=12345
        raw=json.dumps(rows[1]);arm.write_text(''.join(json.dumps(r)+'\n' for r in rows))
        receipts=arm.with_suffix('.meta.jsonl');rr=[json.loads(x) for x in receipts.read_text().splitlines()]
        for r in rr:
            if r['source_key']=='revsi:2':r.update(key='revsi:2:'+digest(raw),record_sha256=digest(raw))
        receipts.write_text(''.join(json.dumps(r)+'\n' for r in rr))
        meta.update(annotated_sha256=sha(arm),annotated_receipts_sha256=sha(receipts));sidecar.write_text(json.dumps(meta))
        tasks=[fixtures.task(i) for i in (1,2,3)]
        with patch('merge.tasks_for',return_value=tasks),patch('merge.probe_tasks',return_value=[]),patch('budget_merge.tasks_for',return_value=tasks),patch('budget_annotation.tasks_for',return_value=tasks):
            with self.assertRaisesRegex(ValueError,'changed original content'):
                budget_merge.merge_budgets(dict(cfg,output=str(result.parent)),0,'test',tokenizer=TOK)

    def test_N4_budget_evidence_relocates_with_result(self):
        d,p,a,original,result,cfg=self.legacy();self.annotate_arm(p,a,original,result,2048)
        archived=fixtures.retained()/'0';shutil.copytree(result,archived)
        self.verify_arm(archived,dict(cfg,output=str(archived.parent)),2048)

    def test_N3_continuation_65_tokens_refused_after_consistent_rehash(self):
        # Everything except token count is valid; removing only >64 must turn this red.
        helper=fixtures.Fork();d,cfg,rows,calls,kwargs=helper.derived()
        path=d/'0/budget_2048.g0.jsonl';record=source_lines(path)['revsi:2'][0]
        meta=next(m for m,_ in source_lines(path.with_suffix('.meta.jsonl')).values() if m['source_key']=='revsi:2')
        for count in (64,65):
            answer=' '*(count-1)+'4';r=deepcopy(record);m=deepcopy(meta)
            text=TOK.decode(rows[1]['token_ids'][:2048])+CLOSE+answer
            scored=score_item(dict(fixtures.task(2),thinking=True),text,count,cap=64,finish='length')
            r.update(raw_generation=answer,raw_answer=answer,token_ids=TOK.encode(answer),scoring_text=text,
                     answer_tokens=count,finish_reason='length',**scored)
            r['at_4096']=dict(raw_generation=text,**scored)
            raw=json.dumps(r);m.update(key=r['key']+':'+digest(raw),record_sha256=digest(raw),answer_tokens=count)
            context=BudgetContext(cfg,0,2048,TOK)
            if count==64:context.add(rows[1],r,raw,m,fixtures.task(2))
            else:
                with self.assertRaisesRegex(ValueError,'continuation cap'):
                    context.add(rows[1],r,raw,m,fixtures.task(2))
