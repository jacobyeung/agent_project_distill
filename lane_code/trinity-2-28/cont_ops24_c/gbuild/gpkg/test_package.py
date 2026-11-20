import ast
import copy
import gzip
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import tarfile
import types
import unittest
from unittest.mock import patch
import numpy as np
import build

ROOT=build.ROOT
sys.path.insert(0,str(ROOT))
from gpkg.runtime import p as parity, c as capture, w as worker, q as points


def temp():
    return Path(tempfile.mkdtemp(prefix='a',dir=ROOT/'work/tests'))


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def definitions(path,names,ns):
    tree=ast.parse(Path(path).read_text()); nodes=[n for n in tree.body if getattr(n,'name',None) in names]
    for n in nodes:
        if isinstance(n,(ast.FunctionDef,ast.ClassDef)):n.decorator_list=[]
    exec(compile(ast.fix_missing_locations(ast.Module(nodes,type_ignores=[])),str(path),'exec'),ns)


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=temp();cls.info=build.build(cls.root/'out')
        cls.raw=(cls.root/'out/delivery.tgz').read_bytes()
        cls.package=cls.root/'pkg';build.extract(cls.raw,cls.package)
        cls.payload=cls.root/'pay';build.extract((cls.package/'0.tgz').read_bytes(),cls.payload)
        cls.pf={m.name:d for m,d in build.read_tar((cls.package/'0.tgz').read_bytes())}
        cls.original={m.name:d for m,d in build.read_tar((ROOT/'parent/0.tgz').read_bytes())}
        cls.refs=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']

    def test_deterministic_and_no_overlay(self):
        out=temp();info=build.build(out)
        self.assertEqual(info,self.info);self.assertEqual((out/'delivery.tgz').read_bytes(),self.raw)
        base=temp();build.build(base,overlay=False)
        for m,d in build.read_tar((base/'delivery.tgz').read_bytes()):
            self.assertEqual(d,(ROOT/'parent'/m.name).read_bytes(),m.name)

    def test_seals_and_parent_helpers(self):
        nf={m.name:d for m,d in build.read_tar(self.raw)}
        pub=json.loads(nf['0.json']);plan=json.loads(self.pf['9.json'])
        self.assertRegex(pub['token'],r'^[a-f][0-9a-f]{12}$')
        self.assertEqual(json.loads(nf['CONFIG.json']),pub)
        self.assertEqual(build.canonical(plan),pub['plan_sha256'])
        for n,h in json.loads(nf['PACKAGE.json'])['files'].items():self.assertEqual(build.sha(nf[n]),h,n)
        for n,pin in plan['payload_pins'].items():self.assertEqual(pin,dict(bytes=len(self.pf[n]),sha256=build.sha(self.pf[n])),n)
        old=json.loads(self.original['9.json'])
        self.assertEqual({k:v for k,v in plan.items() if k not in ('token','payload_pins')},
                         {k:v for k,v in old.items() if k not in ('token','payload_pins')})
        for n,d in self.original.items():
            if n not in self.info['changed_payload']:self.assertEqual(d,self.pf[n],n)
        for n in ('a/1.json','a/export.json','a/5.py'):self.assertEqual(nf[n],(ROOT/'parent'/n).read_bytes())
        # Invoke the parent's untouched 8.py helpers against the actual derived files.
        ns={'__name__':'checked','__file__':str(self.package/'3.py')}
        exec(compile(self.original['8.py'],'8.py','exec'),ns)
        with patch.dict(sys.modules):
            cfg=ns['load_helpers'](self.package)
            from orchard_h10.job import check_inputs
            got=check_inputs(json.loads(nf['a/1.json']),cfg,package=self.package)
            self.assertEqual(got,json.loads(nf['a/1.json']))
            from orchard_h10.common import submit_argv,opaque
            argv=submit_argv(pub['token'],1,'05:00:00')
            self.assertIn('--gres=gpu:1',argv);self.assertIn('--cpus-per-task=16',argv);opaque(argv)
        # The baseline predates serving_pins: preserve every serving/evaluator byte instead.
        for prefix in ('b/','tree/','h1eval/','items/'):
            self.assertEqual([(n,build.sha(d)) for n,d in self.original.items() if n.startswith(prefix)],
                             [(n,build.sha(d)) for n,d in self.pf.items() if n.startswith(prefix)])

    def test_batch_and_compile(self):
        files={m.name:d for m,d in build.read_tar(self.raw)}
        bundle={m.name:d for m,d in build.read_tar(build.bundle_of(files['BATCH.sh'])[1])}
        old={m.name:d for m,d in build.read_tar(build.bundle_of((ROOT/'parent/BATCH.sh').read_bytes())[1])}
        self.assertEqual(set(bundle),{'0.py','0.json','7.py'})
        self.assertEqual(bundle['0.py'],old['0.py']);self.assertEqual(bundle['7.py'],files['a/6.py'])
        self.assertEqual(bundle['0.json'],files['0.json'])
        for n in self.info['changed_payload']:
            if n.endswith('.py'):compile(self.pf[n],n,'exec')
        source=self.pf['orchard_h10/job.py'].decode()
        self.assertLess(source.index('upload_capture(root,cfg,out,return_token,R)'),source.index('returned=R.publish'))

    def test_baseline_calls_and_settings(self):
        with tarfile.open(ROOT/'parent/a/f/0.tgz') as t:
            baseline=[json.loads(x) for x in t.extractfile('metadata/reads/1/metadata/journals/3/0/items.jsonl')]
            settings=json.load(t.extractfile('metadata/reads/1/metadata/0.json'))
        self.assertEqual([r['id'] for r in baseline],[r['item_id'] for r in self.refs])
        for old,ref in zip(baseline,self.refs):
            calls=[{k:c.get(k) for k in ('call','response','served')} for c in old['output']['calls']['records'] if c['family'] in ('ground','gap')]
            self.assertEqual(calls,ref['calls'])
        op=module('dispatch',self.package/'a/6.py')
        spec=op.descriptors(self.payload)[0]
        for k in ('stage1_select_rule','save_own_depth','perception_memo','perception_memo_modules','perception_memo_verify_ids'):
            self.assertEqual(spec[k],settings[k])

    def runtime_modules(self):
        common=module('orchard_h10.common',self.payload/'orchard_h10/common.py')
        pkg=types.ModuleType('orchard_h10');pkg.__path__=[str(self.payload/'orchard_h10')]
        return {'orchard_h10':pkg,'orchard_h10.common':common}

    def test_operator_rehearsal_and_dispatch(self):
        mods=self.runtime_modules()
        reader=types.ModuleType('e2e_reader');reader.__path__=[];mods['e2e_reader']=reader
        torch=types.ModuleType('torch');torch.tensor=np.array;torch.zeros=lambda *x:np.zeros(x);torch.argmax=np.argmax
        mods['torch']=torch
        with patch.dict(sys.modules,mods):
            memo=module('e2e_reader.perception_memo',self.payload/'b/e2e_reader/perception_memo.py')
            sys.modules[memo.__name__]=memo
            s=types.ModuleType('e2e_reader.stage1');s.__package__='e2e_reader';s.np=np;s.torch=torch
            tree=ast.parse((self.payload/'b/e2e_reader/stage1.py').read_text())
            cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='StageOne')
            cls.body=[x for x in cls.body if getattr(x,'name',None) in ('select','propose')]
            for x in cls.body:x.decorator_list=[]
            exec(compile(ast.fix_missing_locations(ast.Module([cls],type_ignores=[])),'stage1.py','exec'),s.__dict__)
            s.OwnDepthScale=lambda:None;s.ScaleHeadCall=lambda x:None
            definitions(self.payload/'b/e2e_reader/stage1.py',{'stage1_factory'},s.__dict__)
            sys.modules[s.__name__]=s;reader.stage1=s
            geometry=types.ModuleType('e2e_reader.geometry');geometry.frame_count=lambda x:32
            grounding=types.ModuleType('e2e_reader.grounding');grounding.StageOneSocket=lambda *x:x
            sys.modules[geometry.__name__]=geometry;sys.modules[grounding.__name__]=grounding
            real=types.ModuleType('e2e_reader.real');real.__package__='e2e_reader';real.TowerG3T=lambda *x,**y:None
            real.Perception=lambda *x:types.SimpleNamespace(socket=x[3]);real.own_gravity=lambda:None;real.anchor_frames=lambda:None
            definitions(self.payload/'b/e2e_reader/real.py',{'real_perception'},real.__dict__)
            sys.modules[real.__name__]=real;reader.real=real
            g=types.ModuleType('g');g.__path__=[str(self.payload/'g')];sys.modules['g']=g
            # This rehearsal uses module doubles; real import provenance is
            # exercised separately against the extracted delivery.
            gw=module('g.w',self.payload/'g/w.py');gw.bind_reader_root=lambda root:root
            sys.modules['g.w']=gw
            op=module('dispatch',self.package/'a/6.py')
            root=temp();settings=root/'0.json'
            original=dict(arm='own_depth',stage1_select_rule='null_argmax',save_own_depth=False,
                          perception_memo='off',perception_memo_modules=['g3t'],perception_memo_verify_ids=[])
            settings.write_text(json.dumps(original))
            cfg=dict(package=str(self.payload),output=str(root/'r'),settings=str(settings),python=sys.executable,
                     plan_sha256=self.info['plan_sha256'],inputs_sha256='a'*64,operator_sha256='b'*64,
                     export_pin='0.json',export='e',binding='b',device='cpu',prefix=[])
            result=op.rehearsal(cfg);self.assertEqual(len(result),1);self.assertEqual(result[0]['expected'],150)
            parent=runpy.run_path(str(ROOT/'parent/a/6.py'))
            self.assertEqual(op.descriptors(self.payload),[parent['descriptors'](self.payload)[1]])
            self.assertEqual(op.memory_probe(cfg),op.memory_bound())
            self.assertTrue(op.memory_bound()['fits'])
            bootstrap={m.name:d for m,d in build.read_tar(build.bundle_of((self.package/'BATCH.sh').read_bytes())[1])}
            dispatch={};exec(compile(bootstrap['0.py'],'0.py','exec'),dispatch)
            (root/'a').mkdir();(root/'a/1.json').write_text(json.dumps(dict(action=1,config={})))
            (root/'7.py').write_bytes((self.package/'a/6.py').read_bytes());calls=[]
            hook=dispatch['make_dispatch'](root,lambda argv,**kw:calls.append(argv),build.sha((root/'7.py').read_bytes()))
            hook(['python',str(root/'a/5.py'),str(root/'a/1.json')])
            self.assertEqual(calls[0][-2:], [str(root/'7.py'),str(root/'a/1.json')])
            # STOP avoids starting a worker and still writes an incomplete summary.
            (root/'r/metadata/STOP').write_text('1')
            summary=op.run(cfg,20000,['0'],launcher=lambda *x,**y:self.fail('launched despite STOP'),clock=lambda:0)
            self.assertFalse(summary['complete']);self.assertEqual(summary['completed'],0)
            fresh=temp();cfg2=dict(cfg,output=str(fresh/'r'),prefix=['bash','9.sh'])
            launched=[]
            def launch(argv,**kwargs):
                launched.append((argv,kwargs))
                def wait(timeout):
                    self.assertGreater(timeout,0)
                    mods['orchard_h10.common'].write(fresh/'r/metadata/6.json',dict(
                        completed=150,expected=150,repeat_completed=10,repeat_expected=10,complete=True,failure=None))
                    return 0
                return types.SimpleNamespace(wait=wait)
            summary=op.run(cfg2,20000,['7'],launcher=launch,clock=lambda:0)
            self.assertTrue(summary['complete']);self.assertEqual(launched[0][0][:2],['bash','9.sh'])
            self.assertEqual(launched[0][1]['env']['CUDA_VISIBLE_DEVICES'],'7')
            self.assertTrue(launched[0][1]['start_new_session'])

    def test_upload_and_finally(self):
        mods=self.runtime_modules()
        with patch.dict(sys.modules,mods):
            job=module('orchard_h10.job',self.payload/'orchard_h10/job.py')
            cfg=dict(json.loads(self.pf['9.json']),**json.loads((self.package/'0.json').read_text()))
            for fail in (False,True,'corrupt','metadata'):
                root=temp();(root/'0.json').write_text(json.dumps({'token':cfg['token']}))
                out=root/'sj'/Path(cfg['logical']).relative_to('/scratch/jjyeung')/'r'
                path=out.parent/'c/0.gz';path.parent.mkdir(parents=True);path.write_bytes(b'partial fixture')
                published=[];calls=[]
                R=types.SimpleNamespace(GCS_ROOT='gs://x/a',CLOUD_CONFIG='/project/community/jjyeung/gcloud',
                    write_test=lambda *a:None,publish=lambda *a:published.append(a) or {'returned':True})
                J=types.SimpleNamespace(physical=lambda root,p:root/'sj'/Path(p).relative_to('/scratch/jjyeung'),storage_proof=lambda *a,**kw:{})
                def fake(argv,**kw):
                    calls.append((argv,kw))
                    self.assertEqual(kw['env']['CLOUDSDK_CONFIG'],R.CLOUD_CONFIG)
                    if fail is True:raise ValueError('fake upload failure')
                    if argv[2]=='cp':return types.SimpleNamespace(returncode=0)
                    if argv[2]=='objects':return types.SimpleNamespace(stdout=json.dumps({'generation':'invalid' if fail=='metadata' else '9','size':path.stat().st_size}))
                    if argv[2]=='cat':kw['stdout'].write(b'corrupt' if fail=='corrupt' else path.read_bytes());return types.SimpleNamespace(returncode=0)
                    self.fail(argv)
                with patch.object(job,'template',return_value=(None,J,R,None,None)),patch.object(job,'read_config',return_value=cfg),\
                     patch.object(mods['orchard_h10.common'],'install_process_guard'),patch.object(job,'sha',side_effect=ValueError('stop before remote reads')),\
                     patch.object(job.subprocess,'run',side_effect=fake),patch.dict(os.environ,{'SLURM_JOB_ID':'100','A_N':'1','A_T':'18000','PATH':'/usr/bin'},clear=True):
                    with self.assertRaises(SystemExit):job.main(root)
                self.assertEqual(len(published),1)
                rec=json.loads((out/'metadata/CAPTURE.json').read_text())
                self.assertEqual(rec['verified'],not fail);self.assertEqual(rec['bytes'],len(b'partial fixture'))
                self.assertEqual(rec['uri'],'gs://x/a/'+cfg['token']+'00000064c/0.gz')
                self.assertFalse((out/'0.gz').exists())
                if not fail:self.assertEqual(calls[-1][0][-1],rec['uri']+'#9')

    def test_parity_rules(self):
        main={r['item_id']:copy.deepcopy(r['calls']) for r in self.refs}
        selected=[r for r in self.refs if r['calls']][:10]
        repeat={r['item_id']:copy.deepcopy(r['calls']) for r in selected}
        self.assertTrue(parity.evaluate(self.refs,main,repeat)['trusted'])
        self.assertEqual(parity.evaluate(self.refs,main,repeat)['gap_atol_m'],0)
        # 141 / 150 = 94%, below the registered threshold.
        bad=copy.deepcopy(main)
        for r in [r for r in self.refs if r['calls']][-9:]:bad[r['item_id']][0]['served']=False
        self.assertEqual(parity.evaluate(self.refs,bad,repeat)['discrete_matches'],141)
        self.assertFalse(parity.evaluate(self.refs,bad,repeat)['trusted'])
        bad=copy.deepcopy(main)
        for r in [r for r in self.refs if r['calls']][-7:]:bad[r['item_id']][0]['served']=False
        self.assertTrue(parity.evaluate(self.refs,bad,repeat)['trusted'])
        key=selected[0]['item_id'];index=next(i for i,c in enumerate(main[key]) if c['response'].startswith('distance '))
        value=parity.printed(main[key][index]['response'])['value']
        repeat[key][index]['response']='distance %.2f m'%(value+parity.Decimal('.03'))
        check=parity.evaluate(self.refs,main,repeat);self.assertEqual(check['gap_atol_m'],.06);self.assertTrue(check['trusted'])
        bad=copy.deepcopy(main); other=[r for r in self.refs if r['calls']][-1]['item_id']
        i=next(i for i,c in enumerate(bad[other]) if c['response'].startswith('distance '))
        val=parity.printed(bad[other][i]['response'])['value']
        bad[other][i]['response']='distance %.2f m'%(val+parity.Decimal('.07'))
        self.assertFalse(parity.evaluate(self.refs,bad,repeat)['trusted'])
        self.assertFalse(parity.evaluate(self.refs,main,{})['trusted'])
        repeat={r['item_id']:copy.deepcopy(r['calls']) for r in selected}
        bad=copy.deepcopy(main);bad[other][i]['response']='distance %.2f m'%(val+parity.Decimal('.01'))
        self.assertFalse(parity.evaluate(self.refs,bad,repeat)['trusted'])
        self.assertFalse(parity.compare([{'call':'x','served':True,'response':'none'}],[{'call':'x','served':True,'response':'error'}])[0])

    def test_writer_cap_flush_location_and_points(self):
        r=self.refs[0]
        row=dict(schema='ground-capture-v1',item_id=r['item_id'],source_indices=r['source_indices'],objects=[],geometry=None,calls=[])
        root=temp();p=root/'0.gz';w=capture.Writer(p,cap=256);w.append(row)
        self.assertGreater(p.stat().st_size,0)
        before=p.read_bytes();large=dict(row,extra=''.join(build.sha(str(i).encode()) for i in range(200)))
        with self.assertRaises(RuntimeError):w.append(large)
        self.assertEqual(p.read_bytes(),before);w.close()
        self.assertEqual(json.loads(gzip.decompress(p.read_bytes())),row)
        self.assertLessEqual(p.stat().st_size,256)
        for shape in ((3,4),(480,640)):
            mask=np.indices(shape).sum(0)%2
            np.testing.assert_array_equal(capture.unrle(capture.rle(mask)),mask.astype(bool))
        self.assertEqual(worker.capture_path({'output':str(root/'r')}),root/'c/0.gz')
        with self.assertRaises(ValueError):worker.capture_path({'output':str(root/'r'),'capture':str(root/'r/0.gz')})
        x=root/'2.json';x.write_text('{"item":{"chair":{"0":[0.5,1.0],"1":null}}}')
        with self.assertRaisesRegex(RuntimeError,'_get_dummy_prompt'):points.admit(x)
        with self.assertRaises(ValueError):points.validate({'i':{'x':{'0':[True,0]}}})
        memo=types.SimpleNamespace(modules=frozenset(['g3t']))
        gen=types.SimpleNamespace(perception=types.SimpleNamespace(memo=memo))
        with worker.fresh_perception(gen):self.assertEqual(memo.modules,frozenset())
        self.assertEqual(memo.modules,frozenset(['g3t']))


if __name__=='__main__':unittest.main()
