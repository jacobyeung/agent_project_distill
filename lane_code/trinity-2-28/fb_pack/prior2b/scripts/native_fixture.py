from common import *
import sqlite3
track(__file__);f=P.load(track(W/'work/fixture/FIXTURE.json'));root=W/'work/native_fixture';root.mkdir(exist_ok=True)
SCOPE='FIXTURE_ONLY_NOT_PRODUCTION'
def put(name,v):
 p=write('work/native_fixture/'+name,dict(v,scope=SCOPE));return P.file_pin(p)
streams={};receipts={};tables={}
for stream,count in f['stream_counts'].items():
 if stream=='vqa':database=f['vqa_database'];track(database['path'],database['sha256'])
 else:
  p=root/(stream+'.sqlite');assert not p.exists();con=sqlite3.connect(p)
  con.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT NOT NULL,target TEXT NOT NULL)')
  for i in range(count):
   row=dict(qid='NONPRODUCTION_FIXTURE_'+stream+'_'+str(i),question_type=stream,target='<think>Fixture source row.</think>0')
   con.execute('INSERT INTO rows VALUES(?,?,?)',(i,P.encoded(row),'{}'))
  con.commit();con.close();database=P.file_pin(p);track(p)
 receipts[stream]=put(stream+'_receipt.json',dict(schema='c1-routing-stream-v1' if stream=='routing' else 'c1-stream-v1',database=database,count=count,stream=stream,heldout_overlap=0))
 p=root/(stream+'_indices.json');p.write_text(P.encoded(list(range(count)))+'\n');tables[stream]=P.file_pin(p);track(p)
 streams[stream]=dict(receipt=receipts[stream],database=database,count=count,source_count=count,indices=tables[stream])
binding=f['binding'];training=dict(routing_slices='deferred_first_boundary',row_plan_sha256=P.digest(binding))
receipt=put('receipt.json',dict(schema='c1-preparation-v1',streams=streams,r2_sampling=binding,r1_training=training))
cfg=put('config.json',dict(preparation=receipt,streams=receipts,r2_sampling=binding,r1_training=training))
put('FIXTURE.json',dict(native_config=cfg,prepared_receipt=receipt,stream_receipts=receipts,offset_tables=tables,source_reconstruction=f['source_reconstruction']))
print('Native reader fixture ready',flush=True)
