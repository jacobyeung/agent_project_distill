"""Load the 150 dev-S1 routed distance items at step 544 (read 171253/1 candidates_argmax) and step 200 (172744), read in place."""
import json, re, sys
from pathlib import Path
O = Path('/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3s')
sys.path.insert(0, str(O))
_argv = sys.argv; sys.argv = ['x']
import score_r5 as S
sys.argv = _argv
sc = S.scorers
P200 = Path('/scratch/jjyeung/orch_n30/cont_ops/work/r1route/out3/A4/ret')
P544 = S.BASE / 'b1/work/ret'
def load_all():
    a, items, _, src_a = S.load(S.O.parent / 'out3/A4/ret', S.O / 'A', 0, 200, 'candidates_argmax')
    bd, _, _, src_b = S.load(S.BASE / 'b1/work/ret', S.BASE / 'b1', 1, 544, 'candidates_argmax')
    ba, _, _, src_c = S.load(S.BASE / 'b1/work/ret', S.BASE / 'b1', 0, 544, 'null_argmax')
    return a, bd, ba, items, src_a + src_b + src_c
UNIT = {1.: 'm', 100.: 'cm', 1/.3048: 'ft', 1/.0254: 'in', 1000.: 'mm'}
def unit(q):
    return UNIT[sc.unit_factor(q)]
