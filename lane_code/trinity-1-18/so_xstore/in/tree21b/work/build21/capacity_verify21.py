from pathlib import Path
import json, math
B=Path(__file__).resolve().parent;O=B/'proofs/capacity'
summary=json.loads((O/'RESULT.json').read_text())
assert summary['complete_native_fixture'] and summary['status']=='ADMIT'
expected={'wrong_h_pin','non_R1','non_N','missing_model_manifest','without_z','k1_slice','altered_shard'}
verified={}
for step in ('400','600'):
    result=summary['milestones'][step]
    assert result['status']=='ADMIT'
    assert result['absolute_resume_step']==int(step)
    assert result['forward']['absolute_step']==int(step)
    assert {'r1_loader.production_audit','persisted_handover','all_rank_full_forward'} <= set(result['steps'])
    forward=json.loads((O/step/'q/f.json').read_text())
    records=forward['records']
    assert {r['rank'] for r in records}=={0,1,2,3}
    for rank in range(4):
        assert {r['stream'] for r in records if r['rank']==rank}=={'pose','vqa','routing','pointing'}
    assert all(r['finite'] and math.isfinite(r['loss']) for r in records)
    twins=summary['twins'][step]
    assert set(twins)==expected|({'export_in_training_config'} if step=='400' else {'export_at_stop'})
    assert all(r['status']=='REFUSE' and r.get('refusal') for r in twins.values())
    verified[step]=dict(first_losses={str(rank):next(r['loss'] for r in records if r['rank']==rank) for rank in range(4)},
                        records=len(records),twins=len(twins),source=str(O/step/'q/f.json'))
(O/'VERIFIED.json').write_text(json.dumps(verified,indent=2)+'\n')
print(json.dumps(verified,indent=2))
