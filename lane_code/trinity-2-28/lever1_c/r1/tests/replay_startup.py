"""Replay the exact old bootstrap with a relocated package and minimal allocation."""
import os
import pathlib
import runpy
import sys
import time
import traceback

root = pathlib.Path(__file__).resolve().parents[1]/'replay_173925/a173925a784b94c2e6af'
OriginalPath = pathlib.PosixPath
shared = OriginalPath('/project/community/jjyeung/a784b94c2e6af')

class LocalPath(pathlib.PosixPath):
    def __new__(cls, *parts):
        return object.__new__(cls)
    def __init__(self, *parts):
        path = OriginalPath(*parts)
        if path == shared or shared in path.parents:
            path = root/'package'/path.relative_to(shared)
        super().__init__(path)

pathlib.Path = LocalPath
os.environ.clear()
os.environ.update(PATH='/usr/bin:/bin', USER='jjyeung', SLURM_JOB_ID='173925',
                  SLURM_JOB_PARTITION='preempt', SLURM_CPUS_PER_TASK='16',
                  SLURM_MEM_PER_NODE='204800', CUDA_VISIBLE_DEVICES='0',
                  SLURM_JOB_START_TIME=str(int(time.time())),
                  SLURM_JOB_END_TIME=str(int(time.time())+3000))
sys.argv=[str(root/'0.py'),str(root)]
try:
    runpy.run_path(sys.argv[0],run_name='__main__')
except Exception:
    traceback.print_exc()
    raise SystemExit(1)
