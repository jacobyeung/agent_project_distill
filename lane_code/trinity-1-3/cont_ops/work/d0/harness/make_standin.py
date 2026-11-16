"""Place the kit's own copies of every small pin the pool receipt names at its original path, under a stand-in root."""
import hashlib, json, glob, os, shutil, sys
base, root = sys.argv[1], sys.argv[2]
bysha = {hashlib.sha256(open(f, 'rb').read()).hexdigest(): f for f in glob.glob(base + '/k/*') if os.path.isfile(f)}
pool = json.load(open(base + '/k/pool_selection.json'))
need = [pool['manifest'], *pool['remove_files'], *pool['scene_exclusions'].values(), *pool['exclusions'].values(),
        *[e['selection'] for e in pool['sources'].values() if e.get('selection')]]
placed = 0
for pin in need:
    src = bysha[pin['sha256']]
    rel = pin['path'].lstrip('/')
    assert rel.startswith('scratch/jjyeung/orch_cd/'), rel
    dst = os.path.join(root, rel[len('scratch/jjyeung/orch_cd/'):])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if not os.path.exists(dst): shutil.copyfile(src, dst); placed += 1
print('placed', placed, 'of', len(need))
