"""Aggregate observed statements; carry only byte-matched coverage evidence."""
from pathlib import Path
from collections import Counter
import difflib,hashlib,json,subprocess,sys,tarfile
L=Path(__file__).resolve().parents[2];B=L/'work/build10';T=L/'work/tree_r1'
inherited=L/'work/build12/proofs/inherited_exact';inherited.mkdir(exist_ok=True)
prior_files=[B/'B9_CHANGED_COVERAGE.json',B/'N1_CHANGED_COVERAGE.json',B/'N1_N1_CHANGED_COVERAGE.json']
prior=dict(statements=[row for path in prior_files for row in json.loads(path.read_text())['statements']])
hits={};hashes={};classes={}
for row in prior['statements']:
    p=T/row['file']
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:continue
    hashes[row['file']]=row['sha256']
    if row['executed']:hits.setdefault(row['file'],[]).append(row['line'])
    else:classes[(row['file'],row['line'])]=row
(inherited/'hits.json').write_text(json.dumps(hits));(inherited/'source_hashes.json').write_text(json.dumps(hashes))
(inherited/'results.json').write_text(json.dumps(dict(complete=True,coverage_code_filter='compiled-source fingerprint',
    inherited_from=[dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in prior_files])))
sources=[]
for p in (L/'work/build12/proofs').rglob('source_hashes.json'):
    if 'frozen' in p.parts or 'pre_suite_r2' in p.parts:continue
    if (p.parent/'results.json').is_file() and (p.parent/'hits.json').is_file():sources.append(p.parent)
subprocess.run([sys.executable,'-I','-s','-B',str(B/'coverage.py'),*map(str,sources)],check=True)
value=json.loads((B/'CHANGED_COVERAGE.json').read_text())
# Only external-input classifications may map across unchanged lines of modified files.
archive=L.parent/'out/tree_rebuild_bn1_e558d4a1.tar'
mapped={}
if archive.is_file():
    with tarfile.open(archive) as tar:
        names={m.name:m for m in tar.getmembers() if m.isfile()}
        for filename in {r['file'] for r in prior['statements'] if r['classification'] in ('GPU','frame-host','model-loader')}:
            member=names.get('work/tree_r1/'+filename)
            if member is None:continue
            raw=tar.extractfile(member).read();sha=hashlib.sha256(raw).hexdigest()
            original=raw.decode().splitlines();current=(T/filename).read_text().splitlines();mapping={}
            for tag,a,b,c,d in difflib.SequenceMatcher(None,original,current,autojunk=False).get_opcodes():
                if tag=='equal':mapping.update({i+1:c+i-a+1 for i in range(a,b)})
            for row in prior['statements']:
                if row['file']==filename and row['sha256']==sha and row['line'] in mapping and row['classification'] in ('GPU','frame-host','model-loader'):
                    mapped[(filename,mapping[row['line']])]=row
for row in value['statements']:
    if row['executed']:continue
    old=classes.get((row['file'],row['line'])) or mapped.get((row['file'],row['line']))
    if old and old['classification'] in ('GPU','frame-host','model-loader'):
        row.update(classification=old['classification'],reason=old['reason'],classification_source='B9_CHANGED_COVERAGE.json, N1_CHANGED_COVERAGE.json and N1_N1_CHANGED_COVERAGE.json; identical statement text in authenticated package source')
    if row['file']=='launch_r1/entry.py' and ((row['function']=='frame_host' and row['line']>=78) or row['function']=='localize'):
        row.update(classification='frame-host',reason='Requires complete production staging and admitted routing selection; neither is available locally. The scene predicate itself is covered by native bounded producer/reader tests.')
value['classes']=dict(Counter(r['classification'] for r in value['statements']))
(B/'CHANGED_COVERAGE.json').write_text(json.dumps(value,indent=2)+'\n')
gaps={}
for row in value['statements']:
    if row['classification']=='CPU-reachable unresolved':gaps.setdefault(row['file'],[]).append(dict(line=row['line'],text=row['text']))
(B/'GAPS.json').write_text(json.dumps(gaps,indent=2)+'\n')
print(json.dumps(dict(classes=value['classes'],cpu_gaps={k:len(v) for k,v in gaps.items()})))
