"""Audit every POOL member and retain bounded, source-bound examples."""
from pathlib import Path
import collections, gzip, hashlib, json, sys
L = Path(__file__).resolve().parents[1]
T = L/'work/trees/r4_applied'
X = L/'work/real/x'
sys.path.insert(0, str(T))
from student_pilot.training_contract import audit_training_contract, call_responses
manifest = json.loads((X/'66caacf5c9191457.json').read_text())
report = dict(source_archive=str(L/'work/real/eb3429c5.tar'), source_manifest=str(X/'66caacf5c9191457.json'),
              audit_source=str(T/'student_pilot/training_contract.py'), members={}, by_type={})
def add(store, typ, reason, row, path, line):
    c = store.setdefault(typ, dict(rows=0, admitted=0, deferred=0, reasons={}))
    c['rows'] += 1
    c['deferred' if reason else 'admitted'] += 1
    if reason:
        r = c['reasons'].setdefault(reason, dict(count=0, examples=[]))
        r['count'] += 1
        if len(r['examples']) < 3:
            r['examples'].append(dict(qid=row.get('qid'), source=str(path), line=line))
for dataset in manifest['sets']:
    for role, pin in dataset['files'].items():
        path = X/(pin['sha256'][:16]+'.jsonl.gz')
        assert hashlib.sha256(path.read_bytes()).hexdigest() == pin['sha256']
        counts = {}
        with gzip.open(path, 'rt') as stream:
            for line, text in enumerate(stream, 1):
                row = json.loads(text)
                typ = row.get('question_type', row.get('type', row.get('routing', {}).get('question_type', 'unknown')))
                reason = audit_training_contract([row])[0]
                add(counts, typ, reason, row, path, line)
                add(report['by_type'], typ, reason, row, path, line)
        report['members'][dataset['name']+':'+role] = dict(source=str(path), sha256=pin['sha256'], by_type=counts)
        print(dataset['name'], role, {k:(v['rows'],v['deferred'],list(v['reasons'])) for k,v in counts.items()}, flush=True)
report['totals'] = {k:sum(v[k] for v in report['by_type'].values()) for k in ('rows','admitted','deferred')}
report['counting'] = 'Source records, with admitted and packed representations reported separately; not unique qids.'
(L/'work/REAL_ROW_AUDIT_R4.json').write_text(json.dumps(report, indent=2)+'\n')
