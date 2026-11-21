
<<HEX 0>>
"""Opaque JSON transport; canonical hashes retain their logical representation."""
import json

if not hasattr(json, '_a0_loads'):
    json._a0_loads = json.loads
    json._a0_dumps = json.dumps

wire_loads = json._a0_loads
wire_dumps = json._a0_dumps
TAG = 'a0'


def raw(data):
    value = wire_loads(data)
    if isinstance(value, dict) and set(value) == {TAG} and isinstance(value[TAG], str):
        return bytes.fromhex(value[TAG])
    return data.encode() if isinstance(data, str) else data


def pack(data):
    if isinstance(data, str):data=data.encode()
    return (wire_dumps({TAG:data.hex()},separators=(',', ':'))+'\n').encode()


def loads(data, *args, **kwargs):
    value=wire_loads(data,*args,**kwargs)
    if isinstance(value,dict) and set(value)=={TAG} and isinstance(value[TAG],str):
        return wire_loads(bytes.fromhex(value[TAG]),*args,**kwargs)
    return value


def load(stream, *args, **kwargs):return loads(stream.read(), *args, **kwargs)


def dumps(value, *args, **kwargs):
    data = wire_dumps(value, *args, **kwargs)
    return pack(data).decode().rstrip('\n') if kwargs.get('indent') is not None else data


def dump(value, stream, *args, **kwargs):
    stream.write(pack(wire_dumps(value, *args, **kwargs)).decode())


def install():
    json.loads=loads;json.load=load;json.dumps=dumps;json.dump=dump

<</HEX>>

<<HEX 0>>
"""Reserve cumulative package metadata writes before forwarding each write."""
import builtins
import fcntl
import io
import os

LIMIT=2_000_000
TOKEN='TOKEN'
PREFIX='/project/community/jjyeung/'+TOKEN+'/'
_original=builtins.open


def charge(size):
    # Fixed-width accounting includes its own writes; failed writes stay charged.
    with _original(os.open(PREFIX+'a/18',os.O_RDWR|os.O_CREAT,0o600), 'r+b', buffering=0) as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        lock.seek(0); raw=lock.read(32);used=int(raw or b'0')
        cost=size+32
        if used+cost>LIMIT:raise OSError('E70')
        lock.seek(0);lock.write(('%032d'%(used+cost)).encode());os.fsync(lock.fileno())


class Writer:
    def __init__(self,stream):self.stream=stream
    def write(self,data):
        charge(len(data.encode(self.stream.encoding or 'utf-8')) if isinstance(data,str) else len(data))
        return self.stream.write(data)
    def writelines(self,lines):
        for line in lines:self.write(line)
    def __getattr__(self,name):return getattr(self.stream,name)
    def __enter__(self):return self
    def __exit__(self,*args):return self.stream.__exit__(*args)


def install():
    if getattr(builtins.open,'_a18',False):return
    io_open=io.open
    def wrap(original):
        def opened(file,mode='r',*args,**kwargs):
            path=os.path.abspath(os.fspath(file)) if not isinstance(file,int) else ''
            watched=path.startswith(PREFIX) and not path.startswith(PREFIX+'a/f/') and any(x in mode for x in 'wax+')
            if watched:charge(0)
            stream=original(file,mode,*args,**kwargs)
            return Writer(stream) if watched else stream
        opened._a18=True
        return opened
    builtins.open=wrap(_original);io.open=wrap(io_open)

<</HEX>>
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


"""Retain bounded CPU comparisons for authenticated failure publication."""
_comparisons=[]


def compare(name, expected, found):
    def bounded(value):
        raw=json.dumps(value,sort_keys=True)
        return value if len(raw)<=2048 else raw[:2048]
    item=dict(check=name,expected=bounded(expected),found=bounded(found),passed=expected==found)
    _comparisons.append(item)
    del _comparisons[:-16]
    if not item['passed']:
        raise ValueError(name+' expected='+json.dumps(item['expected'])+' found='+json.dumps(item['found']))


def cpu_failure(error):
    # This handler covers staging, both guards, preparation and dispatch.
    job=os.environ.get('SLURM_JOB_ID','')
    if not job.isdigit() or '--package' not in sys.argv:return
    package=Path(sys.argv[sys.argv.index('--package')+1])
    public=json.loads((package/'0.json').read_text())
    value=dict(job=job,plan=public['plan_sha256'],passed=False,
               error=(type(error).__name__+': '+str(error))[:2048],
               comparisons=_comparisons,expected=None,found=None)
    last=_comparisons[-1] if _comparisons else None
    if last:value.update(expected=last['expected'],found=last['found'])
    value['failed_check']=last['check'] if last and not last['passed'] else None
    if not last:value['comparison_status']='No comparison reached; inspect the exception'
    elif last['passed']:value['comparison_status']='Last comparison passed; the exception came later'
    if isinstance(error,subprocess.CalledProcessError):
        value.update(failed_check='Pool subprocess exit status',comparison_status='Subprocess failed',
                     expected=dict(returncode=0),found=dict(returncode=error.returncode,
                     stderr=str(error.stderr)[-2048:],stdout=str(error.stdout)[-2048:]))
    # One write keeps the metadata ledger to a single charge.
    with (package/'a/30.json').open('w') as stream:stream.write(json.dumps(value))


def check_bundle_guard(package, root):
    """Exercise the embedded batch layout through the installed process guard."""
    import ast
    import io
    batch = (package/'BATCH.sh').read_text()
    lines = [line for line in batch.splitlines() if line.startswith('b=bytes.fromhex(')]
    if len(lines) != 1:
        raise ValueError('Bundle encoding differs')
    expression = ast.parse(lines[0]).body[0].value
    if (not isinstance(expression, ast.Call) or ast.unparse(expression.func) != 'bytes.fromhex'
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
    compare('Bundle descriptor differs',json.loads((package/'0.json').read_text()),json.loads((root/'0.json').read_text()))
    expected = (package/'a/6.py').read_bytes()
    compare('Bundled operator differs',hashlib.sha256(expected).hexdigest(),hashlib.sha256((root/'7.py').read_bytes()).hexdigest())
    from orchard_h10.common import template, sha
    _, _, results, transport, _ = template()
    pool = root/'wpool'
    token = json.loads((root/'0.json').read_text())['token']
    before = sha(root/'7.py')
    # This is the production job's call, including its guarded Popen spawn.
    receipt = results.write_test(str(pool), token)
    evidence = pool/token/'.wtest'
    compare('Write-test receipt differs',
            dict(bytes=transport.WRITE_TEST_BYTES, evidence_bytes=transport.WRITE_TEST_BYTES,
                 sha256=receipt.get('sha256'), charged=transport.WRITE_TEST_BYTES+32),
            dict(bytes=receipt.get('bytes'), evidence_bytes=evidence.stat().st_size,
                 sha256=sha(evidence), charged=int((pool/(token+'.0')).read_text())))
    vendor = Path(results.__file__).with_name('return_io.py')
    compare('Process guard did not exercise its write target',sha(vendor),sha(root/'6.py'))
    compare('Process guard changed bundled operator',before,sha(root/'7.py'))
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
    compare('Write test must precede operator dispatch',[True,['guard_installed','write_test']],[proof.get('passed'),proof.get('events')])
    evidence = root/'wpool'/proof['token']/'.wtest'
    from orchard_h10.common import template
    transport=template()[3]
    compare('Entry write-test evidence differs',
            dict(pool=str(root/'wpool'),bytes=transport.WRITE_TEST_BYTES,
                 evidence_bytes=transport.WRITE_TEST_BYTES,sha256=proof['write_test']['sha256'],
                 guard=proof['guard_target_sha256'],charged=transport.WRITE_TEST_BYTES+32),
            dict(pool=proof['pool'],bytes=proof['write_test']['bytes'],
                 evidence_bytes=evidence.stat().st_size,sha256=sha(evidence),
                 guard=sha(root/'6.py'),charged=int((root/'wpool'/(proof['token']+'.0')).read_text())))
    before = proof['operator_sha256_before']
    calls = []
    def checked(dispatched, *args, **kw):
        compare('Bootstrap did not dispatch bundled operator',[str(operator),str(root/'a/1.json')],dispatched[-2:])
        calls.append(list(dispatched))
        return original(dispatched, *args, **kw)
    # Import the exact bundled bootstrap without invoking production job.main.
    make_dispatch = runpy.run_path(str(root/'0.py'))['make_dispatch']
    make_dispatch(root, checked, before)(argv, **kwargs)
    compare('Dispatched operator changed',dict(calls=1,sha256=before),dict(calls=len(calls),sha256=sha(operator)))
    proof.update(operator_sha256_after=sha(operator), requested_argv=list(argv),
                 dispatched_argv=calls[0], events=proof['events']+['operator_dispatch'])
    return dict(**proof, entry_sequence_passed=True)


def unit_config(cfg):
    """Deadlines, threads and limits for the CPU real unit."""
    import time
    start=float(os.environ.get('SLURM_JOB_START_TIME',time.time()))
    seconds=int(cfg.get('budget_gpu_seconds',3000))
    end=min(start+seconds,float(os.environ.get('SLURM_JOB_END_TIME',start+seconds)))
    threads=len(os.sched_getaffinity(0))
    return dict(end=end-360,kill_at=end-330,allocation_end=end,threads=threads,
                slurm_cpus=os.environ.get('SLURM_CPUS_PER_TASK'),address_space=193273528320,
                guard_bytes=182536110080,estimates={'first_model': {'32': 325, '64': 985}, 'load': 420, 'prefill': 150, 'margin': 60})


def collect_unit(root, cfg, package):
    """Read the worker and operator receipts; never raises."""
    from orchard_h10.common import template
    J=template()[1]
    try:
        meta=J.physical(root,cfg['logical']+'/r/metadata')
        unit=json.loads((meta/'33.json').read_text()) if (meta/'33.json').exists() else dict(passed=False,status='absent')
        process=json.loads((meta/'34.json').read_text()) if (meta/'34.json').exists() else dict(returncode=None,stopped='absent')
        unit['process']=process
        unit['passed']=bool(unit.get('passed') is True and process.get('returncode')==0
                            and process.get('stopped') is None and process.get('memory',{}).get('over') is False)
    except Exception as error:
        unit=dict(passed=False,status='unreadable',error=(type(error).__name__+': '+str(error))[:2048])
    if not unit['passed'] and unit.get('status')!='absent':
        try:
            raw=json.dumps(unit)
            if len(raw)>100_000:unit={k:unit.get(k) for k in ('passed','status','failure','error','stages','admission','process','unit')};raw=json.dumps(unit)[:100_000]
            with (package/'a/31.json').open('w') as stream:stream.write(raw)
        except Exception:pass
    return unit


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',required=True)
    parser.add_argument('--sequence',required=True)
    parser.add_argument('--return-tar');parser.add_argument('--submerge')
    parser.add_argument('--results',required=True)
    args=parser.parse_args()
    job=os.environ.get('SLURM_JOB_ID','')
    if not job.isdigit():raise ValueError('Run on an allocated compute node')
    if not os.environ.get('USER'):raise KeyError('USER')
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
            if not entry.name.startswith('orchard_h10/') and entry.name!='j.py':continue
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
    destination=Path(args.results).resolve()
    results=root/'results';results.mkdir()
    with __import__('orchard_h10.e',fromlist=['capture']).capture(root/'22.json') as log:
        checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'0.json')],
                    env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    ready=json.loads(J.physical(root,cfg['logical']+'/d/READY.json').read_text())
    settings=json.loads(J.physical(root,cfg['logical']+'/d/settings.json').read_text())
    expected=dict(stage1_select_rule='null_argmax',perception_memo='off',
                  perception_memo_modules=['g3t'],perception_memo_verify_ids=[])
    compare('Prepared default settings differ',expected,{k:settings.get(k) for k in expected})
    run_cfg=dict(package=cfg['logical']+'/p',output=cfg['logical']+'/r',python=inputs['python'],
        export=cfg['logical']+'/d/e',binding=cfg['logical']+'/d/binding.json',
        export_pin=cfg['logical']+'/d/6.json',settings=cfg['logical']+'/d/settings.json',
        plan_sha256=cfg['plan_sha256'],inputs_sha256=canonical({k:v for k,v in inputs.items() if k!='resume'}),
        operator_sha256=sha(sequence),device='cpu',prefix=[],measure_memory=True)
    run_cfg['cpu_unit']=unit_config(cfg)
    write(dispatch/'1.json',dict(action=1,package=run_cfg['package'],config=run_cfg,rehearsal=True))
    try:
        with __import__('orchard_h10.e',fromlist=['capture']).capture(root/'22.json') as log:
            entry_sequence=dispatch_operator(root,bundle_guard,
                        J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'1.json')],checked_run,
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    finally:
        real=collect_unit(root,cfg,package)
    compare('CPU real unit passed',True,real['passed'])
    memory=json.loads(J.physical(root,cfg['logical']+'/r/metadata/MEMORY.json').read_text())
    write(results/'MEMORY.json',memory)
    write(results/'CPU.json',dict(real_unit=real,real_unit_passed=True,boot=json.loads(J.physical(root,cfg['logical']+'/r/metadata/25.json').read_text()),passed=True,entry_sequence_passed=True,entry_sequence=entry_sequence,bundle_guard_passed=True,bundle_guard=bundle_guard,memory=memory,plan=cfg['plan_sha256'],inputs=sha(package/'a/1.json'),
                                 operator_sha256=sha(sequence),
                                 payload=cfg['payload_sha256'],storage=proof,ready=ready,root=str(root)))
    destination.mkdir(parents=True,exist_ok=False)
    for name in ('CPU.json','MEMORY.json'):
        raw=(results/name).read_bytes()
        if len(raw)>400_000:raise ValueError('E73')
        (destination/name).write_bytes(raw)
    print('0')

if __name__=='__main__':
    try:main()
    except Exception as e:
        try:cpu_failure(e)
        except Exception as diagnostic_error:
            print("E89:"+type(diagnostic_error).__name__.encode().hex())
        import traceback
        if os.environ.get('SLURM_JOB_ID','').isdigit():traceback.print_exc()
        print('E40:'+type(e).__name__.encode().hex())
        raise SystemExit(1)
