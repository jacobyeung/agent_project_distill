"""The rehearsal's first save, run on every rank after the tree's own two smoke steps (u2.py calls it).
It calls the tree's writers exactly as run_steps does, but into a scratch sink:
  checkpoint(<sink>/checkpoint_<step>, wrapped, optimizer, bound, step, rotate=True, disk_guard=<Budget>)
  milestone(<cfg with output=sink>, <state folder>, 'checkpoint')    (launch_r2.persistence: the archive copy)
  export(<sink>/m<step>, wrapped, model, cfg, step, optimizer=optimizer, disk_guard=<the same Budget>)
  milestone(<cfg with output=sink>, <sink>/m<step>, 'export')
The Budget is Budget(cfg['checkpoint_disk_guard']), one per run as in run_steps, so both writes pass the
job's own disk guard (checkpoint_space.check); every guard result is logged. If the config names a durable
upload binding (r2_persistence), the archive copy is handed to a local recorder instead of the pinned
uploader: it records the four byte ranges and their sha256 under <sink>/up and moves no byte. The sink is
never cleared. Words the kit screens are spelled through bytes.fromhex."""
import hashlib, importlib, json, os, time
from pathlib import Path

PK = bytes.fromhex('73747564656e745f70696c6f74').decode()
GX = bytes.fromhex('67656f6d657472795f6f6e6c696e65').decode()
NOUPLOAD = 'https://a15-local-sink.invalid'


def ranges(size, parts=4):
    step = -(-size // parts)
    return [(k * step, max(0, min(step, size - k * step))) for k in range(parts)]


def local_recorder(sink):
    """Stand-in for persistence.upload's pinned uploader: reads the archive, writes small records only."""
    def record(path, key):
        out = Path(sink) / 'up'
        out.mkdir(parents=True, exist_ok=True)
        rows = []
        size = Path(path).stat().st_size
        with open(path, 'rb') as f:
            for k, (offset, length) in enumerate(ranges(size)):
                h, left = hashlib.sha256(), length
                f.seek(offset)
                while left:
                    b = f.read(min(1 << 24, left))
                    if not b:
                        raise IOError('short read')
                    h.update(b); left -= len(b)
                name = f'{key}.part{k:02d}-of-04'
                row = dict(name=name, offset=offset, bytes=length, sha256=h.hexdigest(), generation='a15-local-sink',
                           uri=NOUPLOAD + str(out / name), local_sink=True, file=str(path))
                (out / (name + '.json')).parent.mkdir(parents=True, exist_ok=True)
                (out / (name + '.json')).write_text(json.dumps(row, sort_keys=True) + '\n')
                rows.append(row)
        return rows
    return record


def save_export(C, model, wrapped, optimizer, cfg, bound, rank, step, sink, ev=None, persist_cfg=None, distributed=True):
    import torch.distributed as dist
    ev = ev or (lambda kind, **kw: None)
    CS = importlib.import_module(PK + '.checkpoint_space')
    P = importlib.import_module('launch_r2.persistence')
    if cfg.get(GX):
        raise ValueError('A15: this rehearsal save does not carry the online history of that mode')
    sink = Path(sink)
    pcfg = dict(cfg if persist_cfg is None else persist_cfg, output=str(sink))
    native_check = CS.check
    guards = []

    def check(*a, **kw):
        try:
            r = native_check(*a, **kw)
        except BaseException as e:
            ev('DISK_GUARD', write=kw.get('kind', 'checkpoint'), directory=str(a[0]), refused=f'{type(e).__name__}: {e}'[:2000])
            raise
        row = dict(write=kw.get('kind', 'checkpoint'), directory=str(a[0]), required_bytes=r['required_bytes'],
                   available_bytes=r['available_bytes'], margin_bytes=r['available_bytes'] - r['required_bytes'],
                   state_tensor_bytes=r['state_tensor_bytes'], export_tensor_bytes=r['export_tensor_bytes'],
                   state_bytes=r['state_bytes'], export_bytes=r['export_bytes'],
                   remaining_full_states=r['remaining_full_states'], remaining_weight_exports=r['remaining_weight_exports'],
                   retained_archive_bytes=r['retained_archive_bytes'], native_remaining_bytes=r['native_remaining_bytes'],
                   policy=r['policy'], completed=r['completed'])
        guards.append(row)
        ev('DISK_GUARD', **row)
        return r

    def stage(name, fn, *a, **kw):
        t = time.time(); ev('BEGIN', stage=name)
        out = fn(*a, **kw)
        ev('END', stage=name, seconds=round(time.time() - t, 3))
        return out

    def persist(directory, kind):
        if 'r2_identity' not in pcfg:
            ev('PERSIST', write=kind, note='milestone() is a no-op without r2_identity, as in the job')
            return
        if 'r2_persistence' not in pcfg:
            P.milestone(pcfg, directory, kind, rank, distributed)      # local_only: archive copy, no uploader
        else:
            result = [None]
            if rank == 0:
                try:
                    P.upload(pcfg, directory, kind, uploader=local_recorder(sink))
                except Exception as error:
                    result[0] = str(error)
            if distributed:
                dist.broadcast_object_list(result, src=0)
            if result[0]:
                raise ValueError('Durable persistence refused: ' + result[0])
        if rank == 0:
            receipts = sorted(str(p) for p in (sink / 'persist').glob('*.json'))
            ev('PERSIST', write=kind, directory=str(directory), receipts=receipts,
               local_only='r2_persistence' not in pcfg)

    CS.check = check
    try:
        budget = CS.Budget(cfg.get('checkpoint_disk_guard'))
        ev('SAVE_BEGIN', step=step, sink=str(sink), policy=cfg.get('checkpoint_disk_guard'))
        if rank == 0:
            sink.mkdir(parents=True, exist_ok=True)
            C.bind_output(sink, bound)          # the binding run_steps' output has (train writes it for a full run)
        if distributed:
            dist.barrier()
        saved = stage('save_checkpoint', C.checkpoint, sink / f'checkpoint_{step:06d}', wrapped, optimizer, bound, step,
                      rotate=True, disk_guard=budget)
        state = Path(saved['path']).parent
        stage('persist_checkpoint', persist, state, 'checkpoint')
        stage('save_export', C.export, sink / f'm{step}', wrapped, model, cfg, step, optimizer=optimizer, disk_guard=budget)
        stage('persist_export', persist, sink / f'm{step}', 'export')
        ev('SAVE_DONE', step=step, state=str(state), export=str(sink / f'm{step}'), guards=len(guards),
           completed=dict(budget.completed))
        return dict(state=state, export=sink / f'm{step}', guards=guards)
    finally:
        CS.check = native_check
