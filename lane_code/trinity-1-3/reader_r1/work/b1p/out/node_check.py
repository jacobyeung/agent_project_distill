"""Run the production staging and CPU restore in a fresh node-local namespace."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',required=True)
    parser.add_argument('--sequence',required=True)
    parser.add_argument('--return-tar');parser.add_argument('--submerge')
    parser.add_argument('--results',required=True)
    args=parser.parse_args()
    job=os.environ.get('SLURM_JOB_ID','')
    if not job.isdigit():raise ValueError('Run on an allocated compute node')
    package=Path(args.package).resolve()
    public=json.loads((package/'0.json').read_text())
    payload=(package/'0.tgz').read_bytes()
    if hashlib.sha256(payload).hexdigest()!=public['payload_sha256']:
        raise ValueError('Package hash differs')
    receipt=json.loads((package/'PACKAGE.json').read_text())
    for name,h in receipt['files'].items():
        if hashlib.sha256((package/name).read_bytes()).hexdigest()!=h:raise ValueError('Package descriptor differs')
    sequence=Path(args.sequence)
    if sequence.read_bytes()!=(package/'a/6.py').read_bytes():raise ValueError('Operator differs')
    root=Path(tempfile.mkdtemp(prefix='a'+job+public['token'],dir='/tmp'))
    # Bootstrap only the authenticated staging modules, using the batch's layout.
    with tarfile.open(package/'0.tgz') as tar:
        for entry in tar:
            if not entry.name.startswith('orchard_h10/'):continue
            if not entry.isfile() or '..' in Path(entry.name).parts:raise ValueError('Unsafe code')
            path=root/'bootstrap'/entry.name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(tar.extractfile(entry).read())
    sys.path.insert(0,str(root/'bootstrap'))
    from orchard_h10.common import read_config,template,write,sha,checked_run,install_process_guard
    from orchard_h10.job import check_inputs,stage
    from orchard_h10.export_pins import load
    cfg=read_config(package);inputs=check_inputs(json.loads((package/'a/1.json').read_text()),cfg,package=package)
    pins=load(inputs,package);S,J,*_=template()
    proof=J.storage_proof(root,job=job)
    install_process_guard(root)
    stage(root,cfg,inputs,S,J)
    for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
    env=J.environment(root)
    env={k:v for k,v in env.items() if 'sam' not in k.lower()}
    env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16')
    dispatch=root/'a';(dispatch/'5.py').write_bytes((root/'bootstrap/orchard_h10/entry.py').read_bytes())
    write(dispatch/'0.json',dict(action=0,package=cfg['logical']+'/p',config=cfg,
                                inputs={**inputs,'_export':pins}))
    results=Path(args.results).resolve();results.mkdir(parents=True,exist_ok=False)
    with (results/'0.log').open('wb') as log:
        checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'0.json')],
                    env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    ready=json.loads(J.physical(root,cfg['logical']+'/d/READY.json').read_text())
    (dispatch/'6.py').write_bytes(sequence.read_bytes())
    run_cfg=dict(package=cfg['logical']+'/p',output=cfg['logical']+'/r',python=inputs['python'],
        export=cfg['logical']+'/d/e',binding=cfg['logical']+'/d/binding.json',
        export_pin=cfg['logical']+'/d/6.json',settings=cfg['logical']+'/d/settings.json',
        plan_sha256=cfg['plan_sha256'],inputs_sha256=sha(package/'a/1.json'),
        operator_sha256=sha(sequence),device='cpu',prefix=[])
    write(dispatch/'1.json',dict(package=run_cfg['package'],config=run_cfg,rehearsal=True))
    with (results/'1.log').open('wb') as log:
        checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'6.py'),str(dispatch/'1.json')],
                    env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    write(results/'CPU.json',dict(passed=True,plan=cfg['plan_sha256'],inputs=sha(package/'a/1.json'),
                                 operator_sha256=sha(sequence),
                                 payload=cfg['payload_sha256'],storage=proof,ready=ready,root=str(root)))
    print(json.dumps(dict(results=str(results),root=str(root),passed=True)))

if __name__=='__main__':main()
