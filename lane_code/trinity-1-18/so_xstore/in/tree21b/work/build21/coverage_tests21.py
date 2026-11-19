from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
import json,sqlite3,unittest
from student_pilot import r1_coverage as C
from student_pilot.p3_provenance import file_pin,load,write,digest
L=Path(__file__).resolve().parents[2];B=L/'work/build21';O=B/'proofs/coverage_tests'
class Coverage21(unittest.TestCase):
 def setUp(self):
  O.mkdir(parents=True,exist_ok=True)
  self.split=file_pin(L.parent/'ext/v2h/SPLIT_V2.json')
 def put(self,name,value):
  p=O/name;p.write_text(json.dumps(value));return file_pin(p)
 def listing(self,name,rows):
  p=O/name;p.write_text(''.join(json.dumps(r)+'\n' for r in rows));return file_pin(p)
 def test_wording_all_templates_unicode_and_native_reader(self):
  guard=C.WordingExclusion(self.split)
  for template in load(self.split['path'])['held_out']:
   text=template.format(a='chair',b='table',u='feet')
   for field in (None,'student_input','routing','ground_record'):
    row={'question':'  '+text.upper().replace(' ','\u00a0')+'  '}
    if field:row={field:row}
    with self.assertRaisesRegex(ValueError,'R1_HELD_OUT_WORDING:'):guard.check(row)
  self.assertEqual(guard.check({'question':None}),{'question':None})
  self.assertEqual(guard.check({'ground_record':None}),{'ground_record':None})
  self.assertEqual(guard.check({'question':'How far apart are these two things?'}),{'question':'How far apart are these two things?'})
  from student_pilot.carrier_c1_run import Rows
  reader=Rows(dict(streams={},r1_training={'wording_exclusion':self.split}),None)
  db=sqlite3.connect(':memory:');reader.connections['vqa']=db
  db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
  db.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(dict(qid='planted',question=text)),'{}'))
  try:
   with self.assertRaisesRegex(ValueError,'R1_HELD_OUT_WORDING:'):reader.row('vqa',0)
  finally:reader.close()
 def test_wording_authentication(self):
  with self.assertRaisesRegex(ValueError,'PIN'):C.WordingExclusion(dict(self.split,sha256='a'*64))
  p=self.put('short.json',{'held_out':[]})
  with patch.object(C,'SPLIT',p['sha256']):
   with self.assertRaisesRegex(ValueError,'COUNT'):C.WordingExclusion(p)
  with self.assertRaises(ValueError):C.WordingExclusion(dict(self.split,path=str(O/'short.json')))
 def test_census_planted_wording_refuses_by_name(self):
  from student_pilot import r1_rooms
  cfg=load(B/'inputs/config.json');sources=load(cfg['r1_training']['row_sources']['path'])
  empty=O/'empty.jsonl';empty.write_text('')
  for kind in ('recovery','absolute_distance'):sources[kind]['source']=file_pin(empty)
  template=load(self.split['path'])['held_out'][0]
  planted=O/'planted.jsonl';planted.write_text(json.dumps(dict(qid='planted',question=template.format(a='chair',b='table',u='feet'),canonical='scannet/scene9997_00'))+'\n')
  sources['units']['source']=file_pin(planted);cfg['r1_training']['row_sources']=self.put('census_sources.json',sources)
  with patch.object(sqlite3,'connect',side_effect=AssertionError('Store opened before planted wording refusal')):
   with self.assertRaisesRegex(ValueError,'R1_HELD_OUT_WORDING:'+__import__('re').escape(template)):r1_rooms.census(cfg)
 def test_source_binding(self):
  self.assertEqual(C.source_names({}),('recovery','absolute_distance','units'))
  with self.assertRaisesRegex(ValueError,'INCOMPLETE'):C.source_names({'coverage_units':{}})
  self.assertIsNone(C.validate_binding({}))
  self.assertIsNone(C.validate_binding({'r1_training':None}))
  cfg=load(B/'inputs/config.json');self.assertIsInstance(C.validate_binding(cfg),C.WordingExclusion)
  from student_pilot.r1_training import validate
  validate(cfg)
  bad=deepcopy(cfg);bad['r1_training'].pop('wording_exclusion')
  with self.assertRaisesRegex(ValueError,'REQUIRED'):C.validate_binding(bad)
  sources=load(cfg['r1_training']['row_sources']['path']);sources['coverage_units']['source']['sha256']='a'*64
  bad=deepcopy(cfg);bad['r1_training']['row_sources']=self.put('bad_sources.json',sources)
  with self.assertRaisesRegex(ValueError,'SOURCE_PIN'):C.validate_binding(bad)
 def test_union_content_authentication_and_order(self):
  a=dict(row_key='a',canonical='scannet/scene1',reason='k1_heldout_v7');b=dict(a,row_key='b')
  self.assertEqual(C.union_rows([b,a],[a]),[a,b])
  for bad in ({},dict(a,reason='other'),dict(a,row_key=''),dict(a,canonical='unknown')):
   with self.assertRaisesRegex(ValueError,'ROW_INVALID'):C.union_rows([bad],[])
  with self.assertRaisesRegex(ValueError,'CONFLICT'):C.union_rows([a],[dict(a,canonical='scannet/scene2')])
  base=self.listing('u.json',[a]);extra=self.listing('u2.json',[b]);union=self.listing('uu.json',[a,b]);n=self.listing('n.json',[])
  value=dict(v7_k1_removal=union,v7_k1_union=dict(base=base,extra=extra,union=union));removals=[base,union,n]
  self.assertTrue(C.verify_union(value,removals,base['sha256'],n['sha256']))
  self.assertFalse(C.verify_union({},[],base['sha256'],n['sha256']))
  for bad in ([union,base,n],[base,n,union],[base,union],[base,base,union,n]):
   with self.assertRaisesRegex(ValueError,'ORDER'):C.verify_union(value,bad,base['sha256'],n['sha256'])
  wrong=deepcopy(value);wrong['v7_k1_union']['base']=extra
  with self.assertRaisesRegex(ValueError,'BINDING'):C.verify_union(wrong,removals,base['sha256'],n['sha256'])
  wrong=deepcopy(value);wrong['v7_k1_removal']=self.listing('wrong.json',[a]);wrong['v7_k1_union']['union']=wrong['v7_k1_removal']
  with self.assertRaisesRegex(ValueError,'CONTENT'):C.verify_union(wrong,removals,base['sha256'],n['sha256'])
  (O/'u2.json').write_text('{}\n')
  with self.assertRaises(ValueError):C.verify_union(value,removals,base['sha256'],n['sha256'])
 def test_grouped_membership(self):
  from student_pilot.r1_population import Membership
  sources={};rows=[]
  for name in C.PINS:
   pin=self.put(name+'.json',{'source':name});row=dict(qid=name,r1_source=dict(family=name,sha256=pin['sha256']))
   sources[name]=dict(source=pin,rows={name:digest(row)});rows.append(row)
  member=Membership(self.put('membership.json',dict(schema='r1-source-membership-v1',sources=sources)))
  for row in rows:self.assertEqual(member.cell(row,'routing'),'coverage')
  with self.assertRaisesRegex(ValueError,'MISFILED'):member.cell(dict(rows[0],changed=True),'routing')
  with self.assertRaisesRegex(ValueError,'MISFILED'):member.cell(rows[0],'vqa')
 def test_rewording_changes_only_identifiers(self):
  for units in (False,True):
   parent=dict(qid='p',candidate_id='c0',question='old',answer='4',target='printed four',provenance={})
   if units:parent.update(ground_record=dict(qid='p',candidate_id='c0',question='old',question_identity='i0',geometry=[1,2]))
   child=deepcopy(parent);child.update(qid='p_dh00',candidate_id='c1',question='new')
   edit=dict(reworded_from='p',before='old',after='new',candidate_id_before='c0')
   if units:
    parent['provenance']['details']={};child['provenance']['details']={'question_edit':edit}
    child['ground_record'].update(qid='p_dh00',candidate_id='c1',question='new',question_identity='i1')
   else:child['provenance']['dist_diag_question_edit']=edit
   self.assertEqual(C.rewording(child,parent),'p')
   with self.assertRaisesRegex(ValueError,'PARENT_IDENTITY'):C.rewording(dict(child,candidate_id='c0'),parent)
   with self.assertRaisesRegex(ValueError,'NON_WORDING_CHANGE'):C.rewording(dict(child,answer='5'),parent)
