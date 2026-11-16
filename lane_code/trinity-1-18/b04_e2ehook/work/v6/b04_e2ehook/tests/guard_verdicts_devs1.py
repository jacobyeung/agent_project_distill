"""Verdicts of the removed gravity checks on job 170056's 84 dev-S1 geometry exports (report only).
Usage: python -B guard_verdicts_devs1.py GEOMETRY_DIR OUT.json"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent), str(HERE), '/scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449']
import guard_diag
from e2e_reader import geometry as G
per = {p.stem: guard_diag.verdicts(G.from_npz(p)) for p in sorted(Path(sys.argv[1]).glob('*.npz'))}
out = dict(clips=len(per), sealed_refuses=sum(v['sealed_guard_refuses'] for v in per.values()),
           reviewed_refuses=sum(v['reviewed_guard_refuses'] for v in per.values()), reader_refuses=0, per_clip=per)
Path(sys.argv[2]).write_text(json.dumps(out, indent=1) + '\n')
print({k: v for k, v in out.items() if k != 'per_clip'})
