"""Compare bounded eligible examples with P's sealed classifier."""
from pathlib import Path
import sys,json,sqlite3,importlib.util
L=Path(__file__).resolve().parents[2];B=L/'work/build15';T=L/'work/tree_r1';O=B/'proofs/mapping';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(T))
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r1_population import family
source=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/ext/r1_ops/work/snap_fac07052/work/tree/student_pilot/type_mix.py')
spec=importlib.util.spec_from_file_location('student_pilot._sealed_p_type_mix',source);p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
rename=dict(facing='facing_pairs',size='object_size',room='room_size',appearance='appearance_order',first_seen='first_seen_frame',box='box_3d',route='route_planning',camera_absolute_distance='camera_object_abs_distance',
    camera_obj_rel_dist_v1='camera_object_rel_distance_v1',camera_obj_rel_dist_v2='camera_object_rel_distance_v2',camera_obj_rel_dist_v3='camera_object_rel_distance_v3',
    obj_obj_relative_pos_lr='object_object_left_right',obj_obj_relative_pos_nf='object_object_near_far',obj_obj_relative_pos_ud='object_object_up_down')
cfg=load(B/'inputs/config.json');receipt=load(pinned(cfg['streams']['vqa']))
con=sqlite3.connect(pinned(receipt['database']).as_uri()+'?mode=ro',uri=True)
pop=load(B/'proofs/census/population/population.json');indices=load(B/'proofs/census/population/indices.json')['cells'];physical=load(B/'proofs/census/vqa_indices.json')
rows=[]
for c in load(pinned(cfg['r1_training']['mix']))['cells']:
    if c['stream']!='vqa':continue
    for i in indices[c['type']][:5]:
        row=json.loads(con.execute('SELECT row FROM rows WHERE i=?',(physical[i],)).fetchone()[0])
        old=p.family(row,'vqa');expected=rename.get(old,old);actual=family(row,'vqa')
        assert actual==expected==c['type'],(old,actual,c['type'])
        rows.append(dict(qid=row['qid'],question_type=row['question_type'],sealed_family=old,cell=actual))
con.close()
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',source=file_pin(source),rename=rename,examples=rows,
    scope='At most five eligible rows per VQA cell; no claims about unseen P size-selector settings or excluded traces.'),indent=2))
print('PASS mapping',len(rows))
