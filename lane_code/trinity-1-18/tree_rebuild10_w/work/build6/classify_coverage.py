"""Preserve justified external-input classifications across unchanged source lines."""
import collections,difflib,hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build6';T=L/'work/tree_r1';prior=L/'work/contracts_r6/tree_copy'
old=json.loads((L/'work/build5/CHANGED_COVERAGE.json').read_text());value=json.loads((B/'CHANGED_COVERAGE.json').read_text())
mapped={};maps={}
for row in old['statements']:
    if row['classification'] not in ('frame-host','model-loader','GPU'):continue
    name=row['file']
    if name not in maps:
        path=prior/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
        a=path.read_text().splitlines();b=(T/name).read_text().splitlines();mapping={}
        for tag,i,j,k,m in difflib.SequenceMatcher(None,a,b,autojunk=False).get_opcodes():
            if tag=='equal':mapping.update({x+1:k+x-i+1 for x in range(i,j)})
        maps[name]=mapping
    line=maps[name].get(row['line'])
    if line:mapped[(name,line,row['function'])]=row
for row in value['statements']:
    if row['executed']:continue
    previous=mapped.get((row['file'],row['line'],row['function']))
    # Do not carry hard-coded line-number classifications onto changed code.
    if row['file'] in ('launch_r2/host.py','launch_r2/entry.py'):
        row['classification']='CPU-reachable unresolved';row.pop('reason',None)
    if previous:
        row['classification']=previous['classification']
        row['reason']=previous['reason'].replace('step-544 init archive','selected init archive').replace('step-544 vocabulary witness','selected-init vocabulary witness')
        row['classification_source']=dict(path='work/build5/CHANGED_COVERAGE.json',line=previous['line'],unchanged_source=True)
    if row['file']=='launch_r2/host.py' and row['text'] in ('from student_pilot.r2_admission import family_admission',"family_admission(report['intake'])", "cfg['r2_family_admission'] = file_pin(output/'a/materialization.json')"):
        row['classification']='frame-host';row['reason']='Missing authenticated full-store RGB and scene-admission receipts on an admitted frame host; the local full-store guard remains enabled.'
    if row['file']=='launch_r2/entry.py' and ('r2_admission import check_family_receipt' in row['text'] or "check_family_receipt(cfg.get('r2_family_admission'))" in row['text']):
        row['classification']='frame-host';row['reason']='Missing authenticated full-store host receipts and the independent launch authorization required before the final family gate.'
value['classes']=dict(collections.Counter(r['classification'] for r in value['statements']))
(B/'CHANGED_COVERAGE.json').write_text(json.dumps(value,indent=2)+'\n')
gaps={}
for row in value['statements']:
    if row['classification']=='CPU-reachable unresolved':gaps.setdefault(row['file'],[]).append((row['line'],row['text']))
(B/'GAPS.json').write_text(json.dumps(gaps,indent=2)+'\n')
print(json.dumps(dict(classes=value['classes'],gaps={k:len(v) for k,v in gaps.items()})))
