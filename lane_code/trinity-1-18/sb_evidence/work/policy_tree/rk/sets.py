"""Question-only inference inputs and scorer-only answers."""
import argparse
from functools import lru_cache
import json
from pathlib import Path
import re
import subprocess
import sys

DEV = Path('/scratch/jjyeung/orch_cd/evalx/work/devpool/DEV_ITEMS.jsonl')
MEMBERS = Path('/scratch/jjyeung/orch_cd/revsi_dev/MEMBERSHIP_REVSI_DEV_cap71.json')
PARQUET = Path('/data2/jjyeung/agent_project_data/external_benchmarks/revsi/ground_truth_metadata/32_frame.parquet')
CACHE = Path(__file__).parent / 'data/revsi_cap71_rows.json'
PLANNER = '/scratch/jjyeung/envs/planner_local_v1/bin/python'
DEV_TYPES = ('object_rel_direction_medium', 'object_rel_direction_hard',
             'object_abs_distance', 'object_rel_distance')
REVSI_TYPES = ('object_rel_direction', 'object_abs_distance',
               'object_rel_distance', 'object_size_estimation')


def tplib():
    sys.path.insert(0, '/scratch/jjyeung/orch_cd/evalx/work/tp')
    import tplib as T
    return T


def label(name):
    from .ground import mdg
    return mdg().label(name)


def clean(name):
    return re.sub(r'^(?:the|a|an)\s+', '', name.strip(), flags=re.I).strip(' .?')


def options_of(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except ValueError:
            raw = raw.splitlines()
    if isinstance(raw, dict):
        return [f'{k}. {v}' for k, v in raw.items()]
    return [str(v) if re.match(r'^[A-Z]\.', str(v)) else f'{chr(65+i)}. {v}'
            for i, v in enumerate(raw)]


def parse_revsi(row):
    """Parse roles from question text and options, without annotation fields."""
    text, typ = row['question'], row.get('type', row.get('question_type', ''))
    opts = options_of(row.get('options', []))
    if typ.startswith('object_rel_direction'):
        m = re.search(r'standing (?:by|at|near|next to) (.+?) and facing (.+?), (?:is|where is) (.+?) (?:to my\b|relative to\b)', text, re.I)
        if not m:
            raise ValueError('Unrecognized ReVSI direction question: '+text)
        stand, face, query = m.groups()
        away = bool(re.match(r'(?:in )?the opposite direction of ', face, re.I))
        face = re.sub(r'^(?:in )?the opposite direction of ', '', face, flags=re.I)
        roles = dict(stand=clean(stand), face=clean(face), query=clean(query), away=away,
                     hard=('hard' in typ or any('front' in o.lower() for o in opts)))
        objects = [roles[k] for k in ('stand', 'face', 'query')]
    elif typ.startswith('object_abs_distance'):
        m = re.search(r'distance between (.+?) and (.+?)(?:\s*\(|\?|\.|$)', text, re.I)
        if not m:
            raise ValueError('Unrecognized ReVSI absolute distance question: '+text)
        roles = dict(zip(('a', 'b'), map(clean, m.groups())))
        objects = [roles['a'], roles['b']]
    elif typ.startswith('object_rel_distance'):
        m = re.search(r'(?:closest|farthest|furthest) (?:to|from) (.+?)(?:\?|\.|$)', text, re.I)
        if not m:
            raise ValueError('Unrecognized ReVSI relative distance question: '+text)
        cands = [clean(s) for s in tplib().option_texts(opts).values()]
        roles = dict(target=clean(m.group(1)), cands=cands,
                     farthest=bool(re.search(r'farthest|furthest', text, re.I)))
        objects = [roles['target'], *cands]
    elif typ.startswith('object_size_estimation'):
        m = re.search(r'dimension\s*\(length, width, or height\) of (.+?), measured', text, re.I)
        if not m:
            raise ValueError('Unrecognized ReVSI size question: '+text)
        roles = dict(a=clean(m.group(1)))
        objects = [roles['a']]
    else:
        raise ValueError('Unsupported ReVSI type: '+typ)
    return dict(objects=objects, options=opts, roles=roles)


@lru_cache(maxsize=1)
def _dev_rows():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('rk/sets.py:_dev_rows')
    return [json.loads(s) for s in DEV.read_text().splitlines() if s.strip()]


@lru_cache(maxsize=1)
def _revsi_rows():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('rk/sets.py:_revsi_rows')
    if not CACHE.exists():
        raise FileNotFoundError(f'{CACHE}; run python -m rk.sets cache-revsi')
    return json.loads(CACHE.read_text())


def dev_items():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('rk/sets.py:dev_items')
    return [dict(qid=str(r['id']), set='dev', type=r['question_type'], dataset=r['dataset'],
                 scene=r['scene_name'], question=r['question'], options=list(r['options']))
            for r in _dev_rows() if r['question_type'] in DEV_TYPES]


def revsi_items():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('rk/sets.py:revsi_items')
    out = []
    for r in _revsi_rows():
        typ = r.get('category', r['question_type'])
        if typ not in REVSI_TYPES:
            continue
        item = dict(qid=str(r['qid']), set='revsi', type=typ, dataset=r['dataset'],
                    scene=str(r.get('scene', r.get('scene_name'))), question=r['question'])
        parsed = parse_revsi(dict(question=r['question'], type=r['question_type'], options=r.get('options')))
        item.update({k: parsed[k] for k in ('objects', 'options')})
        out.append(item)
    return out


def answers(which):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('rk/sets.py:answers')
    rows = _dev_rows() if which == 'dev' else _revsi_rows() if which == 'revsi' else None
    if rows is None:
        raise ValueError(which)
    return {str(r.get('qid', r.get('id'))): r['ground_truth'] for r in rows}


def labels(item):
    if item.get('set') == 'revsi' or 'objects' in item:
        objs = item.get('objects') or parse_revsi(item)['objects']
    else:
        p = tplib().parse_vsi(dict(question_type=item['type'], question=item['question']))
        objs = [v for value in p.values() for v in (value if isinstance(value, list) else [value])]
    return sorted(set(map(label, objs)))


def cache_revsi():
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('rk/sets.py:cache_revsi')
    if CACHE.exists():
        raise FileExistsError(CACHE)
    if Path(sys.executable).parent != Path(PLANNER).parent:
        subprocess.run([PLANNER, '-B', '-m', 'rk.sets', 'cache-revsi'], check=True)
        return
    import pyarrow.parquet as pq
    members = json.loads(MEMBERS.read_text())
    by_id = {str(r['qid']): r for r in members}
    rows = pq.read_table(PARQUET).to_pylist()
    selected = []
    for row in rows:
        qid = str(row.get('qid', row.get('id')))
        if qid in by_id:
            selected.append(dict(row, **{k: by_id[qid][k] for k in ('qid', 'category', 'dataset', 'scene')}))
    if len(selected) != len(by_id):
        raise ValueError(f'Cache membership mismatch: {len(selected)} != {len(by_id)}; columns {list(rows[0])}')
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open('x') as stream:
        json.dump(selected, stream, indent=2, default=str)
    print(f'Cached {len(selected)} rows at {CACHE}')


def scene_labels(which):
    from student_pilot.r2_policy import unsupported_entry
    unsupported_entry('rk/sets.py:scene_labels')
    from .anchors import scene_key
    out = {}
    for item in dev_items() if which == 'dev' else revsi_items():
        out.setdefault(scene_key(item['dataset'], item['scene']), set()).update(labels(item))
    return {k: sorted(v) for k, v in sorted(out.items())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['cache-revsi', 'labels'])
    parser.add_argument('--set', choices=['dev', 'revsi'])
    parser.add_argument('--out')
    args = parser.parse_args()
    if args.command == 'cache-revsi':
        cache_revsi()
    else:
        Path(args.out).write_text(json.dumps(scene_labels(args.set), indent=1) + '\n')
