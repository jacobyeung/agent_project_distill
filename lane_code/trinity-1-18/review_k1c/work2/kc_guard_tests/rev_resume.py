# Build convert-resume roots: canary captures 0 and 2 genuine, capture 1 replaced by forged variant; no HALTED.json.
import json,sys,shutil
from pathlib import Path
T=Path('/scratch/jjyeung/orch_n30/review_k1c/work2/kc_guard_tests')
py=sys.argv[1]
for v in ('a','b'):
    out=T/f'resume2_{py}_{v}';out.mkdir()
    for n in ('BINDING.json','PROGRESS.jsonl'):shutil.copyfile(T/'canary'/n,out/n)
    forged=next((T/f'forge_{py}'/v).iterdir())
    for k in ('dfece798227526fb','54c1c9d606f2a398','48f3924ccb5dd8b6'):
        src=forged if k==forged.name else T/'canary'/k
        shutil.copytree(src,out/k)
        if True:
            r=json.load(open(out/k/'CACHE_COMPLETE.json'))
            for n,p in r['files'].items():p['path']=str(out/k/n)
            json.dump(r,open(out/k/'CACHE_COMPLETE.json','w'))
    print(out,forged.name)
