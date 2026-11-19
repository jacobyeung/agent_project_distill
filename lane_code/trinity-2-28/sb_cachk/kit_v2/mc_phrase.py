"""S_PHR's detect: fold-specific phrase policies from the phrase kit's PHRASE_FOLDS.json, run through the phrase kit's
own pool functions (select, decode, uniform, reader_frames, ArmObjects), loaded by declaration from sb_mask_phrase/kit.py
without executing that module (its imports have side effects).

Producer schema (sb_mask_phrase/phrase_folds.py): {arm, rule, folds: [{fold, name, policy, phrases}], changed,
bars_sha256, input_sha256}. Each row's `phrases` field is the call sequence; its `policy` label must agree with it:
raw -> [name]; q:w -> [w] (arm W1, one call); call:w -> [name, w] (arm W2c, the spec's ordered pair: w's call runs only
when the raw call returns not seen). W2's fb:w composes pools per frame, which this kit does not implement, so it is
refused. The producer's arm must be its DECISION.json chosen_arm, among shippable_passing, with phrase_worth and
phrase_safe PASS, and bars_sha256 must equal DECISION.json bars_file and the bars file's bytes.
Phrase w's pool: stored instances of the name's record with source_prompt == w, own presence, joint floor, score order,
cap 30; the reader runs with w as the call's name."""
import ast, hashlib, json
from pathlib import Path
from types import SimpleNamespace as NS
import numpy as np
import mc_common as C
import mc_ladder as L

LABELS = {'W1': ('raw', 'q:'), 'W2c': ('raw', 'call:')}

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


def row_phrases(row, arm):
    """The producer row's `phrases` field as a tuple, after checking that its policy label names the same calls."""
    name, label, phrases = row['name'], row['policy'], row['phrases']
    if not (isinstance(name, str) and name and isinstance(label, str)):
        raise ValueError(f'row without a name or policy label: {str(row)[:80]}')
    if not (isinstance(phrases, list) and 1 <= len(phrases) <= 2 and all(isinstance(w, str) and w for w in phrases)):
        raise ValueError(f'fold={row["fold"]} name={name}: phrases must list one or two non-empty strings')
    if label == 'raw':
        expect = [name]
    elif label.startswith('q:') and 'q:' in LABELS[arm]:
        expect = [label[2:]]
    elif label.startswith('call:') and 'call:' in LABELS[arm]:
        expect = [name, label[5:]]
    else:
        raise ValueError(f'fold={row["fold"]} name={name}: policy {label!r} is not a call-level policy of arm {arm}')
    if phrases != expect:
        raise ValueError(f'fold={row["fold"]} name={name}: phrases {phrases} disagree with policy {label!r}')
    return tuple(phrases)


def producer(raw):
    """Checks the producer's arm, passing decision and bars hash; returns the provenance mc_seeds records."""
    if raw.get('bars_passed') is False:
        raise ValueError('PHRASE_FOLDS.json records bars_passed false')
    arm = raw.get('arm')
    if arm not in LABELS:
        raise ValueError(f'arm {arm!r}: this kit implements call-level policies of arms {sorted(LABELS)} only')
    pins = raw['input_sha256']
    paths = [p for p in pins if Path(p).name == 'DECISION.json']
    if len(paths) != 1:
        raise ValueError('input_sha256 must name exactly one DECISION.json')
    decision_path = paths[0]
    decision_bytes = C.read(decision_path)
    if hashlib.sha256(decision_bytes).hexdigest() != pins[decision_path]:
        raise ValueError('DECISION.json bytes differ from the sha256 PHRASE_FOLDS.json recorded')
    decision = json.loads(decision_bytes)
    if decision.get('chosen_arm') != arm:
        raise ValueError(f'DECISION.json chose {decision.get("chosen_arm")!r}, not {arm!r}')
    if arm not in decision.get('shippable_passing', []):
        raise ValueError(f'{arm} is not among the passing arms {decision.get("shippable_passing")}')
    bars = decision['bars'][arm]
    failed = [k for k in ('phrase_worth', 'phrase_safe') if bars[k]['verdict'] != 'PASS']
    if failed:
        raise ValueError(f'{arm} did not pass {failed}')
    bars_file = decision['bars_file']
    bars_sha = hashlib.sha256(C.read(bars_file['path'])).hexdigest()
    if not (raw['bars_sha256'] == bars_file['sha256'] == bars_sha):
        raise ValueError(f'bars sha256 differ: PHRASE_FOLDS {raw["bars_sha256"][:12]}, DECISION {bars_file["sha256"][:12]}, '
                         f'file {bars_sha[:12]}')
    return dict(arm=arm, decision=decision_path, decision_sha256=pins[decision_path], bars_file=bars_file['path'],
                bars_sha256=bars_sha, phrase_worth=bars['phrase_worth']['verdict'], phrase_safe=bars['phrase_safe']['verdict'])


def parse(raw, check_producer=True):
    """{fold: {name: phrases}} from the producer's PHRASE_FOLDS.json; raises ValueError on anything else."""
    if not isinstance(raw, dict) or not isinstance(raw.get('folds'), list):
        raise ValueError(f'PHRASE_FOLDS.json is not the producer schema (keys {sorted(raw)[:8] if isinstance(raw, dict) else type(raw)})')
    arm = raw.get('arm')
    if check_producer:
        producer(raw)
    elif arm not in LABELS:
        raise ValueError(f'arm {arm!r}: this kit implements call-level policies of arms {sorted(LABELS)} only')
    out = {}
    for r in raw['folds']:
        fold = r['fold']
        if not (isinstance(fold, int) and 0 <= fold < 5):
            raise ValueError(f'fold {fold!r} outside the ladder folds 0..4')
        if r['name'] in out.get(fold, {}):
            raise ValueError(f'fold={fold} name={r["name"]} listed twice')
        out.setdefault(fold, {})[r['name']] = row_phrases(r, arm)
    if sorted(out) != list(range(5)) or len({frozenset(v) for v in out.values()}) != 1:
        raise ValueError('PHRASE_FOLDS.json must list the same names in each of the folds 0..4')
    return out


def table():
    """(status, {fold: {name: phrases}}, provenance): NOT_YET while no fold file exists, BLOCKED when it fails a check.
    Provenance names the file and its sha256 so the preflight can compare it with the file staged beside the seeds."""
    path = C.PHRASE_FOLDS
    if not path.exists():
        return 'NOT_YET', None, dict(path=str(path), sha256=None)
    data = C.read(path)
    prov = dict(path=str(path), sha256=hashlib.sha256(data).hexdigest())
    try:
        raw = json.loads(data)
        prov.update(producer(raw))
        return 'PRESENT', parse(raw, check_producer=False), prov
    except (ValueError, KeyError, TypeError) as e:
        return f'BLOCKED: {e}', None, prov


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
