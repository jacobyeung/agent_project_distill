"""Exercise A4's real operator bootstrap and sequence with an a12 ON payload."""
import ast
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
BEFORE=os.environ.get('READ_ROUND3_BEFORE')=='1'
E=L/'work/round3-before-u0' if BEFORE else SRC/'u0'
OPERATOR=Path(os.environ.get('READ_OPERATOR_SOURCE',str(L/('work/operator3-original/7.py' if BEFORE else 'work/operator3/7.py'))))

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def decode(batch):
    line=next(x for x in batch.splitlines() if x.startswith('b=bytes.fromhex('))
    raw=bytes.fromhex(ast.literal_eval(line[len('b=bytes.fromhex('):-1]))
    with tarfile.open(fileobj=io.BytesIO(raw)) as a:
        return {e.name:a.extractfile(e).read() for e in a if e.isfile()}

def child(root,action):
    p=root/'p';sys.path[:0]=[str(p),str(p/'b'),str(p/'tree'),str(p/'u0')]
    import torch
    torch.set_num_threads(8)
    from orchard_h10 import common,runner,prepare
    assert Path(runner.__file__).read_bytes()==(p/'u0/a17.py').read_bytes()
    assert Path(prepare.__file__).read_bytes()==(p/'u0/a18.py').read_bytes()
    boot=load('operator_bootstrap',root/'0.py');operator=load('operator_sequence',root/'7.py')
    cfgpath=root/'a'/f'{action}.json';cfg=json.loads(cfgpath.read_text())
    observed=[]
    def prepare_stub(config,inputs):
        # The heavy restore is a stub, but the preparation module and dispatch are real.
        assert config['read_extensions'] is True
        from e2e_reader import read_cache,parity,stage1
        for module,name in ((read_cache,'a0.py'),(parity,'a1.py'),(stage1,'a3.py')):
            assert Path(module.__file__).read_bytes()==(p/'u0'/name).read_bytes()
        settings=dict(stage1_select_rule='candidates_argmax',perception_memo='on',
                      perception_memo_modules=['g3t'],perception_memo_verify_ids=[])
        for key in ('read_processor_cache','read_vision_cache','read_sam_cache','read_cache_bytes'):
            settings[key]=config[key]
        Path(config['settings']).write_text(json.dumps(settings));observed.append('prepare')
    def execute_worker(argv,**kwargs):
        # Execute the real action-2 entry and parser with a stub model factory.
        worker=Path(kwargs['cwd'])/argv[-1]
        value=json.loads(worker.read_text());assert value['action']==2
        def main(args):
            assert args[0]=='--enable-extensions'
            parsed=fixtures.launch.parser().parse_args(args[1:])
            parsed.reader_entry='fixture:make_real'
            assert parsed.atomic_journal and not parsed.scene_shards
            return_code=fixtures.launch.run_types(parsed,make_real=case.make_real)
            assert return_code['completed']==636
            return 0
        import a8
        with patch.object(sys,'argv',[str(kwargs['cwd']/'5.py'),str(worker)]),patch.object(a8,'main',side_effect=main):
            try:runpy.run_path(str(kwargs['cwd']/'5.py'),run_name='__main__')
            except SystemExit as e:assert e.code==0
        observed.append('worker')
        return types.SimpleNamespace(wait=lambda:0)
    def execute_sequence(config,cards,end,**kwargs):
        nonlocal fixtures,case
        # 7.py must activate its own overlays in this fresh action-1 process.
        from h1eval.h10 import launch
        assert Path(launch.__file__).read_bytes()==(p/'u0/a4.py').read_bytes(),'Operator overlay not active'
        fixtures=load('operator_fixtures',p/'u0/tests/test_read_journal.py')
        case=fixtures.RunnerTests();case.setUp()
        case.manifest=json.loads((p/'items/devs1_routed.json').read_text())
        for patcher in case.patches:patcher.stop()
        case.patches=[patch.object(fixtures.launch,'load_manifest',return_value=case.manifest),
                      patch.object(fixtures.item_module,'read_contract'),
                      patch.object(fixtures.launch,'sha',return_value='0'*64),
                      patch.object(fixtures.launch,'code_hash',return_value='1'*64),
                      patch.object(fixtures.launch,'export_hash',return_value='2'*64)]
        for patcher in case.patches:patcher.start()
        try:
            # Patch only the heavy factory/model, manifest registration and process spawn.
            with patch('h1eval.items.load_manifest',return_value=case.manifest):
                result=actual_runner(config,cards,end,launcher=execute_worker,**kwargs)
            assert result['complete'] and result['completed']==636,result
            assert result['merged_return']['path']=='metadata/u0/answer_trace_return.tgz'
            return result
        finally:case.doCleanups()
    fixtures=case=None;actual_runner=runner.run
    def dispatch(argv,**kwargs):
        observed.append(Path(argv[-2]).name)
        if action==0:
            assert argv[-2:]==[str(root/'a/5.py'),str(cfgpath)]
            with patch.object(sys,'argv',argv[-2:]):runpy.run_path(argv[-2],run_name='__main__')
        else:
            assert argv[-2:]==[str(root/'7.py'),str(cfgpath)]
            with patch.object(sys,'argv',argv[-2:]),patch.object(operator,'run',side_effect=lambda config,end,cards:actual_operator(config,end,['cpu-fixture'])):
                try:operator.main()
                except SystemExit as e:assert e.code==0
    actual_operator=operator.run
    with patch.object(common,'install_process_guard'),patch.object(prepare,'run',side_effect=prepare_stub),patch.object(runner,'run',side_effect=execute_sequence):
        boot.make_dispatch(root,dispatch,common.sha(root/'7.py'))(
            [sys.executable,'-I','-s','-B',str(root/'a/5.py'),str(cfgpath)])
    if action==0:assert observed==['5.py','prepare'],observed
    else:
        assert observed==['7.py','worker'],observed
        archive=root/'output/metadata/reads/0/metadata/u0/answer_trace_return.tgz'
        assert archive.is_file()
        from orchard_h10.vendor import chain_save
        assert 'metadata/reads/0/metadata/u0/answer_trace_return.tgz' in chain_save.members(root/'output')
        with tarfile.open(archive) as t:
            assert len(t.extractfile('items.jsonl').read().splitlines())==636
    print('PASS: A4 operator action',action,'with ON overlays and CPU stubs')

class OperatorTests(unittest.TestCase):
    def test_f2_operator_memory_bound_includes_cache_only_when_enabled(self):
        operator=load('memory_operator',OPERATOR)
        before=load('original_memory_operator',L/'work/operator3-original/7.py')
        self.assertEqual(operator.memory_bound(),before.memory_bound())
        self.assertIn('read_extensions',__import__('inspect').signature(operator.memory_bound).parameters,
                      'Operator omits read cache memory')
        baseline=operator.memory_bound()
        on=operator.memory_bound(read_extensions=True,read_cache_bytes=12*1024**3)
        self.assertEqual(on['read_cache_bytes'],12*1024**3)
        self.assertEqual(on['reads'][0]['host_budget_bytes']-baseline['reads'][0]['host_budget_bytes'],12*1024**3)
        self.assertFalse(operator.memory_bound(read_extensions=True,read_cache_bytes=12*1024**3,
                         allocation_bytes=baseline['reads'][0]['host_budget_bytes'])['fits'])
        self.assertEqual(operator.memory_bound(read_cache_bytes=12*1024**3),baseline)

    def test_f2_a12_payload_through_a4_actions_and_nested_return(self):
        sys.path[:0]=[str(SRC),str(SRC/'b'),str(INPUT/'tree')]
        builder=load('operator_builder',E/'a12.py');original=load('input_builder',INPUT/'orchard_h10/build.py')
        original.B=INPUT/'b';original.T=INPUT/'orchard_h10/vendor'
        root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True)
        for name,path in original.sources().items():
            dest=root/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        for path in E.rglob('*'):
            if path.is_file():
                dest=root/'source/u0'/path.relative_to(E);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(path.read_bytes())
        builder.K=root/'source';builder.B=builder.K/'b';builder.T=builder.K/'orchard_h10/vendor'
        builder.build(builder.K/'package','ab0123456789',enable_extensions=True)
        package=builder.K/'package'
        with tarfile.open(package/'0.tgz') as t:
            payload={e.name:t.extractfile(e).read() for e in t if e.isfile()}
        cfg=json.loads(payload['9.json'])
        for name,pin in cfg['payload_pins'].items():self.assertEqual(hashlib.sha256(payload[name]).hexdigest(),pin['sha256'])
        for name,raw in payload.items():
            dest=root/'p'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
        bundled=decode((INPUT.parent/'package/BATCH.sh').read_text())
        (root/'0.py').write_bytes(bundled['0.py']);(root/'7.py').write_bytes(OPERATOR.read_bytes())
        self.assertEqual(bundled['7.py'],(INPUT.parent/'tower_sequence.py').read_bytes())
        (root/'a').mkdir();(root/'output/metadata').mkdir(parents=True)
        (root/'a/5.py').write_bytes(payload['orchard_h10/entry.py'])
        (root/'pin.json').write_text(json.dumps(dict(lineage='SFT',step=600)))
        config=dict(cfg,package=str(root/'p'),output=str(root/'output'),settings=str(root/'settings.json'),
             export=str(root/'export'),export_pin=str(root/'pin.json'),binding=str(root/'binding.json'),
             python=sys.executable,plan_sha256='1'*64,inputs_sha256='2'*64,device='cpu',prefix=[],
             read_scene_shards=False)
        import time
        for action in (0,1):
            (root/'a'/f'{action}.json').write_text(json.dumps(dict(action=action,package=str(root/'p'),
                config=config,inputs={},end=time.time()+10000)))
            cmd=[sys.executable,'-I','-s','-B',str(Path(__file__).resolve()),'--child',str(root),str(action)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        if not BEFORE:
            # Exercise the actual opt-in bundling interface, including processor-only.
            builder.build(builder.K/'operator','ab0123456789',enable_extensions=True,processor_only=True,
                          operator_bootstrap=root/'0.py',operator_source=OPERATOR)
            bundled=decode((builder.K/'operator/BATCH.sh').read_text())
            self.assertEqual(bundled['0.py'],(root/'0.py').read_bytes());self.assertEqual(bundled['7.py'],OPERATOR.read_bytes())
            with tarfile.open(builder.K/'operator/0.tgz') as t:
                config=json.load(t.extractfile('9.json'))
            self.assertEqual(config['read_processor_only'],'on');self.assertEqual(config['read_sam_cache'],'off')
            self.assertFalse(config['read_scene_shards'])

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--child':child(Path(sys.argv[2]),int(sys.argv[3]))
    else:unittest.main(verbosity=2)
