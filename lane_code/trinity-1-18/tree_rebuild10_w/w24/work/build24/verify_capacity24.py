from pathlib import Path
import math,sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24';O=D/'proofs/capacity';F=O/'final'
sys.path.insert(0,str(D));import joblib as J
result=J.load(F/'RESULT.json');assert result['status']=='ADMIT' and result['complete_native_fixture']
assert result['tree_sha256']==J.load(L/'out/TREE_SEAL.json')['tree_sha256']
verified={};expected={'wrong_h_pin','non_R1','non_N','missing_model_manifest','without_z','k1_slice','altered_shard'}
for step in ('600','400'):
 x=result['milestones'][step];cfg=J.load(x['config']['path']);old=J.load(J.load(x['original_producer_result']['path'])['config']['path'])
 assert cfg['streams']==old['streams'];assert cfg['r2_sampling']==old['r2_sampling']
 # The plan identity hashes the entire binding, not the indices file alone.
 import hashlib,json
 digest=lambda value:hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 assert x['audit']['row_plan_sha256']==digest(cfg['r2_sampling'])
 assert x['audit']['card_sha256']==cfg['r2_sampling']['card']['sha256']
 assert x['audit']['complete'] and x['audit']['largest_repeat']<=4
 assert x['absolute_resume_step']==int(step) and x['forward']['absolute_step']==int(step)
 rows=J.load(F/step/'f.json')['records'];assert len(rows)==288
 assert {r['rank'] for r in rows}==set(range(4));assert all(r['finite'] and math.isfinite(r['loss']) for r in rows)
 for rank in range(4):assert {r['stream'] for r in rows if r['rank']==rank}=={'vqa','pose','routing','pointing'}
 assert set(x['twins'])==expected|({'export_at_stop'} if step=='600' else {'export_in_training_config'})
 assert all(v['status']=='REFUSE' and v['refusal'] for v in x['twins'].values())
 assert all(n==0 for n in x['deferred_cells'].values()) and x['direction_rows']==39971
 receipt=J.load(F/step/'h/receipt.json');statuses={k:v['status'] for k,v in receipt['component_evidence'].items()}
 assert {k for k,v in statuses.items() if v=='NOT_PRESENT'}=={'heads_gf1_connector','heads_frame_embeddings'}
 assert sum(v=='DEFERRED' for v in statuses.values())==7
 verified[step]=dict(status='ADMIT',first_losses=x['first_losses'],records=len(rows),twins=len(x['twins']),
    source_tree=result['tree_sha256'],population=x['direction_rows'],deferred=x['deferred_cells'],component_statuses=statuses,
    sampler_largest_repeat=x['audit']['largest_repeat'],same_prepared_stores=True,same_sampler=True)
source=J.load(O/'vqa/receipt.json');lists=source.get('removals',[])
# This record is emitted by the real removal-list producer in the full run.
named=[r for r in lists if r.get('file',{}).get('sha256','').startswith('d1454a44')]
assert len(named)==1 and named[0]['matched']==109 and named[0]['removed']==107
assert sum(r['removed'] for r in lists)==109
J.write(F/'VERIFIED.json',dict(status='PASS',milestones=verified,named_removal_producer=named,twins_boundary=J.load(O/'TWIN_BOUNDARY.json')))
print('PASS: both milestones, all ranks, immutable stores and sampler, zero deferred cells, 16 refusal twins')
