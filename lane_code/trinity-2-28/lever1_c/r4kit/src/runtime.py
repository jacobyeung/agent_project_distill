"""Private runtime, reviewed locally; public entrypoints use opaque filenames."""
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
import importlib.util
import resource
import threading

C = None
GPU_PEAK = 0
MEMORY_LOCK = threading.RLock()
WATCH_STOP = None
WATCH_THREAD = None

def memory_metrics(out=None, reset=False, final=False):
    with MEMORY_LOCK:
        return _memory_metrics(out, reset, final)

def _memory_metrics(out=None, reset=False, final=False):
    global GPU_PEAK
    torch = sys.modules.get('torch')
    active = torch is not None and torch.cuda.is_initialized()
    allocated = int(torch.cuda.max_memory_allocated()) if active else 0
    GPU_PEAK = max(GPU_PEAK, allocated)
    value = dict(peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                 gpu_max_allocated_bytes=GPU_PEAK, batch_gpu_max_allocated_bytes=allocated,
                 gpu_measured=active, gpu_peak_complete=final, sampled_at=time.time())
    if out is not None:
        temp = Path(out)/'7.part'
        C.store(temp, value); temp.replace(Path(out)/'7.json')
    if reset and active: torch.cuda.reset_peak_memory_stats()
    return value


def read(path): return C.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, value):
    C.store(path, value)


class Deadline(Exception):
    pass


class PairWriter:
    def __init__(self, stream, rows, progress, started):
        self.stream, self.rows, self.progress, self.started = stream, rows, progress, started
        self.pending = {}

    def emit(self, i, result):
        row = self.rows[i]
        result.update(i=row['i'], r=row['r'], a=row['a'], s=time.monotonic()-self.started)
        self.pending[i] = result
        pair = i-i%2
        if pair in self.pending and pair+1 in self.pending:
            raw = b''.join(C.pack(json.dumps(self.pending[j], sort_keys=True, allow_nan=False)) for j in (pair,pair+1))
            assert len(raw) <= 262144 and self.stream.tell()+len(raw) < 1000000
            self.stream.write(raw); self.stream.flush(); os.fsync(self.stream.fileno())
            self.progress[0] += 2
            del self.pending[pair]; del self.pending[pair+1]


def run_batches(out, rows, progress, end, prepare_rows, generate, deadline):
    # The first batch is a measurement; subsequent admission uses the slowest
    # observed prefill and token step, extrapolated to the frozen 64-token cap.
    required = 60.0
    with (out/'0.jsonl').open('xb') as stream, (out/'3.jsonl').open('xb') as timings:
        for start in range(0, len(rows), 8):
            remaining = end-time.time()
            group = rows[start:start+8]
            assert all(group[j]['i']==group[j+1]['i'] and (group[j]['a'],group[j+1]['a'])==(0,1) for j in range(0,len(group),2))
            memory_metrics(out, reset=True)
            record = dict(batch=start//8, rows=len(group), remaining_s=remaining, required_s=required)
            if remaining < required+10:
                record.update(status='not_admitted', completed_pairs=0, **memory_metrics(out))
                timings.write(C.pack(json.dumps(record))); timings.flush(); os.fsync(timings.fileno())
                return 'timeout'
            deadline()
            t0 = time.monotonic(); before = progress[0]; metrics = {}; state = 'failed'; prep_s = 0.
            try:
                batches = prepare_rows(group)
                prep_s = time.monotonic()-t0
                writer = PairWriter(stream, group, progress, t0)
                generate(batches, writer.emit, deadline, metrics)
                batches = None
                state = 'complete'
            finally:
                elapsed = time.monotonic()-t0
                required = max(required, 1.25*(prep_s+metrics.get('prefill_s', 0)+64*metrics.get('max_step_s', 0)), 1.25*elapsed)
                record.update(status=state, elapsed_s=elapsed, prepare_s=prep_s, completed_pairs=(progress[0]-before)//2,
                              next_required_s=required, **metrics, **memory_metrics(out))
                timings.write(C.pack(json.dumps(record))); timings.flush(); os.fsync(timings.fileno())
    return 'complete'


class ClosureImportError(ImportError):
    def __init__(self, entry, error):
        self.closure_entry = entry
        self.exception_message = f'{type(error).__name__}: {error}'
        super().__init__(f'Closure entry {entry}: {self.exception_message}')


def presence(name):
    module = sys.modules.get(name)
    try:
        spec = importlib.util.find_spec(name)
    except (ImportError, ValueError):
        spec = None
    origin = getattr(spec, 'origin', None) if spec is not None else getattr(module, '__file__', None)
    present = spec is not None or module is not None
    return dict(present=present, find_spec=spec is not None, origin=origin,
                loaded=module is not None, fallback_expected=not present,
                fallback='PyTorch reference implementation' if not present else None)


def import_closure(p, mode='c'):
    """Replay the recorded CPU worker trace plus the prior import inventory."""
    import importlib
    import typing
    assert typing.TYPE_CHECKING is False, "Boot requires runtime typing semantics"
    def load(name):
        try:
            canonical = inventory['aliases'].get(name)
            if canonical: importlib.import_module(canonical)
            importlib.import_module(name)
        except Exception as error:
            raise ClosureImportError(name, error) from error
    inventory = read(p/'2.json')['import_closure']
    names = inventory['required_modules']
    digest = hashlib.sha256('\n'.join(names).encode()).hexdigest()
    assert digest == inventory['closure_sha256']
    imported = []
    for name in names:
        load(name)
        imported.append(name)
    excluded = dict(inventory['exclusions'])
    for name, reason in inventory['gpu_only'].items():
        if mode == 'g':
            load(name)
            imported.append(name)
        else:
            excluded[name] = reason
    # Optional kernels: Transformers binds them at import or uses its PyTorch
    # reference path. GPU boot records presence and never fails on absence.
    optional = {}
    for name, reason in inventory.get('gpu_optional', {}).items():
        if mode == 'g':
            optional[name] = presence(name)
        else:
            excluded[name] = reason
    return dict(modules=len(imported), required_modules=imported,
                optional_modules=optional,
                exclusions=excluded, closure_sha256=digest,
                method=inventory['method'], trace=inventory['trace'],
                baseline_modules=inventory['baseline_modules'],
                traced_modules=inventory['traced_modules'])


def run(package, mode, end):
    # Boot and workload use the same interpreter and base package namespace.
    # Only interpreter, environment and code pins must pass before boot.
    global C, WATCH_STOP, WATCH_THREAD
    started = time.monotonic()
    end = min(float(end), time.time()+1500)
    def deadline(*unused):
        if C is not None: memory_metrics(Path(package)/'a')
        if unused or time.time() >= end:
            raise Deadline()
    signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(.001, end-time.time()))
    p = Path(package)
    spec = importlib.util.spec_from_file_location('a_storage', p/'9.py')
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
    spec = importlib.util.spec_from_file_location('a_monitor', p/'11.py')
    monitor = importlib.util.module_from_spec(spec); spec.loader.exec_module(monitor)
    mark = lambda stage, **extra: monitor.mark(C, p/'a', stage, **extra)
    mark('runtime_start')
    memory_metrics(p/'a')
    WATCH_STOP = threading.Event()
    def sample():
        while not WATCH_STOP.wait(.2):
            try: memory_metrics(p/'a')
            except (OSError, RuntimeError, AttributeError): pass
    WATCH_THREAD = threading.Thread(target=sample, daemon=True)
    WATCH_THREAD.start()
    cfg = read(p/'2.json')
    d = Path(cfg['logical'])/'d'
    out = p/'a'
    out.mkdir(exist_ok=True)
    finder = C.install(p, outputs=[d/'e'])
    (p/'c/b/work/tmp').mkdir(parents=True, exist_ok=True)
    sources = finder.Path(p/'c')
    for root in cfg['inputs']['env_roots']:
        sys.path.insert(0, root)
    mark('imports')
    import torch
    torch.set_num_threads(16)
    from parity_kit import stage_restore
    from e2e_reader.parity import load_native, trainer_row
    from evalpath.runtime import prompt_batch
    from student_pilot.carrier_c1_decode import _prepare_decode, consume_cache_tokens
    from student_pilot.ground_context import closed_adapters
    spec = importlib.util.spec_from_file_location('a0', p/'7.py')
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    if os.environ.get('A_B') == '1':
        closure = import_closure(p, mode)
        write(out/'10.json', dict(passed=True, mode=mode, seconds=time.monotonic()-started,
            interpreter=sys.executable, cwd=os.getcwd(), bulk_bytes=0, **closure))
        mark('boot_complete')
        signal.setitimer(signal.ITIMER_REAL, 0)
        return
    pins = cfg['export']
    assert pins['artifact']['sha256'].startswith('5083243c') and pins['step'] == 400
    f = cfg['inputs']['files']
    path = lambda n: Path(f[n]['path'])
    # The stage function's pinned export branch supplies all request fields.
    # Its otherwise unused initial read gets an empty, label-free request.
    request = p/'6.json'
    export = d/'e'
    mark('restore')
    stage_restore.stage(path('full_weights').parent, path('artifact').parent,
        d, export, request=request, tree=sources/'tree',
        base_assets=path('base_config').parent, model_manifest_tar=path('original_model'),
        export_pins=pins, data_root=d, progress=mark)
    mark('frames')
    settings = dict(tree=str(sources/'tree'),
                    config=str(d/pins['preparation']['config']['path']))
    data = read(p/'1.json')
    assert len(data['rows']) == 580 and len(data['captures']) == 98
    # Every RGB is authenticated once; the same capture is used in both arms.
    for capture in data['captures'].values():
        for frame in capture['frames']:
            deadline()
            assert sha(Path(cfg['inputs']['frames_root'])/frame['path']) == frame['sha256']
    def row_for(row):
        task = dict(id=row['i'], question=row['q'], options=[],
                    dataset='a', scene=row['r'], question_type='object_abs_distance')
        return trainer_row(task, data['captures'][row['r']], cfg['inputs']['frames_root'], verify=False)
    if mode == 'c':
        from student_pilot import carrier_c1_run as trainer
        receipt = read(export/'receipt.json')
        config = read(settings['config'])
        receipt.update(align=config.get('align'), init_artifact=config.get('init_artifact'),
                       frame_markers=config.get('frame_markers', False),
                       pointing_weights=config.get('pointing_weights'),
                       camera={**receipt['camera'], **config.get('camera_overrides', {})})
        manifest = read(receipt['model']['path'])
        mark('processor')
        processor = trainer.processor_for_receipt(manifest, receipt)
        checked = []
        previous = None
        for row in data['rows'][:2]:
            mark('prompt', arm=row['a'])
            batch = prompt_batch(processor, row_for(row), config, 'routed')
            assert 'labels' not in batch and batch['input_ids'].shape[0] == 1
            checked.append(dict(i=row['i'], a=row['a'], n=int(batch['input_ids'].shape[1])))
            if previous is not None:
                for key in ('pixel_values_videos','video_grid_thw','aux_camera_positions','frame_indices','video_sha256'):
                    if key in batch:
                        same = torch.equal(batch[key], previous[key]) if isinstance(batch[key], torch.Tensor) else batch[key] == previous[key]
                        assert same, key
            previous = batch
        mark('cpu_complete')
        write(out/'1.json', dict(passed=True, mode='c', checked=checked,
            frames=98*32, artifact=pins['artifact']['sha256'], frozen=cfg['frozen'],
            seconds=time.monotonic()-started, model_loaded=False,
            prefix_27_1884=processor.tokenizer.decode([27,1884],skip_special_tokens=False)=='<ground'))
        signal.setitimer(signal.ITIMER_REAL, 0)
        WATCH_STOP.set(); WATCH_THREAD.join(timeout=1)
        memory_metrics(out, final=True)
        return
    mark('model_load')
    load_start = time.monotonic()
    model, processor, loaded = load_native(export, device='cuda:0', settings=settings)
    assert not getattr(model, 'geometry_online', None)
    assert getattr(model, 'sam3_tower', None) is None
    assert getattr(model, 'g3t_tower', None) is None
    loading = time.monotonic()-load_start
    tokenizer = processor.tokenizer
    reserved = [tokenizer.convert_tokens_to_ids(t) for t in ('<tool_response>', '</tool_response>')]
    carrier = getattr(model, 'carrier_id', None)
    if carrier is not None:
        reserved.append(int(carrier))
    spec = importlib.util.spec_from_file_location('a_batch', p/'10.py')
    batched = importlib.util.module_from_spec(spec); spec.loader.exec_module(batched)
    progress = [0]
    status = 'failed'
    try:
        def prepare_rows(rows):
            batches = [prompt_batch(processor, row_for(row), loaded['config'], 'routed') for row in rows]
            return [{k:v.to('cuda:0') if hasattr(v, 'to') else v for k,v in b.items()} for b in batches]
        def generate(batches, emit, check, metrics):
            batched.generate(model, processor, batches, probe, emit, check, metrics=metrics)
        mark('batches')
        with torch.no_grad():
            status = run_batches(out, data['rows'], progress, end, prepare_rows, generate, deadline)
    except Deadline as error:
        status = 'timeout'
        write(out/'4.json', C.diagnostic(error))
    finally:
        memory_metrics(out)
        signal.setitimer(signal.ITIMER_REAL, 0)
        records = progress[0]
        write(out/'1.json', dict(passed=status=='complete' and records==580, mode='g',
            records=records, status=status, frozen=cfg['frozen'], artifact=pins['artifact']['sha256'],
            load_s=loading, seconds=time.monotonic()-started, tools_served=0,
            external_components_loaded=False, max_new_tokens=64))


def main(package, mode, end):
    global C
    try:
        run(package, mode, end)
        return 0
    except BaseException as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        root = Path(package); (root/'a').mkdir(exist_ok=True)
        if C is None:
            spec = importlib.util.spec_from_file_location('a_storage', root/'9.py')
            C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
        memory_metrics(root/'a')
        write(root/'a/4.json', C.diagnostic(error))
        if os.environ.get('A_B') == '1':
            write(root/'a/10.json', dict(passed=False, mode=mode, bulk_bytes=0,
                **{k:v for k,v in C.diagnostic(error).items() if k != 'passed'}))
        return 1
    finally:
        if WATCH_STOP is not None: WATCH_STOP.set()
        if WATCH_THREAD is not None: WATCH_THREAD.join(timeout=1)
        if C is not None and (Path(package)/'a').is_dir(): memory_metrics(Path(package)/'a', final=True)


if __name__ == '__main__':
    if sys.argv[2] == 'c':
        resource.setrlimit(resource.RLIMIT_AS, (32*1024**3, 32*1024**3))
    raise SystemExit(main(*sys.argv[1:]))
