"""Resolve pinned train identities against all five physical-room exclusion lists."""
from functools import lru_cache
from common import *
import store_room_audit as audit

@lru_cache(maxsize=1)
def authority():
 ledger=audit.Inputs()
 base=ROOT/'inputs/exclusions'
 result=audit.prepare(base/'tree_r1',base/'lists',ledger)
 INPUTS.update({p:v['sha256'] for p,v in ledger.pins.items()})
 sha(ROOT/'code/vendor/store_room_audit.py')
 return result

def check_row(row):
 rooms,mint,sets,checks,aliases,quarantine=authority()
 _,canonical,room,_,error=audit.resolve(row,rooms,mint,aliases,quarantine)
 if error:raise ValueError('Unresolved exclusion identity: '+error)
 return dict(canonical=canonical,room=room,hits=[n for n,s in sets.items() if room in s])

@lru_cache(maxsize=1)
def population():
 from policy import captures,row_ids
 train=row_ids('train');excluded=[];allowed=set();row_rooms={};capture_rooms={}
 for c in captures('train'):
  ds,scene=c['canonical'].split('/',1)
  resolved=check_row(dict(dataset=ds,scene=scene,canonical=c['canonical']))
  if resolved['room']!=c['room']:raise ValueError('Capture/authority room mismatch: '+c['canonical'])
  ids={r['id'] for r in c['rows']} & train
  capture_rooms[c['canonical']]=c['room']
  for i in ids:
   if i in row_rooms:raise ValueError('Duplicate train row: '+i)
   row_rooms[i]=c['room']
  if resolved['hits']:
   excluded.append(dict(capture=c['canonical'],room=c['room'],hits=resolved['hits'],row_ids=sorted(ids)))
   if set(resolved['hits'])!={'withheld-80'}:raise ValueError('Unexpected train exclusion: '+str(excluded[-1]))
  else:allowed.update(ids)
 assert set(row_rooms)==train and len(train)==1037 and len(allowed)==1012
 return dict(status='PASS',full_rows=len(train),decision_rows=len(allowed),allowed_row_ids=sorted(allowed),excluded=excluded,row_rooms=row_rooms,capture_rooms=capture_rooms,list_checks=authority()[3])

def decision_rows(rows):
 p=population();allowed=set(p['allowed_row_ids']);blocked={r['capture'] for r in p['excluded']};out=[]
 for r in rows:
  if r.get('split')!='train':raise ValueError('Decisions accept K1 train only')
  if 'row_id' in r:
   i=r['row_id']
   if i not in p['row_rooms']:raise ValueError('Unpinned decision row: '+i)
   if r['room']!=p['row_rooms'][i]:raise ValueError('Decision row/room mismatch: '+i)
   keep=i in allowed
  else:
   c=r['capture']
   if c not in p['capture_rooms'] or r['room']!=p['capture_rooms'][c]:raise ValueError('Unpinned decision capture: '+c)
   keep=c not in blocked
  if keep:out.append(r)
 return out

if __name__=='__main__':
 code_pins();p=population();planted={}
 for name,rooms in authority()[2].items():
  room=next(r for r in sorted(rooms) if r.startswith('scannet/'))
  r=check_row(dict(dataset='scannet',scene=room.split('/')[1]+'_99'))
  assert name in r['hits'];planted[name]=r
 write_json(ROOT/'out/EXCLUSIONS.json',dict(p,planted_rows=planted,command='bash scripts/cpu.sh code/exclusions.py'))
 print(json.dumps(dict(status=p['status'],decision_rows=p['decision_rows'],full_rows=p['full_rows'],excluded=p['excluded'],planted_rows=planted)))
