"""Reviewer checks for sb_rowB3 (validators, identities, field diff, rooms, bias, REMOVE, MISSING, claims).
Imports only N's sealed W19 tree; never the builder's code."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[k] = '1'
import collections as C
import hashlib
import json
import re
import sqlite3
import sys
import tarfile
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_brev3')
OUT = W / 'out'
B3 = Path('/scratch/jjyeung/orch_n30/sb_rowB3')
B2 = Path('/scratch/jjyeung/orch_n30/sb_rowB2')
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
SEAL = TREE.parents[1] / 'out/TREE_SEAL.json'
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
CFG = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
NJSON = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json')
DEV_S1 = B3 / 'inputs/dev_scene_exclusions.json'
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
    """Dotted paths where a and b differ (dicts recurse, everything else compares whole)."""
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
    """Normalise and add ScanNet room (rescan suffix stripped)."""
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


def main():
    OUT.mkdir(exist_ok=True)
    res = {}
    pins = {}
    # --- N tree seal: every loaded tree module matches TREE_SEAL.json
    seal = json.loads(SEAL.read_text())
    mism = []
    for m in list(sys.modules.values()):
        p = getattr(m, '__file__', None)
        if p and p.startswith(str(TREE)):
            rel = str(Path(p).relative_to(TREE))
            if seal['files'].get(rel) != sha(p):
                mism.append(rel)
    res['tree'] = dict(tree_sha256=seal.get('tree_sha256'), loaded_modules_mismatch=mism)

    # --- store and sources (own loader)
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

    rows = jl(B3 / 'out/rows.jsonl')
    pins[str(B3 / 'out/rows.jsonl')] = sha(B3 / 'out/rows.jsonl')
    b2rows = jl(B2 / 'out/rows.jsonl')
    b2_qid = {r['qid'] for r in b2rows}
    b2_cid = {r['candidate_id'] for r in b2rows}
    b2_src = {r['provenance']['sb_rowB2']['source_qid'] for r in b2rows}
    fam_rows = C.Counter(r['question_type'] for r in rows)
    srcq = [r['provenance']['sb_rowB3']['source_qid'] for r in rows]
    replaced = set(srcq)

    # --- (2) N validators on every new row and every source
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

    # --- (2) identities
    qids = [r['qid'] for r in rows]
    cids = [r['candidate_id'] for r in rows]
    cid_recomputed_bad = 0
    for r in rows:
        si = r['student_input']
        ci = dict(qid=r['qid'], scene=r['scene'], frame_indices=si['frame_indices'], type=r['question_type'],
                  question=si['question'], options=si['options'], trace_revision='3.14')
        if candidate_identity(ci) != r['candidate_id']:
            cid_recomputed_bad += 1
    src_formula = C.Counter()
    for r in src.values():
        si = r['student_input']
        ok = {rev: candidate_identity(dict(qid=r['qid'], scene=r['scene'], frame_indices=si['frame_indices'], type=r['question_type'],
                                           question=si['question'], options=si['options'], trace_revision=rev)) == r.get('candidate_id')
              for rev in ('3.14', '3.12.2')}
        src_formula['3.14' if ok['3.14'] else '3.12.2' if ok['3.12.2'] else 'neither'] += 1
    res['identity'] = dict(rows=len(rows), unique_qids=len(set(qids)), unique_candidate_ids=len(set(cids)),
                           qid_in_store=len(set(qids) & store_qid), qid_in_b2=len(set(qids) & b2_qid),
                           cid_in_store=len(set(cids) & store_cid), cid_in_b2=len(set(cids) & b2_cid),
                           cid_formula_mismatch=cid_recomputed_bad, source_cid_formula_match=dict(src_formula),
                           sources_not_in_store=len(replaced - set(src)))

    # --- (2) field diff vs source, restricted to edited fields
    allowed = {'qid', 'candidate_id', 'answer', 'target', 'student_input.question', 'student_input.options', 'provenance.sb_rowB3'}
    paths = C.Counter()
    bad_rows = 0
    other = C.Counter()
    for r in rows:
        s = src[r['provenance']['sb_rowB3']['source_qid']]
        d = diff_paths(r, s)
        paths.update(d)
        if set(d) - allowed:
            bad_rows += 1
        fam = r['question_type']
        so = sorted(x.split('. ', 1)[1] for x in s['student_input']['options'])
        ro = sorted(x.split('. ', 1)[1] for x in r['student_input']['options'])
        if so != ro:
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

    # --- (3) room rule
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
    k1_rooms = len(rooms.k1)
    # N remove lists: any rebuilt source N already removes would re-enter under a new qid
    rem = Removals(cfg['remove_files'])
    rem_src = C.Counter()
    rem_src_replaced = C.Counter()
    rem_new = 0
    for q, r in src.items():
        for i in rem.match(r):
            name = Path(cfg['remove_files'][i]['path']).name
            rem_src[name] += 1
            if q in replaced:
                rem_src_replaced[name] += 1
    for r in rows:
        rem_new += bool(rem.match(r))
    res['rooms'] = dict(new_row_hits=dict(room_new), source_hits=dict(room_src), k1_heldout_rooms=k1_rooms,
                        r0_union_rooms=len(rooms.r0), set_sizes={k: len(v) for k, v in sets.items()},
                        n_remove_lists_source_hits=dict(rem_src), n_remove_lists_replaced_source_hits=dict(rem_src_replaced),
                        n_remove_lists_new_row_hits=rem_new)

    # --- (4) bias histograms
    def hist(rr):
        out = {}
        for fam in FAMS:
            xs = [r for r in rr if r['question_type'] == fam]
            n = nopt(fam)
            pos = C.Counter(r['answer'] for r in xs)
            semc = C.Counter(sem_of(r) for r in xs)
            pos_sem = C.Counter(r['answer'] + '|' + sem_of(r) for r in xs) if not fam.startswith('camera_') else {}
            d = dict(rows=len(xs), position=dict(sorted(pos.items())),
                     last_option_share=round(pos[chr(64 + n)] / max(1, len(xs)), 4), uniform=round(1 / n, 4))
            if fam.startswith('camera_'):
                earliest = C.Counter()
                rank = C.Counter()
                for r in xs:
                    fs = r['provenance']['first_seen']
                    s = sem_of(r)
                    tied = len(set(fs.values())) < len(fs)
                    rk = 1 + sum(1 for v in fs.values() if v < fs[s])
                    rank[('tied' if tied else 'untied') + '|' + str(rk)] += 1
                    earliest['winner_is_earliest_incl_ties' if fs[s] == min(fs.values()) else 'winner_later'] += 1
                    if not tied:
                        earliest['untied_rows'] += 1
                        earliest['untied_winner_earliest'] += fs[s] == min(fs.values())
                d.update(first_seen_rank_of_winner=dict(sorted(rank.items())), earliest=dict(earliest),
                         untied_earliest_share=round(earliest['untied_winner_earliest'] / max(1, earliest['untied_rows']), 4))
            else:
                fsc = C.Counter()
                for r in xs:
                    fs = r['provenance']['first_seen']
                    a, b = [o['label'] for o in r['provenance']['instances']]
                    fsc[('earlier' if fs[a] < fs[b] else 'later' if fs[a] > fs[b] else 'tied') + '|' + sem_of(r)] += 1
                d.update(semantic=dict(sorted(semc.items())), position_x_semantic=dict(sorted(pos_sem.items())),
                         subject_first_seen_x_semantic=dict(sorted(fsc.items())))
            out[fam] = d
        return out
    res['bias'] = dict(before_all_sources=hist(list(src.values())), before_replaced_sources=hist([src[q] for q in replaced]),
                       after_delivered=hist(rows))

    # --- (5) REMOVE: their list vs exactly the replaced sources; write REMOVE_PROPOSED.json in n.json bytes format
    nlines = NJSON.read_text().splitlines()
    nkeys = set(json.loads(nlines[0]))
    n_compact = all(l == json.dumps(json.loads(l), sort_keys=True, separators=(',', ':')) for l in nlines)
    theirs = jl(B3 / 'out/REMOVE.json')
    tkeys = [x['row_key'] for x in theirs]
    raw_lines = (B3 / 'out/REMOVE.json').read_text().splitlines()
    t_compact = all(l == json.dumps(json.loads(l), sort_keys=True, separators=(',', ':')) for l in raw_lines)
    t_reason = C.Counter(x['reason'] for x in theirs)
    t_reason_fam = C.Counter((x['question_type'], x['reason']) for x in theirs)
    proposed = []
    for q in sorted(replaced, key=lambda q: (FAMS.index(src[q]['question_type']), q)):
        s = src[q]
        proposed.append(dict(pool=s['pool'], question_type=s['question_type'], reason='replaced_by_sb_rowB3_frame_k_visibility',
                             row_key=q, scene=s['dataset'] + '/' + s['scene']))
    with open(W / 'REMOVE_PROPOSED.json', 'w') as f:
        for x in proposed:
            assert set(x) == nkeys
            f.write(json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n')
    replaced_reason = {x['row_key'] for x in theirs if x['reason'] == 'replaced_truthful_frame_k_visibility'}
    res['remove'] = dict(n_json_schema=sorted(nkeys), n_json_compact_sorted=n_compact,
                         theirs_rows=len(theirs), theirs_unique=len(set(tkeys)), theirs_schema_ok=all(set(x) == nkeys for x in theirs),
                         theirs_compact_like_n=t_compact, theirs_reasons=dict(t_reason),
                         theirs_reason_by_family={f'{a}|{b}': v for (a, b), v in sorted(t_reason_fam.items())},
                         replaced_sources=len(replaced), theirs_minus_replaced=len(set(tkeys) - replaced),
                         replaced_minus_theirs=len(replaced - set(tkeys)),
                         theirs_replaced_reason_equals_replaced=replaced_reason == replaced,
                         theirs_contains_new_qids=len(set(tkeys) & set(qids)),
                         proposed_rows=len(proposed), proposed_sha256=sha(W / 'REMOVE_PROPOSED.json'),
                         proposed_by_family=dict(C.Counter(x['question_type'] for x in proposed)))

    # --- (6) MISSING rasters: own determination from each source's raster pin
    have = {}
    for s in src.values():
        h = s['provenance']['raster_sha256']
        if h in have:
            continue
        p = GT_DIR / (h + '.npz')
        orig = Path(s['provenance']['raster'])
        have[h] = (p.is_file() and sha(p) == h) or (orig.is_file() and sha(orig) == h)
    missing_src = {q for q, s in src.items() if not have[s['provenance']['raster_sha256']]}
    their_missing = {q for q, why in json.loads((B3 / 'inputs/GT_REFUSALS.json').read_text())['refused'].items()}
    refusals = json.loads((B3 / 'out/REFUSALS.json').read_text())['rows']
    wording_ref = {q for q, w in refusals.items() if any('wording' in x for x in w)}
    fam6 = {}
    for fam in FAMS:
        fq = {q for q, s in src.items() if s['question_type'] == fam}
        m = fq & missing_src
        fam6[fam] = dict(census=len(fq), missing=len(m), store_rows_left_after_drop=len(fq) - len(m),
                         wording_refused=len(fq & wording_ref - missing_src), replaced_sources=len(fq & replaced),
                         delivered_rows=fam_rows[fam],
                         missing_by_dataset=dict(C.Counter(src[q]['dataset'] for q in m)),
                         missing_rasters=len({src[q]['provenance']['raster_sha256'] for q in m}))
    res['missing'] = dict(rasters_total=len(have), rasters_missing=sum(not v for v in have.values()),
                          sources_missing=len(missing_src), equals_builder_list=missing_src == their_missing,
                          by_dataset=dict(C.Counter(src[q]['dataset'] for q in missing_src)),
                          missing_dirs=dict(C.Counter(str(Path(src[q]['provenance']['raster']).parent) for q in missing_src)),
                          replaced_intersect_missing=len(replaced & missing_src),
                          unaccounted=len(set(src) - replaced - missing_src - wording_ref), families=fam6)

    # --- (7) claims vs files
    claims = {}
    tar_p = B3 / 'out/sb_rowB3.tar'
    tar_sha = sha(tar_p)
    sums = (B3 / 'out/SHA256SUMS').read_text().split()
    claims['tar_sha_matches_SHA256SUMS'] = sums[0] == tar_sha
    with tarfile.open(tar_p) as t:
        names = t.getnames()
        mem = {}
        for n in names:
            if n.endswith(('rows.jsonl', 'REMOVE.json', 'QID_MAP.jsonl', 'CHECKS.json')):
                mem[n] = hashlib.sha256(t.extractfile(n).read()).hexdigest()
    claims['tar_members'] = len(names)
    claims['tar_member_hashes_match_out'] = {n: h == sha(B3 / 'out' / Path(n).name) for n, h in mem.items()}
    chk = json.loads((B3 / 'out/CHECKS.json').read_text())
    claims['CHECKS_output_sha_current'] = {n: chk['output_sha256'][n] == sha(B3 / 'out' / n) for n in chk['output_sha256']}
    claims['CHECKS_input_sha_current'] = {Path(p).name: h == sha(p) for p, h in chk['input_sha256'].items()}
    ind = json.loads((B3 / 'out/INDEPENDENT_CHECK.json').read_text())
    claims['independent_gt_scenes'] = ind.get('gt_scenes')
    claims['independent_sighting_frames'] = ind.get('sighting_frames')
    claims['independent_visibility_objects'] = ind.get('visibility_objects')
    wc = json.loads((B3 / 'inputs/WORDING_CORPUS.json').read_text())
    claims['wording_corpus'] = dict(questions=len(wc['questions']), input_files=len(wc['input_sha256']))
    claims['read30_sections'] = len(re.findall(r'^## \d+\. ', (B3 / 'out/READ30.md').read_text(), re.M))
    qm = jl(B3 / 'out/QID_MAP.jsonl')
    b2map = {r['provenance']['sb_rowB2']['source_qid']: r['qid'] for r in b2rows}
    claims['qid_map'] = dict(rows=len(qm), covers_new=set(m['new_qid'] for m in qm) == set(qids),
                             old_matches_row=all(m['old_qid'] == r['provenance']['sb_rowB3']['source_qid'] for m, r in
                                                 zip(sorted(qm, key=lambda m: m['new_qid']), sorted(rows, key=lambda r: r['qid']))),
                             b2_qid_valid=all(b2map.get(m['old_qid']) == m['sb_rowB2_qid'] for m in qm))
    claims['replaced_equals_b2_sources'] = replaced == b2_src
    claims['b2_rows'] = len(b2rows)
    uses = C.Counter(srcq)
    claims['source_use_hist'] = dict(C.Counter(uses.values()))
    pairs = C.Counter((q, r['answer']) for q, r in zip(srcq, rows))
    claims['repeat_same_source_same_position'] = sum(v > 1 for v in pairs.values())
    # all-out-of-view sources retained
    def all_out(s):
        p = s['provenance']
        return all(p['frame_n_share'][o['label']] < p['visibility_floor'] for o in p['instances'])
    eligible = set(src) - missing_src - wording_ref
    claims['eligible_all_out_of_view'] = sum(all_out(src[q]) for q in eligible)
    claims['eligible_all_out_of_view_replaced'] = sum(all_out(src[q]) for q in eligible & replaced)
    claims['eligible_equals_replaced'] = eligible == replaced
    res['claims'] = claims
    res['input_sha256'] = pins
    res['script_sha256'] = sha(__file__)
    (OUT / 'RV_MAIN.json').write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
    print('DONE')


if __name__ == '__main__':
    main()
