import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path('/scratch/jjyeung/orch_cd/devs1_direct/out')
inventory = {}
for version in ('r3','r4','r5'):
    for p in sorted((SOURCE/version).rglob('*')):
        if not p.is_file() or 'merge_results' in p.parts or p.suffix not in ('.py','.json','.jsonl'): continue
        q = ROOT/'work/vendor'/version/p.relative_to(SOURCE/version)
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_bytes(p.read_bytes())
        inventory[str(q.relative_to(ROOT))] = dict(source=str(p), sha256=hashlib.sha256(q.read_bytes()).hexdigest())
for name in ('ROUTING_POLICY.json',):
    p=Path('/scratch/jjyeung/orch_cd/leg_s1_tree/out')/name
    q=ROOT/'out'/name; q.write_bytes(p.read_bytes())
    inventory[str(q.relative_to(ROOT))]=dict(source=str(p),sha256=hashlib.sha256(q.read_bytes()).hexdigest())
(ROOT/'out/SOURCE_COPIES.json').write_text(json.dumps(inventory,indent=2)+'\n')
print('Copied',len(inventory),'small source/payload files')
