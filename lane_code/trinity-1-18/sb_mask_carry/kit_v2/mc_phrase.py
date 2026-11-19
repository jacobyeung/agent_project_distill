"""S_PHR's detect: fold-specific phrase policies from the phrase kit's PHRASE_FOLDS.json (fold, name, policy), run
through the phrase kit's own pool functions (select, decode, uniform, reader_frames, ArmObjects), loaded by declaration
from sb_mask_phrase/kit.py without executing that module (its imports have side effects).
A policy is one phrase w, or an ordered pair (w1, w2) whose second call runs only when the first returns not seen.
Phrase w's pool: stored instances of the name's record with source_prompt == w, own presence, joint floor, score order,
cap 30; the reader runs with w as the call's name. Names a fold does not list keep the raw name."""
import ast
from types import SimpleNamespace as NS
import numpy as np
import mc_common as C
import mc_ladder as L

NAMES = ('presence_of', 'select', 'decode', 'uniform', 'reader_frames', 'ArmObjects')
_K = None


def kit():
    global _K
    if _K is None:
        tree = ast.parse(C.read(C.PHRASE_KIT).decode())
        keep = [n for n in tree.body if (isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in NAMES)
                or (isinstance(n, ast.Assign) and any('FLOOR' in ast.dump(t) for t in n.targets))]
        scope = dict(np=np, T=L.T())
        exec(compile(ast.Module(keep, []), str(C.PHRASE_KIT), 'exec'), scope)
        _K = NS(**{k: scope[k] for k in NAMES+('FLOOR', 'CAP')})
    return _K


def _policy(value):
    """One policy as a tuple of 1 or 2 phrases, or None when the form is not recognised."""
    if isinstance(value, dict):
        for key in ('phrases', 'policy', 'calls'):
            if key in value:
                return _policy(value[key])
        if 'w1' in value:
            return _policy([value['w1']] + ([value['w2']] if value.get('w2') else []))
        if 'phrase' in value:
            return _policy(value['phrase'])
        return None
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)) and 1 <= len(value) <= 2 and all(isinstance(w, str) and w for w in value):
        return tuple(value)
    return None


def parse(raw):
    """{fold: {name: policy}} from PHRASE_FOLDS.json; raises ValueError on a form it cannot read."""
    if isinstance(raw, dict) and raw.get('bars_passed') is False:
        raise ValueError('PHRASE_FOLDS.json records bars_passed false')
    rows = raw
    if isinstance(raw, dict):
        rows = next((raw[k] for k in ('policies', 'rows', 'entries', 'items', 'folds') if k in raw), None)
        if rows is None:
            raise ValueError(f'no policies list among keys {sorted(raw)[:8]}')
    table = {}
    if isinstance(rows, dict):
        for fold, names in rows.items():
            for name, value in names.items():
                table.setdefault(int(str(fold).lstrip('k')), {})[name] = value
    else:
        for r in rows:
            table.setdefault(int(str(r['fold']).lstrip('k')), {})[r['name']] = r.get('policy', r.get('phrases', r))
    out = {}
    for fold, names in table.items():
        for name, value in names.items():
            p = _policy(value)
            if p is None:
                raise ValueError(f'unreadable policy fold={fold} name={name}: {str(value)[:80]}')
            out.setdefault(fold, {})[name] = p
    if not set(out) <= set(range(5)):
        raise ValueError(f'folds {sorted(out)} outside the ladder folds 0..4')
    return out


def table():
    """(status, {fold: {name: policy}}): NOT_YET while PHRASE_FOLDS.json does not exist, BLOCKED when unreadable."""
    if not C.PHRASE_FOLDS.exists():
        return 'NOT_YET', None
    try:
        return 'PRESENT', parse(C.read_json(C.PHRASE_FOLDS))
    except (ValueError, KeyError, TypeError) as e:
        return f'BLOCKED: {e}', None


def frames_for(cache, name, prompts):
    """The phrase kit's pool for `prompts`: stored instances per anchor, joint floor, score order, cap."""
    K = kit()
    frames = []
    for slot in range(32):
        record = cache['frames'][str(slot)]['phrases'].get(name)
        frames.append([dict(mask=K.decode(p), score=float(p['score']), presence=pres, source_prompt=src)
                       for src, p, pres in K.select(record, name, prompts, K.CAP)])
    return frames


def arm_objects(c, geo, head, gt, cache, name, phrase):
    """ArmObjects bound to phrase's pool for this name, called with the phrase; returns (objects, call). Caller unbinds."""
    K = kit()
    frames = K.uniform(frames_for(cache, name, {phrase}))
    objects = K.ArmObjects(c, geo, head, gt)
    objects.bind(phrase, name, K.reader_frames(frames))
    return objects, phrase
