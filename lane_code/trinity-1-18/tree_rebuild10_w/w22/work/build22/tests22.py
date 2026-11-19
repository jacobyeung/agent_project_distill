from pathlib import Path
from copy import deepcopy
import unittest,json,sys,sqlite3,os
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
os.environ['R2_FIXTURES']=str(L/'fixtures')
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
from student_pilot.p3_provenance import load,file_pin
from student_pilot.r1_launch22 import validate_removals
from student_pilot.row_removals import Removals

class Removals22(unittest.TestCase):
 def test_exact_list_and_order(self):
  cfg=load(D/'inputs/config.json');validate_removals(cfg)
  rows=load(cfg['remove_files'][-1]['path'])['rows'];r=Removals(cfg['remove_files'])
  self.assertEqual(len(rows),109)
  for row in rows:self.assertFalse(r.keep({'qid':row['qid']}))
  for mode in ('absent','reordered','duplicated','wrong_hash','missing_file','missing_binding'):
   bad=deepcopy(cfg)
   if mode=='absent':bad['remove_files']=bad['remove_files'][:-1]
   elif mode=='reordered':bad['remove_files'][-2:]=reversed(bad['remove_files'][-2:])
   elif mode=='duplicated':bad['remove_files'].append(bad['remove_files'][-1])
   elif mode=='wrong_hash':bad['remove_files'][-1]['sha256']='0'*64
   elif mode=='missing_file':bad['remove_files'][-1]['path']=str(D/'absent.json')
   else:bad['r1_training'].pop('launch22')
   with self.subTest(mode=mode),self.assertRaises((ValueError,FileNotFoundError)):validate_removals(bad)

class Camera22(unittest.TestCase):
 def test_all_heldout_wordings_and_native_reader(self):
  from student_pilot import r1_coverage as C
  from student_pilot.carrier_c1_run import Rows
  cfg=load(D/'inputs/config.json');v=cfg['r1_training'];guard=C.validate_binding(cfg)
  templates=[t for ts in load(v['camera_wording_exclusion']['path'])['heldout'].values() for t in ts]
  self.assertEqual(len(templates),24)
  for template in templates:
   text=template.format(i=1,j=32,n=32,unit='metres',options='left; right')
   for field in ('student_input','routing','ground_record',None):
    row={'question':text.upper().replace(' ','\u00a0')}
    if field:row={field:row}
    with self.subTest(template=template,field=field),self.assertRaisesRegex(ValueError,'R1_HELD_OUT_WORDING'):guard.check(row)
  reader=Rows(dict(streams={},r1_training=v,remove_files=cfg['remove_files']),None)
  db=sqlite3.connect(':memory:');reader.connections['vqa']=db
  db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
  db.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(dict(qid='planted',student_input={'question':text})),'{}'))
  try:
   with self.assertRaisesRegex(ValueError,'R1_HELD_OUT_WORDING'):reader.row('vqa',0)
  finally:reader.close()
 def test_missing_and_changed_wording_pin(self):
  from student_pilot.r1_coverage import validate_binding
  cfg=load(D/'inputs/config.json')
  for mode in ('absent','changed'):
   bad=deepcopy(cfg)
   if mode=='absent':bad['r1_training'].pop('camera_wording_exclusion')
   else:bad['r1_training']['camera_wording_exclusion']['sha256']='0'*64
   with self.assertRaisesRegex(ValueError,'CAMERA_WORDING'):validate_binding(bad)
 def test_camera_native_composition_and_membership(self):
  import tempfile
  from student_pilot.r1_routing import compose
  from student_pilot.r1_population import Membership
  from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
  from student_pilot.p3_provenance import write
  cfg=load(D/'inputs/config.json');root=Path(tempfile.mkdtemp(prefix='camera_compose22_',dir=L/'work/tmp'))
  from student_pilot.r1_coverage import source_names
  specs=load(cfg['r1_training']['row_sources']['path']);sources={k:specs[k]['source'] for k in source_names(specs)}
  with Path(sources['camera_wording']['path']).open() as f:row=json.loads(next(f))
  p=root/'base.sqlite';db=sqlite3.connect(p);db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)');db.commit();db.close()
  write(root/'base.json',dict(schema=ROUTING_SCHEMA,stream='routing',database=file_pin(p),count=0,
    division=cfg['scene_division'],scene_role='train',heldout_overlap=0))
  batch=[('camera_wording',sources['camera_wording'],[dict(row=row,target={})],sources['camera_wording'])]
  result=compose(file_pin(root/'base.json'),sources,batch,cfg,root/'out')
  self.assertEqual(result['per_source'],{'camera_wording':1})
  member=Membership(result['source_membership']);db=sqlite3.connect(result['database']['path'])
  stored=json.loads(db.execute('SELECT row FROM rows').fetchone()[0]);db.close()
  self.assertEqual(member.cell(stored,'routing'),'camera_wording')
 def test_camera_event_intake_failing_before(self):
  import importlib.util,tempfile
  from student_pilot.r2_adapters import normalize
  from student_pilot.r2_contract import validate
  from student_pilot.routing_type_gate import validate as form
  from student_pilot.carrier_c1_routing import POLICIES
  cfg=load(D/'inputs/config.json');specs=load(cfg['r1_training']['row_sources']['path'])
  with Path(specs['camera_wording']['source']['path']).open() as f:row=json.loads(next(f))
  spec=importlib.util.spec_from_file_location('student_pilot.old_adapters22',D/'before/r2_adapters.py')
  old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  with self.assertRaises(KeyError):form(old.normalize(row),POLICIES['both-path-20261116'],['pose','depth'])
  normalized=normalize(row);normalized['routing_policy']='both-path-20261116'
  form(normalized,POLICIES['both-path-20261116'],['pose','depth']);validate(normalized,'routing')
  self.assertEqual(normalized['events'],row['routing']['events'])
  self.assertEqual(normalized['student_input'],row['student_input'])
  self.assertEqual(normalized['target'].split('</think>')[0],row['target'].split('</think>')[0])
  from student_pilot.r2_contract import CONTRACT
  from student_pilot.r2_grammar import SHARED_SHA256
  from student_pilot.r2_intake import intake
  from student_pilot.p3_provenance import digest,write
  from tests.test_r2_data_path import RECORDS,SOURCES
  root=Path(tempfile.mkdtemp(prefix='camera_intake22_',dir=L/'work/tmp'))
  p=root/'rows.jsonl';p.write_text(json.dumps(row)+'\n');rp=file_pin(p)
  exclusions={k:file_pin(RECORDS/v) for k,v in SOURCES.items()}
  write(root/'coverage.json',dict(exclusions=exclusions,rows_sha256=rp['sha256'],rows={row['qid']:
   dict(status='known',names=[row['dataset']+'/'+row['scene'],row['routing']['canonical']])}))
  write(root/'manifest.json',dict(schema='r2-family-manifest-v1',family='camera_wording',stream='routing',count=1,
   trace_contract=CONTRACT,validator_sha256=SHARED_SHA256,rows=rp,row_bindings={row['qid']:digest(row)},
   scene_coverage=file_pin(root/'coverage.json'),exclusions=exclusions,upstream_receipts=[],
   routing_policy='both-path-20261116',artifact_heads=['pose','depth']))
  admitted,report=intake(root/'manifest.json');self.assertEqual(len(admitted),1,report)
  bad=deepcopy(row);bad['target']=bad['target'].replace('0.69','0.68')
  with self.assertRaises(ValueError):normalize(bad)

if __name__=='__main__':unittest.main()
