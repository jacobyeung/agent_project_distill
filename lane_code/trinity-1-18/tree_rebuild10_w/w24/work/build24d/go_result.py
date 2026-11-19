from pathlib import Path
import datetime,json,math,re,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
sys.path.insert(0,str(L/'work/build24'));import joblib as J
ranks={}
for rank in range(4):
 p=D/'go'/('rank'+str(rank)+'.json')
 if not p.is_file():continue
 v=J.load(p);events=v.get('events',[])
 losses=[e['info']['stream_means'] for e in events]
 ranks[str(rank)]=dict(fresh_optimizer=v['optimizer_state_entries_at_start']==0,start=v['start_step'],end=v.get('last_step'),steps=[e['step'] for e in events],finite_loss=bool(losses) and all(math.isfinite(x) for row in losses for x in row.values()),losses=losses)
training=J.load(D/'GO_TRAIN.json') if (D/'GO_TRAIN.json').exists() else []
passed=len(ranks)==4 and all(v['fresh_optimizer'] and v['start']==0 and v['end']==2 and v['steps']==[1,2] and v['finite_loss'] for v in ranks.values())
failed=next((x for x in training if x['returncode']),None)
reason='Four gloo workers completed two native optimizer steps.' if passed else ('Refusal at '+failed['stage'] if failed else 'The GO canary or native training had not completed at the packaging cutoff.')
if failed:
 text=Path(failed['log']).read_text()
 errors=[line for line in text.splitlines() if re.search(r'(?:ValueError|RuntimeError|PermissionError|OSError|KeyError|FileNotFoundError):',line)]
 if errors:reason+=': '+errors[-1][:350]
socket_blocked=(D/'go/stage3.log').exists() and 'Operation not permitted' in (D/'go/stage3.log').read_text()
if socket_blocked:reason='t.py invoked one torch.distributed.run; sandbox denied localhost TCP sockets (EPERM) before workers started. No optimizer steps ran.'
phase=D/'go/p2/q/p'
progress=dict(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),prepare_complete=(phase/'phase_prepare.complete.json').exists(),frame_audit_complete=(phase/'phase_frames.complete.json').exists(),canary_result_present=(D/'GO_CANARY_FINAL.json').exists(),training_stages=training)
J.write(D/'GO_PROGRESS.json',progress)
result=dict(status='PASS' if passed else 'BLOCKED' if socket_blocked else 'INCOMPLETE',reason=reason,ranks=ranks,progress=progress,torchrun_completed=bool(training and training[-1]['stage']=='t.py / u.py / native train' and training[-1]['returncode']==0),first_scheduled_export=100,gate_step=400,fixture_export_step=2 if (D/'go/train/m2').is_dir() else None)
result.update(requested_world_size=4,torchrun_attempts=1 if (D/'go/stage3.log').exists() else 0,observed_optimizer_steps=2 if passed else 0 if socket_blocked else None)
if passed:assert result['torchrun_completed'] and result['fixture_export_step']==2
J.write(D/'GO_RESULT.json',result);print(json.dumps(result,indent=2))
