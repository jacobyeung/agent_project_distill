"""Retain numbered installed-source excerpts supporting the review fixes."""
from pathlib import Path
import hashlib
ROOT=Path(__file__).resolve().parents[1]
ENV=Path('/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages')
files={
 'torch/autograd/grad_mode.py':[(312,331)],
 'torch/include/ATen/ParallelOpenMP.h':[(16,48)],
 'torch/include/ATen/Parallel.h':[(10,25)],
 'torch/include/torch/csrc/Exceptions.h':[(344,399)],
 'torchgen/api/python.py':[(1095,1114)],
 'torch/include/torch/csrc/autograd/engine.h':[(203,232),(245,278)],
 'torch/include/torch/csrc/distributed/c10d/ProcessGroupNCCL.hpp':[(1055,1070),(1360,1384)],
 'torch/distributed/fsdp/_runtime_utils.py':[(240,274),(277,309),(748,778),(831,858),(1084,1108)],
 'torch/distributed/run.py':[(849,861)],
 'torch/_torch_docs.py':[(9815,9825)],
 'torch/cuda/streams.py':[(176,245)],
}
output=[]
for relative,ranges in files.items():
 path=ENV/relative;payload=path.read_bytes();lines=payload.decode().splitlines()
 output.append(f'FILE: {path}\nSHA256: {hashlib.sha256(payload).hexdigest()}')
 for first,last in ranges:
  output.extend(f'{i}: {lines[i-1]}' for i in range(first,last+1))
(ROOT/'out/evidence/review1_framework_sources.txt').write_text('\n'.join(output)+'\n')
print(f'SOURCE_AUDIT_PASS: {len(files)} installed source files; numbered excerpts and SHA256 retained')
