import sys,json,shutil,torch
from pathlib import Path
T='/scratch/jjyeung/orch_n30/review_tree11/pkg/work/tree_r1'; sys.path.insert(0,T)
from student_pilot import carrier_c1_run as C
from student_pilot.p3_provenance import file_pin
from tests.test_carrier_c1 import fixture
W=Path(sys.argv[1]); out={}
def tryload(tag,art):
    fresh,_,_=fixture(4)
    try:
        C.load_artifact(fresh,file_pin(art)); out[tag]='LOADED'; return fresh
    except Exception as e:
        out[tag]=type(e).__name__+': '+str(e)[:160]
tryload('9fix_export',W/'legacy/artifact.json')
m=tryload('b11_export',W/'modern/artifact.json')
if m is not None:
    out['b11_loaded_threshold']=m.auxiliary_heads.heading.threshold_ratio.tolist()
t=W/sys.argv[2]
assert not t.exists()
shutil.copytree(W/'modern',t)
h=torch.load(t/'heads.pt',weights_only=True); h['depth_readout.stencil']=h['depth_readout.stencil']*2
torch.save(h,t/'heads.pt')
a=json.load(open(t/'artifact.json')); a['heads']=dict(path=str((t/'heads.pt').resolve()),sha256=a['heads']['sha256']); json.dump(a,open(t/'artifact.json','w'))
tryload('tampered_heads_old_sha',t/'artifact.json')
a['heads']=file_pin(t/'heads.pt'); json.dump(a,open(t/'artifact.json','w'))
m=tryload('tampered_heads_repinned',t/'artifact.json')
if m is not None: out['repinned_stencil_row0_used']=m.auxiliary_heads.depth_readout.stencil[0].tolist()
print(json.dumps(out,indent=1))
