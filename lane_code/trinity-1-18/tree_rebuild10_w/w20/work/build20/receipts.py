from pathlib import Path
import os,sys,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build20';O=B/'proofs/receipts';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(L/'work/tree_r1')
from student_pilot import r1_training as T, r1_handover as H
from student_pilot.p3_provenance import file_pin,load
from student_pilot.r1_persisted import scope
locations=load(L.parent/'ext/pwrap/P_LOCATIONS.json')
wanted={}
for variant,entry in locations.items():
    if isinstance(entry,dict):
        for name,pin in entry.get('streams',{}).items():wanted.setdefault(pin['sha256'],[]).append((variant,name,pin['path']))
for p in (L.parent/'inputs/p_runtime').rglob('*.json'):
    if p.stat().st_size>5_000_000:continue
    v=load(p)
    if not isinstance(v,dict):continue
    for name,pin in v.get('streams',{}).items():
        if 'sha256' in pin:wanted.setdefault(pin['sha256'],[]).append((p.name,name,pin['path']))
index={};scanned=0
for root in (L.parent/'inputs',L.parent/'ext',L/'fixtures'):
    for directory,dirs,files in os.walk(root):
        if len(Path(directory).relative_to(root).parts)>=10:dirs[:]=[]
        for name in files:
            p=Path(directory)/name
            if p.suffix in ('.db','.sqlite','.jsonl','.gz','.tar','.pt','.bin','.safetensors','.png','.jpg','.npz') or p.is_symlink() or p.stat().st_size>5_000_000:continue
            with p.open('rb') as f:
                if f.read(1) not in (b'{',b'['):continue
            scanned+=1;h=hashlib.sha256(p.read_bytes()).hexdigest();index.setdefault(h,str(p))
result=dict(search_roots=[str(L.parent/'inputs'),str(L.parent/'ext'),str(L/'fixtures')],maximum_depth=10,maximum_json_bytes=5_000_000,scanned=scanned,receipts=[],absent=[])
for h,uses in wanted.items():
    if h not in index:
        result['absent'].append(dict(sha256=h,uses=uses));continue
    pin=dict(path=index[h],sha256=h);receipt=load(index[h]);name=uses[0][1]
    identity=T.target_identity(dict(r1_training={},streams={name:pin}))
    result['receipts'].append(dict(pin=pin,uses=uses,schema=receipt.get('schema'),identity=identity,
                                 bound_receipt=H.pin_values(receipt)))
# Audit the authenticated runtime preparation's composite entry through the donor reader helper.
result['prepared']=[]
for p in (L.parent/'inputs/p_runtime').rglob('receipt.json'):
    if p.stat().st_size>5_000_000:continue
    v=load(p)
    if v.get('schema')!='c1-preparation-v1':continue
    for name,stream in v.get('streams',{}).items():
        h=stream.get('receipt',{}).get('sha256')
        if h not in index:continue
        record=dict(preparation=file_pin(p),stream=name)
        try:
            with scope(index):record['identity'],record['source_count']=H.prepared_stream_identity(load(index[h]),stream,name)
            record['status']='PASS'
        except (ValueError,OSError,KeyError) as error:record.update(status='REFUSE',error=str(error))
        result['prepared'].append(record)
(O/'RESULT.json').write_text(json.dumps(result,indent=2));m.save(O)
print(json.dumps({k:result[k] for k in ('scanned','absent','prepared')},indent=2))
print('available stream receipts',len(result['receipts']))
