"""Estimate the one-GPU wall time of the tower-and-own camera read from measured returns."""
import json
from pathlib import Path

O3=Path('/scratch/jjyeung/orch_n30/sb_callrate/in/cont_ops/work/r1route/out3')
A4=O3/'A4/ret';B1=O3/'bases/b1/work/ret';H10=Path('/scratch/jjyeung/orch_n30/sb_ownread/work/h10own_170631')
CAMERA=(0,1,2);ALLOCATED=5*3600;STOP=1800

def rows(p):return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]

def main():
 end=json.loads((A4/'metadata/ALLOCATION.json').read_text())['end']
 steps=rows(A4/'metadata/reads/0/STEPS.jsonl');first=min(s['utc'] for s in steps if s['event']=='start')
 staging=first-(end-ALLOCATED)
 tower200=sum(r['seconds'] for t in CAMERA for r in rows(A4/f'metadata/reads/0/metadata/journals/{t}/0/items.jsonl'))
 tower544=sum(r['seconds'] for t in CAMERA for r in rows(B1/f'metadata/reads/0/metadata/journals/{t}/0/items.jsonl'))
 tower_load=max(l['load_s'] for x in rows(A4/'metadata/reads/0/metadata/journals/3/0/timings.jsonl') for l in x['loads'])
 own=0;own_load=0;overhead=[]
 h=rows(H10/'STEPS.jsonl')
 for t in CAMERA:
  rs=rows(H10/f'metadata/journals/{t}/0/items.jsonl');tim=rows(H10/f'metadata/journals/{t}/0/timings.jsonl')
  own+=sum(r['seconds'] for r in rs if r['mode']=='none')
  own_load=max(own_load,max(l['load_s'] for x in tim for l in x['loads']))
  start=next(s['utc'] for s in h if s['event']=='start' and s['type']==t);stop=next(s['utc'] for s in h if s['event']=='exit' and s['type']==t)
  overhead.append(stop-start-sum(r['seconds'] for r in rs))
 per_process=max(overhead)
 decode=max(tower200,tower544)+own
 estimate=staging+len(CAMERA)*(per_process+tower_load)+decode+120
 upper=staging+len(CAMERA)*(per_process+tower_load)+1.5*decode+120
 value=dict(gpus=1,walltime='05:00:00',allocated_seconds=ALLOCATED,admission_stops_at_seconds=ALLOCATED-STOP,
  measured=dict(staging_seconds=round(staging),tower_decode_seconds_step200=round(tower200),tower_decode_seconds_step544=round(tower544),
   own_decode_seconds_step544=round(own),tower_load_seconds=round(tower_load),own_load_seconds=round(own_load),
   own_process_overhead_seconds_incl_load=[round(x) for x in overhead]),
  model='staging + 3 type processes x (own process overhead incl. own load + tower load) + tower decode + own decode + 120 s return',
  estimated_seconds=round(estimate),estimated_hours=round(estimate/3600,2),upper_seconds_decode_x1_5=round(upper),upper_hours=round(upper/3600,2),
  headroom_to_admission_stop=round((ALLOCATED-STOP)/upper,2),
  sources=dict(tower200='job 172744 (A4)',tower544='job 171253 read 0',own544='job 170631 mode none'))
 print(json.dumps(value,indent=1));return value

if __name__=='__main__':main()
