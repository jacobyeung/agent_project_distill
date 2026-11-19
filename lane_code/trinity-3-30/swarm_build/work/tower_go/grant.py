#!/usr/bin/env python3
"""Ledger owner helper (swarm_build3): open or close one reservation in the kit's shared GPU ledger."""
import json, sys, hashlib, time, os
ROOT='/scratch/jjyeung/orch_n30/sb_ktfix2'; INBOX=ROOT+'/inbox'; LEDGER=INBOX+'/SHARED_GPU_LEDGER.json'
ORDER=['tower_A','tower_B','route_K1','route_R0dev','route_tracker','route_94','tower_C','devS1','devS1_tracker']
HARD={'A':2700,'B':10800,'C':2700}; CODE='076c5d87ab581e9b49332f9deaea20991cee2b8d989cd2287d1a6160e2b93e9c'
AUTH='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/swarm_build/20261119T1030Z_ORCH_GO_tower_frames_trinity_0_13_card6_conditional.md'
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def wj(p,d):
    t=p+'.tmp'; json.dump(d,open(t,'w'),indent=1,sort_keys=True); os.replace(t,p)
def load():
    return json.load(open(LEDGER)) if os.path.exists(LEDGER) else dict(owner='swarm_build3',authority=AUTH,order=ORDER,completed=[],reservations=[],next_authorized_part=None)
cmd,part,card=sys.argv[1],sys.argv[2],sys.argv[3]
L=load()
if cmd=='open':
    assert not L['reservations'], 'a reservation is still open'
    used=sum(float(r['gpu_seconds']) for r in L['completed'])
    assert used+HARD[part] <= 6*3600, 'would exceed the 6 GPU-hour stop'
    rid='swb3tower%s%d'%(part,int(time.time()))
    L['reservations']=[dict(id=rid,part='tower_'+part,workspace=ROOT,code_sha256=CODE,hard_seconds=HARD[part],card=str(card),cards=1,status='RESERVED',opened_utc=time.strftime('%FT%TZ',time.gmtime()))]
    L['next_authorized_part']='tower_'+part; wj(LEDGER,L)
    wj(INBOX+'/SHARED_GPU_RESERVATION.json',dict(ledger_path=LEDGER,ledger_sha256=sha(LEDGER),reservation_id=rid))
    print('OPEN',rid)
elif cmd=='close':
    r=L['reservations'][0]; stop=ROOT+'/out/tower_frames/ledger/%s_STOP.json'%r['id']
    g=json.load(open(stop))['gpu_seconds'] if os.path.exists(stop) else float(r['hard_seconds'])
    L['completed'].append(dict(id=r['id'],part=r['part'],gpu_seconds=g,card=r['card'],closed_utc=time.strftime('%FT%TZ',time.gmtime()),stop_receipt=stop if os.path.exists(stop) else 'MISSING (charged hard_seconds)'))
    L['reservations']=[]; L['next_authorized_part']=None; wj(LEDGER,L); print('CLOSED',r['id'],g)
