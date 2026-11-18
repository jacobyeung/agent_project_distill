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
    write(results/'CPU.json',dict(passed=True,plan=cfg['plan_sha256'],inputs=sha(package/'a/1.json'),
                                 payload=cfg['payload_sha256'],storage=proof,ready=ready,root=str(root)))
    if args.return_tar:
        if not args.submerge:raise ValueError('Require the unchanged submerge.py')
        returned=root/'sj/0';returned.mkdir()
        with Path(args.return_tar).open('rb') as stream:
            S.extract_stream(stream,returned,None,512*1024**2)
        identity=json.loads((returned/'metadata/IDENTITY.json').read_text())
        from orchard_h10.common import canonical
        if (identity['plan']!=cfg['plan_sha256'] or identity['cards']!=1
                or identity['inputs']!=canonical({k:v for k,v in inputs.items() if k!='resume'})):
            raise ValueError('Return does not bind these inputs and package')
        (root/'sj/6.py').write_bytes(Path(args.submerge).read_bytes())
        with (results/'1.log').open('wb') as log:
            checked_run(J.namespace(root)+[inputs['python'],'-B','-I','/scratch/jjyeung/6.py',
                        '/scratch/jjyeung/0/metadata/journals','/scratch/jjyeung/1','3'],
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        curve=json.loads((root/'sj/1/curve.json').read_text())
        binding=json.loads((returned/'metadata/journals/0/0/environment.json').read_text())['binding']
        if any(curve[k]!=binding[k] for k in ('export_sha256','evaluator_code_sha256','lineage','step')):
            raise ValueError('Scored export or evaluator identity differs from journals')
        # Publish only the small score artifacts after complete-prefix validation.
        for name in ('curve.json','items.jsonl','report.md'):
            (results/name).write_bytes((root/'sj/1'/name).read_bytes())
    print(json.dumps(dict(results=str(results),root=str(root),passed=True)))


if __name__=='__main__':main()
