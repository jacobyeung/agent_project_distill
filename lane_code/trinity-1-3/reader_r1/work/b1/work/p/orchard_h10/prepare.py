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
    from parity_kit.stage_restore import stage
    from parity_kit.build_manifest import build
    from parity_kit.common import META, PREP, REQUEST
    f=inputs['files']; path=lambda name:Path(f[name]['path'])
    receipt=json.loads(path(inputs['environment_receipt']).read_text())
    versions={m.__name__:m.__version__ for m in (torch,torchvision,transformers,scipy)}
    if receipt.get('versions')!=versions:raise ValueError('Environment versions differ from staged receipt')
    write(d/'ENVIRONMENT.json',dict(versions=versions,python=sys.executable))
    # Each file was authenticated against INPUTS before entering the namespace.
    export=d/'e'; binding=d/'binding.json'
    stage(path('full_weights').parent,path('artifact').parent,META,export,
          request=REQUEST,tree=p/'tree',base_assets=path('base_config').parent,
          model_manifest_tar=path('original_model'))
    sam=dict(source_root=str(path('sam_receipt').parent/'source'),
             checkpoint_path=str(path('sam_checkpoint')),receipt_path=str(path('sam_receipt')))
    # The source tree has its own explicit logical path; never infer a host path.
    sam['source_root']=inputs['sam_source']
    code=dict(reader=b/'e2e_reader',heads=b/'heads',tree=p/'tree',sam3_source=Path(sam['source_root']),
              evaluator=p/'h1eval',rows=p/'rows',runner=b/'parity_kit')
    manifest=build(Path(config['logical']),export,path('g3t_weights').parent,
                   selector_head=path('selector_config').parent,sam3=sam,code_roots=code)
    write(d/'manifest.json',manifest)
    write(binding,dict(root=config['logical'],name='d/manifest.json',sha256=sha(d/'manifest.json'),
                       code_roots={k:str(v) for k,v in code.items()}))
    settings=dict(export_dir=str(export),artifact_manifest=str(binding),tree=str(p/'tree'),
        config=str(META/PREP/'config.json'),frames_root=inputs['frames_root'],
        selector_head=str(path('selector_config').parent),sam3=sam,
        env_roots=inputs.get('env_roots',[]),arm='own_depth',
        stage1_select_rule=config.get('stage1_select_rule','null_argmax'),
        save_own_depth=config.get('save_own_depth',True))
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
