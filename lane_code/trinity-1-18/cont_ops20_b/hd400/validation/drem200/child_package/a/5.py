"""Run the production staging and CPU restore in a fresh node-local namespace."""
import argparse
import hashlib
import json
import os
import runpy
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


def validate_full_reader(rehearsal):
    if len(rehearsal)!=1:raise ValueError('CPU read count differs')
    full=rehearsal[0]['full_reader']
    if full.get('passed') is not True or full.get('device')!='cpu':raise ValueError('Full reader failed')
    records=full.get('records',[])
    if [r['set'] for r in records]!=['R0-dev-reworded', 'R0-dev-twin']:raise ValueError('Full reader sets differ')
    for r in records:
        row=r['record'];output=row['output']
        if (r.get('passed') is not True or row.get('complete') is not True or row['id']!=r['item']
            or row['type']!='object_abs_distance' or output['finish']!='eos'
            or len(r['frames'])!=32 or r['official_score']['parse_failed']
            or output['scores']['answer']!=r['official_score']['score']):
            raise ValueError('Full reader record failed')
    return full


def check_bundle_guard(package, root):
    """Exercise the embedded batch layout through the installed process guard."""
    import ast
    import io
    batch = (package/'BATCH.sh').read_text()
    lines = [line for line in batch.splitlines() if line.startswith('b=bytes.fromhex(')]
    if len(lines) != 1:
        raise ValueError('Bundle encoding differs')
    expression = ast.parse(lines[0]).body[0].value
    if (not isinstance(expression, ast.Call) or not (isinstance(expression.func,ast.Attribute) and isinstance(expression.func.value,ast.Name) and expression.func.value.id=='bytes' and expression.func.attr=='fromhex')
            or len(expression.args) != 1 or expression.keywords):
        raise ValueError('Bundle encoding differs')
    raw = bytes.fromhex(ast.literal_eval(expression.args[0]))
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        members = archive.getmembers()
        if len(members) != 3 or {m.name for m in members} != {'0.py', '0.json', '7.py'}:
            raise ValueError('Bundle inventory differs')
        for member in members:
            if not member.isfile():
                raise ValueError('Unsafe bundle member')
            with (root/member.name).open('xb') as stream:
                stream.write(archive.extractfile(member).read())
    if json.loads((root/'0.json').read_text()) != json.loads((package/'0.json').read_text()):
        raise ValueError('Bundle descriptor differs')
    expected = (package/'a/6.py').read_bytes()
    if (root/'7.py').read_bytes() != expected:
        raise ValueError('Bundled operator differs')
    from orchard_h10.common import template, sha
    _, _, results, _, _ = template()
    pool = root/'wpool'
    token = json.loads((root/'0.json').read_text())['token']
    before = sha(root/'7.py')
    # This is the production job's call, including its guarded Popen spawn.
    receipt = results.write_test(str(pool), token)
    evidence = pool/token/'.wtest'
    if receipt['bytes'] != 4*1024**2 or evidence.stat().st_size != receipt['bytes'] or sha(evidence) != receipt['sha256']:
        raise ValueError('Write-test receipt differs')
    vendor = Path(results.__file__).with_name('return_io.py')
    if (root/'6.py').read_bytes() != vendor.read_bytes():
        raise ValueError('Process guard did not exercise its write target')
    if sha(root/'7.py') != before:
        raise ValueError('Process guard changed bundled operator')
    return dict(passed=True, operator_sha256=before, operator_sha256_before=before,
                operator_sha256_after=sha(root/'7.py'), write_test=receipt,
                pool=str(pool), token=token, guard_target_sha256=sha(root/'6.py'),
                batch_sha256=hashlib.sha256(batch.encode()).hexdigest(),
                path='7.py', guard_target='6.py', action='test',
                events=['guard_installed', 'write_test'])


def dispatch_operator(root, proof, argv, original, **kwargs):
    """Run the bundled bootstrap wrapper only after the guarded write test."""
    from orchard_h10.common import sha
    operator = root/'7.py'
    if operator.resolve() in {(root/'6.py').resolve(), (root/'a/6.py').resolve()}:
        raise ValueError('Operator collides with guard target')
    if proof.get('passed') is not True or proof.get('events') != ['guard_installed', 'write_test']:
        raise ValueError('Write test must precede operator dispatch')
    evidence = root/'wpool'/proof['token']/'.wtest'
    if (proof['pool'] != str(root/'wpool') or proof['write_test']['bytes'] != 4*1024**2
            or evidence.stat().st_size != proof['write_test']['bytes']
            or sha(evidence) != proof['write_test']['sha256']
            or sha(root/'6.py') != proof['guard_target_sha256']):
        raise ValueError('Entry write-test evidence differs')
    before = proof['operator_sha256_before']
    calls = []
    def checked(dispatched, *args, **kw):
        if dispatched[-2:] != [str(operator), str(root/'a/1.json')]:
            raise ValueError('Bootstrap did not dispatch bundled operator')
        calls.append(list(dispatched))
        return original(dispatched, *args, **kw)
    # Import the exact bundled bootstrap without invoking production job.main.
    make_dispatch = runpy.run_path(str(root/'0.py'))['make_dispatch']
    make_dispatch(root, checked, before)(argv, **kwargs)
    if len(calls) != 1 or sha(operator) != before:
        raise ValueError('Dispatched operator changed')
    proof.update(operator_sha256_after=sha(operator), requested_argv=list(argv),
                 dispatched_argv=calls[0], events=proof['events']+['operator_dispatch'])
    return dict(**proof, entry_sequence_passed=True)


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
    from orchard_h10.common import read_config,template,write,sha,checked_run,install_process_guard,canonical
    from orchard_h10.job import check_inputs,stage
    from orchard_h10.export_pins import load
    cfg=read_config(package);inputs=check_inputs(json.loads((package/'a/1.json').read_text()),cfg,package=package)
    pins=load(inputs,package);S,J,*_=template()
    proof=J.storage_proof(root,job=job)
    install_process_guard(root)
    stage(root,cfg,inputs,S,J)
    bundle_guard=check_bundle_guard(package,root)
    for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
    env=J.environment(root)
    env={k:v for k,v in env.items() if 'sam' not in k.lower()}
    env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8')
    dispatch=root/'a';(dispatch/'5.py').write_bytes((root/'bootstrap/orchard_h10/entry.py').read_bytes())
    write(dispatch/'0.json',dict(action=0,package=cfg['logical']+'/p',config=cfg,
                                inputs={**inputs,'_export':pins}))
    results=Path(args.results).resolve();results.mkdir(parents=True,exist_ok=False)
    with (results/'0.log').open('wb') as log:
        checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'0.json')],
                    env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    ready=json.loads(J.physical(root,cfg['logical']+'/d/READY.json').read_text())
    settings=json.loads(J.physical(root,cfg['logical']+'/d/settings.json').read_text())
    if (settings['stage1_select_rule']!='candidates_argmax' or settings['perception_memo']!='on'
        or settings.get('types')!=['object_abs_distance'] or settings['perception_memo_modules']!=['g3t'] or settings['perception_memo_verify_ids']!=[]):
        raise ValueError('Prepared default settings differ')
    run_cfg=dict(package=cfg['logical']+'/p',output=cfg['logical']+'/r',python=inputs['python'],
        export=cfg['logical']+'/d/e',binding=cfg['logical']+'/d/binding.json',
        export_pin=cfg['logical']+'/d/6.json',settings=cfg['logical']+'/d/settings.json',
        plan_sha256=cfg['plan_sha256'],inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),
        operator_sha256=sha(sequence),device='cpu',prefix=[],measure_memory=True)
    write(dispatch/'1.json',dict(action=1,package=run_cfg['package'],config=run_cfg,rehearsal=True))
    with (results/'1.log').open('wb') as log:
        entry_sequence=dispatch_operator(root,bundle_guard,
                    J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'1.json')],checked_run,
                    env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    rehearsal=json.loads(J.physical(root,cfg['logical']+'/r/REHEARSAL.json').read_text())
    full=validate_full_reader(rehearsal)
    write(results/'FULL_READER.json',full)
    memory=json.loads(J.physical(root,cfg['logical']+'/r/metadata/MEMORY.json').read_text())
    write(results/'MEMORY.json',memory)
    write(results/'CPU.json',dict(passed=True,entry_sequence_passed=True,entry_sequence=entry_sequence,bundle_guard_passed=True,bundle_guard=bundle_guard,full_reader_passed=True,full_reader=full,memory=memory,plan=cfg['plan_sha256'],inputs=sha(package/'a/1.json'),
                                 operator_sha256=sha(sequence),
                                 payload=cfg['payload_sha256'],storage=proof,ready=ready,root=str(root)))
    print(json.dumps(dict(results=str(results),root=str(root),passed=True)))

if __name__=='__main__':main()
