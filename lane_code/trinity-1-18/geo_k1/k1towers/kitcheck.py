"""Verify the bake-off kit against its seal without writing into it: every sealed file's sha256, the five
checkpoints against downloads.jsonl, and the seal digest. Usage: python3 kitcheck.py KIT OUT.json"""
import hashlib, json, sys
from pathlib import Path
kit, out = Path(sys.argv[1]), Path(sys.argv[2])
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()
seal = json.loads((kit / 'KIT_SEAL.json').read_text())
missing, differ = [], []
for rel, d in seal['files'].items():
    p = kit / rel
    if not p.is_file():
        missing.append(rel)
    elif sha(p) != d:
        differ.append(rel)
ledger = [json.loads(l) for l in (kit / 'assets/downloads.jsonl').read_text().splitlines()]
weights = {}
for m in ('moge2', 'mapanything', 'da3', 'pi3x', 'moge3'):
    fn = 'model.pt' if m.startswith('moge') else 'model.safetensors'
    p = kit / 'assets' / m / fn
    r = next((r for r in ledger if r['path'].endswith(f'/{m}/{fn}') and r['verified_expected_sha256']), None)
    weights[m] = dict(present=p.is_file(), bytes_ok=bool(r and p.is_file() and p.stat().st_size == r['bytes']),
                      sha_ok=bool(r and p.is_file() and sha(p) == r['sha256']))
res = dict(kit=str(kit), seal_sha256=sha(kit / 'KIT_SEAL.json'), sealed_files=len(seal['files']),
           missing=missing, differ=differ, weights=weights,
           verdict='COMPLETE' if not missing and not differ and all(w['sha_ok'] for w in weights.values()) else 'INCOMPLETE')
out.write_text(json.dumps(res, indent=1))
print(json.dumps(dict(res, missing=len(missing), differ=differ[:20]), indent=1))
