from common import *
import subprocess,copy,sqlite3
from student_pilot.p3_provenance import file_pin
from student_pilot.r1_persisted import scope
from student_pilot.carrier_c1_run import identity
records=[]
for name in ('q','n','n_go','qd'):
 root=D/'census'/(name+'_clean');k=root/'sealed'
 raw=(root/'c5.json').read_bytes();value=J.load(root/'c5.json')
 value['streams']['pointing']['source_pins'][0]['count']+=1
 replace(root/'c5.json',json.dumps(value))
 p=subprocess.run([sys.executable,'-B','-s',str(k/'b/h.py'),str(root/'p'),str(root/'badsource.json')],capture_output=True,text=True,env={**os.environ,'SLURM_JOB_ID':'91'})
 assert p.returncode and 'R1_CENSUS_SOURCE_PINS_DIFFER:pointing' in p.stderr,p.stderr
 replace(root/'c5.json',raw)
 records.append(dict(kit=name,case='wrong_source',refusal='R1_CENSUS_SOURCE_PINS_DIFFER:pointing'))
# The final native Rows adapter must follow indices and mixture order, not enumerate database rows.
sys.path.insert(0,str(kit('qd')/'b'))
import cs
root=D/'census/qd_clean';cfg=J.load(root/'cfg.json');prep=J.load(cfg['preparation']['path'])
F=D/'mixed_census';(F/'p/q').mkdir(parents=True)
source=J.load(root/'p/q/ss.json')
clean=dict(qid='mixed-clean',dataset='scannet',scene='scene9999_00')
bad=dict(qid='not-selected',dataset='scannet',scene='scene0630_00')
def db(name,rows):
 p=F/name
 with sqlite3.connect(p) as con:
  con.execute('create table rows(i integer primary key,row text,target text)')
  for i,row in enumerate(rows):con.execute('insert into rows values(?,?,?)',(i,json.dumps(row),'{}'))
 return file_pin(p)
a=db('a.sqlite',[bad,dict(clean,qid='a')]);b=db('b.sqlite',[dict(clean,qid='b')])
pa=J.write(F/'a.json',dict(database=a,count=2));pb=J.write(F/'b.json',dict(database=b,count=1))
source['pose']=[dict(receipt=pa,population=a,count=2),dict(receipt=pb,population=b,count=1)]
cfg['streams']['pose']=J.write(F/'mix.json',dict(schema='c1-pose-mix-v1',sources=[dict(kind='rows',receipt=pa),dict(kind='rows',receipt=pb)]))
prep['depth']=dict(num_points_per_frame=1)
prep['streams']['pose']=dict(kind='mix',count=2,order=J.write(F/'order.json',[[1,0],[0,1]]),
 sources=[dict(kind='rows',database=a),dict(kind='rows',database=b)])
routing=db('routing.sqlite',[bad,dict(clean,qid='route')])
prep['streams']['routing']=dict(database=routing,count=1,indices=J.write(F/'ri.json',[1]))
cfg['preparation']=J.write(F/'prep.json',prep);J.write(F/'p/q/ss.json',source)
fake=F/'kit';(fake/'k').mkdir(parents=True);J.write(fake/'k/p.json',dict(n_root=str(F/'target')));J.write(fake/'k/a.json',dict(GO=False,discovery=True))
paths={v['sha256']:v['local_path'] for v in J.load(L/'work/build24m2c/UPLOADS_q.json')['files'] if v['opaque_name'].startswith('u/')}
paths.update({p.name:str(p) for p in (D/'u').iterdir()})
os.environ['SLURM_JOB_ID']='91'
with scope(paths):cs.publish(fake,F,cfg,'91')
report=J.load(F/'c5.json');assert report['status']=='PASS',report
assert report['streams']['pose']['result']['source_rows']==3 and report['streams']['pose']['result']['admitted_rows']==2
assert report['streams']['routing']['result']['admitted_rows']==1
with scope(paths):cs.verify(fake,F,cfg)
records.append(dict(case='native_pose_mixture_and_routing_indices',status='PASS',source_pose=3,admitted_pose=2,admitted_routing=1))
J.write(D/'BINDING_MORE_TESTS.json',dict(status='PASS',records=records))
print('Source-pin rejection, native pose mix and indexed routing PASS')
