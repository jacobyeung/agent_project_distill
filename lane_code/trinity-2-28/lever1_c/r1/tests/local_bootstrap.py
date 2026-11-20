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
    if case=='first_line':
        entry=root/'0.py';entry.write_bytes(b"raise RuntimeError('injected first line')\n"+entry.read_bytes())
    elif case in ('clean','missing_env','oversize','supervisor_noise'):
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
        job.stage=staged
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
    if case=='supervisor_noise':
        source="import os,resource\nassert resource.getrlimit(resource.RLIMIT_FSIZE)[0]==524288\nfor _ in range(4096):os.write(1,b'x'*8192);os.write(2,b'y'*8192)\n"+source
    if case=='archive':source=source.replace("r=Path('/tmp')", "b=b'injected damaged archive'\nr=Path('/tmp')")
    exec(compile(source,'BATCH.sh','exec'),{'__name__':'__main__'})
