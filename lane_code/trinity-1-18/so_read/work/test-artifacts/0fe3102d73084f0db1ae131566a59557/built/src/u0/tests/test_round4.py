"""A4 step-600 CPU contract: real preparation, rehearsal, bootstrap and job dispatch."""
import ast
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tarfile
import types
import unittest
import uuid
from unittest.mock import patch

L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
SRC=Path(__file__).resolve().parents[2]
INPUT=Path(os.environ['READ_INPUT_SRC'])
BEFORE=os.environ.get('READ_ROUND4_BEFORE')=='1'
E=L/'work/round4-before-u0' if BEFORE else SRC/'u0'
OP=Path(os.environ.get('READ_OPERATOR4_SOURCE',str(L/'work/operator4')))
sys.path[:0]=[str(SRC),str(SRC/'b'),str(INPUT/'tree'),str(E)]


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,sort_keys=True))


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(path):
    with tarfile.open(path) as tar:
        return {m.name:tar.extractfile(m).read() for m in tar if m.isfile()}


def directory():
    root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True)
    return root


def build_profile(root,processor_only=False):
    base=root/'base'
    for rel in ('package/0.tgz','package/0.json','package/BATCH.sh','package/3.py',
                'package/a/0.json','package/a/4.py','package/a/7.py','fetch_return.py'):
        dest=base/rel;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes((INPUT.parent/rel).read_bytes())
    for rel in ('tower_sequence.py','unpack_return.py','package/a/5.py'):
        path=(L/'out_round4/operator/tower_sequence.py' if rel=='tower_sequence.py' else INPUT.parent/rel) if BEFORE else OP/rel
        if rel=='package/a/5.py' and os.environ.get('READ_NODE4_BEFORE')=='1':path=INPUT.parent/rel
        dest=base/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
    cfg=json.loads(archive(base/'package/0.tgz')['9.json'])
    # A synthetic binding tests the contract; it is not a production export receipt.
    binding=dict(cfg['export_binding'],step=600,member_directory='m600',object='q8/8865619b/673bc60f_m600.tar',archive_bytes=4,archive_sha256='2'*64)
    write(root/'binding.json',binding)
    target=root/'built'
    if BEFORE:
        builder=load('before_builder4',E/'a12.py')
        original=load('original_builder4',INPUT/'orchard_h10/build.py')
        original.B=INPUT/'b';original.T=INPUT/'orchard_h10/vendor'
        source=root/'source'
        for name,path in original.sources().items():
            dest=source/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        for path in E.rglob('*'):
            if path.is_file():
                dest=source/'u0'/path.relative_to(E);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        builder.K=source;builder.B=source/'b';builder.T=source/'orchard_h10/vendor'
        builder.build(source/'package','ab0123456789',enable_extensions=True,caches_only=True,
                      processor_only=processor_only,operator_bootstrap=L/'out_round4/operator/0.py',
                      operator_source=base/'tower_sequence.py')
        for path in (source/'package').iterdir():
            if path.is_file():
                dest=target/'package'/path.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        for rel in ('a/0.json','a/4.py','a/5.py'):
            dest=target/'package'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((base/'package'/rel).read_bytes())
        for rel in ('tower_sequence.py','fetch_return.py','unpack_return.py'):
            (target/rel).write_bytes((base/rel).read_bytes())
        (target/'package/a/6.py').write_bytes((base/'tower_sequence.py').read_bytes())
        for name,raw in archive(target/'package/0.tgz').items():
            dest=target/'src'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        names=('0.tgz','0.json','3.py','BATCH.sh','CONFIG.json','a/0.json','a/4.py','a/5.py','a/6.py')
        write(target/'package/PACKAGE.json',dict(files={n:digest(target/'package'/n) for n in names}))
    else:
        builder=load('a4_builder4',(L/'work/round5-before-u0' if os.environ.get('READ_NODE4_BEFORE')=='1' else E)/'a19.py')
        builder.build(base,SRC,root/'binding.json',target,'ab0123456789',
                      enable_extensions=True,processor_only=processor_only,**({} if os.environ.get('READ_NODE4_BEFORE')=='1' else dict(
                      manifest_path=L/'out/patches/MANIFEST.json',
                      extension_pins_path=L/'out/kit_parity50/EXTENSION_PINS.json')))
    return target,binding


def seed_inputs(target,binding):
    package=target/'package';payload=archive(package/'0.tgz');cfg=json.loads(payload['9.json'])
    inputs=json.loads((package/'a/0.json').read_text())
    inputs['archives'][0]['sha256']=binding['archive_sha256']
    export=dict(schema='h1-export-pins-v1',**{k:binding[k] for k in ('run','step','member_directory','lineage','object','config_sha256')},
                archive_sha256=inputs['archives'][0]['sha256'],preparation={})
    from orchard_h10.export_pins import MEMBERS
    for name,member in MEMBERS.items():
        pin=dict(sha256='1'*64,bytes=1)
        export[name]=pin
        inputs['files'][name]=dict(path=cfg['logical']+'/d/'+binding['member_directory']+'/'+member,**pin)
    for name,h in binding['preparation_sha256'].items():
        export['preparation'][name]=dict(path=name+'.json',source_path='/scratch/jjyeung/ab0123456789/'+name+'.json',sha256=h,bytes=2)
    write(package/'a/export.json',export)
    inputs['export_pin']=dict(path='a/export.json',sha256=digest(package/'a/export.json'),bytes=(package/'a/export.json').stat().st_size)
    inputs['python']=sys.executable
    write(package/'a/1.json',inputs)
    return cfg,inputs,export


def action_child(target,root,cfgpath):
    import torch
    torch.set_num_threads(8)
    original=json.loads(cfgpath.read_text())
    logical=json.loads((target/'src/9.json').read_text())['logical']
    sandbox=root/'sandbox'
    def mapped(value):
        if isinstance(value,str) and (value==logical or value.startswith(logical+'/')):
            return str(sandbox)+value[len(logical):]
        if isinstance(value,dict):return {k:mapped(v) for k,v in value.items()}
        if isinstance(value,list):return [mapped(v) for v in value]
        return value
    cfg=mapped(original)
    # This is the namespace stub: translate paths, never synthesize run keys.
    local=cfgpath.with_name(cfgpath.stem+'-local.json');write(local,cfg)
    p=sandbox/'p';sys.path[:0]=[str(p),str(p/'b'),str(p/'tree'),str(p/'u0')]
    from orchard_h10 import common,runner
    with ExitStack() as stack:
        stack.enter_context(patch.object(common,'install_process_guard'))
        if cfg['action']==0:
            import transformers,scipy
            tv=types.ModuleType('torchvision');tv.__version__='cpu-stub'
            stack.enter_context(patch.dict(sys.modules,{'torchvision':tv}))
            from parity_kit import stage_restore,build_manifest
            receipt={'versions':{m.__name__:m.__version__ for m in (torch,tv,transformers,scipy)}}
            write(Path(cfg['inputs']['files'][cfg['inputs']['environment_receipt']]['path']),receipt)
            def stage(*args,**kwargs):
                out=Path(args[3]);out.mkdir(parents=True,exist_ok=True);write(out/'RESTORE.json',{})
            stack.enter_context(patch.object(stage_restore,'stage',side_effect=stage))
            stack.enter_context(patch.object(build_manifest,'build',return_value={'fixture':True}))
            stack.enter_context(patch.object(sys,'argv',[str(root/'a/5.py'),str(local)]))
            runpy.run_path(str(root/'a/5.py'),run_name='__main__')
        else:
            operator=load('operator4_action',root/'7.py')
            if not cfg.get('rehearsal'):
                actual_run=runner.run
                def execute(config,cards,end,**kwargs):
                    from h1eval.h10 import launch
                    assert Path(launch.__file__).read_bytes()==(p/'u0/a4.py').read_bytes()
                    fixtures=load('operator4_fixture',p/'u0/tests/test_read_journal.py')
                    case=fixtures.RunnerTests();case.setUp()
                    case.manifest=json.loads((p/'items/devs1_routed.json').read_text())
                    for patcher in case.patches:patcher.stop()
                    case.patches=[patch.object(fixtures.launch,'load_manifest',return_value=case.manifest),
                        patch.object(fixtures.item_module,'read_contract'),patch.object(fixtures.launch,'sha',return_value='0'*64),
                        patch.object(fixtures.launch,'code_hash',return_value='1'*64),patch.object(fixtures.launch,'export_hash',return_value='2'*64)]
                    for patcher in case.patches:patcher.start()
                    from e2e_reader import read_cache
                    class Qwen3_5VisionModel(torch.nn.Module):
                        def __init__(self):
                            super().__init__();self.weight=torch.nn.Parameter(torch.ones(2,2),requires_grad=False)
                            self.config=types.SimpleNamespace(to_dict=lambda:{})
                        def forward(self,x):return x@self.weight
                    model=Qwen3_5VisionModel().eval();store=read_cache.ReadCache(1000000)
                    read_cache.install_vision_cache(types.SimpleNamespace(model=types.SimpleNamespace(visual=model)),store)
                    def factory(*args,**kw):
                        def generate(item):
                            with torch.no_grad():model(torch.ones(1,2))
                            return fixtures.row(item['id'])['output']
                        generate.weight_boundary=store.weight_boundary
                        return generate
                    def worker(argv,**kw):
                        import a8
                        def main(args):
                            assert args.pop(0)=='--enable-extensions'
                            parsed=fixtures.launch.parser().parse_args(args);parsed.reader_entry='fixture:make_real'
                            assert not parsed.atomic_journal and not parsed.scene_shards
                            parsed.device='cpu'
                            assert fixtures.launch.run_types(parsed,make_real=factory)['completed']==636
                            return 0
                        worker_cfg=Path(kw['cwd'])/argv[-1]
                        with patch.object(a8,'main',side_effect=main),patch.object(sys,'argv',[str(Path(kw['cwd'])/'5.py'),str(worker_cfg)]):
                            try:runpy.run_path(str(Path(kw['cwd'])/'5.py'),run_name='__main__')
                            except SystemExit as error:assert error.code==0
                        return types.SimpleNamespace(wait=lambda:0)
                    try:
                        with patch('h1eval.items.load_manifest',return_value=case.manifest):
                            # Only the namespace/model/device query is simulated.
                            config=dict(config,device='cpu',prefix=[])
                            return actual_run(config,['cpu-stub'],end,launcher=worker,**{k:v for k,v in kwargs.items() if k!='prefix'})
                    finally:case.doCleanups()
                stack.enter_context(patch.object(runner,'run',side_effect=execute))
                actual_operator=operator.run
                stack.enter_context(patch.object(operator,'run',side_effect=lambda config,end,cards:actual_operator(config,end,['cpu-stub'])))
            stack.enter_context(patch.object(sys,'argv',[str(root/'7.py'),str(local)]))
            try:operator.main()
            except SystemExit as error:assert error.code==0
    print('PASS action',cfg['action'],'rehearsal',bool(cfg.get('rehearsal')))


def control_child(target,root,mode):
    import torch
    torch.set_num_threads(8)
    p=target/'src';sys.path[:0]=[str(p),str(p/'b'),str(p/'tree'),str(p/'u0')]
    from orchard_h10 import common,job,export_pins
    package=target/'package';cfg=common.read_config(package)
    logical=cfg['logical'];sandbox=root/'sandbox';root.mkdir(parents=True,exist_ok=True)
    def physical(_,value):return sandbox/Path(value).relative_to(logical)
    def stage(r,c,i,S,J):
        assert c==cfg
        # Namespace stub mounts the already-built source read-only by convention.
        # Avoid making two more full payload copies for each CPU regression.
        sandbox.mkdir(parents=True,exist_ok=True)
        (sandbox/'p').symlink_to(p,target_is_directory=True)
        for name,spec in export_pins.load(i,package)['preparation'].items():
            dest=physical(r,logical+'/d/'+spec['path']);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text('{}')
        (r/'a').mkdir(exist_ok=True)
        return {}
    def write_test(pool,token):
        pool=root/'pool' if str(pool).startswith('/project/') else Path(pool)
        dest=pool/token/'.wtest';dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(bytes(4*1024**2))
        (root/'6.py').write_bytes((p/'orchard_h10/vendor/return_io.py').read_bytes())
        return dict(bytes=dest.stat().st_size,sha256=digest(dest))
    def publish(*args):return {'stub_storage_publication':True}
    J=types.SimpleNamespace(physical=physical,storage_proof=lambda *a,**k:{'fixture':True},
          environment=lambda *a:dict(PATH='/usr/bin:/bin'),namespace=lambda *a:[])
    R=types.SimpleNamespace(write_test=write_test,publish=publish,__file__=str(p/'orchard_h10/vendor/orchard_results.py'))
    def execute(argv,**kwargs):
        if argv[0]=='nvidia-smi':return types.SimpleNamespace(returncode=0,stdout='CPU stub; no GPU query ran')
        action=Path(argv[-1]);value=json.loads(action.read_text())
        assert Path(argv[-2]).name==('7.py' if value['action']==1 else '5.py')
        result=subprocess.run([sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'--action',str(target),str(root),str(action)],
                              env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8'),
                              stdout=kwargs.get('stdout'),stderr=subprocess.STDOUT)
        if kwargs.get('check') and result.returncode:raise subprocess.CalledProcessError(result.returncode,argv)
        return result
    def mapped_path(value):
        if str(value)=='/project/community/jjyeung/okh7':return target.parent/'shared'
        return Path(value)
    with ExitStack() as stack:
        stack.enter_context(patch.object(common,'template',return_value=(None,J,R,None,None)))
        stack.enter_context(patch.object(job,'template',return_value=(None,J,R,None,None)))
        stack.enter_context(patch.object(job,'stage',side_effect=stage))
        stack.enter_context(patch.object(common,'install_process_guard'))
        stack.enter_context(patch.object(common,'checked_run',side_effect=execute))
        stack.enter_context(patch.object(job,'checked_run',side_effect=execute))
        stack.enter_context(patch.object(job,'Path',side_effect=mapped_path))
        stack.enter_context(patch.object(job,'os',types.SimpleNamespace(environ=dict(os.environ,
            SLURM_JOB_ID='123',A_N='1',A_T='10000',CUDA_VISIBLE_DEVICES='cpu-stub',
            A_I=digest(package/'a/1.json'),A_C=digest(package/'2.json') if (package/'2.json').exists() else ''),umask=os.umask)))
        if mode=='node':
            node=load('cpu_proof4',package/'a/5.py')
            stack.enter_context(patch.object(node.tempfile,'mkdtemp',return_value=str(root)))
            stack.enter_context(patch.dict(os.environ,SLURM_JOB_ID='123'))
            stack.enter_context(patch.object(sys,'argv',[str(package/'a/5.py'),'--package',str(package),
                  '--sequence',str(package/'a/6.py'),'--results',str(target/'proof')]))
            node.main()
        else:
            boot=load('bootstrap4',root/'0.py')
            stack.enter_context(patch.object(boot,'Path',side_effect=mapped_path))
            stack.enter_context(patch.object(sys,'argv',[str(root/'0.py'),str(root)]))
            # job.main is intentionally real; both a/0.json and a/1.json are its outputs.
            boot.main()
    print('PASS real',mode,'control path')


class Round4Tests(unittest.TestCase):
    def test_f1_step600_package_preserves_a4_contract_and_binding(self):
        root=directory();target,binding=build_profile(root)
        payload=archive(target/'package/0.tgz');cfg=json.loads(payload['9.json'])
        base=archive(INPUT.parent/'package/0.tgz');old=json.loads(base['9.json'])
        for key in ('stage1_select_rule','perception_memo','perception_memo_verify_ids','save_own_depth','perception_memo_modules'):
            self.assertEqual(cfg.get(key),old[key],key)
        self.assertEqual(cfg.get('export_binding'),binding)
        self.assertEqual(payload['8.py'],base['8.py'])
        fill=load('fill4',target/'package/a/4.py')
        self.assertEqual(fill.reviewed_binding(),binding)
        done=root/'done';done.write_text(binding['object']+' '+str(binding['archive_bytes'])+' '+binding['archive_sha256'])
        fill.receipt_review(done)
        done.write_text(binding['object']+' '+str(binding['archive_bytes']+1)+' '+binding['archive_sha256'])
        with self.assertRaisesRegex(ValueError,'receipt'):fill.receipt_review(done)

        self.assertEqual(payload['orchard_h10/export_pins.py'],base['orchard_h10/export_pins.py'])
        ast.parse(payload['8.py'].decode(),feature_version=(3,6))
        self.assertNotIn('file_digest',payload['8.py'].decode())
        self.assertNotIn('capture_output',payload['8.py'].decode())
        self.assertIn("/project/community/jjyeung/okh7",payload['8.py'].decode())
        for n,pin in cfg['payload_pins'].items():
            self.assertEqual(hashlib.sha256(payload[n]).hexdigest(),pin['sha256'])
        self.assertTrue(cfg['read_extensions']);self.assertFalse(cfg['read_atomic_journal']);self.assertFalse(cfg['read_scene_shards'])
        cfg,inputs,export=seed_inputs(target,binding)
        admission=load('admission4',target/'src/orchard_h10/export_pins.py')
        admission.admit(inputs,cfg,export)
        artifact={key:binding[key] for key in ('step','config_sha256','base_identity','frame_layout')}
        for name in ('heads','full_weights'):
            artifact[name]=dict(path='/scratch/jjyeung/'+binding['run']+'/'+binding['member_directory']+'/'+fill.MEMBERS[name])
        args=types.SimpleNamespace(object=binding['object'],step=binding['step'],lineage=binding['lineage'])
        whole=dict(sha256=binding['archive_sha256'],parts=[{'bytes':binding['archive_bytes']}])
        fill.bind_review(args,copy.deepcopy(export),artifact,whole,export['preparation'],binding)
        with self.assertRaisesRegex(ValueError,'whole-tar'):
            fill.bind_review(args,export,artifact,dict(whole,sha256='0'*64),export['preparation'],binding)

        for key in ('step','run','object','member_directory','lineage','config_sha256','archive_sha256'):
            bad=copy.deepcopy(export);bad[key]=601 if key=='step' else 'wrong'
            with self.subTest(key=key),self.assertRaises(ValueError):admission.admit(inputs,cfg,bad)
        for key in binding['preparation_sha256']:
            bad=copy.deepcopy(export);bad['preparation'][key]['sha256']='0'*64
            with self.subTest(preparation=key),self.assertRaises(ValueError):admission.admit(inputs,cfg,bad)

    def test_f2_step600_real_job_and_rehearsal_memory(self):
        root=directory();target,binding=build_profile(root);cfg,inputs,export=seed_inputs(target,binding)
        # Both processes read the package's 9.json unchanged.
        command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'--control',str(target),str(root/'node'),'node']
        result=subprocess.run(command,capture_output=True,text=True)
        logs='\n'.join(p.read_text() for p in (target/'proof').glob('*.log'))
        self.assertEqual(result.returncode,0,str(root)+'\n'+result.stdout+result.stderr+logs+'\n'+'\n'.join(p.read_text() for p in (root/'job/sandbox/r').glob('FAILED.json')))
        proof=json.loads((target/'proof/CPU.json').read_text())
        self.assertEqual(proof['memory'].get('read_cache_bytes'),12*1024**3)
        self.assertTrue(proof['entry_sequence_passed']);self.assertTrue(proof['bundle_guard_passed'])
        shared=root/'shared'/('a15_cot_ap'+cfg['token']);shared.mkdir(parents=True)
        for path in (target/'package').rglob('*'):
            if path.is_file():
                dest=shared/path.relative_to(target/'package');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        write(shared/'a/c/CPU.json',proof)
        receipt=dict(passed=True,plan=proof['plan'],inputs=proof['inputs'])
        write(shared/'2.json',receipt);write(target/'package/2.json',receipt)
        builder=load('bundle_decoder4',SRC/'u0/a19.py')
        jobroot=root/'job';jobroot.mkdir()
        for name,raw in builder.bootstrap((shared/'BATCH.sh').read_text()).items():(jobroot/name).write_bytes(raw)
        command=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'--control',str(target),str(jobroot),'job']
        result=subprocess.run(command,capture_output=True,text=True)
        logs='\n'.join(p.read_text() for p in (jobroot/'sandbox/r/logs').glob('*.log'))
        self.assertEqual(result.returncode,0,str(root)+'\n'+result.stdout+result.stderr+logs+'\n'+'\n'.join(p.read_text() for p in (root/'job/sandbox/r').glob('FAILED.json')))
        zero=json.loads((jobroot/'a/0.json').read_text())
        one=json.loads((jobroot/'a/1.json').read_text())
        public=json.loads((shared/'0.json').read_text())
        self.assertEqual(zero['config'],dict(cfg,**public))
        self.assertEqual(zero['config']['export_binding'],binding)
        self.assertFalse(one['config']['read_atomic_journal']);self.assertTrue(one['config']['read_extensions'])
        settings=json.loads((jobroot/'sandbox/d/settings.json').read_text())
        self.assertEqual(settings['stage1_select_rule'],'candidates_argmax');self.assertEqual(settings['perception_memo'],'on')
        summary=json.loads((jobroot/'sandbox/r/SUMMARY.json').read_text());self.assertEqual(summary['completed'],636)
        self.assertTrue(summary['complete']);self.assertIsNone(summary['failure'])
        journals=jobroot/'sandbox/r/metadata/reads/0/metadata/journals'
        receipts=list(journals.glob('*/*/WEIGHTS.json'));self.assertEqual(len(receipts),5)
        for receipt in receipts:
            self.assertIs(json.loads(receipt.read_text())['verified'],True)
            self.assertFalse((receipt.parent/'committed').exists())
        self.assertFalse((jobroot/'sandbox/r/metadata/reads/0/metadata/u0').exists())
        self.assertEqual(digest(target/'tower_sequence.py'),one['config']['operator_sha256'])
        # Exercise the actual authenticated unpack entry, including partial returns.
        sys.path.insert(0,str(target));unpacker=load('return_entry4',target/'unpack_return.py')
        def returned(name):
            returned_root=jobroot/'sandbox/r'
            raw=builder.tarbytes({str(p.relative_to(returned_root)):p.read_bytes()
                for p in returned_root.rglob('*') if p.is_file()})
            path=root/(name+'.tgz');path.write_bytes(raw)
            receipt=dict(plan_sha256=public['plan_sha256'],token=cfg['token']+format(123,'08x'),
                job='123',synthetic=False,archive_bytes=len(raw),archive_sha256=hashlib.sha256(raw).hexdigest(),
                complete=False,status='FAILED')
            exit_path=root/(name+'.json');write(exit_path,receipt)
            with patch.object(sys,'argv',[str(target/'unpack_return.py'),'--archive',str(path),
                    '--exit',str(exit_path),'--out',str(root/(name+'-return'))]):
                unpacker.main()
        returned('verified')
        write(receipts[0],{'verified':False})
        with self.assertRaisesRegex(ValueError,'Unverified weight journal'):returned('unverified')

        write(root/'EVIDENCE.json',dict(synthetic_binding=binding,proof=proof,summary=summary,weight_receipts=5,
             real_job_main=True,namespace_paths_only=True,ordinary_journals=True))
        print('CPU step-600 fixture:',root)

    def test_f3_cache_only_return_refuses_unverified_journals(self):
        root=directory();path=INPUT.parent/'unpack_return.py' if BEFORE else OP/'unpack_return.py'
        sys.path.insert(0,str(INPUT.parent));module=load('unpack4',path)
        journal=root/'metadata/reads/0/metadata/journals/3/0';journal.mkdir(parents=True)
        write(journal/'STARTED.json',{});write(journal/'environment.json',{})
        (journal/'items.jsonl').write_text('{}\n')
        def validate(enabled=True):
            if BEFORE:return module.validate_journals(root)
            return module.validate_journals(root,read_extensions=enabled)
        validate()
        for value in (False,None,0,1,'true'):
            write(journal/'WEIGHTS.json',{'verified':value})
            with self.subTest(verified=value),self.assertRaisesRegex(ValueError,'Unverified weight journal'):validate()
        write(journal/'WEIGHTS.json',{'verified':True});validate()
        write(journal/'WEIGHTS.json',{'verified':False});validate(False)

    def test_f9_off_builder_guard_and_processor_only(self):
        if BEFORE:self.skipTest('New route default and processor-only checks apply to delivered builder')
        builder=load('default4',E/'a19.py')
        root=directory()
        with self.assertRaisesRegex(ValueError,'OFF'):
            builder.build(INPUT.parent,SRC,root/'missing',root/'out','ab0123456789')
        self.assertFalse((root/'out').exists())
        target,binding=build_profile(root,processor_only=True)
        cfg=json.loads(archive(target/'package/0.tgz')['9.json'])
        self.assertEqual(cfg['read_processor_only'],'on');self.assertEqual(cfg['read_cache_bytes'],4*1024**3)
        self.assertEqual(cfg['read_sam_cache'],'off');self.assertEqual(cfg['read_vision_cache'],'off')
        self.assertEqual(cfg['export_binding'],binding)
        bad=copy.deepcopy(binding);bad.pop('preparation_sha256');write(root/'bad.json',bad)
        with self.assertRaisesRegex(ValueError,'binding'):
            builder.build(root/'base',SRC,root/'bad.json',root/'badout','ab0123456789',enable_extensions=True)
        self.assertFalse((root/'badout').exists())


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--action':action_child(*map(Path,sys.argv[2:5]))
    elif len(sys.argv)>1 and sys.argv[1]=='--control':control_child(Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
    else:unittest.main(verbosity=2)
