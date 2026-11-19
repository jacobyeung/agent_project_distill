"""Run N's native scene-division gate (with N's dev/benchmark filter and all N remove lists) on every sb_rowB4 row."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import collections as C
import hashlib
import json
import sys
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/sb_brev4')
B4 = Path('/scratch/jjyeung/orch_n30/sb_rowB4')
TREE = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
CFG = Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json')
sys.path.insert(0, str(TREE))
from student_pilot.scene_division_gate import check_rows
from student_pilot.row_removals import Removals
from student_pilot.s1_exclusions import Exclusions


def main():
    cfg = json.loads(CFG.read_text())
    rows = [json.loads(s) for s in (B4 / 'out/rows.jsonl').read_text().splitlines()]
    rule = Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions'])
    res = dict(remove_files=[Path(x['path']).name for x in cfg['remove_files']], rows_sha256=hashlib.sha256((B4 / 'out/rows.jsonl').read_bytes()).hexdigest())
    try:
        res['all_delivered'] = dict(rows=len(rows), result=check_rows(rows, cfg['scene_division'], removals=Removals(cfg['remove_files']),
                                                                       scene_filter=rule, stream='vqa'))
    except Exception as ex:
        res['all_delivered'] = dict(rows=len(rows), error=str(ex))
    for fam in sorted({r['question_type'] for r in rows}):
        rr = [r for r in rows if r['question_type'] == fam]
        try:
            res[fam] = check_rows(rr, cfg['scene_division'], removals=Removals(cfg['remove_files']), scene_filter=Exclusions(cfg['dev_scene_exclusions'], cfg['benchmark_scene_exclusions']), stream='vqa')
        except Exception as ex:
            res[fam] = dict(error=str(ex))
    (W / 'out/RV4_GATE.json').write_text(json.dumps(res, indent=1, sort_keys=True) + '\n')
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
