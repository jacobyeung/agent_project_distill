"""Keep bootstrap failures readable through the authenticated production fetch."""
import collections
import hashlib
import io
import json
import os
import resource
from pathlib import Path, PurePosixPath
import signal
import subprocess
import sys
import tarfile
import time
import traceback
import types


def supervise(root, blob, failure=None):
    public=PUBLIC
    shared=Path('/project/community/jjyeung')/public['token']
    path=shared/'a/14.json'
    rc=1;loaded={};diag=None;supervisor_failed=False
    try:
        # Module loading is protected by the shell log/traps and this handler.
        for name,raw in RECOVERY.items():
            module=types.ModuleType(name);module.__file__=str(root/'15.py')
            sys.modules[name]=module
            exec(compile(bytes.fromhex(raw),module.__file__,'exec'),module.__dict__)
            loaded[name]=module
        codec=loaded['j'];codec.install()
        diag=loaded['e'];results=loaded['orchard_results'];transport=loaded['return_io']
        loaded['q'].install()
        if failure is not None:raise RuntimeError(failure)
        root.mkdir(mode=0o700)
        with tarfile.open(fileobj=io.BytesIO(blob)) as archive:
            for entry in archive:
                name=PurePosixPath(entry.name)
                if name.is_absolute() or '..' in name.parts or not entry.isfile():raise ValueError('E62')
                target=root/entry.name;target.parent.mkdir(parents=True,exist_ok=True)
                with archive.extractfile(entry) as source,target.open('xb') as output:output.write(source.read())
        with diag.capture(path) as log:
            def disk_worker():
                # Bulk files live on the admitted job disk. This child has only
                # pipe stdout/stderr; the supervisor and its sinks stay limited.
                hard=resource.getrlimit(resource.RLIMIT_FSIZE)[1]
                resource.setrlimit(resource.RLIMIT_FSIZE,(hard,hard))
            child=subprocess.Popen([sys.executable,'-I','-s','-B',str(root/'0.py'),str(root)],
                                   cwd=root,stdout=log,stderr=subprocess.STDOUT,preexec_fn=disk_worker)
            def forward(number,frame):
                if child.poll() is None:child.send_signal(number)
            old={number:signal.signal(number,forward)
                 for number in (signal.SIGUSR1,signal.SIGTERM,signal.SIGINT)}
            try:rc=child.wait()
            finally:
                for number,handler in old.items():signal.signal(number,handler)
    except Exception as error:
        rc=1;supervisor_failed=True
        failure_lines=collections.deque(maxlen=200)
        for block in traceback.TracebackException.from_exception(error).format(chain=True):
            failure_lines.extend(line[-2048:] for line in block.splitlines())
        if diag is not None:
            try:diag.exception(path,error)
            except Exception:
                try:
                    root.mkdir(mode=0o700,exist_ok=True)
                    path=root/'14.json';diag.exception(path,error)
                except Exception:pass
        else:
            traceback.print_exc()
            return rc
    if rc==0:return 0
    try:
        end=min(time.time()+60,float(os.environ.get('SLURM_JOB_END_TIME',time.time()+62))-2)
        def expired(*args):raise TimeoutError('E63')
        signal.signal(signal.SIGALRM,expired)
        signal.setitimer(signal.ITIMER_REAL,max(.001,end-time.time()))
        job=os.environ['SLURM_JOB_ID'];token=public['token']+format(int(job),'08x')
        pool=Path(POOL);dest=pool/token
        if (dest/'RETURN_RECEIPT.json').exists():
            try:
                auth=loaded['auth'];ex=json.loads((dest/'EXIT.json').read_text())
                receipt=json.loads((dest/'RETURN_RECEIPT.json').read_text())
                auth.validate_exit(ex,dest/'result.tar.gz',public['plan_sha256'],token)
                auth.validate_receipt(receipt,ex,dest/'EXIT.json',dest/'result.tar.gz',public['plan_sha256'],token)
                if str(ex['job'])!=job:raise ValueError('E64')
                if not supervisor_failed and ex['status']=='FAILED' and ex['returncode']!=0:return rc
            except (ValueError,KeyError,OSError):pass
        if not dest.exists():transport.operate('test',pool,token)
        root.mkdir(mode=0o700,exist_ok=True)
        out=root/'15';out.mkdir(mode=0o700)
        (out/'metadata').mkdir()
        def write(name,value):
            (out/name).write_bytes(codec.pack(codec.wire_dumps(value)))
        write('FAILED.json',dict(error='E65',returncode=rc))
        write('metadata/RETURN_ID.json',dict(token=token,job=job))
        write('metadata/CAPTURE.json',dict(verified=False,uploaded=False,items=0,error='E65'))
        write('metadata/PARITY.json',dict(trusted=False,items=0,expected=60,failure='E65'))
        boot=shared/'a/25.json'
        if boot.exists():
            value=json.loads(boot.read_bytes())
            if value.get('job')==job and value.get('plan')==public['plan_sha256']:
                write('metadata/25.json',value)
                write('metadata/27.json',value.get('child_output',dict(lines=[],limit=200,width=2048)))
        compared=shared/'a/30.json'
        if compared.exists() and compared.stat().st_size<=150000:
            value=json.loads(compared.read_bytes())
            if value.get('job')==job and value.get('plan')==public['plan_sha256']:
                write('metadata/30.json',value)
        if supervisor_failed:
            value=dict(lines=list(failure_lines),limit=200,width=2048)
            while len(codec.pack(codec.wire_dumps(value)))>262144:value['lines']=value['lines'][1:]
            write('metadata/14.json',value)
        elif path.exists():(out/'metadata/14.json').write_bytes(path.read_bytes())
        else:write('metadata/14.json',dict(lines=['E65'],limit=200,width=2048))
        results.pool_operation=lambda action,pool,token,local=None,**kw:transport.operate(action,pool,token,local)
        def no_cloud(*args,**kwargs):raise RuntimeError('E66')
        results.upload=no_cloud
        returned=results.publish(out,pool,token,public['plan_sha256'],rc)
        if not returned['returned']:raise ValueError('E67')
    except Exception as error:
        diag.exception(shared/'a/16.json',error)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
    return rc
