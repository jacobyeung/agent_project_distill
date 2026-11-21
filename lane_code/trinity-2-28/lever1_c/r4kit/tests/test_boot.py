"""Pre-bulk boot through prepare, production launch, finalize and real fetch."""
import importlib.util
import ast
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import time
import types
import unittest
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
B = module('builder', ROOT/'build.py')
NATIVE_SITE = module('native_fixture', ROOT/'tests/native_fixture.py').prepare(ROOT)
C = B.storage
ctl = module('control', ROOT/'src/control.py')
def members(raw):
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        return {m.name:archive.extractfile(m).read() for m in archive}
FILES = members((ROOT/'out/delivery.tgz').read_bytes())
EVIDENCE = []


class Boot(unittest.TestCase):
    def exercise(self, mode, missing):
        base = ROOT/'out'/('b'+uuid.uuid4().hex); base.mkdir()
        p = base/'p'; p.mkdir(); root = base/'j'
        files = dict(FILES)
        cfg = C.loads(files['2.json']); cfg['package'] = str(p)
        native = Path(sys.base_prefix); site = Path(sys.prefix)/'lib/python3.12/site-packages'
        native_site = NATIVE_SITE
        cfg['inputs']['env_roots'] = [str(native_site), str(site)]
        cfg['inputs']['files'] = {}
        inputs = base/'i'; inputs.mkdir()
        def archive(name, contents, destination=None):
            target = inputs/name; target.write_bytes(B.archive(contents))
            pin = dict(path=str(target), **B.pin(target.read_bytes()))
            return dict(parts=[pin], sha256=pin['sha256'], expanded_bytes=sum(map(len,contents.values())),
                        destination=destination or 'sj/b01ec87a6f29b/d')
        prefix = cfg['boot']['interpreter_prefix']
        # Tiny pinned fixtures exercise streaming/exclusion and staging order.
        # The namespace binds the existing local interpreter/packages read-only.
        first = archive('0', {prefix+'/0':b'python', 'sj/1':b'bulk-zero'})
        second = archive('1', {'m/ap/19252904/e/0':b'environment'})
        last = archive('2', {'sj/2':b'bulk-two'})
        cfg['assets']['groups'] = [[[r['path'],r['bytes'],r['sha256']] for r in a['parts']]
                                  for a in (first,second,last)]
        # Read only these two tiny members from the locally available pinned
        # archive; use the exact production shell front end and runpy wrapper.
        with tarfile.open('/scratch/jjyeung/orch_n30/reads228/dl/a4.tar') as source:
            entry = {name:source.extractfile(name).read() for name in ('v/py','v/boot.py')}
        overlay = archive('3', entry)
        bulk = archive('4', {'b/0':b'bulk-input'})
        cfg['inputs']['archives'] = [bulk, overlay]
        cfg['assets']['bwrap_pin'] = dict(path='/usr/bin/bwrap', **B.pin(Path('/usr/bin/bwrap').read_bytes()))
        cfg['boot'].update(input_archives=[1], archive_bytes=second['parts'][0]['bytes']+
            overlay['parts'][0]['bytes']+cfg['assets']['bwrap_pin']['bytes'])
        # Missing a real private dependency must fail the delivered worker,
        # including its import closure, without replacing launch or fetch.
        sources = C.loads(files['8.bin'])
        if missing == 'typing':
            sources['c/tree/boot_type_only.py'] = "import typing\nassert typing.TYPE_CHECKING is False\nfrom numbers import _IntegralLike as IntegralLike\n"
            closure = cfg['import_closure']
            closure['required_modules'] = sorted(closure['required_modules'] + ['boot_type_only'])
            closure['closure_sha256'] = B.digest('\n'.join(closure['required_modules']).encode())
            files['8.bin'] = C.pack(B.jd(sources))
        elif missing:
            sources.pop('c/tree/student_pilot/carrier_c1_canary.py')
            files['8.bin'] = C.pack(B.jd(sources))
        # The CPU-only environment cannot import CUDA extensions. Successful
        # GPU-mode boot uses explicit module doubles after Transformers has
        # selected its CPU implementations; missing-dependency cases use none.
        wrapper = ast.parse(files['7.py']).body[0].value
        probe_source = bytes.fromhex(ast.literal_eval(wrapper.args[0].args[0].args[0]))
        # Local torchvision has CUDA native operators while torch is CPU-only.
        # Its Python transforms are real; only the unused NMS schema is a double.
        probe_source += b'''\nimport torch
_vision_fixture = torch.library.Library('torchvision', 'DEF')
_vision_fixture.define('nms(Tensor dets, Tensor scores, float iou_threshold) -> Tensor')
'''
        if mode == 'g' and not missing:
            probe_source += b'''\nimport transformers.models.qwen3_5.modeling_qwen3_5
import types
import sys
for _name in ('fla', 'triton', 'causal_conv1d'):
    sys.modules[_name] = types.ModuleType(_name)
'''
        files['7.py'] = B.wrap(probe_source)
        files['2.json'] = C.pack(B.jd(cfg))
        payload = members(files['0.tgz'])
        payload.update({n:files[n] for n in ('2.json','8.bin','7.py')})
        files['0.tgz'] = B.archive(payload)
        pins = json.loads(files['0.json'])
        pins['files'].update({n:B.pin(files[n]) for n in ('2.json','8.bin','7.py','0.tgz')})
        files['0.json'] = B.jd(pins)
        for name, raw in files.items(): (p/name).write_bytes(raw)
        (p/'a').mkdir()
        current = dict(passed=True, package=ctl.sha(p/'0.json'), payload=ctl.sha(p/'0.tgz'), frozen=cfg['frozen'])
        C.store(p/'a/4.json', current)
        S, J = ctl.materialize(p, base)
        original_namespace = J.namespace
        base_env = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e'
        def namespace(job):
            args = original_namespace(job)
            args += ['--bind',str(job),str(job),
                     '--ro-bind',str(native),str(Path('/scratch/jjyeung/uv-python')/native.name),
                     '--ro-bind',str(native),J.UV,
                     '--ro-bind',sys.prefix,base_env,
                     '--ro-bind',sys.prefix,sys.prefix,
                     '--ro-bind',str(native_site),str(native_site)]
            return args
        # Extraction preserves archive modes; the fixture builder uses 0600.
        extracted = S.extract_stream
        def extract(*args, **kwargs):
            result = extracted(*args, **kwargs)
            front = root/'sj/b01ec87a6f29b/d/v/py'
            if front.exists(): front.chmod(0o700)
            return result
        copied = []; actual_copy = S.copy_parts
        def copying(parts, target, *args, **kwargs):
            copied.append((str(target), sum(r['bytes'] for r in parts)))
            return actual_copy(parts, target, *args, **kwargs)
        started = time.monotonic()
        # Positive cases stop after real preparation to avoid model execution;
        # the tested boot itself uses both production supervisors and 5.py.
        with patch.dict(os.environ,dict(A_M=mode,USER='a',SLURM_JOB_ID='123',CUDA_VISIBLE_DEVICES='0')), \
             patch.object(ctl,'disk_proof',return_value=dict(filesystem='ext4')), \
             patch.object(ctl,'materialize',return_value=(S,J)), \
             patch.object(J,'namespace',side_effect=namespace), \
             patch.object(S,'extract_stream',side_effect=extract), \
             patch.object(S,'copy_parts',side_effect=copying):
            if missing:
                self.assertEqual(ctl.work(p,root),1)
            else:
                root.mkdir()
                ctl.prepare(p,root,cfg,'123',time.time()+120)
                C.store(root/'p/a/1.json',dict(passed=True,records=0))
                ctl.finalize(p,root/'p/a',cfg,mode,'123',time.time(),0)
        with patch('builtins.print'): ctl.fetch(p,base/'f',mode)
        returned = members((base/'f/0.tgz').read_bytes())
        summary = C.loads(returned['1.json']); receipt = summary['execution']['boot']
        self.assertEqual(receipt['passed'],not missing)
        bulk_paths = {str(root/'a/0'), str(root/'a/2'), str(root/'a/a0')}
        bulk_bytes = sum(n for target,n in copied if target in bulk_paths)
        if missing:
            self.assertFalse(summary['passed'])
            self.assertEqual(bulk_bytes,0)
            self.assertFalse((root/'sj/1').exists())
            self.assertFalse((root/'sj/2').exists())
            trace = C.loads(returned['4.json'])['traceback']
            if missing == 'typing':
                failure = C.loads(returned['4.json'])
                self.assertEqual(failure['closure_entry'], 'boot_type_only')
                self.assertIn("cannot import name '_IntegralLike'", failure['exception_message'])
                self.assertGreater(len(failure['exception_message']), 120)
                self.assertIn(failure['exception_message'], trace)
                self.assertEqual(receipt['exception_message'], failure['exception_message'])
            else:
                self.assertIn('carrier_c1_canary',trace)
                self.assertIn("No module named 'student_pilot.carrier_c1_canary'",trace)
            self.assertIn('/5.py',trace)
            self.assertEqual(receipt['bulk_bytes'],0)
        else:
            self.assertGreater(bulk_bytes,0)
            self.assertEqual((root/'sj/1').read_bytes(),b'bulk-zero')
            self.assertGreater(receipt['modules'],1000)
            self.assertIn('student_pilot.carrier_c1_canary',receipt['required_modules'])
            for name in ('fla', 'triton', 'causal_conv1d'):
                self.assertIn(name, receipt['required_modules'] if mode == 'g' else receipt['exclusions'])
            self.assertTrue((root/'18.log').exists())
            self.assertTrue((root/'p/a/18.log').exists())
        EVIDENCE.append(dict(mode=mode,missing=missing,bulk_bytes=bulk_bytes,boot=receipt,
            seconds=time.monotonic()-started,real_fetch=True,real_launch=True,
            missing_module=('boot_type_only' if missing == 'typing' else 'student_pilot.carrier_c1_canary') if missing else None,
            cuda_extension_doubles=['fla','triton','causal_conv1d'] if mode == 'g' and not missing else [],
            namespace='production constructor with read-only local interpreter/package fixture binds'))

    def test_type_only_import_failure(self): self.exercise('c','typing')

    def test_cpu_success(self): self.exercise('c',False)
    def test_gpu_success(self): self.exercise('g',False)
    def test_cpu_missing_module(self): self.exercise('c',True)
    def test_gpu_missing_module(self): self.exercise('g',True)


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Boot))
    (ROOT/'out/BOOT_CHECKS.json').write_text(json.dumps(dict(passed=result.wasSuccessful(),
        tests=result.testsRun,delivery=B.pin((ROOT/'out/delivery.tgz').read_bytes()),
        cases=EVIDENCE),indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
