import os, sys, json, resource, traceback, copy
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS, (15 << 30, 15 << 30))
C=Path.cwd(); B=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w'); T=B/'w24j/work/tree_r1'
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TMPDIR=str(C))
sys.path[:0]=[str(T),str(B/'w24j/out/kit_n_go/b')]
def audit(e,a):
    if e in ('os.remove','os.rmdir','subprocess.Popen','os.system','socket.connect'): raise RuntimeError('AUDIT_FORBIDDEN:'+e)
    if e=='open' and isinstance(a[0],str) and a[0].startswith(('/home/','/data/','/data2/','/data3/','/project/','/lustre/','/scratch/fsw/','/tmp/q_')): raise FileNotFoundError('OFFLINE_UNAVAILABLE:'+a[0])
sys.addaudithook(audit)
from student_pilot import r1_handover, r1_persisted, r2_grammar, trace_version, r1_coverage, r1_training, extent_receipt, r1_components, r1_rooms
from trace_format.contracts import heading_plane_min, contract_epoch
import pl
n=json.loads((C/'n_go_c.json').read_text()); p=json.loads((B/'inputs/p_configs/cprime_31abe087.json').read_text()); idx=json.loads((C/'source_asset_index.json').read_text())
out=[]
def check(name,fn):
    try:
        with r1_persisted.scope(idx): value=fn()
        row=dict(name=name,status='PASS',result=value)
    except Exception as e: row=dict(name=name,status='ERROR',exception=type(e).__name__,output=str(e),traceback=traceback.format_exc())
    out.append(row); print(name,row['status'],str(row.get('output',row.get('result')))[:700],flush=True)
check('handover_min_pixels_only',lambda:r1_handover.compare_configs(p,dict(n,min_pixels=16384),metadata=[n['r1_training']['p_run']['preparation']],replicas=idx))
check('trace_version_metadata',lambda:trace_version.metadata(n))
check('shared_grammar_digest',r2_grammar.check_shared)
check('deferred_without_reading_row_sources',lambda:r1_coverage.deferred(n,read_pins=False))
check('extent_receipt_schema',lambda:extent_receipt.Extents(n['extent_receipt']).receipt.get('schema'))
check('deferred_component_records',lambda:r1_components.deferred(n))
check('room_authority_metadata',lambda:dict(k1=len(r1_rooms.Rooms(n['r1_training']['room_authority']).k1)))
check('launch_routing_selection_pin',lambda:pl.selection_pin(B/'w24j/out/kit_n_go'))
Path('supplemental_results.json').write_text(json.dumps(out,indent=2,default=str)+'\n')
