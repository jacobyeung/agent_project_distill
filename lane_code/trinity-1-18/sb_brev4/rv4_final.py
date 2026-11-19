"""Write REMOVE_FINAL.json (compact n.json JSON Lines) for the orchestrator ruling, then simulate it with N's own Removals and scene gate.
Reading: camera v1 and v3 keep the old store-v7 form (every old row stays, replaced and MISSING_GT alike; rebuilt v1/v3 rows are not added,
so their new qids are listed); the other four families drop every old row (replaced, wording-refused, MISSING_GT) and take the rebuilt rows.
In every family an old row whose own question lies within 0.05 normalized edit distance of a held-out wording is removed (RV4_WORDING.json).
Keys already removed by N's configured remove lists are not repeated."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import collections as C
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_brev4')
B4 = Path('/scratch/jjyeung/orch_n30/sb_rowB4')
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
CFG = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
NJSON = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/inputs/records/n.json')
STORE = Path('/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7')
FAMS = ['camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3',
        'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf', 'obj_obj_relative_pos_ud']
KEEP_OLD = {'camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v3'}
sys.path.insert(0, str(TREE))
from student_pilot.row_removals import Removals
from student_pilot.scene_division_gate import check_rows
from student_pilot.s1_exclusions import Exclusions


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jl(p):
    return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]


def sem_of(r):
    return r['student_input']['options'][ord(r['answer']) - 65].split('. ', 1)[1]


def main():
    cfg = json.loads(CFG.read_text())
    con = sqlite3.connect('file:' + str(STORE / 'vqa/rows.sqlite') + '?mode=ro', uri=True)
    ranges = json.loads((STORE / 'FAMILY_INDEX_RANGES.json').read_text())['families']
    src = {}
    for fam in FAMS:
        for a, b in ranges[fam]:
            for (s,) in con.execute('select row from rows where i between ? and ?', (a, b)):
                r = json.loads(s)
                src[r['qid']] = r
    con.close()
    rows = jl(B4 / 'out/rows.jsonl')
    lists = {n: {x['row_key'] for x in jl(B4 / 'out' / n)} for n in ('REMOVE.json', 'REMOVE_WORDING.json', 'REMOVE_MISSING_GT.json')}
    own_hit = set(json.loads((W / 'out/RV4_WORDING.json').read_text())['source_hit_qids'])
    nrem = Removals(cfg['remove_files'])
    already = {q for q, r in src.items() if nrem.match(r)}
    assert not any(nrem.match(r) for r in rows)
    schema = set(json.loads(NJSON.read_text().splitlines()[0]))

    def item(r, reason):
        x = dict(pool=r['pool'], question_type=r['question_type'], reason=reason, row_key=r['qid'], scene=r['dataset'] + '/' + r['scene'])
        assert set(x) == schema
        return x

    final = []
    for q, r in src.items():
        fam = r['question_type']
        if q in already:
            continue
        if q in own_hit:
            final.append(item(r, 'heldout_wording_distance_le_0.05'))
        elif fam in KEEP_OLD:
            continue
        elif q in lists['REMOVE.json']:
            final.append(item(r, 'replaced_by_sb_rowB4_frame_k_visibility'))
        elif q in lists['REMOVE_MISSING_GT.json']:
            final.append(item(r, 'MISSING_GT_old_form_retired'))
        elif q in lists['REMOVE_WORDING.json']:
            final.append(item(r, 'not_rebuilt_heldout_wording_permutation'))
        else:
            raise AssertionError(('unclassified old row', q))
    for r in rows:
        if r['question_type'] in KEEP_OLD:
            final.append(item(r, 'camera_v1_v3_keep_old_form'))
    final.sort(key=lambda x: (FAMS.index(x['question_type']), x['reason'], x['row_key']))
    p = W / 'REMOVE_FINAL.json'
    with open(p, 'w') as f:
        for x in final:
            f.write(json.dumps(x, sort_keys=True, separators=(',', ':')) + '\n')
    pin = dict(path=str(p), sha256=sha(p))
    raw = p.read_text().splitlines()
    fmt = dict(rows=len(raw), unique_keys=len({json.loads(l)['row_key'] for l in raw}),
               compact_sorted_like_n=all(l == json.dumps(json.loads(l), sort_keys=True, separators=(',', ':')) for l in raw),
               schema=sorted(schema), sha256=pin['sha256'],
               reasons={f'{a}|{b}': v for (a, b), v in sorted(C.Counter((x['question_type'], x['reason']) for x in final).items())})

    # simulate with N's own Removals (configured lists + REMOVE_FINAL) on old + rebuilt rows, then N's scene gate
    allrem = Removals(cfg['remove_files'] + [pin])
    table = {}
    kept_rows = []
    for fam in FAMS:
        old = [r for r in src.values() if r['question_type'] == fam]
        new = [r for r in rows if r['question_type'] == fam]
        ok_old = [r for r in old if not allrem.match(r)]
        ok_new = [r for r in new if not allrem.match(r)]
        kept_rows += ok_old + ok_new
        fr = [x for x in final if x['question_type'] == fam]
        by = C.Counter(x['reason'] for x in fr)
        srcs = {r['qid'] for r in ok_old} | {r['provenance']['sb_rowB4']['source_qid'] for r in ok_new}
        d = dict(old_census=len(old), old_out_n_lists=sum(r['qid'] in already for r in old),
                 old_out_remove_final=len(fr) - by['camera_v1_v3_keep_old_form'], old_out_by_reason={k: v for k, v in by.items() if k != 'camera_v1_v3_keep_old_form'},
                 old_kept=len(ok_old), rebuilt_delivered=len(new), rebuilt_in=len(ok_new), rebuilt_out=len(new) - len(ok_new),
                 final_rows=len(ok_old) + len(ok_new), final_unique_sources=len(srcs), under_1000=len(ok_old) + len(ok_new) < 1000)
        if fam in KEEP_OLD:
            n = len(old[0]['student_input']['options'])
            pos = C.Counter(r['answer'] for r in ok_old)
            unt = [r for r in ok_old if len(set(r['provenance']['first_seen'].values())) == len(r['provenance']['first_seen'])]
            d['kept_old_last_option_share'] = round(pos[chr(64 + n)] / len(ok_old), 4)
            d['kept_old_position'] = dict(sorted(pos.items()))
            d['kept_old_untied_earliest_wins'] = round(sum(r['provenance']['first_seen'][sem_of(r)] == min(r['provenance']['first_seen'].values()) for r in unt) / len(unt), 4)
            d['kept_old_chance'] = round(1 / n, 4)
            d['kept_old_missing_gt'] = sum(r['qid'] in lists['REMOVE_MISSING_GT.json'] for r in ok_old)
            d['kept_old_replaced'] = sum(r['qid'] in lists['REMOVE.json'] for r in ok_old)
            d['kept_old_in_remove_wording'] = sum(r['qid'] in lists['REMOVE_WORDING.json'] for r in ok_old)
        table[fam] = d
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    union = list(src.values()) + rows
    try:
        gate = check_rows(union, cfg['scene_division'], removals=Removals(cfg['remove_files'] + [pin]), scene_filter=rule, stream='vqa')
    except Exception as ex:
        gate = dict(error=str(ex))
    res = dict(reading=__doc__, remove_final=fmt, families=table, totals=dict(final_rows=len(kept_rows),
               old_kept=sum(t['old_kept'] for t in table.values()), rebuilt_in=sum(t['rebuilt_in'] for t in table.values())),
               scene_gate_on_old_plus_rebuilt_with_remove_final=gate, own_wording_hits=len(own_hit),
               own_hits_in_remove_wording=len(own_hit & lists['REMOVE_WORDING.json']), own_hits_in_missing=len(own_hit & lists['REMOVE_MISSING_GT.json']),
               own_hits_in_replaced=len(own_hit & lists['REMOVE.json']), own_hits_in_n_lists=len(own_hit & already),
               own_hits_by_family_and_list=dict(sorted(C.Counter(src[q]['question_type'] + '|' + ('n_lists' if q in already else next(n for n in lists if q in lists[n]))
                                                                 for q in own_hit).items())),
               input_sha256={str(B4 / 'out' / n): sha(B4 / 'out' / n) for n in ('rows.jsonl', 'REMOVE.json', 'REMOVE_WORDING.json', 'REMOVE_MISSING_GT.json')}
               | {str(W / 'out/RV4_WORDING.json'): sha(W / 'out/RV4_WORDING.json'), str(CFG): sha(CFG), str(STORE / 'vqa/rows.sqlite'): sha(STORE / 'vqa/rows.sqlite')},
               script_sha256=sha(__file__))
    (W / 'out/RV4_FINAL.json').write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
    print(json.dumps({k: v for k, v in res.items() if k != 'reading'}, indent=1))


if __name__ == '__main__':
    main()
