"""Retain stage assertion operands and addressing records before propagation."""
from dataclasses import fields, is_dataclass
from functools import wraps
from pathlib import Path
from types import SimpleNamespace
from argparse import Namespace
import hashlib
import json
import sys
import time


def snapshot(value, seen=None):
    """Keep JSON operands; identify large arrays without copying model weights."""
    seen = {} if seen is None else seen
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    identity = id(value)
    if identity in seen:
        return {'snapshot_ref': seen[identity]}
    seen = dict(seen)
    seen[identity] = len(seen)
    if isinstance(value, dict):
        return {str(k): snapshot(v, seen) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [snapshot(v, seen) for v in value]
    if isinstance(value, (SimpleNamespace, Namespace)):
        return snapshot(vars(value), seen)
    if is_dataclass(value) and not isinstance(value, type):
        return {f.name: snapshot(getattr(value, f.name), seen) for f in fields(value)}
    # These inputs can be reconstructed from pinned RGB files and stage settings.
    if hasattr(value, 'detach') and hasattr(value, 'shape'):
        t = value.detach().contiguous().cpu()
        import torch
        return dict(type='tensor', shape=list(t.shape), dtype=str(t.dtype),
                    sha256=hashlib.sha256(t.reshape(-1).view(torch.uint8).numpy().tobytes()).hexdigest(),
                    values=t.tolist() if t.numel() <= 64 else None)
    if hasattr(value, 'tobytes'):
        return dict(type=type(value).__name__, dtype=str(getattr(value, 'dtype', getattr(value, 'mode', None))),
                    shape=str(getattr(value, 'shape', getattr(value, 'size', None))),
                    sha256=hashlib.sha256(value.tobytes()).hexdigest())
    return {'type': type(value).__module__ + '.' + type(value).__name__}


def save(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot(payload), allow_nan=True) + '\n')


def stage_assertions(stage):
    """Catch assertions anywhere in a stage, save traceback locals, then re-raise."""
    def decorate(function):
        @wraps(function)
        def run(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except AssertionError as exc:
                out = (Path(args[0].out) if args and hasattr(args[0], 'out') else
                       Path(sys.argv[sys.argv.index('--out') + 1]))
                frames = []
                tb = exc.__traceback__
                while tb:
                    f = tb.tb_frame
                    if f.f_code.co_name != 'run' or f.f_code.co_filename != __file__:
                        frames.append(dict(file=f.f_code.co_filename, line=tb.tb_lineno,
                            function=f.f_code.co_name, inputs={k:v for k,v in f.f_locals.items()
                            if k not in ('model','native','processor','routed_processor','hf_processor','reference','self')}))
                    tb = tb.tb_next
                save(out / f'ASSERTION_STAGE_{stage}_{time.time_ns()}.json',
                     dict(stage=stage, error=str(exc), argv=sys.argv, frames=frames))
                raise
        return run
    return decorate


def addressing_evidence(row, image, config, enabled, image_only=None, video_only=None):
    digest = hashlib.sha256(image.tobytes()).hexdigest()
    queries = enabled['heads'].get('ground_queries', [])
    rows = [dict(name=q['name'], backend=q.get('backend'), **r)
            for q in queries for r in q.get('rows', [])]
    matches = [r for r in rows if r['name'] == row['name'] and r['frame'] == row['anchor_slot']]
    branch = ('zero_rows' if not matches else 'several_rows' if len(matches) != 1 else
              'digest_mismatch' if matches[0]['pixel_sha256'] != digest else 'match')
    return dict(row=row, ground_queries=queries, ground_rows=rows, matches=matches, branch=branch,
                addressed_image_digest=digest, reread_config=config, image_only=image_only,
                video_only=video_only, generation={k: enabled.get(k) for k in
                    ('tokens','text','calls','finish','errors','scripted')})


def check_addressing(evidence):
    row = evidence['row']
    if evidence['branch'] != 'match':
        raise AssertionError('Reread identity differs: ' + evidence['branch'])
    sub = evidence['matches'][0]
    if (sub['backend'] != 'hrp_reread' or sub.get('obj') != row['name'] or
            sub.get('source_index') != row['source_index']):
        raise AssertionError('Reread source/name identity differs')
    if evidence['generation']['finish'] != 'eos' or evidence['generation']['errors']:
        raise AssertionError('Reread generation incomplete')
    if evidence['image_only'] is not None and any(
            sub[k] != evidence['image_only'][k] for k in ('raw_output','parse_status')):
        raise AssertionError('Image-only/reread mismatch')
    return sub
