"""Audit every POOL member and retain bounded, source-bound examples."""
from pathlib import Path
import collections, gzip, hashlib, json, sys
L = Path(__file__).resolve().parents[1]
T = L/'work/trees/r5_applied'
X = L/'work/real/x'
sys.path.insert(0, str(T))
from student_pilot.training_contract import audit_training_contract, call_responses
manifest = json.loads((X/'66caacf5c9191457.json').read_text())
import ast, inspect, re
from student_pilot import phrases
original = phrases.source_template_candidates
source = inspect.getsource(original)
variants = {}
replacements = {
 'vocabulary': ("            for category, labels in vocabulary().items():\n                if normalize_phrase(category) in names:\n                    names.update(phrase_set(labels))", "            pass"),
 'templates': ("for pattern in (ANGLE_PATTERNS if new_contracts() else ()):", "for pattern in ():"),
 'aliases': ("names.update(aliases[n] for n in tuple(names) if n in aliases)", "pass")}
for name,(old,new) in replacements.items():
    assert source.count(old)==1
    namespace=dict(phrases.__dict__)
    exec(compile(source.replace(old,new),str(T/'student_pilot/phrases.py'),'exec'),namespace)
    variants[name]=namespace['source_template_candidates']
ablation={k:dict(admitted_only=0,examples=[]) for k in variants}
bare_gaps=dict(rows=0,events=0,examples=[],rule='Removed in both epochs: no sealed POOL row uses the bare scalar form')
report = dict(source_archive=str(L/'work/real/eb3429c5.tar'), source_manifest=str(X/'66caacf5c9191457.json'),
              audit_source=str(T/'student_pilot/training_contract.py'), members={}, by_type={})
def add(store, typ, reason, row, path, line):
    c = store.setdefault(typ, dict(rows=0, admitted=0, deferred=0, reasons={}))
    c['rows'] += 1
    examples=c.setdefault('examples',{'admitted':[],'deferred':[]})['deferred' if reason else 'admitted']
    if len(examples)<3:examples.append(dict(qid=row.get('qid'),source=str(path),line=line))
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
                if reason is None:
                    for name,fn in variants.items():
                        phrases.source_template_candidates=fn
                        refused=audit_training_contract([row])[0]
                        phrases.source_template_candidates=original
                        if refused:
                            ablation[name]['admitted_only']+=1
                            if len(ablation[name]['examples'])<3:
                                ablation[name]['examples'].append(dict(qid=row.get('qid'),source=str(path),line=line,reason=refused))
                bare=[(call,text) for call,text in call_responses(row) if isinstance(call,str) and call.startswith('<gap ') and isinstance(text,str) and re.fullmatch(r'\s*(?:<tool_response>)?\s*\d+\.\d{2} m\s*(?:</tool_response>)?\s*',text)]
                if bare:
                    bare_gaps['rows']+=1;bare_gaps['events']+=len(bare)
                    if len(bare_gaps['examples'])<3:bare_gaps['examples'].append(dict(qid=row.get('qid'),source=str(path),line=line,revision=row.get('trace_revision',row.get('spec_version'))))
                add(counts, typ, reason, row, path, line)
                add(report['by_type'], typ, reason, row, path, line)
        report['members'][dataset['name']+':'+role] = dict(source=str(path), sha256=pin['sha256'], by_type=counts)
        print(dataset['name'], role, {k:(v['rows'],v['deferred'],list(v['reasons'])) for k,v in counts.items()}, flush=True)
report['totals'] = {k:sum(v[k] for v in report['by_type'].values()) for k in ('rows','admitted','deferred')}
report['ablations']=ablation
report['legacy_bare_gaps']=bare_gaps
report['counting'] = 'Source records, with admitted and packed representations reported separately; not unique qids.'
(L/'work/REAL_ROW_AUDIT_R5.json').write_text(json.dumps(report, indent=2)+'\n')
