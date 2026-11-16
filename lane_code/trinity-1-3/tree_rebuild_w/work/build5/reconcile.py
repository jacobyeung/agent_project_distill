"""Map each prior unresolved statement to the sealed current coverage receipt."""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
L=Path(__file__).resolve().parents[2]
output=L/'work/build5/proofs/lineage';output.mkdir(parents=True,exist_ok=True)
diff=output/'BUILD4.diff';seal=output/'BUILD4_SEAL.json'
if not diff.exists():
    original=json.loads((L/'out/TREE_SEAL.json').read_text())
    assert original['tree_sha256']=='0fc11a63209cc6e73827149a78dea070aa72f279ec3ed7f79d8d3777be3f4320'
    diff.write_bytes((L/'out/TREE.diff').read_bytes())
    seal.write_text(json.dumps(original))
expected=json.loads(seal.read_text())['files']
old=json.loads((L/'work/build4/CHANGED_COVERAGE.json').read_text())
current=json.loads((L/'work/build5/CHANGED_COVERAGE.json').read_text())
index={(r['file'],r['line']):r for r in current['statements']}
selected=[r for r in old['statements'] if r['classification']=='CPU-reachable, unresolved']
names={r['file'] for r in selected}
chunks={};name=None
for line in diff.read_text().splitlines(keepends=True):
    if line.startswith('--- a/'):
        name=line[6:].strip();chunks[name]=[]
    elif name is not None:chunks[name].append(line)
records=[]
for name in sorted(names):
    base=L/'work/base/tree_b01ce449'/name
    prior=base.read_text().splitlines(keepends=True) if base.exists() else []
    rebuilt=[];cursor=0;active=False
    for line in chunks.get(name,[]):
        if line.startswith('+++ '):continue
        if line.startswith('@@ '):
            match=re.match(r'@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@',line)
            start=max(0,int(match[1])-1)
            rebuilt.extend(prior[cursor:start]);cursor=start;active=True
        elif active and line.startswith((' ','-')):
            assert prior[cursor]==line[1:],(name,cursor,line)
            cursor+=1
            if line.startswith(' '):rebuilt.append(line[1:])
        elif active and line.startswith('+'):rebuilt.append(line[1:])
        elif line.startswith('\\'):continue
        else:raise ValueError('Unexpected source diff record')
    rebuilt.extend(prior[cursor:])
    raw=''.join(rebuilt)
    assert hashlib.sha256(raw.encode()).hexdigest()==expected[name],name
    before=raw.splitlines();after=(L/'work/tree_r1'/name).read_text().splitlines()
    mapping={};replacements={}
    for tag,a,b,c,d in difflib.SequenceMatcher(None,before,after,autojunk=False).get_opcodes():
        if tag=='equal':mapping.update({a+i+1:c+i+1 for i in range(b-a)})
        else:
            for number in range(a+1,b+1):replacements[number]=(c+1,d)
    for row in [r for r in selected if r['file']==name]:
        assert before[row['line']-1].strip()==row['text']
        record=dict(file=name,prior_line=row['line'],prior_text=row['text'],prior_sha256=expected[name])
        if name=='launch_r2/host.py' and row['line'] in (227,228,229):
            values=[r for r in current['statements'] if r['file']=='launch_r2/checklist.py' and r['function']=='stage_inputs']
            assert values and all(r['executed'] for r in values)
            record.update(classification='replacement observed',
                current_file='launch_r2/checklist.py',current_lines=[r['line'] for r in values],
                current_sha256=values[0]['sha256'],
                reason='Physical input staging moved into the mandatory checklist action, before packet-byte resolution; the real staging action executes in the host-order proof.')
            records.append(record)
            continue
        line=mapping.get(row['line'])
        if line is not None:
            value=index.get((name,line))
            assert value is not None,(name,line)
            record.update(current_line=line,classification=value['classification'],
                          current_sha256=value['sha256'],reason=value.get('reason'))
        else:
            a,b=replacements[row['line']]
            values=[r for r in current['statements'] if r['file']==name and a<=r['line']<=b]
            classification='replacement observed' if values and all(r['executed'] for r in values) else 'revised source; inspect current statement coverage'
            if not values and not after[a-1:b]:
                relocated=[r for r in current['statements'] if r['file']==name and r['text']==row['text']]
                if len(relocated)==1:
                    values=relocated;classification=values[0]['classification']
                    record['mapping']='Unique exact statement relocated within the same source file'
                    record['reason']=values[0].get('reason')
                else:
                    assert name in ('student_pilot/carrier_c1_run.py','student_pilot/grounding_eval.py'),(name,row)
                    assert row['text'].startswith(('from .r2_policy import legacy_reader_guard','legacy_reader_guard('))
                    classification='obsolete redundant post-refusal code'
                    record['reason']='An unconditional unsupported_entry refusal precedes this unreachable redundant guard; the refusal remains covered by the current entrypoint tests.'
            record.update(classification=classification,
                          current_lines=[r['line'] for r in values],
                          current_classes=dict(Counter(r['classification'] for r in values)),
                          replacement_text=after[a-1:b])
        records.append(record)
value=dict(prior_source='work/build4/CHANGED_COVERAGE.json',
           current_source='work/build5/CHANGED_COVERAGE.json',
           prior_unresolved=len(selected),classes=dict(Counter(r['classification'] for r in records)),
           statements=records)
(output/'RECONCILIATION.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k!='statements'}))
