from pathlib import Path
import base64,hashlib,json,re
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3';F=L; prior=L/'work/build9fix'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for name in ('CHANGED_COVERAGE.json','KIT_RESULT.json','SUITE_COMPARISON.json','FINAL_PASS.json',
             'proofs/suite_base/results.json','proofs/suite_base/source_hashes.json',
             'proofs/suite_tree/results.json','proofs/suite_tree/source_hashes.json',
             'proofs/text/RESULT.json','proofs/extent_admission/RESULT.json',
             'proofs/division/RESULT.json','proofs/audit/INFERENCE_COMPONENTS.json'):
    source=F/'work/build9fix'/name
    if source.is_file():
        target=B/'inherited'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(source.read_bytes());records.append(dict(path=str(source),sha256=sha(source),target=str(target.relative_to(L))))
for group in ('generator','legacy','r2'):
    for name in ('GROUP_RECEIPT.json','results.json','hits.json','source_hashes.json'):
        source=F/'work/build9fix/proofs/suite_base'/group/name
        if source.is_file():
            target=B/'inherited/suite_base'/group/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(source.read_bytes());records.append(dict(path=str(source),sha256=sha(source),target=str(target.relative_to(L))))
(B/'INHERITED_RECEIPTS.json').write_text(json.dumps(records,indent=2)+'\n')
# Recover the two small source lists from the already staged kit payloads.
capsule=json.loads((prior/'kits/r1/k/s.json').read_text())
staging=json.loads(base64.b64decode(capsule['payload']))
local_by_sha={}
inputs=B/'inputs';inputs.mkdir(exist_ok=True)
for name,entry in staging['entries'].items():
    if 'payload' in entry:
        raw=base64.b64decode(entry['payload'])
        h=hashlib.sha256(raw).hexdigest()
        if h in ('02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411','0d28fdd432b02ae96b6ce2aaa840b744005291a540920ce48409f0e8c90276ad'):
            p=inputs/(h[:12]+'.json');p.write_bytes(raw);local_by_sha[h]=p
def localize(v):
    if isinstance(v,dict):
        if v.get('sha256') in local_by_sha:
            return dict(v,path=str(local_by_sha[v['sha256']]))
        return {k:localize(x) for k,x in v.items()}
    if isinstance(v,list):return [localize(x) for x in v]
    if isinstance(v,str):
        for old in (str(F),str(L.parent),'/scratch/jjyeung/orch_n30/tree_rebuild_w/wn3'):
            if v==old or v.startswith(old+'/'):
                v=str(L)+v[len(old):];break
        return v.replace('/work/build9fix/inputs/','/work/n1fix3/inputs/')
    return v
for p in (prior/'inputs').iterdir():
    if p.is_file():
        if p.suffix=='.json':
            value=json.loads(p.read_text());new=localize(value)
            (inputs/p.name).write_bytes(p.read_bytes() if new==value else (json.dumps(new,indent=2)+'\n').encode())
        else:(inputs/p.name).write_bytes(p.read_bytes())
def refresh(v):
    if isinstance(v,dict):
        result={k:refresh(x) for k,x in v.items()}
        if 'path' in result and 'sha256' in result:
            p=Path(result['path'])
            if p.is_relative_to(inputs) and p.is_file(): result['sha256']=sha(p)
        return result
    if isinstance(v,list):return [refresh(x) for x in v]
    return v
for _ in range(3):
    for p in inputs.glob('*.json'):
        if p in local_by_sha.values():continue
        value=json.loads(p.read_text());new=refresh(value)
        if new!=value:p.write_text(json.dumps(new,indent=2)+'\n')
# Install packet references without copying row datasets.
rows=json.loads((prior/'PACKET_INPUTS.json').read_text())
for row in rows:
    source=L/row['target']; target=L/row['target'].replace('work/build9fix/','work/n1fix3/')
    assert sha(source)==row['sha256']
    target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():target.symlink_to(source)
    row.update(source=str(source.relative_to(L)),target=str(target.relative_to(L)))
(B/'PACKET_INPUTS.json').write_text(json.dumps(rows,indent=2)+'\n')
p=B/'stage9.py';s=p.read_text().replace("L.parent/'work/build9/kits/RESULTS.json'", "B/'inherited/KIT_RESULT.json'")
s=s.replace("v for v in inherited if", "v for v in inherited.values() if")
p.write_text(s)
p=B/'make_delivery.py';s=p.read_text().replace('tree_rebuild_b9f_','tree_rebuild_bn1f_');p.write_text(s)
print(json.dumps(dict(receipts=len(records),local_staging_pins=len(local_by_sha))))
