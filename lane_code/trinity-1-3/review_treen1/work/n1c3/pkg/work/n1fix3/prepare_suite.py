from pathlib import Path
import hashlib,json,re
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';N=L.parent
for name in ('CARRIED_BLOCKERS.json','FINAL_PASS.json','SUITE_COMPARISON.json','CHANGED_COVERAGE.json','N1_CHANGED_COVERAGE.json','FINAL_STAGE.json','RESUME.json'):
    p=N/'work/build_n1'/name
    if p.exists():(B/('N1_'+name)).write_bytes(p.read_bytes())
# Stage only the harness's named small packet inputs from the copied package.
rows=json.loads((B/'PACKET_INPUTS.json').read_text());changes=[]
for row in rows:
    src=L/row['source'];dst=L/row['target']
    if not src.exists():
        candidate=L/'work/build_n1/proofs/packet'/Path(row['target']).relative_to('work/n1fix3/proofs/packet')
        if candidate.exists():src=candidate
    assert src.is_file(),str(src)
    dst.parent.mkdir(parents=True,exist_ok=True)
    if not dst.exists():dst.write_bytes(src.read_bytes())
    changes.append(dict(source=str(src),target=str(dst),sha256=hashlib.sha256(src.read_bytes()).hexdigest(),declared=row['sha256']))
(B/'PACKET_STAGING.json').write_text(json.dumps(changes,indent=2)+'\n')
print('Packet support staged',len(changes))
# A complete search records remaining parent-root mentions for read/write review.
hits=[]
pattern=re.compile(r'/scratch/jjyeung/orch_n30/tree_rebuild_w/wn3/wn2(?:_w)?/(?!w9f(?:/|\b))')
for root in (B,L/'work/tree_r1',L/'work/contracts_r6',L/'fixtures'):
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in ('.py','.sh','.json','.yaml','.yml','.toml'):continue
        if 'proofs' in p.parts:continue
        try:lines=p.read_text().splitlines()
        except UnicodeError:continue
        for i,line in enumerate(lines,1):
            if pattern.search(line):hits.append(dict(path=str(p.relative_to(L)),line=i,text=line[:240]))
(B/'PATH_SEARCH.json').write_text(json.dumps(hits,indent=2)+'\n')
print('Remaining explicit parent-root mentions',len(hits))
