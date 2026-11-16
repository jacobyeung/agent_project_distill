import json
from pathlib import Path

from eat1 import run as R, scan as S
from eat1.artifact import Artifact, sha256
from probes.variants import make_reader

ROOT = Path(__file__).resolve().parent
WORK = ROOT/'fixture'
items = R.read_items(WORK/'move.jsonl')
reader = make_reader(WORK, 'rewrite')
records, _, _ = R.observe(reader, items, Artifact(reader.artifact_manifest))
print('cache_rewrite', json.dumps(dict(changed=reader.rewritten,
    violations=records[0]['provenance']['violations'])))

reader = make_reader(WORK, 'disappear')
with __import__('torch').no_grad():
    next(reader.model.perception.pose_head.parameters()).add_(1)
records, _, _ = R.observe(reader, items, Artifact(reader.artifact_manifest),
                         trace_lines=False, audit=False, monitor=False)
print('perturbed_error', records[0]['error'])

proof = ROOT/'equality.json'
proof.write_text(json.dumps(dict(schema='eat1-cache-proof-v1',
    items=[dict(id=i, live='same', cached='same') for i in range(50)])))
finding = dict(clause='A5', rule='A5.cache', file='memo.py', line=1,
    function='memo', detail='live per-row memo with equality proof', text='cached_tower', executed=True)
judged = R.judge_a5([], [], [finding], True, sandbox={'status':'PASS'},
                    perturb={'status':'PASS'}, cache_proof=proof)
print('valid_cache_proof', judged['cache_proof']['status'], 'A5', judged['status'])

findings, _ = S.scan([ROOT/'benign.py'])
print('benign_scanner', json.dumps([(f['function'], f['rule'], f['line']) for f in findings]))

for name in ('readonly', 'readwrite', 'native', 'mapped', 'child'):
    report = json.loads((ROOT/'results'/name/'EAT1_REPORT.json').read_text())
    print('file_access', name, report['clauses']['A1']['status'],
          'sandbox', report['clauses']['A5']['parts']['i'])

bad = []
for line in (ROOT.parent/'COPY_FILES.sha256').read_text().splitlines():
    digest, name = line.split(maxsplit=1)
    if sha256(ROOT.parent/name) != digest:
        bad.append(name)
print('original_hash_mismatches', bad)
print('workspace_bytes', sum(p.stat().st_size for p in ROOT.parent.rglob('*') if p.is_file()))
