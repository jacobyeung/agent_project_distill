from pathlib import Path
from collections import Counter
import difflib,hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1'
old=json.loads((B/'inherited/CHANGED_COVERAGE.json').read_text())
P=L/'work/merge11/proofs/n1/inherited_exact';P.mkdir(exist_ok=True)
hashes={};hits={};classes={}
for row in old['statements']:
    p=T/row['file']
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:continue
    hashes[row['file']]=row['sha256']
    if row['executed']:hits.setdefault(row['file'],[]).append(row['line'])
    else:classes[(row['file'],row['line'])]=row
(P/'hits.json').write_text(json.dumps(hits));(P/'source_hashes.json').write_text(json.dumps(hashes))
(P/'results.json').write_text(json.dumps(dict(complete=True,coverage_code_filter='compiled-source fingerprint',
    source='work/n1fix2/inherited/CHANGED_COVERAGE.json',sha256=hashlib.sha256((B/'inherited/CHANGED_COVERAGE.json').read_bytes()).hexdigest())))
proofs=[p.parent for p in (L/'work/merge11/proofs/n1').rglob('source_hashes.json') if 'frozen' not in p.parts and
        (p.parent/'hits.json').is_file() and (p.parent/'results.json').is_file()]
subprocess.run([sys.executable,'-I','-s','-B',str(B/'coverage.py'),*map(str,proofs)],check=True)
v=json.loads((B/'CHANGED_COVERAGE.json').read_text())
mapped={}
for name in {r['file'] for r in old['statements'] if r['classification'] in ('GPU','frame-host','model-loader')}:
    prior=B/'original'/name
    if not prior.is_file():continue
    raw=prior.read_bytes();sha=hashlib.sha256(raw).hexdigest();mapping={}
    for tag,a,b,c,d in difflib.SequenceMatcher(None,raw.decode().splitlines(),(T/name).read_text().splitlines(),autojunk=False).get_opcodes():
        if tag=='equal':mapping.update({i+1:c+i-a+1 for i in range(a,b)})
    for row in old['statements']:
        if row['file']==name and row['sha256']==sha and row['line'] in mapping and row['classification'] in ('GPU','frame-host','model-loader'):
            mapped[(name,mapping[row['line']])]=row
host_lines=(T/'launch_r1/entry.py').read_text().splitlines()
host_start=next(i for i,line in enumerate(host_lines,1) if 'from launch_r2.staging import' in line)
host_end=next(i for i,line in enumerate(host_lines,1) if "result['status'] = 'PASS'" in line)
for row in v['statements']:
    if row['executed']:continue
    prior=classes.get((row['file'],row['line'])) or mapped.get((row['file'],row['line']))
    if prior:
        row.update(classification=prior['classification'],reason=prior.get('reason'),classification_source='Authenticated unchanged statement in build 9fix')
    if row['file']=='launch_r1/entry.py' and row['function'] in ('frame_host','localize') and host_start<=row['line']<=host_end:
        row.update(classification='frame-host',reason='Production staging closure, full admitted stores and regenerated selection are unavailable. No local replacement for the production preparation is used.')
v['classes']=dict(Counter(r['classification'] for r in v['statements']))
(B/'CHANGED_COVERAGE.json').write_text(json.dumps(v,indent=2)+'\n')
gaps=[r for r in v['statements'] if r['classification']=='CPU-reachable unresolved']
(B/'GAPS.json').write_text(json.dumps(gaps,indent=2)+'\n')
print(json.dumps(dict(classes=v['classes'],gaps=[(r['file'],r['line'],r['text']) for r in gaps])))
