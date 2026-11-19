from pathlib import Path
import json,math,sys
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
result=dict(status='PASS' if passed else 'INCOMPLETE',reason=reason,ranks=ranks,torchrun_completed=bool(training and training[-1]['stage']=='t.py / u.py / native train' and training[-1]['returncode']==0),first_scheduled_export=100,gate_step=400,fixture_export_step=2 if (D/'go/train/m2').is_dir() else None)
if passed:assert result['torchrun_completed'] and result['fixture_export_step']==2
J.write(D/'GO_RESULT.json',result);print(json.dumps(result,indent=2))
