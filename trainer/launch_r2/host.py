"""Bounded frame-host preparation through the native producer and CPU encoders."""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import resource
import signal
import tarfile
import time

from student_pilot.p3_provenance import digest, file_pin, load, pinned, write

ESTIMATES = {'vqa': 3_200_000_000, 'routing': 1_700_000_000, 'pose': 1_500_000_000,
             'pointing': 800_000_000, 'membership': 1_000_000_000, 'dense': 1_000_000_000}
LIMITS = {key: math.ceil(value*1.5) for key,value in ESTIMATES.items()}
# Sealed rows.sqlite pins in out/POSE_SOURCE_BINDINGS.json.
POSE_SHA256 = frozenset(('b32359ce256a567912d6436fac95dcab78bcef3bb2e1154cabdca57bacdc5320',
                         '0b95850a2dec57ec6702ca72cd198eb5afdcdcdd5f711a76a878104e30ec3571'))


def estimate(rows, measured_bytes, full_rows):
    if type(rows) is not int or not 0 < rows <= 2000 or measured_bytes <= 0 or full_rows < rows:
        raise ValueError('Estimator requires a bounded nonempty slice and a full census')
    projected = math.ceil(measured_bytes/rows*full_rows)
    return dict(slice_rows=rows, slice_bytes=measured_bytes, full_rows=full_rows,
                extrapolated_bytes=projected, limit_bytes=math.ceil(projected*1.5), margin=1.5)


def cpu_guard(args, environment, hashes):
    from .build import bad_string
    if any('gpu' in value.lower() or 'gres' in value.lower() for value in args):
        raise ValueError('GPU request refused by CPU job')
    for key in ('SLURM_GPUS', 'SLURM_GPUS_ON_NODE', 'SLURM_GPUS_PER_NODE', 'SLURM_JOB_GPUS', 'CUDA_VISIBLE_DEVICES'):
        if environment.get(key, '') not in ('', '0') or key == 'CUDA_VISIBLE_DEVICES' and environment.get(key, ''):
            raise ValueError('GPU allocation refused by CPU job')
    for value in [*args, *environment.values()]:
        if bad_string(str(value), hashes):
            raise ValueError('Forbidden job path, argument or environment value')


class Guard:
    def __init__(self, root, *, wall=21600, idle=1200, limits=None, clock=time.monotonic):
        self.root = Path(root).resolve()
        self.clock = clock
        self.started = self.progress = clock()
        self.wall, self.idle = wall, idle
        self.limits = LIMITS if limits is None else limits

    def tick(self):
        self.check()
        self.progress = self.clock()

    def check(self):
        now = self.clock()
        if now-self.started > self.wall:
            raise ValueError('Wall-time limit exceeded')
        if now-self.progress > self.idle:
            raise ValueError('Stalled step: no progress limit exceeded')

    def size(self, name, size):
        if size > self.limits[name]:
            raise ValueError('Store over its per-file limit: '+name)


@contextmanager
def watchdog(guard):
    previous = signal.getsignal(signal.SIGALRM)
    def alarm(*_):
        guard.check()
    signal.signal(signal.SIGALRM, alarm)
    signal.setitimer(signal.ITIMER_REAL, 1, 1)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def input_paths(packet, root):
    """Every required input is pinned; both pose sources are independent inputs."""
    required = ('manifests', 'pose_sources', 'configuration', 'pose_template', 'real_proof', 'counts')
    if not packet.get('pose_sources') or len(packet['pose_sources']) != 2:
        raise ValueError('Missing pose source: require both sealed pose sources')
    for key in required:
        if not packet.get(key):
            raise ValueError('Missing frame-host input: '+key)
    paths = {}
    for key in required:
        values = packet[key] if isinstance(packet[key], list) else [packet[key]]
        paths[key] = []
        for pin in values:
            if not isinstance(pin, dict) or not {'path', 'sha256'} <= set(pin):
                raise ValueError('Missing input sha256: '+key)
            path = Path(pin['path'])
            path = path if path.is_absolute() else Path(root)/path
            if not path.is_file():
                raise ValueError('Missing frame-host input file: '+key)
            if file_pin(path)['sha256'] != pin['sha256']:
                raise ValueError('Input sha256 differs: '+key)
            paths[key].append(path)
    if len({pin['sha256'] for pin in packet['pose_sources']}) != 2:
        raise ValueError('Missing distinct pose source')
    return paths


def stage_init(archive_pin, root, members, *, max_member_bytes):
    """Map delivered m544 members without changing the export metadata bytes."""
    if not isinstance(members,dict) or not members or type(max_member_bytes) is not int or max_member_bytes<=0:
        raise ValueError('Missing init member inventory or positive per-member limit')
    root = Path(root).resolve()
    results = {}
    with tarfile.open(pinned(archive_pin), 'r:*') as archive:
        for member in archive:
            if member.isdir():
                continue
            name = PurePosixPath(member.name)
            if (not member.isfile() or name.is_absolute() or '..' in name.parts
                    or not member.name.startswith('m544/') or member.name not in members
                    or member.name in results or member.size > max_member_bytes):
                raise ValueError('Unadmitted init archive member')
            relative = 'ap/8865619b/runs/469ddece/'+member.name
            if member.name == 'm544/artifact.json':
                relative = 'ap/ee544000/'+member.name
            target = root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            with archive.extractfile(member) as source, target.open('xb') as output:
                for block in iter(lambda: source.read(1 << 20), b''):
                    h.update(block)
                    output.write(block)
            if h.hexdigest() != members[member.name]:
                raise ValueError('Init member sha256 differs')
            results[member.name] = relative
    if set(results) != set(members) or 'm544/artifact.json' not in results:
        raise ValueError('Init archive inventory incomplete')
    return results


def native_config(template, native, pose_template, output):
    """Wrap produced stores in native stream receipts, retaining sealed pose metadata."""
    from student_pilot import carrier_c1_run as run
    from student_pilot.r2_contract import CONTRACT, INIT
    cfg, pose = deepcopy(template), deepcopy(pose_template)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    streams = {}
    for name, store in native['streams'].items():
        value = dict(schema='c1-stream-v1', stream=name, division=pose['inputs']['division'],
                     count=store['count'], database=store['database'], heldout_overlap=0, gt_masks_only=True)
        if name == 'pose':
            value = {**pose, 'count':store['count'], 'database':store['database']}
        if name == 'routing':
            value.update(schema=run.routing.ROUTING_SCHEMA, scene_role='train')
        write(output/(name+'.json'), value)
        streams[name] = file_pin(output/(name+'.json'))
    cfg.update(streams=streams, r2_membership=native['r2_membership'],
               preparation_output=str(output/'p'), output=str(output/'r'))
    cfg = {k:v for k,v in cfg.items() if k != 'preparation'}
    cfg['r2'] = {**cfg.get('r2', {}), 'contract':CONTRACT, 'init':INIT, 'mode':'warm_start',
                 'run_id':output.name, 'code_sha256':load(pinned(cfg['code']))['tree_sha256'],
                 'mixture_sha256':digest({k:cfg.get(k) for k in ('recipe','streams','route_table')})}
    return cfg


def encode_first(cfg, guard):
    """Run native Rows.encode and the real mixed sampler; stop before forward."""
    from student_pilot import carrier_c1_run as run
    receipt, manifest = run.prepared(cfg, admission=False)
    processor = run.processor_for_receipt(manifest, receipt)
    rows = run.Rows(receipt, processor)
    recipe = run.recipe_for(cfg)
    counts = {key:value['count'] for key,value in receipt['streams'].items()}
    plans = run.data.mixed_indices(counts, 1, training_mode=cfg['training_mode'],
                                  mix=recipe['mix'], world=4, r2_sampling=cfg.get('r2_sampling'))
    records = []
    try:
        for plan in plans:
            for stream, indices in plan:
                for rank in range(4):
                    batch, targets, audit = rows.get(stream, int(indices[rank]))
                    if any(value.is_cuda for value in batch.values() if hasattr(value, 'is_cuda')):
                        raise ValueError('CPU boundary received a GPU tensor')
                    records.append(dict(rank=rank, stream=stream, index=int(indices[rank]),
                                        tokens=int(batch['input_ids'].shape[-1]), forward=False))
                    guard.tick()
    finally:
        rows.close()
    return records


def run_packet(root, packet_pin, *, full=True):
    root = Path(root).resolve()
    packet = load(pinned({**packet_pin, 'path':str(root/packet_pin['path'])}))
    guard = Guard(root, wall=packet.get('wall_seconds',21600),
                  idle=packet.get('idle_seconds',1200),limits=packet.get('limits',LIMITS))
    with watchdog(guard):
        return execute_packet(root,packet,guard,full=full)


def execute_packet(root, packet, guard, *, full):
    from .runtime import bounded_writes, obligations, statement_hits, checked_hits, init_layout
    paths = input_paths(packet, root)
    guard.tick()
    if full and any(load(paths[key][0]).get('synthetic') for key in ('configuration','real_proof','counts')):
        raise ValueError('Synthetic inputs cannot admit the full host job')
    if full and {pin['sha256'] for pin in packet['pose_sources']} != POSE_SHA256:
        raise ValueError('Pose sources differ from the sealed source pins')
    pose_headers = [load(path) for path in paths['manifests'] if load(path).get('stream') == 'pose']
    if {value.get('pose_source_sha256') for value in pose_headers} != {pin['sha256'] for pin in packet['pose_sources']}:
        raise ValueError('Pose manifests do not bind both supplied pose sources')
    cfg = load(paths['configuration'][0])
    from student_pilot.r2_policy import preparation
    repeats = None
    if 'r2_build2' in cfg:
        repeats = preparation(cfg['r2_build2'], root)
        if packet['counts']['sha256'] != cfg['r2_build2']['counts']['sha256']:
            raise ValueError('Host counts differ from the admitted mixture')
        if not cfg.get('r2_sampling'):
            raise ValueError('Missing final-reader type indices')
    if cfg.get('geometry_connector') == 'gf1' and not packet.get('dense'):
        raise ValueError('Missing A2 dense manifest')
    if cfg.get('geometry_connector') == 'gf1':
        dense = load(pinned(packet['dense']))
        if dense.get('synthetic') or dense.get('reconstruct_then_subsample') is not True:
            raise ValueError('A2 requires a real dense reconstruction manifest')
        from student_pilot.r2_config import apply_native
        if not packet.get('geometry_assets'):
            raise ValueError('Missing frozen tower assets')
        cfg = apply_native(cfg, load(pinned(packet['geometry_assets'])))
    output = root/packet['output']
    if not output.resolve().is_relative_to(root) or output.exists():
        raise ValueError('Job output must be a new folder inside its job root')
    output.mkdir(parents=True)
    from student_pilot.r2_materialize import materialize
    from student_pilot.r2_real_proof import prove
    from student_pilot import carrier_c1_run as run
    required = obligations()
    if not full:
        required = [r for r in required if r['category'] == 'model-loader']
    ceiling = max(*guard.limits.values(), packet.get('init_member_limit') or 0)
    with bounded_writes(root, ceiling), statement_hits(required) as hits:
        if packet.get('init_archive'):
            staged = init_layout(packet['init_archive'], output/'d', packet['init_members'],
                                 packet['init_member_limit'])
            cfg['init_artifact'] = {**cfg['init_artifact'], 'artifact':staged['artifact']}
            os.environ['C1_INIT_LOCAL'] = staged['mirror_root']
        elif full:
            raise ValueError('Missing delivered init archive and member inventory')
        if full:
            os.environ['STUDENT_R2_FRAME_HOST'] = '0'
            try:
                materialize(paths['manifests'], output/'e', full=True)
            except ValueError as error:
                if str(error) != 'Full materialization requires an explicit frame-host admission':
                    raise
            else:
                raise ValueError('Full-store admission mutation unexpectedly passed')
        os.environ['STUDENT_R2_FRAME_HOST'] = '1'
        report = materialize(paths['manifests'], output/'a', full=full, dense=True,
                             limits=guard.limits, progress=guard.tick)
        if report['status'] != 'ready':
            raise ValueError('Missing real RGB on frame host')
        native = load(pinned(report['receipt']))
        cfg = native_config(cfg, native, load(paths['pose_template'][0]), output/'b')
        run.prepare(cfg)
        cfg['preparation'] = file_pin(Path(cfg['preparation_output'])/'receipt.json')
        first = run.first_batch_check(cfg, range(4), output/'1.json', encode_only=True)
        guard.tick()
        run.dryrun(cfg, output/'2.json', encode_only=True)
        proof = load(paths['real_proof'][0])
        metadata = prove(proof['rows_dir'], proof['sealed_meta_dir'], output/'c')
        result = dict(config=cfg, first_batch=first, metadata=metadata,
                      boundary='CPU tensors before model forward', production_authorized=False,
                      repeats=repeats, statements=checked_hits(required,hits),
                      schema='r2-host-preparation-v1',full_store=full,packet_digest=digest(packet),
                      source_revision='sha256:'+cfg['r2']['code_sha256'])
        write(output/'0.json', result)
        return result
