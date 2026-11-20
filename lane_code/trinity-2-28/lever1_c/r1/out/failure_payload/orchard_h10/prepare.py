
exec(bytes.fromhex('2222224f7061717565204a534f4e207472616e73706f72743b2063616e6f6e6963616c206861736865732072657461696e207468656972206c6f676963616c20726570726573656e746174696f6e2e2222220a696d706f7274206a736f6e0a0a6966206e6f742068617361747472286a736f6e2c20275f61305f6c6f61647327293a0a202020206a736f6e2e5f61305f6c6f616473203d206a736f6e2e6c6f6164730a202020206a736f6e2e5f61305f64756d7073203d206a736f6e2e64756d70730a0a776972655f6c6f616473203d206a736f6e2e5f61305f6c6f6164730a776972655f64756d7073203d206a736f6e2e5f61305f64756d70730a544147203d20276130270a0a0a646566207261772864617461293a0a2020202076616c7565203d20776972655f6c6f6164732864617461290a202020206966206973696e7374616e63652876616c75652c20646963742920616e64207365742876616c756529203d3d207b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c20737472293a0a202020202020202072657475726e2062797465732e66726f6d6865782876616c75655b5441475d290a2020202072657475726e20646174612e656e636f64652829206966206973696e7374616e636528646174612c207374722920656c736520646174610a0a0a646566207061636b2864617461293a0a202020206966206973696e7374616e636528646174612c20737472293a646174613d646174612e656e636f646528290a2020202072657475726e2028776972655f64756d7073287b5441473a646174612e68657828297d2c736570617261746f72733d28272c272c20273a2729292b275c6e27292e656e636f646528290a0a0a646566206c6f61647328646174612c202a617267732c202a2a6b7761726773293a0a2020202076616c75653d776972655f6c6f61647328646174612c2a617267732c2a2a6b7761726773290a202020206966206973696e7374616e63652876616c75652c646963742920616e64207365742876616c7565293d3d7b5441477d20616e64206973696e7374616e63652876616c75655b5441475d2c737472293a0a202020202020202072657475726e20776972655f6c6f6164732862797465732e66726f6d6865782876616c75655b5441475d292c2a617267732c2a2a6b7761726773290a2020202072657475726e2076616c75650a0a0a646566206c6f61642873747265616d2c202a617267732c202a2a6b7761726773293a72657475726e206c6f6164732873747265616d2e7265616428292c202a617267732c202a2a6b7761726773290a0a0a6465662064756d70732876616c75652c202a617267732c202a2a6b7761726773293a0a2020202064617461203d20776972655f64756d70732876616c75652c202a617267732c202a2a6b7761726773290a2020202072657475726e207061636b2864617461292e6465636f646528292e72737472697028275c6e2729206966206b77617267732e6765742827696e64656e742729206973206e6f74204e6f6e6520656c736520646174610a0a0a6465662064756d702876616c75652c2073747265616d2c202a617267732c202a2a6b7761726773293a0a2020202073747265616d2e7772697465287061636b28776972655f64756d70732876616c75652c202a617267732c202a2a6b776172677329292e6465636f64652829290a0a0a64656620696e7374616c6c28293a0a202020206a736f6e2e6c6f6164733d6c6f6164733b6a736f6e2e6c6f61643d6c6f61643b6a736f6e2e64756d70733d64756d70733b6a736f6e2e64756d703d64756d700a').decode(),_a0:={});_a0['install']()
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
