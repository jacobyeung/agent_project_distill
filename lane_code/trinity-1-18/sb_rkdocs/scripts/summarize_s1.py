from adapter import *
import kernel
ins=kernel.input_code();results=[]
for source in [W/'out/S0.json',W/'review/CPU_INPUT_SHA256.txt',W/'review/REVIEW_VERDICT.md']:
 ins[str(source)]=sha(source)
for cap,target in [('scannetpp/067e2e4e61',14.73),('scannetpp/036bce3393',39.35)]:
 areas_by={};frozen_by={}
 for mode in ['k1_64','k1_32']:
  p=W/'out/s1'/mode/cap.replace('/','__')/'pred.npz';d=p.parent/'DONE.json'
  if not d.is_file():raise FileNotFoundError('MISSING '+str(d))
  assert read(d)['pred_sha256']==sha(p);ins[str(p)]=sha(p);ins[str(d)]=sha(d)
  r=pipeline(p,W/'out/s1_geom'/mode/(cap.replace('/','__')+'.npz'));areas_by[mode]=r['area_m2']
  frozen_by[mode]=kernel.pipeline(p,W/'out/s1_geom/frozen'/mode/(cap.replace('/','__')+'.npz'))['area_m2']
 error=abs(areas_by['k1_64']/target-1);ratio=areas_by['k1_32']/areas_by['k1_64']
 results.append(dict(capture=cap,stored_gpu_m2=target,frozen_kernel_m2=frozen_by,**areas_by,relative_error=error,within_5pct=error<=.05,ratio32_to64=ratio))
qpath=W/'configs/R0_QUESTIONS_rl_f32.jsonl';ins[str(qpath)]=sha(qpath)
qs=sorted([q for q in map(json.loads,qpath.read_text().splitlines()) if q['question_type']=='room_size_estimation'],key=lambda q:q['scene'])[:2];rl=[]
for q in qs:
 p=W/'out/s1/r0_rl32'/q['scene']/'pred.npz';d=p.parent/'DONE.json';assert read(d)['pred_sha256']==sha(p);ins[str(p)]=sha(p);ins[str(d)]=sha(d)
 for rule in ['R0','T10']:
  r=pipeline(p,W/'out/s1_geom/r0_rl32'/(q['scene']+'.npz'),rule);rl.append(dict(id=q['qid'],scene=q['scene'],arm='da3_f32+'+rule,gt_m2=q['gt']['area_m2'],**r,input_sha256=dict(ins)))
(W/'out/S1_ROOM_PRED.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rl))
passed=all(r['within_5pct'] for r in results)
write(W/'out/DRYRUN.json',dict(verdict='PASS' if passed else 'FAIL',k1=results,rl=rl,both_ratios_outside_15pct=all(not .85<=r['ratio32_to64']<=1.15 for r in results)),ins)
status('S1 '+('PASS' if passed else 'FAIL')+': full CPU tower pass and local pricing receipts are in out/DRYRUN.json. GPU pricing remains unrun and requires external provenance and a bound GO note.')
print(json.dumps(results,indent=2))
if not passed:raise SystemExit(1)
