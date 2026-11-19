"""Run N's native scene-division gate (with N's dev/benchmark filter and remove lists) on the delivered rows."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import collections as C
import json
import sys
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_brev3')
B3 = Path('/scratch/jjyeung/orch_n30/sb_rowB3')
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
CFG = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
FAMS = ['camera_obj_rel_dist_v1', 'camera_obj_rel_dist_v2', 'camera_obj_rel_dist_v3',
        'obj_obj_relative_pos_lr', 'obj_obj_relative_pos_nf', 'obj_obj_relative_pos_ud']
sys.path.insert(0, str(TREE))
from student_pilot.scene_division_gate import check_rows
from student_pilot.row_removals import Removals
from student_pilot.s1_exclusions import Exclusions


def main():
    cfg = json.loads(CFG.read_text())
    rows = [json.loads(s) for s in (B3 / 'out/rows.jsonl').read_text().splitlines()]
    n = {json.loads(s)['row_key'] for s in Path(cfg['remove_files'][8]['path']).read_text().splitlines()}
    assert cfg['remove_files'][8]['path'].endswith('records/n.json')
    res = {}
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    for name, rr in (('all_delivered', rows), ('without_n_json_sources', [r for r in rows if r['provenance']['sb_rowB3']['source_qid'] not in n])):
        try:
            res[name] = dict(rows=len(rr), result=check_rows(rr, cfg['scene_division'], removals=Removals(cfg['remove_files']),
                                                             scene_filter=rule, stream='vqa'))
        except Exception as ex:
            res[name] = dict(rows=len(rr), error=str(ex))
    kept = [r for r in rows if r['provenance']['sb_rowB3']['source_qid'] not in n]
    res['position_after_dropping_n_json_sources'] = {f: dict(sorted(C.Counter(r['answer'] for r in kept if r['question_type'] == f).items())) for f in FAMS}
    res['rows_after_dropping_n_json_sources'] = dict(C.Counter(r['question_type'] for r in kept))
    (W / 'out/RV_GATE.json').write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
