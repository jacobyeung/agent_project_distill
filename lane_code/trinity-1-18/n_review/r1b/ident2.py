import sys,json,base64,hashlib
sys.path.insert(0,'/tmp/x/tree')
from student_pilot.carrier_c1_run import identity
out={}
for name in ('c','n'):
    raw=open(f'/tmp/x/k/{name}.json','rb').read(); v=json.loads(raw); b=base64.b64decode(v['payload'])
    assert hashlib.sha256(b).hexdigest()==v['sha256']
    cfg=json.loads(b)
    r=dict(file_sha256=hashlib.sha256(raw).hexdigest(),payload_sha256=v['sha256'],identity=identity(cfg))
    t=cfg.get('r1_training',{})
    r['remove_files']=[p['sha256'][:8] for p in cfg.get('remove_files',[])]
    r['init_artifact']=(t.get('init_artifact') or {}).get('sha256'); r['init_policy']=t.get('init_policy')
    r['handover_receipt']=(t.get('handover_receipt') or {}).get('sha256')
    for k in ('routing_slices','row_slice_inputs','routing_inputs','world_size','direction_twins'):
        r['r1.'+k]=t.get(k) if k!='direction_twins' else bool(t.get(k))
    for k in ('r2_all_stream_exclusions','r2_scene_rebuild','scene_coverage','world_size'):
        r[k]=cfg.get(k)
    r['dev']=(cfg.get('dev_scene_exclusions') or {}).get('sha256'); r['bench']=(cfg.get('benchmark_scene_exclusions') or {}).get('sha256')
    r['streams']={s:p['sha256'][:8] for s,p in cfg.get('streams',{}).items()}
    out[name]=r
print(json.dumps(out,indent=1,default=str))
