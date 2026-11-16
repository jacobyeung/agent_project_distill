"""Index suite reports and verify the immutable kit without Git."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
index = {}
for path in sorted((ROOT/'tmp').glob('eat1_*/runs/*/EAT1_REPORT.json')):
    report = json.loads(path.read_text())
    group = 'adversarial' if path.parent.parent.parent.name.startswith('eat1_adv_') else 'toy'
    index[group+'/'+path.parent.name] = dict(path=str(path.relative_to(ROOT)), overall=report['overall'],
        claim_grade=report['claim_grade'], clauses={k: dict(status=c['status'],
        reasons=sorted({o.get('kind') or o.get('rule') or o.get('file', '') for o in c['offenders']}))
        for k, c in report['clauses'].items()}, cache_proof=report['clauses']['A5'].get('cache_proof'),
        claim_needs_live_run=report['clauses']['A5'].get('claim_needs_live_run'))
target = ROOT/'probes_r3'/'suite_evidence.json'
target.write_text(json.dumps(index, indent=2)+'\n')
for name, r in index.items():
    print(name, r['overall'], json.dumps({k: c['reasons'] for k, c in r['clauses'].items() if c['status'] != 'PASS'}))
checks = []
for row in (ROOT/'COPY_FILES.sha256').read_text().splitlines():
    digest, name = row.split(maxsplit=1)
    checks.append(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest)
size = sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
print(json.dumps(dict(kit_hashes_match=all(checks), kit_files=len(checks), workspace_bytes=size)))
