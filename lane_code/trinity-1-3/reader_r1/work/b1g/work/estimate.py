from pathlib import Path
import collections,json,statistics,sys
W=Path.cwd();O=W/'out';sys.path.insert(0,str(O));import tower_sequence as T
groups=collections.defaultdict(list)
for p in sorted((W.parent/'b1p/in/h10own').glob('*/items.jsonl')):
 for line in p.open():
  r=json.loads(line)
  if r['mode']=='none':groups[r['type']].append(r['seconds'])
items=json.loads((O/'src/items/devs1_routed.json').read_text())['items']
order=['camera_displacement','camera_rotation','camera_movement_direction','object_abs_distance','room_size_estimation']
seen={0:set(),1:set()};rows=[];timeline=[];elapsed=0;staging=1800;stop=1800;budget=18000-staging-stop
verify=set(T.descriptors(O/'src')[1]['perception_memo_verify_ids'])
for read,t in T.SCHEDULE:
 kind=order[t];selected=[r for r in items if r['question_type']==kind];mean=statistics.mean(groups[kind]);fresh=0;extra=0;start=elapsed
 for item in selected:
  miss=kind!='room_size_estimation' and item['native'] not in seen[read];verification=read==1 and item['id'] in verify and not miss
  seen[read].add(item['native']);fresh+=miss;extra+=verification
  duration=mean+(miss or verification)*19.8
  timeline.append(dict(read=read,type=kind,id=item['id'],start=elapsed,end=elapsed+duration))
  elapsed+=duration
 rows.append(dict(read=read,type=kind,items=len(selected),new_captures=fresh,verified_hits=extra,own_mean_seconds=mean,own_seconds=mean*len(selected),g3t_calls=fresh+extra,seconds=elapsed-start,end_seconds=elapsed))
started=[r for r in timeline if r['start']<budget];finished=[r for r in timeline if r['end']<=budget];cut=next((r for r in timeline if r['end']>budget),None)
own=sum(r['own_seconds'] for r in rows);calls=sum(r['g3t_calls'] for r in rows)
case=dict(g3t_calls=calls,g3t_seconds=calls*19.8,own_seconds=own,read_seconds=elapsed,read_hours=elapsed/3600,total_hours_with_staging_stop_margin=(elapsed+staging+stop)/3600,total_hours_with_staging_return_margin=(elapsed+staging+1200)/3600,seconds_before_stop_deadline=budget-elapsed,fits_with_stop_and_return_margin=elapsed<=budget)
room_start=next(r['start'] for r in timeline if r['type']=='room_size_estimation')
result=dict(g3t_fresh_seconds=19.8,sam_encode_seconds=None,sam_encode_time_status='unmeasured; fresh on every read that requests SAM, with no memo savings credited',perception_memo_modules=['g3t'],segments=rows,case={'one_worker_per_read':case},staging_and_two_loads_assumed_seconds=staging,stop_margin_seconds=stop,return_margin_seconds=1200,margins_overlap=True,allocated_hours=5,read_budget_seconds=budget,
 expected_cut=dict(read=cut['read'],type=cut['type'],id=cut['id'],completed_by_stop=len(finished),started_before_stop=len(started),room_completed_by_stop=sum(r['type']=='room_size_estimation' for r in finished),room_started_before_stop=sum(r['type']=='room_size_estimation' for r in started),drain='The last started item may finish within the separate return margin.',slack_before_room_seconds=budget-room_start),
 assumptions='Own-read means include their fresh SAM work but do not separate encode time. They are proxies for tower decode time; do not add a second SAM cost to these means. G3T assumes an access on each distance/camera item. Room has no served call in leg R1 and adds no G3T encoding cost. No SAM saving is credited. Staging/loading, hashing, copying and rule-dependent decode differences remain unmeasured.',
 cut_uncertainty='Room is the expected cut under the proxy estimate, not a guaranteed cut with unmeasured runtime. Additional pre-room overhead above the reported slack could move the cut earlier. The selector comparison runs first.',
 price='5 times the approved H100 hourly rate, plus the separate CPU check; rate not supplied')
(O/'TIME_PRICE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
