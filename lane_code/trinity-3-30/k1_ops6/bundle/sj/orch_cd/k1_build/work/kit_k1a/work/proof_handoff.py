import os,sys,json,copy,tempfile,ast
from pathlib import Path
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
sys.path[:0]=[str(Path(__file__).parent),str(Path(__file__).parent/'refit')]
import gate,prooflib,render,k1_report,k1_pipeline as K,build_tables
import bindings as B
def proof():
 from student_pilot.ground_profiles import load_geometry
 from student_pilot.scene_state import FrameMap
 # Replay the real fixture output; no producer or reader return is mocked.
 p4=B.load(prooflib.LANE/'out/P4_RESULT.json');root=Path(p4['fixture']);c=B.load(root/'cache/COMPLETE.json')
 kit=B.load(prooflib.LANE/'out/KIT_RESULT.json');src=Path(kit['fixture'])
 # Reconstruct only manifest metadata from the retained real producer's input pins.
 pins=[dict(path=str(src/'input'/f'f{i:03}.png'),sha256=gate.sha(src/'input'/f'f{i:03}.png'),index=i) for i in range(64)]
 import numpy as np
 slots=np.linspace(0,63,32).astype(int).tolist();cap=dict(canonical='synthetic/room',dense_frames=pins,anchor_slots=slots,anchor_indices=[pins[s]['index'] for s in slots],gt_name_ids={'chair':[1],'table':[2],'lamp':[3]})
 raw=B.load(src/'cache/candidates.json');geo=load_geometry(src/'cache/geometry.npz',FrameMap(tuple(cap['anchor_indices'])),'tower_scaled')
 features,g=build_tables.extract(cap,raw,geo);features['chair'].append(copy.deepcopy(features['chair'][0]));features['chair'][-1]['candidate_id']+='-second'
 with np.load(src/'input/gt.npz',allow_pickle=False) as z:gt={k:z[k] for k in z.files}
 rows,pairs=build_tables.label(cap,features,g,gt,fixture=True);assert len(pairs)==1 and pairs[0]['y']==1
 results=B.load(root/'cache/responses.json');failure=results[1]
 excluded=render.render(dict(id='no_visual_trace',type='object_abs_distance',gt_value=2.),failure,cap,expected_calls_sha256=B.digest(failure['calls']),backend_hashes={'producer':'a'*64},fixture=True)
 assert excluded['label']=='excluded' and 'reviewed' in excluded['reason']
 manifest=B.load(prooflib.LANE/'out/K1_MANIFEST.template.json')
 try:K.check_manifest(manifest)
 except ValueError as e:assert 'not staged' in str(e)
 else:raise AssertionError('Unstaged plan passed preflight')
 # A held-out answer mutation cannot change the constant fit population.
 inv=B.load(prooflib.LANE/'out/CAPTURES.json');tr=next(c for c in inv['pilot'] if c['split']=='train')['canonical'];te=next(c for c in inv['pilot'] if c['split']=='heldout')['canonical']
 data=[dict(id='train',canonical=tr,type='object_abs_distance',gt_value=2.,pred=2.,label='trust'),dict(id='heldout',canonical=te,type='object_abs_distance',gt_value=3.,pred=3.,label='trust')]
 fit={'metrics':{'accept':{'current':dict(auc=.8,top1_accept_accuracy=.8),'refit':dict(auc=.8,top1_accept_accuracy=.8)}}}
 before=k1_report.report(data,inv,fit)['train_constant'];data[1]['gt_value']=999.;assert k1_report.report(data,inv,fit)['train_constant']==before
 assert k1_report.report(data,inv,fit,['train','heldout'])['complete_row_denominator_checked']
 try:k1_report.report(data[:1],inv,fit,['train','heldout'])
 except ValueError:pass
 else:raise AssertionError('Incomplete outcome denominator passed')
 cues=K.printed_cues(dict(calls=[dict(call='<ground obj="chair" mode="box">',response='chair: frames 1,2; size 1.00 x 1.00 x 1.00 m'),dict(call='<ground obj="table" mode="box">',response='table: frames 1')]))
 assert cues['missing_size']==1 and cues['low_frames']==1
 for path in (prooflib.LANE/'work').rglob('*.py'):ast.parse(path.read_text())
 return dict(pair_builder_rows=len(pairs),missing_fallback_evidence_excluded=True,unstaged_plan_refused=True,heldout_constant_leakage_refused=True,incomplete_denominator_refused=True,syntax_pass=True)
if __name__=='__main__':raise SystemExit(not prooflib.run('HANDOFF',proof))
