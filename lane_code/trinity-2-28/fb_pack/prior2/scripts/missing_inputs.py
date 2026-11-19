import json,hashlib,base64
from pathlib import Path
W=Path.cwd();RO=Path('/scratch/jjyeung/orch_n30/fb_pack/ro');R=RO/'orch_n30/tree_rebuild10_w/w24';inputs=[]
def pin(p):
 p=Path(p);v=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest());inputs.append(v);return v
loc=json.loads((W/'out/INPUT_LOCATIONS.json').read_text());pin(W/'out/INPUT_LOCATIONS.json')
recovery=json.loads((W/'out/CAPSULE_RECOVERY.json').read_text());pin(W/'out/CAPSULE_RECOVERY.json')
found={**loc['found'],**recovery['found']}
missing=[dict(v,expected_mirror_path=str(RO/v['path'].removeprefix('/scratch/jjyeung/')),status='MISSING') for v in loc['missing'] if v['sha256'] not in found]
cfg=json.loads((R/'out/N_LAUNCH_CONFIG.json').read_text());pin(R/'out/N_LAUNCH_CONFIG.json')
for k in ('pointing','pose','routing'):
 v=cfg['streams'][k];missing.append(dict(v,status='MISSING_PRODUCTION_NATIVE_POPULATION',reason='Authenticated post-filter offset table for stream '+k+' is not supplied.'))
missing.append(dict(path='/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/f/469ddece/receipt.json',status='MISSING',sha256='MISSING',reason='Production preparation receipt is not supplied.'))
kit=json.loads((R/'out/kit_n_go/k/n.json').read_text());pin(R/'out/kit_n_go/k/n.json');raw=base64.b64decode(kit['payload']);assert hashlib.sha256(raw).hexdigest()==kit['sha256'];kit=json.loads(raw)
assert [p['sha256'] for p in cfg['remove_files']]==[p['sha256'] for p in kit['remove_files']]
assert cfg['r2_sampling']['card']['sha256']==kit['r2_sampling']['card']['sha256']
removal=[dict(v,expected_mirror_path=str(RO/v['path'].removeprefix('/scratch/jjyeung/')),available=(RO/v['path'].removeprefix('/scratch/jjyeung/')).is_file() or v['sha256'] in found) for v in cfg['remove_files']]
record={'status':'NO_GO','production_gate':'MISSING: cannot independently reconstruct N production cell populations after all filters.','missing':missing,'removal_lists':removal,'kit_matches_launch_removal_hashes':True,'kit_matches_launch_card_hash':True,'inputs':inputs+[pin(__file__)]}
(W/'out/MISSING_INPUTS.json').write_text(json.dumps(record,indent=2)+'\n')
print('Missing removals',[(p['path'],p['sha256']) for p in removal if not p['available']])
