"""Exercise the built delivery at each review boundary."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
os.environ['CUDA_VISIBLE_DEVICES']=''
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
import hashlib
import json
import re
import runpy
import subprocess
import tempfile
import types
import io
import builtins
import contextlib
import tarfile
import unittest
from unittest.mock import patch
import build_depth as BD
import layout


def temp():return Path(tempfile.mkdtemp(dir=HERE/'tests',prefix='fix_'))


class FixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.info=json.loads((HERE/'out/BUILD.json').read_text());cls.root=temp()
        cls.package=cls.root/'a';cls.payload=cls.root/'p'
        BD.B.extract((HERE/'out/delivery.tgz').read_bytes(),cls.package)
        BD.B.extract((cls.package/'0.tgz').read_bytes(),cls.payload)
        cls.files={m.name:d for m,d in BD.B.read_tar((cls.package/'0.tgz').read_bytes())}
        sys.path.insert(0,str(cls.payload));import l
        cls.loader=l.install(cls.payload)
        raw=(HERE/'out/delivery.tgz').read_bytes()
        assert BD.B.sha(raw)==cls.info['delivery_sha256']
        assert len(raw)==cls.info['delivery_bytes']
        cls.evidence={k:cls.info[k] for k in ('token','delivery_sha256','delivery_bytes','payload_sha256','plan_sha256')}

    @classmethod
    def tearDownClass(cls):
        import j
        (HERE/'out/FIX_CHECKS.json').write_text(j.wire_dumps(cls.evidence,indent=2)+'\n')

    def test_actual_job_stage_built_delivery(self):
        from orchard_h10 import job
        S,J,*_=job.template()
        root=temp();logical='/scratch/jjyeung/b0';d=J.physical(root,logical+'/d');d.mkdir(parents=True)
        for n in ('1','2'):(d/n).write_bytes(b'0')
        policy=dict(vnice=logical+'/d/1',terminator=logical+'/d/2',authorized=True)
        (d/'3.json').write_bytes(BD.B.jd(policy));source=root/'4';source.write_bytes(b'0')
        assets=dict(groups=[],bwrap_pin=dict(path=str(source),bytes=1,sha256=BD.B.sha(b'0')),
                    vnice_sha256=BD.B.sha(b'0'),terminator_sha256=BD.B.sha(b'0'))
        cfg=json.loads(self.files['9.json']);cfg.update(json.loads((self.package/'0.json').read_text()));cfg['logical']=logical
        inputs=dict(archives=[],files={'0':dict(path=logical+'/d/3.json',bytes=(d/'3.json').stat().st_size,sha256=job.sha(d/'3.json'))},policy=policy,policy_receipt='0')
        assets_text=(Path(job.__file__).parent/'vendor/ORCHARD_ASSETS.json').read_text()
        loads=json.loads;copy=S.copy_parts
        def copying(parts,dest,opener,**kw):
            if dest.name=='c':opener=lambda p:(self.package/'0.tgz').open('rb')
            return copy(parts,dest,opener,**kw)
        with patch('orchard_h10.s.materialize'),patch.object(job.json,'loads',side_effect=lambda s,*a,**kw:assets if s==assets_text else loads(s,*a,**kw)),patch.object(S,'copy_parts',side_effect=copying),patch.object(S,'room'):
            receipt=job.stage(root,cfg,inputs,S,J)
        installed=J.physical(root,logical+'/p')
        for n,h in self.info['payload_files'].items():self.assertEqual(BD.B.sha(Path(str(installed/n)).read_bytes()),h)
        total=sum(map(len,self.files.values()));self.assertLess(total,32*1024**2)
        self.evidence['staging']=dict(passed=True,expanded_bytes=total,limit_bytes=32*1024**2,
            actual_function='orchard_h10.job.stage',external_assets='tiny local fixtures',code_receipt=receipt['code'])

    def test_label_free_and_exact_prompt_rgb_bindings(self):
        for n,data in self.files.items():
            if n.endswith('.json'):self.assertEqual(layout.clean(json.loads(data)),json.loads(data),n)
            if n.endswith('.jsonl'):
                for line in data.splitlines():self.assertEqual(layout.clean(json.loads(line)),json.loads(line),n)
        raw=(BD.GB/'out2/t1/delivery.tgz').read_bytes()
        parent={m.name:d for m,d in BD.B.read_tar(raw)}
        original={m.name:d for m,d in BD.B.read_tar(parent['0.tgz'])}
        before=json.loads(original['g/0.json'])['items'];after=json.loads(self.files['g/0.json'])['items']
        from e2e_reader import parity
        paths=self.info['layout']['paths']
        frames=next(n for n in original if n.endswith('/FRAMES.json') and n.startswith('b/'))
        dense=next(n for n in original if n.endswith('/DENSE_MANIFEST.json'))
        settings=dict(frames_root='/tmp/0',frames_json=json.loads(original[frames]),dense_manifest=json.loads(original[dense]))
        import j
        self.assertEqual(original[frames],j.raw(self.files[paths[frames]]))
        self.assertEqual(original[dense],j.raw(self.files[paths[dense]]))
        for a,b in zip(before,after):
            self.assertEqual(parity.bind_item(a['task'],settings,verify=False),parity.bind_item(b['task'],settings,verify=False))
            self.assertEqual(a['mapping']['frame_binding_sha256'],b['mapping']['frame_binding_sha256'])
            self.assertEqual(layout.digest(b['task']),b['mapping']['task_sha256'])
        self.assertEqual(len(after),150)
        self.evidence['labels']=dict(passed=True,all_data_assets_scanned=True,exact_prompt_rgb_bindings=150)

    def test_opaque_members_sources_and_launch_scripts(self):
        for n in self.files:
            self.assertFalse(any(w in n.lower() for w in layout.DENY),n)
        parent={m.name:d for m,d in BD.B.read_tar((BD.GB/'out2/t1/delivery.tgz').read_bytes())}
        original={m.name:d for m,d in BD.B.read_tar(parent['0.tgz'])}
        for n,pin in self.info['layout']['sources'].items():
            self.assertEqual(self.files[n],original[pin['source']])
            self.assertEqual(BD.B.sha(self.files[n]),pin['sha256'])
        # Scan human-readable launch surfaces; packed bytes are separately scanned above.
        # POSIX /dev/null, umask, CUDA_VISIBLE_DEVICES and split() are infrastructure,
        # not project names. Base64/hex transport literals have no exposed name semantics.
        def scan(text):
            text=re.sub(r"(?:base64\.b64decode|bytes\.fromhex)\('[^']*'\)",'',text)
            text=text.replace('/dev/null','/0').replace('CUDA_VISIBLE_DEVICES','A').replace('umask','mode')
            text=text.replace('.split(','.parts(').replace('.splitlines(','.lines(')
            return re.findall(r'(?<![a-z])(?:'+ '|'.join(layout.DENY)+r')(?![a-z])',text.lower())
        scripts=list((HERE/'orchard').glob('o_*.sh'))
        for p in scripts:self.assertEqual(scan(p.read_text()),[],p.name)
        from orchard_h10.common import submit_argv
        argv=submit_argv(self.info['token'],1,'00:50:00')
        self.assertEqual(scan(' '.join(argv)),[])
        from orchard_h10.runner import environment
        env=environment(dict(package='/tmp/a0',output=str(temp()/'0'),device='cpu'),'0',0)
        self.assertEqual(scan(' '.join(k+'='+v for k,v in env.items())),[])
        env={k:v for k,v in os.environ.items() if not k.startswith('SLURM_')}
        failure=subprocess.run([sys.executable,'-I','-s','-B',str(self.package/'a/5.py'),
            '--package',str(self.package),'--sequence',str(self.package/'a/6.py'),'--results',str(temp()/'0')],
            env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(failure.returncode,1)
        self.assertRegex(failure.stdout,r'^E40:[0-9a-f]+\n$');self.assertEqual(failure.stderr,'')
        self.evidence['naming']=dict(passed=True,members=len(self.files),unchanged_source_hashes=len(self.info['layout']['sources']),launch_scripts=len(scripts),deny=list(layout.DENY))

    def test_all_delivery_json_shell_and_input_paths(self):
        import j
        outer={m.name:d for m,d in BD.B.read_tar((HERE/'out/delivery.tgz').read_bytes())}
        def strings(v):
            if isinstance(v,str):yield v
            elif isinstance(v,dict):
                for k,x in v.items():yield k;yield from strings(x)
            elif isinstance(v,list):
                for x in v:yield from strings(x)
        def check(value):
            self.assertFalse(any(w in value.lower() for w in layout.DENY),value[:160])
        count=0
        for group in (outer,self.files):
            for name,data in group.items():
                check(name)
                if name.endswith('.json'):
                    for value in strings(j.wire_loads(data)):check(value);count+=1
                if name.endswith(('.sh','.cmd')):
                    text=data.decode().replace('/dev/null','/0').replace('CUDA_VISIBLE_DEVICES','A').replace('umask','mode')
                    text=text.replace('.split(','.parts(').replace('.splitlines(','.lines(')
                    check(text)
        import base64
        text=(HERE/'orchard/o_place.sh').read_text()
        encoded=re.search(r"build_raw=base64.b64decode\('([^']+)'\)",text).group(1)
        for value in strings(j.wire_loads(base64.b64decode(encoded))):check(value);count+=1
        inputs=j.loads(outer['a/1.json'])
        from external_inputs import REMOVED
        self.assertFalse(set(REMOVED)&inputs['files'].keys())
        self.assertNotIn('sam_source',inputs)
        paths=[f['path'] for f in inputs['files'].values()]
        paths += [p['path'] for a in inputs['archives'] for p in a['parts']]
        paths += [a['destination'] for a in inputs['archives']]
        paths += [inputs['frames_root'],inputs['python'],*inputs['env_roots'],*inputs['policy'].values()]
        for value in paths:check(value)
        # The unchanged binder must resolve every selected PNG under the opaque
        # frame root, even when provenance includes a historic source path.
        from e2e_reader import parity
        mapping=self.info['layout']['paths']
        frames=next(n for n in mapping if n.endswith('/FRAMES.json') and n.startswith('b/'))
        dense=next(n for n in mapping if n.endswith('/DENSE_MANIFEST.json'))
        settings=dict(frames_root=inputs['frames_root'],frames_json=j.loads(self.files[mapping[frames]]),
                      dense_manifest=j.loads(self.files[mapping[dense]]))
        frame_paths=set()
        for row in j.loads(self.files['g/0.json'])['items']:
            bound=parity.bind_item(row['task'],settings,verify=False)
            for path in bound['frames']['native_frames']:check(path);frame_paths.add(path)
        self.assertGreater(len(frame_paths),1000)
        self.evidence['all_surfaces']=dict(passed=True,json_strings=count,input_paths=len(paths),rgb_paths=len(frame_paths),removed=list(REMOVED))

    def test_external_archive_omits_unused_members_and_authenticates(self):
        from orchard_h10 import job
        import j
        S=job.template()[0];root=temp();data=io.BytesIO()
        files={'g/model.safetensors':b'needed','g/config.json':b'{"model":"g3t","depth":true}',
               'k/sam3.pt':b'forbidden','k/SAM3_RECEIPT.json':b'forbidden',
               's/sam3/a.py':b'forbidden','h/selector_head.json':b'forbidden','unused/0':b'forbidden'}
        with tarfile.open(fileobj=data,mode='w') as t:
            for name,raw in files.items():
                m=tarfile.TarInfo(name);m.size=len(raw);t.addfile(m,io.BytesIO(raw))
        data=data.getvalue();source=root/'0';source.write_bytes(data)
        pin=dict(bytes=len(data),sha256=BD.B.sha(data),path=str(source))
        with patch.object(S,'room'):
            S.copy_parts([pin],root/'1',lambda p:Path(p['path']).open('rb'),expected_sha=pin['sha256'])
        inputs=j.loads((self.package/'a/1.json').read_bytes());opened=[]
        actual=io.open
        def guarded(path,*a,**kw):
            opened.append(str(path))
            self.assertFalse(any(x in str(path) for x in ('/k/','/s/','/h/','/unused/')))
            return actual(path,*a,**kw)
        with patch.object(io,'open',side_effect=guarded):
            result=S.extract_stream(io.BytesIO(data),root/'2',None,1000,links=True,retain_roots=inputs['retain_roots'])
        self.assertEqual(set(result),{'g/model.safetensors','g/config.json'})
        for name in ('k','s','h','unused'):self.assertFalse((root/'2'/name).exists())
        self.assertEqual(result['g/model.safetensors']['sha256'],BD.B.sha(b'needed'))
        self.assertEqual(j.raw((root/'2/g/config.json').read_bytes()),files['g/config.json'])
        self.assertEqual(result['g/config.json']['sha256'],BD.B.sha(files['g/config.json']))
        self.assertEqual(set(j.wire_loads((root/'2/g/config.json').read_bytes())),{'a0'})
        with patch.object(S,'room'),self.assertRaises(ValueError):
            S.copy_parts([dict(pin,sha256='0'*64)],root/'3',lambda p:Path(p['path']).open('rb'))
        self.evidence['external_extraction']=dict(passed=True,retained=list(result),unused_opens=0,corrupt_sha_rejected=True)

    def test_worker_factory_and_capture_never_open_unused_inputs(self):
        import torch
        import numpy as np
        from e2e_reader import parity,real,artifact
        from student_pilot import carrier_c1_decode,ground_context,sam3_tower
        from g import w
        root=temp();model=torch.nn.Linear(1,1,bias=False)
        wrapper=types.SimpleNamespace(model=types.SimpleNamespace(language_model=model))
        processor=types.SimpleNamespace(tokenizer=types.SimpleNamespace(convert_tokens_to_ids=lambda x:1),_routing_tokens={'ids':{}})
        artifact_stub=types.SimpleNamespace(verify=lambda:artifact_stub)
        settings=dict(tree=str(self.payload/'tree'),arm='own_depth',frames_json={'captures':{}},dense_manifest={'captures':{}},
                      frames_root=str(root/'f'),perception_memo='off',perception_memo_modules=['g3t'],perception_memo_verify_ids=[])
        opens=[];original=io.open
        def guarded(path,*args,**kwargs):
            if isinstance(path,(str,os.PathLike)):
                name=str(path);opens.append(name)
                self.assertFalse(any(x in name for x in ('sam3.pt','SAM3_RECEIPT','selector_head.safetensors','selector_head.json','/d/s/')),name)
            return original(path,*args,**kwargs)
        with patch.object(io,'open',side_effect=guarded),patch.object(builtins,'open',side_effect=guarded),\
             patch.object(parity,'Artifact',return_value=artifact_stub),\
             patch.object(parity,'load_native',return_value=(wrapper,processor,dict(config={},export=dict(frame_layout='duplicate')))),\
             patch.object(parity,'install_hook',return_value=object()),patch.object(parity,'CallHook'),\
             patch.object(parity,'_head',side_effect=AssertionError('unused head')),\
             patch.object(sam3_tower,'Sam3Tower',side_effect=AssertionError('unused model')):
            factory=parity.make_real('/0',dict(root='/0',name='0.json',sha256='0'*64),[],device='cpu',settings=settings)
            gen=factory.generator;self.assertIsNone(gen.perception.socket)
            state=types.SimpleNamespace(heads=types.SimpleNamespace(gravity=np.array([0.,-1.,0.])))
            def prepare(*a,**kw):model(torch.ones((1,1)));return state
            raw=np.zeros((32,9));raw[:,6]=1;raw[:,7:]=1.2
            result=dict(raw_pose9=raw,anchor_slots=np.arange(32),frame_indices=np.arange(32),
                        depth_grid=np.full((32,51,51),2.),grid_uv=np.linspace(0,1000,51),source_hw=(480,640))
            from e2e_reader.generate import Perception
            gen.perception=Perception(lambda f:result,real.own_gravity,lambda t:torch.tensor(np.log(2.)),socket=None)
            gen.prompt_batch=lambda *a:{}
            frames=dict(anchor_indices=list(range(32)),dense_indices=list(range(32)),anchor_slots=list(range(32)),
                        native_frames=[types.SimpleNamespace(height=480,width=640)]*32)
            ref=dict(item_id='0',capture='0',source_indices=list(range(32)),mapping=dict(dense_count=32,frame_binding_sha256='0'*64))
            @contextlib.contextmanager
            def audit(*a):yield types.SimpleNamespace(entries=0)
            with patch.object(carrier_c1_decode,'_prepare_decode',prepare),patch.object(ground_context,'closed_adapters',side_effect=lambda f:f),patch.object(artifact,'Audit',audit):
                row=w.capture_one(gen,dict(frames=frames,row={}),ref)
        self.assertEqual((row['prefills'],row['decode_steps']),(1,0))
        self.evidence['unused_worker_inputs']=dict(passed=True,unused_opens=0,observed_opens=len(opens),prefills=1,decode_steps=0,weights='CPU doubles')

    def test_preparation_uses_only_retained_inputs(self):
        import j
        from orchard_h10 import prepare,export_pins
        from parity_kit import stage_restore,build_manifest
        from copy import deepcopy
        inputs=deepcopy(j.loads((self.package/'a/1.json').read_bytes()))
        original=j.loads(self.files['9.json'])['logical'];logical=str(self.root)
        inputs['_export']=export_pins.load(inputs,self.package)
        for f in inputs['files'].values():f['path']=f['path'].replace(original,logical)
        d=self.root/'d';d.mkdir(exist_ok=True)
        import importlib
        modules={name:types.ModuleType(name) for name in ('torchvision','transformers','scipy')}
        for m in modules.values():m.__version__='5.12.0'
        # Preparation now imports the real vendor gate before checking versions.
        # Keep torch real; only the unused environment-version probes are doubles.
        modules['torch']=importlib.import_module('torch')
        env=Path(inputs['files']['env']['path']);env.parent.mkdir(parents=True,exist_ok=True)
        env.write_text(j.wire_dumps(dict(versions={name:m.__version__ for name,m in modules.items()})))
        cfg=j.loads(self.files['9.json']);cfg['logical']=logical
        captured={}
        def restored(*a,**kw):captured['restore']=kw
        def manifest(*a,**kw):
            captured['manifest']=kw
            self.assertNotIn('sam3',kw);self.assertNotIn('selector_head',kw)
            return dict(schema='e2e-artifact-v1',components={},code=[])
        def digest(path):
            if str(path).endswith('/RESTORE.json'):return '0'*64
            return BD.B.sha(prepare.Path(path).read_bytes())
        with patch.dict(sys.modules,modules),patch.object(stage_restore,'stage',side_effect=restored),\
             patch.object(build_manifest,'build',side_effect=manifest),patch.object(prepare,'sha',side_effect=digest):
            prepare.run(cfg,inputs)
        settings=j.loads((d/'settings.json').read_bytes())
        self.assertFalse(any(k in settings for k in ('sam3','selector_head','scale_head')))
        self.assertNotIn('sam3_source',captured['manifest']['code_roots'])
        for spec in inputs['_export']['preparation'].values():
            raw=prepare.Path(d/spec['path']).read_bytes()
            self.assertEqual(BD.B.sha(raw),spec['sha256']);self.assertEqual(len(raw),spec['bytes'])
        for p in d.rglob('*.json'):
            if p==env:continue
            raw=j.wire_loads(p.read_bytes())
            self.assertFalse(any(w in j.wire_dumps(raw).lower() for w in layout.DENY),str(p))
        self.evidence['preparation_inputs']=dict(passed=True,unused_settings_absent=True,preparation_pins_verified=3)

    def test_opaque_capture_roundtrip_and_json_resource_hashes(self):
        import j,gzip
        import numpy as np
        from g.d import Writer,encode,decode
        path=temp()/'0.gz'
        geometry=types.SimpleNamespace(depth_grid=np.full((32,51,51),2.125),grid_uv=np.linspace(0,1000,51))
        value=encode(geometry,dict(capture='scannet/0',tower_scale=1.))
        writer=Writer(path);writer.append(value);writer.close()
        with gzip.open(path,'rt') as stream:raw=stream.read()
        self.assertEqual(set(j.wire_loads(raw)),{'a0'})
        logical=j.loads(raw);self.assertEqual(logical,value)
        self.assertTrue(np.array_equal(decode(logical)[0],geometry.depth_grid))
        for name,data in self.files.items():
            if name.endswith('.json'):
                source=self.loader.Path(self.payload/name)
                self.assertEqual(source.read_bytes(),j.raw(data))
                self.assertEqual(source.stat().st_size,len(j.raw(data)))
        self.evidence['opaque_json']=dict(passed=True,capture_roundtrip=True,resource_bytes_exact=True)

    def test_delivery_identity_matches_handoff(self):
        import j,base64
        raw=(HERE/'out/delivery.tgz').read_bytes();info=self.info
        self.assertEqual(len(raw),info['delivery_bytes'])
        self.assertEqual(BD.B.sha(raw),info['delivery_sha256'])
        for name in ('PLACE.md','REPORT.md'):
            text=(HERE/name).read_text()
            self.assertIn(info['token'],text)
            self.assertIn(info['delivery_sha256'],text)
            self.assertIn(f"{len(raw):,}",text)
            self.assertNotIn('a09fdd101cc93',text);self.assertNotIn('ab6ea69ea972b',text)
        for name in ('0.json','CONFIG.json','PACKAGE.json'):
            self.assertEqual(j.loads((self.package/name).read_bytes())['token'],info['token'])
        self.assertEqual(j.loads(self.files['9.json'])['token'],info['token'])
        script=(HERE/'orchard/o_place.sh').read_text()
        placed=j.loads(base64.b64decode(re.search(r"build_raw=base64.b64decode\('([^']+)'\)",script)[1]))
        for key in ('token','delivery_bytes','delivery_sha256'):self.assertEqual(placed[key],info[key])
        self.evidence['identity']=dict(passed=True,**{k:info[k] for k in ('token','delivery_bytes','delivery_sha256')})

    def test_dynamic_resource_and_factory_imports(self):
        from parity_kit.common import policy,LANE,module
        import importlib
        for name in ('student_pilot.carrier_c1_run','student_pilot.tower_read','student_pilot.sam3_tower','evalpath.runtime'):
            m=importlib.import_module(name)
            self.assertTrue(Path(m.__file__).is_relative_to(self.payload))
        self.assertTrue(hasattr(policy(),'ThinkingBudget'))
        m=module(LANE/'heads/selector/selector_head.py','_test_selected')
        self.assertTrue(hasattr(m,'SelectorHead'))
        from student_pilot import tower_scale
        p=tower_scale.Path(tower_scale.__file__).with_name('tower_scale_rule.json')
        self.assertEqual(BD.B.sha(p.read_bytes()),tower_scale.RULE_SHA256)
        self.evidence['dynamic_imports']=dict(passed=True)

    def test_factory_accepts_unlabelled_tasks(self):
        from e2e_reader import parity
        from h1eval.h10.parity_adapter import make_capped_real
        items=[r['task'] for r in json.loads(self.files['g/0.json'])['items']]
        paths=self.info['layout']['paths']
        frames=next(n for n in paths if n.endswith('/FRAMES.json') and n.startswith('b/'))
        dense=next(n for n in paths if n.endswith('/DENSE_MANIFEST.json'))
        settings=dict(tree=str(self.payload/'tree'),arm='own_depth',frames_json=json.loads(self.files[paths[frames]]),
                      dense_manifest=json.loads(self.files[paths[dense]]),frames_root='/tmp/0')
        artifact=types.SimpleNamespace(verify=lambda:None)
        artifact.verify=lambda:artifact
        processor=types.SimpleNamespace(tokenizer=types.SimpleNamespace(convert_tokens_to_ids=lambda x:1),_routing_tokens={'ids':{}})
        info=dict(config={},export=dict(frame_layout='duplicate'))
        with patch.object(parity,'Artifact',return_value=artifact),patch.object(parity,'load_native',return_value=(object(),processor,info)),patch.object(parity,'install_hook',return_value=object()),patch.object(parity,'CallHook'):
            factory=make_capped_real('/tmp/0',dict(root='/tmp/0',name='0.json',sha256='0'*64),items,
                                    perception_factory=lambda **kw:None,device='cpu',settings=settings)
        self.assertEqual(factory.load_info,info)
        self.assertEqual(factory.generator.frames['count'],32)
        self.evidence['unlabelled_factory']=dict(passed=True,tasks=len(items),weight_loads='stubbed')

    def test_slow_upload_keeps_failure_receipt_window(self):
        from orchard_h10 import job,budget
        root=temp();out=root/'r';(out/'metadata').mkdir(parents=True)
        path=root/'sj/b0/c/0.gz';path.parent.mkdir(parents=True);path.write_bytes(b'0')
        cfg=dict(logical='/scratch/jjyeung/b0',pool='/tmp/a0',plan_sha256='0'*64)
        now=[2760.];calls=[]
        def slow(argv,**kw):
            calls.append(dict(argv=argv,timeout=kw['timeout'],start=now[0]))
            now[0]+=kw['timeout']
            raise subprocess.TimeoutExpired(argv,kw['timeout'])
        _,_,results,pool_io,_=job.template()
        cfg['pool']=str(root/'q');(root/'q'/('a'+'0'*20)).mkdir(parents=True)
        def pool(action,*a,**kw):
            calls.append(dict(action=action,timeout=kw['timeout'],start=now[0]))
            now[0]+=kw['timeout']
            if action=='publish':raise TimeoutError('0')
            return pool_io.operate(action,*a)
        with patch.dict(os.environ,dict(PATH='/usr/bin:/bin',HOME='/tmp/a0',USER='0'),clear=True),patch.object(subprocess,'run',side_effect=slow),patch.object(results,'pool_operation',side_effect=pool),patch.object(results,'GCS_ROOT','gs://a0'),patch.object(results,'CLOUD_CONFIG','/tmp/a0'):
            budget.finish(root,cfg,out,'a'+'0'*20,results,3000,job.upload_capture,job.write,False,clock=lambda:now[0])
        self.assertEqual([c['timeout'] for c in calls],[150,80,8])
        self.assertLess(now[0],3000)
        copied=json.loads((root/'q'/('a'+'0'*20)/'RETURN_RECEIPT.json').read_text())
        self.assertEqual(copied['error'],'E35')
        self.assertEqual(json.loads((out/'RETURN_RECEIPT.json').read_text())['error'],'E35')
        self.evidence['slow_upload']=dict(passed=True,deadline=3000,finished_at=now[0],calls=calls)

    def test_upload_describe_readback_share_deadline(self):
        from orchard_h10 import job,budget
        root=temp();out=root/'r';(out/'metadata').mkdir(parents=True)
        path=root/'sj/b0/c/0.gz';path.parent.mkdir(parents=True);path.write_bytes(b'0')
        cfg=dict(logical='/scratch/jjyeung/b0')
        now=[2760.];calls=[]
        def transfer(argv,**kw):
            calls.append(dict(action=argv[2],timeout=kw['timeout'],start=now[0]))
            if argv[2]=='cp':now[0]+=100;return types.SimpleNamespace(returncode=0)
            if argv[2]=='objects':
                now[0]+=40;return types.SimpleNamespace(stdout=json.dumps(dict(generation='1',size=1)))
            now[0]+=kw['timeout'];raise subprocess.TimeoutExpired(argv,kw['timeout'])
        results=types.SimpleNamespace(GCS_ROOT='gs://a0',CLOUD_CONFIG='/tmp/a0')
        with patch.dict(os.environ,dict(PATH='/usr/bin:/bin',HOME='/tmp/a0',USER='0'),clear=True),patch.object(subprocess,'run',side_effect=transfer):
            with budget.window(2910,clock=lambda:now[0]):
                result=job.upload_capture(root,cfg,out,'a'+'0'*20,results)
        self.assertEqual([c['timeout'] for c in calls],[150,50,10])
        self.assertFalse(result['verified']);self.assertEqual(now[0],2910)
        self.evidence['transfer_deadlines']=dict(passed=True,calls=calls)

    def test_worker_deadline_reaps_before_publication(self):
        op=runpy.run_path(str(self.package/'a/6.py'));root=temp();(root/'metadata').mkdir();marker=root/'metadata/STOP'
        evidence=[]
        for started in (0,600,1200):
            root=temp();(root/'metadata').mkdir();marker=root/'metadata/STOP'
            now=[float(started)];waits=[]
            class Process:
                pid=123
                def wait(self,timeout):
                    waits.append(timeout);now[0]+=timeout
                    if len(waits)<3:raise subprocess.TimeoutExpired('0',timeout)
                    return -9
            cfg=dict(stop_file=str(marker),prefix=[],output=str(root))
            with patch.dict(op['run'].__globals__,prepare=lambda c:{0:cfg},commands=lambda *a:['0']),patch('orchard_h10.runner.environment',return_value={}),patch('orchard_h10.common.opaque'),patch.object(os,'killpg') as signals:
                result=op['run'](dict(output=str(root)),3000,['0'],launcher=lambda *a,**k:Process(),clock=lambda:now[0])
            self.assertEqual(waits,[min(1800,2730-started),20,5]);self.assertEqual(signals.call_count,2)
            self.assertLessEqual(now[0],2760);self.assertFalse(result['complete'])
            evidence.append(dict(start=started,waits=waits,reaped_at=now[0],allocation_end=3000))
        self.evidence['worker_deadline']=dict(passed=True,cases=evidence)

    def test_fifty_minute_admission_and_absolute_windows(self):
        from orchard_h10 import budget
        from orchard_h10.common import submit_argv
        argv=submit_argv(self.info['token'],1,'00:50:00')
        self.assertIn('--time=00:50:00',argv)
        for value in ('00:40:00','00:49:59'):
            with self.assertRaises(ValueError):submit_argv(self.info['token'],1,value)
        self.assertEqual(json.loads(self.files['9.json'])['budget_gpu_seconds'],3000)
        for name in ('3.py','SUBMIT.cmd'):
            text=(self.package/name).read_text();self.assertIn('00:50:00',text);self.assertNotIn('00:40:00',text)
        for name in ('o_cpu.sh','o_check_sub.sh','o_sub_hand.sh'):
            text=(HERE/'orchard'/name).read_text();self.assertIn('00:50:00',text);self.assertNotIn('00:40:00',text)
        forecast=self.info['forecast']
        self.assertEqual(forecast['deadline_offsets_s'],dict(worker_latest_stop=2730,staging_stop=2760,capture_publication_stop=2910,normal_publication_stop=2990,failure_receipt_stop=2998))
        self.assertEqual((budget.WORK_RESERVE,budget.RECEIPT_RESERVE,budget.FINAL_RESERVE),(240,90,10))
        self.assertGreater(forecast['allocation_margin_s'],734)
        self.assertGreater(forecast['worker_margin_s'],374)
        self.evidence['allocation']=dict(passed=True,seconds=3000,worker_cap=1800,windows=forecast['deadline_offsets_s'])



if __name__=='__main__':unittest.main(verbosity=2)
