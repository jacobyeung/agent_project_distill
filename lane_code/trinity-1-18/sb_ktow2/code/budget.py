"""Admission via the orchestrator's one shared ledger, with a reserved hard stop."""
from common import *

ORDER=['tower_A','tower_B','route_K1','route_R0dev','route_tracker','route_94','tower_C','devS1','devS1_tracker']
HOURS=[.75,3.,1.75,3.5,3.25,3.,.75,2.,1.]

def admit(part,cfg):
 p=ROOT/'inbox/SHARED_GPU_RESERVATION.json';grant=read_json(p)
 ledger_path=local(grant['ledger_path']);ledger=read_json(ledger_path)
 if sha(ledger_path)!=grant['ledger_sha256']:raise ValueError('Shared ledger changed after reservation')
 reservation=next(r for r in ledger['reservations'] if r['id']==grant['reservation_id'])
 assert reservation['part']=='tower_'+part and reservation['workspace']==str(ROOT)
 assert reservation['code_sha256']==digest(code_pins())
 assert reservation['hard_seconds']==cfg['hard_seconds'][part]
 assert str(reservation['card'])==os.environ['CUDA_VISIBLE_DEVICES']
 used=sum(float(r['gpu_seconds']) for r in ledger['completed'])
 active=sum(float(r['hard_seconds'])*int(r.get('cards',1)) for r in ledger['reservations'])
 assert used+active<=16*3600 and sum(int(r.get('cards',1)) for r in ledger['reservations'])<=2
 assert reservation.get('status')=='RESERVED'
 assert ledger['next_authorized_part']=='tower_'+part
 assert ledger['order']==ORDER
 assert grant['reservation_id'].replace('_','').replace('-','').isalnum()
 from policy import consume_once
 consume_once(ROOT/'out/tower_frames/ledger'/f"{grant['reservation_id']}.json",dict(part=part,card=reservation['card'],start_unix=time.time(),hard_seconds=reservation['hard_seconds'],ledger_sha256=grant['ledger_sha256']))
 return grant
