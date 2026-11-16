"""Compose R's reviewed staging plan for the native full media manifest."""
from pathlib import Path
import json
import re
from .paths import r_launcher
from .io import dump,sha,load


def prepare(binding,inputs,destination,token,pool):
    R=r_launcher();L=R.launcher(binding['benchmark'])
    d=Path(destination)
    options=dict(media_root=inputs['uploaded_media_root'],phase_b=False) if binding['benchmark']=='revsi999t32' else {}
    config=L.prepare(token,d,mode='production',pool=pool,**options)
    boot=R.boot_files(d/'BATCH.sh')
    config.update(x0=binding['binding_sha256'],x1=binding['export']['sha256'],x2=0)
    if binding['export']['kind']=='done':
        import export_stage
        step=int(re.fullmatch(r'q8/8865619b/359fcc3c_m(100|200|400|600|800|1000)\.tar',binding['export']['object'])[1])
        done=export_stage.parse_done(Path(binding['export']['done_record']).read_bytes(),'359fcc3c',step)
        if done['sha256']!=binding['export']['sha256']:raise ValueError('D0 receipt changed')
        config.update(x2=1,x3=done['bytes'])
        config['spec']['step']=step
        artifact=dict(kind='c1_export',path=str(L.J.FSW/'ap/8865619b/runs/359fcc3c'/('m'+str(step))/'artifact.json'),sha256=None)
        config['spec']['artifact']=artifact;config['spec']['models']['cp1m200']=dict(artifact)
    files=R.unpack(boot['bootstrap/payload.tar.gz'])
    names=[n for n in files if n.endswith('/cohort/MEDIA_MANIFEST.json')]
    if len(names)!=1:raise ValueError('reviewed media manifest location differs')
    files[names[0]]=json.dumps(inputs['media'],sort_keys=True).encode()
    config['payload_pins']={n:__import__('hashlib').sha256(raw).hexdigest() for n,raw in files.items()}
    payload=L.tar_bytes(files)
    config['payload_sha256']=__import__('hashlib').sha256(payload).hexdigest()
    config['plan_sha256']=L.canonical(config['spec'])
    boot['bootstrap/payload.tar.gz']=payload
    boot['bootstrap/CONFIG.json']=json.dumps(config,sort_keys=True).encode()
    dump(d/'NATIVE_STAGE_CONFIG.json',config)
    return config,boot
