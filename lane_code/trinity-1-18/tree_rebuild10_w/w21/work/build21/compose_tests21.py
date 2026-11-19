from pathlib import Path
from unittest.mock import patch
from contextlib import ExitStack
import os,json,sqlite3,unittest
from student_pilot import r1_routing as R,r1_coverage as C
from student_pilot.p3_provenance import load,file_pin
from tests.test_r2_data_path import manifest
L=Path(__file__).resolve().parents[2];B=L/'work/build21';O=B/'proofs/compose'
class Compose21(unittest.TestCase):
 def test_five_sources_through_native_producers(self):
  O.mkdir(parents=True,exist_ok=True)
  cfg=load(B/'proofs/capacity/400/request_config.json')
  cfg['r1_training']['wording_exclusion']=file_pin(L.parent/'ext/v2h/SPLIT_V2.json')
  original=Path.open
  def retained(path,mode='r',*a,**kw):return original(path,mode.replace('x','w') if path.is_relative_to(O) else mode,*a,**kw)
  with patch.object(Path,'open',retained):
   sources={};manifests={};catalog={}
   for kind in C.source_names(dict.fromkeys(C.PINS)):
    mp=manifest(O/kind,[],'routing',kind);value=load(mp)
    sources[kind]={'source':value['rows']};manifests[kind]=file_pin(mp);catalog[kind]=dict(source=value['rows'],qids=[])
   def put(name,value):
    p=O/name;p.write_text(json.dumps(value));return file_pin(p)
   cfg['r1_training'].update(row_sources=put('sources.json',sources),routing_inputs=manifests,
    source_membership=put('catalog.json',dict(schema='r1-source-catalog-v1',sources=catalog)))
   db=sqlite3.connect(':memory:');db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
   (O/'base.sqlite').write_bytes(db.serialize());db.close()
   from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
   base=put('base.json',dict(schema=ROUTING_SCHEMA,scene_role='train',heldout_overlap=0,database=file_pin(O/'base.sqlite'),division=cfg['scene_division']))
   host=os.uname();host=os.uname_result((host.sysname,'fixture-host',host.release,host.version,host.machine))
   # This unit fixture substitutes only the trusted source anchors and empty host envelopes.
   anchors={k:sources[k]['source']['sha256'] for k in C.PINS}
   with patch.object(C,'PINS',anchors),patch.object(os,'uname',return_value=host),patch.dict(os.environ,{'STUDENT_R2_FRAME_HOST':'1','STUDENT_R2_LOCAL_NODE':'0'}):
    result=R.compose_native(cfg,base,O/'out')
   self.assertEqual(result['count'],0);self.assertEqual(len(result['intake_evidence']),5)
   members=load(result['source_membership']['path']);self.assertEqual(set(members['sources']),set(sources))
