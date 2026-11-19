"""Round-3 fail-before/pass-after CPU contracts; no GPU or scheduler."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import types
import unittest
import uuid
from unittest.mock import patch
import torch
torch.set_num_threads(8)
SRC=Path(__file__).resolve().parents[2]
L=Path(os.environ.get('READ_WORKSPACE','/scratch/jjyeung/orch_n30/so_read'))
BEFORE=os.environ.get('READ_ROUND3_BEFORE')=='1'
E=L/'work/round3-before-u0' if BEFORE else SRC/'u0'
KIT=L/'out_round3/kit_parity50' if BEFORE else L/'out/kit_parity50'
sys.path[:0]=[str(E),str(SRC),str(SRC/'b'),str(Path(os.environ['READ_INPUT_SRC'])/'tree')]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def directory():
    root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True);return root

C=load('round3_cache',E/'a0.py')

class Qwen3_5VisionModel(torch.nn.Module):
    def __init__(self):
        super().__init__();self.weight=torch.nn.Parameter(torch.ones(32,32),requires_grad=False)
        self.register_buffer('scale',torch.tensor(2.));self.config=types.SimpleNamespace(to_dict=lambda:{})
    def forward(self,x):return x@self.weight*self.scale

def visual():
    m=Qwen3_5VisionModel().eval();store=C.ReadCache(1000000)
    C.install_vision_cache(types.SimpleNamespace(model=types.SimpleNamespace(visual=m)),store)
    return m,store

class Round3Tests(unittest.TestCase):
    def test_f1_calls_never_hash_parameters_or_buffers(self):
        m,store=visual();original=C.digest
        weights={id(m.weight),id(m.scale)}
        def visit(v):
            if isinstance(v,torch.Tensor):self.assertNotIn(id(v),weights,'Per-call weight hashing')
            elif isinstance(v,(tuple,list)):
                for x in v:visit(x)
            elif isinstance(v,dict):
                for x in v.values():visit(x)
        def checked(v):visit(v);return original(v)
        with torch.no_grad(),patch.object(C,'digest',side_effect=checked):
            a=m(torch.ones(1,32));b=m(torch.ones(1,32))
        self.assertTrue(torch.equal(a,b));self.assertEqual(store.stats['vision']['hits'],1)

    def test_f1_parameter_and_buffer_changes_are_fatal_and_latched(self):
        self.assertTrue(hasattr(C,'ModelMutationError'),'Missing fatal weight guard')
        for name in ('weight','scale'):
            for how in ('inplace','replace','data_assignment'):
                with self.subTest(name=name,how=how):
                    m,store=visual();t=getattr(m,name)
                    with torch.no_grad():
                        m(torch.ones(1,32))
                        if how=='inplace':t.add_(1)
                        elif how=='replace':setattr(m,name,torch.nn.Parameter(t.clone(),requires_grad=False) if name=='weight' else t.clone())
                        else:t.data=t.clone()+1
                        with self.assertRaises(C.ModelMutationError):m(torch.ones(1,32))
                        with self.assertRaises(C.ModelMutationError):store.weight_boundary()
        # Real optimizer steps bump the parameter version on this installed torch.
        m,store=visual();m.weight.requires_grad_(True)
        optimizer=torch.optim.SGD([m.weight],lr=.1,foreach=False)
        stamp=m.weight._version;m.weight.grad=torch.ones_like(m.weight);optimizer.step()
        self.assertGreater(m.weight._version,stamp)

    def test_f1_raw_storage_is_rejected_at_boundary(self):
        self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing boundary hashing')
        for name in ('weight','scale'):
            for how in ('data','numpy'):
                with self.subTest(name=name,how=how):
                    m,store=visual();t=getattr(m,name)
                    stamp=(id(t),t.data_ptr(),t._version)
                    if how=='data':t.data.add_(1)
                    else:t.detach().numpy()[...]+=1
                    self.assertEqual(stamp,(id(t),t.data_ptr(),t._version))
                    with self.assertRaises(C.ModelMutationError):store.weight_boundary()
        with torch.inference_mode():m=Qwen3_5VisionModel().eval()
        with self.assertRaisesRegex(C.ModelMutationError,'version counters'):
            C.install_vision_cache(types.SimpleNamespace(model=types.SimpleNamespace(visual=m)),C.ReadCache(1000000))

    def test_f1_processor_only_overrides_model_switches(self):
        flags=C.switches(dict(read_processor_only='on',read_vision_cache='on',read_sam_cache='on'))
        self.assertEqual(flags,dict(read_processor_cache='on',read_vision_cache='off',read_sam_cache='off'))
        self.assertEqual(C.cache_bytes(dict(read_processor_only='on',read_sam_cache='on')),4*1024**3)
        self.assertEqual(C.switches({}),{k:'off' for k in C.SWITCHES})

    def test_f1_type_boundary_failure_blocks_resume_and_merge(self):
        self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing weight boundary')
        fixtures=load('round3_journal_fixture',SRC/'u0/tests/test_read_journal.py')
        if BEFORE:fixtures.launch=load('h1eval.h10.launch',E/'a4.py')
        case=fixtures.RunnerTests();case.setUp()
        try:
            m,store=visual();calls=[];hashes=[]
            original=C.weight_digest
            def hashed(model):hashes.append(True);return original(model)
            args=case.args('checked');args.types='camera_rotation'
            def factory(*a,**kw):
                def generate(item):
                    calls.append(item['id'])
                    with torch.no_grad():m(torch.ones(1,32))
                    if item['id']=='4':m.weight.data.add_(1)
                    return fixtures.row(item['id'])['output']
                generate.weight_boundary=store.weight_boundary
                return generate
            with patch.object(C,'weight_digest',side_effect=hashed):
                with self.assertRaises(C.ModelMutationError):fixtures.launch.run_types(args,make_real=factory)
            self.assertEqual(calls,['0','1','2','3','4'])
            self.assertEqual(len(hashes),2) # type entry and exit; none per item
            root=Path(args.out)/'1/0'
            from orchard_h10.common import ORDER
            root=Path(args.out)/str(ORDER.index('camera_rotation'))/'0'
            self.assertFalse(json.loads((root/'WEIGHTS.json').read_text())['verified'])
            with self.assertRaisesRegex(ValueError,'Unchecked cache weights'):
                fixtures.launch.run_types(args,make_real=factory)
            with self.assertRaisesRegex(ValueError,'Unchecked cache weights'):
                fixtures.merge(case.manifest,[root],case.root/'bad-merge')
        finally:case.doCleanups()

    def test_f1_valid_boundary_allows_deadline_resume_and_public_merge(self):
        self.assertTrue(hasattr(C.ReadCache,'weight_boundary'),'Missing weight boundary')
        fixtures=load('round3_resume_fixture',SRC/'u0/tests/test_read_journal.py')
        case=fixtures.RunnerTests();case.setUp()
        original_json=fixtures.launch.json;original_journal_json=fixtures.J.json
        try:
            m,store=visual()
            def factory(*a,**kw):
                def generate(item):
                    with torch.no_grad():m(torch.ones(1,32))
                    return fixtures.row(item['id'])['output']
                generate.weight_boundary=store.weight_boundary
                return generate
            args=case.args('graceful');commit=fixtures.launch.commit_record
            def interrupted(stream,row):
                if row.get('id')=='1':raise fixtures.launch.ReadDeadline()
                return commit(stream,row)
            with patch.object(fixtures.launch,'commit_record',side_effect=interrupted):
                with self.assertRaises(fixtures.launch.ReadDeadline):fixtures.launch.run(args,make_real=factory)
            self.assertIs(json.loads((Path(args.out)/'WEIGHTS.json').read_text())['verified'],True)
            self.assertEqual(fixtures.launch.run(args,make_real=factory)['completed'],5)
            private=fixtures.merge(case.manifest,[args.out],case.root/'merged-private')
            args=case.args('public-checked');args.opaque=True
            fixtures.launch.run(args,make_real=factory)
            from a9 import Codec,read_wire
            self.assertTrue(read_wire(json.loads((Path(args.out)/'WEIGHTS.json').read_text()))['verified'])
            result=fixtures.merge(case.manifest,[args.out],case.root/'merged-public',
                                  public_codec=Codec(case.manifest,vars(args)))
            self.assertEqual(result['items'],private['items'])
        finally:
            fixtures.launch.json=original_json;fixtures.J.json=original_journal_json
            case.doCleanups()

    def test_f3_both_base_inventories_are_authenticated(self):
        kit=load('round3_kit_roots',KIT/'run.py');root=directory();kit.HERE=root
        orig=root/'original';src=root/'patched';orig.mkdir();(src/'u0').mkdir(parents=True)
        for target in (orig,src):(target/'base.py').write_bytes(b'base')
        (src/'u0/a8.py').write_bytes(b'extension')
        pins={'u0/a8.py':hashlib.sha256(b'extension').hexdigest()}
        inv={'base.py':hashlib.sha256(b'base').hexdigest()}
        base=dict(inventory=inv,files=1,sha256=hashlib.sha256(json.dumps(sorted(inv.items()),sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())
        (root/'EXTENSION_PINS.json').write_text(json.dumps(pins));(root/'BASE_PIN.json').write_text(json.dumps(base))
        cfg=dict(original_source_root=str(orig),source_root=str(src));kit.validate_roots(cfg)
        # Equal wrong readers must fail even when ORIGINAL/OFF/ON would agree.
        for target in (orig,src):(target/'base.py').write_bytes(b'wrong')
        with self.assertRaisesRegex(ValueError,'Base hash differs'):kit.validate_roots(cfg)
        for target in (orig,src):(target/'base.py').write_bytes(b'base')
        (src/'extra.py').write_bytes(b'extra')
        with self.assertRaisesRegex(ValueError,'Base inventory differs'):kit.validate_roots(cfg)

    def test_f4_worker_uses_settings_argv_without_environment_side_effect(self):
        # Stop at the CUDA availability check, after actual worker setup.
        path=L/'work/round2-before/kit/run.py' if os.environ.get('READ_F16_BEFORE')=='1' else KIT/'run.py'
        kit=load('round3_kit_worker',path);root=directory()
        cfg=dict(original_source_root=str(SRC),source_root=str(SRC),settings=str(root/'u0.json'))
        saved=sys.path[:]
        try:
            with patch.object(kit,'os',types.SimpleNamespace(environ={'CUDA_VISIBLE_DEVICES':'fixture'})), \
                 patch.object(sys,'argv',['u0.py']),patch.object(torch.cuda,'is_available',return_value=False):
                with self.assertRaisesRegex(ValueError,'CUDA is unavailable'):kit.worker(cfg,'OFF',root,True)
                self.assertNotIn('H10_SETTINGS',kit.os.environ)
                self.assertEqual(sys.argv[-2:],['--settings',cfg['settings']])
        finally:sys.path[:]=saved

    def test_f7_off_import_guard_covers_all_overlay_modules(self):
        off=load('round3_off_guard',E/'tests/test_off.py');guard=off.RefuseExtensions()
        for i in range(19):
            with self.subTest(module=i),self.assertRaisesRegex(AssertionError,'OFF attempted'):
                guard.find_spec('a'+str(i))

if __name__=='__main__':unittest.main(verbosity=2)
