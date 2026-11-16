"""T0: head-backed v3.14 traces for the DOSE pool's questions on the 355 r16 scenes (GT.npz on this node's /dev/shm).

Runs ground_rows' production scene renderer (render_full.render_scan, v3.14 copy in work/v314) on items built from
pool rows whose scene and 32-frame set equal the r16 registry entry. Each pool question is parsed into roles with the
generator's own parser (VSI-590K paraphrases included) and re-stated in the benchmark's template, as CP2's rows are.
Supports absolute/relative distance, easy/medium/hard direction, count, relative count, and absolute direction.
usage: dose_t0.py --out OUT [--max-scenes N] [--workers W]"""
import argparse
import collections
import gzip
import hashlib
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'derivgen_v7'))
sys.path.insert(1, str(HERE / 'ground_rows_out'))
for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(k, '1')
import render_full as RF  # noqa: E402
from derivgen.ground_v312 import parse_roles, RowRefusal  # noqa: E402
from derivgen.ground_v312_io import reference  # noqa: E402
from test_v312_benchmark import benchmark_templates, expected_question  # noqa: E402

L = '/scratch/jjyeung/orch_cd/dose_pool'
REG = '/scratch/jjyeung/orch_cd/ground_rows/work/inputs/routing356_scenes.json'
CFG = dict(rkit_root='/scratch/jjyeung/orch_cd/ground_rows/work/rkit_v3122',
           tokenizer=dict(path='/scratch/jjyeung/orch_cd/derivgen/inputs/tokenizer_01/tokenizer.json'),
           backend=dict(path='/scratch/jjyeung/orch_cd/ground_rows/work/backend_v3122/ground_lifting.py'))
TO_M = {'mm': 0.001, 'cm': 0.01, 'm': 1.0, 'in': 0.0254, 'ft': 0.3048}


RENAME = os.environ.get('DOSE_RENAME', '1') == '1'
_LAB = {}


def scene_labels(e):
    """id -> GT label of the scene's GT.npz (read once per scene)."""
    p = e['gt']['path']
    if p not in _LAB:
        import numpy as np
        with np.load(p, allow_pickle=False) as z:
            _LAB[p] = {int(i): str(l) for i, l in zip(z['ids'], z['labels'])}
    return _LAB[p]


def rename_roles(roles, typ, rec, labels):
    """Replace a role name by the GT label of the instances the GT program bound to it, when those instances share
    one label that differs from the name (e.g. 'trash bin' -> 'trash can'). Deterministic; the program's ids are the
    agreement-checked identity. Returns (roles, tags)."""
    if not rec or rec.get('status') != 'OK':
        return roles, ['no_program_ids']
    m = rec.get('meta', {})
    names, ids = m.get('names') or [], m.get('ids') or []
    bound = {n: [int(i) for i in v] for n, v in zip(names, ids)}
    for n, (i, _) in next(iter((m.get('option_nearest') or {}).values()), {}).items():
        bound.setdefault(n, [int(i)])
    out, tags = dict(roles), []
    def fix(n):
        v = bound.get(n)
        if not v or any(i not in labels for i in v):
            return n
        labs = {labels[i] for i in v}
        if len(labs) != 1:
            return n
        lab = labs.pop()
        if lab.lower().strip() == n.lower().strip():
            return n
        tags.append('renamed')
        return lab
    for k, v in roles.items():
        out[k] = [fix(x) for x in v] if isinstance(v, list) else fix(v)
    if typ == 'object_rel_distance' and len(set(out['cands'])) != len(out['cands']):
        return roles, ['rename_collision']
    return out, tags or ['unchanged']


def gen_type(r):
    t, n = r['category'], len(r['student_input']['options'])
    if t == 'relative_distance_object':
        return 'object_rel_distance'
    if t == 'absolute_distance_object':
        return 'object_abs_distance'
    if t == 'relative_direction_object':
        return {2: 'object_rel_direction_easy', 3: 'object_rel_direction_medium', 4: 'object_rel_direction_hard'}.get(n)
    return {'absolute_count':'object_counting', 'relative_count':'relative_count',
            'absolute_direction_object':'absolute_direction_object'}.get(t)


def build_items(P, templates, registry=REG):
    sys.path.insert(0, f'{L}/work/dosepool')
    import common as C
    reg = json.load(open(registry))
    by_canon = {v['canonical'].replace('scannetpp/', 'scannetppv2/'): (k, v) for k, v in reg.items()}
    stream = {}
    for l in gzip.open(f'{L}/out/stream9b_v0/ROWS_VQA_ALL.jsonl.gz', 'rt'):
        x = json.loads(l)
        stream[x['qid']] = x
    groups, stat = collections.defaultdict(list), collections.Counter()
    sys.path.insert(0, f'{L}/work/dosepool')
    import program as PG
    prog = PG.load_v0()
    for l in gzip.open(f'{L}/out/pool_v0/ROWS_ALL.jsonl.gz', 'rt'):
        r = json.loads(l)
        canon = '%s/%s' % (r['source_dataset'], r['scene'])
        if canon not in by_canon:
            continue
        scene, e = by_canon[canon]
        s = stream.get(r['qid'])
        if s is None or s['frames_pending']['i'] != e['frame_indices']:
            stat['frames_differ'] += 1
            continue
        typ = gen_type(r)
        stat['t0_rows|' + r['category']] += 1
        if typ is None:
            stat['unsupported|' + r['category'] + ('_easy' if r['category'] == 'relative_direction_object' else '')] += 1
            continue
        si = r['student_input']
        item = dict(qid=r['qid'], type=typ, scene=scene, question=si['question'], options=si['options'],
                    frame_indices=e['frame_indices'])
        try:
            item['roles'] = parse_roles(item, P.T)
            if typ == 'object_counting' and 'cat' in item['roles']:
                item['roles'] = {'obj':item['roles']['cat']}
            if not item['roles']:
                raise RowRefusal('unparsed_question')
            stat['roles_parsed|' + typ] += 1
        except (RowRefusal, ValueError, KeyError, AttributeError):
            # VSI-590K wording the generator's parser does not know: take the roles from the GT program's own
            # parse of the same question (names in question order), which the agreement filter already checked.
            n = (prog.get(r['qid']) or {}).get('meta', {}).get('names') or []
            opts = [o.split('. ', 1)[1] for o in si['options']]
            if typ == 'object_abs_distance' and len(n) == 2:
                item['roles'] = dict(a=n[0], b=n[1])
            elif typ == 'object_rel_distance' and n and set(opts) <= set(n[1:]):
                item['roles'] = dict(target=n[0], cands=opts)
            elif typ in ('object_counting','relative_count') and len(n) == (1 if typ=='object_counting' else 2):
                item['roles'] = dict(zip(['obj'] if typ=='object_counting' else ['a','b'],n))
            elif (typ.startswith('object_rel_direction') or typ == 'absolute_direction_object') and len(n) == 3:
                item['roles'] = dict(stand=n[0], face=n[1], query=n[2])
            else:
                stat['unparsed|' + typ] += 1
                continue
            stat['roles_from_program|' + typ] += 1
        if typ == 'absolute_direction_object':
            from derivgen.gaps_v314 import rotation_sense
            try:
                ccw = rotation_sense(si['question'])
                if bool((prog.get(r['qid']) or {}).get('meta',{}).get('ccw')) != ccw:
                    raise RowRefusal('rotation_sense_mismatch')
                item['roles']['ccw'] = ccw
            except RowRefusal as ex:
                stat['refused|' + typ + '|' + str(ex)] += 1
                continue
        if typ == 'object_abs_distance':
            u = C.question_unit(si['question'])
            item['gt_answer'] = '%.2f' % (float(r['answer']) * TO_M[u])
            item['options'] = []
        else:
            item['gt_answer'] = r['answer']
        if RENAME:
            before = item['roles']
            item['roles'], how = rename_roles(item['roles'], typ, prog.get(r['qid']), scene_labels(e))
            if typ == 'object_rel_distance':
                ren = dict(zip(before['cands'], item['roles']['cands']))
                item['options'] = ['%s. %s' % (o[0], ren.get(o[3:], o[3:])) for o in item['options']]
            for h in how:
                stat['rename|' + typ + '|' + h] += 1
            if 'renamed' in how:
                item['renamed_from_program_ids'] = True
        item['source_question'] = si['question']
        try:
            item['question'] = expected_question(item, templates)
        except (KeyError, ValueError, IndexError) as ex:
            stat['no_template|' + typ] += 1
            continue
        line = json.dumps(r, sort_keys=True).encode()
        item['source_provenance'] = dict(canonical=e['canonical'], alias=e['alias'], pool='dose_v0', pool_qid=r['qid'],
                                         frame_indices=e['frame_indices'], frames_pending=s['frames_pending'])
        item['source_line_sha256'] = hashlib.sha256(line).hexdigest()
        item['source_provenance']['source_row_sha256'] = item['source_line_sha256']  # c1_row reads it
        item['source_join'] = dict(options=list(item['options']), gt_answer=item['gt_answer'])
        item['authority'] = dict(kind='hash-verified-native-geometry', scene_registry=dict(path=REG),
                                 gt=e['gt'], canonical=e['canonical'], frame_indices=e['frame_indices'])
        stat['items|' + typ] += 1
        groups[scene].append(item)
    return groups, reg, stat


def prefilter(task):
    """Drop multiple-choice items whose native independent label differs from the pool's answer: the scene renderer's
    shuffle check raises on such a row and would abort the whole scene. Returns (task, dropped)."""
    from derivgen.ground_v312_io import GTClip, checked
    scene, items, entry, cfg = task[:4]
    P, M, _ = reference(cfg['rkit_root'])
    clip = GTClip(checked(entry['gt']), entry['frame_indices'], P, M)
    keep, dropped = [], collections.Counter()
    for it in items:
        if it['type'] in ('object_abs_distance','object_rel_direction_easy','object_counting','relative_count','absolute_direction_object'):
            keep.append(it); continue
        try:
            label = RF.independent_label(dict(it), clip, P)
        except Exception:  # noqa: BLE001 - render_scan's own gates refuse these rows later
            keep.append(it); continue
        if str(label) != str(it['gt_answer']):
            dropped[it['type'] + '|native_label_disagrees_v0'] += 1
        else:
            keep.append(it)
    return (scene, keep) + tuple(task[2:]), dropped


def run(task):
    try:
        task, dropped = prefilter(task)
        done = RF.render_scan(task)
        done['prefilter_dropped'] = dict(dropped)
        return done
    except Exception as ex:  # noqa: BLE001 - recorded per scene
        return dict(scene=task[0], error=repr(ex)[:400])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--max-scenes', type=int, default=0)
    ap.add_argument('--workers', type=int, default=8)
    ap.add_argument('--registry', default=REG)
    ap.add_argument('--scenes', default='', help='file with one scene per line (rerun subset)')
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=False)
    P, _, _ = reference(CFG['rkit_root'])
    templates = benchmark_templates()
    groups, reg, stat = build_items(P, templates, a.registry)
    splits = json.load(open(RF.SPLITS)); dev = set(splits['all_scenes']); devrooms = {RF.room(s) for s in dev}
    scenes = sorted(groups)[:a.max_scenes or None]
    if a.scenes:
        want = set(open(a.scenes).read().split())
        scenes = [x for x in scenes if x in want]
    run_key = hashlib.sha256(json.dumps(sorted(scenes)).encode()).hexdigest()[:16]
    tasks = []
    for s in scenes:
        e = dict(reg[s]); e['gt'] = dict(path=e['gt']['path'], sha256=e['gt']['sha256'])
        (out / 'scans' / s).mkdir(parents=True)
        tasks.append((s, groups[s], e, CFG, str(out / 'scans' / s), run_key, sorted(dev), sorted(devrooms)))
    json.dump(dict(stat), open(out / 'ITEMS.json', 'w'), indent=1)
    done = []
    with ProcessPoolExecutor(a.workers) as ex:
        for d in ex.map(run, tasks):
            done.append(d)
    json.dump(done, open(out / 'SCANS.json', 'w'), indent=1, default=str)
    agg = collections.Counter()
    for d in done:
        if 'error' in d:
            agg['scene_error'] += 1
            continue
        for t, c in d['counts'].items():
            for k, v in c.items():
                agg[t + '|' + k] += v
        for k, v in d['refused'].items():
            agg['refused|' + k] += v
        for k, v in d.get('prefilter_dropped', {}).items():
            agg['refused|' + k] += v
        for k, v in d['source_label_agreement'].items():
            agg['source_agree|' + k] += v
    json.dump(dict(items=dict(stat), scans=len(done), agg=dict(agg)), open(out / 'SUMMARY.json', 'w'), indent=1)
    print(json.dumps(dict(agg), indent=1))


if __name__ == '__main__':
    main()
