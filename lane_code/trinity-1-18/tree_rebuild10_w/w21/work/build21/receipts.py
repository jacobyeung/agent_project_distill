from pathlib import Path
import os,sys,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build21';O=B/'proofs/receipts';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/n1fix2')]
from monitor9 import Monitor
m=Monitor(L/'work/tree_r1')
from student_pilot import r1_training as T, r1_handover as H
from student_pilot.p3_provenance import file_pin,load,sha256
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
# Check every supplied fetch against its content manifest. The manifest's own
# self-entry describes the pre-finalized listing and is not a content input.
fetched=L.parent/'ext/preceipts/rc3'
result['fetched']=[]
for line in (fetched/'SHA256SUMS.txt').read_text().splitlines():
    h,name=line.split('  ',1)
    if name in ('./SHA256SUMS.txt','./FETCH_LOG.txt'):continue
    p=fetched/name;assert sha256(p)==h,(name,h)
    index[h]=str(p);result['fetched'].append(dict(path=str(p),sha256=h))
for h,uses in wanted.items():
    if h not in index:
        result['absent'].append(dict(sha256=h,uses=uses));continue
    pin=dict(path=index[h],sha256=h);receipt=load(index[h]);name=uses[0][1]
    with scope(index):identity=T.target_identity(dict(r1_training={},streams={name:pin}))
    result['receipts'].append(dict(pin=pin,uses=uses,schema=receipt.get('schema'),identity=identity,
                                 reader='r1_training.target_identity -> r1_handover.stream_identity',status='PASS',bound_receipt=H.pin_values(receipt)))
# Audit the authenticated runtime preparation's composite entry through the donor reader helper.
result['prepared']=[]
preparations=dict(index)
runtime_root=L.parent/'inputs/p_runtime'
for path in runtime_root.rglob('receipt.json'):
    if path.stat().st_size<=5_000_000:preparations[sha256(path)]=str(path)
for h0,path in sorted(preparations.items()):
    p=Path(path)
    try:v=load(p)
    except (ValueError,UnicodeDecodeError):continue
    if not isinstance(v,dict) or v.get('schema')!='c1-preparation-v1':continue
    if not p.is_relative_to(runtime_root) and not any(s.get('receipt',{}).get('sha256') in wanted for s in v.get('streams',{}).values()):continue
    for name,stream in v.get('streams',{}).items():
        h=stream.get('receipt',{}).get('sha256')
        record=dict(preparation=file_pin(p),stream=name,pin=dict(path=index.get(h,stream.get('receipt',{}).get('path')),sha256=h),reader='r1_handover.prepared_stream_identity')
        try:
            if h not in index:raise ValueError('MISSING_STREAM_RECEIPT:'+str(h))
            with scope(index):record['identity'],record['source_count']=H.prepared_stream_identity(load(index[h]),stream,name)
            record['status']='PASS'
        except (ValueError,OSError,KeyError) as error:record.update(status='REFUSE',error=str(error))
        result['prepared'].append(record)
# The rows child is independently authenticated even if the prepared order is absent.
result['children']=[]
for entry in list(result['receipts']):
    r=load(entry['pin']['path'])
    if r.get('schema')!='c1-pose-mix-v1':continue
    for source in r['sources']:
        if source['kind']!='rows':continue
        pin=source['receipt'];record=dict(pin=pin,reader='r1_handover.stream_identity',parent=entry['pin'])
        try:
            with scope(index):
                from student_pilot.p3_provenance import pinned
                child=load(pinned(pin));record.update(identity=H.stream_identity(child,'pose'),count=child['count'],status='PASS')
        except (ValueError,OSError,KeyError) as e:record.update(status='REFUSE',error=str(e))
        result['children'].append(record)
missing={};visited=set()
def refs(value):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):
            h=value['sha256'];path=value['path']
            if h not in index:missing[(h,path)]=dict(sha256=h,path=path)
            elif h not in visited:
                visited.add(h)
                try:refs(load(index[h]))
                except (ValueError,UnicodeDecodeError):pass
        for v in value.values():refs(v)
    elif isinstance(value,list):
        for v in value:refs(v)
for e in result['receipts']:refs(e['pin'])
for e in result['prepared']:refs(e['preparation'])
result['missing_dependency_pins']=list(missing.values())
result['missing_order_pins']=[v for v in missing.values() if 'order' in v['path']]
(O/'INDEX.json').write_text(json.dumps(index,indent=2))
(O/'RESULT.json').write_text(json.dumps(result,indent=2));m.save(O)
print(json.dumps({k:result[k] for k in ('scanned','absent','prepared')},indent=2))
print('available stream receipts',len(result['receipts']))
