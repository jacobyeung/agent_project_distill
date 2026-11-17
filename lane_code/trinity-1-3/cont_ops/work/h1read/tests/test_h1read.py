import offline_guard
import ast
import asyncio
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import re
import sys
import tarfile
import unittest
import uuid
from unittest.mock import patch
from types import SimpleNamespace as NS

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'kit/launcher'),str(ROOT/'kit/reader')]
import binding as B
import orchard_launcher as L
import export_stage as E
import orchard_stage as S
import chain_save as A
import x7 as X
import h1pair as P

def folder():
    p=ROOT/'evidence'/('test_'+uuid.uuid4().hex);p.mkdir();return p

def function(path,name):
    text=Path(path).read_text();node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    return ast.get_source_segment(text,node)

class Binding(unittest.TestCase):
    def test_closed_identities_and_namespace(self):
        for run in ('359fcc3c','17c4ffa4'):
            for step in (100,200):
                value=B.expected(run,step);self.assertEqual(B.validate(value),value)
                raw=f"{value['object']} 73 {'a'*64}\n".encode()
                self.assertEqual(B.parse(raw,value)['bytes'],73)
                if run=='359fcc3c':self.assertEqual(B.parse(raw,value),E.parse_done(raw,run,step))
        for run,step,gen,namespace in [('469ddece',100,None,'8865619b'),('17c4ffa4',400,None,'8865619b'),
             ('359fcc3c',400,None,'8865619b'),('17c4ffa4',100,None,'bad'),('359fcc3c',137,'mstop','8865619b'),
             ('17c4ffa4',201,'mstop','8865619b'),('17c4ffa4',0,'mstop','8865619b'),
             ('17c4ffa4',True,None,'8865619b'),('17c4ffa4',100,'mstopD','8865619b')]:
            with self.assertRaises(ValueError):B.expected(run,step,gen,namespace)
    def test_stop_generations_require_claim_and_actual_step(self):
        for gen in B.STOPS:
            b=B.expected('17c4ffa4',137,gen)
            self.assertTrue(b['done'].endswith('_m137.done'))
            raw=f"{b['object']} 91 {'b'*64}\n".encode()
            self.assertEqual(B.parse(raw,b,b'm137\n')['object'],b['object'])
            for claim in (None,b'm138\n',b'mstop\n'):
                with self.assertRaises(ValueError):B.parse(raw,b,claim)
            with self.assertRaises(ValueError):B.parse(raw.replace(b'8865619b',b'00000000'),b,b'm137\n')
    def test_d0_stage_and_binding_functions_byte_equal(self):
        for path,names in [('launcher/export_stage.py',['stage_export','parse_done']),
                           ('reader/worker.py',['bind','validate'])]:
            for name in names:
                candidate=function(ROOT/'kit'/path,name)
                if name=='stage_export':
                    candidate=candidate.replace("(args.run not in T.EXPORT_RUNS and (args.run, args.step) != ('469ddece', 544))",
                                                'args.run not in T.EXPORT_RUNS')
                self.assertEqual(candidate,function(ROOT/'readk/kit'/path,name))
        for path in ['reader/out/direct.py','reader/out/common.py','reader/out/export_check.py',
                     'reader/work/vendor/r3/adapter.py','reader/work/vendor/r4/adapter.py','reader/work/vendor/r5/adapter.py']:
            self.assertEqual((ROOT/'kit'/path).read_bytes(),(ROOT/'readk/kit'/path).read_bytes())
    def test_prepare_subsets_and_all_runs_steps(self):
        selections=[['a7'],['main'],['away','forward'],['main','away','forward','a7']]
        for run in ('359fcc3c','17c4ffa4'):
            for step in (100,200):
                for families in selections:
                    dest=folder()/'prepared';cfg=L.prepare('a000000001',dest,step,run=run,families=families)
                    self.assertEqual(cfg['families'],families)
                    L.validate_request(cfg);L.validate_batch((dest/'BATCH.sh').read_text(),cfg)
                    self.assertEqual(cfg['spec']['export_binding'],B.expected(run,step))
                    # Only test fixtures are prepared, under evidence, never kit/build.
                    self.assertNotIn('r0dev',json.dumps(cfg))
                    changed=copy.deepcopy(cfg);changed['spec']['export_binding']['run']='469ddece'
                    changed['plan_sha256']=L.canonical(changed['spec'])
                    with self.assertRaises(ValueError):L.validate_request(changed)
        for families in ([],['a7','a7'],['camera'],['unknown']):
            with self.assertRaises(ValueError):L.prepare('a000000001',folder()/'x',100,families=families)
    def test_stop_prepare_and_tamper(self):
        for generation in B.STOPS:
            dest=folder()/'prepared';cfg=L.prepare('a000000001',dest,137,generation=generation)
            L.validate_request(cfg)
            changed=copy.deepcopy(cfg);changed['extra']['items']=1
            with self.assertRaises(ValueError):L.validate_request(changed)
            with self.assertRaises(ValueError):L.validate_batch((dest/'BATCH.sh').read_text()+'x',cfg)
    def test_fetch_binding_before_cloud(self):
        cfg=dict(spec=dict(step=100,export_binding=B.expected('17c4ffa4',100)),assets={})
        bad=b'q8/8865619b/359fcc3c_m100.tar 12 '+b'0'*64+b'\n'
        with patch.object(Path,'is_symlink',return_value=False),patch.object(Path,'stat',return_value=NS(st_size=len(bad))),patch.object(Path,'read_bytes',return_value=bad),patch.object(S,'process_stream') as remote:
            with self.assertRaises(ValueError):E.fetch_and_stage(folder(),cfg)
            remote.assert_not_called()
    def test_return_selection_has_opaque_family_raw_journals(self):
        root=folder();f=root/'a7/a0/results/budget_2048/0/items_a0.jsonl';f.parent.mkdir(parents=True);f.write_text('{}\n')
        self.assertIn(str(f.relative_to(root)),A.members(root))
        (root/'a7/ASSET_CHECK.json').write_text('{}')
        self.assertIn('a7/ASSET_CHECK.json',A.members(root))

class Assets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg=json.loads((ROOT/'kit/launcher/EXTRA.json').read_text())
        cls.rows=[json.loads(l) for l in (ROOT/'assets/e52a690b.jsonl').read_text().splitlines()]
    def test_pins_inventory_and_determinism(self):
        reg=self.reg;archive=ROOT/'assets/d81f4a26.tar'
        self.assertEqual(archive.stat().st_size,reg['files'][archive.name]['bytes'])
        self.assertEqual(X.sha(archive),reg['files'][archive.name]['sha256'])
        class Sink:
            def __init__(self):self.h=hashlib.sha256();self.n=0
            def write(self,b):self.h.update(b);self.n+=len(b);return len(b)
        sink=Sink();names=[]
        with tarfile.open(archive,'r:') as source,tarfile.open(fileobj=sink,mode='w|',format=tarfile.USTAR_FORMAT) as target:
            for member in source:
                names.append(member.name)
                self.assertRegex(member.name,r'^[0-9a-f]{24}/[0-9a-f]{24}\.png$')
                self.assertEqual((member.uid,member.gid,member.mtime,member.uname,member.gname),(0,0,0,'',''))
                raw=source.extractfile(member).read()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),reg['frames'][member.name]['sha256'])
                m=tarfile.TarInfo(member.name);m.size=len(raw);m.mode=0o644;target.addfile(m,io.BytesIO(raw))
        self.assertEqual(names,sorted(names));self.assertEqual(len(names),3136)
        self.assertEqual(sink.h.hexdigest(),reg['files'][archive.name]['sha256'])
        self.assertEqual(sink.n,archive.stat().st_size)
    def test_rewrite_exact_indices_prompts_answers_denominators(self):
        X.validate_items(self.rows,self.reg)
        mapping=json.loads((ROOT/'evidence/ID_MAP.json').read_text())
        original=list(map(json.loads,(ROOT/'in/out/qsets/R0_QUESTIONS_dev_f32.jsonl').read_text().splitlines()))
        sys.path.insert(0,str(ROOT/'kit/reader/evaluator'))
        from evalpath.official import build_prompt_context
        for row in self.rows:
            old=original[mapping[row['id']]['source_line']-1]
            self.assertEqual(row['source_frame_indices'],old['frame_indices'])
            self.assertEqual(row['ground_truth'],old['answer'])
            self.assertEqual(build_prompt_context(row,'ours'),build_prompt_context(old,'ours'))
            self.assertEqual(row['options'],old['options'])
        self.assertEqual(self.reg['registered_rooms'],100);self.assertEqual(self.reg['deferred_rooms'],2)
        self.assertEqual(self.reg['rooms_with_items'],98)
        with self.assertRaises(ValueError):X.validate_items(self.rows[:-1],self.reg)
    def test_item_and_frame_references_opaque(self):
        for row in self.rows:
            self.assertRegex(row['id'],r'^[0-9a-f]{24}$')
            self.assertRegex(row['scene'],r'^[0-9a-f]{24}$')
            for ref in row['frame_refs']:self.assertNotRegex(ref,r'scannet|r0|vsi|revsi|distill|split|sft|h1')
        self.assertEqual(X.sha(ROOT/'assets/e52a690b.jsonl'),self.reg['files']['e52a690b.jsonl']['sha256'])
    def test_staging_rejects_corruption_before_extraction(self):
        reg=copy.deepcopy(self.reg)
        reg['files']['d81f4a26.tar'].update(path=str(ROOT/'assets/d81f4a26.tar'),sha256='0'*64)
        with self.assertRaises(ValueError):X.stage_assets(reg,folder())
    def test_all_constants(self):
        self.assertEqual(set(X.CONSTANTS),set(X.COUNTS))
        self.assertEqual(X.CONSTANTS['obj_appearance_order'],25)
        self.assertEqual(X.CONSTANTS['object_rel_distance'],25)
        self.assertEqual(sum(X.COUNTS.values()),2169)

class Scores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,str(ROOT/'kit/reader/evaluator'))
        import scoring
        cls.scoring=scoring
    def test_numeric_and_options_use_official_scores(self):
        for typ in X.COUNTS:
            task=dict(benchmark='devrows',question_type=typ,thinking=True,ground_truth='2',options=[],answer_type='numerical')
            if typ not in ('object_counting','object_abs_distance','object_size_estimation','room_size_estimation'):
                task.update(ground_truth='A',options=['A. left','B. right'],answer_type='multiple_choice')
            raw='work</think>\n'+task['ground_truth']
            a=self.scoring.score_item(task,raw,12);b=X.score_policy(self.scoring.score_item,task,raw,12)
            self.assertEqual(a,b);self.assertEqual(b['score'],1)
    def test_cap_nonanswer_refusal_zero_in_denominator(self):
        t=dict(benchmark='devrows',question_type='object_counting',thinking=True,ground_truth='2',options=[],answer_type='numerical')
        for raw,tokens,finish in [('work</think>\n2',64,'stop'),('work</think>\n2',12,'length'),
                                 ('work</think>\nI cannot answer',12,'stop'),('work</think>\n2, but I cannot determine',12,'stop'),('',0,'stop'),('2',1,'stop')]:
            self.assertEqual(X.score_policy(self.scoring.score_item,t,raw,tokens,64,finish)['score'],0)
    def test_trained_layout_uses_original_guards(self):
        import think_settings,budget
        cell=json.loads((ROOT/'kit/reader/e193_contract.json').read_text())['main']['cells'][0]
        self.assertEqual((cell['frames'],cell['layout'],cell['benchmarks']),(32,'duplicate',['devrows']))
        think_settings.validate(cell)
        with self.assertRaises(ValueError):think_settings.validate(dict(cell,layout='spread'))
        row=dict(thinking=True,model='cp1m200',decoding='greedy',frames=32,layout='duplicate',max_new_tokens=16384,binding='a',status='complete')
        budget.validate_source(row,cell,'a')
        with self.assertRaises(ValueError):budget.validate_source(dict(row,layout='spread'),cell,'a')
        self.assertFalse(hasattr(X,'install_layout'))
        for path in (ROOT/'kit/reader/evaluator').rglob('*.py'):
            self.assertEqual(path.read_bytes(),(ROOT/'readk'/path.relative_to(ROOT)).read_bytes())

class Pairing(unittest.TestCase):
    def row(self,id,room,score,typ='object_counting',family='main',step=200):
        return dict(id=id,room=room,scene=room,score=score,task_type=typ,family=family,step=step,budget=2048,scoring_basis='answer')
    def test_harm_sign_and_f1_filter(self):
        a=[self.row(str(i),str(i//2),1) for i in range(6)]
        b=[dict(r,score=0) for r in a]
        v=P.compare(a,b,200)['families']['main']['object_counting']
        self.assertEqual((v['delta_pp'],v['ci95_pp'],v['harm']),(-100,[-100,-100],True))
        v=P.compare(b,a,200)['families']['main']['object_counting'];self.assertFalse(v['harm'])
        a=[dict(r,task_type='object_abs_distance') for r in a];b=[dict(r,task_type='object_abs_distance') for r in b]
        self.assertFalse(P.compare(a,b,200)['families']['main']['object_abs_distance']['harm'])
    def test_physical_room_bootstrap_unequal_cluster_sizes(self):
        a=[self.row('a','x',0),self.row('b','x',0),self.row('c','y',1)]
        b=[dict(r,score=1-r['score']) for r in a]
        v=P.compare(a,b,200)['families']['main']['object_counting']
        self.assertEqual(v['rooms'],2);self.assertAlmostEqual(v['delta_pp'],100/3)
        self.assertEqual(v['ci95_pp'],[-100,100]);self.assertEqual(v['seed'],20261115)
    def test_metadata_duplicates_steps_missing_and_opaque_alias(self):
        a=[self.row('a','x',1,family='r0dev')];b=[dict(a[0],family='a7')]
        self.assertEqual(P.compare(a,b,200)['shared_items'],1)
        with self.assertRaisesRegex(ValueError,'membership'):P.compare(a+[self.row('b','y',0)],b,200)
        for bad in ([dict(b[0],room='z')],[dict(b[0],step=100)],[dict(b[0],score=float('nan'))],b+b):
            with self.assertRaises(ValueError):P.compare(a,bad,200)
    def test_real_d0_self_all_deltas_and_intervals_zero(self):
        p=ROOT/'readk/kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl'
        rows=P.load([p]);result=P.compare(rows,rows,200)
        self.assertEqual(result['shared_items'],1825)
        for family in result['families'].values():
            for typ in family.values():
                self.assertEqual(typ['delta_pp'],0);self.assertEqual(typ['ci95_pp'],[0,0]);self.assertFalse(typ['harm'])
        (ROOT/'evidence/D0_SELF_PAIR.json').write_text(json.dumps(result,indent=2)+'\n')


class Chain(unittest.TestCase):
    def test_extra_only_chain_and_failure(self):
        spec=importlib.util.spec_from_file_location('test_new_chain',ROOT/'kit/reader/chain.py')
        C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
        for failure in (False,True):
            root=folder()/'run'
            cfg=dict(spec=dict(run=str(root),step=100,interpreters=dict(vllm='fixture')),
                families=['a7'],admission={},plan_sha256='a'*64,
                extra=json.loads((ROOT/'kit/launcher/EXTRA.json').read_text()))
            class Process:
                def __init__(self,argv,**kwargs):
                    self.stdout=io.BytesIO(b'scannet private diagnostic')
                    assert argv[-1]=='a7'
                def wait(self):
                    if failure:return 7
                    target=root/'a7';target.mkdir()
                    (target/'COMPLETE.json').write_text('{"items":1}')
                    (target/'ITEMS.jsonl').write_text(json.dumps(dict(id='x',family='a7',task_type='object_counting',score=0))+'\n')
                    return 0
            with patch.object(C.subprocess,'Popen',Process),patch.dict(C.os.environ,dict(A_JOB_CONFIG='fixture')):
                if failure:
                    with self.assertRaises(RuntimeError):C.run(cfg)
                    self.assertFalse((root/'COMPLETE.json').exists())
                else:
                    C.run(cfg);summary=json.loads((root/'SUMMARY.json').read_text())
                    self.assertEqual(summary['scores']['a7']['object_counting']['no_information_pct'],62.2)
                    self.assertEqual(summary['coverage']['registered_rooms'],100)
                    self.assertEqual(summary['scores']['a7']['object_counting']['items'],1)
                self.assertNotIn('scannet',(root/'logs/a7.hex').read_text())

class Staging(unittest.TestCase):
    def test_successful_full_local_asset_staging(self):
        reg=json.loads((ROOT/'kit/launcher/EXTRA.json').read_text())
        for name,pin in reg['files'].items():pin['path']=str(ROOT/'assets'/name)
        root=folder();rows,frames=X.stage_assets(reg,root)
        self.assertEqual(len(rows),2169)
        check=json.loads((root/'ASSET_CHECK.json').read_text())
        self.assertTrue(check['verified']);self.assertEqual(check['members'],3136)
        with self.assertRaises(FileExistsError):X.stage_assets(reg,root)

class ExportTransport(unittest.TestCase):
    def test_ordered_parts_digest_and_stop_claim(self):
        from contextlib import contextmanager
        for generation,step in ((None,100),('mstop',137),('mstopB',138),('mstopC',139)):
            for corrupt in (False,True):
                root=folder();(root/'archives').mkdir();(root/'bootstrap').mkdir()
                bound=B.expected('17c4ffa4',step,generation)
                chunks=[b'one',b'two',b'three',b'four'];body=b''.join(chunks)
                pin='0'*64 if corrupt else hashlib.sha256(body).hexdigest()
                receipt=root/'input.done';receipt.write_text(f"{bound['object']} {len(body)} {pin}\n")
                claim=root/'input.claim';claim.write_text(f'm{step}\n')
                def path(value):
                    return receipt if str(value)==bound['done'] else claim if str(value)==bound['claim'] else Path(value)
                seen=[]
                @contextmanager
                def stream(argv,env,log):
                    seen.append(argv[-1]);yield io.BytesIO(chunks[len(seen)-1])
                cfg=dict(spec=dict(step=step,export_binding=bound,artifact={},models={}),assets=dict(gcloud_config='fixture'))
                with patch.object(E,'Path',path),patch.object(S,'room'),patch.object(S,'cloud_environment',return_value={}),\
                     patch.object(S,'process_stream',stream),patch.object(E,'stage_export',return_value=dict(artifact_sha256='a'*64)) as stage:
                    if corrupt:
                        with self.assertRaises(ValueError):E.fetch_and_stage(root,cfg)
                        stage.assert_not_called()
                    else:
                        E.fetch_and_stage(root,cfg)
                        self.assertEqual(stage.call_args.args[0].run,'17c4ffa4')
                        self.assertEqual(stage.call_args.args[0].step,step)
                        self.assertEqual((root/'archives/export.tar').read_bytes(),body)
                self.assertEqual(seen,['gs://cmu-gpucloud-jjyeung/'+bound['object']+'.part%02d-of-04'%i for i in range(4)])

class ReturnUnpack(unittest.TestCase):
    def test_verified_unpack_and_tamper_refusal(self):
        spec=importlib.util.spec_from_file_location('unpack_return',ROOT/'tools/unpack_return.py')
        U=importlib.util.module_from_spec(spec);spec.loader.exec_module(U)
        root=folder();(root/'fetched').mkdir()
        config=dict(token='a000000001',plan_sha256='a'*64)
        (root/'CONFIG.json').write_text(json.dumps(config));(root/'SUBMISSION.json').write_text('{"status":"SUBMITTED","job":1}')
        archive=root/'fetched/result.tar.gz'
        with tarfile.open(archive,'w:gz') as tf:
            for name,raw in [('COMPLETE.json',json.dumps(dict(plan_sha256='a'*64,synthetic=False)).encode()),('ITEMS.jsonl',b'{}\n')]:
                m=tarfile.TarInfo(name);m.size=len(raw);tf.addfile(m,io.BytesIO(raw))
        receipt=dict(schema='a3',token='a000000001',job=1,plan_sha256='a'*64,synthetic=False,status='COMPLETE',complete=True,
                     conflicting_terminal_markers=False,returncode=0,archive=dict(bytes=archive.stat().st_size,sha256=X.sha(archive)))
        (root/'fetched/EXIT.json').write_text(json.dumps(receipt))
        target=U.unpack(root);self.assertEqual((target/'ITEMS.jsonl').read_bytes(),b'{}\n')
        receipt['job']=2;(root/'fetched/EXIT.json').write_text(json.dumps(receipt))
        with self.assertRaises(ValueError):U.unpack(root)

class Bootstrap(unittest.TestCase):
    def test_embedded_bootstrap_checks_before_execution(self):
        import base64
        import orchard_job as J
        for run in ('359fcc3c','17c4ffa4'):
            dest=folder()/'prepared';cfg=L.prepare('a000000001',dest,200,run=run)
            script=(dest/'BATCH.sh').read_text()
            raw=base64.b64decode(re.search(r"^raw=base64\.b64decode\('([^']+)'",script,re.M)[1])
            root=folder()
            with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
                for member in tf:
                    p=root/member.name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(tf.extractfile(member).read())
            with patch.object(sys,'argv',['fixture','--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')]),patch.object(J,'run',return_value=0) as execute:
                with self.assertRaises(SystemExit) as e:J.main()
                self.assertEqual(e.exception.code,0);execute.assert_called_once()
            bad=copy.deepcopy(cfg);bad['spec']['step']=400;bad['plan_sha256']=L.canonical(bad['spec'])
            (root/'bootstrap/CONFIG.json').write_text(json.dumps(bad))
            with patch.object(sys,'argv',['fixture','--root',str(root),'--config',str(root/'bootstrap/CONFIG.json')]),patch.object(J,'run') as execute:
                with self.assertRaises(ValueError):J.main()
                execute.assert_not_called()

if __name__=='__main__':unittest.main()
