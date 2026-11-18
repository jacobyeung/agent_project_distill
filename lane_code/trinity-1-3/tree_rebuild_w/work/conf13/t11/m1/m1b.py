import sys,json
T='/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/pkg/work/tree_r1'; sys.path.insert(0,T)
from student_pilot import carrier_c1_run as C
from student_pilot.p3_provenance import file_pin
from tests.test_carrier_c1 import fixture
from pathlib import Path
W=Path('/scratch/jjyeung/orch_n30/tree_rebuild_w/work/conf13/t11/m1'); out={}
a=json.load(open(W/'legacy/artifact.json')); out['legacy_config_sha256']=a.get('config_sha256'); out['legacy_has_readout_config']='readout_config' in a
def tl(tag,cfg):
    m,_,_=fixture(4)
    try: C.load_artifact(m,file_pin(W/'legacy/artifact.json'),evaluation_config=cfg); out[tag]='LOADED'; return m
    except Exception as e: out[tag]=type(e).__name__+': '+str(e)[:160]
base=dict(base_identity='fixture',trace_program_version='3.13')
m=tl('legacy_with_export_config',base)
if m is not None:
    out['loaded_threshold']=m.auxiliary_heads.heading.threshold_ratio.tolist(); out['loaded_stencil_row0']=m.auxiliary_heads.depth_readout.stencil[0].tolist()
tl('legacy_threshold_mismatch',dict(base,heading_plane_min=0.31))
tl('legacy_no_threshold_identity',dict(base,contract_epoch=False))
tl('legacy_other_identity',dict(base,trace_program_version='3.14'))
print(json.dumps(out,indent=1)); (W/'M1B.json').write_text(json.dumps(out,indent=1))
