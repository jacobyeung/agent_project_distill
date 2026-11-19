R=/project/community/jjyeung/okh7/x_ee227714/runs/6ed2c7aa/inputs
/usr/bin/python3 - $R <<'PY'
import hashlib,json,sys
from pathlib import Path
r=Path(sys.argv[1]); c=r/'prepare_da5580b7d92f490bb3cfe8df447e7820/config.json'; s=r/'prepare_da5580b7d92f490bb3cfe8df447e7820/prepared/s1_receipt.json'; d=r/'data_receipt.json'
raw={k:p.read_bytes() for k,p in dict(config=c,receipt=s,data_receipt=d).items()}
sha={k:hashlib.sha256(v).hexdigest() for k,v in raw.items()}
cfg,rec,data=[json.loads(raw[k]) for k in ('config','receipt','data_receipt')]
out=dict(sha=sha,bytes={k:len(v) for k,v in raw.items()},
 data_status=data.get('status'),data_schema=data.get('schema'),real_frames_verified=data.get('real_frames_verified'),rehearsal=data.get('rehearsal'),synthetic=data.get('synthetic',False),
 data_config_sha_matches=data['config']['sha256']==sha['config'],data_config_path=data['config'].get('path'),
 data_prep_eq_cfg_prep=data.get('preparation')==cfg.get('preparation'),cfg_prep_sha_eq_receipt=cfg['preparation']['sha256']==sha['receipt'],cfg_prep_path=cfg['preparation'].get('path'),
 base_identity=cfg.get('base_identity'),frame_layout_cfg=cfg.get('frame_layout'),frame_layout_receipt=rec.get('frame_layout'),receipt_config_sha256=rec.get('config_sha256'),
 receipt_model_keys=sorted(rec.get('model',{}))[:8] if isinstance(rec.get('model'),dict) else type(rec.get('model')).__name__,
 data_receipt_source_path_derived=str(Path(data['config']['path']).parent.parent/'data_receipt.json'))
print(json.dumps(out,indent=1))
PY
