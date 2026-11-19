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
        if value.get('encoding') in ('base64', 'base64-json'):
            if set(value) != {'encoding','payload','sha256'}:
                raise ValueError('Unexpected capsule fields')
            raw = base64.b64decode(value['payload'], validate=True)
            if hashlib.sha256(raw).hexdigest() != value['sha256']:
                raise ValueError('Invalid content capsule')
            return
        for key, item in value.items():
            if bad_string(key, hashes):
                raise ValueError('Forbidden JSON field')
            scan_value(item, hashes, key)
    elif isinstance(value, list):
        for item in value:
            scan_value(item, hashes, field)
    elif isinstance(value, str):
        if (value.startswith(('/scratch/','/home/','/data','/project/','/lustre/'))
                or Path(value).is_absolute() or '..' in Path(value).parts or bad_string(value, hashes)):
            raise ValueError('Non-opaque or absolute operational string')


def scan(root):
    root = Path(root)
    hashes = load(root/'b/wh.json')
    for path in root.rglob('*'):
        relative = str(path.relative_to(root))
        if path.is_symlink() or bad_string(relative, hashes):
            raise ValueError('Forbidden staged path')
        if path.is_file():
            with path.open('rb') as handle:
                prefix = handle.read(128).lstrip()
            if path.suffix == '.json' or prefix.startswith((b'{', b'[')):
                scan_value(json.loads(path.read_text()), hashes)
    job = (root/'job.sh').read_text()
    for value in re.findall(r'^(?:export\s+\w+=|#SBATCH --(?:job-name|output|error)=)(.*)$', job, re.M):
        if bad_string(value, hashes):
            raise ValueError('Forbidden job argument or environment value')
    for script in [root/'job.sh', *sorted((root/'b').glob('*.sh'))]:
        for line in script.read_text().splitlines():
            if line.startswith('#') and not line.startswith('#SBATCH'):
                continue
            if bad_string(line, hashes):
                raise ValueError('Forbidden job path, argument or environment value')
            if script.name == 'f.sh' and re.search(r'--(?:gpus|gres)\b', line):
                raise ValueError('GPU request refused by CPU job')
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
        if previous is None:
            sys.modules.pop('v', None)
        else:
            sys.modules['v'] = previous
    scan(root)
    return sha256(root/'SHA256SUMS.txt')


def build(base, output, *, connector=None, records=None, dense_manifest=None, bindings=None, overrides=True, init_pin=None):
    """Stage from empty. Missing evidence is represented explicitly, never invented."""
    base, output = Path(base), Path(output)
    if not overrides:
        from .parent import reproduce
        return reproduce(base, output)
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
        return put_bytes(capsule_json(value))

    def capsule(path):
        raw = Path(path).read_bytes()
        return put(dict(sha256=hashlib.sha256(raw).hexdigest(), encoding='base64', payload=base64.b64encode(raw).decode()))

    for role, path in sorted(records.items()):
        pins[role] = capsule(path)
    from student_pilot.p3_provenance import pinned
    if not init_pin:
        raise ValueError('Missing pinned init selection')
    pins['init_selection'] = capsule(pinned(init_pin))
    withheld_raw = Path(records['withheld']).read_bytes()
    if hashlib.sha256(withheld_raw).hexdigest() != WITHHELD_SHA256:
        raise ValueError('Foreign withheld list')
    if sha256(TREE/'student_pilot/trace_grammar.py') != SHARED_SHA256:
        raise ValueError('Shared grammar differs')
    cfg = load(base/'k/b02e4385.json')
    cfg = configure(cfg, connector, dense_manifest=dense_manifest, init_pin=init_pin)
    cfg = relocate(cfg, paths)
    cfg['dev_scene_exclusions'] = dict(path='u/'+sha256(TREE/'student_pilot/r2_dev_merged.json'), sha256=sha256(TREE/'student_pilot/r2_dev_merged.json'))
    cfg['benchmark_scene_exclusions'] = dict(path='u/'+sha256(base/'k/benchmark_scene_exclusions.json'), sha256=sha256(base/'k/benchmark_scene_exclusions.json'))
    cfg['r2_all_stream_exclusions'] = True
    cfg['scene_coverage'] = None
    cfg['r2_scene_rebuild'] = None
    # The parent source archive keeps native import semantics behind an opaque name.
    files = tree_files(TREE)
    from student_pilot.source_seal import archive, check_archive
    archive_name = 'k/t_'+digest(files)[:16]+'.tar'
    archive(TREE, output/archive_name, files, compress=True)
    archive_pin = dict(path=archive_name, sha256=sha256(output/archive_name))
    check_archive({**archive_pin, 'path':str(output/archive_name)}, files)
    source_pin = put(dict(tree_sha256=digest(files), files=files, archive=archive_pin))
    from student_pilot.p3_provenance import source_files
    sources = {str(p.relative_to(TREE)):sha256(p) for p in source_files([TREE/'student_pilot/carrier_c1_run.py'])}
    code = dict(schema='c1-sealed-source-v1', commit='sha256:'+digest(files),
                tree_sha256=digest(files), files=files, archive=archive_pin,
                sources=sources, operation_sources=sources)
    (output/'k/7.json').write_bytes(capsule_json(code))
    registry = put(slots())
    mix = put(table())
    fallback = put(table(True))
    if bindings:
        from .closure import transport
        from student_pilot.r2_mix import preflight, validate_table
        from student_pilot.r2_policy import components
        def transport_bytes(raw, suffix):
            return put_bytes(capsule_json(json.loads(raw)), suffix) if suffix == '.json' else put_bytes(raw,suffix)
        portable, translations = transport(bindings, transport_bytes)
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
    cfg['code'] = dict(path='k/7.json', sha256=sha256(output/'k/7.json'))
    cfg['s1_route_policy'] = dict(name='frozen-table-no-flag-v1', table=put(cfg['route_table']))
    if 'indices' in portable:
        if not {'mix', 'counts'} <= set(portable):
            raise ValueError('Reader indices require mix and population bindings')
        cfg['r2_sampling'] = {k:v for k,v in portable.items() if k in ('mix','counts','indices','source_presence')}
        cfg['r2_sampling']['portable'] = True
    cfg['init_artifact'] = dict(artifact=dict(path='u/'+cfg['r2_identity']['init']['artifact_sha256'],
                                            sha256=cfg['r2_identity']['init']['artifact_sha256']),
                                heads=['pose','depth','frame_embeddings'], lm='full')
    from .plan import make
    cfg['output'] = 'runs/'+digest(cfg)[:8]
    cfg['preparation_output'] = 'o/'+digest(cfg)[:8]
    cfg['r2_persistence'] = dict(sessions=None, uploader=dict(path='b/gcsput.py',sha256=sha256(TREE/'launch_s1/b/gcsput.py')))
    staging_pin = put(make(cfg, paths, base))
    from student_pilot.r2_policy import seal_catalog, CHOICES
    cfg['r2_evaluation'] = dict(catalog=put(seal_catalog({})), choices=list(CHOICES), camera_routing=False,
                                prereg=None, freeze=None)
    cfg['output'] = 'runs/'+digest(cfg)[:8]
    cfg['preparation_output'] = 'o/'+digest(cfg)[:8]
    cfg_pin = put(cfg)
    identity = put(dict(config=cfg_pin, source=source_pin, records=pins, registry=registry, mix=mix,
                        staging=staging_pin, source_sha256=digest(files), site=SITE,
                        disclosure=cfg['r2_identity'], admission=False))
    for name in ('a.py','v.py','opaque.py','wh.json'):
        (output/'b'/name).write_bytes((TREE/'launch_s1/b'/name).read_bytes())
    (output/'b/e.py').write_bytes((TREE/'launch_r2/bootstrap.py').read_bytes())
    (output/'b/s.py').write_bytes((TREE/'launch_r2/staging.py').read_bytes())
    (output/'b/l.py').write_bytes((TREE/'launch_r2/bootstrap.py').read_bytes())
    (output/'b/q.py').write_bytes((TREE/'launch_r2/stdlib_probe.py').read_bytes())
    (output/'b/gcsput.py').write_bytes((TREE/'launch_s1/b/gcsput.py').read_bytes())
    (output/'b/w.py').write_bytes((TREE/'launch_r2/worker.py').read_bytes())
    job_name = 'a15_cot_ap'+digest(dict(config=cfg_pin, identity=identity))[:12]
    job = '#!/bin/bash\n#SBATCH --partition=advanced\n#SBATCH --nodes=1\n#SBATCH --gpus-per-node=4\n'
    job += '#SBATCH --cpus-per-task=48\n#SBATCH --mem=800G\n#SBATCH --time=24:00:00\n#SBATCH --no-requeue\n'
    job += '#SBATCH --job-name='+job_name+'\n#SBATCH --output=o/%j.out\n#SBATCH --error=o/%j.err\n'
    job += '#SBATCH --signal=B:USR1@3600\nset -euo pipefail\nexport TK_JOB_START="${TK_JOB_START:-$(date +%s)}"\n/usr/bin/python3 -I -s -B b/s.py . t &\np=$!\nc=0\ntrap \'kill -USR1 "$p"\' USR1\nwhile kill -0 "$p" 2>/dev/null; do wait "$p" && break || c=$?; done\nexit "$c"\n'
    (output/'job.sh').write_text(job)
    cpu_job = '#!/bin/bash\n#SBATCH --partition=general\n#SBATCH --nodes=1\n#SBATCH --cpus-per-task=8\n'
    cpu_job += '#SBATCH --mem=800G\n#SBATCH --time=06:00:00\n#SBATCH --no-requeue\n'
    cpu_job += '#SBATCH --job-name='+job_name+'\n#SBATCH --output=o/%j.out\n#SBATCH --error=o/%j.err\n'
    cpu_job += 'set -euo pipefail\nmkdir -p o/ee000003\n'
    cpu_job += '[[ "${SLURM_GPUS_ON_NODE:-0}" == 0 && "${SLURM_GPUS:-0}" == 0 && "${SLURM_JOB_GPUS:-0}" == 0 && "${SLURM_GPUS_PER_NODE:-0}" == 0 && -z "${CUDA_VISIBLE_DEVICES:-}" ]] || exit 2\n'
    cpu_job += 'env -i PATH=/usr/bin:/bin OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -I -s -B b/s.py . h 2>&1 | /usr/bin/python3 -I b/opaque.py\n'
    (output/'b/f.sh').write_text(cpu_job)
    zero = dict(commit='sha256:'+digest(files), trainer=dict(file=archive_name, sha256=archive_pin['sha256']),
                record=dict(file=identity['path'], sha256=identity['sha256']),
                extra=relocate(pose, paths), staging=staging_pin)
    (output/'k/0.json').write_text(json.dumps(zero,sort_keys=True)+'\n')
    (output/'k/1.json').write_text(json.dumps({'0':Path(cfg_pin['path']).stem})+'\n')
    authorization = dict(production_go_granted=False, go=False, config_sha256=cfg_pin['sha256'],
        source_revision='sha256:'+digest(files), admission=False, modes=['t','u'],
        allow_until_utc='1970-01-01T00:00:00Z', conditions=[])
    (output/'k/4.json').write_text(json.dumps(authorization)+'\n')
    launch = dict(schema='r2-production-launch-v1', config=dict(file=cfg_pin['path'],sha256=cfg_pin['sha256']),
                  source_revision=zero['commit'], source=source_pin, inputs=None,
                  prepared=None,
                  production_authorized=False, modes=authorization['modes'],
                  missing=['component evidence', 'post-filter counts', 'frame-host input inventory', 'independent review'])
    (output/'k/launch.json').write_text(json.dumps(launch)+'\n')
    from .host import ESTIMATES, LIMITS
    (output/'k/f.json').write_text(json.dumps(dict(schema='r2-frame-host-packet-v1',
        manifests=None,pose_sources=None,configuration=cfg_pin,pose_template=None,real_proof=None,counts=None,
        dense=None,init_archive=None,init_members=None,init_member_limit=None,scene_rebuild=None,
        checks=dict(roundtrip=None,bank_files=None), required_checks=[1,2,4,5,9,11],
        output='o/ee000004',wall_seconds=21600,idle_seconds=1200,limits=LIMITS,
        estimates=ESTIMATES,estimates_source='user build brief',
        boundary='CPU tensors before model forward',production_authorized=False))+'\n')
    launch['inputs'] = dict(path='k/f.json',sha256=sha256(output/'k/f.json'))
    (output/'k/launch.json').write_text(json.dumps(launch)+'\n')
    # Wrap fixed-name records too; all visible JSON keys and values are scanned.
    for name in ('0.json','4.json','f.json','launch.json'):
        p = output/'k'/name
        p.write_bytes(capsule_json(json.loads(p.read_text())))
    launch['inputs']['sha256'] = sha256(output/'k/f.json')
    (output/'k/launch.json').write_bytes(capsule_json(launch))
    manifest = {str(p.relative_to(output)):sha256(p) for d in ('b','k') for p in (output/d).rglob('*') if p.is_file()}
    manifest['job.sh'] = sha256(output/'job.sh')
    (output/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sorted(manifest.items())))
    scan(output)
    cert = dict(status='CLEAN',hits=0,manifest_sha256=sha256(output/'SHA256SUMS.txt'),
                scope='all visible records and names', external=[])
    (output/'ANON_OK.json').write_text(json.dumps(cert)+'\n')
    result = dict(schema='r2-kit-v1', config=cfg_pin, identity=identity, kit_sha256=verify(output),
                  bytes=sum(p.stat().st_size for p in output.rglob('*') if p.is_file()),
                  target_site=SITE, source_sha256=digest(files), job_name=job_name, admission=False,
                  blockers=['component evidence', 'post-filter counts', 'host admission', 'independent review'],
                  provenance={role:sha256(path) for role,path in records.items()})
    (output/'BUILD.json').write_bytes(capsule_json(result))
    return result


def capsule_json(value):
    raw = (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    return (json.dumps(dict(encoding='base64-json', sha256=hashlib.sha256(raw).hexdigest(),
                            payload=base64.b64encode(raw).decode()))+'\n').encode()
