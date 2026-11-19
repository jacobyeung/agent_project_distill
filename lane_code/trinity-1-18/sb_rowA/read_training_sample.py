"""Factor repeated clip fields for a lossless manual read of the complete READ30 rows."""
from camera_contract import *
import re,copy
pin(__file__);pin(OUT/'READ30.md')
rows=[json.loads(s) for s in re.findall(r'```json\n([^\n]+)\n```',(OUT/'READ30.md').read_text())]
assert len(rows)==30
blocks={};views=[]
fields=[('student_input','frames'),('student_input','frame_indices'),('student_input','timestamps'),('routing','gt_pose9'),('routing','gt_up')]
for row in rows:
 view=copy.deepcopy(row)
 for a,b in fields:
  data=view[a][b];key=dh(data)[:16];blocks[key]=data;view[a][b]={'shared_block':key}
 rebuilt=copy.deepcopy(view)
 for a,b in fields:rebuilt[a][b]=blocks[view[a][b]['shared_block']]
 assert rebuilt==row
 views.append(view)
(OUT/'READ30_SHARED.md').write_text('# Shared clip fields (lossless factorization)\n\n'+'\n\n'.join(f'## {key}\n\n```json\n{enc(value)}\n```' for key,value in blocks.items())+'\n')
(OUT/'READ30_UNIQUE.md').write_text('# Complete rows with references to shared clip fields\n\n'+'\n\n'.join(f'## {i+1}\n\n```json\n{enc(v)}\n```' for i,v in enumerate(views))+'\n')
print('rows',len(rows),'shared blocks',len(blocks),'canonical scenes',len({r['routing']['canonical'] for r in rows}))
