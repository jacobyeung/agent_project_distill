from pathlib import Path
import hashlib,json,os
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';D=B/'inputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(v):
    if isinstance(v,dict):return {k:local(x) for k,x in v.items()}
    if isinstance(v,list):return [local(x) for x in v]
    if isinstance(v,str):
        if v.startswith(str(L)+'/'):return v
        roots=[str(L.parent/'wn2'),str(L.parent/'w9f'),str(L.parent),'/scratch/jjyeung/orch_n30/tree_rebuild']
        for root in roots:
            if v.startswith(root+'/'):
                v=str(L)+v[len(root):];break
        return v.replace('/work/n1fix2/','/work/n1fix3/')
    return v
for p in (L/'work/n1fix2/inputs').glob('*.json'):
    (D/p.name).write_bytes(p.read_bytes())
for p in D.glob('*.json'):
    try:value=json.loads(p.read_text())
    except json.JSONDecodeError:continue
    new=local(value)
    if new!=value:p.write_text(json.dumps(new,indent=2)+'\n')
def repin(v):
    if isinstance(v,dict):
        v={k:repin(x) for k,x in v.items()}
        if 'path' in v and 'sha256' in v:
            p=Path(v['path'])
            if p.is_relative_to(D) and p.is_file():v['sha256']=sha(p)
        return v
    if isinstance(v,list):return [repin(x) for x in v]
    return v
for _ in range(8):
    changed=False
    for p in D.glob('*.json'):
        try:value=json.loads(p.read_text())
        except json.JSONDecodeError:continue
        new=repin(value)
        if new!=value:p.write_text(json.dumps(new,indent=2)+'\n');changed=True
    if not changed:break
assert not changed,'Input pin graph did not settle'
cfg=json.loads((D/'config.json').read_text())
pin=cfg['r1_training']['mix'];(L/'out/MIX_R1.json').write_bytes(Path(pin['path']).read_bytes())
assert sha(L/'out/MIX_R1.json')==pin['sha256']
rows=json.loads((B/'PACKET_INPUTS.json').read_text())
for row in rows:
    source=L/row['target'].replace('work/n1fix3/','work/n1fix2/')
    assert source.is_file(),str(source)
    assert sha(source)==row['sha256'],str(source)
    target=L/row['target'];target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():target.symlink_to(source)
    row['source']=str(source.relative_to(L))
(B/'PACKET_INPUTS.json').write_text(json.dumps(rows,indent=2))
files=['test_runner.py','compact_tmp.py','run.sh','monitor9.py','proof_row_delta.py','proof_text.py',
       'proof_checkpoint.py','seal.py','stage9.py','package.py','make_delivery.py','packet_final.py',
       'PACKET_TEST.sh','PACKAGE_TEST.sh','requalification_gate.py','compare.py','coverage.py','coverage_current.py']
issues=[]
for name in files:
    for i,line in enumerate((B/name).read_text().splitlines(),1):
        if 'L.parent' in line or '/tree_rebuild/' in line or '/tree_rebuild_w/wn2' in line or '/tree_rebuild_w/w9f' in line:
            issues.append(dict(file=name,line=i,text=line))
(B/'EXECUTABLE_PATH_SEARCH.json').write_text(json.dumps(dict(files=files,issues=issues),indent=2))
assert not issues,issues
(B/'STATUS.md').write_text('Handover initialization checks and native table comparison are implemented. Focused tests are running. Harness paths and packet inputs are localized. GO=false. Evidence: EXECUTABLE_PATH_SEARCH.json.\n')
print(json.dumps(dict(localized_inputs=len(list(D.glob('*.json'))),packet_inputs=len(rows))))
