"""Exercise the staging controller with local archives and native validators."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import subprocess

import job_support as H
import stage_job as D

def run(root):
    root = Path(root)
    objects, stage = root / 'objects', root / 'stage'
    objects.mkdir(parents=True)
    stage.mkdir()
    S, R, NS, J = H.native()
    pins = {}
    def tar(name, files, links=None, modes=None):
        path = objects / (name + '.tar')
        inventory = {}
        with tarfile.open(path, 'w') as archive:
            for filename, raw in files.items():
                entry = tarfile.TarInfo(filename)
                entry.size, entry.mode = len(raw), (modes or {}).get(filename, 0o644)
                archive.addfile(entry, io.BytesIO(raw))
                inventory[filename] = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            for filename, target in (links or {}).items():
                entry = tarfile.TarInfo(filename)
                entry.type, entry.linkname = tarfile.SYMTYPE, target
                archive.addfile(entry)
        pin = dict(name='q8/a/' + name + '.tar', generation='1', path=str(path),
                   sha256=H.sha(path), bytes=path.stat().st_size, members=inventory)
        pins[pin['name']] = pin
        return pin
    export = tar('a0', {'m544/artifact.json': b'{}'})
    anchors = tar('a1', {'00/a.png': b'fixture'})
    metadata = tar('a2', {'fsw/a.json': b'{}'})
    model = dict(root='/scratch/jjyeung/a09', files={'a.txt':hashlib.sha256(b'base').hexdigest()})
    model_raw = json.dumps(model).encode()
    model_pin = dict(path='/scratch/jjyeung/a08.json', sha256=hashlib.sha256(model_raw).hexdigest())
    model_tar = tar('a3', {'sj/a08.json': model_raw})
    fla_files = {'fla/__init__.py':b'', 'triton/__init__.py':b'', 'triton/backends/nvidia/bin/ptxas':b'fixture'}
    fla_manifest = ''.join(hashlib.sha256(raw).hexdigest() + '  ' + name + '\n' for name,raw in fla_files.items()).encode()
    code = tar('a4', {'sj/a10/a.py':b'', 'sj/a11/sitecustomize.py':b'pass\n', 'sj/a12.sha':fla_manifest})
    base = tar('a5', {'a/b/c/a.txt':b'base'})
    base.pop('members')
    runtime_files = {NS.RUNTIME + '/lib/python3.12/site-packages/' + name + '/__init__.py':b''
                     for name in ('scipy','torch','transformers','PIL')}
    runtime = tar('a6', runtime_files, {NS.RUNTIME + '/bin/python':'/usr/bin/python3'})
    numpy = tar('a7', {'numpy/__init__.py':b''})
    closure = tar('a8', {'a.py':b''})
    trainer = tar('a9', {'student_pilot/a.py':b''})
    fla = tar('aa', {'ebe69df8/p/' + k:v for k,v in fla_files.items()},
              modes={'ebe69df8/p/triton/backends/nvidia/bin/ptxas':0o755})
    executable = objects / 'a.bin'
    executable.write_bytes(b'fixture')
    bwrap = dict(path=str(executable), bytes=7, sha256=H.sha(executable))
    depth_raw = b'{"schema": "rh-depth-fixture"}\n'
    depth_file = objects / 'd.json'
    depth_file.write_bytes(depth_raw)
    depth = [dict(path=str(depth_file), bytes=len(depth_raw), sha256=hashlib.sha256(depth_raw).hexdigest(),
                  logical_path='/scratch/jjyeung/a17/step/heads.json')]
    assets = dict(small_objects=[{}, metadata, {}, model_tar], gcloud_config=str(objects),
                  model_manifest=model_pin, base=base, runtime=runtime, numpy=numpy, closure=closure,
                  trainer=trainer, tree_root='/scratch/jjyeung/a13', trainer_logical_archive='/scratch/jjyeung/a14.tar',
                  tree_sources={'student_pilot/a.py':hashlib.sha256(b'').hexdigest()},
                  bwrap=bwrap, depth=depth, fla=dict(path=fla['path'], bytes=fla['bytes'],
                    manifest=dict(path='/scratch/jjyeung/a12.sha',sha256=hashlib.sha256(fla_manifest).hexdigest())),
                  kit_import_root='/scratch/jjyeung/a10', aliases_root='/scratch/jjyeung/a11',
                  sitecustomize=dict(path='/scratch/jjyeung/a11/sitecustomize.py',sha256=hashlib.sha256(b'pass\n').hexdigest()),
                  worker_entrypoint=dict(path='/scratch/jjyeung/a.py',sha256='0'*64))
    config = dict(assets=assets, export=dict(parts=[export],sha256=export['sha256']),
                  anchors=anchors,code=code,export_destination='/scratch/jjyeung/a15',
                  logical_run='/scratch/jjyeung/a16', pool=str(root / 'pool'), pointer=str(root / 'pool/a.json'))
    (stage / 'phase_worker.py').write_text('pass\n')
    old, old_run = NS.cloud, subprocess.run
    NS.cloud = lambda record, root, assets: Path(pins[record['name']]['path']).open('rb')
    def describe(command, **kwargs):
        assert command[:4] == ['/usr/bin/gcloud','storage','objects','describe']
        name, generation = command[4].removeprefix('gs://cmu-gpucloud-jjyeung/').rsplit('#',1)
        pin = pins[name]
        assert generation == pin['generation']
        return subprocess.CompletedProcess(command,0,json.dumps(dict(size=pin['bytes'],generation=generation)),'')
    subprocess.run = describe
    try:
        runtime_spec = D.stage(stage, config)
        NS.physical(stage, config['logical_run']).mkdir(parents=True)
        argv = D.namespace(stage, config)
        assert '--ro-bind' in argv and str(NS.physical(stage, config['logical_run'])) in argv
        assert set(runtime_spec['imports']) == {'numpy','scipy','torch','transformers','triton','fla','PIL'}
        assert (stage / 'sj/a09/a.txt').read_bytes() == b'base'
        assert (stage / 'sj/a17/step/heads.json').read_bytes() == depth_raw
        return dict(passed=True, runtime_import_pins=len(runtime_spec['imports']), namespace_argv_constructed=True,
                    substitutions=['local object transport', 'tiny export/base/runtime contents', 'no runtime imports or GPU'],
                    records=json.loads((stage / 'a01.json').read_text()))
    finally:
        NS.cloud = old
        subprocess.run = old_run
