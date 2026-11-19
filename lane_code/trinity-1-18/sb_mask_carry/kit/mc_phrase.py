"""S_PHR's detect: the phrase kit's own pool functions (select, decode, uniform, reader_frames, ArmObjects), loaded by
declaration from sb_mask_phrase/kit.py without executing that module (its imports have side effects)."""
import ast
from types import SimpleNamespace as NS
import numpy as np
import mc_common as C
import mc_ladder as L

KIT = C.PHRASE_SET.parent.parent/'kit.py'
NAMES = ('presence_of', 'select', 'decode', 'uniform', 'reader_frames', 'ArmObjects')
_K = None


def kit():
    global _K
    if _K is None:
        tree = ast.parse(C.read(KIT).decode())
        keep = [n for n in tree.body if (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in NAMES)
                or (isinstance(n, ast.Assign) and any('FLOOR' in ast.dump(t) for t in n.targets))]
        scope = dict(np=np, T=L.T())
        exec(compile(ast.Module(keep, []), str(KIT), 'exec'), scope)
        _K = NS(**{k: scope[k] for k in NAMES+('FLOOR', 'CAP')})
    return _K


def table():
    """PHRASE_SET.json as (status, {name: entry}); every name it does not list keeps its raw name."""
    if not C.PHRASE_SET.exists():
        return 'NOT_YET', None
    raw = C.read_json(C.PHRASE_SET)
    if raw.get('status') != 'frozen':
        return f"NOT_FROZEN: status {raw.get('status')}", None
    entries = {e['name']: e for e in raw['names']}
    bad = sorted({e['variant'] for e in entries.values() if not (e['variant'] == 'raw' or e['variant'].startswith(('q:', 'fb:')))})
    if bad or any(e.get('retention', False) for e in entries.values()):
        return f'BLOCKED: unsupported PHRASE_SET variants {bad} or retention', None
    return 'PRESENT', entries


def frames_for(cache, name, prompts):
    """pools().frames_for of the phrase kit: stored instances of `prompts` per anchor, joint floor, score order, cap."""
    K = kit()
    frames = []
    for slot in range(32):
        record = cache['frames'][str(slot)]['phrases'].get(name)
        frames.append([dict(mask=K.decode(p), score=float(p['score']), presence=pres, source_prompt=src)
                       for src, p, pres in K.select(record, name, prompts, K.CAP)])
    return frames


def pool(cache, name, entry):
    """(frames, call) of the entry's variant: raw, q:<a> (alias a alone, call a) or fb:<a> (raw, alias where raw is empty)."""
    variant = entry['variant'] if entry else 'raw'
    if variant == 'raw':
        return frames_for(cache, name, {name}), name
    alias = variant.split(':', 1)[1]
    q = frames_for(cache, name, {alias})
    if variant.startswith('q:'):
        return q, alias
    raw = frames_for(cache, name, {name})
    return [raw[s] if raw[s] else q[s] for s in range(32)], name


def arm_objects(c, geo, head, gt, cache, name, entry):
    """ArmObjects bound to this name's pool; returns (objects, call). Caller unbinds."""
    K = kit()
    frames, call = pool(cache, name, entry)
    K.uniform(frames)
    objects = K.ArmObjects(c, geo, head, gt)
    objects.bind(call, name, K.reader_frames(frames))
    return objects, call
