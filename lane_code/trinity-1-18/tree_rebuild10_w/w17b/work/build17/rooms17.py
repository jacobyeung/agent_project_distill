from pathlib import Path
import sys,json,hashlib
L=Path(__file__).resolve().parents[2];B=L/'work/build17';I=B/'inputs';I.mkdir(exist_ok=True)
sys.path.insert(0,str(L/'work/tree_r1'))
from student_pilot.p3_provenance import file_pin,load
from student_pilot.r1_rooms import AUTHORITY,census,verify_audit
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');return file_pin(p)
def local(v):
    if isinstance(v,dict):return {k:local(x) for k,x in v.items()}
    if isinstance(v,list):return [local(x) for x in v]
    if isinstance(v,str) and v.startswith(str(L.parent/'w16b')):
        return str(L)+v[len(str(L.parent/'w16b')):]
    return v
cfg=local(load(L/'work/build16/inputs/config.json'))
sources=local(load(L/'work/build16/inputs/row_sources.json'))
cfg['r1_training']['row_sources']=save(I/'row_sources.json',sources)
for key,name in [('mix','mix.json'),('source_membership','source_membership.json')]:
    cfg['r1_training'][key]=save(I/name,local(load(L/'work/build16/inputs'/name)))
cfg['streams']['vqa']=save(I/'v7_receipt.json',local(load(L/'work/build16/inputs/v7_receipt.json')))
cfg['r1_training']['store_parameter']=cfg['streams']['vqa']
paths={'split':'ext/b12/work/auth/K1SPLIT_R0.json','visits':'ext/b12/work/auth/arkit_3dod_metadata.csv',
       'aliases':'ext/b12/work/d3_token_map.json','reserve':'inputs/rooms/R0_ROOMS.txt','build':'inputs/rooms/EXCLUSIONS.json'}
pins={}
for key,name in paths.items():
    raw=(L.parent/name).read_bytes();assert hashlib.sha256(raw).hexdigest()==AUTHORITY[key]
    p=I/(AUTHORITY[key]+'.json');p.write_bytes(raw);pins[key]=file_pin(p)
cfg['r1_training']['room_authority']=pins
if (I/'room_audit.json').exists():
    audit=load(I/'room_audit.json')
    hits=[json.loads(line) for line in (I/'s.json').read_text().splitlines()]
else:
    audit,hits=census(cfg)
raw=''.join(json.dumps(row,sort_keys=True,separators=(',',':'))+'\n' for row in hits).encode()
prior=(L/'work/build16/inputs/s.json').read_bytes()
assert raw==prior,(len(hits),hashlib.sha256(raw).hexdigest())
(I/'s.json').write_bytes(raw)
cfg['remove_files']=[file_pin(I/'s.json') if p['sha256']==hashlib.sha256(prior).hexdigest() else p for p in cfg['remove_files']]
audit['remove_files']=cfg['remove_files']
audit['authority']=pins
audit['row_sources']=cfg['r1_training']['row_sources']
pin=save(I/'room_audit.json',audit)
cfg['r1_training']['room_audit']=pin
verify_audit(cfg,pin)
save(I/'config.json',cfg);save(I/'kit_config.json',cfg)
save(B/'proofs/rooms/RESULT.json',dict(audit=audit,same_bytes=True,removal_rows=len(hits),removal=file_pin(I/'s.json')))
(B/'STATUS.md').write_text('# Build 17 status\n\nStep 1 complete. The full pinned room rule certifies the slices; the regenerated list equals build 16 byte for byte. Store unresolved rows remain explicitly outside fresh overlap certification. GO=false.\n')
print(json.dumps({k:{x:y for x,y in v.items() if x!='source'} for k,v in audit['slices'].items()},indent=2))
print(json.dumps({k:v for k,v in audit['store'].items() if k not in ('unresolved_examples','database')},indent=2))
