import os,sys,json,copy,tempfile
from pathlib import Path
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
sys.path[:0]=[str(Path(__file__).parent),str(Path(__file__).parent/'refit')]
import prooflib,gate,k1_pipeline as K,build_tables,k1_report
import bindings as B,rehearse
from boundaries import CPU
def proof():
 import torch
 from student_pilot.ground_profiles import load_geometry
 from student_pilot.scene_state import FrameMap
 torch.set_num_threads(1);root=Path(tempfile.mkdtemp(prefix='kit_',dir=prooflib.LANE/'work'))
 c,ex=rehearse.fixture(root/'input');c['gt_name_ids']={'chair':[1],'table':[2],'lamp':[3],'light':[3]}
 receipt=K.cache_capture(c,CPU(),root/'cache')
 raw,geo,checked=K.cached(c,root/'cache');assert receipt==checked
 with (root/'cache/parity_raw.jsonl').open() as f:raw_prompt_records=[json.loads(line) for line in f]
 assert len(raw_prompt_records)>=32 and raw_prompt_records[0]['frame_sha256']==c['dense_frames'][0]['sha256']
 features,g=build_tables.extract(c,raw,geo)
 rows,pairs=build_tables.label(c,features,g,K.gt_arrays(c),fixture=True)
 assert rows and all(r['y']==1 for r in rows)
 doubled=copy.deepcopy(features)
 first=copy.deepcopy(doubled['chair'][0]);first['candidate_id']+='-second';doubled['chair'].append(first)
 pair_rows,pair_table=build_tables.label(c,doubled,g,K.gt_arrays(c),fixture=True)
 assert len(pair_table)==1 and pair_table[0]['y']==1
 # The native exported NumPy format is exercised by the real constructor and response dispatcher.
 model=gate.ROOT/'leg_s1_tree/work/tree_s1_admissionfix_168872/student_pilot/assets'
 version=B.load(model/'s1_version.json')['ground_candidate_policy'];policy=model/version['weights']
 backend=K.native_backend(c,c['rows'][0],geo,raw,policy,root/'audit')
 native=B.perception.execute_calls(geo,backend,K.P.calls_for(c['rows'][0]));assert native['calls'][-1]['response']=='distance 0.96 m'
 inv=B.load(prooflib.LANE/'out/CAPTURES.json');train=next(x for x in inv['pilot'] if x['split']=='train');test=next(x for x in inv['pilot'] if x['split']=='heldout')
 data=[dict(id='t'+str(i),canonical=train['canonical'],type='object_abs_distance',gt_value=1.,pred=1.,label='trust') for i in range(8)]
 data.extend(dict(id='h'+str(i),canonical=test['canonical'],type='object_abs_distance',gt_value=float(i+1),pred=float(i+1),label='trust',printed_cues={'status':0,'spread':.1*i}) for i in range(8))
 met={'metrics':{'accept':{'refit':{'auc':.8,'top1_accept_accuracy':.8},'current':{'auc':.8,'top1_accept_accuracy':.8}}}}
 analysis=k1_report.report(data,inv,met);assert not analysis['kill_rows'] and not analysis['kill_refit']
 bad=copy.deepcopy(data)
 for r in bad[8:]:r['label']='excluded';r['pred']=None
 assert k1_report.report(bad,inv,met)['kill_rows']
 met['metrics']['accept']['refit']['auc']=.7;assert k1_report.report(data,inv,met)['kill_refit']
 return dict(fixture=str(root),unselected_cache=True,candidate_rows=len(rows),pair_rows=len(pair_table),raw_parity_records=len(raw_prompt_records),native_distance=native['calls'][-1]['response'],kill_rules_positive_and_negative=True,fixture_only=True)
if __name__=='__main__':raise SystemExit(not prooflib.run('KIT',proof))
