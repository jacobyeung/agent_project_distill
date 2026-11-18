from pathlib import Path
import json,re,hashlib
L=Path(__file__).resolve().parents[2];N=L.parent;B=L/'work/n1fix2';M=L/'work/merge11'
# Localize all metadata dependencies together, retaining immutable input bytes when unchanged.
def relocate(v):
    if isinstance(v,dict):return {k:relocate(x) for k,x in v.items()}
    if isinstance(v,list):return [relocate(x) for x in v]
    if isinstance(v,str):
        for prefix in (str(N/'wn2'),str(N/'w9f'),str(N/'w10')):
            if v.startswith(prefix+'/'):return str(L)+v[len(prefix):]
    return v
for p in (B/'inputs').glob('*.json'):
    try:value=json.loads(p.read_text())
    except json.JSONDecodeError:continue
    new=relocate(value)
    if new!=value:p.write_text(json.dumps(new,indent=2)+'\n')
def refresh(v):
    if isinstance(v,list):return [refresh(x) for x in v]
    if not isinstance(v,dict):return v
    v={k:refresh(x) for k,x in v.items()}
    if isinstance(v.get('path'),str) and v.get('sha256'):
        p=Path(v['path'])
        if p.is_relative_to(B/'inputs') and p.is_file():v['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    return v
for _ in range(5):
    for p in (B/'inputs').glob('*.json'):
        try:value=json.loads(p.read_text())
        except json.JSONDecodeError:continue
        new=refresh(value)
        if new!=value:p.write_text(json.dumps(new,indent=2)+'\n')
# Keep helper metadata locations stable and route every proof output to merge11.
for p in B.iterdir():
    if not p.is_file() or p.suffix not in ('.py','.sh'):continue
    s=p.read_text().replace('work/n1fix2/proofs','work/merge11/proofs/n1')
    p.write_text(s)
for name in ('r1_edges','prepared_guards','forward','contracts','registry_closure','half','scene','extent','checkpoint','target_prepared','review_variants','row_delta','host_checks','faults','kits','audit','packet'):
    (M/'proofs/n1'/name).mkdir(parents=True,exist_ok=True)
# Existing proof fixtures used as read-only inputs remain available at their explicit old locations.
for name in ('PACKET_INPUTS.json',):
    rows=json.loads((B/name).read_text())
    for row in rows:
        path=L/row['source']
        if not path.is_file():path=L/row['target']
        assert path.is_file(),str(path)
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'],str(path)
        row['source']=str(path.relative_to(L))
        row['target']=row['target'].replace('work/n1fix2/proofs','work/merge11/proofs/n1')
        target=L/row['target'];target.parent.mkdir(parents=True,exist_ok=True)
        if not target.exists():target.symlink_to(path)
    (B/name).write_text(json.dumps(rows,indent=2)+'\n')
print('Localized input metadata and final proof output paths.')
