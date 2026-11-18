from pathlib import Path
from collections import Counter
import difflib,hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/merge11';T=L/'work/tree_r1'
priors=[(L.parent/'wn2/work/n1fix2/CHANGED_COVERAGE.json',L.parent/'wn2/work/tree_r1'),
        (L.parent/'w10/work/build10/CHANGED_COVERAGE.json',L.parent/'w10/work/tree_r1')]
mapped={}
for index,(path,root) in enumerate(priors):
    old=json.loads(path.read_text());out=B/'proofs'/('inherited_exact_'+str(index));out.mkdir(exist_ok=True)
    hashes={};hits={};mapping={}
    for row in old['statements']:
        p=T/row['file']
        if not p.is_file():continue
        same=hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
        if same:
            hashes[row['file']]=row['sha256']
            if row['executed']:hits.setdefault(row['file'],[]).append(row['line'])
        if not row['executed'] and row['classification'] in ('GPU','frame-host','model-loader'):
            name=row['file']
            if name not in mapping:
                a=(root/name).read_bytes();assert hashlib.sha256(a).hexdigest()==row['sha256']
                remap={}
                for tag,i,j,k,m in difflib.SequenceMatcher(None,a.decode().splitlines(),p.read_text().splitlines(),autojunk=False).get_opcodes():
                    if tag=='equal':remap.update({x+1:k+x-i+1 for x in range(i,j)})
                mapping[name]=remap
            if row['line'] in mapping[name]:mapped[(name,mapping[name][row['line']])]=dict(row,classification_source=str(path))
    for name,value in [('source_hashes',hashes),('hits',hits),('results',dict(complete=True,coverage_code_filter='compiled-source fingerprint',source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))]:
        (out/(name+'.json')).write_text(json.dumps(value)+'\n')
sources=[p.parent for p in (B/'proofs').rglob('source_hashes.json') if 'frozen' not in p.parts and (p.parent/'hits.json').is_file() and (p.parent/'results.json').is_file()]
subprocess.run([sys.executable,'-I','-s','-B',str(L/'work/n1fix2/coverage.py'),*map(str,sources)],check=True)
value=json.loads((L/'work/n1fix2/CHANGED_COVERAGE.json').read_text())
for row in value['statements']:
    prior=mapped.get((row['file'],row['line']))
    if not row['executed']:
        row['classification']='CPU-reachable unresolved'
        if prior:row.update(classification=prior['classification'],reason=prior.get('reason'),classification_source=prior['classification_source'])
value['classes']=dict(Counter(r['classification'] for r in value['statements']))
(B/'CHANGED_COVERAGE.json').write_text(json.dumps(value,indent=2)+'\n')
gaps=[r for r in value['statements'] if r['classification']=='CPU-reachable unresolved']
(B/'GAPS.json').write_text(json.dumps(gaps,indent=2)+'\n')
print(json.dumps(dict(classes=value['classes'],gaps=[(r['file'],r['line'],r['text']) for r in gaps])))
