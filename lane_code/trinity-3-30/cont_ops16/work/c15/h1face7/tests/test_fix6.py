"""Closed R1 admission, FIX5 reader/plan invariance, and registered manifest parity."""
import offline_guard
import copy
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import runpy
import shlex
import struct
import sys
import tarfile
import unittest
import uuid
from unittest.mock import patch
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'kit/launcher'))
import binding as B
import orchard_launcher as L
import export_stage as E
import orchard_stage as S


def folder():
    p = ROOT/'evidence'/('test_fix6_'+uuid.uuid4().hex)
    p.mkdir()
    return p


def load(p):
    return json.loads(Path(p).read_text())


def dump(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def canonical(value):
    return json.dumps(value, sort_keys=True).encode()


def identity(req, spec):
    cell = req['cells'][0]
    return dict(evaluator=req['source_sha256'], arm=spec['scope'], types=spec.get('types'),
                decoding={**{k:req[k] for k in ('max_tokens','temperature','thinking','max_model_len','engine_version')},
                          **{k:cell[k] for k in ('decoding','frames','layout')}, 'budget':2048})


def build_requests(cfg, root):
    """Execute real request builders; stop a7 immediately after request serialization.

    Export and frame admission are mocked here; their tests run separately. No engine
    or scores run. Full source membership supplies the synthetic manifest population.
    """
    sys.path.insert(0, str(ROOT/'kit/reader'))
    spec = importlib.util.spec_from_file_location('fix6_outer', ROOT/'kit/reader/worker.py')
    W = importlib.util.module_from_spec(spec); spec.loader.exec_module(W)
    import x7 as X
    runtime = ROOT/'readk/evidence/test_fix2_bind_main1000/a0/kit'
    actual = copy.deepcopy(cfg)
    actual['spec']['run'] = str(root/'requests')
    actual['spec']['artifact']['sha256'] = 'a'*64
    actual['spec']['models']['cp1m200'] = actual['spec']['artifact']
    result = {}; populations = {}
    if 'main' in cfg['families']:
        _, _, _, _, req, tasks, _ = W.bind(actual, 'main', root/'requests/main', reader=ROOT/'kit/reader', kit=runtime)
        if 'types' in cfg['spec']: req['types'] = cfg['spec']['types']
        result['main'] = req
        populations['main'] = W.F.select(tasks, cfg['spec'])
    if 'a7' in cfg['families']:
        sys.path.insert(0, str(ROOT/'kit/reader/out'))
        import direct
        sys.path.insert(0, str(runtime/'evaluator'))
        import scoring, data
        rows = [json.loads(line) for line in (ROOT/'assets/e52a690b.jsonl').read_text().splitlines()]
        X.validate_items(rows, cfg['extra'])
        class Captured(Exception): pass
        original_dump = X.dump
        def capture(path, value):
            original_dump(path, value)
            if Path(path).name == 'request.json':
                result['a7'] = value
                raise Captured
        def assets(reg, work):
            work.mkdir(parents=True)
            return rows, work/'unused_frames'
        with patch.object(X, 'stage_assets', assets), patch.object(X, 'dump', capture), \
             patch.object(direct, 'check_export', return_value={'status':'VERIFIED'}), \
             patch.object(scoring, 'score_item', scoring.score_item), patch.object(data, 'tasks_for', data.tasks_for):
            try: X.run(actual, reader=ROOT/'kit/reader', runtime=runtime)
            except Captured: pass
            else: raise AssertionError('The actual a7 request was not captured')
        populations['a7'] = W.F.select(rows, cfg['spec'])
    return result, populations


def requests(cfg, root):
    import isolated_fixture as isolated
    reqs = {}; populations = {}
    for family in cfg['families']:
        child = root/family; child.mkdir(parents=True)
        local = copy.deepcopy(cfg); local['families'] = [family]
        dump(child/'input.json', local)
        wrapper = child/'vllm_isolated.sh'
        wrapper.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' -I "$@"\n')
        wrapper.chmod(0o700)
        script = child/'capture.py'
        script.write_text('import sys\nfrom pathlib import Path\nsys.path.insert(0, '+repr(str(ROOT/'tests'))+')\n'
            'from test_fix6 import load, dump, build_requests\n'
            'root = Path('+repr(str(child))+')\n'
            'requests, populations = build_requests(load(root/"input.json"), root)\n'
            'dump(root/"output.json", dict(requests=requests, populations=populations))\n')
        result = isolated.launch(child, wrapper, 'import', script)
        if result.returncode: raise AssertionError(result.stdout+result.stderr)
        result = load(child/'output.json')
        reqs.update(result['requests']); populations.update(result['populations'])
    return reqs, populations


class R1Tests(unittest.TestCase):
    def test_all_74_reader_pins_equal_fix5(self):
        p = ROOT/'evidence/FIX6_BEFORE_PINS.json'
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(), 'f8911c19041a6bdb3bdf4734e2841a96fd7364675f202ddd0efabc5bc0d9203a')
        pins = {k:v for k,v in load(p).items() if k.startswith('kit/reader/')}
        self.assertEqual(len(pins), 74)
        actual = {str(p.relative_to(ROOT)) for p in (ROOT/'kit/reader').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(actual, set(pins))
        for name, digest in pins.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), digest, name)
        print('FIX6_READER_PINS 74/74 unchanged; no exception used', flush=True)

    def test_37_legacy_plans_equal_fix5_bytes_and_hashes(self):
        # str construction avoids the fixture runner's redirection of new test paths.
        base = Path(str(ROOT)+'/evidence/test_fix6_baseline')
        cases = load(base/'CASES.json')
        self.assertEqual(len(cases), 37)
        results = []
        for case in cases:
            old = load(Path(case['destination'])/'CONFIG.json')
            pins = load(ROOT/'evidence/FIX6_BEFORE_PINS.json')
            for name, digest in old['launcher_pins'].items():
                self.assertEqual(digest, pins['kit/launcher/'+name])
            new = L.prepare('a000000001', folder()/'prepared', **case['kwargs'])
            self.assertEqual(canonical(old['spec']), canonical(new['spec']))
            self.assertEqual(old['plan_sha256'], new['plan_sha256'])
            integrity = {'launcher_pins','launcher_review','launcher_review_pin'}
            self.assertEqual({k:v for k,v in old.items() if k not in integrity},
                             {k:v for k,v in new.items() if k not in integrity})
            results.append(dict(**case, plan_bytes=len(canonical(new['spec']))))
        print('FIX6_LEGACY '+json.dumps(results), flush=True)

    def test_closed_steps_generations_and_namespaces(self):
        for run, (low, high) in B.R1_RANGES.items():
            milestones = (100,200) if run == '673bc60f' else (400,600)
            for step in range(-1,802):
                for gen in (None, *B.STOPS, 'mstopD', 'm100', 'm400', ''):
                    allowed = step in milestones if gen is None else gen in B.STOPS and low <= step <= high and run != '6ed2c7aa'
                    if allowed:
                        bound = B.expected(run, step, gen)
                        self.assertEqual(B.validate(bound), bound)
                        raw = f"{bound['object']} 7 {'a'*64}\n".encode()
                        claim = f'm{step}\n'.encode() if gen else None
                        self.assertEqual(B.parse(raw, bound, claim)['bytes'], 7)
                        if gen:
                            for wrong in (None,b'm0\n',claim.rstrip(b'\n')):
                                with self.assertRaises(ValueError): B.parse(raw, bound, wrong)
                    else:
                        with self.assertRaises(ValueError): B.expected(run, step, gen)
            for step in (True,100.0,'100',None):
                with self.assertRaises(ValueError): B.expected(run, step)
            with self.assertRaises(ValueError): B.expected(run, milestones[0], namespace='other')
        for run in ('deadbeef','673bc60e','05b8ac68'):
            with self.assertRaises(ValueError): B.expected(run, 100)

    def test_family_gates_prepare_and_embedded_validation(self):
        for run, step in (('673bc60f',100),('05b8ac69',400)):
            for types in (None,'direct'):
                choices = [None, ['a7','main']]
                choices += [list(group) for size in range(1, 5)
                            for group in itertools.combinations(('main','away','forward','a7'), size)]
                for families in choices:
                    p = folder()/'prepared'
                    cfg = L.prepare('a000000001', p, step, run=run, families=families, types=types)
                    L.validate_request(cfg); L.validate_batch((p/'BATCH.sh').read_text(), cfg)
                    self.assertEqual(cfg['families'], ['main','away','forward','a7'] if families is None else families)
                for families in ([],['a7','a7'],['camera'],['unknown'],['main','unknown']):
                    dest = folder()/'refused'
                    with self.assertRaises(ValueError):
                        L.prepare('a000000001', dest, step, run=run, families=families, types=types)
                    self.assertFalse(dest.exists())
                    bad = copy.deepcopy(cfg); bad['families'] = bad['spec']['families'] = families
                    bad['plan_sha256'] = L.canonical(bad['spec'])
                    with self.assertRaises(ValueError): L.validate_request(bad)
            with self.assertRaises(ValueError):
                L.prepare('a000000001', folder()/'refused', step, run=run, families=['main'], types='other')

    def test_staging_lineage_and_closed_ranges(self):
        for run, (low,high) in B.R1_RANGES.items():
            for step in (low,high):
                path = str(L.J.FSW/f'ap/8865619b/runs/{run}/m{step}/artifact.json')
                self.assertEqual(E.logical_artifact(None,path,step),path)
                # Passing this gate reaches the completed-file check, never cloud IO.
                with patch.object(E.T,'writable',side_effect=Path), patch.object(E,'completed_local',side_effect=RuntimeError('passed gate')):
                    with self.assertRaisesRegex(RuntimeError,'passed gate'):
                        E.stage_export(NS(root=str(folder()),run=run,step=step,tar='unused'))
            for step in (low-1,high+1,0,800):
                path = str(L.J.FSW/f'ap/8865619b/runs/{run}/m{step}/artifact.json')
                with self.assertRaises(ValueError): E.logical_artifact(None,path,step)
                with patch.object(E.T,'writable',side_effect=Path), self.assertRaises(ValueError):
                    E.stage_export(NS(root=str(folder()),run=run,step=step))
        self.assertEqual(E.T.EXPORT_RUNS, ('359fcc3c','17c4ffa4'))

    def test_r1_full_checker_and_archive_admission(self):
        module = importlib.util.spec_from_file_location('fix6_checker', ROOT/'kit/reader/out/export_check.py')
        checker = importlib.util.module_from_spec(module); module.loader.exec_module(checker)
        for run, step, generation in (('673bc60f',100,None),('673bc60f',200,None),
                                      ('05b8ac69',400,None),('05b8ac69',600,None),
                                      ('673bc60f',137,'mstopB'),('05b8ac69',201,'mstopC')):
            root = folder(); job = root/'job'; base = root/'base'; base.mkdir()
            logical = str(L.J.FSW/f'ap/8865619b/runs/{run}/m{step}/artifact.json')
            physical = L.J.physical(job, logical)
            header = json.dumps({'weight':dict(dtype='BF16',shape=[1],data_offsets=[0,2])}).encode()
            shard = struct.pack('<Q',len(header))+header+b'00'
            (base/'model.safetensors').write_bytes(shard)
            index = canonical(dict(weight_map={'weight':'model.safetensors'}))
            sha = lambda raw: hashlib.sha256(raw).hexdigest()
            manifest = canonical(dict(schema='full-ft-export-v1',dtype='bfloat16',tensor_count=1,
                index=dict(name='model.safetensors.index.json',sha256=sha(index)),
                files=[dict(name='model.safetensors',bytes=len(shard),tensors=1,sha256=sha(shard))]))
            artifact = canonical(dict(schema='carrier-c1-artifact-v1',step=step,
                full_weights=dict(path=str(physical.parent/'full_weights/full_weights.json'),sha256=sha(manifest))))
            files = {'artifact.json':artifact,'heads.pt':b'fixture','full_weights/full_weights.json':manifest,
                     'full_weights/model.safetensors.index.json':index,'full_weights/model.safetensors':shard}
            archive = root/'input.tar'
            with tarfile.open(archive,'w') as tf:
                for name, raw in files.items():
                    member = tarfile.TarInfo(f'm{step}/'+name); member.size=len(raw); tf.addfile(member,io.BytesIO(raw))
            bound = B.expected(run,step,generation)
            done = root/'DONE.json'
            receipt = f"{bound['object']} {archive.stat().st_size} {S.sha(archive)}\n".encode()
            dump(done, B.parse(receipt,bound,f'm{step}\n'.encode() if generation else None))
            def check(root, path, digest, actual_step, full, receipt_dir, bwrap):
                self.assertTrue(full)
                return checker.check_export(L.J.physical(root,path),digest,base,actual_step)
            with patch.object(E.T,'writable',side_effect=Path), \
                 patch.object(E,'completed_local',side_effect=lambda p,tar=False:Path(p)), \
                 patch.object(S,'room'), patch.object(E,'run_export_checker',side_effect=check):
                result=E.stage_export(NS(root=str(job),run=run,step=step,tar=str(archive),done=str(done),full=True,bwrap='fixture'))
            self.assertEqual(result['checker']['status'],'VERIFIED')
            self.assertEqual(result['checker']['step'],step)
            self.assertEqual(result['artifact_sha256'],sha(artifact))

    def test_fixture_requests_and_manifest_configs_equal_registered_baselines(self):
        baseline = Path(str(ROOT)+'/evidence/test_fix6_baseline')
        cases = load(baseline/'CASES.json')
        old544 = load(Path(next(c['destination'] for c in cases if c['kwargs']['run']=='469ddece' and c['kwargs']['types']=='direct'))/'CONFIG.json')
        oldmain = load(Path(next(c['destination'] for c in cases if c['kwargs']['run']=='359fcc3c' and c['kwargs']['families']==['main'] and c['kwargs']['types']=='direct'))/'CONFIG.json')
        base_req, _ = requests(old544, folder())
        main_req, _ = requests(oldmain, folder())
        reference = {'a7':base_req['a7'], 'main':main_req['main']}
        for run, step in (('673bc60f',100),('673bc60f',200),('05b8ac69',400),('05b8ac69',600)):
            root = folder(); build = root/'prepared'
            argv = ['launcher','prepare','--run',run,'--namespace','8865619b','--step',str(step),
                    '--families','main','a7','--types','direct','--token','a000000001','--destination',str(build)]
            with patch.object(sys,'argv',argv): L.main()
            cfg = load(build/'CONFIG.json')
            for field in ('payload_pins','payload_sha256','extra','assets'):
                self.assertEqual(cfg[field], old544[field])
            self.assertEqual(cfg['spec']['scope'], old544['spec']['scope'])
            self.assertEqual(cfg['spec']['types'], old544['spec']['types'])
            reqs, populations = requests(cfg, root)
            for fam, req in reqs.items():
                self.assertEqual(identity(req,cfg['spec']),identity(reference[fam],old544['spec']))
                key = 'items_sha256' if fam=='a7' else 'datasets'
                self.assertEqual(req[key],reference[fam][key])
            # These are explicitly synthetic completion receipts, not inference results.
            x = build/'fetched/x'; spec = copy.deepcopy(cfg['spec']); spec['artifact']['sha256']='a'*64
            dump(build/'SUBMISSION.json',dict(job='fixture',token=cfg['token'],plan_sha256=cfg['plan_sha256']))
            dump(x/'SPEC.json',spec)
            dump(x/'COMPLETE.json',dict(step=step,plan_sha256=cfg['plan_sha256'],synthetic=True))
            records=[]
            for fam, req in reqs.items():
                dump(x/fam/'a0/request.json',req)
                records.extend(dict(family=fam,id=r['example_id'],task_type=r['question_type'],step=step,synthetic=True) for r in populations[fam])
            raw=''.join(json.dumps(r,sort_keys=True)+'\n' for r in records).encode()
            (x/'ITEMS.jsonl').write_bytes(raw)
            archive=build/'fetched/result.tar.gz'
            with tarfile.open(archive,'w:gz') as tf:
                member=tarfile.TarInfo('ITEMS.jsonl');member.size=len(raw);tf.addfile(member,io.BytesIO(raw))
            dump(build/'fetched/FETCH.json',dict(job='fixture',token=cfg['token'],status='COMPLETE',archive=dict(sha256=S.sha(archive))))
            for name, fam in (('R0-dev','a7'),('dev-S1','main')):
                out=build/(name+'_MANIFEST.json')
                tool=ROOT/'evidence/FIX6_build_manifest.py'
                with patch.object(sys,'argv',[str(tool),'kit',str(build),name,str(out)]):
                    runpy.run_path(str(tool),run_name='__main__')
                manifest=load(out); registered=load(ROOT/('evidence/FIX6_BASE_MANIFEST_'+name+'_544.json'))
                self.assertEqual(manifest['config'],registered['config'])
                self.assertEqual(manifest['type_filter'],'direct')
                print('FIX6_MANIFEST '+json.dumps(dict(run=run,step=step,set=name,build=str(build),
                    manifest=str(out),config_equal=True,type_filter=manifest['type_filter'],
                    baseline_type_filter=registered['type_filter'],items=len(populations[fam]),
                    identity=identity(reqs[fam],cfg['spec']),synthetic_receipts=True)),flush=True)


if __name__ == '__main__':
    unittest.main()
