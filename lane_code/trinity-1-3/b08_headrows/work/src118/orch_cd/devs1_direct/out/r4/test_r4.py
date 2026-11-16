"""CPU validation of direction payloads and reviewed dry bindings; retains fixtures."""
import collections
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent; L=O.parents[1]; W=L/'work/r4'; R3=L/'out/r3'
B=Path('/scratch/jjyeung/orch_cd/back_dir/out/r2')
spec=importlib.util.spec_from_file_location('r4_adapter',O/'adapter.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
FAMILIES={'backdir':O/'DEV_BACKDIR','forward_twins':O/'DEV_FORWARD_TWINS'}
KITS={'cp1m200':'aws_vl64rt','f17':'aws_eval_gaps'}
REVIEWED=Path('/scratch/jjyeung/orch_cd/rv_merge_fix/work/r3')

def raw_fields(line):
    """Return the exact UTF-8 JSON value token, without reserializing it."""
    s=line.decode();decoder=json.JSONDecoder();pos=1;out={}
    while True:
        while s[pos].isspace() or s[pos]==',':pos+=1
        if s[pos]=='}':return out
        key,pos=decoder.raw_decode(s,pos)
        while s[pos].isspace() or s[pos]==':':pos+=1
        start=pos;_,pos=decoder.raw_decode(s,pos);out[key]=s[start:pos].encode()

def hash_bytes(b):return hashlib.sha256(b).hexdigest()

def kit_check(model):
    data,media,official=A.kit_import(REVIEWED/KITS[model])
    import scoring
    checks=collections.Counter()
    for fam,root in FAMILIES.items():
        _,pins,rows,cs=A.payload(root)
        dest=W/f'dry_{fam}_{model}'
        cfg=json.loads((dest/'request.json').read_text())
        tasks=data.tasks_for(cfg['datasets'][0],cfg['roots'])
        recs=json.loads((dest/'RECEIPT_TEMPLATES.json').read_text())
        prompts=json.loads((dest/'PROMPT_PINS.json').read_text())
        for t,rec in zip(tasks,recs):
            assert rec==A.receipt_template(t,cfg['cells'][0],cs[t['native']],media)
            assert prompts[t['id']]==hash_bytes(official.build_prompt_context(t,'ours').encode())
            good=scoring.score_item(t,'<think>\n\n</think>\n\n'+t['ground_truth'],8)
            wrong=next(letter for letter in A.option_contents(t['options']) if letter!=t['ground_truth'])
            bad=scoring.score_item(t,'<think>\n\n</think>\n\n'+wrong,8)
            assert good['score']==1.0 and bad['score']==0.0
            # A completed thought remains parseable at the cap; an unclosed one does not.
            capped=scoring.score_item(t,'<think>\n\n</think>\n\n'+t['ground_truth'],16384,finish='length')
            unclosed=scoring.score_item(t,'<think> '+t['ground_truth'],16384,finish='length')
            assert capped['score']==1 and capped['hit_token_cap']
            assert unclosed['score']==0 and unclosed['parse_failed']
            checks['exact_option_scoring_cases']+=4
            checks['fresh_prompt_and_receipt_matches']+=1
        A.validate_cell(cfg['cells'][0],model,root)
        if model=='cp1m200':
            import budget,think_settings
            assert budget.BUDGETS==(2048,4096)
            think_settings.validate(cfg['cells'][0])
            assert 'budgets=(2048,4096)' in (dest/'kit/evaluator/worker.py').read_text()
            assert 'merge_budgets' in (O/'adapter.py').read_text()
    print(json.dumps(dict(model=model,checks=checks,passed=True),sort_keys=True))

class PayloadTests(unittest.TestCase):
    def test_01_payloads_and_membership(self):
        for fam,root in FAMILIES.items():
            _,_,rows,cs=A.payload(root)
            self.assertEqual(len(rows),150)
            self.assertEqual(collections.Counter(r['question_type'] for r in rows),{'object_rel_direction_'+k:50 for k in ('easy','medium','hard')})
            w=json.loads((root/'WITHHOLD_SCENES.json').read_text())
            self.assertTrue(set(cs)<=set(w['natives']))
            self.assertTrue({r['room'] for r in rows}<=set(w['rooms']))
            self.assertEqual(len({r['native'] for r in rows}),40)
            self.assertEqual(len({r['room'] for r in rows}),33)
            self.assertEqual({r['stratum'] for r in rows},{A.FAMILIES[fam][1]})
            for r in rows:
                self.assertIsNone(r['released_answer']);self.assertIsNone(r['released_answer_in_options'])
                self.assertEqual(r['ground_truth'],r['answer'])

    def test_02_source_bytes(self):
        root=FAMILIES['backdir'];proof={'files':{},'task_fields':[]}
        for name in ('ITEMS.jsonl','ROWS.jsonl','CELL_ITEMS.json','EXCLUDED.jsonl'):
            self.assertEqual((root/name).read_bytes(),(B/'DEV_BACKDIR'/name).read_bytes())
            proof['files'][name]=dict(source_sha256=A.sha(B/'DEV_BACKDIR'/name),output_sha256=A.sha(root/name),identical=True)
        old=(B/'DEV_BACKDIR/TASKS.jsonl').read_bytes().splitlines()
        new=(root/'TASKS.jsonl').read_bytes().splitlines()
        for x,y in zip(old,new):
            a,b=raw_fields(x),raw_fields(y)
            unchanged=set(a)-{'fps','total_num_frames','stratum'}
            self.assertEqual(set(b)-set(a),{'label_policy','total_num_frames_lower_bound'})
            for k in unchanged:self.assertEqual(a[k],b[k],k)
            proof['task_fields'].append(dict(id=json.loads(x)['id'],fields={k:dict(source_sha256=hash_bytes(a[k]),output_sha256=hash_bytes(b[k])) for k in sorted(unchanged)}))
        proof['method']='Exact JSON value-token bytes, including option order and UTF-8 spelling; no normalization or reserialization. Only timing, stratum and label_policy may differ.'
        A.dump(O/'BYTE_IDENTITY.json',proof)

    def test_03_forward_source_and_pairing(self):
        pairs=A.jsonl(O/'PAIRS.jsonl');away=A.jsonl(FAMILIES['backdir']/'TASKS.jsonl')
        forward=A.jsonl(FAMILIES['forward_twins']/'TASKS.jsonl')
        proof=json.loads((O/'FORWARD_SOURCE_PROOF.json').read_text());cache=Path(proof['cache']['path'])
        self.assertEqual(A.sha(cache),proof['cache']['sha256'])
        wanted={p['source_qid']:p for p in pairs};found={}
        with gzip.open(cache,'rb') as f:
            for n,line in enumerate(f,1):
                r=json.loads(line)
                if r['qid'] in wanted:
                    self.assertNotIn(r['qid'],found);found[r['qid']]=(r,line,n)
        self.assertEqual(set(found),set(wanted))
        for p,a,f in zip(pairs,away,forward):
            r,line,n=found[p['source_qid']]
            self.assertEqual(r['_split'],'dev');self.assertEqual(n,p['source_cache_line'])
            self.assertEqual(hash_bytes(line),p['source_cache_line_sha256'])
            self.assertEqual(r['_source_line_sha256'],a['label_provenance']['backdir']['source_line_sha256'])
            self.assertEqual(f['id'],p['forward_id']);self.assertEqual(a['id'],p['away_id'])
            for k in ('native','room','scene','source_frame_indices','fps','total_num_frames','total_num_frames_lower_bound','options'):
                self.assertEqual(a[k],f[k])
            for k in ('question','options','answer'):self.assertEqual(f[k],r[k])
            self.assertEqual(f['answer'],r['gt_answer'])
            self.assertEqual(A.selected_content(f['answer'],f['options']),r['answer_content'])
            self.assertEqual(A.selected_content(r['gt_authority']['native_independent_label'],r['source_join']['options']),r['answer_content'])
            self.assertEqual(r['gt_authority'],a['label_provenance']['source_gt_authority']['forward_authority'])

    def test_04_baselines_recomputed(self):
        counts=json.loads((O/'COUNTS.json').read_text());manifest=json.loads((B/'MANIFEST.json').read_text())
        for fam,key in [('backdir','away'),('forward_twins','forward')]:
            rr=A.jsonl(FAMILIES[fam]/'TASKS.jsonl')
            for kind in ('easy','medium','hard'):
                subset=[r for r in rr if r['question_type'].endswith('_'+kind)]
                c=collections.Counter(A.selected_content(r['answer'],r['options']) for r in subset)
                v=counts[key][kind]
                self.assertEqual(v['contents'],dict(c));self.assertEqual(v['letters'],dict(collections.Counter(r['answer'] for r in subset)))
                for field in ('constant_answer','most_frequent_option'):
                    metric=v[field];self.assertEqual(metric['correct'],c[metric['content']]);self.assertEqual(metric['accuracy'],c[metric['content']]/50)
                self.assertEqual(v['back_family']['correct'],sum(n for k,n in c.items() if k.startswith('back')))
                if key=='away':self.assertEqual(v,manifest['answer_distributions_and_baselines']['dev_away|'+kind])

    def test_05_all_timing_and_prompt_authorities(self):
        def scan(v,path):
            if isinstance(v,dict):
                for k,x in v.items():
                    if k in ('fps','frame_rate'):self.assertIn(x,(24.0,60.0,10.0),path)
                    scan(x,path+'/'+k)
            elif isinstance(v,list):
                for i,x in enumerate(v):scan(x,path+'/'+str(i))
        for root in FAMILIES.values():
            _,_,rr,cs=A.payload(root)
            for name in ('FRAMES.json','WITHHOLD_SCENES.json','TIMING_AUTHORITY.json','FPS_RULE.json','FPS_AUTHORITY.source.json','PROMPT_SOURCES.json'):
                self.assertEqual((root/name).read_bytes(),(R3/name).read_bytes())
            for c in cs.values():
                A.validate_timing(c);self.assertEqual(c['timestamps'],[i/c['fps'] for i in c['anchor_indices']])
                self.assertEqual(c['anchor_indices'],[f['index'] for f in c['frames']])
            for p in root.iterdir():
                if p.suffix=='.json':scan(json.loads(p.read_text()),p.name)
                elif p.suffix=='.jsonl':scan(A.jsonl(p),p.name)

    def test_06_bad_timing_and_labels_refused(self):
        root=FAMILIES['backdir'];_,_,rr,cs=A.payload(root);c=next(iter(cs.values()))
        for key,value in [('fps',1),('total_num_frames',1),('anchor_indices',list(reversed(c['anchor_indices']))),('timestamps',[0]*32),('total_num_frames_lower_bound',not c['total_num_frames_lower_bound'])]:
            bad=copy.deepcopy(c);bad[key]=value
            with self.assertRaises(ValueError):A.validate_timing(bad)
        for change in [dict(answer=None),dict(released_answer='A'),dict(label_policy='unknown')]:
            with self.assertRaises(ValueError):A.strata(dict(rr[0],**change))
        cell=json.loads((root/'cells_cp1m200.json').read_text())[0]
        for key,value in [('name','old'),('thinking',False),('max_tokens',4096),('layout','spread'),('frames',64)]:
            with self.assertRaises(ValueError):A.validate_cell(dict(cell,**{key:value}),'cp1m200',root)

    def test_07_repin_does_not_allow_task_timing_or_membership_changes(self):
        src=FAMILIES['backdir']
        for field,value in [('fps',1),('source_frame_indices',[0]*32),('room','not-held-out'),('ground_truth','invalid')]:
            root=Path(tempfile.mkdtemp(prefix='tamper_',dir=W))
            for p in src.iterdir():
                if p.suffix in ('.json','.jsonl'):(root/p.name).write_bytes(p.read_bytes())
            rr=A.jsonl(root/'TASKS.jsonl');rr[0][field]=value;A.dump(root/'TASKS.jsonl',rr,lines=True)
            pins=json.loads((root/'PINS.json').read_text());pins['TASKS.jsonl']=A.sha(root/'TASKS.jsonl');A.dump(root/'PINS.json',pins)
            with self.assertRaises(ValueError):A.payload(root)

class BindingTests(unittest.TestCase):
    def test_08_all_kit_bytes_unchanged_and_requests(self):
        evidence=[]
        for fam in ('main',*FAMILIES):
            for model,kit in KITS.items():
                dest=W/f'dry_{fam}_{model}';cfg=json.loads((dest/'request.json').read_text())
                status=json.loads((dest/'BIND_STATUS.json').read_text())
                self.assertTrue(cfg['build_only']);self.assertEqual(status['tasks'],1525 if fam=='main' else 150)
                self.assertEqual(status['missing_labels'],0);self.assertEqual(status['unavailable_released'],150)
                self.assertEqual(cfg['max_tokens'],16384);self.assertTrue(cfg['thinking']);self.assertEqual(cfg['temperature'],0)
                pins=json.loads((dest/'kit/CODE_PINS.json').read_text())
                for name,h in pins.items():
                    self.assertEqual(A.sha(REVIEWED/kit/'evaluator'/name),h)
                    self.assertEqual((dest/'kit/evaluator'/name).read_bytes(),(REVIEWED/kit/'evaluator'/name).read_bytes())
                self.assertEqual(A.sha(dest/'kit/source.tar'),cfg['source_sha256'])
                evidence.append(dict(family=fam,model=model,dest=str(dest),files=len(pins),code_unchanged=True,
                    source_sha256=cfg['source_sha256'],request_sha256=A.sha(dest/'request.json'),
                    receipt_sha256=A.sha(dest/'RECEIPT_TEMPLATES.json'),prompt_sha256=A.sha(dest/'PROMPT_PINS.json')))
        A.dump(O/'DRY_BINDS.json',evidence)

    def test_09_main_binding_compatibility(self):
        evidence=[]
        for model,oldname in [('cp1m200','cp1'),('f17','f17')]:
            old=L/'work/r3'/('final_'+oldname);new=W/f'dry_main_{model}'
            files=sorted(str(p.relative_to(old)) for p in old.rglob('*') if p.is_file())
            self.assertEqual(files,sorted(str(p.relative_to(new)) for p in new.rglob('*') if p.is_file()))
            records=[]
            for name in files:
                original=(old/name).read_bytes();actual=(new/name).read_bytes();normalized=actual
                if name in ('request.json','RECEIPT_TEMPLATES.json'):
                    normalized=actual.replace(str(new).encode(),str(old).encode())
                    if name=='request.json':
                        cfg=json.loads(normalized);request={k:v for k,v in cfg.items() if k not in ('binding','output')}
                        cfg['binding']=hash_bytes(json.dumps(request,sort_keys=True).encode())
                        normalized=(json.dumps(cfg,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
                    replay=W/f'compat_{model}'/name;replay.parent.mkdir(exist_ok=True);replay.write_bytes(normalized)
                self.assertEqual(original,normalized,name)
                records.append(dict(file=name,original_sha256=hash_bytes(original),new_sha256=hash_bytes(actual),
                    normalized_sha256=hash_bytes(normalized),literal_equal=actual==original))
            evidence.append(dict(model=model,original=str(old),new=str(new),files=records,
                rule='Only replace the fresh destination path with the original destination path and recompute its covered request binding. No other field changes, including adapter hash.'))
        A.dump(O/'PASS3_COMPATIBILITY.json',evidence)

    def test_10_new_receipt_timing_and_prompts(self):
        for fam,root in FAMILIES.items():
            _,_,rows,cs=A.payload(root)
            self.assertEqual((W/f'dry_{fam}_cp1m200/PROMPT_PINS.json').read_bytes(),(W/f'dry_{fam}_f17/PROMPT_PINS.json').read_bytes())
            for model in KITS:
                dest=W/f'dry_{fam}_{model}';recs=json.loads((dest/'RECEIPT_TEMPLATES.json').read_text())
                for t,rec in zip(sorted(rows,key=lambda r:r['id']),recs):
                    c=cs[t['native']];rep=2 if model=='cp1m200' else 1;indices=[i for i in c['anchor_indices'] for _ in range(rep)]
                    self.assertEqual(rec['audit']['metadata'],dict(fps=c['fps'],frames_indices=indices,total_num_frames=c['total_num_frames'],height=c['hw'][0],width=c['hw'][1]))
                    self.assertEqual(rec['audit']['timestamps'],[i/c['fps'] for i in indices])
                    self.assertEqual([f['index'] for f in rec['frames']],indices)
                    self.assertEqual(rec['audit']['total_num_frames_lower_bound'],c['total_num_frames_lower_bound'])
                with self.assertRaisesRegex(ValueError,'Dry bind'):A.verify_bound(dest)

    def test_11_reviewed_prompt_and_scorer_execution(self):
        results=[]
        for model in KITS:
            p=subprocess.run(['/scratch/jjyeung/envs/p1cpu/bin/python','-I','-s',str(__file__),'--kit-check',model],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr);results.append(json.loads(p.stdout))
        A.dump(O/'SCORER_CHECKS.json',results)

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--kit-check':kit_check(sys.argv[2])
    else:unittest.main(verbosity=2)
