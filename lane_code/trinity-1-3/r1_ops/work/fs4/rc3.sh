#!/bin/bash
# r1_ops4: locate 171377's in-job derived config (data_receipt.json "config" pin) on the pool; verify sha and i.py identity; store as runtime_config.json.
set +x; set -uo pipefail; export TZ=UTC; umask 077
R=/project/community/jjyeung/okh7/x_69d2930d/runs/673bc60f
python3 -I -B - "$R" <<'PYCODE'
import json,sys,hashlib,os,base64,gzip
from pathlib import Path
R=Path(sys.argv[1]); WANT='620d5cf8c573afd72e9dcbcf822fb8c8cbae27dd6c2ca803ec156d7cda41e51a'
d=json.loads((R/'inputs/data_receipt.json').read_text())
pin=d['config']; print('PIN',pin)
logical=Path(pin['path']); parts=logical.parts
i=parts.index('inputs') if 'inputs' in parts else None
rel=Path(*parts[i+1:]) if i is not None else None
cand=R/'inputs'/rel if rel else None
print('CAND',cand, cand.exists() if cand else None)
def ident(cfg):
    value={k:v for k,v in cfg.items() if k not in ('preparation','admission','authorization','milestone_gate')}
    if 'readout' in value: value['readout']={k:v for k,v in value['readout'].items() if k!='contiguous_clips'}
    if value.get('frame_layout')=='spread': value.pop('frame_layout')
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
if cand and cand.is_file():
    raw=cand.read_bytes(); sh=hashlib.sha256(raw).hexdigest(); idn=ident(json.loads(raw))
    print('FILE',len(raw),'sha256',sh,'pin_ok',sh==pin['sha256'],'identity',idn,'match',idn==WANT)
    if sh==pin['sha256'] and idn==WANT:
        dst=R/'runtime_config.json'
        if dst.exists(): print('EXISTS',dst)
        else:
            fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); os.write(fd,raw); os.close(fd); print('STORED',dst)
        print('B64',base64.b64encode(gzip.compress(raw)).decode())
else:
    print('NOT ON POOL; inputs listing:'); 
    for p in sorted((R/'inputs').rglob('*'))[:60]: print(' ',p.relative_to(R), p.stat().st_size if p.is_file() else 'dir')
PYCODE
