"""Execute the delivered batch Python with local filesystem bindings only."""
import io
import os
import pathlib
import runpy
import subprocess
import sys
import tarfile

mode,package,work,pool,token,case=sys.argv[1:]
OriginalPath=pathlib.PosixPath
shared=OriginalPath('/project/community/jjyeung')/token
remote_pool=OriginalPath('/project/community/jjyeung/okh7/ae71c903')

class LocalPath(pathlib.PosixPath):
    def __new__(cls,*parts):return object.__new__(cls)
    def __init__(self,*parts):
        path=OriginalPath(*parts)
        for before,after in [(shared,package),(remote_pool,pool),(OriginalPath('/tmp'),work)]:
            if path==before or before in path.parents:
                path=OriginalPath(after)/path.relative_to(before);break
        super().__init__(path)

pathlib.Path=LocalPath
if mode=='child':
    root=LocalPath(work)/('a'+os.environ['SLURM_JOB_ID']+token)
    if case.startswith('late_sink_'):
        # Publish an authenticated success with the delivered recovery modules,
        # then exit zero before the supervisor's sink cleanup fails.
        import json,types
        scope=runpy.run_path(str(LocalPath(package)/'a/29.py'))
        loaded={}
        for name,raw in scope['RECOVERY'].items():
            module=types.ModuleType(name);module.__file__=str(root/'15.py')
            sys.modules[name]=module
            exec(bytes.fromhex(raw),module.__dict__);loaded[name]=module
        loaded['j'].install()
        public=scope['PUBLIC'];returned_token=token+format(int(os.environ['SLURM_JOB_ID']),'08x')
        out=root/'success';out.mkdir();(out/'metadata').mkdir()
        for name,value in {
            'COMPLETE.json':dict(plan_sha256=public['plan_sha256'],synthetic=False),
            'metadata/RETURN_ID.json':dict(token=returned_token,job=os.environ['SLURM_JOB_ID']),
            'metadata/CAPTURE.json':dict(verified=True),
            'metadata/PARITY.json':dict(trusted=True)}.items():
            (out/name).write_text(json.dumps(value,indent=2))
        transport=loaded['return_io'];results=loaded['orchard_results']
        transport.operate('test',LocalPath(pool),returned_token)
        results.pool_operation=lambda action,pool,token,local=None,**kw:transport.operate(action,pool,token,local)
        def no_cloud(*args,**kwargs):raise RuntimeError('local cloud disabled')
        results.upload=no_cloud
        result=results.publish(out,LocalPath(pool),returned_token,public['plan_sha256'],0)
        dest=LocalPath(pool)/returned_token
        ex=json.loads((dest/'EXIT.json').read_bytes());receipt=json.loads((dest/'RETURN_RECEIPT.json').read_bytes())
        loaded['auth'].validate_exit(ex,dest/'result.tar.gz',public['plan_sha256'],returned_token)
        loaded['auth'].validate_receipt(receipt,ex,dest/'EXIT.json',dest/'result.tar.gz',public['plan_sha256'],returned_token)
        assert ex['status']=='COMPLETE' and ex['returncode']==0 and result['returned']
        (root/'success.json').write_text(json.dumps(ex,indent=2))
        print('successful child')
        raise SystemExit(0)
    if case=='first_line':
        entry=root/'0.py';entry.write_bytes(b"raise RuntimeError('injected first line')\n"+entry.read_bytes())
    elif case in ('clean','missing_env','oversize','supervisor_noise','boot_gpu','boot_cpu','boot_success'):
        # Run the actual job.main; substitute only Orchard mount metadata and
        # external bulk staging/transport, never the startup or environment code.
        sys.path.insert(0,str(root/'p'))
        with tarfile.open(LocalPath(package)/'0.tgz') as archive:
            for entry in archive:
                if entry.name.startswith('orchard_h10/') or entry.name=='j.py':
                    target=root/'p'/entry.name;target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(archive.extractfile(entry).read())
        import importlib,json
        importlib.invalidate_caches()
        from orchard_h10 import job
        S,J,R,I,A=job.template()
        J.Path=OriginalPath
        actual=J.storage_proof
        observed=J.active_mount(root)
        mount=f"{observed['mount_id']} 1 8:1 /job_tmp/173925 /tmp rw - ext4 /dev/sda rw"
        # Map the synthetic mount path to the real disk handle's mount ID.
        J.active_mount=lambda path:observed
        def admission(path,**kw):
            value=actual(OriginalPath('/tmp')/root.name,mountinfo=mount,**kw)
            (root/'18.json').write_text(json.dumps(value))
            return value
        J.storage_proof=admission
        R.pool_operation=lambda action,pool,token,local=None,**kw:I.operate(action,pool,token,local)
        def no_cloud(*args,**kwargs):raise RuntimeError('local cloud disabled')
        R.upload=no_cloud
        def staged(root,cfg,inputs,S,J):
            env=J.environment(root)
            assert os.environ['A_N']=='1' and os.environ['A_T']=='3000'
            (root/'17.json').write_text(json.dumps(dict(environment=env,real_job_main=True,filesystem='ext4')))
            if case=='oversize':
                out=J.physical(root,cfg['logical']+'/r');(out/'metadata/23').write_bytes(os.urandom(6_100_000))
            raise RuntimeError('external staging boundary')
        if case.startswith('boot_'):
            sys.path.insert(0,str(OriginalPath(__file__).parent))
            from boot_fixture import configure
            stage=job.stage
            def boot_stage(r,c,i,s,j):
                job.stage=stage
                return configure(job,r,LocalPath(package),c,i,s,j,case)
            job.stage=boot_stage
            if case=='boot_cpu':
                # Execute the delivered CPU route, including its stage call and
                # exception propagation. Substitute only mount/transport inputs.
                os.environ['CUDA_VISIBLE_DEVICES']=''
                import tempfile
                tempfile.mkdtemp=lambda **kwargs:str(root/'34')
                (root/'34').mkdir()
        else:job.stage=staged
        if case=='missing_env':os.environ.pop('USER',None)
    sys.argv=[str(root/'0.py'),str(root)]
    runpy.run_path(sys.argv[0],run_name='__main__')
else:
    original=subprocess.Popen
    def child(argv,**kwargs):
        assert argv[1:4]==['-I','-s','-B'] and argv[-2].endswith('/0.py')
        return original([sys.executable,'-I','-s','-B',__file__,'child',package,work,pool,token,case],**kwargs)
    subprocess.Popen=child
    source=(LocalPath(package)/'BATCH.sh').read_text().split("<<'A'\n",1)[1].rsplit('\nA',1)[0]
    if case in ('sink_start','sink_exit') or case.startswith('late_sink_'):
        # Inject failures only in the delivered child-output sink implementation.
        import ast
        lines=source.splitlines()
        for i,line in enumerate(lines):
            if not line.startswith('exec(bytes.fromhex('):continue
            blob=bytes.fromhex(ast.literal_eval(ast.parse(line).body[0].value.args[0].args[0]))
            text=blob.decode();first=text.splitlines()[0]
            recovery=ast.literal_eval(first.split('=',1)[1]);raw=bytes.fromhex(recovery['e']).decode()
            if case=='sink_start':raw=raw.replace('try:thread.start()',"try:raise RuntimeError('injected sink start')")
            elif case=='sink_exit':raw=raw.replace('block=os.read(read,8192)',"raise RuntimeError('injected sink exit')")
            elif case=='late_sink_drain':raw=raw.replace('if errors:raise errors[0]',"errors.append(OSError('injected late sink drain'))\n        if errors:raise errors[0]")
            elif case=='late_sink_timeout':raw=raw.replace("if thread.is_alive():raise RuntimeError('E80')","raise RuntimeError('E80 injected late sink timeout')")
            elif case=='late_sink_save':raw=raw.replace('def save(path, lines):',"def save(path, lines):\n    raise OSError('injected late sink save')")
            recovery['e']=raw.encode().hex();text=text.replace(first,'RECOVERY='+repr(recovery),1)
            lines[i]="exec(bytes.fromhex("+repr(text.encode().hex())+"))"
        source='\n'.join(lines)
    if case=='supervisor_noise':
        source="import os,resource\nassert resource.getrlimit(resource.RLIMIT_FSIZE)[0]==524288\nfor _ in range(4096):os.write(1,b'x'*8192);os.write(2,b'y'*8192)\n"+source
    if case=='archive':source=source.replace("r=Path('/tmp')", "b=b'injected damaged archive'\nr=Path('/tmp')")
    exec(compile(source,'BATCH.sh','exec'),{'__name__':'__main__'})
