
<<HEX 0>>
"""Opaque JSON transport; canonical hashes retain their logical representation."""
import json

if not hasattr(json, '_a0_loads'):
    json._a0_loads = json.loads
    json._a0_dumps = json.dumps

wire_loads = json._a0_loads
wire_dumps = json._a0_dumps
TAG = 'a0'


def raw(data):
    value = wire_loads(data)
    if isinstance(value, dict) and set(value) == {TAG} and isinstance(value[TAG], str):
        return bytes.fromhex(value[TAG])
    return data.encode() if isinstance(data, str) else data


def pack(data):
    if isinstance(data, str):data=data.encode()
    return (wire_dumps({TAG:data.hex()},separators=(',', ':'))+'\n').encode()


def loads(data, *args, **kwargs):
    value=wire_loads(data,*args,**kwargs)
    if isinstance(value,dict) and set(value)=={TAG} and isinstance(value[TAG],str):
        return wire_loads(bytes.fromhex(value[TAG]),*args,**kwargs)
    return value


def load(stream, *args, **kwargs):return loads(stream.read(), *args, **kwargs)


def dumps(value, *args, **kwargs):
    data = wire_dumps(value, *args, **kwargs)
    return pack(data).decode().rstrip('\n') if kwargs.get('indent') is not None else data


def dump(value, stream, *args, **kwargs):
    stream.write(pack(wire_dumps(value, *args, **kwargs)).decode())


def install():
    json.loads=loads;json.load=load;json.dumps=dumps;json.dump=dump

<</HEX>>
"""Prepare the reviewed restore inside the stable bwrap namespace, on CPU."""
import json
from pathlib import Path
import sys
from orchard_h10.common import sha, write


def run(config, inputs):
    import torch, torchvision, transformers, scipy
    from packaging.version import Version
    if Version(transformers.__version__) < Version('5.12'):
        raise ValueError('transformers >= 5.12 is required')
    p=Path(config['logical'])/'p'; b=p/'b'; d=Path(config['logical'])/'d'
    sys.path[:0]=[str(b),str(p/'tree')]
    from student_pilot.g3t_online import VENDOR, vendor_digest
    from student_pilot.tower_read import SOURCE_SHA256
    from student_pilot.c1r_ref import source_import
    if vendor_digest()!=SOURCE_SHA256:raise ValueError('E53')
    source_import(VENDOR)
    from parity_kit.stage_restore import stage
    from parity_kit.build_manifest import build
    from parity_kit.common import META, PREP, REQUEST
    f=inputs['files']; path=lambda name:Path(f[name]['path'])
    receipt=json.loads(path(inputs['environment_receipt']).read_text())
    versions={m.__name__:m.__version__ for m in (torch,torchvision,transformers,scipy)}
    if receipt.get('versions')!=versions:raise ValueError('Environment versions differ from staged receipt')
    write(d/'ENVIRONMENT.json',dict(versions=versions,python=sys.executable))
    pins=inputs['_export']
    from orchard_h10.export_pins import validate
    validate(pins)
    # The sealed D0 metadata also supplies the unchanged 544 input archives.
    bundled=dict(config=META/PREP/'config.json',receipt=META/PREP/'prepared/s1_receipt.json',
                 data_receipt=META/'fsw/ap/8865619b/runs/469ddece/inputs/data_receipt.json')
    for name,spec in pins['preparation'].items():
        dest=d/spec['path']
        if not dest.exists():
            src=bundled[name]
            if sha(src)!=spec['sha256'] or src.stat().st_size!=spec['bytes']:
                raise ValueError('Stage the pinned preparation file: '+name)
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open('xb') as stream:
                import j
                stream.write(j.pack(src.read_bytes()))
    write(d/'6.json',pins)
    # Each file was authenticated against INPUTS before entering the namespace.
    export=d/'e'; binding=d/'binding.json'
    stage(path('full_weights').parent,path('artifact').parent,META,export,
          request=REQUEST,tree=p/'tree',base_assets=path('base_config').parent,
          model_manifest_tar=path('original_model'),export_pins=pins,data_root=d)
    code=dict(reader=b/'e2e_reader',heads=b/'heads',tree=p/'tree',evaluator=p/'h1eval',runner=b/'parity_kit')
    manifest=build(Path(config['logical']),export,path('g3t_weights').parent,code_roots=code)
    write(d/'manifest.json',manifest)
    write(binding,dict(root=config['logical'],name='d/manifest.json',sha256=sha(d/'manifest.json'),
                       code_roots={k:str(v) for k,v in code.items()}))
    settings=dict(export_dir=str(export),artifact_manifest=str(binding),tree=str(p/'tree'),
        config=str(d/pins['preparation']['config']['path']),frames_root=inputs['frames_root'],
        capture_index=str(d/'9.json'),
        env_roots=inputs.get('env_roots',[]),arm='own_depth',
        stage1_select_rule=config.get('stage1_select_rule','null_argmax'),
        save_own_depth=config.get('save_own_depth',False),
        perception_memo=config.get('perception_memo','off'),
        perception_memo_modules=config['perception_memo_modules'],
        perception_memo_verify_ids=config.get('perception_memo_verify_ids',[]))
    if inputs.get('optional'):
        from h1eval.items import load_manifest
        from h1eval.h10.reserve_frames import captures
        spec=inputs['optional'];items=load_manifest(p/'items/r0dev.json')['items']
        bound=captures(items,spec['root'])
        # Verify every selected RGB once before publishing the admission receipt.
        for c in bound.values():
            for frame in c['frames']:
                if sha(Path(spec['root'])/frame['path'])!=frame['sha256']:raise ValueError('Optional RGB differs')
        settings['item_sets']={'r0dev_f32':dict(frames_root=spec['root'])}
        write(d/'8.json',dict(verified=True,archive_sha256=spec['sha256'],frames_manifest_sha256=load_manifest(p/'items/r0dev.json')['frames_manifest_sha256']))
    write(d/'settings.json',settings)
    write(d/'READY.json',dict(settings=sha(d/'settings.json'),binding=sha(binding),restore=sha(export/'RESTORE.json')))


if __name__=='__main__':run(*[json.loads(Path(p).read_text()) for p in sys.argv[1:3]])
