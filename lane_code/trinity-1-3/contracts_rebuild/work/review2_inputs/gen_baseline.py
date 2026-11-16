import sys,json
T=sys.argv[1]; sys.path[:0]=[T,'/scratch/jjyeung/orch_n30/contracts_rebuild/work/tests_r5']
from generator_fixture_r4 import generate
out={k:generate(T,k) for k in ('landscape','nadir_positive')}
def clean(x):
    import numpy as np
    if isinstance(x,np.ndarray): return x.tolist()
    if isinstance(x,np.generic): return x.item()
    if isinstance(x,dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [clean(v) for v in x]
    return x
json.dump(clean(out),open(sys.argv[2],'w'))
