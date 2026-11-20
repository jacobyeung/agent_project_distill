import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import ast, copy, gzip, importlib.util, sqlite3, unittest
from collections import Counter
from unittest.mock import patch
from types import SimpleNamespace
from student_pilot.p3_provenance import file_pin, pinned
from student_pilot.s1_exclusions import Exclusions
from student_pilot.row_removals import Removals
from student_pilot import r2_scene_bindings as S, s1_pool, s1_scene_census

def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
nd=module('nd_p',L/'out/rcj/nd.py')
F=D/('fixtures_'+str(time.time_ns()));F.mkdir()
DEV=file_pin(T/'student_pilot/r2_dev_merged.json')
OLD=file_pin(L/'work/build24m4n/inputs/969cdb56ce508eff79390d67099c889b92bd360e93dc42ba07f3683ec216a986')
BENCH=file_pin(L/'work/build24m4n/inputs/3119aa4a9594e4507372b99243afc8210fe217393466ac4e5ae78485e7c83970')
oldrule=Exclusions(OLD,BENCH);newrule=Exclusions(DEV,BENCH)
HELD=next(s for s in sorted(newrule.names['dev']-oldrule.names['dev']) if not oldrule.excluded(dict(scene=s)) and not newrule.matches(dict(scene=s))['benchmark'])

def database(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(p) as c:
  c.execute('create table rows(i integer primary key,row text,target text)')
  c.executemany('insert into rows values(?,?,?)',rows)
 return p

def row(q='q',scene='d1/fixture_clean',kind='camera_displacement',src=None):
 ds,s=scene.split('/',1)
 r=dict(qid=q,dataset=ds,scene=s,student_input=dict(question='fixture',options=[]),target='<think>fixture</think>',routing=dict(question_type=kind,events=[],answer='A'))
 if src:r['s1_source']=dict(name=src)
 return r

class Tests(unittest.TestCase):
 def fixture(self,name,p,n,removed=()):
  root=F/name;root.mkdir();(root/'scratch').mkdir()
  path=root/'list';path.write_text(''.join(json.dumps(dict(row_key=q))+'\n' for q in removed))
  rem=Removals([file_pin(path)])
  pdb=database(root/'p.db',p);ndb=database(root/'q/selection/rows.sqlite',n)
  return (pdb,ndb,root/'missing_request',root/'rd0',root/'out',root/'scratch'),(rem,newrule,dict(dev_sha256=nd.DEV))
 def publish(self,args,rules):
  with sqlite3.connect(args[1]) as c: count=c.execute('select count(*) from rows').fetchone()[0]
  chain=dict(status='PASS',config_sha256='a'*64,streams=dict(routing=dict(status='PASS',
   databases=[file_pin(args[1])],complete=True,rows_checked=count,database_rows=count,refused_rows=0,
   checked_key_set_sha256='b'*64,database_key_set_sha256='b'*64)))
  (args[5]/'chain.json').write_bytes(nd.raw(chain))
  with patch.object(nd,'GATE',z.sha(args[0])),patch.object(nd,'native_rules',return_value=rules):
   return nd.publish(*args)
 def test_complete_population_and_all_absence_attributions(self):
  p=[(i,json.dumps(row('q'+str(i))),'{}') for i in range(2005)]
  p += [(2005,json.dumps(row('listed',src='U_Faithful')),'{}'),(2006,json.dumps(row('scene',HELD,src='U_Faithful')),'{}'),(2007,json.dumps(row('keep',src='U_Faithful')),'{}')]
  n=p[:2005]+[p[-1]]
  args,rules=self.fixture('population',p,n,['listed']);result=self.publish(args,rules)
  v=nd.load(args[4]/'nd.json');a=json.loads(gzip.decompress((args[4]/'na.json.gz').read_bytes()))
  self.assertEqual(v['matched_rows'],2006);self.assertEqual(v['task_i'],'PASS');self.assertEqual(v['task_ii'],'PASS')
  self.assertEqual(v['U_Faithful'],dict(P=3,kept=1,expected_kept=1,status='PASS'))
  self.assertEqual([r['attribution'] for r in a['rows']],['list','scene'])
  self.assertEqual(a['rows'][1]['scene_sha256'],nd.DEV);self.assertTrue(a['rows'][1]['scene_ids'])
  self.assertEqual(a['rows'][0]['removal_list_sha256s'],[rules[0].files[0]['sha256']])
  self.assertIn('routing_types.json',result['files']);self.assertLess(result['bytes'],5_000_000)
 def test_unattributed_extra_and_missing_faithful_fail(self):
  p=[(0,json.dumps(row('absent',src='U_Faithful')),'{}')];n=[(0,json.dumps(row('extra')),'{}')]
  args,rules=self.fixture('bad_members',p,n);self.publish(args,rules);v=nd.load(args[4]/'nd.json')
  self.assertEqual((v['task_i'],v['task_ii'],v['task_iii']),('FAIL','FAIL','FAIL'))
  self.assertEqual(v['absent_unattributed'],1);self.assertEqual(v['N_without_P'],1)
 def test_four_classes_are_counted_but_content_wins(self):
  a=row();a['s1_source']=dict(name='s',source=dict(path='old'),frame_binding=dict(fps_source='old'))
  a['s1_source']['frame_binding'].update(authority={k:dict(path='old') for k in ('map','plan','fps_authority')})
  b=copy.deepcopy(a);b['question']='copied';b['s1_source']['source']['path']='new';b['s1_source']['frame_binding']['fps_source']='new'
  for k in b['s1_source']['frame_binding']['authority']:b['s1_source']['frame_binding']['authority'][k]['path']='new'
  args,rules=self.fixture('classes',[(0,json.dumps(a),'{}')],[(1,json.dumps(b),'{}')]);self.publish(args,rules)
  v=nd.load(args[4]/'nd.json');self.assertEqual(v['status'],'PASS')
  self.assertEqual({k:d['path_differences'] for k,d in v['metadata_classes'].items()},dict(ordinal=1,copied=1,paths=4,fps_source=1))
  self.assertTrue(all(d['content_rows']==0 for d in v['metadata_classes'].values()));self.assertEqual(v['unclassified_paths'],{})
 def test_raw_fields_missing_null_numeric_escapes_and_sql_target(self):
  c=nd.load(L/'out/rcj/f.json')
  for a,b in [('{"x":1}','{"x":1.0}'),('{"x":"a"}','{"x":"\\u0061"}'),('{}','{"x":null}'),('{"x":1}','{ "x": 1 }')]:
   self.assertEqual(nd.exact_fields((0,'{"student_input":'+a+'}','{}'),(0,'{"student_input":'+b+'}','{}'),c)[0][0],'/row/student_input')
  self.assertEqual(nd.exact_fields((0,'{}','{}'),(0,'{}','{ }'),c)[0][0],'/target')
  with self.assertRaisesRegex(ValueError,'duplicate'):nd.tokens('{"x":1,"x":2}')
  self.assertEqual(nd.tokens('{"a/b":{"~":1e0}}')['/row/a~1b/~0'],'1e0')
 def test_all_copied_fields_reach_real_admission(self):
  from student_pilot.r0_exclusion import reserve
  from student_pilot.r1_training import row_check
  from student_pilot.extent_receipt import content
  base=row();r=reserve();protected=sorted(r.names)[0]
  for k in ('source_qid','candidate_id','question','question_type','answer','gt_answer','ground_record','provenance','tool_output_spans'):
   with self.assertRaisesRegex(ValueError,'r0_room_refused'):r.check(dict(base,**{k:protected}),'routing')
  with self.assertRaisesRegex(ValueError,'OWN_VALUED'):row_check(dict(base,provenance=dict(geometry_source='own')),'routing')
  a=dict(base,question='one');b=dict(base,question='two');self.assertNotEqual(content(a),content(b))
 def test_ordinal_reaches_actual_reader_lookup(self):
  from student_pilot.carrier_c1_run import Rows
  c=sqlite3.connect(':memory:');c.execute('create table rows(i integer,row text,target text)')
  a=row('a');b=row('b');c.executemany('insert into rows values(?,?,?)',[(0,json.dumps(a),'{}'),(1,json.dumps(b),'{}')])
  r=Rows.__new__(Rows);r.indices={};r.connections={'routing':c};r.wording_exclusion=None;r.extents=SimpleNamespace(check=lambda *a:None);r.r1_training=False;r.b7_inputs=None;r.r2_admission=None;r.tool_flag=None
  self.assertEqual(r.row('routing',0)[0]['qid'],'a')
  c.execute('update rows set i=2-i');self.assertEqual(r.row('routing',1)[0]['qid'],'b')
  c.execute('update rows set i=i-1');self.assertEqual(r.row('routing',0)[0]['qid'],'b');c.close()
 def test_type_table_boundaries_native_family_and_known_evidence(self):
  from student_pilot.r1_population import family
  counts={k:int(v*100) for k,v in nd.QUOTAS.items()};v=nd.type_table(counts);self.assertEqual(v['status'],'PASS')
  bad=dict(counts,units=0);self.assertEqual(nd.type_table(bad)['status'],'FAIL')
  self.assertEqual(nd.type_table({})['status'],'FAIL');self.assertEqual(nd.type_table(dict(counts,other=1))['status'],'FAIL')
  for r in [row(kind='object_abs_distance'),row(q='a0_units_x'),row(kind='camera_rotation'),dict(row(),routing=dict(question_type='object_abs_distance',ground_record=dict(unit='feet')))]:
   self.assertEqual(nd.row_type(r),family(r,'routing'))
  v=nd.type_table(dict(camera_displacement=14020,camera_movement_direction=12260,camera_rotation=5158,absolute_distance=10945,units=718))
  self.assertEqual(v['status'],'FAIL');self.assertAlmostEqual(v['units_rows_per_step'],1.066146957147166)
  for units,expected in [(90,'PASS'),(89,'FAIL'),(110,'PASS'),(111,'FAIL')]:
   trial=dict(counts,units=units,absolute_distance=counts['absolute_distance']+100-units)
   self.assertEqual(nd.type_table(trial)['status'],expected)
 def test_unclassified_counts_and_three_examples(self):
  p=[];n=[]
  for i in range(4):
   a=dict(row('q'+str(i)),unknown='a');b=dict(a,unknown='b')
   p.append((i,json.dumps(a),'{}'));n.append((i,json.dumps(b),'{}'))
  args,rules=self.fixture('unclassified',p,n)
  contract=nd.load(L/'out/rcj/f.json');contract['content_field_paths']=['/i','/target','/row/student_input','/row/routing']
  original=nd.load
  with patch.object(nd,'load',side_effect=lambda path:contract if Path(path).name=='f.json' else original(path)):
   self.publish(args,rules)
  v=nd.load(args[4]/'nd.json');self.assertEqual(v['task_i'],'FAIL')
  self.assertEqual(v['unclassified_paths']['/row/unknown']['count'],4)
  self.assertEqual(len(v['unclassified_paths']['/row/unknown']['examples']),3)
 def test_type_publication_without_P_or_sample(self):
  root=F/'type_only';root.mkdir()
  p=database(root/'n.db',[(0,json.dumps(row(kind='camera_rotation')),'{}')])
  with patch.object(nd,'native_rules',return_value=None):result=nd.publish_types(p,root/'out/routing_types.json')
  v=nd.load(root/'out/routing_types.json');self.assertEqual(v['rows_by_type'],dict(camera_rotation=1))
  self.assertEqual(v['database_sha256'],z.sha(p));self.assertEqual(result['status'],'FAIL')
 def test_gate_contract_and_budget_refuse(self):
  args,rules=self.fixture('gate',[(0,json.dumps(row()),'{}')],[(0,json.dumps(row()),'{}')])
  with patch.dict(os.environ,PS_GATE=z.sha(args[0])),self.assertRaisesRegex(ValueError,'gate'):nd.publish(*args)
  with patch.object(nd,'GATE',z.sha(args[0])),patch.object(nd,'FIELDS','0'*64),self.assertRaisesRegex(ValueError,'fields'):nd.publish(*args)
  with patch.object(nd,'LIMIT',1),self.assertRaisesRegex(ValueError,'size'):self.publish(args,rules)
  self.assertFalse(args[4].exists())
 def test_merged_pool_native_census_other_streams_byte_identical(self):
  root=F/'census';root.mkdir();sets=[];lists={}
  for name in ('T0_gaps','OTHER','U_Faithful'):
   path=root/(name+'.gz')
   records=[dict(qid=name+str(i),dataset=scene.split('/')[0],scene=scene.split('/')[1],question_type='route_planning',head_program=None,score_nomination_allowed=False,answer='A',target='<think>\nA.\n</think>\n\nA') for i,scene in enumerate(('d1/fixture_clean',HELD))]
   path.write_bytes(gzip.compress(('\n'.join(json.dumps(r) for r in records)+'\n').encode(),mtime=0))
   sets.append(dict(name=name,status='final',files=dict(rows=dict(file_pin(path),rows=2,bytes=path.stat().st_size)),rows_per_type=dict(route_planning=2)))
  for name in ('dev_s1','eval_rooms','room_release_gate'):
   p=root/(name+'.tsv');p.write_text('');lists[name]=dict(list=str(p),list_sha256=z.sha(p),rows=0)
  lists['dev_s1'].update(withhold=OLD['path'],withhold_sha256=OLD['sha256']);lists['eval_rooms'].update(v2=BENCH['path'],v2_sha256=BENCH['sha256'])
  write(root/'manifest.json',dict(schema='dose-pool-s1-manifest-v2',sets=sets,exclusions=lists))
  spec=dict(pool_manifest=file_pin(root/'manifest.json'),sources={})
  for name in S.SOURCES:
   p=root/(name+'.jsonl');p.write_text(json.dumps(row(name))+'\n'+json.dumps(row(name+'x',HELD))+'\n')
   pin=file_pin(p);write(root/(name+'.json'),dict(rows_metadata=pin,count=2));spec['sources'][name]=dict(rows=pin,count=2,receipt=file_pin(root/(name+'.json')))
  cfg=dict(dev_scene_exclusions=DEV,benchmark_scene_exclusions=BENCH,r2_all_stream_exclusions=True)
  before={name:S.rebuild_receipt(dict(value,source=name),DEV,BENCH,root/('old_'+name)) for name,value in spec['sources'].items()}
  got=S.rebuild(spec,cfg,root/'new');pool=nd.load(pinned(got['pool_selection']))
  for name in S.SOURCES:
   self.assertEqual(nd.raw(nd.load(before[name]['path'])['source_scene_exclusions']),nd.raw(nd.load(got['receipts'][name]['path'])['source_scene_exclusions']))
  self.assertEqual(pool['source_scene_exclusions']['files']['dev']['sha256'],nd.DEV)
  downstream=Exclusions(DEV,BENCH)
  for name in ('T0_gaps','OTHER','U_Faithful'):
   self.assertEqual(pool['source_scene_exclusions']['sources'][name]['dev_matches'],1)
   selected=list(s1_pool.selected_rows(got['pool_selection'],name));self.assertEqual(len(selected),1)
   source='pool/'+name;downstream.counts(source)
   downstream.expected[source]=dict(schema='s1-scene-census-v1',method='subset-of-independently-checked-pool-selection',files=downstream.files,rows=None,counts=dict(dev_matches=0,benchmark_matches=0,overlap_matches=0))
   for r in selected:downstream.keep(r,source)
  downstream.report()
  downstream.keep(row('leak',HELD),'pool/T0_gaps')
  with self.assertRaisesRegex(ValueError,'dev_matches'):downstream.report()
  write(D/'CENSUS_TEST.json',dict(status='PASS',dev=DEV['sha256'],pool_sources=pool['source_scene_exclusions']['sources'],other_entries_byte_identical=list(S.SOURCES),tree_compare_sha256=z.sha(T/'student_pilot/s1_scene_census.py')))

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
 write(D/'NEW_TESTS.json',dict(status='PASS' if result.wasSuccessful() else 'FAIL',tests=result.testsRun,failures=[str(x) for x in result.failures],errors=[str(x) for x in result.errors],fixtures=str(F)))
 raise SystemExit(not result.wasSuccessful())
