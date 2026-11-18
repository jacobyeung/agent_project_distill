"""Native composed-store reader and encoder, with synthetic RGB at the frame boundary."""
from pathlib import Path
import sys,os,json,sqlite3
from unittest.mock import patch
import numpy as np
L=Path(__file__).resolve().parents[2];B=L/'work/build13';T=L/'work/tree_r1';O=B/'proofs/encode';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(L/'work/n1fix2')];os.environ.update(R2_FIXTURES=str(L/'fixtures'),R2_PROOFS=str(O))
from monitor9 import Monitor
m=Monitor(T)
from student_pilot.p3_provenance import load,pinned,file_pin
from student_pilot.r1_routing import compose
from student_pilot.r1_population import Membership
from student_pilot.carrier_c1_run import Rows
from tests.test_r2_data_path import TinyProcessor
cfg=load(B/'inputs/config.json');old=load(B/'proofs/census/composed/receipt.json');membership=Membership(old['source_membership'])
sources={k:v['source'] for k,v in membership.sources.items()}
con=sqlite3.connect(pinned(old['database']).as_uri()+'?mode=ro',uri=True)
batches=[]
for k,p in sources.items():
    row=json.loads(con.execute("SELECT row FROM rows WHERE json_extract(row,'$.r1_source.family')=? LIMIT 1",(k,)).fetchone()[0])
    assert membership.cell(row,'routing')==k
    batches.append((k,p,[dict(row=row,target={})],file_pin(B/'proofs/census/slice_intake.json')))
con.close()
native=Path.open
def opened(p,mode='r',*a,**kw):return native(p,mode.replace('x','w') if p.is_relative_to(O) else mode,*a,**kw)
Path.open=opened
r=compose(file_pin(B/'proofs/builder/routing/receipt.json'),sources,batches,cfg,O/'composed')
assert r['count']==3,r
reader=Rows(dict(streams=dict(routing=dict(database=r['database'],count=r['count'])),
    r1_training=cfg['r1_training'],extent_receipt=cfg['extent_receipt'],frame_layout='duplicate'),TinyProcessor())
results=[]
with patch('student_pilot.pose_samples.load_frames',return_value=np.zeros((32,32,32,3),dtype=np.uint8)):
    for i in range(3):
        row,_=reader.row('routing',i);assert isinstance(row['routing']['events'],list)
        batch,target,audit=reader.get('routing',i)
        assert batch['input_ids'].shape==batch['labels'].shape
        assert (batch['labels']!=-100).any() and (batch['labels']==-100).any()
        results.append(dict(qid=row['qid'],family=row['r1_source']['family'],tokens=batch['input_ids'].shape[1],
                            trained_tokens=int((batch['labels']!=-100).sum()),audit=audit))
reader.close()
(O/'RESULT.json').write_text(json.dumps(dict(status='PASS',receipt=file_pin(O/'composed/receipt.json'),rows=results,
    standins='Synthetic 32-frame RGB arrays at pose_samples.load_frames and TinyProcessor at the pretrained processor boundary. Composition, native C1 row conversion, SQLite view, extent checks, Rows.row, Rows.get and routing.encode execute unchanged.'),indent=2))
m.save(O);print('PASS composed native encode')
