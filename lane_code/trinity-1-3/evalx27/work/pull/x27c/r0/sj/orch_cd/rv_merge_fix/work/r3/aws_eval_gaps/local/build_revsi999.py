"""Build the official ReVSI 999 rows at the 32- and 64-frame tiers from the official ground-truth parquets.

Run once with a pyarrow interpreter (the kit's own environments lack it):
  /scratch/jjyeung/envs/planner_local_v1/bin/python local/build_revsi999.py PARQUET_DIR QUESTIONS_999_JSON
The 999 = the official tiny-set ids present in the 32-frame tier (all also exist in the 64-frame tier).
Writes inputs/revsi999_rows_t32.json, revsi999_rows_t64.json, revsi999_membership.json and REVSI999_PROVENANCE.json.
"""
import hashlib, json, sys
from pathlib import Path
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
CATEGORY = {'object_counting_single': 'object_counting', 'object_counting_multiple': 'object_counting',
            'object_rel_distance_closest': 'object_rel_distance', 'object_rel_distance_farthest': 'object_rel_distance',
            'room_size_estimation_single': 'room_size_estimation', 'room_size_estimation_multiple': 'room_size_estimation',
            'object_size_estimation': 'object_size_estimation', 'object_abs_distance': 'object_abs_distance',
            'route_planning': 'route_planning'}


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def category(t): return CATEGORY.get(t) or ('object_rel_direction' if t.startswith('object_rel_direction_') else None)


def main(pdir, qpath):
    pdir = Path(pdir)
    ids = sorted(int(k.split('_')[1]) for k in json.loads(Path(qpath).read_text()))
    if len(ids) != 999: raise SystemExit('need 999 ids')
    cap = {r['example_id']: r for r in json.loads((ROOT / 'inputs/revsi_rows.json').read_text())}
    prov = dict(questions_999=dict(path=str(qpath), sha256=sha(qpath)), parquets={}, rows={})
    for tier in (32, 64):
        src = pdir / f'{tier}_frame.parquet'
        prov['parquets'][str(tier)] = dict(path=str(src), sha256=sha(src))
        table = {int(r['id']): r for r in pq.read_table(src).to_pylist()}
        rows = []
        for i in ids:
            r = table[i]; key = str(i); c = cap.get(key)
            if str(r['num_frames']) != str(tier): raise SystemExit(f'tier differs on {i}')
            opts = r['options']
            opts = [] if opts is None or opts == 'None' else (json.loads(opts) if isinstance(opts, str) else list(opts))
            q_ids = r['queried_object_ids']
            q_ids = [] if q_ids is None else (json.loads(q_ids) if isinstance(q_ids, str) else list(q_ids))
            row = dict(id=i, dataset=r['dataset'], scene_id=str(r['scene_id']), question_type=r['question_type'],
                       question=r['question'], ground_truth=str(r['ground_truth']), options=opts, num_frames=str(tier),
                       queried_object_ids=q_ids, qid=key, revsi_id=i, category=category(r['question_type']),
                       scene=str(r['scene_id']), visible_32=c['visible_32'] if c else None,
                       invisible_object_ids=c['invisible_object_ids'] if c else None,
                       provenance=f'official_parquet_{tier}frame', example_id=key, scene_name=str(r['scene_id']),
                       benchmark='revsi', cap452=c is not None)
            if row['category'] is None: raise SystemExit(f'unknown type {r["question_type"]}')
            rows.append(row)
        out = ROOT / f'inputs/revsi999_rows_t{tier}.json'
        out.write_text(json.dumps(rows, sort_keys=True) + '\n')
        prov['rows'][str(tier)] = dict(path=out.name, sha256=sha(out), count=len(rows))
    members = [dict(qid=str(i)) for i in ids]
    (ROOT / 'inputs/revsi999_membership.json').write_text(json.dumps(members) + '\n')
    prov['membership'] = dict(path='revsi999_membership.json', sha256=sha(ROOT / 'inputs/revsi999_membership.json'))
    (ROOT / 'inputs/REVSI999_PROVENANCE.json').write_text(json.dumps(prov, indent=1, sort_keys=True) + '\n')
    print(json.dumps(prov['rows']))


if __name__ == '__main__':
    main(*sys.argv[1:3])
