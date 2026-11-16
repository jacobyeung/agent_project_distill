"""Validate immutable operation inputs before staging and dispatch."""
import json
from pathlib import Path
import re
from v import checked, sha

def binding(value):
    if (not isinstance(value,dict) or set(value)!={'path','sha256'}
            or not isinstance(value['path'],str) or not value['path'].startswith('/')
            or not isinstance(value['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',value['sha256'])):
        raise ValueError('Missing binding')
    return value

def ready(cfg, mode, auth):
    if cfg.get('training_mode')!='final': return
    if mode not in ('j','p','t','u','e','n','x','c'): raise ValueError('Operation not supported')
    if mode in ('p','t','u','e','n','x','c'):
        for key in ('pose','vqa','pointing','routing'): binding(cfg['streams'].get(key))
        binding(cfg.get('depth_init'))
        if cfg.get('unbound'): raise ValueError('Inputs unbound')
    if mode in ('t','u','e','n','x'):
        binding(cfg.get('preparation'))
    # Chained final-mode legs resume the run's newest complete state ('latest').
    if mode in ('u','x') and auth.get('resume')!='latest': binding(auth.get('resume'))
    if mode=='x' and not isinstance(auth.get('export_binding'),dict): raise ValueError('Export binding absent')
    if mode in ('e','n'): binding(auth.get('artifact'))
    if mode=='n': binding(auth.get('heldout'))

def routing_input(root, pin):
    spec=json.loads(checked(binding(pin)).read_text())
    return routing_spec(root,spec)

def routing_spec(root,spec):
    required={'source','rgb_index','division','processor','output'}
    optional={'allow_paired_anchor','direct_source','scene_role'}
    if not required<=set(spec) or set(spec)-required-optional:
        raise ValueError('Input fields differ')
    for field in ('source','rgb_index','division'): binding(spec[field])
    if spec.get('direct_source') is not None: binding(spec['direct_source'])
    if type(spec.get('allow_paired_anchor',False)) is not bool:
        raise ValueError('Invalid option')
    if spec.get('scene_role','train') not in ('train','heldout'):
        raise ValueError('Invalid selection')
    output=Path(spec['output'])
    if not output.is_absolute() or '..' in output.parts or not output.is_relative_to(root/'f') or output==root/'f':
        raise ValueError('Output leaves allocation')
    processor=Path(spec['processor'])
    if not processor.is_absolute() or '..' in processor.parts or not processor.is_relative_to(root/'models'):
        raise ValueError('Processor leaves allocation')
    return spec

def scanned(root, values):
    cert=json.loads((root/'ANON_OK.json').read_text())
    shipped={name:digest for digest,name in (line.split('  ',1) for line in (root/'SHA256SUMS.txt').read_text().splitlines())}
    for value in values:
        binding(value)
        path=Path(value['path'])
        internal=path.is_relative_to(root/'k') and shipped.get(str(path.relative_to(root)))==value['sha256']
        if value not in cert['external'] and not internal:
            # USER 11-08: record, never block, on missing input scans (data contents are not names/paths).
            print(json.dumps({'warning': 'input scan absent', 'path': value['path']}), flush=True)
            continue
        checked(value)

def operation_code(root):
    import os
    from student_pilot.p3_provenance import source_files
    trainer=Path(os.environ['TRAINER'])
    files=source_files([trainer/'student_pilot/carrier_c1_routing.py',trainer/'student_pilot/carrier_c1_canary.py'])
    actual={str(path.relative_to(trainer)):sha(path) for path in files}
    if json.loads((root/'k/7.json').read_text()).get('operation_sources')!=actual:
        raise ValueError('Operation source differs')
