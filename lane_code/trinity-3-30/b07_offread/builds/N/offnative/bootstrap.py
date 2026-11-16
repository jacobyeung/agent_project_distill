"""Execute a staged worker with an outer deadline and bounded terminal return."""
from pathlib import Path
import json
import os
import sys
from .io import load,dump,sha,digest,tar_bytes


def binding(spec):
    kind='e2e' if spec['reader_code'] else 'harness'
    return {'benchmark':'revsi999t32','mode':('fixture','proof','production')[spec['mode_code']],
            'binding_sha256':spec['x0'],'reader':{'kind':kind,'freeze_values':spec.get('freeze_values')},
            'export':spec['export'],'arms':spec['arms'],'read_config':{'frames':spec['frames'],'g3t':spec['g3t']}}


def work(plan):
    from .production import Runtime
    from .worker import Worker
    from .scoring import Scorer
    b=binding(plan['spec']);config=plan['config']
    if os.environ.get('OFFNATIVE_DEADLINE'):config=dict(config,deadline_utc=os.environ['OFFNATIVE_DEADLINE'])
    runtime=Runtime(Path.cwd()/'work/runtime',plan['items'],b,plan['inputs'])
    worker=Worker(config,b,plan['items'],runtime,Scorer(plan['inputs']['label_file']),Path.cwd()/'return')
    worker.run()


def main():
    plan=load('p.json')
    if '--worker' in sys.argv:
        work(plan);return
    from .watchdog import run
    from datetime import datetime,timezone
    import time
    config=plan['config'];limit=config['job']['time_limit_s']
    deadline=datetime.fromtimestamp(time.time()+limit,timezone.utc).isoformat()
    from .paths import r_launcher
    r_launcher().launcher('revsi999t32')
    import orchard_results
    orchard_results.write_test(config['pool'],config['token'])
    outcome=run([sys.executable,'-B','0.py','--worker'],Path.cwd(),Path.cwd()/'WATCHDOG.json',
                deadline_utc=deadline,limit=limit-600)
    returned=Path.cwd()/'return';returned.mkdir(exist_ok=True)
    if outcome['returncode']!=0 or not (returned/'COMPLETE.json').exists():
        dump(returned/'FAILED.json',outcome)
    else:
        marker=load(returned/'COMPLETE.json')
        marker.update(plan_sha256=plan['config_sha256'],synthetic=False)
        dump(returned/'COMPLETE.json',marker)
    files={str(p.relative_to(returned)):p.read_bytes() for p in returned.rglob('*') if p.is_file()}
    if sum(map(len,files.values()))>90_000_000:raise ValueError('return byte cap exceeded')
    target=Path.cwd()/'result.tar.gz'
    import gzip
    target.write_bytes(gzip.compress(tar_bytes(files),mtime=0))
    # Publication is external and requires both authenticated transport receipts.
    dump(Path.cwd()/'EXIT.json',{'status':'COMPLETE' if outcome['returncode']==0 else 'FAILED',
        'token':config['token'],'job':int(os.environ.get('SLURM_JOB_ID','0')),
        'binding_sha256':config['x0'],'config_sha256':plan['config_sha256'],
        'packet_sha256':os.environ.get('OFFNATIVE_PACKET_SHA256'),'synthetic':False,
        'archive':{'name':target.name,'sha256':sha(target),'bytes':target.stat().st_size}})
    (Path.cwd()/'JOB.log').write_text(json.dumps({'x0':sha(Path.cwd()/'EXIT.json')})+'\n')
    from .transport import publish
    publish(config,Path.cwd())

