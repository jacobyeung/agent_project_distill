from pathlib import Path
import collections,json,statistics
W=Path.cwd();O=W/'out';base=W.parent/'b1p';groups=collections.defaultdict(list)
for p in sorted((base/'in/h10own').glob('*/items.jsonl')):
 for line in p.open():
  r=json.loads(line)
  if r['mode']=='none':groups[r['type']].append(r['seconds'])
items=json.loads((O/'src/items/devs1_routed.json').read_text())['items']
order=['object_abs_distance','object_abs_distance','camera_displacement','camera_rotation','camera_movement_direction','room_size_estimation']
first=[i for i in items if i['question_type']==order[0]][:30]
verified_hits=30-len({i['native'] for i in first});g3t=19.8
rows=[]
for j,k in enumerate(order):
 selected=[r for r in items if r['question_type']==k];captures=len({r['native'] for r in selected})
 mean=statistics.mean(groups[k]);extra=verified_hits if j==0 else 0
 rows.append(dict(segment=j,read=1 if j==1 else 0,type=k,items=len(selected),captures=captures,
 own_mean_seconds=mean,own_seconds=mean*len(selected),g3t_fresh_calls=captures+extra,
 g3t_seconds=(captures+extra)*g3t))
own=sum(r['own_seconds'] for r in rows);unique=len({i['native'] for i in items});staging=1800;stop=1800;ret=1200
cases={}
for name,calls in [('off',786),('segment_local',sum(r['g3t_fresh_calls'] for r in rows)),('one_worker_per_read',unique+60+verified_hits)]:
 reads=own+calls*g3t
 cases[name]=dict(g3t_calls=calls,g3t_seconds=calls*g3t,own_seconds=own,read_seconds=reads,read_hours=reads/3600,
 total_hours_with_staging_stop_margin=(reads+staging+stop)/3600,
 total_hours_with_staging_return_margin=(reads+staging+ret)/3600,
 seconds_before_stop_deadline=18000-stop-staging-reads,
 fits_with_stop_and_return_margin=(reads+staging+stop)<=18000)
result=dict(g3t_fresh_seconds=g3t,segments=rows,unique_captures=unique,first_30_captures=len({i['native'] for i in first}),
 first_30_verification_hit_recomputes=verified_hits,case=cases,staging_and_two_loads_assumed_seconds=staging,
 stop_margin_seconds=stop,return_margin_seconds=ret,margins_overlap=True,allocated_hours=5,
 overheads_not_measured=['SAM encoding savings','hashing and defensive copies','GPU trajectory differences','staging and model loading'],
 assumptions='One G3T access per read; one miss per capture per worker plus verified hits. No eviction. Separate reads retain separate memo stores. Own means are timing proxies, not tower decode measurements. SAM savings are not credited because no measured SAM-only split is available.',
 order='Read 0 orders distance, displacement, rotation, movement direction, room; read 1 is distance. Each type preserves manifest order. First 30 distance IDs span 11 captures.',
 price='5 times approved H100 hourly rate, plus separate CPU check; rate not supplied')
(O/'TIME_PRICE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
