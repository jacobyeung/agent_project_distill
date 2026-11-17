from pathlib import Path
import json,sys
W=Path.cwd();O=W/'out';P=O/'src';sys.path[:0]=[str(O),str(P/'b'),str(P/'tree'),str(P)]
import torch
from e2e_reader import perception_memo as M
import tower_sequence as T
checks=[]
for dtype in (torch.float16,torch.bfloat16,torch.float32,torch.float64,torch.int32,torch.int64,torch.bool):
 value=torch.arange(12).reshape(3,4).t().to(dtype)
 if dtype.is_floating_point:value[0,0]=-0.;value[1,0]=float('nan')
 stored=M.store_value(value);got=M.restore_value(stored)
 assert stored.value.device.type=='cpu' and got.device==value.device and got.dtype==value.dtype and M.equal(value,got)
 got.fill_(0);assert M.equal(value,M.restore_value(stored))
 checks.append(dict(device=str(value.device),dtype=str(dtype),shape=list(value.shape),bit_identical=True))
result=dict(**T.memory_bound(),device_tests=checks,cuda_tested=False,production_measurement_available=False,
 bound_scope='G3T retained payload plus three transient capture copies, 1 MiB per capture for Python/allocator overhead, and a 64 GiB runtime allowance. This bounds memo retention; the runtime allowance is not a measured full-model peak RSS bound. SAM is fresh and retains no cross-read encoding.',
 production_gate='CPU helper checks the fixed G3T shapes against the allocation; neither it nor bootstrap requires a measured SAM encoding receipt.')
assert result['fits'] and result['g3t_capture_bytes_upper']==3335080
(O/'MEMORY_BOUND.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
