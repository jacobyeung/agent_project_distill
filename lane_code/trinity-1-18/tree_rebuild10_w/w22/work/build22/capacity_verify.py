from pathlib import Path
import json, math
B=Path(__file__).resolve().parent;O=B/'proofs/capacity'
summary=json.loads((O/'RESULT.json').read_text())
assert summary.get('requested_milestones')==[int(s) for s in sorted(summary['milestones'],reverse=True)]
current=json.loads((B.parents[1]/'out/TREE_SEAL.json').read_text())['tree_sha256']
assert json.loads((O/'code.json').read_text())['tree_sha256']==current
assert summary['complete_native_fixture'] and summary['status']=='ADMIT'
expected={'wrong_h_pin','non_R1','non_N','missing_model_manifest','without_z','k1_slice','altered_shard'}
verified={}
assert '600' in summary['milestones'] and set(summary['milestones'])<={'400','600'}
for step in sorted(summary['milestones']):
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
    receipt=json.loads((O/step/'q/h/receipt.json').read_text())
    statuses={k:v['status'] for k,v in receipt['component_evidence'].items()}
    assert {k for k,v in statuses.items() if v=='NOT_PRESENT'}=={'heads_gf1_connector','heads_frame_embeddings'}
    assert sum(v=='DEFERRED' for v in statuses.values())==7
    if step=='600':
        checkpoint=json.loads((O/step/'checkpoint/complete.json').read_text())
        assert checkpoint['step']==600 and checkpoint['binding']['trainer_commit']=='sha256:'+current
    twins=summary['twins'][step]
    assert set(twins)==expected|({'export_in_training_config'} if step=='400' else {'export_at_stop'})
    assert all(r['status']=='REFUSE' and r.get('refusal') for r in twins.values())
    verified[step]=dict(first_losses={str(rank):next(r['loss'] for r in records if r['rank']==rank) for rank in range(4)},
                        tree_sha256=current,component_statuses=statuses,records=len(records),twins=len(twins),source=str(O/step/'q/f.json'))
(O/'VERIFIED.json').write_text(json.dumps(verified,indent=2)+'\n')
print(json.dumps(verified,indent=2))
