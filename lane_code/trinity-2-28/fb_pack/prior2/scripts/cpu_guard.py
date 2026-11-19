"""CPU-suite restrictions apply to parent processes and any imported worker entrypoint."""
import os,sys,tempfile,resource
from pathlib import Path

def install(workspace, name):
    workspace=Path(workspace).resolve();out=workspace/'work/cpu_guarded'/name
    out.mkdir(parents=True,exist_ok=True)
    for key in ('R2_PROOFS','LANE_TEST_OUTPUT','STUDENT_PILOT_TEST_OUTPUT','STUDENT_CONVERTER_TEST_OUTPUT',
                'CLEAN_VSI590K_TEST_ROOT','TMPDIR','XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR',
                'CONDA_PKGS_DIRS','TORCH_HOME','B2_TEST_OUTPUT','B9_TEST_OUTPUT','B11_TEST_OUTPUT'):
        p=out/key;p.mkdir(exist_ok=True);os.environ[key]=str(p)
    for key in ('R2_LANE_ROOT','S1_LANE_ROOT','CLEAN_VSI590K_WORKSPACE'):os.environ[key]=str(workspace)
    os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',
                      TRANSFORMERS_OFFLINE='1',S1_CPU_REHEARSAL='0',OMP_NUM_THREADS='16',
                      MKL_NUM_THREADS='16',OPENBLAS_NUM_THREADS='16')
    tempfile.tempdir=os.environ['TMPDIR'];sys.dont_write_bytecode=True
    resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
    import torch
    torch.set_num_threads(16)
    import multiprocessing.process
    def refuse_process(*args,**kwargs):raise PermissionError('TASK_RESTRICTION:multiprocessing.start')
    multiprocessing.process.BaseProcess.start=refuse_process
    def guard(event,args):
        if event in ('subprocess.Popen','os.system','os.posix_spawn','os.fork','socket.connect','socket.bind','os.kill','os.killpg'):
            raise PermissionError('TASK_RESTRICTION:'+event)
        if event in ('os.listdir','os.scandir'):
            p=os.path.realpath(str(args[0]))
            if p.startswith(('/home/','/data/','/data2/','/data3/')):raise PermissionError('TASK_NFS_RESTRICTION:'+p)
        if event=='open':
            p,mode,flags=args
            if isinstance(p,(str,bytes)):
                p=os.path.realpath(os.fsdecode(p))
                if p.startswith(('/home/','/data/','/data2/','/data3/')):raise PermissionError('TASK_NFS_RESTRICTION:'+p)
                if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC) and not (p.startswith(str(workspace)+'/') or p=='/dev/null'):
                    raise PermissionError('TASK_WRITE_RESTRICTION:'+p)
        if event in ('os.remove','os.rmdir'):raise PermissionError('TASK_NO_DELETE:'+str(args[0]))
        if event in ('os.mkdir','os.rename','os.symlink','os.link'):
            paths=args[:2] if event in ('os.rename','os.link') else args[1:2] if event=='os.symlink' else args[:1]
            for p in paths:
                if isinstance(p,(str,bytes)) and not os.path.abspath(os.fsdecode(p)).startswith(str(workspace)+'/'):
                    raise PermissionError('TASK_WRITE_RESTRICTION:'+str(p))
    sys.addaudithook(guard)
    return out
