"""cont_ops23: run the sealed H remainder kit's score() on local copies (no /project bytes).
Usage: python3 -B local_score.py ROOT KIT OUTDIR WORKDIR [--test]
ROOT holds the package dirs (a/f = authenticated publication: 0.tgz, EXIT.json, RETURN_RECEIPT.json)."""
import json, sys
from pathlib import Path
root, kit, out, work = map(Path, sys.argv[1:5]); test = '--test' in sys.argv
sys.path.insert(0, str(kit))
from score_h_merge import score

def seg(p):
    f = root/p/'a/f'
    return dict(package=str(root/p), archive=str(f/'0.tgz'), exit=str(f/'EXIT.json'), receipt=str(f/'RETURN_RECEIPT.json'))

H400, H200 = seg('a15_cot_apd7a6db629db02'), seg('a15_cot_apdacd91c2f5c4b')
if test:
    jobs = [('TEST_H400_vs_H200', H400, H200)]
else:
    spec = dict(parent=seg('a15_cot_apdc863c3e6b41d'), remainder=seg('a15_cot_apdd982cd5c4b25'))
    out.mkdir(parents=True, exist_ok=True)
    with (out/'SCORE_SPEC.json').open('x') as f: json.dump(spec, f, sort_keys=True, indent=2)
    jobs = [('SCORES', spec, None), ('SCORES_vs_H400', spec, H400), ('SCORES_vs_H200', spec, H200), ('ALONE_H400', H400, None), ('ALONE_H200', H200, None)]
out.mkdir(parents=True, exist_ok=True)
for name, s, o in jobs:
    r = score(s, work/name, o)
    with (out/(name+'.json')).open('x') as f: json.dump(r, f, sort_keys=True, indent=2, allow_nan=False); f.write('\n')
    print(name, 'completed', r['meta'].get('completed'), flush=True)
