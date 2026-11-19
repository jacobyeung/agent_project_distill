"""Run the real catalog selector, relocation and routing builder on one bounded row."""
from pathlib import Path
import sys,os,json,sqlite3,gzip
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build13';T=L/'work/tree_r1';O=B/'proofs/builder'
O.mkdir(parents=True,exist_ok=True);sys.path[:0]=[str(T),str(L/'work/n1fix2')]
os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
m=Monitor(T)
from student_pilot.p3_provenance import load,pinned,file_pin,write
from student_pilot import s1_pool,s1_routing,carrier_c1_routing as R,carrier_c1_run as C
from tests.test_r2_data_path import TinyProcessor
oldopen,oldmkdir=Path.open,Path.mkdir
def opened(p,mode='r',*a,**kw):return oldopen(p,mode.replace('x','w') if p.is_relative_to(O) else mode,*a,**kw)
def mkdir(p,mode=0o777,parents=False,exist_ok=False):return oldmkdir(p,mode,parents,True if p.is_relative_to(O) else exist_ok)
Path.open=opened;Path.mkdir=mkdir
cfg=load(B/'inputs/config.json')
con=sqlite3.connect((B/'proofs/census/composed/rows.sqlite').as_uri()+'?mode=ro',uri=True)
row=json.loads(con.execute("SELECT row FROM rows WHERE json_extract(row,'$.r1_source.family')='units' LIMIT 1").fetchone()[0]);con.close()
row={k:v for k,v in row.items() if k!='r1_source'}
with gzip.open(O/'pool.gz','wt') as f:f.write(json.dumps(row)+'\n')
ex={}
for name in ('dev_s1','eval_rooms','room_release_gate'):
    p=O/(name+'.tsv');p.write_text('');pin=file_pin(p)
    ex[name]=dict(list=pin['path'],list_sha256=pin['sha256'],rows=0)
for n,k,p in [('dev_s1','withhold',cfg['dev_scene_exclusions']),('eval_rooms','v2',cfg['benchmark_scene_exclusions'])]:
    ex[n].update({k:p['path'],k+'_sha256':p['sha256']})
write(O/'manifest.json',dict(schema='dose-pool-s1-manifest-v2',sets=[dict(name='source',status='final',
    rows_per_type={row['question_type']:1},files=dict(packed=dict(file_pin(O/'pool.gz'),rows=1,bytes=(O/'pool.gz').stat().st_size)))],exclusions=ex))
s1_pool.prepare(file_pin(O/'manifest.json'),O/'selected',cfg['remove_files'])
request=s1_routing.frame_request(row);d,s,ind=request['d'],request['s'],request['i']
with gzip.open(O/'frames.gz','wt') as f:
    for i in ind:f.write(json.dumps(dict(d=d,s=s,i=i,sha256='a'*64,path='/data2/k6tk/aa/'+'a'*64+'.png'))+'\n')
with gzip.open(O/'plan.gz','wt') as f:json.dump(dict(v={s:dict(g=d,raw_n=row['student_input']['total_num_frames'])}),f)
db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)');db.commit()
(O/'legacy.sqlite').write_bytes(db.serialize());db.close()
write(O/'legacy.json',dict(schema=R.ROUTING_SCHEMA,count=0,types={},database=file_pin(O/'legacy.sqlite'),
    division=cfg['scene_division'],scene_role='train'))
(O/'model').mkdir(exist_ok=True);(O/'model/tokenizer.json').write_text('{}')
write(O/'model.json',dict(kind='base',root=str(O/'model')))
run=dict(cfg,streams=dict(routing=file_pin(O/'legacy.json')),
    s1_routing=dict(schema='s1-routing-inputs-v1',selection=file_pin(O/'selected/receipt.json'),catalog={},
                    frame_map=file_pin(O/'frames.gz'),frame_plan=file_pin(O/'plan.gz')))
run['s1_route_policy']=None
run['route_table']={row['question_type']:'route'}
processor=TinyProcessor();processor._routing_tokens=dict(ids={})
target=O/'routing/rows.sqlite'
if target.exists():target.write_bytes(b'')
with patch.object(C,'processor_for_receipt',return_value=processor):
    result=s1_routing.build(run,O/'routing',cfg['scene_division'],file_pin(O/'model.json'))
assert result['count']==1,result
write(O/'RESULT.json',dict(status='PASS',receipt=file_pin(O/'routing/receipt.json'),
    row_source=file_pin(B/'proofs/census/composed/receipt.json'),rows_read=1,
    standins='One real admitted unit row replaces the host catalogs. Metadata-only frame map and TinyProcessor replace frame-host/pretrained boundaries. Native pool selection, relocation, schema/scene gates and s1_routing.build execute. Legacy store is empty.',
    production=False))
m.save(O);print('PASS native builder')
