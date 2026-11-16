"""For each ARKit capture whose plain build differs from its pin: move the plain output to out/rejected/, and copy a
declared-variant output whose sha256 equals the pin into the gt path. Never writes a file that differs from its pin."""
import glob, hashlib, json, os, shutil
G = '/scratch/jjyeung/orch_n30/gt_build'
C = {p['canonical']: p['gt'] for p in json.load(open('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json'))['pilot']}
sha = lambda f: hashlib.sha256(open(f, 'rb').read()).hexdigest()
os.makedirs(f'{G}/out/rejected/arkit_gt', exist_ok=True); src = {}
for cn, gt in C.items():
    if not cn.startswith('arkitscenes/'): continue
    name = os.path.basename(gt['path']); out = f'{G}/out/dose_pool/out/arkit_gt/gt/{name}'
    if os.path.exists(out) and sha(out) == gt['expected_sha256']: src[cn] = 'plain'; continue
    if os.path.exists(out): shutil.move(out, f'{G}/out/rejected/arkit_gt/{name}')
    for v in sorted(glob.glob(f'{G}/out/variants/*/{name}')):
        if sha(v) == gt['expected_sha256']:
            shutil.copyfile(v, out + '.part'); assert sha(out + '.part') == gt['expected_sha256']; os.replace(out + '.part', out)
            src[cn] = v.split('/')[-2]; break
json.dump(src, open(f'{G}/work/ARKIT_SOURCE_VARIANT.json', 'w'), indent=0)
from collections import Counter; print(Counter(src.values()), 'placed', len(src))
