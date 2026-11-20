"""Derive a pinned geometry-only job from the authenticated T1 delivery."""
import os
for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[k]='1'
import sys
from pathlib import Path
import collections
import gzip
import hashlib
import importlib
import json
import tarfile
import numpy as np
HERE=Path(__file__).resolve().parent
BASE=Path('/scratch/jjyeung/orch_n30/cont_ops24_c')
GB=BASE/'gbuild'
sys.path.insert(0,str(GB/'gpkg'))
B=importlib.import_module('build')
T1_SHA='fe9f10b875283b02e3c376b69c3601a4086312ac56ba77fbebedce4eb21e51b7'
PARENT_SHA='ef9575f1eb53d4b603592d6cd94e0bdd07e0a83e69c720c97b4191dadbe4542e'


def reference():
    path=BASE/'cap/t1.gz'
    with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==T1_SHA
    first={};prim={};rep=[];timings=[]
    with gzip.open(path,'rt') as f:
        for line in f:
            r=json.loads(line)
            if r['pass_index']==0:
                if r['geometry']:
                    first.setdefault(r['capture'],r['item_id'])
                    prim[r['item_id']]={k:r[k] for k in ('capture','geometry')}
                timings.append({k:r[k] for k in ('item_id','seconds','timings')})
            else:rep.append(r)
    fields=('scale','camera_to_world_metric','camera_to_world_unscaled','K','canvas_to_source')
    differences=[dict(item_id=r['item_id'],**{k:float(np.max(np.abs(np.asarray(r['geometry'][k])-np.asarray(prim[r['item_id']]['geometry'][k])))) for k in fields}) for r in rep]
    assert len(first)==60 and len(rep)==10
    bounds={k:2*max(r[k] for r in differences) for k in fields}
    p=json.loads((BASE/'cap/t1ret/PARITY.json').read_text());assert p['trusted'] is True
    result=dict(schema=1,capture_sha256=T1_SHA,representatives=list(first.values()),geometry=prim,
                bounds=bounds,repeat_deviations=differences,gap_atol_m=p['gap_atol_m'])
    selected=[r for r in timings if r['item_id'] in first.values()]
    replay_s=sum(r['seconds'] for r in selected)
    forecast=dict(t1_first_per_capture_replay_s=replay_s,t1_first_per_capture_tower_s=sum(r['timings'].get('g3t_s',0) for r in selected),
        captures=60,worker_forecast_minutes=replay_s/60,allocation_planning_minutes=(replay_s+600+120)/60,
        staging_allowance_s=600,publication_allowance_s=120,allowances_measured=False,
        float16_depth_bytes=60*32*51*51*2,lossless_depth_plane_bytes=60*32*51*51*10,
        compressed_return_forecast_bytes=40_000_000,compressed_return_conservative_bytes=80_000_000,return_cap_bytes=1_000_000_000,
        caveat='T1 per-item timings include SAM/linking and exclude staging; staging allowances are planning estimates. No GPU timing of this worker exists.')
    return result,forecast


def build(out=HERE/'out',scripts=HERE/'orchard'):
    raw=(GB/'out2/t1/delivery.tgz').read_bytes();assert B.sha(raw)==PARENT_SHA
    nf={m.name:d for m,d in B.read_tar(raw)};original=dict(nf)
    entries=B.read_tar(nf['0.tgz']);pf={m.name:d for m,d in entries};before=dict(pf)
    pub=json.loads(nf['0.json']);plan=json.loads(pf['9.json']);oldtoken=plan['token']
    assert oldtoken=='a52c1dcfae7bb'
    ref,forecast=reference()
    pf['g/t.py']=pf['g/w.py'];pf['g/w.py']=(HERE/'runtime/w.py').read_bytes()
    pf['g/d.py']=(HERE/'depth_format.py').read_bytes();pf['g/8.json']=B.jd(ref)
    # Keep serving sources and assets byte-identical. Only the capture worker,
    # resource signal, operator deadline and publication cap change.
    common=pf['orchard_h10/common.py'].decode()
    common=B.once(common,"'--time='+walltime, '--signal=B:USR1@1800'","'--exclude=orchard-community-4', '--time='+walltime, '--signal=B:USR1@120'")
    pf['orchard_h10/common.py']=common.encode()
    job=pf['orchard_h10/job.py'].decode().replace('1_900_000_000','1_000_000_000')
    job=job.replace("with (out/'logs/0.log').open('wb') as log:","with open('/dev/null','wb') as log:").replace("with (out/'logs/1.log').open('wb') as log:","with open('/dev/null','wb') as log:")
    job=job.replace("failed=str(error);","failed='E98:'+type(error).__name__.encode().hex();")
    pf['orchard_h10/job.py']=job.encode()
    op=nf['a/6.py'].decode()
    op=B.once(op,"stop_at = end-max(config.get('stop_margin',1800), 5100)","stop_at = min(end-120, clock()+1800)")
    # All worker stdout/stderr (including third-party warnings) stays off public logs.
    op=B.once(op,"with (out/'logs/3.log').open('ab') as log:","with open('/dev/null','ab') as log:")
    op=B.once(op,"    # Exercise the actual tower socket and selector with CPU weight doubles.","    from g.d import decode, encode\n    import numpy as np\n    from types import SimpleNamespace\n    synthetic=SimpleNamespace(depth_grid=np.ones((32,51,51)),grid_uv=np.linspace(0,1000,51))\n    assert np.array_equal(decode(encode(synthetic,{}))[0],synthetic.depth_grid)\n    # Exercise the actual tower socket and selector with CPU weight doubles.")
    nf['a/6.py']=op.encode()
    # 40 minutes accommodates staging. The worker itself has a 30-minute cap.
    for n in ('3.py','SUBMIT.cmd'):
        nf[n]=nf[n].replace(b'05:00:00',b'00:40:00')
    token='a'+B.canonical(dict(budget=2400,stop_margin=120,return_margin=120,parent=PARENT_SHA,payload={n:B.sha(v) for n,v in pf.items() if before.get(n)!=v},operator=B.sha(nf['a/6.py'])))[:12]
    plan['token']=token;plan['stop_margin']=120;plan['return_margin']=120;plan['budget_gpu_seconds']=2400
    for n,d in pf.items():
        if n!='9.json' and d!=before.get(n):plan['payload_pins'][n]=dict(bytes=len(d),sha256=B.sha(d))
    pf['9.json']=B.jd(plan)
    nf['0.tgz']=B.write_tar([(m,pf[m.name]) for m,d in entries]+[B.added(n,pf[n]) for n in sorted(set(pf)-set(before))])
    pub.update(token=token,payload_bytes=len(nf['0.tgz']),payload_sha256=B.sha(nf['0.tgz']),plan_sha256=B.canonical(plan))
    nf['0.json']=nf['CONFIG.json']=B.jd(pub)
    nf['BATCH.sh']=B.make_batch(original['BATCH.sh'],oldtoken,token,original['0.json'],nf['0.json'],original['a/6.py'],nf['a/6.py'])
    pk=json.loads(nf['PACKAGE.json']);pk['token']=token
    pk['files']={n:B.sha(v) for n,v in nf.items() if n!='PACKAGE.json'};nf['PACKAGE.json']=B.jd(pk)
    delivery=B.write_tar([B.added(n,nf[n]) for n in sorted(nf)])
    result=dict(token=token,package='/project/community/jjyeung/'+token,job_name='a15_cot_ap'+token,
        walltime='00:40:00',delivery_bytes=len(delivery),delivery_sha256=B.sha(delivery),
        installed_bytes=sum(map(len,nf.values())),files={n:B.sha(v) for n,v in nf.items()},
        payload_files={n:B.sha(v) for n,v in pf.items()},payload_sha256=B.sha(nf['0.tgz']),plan_sha256=B.canonical(plan),
        parent_sha256=PARENT_SHA,changed_payload=[n for n in pf if before.get(n)!=pf[n]])
    out.mkdir(parents=True,exist_ok=True)
    for n,v in [('BUILD.json',B.jd(result)),('REFERENCE.json',B.jd(ref)),('FORECAST.json',B.jd(forecast)),('delivery.tgz',delivery)]:
        (out/n).write_bytes(v)
    import scripts as S
    S.render(out,scripts,cpu_partition='general')
    for p in scripts.glob('*.sh'):
        if p.name!='o_place.sh':
            text=p.read_text().replace('05:00:00','00:40:00').replace('--cpus-per-task=8','--cpus-per-task=16').replace("--exclude='orchard-flame-[0-31]'",'--exclude=orchard-community-4')
            if p.name=='o_fetch.sh':
                text=text.replace("with (dest/name).open('xb') as f:f.write(raw)","with (dest/({'CAPTURE.json':'4.json','PARITY.json':'5.json'}[name])).open('xb') as f:f.write(raw)")
                text=text.replace("print(name);print(raw.decode())","print(hashlib.sha256(raw).hexdigest())")
            p.write_text(text)
    (scripts/'o_get.sh').write_text('#!/bin/bash\nset -euo pipefail\nP=/project/community/jjyeung/'+token+'\ntar -czf - -C "$P/a/f" 0.tgz 4.json 5.json EXIT.json RETURN_RECEIPT.json\n')
    (scripts/'o_sub_hand.sh').write_bytes((scripts/'o_check_sub.sh').read_bytes())
    return result


if __name__=='__main__':
    info=build();print(json.dumps({k:info[k] for k in ('token','delivery_bytes','delivery_sha256','installed_bytes','walltime')}))
