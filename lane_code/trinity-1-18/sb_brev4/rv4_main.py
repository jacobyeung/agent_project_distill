"""Reviewer checks for sb_rowB4: validators, identities, field diff, rooms, balance vs B3, REMOVE lists, MISSING, claims.
Imports only N's sealed W19 tree; never the builder's code."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[k] = '1'
import collections as C
import hashlib
import json
import math
import re
import sqlite3
import sys
import tarfile
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_brev4')
OUT = W / 'out'
B4 = Path('/scratch/jjyeung/orch_n30/sb_rowB4')
B3 = Path('/scratch/jjyeung/orch_n30/sb_rowB3')
B2 = Path('/scratch/jjyeung/orch_n30/sb_rowB2')
KEY = 'sb_rowB4'
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
SEAL = TREE.parents[1] / 'out/TREE_SEAL.json'
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
CFG = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
NJSON = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json')
DEV_S1 = B4 / 'inputs/dev_scene_exclusions.json'
GT_DIR = B2 / 'inputs/gt'
FAMS = ['camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3',
        'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf', 'obj_obj_relative_pos_ud']
NOPT = {'camera_obj_rel_dist_v1': 4, 'camera_obj_rel_dist_v2': 3}
sys.path.insert(0, str(TREE))
from student_pilot.trace_grammar import validate_row
from student_pilot.carrier_c1_routing import direct_row
from student_pilot.r2_grammar import validate_direct
from student_pilot.r1_training import row_check
from student_pilot.r2_contract import validate as r2_validate
from student_pilot.r1_rooms import Rooms
from student_pilot.r2_withheld import Withheld
from student_pilot.row_removals import Removals
from generator.derivgen_v7.derivgen.ground_v312_quality import candidate_identity


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def jl(p):
    with open(p) as f:
        return [json.loads(s) for s in f if s.strip()]


def nopt(fam):
    return NOPT.get(fam, 2)


def sem_of(r):
    return r['student_input']['options'][ord(r['answer']) - 65].split('. ', 1)[1]


def diff_paths(a, b, prefix=''):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in set(a) | set(b):
            p = prefix + ('.' if prefix else '') + k
            if k not in a or k not in b:
                out.append(p)
            else:
                out += diff_paths(a[k], b[k], p)
        return out
    return [] if a == b else [prefix]


def norm_name(x):
    ds, rest = x.split('/', 1)
    ds = {'d1': 'scannet', 'd2': 'scannetpp', 'd3': 'arkitscenes', 'scannetppv2': 'scannetpp'}.get(ds, ds)
    return ds + '/' + rest


def expand(names):
    out = set()
    for x in names:
        if not isinstance(x, str) or '/' not in x:
            continue
        n = norm_name(x)
        out.add(n)
        if n.startswith('scannet/scene'):
            out.add(re.sub(r'_\d\d$', '', n))
    return out


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def cell(r):
    """(stratum, category) of a row: camera = tied/untied first-seen x winner rank by (first_seen, id); pair = subject earlier/later/tied x semantic."""
    p = r['provenance']
    fs = p['first_seen']
    s = sem_of(r)
    if r['question_type'].startswith('camera_'):
        order = sorted(p['instances'], key=lambda o: (fs[o['label']], o['id']))
        rank = [o['label'] for o in order].index(s) + 1
        return ('tied' if len(set(fs.values())) < len(fs) else 'untied', str(rank))
    a, b = [fs[o['label']] for o in p['instances']]
    return ('earlier' if a < b else 'later' if a > b else 'tied', s)


def skeleton(t):
    """Target with the sighting wording removed: Step-1 rule sentence, 'last seen' clauses, first-appearance steps; steps renumbered."""
    out = []
    for l in t.split('\n'):
        m = re.match(r'Step \d+: (.*)$', l)
        if not m:
            out.append(l)
            continue
        body = m[1]
        if body.startswith('for the object instance labelled '):
            continue
        body = re.sub(r'^(take the camera viewpoint of frame \d+ of 32\.).*$', r'\1', body)
        body = re.sub(r'; it was last seen in frame \d+(?: \([^)]*\))?;', ';', body)
        out.append(f'Step {sum(1 for x in out if x.startswith("Step ")) + 1}: ' + body)
    return '\n'.join(out)


def balance(rows, label):
    """Exact-cell check and the plan rule (per stratum every cell = ceil(max category sources / nopt)) on the delivered sources."""
    out = {}
    for fam in FAMS:
        xs = [r for r in rows if r['question_type'] == fam]
        n = nopt(fam)
        cells = C.Counter(cell(r) + (r['answer'],) for r in xs)
        srcs = {}
        for r in xs:
            srcs[r['provenance'][label]['source_qid']] = cell(r)
        groups = C.Counter(srcs.values())
        strata = sorted({a for a, _ in groups})
        per = {}
        rule_ok = True
        for a in strata:
            cats = sorted(b for x, b in groups if x == a)
            vals = {cells[(a, b, chr(65 + i))] for b in cats for i in range(n)}
            want = math.ceil(max(groups[(a, b)] for b in cats) / n)
            per[a] = dict(cell_counts=sorted(vals), categories=len(cats), rule_count=want)
            rule_ok &= vals == {want}
        pos = C.Counter(r['answer'] for r in xs)
        semc = C.Counter(sem_of(r) for r in xs)
        d = dict(rows=len(xs), sources=len(srcs), strata=per, exact_cells_follow_rule=rule_ok,
                 position=dict(sorted(pos.items())), last_option_share=round(pos[chr(64 + n)] / max(1, len(xs)), 4),
                 position_uniform=len(set(pos.values())) == 1 and len(pos) == n)
        if fam.startswith('camera_'):
            unt = [r for r in xs if cell(r)[0] == 'untied']
            fsmin = lambda r: r['provenance']['first_seen'][sem_of(r)] == min(r['provenance']['first_seen'].values())
            d['untied_earliest_wins'] = round(sum(fsmin(r) for r in unt) / max(1, len(unt)), 4)
            d['rank_counts'] = dict(sorted(C.Counter('|'.join(cell(r)) for r in xs).items()))
        else:
            d['semantic'] = dict(sorted(semc.items()))
            d['position_x_semantic'] = dict(sorted(C.Counter(r['answer'] + '|' + sem_of(r) for r in xs).items()))
        out[fam] = d
    return out


def main():
    OUT.mkdir(exist_ok=True)
    res = {}
    pins = {}
    seal = json.loads(SEAL.read_text())
    mism = []
    for m in list(sys.modules.values()):
        p = getattr(m, '__file__', None)
        if p and p.startswith(str(TREE)):
            rel = str(Path(p).relative_to(TREE))
            if seal['files'].get(rel) != sha(p):
                mism.append(rel)
    res['tree'] = dict(tree_sha256=seal.get('tree_sha256'), loaded_modules_mismatch=mism)

    pins[str(STORE / 'vqa/rows.sqlite')] = sha(STORE / 'vqa/rows.sqlite')
    con = sqlite3.connect('file:' + str(STORE / 'vqa/rows.sqlite') + '?mode=ro', uri=True)
    store_qid, store_cid = set(), set()
    for q, c in con.execute("select json_extract(row,'$.qid'), json_extract(row,'$.candidate_id') from rows"):
        store_qid.add(q)
        if c:
            store_cid.add(c)
    ranges = json.loads((STORE / 'FAMILY_INDEX_RANGES.json').read_text())['families']
    src = {}
    for fam in FAMS:
        for a, b in ranges[fam]:
            for (s,) in con.execute('select row from rows where i between ? and ?', (a, b)):
                r = json.loads(s)
                assert r['question_type'] == fam
                src[r['qid']] = r
    con.close()
    census = C.Counter(r['question_type'] for r in src.values())
    res['store'] = dict(sha256=pins[str(STORE / 'vqa/rows.sqlite')], rows=len(store_qid), census=dict(census))

    rows = jl(B4 / 'out/rows.jsonl')
    pins[str(B4 / 'out/rows.jsonl')] = sha(B4 / 'out/rows.jsonl')
    b3rows = jl(B3 / 'out/rows.jsonl')
    b2rows = jl(B2 / 'out/rows.jsonl')
    b2_qid = {r['qid'] for r in b2rows}
    b2_cid = {r['candidate_id'] for r in b2rows}
    b3_qid = {r['qid'] for r in b3rows}
    b3_cid = {r['candidate_id'] for r in b3rows}
    fam_rows = C.Counter(r['question_type'] for r in rows)
    srcq = [r['provenance'][KEY]['source_qid'] for r in rows]
    replaced = set(srcq)
    b3_replaced = {r['provenance']['sb_rowB3']['source_qid'] for r in b3rows}

    # --- validators on every new row and every source
    def run_validators(r):
        errs = []
        try:
            e = validate_row(r)
            if e:
                errs.append('trace_grammar:' + ','.join(sorted({x.rule_id for x in e})))
        except Exception as ex:
            errs.append('trace_grammar_exc:' + str(ex)[:60])
        try:
            p = direct_row(r)
            if p['target'] != r['target'] or p['routing']['answer'] != r['answer']:
                errs.append('direct_row_mismatch')
        except Exception as ex:
            errs.append('direct_row:' + str(ex)[:60])
        try:
            if validate_direct(r['target'], r['student_input']['question'], 32) != r['answer']:
                errs.append('validate_direct_answer')
        except Exception as ex:
            errs.append('validate_direct:' + str(ex)[:60])
        for name, fn in (('row_check', lambda: row_check(r, 'vqa')), ('r2_contract', lambda: r2_validate(r, 'vqa'))):
            try:
                fn()
            except Exception as ex:
                errs.append(name + ':' + str(ex)[:60])
        return errs
    vfail_new = C.Counter(e for r in rows for e in run_validators(r))
    vfail_src = C.Counter(e for r in src.values() for e in run_validators(r))
    res['validators'] = dict(new_rows=len(rows), new_failures=dict(vfail_new), sources=len(src), source_failures=dict(vfail_src))
    print('validators', res['validators'], flush=True)

    # --- identities
    qids = [r['qid'] for r in rows]
    cids = [r['candidate_id'] for r in rows]
    cid_bad = 0
    for r in rows:
        si = r['student_input']
        ci = dict(qid=r['qid'], scene=r['scene'], frame_indices=si['frame_indices'], type=r['question_type'],
                  question=si['question'], options=si['options'], trace_revision='3.14')
        cid_bad += candidate_identity(ci) != r['candidate_id']
    res['identity'] = dict(rows=len(rows), unique_qids=len(set(qids)), unique_candidate_ids=len(set(cids)),
                           qid_in_store=len(set(qids) & store_qid), qid_in_b2=len(set(qids) & b2_qid), qid_in_b3=len(set(qids) & b3_qid),
                           cid_in_store=len(set(cids) & store_cid), cid_in_b2=len(set(cids) & b2_cid), cid_in_b3=len(set(cids) & b3_cid),
                           cid_formula_mismatch=cid_bad, sources_not_in_store=len(replaced - set(src)))

    # --- field diff vs source
    allowed = {'qid', 'candidate_id', 'answer', 'target', 'student_input.question', 'student_input.options', 'provenance.' + KEY}
    paths = C.Counter()
    bad_rows = 0
    other = C.Counter()
    for r in rows:
        s = src[r['provenance'][KEY]['source_qid']]
        d = diff_paths(r, s)
        paths.update(d)
        bad_rows += bool(set(d) - allowed)
        fam = r['question_type']
        if sorted(x.split('. ', 1)[1] for x in s['student_input']['options']) != sorted(x.split('. ', 1)[1] for x in r['student_input']['options']):
            other['option_set_changed'] += 1
        if [x[:3] for x in r['student_input']['options']] != [f'{chr(65+i)}. ' for i in range(nopt(fam))]:
            other['option_letters_bad'] += 1
        if sem_of(r) != sem_of(s):
            other['semantic_answer_changed'] += 1
        if fam.startswith('camera_'):
            m = re.search(r'\(([^()]+)\)', r['student_input']['question'])
            if m[1].split(', ') != [x.split('. ', 1)[1] for x in r['student_input']['options']]:
                other['question_list_neq_options'] += 1
            if re.sub(r'\([^()]+\)', '()', r['student_input']['question']) != re.sub(r'\([^()]+\)', '()', s['student_input']['question']):
                other['camera_template_changed'] += 1
        elif r['student_input']['question'] != s['student_input']['question']:
            other['pair_question_changed'] += 1
    res['field_diff'] = dict(paths=dict(paths), rows_with_disallowed_paths=bad_rows, other=dict(other))

    # --- room rule
    cfg = json.loads(CFG.read_text())
    rooms = Rooms(cfg['r1_training']['room_authority'])
    wh = Withheld()
    pins[str(DEV_S1)] = sha(DEV_S1)
    bench_p = Path(cfg['benchmark_scene_exclusions']['path'])
    pins[str(bench_p)] = sha(bench_p)
    devm_p = Path(cfg['dev_scene_exclusions']['path'])
    pins[str(devm_p)] = sha(devm_p)
    wh_p = TREE / 'student_pilot/r2_withheld.json'
    pins[str(wh_p)] = sha(wh_p)
    assert pins[str(DEV_S1)].startswith('969cdb56') and pins[str(bench_p)].startswith('3119aa4a') and pins[str(wh_p)].startswith('634820b4')
    dev = json.loads(DEV_S1.read_text())
    bench = json.loads(bench_p.read_text())
    devm = json.loads(devm_p.read_text())
    whd = json.loads(wh_p.read_text())
    sets = {
        'dev_s1_969cdb56': expand(strings({k: dev[k] for k in ('aliases', 'canonical', 'natives', 'physical_groups', 'rooms')})),
        'bench_v2_3119aa4a': expand(list(bench['scenes']) + list(bench['physical_groups']) + ['/'.join(t) for t in bench['rung1_tokens']]
                                    + [v['group'] for v in bench['members'].values()]),
        'withheld80_634820b4': expand(list(strings(whd['aliases'])) + list(whd['rooms'])),
        'n_dev_merged_a1869ae2': expand(strings({k: devm[k] for k in ('aliases', 'canonical', 'natives', 'physical_groups', 'rooms')})),
    }

    def room_hits(r):
        status, canonical, _ = rooms.status(r)
        hits = [] if status == 'ok' else [status]
        names = {r['dataset'] + '/' + r['scene']}
        if canonical:
            names.add(canonical)
            try:
                names.add(rooms.room(canonical))
            except ValueError:
                hits.append('room_unresolved')
        names = expand(names)
        hits += [k for k, v in sets.items() if names & v]
        if wh.touches(r, {}):
            hits.append('withheld80_native')
        return hits
    room_new = C.Counter(h for r in rows for h in room_hits(r))
    room_src = C.Counter(h for r in src.values() for h in room_hits(r))
    rem = Removals(cfg['remove_files'])
    rem_src = C.Counter()
    rem_src_q = C.defaultdict(set)
    for q, r in src.items():
        for i in rem.match(r):
            name = Path(cfg['remove_files'][i]['path']).name
            rem_src[name] += 1
            rem_src_q[name].add(q)
    rem_new = sum(bool(rem.match(r)) for r in rows)
    res['rooms'] = dict(new_row_hits=dict(room_new), source_hits=dict(room_src), k1_heldout_rooms=len(rooms.k1),
                        r0_union_rooms=len(rooms.r0), set_sizes={k: len(v) for k, v in sets.items()},
                        n_remove_lists_source_hits=dict(rem_src), n_remove_lists_replaced_source_hits={k: len(v & replaced) for k, v in rem_src_q.items()},
                        n_remove_lists_new_row_hits=rem_new)

    # --- balance (own cell definition), B4 and B3 under the same rule
    res['balance'] = dict(after_b4=balance(rows, KEY), b3=balance(b3rows, 'sb_rowB3'))

    # --- B4 vs B3: dropped sources, same (source, position) => same question/options/target skeleton
    njson = jl(NJSON)
    n_outside = {x['row_key'] for x in njson if x['reason'] == 'outside_native_training_division'}
    dropped = b3_replaced - replaced
    b3_by = {(r['provenance']['sb_rowB3']['source_qid'], r['answer']): r for r in b3rows}
    cmp = C.Counter()
    ex = []
    for r in rows:
        k = (r['provenance'][KEY]['source_qid'], r['answer'])
        o = b3_by.get(k)
        if o is None:
            cmp['b4_position_not_in_b3'] += 1
            continue
        cmp['matched'] += 1
        cmp['question_options_equal'] += o['student_input']['question'] == r['student_input']['question'] and o['student_input']['options'] == r['student_input']['options']
        same = skeleton(o['target']) == skeleton(r['target'])
        cmp['target_equal_outside_sighting_wording'] += same
        if not same and len(ex) < 3:
            ex.append(dict(qid=r['qid'], b3=skeleton(o['target']), b4=skeleton(r['target'])))
        cmp['other_fields_equal'] += not (set(diff_paths(r, o)) - {'qid', 'candidate_id', 'target', 'provenance.' + KEY, 'provenance.sb_rowB3'})
    res['vs_b3'] = dict(b3_rows=len(b3rows), b3_sources=len(b3_replaced), b4_sources=len(replaced), b4_minus_b3=len(replaced - b3_replaced),
                        dropped=len(dropped), dropped_all_in_n_outside=dropped <= n_outside, dropped_scenes=len({src[q]['dataset'] + '/' + src[q]['scene'] for q in dropped}),
                        b3_sources_in_n_outside=len(b3_replaced & n_outside), b4_sources_in_n_outside=len(replaced & n_outside),
                        comparison=dict(cmp), mismatch_examples=ex,
                        source_use_b4=dict(sorted(C.Counter(C.Counter(srcq).values()).items())),
                        source_use_b3=dict(sorted(C.Counter(C.Counter(r['provenance']['sb_rowB3']['source_qid'] for r in b3rows).values()).items())))

    # --- MISSING rasters: own determination from each source's raster pin
    have = {}
    for s in src.values():
        h = s['provenance']['raster_sha256']
        if h in have:
            continue
        p = GT_DIR / (h + '.npz')
        orig = Path(s['provenance']['raster'])
        have[h] = (p.is_file() and sha(p) == h) or (orig.is_file() and sha(orig) == h)
    missing_src = {q for q, s in src.items() if not have[s['provenance']['raster_sha256']]}
    refusals = json.loads((B3 / 'out/REFUSALS.json').read_text())['rows']
    wording_ref_b3 = {q for q, w in refusals.items() if any('wording' in x for x in w)}
    res['missing'] = dict(rasters_total=len(have), rasters_missing=sum(not v for v in have.values()), sources_missing=len(missing_src),
                          replaced_intersect_missing=len(replaced & missing_src),
                          by_family={f: sum(src[q]['question_type'] == f for q in missing_src) for f in FAMS})

    # --- REMOVE lists: exact sets, compact n.json bytes, schema, field values, N loader
    nkeys = set(json.loads(NJSON.read_text().splitlines()[0]))
    compact = lambda l: l == json.dumps(json.loads(l), sort_keys=True, separators=(',', ':'))
    lists = {}
    rl = {}
    for name in ('REMOVE.json', 'REMOVE_WORDING.json', 'REMOVE_MISSING_GT.json'):
        p = B4 / 'out' / name
        raw = p.read_text().splitlines()
        items = [json.loads(l) for l in raw]
        keys = [x['row_key'] for x in items]
        lists[name] = set(keys)
        fields_ok = sum(x['row_key'] in src and x['pool'] == src[x['row_key']]['pool'] and x['question_type'] == src[x['row_key']]['question_type']
                        and x['scene'] == src[x['row_key']]['dataset'] + '/' + src[x['row_key']]['scene'] for x in items)
        try:
            Removals([dict(path=str(p), sha256=sha(p))])
            loads = True
        except Exception as e:
            loads = 'ERR ' + str(e)[:80]
        rl[name] = dict(rows=len(items), unique=len(set(keys)), compact_sorted_like_n=all(compact(l) for l in raw), schema_ok=all(set(x) == nkeys for x in items),
                        fields_match_store=fields_ok, reasons=dict(C.Counter(x['reason'] for x in items)),
                        by_family=dict(C.Counter(x['question_type'] for x in items)), sha256=sha(p), n_removals_loader=loads,
                        overlap_n_lists={k: len(set(keys) & v) for k, v in rem_src_q.items()})
    allsrc = set(src)
    part = [lists['REMOVE.json'], lists['REMOVE_WORDING.json'], lists['REMOVE_MISSING_GT.json'], dropped]
    rl['exact'] = dict(remove_equals_delivered_sources=lists['REMOVE.json'] == replaced,
                       missing_equals_own_missing=lists['REMOVE_MISSING_GT.json'] == missing_src,
                       wording_equals_b3_wording_refusals=lists['REMOVE_WORDING.json'] == wording_ref_b3,
                       wording_equals_rest=lists['REMOVE_WORDING.json'] == allsrc - replaced - missing_src - dropped,
                       pairwise_disjoint=sum(map(len, part)) == len(set().union(*part)), union_is_all_sources=set().union(*part) == allsrc,
                       n_json_compact=all(compact(l) for l in NJSON.read_text().splitlines()))
    res['remove'] = rl

    # --- claims vs files
    claims = {}
    tar_p = B4 / 'out/sb_rowB4.tar'
    claims['tar_sha256'] = sha(tar_p)
    claims['tar_sha_matches_SHA256SUMS'] = (B4 / 'out/SHA256SUMS').read_text().split()[0] == claims['tar_sha256']
    with tarfile.open(tar_p) as t:
        names = t.getnames()
        mem = {n: hashlib.sha256(t.extractfile(n).read()).hexdigest() for n in names
               if n.endswith(('rows.jsonl', 'REMOVE.json', 'REMOVE_WORDING.json', 'REMOVE_MISSING_GT.json', 'QID_MAP.jsonl', 'CHECKS.json', 'REPORT.md'))}
    claims['tar_members'] = len(names)
    claims['tar_member_hashes_match_out'] = {n: h == sha(B4 / 'out' / Path(n).name) for n, h in mem.items()}
    chk = json.loads((B4 / 'out/CHECKS.json').read_text())
    claims['CHECKS_output_sha_current'] = all(chk['output_sha256'][n] == sha(B4 / 'out' / n) for n in chk['output_sha256'])
    claims['CHECKS_input_sha_current'] = all(h == sha(p) for p, h in chk['input_sha256'].items())
    qm = jl(B4 / 'out/QID_MAP.jsonl')
    b2map = {r['provenance']['sb_rowB2']['source_qid']: r['qid'] for r in b2rows}
    rowmap = {r['qid']: r['provenance'][KEY]['source_qid'] for r in rows}
    claims['qid_map'] = dict(rows=len(qm), covers_new=set(m['new_qid'] for m in qm) == set(qids),
                             old_matches_row=all(rowmap[m['new_qid']] == m['old_qid'] for m in qm),
                             b2_qid_valid=all(b2map.get(m['old_qid']) == m['sb_rowB2_qid'] for m in qm))
    claims['repeat_same_source_same_position'] = sum(v > 1 for v in C.Counter(zip(srcq, (r['answer'] for r in rows))).values())

    def all_out(s):
        p = s['provenance']
        return all(p['frame_n_share'][o['label']] < p['visibility_floor'] for o in p['instances'])
    eligible = allsrc - missing_src - wording_ref_b3 - n_outside
    claims['eligible_equals_replaced'] = eligible == replaced
    claims['eligible_all_out_of_view'] = sum(all_out(src[q]) for q in eligible)
    claims['eligible_all_out_of_view_replaced'] = sum(all_out(src[q]) for q in eligible & replaced)
    claims['delivered_unique_questions'] = len({r['student_input']['question'] for r in rows})
    res['claims'] = claims
    res['families'] = {f: dict(census=census[f], delivered=fam_rows[f], sources=len({q for q in replaced if src[q]['question_type'] == f})) for f in FAMS}
    res['input_sha256'] = pins
    res['script_sha256'] = sha(__file__)
    (OUT / 'RV4_MAIN.json').write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + '\n')
    print('DONE')


if __name__ == '__main__':
    main()
