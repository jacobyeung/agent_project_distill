from pathlib import Path
import json,statistics,collections
W=Path.cwd();O=W/'out';groups=collections.defaultdict(list);active=collections.Counter()
for p in (W/'in/h10own').glob('*/items.jsonl'):
 for line in p.open():
  r=json.loads(line)
  if r['mode']!='none':continue
  groups[r['type']].append(r['seconds'])
  active[r['type']]+=any(c['family'] in ('move','turn','pose','depth_at','other','ground','gap') for c in r['output']['calls']['records'])
proof=Path('/scratch/jjyeung/orch_n30/reader_r1/work/b1/work/b04full/out/proofs/PARITY_own_depth_p0_51rows.jsonl');g=collections.defaultdict(list)
for line in proof.open():
 r=json.loads(line)
 if 'g3t_s' in r.get('timings',{}):g[r['question_type']].append(r['timings']['g3t_s'])
means={k:statistics.mean(v) for k,v in g.items()};distance='object_abs_distance';rows=[]
for k,v in groups.items():
 n=len(v)*(2 if k==distance else 1);extra=means.get(k,means[distance])
 rows.append(dict(type=k,observed_reads=len(v),planned_reads=n,own_mean_seconds=statistics.mean(v),own_total_seconds=n*statistics.mean(v),
    observed_g3t_activating_reads=active[k],g3t_seconds_per_read=extra,g3t_source='measured same type' if k in means else 'estimate from distance proxy',
    estimated_seconds=n*(statistics.mean(v)+extra)))
base=sum(r['own_total_seconds'] for r in rows);full=sum(r['estimated_seconds'] for r in rows)
result=dict(types=rows,g3t_samples={k:dict(n=len(v),mean=means[k]) for k,v in g.items()},own_only_hours=base/3600,
 estimated_read_hours=full/3600,estimated_full_hours_with_overhead=(full+1800)/3600,
 overhead_assumption_seconds=1800,overhead_note='Unmeasured staging, CPU restore, and six worker model loads; allow at least 30 minutes. No overlap or warm-cache discount.',
 allocated_gpu_hours=5,stop_margin_seconds=1800,return_margin_seconds=1200,
 distance_both_hours=300*(statistics.mean(groups[distance])+means[distance])/3600,
 usd_per_h100_hour=None,price='5 * the approved USD/H100-hour rate; no rate exists in the supplied sources and network access is forbidden.',
 full_coverage_expected=False,estimate_note='Add G3T once per read conservatively; room calls may not activate it. Camera G3T is a distance timing proxy, not a measurement. Changed call trajectories can change decode time.')
(O/'TIME_PRICE.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
inputs=json.loads((O/'inputs_tower.json').read_text())
missing=dict(real_cpu_first_item_per_type=False,reason='Only code, metadata, CPU fixtures and cached replay geometry are supplied. The authenticated production archives and restored runtime are not staged under W2.',
 required_archives=[dict(sha256=a['sha256'],parts=a['parts'],expanded_bytes=a['expanded_bytes']) for a in inputs['archives']],
 required_runtime_python=inputs['python'],required_frames_root=inputs['frames_root'],required_files=inputs['files'])
(O/'MISSING_RUNTIME.json').write_text(json.dumps(missing,indent=2)+'\n')
