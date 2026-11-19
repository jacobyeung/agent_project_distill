"""Price all available object-route CPU arms from pinned training measurements."""
from common import *
from collections import defaultdict
from itertools import combinations
from ruling0749 import contrast,doubt,interval,score
from box_hook import load

def objects(rows):
 result={}
 for r in rows:
  for name,d in r['diagnostics'].items():
   key=d['object_id'];value=dict(d,capture=r['capture'],room=r['room'],name=name)
   if key in result:
    old=result[key]
    assert old['gt_longest']==value['gt_longest'] and old['first_gt']==value['first_gt']
    if old['printed_longest'] is not None and value['printed_longest'] is not None:assert old['printed_longest']==value['printed_longest']
    if old['printed_longest'] is not None:continue
   result[key]=value
 return result

def sizes(rows):
 return [dict(row_id=k,capture=o['capture'],room=o['room'],prediction=o['printed_longest'],label=o['gt_longest']) for k,o in sorted(objects(rows).items())]

def first_seen(rows):
 grouped=defaultdict(list)
 for o in objects(rows).values():grouped[o['capture']].append(o)
 pairs=[]
 for cap,obs in grouped.items():
  for a,b in combinations(sorted(obs,key=lambda x:x['instance']),2):
   if a['first_gt'] is None or b['first_gt'] is None or a['first_gt']==b['first_gt']:continue
   correct=a['first_printed'] is not None and b['first_printed'] is not None and (a['first_printed']-b['first_printed'])*(a['first_gt']-b['first_gt'])>0
   pairs.append(dict(capture=cap,room=a['room'],instances=[a['instance'],b['instance']],correct=correct))
 return dict(pairs=len(pairs),correct=sum(r['correct'] for r in pairs),rate=interval([float(r['correct']) for r in pairs],[r['room'] for r in pairs]))

def size_screen(serving,s4,construction,rebuilt):
 a,b=sizes(s4),sizes(serving)
 keys=lambda rs:sorted((r['row_id'],r['label'],r['room']) for r in rs)
 assert keys(a)==keys(b)
 identity=digest(keys(a));treatment=contrast(a,b,{c:True for c in rebuilt})
 return dict(status='COMPLETE',selection_split='K1-train',construction=construction,object_set_sha256=identity,geometries={g:dict(objects=len(rs),score=100*sum(score(r['prediction'],r['label']) for r in rs)/len(rs),refusals=sum(r['prediction'] is None for r in rs),object_set_sha256=identity,refusals_score_zero=True) for g,rs in [('serving',b),('g3t_s4',a)]},treatment=treatment)

def main():
 import torch
 torch.set_num_threads(8)
 assert os.environ.get('CUDA_VISIBLE_DEVICES')=='' and os.getpriority(os.PRIO_PROCESS,0)>=10
 pins()
 for p in (ROOT/'inputs/ruling0749').glob('*.md'):sha(p)
 snapshot=js(ROOT/'inputs/KBOX_SNAPSHOT.json');hook,gate=load();replay=hook.stage1_replay()
 frozen=js(ROOT/'inputs/kbox4/FREEZE.json')
 wanted=set(read(ROOT/'inputs/rowsets/K1_TRAIN_1037.txt').decode().splitlines());tableids=set(read(ROOT/'inputs/rowsets/K1_TRAIN_TABLES_883.txt').decode().splitlines())
 arms=defaultdict(list);counts={};rebuilt={c:e['rebuilt_table'] for c,e in snapshot['captures'].items()}
 for cap in sorted(snapshot['captures']):
  data=hook.capture(cap)
  names=sorted({r['arm'] for r in data['items'] if r['arm']=='A0_deployed' or r['arm']=='A9_s4_today' or r['arm'].startswith('A4_obj_')})
  for name in names:
   rr=hook.object_source(cap,name);arms[name]+=rr
   if name.startswith('A4_obj_') or name=='A0_deployed':counts.setdefault(name,{})[cap]=hook.count_objects(cap,name)
 for name,rr in arms.items():assert len(rr)==len(wanted) and {r['row_id'] for r in rr}==wanted
 baseline=arms['A0_deployed'];comparisons=[];doubts={};diagnostics={}
 for name,rr in sorted(arms.items()):
  if name=='A0_deployed':continue
  for subset,ids in [('K1_TRAIN_1037',wanted),('K1_TRAIN_TABLES_883',tableids)]:
   for ds in ['all','arkitscenes','scannet','scannetpp']:
    keep=lambda r:r['row_id'] in ids and (ds=='all' or r['dataset']==ds)
    a,b=[r for r in rr if keep(r)],[r for r in baseline if keep(r)]
    comparisons.append(dict(arm=name,rowset=subset,dataset=ds,**contrast(a,b,rebuilt)))
  if name.startswith('A4_obj_'):
   doubts[name]=doubt(rr,baseline,rebuilt)
   obs=objects(rr);added=sum(o['added'] for o in obs.values());correct=sum(o['correct'] for o in obs.values())
   diagnostics[name]=dict(first_seen=first_seen(rr),objects=len(obs),added_members=added,correct_added_members=correct,merge_precision=correct/added if added else None,counts=counts[name])
 diagnostics['A0_deployed']=dict(first_seen=first_seen(baseline),objects=len(objects(baseline)),counts=counts['A0_deployed'])
 missing_count=sum(not rebuilt[r['capture']] for r in baseline)
 write(ROOT/'out/K1_TRAIN_RESULTS.json',dict(status='COMPLETE_AVAILABLE_CPU',selection_split='K1-train',comparisons=comparisons,retained_A0_rows=missing_count,missing_rebuilt_captures=[c for c,v in rebuilt.items() if not v],A0_geometry='R1 serving own-depth scale and own gravity',scorer='Accepted spec section 6: float64 <= thresholds from numpy.linspace(.5,.95,10)',statistics='10,000 paired physical-room draws; seed 20261119; item weighted; zero-scored executed refusals except missing-rebuilt rows retain A0 in both arms'))
 write(ROOT/'out/K1_TRAIN_DIAGNOSTICS.json',dict(status='COMPLETE',selection_split='K1-train',arms=diagnostics,role='Training diagnostics; no arm chosen here'))
 write(ROOT/'out/DOUBT_REMEASURE.json',dict(status='COMPLETE_DIAGNOSTICS_PRIMARY_MISSING',selection_split='K1-train',detector='rarer object grounded in fewer than 3 frames',detector_source='LABELLING_PILOT_20261119.md section 7(b)',detector_uses_truth=False,three_field_detector=dict(status='MISSING',reason='Pilot record gives no fitted coefficients or firing threshold'),size_detector=dict(status='MISSING',reason='The named record provides no size-specific detector or threshold'),variants=doubts,selected_arm=None,selected_arm_status='MISSING: no eligible frozen merged-object variant',tracking_status='GPU_NEEDED',rows_built=0))
 diagnostic=size_screen(baseline,arms['A9_s4_today'],'today_diagnostic',rebuilt)
 write(ROOT/'out/SIZE_TODAY_DIAGNOSTIC.json',dict(diagnostic,role='Diagnostic only; cannot authorize a selected P0/P1/P2 size look'))
 write(ROOT/'out/SELECTED_SIZE_SCREEN.json',dict(status='MISSING',selection_split='K1-train',construction=None,geometries={},reason='FREEZE.json has no eligible object variant; P1 evidence and P2 tracks are unavailable',expected_inputs=[str(ROOT/'inputs/TOWER_DECISION.json'),str(ROOT/'out/object_route/K1_TRACK.json')],r0_size_read_allowed=False))
 write(ROOT/'out/CONSTRUCTION_SELECTION.json',dict(status='MISSING',selection_split='K1-train',P0=dict(status='REFUSED',reason='No eligible frozen object variant',replace_box_part1=frozen['replace_box_part1']),P1=dict(status='MISSING',expected_path=str(ROOT/'inputs/TOWER_DECISION.json')),P2=dict(status='GPU_NEEDED',expected_path=str(ROOT/'out/object_route/K1_TRACK.json')),selected=None,sequence='P0; P1 only on paired lower bound > 0; P2 only versus the arm held so far on paired lower bound > 0',read_spent=False))
 census=js(ROOT/'out/TRAIN_CENSUS.json')['counts']['all']
 write(ROOT/'out/GPU_NEED.json',dict(status='NEEDED_NOT_RUN',selection_split='K1-train',cards=1,memory_gib=48,estimated_gpu_hours=1.3,hard_stop_hours=1.75,hard_stop_seconds=6300,GPU_hours_used=0,remaining_captures=census['captures'],remaining_capture_name_jobs=census['capture_name_jobs'],remaining_rows=len(wanted),command='bash scripts/gpu_k1_track.sh',scope='K1 training 32-anchor tracker and tracking re-measure arm only',requirements=['Separate GPU authorization and pinned exclusive ledger under /scratch','CUDA SAM3 runtime and checkpoint','Native sb_kbox4 price_k1_tracks export and selected construction geometry'],estimate_basis='Accepted spec sections 3b and 3e; no measured CUDA timing',CPU_tracking='Not attempted: staged predictor requires CUDA',vnice='/data3/shared/scripts/vnice/vnice.sh'))
 rows=['# K1 training CPU results','', 'All results use registered training rows. No R0-dev or K1 held-out outcomes were read.', '',f'Missing rebuilt-table fallback: {missing_count} rows keep A0 in both arms. The legacy table subset has {len(tableids)} rows; all-row pricing has {len(wanted)}.', '', 'A0 uses the serving geometry. Scores use the accepted object-route scorer. Intervals resample physical rooms 10,000 times, seed 20261119.', '', '| Arm | Rows | A0 MRA | Arm MRA | Difference [95% CI] | Refusals |','|---|---:|---:|---:|---|---:|']
 for r in comparisons:
  if r['dataset']=='all':rows.append(f"| {r['arm']} ({r['rowset']}) | {r['n']} | {r['A0_score']:.3f} | {r['arm_score']:.3f} | {r['estimate']:+.3f} [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}] | {r['refusals']} |")
 rows+=['','Dataset-specific paired contrasts appear in K1_TRAIN_RESULTS.json. Every merged variant below is diagnostic; FREEZE selects none.','', '| Re-measure arm | Triggered | Both numeric | Closer / worse / tied | Closer % [95% CI] | Switch MRA gain [95% CI] |','|---|---:|---:|---|---|---|']
 for arm,d in doubts.items():
  c=d['closer_rate'];g=d['repair_gain'];rows.append(f"| {arm} | {d['triggered']} | {d['paired_numeric']} | {d['closer']} / {d['worse']} / {d['ties']} | {100*c['estimate']:.2f} [{100*c['ci95'][0]:.2f}, {100*c['ci95'][1]:.2f}] | {g['estimate']:+.3f} [{g['ci95'][0]:+.3f}, {g['ci95'][1]:+.3f}] |")
 rows+=['','Trigger: min grounded operand frames < 3. Rows with no numeric first value are counted but cannot establish whether a second value is closer. A refused second call retains the first value. DOUBT_REMEASURE.json supplies paired row evidence and closer-minus-worse intervals.','', 'The fitted three-field distance detector and a size-specific trigger are MISSING from the named pilot record. Tracking requires CUDA. No training rows were built.','', '| Source | Correct first-seen pairs | Pair rate |','|---|---:|---:|']
 for arm,d in diagnostics.items():
  f=d['first_seen'];rows.append(f"| {arm} | {f['correct']}/{f['pairs']} | {f['rate']['estimate']:.4f} |")
 rows+=['','Object counts and merge precision by capture/name are in K1_TRAIN_DIAGNOSTICS.json. Counts are diagnostics, not a route decision.','',f"Today-only size geometry diagnostic: serving {diagnostic['geometries']['serving']['score']:.3f}; S4 {diagnostic['geometries']['g3t_s4']['score']:.3f}; paired change {diagnostic['treatment']['estimate']:+.3f} [{diagnostic['treatment']['ci95'][0]:+.3f}, {diagnostic['treatment']['ci95'][1]:+.3f}] on {diagnostic['geometries']['serving']['objects']} deduplicated objects. This does not satisfy the selected-construction gate.",'','P0 has no eligible frozen variant; P1 evidence is MISSING; P2 needs GPU. Selected size screening is MISSING and the size look is refused. Package-D is MISSING and the absolute-distance comparison is refused.','','Commands: `bash scripts/train_cpu.sh code/bind0749.py`; `bash scripts/train_cpu.sh code/train0749.py`. Predictions come from the SHA-bound sb_kbox4 base exports; this command re-scores them on CPU.']
 (ROOT/'out/K1_TRAIN_TABLES.md').write_text('\n'.join(rows)+'\n')
 status('Stage 3: CPU scoring and paired room-bootstrap pricing are complete for all 33 available merged variants and the S4-today diagnostic on both fixed rowsets. Triggered re-measurement, counts, first-seen rates and size geometry diagnostics are written. The selected construction, native live exports, package-D returns and CUDA tracker remain unavailable; all evaluation reads remain unspent.')
 print(json.dumps(dict(arms=len(arms),comparisons=len(comparisons),doubt_variants=len(doubts),retained_A0_rows=missing_count,selected=frozen['frozen_variant'])))

if __name__=='__main__':main()
