"""Use authenticated inherited observations only when complete source bytes match."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1'
prior=json.loads((B/'B9F_COVERAGE.json').read_text())
out=L/'work/build12/proofs/inherited_exact';out.mkdir(exist_ok=True)
hashes={};hits={};classes={}
for row in prior['statements']:
    path=T/row['file']
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:continue
    hashes[row['file']]=row['sha256']
    if row['executed']:hits.setdefault(row['file'],[]).append(row['line'])
    else:classes[(row['file'],row['line'])]=row
(out/'source_hashes.json').write_text(json.dumps(hashes))
(out/'hits.json').write_text(json.dumps(hits))
(out/'results.json').write_text(json.dumps(dict(complete=True,coverage_code_filter='compiled-source fingerprint',
    inherited_source='B9F_COVERAGE.json',sha256=hashlib.sha256((B/'B9F_COVERAGE.json').read_bytes()).hexdigest())))
sources=[p.parent for p in (L/'work/build12/proofs').rglob('source_hashes.json') if 'frozen' not in p.parts and
    (p.parent/'hits.json').exists() and (p.parent/'results.json').exists()]
subprocess.run([sys.executable,'-I','-s','-B',str(B/'coverage.py'),*map(str,sources)],check=True)
result=json.loads((B/'CHANGED_COVERAGE.json').read_text())
for row in result['statements']:
    old=classes.get((row['file'],row['line']))
    if not row['executed'] and old and old['classification'] in ('GPU','frame-host','model-loader'):
        row['classification']=old['classification'];row['reason']=old.get('reason')
result['classes']=dict(Counter(r['classification'] for r in result['statements']))
(B/'CHANGED_COVERAGE.json').write_text(json.dumps(result,indent=2)+'\n')
gaps={}
for row in result['statements']:
    if row['classification']=='CPU-reachable unresolved':gaps.setdefault(row['file'],[]).append(row['line'])
(B/'GAPS.json').write_text(json.dumps(gaps,indent=2)+'\n')
print(json.dumps(result['classes']))
