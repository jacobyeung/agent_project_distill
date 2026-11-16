pass
import atexit
import copy
import hashlib
import json
import os
from pathlib import Path
import pickle
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4
PINNED = {'student_pilot.common': {'dc087343291b18607235a85d1bdcdfe2b66b1b8f02d3963bb96a5530607621d2'}, 'student_pilot.ddp_admission': {'d3036c32f1f5364304ecec4992280da06defb76b68e916fd7a049f7203ae1c50', 'bcd718947c3c2623287bff32236b1ba63b2ed45a25b6bc2a323c3b0de58271d5'}, 'student_pilot.provisional_data': {'9a95bb1f3dc5f5d3a454cd2936bcaffefb48e2355be28af5552d75750bc055f7', 'ea77b836aa6bb69fb8e6b1cb5971945d13ca2d09a12193543c105d606af8065e', 'd9c6430359b1e889e787bf6279fccbd9000d6a5f07f1a5b3750f80f329b0102d', '1817fe142c3e91cf5234429e9ef47993a0f1c25ae140335cbd4f1ba3aa43c997'}, 'student_pilot.storage': {'74b51ddd14a8bc8b1b2b783d3ae1b7a268a37e71f9164840aa7fdd618d5c8186', '82f48f670b0eafa71690dfe1629b4bf627c43dd1a9a11fe31eccbfbe39b5e99c', 'ed22abb5ef8f27afaccd3a0e1c92d8b04e0e6bfb4211134bb90124b72b783911'}, 'student_pilot.ddp_training': {'4efd337f30fee7450334f10701dfc261d7a01349d224729aeb286bcd5a0a0096', '74f33f63db6b6cff8a66b93ffd3bdd9026a565e514ced0d5597f1d4d1c45d29c', 'cbdf7e1644683544c40a60efc611be55dc9c195b3d5258a0a053a02a3e468337', '35fca46322e36db668fd023b475339ae0c3504bcdf0b4a52ee4b8fdce896ae2e', '4cd9e64ddf9294218c8393f19bda576add8cd7ffb0a22caafb9985de857609fd', '05ec8f868f1750b3d848c0b057e3639f8ff25ac783470c666c5a7fc9ba5f20af', 'c6decb513b853a24c135e5bb559cadd8e26462cccf476d4bc75d9a2bdde3b20b', '58ed6df92cfe4c84d4cbd0bc3f6a57fd5522f4b6eed8c878f1b0345693de2524', '4d46427156a5b20c00ecc8dec1ac97f21e6e4e79a26920965b9307ae1fed302e', '7784a2f0d5d2ba09e156be872e167d9b480a75d03ec390007255272029718ba5', 'ef4866195cfe037bac61a0bcce010cd73a3f6c1c731c35454512d312b30055dd', 'be6611c9fcac16cddb1295c4e4d0e2c367bb3e358bf2ae89a6bd352707a67585'}}
TOKEN_BUDGET_TREES = {'4efd337f30fee7450334f10701dfc261d7a01349d224729aeb286bcd5a0a0096', '4d46427156a5b20c00ecc8dec1ac97f21e6e4e79a26920965b9307ae1fed302e', '7784a2f0d5d2ba09e156be872e167d9b480a75d03ec390007255272029718ba5', 'ef4866195cfe037bac61a0bcce010cd73a3f6c1c731c35454512d312b30055dd', 'be6611c9fcac16cddb1295c4e4d0e2c367bb3e358bf2ae89a6bd352707a67585'}
SENTINEL = '__r1_prestage_rows_sentinel_5d0c1e__'
FRAMES_WAIT_SECONDS = 900
CACHE_LOCK = threading.Lock()
SWAP_LOCK = threading.RLock()
PROBE_FREE_SETTINGS = ('seed', 'learning_rate', 'epochs', 'max_steps', 'warmup_ratio', 'weight_decay', 'betas', 'clip_norm', 'schedule', 'shuffle')

def log(event, **values):
    from student_pilot.opaque_logs import console
    print(json.dumps(console({'event': event, 'pid': os.getpid(), **values}), sort_keys=True, default=str), file=sys.stderr, flush=True)

def fingerprint(path):
    status = os.stat(path)
    return [status.st_size, status.st_mtime_ns, status.st_ctime_ns, status.st_ino]

def enabled():
    return bool(os.environ.get('R1_PRESTAGE_DIR') and os.environ.get('R1_PRESTAGE_RECEIPT_SHA256'))

class Cache:

    def __init__(self):
        self.dir = Path(os.environ['R1_PRESTAGE_DIR'])
        raw = (self.dir / 'RECEIPT.json').read_bytes()
        if hashlib.sha256(raw).hexdigest() != os.environ['R1_PRESTAGE_RECEIPT_SHA256']:
            raise ValueError('pre-stage RECEIPT.json differs from its pinned SHA256')
        self.receipt = json.loads(raw)
        if self.receipt.get('schema') != 'r1-prestage-receipt-v1':
            raise ValueError('unknown pre-stage receipt schema')
        stamp_raw = self.read_pinned(self.receipt['verify_stamp'])
        self.stamp = json.loads(stamp_raw)
        manifest = self.receipt['inputs']['training.json']
        if self.receipt.get('format') != 'r1-prestage-v2' or self.stamp.get('schema') != 'r1-prestage-verify-v1' or self.stamp.get('manifest') != {'path': manifest['path'], 'sha256': manifest['sha256'], 'bytes': manifest['stat'][0], 'mtime_ns': manifest['stat'][1]} or (type(self.stamp.get('shards')) is not list) or (not self.stamp['shards']):
            raise ValueError('pre-stage verification stamp differs from its receipt')
        if not self.inputs_unchanged(None):
            raise ValueError('pre-stage verification stamp file identity changed')
        self.memo = self.receipt['verified_hashes']
        self.local = Path(os.environ['R1_PRESTAGE_LOCAL']) if os.environ.get('R1_PRESTAGE_LOCAL') else None
        self.manifest_rows = self.staged_rows = self.frames_root = self._staging = None
        self.hits = self.heads = 0
        log('stamp_checked', manifest_sha256=self.stamp['manifest']['sha256'], shards=len(self.stamp['shards']), rows=self.stamp['rows'])
        atexit.register(self.summary)

    def summary(self):
        if self.hits or self.heads:
            log('summary', hash_memo_hits=self.hits, manifest_head_reads=self.heads)

    def unchanged(self, path, pin):
        try:
            return fingerprint(path) == pin['stat']
        except OSError:
            return False

    def inputs_unchanged(self, resolve_read):
        pass
        try:
            for item in self.stamp['shards']:
                status = os.stat(item['path'])
                if status.st_size != item['bytes'] or status.st_mtime_ns != item['mtime_ns']:
                    return False
            return True
        except (KeyError, OSError, TypeError, ValueError):
            return False

    def manifest_pin(self, path, label):
        pin = self.receipt['inputs']['training.json']
        try:
            status = os.stat(pin['path'])
            if str(path) == pin['path'] and label == self.receipt['label'] and (self.stamp['manifest']['sha256'] == pin['sha256']) and (status.st_size == self.stamp['manifest']['bytes']) and (status.st_mtime_ns == self.stamp['manifest']['mtime_ns']):
                return pin
        except OSError:
            pass
        return None

    def read_pinned(self, item):
        data = (self.dir / item['file']).read_bytes()
        if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError(f"pre-stage {item['file']} differs from its receipt")
        return data

    def staging(self):
        if self._staging is None:
            item = self.receipt['staging']
            data = (self.dir / item['file']).read_bytes()
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise ValueError('pre-stage STAGING.json differs from its receipt')
            self._staging = json.loads(data)
        return self._staging

    def wait_frames(self):
        pass
        if self.local is None:
            return None
        state, frames = (self.local / 'STATE.json', self.local / 'frames')
        deadline = time.monotonic() + FRAMES_WAIT_SECONDS
        while time.monotonic() < deadline:
            try:
                value = json.loads(state.read_text())
            except (OSError, ValueError):
                value = None
            if value is not None:
                if value.get('status') == 'ready' and frames.is_dir():
                    return frames
                log('frames_unavailable', state=value)
                return None
            if not self.attach_alive():
                log('frames_unavailable', reason='attach process ended without a state')
                return None
            time.sleep(1)
        log('frames_timeout', local=str(self.local))
        return None

    def attach_alive(self):
        try:
            os.kill(int((self.local / 'PID').read_text()), 0)
            return True
        except ProcessLookupError:
            return False
        except (OSError, ValueError):
            return True
_CACHE = [None, False]

def cache():
    if not enabled():
        return None
    with CACHE_LOCK:
        if not _CACHE[1]:
            _CACHE[1] = True
            try:
                _CACHE[0] = Cache()
            except Exception as error:
                log('cache_refused', error=f'{type(error).__name__}: {error}')
        return _CACHE[0]

def patch_common(module):
    original = module.sha256

    def sha256(path, *, read_path=None):
        state = cache()
        entry = state.memo.get(str(path)) if state is not None else None
        if entry is not None:
            try:
                target = str((read_path or module.resolve_read)(path))
                if target == entry['target'] and fingerprint(target) == entry['stat']:
                    state.hits += 1
                    return entry['sha256']
            except (OSError, TypeError, ValueError):
                pass
        return original(path, read_path=read_path)
    module.sha256 = sha256

def patch_admission(module):
    original = module.request_identity
    provisional = module.provisional

    def request_identity(manifest_path, protocol_path, label, student, world_size):
        state = cache()
        try:
            target = str(module.input_path(manifest_path))
        except Exception:
            target = None
        pin = state.manifest_pin(target, label) if state is not None and target is not None else None
        if pin is None:
            return original(manifest_path, protocol_path, label, student, world_size)
        load = provisional.load_json

        def load_json(path):
            if str(path) == target and state.unchanged(target, pin):
                state.heads += 1
                return copy.deepcopy(state.receipt['manifest_head'])
            return load(path)
        with SWAP_LOCK:
            provisional.load_json = load_json
            try:
                return original(manifest_path, protocol_path, label, student, world_size)
            finally:
                provisional.load_json = load
    module.request_identity = request_identity

def patch_data(module):
    original = module.load_training

    def load_training(path, label, use_receipt=True):
        state = cache()
        if state is not None and use_receipt and (state.manifest_pin(str(path), label) is not None) and state.inputs_unchanged(module.resolve_read):
            started = time.monotonic()
            try:
                manifest = pickle.loads(state.read_pinned(state.receipt['manifest_pickle']))
                if len(manifest['rows']) != state.receipt['rows'] or manifest['counts'] != state.receipt['counts']:
                    raise ValueError('pre-stage manifest differs from its receipt')
            except Exception as error:
                log('manifest_fallback', error=f'{type(error).__name__}: {error}')
                return original(path, label, use_receipt)
            state.manifest_rows = manifest['rows']
            log('manifest_from_cache', rows=len(manifest['rows']), seconds=round(time.monotonic() - started, 1))
            return manifest
        return original(path, label, use_receipt)
    module.load_training = load_training

def staged_copy(rows, destinations):
    pass
    staged = []
    for row in rows:
        inputs = row.get('student_input')
        if inputs is None:
            staged.append(dict(row))
            continue
        inputs = {name: [destinations[frame['sha256']].copy() for frame in value] if name == 'frames' else value for name, value in inputs.items()}
        staged.append({name: inputs if name == 'student_input' else value for name, value in row.items()})
    return staged

def patch_storage(module):
    original_stage, original_write = (module.stage_frames, module.write_new)

    def stage_frames(rows, output, scratch_root):
        state = cache()
        if state is None or state.manifest_rows is None or rows is not state.manifest_rows:
            return original_stage(rows, output, scratch_root)
        started = time.monotonic()
        try:
            staging = state.staging()
        except Exception as error:
            log('stage_fallback', reason=f'{type(error).__name__}: {error}')
            return original_stage(rows, output, scratch_root)
        frames = state.wait_frames()
        if frames is None or staging['rows'] != len(rows):
            log('stage_fallback', reason='frames unavailable or row count differs')
            return original_stage(rows, output, scratch_root)
        output = module.output_path(output, module.scratch_directory(scratch_root), new=True)
        module.ensure_free_space(output)
        try:
            os.rename(frames, output)
        except OSError as error:
            log('stage_fallback', reason=f'rename failed: {error}')
            return original_stage(rows, output, scratch_root)
        files, destinations = ([], {})
        for item in staging['files']:
            digest = item['source']['sha256']
            staged = {'path': str(output / digest[:2] / digest), 'sha256': digest}
            destinations[digest] = staged
            files.append({'source': dict(item['source']), 'staged': staged, 'bytes': item['bytes']})
        present = {entry.name: entry.stat().st_size for folder in os.scandir(output) for entry in os.scandir(folder.path)}
        if present != {item['staged']['sha256']: item['bytes'] for item in files}:
            raise ValueError('extracted frames differ from the staging plan')
        staged_rows = staged_copy(rows, destinations)
        receipt = {'schema': 'student-frame-staging-v1', 'files': files, 'source_references': staging['source_references'], 'unique_frames': len(files), 'staged_bytes': sum((item['bytes'] for item in files)), 'scratch_root': str(module.scratch_directory(scratch_root)), 'rows': len(rows), **({'orchard_path_map': os.environ.get('STUDENT_FRAME_ROOT_MAP')} if module.orchard_enabled() else {})}
        state.staged_rows, state.frames_root = (staged_rows, str(output))
        log('frames_attached', frames=len(files), seconds=round(time.monotonic() - started, 1))
        return (staged_rows, receipt)

    def write_new(path, value, root):
        state = cache()
        if state is None or state.staged_rows is None or (not isinstance(value, dict)) or (value.get('rows') is not state.staged_rows) or (Path(path).name != 'input_manifest.json'):
            return original_write(path, value, root)
        started = time.monotonic()
        item = state.receipt['rows_text']
        frames_root = state.frames_root
        small = module.canonical_bytes({**value, 'rows': SENTINEL})
        marker = json.dumps(SENTINEL).encode()
        if not frames_root or json.dumps(frames_root) != '"%s"' % frames_root or small.count(marker) != 1 or (item['placeholder'] in frames_root):
            log('input_manifest_fallback', frames_root=frames_root)
            return original_write(path, value, root)
        try:
            text = state.read_pinned(item)
            if text.count(item['placeholder'].encode()) != item['references']:
                raise ValueError('pre-stage rows.json placeholder count differs from its receipt')
        except Exception as error:
            log('input_manifest_fallback', error=f'{type(error).__name__}: {error}')
            return original_write(path, value, root)
        text = text.replace(item['placeholder'].encode(), frames_root.encode())
        path = module.contained(root, path)
        if path.exists():
            raise ValueError(f'Refusing to replace an existing artifact: {path}')
        path.parent.mkdir(parents=True, exist_ok=True)
        module.directory_capacity(path.parent)
        head, _, tail = small.partition(marker)
        with path.open('xb') as stream:
            stream.write(head)
            stream.write(text)
            stream.write(tail)
        log('input_manifest_from_cache', bytes=len(head) + len(text) + len(tail), seconds=round(time.monotonic() - started, 1))
        return path
    module.stage_frames, module.write_new = (stage_frames, write_new)

def patch_training(module):
    original_mirror = module.mirror_staged_frames

    def mirror_staged_frames(receipt, receipt_pin, rows, output, scratch_root, node_rank, label):
        state = cache()
        if state is None or state.local is None:
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        from student_pilot.storage import ensure_free_space, output_path, write_new
        root = output_path(output, scratch_root)
        files = receipt.get('files', [])
        if receipt.get('schema') != 'student-frame-staging-v1' or module.digest_json(receipt) != receipt_pin['sha256']:
            raise ValueError('Node-local frame staging receipt changed')
        expected = {(frame['path'], frame['sha256']) for row in rows if row.get('student_input') is not None for frame in row['student_input']['frames']}
        declared = {(item['staged']['path'], item['staged']['sha256']) for item in files}
        if declared != expected or len(declared) != len(files) or receipt.get('unique_frames') != len(files):
            raise ValueError('Node-local mirror must cover exactly the admitted staged frames')
        for item in files:
            digest = item['staged']['sha256']
            destination = Path(item['staged']['path'])
            if len(digest) != 64 or any((character not in '0123456789abcdef' for character in digest)) or item['source']['sha256'] != digest or (destination != root / 'frames' / digest[:2] / digest) or destination.is_symlink() or (destination.resolve() != destination) or (type(item['bytes']) is not int) or (item['bytes'] < 0):
                raise ValueError('Node-local frame path, size, or source identity changed')
        try:
            plan = state.staging()['files']
        except Exception as error:
            log('mirror_fallback', reason=f'{type(error).__name__}: {error}')
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        if [(item['source']['sha256'], item['bytes']) for item in plan] != [(item['staged']['sha256'], item['bytes']) for item in files] or (root / 'frames').exists():
            log('mirror_fallback', reason='receipt differs from the cache plan or frames already present')
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        frames = state.wait_frames()
        if frames is None:
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)
        started = time.monotonic()
        root.mkdir(parents=True, exist_ok=True)
        ensure_free_space(root)
        try:
            os.rename(frames, root / 'frames')
        except OSError as error:
            log('mirror_fallback', reason=f'rename failed: {error}')
            return original_mirror(receipt, receipt_pin, rows, output, scratch_root, node_rank, label)

        def verify(item):
            destination = Path(item['staged']['path'])
            module.binding(destination, item['staged']['sha256'])
            if destination.stat().st_size != item['bytes']:
                raise ValueError('Node-local staged frame size changed')
        with ThreadPoolExecutor(max_workers=16) as pool:
            list(pool.map(verify, files))
        record = module.tag({'schema': 'provisional-ddp-node-frame-staging-v1', 'node_rank': node_rank, 'source_receipt': receipt_pin, 'files': files, 'verified_at': datetime.now(timezone.utc).isoformat()}, label)
        path = write_new(f'runtime/node{node_rank}/frame_staging-{uuid4().hex}.json', record, root)
        log('mirror_attached', frames=len(files), seconds=round(time.monotonic() - started, 1))
        return module.binding(path)
    original_write_metric = module.write_metric

    def write_metric(store, metrics, log_stream, value, total_steps, label):
        original_write_metric(store, metrics, log_stream, value, total_steps, label)
        smoke_step = int(os.environ.get('R1_SMOKE_STOP_STEP', '0') or '0')
        if smoke_step > 0 and value.get('step') == smoke_step:
            import signal
            os.kill(os.getpid(), signal.SIGUSR1)
    if enabled():
        module.mirror_staged_frames = mirror_staged_frames
        module.write_metric = write_metric

def probe_key(protocol, rows, audits, settings, topology):
    import torch
    from student_pilot.ddp_config import allocator_settings
    names = ('sequence_tokens', 'visual_tokens', 'assistant_tokens_including_eos')
    stress = sorted({max(range(len(rows)), key=lambda index: audits[rows[index]['qid']][name]) for name in names})
    device = torch.cuda.get_device_properties(0)
    material = {'schema': 'r1-probe-key-v2', 'student': protocol['student'], 'base_sha256': protocol['base_sha256'], 'runtime': protocol['runtime'], 'versions': protocol['versions'], 'init_adapter_sha256': protocol.get('init_adapter_sha256'), 'efa': os.environ.get('R1_EFA'), **({'camera_sha256': protocol['camera_sha256']} if protocol.get('camera_sha256') else {}), **({'geometry_sha256': protocol['geometry_sha256']} if protocol.get('geometry_sha256') else {}), 'settings': {name: value for name, value in settings.items() if name not in PROBE_FREE_SETTINGS}, 'stress_audits': [audits[rows[index]['qid']] for index in stress], 'topology': {name: topology.get(name) for name in ('nnodes', 'local_world_size')}, 'device': {'name': device.name, 'total_memory_bytes': device.total_memory}, 'torch': torch.__version__, 'allocator': allocator_settings()}
    return (hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest(), material)

def reuse_microbatch(reports, settings, topology, checkpoint=None):
    pass
    from student_pilot.ddp_checkpoints import resumed_microbatch
    return resumed_microbatch(reports, settings['world_size'], settings['effective_batch_size'], checkpoint, exact=topology.get('nnodes', 1) > 1)

def patch_probe(module):
    original = module.startup_memory_probe
    original_candidate = module.probe_candidate

    def probe_candidate(model, parameters, cpu_rows, size, pad_token_id, memory_fraction, memory_fit_safety_factor=module.DEFAULTS['memory_fit_safety_factor'], replicated=None, digit_loss=None):
        res = original_candidate(model, parameters, cpu_rows, size, pad_token_id, memory_fraction, memory_fit_safety_factor=memory_fit_safety_factor, replicated=replicated, **{'digit_loss': digit_loss} if digit_loss is not None else {})
        import torch.distributed as dist
        world = dist.get_world_size() if dist.is_available() and dist.is_initialized() else 1
        rep_ids = {id(p) for p in replicated or ()}
        sharded_base_bytes = sum((p.numel() * p.element_size() for p in parameters if id(p) not in rep_ids))
        if world == 8 and sharded_base_bytes > 1 << 30 and ('peak_allocated_bytes' in res):
            delta = 3 * int(sharded_base_bytes)
            raw_allocated = int(res['peak_allocated_bytes'])
            raw_reserved = int(res['peak_reserved_bytes'])
            adj_allocated = max(0, raw_allocated - delta)
            adj_reserved = max(0, raw_reserved - delta)
            limit = res['memory_limit_bytes']
            adj_with_margin = adj_allocated * memory_fit_safety_factor
            adj_reserved_over = adj_reserved > limit
            fits = bool(res['fits']) and adj_with_margin <= limit and (res.get('expandable_segments') or not adj_reserved_over)
            res['world8_raw_peak_allocated_bytes'] = raw_allocated
            res['world8_raw_peak_reserved_bytes'] = raw_reserved
            res['world8_raw_allocated_with_safety_factor_bytes'] = res['allocated_with_safety_factor_bytes']
            res['world8_raw_fits'] = res['fits']
            res['world8_to_world32_sharded_delta_bytes'] = delta
            res['peak_allocated_bytes'] = adj_allocated
            res['peak_reserved_bytes'] = adj_reserved
            res['allocated_with_safety_factor_bytes'] = adj_with_margin
            res['reserved_over_limit'] = adj_reserved_over
            res['fits'] = fits
        return res

    def startup_memory_probe(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint, geometry=None):
        import torch
        extra = module.geometry_option(geometry) if hasattr(module, 'geometry_option') else {} if geometry is None else {'geometry': geometry}
        registry = os.environ.get('R1_PROBE_REGISTRY')
        if os.environ.get('STUDENT_MEMORY_PROBE_CACHE') is not None or not registry:
            return original(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint, **extra)
        world = settings['world_size']
        key = material = reports = source = None
        try:
            key, material = probe_key(protocol, rows, audits, settings, topology)
            entry = Path(registry) / (key + '.json')
            if entry.is_file():
                value = json.loads(entry.read_text())
                if value.get('key') == key and len(value.get('ranks', [])) == world:
                    reports, source = (value['ranks'], str(entry))
            resume = os.environ.get('RESUME_FROM')
            if reports is None and checkpoint is not None and resume and (topology.get('nnodes', 1) > 1):
                path = Path(resume) / 'artifacts/memory_probe.json'
                pin = checkpoint['files'].get('artifacts/memory_probe.json')
                if pin is not None and hashlib.sha256(path.read_bytes()).hexdigest() == pin['sha256']:
                    candidate = json.loads(path.read_text())['ranks']
                    total = torch.cuda.get_device_properties(0).total_memory
                    if len(candidate) == world and all((trial.get('total_memory_bytes') == total for report in candidate for trial in report['trials'] if trial.get('fits'))):
                        reports, source = (candidate, str(path))
        except Exception as error:
            log('probe_lookup_failed', error=f'{type(error).__name__}: {error}')
            reports = None
        usable = False
        try:
            if reports is not None:
                size = reuse_microbatch(reports, settings, topology, checkpoint)
                report = next((item for item in reports if item.get('rank') == rank), None)
                trial = next((item for item in (report or {}).get('trials', []) if item.get('microbatch') == size and item.get('fits')), None)
                if trial is not None:
                    free, _ = torch.cuda.mem_get_info()
                    usable = trial['peak_allocated_bytes'] * settings['memory_fit_safety_factor'] <= free + torch.cuda.memory_reserved()
        except Exception as error:
            log('probe_check_failed', error=f'{type(error).__name__}: {error}')
            usable = False
        votes = module.gather({'key': key, 'usable': usable}, world)
        if key is not None and all((vote['usable'] and vote['key'] == key for vote in votes)):
            module.startup_event('memory_probe_reused')
            report = next((item for item in reports if item.get('rank') == rank))
            log('probe_reused', source=source, key=key)
            return ({**report, 'reused_measured_probe': {'source': source, 'key': key}}, None)
        probe, context = original(model, processor, rows, audits, settings, rank, lease_check, protocol, topology, checkpoint, **extra)
        probes = module.gather(probe, world)
        if rank == 0 and key is not None:
            try:
                directory = Path(registry)
                directory.mkdir(parents=True, exist_ok=True)
                entry = directory / (key + '.json')
                if not entry.exists():
                    part = directory / (key + '.json.part.%d' % os.getpid())
                    part.write_text(json.dumps({'key': key, 'material': material, 'ranks': probes, 'recorded_at': datetime.now(timezone.utc).isoformat()}, sort_keys=True) + '\n')
                    os.replace(part, entry)
                    log('probe_recorded', entry=str(entry))
            except Exception as error:
                log('probe_record_failed', error=f'{type(error).__name__}: {error}')
        return (probe, context)
    module.probe_candidate = probe_candidate
    module.startup_memory_probe = startup_memory_probe
PATCHES = {'student_pilot.common': (patch_common,), 'student_pilot.ddp_admission': (patch_admission,), 'student_pilot.provisional_data': (patch_data,), 'student_pilot.storage': (patch_storage,), 'student_pilot.ddp_training': (patch_training, patch_probe)}

def wanted(fullname):
    if fullname not in PATCHES:
        return False
    if fullname == 'student_pilot.ddp_training':
        return enabled() or bool(os.environ.get('R1_PROBE_REGISTRY'))
    return enabled()

def patch(module, source_bytes):
    if not wanted(module.__name__):
        return
    if hashlib.sha256(source_bytes).hexdigest() not in PINNED[module.__name__]:
        log('module_not_pinned', module=module.__name__)
        return
    for function in PATCHES[module.__name__]:
        if function is patch_probe and (not os.environ.get('R1_PROBE_REGISTRY')):
            continue
        if function is patch_probe and hashlib.sha256(source_bytes).hexdigest() in TOKEN_BUDGET_TREES:
            log('probe_hook_skipped', module=module.__name__, reason='token-budget tree probes its planned boxes')
            continue
        if function is not patch_probe and (not enabled()):
            continue
        function(module)
PINNED['student_pilot.provisional_data'].add('c105b3e52f691f87bf3d6837a00cfb424d106bd9986f88c7498044c2a0ed6985')
PINNED['student_pilot.ddp_training'].add('9d374a2276f0a9263f13c1362cb4deefb11684fa775e3be7a611ddea1c979473')
TOKEN_BUDGET_TREES.add('9d374a2276f0a9263f13c1362cb4deefb11684fa775e3be7a611ddea1c979473')

PINNED['student_pilot.ddp_training'].add('25e46ca7520cab909210daf725a5d87b5955fe484bda37f8e172418bb19bdc2d')
TOKEN_BUDGET_TREES.add('25e46ca7520cab909210daf725a5d87b5955fe484bda37f8e172418bb19bdc2d')
