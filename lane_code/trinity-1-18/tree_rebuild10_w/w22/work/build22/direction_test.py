from pathlib import Path
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch
import tempfile,sys,json,sqlite3,unittest,importlib.util
L=Path(__file__).resolve().parents[2];D=L/'work/build22'
sys.path[:0]=[str(L/'work/tree_r1'),str(L/'work/build21')]
from student_pilot import r1_direction_twins as T,r1_rooms as R
from student_pilot.p3_provenance import load,write,file_pin,digest
from student_pilot.row_removals import Removals

class Twins22(unittest.TestCase):
 def setUp(self):
  self.root=Path(tempfile.mkdtemp(prefix='twins22_',dir=L/'work/tmp'))
  self.cfg=load(D/'inputs/config.json');v=self.cfg['r1_training']
  self.source=dict(qid='source',dataset='scannet',scene='scene9997_00',canonical='scannet/scene9997_00',question_type='object_rel_direction_easy')
  self.twin=dict(self.source,qid='twin',label_row_keys=['source'],answer='front')
  db=self.root/'base.sqlite';c=sqlite3.connect(db)
  c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)');c.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(self.source),'{}'));c.commit();c.close()
  self.base=file_pin(db)
  p=self.root/'rows.jsonl';p.write_text(json.dumps(self.twin)+'\n');self.rows=file_pin(p)
  self.record=dict(twin_key='twin',source_key='source',source_room='scannet/scene9997',twin_sha256=digest(self.twin))
  p=self.root/'binding.jsonl';p.write_text(json.dumps(self.record)+'\n');self.binding=file_pin(p)
  p=self.root/'aliases.json';write(p,dict(complete=True,conflicts=[],quarantined_tokens=[],aliases={}));self.aliases=file_pin(p)
  v['direction_twins']=dict(rows=self.rows,binding=self.binding,aliases=self.aliases,source_database=self.base)
  receipt=load(self.cfg['streams']['vqa']['path']);receipt.update(database=self.base,count=1)
  p=self.root/'receipt.json';write(p,receipt);self.cfg['streams']['vqa']=file_pin(p)
  self.stack=ExitStack()
  for module,key,val in ((T,'ROWS',self.rows['sha256']),(T,'BINDING',self.binding['sha256']),(T,'ALIASES',self.aliases['sha256']),(T,'COUNT',1),(R,'STORE',self.base['sha256'])):
   self.stack.enter_context(patch.object(module,key,val))
 def tearDown(self):self.stack.close()
 def test_producer_and_store_exception_failing_before(self):
  cfg=T.augment(self.cfg,self.root/'aug');actual=load(cfg['streams']['vqa']['path'])['database']
  T.verify_augmented(cfg,actual)
  audit=load(cfg['r1_training']['room_audit']['path']);audit.update(row_sources=cfg['r1_training']['row_sources'],remove_files=cfg['remove_files'])
  # Fixture keeps the bound slice metadata and replaces only the synthetic store.
  for kind,pin in load(cfg['r1_training']['row_sources']['path']).items():
   if kind=='camera_wording':audit['slices'][kind]=dict(source=pin['source'],unresolved=0,unremoved_hits=0)
  audit['store'].update(database=actual,unresolved=1,unremoved_hits=0)
  p=self.root/'audit.json';write(p,audit);ap=file_pin(p)
  # Restore the original K1 authority constant for the list rule; STORE alone is a stand-in.
  spec=importlib.util.spec_from_file_location('student_pilot.old_rooms22',D/'before/r1_rooms.py')
  old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
  with self.assertRaisesRegex(ValueError,'STORE_PIN_MISMATCH'):old.verify_audit(cfg,ap)
  R.verify_audit(cfg,ap)
  bad=deepcopy(cfg);bad['r1_training'].pop('direction_twins')
  audit['store']['unresolved']=0;p.write_text(json.dumps(audit))
  with self.assertRaisesRegex(ValueError,'BINDING_REQUIRED_FOR_STORE'):R.verify_audit(bad,file_pin(p))
  audit['store']['unresolved']=1;p.write_text(json.dumps(audit));ap=file_pin(p)
  bad=deepcopy(cfg);bad['r1_training'].pop('direction_augmented')
  with self.assertRaisesRegex(ValueError,'AUGMENTATION_REQUIRED'):R.verify_audit(bad,ap)
  audit['store']['unremoved_hits']=1;p.write_text(json.dumps(audit))
  with self.assertRaisesRegex(ValueError,'K1_UNREMOVED'):R.verify_audit(cfg,file_pin(p))
 def test_missing_source_and_room_and_digest(self):
  for mode in ('missing_source','room','digest','facing','source_key'):
   row=deepcopy(self.twin);record=deepcopy(self.record)
   if mode=='missing_source':record['source_key']='missing'
   elif mode=='room':record['source_room']='scannet/scene9998'
   elif mode=='digest':record['twin_sha256']='0'*64
   elif mode=='facing':row['facing']='away';record['twin_sha256']=digest(row)
   else:row['label_row_keys']=[];record['twin_sha256']=digest(row)
   p=self.root/(mode+'.jsonl');p.write_text(json.dumps(record)+'\n');bp=file_pin(p)
   cfg=deepcopy(self.cfg);cfg['r1_training']['direction_twins']['binding']=bp
   with patch.object(T,'BINDING',bp['sha256']),self.subTest(mode=mode),self.assertRaises(ValueError):
    binding=T.Binding(cfg);binding.check(row)
 def test_k1_source_key_removes_twin_and_unicode_digest(self):
  p=self.root/'remove.jsonl';p.write_text(json.dumps(dict(row_key='source'))+'\n')
  self.assertFalse(Removals([file_pin(p)]).keep(self.twin))
  row=dict(self.twin,question='caméra')
  self.assertNotEqual(digest(row),__import__('hashlib').sha256(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 def test_complete_population_and_manifest_mutations(self):
  for mode,reason in (('base','BASE_POPULATION_DIFFERS'),('twin','AUGMENTED_ROW_DIFFERS'),('extra','AUGMENTED_EXTRA_ROW')):
   cfg=T.augment(self.cfg,self.root/mode);actual=load(cfg['streams']['vqa']['path'])['database']
   db=sqlite3.connect(actual['path'])
   if mode=='base':db.execute('UPDATE rows SET target=? WHERE i=0',('{"forged":1}',))
   elif mode=='twin':db.execute('UPDATE rows SET target=? WHERE i=1',('{"forged":1}',))
   else:db.execute('INSERT INTO rows VALUES(2,?,?)',(json.dumps(self.twin),'{}'))
   db.commit();db.close();actual=file_pin(actual['path'])
   proof=load(cfg['r1_training']['direction_augmented']['path']);proof['database']=actual
   p=self.root/(mode+'_proof.json');write(p,proof);cfg['r1_training']['direction_augmented']=file_pin(p)
   with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,reason):T.verify_augmented(cfg,actual)
  cfg=T.augment(self.cfg,self.root/'manifest');actual=load(cfg['streams']['vqa']['path'])['database']
  proof=load(cfg['r1_training']['direction_augmented']['path']);proof['binding']=self.rows
  p=self.root/'forged_proof.json';write(p,proof);cfg['r1_training']['direction_augmented']=file_pin(p)
  with self.assertRaisesRegex(ValueError,'AUGMENTATION_BINDING'):T.verify_augmented(cfg,actual)
  with self.assertRaisesRegex(ValueError,'OUTPUT_EXISTS'):T.augment(self.cfg,self.root/'manifest')
 def test_incomplete_row_set_and_bad_authority(self):
  for mode,raw,reason in (('empty','','ROWS_INCOMPLETE'),('duplicate',(json.dumps(self.twin)+'\n')*2,'ROW_DUPLICATE')):
   p=self.root/(mode+'_rows.jsonl');p.write_text(raw);pin=file_pin(p)
   cfg=deepcopy(self.cfg);cfg['r1_training']['direction_twins']['rows']=pin
   with patch.object(T,'ROWS',pin['sha256']),self.assertRaisesRegex(ValueError,reason):list(T.Binding(cfg).rows())
  p=self.root/'bad_authority.json';write(p,dict(complete=False,aliases={}));pin=file_pin(p)
  cfg=deepcopy(self.cfg);cfg['r1_training']['direction_twins']['aliases']=pin
  with patch.object(T,'ALIASES',pin['sha256']),self.assertRaisesRegex(ValueError,'ROOM_AUTHORITY'):T.Binding(cfg)
  self.assertEqual(T.dimensions(dict(question='Other',answer='front',student_input={'options':{'front':'front'}})),('unspecified','unknown','front'))
 def test_clause_and_answer_dimensions(self):
  for clause,expected in (('facing away from','away'),('face away from','away'),('look toward','toward'),('facing','toward')):
   row=dict(question_type='object_rel_direction_hard',answer='B',student_input=dict(question=clause,options=['A. front-left','B. back-right']))
   self.assertEqual(T.dimensions(row),(expected,'hard','back'))

if __name__=='__main__':unittest.main(verbosity=2)
