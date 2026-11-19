"""Apply the frozen K1-training kernel with the kit's audited conversion."""
from adapter import *
import room_kernel

def frozen():
 p=W/'configs/KERNEL_FROZEN.json'
 if not p.is_file():raise FileNotFoundError('MISSING '+str(p))
 record=read(p)
 if record.get('status')!='FROZEN' or record.get('selection_scope')!='K1 train only' or record.get('benchmark_selected') is not False:raise ValueError('kernel is not frozen on K1 train')
 if record['kernel_sha256']!=sha(W/'vendor/room_kernel.py'):raise ValueError('stale kernel implementation')
 room_kernel.configure(record['constants'])
 return record

def pipeline(path,dest,rule='R0'):
 if rule!='R0':raise ValueError('only the frozen R0 kernel is allowed')
 frozen()
 try:
  geo=convert(path,dest)
  result=room_kernel.from_points(**room.sample(geo,'predicted'))
  response=room_kernel.format_result(result)
  parsed=room_kernel.parse_response(response)
  return dict(area_m2=parsed['area_m2'],refusal=None,response=response,**{k:result[k] for k in ('floor_cells','supported_cells','floor_height_m')})
 except (ValueError,KeyError,FloatingPointError,np.linalg.LinAlgError) as e:
  return dict(area_m2=None,refusal=getattr(e,'code',str(e)),response=None)

def input_code():
 import adapter
 p=W/'configs/KERNEL_FROZEN.json'
 return {**adapter.input_code(),str(p):sha(p)}
