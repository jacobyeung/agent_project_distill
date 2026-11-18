"""Offline r6 admission, population, scoring, paired summary and legacy proofs."""
import offline_guard
from collections import Counter
from contextlib import redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT.parent/'h1read'
SOURCE = Path('/scratch/jjyeung/orch_n30/rows_r1/out/vsti_rel_dev_r0')
sys.path[:0] = [str(ROOT), str(ROOT/'kit/launcher'), str(ROOT/'kit/reader'), str(ROOT/'kit/reader/evaluator')]
import orchard_launcher as L
import binding as B
import chain_save as A
import r6 as R6
import x7 as X
import vsti_summary as V
from evalpath import official
from tools.item_ids import decode_inventories


def folder():
    path = ROOT/'evidence'/('test_fixv1_'+uuid.uuid4().hex)
    path.mkdir(); return path


def load(path):
    return json.loads(Path(path).read_text())


def rows():
    return [json.loads(line) for line in (ROOT/'assets/b62c14e9.jsonl').read_text().splitlines()]


def prepared(root, run='469ddece', step=544, generation='mstop', types=None):
    return L.prepare('a000000001',root/'prepared',step,run=run,generation=generation,families=['r6'],types=types)


def synthetic(root, cfg, scores):
    root.mkdir(parents=True); (root/'r6').mkdir()
    (root/'SPEC.json').write_text(json.dumps(cfg['spec']))
    (root/'SUMMARY.json').write_text(json.dumps(dict(complete=True, synthetic=True)))
    values=[]
    for index, task in enumerate(rows()):
        score=scores(task,index)
        prediction=task['answer'] if score else next(c for c in 'AB' if c!=task['answer'])
        values.append(dict(id=task['id'],family='r6',room=task['room'],scene=task['scene'],
            task_type=task['question_type'],predicted_letter=prediction,prediction=prediction,
            gold_letter=task['answer'],score=score,step=cfg['spec']['step'],budget=2048,
            scoring_basis='answer',template_capture=index%3==0,synthetic=True))
    raw=''.join(json.dumps(r,sort_keys=True)+'\n' for r in values)
    (root/'r6/ITEMS.jsonl').write_text(raw); (root/'ITEMS.jsonl').write_text(raw)
    return root


class SmallTests(unittest.TestCase):
    def test_both_cli_prepares_counts_filters_and_embedded_pins(self):
        for run,step,gen in [('469ddece',544,'mstop'),('673bc60f',200,None)]:
            for selection in (None,'direct'):
                dest=folder()/'prepared'
                argv=['launcher','prepare','--run',run,'--namespace','8865619b','--step',str(step),
                      '--families','r6','--token','a000000001','--destination',str(dest)]
                if gen:argv += ['--generation',gen]
                if selection:argv += ['--types',selection]
                with patch.object(sys,'argv',argv),redirect_stdout(io.StringIO()):L.main()
                cfg=load(dest/'CONFIG.json')
                self.assertEqual(cfg['spec']['population']['r6'],dict(items=900,types=R6.COUNTS,excluded={},rooms_with_items=68))
                self.assertEqual(cfg['families'],['r6'])
                L.validate_request(cfg); L.validate_batch((dest/'BATCH.sh').read_text(),cfg)
                self.assertEqual(cfg['r6'],load(ROOT/'kit/launcher/R6.json'))
                self.assertIn('R6.json',cfg['launcher_pins'])
                capture=[h for n,h in cfg['payload_pins'].items() if n.endswith('/reader/c6.py')]
                self.assertEqual(capture,[R6.CAPTURE_SHA256])
                for name in cfg['payload_pins']:
                    self.assertNotRegex(name.lower(),r'vsti|revsi|scannet')
                print('R6_PREPARE '+json.dumps(dict(run=run,step=step,types=selection,destination=str(dest),
                       plan_sha256=cfg['plan_sha256'],population=cfg['spec']['population'])),flush=True)

    def test_unregistered_combinations_and_tampering_refuse(self):
        for run in B.RUNS:
            for step in (1,100,137,200,201,400,544,600):
                for gen in (None,*B.STOPS):
                    try:bound=B.expected(run,step,gen)
                    except ValueError:continue
                    allowed=(run,step,gen) in [('469ddece',544,'mstop'),('673bc60f',200,None)]
                    for families in (['r6'],['r6','a7'],['main','r6'],['r6','r6']):
                        if allowed and families==['r6']:L.family_gate(bound,families)
                        else:
                            with self.assertRaises(ValueError):L.family_gate(bound,families)
        cfg=prepared(folder())
        for field in ('items','capture_sha256','used_frames'):
            changed=copy.deepcopy(cfg);changed['r6'][field]=None
            with self.assertRaises(ValueError):L.validate_request(changed)
        for run,step,gen in [('17c4ffa4',200,None),('673bc60f',100,None),('673bc60f',200,'mstop'),('05b8ac69',400,None)]:
            dest=folder()/'refused'
            with self.assertRaises(ValueError):L.prepare('a000000001',dest,step,run=run,generation=gen,families=['r6'])
            self.assertFalse(dest.exists())
        changed=copy.deepcopy(cfg);changed['spec']['population']['r6']['items']=899
        changed['plan_sha256']=L.canonical(changed['spec'])
        with self.assertRaises(ValueError):L.validate_request(changed)

    def test_source_preservation_frames_and_capture_pin(self):
        reg=load(ROOT/'kit/launcher/R6.json'); items=rows(); R6.validate_items(items,reg)
        mapping=load(ROOT/'evidence/R6_ID_MAP.json')
        source=[json.loads(line) for line in (SOURCE/'items.jsonl').read_text().splitlines()]
        source_by_id={r['qid']:r for r in source}
        self.assertEqual(len(items),900);self.assertEqual(Counter(r['question_type'] for r in items),R6.COUNTS)
        used=set()
        for item in items:
            old=source_by_id[mapping[item['id']]['id']]
            for key in ('question','options','answer','fps','total_num_frames','question_type'):
                self.assertEqual(item[key],old[key])
            self.assertEqual(item['source_frame_indices'],old['frame_indices'])
            for ref,frame in zip(item['frame_refs'],old['frames']):
                self.assertEqual(reg['frames'][ref]['sha256'],frame['sha256']);used.add(ref)
            self.assertEqual(official.build_prompt_context(item,'ours'),
                old['question']+'\n'+'\n'.join(old['options'])+'\n\n'+official.DEFAULT_ANSWER_FORMAT_INSTRUCTION)
        self.assertEqual(len(used),2176);self.assertEqual(used,set(reg['used_frames']))
        self.assertEqual(reg['frames'],load(ROOT/'kit/launcher/EXTRA.json')['frames'])
        self.assertEqual((ROOT/'kit/reader/c6.py').read_bytes(),(SOURCE/'capture.py').read_bytes())
        R6.check_capture(reg)
        self.assertEqual(hashlib.sha256((SOURCE/'items.jsonl').read_bytes()).hexdigest(),
                         'b5853845aaf815c85e48e32f913efd14e8e7938c00723ff8c4a378375c4bfea3')
        for mutation in ('counts','frames','answer','empty_answer'):
            bad=copy.deepcopy(items)
            if mutation=='counts':bad.pop()
            elif mutation=='frames':bad[0]['frame_refs'][0]='unknown.png'
            elif mutation=='answer':bad[0]['answer']='Z'
            else:bad[0]['answer']=bad[0]['ground_truth']=''
            with self.assertRaises(ValueError):R6.validate_items(bad,reg)

    def test_capture_uses_b2048_trace_and_shared_scoring(self):
        import scoring
        tasks=[next(r for r in rows() if r['question_type']==t) for t in R6.COUNTS]
        scored=[]
        for index,task in enumerate(tasks):
            trace=('The camera is first seen in frame 3. ' if index%2==0 else 'The chair is seen in frame 3. ')
            trace += '</think>\n'+task['answer']
            score=X.score_policy(scoring.score_item,task,trace,20)
            self.assertEqual(score['score'],1)
            scored.append(dict(task,**score,status='complete',raw_generation=task['answer'],scoring_text=trace))
            self.assertEqual(X.score_policy(scoring.score_item,task,trace,64,cap=64)['score'],0)
        result=R6.compact(scored,tasks,200)
        self.assertEqual([r['template_capture'] for r in result],[True,False,True,False,True,False])
        self.assertTrue(all(r['predicted_letter']==r['gold_letter'] and r['score']==1 for r in result))
        reused=dict(scored[0]);reused.pop('scoring_text');reused['raw_generation']='The camera was in frame 2. </think>\n'+tasks[0]['answer']
        self.assertTrue(R6.compact([reused],[tasks[0]],544)[0]['template_capture'])

    def test_synthetic_summary_gate_bootstrap_decoding_and_refusals(self):
        base_root=folder();read_root=folder()
        base_cfg=prepared(base_root)
        read_cfg=prepared(read_root,run='673bc60f',step=200,generation=None)
        base=synthetic(base_root/'fetched/x',base_cfg,lambda t,i:i%2)
        first=next(iter(R6.COUNTS))
        read=synthetic(read_root/'fetched/x',read_cfg,lambda t,i:int(t['question_type']!=first))
        report=V.summarize(read,base)
        self.assertEqual(report['pooled']['n'],900)
        self.assertAlmostEqual(report['pooled']['template_capture_pct'],100/3)
        self.assertAlmostEqual(report['pooled']['paired']['delta_pp'],100/3)
        self.assertEqual(report['gate'],dict(pooled_accuracy_rises=True,types_wholly_below_zero=[first],passed=False))
        self.assertEqual(report['per_type'][first]['paired']['replicates'],10000)
        self.assertEqual(report['per_type'][first]['paired']['seed'],20261118)
        self.assertTrue(report['per_type'][first]['paired']['wholly_below_zero'])
        before=report['per_type'];decode_inventories(read);decode_inventories(base)
        after=V.summarize(read,base)
        self.assertEqual(after['per_type'],before)
        self.assertEqual(after['items_sha256'],hashlib.sha256((read/'r6/ITEMS.jsonl').read_bytes()).hexdigest())
        with patch.object(sys,'argv',['vsti_summary.py','--read',str(read),'--base',str(base)]),redirect_stdout(io.StringIO()) as out:V.main()
        self.assertIn('BELOW ZERO',out.getvalue());self.assertIn('Gate: FAIL',out.getvalue())
        (read_root/'SUMMARY_OUTPUT.txt').write_text(out.getvalue())
        bad=load(read/'SUMMARY.json');bad['complete']=False;(read/'SUMMARY.json').write_text(json.dumps(bad))
        with self.assertRaisesRegex(ValueError,'complete read'):V.summarize(read)
        bad['complete']=True;(read/'SUMMARY.json').write_text(json.dumps(bad))
        raw=(read/'r6/ITEMS.jsonl').read_text();lines=raw.splitlines()
        for altered in ('\n'.join(lines[:-1])+'\n',raw+lines[0]+'\n'):
            (read/'r6/ITEMS.jsonl').write_text(altered)
            with self.assertRaises(ValueError):V.summarize(read)
        (read/'r6/ITEMS.jsonl').write_text(raw)
        with self.assertRaisesRegex(ValueError,'Pair requires'):V.summarize(base,read)
        print('R6_SYNTHETIC '+json.dumps(dict(read=str(read),base=str(base),gate=after['gate'],
              delta_pp=after['pooled']['paired']['delta_pp'],ci95_pp=after['pooled']['paired']['ci95_pp'])),flush=True)

    def test_room_bootstrap_uses_whole_unequal_rooms(self):
        current=[dict(id=str(i),room='a' if i<1 else 'b',task_type='t',score=int(i<1)) for i in range(4)]
        base=[dict(r,score=0) for r in current]
        result=V.compare(current,base)
        self.assertEqual(result['delta_pp'],25)
        self.assertEqual(result['ci95_pp'],[0,100])
        self.assertEqual(result,V.compare(list(reversed(current)),base))
        self.assertFalse(result['wholly_below_zero'])

    def test_r6_chain_completes_and_reports_all_six_types(self):
        import isolated_fixture as isolated
        root=folder();payload=isolated.package(root)
        cfg=prepared(root/'r6prep',run='673bc60f',step=200,generation=None)
        cfg['spec']['run']=str(root/'run')
        cfg['spec']['interpreters']['vllm']=str(payload/'vllm_isolated.sh')
        cfg['admission']={}
        cfg['fixture_rows']=[dict(id=t['id'],family='r6',room=t['room'],task_type=t['question_type'],
                                 score=1,template_capture=i%2==0) for i,t in enumerate(rows())]
        path=root/'CONFIG.json';path.write_text(json.dumps(cfg))
        result=isolated.launch(root,payload/'vllm_isolated.sh','chain',payload/'reader/chain.py','--config',path)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        report=load(root/'run/SUMMARY.json')
        self.assertTrue(report['complete']);self.assertEqual(report['items'],900)
        self.assertEqual(report['template_capture_pct'],50)
        self.assertEqual(set(report['scores']['r6']),set(R6.COUNTS))
        for typ,value in report['scores']['r6'].items():
            self.assertEqual(value['items'],150)
            self.assertEqual(value['constant_baseline_pct'],R6.CONSTANTS[typ])
        self.assertEqual(len((root/'run/r6/ITEMS.jsonl').read_text().splitlines()),900)

    def test_r6_return_inventory_and_readonly_asset_mount(self):
        root=folder(); path=root/'r6/a0/results/budget_2048/0/items_a0.jsonl'
        path.parent.mkdir(parents=True);path.write_text('{}\n')
        self.assertIn('r6/a0/results/budget_2048/0/items_a0.jsonl',A.members(root))
        import orchard_job as J
        command=J.namespace(root,dict(families=['r6']))
        target='/project/community/jjyeung/okh7/af83c921'
        index=command.index(target)
        self.assertEqual(command[index-1:index+2],['--ro-bind',target,target])


class LegacyTests(unittest.TestCase):
    def test_main_a7_plan_bytes_and_hashes_match_h1read_every_run(self):
        module=importlib.util.spec_from_file_location('reference_fix6_launcher',REFERENCE/'kit/launcher/orchard_launcher.py')
        old=importlib.util.module_from_spec(module);module.loader.exec_module(old)
        cases=[]
        for run in B.RUNS:
            milestones=[544] if run=='469ddece' else [400,600] if run=='05b8ac69' else [100,200]
            identities=[(s,'mstop' if run=='469ddece' else None) for s in milestones]
            if run in ('17c4ffa4','673bc60f','05b8ac69'):
                low,high=(201,600) if run=='05b8ac69' else (1,200)
                identities += [(s,g) for g in B.STOPS for s in (low,high)]
            for step,gen in identities:
                for families in ([['a7']] if run=='469ddece' else [['main'],['a7']]):
                    for types in (None,'direct'):
                        kwargs=dict(run=run,step=step,generation=gen,families=families,types=types)
                        root=folder()
                        a=old.prepare('a000000001',root/'reference',**kwargs)
                        b=L.prepare('a000000001',root/'candidate',**kwargs)
                        raw=lambda value:json.dumps(value,sort_keys=True).encode()
                        self.assertEqual(raw(a['spec']),raw(b['spec']),kwargs)
                        self.assertEqual(a['plan_sha256'],b['plan_sha256'],kwargs)
                        for key in ('assets','extra'):self.assertEqual(a[key],b[key])
                        cases.append(dict(**kwargs,plan_sha256=b['plan_sha256'],plan_bytes=len(raw(b['spec']))))
        print('R6_LEGACY_PLANS '+json.dumps(cases,sort_keys=True),flush=True)
        self.assertEqual({c['run'] for c in cases},set(B.RUNS))
        # Every evaluator and export-checker source file remains identical.
        for directory in ('evaluator','out','work'):
            for path in (ROOT/'kit/reader'/directory).rglob('*'):
                if path.is_file() and '__pycache__' not in path.parts:
                    self.assertEqual(path.read_bytes(),(REFERENCE/path.relative_to(ROOT)).read_bytes(),str(path))


if __name__=='__main__':unittest.main()
