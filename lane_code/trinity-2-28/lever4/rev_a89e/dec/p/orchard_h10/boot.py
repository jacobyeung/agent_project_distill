
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
"""Boot the real numeric worker before any model or capture staging."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def check(cfg):
    from orchard_h10.common import write, template
    from orchard_h10.e import exception
    config=cfg['config'];receipt=Path(config['output'])/'metadata/25.json'
    started=time.monotonic()
    value=dict(passed=False,bulk_bytes=0,python=sys.executable,cwd=os.getcwd(),
               plan=cfg['plan'],job=cfg['job'],modules=0,failed_module=None)
    try:
        from g.w import bind_reader_root
        bind_reader_root(Path(config['package'])/'b')
        template()
        from student_pilot.g3t_online import VENDOR, vendor_digest
        from student_pilot.tower_read import SOURCE_SHA256
        from student_pilot.c1r_ref import source_import
        if vendor_digest()!=SOURCE_SHA256:raise ValueError('E53')
        source_import(VENDOR)
        import importlib
        manifest=json.loads((Path(config['package'])/'g/3.json').read_text())
        for name in manifest['modules']:
            value['failed_module']=name
            importlib.import_module(name)
            value['modules']+=1
        for name,symbol in manifest['symbols']:
            value['failed_module']=name
            module=__import__(name,fromlist=[symbol])
            getattr(module,symbol)
        value.update(passed=True,failed_module=None)
    except BaseException as error:
        if value['failed_module'] is None:value['failed_module']=getattr(error,'name',None)
        exception(receipt.with_name('26.json'),error)
        raise
    finally:
        value['seconds']=time.monotonic()-started
        write(receipt,value)


def worker(cfg):
    from orchard_h10.runner import control, environment
    from orchard_h10.common import write, checked_run
    config=cfg['config'];root=control(config)
    request=dict(cfg,action=3,boot=True)
    write(root/'30.json',request)
    # Match the production operator: same prefix, interpreter, flags, relative
    # entry/config names, cache root, environment constructor and working dir.
    argv=[*config['prefix'],config['python'],'-B','-I','5.py','30.json']
    receipt=Path(config['output'])/'metadata/25.json'
    status=dict(worker_returncode=None,worker_signal=None)
    try:
        result=checked_run(argv,env=environment(config,os.environ.get('CUDA_VISIBLE_DEVICES',''),0),
                           cwd=root,stdout=sys.stdout,stderr=sys.stderr,check=False)
        status.update(worker_returncode=result.returncode,worker_signal=-result.returncode if result.returncode<0 else None)
        if result.returncode:raise subprocess.CalledProcessError(result.returncode,argv)
    finally:
        value=json.loads(receipt.read_text()) if receipt.exists() else {}
        value.update(status);write(receipt,value)


def launch(root,cfg,inputs,J,pre_bytes,stage_seconds):
    from orchard_h10.common import write, checked_run
    from orchard_h10.e import capture, exception
    physical=J.physical(root,cfg['logical']+'/r')
    metadata=physical/'metadata';metadata.mkdir(parents=True,exist_ok=True)
    receipt=metadata/'25.json'
    value=dict(passed=False,bulk_bytes=0,pre_bulk_bytes=pre_bytes,
               stage_seconds=stage_seconds,plan=cfg['plan_sha256'],job=os.environ['SLURM_JOB_ID'],
               child_returncode=None,child_signal=None,worker_returncode=None,worker_signal=None,failed_module=None)
    write(receipt,value)
    started=time.monotonic();accepted=False
    try:
        for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)
        dispatch=root/'a'
        (dispatch/'5.py').write_bytes((Path(__file__).parent/'entry.py').read_bytes())
        config=dict(package=cfg['logical']+'/p',output=cfg['logical']+'/r',python=inputs['python'],
                    cache_root=cfg['logical']+'/r/cache/0',prefix=['bash',inputs['policy']['vnice']])
        write(dispatch/'4.json',dict(action=4,config=config,package=config['package'],plan=cfg['plan_sha256'],job=os.environ['SLURM_JOB_ID']))
        env=J.environment(root)
        env={k:v for k,v in env.items() if 'sam' not in k.lower()}
        env.update(OMP_NUM_THREADS='16',MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16')
        with capture(metadata/'27.json') as log:
            child=checked_run(J.namespace(root)+[inputs['python'],'-B','-I',str(dispatch/'5.py'),str(dispatch/'4.json')],
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
            value.update(child_returncode=child.returncode,child_signal=-child.returncode if child.returncode<0 else None)
            if child.returncode:raise subprocess.CalledProcessError(child.returncode,child.args)
        result=json.loads(receipt.read_text())
        if not result.get('passed') or result.get('bulk_bytes')!=0 or result.get('plan')!=cfg['plan_sha256']:
            raise ValueError('E84')
        value.update(result);accepted=True
    except BaseException as error:
        exception(metadata/'28.json',error)
        # A CPU failure is returned by the common supervisor. Preserve the
        # worker traceback in its pipe even when the CPU root is private.
        for name in ('26.json','27.json'):
            path=metadata/name
            if path.exists():
                for line in json.loads(path.read_text()).get('lines',[]):print(line,file=sys.stderr)
        raise
    finally:
        if receipt.exists():
            saved=json.loads(receipt.read_text())
            # The worker writes the initial receipt before the launch exits.
            saved.pop('child_returncode',None);saved.pop('child_signal',None)
            value.update(saved)
        tail=metadata/'27.json'
        value['child_output']=json.loads(tail.read_text()) if tail.exists() else dict(lines=[],limit=200,width=2048)
        value.update(passed=accepted,pre_bulk_bytes=pre_bytes,stage_seconds=stage_seconds,
                     launch_seconds=time.monotonic()-started)
        value['pre_bulk_seconds']=value['stage_seconds']+value['launch_seconds']
        write(receipt,value)
        # The supervisor can retain this small receipt on CPU/bootstrap failure.
        write(Path('/project/community/jjyeung')/cfg['token']/'a/25.json',value)


def environment_archive(spec,root,S,retain_roots=('v','q'),retain_prefix=None):
    """Authenticate every part and materialize only the selected runtime members."""
    import hashlib
    class Stream:
        def __init__(self):
            self.parts=iter(spec['parts']);self.source=None;self.whole=hashlib.sha256();self.bytes=0
        def read(self,size):
            while True:
                if self.source is None:
                    self.part=next(self.parts,None)
                    if self.part is None:return b''
                    self.source=Path(self.part['path']).open('rb');self.hashed=hashlib.sha256();self.count=0
                data=self.source.read(size)
                if data:
                    self.count+=len(data);self.bytes+=len(data)
                    if self.count>self.part['bytes']:raise ValueError('E85')
                    self.hashed.update(data);self.whole.update(data);return data
                self.source.close();self.source=None
                if self.count!=self.part['bytes'] or self.hashed.hexdigest()!=self.part['sha256']:raise ValueError('E85')
        def close(self):
            if self.source is not None:self.source.close()
    stream=Stream()
    try:
        S.room(root,spec['expanded_bytes'])
        inventory=S.extract_stream(stream,root/spec['destination'],None,spec['expanded_bytes'],links=True,retain_roots=retain_roots,retain_prefix=retain_prefix)
        while stream.read(1024**2):pass
        if spec.get('sha256') is not None and stream.whole.hexdigest()!=spec['sha256']:raise ValueError('E85')
        return dict(bytes=stream.bytes,sha256=stream.whole.hexdigest(),extracted_bytes=sum(x['bytes'] for x in inventory.values()))
    finally:stream.close()


PYTHON_PREFIX='sj/uv-python/cpython-3.12.13-linux-x86_64-gnu'


def interpreter_archive(group,root,S):
    spec=dict(parts=[dict(path=p,bytes=n,sha256=h) for p,n,h in group],
              destination='.',expanded_bytes=sum(p[1] for p in group))
    return environment_archive(spec,root,S,retain_roots=None,retain_prefix=PYTHON_PREFIX)
