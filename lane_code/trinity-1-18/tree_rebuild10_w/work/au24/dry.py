import importlib.util,json,gzip,sqlite3,copy,hashlib,sys
from pathlib import Path
A=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('au',A/'orchard/au.py');au=importlib.util.module_from_spec(spec);spec.loader.exec_module(au)
manifest=au.read(A/'orchard/k.json');work=A/'dry3';work.mkdir(exist_ok=True);out=work/'o';out.mkdir(exist_ok=True)
archive=Path('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24e/out/kit_qd/k/t_e047002134f979bd.tar')
au.extract_tree(archive,work/'k_C',manifest['trees']['C'])
indices=list(range(32));h='a'*64
maps=[dict(d='d1',s='a',i=i,sha256=h,path='/data2/k6tk/'+h[:2]+'/'+h+'.png') for i in indices]
with gzip.open(work/'k_m','wt') as f:
 for v in maps:f.write(json.dumps(v)+'\n')
with gzip.open(work/'k_p','wt') as f:json.dump({'v':{'a':{'g':'d1','raw_n':40}}},f)
(work/'k_a').write_text(json.dumps({'schema':'s1-fps-authority-v1','by_scene':{'d1/a':24.0}}))
raw=dict(qid='au_0',dataset='d1',scene='a',question_type='route_planning',answer='A',target='<think>\nThe turn is Turn Left.\n</think>\n\nA',student_input={'question':'Which way?', 'options':['A. Turn Left','B. Turn Right']},frames_pending={'d':'d1','s':'a','i':indices})
rows=[]
for i in range(8):
 r=copy.deepcopy(raw);r['qid']='au_'+str(i);rows.append(r)
rows[1]['answer']='Z'
rows[2]['frames_pending']['s']='b'
rows[3]['student_input']['fps']=30
rows[4]['target']='<think>\nOther text.\n</think>\n\nA'
rows[5]['target']='<think>\n\n</think>\n\nA'
rows[6]['student_input']['total_num_frames']=50
rows[7]['frames_pending']['i']=[0]
with gzip.open(work/'k_r','wt') as f:
 for r in rows:f.write(json.dumps(r)+'\n')
# All rows contribute FPS, including a conflicting scene and invalid values.
with sqlite3.connect(work/'k_l') as db:
 db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT)')
 for i,(scene,fps) in enumerate([('a',24),('b',24),('b',30),('c',True),('d',-1)]):
  row=dict(dataset='d1',scene=scene,student_input={'fps':fps},routing={'question_type':'au','category':'route'})
  db.execute('INSERT INTO rows VALUES(?,?)',(i,json.dumps(row)))
state={'pins':{},'evidence':{'fixture':True},'fps':au.census(work/'k_l',5,{'au:route':5})}
assert state['fps']['fps']['d1/b']=='conflicting_rates'
assert state['fps']['groups']=={'d1':[24,30]}
for key,name in [('frame_map','k_m'),('frame_plan','k_p'),('fps_authority','k_a'),('rows','k_r')]:
 state['pins'][key]={'path':str(work/name),'sha256':au.sha(work/name)}
au.dump(work/'k_0.json',state)
manifest['sources']['ROUTE_direct']['declared_rows']=8
au.dump(work/'k_d.json',manifest)
import subprocess
code=subprocess.run([sys.executable,'-I','-s','-B',str(A/'orchard/au.py'),'d',str(work),str(out),'C']).returncode
r=au.read(out/'AUDIT_TREE_C.json')
assert code==0,r
assert r['rows']==8 and r['deferred']==8 and r['passed']==0,r
assert r['steps']['direct_transform']['deferred']==2,r
assert r['steps']['frames.resolve']['deferred']==4,r
assert r['steps']['routing.direct_row']['deferred']==2,r
assert r['transform_changed_before_later_checks']==5 and r['transformed']==0,r
assert all(len(v)<=3 for v in r['examples'].values())
print(json.dumps({'fixture_rows':r['rows'],'deferred':r['deferred'],'reasons':r['reasons'],'peak_rss_kib':r['peak_rss_kib']}))
