"""Pinned CPU preparation for the all-frame arm; never submits work."""
from collections import Counter
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import random
import resource
import shutil
import tarfile
import time

from . import recording_pose as rp


FIELDS = {'vsi288': 'b1', 'vsti': 'b2'}


def codec(value, reverse=False):
    mapping = {v: k for k, v in FIELDS.items()} if reverse else FIELDS
    if isinstance(value, dict):
        return {mapping.get(k, k): codec(v, reverse) for k, v in value.items()}
    if isinstance(value, list):
        return [codec(v, reverse) for v in value]
    return mapping.get(value, value) if isinstance(value, str) else value


def save(path, value):
    rp.write_new(path, rp.payload(codec(value)))
    return rp.pin(path)


def read(value):
    return codec(json.loads(rp.read_pin(value)), True)


def division(request, inherited):
    """Extend only training membership, with the inherited exclusions unchanged."""
    old = read(inherited)
    authorities = request['authorities']
    _, blocked = rp.load_authorities(authorities)
    index = read(request['recordings'])
    selected, excluded = [], []
    seen = set()
    for record in index['recordings']:
        dataset, scene = rp.identity(record['dataset'], record['scene'])
        if (dataset, scene) in seen:
            raise ValueError('Duplicate recording')
        seen.add((dataset, scene))
        reasons = [name for name, keys in blocked.items() if rp.exclusion_keys(dataset, scene) & keys]
        target = excluded if reasons else selected
        target.append(dict(dataset=dataset, scene=scene, reasons=reasons))
    extended = copy.deepcopy(old)
    new = {r['dataset']+'/'+rp.token(r['dataset'], r['scene']) for r in selected}
    extended['train_scenes'] = sorted({v for v in old['train_scenes'] if v.split('/')[0] in ('d1','d2','d3')} | new)
    extended['train_group_ids'] = sorted({v for v in old.get('train_group_ids', []) if v.split('/')[0] in ('d1','d2','d3')} | new)
    extended['a1_authority'] = dict(inherited=inherited, exclusions=authorities,
        policy='all eligible recordings; inherited heldout and exclusions unchanged')
    policy = read(authorities['admission_policy'])
    policy['allowed_groups'] = sorted(set(policy['allowed_groups']) | new)
    census = dict(schema='a1-division-census-v1', recordings=len(index['recordings']),
        admitted=dict(Counter(r['dataset'] for r in selected)), excluded=len(excluded),
        reasons=dict(Counter(reason for r in excluded for reason in r['reasons'])),
        exclusions=excluded, rows_per_scene=request['rows_per_scene'],
        inherited=inherited, heldout_unchanged=all(extended.get(k)==old.get(k)
            for k in ('heldout_scenes','heldout_group_ids','heldout_qids')))
    return extended, policy, census


def used_frames(source, plan):
    sampling = rp.sampling_settings(plan['sampling'])
    sampler = rp.sampler_for(source, sampling, plan['seed'])
    result = set()
    for index in range(plan['rows_per_scene']):
        rng = random.Random(f"{plan['seed']}:{source['dataset']}:{source['scene']}:{index}:{sampling['variant']}:{sampling['epoch']}")
        result.update(sampler.draw(rng, source['dataset'])[2])
    return sorted(result)


def index(spec):
    """Only this operation and alias creation may open the private real-path map."""
    pending, mapping = read(spec['pending']), read(spec['mapping'])
    archive = spec['archive']
    if rp.file_sha(archive['path']) != archive['sha256']:
        raise ValueError('Archive changed')
    result = []
    for original in pending['recordings']:
        record = copy.deepcopy(original)
        key = record['dataset']+'/'+record['scene']
        path = mapping.get(key, record['video']['path'])
        if not Path(path).is_absolute():
            raise ValueError('Absolute source required')
        path = str(Path(path).resolve())
        digest = rp.file_sha(path)
        if record['video'].get('sha256', digest) != digest:
            raise ValueError('Video changed')
        record['video'] = dict(path=path, sha256=digest)
        if record['poses']['sha256'] != archive['sha256']:
            raise ValueError('Pose archive changed')
        record['poses']['path'] = archive['path']
        result.append(record)
    return {'recordings': result}


def aliases(document, root):
    """Hardlink opaque names; cross-filesystem copies are serial and hash checked."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    result, cache, private = copy.deepcopy(document), {}, {}
    for record in result['recordings']:
        dataset, native = rp.identity(record['dataset'], record['scene'])
        record['dataset'] = dataset
        # Native scene values remain private JSON data, never command arguments.
        for kind in ('video', 'poses'):
            pin = record[kind]
            source = Path(pin['path']).resolve()
            key = str(source), pin['sha256']
            if key not in cache:
                if rp.file_sha(source) != pin['sha256']:
                    raise ValueError('Alias source changed')
                destination = root / pin['sha256']
                if destination.exists():
                    if rp.file_sha(destination) != pin['sha256']:
                        raise ValueError('Alias collision')
                else:
                    try:
                        os.link(source, destination)
                    except OSError as error:
                        import errno
                        if error.errno != errno.EXDEV:
                            raise
                        with source.open('rb') as src, destination.open('xb') as dst:
                            shutil.copyfileobj(src, dst, 1 << 20)
                if rp.file_sha(destination) != pin['sha256'] or destination.is_symlink():
                    raise ValueError('Alias differs')
                cache[key] = str(destination)
                private[str(destination)] = str(source)
            pin['path'] = cache[key]
    return result, private


def package(plan, staged, root, archive, manifest, a0_manifest=None, a0_archive=None, a0_rows=None):
    """One tar includes exactly row-used PNGs and all legacy A0 PNGs."""
    rp.validate_plan(plan)
    root = Path(root)
    frames = {}
    wanted = {(s['dataset'], s['scene']): set(used_frames(s, plan)) for s in plan['scenes']}
    seen, shards, total_shards = set(), set(), None
    for pin in staged:
        receipt = read(pin)
        if receipt.get('schema') != 'recording-pose-staged-v1' or receipt['shard'] in shards:
            raise ValueError('Invalid or duplicate frame receipt')
        if total_shards is not None and total_shards != receipt['shards']:
            raise ValueError('Frame shard count differs')
        total_shards = receipt['shards'];shards.add(receipt['shard'])
        for scene in receipt['scenes']:
            key = scene['dataset'], scene['scene']
            if key in seen or key not in wanted:
                raise ValueError('Invalid or duplicate frame scene')
            seen.add(key)
            if not wanted[key] <= {f['frame_number'] for f in scene['frames']}:
                raise ValueError('Missing row frames')
            for frame in scene['frames']:
                if frame['frame_number'] in wanted[(scene['dataset'], scene['scene'])]:
                    frames[frame['sha256']] = frame['path']
    if seen != set(wanted) or total_shards is None or shards != set(range(total_shards)):
        raise ValueError('Incomplete frame coverage')
    legacy = {}
    if a0_manifest:
        available = {f['sha256']: f for f in read(a0_manifest)}
        with Path(a0_rows['path']).open() as stream:
            if rp.file_sha(a0_rows['path']) != a0_rows['sha256']:
                raise ValueError('Legacy rows changed')
            for line in stream:
                for frame in json.loads(line)['student_input']['frames']:
                    if frame['sha256'] not in available:
                        raise ValueError('Legacy frame not in manifest')
                    legacy[frame['sha256']] = frame
        if rp.file_sha(a0_archive['path']) != a0_archive['sha256']:
            raise ValueError('Legacy frames archive changed')
    entries = []
    with tarfile.open(archive, 'x') as target:
        for digest, source in sorted(frames.items()):
            if rp.file_sha(source) != digest:
                raise ValueError('Frame changed')
            name = 'k3f8/'+digest[:2]+'/'+digest+'.png'
            target.add(source, arcname=name, recursive=False)
            entries.append(dict(path='/data2/'+name, sha256=digest))
        if legacy:
            found = set()
            with tarfile.open(a0_archive['path']) as source_tar:
                for member in source_tar:
                    digest = Path(member.name).stem
                    if digest not in legacy or digest in frames:
                        continue
                    expected = 'k3f8/'+digest[:2]+'/'+digest+'.png'
                    if member.name != expected or not member.isfile() or digest in found:
                        raise ValueError('Invalid legacy archive member')
                    raw = source_tar.extractfile(member).read()
                    if hashlib.sha256(raw).hexdigest() != digest:
                        raise ValueError('Legacy frame changed')
                    info = tarfile.TarInfo(expected); info.size = len(raw)
                    target.addfile(info, io.BytesIO(raw));found.add(digest)
                    entries.append(dict(path='/data2/'+expected,sha256=digest))
            if found != set(legacy)-set(frames):
                raise ValueError('Missing legacy frames')
    save(manifest, entries)
    return len(entries)


def mixed_rows(new_rows, a0, output, expected_a0=37952):
    """Keep A0 targets and identities byte-equivalent except content-addressed paths."""
    count, datasets, scenes, seen = 0, Counter(), set(), set()
    with Path(output).open('x') as dst:
        for source, legacy in ((Path(new_rows), False), (Path(a0), True)):
            n = 0
            with source.open() as stream:
                for line in stream:
                    row = json.loads(line)
                    if row['qid'] in seen:
                        raise ValueError('Mixed row id collision')
                    seen.add(row['qid'])
                    for frame in row['student_input']['frames']:
                        digest = frame['sha256']
                        frame['path'] = '/data2/k3f8/'+digest[:2]+'/'+digest+'.png'
                    from .pose_samples import manifest_line
                    dst.write(manifest_line(row)+'\n')
                    datasets[row['dataset']] += 1; scenes.add((row['dataset'],row['scene']))
                    count += 1; n += 1
            if legacy and n != expected_a0:
                raise ValueError('A0 census differs')
    return dict(rows=count, by_dataset=dict(datasets), scenes=len(scenes))


def run(spec):
    """Execute a pinned spec on a compute node and write a new measured receipt."""
    if not os.environ.get('SLURM_JOB_ID') or not os.environ.get('SLURMD_NODENAME'):
        raise ValueError('Compute allocation required')
    def cpu_time():
        return sum(getattr(resource.getrusage(who), field)
            for who in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN)
            for field in ('ru_utime','ru_stime'))
    start, cpu = time.monotonic(), cpu_time()
    operation = spec['operation']
    outputs, details = [], {}
    if operation in ('plan', 'frames', 'package'):
        details['decoder'] = rp.pyav_preflight()
    if operation == 'index':
        document = index(spec)
        outputs.append(save(spec['output'], document))
        os.chmod(spec['output'], 0o600)
        details['recordings'] = len(document['recordings'])
    elif operation == 'aliases':
        document, private = aliases(read(spec['index']), spec['root'])
        outputs.append(save(spec['output'], document))
        # This file is deliberately private and excluded from all later job specs.
        details.update(recordings=len(document['recordings']), aliases=len(private), private_map=save(spec['private'], private))
        os.chmod(spec['private'], 0o600)
        details['alias_logical_bytes'] = sum(Path(path).stat().st_size for path in private)
    elif operation == 'plan':
        request = read(spec['request'])
        request['recordings'] = spec['index']
        request_pin = save(spec['output'], request)
        plan = rp.make_plan(request)
        outputs += [request_pin, save(spec['plan'], plan)]
        details.update(scenes=len(plan['scenes']), rows=len(plan['scenes'])*plan['rows_per_scene'],
            by_dataset=dict(Counter(s['dataset'] for s in plan['scenes'])), deferred=plan['deferred'], excluded=len(plan['excluded']))
    elif operation == 'frames':
        plan = read(spec['plan'])
        # build() expects pool identity; require that all pool slots are used.
        # If a future recipe leaves unused slots, refuse before decoding extras.
        part = int(os.environ.get('SLURM_ARRAY_TASK_ID', '0'))
        scene_count = sum(i % spec['shards'] == part for i in range(len(plan['scenes'])))
        workers = min(len(os.sched_getaffinity(0)), scene_count)
        if any(used_frames(s, plan) != s['pool'] for i, s in enumerate(plan['scenes'])
               if i % spec['shards'] == part):
            raise ValueError('Plan has unused pool slots; regenerate exact frame plan')
        receipt = rp.stage(plan, spec['plan'], spec['root'],
            part, spec['shards'], use_pyav=True, workers=max(1, workers))
        outputs.append(save(spec['output'], receipt))
        details.update(workers=workers, scenes=len(receipt['scenes']), frames=sum(len(s['frames']) for s in receipt['scenes']),
            png_bytes=sum(Path(f['path']).stat().st_size for s in receipt['scenes'] for f in s['frames']))
    elif operation == 'package':
        details['frames'] = package(read(spec['plan']), spec['staged'], spec['root'],
            spec['output'], spec['manifest'], spec['a0_manifest'], spec['a0_archive'], spec['a0'])
        outputs += [rp.pin(spec['output']), rp.pin(spec['manifest'])]
    elif operation == 'rows':
        audit = rp.build(read(spec['plan']), spec['plan'], spec['staged'], spec['new_rows'])
        from .p3_provenance import pinned
        details = mixed_rows(Path(spec['new_rows'])/'pose_rows.jsonl', pinned(spec['a0']), spec['output'])
        outputs.append(rp.pin(spec['output']))
    else:
        raise ValueError('Unknown operation')
    result = dict(schema='a1-cpu-receipt-v1', status='PASS', inputs=spec,
        outputs=outputs, details=details, wall_seconds=time.monotonic()-start,
        cpu_seconds=cpu_time()-cpu,
        bytes=sum(Path(p['path']).stat().st_size for p in outputs)+details.get('png_bytes',0))
    save(spec['receipt'], result)
    return result
