import sys, json, time
sys.dont_write_bytecode=True
L='/scratch/jjyeung/orch_n30/b04host3/b04_e2ehook'; T='/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449'
sys.path[:0]=[L,T]
import numpy as np
t0=time.time()
from e2e_reader import geometry as G
from e2e_reader.servers import ReadServers
from evalpath.run import score_item
R=L+'/work/n13/ret/native'
d=json.load(open(R+'/R1.json'))
U=[x for x in d['arms']['unflagged'] if x['question_type'].startswith('camera')]
x=U[0]; clip=x['perception']['clip']
z=np.load(R+'/geometry/'+clip+'.npz'); print({k:(z[k].shape,z[k].dtype) for k in z.files})
g=G.from_npz(R+'/geometry/'+clip+'.npz'); s=ReadServers(g)
c=x['decode']['calls'][0]; print(s.head(c['call']), '|', c['response'])
print(time.time()-t0)
