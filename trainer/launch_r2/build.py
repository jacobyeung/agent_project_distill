"""Small, non-admitting Orchard kits with one authenticated content closure."""
import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re

from launch_s1.build import tree_files
from student_pilot.p3_provenance import digest, sha256, load
from student_pilot.r2_config import configure, SITE
from student_pilot.r2_grammar import SHARED_SHA256
from student_pilot.r2_policy import slots
from student_pilot.r2_withheld import SHA256 as WITHHELD_SHA256
from student_pilot.r2_mix import table

TREE = Path(__file__).resolve().parents[1]
WORDS = ('split', 'distill', 'revsi', 'vsi', 'vsibench', 'vsti', 'sti', 'mindcube',
         'scannet', 'arkit', 'qwen', 'qgen', 'gf1', 'geometry', 'benchmark', 'dataset',
         'student', 'teacher', 'trace', 'resti', 'sam3', 'g3t', 'vggt')


def bad_string(value, hashes):
    lowered = value.lower()
    if any(word in lowered for word in WORDS):
        return True
    h = lambda v: hashlib.sha256(v.encode()).hexdigest()
    for token in re.findall(r'[a-z0-9_]+', lowered):
        if h(token) in hashes['word']:
            return True
        for width, values in hashes['substr'].items():
            n = int(width)
            if any(h(token[i:i+n]) in values for i in range(len(token)-n+1)):
                return True
    return False


def scan_value(value, hashes, field=''):
    if isinstance(value, dict):
        for key, item in value.items():
            scan_value(item, hashes, key if field not in ('env','args','parts') else field)
    elif isinstance(value, list):
        for item in value:
            scan_value(item, hashes, field)
    elif isinstance(value, str):
        operational = field in ('path','file','dest','env','args','parts','job_name','output','preparation_output')
        if (value.startswith(('/scratch/','/home/','/data','/project/','/lustre/'))
                or operational and (Path(value).is_absolute() or '..' in Path(value).parts or bad_string(value, hashes))):
            raise ValueError('Non-opaque or absolute operational string')


def scan(root):
    root = Path(root)
    hashes = load(root/'b/wh.json')
    for path in root.rglob('*'):
        relative = str(path.relative_to(root))
        if path.is_symlink() or bad_string(relative, hashes):
            raise ValueError('Forbidden staged path')
        if path.is_file() and path.suffix == '.json':
            scan_value(load(path), hashes)
    job = (root/'job.sh').read_text()
    for value in re.findall(r'^(?:export\s+\w+=|#SBATCH --(?:job-name|output|error)=)(.*)$', job, re.M):
        if bad_string(value, hashes):
            raise ValueError('Forbidden job argument or environment value')
    return dict(status='CLEAN', hits=0)


def relocate(value, paths):
    """Relocate operational node paths; original bytes remain in provenance capsules."""
    if isinstance(value, dict):
        return {relocate(k,paths):relocate(v,paths) for k,v in value.items()}
    if isinstance(value, list):
        return [relocate(v,paths) for v in value]
    if isinstance(value, str) and value.startswith('/'):
        return paths.setdefault(value, 'u/'+hashlib.sha256(value.encode()).hexdigest())
    return value


def verify(root):
    root = Path(root)
    # Reuse the sealed leg's real byte/inventory verifier, with its dependency local.
    import sys
    spec = importlib.util.spec_from_file_location('r2_native_v', TREE/'launch_s1/b/v.py')
    v = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v)
    previous = sys.modules.get('v')
    sys.modules['v'] = v
    try:
        spec = importlib.util.spec_from_file_location('r2_native_a', TREE/'launch_s1/b/a.py')
        a = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(a)
        a.main(root, build_only=True)
    finally:
        sys.modules['v'] = previous
    scan(root)
    return sha256(root/'SHA256SUMS.txt')


def build(base, output, *, connector, records, dense_manifest=None, bindings=None):
    """Stage from empty. Missing evidence is represented explicitly, never invented."""
    base, output = Path(base), Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Kit must stage from empty')
    output.mkdir(parents=True, exist_ok=True)
    for name in ('b','k','o','runs'):
        (output/name).mkdir(exist_ok=True)
    paths, pins = {}, {}

    def put_bytes(raw, suffix='.json'):
        identity = hashlib.sha256(raw).hexdigest()
        relative = 'k/'+identity+suffix
        path = output/relative
        if not path.exists():
            path.write_bytes(raw)
        return dict(path=relative, sha256=identity)

    def put(value):
        return put_bytes((json.dumps(value, sort_keys=True, separators=(',',':'))+'\n').encode())

    def capsule(path):
        raw = Path(path).read_bytes()
        return put(dict(sha256=hashlib.sha256(raw).hexdigest(), encoding='base64', payload=base64.b64encode(raw).decode()))

    for role, path in sorted(records.items()):
        pins[role] = capsule(path)
    withheld_raw = Path(records['withheld']).read_bytes()
    if hashlib.sha256(withheld_raw).hexdigest() != WITHHELD_SHA256:
        raise ValueError('Foreign withheld list')
    if sha256(TREE/'student_pilot/trace_grammar.py') != SHARED_SHA256:
        raise ValueError('Shared grammar differs')
    cfg = load(base/'k/b02e4385.json')
    cfg = configure(cfg, connector, dense_manifest=dense_manifest)
    cfg = relocate(cfg, paths)
    # Source members use opaque names; module identities are labels, never job arguments.
    files = tree_files(TREE)
    source = {}
    for name, expected in files.items():
        raw = (TREE/name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Source changed during packaging')
        source[hashlib.sha256(name.encode()).hexdigest()] = put_bytes(raw, '.dat')
    source_pin = put(dict(tree_sha256=digest(files), files=source))
    registry = put(slots())
    mix = put(table())
    fallback = put(table(True))
    if bindings:
        from .closure import transport
        from student_pilot.r2_mix import preflight, validate_table
        from student_pilot.r2_policy import components
        portable, translations = transport(bindings, put_bytes)
        registry = portable.get('registry', registry)
        mix = portable.get('mix', mix)
        validate_table(load(output / mix['path']))
        components(registry, 'training', output)
        if 'counts' in portable:
            preflight(mix, portable['counts'], root=output, source_presence=portable.get('source_presence'))
        pins['transports'] = put(translations)
    else:
        portable = {}
    staged = relocate(load(base/'k/0.json'), paths)
    staging_pin = put(staged)
    pose = [entry for entry in load(base/'k/0.json')['extra']
            if re.search(r'/a[23]v[23]/(?:rows.sqlite|receipt.json|division.json)$', entry.get('dest',''))]
    if len([x for x in pose if x['dest'].endswith('/rows.sqlite')]) != 2:
        raise ValueError('Both sealed pose sources are required')
    pose_pin = put(relocate(pose, paths))
    if dense_manifest:
        pins['dense'] = capsule(dense_manifest['path'])
    cfg['r2_build2'] = dict(registry=registry, records=pins, mix=mix, fallback=fallback, pose_sources=pose_pin,
                           source=source_pin, target_site=SITE, admission=False)
    cfg['r2_build2'].update({k:v for k,v in portable.items() if k in ('counts', 'source_presence')})
    from student_pilot.r2_config import bind_mix
    cfg = bind_mix(cfg, load(output/mix['path']))
    cfg['s1_route_policy'] = dict(name='frozen-table-no-flag-v1', table=put(cfg['route_table']))
    if 'indices' in portable:
        if not {'mix', 'counts'} <= set(portable):
            raise ValueError('Reader indices require mix and population bindings')
        cfg['r2_sampling'] = {k:v for k,v in portable.items() if k in ('mix','counts','indices','source_presence')}
        cfg['r2_sampling']['portable'] = True
    cfg['init_artifact'] = dict(artifact=dict(path='u/'+cfg['r2_identity']['init']['artifact_sha256'],
                                            sha256=cfg['r2_identity']['init']['artifact_sha256']),
                                heads=['pose','depth','frame_embeddings'], lm='full')
    cfg['output'] = 'runs/'+digest(cfg)[:8]
    cfg['preparation_output'] = 'o/'+digest(cfg)[:8]
    cfg_pin = put(cfg)
    identity = put(dict(config=cfg_pin, source=source_pin, records=pins, registry=registry, mix=mix,
                        staging=staging_pin, source_sha256=digest(files), site=SITE,
                        disclosure=cfg['r2_identity'], admission=False))
    for name in ('a.py','v.py','opaque.py','wh.json'):
        (output/'b'/name).write_bytes((TREE/'launch_s1/b'/name).read_bytes())
    # Build 3 supplies the host admission and launch entry. This kit can only verify bytes.
    job_name = 'a15_cot_ap'+digest(dict(config=cfg_pin, identity=identity))[:12]
    job = '#!/bin/bash\n#SBATCH --partition=advanced\n#SBATCH --nodes=1\n#SBATCH --gpus-per-node=4\n'
    job += '#SBATCH --job-name='+job_name+'\n#SBATCH --output=o/%j.out\n#SBATCH --error=o/%j.err\n'
    job += 'set -euo pipefail\npython3 -B b/a.py . --build-only\nexit 1\n'
    (output/'job.sh').write_text(job)
    zero = dict(commit='sha256:'+digest(files), trainer=dict(file=source_pin['path'], sha256=source_pin['sha256']),
                record=dict(file=identity['path'], sha256=identity['sha256']),
                extra=relocate(pose, paths), staging=staging_pin)
    (output/'k/0.json').write_text(json.dumps(zero,sort_keys=True)+'\n')
    (output/'k/1.json').write_text(json.dumps({'0':Path(cfg_pin['path']).stem})+'\n')
    (output/'k/4.json').write_text(json.dumps(dict(modes=[], arm=['0'], admission=False))+'\n')
    manifest = {str(p.relative_to(output)):sha256(p) for d in ('b','k') for p in (output/d).rglob('*') if p.is_file()}
    manifest['job.sh'] = sha256(output/'job.sh')
    (output/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sorted(manifest.items())))
    scan(output)
    cert = dict(status='CLEAN',hits=0,manifest_sha256=sha256(output/'SHA256SUMS.txt'),
                scope='operational paths, arguments, environment and inventory', external=[])
    (output/'ANON_OK.json').write_text(json.dumps(cert)+'\n')
    result = dict(schema='r2-kit-v1', config=cfg_pin, identity=identity, kit_sha256=verify(output),
                  bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file()),
                  target_site=SITE, source_sha256=digest(files), job_name=job_name, admission=False,
                  blockers=['component evidence', 'post-filter counts', 'host admission', 'launch entry'],
                  provenance={role:sha256(path) for role,path in records.items()})
    (output/'BUILD.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
