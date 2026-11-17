from pathlib import Path
import json,sys
W=Path.cwd();O=W/'out';P=O/'src';sys.path[:0]=[str(O),str(P/'b'),str(P/'tree'),str(P)]
import torch,numpy as np
from e2e_reader import perception_memo as M
import tower_sequence as T
# A one-frame allocation measures the implementation's retained tensor payload.
# It is a shape sensitivity calculation, not a claim about absent SAM weights.
shapes=[('one_level_fp32',[(1,256,72,72)]),('three_levels_fp32',[(1,256,n,n) for n in (288,144,72)])]
rows=[]
for name,levels in shapes:
 value=dict(backbone_fpn=[torch.empty(s,dtype=torch.float32) for s in levels],vision_pos_enc=[torch.empty(s,dtype=torch.float32) for s in levels])
 measured=M.held_bytes(value);report=T.memory_bound(measured)
 rows.append(dict(name=name,shapes=levels,measured_tensor_payload_bytes=measured,**report))
assert rows[0]['fits'] and not rows[1]['fits']
# Every device and dtype supported in this CPU workspace retains exact payload.
checks=[]
for dtype in (torch.float16,torch.bfloat16,torch.float32,torch.float64,torch.int32,torch.int64,torch.bool):
 value=torch.arange(12).reshape(3,4).t().to(dtype)
 if dtype.is_floating_point:value[0,0]=-0.;value[1,0]=float('nan')
 stored=M.store_value(value);got=M.restore_value(stored)
 assert stored.value.device.type=='cpu' and got.device==value.device and got.dtype==value.dtype and M.equal(value,got)
 got.fill_(0);assert M.equal(value,M.restore_value(stored))
 checks.append(dict(device=str(value.device),dtype=str(dtype),shape=list(value.shape),bit_identical=True))
result=dict(production_measurement_available=False,reason='Pinned SAM source and weights are absent from the authorized local inputs; no CPU or GPU restore ran.',
 device_tests=checks,cuda_tested=False,shape_sensitivity=rows,
 production_gate='a/5.py executes tower_sequence.memory_probe on one authenticated frame with real SAM CPU float32 weights. It saves MEMORY.json and refuses an upper bound over 200 GiB.',
 bound_scope='Memo plus three transient capture copies, 1 MiB per capture Python/allocator allowance, and 64 GiB runtime allowance. Runtime allowance is a planning allowance, not a measured full-model RSS bound.',
 max_sam_bytes_per_frame_to_fit=(200*1024**3-64*1024**3)//87//32-(T.memory_bound(0)['g3t_capture_bytes_upper']+1024**2)//32)
(O/'MEMORY_BOUND.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
